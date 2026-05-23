import asyncio
import unittest

from core.workflow import tool_runtime
from source_adapters.local_review_adapter import LocalReviewAdapter
from source_adapters.mock_trend_adapter import MockTrendAdapter


class LocalReviewAdapterTest(unittest.TestCase):
    def test_reads_grounded_balsamic_dataset(self):
        evidence = LocalReviewAdapter().fetch(
            "https://test.local/products/balsamic_vinegar",
            "balsamic_vinegar",
        )

        self.assertEqual(evidence.source_type, "local_review_dataset")
        self.assertEqual(evidence.review_confidence, 0.75)
        self.assertGreaterEqual(evidence.review_count, 5)
        self.assertTrue(evidence.evidence_quotes)

    def test_unknown_product_returns_unavailable(self):
        evidence = LocalReviewAdapter().fetch(
            "https://test.local/products/unknown_product",
            "unknown_product",
        )

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertEqual(evidence.review_confidence, 0.0)
        self.assertIn("missing_local_review_dataset", evidence.data_warnings)


class MockTrendAdapterTest(unittest.TestCase):
    def test_returns_stable_trend_signals(self):
        evidence = MockTrendAdapter().fetch(
            "https://test.local/products/phone_case",
            "phone_case",
        )

        self.assertEqual(evidence.source_type, "mock_trend_adapter")
        self.assertEqual(evidence.trend_confidence, 0.35)
        self.assertTrue(evidence.trend_signals)


class ToolRuntimeAdapterBridgeTest(unittest.TestCase):
    def test_local_review_tool_preserves_workflow_contract(self):
        source = asyncio.run(
            tool_runtime.run(
                "local_review_dataset",
                {
                    "url": "https://test.local/products/balsamic_vinegar",
                    "env_state": {"product_category": "food"},
                },
            )
        )

        self.assertEqual(source.source_type, "local_dataset")
        self.assertEqual(source.source_role, "review")
        self.assertGreaterEqual(len(source.items), 5)

    def test_mock_trend_tool_uses_adapter_signals(self):
        source = asyncio.run(
            tool_runtime.run(
                "tiktok_trend_mock",
                {
                    "url": "https://test.local/products/phone_case",
                    "env_state": {"product_category": "phone_case"},
                },
            )
        )

        self.assertEqual(source.source_type, "mock")
        self.assertEqual(source.source_role, "trend")
        self.assertTrue(source.items)


if __name__ == "__main__":
    unittest.main()
