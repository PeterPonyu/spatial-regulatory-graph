import unittest
from spatial_regulatory_graph import ClaimGateEvidence, ClaimStatus, RegulatoryEdge, evaluate_claim_gate

class EdgeContractTests(unittest.TestCase):
    def test_claim_lock(self):
        self.assertEqual(evaluate_claim_gate(ClaimGateEvidence(ablation=True)), ClaimStatus.LOCKED)
    def test_edge_contract(self):
        edge = RegulatoryEdge("TF", "G", "tf_target", 0.5, "unknown")
        self.assertEqual(edge.target, "G")

if __name__ == "__main__":
    unittest.main()
