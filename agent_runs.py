"""In-memory async agent run state for staged creative generation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
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

    run = build_agent_run(
        input_type="experiment_feedback_rework",
        output_language=str(safe_decision.get("output_language") or "en"),
        request_id="",
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

    visited = ["experiment_agent", target_agent_id]
    if secondary_target_agent_id:
        visited.append(secondary_target_agent_id)
    run["visited_node_ids"] = list(dict.fromkeys(visited))

    for node in run.get("graph_nodes", []):
        node_id = str(node.get("node_id") or "")
        if node_id == "experiment_agent":
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
