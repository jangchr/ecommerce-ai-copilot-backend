import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


VALID_REVIEWS_REQUEST = {
    "product_name": "Portable Mini Blender",
    "product_category": "kitchen_appliance",
    "product_description": "A compact rechargeable blender for smoothies and travel.",
    "pasted_reviews": (
        "Hard to clean after one smoothie.\n"
        "Too loud for early mornings.\n"
        "Small enough for travel but the cup sometimes leaks in my bag."
    ),
}


GENERATED_REVIEWS_BRIEF = {
    "target_audience": "Busy smoothie drinkers who want single-serve convenience.",
    "core_hook_strategy": "Open with the cleanup frustration and contrast it with a quick rinse routine.",
    "emotional_trigger": "Relief from noisy, messy morning prep.",
    "hook": "Your blender should not make one smoothie feel like a full kitchen cleanup.",
    "cta": "Try a compact blender built around quick daily use.",
    "storyboard_scenes": [
        {
            "visual_description": "A sink full of blender parts after one drink.",
            "narration": "One smoothie should not create this much cleanup.",
            "evidence_quote_used": "Hard to clean after one smoothie.",
        },
        {
            "visual_description": "A person hesitates before blending early in the morning.",
            "narration": "The noise makes the routine feel harder.",
            "evidence_quote_used": "Too loud for early mornings.",
        },
        {
            "visual_description": "The compact cup slides into a backpack pocket.",
            "narration": "A smaller setup makes the habit easier to keep.",
            "evidence_quote_used": "Small enough for travel.",
        },
        {
            "visual_description": "The product is rinsed quickly after a shake.",
            "narration": "Make the daily drink feel simple again.",
            "evidence_quote_used": "Hard to clean after one smoothie.",
        },
    ],
    "evaluation_reasoning": "Grounded in pasted customer complaint snippets.",
    "feedback": "Verify pasted reviews before paid use.",
}


ZH_REVIEWS_DATA = {
    "insights": {
        "pain_points": ["\u6e05\u6d17\u9ebb\u70e6", "\u65e9\u4e0a\u592a\u5435"],
        "user_complaint_cluster": ["\u6e05\u6d17\u9ebb\u70e6"],
        "evidence": {
            "source_type": "user_pasted_reviews",
            "source_url": "",
            "confidence": 0.64,
            "review_confidence": 0.64,
            "trend_confidence": 0.0,
            "review_count": 3,
            "evidence_quotes": ["\u4e00\u676f\u679c\u6614\u540e\u5f88\u96be\u6e05\u6d17"],
            "trend_signals": [],
            "data_warnings": [
                "user_pasted_reviews_unverified",
                "user_pasted_reviews_no_external_fetch",
            ],
        },
    },
    "audience": {
        "primary": "\u9700\u8981\u5feb\u901f\u505a\u679c\u6614\u7684\u5fd9\u788c\u7528\u6237",
        "sensitivity": "\u6015\u9ebb\u70e6",
        "trust_barriers": ["\u62c5\u5fc3\u6e05\u6d17"],
    },
    "strategy": {
        "core_hook_strategy": "\u7528\u6e05\u6d17\u75db\u70b9\u505a\u5f00\u573a",
        "emotional_trigger": "\u4ece\u9ebb\u70e6\u5230\u8f7b\u677e",
    },
    "assets": {
        "tiktok_script": {
            "hook": "\u8fd9\u662f\u6765\u81ea\u7c98\u8d34\u8bc4\u8bba\u7684\u4e2d\u6587 Hook",
            "cta": "\u8bd5\u8bd5\u66f4\u8f7b\u677e\u7684\u679c\u6614\u65b9\u5f0f",
        },
        "storyboard": {
            "source": "user_pasted_reviews",
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_description": "\u5c55\u793a\u6e05\u6d17\u9ebb\u70e6",
                    "narration": "\u4e00\u676f\u679c\u6614\u4e0d\u5e94\u8be5\u8fd9\u4e48\u9ebb\u70e6",
                    "evidence_quote_used": "\u4e00\u676f\u679c\u6614\u540e\u5f88\u96be\u6e05\u6d17",
                }
            ],
        },
    },
    "evaluation": {
        "confidence_score": 0.66,
        "risk_level": "medium",
        "reasoning": "\u57fa\u4e8e\u7c98\u8d34\u8bc4\u8bba\u751f\u6210",
        "is_approved": True,
        "is_grounded": True,
        "creative_approved": True,
        "grounded_approved": True,
    },
    "feedback": "\u4f7f\u7528\u524d\u8bf7\u6838\u5b9e\u8bc4\u8bba\u771f\u5b9e\u6027",
}


class PastedReviewsEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_success_returns_product_like_response_from_pasted_reviews(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json=VALID_REVIEWS_REQUEST,
                headers={"X-Request-ID": "reviews-success-1"},
            )

        self.assertEqual(response.status_code, 200)
        generate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["output_language"], "en")
        self.assertEqual(payload["request_id"], "reviews-success-1")
        for field in ["insights", "audience", "strategy", "assets", "evaluation", "feedback"]:
            with self.subTest(field=field):
                self.assertIn(field, payload["data"])

        evidence = payload["data"]["insights"]["evidence"]
        self.assertEqual(evidence["source_type"], "user_pasted_reviews")
        self.assertEqual(evidence["source_url"], "")
        self.assertEqual(evidence["review_count"], 3)
        self.assertIn("Hard to clean", evidence["evidence_quotes"][0])
        self.assertIn("user_pasted_reviews_unverified", evidence["data_warnings"])
        self.assertIn("user_pasted_reviews_no_external_fetch", evidence["data_warnings"])
        self.assertEqual(payload["data"]["assets"]["storyboard"]["source"], "user_pasted_reviews")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_explicit_english_language_succeeds(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ):
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "en"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["output_language"], "en")

    def test_chinese_language_translates_visible_product_payload(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ), patch(
            "main.translate_product_visible_data",
            new=AsyncMock(return_value=ZH_REVIEWS_DATA),
        ) as translate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "zh-CN"},
            )

        self.assertEqual(response.status_code, 200)
        translate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["output_language"], "zh-CN")
        self.assertIn("\u4e2d\u6587", payload["data"]["assets"]["tiktok_script"]["hook"])
        self.assertEqual(payload["data"]["insights"]["evidence"]["source_type"], "user_pasted_reviews")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_missing_product_name_returns_400(self):
        response = self.client.post(
            "/api/v1/generate-from-reviews",
            json={**VALID_REVIEWS_REQUEST, "product_name": " "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "missing_product_name")

    def test_missing_pasted_reviews_returns_400(self):
        response = self.client.post(
            "/api/v1/generate-from-reviews",
            json={**VALID_REVIEWS_REQUEST, "pasted_reviews": ""},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "missing_pasted_reviews")

    def test_short_pasted_reviews_returns_400(self):
        response = self.client.post(
            "/api/v1/generate-from-reviews",
            json={**VALID_REVIEWS_REQUEST, "pasted_reviews": "Too loud."},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "pasted_reviews_too_short")

    def test_invalid_output_language_returns_400(self):
        with patch("main.generate_pasted_reviews_brief", new=AsyncMock()) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "fr"},
                headers={"X-Request-ID": "reviews-invalid-language"},
            )

        self.assertEqual(response.status_code, 400)
        generate.assert_not_awaited()
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "unsupported_output_language")
        self.assertEqual(payload["request_id"], "reviews-invalid-language")

    def test_endpoint_does_not_call_workflow_sources_shadow_or_memory(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ), patch("main.copilot_engine.ainvoke", new=AsyncMock()) as workflow, patch(
            "main.source_probe_registry.fetch",
        ) as source_fetch, patch("main._amazon_shadow_sources") as shadow, patch(
            "main.memory_engine.save_memory"
        ) as save_memory, patch(
            "main.memory_engine.observability_snapshot"
        ) as memory_snapshot:
            response = self.client.post("/api/v1/generate-from-reviews", json=VALID_REVIEWS_REQUEST)

        self.assertEqual(response.status_code, 200)
        workflow.assert_not_awaited()
        source_fetch.assert_not_called()
        shadow.assert_not_called()
        save_memory.assert_not_called()
        memory_snapshot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
