import unittest

from spatial_regulatory_graph.comparison import build_survival_parity_table


class Gate2ParityTests(unittest.TestCase):
    def test_validated_tier_survival_is_compared_to_raw_top_edges(self):
        rows = [
            {"regulator": "A", "target": "B", "score": 0.9, "survives_controls": True, "tier": "validated"},
            {"regulator": "A", "target": "C", "score": 0.8, "survives_controls": False, "tier": "candidate"},
            {"regulator": "D", "target": "E", "score": 0.7, "survives_controls": False, "tier": "candidate"},
        ]
        table = build_survival_parity_table(rows)
        self.assertEqual(table["claim_status"], "locked")
        self.assertEqual(table["differentiator"]["validated_survival_rate"], 1.0)
        self.assertAlmostEqual(table["differentiator"]["raw_top_survival_rate"], 1 / 3, places=5)
        self.assertIn("failure_modes", table["missing_claim_evidence"])

    def test_evaluated_external_rows_use_their_own_control_survival(self):
        rows = [
            {"regulator": "A", "target": "B", "score": 0.9, "survives_controls": True, "tier": "validated"},
            {"regulator": "D", "target": "E", "score": 0.7, "survives_controls": False, "tier": "candidate"},
        ]
        external = [
            {"regulator": "X", "target": "Y", "survives_controls": False, "evaluated": True},
            {"regulator": "Q", "target": "R", "survives_controls": True, "evaluated": True},
            {"regulator": "M", "target": "N", "survives_controls": False, "evaluated": False},
        ]
        table = build_survival_parity_table(rows, reference_edge_rows=external)
        self.assertEqual(table["differentiator"]["external_survival_rate"], 0.5)
        self.assertEqual(table["differentiator"]["external_unmatched_edge_count"], 1)


if __name__ == "__main__":
    unittest.main()
