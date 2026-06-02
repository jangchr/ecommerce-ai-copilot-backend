import unittest

from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
)
from video_generation.provider_clients import (
    FakePikaClient,
    FakeRunwayClient,
    build_provider_client,
    build_provider_create_request,
    normalize_provider_create_response,
    normalize_provider_status_response,
)


def sample_job(provider: str = "runway") -> dict:
    return {
        "job_id": "video_job_fake_client",
        "provider": provider,
        "provider_payload": {
            "selected_export_key": f"{provider}_style_prompt",
            "prompt": "Create a product video prompt.",
            "scenes": [
                {"scene_id": 1, "visual_prompt": "Show the product."},
                {"scene_id": 2, "visual_prompt": "Show the proof."},
            ],
            "aspect_ratio": "9:16",
            "recommended_duration_seconds": 20,
        },
    }


class VideoProviderClientsTest(unittest.TestCase):
    def test_fake_runway_client_create_video_job_returns_queued(self):
        client = FakeRunwayClient()
        request = build_provider_create_request(sample_job("runway"))
        response = client.create_video_job(request)

        self.assertEqual(response["provider"], "runway")
        self.assertTrue(response["provider_job_id"].startswith("runway_fake_"))
        self.assertEqual(response["provider_status"], VIDEO_JOB_STATUS_QUEUED)
        self.assertFalse(response["external_api_called"])
        self.assertFalse(client.supports_real_network)
        self.assertFalse(response["request_preview"]["secrets_included"])

    def test_fake_pika_client_create_video_job_returns_queued(self):
        client = FakePikaClient()
        request = build_provider_create_request(sample_job("pika"))
        response = client.create_video_job(request)

        self.assertEqual(response["provider"], "pika")
        self.assertTrue(response["provider_job_id"].startswith("pika_fake_"))
        self.assertEqual(response["provider_status"], VIDEO_JOB_STATUS_QUEUED)
        self.assertFalse(response["external_api_called"])
        self.assertFalse(client.supports_real_network)

    def test_fake_status_response_can_represent_processing_and_completed(self):
        client = FakeRunwayClient()

        processing = client.get_video_job("runway_fake_123", state=VIDEO_JOB_STATUS_PROCESSING)
        self.assertEqual(processing["provider_status"], VIDEO_JOB_STATUS_PROCESSING)
        self.assertEqual(processing["result_url"], "")
        self.assertFalse(processing["external_api_called"])

        completed = client.get_video_job("runway_fake_123", state=VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY)
        self.assertEqual(completed["provider_status"], VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY)
        self.assertIn("runway_fake_123.mp4", completed["result_url"])
        self.assertFalse(completed["external_api_called"])

    def test_normalized_response_shape_contains_safe_result_fields(self):
        normalized = normalize_provider_status_response(
            "runway",
            {
                "id": "runway_fake_123",
                "status": VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
                "video_url": "https://example.com/video.mp4",
                "thumbnail_url": "https://example.com/preview.jpg",
            },
        )

        self.assertEqual(normalized["provider"], "runway")
        self.assertEqual(normalized["provider_job_id"], "runway_fake_123")
        self.assertEqual(normalized["provider_status"], VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY)
        self.assertEqual(normalized["result_url"], "https://example.com/video.mp4")
        self.assertEqual(normalized["preview_url"], "https://example.com/preview.jpg")
        self.assertFalse(normalized["external_api_called"])
        self.assertIn("raw_response_safe", normalized)

    def test_normalize_create_response_reuses_stable_shape(self):
        normalized = normalize_provider_create_response(
            "pika",
            {
                "provider_job_id": "pika_fake_123",
                "provider_status": VIDEO_JOB_STATUS_QUEUED,
            },
        )

        self.assertEqual(normalized["provider"], "pika")
        self.assertEqual(normalized["provider_job_id"], "pika_fake_123")
        self.assertEqual(normalized["provider_status"], VIDEO_JOB_STATUS_QUEUED)
        self.assertFalse(normalized["external_api_called"])

    def test_factory_returns_fake_clients_for_runway_and_pika(self):
        self.assertIsInstance(build_provider_client("runway"), FakeRunwayClient)
        self.assertIsInstance(build_provider_client("runway_style_prompt"), FakeRunwayClient)
        self.assertIsInstance(build_provider_client("pika"), FakePikaClient)
        self.assertIsInstance(build_provider_client("pika_style_prompt"), FakePikaClient)

    def test_factory_rejects_unsupported_provider_consistently(self):
        with self.assertRaises(ValueError):
            build_provider_client("manual_export")
        with self.assertRaises(ValueError):
            build_provider_client("runway", mode="real")

    def test_request_preview_and_normalized_response_do_not_include_api_key_values(self):
        request = build_provider_create_request(
            {
                **sample_job("runway"),
                "provider_payload": {
                    **sample_job("runway")["provider_payload"],
                    "prompt": "Prompt text; not a secret.",
                },
            }
        )
        response = FakeRunwayClient().create_video_job(request)
        normalized = normalize_provider_status_response("runway", response)

        combined = f"{request} {response} {normalized}"
        self.assertNotIn("secret-runway-key", combined)
        self.assertNotIn("RUNWAY_API_KEY", combined)
        self.assertNotIn("PIKA_API_KEY", combined)
        self.assertFalse(request["secrets_included"])
        self.assertFalse(normalized["external_api_called"])


if __name__ == "__main__":
    unittest.main()
