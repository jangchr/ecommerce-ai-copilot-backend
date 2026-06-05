"""In-memory async agent run state for staged creative generation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4


AGENT_RUN_STATUSES = {"queued", "running", "completed", "failed", "cancelled"}
AGENT_STATE_STATUSES = {"pending", "running", "complete", "failed", "skipped", "waiting_for_user"}


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
