from copy import deepcopy
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agent_runs import (
    append_graph_router_decision,
    apply_evidence_safe_storyboard_rework,
    build_controlled_provider_handoff_checklist,
    build_demo_ready_run_summary,
    build_experiment_comparison_decision_gate,
    build_graph_router_decision,
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
        lineage = build_lightweight_artifact_lineage(
            {"job_id": "job_1"},
            baseline,
            second,
            rework_run,
            comparison,
            gate,
        )
        checklist = build_controlled_provider_handoff_checklist(
            {"job_id": "job_1"},
            gate,
            rework_run,
            comparison,
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
        )

        self.assertEqual(lineage["lineage_version"], "agent_artifact_lineage_v1")
        self.assertEqual(lineage["lineage_type"], "experiment_feedback_demo_lineage")
        artifact_types = [artifact["artifact_type"] for artifact in lineage["artifact_chain"]]
        self.assertIn("revised_keyframe_plan", artifact_types)
        self.assertIn("revised_external_video_handoff", artifact_types)
        self.assertIn("experiment_comparison_decision_gate", artifact_types)
        self.assertIn("graph_router_decision", artifact_types)
        self.assertFalse(lineage["graph_evidence"]["is_linear_workflow"])
        self.assertTrue(lineage["graph_evidence"]["has_rework_run"])
        self.assertIn("provider_job_agent", lineage["agents_involved"])
        self.assertIn("graph_router_agent", lineage["agents_involved"])
        self.assertTrue(lineage["graph_evidence"]["has_graph_router_decision"])
        self.assertTrue(lineage["graph_evidence"]["has_centralized_route_decision"])
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
