import unittest

from fastapi.testclient import TestClient

from main import app
from schemas.api_contract import (
    DebugCopilotResponse,
    GenerateCopilotResponse,
    GrowthRequest,
    PastedReviewsRequest,
    PastedReviewsResponse,
    ProductDescriptionRequest,
    ProductDescriptionResponse,
    TranslationRequest,
    TranslationResponse,
)
from schemas.source_probe_contract import SourceProbeRequest, SourceProbeResponse


def route_response_model(path: str):
    for route in app.routes:
        if route.path == path:
            return route.response_model
    raise AssertionError(f"Route not found: {path}")


class ApiContractTest(unittest.TestCase):
    def test_generate_endpoint_uses_product_response_contract(self):
        self.assertIs(
            route_response_model("/api/v1/generate-copilot"),
            GenerateCopilotResponse,
        )

    def test_debug_endpoint_uses_debug_response_contract(self):
        self.assertIs(
            route_response_model("/api/v1/debug-copilot"),
            DebugCopilotResponse,
        )

    def test_debug_source_probe_endpoint_uses_probe_response_contract(self):
        self.assertIs(
            route_response_model("/api/v1/debug-source-probe"),
            SourceProbeResponse,
        )

    def test_translation_endpoint_uses_translation_response_contract(self):
        self.assertIs(
            route_response_model("/api/v1/translate-output"),
            TranslationResponse,
        )

    def test_product_description_endpoint_uses_description_response_contract(self):
        self.assertIs(
            route_response_model("/api/v1/generate-from-description"),
            ProductDescriptionResponse,
        )

    def test_pasted_reviews_endpoint_uses_reviews_response_contract(self):
        self.assertIs(
            route_response_model("/api/v1/generate-from-reviews"),
            PastedReviewsResponse,
        )

    def test_generate_contract_does_not_expose_debug_state(self):
        response_properties = GenerateCopilotResponse.model_json_schema()["properties"]
        data_schema = GenerateCopilotResponse.model_json_schema()["$defs"]["GenerateCopilotData"]
        self.assertNotIn("request_id", response_properties)
        self.assertNotIn("telemetry_summary", response_properties)
        self.assertNotIn("debug", data_schema["properties"])

    def test_debug_contract_exposes_observability_fields(self):
        properties = DebugCopilotResponse.model_json_schema()["properties"]
        for field in [
            "request_id",
            "evidence",
            "world_metrics",
            "telemetry",
            "telemetry_summary",
            "memory_observability",
            "shadow_sources",
            "revision_count",
            "regenerate_node",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, properties)

    def test_growth_request_defaults_to_tiktok_ctr(self):
        self.assertEqual(GrowthRequest(url="x").goal, "tiktok_ctr")
        self.assertEqual(GrowthRequest(url="x").real_source_mode, "local")
        self.assertEqual(GrowthRequest(url="x").output_language, "en")

    def test_source_probe_contract_exposes_debug_and_memory_guard_fields(self):
        request_properties = SourceProbeRequest.model_json_schema()["properties"]
        response_properties = SourceProbeResponse.model_json_schema()["properties"]

        self.assertIn("debug_only", request_properties)
        self.assertIn("debug_only", response_properties)
        self.assertIn("memory_write_allowed", response_properties)
        self.assertIn("request_id", response_properties)

    def test_translation_contract_defaults_and_fields(self):
        request = TranslationRequest(text="hello")
        self.assertEqual(request.target_language, "zh-CN")

        request_properties = TranslationRequest.model_json_schema()["properties"]
        response_properties = TranslationResponse.model_json_schema()["properties"]
        self.assertIn("text", request_properties)
        self.assertIn("target_language", request_properties)
        self.assertIn("translated_text", response_properties)
        self.assertIn("target_language", response_properties)
        self.assertIn("request_id", response_properties)

    def test_product_description_contract_defaults_and_fields(self):
        request = ProductDescriptionRequest(
            product_name="Desk Lamp",
            product_description="A compact desk lamp with soft adjustable lighting.",
            customer_pain_points="Users complain about glare and late-night eye fatigue.",
        )
        self.assertEqual(request.target_platform, "TikTok")
        self.assertEqual(request.goal, "tiktok_ctr")

        request_properties = ProductDescriptionRequest.model_json_schema()["properties"]
        response_properties = ProductDescriptionResponse.model_json_schema()["properties"]
        self.assertIn("product_name", request_properties)
        self.assertIn("product_description", request_properties)
        self.assertIn("customer_pain_points", request_properties)
        self.assertIn("target_platform", request_properties)
        self.assertIn("goal", request_properties)
        self.assertIn("output_language", request_properties)
        self.assertIn("status", response_properties)
        self.assertIn("data", response_properties)
        self.assertIn("request_id", response_properties)
        self.assertIn("output_language", response_properties)
        self.assertEqual(request.output_language, "en")

    def test_pasted_reviews_contract_defaults_and_fields(self):
        request = PastedReviewsRequest(
            product_name="Mini Blender",
            pasted_reviews="Hard to clean after one smoothie.\nToo loud for early mornings.",
        )
        self.assertEqual(request.target_platform, "TikTok")
        self.assertEqual(request.goal, "tiktok_ctr")
        self.assertEqual(request.output_language, "en")

        request_properties = PastedReviewsRequest.model_json_schema()["properties"]
        response_properties = PastedReviewsResponse.model_json_schema()["properties"]
        self.assertIn("product_name", request_properties)
        self.assertIn("product_category", request_properties)
        self.assertIn("product_description", request_properties)
        self.assertIn("pasted_reviews", request_properties)
        self.assertIn("target_platform", request_properties)
        self.assertIn("goal", request_properties)
        self.assertIn("output_language", request_properties)
        self.assertIn("status", response_properties)
        self.assertIn("data", response_properties)
        self.assertIn("request_id", response_properties)
        self.assertIn("output_language", response_properties)

    def test_pasted_reviews_invalid_output_language_returns_safe_error(self):
        client = TestClient(app)

        response = client.post(
            "/api/v1/generate-from-reviews",
            json={
                "product_name": "Mini Blender",
                "pasted_reviews": "Hard to clean after smoothies. Too loud for early mornings.",
                "output_language": "fr",
            },
            headers={"X-Request-ID": "reviews-invalid-language"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "unsupported_output_language")
        self.assertEqual(payload["request_id"], "reviews-invalid-language")

    def test_generate_contract_exposes_output_language_without_debug_fields(self):
        request_properties = GrowthRequest.model_json_schema()["properties"]
        response_properties = GenerateCopilotResponse.model_json_schema()["properties"]

        self.assertIn("output_language", request_properties)
        self.assertIn("output_language", response_properties)
        self.assertNotIn("telemetry_summary", response_properties)
        self.assertNotIn("shadow_sources", response_properties)
        self.assertNotIn("memory_observability", response_properties)

    def test_invalid_output_language_returns_safe_error(self):
        client = TestClient(app)

        response = client.post(
            "/api/v1/generate-copilot",
            json={"url": "balsamic_vinegar", "output_language": "fr"},
            headers={"X-Request-ID": "invalid-language-contract"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "unsupported_output_language")
        self.assertEqual(payload["request_id"], "invalid-language-contract")

    def test_generate_contract_is_unchanged_by_translation_endpoint(self):
        response_properties = GenerateCopilotResponse.model_json_schema()["properties"]
        data_schema = GenerateCopilotResponse.model_json_schema()["$defs"]["GenerateCopilotData"]
        self.assertNotIn("translated_text", response_properties)
        self.assertNotIn("translation", data_schema["properties"])


if __name__ == "__main__":
    unittest.main()
