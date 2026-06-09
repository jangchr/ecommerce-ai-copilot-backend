"""In-memory async agent run state for staged creative generation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
from threading import RLock
from typing import Any
from uuid import uuid4


AGENT_RUN_STATUSES = {"queued", "running", "completed", "failed", "cancelled"}
AGENT_STATE_STATUSES = {"pending", "running", "complete", "failed", "skipped", "waiting_for_user", "rework_requested"}
GRAPH_VERSION = "agent_graph_runtime_v1"
GRAPH_EXECUTION_MODE = "rule_driven_agent_graph"
AUTONOMY_LEVEL = "rule_driven_v1"

RISKY_STORYBOARD_TERMS = [
    "leak-proof guarantee",
    "no leaks guaranteed",
    "clinically proven",
    "best on the market",
    "guarantees",
    "guaranteed",
    "permanent",
    "eliminate",
    "medical",
    "always",
    "never",
    "100%",
    "cure",
    "#1",
]

STORYBOARD_REWORK_TEXT_KEYS = {
    "caption",
    "caption_draft",
    "capcut_shot_list",
    "cta",
    "full_video_prompt",
    "generic_video_prompt",
    "hook",
    "narration",
    "on_screen_text",
    "overlay_text",
    "pika_style_prompt",
    "prompt",
    "runway_style_prompt",
    "selected_prompt",
    "scene_goal",
    "visual",
    "visual_description",
    "visual_prompt",
}

STORYBOARD_REWORK_SKIP_KEYS = {
    "evidence",
    "evidence_quote",
    "evidence_quote_used",
    "evidence_quotes",
    "product_category",
    "product_identity",
    "product_name",
    "source",
    "source_url",
}

STORYBOARD_REWRITE_REPLACEMENTS = [
    (r"\bleak-proof guarantee\b", "check the supplied review concerns before buying"),
    (r"\bno leaks guaranteed\b", "check the supplied review concerns before buying"),
    (r"\bclinically proven\b", "unsupported claim removed"),
    (r"\bbest on the market\b", "one review-backed option"),
    (r"\bguarantees\b", "is framed by supplied reviews"),
    (r"\bguaranteed\b", "review-backed"),
    (r"\bpermanent\b", "longer-term review-backed"),
    (r"\beliminate\b", "reduce in supplied review context"),
    (r"\bmedical\b", "unsupported claim removed"),
    (r"\balways\b", "in these supplied reviews"),
    (r"\bnever\b", "not reported in these supplied reviews"),
    (r"100%", "review-backed"),
    (r"\bcure\b", "unsupported claim removed"),
    (r"#1", "review-backed option"),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now_ms() -> float:
    return datetime.now(timezone.utc).timestamp() * 1000


def _storyboard_rework_candidate_texts(value: Any, key: str = "") -> list[str]:
    if isinstance(value, dict):
        texts: list[str] = []
        for child_key, child_value in value.items():
            safe_key = str(child_key or "")
            if safe_key in STORYBOARD_REWORK_SKIP_KEYS:
                continue
            texts.extend(_storyboard_rework_candidate_texts(child_value, safe_key))
        return texts
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_storyboard_rework_candidate_texts(item, key))
        return texts
    if isinstance(value, str) and key in STORYBOARD_REWORK_TEXT_KEYS:
        return [value]
    return []


def _storyboard_risk_scan_text(text: str) -> str:
    safe_text = str(text or "")
    safety_boilerplate_patterns = [
        r"Evidence boundary:.*?(?:\.|\n)",
        r"avoid unsupported claims[^.]*\.",
        r"before/after guarantees, medical claims, or full-market statistics",
        r"Missing; keep claim conservative\.?",
        r"Missing scene-level evidence quote; keep claim conservative\.?",
    ]
    for pattern in safety_boilerplate_patterns:
        safe_text = re.sub(pattern, " ", safe_text, flags=re.IGNORECASE | re.DOTALL)
    return safe_text


def _append_graph_warning(data: dict[str, Any], warning: str) -> None:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else None
    evidence = insights.get("evidence") if isinstance(insights, dict) and isinstance(insights.get("evidence"), dict) else None
    if evidence is not None:
        warnings = evidence.get("data_warnings")
        if not isinstance(warnings, list):
            warnings = []
        if warning not in warnings:
            warnings.append(warning)
        evidence["data_warnings"] = warnings
    video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else None
    if video_packet is not None:
        risk_notes = video_packet.get("risk_notes")
        if not isinstance(risk_notes, list):
            risk_notes = []
        if warning not in risk_notes:
            risk_notes.append(warning)
        video_packet["risk_notes"] = risk_notes


def detect_storyboard_rework_need(generated_data: dict[str, Any]) -> dict[str, Any]:
    """Detect unsupported absolute claims in generated storyboard artifacts."""

    if not isinstance(generated_data, dict):
        return {
            "needs_rework": False,
            "reason": "No generated data available for storyboard risk validation.",
            "matched_terms": [],
            "severity": "medium",
        }

    evaluation = generated_data.get("evaluation") if isinstance(generated_data.get("evaluation"), dict) else {}
    risk_level = str(evaluation.get("risk_level") or "").strip().lower()
    matched_terms: list[str] = []
    text_blob = "\n".join(
        _storyboard_risk_scan_text(text)
        for text in _storyboard_rework_candidate_texts(generated_data)
    ).lower()
    for term in RISKY_STORYBOARD_TERMS:
        if term.lower() in text_blob and term not in matched_terms:
            matched_terms.append(term)

    high_terms = {
        "#1",
        "100%",
        "best on the market",
        "clinically proven",
        "cure",
        "eliminate",
        "leak-proof guarantee",
        "medical",
        "no leaks guaranteed",
        "permanent",
    }
    needs_rework = risk_level == "high" or bool(matched_terms)
    severity = "high" if risk_level == "high" or any(term in high_terms for term in matched_terms) else "medium"
    if risk_level == "high" and matched_terms:
        reason = f"High risk level plus unsupported storyboard wording: {', '.join(matched_terms)}."
    elif risk_level == "high":
        reason = "High risk level requires storyboard rework before continuing."
    elif matched_terms:
        reason = f"Unsupported storyboard wording detected: {', '.join(matched_terms)}."
    else:
        reason = "No risky unsupported storyboard wording detected."

    return {
        "needs_rework": needs_rework,
        "reason": reason,
        "matched_terms": matched_terms,
        "severity": severity,
    }


def _rewrite_storyboard_text(text: str) -> str:
    rewritten = str(text or "")
    for pattern, replacement in STORYBOARD_REWRITE_REPLACEMENTS:
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
    return rewritten


def _rewrite_storyboard_fields(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        rewritten: dict[str, Any] = {}
        for child_key, child_value in value.items():
            safe_key = str(child_key or "")
            if safe_key in STORYBOARD_REWORK_SKIP_KEYS:
                rewritten[child_key] = deepcopy(child_value)
            else:
                rewritten[child_key] = _rewrite_storyboard_fields(child_value, safe_key)
        return rewritten
    if isinstance(value, list):
        return [_rewrite_storyboard_fields(item, key) for item in value]
    if isinstance(value, str) and key in STORYBOARD_REWORK_TEXT_KEYS:
        return _rewrite_storyboard_text(value)
    return deepcopy(value)


def apply_evidence_safe_storyboard_rework(
    generated_data: dict[str, Any],
    reason: str,
    matched_terms: list[str],
) -> dict[str, Any]:
    """Apply a deterministic evidence-safe rewrite to generated storyboard text."""

    data = _rewrite_storyboard_fields(generated_data if isinstance(generated_data, dict) else {})
    rework_summary = {
        "rework_version": "risk_storyboard_rework_v1",
        "source_agent_id": "risk_agent",
        "target_agent_id": "storyboard_agent",
        "reason": str(reason or "Storyboard wording was revised for evidence safety."),
        "matched_terms": list(matched_terms or []),
        "changed": True,
    }
    data["agent_graph_rework_summary"] = rework_summary
    evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else None
    if evaluation is not None and str(evaluation.get("risk_level") or "").lower() == "high":
        evaluation["risk_level"] = "medium"
        reasoning = str(evaluation.get("reasoning") or "").strip()
        suffix = "Evidence-safe storyboard rework applied; keep human review on unsupported claim boundaries."
        evaluation["reasoning"] = f"{reasoning} {suffix}".strip()
    _append_graph_warning(data, "storyboard_reworked_for_evidence_safety")
    return data


def _experiment_score_snapshot(experiment: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_consistency_score": experiment.get("product_consistency_score"),
        "storyboard_following_score": experiment.get("storyboard_following_score"),
        "visual_quality_score": experiment.get("visual_quality_score"),
        "ad_readiness_score": experiment.get("ad_readiness_score"),
        "overall_score": experiment.get("overall_score"),
        "actual_cost_usd": experiment.get("actual_cost_usd"),
    }


def _numeric_experiment_score(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_experiment_feedback_decision(
    experiment: dict[str, Any],
    job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic graph feedback decision from external experiment scores."""

    safe_experiment = experiment if isinstance(experiment, dict) else {}
    scores = _experiment_score_snapshot(safe_experiment)
    issue_options = [
        (
            "product_consistency_score",
            "product_consistency",
            "keyframe_agent",
            "asset_lock_agent",
            "high",
            "Product drift or identity mismatch detected.",
            "Route back to Keyframe Agent and Asset Lock Agent to tighten product identity and visual anchors.",
        ),
        (
            "storyboard_following_score",
            "storyboard_following",
            "prompt_handoff_agent",
            "keyframe_agent",
            "medium",
            "External result did not follow the storyboard enough.",
            "Revise prompt handoff and keyframe constraints so the external tool follows the scene sequence.",
        ),
        (
            "ad_readiness_score",
            "ad_readiness",
            "storyboard_agent",
            "strategy_agent",
            "medium",
            "Result is not ad-ready; revise hook, CTA, or scene sequence.",
            "Route back to Storyboard Agent to make the video draft more conversion-ready.",
        ),
        (
            "visual_quality_score",
            "visual_quality",
            "prompt_handoff_agent",
            "",
            "medium",
            "Visual quality is too weak for handoff.",
            "Improve visual and motion prompt constraints before another external test.",
        ),
    ]
    low_dimension_issues: list[tuple[float, int, tuple[str, str, str, str, str, str, str]]] = []
    for priority, option in enumerate(issue_options):
        score = _numeric_experiment_score(scores.get(option[0]))
        if score is not None and score <= 2:
            low_dimension_issues.append((score, priority, option))

    actual_cost = _numeric_experiment_score(scores.get("actual_cost_usd"))
    overall_score = _numeric_experiment_score(scores.get("overall_score"))
    cost_value_issue = actual_cost is not None and actual_cost >= 1.0 and overall_score is not None and overall_score <= 3

    selected: tuple[str, str, str, str, str, str, str] | None = None
    if low_dimension_issues:
        selected = sorted(low_dimension_issues, key=lambda item: (item[0], item[1]))[0][2]
    elif overall_score is not None and overall_score <= 2:
        selected = (
            "overall_score",
            "overall_quality",
            "prompt_handoff_agent",
            "",
            "medium",
            "Overall external result quality is too low.",
            "Route back to Prompt Handoff Agent to tighten the next external generation prompt.",
        )
    elif cost_value_issue:
        selected = (
            "actual_cost_usd",
            "cost_value",
            "cost_agent",
            "route_selector_agent",
            "medium",
            "Poor value for cost detected.",
            "Route back to Cost Agent and Route Selector Agent to prefer cheaper or manual routes.",
        )

    if selected is None:
        return {
            "feedback_version": "experiment_feedback_loop_v1",
            "has_feedback": False,
            "source_agent_id": "experiment_agent",
            "target_agent_id": "",
            "secondary_target_agent_id": "",
            "decision_type": "feedback_recorded_no_rework",
            "severity": "low",
            "issue_type": "none",
            "reason": "Experiment scores do not require graph rework.",
            "recommended_action": "Keep the current video workflow and record this experiment as a usable reference.",
            "score_snapshot": scores,
            "loop_guard": {
                "max_feedback_loop_count": 1,
                "feedback_loop_count": 0,
            },
        }

    _, issue_type, target_agent_id, secondary_target_agent_id, severity, reason, recommended_action = selected
    return {
        "feedback_version": "experiment_feedback_loop_v1",
        "has_feedback": True,
        "source_agent_id": "experiment_agent",
        "target_agent_id": target_agent_id,
        "secondary_target_agent_id": secondary_target_agent_id,
        "decision_type": "feedback_rework_requested",
        "severity": "high" if severity == "high" else "medium",
        "issue_type": issue_type,
        "reason": reason,
        "recommended_action": recommended_action,
        "score_snapshot": scores,
        "loop_guard": {
            "max_feedback_loop_count": 1,
            "feedback_loop_count": 1,
        },
    }



def _planner_safe_bool(value: Any) -> bool:
    return bool(value) and value not in ("", [], {}, None)


def _planner_artifact_types(artifact_registry: dict[str, Any] | None) -> set[str]:
    registry = artifact_registry if isinstance(artifact_registry, dict) else {}
    artifacts = registry.get("artifacts") if isinstance(registry.get("artifacts"), list) else []
    return {
        str(item.get("artifact_type") or "")
        for item in artifacts
        if isinstance(item, dict) and item.get("artifact_type")
    }


def _planner_latest_experiments(job: dict[str, Any]) -> list[dict[str, Any]]:
    experiments = job.get("external_video_experiments")
    if isinstance(experiments, list):
        return [item for item in experiments if isinstance(item, dict)]
    experiments = job.get("external_experiments")
    if isinstance(experiments, list):
        return [item for item in experiments if isinstance(item, dict)]
    return []


def _planner_gate_status(source_quality_gate: dict[str, Any]) -> str:
    return str(source_quality_gate.get("status") or "").strip().lower()


def _planner_source_review_count(source: dict[str, Any], evidence_artifact: dict[str, Any]) -> int:
    summary = source.get("source_summary") if isinstance(source.get("source_summary"), dict) else {}
    for key in ("unique_review_count", "review_count"):
        try:
            value = int(summary.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    snippets = evidence_artifact.get("review_snippets")
    if isinstance(snippets, list):
        return len([item for item in snippets if str(item or "").strip()])
    quotes = evidence_artifact.get("evidence_quotes")
    if isinstance(quotes, list):
        return len([item for item in quotes if str(item or "").strip()])
    return 0


def _planner_has_uploaded_asset(
    artifact_registry: dict[str, Any],
    source_evidence_artifact: dict[str, Any],
    latest_job: dict[str, Any],
) -> bool:
    registry = artifact_registry if isinstance(artifact_registry, dict) else {}
    artifacts = registry.get("artifacts") if isinstance(registry.get("artifacts"), list) else []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_type = str(artifact.get("artifact_type") or "")
        if artifact_type in {"uploaded_product_asset", "uploaded_reference_asset"}:
            return True
        if artifact_type == "product_asset_lock_v2":
            metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
            if metadata.get("primary_asset_id"):
                return True

    asset_refs = source_evidence_artifact.get("asset_refs")
    if isinstance(asset_refs, list) and asset_refs:
        return True

    lock_v2 = latest_job.get("product_asset_lock_v2")
    if isinstance(lock_v2, dict) and lock_v2.get("primary_asset_id"):
        return True

    return False


def _planner_registry_has(
    artifact_registry: dict[str, Any],
    artifact_type: str,
) -> bool:
    return artifact_type in _planner_artifact_types(artifact_registry)


def build_supervisor_planner_recommendation(
    project: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
    source_quality_gate: dict[str, Any] | None = None,
    source_evidence_artifact: dict[str, Any] | None = None,
    artifact_registry: dict[str, Any] | None = None,
    latest_run: dict[str, Any] | None = None,
    latest_job: dict[str, Any] | None = None,
    latest_experiment: dict[str, Any] | None = None,
    approval_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic project-level next-best-action recommendation.

    Supervisor / Planner Agent v2 is project-level planning. It does not replace
    Graph Router Agent, does not call external APIs, and does not enable LLM
    autonomous decisions.
    """

    safe_project = project if isinstance(project, dict) else {}
    safe_source = source if isinstance(source, dict) else {}
    safe_gate = source_quality_gate if isinstance(source_quality_gate, dict) else {}
    safe_evidence = source_evidence_artifact if isinstance(source_evidence_artifact, dict) else {}
    safe_registry = artifact_registry if isinstance(artifact_registry, dict) else {}
    safe_run = latest_run if isinstance(latest_run, dict) else {}
    safe_job = latest_job if isinstance(latest_job, dict) else {}
    safe_experiment = latest_experiment if isinstance(latest_experiment, dict) else {}
    safe_approval = approval_gate if isinstance(approval_gate, dict) else {}

    project_id = str(
        safe_project.get("project_id")
        or safe_source.get("project_id")
        or safe_gate.get("project_id")
        or safe_evidence.get("project_id")
        or safe_registry.get("project_id")
        or safe_run.get("project_id")
        or safe_job.get("project_id")
        or "demo_project_default"
    )

    source_type = str(safe_source.get("source_type") or "").strip()
    gate_status = _planner_gate_status(safe_gate)
    gate_allows_agent_run = safe_gate.get("allows_agent_run") is True
    evidence_readiness = str(safe_gate.get("evidence_readiness") or "").strip()
    source_confidence = safe_source.get("source_confidence")
    if source_confidence is None:
        source_confidence = safe_evidence.get("source_confidence")
    try:
        source_confidence_value = float(source_confidence or 0)
    except (TypeError, ValueError):
        source_confidence_value = 0.0

    review_count = _planner_source_review_count(safe_source, safe_evidence)
    source_warnings = list(safe_source.get("warnings") or []) + list(safe_gate.get("warnings") or []) + list(safe_evidence.get("warnings") or [])
    source_missing = not safe_source and not safe_evidence
    source_ready = bool(safe_evidence) and gate_status in {"passed", "warning"} and (
        gate_allows_agent_run or review_count > 0
    )
    source_needs_reviews = (
        source_type in {"amazon_url", "shopify_url"}
        and review_count <= 0
        and (
            gate_status in {"warning", "fallback_required", "partial", ""}
            or "manual_reviews_recommended" in source_warnings
        )
    )
    source_blocked = gate_status in {"blocked", "failed"} or safe_gate.get("allows_agent_run") is False and gate_status == "blocked"

    has_uploaded_asset = _planner_has_uploaded_asset(safe_registry, safe_evidence, safe_job)
    run_completed = str(safe_run.get("status") or "").lower() == "completed"
    has_generation_packet = _planner_registry_has(safe_registry, "video_generation_packet") or bool(
        safe_run.get("result", {}).get("video_generation_packet")
        if isinstance(safe_run.get("result"), dict)
        else False
    )
    has_handoff = _planner_registry_has(safe_registry, "external_video_tool_handoff") or bool(
        safe_run.get("result", {}).get("external_video_tool_handoff")
        if isinstance(safe_run.get("result"), dict)
        else False
    )
    has_job = bool(safe_job.get("job_id"))
    experiments = _planner_latest_experiments(safe_job)
    if safe_experiment:
        experiments.append(safe_experiment)
    experiment_count = len(experiments)

    has_revised_artifact = bool(
        safe_job.get("latest_rework_artifact_type")
        or safe_job.get("latest_rework_next_artifact_type")
        or _planner_registry_has(safe_registry, "revised_keyframe_plan")
        or _planner_registry_has(safe_registry, "revised_external_video_handoff")
    )
    comparison_gate = safe_job.get("latest_experiment_comparison_decision_gate")
    if not isinstance(comparison_gate, dict):
        comparison_gate = safe_job.get("experiment_comparison_decision_gate")
    comparison_gate = comparison_gate if isinstance(comparison_gate, dict) else {}
    gate_decision_type = str(comparison_gate.get("decision_type") or "").strip()

    approval = safe_approval
    if not approval and isinstance(safe_job.get("latest_human_approval_gate"), dict):
        approval = safe_job.get("latest_human_approval_gate")
    approval = approval if isinstance(approval, dict) else {}
    approval_status = str(approval.get("status") or "").strip().lower()
    provider_runtime = safe_job.get("provider_runtime") if isinstance(safe_job.get("provider_runtime"), dict) else {}
    provider_status = str(provider_runtime.get("provider_status") or safe_job.get("provider_status") or safe_job.get("status") or "").strip().lower()
    provider_ready_result = provider_status in {"external_result_ready", "manual_export_completed", "provider_result_ready"} or _planner_registry_has(safe_registry, "provider_result")

    overall_status = "needs_source"
    next_action_type = "add_source"
    next_agent_id = "source_adapter_agent"
    next_best_action = "Add a product source or paste customer feedback."
    user_action_required = True
    can_start_agent_run = False
    can_create_video_job = False
    can_record_experiment = False
    can_request_approval = False
    can_submit_provider = False
    missing_inputs: list[str] = []
    warnings: list[str] = []
    reasons: list[str] = []

    if source_missing:
        missing_inputs.append("project_source")
        reasons.append("No project source or source evidence artifact is available yet.")
    elif source_blocked:
        overall_status = "blocked"
        next_action_type = "review_blocker"
        next_agent_id = "source_quality_agent"
        next_best_action = "Review the blocker and provide the missing input or decision."
        user_action_required = True
        missing_inputs.append("valid_source_evidence")
        warnings.extend(source_warnings or ["source_quality_gate_blocked"])
        reasons.append("Source Quality Gate is blocked.")
    elif source_needs_reviews:
        overall_status = "needs_reviews"
        next_action_type = "paste_reviews"
        next_agent_id = "source_quality_agent"
        next_best_action = "Paste customer reviews before starting review-grounded generation."
        user_action_required = True
        missing_inputs.append("customer_reviews")
        warnings.extend(source_warnings or ["manual_reviews_recommended"])
        reasons.append("Public source does not provide enough usable customer-review evidence.")
    elif provider_ready_result:
        overall_status = "completed"
        next_action_type = "export_report"
        next_agent_id = "finalizer_agent"
        next_best_action = "Export the graph report or start another iteration."
        user_action_required = False
        reasons.append("Provider result is ready and graph report can be exported.")
    elif approval_status == "approved":
        overall_status = "provider_ready"
        next_action_type = "submit_provider_simulation"
        next_agent_id = "provider_job_agent"
        next_best_action = "Submit simulated provider job."
        user_action_required = True
        can_submit_provider = True
        reasons.append("Human Approval Gate approved the controlled manual/provider test.")
    elif approval_status in {"pending_approval", "pending"} or approval.get("blocks_provider_submit") is True:
        overall_status = "waiting_for_approval"
        next_action_type = "approve_controlled_test"
        next_agent_id = "human_approval_agent"
        next_best_action = "Approve controlled test or request changes before provider submit."
        user_action_required = True
        can_request_approval = True
        reasons.append("Provider submit is blocked until Human Approval Gate is decided.")
    elif gate_decision_type == "proceed_to_controlled_test":
        overall_status = "waiting_for_approval"
        next_action_type = "approve_controlled_test"
        next_agent_id = "human_approval_agent"
        next_best_action = "Review the controlled provider checklist and approve or request changes."
        user_action_required = True
        can_request_approval = True
        reasons.append("Second experiment improved and the decision gate selected a controlled provider test.")
    elif experiment_count >= 1 and has_revised_artifact:
        overall_status = "needs_rework"
        next_action_type = "use_revised_handoff"
        next_agent_id = "prompt_handoff_agent"
        next_best_action = "Use the revised external video handoff for a second experiment."
        user_action_required = True
        reasons.append("Experiment feedback produced revised artifacts for another test.")
    elif has_job and experiment_count <= 0:
        overall_status = "waiting_for_experiment"
        next_action_type = "record_experiment"
        next_agent_id = "experiment_agent"
        next_best_action = "Generate video manually in the external tool, then record experiment results."
        user_action_required = True
        can_record_experiment = True
        reasons.append("Video Job exists but no external experiment has been recorded.")
    elif run_completed and has_generation_packet and has_handoff and not has_job:
        overall_status = "ready_for_video_job"
        next_action_type = "create_video_job"
        next_agent_id = "provider_job_agent"
        next_best_action = "Create a Video Job from the handoff."
        user_action_required = False
        can_create_video_job = True
        reasons.append("Agent Run completed and produced a video handoff.")
    elif source_ready and has_uploaded_asset:
        overall_status = "ready_for_agent_run"
        next_action_type = "start_agent_run"
        next_agent_id = "planner_agent"
        next_best_action = "Start Agent Run."
        user_action_required = False
        can_start_agent_run = True
        reasons.append("Source evidence and product identity assets are ready.")
    elif source_ready:
        overall_status = "asset_recommended"
        next_action_type = "upload_asset"
        next_agent_id = "asset_lock_agent"
        next_best_action = "You can start the Agent Run, but uploading a product image is recommended for product consistency."
        user_action_required = False
        can_start_agent_run = True
        missing_inputs.append("product_image_recommended")
        reasons.append("Source evidence is ready, but product image upload would improve product consistency.")
    else:
        overall_status = "needs_source"
        next_action_type = "add_source"
        next_agent_id = "source_adapter_agent"
        next_best_action = "Add a product source or paste customer feedback."
        user_action_required = True
        missing_inputs.append("usable_source_evidence")
        warnings.extend(source_warnings)
        reasons.append("Project does not yet have enough source evidence for planning.")

    return {
        "planner_version": "supervisor_planner_v2",
        "project_id": project_id,
        "overall_status": overall_status,
        "next_best_action": next_best_action,
        "next_action_type": next_action_type,
        "next_agent_id": next_agent_id,
        "user_action_required": user_action_required,
        "can_start_agent_run": can_start_agent_run,
        "can_create_video_job": can_create_video_job,
        "can_record_experiment": can_record_experiment,
        "can_request_approval": can_request_approval,
        "can_submit_provider": can_submit_provider,
        "missing_inputs": list(dict.fromkeys([item for item in missing_inputs if item])),
        "warnings": list(dict.fromkeys([str(item) for item in warnings if str(item or "")])),
        "reasons": list(dict.fromkeys([item for item in reasons if item])),
        "evidence": {
            "source_quality_gate_status": gate_status,
            "source_confidence": source_confidence_value,
            "artifact_registry_version": str(safe_registry.get("registry_version") or ""),
            "latest_run_id": safe_run.get("run_id"),
            "latest_job_id": safe_job.get("job_id"),
            "latest_experiment_status": (
                safe_experiment.get("status")
                or (experiments[-1].get("status") if experiments else None)
            ),
            "review_count": review_count,
            "approval_status": approval_status,
            "provider_status": provider_status,
        },
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
        },
    }

def build_graph_router_decision(
    route_context: dict[str, Any],
    job: dict[str, Any] | None = None,
    run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select a deterministic next graph route without executing it."""

    context = route_context if isinstance(route_context, dict) else {}
    context_type = str(context.get("route_context_type") or "").strip()
    validation_status = str(context.get("validation_status") or context.get("status") or "").strip().lower()
    issue_type = str(context.get("issue_type") or "").strip().lower()
    comparison_status = str(context.get("comparison_status") or context.get("status") or "").strip().lower()
    gate_decision_type = str(context.get("gate_decision_type") or context.get("decision_type") or "").strip()
    score_deltas = context.get("score_deltas")
    score_deltas = deepcopy(score_deltas) if isinstance(score_deltas, dict) else {}
    artifact_types = context.get("artifact_types")
    artifact_types = list(artifact_types) if isinstance(artifact_types, list) else []
    reason = str(context.get("reason") or "").strip()

    selected = {
        "from_agent_id": str(context.get("from_agent_id") or "graph_router_agent"),
        "selected_next_agent_id": "finalizer_agent",
        "secondary_next_agent_id": "",
        "route_type": "stop",
        "decision_type": "route_to_final_summary",
        "reason": reason or "No supported graph branch matched; route to the final summary.",
        "confidence": 0.7,
        "should_continue_graph": False,
        "should_trigger_rework": False,
        "should_request_human_approval": False,
        "should_proceed_to_provider_test": False,
        "should_stop": True,
        "edge_type": "normal",
    }

    if context_type == "risk_validation" and validation_status in {"failed", "warning", "risky", "risk_detected"}:
        selected.update(
            {
                "from_agent_id": "risk_agent",
                "selected_next_agent_id": "storyboard_agent",
                "route_type": "rework",
                "decision_type": "route_to_storyboard_rework",
                "reason": reason or "Risk validation found unsupported or risky storyboard wording.",
                "confidence": 0.95,
                "should_continue_graph": True,
                "should_trigger_rework": True,
                "should_stop": False,
                "edge_type": "rework",
            }
        )
    elif context_type == "experiment_feedback":
        feedback_routes = {
            "product_consistency": (
                "keyframe_agent",
                "asset_lock_agent",
                "route_to_keyframe_asset_lock_rework",
                "Product consistency feedback requires tighter keyframes and product identity locks.",
            ),
            "storyboard_following": (
                "prompt_handoff_agent",
                "keyframe_agent",
                "route_to_prompt_keyframe_rework",
                "Storyboard-following feedback requires revised prompt handoff and keyframe constraints.",
            ),
            "ad_readiness": (
                "storyboard_agent",
                "strategy_agent",
                "route_to_storyboard_strategy_rework",
                "Ad-readiness feedback requires a stronger storyboard and creative strategy.",
            ),
            "visual_quality": (
                "prompt_handoff_agent",
                "",
                "route_to_prompt_handoff_rework",
                "Visual-quality feedback requires tighter external prompt constraints.",
            ),
            "cost_value": (
                "cost_agent",
                "route_selector_agent",
                "route_to_cost_route_selector_review",
                "Cost/value feedback requires cost review and safe route selection.",
            ),
            "overall_quality": (
                "prompt_handoff_agent",
                "",
                "route_to_prompt_handoff_rework",
                "Low overall quality requires tighter prompt handoff constraints.",
            ),
        }
        route = feedback_routes.get(issue_type)
        if route:
            selected.update(
                {
                    "from_agent_id": "experiment_agent",
                    "selected_next_agent_id": route[0],
                    "secondary_next_agent_id": route[1],
                    "route_type": "rework",
                    "decision_type": route[2],
                    "reason": reason or route[3],
                    "confidence": 0.92 if issue_type == "product_consistency" else 0.88,
                    "should_continue_graph": True,
                    "should_trigger_rework": True,
                    "should_stop": False,
                    "edge_type": "rework",
                }
            )
    elif context_type == "revised_keyframe_created":
        selected.update(
            {
                "from_agent_id": "keyframe_agent",
                "selected_next_agent_id": "prompt_handoff_agent",
                "route_type": "handoff",
                "decision_type": "route_to_prompt_handoff",
                "reason": reason or "The revised keyframe plan is ready for external prompt handoff.",
                "confidence": 0.96,
                "should_continue_graph": True,
                "should_stop": False,
                "edge_type": "normal",
            }
        )
    elif context_type == "second_experiment_comparison":
        comparison_routes = {
            "improved": {
                "next": "provider_job_agent",
                "secondary": "experiment_agent",
                "route_type": "decision_gate",
                "decision_type": "route_to_provider_controlled_test",
                "reason": "The second experiment improved enough to open a controlled provider/manual test gate.",
                "rework": False,
                "approval": True,
                "provider": True,
                "edge_type": "gate",
                "confidence": 0.9,
            },
            "regressed": {
                "next": "prompt_handoff_agent",
                "secondary": "keyframe_agent",
                "route_type": "rework",
                "decision_type": "route_to_prompt_keyframe_retry",
                "reason": "The second experiment regressed and should return to prompt and keyframe rework.",
                "rework": True,
                "approval": False,
                "provider": False,
                "edge_type": "rework",
                "confidence": 0.92,
            },
            "mixed": {
                "next": "experiment_agent",
                "secondary": "prompt_handoff_agent",
                "route_type": "human_approval",
                "decision_type": "route_to_manual_review",
                "reason": "Mixed score movement requires human review before choosing another route.",
                "rework": False,
                "approval": True,
                "provider": False,
                "edge_type": "human_approval",
                "confidence": 0.72,
            },
            "no_change": {
                "next": "asset_lock_agent",
                "secondary": "keyframe_agent",
                "route_type": "rework",
                "decision_type": "route_to_stronger_reference_keyframe_rework",
                "reason": "No meaningful improvement requires a stronger reference and revised keyframes.",
                "rework": True,
                "approval": False,
                "provider": False,
                "edge_type": "rework",
                "confidence": 0.8,
            },
        }
        route = comparison_routes.get(comparison_status)
        if route:
            selected.update(
                {
                    "from_agent_id": "experiment_agent",
                    "selected_next_agent_id": route["next"],
                    "secondary_next_agent_id": route["secondary"],
                    "route_type": route["route_type"],
                    "decision_type": route["decision_type"],
                    "reason": reason or route["reason"],
                    "confidence": route["confidence"],
                    "should_continue_graph": True,
                    "should_trigger_rework": route["rework"],
                    "should_request_human_approval": route["approval"],
                    "should_proceed_to_provider_test": route["provider"],
                    "should_stop": False,
                    "edge_type": route["edge_type"],
                }
            )
    elif context_type == "experiment_comparison_decision_gate":
        gate_routes = {
            "proceed_to_controlled_test": (
                "provider_job_agent",
                "experiment_agent",
                "decision_gate",
                "route_to_provider_controlled_test",
                False,
                True,
                True,
                "gate",
            ),
            "retry_rework": (
                "prompt_handoff_agent",
                "keyframe_agent",
                "rework",
                "route_to_prompt_keyframe_retry",
                True,
                False,
                False,
                "rework",
            ),
            "manual_review_required": (
                "experiment_agent",
                "prompt_handoff_agent",
                "human_approval",
                "route_to_manual_review",
                False,
                True,
                False,
                "human_approval",
            ),
            "stop_or_revise_reference": (
                "asset_lock_agent",
                "keyframe_agent",
                "rework",
                "route_to_stronger_reference_keyframe_rework",
                True,
                False,
                False,
                "rework",
            ),
        }
        route = gate_routes.get(gate_decision_type)
        if route:
            selected.update(
                {
                    "from_agent_id": "experiment_agent",
                    "selected_next_agent_id": route[0],
                    "secondary_next_agent_id": route[1],
                    "route_type": route[2],
                    "decision_type": route[3],
                    "reason": reason or "The experiment comparison decision gate selected the next safe graph route.",
                    "confidence": float(context.get("confidence") or 0.86),
                    "should_continue_graph": True,
                    "should_trigger_rework": route[4],
                    "should_request_human_approval": route[5],
                    "should_proceed_to_provider_test": route[6],
                    "should_stop": False,
                    "edge_type": route[7],
                }
            )
    elif context_type == "controlled_provider_checklist":
        selected.update(
            {
                "from_agent_id": "provider_job_agent",
                "selected_next_agent_id": "human_approval_agent",
                "route_type": "human_approval",
                "decision_type": "route_to_human_approval_before_provider",
                "reason": reason or "Controlled provider/manual handoff requires explicit human approval before paid generation.",
                "confidence": 0.99,
                "should_continue_graph": True,
                "should_request_human_approval": True,
                "should_proceed_to_provider_test": False,
                "should_stop": False,
                "edge_type": "human_approval",
            }
        )

    selected_edge = {
        "from_node_id": selected["from_agent_id"],
        "to_node_id": selected["selected_next_agent_id"],
        "edge_type": selected.pop("edge_type"),
    }
    input_signal = str(
        context.get("input_signal")
        or issue_type
        or comparison_status
        or gate_decision_type
        or validation_status
        or "no_supported_route"
    )
    return {
        "router_version": "graph_router_agent_v1",
        "source_agent_id": "graph_router_agent",
        "route_context_type": context_type or "fallback",
        "input_signal": input_signal,
        **selected,
        "selected_edge": selected_edge,
        "evidence": {
            "score_deltas": score_deltas,
            "validation_status": validation_status,
            "issue_type": issue_type,
            "comparison_status": comparison_status,
            "gate_decision_type": gate_decision_type,
            "artifact_types": artifact_types,
        },
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "requires_human_approval_before_paid_generation": True,
        },
    }


def append_graph_router_decision(
    container: dict[str, Any],
    router_decision: dict[str, Any],
) -> dict[str, Any]:
    """Append a router decision and refresh compact non-linear graph counts."""

    target = container if isinstance(container, dict) else {}
    decision = router_decision if isinstance(router_decision, dict) else {}
    if not decision:
        return target
    decisions = list(target.get("graph_router_decisions") or [])
    decisions.append(deepcopy(decision))
    decisions = decisions[-20:]
    target["graph_router_decisions"] = decisions
    target["latest_graph_router_decision"] = deepcopy(decisions[-1])
    target["graph_router_summary"] = {
        "router_version": "graph_router_agent_v1",
        "decision_count": len(decisions),
        "has_rework_route": any(item.get("should_trigger_rework") is True for item in decisions),
        "has_provider_route": any(item.get("should_proceed_to_provider_test") is True for item in decisions),
        "has_human_approval_route": any(item.get("should_request_human_approval") is True for item in decisions),
        "has_stop_route": any(item.get("should_stop") is True for item in decisions),
        "is_linear_workflow": False,
    }
    return target


def build_second_experiment_comparison(
    baseline_experiment: dict[str, Any],
    second_experiment: dict[str, Any],
    feedback_decision: dict[str, Any] | None = None,
    rework_run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare a second external result against the experiment that triggered rework."""

    baseline = baseline_experiment if isinstance(baseline_experiment, dict) else {}
    second = second_experiment if isinstance(second_experiment, dict) else {}
    decision = feedback_decision if isinstance(feedback_decision, dict) else {}
    run = rework_run if isinstance(rework_run, dict) else {}
    score_fields = [
        "product_consistency_score",
        "storyboard_following_score",
        "visual_quality_score",
        "ad_readiness_score",
        "overall_score",
    ]
    score_deltas: dict[str, float] = {}
    improved_dimensions: list[str] = []
    regressed_dimensions: list[str] = []
    unchanged_dimensions: list[str] = []
    for field_name in score_fields:
        baseline_score = _numeric_experiment_score(baseline.get(field_name))
        second_score = _numeric_experiment_score(second.get(field_name))
        if baseline_score is None or second_score is None:
            continue
        delta = second_score - baseline_score
        score_deltas[field_name] = int(delta) if float(delta).is_integer() else round(delta, 2)
        if delta > 0:
            improved_dimensions.append(field_name)
        elif delta < 0:
            regressed_dimensions.append(field_name)
        else:
            unchanged_dimensions.append(field_name)

    primary_metric = "product_consistency_score"
    primary_delta = _numeric_experiment_score(score_deltas.get(primary_metric))
    overall_delta = _numeric_experiment_score(score_deltas.get("overall_score"))

    if primary_delta is not None and primary_delta < 0:
        status = "regressed"
    elif overall_delta is not None and overall_delta <= -2:
        status = "regressed"
    elif primary_delta is not None and primary_delta >= 2 and (overall_delta is None or overall_delta >= 0):
        status = "improved"
    elif improved_dimensions and regressed_dimensions:
        status = "mixed"
    elif not score_deltas or all(_numeric_experiment_score(value) == 0 for value in score_deltas.values()):
        status = "no_change"
    else:
        status = "mixed"

    recommendations = {
        "improved": "Use the revised prompt handoff for another short clip or proceed to a controlled provider/manual handoff test.",
        "regressed": "Do not scale this prompt. Return to Keyframe Agent or Prompt Handoff Agent for another revision.",
        "mixed": "Review dimensions manually before another rework. Keep improvements but fix regressed dimensions.",
        "no_change": "Try a stronger product identity reference or revise the keyframe plan again.",
    }
    reasons = {
        "improved": "The primary product consistency score improved by at least two points and overall score did not regress.",
        "regressed": "The primary product consistency score or overall score regressed enough to block scale-up.",
        "mixed": "The second result improved in some dimensions and regressed or moved only partially in others.",
        "no_change": "The second result did not show a meaningful score movement from the baseline.",
    }

    linked_rework_run_id = (
        str(second.get("linked_rework_run_id") or "").strip()
        or str(decision.get("triggered_rework_run_id") or "").strip()
        or str(run.get("run_id") or "").strip()
    )
    prompt_source = str(second.get("prompt_source") or "").strip()
    if not prompt_source and (run.get("result") or {}).get("revised_external_video_handoff"):
        prompt_source = "revised_external_video_handoff"

    return {
        "comparison_version": "second_external_experiment_comparison_v1",
        "source_agent_id": "experiment_agent",
        "baseline_experiment_id": str(baseline.get("experiment_id") or ""),
        "second_experiment_id": str(second.get("experiment_id") or ""),
        "linked_rework_run_id": linked_rework_run_id,
        "prompt_source": prompt_source,
        "status": status,
        "primary_metric": primary_metric,
        "score_deltas": score_deltas,
        "improved_dimensions": improved_dimensions,
        "regressed_dimensions": regressed_dimensions,
        "unchanged_dimensions": unchanged_dimensions,
        "decision_type": f"second_experiment_{status}",
        "reason": reasons[status],
        "recommended_next_action": recommendations[status],
        "human_review_required": True,
    }


def build_experiment_comparison_decision_gate(
    comparison: dict[str, Any],
    job: dict[str, Any] | None = None,
    baseline_experiment: dict[str, Any] | None = None,
    second_experiment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic business-action gate from a second experiment comparison."""

    safe_comparison = comparison if isinstance(comparison, dict) else {}
    status = str(safe_comparison.get("status") or "no_change").strip().lower()
    if status not in {"improved", "regressed", "mixed", "no_change"}:
        status = "no_change"

    routes = {
        "improved": {
            "decision_type": "proceed_to_controlled_test",
            "recommended_route": "controlled_provider_or_manual_handoff",
            "next_agent_id": "provider_job_agent",
            "secondary_next_agent_id": "experiment_agent",
            "reason": "The revised prompt improved the primary metric and did not regress overall.",
            "recommended_next_action": "Run one controlled manual/provider test using the revised handoff before scaling.",
            "should_trigger_new_rework": False,
            "should_proceed_to_provider_test": True,
        },
        "regressed": {
            "decision_type": "retry_rework",
            "recommended_route": "keyframe_or_prompt_rework",
            "next_agent_id": "prompt_handoff_agent",
            "secondary_next_agent_id": "keyframe_agent",
            "reason": "The second test regressed, so do not scale this prompt.",
            "recommended_next_action": "Return to Prompt Handoff Agent or Keyframe Agent for another revision.",
            "should_trigger_new_rework": True,
            "should_proceed_to_provider_test": False,
        },
        "mixed": {
            "decision_type": "manual_review_required",
            "recommended_route": "manual_review",
            "next_agent_id": "experiment_agent",
            "secondary_next_agent_id": "prompt_handoff_agent",
            "reason": "Some dimensions improved but others regressed.",
            "recommended_next_action": "Manually review score tradeoffs before another rework.",
            "should_trigger_new_rework": False,
            "should_proceed_to_provider_test": False,
        },
        "no_change": {
            "decision_type": "stop_or_revise_reference",
            "recommended_route": "stronger_reference_required",
            "next_agent_id": "asset_lock_agent",
            "secondary_next_agent_id": "keyframe_agent",
            "reason": "The second test did not meaningfully improve.",
            "recommended_next_action": "Add stronger product reference or revise the keyframe plan again.",
            "should_trigger_new_rework": True,
            "should_proceed_to_provider_test": False,
        },
    }
    selected = routes[status]
    score_deltas = safe_comparison.get("score_deltas")
    score_deltas = score_deltas if isinstance(score_deltas, dict) else {}
    primary_metric = str(safe_comparison.get("primary_metric") or "product_consistency_score")
    primary_delta = _numeric_experiment_score(score_deltas.get(primary_metric))
    overall_delta = _numeric_experiment_score(score_deltas.get("overall_score"))

    confidence = {
        "improved": 0.82 if (primary_delta or 0) >= 2 and (overall_delta or 0) >= 1 else 0.76,
        "regressed": 0.86,
        "mixed": 0.64,
        "no_change": 0.72,
    }[status]

    return {
        "gate_version": "experiment_comparison_decision_gate_v1",
        "source_agent_id": "experiment_agent",
        "comparison_status": status,
        "decision_type": selected["decision_type"],
        "recommended_route": selected["recommended_route"],
        "next_agent_id": selected["next_agent_id"],
        "secondary_next_agent_id": selected["secondary_next_agent_id"],
        "reason": selected["reason"],
        "recommended_next_action": selected["recommended_next_action"],
        "confidence": confidence,
        "requires_human_approval": True,
        "should_trigger_new_rework": selected["should_trigger_new_rework"],
        "should_proceed_to_provider_test": selected["should_proceed_to_provider_test"],
        "score_summary": {
            "primary_metric": primary_metric,
            "primary_delta": primary_delta,
            "overall_delta": overall_delta,
            "improved_dimensions": list(safe_comparison.get("improved_dimensions") or []),
            "regressed_dimensions": list(safe_comparison.get("regressed_dimensions") or []),
        },
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
        },
    }


def _experiment_rework_edge_id(target_agent_id: str) -> str:
    return {
        "keyframe_agent": "experiment_to_keyframe_rework",
        "prompt_handoff_agent": "experiment_to_prompt_handoff_rework",
        "storyboard_agent": "experiment_to_storyboard_rework",
        "cost_agent": "experiment_to_cost_rework",
    }.get(str(target_agent_id or ""), "experiment_to_keyframe_rework")


def _experiment_rework_text(value: Any, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _experiment_rework_list(values: Any, limit: int = 6, text_limit: int = 220) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _experiment_rework_text(value, limit=text_limit)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def _experiment_rework_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _stable_graph_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _graph_safety_boundaries() -> dict[str, bool]:
    return {
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
    }


AGENT_CONTRACT_REGISTRY_VERSION = "agent_contract_registry_v1"


def build_agent_contract_registry() -> dict[str, Any]:
    """Build deterministic role/input/output contracts for graph agents.

    The registry is intentionally rule-driven. It describes how agents are
    allowed to hand off work without enabling autonomous LLM decisions.
    """

    contracts = [
        {
            "agent_id": "source_adapter_agent",
            "display_name": "Source Adapter Agent",
            "stage": "source_intake",
            "role": "Normalize product links, pasted reviews, or user-provided source inputs into project source records.",
            "input_contract": ["project_id", "source_type", "raw_source_payload"],
            "output_contract": ["project_source", "source_summary", "source_confidence"],
            "handoff_artifact_types": ["project_source", "source_snapshot"],
            "allowed_next_agent_ids": ["source_quality_agent", "planner_agent"],
            "failure_outputs": ["low_source_confidence", "source_unavailable", "source_parse_failed"],
        },
        {
            "agent_id": "source_quality_agent",
            "display_name": "Source Quality Agent",
            "stage": "source_quality",
            "role": "Check whether source evidence is strong enough for grounded generation.",
            "input_contract": ["project_source", "source_summary", "source_confidence"],
            "output_contract": ["source_quality_gate", "source_evidence_artifact"],
            "handoff_artifact_types": ["source_quality_gate", "source_evidence_artifact"],
            "allowed_next_agent_ids": ["planner_agent", "evidence_agent", "source_adapter_agent"],
            "failure_outputs": ["needs_reviews", "source_quality_gate_blocked", "manual_reviews_recommended"],
        },
        {
            "agent_id": "evidence_agent",
            "display_name": "Evidence Agent",
            "stage": "evidence",
            "role": "Extract review-backed evidence, objections, user language, and source-grounded signals.",
            "input_contract": ["source_evidence_artifact", "project_source"],
            "output_contract": ["evidence_quotes", "customer_feedback_signals", "positive_signals"],
            "handoff_artifact_types": ["evidence_brief", "source_evidence_artifact"],
            "allowed_next_agent_ids": ["strategy_agent", "planner_agent"],
            "failure_outputs": ["no_evidence_alignment", "insufficient_evidence_quotes"],
        },
        {
            "agent_id": "planner_agent",
            "display_name": "Supervisor Planner Agent",
            "stage": "planning",
            "role": "Recommend the next best project action from source, run, job, artifact, approval, and provider state.",
            "input_contract": ["project_state", "source_quality_gate", "artifact_registry", "latest_run", "latest_job"],
            "output_contract": ["supervisor_planner_recommendation", "next_best_action", "next_agent_id"],
            "handoff_artifact_types": ["supervisor_planner_recommendation"],
            "allowed_next_agent_ids": ["source_adapter_agent", "source_quality_agent", "asset_lock_agent", "strategy_agent", "planner_agent", "prompt_handoff_agent", "provider_job_agent", "experiment_agent", "human_approval_agent", "finalizer_agent"],
            "failure_outputs": ["needs_source", "blocked", "waiting_for_approval"],
        },
        {
            "agent_id": "asset_lock_agent",
            "display_name": "Asset Lock Agent",
            "stage": "identity_lock",
            "role": "Lock product identity, uploaded asset references, and visual consistency constraints.",
            "input_contract": ["project", "generation_data", "uploaded_assets"],
            "output_contract": ["product_asset_lock_v2", "identity_constraints"],
            "handoff_artifact_types": ["product_asset_lock_v2", "uploaded_product_asset"],
            "allowed_next_agent_ids": ["keyframe_agent", "storyboard_agent", "planner_agent"],
            "failure_outputs": ["missing_product_identity", "asset_recommended"],
        },
        {
            "agent_id": "strategy_agent",
            "display_name": "Creative Strategy Agent",
            "stage": "creative_strategy",
            "role": "Convert source evidence into hook strategy, audience angle, CTA logic, and buyer-objection framing.",
            "input_contract": ["evidence_brief", "source_evidence_artifact", "project_context"],
            "output_contract": ["creative_strategy", "hook_candidates", "cta_logic"],
            "handoff_artifact_types": ["creative_strategy"],
            "allowed_next_agent_ids": ["storyboard_agent", "risk_agent"],
            "failure_outputs": ["weak_hook", "no_evidence_alignment", "reward_hacking"],
        },
        {
            "agent_id": "storyboard_agent",
            "display_name": "Storyboard Agent",
            "stage": "storyboard",
            "role": "Generate or revise scene sequence, narration, overlays, and evidence-linked visual direction.",
            "input_contract": ["creative_strategy", "evidence_brief", "product_asset_lock_v2"],
            "output_contract": ["storyboard", "video_generation_packet"],
            "handoff_artifact_types": ["storyboard", "video_generation_packet"],
            "allowed_next_agent_ids": ["risk_agent", "keyframe_agent", "prompt_handoff_agent"],
            "failure_outputs": ["weak_visual", "risky_storyboard", "no_evidence_alignment"],
        },
        {
            "agent_id": "risk_agent",
            "display_name": "Risk Agent",
            "stage": "quality_safety",
            "role": "Detect unsupported claims, risky wording, and evidence-safety issues before handoff.",
            "input_contract": ["storyboard", "video_generation_packet", "evaluation"],
            "output_contract": ["risk_validation", "storyboard_rework_request"],
            "handoff_artifact_types": ["risk_validation", "storyboard_rework_summary"],
            "allowed_next_agent_ids": ["storyboard_agent", "graph_router_agent", "finalizer_agent"],
            "failure_outputs": ["reward_hacking", "unsupported_claim", "high_risk"],
        },
        {
            "agent_id": "keyframe_agent",
            "display_name": "Keyframe Agent",
            "stage": "visual_planning",
            "role": "Turn storyboard scenes and asset locks into keyframe-level visual constraints.",
            "input_contract": ["storyboard", "product_asset_lock_v2", "experiment_feedback"],
            "output_contract": ["keyframe_plan", "revised_keyframe_plan"],
            "handoff_artifact_types": ["keyframe_plan", "revised_keyframe_plan"],
            "allowed_next_agent_ids": ["prompt_handoff_agent", "asset_lock_agent", "graph_router_agent"],
            "failure_outputs": ["product_consistency", "weak_visual", "missing_reference"],
        },
        {
            "agent_id": "prompt_handoff_agent",
            "display_name": "Prompt Handoff Agent",
            "stage": "external_handoff",
            "role": "Package keyframes, storyboard, and constraints into copy-ready external video tool prompts.",
            "input_contract": ["keyframe_plan", "storyboard", "product_asset_lock_v2"],
            "output_contract": ["external_video_tool_handoff", "revised_external_video_handoff"],
            "handoff_artifact_types": ["external_video_tool_handoff", "revised_external_video_handoff"],
            "allowed_next_agent_ids": ["provider_job_agent", "experiment_agent", "human_approval_agent"],
            "failure_outputs": ["prompt_handoff_incomplete", "visual_quality"],
        },
        {
            "agent_id": "provider_job_agent",
            "display_name": "Provider Job Agent",
            "stage": "provider_or_manual_test",
            "role": "Create controlled manual/provider video jobs after handoff and approval checks.",
            "input_contract": ["external_video_tool_handoff", "human_approval_gate"],
            "output_contract": ["video_job", "provider_runtime"],
            "handoff_artifact_types": ["video_job", "provider_runtime"],
            "allowed_next_agent_ids": ["human_approval_agent", "experiment_agent", "finalizer_agent"],
            "failure_outputs": ["waiting_for_approval", "provider_blocked", "provider_result_missing"],
        },
        {
            "agent_id": "human_approval_agent",
            "display_name": "Human Approval Agent",
            "stage": "approval_gate",
            "role": "Represent explicit human approval before provider submit, paid generation, or scale-up.",
            "input_contract": ["controlled_provider_checklist", "experiment_comparison_decision_gate"],
            "output_contract": ["human_approval_gate", "approval_status"],
            "handoff_artifact_types": ["human_approval_gate"],
            "allowed_next_agent_ids": ["provider_job_agent", "planner_agent", "finalizer_agent"],
            "failure_outputs": ["pending_approval", "approval_rejected", "changes_requested"],
        },
        {
            "agent_id": "experiment_agent",
            "display_name": "Experiment Agent",
            "stage": "feedback_loop",
            "role": "Record external/manual experiment results and decide whether graph rework is needed.",
            "input_contract": ["video_job", "external_result", "score_snapshot"],
            "output_contract": ["experiment_feedback_decision", "second_experiment_comparison"],
            "handoff_artifact_types": ["experiment_feedback_decision", "second_experiment_comparison"],
            "allowed_next_agent_ids": ["graph_router_agent", "keyframe_agent", "prompt_handoff_agent", "human_approval_agent"],
            "failure_outputs": ["product_consistency", "storyboard_following", "ad_readiness", "visual_quality", "cost_value"],
        },
        {
            "agent_id": "graph_router_agent",
            "display_name": "Graph Router Agent",
            "stage": "routing",
            "role": "Select the next deterministic graph route after risk validation, feedback, or comparison gates.",
            "input_contract": ["route_context", "latest_job", "latest_run"],
            "output_contract": ["graph_router_decision", "selected_edge"],
            "handoff_artifact_types": ["graph_router_decision"],
            "allowed_next_agent_ids": ["storyboard_agent", "keyframe_agent", "prompt_handoff_agent", "provider_job_agent", "human_approval_agent", "finalizer_agent"],
            "failure_outputs": ["no_supported_route", "manual_review_required"],
        },
        {
            "agent_id": "cost_agent",
            "display_name": "Cost Agent",
            "stage": "cost_review",
            "role": "Review cost/value feedback and prefer safe manual or low-cost routes.",
            "input_contract": ["experiment_feedback_decision", "score_snapshot"],
            "output_contract": ["cost_review", "route_cost_recommendation"],
            "handoff_artifact_types": ["cost_review"],
            "allowed_next_agent_ids": ["route_selector_agent", "planner_agent"],
            "failure_outputs": ["poor_cost_value", "manual_route_recommended"],
        },
        {
            "agent_id": "route_selector_agent",
            "display_name": "Route Selector Agent",
            "stage": "route_selection",
            "role": "Choose between rework, manual test, provider test, or stop routes based on deterministic gates.",
            "input_contract": ["cost_review", "planner_recommendation", "graph_router_decision"],
            "output_contract": ["route_selection_decision"],
            "handoff_artifact_types": ["route_selection_decision"],
            "allowed_next_agent_ids": ["planner_agent", "provider_job_agent", "finalizer_agent"],
            "failure_outputs": ["manual_review_required", "stop_or_revise_reference"],
        },
        {
            "agent_id": "finalizer_agent",
            "display_name": "Finalizer Agent",
            "stage": "final_report",
            "role": "Summarize graph state, export reports, and close the current workflow iteration.",
            "input_contract": ["artifact_registry", "graph_state_snapshot", "project_history"],
            "output_contract": ["run_report", "job_markdown_report", "project_workspace_export"],
            "handoff_artifact_types": ["run_report", "job_markdown_report", "project_workspace_export"],
            "allowed_next_agent_ids": ["planner_agent"],
            "failure_outputs": ["report_export_failed"],
        },
    ]

    contract_by_agent_id = {item["agent_id"]: deepcopy(item) for item in contracts}
    edge_catalog = []
    for item in contracts:
        for next_agent_id in item["allowed_next_agent_ids"]:
            edge_catalog.append(
                {
                    "from_agent_id": item["agent_id"],
                    "to_agent_id": next_agent_id,
                    "edge_id": f"{item['agent_id']}__to__{next_agent_id}",
                    "edge_type": "allowed_handoff",
                }
            )

    return {
        "registry_version": AGENT_CONTRACT_REGISTRY_VERSION,
        "graph_version": GRAPH_VERSION,
        "execution_mode": GRAPH_EXECUTION_MODE,
        "autonomy_level": AUTONOMY_LEVEL,
        "contract_count": len(contracts),
        "edge_count": len(edge_catalog),
        "contracts": contracts,
        "contract_by_agent_id": contract_by_agent_id,
        "edge_catalog": edge_catalog,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def get_agent_contract(agent_id: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_registry = registry if isinstance(registry, dict) else build_agent_contract_registry()
    by_id = safe_registry.get("contract_by_agent_id") if isinstance(safe_registry.get("contract_by_agent_id"), dict) else {}
    return deepcopy(by_id.get(str(agent_id or ""), {}))


def build_agent_contract_summary(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_registry = registry if isinstance(registry, dict) else build_agent_contract_registry()
    contracts = safe_registry.get("contracts") if isinstance(safe_registry.get("contracts"), list) else []
    stages: dict[str, int] = {}
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        stage = str(contract.get("stage") or "unknown")
        stages[stage] = stages.get(stage, 0) + 1

    return {
        "summary_version": "agent_contract_summary_v1",
        "registry_version": str(safe_registry.get("registry_version") or AGENT_CONTRACT_REGISTRY_VERSION),
        "agent_count": len(contracts),
        "edge_count": int(safe_registry.get("edge_count") or 0),
        "stages": stages,
        "autonomy_level": str(safe_registry.get("autonomy_level") or AUTONOMY_LEVEL),
        "execution_mode": str(safe_registry.get("execution_mode") or GRAPH_EXECUTION_MODE),
        "safety_boundaries": _graph_safety_boundaries(),
    }


def validate_agent_contract_handoff(
    source_agent_id: str,
    target_agent_id: str,
    artifact_types: list[str] | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_registry = registry if isinstance(registry, dict) else build_agent_contract_registry()
    source = get_agent_contract(source_agent_id, safe_registry)
    target = get_agent_contract(target_agent_id, safe_registry)
    safe_artifacts = [str(value) for value in (artifact_types or []) if str(value or "")]
    reasons: list[str] = []
    warnings: list[str] = []

    if not source:
        reasons.append("Unknown source agent contract.")
    if not target:
        reasons.append("Unknown target agent contract.")

    allowed_next = list(source.get("allowed_next_agent_ids") or []) if source else []
    if source and target and str(target_agent_id or "") not in allowed_next:
        reasons.append("Target agent is not in source agent allowed_next_agent_ids.")

    source_outputs = set(str(value) for value in (source.get("handoff_artifact_types") or []))
    if safe_artifacts:
        unsupported = [value for value in safe_artifacts if value not in source_outputs]
        if unsupported:
            warnings.append(f"Artifact types are not declared by source contract: {', '.join(unsupported)}.")

    return {
        "validation_version": "agent_contract_handoff_validation_v1",
        "registry_version": str(safe_registry.get("registry_version") or AGENT_CONTRACT_REGISTRY_VERSION),
        "valid": not reasons,
        "source_agent_id": str(source_agent_id or ""),
        "target_agent_id": str(target_agent_id or ""),
        "artifact_types": safe_artifacts,
        "allowed_next_agent_ids": allowed_next,
        "reasons": reasons,
        "warnings": warnings,
        "source_stage": str(source.get("stage") or ""),
        "target_stage": str(target.get("stage") or ""),
        "safety_boundaries": _graph_safety_boundaries(),
    }




def build_agent_message(
    message_type: str,
    source_agent_id: str,
    target_agent_id: str | None,
    payload: dict[str, Any],
    run_id: str | None = None,
    job_id: str | None = None,
    artifact_ids: list[str] | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Build one deterministic structured message without replacing run events."""

    safe_payload = deepcopy(payload) if isinstance(payload, dict) else {}
    safe_artifact_ids = [str(value) for value in (artifact_ids or []) if str(value or "")]
    return {
        "message_version": "agent_message_v1",
        "message_id": _stable_graph_id(
            "agent_message",
            message_type,
            source_agent_id,
            target_agent_id or "",
            run_id or "",
            job_id or "",
            safe_artifact_ids,
            safe_payload,
        ),
        "message_type": str(message_type or "handoff"),
        "source_agent_id": str(source_agent_id or ""),
        "target_agent_id": str(target_agent_id or ""),
        "run_id": str(run_id or ""),
        "job_id": str(job_id or ""),
        "project_id": str(project_id or "demo_project_default"),
        "artifact_ids": safe_artifact_ids,
        "payload": safe_payload,
        "created_at": utc_now_iso(),
        "safety_boundaries": _graph_safety_boundaries(),
    }



def build_agent_contract_handoff_message(
    source_agent_id: str,
    target_agent_id: str,
    payload: dict[str, Any],
    run_id: str | None = None,
    job_id: str | None = None,
    artifact_ids: list[str] | None = None,
    artifact_types: list[str] | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Build a structured handoff message with contract validation metadata."""

    validation = validate_agent_contract_handoff(
        source_agent_id=source_agent_id,
        target_agent_id=target_agent_id,
        artifact_types=artifact_types,
    )
    safe_payload = deepcopy(payload) if isinstance(payload, dict) else {}
    safe_payload["contract_validation"] = validation
    message = build_agent_message(
        message_type="contract_handoff",
        source_agent_id=source_agent_id,
        target_agent_id=target_agent_id,
        payload=safe_payload,
        run_id=run_id,
        job_id=job_id,
        artifact_ids=artifact_ids,
        project_id=project_id,
    )
    message["contract_registry_version"] = AGENT_CONTRACT_REGISTRY_VERSION
    message["contract_validation"] = validation
    message["handoff_valid"] = validation["valid"]
    return message


AGENT_RUNNER_PLAN_VERSION = "agent_runner_plan_v1"


def _runner_plan_step(
    step_id: str,
    step_type: str,
    agent_id: str,
    status: str,
    description: str,
    requires_user_action: bool = False,
) -> dict[str, Any]:
    return {
        "step_id": str(step_id or ""),
        "step_type": str(step_type or ""),
        "agent_id": str(agent_id or ""),
        "status": str(status or "pending"),
        "description": str(description or ""),
        "requires_user_action": bool(requires_user_action),
    }


def _runner_waiting_action_types() -> set[str]:
    return {
        "add_source",
        "paste_reviews",
        "review_blocker",
        "upload_asset",
        "record_experiment",
        "approve_controlled_test",
        "submit_provider_simulation",
    }


def build_agent_runner_plan(
    planner_recommendation: dict[str, Any],
    project: dict[str, Any] | None = None,
    artifact_registry: dict[str, Any] | None = None,
    latest_run: dict[str, Any] | None = None,
    latest_job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Turn one Supervisor Planner recommendation into a deterministic runner plan.

    This function plans the next graph step only. It does not execute agents,
    call external providers, or enable autonomous LLM decisions.
    """

    recommendation = planner_recommendation if isinstance(planner_recommendation, dict) else {}
    safe_project = project if isinstance(project, dict) else {}
    safe_registry = artifact_registry if isinstance(artifact_registry, dict) else {}
    safe_run = latest_run if isinstance(latest_run, dict) else {}
    safe_job = latest_job if isinstance(latest_job, dict) else {}

    project_id = str(
        recommendation.get("project_id")
        or safe_project.get("project_id")
        or safe_registry.get("project_id")
        or safe_run.get("project_id")
        or safe_job.get("project_id")
        or "demo_project_default"
    )
    next_agent_id = str(recommendation.get("next_agent_id") or "").strip()
    next_action_type = str(recommendation.get("next_action_type") or "").strip()
    overall_status = str(recommendation.get("overall_status") or "").strip()
    user_action_required = bool(recommendation.get("user_action_required"))
    waiting_action = next_action_type in _runner_waiting_action_types()
    optional_user_input = (
        next_action_type == "upload_asset"
        and recommendation.get("can_start_agent_run") is True
    )

    contract = get_agent_contract(next_agent_id)
    handoff_message: dict[str, Any] = {}
    validation: dict[str, Any] = {
        "valid": False,
        "reasons": ["No next_agent_id was provided."],
        "warnings": [],
    }

    if next_agent_id:
        handoff_message = build_agent_contract_handoff_message(
            source_agent_id="planner_agent",
            target_agent_id=next_agent_id,
            payload={
                "planner_recommendation": deepcopy(recommendation),
                "project_id": project_id,
                "overall_status": overall_status,
                "next_action_type": next_action_type,
            },
            run_id=str(safe_run.get("run_id") or ""),
            job_id=str(safe_job.get("job_id") or ""),
            artifact_ids=[
                str(value)
                for value in (
                    recommendation.get("artifact_ids")
                    or safe_registry.get("artifact_ids")
                    or []
                )
                if str(value or "")
            ],
            artifact_types=["supervisor_planner_recommendation"],
            project_id=project_id,
        )
        validation = handoff_message.get("contract_validation") if isinstance(handoff_message.get("contract_validation"), dict) else validation

    contract_valid = bool(validation.get("valid"))
    blocked_reasons = list(validation.get("reasons") or [])
    warnings = list(validation.get("warnings") or []) + list(recommendation.get("warnings") or [])

    if not next_agent_id or not contract:
        execution_status = "blocked"
        can_execute_next_agent = False
        if not contract:
            blocked_reasons.append("Next agent contract was not found.")
    elif not contract_valid:
        execution_status = "blocked"
        can_execute_next_agent = False
    elif waiting_action or user_action_required:
        execution_status = "ready_with_optional_user_input" if optional_user_input else "waiting_for_user"
        can_execute_next_agent = False
    else:
        execution_status = "ready"
        can_execute_next_agent = True

    planned_steps = [
        _runner_plan_step(
            "inspect_project_state",
            "state_check",
            "planner_agent",
            "complete",
            "Read project state and Supervisor Planner recommendation.",
        ),
        _runner_plan_step(
            "validate_contract_handoff",
            "contract_validation",
            "planner_agent",
            "complete" if contract_valid else "failed",
            "Validate the planner-to-next-agent handoff against Agent Contract Registry.",
        ),
    ]

    if execution_status == "ready":
        planned_steps.append(
            _runner_plan_step(
                "execute_next_agent",
                "agent_execution",
                next_agent_id,
                "pending",
                "Runner may execute the next deterministic agent step.",
            )
        )
    elif execution_status in {"waiting_for_user", "ready_with_optional_user_input"}:
        planned_steps.append(
            _runner_plan_step(
                "wait_for_user_input",
                "user_gate",
                next_agent_id,
                "waiting_for_user",
                "User action or manual confirmation is needed before this graph path continues.",
                requires_user_action=True,
            )
        )
    else:
        planned_steps.append(
            _runner_plan_step(
                "block_next_agent",
                "blocked",
                next_agent_id,
                "failed",
                "Runner cannot execute the next agent until contract or project-state issues are fixed.",
            )
        )

    return {
        "runner_plan_version": AGENT_RUNNER_PLAN_VERSION,
        "project_id": project_id,
        "registry_version": AGENT_CONTRACT_REGISTRY_VERSION,
        "graph_version": GRAPH_VERSION,
        "execution_mode": GRAPH_EXECUTION_MODE,
        "autonomy_level": AUTONOMY_LEVEL,
        "overall_status": overall_status,
        "next_action_type": next_action_type,
        "next_agent_id": next_agent_id,
        "execution_status": execution_status,
        "can_execute_next_agent": can_execute_next_agent,
        "requires_user_action": execution_status == "waiting_for_user",
        "optional_user_input": optional_user_input,
        "blocked_reasons": list(dict.fromkeys(str(item) for item in blocked_reasons if str(item or ""))),
        "warnings": list(dict.fromkeys(str(item) for item in warnings if str(item or ""))),
        "next_agent_contract": deepcopy(contract),
        "contract_validation": deepcopy(validation),
        "handoff_message": deepcopy(handoff_message),
        "planned_steps": planned_steps,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    safe_plan = plan if isinstance(plan, dict) else {}
    steps = safe_plan.get("planned_steps") if isinstance(safe_plan.get("planned_steps"), list) else []
    return {
        "summary_version": "agent_runner_plan_summary_v1",
        "runner_plan_version": str(safe_plan.get("runner_plan_version") or AGENT_RUNNER_PLAN_VERSION),
        "project_id": str(safe_plan.get("project_id") or "demo_project_default"),
        "execution_status": str(safe_plan.get("execution_status") or "blocked"),
        "next_agent_id": str(safe_plan.get("next_agent_id") or ""),
        "next_action_type": str(safe_plan.get("next_action_type") or ""),
        "can_execute_next_agent": bool(safe_plan.get("can_execute_next_agent")),
        "requires_user_action": bool(safe_plan.get("requires_user_action")),
        "optional_user_input": bool(safe_plan.get("optional_user_input")),
        "planned_step_count": len(steps),
        "blocked_reason_count": len(safe_plan.get("blocked_reasons") or []),
        "warning_count": len(safe_plan.get("warnings") or []),
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_DISPATCH_TICKET_VERSION = "agent_runner_dispatch_ticket_v1"


def _runner_dispatch_preflight_check(
    check_id: str,
    status: str,
    message: str,
    blocking: bool = False,
) -> dict[str, Any]:
    return {
        "check_id": str(check_id or ""),
        "status": str(status or "unknown"),
        "message": str(message or ""),
        "blocking": bool(blocking),
    }


def build_agent_runner_dispatch_ticket(
    runner_plan: dict[str, Any],
    requested_by: str = "runner_plan_api",
) -> dict[str, Any]:
    """Build a safe dispatch ticket from a runner plan.

    The ticket is still dry-run only. It does not execute agents, call providers,
    spend money, or enable autonomous LLM routing.
    """

    plan = runner_plan if isinstance(runner_plan, dict) else {}
    execution_status = str(plan.get("execution_status") or "blocked")
    next_agent_id = str(plan.get("next_agent_id") or "")
    next_action_type = str(plan.get("next_action_type") or "")
    contract_validation = plan.get("contract_validation") if isinstance(plan.get("contract_validation"), dict) else {}
    safety_boundaries = _graph_safety_boundaries()

    preflight_checks = [
        _runner_dispatch_preflight_check(
            "runner_plan_shape",
            "passed" if plan.get("runner_plan_version") == AGENT_RUNNER_PLAN_VERSION else "failed",
            "Runner plan version is recognized." if plan.get("runner_plan_version") == AGENT_RUNNER_PLAN_VERSION else "Runner plan version is missing or unsupported.",
            blocking=plan.get("runner_plan_version") != AGENT_RUNNER_PLAN_VERSION,
        ),
        _runner_dispatch_preflight_check(
            "contract_validation",
            "passed" if bool(contract_validation.get("valid")) else "failed",
            "Agent contract handoff is valid." if bool(contract_validation.get("valid")) else "Agent contract handoff is invalid.",
            blocking=not bool(contract_validation.get("valid")),
        ),
        _runner_dispatch_preflight_check(
            "user_gate",
            "waiting" if bool(plan.get("requires_user_action")) else "passed",
            "User action is required before dispatch." if bool(plan.get("requires_user_action")) else "No required user gate blocks dispatch.",
            blocking=bool(plan.get("requires_user_action")),
        ),
        _runner_dispatch_preflight_check(
            "execution_status",
            "passed" if execution_status == "ready" else execution_status,
            f"Runner plan execution_status is {execution_status}.",
            blocking=execution_status != "ready",
        ),
        _runner_dispatch_preflight_check(
            "external_provider_guard",
            "passed",
            "Dry-run dispatch ticket does not call external providers or incur cost.",
            blocking=False,
        ),
    ]

    blocking_checks = [item for item in preflight_checks if item.get("blocking")]
    dispatch_allowed = bool(plan.get("can_execute_next_agent")) and not blocking_checks and bool(next_agent_id)

    if dispatch_allowed:
        dispatch_status = "ready_to_dispatch"
        recommended_command = "execute_next_agent_dry_run"
    elif bool(plan.get("requires_user_action")):
        dispatch_status = "waiting_for_user"
        recommended_command = "collect_required_user_input"
    else:
        dispatch_status = "blocked"
        recommended_command = "fix_runner_plan_blockers"

    return {
        "dispatch_ticket_version": AGENT_RUNNER_DISPATCH_TICKET_VERSION,
        "runner_plan_version": str(plan.get("runner_plan_version") or ""),
        "registry_version": str(plan.get("registry_version") or AGENT_CONTRACT_REGISTRY_VERSION),
        "graph_version": GRAPH_VERSION,
        "execution_mode": GRAPH_EXECUTION_MODE,
        "autonomy_level": AUTONOMY_LEVEL,
        "project_id": str(plan.get("project_id") or "demo_project_default"),
        "requested_by": str(requested_by or "runner_plan_api"),
        "dry_run": True,
        "dispatch_allowed": dispatch_allowed,
        "dispatch_status": dispatch_status,
        "recommended_command": recommended_command,
        "next_agent_id": next_agent_id,
        "next_action_type": next_action_type,
        "handoff_message": deepcopy(plan.get("handoff_message") or {}),
        "contract_validation": deepcopy(contract_validation),
        "preflight_checks": preflight_checks,
        "blocking_check_ids": [str(item.get("check_id") or "") for item in blocking_checks],
        "planned_steps": deepcopy(plan.get("planned_steps") or []),
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "safety_boundaries": safety_boundaries,
    }


def build_agent_runner_dispatch_summary(ticket: dict[str, Any]) -> dict[str, Any]:
    safe_ticket = ticket if isinstance(ticket, dict) else {}
    checks = safe_ticket.get("preflight_checks") if isinstance(safe_ticket.get("preflight_checks"), list) else []
    return {
        "summary_version": "agent_runner_dispatch_summary_v1",
        "dispatch_ticket_version": str(safe_ticket.get("dispatch_ticket_version") or AGENT_RUNNER_DISPATCH_TICKET_VERSION),
        "project_id": str(safe_ticket.get("project_id") or "demo_project_default"),
        "dispatch_status": str(safe_ticket.get("dispatch_status") or "blocked"),
        "dispatch_allowed": bool(safe_ticket.get("dispatch_allowed")),
        "next_agent_id": str(safe_ticket.get("next_agent_id") or ""),
        "next_action_type": str(safe_ticket.get("next_action_type") or ""),
        "recommended_command": str(safe_ticket.get("recommended_command") or ""),
        "preflight_check_count": len(checks),
        "blocking_check_count": len(safe_ticket.get("blocking_check_ids") or []),
        "dry_run": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_DISPATCH_EVENT_VERSION = "agent_runner_dispatch_event_v1"


def _dispatch_event_status_from_ticket(ticket: dict[str, Any]) -> str:
    dispatch_status = str(ticket.get("dispatch_status") or "blocked")
    if bool(ticket.get("dispatch_allowed")):
        return "dispatch_ready"
    if dispatch_status == "waiting_for_user":
        return "dispatch_waiting_for_user"
    return "dispatch_blocked"


def build_agent_runner_dispatch_event(
    dispatch_ticket: dict[str, Any],
    event_id: str | None = None,
) -> dict[str, Any]:
    """Build a dry-run dispatch event for auditability.

    This records a proposed dispatch. It does not execute agents, call
    providers, spend money, or enable autonomous LLM decisions.
    """

    ticket = dispatch_ticket if isinstance(dispatch_ticket, dict) else {}
    project_id = str(ticket.get("project_id") or "demo_project_default")
    next_agent_id = str(ticket.get("next_agent_id") or "")
    dispatch_status = str(ticket.get("dispatch_status") or "blocked")
    safe_event_id = str(
        event_id
        or f"dispatch_event_{project_id}_{next_agent_id or 'none'}_{dispatch_status}"
    ).replace(" ", "_")

    preflight_checks = ticket.get("preflight_checks") if isinstance(ticket.get("preflight_checks"), list) else []
    preflight_check_ids = [
        str(item.get("check_id") or "")
        for item in preflight_checks
        if isinstance(item, dict) and str(item.get("check_id") or "")
    ]
    blocking_check_ids = [
        str(item)
        for item in (ticket.get("blocking_check_ids") or [])
        if str(item or "")
    ]

    event_status = _dispatch_event_status_from_ticket(ticket)
    message = build_agent_message(
        message_type="runner_dispatch_event",
        source_agent_id="runner_dispatcher",
        target_agent_id=next_agent_id,
        payload={
            "dispatch_ticket_version": ticket.get("dispatch_ticket_version"),
            "dispatch_status": dispatch_status,
            "dispatch_allowed": bool(ticket.get("dispatch_allowed")),
            "recommended_command": ticket.get("recommended_command"),
            "preflight_check_ids": preflight_check_ids,
            "blocking_check_ids": blocking_check_ids,
            "dry_run": True,
        },
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "dispatch_event_version": AGENT_RUNNER_DISPATCH_EVENT_VERSION,
        "event_id": safe_event_id,
        "event_type": "runner_dispatch_dry_run",
        "event_status": event_status,
        "project_id": project_id,
        "source_agent_id": "runner_dispatcher",
        "target_agent_id": next_agent_id,
        "dispatch_ticket_version": str(ticket.get("dispatch_ticket_version") or ""),
        "dispatch_status": dispatch_status,
        "dispatch_allowed": bool(ticket.get("dispatch_allowed")),
        "recommended_command": str(ticket.get("recommended_command") or ""),
        "next_action_type": str(ticket.get("next_action_type") or ""),
        "dry_run": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "preflight_check_ids": preflight_check_ids,
        "blocking_check_ids": blocking_check_ids,
        "handoff_message": deepcopy(ticket.get("handoff_message") or {}),
        "contract_validation": deepcopy(ticket.get("contract_validation") or {}),
        "dispatch_message": message,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_dispatch_event_summary(event: dict[str, Any]) -> dict[str, Any]:
    safe_event = event if isinstance(event, dict) else {}
    return {
        "summary_version": "agent_runner_dispatch_event_summary_v1",
        "dispatch_event_version": str(safe_event.get("dispatch_event_version") or AGENT_RUNNER_DISPATCH_EVENT_VERSION),
        "event_id": str(safe_event.get("event_id") or ""),
        "event_status": str(safe_event.get("event_status") or "dispatch_blocked"),
        "event_type": str(safe_event.get("event_type") or "runner_dispatch_dry_run"),
        "project_id": str(safe_event.get("project_id") or "demo_project_default"),
        "target_agent_id": str(safe_event.get("target_agent_id") or ""),
        "dispatch_allowed": bool(safe_event.get("dispatch_allowed")),
        "blocking_check_count": len(safe_event.get("blocking_check_ids") or []),
        "preflight_check_count": len(safe_event.get("preflight_check_ids") or []),
        "dry_run": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_EXECUTION_RECEIPT_VERSION = "agent_runner_execution_receipt_v1"


def _execution_receipt_status_from_dispatch(
    dispatch_ticket: dict[str, Any],
    dispatch_event: dict[str, Any],
) -> str:
    ticket = dispatch_ticket if isinstance(dispatch_ticket, dict) else {}
    event = dispatch_event if isinstance(dispatch_event, dict) else {}

    if bool(ticket.get("dispatch_allowed")) and str(event.get("event_status") or "") == "dispatch_ready":
        return "execution_ready_dry_run"
    if str(ticket.get("dispatch_status") or "") == "waiting_for_user" or str(event.get("event_status") or "") == "dispatch_waiting_for_user":
        return "execution_waiting_for_user"
    return "execution_blocked"


def build_agent_runner_execution_receipt(
    dispatch_ticket: dict[str, Any],
    dispatch_event: dict[str, Any],
    requested_by: str = "runner_execute_dry_run_api",
) -> dict[str, Any]:
    """Build a safe dry-run execution receipt from a dispatch ticket/event.

    This does not execute agents, call providers, spend money, or enable
    autonomous LLM routing. It only records what would happen next.
    """

    ticket = dispatch_ticket if isinstance(dispatch_ticket, dict) else {}
    event = dispatch_event if isinstance(dispatch_event, dict) else {}

    project_id = str(ticket.get("project_id") or event.get("project_id") or "demo_project_default")
    target_agent_id = str(ticket.get("next_agent_id") or event.get("target_agent_id") or "")
    receipt_status = _execution_receipt_status_from_dispatch(ticket, event)
    execution_allowed = receipt_status == "execution_ready_dry_run"

    blocking_check_ids = [
        str(item)
        for item in (ticket.get("blocking_check_ids") or event.get("blocking_check_ids") or [])
        if str(item or "")
    ]

    if execution_allowed:
        recommended_next_state = "ready_for_explicit_real_execution"
        execution_message = "Dry-run passed. Real agent execution is still disabled until an explicit execution mode is implemented."
    elif receipt_status == "execution_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        execution_message = "Execution dry-run is waiting for required user action."
    else:
        recommended_next_state = "fix_execution_blockers"
        execution_message = "Execution dry-run is blocked by dispatch preflight or contract validation."

    execution_payload = {
        "receipt_status": receipt_status,
        "target_agent_id": target_agent_id,
        "dispatch_event_id": event.get("event_id"),
        "dispatch_status": ticket.get("dispatch_status"),
        "dispatch_allowed": bool(ticket.get("dispatch_allowed")),
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "execution_performed": False,
    }

    execution_message_record = build_agent_message(
        message_type="runner_execution_dry_run_receipt",
        source_agent_id="runner_executor",
        target_agent_id=target_agent_id,
        payload=execution_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "execution_receipt_version": AGENT_RUNNER_EXECUTION_RECEIPT_VERSION,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_execute_dry_run_api"),
        "receipt_status": receipt_status,
        "target_agent_id": target_agent_id,
        "dispatch_ticket_version": str(ticket.get("dispatch_ticket_version") or ""),
        "dispatch_event_version": str(event.get("dispatch_event_version") or ""),
        "dispatch_event_id": str(event.get("event_id") or ""),
        "dispatch_allowed": bool(ticket.get("dispatch_allowed")),
        "execution_allowed": execution_allowed,
        "execution_performed": False,
        "dry_run": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "blocking_check_ids": blocking_check_ids,
        "recommended_next_state": recommended_next_state,
        "execution_message": execution_message,
        "execution_message_record": execution_message_record,
        "handoff_message": deepcopy(ticket.get("handoff_message") or event.get("handoff_message") or {}),
        "contract_validation": deepcopy(ticket.get("contract_validation") or event.get("contract_validation") or {}),
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_execution_receipt_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    safe_receipt = receipt if isinstance(receipt, dict) else {}
    return {
        "summary_version": "agent_runner_execution_receipt_summary_v1",
        "execution_receipt_version": str(safe_receipt.get("execution_receipt_version") or AGENT_RUNNER_EXECUTION_RECEIPT_VERSION),
        "project_id": str(safe_receipt.get("project_id") or "demo_project_default"),
        "receipt_status": str(safe_receipt.get("receipt_status") or "execution_blocked"),
        "target_agent_id": str(safe_receipt.get("target_agent_id") or ""),
        "execution_allowed": bool(safe_receipt.get("execution_allowed")),
        "execution_performed": False,
        "dry_run": True,
        "blocking_check_count": len(safe_receipt.get("blocking_check_ids") or []),
        "recommended_next_state": str(safe_receipt.get("recommended_next_state") or ""),
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }



AGENT_RUNNER_EVENT_LEDGER_SUMMARY_VERSION = "agent_runner_event_ledger_summary_v1"


def _runner_normalized_event_from_record(
    record: dict[str, Any],
    *,
    fallback_event_type: str,
    fallback_status_key: str,
    source_agent_id: str = "",
    target_agent_id: str = "",
    blocking_default: bool = True,
) -> dict[str, Any]:
    safe_record = record if isinstance(record, dict) else {}

    event_status = str(
        safe_record.get("event_status")
        or safe_record.get("receipt_status")
        or safe_record.get("audit_ledger_status")
        or safe_record.get("real_execution_incident_response_status")
        or safe_record.get("incident_receipt_status")
        or safe_record.get(fallback_status_key)
        or "not_refreshed"
    )
    event_type = str(
        safe_record.get("event_type")
        or safe_record.get("message_type")
        or fallback_event_type
    )
    event_id = str(
        safe_record.get("event_id")
        or safe_record.get("receipt_id")
        or safe_record.get("audit_ledger_id")
        or safe_record.get("incident_receipt_id")
        or f"{event_type}_{event_status}"
    ).replace(" ", "_")

    safe_to_continue = bool(safe_record.get("safe_to_continue"))
    provider_call_performed = bool(safe_record.get("provider_call_performed"))
    external_api_called = bool(safe_record.get("external_api_called"))
    agent_execution_performed = bool(safe_record.get("agent_execution_performed") or safe_record.get("execution_performed"))

    blocking = bool(
        safe_record.get("blocking")
        or safe_record.get("abort_recommended")
        or safe_record.get("incident_detected")
        or safe_record.get("manual_review_required")
        or blocking_default
    )

    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_status": event_status,
        "project_id": str(safe_record.get("project_id") or "demo_project_default"),
        "source_agent_id": str(safe_record.get("source_agent_id") or source_agent_id),
        "target_agent_id": str(safe_record.get("target_agent_id") or target_agent_id),
        "blocking": blocking,
        "safe_to_continue": safe_to_continue,
        "dry_run": True,
        "provider_call_performed": provider_call_performed,
        "external_api_called": external_api_called,
        "agent_execution_performed": agent_execution_performed,
        "manual_review_required": bool(safe_record.get("manual_review_required") or blocking),
    }



AGENT_RUNNER_SUPERVISOR_EVENT_LEDGER_DECISION_SUMMARY_VERSION = "agent_runner_supervisor_event_ledger_decision_summary_v1"


def build_agent_runner_supervisor_event_ledger_decision_summary(
    event_ledger_summary: dict[str, Any],
    *,
    project_id: str = "demo_project_default",
    requested_by: str = "runner_supervisor_event_ledger_decision_builder",
) -> dict[str, Any]:
    """Build a Supervisor decision summary from the unified runner event ledger.

    This is a dry-run routing decision. It does not execute agents, call
    providers, call external APIs, spend money, or unlock real execution.
    """

    ledger = event_ledger_summary if isinstance(event_ledger_summary, dict) else {}
    safe_project_id = str(project_id or ledger.get("project_id") or "demo_project_default")
    events = ledger.get("normalized_events") if isinstance(ledger.get("normalized_events"), list) else []
    blocking_event_count = int(ledger.get("blocking_event_count") or 0)
    event_count = int(ledger.get("event_count") or len(events))
    provider_call_performed = bool(ledger.get("provider_call_performed"))
    external_api_called = bool(ledger.get("external_api_called"))
    agent_execution_performed = bool(ledger.get("agent_execution_performed"))
    safe_to_continue = bool(ledger.get("safe_to_continue"))

    if not event_count:
        supervisor_decision_status = "supervisor_waiting_for_event_ledger"
        recommended_next_action = "refresh_runner_event_ledger_summary"
        decision_reason = "No normalized runner events are available for Supervisor routing."
    elif provider_call_performed or external_api_called or agent_execution_performed:
        supervisor_decision_status = "supervisor_hard_blocked_external_execution_detected"
        recommended_next_action = "open_incident_response_and_manual_review"
        decision_reason = "A real provider/API/agent execution signal was detected, so Supervisor must hard-block the chain."
    elif blocking_event_count > 0:
        supervisor_decision_status = "supervisor_blocked_by_event_ledger"
        recommended_next_action = "inspect_blocking_events_before_next_dry_run"
        decision_reason = "The event ledger contains blocking events, so Supervisor keeps real execution disabled."
    elif safe_to_continue:
        supervisor_decision_status = "supervisor_ready_for_next_dry_run_step"
        recommended_next_action = "continue_next_safe_dry_run_step"
        decision_reason = "The event ledger has no blocking events, but real execution is still disabled by default."
    else:
        supervisor_decision_status = "supervisor_manual_review_required"
        recommended_next_action = "request_operator_review"
        decision_reason = "The event ledger is recorded but does not permit automatic continuation."

    blocking_event_ids = [
        str(event.get("event_id") or "")
        for event in events
        if isinstance(event, dict) and bool(event.get("blocking"))
    ]
    next_agent_candidates = [
        str(event.get("target_agent_id") or "")
        for event in events
        if isinstance(event, dict) and str(event.get("target_agent_id") or "")
    ]

    return {
        "supervisor_event_ledger_decision_summary_version": AGENT_RUNNER_SUPERVISOR_EVENT_LEDGER_DECISION_SUMMARY_VERSION,
        "supervisor_event_ledger_decision_status": supervisor_decision_status,
        "project_id": safe_project_id,
        "requested_by": str(requested_by or "runner_supervisor_event_ledger_decision_builder"),
        "event_ledger_summary_version": str(ledger.get("runner_event_ledger_summary_version") or ""),
        "event_ledger_summary_status": str(ledger.get("runner_event_ledger_summary_status") or ""),
        "event_count": event_count,
        "blocking_event_count": blocking_event_count,
        "blocking_event_ids": blocking_event_ids,
        "next_agent_candidates": next_agent_candidates,
        "recommended_next_action": recommended_next_action,
        "decision_reason": decision_reason,
        "supervisor_routing_allowed": safe_to_continue and blocking_event_count == 0,
        "real_execution_allowed": False,
        "provider_call_allowed": False,
        "external_api_call_allowed": False,
        "agent_execution_allowed": False,
        "provider_call_performed": provider_call_performed,
        "external_api_called": external_api_called,
        "agent_execution_performed": agent_execution_performed,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }



AGENT_RUNNER_SUPERVISOR_NEXT_STEP_ROUTING_PLAN_VERSION = "agent_runner_supervisor_next_step_routing_plan_v1"


def build_agent_runner_supervisor_next_step_routing_plan(
    supervisor_decision: dict[str, Any],
    *,
    project_id: str = "demo_project_default",
    requested_by: str = "runner_supervisor_next_step_routing_plan_builder",
) -> dict[str, Any]:
    """Build the next dry-run routing plan from Supervisor decision summary.

    This is a safe routing plan only. It does not execute agents, call
    providers, call external APIs, spend money, or unlock real execution.
    """

    decision = supervisor_decision if isinstance(supervisor_decision, dict) else {}
    safe_project_id = str(project_id or decision.get("project_id") or "demo_project_default")
    decision_status = str(decision.get("supervisor_event_ledger_decision_status") or "supervisor_manual_review_required")
    recommended_next_action = str(decision.get("recommended_next_action") or "request_operator_review")
    blocking_event_ids = [
        str(item)
        for item in (decision.get("blocking_event_ids") or [])
        if str(item or "")
    ]
    next_agent_candidates = [
        str(item)
        for item in (decision.get("next_agent_candidates") or [])
        if str(item or "")
    ]

    if decision_status == "supervisor_waiting_for_event_ledger":
        routing_plan_status = "routing_plan_waiting_for_event_ledger"
        next_step_type = "refresh_event_ledger"
        target_agent_id = "supervisor_agent"
        recommended_endpoint = "/api/v1/projects/{project_id}/runner/real-execution-incident-response/dry-run"
        routing_reason = "Supervisor needs a refreshed unified event ledger before planning the next dry-run step."
    elif decision_status == "supervisor_hard_blocked_external_execution_detected":
        routing_plan_status = "routing_plan_hard_blocked"
        next_step_type = "open_incident_response"
        target_agent_id = "incident_response_agent"
        recommended_endpoint = "/api/v1/projects/{project_id}/runner/real-execution-incident-response/dry-run"
        routing_reason = "External execution signals require incident response and manual review."
    elif decision_status == "supervisor_blocked_by_event_ledger":
        routing_plan_status = "routing_plan_blocked_by_event_ledger"
        next_step_type = "inspect_blocking_events"
        target_agent_id = "risk_approval_agent"
        recommended_endpoint = "/api/v1/projects/{project_id}/runner/real-execution-incident-response/dry-run"
        routing_reason = "Blocking ledger events must be inspected before any next dry-run routing step."
    elif decision_status == "supervisor_ready_for_next_dry_run_step":
        routing_plan_status = "routing_plan_ready_for_next_dry_run"
        next_step_type = "continue_next_safe_dry_run"
        target_agent_id = next_agent_candidates[0] if next_agent_candidates else "supervisor_agent"
        recommended_endpoint = "/api/v1/projects/{project_id}/runner/dispatch/dry-run"
        routing_reason = "Supervisor can continue only to the next safe dry-run step; real execution remains disabled."
    else:
        routing_plan_status = "routing_plan_manual_review_required"
        next_step_type = "request_operator_review"
        target_agent_id = "operator_agent"
        recommended_endpoint = "/api/v1/projects/{project_id}/runner/real-execution-approval-request/dry-run"
        routing_reason = "Supervisor requires operator review before planning the next dry-run step."

    routing_allowed = routing_plan_status == "routing_plan_ready_for_next_dry_run"

    return {
        "supervisor_next_step_routing_plan_version": AGENT_RUNNER_SUPERVISOR_NEXT_STEP_ROUTING_PLAN_VERSION,
        "supervisor_next_step_routing_plan_status": routing_plan_status,
        "project_id": safe_project_id,
        "requested_by": str(requested_by or "runner_supervisor_next_step_routing_plan_builder"),
        "source_decision_status": decision_status,
        "source_recommended_next_action": recommended_next_action,
        "next_step_type": next_step_type,
        "target_agent_id": target_agent_id,
        "recommended_endpoint": recommended_endpoint,
        "recommended_command": recommended_endpoint.replace("{project_id}", safe_project_id),
        "routing_reason": routing_reason,
        "blocking_event_ids": blocking_event_ids,
        "blocking_event_count": len(blocking_event_ids),
        "next_agent_candidates": next_agent_candidates,
        "routing_allowed": routing_allowed,
        "supervisor_routing_allowed": bool(decision.get("supervisor_routing_allowed")) and routing_allowed,
        "manual_review_required": True,
        "real_execution_allowed": False,
        "provider_call_allowed": False,
        "external_api_call_allowed": False,
        "agent_execution_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "safe_to_continue": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }



AGENT_RUNNER_SUPERVISOR_NEXT_STEP_WORK_ORDER_PREVIEW_VERSION = "agent_runner_supervisor_next_step_work_order_preview_v1"


def build_agent_runner_supervisor_next_step_work_order_preview(
    routing_plan: dict[str, Any],
    *,
    project_id: str = "demo_project_default",
    requested_by: str = "runner_supervisor_next_step_work_order_preview_builder",
) -> dict[str, Any]:
    """Bridge a Supervisor next-step routing plan into a dry-run work order preview.

    This creates a structured work order draft for the next safe dry-run step.
    It does not execute agents, call providers, call external APIs, spend money,
    persist a queue item, or unlock real execution.
    """

    plan = routing_plan if isinstance(routing_plan, dict) else {}
    safe_project_id = str(project_id or plan.get("project_id") or "demo_project_default")
    routing_status = str(plan.get("supervisor_next_step_routing_plan_status") or "routing_plan_manual_review_required")
    next_step_type = str(plan.get("next_step_type") or "request_operator_review")
    target_agent_id = str(plan.get("target_agent_id") or "operator_agent")
    recommended_command = str(plan.get("recommended_command") or "")
    recommended_endpoint = str(plan.get("recommended_endpoint") or "")
    blocking_event_ids = [
        str(item)
        for item in (plan.get("blocking_event_ids") or [])
        if str(item or "")
    ]
    next_agent_candidates = [
        str(item)
        for item in (plan.get("next_agent_candidates") or [])
        if str(item or "")
    ]

    if bool(plan.get("routing_allowed")) and routing_status == "routing_plan_ready_for_next_dry_run":
        work_order_status = "supervisor_work_order_ready_dry_run"
        work_order_allowed = True
        recommended_next_state = "continue_next_safe_dry_run_step"
        work_order_message = "Supervisor routing plan is ready for the next safe dry-run work order. Real execution remains disabled."
    elif routing_status == "routing_plan_waiting_for_event_ledger":
        work_order_status = "supervisor_work_order_waiting_for_event_ledger"
        work_order_allowed = False
        recommended_next_state = "refresh_runner_event_ledger_summary"
        work_order_message = "Supervisor needs a refreshed event ledger before creating a runnable dry-run work order."
    elif routing_status == "routing_plan_manual_review_required":
        work_order_status = "supervisor_work_order_waiting_for_manual_review"
        work_order_allowed = False
        recommended_next_state = "request_operator_review"
        work_order_message = "Supervisor requires manual review before the next dry-run work order can proceed."
    else:
        work_order_status = "supervisor_work_order_blocked"
        work_order_allowed = False
        recommended_next_state = "inspect_blocking_events_before_next_dry_run"
        work_order_message = "Supervisor work order is blocked by event ledger or safety routing blockers."

    work_order_id = f"supervisor_next_step_work_order_{safe_project_id}_{next_step_type}_{work_order_status}".replace(" ", "_")

    return {
        "supervisor_next_step_work_order_preview_version": AGENT_RUNNER_SUPERVISOR_NEXT_STEP_WORK_ORDER_PREVIEW_VERSION,
        "supervisor_next_step_work_order_status": work_order_status,
        "work_order_id": work_order_id,
        "project_id": safe_project_id,
        "requested_by": str(requested_by or "runner_supervisor_next_step_work_order_preview_builder"),
        "source_routing_plan_version": str(plan.get("supervisor_next_step_routing_plan_version") or ""),
        "source_routing_plan_status": routing_status,
        "next_step_type": next_step_type,
        "target_agent_id": target_agent_id,
        "recommended_endpoint": recommended_endpoint,
        "recommended_command": recommended_command,
        "routing_reason": str(plan.get("routing_reason") or ""),
        "work_order_allowed": work_order_allowed,
        "routing_allowed": bool(plan.get("routing_allowed")) and work_order_allowed,
        "supervisor_routing_allowed": bool(plan.get("supervisor_routing_allowed")) and work_order_allowed,
        "recommended_next_state": recommended_next_state,
        "work_order_message": work_order_message,
        "blocking_event_ids": blocking_event_ids,
        "blocking_event_count": len(blocking_event_ids),
        "next_agent_candidates": next_agent_candidates,
        "manual_review_required": True,
        "queue_persisted": False,
        "work_order_persisted": False,
        "real_execution_allowed": False,
        "provider_call_allowed": False,
        "external_api_call_allowed": False,
        "agent_execution_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "safe_to_continue": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_event_ledger_summary(
    *,
    project_id: str = "demo_project_default",
    dispatch_event: dict[str, Any] | None = None,
    execution_receipt: dict[str, Any] | None = None,
    audit_ledger: dict[str, Any] | None = None,
    safety_chain_event: dict[str, Any] | None = None,
    incident_receipt: dict[str, Any] | None = None,
    requested_by: str = "runner_event_ledger_summary_builder",
) -> dict[str, Any]:
    """Build a unified dry-run event ledger summary.

    This normalizes multiple runner events and receipts into a single ledger
    summary. It does not persist the ledger, execute agents, call providers,
    call external APIs, or enable real execution.
    """

    safe_project_id = str(project_id or "demo_project_default")
    normalized_events: list[dict[str, Any]] = []

    if isinstance(dispatch_event, dict) and dispatch_event:
        normalized_events.append(
            _runner_normalized_event_from_record(
                dispatch_event,
                fallback_event_type="runner_dispatch_dry_run",
                fallback_status_key="dispatch_status",
                source_agent_id="runner_dispatcher",
                target_agent_id=str(dispatch_event.get("target_agent_id") or ""),
                blocking_default=not bool(dispatch_event.get("dispatch_allowed")),
            )
        )

    if isinstance(execution_receipt, dict) and execution_receipt:
        normalized_events.append(
            _runner_normalized_event_from_record(
                execution_receipt,
                fallback_event_type="runner_execution_receipt",
                fallback_status_key="receipt_status",
                source_agent_id="runner_executor",
                target_agent_id=str(execution_receipt.get("target_agent_id") or ""),
                blocking_default=not bool(execution_receipt.get("execution_allowed")),
            )
        )

    if isinstance(audit_ledger, dict) and audit_ledger:
        normalized_events.append(
            _runner_normalized_event_from_record(
                audit_ledger,
                fallback_event_type="runner_audit_ledger_dry_run",
                fallback_status_key="audit_ledger_status",
                source_agent_id="runner_auditor",
                target_agent_id=str(audit_ledger.get("target_agent_id") or ""),
                blocking_default=True,
            )
        )

    if isinstance(safety_chain_event, dict) and safety_chain_event:
        normalized_events.append(
            _runner_normalized_event_from_record(
                safety_chain_event,
                fallback_event_type="runner_real_execution_safety_chain_dry_run",
                fallback_status_key="event_status",
                source_agent_id="risk_approval_agent",
                target_agent_id="supervisor_agent",
                blocking_default=not bool(safety_chain_event.get("safe_to_continue")),
            )
        )

    if isinstance(incident_receipt, dict) and incident_receipt:
        normalized_events.append(
            _runner_normalized_event_from_record(
                incident_receipt,
                fallback_event_type="runner_real_execution_incident_receipt",
                fallback_status_key="incident_receipt_status",
                source_agent_id="incident_response_agent",
                target_agent_id="supervisor_agent",
                blocking_default=True,
            )
        )

    for index, event in enumerate(normalized_events, start=1):
        event["sequence_index"] = index
        event["project_id"] = safe_project_id

    blocking_events = [event for event in normalized_events if bool(event.get("blocking"))]
    provider_call_performed = any(bool(event.get("provider_call_performed")) for event in normalized_events)
    external_api_called = any(bool(event.get("external_api_called")) for event in normalized_events)
    agent_execution_performed = any(bool(event.get("agent_execution_performed")) for event in normalized_events)
    safe_to_continue = bool(normalized_events) and not blocking_events and not provider_call_performed and not external_api_called and not agent_execution_performed

    return {
        "runner_event_ledger_summary_version": AGENT_RUNNER_EVENT_LEDGER_SUMMARY_VERSION,
        "runner_event_ledger_summary_status": "event_ledger_recorded_safely" if normalized_events else "event_ledger_not_refreshed",
        "project_id": safe_project_id,
        "requested_by": str(requested_by or "runner_event_ledger_summary_builder"),
        "event_count": len(normalized_events),
        "blocking_event_count": len(blocking_events),
        "non_blocking_event_count": len(normalized_events) - len(blocking_events),
        "event_types": [str(event.get("event_type") or "") for event in normalized_events],
        "event_statuses": [str(event.get("event_status") or "") for event in normalized_events],
        "blocking_event_ids": [str(event.get("event_id") or "") for event in blocking_events],
        "normalized_events": normalized_events,
        "safe_to_continue": safe_to_continue,
        "manual_review_required": True,
        "dry_run": True,
        "ledger_persisted": False,
        "provider_call_performed": provider_call_performed,
        "external_api_called": external_api_called,
        "agent_execution_performed": agent_execution_performed,
        "cost_incurred_by_crossgrowth": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }





AGENT_RUNNER_WORK_ORDER_VERSION = "agent_runner_work_order_v1"


def _work_order_status_from_execution_receipt(receipt: dict[str, Any]) -> str:
    safe_receipt = receipt if isinstance(receipt, dict) else {}
    receipt_status = str(safe_receipt.get("receipt_status") or "execution_blocked")
    if bool(safe_receipt.get("execution_allowed")) and receipt_status == "execution_ready_dry_run":
        return "work_order_ready_dry_run"
    if receipt_status == "execution_waiting_for_user":
        return "work_order_waiting_for_user"
    return "work_order_blocked"


def build_agent_runner_work_order(
    runner_plan: dict[str, Any],
    dispatch_ticket: dict[str, Any],
    dispatch_event: dict[str, Any],
    execution_receipt: dict[str, Any],
    requested_by: str = "runner_work_order_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run work order for the next graph agent.

    This is a structured task package. It does not execute the agent, call
    providers, spend money, or enable autonomous LLM routing.
    """

    plan = runner_plan if isinstance(runner_plan, dict) else {}
    ticket = dispatch_ticket if isinstance(dispatch_ticket, dict) else {}
    event = dispatch_event if isinstance(dispatch_event, dict) else {}
    receipt = execution_receipt if isinstance(execution_receipt, dict) else {}

    project_id = str(
        receipt.get("project_id")
        or ticket.get("project_id")
        or event.get("project_id")
        or plan.get("project_id")
        or "demo_project_default"
    )
    target_agent_id = str(
        receipt.get("target_agent_id")
        or ticket.get("next_agent_id")
        or event.get("target_agent_id")
        or plan.get("next_agent_id")
        or ""
    )
    target_contract = get_agent_contract(target_agent_id)
    work_order_status = _work_order_status_from_execution_receipt(receipt)
    work_order_allowed = work_order_status == "work_order_ready_dry_run"
    blocking_check_ids = [
        str(item)
        for item in (
            receipt.get("blocking_check_ids")
            or ticket.get("blocking_check_ids")
            or event.get("blocking_check_ids")
            or []
        )
        if str(item or "")
    ]

    handoff_message = ticket.get("handoff_message") if isinstance(ticket.get("handoff_message"), dict) else {}
    handoff_payload = handoff_message.get("payload") if isinstance(handoff_message.get("payload"), dict) else {}

    work_payload = {
        "runner_plan_version": plan.get("runner_plan_version"),
        "dispatch_ticket_version": ticket.get("dispatch_ticket_version"),
        "dispatch_event_version": event.get("dispatch_event_version"),
        "execution_receipt_version": receipt.get("execution_receipt_version"),
        "target_agent_id": target_agent_id,
        "next_action_type": str(plan.get("next_action_type") or ticket.get("next_action_type") or ""),
        "handoff_payload": deepcopy(handoff_payload),
        "contract_input_contract": deepcopy(target_contract.get("input_contract") or []),
        "contract_output_contract": deepcopy(target_contract.get("output_contract") or []),
        "dry_run": True,
        "execution_performed": False,
    }

    work_order_message = build_agent_message(
        message_type="runner_work_order_dry_run",
        source_agent_id="runner_work_order_builder",
        target_agent_id=target_agent_id,
        payload=work_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "work_order_version": AGENT_RUNNER_WORK_ORDER_VERSION,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_work_order_dry_run_api"),
        "work_order_status": work_order_status,
        "work_order_allowed": work_order_allowed,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(target_contract.get("stage") or ""),
        "target_agent_display_name": str(target_contract.get("display_name") or target_agent_id),
        "next_action_type": str(plan.get("next_action_type") or ticket.get("next_action_type") or ""),
        "recommended_next_state": str(receipt.get("recommended_next_state") or ""),
        "required_inputs": deepcopy(target_contract.get("input_contract") or []),
        "expected_outputs": deepcopy(target_contract.get("output_contract") or []),
        "handoff_artifact_types": deepcopy(target_contract.get("handoff_artifact_types") or []),
        "allowed_next_agent_ids": deepcopy(target_contract.get("allowed_next_agent_ids") or []),
        "blocking_check_ids": blocking_check_ids,
        "runner_plan_summary": build_agent_runner_plan_summary(plan),
        "dispatch_summary": build_agent_runner_dispatch_summary(ticket),
        "dispatch_event_summary": build_agent_runner_dispatch_event_summary(event),
        "execution_receipt_summary": build_agent_runner_execution_receipt_summary(receipt),
        "handoff_message": deepcopy(handoff_message),
        "contract_validation": deepcopy(ticket.get("contract_validation") or event.get("contract_validation") or receipt.get("contract_validation") or {}),
        "work_payload": work_payload,
        "work_order_message": work_order_message,
        "dry_run": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_work_order_summary(work_order: dict[str, Any]) -> dict[str, Any]:
    safe_order = work_order if isinstance(work_order, dict) else {}
    return {
        "summary_version": "agent_runner_work_order_summary_v1",
        "work_order_version": str(safe_order.get("work_order_version") or AGENT_RUNNER_WORK_ORDER_VERSION),
        "project_id": str(safe_order.get("project_id") or "demo_project_default"),
        "work_order_status": str(safe_order.get("work_order_status") or "work_order_blocked"),
        "work_order_allowed": bool(safe_order.get("work_order_allowed")),
        "target_agent_id": str(safe_order.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_order.get("target_agent_stage") or ""),
        "required_input_count": len(safe_order.get("required_inputs") or []),
        "expected_output_count": len(safe_order.get("expected_outputs") or []),
        "blocking_check_count": len(safe_order.get("blocking_check_ids") or []),
        "dry_run": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_QUEUE_ITEM_VERSION = "agent_runner_queue_item_v1"


def _queue_status_from_work_order(work_order: dict[str, Any]) -> str:
    safe_order = work_order if isinstance(work_order, dict) else {}
    status = str(safe_order.get("work_order_status") or "work_order_blocked")
    if bool(safe_order.get("work_order_allowed")) and status == "work_order_ready_dry_run":
        return "queue_ready_dry_run"
    if status == "work_order_waiting_for_user":
        return "queue_waiting_for_user"
    return "queue_blocked"


def build_agent_runner_queue_item(
    work_order: dict[str, Any],
    requested_by: str = "runner_queue_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run queue item from an Agent work order.

    This does not persist a queue record, execute the agent, call providers,
    spend money, or enable autonomous LLM routing.
    """

    order = work_order if isinstance(work_order, dict) else {}
    project_id = str(order.get("project_id") or "demo_project_default")
    target_agent_id = str(order.get("target_agent_id") or "")
    queue_status = _queue_status_from_work_order(order)
    enqueue_allowed = queue_status == "queue_ready_dry_run"
    queue_item_id = f"queue_item_{project_id}_{target_agent_id or 'none'}_{queue_status}".replace(" ", "_")

    blocking_check_ids = [
        str(item)
        for item in (order.get("blocking_check_ids") or [])
        if str(item or "")
    ]

    if enqueue_allowed:
        recommended_next_state = "ready_for_explicit_queue_persistence"
        queue_message_text = "Dry-run queue item is ready. Real queue persistence is still disabled until explicit execution mode is implemented."
    elif queue_status == "queue_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        queue_message_text = "Queue item is waiting for required user action."
    else:
        recommended_next_state = "fix_queue_blockers"
        queue_message_text = "Queue item is blocked by work order, execution receipt, dispatch, or contract validation."

    queue_payload = {
        "queue_item_version": AGENT_RUNNER_QUEUE_ITEM_VERSION,
        "queue_status": queue_status,
        "enqueue_allowed": enqueue_allowed,
        "target_agent_id": target_agent_id,
        "target_agent_stage": order.get("target_agent_stage"),
        "work_order_version": order.get("work_order_version"),
        "work_order_status": order.get("work_order_status"),
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "queue_persisted": False,
        "agent_execution_performed": False,
    }

    queue_message = build_agent_message(
        message_type="runner_queue_item_dry_run",
        source_agent_id="runner_queue_manager",
        target_agent_id=target_agent_id,
        payload=queue_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "queue_item_version": AGENT_RUNNER_QUEUE_ITEM_VERSION,
        "queue_item_id": queue_item_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_queue_dry_run_api"),
        "queue_status": queue_status,
        "enqueue_allowed": enqueue_allowed,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(order.get("target_agent_stage") or ""),
        "target_agent_display_name": str(order.get("target_agent_display_name") or target_agent_id),
        "priority": "normal",
        "recommended_next_state": recommended_next_state,
        "queue_message_text": queue_message_text,
        "blocking_check_ids": blocking_check_ids,
        "work_order_version": str(order.get("work_order_version") or ""),
        "work_order_status": str(order.get("work_order_status") or ""),
        "work_order_allowed": bool(order.get("work_order_allowed")),
        "work_order_summary": build_agent_runner_work_order_summary(order),
        "required_inputs": deepcopy(order.get("required_inputs") or []),
        "expected_outputs": deepcopy(order.get("expected_outputs") or []),
        "work_payload": deepcopy(order.get("work_payload") or {}),
        "work_order_message": deepcopy(order.get("work_order_message") or {}),
        "queue_message": queue_message,
        "dry_run": True,
        "queue_persisted": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_queue_item_summary(queue_item: dict[str, Any]) -> dict[str, Any]:
    safe_item = queue_item if isinstance(queue_item, dict) else {}
    return {
        "summary_version": "agent_runner_queue_item_summary_v1",
        "queue_item_version": str(safe_item.get("queue_item_version") or AGENT_RUNNER_QUEUE_ITEM_VERSION),
        "queue_item_id": str(safe_item.get("queue_item_id") or ""),
        "project_id": str(safe_item.get("project_id") or "demo_project_default"),
        "queue_status": str(safe_item.get("queue_status") or "queue_blocked"),
        "enqueue_allowed": bool(safe_item.get("enqueue_allowed")),
        "target_agent_id": str(safe_item.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_item.get("target_agent_stage") or ""),
        "priority": str(safe_item.get("priority") or "normal"),
        "blocking_check_count": len(safe_item.get("blocking_check_ids") or []),
        "dry_run": True,
        "queue_persisted": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_QUEUE_CLAIM_VERSION = "agent_runner_queue_claim_v1"


def _claim_status_from_queue_item(queue_item: dict[str, Any]) -> str:
    safe_item = queue_item if isinstance(queue_item, dict) else {}
    status = str(safe_item.get("queue_status") or "queue_blocked")
    if bool(safe_item.get("enqueue_allowed")) and status == "queue_ready_dry_run":
        return "claim_ready_dry_run"
    if status == "queue_waiting_for_user":
        return "claim_waiting_for_user"
    return "claim_blocked"


def build_agent_runner_queue_claim(
    queue_item: dict[str, Any],
    worker_id: str = "runner_worker_dry_run",
    requested_by: str = "runner_claim_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run worker claim for a queue item.

    This does not persist a claim, acquire a real lock, execute the agent,
    call providers, spend money, or enable autonomous LLM routing.
    """

    item = queue_item if isinstance(queue_item, dict) else {}
    project_id = str(item.get("project_id") or "demo_project_default")
    target_agent_id = str(item.get("target_agent_id") or "")
    safe_worker_id = str(worker_id or "runner_worker_dry_run")
    claim_status = _claim_status_from_queue_item(item)
    claim_allowed = claim_status == "claim_ready_dry_run"
    claim_id = f"claim_{project_id}_{target_agent_id or 'none'}_{safe_worker_id}_{claim_status}".replace(" ", "_")

    blocking_check_ids = [
        str(value)
        for value in (item.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if claim_allowed:
        recommended_next_state = "ready_for_explicit_worker_lease"
        claim_message_text = "Dry-run worker claim is ready. Real queue lock acquisition is still disabled."
    elif claim_status == "claim_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        claim_message_text = "Worker claim is waiting for required user action."
    else:
        recommended_next_state = "fix_claim_blockers"
        claim_message_text = "Worker claim is blocked by queue item, work order, execution receipt, dispatch, or contract validation."

    lease_payload = {
        "claim_version": AGENT_RUNNER_QUEUE_CLAIM_VERSION,
        "claim_status": claim_status,
        "claim_allowed": claim_allowed,
        "claim_id": claim_id,
        "worker_id": safe_worker_id,
        "queue_item_id": item.get("queue_item_id"),
        "target_agent_id": target_agent_id,
        "target_agent_stage": item.get("target_agent_stage"),
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "claim_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
    }

    claim_message = build_agent_message(
        message_type="runner_queue_claim_dry_run",
        source_agent_id="runner_queue_worker",
        target_agent_id=target_agent_id,
        payload=lease_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "claim_version": AGENT_RUNNER_QUEUE_CLAIM_VERSION,
        "claim_id": claim_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_claim_dry_run_api"),
        "worker_id": safe_worker_id,
        "claim_status": claim_status,
        "claim_allowed": claim_allowed,
        "queue_item_id": str(item.get("queue_item_id") or ""),
        "queue_item_version": str(item.get("queue_item_version") or ""),
        "queue_status": str(item.get("queue_status") or ""),
        "enqueue_allowed": bool(item.get("enqueue_allowed")),
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(item.get("target_agent_stage") or ""),
        "priority": str(item.get("priority") or "normal"),
        "recommended_next_state": recommended_next_state,
        "claim_message_text": claim_message_text,
        "blocking_check_ids": blocking_check_ids,
        "queue_item_summary": build_agent_runner_queue_item_summary(item),
        "work_order_summary": deepcopy(item.get("work_order_summary") or {}),
        "required_inputs": deepcopy(item.get("required_inputs") or []),
        "expected_outputs": deepcopy(item.get("expected_outputs") or []),
        "work_payload": deepcopy(item.get("work_payload") or {}),
        "queue_message": deepcopy(item.get("queue_message") or {}),
        "claim_message": claim_message,
        "dry_run": True,
        "claim_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_queue_claim_summary(queue_claim: dict[str, Any]) -> dict[str, Any]:
    safe_claim = queue_claim if isinstance(queue_claim, dict) else {}
    return {
        "summary_version": "agent_runner_queue_claim_summary_v1",
        "claim_version": str(safe_claim.get("claim_version") or AGENT_RUNNER_QUEUE_CLAIM_VERSION),
        "claim_id": str(safe_claim.get("claim_id") or ""),
        "project_id": str(safe_claim.get("project_id") or "demo_project_default"),
        "worker_id": str(safe_claim.get("worker_id") or "runner_worker_dry_run"),
        "claim_status": str(safe_claim.get("claim_status") or "claim_blocked"),
        "claim_allowed": bool(safe_claim.get("claim_allowed")),
        "target_agent_id": str(safe_claim.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_claim.get("target_agent_stage") or ""),
        "queue_item_id": str(safe_claim.get("queue_item_id") or ""),
        "blocking_check_count": len(safe_claim.get("blocking_check_ids") or []),
        "dry_run": True,
        "claim_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_WORKER_LEASE_VERSION = "agent_runner_worker_lease_v1"


def _worker_lease_status_from_claim(queue_claim: dict[str, Any]) -> str:
    safe_claim = queue_claim if isinstance(queue_claim, dict) else {}
    status = str(safe_claim.get("claim_status") or "claim_blocked")
    if bool(safe_claim.get("claim_allowed")) and status == "claim_ready_dry_run":
        return "lease_ready_dry_run"
    if status == "claim_waiting_for_user":
        return "lease_waiting_for_user"
    return "lease_blocked"


def build_agent_runner_worker_lease(
    queue_claim: dict[str, Any],
    lease_seconds: int = 300,
    requested_by: str = "runner_lease_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run worker lease for a queue claim.

    This does not acquire a real lease, persist a lock, execute the agent,
    call providers, spend money, or enable autonomous LLM routing.
    """

    claim = queue_claim if isinstance(queue_claim, dict) else {}
    project_id = str(claim.get("project_id") or "demo_project_default")
    target_agent_id = str(claim.get("target_agent_id") or "")
    worker_id = str(claim.get("worker_id") or "runner_worker_dry_run")
    lease_status = _worker_lease_status_from_claim(claim)
    lease_allowed = lease_status == "lease_ready_dry_run"
    safe_seconds = max(30, min(int(lease_seconds or 300), 3600))
    lease_id = f"lease_{project_id}_{target_agent_id or 'none'}_{worker_id}_{lease_status}".replace(" ", "_")
    lease_token = f"dry_run_token::{lease_id}"

    blocking_check_ids = [
        str(value)
        for value in (claim.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if lease_allowed:
        recommended_next_state = "ready_for_explicit_agent_invocation_dry_run"
        lease_message_text = "Dry-run worker lease is ready. Real lock persistence and Agent execution are still disabled."
    elif lease_status == "lease_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        lease_message_text = "Worker lease is waiting for required user action."
    else:
        recommended_next_state = "fix_lease_blockers"
        lease_message_text = "Worker lease is blocked by claim, queue item, work order, execution receipt, dispatch, or contract validation."

    lease_payload = {
        "worker_lease_version": AGENT_RUNNER_WORKER_LEASE_VERSION,
        "lease_status": lease_status,
        "lease_allowed": lease_allowed,
        "lease_id": lease_id,
        "lease_token": lease_token,
        "lease_seconds": safe_seconds,
        "worker_id": worker_id,
        "claim_id": claim.get("claim_id"),
        "queue_item_id": claim.get("queue_item_id"),
        "target_agent_id": target_agent_id,
        "target_agent_stage": claim.get("target_agent_stage"),
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "lease_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
    }

    lease_message = build_agent_message(
        message_type="runner_worker_lease_dry_run",
        source_agent_id="runner_lease_manager",
        target_agent_id=target_agent_id,
        payload=lease_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "worker_lease_version": AGENT_RUNNER_WORKER_LEASE_VERSION,
        "lease_id": lease_id,
        "lease_token": lease_token,
        "lease_seconds": safe_seconds,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_lease_dry_run_api"),
        "worker_id": worker_id,
        "lease_status": lease_status,
        "lease_allowed": lease_allowed,
        "claim_id": str(claim.get("claim_id") or ""),
        "claim_version": str(claim.get("claim_version") or ""),
        "claim_status": str(claim.get("claim_status") or ""),
        "claim_allowed": bool(claim.get("claim_allowed")),
        "queue_item_id": str(claim.get("queue_item_id") or ""),
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(claim.get("target_agent_stage") or ""),
        "priority": str(claim.get("priority") or "normal"),
        "recommended_next_state": recommended_next_state,
        "lease_message_text": lease_message_text,
        "blocking_check_ids": blocking_check_ids,
        "queue_claim_summary": build_agent_runner_queue_claim_summary(claim),
        "queue_item_summary": deepcopy(claim.get("queue_item_summary") or {}),
        "work_order_summary": deepcopy(claim.get("work_order_summary") or {}),
        "required_inputs": deepcopy(claim.get("required_inputs") or []),
        "expected_outputs": deepcopy(claim.get("expected_outputs") or []),
        "work_payload": deepcopy(claim.get("work_payload") or {}),
        "claim_message": deepcopy(claim.get("claim_message") or {}),
        "lease_message": lease_message,
        "dry_run": True,
        "lease_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_lease_summary(worker_lease: dict[str, Any]) -> dict[str, Any]:
    safe_lease = worker_lease if isinstance(worker_lease, dict) else {}
    return {
        "summary_version": "agent_runner_worker_lease_summary_v1",
        "worker_lease_version": str(safe_lease.get("worker_lease_version") or AGENT_RUNNER_WORKER_LEASE_VERSION),
        "lease_id": str(safe_lease.get("lease_id") or ""),
        "project_id": str(safe_lease.get("project_id") or "demo_project_default"),
        "worker_id": str(safe_lease.get("worker_id") or "runner_worker_dry_run"),
        "lease_status": str(safe_lease.get("lease_status") or "lease_blocked"),
        "lease_allowed": bool(safe_lease.get("lease_allowed")),
        "target_agent_id": str(safe_lease.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_lease.get("target_agent_stage") or ""),
        "claim_id": str(safe_lease.get("claim_id") or ""),
        "queue_item_id": str(safe_lease.get("queue_item_id") or ""),
        "lease_seconds": int(safe_lease.get("lease_seconds") or 300),
        "blocking_check_count": len(safe_lease.get("blocking_check_ids") or []),
        "dry_run": True,
        "lease_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_INVOCATION_ENVELOPE_VERSION = "agent_runner_invocation_envelope_v1"
AGENT_RUNNER_INVOCATION_ATTEMPT_VERSION = "agent_runner_invocation_attempt_v1"


def _invocation_envelope_status_from_lease(worker_lease: dict[str, Any]) -> str:
    safe_lease = worker_lease if isinstance(worker_lease, dict) else {}
    status = str(safe_lease.get("lease_status") or "lease_blocked")
    if bool(safe_lease.get("lease_allowed")) and status == "lease_ready_dry_run":
        return "invocation_ready_dry_run"
    if status == "lease_waiting_for_user":
        return "invocation_waiting_for_user"
    return "invocation_blocked"


def build_agent_runner_invocation_envelope(
    worker_lease: dict[str, Any],
    requested_by: str = "runner_invoke_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run invocation envelope for the next Agent.

    This packages the inputs for a future Agent call. It does not invoke the
    Agent, call providers, spend money, or enable autonomous LLM routing.
    """

    lease = worker_lease if isinstance(worker_lease, dict) else {}
    project_id = str(lease.get("project_id") or "demo_project_default")
    target_agent_id = str(lease.get("target_agent_id") or "")
    envelope_status = _invocation_envelope_status_from_lease(lease)
    invocation_allowed = envelope_status == "invocation_ready_dry_run"
    envelope_id = f"invocation_envelope_{project_id}_{target_agent_id or 'none'}_{envelope_status}".replace(" ", "_")
    idempotency_key = f"dry_run_idempotency::{envelope_id}"

    target_contract = get_agent_contract(target_agent_id)
    blocking_check_ids = [
        str(value)
        for value in (lease.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if invocation_allowed:
        recommended_next_state = "ready_for_explicit_agent_call_attempt"
        envelope_message_text = "Dry-run invocation envelope is ready. Real Agent calls are still disabled."
    elif envelope_status == "invocation_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        envelope_message_text = "Invocation envelope is waiting for required user action."
    else:
        recommended_next_state = "fix_invocation_blockers"
        envelope_message_text = "Invocation envelope is blocked by lease, claim, queue, work order, execution receipt, dispatch, or contract validation."

    invocation_payload = {
        "invocation_envelope_version": AGENT_RUNNER_INVOCATION_ENVELOPE_VERSION,
        "envelope_status": envelope_status,
        "invocation_allowed": invocation_allowed,
        "envelope_id": envelope_id,
        "idempotency_key": idempotency_key,
        "lease_id": lease.get("lease_id"),
        "lease_token": lease.get("lease_token"),
        "worker_id": lease.get("worker_id"),
        "target_agent_id": target_agent_id,
        "target_agent_stage": lease.get("target_agent_stage"),
        "input_contract": deepcopy(target_contract.get("input_contract") or []),
        "output_contract": deepcopy(target_contract.get("output_contract") or []),
        "required_inputs": deepcopy(lease.get("required_inputs") or []),
        "expected_outputs": deepcopy(lease.get("expected_outputs") or []),
        "work_payload": deepcopy(lease.get("work_payload") or {}),
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
    }

    envelope_message = build_agent_message(
        message_type="runner_invocation_envelope_dry_run",
        source_agent_id="runner_invocation_manager",
        target_agent_id=target_agent_id,
        payload=invocation_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "invocation_envelope_version": AGENT_RUNNER_INVOCATION_ENVELOPE_VERSION,
        "envelope_id": envelope_id,
        "idempotency_key": idempotency_key,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_invoke_dry_run_api"),
        "envelope_status": envelope_status,
        "invocation_allowed": invocation_allowed,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(lease.get("target_agent_stage") or ""),
        "target_agent_display_name": str(target_contract.get("display_name") or lease.get("target_agent_display_name") or target_agent_id),
        "worker_id": str(lease.get("worker_id") or "runner_worker_dry_run"),
        "lease_id": str(lease.get("lease_id") or ""),
        "lease_status": str(lease.get("lease_status") or ""),
        "lease_allowed": bool(lease.get("lease_allowed")),
        "claim_id": str(lease.get("claim_id") or ""),
        "queue_item_id": str(lease.get("queue_item_id") or ""),
        "recommended_next_state": recommended_next_state,
        "envelope_message_text": envelope_message_text,
        "blocking_check_ids": blocking_check_ids,
        "input_contract": deepcopy(target_contract.get("input_contract") or []),
        "output_contract": deepcopy(target_contract.get("output_contract") or []),
        "required_inputs": deepcopy(lease.get("required_inputs") or []),
        "expected_outputs": deepcopy(lease.get("expected_outputs") or []),
        "work_payload": deepcopy(lease.get("work_payload") or {}),
        "worker_lease_summary": build_agent_runner_worker_lease_summary(lease),
        "queue_claim_summary": deepcopy(lease.get("queue_claim_summary") or {}),
        "queue_item_summary": deepcopy(lease.get("queue_item_summary") or {}),
        "work_order_summary": deepcopy(lease.get("work_order_summary") or {}),
        "lease_message": deepcopy(lease.get("lease_message") or {}),
        "invocation_payload": invocation_payload,
        "invocation_message": envelope_message,
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_invocation_envelope_summary(envelope: dict[str, Any]) -> dict[str, Any]:
    safe_envelope = envelope if isinstance(envelope, dict) else {}
    return {
        "summary_version": "agent_runner_invocation_envelope_summary_v1",
        "invocation_envelope_version": str(safe_envelope.get("invocation_envelope_version") or AGENT_RUNNER_INVOCATION_ENVELOPE_VERSION),
        "envelope_id": str(safe_envelope.get("envelope_id") or ""),
        "project_id": str(safe_envelope.get("project_id") or "demo_project_default"),
        "envelope_status": str(safe_envelope.get("envelope_status") or "invocation_blocked"),
        "invocation_allowed": bool(safe_envelope.get("invocation_allowed")),
        "target_agent_id": str(safe_envelope.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_envelope.get("target_agent_stage") or ""),
        "worker_id": str(safe_envelope.get("worker_id") or "runner_worker_dry_run"),
        "lease_id": str(safe_envelope.get("lease_id") or ""),
        "blocking_check_count": len(safe_envelope.get("blocking_check_ids") or []),
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _invocation_attempt_status_from_envelope(envelope: dict[str, Any]) -> str:
    safe_envelope = envelope if isinstance(envelope, dict) else {}
    status = str(safe_envelope.get("envelope_status") or "invocation_blocked")
    if bool(safe_envelope.get("invocation_allowed")) and status == "invocation_ready_dry_run":
        return "attempt_ready_dry_run"
    if status == "invocation_waiting_for_user":
        return "attempt_waiting_for_user"
    return "attempt_blocked"


def build_agent_runner_invocation_attempt(
    invocation_envelope: dict[str, Any],
    requested_by: str = "runner_invoke_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run invocation attempt.

    This records the decision to prepare an Agent call. It does not call the
    Agent, call external providers, spend money, or let an LLM route itself.
    """

    envelope = invocation_envelope if isinstance(invocation_envelope, dict) else {}
    project_id = str(envelope.get("project_id") or "demo_project_default")
    target_agent_id = str(envelope.get("target_agent_id") or "")
    attempt_status = _invocation_attempt_status_from_envelope(envelope)
    attempt_allowed = attempt_status == "attempt_ready_dry_run"
    attempt_id = f"invocation_attempt_{project_id}_{target_agent_id or 'none'}_{attempt_status}".replace(" ", "_")

    blocking_check_ids = [
        str(value)
        for value in (envelope.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if attempt_allowed:
        recommended_next_state = "ready_for_real_agent_invocation_feature_flag"
        attempt_message_text = "Dry-run invocation attempt is ready. Real Agent invocation still requires an explicit feature flag and implementation."
    elif attempt_status == "attempt_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        attempt_message_text = "Invocation attempt is waiting for required user action."
    else:
        recommended_next_state = "fix_invocation_attempt_blockers"
        attempt_message_text = "Invocation attempt is blocked by invocation envelope or upstream safety checks."

    attempt_payload = {
        "invocation_attempt_version": AGENT_RUNNER_INVOCATION_ATTEMPT_VERSION,
        "attempt_status": attempt_status,
        "attempt_allowed": attempt_allowed,
        "attempt_id": attempt_id,
        "envelope_id": envelope.get("envelope_id"),
        "idempotency_key": envelope.get("idempotency_key"),
        "target_agent_id": target_agent_id,
        "target_agent_stage": envelope.get("target_agent_stage"),
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
    }

    attempt_message = build_agent_message(
        message_type="runner_invocation_attempt_dry_run",
        source_agent_id="runner_invocation_manager",
        target_agent_id=target_agent_id,
        payload=attempt_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "invocation_attempt_version": AGENT_RUNNER_INVOCATION_ATTEMPT_VERSION,
        "attempt_id": attempt_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_invoke_dry_run_api"),
        "attempt_status": attempt_status,
        "attempt_allowed": attempt_allowed,
        "envelope_id": str(envelope.get("envelope_id") or ""),
        "idempotency_key": str(envelope.get("idempotency_key") or ""),
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(envelope.get("target_agent_stage") or ""),
        "worker_id": str(envelope.get("worker_id") or "runner_worker_dry_run"),
        "lease_id": str(envelope.get("lease_id") or ""),
        "recommended_next_state": recommended_next_state,
        "attempt_message_text": attempt_message_text,
        "blocking_check_ids": blocking_check_ids,
        "invocation_envelope_summary": build_agent_runner_invocation_envelope_summary(envelope),
        "invocation_payload": deepcopy(envelope.get("invocation_payload") or {}),
        "invocation_message": deepcopy(envelope.get("invocation_message") or {}),
        "attempt_message": attempt_message,
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_invocation_attempt_summary(attempt: dict[str, Any]) -> dict[str, Any]:
    safe_attempt = attempt if isinstance(attempt, dict) else {}
    return {
        "summary_version": "agent_runner_invocation_attempt_summary_v1",
        "invocation_attempt_version": str(safe_attempt.get("invocation_attempt_version") or AGENT_RUNNER_INVOCATION_ATTEMPT_VERSION),
        "attempt_id": str(safe_attempt.get("attempt_id") or ""),
        "project_id": str(safe_attempt.get("project_id") or "demo_project_default"),
        "attempt_status": str(safe_attempt.get("attempt_status") or "attempt_blocked"),
        "attempt_allowed": bool(safe_attempt.get("attempt_allowed")),
        "target_agent_id": str(safe_attempt.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_attempt.get("target_agent_stage") or ""),
        "envelope_id": str(safe_attempt.get("envelope_id") or ""),
        "worker_id": str(safe_attempt.get("worker_id") or "runner_worker_dry_run"),
        "blocking_check_count": len(safe_attempt.get("blocking_check_ids") or []),
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_INVOCATION_RESULT_VERSION = "agent_runner_invocation_result_v1"
AGENT_RUNNER_COMPLETION_RECEIPT_VERSION = "agent_runner_completion_receipt_v1"


def _invocation_result_status_from_attempt(invocation_attempt: dict[str, Any]) -> str:
    safe_attempt = invocation_attempt if isinstance(invocation_attempt, dict) else {}
    status = str(safe_attempt.get("attempt_status") or "attempt_blocked")
    if bool(safe_attempt.get("attempt_allowed")) and status == "attempt_ready_dry_run":
        return "result_ready_dry_run"
    if status == "attempt_waiting_for_user":
        return "result_waiting_for_user"
    return "result_blocked"


def build_agent_runner_invocation_result(
    invocation_attempt: dict[str, Any],
    requested_by: str = "runner_result_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run result receipt for an invocation attempt.

    This does not invoke an Agent, generate Agent output, persist output,
    call providers, spend money, or enable autonomous LLM routing.
    """

    attempt = invocation_attempt if isinstance(invocation_attempt, dict) else {}
    project_id = str(attempt.get("project_id") or "demo_project_default")
    target_agent_id = str(attempt.get("target_agent_id") or "")
    result_status = _invocation_result_status_from_attempt(attempt)
    result_allowed = result_status == "result_ready_dry_run"
    result_id = f"invocation_result_{project_id}_{target_agent_id or 'none'}_{result_status}".replace(" ", "_")

    target_contract = get_agent_contract(target_agent_id)
    expected_outputs = deepcopy(target_contract.get("output_contract") or [])
    blocking_check_ids = [
        str(value)
        for value in (attempt.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if result_allowed:
        recommended_next_state = "wait_for_real_agent_output"
        result_message_text = "Dry-run result shell is ready. Real Agent output is not generated in dry-run mode."
    elif result_status == "result_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        result_message_text = "Invocation result is waiting for required user action."
    else:
        recommended_next_state = "fix_result_blockers"
        result_message_text = "Invocation result is blocked by attempt, envelope, lease, claim, queue, work order, execution receipt, dispatch, or contract validation."

    output_contract_check = {
        "check_version": "agent_runner_output_contract_check_v1",
        "target_agent_id": target_agent_id,
        "expected_outputs": expected_outputs,
        "expected_output_count": len(expected_outputs),
        "agent_output_generated": False,
        "actual_outputs": [],
        "missing_outputs": expected_outputs,
        "contract_satisfied": False,
        "dry_run": True,
    }

    result_payload = {
        "invocation_result_version": AGENT_RUNNER_INVOCATION_RESULT_VERSION,
        "result_status": result_status,
        "result_allowed": result_allowed,
        "result_id": result_id,
        "attempt_id": attempt.get("attempt_id"),
        "envelope_id": attempt.get("envelope_id"),
        "target_agent_id": target_agent_id,
        "target_agent_stage": attempt.get("target_agent_stage"),
        "output_contract_check": output_contract_check,
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "agent_output_generated": False,
        "result_persisted": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
    }

    result_message = build_agent_message(
        message_type="runner_invocation_result_dry_run",
        source_agent_id="runner_result_manager",
        target_agent_id=target_agent_id,
        payload=result_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "invocation_result_version": AGENT_RUNNER_INVOCATION_RESULT_VERSION,
        "result_id": result_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_result_dry_run_api"),
        "result_status": result_status,
        "result_allowed": result_allowed,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(attempt.get("target_agent_stage") or ""),
        "attempt_id": str(attempt.get("attempt_id") or ""),
        "attempt_status": str(attempt.get("attempt_status") or ""),
        "attempt_allowed": bool(attempt.get("attempt_allowed")),
        "envelope_id": str(attempt.get("envelope_id") or ""),
        "worker_id": str(attempt.get("worker_id") or "runner_worker_dry_run"),
        "lease_id": str(attempt.get("lease_id") or ""),
        "recommended_next_state": recommended_next_state,
        "result_message_text": result_message_text,
        "blocking_check_ids": blocking_check_ids,
        "expected_outputs": expected_outputs,
        "output_contract_check": output_contract_check,
        "invocation_attempt_summary": build_agent_runner_invocation_attempt_summary(attempt),
        "invocation_envelope_summary": deepcopy(attempt.get("invocation_envelope_summary") or {}),
        "invocation_payload": deepcopy(attempt.get("invocation_payload") or {}),
        "attempt_message": deepcopy(attempt.get("attempt_message") or {}),
        "result_payload": result_payload,
        "result_message": result_message,
        "dry_run": True,
        "agent_output_generated": False,
        "result_persisted": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_invocation_result_summary(invocation_result: dict[str, Any]) -> dict[str, Any]:
    safe_result = invocation_result if isinstance(invocation_result, dict) else {}
    output_check = safe_result.get("output_contract_check") if isinstance(safe_result.get("output_contract_check"), dict) else {}
    return {
        "summary_version": "agent_runner_invocation_result_summary_v1",
        "invocation_result_version": str(safe_result.get("invocation_result_version") or AGENT_RUNNER_INVOCATION_RESULT_VERSION),
        "result_id": str(safe_result.get("result_id") or ""),
        "project_id": str(safe_result.get("project_id") or "demo_project_default"),
        "result_status": str(safe_result.get("result_status") or "result_blocked"),
        "result_allowed": bool(safe_result.get("result_allowed")),
        "target_agent_id": str(safe_result.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_result.get("target_agent_stage") or ""),
        "attempt_id": str(safe_result.get("attempt_id") or ""),
        "expected_output_count": int(output_check.get("expected_output_count") or 0),
        "contract_satisfied": bool(output_check.get("contract_satisfied")),
        "blocking_check_count": len(safe_result.get("blocking_check_ids") or []),
        "dry_run": True,
        "agent_output_generated": False,
        "result_persisted": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _completion_status_from_result(invocation_result: dict[str, Any]) -> str:
    safe_result = invocation_result if isinstance(invocation_result, dict) else {}
    status = str(safe_result.get("result_status") or "result_blocked")
    if status == "result_ready_dry_run":
        return "completion_waiting_for_real_agent_output"
    if status == "result_waiting_for_user":
        return "completion_waiting_for_user"
    return "completion_blocked"


def build_agent_runner_completion_receipt(
    invocation_result: dict[str, Any],
    requested_by: str = "runner_completion_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run completion receipt from an invocation result.

    In dry-run mode, no real Agent output exists, so a ready result still
    becomes a completion receipt that waits for real Agent output.
    """

    result = invocation_result if isinstance(invocation_result, dict) else {}
    project_id = str(result.get("project_id") or "demo_project_default")
    target_agent_id = str(result.get("target_agent_id") or "")
    completion_status = _completion_status_from_result(result)
    completion_id = f"completion_receipt_{project_id}_{target_agent_id or 'none'}_{completion_status}".replace(" ", "_")

    output_check = result.get("output_contract_check") if isinstance(result.get("output_contract_check"), dict) else {}
    blocking_check_ids = [
        str(value)
        for value in (result.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if completion_status == "completion_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_under_feature_flag"
        completion_message_text = "Dry-run chain is structurally ready, but completion requires real Agent output."
    elif completion_status == "completion_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        completion_message_text = "Completion is waiting for required user action."
    else:
        recommended_next_state = "fix_completion_blockers"
        completion_message_text = "Completion is blocked by result, attempt, envelope, lease, claim, queue, work order, execution receipt, dispatch, or contract validation."

    completion_payload = {
        "completion_receipt_version": AGENT_RUNNER_COMPLETION_RECEIPT_VERSION,
        "completion_status": completion_status,
        "completion_id": completion_id,
        "target_agent_id": target_agent_id,
        "result_id": result.get("result_id"),
        "output_contract_check": output_check,
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "completion_recorded": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
    }

    completion_message = build_agent_message(
        message_type="runner_completion_receipt_dry_run",
        source_agent_id="runner_completion_manager",
        target_agent_id=target_agent_id,
        payload=completion_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "completion_receipt_version": AGENT_RUNNER_COMPLETION_RECEIPT_VERSION,
        "completion_id": completion_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_completion_dry_run_api"),
        "completion_status": completion_status,
        "completion_allowed": False,
        "handoff_complete": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(result.get("target_agent_stage") or ""),
        "result_id": str(result.get("result_id") or ""),
        "result_status": str(result.get("result_status") or ""),
        "result_allowed": bool(result.get("result_allowed")),
        "attempt_id": str(result.get("attempt_id") or ""),
        "recommended_next_state": recommended_next_state,
        "completion_message_text": completion_message_text,
        "blocking_check_ids": blocking_check_ids,
        "output_contract_check": deepcopy(output_check),
        "invocation_result_summary": build_agent_runner_invocation_result_summary(result),
        "completion_payload": completion_payload,
        "completion_message": completion_message,
        "dry_run": True,
        "completion_recorded": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_completion_receipt_summary(completion_receipt: dict[str, Any]) -> dict[str, Any]:
    safe_receipt = completion_receipt if isinstance(completion_receipt, dict) else {}
    return {
        "summary_version": "agent_runner_completion_receipt_summary_v1",
        "completion_receipt_version": str(safe_receipt.get("completion_receipt_version") or AGENT_RUNNER_COMPLETION_RECEIPT_VERSION),
        "completion_id": str(safe_receipt.get("completion_id") or ""),
        "project_id": str(safe_receipt.get("project_id") or "demo_project_default"),
        "completion_status": str(safe_receipt.get("completion_status") or "completion_blocked"),
        "completion_allowed": bool(safe_receipt.get("completion_allowed")),
        "handoff_complete": bool(safe_receipt.get("handoff_complete")),
        "target_agent_id": str(safe_receipt.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_receipt.get("target_agent_stage") or ""),
        "result_id": str(safe_receipt.get("result_id") or ""),
        "blocking_check_count": len(safe_receipt.get("blocking_check_ids") or []),
        "dry_run": True,
        "completion_recorded": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_HANDOFF_CHECKPOINT_VERSION = "agent_runner_handoff_checkpoint_v1"
AGENT_RUNNER_NEXT_AGENT_UNLOCK_VERSION = "agent_runner_next_agent_unlock_v1"


def _handoff_checkpoint_status_from_completion(completion_receipt: dict[str, Any]) -> str:
    safe_receipt = completion_receipt if isinstance(completion_receipt, dict) else {}
    status = str(safe_receipt.get("completion_status") or "completion_blocked")
    if status == "completion_waiting_for_real_agent_output":
        return "checkpoint_waiting_for_real_agent_output"
    if status == "completion_waiting_for_user":
        return "checkpoint_waiting_for_user"
    return "checkpoint_blocked"


def build_agent_runner_handoff_checkpoint(
    completion_receipt: dict[str, Any],
    requested_by: str = "runner_checkpoint_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run handoff checkpoint from a completion receipt.

    This summarizes the graph handoff state. It does not mark the handoff
    complete, unlock the next Agent, call providers, spend money, or enable
    autonomous LLM routing.
    """

    receipt = completion_receipt if isinstance(completion_receipt, dict) else {}
    project_id = str(receipt.get("project_id") or "demo_project_default")
    target_agent_id = str(receipt.get("target_agent_id") or "")
    checkpoint_status = _handoff_checkpoint_status_from_completion(receipt)
    checkpoint_id = f"handoff_checkpoint_{project_id}_{target_agent_id or 'none'}_{checkpoint_status}".replace(" ", "_")

    output_check = receipt.get("output_contract_check") if isinstance(receipt.get("output_contract_check"), dict) else {}
    blocking_check_ids = [
        str(value)
        for value in (receipt.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if checkpoint_status == "checkpoint_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_handoff_unlock"
        checkpoint_message_text = "Dry-run handoff checkpoint is structurally ready, but waits for real Agent output before unlock."
    elif checkpoint_status == "checkpoint_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        checkpoint_message_text = "Handoff checkpoint is waiting for required user action."
    else:
        recommended_next_state = "fix_handoff_checkpoint_blockers"
        checkpoint_message_text = "Handoff checkpoint is blocked by completion receipt or upstream safety checks."

    checkpoint_payload = {
        "handoff_checkpoint_version": AGENT_RUNNER_HANDOFF_CHECKPOINT_VERSION,
        "checkpoint_status": checkpoint_status,
        "checkpoint_id": checkpoint_id,
        "target_agent_id": target_agent_id,
        "completion_id": receipt.get("completion_id"),
        "completion_status": receipt.get("completion_status"),
        "result_id": receipt.get("result_id"),
        "output_contract_check": output_check,
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "handoff_checkpoint_recorded": False,
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "agent_output_generated": False,
        "agent_execution_performed": False,
    }

    checkpoint_message = build_agent_message(
        message_type="runner_handoff_checkpoint_dry_run",
        source_agent_id="runner_handoff_manager",
        target_agent_id=target_agent_id,
        payload=checkpoint_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "handoff_checkpoint_version": AGENT_RUNNER_HANDOFF_CHECKPOINT_VERSION,
        "checkpoint_id": checkpoint_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_checkpoint_dry_run_api"),
        "checkpoint_status": checkpoint_status,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(receipt.get("target_agent_stage") or ""),
        "completion_id": str(receipt.get("completion_id") or ""),
        "completion_status": str(receipt.get("completion_status") or ""),
        "completion_allowed": bool(receipt.get("completion_allowed")),
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "result_id": str(receipt.get("result_id") or ""),
        "attempt_id": str(receipt.get("attempt_id") or ""),
        "recommended_next_state": recommended_next_state,
        "checkpoint_message_text": checkpoint_message_text,
        "blocking_check_ids": blocking_check_ids,
        "output_contract_check": deepcopy(output_check),
        "completion_receipt_summary": build_agent_runner_completion_receipt_summary(receipt),
        "invocation_result_summary": deepcopy(receipt.get("invocation_result_summary") or {}),
        "completion_payload": deepcopy(receipt.get("completion_payload") or {}),
        "completion_message": deepcopy(receipt.get("completion_message") or {}),
        "checkpoint_payload": checkpoint_payload,
        "checkpoint_message": checkpoint_message,
        "dry_run": True,
        "handoff_checkpoint_recorded": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_handoff_checkpoint_summary(checkpoint: dict[str, Any]) -> dict[str, Any]:
    safe_checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    return {
        "summary_version": "agent_runner_handoff_checkpoint_summary_v1",
        "handoff_checkpoint_version": str(safe_checkpoint.get("handoff_checkpoint_version") or AGENT_RUNNER_HANDOFF_CHECKPOINT_VERSION),
        "checkpoint_id": str(safe_checkpoint.get("checkpoint_id") or ""),
        "project_id": str(safe_checkpoint.get("project_id") or "demo_project_default"),
        "checkpoint_status": str(safe_checkpoint.get("checkpoint_status") or "checkpoint_blocked"),
        "target_agent_id": str(safe_checkpoint.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_checkpoint.get("target_agent_stage") or ""),
        "completion_id": str(safe_checkpoint.get("completion_id") or ""),
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "blocking_check_count": len(safe_checkpoint.get("blocking_check_ids") or []),
        "dry_run": True,
        "handoff_checkpoint_recorded": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _next_agent_unlock_status_from_checkpoint(checkpoint: dict[str, Any]) -> str:
    safe_checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    status = str(safe_checkpoint.get("checkpoint_status") or "checkpoint_blocked")
    if status == "checkpoint_waiting_for_real_agent_output":
        return "unlock_waiting_for_real_agent_output"
    if status == "checkpoint_waiting_for_user":
        return "unlock_waiting_for_user"
    return "unlock_blocked"


def build_agent_runner_next_agent_unlock(
    handoff_checkpoint: dict[str, Any],
    requested_by: str = "runner_checkpoint_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run next-Agent unlock decision from a handoff checkpoint.

    In dry-run mode, the next Agent is never truly unlocked because no real
    Agent output has been generated.
    """

    checkpoint = handoff_checkpoint if isinstance(handoff_checkpoint, dict) else {}
    project_id = str(checkpoint.get("project_id") or "demo_project_default")
    target_agent_id = str(checkpoint.get("target_agent_id") or "")
    unlock_status = _next_agent_unlock_status_from_checkpoint(checkpoint)
    unlock_id = f"next_agent_unlock_{project_id}_{target_agent_id or 'none'}_{unlock_status}".replace(" ", "_")

    blocking_check_ids = [
        str(value)
        for value in (checkpoint.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if unlock_status == "unlock_waiting_for_real_agent_output":
        recommended_next_state = "execute_real_agent_then_recheck_unlock"
        unlock_message_text = "Next Agent remains locked in dry-run mode until real Agent output satisfies the output contract."
    elif unlock_status == "unlock_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        unlock_message_text = "Next Agent unlock is waiting for required user action."
    else:
        recommended_next_state = "fix_next_agent_unlock_blockers"
        unlock_message_text = "Next Agent unlock is blocked by handoff checkpoint or upstream safety checks."

    unlock_payload = {
        "next_agent_unlock_version": AGENT_RUNNER_NEXT_AGENT_UNLOCK_VERSION,
        "unlock_status": unlock_status,
        "unlock_id": unlock_id,
        "target_agent_id": target_agent_id,
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "completion_id": checkpoint.get("completion_id"),
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "unlock_recorded": False,
        "agent_output_generated": False,
        "agent_execution_performed": False,
    }

    unlock_message = build_agent_message(
        message_type="runner_next_agent_unlock_dry_run",
        source_agent_id="runner_handoff_manager",
        target_agent_id=target_agent_id,
        payload=unlock_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "next_agent_unlock_version": AGENT_RUNNER_NEXT_AGENT_UNLOCK_VERSION,
        "unlock_id": unlock_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_checkpoint_dry_run_api"),
        "unlock_status": unlock_status,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(checkpoint.get("target_agent_stage") or ""),
        "checkpoint_id": str(checkpoint.get("checkpoint_id") or ""),
        "checkpoint_status": str(checkpoint.get("checkpoint_status") or ""),
        "completion_id": str(checkpoint.get("completion_id") or ""),
        "result_id": str(checkpoint.get("result_id") or ""),
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "unlock_recorded": False,
        "recommended_next_state": recommended_next_state,
        "unlock_message_text": unlock_message_text,
        "blocking_check_ids": blocking_check_ids,
        "handoff_checkpoint_summary": build_agent_runner_handoff_checkpoint_summary(checkpoint),
        "completion_receipt_summary": deepcopy(checkpoint.get("completion_receipt_summary") or {}),
        "output_contract_check": deepcopy(checkpoint.get("output_contract_check") or {}),
        "checkpoint_message": deepcopy(checkpoint.get("checkpoint_message") or {}),
        "unlock_payload": unlock_payload,
        "unlock_message": unlock_message,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_next_agent_unlock_summary(next_agent_unlock: dict[str, Any]) -> dict[str, Any]:
    safe_unlock = next_agent_unlock if isinstance(next_agent_unlock, dict) else {}
    return {
        "summary_version": "agent_runner_next_agent_unlock_summary_v1",
        "next_agent_unlock_version": str(safe_unlock.get("next_agent_unlock_version") or AGENT_RUNNER_NEXT_AGENT_UNLOCK_VERSION),
        "unlock_id": str(safe_unlock.get("unlock_id") or ""),
        "project_id": str(safe_unlock.get("project_id") or "demo_project_default"),
        "unlock_status": str(safe_unlock.get("unlock_status") or "unlock_blocked"),
        "target_agent_id": str(safe_unlock.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_unlock.get("target_agent_stage") or ""),
        "checkpoint_id": str(safe_unlock.get("checkpoint_id") or ""),
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "unlock_recorded": False,
        "blocking_check_count": len(safe_unlock.get("blocking_check_ids") or []),
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_GRAPH_TRANSITION_PROPOSAL_VERSION = "agent_runner_graph_transition_proposal_v1"
AGENT_RUNNER_STATE_PROJECTION_VERSION = "agent_runner_state_projection_v1"


def _graph_transition_status_from_unlock(next_agent_unlock: dict[str, Any]) -> str:
    safe_unlock = next_agent_unlock if isinstance(next_agent_unlock, dict) else {}
    status = str(safe_unlock.get("unlock_status") or "unlock_blocked")
    if bool(safe_unlock.get("next_agent_unlocked")) and status == "unlock_ready":
        return "transition_ready"
    if status == "unlock_waiting_for_real_agent_output":
        return "transition_waiting_for_real_agent_output"
    if status == "unlock_waiting_for_user":
        return "transition_waiting_for_user"
    return "transition_blocked"


def build_agent_runner_graph_transition_proposal(
    next_agent_unlock: dict[str, Any],
    requested_by: str = "runner_transition_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run graph transition proposal from the unlock decision.

    This previews the next graph state. It does not mutate the graph, unlock
    the next Agent, call providers, spend money, or enable autonomous routing.
    """

    unlock = next_agent_unlock if isinstance(next_agent_unlock, dict) else {}
    project_id = str(unlock.get("project_id") or "demo_project_default")
    target_agent_id = str(unlock.get("target_agent_id") or "")
    transition_status = _graph_transition_status_from_unlock(unlock)
    transition_id = f"graph_transition_{project_id}_{target_agent_id or 'none'}_{transition_status}".replace(" ", "_")

    blocking_check_ids = [
        str(value)
        for value in (unlock.get("blocking_check_ids") or [])
        if str(value or "")
    ]

    if transition_status == "transition_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_then_rebuild_transition"
        transition_message_text = "Graph transition is only a dry-run preview and waits for real Agent output."
        proposed_graph_state = "waiting_for_real_agent_output"
    elif transition_status == "transition_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        transition_message_text = "Graph transition is waiting for required user action."
        proposed_graph_state = "waiting_for_user"
    elif transition_status == "transition_ready":
        recommended_next_state = "persist_graph_transition_under_explicit_gate"
        transition_message_text = "Graph transition is ready, but persistence requires an explicit gate."
        proposed_graph_state = "next_agent_ready"
    else:
        recommended_next_state = "fix_graph_transition_blockers"
        transition_message_text = "Graph transition is blocked by next-Agent unlock or upstream safety checks."
        proposed_graph_state = "blocked"

    transition_payload = {
        "graph_transition_proposal_version": AGENT_RUNNER_GRAPH_TRANSITION_PROPOSAL_VERSION,
        "transition_status": transition_status,
        "transition_id": transition_id,
        "target_agent_id": target_agent_id,
        "target_agent_stage": unlock.get("target_agent_stage"),
        "checkpoint_id": unlock.get("checkpoint_id"),
        "unlock_id": unlock.get("unlock_id"),
        "proposed_graph_state": proposed_graph_state,
        "blocking_check_ids": blocking_check_ids,
        "dry_run": True,
        "graph_transition_persisted": False,
        "next_agent_unlocked": False,
        "agent_execution_performed": False,
    }

    transition_message = build_agent_message(
        message_type="runner_graph_transition_proposal_dry_run",
        source_agent_id="runner_transition_manager",
        target_agent_id=target_agent_id,
        payload=transition_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "graph_transition_proposal_version": AGENT_RUNNER_GRAPH_TRANSITION_PROPOSAL_VERSION,
        "transition_id": transition_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_transition_dry_run_api"),
        "transition_status": transition_status,
        "proposed_graph_state": proposed_graph_state,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(unlock.get("target_agent_stage") or ""),
        "unlock_id": str(unlock.get("unlock_id") or ""),
        "unlock_status": str(unlock.get("unlock_status") or ""),
        "checkpoint_id": str(unlock.get("checkpoint_id") or ""),
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "graph_transition_persisted": False,
        "recommended_next_state": recommended_next_state,
        "transition_message_text": transition_message_text,
        "blocking_check_ids": blocking_check_ids,
        "next_agent_unlock_summary": build_agent_runner_next_agent_unlock_summary(unlock),
        "handoff_checkpoint_summary": deepcopy(unlock.get("handoff_checkpoint_summary") or {}),
        "output_contract_check": deepcopy(unlock.get("output_contract_check") or {}),
        "unlock_message": deepcopy(unlock.get("unlock_message") or {}),
        "transition_payload": transition_payload,
        "transition_message": transition_message,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_graph_transition_proposal_summary(proposal: dict[str, Any]) -> dict[str, Any]:
    safe_proposal = proposal if isinstance(proposal, dict) else {}
    return {
        "summary_version": "agent_runner_graph_transition_proposal_summary_v1",
        "graph_transition_proposal_version": str(safe_proposal.get("graph_transition_proposal_version") or AGENT_RUNNER_GRAPH_TRANSITION_PROPOSAL_VERSION),
        "transition_id": str(safe_proposal.get("transition_id") or ""),
        "project_id": str(safe_proposal.get("project_id") or "demo_project_default"),
        "transition_status": str(safe_proposal.get("transition_status") or "transition_blocked"),
        "proposed_graph_state": str(safe_proposal.get("proposed_graph_state") or "blocked"),
        "target_agent_id": str(safe_proposal.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_proposal.get("target_agent_stage") or ""),
        "unlock_id": str(safe_proposal.get("unlock_id") or ""),
        "checkpoint_id": str(safe_proposal.get("checkpoint_id") or ""),
        "next_agent_unlocked": False,
        "graph_transition_persisted": False,
        "blocking_check_count": len(safe_proposal.get("blocking_check_ids") or []),
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_state_projection(
    graph_transition_proposal: dict[str, Any],
    project: dict[str, Any] | None = None,
    requested_by: str = "runner_transition_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run state projection from a graph transition proposal.

    This previews the project graph summary after a possible transition. It
    does not persist state or trigger any Agent.
    """

    proposal = graph_transition_proposal if isinstance(graph_transition_proposal, dict) else {}
    safe_project = project if isinstance(project, dict) else {}
    project_id = str(proposal.get("project_id") or safe_project.get("project_id") or "demo_project_default")
    target_agent_id = str(proposal.get("target_agent_id") or "")
    projection_status = str(proposal.get("transition_status") or "transition_blocked").replace("transition_", "projection_")
    projection_id = f"state_projection_{project_id}_{target_agent_id or 'none'}_{projection_status}".replace(" ", "_")

    current_graph_summary = deepcopy(safe_project.get("graph_summary") or {})
    projected_graph_summary = deepcopy(current_graph_summary)
    projected_graph_summary.update(
        {
            "projected_runner_transition_status": proposal.get("transition_status", ""),
            "projected_runner_graph_state": proposal.get("proposed_graph_state", ""),
            "projected_runner_target_agent_id": target_agent_id,
            "projected_next_agent_unlocked": False,
            "projected_handoff_complete": False,
            "projected_agent_execution_performed": False,
        }
    )

    projection_payload = {
        "state_projection_version": AGENT_RUNNER_STATE_PROJECTION_VERSION,
        "projection_status": projection_status,
        "projection_id": projection_id,
        "transition_id": proposal.get("transition_id"),
        "current_graph_summary": current_graph_summary,
        "projected_graph_summary": projected_graph_summary,
        "dry_run": True,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_execution_performed": False,
    }

    projection_message = build_agent_message(
        message_type="runner_state_projection_dry_run",
        source_agent_id="runner_transition_manager",
        target_agent_id=target_agent_id,
        payload=projection_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "state_projection_version": AGENT_RUNNER_STATE_PROJECTION_VERSION,
        "projection_id": projection_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_transition_dry_run_api"),
        "projection_status": projection_status,
        "transition_id": str(proposal.get("transition_id") or ""),
        "transition_status": str(proposal.get("transition_status") or ""),
        "proposed_graph_state": str(proposal.get("proposed_graph_state") or "blocked"),
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(proposal.get("target_agent_stage") or ""),
        "current_graph_summary": current_graph_summary,
        "projected_graph_summary": projected_graph_summary,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "graph_transition_proposal_summary": build_agent_runner_graph_transition_proposal_summary(proposal),
        "transition_message": deepcopy(proposal.get("transition_message") or {}),
        "projection_payload": projection_payload,
        "projection_message": projection_message,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_state_projection_summary(state_projection: dict[str, Any]) -> dict[str, Any]:
    safe_projection = state_projection if isinstance(state_projection, dict) else {}
    return {
        "summary_version": "agent_runner_state_projection_summary_v1",
        "state_projection_version": str(safe_projection.get("state_projection_version") or AGENT_RUNNER_STATE_PROJECTION_VERSION),
        "projection_id": str(safe_projection.get("projection_id") or ""),
        "project_id": str(safe_projection.get("project_id") or "demo_project_default"),
        "projection_status": str(safe_projection.get("projection_status") or "projection_blocked"),
        "transition_status": str(safe_projection.get("transition_status") or "transition_blocked"),
        "proposed_graph_state": str(safe_projection.get("proposed_graph_state") or "blocked"),
        "target_agent_id": str(safe_projection.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_projection.get("target_agent_stage") or ""),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_TRANSITION_COMMIT_PLAN_VERSION = "agent_runner_transition_commit_plan_v1"
AGENT_RUNNER_MUTATION_GUARD_VERSION = "agent_runner_mutation_guard_v1"


def _transition_commit_plan_status_from_projection(state_projection: dict[str, Any]) -> str:
    safe_projection = state_projection if isinstance(state_projection, dict) else {}
    status = str(safe_projection.get("projection_status") or "projection_blocked")
    if status == "projection_waiting_for_real_agent_output":
        return "commit_plan_waiting_for_real_agent_output"
    if status == "projection_waiting_for_user":
        return "commit_plan_waiting_for_user"
    if status == "projection_ready":
        return "commit_plan_ready"
    return "commit_plan_blocked"


def build_agent_runner_transition_commit_plan(
    state_projection: dict[str, Any],
    requested_by: str = "runner_commit_plan_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run transition commit plan from a state projection.

    This previews which graph state changes would be persisted later. It does
    not persist project state, mutate the graph, unlock an Agent, or execute.
    """

    projection = state_projection if isinstance(state_projection, dict) else {}
    project_id = str(projection.get("project_id") or "demo_project_default")
    target_agent_id = str(projection.get("target_agent_id") or "")
    commit_plan_status = _transition_commit_plan_status_from_projection(projection)
    commit_plan_id = f"transition_commit_plan_{project_id}_{target_agent_id or 'none'}_{commit_plan_status}".replace(" ", "_")

    projected_graph_summary = deepcopy(projection.get("projected_graph_summary") or {})
    current_graph_summary = deepcopy(projection.get("current_graph_summary") or {})
    planned_mutations = [
        {
            "path": "project.graph_summary.latest_runner_transition_status",
            "current_value": current_graph_summary.get("latest_runner_transition_status"),
            "projected_value": projected_graph_summary.get("projected_runner_transition_status"),
        },
        {
            "path": "project.graph_summary.latest_runner_projected_graph_state",
            "current_value": current_graph_summary.get("latest_runner_projected_graph_state"),
            "projected_value": projected_graph_summary.get("projected_runner_graph_state"),
        },
        {
            "path": "project.graph_summary.latest_runner_target_agent_id",
            "current_value": current_graph_summary.get("latest_runner_target_agent_id"),
            "projected_value": projected_graph_summary.get("projected_runner_target_agent_id"),
        },
        {
            "path": "project.graph_summary.latest_runner_state_projection_status",
            "current_value": current_graph_summary.get("latest_runner_state_projection_status"),
            "projected_value": projection.get("projection_status"),
        },
    ]

    if commit_plan_status == "commit_plan_waiting_for_real_agent_output":
        recommended_next_state = "wait_for_real_agent_output_before_commit"
        commit_plan_message_text = "Commit plan is only a dry-run preview and waits for real Agent output."
    elif commit_plan_status == "commit_plan_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        commit_plan_message_text = "Commit plan is waiting for required user action."
    elif commit_plan_status == "commit_plan_ready":
        recommended_next_state = "run_mutation_guard_before_persist"
        commit_plan_message_text = "Commit plan is ready, but mutation persistence still requires an explicit guard."
    else:
        recommended_next_state = "fix_commit_plan_blockers"
        commit_plan_message_text = "Commit plan is blocked by state projection, transition proposal, or upstream safety checks."

    commit_payload = {
        "transition_commit_plan_version": AGENT_RUNNER_TRANSITION_COMMIT_PLAN_VERSION,
        "commit_plan_status": commit_plan_status,
        "commit_plan_id": commit_plan_id,
        "projection_id": projection.get("projection_id"),
        "transition_id": projection.get("transition_id"),
        "target_agent_id": target_agent_id,
        "planned_mutations": planned_mutations,
        "planned_mutation_count": len(planned_mutations),
        "dry_run": True,
        "commit_plan_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_execution_performed": False,
    }

    commit_message = build_agent_message(
        message_type="runner_transition_commit_plan_dry_run",
        source_agent_id="runner_transition_manager",
        target_agent_id=target_agent_id,
        payload=commit_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "transition_commit_plan_version": AGENT_RUNNER_TRANSITION_COMMIT_PLAN_VERSION,
        "commit_plan_id": commit_plan_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_commit_plan_dry_run_api"),
        "commit_plan_status": commit_plan_status,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(projection.get("target_agent_stage") or ""),
        "projection_id": str(projection.get("projection_id") or ""),
        "projection_status": str(projection.get("projection_status") or ""),
        "transition_id": str(projection.get("transition_id") or ""),
        "transition_status": str(projection.get("transition_status") or ""),
        "proposed_graph_state": str(projection.get("proposed_graph_state") or "blocked"),
        "planned_mutations": planned_mutations,
        "planned_mutation_count": len(planned_mutations),
        "recommended_next_state": recommended_next_state,
        "commit_plan_message_text": commit_plan_message_text,
        "current_graph_summary": current_graph_summary,
        "projected_graph_summary": projected_graph_summary,
        "state_projection_summary": build_agent_runner_state_projection_summary(projection),
        "graph_transition_proposal_summary": deepcopy(projection.get("graph_transition_proposal_summary") or {}),
        "projection_message": deepcopy(projection.get("projection_message") or {}),
        "commit_payload": commit_payload,
        "commit_message": commit_message,
        "dry_run": True,
        "commit_plan_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_transition_commit_plan_summary(commit_plan: dict[str, Any]) -> dict[str, Any]:
    safe_plan = commit_plan if isinstance(commit_plan, dict) else {}
    return {
        "summary_version": "agent_runner_transition_commit_plan_summary_v1",
        "transition_commit_plan_version": str(safe_plan.get("transition_commit_plan_version") or AGENT_RUNNER_TRANSITION_COMMIT_PLAN_VERSION),
        "commit_plan_id": str(safe_plan.get("commit_plan_id") or ""),
        "project_id": str(safe_plan.get("project_id") or "demo_project_default"),
        "commit_plan_status": str(safe_plan.get("commit_plan_status") or "commit_plan_blocked"),
        "target_agent_id": str(safe_plan.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_plan.get("target_agent_stage") or ""),
        "projection_id": str(safe_plan.get("projection_id") or ""),
        "transition_id": str(safe_plan.get("transition_id") or ""),
        "planned_mutation_count": int(safe_plan.get("planned_mutation_count") or 0),
        "commit_plan_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _mutation_guard_status_from_commit_plan(commit_plan: dict[str, Any]) -> str:
    safe_plan = commit_plan if isinstance(commit_plan, dict) else {}
    status = str(safe_plan.get("commit_plan_status") or "commit_plan_blocked")
    if status == "commit_plan_waiting_for_real_agent_output":
        return "mutation_guard_waiting_for_real_agent_output"
    if status == "commit_plan_waiting_for_user":
        return "mutation_guard_waiting_for_user"
    if status == "commit_plan_ready":
        return "mutation_guard_ready"
    return "mutation_guard_blocked"


def build_agent_runner_mutation_guard(
    transition_commit_plan: dict[str, Any],
    requested_by: str = "runner_commit_plan_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run mutation guard from a transition commit plan.

    This checks whether a state mutation could be allowed later. In dry-run
    mode it never persists state or marks the mutation as applied.
    """

    plan = transition_commit_plan if isinstance(transition_commit_plan, dict) else {}
    project_id = str(plan.get("project_id") or "demo_project_default")
    target_agent_id = str(plan.get("target_agent_id") or "")
    guard_status = _mutation_guard_status_from_commit_plan(plan)
    guard_id = f"mutation_guard_{project_id}_{target_agent_id or 'none'}_{guard_status}".replace(" ", "_")

    planned_mutations = deepcopy(plan.get("planned_mutations") or [])
    guard_checks = [
        {
            "check_id": "dry_run_only",
            "passed": True,
            "message": "Mutation is dry-run only and will not be persisted.",
        },
        {
            "check_id": "real_agent_output_required",
            "passed": guard_status not in {"mutation_guard_waiting_for_real_agent_output"},
            "message": "Real Agent output is required before a persistent graph transition.",
        },
        {
            "check_id": "explicit_persist_gate_required",
            "passed": False,
            "message": "Persistent mutation requires a future explicit persist gate.",
        },
    ]

    mutation_allowed = guard_status == "mutation_guard_ready" and all(item["passed"] for item in guard_checks)

    if guard_status == "mutation_guard_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_mutation"
        guard_message_text = "Mutation guard is waiting for real Agent output."
    elif guard_status == "mutation_guard_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        guard_message_text = "Mutation guard is waiting for required user action."
    elif guard_status == "mutation_guard_ready":
        recommended_next_state = "add_explicit_persist_gate"
        guard_message_text = "Mutation guard is structurally ready, but persistent mutation is still disabled."
    else:
        recommended_next_state = "fix_mutation_guard_blockers"
        guard_message_text = "Mutation guard is blocked by commit plan, projection, transition, or upstream checks."

    guard_payload = {
        "mutation_guard_version": AGENT_RUNNER_MUTATION_GUARD_VERSION,
        "mutation_guard_status": guard_status,
        "mutation_guard_id": guard_id,
        "commit_plan_id": plan.get("commit_plan_id"),
        "projection_id": plan.get("projection_id"),
        "target_agent_id": target_agent_id,
        "planned_mutation_count": len(planned_mutations),
        "guard_checks": guard_checks,
        "mutation_allowed": mutation_allowed,
        "dry_run": True,
        "mutation_guard_recorded": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_execution_performed": False,
    }

    guard_message = build_agent_message(
        message_type="runner_mutation_guard_dry_run",
        source_agent_id="runner_transition_manager",
        target_agent_id=target_agent_id,
        payload=guard_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "mutation_guard_version": AGENT_RUNNER_MUTATION_GUARD_VERSION,
        "mutation_guard_id": guard_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_commit_plan_dry_run_api"),
        "mutation_guard_status": guard_status,
        "mutation_allowed": mutation_allowed,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(plan.get("target_agent_stage") or ""),
        "commit_plan_id": str(plan.get("commit_plan_id") or ""),
        "commit_plan_status": str(plan.get("commit_plan_status") or ""),
        "projection_id": str(plan.get("projection_id") or ""),
        "transition_id": str(plan.get("transition_id") or ""),
        "planned_mutations": planned_mutations,
        "planned_mutation_count": len(planned_mutations),
        "guard_checks": guard_checks,
        "recommended_next_state": recommended_next_state,
        "guard_message_text": guard_message_text,
        "transition_commit_plan_summary": build_agent_runner_transition_commit_plan_summary(plan),
        "state_projection_summary": deepcopy(plan.get("state_projection_summary") or {}),
        "commit_message": deepcopy(plan.get("commit_message") or {}),
        "guard_payload": guard_payload,
        "guard_message": guard_message,
        "dry_run": True,
        "mutation_guard_recorded": False,
        "commit_plan_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_mutation_guard_summary(mutation_guard: dict[str, Any]) -> dict[str, Any]:
    safe_guard = mutation_guard if isinstance(mutation_guard, dict) else {}
    return {
        "summary_version": "agent_runner_mutation_guard_summary_v1",
        "mutation_guard_version": str(safe_guard.get("mutation_guard_version") or AGENT_RUNNER_MUTATION_GUARD_VERSION),
        "mutation_guard_id": str(safe_guard.get("mutation_guard_id") or ""),
        "project_id": str(safe_guard.get("project_id") or "demo_project_default"),
        "mutation_guard_status": str(safe_guard.get("mutation_guard_status") or "mutation_guard_blocked"),
        "mutation_allowed": bool(safe_guard.get("mutation_allowed")),
        "target_agent_id": str(safe_guard.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_guard.get("target_agent_stage") or ""),
        "commit_plan_id": str(safe_guard.get("commit_plan_id") or ""),
        "projection_id": str(safe_guard.get("projection_id") or ""),
        "planned_mutation_count": int(safe_guard.get("planned_mutation_count") or 0),
        "mutation_guard_recorded": False,
        "commit_plan_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_TRANSITION_PERSIST_REQUEST_VERSION = "agent_runner_transition_persist_request_v1"
AGENT_RUNNER_ROLLBACK_PLAN_VERSION = "agent_runner_rollback_plan_v1"


def _persist_request_status_from_guard(mutation_guard: dict[str, Any]) -> str:
    safe_guard = mutation_guard if isinstance(mutation_guard, dict) else {}
    status = str(safe_guard.get("mutation_guard_status") or "mutation_guard_blocked")
    if status == "mutation_guard_waiting_for_real_agent_output":
        return "persist_request_waiting_for_real_agent_output"
    if status == "mutation_guard_waiting_for_user":
        return "persist_request_waiting_for_user"
    if status == "mutation_guard_ready":
        return "persist_request_waiting_for_explicit_gate"
    return "persist_request_blocked"


def build_agent_runner_transition_persist_request(
    mutation_guard: dict[str, Any],
    requested_by: str = "runner_persist_request_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run transition persist request from a mutation guard.

    This prepares a future write request, but it does not persist state,
    mutate the graph, save a project snapshot, unlock an Agent, or execute.
    """

    guard = mutation_guard if isinstance(mutation_guard, dict) else {}
    project_id = str(guard.get("project_id") or "demo_project_default")
    target_agent_id = str(guard.get("target_agent_id") or "")
    persist_request_status = _persist_request_status_from_guard(guard)
    persist_request_id = f"transition_persist_request_{project_id}_{target_agent_id or 'none'}_{persist_request_status}".replace(" ", "_")

    planned_mutations = deepcopy(guard.get("planned_mutations") or [])
    guard_checks = deepcopy(guard.get("guard_checks") or [])

    if persist_request_status == "persist_request_waiting_for_real_agent_output":
        recommended_next_state = "wait_for_real_agent_output_before_persist_request"
        persist_request_message_text = "Persist request is waiting for real Agent output."
    elif persist_request_status == "persist_request_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        persist_request_message_text = "Persist request is waiting for required user action."
    elif persist_request_status == "persist_request_waiting_for_explicit_gate":
        recommended_next_state = "add_explicit_persist_gate_before_write"
        persist_request_message_text = "Persist request is structurally ready, but write is disabled until an explicit persist gate exists."
    else:
        recommended_next_state = "fix_persist_request_blockers"
        persist_request_message_text = "Persist request is blocked by mutation guard, commit plan, projection, transition, or upstream checks."

    persist_payload = {
        "transition_persist_request_version": AGENT_RUNNER_TRANSITION_PERSIST_REQUEST_VERSION,
        "persist_request_status": persist_request_status,
        "persist_request_id": persist_request_id,
        "mutation_guard_id": guard.get("mutation_guard_id"),
        "commit_plan_id": guard.get("commit_plan_id"),
        "projection_id": guard.get("projection_id"),
        "target_agent_id": target_agent_id,
        "planned_mutations": planned_mutations,
        "planned_mutation_count": len(planned_mutations),
        "guard_checks": guard_checks,
        "dry_run": True,
        "persist_request_recorded": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_execution_performed": False,
    }

    persist_message = build_agent_message(
        message_type="runner_transition_persist_request_dry_run",
        source_agent_id="runner_persistence_manager",
        target_agent_id=target_agent_id,
        payload=persist_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "transition_persist_request_version": AGENT_RUNNER_TRANSITION_PERSIST_REQUEST_VERSION,
        "persist_request_id": persist_request_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_persist_request_dry_run_api"),
        "persist_request_status": persist_request_status,
        "write_authorized": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(guard.get("target_agent_stage") or ""),
        "mutation_guard_id": str(guard.get("mutation_guard_id") or ""),
        "mutation_guard_status": str(guard.get("mutation_guard_status") or ""),
        "mutation_allowed": bool(guard.get("mutation_allowed")),
        "commit_plan_id": str(guard.get("commit_plan_id") or ""),
        "projection_id": str(guard.get("projection_id") or ""),
        "transition_id": str(guard.get("transition_id") or ""),
        "planned_mutations": planned_mutations,
        "planned_mutation_count": len(planned_mutations),
        "guard_checks": guard_checks,
        "recommended_next_state": recommended_next_state,
        "persist_request_message_text": persist_request_message_text,
        "mutation_guard_summary": build_agent_runner_mutation_guard_summary(guard),
        "transition_commit_plan_summary": deepcopy(guard.get("transition_commit_plan_summary") or {}),
        "state_projection_summary": deepcopy(guard.get("state_projection_summary") or {}),
        "guard_message": deepcopy(guard.get("guard_message") or {}),
        "persist_payload": persist_payload,
        "persist_message": persist_message,
        "dry_run": True,
        "persist_request_recorded": False,
        "commit_plan_persisted": False,
        "mutation_guard_recorded": False,
        "graph_transition_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_transition_persist_request_summary(persist_request: dict[str, Any]) -> dict[str, Any]:
    safe_request = persist_request if isinstance(persist_request, dict) else {}
    return {
        "summary_version": "agent_runner_transition_persist_request_summary_v1",
        "transition_persist_request_version": str(safe_request.get("transition_persist_request_version") or AGENT_RUNNER_TRANSITION_PERSIST_REQUEST_VERSION),
        "persist_request_id": str(safe_request.get("persist_request_id") or ""),
        "project_id": str(safe_request.get("project_id") or "demo_project_default"),
        "persist_request_status": str(safe_request.get("persist_request_status") or "persist_request_blocked"),
        "write_authorized": False,
        "target_agent_id": str(safe_request.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_request.get("target_agent_stage") or ""),
        "mutation_guard_id": str(safe_request.get("mutation_guard_id") or ""),
        "commit_plan_id": str(safe_request.get("commit_plan_id") or ""),
        "planned_mutation_count": int(safe_request.get("planned_mutation_count") or 0),
        "persist_request_recorded": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _rollback_plan_status_from_persist_request(persist_request: dict[str, Any]) -> str:
    safe_request = persist_request if isinstance(persist_request, dict) else {}
    status = str(safe_request.get("persist_request_status") or "persist_request_blocked")
    if status == "persist_request_waiting_for_real_agent_output":
        return "rollback_plan_waiting_for_real_agent_output"
    if status == "persist_request_waiting_for_user":
        return "rollback_plan_waiting_for_user"
    if status == "persist_request_waiting_for_explicit_gate":
        return "rollback_plan_waiting_for_explicit_gate"
    return "rollback_plan_blocked"


def build_agent_runner_rollback_plan(
    transition_persist_request: dict[str, Any],
    requested_by: str = "runner_persist_request_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run rollback plan for a future transition persist request.

    This previews reverse mutations for a possible future write. It does not
    persist state, record rollback, or apply any mutation.
    """

    request = transition_persist_request if isinstance(transition_persist_request, dict) else {}
    project_id = str(request.get("project_id") or "demo_project_default")
    target_agent_id = str(request.get("target_agent_id") or "")
    rollback_plan_status = _rollback_plan_status_from_persist_request(request)
    rollback_plan_id = f"rollback_plan_{project_id}_{target_agent_id or 'none'}_{rollback_plan_status}".replace(" ", "_")

    planned_mutations = deepcopy(request.get("planned_mutations") or [])
    rollback_steps = []
    for mutation in planned_mutations:
        if not isinstance(mutation, dict):
            continue
        rollback_steps.append(
            {
                "path": mutation.get("path"),
                "restore_value": mutation.get("current_value"),
                "discard_value": mutation.get("projected_value"),
            }
        )

    if rollback_plan_status == "rollback_plan_waiting_for_real_agent_output":
        recommended_next_state = "wait_for_real_agent_output_before_rollback_readiness"
        rollback_plan_message_text = "Rollback plan is prepared as a dry-run shell but waits for real Agent output."
    elif rollback_plan_status == "rollback_plan_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        rollback_plan_message_text = "Rollback plan is waiting for required user action."
    elif rollback_plan_status == "rollback_plan_waiting_for_explicit_gate":
        recommended_next_state = "add_explicit_persist_gate_and_confirm_rollback"
        rollback_plan_message_text = "Rollback plan is structurally available, but no write or rollback is enabled in dry-run."
    else:
        recommended_next_state = "fix_rollback_plan_blockers"
        rollback_plan_message_text = "Rollback plan is blocked by persist request or upstream checks."

    rollback_payload = {
        "rollback_plan_version": AGENT_RUNNER_ROLLBACK_PLAN_VERSION,
        "rollback_plan_status": rollback_plan_status,
        "rollback_plan_id": rollback_plan_id,
        "persist_request_id": request.get("persist_request_id"),
        "mutation_guard_id": request.get("mutation_guard_id"),
        "target_agent_id": target_agent_id,
        "rollback_steps": rollback_steps,
        "rollback_step_count": len(rollback_steps),
        "dry_run": True,
        "rollback_plan_recorded": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
    }

    rollback_message = build_agent_message(
        message_type="runner_rollback_plan_dry_run",
        source_agent_id="runner_persistence_manager",
        target_agent_id=target_agent_id,
        payload=rollback_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "rollback_plan_version": AGENT_RUNNER_ROLLBACK_PLAN_VERSION,
        "rollback_plan_id": rollback_plan_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_persist_request_dry_run_api"),
        "rollback_plan_status": rollback_plan_status,
        "rollback_available": False,
        "rollback_applied": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(request.get("target_agent_stage") or ""),
        "persist_request_id": str(request.get("persist_request_id") or ""),
        "persist_request_status": str(request.get("persist_request_status") or ""),
        "mutation_guard_id": str(request.get("mutation_guard_id") or ""),
        "commit_plan_id": str(request.get("commit_plan_id") or ""),
        "planned_mutation_count": int(request.get("planned_mutation_count") or 0),
        "rollback_steps": rollback_steps,
        "rollback_step_count": len(rollback_steps),
        "recommended_next_state": recommended_next_state,
        "rollback_plan_message_text": rollback_plan_message_text,
        "transition_persist_request_summary": build_agent_runner_transition_persist_request_summary(request),
        "mutation_guard_summary": deepcopy(request.get("mutation_guard_summary") or {}),
        "persist_message": deepcopy(request.get("persist_message") or {}),
        "rollback_payload": rollback_payload,
        "rollback_message": rollback_message,
        "dry_run": True,
        "rollback_plan_recorded": False,
        "persist_request_recorded": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_rollback_plan_summary(rollback_plan: dict[str, Any]) -> dict[str, Any]:
    safe_plan = rollback_plan if isinstance(rollback_plan, dict) else {}
    return {
        "summary_version": "agent_runner_rollback_plan_summary_v1",
        "rollback_plan_version": str(safe_plan.get("rollback_plan_version") or AGENT_RUNNER_ROLLBACK_PLAN_VERSION),
        "rollback_plan_id": str(safe_plan.get("rollback_plan_id") or ""),
        "project_id": str(safe_plan.get("project_id") or "demo_project_default"),
        "rollback_plan_status": str(safe_plan.get("rollback_plan_status") or "rollback_plan_blocked"),
        "rollback_available": False,
        "rollback_applied": False,
        "target_agent_id": str(safe_plan.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_plan.get("target_agent_stage") or ""),
        "persist_request_id": str(safe_plan.get("persist_request_id") or ""),
        "mutation_guard_id": str(safe_plan.get("mutation_guard_id") or ""),
        "rollback_step_count": int(safe_plan.get("rollback_step_count") or 0),
        "rollback_plan_recorded": False,
        "persist_request_recorded": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_PERSIST_GATE_VERSION = "agent_runner_persist_gate_v1"
AGENT_RUNNER_AUDIT_LEDGER_VERSION = "agent_runner_audit_ledger_v1"


def _persist_gate_status_from_request(persist_request: dict[str, Any]) -> str:
    safe_request = persist_request if isinstance(persist_request, dict) else {}
    status = str(safe_request.get("persist_request_status") or "persist_request_blocked")
    if status == "persist_request_waiting_for_real_agent_output":
        return "persist_gate_waiting_for_real_agent_output"
    if status == "persist_request_waiting_for_user":
        return "persist_gate_waiting_for_user"
    if status == "persist_request_waiting_for_explicit_gate":
        return "persist_gate_waiting_for_explicit_approval"
    return "persist_gate_blocked"


def build_agent_runner_persist_gate(
    transition_persist_request: dict[str, Any],
    rollback_plan: dict[str, Any] | None = None,
    requested_by: str = "runner_persist_gate_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run explicit persist gate.

    This is the last pre-write gate. In dry-run mode it never authorizes a
    write, persists state, applies rollback, or executes an Agent.
    """

    request = transition_persist_request if isinstance(transition_persist_request, dict) else {}
    rollback = rollback_plan if isinstance(rollback_plan, dict) else {}
    project_id = str(request.get("project_id") or rollback.get("project_id") or "demo_project_default")
    target_agent_id = str(request.get("target_agent_id") or rollback.get("target_agent_id") or "")
    gate_status = _persist_gate_status_from_request(request)
    gate_id = f"persist_gate_{project_id}_{target_agent_id or 'none'}_{gate_status}".replace(" ", "_")

    gate_checks = [
        {
            "check_id": "dry_run_only",
            "passed": True,
            "message": "Persist gate is dry-run only.",
        },
        {
            "check_id": "write_authorized",
            "passed": False,
            "message": "Write authorization is disabled until a future explicit approval flow exists.",
        },
        {
            "check_id": "rollback_available",
            "passed": bool(rollback.get("rollback_available")),
            "message": "Rollback must be available before a real write.",
        },
        {
            "check_id": "real_agent_output_required",
            "passed": gate_status not in {"persist_gate_waiting_for_real_agent_output"},
            "message": "Real Agent output is required before persistent state changes.",
        },
    ]

    if gate_status == "persist_gate_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_persist_gate"
        gate_message_text = "Persist gate is waiting for real Agent output."
    elif gate_status == "persist_gate_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        gate_message_text = "Persist gate is waiting for required user action."
    elif gate_status == "persist_gate_waiting_for_explicit_approval":
        recommended_next_state = "add_explicit_human_or_policy_approval"
        gate_message_text = "Persist gate is structurally ready, but explicit approval is not implemented."
    else:
        recommended_next_state = "fix_persist_gate_blockers"
        gate_message_text = "Persist gate is blocked by persist request, rollback plan, or upstream checks."

    gate_payload = {
        "persist_gate_version": AGENT_RUNNER_PERSIST_GATE_VERSION,
        "persist_gate_status": gate_status,
        "persist_gate_id": gate_id,
        "persist_request_id": request.get("persist_request_id"),
        "rollback_plan_id": rollback.get("rollback_plan_id"),
        "target_agent_id": target_agent_id,
        "gate_checks": gate_checks,
        "gate_check_count": len(gate_checks),
        "dry_run": True,
        "explicit_approval_present": False,
        "write_authorized": False,
        "persist_gate_recorded": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "rollback_available": False,
        "rollback_applied": False,
    }

    gate_message = build_agent_message(
        message_type="runner_persist_gate_dry_run",
        source_agent_id="runner_persistence_manager",
        target_agent_id=target_agent_id,
        payload=gate_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "persist_gate_version": AGENT_RUNNER_PERSIST_GATE_VERSION,
        "persist_gate_id": gate_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_persist_gate_dry_run_api"),
        "persist_gate_status": gate_status,
        "explicit_approval_present": False,
        "write_authorized": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(request.get("target_agent_stage") or rollback.get("target_agent_stage") or ""),
        "persist_request_id": str(request.get("persist_request_id") or ""),
        "persist_request_status": str(request.get("persist_request_status") or ""),
        "rollback_plan_id": str(rollback.get("rollback_plan_id") or ""),
        "rollback_plan_status": str(rollback.get("rollback_plan_status") or ""),
        "rollback_available": False,
        "rollback_applied": False,
        "gate_checks": gate_checks,
        "gate_check_count": len(gate_checks),
        "recommended_next_state": recommended_next_state,
        "gate_message_text": gate_message_text,
        "transition_persist_request_summary": build_agent_runner_transition_persist_request_summary(request),
        "rollback_plan_summary": build_agent_runner_rollback_plan_summary(rollback),
        "persist_message": deepcopy(request.get("persist_message") or {}),
        "rollback_message": deepcopy(rollback.get("rollback_message") or {}),
        "gate_payload": gate_payload,
        "gate_message": gate_message,
        "dry_run": True,
        "persist_gate_recorded": False,
        "persist_request_recorded": False,
        "rollback_plan_recorded": False,
        "commit_plan_persisted": False,
        "mutation_guard_recorded": False,
        "graph_transition_persisted": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_persist_gate_summary(persist_gate: dict[str, Any]) -> dict[str, Any]:
    safe_gate = persist_gate if isinstance(persist_gate, dict) else {}
    return {
        "summary_version": "agent_runner_persist_gate_summary_v1",
        "persist_gate_version": str(safe_gate.get("persist_gate_version") or AGENT_RUNNER_PERSIST_GATE_VERSION),
        "persist_gate_id": str(safe_gate.get("persist_gate_id") or ""),
        "project_id": str(safe_gate.get("project_id") or "demo_project_default"),
        "persist_gate_status": str(safe_gate.get("persist_gate_status") or "persist_gate_blocked"),
        "explicit_approval_present": False,
        "write_authorized": False,
        "target_agent_id": str(safe_gate.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_gate.get("target_agent_stage") or ""),
        "persist_request_id": str(safe_gate.get("persist_request_id") or ""),
        "rollback_plan_id": str(safe_gate.get("rollback_plan_id") or ""),
        "gate_check_count": int(safe_gate.get("gate_check_count") or 0),
        "persist_gate_recorded": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _audit_ledger_status_from_gate(persist_gate: dict[str, Any]) -> str:
    safe_gate = persist_gate if isinstance(persist_gate, dict) else {}
    status = str(safe_gate.get("persist_gate_status") or "persist_gate_blocked")
    if status == "persist_gate_waiting_for_real_agent_output":
        return "audit_ledger_waiting_for_real_agent_output"
    if status == "persist_gate_waiting_for_user":
        return "audit_ledger_waiting_for_user"
    if status == "persist_gate_waiting_for_explicit_approval":
        return "audit_ledger_waiting_for_explicit_approval"
    return "audit_ledger_blocked"


def build_agent_runner_audit_ledger(
    persist_gate: dict[str, Any],
    requested_by: str = "runner_persist_gate_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run audit ledger for the runner chain.

    This records a compact audit view of the dry-run chain without persisting
    the ledger or mutating project state.
    """

    gate = persist_gate if isinstance(persist_gate, dict) else {}
    project_id = str(gate.get("project_id") or "demo_project_default")
    target_agent_id = str(gate.get("target_agent_id") or "")
    audit_status = _audit_ledger_status_from_gate(gate)
    audit_ledger_id = f"audit_ledger_{project_id}_{target_agent_id or 'none'}_{audit_status}".replace(" ", "_")

    audit_entries = [
        {
            "step": "persist_request",
            "id": gate.get("persist_request_id"),
            "status": gate.get("persist_request_status"),
            "persisted": False,
        },
        {
            "step": "rollback_plan",
            "id": gate.get("rollback_plan_id"),
            "status": gate.get("rollback_plan_status"),
            "persisted": False,
        },
        {
            "step": "persist_gate",
            "id": gate.get("persist_gate_id"),
            "status": gate.get("persist_gate_status"),
            "persisted": False,
        },
    ]

    if audit_status == "audit_ledger_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_audit_ledger_persistence"
        audit_message_text = "Audit ledger is waiting for real Agent output."
    elif audit_status == "audit_ledger_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        audit_message_text = "Audit ledger is waiting for required user action."
    elif audit_status == "audit_ledger_waiting_for_explicit_approval":
        recommended_next_state = "add_explicit_persist_gate_and_audit_storage"
        audit_message_text = "Audit ledger is structurally available, but persistence is disabled in dry-run."
    else:
        recommended_next_state = "fix_audit_ledger_blockers"
        audit_message_text = "Audit ledger is blocked by persist gate or upstream checks."

    audit_payload = {
        "audit_ledger_version": AGENT_RUNNER_AUDIT_LEDGER_VERSION,
        "audit_ledger_status": audit_status,
        "audit_ledger_id": audit_ledger_id,
        "persist_gate_id": gate.get("persist_gate_id"),
        "target_agent_id": target_agent_id,
        "audit_entries": audit_entries,
        "audit_entry_count": len(audit_entries),
        "dry_run": True,
        "audit_ledger_recorded": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_execution_performed": False,
    }

    audit_message = build_agent_message(
        message_type="runner_audit_ledger_dry_run",
        source_agent_id="runner_persistence_manager",
        target_agent_id=target_agent_id,
        payload=audit_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "audit_ledger_version": AGENT_RUNNER_AUDIT_LEDGER_VERSION,
        "audit_ledger_id": audit_ledger_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_persist_gate_dry_run_api"),
        "audit_ledger_status": audit_status,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(gate.get("target_agent_stage") or ""),
        "persist_gate_id": str(gate.get("persist_gate_id") or ""),
        "persist_gate_status": str(gate.get("persist_gate_status") or ""),
        "persist_request_id": str(gate.get("persist_request_id") or ""),
        "rollback_plan_id": str(gate.get("rollback_plan_id") or ""),
        "audit_entries": audit_entries,
        "audit_entry_count": len(audit_entries),
        "recommended_next_state": recommended_next_state,
        "audit_message_text": audit_message_text,
        "persist_gate_summary": build_agent_runner_persist_gate_summary(gate),
        "transition_persist_request_summary": deepcopy(gate.get("transition_persist_request_summary") or {}),
        "rollback_plan_summary": deepcopy(gate.get("rollback_plan_summary") or {}),
        "gate_message": deepcopy(gate.get("gate_message") or {}),
        "audit_payload": audit_payload,
        "audit_message": audit_message,
        "dry_run": True,
        "audit_ledger_recorded": False,
        "persist_gate_recorded": False,
        "write_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_audit_ledger_summary(audit_ledger: dict[str, Any]) -> dict[str, Any]:
    safe_ledger = audit_ledger if isinstance(audit_ledger, dict) else {}
    return {
        "summary_version": "agent_runner_audit_ledger_summary_v1",
        "audit_ledger_version": str(safe_ledger.get("audit_ledger_version") or AGENT_RUNNER_AUDIT_LEDGER_VERSION),
        "audit_ledger_id": str(safe_ledger.get("audit_ledger_id") or ""),
        "project_id": str(safe_ledger.get("project_id") or "demo_project_default"),
        "audit_ledger_status": str(safe_ledger.get("audit_ledger_status") or "audit_ledger_blocked"),
        "target_agent_id": str(safe_ledger.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_ledger.get("target_agent_stage") or ""),
        "persist_gate_id": str(safe_ledger.get("persist_gate_id") or ""),
        "audit_entry_count": int(safe_ledger.get("audit_entry_count") or 0),
        "audit_ledger_recorded": False,
        "persist_gate_recorded": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_APPROVAL_REQUEST_VERSION = "agent_runner_approval_request_v1"
AGENT_RUNNER_POLICY_DECISION_VERSION = "agent_runner_policy_decision_v1"


def _approval_request_status_from_gate(persist_gate: dict[str, Any]) -> str:
    safe_gate = persist_gate if isinstance(persist_gate, dict) else {}
    status = str(safe_gate.get("persist_gate_status") or "persist_gate_blocked")
    if status == "persist_gate_waiting_for_real_agent_output":
        return "approval_request_waiting_for_real_agent_output"
    if status == "persist_gate_waiting_for_user":
        return "approval_request_waiting_for_user"
    if status == "persist_gate_waiting_for_explicit_approval":
        return "approval_request_ready_for_explicit_review"
    return "approval_request_blocked"


def build_agent_runner_approval_request(
    persist_gate: dict[str, Any],
    audit_ledger: dict[str, Any] | None = None,
    requested_by: str = "runner_approval_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run approval request for a future persist gate.

    This prepares the approval envelope. It does not approve writes, persist
    state, execute agents, call providers, or record approval.
    """

    gate = persist_gate if isinstance(persist_gate, dict) else {}
    ledger = audit_ledger if isinstance(audit_ledger, dict) else {}
    project_id = str(gate.get("project_id") or ledger.get("project_id") or "demo_project_default")
    target_agent_id = str(gate.get("target_agent_id") or ledger.get("target_agent_id") or "")
    approval_request_status = _approval_request_status_from_gate(gate)
    approval_request_id = f"approval_request_{project_id}_{target_agent_id or 'none'}_{approval_request_status}".replace(" ", "_")

    required_approvals = [
        {
            "approval_id": "explicit_persist_approval",
            "required": True,
            "present": False,
            "message": "A future explicit approval is required before any persistent write.",
        },
        {
            "approval_id": "rollback_readiness_approval",
            "required": True,
            "present": bool(gate.get("rollback_available")),
            "message": "Rollback readiness must be confirmed before persistent write.",
        },
        {
            "approval_id": "real_agent_output_approval",
            "required": True,
            "present": approval_request_status not in {"approval_request_waiting_for_real_agent_output"},
            "message": "Real Agent output must exist before approval can be granted.",
        },
    ]

    if approval_request_status == "approval_request_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_approval"
        approval_message_text = "Approval request is waiting for real Agent output."
    elif approval_request_status == "approval_request_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        approval_message_text = "Approval request is waiting for required user action."
    elif approval_request_status == "approval_request_ready_for_explicit_review":
        recommended_next_state = "add_explicit_review_ui_or_policy_gate"
        approval_message_text = "Approval request is structurally ready, but no explicit approval exists in dry-run."
    else:
        recommended_next_state = "fix_approval_request_blockers"
        approval_message_text = "Approval request is blocked by persist gate, audit ledger, or upstream checks."

    approval_payload = {
        "approval_request_version": AGENT_RUNNER_APPROVAL_REQUEST_VERSION,
        "approval_request_status": approval_request_status,
        "approval_request_id": approval_request_id,
        "persist_gate_id": gate.get("persist_gate_id"),
        "audit_ledger_id": ledger.get("audit_ledger_id"),
        "target_agent_id": target_agent_id,
        "required_approvals": required_approvals,
        "required_approval_count": len(required_approvals),
        "dry_run": True,
        "approval_recorded": False,
        "approval_granted": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
    }

    approval_message = build_agent_message(
        message_type="runner_approval_request_dry_run",
        source_agent_id="runner_approval_manager",
        target_agent_id=target_agent_id,
        payload=approval_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "approval_request_version": AGENT_RUNNER_APPROVAL_REQUEST_VERSION,
        "approval_request_id": approval_request_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_approval_dry_run_api"),
        "approval_request_status": approval_request_status,
        "approval_granted": False,
        "approval_recorded": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(gate.get("target_agent_stage") or ledger.get("target_agent_stage") or ""),
        "persist_gate_id": str(gate.get("persist_gate_id") or ""),
        "persist_gate_status": str(gate.get("persist_gate_status") or ""),
        "audit_ledger_id": str(ledger.get("audit_ledger_id") or ""),
        "audit_ledger_status": str(ledger.get("audit_ledger_status") or ""),
        "required_approvals": required_approvals,
        "required_approval_count": len(required_approvals),
        "recommended_next_state": recommended_next_state,
        "approval_message_text": approval_message_text,
        "persist_gate_summary": build_agent_runner_persist_gate_summary(gate),
        "audit_ledger_summary": build_agent_runner_audit_ledger_summary(ledger),
        "gate_message": deepcopy(gate.get("gate_message") or {}),
        "audit_message": deepcopy(ledger.get("audit_message") or {}),
        "approval_payload": approval_payload,
        "approval_message": approval_message,
        "dry_run": True,
        "persist_gate_recorded": False,
        "audit_ledger_recorded": False,
        "explicit_approval_present": False,
        "write_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_approval_request_summary(approval_request: dict[str, Any]) -> dict[str, Any]:
    safe_request = approval_request if isinstance(approval_request, dict) else {}
    return {
        "summary_version": "agent_runner_approval_request_summary_v1",
        "approval_request_version": str(safe_request.get("approval_request_version") or AGENT_RUNNER_APPROVAL_REQUEST_VERSION),
        "approval_request_id": str(safe_request.get("approval_request_id") or ""),
        "project_id": str(safe_request.get("project_id") or "demo_project_default"),
        "approval_request_status": str(safe_request.get("approval_request_status") or "approval_request_blocked"),
        "approval_granted": False,
        "approval_recorded": False,
        "target_agent_id": str(safe_request.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_request.get("target_agent_stage") or ""),
        "persist_gate_id": str(safe_request.get("persist_gate_id") or ""),
        "audit_ledger_id": str(safe_request.get("audit_ledger_id") or ""),
        "required_approval_count": int(safe_request.get("required_approval_count") or 0),
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _policy_decision_status_from_approval(approval_request: dict[str, Any]) -> str:
    safe_request = approval_request if isinstance(approval_request, dict) else {}
    status = str(safe_request.get("approval_request_status") or "approval_request_blocked")
    if status == "approval_request_waiting_for_real_agent_output":
        return "policy_decision_waiting_for_real_agent_output"
    if status == "approval_request_waiting_for_user":
        return "policy_decision_waiting_for_user"
    if status == "approval_request_ready_for_explicit_review":
        return "policy_decision_review_required"
    return "policy_decision_blocked"


def build_agent_runner_policy_decision(
    approval_request: dict[str, Any],
    requested_by: str = "runner_approval_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run policy decision from an approval request.

    The decision stays non-approving in dry-run mode.
    """

    request = approval_request if isinstance(approval_request, dict) else {}
    project_id = str(request.get("project_id") or "demo_project_default")
    target_agent_id = str(request.get("target_agent_id") or "")
    policy_decision_status = _policy_decision_status_from_approval(request)
    policy_decision_id = f"policy_decision_{project_id}_{target_agent_id or 'none'}_{policy_decision_status}".replace(" ", "_")

    policy_checks = [
        {
            "policy_id": "dry_run_no_write",
            "passed": True,
            "message": "Dry-run policy forbids writes.",
        },
        {
            "policy_id": "approval_granted",
            "passed": False,
            "message": "Approval is not granted in dry-run mode.",
        },
        {
            "policy_id": "cost_boundary",
            "passed": True,
            "message": "No external provider call or cost is allowed in this dry-run chain.",
        },
        {
            "policy_id": "autonomous_routing_boundary",
            "passed": True,
            "message": "Autonomous LLM routing remains disabled.",
        },
    ]

    if policy_decision_status == "policy_decision_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_policy_decision"
        policy_message_text = "Policy decision is waiting for real Agent output."
    elif policy_decision_status == "policy_decision_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        policy_message_text = "Policy decision is waiting for required user action."
    elif policy_decision_status == "policy_decision_review_required":
        recommended_next_state = "implement_explicit_policy_review_before_persist"
        policy_message_text = "Policy decision requires explicit review; dry-run cannot approve writes."
    else:
        recommended_next_state = "fix_policy_decision_blockers"
        policy_message_text = "Policy decision is blocked by approval request or upstream checks."

    decision_payload = {
        "policy_decision_version": AGENT_RUNNER_POLICY_DECISION_VERSION,
        "policy_decision_status": policy_decision_status,
        "policy_decision_id": policy_decision_id,
        "approval_request_id": request.get("approval_request_id"),
        "target_agent_id": target_agent_id,
        "policy_checks": policy_checks,
        "policy_check_count": len(policy_checks),
        "dry_run": True,
        "policy_decision_recorded": False,
        "policy_approved": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
    }

    decision_message = build_agent_message(
        message_type="runner_policy_decision_dry_run",
        source_agent_id="runner_approval_manager",
        target_agent_id=target_agent_id,
        payload=decision_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "policy_decision_version": AGENT_RUNNER_POLICY_DECISION_VERSION,
        "policy_decision_id": policy_decision_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_approval_dry_run_api"),
        "policy_decision_status": policy_decision_status,
        "policy_approved": False,
        "policy_decision_recorded": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(request.get("target_agent_stage") or ""),
        "approval_request_id": str(request.get("approval_request_id") or ""),
        "approval_request_status": str(request.get("approval_request_status") or ""),
        "persist_gate_id": str(request.get("persist_gate_id") or ""),
        "audit_ledger_id": str(request.get("audit_ledger_id") or ""),
        "policy_checks": policy_checks,
        "policy_check_count": len(policy_checks),
        "recommended_next_state": recommended_next_state,
        "policy_message_text": policy_message_text,
        "approval_request_summary": build_agent_runner_approval_request_summary(request),
        "persist_gate_summary": deepcopy(request.get("persist_gate_summary") or {}),
        "audit_ledger_summary": deepcopy(request.get("audit_ledger_summary") or {}),
        "approval_message": deepcopy(request.get("approval_message") or {}),
        "decision_payload": decision_payload,
        "decision_message": decision_message,
        "dry_run": True,
        "approval_granted": False,
        "approval_recorded": False,
        "persist_gate_recorded": False,
        "audit_ledger_recorded": False,
        "explicit_approval_present": False,
        "write_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_policy_decision_summary(policy_decision: dict[str, Any]) -> dict[str, Any]:
    safe_decision = policy_decision if isinstance(policy_decision, dict) else {}
    return {
        "summary_version": "agent_runner_policy_decision_summary_v1",
        "policy_decision_version": str(safe_decision.get("policy_decision_version") or AGENT_RUNNER_POLICY_DECISION_VERSION),
        "policy_decision_id": str(safe_decision.get("policy_decision_id") or ""),
        "project_id": str(safe_decision.get("project_id") or "demo_project_default"),
        "policy_decision_status": str(safe_decision.get("policy_decision_status") or "policy_decision_blocked"),
        "policy_approved": False,
        "policy_decision_recorded": False,
        "target_agent_id": str(safe_decision.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_decision.get("target_agent_stage") or ""),
        "approval_request_id": str(safe_decision.get("approval_request_id") or ""),
        "policy_check_count": int(safe_decision.get("policy_check_count") or 0),
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_AUTHORIZATION_PREVIEW_VERSION = "agent_runner_authorization_preview_v1"
AGENT_RUNNER_EXECUTION_MANIFEST_VERSION = "agent_runner_execution_manifest_v1"


def _authorization_preview_status_from_policy(policy_decision: dict[str, Any]) -> str:
    safe_decision = policy_decision if isinstance(policy_decision, dict) else {}
    status = str(safe_decision.get("policy_decision_status") or "policy_decision_blocked")
    if status == "policy_decision_waiting_for_real_agent_output":
        return "authorization_waiting_for_real_agent_output"
    if status == "policy_decision_waiting_for_user":
        return "authorization_waiting_for_user"
    if status == "policy_decision_review_required":
        return "authorization_waiting_for_explicit_review"
    return "authorization_blocked"


def build_agent_runner_authorization_preview(
    policy_decision: dict[str, Any],
    requested_by: str = "runner_authorization_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run authorization preview from a policy decision.

    This prepares the authorization shape for future execution, but never
    creates real credentials, authorizes writes, calls providers, or runs an
    Agent.
    """

    decision = policy_decision if isinstance(policy_decision, dict) else {}
    project_id = str(decision.get("project_id") or "demo_project_default")
    target_agent_id = str(decision.get("target_agent_id") or "")
    authorization_status = _authorization_preview_status_from_policy(decision)
    authorization_preview_id = f"authorization_preview_{project_id}_{target_agent_id or 'none'}_{authorization_status}".replace(" ", "_")

    authorization_scopes = [
        {
            "scope": "agent_execution",
            "requested": True,
            "granted": False,
            "message": "Agent execution remains disabled in dry-run.",
        },
        {
            "scope": "state_write",
            "requested": True,
            "granted": False,
            "message": "State write remains disabled in dry-run.",
        },
        {
            "scope": "external_provider_call",
            "requested": False,
            "granted": False,
            "message": "External provider calls are not requested in this dry-run path.",
        },
        {
            "scope": "cost_spend",
            "requested": False,
            "granted": False,
            "message": "No CrossGrowth cost may be incurred in dry-run.",
        },
    ]

    if authorization_status == "authorization_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_authorization"
        authorization_message_text = "Authorization preview is waiting for real Agent output."
    elif authorization_status == "authorization_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        authorization_message_text = "Authorization preview is waiting for required user action."
    elif authorization_status == "authorization_waiting_for_explicit_review":
        recommended_next_state = "implement_explicit_review_before_authorization"
        authorization_message_text = "Authorization preview is structurally available, but no real authorization is granted in dry-run."
    else:
        recommended_next_state = "fix_authorization_blockers"
        authorization_message_text = "Authorization preview is blocked by policy decision or upstream checks."

    authorization_payload = {
        "authorization_preview_version": AGENT_RUNNER_AUTHORIZATION_PREVIEW_VERSION,
        "authorization_status": authorization_status,
        "authorization_preview_id": authorization_preview_id,
        "policy_decision_id": decision.get("policy_decision_id"),
        "approval_request_id": decision.get("approval_request_id"),
        "target_agent_id": target_agent_id,
        "authorization_scopes": authorization_scopes,
        "authorization_scope_count": len(authorization_scopes),
        "dry_run": True,
        "authorization_recorded": False,
        "authorization_granted": False,
        "authorization_token_issued": False,
        "write_authorized": False,
        "agent_execution_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
    }

    authorization_message = build_agent_message(
        message_type="runner_authorization_preview_dry_run",
        source_agent_id="runner_authorization_manager",
        target_agent_id=target_agent_id,
        payload=authorization_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "authorization_preview_version": AGENT_RUNNER_AUTHORIZATION_PREVIEW_VERSION,
        "authorization_preview_id": authorization_preview_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_authorization_dry_run_api"),
        "authorization_status": authorization_status,
        "authorization_granted": False,
        "authorization_recorded": False,
        "authorization_token_issued": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(decision.get("target_agent_stage") or ""),
        "policy_decision_id": str(decision.get("policy_decision_id") or ""),
        "policy_decision_status": str(decision.get("policy_decision_status") or ""),
        "approval_request_id": str(decision.get("approval_request_id") or ""),
        "authorization_scopes": authorization_scopes,
        "authorization_scope_count": len(authorization_scopes),
        "recommended_next_state": recommended_next_state,
        "authorization_message_text": authorization_message_text,
        "policy_decision_summary": build_agent_runner_policy_decision_summary(decision),
        "approval_request_summary": deepcopy(decision.get("approval_request_summary") or {}),
        "decision_message": deepcopy(decision.get("decision_message") or {}),
        "authorization_payload": authorization_payload,
        "authorization_message": authorization_message,
        "dry_run": True,
        "policy_approved": False,
        "approval_granted": False,
        "approval_recorded": False,
        "explicit_approval_present": False,
        "write_authorized": False,
        "agent_execution_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_authorization_preview_summary(authorization_preview: dict[str, Any]) -> dict[str, Any]:
    safe_preview = authorization_preview if isinstance(authorization_preview, dict) else {}
    return {
        "summary_version": "agent_runner_authorization_preview_summary_v1",
        "authorization_preview_version": str(safe_preview.get("authorization_preview_version") or AGENT_RUNNER_AUTHORIZATION_PREVIEW_VERSION),
        "authorization_preview_id": str(safe_preview.get("authorization_preview_id") or ""),
        "project_id": str(safe_preview.get("project_id") or "demo_project_default"),
        "authorization_status": str(safe_preview.get("authorization_status") or "authorization_blocked"),
        "authorization_granted": False,
        "authorization_recorded": False,
        "authorization_token_issued": False,
        "target_agent_id": str(safe_preview.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_preview.get("target_agent_stage") or ""),
        "policy_decision_id": str(safe_preview.get("policy_decision_id") or ""),
        "authorization_scope_count": int(safe_preview.get("authorization_scope_count") or 0),
        "write_authorized": False,
        "agent_execution_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _execution_manifest_status_from_authorization(authorization_preview: dict[str, Any]) -> str:
    safe_preview = authorization_preview if isinstance(authorization_preview, dict) else {}
    status = str(safe_preview.get("authorization_status") or "authorization_blocked")
    if status == "authorization_waiting_for_real_agent_output":
        return "execution_manifest_waiting_for_real_agent_output"
    if status == "authorization_waiting_for_user":
        return "execution_manifest_waiting_for_user"
    if status == "authorization_waiting_for_explicit_review":
        return "execution_manifest_waiting_for_explicit_review"
    return "execution_manifest_blocked"


def build_agent_runner_execution_manifest(
    authorization_preview: dict[str, Any],
    requested_by: str = "runner_authorization_dry_run_api",
) -> dict[str, Any]:
    """Build a dry-run execution manifest from an authorization preview.

    This manifest is a preflight checklist, not an execution command.
    """

    preview = authorization_preview if isinstance(authorization_preview, dict) else {}
    project_id = str(preview.get("project_id") or "demo_project_default")
    target_agent_id = str(preview.get("target_agent_id") or "")
    manifest_status = _execution_manifest_status_from_authorization(preview)
    execution_manifest_id = f"execution_manifest_{project_id}_{target_agent_id or 'none'}_{manifest_status}".replace(" ", "_")

    manifest_items = [
        {
            "item_id": "target_agent",
            "value": target_agent_id,
            "ready": bool(target_agent_id),
        },
        {
            "item_id": "policy_decision",
            "value": preview.get("policy_decision_status"),
            "ready": False,
        },
        {
            "item_id": "authorization",
            "value": preview.get("authorization_status"),
            "ready": False,
        },
        {
            "item_id": "dry_run_boundary",
            "value": "enabled",
            "ready": True,
        },
    ]

    if manifest_status == "execution_manifest_waiting_for_real_agent_output":
        recommended_next_state = "run_real_agent_before_manifest_execution"
        manifest_message_text = "Execution manifest is waiting for real Agent output."
    elif manifest_status == "execution_manifest_waiting_for_user":
        recommended_next_state = "collect_required_user_input"
        manifest_message_text = "Execution manifest is waiting for required user action."
    elif manifest_status == "execution_manifest_waiting_for_explicit_review":
        recommended_next_state = "add_explicit_review_and_execution_authorization"
        manifest_message_text = "Execution manifest is structurally available, but execution remains disabled."
    else:
        recommended_next_state = "fix_execution_manifest_blockers"
        manifest_message_text = "Execution manifest is blocked by authorization preview or upstream checks."

    manifest_payload = {
        "execution_manifest_version": AGENT_RUNNER_EXECUTION_MANIFEST_VERSION,
        "execution_manifest_status": manifest_status,
        "execution_manifest_id": execution_manifest_id,
        "authorization_preview_id": preview.get("authorization_preview_id"),
        "policy_decision_id": preview.get("policy_decision_id"),
        "target_agent_id": target_agent_id,
        "manifest_items": manifest_items,
        "manifest_item_count": len(manifest_items),
        "dry_run": True,
        "manifest_recorded": False,
        "execution_started": False,
        "agent_execution_authorized": False,
        "agent_execution_performed": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
    }

    manifest_message = build_agent_message(
        message_type="runner_execution_manifest_dry_run",
        source_agent_id="runner_authorization_manager",
        target_agent_id=target_agent_id,
        payload=manifest_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "execution_manifest_version": AGENT_RUNNER_EXECUTION_MANIFEST_VERSION,
        "execution_manifest_id": execution_manifest_id,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_authorization_dry_run_api"),
        "execution_manifest_status": manifest_status,
        "execution_started": False,
        "manifest_recorded": False,
        "target_agent_id": target_agent_id,
        "target_agent_stage": str(preview.get("target_agent_stage") or ""),
        "authorization_preview_id": str(preview.get("authorization_preview_id") or ""),
        "authorization_status": str(preview.get("authorization_status") or ""),
        "policy_decision_id": str(preview.get("policy_decision_id") or ""),
        "policy_decision_status": str(preview.get("policy_decision_status") or ""),
        "manifest_items": manifest_items,
        "manifest_item_count": len(manifest_items),
        "recommended_next_state": recommended_next_state,
        "manifest_message_text": manifest_message_text,
        "authorization_preview_summary": build_agent_runner_authorization_preview_summary(preview),
        "policy_decision_summary": deepcopy(preview.get("policy_decision_summary") or {}),
        "authorization_message": deepcopy(preview.get("authorization_message") or {}),
        "manifest_payload": manifest_payload,
        "manifest_message": manifest_message,
        "dry_run": True,
        "authorization_granted": False,
        "authorization_recorded": False,
        "authorization_token_issued": False,
        "policy_approved": False,
        "approval_granted": False,
        "write_authorized": False,
        "agent_execution_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "next_agent_unlocked": False,
        "handoff_complete": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_execution_manifest_summary(execution_manifest: dict[str, Any]) -> dict[str, Any]:
    safe_manifest = execution_manifest if isinstance(execution_manifest, dict) else {}
    return {
        "summary_version": "agent_runner_execution_manifest_summary_v1",
        "execution_manifest_version": str(safe_manifest.get("execution_manifest_version") or AGENT_RUNNER_EXECUTION_MANIFEST_VERSION),
        "execution_manifest_id": str(safe_manifest.get("execution_manifest_id") or ""),
        "project_id": str(safe_manifest.get("project_id") or "demo_project_default"),
        "execution_manifest_status": str(safe_manifest.get("execution_manifest_status") or "execution_manifest_blocked"),
        "execution_started": False,
        "manifest_recorded": False,
        "target_agent_id": str(safe_manifest.get("target_agent_id") or ""),
        "target_agent_stage": str(safe_manifest.get("target_agent_stage") or ""),
        "authorization_preview_id": str(safe_manifest.get("authorization_preview_id") or ""),
        "manifest_item_count": int(safe_manifest.get("manifest_item_count") or 0),
        "authorization_granted": False,
        "agent_execution_authorized": False,
        "agent_execution_performed": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
        "agent_output_generated": False,
        "agent_invoked": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }





if "AGENT_RUNNER_EXECUTION_SESSION_VERSION" not in globals():
    AGENT_RUNNER_EXECUTION_SESSION_VERSION = "agent_runner_execution_session_v1"
if "AGENT_RUNNER_PREFLIGHT_CERTIFICATE_VERSION" not in globals():
    AGENT_RUNNER_PREFLIGHT_CERTIFICATE_VERSION = "agent_runner_preflight_certificate_v1"
if "AGENT_RUNNER_RUNTIME_SANDBOX_VERSION" not in globals():
    AGENT_RUNNER_RUNTIME_SANDBOX_VERSION = "agent_runner_runtime_sandbox_v1"
if "AGENT_RUNNER_WORKER_BOOTSTRAP_PLAN_VERSION" not in globals():
    AGENT_RUNNER_WORKER_BOOTSTRAP_PLAN_VERSION = "agent_runner_worker_bootstrap_plan_v1"


def _runner_wait_status(upstream_status: str, prefix: str, default_blocked: str) -> str:
    status = str(upstream_status or "")
    if "waiting_for_real_agent_output" in status:
        return f"{prefix}_waiting_for_real_agent_output"
    if "waiting_for_user" in status:
        return f"{prefix}_waiting_for_user"
    if "review" in status or "approval" in status:
        return f"{prefix}_waiting_for_explicit_review"
    if "ready" in status:
        return f"{prefix}_waiting_for_explicit_review"
    return default_blocked


def build_agent_runner_execution_session(
    execution_manifest: dict[str, Any],
    requested_by: str = "runner_runtime_readiness_dry_run_api",
) -> dict[str, Any]:
    manifest = execution_manifest if isinstance(execution_manifest, dict) else {}
    project_id = str(manifest.get("project_id") or "demo_project_default")
    target_agent_id = str(manifest.get("target_agent_id") or "")
    status = _runner_wait_status(
        str(manifest.get("execution_manifest_status") or ""),
        "execution_session",
        "execution_session_blocked",
    )
    execution_session_id = f"execution_session_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    steps = [
        {"step_id": "load_manifest", "status": "previewed", "ready": bool(manifest.get("execution_manifest_id"))},
        {"step_id": "confirm_authorization", "status": "blocked_in_dry_run", "ready": False},
        {"step_id": "start_worker", "status": "blocked_in_dry_run", "ready": False},
        {"step_id": "record_audit", "status": "previewed", "ready": True},
    ]
    payload = {
        "execution_session_version": AGENT_RUNNER_EXECUTION_SESSION_VERSION,
        "execution_session_status": status,
        "execution_session_id": execution_session_id,
        "execution_manifest_id": manifest.get("execution_manifest_id"),
        "target_agent_id": target_agent_id,
        "session_steps": steps,
        "session_step_count": len(steps),
        "dry_run": True,
        "execution_session_recorded": False,
        "session_started": False,
        "worker_started": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_runtime_readiness_dry_run_api"),
        "target_agent_stage": str(manifest.get("target_agent_stage") or ""),
        "execution_manifest_status": str(manifest.get("execution_manifest_status") or ""),
        "authorization_preview_id": str(manifest.get("authorization_preview_id") or ""),
        "execution_manifest_summary": build_agent_runner_execution_manifest_summary(manifest),
        "session_message": build_agent_message(
            message_type="runner_execution_session_dry_run",
            source_agent_id="runner_execution_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "agent_execution_authorized": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_execution_session_summary(execution_session: dict[str, Any]) -> dict[str, Any]:
    safe_session = execution_session if isinstance(execution_session, dict) else {}
    return {
        "summary_version": "agent_runner_execution_session_summary_v1",
        "execution_session_version": str(safe_session.get("execution_session_version") or AGENT_RUNNER_EXECUTION_SESSION_VERSION),
        "execution_session_id": str(safe_session.get("execution_session_id") or ""),
        "project_id": str(safe_session.get("project_id") or "demo_project_default"),
        "execution_session_status": str(safe_session.get("execution_session_status") or "execution_session_blocked"),
        "session_step_count": int(safe_session.get("session_step_count") or 0),
        "session_started": False,
        "worker_started": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_preflight_certificate(
    execution_session: dict[str, Any],
    requested_by: str = "runner_runtime_readiness_dry_run_api",
) -> dict[str, Any]:
    session = execution_session if isinstance(execution_session, dict) else {}
    project_id = str(session.get("project_id") or "demo_project_default")
    target_agent_id = str(session.get("target_agent_id") or "")
    status = _runner_wait_status(
        str(session.get("execution_session_status") or ""),
        "preflight",
        "preflight_blocked",
    )
    preflight_certificate_id = f"preflight_certificate_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    checks = [
        {"check_id": "session_exists", "passed": bool(session.get("execution_session_id"))},
        {"check_id": "execution_not_started", "passed": not bool(session.get("session_started"))},
        {"check_id": "worker_not_started", "passed": not bool(session.get("worker_started"))},
        {"check_id": "no_external_cost", "passed": not bool(session.get("cost_incurred_by_crossgrowth"))},
    ]
    payload = {
        "preflight_certificate_version": AGENT_RUNNER_PREFLIGHT_CERTIFICATE_VERSION,
        "preflight_status": status,
        "preflight_certificate_id": preflight_certificate_id,
        "execution_session_id": session.get("execution_session_id"),
        "target_agent_id": target_agent_id,
        "preflight_checks": checks,
        "preflight_check_count": len(checks),
        "dry_run": True,
        "preflight_certificate_recorded": False,
        "preflight_clearance_granted": False,
        "session_started": False,
        "worker_started": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_runtime_readiness_dry_run_api"),
        "target_agent_stage": str(session.get("target_agent_stage") or ""),
        "execution_session_status": str(session.get("execution_session_status") or ""),
        "execution_manifest_id": str(session.get("execution_manifest_id") or ""),
        "execution_session_summary": build_agent_runner_execution_session_summary(session),
        "certificate_message": build_agent_message(
            message_type="runner_preflight_certificate_dry_run",
            source_agent_id="runner_execution_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "agent_execution_authorized": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_preflight_certificate_summary(preflight_certificate: dict[str, Any]) -> dict[str, Any]:
    safe_certificate = preflight_certificate if isinstance(preflight_certificate, dict) else {}
    return {
        "summary_version": "agent_runner_preflight_certificate_summary_v1",
        "preflight_certificate_version": str(safe_certificate.get("preflight_certificate_version") or AGENT_RUNNER_PREFLIGHT_CERTIFICATE_VERSION),
        "preflight_certificate_id": str(safe_certificate.get("preflight_certificate_id") or ""),
        "project_id": str(safe_certificate.get("project_id") or "demo_project_default"),
        "preflight_status": str(safe_certificate.get("preflight_status") or "preflight_blocked"),
        "preflight_check_count": int(safe_certificate.get("preflight_check_count") or 0),
        "preflight_clearance_granted": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_runtime_sandbox(
    preflight_certificate: dict[str, Any],
    requested_by: str = "runner_runtime_readiness_dry_run_api",
) -> dict[str, Any]:
    certificate = preflight_certificate if isinstance(preflight_certificate, dict) else {}
    project_id = str(certificate.get("project_id") or "demo_project_default")
    target_agent_id = str(certificate.get("target_agent_id") or "")
    status = _runner_wait_status(
        str(certificate.get("preflight_status") or ""),
        "runtime_sandbox",
        "runtime_sandbox_blocked",
    )
    runtime_sandbox_id = f"runtime_sandbox_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    restrictions = [
        {"restriction_id": "no_state_write", "enforced": True},
        {"restriction_id": "no_external_provider_call", "enforced": True},
        {"restriction_id": "no_crossgrowth_cost", "enforced": True},
        {"restriction_id": "no_autonomous_llm_routing", "enforced": True},
    ]
    payload = {
        "runtime_sandbox_version": AGENT_RUNNER_RUNTIME_SANDBOX_VERSION,
        "runtime_sandbox_status": status,
        "runtime_sandbox_id": runtime_sandbox_id,
        "preflight_certificate_id": certificate.get("preflight_certificate_id"),
        "target_agent_id": target_agent_id,
        "sandbox_restrictions": restrictions,
        "sandbox_restriction_count": len(restrictions),
        "dry_run": True,
        "runtime_sandbox_recorded": False,
        "sandbox_active": False,
        "worker_started": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_runtime_readiness_dry_run_api"),
        "target_agent_stage": str(certificate.get("target_agent_stage") or ""),
        "preflight_status": str(certificate.get("preflight_status") or ""),
        "preflight_certificate_summary": build_agent_runner_preflight_certificate_summary(certificate),
        "sandbox_message": build_agent_message(
            message_type="runner_runtime_sandbox_dry_run",
            source_agent_id="runner_execution_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_runtime_sandbox_summary(runtime_sandbox: dict[str, Any]) -> dict[str, Any]:
    safe_sandbox = runtime_sandbox if isinstance(runtime_sandbox, dict) else {}
    return {
        "summary_version": "agent_runner_runtime_sandbox_summary_v1",
        "runtime_sandbox_version": str(safe_sandbox.get("runtime_sandbox_version") or AGENT_RUNNER_RUNTIME_SANDBOX_VERSION),
        "runtime_sandbox_id": str(safe_sandbox.get("runtime_sandbox_id") or ""),
        "project_id": str(safe_sandbox.get("project_id") or "demo_project_default"),
        "runtime_sandbox_status": str(safe_sandbox.get("runtime_sandbox_status") or "runtime_sandbox_blocked"),
        "sandbox_restriction_count": int(safe_sandbox.get("sandbox_restriction_count") or 0),
        "sandbox_active": False,
        "worker_started": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_bootstrap_plan(
    runtime_sandbox: dict[str, Any],
    requested_by: str = "runner_runtime_readiness_dry_run_api",
) -> dict[str, Any]:
    sandbox = runtime_sandbox if isinstance(runtime_sandbox, dict) else {}
    project_id = str(sandbox.get("project_id") or "demo_project_default")
    target_agent_id = str(sandbox.get("target_agent_id") or "")
    status = _runner_wait_status(
        str(sandbox.get("runtime_sandbox_status") or ""),
        "worker_bootstrap",
        "worker_bootstrap_blocked",
    )
    worker_bootstrap_plan_id = f"worker_bootstrap_plan_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    bootstrap_steps = [
        {"step_id": "load_runtime_sandbox", "ready": bool(sandbox.get("runtime_sandbox_id"))},
        {"step_id": "prepare_worker_context", "ready": False},
        {"step_id": "bind_queue_claim", "ready": False},
        {"step_id": "start_worker_loop", "ready": False},
    ]
    payload = {
        "worker_bootstrap_plan_version": AGENT_RUNNER_WORKER_BOOTSTRAP_PLAN_VERSION,
        "worker_bootstrap_status": status,
        "worker_bootstrap_plan_id": worker_bootstrap_plan_id,
        "runtime_sandbox_id": sandbox.get("runtime_sandbox_id"),
        "target_agent_id": target_agent_id,
        "bootstrap_steps": bootstrap_steps,
        "bootstrap_step_count": len(bootstrap_steps),
        "dry_run": True,
        "worker_bootstrap_recorded": False,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_runtime_readiness_dry_run_api"),
        "target_agent_stage": str(sandbox.get("target_agent_stage") or ""),
        "runtime_sandbox_status": str(sandbox.get("runtime_sandbox_status") or ""),
        "runtime_sandbox_summary": build_agent_runner_runtime_sandbox_summary(sandbox),
        "bootstrap_message": build_agent_message(
            message_type="runner_worker_bootstrap_plan_dry_run",
            source_agent_id="runner_execution_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "sandbox_active": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_bootstrap_plan_summary(worker_bootstrap_plan: dict[str, Any]) -> dict[str, Any]:
    safe_plan = worker_bootstrap_plan if isinstance(worker_bootstrap_plan, dict) else {}
    return {
        "summary_version": "agent_runner_worker_bootstrap_plan_summary_v1",
        "worker_bootstrap_plan_version": str(safe_plan.get("worker_bootstrap_plan_version") or AGENT_RUNNER_WORKER_BOOTSTRAP_PLAN_VERSION),
        "worker_bootstrap_plan_id": str(safe_plan.get("worker_bootstrap_plan_id") or ""),
        "project_id": str(safe_plan.get("project_id") or "demo_project_default"),
        "worker_bootstrap_status": str(safe_plan.get("worker_bootstrap_status") or "worker_bootstrap_blocked"),
        "bootstrap_step_count": int(safe_plan.get("bootstrap_step_count") or 0),
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }



AGENT_RUNNER_WORKER_POLL_VERSION = "agent_runner_worker_poll_v1"
AGENT_RUNNER_WORKER_HEARTBEAT_VERSION = "agent_runner_worker_heartbeat_v1"
AGENT_RUNNER_WORKER_LOOP_SIMULATION_VERSION = "agent_runner_worker_loop_simulation_v1"
AGENT_RUNNER_FAILURE_RECEIPT_VERSION = "agent_runner_failure_receipt_v1"
AGENT_RUNNER_RETRY_PLAN_VERSION = "agent_runner_retry_plan_v1"
AGENT_RUNNER_RECOVERY_SUMMARY_VERSION = "agent_runner_recovery_summary_v1"


def _runner_worker_wait_status(upstream_status: str, prefix: str, default_blocked: str) -> str:
    status = str(upstream_status or "")
    if "waiting_for_real_agent_output" in status:
        return f"{prefix}_waiting_for_real_agent_output"
    if "waiting_for_user" in status:
        return f"{prefix}_waiting_for_user"
    if "waiting_for_explicit_review" in status or "review" in status:
        return f"{prefix}_waiting_for_explicit_review"
    if "blocked" in status:
        return default_blocked
    return default_blocked


def build_agent_runner_worker_poll(
    worker_bootstrap_plan: dict[str, Any],
    requested_by: str = "runner_worker_loop_dry_run_api",
) -> dict[str, Any]:
    plan = worker_bootstrap_plan if isinstance(worker_bootstrap_plan, dict) else {}
    project_id = str(plan.get("project_id") or "demo_project_default")
    target_agent_id = str(plan.get("target_agent_id") or "")
    status = _runner_worker_wait_status(
        str(plan.get("worker_bootstrap_status") or ""),
        "worker_poll",
        "worker_poll_blocked",
    )
    poll_id = f"worker_poll_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    poll_items = [
        {"poll_item_id": "queue_claim", "available": False, "reason": "dry_run_no_real_queue_claim"},
        {"poll_item_id": "runtime_sandbox", "available": bool(plan.get("runtime_sandbox_id")), "reason": "sandbox_preview_only"},
        {"poll_item_id": "worker_bootstrap", "available": bool(plan.get("worker_bootstrap_plan_id")), "reason": "bootstrap_preview_only"},
    ]
    payload = {
        "worker_poll_version": AGENT_RUNNER_WORKER_POLL_VERSION,
        "worker_poll_status": status,
        "worker_poll_id": poll_id,
        "worker_bootstrap_plan_id": plan.get("worker_bootstrap_plan_id"),
        "target_agent_id": target_agent_id,
        "poll_items": poll_items,
        "poll_item_count": len(poll_items),
        "dry_run": True,
        "worker_poll_recorded": False,
        "queue_item_claimed": False,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_loop_dry_run_api"),
        "target_agent_stage": str(plan.get("target_agent_stage") or ""),
        "worker_bootstrap_status": str(plan.get("worker_bootstrap_status") or ""),
        "worker_bootstrap_plan_summary": build_agent_runner_worker_bootstrap_plan_summary(plan),
        "poll_message": build_agent_message(
            message_type="runner_worker_poll_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_poll_summary(worker_poll: dict[str, Any]) -> dict[str, Any]:
    safe_poll = worker_poll if isinstance(worker_poll, dict) else {}
    return {
        "summary_version": "agent_runner_worker_poll_summary_v1",
        "worker_poll_version": str(safe_poll.get("worker_poll_version") or AGENT_RUNNER_WORKER_POLL_VERSION),
        "worker_poll_id": str(safe_poll.get("worker_poll_id") or ""),
        "project_id": str(safe_poll.get("project_id") or "demo_project_default"),
        "worker_poll_status": str(safe_poll.get("worker_poll_status") or "worker_poll_blocked"),
        "poll_item_count": int(safe_poll.get("poll_item_count") or 0),
        "queue_item_claimed": False,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_heartbeat(
    worker_poll: dict[str, Any],
    requested_by: str = "runner_worker_loop_dry_run_api",
) -> dict[str, Any]:
    poll = worker_poll if isinstance(worker_poll, dict) else {}
    project_id = str(poll.get("project_id") or "demo_project_default")
    target_agent_id = str(poll.get("target_agent_id") or "")
    status = _runner_worker_wait_status(
        str(poll.get("worker_poll_status") or ""),
        "worker_heartbeat",
        "worker_heartbeat_blocked",
    )
    heartbeat_id = f"worker_heartbeat_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    payload = {
        "worker_heartbeat_version": AGENT_RUNNER_WORKER_HEARTBEAT_VERSION,
        "worker_heartbeat_status": status,
        "worker_heartbeat_id": heartbeat_id,
        "worker_poll_id": poll.get("worker_poll_id"),
        "target_agent_id": target_agent_id,
        "heartbeat_interval_seconds": 30,
        "heartbeat_recorded": False,
        "worker_alive": False,
        "dry_run": True,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_loop_dry_run_api"),
        "target_agent_stage": str(poll.get("target_agent_stage") or ""),
        "worker_poll_status": str(poll.get("worker_poll_status") or ""),
        "worker_poll_summary": build_agent_runner_worker_poll_summary(poll),
        "heartbeat_message": build_agent_message(
            message_type="runner_worker_heartbeat_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_heartbeat_summary(worker_heartbeat: dict[str, Any]) -> dict[str, Any]:
    safe_heartbeat = worker_heartbeat if isinstance(worker_heartbeat, dict) else {}
    return {
        "summary_version": "agent_runner_worker_heartbeat_summary_v1",
        "worker_heartbeat_version": str(safe_heartbeat.get("worker_heartbeat_version") or AGENT_RUNNER_WORKER_HEARTBEAT_VERSION),
        "worker_heartbeat_id": str(safe_heartbeat.get("worker_heartbeat_id") or ""),
        "project_id": str(safe_heartbeat.get("project_id") or "demo_project_default"),
        "worker_heartbeat_status": str(safe_heartbeat.get("worker_heartbeat_status") or "worker_heartbeat_blocked"),
        "worker_alive": False,
        "heartbeat_recorded": False,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_loop_simulation(
    worker_heartbeat: dict[str, Any],
    requested_by: str = "runner_worker_loop_dry_run_api",
) -> dict[str, Any]:
    heartbeat = worker_heartbeat if isinstance(worker_heartbeat, dict) else {}
    project_id = str(heartbeat.get("project_id") or "demo_project_default")
    target_agent_id = str(heartbeat.get("target_agent_id") or "")
    status = _runner_worker_wait_status(
        str(heartbeat.get("worker_heartbeat_status") or ""),
        "worker_loop",
        "worker_loop_blocked",
    )
    worker_loop_simulation_id = f"worker_loop_simulation_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    loop_steps = [
        {"loop_step_id": "poll_queue", "simulated": True, "executed": False},
        {"loop_step_id": "send_heartbeat", "simulated": True, "executed": False},
        {"loop_step_id": "run_agent", "simulated": False, "executed": False},
        {"loop_step_id": "write_result", "simulated": False, "executed": False},
    ]
    payload = {
        "worker_loop_simulation_version": AGENT_RUNNER_WORKER_LOOP_SIMULATION_VERSION,
        "worker_loop_status": status,
        "worker_loop_simulation_id": worker_loop_simulation_id,
        "worker_heartbeat_id": heartbeat.get("worker_heartbeat_id"),
        "target_agent_id": target_agent_id,
        "loop_steps": loop_steps,
        "loop_step_count": len(loop_steps),
        "dry_run": True,
        "loop_simulation_recorded": False,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "result_written": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_loop_dry_run_api"),
        "target_agent_stage": str(heartbeat.get("target_agent_stage") or ""),
        "worker_heartbeat_status": str(heartbeat.get("worker_heartbeat_status") or ""),
        "worker_heartbeat_summary": build_agent_runner_worker_heartbeat_summary(heartbeat),
        "loop_message": build_agent_message(
            message_type="runner_worker_loop_simulation_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_loop_simulation_summary(worker_loop_simulation: dict[str, Any]) -> dict[str, Any]:
    safe_loop = worker_loop_simulation if isinstance(worker_loop_simulation, dict) else {}
    return {
        "summary_version": "agent_runner_worker_loop_simulation_summary_v1",
        "worker_loop_simulation_version": str(safe_loop.get("worker_loop_simulation_version") or AGENT_RUNNER_WORKER_LOOP_SIMULATION_VERSION),
        "worker_loop_simulation_id": str(safe_loop.get("worker_loop_simulation_id") or ""),
        "project_id": str(safe_loop.get("project_id") or "demo_project_default"),
        "worker_loop_status": str(safe_loop.get("worker_loop_status") or "worker_loop_blocked"),
        "loop_step_count": int(safe_loop.get("loop_step_count") or 0),
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "result_written": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_failure_receipt(
    worker_loop_simulation: dict[str, Any],
    requested_by: str = "runner_worker_loop_dry_run_api",
) -> dict[str, Any]:
    loop = worker_loop_simulation if isinstance(worker_loop_simulation, dict) else {}
    project_id = str(loop.get("project_id") or "demo_project_default")
    target_agent_id = str(loop.get("target_agent_id") or "")
    upstream_status = str(loop.get("worker_loop_status") or "")
    if "waiting_for_real_agent_output" in upstream_status:
        status = "failure_receipt_waiting_for_real_agent_output"
    elif "waiting_for_user" in upstream_status:
        status = "failure_receipt_waiting_for_user"
    elif "waiting_for_explicit_review" in upstream_status:
        status = "failure_receipt_waiting_for_explicit_review"
    else:
        status = "failure_receipt_blocked"
    failure_receipt_id = f"failure_receipt_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    payload = {
        "failure_receipt_version": AGENT_RUNNER_FAILURE_RECEIPT_VERSION,
        "failure_receipt_status": status,
        "failure_receipt_id": failure_receipt_id,
        "worker_loop_simulation_id": loop.get("worker_loop_simulation_id"),
        "target_agent_id": target_agent_id,
        "failure_detected": False,
        "failure_recorded": False,
        "failure_type": "none_in_dry_run",
        "retry_allowed": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_loop_dry_run_api"),
        "target_agent_stage": str(loop.get("target_agent_stage") or ""),
        "worker_loop_status": upstream_status,
        "worker_loop_simulation_summary": build_agent_runner_worker_loop_simulation_summary(loop),
        "failure_message": build_agent_message(
            message_type="runner_failure_receipt_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_failure_receipt_summary(failure_receipt: dict[str, Any]) -> dict[str, Any]:
    safe_receipt = failure_receipt if isinstance(failure_receipt, dict) else {}
    return {
        "summary_version": "agent_runner_failure_receipt_summary_v1",
        "failure_receipt_version": str(safe_receipt.get("failure_receipt_version") or AGENT_RUNNER_FAILURE_RECEIPT_VERSION),
        "failure_receipt_id": str(safe_receipt.get("failure_receipt_id") or ""),
        "project_id": str(safe_receipt.get("project_id") or "demo_project_default"),
        "failure_receipt_status": str(safe_receipt.get("failure_receipt_status") or "failure_receipt_blocked"),
        "failure_detected": False,
        "failure_recorded": False,
        "retry_allowed": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_retry_plan(
    failure_receipt: dict[str, Any],
    requested_by: str = "runner_worker_loop_dry_run_api",
) -> dict[str, Any]:
    receipt = failure_receipt if isinstance(failure_receipt, dict) else {}
    project_id = str(receipt.get("project_id") or "demo_project_default")
    target_agent_id = str(receipt.get("target_agent_id") or "")
    status = _runner_worker_wait_status(
        str(receipt.get("failure_receipt_status") or ""),
        "retry_plan",
        "retry_plan_blocked",
    )
    retry_plan_id = f"retry_plan_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    retry_steps = [
        {"retry_step_id": "inspect_failure", "ready": bool(receipt.get("failure_receipt_id"))},
        {"retry_step_id": "verify_retry_policy", "ready": False},
        {"retry_step_id": "schedule_retry", "ready": False},
        {"retry_step_id": "record_retry_audit", "ready": False},
    ]
    payload = {
        "retry_plan_version": AGENT_RUNNER_RETRY_PLAN_VERSION,
        "retry_plan_status": status,
        "retry_plan_id": retry_plan_id,
        "failure_receipt_id": receipt.get("failure_receipt_id"),
        "target_agent_id": target_agent_id,
        "retry_steps": retry_steps,
        "retry_step_count": len(retry_steps),
        "retry_allowed": False,
        "retry_scheduled": False,
        "retry_attempt_started": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_loop_dry_run_api"),
        "target_agent_stage": str(receipt.get("target_agent_stage") or ""),
        "failure_receipt_status": str(receipt.get("failure_receipt_status") or ""),
        "failure_receipt_summary": build_agent_runner_failure_receipt_summary(receipt),
        "retry_message": build_agent_message(
            message_type="runner_retry_plan_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_retry_plan_summary(retry_plan: dict[str, Any]) -> dict[str, Any]:
    safe_plan = retry_plan if isinstance(retry_plan, dict) else {}
    return {
        "summary_version": "agent_runner_retry_plan_summary_v1",
        "retry_plan_version": str(safe_plan.get("retry_plan_version") or AGENT_RUNNER_RETRY_PLAN_VERSION),
        "retry_plan_id": str(safe_plan.get("retry_plan_id") or ""),
        "project_id": str(safe_plan.get("project_id") or "demo_project_default"),
        "retry_plan_status": str(safe_plan.get("retry_plan_status") or "retry_plan_blocked"),
        "retry_step_count": int(safe_plan.get("retry_step_count") or 0),
        "retry_allowed": False,
        "retry_scheduled": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_recovery_summary(
    retry_plan: dict[str, Any],
    requested_by: str = "runner_worker_loop_dry_run_api",
) -> dict[str, Any]:
    plan = retry_plan if isinstance(retry_plan, dict) else {}
    project_id = str(plan.get("project_id") or "demo_project_default")
    target_agent_id = str(plan.get("target_agent_id") or "")
    status = _runner_worker_wait_status(
        str(plan.get("retry_plan_status") or ""),
        "recovery",
        "recovery_blocked",
    )
    recovery_summary_id = f"recovery_summary_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    payload = {
        "recovery_summary_version": AGENT_RUNNER_RECOVERY_SUMMARY_VERSION,
        "recovery_status": status,
        "recovery_summary_id": recovery_summary_id,
        "retry_plan_id": plan.get("retry_plan_id"),
        "target_agent_id": target_agent_id,
        "recovery_complete": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "dry_run": True,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "retry_scheduled": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_loop_dry_run_api"),
        "target_agent_stage": str(plan.get("target_agent_stage") or ""),
        "retry_plan_status": str(plan.get("retry_plan_status") or ""),
        "retry_plan_summary": build_agent_runner_retry_plan_summary(plan),
        "recovery_message": build_agent_message(
            message_type="runner_recovery_summary_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_recovery_summary_summary(recovery_summary: dict[str, Any]) -> dict[str, Any]:
    safe_summary = recovery_summary if isinstance(recovery_summary, dict) else {}
    return {
        "summary_version": "agent_runner_recovery_summary_summary_v1",
        "recovery_summary_version": str(safe_summary.get("recovery_summary_version") or AGENT_RUNNER_RECOVERY_SUMMARY_VERSION),
        "recovery_summary_id": str(safe_summary.get("recovery_summary_id") or ""),
        "project_id": str(safe_summary.get("project_id") or "demo_project_default"),
        "recovery_status": str(safe_summary.get("recovery_status") or "recovery_blocked"),
        "recovery_complete": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "retry_scheduled": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_OUTPUT_BUFFER_VERSION = "agent_runner_output_buffer_v1"
AGENT_RUNNER_ARTIFACT_MANIFEST_VERSION = "agent_runner_artifact_manifest_v1"
AGENT_RUNNER_RESULT_VALIDATION_GATE_VERSION = "agent_runner_result_validation_gate_v1"
AGENT_RUNNER_RESUME_CURSOR_VERSION = "agent_runner_resume_cursor_v1"
AGENT_RUNNER_DEAD_LETTER_POLICY_VERSION = "agent_runner_dead_letter_policy_v1"
AGENT_RUNNER_WORKER_CHECKPOINT_BUNDLE_VERSION = "agent_runner_worker_checkpoint_bundle_v1"


def _runner_checkpoint_wait_status(upstream_status: str, prefix: str, default_blocked: str) -> str:
    status = str(upstream_status or "")
    if "waiting_for_real_agent_output" in status:
        return f"{prefix}_waiting_for_real_agent_output"
    if "waiting_for_user" in status:
        return f"{prefix}_waiting_for_user"
    if "waiting_for_explicit_review" in status or "review" in status:
        return f"{prefix}_waiting_for_explicit_review"
    if "blocked" in status:
        return default_blocked
    return default_blocked


def build_agent_runner_output_buffer(
    recovery_summary: dict[str, Any],
    requested_by: str = "runner_worker_checkpoint_dry_run_api",
) -> dict[str, Any]:
    recovery = recovery_summary if isinstance(recovery_summary, dict) else {}
    project_id = str(recovery.get("project_id") or "demo_project_default")
    target_agent_id = str(recovery.get("target_agent_id") or "")
    status = _runner_checkpoint_wait_status(
        str(recovery.get("recovery_status") or ""),
        "output_buffer",
        "output_buffer_blocked",
    )
    output_buffer_id = f"output_buffer_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    buffer_slots = [
        {"slot_id": "agent_text_output", "reserved": True, "written": False},
        {"slot_id": "agent_structured_payload", "reserved": True, "written": False},
        {"slot_id": "agent_artifact_refs", "reserved": True, "written": False},
    ]
    payload = {
        "output_buffer_version": AGENT_RUNNER_OUTPUT_BUFFER_VERSION,
        "output_buffer_status": status,
        "output_buffer_id": output_buffer_id,
        "recovery_summary_id": recovery.get("recovery_summary_id"),
        "target_agent_id": target_agent_id,
        "buffer_slots": buffer_slots,
        "buffer_slot_count": len(buffer_slots),
        "dry_run": True,
        "output_buffer_recorded": False,
        "output_written": False,
        "result_written": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_checkpoint_dry_run_api"),
        "target_agent_stage": str(recovery.get("target_agent_stage") or ""),
        "recovery_status": str(recovery.get("recovery_status") or ""),
        "recovery_summary_summary": build_agent_runner_recovery_summary_summary(recovery),
        "output_buffer_message": build_agent_message(
            message_type="runner_output_buffer_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_output_buffer_summary(output_buffer: dict[str, Any]) -> dict[str, Any]:
    safe_buffer = output_buffer if isinstance(output_buffer, dict) else {}
    return {
        "summary_version": "agent_runner_output_buffer_summary_v1",
        "output_buffer_version": str(safe_buffer.get("output_buffer_version") or AGENT_RUNNER_OUTPUT_BUFFER_VERSION),
        "output_buffer_id": str(safe_buffer.get("output_buffer_id") or ""),
        "project_id": str(safe_buffer.get("project_id") or "demo_project_default"),
        "output_buffer_status": str(safe_buffer.get("output_buffer_status") or "output_buffer_blocked"),
        "buffer_slot_count": int(safe_buffer.get("buffer_slot_count") or 0),
        "output_written": False,
        "result_written": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_artifact_manifest(
    output_buffer: dict[str, Any],
    requested_by: str = "runner_worker_checkpoint_dry_run_api",
) -> dict[str, Any]:
    buffer = output_buffer if isinstance(output_buffer, dict) else {}
    project_id = str(buffer.get("project_id") or "demo_project_default")
    target_agent_id = str(buffer.get("target_agent_id") or "")
    status = _runner_checkpoint_wait_status(
        str(buffer.get("output_buffer_status") or ""),
        "artifact_manifest",
        "artifact_manifest_blocked",
    )
    artifact_manifest_id = f"artifact_manifest_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    artifacts = [
        {"artifact_id": "planned_text_output", "artifact_type": "text", "created": False},
        {"artifact_id": "planned_json_payload", "artifact_type": "json", "created": False},
        {"artifact_id": "planned_audit_trace", "artifact_type": "audit", "created": False},
    ]
    payload = {
        "artifact_manifest_version": AGENT_RUNNER_ARTIFACT_MANIFEST_VERSION,
        "artifact_manifest_status": status,
        "artifact_manifest_id": artifact_manifest_id,
        "output_buffer_id": buffer.get("output_buffer_id"),
        "target_agent_id": target_agent_id,
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "dry_run": True,
        "artifact_manifest_recorded": False,
        "artifact_created": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_checkpoint_dry_run_api"),
        "target_agent_stage": str(buffer.get("target_agent_stage") or ""),
        "output_buffer_status": str(buffer.get("output_buffer_status") or ""),
        "output_buffer_summary": build_agent_runner_output_buffer_summary(buffer),
        "artifact_manifest_message": build_agent_message(
            message_type="runner_artifact_manifest_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_artifact_manifest_summary(artifact_manifest: dict[str, Any]) -> dict[str, Any]:
    safe_manifest = artifact_manifest if isinstance(artifact_manifest, dict) else {}
    return {
        "summary_version": "agent_runner_artifact_manifest_summary_v1",
        "artifact_manifest_version": str(safe_manifest.get("artifact_manifest_version") or AGENT_RUNNER_ARTIFACT_MANIFEST_VERSION),
        "artifact_manifest_id": str(safe_manifest.get("artifact_manifest_id") or ""),
        "project_id": str(safe_manifest.get("project_id") or "demo_project_default"),
        "artifact_manifest_status": str(safe_manifest.get("artifact_manifest_status") or "artifact_manifest_blocked"),
        "artifact_count": int(safe_manifest.get("artifact_count") or 0),
        "artifact_created": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_result_validation_gate(
    artifact_manifest: dict[str, Any],
    requested_by: str = "runner_worker_checkpoint_dry_run_api",
) -> dict[str, Any]:
    manifest = artifact_manifest if isinstance(artifact_manifest, dict) else {}
    project_id = str(manifest.get("project_id") or "demo_project_default")
    target_agent_id = str(manifest.get("target_agent_id") or "")
    status = _runner_checkpoint_wait_status(
        str(manifest.get("artifact_manifest_status") or ""),
        "result_validation_gate",
        "result_validation_gate_blocked",
    )
    validation_gate_id = f"result_validation_gate_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    validation_checks = [
        {"check_id": "schema_shape", "passed": False, "reason": "no_real_agent_output"},
        {"check_id": "evidence_boundary", "passed": False, "reason": "no_real_agent_output"},
        {"check_id": "write_safety", "passed": True, "reason": "dry_run_no_write"},
        {"check_id": "cost_safety", "passed": True, "reason": "dry_run_no_cost"},
    ]
    payload = {
        "result_validation_gate_version": AGENT_RUNNER_RESULT_VALIDATION_GATE_VERSION,
        "result_validation_gate_status": status,
        "result_validation_gate_id": validation_gate_id,
        "artifact_manifest_id": manifest.get("artifact_manifest_id"),
        "target_agent_id": target_agent_id,
        "validation_checks": validation_checks,
        "validation_check_count": len(validation_checks),
        "dry_run": True,
        "validation_passed": False,
        "validation_recorded": False,
        "result_accepted": False,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_checkpoint_dry_run_api"),
        "target_agent_stage": str(manifest.get("target_agent_stage") or ""),
        "artifact_manifest_status": str(manifest.get("artifact_manifest_status") or ""),
        "artifact_manifest_summary": build_agent_runner_artifact_manifest_summary(manifest),
        "validation_gate_message": build_agent_message(
            message_type="runner_result_validation_gate_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_result_validation_gate_summary(result_validation_gate: dict[str, Any]) -> dict[str, Any]:
    safe_gate = result_validation_gate if isinstance(result_validation_gate, dict) else {}
    return {
        "summary_version": "agent_runner_result_validation_gate_summary_v1",
        "result_validation_gate_version": str(safe_gate.get("result_validation_gate_version") or AGENT_RUNNER_RESULT_VALIDATION_GATE_VERSION),
        "result_validation_gate_id": str(safe_gate.get("result_validation_gate_id") or ""),
        "project_id": str(safe_gate.get("project_id") or "demo_project_default"),
        "result_validation_gate_status": str(safe_gate.get("result_validation_gate_status") or "result_validation_gate_blocked"),
        "validation_check_count": int(safe_gate.get("validation_check_count") or 0),
        "validation_passed": False,
        "result_accepted": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_resume_cursor(
    result_validation_gate: dict[str, Any],
    requested_by: str = "runner_worker_checkpoint_dry_run_api",
) -> dict[str, Any]:
    gate = result_validation_gate if isinstance(result_validation_gate, dict) else {}
    project_id = str(gate.get("project_id") or "demo_project_default")
    target_agent_id = str(gate.get("target_agent_id") or "")
    status = _runner_checkpoint_wait_status(
        str(gate.get("result_validation_gate_status") or ""),
        "resume_cursor",
        "resume_cursor_blocked",
    )
    resume_cursor_id = f"resume_cursor_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    payload = {
        "resume_cursor_version": AGENT_RUNNER_RESUME_CURSOR_VERSION,
        "resume_cursor_status": status,
        "resume_cursor_id": resume_cursor_id,
        "result_validation_gate_id": gate.get("result_validation_gate_id"),
        "target_agent_id": target_agent_id,
        "resume_position": "before_real_agent_execution",
        "resume_allowed": False,
        "resume_cursor_recorded": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_checkpoint_dry_run_api"),
        "target_agent_stage": str(gate.get("target_agent_stage") or ""),
        "result_validation_gate_status": str(gate.get("result_validation_gate_status") or ""),
        "result_validation_gate_summary": build_agent_runner_result_validation_gate_summary(gate),
        "resume_cursor_message": build_agent_message(
            message_type="runner_resume_cursor_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_resume_cursor_summary(resume_cursor: dict[str, Any]) -> dict[str, Any]:
    safe_cursor = resume_cursor if isinstance(resume_cursor, dict) else {}
    return {
        "summary_version": "agent_runner_resume_cursor_summary_v1",
        "resume_cursor_version": str(safe_cursor.get("resume_cursor_version") or AGENT_RUNNER_RESUME_CURSOR_VERSION),
        "resume_cursor_id": str(safe_cursor.get("resume_cursor_id") or ""),
        "project_id": str(safe_cursor.get("project_id") or "demo_project_default"),
        "resume_cursor_status": str(safe_cursor.get("resume_cursor_status") or "resume_cursor_blocked"),
        "resume_position": str(safe_cursor.get("resume_position") or "before_real_agent_execution"),
        "resume_allowed": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_dead_letter_policy(
    resume_cursor: dict[str, Any],
    requested_by: str = "runner_worker_checkpoint_dry_run_api",
) -> dict[str, Any]:
    cursor = resume_cursor if isinstance(resume_cursor, dict) else {}
    project_id = str(cursor.get("project_id") or "demo_project_default")
    target_agent_id = str(cursor.get("target_agent_id") or "")
    status = _runner_checkpoint_wait_status(
        str(cursor.get("resume_cursor_status") or ""),
        "dead_letter_policy",
        "dead_letter_policy_blocked",
    )
    dead_letter_policy_id = f"dead_letter_policy_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    policy_rules = [
        {"rule_id": "max_retry_exceeded", "action": "quarantine", "enabled": True},
        {"rule_id": "unsafe_write_detected", "action": "block_and_review", "enabled": True},
        {"rule_id": "missing_evidence", "action": "return_to_planner", "enabled": True},
    ]
    payload = {
        "dead_letter_policy_version": AGENT_RUNNER_DEAD_LETTER_POLICY_VERSION,
        "dead_letter_policy_status": status,
        "dead_letter_policy_id": dead_letter_policy_id,
        "resume_cursor_id": cursor.get("resume_cursor_id"),
        "target_agent_id": target_agent_id,
        "policy_rules": policy_rules,
        "policy_rule_count": len(policy_rules),
        "dead_letter_required": False,
        "dead_letter_recorded": False,
        "manual_review_required": True,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_checkpoint_dry_run_api"),
        "target_agent_stage": str(cursor.get("target_agent_stage") or ""),
        "resume_cursor_status": str(cursor.get("resume_cursor_status") or ""),
        "resume_cursor_summary": build_agent_runner_resume_cursor_summary(cursor),
        "dead_letter_policy_message": build_agent_message(
            message_type="runner_dead_letter_policy_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_dead_letter_policy_summary(dead_letter_policy: dict[str, Any]) -> dict[str, Any]:
    safe_policy = dead_letter_policy if isinstance(dead_letter_policy, dict) else {}
    return {
        "summary_version": "agent_runner_dead_letter_policy_summary_v1",
        "dead_letter_policy_version": str(safe_policy.get("dead_letter_policy_version") or AGENT_RUNNER_DEAD_LETTER_POLICY_VERSION),
        "dead_letter_policy_id": str(safe_policy.get("dead_letter_policy_id") or ""),
        "project_id": str(safe_policy.get("project_id") or "demo_project_default"),
        "dead_letter_policy_status": str(safe_policy.get("dead_letter_policy_status") or "dead_letter_policy_blocked"),
        "policy_rule_count": int(safe_policy.get("policy_rule_count") or 0),
        "dead_letter_required": False,
        "dead_letter_recorded": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_checkpoint_bundle(
    dead_letter_policy: dict[str, Any],
    requested_by: str = "runner_worker_checkpoint_dry_run_api",
) -> dict[str, Any]:
    policy = dead_letter_policy if isinstance(dead_letter_policy, dict) else {}
    project_id = str(policy.get("project_id") or "demo_project_default")
    target_agent_id = str(policy.get("target_agent_id") or "")
    status = _runner_checkpoint_wait_status(
        str(policy.get("dead_letter_policy_status") or ""),
        "worker_checkpoint_bundle",
        "worker_checkpoint_bundle_blocked",
    )
    worker_checkpoint_bundle_id = f"worker_checkpoint_bundle_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    checkpoint_items = [
        {"checkpoint_item_id": "output_buffer", "included": True},
        {"checkpoint_item_id": "artifact_manifest", "included": True},
        {"checkpoint_item_id": "result_validation_gate", "included": True},
        {"checkpoint_item_id": "resume_cursor", "included": True},
        {"checkpoint_item_id": "dead_letter_policy", "included": True},
    ]
    payload = {
        "worker_checkpoint_bundle_version": AGENT_RUNNER_WORKER_CHECKPOINT_BUNDLE_VERSION,
        "worker_checkpoint_bundle_status": status,
        "worker_checkpoint_bundle_id": worker_checkpoint_bundle_id,
        "dead_letter_policy_id": policy.get("dead_letter_policy_id"),
        "target_agent_id": target_agent_id,
        "checkpoint_items": checkpoint_items,
        "checkpoint_item_count": len(checkpoint_items),
        "checkpoint_recorded": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_worker_checkpoint_dry_run_api"),
        "target_agent_stage": str(policy.get("target_agent_stage") or ""),
        "dead_letter_policy_status": str(policy.get("dead_letter_policy_status") or ""),
        "dead_letter_policy_summary": build_agent_runner_dead_letter_policy_summary(policy),
        "worker_checkpoint_bundle_message": build_agent_message(
            message_type="runner_worker_checkpoint_bundle_dry_run",
            source_agent_id="runner_worker_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_worker_checkpoint_bundle_summary(worker_checkpoint_bundle: dict[str, Any]) -> dict[str, Any]:
    safe_bundle = worker_checkpoint_bundle if isinstance(worker_checkpoint_bundle, dict) else {}
    return {
        "summary_version": "agent_runner_worker_checkpoint_bundle_summary_v1",
        "worker_checkpoint_bundle_version": str(safe_bundle.get("worker_checkpoint_bundle_version") or AGENT_RUNNER_WORKER_CHECKPOINT_BUNDLE_VERSION),
        "worker_checkpoint_bundle_id": str(safe_bundle.get("worker_checkpoint_bundle_id") or ""),
        "project_id": str(safe_bundle.get("project_id") or "demo_project_default"),
        "worker_checkpoint_bundle_status": str(safe_bundle.get("worker_checkpoint_bundle_status") or "worker_checkpoint_bundle_blocked"),
        "checkpoint_item_count": int(safe_bundle.get("checkpoint_item_count") or 0),
        "checkpoint_recorded": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }




AGENT_RUNNER_RESULT_ACCEPTANCE_VERSION = "agent_runner_result_acceptance_v1"
AGENT_RUNNER_PROJECT_MERGE_PREVIEW_VERSION = "agent_runner_project_merge_preview_v1"
AGENT_RUNNER_DOWNSTREAM_HANDOFF_VERSION = "agent_runner_downstream_handoff_v1"
AGENT_RUNNER_HUMAN_REVIEW_PACKET_VERSION = "agent_runner_human_review_packet_v1"
AGENT_RUNNER_RUN_FINALIZATION_VERSION = "agent_runner_run_finalization_v1"
AGENT_RUNNER_COMPLETION_LEDGER_VERSION = "agent_runner_completion_ledger_v1"


def _runner_finalization_wait_status(upstream_status: str, prefix: str, default_blocked: str) -> str:
    status = str(upstream_status or "")
    if "waiting_for_real_agent_output" in status:
        return f"{prefix}_waiting_for_real_agent_output"
    if "waiting_for_user" in status:
        return f"{prefix}_waiting_for_user"
    if "waiting_for_explicit_review" in status or "review" in status:
        return f"{prefix}_waiting_for_explicit_review"
    if "blocked" in status:
        return default_blocked
    return default_blocked


def build_agent_runner_result_acceptance(
    worker_checkpoint_bundle: dict[str, Any],
    requested_by: str = "runner_finalization_dry_run_api",
) -> dict[str, Any]:
    bundle = worker_checkpoint_bundle if isinstance(worker_checkpoint_bundle, dict) else {}
    project_id = str(bundle.get("project_id") or "demo_project_default")
    target_agent_id = str(bundle.get("target_agent_id") or "")
    status = _runner_finalization_wait_status(
        str(bundle.get("worker_checkpoint_bundle_status") or ""),
        "result_acceptance",
        "result_acceptance_blocked",
    )
    result_acceptance_id = f"result_acceptance_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    acceptance_checks = [
        {"check_id": "checkpoint_present", "passed": bool(bundle.get("worker_checkpoint_bundle_id"))},
        {"check_id": "result_validation_passed", "passed": False},
        {"check_id": "manual_review_available", "passed": True},
        {"check_id": "dry_run_write_blocked", "passed": True},
    ]
    payload = {
        "result_acceptance_version": AGENT_RUNNER_RESULT_ACCEPTANCE_VERSION,
        "result_acceptance_status": status,
        "result_acceptance_id": result_acceptance_id,
        "worker_checkpoint_bundle_id": bundle.get("worker_checkpoint_bundle_id"),
        "target_agent_id": target_agent_id,
        "acceptance_checks": acceptance_checks,
        "acceptance_check_count": len(acceptance_checks),
        "result_accepted": False,
        "acceptance_recorded": False,
        "manual_review_required": True,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_finalization_dry_run_api"),
        "target_agent_stage": str(bundle.get("target_agent_stage") or ""),
        "worker_checkpoint_bundle_status": str(bundle.get("worker_checkpoint_bundle_status") or ""),
        "worker_checkpoint_bundle_summary": build_agent_runner_worker_checkpoint_bundle_summary(bundle),
        "result_acceptance_message": build_agent_message(
            message_type="runner_result_acceptance_dry_run",
            source_agent_id="runner_finalization_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_result_acceptance_summary(result_acceptance: dict[str, Any]) -> dict[str, Any]:
    safe_acceptance = result_acceptance if isinstance(result_acceptance, dict) else {}
    return {
        "summary_version": "agent_runner_result_acceptance_summary_v1",
        "result_acceptance_version": str(safe_acceptance.get("result_acceptance_version") or AGENT_RUNNER_RESULT_ACCEPTANCE_VERSION),
        "result_acceptance_id": str(safe_acceptance.get("result_acceptance_id") or ""),
        "project_id": str(safe_acceptance.get("project_id") or "demo_project_default"),
        "result_acceptance_status": str(safe_acceptance.get("result_acceptance_status") or "result_acceptance_blocked"),
        "acceptance_check_count": int(safe_acceptance.get("acceptance_check_count") or 0),
        "result_accepted": False,
        "acceptance_recorded": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_project_merge_preview(
    result_acceptance: dict[str, Any],
    requested_by: str = "runner_finalization_dry_run_api",
) -> dict[str, Any]:
    acceptance = result_acceptance if isinstance(result_acceptance, dict) else {}
    project_id = str(acceptance.get("project_id") or "demo_project_default")
    target_agent_id = str(acceptance.get("target_agent_id") or "")
    status = _runner_finalization_wait_status(
        str(acceptance.get("result_acceptance_status") or ""),
        "project_merge_preview",
        "project_merge_preview_blocked",
    )
    merge_preview_id = f"project_merge_preview_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    merge_items = [
        {"merge_item_id": "graph_summary_update", "planned": True, "applied": False},
        {"merge_item_id": "latest_agent_result_ref", "planned": True, "applied": False},
        {"merge_item_id": "workspace_audit_preview", "planned": True, "applied": False},
    ]
    payload = {
        "project_merge_preview_version": AGENT_RUNNER_PROJECT_MERGE_PREVIEW_VERSION,
        "project_merge_preview_status": status,
        "project_merge_preview_id": merge_preview_id,
        "result_acceptance_id": acceptance.get("result_acceptance_id"),
        "target_agent_id": target_agent_id,
        "merge_items": merge_items,
        "merge_item_count": len(merge_items),
        "merge_applied": False,
        "merge_preview_recorded": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_finalization_dry_run_api"),
        "target_agent_stage": str(acceptance.get("target_agent_stage") or ""),
        "result_acceptance_status": str(acceptance.get("result_acceptance_status") or ""),
        "result_acceptance_summary": build_agent_runner_result_acceptance_summary(acceptance),
        "project_merge_preview_message": build_agent_message(
            message_type="runner_project_merge_preview_dry_run",
            source_agent_id="runner_finalization_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_project_merge_preview_summary(project_merge_preview: dict[str, Any]) -> dict[str, Any]:
    safe_preview = project_merge_preview if isinstance(project_merge_preview, dict) else {}
    return {
        "summary_version": "agent_runner_project_merge_preview_summary_v1",
        "project_merge_preview_version": str(safe_preview.get("project_merge_preview_version") or AGENT_RUNNER_PROJECT_MERGE_PREVIEW_VERSION),
        "project_merge_preview_id": str(safe_preview.get("project_merge_preview_id") or ""),
        "project_id": str(safe_preview.get("project_id") or "demo_project_default"),
        "project_merge_preview_status": str(safe_preview.get("project_merge_preview_status") or "project_merge_preview_blocked"),
        "merge_item_count": int(safe_preview.get("merge_item_count") or 0),
        "merge_applied": False,
        "merge_preview_recorded": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_downstream_handoff(
    project_merge_preview: dict[str, Any],
    requested_by: str = "runner_finalization_dry_run_api",
) -> dict[str, Any]:
    preview = project_merge_preview if isinstance(project_merge_preview, dict) else {}
    project_id = str(preview.get("project_id") or "demo_project_default")
    target_agent_id = str(preview.get("target_agent_id") or "")
    status = _runner_finalization_wait_status(
        str(preview.get("project_merge_preview_status") or ""),
        "downstream_handoff",
        "downstream_handoff_blocked",
    )
    downstream_handoff_id = f"downstream_handoff_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    handoff_targets = [
        {"handoff_target_id": "planner_agent", "ready": False},
        {"handoff_target_id": "storyboard_agent", "ready": False},
        {"handoff_target_id": "workspace_review", "ready": True},
    ]
    payload = {
        "downstream_handoff_version": AGENT_RUNNER_DOWNSTREAM_HANDOFF_VERSION,
        "downstream_handoff_status": status,
        "downstream_handoff_id": downstream_handoff_id,
        "project_merge_preview_id": preview.get("project_merge_preview_id"),
        "target_agent_id": target_agent_id,
        "handoff_targets": handoff_targets,
        "handoff_target_count": len(handoff_targets),
        "handoff_ready": False,
        "handoff_recorded": False,
        "next_agent_unlocked": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_finalization_dry_run_api"),
        "target_agent_stage": str(preview.get("target_agent_stage") or ""),
        "project_merge_preview_status": str(preview.get("project_merge_preview_status") or ""),
        "project_merge_preview_summary": build_agent_runner_project_merge_preview_summary(preview),
        "downstream_handoff_message": build_agent_message(
            message_type="runner_downstream_handoff_dry_run",
            source_agent_id="runner_finalization_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_downstream_handoff_summary(downstream_handoff: dict[str, Any]) -> dict[str, Any]:
    safe_handoff = downstream_handoff if isinstance(downstream_handoff, dict) else {}
    return {
        "summary_version": "agent_runner_downstream_handoff_summary_v1",
        "downstream_handoff_version": str(safe_handoff.get("downstream_handoff_version") or AGENT_RUNNER_DOWNSTREAM_HANDOFF_VERSION),
        "downstream_handoff_id": str(safe_handoff.get("downstream_handoff_id") or ""),
        "project_id": str(safe_handoff.get("project_id") or "demo_project_default"),
        "downstream_handoff_status": str(safe_handoff.get("downstream_handoff_status") or "downstream_handoff_blocked"),
        "handoff_target_count": int(safe_handoff.get("handoff_target_count") or 0),
        "handoff_ready": False,
        "handoff_recorded": False,
        "next_agent_unlocked": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_human_review_packet(
    downstream_handoff: dict[str, Any],
    requested_by: str = "runner_finalization_dry_run_api",
) -> dict[str, Any]:
    handoff = downstream_handoff if isinstance(downstream_handoff, dict) else {}
    project_id = str(handoff.get("project_id") or "demo_project_default")
    target_agent_id = str(handoff.get("target_agent_id") or "")
    status = _runner_finalization_wait_status(
        str(handoff.get("downstream_handoff_status") or ""),
        "human_review_packet",
        "human_review_packet_blocked",
    )
    human_review_packet_id = f"human_review_packet_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    review_items = [
        {"review_item_id": "dry_run_boundary", "required": True, "ready": True},
        {"review_item_id": "result_acceptance", "required": True, "ready": False},
        {"review_item_id": "merge_preview", "required": True, "ready": False},
        {"review_item_id": "handoff_plan", "required": True, "ready": False},
    ]
    payload = {
        "human_review_packet_version": AGENT_RUNNER_HUMAN_REVIEW_PACKET_VERSION,
        "human_review_packet_status": status,
        "human_review_packet_id": human_review_packet_id,
        "downstream_handoff_id": handoff.get("downstream_handoff_id"),
        "target_agent_id": target_agent_id,
        "review_items": review_items,
        "review_item_count": len(review_items),
        "human_review_required": True,
        "human_review_recorded": False,
        "approved_by_human": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_finalization_dry_run_api"),
        "target_agent_stage": str(handoff.get("target_agent_stage") or ""),
        "downstream_handoff_status": str(handoff.get("downstream_handoff_status") or ""),
        "downstream_handoff_summary": build_agent_runner_downstream_handoff_summary(handoff),
        "human_review_packet_message": build_agent_message(
            message_type="runner_human_review_packet_dry_run",
            source_agent_id="runner_finalization_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_human_review_packet_summary(human_review_packet: dict[str, Any]) -> dict[str, Any]:
    safe_packet = human_review_packet if isinstance(human_review_packet, dict) else {}
    return {
        "summary_version": "agent_runner_human_review_packet_summary_v1",
        "human_review_packet_version": str(safe_packet.get("human_review_packet_version") or AGENT_RUNNER_HUMAN_REVIEW_PACKET_VERSION),
        "human_review_packet_id": str(safe_packet.get("human_review_packet_id") or ""),
        "project_id": str(safe_packet.get("project_id") or "demo_project_default"),
        "human_review_packet_status": str(safe_packet.get("human_review_packet_status") or "human_review_packet_blocked"),
        "review_item_count": int(safe_packet.get("review_item_count") or 0),
        "human_review_required": True,
        "human_review_recorded": False,
        "approved_by_human": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_run_finalization(
    human_review_packet: dict[str, Any],
    requested_by: str = "runner_finalization_dry_run_api",
) -> dict[str, Any]:
    packet = human_review_packet if isinstance(human_review_packet, dict) else {}
    project_id = str(packet.get("project_id") or "demo_project_default")
    target_agent_id = str(packet.get("target_agent_id") or "")
    status = _runner_finalization_wait_status(
        str(packet.get("human_review_packet_status") or ""),
        "run_finalization",
        "run_finalization_blocked",
    )
    run_finalization_id = f"run_finalization_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    finalization_items = [
        {"finalization_item_id": "no_write_confirmed", "complete": True},
        {"finalization_item_id": "no_cost_confirmed", "complete": True},
        {"finalization_item_id": "manual_review_pending", "complete": False},
        {"finalization_item_id": "next_real_execution_blocked", "complete": True},
    ]
    payload = {
        "run_finalization_version": AGENT_RUNNER_RUN_FINALIZATION_VERSION,
        "run_finalization_status": status,
        "run_finalization_id": run_finalization_id,
        "human_review_packet_id": packet.get("human_review_packet_id"),
        "target_agent_id": target_agent_id,
        "finalization_items": finalization_items,
        "finalization_item_count": len(finalization_items),
        "run_finalized": False,
        "finalization_recorded": False,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_finalization_dry_run_api"),
        "target_agent_stage": str(packet.get("target_agent_stage") or ""),
        "human_review_packet_status": str(packet.get("human_review_packet_status") or ""),
        "human_review_packet_summary": build_agent_runner_human_review_packet_summary(packet),
        "run_finalization_message": build_agent_message(
            message_type="runner_run_finalization_dry_run",
            source_agent_id="runner_finalization_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_run_finalization_summary(run_finalization: dict[str, Any]) -> dict[str, Any]:
    safe_finalization = run_finalization if isinstance(run_finalization, dict) else {}
    return {
        "summary_version": "agent_runner_run_finalization_summary_v1",
        "run_finalization_version": str(safe_finalization.get("run_finalization_version") or AGENT_RUNNER_RUN_FINALIZATION_VERSION),
        "run_finalization_id": str(safe_finalization.get("run_finalization_id") or ""),
        "project_id": str(safe_finalization.get("project_id") or "demo_project_default"),
        "run_finalization_status": str(safe_finalization.get("run_finalization_status") or "run_finalization_blocked"),
        "finalization_item_count": int(safe_finalization.get("finalization_item_count") or 0),
        "run_finalized": False,
        "finalization_recorded": False,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_completion_ledger(
    run_finalization: dict[str, Any],
    requested_by: str = "runner_finalization_dry_run_api",
) -> dict[str, Any]:
    finalization = run_finalization if isinstance(run_finalization, dict) else {}
    project_id = str(finalization.get("project_id") or "demo_project_default")
    target_agent_id = str(finalization.get("target_agent_id") or "")
    status = _runner_finalization_wait_status(
        str(finalization.get("run_finalization_status") or ""),
        "completion_ledger",
        "completion_ledger_blocked",
    )
    completion_ledger_id = f"completion_ledger_{project_id}_{target_agent_id or 'none'}_{status}".replace(" ", "_")
    ledger_entries = [
        {"ledger_entry_id": "result_acceptance_preview", "recorded": False},
        {"ledger_entry_id": "merge_preview", "recorded": False},
        {"ledger_entry_id": "downstream_handoff_preview", "recorded": False},
        {"ledger_entry_id": "human_review_packet", "recorded": False},
        {"ledger_entry_id": "finalization_preview", "recorded": False},
    ]
    payload = {
        "completion_ledger_version": AGENT_RUNNER_COMPLETION_LEDGER_VERSION,
        "completion_ledger_status": status,
        "completion_ledger_id": completion_ledger_id,
        "run_finalization_id": finalization.get("run_finalization_id"),
        "target_agent_id": target_agent_id,
        "ledger_entries": ledger_entries,
        "ledger_entry_count": len(ledger_entries),
        "completion_ledger_recorded": False,
        "run_finalized": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "dry_run": True,
        "agent_execution_performed": False,
    }
    return {
        **payload,
        "project_id": project_id,
        "requested_by": str(requested_by or "runner_finalization_dry_run_api"),
        "target_agent_stage": str(finalization.get("target_agent_stage") or ""),
        "run_finalization_status": str(finalization.get("run_finalization_status") or ""),
        "run_finalization_summary": build_agent_runner_run_finalization_summary(finalization),
        "completion_ledger_message": build_agent_message(
            message_type="runner_completion_ledger_dry_run",
            source_agent_id="runner_finalization_manager",
            target_agent_id=target_agent_id,
            payload=payload,
            run_id="",
            job_id="",
            artifact_ids=[],
            project_id=project_id,
        ),
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "llm_autonomous_decision_enabled": False,
        "safety_boundaries": _graph_safety_boundaries(),
    }


def build_agent_runner_completion_ledger_summary(completion_ledger: dict[str, Any]) -> dict[str, Any]:
    safe_ledger = completion_ledger if isinstance(completion_ledger, dict) else {}
    return {
        "summary_version": "agent_runner_completion_ledger_summary_v1",
        "completion_ledger_version": str(safe_ledger.get("completion_ledger_version") or AGENT_RUNNER_COMPLETION_LEDGER_VERSION),
        "completion_ledger_id": str(safe_ledger.get("completion_ledger_id") or ""),
        "project_id": str(safe_ledger.get("project_id") or "demo_project_default"),
        "completion_ledger_status": str(safe_ledger.get("completion_ledger_status") or "completion_ledger_blocked"),
        "ledger_entry_count": int(safe_ledger.get("ledger_entry_count") or 0),
        "completion_ledger_recorded": False,
        "run_finalized": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "dry_run": True,
        "safety_boundaries": _graph_safety_boundaries(),
    }




def build_product_asset_lock_v2(
    project: dict[str, Any] | None,
    generation_data: dict[str, Any] | None,
    uploaded_assets: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    safe_project = _experiment_rework_dict(project)
    generation = _experiment_rework_dict(generation_data)
    assets = [item for item in (uploaded_assets or []) if isinstance(item, dict)]
    product_assets = [
        item for item in assets if item.get("asset_role") == "product_image"
    ]
    primary = (product_assets or assets or [{}])[0]
    reference_ids = [
        str(item.get("asset_id"))
        for item in assets
        if item.get("asset_id") and item is not primary
    ]
    product_name = str(
        safe_project.get("product_name")
        or generation.get("product_name")
        or _experiment_rework_dict(generation.get("video_generation_packet")).get("product_name")
        or ""
    )
    product_category = str(
        safe_project.get("product_category")
        or generation.get("product_category")
        or _experiment_rework_dict(generation.get("video_generation_packet")).get("product_category")
        or ""
    )
    primary_id = str(primary.get("asset_id") or "")
    asset_source = "uploaded_asset" if primary_id else "product_description"
    if primary_id and (product_name or product_category):
        asset_source = "mixed"
    return {
        "lock_version": "product_asset_lock_v2",
        "project_id": str(safe_project.get("project_id") or generation.get("project_id") or "demo_project_default"),
        "source_agent_id": "asset_lock_agent",
        "asset_source": asset_source,
        "primary_asset_id": primary_id,
        "reference_asset_ids": reference_ids,
        "product_name": product_name,
        "product_category": product_category,
        "identity_constraints": [
            value
            for value in (
                f"Preserve the visible identity of uploaded asset {primary_id}." if primary_id else "",
                f"Keep the product recognizable as {product_name}." if product_name else "",
                f"Keep category cues consistent with {product_category}." if product_category else "",
            )
            if value
        ],
        "must_preserve": [
            "Product shape, packaging, proportions, and visible branding supplied by the user.",
            "Evidence-backed product identity across every generated scene.",
        ],
        "must_not_change": [
            "Do not invent a different product, package, color, size, or logo.",
            "Do not infer image details that are not visible in the uploaded asset metadata.",
        ],
        "handoff_usage": {
            "use_primary_image_as_identity_reference": bool(primary_id),
            "requires_manual_upload_to_external_tool": True,
        },
        "safety_boundaries": _graph_safety_boundaries(),
    }


def _artifact_summary(value: Any, fallback: str) -> str:
    if isinstance(value, dict):
        for key in (
            "headline",
            "recommended_next_action",
            "reason",
            "summary",
            "approval_prompt",
            "decision_type",
            "status",
        ):
            text = str(value.get(key) or "").strip()
            if text:
                return _experiment_rework_text(text, limit=240)
    return fallback


def build_lightweight_artifact_registry(
    generation_data: dict[str, Any] | None = None,
    job: dict[str, Any] | None = None,
    run: dict[str, Any] | None = None,
    experiment: dict[str, Any] | None = None,
    project: dict[str, Any] | None = None,
    uploaded_assets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic registry across generation, run, job, and experiment artifacts."""

    generation = _experiment_rework_dict(generation_data)
    safe_job = _experiment_rework_dict(job)
    safe_run = _experiment_rework_dict(run)
    safe_experiment = _experiment_rework_dict(experiment)
    safe_project = _experiment_rework_dict(project)
    run_result = _experiment_rework_dict(safe_run.get("result"))
    source_generation = _experiment_rework_dict(safe_job.get("source_generation"))
    graph_feedback = _experiment_rework_dict(safe_job.get("agent_graph_feedback"))
    experiments = list(safe_job.get("external_video_experiments") or [])
    latest_experiment = safe_experiment or (experiments[-1] if experiments else {})
    rework_run_id = str(
        latest_experiment.get("linked_rework_run_id")
        or latest_experiment.get("triggered_rework_run_id")
        or graph_feedback.get("latest_rework_run_id")
        or ""
    )
    project_id = str(
        safe_project.get("project_id")
        or safe_job.get("project_id")
        or safe_run.get("project_id")
        or generation.get("project_id")
        or "demo_project_default"
    )
    product_asset_lock_v2 = (
        generation.get("product_asset_lock_v2")
        or safe_job.get("product_asset_lock_v2")
        or run_result.get("product_asset_lock_v2")
    )
    if not isinstance(product_asset_lock_v2, dict) or not product_asset_lock_v2:
        product_asset_lock_v2 = build_product_asset_lock_v2(
            {**safe_project, "project_id": project_id},
            generation or source_generation,
            uploaded_assets,
        )
    project_source = (
        generation.get("project_source")
        or source_generation.get("project_source")
        or run_result.get("project_source")
    )
    source_quality_gate = (
        generation.get("source_quality_gate")
        or source_generation.get("source_quality_gate")
        or run_result.get("source_quality_gate")
    )
    source_evidence_artifact = (
        generation.get("source_evidence_artifact")
        or source_generation.get("source_evidence_artifact")
        or run_result.get("source_evidence_artifact")
    )
    source_snapshot = (
        generation.get("source_snapshot")
        or source_generation.get("source_snapshot")
        or run_result.get("source_snapshot")
    )
    source_specific_type = ""
    if isinstance(project_source, dict):
        source_specific_type = {
            "amazon_url": "amazon_source",
            "shopify_url": "shopify_source",
            "csv_reviews": "csv_reviews_source",
        }.get(str(project_source.get("source_type") or ""), "")
    artifact_sources: list[tuple[str, Any, str, list[str], str, list[str]]] = [
        (
            "project_workspace",
            safe_project or {"project_id": project_id, "project_version": "project_workspace_v1"},
            "planner_agent",
            [],
            "used",
            ["evidence_agent", "asset_lock_agent"],
        ),
        (
            "project_source",
            project_source,
            "source_adapter_agent",
            ["project_workspace"],
            "used",
            ["source_quality_agent"],
        ),
        (
            source_specific_type,
            project_source if source_specific_type else {},
            "source_adapter_agent",
            ["project_source"],
            "created",
            ["source_quality_agent"],
        ),
        (
            "source_quality_gate",
            source_quality_gate,
            "source_quality_agent",
            ["project_source"],
            "used",
            ["evidence_agent"],
        ),
        (
            "source_evidence_artifact",
            source_evidence_artifact,
            "evidence_agent",
            ["source_quality_gate"],
            "used",
            ["strategy_agent", "storyboard_agent"],
        ),
        (
            "source_snapshot",
            source_snapshot,
            "source_adapter_agent",
            ["source_evidence_artifact"],
            "created",
            [],
        ),
        (
            "llm_evidence_packet",
            generation.get("llm_evidence_packet") or source_generation.get("llm_evidence_packet"),
            "evidence_agent",
            ["source_evidence_artifact", "project_workspace"],
            "used",
            ["strategy_agent"],
        ),
        (
            "video_generation_packet",
            generation.get("video_generation_packet")
            or safe_job.get("video_generation_packet")
            or run_result.get("video_generation_packet"),
            "prompt_handoff_agent",
            ["llm_evidence_packet"],
            "used" if safe_job else "created",
            ["provider_job_agent"],
        ),
        (
            "external_video_tool_handoff",
            generation.get("external_video_tool_handoff")
            or safe_job.get("external_video_tool_handoff")
            or run_result.get("external_video_tool_handoff"),
            "prompt_handoff_agent",
            ["video_generation_packet"],
            "used" if experiments else "created",
            ["provider_job_agent", "experiment_agent"],
        ),
        (
            "product_asset_lock",
            generation.get("product_asset_lock")
            or run_result.get("product_asset_lock")
            or _experiment_rework_dict(source_generation.get("agent_trace")).get("product_asset_lock"),
            "asset_lock_agent",
            ["external_video_tool_handoff"],
            "used",
            ["product_identity_validator", "keyframe_agent"],
        ),
        (
            "product_asset_lock_v2",
            product_asset_lock_v2,
            "asset_lock_agent",
            ["uploaded_product_asset", "product_asset_lock"],
            "used",
            ["product_identity_validator", "keyframe_agent", "prompt_handoff_agent"],
        ),
        (
            "keyframe_plan",
            generation.get("keyframe_plan")
            or run_result.get("keyframe_plan")
            or _experiment_rework_dict(source_generation.get("agent_trace")).get("keyframe_plan"),
            "keyframe_agent",
            ["product_asset_lock_v2", "product_asset_lock"],
            "used",
            ["prompt_handoff_agent"],
        ),
        (
            "revised_keyframe_plan",
            latest_experiment.get("revised_keyframe_plan")
            or run_result.get("revised_keyframe_plan")
            or graph_feedback.get("latest_revised_keyframe_plan"),
            "keyframe_agent",
            ["keyframe_plan"],
            "revised",
            ["prompt_handoff_agent"],
        ),
        (
            "revised_external_video_handoff",
            latest_experiment.get("revised_external_video_handoff")
            or run_result.get("revised_external_video_handoff")
            or graph_feedback.get("latest_revised_external_video_handoff"),
            "prompt_handoff_agent",
            ["revised_keyframe_plan"],
            "revised",
            ["experiment_agent"],
        ),
        (
            "experiment_feedback_decision",
            latest_experiment.get("agent_feedback_decision")
            or safe_job.get("latest_agent_feedback_decision"),
            "experiment_agent",
            [],
            "created",
            ["graph_router_agent"],
        ),
        (
            "second_experiment_comparison",
            latest_experiment.get("second_experiment_comparison")
            or graph_feedback.get("latest_second_experiment_comparison"),
            "experiment_agent",
            ["experiment_feedback_decision", "revised_external_video_handoff"],
            "created",
            ["graph_router_agent"],
        ),
        (
            "experiment_comparison_decision_gate",
            latest_experiment.get("experiment_comparison_decision_gate")
            or graph_feedback.get("latest_experiment_comparison_decision_gate"),
            "experiment_agent",
            ["second_experiment_comparison"],
            "created",
            ["graph_router_agent", "human_approval_agent"],
        ),
        (
            "demo_ready_run_summary",
            latest_experiment.get("demo_ready_run_summary")
            or safe_job.get("latest_demo_ready_run_summary"),
            "finalizer_agent",
            ["experiment_comparison_decision_gate"],
            "created",
            [],
        ),
        (
            "artifact_lineage",
            latest_experiment.get("artifact_lineage")
            or safe_job.get("latest_artifact_lineage"),
            "finalizer_agent",
            [],
            "created",
            [],
        ),
        (
            "controlled_provider_handoff_checklist",
            latest_experiment.get("controlled_provider_handoff_checklist")
            or safe_job.get("latest_controlled_provider_handoff_checklist"),
            "provider_job_agent",
            ["experiment_comparison_decision_gate"],
            "used",
            ["human_approval_agent"],
        ),
        (
            "human_approval_gate",
            latest_experiment.get("human_approval_gate")
            or safe_job.get("latest_human_approval_gate"),
            "human_approval_agent",
            ["controlled_provider_handoff_checklist"],
            "used",
            ["provider_job_agent"],
        ),
        (
            "graph_router_decision",
            latest_experiment.get("latest_graph_router_decision")
            or safe_job.get("latest_graph_router_decision")
            or safe_run.get("latest_graph_router_decision"),
            "graph_router_agent",
            [],
            "used",
            [],
        ),
        (
            "provider_result",
            safe_job.get("result")
            if _experiment_rework_dict(safe_job.get("result")).get("result_url")
            else {},
            "provider_job_agent",
            ["human_approval_gate", "video_generation_packet"],
            "created",
            ["experiment_agent"],
        ),
    ]
    artifacts: list[dict[str, Any]] = []
    artifact_ids_by_type: dict[str, str] = {}
    for uploaded_asset in uploaded_assets or []:
        if not isinstance(uploaded_asset, dict) or not uploaded_asset.get("asset_id"):
            continue
        artifact_type = (
            "uploaded_product_asset"
            if uploaded_asset.get("asset_role") == "product_image"
            else "uploaded_reference_asset"
        )
        artifact_id = _stable_graph_id(
            "artifact",
            artifact_type,
            project_id,
            uploaded_asset.get("asset_id"),
        )
        artifact_ids_by_type.setdefault(artifact_type, artifact_id)
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "project_id": project_id,
                "artifact_type": artifact_type,
                "source_agent_id": "user_upload",
                "parent_artifact_ids": [],
                "child_artifact_ids": [],
                "status": "created",
                "version": 1,
                "supersedes_artifact_id": None,
                "superseded_by_artifact_id": None,
                "quality_score": None,
                "summary": str(uploaded_asset.get("filename") or "Uploaded product asset"),
                "used_by_agent_ids": ["asset_lock_agent"],
                "created_by_run_id": "",
                "created_from_job_id": str(safe_job.get("job_id") or ""),
                "created_from_experiment_id": "",
            }
        )
    for artifact_type, value, source_agent_id, parent_types, status, used_by in artifact_sources:
        if not isinstance(value, dict) or not value:
            continue
        artifact_id = _stable_graph_id(
            "artifact",
            artifact_type,
            safe_run.get("run_id"),
            safe_job.get("job_id"),
            value,
        )
        artifact_ids_by_type[artifact_type] = artifact_id
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "project_id": project_id,
                "artifact_type": artifact_type,
                "source_agent_id": source_agent_id,
                "parent_artifact_ids": list(parent_types),
                "child_artifact_ids": [],
                "status": status,
                "version": 2 if artifact_type in {"product_asset_lock_v2"} else 1,
                "supersedes_artifact_id": None,
                "superseded_by_artifact_id": None,
                "quality_score": (
                    latest_experiment.get("overall_score")
                    if artifact_type in {
                        "second_experiment_comparison",
                        "experiment_comparison_decision_gate",
                    }
                    else None
                ),
                "summary": _artifact_summary(
                    value,
                    f"{artifact_type.replace('_', ' ').title()} available.",
                ),
                "used_by_agent_ids": list(used_by),
                "created_by_run_id": str(safe_run.get("run_id") or rework_run_id or ""),
                "created_from_job_id": str(safe_job.get("job_id") or ""),
                "created_from_experiment_id": str(latest_experiment.get("experiment_id") or ""),
                "artifact_metadata": (
                    {
                        "source_type": value.get("source_type", ""),
                        "source_url": value.get("normalized_url")
                        or value.get("source_url", ""),
                        "source_confidence": value.get("source_confidence", ""),
                        "warnings": value.get("warnings") or [],
                        "manual_fallback_needed": value.get(
                            "manual_fallback_needed",
                            (value.get("source_summary") or {}).get(
                                "manual_fallback_needed",
                                False,
                            ),
                        ),
                        "asin": value.get("asin", ""),
                        "shopify_handle": value.get("shopify_handle", ""),
                        "review_classifications": value.get(
                            "review_classifications",
                            [],
                        ),
                    }
                    if artifact_type
                    in {
                        "project_source",
                        "amazon_source",
                        "shopify_source",
                        "csv_reviews_source",
                        "source_quality_gate",
                        "source_evidence_artifact",
                        "source_snapshot",
                    }
                    else {}
                ),
            }
        )
    for artifact in artifacts:
        artifact["parent_artifact_ids"] = [
            artifact_ids_by_type[parent_type]
            for parent_type in artifact["parent_artifact_ids"]
            if parent_type in artifact_ids_by_type
        ]
    artifacts_by_id = {item["artifact_id"]: item for item in artifacts}
    for artifact in artifacts:
        for parent_id in artifact["parent_artifact_ids"]:
            parent = artifacts_by_id.get(parent_id)
            if parent and artifact["artifact_id"] not in parent["child_artifact_ids"]:
                parent["child_artifact_ids"].append(artifact["artifact_id"])
    for artifact in artifacts:
        if artifact["artifact_type"] == "revised_keyframe_plan":
            parent_id = next(iter(artifact["parent_artifact_ids"]), None)
            artifact["supersedes_artifact_id"] = parent_id
            if parent_id in artifacts_by_id:
                artifacts_by_id[parent_id]["status"] = "superseded"
                artifacts_by_id[parent_id]["superseded_by_artifact_id"] = artifact["artifact_id"]
        if artifact["artifact_type"] == "human_approval_gate":
            approval_value = _experiment_rework_dict(
                latest_experiment.get("human_approval_gate")
                or safe_job.get("latest_human_approval_gate")
            )
            if approval_value.get("status") == "approved":
                artifact["status"] = "approved"
            elif approval_value.get("status") in {"rejected", "cancelled"}:
                artifact["status"] = "blocked"
    counts = {
        "total": len(artifacts),
        "created": sum(item["status"] == "created" for item in artifacts),
        "used": sum(item["status"] == "used" for item in artifacts),
        "revised": sum(item["status"] == "revised" for item in artifacts),
        "approved": sum(item["status"] == "approved" for item in artifacts),
        "blocked": sum(item["status"] == "blocked" for item in artifacts),
    }
    artifact_types = {item["artifact_type"] for item in artifacts}
    router_artifacts = bool(
        artifact_types.intersection(
            {"graph_router_decision", "experiment_comparison_decision_gate"}
        )
    )
    lineage_summary = {
        "has_parent_child_links": any(item["parent_artifact_ids"] for item in artifacts),
        "has_revisions": bool(
            artifact_types.intersection(
                {"revised_keyframe_plan", "revised_external_video_handoff"}
            )
        ),
        "has_uploaded_assets": bool(
            artifact_types.intersection({"uploaded_product_asset", "uploaded_reference_asset"})
        ),
        "has_approval_artifact": "human_approval_gate" in artifact_types,
        "has_provider_result": "provider_result" in artifact_types,
        "has_source_artifacts": bool(
            artifact_types.intersection(
                {
                    "project_source",
                    "source_quality_gate",
                    "source_evidence_artifact",
                    "source_snapshot",
                }
            )
        ),
        "has_source_quality_gate": "source_quality_gate" in artifact_types,
        "has_review_classifications": bool(
            isinstance(source_evidence_artifact, dict)
            and source_evidence_artifact.get("review_classifications")
        ),
        "has_manual_fallback": bool(
            isinstance(project_source, dict)
            and (project_source.get("source_summary") or {}).get(
                "manual_fallback_needed"
            )
        ),
        "is_linear_workflow": False,
    }
    return {
        "registry_version": "artifact_registry_v2",
        "compatible_with": ["artifact_registry_v1"],
        "registry_type": "project_scoped_graph_artifacts",
        "registry_id": _stable_graph_id(
            "artifact_registry",
            project_id,
            safe_run.get("run_id"),
            safe_job.get("job_id"),
            [item["artifact_id"] for item in artifacts],
        ),
        "project_id": project_id,
        "root_run_id": str(safe_run.get("run_id") or rework_run_id or ""),
        "root_job_id": str(safe_job.get("job_id") or ""),
        "artifacts": artifacts,
        "artifact_counts": counts,
        "lineage_summary": lineage_summary,
        "graph_evidence": {
            "has_artifact_chain": len(artifacts) > 1,
            "has_revised_artifacts": bool(
                artifact_types.intersection(
                    {"revised_keyframe_plan", "revised_external_video_handoff"}
                )
            ),
            "has_router_artifacts": router_artifacts,
            "has_approval_artifact": "human_approval_gate" in artifact_types,
            "is_linear_workflow": False,
        },
    }


def _snapshot_router_edges(run: dict[str, Any], job: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = list(run.get("graph_router_decisions") or job.get("graph_router_decisions") or [])
    latest = _experiment_rework_dict(
        job.get("latest_graph_router_decision")
        or run.get("latest_graph_router_decision")
        or (decisions[-1] if decisions else {})
    )
    selected_edges: list[dict[str, Any]] = []
    for index, decision in enumerate(decisions or ([latest] if latest else [])):
        if not isinstance(decision, dict):
            continue
        edge = _experiment_rework_dict(decision.get("selected_edge"))
        from_node = str(edge.get("from_node_id") or decision.get("source_node_id") or "")
        to_node = str(
            edge.get("to_node_id")
            or decision.get("selected_next_agent_id")
            or ""
        )
        if not from_node or not to_node:
            continue
        selected_edges.append(
            {
                "from_node_id": from_node,
                "to_node_id": to_node,
                "edge_type": str(edge.get("edge_type") or decision.get("route_type") or "router"),
                "status": "selected" if decision == latest else "traversed",
                "selected_by_agent_id": "graph_router_agent",
                "reason": str(decision.get("reason") or ""),
                "route_type": str(decision.get("route_type") or ""),
                "is_primary_route": True,
                "is_secondary_route": False,
            }
        )
        secondary = str(decision.get("secondary_next_agent_id") or "")
        if secondary:
            selected_edges.append(
                {
                    "from_node_id": "graph_router_agent",
                    "to_node_id": secondary,
                    "edge_type": str(decision.get("route_type") or "router"),
                    "status": "selected" if decision == latest else "traversed",
                    "selected_by_agent_id": "graph_router_agent",
                    "reason": str(decision.get("reason") or ""),
                    "route_type": str(decision.get("route_type") or ""),
                    "is_primary_route": False,
                    "is_secondary_route": True,
                }
            )
    return selected_edges[-12:]


def build_graph_state_snapshot(
    run: dict[str, Any] | None = None,
    job: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
    artifact_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact deterministic run/job graph snapshot for history and reports."""

    safe_run = _experiment_rework_dict(run)
    safe_job = _experiment_rework_dict(job)
    safe_events = list(events or safe_run.get("events") or [])
    registry = _experiment_rework_dict(artifact_registry)
    node_statuses = {
        str(node.get("node_id") or ""): str(node.get("status") or "pending")
        for node in safe_run.get("graph_nodes") or []
        if isinstance(node, dict) and node.get("node_id")
    }
    approval = _experiment_rework_dict(
        safe_job.get("latest_human_approval_gate")
        or safe_run.get("latest_human_approval_gate")
    )
    provider = _experiment_rework_dict(safe_job.get("provider_runtime"))
    if approval:
        approval_status = str(approval.get("status") or "pending_approval")
        node_statuses["human_approval_agent"] = approval_status
        if approval.get("blocks_provider_submit") is True:
            node_statuses["provider_job_agent"] = "blocked"
    if provider:
        provider_status = str(provider.get("provider_status") or safe_job.get("status") or "")
        if provider_status in {"queued", "processing"}:
            node_statuses["provider_job_agent"] = "running"
        elif provider_status in {"external_result_ready", "manual_export_completed"}:
            node_statuses["provider_job_agent"] = "complete"
    active_loops: list[str] = []
    if safe_run.get("rework_loops"):
        active_loops.append("risk_rework_loop")
    if safe_job.get("latest_agent_feedback_decision") or safe_job.get("latest_rework_run_id"):
        active_loops.append("experiment_feedback_loop")
    active_gates = ["human_approval_gate"] if approval else []
    blocked_by = ""
    if approval.get("blocks_provider_submit") is True:
        blocked_by = "human_approval_gate"
    waiting_for_user = bool(safe_run.get("waiting_for_user")) or bool(
        approval.get("status") == "pending_approval"
    )
    if blocked_by:
        next_action = "Review the controlled checklist and approve or request changes before provider submit."
    elif safe_job.get("latest_rework_run_id") and not safe_job.get("latest_second_experiment_comparison"):
        next_action = "Use the revised handoff in a second external experiment."
    elif safe_run.get("status") == "completed" and not safe_job:
        next_action = "Review handoff and create a video job."
    else:
        next_action = "Review the latest graph artifact and selected route."
    snapshot = {
        "snapshot_version": "graph_state_snapshot_v1",
        "snapshot_type": "run_job_graph_state",
        "snapshot_id": _stable_graph_id(
            "graph_snapshot",
            safe_run.get("run_id"),
            safe_job.get("job_id"),
            node_statuses,
            _snapshot_router_edges(safe_run, safe_job),
            len(safe_events),
        ),
        "run_id": str(safe_run.get("run_id") or ""),
        "job_id": str(safe_job.get("job_id") or ""),
        "project_id": str(
            safe_job.get("project_id")
            or safe_run.get("project_id")
            or registry.get("project_id")
            or "demo_project_default"
        ),
        "node_statuses": node_statuses,
        "selected_edges": _snapshot_router_edges(safe_run, safe_job),
        "active_loops": active_loops,
        "active_gates": active_gates,
        "artifact_counts": deepcopy(registry.get("artifact_counts") or {}),
        "message_count": len(safe_run.get("agent_messages") or safe_job.get("agent_messages") or []),
        "event_count": len(safe_events),
        "waiting_for_user": waiting_for_user,
        "blocked_by": blocked_by,
        "next_graph_action": next_action,
        "safety_boundaries": _graph_safety_boundaries(),
        "is_linear_workflow": False,
        "created_at": utc_now_iso(),
    }
    return snapshot


def build_graph_health_summary(
    run: dict[str, Any] | None,
    job: dict[str, Any] | None,
    artifact_registry: dict[str, Any] | None,
    graph_state: dict[str, Any] | None,
) -> dict[str, Any]:
    safe_run = _experiment_rework_dict(run)
    safe_job = _experiment_rework_dict(job)
    registry = _experiment_rework_dict(artifact_registry)
    state = _experiment_rework_dict(graph_state)
    checks = {
        "has_events": bool(safe_run.get("events") or safe_job.get("history")),
        "has_router_decision": bool(state.get("selected_edges")),
        "has_rework_loop": bool(state.get("active_loops")),
        "has_human_gate": bool(state.get("active_gates")),
        "has_artifacts": bool(registry.get("artifacts")),
        "has_persistence_snapshot": bool(state.get("snapshot_version")),
        "has_safety_boundary": state.get("safety_boundaries") == _graph_safety_boundaries(),
    }
    missing = [
        key.replace("has_", "")
        for key, value in checks.items()
        if not value and key not in {"has_rework_loop", "has_human_gate"}
    ]
    return {
        "health_version": "graph_health_v1",
        "is_linear_workflow": False,
        **checks,
        "missing_recommended_capabilities": missing,
    }


def build_lightweight_artifact_lineage(
    job: dict[str, Any] | None,
    baseline_experiment: dict[str, Any] | None = None,
    second_experiment: dict[str, Any] | None = None,
    rework_run: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
    decision_gate: dict[str, Any] | None = None,
    human_approval_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize the experiment feedback artifact chain without changing runtime behavior."""

    safe_job = _experiment_rework_dict(job)
    baseline = _experiment_rework_dict(baseline_experiment)
    second = _experiment_rework_dict(second_experiment)
    run = _experiment_rework_dict(rework_run)
    safe_comparison = _experiment_rework_dict(comparison)
    gate = _experiment_rework_dict(decision_gate)
    approval_gate = _experiment_rework_dict(human_approval_gate)
    feedback = _experiment_rework_dict(baseline.get("agent_feedback_decision"))
    run_result = _experiment_rework_dict(run.get("result"))
    revised_plan = _experiment_rework_dict(run_result.get("revised_keyframe_plan"))
    revised_handoff = _experiment_rework_dict(run_result.get("revised_external_video_handoff"))
    router_decisions = list(second.get("graph_router_decisions") or safe_job.get("graph_router_decisions") or [])
    latest_router_decision = _experiment_rework_dict(
        second.get("latest_graph_router_decision")
        or safe_job.get("latest_graph_router_decision")
        or (router_decisions[-1] if router_decisions else {})
    )

    artifact_chain: list[dict[str, Any]] = []

    def append_artifact(
        artifact_type: str,
        artifact_id: str,
        source_agent_id: str,
        status: str,
        summary: str,
        **details: Any,
    ) -> None:
        clean_details = {
            key: value for key, value in details.items() if value not in (None, "", [], {})
        }
        if not artifact_id and not clean_details:
            return
        artifact = {
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
            "source_agent_id": source_agent_id,
            "status": status,
            "summary": summary,
        }
        artifact.update(clean_details)
        artifact_chain.append(artifact)

    append_artifact(
        "baseline_external_experiment",
        str(baseline.get("experiment_id") or ""),
        "experiment_agent",
        "failed_or_low_score" if feedback.get("has_feedback") else "recorded",
        str(feedback.get("reason") or "Baseline external experiment recorded for comparison."),
        overall_score=baseline.get("overall_score"),
    )
    append_artifact(
        "feedback_decision",
        str(feedback.get("feedback_version") or ""),
        str(feedback.get("source_agent_id") or "experiment_agent"),
        "rework_requested" if feedback.get("has_feedback") else "recorded",
        str(feedback.get("recommended_action") or feedback.get("reason") or "Experiment feedback recorded."),
        target_agent_id=feedback.get("target_agent_id"),
        issue_type=feedback.get("issue_type"),
    )
    append_artifact(
        "revised_keyframe_plan",
        str(revised_plan.get("plan_version") or ""),
        str(revised_plan.get("target_agent_id") or "keyframe_agent"),
        "created",
        "Keyframe Agent created a revised product-consistent keyframe plan.",
        upstream_source_agent_id=revised_plan.get("source_agent_id"),
    )
    append_artifact(
        "revised_external_video_handoff",
        str(revised_handoff.get("handoff_version") or ""),
        str(revised_handoff.get("target_agent_id") or "prompt_handoff_agent"),
        "created",
        "Prompt Handoff Agent created revised external video prompts.",
        upstream_source_agent_id=revised_handoff.get("source_agent_id"),
    )
    append_artifact(
        "second_external_experiment",
        str(second.get("experiment_id") or ""),
        "experiment_agent",
        str(safe_comparison.get("status") or "recorded"),
        str(safe_comparison.get("reason") or "Second external experiment compared with the baseline."),
        overall_score=second.get("overall_score"),
    )
    append_artifact(
        "experiment_comparison_decision_gate",
        str(gate.get("gate_version") or ""),
        str(gate.get("source_agent_id") or "experiment_agent"),
        str(gate.get("decision_type") or "created"),
        str(gate.get("recommended_next_action") or gate.get("reason") or "Decision gate created."),
        target_agent_id=gate.get("next_agent_id"),
        decision_type=gate.get("decision_type"),
        recommended_route=gate.get("recommended_route"),
    )
    append_artifact(
        "graph_router_decision",
        str(latest_router_decision.get("router_version") or ""),
        "graph_router_agent",
        "route_selected",
        "Graph Router Agent selected the next graph route based on comparison and gate evidence.",
        decision_type=latest_router_decision.get("decision_type"),
        selected_next_agent_id=latest_router_decision.get("selected_next_agent_id"),
        route_type=latest_router_decision.get("route_type"),
    )
    append_artifact(
        "human_approval_gate",
        str(approval_gate.get("approval_gate_version") or ""),
        str(approval_gate.get("source_agent_id") or "human_approval_agent"),
        str(approval_gate.get("status") or "pending_approval"),
        str(approval_gate.get("approval_prompt") or "Human approval is required before provider handoff."),
        approval_scope=approval_gate.get("approval_scope"),
        blocks_provider_submit=approval_gate.get("blocks_provider_submit"),
        blocks_external_api_call=approval_gate.get("blocks_external_api_call"),
    )

    agents: list[str] = []
    for candidate in [
        "experiment_agent",
        feedback.get("target_agent_id"),
        feedback.get("secondary_target_agent_id"),
        revised_plan.get("target_agent_id"),
        revised_plan.get("secondary_target_agent_id"),
        revised_handoff.get("target_agent_id"),
        gate.get("next_agent_id"),
        gate.get("secondary_next_agent_id"),
        "graph_router_agent" if latest_router_decision else "",
        approval_gate.get("source_agent_id"),
        approval_gate.get("recommended_route_after_approval"),
    ]:
        agent_id = str(candidate or "").strip()
        if agent_id and agent_id not in agents:
            agents.append(agent_id)

    return {
        "lineage_version": "agent_artifact_lineage_v1",
        "lineage_type": "experiment_feedback_demo_lineage",
        "root_job_id": str(safe_job.get("job_id") or ""),
        "baseline_experiment_id": str(
            safe_comparison.get("baseline_experiment_id") or baseline.get("experiment_id") or ""
        ),
        "linked_rework_run_id": str(
            safe_comparison.get("linked_rework_run_id") or run.get("run_id") or ""
        ),
        "second_experiment_id": str(
            safe_comparison.get("second_experiment_id") or second.get("experiment_id") or ""
        ),
        "agents_involved": agents,
        "artifact_chain": artifact_chain,
        "graph_evidence": {
            "has_feedback_loop": bool(feedback.get("has_feedback")),
            "has_rework_run": bool(run.get("run_id")),
            "has_revised_artifacts": bool(revised_plan or revised_handoff),
            "has_second_experiment_comparison": bool(safe_comparison),
            "has_decision_gate": bool(gate),
            "has_graph_router_decision": bool(latest_router_decision),
            "has_centralized_route_decision": bool(latest_router_decision),
            "has_human_approval_gate": bool(approval_gate),
            "is_linear_workflow": False,
        },
    }


def build_controlled_provider_handoff_checklist(
    job: dict[str, Any] | None,
    decision_gate: dict[str, Any] | None,
    rework_run: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a human-approved provider/manual handoff checklist without submitting a job."""

    safe_job = _experiment_rework_dict(job)
    gate = _experiment_rework_dict(decision_gate)
    run = _experiment_rework_dict(rework_run)
    safe_comparison = _experiment_rework_dict(comparison)
    checks = [
        ("review_revised_handoff", "Review the revised prompt handoff against the winning experiment."),
        ("confirm_product_identity", "Confirm product identity and visual references are locked."),
        ("confirm_cost_boundary", "Review provider pricing and set a one-clip cost ceiling."),
        ("run_one_short_clip", "Run one short controlled clip in manual or simulated mode."),
        ("record_result_as_external_experiment", "Record the result as another external experiment."),
    ]
    return {
        "checklist_version": "controlled_provider_handoff_checklist_v1",
        "source_agent_id": "provider_job_agent",
        "triggered_by_gate": str(gate.get("gate_version") or "experiment_comparison_decision_gate_v1"),
        "job_id": str(safe_job.get("job_id") or ""),
        "rework_run_id": str(run.get("run_id") or safe_comparison.get("linked_rework_run_id") or ""),
        "recommended_route": str(gate.get("recommended_route") or ""),
        "provider_mode": "manual_or_simulated",
        "external_api_call_allowed": False,
        "cost_incurred_by_crossgrowth": False,
        "human_approval_required": True,
        "preflight_checks": [
            {"check_id": check_id, "label": label, "required": True, "status": "pending"}
            for check_id, label in checks
        ],
        "recommended_next_action": (
            "Run one controlled manual/provider test using the revised handoff, "
            "then record the result as another external experiment."
        ),
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "requires_human_approval_before_paid_generation": True,
            "automatic_provider_submission_enabled": False,
        },
    }


def build_human_approval_gate(
    job: dict[str, Any] | None,
    decision_gate: dict[str, Any] | None = None,
    checklist: dict[str, Any] | None = None,
    router_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a pending human-owned gate without approving or submitting anything."""

    safe_job = _experiment_rework_dict(job)
    gate = _experiment_rework_dict(decision_gate)
    safe_checklist = _experiment_rework_dict(checklist)
    router = _experiment_rework_dict(router_decision)
    preflight_checks = safe_checklist.get("preflight_checks")
    approval_checklist = deepcopy(preflight_checks) if isinstance(preflight_checks, list) else []
    return {
        "approval_gate_version": "human_approval_gate_v1",
        "source_agent_id": "human_approval_agent",
        "triggered_by_agent_id": str(router.get("source_agent_id") or "graph_router_agent"),
        "triggered_by_decision_type": str(
            router.get("decision_type") or "route_to_human_approval_before_provider"
        ),
        "job_id": str(safe_job.get("job_id") or ""),
        "approval_scope": "controlled_provider_or_manual_handoff",
        "status": "pending_approval",
        "allowed_transitions": ["approved", "rejected", "changes_requested", "cancelled"],
        "requires_human_approval": True,
        "blocks_provider_submit": True,
        "blocks_external_api_call": True,
        "provider_mode": "manual_or_simulated",
        "recommended_route_after_approval": "provider_job_agent",
        "approval_prompt": (
            "Review the revised handoff, product identity, cost boundary, and one-short-clip "
            "plan before provider/manual test."
        ),
        "approval_checklist": approval_checklist,
        "decision_history": [],
        "created_at": utc_now_iso(),
        "decision_gate_version": str(gate.get("gate_version") or ""),
        "checklist_version": str(safe_checklist.get("checklist_version") or ""),
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "requires_human_approval_before_paid_generation": True,
        },
    }


def apply_human_approval_decision(
    approval_gate: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    """Apply one terminal human decision while preserving provider safety boundaries."""

    gate = deepcopy(_experiment_rework_dict(approval_gate))
    if not gate:
        raise ValueError("human approval gate is required")
    current_status = str(gate.get("status") or "pending_approval").strip().lower()
    if current_status != "pending_approval":
        raise ValueError(f"human approval gate is already terminal: {current_status}")

    payload = _experiment_rework_dict(decision)
    next_status = str(payload.get("decision") or "").strip().lower()
    allowed = list(gate.get("allowed_transitions") or [])
    if next_status not in allowed:
        raise ValueError(
            "unsupported human approval decision; use approved, rejected, changes_requested, or cancelled"
        )

    timestamp = utc_now_iso()
    approval_scope = str(
        payload.get("approved_scope")
        or gate.get("approval_scope")
        or "controlled_provider_or_manual_handoff"
    )
    history_entry = {
        "decision": next_status,
        "reviewer": str(payload.get("reviewer") or "manual_user"),
        "notes": str(payload.get("notes") or ""),
        "approved_scope": approval_scope,
        "timestamp": timestamp,
    }
    gate["status"] = next_status
    gate["blocks_provider_submit"] = next_status != "approved"
    gate["blocks_external_api_call"] = True
    gate["requires_human_approval"] = True
    gate["updated_at"] = timestamp
    gate["decided_at"] = timestamp
    gate["approved_scope"] = approval_scope if next_status == "approved" else ""
    decision_history = list(gate.get("decision_history") or [])
    decision_history.append(history_entry)
    gate["decision_history"] = decision_history
    if next_status == "changes_requested":
        gate["recommended_next_agent_id"] = str(
            payload.get("recommended_next_agent_id") or "prompt_handoff_agent"
        )
    elif next_status == "approved":
        gate["recommended_next_agent_id"] = "provider_job_agent"

    safety = dict(gate.get("safety_boundaries") or {})
    safety.update(
        {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "requires_human_approval_before_paid_generation": True,
        }
    )
    gate["safety_boundaries"] = safety
    return gate


def build_demo_ready_run_summary(
    job: dict[str, Any] | None,
    baseline_experiment: dict[str, Any] | None,
    second_experiment: dict[str, Any] | None,
    rework_run: dict[str, Any] | None,
    comparison: dict[str, Any] | None,
    decision_gate: dict[str, Any] | None,
    artifact_lineage: dict[str, Any] | None = None,
    handoff_checklist: dict[str, Any] | None = None,
    human_approval_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact demo narrative for the completed feedback and decision loop."""

    baseline = _experiment_rework_dict(baseline_experiment)
    second = _experiment_rework_dict(second_experiment)
    run = _experiment_rework_dict(rework_run)
    safe_comparison = _experiment_rework_dict(comparison)
    gate = _experiment_rework_dict(decision_gate)
    approval_gate = _experiment_rework_dict(human_approval_gate)
    lineage = _experiment_rework_dict(artifact_lineage) or build_lightweight_artifact_lineage(
        job,
        baseline,
        second,
        run,
        safe_comparison,
        gate,
        approval_gate,
    )
    checklist = _experiment_rework_dict(handoff_checklist)
    if not checklist and gate.get("should_proceed_to_provider_test") is True:
        checklist = build_controlled_provider_handoff_checklist(job, gate, run, safe_comparison)
    primary_metric = str(safe_comparison.get("primary_metric") or "product_consistency_score")
    baseline_score = _numeric_experiment_score(baseline.get(primary_metric))
    second_score = _numeric_experiment_score(second.get(primary_metric))
    score_deltas = _experiment_rework_dict(safe_comparison.get("score_deltas"))

    created_artifacts = [
        artifact_type
        for artifact_type in [
            "revised_keyframe_plan" if run else "",
            "revised_external_video_handoff" if run else "",
            "second_experiment_comparison" if safe_comparison else "",
            "experiment_comparison_decision_gate" if gate else "",
        ]
        if artifact_type
    ]
    if checklist:
        created_artifacts.append("controlled_provider_handoff_checklist")
    if approval_gate:
        created_artifacts.append("human_approval_gate")

    feedback = _experiment_rework_dict(baseline.get("agent_feedback_decision"))
    router_summary = _experiment_rework_dict(
        second.get("graph_router_summary")
        or _experiment_rework_dict(job).get("graph_router_summary")
    )
    if router_summary.get("decision_count"):
        created_artifacts.append("graph_router_decision")
    decision_chain = [
        {
            "agent_id": "experiment_agent",
            "decision": str(feedback.get("decision_type") or "feedback_recorded"),
        },
        {
            "agent_id": str(feedback.get("target_agent_id") or "keyframe_agent"),
            "decision": "revised_keyframe_plan_created" if run else "rework_not_available",
        },
        {
            "agent_id": "prompt_handoff_agent",
            "decision": "revised_external_video_handoff_created" if run else "handoff_not_available",
        },
        {
            "agent_id": "experiment_agent",
            "decision": str(safe_comparison.get("decision_type") or "second_experiment_compared"),
        },
        {
            "agent_id": str(gate.get("next_agent_id") or "provider_job_agent"),
            "decision": str(gate.get("decision_type") or "human_review_required"),
        },
    ]
    if approval_gate:
        decision_chain.append(
            {
                "agent_id": "human_approval_agent",
                "decision": str(approval_gate.get("status") or "pending_approval"),
            }
        )

    return {
        "summary_version": "multi_agent_demo_run_summary_v1",
        "summary_type": "experiment_feedback_closed_loop_demo",
        "headline": "Experiment feedback improved the revised video handoff and opened a human-approved controlled test gate.",
        "why_this_is_multi_agent_graph": [
            "Experiment Agent scored the baseline result and routed feedback upstream.",
            "Keyframe and Prompt Handoff agents produced revised artifacts.",
            "Experiment Agent compared a second external result against the baseline.",
            "A deterministic decision gate selected the next business-safe route.",
            "Graph Router Agent centralized route decisions across feedback, rework, comparison, and decision gate.",
            "This is not a linear workflow: feedback creates an upstream rework loop before the next gate.",
        ],
        "agent_decision_chain": decision_chain,
        "score_improvement_summary": {
            "primary_metric": primary_metric,
            "baseline_score": baseline_score,
            "second_score": second_score,
            "delta": _numeric_experiment_score(score_deltas.get(primary_metric)),
            "overall_delta": _numeric_experiment_score(score_deltas.get("overall_score")),
            "status": str(safe_comparison.get("status") or ""),
        },
        "created_artifacts": created_artifacts,
        "next_action": (
            "Human approval is required before the controlled provider/manual test."
            if approval_gate
            else str(gate.get("recommended_next_action") or "")
        ),
        "human_review_required": True,
        "safety_summary": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "automatic_provider_submission_enabled": False,
        },
        "is_linear_workflow": False,
        "graph_router_summary": router_summary,
        "lineage": lineage,
        "controlled_provider_handoff_checklist": checklist,
        "human_approval_gate": approval_gate,
    }


def _experiment_rework_scene_source(original_generation_data: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    handoff = _experiment_rework_dict(original_generation_data.get("external_video_tool_handoff"))
    keyframe_plan = _experiment_rework_dict(handoff.get("keyframe_plan"))
    keyframe_scenes = keyframe_plan.get("scenes")
    if isinstance(keyframe_scenes, list) and keyframe_scenes:
        return [scene for scene in keyframe_scenes if isinstance(scene, dict)], "external_video_tool_handoff.keyframe_plan"

    keyframe_prompts = handoff.get("keyframe_prompts")
    if isinstance(keyframe_prompts, list) and keyframe_prompts:
        return [scene for scene in keyframe_prompts if isinstance(scene, dict)], "external_video_tool_handoff.keyframe_prompts"

    video_packet = _experiment_rework_dict(original_generation_data.get("video_generation_packet"))
    video_scenes = video_packet.get("scenes")
    if isinstance(video_scenes, list) and video_scenes:
        return [scene for scene in video_scenes if isinstance(scene, dict)], "video_generation_packet.scenes"

    assets = _experiment_rework_dict(original_generation_data.get("assets"))
    storyboard = _experiment_rework_dict(assets.get("storyboard"))
    storyboard_scenes = storyboard.get("scenes")
    if isinstance(storyboard_scenes, list) and storyboard_scenes:
        return [scene for scene in storyboard_scenes if isinstance(scene, dict)], "assets.storyboard.scenes"

    return [], "fallback"


def _experiment_rework_product_lock(original_generation_data: dict[str, Any]) -> dict[str, Any]:
    handoff = _experiment_rework_dict(original_generation_data.get("external_video_tool_handoff"))
    lock = _experiment_rework_dict(handoff.get("product_asset_lock"))
    if lock:
        return deepcopy(lock)

    video_packet = _experiment_rework_dict(original_generation_data.get("video_generation_packet"))
    video_text = " ".join(
        _experiment_rework_text(value, limit=180)
        for value in [
            _experiment_rework_dict(video_packet.get("video")).get("product_name", ""),
            video_packet.get("product_name", ""),
            video_packet.get("product_title", ""),
            video_packet.get("full_video_prompt", ""),
        ]
    ).strip()
    source_generation = _experiment_rework_dict(original_generation_data.get("source_generation"))
    product_identity = _experiment_rework_text(
        original_generation_data.get("product_name")
        or source_generation.get("product_name")
        or video_packet.get("product_name")
        or "Supplied product",
        limit=160,
    )
    if product_identity == "Supplied product" and video_text:
        product_identity = _experiment_rework_text(video_text, limit=120)
    product_category = _experiment_rework_text(
        original_generation_data.get("product_category")
        or source_generation.get("product_category")
        or video_packet.get("product_category")
        or "product",
        limit=120,
    )
    return {
        "lock_version": "product_asset_lock_v1",
        "product_identity": product_identity,
        "product_category": product_category,
        "visual_identity_source": "Use the supplied product fields, video packet, and manually supplied reference image when available.",
        "must_preserve": [
            f"Keep product identity as {product_identity}.",
            f"Keep product category as {product_category}; do not drift into another category.",
            "Preserve visible color, material, label placement, package shape, and scale from the supplied product reference.",
        ],
        "must_not_change": [
            "Do not invent fake variants, colors, package sizes, logos, or competitor products.",
            "Do not transform the product into a different category or unrealistic object.",
            "Do not change size, function, or product form factor without supplied evidence.",
        ],
        "image_reference_rules": [
            "Use a reference image when available.",
            "Reject output if product identity visibly drifts.",
        ],
        "human_review_required": True,
    }


def build_revised_keyframe_plan_from_experiment_feedback(
    original_generation_data: dict[str, Any],
    feedback_decision: dict[str, Any],
    experiment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic product-consistency keyframe rework artifact."""

    data = original_generation_data if isinstance(original_generation_data, dict) else {}
    decision = feedback_decision if isinstance(feedback_decision, dict) else {}
    experiment = experiment if isinstance(experiment, dict) else {}
    product_lock = _experiment_rework_product_lock(data)
    product_identity = _experiment_rework_text(product_lock.get("product_identity") or "supplied product", limit=160)
    product_category = _experiment_rework_text(product_lock.get("product_category") or "product", limit=120)
    scenes, scene_source = _experiment_rework_scene_source(data)
    reason_parts = [
        decision.get("reason"),
        decision.get("recommended_action"),
        experiment.get("failure_reason"),
        experiment.get("notes"),
    ]
    reason = _experiment_rework_text(" ".join(str(part or "") for part in reason_parts if part), limit=420)
    if not reason:
        reason = "Product consistency score was low; tighten visual identity before another external video test."

    global_rules = [
        "Keep the same product form factor in every scene.",
        "Keep the same color/material/label/package shape when those details are supplied.",
        "Do not change product category.",
        "Do not add brand, logo, variant, color, size, or packaging details not supplied.",
        "Do not change product size, function, or use case without supplied evidence.",
        "Use a reference image when available.",
        "Show the product clearly in the first frame.",
        "Avoid morphing, replacing, or visually drifting away from the product.",
    ]
    must_preserve = _experiment_rework_list(product_lock.get("must_preserve"), limit=5)
    must_not_change = _experiment_rework_list(product_lock.get("must_not_change"), limit=5)
    image_rules = _experiment_rework_list(product_lock.get("image_reference_rules"), limit=4)

    revised_scenes: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes[:4]):
        scene_index = int(scene.get("scene_id") or scene.get("scene_index") or index + 1)
        original_goal = _experiment_rework_text(
            scene.get("keyframe_goal")
            or scene.get("visual_prompt")
            or scene.get("visual_description")
            or scene.get("scene_goal")
            or f"Create scene {scene_index} for {product_identity}.",
            limit=300,
        )
        evidence_anchor = _experiment_rework_text(
            scene.get("evidence_anchor")
            or scene.get("evidence_quote")
            or scene.get("evidence_quote_used")
            or scene.get("linked_painpoint")
            or "",
            limit=220,
        )
        revised_scenes.append(
            {
                "scene_index": scene_index,
                "scene_goal": original_goal,
                "original_keyframe_goal": original_goal,
                "revised_keyframe_goal": _experiment_rework_text(
                    f"Regenerate scene {scene_index} with {product_identity} locked as the visible hero product. "
                    f"Keep category as {product_category}, show product clearly in the first frame, and correct the product-consistency issue: {reason}",
                    limit=420,
                ),
                "product_position": _experiment_rework_text(
                    scene.get("product_position")
                    or f"Keep {product_identity} centered or clearly foregrounded; do not replace it with a different object.",
                    limit=260,
                ),
                "camera_direction": _experiment_rework_text(
                    scene.get("camera_direction")
                    or "Use a stable close-up or gentle push-in that preserves product shape, label, material, and scale.",
                    limit=260,
                ),
                "identity_constraints": (must_preserve + image_rules + global_rules)[:8],
                "negative_constraints": (must_not_change + global_rules[2:5] + [global_rules[-1]])[:8],
                "evidence_anchor": evidence_anchor,
                "review_before_generation": True,
            }
        )

    if not revised_scenes:
        revised_scenes.append(
            {
                "scene_index": 1,
                "scene_goal": f"Create a conservative product-identity check clip for {product_identity}.",
                "original_keyframe_goal": "",
                "revised_keyframe_goal": f"Generate one short clip with {product_identity} clearly visible and locked to category {product_category}.",
                "product_position": f"Keep {product_identity} as the hero object in the first frame.",
                "camera_direction": "Static product close-up with clean lighting; avoid morphing.",
                "identity_constraints": (must_preserve + image_rules + global_rules)[:8],
                "negative_constraints": (must_not_change + global_rules[2:5] + [global_rules[-1]])[:8],
                "evidence_anchor": "",
                "review_before_generation": True,
            }
        )

    score_snapshot = dict(decision.get("score_snapshot") or {})
    for score_key in [
        "product_consistency_score",
        "storyboard_following_score",
        "visual_quality_score",
        "ad_readiness_score",
        "overall_score",
        "actual_cost_usd",
    ]:
        if score_key not in score_snapshot and score_key in experiment:
            score_snapshot[score_key] = experiment.get(score_key)

    return {
        "plan_version": "revised_keyframe_plan_v1",
        "source": "experiment_feedback_rework",
        "source_agent_id": "experiment_agent",
        "target_agent_id": "keyframe_agent",
        "secondary_target_agent_id": "asset_lock_agent",
        "issue_type": "product_consistency",
        "reason": reason,
        "score_snapshot": score_snapshot,
        "product_identity_lock": product_lock,
        "global_consistency_rules": global_rules,
        "source_scene_plan": scene_source,
        "revised_scene_keyframes": revised_scenes,
        "recommended_next_action": "Regenerate one short clip using the revised keyframe plan before full video generation.",
        "human_review_required": True,
    }


def _revised_handoff_product_lock(revised_keyframe_plan: dict[str, Any]) -> dict[str, Any]:
    return _experiment_rework_dict(revised_keyframe_plan.get("product_identity_lock"))


def _revised_handoff_scene_lines(revised_keyframe_plan: dict[str, Any]) -> list[str]:
    scenes = revised_keyframe_plan.get("revised_scene_keyframes")
    if not isinstance(scenes, list):
        return []
    lines: list[str] = []
    for scene in scenes[:4]:
        if not isinstance(scene, dict):
            continue
        scene_index = scene.get("scene_index") or len(lines) + 1
        revised_goal = _experiment_rework_text(scene.get("revised_keyframe_goal") or scene.get("scene_goal"), limit=360)
        product_position = _experiment_rework_text(scene.get("product_position"), limit=220)
        camera_direction = _experiment_rework_text(scene.get("camera_direction"), limit=220)
        evidence = _experiment_rework_text(scene.get("evidence_anchor"), limit=180)
        line = (
            f"Scene {scene_index}: {revised_goal} "
            f"Product position: {product_position or 'product clearly visible in first frame'}. "
            f"Camera: {camera_direction or 'stable product-safe close-up'}. "
            f"Evidence: {evidence or 'use supplied evidence only'}."
        )
        lines.append(_experiment_rework_text(line, limit=700))
    return lines


def build_revised_external_video_handoff_from_keyframe_plan(
    original_generation_data: dict[str, Any],
    revised_keyframe_plan: dict[str, Any],
    feedback_decision: dict[str, Any],
    experiment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic revised external video prompts from revised keyframes."""

    data = original_generation_data if isinstance(original_generation_data, dict) else {}
    plan = revised_keyframe_plan if isinstance(revised_keyframe_plan, dict) else {}
    decision = feedback_decision if isinstance(feedback_decision, dict) else {}
    experiment = experiment if isinstance(experiment, dict) else {}
    product_lock = _revised_handoff_product_lock(plan)
    product_identity = _experiment_rework_text(product_lock.get("product_identity") or "supplied product", limit=160)
    product_category = _experiment_rework_text(product_lock.get("product_category") or "product", limit=120)
    score_snapshot = dict(plan.get("score_snapshot") or decision.get("score_snapshot") or {})
    for score_key in [
        "product_consistency_score",
        "storyboard_following_score",
        "visual_quality_score",
        "ad_readiness_score",
        "overall_score",
        "actual_cost_usd",
    ]:
        if score_key not in score_snapshot and score_key in experiment:
            score_snapshot[score_key] = experiment.get(score_key)

    reason_parts = [
        plan.get("reason"),
        decision.get("reason"),
        decision.get("recommended_action"),
        experiment.get("failure_reason"),
        experiment.get("notes"),
    ]
    reason = _experiment_rework_text(" ".join(str(part or "") for part in reason_parts if part), limit=460)
    if not reason:
        reason = "Previous external output drifted from product identity; regenerate with stricter keyframe constraints."

    scene_lines = _revised_handoff_scene_lines(plan)
    scene_prompt = " | ".join(scene_lines) or f"Scene 1: show {product_identity} clearly, preserve category {product_category}, and review before full generation."
    global_rules = _experiment_rework_list(plan.get("global_consistency_rules"), limit=8, text_limit=240)
    product_rules = _experiment_rework_list(product_lock.get("must_preserve"), limit=5, text_limit=240)
    negative_rules = _experiment_rework_list(product_lock.get("must_not_change"), limit=5, text_limit=240)
    image_rules = _experiment_rework_list(product_lock.get("image_reference_rules"), limit=4, text_limit=240)
    keyframe_constraints = []
    for scene in plan.get("revised_scene_keyframes") or []:
        if not isinstance(scene, dict):
            continue
        for value in scene.get("identity_constraints") or []:
            text = _experiment_rework_text(value, limit=220)
            if text and text not in keyframe_constraints:
                keyframe_constraints.append(text)
        if len(keyframe_constraints) >= 8:
            break
    product_consistency_rules = list(dict.fromkeys(product_rules + image_rules + global_rules))[:10]
    if not product_consistency_rules:
        product_consistency_rules = [
            "Keep the exact same product identity.",
            "Use the product reference image if available.",
            "Show the product clearly in the first frame.",
            "Avoid morphing, replacing, or redesigning the product.",
            "Do not add brand/logo not supplied.",
            "Do not change product category or function.",
        ]
    negative_constraints = list(dict.fromkeys(negative_rules + [
        "Do not add brand/logo not supplied.",
        "Do not change product category or function.",
        "Do not morph, replace, or redesign the product.",
        "Do not make unsupported claims or full-market promises.",
    ]))[:10]
    prompt_strategy = _experiment_rework_text(
        "Use the revised keyframe plan as the scene-by-scene source of truth. "
        "Run one short external video test first, check product identity and product consistency, "
        "then decide whether to generate the full clip.",
        limit=520,
    )
    constraints_text = "; ".join(product_consistency_rules[:6])
    negative_prompt = _experiment_rework_text(
        "Do not change product category, function, form factor, color/material/package shape, supplied brand/logo boundaries, "
        "or reference-image identity. Do not invent variants, competitor products, unsupported claims, fake reviews, "
        "medical claims, or full-market statistics. Avoid morphing or replacing the product.",
        limit=900,
    )
    gemini_prompt = _experiment_rework_text(
        f"Create a revised vertical ecommerce video test for {product_identity} ({product_category}). "
        f"Source: revised keyframe plan from experiment feedback. Reason: {reason}. "
        f"Use product reference image if available. Product consistency rules: {constraints_text}. "
        f"Follow revised scene keyframes exactly: {scene_prompt}. "
        "Generate one short clip first and require human review before full video generation.",
        limit=1800,
    )
    doubao_prompt = _experiment_rework_text(
        f"Regenerate a short vertical product video draft for {product_identity}. "
        f"Keep category as {product_category}; do not redesign or replace the product. "
        f"Scene-by-scene revised keyframes: {scene_prompt}. "
        f"Negative constraints: {'; '.join(negative_constraints[:6])}. "
        "Output one short test clip first for product-consistency review.",
        limit=1800,
    )
    image_to_video_prompt = _experiment_rework_text(
        f"Use the uploaded/reference product image as identity source for {product_identity}. "
        f"Animate only according to the revised keyframe plan. Show product clearly in the first frame, "
        f"preserve {product_category} category, keep color/material/shape/scale stable, and avoid morphing or replacement.",
        limit=1100,
    )
    short_motion_prompt = _experiment_rework_text(
        f"{product_identity}, vertical short-form ecommerce motion, stable close-up, product clearly visible, "
        "conservative motion, reference-image identity lock, no redesign, one short test clip.",
        limit=700,
    )
    copy_ready_generation_brief = "\n".join(
        [
            "Revised external video handoff",
            f"Product: {product_identity}",
            f"Category: {product_category}",
            f"Issue: {plan.get('issue_type') or decision.get('issue_type') or 'product_consistency'}",
            f"Reason: {reason}",
            f"Strategy: {prompt_strategy}",
            "Product consistency rules:",
            *[f"- {rule}" for rule in product_consistency_rules[:8]],
            "Revised scene keyframes:",
            *[f"- {line}" for line in scene_lines[:4]],
            "Gemini prompt:",
            gemini_prompt,
            "Doubao prompt:",
            doubao_prompt,
            "Image-to-video prompt:",
            image_to_video_prompt,
            "Short motion prompt:",
            short_motion_prompt,
            "Negative prompt:",
            negative_prompt,
            "Next action: Run one short external video test using this revised prompt handoff before full video generation.",
        ]
    ).strip()

    return {
        "handoff_version": "revised_external_video_handoff_v1",
        "source": "experiment_feedback_rework",
        "source_agent_id": "keyframe_agent",
        "target_agent_id": "prompt_handoff_agent",
        "issue_type": "product_consistency",
        "reason": reason,
        "score_snapshot": score_snapshot,
        "revised_prompt_strategy": prompt_strategy,
        "tool_prompts": {
            "gemini_video_prompt": gemini_prompt,
            "doubao_video_prompt": doubao_prompt,
            "image_to_video_prompt": image_to_video_prompt,
            "short_motion_prompt": short_motion_prompt,
        },
        "negative_prompt": negative_prompt,
        "copy_ready_generation_brief": _experiment_rework_text(copy_ready_generation_brief, limit=3600),
        "product_consistency_rules": product_consistency_rules,
        "keyframe_constraints": keyframe_constraints[:8],
        "recommended_next_action": "Run one short external video test using the revised prompt handoff before full video generation.",
        "human_review_required": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
    }


def trigger_experiment_rework_run(
    job_id: str,
    feedback_decision: dict[str, Any],
    original_generation_data: dict[str, Any] | None = None,
    experiment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a rule-driven agent run scaffold for experiment feedback rework.

    Product-consistency feedback also creates a deterministic revised keyframe
    artifact. It intentionally does not call LLMs or external providers.
    """

    safe_decision = feedback_decision if isinstance(feedback_decision, dict) else {}
    if not safe_decision.get("has_feedback"):
        return {}

    target_agent_id = str(safe_decision.get("target_agent_id") or "keyframe_agent")
    secondary_target_agent_id = str(safe_decision.get("secondary_target_agent_id") or "")
    reason = str(safe_decision.get("reason") or "Experiment feedback requested upstream rework.")
    recommended_action = str(safe_decision.get("recommended_action") or "")
    severity = str(safe_decision.get("severity") or "medium")
    issue_type = str(safe_decision.get("issue_type") or "experiment_feedback")
    now = utc_now_iso()
    original_generation_data = original_generation_data if isinstance(original_generation_data, dict) else {}
    revised_keyframe_plan: dict[str, Any] = {}
    if issue_type == "product_consistency" and target_agent_id == "keyframe_agent":
        revised_keyframe_plan = build_revised_keyframe_plan_from_experiment_feedback(
            original_generation_data,
            safe_decision,
            experiment,
        )
    revised_external_video_handoff: dict[str, Any] = {}
    if revised_keyframe_plan:
        revised_external_video_handoff = build_revised_external_video_handoff_from_keyframe_plan(
            original_generation_data,
            revised_keyframe_plan,
            safe_decision,
            experiment,
        )
    feedback_router_decision = build_graph_router_decision(
        {
            "route_context_type": "experiment_feedback",
            "input_signal": issue_type,
            "issue_type": issue_type,
            "reason": reason,
            "score_deltas": safe_decision.get("score_snapshot") or {},
            "artifact_types": ["external_video_experiment"],
        },
        job={"job_id": job_id},
    )
    revised_keyframe_router_decision: dict[str, Any] = {}
    if revised_keyframe_plan and revised_external_video_handoff:
        revised_keyframe_router_decision = build_graph_router_decision(
            {
                "route_context_type": "revised_keyframe_created",
                "input_signal": revised_keyframe_plan.get("plan_version"),
                "reason": "Revised keyframes are ready for Prompt Handoff Agent.",
                "artifact_types": [
                    "revised_keyframe_plan",
                    "revised_external_video_handoff",
                ],
            },
            job={"job_id": job_id},
        )

    run = build_agent_run(
        input_type="experiment_feedback_rework",
        output_language=str(safe_decision.get("output_language") or "en"),
        request_id="",
        project_id=str(
            _experiment_rework_dict(original_generation_data).get("project_id")
            or "demo_project_default"
        ),
    )
    run["status"] = "completed"
    run["started_at"] = now
    run["completed_at"] = now
    run["current_agent_id"] = None
    run["active_node_id"] = None
    run["source_video_job_id"] = str(job_id or "")
    run["trigger_type"] = "external_video_experiment_feedback"
    run["trigger_feedback_decision"] = deepcopy(safe_decision)
    run["waiting_for_user"] = False
    run["waiting_reason"] = ""
    run["external_api_called"] = False
    run["cost_incurred_by_crossgrowth"] = False
    run["updated_at"] = now
    append_graph_router_decision(run, feedback_router_decision)
    if revised_keyframe_router_decision:
        append_graph_router_decision(run, revised_keyframe_router_decision)
    run["result"] = {
        "result_type": "experiment_feedback_rework_result" if revised_keyframe_plan else "experiment_feedback_rework_scaffold",
        "source_video_job_id": str(job_id or ""),
        "target_agent_id": target_agent_id,
        "secondary_target_agent_id": secondary_target_agent_id,
        "issue_type": issue_type,
        "feedback_decision": deepcopy(safe_decision),
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
    }
    if revised_keyframe_plan:
        run["result"]["revised_keyframe_plan"] = revised_keyframe_plan
        run["result"]["revised_external_video_handoff"] = revised_external_video_handoff
        run["result"]["agent_feedback_decision"] = deepcopy(safe_decision)
        run["result"]["next_agent_id"] = "prompt_handoff_agent"
        run["rework_artifacts"] = {
            "revised_keyframe_plan": True,
            "revised_external_video_handoff": bool(revised_external_video_handoff),
            "target_agent_id": target_agent_id,
            "secondary_target_agent_id": secondary_target_agent_id,
            "next_agent_id": "prompt_handoff_agent",
        }

    visited = ["experiment_agent", "graph_router_agent", target_agent_id]
    if secondary_target_agent_id:
        visited.append(secondary_target_agent_id)
    run["visited_node_ids"] = list(dict.fromkeys(visited))

    for node in run.get("graph_nodes", []):
        node_id = str(node.get("node_id") or "")
        if node_id == "experiment_agent":
            node["status"] = "complete"
        elif node_id == "graph_router_agent":
            node["status"] = "complete"
        elif node_id == target_agent_id or (secondary_target_agent_id and node_id == secondary_target_agent_id):
            node["status"] = "rework_requested"

    for agent in run.get("agents", []):
        agent_id = str(agent.get("agent_id") or "")
        if agent_id == "experiment_agent":
            agent["status"] = "complete"
            agent["completed_at"] = now
            agent["decision_summary"] = "Experiment Agent converted poor external scores into a graph feedback decision."
            agent["business_impact"] = "Poor external video results are routed back to the most relevant upstream agent."
        elif agent_id == "graph_router_agent":
            agent["status"] = "complete"
            agent["started_at"] = now
            agent["completed_at"] = now
            agent["decision_summary"] = str(run["latest_graph_router_decision"].get("reason") or "")
            agent["business_impact"] = "Centralizes the next graph edge while preserving human and provider safety boundaries."
        elif agent_id == target_agent_id or (secondary_target_agent_id and agent_id == secondary_target_agent_id):
            agent["status"] = "complete"
            agent["started_at"] = now
            agent["completed_at"] = now
            agent["decision_summary"] = reason
            agent["business_impact"] = recommended_action
            warnings = list(agent.get("warnings") or [])
            warnings.append(issue_type)
            agent["warnings"] = warnings

    edge_id = _experiment_rework_edge_id(target_agent_id)
    for edge in run.get("graph_edges", []):
        if edge.get("edge_id") == edge_id:
            edge["status"] = "traversed"
            edge["decision_reason"] = reason
            break
    run["active_edge_ids"] = [edge_id]

    transition = {
        "decision_id": str(uuid4()),
        "from_node_id": "experiment_agent",
        "selected_to_node_id": target_agent_id,
        "agent_id": "experiment_agent",
        "decision_type": "feedback_rework_requested",
        "reason": reason,
        "created_at": now,
        "data": {
            "feedback_decision": deepcopy(safe_decision),
            "secondary_target_agent_id": secondary_target_agent_id,
            "source_video_job_id": str(job_id or ""),
        },
    }
    validation = {
        "validation_id": str(uuid4()),
        "validator_agent_id": "experiment_agent",
        "target_agent_id": target_agent_id,
        "target_artifact": "external_video_experiment",
        "status": "failed" if severity == "high" else "warning",
        "reason": reason,
        "severity": severity,
        "rework_target": target_agent_id,
        "created_at": now,
    }
    loop = {
        "loop_id": str(uuid4()),
        "source_agent_id": "experiment_agent",
        "target_agent_id": target_agent_id,
        "reason": reason,
        "loop_count": 1,
        "max_loop_count": 1,
        "status": "requested",
    }
    run["transition_decisions"] = [transition]
    run["validation_results"] = [validation]
    run["rework_loops"] = [loop]
    run["loop_count"] = 1
    run["max_loop_count"] = 1
    run["events"] = [
        {
            "event_id": str(uuid4()),
            "event_type": "run_created",
            "agent_id": None,
            "message": "Experiment feedback-triggered rework run created.",
            "created_at": now,
            "data": {
                "input_type": "experiment_feedback_rework",
                "source_video_job_id": str(job_id or ""),
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        },
        {
            "event_id": str(uuid4()),
            "event_type": "graph_initialized",
            "agent_id": None,
            "message": "Rule-driven agent graph initialized for experiment feedback rework.",
            "created_at": now,
            "data": {
                "graph_version": GRAPH_VERSION,
                "graph_execution_mode": GRAPH_EXECUTION_MODE,
                "autonomy_level": AUTONOMY_LEVEL,
                "llm_autonomous_decision_enabled": False,
            },
        },
        {
            "event_id": str(uuid4()),
            "event_type": "transition_decision",
            "agent_id": "experiment_agent",
            "message": reason,
            "created_at": now,
            "data": deepcopy(transition),
        },
        {
            "event_id": str(uuid4()),
            "event_type": "graph_router_decision_created",
            "agent_id": "graph_router_agent",
            "message": feedback_router_decision["reason"],
            "created_at": now,
            "data": deepcopy(feedback_router_decision),
        },
        {
            "event_id": str(uuid4()),
            "event_type": "graph_router_route_selected",
            "agent_id": "graph_router_agent",
            "message": (
                f"Graph Router Agent selected {feedback_router_decision['selected_next_agent_id']} "
                f"for {feedback_router_decision['route_type']}."
            ),
            "created_at": now,
            "data": deepcopy(feedback_router_decision),
        },
        {
            "event_id": str(uuid4()),
            "event_type": "experiment_feedback_rework_requested",
            "agent_id": "experiment_agent",
            "message": recommended_action or reason,
            "created_at": now,
            "data": {
                "source_agent_id": "experiment_agent",
                "target_agent_id": target_agent_id,
                "secondary_target_agent_id": secondary_target_agent_id,
                "issue_type": issue_type,
                "severity": severity,
                "source_video_job_id": str(job_id or ""),
            },
        },
        {
            "event_id": str(uuid4()),
            "event_type": "node_started",
            "agent_id": target_agent_id,
            "message": f"{target_agent_id} started feedback-triggered rework scaffold.",
            "created_at": now,
            "data": {
                "node_id": target_agent_id,
                "source_agent_id": "experiment_agent",
                "issue_type": issue_type,
            },
        },
        {
            "event_id": str(uuid4()),
            "event_type": "rework_requested",
            "agent_id": "experiment_agent",
            "message": reason,
            "created_at": now,
            "data": deepcopy(loop),
        },
        *(
            [
                {
                    "event_id": str(uuid4()),
                    "event_type": "revised_keyframe_plan_created",
                    "agent_id": "keyframe_agent",
                    "message": "Revised keyframe plan created from experiment feedback.",
                    "created_at": now,
                    "data": {
                        "plan_version": revised_keyframe_plan.get("plan_version", ""),
                        "target_agent_id": target_agent_id,
                        "secondary_target_agent_id": secondary_target_agent_id,
                        "issue_type": issue_type,
                        "source_video_job_id": str(job_id or ""),
                    },
                },
                {
                    "event_id": str(uuid4()),
                    "event_type": "rework_artifact_created",
                    "agent_id": "keyframe_agent",
                    "message": "Feedback-triggered rework artifact created.",
                    "created_at": now,
                    "data": {
                        "artifact_type": "revised_keyframe_plan",
                        "target_agent_id": target_agent_id,
                        "source_video_job_id": str(job_id or ""),
                    },
                },
                {
                    "event_id": str(uuid4()),
                    "event_type": "revised_external_video_handoff_created",
                    "agent_id": "prompt_handoff_agent",
                    "message": "Revised external video handoff created from revised keyframes.",
                    "created_at": now,
                    "data": {
                        "handoff_version": revised_external_video_handoff.get("handoff_version", ""),
                        "target_agent_id": "prompt_handoff_agent",
                        "source_video_job_id": str(job_id or ""),
                    },
                },
                {
                    "event_id": str(uuid4()),
                    "event_type": "revised_prompt_handoff_created",
                    "agent_id": "prompt_handoff_agent",
                    "message": "Revised prompt handoff created for next external video test.",
                    "created_at": now,
                    "data": {
                        "artifact_type": "revised_external_video_handoff",
                        "next_agent_id": "prompt_handoff_agent",
                        "source_video_job_id": str(job_id or ""),
                    },
                },
                {
                    "event_id": str(uuid4()),
                    "event_type": "graph_router_decision_created",
                    "agent_id": "graph_router_agent",
                    "message": revised_keyframe_router_decision["reason"],
                    "created_at": now,
                    "data": deepcopy(revised_keyframe_router_decision),
                },
                {
                    "event_id": str(uuid4()),
                    "event_type": "graph_router_route_selected",
                    "agent_id": "graph_router_agent",
                    "message": "Graph Router Agent routed revised keyframes to Prompt Handoff Agent.",
                    "created_at": now,
                    "data": deepcopy(revised_keyframe_router_decision),
                },
            ]
            if revised_keyframe_plan
            else []
        ),
        {
            "event_id": str(uuid4()),
            "event_type": "node_completed",
            "agent_id": target_agent_id,
            "message": (
                f"{target_agent_id} created revised keyframe plan."
                if revised_keyframe_plan
                else f"{target_agent_id} completed feedback-triggered rework scaffold."
            ),
            "created_at": now,
            "data": {
                "node_id": target_agent_id,
                "source_agent_id": "experiment_agent",
                "issue_type": issue_type,
                "recommended_action": recommended_action,
                "artifact_type": "revised_keyframe_plan" if revised_keyframe_plan else "",
            },
        },
        {
            "event_id": str(uuid4()),
            "event_type": "graph_completed",
            "agent_id": None,
            "message": "Experiment feedback-triggered rework graph completed.",
            "created_at": now,
            "data": {
                "source_video_job_id": str(job_id or ""),
                "target_agent_id": target_agent_id,
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        },
        {
            "event_id": str(uuid4()),
            "event_type": "run_completed",
            "agent_id": None,
            "message": "Experiment feedback-triggered rework run completed.",
            "created_at": now,
            "data": {
                "has_result": True,
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        },
    ]
    return run


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
            "graph_router_agent",
            "Graph Router Agent",
            "Review the selected graph route and its safety boundary.",
            ["validation_results", "experiment_feedback", "comparison_gate"],
            ["graph_router_decision"],
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
        build_graph_node("source_adapter_agent", "source_adapter_agent", "Source Adapter", "agent", "Normalize the project source without bypassing platform controls.", "Review source warnings and manual fallback requirements.", ["project_source_request"], ["project_source"]),
        build_graph_node("source_quality_agent", "source_quality_agent", "Source Quality Gate", "validation", "Check source confidence and evidence readiness.", "Add manual reviews when source evidence is insufficient.", ["project_source"], ["source_quality_gate"]),
        build_graph_node("source_evidence_agent", "source_evidence_agent", "Source Evidence", "agent", "Create the project-scoped source evidence artifact.", "Review classifications before creative generation.", ["source_quality_gate"], ["source_evidence_artifact"]),
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
        build_graph_node("graph_router_agent", "graph_router_agent", "Graph Router Agent", "router", "Centralize deterministic graph branch, loop, gate, and human-approval route decisions.", "Review the selected graph edge and safety boundary.", ["validation_results", "experiment_feedback", "comparison_gate"], ["graph_router_decision"]),
        build_graph_node("finalizer_agent", "finalizer_agent", "Finalizer Agent", "terminal", "Finalize generated artifacts for the Product dashboard.", "Use the completed result for copy, video jobs, and manual handoff.", ["all_generated_artifacts"], ["final_product_result"]),
    ]


def default_agent_graph_edges() -> list[dict[str, Any]]:
    return [
        build_graph_edge("planner_to_source_adapter", "planner_agent", "source_adapter_agent", "normal", "request valid"),
        build_graph_edge("source_adapter_to_source_quality", "source_adapter_agent", "source_quality_agent", "validation", "source normalized"),
        build_graph_edge("source_quality_to_source_evidence", "source_quality_agent", "source_evidence_agent", "normal", "source evidence ready"),
        build_graph_edge("source_quality_manual_fallback", "source_quality_agent", "source_adapter_agent", "waiting_for_user", "manual fallback required"),
        build_graph_edge("source_evidence_to_evidence", "source_evidence_agent", "evidence_agent", "normal", "source evidence artifact created"),
        build_graph_edge("planner_to_evidence", "planner_agent", "evidence_agent", "normal", "legacy request valid"),
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
        build_graph_edge("experiment_to_prompt_handoff_rework", "experiment_agent", "prompt_handoff_agent", "rework", "experiment did not follow storyboard or visual prompt constraints"),
        build_graph_edge("experiment_to_storyboard_rework", "experiment_agent", "storyboard_agent", "rework", "experiment was not ad-ready"),
        build_graph_edge("experiment_to_cost_rework", "experiment_agent", "cost_agent", "rework", "experiment cost/value was not acceptable"),
        build_graph_edge("experiment_to_finalizer", "experiment_agent", "finalizer_agent", "normal", "experiment accepted"),
        build_graph_edge("prompt_handoff_to_finalizer_fallback", "prompt_handoff_agent", "finalizer_agent", "fallback", "manual external tool workflow selected"),
    ]


def build_agent_run(
    input_type: str,
    output_language: str,
    request_id: str = "",
    project_id: str = "demo_project_default",
) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "run_id": str(uuid4()),
        "project_id": str(project_id or "demo_project_default"),
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
        "graph_router_decisions": [],
        "latest_graph_router_decision": {},
        "graph_router_summary": {
            "router_version": "graph_router_agent_v1",
            "decision_count": 0,
            "has_rework_route": False,
            "has_provider_route": False,
            "has_human_approval_route": False,
            "has_stop_route": False,
            "is_linear_workflow": False,
        },
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
            current_loop_count = int(run.get("loop_count") or 0)
            loop_count = current_loop_count if status == "blocked" else current_loop_count + 1
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
