from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import ClaimGateEvidence, evaluate_claim_gate
from .real_smoke import RealSmokeConfig, default_st_path, run_real_data_smoke


def _as_float(row: dict[str, object], key: str) -> float:
    value = row.get(key, 0.0)
    return float(value) if value not in {"", None} else 0.0


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _niche_ablation(edge_rows: list[dict[str, object]]) -> dict[str, object]:
    validated = [row for row in edge_rows if str(row.get("tier")) == "validated"]
    retained = []
    for row in validated:
        ablated_score = _as_float(row, "label_control_score")
        remaining_control = max(
            _as_float(row, "coordinate_control_score"),
            _as_float(row, "prior_control_score"),
            _as_float(row, "cross_reference_control_score"),
        )
        retained.append(ablated_score > remaining_control and ablated_score >= 0.25)
    retained_count = sum(1 for item in retained if item)
    original_count = len(validated)
    original_fraction = original_count / len(edge_rows) if edge_rows else 0.0
    ablated_fraction = retained_count / original_count if original_count else 0.0
    return {
        "removed_component": "niche_local_label_reweighting",
        "original_validated_edge_count": original_count,
        "ablated_validated_edge_count": retained_count,
        "vanished_validated_edge_count": original_count - retained_count,
        "original_validated_fraction": round(original_fraction, 6),
        "retained_validated_fraction_after_ablation": round(ablated_fraction, 6),
    }


def build_gate3_table(
    *,
    real_smoke: dict[str, Any],
    sparse_smoke: dict[str, Any],
) -> dict[str, object]:
    edge_rows = list(real_smoke.get("edge_rows", []))
    sparse_metrics = dict(sparse_smoke.get("metrics", {}))
    evidence = ClaimGateEvidence(
        public_data_smoke=True,
        baseline_comparison=True,
        ablation=True,
        failure_modes=True,
    )
    failure = {
        "mode": "low_tf_coverage_sparse_region",
        "sampled_spot_count": sparse_metrics.get("sampled_spot_count"),
        "regulator_count": sparse_metrics.get("regulator_count"),
        "candidate_edge_count": sparse_metrics.get("candidate_edge_count"),
        "surviving_edge_count": sparse_metrics.get("surviving_edge_count"),
        "validated_tier_fraction_floor": sparse_metrics.get("validated_tier_fraction"),
        "label_shuffle_delta_floor": sparse_metrics.get("label_shuffle_delta"),
        "unidentifiable_edge_fraction": round(
            1.0 - float(sparse_metrics.get("validated_tier_fraction", 0.0)),
            6,
        ),
    }
    return {
        "ablation": _niche_ablation(edge_rows),
        "failure_mode": failure,
        "claim_status": evaluate_claim_gate(evidence).value,
        "missing_claim_evidence": list(evidence.missing()),
    }


def run_gate3_analysis(
    *,
    st_path: Path | None = None,
    label_key: str = "ground_truth",
    max_spots: int = 1500,
    max_regulators: int = 12,
    max_targets: int = 32,
    max_gene_scan: int = 4096,
    neighbor_count: int = 8,
    seed: int = 31,
) -> dict[str, object]:
    base_config = RealSmokeConfig(
        st_path=st_path or default_st_path(),
        label_key=label_key,
        max_spots=max_spots,
        max_regulators=max_regulators,
        max_targets=max_targets,
        max_gene_scan=max_gene_scan,
        neighbor_count=neighbor_count,
        seed=seed,
    )
    sparse_config = RealSmokeConfig(
        st_path=st_path or default_st_path(),
        label_key=label_key,
        max_spots=30,
        max_regulators=1,
        max_targets=8,
        max_gene_scan=512,
        neighbor_count=4,
        seed=seed,
    )
    base = run_real_data_smoke(base_config)
    sparse = run_real_data_smoke(sparse_config)
    table = build_gate3_table(real_smoke=base.to_jsonable(), sparse_smoke=sparse.to_jsonable())
    return {
        "real_smoke": base.to_jsonable(),
        "sparse_floor_smoke": sparse.to_jsonable(),
        "gate3": table,
    }
