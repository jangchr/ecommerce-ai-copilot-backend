import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from schemas.source_contract import SourceEvidence


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
        self.assertNotIn("shadow_sources", payload)
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
        self.assertEqual(payload["shadow_sources"], {})

    def test_debug_endpoint_runs_amazon_shadow_probe_when_requested(self):
        evidence = SourceEvidence(
            source_type="amazon_review_api",
            product_category="balsamic_vinegar",
            confidence=0.82,
            evidence_quotes=["Arrived with the cap cracked and leaked in the box."],
            metadata={
                "product_title": "Colavita Balsamic Vinegar",
                "review_count": "485",
            },
        )
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(return_value=self.final_state),
        ), patch(
            "main.memory_engine.observability_snapshot",
            return_value=self.final_state["memory_observability"],
        ), patch("main.source_probe_registry.fetch", return_value=evidence) as fetch:
            response = self.client.post(
                "/api/v1/debug-copilot",
                json={
                    "url": "https://www.amazon.com/dp/B00QIIMCCW",
                    "real_source_mode": "amazon_shadow",
                },
            )

        self.assertEqual(response.status_code, 200)
        fetch.assert_called_once_with(
            "amazon_review_api",
            "https://www.amazon.com/dp/B00QIIMCCW",
            "balsamic_vinegar",
        )
        shadow = response.json()["shadow_sources"]
        self.assertEqual(shadow["mode"], "amazon_shadow")
        self.assertFalse(shadow["memory_write_allowed"])
        self.assertFalse(shadow["used_for_generation"])
        self.assertEqual(shadow["amazon_review_api"]["status"], "success")
        self.assertEqual(shadow["amazon_review_api"]["source_confidence"], 0.82)
        self.assertIn("cap cracked", shadow["amazon_review_api"]["evidence_preview"][0])

    def test_debug_endpoint_shadow_probe_failure_does_not_break_response(self):
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(return_value=self.final_state),
        ), patch(
            "main.memory_engine.observability_snapshot",
            return_value=self.final_state["memory_observability"],
        ), patch("main.source_probe_registry.fetch", side_effect=RuntimeError("blocked")):
            response = self.client.post(
                "/api/v1/debug-copilot",
                json={
                    "url": "https://www.amazon.com/dp/B00QIIMCCW",
                    "real_source_mode": "amazon_shadow",
                },
            )

        self.assertEqual(response.status_code, 200)
        shadow = response.json()["shadow_sources"]
        self.assertEqual(shadow["amazon_review_api"]["status"], "error")
        self.assertEqual(shadow["amazon_review_api"]["error"], "blocked")
        self.assertFalse(shadow["memory_write_allowed"])
        self.assertFalse(shadow["used_for_generation"])

    def test_generate_endpoint_ignores_amazon_shadow_body_contract(self):
        evidence = SourceEvidence(source_type="amazon_review_api", confidence=0.9)
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(return_value=self.final_state),
        ), patch("main.source_probe_registry.fetch", return_value=evidence) as fetch:
            response = self.client.post(
                "/api/v1/generate-copilot",
                json={
                    "url": "https://www.amazon.com/dp/B00QIIMCCW",
                    "real_source_mode": "amazon_shadow",
                },
            )

        self.assertEqual(response.status_code, 200)
        fetch.assert_not_called()
        payload = response.json()
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("shadow_sources", payload["data"])


if __name__ == "__main__":
    unittest.main()
