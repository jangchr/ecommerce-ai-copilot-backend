"""In-memory async agent run state for staged creative generation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4


AGENT_RUN_STATUSES = {"queued", "running", "completed", "failed", "cancelled"}
AGENT_STATE_STATUSES = {"pending", "running", "complete", "failed", "skipped", "waiting_for_user", "rework_requested"}
GRAPH_VERSION = "agent_graph_runtime_v1"
GRAPH_EXECUTION_MODE = "rule_driven_agent_graph"
AUTONOMY_LEVEL = "rule_driven_v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now_ms() -> float:
    return datetime.now(timezone.utc).timestamp() * 1000


def build_agent_state(
    agent_id: str,
    role: str,
    recommended_user_action: str,
    input_artifacts: list[str] | None = None,
    output_artifacts: list[str] | None = None,
    requires_human_review: bool = False,
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "role": role,
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "duration_ms": None,
        "input_artifacts": list(input_artifacts or []),
        "output_artifacts": list(output_artifacts or []),
        "decision_summary": "",
        "warnings": [],
        "requires_human_review": bool(requires_human_review),
        "business_impact": "",
        "recommended_user_action": recommended_user_action,
    }


def build_graph_node(
    node_id: str,
    agent_id: str,
    role: str,
    node_type: str,
    description: str,
    recommended_user_action: str,
    input_artifacts: list[str] | None = None,
    output_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "agent_id": agent_id,
        "role": role,
        "status": "pending",
        "node_type": node_type,
        "description": description,
        "recommended_user_action": recommended_user_action,
        "input_artifacts": list(input_artifacts or []),
        "output_artifacts": list(output_artifacts or []),
    }


def build_graph_edge(
    edge_id: str,
    from_node_id: str,
    to_node_id: str,
    edge_type: str,
    condition: str,
) -> dict[str, Any]:
    return {
        "edge_id": edge_id,
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "edge_type": edge_type,
        "condition": condition,
        "status": "inactive",
        "decision_reason": "",
    }


def default_pasted_reviews_agent_states() -> list[dict[str, Any]]:
    return [
        build_agent_state(
            "planner_agent",
            "Planner Agent",
            "Confirm the pasted feedback brief is valid before generation.",
            ["pasted_reviews_request"],
            ["validated_generation_plan"],
        ),
        build_agent_state(
            "evidence_agent",
            "Evidence Agent",
            "Review evidence warnings before using claims.",
            ["pasted_reviews"],
            ["evidence_quotes", "llm_evidence_packet"],
            requires_human_review=True,
        ),
        build_agent_state(
            "strategy_agent",
            "Strategy Agent",
            "Confirm selected creative angle.",
            ["llm_evidence_packet"],
            ["creative_strategy"],
        ),
        build_agent_state(
            "storyboard_agent",
            "Storyboard Agent",
            "Review hook, CTA, and scenes.",
            ["creative_strategy"],
            ["storyboard"],
        ),
        build_agent_state(
            "asset_lock_agent",
            "Product Asset Lock Agent",
            "Confirm product identity and image reference rules.",
            ["storyboard"],
            ["product_asset_lock"],
            requires_human_review=True,
        ),
        build_agent_state(
            "keyframe_agent",
            "Keyframe Agent",
            "Generate one short clip first and check product consistency.",
            ["product_asset_lock"],
            ["keyframe_plan"],
            requires_human_review=True,
        ),
        build_agent_state(
            "prompt_handoff_agent",
            "Prompt Handoff Agent",
            "Copy Gemini/Doubao prompt for manual testing.",
            ["video_generation_packet"],
            ["external_video_tool_handoff"],
        ),
        build_agent_state(
            "cost_agent",
            "Cost Agent",
            "Review estimated pricing before paid generation.",
            ["external_video_tool_handoff"],
            ["cost_estimate"],
            requires_human_review=True,
        ),
        build_agent_state(
            "risk_agent",
            "Risk Agent",
            "Review unsupported-claim warnings.",
            ["evaluation", "data_warnings"],
            ["risk_notes"],
            requires_human_review=True,
        ),
        build_agent_state(
            "finalizer_agent",
            "Finalizer Agent",
            "Use the completed result for copy, video jobs, and manual handoff.",
            ["all_generated_artifacts"],
            ["final_product_result"],
        ),
    ]


def default_agent_graph_nodes() -> list[dict[str, Any]]:
    return [
        build_graph_node("planner_agent", "planner_agent", "Planner Agent", "agent", "Validate request and define the staged graph route.", "Confirm the pasted feedback brief is valid before generation.", ["pasted_reviews_request"], ["validated_generation_plan"]),
        build_graph_node("evidence_agent", "evidence_agent", "Evidence Agent", "agent", "Build the LLM evidence packet from supplied reviews.", "Review evidence warnings before using claims.", ["pasted_reviews"], ["evidence_quotes", "llm_evidence_packet"]),
        build_graph_node("strategy_agent", "strategy_agent", "Strategy Agent", "agent", "Turn evidence into a creative strategy and hook direction.", "Confirm selected creative angle.", ["llm_evidence_packet"], ["creative_strategy"]),
        build_graph_node("storyboard_agent", "storyboard_agent", "Storyboard Agent", "agent", "Build hook, CTA, and storyboard scenes.", "Review hook, CTA, and scenes.", ["creative_strategy"], ["storyboard"]),
        build_graph_node("risk_agent", "risk_agent", "Risk Agent", "validation", "Validate unsupported-claim and evidence-boundary risks.", "Review unsupported-claim warnings.", ["storyboard", "evaluation"], ["risk_notes"]),
        build_graph_node("asset_lock_agent", "asset_lock_agent", "Product Asset Lock Agent", "agent", "Prepare product identity and image-reference rules.", "Confirm product identity and image reference rules.", ["storyboard"], ["product_asset_lock"]),
        build_graph_node("product_identity_validator", "product_identity_validator", "Product Identity Validator", "validation", "Validate product identity and category before visual prompts.", "Provide product identity or reference details if the lock is weak.", ["product_asset_lock"], ["product_identity_validation"]),
        build_graph_node("keyframe_agent", "keyframe_agent", "Keyframe Agent", "agent", "Prepare keyframe and short-clip guidance.", "Generate one short clip first and check product consistency.", ["product_asset_lock"], ["keyframe_plan"]),
        build_graph_node("prompt_handoff_agent", "prompt_handoff_agent", "Prompt Handoff Agent", "agent", "Prepare manual external video tool handoff prompts.", "Copy Gemini/Doubao prompt for manual testing.", ["video_generation_packet"], ["external_video_tool_handoff"]),
        build_graph_node("cost_agent", "cost_agent", "Cost Agent", "validation", "Check provider/cost routing before any paid path.", "Review estimated pricing before paid generation.", ["external_video_tool_handoff"], ["cost_boundary"]),
        build_graph_node("route_selector_agent", "route_selector_agent", "Route Selector Agent", "validation", "Choose safe manual/provider route based on cost and feature flags.", "Use manual external tool handoff unless a real provider is explicitly enabled.", ["cost_boundary"], ["route_decision"]),
        build_graph_node("provider_job_agent", "provider_job_agent", "Provider Job Agent", "human_review", "Create or update a tracked Video Job when the user chooses.", "Create or update a Video Job.", ["route_decision"], ["video_job"]),
        build_graph_node("experiment_agent", "experiment_agent", "Experiment Agent", "human_review", "Wait for external result and score experiment quality.", "Paste external video result and score experiment.", ["video_job"], ["external_video_experiment"]),
        build_graph_node("finalizer_agent", "finalizer_agent", "Finalizer Agent", "terminal", "Finalize generated artifacts for the Product dashboard.", "Use the completed result for copy, video jobs, and manual handoff.", ["all_generated_artifacts"], ["final_product_result"]),
    ]


def default_agent_graph_edges() -> list[dict[str, Any]]:
    return [
        build_graph_edge("planner_to_evidence", "planner_agent", "evidence_agent", "normal", "request valid"),
        build_graph_edge("evidence_to_strategy", "evidence_agent", "strategy_agent", "normal", "evidence packet built"),
        build_graph_edge("strategy_to_storyboard", "strategy_agent", "storyboard_agent", "normal", "strategy generated"),
        build_graph_edge("storyboard_to_risk", "storyboard_agent", "risk_agent", "validation", "storyboard requires risk validation"),
        build_graph_edge("risk_to_storyboard_rework", "risk_agent", "storyboard_agent", "rework", "unsupported claims or high risk and loop_count < max"),
        build_graph_edge("risk_to_asset_lock", "risk_agent", "asset_lock_agent", "normal", "risk accepted or warning-only"),
        build_graph_edge("asset_lock_to_product_identity_validator", "asset_lock_agent", "product_identity_validator", "validation", "asset lock ready"),
        build_graph_edge("product_identity_validator_to_asset_lock_rework", "product_identity_validator", "asset_lock_agent", "rework", "product identity weak"),
        build_graph_edge("product_identity_validator_waiting", "product_identity_validator", "provider_job_agent", "waiting_for_user", "product image or reference needed"),
        build_graph_edge("product_identity_validator_to_keyframe", "product_identity_validator", "keyframe_agent", "normal", "product identity validated"),
        build_graph_edge("keyframe_to_prompt_handoff", "keyframe_agent", "prompt_handoff_agent", "normal", "keyframe plan ready"),
        build_graph_edge("prompt_handoff_to_cost", "prompt_handoff_agent", "cost_agent", "normal", "handoff prompts ready"),
        build_graph_edge("cost_to_route_selector", "cost_agent", "route_selector_agent", "validation", "cost boundary checked"),
        build_graph_edge("route_selector_to_provider_job", "route_selector_agent", "provider_job_agent", "branch", "estimated cost acceptable and user confirmation possible"),
        build_graph_edge("route_selector_to_prompt_handoff_fallback", "route_selector_agent", "prompt_handoff_agent", "fallback", "cost too high or real API disabled"),
        build_graph_edge("provider_job_to_experiment", "provider_job_agent", "experiment_agent", "waiting_for_user", "provider job requires user action"),
        build_graph_edge("experiment_to_keyframe_rework", "experiment_agent", "keyframe_agent", "rework", "experiment failed or product drift detected"),
        build_graph_edge("experiment_to_finalizer", "experiment_agent", "finalizer_agent", "normal", "experiment accepted"),
        build_graph_edge("prompt_handoff_to_finalizer_fallback", "prompt_handoff_agent", "finalizer_agent", "fallback", "manual external tool workflow selected"),
    ]


def build_agent_run(
    input_type: str,
    output_language: str,
    request_id: str = "",
) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "run_id": str(uuid4()),
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "updated_at": now,
        "input_type": input_type,
        "output_language": output_language or "en",
        "current_agent_id": None,
        "agents": default_pasted_reviews_agent_states(),
        "graph_version": GRAPH_VERSION,
        "graph_execution_mode": GRAPH_EXECUTION_MODE,
        "graph_nodes": default_agent_graph_nodes(),
        "graph_edges": default_agent_graph_edges(),
        "active_node_id": None,
        "visited_node_ids": [],
        "active_edge_ids": [],
        "transition_decisions": [],
        "validation_results": [],
        "rework_loops": [],
        "loop_count": 0,
        "max_loop_count": 1,
        "waiting_for_user": False,
        "waiting_reason": "",
        "branch_selected": "",
        "is_autonomous_graph_runtime": True,
        "autonomy_level": AUTONOMY_LEVEL,
        "llm_autonomous_decision_enabled": False,
        "events": [],
        "result": None,
        "error": "",
        "request_id": request_id,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
    }


class InMemoryAgentRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def create(self, run: dict[str, Any]) -> dict[str, Any]:
        run_id = str(run.get("run_id") or "")
        if not run_id:
            raise ValueError("run_id is required")
        with self._lock:
            self._runs[run_id] = deepcopy(run)
            return deepcopy(self._runs[run_id])

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(str(run_id or ""))
            return deepcopy(run) if run is not None else None

    def update(self, run_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        safe_run_id = str(run_id or "")
        if not safe_run_id:
            raise ValueError("run_id is required")
        with self._lock:
            run = deepcopy(self._runs[safe_run_id])
            run.update(deepcopy(changes))
            run["updated_at"] = utc_now_iso()
            self._runs[safe_run_id] = run
            return deepcopy(run)

    def list(self, limit: int = 10) -> list[dict[str, Any]]:
        safe_limit = max(1, int(limit or 10))
        with self._lock:
            runs = sorted(
                self._runs.values(),
                key=lambda item: str(item.get("created_at") or ""),
                reverse=True,
            )
            return deepcopy(runs[:safe_limit])

    def clear(self) -> None:
        with self._lock:
            self._runs.clear()

    def append_event(
        self,
        run_id: str,
        event_type: str,
        message: str,
        agent_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "agent_id": agent_id,
            "message": message,
            "created_at": utc_now_iso(),
            "data": deepcopy(data or {}),
        }
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            run.setdefault("events", []).append(event)
            run["updated_at"] = utc_now_iso()
            self._runs[str(run_id)] = run
            return deepcopy(event)

    def start_run(self, run_id: str) -> dict[str, Any]:
        now = utc_now_iso()
        return self.update(run_id, {"status": "running", "started_at": now})

    def complete_run(self, run_id: str, result: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        return self.update(
            run_id,
            {
                "status": "completed",
                "completed_at": now,
                "current_agent_id": None,
                "result": deepcopy(result),
                "error": "",
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        )

    def fail_run(self, run_id: str, error: str) -> dict[str, Any]:
        now = utc_now_iso()
        return self.update(
            run_id,
            {
                "status": "failed",
                "completed_at": now,
                "current_agent_id": None,
                "error": str(error or "Agent run failed."),
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        )

    def start_agent(self, run_id: str, agent_id: str) -> dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            for agent in run.get("agents", []):
                if agent.get("agent_id") == agent_id:
                    agent["status"] = "running"
                    agent["started_at"] = now
                    agent["_started_ms"] = utc_now_ms()
                    break
            run["status"] = "running"
            run["current_agent_id"] = agent_id
            run["updated_at"] = now
            self._runs[str(run_id)] = run
            return deepcopy(run)

    def complete_agent(
        self,
        run_id: str,
        agent_id: str,
        decision_summary: str,
        business_impact: str = "",
        output_artifacts: list[str] | None = None,
        warnings: list[str] | None = None,
        status: str = "complete",
    ) -> dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            for agent in run.get("agents", []):
                if agent.get("agent_id") == agent_id:
                    started_ms = agent.pop("_started_ms", None)
                    agent["status"] = status if status in AGENT_STATE_STATUSES else "complete"
                    agent["completed_at"] = now
                    agent["duration_ms"] = max(0, int(utc_now_ms() - started_ms)) if started_ms else None
                    agent["decision_summary"] = decision_summary
                    agent["business_impact"] = business_impact
                    if output_artifacts is not None:
                        agent["output_artifacts"] = list(output_artifacts)
                    if warnings is not None:
                        agent["warnings"] = list(warnings)
                    break
            run["updated_at"] = now
            self._runs[str(run_id)] = run
            return deepcopy(run)

    def fail_agent(self, run_id: str, agent_id: str, error: str) -> dict[str, Any]:
        return self.complete_agent(
            run_id,
            agent_id,
            decision_summary=str(error or "Agent failed."),
            business_impact="Generation stopped before final artifacts were ready.",
            status="failed",
            warnings=[str(error or "Agent failed.")],
        )

    def set_graph_node_status(self, run_id: str, node_id: str, status: str) -> dict[str, Any]:
        safe_status = status if status in AGENT_STATE_STATUSES else "pending"
        now = utc_now_iso()
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            for node in run.get("graph_nodes", []):
                if node.get("node_id") == node_id:
                    node["status"] = safe_status
                    break
            if safe_status == "running":
                run["active_node_id"] = node_id
            elif run.get("active_node_id") == node_id and safe_status in {"complete", "failed", "skipped", "waiting_for_user"}:
                run["active_node_id"] = None
            visited = list(run.get("visited_node_ids") or [])
            if node_id and node_id not in visited and safe_status in {"running", "complete", "waiting_for_user", "rework_requested"}:
                visited.append(node_id)
            run["visited_node_ids"] = visited
            run["updated_at"] = now
            self._runs[str(run_id)] = run
            return deepcopy(run)

    def traverse_graph_edge(self, run_id: str, edge_id: str, decision_reason: str = "") -> dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            active_edges = list(run.get("active_edge_ids") or [])
            edge_to_node = ""
            edge_from_node = ""
            for edge in run.get("graph_edges", []):
                if edge.get("edge_id") == edge_id:
                    edge["status"] = "traversed"
                    edge["decision_reason"] = decision_reason
                    edge_from_node = str(edge.get("from_node_id") or "")
                    edge_to_node = str(edge.get("to_node_id") or "")
                    break
            if edge_id and edge_id not in active_edges:
                active_edges.append(edge_id)
            visited = list(run.get("visited_node_ids") or [])
            for node_id in [edge_from_node, edge_to_node]:
                if node_id and node_id not in visited:
                    visited.append(node_id)
            run["active_edge_ids"] = active_edges
            run["visited_node_ids"] = visited
            run["updated_at"] = now
            self._runs[str(run_id)] = run
            return deepcopy(run)

    def add_transition_decision(
        self,
        run_id: str,
        from_node_id: str,
        selected_to_node_id: str,
        agent_id: str,
        decision_type: str,
        reason: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        decision = {
            "decision_id": str(uuid4()),
            "from_node_id": from_node_id,
            "selected_to_node_id": selected_to_node_id,
            "agent_id": agent_id,
            "decision_type": decision_type,
            "reason": reason,
            "created_at": utc_now_iso(),
            "data": deepcopy(data or {}),
        }
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            run.setdefault("transition_decisions", []).append(decision)
            run["updated_at"] = utc_now_iso()
            self._runs[str(run_id)] = run
            return deepcopy(decision)

    def add_validation_result(
        self,
        run_id: str,
        validator_agent_id: str,
        target_agent_id: str,
        target_artifact: str,
        status: str,
        reason: str,
        severity: str = "low",
        rework_target: str = "",
    ) -> dict[str, Any]:
        validation = {
            "validation_id": str(uuid4()),
            "validator_agent_id": validator_agent_id,
            "target_agent_id": target_agent_id,
            "target_artifact": target_artifact,
            "status": status,
            "reason": reason,
            "severity": severity,
            "rework_target": rework_target,
            "created_at": utc_now_iso(),
        }
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            run.setdefault("validation_results", []).append(validation)
            run["updated_at"] = utc_now_iso()
            self._runs[str(run_id)] = run
            return deepcopy(validation)

    def add_rework_loop(
        self,
        run_id: str,
        source_agent_id: str,
        target_agent_id: str,
        reason: str,
        status: str = "requested",
    ) -> dict[str, Any]:
        with self._lock:
            run = deepcopy(self._runs[str(run_id)])
            loop_count = int(run.get("loop_count") or 0) + 1
            max_loop_count = int(run.get("max_loop_count") or 1)
            loop = {
                "loop_id": str(uuid4()),
                "source_agent_id": source_agent_id,
                "target_agent_id": target_agent_id,
                "reason": reason,
                "loop_count": loop_count,
                "max_loop_count": max_loop_count,
                "status": status,
            }
            run["loop_count"] = loop_count
            run.setdefault("rework_loops", []).append(loop)
            run["updated_at"] = utc_now_iso()
            self._runs[str(run_id)] = run
            return deepcopy(loop)

    def set_branch_selected(self, run_id: str, branch: str) -> dict[str, Any]:
        return self.update(run_id, {"branch_selected": branch})

    def set_waiting_for_user(self, run_id: str, waiting: bool, reason: str = "") -> dict[str, Any]:
        return self.update(run_id, {"waiting_for_user": bool(waiting), "waiting_reason": reason})

    def complete_graph(self, run_id: str) -> dict[str, Any]:
        return self.update(run_id, {"active_node_id": None})
