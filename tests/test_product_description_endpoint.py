import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


VALID_REQUEST = {
    "product_name": "SoftGlow Desk Lamp",
    "product_category": "desk_lamp",
    "product_description": "A compact desk lamp with soft adjustable lighting for late-night work.",
    "customer_pain_points": "Users complain about glare, messy desks, and eye fatigue at night.",
}


GENERATED_BRIEF = {
    "target_audience": "Remote workers who need a calmer desk setup.",
    "core_hook_strategy": "Show the moment harsh light makes work feel harder.",
    "emotional_trigger": "Relief from eye strain and desk chaos.",
    "hook": "Your desk lamp should help you work, not make you more tired.",
    "cta": "Try a softer desk setup tonight.",
    "storyboard_scenes": [
        {
            "visual_description": "A tired worker squints under a harsh desk light.",
            "narration": "If your lamp makes your eyes work harder, the setup is broken.",
            "evidence_quote_used": "Users complain about glare and eye fatigue.",
        },
        {
            "visual_description": "A cluttered desk makes the task feel heavier.",
            "narration": "The desk feels busy before the work even begins.",
            "evidence_quote_used": "Users complain about messy desks.",
        },
        {
            "visual_description": "The lamp switches to a softer glow.",
            "narration": "A calmer light changes the whole desk mood.",
            "evidence_quote_used": "Soft adjustable lighting for late-night work.",
        },
        {
            "visual_description": "A clean desk and warm light frame the final setup.",
            "narration": "Make the desk feel ready before you start.",
            "evidence_quote_used": "Soft adjustable lighting for late-night work.",
        },
    ],
    "evaluation_reasoning": "Generated only from user-provided product description.",
    "feedback": "Validate claims before using this in paid ads.",
}


class ProductDescriptionEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_missing_product_name_returns_400(self):
        body = {**VALID_REQUEST, "product_name": "  "}
        response = self.client.post("/api/v1/generate-from-description", json=body)

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "missing_product_name")
        self.assertIn("request_id", payload)

    def test_missing_product_description_returns_400(self):
        body = {**VALID_REQUEST, "product_description": ""}
        response = self.client.post("/api/v1/generate-from-description", json=body)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "missing_product_description")

    def test_missing_customer_pain_points_returns_400(self):
        body = {**VALID_REQUEST, "customer_pain_points": ""}
        response = self.client.post("/api/v1/generate-from-description", json=body)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "missing_customer_pain_points")

    def test_too_short_input_returns_400(self):
        body = {
            **VALID_REQUEST,
            "product_description": "short",
            "customer_pain_points": "short",
        }
        response = self.client.post("/api/v1/generate-from-description", json=body)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "input_too_short")

    def test_success_returns_product_like_payload_from_user_description_source(self):
        with patch(
            "main.generate_description_brief",
            new=AsyncMock(return_value=GENERATED_BRIEF),
        ) as generate:
            response = self.client.post(
                "/api/v1/generate-from-description",
                json=VALID_REQUEST,
                headers={"X-Request-ID": "description-smoke-1"},
            )

        self.assertEqual(response.status_code, 200)
        generate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "description-smoke-1")
        self.assertEqual(response.headers["X-Request-ID"], "description-smoke-1")
        for field in ["insights", "audience", "strategy", "assets", "evaluation", "feedback"]:
            with self.subTest(field=field):
                self.assertIn(field, payload["data"])

        evidence = payload["data"]["insights"]["evidence"]
        self.assertEqual(evidence["source_type"], "user_provided_description")
        self.assertNotEqual(evidence["source_type"], "local_dataset")
        self.assertNotEqual(evidence["source_type"], "amazon_review_api")
        self.assertEqual(evidence["review_count"], 0)
        self.assertIn("user_provided_description_no_review_evidence", evidence["data_warnings"])
        self.assertEqual(payload["data"]["assets"]["storyboard"]["source"], "user_provided_description")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_endpoint_does_not_call_workflow_sources_shadow_or_memory(self):
        with patch(
            "main.generate_description_brief",
            new=AsyncMock(return_value=GENERATED_BRIEF),
        ), patch("main.copilot_engine.ainvoke", new=AsyncMock()) as workflow, patch(
            "main.source_probe_registry.fetch",
        ) as source_fetch, patch("main._amazon_shadow_sources") as shadow, patch(
            "main.memory_engine.save_memory"
        ) as save_memory, patch(
            "main.memory_engine.observability_snapshot"
        ) as memory_snapshot:
            response = self.client.post("/api/v1/generate-from-description", json=VALID_REQUEST)

        self.assertEqual(response.status_code, 200)
        workflow.assert_not_awaited()
        source_fetch.assert_not_called()
        shadow.assert_not_called()
        save_memory.assert_not_called()
        memory_snapshot.assert_not_called()

    def test_generation_failure_returns_safe_json_error(self):
        with patch(
            "main.generate_description_brief",
            new=AsyncMock(side_effect=RuntimeError("provider failed with secret-like traceback")),
        ):
            response = self.client.post(
                "/api/v1/generate-from-description",
                json=VALID_REQUEST,
                headers={"X-Request-ID": "description-failure-1"},
            )

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "generation_failed")
        self.assertEqual(payload["request_id"], "description-failure-1")
        self.assertNotIn("traceback", str(payload).lower())
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_existing_generate_copilot_route_still_exists(self):
        paths = {getattr(route, "path", "") for route in app.routes}
        self.assertIn("/api/v1/generate-copilot", paths)
        self.assertIn("/api/v1/generate-from-description", paths)


if __name__ == "__main__":
    unittest.main()
