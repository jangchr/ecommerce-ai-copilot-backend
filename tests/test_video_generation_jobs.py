import unittest

from fastapi.testclient import TestClient

from main import app


VIDEO_PACKET = {
    "packet_version": "video_generation_v1",
    "intended_use": "video_prompt_export",
    "video": {
        "platform": "TikTok",
        "recommended_duration_seconds": 20,
        "aspect_ratio": "9:16",
    },
    "scenes": [
        {
            "scene_id": 1,
            "duration_seconds": 5,
            "visual_prompt": "Show a compact blender on a kitchen counter.",
            "narration": "One smoothie should not make cleanup hard.",
            "overlay_text": "Hard to clean?",
            "evidence_quote": "Hard to clean after one smoothie",
        },
        {
            "scene_id": 2,
            "duration_seconds": 5,
            "visual_prompt": "Show someone blending early in the morning.",
            "narration": "Nobody wants to wake the whole house.",
            "overlay_text": "Too loud?",
            "evidence_quote": "Too loud for early mornings",
        },
    ],
    "full_video_prompt": "Create a 9:16 TikTok video about a compact blender.",
    "export_formats": {
        "generic_video_prompt": "Create a 9:16 TikTok video about a compact blender.",
        "capcut_shot_list": "Scene 1 - 5s - Show compact blender.\\nScene 2 - 5s - Blend early morning.",
        "runway_style_prompt": "Cinematic close-up of compact blender in a bright kitchen.",
        "pika_style_prompt": "Short motion video, compact blender, quick cuts.",
    },
}


class VideoGenerationJobEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_video_generation_providers_endpoint_lists_supported_providers(self):
        response = self.client.get(
            "/api/v1/video-generation/providers",
            headers={"X-Request-ID": "video-providers-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-providers-1")

        providers = {item["provider"]: item for item in payload["providers"]}
        for provider in ["manual_export", "generic", "capcut", "runway", "pika"]:
            self.assertIn(provider, providers)
            self.assertIn("export_key", providers[provider])
            self.assertFalse(providers[provider]["external_api_ready"])

    def test_create_video_generation_job_selects_provider_export_prompt(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
                "output_language": "en",
            },
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["provider"], "runway")
        self.assertEqual(job["provider_payload"]["selected_export_key"], "runway_style_prompt")
        self.assertEqual(job["provider_payload"]["prompt"], VIDEO_PACKET["export_formats"]["runway_style_prompt"])
        self.assertEqual(job["provider_payload"]["next_action"], "manual_copy_to_video_tool")

    def test_create_video_generation_job_accepts_export_key_alias(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "capcut_shot_list",
                "output_language": "en",
            },
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["provider"], "capcut")
        self.assertEqual(job["provider_payload"]["selected_export_key"], "capcut_shot_list")

    def test_create_video_generation_job_rejects_unsupported_provider(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "unknown_video_tool",
            },
            headers={"X-Request-ID": "video-job-provider-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-provider-invalid-1")
        self.assertIn("unsupported", payload["error"])
        self.assertIn("runway", payload["supported_providers"])

    def test_create_video_generation_job_returns_manual_export_payload(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
                "output_language": "en",
            },
            headers={"X-Request-ID": "video-job-create-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-create-1")

        job = payload["job"]
        self.assertTrue(job["job_id"].startswith("video_job_"))
        self.assertEqual(job["status"], "ready_for_manual_export")
        self.assertEqual(job["provider"], "manual_export")
        self.assertEqual(job["video_generation_packet"]["packet_version"], "video_generation_v1")
        self.assertEqual(job["provider_payload"]["handoff_type"], "manual_export")
        self.assertIn("generic_video_prompt", job["provider_payload"]["export_formats"])
        self.assertIn("capcut_shot_list", job["provider_payload"]["export_formats"])
        self.assertEqual(len(job["provider_payload"]["scenes"]), 2)
        self.assertEqual(job["result"]["result_url"], "")

    def test_update_video_generation_job_result_records_external_result(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
                "output_language": "en",
            },
        ).json()

        job_id = created["job"]["job_id"]
        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/result",
            json={
                "status": "external_result_ready",
                "result_url": "https://example.com/video.mp4",
                "preview_url": "https://example.com/preview.jpg",
                "download_url": "https://example.com/download.mp4",
                "provider_job_id": "runway_job_123",
                "notes": "Generated externally from copied prompt.",
            },
            headers={"X-Request-ID": "video-job-result-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-result-1")

        job = payload["job"]
        self.assertEqual(job["job_id"], job_id)
        self.assertEqual(job["status"], "external_result_ready")
        self.assertEqual(job["result"]["result_url"], "https://example.com/video.mp4")
        self.assertEqual(job["result"]["preview_url"], "https://example.com/preview.jpg")
        self.assertEqual(job["result"]["download_url"], "https://example.com/download.mp4")
        self.assertEqual(job["result"]["provider_job_id"], "runway_job_123")
        self.assertTrue(job["history"])
        self.assertEqual(job["history"][-1]["event"], "result_update")

    def test_update_video_generation_job_result_falls_back_to_manual_completed_status(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
            },
        ).json()

        job_id = created["job"]["job_id"]
        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/result",
            json={
                "status": "not_supported",
                "notes": "Copied into a manual editor.",
            },
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["status"], "manual_export_completed")
        self.assertEqual(job["result"]["notes"], "Copied into a manual editor.")

    def test_update_video_generation_job_result_returns_404_for_missing_job(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/video_job_missing/result",
            json={
                "status": "external_result_ready",
                "result_url": "https://example.com/video.mp4",
            },
            headers={"X-Request-ID": "video-job-result-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-result-missing-1")

    def test_create_video_generation_job_from_generation_data(self):
        generation_data = {
            "assets": {
                "tiktok_script": {
                    "hook": "Tired of loud blenders?",
                    "cta": "Try this compact option.",
                },
                "storyboard": {
                    "scenes": [
                        {"narration": "Scene one"},
                        {"narration": "Scene two"},
                    ]
                },
            },
            "evaluation": {
                "risk_level": "medium",
                "is_grounded": True,
            },
            "agent_trace": {
                "trace_version": "agent_trace_v1",
            },
            "video_generation_packet": VIDEO_PACKET,
        }

        response = self.client.post(
            "/api/v1/video-generation/jobs/from-generation",
            json={
                "generation_data": generation_data,
                "provider": "pika",
                "output_language": "en",
            },
            headers={"X-Request-ID": "video-job-from-generation-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-from-generation-1")

        job = payload["job"]
        self.assertEqual(job["provider"], "pika")
        self.assertEqual(job["provider_payload"]["selected_export_key"], "pika_style_prompt")
        self.assertEqual(job["source_generation"]["hook"], "Tired of loud blenders?")
        self.assertEqual(job["source_generation"]["storyboard_scene_count"], 2)
        self.assertEqual(job["source_generation"]["risk_level"], "medium")
        self.assertTrue(job["source_generation"]["is_grounded"])
        self.assertEqual(job["source_generation"]["agent_trace_version"], "agent_trace_v1")

    def test_create_video_generation_job_from_generation_rejects_missing_video_packet(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/from-generation",
            json={
                "generation_data": {
                    "assets": {
                        "tiktok_script": {
                            "hook": "Missing packet"
                        }
                    }
                },
                "provider": "manual_export",
            },
            headers={"X-Request-ID": "video-job-from-generation-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-from-generation-invalid-1")
        self.assertIn("generation_data.video_generation_packet", payload["error"])

    def test_create_video_generation_job_from_generation_rejects_unsupported_provider(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/from-generation",
            json={
                "generation_data": {
                    "video_generation_packet": VIDEO_PACKET
                },
                "provider": "unknown_provider",
            },
            headers={"X-Request-ID": "video-job-from-generation-provider-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-from-generation-provider-invalid-1")
        self.assertIn("unsupported", payload["error"])

    def test_get_video_generation_job_returns_created_job(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
                "output_language": "en",
            },
        ).json()

        job_id = created["job"]["job_id"]
        response = self.client.get(
            f"/api/v1/video-generation/jobs/{job_id}",
            headers={"X-Request-ID": "video-job-get-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-get-1")
        self.assertEqual(payload["job"]["job_id"], job_id)
        self.assertEqual(payload["job"]["status"], "ready_for_manual_export")

    def test_create_video_generation_job_rejects_wrong_packet_version(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": {"packet_version": "wrong"},
                "provider": "manual_export",
            },
            headers={"X-Request-ID": "video-job-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-invalid-1")
        self.assertIn("video_generation_v1", payload["error"])

    def test_get_video_generation_job_returns_404_for_missing_job(self):
        response = self.client.get(
            "/api/v1/video-generation/jobs/video_job_missing",
            headers={"X-Request-ID": "video-job-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-missing-1")


if __name__ == "__main__":
    unittest.main()
