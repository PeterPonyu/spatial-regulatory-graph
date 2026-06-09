import unittest
from spatial_regulatory_graph import EvidenceTier, RegulatoryEdge, assign_tier, normalize_external_edge_rows, run_synthetic_smoke

class ControlTests(unittest.TestCase):
    def test_expression_only_edge_is_not_validated(self):
        edge = RegulatoryEdge("TF", "G", "coexpression_candidate", 0.8, "unknown", evidence_used=("expression",))
        self.assertEqual(assign_tier(edge, survives_controls=True), EvidenceTier.CANDIDATE)
    def test_smoke_reports_control_deltas(self):
        report = run_synthetic_smoke()
        self.assertEqual(report.claim_status.value, "locked")
        self.assertGreater(report.coordinate_shuffle_delta, 0.5)
        self.assertGreaterEqual(report.surviving_edges_by_tier.get("validated", 0), 1)
    def test_external_adapter_reads_neutral_rows(self):
        edges = normalize_external_edge_rows([{"regulator": "TF", "target": "G", "score": 0.7}])
        self.assertEqual(edges[0].score, 0.7)

if __name__ == "__main__":
    unittest.main()
