import unittest
from unittest.mock import patch

from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
)
from video_generation.provider_sandbox import EXTERNAL_CALLS_FEATURE_FLAG
from video_generation.provider_runtime import (
    build_provider_poll_runtime,
    build_provider_runtime,
    next_simulated_provider_status,
    supports_provider_polling,
)


class VideoProviderRuntimeTest(unittest.TestCase):
    def test_generated_provider_runtime_metadata(self):
        with patch.dict("os.environ", {}, clear=True):
            runtime = build_provider_runtime("runway", now="2026-06-02T00:00:00Z")

        self.assertEqual(runtime["provider"], "runway")
        self.assertTrue(runtime["provider_job_id"].startswith("runway_sim_"))
        self.assertEqual(runtime["provider_status"], VIDEO_JOB_STATUS_QUEUED)
        self.assertEqual(runtime["submitted_at"], "2026-06-02T00:00:00Z")
        self.assertEqual(runtime["poll_count"], 0)
        self.assertEqual(runtime["mode"], "simulated_provider_polling")
        self.assertEqual(runtime["integration_mode"], "simulated")
        self.assertFalse(runtime["feature_flag_enabled"])
        self.assertFalse(runtime["real_external_api_call_enabled"])
        self.assertFalse(runtime["external_api_called"])
        self.assertFalse(runtime["integration_readiness"]["can_call_external_api"])

    def test_provider_runtime_feature_flag_enabled_missing_key_is_blocked_but_simulated(self):
        with patch.dict("os.environ", {EXTERNAL_CALLS_FEATURE_FLAG: "true"}, clear=True):
            runtime = build_provider_runtime("runway", now="2026-06-02T00:00:00Z")

        self.assertEqual(runtime["integration_mode"], "blocked_missing_api_key")
        self.assertTrue(runtime["feature_flag_enabled"])
        self.assertFalse(runtime["real_external_api_call_enabled"])
        self.assertFalse(runtime["external_api_called"])
        self.assertFalse(runtime["integration_readiness"]["api_key_configured"])

    def test_provider_runtime_feature_flag_and_fake_key_still_does_not_call_external_api(self):
        with patch.dict(
            "os.environ",
            {EXTERNAL_CALLS_FEATURE_FLAG: "true", "RUNWAY_API_KEY": "secret-runway-key"},
            clear=True,
        ):
            runtime = build_provider_runtime("runway", now="2026-06-02T00:00:00Z")

        self.assertEqual(runtime["integration_mode"], "sandbox_ready_no_external_call")
        self.assertTrue(runtime["feature_flag_enabled"])
        self.assertFalse(runtime["real_external_api_call_enabled"])
        self.assertFalse(runtime["external_api_called"])
        self.assertNotIn("secret-runway-key", str(runtime))

    def test_supports_polling_only_for_planned_async_providers(self):
        self.assertTrue(supports_provider_polling("runway"))
        self.assertTrue(supports_provider_polling("pika"))
        self.assertFalse(supports_provider_polling("manual_export"))
        self.assertFalse(supports_provider_polling("generic"))
        self.assertFalse(supports_provider_polling("capcut"))

    def test_default_poll_lifecycle(self):
        self.assertEqual(next_simulated_provider_status(VIDEO_JOB_STATUS_QUEUED), VIDEO_JOB_STATUS_PROCESSING)
        self.assertEqual(next_simulated_provider_status(VIDEO_JOB_STATUS_PROCESSING), VIDEO_JOB_STATUS_PROCESSING)
        self.assertEqual(
            next_simulated_provider_status(VIDEO_JOB_STATUS_PROCESSING, VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY),
            VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
        )
        self.assertEqual(
            next_simulated_provider_status(VIDEO_JOB_STATUS_PROCESSING, VIDEO_JOB_STATUS_FAILED),
            VIDEO_JOB_STATUS_FAILED,
        )

    def test_poll_runtime_updates_poll_count_and_error(self):
        runtime = build_provider_runtime("pika", provider_job_id="pika_job_1", now="2026-06-02T00:00:00Z")
        updated = build_provider_poll_runtime(
            runtime,
            VIDEO_JOB_STATUS_FAILED,
            error_message="provider timeout",
            notes="manual scaffold failure",
            now="2026-06-02T00:01:00Z",
        )

        self.assertEqual(updated["provider_job_id"], "pika_job_1")
        self.assertEqual(updated["provider_status"], VIDEO_JOB_STATUS_FAILED)
        self.assertEqual(updated["last_polled_at"], "2026-06-02T00:01:00Z")
        self.assertEqual(updated["poll_count"], 1)
        self.assertEqual(updated["error_message"], "provider timeout")
        self.assertEqual(updated["integration_mode"], "simulated")
        self.assertFalse(updated["feature_flag_enabled"])
        self.assertFalse(updated["real_external_api_call_enabled"])
        self.assertFalse(updated["external_api_called"])


if __name__ == "__main__":
    unittest.main()
