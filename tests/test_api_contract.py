import unittest

from main import app
from schemas.api_contract import (
    DebugCopilotResponse,
    GenerateCopilotResponse,
    GrowthRequest,
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

    def test_generate_contract_is_unchanged_by_translation_endpoint(self):
        response_properties = GenerateCopilotResponse.model_json_schema()["properties"]
        data_schema = GenerateCopilotResponse.model_json_schema()["$defs"]["GenerateCopilotData"]
        self.assertNotIn("translated_text", response_properties)
        self.assertNotIn("translation", data_schema["properties"])


if __name__ == "__main__":
    unittest.main()
