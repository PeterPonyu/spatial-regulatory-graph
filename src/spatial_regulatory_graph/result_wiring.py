from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .contracts import ClaimGateEvidence
from .real_smoke import RealSmokeConfig, RealSmokeResult
from .results_contract import dataset_card_id, write_results

PROJECT_ID = "spatial-regulatory-graph"


def _numeric_items(payload: Mapping[str, Any], prefix: str = "") -> dict[str, float | None]:
    metrics: dict[str, float | None] = {}
    for key, value in payload.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if value is None:
            metrics[name] = None
        elif isinstance(value, bool):
            continue
        elif isinstance(value, (int, float)):
            metrics[name] = float(value)
        elif isinstance(value, Mapping):
            metrics.update(_numeric_items(value, name))
    return metrics


def _metadata(config: RealSmokeConfig, report: RealSmokeResult | None, *, notes: str) -> dict[str, Any]:
    dataset_paths = [str(config.st_path)]
    real_metrics = report.metrics if report is not None else {}
    return {
        "dataset_paths": dataset_paths,
        "n_obs": real_metrics.get("sampled_spot_count"),
        "n_vars": real_metrics.get("target_count"),
        "seed": config.seed,
        "deterministic": True,
        "num_threads": 1,
        "reproducibility_level": "seeded",
        "normalization": {"applied": True, "method": "log1p"},
        "interpretability": {
            "negative_controls": ["coordinate_shuffle", "label_shuffle", "prior_shuffle", "cross_reference_shuffle"],
            "evidence_tiers": ["candidate", "supported", "validated"],
        },
        "notes": notes,
        "provenance": {
            "label_key": config.label_key,
            "max_spots": config.max_spots,
            "max_regulators": config.max_regulators,
            "max_targets": config.max_targets,
            "max_gene_scan": config.max_gene_scan,
            "neighbor_count": config.neighbor_count,
        },
    }


def emit_real_smoke_results(
    report: RealSmokeResult,
    config: RealSmokeConfig,
    *,
    results_dir: Path | None = None,
    outputs: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    metrics = dict(report.metrics)
    metrics.update({f"tier_count.{tier}": float(count) for tier, count in report.tier_counts.items()})
    return write_results(
        PROJECT_ID,
        dataset_card_id([str(config.st_path)]),
        metrics,
        outputs=outputs,
        run_metadata=_metadata(config, report, notes="real-data smoke emitted through the vendored results contract"),
        results_dir=results_dir,
    )


def emit_gate2_results(
    report: RealSmokeResult,
    parity_table: Mapping[str, Any],
    config: RealSmokeConfig,
    *,
    results_dir: Path | None = None,
    outputs: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    metrics = {f"real_smoke.{key}": value for key, value in report.metrics.items()}
    metrics.update(_numeric_items(parity_table.get("differentiator", {}), "gate2"))
    return write_results(
        PROJECT_ID,
        dataset_card_id([str(config.st_path)]),
        metrics,
        outputs=outputs,
        run_metadata=_metadata(config, report, notes="gate-2 parity emitted through the vendored results contract"),
        results_dir=results_dir,
    )


def emit_gate3_results(
    payload: Mapping[str, Any],
    config: RealSmokeConfig,
    *,
    results_dir: Path | None = None,
    outputs: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    real_payload = payload.get("real_smoke", {})
    real_metrics = real_payload.get("metrics", {}) if isinstance(real_payload, Mapping) else {}
    metrics = {f"real_smoke.{key}": value for key, value in real_metrics.items() if not isinstance(value, bool)}
    gate3_payload = payload.get("gate3", {})
    if isinstance(gate3_payload, Mapping):
        metrics.update(_numeric_items(gate3_payload.get("ablation", {}), "gate3.ablation"))
        metrics.update(_numeric_items(gate3_payload.get("failure_mode", {}), "gate3.failure_mode"))
    report = RealSmokeResult(dict(real_metrics), {}, evidence=ClaimGateEvidence(public_data_smoke=True)) if isinstance(real_metrics, Mapping) else None
    return write_results(
        PROJECT_ID,
        dataset_card_id([str(config.st_path)]),
        metrics,
        outputs=outputs,
        run_metadata=_metadata(config, report, notes="gate-3 ablation/failure emitted through the vendored results contract"),
        results_dir=results_dir,
    )
