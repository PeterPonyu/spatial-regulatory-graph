import tempfile
import unittest
from pathlib import Path

from spatial_regulatory_graph.contracts import ClaimGateEvidence
from spatial_regulatory_graph.data_paths import find_repo_root, processed_data_path
from spatial_regulatory_graph.real_smoke import RealSmokeConfig, RealSmokeResult, _safe_corr, _tier


class RealDataSmokeUnitTests(unittest.TestCase):
    def test_result_keeps_claim_locked(self):
        result = RealSmokeResult({"surviving_edge_count": 1.0}, {"candidate": 0, "supported": 1, "validated": 0}, ClaimGateEvidence(public_data_smoke=True))
        self.assertEqual(result.claim_status.value, "locked")
        self.assertEqual(
            result.to_jsonable()["missing_claim_evidence"],
            ["baseline_comparison", "ablation", "failure_modes", "license_review"],
        )

    def test_config_rejects_tiny_sample(self):
        with self.assertRaises(ValueError):
            RealSmokeConfig(st_path=Path("fixture.h5ad"), max_spots=4).validate()

    def test_repo_root_path_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "processed").mkdir(parents=True)
            anchor = root / "src" / "package" / "module.py"
            anchor.parent.mkdir(parents=True)
            anchor.touch()
            self.assertEqual(find_repo_root(anchor), root)
            self.assertEqual(
                processed_data_path("fixture_card", anchor=anchor),
                root / "data" / "processed" / "fixture_card",
            )

    def test_corr_and_tier_helpers(self):
        self.assertAlmostEqual(_safe_corr([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)
        self.assertEqual(_tier(0.3, True), "validated")


if __name__ == "__main__":
    unittest.main()
