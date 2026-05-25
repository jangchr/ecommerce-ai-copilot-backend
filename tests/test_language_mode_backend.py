import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from tests.test_api_live_smoke import final_state_fixture
from tests.test_product_description_endpoint import GENERATED_BRIEF, VALID_REQUEST


ZH_DATA = {
    "insights": {
        "pain_points": ["\u4e2d\u6587\u75db\u70b9"],
        "user_complaint_cluster": ["\u4e2d\u6587\u6295\u8bc9"],
        "evidence": {
            "source_type": "user_provided_description",
            "source_url": "",
            "confidence": 0.55,
            "review_confidence": 0.0,
            "trend_confidence": 0.0,
            "review_count": 0,
            "evidence_quotes": ["\u4e2d\u6587\u53ef\u89c1\u8bc1\u636e"],
            "trend_signals": [],
            "data_warnings": ["user_provided_description_no_review_evidence"],
        },
    },
    "audience": {
        "primary": "\u9700\u8981\u5feb\u901f\u89e3\u51b3\u95ee\u9898\u7684\u7528\u6237",
        "sensitivity": "\u7701\u5fc3",
        "trust_barriers": ["\u62c5\u5fc3\u6548\u679c"],
    },
    "strategy": {
        "core_hook_strategy": "\u7528\u771f\u5b9e\u75db\u70b9\u505a\u5f00\u573a",
        "emotional_trigger": "\u4ece\u9ebb\u70e6\u5230\u8f7b\u677e",
    },
    "assets": {
        "tiktok_script": {
            "hook": "\u8fd9\u662f\u4e00\u4e2a\u4e2d\u6587\u94a9\u5b50",
            "cta": "\u73b0\u5728\u8bd5\u8bd5",
        },
        "storyboard": {
            "source": "user_provided_description",
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_description": "\u5c55\u793a\u95ee\u9898",
                    "narration": "\u8ba9\u7528\u6237\u7acb\u523b\u8ba4\u51fa\u75db\u70b9",
                    "evidence_quote_used": "\u4e2d\u6587\u53ef\u89c1\u8bc1\u636e",
                }
            ],
        },
    },
    "evaluation": {
        "confidence_score": 0.62,
        "risk_level": "medium",
        "reasoning": "\u4e2d\u6587\u8d28\u91cf\u5224\u65ad",
        "is_approved": True,
        "is_grounded": True,
        "creative_approved": True,
        "grounded_approved": True,
    },
    "feedback": "\u4e2d\u6587\u53cd\u9988",
}


class LanguageModeBackendTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_description_default_language_is_english(self):
        with patch(
            "main.generate_description_brief",
            new=AsyncMock(return_value=GENERATED_BRIEF),
        ):
            response = self.client.post("/api/v1/generate-from-description", json=VALID_REQUEST)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["output_language"], "en")
        self.assertIn("desk lamp", str(payload["data"]).lower())

    def test_description_explicit_english_language_is_unchanged(self):
        with patch(
            "main.generate_description_brief",
            new=AsyncMock(return_value=GENERATED_BRIEF),
        ):
            response = self.client.post(
                "/api/v1/generate-from-description",
                json={**VALID_REQUEST, "output_language": "en"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["output_language"], "en")
        self.assertIn("user_provided_description", str(payload["data"]))

    def test_description_chinese_language_translates_visible_product_payload(self):
        with patch(
            "main.generate_description_brief",
            new=AsyncMock(return_value=GENERATED_BRIEF),
        ), patch(
            "main.translate_product_visible_data",
            new=AsyncMock(return_value=ZH_DATA),
        ) as translate:
            response = self.client.post(
                "/api/v1/generate-from-description",
                json={**VALID_REQUEST, "output_language": "zh-CN"},
            )

        self.assertEqual(response.status_code, 200)
        translate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["output_language"], "zh-CN")
        self.assertIn("\u4e2d\u6587", payload["data"]["assets"]["tiktok_script"]["hook"])
        self.assertEqual(
            payload["data"]["insights"]["evidence"]["source_type"],
            "user_provided_description",
        )
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_description_invalid_language_returns_400(self):
        with patch("main.generate_description_brief", new=AsyncMock()) as generate:
            response = self.client.post(
                "/api/v1/generate-from-description",
                json={**VALID_REQUEST, "output_language": "fr"},
                headers={"X-Request-ID": "description-invalid-language"},
            )

        self.assertEqual(response.status_code, 400)
        generate.assert_not_awaited()
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "unsupported_output_language")
        self.assertEqual(payload["request_id"], "description-invalid-language")

    def test_generate_copilot_default_language_succeeds(self):
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(return_value=final_state_fixture()),
        ):
            response = self.client.post(
                "/api/v1/generate-copilot",
                json={"url": "balsamic_vinegar"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["output_language"], "en")

    def test_generate_copilot_chinese_language_succeeds_for_stable_slug(self):
        zh_data = {
            **ZH_DATA,
            "insights": {
                **ZH_DATA["insights"],
                "evidence": {
                    **ZH_DATA["insights"]["evidence"],
                    "source_type": "local_dataset+mock",
                    "review_confidence": 0.75,
                },
            },
        }
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(return_value=final_state_fixture()),
        ), patch(
            "main.translate_product_visible_data",
            new=AsyncMock(return_value=zh_data),
        ) as translate:
            response = self.client.post(
                "/api/v1/generate-copilot",
                json={"url": "balsamic_vinegar", "output_language": "zh-CN"},
            )

        self.assertEqual(response.status_code, 200)
        translate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["output_language"], "zh-CN")
        self.assertIn("\u4e2d\u6587", payload["data"]["assets"]["tiktok_script"]["hook"])
        self.assertEqual(payload["data"]["insights"]["evidence"]["source_type"], "local_dataset+mock")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_generate_copilot_invalid_language_returns_400_without_workflow(self):
        with patch("main.copilot_engine.ainvoke", new=AsyncMock()) as workflow:
            response = self.client.post(
                "/api/v1/generate-copilot",
                json={"url": "balsamic_vinegar", "output_language": "fr"},
            )

        self.assertEqual(response.status_code, 400)
        workflow.assert_not_awaited()
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "unsupported_output_language")


if __name__ == "__main__":
    unittest.main()
