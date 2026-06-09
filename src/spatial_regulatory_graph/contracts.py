from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimStatus(str, Enum):
    LOCKED = "locked"
    PRELIMINARY = "preliminary"
    REVIEW_READY = "review_ready"
    VALIDATED = "validated"


@dataclass(frozen=True)
class ClaimGateEvidence:
    public_data_smoke: bool = False
    baseline_comparison: bool = False
    ablation: bool = False
    failure_modes: bool = False
    license_review: bool = False

    def missing(self) -> tuple[str, ...]:
        required = {
            "public_data_smoke": self.public_data_smoke,
            "baseline_comparison": self.baseline_comparison,
            "ablation": self.ablation,
            "failure_modes": self.failure_modes,
            "license_review": self.license_review,
        }
        return tuple(name for name, present in required.items() if not present)


def evaluate_claim_gate(evidence: ClaimGateEvidence, *, human_signed: bool = False) -> ClaimStatus:
    if evidence.missing():
        return ClaimStatus.LOCKED
    return ClaimStatus.VALIDATED if human_signed else ClaimStatus.REVIEW_READY



class EvidenceTier(str, Enum):
    CANDIDATE = "candidate"
    SUPPORTED = "supported"
    VALIDATED = "validated"


@dataclass(frozen=True)
class RegulatoryEdge:
    regulator: str
    target: str
    edge_type: str
    score: float
    sign: str
    cell_type: str | None = None
    niche: str | None = None
    evidence_used: tuple[str, ...] = ()
    uncertainty: float | None = None


@dataclass(frozen=True)
class NegativeControlReport:
    coordinate_shuffle_delta: float
    cell_label_shuffle_delta: float
    prior_shuffle_delta: float
    surviving_edges_by_tier: dict[str, int]
    evidence: ClaimGateEvidence

    @property
    def claim_status(self) -> ClaimStatus:
        return evaluate_claim_gate(self.evidence)
