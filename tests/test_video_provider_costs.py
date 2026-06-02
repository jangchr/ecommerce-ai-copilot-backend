import unittest

from fastapi.testclient import TestClient

from main import app
from video_generation.provider_costs import (
    estimate_video_generation_cost,
    video_provider_cost_catalog,
    video_provider_cost_level,
)


class VideoProviderCostsTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_catalog_contains_manual_and_paid_estimate_models(self):
        catalog = video_provider_cost_catalog()
        models = {item["model"] for item in catalog}

        self.assertIn("manual_export", models)
        self.assertIn("fal_pika_720p", models)
        self.assertIn("runway_gen4_turbo", models)
        self.assertIn("veo_fast", models)
        self.assertTrue(all(item["external_api_call_planned"] is False for item in catalog))

    def test_cost_level_thresholds(self):
        self.assertEqual(video_provider_cost_level(None), "unknown")
        self.assertEqual(video_provider_cost_level(0), "free")
        self.assertEqual(video_provider_cost_level(0.5), "low")
        self.assertEqual(video_provider_cost_level(2), "medium")
        self.assertEqual(video_provider_cost_level(8), "high")

    def test_manual_export_estimate_has_zero_cost_and_no_confirmation(self):
        estimate = estimate_video_generation_cost(
            provider="manual_export",
            model="manual_export",
            duration_seconds=20,
            clip_count=1,
            retry_count=1,
        )

        self.assertEqual(estimate["estimated_cost_usd"], 0)
        self.assertEqual(estimate["cost_level"], "free")
        self.assertFalse(estimate["requires_user_confirmation"])
        self.assertFalse(estimate["external_api_call_planned"])
        self.assertTrue(estimate["pricing_is_estimate"])
        self.assertIn("No external video API cost", " ".join(estimate["warnings"]))

    def test_paid_model_estimate_scales_by_duration_clips_and_retries(self):
        estimate = estimate_video_generation_cost(
            provider="pika",
            model="fal_pika_720p",
            duration_seconds=10,
            clip_count=2,
            retry_count=3,
            budget_usd=1,
        )

        self.assertEqual(estimate["estimated_billable_seconds"], 60)
        self.assertEqual(estimate["estimated_cost_usd"], 3.6)
        self.assertEqual(estimate["cost_level"], "medium")
        self.assertTrue(estimate["requires_user_confirmation"])
        self.assertFalse(estimate["external_api_call_planned"])
        self.assertFalse(estimate["within_budget"])
        self.assertIn("User confirmation", " ".join(estimate["warnings"]))

    def test_unknown_model_returns_unknown_safe_estimate(self):
        estimate = estimate_video_generation_cost(
            provider="unknown_tool",
            model="unknown_model",
            duration_seconds=5,
        )

        self.assertEqual(estimate["cost_level"], "unknown")
        self.assertIsNone(estimate["estimated_cost_usd"])
        self.assertFalse(estimate["external_api_call_planned"])
        self.assertTrue(estimate["requires_user_confirmation"])

    def test_cost_catalog_endpoint_returns_safe_estimate_catalog(self):
        response = self.client.get(
            "/api/v1/video-generation/cost/catalog",
            headers={"X-Request-ID": "video-cost-catalog-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-cost-catalog-1")
        self.assertTrue(payload["catalog"])
        self.assertNotIn("API_KEY", str(payload))

    def test_cost_estimate_endpoint_returns_estimate_only(self):
        response = self.client.post(
            "/api/v1/video-generation/cost/estimate",
            json={
                "provider": "runway",
                "model": "runway_gen4_turbo",
                "duration_seconds": 20,
                "clip_count": 1,
                "retry_count": 1,
                "budget_usd": 10,
            },
            headers={"X-Request-ID": "video-cost-estimate-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-cost-estimate-1")
        estimate = payload["estimate"]
        self.assertEqual(estimate["provider"], "runway")
        self.assertEqual(estimate["model"], "runway_gen4_turbo")
        self.assertTrue(estimate["pricing_is_estimate"])
        self.assertFalse(estimate["external_api_call_planned"])
        self.assertTrue(estimate["requires_user_confirmation"])


if __name__ == "__main__":
    unittest.main()
