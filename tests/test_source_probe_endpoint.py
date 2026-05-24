import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from schemas.source_contract import SourceEvidence


class SourceProbeEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_default_probe_returns_disabled_real_shell_results(self):
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(side_effect=AssertionError("Probe endpoint must not run workflow.")),
        ):
            response = self.client.post(
                "/api/v1/debug-source-probe",
                json={"product_category": "printer"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["request_id"], response.headers["X-Request-ID"])
        self.assertTrue(payload["debug_only"])
        self.assertFalse(payload["memory_write_allowed"])
        self.assertTrue(payload["fallback_required"])
        self.assertEqual(len(payload["results"]), 3)
        self.assertIn("telemetry", payload)
        telemetry = payload["telemetry"]
        self.assertEqual(telemetry["provider_count"], 3)
        self.assertEqual(
            telemetry["disabled_count"]
            + telemetry["unavailable_count"]
            + telemetry["error_count"]
            + telemetry["success_count"],
            telemetry["provider_count"],
        )
        self.assertEqual(telemetry["fallback_required"], payload["fallback_required"])
        self.assertGreaterEqual(telemetry["total_latency_ms"], 0)

        results = {result["provider"]: result for result in payload["results"]}
        self.assertEqual(
            set(results),
            {"amazon_review_api", "tiktok_trend_api", "reddit_review_api"},
        )
        for provider, result in results.items():
            with self.subTest(provider=provider):
                self.assertIn(result["status"], {"disabled", "unavailable"})
                self.assertNotEqual(result["status"], "success")
                self.assertGreaterEqual(result["latency_ms"], 0)

    def test_probe_does_not_execute_local_or_mock_provider(self):
        with patch(
            "main.source_probe_registry.fetch",
            side_effect=AssertionError("Local/mock providers must not execute through the probe endpoint."),
        ) as fetch:
            response = self.client.post(
                "/api/v1/debug-source-probe",
                json={
                    "product_category": "printer",
                    "providers": ["local_review_dataset", "tiktok_trend_mock"],
                },
            )

        self.assertEqual(response.status_code, 200)
        fetch.assert_not_called()
        payload = response.json()
        self.assertTrue(payload["fallback_required"])
        self.assertTrue(all(item["status"] == "disabled" for item in payload["results"]))
        self.assertTrue(all(item["source_confidence"] == 0.0 for item in payload["results"]))
        self.assertEqual(payload["telemetry"]["provider_count"], 2)
        self.assertEqual(payload["telemetry"]["disabled_count"], 2)

    def test_amazon_probe_success_can_return_success_without_workflow(self):
        evidence = SourceEvidence(
            source_type="amazon_review_api",
            source_url="https://www.amazon.com/dp/B000TEST",
            product_category="balsamic_vinegar",
            confidence=0.75,
            review_confidence=0.75,
            review_count=1234,
            evidence_quotes=["The cap cracked during shipping and leaked all over the box."],
            metadata={
                "product_title": "Premium Balsamic Glaze",
                "rating": "4.4",
                "review_count": "1,234",
                "price": "$14.99",
                "category_hint": "Grocery",
                "bullet_points": ["Thick glaze for salads."],
            },
        )
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(side_effect=AssertionError("Probe endpoint must not run workflow.")),
        ), patch("main.source_probe_registry.fetch", return_value=evidence):
            response = self.client.post(
                "/api/v1/debug-source-probe",
                json={
                    "product_category": "balsamic_vinegar",
                    "url": "https://www.amazon.com/dp/B000TEST",
                    "providers": ["amazon_review_api"],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["memory_write_allowed"])
        self.assertFalse(payload["fallback_required"])
        self.assertEqual(payload["telemetry"]["success_count"], 1)
        result = payload["results"][0]
        self.assertEqual(result["provider"], "amazon_review_api")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_confidence"], 0.75)
        self.assertIn("cap cracked", result["evidence_preview"][0])
        self.assertEqual(result["metadata"]["product_title"], "Premium Balsamic Glaze")


if __name__ == "__main__":
    unittest.main()
