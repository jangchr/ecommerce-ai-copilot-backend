import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from video_generation.provider_integration import (
    build_provider_request_contract,
    normalize_provider_response,
    provider_error_contract,
    provider_integration_readiness,
    provider_polling_contract,
)
from video_generation.provider_sandbox import (
    EXTERNAL_CALLS_FEATURE_FLAG,
    blocked_provider_external_call_result,
    build_provider_sandbox_request_preview,
    provider_external_call_settings,
    provider_sandbox_readiness,
)


class VideoProviderIntegrationContractTest(unittest.TestCase):
    def test_runway_readiness_requires_key_but_cannot_call_external_api(self):
        readiness = provider_integration_readiness("runway", env={})

        self.assertEqual(readiness["provider"], "runway")
        self.assertFalse(readiness["external_api_ready"])
        self.assertFalse(readiness["integration_enabled"])
        self.assertTrue(readiness["requires_api_key"])
        self.assertEqual(readiness["env_key_name"], "RUNWAY_API_KEY")
        self.assertFalse(readiness["api_key_configured"])
        self.assertFalse(readiness["can_call_external_api"])
        self.assertEqual(readiness["feature_flag_name"], EXTERNAL_CALLS_FEATURE_FLAG)
        self.assertFalse(readiness["feature_flag_enabled"])
        self.assertEqual(readiness["integration_mode"], "simulated")
        self.assertFalse(readiness["real_external_api_call_enabled"])
        self.assertFalse(readiness["external_api_called"])
        self.assertIn("false", readiness["disabled_reason"])

    def test_pika_key_configured_still_cannot_call_external_api(self):
        readiness = provider_integration_readiness(
            "pika",
            env={EXTERNAL_CALLS_FEATURE_FLAG: "true", "PIKA_API_KEY": "secret-pika-key"},
        )

        self.assertTrue(readiness["api_key_configured"])
        self.assertFalse(readiness["can_call_external_api"])
        self.assertFalse(readiness["external_api_ready"])
        self.assertTrue(readiness["feature_flag_enabled"])
        self.assertEqual(readiness["integration_mode"], "sandbox_ready_no_external_call")
        self.assertTrue(readiness["sandbox_ready"])
        self.assertNotIn("secret-pika-key", str(readiness))

    def test_feature_flag_true_missing_runway_key_is_blocked(self):
        readiness = provider_integration_readiness("runway", env={EXTERNAL_CALLS_FEATURE_FLAG: "true"})

        self.assertTrue(readiness["feature_flag_enabled"])
        self.assertFalse(readiness["api_key_configured"])
        self.assertFalse(readiness["can_call_external_api"])
        self.assertEqual(readiness["integration_mode"], "blocked_missing_api_key")
        self.assertIn("RUNWAY_API_KEY", readiness["disabled_reason"])

    def test_provider_sandbox_settings_default_off(self):
        settings = provider_external_call_settings(env={})

        self.assertEqual(settings["feature_flag_name"], EXTERNAL_CALLS_FEATURE_FLAG)
        self.assertFalse(settings["feature_flag_enabled"])
        self.assertFalse(settings["can_call_external_api"])
        self.assertFalse(settings["real_external_api_call_enabled"])
        self.assertFalse(settings["external_api_called"])
        self.assertEqual(settings["integration_mode"], "simulated")

    def test_provider_sandbox_fake_key_never_exposes_secret_or_enables_call(self):
        readiness = provider_sandbox_readiness(
            "runway",
            env={EXTERNAL_CALLS_FEATURE_FLAG: "true", "RUNWAY_API_KEY": "secret-runway-key"},
        )

        self.assertTrue(readiness["api_key_configured"])
        self.assertTrue(readiness["feature_flag_enabled"])
        self.assertFalse(readiness["can_call_external_api"])
        self.assertFalse(readiness["real_external_api_call_enabled"])
        self.assertFalse(readiness["external_api_called"])
        self.assertEqual(readiness["integration_mode"], "sandbox_ready_no_external_call")
        self.assertNotIn("secret-runway-key", str(readiness))

    def test_manual_export_readiness_never_requires_key(self):
        readiness = provider_integration_readiness("manual_export", env={"RUNWAY_API_KEY": "secret"})

        self.assertEqual(readiness["provider"], "manual_export")
        self.assertFalse(readiness["requires_api_key"])
        self.assertEqual(readiness["env_key_name"], "")
        self.assertFalse(readiness["api_key_configured"])
        self.assertFalse(readiness["can_call_external_api"])
        self.assertEqual(readiness["integration_mode"], "manual_or_prompt_export")
        self.assertIn("manual", readiness["disabled_reason"])

    def test_request_contract_never_contains_real_api_key_value(self):
        job = {
            "job_id": "video_job_test",
            "provider": "runway",
            "provider_runtime": {"provider_job_id": "runway_job_123"},
            "provider_payload": {
                "selected_export_key": "runway_style_prompt",
                "prompt": "Prompt text",
                "scene_count": 4,
                "recommended_duration_seconds": 20,
                "aspect_ratio": "9:16",
            },
        }

        contract = build_provider_request_contract(job)

        self.assertEqual(contract["provider"], "runway")
        self.assertEqual(contract["provider_job_id"], "runway_job_123")
        self.assertTrue(contract["prompt_present"])
        self.assertFalse(contract["secrets_included"])
        self.assertNotIn("API_KEY", str(contract))

        preview = build_provider_sandbox_request_preview(job)
        self.assertEqual(preview["provider"], "runway")
        self.assertFalse(preview["secrets_included"])

    def test_blocked_external_call_result_is_safe(self):
        result = blocked_provider_external_call_result("runway", "sandbox only")

        self.assertEqual(result["provider"], "runway")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["can_call_external_api"])
        self.assertFalse(result["external_api_called"])
        self.assertIn("integration_mode", result)

    def test_response_and_error_contracts_are_safe_normalized_shapes(self):
        normalized = normalize_provider_response(
            "runway",
            {
                "id": "runway_job_123",
                "status": "external_result_ready",
                "video_url": "https://example.com/video.mp4",
                "thumbnail_url": "https://example.com/preview.jpg",
            },
        )
        self.assertEqual(normalized["provider"], "runway")
        self.assertEqual(normalized["provider_job_id"], "runway_job_123")
        self.assertEqual(normalized["result_url"], "https://example.com/video.mp4")
        self.assertFalse(normalized["raw_response_stored"])

        error = provider_error_contract("runway", {"category": "provider_timeout", "message": "timed out"})
        self.assertEqual(error["error_category"], "provider_timeout")
        self.assertTrue(error["retryable"])
        self.assertTrue(error["safe_for_logs"])

    def test_polling_contract_is_simulated_and_bounded(self):
        contract = provider_polling_contract("pika")

        self.assertEqual(contract["provider"], "pika")
        self.assertEqual(contract["mode"], "simulated_provider_polling")
        self.assertFalse(contract["external_api_called"])
        self.assertIn("queued", contract["default_poll_sequence"])
        self.assertGreater(contract["timeout_seconds"], 0)
        self.assertGreater(contract["max_poll_attempts"], 0)

    def test_provider_plan_endpoint_includes_integration_contract(self):
        client = TestClient(app)
        with patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/v1/video-generation/providers/runway/plan")

        self.assertEqual(response.status_code, 200)
        plan = response.json()["plan"]
        self.assertEqual(plan["selected_export_key"], "runway_style_prompt")
        self.assertIn("integration_readiness", plan)
        self.assertIn("polling_contract", plan)
        self.assertIn("request_contract_summary", plan)
        self.assertIn("error_contract_summary", plan)
        readiness = plan["integration_readiness"]
        self.assertIsInstance(readiness["api_key_configured"], bool)
        self.assertFalse(readiness["can_call_external_api"])
        self.assertEqual(readiness["feature_flag_name"], EXTERNAL_CALLS_FEATURE_FLAG)
        self.assertFalse(readiness["feature_flag_enabled"])
        self.assertEqual(readiness["integration_mode"], "simulated")
        self.assertFalse(readiness["real_external_api_call_enabled"])
        self.assertFalse(readiness["external_api_called"])
        self.assertNotIn("sk-", str(plan))


if __name__ == "__main__":
    unittest.main()
