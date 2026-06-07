import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from agent_runs import build_lightweight_artifact_registry, build_supervisor_planner_recommendation


def _project():
    return {
        "project_version": "project_workspace_v1",
        "project_id": "planner_project_1",
        "project_name": "Planner Test Project",
        "product_name": "Travel Blender",
        "product_category": "kitchen_appliance",
    }


def _source(source_type="pasted_reviews", review_count=3, warnings=None):
    return {
        "source_version": "project_source_v1",
        "source_id": "source_planner_1",
        "project_id": "planner_project_1",
        "source_type": source_type,
        "source_confidence": 0.82,
        "warnings": list(warnings or []),
        "source_summary": {
            "review_count": review_count,
            "unique_review_count": review_count,
            "manual_fallback_needed": review_count <= 0,
        },
    }


def _gate(status="passed", allows=True, warnings=None, evidence_readiness="ready"):
    return {
        "gate_version": "source_quality_gate_v1",
        "project_id": "planner_project_1",
        "source_id": "source_planner_1",
        "status": status,
        "allows_agent_run": allows,
        "evidence_readiness": evidence_readiness,
        "warnings": list(warnings or []),
    }


def _evidence(review_count=3):
    return {
        "artifact_version": "source_evidence_artifact_v1",
        "artifact_id": "source_evidence_1",
        "project_id": "planner_project_1",
        "source_id": "source_planner_1",
        "review_snippets": [f"review {index}" for index in range(review_count)],
        "evidence_quotes": [f"quote {index}" for index in range(review_count)],
        "source_confidence": 0.82,
    }


def _registry(extra_generation=None, uploaded_assets=None):
    generation = {
        "project_source": _source(),
        "source_quality_gate": _gate(),
        "source_evidence_artifact": _evidence(),
        "llm_evidence_packet": {"packet_version": "pasted_reviews_v1"},
        "video_generation_packet": {"packet_version": "video_generation_v1"},
        "external_video_tool_handoff": {"handoff_version": "external_video_tool_handoff_v1"},
        "product_asset_lock": {"lock_version": "product_asset_lock_v1"},
        "keyframe_plan": {"plan_version": "keyframe_plan_v1"},
    }
    generation.update(extra_generation or {})
    return build_lightweight_artifact_registry(
        generation_data=generation,
        project=_project(),
        uploaded_assets=uploaded_assets or [],
    )


class SupervisorPlannerRecommendationTests(unittest.TestCase):
    def assert_safety_false(self, recommendation):
        self.assertEqual(
            recommendation["safety_boundaries"],
            {
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
                "llm_autonomous_decision_enabled": False,
            },
        )

    def test_empty_project_recommends_add_source(self):
        recommendation = build_supervisor_planner_recommendation(project=_project())
        self.assertEqual(recommendation["overall_status"], "needs_source")
        self.assertEqual(recommendation["next_action_type"], "add_source")
        self.assertFalse(recommendation["can_start_agent_run"])
        self.assert_safety_false(recommendation)

    def test_amazon_source_without_reviews_recommends_paste_reviews(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(
                source_type="amazon_url",
                review_count=0,
                warnings=["manual_reviews_recommended"],
            ),
            source_quality_gate=_gate(
                status="fallback_required",
                allows=False,
                warnings=["manual_reviews_recommended"],
                evidence_readiness="needs_manual_reviews",
            ),
            source_evidence_artifact=_evidence(review_count=0),
        )
        self.assertEqual(recommendation["overall_status"], "needs_reviews")
        self.assertEqual(recommendation["next_action_type"], "paste_reviews")
        self.assertIn("customer_reviews", recommendation["missing_inputs"])
        self.assert_safety_false(recommendation)

    def test_ready_reviews_without_product_image_recommends_asset_but_allows_run(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            artifact_registry=_registry(),
        )
        self.assertEqual(recommendation["overall_status"], "asset_recommended")
        self.assertEqual(recommendation["next_action_type"], "upload_asset")
        self.assertTrue(recommendation["can_start_agent_run"])
        self.assert_safety_false(recommendation)

    def test_source_and_image_ready_recommends_start_agent_run(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            artifact_registry=_registry(
                uploaded_assets=[
                    {
                        "asset_version": "project_asset_v1",
                        "asset_id": "asset_product_1",
                        "project_id": "planner_project_1",
                        "asset_role": "product_image",
                    }
                ],
            ),
        )
        self.assertEqual(recommendation["overall_status"], "ready_for_agent_run")
        self.assertEqual(recommendation["next_action_type"], "start_agent_run")
        self.assertTrue(recommendation["can_start_agent_run"])

    def test_completed_agent_run_without_job_recommends_create_video_job(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            artifact_registry=_registry(),
            latest_run={
                "run_id": "run_1",
                "project_id": "planner_project_1",
                "status": "completed",
                "result": {
                    "video_generation_packet": {"packet_version": "video_generation_v1"},
                    "external_video_tool_handoff": {"handoff_version": "external_video_tool_handoff_v1"},
                },
            },
        )
        self.assertEqual(recommendation["overall_status"], "ready_for_video_job")
        self.assertEqual(recommendation["next_action_type"], "create_video_job")
        self.assertTrue(recommendation["can_create_video_job"])

    def test_job_without_experiment_recommends_record_experiment(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            latest_job={"job_id": "job_1", "project_id": "planner_project_1"},
        )
        self.assertEqual(recommendation["overall_status"], "waiting_for_experiment")
        self.assertEqual(recommendation["next_action_type"], "record_experiment")
        self.assertTrue(recommendation["can_record_experiment"])

    def test_bad_first_experiment_with_revised_artifact_recommends_rework_handoff(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            artifact_registry=build_lightweight_artifact_registry(
                generation_data={
                    "project_source": _source(),
                    "source_quality_gate": _gate(),
                    "source_evidence_artifact": _evidence(),
                },
                job={
                    "job_id": "job_1",
                    "project_id": "planner_project_1",
                    "external_video_experiments": [{"experiment_id": "exp_1"}],
                    "agent_graph_feedback": {
                        "latest_rework_artifact_type": "revised_keyframe_plan",
                    },
                },
                project=_project(),
            ),
            latest_job={
                "job_id": "job_1",
                "project_id": "planner_project_1",
                "external_video_experiments": [{"experiment_id": "exp_1"}],
                "latest_rework_artifact_type": "revised_keyframe_plan",
            },
        )
        self.assertEqual(recommendation["overall_status"], "needs_rework")
        self.assertEqual(recommendation["next_action_type"], "use_revised_handoff")

    def test_improved_second_experiment_recommends_approval(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            latest_job={
                "job_id": "job_1",
                "project_id": "planner_project_1",
                "external_video_experiments": [{"experiment_id": "exp_1"}, {"experiment_id": "exp_2"}],
                "latest_experiment_comparison_decision_gate": {
                    "decision_type": "proceed_to_controlled_test",
                },
            },
        )
        self.assertEqual(recommendation["overall_status"], "waiting_for_approval")
        self.assertEqual(recommendation["next_action_type"], "approve_controlled_test")
        self.assertTrue(recommendation["can_request_approval"])

    def test_approval_pending_blocks_provider_submit(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            approval_gate={
                "approval_gate_version": "human_approval_gate_v1",
                "status": "pending_approval",
                "blocks_provider_submit": True,
            },
        )
        self.assertEqual(recommendation["overall_status"], "waiting_for_approval")
        self.assertFalse(recommendation["can_submit_provider"])

    def test_approval_approved_allows_simulated_provider_submit(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            approval_gate={
                "approval_gate_version": "human_approval_gate_v1",
                "status": "approved",
                "blocks_provider_submit": False,
            },
        )
        self.assertEqual(recommendation["overall_status"], "provider_ready")
        self.assertEqual(recommendation["next_action_type"], "submit_provider_simulation")
        self.assertTrue(recommendation["can_submit_provider"])

    def test_provider_result_ready_recommends_export_report(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(),
            source_evidence_artifact=_evidence(),
            artifact_registry=build_lightweight_artifact_registry(
                generation_data={
                    "project_source": _source(),
                    "source_quality_gate": _gate(),
                    "source_evidence_artifact": _evidence(),
                },
                job={
                    "job_id": "job_1",
                    "project_id": "planner_project_1",
                    "provider_runtime": {"provider_status": "external_result_ready"},
                },
                project=_project(),
            ),
            latest_job={
                "job_id": "job_1",
                "project_id": "planner_project_1",
                "provider_runtime": {"provider_status": "external_result_ready"},
            },
        )
        self.assertEqual(recommendation["overall_status"], "completed")
        self.assertEqual(recommendation["next_action_type"], "export_report")

    def test_blocked_source_quality_gate_recommends_review_blocker(self):
        recommendation = build_supervisor_planner_recommendation(
            project=_project(),
            source=_source(),
            source_quality_gate=_gate(status="blocked", allows=False),
            source_evidence_artifact=_evidence(),
        )
        self.assertEqual(recommendation["overall_status"], "blocked")
        self.assertEqual(recommendation["next_action_type"], "review_blocker")
        self.assertTrue(recommendation["user_action_required"])



class SupervisorPlannerEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _create_project(self):
        response = self.client.post(
            "/api/v1/projects",
            json={
                "project_name": f"Planner Endpoint {uuid4().hex[:8]}",
                "product_name": "Travel Blender",
                "product_category": "kitchen_appliance",
                "source_type": "manual",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["project"]

    def test_project_planner_endpoint_empty_project(self):
        project = self._create_project()
        response = self.client.get(
            f"/api/v1/projects/{project['project_id']}/planner/recommendation"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        recommendation = payload["planner_recommendation"]
        self.assertEqual(recommendation["planner_version"], "supervisor_planner_v2")
        self.assertEqual(recommendation["overall_status"], "needs_source")
        self.assertEqual(recommendation["next_action_type"], "add_source")
        self.assertFalse(recommendation["can_start_agent_run"])

    def test_project_graph_summary_includes_planner_recommendation(self):
        project = self._create_project()
        response = self.client.get(f"/api/v1/projects/{project['project_id']}/graph-summary")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertIn("planner_recommendation", payload)
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_planner_status"],
            payload["planner_recommendation"]["overall_status"],
        )

    def test_project_source_updates_planner_recommendation(self):
        project = self._create_project()
        source_response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/sources",
            json={
                "source_type": "pasted_reviews",
                "product_name": "Travel Blender",
                "product_category": "kitchen_appliance",
                "product_description": "A compact blender for travel smoothies.",
                "pasted_reviews": (
                    "Hard to clean after one smoothie.\n"
                    "Too loud for early mornings.\n"
                    "Small enough for travel but the cup sometimes leaks in my bag.\n"
                    "Blends soft fruit well, but ice takes longer."
                ),
            },
        )
        self.assertEqual(source_response.status_code, 200)

        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/planner/recommendation/refresh"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["refreshed"])
        recommendation = payload["planner_recommendation"]
        self.assertIn(
            recommendation["overall_status"],
            {"asset_recommended", "ready_for_agent_run"},
        )
        self.assertTrue(recommendation["can_start_agent_run"])
        self.assertEqual(
            recommendation["safety_boundaries"]["external_api_called"],
            False,
        )


if __name__ == "__main__":
    unittest.main()
