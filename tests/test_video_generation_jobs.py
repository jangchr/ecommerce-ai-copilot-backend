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
