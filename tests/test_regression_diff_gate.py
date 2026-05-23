import unittest

from scripts.run_debug_tests import MIN_GROUNDED_CTR, result_row


def result_data(grounded_ctr: float) -> dict:
    return {
        "product_category": "phone_case",
        "evidence": {
            "source_type": "local_dataset+mock",
            "review_confidence": 0.75,
            "trend_confidence": 0.35,
            "review_count": 6,
        },
        "world_metrics": {
            "grounded_ctr": grounded_ctr,
            "evidence_alignment": 1.0,
            "is_grounded": grounded_ctr >= MIN_GROUNDED_CTR,
        },
        "revision_count": 0,
    }


class RegressionDiffGateTest(unittest.TestCase):
    def test_large_relative_drop_is_warning_when_absolute_grounded_gate_passes(self):
        row = result_row(
            "phone_case",
            result_data(0.0500),
            {"grounded_ctr": "0.0716", "evidence_alignment": "1.0", "revision_count": "0"},
        )

        self.assertEqual(row["diff_status"], "WARN")
        self.assertIn("grounded_ctr dropped", row["diff_warning"])

    def test_large_relative_drop_remains_failure_below_absolute_gate(self):
        row = result_row(
            "phone_case",
            result_data(0.0390),
            {"grounded_ctr": "0.0716", "evidence_alignment": "1.0", "revision_count": "0"},
        )

        self.assertEqual(row["diff_status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
