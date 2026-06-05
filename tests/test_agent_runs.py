from copy import deepcopy
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agent_runs import apply_evidence_safe_storyboard_rework, detect_storyboard_rework_need
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
        self.assertEqual(completed_run["rework_loops"], [])
        self.assertEqual(completed_run["loop_count"], 0)
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

    def test_storyboard_rework_detection_helper(self):
        risky_data = {
            "assets": {
                "tiktok_script": {
                    "hook": "This 100% guaranteed blender will never leak.",
                    "cta": "Choose the #1 best on the market travel blender.",
                },
                "storyboard": {
                    "scenes": [
                        {
                            "visual_description": "Show a no leaks guaranteed bag test.",
                            "narration": "It always eliminates messy mornings.",
                            "evidence_quote_used": "The cup sometimes leaks in my bag.",
                        }
                    ]
                },
            },
            "evaluation": {"risk_level": "medium"},
        }

        result = detect_storyboard_rework_need(risky_data)

        self.assertTrue(result["needs_rework"])
        self.assertEqual(result["severity"], "high")
        self.assertIn("100%", result["matched_terms"])
        self.assertIn("guaranteed", result["matched_terms"])

    def test_storyboard_rework_application_helper(self):
        risky_data = {
            "insights": {"evidence": {"data_warnings": []}},
            "assets": {
                "tiktok_script": {
                    "hook": "This 100% guaranteed blender will never leak.",
                    "cta": "Choose the best on the market option.",
                },
                "storyboard": {
                    "product_name": "Portable Mini Blender",
                    "product_category": "kitchen_appliance",
                    "scenes": [
                        {
                            "visual_description": "Show a no leaks guaranteed bag test.",
                            "narration": "It always eliminates messy mornings.",
                            "evidence_quote_used": "The cup sometimes leaks in my bag.",
                        }
                    ],
                },
            },
            "evaluation": {"risk_level": "high", "reasoning": "Needs review."},
        }

        reworked = apply_evidence_safe_storyboard_rework(
            risky_data,
            "Unsupported storyboard wording detected.",
            ["100%", "guaranteed", "never"],
        )

        self.assertIn("agent_graph_rework_summary", reworked)
        self.assertEqual(reworked["agent_graph_rework_summary"]["rework_version"], "risk_storyboard_rework_v1")
        self.assertEqual(reworked["assets"]["storyboard"]["product_name"], "Portable Mini Blender")
        self.assertEqual(reworked["assets"]["storyboard"]["product_category"], "kitchen_appliance")
        self.assertNotIn("100%", reworked["assets"]["tiktok_script"]["hook"])
        self.assertNotIn("guaranteed", reworked["assets"]["tiktok_script"]["hook"].lower())
        self.assertNotIn("never", reworked["assets"]["tiktok_script"]["hook"].lower())
        self.assertEqual(
            reworked["assets"]["storyboard"]["scenes"][0]["evidence_quote_used"],
            "The cup sometimes leaks in my bag.",
        )
        self.assertIn(
            "storyboard_reworked_for_evidence_safety",
            reworked["insights"]["evidence"]["data_warnings"],
        )
        self.assertEqual(reworked["evaluation"]["risk_level"], "medium")

    def test_agent_graph_runtime_records_rework_loop_when_storyboard_risk_detected(self):
        risky_generated = deepcopy(GENERATED_REVIEWS_BRIEF)
        risky_generated["hook"] = "This 100% guaranteed mini blender will never leak."
        risky_generated["cta"] = "Use the leak-proof guarantee for every trip."
        risky_generated["storyboard_scenes"][0]["visual_description"] = "Show no leaks guaranteed in a backpack."
        risky_generated["storyboard_scenes"][0]["narration"] = "This blender always eliminates leaks."

        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=risky_generated),
        ):
            response = self.client.post(
                "/api/v1/agent-runs/from-reviews",
                json=VALID_REVIEWS_REQUEST,
                headers={"X-Request-ID": "agent-run-rework-test-1"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        run_id = response.json()["run"]["run_id"]
        completed_run = None
        for _ in range(10):
            run_response = self.client.get(f"/api/v1/agent-runs/{run_id}")
            self.assertEqual(run_response.status_code, 200, run_response.text)
            completed_run = run_response.json()["run"]
            if completed_run["status"] == "completed":
                break
            time.sleep(0.05)

        self.assertIsNotNone(completed_run)
        self.assertEqual(completed_run["status"], "completed")
        self.assertGreaterEqual(len(completed_run["rework_loops"]), 1)
        self.assertTrue(any(loop["status"] == "applied" for loop in completed_run["rework_loops"]))
        self.assertEqual(completed_run["loop_count"], 1)
        self.assertLessEqual(completed_run["loop_count"], completed_run["max_loop_count"])
        self.assertTrue(
            any(decision["decision_type"] == "rework_requested" for decision in completed_run["transition_decisions"])
        )
        edge_statuses = {edge["edge_id"]: edge["status"] for edge in completed_run["graph_edges"]}
        self.assertEqual(edge_statuses["risk_to_storyboard_rework"], "traversed")
        self.assertFalse(completed_run["external_api_called"])
        self.assertFalse(completed_run["cost_incurred_by_crossgrowth"])

        final_data = completed_run["result"]
        self.assertIn("agent_graph_rework_summary", final_data)
        self.assertEqual(
            final_data["agent_graph_rework_summary"]["rework_version"],
            "risk_storyboard_rework_v1",
        )
        hook = final_data["assets"]["tiktok_script"]["hook"].lower()
        scene_narration = final_data["assets"]["storyboard"]["scenes"][0]["narration"].lower()
        self.assertNotIn("100%", hook)
        self.assertNotIn("guaranteed", hook)
        self.assertNotIn("never", hook)
        self.assertNotIn("always", scene_narration)

        events = self.client.get(f"/api/v1/agent-runs/{run_id}/events").json()["events"]
        event_types = [event["event_type"] for event in events]
        self.assertIn("validation_failed", event_types)
        self.assertIn("rework_requested", event_types)
        self.assertIn("edge_traversed", event_types)

    def test_invalid_run_id_returns_404(self):
        response = self.client.get("/api/v1/agent-runs/not-a-run")
        self.assertEqual(response.status_code, 404)

        events_response = self.client.get("/api/v1/agent-runs/not-a-run/events")
        self.assertEqual(events_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
