import unittest

from schemas.source_probe_contract import (
    SourceProbeRequest,
    SourceProbeResponse,
    SourceProbeResult,
    SourceProbeTelemetry,
)


class SourceProbeContractTest(unittest.TestCase):
    def test_request_defaults_to_debug_only_without_api_credentials(self):
        request = SourceProbeRequest(product_category="printer")

        self.assertTrue(request.debug_only)
        self.assertIsNone(request.url)
        self.assertEqual(request.providers, [])

    def test_response_disallows_memory_write_by_default(self):
        response = SourceProbeResponse(
            debug_only=True,
            product_category="printer",
            results=[],
            fallback_required=True,
            telemetry=SourceProbeTelemetry(fallback_required=True),
        )

        self.assertFalse(response.memory_write_allowed)

    def test_response_schema_contains_probe_telemetry(self):
        properties = SourceProbeResponse.model_json_schema()["properties"]
        telemetry_properties = SourceProbeTelemetry.model_json_schema()["properties"]

        self.assertIn("telemetry", properties)
        for field in [
            "total_latency_ms",
            "provider_count",
            "success_count",
            "disabled_count",
            "unavailable_count",
            "error_count",
            "fallback_required",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, telemetry_properties)

    def test_result_status_models_probe_non_success_outcomes(self):
        for status in ["disabled", "unavailable", "error"]:
            with self.subTest(status=status):
                result = SourceProbeResult(provider="amazon_review_api", status=status)
                self.assertEqual(result.status, status)
                self.assertEqual(result.evidence_preview, [])

    def test_contract_schema_has_no_api_key_requirement(self):
        request_schema = SourceProbeRequest.model_json_schema()
        result_schema = SourceProbeResult.model_json_schema()

        self.assertNotIn("api_key", request_schema.get("properties", {}))
        self.assertNotIn("api_key", result_schema.get("properties", {}))
        self.assertNotIn("api_key", request_schema.get("required", []))
        self.assertNotIn("api_key", result_schema.get("required", []))


if __name__ == "__main__":
    unittest.main()
