import unittest

from fastapi.testclient import TestClient

from main import app


class MultiAgentWorkflowTests(unittest.TestCase):
    _cached_data = None

    def setUp(self):
        self.client = TestClient(app)

    def _generate(self):
        if MultiAgentWorkflowTests._cached_data is not None:
            return MultiAgentWorkflowTests._cached_data

        body = {
            "product_name": "Portable Mini Blender",
            "product_category": "kitchen_appliance",
            "product_description": "A compact rechargeable blender for smoothies and travel.",
            "pasted_reviews": (
                "Hard to clean after one smoothie.\n"
                "Too loud for early mornings.\n"
                "Small enough for travel but the cup sometimes leaks in my bag."
            ),
            "target_platform": "TikTok",
            "goal": "tiktok_ctr",
            "output_language": "en",
        }
        response = self.client.post("/api/v1/generate-from-reviews", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        MultiAgentWorkflowTests._cached_data = payload["data"]
        return MultiAgentWorkflowTests._cached_data

    def test_generate_from_reviews_returns_business_grounded_multi_agent_workflow(self):
        data = self._generate()
        workflow = data.get("multi_agent_workflow")

        self.assertIsInstance(workflow, dict)
        self.assertEqual(workflow.get("workflow_version"), "multi_agent_workflow_v2")
        self.assertEqual(workflow.get("execution_mode"), "artifact_orchestrated_agent_workflow")
        self.assertFalse(workflow.get("is_plain_automation"))
        self.assertFalse(workflow.get("is_real_multi_agent_execution"))

        agents = workflow.get("agents")
        self.assertIsInstance(agents, list)
        self.assertGreaterEqual(len(agents), 10)

        agent_ids = {agent.get("agent_id") for agent in agents}
        expected_agents = {
            "evidence_agent",
            "strategy_agent",
            "storyboard_agent",
            "asset_lock_agent",
            "keyframe_agent",
            "prompt_handoff_agent",
            "cost_agent",
            "risk_agent",
            "provider_job_agent",
            "experiment_agent",
        }
        self.assertTrue(expected_agents.issubset(agent_ids))

        for agent in agents:
            self.assertTrue(agent.get("role"))
            self.assertTrue(agent.get("goal"))
            self.assertTrue(agent.get("decision_summary"))
            self.assertIsInstance(agent.get("input_artifacts"), list)
            self.assertIsInstance(agent.get("output_artifacts"), list)
            self.assertIsInstance(agent.get("handoff_to"), list)
            self.assertIn("confidence_score", agent)
            self.assertIn("business_impact", agent)
            self.assertIn("requires_human_review", agent)

    def test_workflow_is_tied_to_real_business_artifacts(self):
        data = self._generate()
        workflow = data["multi_agent_workflow"]

        artifact_index = workflow.get("artifact_index") or {}
        self.assertTrue(artifact_index.get("llm_evidence_packet"))
        self.assertTrue(artifact_index.get("video_generation_packet"))
        self.assertTrue(artifact_index.get("external_video_tool_handoff"))
        self.assertTrue(artifact_index.get("agent_trace"))

        agents_by_id = {agent["agent_id"]: agent for agent in workflow["agents"]}

        evidence_agent = agents_by_id["evidence_agent"]
        self.assertIn("llm_evidence_packet", evidence_agent["input_artifacts"])
        self.assertIn("pain_points", evidence_agent["output_artifacts"])

        prompt_agent = agents_by_id["prompt_handoff_agent"]
        self.assertIn("external_video_tool_handoff", prompt_agent["input_artifacts"])
        self.assertIn("gemini_video_prompt", prompt_agent["output_artifacts"])
        self.assertFalse(prompt_agent["key_outputs"].get("external_api_called"))
        self.assertFalse(prompt_agent["key_outputs"].get("cost_incurred_by_crossgrowth"))

        cost_agent = agents_by_id["cost_agent"]
        self.assertEqual(cost_agent["status"], "ready_for_job_creation")
        self.assertTrue(cost_agent["requires_human_review"])

        provider_agent = agents_by_id["provider_job_agent"]
        self.assertEqual(provider_agent["status"], "waiting_for_user_action")

        experiment_agent = agents_by_id["experiment_agent"]
        self.assertEqual(experiment_agent["status"], "waiting_for_user_experiment")


if __name__ == "__main__":
    unittest.main()
