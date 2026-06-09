from __future__ import annotations
from .contracts import EvidenceTier, RegulatoryEdge


def assign_tier(edge: RegulatoryEdge, *, survives_controls: bool) -> EvidenceTier:
    evidence = set(edge.evidence_used)
    if survives_controls and {"expression", "spatial_stability", "orthogonal_support"}.issubset(evidence):
        return EvidenceTier.VALIDATED
    if "expression" in evidence and ("spatial_stability" in evidence or "prior_support" in evidence):
        return EvidenceTier.SUPPORTED
    return EvidenceTier.CANDIDATE
