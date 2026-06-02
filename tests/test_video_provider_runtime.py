import unittest

from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
)
from video_generation.provider_runtime import (
    build_provider_poll_runtime,
    build_provider_runtime,
    next_simulated_provider_status,
    supports_provider_polling,
)


class VideoProviderRuntimeTest(unittest.TestCase):
    def test_generated_provider_runtime_metadata(self):
        runtime = build_provider_runtime("runway", now="2026-06-02T00:00:00Z")

        self.assertTrue(runtime["provider_job_id"].startswith("runway_sim_"))
        self.assertEqual(runtime["provider_status"], VIDEO_JOB_STATUS_QUEUED)
        self.assertEqual(runtime["submitted_at"], "2026-06-02T00:00:00Z")
        self.assertEqual(runtime["poll_count"], 0)
        self.assertEqual(runtime["mode"], "simulated_provider_polling")
        self.assertFalse(runtime["external_api_called"])

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
        self.assertFalse(updated["external_api_called"])


if __name__ == "__main__":
    unittest.main()
