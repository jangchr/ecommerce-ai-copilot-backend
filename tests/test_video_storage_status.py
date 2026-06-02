import unittest

from fastapi.testclient import TestClient

from main import app


class VideoStorageStatusEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_video_storage_status_reports_default_memory_mode(self):
        response = self.client.get(
            "/api/v1/video-generation/storage/status",
            headers={"X-Request-ID": "video-storage-status-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-storage-status-1")

        storage = payload["storage"]
        self.assertEqual(storage["storage_mode"], "memory")
        self.assertTrue(storage["is_memory_store"])
        self.assertFalse(storage["is_file_store"])
        self.assertFalse(storage["restart_persistence_enabled"])
        self.assertTrue(storage["persistent_storage_required_for_restart_survival"])
        self.assertIn("reset", " ".join(storage["warnings"]).lower())

    def test_video_storage_status_response_does_not_expose_secrets(self):
        response = self.client.get("/api/v1/video-generation/storage/status")

        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertNotIn("OPENAI_API_KEY", text)
        self.assertNotIn("RUNWAY_API_KEY=", text)
        self.assertNotIn("PIKA_API_KEY=", text)
        self.assertNotIn("sk-", text)
        self.assertNotIn("rk-", text)


if __name__ == "__main__":
    unittest.main()
