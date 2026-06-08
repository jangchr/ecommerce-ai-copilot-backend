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

