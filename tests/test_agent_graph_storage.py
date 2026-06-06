import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from agent_graph_storage import (
    load_artifact_registry_snapshot,
    load_recent_agent_run_snapshots,
    load_recent_video_job_snapshots,
    list_recent_agent_messages,
    list_recent_graph_events,
    list_recent_graph_exports,
    list_recent_graph_snapshots,
    persistence_metadata,
    save_agent_message_snapshot,
    save_agent_run_snapshot,
    save_artifact_registry_snapshot,
    save_graph_event_snapshot,
    save_graph_report_export,
    save_graph_state_snapshot,
    save_video_job_snapshot,
)


class AgentGraphStorageTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {"AGENT_GRAPH_STORAGE_PATH": self.temp_dir.name},
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp_dir.cleanup()

    def test_snapshots_round_trip_across_all_categories(self):
        save_agent_run_snapshot(
            {"run_id": "run_storage_1", "status": "completed", "updated_at": "2026-06-06T01:00:00Z"}
        )
        save_video_job_snapshot(
            {"job_id": "job_storage_1", "status": "processing", "updated_at": "2026-06-06T01:01:00Z"}
        )
        registry = {
            "registry_version": "artifact_registry_v1",
            "artifacts": [{"artifact_id": "artifact_1", "artifact_type": "video_generation_packet"}],
            "updated_at": "2026-06-06T01:02:00Z",
        }
        save_artifact_registry_snapshot(registry, "job_job_storage_1")
        save_graph_event_snapshot(
            "run_storage_1",
            [
                {
                    "event_id": "event_1",
                    "event_type": "graph_router_route_selected",
                    "agent_id": "graph_router_agent",
                    "message": "Selected keyframe rework.",
                    "created_at": "2026-06-06T01:03:00Z",
                }
            ],
        )
        save_agent_message_snapshot(
            {
                "message_id": "message_1",
                "message_version": "agent_message_v1",
                "message_type": "router_route",
                "created_at": "2026-06-06T01:04:00Z",
            }
        )
        save_graph_state_snapshot(
            {
                "snapshot_id": "snapshot_1",
                "snapshot_version": "graph_state_snapshot_v1",
                "created_at": "2026-06-06T01:05:00Z",
            }
        )
        save_graph_report_export(
            {
                "export_id": "export_1",
                "export_type": "agent_run_graph_report",
                "created_at": "2026-06-06T01:06:00Z",
            }
        )

        self.assertEqual(load_recent_agent_run_snapshots()[0]["run_id"], "run_storage_1")
        self.assertEqual(load_recent_video_job_snapshots()[0]["job_id"], "job_storage_1")
        self.assertEqual(
            load_artifact_registry_snapshot("job_job_storage_1")["registry_version"],
            "artifact_registry_v1",
        )
        self.assertEqual(list_recent_graph_events()[0]["event_type"], "graph_router_route_selected")
        self.assertEqual(list_recent_agent_messages()[0]["message_version"], "agent_message_v1")
        self.assertEqual(
            list_recent_graph_snapshots()[0]["snapshot_version"],
            "graph_state_snapshot_v1",
        )
        self.assertEqual(list_recent_graph_exports()[0]["export_id"], "export_1")

        metadata = persistence_metadata()
        self.assertEqual(metadata["persistence_mode"], "file_backed_lightweight_v1")
        self.assertIn("durability depends", metadata["durability_note"])

    def test_corrupt_json_is_ignored_without_breaking_history_reads(self):
        runs_dir = Path(self.temp_dir.name) / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        (runs_dir / "broken.json").write_text("{not valid json", encoding="utf-8")
        (runs_dir / "valid.json").write_text(
            json.dumps({"run_id": "valid_run", "updated_at": "2026-06-06T02:00:00Z"}),
            encoding="utf-8",
        )

        records = load_recent_agent_run_snapshots()

        self.assertEqual([record["run_id"] for record in records], ["valid_run"])


if __name__ == "__main__":
    unittest.main()
