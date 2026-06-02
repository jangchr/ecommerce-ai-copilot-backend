import unittest

from video_generation.job_status import (
    VIDEO_JOB_STATUS_CANCELLED,
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
    VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    build_video_job_history_event,
    can_transition_video_job_status,
    is_valid_video_job_status,
    normalize_video_job_status,
    video_job_status_metadata,
)


class VideoJobStatusTest(unittest.TestCase):
    def test_known_statuses_are_valid(self):
        for status in [
            "created",
            "ready_for_manual_export",
            "queued",
            "processing",
            "manual_export_completed",
            "external_result_ready",
            "failed",
            "cancelled",
        ]:
            self.assertTrue(is_valid_video_job_status(status))

    def test_unknown_status_is_invalid_and_normalize_uses_fallback(self):
        self.assertFalse(is_valid_video_job_status("not_real"))
        self.assertEqual(
            normalize_video_job_status("not_real", fallback=VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED),
            VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
        )

    def test_allowed_transitions(self):
        self.assertTrue(can_transition_video_job_status(VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT, VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY))
        self.assertTrue(can_transition_video_job_status(VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT, VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED))
        self.assertTrue(can_transition_video_job_status(VIDEO_JOB_STATUS_QUEUED, VIDEO_JOB_STATUS_PROCESSING))
        self.assertTrue(can_transition_video_job_status(VIDEO_JOB_STATUS_PROCESSING, VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY))

    def test_disallowed_transitions(self):
        self.assertFalse(can_transition_video_job_status(VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY, VIDEO_JOB_STATUS_PROCESSING))
        self.assertFalse(can_transition_video_job_status(VIDEO_JOB_STATUS_CANCELLED, VIDEO_JOB_STATUS_PROCESSING))

    def test_status_metadata_marks_groups(self):
        ready = video_job_status_metadata(VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT)
        self.assertTrue(ready["is_manual"])
        self.assertFalse(ready["is_terminal"])
        self.assertIn(VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY, ready["allowed_next_statuses"])

        done = video_job_status_metadata(VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY)
        self.assertTrue(done["is_terminal"])
        self.assertEqual(done["allowed_next_statuses"], [])

    def test_history_event_builder_includes_event_status_and_updated_at(self):
        event = build_video_job_history_event(
            "status_changed",
            VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
            updated_at="2026-06-02T00:00:00Z",
            from_status=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
        )

        self.assertEqual(event["event"], "status_changed")
        self.assertEqual(event["status"], VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY)
        self.assertEqual(event["updated_at"], "2026-06-02T00:00:00Z")
        self.assertEqual(event["from_status"], VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT)


if __name__ == "__main__":
    unittest.main()
