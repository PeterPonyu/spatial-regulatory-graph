import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from spatial_regulatory_graph.contracts import ClaimGateEvidence
from spatial_regulatory_graph.real_smoke import RealSmokeConfig, RealSmokeResult
from spatial_regulatory_graph.result_wiring import emit_gate2_results


class ResultsContractWiringTests(unittest.TestCase):
    def test_vendored_contract_matches_recorded_sha256(self):
        package_dir = Path(__file__).resolve().parents[1] / "src" / "spatial_regulatory_graph"
        contract_path = package_dir / "results_contract.py"
        expected = (package_dir / "results_contract.sha256").read_text(encoding="utf-8").strip().split()[0]
        observed = hashlib.sha256(contract_path.read_bytes()).hexdigest()
        self.assertEqual(observed, expected)

    def test_gate2_emits_contract_files(self):
        report = RealSmokeResult(
            metrics={
                "sampled_spot_count": 10.0,
                "target_count": 4.0,
                "validated_tier_fraction": 0.5,
            },
            tier_counts={"candidate": 1, "supported": 1, "validated": 2},
            evidence=ClaimGateEvidence(public_data_smoke=True),
        )
        parity = {"differentiator": {"validated_survival_rate": 1.0, "external_survival_rate": 0.25}}
        config = RealSmokeConfig(st_path=Path("data/processed/example/anndata.h5ad"), max_spots=30)
        with tempfile.TemporaryDirectory() as tmp:
            paths = emit_gate2_results(report, parity, config, results_dir=Path(tmp))
            metrics = json.loads(paths["metrics"].read_text(encoding="utf-8"))
            self.assertEqual(metrics["project"], "spatial-regulatory-graph")
            self.assertEqual(metrics["metrics"]["gate2.validated_survival_rate"], 1.0)
            self.assertTrue(paths["run_metadata"].is_file())


if __name__ == "__main__":
    unittest.main()
