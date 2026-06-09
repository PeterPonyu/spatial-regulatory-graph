from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .contracts import ClaimGateEvidence, ClaimStatus, evaluate_claim_gate


def write_edge_rows(path: Path, edge_rows: list[dict[str, object]] | tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    base_fields = [
        "rank",
        "source_rank",
        "regulator",
        "target",
        "reference_score",
        "score",
        "coordinate_control_score",
        "label_control_score",
        "prior_control_score",
        "cross_reference_control_score",
        "survives_controls",
        "tier",
        "evaluated",
        "missing_reason",
    ]
    extra_fields = sorted({str(key) for row in edge_rows for key in row if str(key) not in base_fields})
    fields = [field for field in base_fields if any(field in row for row in edge_rows)] + extra_fields
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in edge_rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_edge_rows(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _rate(rows: list[dict[str, object]]) -> float | None:
    if not rows:
        return None
    return round(sum(1 for row in rows if _truthy(row.get("survives_controls", False))) / len(rows), 6)


def _top_rows(edge_rows: list[dict[str, object]], top_n: int | None) -> list[dict[str, object]]:
    ordered = sorted(edge_rows, key=lambda row: float(row.get("score", 0.0)), reverse=True)
    return ordered if top_n is None else ordered[:top_n]


def _matched_reference_rows(
    edge_rows: list[dict[str, object]],
    reference_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], int]:
    indexed = {(str(row.get("regulator")), str(row.get("target"))): row for row in edge_rows}
    matched: list[dict[str, object]] = []
    missing = 0
    for row in reference_rows:
        key = (str(row.get("regulator")), str(row.get("target")))
        if key in indexed:
            matched.append(indexed[key])
        else:
            missing += 1
    return matched, missing


def _evaluated_reference_rows(reference_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], int, bool]:
    if not reference_rows:
        return [], 0, False
    carries_control_scores = any("survives_controls" in row for row in reference_rows)
    carries_evaluation_flag = any("evaluated" in row for row in reference_rows)
    if not (carries_control_scores or carries_evaluation_flag):
        return [], len(reference_rows), False
    evaluated = [row for row in reference_rows if _truthy(row.get("evaluated", True))]
    return evaluated, len(reference_rows) - len(evaluated), True


def build_survival_parity_table(
    edge_rows: list[dict[str, object]] | tuple[dict[str, object], ...],
    *,
    reference_edge_rows: list[dict[str, object]] | None = None,
    top_n: int | None = None,
) -> dict[str, object]:
    evidence = ClaimGateEvidence(public_data_smoke=True, baseline_comparison=True)
    rows = list(edge_rows)
    validated = [row for row in rows if str(row.get("tier")) == "validated"]
    raw_top = _top_rows(rows, top_n)
    validated_rate = _rate(validated)
    raw_top_rate = _rate(raw_top)
    parity_rows: list[dict[str, object]] = [
        {
            "method_id": "local_validated_tier",
            "provenance": "RAN",
            "edge_count": len(validated),
            "survival_rate": validated_rate,
        },
        {
            "method_id": "local_raw_top_edges",
            "provenance": "RAN",
            "edge_count": len(raw_top),
            "survival_rate": raw_top_rate,
        },
    ]
    reference_rate = None
    reference_missing = None
    if reference_edge_rows is not None:
        matched, missing, evaluated_in_place = _evaluated_reference_rows(reference_edge_rows)
        if not evaluated_in_place:
            matched, missing = _matched_reference_rows(rows, reference_edge_rows)
        reference_rate = _rate(matched)
        reference_missing = missing
        parity_rows.append(
            {
                "method_id": "external_top_edges",
                "provenance": "RAN",
                "edge_count": len(reference_edge_rows),
                "evaluated_edge_count": len(matched),
                "unevaluated_edge_count": missing,
                "survival_rate": reference_rate,
            }
        )
    gap = None
    if validated_rate is not None and raw_top_rate is not None:
        gap = round(validated_rate - raw_top_rate, 6)
    return {
        "rows": parity_rows,
        "differentiator": {
            "validated_survival_rate": validated_rate,
            "raw_top_survival_rate": raw_top_rate,
            "validated_minus_raw_top": gap,
            "external_survival_rate": reference_rate,
            "external_unmatched_edge_count": reference_missing,
        },
        "claim_status": evaluate_claim_gate(evidence).value,
        "missing_claim_evidence": list(evidence.missing()),
    }


def assert_locked_after_gate2(table: dict[str, Any]) -> ClaimStatus:
    status = ClaimStatus(str(table["claim_status"]))
    if status != ClaimStatus.LOCKED:
        raise AssertionError("gate-2 parity must not unlock claims")
    return status
