import asyncio
import unittest

from core.workflow import retrieval_node, tool_runtime
from scripts.run_debug_tests import telemetry_node_aggregate, telemetry_rows
from source_adapters import SourceAdapterRegistry


class SourceAdapterRegistryTest(unittest.TestCase):
    def setUp(self):
        self.registry = SourceAdapterRegistry()

    def test_default_enabled_tools_keep_regression_anchor(self):
        self.assertEqual(
            set(self.registry.enabled_tools()),
            {"local_review_dataset", "tiktok_trend_mock"},
        )

    def test_real_source_adapters_are_disabled_shells(self):
        for tool_name in ["amazon_review_api", "tiktok_trend_api", "reddit_review_api"]:
            self.assertFalse(self.registry.is_enabled(tool_name))
            evidence = self.registry.fetch(tool_name, "https://test.local/product", "printer")
            self.assertEqual(evidence.source_type, "unavailable")
            self.assertEqual(evidence.confidence, 0.0)

    def test_registry_can_fetch_enabled_local_source(self):
        evidence = self.registry.fetch(
            "local_review_dataset",
            "https://test.local/products/printer",
            "printer",
        )
        self.assertEqual(evidence.source_type, "local_review_dataset")
        self.assertGreaterEqual(evidence.review_count, 5)

    def test_registry_fetch_trace_exposes_adapter_latency_and_confidence(self):
        evidence, trace = self.registry.fetch_with_trace(
            "local_review_dataset",
            "https://test.local/products/printer",
            "printer",
            fallback_reason="real_source_unavailable",
        )
        self.assertEqual(evidence.source_type, "local_review_dataset")
        self.assertEqual(trace["source_name"], "local_review_dataset")
        self.assertEqual(trace["adapter_name"], "LocalReviewAdapter")
        self.assertTrue(trace["enabled"])
        self.assertTrue(trace["fallback"])
        self.assertEqual(trace["fallback_reason"], "real_source_unavailable")
        self.assertGreaterEqual(trace["fetch_latency_ms"], 0)
        self.assertEqual(trace["confidence"], 0.75)


class ToolRuntimeDisabledSourceTest(unittest.TestCase):
    def test_real_tool_routes_remain_unavailable(self):
        for tool_name in ["amazon_review_api", "tiktok_trend_api", "reddit_review_api"]:
            source = asyncio.run(
                tool_runtime.run(
                    tool_name,
                    {
                        "url": "https://test.local/products/printer",
                        "env_state": {"product_category": "printer"},
                    },
                )
            )
            self.assertEqual(source.source_type, "unavailable")
            self.assertEqual(source.items, [])

    def test_unavailable_real_sources_fall_back_to_regression_anchors(self):
        result = asyncio.run(
            retrieval_node(
                {
                    "env_state": {
                        "asin_url": "https://test.local/products/printer",
                        "product_category": "printer",
                        "selected_tools": [
                            "amazon_review_api",
                            "local_review_dataset",
                            "tiktok_trend_api",
                            "tiktok_trend_mock",
                        ],
                    },
                    "cognitive_state": {},
                    "execution_state": {},
                    "telemetry_state": {},
                    "world_metrics": {},
                    "revision_count": 0,
                    "next_nodes": [],
                }
            )
        )
        env = result["env_state"]
        source_types = [source["source_type"] for source in env["tool_sources"]]

        self.assertIn("unavailable", source_types)
        self.assertIn("local_dataset", source_types)
        self.assertIn("mock", source_types)
        self.assertGreaterEqual(len(env["raw_reviews"]), 5)
        self.assertTrue(env["trend_signals"])
        traces = result["telemetry_state"]["retrieval_sources"]["source_traces"]
        memory = result["telemetry_state"]["retrieval_sources"]
        review_fallback = next(trace for trace in traces if trace["source_name"] == "local_review_dataset")
        trend_fallback = next(trace for trace in traces if trace["source_name"] == "tiktok_trend_mock")
        self.assertTrue(review_fallback["fallback"])
        self.assertEqual(review_fallback["fallback_reason"], "review_real_source_unavailable")
        self.assertTrue(trend_fallback["fallback"])
        self.assertEqual(trend_fallback["fallback_reason"], "trend_real_source_unavailable")
        self.assertIn("memory_record_count_total", memory)
        self.assertIn("memory_backend", memory)
        self.assertIn("memory_faiss_error", memory)

        rows = telemetry_rows("printer", {"telemetry": result["telemetry_state"]})
        retrieval_row = next(row for row in rows if row["node"] == "retrieval_sources")
        aggregate = next(
            row for row in telemetry_node_aggregate(rows) if row["node"] == "retrieval_sources"
        )
        self.assertIn("LocalReviewAdapter", retrieval_row["adapter_names"])
        self.assertIn("review_real_source_unavailable", retrieval_row["adapter_fallback_reason"])
        self.assertIn("local_review_dataset", aggregate["source_names"])
        self.assertIn("review_real_source_unavailable", aggregate["adapter_fallback_reasons"])
        self.assertGreaterEqual(aggregate["adapter_fallback_count"], 2)


if __name__ == "__main__":
    unittest.main()
