from __future__ import annotations
from .contracts import ClaimGateEvidence, NegativeControlReport, RegulatoryEdge
from .tiering import assign_tier


def build_edges() -> list[RegulatoryEdge]:
    return [
        RegulatoryEdge("TF_A", "GENE_X", "tf_target", 0.94, "activation", niche="niche_1", evidence_used=("expression", "spatial_stability", "orthogonal_support"), uncertainty=0.05),
        RegulatoryEdge("TF_B", "GENE_Y", "coexpression_candidate", 0.41, "unknown", evidence_used=("expression",), uncertainty=0.3),
        RegulatoryEdge("TF_C", "GENE_Z", "prior_only", 0.33, "unknown", evidence_used=("prior_support",), uncertainty=0.4),
    ]


def run_synthetic_smoke() -> NegativeControlReport:
    edges = build_edges()
    tiers = [assign_tier(e, survives_controls=e.regulator == "TF_A") for e in edges]
    counts = {tier.value: tiers.count(tier) for tier in set(tiers)}
    return NegativeControlReport(0.72, 0.51, 0.44, counts, ClaimGateEvidence(ablation=True, failure_modes=True))
