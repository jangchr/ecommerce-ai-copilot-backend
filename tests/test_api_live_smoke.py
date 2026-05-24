import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


def final_state_fixture() -> dict:
    audience = {
        "primary_user": "Busy home cooks",
        "trust_barriers": ["Shipping leakage"],
    }
    painpoint = {
        "physical_painpoints": ["Leaking cap"],
        "emotional_painpoints": ["Wasted purchase"],
        "use_case_disasters": ["Bottle leaks inside the delivery box"],
    }
    return {
        "env_state": {
            "product_category": "balsamic_vinegar",
            "evidence": {
                "source_type": "local_dataset+mock",
                "confidence": 0.67,
                "review_confidence": 0.75,
                "trend_confidence": 0.35,
                "review_count": 6,
                "evidence_quotes": ["The cap cracked during shipping and leaked all over the box."],
                "trend_signals": ["Visible packaging failure demonstrations hold attention."],
                "data_warnings": [],
            },
        },
        "cognitive_state": {
            "strategy": {
                "identity_attack": "Stop accepting messy deliveries.",
                "status_desire": "A clean, reliable pantry staple.",
                "future_self_gap": "From cleanup to effortless plating.",
                "conversion_mechanism": "Show a secure seal.",
                "cta_logic": "Choose the bottle designed to arrive intact.",
                "evidence_basis": ["The cap cracked during shipping and leaked all over the box."],
            },
            "audience": audience,
            "painpoint": painpoint,
            "profile": {
                "audience": audience,
                "painpoint": painpoint,
                "dopamine": {"viral_emotion": "Relief"},
            },
        },
        "execution_state": {
            "storyboard": {
                "scenes": [
                    {
                        "duration_sec": 2.0,
                        "scene_goal": "Expose the leak",
                        "visual_description": "A delivery box opens to reveal a stained bottle wrap.",
                        "narration": "A cracked cap should not ruin dinner before it begins.",
                        "on_screen_text": "Leaked again?",
                        "retention_reason": "Immediate recognizable failure",
                        "linked_painpoint": "Leaking cap",
                    }
                ]
            }
        },
        "world_metrics": {
            "retention_3s": 0.78,
            "reason": "Evidence-linked storyboard accepted.",
            "dopamine_score": 0.70,
            "evidence_alignment": 1.0,
            "predicted_ctr": 0.07,
            "grounded_ctr": 0.06,
            "source_confidence": 0.67,
            "failure_type": "",
            "is_approved": True,
            "is_grounded": True,
            "creative_approved": True,
            "grounded_approved": True,
        },
        "telemetry_state": {
            "strategy": {"status": "success", "latency_ms": 12.0, "total_tokens": 20}
        },
        "memory_observability": {
            "backend": "faiss",
            "memory_record_count": 1,
            "fallback_count": 0,
        },
        "revision_count": 0,
    }


class ApiLiveSmokeTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.final_state = final_state_fixture()

    def test_generate_endpoint_returns_product_payload_without_debug(self):
        with patch("main.copilot_engine.ainvoke", new=AsyncMock(return_value=self.final_state)):
            response = self.client.post(
                "/api/v1/generate-copilot",
                json={"url": "https://test.local/products/balsamic_vinegar"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("status", payload)
        self.assertIn("data", payload)
        self.assertIn("X-Request-ID", response.headers)
        self.assertNotIn("request_id", payload)
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("debug", payload["data"])
        for field in ["insights", "audience", "strategy", "assets", "evaluation", "feedback"]:
            with self.subTest(field=field):
                self.assertIn(field, payload["data"])

    def test_debug_endpoint_returns_full_observability_payload(self):
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(return_value=self.final_state),
        ), patch(
            "main.memory_engine.observability_snapshot",
            return_value=self.final_state["memory_observability"],
        ):
            response = self.client.post(
                "/api/v1/debug-copilot",
                json={"url": "https://test.local/products/balsamic_vinegar"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for field in [
            "request_id",
            "product_category",
            "evidence",
            "cognitive_state",
            "execution_state",
            "world_metrics",
            "telemetry",
            "telemetry_summary",
            "memory_observability",
            "shadow_sources",
            "revision_count",
            "regenerate_node",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, payload)
        self.assertEqual(payload["request_id"], response.headers["X-Request-ID"])
        self.assertEqual(payload["telemetry_summary"]["node_count"], 1)
        self.assertEqual(payload["telemetry_summary"]["total_tokens"], 20)
        self.assertEqual(payload["telemetry_summary"]["max_token_node"], "strategy")
        self.assertEqual(payload["memory_observability"]["backend"], "faiss")


if __name__ == "__main__":
    unittest.main()
