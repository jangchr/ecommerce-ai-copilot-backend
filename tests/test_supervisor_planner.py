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


class AgentRunnerPlanEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _create_project(self):
        response = self.client.post(
            "/api/v1/projects",
            json={
                "project_name": f"Runner Plan Endpoint {uuid4().hex[:8]}",
                "product_name": "Travel Blender",
                "product_category": "kitchen_appliance",
                "source_type": "manual",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["project"]

    def test_project_runner_plan_endpoint_empty_project_waits_for_user(self):
        project = self._create_project()
        response = self.client.get(
            f"/api/v1/projects/{project['project_id']}/runner/plan"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])

        plan = payload["runner_plan"]
        summary = payload["runner_plan_summary"]
        self.assertEqual(plan["runner_plan_version"], "agent_runner_plan_v1")
        self.assertEqual(plan["execution_status"], "waiting_for_user")
        self.assertFalse(plan["can_execute_next_agent"])
        self.assertTrue(plan["requires_user_action"])
        self.assertEqual(plan["next_agent_id"], "source_adapter_agent")
        self.assertEqual(plan["next_action_type"], "add_source")
        self.assertTrue(plan["handoff_message"]["handoff_valid"], plan["handoff_message"])
        self.assertEqual(summary["summary_version"], "agent_runner_plan_summary_v1")
        self.assertEqual(summary["execution_status"], plan["execution_status"])
        self.assertIn("agent_contract_registry", payload)
        self.assertIn("agent_contract_summary", payload)
        self.assertIn("agent_contract_completeness_report", payload)
        contract_report = payload["agent_contract_completeness_report"]
        self.assertEqual(
            contract_report["completeness_report_version"],
            "agent_contract_completeness_report_v1",
        )
        self.assertEqual(contract_report["report_status"], "agent_contract_registry_complete")
        self.assertEqual(contract_report["missing_role_count"], 0)
        self.assertTrue(contract_report["supervisor_can_use_registry"])
        self.assertFalse(contract_report["real_execution_allowed"])
        self.assertFalse(contract_report["provider_call_allowed"])
        self.assertFalse(contract_report["external_api_call_allowed"])
        self.assertFalse(contract_report["agent_execution_allowed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_agent_contract_report_status"],
            "agent_contract_registry_complete",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_agent_contract_missing_role_count"],
            0,
        )
        self.assertTrue(
            payload["project"]["graph_summary"]["latest_agent_contract_supervisor_can_use_registry"]
        )
        self.assertIn("source_adapter_contract_report", payload)
        source_adapter_report = payload["source_adapter_contract_report"]
        self.assertEqual(
            source_adapter_report["source_adapter_contract_report_version"],
            "source_adapter_contract_report_v1",
        )
        self.assertEqual(source_adapter_report["report_status"], "source_adapter_contracts_complete")
        self.assertEqual(source_adapter_report["missing_adapter_count"], 0)
        self.assertTrue(source_adapter_report["supports_amazon_visible_reviews"])
        self.assertTrue(source_adapter_report["supports_pasted_reviews"])
        self.assertTrue(source_adapter_report["supports_external_crawler_dry_run"])
        self.assertFalse(source_adapter_report["real_source_adapter_enabled"])
        self.assertFalse(source_adapter_report["external_fetch_performed"])
        self.assertFalse(source_adapter_report["external_api_called"])
        self.assertFalse(source_adapter_report["agent_execution_performed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_source_adapter_contract_report_status"],
            "source_adapter_contracts_complete",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_source_adapter_contract_missing_count"],
            0,
        )
        self.assertTrue(
            payload["project"]["graph_summary"]["latest_source_adapter_contract_supports_external_crawler_dry_run"]
        )
        self.assertIn("multi_agent_output_chain_report", payload)
        output_chain = payload["multi_agent_output_chain_report"]
        self.assertEqual(
            output_chain["multi_agent_output_chain_report_version"],
            "multi_agent_output_chain_report_v1",
        )
        self.assertEqual(output_chain["report_status"], "multi_agent_output_chain_ready_dry_run")
        self.assertEqual(output_chain["missing_stage_count"], 0)
        self.assertTrue(output_chain["supports_evidence_to_strategy"])
        self.assertTrue(output_chain["supports_strategy_to_creative"])
        self.assertTrue(output_chain["supports_creative_to_video"])
        self.assertTrue(output_chain["supports_risk_to_finalizer"])
        self.assertFalse(output_chain["real_execution_allowed"])
        self.assertFalse(output_chain["provider_call_allowed"])
        self.assertFalse(output_chain["external_api_call_allowed"])
        self.assertFalse(output_chain["agent_execution_allowed"])
        self.assertFalse(output_chain["video_generation_performed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_multi_agent_output_chain_status"],
            "multi_agent_output_chain_ready_dry_run",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_multi_agent_output_missing_stage_count"],
            0,
        )
        self.assertTrue(
            payload["project"]["graph_summary"]["latest_multi_agent_output_supports_creative_to_video"]
        )
        self.assertIn("keyframe_video_asset_chain_report", payload)
        asset_chain = payload["keyframe_video_asset_chain_report"]
        self.assertEqual(
            asset_chain["keyframe_video_asset_chain_report_version"],
            "keyframe_video_asset_chain_report_v1",
        )
        self.assertEqual(asset_chain["report_status"], "keyframe_video_asset_chain_ready_dry_run")
        self.assertEqual(asset_chain["missing_stage_count"], 0)
        self.assertTrue(asset_chain["supports_product_asset_lock"])
        self.assertTrue(asset_chain["supports_keyframe_scene_plan"])
        self.assertTrue(asset_chain["supports_prompt_handoff_pack"])
        self.assertTrue(asset_chain["supports_manual_generation_handoff"])
        self.assertTrue(asset_chain["provider_neutral_prompt_pack_ready"])
        self.assertTrue(asset_chain["manual_generation_handoff_ready"])
        self.assertTrue(asset_chain["image_reference_required"])
        self.assertTrue(asset_chain["human_approval_required_before_generation"])
        self.assertFalse(asset_chain["real_execution_allowed"])
        self.assertFalse(asset_chain["provider_call_allowed"])
        self.assertFalse(asset_chain["external_api_call_allowed"])
        self.assertFalse(asset_chain["video_generation_performed"])
        self.assertFalse(asset_chain["image_generation_performed"])
        self.assertFalse(asset_chain["paid_generation_allowed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_keyframe_video_asset_chain_status"],
            "keyframe_video_asset_chain_ready_dry_run",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_keyframe_video_asset_missing_stage_count"],
            0,
        )
        self.assertTrue(
            payload["project"]["graph_summary"]["latest_keyframe_video_asset_supports_manual_handoff"]
        )
        self.assertIn("keyframe_prompt_pack_report", payload)
        prompt_pack = payload["keyframe_prompt_pack_report"]
        self.assertEqual(
            prompt_pack["keyframe_prompt_pack_report_version"],
            "keyframe_prompt_pack_report_v1",
        )
        self.assertEqual(prompt_pack["report_status"], "keyframe_prompt_pack_ready_dry_run")
        self.assertEqual(prompt_pack["missing_item_count"], 0)
        self.assertEqual(prompt_pack["shot_prompt_count"], 4)
        self.assertEqual(prompt_pack["provider_variant_count"], 4)
        self.assertEqual(set(prompt_pack["provider_ids"]), {"gemini", "doubao", "runway", "pika"})
        self.assertTrue(prompt_pack["supports_negative_prompt"])
        self.assertTrue(prompt_pack["supports_image_reference_checklist"])
        self.assertTrue(prompt_pack["manual_copy_paste_only"])
        self.assertTrue(prompt_pack["image_reference_required"])
        self.assertFalse(prompt_pack["real_execution_allowed"])
        self.assertFalse(prompt_pack["provider_call_allowed"])
        self.assertFalse(prompt_pack["external_api_call_allowed"])
        self.assertFalse(prompt_pack["video_generation_performed"])
        self.assertFalse(prompt_pack["image_generation_performed"])
        self.assertFalse(prompt_pack["paid_generation_allowed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_keyframe_prompt_pack_status"],
            "keyframe_prompt_pack_ready_dry_run",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_keyframe_prompt_pack_shot_prompt_count"],
            4,
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_keyframe_prompt_pack_provider_variant_count"],
            4,
        )
        self.assertTrue(
            payload["project"]["graph_summary"]["latest_keyframe_prompt_pack_manual_copy_only"]
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_plan_status"],
            plan["execution_status"],
        )
        self.assertFalse(plan["safety_boundaries"]["external_api_called"])
        self.assertFalse(plan["safety_boundaries"]["cost_incurred_by_crossgrowth"])
        self.assertFalse(plan["safety_boundaries"]["llm_autonomous_decision_enabled"])

    def test_project_runner_plan_refresh_endpoint_matches_plan_shape(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/plan/refresh"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertIn("planner_recommendation", payload)
        self.assertIn("runner_plan", payload)
        self.assertIn("runner_plan_summary", payload)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(
            payload["runner_plan"]["runner_plan_version"],
            "agent_runner_plan_v1",
        )
        self.assertEqual(
            payload["runner_plan_summary"]["runner_plan_version"],
            "agent_runner_plan_v1",
        )

    def test_project_runner_plan_after_source_keeps_contract_validation(self):
        project = self._create_project()
        source_response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/sources",
            json={
                "source_type": "pasted_reviews",
                "product_name": "Travel Blender",
                "product_category": "kitchen_appliance",
                "raw_text": "Great for office smoothies. Small enough for travel. Cup can leak in my bag.",
                "source_url": "",
                "metadata": {"test_case": "runner_plan_after_source"},
            },
        )
        self.assertEqual(source_response.status_code, 200)

        response = self.client.get(
            f"/api/v1/projects/{project['project_id']}/runner/plan"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        plan = payload["runner_plan"]

        self.assertEqual(plan["runner_plan_version"], "agent_runner_plan_v1")
        self.assertIn(
            plan["execution_status"],
            {"ready", "ready_with_optional_user_input", "waiting_for_user", "blocked"},
        )
        self.assertIn("contract_validation", plan)
        self.assertIn("planned_steps", plan)
        self.assertGreaterEqual(len(plan["planned_steps"]), 2)
        self.assertFalse(plan["safety_boundaries"]["external_api_called"])

    def test_project_runner_plan_endpoint_includes_dispatch_ticket(self):
        project = self._create_project()
        response = self.client.get(
            f"/api/v1/projects/{project['project_id']}/runner/plan"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("runner_dispatch_ticket", payload)
        self.assertIn("runner_dispatch_summary", payload)

        ticket = payload["runner_dispatch_ticket"]
        summary = payload["runner_dispatch_summary"]
        self.assertEqual(ticket["dispatch_ticket_version"], "agent_runner_dispatch_ticket_v1")
        self.assertTrue(ticket["dry_run"])
        self.assertFalse(ticket["external_api_called"])
        self.assertFalse(ticket["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_dispatch_summary_v1")
        self.assertEqual(summary["dispatch_status"], ticket["dispatch_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_dispatch_status"],
            ticket["dispatch_status"],
        )

    def test_project_runner_plan_endpoint_includes_dispatch_event(self):
        project = self._create_project()
        response = self.client.get(
            f"/api/v1/projects/{project['project_id']}/runner/plan"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("runner_dispatch_event", payload)
        self.assertIn("runner_dispatch_event_summary", payload)

        event = payload["runner_dispatch_event"]
        summary = payload["runner_dispatch_event_summary"]
        self.assertEqual(event["dispatch_event_version"], "agent_runner_dispatch_event_v1")
        self.assertEqual(event["event_type"], "runner_dispatch_dry_run")
        self.assertTrue(event["dry_run"])
        self.assertFalse(event["external_api_called"])
        self.assertFalse(event["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_dispatch_event_summary_v1")
        self.assertEqual(summary["event_status"], event["event_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_dispatch_event_status"],
            event["event_status"],
        )

    def test_project_runner_dispatch_dry_run_endpoint_returns_ticket_and_event(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/dispatch/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["dispatch_executed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])

        self.assertIn("runner_plan", payload)
        self.assertIn("runner_dispatch_ticket", payload)
        self.assertIn("runner_dispatch_event", payload)
        self.assertIn("runner_dispatch_summary", payload)
        self.assertIn("runner_dispatch_event_summary", payload)

        ticket = payload["runner_dispatch_ticket"]
        event = payload["runner_dispatch_event"]
        self.assertEqual(ticket["dispatch_ticket_version"], "agent_runner_dispatch_ticket_v1")
        self.assertEqual(event["dispatch_event_version"], "agent_runner_dispatch_event_v1")
        self.assertEqual(event["event_type"], "runner_dispatch_dry_run")
        self.assertTrue(event["dry_run"])
        self.assertFalse(event["external_api_called"])
        self.assertFalse(event["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_dispatch_dry_run_event_status"],
            event["event_status"],
        )

    def test_project_runner_execute_dry_run_endpoint_returns_execution_receipt(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/execute/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_execution_receipt", payload)
        self.assertIn("runner_execution_receipt_summary", payload)

        receipt = payload["runner_execution_receipt"]
        summary = payload["runner_execution_receipt_summary"]
        self.assertEqual(receipt["execution_receipt_version"], "agent_runner_execution_receipt_v1")
        self.assertFalse(receipt["execution_performed"])
        self.assertTrue(receipt["dry_run"])
        self.assertFalse(receipt["external_api_called"])
        self.assertFalse(receipt["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_execution_receipt_summary_v1")
        self.assertEqual(summary["receipt_status"], receipt["receipt_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_execution_receipt_status"],
            receipt["receipt_status"],
        )

    def test_project_runner_work_order_dry_run_endpoint_returns_work_order(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/work-order/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_work_order", payload)
        self.assertIn("runner_work_order_summary", payload)

        order = payload["runner_work_order"]
        summary = payload["runner_work_order_summary"]
        self.assertEqual(order["work_order_version"], "agent_runner_work_order_v1")
        self.assertTrue(order["dry_run"])
        self.assertFalse(order["agent_execution_performed"])
        self.assertFalse(order["external_api_called"])
        self.assertFalse(order["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_work_order_summary_v1")
        self.assertEqual(summary["work_order_status"], order["work_order_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_work_order_status"],
            order["work_order_status"],
        )

    def test_project_runner_queue_dry_run_endpoint_returns_queue_item(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/queue/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["queue_persisted"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_queue_item", payload)
        self.assertIn("runner_queue_item_summary", payload)

        item = payload["runner_queue_item"]
        summary = payload["runner_queue_item_summary"]
        self.assertEqual(item["queue_item_version"], "agent_runner_queue_item_v1")
        self.assertTrue(item["dry_run"])
        self.assertFalse(item["queue_persisted"])
        self.assertFalse(item["agent_execution_performed"])
        self.assertFalse(item["external_api_called"])
        self.assertFalse(item["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_queue_item_summary_v1")
        self.assertEqual(summary["queue_status"], item["queue_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_queue_status"],
            item["queue_status"],
        )

    def test_project_runner_claim_dry_run_endpoint_returns_queue_claim(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/claim/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["claim_persisted"])
        self.assertFalse(payload["lease_acquired"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_queue_claim", payload)
        self.assertIn("runner_queue_claim_summary", payload)

        claim = payload["runner_queue_claim"]
        summary = payload["runner_queue_claim_summary"]
        self.assertEqual(claim["claim_version"], "agent_runner_queue_claim_v1")
        self.assertTrue(claim["dry_run"])
        self.assertFalse(claim["claim_persisted"])
        self.assertFalse(claim["lease_acquired"])
        self.assertFalse(claim["agent_execution_performed"])
        self.assertFalse(claim["external_api_called"])
        self.assertFalse(claim["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_queue_claim_summary_v1")
        self.assertEqual(summary["claim_status"], claim["claim_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_claim_status"],
            claim["claim_status"],
        )

    def test_project_runner_lease_dry_run_endpoint_returns_worker_lease(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/lease/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["lease_persisted"])
        self.assertFalse(payload["lease_acquired"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_worker_lease", payload)
        self.assertIn("runner_worker_lease_summary", payload)

        lease = payload["runner_worker_lease"]
        summary = payload["runner_worker_lease_summary"]
        self.assertEqual(lease["worker_lease_version"], "agent_runner_worker_lease_v1")
        self.assertTrue(lease["dry_run"])
        self.assertFalse(lease["lease_persisted"])
        self.assertFalse(lease["lease_acquired"])
        self.assertFalse(lease["agent_execution_performed"])
        self.assertFalse(lease["external_api_called"])
        self.assertFalse(lease["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_worker_lease_summary_v1")
        self.assertEqual(summary["lease_status"], lease["lease_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_worker_lease_status"],
            lease["lease_status"],
        )

    def test_project_runner_invoke_dry_run_endpoint_returns_invocation_attempt(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/invoke/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_invocation_envelope", payload)
        self.assertIn("runner_invocation_attempt", payload)
        self.assertIn("runner_invocation_attempt_summary", payload)

        envelope = payload["runner_invocation_envelope"]
        attempt = payload["runner_invocation_attempt"]
        summary = payload["runner_invocation_attempt_summary"]
        self.assertEqual(envelope["invocation_envelope_version"], "agent_runner_invocation_envelope_v1")
        self.assertEqual(attempt["invocation_attempt_version"], "agent_runner_invocation_attempt_v1")
        self.assertTrue(attempt["dry_run"])
        self.assertFalse(attempt["agent_invoked"])
        self.assertFalse(attempt["agent_execution_performed"])
        self.assertFalse(attempt["external_api_called"])
        self.assertFalse(attempt["cost_incurred_by_crossgrowth"])
        self.assertEqual(summary["summary_version"], "agent_runner_invocation_attempt_summary_v1")
        self.assertEqual(summary["attempt_status"], attempt["attempt_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_invocation_attempt_status"],
            attempt["attempt_status"],
        )

    def test_project_runner_result_dry_run_endpoint_returns_result_and_completion(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/result/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["completion_recorded"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_invocation_result", payload)
        self.assertIn("runner_completion_receipt", payload)
        self.assertIn("runner_completion_receipt_summary", payload)

        result = payload["runner_invocation_result"]
        completion = payload["runner_completion_receipt"]
        summary = payload["runner_completion_receipt_summary"]
        self.assertEqual(result["invocation_result_version"], "agent_runner_invocation_result_v1")
        self.assertEqual(completion["completion_receipt_version"], "agent_runner_completion_receipt_v1")
        self.assertTrue(completion["dry_run"])
        self.assertFalse(completion["completion_recorded"])
        self.assertFalse(completion["agent_output_generated"])
        self.assertFalse(completion["agent_invoked"])
        self.assertFalse(completion["agent_execution_performed"])
        self.assertEqual(summary["summary_version"], "agent_runner_completion_receipt_summary_v1")
        self.assertEqual(summary["completion_status"], completion["completion_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_completion_status"],
            completion["completion_status"],
        )

    def test_project_runner_checkpoint_dry_run_endpoint_returns_checkpoint_and_unlock(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/checkpoint/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["handoff_checkpoint_recorded"])
        self.assertFalse(payload["handoff_complete"])
        self.assertFalse(payload["next_agent_unlocked"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_handoff_checkpoint", payload)
        self.assertIn("runner_next_agent_unlock", payload)
        self.assertIn("runner_next_agent_unlock_summary", payload)

        checkpoint = payload["runner_handoff_checkpoint"]
        unlock = payload["runner_next_agent_unlock"]
        summary = payload["runner_next_agent_unlock_summary"]
        self.assertEqual(checkpoint["handoff_checkpoint_version"], "agent_runner_handoff_checkpoint_v1")
        self.assertEqual(unlock["next_agent_unlock_version"], "agent_runner_next_agent_unlock_v1")
        self.assertTrue(unlock["dry_run"])
        self.assertFalse(unlock["handoff_complete"])
        self.assertFalse(unlock["next_agent_unlocked"])
        self.assertFalse(unlock["unlock_recorded"])
        self.assertEqual(summary["summary_version"], "agent_runner_next_agent_unlock_summary_v1")
        self.assertEqual(summary["unlock_status"], unlock["unlock_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_next_agent_unlock_status"],
            unlock["unlock_status"],
        )

    def test_project_runner_transition_dry_run_endpoint_returns_transition_projection(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/transition/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["graph_transition_persisted"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["next_agent_unlocked"])
        self.assertFalse(payload["handoff_complete"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_graph_transition_proposal", payload)
        self.assertIn("runner_state_projection", payload)
        self.assertIn("runner_state_projection_summary", payload)

        proposal = payload["runner_graph_transition_proposal"]
        projection = payload["runner_state_projection"]
        summary = payload["runner_state_projection_summary"]
        self.assertEqual(proposal["graph_transition_proposal_version"], "agent_runner_graph_transition_proposal_v1")
        self.assertEqual(projection["state_projection_version"], "agent_runner_state_projection_v1")
        self.assertTrue(projection["dry_run"])
        self.assertFalse(projection["state_persisted"])
        self.assertFalse(projection["project_snapshot_saved"])
        self.assertFalse(projection["agent_execution_performed"])
        self.assertEqual(summary["summary_version"], "agent_runner_state_projection_summary_v1")
        self.assertEqual(summary["projection_status"], projection["projection_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_transition_status"],
            proposal["transition_status"],
        )

    def test_project_runner_commit_plan_dry_run_endpoint_returns_guard(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/commit-plan/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["commit_plan_persisted"])
        self.assertFalse(payload["mutation_guard_recorded"])
        self.assertFalse(payload["mutation_allowed"])
        self.assertFalse(payload["graph_transition_persisted"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["next_agent_unlocked"])
        self.assertFalse(payload["handoff_complete"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_transition_commit_plan", payload)
        self.assertIn("runner_mutation_guard", payload)
        self.assertIn("runner_mutation_guard_summary", payload)

        commit_plan = payload["runner_transition_commit_plan"]
        guard = payload["runner_mutation_guard"]
        summary = payload["runner_mutation_guard_summary"]
        self.assertEqual(commit_plan["transition_commit_plan_version"], "agent_runner_transition_commit_plan_v1")
        self.assertEqual(guard["mutation_guard_version"], "agent_runner_mutation_guard_v1")
        self.assertTrue(guard["dry_run"])
        self.assertFalse(guard["mutation_allowed"])
        self.assertFalse(guard["mutation_guard_recorded"])
        self.assertFalse(guard["state_persisted"])
        self.assertFalse(guard["project_snapshot_saved"])
        self.assertEqual(summary["summary_version"], "agent_runner_mutation_guard_summary_v1")
        self.assertEqual(summary["mutation_guard_status"], guard["mutation_guard_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_commit_plan_status"],
            commit_plan["commit_plan_status"],
        )

    def test_project_runner_persist_request_dry_run_endpoint_returns_rollback_plan(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/persist-request/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["persist_request_recorded"])
        self.assertFalse(payload["rollback_plan_recorded"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["rollback_available"])
        self.assertFalse(payload["rollback_applied"])
        self.assertFalse(payload["commit_plan_persisted"])
        self.assertFalse(payload["mutation_guard_recorded"])
        self.assertFalse(payload["graph_transition_persisted"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["next_agent_unlocked"])
        self.assertFalse(payload["handoff_complete"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_transition_persist_request", payload)
        self.assertIn("runner_rollback_plan", payload)
        self.assertIn("runner_rollback_plan_summary", payload)

        persist_request = payload["runner_transition_persist_request"]
        rollback_plan = payload["runner_rollback_plan"]
        summary = payload["runner_rollback_plan_summary"]
        self.assertEqual(persist_request["transition_persist_request_version"], "agent_runner_transition_persist_request_v1")
        self.assertEqual(rollback_plan["rollback_plan_version"], "agent_runner_rollback_plan_v1")
        self.assertTrue(rollback_plan["dry_run"])
        self.assertFalse(rollback_plan["rollback_available"])
        self.assertFalse(rollback_plan["rollback_applied"])
        self.assertFalse(rollback_plan["state_persisted"])
        self.assertFalse(rollback_plan["project_snapshot_saved"])
        self.assertEqual(summary["summary_version"], "agent_runner_rollback_plan_summary_v1")
        self.assertEqual(summary["rollback_plan_status"], rollback_plan["rollback_plan_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_persist_request_status"],
            persist_request["persist_request_status"],
        )

    def test_project_runner_persist_gate_dry_run_endpoint_returns_audit_ledger(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/persist-gate/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["persist_gate_recorded"])
        self.assertFalse(payload["audit_ledger_recorded"])
        self.assertFalse(payload["explicit_approval_present"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["rollback_available"])
        self.assertFalse(payload["rollback_applied"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_persist_gate", payload)
        self.assertIn("runner_audit_ledger", payload)
        self.assertIn("runner_audit_ledger_summary", payload)

        persist_gate = payload["runner_persist_gate"]
        audit_ledger = payload["runner_audit_ledger"]
        summary = payload["runner_audit_ledger_summary"]
        self.assertEqual(persist_gate["persist_gate_version"], "agent_runner_persist_gate_v1")
        self.assertEqual(audit_ledger["audit_ledger_version"], "agent_runner_audit_ledger_v1")
        self.assertTrue(audit_ledger["dry_run"])
        self.assertFalse(audit_ledger["audit_ledger_recorded"])
        self.assertFalse(audit_ledger["write_authorized"])
        self.assertFalse(audit_ledger["state_persisted"])
        self.assertEqual(summary["summary_version"], "agent_runner_audit_ledger_summary_v1")
        self.assertEqual(summary["audit_ledger_status"], audit_ledger["audit_ledger_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_persist_gate_status"],
            persist_gate["persist_gate_status"],
        )

    def test_project_runner_approval_dry_run_endpoint_returns_policy_decision(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/approval/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["approval_recorded"])
        self.assertFalse(payload["approval_granted"])
        self.assertFalse(payload["policy_decision_recorded"])
        self.assertFalse(payload["policy_approved"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["agent_output_generated"])
        self.assertFalse(payload["agent_invoked"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_approval_request", payload)
        self.assertIn("runner_policy_decision", payload)
        self.assertIn("runner_policy_decision_summary", payload)

        approval = payload["runner_approval_request"]
        policy = payload["runner_policy_decision"]
        summary = payload["runner_policy_decision_summary"]
        self.assertEqual(approval["approval_request_version"], "agent_runner_approval_request_v1")
        self.assertEqual(policy["policy_decision_version"], "agent_runner_policy_decision_v1")
        self.assertTrue(policy["dry_run"])
        self.assertFalse(policy["policy_approved"])
        self.assertFalse(policy["write_authorized"])
        self.assertEqual(summary["summary_version"], "agent_runner_policy_decision_summary_v1")
        self.assertEqual(summary["policy_decision_status"], policy["policy_decision_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_approval_request_status"],
            approval["approval_request_status"],
        )

    def test_project_runner_authorization_dry_run_endpoint_returns_execution_manifest(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/authorization/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["authorization_recorded"])
        self.assertFalse(payload["authorization_granted"])
        self.assertFalse(payload["authorization_token_issued"])
        self.assertFalse(payload["manifest_recorded"])
        self.assertFalse(payload["execution_started"])
        self.assertFalse(payload["agent_execution_authorized"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertIn("runner_authorization_preview", payload)
        self.assertIn("runner_execution_manifest", payload)
        self.assertIn("runner_execution_manifest_summary", payload)

        authorization = payload["runner_authorization_preview"]
        manifest = payload["runner_execution_manifest"]
        summary = payload["runner_execution_manifest_summary"]
        self.assertEqual(authorization["authorization_preview_version"], "agent_runner_authorization_preview_v1")
        self.assertEqual(manifest["execution_manifest_version"], "agent_runner_execution_manifest_v1")
        self.assertTrue(manifest["dry_run"])
        self.assertFalse(manifest["execution_started"])
        self.assertFalse(manifest["agent_execution_performed"])
        self.assertEqual(summary["summary_version"], "agent_runner_execution_manifest_summary_v1")
        self.assertEqual(summary["execution_manifest_status"], manifest["execution_manifest_status"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_authorization_status"],
            authorization["authorization_status"],
        )

    def test_project_runner_runtime_readiness_dry_run_endpoint_returns_bootstrap_plan(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/runtime-readiness/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_authorization_preview",
            "runner_execution_manifest",
            "runner_execution_session",
            "runner_preflight_certificate",
            "runner_runtime_sandbox",
            "runner_worker_bootstrap_plan",
            "runner_worker_bootstrap_plan_summary",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["authorization_granted"])
        self.assertFalse(payload["authorization_token_issued"])
        self.assertFalse(payload["execution_started"])
        self.assertFalse(payload["session_started"])
        self.assertFalse(payload["preflight_clearance_granted"])
        self.assertFalse(payload["sandbox_active"])
        self.assertFalse(payload["worker_started"])
        self.assertFalse(payload["worker_loop_started"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_worker_bootstrap_plan"]["worker_bootstrap_plan_version"],
            "agent_runner_worker_bootstrap_plan_v1",
        )
        self.assertEqual(
            payload["runner_worker_bootstrap_plan_summary"]["summary_version"],
            "agent_runner_worker_bootstrap_plan_summary_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_worker_bootstrap_status"],
            payload["runner_worker_bootstrap_plan"]["worker_bootstrap_status"],
        )

    def test_project_runner_worker_loop_dry_run_endpoint_returns_recovery_summary(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/worker-loop/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_worker_poll",
            "runner_worker_heartbeat",
            "runner_worker_loop_simulation",
            "runner_failure_receipt",
            "runner_retry_plan",
            "runner_recovery_summary",
            "runner_recovery_summary_summary",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["queue_item_claimed"])
        self.assertFalse(payload["heartbeat_recorded"])
        self.assertFalse(payload["worker_alive"])
        self.assertFalse(payload["worker_started"])
        self.assertFalse(payload["worker_loop_started"])
        self.assertFalse(payload["loop_simulation_recorded"])
        self.assertFalse(payload["failure_detected"])
        self.assertFalse(payload["failure_recorded"])
        self.assertFalse(payload["retry_allowed"])
        self.assertFalse(payload["retry_scheduled"])
        self.assertFalse(payload["recovery_complete"])
        self.assertFalse(payload["safe_to_continue"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_recovery_summary_summary"]["summary_version"],
            "agent_runner_recovery_summary_summary_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_recovery_status"],
            payload["runner_recovery_summary"]["recovery_status"],
        )

    def test_project_runner_worker_checkpoint_dry_run_endpoint_returns_checkpoint_bundle(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/worker-checkpoint/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_output_buffer",
            "runner_artifact_manifest",
            "runner_result_validation_gate",
            "runner_resume_cursor",
            "runner_dead_letter_policy",
            "runner_worker_checkpoint_bundle",
            "runner_worker_checkpoint_bundle_summary",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["output_buffer_recorded"])
        self.assertFalse(payload["output_written"])
        self.assertFalse(payload["artifact_manifest_recorded"])
        self.assertFalse(payload["artifact_created"])
        self.assertFalse(payload["validation_passed"])
        self.assertFalse(payload["validation_recorded"])
        self.assertFalse(payload["result_accepted"])
        self.assertFalse(payload["resume_allowed"])
        self.assertFalse(payload["resume_cursor_recorded"])
        self.assertFalse(payload["dead_letter_required"])
        self.assertFalse(payload["dead_letter_recorded"])
        self.assertFalse(payload["checkpoint_recorded"])
        self.assertFalse(payload["safe_to_continue"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_worker_checkpoint_bundle_summary"]["summary_version"],
            "agent_runner_worker_checkpoint_bundle_summary_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_worker_checkpoint_bundle_status"],
            payload["runner_worker_checkpoint_bundle"]["worker_checkpoint_bundle_status"],
        )

    def test_project_runner_finalization_dry_run_endpoint_returns_completion_ledger(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/finalization/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_result_acceptance",
            "runner_project_merge_preview",
            "runner_downstream_handoff",
            "runner_human_review_packet",
            "runner_run_finalization",
            "runner_completion_ledger",
            "runner_completion_ledger_summary",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["result_accepted"])
        self.assertFalse(payload["acceptance_recorded"])
        self.assertFalse(payload["merge_applied"])
        self.assertFalse(payload["handoff_ready"])
        self.assertFalse(payload["next_agent_unlocked"])
        self.assertTrue(payload["human_review_required"])
        self.assertFalse(payload["approved_by_human"])
        self.assertFalse(payload["run_finalized"])
        self.assertFalse(payload["completion_ledger_recorded"])
        self.assertFalse(payload["safe_to_continue"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_completion_ledger_summary"]["summary_version"],
            "agent_runner_completion_ledger_summary_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_completion_ledger_status"],
            payload["runner_completion_ledger"]["completion_ledger_status"],
        )

    def test_project_runner_orchestration_readiness_dry_run_endpoint_returns_report(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/orchestration-readiness/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        for key in [
            "runner_capability_matrix",
            "runner_blocker_map",
            "runner_real_execution_checklist",
            "runner_safety_contract_snapshot",
            "runner_milestone_report",
        ]:
            self.assertIn(key, payload)

        self.assertGreaterEqual(len(payload["runner_capability_matrix"]), 8)
        self.assertGreaterEqual(len(payload["runner_blocker_map"]), 4)
        self.assertGreaterEqual(len(payload["runner_real_execution_checklist"]), 8)
        self.assertEqual(
            payload["runner_safety_contract_snapshot"]["snapshot_version"],
            "runner_safety_contract_snapshot_v1",
        )
        self.assertEqual(
            payload["runner_milestone_report"]["milestone_report_version"],
            "runner_orchestration_milestone_report_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_orchestration_readiness_status"],
            "orchestration_readiness_dry_run_complete",
        )

    def test_project_runner_operator_control_dry_run_endpoint_returns_release_decision(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/operator-control/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_operator_control_center",
            "runner_human_approval_capture_preview",
            "runner_execution_mode_switch_preview",
            "runner_provider_sandbox_preview",
            "runner_quota_policy_preview",
            "runner_release_decision_packet",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["operator_can_enable_real_execution"])
        self.assertTrue(payload["approval_required"])
        self.assertFalse(payload["approval_captured"])
        self.assertFalse(payload["approved_by_human"])
        self.assertFalse(payload["provider_calls_enabled"])
        self.assertFalse(payload["quota_policy_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertFalse(payload["write_authorized"])
        self.assertFalse(payload["state_persisted"])
        self.assertFalse(payload["project_snapshot_saved"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        self.assertEqual(
            payload["runner_operator_control_center"]["operator_control_center_version"],
            "runner_operator_control_center_v1",
        )
        self.assertEqual(
            payload["runner_release_decision_packet"]["release_decision_packet_version"],
            "runner_release_decision_packet_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_release_decision_status"],
            "release_blocked_pending_operator_approval",
        )

    def test_project_runner_operator_approval_dry_run_endpoint_returns_guarded_release(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/operator-approval/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_approval_request_preview",
            "runner_approval_audit_trail_preview",
            "runner_consent_checklist_preview",
            "runner_rollback_playbook_preview",
            "runner_guarded_release_preview",
        ]:
            self.assertIn(key, payload)

        self.assertTrue(payload["approval_required"])
        self.assertFalse(payload["approval_request_recorded"])
        self.assertFalse(payload["approval_captured"])
        self.assertFalse(payload["approved_by_human"])
        self.assertFalse(payload["audit_trail_recorded"])
        self.assertFalse(payload["all_required_consent_confirmed"])
        self.assertFalse(payload["rollback_ready"])
        self.assertFalse(payload["rollback_executed"])
        self.assertFalse(payload["guarded_release_allowed"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertTrue(payload["operator_final_confirmation_required"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_guarded_release_preview"]["guarded_release_preview_version"],
            "runner_guarded_release_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_guarded_release_status"],
            "guarded_release_blocked",
        )

    def test_project_runner_approval_decision_dry_run_endpoint_returns_locked_gate(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/approval-decision/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_operator_decision_input_preview",
            "runner_approval_decision_simulator",
            "runner_release_gate_state_preview",
            "runner_execution_unlock_preview",
            "runner_operator_decision_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["decision_captured"])
        self.assertFalse(payload["decision_recorded"])
        self.assertFalse(payload["approved_by_human"])
        self.assertFalse(payload["rejected_by_human"])
        self.assertFalse(payload["gate_open"])
        self.assertTrue(payload["gate_locked"])
        self.assertFalse(payload["unlock_allowed"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["receipt_recorded"])
        self.assertFalse(payload["decision_audit_recorded"])
        self.assertTrue(payload["operator_final_confirmation_required"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_release_gate_state_preview"]["release_gate_state_version"],
            "runner_release_gate_state_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_execution_unlock_status"],
            "execution_unlock_blocked",
        )

    def test_project_runner_execution_sandbox_dry_run_endpoint_returns_quota_and_secret_boundaries(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/execution-sandbox/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_execution_sandbox_contract",
            "runner_provider_boundary_preview",
            "runner_secret_boundary_preview",
            "runner_quota_ledger_preview",
            "runner_cost_simulation_preview",
            "runner_sandbox_incident_plan_preview",
            "runner_execution_sandbox_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["sandbox_enabled"])
        self.assertFalse(payload["provider_calls_enabled"])
        self.assertFalse(payload["secret_access_enabled"])
        self.assertFalse(payload["quota_enabled"])
        self.assertFalse(payload["cost_simulation_allowed"])
        self.assertFalse(payload["incident_plan_ready"])
        self.assertFalse(payload["sandbox_ready_for_real_execution"])
        self.assertFalse(payload["receipt_recorded"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertTrue(payload["manual_review_required"])
        self.assertEqual(
            payload["runner_execution_sandbox_contract"]["execution_sandbox_contract_version"],
            "runner_execution_sandbox_contract_v1",
        )
        self.assertEqual(
            payload["runner_execution_sandbox_receipt_preview"]["execution_sandbox_receipt_version"],
            "runner_execution_sandbox_receipt_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_sandbox_ready_for_real_execution"],
            False,
        )

    def test_project_runner_provider_adapter_dry_run_endpoint_returns_adapter_registry(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/provider-adapter/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_provider_adapter_registry_preview",
            "runner_provider_adapter_handshake_preview",
            "runner_invocation_envelope_preview",
            "runner_provider_policy_matrix_preview",
            "runner_adapter_invocation_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertFalse(payload["provider_calls_enabled"])
        self.assertFalse(payload["handshake_passed"])
        self.assertFalse(payload["quota_reserved"])
        self.assertFalse(payload["operator_approval_attached"])
        self.assertFalse(payload["invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["receipt_recorded"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertTrue(payload["manual_review_required"])
        self.assertEqual(
            payload["runner_provider_adapter_registry_preview"]["provider_adapter_registry_version"],
            "runner_provider_adapter_registry_preview_v1",
        )
        self.assertEqual(
            payload["runner_adapter_invocation_receipt_preview"]["adapter_invocation_receipt_version"],
            "runner_adapter_invocation_receipt_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_provider_invocation_allowed"],
            False,
        )

    def test_project_runner_provider_invocation_dry_run_endpoint_returns_normalized_result(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/provider-invocation/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_provider_invocation_router_preview",
            "runner_provider_invocation_stub_preview",
            "runner_normalized_provider_result_preview",
            "runner_provider_idempotency_key_preview",
            "runner_provider_result_handoff_preview",
            "runner_provider_invocation_audit_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertTrue(payload["route_selected"])
        self.assertFalse(payload["route_invocation_allowed"])
        self.assertTrue(payload["normalized"])
        self.assertFalse(payload["handoff_ready"])
        self.assertFalse(payload["real_handoff_performed"])
        self.assertFalse(payload["audit_receipt_recorded"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertEqual(
            payload["runner_provider_invocation_router_preview"]["provider_invocation_router_version"],
            "runner_provider_invocation_router_preview_v1",
        )
        self.assertEqual(
            payload["runner_normalized_provider_result_preview"]["normalized_provider_result_version"],
            "runner_normalized_provider_result_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_provider_call_performed"],
            False,
        )

    def test_project_runner_provider_failure_dry_run_endpoint_returns_retry_and_circuit_breaker(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/provider-failure/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_provider_failure_taxonomy_preview",
            "runner_provider_retry_policy_preview",
            "runner_provider_fallback_plan_preview",
            "runner_provider_circuit_breaker_preview",
            "runner_provider_failure_recovery_handoff_preview",
            "runner_provider_failure_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertTrue(payload["failure_detected"])
        self.assertFalse(payload["retry_allowed"])
        self.assertTrue(payload["fallback_selected"])
        self.assertFalse(payload["fallback_executed"])
        self.assertTrue(payload["circuit_open"])
        self.assertTrue(payload["provider_temporarily_blocked"])
        self.assertFalse(payload["next_provider_call_allowed"])
        self.assertTrue(payload["operator_review_required"])
        self.assertFalse(payload["failure_receipt_recorded"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_provider_failure_taxonomy_preview"]["provider_failure_taxonomy_version"],
            "runner_provider_failure_taxonomy_preview_v1",
        )
        self.assertEqual(
            payload["runner_provider_failure_receipt_preview"]["provider_failure_receipt_version"],
            "runner_provider_failure_receipt_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_provider_temporarily_blocked"],
            True,
        )

    def test_project_runner_provider_observability_dry_run_endpoint_returns_dashboard(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/provider-observability/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_provider_health_snapshot_preview",
            "runner_provider_metric_rollup_preview",
            "runner_provider_alert_policy_preview",
            "runner_provider_trace_summary_preview",
            "runner_provider_observability_dashboard_preview",
            "runner_provider_observability_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertTrue(payload["dashboard_ready"])
        self.assertTrue(payload["alerts_triggered"])
        self.assertTrue(payload["operator_review_required"])
        self.assertFalse(payload["observability_receipt_recorded"])
        self.assertFalse(payload["trace_persisted"])
        self.assertFalse(payload["external_notification_sent"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_provider_health_snapshot_preview"]["provider_health_snapshot_version"],
            "runner_provider_health_snapshot_preview_v1",
        )
        self.assertEqual(
            payload["runner_provider_observability_receipt_preview"]["provider_observability_receipt_version"],
            "runner_provider_observability_receipt_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_provider_observability_dashboard_ready"],
            True,
        )

    def test_project_runner_capability_binding_dry_run_endpoint_returns_tool_binding_matrix(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/capability-binding/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["dry_run"])
        for key in [
            "runner_agent_capability_catalog_preview",
            "runner_agent_tool_binding_matrix_preview",
            "runner_capability_policy_gate_preview",
            "runner_tool_invocation_contract_preview",
            "runner_capability_handoff_plan_preview",
            "runner_capability_binding_receipt_preview",
        ]:
            self.assertIn(key, payload)

        self.assertTrue(payload["least_privilege_required"])
        self.assertTrue(payload["all_bindings_least_privilege"])
        self.assertFalse(payload["all_required_policy_checks_passed"])
        self.assertFalse(payload["contract_complete"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["handoff_ready"])
        self.assertFalse(payload["real_handoff_performed"])
        self.assertFalse(payload["capability_binding_receipt_recorded"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["cost_incurred_by_crossgrowth"])
        self.assertEqual(
            payload["runner_agent_capability_catalog_preview"]["agent_capability_catalog_version"],
            "runner_agent_capability_catalog_preview_v1",
        )
        self.assertEqual(
            payload["runner_capability_binding_receipt_preview"]["capability_binding_receipt_version"],
            "runner_capability_binding_receipt_preview_v1",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_tool_invocation_allowed"],
            False,
        )

    def test_project_runner_capability_invocation_gate_dry_run_endpoint_returns_blocked_gate(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/capability-invocation-gate/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        gate = payload["runner_capability_invocation_gate_preview"]
        request = payload["runner_capability_invocation_request_preview"]
        decision = payload["runner_capability_invocation_decision_preview"]
        receipt = payload["runner_capability_invocation_gate_receipt_preview"]

        self.assertEqual(gate["capability_invocation_gate_status"], "capability_invocation_blocked")
        self.assertGreater(gate["blocking_check_count"], 0)
        self.assertEqual(request["capability_invocation_request_status"], "capability_invocation_request_blocked")
        self.assertIn("operator_approval_id", request["missing_authorization_refs"])
        self.assertEqual(decision["capability_invocation_decision_status"], "capability_invocation_blocked")
        self.assertEqual(decision["decision_type"], "block_real_invocation")
        self.assertEqual(receipt["capability_invocation_gate_receipt_status"], "capability_invocation_gate_receipt_preview_only")
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_capability_invocation_gate_status"],
            gate["capability_invocation_gate_status"],
        )

    def test_project_runner_capability_invocation_rehearsal_dry_run_endpoint_returns_safe_blocked_receipt(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/capability-invocation-rehearsal/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["runtime_rehearsal_allowed"])
        self.assertFalse(payload["adapter_invocation_attempted"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        rehearsal = payload["runner_capability_invocation_runtime_rehearsal_preview"]
        ledger = payload["runner_capability_invocation_attempt_ledger_preview"]
        receipt = payload["runner_capability_invocation_rehearsal_receipt_preview"]

        self.assertEqual(rehearsal["capability_invocation_runtime_rehearsal_status"], "runtime_rehearsal_blocked")
        self.assertGreater(rehearsal["blocking_step_count"], 0)
        self.assertEqual(ledger["capability_invocation_attempt_ledger_status"], "attempt_ledger_preview_recorded")
        self.assertEqual(ledger["attempt_status"], "blocked_before_invocation")
        self.assertEqual(receipt["capability_invocation_rehearsal_receipt_status"], "capability_invocation_rehearsal_blocked_safely")
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_capability_invocation_rehearsal_receipt_status"],
            receipt["capability_invocation_rehearsal_receipt_status"],
        )

    def test_project_runner_capability_invocation_runbook_dry_run_endpoint_returns_blocked_release_guard(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/capability-invocation-runbook/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_invocation_ready"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        runbook = payload["runner_capability_invocation_runbook_preview"]
        review = payload["runner_capability_invocation_operator_review_packet_preview"]
        guard = payload["runner_capability_invocation_release_guard_preview"]

        self.assertEqual(runbook["capability_invocation_runbook_status"], "capability_invocation_runbook_blocked")
        self.assertGreater(runbook["blocking_step_count"], 0)
        self.assertEqual(review["capability_invocation_operator_review_packet_status"], "operator_review_required")
        self.assertFalse(review["operator_approval_captured"])
        self.assertEqual(guard["capability_invocation_release_guard_status"], "release_guard_blocked")
        self.assertFalse(guard["release_allowed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_capability_invocation_release_guard_status"],
            guard["capability_invocation_release_guard_status"],
        )

    def test_project_runner_capability_invocation_release_packet_dry_run_endpoint_returns_final_blocked_receipt(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/capability-invocation-release-packet/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["real_invocation_ready"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        packet = payload["runner_capability_invocation_release_packet_preview"]
        risk = payload["runner_capability_invocation_risk_summary_preview"]
        signoff = payload["runner_capability_invocation_signoff_packet_preview"]
        receipt = payload["runner_capability_invocation_final_blocked_receipt_preview"]

        self.assertEqual(packet["capability_invocation_release_packet_status"], "release_packet_blocked")
        self.assertGreater(packet["blocking_release_check_count"], 0)
        self.assertEqual(risk["capability_invocation_risk_summary_status"], "risk_summary_requires_operator_review")
        self.assertEqual(signoff["capability_invocation_signoff_packet_status"], "signoff_missing")
        self.assertGreater(signoff["missing_signoff_field_count"], 0)
        self.assertEqual(receipt["capability_invocation_final_blocked_receipt_status"], "final_blocked_before_real_invocation")
        self.assertFalse(receipt["release_allowed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_capability_invocation_final_blocked_receipt_status"],
            receipt["capability_invocation_final_blocked_receipt_status"],
        )

    def test_project_runner_real_execution_mode_gate_dry_run_endpoint_stays_blocked(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-mode-gate/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        gate = payload["runner_real_execution_mode_gate_preview"]
        switch_plan = payload["runner_real_execution_switch_plan_preview"]
        safety_case = payload["runner_real_execution_safety_case_preview"]
        receipt = payload["runner_real_execution_mode_receipt_preview"]

        self.assertEqual(gate["real_execution_mode_gate_status"], "real_execution_mode_blocked")
        self.assertGreater(gate["blocking_mode_gate_check_count"], 0)
        self.assertEqual(switch_plan["real_execution_switch_plan_status"], "switch_plan_blocked_in_dry_run")
        self.assertEqual(safety_case["real_execution_safety_case_status"], "real_execution_safety_case_blocked_safely")
        self.assertEqual(receipt["real_execution_mode_receipt_status"], "real_execution_mode_blocked_safely")
        self.assertFalse(receipt["real_execution_enabled"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_mode_receipt_status"],
            receipt["real_execution_mode_receipt_status"],
        )

    def test_project_runner_real_execution_readiness_summary_dry_run_endpoint_returns_no_go_brief(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-readiness-summary/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["go_no_go_decision"], "no_go")
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        summary = payload["runner_real_execution_readiness_summary_preview"]
        actions = payload["runner_real_execution_operator_next_actions_preview"]
        brief = payload["runner_real_execution_executive_brief_preview"]

        self.assertEqual(summary["real_execution_readiness_summary_status"], "not_ready_for_real_execution")
        self.assertEqual(summary["go_no_go_decision"], "no_go")
        self.assertGreater(summary["blocking_readiness_check_count"], 0)
        self.assertEqual(actions["real_execution_operator_next_actions_status"], "operator_actions_required")
        self.assertEqual(brief["real_execution_executive_brief_status"], "real_execution_no_go_brief_ready")
        self.assertIn("No-go for real execution.", brief["brief_lines"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_go_no_go_decision"],
            "no_go",
        )

    def test_project_runner_real_execution_approval_request_dry_run_endpoint_records_draft_not_approval(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-approval-request/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["operator_approval_captured"])
        self.assertFalse(payload["approval_request_ready"])
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        draft = payload["runner_real_execution_approval_request_draft_preview"]
        schema = payload["runner_real_execution_approval_form_schema_preview"]
        queue = payload["runner_real_execution_approval_review_queue_preview"]
        receipt = payload["runner_real_execution_approval_request_receipt_preview"]

        self.assertEqual(draft["real_execution_approval_request_draft_status"], "approval_request_draft_blocked")
        self.assertGreater(draft["missing_approval_field_count"], 0)
        self.assertEqual(schema["real_execution_approval_form_schema_status"], "approval_form_schema_ready_for_review")
        self.assertEqual(queue["real_execution_approval_review_queue_status"], "approval_review_queue_waiting_for_operator")
        self.assertEqual(receipt["real_execution_approval_request_receipt_status"], "approval_request_draft_recorded_not_approved")
        self.assertFalse(receipt["operator_approval_captured"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_approval_request_receipt_status"],
            receipt["real_execution_approval_request_receipt_status"],
        )

    def test_project_runner_real_execution_approval_decision_dry_run_endpoint_denies_without_operator_approval(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-approval-decision/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["approval_decision"], "denied")
        self.assertFalse(payload["operator_approval_captured"])
        self.assertFalse(payload["approval_request_ready"])
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        decision = payload["runner_real_execution_approval_decision_preview"]
        ledger = payload["runner_real_execution_decision_ledger_preview"]
        receipt = payload["runner_real_execution_denied_receipt_preview"]

        self.assertEqual(decision["real_execution_approval_decision_status"], "approval_decision_denied_in_dry_run")
        self.assertEqual(decision["approval_decision"], "denied")
        self.assertGreater(decision["blocking_decision_check_count"], 0)
        self.assertEqual(ledger["real_execution_decision_ledger_status"], "decision_ledger_recorded")
        self.assertEqual(receipt["real_execution_denied_receipt_status"], "real_execution_denied_safely")
        self.assertFalse(receipt["real_execution_enabled"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_approval_decision"],
            "denied",
        )

    def test_project_runner_real_execution_launch_authorization_dry_run_endpoint_keeps_launch_locked(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-launch-authorization/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["launch_authorized"])
        self.assertFalse(payload["launch_allowed"])
        self.assertFalse(payload["operator_approval_captured"])
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        authorization = payload["runner_real_execution_launch_authorization_preview"]
        lock = payload["runner_real_execution_launch_lock_preview"]
        receipt = payload["runner_real_execution_launch_denial_receipt_preview"]

        self.assertEqual(authorization["real_execution_launch_authorization_status"], "launch_authorization_denied")
        self.assertGreater(authorization["blocking_authorization_check_count"], 0)
        self.assertEqual(lock["real_execution_launch_lock_status"], "launch_locked")
        self.assertGreater(lock["lock_count"], 0)
        self.assertEqual(receipt["real_execution_launch_denial_receipt_status"], "launch_denied_safely")
        self.assertFalse(receipt["launch_allowed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_launch_denial_receipt_status"],
            receipt["real_execution_launch_denial_receipt_status"],
        )

    def test_project_runner_real_execution_launch_monitor_dry_run_endpoint_records_tripwires_and_abort_plan(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-launch-monitor/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertTrue(payload["monitoring_started"])
        self.assertTrue(payload["abort_recommended"])
        self.assertFalse(payload["launch_authorized"])
        self.assertFalse(payload["launch_allowed"])
        self.assertFalse(payload["operator_approval_captured"])
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        monitor = payload["runner_real_execution_launch_monitor_preview"]

        self.assertEqual(monitor["real_execution_launch_monitor_status"], "launch_monitor_blocked_safely")
        self.assertEqual(monitor["launch_authorization_status"], "launch_authorization_denied")
        self.assertEqual(monitor["launch_lock_status"], "launch_locked")
        self.assertEqual(monitor["launch_denial_receipt_status"], "launch_denied_safely")
        self.assertGreater(monitor["blocking_tripwire_signal_count"], 0)
        self.assertIn("launch_authorization_denied", monitor["blocking_tripwire_signal_ids"])
        self.assertIn("launch_lock_active", monitor["blocking_tripwire_signal_ids"])
        self.assertEqual(monitor["failed_health_probe_count"], 0)
        self.assertEqual(monitor["health_probe_summary"], "dry_run_safe_but_launch_blocked")
        self.assertGreater(monitor["abort_plan_step_count"], 0)
        self.assertTrue(monitor["abort_recommended"])
        self.assertFalse(monitor["provider_call_performed"])
        self.assertFalse(monitor["external_api_called"])
        self.assertFalse(monitor["agent_execution_performed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_launch_monitor_status"],
            monitor["real_execution_launch_monitor_status"],
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_abort_recommended"],
            True,
        )

    def test_project_runner_real_execution_incident_response_dry_run_endpoint_opens_containment_plan(self):
        project = self._create_project()
        response = self.client.post(
            f"/api/v1/projects/{project['project_id']}/runner/real-execution-incident-response/dry-run"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertTrue(payload["incident_detected"])
        self.assertTrue(payload["incident_response_opened"])
        self.assertTrue(payload["abort_recommended"])
        self.assertEqual(payload["containment_plan_status"], "containment_ready")
        self.assertFalse(payload["recovery_ready"])
        self.assertFalse(payload["launch_authorized"])
        self.assertFalse(payload["launch_allowed"])
        self.assertFalse(payload["operator_approval_captured"])
        self.assertFalse(payload["real_execution_mode_allowed"])
        self.assertFalse(payload["real_execution_enabled"])
        self.assertFalse(payload["release_allowed"])
        self.assertFalse(payload["capability_invocation_allowed"])
        self.assertFalse(payload["tool_invocation_allowed"])
        self.assertFalse(payload["provider_call_performed"])
        self.assertFalse(payload["external_api_called"])
        self.assertFalse(payload["agent_execution_performed"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["safe_to_continue"])

        incident = payload["runner_real_execution_incident_response_preview"]
        receipt = incident["incident_receipt"]
        audit_summary = payload["runner_real_execution_safety_chain_audit_summary_preview"]
        safety_event = payload["runner_real_execution_safety_chain_event_preview"]
        event_ledger_summary = payload["runner_event_ledger_summary"]
        supervisor_decision = payload["runner_supervisor_event_ledger_decision_summary"]
        supervisor_routing_plan = payload["runner_supervisor_next_step_routing_plan"]
        supervisor_work_order = payload["runner_supervisor_next_step_work_order_preview"]
        queue_lease_worker_chain = payload["runner_queue_lease_worker_dry_run_chain"]

        self.assertEqual(incident["real_execution_incident_response_status"], "incident_response_opened_safely")
        self.assertEqual(incident["launch_monitor_status"], "launch_monitor_blocked_safely")
        self.assertEqual(incident["containment_plan_status"], "containment_ready")
        self.assertGreater(incident["containment_action_count"], 0)
        self.assertGreater(incident["recovery_check_count"], 0)
        self.assertTrue(incident["incident_detected"])
        self.assertEqual(incident["incident_severity"], "high")
        self.assertIn("launch_authorization_denied", incident["blocking_tripwire_signal_ids"])
        self.assertFalse(incident["recovery_ready"])
        self.assertEqual(receipt["incident_receipt_status"], "incident_response_recorded")
        self.assertFalse(receipt["real_execution_enabled"])
        self.assertFalse(receipt["provider_call_performed"])
        self.assertFalse(receipt["external_api_called"])
        self.assertFalse(receipt["agent_execution_performed"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_incident_response_status"],
            incident["real_execution_incident_response_status"],
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_containment_plan_status"],
            "containment_ready",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_incident_receipt_status"],
            "incident_response_recorded",
        )
        self.assertEqual(
            audit_summary["real_execution_safety_chain_audit_summary_status"],
            "safety_chain_recorded_safely",
        )
        self.assertEqual(audit_summary["chain_status"], "blocked_safely")
        self.assertEqual(audit_summary["launch_authorization_status"], "launch_authorization_denied")
        self.assertEqual(audit_summary["launch_monitor_status"], "launch_monitor_blocked_safely")
        self.assertEqual(audit_summary["incident_response_status"], "incident_response_opened_safely")
        self.assertTrue(audit_summary["abort_recommended"])
        self.assertTrue(audit_summary["incident_detected"])
        self.assertFalse(audit_summary["provider_call_performed"])
        self.assertFalse(audit_summary["external_api_called"])
        self.assertFalse(audit_summary["agent_execution_performed"])
        self.assertFalse(audit_summary["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_safety_chain_audit_summary_status"],
            "safety_chain_recorded_safely",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_safety_chain_status"],
            "blocked_safely",
        )
        self.assertEqual(
            safety_event["real_execution_safety_chain_event_version"],
            "runner_real_execution_safety_chain_event_preview_v1",
        )
        self.assertEqual(safety_event["event_type"], "runner_real_execution_safety_chain_dry_run")
        self.assertEqual(safety_event["event_status"], "safety_chain_blocked_safely")
        self.assertEqual(safety_event["source_agent_id"], "risk_approval_agent")
        self.assertEqual(safety_event["target_agent_id"], "supervisor_agent")
        self.assertEqual(safety_event["chain_status"], "blocked_safely")
        self.assertTrue(safety_event["abort_recommended"])
        self.assertTrue(safety_event["incident_detected"])
        self.assertFalse(safety_event["provider_call_performed"])
        self.assertFalse(safety_event["external_api_called"])
        self.assertFalse(safety_event["agent_execution_performed"])
        self.assertFalse(safety_event["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_safety_chain_event_status"],
            "safety_chain_blocked_safely",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_real_execution_safety_chain_event_type"],
            "runner_real_execution_safety_chain_dry_run",
        )
        self.assertEqual(
            event_ledger_summary["runner_event_ledger_summary_version"],
            "agent_runner_event_ledger_summary_v1",
        )
        self.assertEqual(
            event_ledger_summary["runner_event_ledger_summary_status"],
            "event_ledger_recorded_safely",
        )
        self.assertEqual(event_ledger_summary["event_count"], 2)
        self.assertEqual(event_ledger_summary["blocking_event_count"], 2)
        self.assertFalse(event_ledger_summary["provider_call_performed"])
        self.assertFalse(event_ledger_summary["external_api_called"])
        self.assertFalse(event_ledger_summary["agent_execution_performed"])
        self.assertFalse(event_ledger_summary["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_event_ledger_summary_status"],
            "event_ledger_recorded_safely",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_event_ledger_event_count"],
            2,
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_event_ledger_blocking_event_count"],
            2,
        )
        self.assertFalse(
            payload["project"]["graph_summary"]["latest_runner_event_ledger_safe_to_continue"]
        )
        self.assertEqual(
            supervisor_decision["supervisor_event_ledger_decision_summary_version"],
            "agent_runner_supervisor_event_ledger_decision_summary_v1",
        )
        self.assertEqual(
            supervisor_decision["supervisor_event_ledger_decision_status"],
            "supervisor_blocked_by_event_ledger",
        )
        self.assertEqual(
            supervisor_decision["recommended_next_action"],
            "inspect_blocking_events_before_next_dry_run",
        )
        self.assertFalse(supervisor_decision["supervisor_routing_allowed"])
        self.assertFalse(supervisor_decision["real_execution_allowed"])
        self.assertFalse(supervisor_decision["provider_call_allowed"])
        self.assertFalse(supervisor_decision["external_api_call_allowed"])
        self.assertFalse(supervisor_decision["agent_execution_allowed"])
        self.assertFalse(supervisor_decision["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_event_ledger_decision_status"],
            "supervisor_blocked_by_event_ledger",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_recommended_next_action"],
            "inspect_blocking_events_before_next_dry_run",
        )
        self.assertFalse(
            payload["project"]["graph_summary"]["latest_runner_supervisor_routing_allowed"]
        )
        self.assertEqual(
            supervisor_routing_plan["supervisor_next_step_routing_plan_version"],
            "agent_runner_supervisor_next_step_routing_plan_v1",
        )
        self.assertEqual(
            supervisor_routing_plan["supervisor_next_step_routing_plan_status"],
            "routing_plan_blocked_by_event_ledger",
        )
        self.assertEqual(supervisor_routing_plan["next_step_type"], "inspect_blocking_events")
        self.assertEqual(supervisor_routing_plan["target_agent_id"], "risk_approval_agent")
        self.assertFalse(supervisor_routing_plan["routing_allowed"])
        self.assertFalse(supervisor_routing_plan["real_execution_allowed"])
        self.assertFalse(supervisor_routing_plan["provider_call_allowed"])
        self.assertFalse(supervisor_routing_plan["external_api_call_allowed"])
        self.assertFalse(supervisor_routing_plan["agent_execution_allowed"])
        self.assertFalse(supervisor_routing_plan["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_routing_plan_status"],
            "routing_plan_blocked_by_event_ledger",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_type"],
            "inspect_blocking_events",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_target_agent_id"],
            "risk_approval_agent",
        )
        self.assertFalse(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_routing_allowed"]
        )
        self.assertEqual(
            supervisor_work_order["supervisor_next_step_work_order_preview_version"],
            "agent_runner_supervisor_next_step_work_order_preview_v1",
        )
        self.assertEqual(
            supervisor_work_order["supervisor_next_step_work_order_status"],
            "supervisor_work_order_blocked",
        )
        self.assertEqual(supervisor_work_order["next_step_type"], "inspect_blocking_events")
        self.assertEqual(supervisor_work_order["target_agent_id"], "risk_approval_agent")
        self.assertFalse(supervisor_work_order["work_order_allowed"])
        self.assertFalse(supervisor_work_order["routing_allowed"])
        self.assertFalse(supervisor_work_order["real_execution_allowed"])
        self.assertFalse(supervisor_work_order["provider_call_allowed"])
        self.assertFalse(supervisor_work_order["external_api_call_allowed"])
        self.assertFalse(supervisor_work_order["agent_execution_allowed"])
        self.assertFalse(supervisor_work_order["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_work_order_status"],
            "supervisor_work_order_blocked",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_work_order_target_agent_id"],
            "risk_approval_agent",
        )
        self.assertFalse(
            payload["project"]["graph_summary"]["latest_runner_supervisor_next_step_work_order_allowed"]
        )
        self.assertEqual(
            queue_lease_worker_chain["queue_lease_worker_dry_run_chain_version"],
            "agent_runner_queue_lease_worker_dry_run_chain_v1",
        )
        self.assertEqual(
            queue_lease_worker_chain["queue_lease_worker_dry_run_chain_status"],
            "queue_lease_worker_chain_blocked_safely",
        )
        self.assertEqual(
            queue_lease_worker_chain["queue_persistence_status"],
            "queue_persistence_blocked_by_work_order",
        )
        self.assertEqual(
            queue_lease_worker_chain["worker_lease_status"],
            "worker_lease_blocked_by_queue_preview",
        )
        self.assertEqual(
            queue_lease_worker_chain["worker_invocation_status"],
            "worker_invocation_blocked_by_lease_preview",
        )
        self.assertFalse(queue_lease_worker_chain["queue_persisted"])
        self.assertFalse(queue_lease_worker_chain["worker_lease_created"])
        self.assertFalse(queue_lease_worker_chain["worker_invocation_performed"])
        self.assertFalse(queue_lease_worker_chain["provider_call_performed"])
        self.assertFalse(queue_lease_worker_chain["external_api_called"])
        self.assertFalse(queue_lease_worker_chain["agent_execution_performed"])
        self.assertFalse(queue_lease_worker_chain["safe_to_continue"])
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_queue_lease_worker_chain_status"],
            "queue_lease_worker_chain_blocked_safely",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_queue_persistence_status"],
            "queue_persistence_blocked_by_work_order",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_worker_lease_status"],
            "worker_lease_blocked_by_queue_preview",
        )
        self.assertEqual(
            payload["project"]["graph_summary"]["latest_runner_worker_invocation_status"],
            "worker_invocation_blocked_by_lease_preview",
        )
        self.assertFalse(payload["project"]["graph_summary"]["latest_runner_queue_persisted"])
        self.assertFalse(payload["project"]["graph_summary"]["latest_runner_worker_lease_created"])
        self.assertFalse(payload["project"]["graph_summary"]["latest_runner_worker_invocation_performed"])
        self.assertFalse(payload["project"]["graph_summary"]["latest_runner_queue_lease_worker_safe_to_continue"])
