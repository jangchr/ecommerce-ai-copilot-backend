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
    def test_execution_receipt_records_ready_dry_run_without_execution(self):
        from agent_runs import (
            build_agent_runner_dispatch_event,
            build_agent_runner_dispatch_ticket,
            build_agent_runner_execution_receipt,
            build_agent_runner_execution_receipt_summary,
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

