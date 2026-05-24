import unittest

from pydantic import ValidationError

from schemas.api_contract import (
    DebugCopilotResponse,
    GenerateCopilotResponse,
    GrowthRequest,
)


class ShadowModeContractTest(unittest.TestCase):
    def test_growth_request_defaults_to_local_source_mode(self):
        request = GrowthRequest(url="https://test.local/products/balsamic_vinegar")
        self.assertEqual(request.real_source_mode, "local")

    def test_growth_request_allows_amazon_shadow_mode(self):
        request = GrowthRequest(
            url="https://www.amazon.com/dp/B00QIIMCCW",
            real_source_mode="amazon_shadow",
        )
        self.assertEqual(request.real_source_mode, "amazon_shadow")

    def test_growth_request_rejects_amazon_primary_mode(self):
        with self.assertRaises(ValidationError):
            GrowthRequest(
                url="https://www.amazon.com/dp/B00QIIMCCW",
                real_source_mode="amazon_primary",
            )

    def test_product_response_does_not_expose_shadow_sources(self):
        properties = GenerateCopilotResponse.model_json_schema()["properties"]
        data_properties = GenerateCopilotResponse.model_json_schema()["$defs"][
            "GenerateCopilotData"
        ]["properties"]
        self.assertNotIn("shadow_sources", properties)
        self.assertNotIn("shadow_sources", data_properties)

    def test_debug_response_exposes_shadow_sources(self):
        properties = DebugCopilotResponse.model_json_schema()["properties"]
        self.assertIn("shadow_sources", properties)


if __name__ == "__main__":
    unittest.main()
