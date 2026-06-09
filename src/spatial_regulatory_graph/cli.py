from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import ClaimGateEvidence, evaluate_claim_gate
from .claim_status import graduation_claim_status_line
from .real_smoke import RealSmokeConfig, default_st_path
from .smoke import run_synthetic_smoke


def _paths_payload(paths: dict[str, Path]) -> dict[str, str]:
    return {key: str(path) for key, path in paths.items()}


def _real_config(args: argparse.Namespace) -> RealSmokeConfig:
    return RealSmokeConfig(
        st_path=args.st_path or default_st_path(),
        label_key=args.label_key,
        max_spots=args.max_spots,
        max_regulators=args.max_regulators,
        max_targets=args.max_targets,
        max_gene_scan=args.max_gene_scan,
        neighbor_count=args.neighbor_count,
        seed=args.seed,
    )


def _add_real_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--st-path", dest="st_path", type=Path, default=None)
    parser.add_argument("--label-key", default="ground_truth")
    parser.add_argument("--max-spots", type=int, default=1500)
    parser.add_argument("--max-regulators", type=int, default=12)
    parser.add_argument("--max-targets", type=int, default=32)
    parser.add_argument("--max-gene-scan", type=int, default=4096)
    parser.add_argument("--neighbor-count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--results-dir", type=Path, default=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spatial-regulatory-graph")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("smoke-synthetic")

    real = sub.add_parser("smoke-real")
    _add_real_config_args(real)

    parity = sub.add_parser("gate2-parity")
    _add_real_config_args(parity)
    parity.add_argument("--external-edge-path", type=Path, default=None)
    parity.add_argument("--external-evaluation-output-path", type=Path, default=None)
    parity.add_argument("--edge-output-path", type=Path, default=None)
    parity.add_argument("--out-path", type=Path, default=None)
    parity.add_argument("--top-n", type=int, default=None)

    gate3 = sub.add_parser("gate3-analysis")
    _add_real_config_args(gate3)
    gate3.add_argument("--out-path", type=Path, default=None)

    sub.add_parser("claim-status")
    args = parser.parse_args(argv)

    if args.command == "smoke-synthetic":
        report = run_synthetic_smoke()
        print(
            json.dumps(
                {
                    "coordinate_shuffle_delta": report.coordinate_shuffle_delta,
                    "surviving_edges_by_tier": report.surviving_edges_by_tier,
                    "claim_status": report.claim_status.value,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "smoke-real":
        from .real_smoke import run_real_data_smoke
        from .result_wiring import emit_real_smoke_results

        config = _real_config(args)
        report = run_real_data_smoke(config)
        payload = report.to_jsonable()
        payload["contract_results"] = _paths_payload(
            emit_real_smoke_results(report, config, results_dir=args.results_dir)
        )
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "gate2-parity":
        from .comparison import build_survival_parity_table, read_edge_rows, write_edge_rows
        from .real_smoke import evaluate_external_edges, run_real_data_smoke
        from .result_wiring import emit_gate2_results

        config = _real_config(args)
        report = run_real_data_smoke(config)
        reference_rows = None
        if args.external_edge_path is not None:
            reference_rows = list(evaluate_external_edges(read_edge_rows(args.external_edge_path), config))
            if args.external_evaluation_output_path is not None:
                write_edge_rows(args.external_evaluation_output_path, reference_rows)
        table = build_survival_parity_table(report.edge_rows, reference_edge_rows=reference_rows, top_n=args.top_n)
        if args.edge_output_path is not None:
            write_edge_rows(args.edge_output_path, report.edge_rows)
        payload = {"real_smoke": report.to_jsonable(), "parity": table}
        outputs = {}
        if args.out_path is not None:
            outputs["parity_table"] = args.out_path
        if args.edge_output_path is not None:
            outputs["local_edge_rows"] = args.edge_output_path
        if args.external_evaluation_output_path is not None:
            outputs["external_evaluated_edge_rows"] = args.external_evaluation_output_path
        payload["contract_results"] = _paths_payload(
            emit_gate2_results(report, table, config, results_dir=args.results_dir, outputs=outputs)
        )
        text = json.dumps(payload, indent=2, sort_keys=True)
        if args.out_path is not None:
            args.out_path.parent.mkdir(parents=True, exist_ok=True)
            args.out_path.write_text(text + "\n", encoding="utf-8")
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "gate3-analysis":
        from .gate3 import run_gate3_analysis
        from .result_wiring import emit_gate3_results

        config = _real_config(args)
        payload = run_gate3_analysis(
            st_path=config.st_path,
            label_key=config.label_key,
            max_spots=config.max_spots,
            max_regulators=config.max_regulators,
            max_targets=config.max_targets,
            max_gene_scan=config.max_gene_scan,
            neighbor_count=config.neighbor_count,
            seed=config.seed,
        )
        outputs = {}
        if args.out_path is not None:
            outputs["gate3_table"] = args.out_path
        payload["contract_results"] = _paths_payload(
            emit_gate3_results(payload, config, results_dir=args.results_dir, outputs=outputs)
        )
        text = json.dumps(payload, indent=2, sort_keys=True)
        if args.out_path is not None:
            args.out_path.parent.mkdir(parents=True, exist_ok=True)
            args.out_path.write_text(text + "\n", encoding="utf-8")
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "claim-status":
        print(graduation_claim_status_line())
        return 0

    print(evaluate_claim_gate(ClaimGateEvidence()).value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
