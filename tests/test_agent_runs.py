from copy import deepcopy
import os
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agent_runs import (
    append_graph_router_decision,
    apply_human_approval_decision,
    apply_evidence_safe_storyboard_rework,
    build_agent_message,
    build_controlled_provider_handoff_checklist,
    build_demo_ready_run_summary,
    build_experiment_comparison_decision_gate,
    build_graph_health_summary,
    build_graph_router_decision,
    build_graph_state_snapshot,
    build_human_approval_gate,
    build_lightweight_artifact_registry,
    build_lightweight_artifact_lineage,
    build_revised_external_video_handoff_from_keyframe_plan,
    build_revised_keyframe_plan_from_experiment_feedback,
    detect_storyboard_rework_need,
    trigger_experiment_rework_run,
)
from main import AGENT_RUN_STORE, app
from tests.test_pasted_reviews_endpoint import GENERATED_REVIEWS_BRIEF, VALID_REVIEWS_REQUEST


class AgentRunsEndpointTest(unittest.TestCase):
    def setUp(self):
        AGENT_RUN_STORE.clear()
        self.client = TestClient(app)

    def test_graph_router_risk_route_and_registry_are_deterministic_and_safe(self):
        decision = build_graph_router_decision(
            {
                "route_context_type": "risk_validation",
                "validation_status": "failed",
                "issue_type": "unsupported_storyboard_claim",
                "reason": "Unsupported claim requires storyboard rework.",
                "artifact_types": ["storyboard", "risk_notes"],
            }
        )
        container = append_graph_router_decision({}, decision)

        self.assertEqual(decision["router_version"], "graph_router_agent_v1")
        self.assertEqual(decision["source_agent_id"], "graph_router_agent")
        self.assertEqual(decision["selected_next_agent_id"], "storyboard_agent")
        self.assertEqual(decision["route_type"], "rework")
        self.assertTrue(decision["should_trigger_rework"])
        self.assertEqual(
            decision["selected_edge"],
            {
                "from_node_id": "risk_agent",
                "to_node_id": "storyboard_agent",
                "edge_type": "rework",
            },
        )
        self.assertFalse(decision["safety_boundaries"]["external_api_called"])
        self.assertFalse(decision["safety_boundaries"]["cost_incurred_by_crossgrowth"])
        self.assertFalse(decision["safety_boundaries"]["llm_autonomous_decision_enabled"])
        self.assertEqual(container["latest_graph_router_decision"], decision)
        self.assertTrue(container["graph_router_summary"]["has_rework_route"])
        self.assertFalse(container["graph_router_summary"]["is_linear_workflow"])

    def test_agent_message_protocol_and_graph_snapshot_preserve_safety_boundaries(self):
        decision = build_graph_router_decision(
            {
                "route_context_type": "experiment_feedback",
                "issue_type": "product_consistency",
                "reason": "Product identity needs stronger keyframes.",
            }
        )
        message = build_agent_message(
            "router_route",
            "graph_router_agent",
            "keyframe_agent",
            {"selected_edge": decision["selected_edge"], "reason": decision["reason"]},
            run_id="run_graph_os_1",
            job_id="job_graph_os_1",
            artifact_ids=["artifact_keyframe_1"],
        )
        run = {
            "run_id": "run_graph_os_1",
            "status": "completed",
            "graph_nodes": [{"node_id": "graph_router_agent", "status": "complete"}],
            "graph_router_decisions": [decision],
            "latest_graph_router_decision": decision,
            "agent_messages": [message],
            "events": [{"event_type": "graph_router_route_selected"}],
        }
        registry = build_lightweight_artifact_registry(
            generation_data={
                "project_source": {
                    "source_id": "source_demo_1",
                    "source_type": "pasted_reviews",
                    "source_confidence": 0.82,
                    "warnings": ["manual_review_classification_recommended"],
                },
                "source_quality_gate": {
                    "gate_version": "source_quality_gate_v1",
                    "source_id": "source_demo_1",
                    "status": "warning",
                    "allows_agent_run": True,
                },
                "source_evidence_artifact": {
                    "artifact_version": "source_evidence_artifact_v1",
                    "artifact_id": "source_artifact_demo_1",
                    "source_id": "source_demo_1",
                    "review_classifications": [
                        {
                            "text": "Hard to clean after one smoothie.",
                            "categories": ["pain_point"],
                        }
                    ],
                },
                "source_snapshot": {
                    "snapshot_version": "source_snapshot_v1",
                    "source_id": "source_demo_1",
                },
                "llm_evidence_packet": {"packet_version": "pasted_reviews_v1"},
                "video_generation_packet": {"packet_version": "video_generation_v1"},
                "external_video_tool_handoff": {"handoff_version": "external_video_tool_handoff_v1"},
                "product_asset_lock": {"lock_version": "product_asset_lock_v1"},
                "keyframe_plan": {"plan_version": "keyframe_plan_v1"},
            },
            run=run,
        )
        snapshot = build_graph_state_snapshot(
            run=run,
            events=run["events"],
            artifact_registry=registry,
        )
        health = build_graph_health_summary(run, None, registry, snapshot)

        self.assertEqual(message["message_version"], "agent_message_v1")
        self.assertEqual(message["source_agent_id"], "graph_router_agent")
        self.assertEqual(message["artifact_ids"], ["artifact_keyframe_1"])
        self.assertEqual(
            message["safety_boundaries"],
            {
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
                "llm_autonomous_decision_enabled": False,
            },
        )
        self.assertEqual(registry["registry_version"], "artifact_registry_v2")
        self.assertIn("artifact_registry_v1", registry["compatible_with"])
        self.assertEqual(registry["project_id"], "demo_project_default")
        artifact_types = {item["artifact_type"] for item in registry["artifacts"]}
        self.assertTrue(
            {
                "llm_evidence_packet",
                "project_source",
                "source_quality_gate",
                "source_evidence_artifact",
                "source_snapshot",
                "video_generation_packet",
                "external_video_tool_handoff",
                "product_asset_lock",
                "keyframe_plan",
            }.issubset(artifact_types)
        )
        self.assertFalse(registry["graph_evidence"]["is_linear_workflow"])
        self.assertFalse(registry["lineage_summary"]["is_linear_workflow"])
        self.assertTrue(registry["lineage_summary"]["has_source_artifacts"])
        self.assertTrue(registry["lineage_summary"]["has_source_quality_gate"])
        self.assertTrue(registry["lineage_summary"]["has_review_classifications"])
        self.assertEqual(snapshot["snapshot_version"], "graph_state_snapshot_v1")
        self.assertFalse(snapshot["is_linear_workflow"])
        self.assertTrue(snapshot["selected_edges"])
        self.assertEqual(snapshot["selected_edges"][0]["selected_by_agent_id"], "graph_router_agent")
        self.assertFalse(snapshot["safety_boundaries"]["external_api_called"])
        self.assertEqual(health["health_version"], "graph_health_v1")
        self.assertFalse(health["is_linear_workflow"])

    def test_graph_router_maps_feedback_comparison_gate_and_approval_routes(self):
        feedback_expectations = {
            "product_consistency": ("keyframe_agent", "asset_lock_agent"),
            "storyboard_following": ("prompt_handoff_agent", "keyframe_agent"),
            "ad_readiness": ("storyboard_agent", "strategy_agent"),
            "visual_quality": ("prompt_handoff_agent", ""),
            "cost_value": ("cost_agent", "route_selector_agent"),
        }
        for issue_type, expected_agents in feedback_expectations.items():
            with self.subTest(issue_type=issue_type):
                decision = build_graph_router_decision(
                    {
                        "route_context_type": "experiment_feedback",
                        "issue_type": issue_type,
                    }
                )
                self.assertEqual(decision["selected_next_agent_id"], expected_agents[0])
                self.assertEqual(decision["secondary_next_agent_id"], expected_agents[1])
                self.assertTrue(decision["should_trigger_rework"])

        comparison_expectations = {
            "improved": ("provider_job_agent", "decision_gate", False, True),
            "regressed": ("prompt_handoff_agent", "rework", True, False),
            "mixed": ("experiment_agent", "human_approval", False, True),
            "no_change": ("asset_lock_agent", "rework", True, False),
        }
        for status, expected in comparison_expectations.items():
            with self.subTest(comparison_status=status):
                decision = build_graph_router_decision(
                    {
                        "route_context_type": "second_experiment_comparison",
                        "comparison_status": status,
                    }
                )
                self.assertEqual(decision["selected_next_agent_id"], expected[0])
                self.assertEqual(decision["route_type"], expected[1])
                self.assertEqual(decision["should_trigger_rework"], expected[2])
                self.assertEqual(decision["should_request_human_approval"], expected[3])

        gate = build_graph_router_decision(
            {
                "route_context_type": "experiment_comparison_decision_gate",
                "gate_decision_type": "retry_rework",
            }
        )
        self.assertEqual(gate["selected_next_agent_id"], "prompt_handoff_agent")
        self.assertEqual(gate["secondary_next_agent_id"], "keyframe_agent")

        checklist = build_graph_router_decision(
            {"route_context_type": "controlled_provider_checklist"}
        )
        self.assertEqual(checklist["selected_next_agent_id"], "human_approval_agent")
        self.assertTrue(checklist["should_request_human_approval"])
        self.assertFalse(checklist["should_proceed_to_provider_test"])

    def test_experiment_comparison_decision_gate_maps_all_statuses_without_autonomous_calls(self):
        expected = {
            "improved": ("proceed_to_controlled_test", "controlled_provider_or_manual_handoff"),
            "regressed": ("retry_rework", "keyframe_or_prompt_rework"),
            "mixed": ("manual_review_required", "manual_review"),
            "no_change": ("stop_or_revise_reference", "stronger_reference_required"),
        }
        for status, (decision_type, route) in expected.items():
            with self.subTest(status=status):
                gate = build_experiment_comparison_decision_gate(
                    {
                        "status": status,
                        "primary_metric": "product_consistency_score",
                        "score_deltas": {
                            "product_consistency_score": 3 if status == "improved" else 0,
                            "overall_score": 2 if status == "improved" else 0,
                        },
                        "improved_dimensions": ["product_consistency_score"] if status == "improved" else [],
                        "regressed_dimensions": ["product_consistency_score"] if status == "regressed" else [],
                    }
                )
                self.assertEqual(gate["gate_version"], "experiment_comparison_decision_gate_v1")
                self.assertEqual(gate["decision_type"], decision_type)
                self.assertEqual(gate["recommended_route"], route)
                self.assertTrue(gate["requires_human_approval"])
                self.assertFalse(gate["safety_boundaries"]["external_api_called"])
                self.assertFalse(gate["safety_boundaries"]["cost_incurred_by_crossgrowth"])
                self.assertFalse(gate["safety_boundaries"]["llm_autonomous_decision_enabled"])

    def test_demo_summary_lineage_and_checklist_preserve_controlled_handoff_boundaries(self):
        baseline = {
            "experiment_id": "baseline_1",
            "product_consistency_score": 1,
            "overall_score": 2,
            "agent_feedback_decision": {
                "feedback_version": "experiment_feedback_loop_v1",
                "has_feedback": True,
                "source_agent_id": "experiment_agent",
                "target_agent_id": "keyframe_agent",
                "secondary_target_agent_id": "asset_lock_agent",
                "decision_type": "feedback_rework_requested",
                "issue_type": "product_consistency",
            },
        }
        second = {
            "experiment_id": "second_1",
            "product_consistency_score": 4,
            "overall_score": 4,
        }
        rework_run = {
            "run_id": "run_1",
            "result": {
                "revised_keyframe_plan": {
                    "plan_version": "revised_keyframe_plan_v1",
                    "target_agent_id": "keyframe_agent",
                },
                "revised_external_video_handoff": {
                    "handoff_version": "revised_external_video_handoff_v1",
                    "target_agent_id": "prompt_handoff_agent",
                },
            },
        }
        comparison = {
            "status": "improved",
            "primary_metric": "product_consistency_score",
            "baseline_experiment_id": "baseline_1",
            "second_experiment_id": "second_1",
            "linked_rework_run_id": "run_1",
            "score_deltas": {"product_consistency_score": 3, "overall_score": 2},
            "decision_type": "second_experiment_improved",
        }
        gate = build_experiment_comparison_decision_gate(comparison)
        append_graph_router_decision(
            second,
            build_graph_router_decision(
                {
                    "route_context_type": "experiment_comparison_decision_gate",
                    "gate_decision_type": gate["decision_type"],
                    "comparison_status": comparison["status"],
                    "score_deltas": comparison["score_deltas"],
                }
            ),
        )
        checklist = build_controlled_provider_handoff_checklist(
            {"job_id": "job_1"},
            gate,
            rework_run,
            comparison,
        )
        approval_router = build_graph_router_decision(
            {
                "route_context_type": "controlled_provider_checklist",
                "artifact_types": ["controlled_provider_handoff_checklist"],
            }
        )
        approval_gate = build_human_approval_gate(
            {"job_id": "job_1"},
            gate,
            checklist,
            approval_router,
        )
        lineage = build_lightweight_artifact_lineage(
            {"job_id": "job_1"},
            baseline,
            second,
            rework_run,
            comparison,
            gate,
            approval_gate,
        )
        summary = build_demo_ready_run_summary(
            {"job_id": "job_1"},
            baseline,
            second,
            rework_run,
            comparison,
            gate,
            lineage,
            checklist,
            approval_gate,
        )

        self.assertEqual(lineage["lineage_version"], "agent_artifact_lineage_v1")
        self.assertEqual(lineage["lineage_type"], "experiment_feedback_demo_lineage")
        artifact_types = [artifact["artifact_type"] for artifact in lineage["artifact_chain"]]
        self.assertIn("revised_keyframe_plan", artifact_types)
        self.assertIn("revised_external_video_handoff", artifact_types)
        self.assertIn("experiment_comparison_decision_gate", artifact_types)
        self.assertIn("graph_router_decision", artifact_types)
        self.assertIn("human_approval_gate", artifact_types)
        self.assertFalse(lineage["graph_evidence"]["is_linear_workflow"])
        self.assertTrue(lineage["graph_evidence"]["has_rework_run"])
        self.assertIn("provider_job_agent", lineage["agents_involved"])
        self.assertIn("graph_router_agent", lineage["agents_involved"])
        self.assertTrue(lineage["graph_evidence"]["has_graph_router_decision"])
        self.assertTrue(lineage["graph_evidence"]["has_centralized_route_decision"])
        self.assertTrue(lineage["graph_evidence"]["has_human_approval_gate"])
        self.assertEqual(checklist["checklist_version"], "controlled_provider_handoff_checklist_v1")
        self.assertEqual(len(checklist["preflight_checks"]), 5)
        self.assertTrue(all(check["required"] for check in checklist["preflight_checks"]))
        self.assertFalse(checklist["external_api_call_allowed"])
        self.assertFalse(checklist["cost_incurred_by_crossgrowth"])
        self.assertTrue(checklist["human_approval_required"])
        self.assertFalse(checklist["safety_boundaries"]["automatic_provider_submission_enabled"])
        self.assertEqual(summary["summary_version"], "multi_agent_demo_run_summary_v1")
        self.assertEqual(summary["score_improvement_summary"]["delta"], 3)
        self.assertFalse(summary["lineage"]["graph_evidence"]["is_linear_workflow"])
        self.assertFalse(summary["is_linear_workflow"])
        self.assertEqual(summary["graph_router_summary"]["router_version"], "graph_router_agent_v1")
        self.assertFalse(summary["safety_summary"]["llm_autonomous_decision_enabled"])
        self.assertEqual(summary["human_approval_gate"]["status"], "pending_approval")
        self.assertIn("approval is required", summary["next_action"].lower())

    def test_human_approval_gate_transitions_preserve_safety_boundaries(self):
        checklist = build_controlled_provider_handoff_checklist(
            {"job_id": "job_approval_1"},
            {"gate_version": "experiment_comparison_decision_gate_v1"},
        )
        router = build_graph_router_decision(
            {"route_context_type": "controlled_provider_checklist"}
        )
        approval_gate = build_human_approval_gate(
            {"job_id": "job_approval_1"},
            {"gate_version": "experiment_comparison_decision_gate_v1"},
            checklist,
            router,
        )

        self.assertEqual(approval_gate["approval_gate_version"], "human_approval_gate_v1")
        self.assertEqual(approval_gate["status"], "pending_approval")
        self.assertTrue(approval_gate["blocks_provider_submit"])
        self.assertEqual(len(approval_gate["approval_checklist"]), 5)

        approved = apply_human_approval_decision(
            approval_gate,
            {
                "decision": "approved",
                "reviewer": "manual_user",
                "notes": "Approved for one simulated clip.",
            },
        )
        self.assertEqual(approved["status"], "approved")
        self.assertFalse(approved["blocks_provider_submit"])
        self.assertTrue(approved["blocks_external_api_call"])
        self.assertFalse(approved["safety_boundaries"]["external_api_called"])
        self.assertFalse(approved["safety_boundaries"]["cost_incurred_by_crossgrowth"])
        self.assertFalse(approved["safety_boundaries"]["llm_autonomous_decision_enabled"])
        self.assertEqual(approved["decision_history"][0]["reviewer"], "manual_user")

        with self.assertRaises(ValueError):
            apply_human_approval_decision(approved, {"decision": "rejected"})

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
        self.assertEqual(created_run["project_id"], "demo_project_default")
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
        self.assertEqual(completed_run["artifact_registry"]["registry_version"], "artifact_registry_v2")
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

    def test_project_workspace_create_get_and_default_run_scope(self):
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"AGENT_GRAPH_STORAGE_PATH": temp_dir},
        ):
            created = self.client.post(
                "/api/v1/projects",
                json={
                    "project_name": "Portable Blender Launch",
                    "product_name": "Portable Mini Blender",
                    "product_category": "kitchen_appliance",
                    "source_type": "manual",
                },
            )
            self.assertEqual(created.status_code, 200, created.text)
            project = created.json()["project"]
            self.assertEqual(project["project_version"], "project_workspace_v1")
            self.assertTrue(project["project_id"])
            self.assertEqual(
                project["durability_note"],
                "File-backed demo storage; durability depends on deployment storage configuration.",
            )
            fetched = self.client.get(f"/api/v1/projects/{project['project_id']}")
            self.assertEqual(fetched.status_code, 200)
            self.assertEqual(fetched.json()["project"]["project_id"], project["project_id"])

            with patch(
                "main.generate_pasted_reviews_brief",
                new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
            ):
                run_response = self.client.post(
                    "/api/v1/agent-runs/from-reviews",
                    json=VALID_REVIEWS_REQUEST,
                )
            self.assertEqual(run_response.status_code, 200, run_response.text)
            self.assertEqual(
                run_response.json()["run"]["project_id"],
                "demo_project_default",
            )

            project_request = {
                **VALID_REVIEWS_REQUEST,
                "project_id": project["project_id"],
            }
            with patch(
                "main.generate_pasted_reviews_brief",
                new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
            ):
                scoped_run_response = self.client.post(
                    "/api/v1/agent-runs/from-reviews",
                    json=project_request,
                )
            self.assertEqual(
                scoped_run_response.status_code,
                200,
                scoped_run_response.text,
            )
            self.assertEqual(
                scoped_run_response.json()["run"]["project_id"],
                project["project_id"],
            )

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

    def test_experiment_feedback_rework_run_helper_preserves_graph_structures(self):
        decision = {
            "feedback_version": "experiment_feedback_loop_v1",
            "has_feedback": True,
            "source_agent_id": "experiment_agent",
            "target_agent_id": "prompt_handoff_agent",
            "secondary_target_agent_id": "keyframe_agent",
            "decision_type": "feedback_rework_requested",
            "severity": "medium",
            "issue_type": "storyboard_following",
            "reason": "External result did not follow storyboard enough.",
            "recommended_action": "Revise prompt handoff and keyframe constraints.",
            "score_snapshot": {"storyboard_following_score": 1},
            "loop_guard": {"max_feedback_loop_count": 1, "feedback_loop_count": 1},
        }

        run = trigger_experiment_rework_run("video_job_123", decision)

        self.assertEqual(run["input_type"], "experiment_feedback_rework")
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["source_video_job_id"], "video_job_123")
        self.assertIsNone(run["active_node_id"])
        self.assertEqual(run["result"]["target_agent_id"], "prompt_handoff_agent")
        self.assertEqual(run["trigger_feedback_decision"]["issue_type"], "storyboard_following")
        self.assertFalse(run["llm_autonomous_decision_enabled"])
        self.assertFalse(run["external_api_called"])
        self.assertFalse(run["cost_incurred_by_crossgrowth"])
        self.assertEqual(run["transition_decisions"][0]["decision_type"], "feedback_rework_requested")
        self.assertEqual(run["validation_results"][0]["rework_target"], "prompt_handoff_agent")
        self.assertEqual(run["rework_loops"][0]["target_agent_id"], "prompt_handoff_agent")
        self.assertIn("experiment_to_prompt_handoff_rework", run["active_edge_ids"])
        event_types = [event["event_type"] for event in run["events"]]
        self.assertIn("run_created", event_types)
        self.assertIn("graph_initialized", event_types)
        self.assertIn("transition_decision", event_types)
        self.assertIn("experiment_feedback_rework_requested", event_types)
        self.assertIn("rework_requested", event_types)
        self.assertIn("graph_router_decision_created", event_types)
        self.assertIn("graph_router_route_selected", event_types)
        self.assertIn("node_started", event_types)
        self.assertIn("node_completed", event_types)
        self.assertIn("graph_completed", event_types)
        self.assertIn("run_completed", event_types)

    def test_experiment_feedback_rework_run_creates_revised_keyframe_plan(self):
        decision = {
            "feedback_version": "experiment_feedback_loop_v1",
            "has_feedback": True,
            "source_agent_id": "experiment_agent",
            "target_agent_id": "keyframe_agent",
            "secondary_target_agent_id": "asset_lock_agent",
            "decision_type": "feedback_rework_requested",
            "severity": "high",
            "issue_type": "product_consistency",
            "reason": "Product drift or identity mismatch detected.",
            "recommended_action": "Route back to Keyframe Agent and Asset Lock Agent.",
            "score_snapshot": {"product_consistency_score": 1},
            "loop_guard": {"max_feedback_loop_count": 1, "feedback_loop_count": 1},
        }
        original_generation_data = {
            "external_video_tool_handoff": {
                "product_asset_lock": {
                    "lock_version": "product_asset_lock_v1",
                    "product_identity": "Portable Mini Blender",
                    "product_category": "kitchen_appliance",
                    "must_preserve": ["Keep Portable Mini Blender visible."],
                    "must_not_change": ["Do not turn it into a full-size countertop blender."],
                    "image_reference_rules": ["Use the supplied reference image."],
                    "human_review_required": True,
                },
                "keyframe_plan": {
                    "plan_version": "keyframe_plan_v1",
                    "scenes": [
                        {
                            "scene_id": 1,
                            "keyframe_goal": "Show the mini blender on a gym bag.",
                            "evidence_anchor": "Small enough for travel.",
                        }
                    ],
                },
            }
        }

        plan = build_revised_keyframe_plan_from_experiment_feedback(
            original_generation_data,
            decision,
            {"failure_reason": "Generated clip looked like a different blender."},
        )
        self.assertEqual(plan["plan_version"], "revised_keyframe_plan_v1")
        self.assertEqual(plan["target_agent_id"], "keyframe_agent")
        self.assertEqual(plan["secondary_target_agent_id"], "asset_lock_agent")
        self.assertTrue(plan["human_review_required"])
        self.assertEqual(plan["product_identity_lock"]["product_identity"], "Portable Mini Blender")

        run = trigger_experiment_rework_run(
            "video_job_123",
            decision,
            original_generation_data=original_generation_data,
            experiment={"failure_reason": "Generated clip looked like a different blender."},
        )

        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["input_type"], "experiment_feedback_rework")
        self.assertEqual(run["result"]["result_type"], "experiment_feedback_rework_result")
        self.assertIn("revised_keyframe_plan", run["result"])
        self.assertEqual(run["result"]["revised_keyframe_plan"]["plan_version"], "revised_keyframe_plan_v1")
        self.assertEqual(run["result"]["target_agent_id"], "keyframe_agent")
        self.assertEqual(run["result"]["secondary_target_agent_id"], "asset_lock_agent")
        self.assertTrue(run["result"]["revised_keyframe_plan"]["human_review_required"])
        self.assertFalse(run["result"]["external_api_called"])
        self.assertFalse(run["result"]["cost_incurred_by_crossgrowth"])
        self.assertTrue(run["rework_artifacts"]["revised_keyframe_plan"])
        self.assertTrue(run["graph_router_decisions"])
        self.assertTrue(
            any(
                decision["from_agent_id"] == "keyframe_agent"
                and decision["selected_next_agent_id"] == "prompt_handoff_agent"
                for decision in run["graph_router_decisions"]
            )
        )
        event_types = [event["event_type"] for event in run["events"]]
        self.assertIn("revised_keyframe_plan_created", event_types)
        self.assertIn("rework_artifact_created", event_types)
        self.assertIn("graph_router_route_selected", event_types)
        self.assertIn("graph_completed", event_types)
        self.assertIn("run_completed", event_types)

    def test_experiment_feedback_rework_run_creates_revised_external_video_handoff(self):
        decision = {
            "feedback_version": "experiment_feedback_loop_v1",
            "has_feedback": True,
            "source_agent_id": "experiment_agent",
            "target_agent_id": "keyframe_agent",
            "secondary_target_agent_id": "asset_lock_agent",
            "decision_type": "feedback_rework_requested",
            "severity": "high",
            "issue_type": "product_consistency",
            "reason": "Product drift or identity mismatch detected.",
            "recommended_action": "Route back to Keyframe Agent and Asset Lock Agent.",
            "score_snapshot": {"product_consistency_score": 1},
            "loop_guard": {"max_feedback_loop_count": 1, "feedback_loop_count": 1},
        }
        original_generation_data = {
            "external_video_tool_handoff": {
                "product_asset_lock": {
                    "lock_version": "product_asset_lock_v1",
                    "product_identity": "Portable Mini Blender",
                    "product_category": "kitchen_appliance",
                    "must_preserve": ["Keep Portable Mini Blender visible."],
                    "must_not_change": ["Do not turn it into a full-size countertop blender."],
                    "image_reference_rules": ["Use the supplied reference image."],
                    "human_review_required": True,
                },
                "keyframe_plan": {
                    "plan_version": "keyframe_plan_v1",
                    "scenes": [
                        {
                            "scene_id": 1,
                            "keyframe_goal": "Show the mini blender on a gym bag.",
                            "evidence_anchor": "Small enough for travel.",
                        }
                    ],
                },
            }
        }
        revised_plan = build_revised_keyframe_plan_from_experiment_feedback(
            original_generation_data,
            decision,
            {"failure_reason": "Generated clip looked like a different blender."},
        )
        handoff = build_revised_external_video_handoff_from_keyframe_plan(
            original_generation_data,
            revised_plan,
            decision,
            {"failure_reason": "Generated clip looked like a different blender."},
        )
        self.assertEqual(handoff["handoff_version"], "revised_external_video_handoff_v1")
        self.assertEqual(handoff["target_agent_id"], "prompt_handoff_agent")
        self.assertTrue(handoff["tool_prompts"]["gemini_video_prompt"])
        self.assertTrue(handoff["tool_prompts"]["doubao_video_prompt"])
        self.assertTrue(handoff["tool_prompts"]["image_to_video_prompt"])
        self.assertTrue(handoff["tool_prompts"]["short_motion_prompt"])
        self.assertTrue(handoff["negative_prompt"])
        self.assertTrue(handoff["copy_ready_generation_brief"])

        run = trigger_experiment_rework_run(
            "video_job_123",
            decision,
            original_generation_data=original_generation_data,
            experiment={"failure_reason": "Generated clip looked like a different blender."},
        )

        self.assertEqual(run["status"], "completed")
        self.assertIn("revised_keyframe_plan", run["result"])
        self.assertIn("revised_external_video_handoff", run["result"])
        self.assertEqual(
            run["result"]["revised_external_video_handoff"]["handoff_version"],
            "revised_external_video_handoff_v1",
        )
        self.assertEqual(run["result"]["revised_external_video_handoff"]["target_agent_id"], "prompt_handoff_agent")
        self.assertTrue(run["result"]["revised_external_video_handoff"]["tool_prompts"]["gemini_video_prompt"])
        self.assertTrue(run["result"]["revised_external_video_handoff"]["tool_prompts"]["doubao_video_prompt"])
        self.assertTrue(run["result"]["revised_external_video_handoff"]["tool_prompts"]["image_to_video_prompt"])
        self.assertTrue(run["result"]["revised_external_video_handoff"]["negative_prompt"])
        self.assertTrue(run["result"]["revised_external_video_handoff"]["copy_ready_generation_brief"])
        self.assertFalse(run["result"]["external_api_called"])
        self.assertFalse(run["result"]["cost_incurred_by_crossgrowth"])
        self.assertTrue(run["rework_artifacts"]["revised_external_video_handoff"])
        event_types = [event["event_type"] for event in run["events"]]
        self.assertIn("revised_external_video_handoff_created", event_types)
        self.assertIn("revised_prompt_handoff_created", event_types)

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
        self.assertTrue(completed_run["graph_router_decisions"])
        self.assertEqual(
            completed_run["latest_graph_router_decision"]["source_agent_id"],
            "graph_router_agent",
        )
        self.assertEqual(
            completed_run["latest_graph_router_decision"]["selected_next_agent_id"],
            "storyboard_agent",
        )
        self.assertEqual(completed_run["latest_graph_router_decision"]["route_type"], "rework")

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
        self.assertIn("graph_router_decision_created", event_types)
        self.assertIn("graph_router_route_selected", event_types)

    def test_invalid_run_id_returns_404(self):
        response = self.client.get("/api/v1/agent-runs/not-a-run")
        self.assertEqual(response.status_code, 404)

        events_response = self.client.get("/api/v1/agent-runs/not-a-run/events")
        self.assertEqual(events_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()


class AgentContractRegistryTests(unittest.TestCase):
    def test_agent_contract_registry_contains_core_agents(self):
        from agent_runs import build_agent_contract_registry, build_agent_contract_summary

        registry = build_agent_contract_registry()
        summary = build_agent_contract_summary(registry)
        self.assertEqual(registry["registry_version"], "agent_contract_registry_v1")
        self.assertEqual(registry["graph_version"], "agent_graph_runtime_v1")
        self.assertEqual(registry["execution_mode"], "rule_driven_agent_graph")
        self.assertEqual(registry["autonomy_level"], "rule_driven_v1")
        self.assertGreaterEqual(registry["contract_count"], 12)
        self.assertGreaterEqual(registry["edge_count"], registry["contract_count"])
        self.assertIn("source_adapter_agent", registry["contract_by_agent_id"])
        self.assertIn("planner_agent", registry["contract_by_agent_id"])
        self.assertIn("storyboard_agent", registry["contract_by_agent_id"])
        self.assertIn("risk_agent", registry["contract_by_agent_id"])
        self.assertIn("graph_router_agent", registry["contract_by_agent_id"])
        self.assertIn("finalizer_agent", registry["contract_by_agent_id"])
        self.assertEqual(summary["summary_version"], "agent_contract_summary_v1")
        self.assertGreaterEqual(summary["agent_count"], 12)
        self.assertFalse(summary["safety_boundaries"]["external_api_called"])
        self.assertFalse(summary["safety_boundaries"]["cost_incurred_by_crossgrowth"])
        self.assertFalse(summary["safety_boundaries"]["llm_autonomous_decision_enabled"])

    def test_agent_contract_handoff_validation_allows_known_edges(self):
        from agent_runs import validate_agent_contract_handoff

        validation = validate_agent_contract_handoff(
            "source_adapter_agent",
            "source_quality_agent",
            artifact_types=["project_source", "source_snapshot"],
        )
        self.assertTrue(validation["valid"], validation)
        self.assertEqual(validation["validation_version"], "agent_contract_handoff_validation_v1")
        self.assertEqual(validation["source_stage"], "source_intake")
        self.assertEqual(validation["target_stage"], "source_quality")
        self.assertEqual(validation["reasons"], [])
        self.assertFalse(validation["safety_boundaries"]["external_api_called"])

    def test_agent_contract_handoff_validation_blocks_unknown_or_disallowed_edges(self):
        from agent_runs import validate_agent_contract_handoff

        unknown = validate_agent_contract_handoff("missing_agent", "planner_agent")
        self.assertFalse(unknown["valid"])
        self.assertIn("Unknown source agent contract.", unknown["reasons"])

        disallowed = validate_agent_contract_handoff(
            "source_adapter_agent",
            "provider_job_agent",
            artifact_types=["provider_runtime"],
        )
        self.assertFalse(disallowed["valid"])
        self.assertIn("Target agent is not in source agent allowed_next_agent_ids.", disallowed["reasons"])
        self.assertTrue(disallowed["warnings"])

    def test_agent_contract_handoff_message_embeds_validation(self):
        from agent_runs import build_agent_contract_handoff_message

        message = build_agent_contract_handoff_message(
            source_agent_id="planner_agent",
            target_agent_id="asset_lock_agent",
            payload={"next_best_action": "Upload a product image."},
            run_id="run_contract_demo",
            job_id="job_contract_demo",
            artifact_ids=["artifact_contract_demo"],
            artifact_types=["supervisor_planner_recommendation"],
            project_id="project_contract_demo",
        )

        self.assertEqual(message["message_type"], "contract_handoff")
        self.assertEqual(message["contract_registry_version"], "agent_contract_registry_v1")
        self.assertTrue(message["handoff_valid"], message)
        self.assertEqual(message["contract_validation"]["source_agent_id"], "planner_agent")
        self.assertEqual(message["contract_validation"]["target_agent_id"], "asset_lock_agent")
        self.assertEqual(message["payload"]["contract_validation"]["valid"], True)
        self.assertEqual(message["project_id"], "project_contract_demo")
        self.assertFalse(message["safety_boundaries"]["external_api_called"])


class AgentRunnerPlanBuilderTests(unittest.TestCase):
    def test_agent_runner_plan_ready_for_agent_run(self):
        from agent_runs import (
            build_agent_runner_plan,
            build_agent_runner_plan_summary,
            build_supervisor_planner_recommendation,
        )

        recommendation = build_supervisor_planner_recommendation(
            project={"project_id": "project_runner_ready"},
            source={
                "project_id": "project_runner_ready",
                "source_type": "pasted_reviews",
                "source_summary": {"review_count": 3},
                "source_confidence": 0.9,
            },
            source_quality_gate={
                "project_id": "project_runner_ready",
                "status": "passed",
                "allows_agent_run": True,
            },
            source_evidence_artifact={
                "project_id": "project_runner_ready",
                "evidence_quotes": ["Review-backed evidence."],
                "source_confidence": 0.9,
            },
            artifact_registry={
                "project_id": "project_runner_ready",
                "registry_version": "artifact_registry_v2",
                "artifacts": [
                    {
                        "artifact_id": "asset_runner_ready",
                        "artifact_type": "uploaded_product_asset",
                    }
                ],
            },
        )
        self.assertEqual(recommendation["overall_status"], "ready_for_agent_run")

        plan = build_agent_runner_plan(
            recommendation,
            project={"project_id": "project_runner_ready"},
        )
        summary = build_agent_runner_plan_summary(plan)

        self.assertEqual(plan["runner_plan_version"], "agent_runner_plan_v1")
        self.assertEqual(plan["execution_status"], "ready")
        self.assertTrue(plan["can_execute_next_agent"], plan)
        self.assertFalse(plan["requires_user_action"])
        self.assertEqual(plan["next_agent_id"], "planner_agent")
        self.assertTrue(plan["handoff_message"]["handoff_valid"], plan["handoff_message"])
        self.assertEqual(plan["contract_validation"]["source_agent_id"], "planner_agent")
        self.assertEqual(plan["contract_validation"]["target_agent_id"], "planner_agent")
        self.assertEqual(plan["planned_steps"][-1]["step_id"], "execute_next_agent")
        self.assertEqual(summary["summary_version"], "agent_runner_plan_summary_v1")
        self.assertTrue(summary["can_execute_next_agent"])
        self.assertFalse(summary["safety_boundaries"]["external_api_called"])

    def test_agent_runner_plan_waits_for_user_when_source_missing(self):
        from agent_runs import build_agent_runner_plan, build_supervisor_planner_recommendation

        recommendation = build_supervisor_planner_recommendation(
            project={"project_id": "project_runner_needs_source"}
        )
        self.assertEqual(recommendation["overall_status"], "needs_source")
        self.assertEqual(recommendation["next_agent_id"], "source_adapter_agent")

        plan = build_agent_runner_plan(
            recommendation,
            project={"project_id": "project_runner_needs_source"},
        )

        self.assertEqual(plan["execution_status"], "waiting_for_user")
        self.assertFalse(plan["can_execute_next_agent"])
        self.assertTrue(plan["requires_user_action"])
        self.assertEqual(plan["planned_steps"][-1]["step_id"], "wait_for_user_input")
        self.assertEqual(plan["planned_steps"][-1]["status"], "waiting_for_user")
        self.assertTrue(plan["handoff_message"]["handoff_valid"], plan["handoff_message"])

    def test_agent_runner_plan_supports_source_quality_planner_route(self):
        from agent_runs import build_agent_runner_plan, build_supervisor_planner_recommendation

        recommendation = build_supervisor_planner_recommendation(
            project={"project_id": "project_runner_reviews"},
            source={
                "project_id": "project_runner_reviews",
                "source_type": "amazon_url",
                "source_summary": {"review_count": 0},
                "warnings": ["manual_reviews_recommended"],
            },
            source_quality_gate={
                "project_id": "project_runner_reviews",
                "status": "warning",
                "allows_agent_run": False,
                "warnings": ["manual_reviews_recommended"],
            },
        )
        self.assertEqual(recommendation["overall_status"], "needs_reviews")
        self.assertEqual(recommendation["next_agent_id"], "source_quality_agent")

        plan = build_agent_runner_plan(
            recommendation,
            project={"project_id": "project_runner_reviews"},
        )

        self.assertEqual(plan["execution_status"], "waiting_for_user")
        self.assertFalse(plan["can_execute_next_agent"])
        self.assertTrue(plan["handoff_message"]["handoff_valid"], plan["handoff_message"])
        self.assertEqual(plan["contract_validation"]["target_stage"], "source_quality")

    def test_agent_runner_plan_blocks_unknown_next_agent(self):
        from agent_runs import build_agent_runner_plan

        plan = build_agent_runner_plan(
            {
                "project_id": "project_runner_unknown",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )

        self.assertEqual(plan["execution_status"], "blocked")
        self.assertFalse(plan["can_execute_next_agent"])
        self.assertIn("Next agent contract was not found.", plan["blocked_reasons"])
        self.assertEqual(plan["planned_steps"][-1]["step_id"], "block_next_agent")
        self.assertFalse(plan["safety_boundaries"]["external_api_called"])


class AgentRunnerDispatchTicketTests(unittest.TestCase):
    def test_dispatch_ticket_ready_plan_allows_dry_run_dispatch(self):
        from agent_runs import (
            build_agent_runner_dispatch_summary,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_dispatch_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_dispatch_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan, requested_by="unit_test")
        summary = build_agent_runner_dispatch_summary(ticket)

        self.assertEqual(ticket["dispatch_ticket_version"], "agent_runner_dispatch_ticket_v1")
        self.assertEqual(ticket["dispatch_status"], "ready_to_dispatch")
        self.assertTrue(ticket["dispatch_allowed"], ticket)
        self.assertTrue(ticket["dry_run"])
        self.assertEqual(ticket["recommended_command"], "execute_next_agent_dry_run")
        self.assertEqual(ticket["next_agent_id"], "planner_agent")
        self.assertEqual(ticket["blocking_check_ids"], [])
        self.assertFalse(ticket["external_api_called"])
        self.assertFalse(ticket["cost_incurred_by_crossgrowth"])
        self.assertFalse(ticket["safety_boundaries"]["llm_autonomous_decision_enabled"])
        self.assertEqual(summary["summary_version"], "agent_runner_dispatch_summary_v1")
        self.assertTrue(summary["dispatch_allowed"])
        self.assertEqual(summary["blocking_check_count"], 0)

    def test_dispatch_ticket_waits_when_user_gate_required(self):
        from agent_runs import build_agent_runner_dispatch_ticket, build_agent_runner_plan

        plan = build_agent_runner_plan(
            {
                "project_id": "project_dispatch_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_dispatch_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)

        self.assertEqual(ticket["dispatch_status"], "waiting_for_user")
        self.assertFalse(ticket["dispatch_allowed"])
        self.assertIn("user_gate", ticket["blocking_check_ids"])
        self.assertIn("execution_status", ticket["blocking_check_ids"])
        self.assertEqual(ticket["recommended_command"], "collect_required_user_input")
        self.assertTrue(ticket["dry_run"])

    def test_dispatch_ticket_blocks_invalid_contract(self):
        from agent_runs import build_agent_runner_dispatch_ticket, build_agent_runner_plan

        plan = build_agent_runner_plan(
            {
                "project_id": "project_dispatch_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)

        self.assertEqual(ticket["dispatch_status"], "blocked")
        self.assertFalse(ticket["dispatch_allowed"])
        self.assertIn("contract_validation", ticket["blocking_check_ids"])
        self.assertIn("execution_status", ticket["blocking_check_ids"])
        self.assertEqual(ticket["recommended_command"], "fix_runner_plan_blockers")
        self.assertFalse(ticket["safety_boundaries"]["external_api_called"])


class AgentRunnerDispatchEventTests(unittest.TestCase):
    def test_dispatch_event_records_ready_ticket_without_execution(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_event_summary,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_dispatch_event_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_dispatch_event_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        summary = build_agent_runner_dispatch_event_summary(event)

        self.assertEqual(event["dispatch_event_version"], "agent_runner_dispatch_event_v1")
        self.assertEqual(event["event_type"], "runner_dispatch_dry_run")
        self.assertEqual(event["event_status"], "dispatch_ready")
        self.assertTrue(event["dispatch_allowed"], event)
        self.assertTrue(event["dry_run"])
        self.assertFalse(event["external_api_called"])
        self.assertFalse(event["cost_incurred_by_crossgrowth"])
        self.assertEqual(event["target_agent_id"], "planner_agent")
        self.assertEqual(event["dispatch_message"]["message_type"], "runner_dispatch_event")
        self.assertEqual(event["dispatch_message"]["target_agent_id"], "planner_agent")
        self.assertFalse(event["safety_boundaries"]["llm_autonomous_decision_enabled"])
        self.assertEqual(summary["summary_version"], "agent_runner_dispatch_event_summary_v1")
        self.assertEqual(summary["event_status"], "dispatch_ready")
        self.assertTrue(summary["dispatch_allowed"])

    def test_dispatch_event_records_waiting_ticket(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_dispatch_event_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_dispatch_event_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)

        self.assertEqual(event["event_status"], "dispatch_waiting_for_user")
        self.assertFalse(event["dispatch_allowed"])
        self.assertIn("user_gate", event["blocking_check_ids"])
        self.assertEqual(event["target_agent_id"], "source_adapter_agent")
        self.assertTrue(event["dry_run"])

    def test_dispatch_event_records_blocked_ticket(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_dispatch_event_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)

        self.assertEqual(event["event_status"], "dispatch_blocked")
        self.assertFalse(event["dispatch_allowed"])
        self.assertIn("contract_validation", event["blocking_check_ids"])
        self.assertEqual(event["target_agent_id"], "missing_agent")
        self.assertFalse(event["safety_boundaries"]["external_api_called"])


class AgentRunnerExecutionReceiptTests(unittest.TestCase):





    def test_queue_lease_worker_dry_run_chain_blocks_without_allowed_work_order(self):
        from agent_runs import build_agent_runner_queue_lease_worker_dry_run_chain

        work_order = {
            "project_id": "project_queue_lease_worker_chain",
            "supervisor_next_step_work_order_status": "supervisor_work_order_blocked",
            "work_order_id": "supervisor_next_step_work_order_project_queue_lease_worker_chain",
            "target_agent_id": "risk_approval_agent",
            "next_step_type": "inspect_blocking_events",
            "recommended_command": "/api/v1/projects/project_queue_lease_worker_chain/runner/real-execution-incident-response/dry-run",
            "work_order_allowed": False,
            "blocking_event_ids": ["event_one"],
            "dry_run": True,
        }
        chain = build_agent_runner_queue_lease_worker_dry_run_chain(
            work_order,
            project_id="project_queue_lease_worker_chain",
            requested_by="unit_test",
        )

        self.assertEqual(
            chain["queue_lease_worker_dry_run_chain_version"],
            "agent_runner_queue_lease_worker_dry_run_chain_v1",
        )
        self.assertEqual(chain["queue_lease_worker_dry_run_chain_status"], "queue_lease_worker_chain_blocked_safely")
        self.assertEqual(chain["queue_persistence_status"], "queue_persistence_blocked_by_work_order")
        self.assertEqual(chain["worker_lease_status"], "worker_lease_blocked_by_queue_preview")
        self.assertEqual(chain["worker_invocation_status"], "worker_invocation_blocked_by_lease_preview")
        self.assertFalse(chain["queue_persistence_allowed"])
        self.assertFalse(chain["worker_lease_allowed"])
        self.assertFalse(chain["worker_invocation_allowed"])
        self.assertFalse(chain["queue_persisted"])
        self.assertFalse(chain["worker_lease_created"])
        self.assertFalse(chain["worker_invocation_performed"])
        self.assertFalse(chain["provider_call_performed"])
        self.assertFalse(chain["external_api_called"])
        self.assertFalse(chain["agent_execution_performed"])
        self.assertFalse(chain["safe_to_continue"])
        self.assertTrue(chain["dry_run"])


    def test_supervisor_next_step_work_order_preview_blocks_on_blocking_route(self):
        from agent_runs import build_agent_runner_supervisor_next_step_work_order_preview

        routing_plan = {
            "project_id": "project_supervisor_next_step_work_order",
            "supervisor_next_step_routing_plan_version": "agent_runner_supervisor_next_step_routing_plan_v1",
            "supervisor_next_step_routing_plan_status": "routing_plan_blocked_by_event_ledger",
            "next_step_type": "inspect_blocking_events",
            "target_agent_id": "risk_approval_agent",
            "recommended_endpoint": "/api/v1/projects/{project_id}/runner/real-execution-incident-response/dry-run",
            "recommended_command": "/api/v1/projects/project_supervisor_next_step_work_order/runner/real-execution-incident-response/dry-run",
            "routing_allowed": False,
            "blocking_event_ids": ["event_one", "event_two"],
            "next_agent_candidates": ["risk_approval_agent"],
            "dry_run": True,
        }
        preview = build_agent_runner_supervisor_next_step_work_order_preview(
            routing_plan,
            project_id="project_supervisor_next_step_work_order",
            requested_by="unit_test",
        )

        self.assertEqual(
            preview["supervisor_next_step_work_order_preview_version"],
            "agent_runner_supervisor_next_step_work_order_preview_v1",
        )
        self.assertEqual(preview["supervisor_next_step_work_order_status"], "supervisor_work_order_blocked")
        self.assertIn("supervisor_next_step_work_order_project_supervisor_next_step_work_order", preview["work_order_id"])
        self.assertEqual(preview["next_step_type"], "inspect_blocking_events")
        self.assertEqual(preview["target_agent_id"], "risk_approval_agent")
        self.assertEqual(preview["blocking_event_count"], 2)
        self.assertFalse(preview["work_order_allowed"])
        self.assertFalse(preview["routing_allowed"])
        self.assertFalse(preview["real_execution_allowed"])
        self.assertFalse(preview["provider_call_allowed"])
        self.assertFalse(preview["external_api_call_allowed"])
        self.assertFalse(preview["agent_execution_allowed"])
        self.assertFalse(preview["provider_call_performed"])
        self.assertFalse(preview["external_api_called"])
        self.assertFalse(preview["agent_execution_performed"])
        self.assertFalse(preview["safe_to_continue"])
        self.assertTrue(preview["dry_run"])


    def test_supervisor_next_step_routing_plan_blocks_on_blocking_events(self):
        from agent_runs import build_agent_runner_supervisor_next_step_routing_plan

        decision = {
            "project_id": "project_supervisor_next_step_routing",
            "supervisor_event_ledger_decision_status": "supervisor_blocked_by_event_ledger",
            "recommended_next_action": "inspect_blocking_events_before_next_dry_run",
            "blocking_event_ids": ["event_one", "event_two"],
            "next_agent_candidates": ["risk_approval_agent"],
            "supervisor_routing_allowed": False,
            "safe_to_continue": False,
            "dry_run": True,
        }
        plan = build_agent_runner_supervisor_next_step_routing_plan(
            decision,
            project_id="project_supervisor_next_step_routing",
            requested_by="unit_test",
        )

        self.assertEqual(
            plan["supervisor_next_step_routing_plan_version"],
            "agent_runner_supervisor_next_step_routing_plan_v1",
        )
        self.assertEqual(plan["supervisor_next_step_routing_plan_status"], "routing_plan_blocked_by_event_ledger")
        self.assertEqual(plan["next_step_type"], "inspect_blocking_events")
        self.assertEqual(plan["target_agent_id"], "risk_approval_agent")
        self.assertEqual(plan["blocking_event_count"], 2)
        self.assertFalse(plan["routing_allowed"])
        self.assertFalse(plan["real_execution_allowed"])
        self.assertFalse(plan["provider_call_allowed"])
        self.assertFalse(plan["external_api_call_allowed"])
        self.assertFalse(plan["agent_execution_allowed"])
        self.assertFalse(plan["safe_to_continue"])
        self.assertTrue(plan["dry_run"])


    def test_supervisor_event_ledger_decision_blocks_on_blocking_events(self):
        from agent_runs import (
            build_agent_runner_event_ledger_summary,
            build_agent_runner_supervisor_event_ledger_decision_summary,
        )

        ledger = build_agent_runner_event_ledger_summary(
            project_id="project_supervisor_event_ledger_decision",
            safety_chain_event={
                "event_id": "safety_chain_event_project_supervisor_event_ledger_decision",
                "event_type": "runner_real_execution_safety_chain_dry_run",
                "event_status": "safety_chain_blocked_safely",
                "project_id": "project_supervisor_event_ledger_decision",
                "source_agent_id": "risk_approval_agent",
                "target_agent_id": "supervisor_agent",
                "abort_recommended": True,
                "incident_detected": True,
                "safe_to_continue": False,
                "provider_call_performed": False,
                "external_api_called": False,
                "agent_execution_performed": False,
                "dry_run": True,
            },
            requested_by="unit_test",
        )
        decision = build_agent_runner_supervisor_event_ledger_decision_summary(
            ledger,
            project_id="project_supervisor_event_ledger_decision",
            requested_by="unit_test",
        )

        self.assertEqual(
            decision["supervisor_event_ledger_decision_summary_version"],
            "agent_runner_supervisor_event_ledger_decision_summary_v1",
        )
        self.assertEqual(
            decision["supervisor_event_ledger_decision_status"],
            "supervisor_blocked_by_event_ledger",
        )
        self.assertEqual(decision["recommended_next_action"], "inspect_blocking_events_before_next_dry_run")
        self.assertFalse(decision["supervisor_routing_allowed"])
        self.assertFalse(decision["real_execution_allowed"])
        self.assertFalse(decision["provider_call_allowed"])
        self.assertFalse(decision["external_api_call_allowed"])
        self.assertFalse(decision["agent_execution_allowed"])
        self.assertFalse(decision["provider_call_performed"])
        self.assertFalse(decision["external_api_called"])
        self.assertFalse(decision["agent_execution_performed"])
        self.assertFalse(decision["safe_to_continue"])
        self.assertTrue(decision["dry_run"])


    def test_event_ledger_summary_normalizes_runner_events(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_event_ledger_summary,
            build_agent_runner_execution_receipt,
        )

        ticket = build_agent_runner_dispatch_ticket(
            {
                "project": {"project_id": "project_event_ledger_summary"},
                "next_agent_id": "strategy_agent",
                "next_action_type": "draft_strategy",
                "contract_validation": {"valid": False, "errors": ["missing_input"]},
            }
        )
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        summary = build_agent_runner_event_ledger_summary(
            project_id="project_event_ledger_summary",
            dispatch_event=event,
            execution_receipt=receipt,
            requested_by="unit_test",
        )

        self.assertEqual(summary["runner_event_ledger_summary_version"], "agent_runner_event_ledger_summary_v1")
        self.assertEqual(summary["runner_event_ledger_summary_status"], "event_ledger_recorded_safely")
        self.assertEqual(summary["project_id"], "project_event_ledger_summary")
        self.assertEqual(summary["event_count"], 2)
        self.assertGreaterEqual(summary["blocking_event_count"], 1)
        self.assertFalse(summary["safe_to_continue"])
        self.assertFalse(summary["provider_call_performed"])
        self.assertFalse(summary["external_api_called"])
        self.assertFalse(summary["agent_execution_performed"])
        self.assertTrue(summary["dry_run"])
        self.assertEqual(summary["normalized_events"][0]["event_type"], "runner_dispatch_dry_run")


    def test_execution_receipt_records_ready_dry_run_without_execution(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_execution_receipt_summary,
            build_agent_runner_event_ledger_summary,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_execution_receipt_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_execution_receipt_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        summary = build_agent_runner_execution_receipt_summary(receipt)

        self.assertEqual(receipt["execution_receipt_version"], "agent_runner_execution_receipt_v1")
        self.assertEqual(receipt["receipt_status"], "execution_ready_dry_run")
        self.assertTrue(receipt["execution_allowed"])
        self.assertFalse(receipt["execution_performed"])
        self.assertTrue(receipt["dry_run"])
        self.assertFalse(receipt["external_api_called"])
        self.assertFalse(receipt["cost_incurred_by_crossgrowth"])
        self.assertFalse(receipt["llm_autonomous_decision_enabled"])
        self.assertEqual(receipt["target_agent_id"], "planner_agent")
        self.assertEqual(receipt["execution_message_record"]["message_type"], "runner_execution_dry_run_receipt")
        self.assertEqual(summary["summary_version"], "agent_runner_execution_receipt_summary_v1")
        self.assertEqual(summary["receipt_status"], "execution_ready_dry_run")
        self.assertFalse(summary["execution_performed"])

    def test_execution_receipt_waits_for_user(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_execution_receipt_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_execution_receipt_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)

        self.assertEqual(receipt["receipt_status"], "execution_waiting_for_user")
        self.assertFalse(receipt["execution_allowed"])
        self.assertFalse(receipt["execution_performed"])
        self.assertIn("user_gate", receipt["blocking_check_ids"])
        self.assertEqual(receipt["recommended_next_state"], "collect_required_user_input")

    def test_execution_receipt_blocks_invalid_contract(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_execution_receipt_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)

        self.assertEqual(receipt["receipt_status"], "execution_blocked")
        self.assertFalse(receipt["execution_allowed"])
        self.assertFalse(receipt["execution_performed"])
        self.assertIn("contract_validation", receipt["blocking_check_ids"])
        self.assertEqual(receipt["recommended_next_state"], "fix_execution_blockers")


class AgentRunnerWorkOrderTests(unittest.TestCase):
    def test_work_order_records_ready_agent_package_without_execution(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_work_order,
            build_agent_runner_work_order_summary,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_work_order_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_work_order_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        summary = build_agent_runner_work_order_summary(order)

        self.assertEqual(order["work_order_version"], "agent_runner_work_order_v1")
        self.assertEqual(order["work_order_status"], "work_order_ready_dry_run")
        self.assertTrue(order["work_order_allowed"])
        self.assertTrue(order["dry_run"])
        self.assertFalse(order["agent_execution_performed"])
        self.assertFalse(order["external_api_called"])
        self.assertFalse(order["cost_incurred_by_crossgrowth"])
        self.assertFalse(order["llm_autonomous_decision_enabled"])
        self.assertEqual(order["target_agent_id"], "planner_agent")
        self.assertEqual(order["work_order_message"]["message_type"], "runner_work_order_dry_run")
        self.assertIn("project_state", order["required_inputs"])
        self.assertIn("supervisor_planner_recommendation", order["expected_outputs"])
        self.assertEqual(summary["summary_version"], "agent_runner_work_order_summary_v1")
        self.assertTrue(summary["work_order_allowed"])
        self.assertFalse(summary["agent_execution_performed"])

    def test_work_order_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_work_order_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_work_order_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)

        self.assertEqual(order["work_order_status"], "work_order_waiting_for_user")
        self.assertFalse(order["work_order_allowed"])
        self.assertIn("user_gate", order["blocking_check_ids"])
        self.assertEqual(order["target_agent_id"], "source_adapter_agent")
        self.assertFalse(order["agent_execution_performed"])

    def test_work_order_blocks_invalid_target_agent(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_work_order_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)

        self.assertEqual(order["work_order_status"], "work_order_blocked")
        self.assertFalse(order["work_order_allowed"])
        self.assertEqual(order["target_agent_id"], "missing_agent")
        self.assertIn("contract_validation", order["blocking_check_ids"])
        self.assertFalse(order["safety_boundaries"]["external_api_called"])


class AgentRunnerQueueItemTests(unittest.TestCase):
    def test_queue_item_records_ready_work_order_without_persistence(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_item,
            build_agent_runner_queue_item_summary,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_queue_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_queue_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        item = build_agent_runner_queue_item(order)
        summary = build_agent_runner_queue_item_summary(item)

        self.assertEqual(item["queue_item_version"], "agent_runner_queue_item_v1")
        self.assertEqual(item["queue_status"], "queue_ready_dry_run")
        self.assertTrue(item["enqueue_allowed"])
        self.assertTrue(item["dry_run"])
        self.assertFalse(item["queue_persisted"])
        self.assertFalse(item["agent_execution_performed"])
        self.assertFalse(item["external_api_called"])
        self.assertFalse(item["cost_incurred_by_crossgrowth"])
        self.assertFalse(item["llm_autonomous_decision_enabled"])
        self.assertEqual(item["target_agent_id"], "planner_agent")
        self.assertEqual(item["queue_message"]["message_type"], "runner_queue_item_dry_run")
        self.assertEqual(summary["summary_version"], "agent_runner_queue_item_summary_v1")
        self.assertTrue(summary["enqueue_allowed"])
        self.assertFalse(summary["queue_persisted"])

    def test_queue_item_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_item,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_queue_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_queue_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        item = build_agent_runner_queue_item(order)

        self.assertEqual(item["queue_status"], "queue_waiting_for_user")
        self.assertFalse(item["enqueue_allowed"])
        self.assertFalse(item["queue_persisted"])
        self.assertIn("user_gate", item["blocking_check_ids"])
        self.assertEqual(item["target_agent_id"], "source_adapter_agent")

    def test_queue_item_blocks_invalid_work_order(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_item,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_queue_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        item = build_agent_runner_queue_item(order)

        self.assertEqual(item["queue_status"], "queue_blocked")
        self.assertFalse(item["enqueue_allowed"])
        self.assertFalse(item["queue_persisted"])
        self.assertIn("contract_validation", item["blocking_check_ids"])
        self.assertEqual(item["target_agent_id"], "missing_agent")


class AgentRunnerQueueClaimTests(unittest.TestCase):
    def test_queue_claim_records_ready_queue_item_without_locking(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_claim_summary,
            build_agent_runner_queue_item,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_claim_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_claim_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item, worker_id="unit_worker")
        summary = build_agent_runner_queue_claim_summary(claim)

        self.assertEqual(claim["claim_version"], "agent_runner_queue_claim_v1")
        self.assertEqual(claim["claim_status"], "claim_ready_dry_run")
        self.assertTrue(claim["claim_allowed"])
        self.assertTrue(claim["dry_run"])
        self.assertFalse(claim["claim_persisted"])
        self.assertFalse(claim["lease_acquired"])
        self.assertFalse(claim["agent_execution_performed"])
        self.assertFalse(claim["external_api_called"])
        self.assertFalse(claim["cost_incurred_by_crossgrowth"])
        self.assertFalse(claim["llm_autonomous_decision_enabled"])
        self.assertEqual(claim["worker_id"], "unit_worker")
        self.assertEqual(claim["target_agent_id"], "planner_agent")
        self.assertEqual(claim["claim_message"]["message_type"], "runner_queue_claim_dry_run")
        self.assertEqual(summary["summary_version"], "agent_runner_queue_claim_summary_v1")
        self.assertTrue(summary["claim_allowed"])
        self.assertFalse(summary["lease_acquired"])

    def test_queue_claim_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_claim_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_claim_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)

        self.assertEqual(claim["claim_status"], "claim_waiting_for_user")
        self.assertFalse(claim["claim_allowed"])
        self.assertFalse(claim["lease_acquired"])
        self.assertIn("user_gate", claim["blocking_check_ids"])
        self.assertEqual(claim["target_agent_id"], "source_adapter_agent")

    def test_queue_claim_blocks_invalid_queue_item(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_claim_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)

        self.assertEqual(claim["claim_status"], "claim_blocked")
        self.assertFalse(claim["claim_allowed"])
        self.assertFalse(claim["lease_acquired"])
        self.assertIn("contract_validation", claim["blocking_check_ids"])
        self.assertEqual(claim["target_agent_id"], "missing_agent")


class AgentRunnerWorkerLeaseTests(unittest.TestCase):
    def test_worker_lease_records_ready_claim_without_locking(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_worker_lease_summary,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_lease_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_lease_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item, worker_id="unit_worker")
        lease = build_agent_runner_worker_lease(claim, lease_seconds=600)
        summary = build_agent_runner_worker_lease_summary(lease)

        self.assertEqual(lease["worker_lease_version"], "agent_runner_worker_lease_v1")
        self.assertEqual(lease["lease_status"], "lease_ready_dry_run")
        self.assertTrue(lease["lease_allowed"])
        self.assertTrue(lease["dry_run"])
        self.assertEqual(lease["lease_seconds"], 600)
        self.assertFalse(lease["lease_persisted"])
        self.assertFalse(lease["lease_acquired"])
        self.assertFalse(lease["agent_execution_performed"])
        self.assertFalse(lease["external_api_called"])
        self.assertFalse(lease["cost_incurred_by_crossgrowth"])
        self.assertFalse(lease["llm_autonomous_decision_enabled"])
        self.assertEqual(lease["worker_id"], "unit_worker")
        self.assertEqual(lease["target_agent_id"], "planner_agent")
        self.assertEqual(lease["lease_message"]["message_type"], "runner_worker_lease_dry_run")
        self.assertEqual(summary["summary_version"], "agent_runner_worker_lease_summary_v1")
        self.assertTrue(summary["lease_allowed"])
        self.assertFalse(summary["lease_acquired"])

    def test_worker_lease_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_lease_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_lease_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)

        self.assertEqual(lease["lease_status"], "lease_waiting_for_user")
        self.assertFalse(lease["lease_allowed"])
        self.assertFalse(lease["lease_acquired"])
        self.assertIn("user_gate", lease["blocking_check_ids"])
        self.assertEqual(lease["target_agent_id"], "source_adapter_agent")

    def test_worker_lease_blocks_invalid_claim(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_lease_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)

        self.assertEqual(lease["lease_status"], "lease_blocked")
        self.assertFalse(lease["lease_allowed"])
        self.assertFalse(lease["lease_acquired"])
        self.assertIn("contract_validation", lease["blocking_check_ids"])
        self.assertEqual(lease["target_agent_id"], "missing_agent")


class AgentRunnerInvocationDryRunTests(unittest.TestCase):
    def test_invocation_envelope_and_attempt_ready_without_agent_call(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_attempt_summary,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_envelope_summary,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_invocation_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_invocation_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item, worker_id="unit_worker")
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        envelope_summary = build_agent_runner_invocation_envelope_summary(envelope)
        attempt = build_agent_runner_invocation_attempt(envelope)
        attempt_summary = build_agent_runner_invocation_attempt_summary(attempt)

        self.assertEqual(envelope["invocation_envelope_version"], "agent_runner_invocation_envelope_v1")
        self.assertEqual(envelope["envelope_status"], "invocation_ready_dry_run")
        self.assertTrue(envelope["invocation_allowed"])
        self.assertFalse(envelope["agent_invoked"])
        self.assertFalse(envelope["agent_execution_performed"])
        self.assertFalse(envelope["external_api_called"])
        self.assertFalse(envelope["cost_incurred_by_crossgrowth"])
        self.assertFalse(envelope["llm_autonomous_decision_enabled"])
        self.assertEqual(envelope["target_agent_id"], "planner_agent")
        self.assertEqual(envelope["invocation_message"]["message_type"], "runner_invocation_envelope_dry_run")
        self.assertEqual(envelope_summary["summary_version"], "agent_runner_invocation_envelope_summary_v1")

        self.assertEqual(attempt["invocation_attempt_version"], "agent_runner_invocation_attempt_v1")
        self.assertEqual(attempt["attempt_status"], "attempt_ready_dry_run")
        self.assertTrue(attempt["attempt_allowed"])
        self.assertFalse(attempt["agent_invoked"])
        self.assertFalse(attempt["agent_execution_performed"])
        self.assertFalse(attempt["external_api_called"])
        self.assertFalse(attempt["cost_incurred_by_crossgrowth"])
        self.assertEqual(attempt["target_agent_id"], "planner_agent")
        self.assertEqual(attempt["attempt_message"]["message_type"], "runner_invocation_attempt_dry_run")
        self.assertEqual(attempt_summary["summary_version"], "agent_runner_invocation_attempt_summary_v1")

    def test_invocation_attempt_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_invocation_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_invocation_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)

        self.assertEqual(envelope["envelope_status"], "invocation_waiting_for_user")
        self.assertEqual(attempt["attempt_status"], "attempt_waiting_for_user")
        self.assertFalse(attempt["attempt_allowed"])
        self.assertFalse(attempt["agent_invoked"])
        self.assertIn("user_gate", attempt["blocking_check_ids"])

    def test_invocation_attempt_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_invocation_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)

        self.assertEqual(envelope["envelope_status"], "invocation_blocked")
        self.assertEqual(attempt["attempt_status"], "attempt_blocked")
        self.assertFalse(attempt["attempt_allowed"])
        self.assertFalse(attempt["agent_invoked"])
        self.assertIn("contract_validation", attempt["blocking_check_ids"])


class AgentRunnerInvocationResultCompletionTests(unittest.TestCase):
    def test_invocation_result_and_completion_receipt_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_completion_receipt_summary,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_invocation_result_summary,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_result_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_result_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        result_summary = build_agent_runner_invocation_result_summary(result)
        completion = build_agent_runner_completion_receipt(result)
        completion_summary = build_agent_runner_completion_receipt_summary(completion)

        self.assertEqual(result["invocation_result_version"], "agent_runner_invocation_result_v1")
        self.assertEqual(result["result_status"], "result_ready_dry_run")
        self.assertTrue(result["result_allowed"])
        self.assertFalse(result["agent_output_generated"])
        self.assertFalse(result["result_persisted"])
        self.assertFalse(result["agent_invoked"])
        self.assertFalse(result["agent_execution_performed"])
        self.assertFalse(result["external_api_called"])
        self.assertFalse(result["cost_incurred_by_crossgrowth"])
        self.assertFalse(result["output_contract_check"]["contract_satisfied"])
        self.assertEqual(result["result_message"]["message_type"], "runner_invocation_result_dry_run")
        self.assertEqual(result_summary["summary_version"], "agent_runner_invocation_result_summary_v1")

        self.assertEqual(completion["completion_receipt_version"], "agent_runner_completion_receipt_v1")
        self.assertEqual(completion["completion_status"], "completion_waiting_for_real_agent_output")
        self.assertFalse(completion["completion_allowed"])
        self.assertFalse(completion["handoff_complete"])
        self.assertFalse(completion["completion_recorded"])
        self.assertFalse(completion["agent_output_generated"])
        self.assertEqual(completion["completion_message"]["message_type"], "runner_completion_receipt_dry_run")
        self.assertEqual(completion_summary["summary_version"], "agent_runner_completion_receipt_summary_v1")

    def test_invocation_result_completion_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_result_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_result_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)

        self.assertEqual(result["result_status"], "result_waiting_for_user")
        self.assertEqual(completion["completion_status"], "completion_waiting_for_user")
        self.assertFalse(completion["completion_allowed"])
        self.assertIn("user_gate", result["blocking_check_ids"])

    def test_invocation_result_completion_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_result_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)

        self.assertEqual(result["result_status"], "result_blocked")
        self.assertEqual(completion["completion_status"], "completion_blocked")
        self.assertFalse(completion["handoff_complete"])
        self.assertIn("contract_validation", result["blocking_check_ids"])


class AgentRunnerHandoffCheckpointUnlockTests(unittest.TestCase):
    def test_checkpoint_and_unlock_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_handoff_checkpoint_summary,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_next_agent_unlock_summary,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_checkpoint_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project={"project_id": "project_checkpoint_ready"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(checkpoint)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        unlock_summary = build_agent_runner_next_agent_unlock_summary(unlock)

        self.assertEqual(checkpoint["handoff_checkpoint_version"], "agent_runner_handoff_checkpoint_v1")
        self.assertEqual(checkpoint["checkpoint_status"], "checkpoint_waiting_for_real_agent_output")
        self.assertFalse(checkpoint["handoff_complete"])
        self.assertFalse(checkpoint["next_agent_unlocked"])
        self.assertFalse(checkpoint["handoff_checkpoint_recorded"])
        self.assertFalse(checkpoint["agent_output_generated"])
        self.assertEqual(checkpoint["checkpoint_message"]["message_type"], "runner_handoff_checkpoint_dry_run")
        self.assertEqual(checkpoint_summary["summary_version"], "agent_runner_handoff_checkpoint_summary_v1")

        self.assertEqual(unlock["next_agent_unlock_version"], "agent_runner_next_agent_unlock_v1")
        self.assertEqual(unlock["unlock_status"], "unlock_waiting_for_real_agent_output")
        self.assertFalse(unlock["handoff_complete"])
        self.assertFalse(unlock["next_agent_unlocked"])
        self.assertFalse(unlock["unlock_recorded"])
        self.assertFalse(unlock["agent_execution_performed"])
        self.assertFalse(unlock["external_api_called"])
        self.assertFalse(unlock["cost_incurred_by_crossgrowth"])
        self.assertEqual(unlock["unlock_message"]["message_type"], "runner_next_agent_unlock_dry_run")
        self.assertEqual(unlock_summary["summary_version"], "agent_runner_next_agent_unlock_summary_v1")

    def test_checkpoint_unlock_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_checkpoint_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_checkpoint_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)

        self.assertEqual(checkpoint["checkpoint_status"], "checkpoint_waiting_for_user")
        self.assertEqual(unlock["unlock_status"], "unlock_waiting_for_user")
        self.assertFalse(unlock["next_agent_unlocked"])
        self.assertIn("user_gate", checkpoint["blocking_check_ids"])

    def test_checkpoint_unlock_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_checkpoint_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)

        self.assertEqual(checkpoint["checkpoint_status"], "checkpoint_blocked")
        self.assertEqual(unlock["unlock_status"], "unlock_blocked")
        self.assertFalse(unlock["next_agent_unlocked"])
        self.assertIn("contract_validation", checkpoint["blocking_check_ids"])


class AgentRunnerGraphTransitionProjectionTests(unittest.TestCase):
    def test_transition_projection_waits_for_real_output_without_persisting(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_graph_transition_proposal_summary,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_state_projection,
            build_agent_runner_state_projection_summary,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        project = {
            "project_id": "project_transition_ready",
            "graph_summary": {"existing_state": "kept"},
        }
        plan = build_agent_runner_plan(
            {
                "project_id": "project_transition_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project=project,
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        proposal_summary = build_agent_runner_graph_transition_proposal_summary(proposal)
        projection = build_agent_runner_state_projection(proposal, project=project)
        projection_summary = build_agent_runner_state_projection_summary(projection)

        self.assertEqual(proposal["graph_transition_proposal_version"], "agent_runner_graph_transition_proposal_v1")
        self.assertEqual(proposal["transition_status"], "transition_waiting_for_real_agent_output")
        self.assertEqual(proposal["proposed_graph_state"], "waiting_for_real_agent_output")
        self.assertFalse(proposal["next_agent_unlocked"])
        self.assertFalse(proposal["graph_transition_persisted"])
        self.assertFalse(proposal["agent_execution_performed"])
        self.assertEqual(proposal["transition_message"]["message_type"], "runner_graph_transition_proposal_dry_run")
        self.assertEqual(proposal_summary["summary_version"], "agent_runner_graph_transition_proposal_summary_v1")

        self.assertEqual(projection["state_projection_version"], "agent_runner_state_projection_v1")
        self.assertEqual(projection["projection_status"], "projection_waiting_for_real_agent_output")
        self.assertFalse(projection["state_persisted"])
        self.assertFalse(projection["project_snapshot_saved"])
        self.assertEqual(projection["current_graph_summary"]["existing_state"], "kept")
        self.assertEqual(projection["projected_graph_summary"]["projected_runner_graph_state"], "waiting_for_real_agent_output")
        self.assertEqual(projection["projection_message"]["message_type"], "runner_state_projection_dry_run")
        self.assertEqual(projection_summary["summary_version"], "agent_runner_state_projection_summary_v1")

    def test_transition_projection_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_state_projection,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_transition_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_transition_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)

        self.assertEqual(proposal["transition_status"], "transition_waiting_for_user")
        self.assertEqual(projection["projection_status"], "projection_waiting_for_user")
        self.assertFalse(projection["state_persisted"])
        self.assertIn("user_gate", proposal["blocking_check_ids"])

    def test_transition_projection_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_state_projection,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_transition_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)

        self.assertEqual(proposal["transition_status"], "transition_blocked")
        self.assertEqual(projection["projection_status"], "projection_blocked")
        self.assertFalse(projection["state_persisted"])
        self.assertIn("contract_validation", proposal["blocking_check_ids"])


class AgentRunnerTransitionCommitPlanGuardTests(unittest.TestCase):
    def test_commit_plan_and_mutation_guard_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_mutation_guard_summary,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_commit_plan_summary,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        project = {
            "project_id": "project_commit_plan_ready",
            "graph_summary": {"existing_state": "kept"},
        }
        plan = build_agent_runner_plan(
            {
                "project_id": "project_commit_plan_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project=project,
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal, project=project)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        commit_summary = build_agent_runner_transition_commit_plan_summary(commit_plan)
        guard = build_agent_runner_mutation_guard(commit_plan)
        guard_summary = build_agent_runner_mutation_guard_summary(guard)

        self.assertEqual(commit_plan["transition_commit_plan_version"], "agent_runner_transition_commit_plan_v1")
        self.assertEqual(commit_plan["commit_plan_status"], "commit_plan_waiting_for_real_agent_output")
        self.assertEqual(commit_plan["planned_mutation_count"], 4)
        self.assertFalse(commit_plan["commit_plan_persisted"])
        self.assertFalse(commit_plan["state_persisted"])
        self.assertFalse(commit_plan["project_snapshot_saved"])
        self.assertEqual(commit_plan["commit_message"]["message_type"], "runner_transition_commit_plan_dry_run")
        self.assertEqual(commit_summary["summary_version"], "agent_runner_transition_commit_plan_summary_v1")

        self.assertEqual(guard["mutation_guard_version"], "agent_runner_mutation_guard_v1")
        self.assertEqual(guard["mutation_guard_status"], "mutation_guard_waiting_for_real_agent_output")
        self.assertFalse(guard["mutation_allowed"])
        self.assertFalse(guard["mutation_guard_recorded"])
        self.assertFalse(guard["state_persisted"])
        self.assertFalse(guard["project_snapshot_saved"])
        self.assertEqual(guard["guard_message"]["message_type"], "runner_mutation_guard_dry_run")
        self.assertEqual(guard_summary["summary_version"], "agent_runner_mutation_guard_summary_v1")

    def test_commit_plan_guard_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_commit_plan_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_commit_plan_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)

        self.assertEqual(commit_plan["commit_plan_status"], "commit_plan_waiting_for_user")
        self.assertEqual(guard["mutation_guard_status"], "mutation_guard_waiting_for_user")
        self.assertFalse(guard["mutation_allowed"])

    def test_commit_plan_guard_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_commit_plan_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)

        self.assertEqual(commit_plan["commit_plan_status"], "commit_plan_blocked")
        self.assertEqual(guard["mutation_guard_status"], "mutation_guard_blocked")
        self.assertFalse(guard["mutation_allowed"])


class AgentRunnerTransitionPersistRequestRollbackTests(unittest.TestCase):
    def test_persist_request_and_rollback_plan_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_rollback_plan_summary,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_transition_persist_request_summary,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        project = {
            "project_id": "project_persist_request_ready",
            "graph_summary": {"existing_state": "kept"},
        }
        plan = build_agent_runner_plan(
            {
                "project_id": "project_persist_request_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project=project,
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal, project=project)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        persist_summary = build_agent_runner_transition_persist_request_summary(persist_request)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        rollback_summary = build_agent_runner_rollback_plan_summary(rollback_plan)

        self.assertEqual(persist_request["transition_persist_request_version"], "agent_runner_transition_persist_request_v1")
        self.assertEqual(persist_request["persist_request_status"], "persist_request_waiting_for_real_agent_output")
        self.assertFalse(persist_request["write_authorized"])
        self.assertFalse(persist_request["persist_request_recorded"])
        self.assertFalse(persist_request["state_persisted"])
        self.assertFalse(persist_request["project_snapshot_saved"])
        self.assertEqual(persist_request["planned_mutation_count"], 4)
        self.assertEqual(persist_request["persist_message"]["message_type"], "runner_transition_persist_request_dry_run")
        self.assertEqual(persist_summary["summary_version"], "agent_runner_transition_persist_request_summary_v1")

        self.assertEqual(rollback_plan["rollback_plan_version"], "agent_runner_rollback_plan_v1")
        self.assertEqual(rollback_plan["rollback_plan_status"], "rollback_plan_waiting_for_real_agent_output")
        self.assertFalse(rollback_plan["rollback_available"])
        self.assertFalse(rollback_plan["rollback_applied"])
        self.assertFalse(rollback_plan["rollback_plan_recorded"])
        self.assertEqual(rollback_plan["rollback_step_count"], 4)
        self.assertEqual(rollback_plan["rollback_message"]["message_type"], "runner_rollback_plan_dry_run")
        self.assertEqual(rollback_summary["summary_version"], "agent_runner_rollback_plan_summary_v1")

    def test_persist_request_rollback_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_persist_request_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_persist_request_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)

        self.assertEqual(persist_request["persist_request_status"], "persist_request_waiting_for_user")
        self.assertEqual(rollback_plan["rollback_plan_status"], "rollback_plan_waiting_for_user")
        self.assertFalse(persist_request["write_authorized"])
        self.assertFalse(rollback_plan["rollback_available"])

    def test_persist_request_rollback_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_persist_request_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)

        self.assertEqual(persist_request["persist_request_status"], "persist_request_blocked")
        self.assertEqual(rollback_plan["rollback_plan_status"], "rollback_plan_blocked")
        self.assertFalse(persist_request["write_authorized"])
        self.assertFalse(rollback_plan["rollback_available"])


class AgentRunnerPersistGateAuditLedgerTests(unittest.TestCase):
    def test_persist_gate_and_audit_ledger_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_audit_ledger,
            build_agent_runner_audit_ledger_summary,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_persist_gate_summary,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        project = {
            "project_id": "project_persist_gate_ready",
            "graph_summary": {"existing_state": "kept"},
        }
        plan = build_agent_runner_plan(
            {
                "project_id": "project_persist_gate_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project=project,
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal, project=project)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        gate_summary = build_agent_runner_persist_gate_summary(persist_gate)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        audit_summary = build_agent_runner_audit_ledger_summary(audit_ledger)

        self.assertEqual(persist_gate["persist_gate_version"], "agent_runner_persist_gate_v1")
        self.assertEqual(persist_gate["persist_gate_status"], "persist_gate_waiting_for_real_agent_output")
        self.assertFalse(persist_gate["explicit_approval_present"])
        self.assertFalse(persist_gate["write_authorized"])
        self.assertFalse(persist_gate["persist_gate_recorded"])
        self.assertFalse(persist_gate["state_persisted"])
        self.assertEqual(persist_gate["gate_message"]["message_type"], "runner_persist_gate_dry_run")
        self.assertEqual(gate_summary["summary_version"], "agent_runner_persist_gate_summary_v1")

        self.assertEqual(audit_ledger["audit_ledger_version"], "agent_runner_audit_ledger_v1")
        self.assertEqual(audit_ledger["audit_ledger_status"], "audit_ledger_waiting_for_real_agent_output")
        self.assertEqual(audit_ledger["audit_entry_count"], 3)
        self.assertFalse(audit_ledger["audit_ledger_recorded"])
        self.assertFalse(audit_ledger["write_authorized"])
        self.assertFalse(audit_ledger["state_persisted"])
        self.assertEqual(audit_ledger["audit_message"]["message_type"], "runner_audit_ledger_dry_run")
        self.assertEqual(audit_summary["summary_version"], "agent_runner_audit_ledger_summary_v1")

    def test_persist_gate_audit_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_audit_ledger,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_persist_gate_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_persist_gate_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)

        self.assertEqual(persist_gate["persist_gate_status"], "persist_gate_waiting_for_user")
        self.assertEqual(audit_ledger["audit_ledger_status"], "audit_ledger_waiting_for_user")
        self.assertFalse(persist_gate["write_authorized"])
        self.assertFalse(audit_ledger["audit_ledger_recorded"])

    def test_persist_gate_audit_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_audit_ledger,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_persist_gate_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)

        self.assertEqual(persist_gate["persist_gate_status"], "persist_gate_blocked")
        self.assertEqual(audit_ledger["audit_ledger_status"], "audit_ledger_blocked")
        self.assertFalse(persist_gate["write_authorized"])
        self.assertFalse(audit_ledger["audit_ledger_recorded"])


class AgentRunnerApprovalPolicyDecisionTests(unittest.TestCase):
    def test_approval_request_and_policy_decision_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_approval_request_summary,
            build_agent_runner_audit_ledger,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_policy_decision_summary,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        project = {
            "project_id": "project_approval_ready",
            "graph_summary": {"existing_state": "kept"},
        }
        plan = build_agent_runner_plan(
            {
                "project_id": "project_approval_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project=project,
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal, project=project)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        approval_summary = build_agent_runner_approval_request_summary(approval_request)
        policy_decision = build_agent_runner_policy_decision(approval_request)
        policy_summary = build_agent_runner_policy_decision_summary(policy_decision)

        self.assertEqual(approval_request["approval_request_version"], "agent_runner_approval_request_v1")
        self.assertEqual(approval_request["approval_request_status"], "approval_request_waiting_for_real_agent_output")
        self.assertFalse(approval_request["approval_granted"])
        self.assertFalse(approval_request["approval_recorded"])
        self.assertFalse(approval_request["write_authorized"])
        self.assertEqual(approval_request["required_approval_count"], 3)
        self.assertEqual(approval_request["approval_message"]["message_type"], "runner_approval_request_dry_run")
        self.assertEqual(approval_summary["summary_version"], "agent_runner_approval_request_summary_v1")

        self.assertEqual(policy_decision["policy_decision_version"], "agent_runner_policy_decision_v1")
        self.assertEqual(policy_decision["policy_decision_status"], "policy_decision_waiting_for_real_agent_output")
        self.assertFalse(policy_decision["policy_approved"])
        self.assertFalse(policy_decision["policy_decision_recorded"])
        self.assertFalse(policy_decision["write_authorized"])
        self.assertEqual(policy_decision["policy_check_count"], 4)
        self.assertEqual(policy_decision["decision_message"]["message_type"], "runner_policy_decision_dry_run")
        self.assertEqual(policy_summary["summary_version"], "agent_runner_policy_decision_summary_v1")

    def test_approval_policy_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_audit_ledger,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_approval_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_approval_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        policy_decision = build_agent_runner_policy_decision(approval_request)

        self.assertEqual(approval_request["approval_request_status"], "approval_request_waiting_for_user")
        self.assertEqual(policy_decision["policy_decision_status"], "policy_decision_waiting_for_user")
        self.assertFalse(approval_request["approval_granted"])
        self.assertFalse(policy_decision["policy_approved"])

    def test_approval_policy_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_audit_ledger,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_approval_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        policy_decision = build_agent_runner_policy_decision(approval_request)

        self.assertEqual(approval_request["approval_request_status"], "approval_request_blocked")
        self.assertEqual(policy_decision["policy_decision_status"], "policy_decision_blocked")
        self.assertFalse(approval_request["approval_granted"])
        self.assertFalse(policy_decision["policy_approved"])


class AgentRunnerAuthorizationManifestTests(unittest.TestCase):
    def test_authorization_preview_and_execution_manifest_wait_for_real_output(self):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_audit_ledger,
            build_agent_runner_authorization_preview,
            build_agent_runner_authorization_preview_summary,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_manifest,
            build_agent_runner_execution_manifest_summary,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        project = {"project_id": "project_authorization_ready", "graph_summary": {"existing_state": "kept"}}
        plan = build_agent_runner_plan(
            {
                "project_id": "project_authorization_ready",
                "overall_status": "ready_for_agent_run",
                "next_action_type": "start_agent_run",
                "next_agent_id": "planner_agent",
                "can_start_agent_run": True,
                "user_action_required": False,
            },
            project=project,
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal, project=project)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        policy_decision = build_agent_runner_policy_decision(approval_request)
        authorization_preview = build_agent_runner_authorization_preview(policy_decision)
        authorization_summary = build_agent_runner_authorization_preview_summary(authorization_preview)
        execution_manifest = build_agent_runner_execution_manifest(authorization_preview)
        manifest_summary = build_agent_runner_execution_manifest_summary(execution_manifest)

        self.assertEqual(authorization_preview["authorization_preview_version"], "agent_runner_authorization_preview_v1")
        self.assertEqual(authorization_preview["authorization_status"], "authorization_waiting_for_real_agent_output")
        self.assertFalse(authorization_preview["authorization_granted"])
        self.assertFalse(authorization_preview["authorization_token_issued"])
        self.assertFalse(authorization_preview["agent_execution_authorized"])
        self.assertEqual(authorization_preview["authorization_scope_count"], 4)
        self.assertEqual(authorization_preview["authorization_message"]["message_type"], "runner_authorization_preview_dry_run")
        self.assertEqual(authorization_summary["summary_version"], "agent_runner_authorization_preview_summary_v1")

        self.assertEqual(execution_manifest["execution_manifest_version"], "agent_runner_execution_manifest_v1")
        self.assertEqual(execution_manifest["execution_manifest_status"], "execution_manifest_waiting_for_real_agent_output")
        self.assertFalse(execution_manifest["execution_started"])
        self.assertFalse(execution_manifest["manifest_recorded"])
        self.assertFalse(execution_manifest["agent_execution_performed"])
        self.assertEqual(execution_manifest["manifest_item_count"], 4)
        self.assertEqual(execution_manifest["manifest_message"]["message_type"], "runner_execution_manifest_dry_run")
        self.assertEqual(manifest_summary["summary_version"], "agent_runner_execution_manifest_summary_v1")

    def test_authorization_manifest_waits_for_user_input(self):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_audit_ledger,
            build_agent_runner_authorization_preview,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_manifest,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_authorization_waiting",
                "overall_status": "needs_source",
                "next_action_type": "add_source",
                "next_agent_id": "source_adapter_agent",
                "user_action_required": True,
            },
            project={"project_id": "project_authorization_waiting"},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        policy_decision = build_agent_runner_policy_decision(approval_request)
        authorization_preview = build_agent_runner_authorization_preview(policy_decision)
        execution_manifest = build_agent_runner_execution_manifest(authorization_preview)

        self.assertEqual(authorization_preview["authorization_status"], "authorization_waiting_for_user")
        self.assertEqual(execution_manifest["execution_manifest_status"], "execution_manifest_waiting_for_user")
        self.assertFalse(authorization_preview["authorization_granted"])
        self.assertFalse(execution_manifest["execution_started"])

    def test_authorization_manifest_blocks_invalid_target(self):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_audit_ledger,
            build_agent_runner_authorization_preview,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_manifest,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )

        plan = build_agent_runner_plan(
            {
                "project_id": "project_authorization_blocked",
                "overall_status": "unknown",
                "next_action_type": "unknown_action",
                "next_agent_id": "missing_agent",
                "user_action_required": False,
            }
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal)
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        policy_decision = build_agent_runner_policy_decision(approval_request)
        authorization_preview = build_agent_runner_authorization_preview(policy_decision)
        execution_manifest = build_agent_runner_execution_manifest(authorization_preview)

        self.assertEqual(authorization_preview["authorization_status"], "authorization_blocked")
        self.assertEqual(execution_manifest["execution_manifest_status"], "execution_manifest_blocked")
        self.assertFalse(authorization_preview["authorization_granted"])
        self.assertFalse(execution_manifest["execution_started"])


class AgentRunnerRuntimeReadinessTests(unittest.TestCase):
    def _build_policy_decision(self, project_id="project_runtime_ready", user_action_required=False, next_agent_id="planner_agent"):
        from agent_runs import (
            build_agent_runner_approval_request,
            build_agent_runner_audit_ledger,
            build_agent_runner_completion_receipt,
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_graph_transition_proposal,
            build_agent_runner_handoff_checkpoint,
            build_agent_runner_invocation_attempt,
            build_agent_runner_invocation_envelope,
            build_agent_runner_invocation_result,
            build_agent_runner_mutation_guard,
            build_agent_runner_next_agent_unlock,
            build_agent_runner_persist_gate,
            build_agent_runner_plan,
            build_agent_runner_policy_decision,
            build_agent_runner_queue_claim,
            build_agent_runner_queue_item,
            build_agent_runner_rollback_plan,
            build_agent_runner_state_projection,
            build_agent_runner_transition_commit_plan,
            build_agent_runner_transition_persist_request,
            build_agent_runner_worker_lease,
            build_agent_runner_work_order,
        )
        plan = build_agent_runner_plan(
            {
                "project_id": project_id,
                "overall_status": "needs_source" if user_action_required else "ready_for_agent_run",
                "next_action_type": "add_source" if user_action_required else "start_agent_run",
                "next_agent_id": next_agent_id,
                "can_start_agent_run": not user_action_required,
                "user_action_required": user_action_required,
            },
            project={"project_id": project_id},
        )
        ticket = build_agent_runner_dispatch_ticket(plan)
        event = build_agent_runner_dispatch_event(ticket)
        receipt = build_agent_runner_execution_receipt(ticket, event)
        order = build_agent_runner_work_order(plan, ticket, event, receipt)
        queue_item = build_agent_runner_queue_item(order)
        claim = build_agent_runner_queue_claim(queue_item)
        lease = build_agent_runner_worker_lease(claim)
        envelope = build_agent_runner_invocation_envelope(lease)
        attempt = build_agent_runner_invocation_attempt(envelope)
        result = build_agent_runner_invocation_result(attempt)
        completion = build_agent_runner_completion_receipt(result)
        checkpoint = build_agent_runner_handoff_checkpoint(completion)
        unlock = build_agent_runner_next_agent_unlock(checkpoint)
        proposal = build_agent_runner_graph_transition_proposal(unlock)
        projection = build_agent_runner_state_projection(proposal, project={"project_id": project_id})
        commit_plan = build_agent_runner_transition_commit_plan(projection)
        guard = build_agent_runner_mutation_guard(commit_plan)
        persist_request = build_agent_runner_transition_persist_request(guard)
        rollback_plan = build_agent_runner_rollback_plan(persist_request)
        persist_gate = build_agent_runner_persist_gate(persist_request, rollback_plan)
        audit_ledger = build_agent_runner_audit_ledger(persist_gate)
        approval_request = build_agent_runner_approval_request(persist_gate, audit_ledger)
        return build_agent_runner_policy_decision(approval_request)

    def test_runtime_readiness_chain_waits_for_real_output(self):
        from agent_runs import (
            build_agent_runner_authorization_preview,
            build_agent_runner_execution_manifest,
            build_agent_runner_execution_session,
            build_agent_runner_preflight_certificate,
            build_agent_runner_runtime_sandbox,
            build_agent_runner_worker_bootstrap_plan,
            build_agent_runner_worker_bootstrap_plan_summary,
        )
        policy = self._build_policy_decision()
        authorization = build_agent_runner_authorization_preview(policy)
        manifest = build_agent_runner_execution_manifest(authorization)
        session = build_agent_runner_execution_session(manifest)
        preflight = build_agent_runner_preflight_certificate(session)
        sandbox = build_agent_runner_runtime_sandbox(preflight)
        bootstrap = build_agent_runner_worker_bootstrap_plan(sandbox)
        summary = build_agent_runner_worker_bootstrap_plan_summary(bootstrap)

        self.assertEqual(authorization["authorization_preview_version"], "agent_runner_authorization_preview_v1")
        self.assertEqual(manifest["execution_manifest_version"], "agent_runner_execution_manifest_v1")
        self.assertEqual(session["execution_session_version"], "agent_runner_execution_session_v1")
        self.assertEqual(preflight["preflight_certificate_version"], "agent_runner_preflight_certificate_v1")
        self.assertEqual(sandbox["runtime_sandbox_version"], "agent_runner_runtime_sandbox_v1")
        self.assertEqual(bootstrap["worker_bootstrap_plan_version"], "agent_runner_worker_bootstrap_plan_v1")
        self.assertFalse(authorization["authorization_granted"])
        self.assertFalse(manifest["execution_started"])
        self.assertFalse(session["session_started"])
        self.assertFalse(preflight["preflight_clearance_granted"])
        self.assertFalse(sandbox["sandbox_active"])
        self.assertFalse(bootstrap["worker_started"])
        self.assertFalse(bootstrap["worker_loop_started"])
        self.assertEqual(summary["summary_version"], "agent_runner_worker_bootstrap_plan_summary_v1")

    def test_runtime_readiness_chain_waits_for_user(self):
        from agent_runs import (
            build_agent_runner_authorization_preview,
            build_agent_runner_execution_manifest,
            build_agent_runner_execution_session,
            build_agent_runner_preflight_certificate,
            build_agent_runner_runtime_sandbox,
            build_agent_runner_worker_bootstrap_plan,
        )
        policy = self._build_policy_decision(project_id="project_runtime_waiting", user_action_required=True, next_agent_id="source_adapter_agent")
        authorization = build_agent_runner_authorization_preview(policy)
        manifest = build_agent_runner_execution_manifest(authorization)
        session = build_agent_runner_execution_session(manifest)
        preflight = build_agent_runner_preflight_certificate(session)
        sandbox = build_agent_runner_runtime_sandbox(preflight)
        bootstrap = build_agent_runner_worker_bootstrap_plan(sandbox)

        self.assertIn("waiting_for_user", authorization["authorization_status"])
        self.assertIn("waiting_for_user", manifest["execution_manifest_status"])
        self.assertIn("waiting_for_user", session["execution_session_status"])
        self.assertIn("waiting_for_user", preflight["preflight_status"])
        self.assertIn("waiting_for_user", sandbox["runtime_sandbox_status"])
        self.assertIn("waiting_for_user", bootstrap["worker_bootstrap_status"])


class AgentRunnerWorkerLoopRetryTests(unittest.TestCase):
    def test_worker_loop_retry_chain_stays_dry_run(self):
        from agent_runs import (
            build_agent_runner_failure_receipt,
            build_agent_runner_recovery_summary,
            build_agent_runner_recovery_summary_summary,
            build_agent_runner_retry_plan,
            build_agent_runner_worker_heartbeat,
            build_agent_runner_worker_loop_simulation,
            build_agent_runner_worker_poll,
        )

        bootstrap = {
            "project_id": "project_worker_loop_ready",
            "target_agent_id": "planner_agent",
            "target_agent_stage": "planning",
            "worker_bootstrap_plan_id": "worker_bootstrap_plan_project_worker_loop_ready",
            "worker_bootstrap_status": "worker_bootstrap_waiting_for_real_agent_output",
            "runtime_sandbox_id": "runtime_sandbox_project_worker_loop_ready",
            "dry_run": True,
        }
        poll = build_agent_runner_worker_poll(bootstrap)
        heartbeat = build_agent_runner_worker_heartbeat(poll)
        loop = build_agent_runner_worker_loop_simulation(heartbeat)
        failure = build_agent_runner_failure_receipt(loop)
        retry = build_agent_runner_retry_plan(failure)
        recovery = build_agent_runner_recovery_summary(retry)
        recovery_summary = build_agent_runner_recovery_summary_summary(recovery)

        self.assertEqual(poll["worker_poll_version"], "agent_runner_worker_poll_v1")
        self.assertEqual(heartbeat["worker_heartbeat_version"], "agent_runner_worker_heartbeat_v1")
        self.assertEqual(loop["worker_loop_simulation_version"], "agent_runner_worker_loop_simulation_v1")
        self.assertEqual(failure["failure_receipt_version"], "agent_runner_failure_receipt_v1")
        self.assertEqual(retry["retry_plan_version"], "agent_runner_retry_plan_v1")
        self.assertEqual(recovery["recovery_summary_version"], "agent_runner_recovery_summary_v1")
        self.assertFalse(poll["queue_item_claimed"])
        self.assertFalse(heartbeat["worker_alive"])
        self.assertFalse(loop["worker_loop_started"])
        self.assertFalse(loop["agent_execution_performed"])
        self.assertFalse(failure["failure_detected"])
        self.assertFalse(retry["retry_scheduled"])
        self.assertFalse(recovery["safe_to_continue"])
        self.assertTrue(recovery["manual_review_required"])
        self.assertEqual(recovery_summary["summary_version"], "agent_runner_recovery_summary_summary_v1")

    def test_worker_loop_retry_chain_waits_for_user(self):
        from agent_runs import (
            build_agent_runner_failure_receipt,
            build_agent_runner_recovery_summary,
            build_agent_runner_retry_plan,
            build_agent_runner_worker_heartbeat,
            build_agent_runner_worker_loop_simulation,
            build_agent_runner_worker_poll,
        )

        bootstrap = {
            "project_id": "project_worker_loop_waiting",
            "target_agent_id": "source_adapter_agent",
            "target_agent_stage": "source",
            "worker_bootstrap_plan_id": "worker_bootstrap_plan_project_worker_loop_waiting",
            "worker_bootstrap_status": "worker_bootstrap_waiting_for_user",
            "runtime_sandbox_id": "runtime_sandbox_project_worker_loop_waiting",
            "dry_run": True,
        }
        poll = build_agent_runner_worker_poll(bootstrap)
        heartbeat = build_agent_runner_worker_heartbeat(poll)
        loop = build_agent_runner_worker_loop_simulation(heartbeat)
        failure = build_agent_runner_failure_receipt(loop)
        retry = build_agent_runner_retry_plan(failure)
        recovery = build_agent_runner_recovery_summary(retry)

        self.assertIn("waiting_for_user", poll["worker_poll_status"])
        self.assertIn("waiting_for_user", heartbeat["worker_heartbeat_status"])
        self.assertIn("waiting_for_user", loop["worker_loop_status"])
        self.assertIn("waiting_for_user", failure["failure_receipt_status"])
        self.assertIn("waiting_for_user", retry["retry_plan_status"])
        self.assertIn("waiting_for_user", recovery["recovery_status"])
        self.assertFalse(recovery["recovery_complete"])


class AgentRunnerWorkerOutputCheckpointTests(unittest.TestCase):
    def test_worker_output_checkpoint_chain_stays_dry_run(self):
        from agent_runs import (
            build_agent_runner_artifact_manifest,
            build_agent_runner_dead_letter_policy,
            build_agent_runner_output_buffer,
            build_agent_runner_result_validation_gate,
            build_agent_runner_resume_cursor,
            build_agent_runner_worker_checkpoint_bundle,
            build_agent_runner_worker_checkpoint_bundle_summary,
        )

        recovery = {
            "project_id": "project_worker_checkpoint_ready",
            "target_agent_id": "planner_agent",
            "target_agent_stage": "planning",
            "recovery_summary_id": "recovery_summary_project_worker_checkpoint_ready",
            "recovery_status": "recovery_waiting_for_real_agent_output",
            "dry_run": True,
        }
        output_buffer = build_agent_runner_output_buffer(recovery)
        artifact_manifest = build_agent_runner_artifact_manifest(output_buffer)
        validation_gate = build_agent_runner_result_validation_gate(artifact_manifest)
        resume_cursor = build_agent_runner_resume_cursor(validation_gate)
        dead_letter_policy = build_agent_runner_dead_letter_policy(resume_cursor)
        checkpoint_bundle = build_agent_runner_worker_checkpoint_bundle(dead_letter_policy)
        checkpoint_summary = build_agent_runner_worker_checkpoint_bundle_summary(checkpoint_bundle)

        self.assertEqual(output_buffer["output_buffer_version"], "agent_runner_output_buffer_v1")
        self.assertEqual(artifact_manifest["artifact_manifest_version"], "agent_runner_artifact_manifest_v1")
        self.assertEqual(validation_gate["result_validation_gate_version"], "agent_runner_result_validation_gate_v1")
        self.assertEqual(resume_cursor["resume_cursor_version"], "agent_runner_resume_cursor_v1")
        self.assertEqual(dead_letter_policy["dead_letter_policy_version"], "agent_runner_dead_letter_policy_v1")
        self.assertEqual(checkpoint_bundle["worker_checkpoint_bundle_version"], "agent_runner_worker_checkpoint_bundle_v1")
        self.assertFalse(output_buffer["output_written"])
        self.assertFalse(artifact_manifest["artifact_created"])
        self.assertFalse(validation_gate["validation_passed"])
        self.assertFalse(validation_gate["result_accepted"])
        self.assertFalse(resume_cursor["resume_allowed"])
        self.assertFalse(dead_letter_policy["dead_letter_required"])
        self.assertFalse(checkpoint_bundle["checkpoint_recorded"])
        self.assertFalse(checkpoint_bundle["safe_to_continue"])
        self.assertTrue(checkpoint_bundle["manual_review_required"])
        self.assertEqual(checkpoint_summary["summary_version"], "agent_runner_worker_checkpoint_bundle_summary_v1")

    def test_worker_output_checkpoint_chain_waits_for_user(self):
        from agent_runs import (
            build_agent_runner_artifact_manifest,
            build_agent_runner_dead_letter_policy,
            build_agent_runner_output_buffer,
            build_agent_runner_result_validation_gate,
            build_agent_runner_resume_cursor,
            build_agent_runner_worker_checkpoint_bundle,
        )

        recovery = {
            "project_id": "project_worker_checkpoint_waiting",
            "target_agent_id": "source_adapter_agent",
            "target_agent_stage": "source",
            "recovery_summary_id": "recovery_summary_project_worker_checkpoint_waiting",
            "recovery_status": "recovery_waiting_for_user",
            "dry_run": True,
        }
        output_buffer = build_agent_runner_output_buffer(recovery)
        artifact_manifest = build_agent_runner_artifact_manifest(output_buffer)
        validation_gate = build_agent_runner_result_validation_gate(artifact_manifest)
        resume_cursor = build_agent_runner_resume_cursor(validation_gate)
        dead_letter_policy = build_agent_runner_dead_letter_policy(resume_cursor)
        checkpoint_bundle = build_agent_runner_worker_checkpoint_bundle(dead_letter_policy)

        self.assertIn("waiting_for_user", output_buffer["output_buffer_status"])
        self.assertIn("waiting_for_user", artifact_manifest["artifact_manifest_status"])
        self.assertIn("waiting_for_user", validation_gate["result_validation_gate_status"])
        self.assertIn("waiting_for_user", resume_cursor["resume_cursor_status"])
        self.assertIn("waiting_for_user", dead_letter_policy["dead_letter_policy_status"])
        self.assertIn("waiting_for_user", checkpoint_bundle["worker_checkpoint_bundle_status"])


class AgentRunnerFinalizationTests(unittest.TestCase):
    def test_finalization_chain_stays_dry_run(self):
        from agent_runs import (
            build_agent_runner_completion_ledger,
            build_agent_runner_completion_ledger_summary,
            build_agent_runner_downstream_handoff,
            build_agent_runner_human_review_packet,
            build_agent_runner_project_merge_preview,
            build_agent_runner_result_acceptance,
            build_agent_runner_run_finalization,
        )

        checkpoint = {
            "project_id": "project_finalization_ready",
            "target_agent_id": "planner_agent",
            "target_agent_stage": "planning",
            "worker_checkpoint_bundle_id": "worker_checkpoint_bundle_project_finalization_ready",
            "worker_checkpoint_bundle_status": "worker_checkpoint_bundle_waiting_for_real_agent_output",
            "dry_run": True,
        }
        acceptance = build_agent_runner_result_acceptance(checkpoint)
        merge_preview = build_agent_runner_project_merge_preview(acceptance)
        handoff = build_agent_runner_downstream_handoff(merge_preview)
        review_packet = build_agent_runner_human_review_packet(handoff)
        finalization = build_agent_runner_run_finalization(review_packet)
        completion_ledger = build_agent_runner_completion_ledger(finalization)
        completion_summary = build_agent_runner_completion_ledger_summary(completion_ledger)

        self.assertEqual(acceptance["result_acceptance_version"], "agent_runner_result_acceptance_v1")
        self.assertEqual(merge_preview["project_merge_preview_version"], "agent_runner_project_merge_preview_v1")
        self.assertEqual(handoff["downstream_handoff_version"], "agent_runner_downstream_handoff_v1")
        self.assertEqual(review_packet["human_review_packet_version"], "agent_runner_human_review_packet_v1")
        self.assertEqual(finalization["run_finalization_version"], "agent_runner_run_finalization_v1")
        self.assertEqual(completion_ledger["completion_ledger_version"], "agent_runner_completion_ledger_v1")
        self.assertFalse(acceptance["result_accepted"])
        self.assertFalse(merge_preview["merge_applied"])
        self.assertFalse(handoff["handoff_ready"])
        self.assertTrue(review_packet["human_review_required"])
        self.assertFalse(finalization["run_finalized"])
        self.assertFalse(completion_ledger["completion_ledger_recorded"])
        self.assertTrue(completion_ledger["manual_review_required"])
        self.assertEqual(completion_summary["summary_version"], "agent_runner_completion_ledger_summary_v1")

    def test_finalization_chain_waits_for_user(self):
        from agent_runs import (
            build_agent_runner_completion_ledger,
            build_agent_runner_downstream_handoff,
            build_agent_runner_human_review_packet,
            build_agent_runner_project_merge_preview,
            build_agent_runner_result_acceptance,
            build_agent_runner_run_finalization,
        )

        checkpoint = {
            "project_id": "project_finalization_waiting",
            "target_agent_id": "source_adapter_agent",
            "target_agent_stage": "source",
            "worker_checkpoint_bundle_id": "worker_checkpoint_bundle_project_finalization_waiting",
            "worker_checkpoint_bundle_status": "worker_checkpoint_bundle_waiting_for_user",
            "dry_run": True,
        }
        acceptance = build_agent_runner_result_acceptance(checkpoint)
        merge_preview = build_agent_runner_project_merge_preview(acceptance)
        handoff = build_agent_runner_downstream_handoff(merge_preview)
        review_packet = build_agent_runner_human_review_packet(handoff)
        finalization = build_agent_runner_run_finalization(review_packet)
        completion_ledger = build_agent_runner_completion_ledger(finalization)

        self.assertIn("waiting_for_user", acceptance["result_acceptance_status"])
        self.assertIn("waiting_for_user", merge_preview["project_merge_preview_status"])
        self.assertIn("waiting_for_user", handoff["downstream_handoff_status"])
        self.assertIn("waiting_for_user", review_packet["human_review_packet_status"])
        self.assertIn("waiting_for_user", finalization["run_finalization_status"])
        self.assertIn("waiting_for_user", completion_ledger["completion_ledger_status"])










    def test_provider_failure_recovery_report_blocks_real_retry_and_models_incident_policy(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_prompt_pack_report,
            build_keyframe_video_asset_chain_report,
            build_manual_generation_result_report,
            build_multi_agent_output_chain_report,
            build_provider_api_readiness_report,
            build_provider_failure_recovery_report,
            build_provider_sandbox_runtime_report,
            build_real_provider_execution_gate_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        asset_report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        prompt_pack_report = build_keyframe_prompt_pack_report(
            keyframe_video_asset_chain_report=asset_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        manual_result_report = build_manual_generation_result_report(
            keyframe_prompt_pack_report=prompt_pack_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        provider_api_report = build_provider_api_readiness_report(
            manual_generation_result_report=manual_result_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        sandbox_report = build_provider_sandbox_runtime_report(
            provider_api_readiness_report=provider_api_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        real_gate = build_real_provider_execution_gate_report(
            provider_api_readiness_report=provider_api_report,
            provider_sandbox_runtime_report=sandbox_report,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )
        report = build_provider_failure_recovery_report(
            real_provider_execution_gate_report=real_gate,
            project_id="project_provider_failure_recovery",
            requested_by="unit_test",
        )

        self.assertEqual(report["provider_failure_recovery_report_version"], "provider_failure_recovery_report_v1")
        self.assertEqual(report["report_status"], "provider_failure_recovery_ready_dry_run")
        self.assertTrue(report["real_provider_execution_gate_ready"])
        self.assertGreaterEqual(report["failure_type_count"], 8)
        self.assertGreater(report["retryable_failure_count"], 0)
        self.assertGreater(report["operator_review_failure_count"], 0)
        failure_types = {item["failure_type"] for item in report["failure_taxonomy"]}
        self.assertIn("provider_timeout", failure_types)
        self.assertIn("provider_rate_limited", failure_types)
        self.assertIn("provider_result_missing", failure_types)
        self.assertIn("quota_exceeded", failure_types)
        self.assertIn("secret_boundary_violation", failure_types)
        self.assertTrue(report["retry_policy"])
        self.assertTrue(report["fallback_plan"])
        self.assertTrue(report["circuit_breaker"])
        self.assertTrue(report["incident_policy"])
        self.assertTrue(report["alert_policy"])
        self.assertTrue(report["operator_review_packet"])
        self.assertTrue(report["rollback_pause_policy"])
        self.assertTrue(report["dry_run_receipt"])
        self.assertTrue(report["supports_failure_taxonomy"])
        self.assertTrue(report["supports_retry_policy"])
        self.assertTrue(report["supports_circuit_breaker"])
        self.assertTrue(report["supports_incident_policy"])
        self.assertTrue(report["supports_operator_review_packet"])
        self.assertTrue(report["operator_review_required"])
        self.assertTrue(report["rollback_required"])
        self.assertTrue(report["pause_followup_execution"])
        self.assertTrue(report["block_followup_real_execution"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["real_execution_enabled"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["external_api_called"])
        self.assertFalse(report["real_retry_performed"])
        self.assertFalse(report["provider_job_submitted"])
        self.assertFalse(report["provider_polling_performed"])
        self.assertFalse(report["provider_secret_read"])
        self.assertFalse(report["provider_secret_exported"])
        self.assertFalse(report["quota_reserved"])
        self.assertFalse(report["operator_review_captured"])
        self.assertFalse(report["operator_approval_captured"])
        self.assertFalse(report["circuit_state_mutated"])
        self.assertFalse(report["incident_detected"])
        self.assertFalse(report["incident_opened"])
        self.assertFalse(report["rollback_ready"])
        self.assertFalse(report["rollback_executed"])
        self.assertFalse(report["media_uploaded"])
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["result_url_fetched"])
        self.assertFalse(report["preview_url_fetched"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertTrue(report["dry_run"])


    def test_real_provider_execution_gate_report_blocks_real_provider_calls(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_prompt_pack_report,
            build_keyframe_video_asset_chain_report,
            build_manual_generation_result_report,
            build_multi_agent_output_chain_report,
            build_provider_api_readiness_report,
            build_provider_sandbox_runtime_report,
            build_real_provider_execution_gate_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )
        asset_report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )
        prompt_pack_report = build_keyframe_prompt_pack_report(
            keyframe_video_asset_chain_report=asset_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )
        manual_result_report = build_manual_generation_result_report(
            keyframe_prompt_pack_report=prompt_pack_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )
        provider_api_report = build_provider_api_readiness_report(
            manual_generation_result_report=manual_result_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )
        sandbox_report = build_provider_sandbox_runtime_report(
            provider_api_readiness_report=provider_api_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )
        report = build_real_provider_execution_gate_report(
            provider_api_readiness_report=provider_api_report,
            provider_sandbox_runtime_report=sandbox_report,
            project_id="project_real_provider_gate",
            requested_by="unit_test",
        )

        self.assertEqual(report["real_provider_execution_gate_report_version"], "real_provider_execution_gate_report_v1")
        self.assertEqual(report["report_status"], "real_provider_execution_gate_locked_ready_dry_run")
        self.assertTrue(report["provider_api_ready"])
        self.assertTrue(report["provider_sandbox_ready"])
        self.assertGreater(report["gate_check_count"], 0)
        self.assertGreater(report["blocking_failure_count"], 0)
        self.assertIn("operator_approval_captured", report["blocking_failures"])
        self.assertIn("quota_budget_policy_ready", report["blocking_failures"])
        self.assertIn("real_execution_adapter_enabled", report["blocking_failures"])
        self.assertTrue(report["credential_preflight"])
        self.assertTrue(report["quota_budget_gate"])
        self.assertTrue(report["approval_gate"])
        self.assertTrue(report["invocation_contract"])
        self.assertTrue(report["dry_run_receipt"])
        self.assertTrue(report["operator_approval_required"])
        self.assertTrue(report["rollback_required"])
        self.assertTrue(report["idempotency_required"])
        self.assertTrue(report["idempotency_key_ready"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["real_execution_enabled"])
        self.assertFalse(report["real_provider_client_allowed"])
        self.assertFalse(report["real_provider_client_constructed"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["external_api_called"])
        self.assertFalse(report["provider_job_submitted"])
        self.assertFalse(report["provider_polling_performed"])
        self.assertFalse(report["provider_secret_read"])
        self.assertFalse(report["provider_secret_exported"])
        self.assertFalse(report["secret_access_enabled"])
        self.assertFalse(report["quota_enabled"])
        self.assertFalse(report["quota_reserved"])
        self.assertFalse(report["operator_approval_captured"])
        self.assertFalse(report["rollback_ready"])
        self.assertFalse(report["media_uploaded"])
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["result_url_fetched"])
        self.assertFalse(report["preview_url_fetched"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertTrue(report["dry_run"])


    def test_provider_sandbox_runtime_report_models_fake_submit_poll_and_result_handoff(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_prompt_pack_report,
            build_keyframe_video_asset_chain_report,
            build_manual_generation_result_report,
            build_multi_agent_output_chain_report,
            build_provider_api_readiness_report,
            build_provider_sandbox_runtime_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_provider_sandbox_runtime",
            requested_by="unit_test",
        )
        asset_report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_provider_sandbox_runtime",
            requested_by="unit_test",
        )
        prompt_pack_report = build_keyframe_prompt_pack_report(
            keyframe_video_asset_chain_report=asset_report,
            project_id="project_provider_sandbox_runtime",
            requested_by="unit_test",
        )
        manual_result_report = build_manual_generation_result_report(
            keyframe_prompt_pack_report=prompt_pack_report,
            project_id="project_provider_sandbox_runtime",
            requested_by="unit_test",
        )
        provider_api_report = build_provider_api_readiness_report(
            manual_generation_result_report=manual_result_report,
            project_id="project_provider_sandbox_runtime",
            requested_by="unit_test",
        )
        report = build_provider_sandbox_runtime_report(
            provider_api_readiness_report=provider_api_report,
            project_id="project_provider_sandbox_runtime",
            requested_by="unit_test",
        )

        self.assertEqual(report["provider_sandbox_runtime_report_version"], "provider_sandbox_runtime_report_v1")
        self.assertEqual(report["report_status"], "provider_sandbox_runtime_ready_dry_run")
        self.assertTrue(report["provider_api_readiness_ready"])
        self.assertEqual(report["missing_item_count"], 0)
        self.assertEqual(report["stage_count"], 5)
        self.assertEqual(report["complete_stage_count"], 5)
        self.assertEqual(report["missing_stage_count"], 0)
        self.assertEqual(set(report["fake_provider_ids"]), {"runway", "pika"})
        self.assertEqual(report["fake_provider_count"], 2)
        self.assertTrue(report["supports_fake_runway_client"])
        self.assertTrue(report["supports_fake_pika_client"])
        self.assertTrue(report["supports_fake_provider_submit"])
        self.assertTrue(report["supports_simulated_provider_polling"])
        self.assertTrue(report["supports_normalized_provider_result"])
        self.assertTrue(report["supports_provider_result_handoff"])
        self.assertTrue(report["supports_experiment_feedback_bridge"])
        self.assertEqual(report["client_mode"], "fake_no_network")
        self.assertTrue(report["submit_contract"])
        self.assertTrue(report["polling_contract"])
        self.assertTrue(report["normalized_result_contract"])
        self.assertTrue(report["result_handoff_contract"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["real_execution_enabled"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["real_provider_client_constructed"])
        self.assertFalse(report["provider_job_submitted"])
        self.assertTrue(report["fake_provider_job_submittable"])
        self.assertFalse(report["provider_polling_performed"])
        self.assertTrue(report["fake_provider_polling_submittable"])
        self.assertFalse(report["external_api_called"])
        self.assertFalse(report["provider_secret_read"])
        self.assertFalse(report["provider_secret_exported"])
        self.assertFalse(report["media_uploaded"])
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["result_url_fetched"])
        self.assertFalse(report["preview_url_fetched"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertTrue(report["manual_review_required"])
        self.assertTrue(report["human_approval_required_before_provider_submit"])
        self.assertFalse(report["operator_approval_captured"])
        self.assertTrue(report["dry_run"])


    def test_provider_api_readiness_report_keeps_real_provider_calls_locked(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_prompt_pack_report,
            build_keyframe_video_asset_chain_report,
            build_manual_generation_result_report,
            build_multi_agent_output_chain_report,
            build_provider_api_readiness_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_provider_api_readiness",
            requested_by="unit_test",
        )
        asset_report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_provider_api_readiness",
            requested_by="unit_test",
        )
        prompt_pack_report = build_keyframe_prompt_pack_report(
            keyframe_video_asset_chain_report=asset_report,
            project_id="project_provider_api_readiness",
            requested_by="unit_test",
        )
        manual_result_report = build_manual_generation_result_report(
            keyframe_prompt_pack_report=prompt_pack_report,
            project_id="project_provider_api_readiness",
            requested_by="unit_test",
        )
        report = build_provider_api_readiness_report(
            manual_generation_result_report=manual_result_report,
            project_id="project_provider_api_readiness",
            requested_by="unit_test",
        )

        self.assertEqual(report["provider_api_readiness_report_version"], "provider_api_readiness_report_v1")
        self.assertEqual(report["report_status"], "provider_api_readiness_ready_dry_run")
        self.assertTrue(report["manual_generation_result_ready"])
        self.assertEqual(report["missing_item_count"], 0)
        self.assertEqual(report["provider_count"], 4)
        self.assertEqual(set(report["provider_ids"]), {"gemini", "doubao", "runway", "pika"})
        self.assertTrue(report["supports_gemini_contract"])
        self.assertTrue(report["supports_doubao_contract"])
        self.assertTrue(report["supports_runway_contract"])
        self.assertTrue(report["supports_pika_contract"])
        self.assertTrue(report["supports_fake_provider_clients"])
        self.assertTrue(report["supports_provider_polling_scaffold"])
        self.assertTrue(report["supports_cost_estimate_before_submit"])
        self.assertTrue(report["supports_approval_gate_before_submit"])
        self.assertTrue(report["supports_timeout_failure_contract"])
        self.assertTrue(report["supports_idempotency_boundary"])
        self.assertTrue(report["supports_secret_boundary"])
        self.assertTrue(report["api_key_boundary"])
        self.assertTrue(report["async_job_schema"])
        self.assertTrue(report["polling_contract"])
        self.assertTrue(report["failure_handling_contract"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["real_execution_enabled"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["provider_job_submitted"])
        self.assertFalse(report["provider_polling_performed"])
        self.assertFalse(report["provider_secret_read"])
        self.assertFalse(report["provider_secret_exported"])
        self.assertFalse(report["media_uploaded"])
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertTrue(report["human_approval_required_before_provider_submit"])
        self.assertFalse(report["operator_approval_captured"])
        self.assertTrue(report["dry_run"])


    def test_manual_generation_result_report_prepares_external_result_intake(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_prompt_pack_report,
            build_keyframe_video_asset_chain_report,
            build_manual_generation_result_report,
            build_multi_agent_output_chain_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_manual_generation_result",
            requested_by="unit_test",
        )
        asset_report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_manual_generation_result",
            requested_by="unit_test",
        )
        prompt_pack_report = build_keyframe_prompt_pack_report(
            keyframe_video_asset_chain_report=asset_report,
            project_id="project_manual_generation_result",
            requested_by="unit_test",
        )
        report = build_manual_generation_result_report(
            keyframe_prompt_pack_report=prompt_pack_report,
            project_id="project_manual_generation_result",
            requested_by="unit_test",
        )

        self.assertEqual(report["manual_generation_result_report_version"], "manual_generation_result_report_v1")
        self.assertEqual(report["report_status"], "manual_generation_result_intake_ready_dry_run")
        self.assertTrue(report["keyframe_prompt_pack_ready"])
        self.assertEqual(report["missing_item_count"], 0)
        self.assertTrue(report["external_result_input_schema_ready"])
        self.assertTrue(report["supports_result_url_intake"])
        self.assertTrue(report["supports_preview_url_intake"])
        self.assertTrue(report["supports_operator_notes"])
        self.assertTrue(report["supports_product_drift_checklist"])
        self.assertTrue(report["supports_evidence_consistency_checklist"])
        self.assertTrue(report["supports_rework_recommendation"])
        self.assertTrue(report["supports_revised_prompt_handoff"])
        self.assertTrue(report["supports_second_experiment_comparison"])
        self.assertTrue(report["can_record_external_experiment"])
        self.assertIn("gemini", report["supported_manual_tools"])
        self.assertIn("runway", report["supported_manual_tools"])
        fields = {item["field"] for item in report["result_intake_required_fields"]}
        self.assertIn("tool_name", fields)
        self.assertIn("prompt_source", fields)
        self.assertIn("result_url", fields)
        self.assertIn("preview_url", fields)
        self.assertTrue(report["product_drift_checklist"])
        self.assertTrue(report["evidence_consistency_checklist"])
        self.assertTrue(report["rework_recommendation_rules"])
        self.assertIn(
            "/api/v1/video-generation/jobs/{job_id}/external-experiments",
            report["existing_endpoint_contracts"],
        )
        self.assertTrue(report["manual_copy_paste_only"])
        self.assertTrue(report["manual_review_required"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["result_url_fetched"])
        self.assertFalse(report["preview_url_fetched"])
        self.assertFalse(report["media_uploaded"])
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertTrue(report["dry_run"])


    def test_keyframe_prompt_pack_report_builds_copy_ready_provider_variants(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_prompt_pack_report,
            build_keyframe_video_asset_chain_report,
            build_multi_agent_output_chain_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_keyframe_prompt_pack",
            requested_by="unit_test",
        )
        asset_report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_keyframe_prompt_pack",
            requested_by="unit_test",
        )
        report = build_keyframe_prompt_pack_report(
            keyframe_video_asset_chain_report=asset_report,
            project_id="project_keyframe_prompt_pack",
            requested_by="unit_test",
        )

        self.assertEqual(report["keyframe_prompt_pack_report_version"], "keyframe_prompt_pack_report_v1")
        self.assertEqual(report["report_status"], "keyframe_prompt_pack_ready_dry_run")
        self.assertTrue(report["keyframe_video_asset_chain_ready"])
        self.assertEqual(report["missing_item_count"], 0)
        self.assertEqual(report["shot_prompt_count"], 4)
        self.assertEqual(report["provider_variant_count"], 4)
        self.assertEqual(set(report["provider_ids"]), {"gemini", "doubao", "runway", "pika"})
        self.assertTrue(report["supports_product_identity_lock_prompt"])
        self.assertTrue(report["supports_shot_by_shot_keyframe_prompts"])
        self.assertTrue(report["supports_negative_prompt"])
        self.assertTrue(report["supports_image_reference_checklist"])
        self.assertTrue(report["supports_gemini_prompt"])
        self.assertTrue(report["supports_doubao_prompt"])
        self.assertTrue(report["supports_runway_prompt"])
        self.assertTrue(report["supports_pika_prompt"])
        self.assertIn("[PRODUCT_NAME]", report["product_identity_lock_prompt"])
        self.assertIn("Do not alter product shape", report["negative_prompt"])
        self.assertTrue(report["image_reference_checklist"])
        self.assertTrue(report["shot_prompts"][0]["copy_ready"])
        self.assertIn("Negative prompt:", report["shot_prompts"][0]["prompt"])
        self.assertTrue(all(item["manual_copy_paste_only"] for item in report["provider_prompt_variants"]))
        self.assertFalse(any(item["external_api_enabled"] for item in report["provider_prompt_variants"]))
        self.assertTrue(report["manual_copy_paste_only"])
        self.assertTrue(report["image_reference_required"])
        self.assertTrue(report["manual_review_required"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertTrue(report["dry_run"])


    def test_keyframe_video_asset_chain_report_connects_prompt_pack_and_manual_handoff(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_keyframe_video_asset_chain_report,
            build_multi_agent_output_chain_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        output_report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_keyframe_video_asset_chain",
            requested_by="unit_test",
        )
        report = build_keyframe_video_asset_chain_report(
            multi_agent_output_chain_report=output_report,
            project_id="project_keyframe_video_asset_chain",
            requested_by="unit_test",
        )

        self.assertEqual(
            report["keyframe_video_asset_chain_report_version"],
            "keyframe_video_asset_chain_report_v1",
        )
        self.assertEqual(report["report_status"], "keyframe_video_asset_chain_ready_dry_run")
        self.assertGreaterEqual(report["stage_count"], 6)
        self.assertEqual(report["missing_stage_count"], 0)
        self.assertTrue(report["multi_agent_output_chain_ready"])
        self.assertTrue(report["supports_product_asset_lock"])
        self.assertTrue(report["supports_keyframe_scene_plan"])
        self.assertTrue(report["supports_prompt_handoff_pack"])
        self.assertTrue(report["supports_manual_generation_handoff"])
        self.assertTrue(report["supports_experiment_feedback_rework"])
        self.assertTrue(report["supports_video_asset_export"])
        self.assertTrue(report["provider_neutral_prompt_pack_ready"])
        self.assertTrue(report["manual_generation_handoff_ready"])
        self.assertTrue(report["image_reference_required"])
        self.assertTrue(report["manual_review_required"])
        self.assertTrue(report["human_approval_required_before_generation"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["image_generation_performed"])
        self.assertFalse(report["paid_generation_allowed"])
        self.assertFalse(report["provider_secret_required"])
        self.assertFalse(report["provider_secret_exported"])
        self.assertTrue(report["dry_run"])


    def test_multi_agent_output_chain_report_connects_ecommerce_output_stages(self):
        from agent_runs import (
            build_agent_contract_completeness_report,
            build_agent_contract_registry,
            build_multi_agent_output_chain_report,
            build_source_adapter_contract_report,
        )

        agent_report = build_agent_contract_completeness_report(build_agent_contract_registry())
        source_report = build_source_adapter_contract_report()
        report = build_multi_agent_output_chain_report(
            agent_contract_report=agent_report,
            source_adapter_contract_report=source_report,
            project_id="project_multi_agent_output_chain",
            requested_by="unit_test",
        )

        self.assertEqual(
            report["multi_agent_output_chain_report_version"],
            "multi_agent_output_chain_report_v1",
        )
        self.assertEqual(report["report_status"], "multi_agent_output_chain_ready_dry_run")
        self.assertGreaterEqual(report["stage_count"], 6)
        self.assertEqual(report["missing_stage_count"], 0)
        self.assertTrue(report["agent_registry_ready"])
        self.assertTrue(report["source_adapter_contracts_ready"])
        self.assertTrue(report["source_visible_sample_ready"])
        self.assertTrue(report["supports_evidence_to_strategy"])
        self.assertTrue(report["supports_strategy_to_creative"])
        self.assertTrue(report["supports_creative_to_video"])
        self.assertTrue(report["supports_risk_to_finalizer"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertFalse(report["provider_call_allowed"])
        self.assertFalse(report["external_api_call_allowed"])
        self.assertFalse(report["agent_execution_allowed"])
        self.assertFalse(report["video_generation_performed"])
        self.assertFalse(report["creative_output_generated"])
        self.assertFalse(report["evidence_claims_invented"])
        self.assertTrue(report["dry_run"])


    def test_source_adapter_contract_report_covers_ecommerce_inputs(self):
        from agent_runs import build_source_adapter_contract_report

        report = build_source_adapter_contract_report()

        self.assertEqual(
            report["source_adapter_contract_report_version"],
            "source_adapter_contract_report_v1",
        )
        self.assertEqual(report["report_status"], "source_adapter_contracts_complete")
        self.assertGreaterEqual(report["adapter_count"], 5)
        self.assertEqual(report["missing_adapter_count"], 0)
        self.assertTrue(report["supports_amazon_visible_reviews"])
        self.assertTrue(report["supports_pasted_reviews"])
        self.assertTrue(report["supports_source_probe_debug"])
        self.assertTrue(report["supports_external_crawler_dry_run"])
        self.assertTrue(report["supports_review_workspace_visible_sample"])
        self.assertIn("bypass_login", report["prohibited_action_catalog"])
        self.assertIn("bypass_captcha", report["prohibited_action_catalog"])
        self.assertIn("visible_sample_only", report["boundary_catalog"])
        self.assertFalse(report["real_source_adapter_enabled"])
        self.assertFalse(report["allow_real_source_adapters_default"])
        self.assertFalse(report["external_fetch_performed"])
        self.assertFalse(report["provider_call_performed"])
        self.assertFalse(report["external_api_called"])
        self.assertFalse(report["agent_execution_performed"])
        self.assertFalse(report["real_execution_allowed"])
        self.assertTrue(report["dry_run"])
