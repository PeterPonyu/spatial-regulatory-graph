import unittest

from spatial_regulatory_graph.gate3 import build_gate3_table


class Gate3AnalysisTests(unittest.TestCase):
    def test_ablation_and_failure_modes_reduce_missing_claim_evidence(self):
        real_smoke = {
            "edge_rows": [
                {
                    "tier": "validated",
                    "label_control_score": 0.20,
                    "coordinate_control_score": 0.10,
                    "prior_control_score": 0.10,
                    "cross_reference_control_score": 0.10,
                },
                {
                    "tier": "validated",
                    "label_control_score": 0.30,
                    "coordinate_control_score": 0.20,
                    "prior_control_score": 0.10,
                    "cross_reference_control_score": 0.10,
                },
            ]
        }
        sparse_smoke = {
            "metrics": {
                "sampled_spot_count": 30.0,
                "regulator_count": 1.0,
                "candidate_edge_count": 8.0,
                "surviving_edge_count": 1.0,
                "validated_tier_fraction": 0.125,
                "label_shuffle_delta": -0.03,
            }
        }
        table = build_gate3_table(real_smoke=real_smoke, sparse_smoke=sparse_smoke)
        self.assertEqual(table["claim_status"], "locked")
        self.assertEqual(table["missing_claim_evidence"], ["license_review"])
        self.assertEqual(table["ablation"]["vanished_validated_edge_count"], 1)
        self.assertEqual(table["failure_mode"]["validated_tier_fraction_floor"], 0.125)


if __name__ == "__main__":
    unittest.main()
