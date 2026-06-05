import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import AGENT_RUN_STORE, app
from tests.test_pasted_reviews_endpoint import GENERATED_REVIEWS_BRIEF, VALID_REVIEWS_REQUEST


class AgentRunsEndpointTest(unittest.TestCase):
    def setUp(self):
        AGENT_RUN_STORE.clear()
        self.client = TestClient(app)

    def test_create_poll_events_and_complete_agent_run_from_reviews(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ) as generate:
            response = self.client.post(
                "/api/v1/agent-runs/from-reviews",
                json=VALID_REVIEWS_REQUEST,
                headers={"X-Request-ID": "agent-run-test-1"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        generate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "agent-run-test-1")
        self.assertIn("/api/v1/agent-runs/", payload["poll_url"])
        self.assertIn("/events", payload["events_url"])

        created_run = payload["run"]
        run_id = created_run["run_id"]
        self.assertIn(created_run["status"], {"queued", "running"})
        self.assertEqual(created_run["input_type"], "pasted_reviews")
        self.assertFalse(created_run["external_api_called"])
        self.assertFalse(created_run["cost_incurred_by_crossgrowth"])

        completed_run = None
        for _ in range(10):
            run_response = self.client.get(f"/api/v1/agent-runs/{run_id}")
            self.assertEqual(run_response.status_code, 200, run_response.text)
            run_payload = run_response.json()
            completed_run = run_payload["run"]
            if completed_run["status"] == "completed":
                break
            time.sleep(0.05)

        self.assertIsNotNone(completed_run)
        self.assertEqual(completed_run["status"], "completed")
        self.assertFalse(completed_run["external_api_called"])
        self.assertFalse(completed_run["cost_incurred_by_crossgrowth"])
        self.assertIsInstance(completed_run["result"], dict)
        self.assertIn("video_generation_packet", completed_run["result"])
        self.assertIn("external_video_tool_handoff", completed_run["result"])
        self.assertIn("multi_agent_workflow", completed_run["result"])
        self.assertEqual(
            completed_run["result"]["video_generation_packet"]["packet_version"],
            "video_generation_v1",
        )

        agent_statuses = {agent["agent_id"]: agent["status"] for agent in completed_run["agents"]}
        self.assertEqual(agent_statuses["planner_agent"], "complete")
        self.assertEqual(agent_statuses["evidence_agent"], "complete")
        self.assertEqual(agent_statuses["finalizer_agent"], "complete")

        events_response = self.client.get(f"/api/v1/agent-runs/{run_id}/events")
        self.assertEqual(events_response.status_code, 200, events_response.text)
        events = events_response.json()["events"]
        event_types = [event["event_type"] for event in events]
        self.assertIn("run_created", event_types)
        self.assertIn("run_started", event_types)
        self.assertIn("agent_started", event_types)
        self.assertIn("agent_completed", event_types)
        self.assertIn("run_completed", event_types)

    def test_invalid_run_id_returns_404(self):
        response = self.client.get("/api/v1/agent-runs/not-a-run")
        self.assertEqual(response.status_code, 404)

        events_response = self.client.get("/api/v1/agent-runs/not-a-run/events")
        self.assertEqual(events_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
