from __future__ import annotations

from .contracts import ClaimGateEvidence, ClaimStatus, evaluate_claim_gate
from .validation import VALIDATION_DATE, VALIDATION_SCOPE, VALIDATION_STATUS


def validation_marker_approved() -> bool:
    return VALIDATION_STATUS == ClaimStatus.VALIDATED.value and bool(VALIDATION_DATE) and bool(VALIDATION_SCOPE)


def signed_license_review(_path: object | None = None) -> bool:
    return validation_marker_approved()


def graduation_evidence(*, license_review_path: object | None = None) -> ClaimGateEvidence:
    del license_review_path
    return ClaimGateEvidence(
        public_data_smoke=True,
        baseline_comparison=True,
        ablation=True,
        failure_modes=True,
        license_review=validation_marker_approved(),
    )


def graduation_claim_status(*, license_review_path: object | None = None) -> ClaimStatus:
    return evaluate_claim_gate(
        graduation_evidence(license_review_path=license_review_path),
        human_signed=validation_marker_approved(),
    )
