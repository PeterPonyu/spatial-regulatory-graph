from __future__ import annotations

from typing import Any

from .contracts import ClaimGateEvidence, ClaimStatus, evaluate_claim_gate
from .validation import load_evidence_summary


def _summary() -> dict[str, Any]:
    try:
        return load_evidence_summary()
    except FileNotFoundError:
        return {}


def _gate_evidence(summary: dict[str, Any]) -> dict[str, bool]:
    gates = summary.get("claim_gate_evidence", {})
    if not isinstance(gates, dict):
        return {}
    return {str(key): bool(value) for key, value in gates.items()}


def missing_evidence() -> tuple[str, ...]:
    missing = _summary().get("missing_evidence", ())
    if not isinstance(missing, list | tuple):
        return ()
    return tuple(str(item) for item in missing)


def validation_marker_approved() -> bool:
    summary = _summary()
    bar = summary.get("validation_bar", {})
    return bool(isinstance(bar, dict) and bar.get("met") is True and not missing_evidence())


def signed_license_review(_path: object | None = None) -> bool:
    return validation_marker_approved()


def graduation_evidence(*, license_review_path: object | None = None) -> ClaimGateEvidence:
    del license_review_path
    gates = _gate_evidence(_summary())
    return ClaimGateEvidence(
        public_data_smoke=gates.get("public_data_smoke", False),
        baseline_comparison=gates.get("baseline_comparison", False),
        ablation=gates.get("ablation", False),
        failure_modes=gates.get("failure_modes", False),
        license_review=gates.get("license_review", False),
    )


def graduation_claim_status(*, license_review_path: object | None = None) -> ClaimStatus:
    summary = _summary()
    evidence = graduation_evidence(license_review_path=license_review_path)
    if validation_marker_approved():
        return evaluate_claim_gate(evidence, human_signed=True)
    bar = summary.get("validation_bar", {})
    if summary and (missing_evidence() or (isinstance(bar, dict) and bar.get("met") is False)):
        return ClaimStatus.PRELIMINARY
    return evaluate_claim_gate(evidence, human_signed=False)


def graduation_claim_status_line() -> str:
    status = graduation_claim_status().value
    missing = missing_evidence()
    if missing:
        return f"{status} missing={','.join(missing)}"
    return status
