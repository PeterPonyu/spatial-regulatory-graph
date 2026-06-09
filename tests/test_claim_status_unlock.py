from __future__ import annotations

import unittest

from spatial_regulatory_graph.claim_status import (
    graduation_claim_status,
    graduation_evidence,
    signed_license_review,
    validation_marker_approved,
)
from spatial_regulatory_graph.contracts import ClaimStatus


class ClaimStatusUnlockTests(unittest.TestCase):
    def test_committed_validation_marker_unlocks_programmatic_status(self):
        self.assertTrue(validation_marker_approved())
        self.assertTrue(signed_license_review())
        evidence = graduation_evidence()
        self.assertEqual(evidence.missing(), ())
        self.assertEqual(graduation_claim_status(), ClaimStatus.VALIDATED)

    def test_claim_status_does_not_require_governance_docs(self):
        self.assertEqual(graduation_claim_status().value, "validated")


if __name__ == "__main__":
    unittest.main()
