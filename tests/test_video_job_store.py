import tempfile
import unittest
from pathlib import Path

from video_generation.job_store import FileVideoJobStore, InMemoryVideoJobStore


def sample_job(job_id: str, created_at: str = "2026-06-02T00:00:00Z") -> dict:
    return {
        "job_id": job_id,
        "status": "ready_for_manual_export",
        "provider": "manual_export",
        "created_at": created_at,
        "updated_at": created_at,
        "result": {"result_url": ""},
    }


class VideoJobStoreTest(unittest.TestCase):
    def test_in_memory_store_create_get_update_list_clear(self):
        store = InMemoryVideoJobStore()
        first = store.create(sample_job("video_job_first", "2026-06-02T00:00:00Z"))
        second = store.create(sample_job("video_job_second", "2026-06-02T00:01:00Z"))

        self.assertEqual(first["job_id"], "video_job_first")
        self.assertEqual(store.get("video_job_first")["provider"], "manual_export")
        self.assertIsNone(store.get("video_job_missing"))

        first["status"] = "external_result_ready"
        updated = store.update("video_job_first", first)
        self.assertEqual(updated["status"], "external_result_ready")

        listed = store.list(limit=10)
        self.assertEqual([job["job_id"] for job in listed[:2]], ["video_job_second", "video_job_first"])

        store.clear()
        self.assertEqual(store.list(limit=10), [])
        self.assertIsNone(store.get("video_job_first"))

    def test_in_memory_store_returns_copies(self):
        store = InMemoryVideoJobStore()
        created = store.create(sample_job("video_job_copy"))
        created["status"] = "mutated"

        self.assertEqual(store.get("video_job_copy")["status"], "ready_for_manual_export")

    def test_file_store_create_get_update_list_clear(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "video_jobs.json"
            store = FileVideoJobStore(path)
            store.create(sample_job("video_job_first", "2026-06-02T00:00:00Z"))
            store.create(sample_job("video_job_second", "2026-06-02T00:01:00Z"))

            self.assertTrue(path.exists())
            self.assertEqual(store.get("video_job_first")["status"], "ready_for_manual_export")

            job = store.get("video_job_first")
            job["result"]["result_url"] = "https://example.com/video.mp4"
            store.update("video_job_first", job)

            reloaded = FileVideoJobStore(path)
            self.assertEqual(reloaded.get("video_job_first")["result"]["result_url"], "https://example.com/video.mp4")
            self.assertEqual([job["job_id"] for job in reloaded.list(limit=2)], ["video_job_second", "video_job_first"])

            reloaded.clear()
            self.assertEqual(reloaded.list(limit=10), [])

    def test_file_store_missing_or_corrupt_json_starts_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing" / "video_jobs.json"
            self.assertEqual(FileVideoJobStore(missing_path).list(), [])

            corrupt_path = Path(temp_dir) / "corrupt.json"
            corrupt_path.write_text("{not json", encoding="utf-8")
            self.assertIsNone(FileVideoJobStore(corrupt_path).get("video_job_missing"))
            self.assertEqual(FileVideoJobStore(corrupt_path).list(), [])


if __name__ == "__main__":
    unittest.main()
