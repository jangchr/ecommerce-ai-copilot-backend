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
        self.assertEqual(completed_run["graph_version"], "agent_graph_runtime_v1")
        self.assertEqual(completed_run["graph_execution_mode"], "rule_driven_agent_graph")
        self.assertTrue(completed_run["is_autonomous_graph_runtime"])
        self.assertEqual(completed_run["autonomy_level"], "rule_driven_v1")
        self.assertFalse(completed_run["llm_autonomous_decision_enabled"])
        self.assertFalse(completed_run["external_api_called"])
        self.assertFalse(completed_run["cost_incurred_by_crossgrowth"])
        self.assertGreaterEqual(len(completed_run["graph_nodes"]), 10)
        self.assertGreaterEqual(len(completed_run["graph_edges"]), 10)
        self.assertTrue(completed_run["transition_decisions"])
        self.assertTrue(completed_run["validation_results"])
        self.assertIn("rework_loops", completed_run)
        self.assertIn("waiting_for_user", completed_run)
        self.assertEqual(completed_run["branch_selected"], "manual_external_tool_handoff")
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
        graph_statuses = {node["node_id"]: node["status"] for node in completed_run["graph_nodes"]}
        self.assertEqual(graph_statuses["product_identity_validator"], "complete")
        self.assertEqual(graph_statuses["route_selector_agent"], "complete")
        self.assertEqual(graph_statuses["provider_job_agent"], "waiting_for_user")
        self.assertEqual(graph_statuses["experiment_agent"], "waiting_for_user")

        events_response = self.client.get(f"/api/v1/agent-runs/{run_id}/events")
        self.assertEqual(events_response.status_code, 200, events_response.text)
        events = events_response.json()["events"]
        event_types = [event["event_type"] for event in events]
        self.assertIn("run_created", event_types)
        self.assertIn("run_started", event_types)
        self.assertIn("agent_started", event_types)
        self.assertIn("agent_completed", event_types)
        self.assertIn("graph_initialized", event_types)
        self.assertIn("node_started", event_types)
        self.assertIn("node_completed", event_types)
        self.assertIn("edge_traversed", event_types)
        self.assertIn("transition_decision", event_types)
        self.assertIn("validation_passed", event_types)
        self.assertIn("branch_selected", event_types)
        self.assertIn("waiting_for_user", event_types)
        self.assertIn("run_completed", event_types)
        self.assertIn("graph_completed", event_types)

    def test_invalid_run_id_returns_404(self):
        response = self.client.get("/api/v1/agent-runs/not-a-run")
        self.assertEqual(response.status_code, 404)

        events_response = self.client.get("/api/v1/agent-runs/not-a-run/events")
        self.assertEqual(events_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
