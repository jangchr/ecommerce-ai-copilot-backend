import unittest

from core.telemetry_utils import summarize_telemetry


class TelemetryUtilsTest(unittest.TestCase):
    def test_empty_telemetry_returns_zero_summary(self):
        self.assertEqual(
            summarize_telemetry({}),
            {
                "node_count": 0,
                "total_tokens": 0,
                "total_latency_ms": 0.0,
                "failed_nodes": [],
                "max_latency_node": None,
                "max_token_node": None,
            },
        )

    def test_summary_aggregates_metrics_and_identifies_hotspots_and_failure(self):
        summary = summarize_telemetry(
            {
                "strategy": {
                    "status": "success",
                    "total_tokens": 44,
                    "latency_ms": 20.0,
                },
                "storyboard": {
                    "status": "error",
                    "total_tokens": 30,
                    "latency_ms": 51.0,
                },
            }
        )

        self.assertEqual(summary["node_count"], 2)
        self.assertEqual(summary["total_tokens"], 74)
        self.assertEqual(summary["total_latency_ms"], 71.0)
        self.assertEqual(summary["failed_nodes"], ["storyboard"])
        self.assertEqual(summary["max_latency_node"], "storyboard")
        self.assertEqual(summary["max_token_node"], "strategy")


if __name__ == "__main__":
    unittest.main()
