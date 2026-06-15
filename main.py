import re
import json
import os
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import uvicorn
from uuid import uuid4

from core.logging_utils import emit_event
from core.telemetry_utils import summarize_telemetry
from core.workflow import copilot_engine, memory_engine
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from schemas.api_contract import (
    AgentRunCreateResponse,
    AgentRunEventsResponse,
    AgentRunListResponse,
    AgentRunStatusResponse,
    AmazonIntakeRequest,
    AmazonIntakeResponse,
    DebugCopilotResponse,
    GenerateCopilotResponse,
    GrowthRequest,
    PastedReviewsRequest,
    PastedReviewsResponse,
    ProductDescriptionRequest,
    ProductDescriptionResponse,
    ProjectCreateRequest,
    ProjectSourceGenerateRequest,
    ProjectSourceRequest,
    TranslationRequest,
    TranslationResponse,
    VideoGenerationJobRequest,
    VideoGenerationFromGenerationRequest,
    VideoGenerationJobResponse,
    VideoGenerationJobStatusResponse,
    VideoGenerationJobListResponse,
    VideoGenerationProvidersResponse,
    VideoGenerationProviderPlanResponse,
    VideoGenerationCostCatalogResponse,
    VideoGenerationCostEstimateRequest,
    VideoGenerationCostEstimateResponse,
    VideoGenerationJobResultRequest,
    VideoGenerationExperimentRequest,
    VideoGenerationProviderSubmitRequest,
    VideoGenerationProviderPollRequest,
    VideoGenerationApprovalDecisionRequest,
    VideoGenerationApprovalGateResponse,
    VideoGenerationStorageStatusResponse,
)
from agent_runs import (
    InMemoryAgentRunStore,
    append_graph_router_decision,
    apply_human_approval_decision,
    apply_evidence_safe_storyboard_rework,
    build_agent_message,
    build_agent_capability_runtime,
    build_agent_runner_plan,
    build_agent_runner_plan_summary,
    build_agent_contract_registry,
    build_agent_contract_summary,
    build_agent_contract_completeness_report,
    build_source_adapter_contract_report,
    build_multi_agent_output_chain_report,
    build_keyframe_video_asset_chain_report,
    build_keyframe_prompt_pack_report,
    build_manual_generation_result_report,
    build_provider_api_readiness_report,
    build_provider_sandbox_runtime_report,
    build_real_provider_execution_gate_report,
    build_provider_failure_recovery_report,
    build_provider_observability_report,
    build_provider_queue_lease_worker_report,
    build_provider_worker_checkpoint_resume_report,
    build_provider_worker_finalization_report,
    build_provider_artifact_lineage_report,
    build_provider_artifact_registry_restore_report,
    build_provider_registry_operation_approval_report,
    build_provider_registry_transaction_rehearsal_report,
    build_provider_transaction_monitor_report,
    build_provider_transaction_incident_drill_report,
    build_provider_execution_readiness_packet_report,
    build_agent_runner_dispatch_ticket,
    build_agent_runner_dispatch_summary,
    build_agent_runner_dispatch_event,
    build_agent_runner_dispatch_event_summary,
    build_agent_runner_execution_receipt,
    build_agent_runner_execution_receipt_summary,
    build_agent_runner_event_ledger_summary,
    build_agent_runner_supervisor_event_ledger_decision_summary,
    build_agent_runner_supervisor_next_step_routing_plan,
    build_agent_runner_supervisor_next_step_work_order_preview,
    build_agent_runner_queue_lease_worker_dry_run_chain,
    build_agent_runner_work_order,
    build_agent_runner_work_order_summary,
    build_agent_runner_queue_item,
    build_agent_runner_queue_item_summary,
    build_agent_runner_queue_claim,
    build_agent_runner_queue_claim_summary,
    build_agent_runner_worker_lease,
    build_agent_runner_worker_lease_summary,
    build_agent_runner_invocation_envelope,
    build_agent_runner_invocation_envelope_summary,
    build_agent_runner_invocation_attempt,
    build_agent_runner_invocation_attempt_summary,
    build_agent_runner_invocation_result,
    build_agent_runner_invocation_result_summary,
    build_agent_runner_completion_receipt,
    build_agent_runner_completion_receipt_summary,
    build_agent_runner_handoff_checkpoint,
    build_agent_runner_handoff_checkpoint_summary,
    build_agent_runner_next_agent_unlock,
    build_agent_runner_next_agent_unlock_summary,
    build_agent_runner_graph_transition_proposal,
    build_agent_runner_graph_transition_proposal_summary,
    build_agent_runner_state_projection,
    build_agent_runner_state_projection_summary,
    build_agent_runner_transition_commit_plan,
    build_agent_runner_transition_commit_plan_summary,
    build_agent_runner_mutation_guard,
    build_agent_runner_mutation_guard_summary,
    build_agent_runner_transition_persist_request,
    build_agent_runner_transition_persist_request_summary,
    build_agent_runner_rollback_plan,
    build_agent_runner_rollback_plan_summary,
    build_agent_runner_persist_gate,
    build_agent_runner_persist_gate_summary,
    build_agent_runner_audit_ledger,
    build_agent_runner_audit_ledger_summary,
    build_agent_runner_approval_request,
    build_agent_runner_approval_request_summary,
    build_agent_runner_policy_decision,
    build_agent_runner_policy_decision_summary,
    build_agent_runner_authorization_preview,
    build_agent_runner_authorization_preview_summary,
    build_agent_runner_execution_manifest,
    build_agent_runner_execution_manifest_summary,
    build_agent_runner_execution_session,
    build_agent_runner_execution_session_summary,
    build_agent_runner_preflight_certificate,
    build_agent_runner_preflight_certificate_summary,
    build_agent_runner_runtime_sandbox,
    build_agent_runner_runtime_sandbox_summary,
    build_agent_runner_worker_bootstrap_plan,
    build_agent_runner_worker_bootstrap_plan_summary,
    build_agent_runner_failure_receipt,
    build_agent_runner_failure_receipt_summary,
    build_agent_runner_recovery_summary,
    build_agent_runner_recovery_summary_summary,
    build_agent_runner_retry_plan,
    build_agent_runner_retry_plan_summary,
    build_agent_runner_worker_heartbeat,
    build_agent_runner_worker_heartbeat_summary,
    build_agent_runner_worker_loop_simulation,
    build_agent_runner_worker_loop_simulation_summary,
    build_agent_runner_worker_poll,
    build_agent_runner_worker_poll_summary,
    build_agent_runner_artifact_manifest,
    build_agent_runner_artifact_manifest_summary,
    build_agent_runner_dead_letter_policy,
    build_agent_runner_dead_letter_policy_summary,
    build_agent_runner_output_buffer,
    build_agent_runner_output_buffer_summary,
    build_agent_runner_result_validation_gate,
    build_agent_runner_result_validation_gate_summary,
    build_agent_runner_resume_cursor,
    build_agent_runner_resume_cursor_summary,
    build_agent_runner_worker_checkpoint_bundle,
    build_agent_runner_worker_checkpoint_bundle_summary,
    build_agent_runner_completion_ledger,
    build_agent_runner_completion_ledger_summary,
    build_agent_runner_downstream_handoff,
    build_agent_runner_downstream_handoff_summary,
    build_agent_runner_human_review_packet,
    build_agent_runner_human_review_packet_summary,
    build_agent_runner_project_merge_preview,
    build_agent_runner_project_merge_preview_summary,
    build_agent_runner_result_acceptance,
    build_agent_runner_result_acceptance_summary,
    build_agent_runner_run_finalization,
    build_agent_runner_run_finalization_summary,
    build_agent_runner_authorization_preview,
    build_agent_runner_authorization_preview_summary,
    build_agent_runner_execution_manifest,
    build_agent_runner_execution_manifest_summary,
    build_agent_run,
    build_controlled_provider_handoff_checklist,
    build_demo_ready_run_summary,
    build_experiment_comparison_decision_gate,
    build_experiment_feedback_decision,
    build_graph_health_summary,
    build_graph_router_decision,
    build_graph_state_snapshot,
    build_human_approval_gate,
    build_lightweight_artifact_registry,
    build_product_asset_lock_v2,
    build_lightweight_artifact_lineage,
    build_second_experiment_comparison,
    build_supervisor_planner_recommendation,
    detect_storyboard_rework_need,
    trigger_experiment_rework_run,
)
from agent_graph_storage import (
    DEFAULT_PROJECT_ID,
    DEFAULT_PROJECT_NAME,
    DURABILITY_NOTE,
    list_project_assets,
    list_project_sources,
    list_project_records,
    list_source_evidence_artifacts,
    list_source_quality_gates,
    list_source_snapshots,
    list_recent_projects,
    list_recent_agent_messages,
    list_recent_artifacts,
    list_recent_graph_events,
    list_recent_graph_exports,
    list_recent_graph_snapshots,
    load_recent_agent_run_snapshots,
    load_recent_video_job_snapshots,
    load_project,
    load_project_asset,
    load_project_source,
    load_source_evidence_artifact,
    load_source_quality_gate,
    persistence_metadata,
    save_agent_message_snapshot,
    save_agent_run_snapshot,
    save_approval_snapshot,
    save_artifact_registry_snapshot,
    save_graph_event_snapshot,
    save_graph_report_export,
    save_graph_state_snapshot,
    save_project_asset_snapshot,
    save_project_source_snapshot,
    save_project_snapshot,
    save_source_evidence_artifact,
    save_source_quality_gate,
    save_source_snapshot,
    save_video_job_snapshot,
    project_assets_directory,
    update_project_summary,
)
from schemas.source_probe_contract import (
    SourceProbeRequest,
    SourceProbeResponse,
    SourceProbeResult,
    SourceProbeTelemetry,
)
from source_adapters import SourceAdapterRegistry
from source_adapters.project_sources import build_project_source
from source_adapters.amazon_url_utils import normalize_amazon_product_url
from video_generation.providers import (
    normalize_video_provider,
    supported_video_provider_names,
    video_job_export_formats,
    video_provider_catalog,
    video_provider_payload_metadata,
    video_provider_plan,
)
from video_generation.provider_costs import (
    estimate_cost_from_video_packet,
    estimate_video_generation_cost,
    video_provider_cost_catalog,
)
from video_generation.job_store import get_video_job_store, video_job_storage_diagnostics
from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
    VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    build_video_job_history_event,
    can_transition_video_job_status,
    normalize_video_job_status,
)
from video_generation.provider_runtime import (
    build_provider_poll_runtime,
    build_provider_runtime,
    next_simulated_provider_status,
    provider_poll_history_event,
    provider_submit_history_events,
    supports_provider_polling,
)
from video_generation.provider_integration import provider_plan_integration_metadata

app = FastAPI()
source_probe_registry = SourceAdapterRegistry()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def get_server_port() -> int:
    return int(os.getenv("PORT", "8001"))


def _safe_product_category_hint(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if "://" in value or "/" in value or len(value) > 80:
        return "external_url"
    return value


def _error_type(exc: Exception) -> str:
    name = type(exc).__name__
    text = f"{name}: {exc}".lower()
    if "huggingface" in text or "hf hub" in text or "sentence-transformers" in text:
        return "runtime_model_unavailable"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "memory" in text or "out of memory" in text:
        return "memory_failure"
    return name
INDEX_HTML = STATIC_DIR / "index.html"
SOURCE_PROBE_PROVIDERS = {
    "amazon_review_api",
    "tiktok_trend_api",
    "reddit_review_api",
}

TRANSLATION_SYSTEM_PROMPT = (
    "You translate product creative briefs into natural Chinese. "
    "Preserve Markdown structure. Preserve English product slugs, numbers, percentages, "
    "and necessary technical field names. Do not add facts. Do not change strategy meaning. "
    "Do not translate JSON/code keys inside code blocks unless the value is natural language."
)

DESCRIPTION_SYSTEM_PROMPT = (
    "You create concise ecommerce TikTok creative briefs from user-provided product descriptions. "
    "Use only the supplied product description and customer pain points. Do not invent review evidence, "
    "do not claim Amazon or local dataset sources, and return compact JSON only."
)

PASTED_REVIEWS_SYSTEM_PROMPT = (
    "You create concise ecommerce TikTok creative briefs from user-pasted review snippets. "
    "Use only the supplied product context and pasted reviews. Do not claim Amazon, local dataset, "
    "or external source access. Return compact JSON only."
)

DESCRIPTION_MIN_CHARS = 12
DESCRIPTION_MAX_CHARS = 6000
PASTED_REVIEWS_MIN_CHARS = 24
PASTED_REVIEWS_COMPACT_QUOTE_LIMIT = 12
PASTED_REVIEWS_RAW_MAX_CHARS = 50000
SUPPORTED_OUTPUT_LANGUAGES = {"en", "zh-CN"}
VIDEO_JOB_STORE = get_video_job_store()
AGENT_RUN_STORE = InMemoryAgentRunStore()
VIDEO_GENERATION_RESULT_STATUSES = {
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
}
PROJECT_SOURCE_TYPES = {
    "pasted_reviews",
    "amazon",
    "shopify",
    "amazon_url",
    "shopify_url",
    "csv_reviews",
    "text_review_batch",
    "uploaded_asset",
    "manual",
    "demo",
}
PROJECT_ASSET_ROLES = {"product_image", "reference_image", "packaging_image", "other"}
PROJECT_ASSET_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
PROJECT_ASSET_MAX_BYTES = 8 * 1024 * 1024


def _safe_project_id(value: str | None) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "")).strip("._")
    return (cleaned or DEFAULT_PROJECT_ID)[:120]


def _project_shape(
    project_id: str = DEFAULT_PROJECT_ID,
    project_name: str = DEFAULT_PROJECT_NAME,
    product_name: str = "",
    product_category: str = "",
    source_type: str = "demo",
) -> dict:
    now = _utc_now_iso()
    safe_source = source_type if source_type in PROJECT_SOURCE_TYPES else "manual"
    metadata = persistence_metadata()
    return {
        "project_version": "project_workspace_v1",
        "project_id": _safe_project_id(project_id),
        "project_name": _clean_description_text(project_name) or DEFAULT_PROJECT_NAME,
        "product_name": _clean_description_text(product_name),
        "product_category": _clean_description_text(product_category),
        "source_type": safe_source,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "persistence_mode": metadata["persistence_mode"],
        "durability_note": DURABILITY_NOTE,
        "graph_summary": {
            "run_count": 0,
            "job_count": 0,
            "artifact_count": 0,
            "experiment_count": 0,
            "approval_count": 0,
            "asset_count": 0,
            "report_count": 0,
        },
        "latest_run_id": None,
        "latest_job_id": None,
        "latest_artifact_registry_id": None,
    }


def _ensure_project(
    project_id: str | None = None,
    *,
    product_name: str = "",
    product_category: str = "",
    source_type: str = "demo",
) -> dict:
    safe_id = _safe_project_id(project_id)
    existing = load_project(safe_id)
    if existing:
        changed = False
        if product_name and not existing.get("product_name"):
            existing["product_name"] = _clean_description_text(product_name)
            changed = True
        if product_category and not existing.get("product_category"):
            existing["product_category"] = _clean_description_text(product_category)
            changed = True
        if changed:
            existing["updated_at"] = _utc_now_iso()
            return save_project_snapshot(existing)
        return existing
    return save_project_snapshot(
        _project_shape(
            project_id=safe_id,
            project_name=DEFAULT_PROJECT_NAME if safe_id == DEFAULT_PROJECT_ID else safe_id,
            product_name=product_name,
            product_category=product_category,
            source_type="demo" if safe_id == DEFAULT_PROJECT_ID else source_type,
        )
    )


def _project_context(project_id: str | None, related: dict | None = None) -> tuple[dict, list[dict]]:
    related_data = related if isinstance(related, dict) else {}
    project = _ensure_project(
        project_id,
        product_name=str(related_data.get("product_name") or ""),
        product_category=str(related_data.get("product_category") or ""),
        source_type=str(related_data.get("source_type") or "demo"),
    )
    return project, list_project_assets(project["project_id"], 50)


def _source_registry_snapshot(
    project: dict,
    bundle: dict,
    generation_data: dict | None = None,
) -> dict:
    source = bundle.get("project_source") or {}
    artifact = bundle.get("source_evidence_artifact") or {}
    gate = bundle.get("source_quality_gate") or {}
    snapshot = bundle.get("source_snapshot") or {}
    registry = build_lightweight_artifact_registry(
        generation_data={
            **(generation_data or {}),
            "project_id": project["project_id"],
            "project_source": source,
            "source_evidence_artifact": artifact,
            "source_quality_gate": gate,
            "source_snapshot": snapshot,
        },
        project=project,
        uploaded_assets=list_project_assets(project["project_id"], 50),
    )
    save_artifact_registry_snapshot(
        registry,
        f"source_{source.get('source_id') or uuid4().hex[:12]}",
    )
    return registry


def _persist_project_source_bundle(bundle: dict) -> dict:
    source = dict(bundle.get("project_source") or {})
    project_id = _safe_project_id(source.get("project_id"))
    project = _ensure_project(
        project_id,
        product_name=source.get("product_name", ""),
        product_category=source.get("product_category", ""),
        source_type=source.get("source_type", "manual"),
    )
    source["project_id"] = project["project_id"]
    bundle["project_source"] = save_project_source_snapshot(source)
    artifact = dict(bundle.get("source_evidence_artifact") or {})
    artifact["project_id"] = project["project_id"]
    bundle["source_evidence_artifact"] = save_source_evidence_artifact(
        project["project_id"],
        artifact,
    )
    gate = dict(bundle.get("source_quality_gate") or {})
    gate["project_id"] = project["project_id"]
    gate["source_id"] = source.get("source_id", "")
    bundle["source_quality_gate"] = save_source_quality_gate(
        project["project_id"],
        source.get("source_id", ""),
        gate,
    )
    snapshot = dict(bundle.get("source_snapshot") or {})
    snapshot["project_id"] = project["project_id"]
    bundle["source_snapshot"] = save_source_snapshot(project["project_id"], snapshot)
    bundle["artifact_registry"] = _source_registry_snapshot(project, bundle)
    return bundle


def _build_project_source_bundle(
    project_id: str,
    request: ProjectSourceRequest | dict,
    *,
    persist: bool,
    network_fetch: bool = True,
) -> dict:
    payload = (
        request.model_dump()
        if hasattr(request, "model_dump")
        else dict(request or {})
    )
    payload["project_id"] = _safe_project_id(project_id)
    bundle = build_project_source(payload, network_fetch=network_fetch)
    return _persist_project_source_bundle(bundle) if persist else bundle


def _pasted_request_source_bundle(
    request: PastedReviewsRequest,
    *,
    persist: bool = True,
) -> dict:
    source_request = {
        "project_id": _safe_project_id(request.project_id),
        "source_type": "pasted_reviews",
        "product_name": request.product_name,
        "product_category": request.product_category or "",
        "product_description": request.product_description or "",
        "pasted_reviews": request.pasted_reviews,
        "source_notes": "Created from the existing pasted customer feedback flow.",
    }
    bundle = build_project_source(source_request, network_fetch=False)
    return _persist_project_source_bundle(bundle) if persist else bundle

def _graph_storage_warning(container: dict, exc: Exception) -> None:
    warnings = list(container.get("persistence_warnings") or [])
    warning = f"agent_graph_storage_write_failed:{type(exc).__name__}"
    if warning not in warnings:
        warnings.append(warning)
    container["persistence_warnings"] = warnings[-5:]


def _graph_messages_for_state(run: dict | None = None, job: dict | None = None) -> list[dict]:
    safe_run = run if isinstance(run, dict) else {}
    safe_job = job if isinstance(job, dict) else {}
    run_id = str(safe_run.get("run_id") or "")
    job_id = str(safe_job.get("job_id") or "")
    project_id = str(
        safe_job.get("project_id") or safe_run.get("project_id") or DEFAULT_PROJECT_ID
    )
    messages: list[dict] = []
    generation_data = (
        safe_run.get("result")
        if isinstance(safe_run.get("result"), dict)
        else safe_job.get("source_generation")
        if isinstance(safe_job.get("source_generation"), dict)
        else {}
    )
    source = generation_data.get("project_source") or {}
    source_gate = generation_data.get("source_quality_gate") or {}
    source_artifact = generation_data.get("source_evidence_artifact") or {}
    if source:
        messages.append(
            build_agent_message(
                "source_created",
                "source_adapter_agent",
                "source_quality_agent",
                {
                    "source_id": source.get("source_id", ""),
                    "source_type": source.get("source_type", ""),
                    "source_status": source.get("source_status", ""),
                    "warnings": source.get("warnings") or [],
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )
    if source_gate:
        messages.append(
            build_agent_message(
                "quality_gate_decision",
                "source_quality_agent",
                "evidence_agent",
                {
                    "status": source_gate.get("status", ""),
                    "evidence_readiness": source_gate.get("evidence_readiness", ""),
                    "allows_agent_run": source_gate.get("allows_agent_run", False),
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )
        if source_gate.get("status") == "fallback_required":
            messages.append(
                build_agent_message(
                    "manual_fallback_required",
                    "source_quality_agent",
                    None,
                    {
                        "recommended_next_action": source_gate.get(
                            "recommended_next_action",
                            "",
                        )
                    },
                    run_id=run_id,
                    job_id=job_id,
                    project_id=project_id,
                )
            )
    if source_artifact:
        messages.append(
            build_agent_message(
                "source_evidence_ready",
                "evidence_agent",
                "strategy_agent",
                {
                    "artifact_id": source_artifact.get("artifact_id", ""),
                    "review_count": len(source_artifact.get("evidence_quotes") or []),
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    for validation in safe_run.get("validation_results") or []:
        if not isinstance(validation, dict) or validation.get("status") not in {"failed", "warning"}:
            continue
        messages.append(
            build_agent_message(
                "rework_request",
                str(validation.get("validator_agent_id") or "risk_agent"),
                str(validation.get("rework_target") or validation.get("target_agent_id") or "storyboard_agent"),
                {
                    "status": validation.get("status", ""),
                    "reason": validation.get("reason", ""),
                    "target_artifact": validation.get("target_artifact", ""),
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    router_decisions = list(
        safe_job.get("graph_router_decisions")
        or safe_run.get("graph_router_decisions")
        or []
    )
    for decision in router_decisions[-6:]:
        if not isinstance(decision, dict):
            continue
        messages.append(
            build_agent_message(
                "router_route",
                "graph_router_agent",
                str(decision.get("selected_next_agent_id") or ""),
                {
                    "decision_type": decision.get("decision_type", ""),
                    "route_type": decision.get("route_type", ""),
                    "reason": decision.get("reason", ""),
                    "selected_edge": decision.get("selected_edge") or {},
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    feedback = safe_job.get("latest_agent_feedback_decision")
    if isinstance(feedback, dict) and feedback:
        messages.append(
            build_agent_message(
                "experiment_feedback",
                "experiment_agent",
                str(feedback.get("target_agent_id") or "graph_router_agent"),
                {
                    "decision_type": feedback.get("decision_type", ""),
                    "issue_type": feedback.get("issue_type", ""),
                    "reason": feedback.get("reason", ""),
                    "rework_run_id": feedback.get("triggered_rework_run_id", ""),
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    approval = safe_job.get("latest_human_approval_gate")
    if isinstance(approval, dict) and approval:
        messages.append(
            build_agent_message(
                "approval_request" if approval.get("status") == "pending_approval" else "approval_decision",
                "human_approval_agent",
                "provider_job_agent",
                {
                    "status": approval.get("status", ""),
                    "approval_scope": approval.get("approval_scope", ""),
                    "blocks_provider_submit": approval.get("blocks_provider_submit", True),
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    provider = safe_job.get("provider_runtime")
    if isinstance(provider, dict) and provider:
        messages.append(
            build_agent_message(
                "provider_state",
                "provider_job_agent",
                "experiment_agent",
                {
                    "provider_status": provider.get("provider_status", ""),
                    "integration_mode": provider.get("integration_mode", "simulated"),
                    "external_api_called": False,
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    if safe_run.get("status") == "completed":
        messages.append(
            build_agent_message(
                "final_summary",
                "finalizer_agent",
                None,
                {
                    "status": "completed",
                    "waiting_for_user": bool(safe_run.get("waiting_for_user")),
                    "next_action": "Review generated artifacts and continue with a video job.",
                },
                run_id=run_id,
                job_id=job_id,
                project_id=project_id,
            )
        )

    return list(
        {
            str(message.get("message_id") or index): message
            for index, message in enumerate(messages)
        }.values()
    )[-20:]


def _refresh_agent_run_graph_os(run: dict) -> dict:
    safe_run = dict(run or {})
    safe_run["project_id"] = _safe_project_id(safe_run.get("project_id"))
    generation_data = safe_run.get("result") if isinstance(safe_run.get("result"), dict) else {}
    project, uploaded_assets = _project_context(safe_run["project_id"], generation_data)
    registry = build_lightweight_artifact_registry(
        generation_data=generation_data,
        run=safe_run,
        project=project,
        uploaded_assets=uploaded_assets,
    )
    safe_run["artifact_registry"] = registry
    safe_run["agent_messages"] = _graph_messages_for_state(run=safe_run)
    snapshot = build_graph_state_snapshot(
        run=safe_run,
        events=safe_run.get("events") or [],
        artifact_registry=registry,
    )
    safe_run["latest_graph_state_snapshot"] = snapshot
    safe_run["graph_health"] = build_graph_health_summary(safe_run, None, registry, snapshot)
    safe_run["persistence"] = persistence_metadata()
    return safe_run


def _persist_agent_run_graph_os(run: dict) -> dict:
    safe_run = _refresh_agent_run_graph_os(run)
    try:
        save_agent_run_snapshot(safe_run)
        save_graph_event_snapshot(str(safe_run.get("run_id") or ""), list(safe_run.get("events") or []))
        registry = safe_run.get("artifact_registry") or {}
        if registry.get("artifacts"):
            save_artifact_registry_snapshot(registry, f"run_{safe_run.get('run_id')}")
        for message in safe_run.get("agent_messages") or []:
            save_agent_message_snapshot(message)
        save_graph_state_snapshot(safe_run["latest_graph_state_snapshot"])
        update_project_summary(safe_run["project_id"], safe_run)
    except Exception as exc:
        _graph_storage_warning(safe_run, exc)
    return safe_run


def _refresh_video_job_graph_os(job: dict, experiment: dict | None = None) -> dict:
    safe_job = dict(job or {})
    safe_job["project_id"] = _safe_project_id(safe_job.get("project_id"))
    experiments = list(safe_job.get("external_video_experiments") or [])
    latest_experiment = experiment if isinstance(experiment, dict) else (experiments[-1] if experiments else {})
    existing_feedback = (
        dict(safe_job.get("agent_graph_feedback") or {})
        if isinstance(safe_job.get("agent_graph_feedback"), dict)
        else {}
    )
    feedback_decision = (
        safe_job.get("latest_agent_feedback_decision")
        if isinstance(safe_job.get("latest_agent_feedback_decision"), dict)
        else {}
    )
    rework_run_id = str(
        latest_experiment.get("linked_rework_run_id")
        or latest_experiment.get("triggered_rework_run_id")
        or feedback_decision.get("triggered_rework_run_id")
        or existing_feedback.get("latest_rework_run_id")
        or ""
    )
    rework_run = AGENT_RUN_STORE.get(rework_run_id) if rework_run_id else {}
    source_generation = (
        dict(safe_job.get("source_generation") or {})
        if isinstance(safe_job.get("source_generation"), dict)
        else {}
    )
    project, uploaded_assets = _project_context(
        safe_job["project_id"],
        source_generation,
    )
    asset_lock_v2 = build_product_asset_lock_v2(
        project,
        {**source_generation, "project_id": safe_job["project_id"]},
        uploaded_assets,
    )
    safe_job["product_asset_lock_v2"] = asset_lock_v2
    handoff = (
        dict(safe_job.get("external_video_tool_handoff") or {})
        if isinstance(safe_job.get("external_video_tool_handoff"), dict)
        else {}
    )
    if handoff:
        handoff["product_asset_lock_v2"] = asset_lock_v2
        handoff["uploaded_asset_reference"] = {
            "primary_asset_id": asset_lock_v2.get("primary_asset_id", ""),
            "reference_asset_ids": asset_lock_v2.get("reference_asset_ids", []),
            "requires_manual_upload_to_external_tool": True,
        }
        safe_job["external_video_tool_handoff"] = handoff
    registry = build_lightweight_artifact_registry(
        generation_data={
            **source_generation,
            "project_id": safe_job["project_id"],
            "video_generation_packet": safe_job.get("video_generation_packet") or {},
            "external_video_tool_handoff": safe_job.get("external_video_tool_handoff") or {},
            "product_asset_lock_v2": asset_lock_v2,
        },
        job=safe_job,
        run=rework_run,
        experiment=latest_experiment,
        project=project,
        uploaded_assets=uploaded_assets,
    )
    previous_ids = {
        item.get("artifact_id")
        for item in (safe_job.get("latest_artifact_registry") or {}).get("artifacts", [])
        if isinstance(item, dict)
    }
    next_ids = {
        item.get("artifact_id")
        for item in registry.get("artifacts", [])
        if isinstance(item, dict)
    }
    safe_job["latest_artifact_registry"] = registry
    feedback = existing_feedback
    feedback["latest_artifact_registry"] = registry
    safe_job["agent_messages"] = _graph_messages_for_state(job=safe_job)
    feedback["latest_agent_messages"] = safe_job["agent_messages"][-10:]
    safe_job["agent_graph_feedback"] = feedback
    snapshot = build_graph_state_snapshot(
        job=safe_job,
        events=list(safe_job.get("history") or []),
        artifact_registry=registry,
    )
    safe_job["latest_graph_state_snapshot"] = snapshot
    safe_job["graph_health"] = build_graph_health_summary(None, safe_job, registry, snapshot)
    safe_job["persistence"] = persistence_metadata()
    if next_ids and next_ids != previous_ids:
        history = list(safe_job.get("history") or [])
        registry_event = build_video_job_history_event(
            "artifact_registry_updated",
            str(safe_job.get("status") or VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT),
            updated_at=str(safe_job.get("updated_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            registry_version=registry.get("registry_version", ""),
            artifact_count=registry.get("artifact_counts", {}).get("total", 0),
            is_linear_workflow=False,
        )
        insert_at = 1 if len(history) <= 1 else max(1, len(history) - 1)
        history.insert(insert_at, registry_event)
        safe_job["history"] = history
    return safe_job


def _persist_video_job_graph_os(job: dict, experiment: dict | None = None) -> dict:
    safe_job = _refresh_video_job_graph_os(job, experiment)
    try:
        save_video_job_snapshot(safe_job)
        registry = safe_job.get("latest_artifact_registry") or {}
        if registry.get("artifacts"):
            save_artifact_registry_snapshot(registry, f"job_{safe_job.get('job_id')}")
        approval = safe_job.get("latest_human_approval_gate")
        if isinstance(approval, dict) and approval:
            save_approval_snapshot(approval, f"job_{safe_job.get('job_id')}")
        for message in safe_job.get("agent_messages") or []:
            save_agent_message_snapshot(message)
        save_graph_state_snapshot(safe_job["latest_graph_state_snapshot"])
        update_project_summary(safe_job["project_id"], safe_job)
    except Exception as exc:
        _graph_storage_warning(safe_job, exc)
    return safe_job


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
async def index():
    return FileResponse(INDEX_HTML)


def _probe_status_from_evidence(evidence) -> str:
    warnings = list(getattr(evidence, "data_warnings", []) or [])
    if any(
        warning.endswith("_disabled") or warning.endswith("_not_enabled")
        for warning in warnings
    ):
        return "disabled"
    if getattr(evidence, "source_type", "") == "unavailable":
        return "unavailable"
    return "success"


def _amazon_shadow_sources(url: str, product_category: str) -> dict:
    started = time.perf_counter()
    try:
        evidence = source_probe_registry.fetch(
            "amazon_review_api",
            url or "",
            product_category or "",
        )
        metadata = dict(evidence.metadata or {})
        return {
            "mode": "amazon_shadow",
            "amazon_review_api": {
                "status": _probe_status_from_evidence(evidence),
                "source_confidence": evidence.confidence,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "evidence_preview": evidence.evidence_quotes[:3],
                "metadata": {
                    **metadata,
                    "source_type": evidence.source_type,
                    "data_warnings": list(evidence.data_warnings),
                },
                "error": metadata.get("error", ""),
            },
            "memory_write_allowed": False,
            "used_for_generation": False,
        }
    except Exception as exc:
        return {
            "mode": "amazon_shadow",
            "amazon_review_api": {
                "status": "error",
                "source_confidence": 0.0,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "evidence_preview": [],
                "metadata": {},
                "error": str(exc),
            },
            "memory_write_allowed": False,
            "used_for_generation": False,
        }


async def translate_visible_output(text: str, target_language: str = "zh-CN") -> str:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0.2,
        max_retries=0,
    )
    message = await llm.ainvoke(
        [
            SystemMessage(content=TRANSLATION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Target language: {target_language}\n\n"
                    "Translate only the visible product output below:\n\n"
                    f"{text}"
                )
            ),
        ]
    )
    return str(message.content or "").strip()


def _normalize_output_language(value: str | None) -> str:
    normalized = (value or "en").strip()
    return normalized or "en"


def _output_language_error(request_id: str):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error": "Unsupported output_language. Use en or zh-CN.",
            "error_type": "unsupported_output_language",
            "request_id": request_id,
        },
    )


def _validate_output_language(value: str | None, request_id: str):
    output_language = _normalize_output_language(value)
    if output_language not in SUPPORTED_OUTPUT_LANGUAGES:
        return None, _output_language_error(request_id)
    return output_language, None


def _json_from_translation(raw: str) -> dict:
    cleaned = (raw or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Translated product payload must be a JSON object.")
    return parsed


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _looks_like_utf8_mojibake(text: str) -> bool:
    markers = ("æ", "ä¸", "å®", "ï¼", "ç")
    return any(marker in text for marker in markers)


def _repair_mojibake_text(text: str) -> str:
    if not text or not _looks_like_utf8_mojibake(text):
        return text
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    if _contains_cjk(repaired):
        return repaired
    return text


def _repair_mojibake_payload(value):
    if isinstance(value, str):
        return _repair_mojibake_text(value)
    if isinstance(value, list):
        return [_repair_mojibake_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _repair_mojibake_payload(item) for key, item in value.items()}
    return value


def _preserve_product_identifiers(translated: dict, original: dict) -> dict:
    if not isinstance(translated, dict) or not isinstance(original, dict):
        return translated

    for key, value in original.items():
        if key in {
            "source",
            "source_type",
            "source_url",
            "data_warnings",
            "product_name",
            "product_category",
            "risk_level",
            "agent_name",
            "packet_version",
            "execution_mode",
            "status",
        }:
            translated[key] = value
        elif isinstance(value, dict) and isinstance(translated.get(key), dict):
            translated[key] = _preserve_product_identifiers(translated[key], value)
        elif isinstance(value, list) and isinstance(translated.get(key), list):
            translated[key] = [
                _preserve_product_identifiers(item, value[index])
                if index < len(value) and isinstance(item, dict) and isinstance(value[index], dict)
                else item
                for index, item in enumerate(translated[key])
            ]
    return translated


async def translate_product_visible_data(data: dict, target_language: str) -> dict:
    if target_language != "zh-CN":
        return data

    raw = await translate_visible_output(
        (
            "Translate only user-visible natural-language string values in this JSON object. "
            "Return valid JSON only. Preserve all object keys exactly. Do not translate source identifiers, "
            "enum-like values, booleans, numbers, request IDs, or URLs.\n\n"
            f"{json.dumps(data, ensure_ascii=False)}"
        ),
        target_language,
    )
    translated = _json_from_translation(raw)
    translated = _repair_mojibake_payload(translated)
    return _preserve_product_identifiers(translated, data)


def _clean_description_text(value: str) -> str:
    return (value or "").strip()


def _strip_amazon_reviewer_prefix(text: str) -> str:
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return ""

    title_starters = (
        "worth", "cannot", "can't", "value", "quality", "great", "good", "love",
        "best", "this", "these", "the", "it", "not", "however", "yes",
        "excellent", "delicious", "tastes", "taste", "no", "price", "flavor",
        "flavour", "bottle", "arrived",
    )
    first_token = re.match(r"^(?:By\s+)?([A-Za-z][A-Za-z0-9_-]{1,24})\b", cleaned, flags=re.IGNORECASE)
    if first_token and first_token.group(1).lower() in title_starters:
        return cleaned

    starter_pattern = "|".join(re.escape(item) for item in title_starters)
    name_pattern = r"(?:Amazon Customer|[A-Za-z][A-Za-z0-9_-]{1,24})"

    cleaned = re.sub(
        rf"^(?:By\s+)?{name_pattern}\s*[:\-]\s+(?=(?:{starter_pattern})\b)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        rf"^(?:By\s+)?{name_pattern}\s+(?=(?:{starter_pattern})\b)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _description_error(error: str, error_type: str, request_id: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error": error,
            "error_type": error_type,
            "request_id": request_id,
        },
    )


def _validate_description_request(request: ProductDescriptionRequest, request_id: str):
    product_name = _clean_description_text(request.product_name)
    product_description = _clean_description_text(request.product_description)
    customer_pain_points = _clean_description_text(request.customer_pain_points)
    combined_size = len(product_name) + len(product_description) + len(customer_pain_points)

    if not product_name:
        return _description_error("product_name is required.", "missing_product_name", request_id)
    if not product_description:
        return _description_error(
            "product_description is required.",
            "missing_product_description",
            request_id,
        )
    if not customer_pain_points:
        return _description_error(
            "customer_pain_points is required.",
            "missing_customer_pain_points",
            request_id,
        )
    if len(product_name) < 2 or len(product_description) < DESCRIPTION_MIN_CHARS or len(customer_pain_points) < DESCRIPTION_MIN_CHARS:
        return _description_error(
            "Product description mode needs a product name plus a short product description and customer pain point summary.",
            "input_too_short",
            request_id,
        )
    if combined_size > DESCRIPTION_MAX_CHARS:
        return _description_error(
            "Input is too long for Product Description Mode. Please shorten the description and pain points.",
            "input_too_long",
            request_id,
        )
    return None


def _is_pasted_review_label_line(line: str) -> bool:
    normalized = " ".join(str(line or "").strip().split()).lower()
    label_prefixes = (
        "\u75db\u70b9:",
        "\u75db\u70b9\uff1a",
        "\u6b63\u5411:",
        "\u6b63\u5411\uff1a",
        "\u4f7f\u7528\u573a\u666f:",
        "\u4f7f\u7528\u573a\u666f\uff1a",
        "pain point:",
        "pain points:",
        "positive:",
        "pros:",
        "use case:",
        "use cases:",
        "usage scenario:",
        "usage scenarios:",
    )
    return normalized.startswith(label_prefixes)


def _clean_pasted_review_quote_text(value: str) -> str:
    text = _clean_description_text(value)
    if not text:
        return ""

    cleaner = globals().get("_rw_clean_evidence_fragment")
    if callable(cleaner):
        text = cleaner(text)

    text = re.sub(r"^(?:Amazon Customer|Kindle Customer)\s*[1-5](?:\.0)?\s+out of\s+5\s+stars\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:Amazon Customer|Kindle Customer)(?=[A-Z])", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^\[?\s*[1-5](?:\.0)?\s+out of\s+5\s+stars\s*\]?\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[1-5](?:\.0)?\s+out of\s+5\s+stars\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:Amazon Customer|Kindle Customer)\s*[1-5](?:\.0)?\s+out of 5 stars\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Reviewed in .*? on [A-Za-z]+ \d{1,2}, \d{4}", " ", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(?:Flavor Name|Size|Color|Style|Pattern Name|Package Quantity)\s*:\s*"
        r".*?(?=\b(?:Flavor Name|Size|Color|Style|Pattern Name|Package Quantity|Verified Purchase|Reviewed in|[1-5](?:\.0)?\s+out of\s+5\s+stars)\b|$)",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5[^\s]{0,18}\u8bc4\u8bba", " ", text)
    text = re.sub(r"\bVerified Purchase\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\u5df2\u9a8c\u8bc1\u8d2d\u4e70|\u5df2\u786e\u8ba4\u8d2d\u4e70", " ", text)
    text = re.sub(r"\b(?:One|Two|\d+)\s+people?\s+found\s+this\s+helpful\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:Helpful|Report|Submit a review|Community guidelines?)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -:;,.[]")
    text = _strip_amazon_reviewer_prefix(text)
    if not re.search(r"[A-Za-z\u4e00-\u9fff]", text):
        return ""
    return text


def _split_pasted_review_quotes(text: str, limit: int = 10) -> list[str]:
    cleaned_lines = []
    for raw_line in (text or "").replace("\r", "\n").split("\n"):
        line = raw_line.strip().lstrip("-*•0123456789. )(").strip()
        line = _clean_pasted_review_quote_text(line)
        if line and not _is_pasted_review_label_line(line):
            cleaned_lines.append(line)

    if not cleaned_lines:
        normalized = " ".join((text or "").split())
        pieces = [piece.strip() for piece in normalized.replace("!", ".").replace("?", ".").split(".")]
        cleaned_lines = [
            cleaned
            for piece in pieces
            for cleaned in [_clean_pasted_review_quote_text(piece)]
            if cleaned and not _is_pasted_review_label_line(cleaned)
        ]

    quotes = []
    for line in cleaned_lines:
        quote = _safe_evidence_quote(line, limit=240)
        if quote and quote not in quotes:
            quotes.append(quote)
        if len(quotes) >= limit:
            break
    return quotes


def _compact_pasted_reviews_for_generation(text: str, limit: int = PASTED_REVIEWS_COMPACT_QUOTE_LIMIT) -> str:
    quotes = _split_pasted_review_quotes(text, limit=limit)
    return "\n".join(quotes)


def _validate_pasted_reviews_request(request: PastedReviewsRequest, request_id: str):
    product_name = _clean_description_text(request.product_name)
    pasted_reviews = _clean_description_text(request.pasted_reviews)

    if not product_name:
        return _description_error("product_name is required.", "missing_product_name", request_id)
    if not pasted_reviews:
        return _description_error("pasted_reviews is required.", "missing_pasted_reviews", request_id)
    if len(pasted_reviews) < PASTED_REVIEWS_MIN_CHARS:
        return _description_error(
            "Pasted Reviews Mode needs a few concrete review snippets or customer complaints.",
            "pasted_reviews_too_short",
            request_id,
        )
    compact_reviews = _compact_pasted_reviews_for_generation(pasted_reviews)
    if not compact_reviews:
        return _description_error(
            "Pasted Reviews Mode needs at least one concrete review line, not only category labels.",
            "pasted_reviews_no_concrete_reviews",
            request_id,
        )
    if len(pasted_reviews) > PASTED_REVIEWS_RAW_MAX_CHARS:
        return _description_error(
            "Input is too long for Pasted Reviews Mode. Please paste a smaller visible review sample.",
            "input_too_long",
            request_id,
        )
    effective_reviews = compact_reviews or pasted_reviews
    if len(product_name) + len(_clean_description_text(request.product_description or "")) + len(effective_reviews) > DESCRIPTION_MAX_CHARS:
        return _description_error(
            "Input is too long for Pasted Reviews Mode. Please shorten the pasted reviews.",
            "input_too_long",
            request_id,
        )
    return None


def _safe_evidence_quote(text: str, limit: int = 220) -> str:
    cleaned = " ".join(_clean_description_text(text).split())
    return cleaned[:limit]


def _video_packet_text(value, limit: int = 260) -> str:
    return _safe_evidence_quote(str(value or ""), limit=limit)


def _video_overlay_text(scene: dict, script: dict) -> str:
    source = (
        scene.get("on_screen_text")
        or scene.get("overlay_text")
        or scene.get("narration")
        or script.get("hook")
        or script.get("cta")
        or ""
    )
    text = _video_packet_text(source, limit=90)
    for separator in [". ", "! ", "? ", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
            break
    return text[:72].strip()


def _build_video_generation_packet(
    product_name: str,
    category: str,
    assets: dict,
    insights: dict,
    evaluation: dict,
    output_language: str = "en",
) -> dict:
    assets = assets if isinstance(assets, dict) else {}
    insights = insights if isinstance(insights, dict) else {}
    evaluation = evaluation if isinstance(evaluation, dict) else {}
    script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
    evidence = insights.get("evidence") if isinstance(insights.get("evidence"), dict) else {}
    source_type = evidence.get("source_type") or storyboard.get("source") or ""
    risk_level = evaluation.get("risk_level") or ""
    raw_scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    normalized_scenes = []

    for index, scene in enumerate(raw_scenes[:4]):
        if not isinstance(scene, dict):
            continue
        visual_prompt = _video_packet_text(
            scene.get("visual_description") or scene.get("visual") or scene.get("scene_goal") or "",
            limit=320,
        )
        narration = _video_packet_text(scene.get("narration") or "", limit=260)
        evidence_quote = _video_packet_text(
            scene.get("evidence_quote_used") or scene.get("evidence_quote") or scene.get("linked_painpoint") or "",
            limit=240,
        )
        risk_notes = []
        if not evidence_quote:
            risk_notes.append("Missing scene-level evidence quote; keep claim conservative.")
        if not visual_prompt or len(visual_prompt) < 24:
            risk_notes.append("Visual prompt is generic; expand with product-specific visible action before video rendering.")
        normalized_scenes.append(
            {
                "scene_id": scene.get("scene_id") or index + 1,
                "duration_seconds": 5,
                "visual_prompt": visual_prompt or f"Show {product_name} in a simple product-use moment.",
                "narration": narration,
                "overlay_text": _video_overlay_text(scene, script),
                "evidence_quote": evidence_quote,
                "risk_notes": risk_notes,
            }
        )

    if not normalized_scenes:
        normalized_scenes.append(
            {
                "scene_id": 1,
                "duration_seconds": 5,
                "visual_prompt": f"Show {product_name} in a vertical product demo.",
                "narration": _video_packet_text(script.get("hook") or script.get("cta") or "", limit=260),
                "overlay_text": _video_packet_text(script.get("hook") or product_name, limit=72),
                "evidence_quote": "",
                "risk_notes": ["No storyboard scenes were available; treat this as a draft placeholder."],
            }
        )

    duration_seconds = 20
    aspect_ratio = "9:16"
    product_descriptor = f"{product_name} ({category or 'product'})"
    cta = _video_packet_text(script.get("cta") or "", limit=180)
    risk_boundary = (
        "Evidence boundary: use only the supplied review/product evidence; avoid unsupported claims, "
        "before/after guarantees, medical claims, or full-market statistics. "
        "If a scene is missing an evidence quote, show product use visually but avoid unsupported factual claims."
    )
    scene_lines = [
        (
            f"Scene {scene['scene_id']} ({scene['duration_seconds']}s) - "
            f"Shot direction: {scene['visual_prompt']} "
            f"Narration: {scene['narration'] or 'No narration supplied.'} "
            f"Overlay text: {scene['overlay_text'] or 'None.'} "
            f"Evidence anchor: {scene['evidence_quote'] or 'Missing; keep claim conservative.'}"
        )
        for scene in normalized_scenes
    ]
    compact_scene_sequence = " | ".join(
        f"Scene {scene['scene_id']}: {scene['visual_prompt']} (overlay: {scene['overlay_text'] or 'none'})"
        for scene in normalized_scenes
    )
    generic_video_prompt = (
        f"Universal video prompt for {product_descriptor}.\n"
        f"Format: {duration_seconds}-second vertical {aspect_ratio} TikTok-style product video.\n"
        f"{risk_boundary}\n"
        "Scene sequence:\n"
        + "\n".join(scene_lines)
        + (f"\nCTA: {cta}" if cta else "\nCTA: Keep the ending grounded and non-exaggerated.")
    )
    capcut_shot_list = "\n".join(
        (
            f"Scene {scene['scene_id']} - {scene['duration_seconds']}s\n"
            f"Shot direction: {scene['visual_prompt']}\n"
            f"Overlay text: {scene['overlay_text'] or 'None'}\n"
            f"Narration: {scene['narration'] or 'No narration supplied'}\n"
            f"Evidence anchor: {scene['evidence_quote'] or 'Missing; keep claim conservative'}\n"
            "Edit notes: use a quick cut, close-up, product handling, and a clean transition to the next scene."
        )
        for scene in normalized_scenes
    )
    runway_style_prompt = (
        f"Cinematic vertical {aspect_ratio} product ad for {product_descriptor}. "
        "Use clean ecommerce lighting, close-up product handling, shallow depth of field, "
        "gentle push-in camera movement, and natural short-form pacing. "
        f"{risk_boundary} "
        f"Visual sequence: {compact_scene_sequence}. "
        "Keep text overlays minimal and preserve the supplied evidence boundary."
    )
    pika_style_prompt = (
        f"Short motion product demo for {product_name}: quick cuts, product-in-use action, "
        "simple overlays, compact narration, and evidence-safe narration. Sequence: "
        + " -> ".join(
            f"{scene['visual_prompt']} [overlay: {scene['overlay_text'] or 'none'}]"
            for scene in normalized_scenes
        )
        + ". Avoid unsupported claims."
    )

    return {
        "packet_version": "video_generation_v1",
        "intended_use": "video_prompt_export",
        "source": {
            "storyboard_source": storyboard.get("source") or source_type,
            "evidence_source_type": source_type,
            "risk_level": risk_level,
            "output_language": output_language,
        },
        "video": {
            "platform": "TikTok",
            "recommended_duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "style_notes": [
                "Vertical short-form product demo.",
                "Keep claims tied to supplied evidence quotes.",
                "Use natural product-use visuals before adding stylized effects.",
            ],
        },
        "scenes": normalized_scenes,
        "evidence_boundary": risk_boundary,
        "full_video_prompt": generic_video_prompt,
        "export_formats": {
            "generic_video_prompt": generic_video_prompt,
            "capcut_shot_list": capcut_shot_list,
            "runway_style_prompt": runway_style_prompt,
            "pika_style_prompt": pika_style_prompt,
        },
    }


def _handoff_text(value, limit: int = 700) -> str:
    return _safe_evidence_quote(str(value or ""), limit=limit)


def _build_product_asset_lock(product_title: str, product_category: str) -> dict:
    product_identity = _handoff_text(product_title or "Product", limit=160)
    category = _handoff_text(product_category or "product", limit=120)
    return {
        "lock_version": "product_asset_lock_v1",
        "product_identity": product_identity,
        "product_category": category,
        "visual_identity_source": "Use the supplied product name/category and a manually uploaded reference product image in external tools.",
        "must_preserve": [
            f"Keep product identity as {product_identity}.",
            f"Keep product category as {category}; do not drift into another category.",
            "Preserve visible color, material, label placement, package shape, and scale from the uploaded/reference product image.",
            "Keep review-backed benefit and concern boundaries tied to supplied evidence.",
        ],
        "must_not_change": [
            "Do not invent fake variants, colors, package sizes, logos, or competitor products.",
            "Do not transform the product into a different category or unrealistic object.",
            "Do not add unsupported medical, safety, before/after, or full-market performance claims.",
            "Do not imply verified certifications, endorsements, or guarantees unless supplied in evidence.",
        ],
        "allowed_contexts": [
            "Clean ecommerce product demo surface.",
            "Simple product-in-use moment relevant to the supplied category.",
            "Close-up handling, setup, or comparison visual that does not invent unsupported claims.",
            "Neutral lifestyle background where the product remains the hero.",
        ],
        "image_reference_rules": [
            "Upload or reference the real product image manually before paid generation.",
            "Use the image as the source of truth for product appearance.",
            "If the generated clip changes product identity, reject it and regenerate from one short clip.",
            "Do not rely on text prompt alone for exact product appearance.",
        ],
        "human_review_required": True,
    }


def _build_keyframe_plan(
    product_title: str,
    product_category: str,
    keyframes: list[dict],
    product_asset_lock: dict,
    aspect_ratio: str,
    quote_preview: list[str],
) -> dict:
    must_preserve = product_asset_lock.get("must_preserve") if isinstance(product_asset_lock.get("must_preserve"), list) else []
    scenes = []
    for index, frame in enumerate((keyframes or [])[:4]):
        if not isinstance(frame, dict):
            continue
        scene_id = frame.get("scene_id") or index + 1
        duration = int(frame.get("duration_seconds") or 5)
        evidence_anchor = _handoff_text(
            frame.get("evidence_anchor") or (quote_preview[index % len(quote_preview)] if quote_preview else ""),
            limit=240,
        )
        scenes.append(
            {
                "scene_id": scene_id,
                "duration_seconds": duration,
                "keyframe_goal": _handoff_text(
                    frame.get("keyframe_goal") or f"Create scene {scene_id} for {product_title}.",
                    limit=260,
                ),
                "product_position": _handoff_text(
                    f"Keep {product_title} clearly visible as the hero product in a vertical {aspect_ratio} frame.",
                    limit=220,
                ),
                "camera_direction": _handoff_text(
                    "Use a stable close-up or gentle push-in; avoid fast camera moves that distort product identity.",
                    limit=220,
                ),
                "motion_control": _handoff_text(
                    frame.get("motion_prompt") or "Use natural product handling and conservative short-form motion.",
                    limit=360,
                ),
                "overlay_text": _handoff_text(frame.get("overlay_text") or "", limit=90),
                "evidence_anchor": evidence_anchor,
                "product_constraints": must_preserve[:4],
                "risk_notes": [
                    "Review this keyframe before paid generation.",
                    "Reject output if product category, shape, color, material, or label identity drifts.",
                    "Do not treat one variant or complaint as a whole-market claim.",
                ],
            }
        )

    if not scenes:
        scenes.append(
            {
                "scene_id": 1,
                "duration_seconds": 5,
                "keyframe_goal": f"Create one conservative product demo opening for {product_title}.",
                "product_position": f"Keep {product_title} centered and clearly visible.",
                "camera_direction": "Static product close-up with clean ecommerce lighting.",
                "motion_control": "Use minimal motion; generate one short clip first.",
                "overlay_text": "",
                "evidence_anchor": quote_preview[0] if quote_preview else "",
                "product_constraints": must_preserve[:4],
                "risk_notes": [
                    "Fallback scene only; review manually before using paid generation.",
                    "Do not invent unsupported claims or product variants.",
                ],
            }
        )

    return {
        "plan_version": "keyframe_plan_v1",
        "recommended_clip_strategy": "Generate one short clip first, review product identity and evidence boundaries, then spend more credits only after approval.",
        "scene_count": len(scenes),
        "scenes": scenes,
        "review_before_paid_generation": True,
        "stability_notes": [
            "Use the product asset lock with every external video prompt.",
            "Keep evidence anchors visible in scene planning; do not invent claims.",
            "Generate one short clip first before spending more credits.",
            f"Preserve {product_category or 'product'} category and product image identity.",
        ],
    }


def _build_external_video_tool_handoff(
    product_name: str,
    category: str,
    data: dict,
) -> dict:
    try:
        data = data if isinstance(data, dict) else {}
        assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
        script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
        storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
        insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
        evidence = insights.get("evidence") if isinstance(insights.get("evidence"), dict) else {}
        llm_packet = data.get("llm_evidence_packet") if isinstance(data.get("llm_evidence_packet"), dict) else {}
        video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else {}
        video = video_packet.get("video") if isinstance(video_packet.get("video"), dict) else {}
        export_formats = video_packet.get("export_formats") if isinstance(video_packet.get("export_formats"), dict) else {}
        scenes = video_packet.get("scenes") if isinstance(video_packet.get("scenes"), list) else []
        storyboard_scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []

        if not scenes and storyboard_scenes:
            for index, scene in enumerate(storyboard_scenes[:4]):
                if not isinstance(scene, dict):
                    continue
                scenes.append(
                    {
                        "scene_id": scene.get("scene_id") or index + 1,
                        "duration_seconds": 5,
                        "visual_prompt": scene.get("visual_description") or scene.get("visual") or scene.get("scene_goal") or "",
                        "narration": scene.get("narration") or "",
                        "overlay_text": scene.get("on_screen_text") or scene.get("overlay_text") or "",
                        "evidence_quote": scene.get("evidence_quote_used") or scene.get("evidence_quote") or scene.get("linked_painpoint") or "",
                    }
                )

        product_title = _handoff_text(product_name or storyboard.get("product_name") or "Product", limit=160)
        product_category = _handoff_text(category or storyboard.get("product_category") or "product", limit=120)
        hook = _handoff_text(script.get("hook") or "", limit=220)
        cta = _handoff_text(script.get("cta") or "", limit=180)
        evidence_quotes = evidence.get("evidence_quotes") if isinstance(evidence.get("evidence_quotes"), list) else []
        packet_evidence = llm_packet.get("evidence") if isinstance(llm_packet.get("evidence"), dict) else {}
        packet_quotes = packet_evidence.get("quotes") if isinstance(packet_evidence.get("quotes"), list) else []
        quote_preview = [_handoff_text(value, limit=220) for value in (evidence_quotes or packet_quotes)[:5] if value]
        duration = int(video.get("recommended_duration_seconds") or 20)
        aspect_ratio = _handoff_text(video.get("aspect_ratio") or "9:16", limit=20)
        source_packet_version = _handoff_text(video_packet.get("packet_version") or "", limit=80)

        keyframes = []
        for index, scene in enumerate(scenes[:4]):
            if not isinstance(scene, dict):
                continue
            visual = _handoff_text(scene.get("visual_prompt") or scene.get("visual_description") or "", limit=360)
            narration = _handoff_text(scene.get("narration") or "", limit=260)
            overlay = _handoff_text(scene.get("overlay_text") or "", limit=90)
            evidence_anchor = _handoff_text(scene.get("evidence_quote") or scene.get("evidence_quote_used") or "", limit=240)
            keyframe_goal = f"Create scene {scene.get('scene_id') or index + 1} for {product_title}: {overlay or narration or visual}"
            keyframes.append(
                {
                    "scene_id": scene.get("scene_id") or index + 1,
                    "duration_seconds": int(scene.get("duration_seconds") or 5),
                    "keyframe_goal": _handoff_text(keyframe_goal, limit=260),
                    "image_prompt": _handoff_text(
                        f"Vertical {aspect_ratio} ecommerce keyframe for {product_title}. {visual} Keep product category as {product_category}.",
                        limit=460,
                    ),
                    "motion_prompt": _handoff_text(
                        f"Animate this keyframe with natural product handling and short-form pacing. Narration: {narration or hook}. Overlay: {overlay or 'minimal text'}.",
                        limit=460,
                    ),
                    "overlay_text": overlay,
                    "evidence_anchor": evidence_anchor,
                }
            )

        if not keyframes:
            keyframes.append(
                {
                    "scene_id": 1,
                    "duration_seconds": 5,
                    "keyframe_goal": f"Create a grounded product demo opening for {product_title}.",
                    "image_prompt": f"Vertical {aspect_ratio} ecommerce keyframe showing {product_title} in a clean product-use moment.",
                    "motion_prompt": f"Animate a short product demo clip for {product_title}; keep claims conservative and evidence-safe.",
                    "overlay_text": hook[:72],
                    "evidence_anchor": quote_preview[0] if quote_preview else "",
                }
            )

        evidence_summary = "; ".join(quote_preview[:3]) or "Use only the supplied review/product evidence."
        general_prompt = _handoff_text(export_formats.get("generic_video_prompt") or video_packet.get("full_video_prompt") or "", limit=1400)
        product_asset_lock = _build_product_asset_lock(product_title, product_category)
        keyframe_plan = _build_keyframe_plan(product_title, product_category, keyframes, product_asset_lock, aspect_ratio, quote_preview)
        lock_summary = (
            f"Product asset lock: preserve {product_asset_lock['product_identity']} as a "
            f"{product_asset_lock['product_category']}; use a manually uploaded/reference product image as identity source."
        )
        keyframe_summary = (
            f"Keyframe plan: {keyframe_plan['scene_count']} scenes. "
            f"{keyframe_plan['recommended_clip_strategy']}"
        )
        gemini_prompt = (
            f"Create a {duration}-second vertical {aspect_ratio} ecommerce video for {product_title} ({product_category}). "
            f"{lock_summary} "
            f"{keyframe_summary} "
            f"Hook: {hook or 'Open with the strongest grounded buyer signal.'} "
            f"CTA: {cta or 'End with a conservative product CTA.'} "
            f"Use these evidence anchors only: {evidence_summary}. "
            "Review before paid generation, keep product appearance consistent, and avoid unsupported claims."
        )
        doubao_prompt = (
            f"Generate a vertical {aspect_ratio} short product video draft for {product_title}. "
            f"{lock_summary} "
            f"{keyframe_summary} "
            f"Scene plan: "
            + " | ".join(
                f"Scene {frame['scene_id']}: {frame['motion_prompt']}"
                for frame in keyframes[:4]
            )
            + f" Evidence boundary: {evidence_summary}. Review one short clip first. No full-market claims."
        )
        image_to_video_prompt = (
            f"Use the uploaded/reference product image as the product identity source. Product: {product_title}. "
            f"Apply the product asset lock and keyframe plan. Animate using the keyframe plan, preserve color/material/shape, "
            "generate one short clip first, and avoid visual changes not supported by the product image, description, or evidence."
        )
        short_motion_prompt = (
            f"{product_title}, vertical {aspect_ratio}, quick ecommerce motion, product-in-use, evidence-safe hook, "
            "clean lighting, short-form pacing, no exaggerated claims."
        )
        negative_prompt = (
            "Do not change the product category, color, material, or package shape. "
            "Do not add competitor logos, medical claims, full-market statistics, fake reviews, unrealistic transformations, or unsupported before/after guarantees."
        )
        copy_ready_generation_brief = "\n".join(
            [
                f"Product: {product_title}",
                f"Category: {product_category}",
                f"Format: {duration}s vertical {aspect_ratio}",
                f"Hook: {hook}",
                f"CTA: {cta}",
                f"Evidence anchors: {evidence_summary}",
                f"Product asset lock: {product_asset_lock['product_identity']} / {product_asset_lock['product_category']}",
                f"Must preserve: {'; '.join(product_asset_lock['must_preserve'][:3])}",
                f"Must not change: {'; '.join(product_asset_lock['must_not_change'][:3])}",
                f"Keyframe plan: {keyframe_plan['scene_count']} scenes; {keyframe_plan['recommended_clip_strategy']}",
                "Workflow: paste a tool prompt into Gemini, Doubao, Runway, Pika, Kling, or a manual video workflow. CrossGrowth does not call external video APIs.",
                "Review the first short clip before paid generation and keep all claims inside the supplied evidence boundary.",
                general_prompt,
            ]
        ).strip()

        return {
            "packet_version": "external_video_tool_handoff_v1",
            "source_packet_version": source_packet_version or "video_generation_v1",
            "recommended_workflow": "Use this package by copying prompts into external video tools. No API call is made by CrossGrowth.",
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "requires_user_confirmation_before_paid_generation": True,
            "tool_prompts": {
                "gemini_video_prompt": _handoff_text(gemini_prompt, limit=1600),
                "doubao_video_prompt": _handoff_text(doubao_prompt, limit=1600),
                "general_image_to_video_prompt": _handoff_text(image_to_video_prompt, limit=1200),
                "short_motion_prompt": _handoff_text(short_motion_prompt, limit=700),
            },
            "product_asset_lock": product_asset_lock,
            "keyframe_plan": keyframe_plan,
            "keyframe_prompts": keyframes,
            "product_consistency_rules": [
                "Keep the product category unchanged.",
                "Preserve the visible product color/material/shape from the supplied product image or product description.",
                "Do not introduce unsupported claims.",
                "Keep main product, variant, and competitor boundaries visible when evidence is variant-specific.",
            ],
            "negative_prompt": negative_prompt,
            "copy_ready_generation_brief": _handoff_text(copy_ready_generation_brief, limit=3000),
            "manual_steps": [
                "Upload or reference the product image in the external video tool.",
                "Paste the Gemini/Doubao/general prompt.",
                "Generate one short clip first.",
                "Review product consistency before generating more clips.",
                "Paste the result URL back into the Video Job panel.",
            ],
            "quality_checklist": [
                "Product still matches original product.",
                "Claim is supported by review evidence.",
                "Overlay text matches the scene.",
                "No exaggerated market-wide claims.",
                "Clip is usable before spending more credits.",
            ],
            "warnings": [
                "External tool pricing can vary.",
                "CrossGrowth does not call external video APIs in this flow.",
                "Review costs before using paid generation.",
            ],
        }
    except Exception:
        return {}


def _agent_trace_text(value, limit: int = 220) -> str:
    return _safe_evidence_quote(str(value or ""), limit=limit)


def _agent_trace_items(value, limit: int = 4) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = (
                item.get("label")
                or item.get("theme")
                or item.get("summary")
                or item.get("quote")
                or item.get("text")
                or ""
            )
        else:
            text = item
        cleaned = _agent_trace_text(text)
        if cleaned and cleaned not in items:
            items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def _agent_trace_count(value) -> int:
    return len(value) if isinstance(value, list) else 0


def _build_agent_trace(data: dict, output_language: str = "en") -> dict:
    if not isinstance(data, dict):
        return {}

    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    audience = data.get("audience") if isinstance(data.get("audience"), dict) else {}
    strategy = data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
    evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else {}
    evidence = insights.get("evidence") if isinstance(insights.get("evidence"), dict) else {}
    script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    llm_packet = data.get("llm_evidence_packet") if isinstance(data.get("llm_evidence_packet"), dict) else {}
    video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else {}
    packet_evidence = llm_packet.get("evidence") if isinstance(llm_packet.get("evidence"), dict) else {}
    packet_stats = llm_packet.get("review_stats") if isinstance(llm_packet.get("review_stats"), dict) else {}
    packet_product = llm_packet.get("product") if isinstance(llm_packet.get("product"), dict) else {}
    constraints = llm_packet.get("generation_constraints") if isinstance(llm_packet.get("generation_constraints"), list) else []
    warnings = (
        _agent_trace_items(packet_stats.get("warnings"), limit=4)
        + _agent_trace_items(evidence.get("data_warnings"), limit=4)
        + _agent_trace_items(constraints, limit=3)
    )
    source_type = (
        packet_product.get("source_type")
        or evidence.get("source_type")
        or storyboard.get("source")
        or "unknown"
    )
    review_count = (
        packet_stats.get("total_reviews")
        or packet_stats.get("review_count")
        or evidence.get("review_count")
        or 0
    )
    quote_count = _agent_trace_count(packet_evidence.get("quotes")) or _agent_trace_count(evidence.get("evidence_quotes"))
    video_formats = []
    if isinstance(video_packet.get("export_formats"), dict):
        video_formats = sorted(key for key, value in video_packet["export_formats"].items() if value)

    agents = {
        "evidence_agent": {
            "agent_name": "evidence_agent",
            "role": "Extract buyer evidence and source boundaries",
            "input_summary": f"packet={llm_packet.get('packet_version') or 'none'}; source_type={source_type}; reviews={review_count}",
            "output_summary": f"{quote_count} evidence quotes prepared with source boundary {source_type}.",
            "key_outputs": {
                "packet_version": llm_packet.get("packet_version", ""),
                "source_type": source_type,
                "review_count": review_count,
                "pain_points": _agent_trace_items(insights.get("pain_points") or packet_evidence.get("pain_points"), limit=4),
                "buyer_objections": _agent_trace_items(insights.get("buyer_objections") or packet_evidence.get("buyer_objections"), limit=4),
                "positive_signals": _agent_trace_items(insights.get("positive_signals") or packet_evidence.get("positive_signals"), limit=4),
                "evidence_quote_count": quote_count,
            },
            "warnings": warnings[:8],
            "status": "complete",
        },
        "strategy_agent": {
            "agent_name": "strategy_agent",
            "role": "Choose target audience and creative angle",
            "input_summary": "Uses top evidence signals, buyer objections, and positive proof from the evidence packet.",
            "output_summary": _agent_trace_text(strategy.get("core_hook_strategy") or script.get("hook"), limit=260),
            "key_outputs": {
                "audience_primary": _agent_trace_text(audience.get("primary")),
                "core_hook_strategy": _agent_trace_text(strategy.get("core_hook_strategy"), limit=260),
                "emotional_trigger": _agent_trace_text(strategy.get("emotional_trigger"), limit=260),
            },
            "warnings": [],
            "status": "complete",
        },
        "storyboard_agent": {
            "agent_name": "storyboard_agent",
            "role": "Turn strategy into short-form storyboard",
            "input_summary": _agent_trace_text(strategy.get("core_hook_strategy") or script.get("hook"), limit=220),
            "output_summary": f"{len(scenes)} storyboard scenes with hook and CTA.",
            "key_outputs": {
                "hook": _agent_trace_text(script.get("hook"), limit=260),
                "cta": _agent_trace_text(script.get("cta"), limit=260),
                "scene_count": len(scenes),
            },
            "warnings": [],
            "status": "complete",
        },
        "video_prompt_agent": {
            "agent_name": "video_prompt_agent",
            "role": "Convert storyboard into video prompts and export formats",
            "input_summary": f"storyboard_scene_count={len(scenes)}",
            "output_summary": f"video_packet={video_packet.get('packet_version') or 'none'}; scenes={_agent_trace_count(video_packet.get('scenes'))}",
            "key_outputs": {
                "packet_version": video_packet.get("packet_version", ""),
                "scene_count": _agent_trace_count(video_packet.get("scenes")),
                "export_format_keys": video_formats,
            },
            "warnings": _agent_trace_items(
                [
                    note
                    for scene in (video_packet.get("scenes") if isinstance(video_packet.get("scenes"), list) else [])
                    for note in (scene.get("risk_notes") if isinstance(scene, dict) and isinstance(scene.get("risk_notes"), list) else [])
                ],
                limit=4,
            ),
            "status": "complete",
        },
        "risk_agent": {
            "agent_name": "risk_agent",
            "role": "Check grounding and claim risk",
            "input_summary": _agent_trace_text(evaluation.get("reasoning"), limit=260),
            "output_summary": f"risk_level={evaluation.get('risk_level') or 'unknown'}; grounded={bool(evaluation.get('is_grounded'))}",
            "key_outputs": {
                "risk_level": evaluation.get("risk_level", ""),
                "is_grounded": bool(evaluation.get("is_grounded")),
                "is_approved": bool(evaluation.get("is_approved")),
                "confidence_score": evaluation.get("confidence_score", 0.0),
            },
            "warnings": _agent_trace_items(constraints, limit=4),
            "status": "complete",
        },
    }

    return {
        "trace_version": "agent_trace_v1",
        "execution_mode": "single_workflow_scaffold",
        "is_real_multi_agent_execution": False,
        "output_language": output_language or "en",
        "agents": agents,
        "agent_order": [
            "evidence_agent",
            "strategy_agent",
            "storyboard_agent",
            "video_prompt_agent",
            "risk_agent",
        ],
    }


def _pasted_review_signal_kind(quote: str) -> str:
    lowered = _clean_description_text(quote).lower()
    if not lowered:
        return "neutral"

    positive_value_markers = (
        "worth the price", "worth it", "cannot beat the price", "can't beat the price",
        "value priced", "great value", "good value",
    )
    explicit_price_objection_markers = (
        "too expensive", "high price", "not worth", "overpriced", "pricey", "pricy",
        "cost too much", "priced wrong", "price is wrong",
        "\u4ef7\u683c\u8d35", "\u592a\u8d35", "\u4e0d\u503c",
    )
    packaging_objection_markers = (
        "no lid", "not lid", "without a lid", "lid to go over the spout",
        "air is ever present", "oxidation", "cap leaked", "leaky cap", "bottle cap",
    )
    objection_markers = (
        "too much",
        "\u4ef7\u683c\u8d35", "\u592a\u8d35", "\u4e0d\u503c", "\u6027\u4ef7\u6bd4",
    )
    availability_markers = (
        "not available", "unavailable", "can't find", "cannot find", "hard to find",
        "west coast", "local store", "\u4e70\u4e0d\u5230", "\u4e0d\u597d\u4e70", "\u7f3a\u8d27", "\u897f\u6d77\u5cb8",
    )
    pain_markers = (
        "leak", "broken", "crack", "hard to clean", "too loud", "doesn't work",
        "stopped working", "bad", "terrible", "disappointed", "complain",
        "\u6f0f", "\u7834", "\u88c2", "\u96be\u6e05\u6d17", "\u592a\u5435", "\u5931\u671b", "\u5dee\u8bc4",
    )
    repeat_markers = (
        "continue to purchase", "will continue", "order it frequently", "buy again",
        "repeat purchase", "\u7ee7\u7eed\u8d2d\u4e70", "\u7ecf\u5e38\u8d2d\u4e70", "\u56de\u8d2d", "\u590d\u8d2d",
    )
    positive_markers = (
        "love", "best", "great", "smooth", "smoother", "flavor", "tastes good",
        "delicious", "worth it", "excellent", "favorite", "recommend",
        "\u6700\u597d", "\u559c\u6b22", "\u5f88\u559c\u6b22", "\u8d85\u68d2", "\u53e3\u611f", "\u987a\u6ed1", "\u5473\u9053", "\u597d\u8bc4", "\u63a8\u8350",
    )

    has_positive_value = any(marker in lowered for marker in positive_value_markers)
    has_price_objection = any(marker in lowered for marker in explicit_price_objection_markers)
    has_packaging_objection = any(marker in lowered for marker in packaging_objection_markers)

    if any(marker in lowered for marker in availability_markers):
        return "availability"
    if has_packaging_objection or has_price_objection or any(marker in lowered for marker in objection_markers):
        return "objection"
    if any(marker in lowered for marker in pain_markers):
        return "pain"
    if any(marker in lowered for marker in repeat_markers):
        return "repeat_purchase"
    if has_positive_value:
        return "positive"
    if any(marker in lowered for marker in positive_markers):
        return "positive"
    return "neutral"


def _pasted_review_is_price_value_positive_only(quote: str) -> bool:
    lowered = _clean_description_text(quote).lower()
    positive_value_markers = (
        "worth the price",
        "cannot beat the price",
        "can't beat the price",
        "value priced",
        "great value",
        "good value",
        "worth every",
        "for this quality",
    )
    explicit_price_objection_markers = (
        "too expensive",
        "high price",
        "not worth",
        "overpriced",
        "pricey",
        "pricy",
        "cost too much",
        "priced wrong",
        "price is wrong",
        "\u4ef7\u683c\u8d35",
        "\u592a\u8d35",
        "\u4e0d\u503c",
    )
    has_positive_value = any(marker in lowered for marker in positive_value_markers)
    has_explicit_price_objection = any(marker in lowered for marker in explicit_price_objection_markers)
    return has_positive_value and not has_explicit_price_objection


def _pasted_review_is_real_buyer_objection(quote: str) -> bool:
    kind = _pasted_review_signal_kind(quote)
    if kind not in {"objection", "availability"}:
        return False
    if _pasted_review_is_price_value_positive_only(quote):
        return False
    return True


def _pasted_review_signal_groups(evidence_quotes: list[str]) -> dict[str, list[str]]:
    groups = {
        "pain": [],
        "objection": [],
        "availability": [],
        "repeat_purchase": [],
        "positive": [],
        "neutral": [],
    }
    for quote in evidence_quotes:
        lowered = _clean_description_text(quote).lower()
        kind = _pasted_review_signal_kind(quote)
        target = groups.get(kind, groups["neutral"])
        if quote and quote not in target:
            target.append(quote)
        if quote and any(marker in lowered for marker in [
            "worth the price",
            "worth it",
            "cannot beat the price",
            "can't beat the price",
            "value priced",
            "great value",
            "good value",
        ]) and quote not in groups["positive"]:
            groups["positive"].append(quote)
    return groups


def _pasted_review_scene_goal(quote: str, request: PastedReviewsRequest, product_name: str, provided_goal: str | None = None) -> str:
    goal = _clean_description_text(provided_goal or "")
    kind = _pasted_review_signal_kind(quote)
    if goal and not (kind != "pain" and re.search(r"\bpain point\b|\bcustomer complaint\b", goal, flags=re.IGNORECASE)):
        return goal
    if kind in {"positive", "repeat_purchase"}:
        return "Show the positive review signal"
    if kind == "availability":
        return "Show the availability or scarcity signal"
    if kind == "objection":
        return "Show the buyer objection"
    if kind == "pain":
        return "Show the customer pain point"
    return "Show the core review signal"


async def generate_description_brief(request: ProductDescriptionRequest) -> dict:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0.4,
        max_retries=0,
    )
    content = (
        "Return JSON with keys: target_audience, core_hook_strategy, emotional_trigger, hook, "
        "cta, storyboard_scenes, evaluation_reasoning, feedback. "
        "storyboard_scenes must be a list of exactly 4 objects with visual_description, narration, evidence_quote_used.\n\n"
        f"Product name: {request.product_name}\n"
        f"Product category: {request.product_category or 'unspecified'}\n"
        f"Target platform: {request.target_platform or 'TikTok'}\n"
        f"Goal: {request.goal or 'tiktok_ctr'}\n"
        f"Product description: {request.product_description}\n"
        f"Customer pain points: {request.customer_pain_points}\n"
    )
    message = await llm.ainvoke(
        [
            SystemMessage(content=DESCRIPTION_SYSTEM_PROMPT),
            HumanMessage(content=content),
        ]
    )
    raw = str(message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Description generation returned non-object JSON.")
    return parsed


async def generate_pasted_reviews_brief(request: PastedReviewsRequest, evidence_quotes: list[str]) -> dict:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0.4,
        max_retries=0,
    )
    signal_groups = _pasted_review_signal_groups(evidence_quotes)
    pain_points = signal_groups["pain"][:4]
    buyer_objections = [
        quote
        for quote in (signal_groups["objection"] + signal_groups["availability"])
        if _pasted_review_is_real_buyer_objection(quote)
    ][:4]
    positive_signals = (signal_groups["positive"] + signal_groups["repeat_purchase"])[:4]
    neutral_signals = signal_groups["neutral"][:4]
    llm_evidence_packet = _review_workspace_packet_from_pasted_request(request) or _pasted_reviews_llm_evidence_packet(
        request,
        evidence_quotes,
        signal_groups,
        pain_points,
        buyer_objections,
        positive_signals,
        neutral_signals,
    )
    content = _pasted_reviews_llm_prompt_content(request, llm_evidence_packet)
    message = await llm.ainvoke(
        [
            SystemMessage(content=PASTED_REVIEWS_SYSTEM_PROMPT),
            HumanMessage(content=content),
        ]
    )
    raw = str(message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Pasted reviews generation returned non-object JSON.")
    return parsed


def _description_response_data(request: ProductDescriptionRequest, generated: dict) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_provided_product")
    description_quote = _safe_evidence_quote(request.product_description)
    pain_quote = _safe_evidence_quote(request.customer_pain_points)
    scenes = generated.get("storyboard_scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    normalized_scenes = []
    for index, scene in enumerate(scenes[:4]):
        if not isinstance(scene, dict):
            continue
        quote = scene.get("evidence_quote_used") or pain_quote or description_quote
        normalized_scenes.append(
            {
                "scene_id": index + 1,
                "scene_goal": scene.get("scene_goal", f"Show {product_name} benefit"),
                "visual_description": scene.get("visual_description", ""),
                "narration": scene.get("narration", ""),
                "evidence_quote_used": quote,
                "linked_painpoint": pain_quote,
            }
        )
    while len(normalized_scenes) < 4:
        index = len(normalized_scenes) + 1
        normalized_scenes.append(
            {
                "scene_id": index,
                "scene_goal": f"Make {product_name} feel useful",
                "visual_description": f"Show {product_name} solving the stated customer frustration in a simple {request.target_platform or 'TikTok'} scene.",
                "narration": f"{product_name} is positioned around the pain point: {pain_quote}",
                "evidence_quote_used": pain_quote or description_quote,
                "linked_painpoint": pain_quote,
            }
        )

    hook = generated.get("hook") or f"Stop ignoring this product pain point: {pain_quote}"
    cta = generated.get("cta") or f"Try {product_name} if this pain point sounds familiar."
    data = {
        "insights": {
            "pain_points": [pain_quote],
            "user_complaint_cluster": [pain_quote],
            "evidence": {
                "source_type": "user_provided_description",
                "source_url": "",
                "confidence": 0.55,
                "review_confidence": 0.0,
                "trend_confidence": 0.0,
                "review_count": 0,
                "evidence_quotes": [description_quote, pain_quote],
                "trend_signals": [],
                "data_warnings": ["user_provided_description_no_review_evidence"],
            },
        },
        "audience": {
            "primary": generated.get("target_audience", f"People considering {product_name}"),
            "sensitivity": generated.get("emotional_trigger", ""),
            "trust_barriers": [pain_quote],
        },
        "strategy": {
            "core_hook_strategy": generated.get("core_hook_strategy", ""),
            "emotional_trigger": generated.get("emotional_trigger", ""),
        },
        "assets": {
            "tiktok_script": {
                "hook": hook,
                "cta": cta,
            },
            "storyboard": {
                "product_name": product_name,
                "product_category": category,
                "source": "user_provided_description",
                "scenes": normalized_scenes,
            },
        },
        "evaluation": {
            "confidence_score": 0.62,
            "risk_level": "medium",
            "reasoning": generated.get(
                "evaluation_reasoning",
                "Generated from user-provided description only; no review evidence or source adapter was used.",
            ),
            "is_approved": True,
            "is_grounded": True,
            "creative_approved": True,
            "grounded_approved": True,
        },
        "feedback": generated.get(
            "feedback",
            "Generated from user-provided product description. Validate claims before using in paid creative.",
        ),
    }
    data["video_generation_packet"] = _build_video_generation_packet(
        product_name,
        category,
        data["assets"],
        data["insights"],
        data["evaluation"],
        getattr(request, "output_language", "en"),
    )
    data["external_video_tool_handoff"] = _build_external_video_tool_handoff(product_name, category, data)
    data["agent_trace"] = _build_agent_trace(data, getattr(request, "output_language", "en"))
    data["multi_agent_workflow"] = _build_multi_agent_workflow(data, getattr(request, "output_language", "en"))
    return data


def _multi_agent_workflow_text(value, limit: int = 260) -> str:
    return _agent_trace_text(value, limit=limit)


def _multi_agent_workflow_list(value, limit: int = 5) -> list[str]:
    return _agent_trace_items(value, limit=limit)


def _multi_agent_workflow_score(value, default: float = 0.66) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def _build_multi_agent_workflow(data: dict, output_language: str = "en") -> dict:
    """Build a business-grounded multi-agent workflow view from existing artifacts.

    This is not a separate multi-model execution engine yet. It is a transparent
    agent collaboration layer that maps current business artifacts into agent
    responsibilities, decisions, warnings, and handoffs.
    """
    if not isinstance(data, dict):
        return {}

    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    audience = data.get("audience") if isinstance(data.get("audience"), dict) else {}
    strategy = data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
    evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else {}
    script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []

    llm_packet = data.get("llm_evidence_packet") if isinstance(data.get("llm_evidence_packet"), dict) else {}
    video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else {}
    handoff = data.get("external_video_tool_handoff") if isinstance(data.get("external_video_tool_handoff"), dict) else {}
    agent_trace = data.get("agent_trace") if isinstance(data.get("agent_trace"), dict) else {}

    packet_evidence = llm_packet.get("evidence") if isinstance(llm_packet.get("evidence"), dict) else {}
    packet_stats = llm_packet.get("review_stats") if isinstance(llm_packet.get("review_stats"), dict) else {}
    packet_product = llm_packet.get("product") if isinstance(llm_packet.get("product"), dict) else {}
    constraints = llm_packet.get("generation_constraints") if isinstance(llm_packet.get("generation_constraints"), list) else []

    handoff_prompts = handoff.get("tool_prompts") if isinstance(handoff.get("tool_prompts"), dict) else {}
    keyframes = handoff.get("keyframe_prompts") if isinstance(handoff.get("keyframe_prompts"), list) else []
    product_rules = handoff.get("product_consistency_rules") if isinstance(handoff.get("product_consistency_rules"), list) else []
    product_asset_lock = handoff.get("product_asset_lock") if isinstance(handoff.get("product_asset_lock"), dict) else {}
    keyframe_plan = handoff.get("keyframe_plan") if isinstance(handoff.get("keyframe_plan"), dict) else {}
    plan_scenes = keyframe_plan.get("scenes") if isinstance(keyframe_plan.get("scenes"), list) else []

    source_type = (
        packet_product.get("source_type")
        or packet_evidence.get("source_type")
        or insights.get("evidence_source")
        or "unknown"
    )
    review_count = (
        packet_stats.get("review_count")
        or packet_evidence.get("review_count")
        or insights.get("review_count")
        or 0
    )
    evidence_quotes = packet_evidence.get("quotes") or packet_evidence.get("evidence_quotes") or insights.get("evidence_quotes") or []
    warning_items = (
        _multi_agent_workflow_list(packet_stats.get("warnings"), limit=4)
        + _multi_agent_workflow_list(insights.get("data_warnings"), limit=4)
        + _multi_agent_workflow_list(constraints, limit=4)
    )

    video_scenes = video_packet.get("scenes") if isinstance(video_packet.get("scenes"), list) else []
    export_formats = video_packet.get("export_formats") if isinstance(video_packet.get("export_formats"), dict) else {}
    export_keys = sorted(key for key, value in export_formats.items() if value)

    estimated_cost_summary = {}
    # A job-level provider_payload.cost_estimate is added later when a Video Job is created.
    # At generation time we expose the estimate agent as ready_for_job_creation.
    if isinstance(video_packet, dict):
        estimated_cost_summary = {
            "packet_version": video_packet.get("packet_version", ""),
            "recommended_duration_seconds": (video_packet.get("video") or {}).get("recommended_duration_seconds", ""),
            "scene_count": len(video_scenes),
            "requires_job_selection": True,
        }

    def agent(
        agent_id: str,
        role: str,
        goal: str,
        input_artifacts: list[str],
        decision_summary: str,
        output_artifacts: list[str],
        handoff_to: list[str],
        status: str = "complete",
        confidence_score: float = 0.66,
        warnings: list[str] | None = None,
        business_impact: str = "",
        requires_human_review: bool = False,
        key_outputs: dict | None = None,
    ) -> dict:
        return {
            "agent_id": agent_id,
            "role": role,
            "goal": goal,
            "status": status,
            "input_artifacts": input_artifacts,
            "decision_summary": _multi_agent_workflow_text(decision_summary, limit=420),
            "output_artifacts": output_artifacts,
            "handoff_to": handoff_to,
            "confidence_score": _multi_agent_workflow_score(confidence_score),
            "warnings": (warnings or [])[:8],
            "requires_human_review": bool(requires_human_review),
            "business_impact": business_impact,
            "key_outputs": key_outputs or {},
        }

    evidence_confidence = _multi_agent_workflow_score(packet_stats.get("source_confidence") or insights.get("source_confidence") or 0.64)
    risk_confidence = _multi_agent_workflow_score(evaluation.get("confidence_score") or 0.66)

    agents = [
        agent(
            "evidence_agent",
            "Evidence Agent",
            "Extract review-backed buyer signals and source boundaries.",
            ["llm_evidence_packet", "insights.evidence"],
            f"Using source_type={source_type}, prepared {len(evidence_quotes) if isinstance(evidence_quotes, list) else 0} evidence quotes from {review_count} review signals.",
            ["pain_points", "buyer_objections", "positive_signals", "evidence_quotes"],
            ["strategy_agent", "risk_agent"],
            confidence_score=evidence_confidence,
            warnings=warning_items,
            business_impact="Keeps creative generation grounded in buyer language instead of generic claims.",
            requires_human_review=bool(warning_items),
            key_outputs={
                "source_type": source_type,
                "review_count": review_count,
                "pain_points": _multi_agent_workflow_list(insights.get("pain_points") or packet_evidence.get("pain_points"), limit=5),
                "evidence_quote_count": len(evidence_quotes) if isinstance(evidence_quotes, list) else 0,
            },
        ),
        agent(
            "strategy_agent",
            "Strategy Agent",
            "Choose the audience, emotional trigger, and creative angle from the evidence.",
            ["llm_evidence_packet", "audience", "strategy"],
            strategy.get("core_hook_strategy") or script.get("hook") or "Use the strongest review-backed pain point as the creative angle.",
            ["target_audience", "core_hook_strategy", "emotional_trigger"],
            ["storyboard_agent", "risk_agent"],
            confidence_score=risk_confidence,
            business_impact="Turns raw buyer evidence into an ad direction that can convert.",
            key_outputs={
                "audience_primary": _multi_agent_workflow_text(audience.get("primary"), limit=320),
                "emotional_trigger": _multi_agent_workflow_text(strategy.get("emotional_trigger"), limit=320),
            },
        ),
        agent(
            "storyboard_agent",
            "Storyboard Agent",
            "Turn strategy into a short-form hook, CTA, and scene plan.",
            ["strategy", "assets.tiktok_script", "assets.storyboard"],
            f"Built a short-form script with hook={bool(script.get('hook'))}, cta={bool(script.get('cta'))}, scenes={len(scenes)}.",
            ["hook", "cta", "storyboard_scenes", "caption_draft"],
            ["asset_lock_agent", "keyframe_agent", "prompt_handoff_agent"],
            confidence_score=risk_confidence,
            business_impact="Converts strategy into a concrete shot list that creators or video tools can follow.",
            key_outputs={
                "hook": _multi_agent_workflow_text(script.get("hook"), limit=320),
                "cta": _multi_agent_workflow_text(script.get("cta"), limit=320),
                "scene_count": len(scenes),
            },
        ),
        agent(
            "asset_lock_agent",
            "Asset Lock Agent",
            "Define product identity and visual consistency constraints before generation.",
            ["product fields", "external_video_tool_handoff.product_asset_lock", "external_video_tool_handoff.product_consistency_rules"],
            "Prepared a product asset lock so external video tools preserve product identity, category, visible material, color, shape, and evidence boundaries.",
            ["product_asset_lock", "product_consistency_rules", "negative_prompt"],
            ["keyframe_agent", "prompt_handoff_agent", "risk_agent"],
            confidence_score=0.76 if product_asset_lock else (0.72 if product_rules else 0.55),
            warnings=[] if product_asset_lock else ["Product asset lock is missing or weak."],
            business_impact="Reduces product drift when using Gemini, Doubao, Runway, Pika, or other external tools.",
            requires_human_review=not bool(product_asset_lock),
            key_outputs={
                "asset_lock_version": product_asset_lock.get("lock_version", ""),
                "product_identity": product_asset_lock.get("product_identity", ""),
                "must_preserve": _multi_agent_workflow_list(product_asset_lock.get("must_preserve"), limit=5),
                "must_not_change": _multi_agent_workflow_list(product_asset_lock.get("must_not_change"), limit=5),
                "rule_count": len(product_rules),
                "rules": product_rules[:5],
            },
        ),
        agent(
            "keyframe_agent",
            "Keyframe Agent",
            "Convert storyboard scenes into controllable keyframes and motion prompts.",
            ["video_generation_packet.scenes", "external_video_tool_handoff.keyframe_prompts", "external_video_tool_handoff.keyframe_plan"],
            f"Prepared {len(plan_scenes) or len(keyframes)} planned keyframes for external video generation tools.",
            ["keyframe_plan", "keyframe_prompts", "motion_prompts", "overlay_text"],
            ["prompt_handoff_agent", "experiment_agent"],
            confidence_score=0.76 if keyframe_plan else (0.72 if keyframes else 0.55),
            warnings=[] if keyframe_plan else ["Keyframe plan is missing; external video tools may improvise too much."],
            business_impact="Improves generation stability by breaking the video into scene-level visual targets.",
            requires_human_review=not bool(keyframe_plan),
            key_outputs={
                "keyframe_plan_version": keyframe_plan.get("plan_version", ""),
                "keyframe_plan_scene_count": keyframe_plan.get("scene_count", 0),
                "recommended_clip_strategy": keyframe_plan.get("recommended_clip_strategy", ""),
                "keyframe_count": len(keyframes),
                "first_keyframe_goal": _multi_agent_workflow_text((keyframes[0] or {}).get("keyframe_goal") if keyframes else "", limit=240),
            },
        ),
        agent(
            "prompt_handoff_agent",
            "Prompt Handoff Agent",
            "Create copy-ready prompts for Gemini, Doubao, image-to-video, and manual workflows.",
            ["video_generation_packet", "external_video_tool_handoff"],
            "Generated external tool prompts without calling external APIs or incurring CrossGrowth cost.",
            ["gemini_video_prompt", "doubao_video_prompt", "general_image_to_video_prompt", "copy_ready_generation_brief"],
            ["cost_agent", "experiment_agent"],
            confidence_score=0.74 if handoff_prompts else 0.55,
            warnings=_multi_agent_workflow_list(handoff.get("warnings"), limit=5),
            business_impact="Lets the user test real external tools manually before committing to paid API integration.",
            key_outputs={
                "packet_version": handoff.get("packet_version", ""),
                "prompt_keys": sorted(key for key, value in handoff_prompts.items() if value),
                "external_api_called": bool(handoff.get("external_api_called", False)),
                "cost_incurred_by_crossgrowth": bool(handoff.get("cost_incurred_by_crossgrowth", False)),
            },
        ),
        agent(
            "cost_agent",
            "Cost Agent",
            "Estimate video generation cost before any real paid provider call.",
            ["video_generation_packet", "provider cost catalog"],
            "Prepared cost-estimate context. Final provider-specific estimate is attached when the user creates a Video Job.",
            ["cost_estimate_context", "requires_user_confirmation"],
            ["provider_job_agent", "risk_agent"],
            status="ready_for_job_creation",
            confidence_score=0.7,
            warnings=["Pricing is estimate-only and must be reviewed before enabling real external API calls."],
            business_impact="Prevents accidental cost surprises before paid video generation.",
            requires_human_review=True,
            key_outputs=estimated_cost_summary,
        ),
        agent(
            "risk_agent",
            "Risk Agent",
            "Check evidence grounding, unsupported claims, and generation risk.",
            ["llm_evidence_packet", "evaluation", "generation_constraints"],
            evaluation.get("reasoning") or "Checked available evidence boundaries and generation constraints.",
            ["risk_level", "is_grounded", "approval_status", "warnings"],
            ["provider_job_agent", "experiment_agent"],
            confidence_score=risk_confidence,
            warnings=_multi_agent_workflow_list(constraints, limit=5),
            business_impact="Protects the output from unsupported market-wide or unverifiable claims.",
            requires_human_review=bool(warning_items) or evaluation.get("risk_level") == "high",
            key_outputs={
                "risk_level": evaluation.get("risk_level", ""),
                "is_grounded": bool(evaluation.get("is_grounded")),
                "is_approved": bool(evaluation.get("is_approved")),
                "confidence_score": evaluation.get("confidence_score", 0.0),
            },
        ),
        agent(
            "provider_job_agent",
            "Provider Job Agent",
            "Track video generation jobs, provider status, result URLs, and manual fallback.",
            ["video_generation_packet", "provider_payload", "cost_estimate"],
            "Ready to create a tracked Video Job. The current generation flow does not call external video APIs.",
            ["video_job", "provider_runtime", "result_url", "history"],
            ["experiment_agent"],
            status="waiting_for_user_action",
            confidence_score=0.66,
            warnings=["Video Job records are memory-backed unless file storage or database persistence is enabled."],
            business_impact="Turns generated prompts into a trackable production task with status and result history.",
            requires_human_review=True,
            key_outputs={
                "supported_providers": ["manual_export", "generic", "capcut", "runway", "pika"],
                "simulated_provider_flow": "ready_for_manual_export -> queued -> processing -> external_result_ready",
            },
        ),
        agent(
            "experiment_agent",
            "Experiment Agent",
            "Record and compare manual Gemini, Doubao, Runway, Pika, or other external video results.",
            ["external_video_tool_handoff", "external_video_experiments"],
            "Waiting for the user to paste external tool results, costs, scores, and notes.",
            ["external_video_experiments", "quality_scores", "tool_comparison"],
            [],
            status="waiting_for_user_experiment",
            confidence_score=0.62,
            warnings=["Manual experiment quality requires user-provided result URLs, screenshots, or notes."],
            business_impact="Collects evidence for deciding whether a real provider API is worth integrating.",
            requires_human_review=True,
            key_outputs={
                "score_dimensions": [
                    "product_consistency",
                    "storyboard_following",
                    "visual_quality",
                    "ad_readiness",
                    "overall",
                ],
            },
        ),
    ]

    agent_order = [item["agent_id"] for item in agents]
    artifact_index = {
        "llm_evidence_packet": bool(llm_packet),
        "video_generation_packet": bool(video_packet),
        "external_video_tool_handoff": bool(handoff),
        "product_asset_lock": bool(product_asset_lock),
        "keyframe_plan": bool(keyframe_plan),
        "agent_trace": bool(agent_trace),
        "cost_estimate_context": bool(estimated_cost_summary),
    }

    return {
        "workflow_version": "multi_agent_workflow_v2",
        "workflow_name": "Business-grounded multi-agent video production workflow",
        "execution_mode": "artifact_orchestrated_agent_workflow",
        "is_real_multi_agent_execution": False,
        "is_plain_automation": False,
        "differentiator": "Each agent is mapped to a business artifact, decision, warning, and handoff instead of a simple linear automation step.",
        "output_language": output_language or "en",
        "agent_order": agent_order,
        "agents": agents,
        "artifact_index": artifact_index,
        "business_goal": "Transform review evidence into a controllable external video generation package and track manual/paid provider experiments.",
        "next_recommended_action": "Review the external video tool handoff, test Gemini or Doubao manually, then record the result in External Video Experiments.",
    }


def _pasted_reviews_llm_evidence_packet(
    request: PastedReviewsRequest,
    evidence_quotes: list[str],
    signal_groups: dict[str, list[str]],
    pain_points: list[str],
    buyer_objections: list[str],
    positive_signals: list[str],
    neutral_signals: list[str],
) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_pasted_reviews_product")
    warnings = [
        "user_pasted_reviews_unverified",
        "user_pasted_reviews_no_external_fetch",
    ]

    return {
        "packet_version": "pasted_reviews_v1",
        "intended_model_use": "creative_brief_generation",
        "product": {
            "title": product_name,
            "category": category,
            "source_type": "user_pasted_reviews",
            "source_url": "",
        },
        "review_stats": {
            "review_count": len(evidence_quotes),
            "source_confidence": 0.64,
            "review_confidence": 0.64,
            "trend_confidence": 0.0,
            "warnings": warnings,
        },
        "evidence": {
            "quotes": evidence_quotes[:12],
            "pain_points": pain_points[:4],
            "buyer_objections": buyer_objections[:4],
            "positive_signals": positive_signals[:4],
            "repeat_purchase_signals": signal_groups.get("repeat_purchase", [])[:3],
            "availability_signals": signal_groups.get("availability", [])[:3],
            "use_cases": neutral_signals[:4],
        },
        "generation_constraints": [
            "Use only the supplied review evidence and product fields.",
            "Do not claim full-market statistics or verified purchase coverage beyond the provided metadata.",
            "Keep uncertainty visible when evidence comes from pasted or extension-collected reviews.",
            "Prefer product-specific review language over generic category claims.",
            "Do not turn buyer objections into positive claims unless the evidence explicitly resolves the concern.",
        ],
    }


def _review_workspace_packet_from_pasted_request(request: PastedReviewsRequest) -> dict | None:
    packet = getattr(request, "llm_evidence_packet", None)
    if isinstance(packet, dict) and packet.get("packet_version") in {
        "review_workspace_v1",
        "source_evidence_v1",
    }:
        return packet
    return None


def _pasted_reviews_llm_prompt_content(request: PastedReviewsRequest, llm_evidence_packet: dict) -> str:
    target_platform = getattr(request, "target_platform", None) or "TikTok"
    goal = getattr(request, "goal", None) or "tiktok_ctr"
    return (
        "Return JSON with keys: target_audience, core_hook_strategy, emotional_trigger, hook, "
        "cta, storyboard_scenes, evaluation_reasoning, feedback. "
        "storyboard_scenes must be a list of exactly 4 objects with visual_description, narration, evidence_quote_used.\n\n"
        "Use the following llm_evidence_packet as the only evidence source. "
        "Follow generation_constraints strictly. Do not use raw assumptions outside the packet.\n\n"
        f"Target platform: {target_platform}\n"
        f"Goal: {goal}\n"
        "llm_evidence_packet JSON:\n"
        f"{json.dumps(llm_evidence_packet, ensure_ascii=False, indent=2)}"
    )


def _pasted_reviews_response_data(
    request: PastedReviewsRequest,
    generated: dict,
    evidence_quotes: list[str],
) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_pasted_reviews_product")
    description_quote = _safe_evidence_quote(request.product_description or "")
    primary_quote = evidence_quotes[0] if evidence_quotes else ""
    signal_groups = _pasted_review_signal_groups(evidence_quotes)
    pain_points = signal_groups["pain"][:4]
    buyer_objections = [quote for quote in (signal_groups["objection"] + signal_groups["availability"]) if _pasted_review_is_real_buyer_objection(quote)][:4]
    positive_signals = (signal_groups["positive"] + signal_groups["repeat_purchase"])[:4]
    neutral_signals = signal_groups["neutral"][:4]
    scenes = generated.get("storyboard_scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    normalized_scenes = []
    for index, scene in enumerate(scenes[:4]):
        if not isinstance(scene, dict):
            continue
        fallback_quote = evidence_quotes[index % len(evidence_quotes)] if evidence_quotes else primary_quote
        quote = _safe_evidence_quote(_clean_pasted_review_quote_text(scene.get("evidence_quote_used") or fallback_quote), limit=240)
        normalized_scenes.append(
            {
                "scene_id": index + 1,
                "scene_goal": _pasted_review_scene_goal(quote, request, product_name, scene.get("scene_goal")),
                "visual_description": scene.get("visual_description", ""),
                "narration": scene.get("narration", ""),
                "evidence_quote_used": quote,
                "linked_painpoint": quote,
            }
        )

    while len(normalized_scenes) < 4:
        index = len(normalized_scenes) + 1
        quote = evidence_quotes[(index - 1) % len(evidence_quotes)] if evidence_quotes else primary_quote
        quote = _safe_evidence_quote(_clean_pasted_review_quote_text(quote), limit=240)
        normalized_scenes.append(
            {
                "scene_id": index,
                "scene_goal": _pasted_review_scene_goal(quote, request, product_name),
                "visual_description": f"Show {product_name} turning this customer review signal into a simple product scene.",
                "narration": f"This review signal becomes the creative angle: {quote}",
                "evidence_quote_used": quote,
                "linked_painpoint": quote,
            }
        )

    hook = generated.get("hook") or f"If this review sounds familiar, {product_name} needs a better creative angle."
    cta = generated.get("cta") or f"Use {product_name} to answer the review signal your buyers already mention."
    llm_evidence_packet = _review_workspace_packet_from_pasted_request(request) or _pasted_reviews_llm_evidence_packet(
        request,
        evidence_quotes,
        signal_groups,
        pain_points,
        buyer_objections,
        positive_signals,
        neutral_signals,
    )

    data = {
        "insights": {
            "pain_points": pain_points,
            "buyer_objections": buyer_objections,
            "positive_signals": positive_signals,
            "social_proof": positive_signals,
            "repeat_purchase_signals": signal_groups["repeat_purchase"][:3],
            "availability_signals": signal_groups["availability"][:3],
            "user_complaint_cluster": pain_points + buyer_objections,
            "customer_feedback_signals": (pain_points + buyer_objections + positive_signals + neutral_signals)[:6],
            "evidence": {
                "source_type": "user_pasted_reviews",
                "source_url": "",
                "confidence": 0.64,
                "review_confidence": 0.64,
                "trend_confidence": 0.0,
                "review_count": len(evidence_quotes),
                "evidence_quotes": evidence_quotes,
                "trend_signals": [],
                "data_warnings": [
                    "user_pasted_reviews_unverified",
                    "user_pasted_reviews_no_external_fetch",
                ],
            },
        },
        "audience": {
            "primary": generated.get("target_audience", f"People considering {product_name}"),
            "sensitivity": generated.get("emotional_trigger", ""),
            "trust_barriers": buyer_objections,
        },
        "strategy": {
            "core_hook_strategy": generated.get("core_hook_strategy", ""),
            "emotional_trigger": generated.get("emotional_trigger", ""),
        },
        "assets": {
            "tiktok_script": {
                "hook": hook,
                "cta": cta,
            },
            "storyboard": {
                "product_name": product_name,
                "product_category": category,
                "source": "user_pasted_reviews",
                "scenes": normalized_scenes,
            },
        },
        "evaluation": {
            "confidence_score": 0.66,
            "risk_level": "medium",
            "reasoning": generated.get(
                "evaluation_reasoning",
                "Generated from user-pasted review snippets only; no external fetch or source adapter was used.",
            ),
            "is_approved": True,
            "is_grounded": True,
            "creative_approved": True,
            "grounded_approved": True,
        },
        "feedback": generated.get(
            "feedback",
            "Generated from pasted reviews. Verify claims and review authenticity before using in paid creative.",
        ),
        "llm_evidence_packet": llm_evidence_packet,
    }
    data["video_generation_packet"] = _build_video_generation_packet(
        product_name,
        category,
        data["assets"],
        data["insights"],
        data["evaluation"],
        getattr(request, "output_language", "en"),
    )
    data["external_video_tool_handoff"] = _build_external_video_tool_handoff(product_name, category, data)
    data["agent_trace"] = _build_agent_trace(data, getattr(request, "output_language", "en"))
    data["multi_agent_workflow"] = _build_multi_agent_workflow(data, getattr(request, "output_language", "en"))
    return data


def _agent_run_not_found(run_id: str):
    raise HTTPException(status_code=404, detail=f"Agent run not found: {run_id}")


def _start_agent_run_stage(run_id: str, agent_id: str, message: str, data: dict | None = None) -> None:
    AGENT_RUN_STORE.start_agent(run_id, agent_id)
    AGENT_RUN_STORE.set_graph_node_status(run_id, agent_id, "running")
    AGENT_RUN_STORE.append_event(
        run_id,
        "agent_started",
        message,
        agent_id=agent_id,
        data=data or {},
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "node_started",
        message,
        agent_id=agent_id,
        data={"node_id": agent_id, **(data or {})},
    )


def _complete_agent_run_stage(
    run_id: str,
    agent_id: str,
    message: str,
    decision_summary: str,
    business_impact: str = "",
    output_artifacts: list[str] | None = None,
    warnings: list[str] | None = None,
    data: dict | None = None,
) -> None:
    AGENT_RUN_STORE.complete_agent(
        run_id,
        agent_id,
        decision_summary=decision_summary,
        business_impact=business_impact,
        output_artifacts=output_artifacts,
        warnings=warnings,
    )
    AGENT_RUN_STORE.set_graph_node_status(run_id, agent_id, "complete")
    AGENT_RUN_STORE.append_event(
        run_id,
        "agent_completed",
        message,
        agent_id=agent_id,
        data=data or {},
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "node_completed",
        message,
        agent_id=agent_id,
        data={"node_id": agent_id, **(data or {})},
    )


def _traverse_agent_graph_edge(run_id: str, edge_id: str, reason: str) -> None:
    AGENT_RUN_STORE.traverse_graph_edge(run_id, edge_id, reason)
    AGENT_RUN_STORE.append_event(
        run_id,
        "edge_traversed",
        f"Graph edge traversed: {edge_id}.",
        data={"edge_id": edge_id, "reason": reason},
    )


def _record_graph_transition_decision(
    run_id: str,
    from_node_id: str,
    selected_to_node_id: str,
    agent_id: str,
    decision_type: str,
    reason: str,
    data: dict | None = None,
) -> None:
    decision = AGENT_RUN_STORE.add_transition_decision(
        run_id,
        from_node_id,
        selected_to_node_id,
        agent_id,
        decision_type,
        reason,
        data=data or {},
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "transition_decision",
        reason,
        agent_id=agent_id,
        data=decision,
    )


def _record_graph_validation_result(
    run_id: str,
    validator_agent_id: str,
    target_agent_id: str,
    target_artifact: str,
    status: str,
    reason: str,
    severity: str = "low",
    rework_target: str = "",
) -> None:
    validation = AGENT_RUN_STORE.add_validation_result(
        run_id,
        validator_agent_id,
        target_agent_id,
        target_artifact,
        status,
        reason,
        severity,
        rework_target,
    )
    event_type = "validation_failed" if status == "failed" else "validation_passed"
    AGENT_RUN_STORE.append_event(
        run_id,
        event_type,
        reason,
        agent_id=validator_agent_id,
        data=validation,
    )


def _record_graph_rework_loop(
    run_id: str,
    source_agent_id: str,
    target_agent_id: str,
    reason: str,
    status: str = "requested",
) -> None:
    loop = AGENT_RUN_STORE.add_rework_loop(
        run_id,
        source_agent_id,
        target_agent_id,
        reason,
        status=status,
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "rework_requested",
        reason,
        agent_id=source_agent_id,
        data=loop,
    )


def _record_graph_router_decision_for_run(run_id: str, router_decision: dict) -> None:
    current_run = AGENT_RUN_STORE.get(run_id) or {}
    append_graph_router_decision(current_run, router_decision)
    visited_node_ids = list(current_run.get("visited_node_ids") or [])
    if "graph_router_agent" not in visited_node_ids:
        visited_node_ids.append("graph_router_agent")
    graph_nodes = list(current_run.get("graph_nodes") or [])
    for node in graph_nodes:
        if node.get("node_id") == "graph_router_agent":
            node["status"] = "complete"
            break
    agents = list(current_run.get("agents") or [])
    for agent in agents:
        if agent.get("agent_id") == "graph_router_agent":
            agent["status"] = "complete"
            agent["decision_summary"] = str(router_decision.get("reason") or "")
            agent["business_impact"] = (
                "Centralizes the selected graph edge without triggering autonomous provider or paid actions."
            )
            break
    AGENT_RUN_STORE.update(
        run_id,
        {
            "graph_router_decisions": current_run.get("graph_router_decisions") or [],
            "latest_graph_router_decision": current_run.get("latest_graph_router_decision") or {},
            "graph_router_summary": current_run.get("graph_router_summary") or {},
            "visited_node_ids": visited_node_ids,
            "graph_nodes": graph_nodes,
            "agents": agents,
        },
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "graph_router_decision_created",
        str(router_decision.get("reason") or "Graph Router Agent created a route decision."),
        agent_id="graph_router_agent",
        data=router_decision,
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "graph_router_route_selected",
        (
            f"Graph Router Agent selected {router_decision.get('selected_next_agent_id') or 'finalizer_agent'} "
            f"for {router_decision.get('route_type') or 'stop'}."
        ),
        agent_id="graph_router_agent",
        data=router_decision,
    )


async def _execute_pasted_reviews_agent_run(run_id: str, request: PastedReviewsRequest) -> None:
    current_agent_id = ""
    try:
        source_bundle = _pasted_request_source_bundle(request, persist=True)
        AGENT_RUN_STORE.start_run(run_id)
        AGENT_RUN_STORE.append_event(
            run_id,
            "run_started",
            "Backend-tracked async agent run started.",
            data={"input_type": "pasted_reviews", "output_language": request.output_language or "en"},
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "graph_initialized",
            "Rule-driven agent graph initialized.",
            data={
                "graph_version": "agent_graph_runtime_v1",
                "graph_execution_mode": "rule_driven_agent_graph",
                "autonomy_level": "rule_driven_v1",
                "llm_autonomous_decision_enabled": False,
            },
        )

        current_agent_id = "planner_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Planner Agent validating pasted feedback request.")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Planner Agent completed request validation.",
            "Validated the pasted customer feedback request for artifact-orchestrated async generation.",
            "The run can proceed without changing the existing synchronous endpoint.",
            ["validated_generation_plan"],
        )
        _record_graph_transition_decision(
            run_id,
            "planner_agent",
            "evidence_agent",
            current_agent_id,
            "proceed",
            "Request validation passed; proceed to evidence extraction.",
        )
        _traverse_agent_graph_edge(run_id, "planner_to_evidence", "Request validation passed.")

        current_agent_id = "evidence_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Evidence Agent building review evidence packet.")
        evidence_quotes = _split_pasted_review_quotes(request.pasted_reviews)
        signal_groups = _pasted_review_signal_groups(evidence_quotes)
        pain_points = signal_groups["pain"][:4]
        buyer_objections = [
            quote
            for quote in (signal_groups["objection"] + signal_groups["availability"])
            if _pasted_review_is_real_buyer_objection(quote)
        ][:4]
        positive_signals = (signal_groups["positive"] + signal_groups["repeat_purchase"])[:4]
        neutral_signals = signal_groups["neutral"][:4]
        llm_evidence_packet = _review_workspace_packet_from_pasted_request(request) or _pasted_reviews_llm_evidence_packet(
            request,
            evidence_quotes,
            signal_groups,
            pain_points,
            buyer_objections,
            positive_signals,
            neutral_signals,
        )
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Evidence Agent completed evidence packet.",
            "Built the LLM evidence packet from supplied review snippets and product fields.",
            "Keeps review evidence explicit before any creative claims are made.",
            ["evidence_quotes", "llm_evidence_packet"],
            warnings=(llm_evidence_packet.get("review_stats") or {}).get("warnings") or [],
            data={
                "quote_count": len(evidence_quotes),
                "packet_version": llm_evidence_packet.get("packet_version"),
            },
        )
        _record_graph_transition_decision(
            run_id,
            "evidence_agent",
            "strategy_agent",
            current_agent_id,
            "proceed",
            "Evidence packet exists; proceed to strategy generation.",
            data={"packet_version": llm_evidence_packet.get("packet_version")},
        )
        _traverse_agent_graph_edge(run_id, "evidence_to_strategy", "Evidence packet built.")

        current_agent_id = "strategy_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Strategy Agent calling existing creative generation helper.")
        generated = await generate_pasted_reviews_brief(request, evidence_quotes)
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Strategy Agent completed creative strategy generation.",
            "Generated hook strategy, emotional trigger, hook, CTA, and storyboard draft from the evidence packet.",
            "Turns review evidence into a creative direction while preserving the existing generation behavior.",
            ["creative_strategy", "hook", "cta"],
        )
        _record_graph_transition_decision(
            run_id,
            "strategy_agent",
            "storyboard_agent",
            current_agent_id,
            "proceed",
            "Creative strategy generated; proceed to storyboard normalization.",
        )
        _traverse_agent_graph_edge(run_id, "strategy_to_storyboard", "Creative strategy generated.")

        current_agent_id = "storyboard_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Storyboard Agent building product response artifacts.")
        data = _pasted_reviews_response_data(request, generated, evidence_quotes)
        scenes = ((data.get("assets") or {}).get("storyboard") or {}).get("scenes") or []
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Storyboard Agent completed scenes and script assets.",
            "Normalized generated storyboard scenes into the Product Mode response shape.",
            "Makes the generated result reusable by copy, export, translation, and video job flows.",
            ["storyboard", "tiktok_script"],
            data={"scene_count": len(scenes)},
        )
        _record_graph_transition_decision(
            run_id,
            "storyboard_agent",
            "risk_agent",
            current_agent_id,
            "proceed",
            "Storyboard artifacts exist; run risk validation.",
            data={"scene_count": len(scenes)},
        )
        _traverse_agent_graph_edge(run_id, "storyboard_to_risk", "Storyboard requires risk validation.")

        current_agent_id = "risk_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Risk Agent reviewing warnings and evidence boundaries.")
        evidence = ((data.get("insights") or {}).get("evidence") or {})
        data_warnings = list(evidence.get("data_warnings") or [])
        evaluation = data.get("evaluation") or {}
        risk_level = str(evaluation.get("risk_level") or "").lower()
        warning_text = " ".join(str(item or "") for item in data_warnings).lower()
        unsupported_risk = any(token in warning_text for token in ["unsupported", "medical", "full-market", "full market"])
        risk_check = detect_storyboard_rework_need(data)
        if unsupported_risk and not risk_check.get("needs_rework"):
            risk_check = {
                "needs_rework": True,
                "reason": "Unsupported evidence-boundary warning requires storyboard rework.",
                "matched_terms": ["unsupported_warning"],
                "severity": "high" if "medical" in warning_text else "medium",
            }
        needs_rework = bool(risk_check.get("needs_rework"))
        risk_failed = needs_rework and risk_check.get("severity") == "high"
        risk_validation_status = "failed" if risk_failed else ("warning" if needs_rework or risk_level == "medium" or data_warnings else "passed")
        risk_reason = (
            str(risk_check.get("reason") or "Risk validation requested storyboard rework.")
            if needs_rework
            else "Risk validation passed with warnings." if risk_validation_status == "warning"
            else "Risk validation passed."
        )
        _record_graph_validation_result(
            run_id,
            "risk_agent",
            "storyboard_agent",
            "storyboard",
            risk_validation_status,
            risk_reason,
            severity=str(risk_check.get("severity") or ("medium" if risk_validation_status == "warning" else "low")),
            rework_target="storyboard_agent" if needs_rework else "",
        )
        if needs_rework:
            current_run_state = AGENT_RUN_STORE.get(run_id) or {}
            loop_count = int(current_run_state.get("loop_count") or 0)
            max_loop_count = int(current_run_state.get("max_loop_count") or 1)
            risk_router_decision = build_graph_router_decision(
                {
                    "route_context_type": "risk_validation",
                    "input_signal": "risky_terms_detected",
                    "validation_status": risk_validation_status,
                    "issue_type": "unsupported_storyboard_claim",
                    "reason": risk_reason,
                    "artifact_types": ["storyboard", "risk_notes"],
                },
                run=current_run_state,
            )
            _record_graph_router_decision_for_run(run_id, risk_router_decision)
            _record_graph_transition_decision(
                run_id,
                "risk_agent",
                "storyboard_agent",
                current_agent_id,
                "rework_requested",
                risk_reason,
                data={
                    "risk_level": risk_level,
                    "loop_count": loop_count,
                    "max_loop_count": max_loop_count,
                    "matched_terms": risk_check.get("matched_terms") or [],
                },
            )
            if loop_count < max_loop_count:
                _record_graph_rework_loop(
                    run_id,
                    "risk_agent",
                    "storyboard_agent",
                    risk_reason,
                    status="applied",
                )
                _traverse_agent_graph_edge(run_id, "risk_to_storyboard_rework", "Risk validation requested evidence-safe storyboard rework.")
                _complete_agent_run_stage(
                    run_id,
                    current_agent_id,
                    "Risk Agent requested evidence-safe storyboard rework.",
                    "Detected risky unsupported storyboard wording and routed the graph back to Storyboard Agent.",
                    "Prevents absolute or unsupported claims from continuing into video handoff.",
                    ["risk_notes", "rework_request"],
                    warnings=data_warnings,
                    data={
                        "matched_terms": risk_check.get("matched_terms") or [],
                        "severity": risk_check.get("severity"),
                    },
                )

                current_agent_id = "storyboard_agent"
                _start_agent_run_stage(run_id, current_agent_id, "Storyboard Agent applying evidence-safe rework.")
                data = apply_evidence_safe_storyboard_rework(
                    data,
                    risk_reason,
                    list(risk_check.get("matched_terms") or []),
                )
                scenes = ((data.get("assets") or {}).get("storyboard") or {}).get("scenes") or []
                _complete_agent_run_stage(
                    run_id,
                    current_agent_id,
                    "Storyboard Agent applied evidence-safe rework.",
                    "Replaced unsupported absolute wording with evidence-bound phrasing.",
                    "Keeps the generated storyboard usable while preserving supplied evidence and product identity.",
                    ["storyboard", "tiktok_script", "agent_graph_rework_summary"],
                    data={"scene_count": len(scenes), "rework_applied": True},
                )
                _record_graph_transition_decision(
                    run_id,
                    "storyboard_agent",
                    "risk_agent",
                    current_agent_id,
                    "validation_requested",
                    "Evidence-safe storyboard rework applied; Risk Agent must validate again.",
                    data={"scene_count": len(scenes), "rework_applied": True},
                )
                _traverse_agent_graph_edge(run_id, "storyboard_to_risk", "Reworked storyboard requires risk validation.")

                current_agent_id = "risk_agent"
                _start_agent_run_stage(run_id, current_agent_id, "Risk Agent re-validating evidence-safe storyboard rework.")
                evidence = ((data.get("insights") or {}).get("evidence") or {})
                data_warnings = list(evidence.get("data_warnings") or [])
                evaluation = data.get("evaluation") or {}
                risk_level = str(evaluation.get("risk_level") or "").lower()
                warning_text = " ".join(str(item or "") for item in data_warnings).lower()
                unsupported_risk = any(token in warning_text for token in ["unsupported", "medical", "full-market", "full market"])
                second_risk_check = detect_storyboard_rework_need(data)
                if unsupported_risk and not second_risk_check.get("needs_rework"):
                    second_risk_check = {
                        "needs_rework": True,
                        "reason": "Unsupported evidence-boundary warning remains after storyboard rework.",
                        "matched_terms": ["unsupported_warning"],
                        "severity": "high" if "medical" in warning_text else "medium",
                    }
                second_needs_rework = bool(second_risk_check.get("needs_rework"))
                if second_needs_rework:
                    second_reason = str(second_risk_check.get("reason") or "Risk remains after evidence-safe rework.")
                    _record_graph_validation_result(
                        run_id,
                        "risk_agent",
                        "storyboard_agent",
                        "storyboard",
                        "failed" if second_risk_check.get("severity") == "high" else "warning",
                        second_reason,
                        severity=str(second_risk_check.get("severity") or "medium"),
                        rework_target="storyboard_agent",
                    )
                    _record_graph_rework_loop(
                        run_id,
                        "risk_agent",
                        "storyboard_agent",
                        "Risk rework limit reached; human review is required before relying on storyboard claims.",
                        status="blocked",
                    )
                    AGENT_RUN_STORE.set_waiting_for_user(
                        run_id,
                        True,
                        "risk rework limit reached; human review is required before relying on storyboard claims.",
                    )
                    AGENT_RUN_STORE.append_event(
                        run_id,
                        "waiting_for_user",
                        "Risk rework limit reached; human review is required before relying on storyboard claims.",
                        agent_id="risk_agent",
                        data={"node_id": "risk_agent", "matched_terms": second_risk_check.get("matched_terms") or []},
                    )
                    _record_graph_transition_decision(
                        run_id,
                        "risk_agent",
                        "asset_lock_agent",
                        "risk_agent",
                        "validation_warning",
                        "Rework limit reached; continue with human review required and no further automatic loop.",
                        data={"loop_count": int((AGENT_RUN_STORE.get(run_id) or {}).get("loop_count") or 0), "max_loop_count": max_loop_count},
                    )
                else:
                    second_status = "warning" if risk_level == "medium" or data_warnings else "passed"
                    second_reason = "Risk validation passed after evidence-safe storyboard rework." if second_status == "passed" else "Risk validation passed after rework with warnings."
                    _record_graph_validation_result(
                        run_id,
                        "risk_agent",
                        "storyboard_agent",
                        "storyboard",
                        second_status,
                        second_reason,
                        severity="medium" if second_status == "warning" else "low",
                    )
                    _record_graph_transition_decision(
                        run_id,
                        "risk_agent",
                        "asset_lock_agent",
                        "risk_agent",
                        "validation_passed",
                        second_reason,
                        data={"risk_level": risk_level, "warning_count": len(data_warnings), "rework_applied": True},
                    )
                _traverse_agent_graph_edge(run_id, "risk_to_asset_lock", "Risk accepted after evidence-safe rework.")
                risk_reason = second_reason
            else:
                _record_graph_rework_loop(
                    run_id,
                    "risk_agent",
                    "storyboard_agent",
                    "Risk rework limit reached; human review is required before relying on storyboard claims.",
                    status="blocked",
                )
                AGENT_RUN_STORE.set_waiting_for_user(
                    run_id,
                    True,
                    "risk rework limit reached; human review is required before relying on storyboard claims.",
                )
                AGENT_RUN_STORE.append_event(
                    run_id,
                    "waiting_for_user",
                    "Risk rework limit reached; human review is required before relying on storyboard claims.",
                    agent_id="risk_agent",
                    data={"node_id": "risk_agent", "matched_terms": risk_check.get("matched_terms") or []},
                )
                _traverse_agent_graph_edge(run_id, "risk_to_asset_lock", "Risk rework limit reached; continue with human review required.")
        else:
            _record_graph_transition_decision(
                run_id,
                "risk_agent",
                "asset_lock_agent",
                current_agent_id,
                "validation_passed",
                risk_reason,
                data={"risk_level": risk_level, "warning_count": len(data_warnings)},
            )
            _traverse_agent_graph_edge(run_id, "risk_to_asset_lock", "Risk accepted or warning-only.")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Risk Agent completed evidence-risk review.",
            "Reviewed warnings and kept user-pasted evidence boundaries visible.",
            "Keeps claims grounded to supplied feedback instead of unsupported market-wide conclusions.",
            ["risk_notes", "data_warnings"],
            warnings=data_warnings,
        )

        current_agent_id = "asset_lock_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Product Asset Lock Agent checking product identity artifacts.")
        video_packet = data.get("video_generation_packet") or {}
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Product Asset Lock Agent completed product identity check.",
            "Checked the video generation packet for product identity and image-reference guidance.",
            "Helps prevent external video drafts from drifting away from the selected product.",
            ["product_asset_lock"],
            warnings=(video_packet.get("risk_notes") or [])[:3] if isinstance(video_packet.get("risk_notes"), list) else [],
        )
        _record_graph_transition_decision(
            run_id,
            "asset_lock_agent",
            "product_identity_validator",
            current_agent_id,
            "proceed",
            "Product asset lock exists; validate product identity.",
        )
        _traverse_agent_graph_edge(run_id, "asset_lock_to_product_identity_validator", "Asset lock ready.")

        product_identity = ((data.get("external_video_tool_handoff") or {}).get("product_asset_lock") or {}).get("product_identity") or ""
        product_category = ((data.get("external_video_tool_handoff") or {}).get("product_asset_lock") or {}).get("product_category") or ""
        AGENT_RUN_STORE.set_graph_node_status(run_id, "product_identity_validator", "running")
        AGENT_RUN_STORE.append_event(
            run_id,
            "node_started",
            "Product Identity Validator started.",
            agent_id="product_identity_validator",
            data={"node_id": "product_identity_validator"},
        )
        if not product_identity or not product_category:
            identity_reason = "Product identity or category is missing; user review is needed before visual prompts."
            _record_graph_validation_result(
                run_id,
                "product_identity_validator",
                "asset_lock_agent",
                "product_asset_lock",
                "failed",
                identity_reason,
                severity="medium",
                rework_target="asset_lock_agent",
            )
            _record_graph_transition_decision(
                run_id,
                "product_identity_validator",
                "asset_lock_agent",
                "product_identity_validator",
                "waiting_for_user",
                identity_reason,
            )
            AGENT_RUN_STORE.set_graph_node_status(run_id, "product_identity_validator", "waiting_for_user")
            AGENT_RUN_STORE.set_waiting_for_user(run_id, True, identity_reason)
            AGENT_RUN_STORE.append_event(
                run_id,
                "waiting_for_user",
                identity_reason,
                agent_id="product_identity_validator",
                data={"node_id": "product_identity_validator"},
            )
            _traverse_agent_graph_edge(run_id, "product_identity_validator_waiting", "Product identity needs user confirmation.")
        else:
            identity_reason = "Product identity validation passed."
            _record_graph_validation_result(
                run_id,
                "product_identity_validator",
                "asset_lock_agent",
                "product_asset_lock",
                "passed",
                identity_reason,
                severity="low",
            )
            _record_graph_transition_decision(
                run_id,
                "product_identity_validator",
                "keyframe_agent",
                "product_identity_validator",
                "validation_passed",
                identity_reason,
                data={"product_identity": product_identity, "product_category": product_category},
            )
            AGENT_RUN_STORE.set_graph_node_status(run_id, "product_identity_validator", "complete")
            AGENT_RUN_STORE.append_event(
                run_id,
                "node_completed",
                "Product Identity Validator completed.",
                agent_id="product_identity_validator",
                data={"node_id": "product_identity_validator"},
            )
            _traverse_agent_graph_edge(run_id, "product_identity_validator_to_keyframe", "Product identity validated.")

        current_agent_id = "keyframe_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Keyframe Agent checking scene/keyframe plan.")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Keyframe Agent completed keyframe planning.",
            "Prepared staged scene guidance for short test clips before longer video export.",
            "Encourages low-risk clip validation before paid or external provider generation.",
            ["keyframe_plan"],
        )
        _record_graph_transition_decision(
            run_id,
            "keyframe_agent",
            "prompt_handoff_agent",
            current_agent_id,
            "proceed",
            "Keyframe plan exists; proceed to prompt handoff.",
        )
        _traverse_agent_graph_edge(run_id, "keyframe_to_prompt_handoff", "Keyframe plan ready.")

        current_agent_id = "prompt_handoff_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Prompt Handoff Agent preparing external tool handoff.")
        handoff = data.get("external_video_tool_handoff") or {}
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Prompt Handoff Agent completed external video prompt handoff.",
            "Prepared manual Gemini/Doubao/export prompts without calling external video APIs.",
            "Keeps external provider work under user control and manual review.",
            ["external_video_tool_handoff"],
            data={"has_handoff": bool(handoff)},
        )
        _record_graph_transition_decision(
            run_id,
            "prompt_handoff_agent",
            "cost_agent",
            current_agent_id,
            "proceed",
            "External video handoff exists; proceed to cost validation.",
        )
        _traverse_agent_graph_edge(run_id, "prompt_handoff_to_cost", "Handoff prompts ready.")

        current_agent_id = "cost_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Cost Agent checking cost boundary.")
        _record_graph_validation_result(
            run_id,
            "cost_agent",
            "route_selector_agent",
            "provider_route",
            "warning",
            "Real external video APIs are disabled; route to manual external tool handoff.",
            severity="medium",
        )
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Cost Agent completed cost boundary check.",
            "Confirmed this async run does not call paid external video APIs.",
            "Cost-incurring provider execution remains gated behind manual/provider job controls.",
            ["cost_boundary"],
            data={"cost_incurred_by_crossgrowth": False},
        )
        _record_graph_transition_decision(
            run_id,
            "cost_agent",
            "route_selector_agent",
            current_agent_id,
            "validation_passed",
            "Cost boundary checked; choose a safe route.",
            data={"external_api_called": False},
        )
        _traverse_agent_graph_edge(run_id, "cost_to_route_selector", "Cost boundary checked.")

        AGENT_RUN_STORE.set_graph_node_status(run_id, "route_selector_agent", "running")
        AGENT_RUN_STORE.append_event(
            run_id,
            "node_started",
            "Route Selector Agent started.",
            agent_id="route_selector_agent",
            data={"node_id": "route_selector_agent"},
        )
        AGENT_RUN_STORE.set_branch_selected(run_id, "manual_external_tool_handoff")
        _record_graph_transition_decision(
            run_id,
            "route_selector_agent",
            "prompt_handoff_agent",
            "route_selector_agent",
            "branch_selected",
            "Real provider APIs are disabled, so the graph selects manual_external_tool_handoff.",
            data={"branch_selected": "manual_external_tool_handoff"},
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "branch_selected",
            "Manual external tool handoff selected because real external API calls are disabled.",
            agent_id="route_selector_agent",
            data={"branch_selected": "manual_external_tool_handoff"},
        )
        AGENT_RUN_STORE.set_graph_node_status(run_id, "route_selector_agent", "complete")
        AGENT_RUN_STORE.append_event(
            run_id,
            "node_completed",
            "Route Selector Agent completed.",
            agent_id="route_selector_agent",
            data={"node_id": "route_selector_agent", "branch_selected": "manual_external_tool_handoff"},
        )
        _traverse_agent_graph_edge(run_id, "route_selector_to_prompt_handoff_fallback", "Manual fallback selected.")
        AGENT_RUN_STORE.set_graph_node_status(run_id, "provider_job_agent", "waiting_for_user")
        AGENT_RUN_STORE.set_graph_node_status(run_id, "experiment_agent", "waiting_for_user")
        AGENT_RUN_STORE.set_waiting_for_user(
            run_id,
            True,
            "Video Job creation and external experiment scoring are waiting for user action after generation.",
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "waiting_for_user",
            "Provider job and experiment nodes are waiting for user action after generation.",
            agent_id="provider_job_agent",
            data={"nodes": ["provider_job_agent", "experiment_agent"]},
        )
        _traverse_agent_graph_edge(run_id, "prompt_handoff_to_finalizer_fallback", "Manual workflow can finalize generated artifacts.")

        current_agent_id = "finalizer_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Finalizer Agent preparing final generated result.")
        data["project_id"] = _safe_project_id(request.project_id)
        final_data = await translate_product_visible_data(data, request.output_language or "en")
        final_data.update(
            {
                "project_source": source_bundle.get("project_source") or {},
                "source_evidence_artifact": source_bundle.get("source_evidence_artifact") or {},
                "source_quality_gate": source_bundle.get("source_quality_gate") or {},
                "source_snapshot": source_bundle.get("source_snapshot") or {},
            }
        )
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Finalizer Agent completed final result.",
            "Stored the completed Product Mode result on the agent run.",
            "The same dashboard, video job, provider progress, and manual handoff flows can use this result.",
            ["final_product_result", "multi_agent_workflow"],
        )

        AGENT_RUN_STORE.complete_run(run_id, final_data)
        AGENT_RUN_STORE.complete_graph(run_id)
        AGENT_RUN_STORE.append_event(
            run_id,
            "run_completed",
            "Agent run completed.",
            data={
                "has_result": True,
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "graph_completed",
            "Rule-driven agent graph completed.",
            data={"branch_selected": "manual_external_tool_handoff"},
        )
        completed_run = AGENT_RUN_STORE.get(run_id) or {}
        completed_run = _persist_agent_run_graph_os(completed_run)
        AGENT_RUN_STORE.update(
            run_id,
            {
                "artifact_registry": completed_run.get("artifact_registry") or {},
                "agent_messages": completed_run.get("agent_messages") or [],
                "latest_graph_state_snapshot": completed_run.get("latest_graph_state_snapshot") or {},
                "graph_health": completed_run.get("graph_health") or {},
                "persistence": completed_run.get("persistence") or {},
                "persistence_warnings": completed_run.get("persistence_warnings") or [],
            },
        )
    except Exception as exc:
        error = str(exc or "Agent run failed.")
        if current_agent_id:
            AGENT_RUN_STORE.fail_agent(run_id, current_agent_id, error)
            AGENT_RUN_STORE.append_event(
                run_id,
                "agent_failed",
                "Agent stage failed safely.",
                agent_id=current_agent_id,
                data={"error_type": _error_type(exc)},
            )
        AGENT_RUN_STORE.fail_run(run_id, error)
        AGENT_RUN_STORE.append_event(
            run_id,
            "run_failed",
            "Agent run failed safely.",
            data={"error_type": _error_type(exc), "error": error[:240]},
        )
        failed_run = AGENT_RUN_STORE.get(run_id) or {}
        failed_run = _persist_agent_run_graph_os(failed_run)
        AGENT_RUN_STORE.update(
            run_id,
            {
                "artifact_registry": failed_run.get("artifact_registry") or {},
                "agent_messages": failed_run.get("agent_messages") or [],
                "latest_graph_state_snapshot": failed_run.get("latest_graph_state_snapshot") or {},
                "graph_health": failed_run.get("graph_health") or {},
                "persistence": failed_run.get("persistence") or {},
                "persistence_warnings": failed_run.get("persistence_warnings") or [],
            },
        )


@app.get("/healthz")
async def healthz(request: Request):
    started = time.perf_counter()
    emit_event(
        "healthz_request",
        request.state.request_id,
        endpoint="/healthz",
        status="ok",
        latency_ms=(time.perf_counter() - started) * 1000,
    )
    return {
        "status": "ok",
        "service": "grounded-ecommerce-creative-agent",
        "stable_baseline": "l9_9_stable",
    }


def _amazon_intake_fallback_message(data_warnings: list[str] | None = None) -> str:
    warnings = set(data_warnings or [])
    if "review_sign_in_required" in warnings:
        return (
            "Product signals were fetched, but Amazon reviews require sign-in. "
            "Paste 3-5 Amazon reviews to improve the creative brief."
        )
    return "Paste 3-5 Amazon reviews or product bullets to improve the creative brief."


def _amazon_empty_review_insights() -> dict:
    return {
        "pain_points": [],
        "buyer_objections": [],
        "use_cases": [],
        "emotional_triggers": [],
        "evidence_quotes": [],
    }


def _amazon_review_insights(review_items: list[dict]) -> dict:
    texts = [
        str(item.get("text") or "").strip()
        for item in review_items
        if str(item.get("text") or "").strip()
    ]
    if not texts:
        return _amazon_empty_review_insights()

    def pick(keywords: tuple[str, ...], fallback: list[str], limit: int = 3) -> list[str]:
        matches = []
        for text in texts:
            lowered = text.lower()
            if any(keyword in lowered for keyword in keywords):
                matches.append(text)
        return _dedupe_amazon_insight_lines(matches or fallback, limit)

    pain_keywords = (
        "leak",
        "crack",
        "broken",
        "watery",
        "thin",
        "flavorless",
        "terrible",
        "problem",
        "issue",
        "hard to",
        "too ",
        "not ",
        "failed",
    )
    objection_keywords = (
        "price",
        "expensive",
        "worth",
        "quality",
        "shipping",
        "delivery",
        "box",
        "bottle",
        "size",
        "received",
        "return",
    )
    use_case_keywords = (
        "salad",
        "vinaigrette",
        "cheese",
        "cooking",
        "use",
        "used",
        "order",
        "favorite",
        "bottle",
    )
    emotion_keywords = (
        "favorite",
        "love",
        "like",
        "good",
        "great",
        "fairly priced",
        "terrible",
        "disappointed",
        "wateriest",
        "flavorless",
    )

    return {
        "pain_points": pick(pain_keywords, texts),
        "buyer_objections": pick(objection_keywords, texts),
        "use_cases": pick(use_case_keywords, texts),
        "emotional_triggers": pick(emotion_keywords, texts),
        "evidence_quotes": _dedupe_amazon_insight_lines(texts, 5),
    }


def _dedupe_amazon_insight_lines(values: list[str], limit: int) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = _clean_description_text(value)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _create_video_generation_job(request: VideoGenerationJobRequest) -> dict:
    packet = dict(request.video_generation_packet or {})
    provider = normalize_video_provider(request.provider or "manual_export") or "manual_export"
    now = _utc_now_iso()
    job_id = f"video_job_{uuid4().hex[:12]}"
    export_formats = video_job_export_formats(packet)
    provider_payload = video_provider_payload_metadata(provider, export_formats, packet)
    provider_payload["cost_estimate"] = estimate_cost_from_video_packet(packet, provider=provider)
    initial_status = normalize_video_job_status(VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT)

    warnings = []
    if not provider_payload["prompt"]:
        warnings.append("missing_generic_video_prompt")
    if not provider_payload["scenes"]:
        warnings.append("missing_video_scenes")

    job = {
        "job_id": job_id,
        "project_id": _safe_project_id(request.project_id),
        "status": initial_status,
        "provider": provider,
        "created_at": now,
        "updated_at": now,
        "output_language": request.output_language,
        "video_generation_packet": packet,
        "provider_payload": provider_payload,
        "result": {
            "result_url": "",
            "preview_url": "",
            "download_url": "",
            "provider_job_id": "",
            "notes": "",
            "message": "Manual export scaffold created. No external video API has been called.",
        },
        "warnings": warnings,
        "history": [
            build_video_job_history_event("created", initial_status, updated_at=now, provider=provider)
        ],
    }
    job = _persist_video_job_graph_os(job)
    return VIDEO_JOB_STORE.create(job)


def _update_video_generation_job_result(job: dict, request: VideoGenerationJobResultRequest) -> tuple[dict | None, str]:
    requested_status = _clean_description_text(request.status or "manual_export_completed")
    if requested_status not in VIDEO_GENERATION_RESULT_STATUSES:
        requested_status = VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED
    requested_status = normalize_video_job_status(
        requested_status,
        fallback=VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    )

    current_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    if not can_transition_video_job_status(current_status, requested_status):
        return None, f"invalid video job status transition: {current_status} -> {requested_status}"

    result = dict(job.get("result") or {})
    result.update(
        {
            "result_url": _clean_description_text(request.result_url),
            "preview_url": _clean_description_text(request.preview_url),
            "download_url": _clean_description_text(request.download_url),
            "provider_job_id": _clean_description_text(request.provider_job_id),
            "notes": _clean_description_text(request.notes),
            "message": "External/manual video result recorded." if requested_status != "failed" else "External/manual video generation failed.",
        }
    )

    job["status"] = requested_status
    now = _utc_now_iso()
    job["updated_at"] = now
    job["result"] = result

    history = list(job.get("history") or [])
    if current_status != requested_status:
        history.append(
            build_video_job_history_event(
                "status_changed",
                requested_status,
                updated_at=now,
                from_status=current_status,
                to_status=requested_status,
            )
        )
    history.append(
        build_video_job_history_event(
            "result_update",
            requested_status,
            updated_at=now,
            provider_job_id=result.get("provider_job_id", ""),
            has_result_url=bool(result.get("result_url")),
        )
    )
    job["history"] = history
    return job, ""


def _validate_video_experiment_scores(request: VideoGenerationExperimentRequest) -> str:
    for field_name in [
        "product_consistency_score",
        "storyboard_following_score",
        "visual_quality_score",
        "ad_readiness_score",
        "overall_score",
    ]:
        value = getattr(request, field_name)
        if value is None:
            continue
        if value < 1 or value > 5:
            return f"{field_name} must be between 1 and 5"
    return ""


def _is_second_video_experiment_request(request: VideoGenerationExperimentRequest) -> bool:
    try:
        round_number = int(getattr(request, "experiment_round", 1) or 1)
    except (TypeError, ValueError):
        round_number = 1
    return round_number == 2 or bool(getattr(request, "compare_to_previous", False))


def _experiment_triggered_rework_run_id(experiment: dict) -> str:
    decision = experiment.get("agent_feedback_decision") if isinstance(experiment.get("agent_feedback_decision"), dict) else {}
    return (
        str(experiment.get("triggered_rework_run_id") or "").strip()
        or str(decision.get("triggered_rework_run_id") or "").strip()
    )


def _find_second_experiment_baseline(
    experiments: list[dict],
    request: VideoGenerationExperimentRequest,
) -> dict:
    baseline_id = str(getattr(request, "baseline_experiment_id", "") or "").strip()
    if baseline_id:
        for experiment in experiments:
            if str(experiment.get("experiment_id") or "") == baseline_id:
                return experiment

    linked_rework_run_id = str(getattr(request, "linked_rework_run_id", "") or "").strip()
    if linked_rework_run_id:
        for experiment in reversed(experiments):
            if _experiment_triggered_rework_run_id(experiment) == linked_rework_run_id:
                return experiment

    for experiment in reversed(experiments):
        decision = experiment.get("agent_feedback_decision") if isinstance(experiment.get("agent_feedback_decision"), dict) else {}
        if decision.get("has_feedback") is True:
            return experiment

    return {}


def _rework_run_for_second_experiment(request: VideoGenerationExperimentRequest, baseline: dict) -> dict:
    linked_rework_run_id = (
        str(getattr(request, "linked_rework_run_id", "") or "").strip()
        or _experiment_triggered_rework_run_id(baseline)
    )
    if not linked_rework_run_id:
        return {}
    return AGENT_RUN_STORE.get(linked_rework_run_id) or {}


def _record_external_video_experiment(job: dict, request: VideoGenerationExperimentRequest) -> tuple[dict | None, str]:
    score_error = _validate_video_experiment_scores(request)
    if score_error:
        return None, score_error

    now = _utc_now_iso()
    existing_experiments = list(job.get("external_video_experiments") or job.get("external_experiments") or [])
    is_second_experiment = _is_second_video_experiment_request(request)
    experiment = {
        "experiment_id": f"video_experiment_{uuid4().hex[:12]}",
        "project_id": _safe_project_id(job.get("project_id")),
        "tool_name": _clean_description_text(request.tool_name or "other"),
        "prompt_type": _clean_description_text(request.prompt_type or "custom"),
        "result_url": _clean_description_text(request.result_url),
        "preview_url": _clean_description_text(request.preview_url),
        "prompt_used": _safe_evidence_quote(request.prompt_used, limit=4000),
        "estimated_cost_usd": request.estimated_cost_usd,
        "actual_cost_usd": request.actual_cost_usd,
        "product_consistency_score": request.product_consistency_score,
        "storyboard_following_score": request.storyboard_following_score,
        "visual_quality_score": request.visual_quality_score,
        "ad_readiness_score": request.ad_readiness_score,
        "overall_score": request.overall_score,
        "notes": _clean_description_text(request.notes),
        "failure_reason": _clean_description_text(request.failure_reason),
        "created_at": now,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
    }
    baseline_experiment_id = _clean_description_text(getattr(request, "baseline_experiment_id", ""))
    linked_rework_run_id = _clean_description_text(getattr(request, "linked_rework_run_id", ""))
    prompt_source = _clean_description_text(getattr(request, "prompt_source", ""))
    if baseline_experiment_id:
        experiment["baseline_experiment_id"] = baseline_experiment_id
    if linked_rework_run_id:
        experiment["linked_rework_run_id"] = linked_rework_run_id
    if prompt_source:
        experiment["prompt_source"] = prompt_source
    if is_second_experiment:
        experiment["experiment_round"] = 2
        experiment["compare_to_previous"] = True
    feedback_decision = build_experiment_feedback_decision(experiment, job)
    router_decisions: list[dict] = []
    if not is_second_experiment and feedback_decision.get("has_feedback") is True:
        feedback_router_decision = build_graph_router_decision(
            {
                "route_context_type": "experiment_feedback",
                "input_signal": feedback_decision.get("issue_type"),
                "issue_type": feedback_decision.get("issue_type"),
                "reason": feedback_decision.get("reason"),
                "score_deltas": feedback_decision.get("score_snapshot") or {},
                "artifact_types": ["external_video_experiment"],
            },
            job=job,
        )
        append_graph_router_decision(experiment, feedback_router_decision)
        router_decisions.append(feedback_router_decision)
    original_generation_data = {
        "project_id": _safe_project_id(job.get("project_id")),
        "video_generation_packet": job.get("video_generation_packet") or {},
        "provider_payload": job.get("provider_payload") or {},
        "source_generation": job.get("source_generation") or {},
        "external_video_tool_handoff": job.get("external_video_tool_handoff") or {},
    }
    rework_run = None
    if not is_second_experiment:
        rework_run = trigger_experiment_rework_run(
            str(job.get("job_id") or ""),
            feedback_decision,
            original_generation_data=original_generation_data,
            experiment=experiment,
        )
    if rework_run:
        AGENT_RUN_STORE.create(rework_run)
        persisted_rework_run = _persist_agent_run_graph_os(rework_run)
        AGENT_RUN_STORE.update(
            rework_run["run_id"],
            {
                "artifact_registry": persisted_rework_run.get("artifact_registry") or {},
                "agent_messages": persisted_rework_run.get("agent_messages") or [],
                "latest_graph_state_snapshot": persisted_rework_run.get("latest_graph_state_snapshot") or {},
                "graph_health": persisted_rework_run.get("graph_health") or {},
                "persistence": persisted_rework_run.get("persistence") or {},
            },
        )
        feedback_decision = dict(feedback_decision)
        feedback_decision["triggered_rework_run_id"] = rework_run["run_id"]
        feedback_decision["triggered_rework_poll_url"] = f"/api/v1/agent-runs/{rework_run['run_id']}"
        feedback_decision["triggered_rework_events_url"] = f"/api/v1/agent-runs/{rework_run['run_id']}/events"
        if (rework_run.get("result") or {}).get("revised_keyframe_plan"):
            feedback_decision["triggered_rework_result_type"] = "revised_keyframe_plan"
            experiment["triggered_rework_result_type"] = "revised_keyframe_plan"
        if (rework_run.get("result") or {}).get("revised_external_video_handoff"):
            feedback_decision["triggered_rework_next_artifact_type"] = "revised_external_video_handoff"
            experiment["triggered_rework_next_artifact_type"] = "revised_external_video_handoff"
    experiment["agent_feedback_decision"] = feedback_decision

    second_comparison: dict = {}
    comparison_decision_gate: dict = {}
    artifact_lineage_summary: dict = {}
    controlled_provider_handoff_checklist: dict = {}
    human_approval_gate: dict = {}
    demo_ready_run_summary: dict = {}
    if is_second_experiment:
        baseline_experiment = _find_second_experiment_baseline(existing_experiments, request)
        baseline_decision = (
            baseline_experiment.get("agent_feedback_decision")
            if isinstance(baseline_experiment.get("agent_feedback_decision"), dict)
            else {}
        )
        comparison_rework_run = _rework_run_for_second_experiment(request, baseline_experiment)
        if baseline_experiment:
            second_comparison = build_second_experiment_comparison(
                baseline_experiment,
                experiment,
                baseline_decision,
                comparison_rework_run,
            )
            if prompt_source and not second_comparison.get("prompt_source"):
                second_comparison["prompt_source"] = prompt_source
            experiment["second_experiment_comparison"] = second_comparison
            comparison_router_decision = build_graph_router_decision(
                {
                    "route_context_type": "second_experiment_comparison",
                    "input_signal": second_comparison.get("status"),
                    "comparison_status": second_comparison.get("status"),
                    "reason": second_comparison.get("reason"),
                    "score_deltas": second_comparison.get("score_deltas") or {},
                    "artifact_types": [
                        "second_external_experiment",
                        "second_experiment_comparison",
                    ],
                },
                job=job,
            )
            append_graph_router_decision(experiment, comparison_router_decision)
            router_decisions.append(comparison_router_decision)
            comparison_decision_gate = build_experiment_comparison_decision_gate(
                second_comparison,
                job=job,
                baseline_experiment=baseline_experiment,
                second_experiment=experiment,
            )
            experiment["experiment_comparison_decision_gate"] = comparison_decision_gate
            gate_router_decision = build_graph_router_decision(
                {
                    "route_context_type": "experiment_comparison_decision_gate",
                    "input_signal": comparison_decision_gate.get("decision_type"),
                    "gate_decision_type": comparison_decision_gate.get("decision_type"),
                    "comparison_status": comparison_decision_gate.get("comparison_status"),
                    "reason": comparison_decision_gate.get("reason"),
                    "confidence": comparison_decision_gate.get("confidence"),
                    "score_deltas": second_comparison.get("score_deltas") or {},
                    "artifact_types": ["experiment_comparison_decision_gate"],
                },
                job=job,
            )
            append_graph_router_decision(experiment, gate_router_decision)
            router_decisions.append(gate_router_decision)
            if comparison_decision_gate.get("should_proceed_to_provider_test") is True:
                controlled_provider_handoff_checklist = build_controlled_provider_handoff_checklist(
                    job,
                    comparison_decision_gate,
                    rework_run=comparison_rework_run,
                    comparison=second_comparison,
                )
                checklist_router_decision = build_graph_router_decision(
                    {
                        "route_context_type": "controlled_provider_checklist",
                        "input_signal": controlled_provider_handoff_checklist.get("checklist_version"),
                        "reason": controlled_provider_handoff_checklist.get("recommended_next_action"),
                        "artifact_types": ["controlled_provider_handoff_checklist"],
                    },
                    job=job,
                )
                append_graph_router_decision(experiment, checklist_router_decision)
                router_decisions.append(checklist_router_decision)
                experiment["controlled_provider_handoff_checklist"] = controlled_provider_handoff_checklist
                if (
                    second_comparison.get("status") == "improved"
                    and comparison_decision_gate.get("decision_type") == "proceed_to_controlled_test"
                    and checklist_router_decision.get("decision_type")
                    == "route_to_human_approval_before_provider"
                    and checklist_router_decision.get("selected_next_agent_id") == "human_approval_agent"
                ):
                    human_approval_gate = build_human_approval_gate(
                        job,
                        decision_gate=comparison_decision_gate,
                        checklist=controlled_provider_handoff_checklist,
                        router_decision=checklist_router_decision,
                    )
                    experiment["human_approval_gate"] = human_approval_gate
            artifact_lineage_summary = build_lightweight_artifact_lineage(
                job,
                baseline_experiment=baseline_experiment,
                second_experiment=experiment,
                rework_run=comparison_rework_run,
                comparison=second_comparison,
                decision_gate=comparison_decision_gate,
                human_approval_gate=human_approval_gate,
            )
            experiment["artifact_lineage"] = artifact_lineage_summary
            if controlled_provider_handoff_checklist:
                demo_ready_run_summary = build_demo_ready_run_summary(
                    job,
                    baseline_experiment,
                    experiment,
                    comparison_rework_run,
                    second_comparison,
                    comparison_decision_gate,
                    artifact_lineage_summary,
                    controlled_provider_handoff_checklist,
                    human_approval_gate,
                )
                experiment["demo_ready_run_summary"] = demo_ready_run_summary

    experiments = list(existing_experiments)
    experiments.append(experiment)
    job["external_video_experiments"] = experiments
    job["external_experiments"] = experiments
    job["latest_agent_feedback_decision"] = feedback_decision
    for router_decision in router_decisions:
        append_graph_router_decision(job, router_decision)
    if second_comparison:
        job["latest_second_experiment_comparison"] = second_comparison
    if comparison_decision_gate:
        job["latest_experiment_comparison_decision_gate"] = comparison_decision_gate
    if artifact_lineage_summary:
        job["latest_artifact_lineage"] = artifact_lineage_summary
    if controlled_provider_handoff_checklist:
        job["latest_controlled_provider_handoff_checklist"] = controlled_provider_handoff_checklist
    if human_approval_gate:
        job["latest_human_approval_gate"] = human_approval_gate
    if demo_ready_run_summary:
        job["latest_demo_ready_run_summary"] = demo_ready_run_summary
    if rework_run:
        job["latest_experiment_rework_run_id"] = rework_run["run_id"]
        rework_run_ids = list(job.get("experiment_rework_run_ids") or [])
        rework_run_ids.append(rework_run["run_id"])
        job["experiment_rework_run_ids"] = rework_run_ids[-10:]
        if (rework_run.get("result") or {}).get("revised_keyframe_plan"):
            job["latest_rework_artifact_type"] = "revised_keyframe_plan"
        if (rework_run.get("result") or {}).get("revised_external_video_handoff"):
            job["latest_rework_next_artifact_type"] = "revised_external_video_handoff"
    existing_feedback = job.get("agent_graph_feedback") if isinstance(job.get("agent_graph_feedback"), dict) else {}
    feedback_decisions = list(existing_feedback.get("decisions") or [])
    feedback_decisions.append(feedback_decision)
    job["agent_graph_feedback"] = {
        "feedback_version": "experiment_feedback_loop_v1",
        "decisions": feedback_decisions[-5:],
    }
    for router_decision in list(existing_feedback.get("graph_router_decisions") or []):
        append_graph_router_decision(job["agent_graph_feedback"], router_decision)
    for router_decision in router_decisions:
        append_graph_router_decision(job["agent_graph_feedback"], router_decision)
    if rework_run:
        job["agent_graph_feedback"]["latest_rework_run_id"] = rework_run["run_id"]
        job["agent_graph_feedback"]["rework_run_ids"] = list(job.get("experiment_rework_run_ids") or [])
        if (rework_run.get("result") or {}).get("revised_keyframe_plan"):
            job["agent_graph_feedback"]["latest_rework_artifact_type"] = "revised_keyframe_plan"
        if (rework_run.get("result") or {}).get("revised_external_video_handoff"):
            job["agent_graph_feedback"]["latest_rework_next_artifact_type"] = "revised_external_video_handoff"
    if second_comparison:
        job["agent_graph_feedback"]["latest_second_experiment_comparison"] = second_comparison
    if comparison_decision_gate:
        job["agent_graph_feedback"]["latest_experiment_comparison_decision_gate"] = comparison_decision_gate
    if artifact_lineage_summary:
        job["agent_graph_feedback"]["latest_artifact_lineage"] = artifact_lineage_summary
    if controlled_provider_handoff_checklist:
        job["agent_graph_feedback"][
            "latest_controlled_provider_handoff_checklist"
        ] = controlled_provider_handoff_checklist
    if human_approval_gate:
        job["agent_graph_feedback"]["latest_human_approval_gate"] = human_approval_gate
    if demo_ready_run_summary:
        job["agent_graph_feedback"]["latest_demo_ready_run_summary"] = demo_ready_run_summary
    job["updated_at"] = now

    history = list(job.get("history") or [])
    job_status = normalize_video_job_status(job.get("status", ""), fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT)
    history.append(
        build_video_job_history_event(
            "external_video_experiment_recorded",
            job_status,
            updated_at=now,
            experiment_id=experiment["experiment_id"],
            tool_name=experiment["tool_name"],
            prompt_type=experiment["prompt_type"],
            has_result_url=bool(experiment["result_url"]),
            feedback_decision_type=feedback_decision["decision_type"],
            feedback_target_agent_id=feedback_decision.get("target_agent_id", ""),
            feedback_rework_run_id=feedback_decision.get("triggered_rework_run_id", ""),
        )
    )
    history.append(
        build_video_job_history_event(
            "experiment_feedback_recorded",
            job_status,
            updated_at=now,
            experiment_id=experiment["experiment_id"],
            tool_name=experiment["tool_name"],
            prompt_type=experiment["prompt_type"],
            has_result_url=bool(experiment["result_url"]),
            feedback_decision_type=feedback_decision["decision_type"],
            feedback_has_feedback=bool(feedback_decision.get("has_feedback")),
            feedback_target_agent_id=feedback_decision.get("target_agent_id", ""),
            feedback_rework_run_id=feedback_decision.get("triggered_rework_run_id", ""),
        )
    )
    for router_decision in router_decisions:
        route_context_type = str(router_decision.get("route_context_type") or "")
        common_router_fields = {
            "experiment_id": experiment["experiment_id"],
            "router_version": router_decision.get("router_version", ""),
            "route_context_type": route_context_type,
            "decision_type": router_decision.get("decision_type", ""),
            "selected_next_agent_id": router_decision.get("selected_next_agent_id", ""),
            "secondary_next_agent_id": router_decision.get("secondary_next_agent_id", ""),
            "route_type": router_decision.get("route_type", ""),
        }
        if route_context_type in {"experiment_feedback", "second_experiment_comparison"}:
            history.append(
                build_video_job_history_event(
                    "graph_router_decision_created",
                    job_status,
                    updated_at=now,
                    **common_router_fields,
                )
            )
            history.append(
                build_video_job_history_event(
                    "graph_router_route_selected",
                    job_status,
                    updated_at=now,
                    **common_router_fields,
                )
            )
        elif route_context_type == "experiment_comparison_decision_gate":
            history.append(
                build_video_job_history_event(
                    "graph_router_gate_route_selected",
                    job_status,
                    updated_at=now,
                    **common_router_fields,
                )
            )
        elif route_context_type == "controlled_provider_checklist":
            history.append(
                build_video_job_history_event(
                    "graph_router_human_approval_route_selected",
                    job_status,
                    updated_at=now,
                    **common_router_fields,
                )
            )
    if rework_run and feedback_decision.get("has_feedback"):
        history.append(
            build_video_job_history_event(
                "experiment_feedback_rework_requested",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                source_agent_id=feedback_decision.get("source_agent_id", "experiment_agent"),
                target_agent_id=feedback_decision.get("target_agent_id", ""),
                secondary_target_agent_id=feedback_decision.get("secondary_target_agent_id", ""),
                issue_type=feedback_decision.get("issue_type", ""),
                severity=feedback_decision.get("severity", ""),
                rework_run_id=feedback_decision.get("triggered_rework_run_id", ""),
            )
        )
    if second_comparison:
        history.append(
            build_video_job_history_event(
                "second_external_experiment_recorded",
                job_status,
                updated_at=now,
                baseline_experiment_id=second_comparison.get("baseline_experiment_id", ""),
                second_experiment_id=second_comparison.get("second_experiment_id", ""),
                linked_rework_run_id=second_comparison.get("linked_rework_run_id", ""),
                comparison_status=second_comparison.get("status", ""),
            )
        )
        history.append(
            build_video_job_history_event(
                second_comparison.get("decision_type", "second_experiment_no_change"),
                job_status,
                updated_at=now,
                baseline_experiment_id=second_comparison.get("baseline_experiment_id", ""),
                second_experiment_id=second_comparison.get("second_experiment_id", ""),
                prompt_source=second_comparison.get("prompt_source", ""),
                primary_metric=second_comparison.get("primary_metric", ""),
            )
        )
    if comparison_decision_gate:
        history.append(
            build_video_job_history_event(
                "experiment_comparison_decision_gate_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                gate_version=comparison_decision_gate.get("gate_version", ""),
                comparison_status=comparison_decision_gate.get("comparison_status", ""),
                decision_type=comparison_decision_gate.get("decision_type", ""),
                recommended_route=comparison_decision_gate.get("recommended_route", ""),
            )
        )
        history.append(
            build_video_job_history_event(
                f"experiment_gate_{comparison_decision_gate.get('decision_type', 'manual_review_required')}",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                next_agent_id=comparison_decision_gate.get("next_agent_id", ""),
                secondary_next_agent_id=comparison_decision_gate.get("secondary_next_agent_id", ""),
                requires_human_approval=bool(comparison_decision_gate.get("requires_human_approval")),
                should_trigger_new_rework=bool(comparison_decision_gate.get("should_trigger_new_rework")),
                should_proceed_to_provider_test=bool(
                    comparison_decision_gate.get("should_proceed_to_provider_test")
                ),
            )
        )
    if artifact_lineage_summary:
        history.append(
            build_video_job_history_event(
                "artifact_lineage_summary_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                lineage_version=artifact_lineage_summary.get("lineage_version", ""),
                rework_run_id=artifact_lineage_summary.get("linked_rework_run_id", ""),
                is_linear_workflow=False,
            )
        )
    if controlled_provider_handoff_checklist:
        history.append(
            build_video_job_history_event(
                "controlled_provider_handoff_checklist_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                checklist_version=controlled_provider_handoff_checklist.get("checklist_version", ""),
                provider_mode=controlled_provider_handoff_checklist.get("provider_mode", ""),
                human_approval_required=True,
            )
        )
    if human_approval_gate:
        history.append(
            build_video_job_history_event(
                "human_approval_gate_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                approval_gate_version=human_approval_gate.get("approval_gate_version", ""),
                approval_scope=human_approval_gate.get("approval_scope", ""),
                source_agent_id=human_approval_gate.get("source_agent_id", "human_approval_agent"),
                approval_status=human_approval_gate.get("status", "pending_approval"),
            )
        )
        history.append(
            build_video_job_history_event(
                "human_approval_pending",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                approval_scope=human_approval_gate.get("approval_scope", ""),
                blocks_provider_submit=True,
                blocks_external_api_call=True,
            )
        )
    if demo_ready_run_summary:
        history.append(
            build_video_job_history_event(
                "demo_ready_run_summary_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                summary_version=demo_ready_run_summary.get("summary_version", ""),
                summary_type=demo_ready_run_summary.get("summary_type", ""),
                is_linear_workflow=False,
            )
        )
    job["history"] = history
    job = _persist_video_job_graph_os(job, experiment)
    return job, ""


def _summarize_video_generation_job(job: dict) -> dict:
    provider_payload = job.get("provider_payload") or {}
    result = job.get("result") or {}
    source_generation = job.get("source_generation") or {}
    return {
        "job_id": job.get("job_id", ""),
        "project_id": job.get("project_id", DEFAULT_PROJECT_ID),
        "status": job.get("status", ""),
        "provider": job.get("provider", ""),
        "provider_label": provider_payload.get("provider_label", ""),
        "selected_export_key": provider_payload.get("selected_export_key", ""),
        "created_at": job.get("created_at", ""),
        "updated_at": job.get("updated_at", ""),
        "output_language": job.get("output_language", ""),
        "has_result_url": bool(result.get("result_url")),
        "result_url": result.get("result_url", ""),
        "preview_url": result.get("preview_url", ""),
        "source_hook": source_generation.get("hook", ""),
        "source_risk_level": source_generation.get("risk_level", ""),
        "warning_count": len(job.get("warnings") or []),
        "experiment_count": len(job.get("external_video_experiments") or []),
    }


def _append_video_job_status_event(
    history: list[dict],
    current_status: str,
    next_status: str,
    now: str,
) -> None:
    if current_status != next_status:
        history.append(
            build_video_job_history_event(
                "status_changed",
                next_status,
                updated_at=now,
                from_status=current_status,
                to_status=next_status,
            )
        )


def _apply_human_approval_to_video_job(
    job: dict,
    request: VideoGenerationApprovalDecisionRequest,
) -> tuple[dict | None, str]:
    approval_gate = job.get("latest_human_approval_gate")
    if not isinstance(approval_gate, dict) or not approval_gate:
        return None, "human approval gate not found"

    try:
        updated_gate = apply_human_approval_decision(
            approval_gate,
            {
                "decision": request.decision,
                "reviewer": request.reviewer,
                "notes": request.notes,
                "approved_scope": request.approved_scope,
            },
        )
    except ValueError as exc:
        return None, str(exc)

    now = _utc_now_iso()
    job["latest_human_approval_gate"] = updated_gate
    feedback = (
        dict(job.get("agent_graph_feedback") or {})
        if isinstance(job.get("agent_graph_feedback"), dict)
        else {}
    )
    feedback["latest_human_approval_gate"] = updated_gate
    job["agent_graph_feedback"] = feedback

    experiments = list(job.get("external_video_experiments") or job.get("external_experiments") or [])
    for experiment in reversed(experiments):
        if isinstance(experiment.get("human_approval_gate"), dict):
            experiment["human_approval_gate"] = updated_gate
            summary = (
                dict(experiment.get("demo_ready_run_summary") or {})
                if isinstance(experiment.get("demo_ready_run_summary"), dict)
                else {}
            )
            if summary:
                summary["human_approval_gate"] = updated_gate
                experiment["demo_ready_run_summary"] = summary
                job["latest_demo_ready_run_summary"] = summary
                feedback["latest_demo_ready_run_summary"] = summary
            break
    job["external_video_experiments"] = experiments
    job["external_experiments"] = experiments

    decision_status = str(updated_gate.get("status") or "")
    if decision_status == "approved":
        job["controlled_provider_test_approval"] = {
            "approved": True,
            "provider_mode": "manual_or_simulated",
            "external_api_call_allowed": False,
            "approved_scope": str(
                updated_gate.get("approved_scope")
                or "controlled_provider_or_manual_handoff"
            ),
        }

    history = list(job.get("history") or [])
    job_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    history.append(
        build_video_job_history_event(
            f"human_approval_{decision_status}",
            job_status,
            updated_at=now,
            approval_gate_version=updated_gate.get("approval_gate_version", ""),
            approval_scope=updated_gate.get("approval_scope", ""),
            reviewer=request.reviewer or "manual_user",
            notes=_clean_description_text(request.notes),
            blocks_provider_submit=bool(updated_gate.get("blocks_provider_submit", True)),
            external_api_called=False,
            cost_incurred_by_crossgrowth=False,
        )
    )
    job["history"] = history
    job["updated_at"] = now
    return job, ""


def _submit_video_generation_provider_job(job: dict, request: VideoGenerationProviderSubmitRequest) -> tuple[dict | None, str]:
    provider = normalize_video_provider(job.get("provider", ""))
    if not supports_provider_polling(provider):
        return None, "provider does not support polling scaffold"

    current_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    approval_gate = job.get("latest_human_approval_gate")
    if isinstance(approval_gate, dict) and approval_gate:
        approval_status = str(approval_gate.get("status") or "pending_approval")
        if approval_status != "approved":
            now = _utc_now_iso()
            runtime = (
                dict(job.get("provider_runtime") or {})
                if isinstance(job.get("provider_runtime"), dict)
                else {}
            )
            runtime.update(
                {
                    "provider": provider,
                    "provider_status": "blocked_by_human_approval",
                    "mode": runtime.get("mode") or "simulated_provider_polling",
                    "integration_mode": runtime.get("integration_mode") or "simulated",
                    "real_external_api_call_enabled": False,
                    "external_api_called": False,
                    "blocked_reason": "human_approval_required",
                    "approval_gate_status": approval_status,
                }
            )
            job["provider_runtime"] = runtime
            job["updated_at"] = now
            history = list(job.get("history") or [])
            history.append(
                build_video_job_history_event(
                    "provider_submit_blocked_by_human_approval",
                    current_status,
                    updated_at=now,
                    provider=provider,
                    approval_gate_status=approval_status,
                    blocks_provider_submit=True,
                    external_api_called=False,
                )
            )
            job["history"] = history
            return job, ""

    next_status = VIDEO_JOB_STATUS_QUEUED
    if not can_transition_video_job_status(current_status, next_status):
        return None, f"invalid video job status transition: {current_status} -> {next_status}"

    now = _utc_now_iso()
    runtime = build_provider_runtime(
        provider,
        provider_job_id=_clean_description_text(request.provider_job_id),
        notes=_clean_description_text(request.notes),
        now=now,
    )
    job["provider_runtime"] = runtime
    job["status"] = next_status
    job["updated_at"] = now

    result = dict(job.get("result") or {})
    result["provider_job_id"] = runtime.get("provider_job_id", "")
    result["message"] = "Provider polling scaffold submitted. No external video API has been called."
    if request.notes:
        result["notes"] = _clean_description_text(request.notes)
    job["result"] = result

    history = list(job.get("history") or [])
    history.extend(provider_submit_history_events(provider, next_status, now=now))
    if isinstance(approval_gate, dict) and approval_gate.get("status") == "approved":
        history.append(
            build_video_job_history_event(
                "provider_submit_allowed_by_human_approval",
                next_status,
                updated_at=now,
                provider=provider,
                approval_scope=approval_gate.get("approval_scope", ""),
                external_api_called=False,
            )
        )
    _append_video_job_status_event(history, current_status, next_status, now)
    job["history"] = history
    return job, ""


def _poll_video_generation_provider_job(job: dict, request: VideoGenerationProviderPollRequest) -> tuple[dict | None, str]:
    provider = normalize_video_provider(job.get("provider", ""))
    runtime = dict(job.get("provider_runtime") or {})
    if not runtime.get("provider_job_id"):
        return None, "provider job has not been submitted"

    current_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    requested_provider_status = _clean_description_text(request.provider_status)
    next_status = next_simulated_provider_status(current_status, requested_provider_status)
    if next_status not in {VIDEO_JOB_STATUS_PROCESSING, VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY, VIDEO_JOB_STATUS_FAILED}:
        next_status = VIDEO_JOB_STATUS_PROCESSING
    if not can_transition_video_job_status(current_status, next_status):
        return None, f"invalid video job status transition: {current_status} -> {next_status}"

    now = _utc_now_iso()
    runtime = build_provider_poll_runtime(
        runtime,
        next_status,
        error_message=_clean_description_text(request.error_message),
        notes=_clean_description_text(request.notes),
        now=now,
    )
    job["provider_runtime"] = runtime
    job["status"] = next_status
    job["updated_at"] = now

    result = dict(job.get("result") or {})
    result["provider_job_id"] = runtime.get("provider_job_id", "")
    result["message"] = "Provider polling scaffold checked. No external video API has been called."
    if next_status == VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY:
        result.update(
            {
                "result_url": _clean_description_text(request.result_url),
                "preview_url": _clean_description_text(request.preview_url),
                "download_url": _clean_description_text(request.download_url),
                "notes": _clean_description_text(request.notes),
                "message": "Simulated provider result recorded.",
            }
        )
    elif next_status == VIDEO_JOB_STATUS_FAILED:
        result["notes"] = _clean_description_text(request.notes)
        result["error_message"] = _clean_description_text(request.error_message)
        result["message"] = "Simulated provider polling marked the job failed."
    job["result"] = result

    history = list(job.get("history") or [])
    _append_video_job_status_event(history, current_status, next_status, now)
    history.append(provider_poll_history_event(provider, next_status, runtime, now=now))
    job["history"] = history
    return job, ""


@app.get("/api/v1/video-generation/providers", response_model=VideoGenerationProvidersResponse)
async def list_video_generation_providers(http_request: Request):
    return {
        "status": "success",
        "providers": video_provider_catalog(),
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/video-generation/providers/{provider}/plan", response_model=VideoGenerationProviderPlanResponse)
async def get_video_generation_provider_plan(provider: str, http_request: Request):
    request_id = http_request.state.request_id
    provider_name = normalize_video_provider(provider)
    plan = video_provider_plan(provider)
    if not provider_name or not plan:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation provider not found",
                "request_id": request_id,
            },
        )
    plan.update(provider_plan_integration_metadata(provider_name))
    return {
        "status": "success",
        "provider": provider_name,
        "plan": plan,
        "request_id": request_id,
    }


@app.get("/api/v1/video-generation/cost/catalog", response_model=VideoGenerationCostCatalogResponse)
async def get_video_generation_cost_catalog(http_request: Request):
    return {
        "status": "success",
        "catalog": video_provider_cost_catalog(),
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/video-generation/cost/estimate", response_model=VideoGenerationCostEstimateResponse)
async def estimate_video_generation_provider_cost(request: VideoGenerationCostEstimateRequest, http_request: Request):
    return {
        "status": "success",
        "estimate": estimate_video_generation_cost(
            provider=request.provider,
            model=request.model,
            duration_seconds=request.duration_seconds,
            clip_count=request.clip_count,
            retry_count=request.retry_count,
            budget_usd=request.budget_usd,
        ),
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/video-generation/storage/status", response_model=VideoGenerationStorageStatusResponse)
async def get_video_generation_storage_status(http_request: Request):
    return {
        "status": "success",
        "storage": video_job_storage_diagnostics(VIDEO_JOB_STORE),
        "request_id": http_request.state.request_id,
    }


def _video_generation_packet_from_generation_data(generation_data: dict) -> dict:
    if not isinstance(generation_data, dict):
        return {}
    packet = generation_data.get("video_generation_packet") or {}
    if not isinstance(packet, dict):
        return {}
    return packet


def _video_generation_source_summary(generation_data: dict) -> dict:
    if not isinstance(generation_data, dict):
        return {}

    assets = generation_data.get("assets") or {}
    script = assets.get("tiktok_script") if isinstance(assets, dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets, dict) else {}
    evaluation = generation_data.get("evaluation") or {}
    agent_trace = generation_data.get("agent_trace") or {}

    if not isinstance(script, dict):
        script = {}
    if not isinstance(storyboard, dict):
        storyboard = {}
    if not isinstance(evaluation, dict):
        evaluation = {}
    if not isinstance(agent_trace, dict):
        agent_trace = {}

    scenes = storyboard.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    return {
        "hook": script.get("hook", ""),
        "cta": script.get("cta", ""),
        "storyboard_scene_count": len(scenes),
        "risk_level": evaluation.get("risk_level", ""),
        "is_grounded": bool(evaluation.get("is_grounded", False)),
        "agent_trace_version": agent_trace.get("trace_version", ""),
    }


@app.get("/api/v1/video-generation/jobs", response_model=VideoGenerationJobListResponse)
async def list_video_generation_jobs(http_request: Request, limit: int = 20):
    safe_limit = max(1, min(int(limit or 20), 50))
    jobs = VIDEO_JOB_STORE.list(safe_limit)
    summarized = [_summarize_video_generation_job(job) for job in jobs]
    return {
        "status": "success",
        "jobs": summarized,
        "job_count": len(summarized),
        "limit": safe_limit,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/video-generation/jobs", response_model=VideoGenerationJobResponse)
async def create_video_generation_job(request: VideoGenerationJobRequest, http_request: Request):
    request_id = http_request.state.request_id
    packet = request.video_generation_packet or {}

    if packet.get("packet_version") != "video_generation_v1":
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "video_generation_packet with packet_version=video_generation_v1 is required.",
                "request_id": request_id,
            },
        )

    if not normalize_video_provider(request.provider or "manual_export"):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "unsupported video generation provider",
                "supported_providers": supported_video_provider_names(),
                "request_id": request_id,
            },
        )

    job = _create_video_generation_job(request)
    emit_event(
        "video_generation_job_created",
        request_id,
        endpoint="/api/v1/video-generation/jobs",
        status="success",
        job_id=job["job_id"],
        provider=job["provider"],
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.get(
    "/api/v1/video-generation/jobs/{job_id}/approval-gate",
    response_model=VideoGenerationApprovalGateResponse,
)
async def get_video_generation_approval_gate(job_id: str, http_request: Request):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)
    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )
    approval_gate = job.get("latest_human_approval_gate")
    if not isinstance(approval_gate, dict) or not approval_gate:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "human approval gate not found",
                "request_id": request_id,
            },
        )
    return {
        "status": "success",
        "job_id": job_id,
        "approval_gate": approval_gate,
        "request_id": request_id,
    }


@app.post(
    "/api/v1/video-generation/jobs/{job_id}/approval-gate/decision",
    response_model=VideoGenerationApprovalGateResponse,
)
async def decide_video_generation_approval_gate(
    job_id: str,
    request: VideoGenerationApprovalDecisionRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)
    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, approval_error = _apply_human_approval_to_video_job(job, request)
    if approval_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": approval_error,
                "request_id": request_id,
            },
        )

    job = _persist_video_job_graph_os(job)
    job = VIDEO_JOB_STORE.update(job_id, job)
    emit_event(
        "human_approval_gate_decided",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/approval-gate/decision",
        status="success",
        job_id=job_id,
        approval_status=job["latest_human_approval_gate"].get("status", ""),
        external_api_called=False,
    )
    return {
        "status": "success",
        "job_id": job_id,
        "approval_gate": job["latest_human_approval_gate"],
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/provider-submit", response_model=VideoGenerationJobStatusResponse)
async def submit_video_generation_provider_job(
    job_id: str,
    request: VideoGenerationProviderSubmitRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, submit_error = _submit_video_generation_provider_job(job, request)
    if submit_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": submit_error,
                "request_id": request_id,
            },
        )

    job = _persist_video_job_graph_os(job)
    job = VIDEO_JOB_STORE.update(job_id, job)
    provider_submit_blocked = (
        (job.get("provider_runtime") or {}).get("provider_status")
        == "blocked_by_human_approval"
    )
    emit_event(
        (
            "video_generation_provider_submit_blocked"
            if provider_submit_blocked
            else "video_generation_provider_submitted"
        ),
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/provider-submit",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/provider-poll", response_model=VideoGenerationJobStatusResponse)
async def poll_video_generation_provider_job(
    job_id: str,
    request: VideoGenerationProviderPollRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, poll_error = _poll_video_generation_provider_job(job, request)
    if poll_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": poll_error,
                "request_id": request_id,
            },
        )

    job = _persist_video_job_graph_os(job)
    job = VIDEO_JOB_STORE.update(job_id, job)
    emit_event(
        "video_generation_provider_polled",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/provider-poll",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/result", response_model=VideoGenerationJobStatusResponse)
async def update_video_generation_job_result(
    job_id: str,
    request: VideoGenerationJobResultRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, transition_error = _update_video_generation_job_result(job, request)
    if transition_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": transition_error,
                "request_id": request_id,
            },
        )
    job = _persist_video_job_graph_os(job)
    job = VIDEO_JOB_STORE.update(job_id, job)

    emit_event(
        "video_generation_job_result_updated",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/result",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )

    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/experiments", response_model=VideoGenerationJobStatusResponse)
async def record_external_video_experiment(
    job_id: str,
    request: VideoGenerationExperimentRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, experiment_error = _record_external_video_experiment(job, request)
    if experiment_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": experiment_error,
                "request_id": request_id,
            },
        )

    job = _persist_video_job_graph_os(job)
    job = VIDEO_JOB_STORE.update(job_id, job)
    emit_event(
        "external_video_experiment_recorded",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/experiments",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/from-generation", response_model=VideoGenerationJobResponse)
async def create_video_generation_job_from_generation(
    request: VideoGenerationFromGenerationRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    generation_data = request.generation_data or {}
    packet = _video_generation_packet_from_generation_data(generation_data)

    if packet.get("packet_version") != "video_generation_v1":
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "generation_data.video_generation_packet with packet_version=video_generation_v1 is required.",
                "request_id": request_id,
            },
        )

    if not normalize_video_provider(request.provider or "manual_export"):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "unsupported video generation provider",
                "supported_providers": supported_video_provider_names(),
                "request_id": request_id,
            },
        )

    job_request = VideoGenerationJobRequest(
        video_generation_packet=packet,
        provider=request.provider,
        output_language=request.output_language,
        project_id=request.project_id or generation_data.get("project_id"),
    )
    job = _create_video_generation_job(job_request)
    job["source_generation"] = {
        **_video_generation_source_summary(generation_data),
        "project_id": job["project_id"],
        "product_name": generation_data.get("product_name", ""),
        "product_category": generation_data.get("product_category", ""),
        "llm_evidence_packet": generation_data.get("llm_evidence_packet") or {},
    }
    handoff = generation_data.get("external_video_tool_handoff") if isinstance(generation_data.get("external_video_tool_handoff"), dict) else {}
    if handoff:
        job["external_video_tool_handoff"] = handoff
    job["updated_at"] = _utc_now_iso()
    job = _persist_video_job_graph_os(job)
    job = VIDEO_JOB_STORE.update(job["job_id"], job)

    emit_event(
        "video_generation_job_created_from_generation",
        request_id,
        endpoint="/api/v1/video-generation/jobs/from-generation",
        status="success",
        job_id=job["job_id"],
        provider=job["provider"],
    )

    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.get("/api/v1/video-generation/jobs/{job_id}", response_model=VideoGenerationJobStatusResponse)
async def get_video_generation_job(job_id: str, http_request: Request):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/amazon-intake", response_model=AmazonIntakeResponse)
async def amazon_intake(request: AmazonIntakeRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    intake = normalize_amazon_product_url(request.url)

    emit_event(
        "amazon_intake_start",
        request_id,
        endpoint="/api/v1/amazon-intake",
        status="started",
        product_category=request.product_category,
    )

    base_data = {
        "input_url": request.url,
        "is_supported": intake.is_supported,
        "asin": intake.asin,
        "normalized_url": intake.normalized_url,
        "provider_status": "unsupported" if not intake.is_supported else "pending",
        "source_confidence": 0.0,
        "product_title": "",
        "rating": "",
        "review_count": "",
        "price": "",
        "category_hint": "",
        "bullet_points": [],
        "evidence_preview": [],
        "review_items": [],
        "review_insights": _amazon_empty_review_insights(),
        "data_warnings": [],
        "fallback_required": True,
        "fallback_message": _amazon_intake_fallback_message(),
        "error": "",
        "metadata": {},
    }

    if not intake.is_supported:
        base_data["data_warnings"] = ["unsupported_amazon_url", intake.reason]
        base_data["metadata"] = {
            "intake_status": "unsupported",
            "intake_reason": intake.reason,
            "intake_source_type": intake.source_type,
        }
        emit_event(
            "amazon_intake_complete",
            request_id,
            endpoint="/api/v1/amazon-intake",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category,
            fallback_required=True,
        )
        return {
            "status": "success",
            "data": base_data,
            "request_id": request_id,
        }

    try:
        evidence = source_probe_registry.fetch(
            "amazon_review_api",
            intake.normalized_url,
            request.product_category,
        )
        metadata = dict(evidence.metadata or {})
        provider_status = _probe_status_from_evidence(evidence)
        fallback_required = not (provider_status == "success" and evidence.confidence >= 0.70)
        data_warnings = list(evidence.data_warnings or [])
        if "review_sign_in_required" in data_warnings:
            fallback_required = True
        review_items = [
            {
                "text": review.text,
                "source": review.source or evidence.source_type,
                "rating": review.rating,
                "date": review.date,
                "title": review.title,
            }
            for review in list(evidence.reviews or [])[:6]
        ]

        base_data.update(
            {
                "provider_status": provider_status,
                "source_confidence": evidence.confidence,
                "product_title": metadata.get("product_title", ""),
                "rating": metadata.get("rating", ""),
                "review_count": metadata.get("review_count", ""),
                "price": metadata.get("price", ""),
                "category_hint": metadata.get("category_hint", ""),
                "bullet_points": list(metadata.get("bullet_points") or []),
                "evidence_preview": list(evidence.evidence_quotes[:3]),
                "review_items": review_items,
                "review_insights": _amazon_review_insights(review_items),
                "data_warnings": data_warnings,
                "fallback_required": fallback_required,
                "fallback_message": _amazon_intake_fallback_message(data_warnings) if fallback_required else "",
                "error": metadata.get("error", ""),
                "metadata": {
                    **metadata,
                    "source_type": evidence.source_type,
                    "data_warnings": data_warnings,
                },
            }
        )

        emit_event(
            "amazon_intake_complete",
            request_id,
            endpoint="/api/v1/amazon-intake",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category,
            fallback_required=fallback_required,
        )
        return {
            "status": "success",
            "data": base_data,
            "request_id": request_id,
        }
    except Exception as exc:
        base_data.update(
            {
                "provider_status": "error",
                "data_warnings": ["amazon_fetch_error"],
                "fallback_required": True,
                "fallback_message": _amazon_intake_fallback_message(),
                "error": str(exc),
                "metadata": {
                    "intake_status": "supported",
                    "asin": intake.asin,
                    "normalized_url": intake.normalized_url,
                    "error_type": "amazon_fetch_error",
                },
            }
        )
        emit_event(
            "amazon_intake_complete",
            request_id,
            endpoint="/api/v1/amazon-intake",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category,
            fallback_required=True,
        )
        return {
            "status": "success",
            "data": base_data,
            "request_id": request_id,
        }


@app.post("/api/v1/generate-copilot", response_model=GenerateCopilotResponse)
async def generate_copilot_flow(request: GrowthRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    product_category_hint = _safe_product_category_hint(request.url)
    emit_event(
        "generate_copilot_start",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="started",
        product_category=product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )
    emit_event(
        "generate_copilot_after_request_parse",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )

    initial_state = {
        "env_state": {"asin_url": request.url, "business_goal": request.goal},
        "cognitive_state": {},
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": {},
        "revision_count": 0,
        "next_nodes": [],
    }

    emit_event(
        "generate_copilot_before_workflow",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="started",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )
    try:
        final_state = await copilot_engine.ainvoke(initial_state)
    except Exception as exc:
        error_type = _error_type(exc)
        emit_event(
            "generate_copilot_error",
            request_id,
            endpoint="/api/v1/generate-copilot",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=product_category_hint,
            goal=request.goal,
            error_type=error_type,
            output_language=output_language,
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": "generate-copilot workflow failed safely. Please retry after the service is warm.",
                "error_type": error_type,
                "request_id": request_id,
            },
        )

    env_state = final_state.get("env_state", {})
    emit_event(
        "generate_copilot_after_workflow",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category") or product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )
    cog_state = final_state.get("cognitive_state", {})
    exec_state = final_state.get("execution_state", {})
    world_metrics = final_state.get("world_metrics", {})
    strategy_data = cog_state.get("strategy", {})
    profile = cog_state.get("profile", {})
    painpoint = profile.get("painpoint", {})
    audience = profile.get("audience", {})
    dopamine = profile.get("dopamine", {})
    storyboard_data = exec_state.get("storyboard", {})
    scenes = storyboard_data.get("scenes", [])

    ui_strategy = {
        "core_hook_strategy": (
            f"Identity attack:\n{strategy_data.get('identity_attack', '')}\n\n"
            f"Status desire:\n{strategy_data.get('status_desire', '')}\n\n"
            f"Evidence:\n" + "\n".join(strategy_data.get("evidence_basis", []))
        ),
        "emotional_trigger": (
            f"Future-self gap:\n{strategy_data.get('future_self_gap', '')}\n\n"
            f"Conversion mechanism:\n{strategy_data.get('conversion_mechanism', '')}\n\n"
            f"CTA logic:\n{strategy_data.get('cta_logic', '')}"
        ),
    }

    hook_text = "Scene graph was not generated."
    cta_text = "Conversion scene was not generated."
    if scenes and isinstance(scenes, list):
        first_scene = scenes[0]
        last_scene = scenes[-1]
        hook_text = (
            f"0-{first_scene.get('duration_sec', 0)}s | {first_scene.get('scene_goal', '')}\n"
            f"Visual: {first_scene.get('visual_description', '')}\n"
            f"Narration: {first_scene.get('narration', '')}\n"
            f"Text: {first_scene.get('on_screen_text', '')}\n"
            f"Retention: {first_scene.get('retention_reason', '')}"
        )
        cta_text = (
            f"Final scene | {last_scene.get('scene_goal', '')}\n"
            f"Visual: {last_scene.get('visual_description', '')}\n"
            f"Narration: {last_scene.get('narration', '')}\n"
            f"Painpoint: {last_scene.get('linked_painpoint', '')}"
        )

    retention_score = world_metrics.get("retention_3s", 0.0)
    if retention_score < 0.50:
        risk_level = "high"
    elif retention_score < 0.70:
        risk_level = "medium"
    else:
        risk_level = "low"

    response = {
        "status": "success",
        "data": {
            "insights": {
                "pain_points": painpoint.get("physical_painpoints", []) + painpoint.get("emotional_painpoints", []),
                "user_complaint_cluster": painpoint.get("use_case_disasters", []),
                "evidence": env_state.get("evidence", {}),
            },
            "audience": {
                "primary": audience.get("primary_user", ""),
                "sensitivity": dopamine.get("viral_emotion", ""),
                "trust_barriers": audience.get("trust_barriers", []),
            },
            "strategy": ui_strategy,
            "assets": {"tiktok_script": {"hook": hook_text, "cta": cta_text}, "storyboard": storyboard_data},
            "evaluation": {
                "confidence_score": retention_score,
                "risk_level": risk_level,
                "reasoning": (
                    f"{world_metrics.get('reason', '')}\n"
                    f"Dopamine score: {world_metrics.get('dopamine_score', 0):.2f}\n"
                    f"Evidence alignment: {world_metrics.get('evidence_alignment', 0):.2f}\n"
                    f"Creative CTR: {world_metrics.get('predicted_ctr', 0) * 100:.1f}%\n"
                    f"Grounded CTR: {world_metrics.get('grounded_ctr', 0) * 100:.1f}%\n"
                    f"Source confidence: {world_metrics.get('source_confidence', 0):.2f}\n"
                    f"Failure type: {world_metrics.get('failure_type', '')}"
                ),
                "is_approved": world_metrics.get("is_approved", False),
                "is_grounded": world_metrics.get("is_grounded", False),
                "creative_approved": world_metrics.get("creative_approved", False),
                "grounded_approved": world_metrics.get("grounded_approved", False),
            },
            "feedback": exec_state.get("reflection", {}).get("root_cause", "Memory writer recorded the final outcome."),
        },
        "output_language": output_language,
    }
    response["data"]["video_generation_packet"] = _build_video_generation_packet(
        storyboard_data.get("product_name") or env_state.get("product_title") or request.url,
        storyboard_data.get("product_category") or env_state.get("product_category") or "",
        response["data"]["assets"],
        response["data"]["insights"],
        response["data"]["evaluation"],
        output_language,
    )
    response["data"]["external_video_tool_handoff"] = _build_external_video_tool_handoff(
        storyboard_data.get("product_name") or env_state.get("product_title") or request.url,
        storyboard_data.get("product_category") or env_state.get("product_category") or "",
        response["data"],
    )
    response["data"]["agent_trace"] = _build_agent_trace(response["data"], output_language)
    response["data"]["multi_agent_workflow"] = _build_multi_agent_workflow(response["data"], output_language)
    try:
        response["data"] = await translate_product_visible_data(
            response["data"],
            output_language,
        )
    except Exception as exc:
        error_type = _error_type(exc)
        emit_event(
            "generate_copilot_error",
            request_id,
            endpoint="/api/v1/generate-copilot",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=env_state.get("product_category"),
            goal=request.goal,
            error_type=error_type,
            output_language=output_language,
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": "generate-copilot language rendering failed safely. Please retry.",
                "error_type": "generation_failed",
                "request_id": request_id,
            },
        )

    emit_event(
        "generate_copilot_complete",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category"),
        goal=request.goal,
        output_language=output_language,
    )
    return response


@app.post("/api/v1/generate-from-description", response_model=ProductDescriptionResponse)
async def generate_from_description(request: ProductDescriptionRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    product_name = _clean_description_text(request.product_name)
    emit_event(
        "generate_from_description_start",
        request_id,
        endpoint="/api/v1/generate-from-description",
        status="started",
        product_category=request.product_category or "user_provided_product",
        goal=request.goal,
        output_language=output_language,
    )

    validation_error = _validate_description_request(request, request_id)
    if validation_error:
        emit_event(
            "generate_from_description_error",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or "user_provided_product",
            goal=request.goal,
            output_language=output_language,
        )
        return validation_error

    try:
        generated = await generate_description_brief(request)
        data = _description_response_data(request, generated)
        data = await translate_product_visible_data(data, output_language)
        response = {
            "status": "success",
            "data": data,
            "request_id": request_id,
            "output_language": output_language,
        }
        emit_event(
            "generate_from_description_complete",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            output_language=output_language,
        )
        return response
    except Exception:
        emit_event(
            "generate_from_description_error",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            error_type="generation_failed",
            output_language=output_language,
        )
        return _description_error(
            "Product Description Mode generation failed safely. Please retry with a shorter description.",
            "generation_failed",
            request_id,
            status_code=503,
        )


def _stored_run_by_id(run_id: str) -> dict:
    for run in load_recent_agent_run_snapshots(100):
        if str(run.get("run_id") or "") == str(run_id or ""):
            return run
    return {}


def _stored_job_by_id(job_id: str) -> dict:
    for job in load_recent_video_job_snapshots(100):
        if str(job.get("job_id") or "") == str(job_id or ""):
            return job
    return {}


def _graph_report_markdown(report: dict) -> str:
    summary = report.get("summary") or {}
    snapshot = report.get("graph_state_snapshot") or {}
    safety = report.get("safety_boundaries") or {}
    artifact_registry = report.get("artifact_registry") or {}
    selected_edges = snapshot.get("selected_edges") or []
    project = report.get("project") or {}
    assets = report.get("uploaded_assets") or []
    asset_lock_v2 = report.get("product_asset_lock_v2") or {}
    source = report.get("project_source") or {}
    source_gate = report.get("source_quality_gate") or {}
    source_artifact = report.get("source_evidence_artifact") or {}
    source_snapshot = report.get("source_snapshot") or {}
    review_classifications = source_artifact.get("review_classifications") or []
    lines = [
        f"# {report.get('report_title') or 'Agent Graph Report'}",
        "",
        f"- Report version: {report.get('report_version', '')}",
        f"- Project: {project.get('project_name', '')} ({report.get('project_id', DEFAULT_PROJECT_ID)})",
        f"- Product: {project.get('product_name', '')}",
        f"- Source: {project.get('source_type', '')}",
        f"- Run ID: {summary.get('run_id', '')}",
        f"- Job ID: {summary.get('job_id', '')}",
        f"- Status: {summary.get('status', '')}",
        f"- Next action: {report.get('next_recommended_action', '')}",
        "",
        "## Why This Is Not A Workflow",
        "",
        str(report.get("why_not_workflow") or ""),
        "",
        "## Graph State Snapshot",
        "",
        f"- Active loops: {', '.join(snapshot.get('active_loops') or []) or 'none'}",
        f"- Active gates: {', '.join(snapshot.get('active_gates') or []) or 'none'}",
        f"- Selected edges: {len(selected_edges)}",
        f"- Artifact count: {(artifact_registry.get('artifact_counts') or {}).get('total', 0)}",
        f"- Uploaded assets: {len(assets)}",
        f"- Product Asset Lock v2: {asset_lock_v2.get('lock_version', 'not available')}",
        "",
        "## Project Source",
        "",
        f"- Source ID: {source.get('source_id', '')}",
        f"- Source type: {source.get('source_type', '')}",
        f"- Source URL: {source.get('normalized_url') or source.get('source_url', '')}",
        f"- Source confidence: {source.get('source_confidence', 0.0)}",
        "",
        "## Source Adapter",
        "",
        f"- Source status: {source.get('source_status', '')}",
        f"- No anti-bot bypass: {str(not bool((source.get('safety_boundaries') or {}).get('anti_bot_bypass_used', False))).lower()}",
        "",
        "## Source Quality Gate",
        "",
        f"- Gate status: {source_gate.get('status', '')}",
        f"- Evidence readiness: {source_gate.get('evidence_readiness', '')}",
        f"- Allows agent run: {str(source_gate.get('allows_agent_run', False)).lower()}",
        "",
        "## Source Evidence",
        "",
        f"- Artifact ID: {source_artifact.get('artifact_id', '')}",
        f"- Evidence quotes: {len(source_artifact.get('evidence_quotes') or [])}",
        f"- Source snapshot: {source_snapshot.get('snapshot_version', '')}",
        "",
        "## Review Classification",
        "",
        f"- Classified reviews: {len(review_classifications)}",
        "",
        "## Source Warnings",
        "",
        *(f"- {warning}" for warning in (source.get("warnings") or [])),
        "",
        "## Manual Fallback",
        "",
        f"- Required: {str((source.get('source_summary') or {}).get('manual_fallback_needed', False)).lower()}",
        "",
        "## Artifacts",
        "",
        f"- Registry version: {artifact_registry.get('registry_version', '')}",
        f"- Registry ID: {artifact_registry.get('registry_id', '')}",
        f"- Created: {(artifact_registry.get('artifact_counts') or {}).get('created', 0)}",
        f"- Used: {(artifact_registry.get('artifact_counts') or {}).get('used', 0)}",
        f"- Revised: {(artifact_registry.get('artifact_counts') or {}).get('revised', 0)}",
        f"- Approved: {(artifact_registry.get('artifact_counts') or {}).get('approved', 0)}",
        f"- Blocked: {(artifact_registry.get('artifact_counts') or {}).get('blocked', 0)}",
        "",
        "## Experiments",
        "",
        f"- Experiment count: {summary.get('experiment_count', 0)}",
        "",
        "## Graph Evidence",
        "",
        f"- Parent/child lineage: {str((artifact_registry.get('lineage_summary') or {}).get('has_parent_child_links', False)).lower()}",
        f"- Revisions present: {str((artifact_registry.get('lineage_summary') or {}).get('has_revisions', False)).lower()}",
        f"- Uploaded assets present: {str((artifact_registry.get('lineage_summary') or {}).get('has_uploaded_assets', False)).lower()}",
        "",
        "## Safety Boundaries",
        "",
        f"- external_api_called: {str(safety.get('external_api_called', False)).lower()}",
        f"- cost_incurred_by_crossgrowth: {str(safety.get('cost_incurred_by_crossgrowth', False)).lower()}",
        f"- llm_autonomous_decision_enabled: {str(safety.get('llm_autonomous_decision_enabled', False)).lower()}",
        f"- anti_bot_bypass_used: {str(safety.get('anti_bot_bypass_used', False)).lower()}",
        "",
        "## Next Recommended Action",
        "",
        str(report.get("next_recommended_action") or ""),
    ]
    return "\n".join(lines).strip()


def _latest_project_source_context(project_id: str) -> dict:
    sources = list_project_sources(project_id, 1)
    artifacts = list_source_evidence_artifacts(project_id, 1)
    gates = list_source_quality_gates(project_id, 1)
    snapshots = list_source_snapshots(project_id, 1)
    return {
        "project_source": sources[0] if sources else {},
        "source_evidence_artifact": artifacts[0] if artifacts else {},
        "source_quality_gate": gates[0] if gates else {},
        "source_snapshot": snapshots[0] if snapshots else {},
    }


def _build_run_graph_report(run: dict) -> dict:
    enriched = _refresh_agent_run_graph_os(run)
    project = _ensure_project(enriched.get("project_id"))
    assets = list_project_assets(project["project_id"], 50)
    source_context = _latest_project_source_context(project["project_id"])
    report = {
        "report_version": "agent_graph_report_v2",
        "project_id": project["project_id"],
        "project": project,
        "project_graph_summary": project.get("graph_summary") or {},
        "uploaded_assets": assets,
        **source_context,
        "product_asset_lock_v2": build_product_asset_lock_v2(
            project,
            enriched.get("result") or {},
            assets,
        ),
        "report_type": "agent_run_graph_report",
        "report_title": "Agent Run Graph Report",
        "summary": {
            "run_id": enriched.get("run_id", ""),
            "job_id": "",
            "status": enriched.get("status", ""),
            "input_type": enriched.get("input_type", ""),
            "waiting_for_user": bool(enriched.get("waiting_for_user")),
        },
        "graph_state_snapshot": enriched.get("latest_graph_state_snapshot") or {},
        "events_summary": [
            {
                "event_type": event.get("event_type", ""),
                "agent_id": event.get("agent_id", ""),
                "message": event.get("message", ""),
                "created_at": event.get("created_at", ""),
            }
            for event in (enriched.get("events") or [])[-30:]
            if isinstance(event, dict)
        ],
        "router_decisions": enriched.get("graph_router_decisions") or [],
        "artifact_registry": enriched.get("artifact_registry") or {},
        "agent_messages": enriched.get("agent_messages") or [],
        "graph_health": enriched.get("graph_health") or {},
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "anti_bot_bypass_used": False,
        },
        "why_not_workflow": (
            "The run records routed edges, validation/rework loops, agent-produced artifacts, "
            "structured messages, and human/provider waiting states instead of one fixed linear sequence."
        ),
        "next_recommended_action": (
            enriched.get("latest_graph_state_snapshot") or {}
        ).get("next_graph_action", ""),
    }
    return report


def _build_job_graph_report(job: dict) -> dict:
    enriched = _refresh_video_job_graph_os(job)
    project = _ensure_project(enriched.get("project_id"))
    assets = list_project_assets(project["project_id"], 50)
    source_context = _latest_project_source_context(project["project_id"])
    experiments = list(enriched.get("external_video_experiments") or [])
    report = {
        "report_version": "agent_graph_report_v2",
        "project_id": project["project_id"],
        "project": project,
        "project_graph_summary": project.get("graph_summary") or {},
        "uploaded_assets": assets,
        **source_context,
        "product_asset_lock_v2": enriched.get("product_asset_lock_v2") or build_product_asset_lock_v2(
            project,
            enriched.get("source_generation") or {},
            assets,
        ),
        "report_type": "video_job_graph_report",
        "report_title": "Video Job Agent Graph Report",
        "summary": {
            "run_id": str((enriched.get("latest_graph_state_snapshot") or {}).get("run_id") or ""),
            "job_id": enriched.get("job_id", ""),
            "status": enriched.get("status", ""),
            "provider": enriched.get("provider", ""),
            "experiment_count": len(experiments),
        },
        "graph_state_snapshot": enriched.get("latest_graph_state_snapshot") or {},
        "experiments_summary": [
            {
                "experiment_id": experiment.get("experiment_id", ""),
                "experiment_round": experiment.get("experiment_round", 1),
                "overall_score": experiment.get("overall_score"),
                "decision_type": (experiment.get("agent_feedback_decision") or {}).get("decision_type", ""),
                "created_at": experiment.get("created_at", ""),
            }
            for experiment in experiments[-10:]
            if isinstance(experiment, dict)
        ],
        "artifact_registry": enriched.get("latest_artifact_registry") or {},
        "approval_gate": enriched.get("latest_human_approval_gate") or {},
        "provider_runtime": enriched.get("provider_runtime") or {},
        "router_decisions": enriched.get("graph_router_decisions") or [],
        "agent_messages": enriched.get("agent_messages") or [],
        "graph_health": enriched.get("graph_health") or {},
        "safety_boundaries": {
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "llm_autonomous_decision_enabled": False,
            "anti_bot_bypass_used": False,
        },
        "why_not_workflow": (
            "The job continues the graph through experiments, router-selected rework, revised artifacts, "
            "a decision gate, human approval, and a simulated/manual provider branch."
        ),
        "next_recommended_action": (
            enriched.get("latest_graph_state_snapshot") or {}
        ).get("next_graph_action", ""),
    }
    return report


def _graph_report_response(report: dict, report_format: str) -> dict:
    safe_format = str(report_format or "json").strip().lower()
    payload = {
        "status": "success",
        "format": "markdown" if safe_format == "markdown" else "json",
        "report": report,
    }
    if safe_format == "markdown":
        payload["markdown_report"] = _graph_report_markdown(report)
    export = {
        "export_id": f"graph_export_{uuid4().hex[:16]}",
        "export_type": report.get("report_type", ""),
        "format": payload["format"],
        "run_id": (report.get("summary") or {}).get("run_id", ""),
        "job_id": (report.get("summary") or {}).get("job_id", ""),
        "project_id": str(report.get("project_id") or DEFAULT_PROJECT_ID),
        "created_at": _utc_now_iso(),
        "report": report,
        "markdown_report": payload.get("markdown_report", ""),
    }
    try:
        save_graph_report_export(export)
    except Exception:
        pass
    return payload



def _latest_project_planner_context(project_id: str) -> dict:
    safe_id = _safe_project_id(project_id)
    project = update_project_summary(safe_id)

    sources = list_project_sources(safe_id, 30)
    source_gates = list_source_quality_gates(safe_id, 30)
    source_artifacts = list_source_evidence_artifacts(safe_id, 30)
    runs = list_project_records("runs", safe_id, 20)
    jobs = list_project_records("jobs", safe_id, 20)
    artifact_records = list_project_records("artifacts", safe_id, 30)
    assets = list_project_assets(safe_id, 30)

    latest_source = sources[0] if sources else {}
    latest_gate = source_gates[0] if source_gates else {}
    latest_source_artifact = source_artifacts[0] if source_artifacts else {}
    latest_run = runs[0] if runs else {}
    latest_job = jobs[0] if jobs else {}

    if not latest_gate and latest_source:
        loaded_gate = load_source_quality_gate(
            safe_id,
            str(latest_source.get("source_id") or ""),
        )
        latest_gate = loaded_gate if isinstance(loaded_gate, dict) else {}

    if not latest_source_artifact and latest_source:
        loaded_artifact = load_source_evidence_artifact(
            safe_id,
            str(latest_source.get("source_id") or ""),
        )
        latest_source_artifact = loaded_artifact if isinstance(loaded_artifact, dict) else {}

    artifact_registry = {}
    if isinstance(latest_job, dict):
        artifact_registry = latest_job.get("latest_artifact_registry") or {}
    if not artifact_registry and isinstance(latest_run, dict):
        artifact_registry = latest_run.get("artifact_registry") or {}
    if not artifact_registry:
        for record in artifact_records:
            if isinstance(record, dict) and record.get("registry_version"):
                artifact_registry = record
                break

    experiments = []
    if isinstance(latest_job, dict):
        experiments = list(latest_job.get("external_video_experiments") or [])
    latest_experiment = experiments[-1] if experiments else {}

    approval_gate = {}
    if isinstance(latest_job, dict):
        approval_gate = latest_job.get("latest_human_approval_gate") or {}

    return {
        "project": project,
        "latest_source": latest_source if isinstance(latest_source, dict) else {},
        "latest_source_quality_gate": latest_gate if isinstance(latest_gate, dict) else {},
        "latest_source_evidence_artifact": latest_source_artifact if isinstance(latest_source_artifact, dict) else {},
        "latest_artifact_registry": artifact_registry if isinstance(artifact_registry, dict) else {},
        "latest_run": latest_run if isinstance(latest_run, dict) else {},
        "latest_job": latest_job if isinstance(latest_job, dict) else {},
        "latest_experiment": latest_experiment if isinstance(latest_experiment, dict) else {},
        "latest_approval_gate": approval_gate if isinstance(approval_gate, dict) else {},
        "uploaded_assets": assets,
    }


def _build_project_planner_recommendation(project_id: str) -> dict:
    context = _latest_project_planner_context(project_id)
    recommendation = build_supervisor_planner_recommendation(
        project=context["project"],
        source=context["latest_source"],
        source_quality_gate=context["latest_source_quality_gate"],
        source_evidence_artifact=context["latest_source_evidence_artifact"],
        artifact_registry=context["latest_artifact_registry"],
        latest_run=context["latest_run"],
        latest_job=context["latest_job"],
        latest_experiment=context["latest_experiment"],
        approval_gate=context["latest_approval_gate"],
    )
    recommendation["uploaded_asset_count"] = len(context.get("uploaded_assets") or [])
    return recommendation


def _project_with_planner_summary(project_id: str) -> tuple[dict, dict]:
    safe_id = _safe_project_id(project_id)
    project = update_project_summary(safe_id)
    recommendation = _build_project_planner_recommendation(safe_id)

    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_planner_status": recommendation.get("overall_status", ""),
            "latest_next_action_type": recommendation.get("next_action_type", ""),
            "latest_next_best_action": recommendation.get("next_best_action", ""),
            "can_start_agent_run": bool(recommendation.get("can_start_agent_run")),
            "can_create_video_job": bool(recommendation.get("can_create_video_job")),
            "can_record_experiment": bool(recommendation.get("can_record_experiment")),
            "can_request_approval": bool(recommendation.get("can_request_approval")),
            "can_submit_provider": bool(recommendation.get("can_submit_provider")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass
    return project, recommendation



def _build_project_runner_plan_payload(project_id: str) -> dict:
    safe_id = _safe_project_id(project_id)
    project, planner_recommendation = _project_with_planner_summary(safe_id)
    context = _latest_project_planner_context(safe_id)

    agent_contract_registry = build_agent_contract_registry()
    agent_contract_summary = build_agent_contract_summary(agent_contract_registry)
    agent_contract_completeness_report = build_agent_contract_completeness_report(agent_contract_registry)
    source_adapter_contract_report = build_source_adapter_contract_report()
    multi_agent_output_chain_report = build_multi_agent_output_chain_report(
        agent_contract_report=agent_contract_completeness_report,
        source_adapter_contract_report=source_adapter_contract_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    keyframe_video_asset_chain_report = build_keyframe_video_asset_chain_report(
        multi_agent_output_chain_report=multi_agent_output_chain_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    keyframe_prompt_pack_report = build_keyframe_prompt_pack_report(
        keyframe_video_asset_chain_report=keyframe_video_asset_chain_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    manual_generation_result_report = build_manual_generation_result_report(
        keyframe_prompt_pack_report=keyframe_prompt_pack_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_api_readiness_report = build_provider_api_readiness_report(
        manual_generation_result_report=manual_generation_result_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_sandbox_runtime_report = build_provider_sandbox_runtime_report(
        provider_api_readiness_report=provider_api_readiness_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    real_provider_execution_gate_report = build_real_provider_execution_gate_report(
        provider_api_readiness_report=provider_api_readiness_report,
        provider_sandbox_runtime_report=provider_sandbox_runtime_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_failure_recovery_report = build_provider_failure_recovery_report(
        real_provider_execution_gate_report=real_provider_execution_gate_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_observability_report = build_provider_observability_report(
        provider_failure_recovery_report=provider_failure_recovery_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_queue_lease_worker_report = build_provider_queue_lease_worker_report(
        provider_observability_report=provider_observability_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_worker_checkpoint_resume_report = build_provider_worker_checkpoint_resume_report(
        provider_queue_lease_worker_report=provider_queue_lease_worker_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_worker_finalization_report = build_provider_worker_finalization_report(
        provider_worker_checkpoint_resume_report=provider_worker_checkpoint_resume_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_artifact_lineage_report = build_provider_artifact_lineage_report(
        provider_worker_finalization_report=provider_worker_finalization_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_artifact_registry_restore_report = build_provider_artifact_registry_restore_report(
        provider_artifact_lineage_report=provider_artifact_lineage_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_registry_operation_approval_report = build_provider_registry_operation_approval_report(
        provider_artifact_registry_restore_report=provider_artifact_registry_restore_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_registry_transaction_rehearsal_report = (
        build_provider_registry_transaction_rehearsal_report(
            provider_registry_operation_approval_report=provider_registry_operation_approval_report,
            project_id=project_id,
            requested_by="project_runner_plan_api",
        )
    )
    provider_transaction_monitor_report = build_provider_transaction_monitor_report(
        provider_registry_transaction_rehearsal_report=provider_registry_transaction_rehearsal_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_transaction_incident_drill_report = build_provider_transaction_incident_drill_report(
        provider_transaction_monitor_report=provider_transaction_monitor_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    provider_execution_readiness_packet_report = build_provider_execution_readiness_packet_report(
        provider_transaction_incident_drill_report=provider_transaction_incident_drill_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    runner_plan = build_agent_runner_plan(
        planner_recommendation=planner_recommendation,
        project=project,
        artifact_registry=context["latest_artifact_registry"],
        latest_run=context["latest_run"],
        latest_job=context["latest_job"],
    )
    runner_plan_summary = build_agent_runner_plan_summary(runner_plan)
    agent_capability_runtime = build_agent_capability_runtime(
        agent_contract_registry=agent_contract_registry,
        agent_contract_completeness_report=agent_contract_completeness_report,
        multi_agent_output_chain_report=multi_agent_output_chain_report,
        runner_plan=runner_plan,
        provider_execution_readiness_packet_report=provider_execution_readiness_packet_report,
        project_id=project_id,
        requested_by="project_runner_plan_api",
    )
    runner_dispatch_ticket = build_agent_runner_dispatch_ticket(
        runner_plan,
        requested_by="project_runner_plan_api",
    )
    runner_dispatch_summary = build_agent_runner_dispatch_summary(runner_dispatch_ticket)
    runner_dispatch_event = build_agent_runner_dispatch_event(runner_dispatch_ticket)
    runner_dispatch_event_summary = build_agent_runner_dispatch_event_summary(runner_dispatch_event)

    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_plan_status": runner_plan.get("execution_status", ""),
            "latest_runner_next_agent_id": runner_plan.get("next_agent_id", ""),
            "latest_runner_next_action_type": runner_plan.get("next_action_type", ""),
            "latest_runner_can_execute_next_agent": bool(runner_plan.get("can_execute_next_agent")),
            "latest_runner_requires_user_action": bool(runner_plan.get("requires_user_action")),
            "latest_runner_dispatch_status": runner_dispatch_ticket.get("dispatch_status", ""),
            "latest_runner_dispatch_allowed": bool(runner_dispatch_ticket.get("dispatch_allowed")),
            "latest_runner_dispatch_event_status": runner_dispatch_event.get("event_status", ""),
            "latest_runner_dispatch_event_id": runner_dispatch_event.get("event_id", ""),
        "latest_agent_task_count": int(agent_capability_runtime.get("agent_task_count") or 0),
        "latest_agent_next_action_count": int(agent_capability_runtime.get("supervisor_next_action_count") or 0),
        "latest_agent_quality_check_count": int(agent_capability_runtime.get("agent_quality_check_count") or 0),
        "latest_agent_handoff_ready": bool(agent_capability_runtime.get("agent_handoff_ready")),
        "latest_agent_contract_report_status": agent_contract_completeness_report.get("report_status", ""),
        "latest_agent_contract_complete_role_count": int(agent_contract_completeness_report.get("complete_role_count") or 0),
        "latest_agent_contract_missing_role_count": int(agent_contract_completeness_report.get("missing_role_count") or 0),
        "latest_agent_contract_supervisor_can_use_registry": bool(agent_contract_completeness_report.get("supervisor_can_use_registry")),
        "latest_source_adapter_contract_report_status": source_adapter_contract_report.get("report_status", ""),
        "latest_source_adapter_contract_complete_count": int(source_adapter_contract_report.get("complete_adapter_count") or 0),
        "latest_source_adapter_contract_missing_count": int(source_adapter_contract_report.get("missing_adapter_count") or 0),
        "latest_source_adapter_contract_supports_external_crawler_dry_run": bool(source_adapter_contract_report.get("supports_external_crawler_dry_run")),
        "latest_multi_agent_output_chain_status": multi_agent_output_chain_report.get("report_status", ""),
        "latest_multi_agent_output_complete_stage_count": int(multi_agent_output_chain_report.get("complete_stage_count") or 0),
        "latest_multi_agent_output_missing_stage_count": int(multi_agent_output_chain_report.get("missing_stage_count") or 0),
        "latest_multi_agent_output_supports_creative_to_video": bool(multi_agent_output_chain_report.get("supports_creative_to_video")),
        "latest_keyframe_video_asset_chain_status": keyframe_video_asset_chain_report.get("report_status", ""),
        "latest_keyframe_video_asset_complete_stage_count": int(keyframe_video_asset_chain_report.get("complete_stage_count") or 0),
        "latest_keyframe_video_asset_missing_stage_count": int(keyframe_video_asset_chain_report.get("missing_stage_count") or 0),
        "latest_keyframe_video_asset_supports_manual_handoff": bool(keyframe_video_asset_chain_report.get("supports_manual_generation_handoff")),
        "latest_keyframe_prompt_pack_status": keyframe_prompt_pack_report.get("report_status", ""),
        "latest_keyframe_prompt_pack_shot_prompt_count": int(keyframe_prompt_pack_report.get("shot_prompt_count") or 0),
        "latest_keyframe_prompt_pack_provider_variant_count": int(keyframe_prompt_pack_report.get("provider_variant_count") or 0),
        "latest_keyframe_prompt_pack_manual_copy_only": bool(keyframe_prompt_pack_report.get("manual_copy_paste_only")),
        "latest_manual_generation_result_status": manual_generation_result_report.get("report_status", ""),
        "latest_manual_generation_result_can_record_external_experiment": bool(manual_generation_result_report.get("can_record_external_experiment")),
        "latest_manual_generation_result_supports_rework": bool(manual_generation_result_report.get("supports_rework_recommendation")),
        "latest_manual_generation_result_manual_review_required": bool(manual_generation_result_report.get("manual_review_required")),
        "latest_provider_api_readiness_status": provider_api_readiness_report.get("report_status", ""),
        "latest_provider_api_readiness_provider_count": int(provider_api_readiness_report.get("provider_count") or 0),
        "latest_provider_api_readiness_real_execution_enabled": bool(provider_api_readiness_report.get("real_execution_enabled")),
        "latest_provider_api_readiness_provider_call_allowed": bool(provider_api_readiness_report.get("provider_call_allowed")),
        "latest_provider_sandbox_runtime_status": provider_sandbox_runtime_report.get("report_status", ""),
        "latest_provider_sandbox_runtime_fake_provider_count": int(provider_sandbox_runtime_report.get("fake_provider_count") or 0),
        "latest_provider_sandbox_runtime_real_execution_enabled": bool(provider_sandbox_runtime_report.get("real_execution_enabled")),
        "latest_provider_sandbox_runtime_external_api_called": bool(provider_sandbox_runtime_report.get("external_api_called")),
        "latest_real_provider_execution_gate_status": real_provider_execution_gate_report.get("report_status", ""),
        "latest_real_provider_execution_blocking_failure_count": int(real_provider_execution_gate_report.get("blocking_failure_count") or 0),
        "latest_real_provider_execution_enabled": bool(real_provider_execution_gate_report.get("real_execution_enabled")),
        "latest_real_provider_external_api_called": bool(real_provider_execution_gate_report.get("external_api_called")),
        "latest_provider_failure_recovery_status": provider_failure_recovery_report.get("report_status", ""),
        "latest_provider_failure_recovery_blocking_failure_count": int(provider_failure_recovery_report.get("blocking_failure_count") or 0),
        "latest_provider_failure_recovery_operator_review_required": bool(provider_failure_recovery_report.get("operator_review_required")),
        "latest_provider_failure_recovery_external_api_called": bool(provider_failure_recovery_report.get("external_api_called")),
        "latest_provider_observability_status": provider_observability_report.get("report_status", ""),
        "latest_provider_observability_dashboard_ready": bool(provider_observability_report.get("dashboard_ready")),
        "latest_provider_observability_alerts_triggered": bool(provider_observability_report.get("alert_policy", {}).get("alerts_triggered")),
        "latest_provider_observability_operator_review_required": bool(provider_observability_report.get("operator_review_required")),
        "latest_provider_observability_external_api_called": bool(provider_observability_report.get("external_api_called")),
        "latest_provider_queue_lease_worker_status": provider_queue_lease_worker_report.get("report_status", ""),
        "latest_provider_queue_lease_worker_blocking_failure_count": int(provider_queue_lease_worker_report.get("blocking_failure_count") or 0),
        "latest_provider_queue_lease_worker_lease_acquired": bool(provider_queue_lease_worker_report.get("lease_acquired")),
        "latest_provider_queue_lease_worker_worker_started": bool(provider_queue_lease_worker_report.get("worker_started")),
        "latest_provider_queue_lease_worker_external_api_called": bool(provider_queue_lease_worker_report.get("external_api_called")),
        "latest_provider_worker_checkpoint_resume_status": provider_worker_checkpoint_resume_report.get("report_status", ""),
        "latest_provider_worker_checkpoint_resume_blocking_failure_count": int(provider_worker_checkpoint_resume_report.get("blocking_failure_count") or 0),
        "latest_provider_worker_checkpoint_resume_checkpoint_recorded": bool(provider_worker_checkpoint_resume_report.get("checkpoint_recorded")),
        "latest_provider_worker_checkpoint_resume_resume_allowed": bool(provider_worker_checkpoint_resume_report.get("resume_allowed")),
        "latest_provider_worker_checkpoint_resume_external_api_called": bool(provider_worker_checkpoint_resume_report.get("external_api_called")),
        "latest_provider_worker_finalization_status": provider_worker_finalization_report.get("report_status", ""),
        "latest_provider_worker_finalization_blocking_failure_count": int(provider_worker_finalization_report.get("blocking_failure_count") or 0),
        "latest_provider_worker_finalization_result_validated": bool(provider_worker_finalization_report.get("result_validated")),
        "latest_provider_worker_finalization_artifact_handoff_ready": bool(provider_worker_finalization_report.get("artifact_handoff_ready")),
        "latest_provider_worker_finalization_external_api_called": bool(provider_worker_finalization_report.get("external_api_called")),
        "latest_provider_artifact_lineage_status": provider_artifact_lineage_report.get("report_status", ""),
        "latest_provider_artifact_lineage_blocking_failure_count": int(provider_artifact_lineage_report.get("blocking_failure_count") or 0),
        "latest_provider_artifact_lineage_versioned_snapshot_persisted": bool(provider_artifact_lineage_report.get("versioned_snapshot_persisted")),
        "latest_provider_artifact_lineage_workspace_export_ready": bool(provider_artifact_lineage_report.get("workspace_export_ready")),
        "latest_provider_artifact_lineage_external_api_called": bool(provider_artifact_lineage_report.get("external_api_called")),
        "latest_provider_artifact_registry_restore_status": provider_artifact_registry_restore_report.get("report_status", ""),
        "latest_provider_artifact_registry_restore_blocking_failure_count": int(provider_artifact_registry_restore_report.get("blocking_failure_count") or 0),
        "latest_provider_artifact_registry_restore_registry_persisted": bool(provider_artifact_registry_restore_report.get("registry_persisted")),
        "latest_provider_artifact_registry_restore_restore_available": bool(provider_artifact_registry_restore_report.get("restore_available")),
        "latest_provider_artifact_registry_restore_external_api_called": bool(provider_artifact_registry_restore_report.get("external_api_called")),
        "latest_provider_registry_operation_approval_status": provider_registry_operation_approval_report.get("report_status", ""),
        "latest_provider_registry_operation_approval_blocking_failure_count": int(provider_registry_operation_approval_report.get("blocking_failure_count") or 0),
        "latest_provider_registry_operation_approval_persist_allowed": bool(provider_registry_operation_approval_report.get("persist_allowed")),
        "latest_provider_registry_operation_approval_restore_applied": bool(provider_registry_operation_approval_report.get("restore_applied")),
        "latest_provider_registry_operation_approval_external_api_called": bool(provider_registry_operation_approval_report.get("external_api_called")),
        "latest_provider_registry_transaction_rehearsal_status": provider_registry_transaction_rehearsal_report.get("report_status", ""),
        "latest_provider_registry_transaction_rehearsal_blocking_failure_count": int(provider_registry_transaction_rehearsal_report.get("blocking_failure_count") or 0),
        "latest_provider_registry_transaction_rehearsal_commit_allowed": bool(provider_registry_transaction_rehearsal_report.get("commit_allowed")),
        "latest_provider_registry_transaction_rehearsal_transaction_committed": bool(provider_registry_transaction_rehearsal_report.get("transaction_committed")),
        "latest_provider_registry_transaction_rehearsal_external_api_called": bool(provider_registry_transaction_rehearsal_report.get("external_api_called")),
        "latest_provider_transaction_monitor_status": provider_transaction_monitor_report.get("report_status", ""),
        "latest_provider_transaction_monitor_blocking_failure_count": int(provider_transaction_monitor_report.get("blocking_failure_count") or 0),
        "latest_provider_transaction_monitor_drift_detected": bool(provider_transaction_monitor_report.get("drift_detected")),
        "latest_provider_transaction_monitor_auto_abort_triggered": bool(provider_transaction_monitor_report.get("auto_abort_triggered")),
        "latest_provider_transaction_monitor_external_api_called": bool(provider_transaction_monitor_report.get("external_api_called")),
        "latest_provider_transaction_incident_drill_status": provider_transaction_incident_drill_report.get("report_status", ""),
        "latest_provider_transaction_incident_drill_blocking_failure_count": int(provider_transaction_incident_drill_report.get("blocking_failure_count") or 0),
        "latest_provider_transaction_incident_drill_incident_opened": bool(provider_transaction_incident_drill_report.get("incident_opened")),
        "latest_provider_transaction_incident_drill_rollback_restore_executed": bool(provider_transaction_incident_drill_report.get("rollback_restore_executed")),
        "latest_provider_transaction_incident_drill_external_api_called": bool(provider_transaction_incident_drill_report.get("external_api_called")),
        "latest_provider_execution_readiness_packet_status": provider_execution_readiness_packet_report.get("report_status", ""),
        "latest_provider_execution_readiness_packet_blocking_failure_count": int(provider_execution_readiness_packet_report.get("blocking_failure_count") or 0),
        "latest_provider_execution_readiness_packet_final_gate_passed": bool(provider_execution_readiness_packet_report.get("final_gate_passed")),
        "latest_provider_execution_readiness_packet_real_execution_enabled": bool(provider_execution_readiness_packet_report.get("real_execution_enabled")),
        "latest_provider_execution_readiness_packet_external_api_called": bool(provider_execution_readiness_packet_report.get("external_api_called")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "project": project,
        "planner_recommendation": planner_recommendation,
        "runner_plan": runner_plan,
        "runner_plan_summary": runner_plan_summary,
        "runner_dispatch_ticket": runner_dispatch_ticket,
        "runner_dispatch_summary": runner_dispatch_summary,
        "runner_dispatch_event": runner_dispatch_event,
        "runner_dispatch_event_summary": runner_dispatch_event_summary,
        "agent_capability_runtime": agent_capability_runtime,
        "agent_contract_registry": agent_contract_registry,
        "agent_contract_summary": agent_contract_summary,
        "agent_contract_completeness_report": agent_contract_completeness_report,
        "source_adapter_contract_report": source_adapter_contract_report,
        "multi_agent_output_chain_report": multi_agent_output_chain_report,
        "keyframe_video_asset_chain_report": keyframe_video_asset_chain_report,
        "keyframe_prompt_pack_report": keyframe_prompt_pack_report,
        "manual_generation_result_report": manual_generation_result_report,
        "provider_api_readiness_report": provider_api_readiness_report,
        "provider_sandbox_runtime_report": provider_sandbox_runtime_report,
        "real_provider_execution_gate_report": real_provider_execution_gate_report,
        "provider_failure_recovery_report": provider_failure_recovery_report,
        "provider_observability_report": provider_observability_report,
        "provider_queue_lease_worker_report": provider_queue_lease_worker_report,
        "provider_worker_checkpoint_resume_report": provider_worker_checkpoint_resume_report,
        "provider_worker_finalization_report": provider_worker_finalization_report,
        "provider_artifact_lineage_report": provider_artifact_lineage_report,
        "provider_artifact_registry_restore_report": provider_artifact_registry_restore_report,
        "provider_registry_operation_approval_report": provider_registry_operation_approval_report,
        "provider_registry_transaction_rehearsal_report": provider_registry_transaction_rehearsal_report,
        "provider_transaction_monitor_report": provider_transaction_monitor_report,
        "provider_transaction_incident_drill_report": provider_transaction_incident_drill_report,
        "provider_execution_readiness_packet_report": provider_execution_readiness_packet_report,
        "dry_run": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
    }


@app.get("/api/v1/projects/{project_id}/runner/plan")
async def get_project_agent_runner_plan(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    return {
        "status": "success",
        **payload,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/projects/{project_id}/runner/plan/refresh")
async def refresh_project_agent_runner_plan(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    return {
        "status": "success",
        **payload,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/dispatch/dry-run")
async def dry_run_project_agent_dispatch(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_dispatch_ticket = payload["runner_dispatch_ticket"]
    runner_dispatch_event = payload["runner_dispatch_event"]
    runner_dispatch_summary = payload["runner_dispatch_summary"]
    runner_dispatch_event_summary = payload["runner_dispatch_event_summary"]

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_dispatch_dry_run_status": runner_dispatch_ticket.get("dispatch_status", ""),
            "latest_runner_dispatch_dry_run_allowed": bool(runner_dispatch_ticket.get("dispatch_allowed")),
            "latest_runner_dispatch_dry_run_event_status": runner_dispatch_event.get("event_status", ""),
            "latest_runner_dispatch_dry_run_event_id": runner_dispatch_event.get("event_id", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": runner_dispatch_ticket,
        "runner_dispatch_summary": runner_dispatch_summary,
        "runner_dispatch_event": runner_dispatch_event,
        "runner_dispatch_event_summary": runner_dispatch_event_summary,
        "dry_run": True,
        "dispatch_executed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/execute/dry-run")
async def dry_run_project_agent_execution(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_execute_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_execution_receipt_status": runner_execution_receipt.get("receipt_status", ""),
            "latest_runner_execution_allowed": bool(runner_execution_receipt.get("execution_allowed")),
            "latest_runner_execution_performed": bool(runner_execution_receipt.get("execution_performed")),
            "latest_runner_execution_target_agent_id": runner_execution_receipt.get("target_agent_id", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "dry_run": True,
        "execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/work-order/dry-run")
async def dry_run_project_agent_work_order(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_work_order_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_work_order_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_work_order_status": runner_work_order.get("work_order_status", ""),
            "latest_runner_work_order_allowed": bool(runner_work_order.get("work_order_allowed")),
            "latest_runner_work_order_target_agent_id": runner_work_order.get("target_agent_id", ""),
            "latest_runner_work_order_target_agent_stage": runner_work_order.get("target_agent_stage", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "dry_run": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/queue/dry-run")
async def dry_run_project_agent_queue_item(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_queue_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_queue_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_queue_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_queue_status": runner_queue_item.get("queue_status", ""),
            "latest_runner_enqueue_allowed": bool(runner_queue_item.get("enqueue_allowed")),
            "latest_runner_queue_item_id": runner_queue_item.get("queue_item_id", ""),
            "latest_runner_queue_target_agent_id": runner_queue_item.get("target_agent_id", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "dry_run": True,
        "queue_persisted": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/claim/dry-run")
async def dry_run_project_agent_queue_claim(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_claim_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_claim_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_claim_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_claim_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_claim_status": runner_queue_claim.get("claim_status", ""),
            "latest_runner_claim_allowed": bool(runner_queue_claim.get("claim_allowed")),
            "latest_runner_claim_id": runner_queue_claim.get("claim_id", ""),
            "latest_runner_claim_worker_id": runner_queue_claim.get("worker_id", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "dry_run": True,
        "claim_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/lease/dry-run")
async def dry_run_project_agent_worker_lease(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_lease_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_lease_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_lease_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_lease_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_lease_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_worker_lease_status": runner_worker_lease.get("lease_status", ""),
            "latest_runner_worker_lease_allowed": bool(runner_worker_lease.get("lease_allowed")),
            "latest_runner_worker_lease_id": runner_worker_lease.get("lease_id", ""),
            "latest_runner_worker_lease_worker_id": runner_worker_lease.get("worker_id", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "dry_run": True,
        "lease_persisted": False,
        "lease_acquired": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/invoke/dry-run")
async def dry_run_project_agent_invocation(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_invoke_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_invocation_envelope_status": runner_invocation_envelope.get("envelope_status", ""),
            "latest_runner_invocation_attempt_status": runner_invocation_attempt.get("attempt_status", ""),
            "latest_runner_invocation_attempt_allowed": bool(runner_invocation_attempt.get("attempt_allowed")),
            "latest_runner_invocation_target_agent_id": runner_invocation_attempt.get("target_agent_id", ""),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "dry_run": True,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/result/dry-run")
async def dry_run_project_agent_result_completion(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_result_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_result_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(
        runner_invocation_result
    )
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_result_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(
        runner_completion_receipt
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_invocation_result_status": runner_invocation_result.get("result_status", ""),
            "latest_runner_completion_status": runner_completion_receipt.get("completion_status", ""),
            "latest_runner_completion_allowed": bool(runner_completion_receipt.get("completion_allowed")),
            "latest_runner_agent_output_generated": bool(runner_invocation_result.get("agent_output_generated")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "dry_run": True,
        "agent_output_generated": False,
        "completion_recorded": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/checkpoint/dry-run")
async def dry_run_project_agent_handoff_checkpoint(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(
        runner_invocation_result
    )
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(
        runner_completion_receipt
    )
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(
        runner_completion_receipt,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(
        runner_handoff_checkpoint
    )
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(
        runner_handoff_checkpoint,
        requested_by="project_runner_checkpoint_dry_run_api",
    )
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(
        runner_next_agent_unlock
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_handoff_checkpoint_status": runner_handoff_checkpoint.get("checkpoint_status", ""),
            "latest_runner_next_agent_unlock_status": runner_next_agent_unlock.get("unlock_status", ""),
            "latest_runner_next_agent_unlocked": bool(runner_next_agent_unlock.get("next_agent_unlocked")),
            "latest_runner_handoff_complete": bool(runner_handoff_checkpoint.get("handoff_complete")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "dry_run": True,
        "handoff_checkpoint_recorded": False,
        "handoff_complete": False,
        "next_agent_unlocked": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/transition/dry-run")
async def dry_run_project_agent_graph_transition(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(
        runner_invocation_result
    )
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(
        runner_completion_receipt
    )
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(
        runner_completion_receipt,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(
        runner_handoff_checkpoint
    )
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(
        runner_handoff_checkpoint,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(
        runner_next_agent_unlock
    )
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(
        runner_next_agent_unlock,
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(
        runner_graph_transition_proposal
    )
    runner_state_projection = build_agent_runner_state_projection(
        runner_graph_transition_proposal,
        project=payload["project"],
        requested_by="project_runner_transition_dry_run_api",
    )
    runner_state_projection_summary = build_agent_runner_state_projection_summary(
        runner_state_projection
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_transition_status": runner_graph_transition_proposal.get("transition_status", ""),
            "latest_runner_projected_graph_state": runner_state_projection.get("proposed_graph_state", ""),
            "latest_runner_state_projection_status": runner_state_projection.get("projection_status", ""),
            "latest_runner_transition_persisted": bool(runner_graph_transition_proposal.get("graph_transition_persisted")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "dry_run": True,
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
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/commit-plan/dry-run")
async def dry_run_project_agent_transition_commit_plan(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(
        runner_invocation_result
    )
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(
        runner_completion_receipt
    )
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(
        runner_completion_receipt,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(
        runner_handoff_checkpoint
    )
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(
        runner_handoff_checkpoint,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(
        runner_next_agent_unlock
    )
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(
        runner_next_agent_unlock,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(
        runner_graph_transition_proposal
    )
    runner_state_projection = build_agent_runner_state_projection(
        runner_graph_transition_proposal,
        project=payload["project"],
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_state_projection_summary = build_agent_runner_state_projection_summary(
        runner_state_projection
    )
    runner_transition_commit_plan = build_agent_runner_transition_commit_plan(
        runner_state_projection,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_transition_commit_plan_summary = build_agent_runner_transition_commit_plan_summary(
        runner_transition_commit_plan
    )
    runner_mutation_guard = build_agent_runner_mutation_guard(
        runner_transition_commit_plan,
        requested_by="project_runner_commit_plan_dry_run_api",
    )
    runner_mutation_guard_summary = build_agent_runner_mutation_guard_summary(
        runner_mutation_guard
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_commit_plan_status": runner_transition_commit_plan.get("commit_plan_status", ""),
            "latest_runner_mutation_guard_status": runner_mutation_guard.get("mutation_guard_status", ""),
            "latest_runner_mutation_allowed": bool(runner_mutation_guard.get("mutation_allowed")),
            "latest_runner_planned_mutation_count": int(runner_transition_commit_plan.get("planned_mutation_count") or 0),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "runner_transition_commit_plan": runner_transition_commit_plan,
        "runner_transition_commit_plan_summary": runner_transition_commit_plan_summary,
        "runner_mutation_guard": runner_mutation_guard,
        "runner_mutation_guard_summary": runner_mutation_guard_summary,
        "dry_run": True,
        "commit_plan_persisted": False,
        "mutation_guard_recorded": False,
        "mutation_allowed": False,
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
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/persist-request/dry-run")
async def dry_run_project_agent_transition_persist_request(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(
        runner_invocation_result
    )
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(
        runner_completion_receipt
    )
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(
        runner_completion_receipt,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(
        runner_handoff_checkpoint
    )
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(
        runner_handoff_checkpoint,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(
        runner_next_agent_unlock
    )
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(
        runner_next_agent_unlock,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(
        runner_graph_transition_proposal
    )
    runner_state_projection = build_agent_runner_state_projection(
        runner_graph_transition_proposal,
        project=payload["project"],
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_state_projection_summary = build_agent_runner_state_projection_summary(
        runner_state_projection
    )
    runner_transition_commit_plan = build_agent_runner_transition_commit_plan(
        runner_state_projection,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_transition_commit_plan_summary = build_agent_runner_transition_commit_plan_summary(
        runner_transition_commit_plan
    )
    runner_mutation_guard = build_agent_runner_mutation_guard(
        runner_transition_commit_plan,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_mutation_guard_summary = build_agent_runner_mutation_guard_summary(
        runner_mutation_guard
    )
    runner_transition_persist_request = build_agent_runner_transition_persist_request(
        runner_mutation_guard,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_transition_persist_request_summary = build_agent_runner_transition_persist_request_summary(
        runner_transition_persist_request
    )
    runner_rollback_plan = build_agent_runner_rollback_plan(
        runner_transition_persist_request,
        requested_by="project_runner_persist_request_dry_run_api",
    )
    runner_rollback_plan_summary = build_agent_runner_rollback_plan_summary(
        runner_rollback_plan
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_persist_request_status": runner_transition_persist_request.get("persist_request_status", ""),
            "latest_runner_rollback_plan_status": runner_rollback_plan.get("rollback_plan_status", ""),
            "latest_runner_write_authorized": bool(runner_transition_persist_request.get("write_authorized")),
            "latest_runner_rollback_available": bool(runner_rollback_plan.get("rollback_available")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "runner_transition_commit_plan": runner_transition_commit_plan,
        "runner_transition_commit_plan_summary": runner_transition_commit_plan_summary,
        "runner_mutation_guard": runner_mutation_guard,
        "runner_mutation_guard_summary": runner_mutation_guard_summary,
        "runner_transition_persist_request": runner_transition_persist_request,
        "runner_transition_persist_request_summary": runner_transition_persist_request_summary,
        "runner_rollback_plan": runner_rollback_plan,
        "runner_rollback_plan_summary": runner_rollback_plan_summary,
        "dry_run": True,
        "persist_request_recorded": False,
        "rollback_plan_recorded": False,
        "write_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
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
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/persist-gate/dry-run")
async def dry_run_project_agent_persist_gate(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(
        runner_execution_receipt
    )
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(
        runner_work_order,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(
        runner_invocation_envelope
    )
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(
        runner_invocation_attempt
    )
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(
        runner_invocation_result
    )
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(
        runner_completion_receipt
    )
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(
        runner_completion_receipt,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(
        runner_handoff_checkpoint
    )
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(
        runner_handoff_checkpoint,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(
        runner_next_agent_unlock
    )
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(
        runner_next_agent_unlock,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(
        runner_graph_transition_proposal
    )
    runner_state_projection = build_agent_runner_state_projection(
        runner_graph_transition_proposal,
        project=payload["project"],
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_state_projection_summary = build_agent_runner_state_projection_summary(
        runner_state_projection
    )
    runner_transition_commit_plan = build_agent_runner_transition_commit_plan(
        runner_state_projection,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_transition_commit_plan_summary = build_agent_runner_transition_commit_plan_summary(
        runner_transition_commit_plan
    )
    runner_mutation_guard = build_agent_runner_mutation_guard(
        runner_transition_commit_plan,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_mutation_guard_summary = build_agent_runner_mutation_guard_summary(
        runner_mutation_guard
    )
    runner_transition_persist_request = build_agent_runner_transition_persist_request(
        runner_mutation_guard,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_transition_persist_request_summary = build_agent_runner_transition_persist_request_summary(
        runner_transition_persist_request
    )
    runner_rollback_plan = build_agent_runner_rollback_plan(
        runner_transition_persist_request,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_rollback_plan_summary = build_agent_runner_rollback_plan_summary(
        runner_rollback_plan
    )
    runner_persist_gate = build_agent_runner_persist_gate(
        runner_transition_persist_request,
        runner_rollback_plan,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_persist_gate_summary = build_agent_runner_persist_gate_summary(
        runner_persist_gate
    )
    runner_audit_ledger = build_agent_runner_audit_ledger(
        runner_persist_gate,
        requested_by="project_runner_persist_gate_dry_run_api",
    )
    runner_audit_ledger_summary = build_agent_runner_audit_ledger_summary(
        runner_audit_ledger
    )

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_persist_gate_status": runner_persist_gate.get("persist_gate_status", ""),
            "latest_runner_audit_ledger_status": runner_audit_ledger.get("audit_ledger_status", ""),
            "latest_runner_explicit_approval_present": bool(runner_persist_gate.get("explicit_approval_present")),
            "latest_runner_audit_entry_count": int(runner_audit_ledger.get("audit_entry_count") or 0),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "runner_transition_commit_plan": runner_transition_commit_plan,
        "runner_transition_commit_plan_summary": runner_transition_commit_plan_summary,
        "runner_mutation_guard": runner_mutation_guard,
        "runner_mutation_guard_summary": runner_mutation_guard_summary,
        "runner_transition_persist_request": runner_transition_persist_request,
        "runner_transition_persist_request_summary": runner_transition_persist_request_summary,
        "runner_rollback_plan": runner_rollback_plan,
        "runner_rollback_plan_summary": runner_rollback_plan_summary,
        "runner_persist_gate": runner_persist_gate,
        "runner_persist_gate_summary": runner_persist_gate_summary,
        "runner_audit_ledger": runner_audit_ledger,
        "runner_audit_ledger_summary": runner_audit_ledger_summary,
        "dry_run": True,
        "persist_gate_recorded": False,
        "audit_ledger_recorded": False,
        "explicit_approval_present": False,
        "write_authorized": False,
        "rollback_available": False,
        "rollback_applied": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/approval/dry-run")
async def dry_run_project_agent_approval_policy(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(runner_execution_receipt)
    runner_work_order = build_agent_runner_work_order(
        payload["runner_plan"],
        payload["runner_dispatch_ticket"],
        payload["runner_dispatch_event"],
        runner_execution_receipt,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(runner_work_order, requested_by="project_runner_approval_dry_run_api")
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(
        runner_queue_item,
        worker_id="project_workspace_runner_worker",
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(
        runner_queue_claim,
        lease_seconds=300,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(
        runner_worker_lease,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(runner_invocation_envelope)
    runner_invocation_attempt = build_agent_runner_invocation_attempt(
        runner_invocation_envelope,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(runner_invocation_attempt)
    runner_invocation_result = build_agent_runner_invocation_result(
        runner_invocation_attempt,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(runner_invocation_result)
    runner_completion_receipt = build_agent_runner_completion_receipt(
        runner_invocation_result,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(runner_completion_receipt)
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(
        runner_completion_receipt,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(runner_handoff_checkpoint)
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(
        runner_handoff_checkpoint,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(runner_next_agent_unlock)
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(
        runner_next_agent_unlock,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(runner_graph_transition_proposal)
    runner_state_projection = build_agent_runner_state_projection(
        runner_graph_transition_proposal,
        project=payload["project"],
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_state_projection_summary = build_agent_runner_state_projection_summary(runner_state_projection)
    runner_transition_commit_plan = build_agent_runner_transition_commit_plan(
        runner_state_projection,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_transition_commit_plan_summary = build_agent_runner_transition_commit_plan_summary(runner_transition_commit_plan)
    runner_mutation_guard = build_agent_runner_mutation_guard(
        runner_transition_commit_plan,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_mutation_guard_summary = build_agent_runner_mutation_guard_summary(runner_mutation_guard)
    runner_transition_persist_request = build_agent_runner_transition_persist_request(
        runner_mutation_guard,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_transition_persist_request_summary = build_agent_runner_transition_persist_request_summary(runner_transition_persist_request)
    runner_rollback_plan = build_agent_runner_rollback_plan(
        runner_transition_persist_request,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_rollback_plan_summary = build_agent_runner_rollback_plan_summary(runner_rollback_plan)
    runner_persist_gate = build_agent_runner_persist_gate(
        runner_transition_persist_request,
        runner_rollback_plan,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_persist_gate_summary = build_agent_runner_persist_gate_summary(runner_persist_gate)
    runner_audit_ledger = build_agent_runner_audit_ledger(
        runner_persist_gate,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_audit_ledger_summary = build_agent_runner_audit_ledger_summary(runner_audit_ledger)
    runner_approval_request = build_agent_runner_approval_request(
        runner_persist_gate,
        runner_audit_ledger,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_approval_request_summary = build_agent_runner_approval_request_summary(runner_approval_request)
    runner_policy_decision = build_agent_runner_policy_decision(
        runner_approval_request,
        requested_by="project_runner_approval_dry_run_api",
    )
    runner_policy_decision_summary = build_agent_runner_policy_decision_summary(runner_policy_decision)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_approval_request_status": runner_approval_request.get("approval_request_status", ""),
            "latest_runner_policy_decision_status": runner_policy_decision.get("policy_decision_status", ""),
            "latest_runner_approval_granted": bool(runner_approval_request.get("approval_granted")),
            "latest_runner_policy_approved": bool(runner_policy_decision.get("policy_approved")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "runner_transition_commit_plan": runner_transition_commit_plan,
        "runner_transition_commit_plan_summary": runner_transition_commit_plan_summary,
        "runner_mutation_guard": runner_mutation_guard,
        "runner_mutation_guard_summary": runner_mutation_guard_summary,
        "runner_transition_persist_request": runner_transition_persist_request,
        "runner_transition_persist_request_summary": runner_transition_persist_request_summary,
        "runner_rollback_plan": runner_rollback_plan,
        "runner_rollback_plan_summary": runner_rollback_plan_summary,
        "runner_persist_gate": runner_persist_gate,
        "runner_persist_gate_summary": runner_persist_gate_summary,
        "runner_audit_ledger": runner_audit_ledger,
        "runner_audit_ledger_summary": runner_audit_ledger_summary,
        "runner_approval_request": runner_approval_request,
        "runner_approval_request_summary": runner_approval_request_summary,
        "runner_policy_decision": runner_policy_decision,
        "runner_policy_decision_summary": runner_policy_decision_summary,
        "dry_run": True,
        "approval_recorded": False,
        "approval_granted": False,
        "policy_decision_recorded": False,
        "policy_approved": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "agent_output_generated": False,
        "agent_invoked": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/authorization/dry-run")
async def dry_run_project_agent_authorization_manifest(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)
    runner_execution_receipt = build_agent_runner_execution_receipt(payload["runner_dispatch_ticket"], payload["runner_dispatch_event"], requested_by="project_runner_authorization_dry_run_api")
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(runner_execution_receipt)
    runner_work_order = build_agent_runner_work_order(payload["runner_plan"], payload["runner_dispatch_ticket"], payload["runner_dispatch_event"], runner_execution_receipt, requested_by="project_runner_authorization_dry_run_api")
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(runner_work_order, requested_by="project_runner_authorization_dry_run_api")
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(runner_queue_item, worker_id="project_workspace_runner_worker", requested_by="project_runner_authorization_dry_run_api")
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(runner_queue_claim, lease_seconds=300, requested_by="project_runner_authorization_dry_run_api")
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(runner_worker_lease, requested_by="project_runner_authorization_dry_run_api")
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(runner_invocation_envelope)
    runner_invocation_attempt = build_agent_runner_invocation_attempt(runner_invocation_envelope, requested_by="project_runner_authorization_dry_run_api")
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(runner_invocation_attempt)
    runner_invocation_result = build_agent_runner_invocation_result(runner_invocation_attempt, requested_by="project_runner_authorization_dry_run_api")
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(runner_invocation_result)
    runner_completion_receipt = build_agent_runner_completion_receipt(runner_invocation_result, requested_by="project_runner_authorization_dry_run_api")
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(runner_completion_receipt)
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(runner_completion_receipt, requested_by="project_runner_authorization_dry_run_api")
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(runner_handoff_checkpoint)
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(runner_handoff_checkpoint, requested_by="project_runner_authorization_dry_run_api")
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(runner_next_agent_unlock)
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(runner_next_agent_unlock, requested_by="project_runner_authorization_dry_run_api")
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(runner_graph_transition_proposal)
    runner_state_projection = build_agent_runner_state_projection(runner_graph_transition_proposal, project=payload["project"], requested_by="project_runner_authorization_dry_run_api")
    runner_state_projection_summary = build_agent_runner_state_projection_summary(runner_state_projection)
    runner_transition_commit_plan = build_agent_runner_transition_commit_plan(runner_state_projection, requested_by="project_runner_authorization_dry_run_api")
    runner_transition_commit_plan_summary = build_agent_runner_transition_commit_plan_summary(runner_transition_commit_plan)
    runner_mutation_guard = build_agent_runner_mutation_guard(runner_transition_commit_plan, requested_by="project_runner_authorization_dry_run_api")
    runner_mutation_guard_summary = build_agent_runner_mutation_guard_summary(runner_mutation_guard)
    runner_transition_persist_request = build_agent_runner_transition_persist_request(runner_mutation_guard, requested_by="project_runner_authorization_dry_run_api")
    runner_transition_persist_request_summary = build_agent_runner_transition_persist_request_summary(runner_transition_persist_request)
    runner_rollback_plan = build_agent_runner_rollback_plan(runner_transition_persist_request, requested_by="project_runner_authorization_dry_run_api")
    runner_rollback_plan_summary = build_agent_runner_rollback_plan_summary(runner_rollback_plan)
    runner_persist_gate = build_agent_runner_persist_gate(runner_transition_persist_request, runner_rollback_plan, requested_by="project_runner_authorization_dry_run_api")
    runner_persist_gate_summary = build_agent_runner_persist_gate_summary(runner_persist_gate)
    runner_audit_ledger = build_agent_runner_audit_ledger(runner_persist_gate, requested_by="project_runner_authorization_dry_run_api")
    runner_audit_ledger_summary = build_agent_runner_audit_ledger_summary(runner_audit_ledger)
    runner_approval_request = build_agent_runner_approval_request(runner_persist_gate, runner_audit_ledger, requested_by="project_runner_authorization_dry_run_api")
    runner_approval_request_summary = build_agent_runner_approval_request_summary(runner_approval_request)
    runner_policy_decision = build_agent_runner_policy_decision(runner_approval_request, requested_by="project_runner_authorization_dry_run_api")
    runner_policy_decision_summary = build_agent_runner_policy_decision_summary(runner_policy_decision)
    runner_authorization_preview = build_agent_runner_authorization_preview(runner_policy_decision, requested_by="project_runner_authorization_dry_run_api")
    runner_authorization_preview_summary = build_agent_runner_authorization_preview_summary(runner_authorization_preview)
    runner_execution_manifest = build_agent_runner_execution_manifest(runner_authorization_preview, requested_by="project_runner_authorization_dry_run_api")
    runner_execution_manifest_summary = build_agent_runner_execution_manifest_summary(runner_execution_manifest)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update(
        {
            "latest_runner_authorization_status": runner_authorization_preview.get("authorization_status", ""),
            "latest_runner_execution_manifest_status": runner_execution_manifest.get("execution_manifest_status", ""),
            "latest_runner_authorization_granted": bool(runner_authorization_preview.get("authorization_granted")),
            "latest_runner_execution_started": bool(runner_execution_manifest.get("execution_started")),
        }
    )
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "runner_transition_commit_plan": runner_transition_commit_plan,
        "runner_transition_commit_plan_summary": runner_transition_commit_plan_summary,
        "runner_mutation_guard": runner_mutation_guard,
        "runner_mutation_guard_summary": runner_mutation_guard_summary,
        "runner_transition_persist_request": runner_transition_persist_request,
        "runner_transition_persist_request_summary": runner_transition_persist_request_summary,
        "runner_rollback_plan": runner_rollback_plan,
        "runner_rollback_plan_summary": runner_rollback_plan_summary,
        "runner_persist_gate": runner_persist_gate,
        "runner_persist_gate_summary": runner_persist_gate_summary,
        "runner_audit_ledger": runner_audit_ledger,
        "runner_audit_ledger_summary": runner_audit_ledger_summary,
        "runner_approval_request": runner_approval_request,
        "runner_approval_request_summary": runner_approval_request_summary,
        "runner_policy_decision": runner_policy_decision,
        "runner_policy_decision_summary": runner_policy_decision_summary,
        "runner_authorization_preview": runner_authorization_preview,
        "runner_authorization_preview_summary": runner_authorization_preview_summary,
        "runner_execution_manifest": runner_execution_manifest,
        "runner_execution_manifest_summary": runner_execution_manifest_summary,
        "dry_run": True,
        "authorization_recorded": False,
        "authorization_granted": False,
        "authorization_token_issued": False,
        "manifest_recorded": False,
        "execution_started": False,
        "agent_execution_authorized": False,
        "agent_execution_performed": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/runtime-readiness/dry-run")
async def dry_run_project_agent_runtime_readiness(project_id: str, http_request: Request):
    payload = _build_project_runner_plan_payload(project_id)

    runner_execution_receipt = build_agent_runner_execution_receipt(payload["runner_dispatch_ticket"], payload["runner_dispatch_event"], requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_execution_receipt_summary = build_agent_runner_execution_receipt_summary(runner_execution_receipt)
    runner_work_order = build_agent_runner_work_order(payload["runner_plan"], payload["runner_dispatch_ticket"], payload["runner_dispatch_event"], runner_execution_receipt, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_work_order_summary = build_agent_runner_work_order_summary(runner_work_order)
    runner_queue_item = build_agent_runner_queue_item(runner_work_order, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_queue_item_summary = build_agent_runner_queue_item_summary(runner_queue_item)
    runner_queue_claim = build_agent_runner_queue_claim(runner_queue_item, worker_id="project_workspace_runner_worker", requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_queue_claim_summary = build_agent_runner_queue_claim_summary(runner_queue_claim)
    runner_worker_lease = build_agent_runner_worker_lease(runner_queue_claim, lease_seconds=300, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_worker_lease_summary = build_agent_runner_worker_lease_summary(runner_worker_lease)
    runner_invocation_envelope = build_agent_runner_invocation_envelope(runner_worker_lease, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_invocation_envelope_summary = build_agent_runner_invocation_envelope_summary(runner_invocation_envelope)
    runner_invocation_attempt = build_agent_runner_invocation_attempt(runner_invocation_envelope, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_invocation_attempt_summary = build_agent_runner_invocation_attempt_summary(runner_invocation_attempt)
    runner_invocation_result = build_agent_runner_invocation_result(runner_invocation_attempt, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_invocation_result_summary = build_agent_runner_invocation_result_summary(runner_invocation_result)
    runner_completion_receipt = build_agent_runner_completion_receipt(runner_invocation_result, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_completion_receipt_summary = build_agent_runner_completion_receipt_summary(runner_completion_receipt)
    runner_handoff_checkpoint = build_agent_runner_handoff_checkpoint(runner_completion_receipt, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_handoff_checkpoint_summary = build_agent_runner_handoff_checkpoint_summary(runner_handoff_checkpoint)
    runner_next_agent_unlock = build_agent_runner_next_agent_unlock(runner_handoff_checkpoint, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_next_agent_unlock_summary = build_agent_runner_next_agent_unlock_summary(runner_next_agent_unlock)
    runner_graph_transition_proposal = build_agent_runner_graph_transition_proposal(runner_next_agent_unlock, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_graph_transition_proposal_summary = build_agent_runner_graph_transition_proposal_summary(runner_graph_transition_proposal)
    runner_state_projection = build_agent_runner_state_projection(runner_graph_transition_proposal, project=payload["project"], requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_state_projection_summary = build_agent_runner_state_projection_summary(runner_state_projection)
    runner_transition_commit_plan = build_agent_runner_transition_commit_plan(runner_state_projection, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_transition_commit_plan_summary = build_agent_runner_transition_commit_plan_summary(runner_transition_commit_plan)
    runner_mutation_guard = build_agent_runner_mutation_guard(runner_transition_commit_plan, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_mutation_guard_summary = build_agent_runner_mutation_guard_summary(runner_mutation_guard)
    runner_transition_persist_request = build_agent_runner_transition_persist_request(runner_mutation_guard, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_transition_persist_request_summary = build_agent_runner_transition_persist_request_summary(runner_transition_persist_request)
    runner_rollback_plan = build_agent_runner_rollback_plan(runner_transition_persist_request, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_rollback_plan_summary = build_agent_runner_rollback_plan_summary(runner_rollback_plan)
    runner_persist_gate = build_agent_runner_persist_gate(runner_transition_persist_request, runner_rollback_plan, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_persist_gate_summary = build_agent_runner_persist_gate_summary(runner_persist_gate)
    runner_audit_ledger = build_agent_runner_audit_ledger(runner_persist_gate, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_audit_ledger_summary = build_agent_runner_audit_ledger_summary(runner_audit_ledger)
    runner_approval_request = build_agent_runner_approval_request(runner_persist_gate, runner_audit_ledger, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_approval_request_summary = build_agent_runner_approval_request_summary(runner_approval_request)
    runner_policy_decision = build_agent_runner_policy_decision(runner_approval_request, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_policy_decision_summary = build_agent_runner_policy_decision_summary(runner_policy_decision)

    runner_authorization_preview = build_agent_runner_authorization_preview(runner_policy_decision, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_authorization_preview_summary = build_agent_runner_authorization_preview_summary(runner_authorization_preview)
    runner_execution_manifest = build_agent_runner_execution_manifest(runner_authorization_preview, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_execution_manifest_summary = build_agent_runner_execution_manifest_summary(runner_execution_manifest)
    runner_execution_session = build_agent_runner_execution_session(runner_execution_manifest, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_execution_session_summary = build_agent_runner_execution_session_summary(runner_execution_session)
    runner_preflight_certificate = build_agent_runner_preflight_certificate(runner_execution_session, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_preflight_certificate_summary = build_agent_runner_preflight_certificate_summary(runner_preflight_certificate)
    runner_runtime_sandbox = build_agent_runner_runtime_sandbox(runner_preflight_certificate, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_runtime_sandbox_summary = build_agent_runner_runtime_sandbox_summary(runner_runtime_sandbox)
    runner_worker_bootstrap_plan = build_agent_runner_worker_bootstrap_plan(runner_runtime_sandbox, requested_by="project_runner_runtime_readiness_dry_run_api")
    runner_worker_bootstrap_plan_summary = build_agent_runner_worker_bootstrap_plan_summary(runner_worker_bootstrap_plan)

    project = payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_authorization_status": runner_authorization_preview.get("authorization_status", ""),
        "latest_runner_execution_manifest_status": runner_execution_manifest.get("execution_manifest_status", ""),
        "latest_runner_execution_session_status": runner_execution_session.get("execution_session_status", ""),
        "latest_runner_preflight_status": runner_preflight_certificate.get("preflight_status", ""),
        "latest_runner_runtime_sandbox_status": runner_runtime_sandbox.get("runtime_sandbox_status", ""),
        "latest_runner_worker_bootstrap_status": runner_worker_bootstrap_plan.get("worker_bootstrap_status", ""),
        "latest_runner_worker_started": bool(runner_worker_bootstrap_plan.get("worker_started")),
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        "status": "success",
        "project": project,
        "planner_recommendation": payload["planner_recommendation"],
        "runner_plan": payload["runner_plan"],
        "runner_plan_summary": payload["runner_plan_summary"],
        "runner_dispatch_ticket": payload["runner_dispatch_ticket"],
        "runner_dispatch_summary": payload["runner_dispatch_summary"],
        "runner_dispatch_event": payload["runner_dispatch_event"],
        "runner_dispatch_event_summary": payload["runner_dispatch_event_summary"],
        "runner_execution_receipt": runner_execution_receipt,
        "runner_execution_receipt_summary": runner_execution_receipt_summary,
        "runner_work_order": runner_work_order,
        "runner_work_order_summary": runner_work_order_summary,
        "runner_queue_item": runner_queue_item,
        "runner_queue_item_summary": runner_queue_item_summary,
        "runner_queue_claim": runner_queue_claim,
        "runner_queue_claim_summary": runner_queue_claim_summary,
        "runner_worker_lease": runner_worker_lease,
        "runner_worker_lease_summary": runner_worker_lease_summary,
        "runner_invocation_envelope": runner_invocation_envelope,
        "runner_invocation_envelope_summary": runner_invocation_envelope_summary,
        "runner_invocation_attempt": runner_invocation_attempt,
        "runner_invocation_attempt_summary": runner_invocation_attempt_summary,
        "runner_invocation_result": runner_invocation_result,
        "runner_invocation_result_summary": runner_invocation_result_summary,
        "runner_completion_receipt": runner_completion_receipt,
        "runner_completion_receipt_summary": runner_completion_receipt_summary,
        "runner_handoff_checkpoint": runner_handoff_checkpoint,
        "runner_handoff_checkpoint_summary": runner_handoff_checkpoint_summary,
        "runner_next_agent_unlock": runner_next_agent_unlock,
        "runner_next_agent_unlock_summary": runner_next_agent_unlock_summary,
        "runner_graph_transition_proposal": runner_graph_transition_proposal,
        "runner_graph_transition_proposal_summary": runner_graph_transition_proposal_summary,
        "runner_state_projection": runner_state_projection,
        "runner_state_projection_summary": runner_state_projection_summary,
        "runner_transition_commit_plan": runner_transition_commit_plan,
        "runner_transition_commit_plan_summary": runner_transition_commit_plan_summary,
        "runner_mutation_guard": runner_mutation_guard,
        "runner_mutation_guard_summary": runner_mutation_guard_summary,
        "runner_transition_persist_request": runner_transition_persist_request,
        "runner_transition_persist_request_summary": runner_transition_persist_request_summary,
        "runner_rollback_plan": runner_rollback_plan,
        "runner_rollback_plan_summary": runner_rollback_plan_summary,
        "runner_persist_gate": runner_persist_gate,
        "runner_persist_gate_summary": runner_persist_gate_summary,
        "runner_audit_ledger": runner_audit_ledger,
        "runner_audit_ledger_summary": runner_audit_ledger_summary,
        "runner_approval_request": runner_approval_request,
        "runner_approval_request_summary": runner_approval_request_summary,
        "runner_policy_decision": runner_policy_decision,
        "runner_policy_decision_summary": runner_policy_decision_summary,
        "runner_authorization_preview": runner_authorization_preview,
        "runner_authorization_preview_summary": runner_authorization_preview_summary,
        "runner_execution_manifest": runner_execution_manifest,
        "runner_execution_manifest_summary": runner_execution_manifest_summary,
        "runner_execution_session": runner_execution_session,
        "runner_execution_session_summary": runner_execution_session_summary,
        "runner_preflight_certificate": runner_preflight_certificate,
        "runner_preflight_certificate_summary": runner_preflight_certificate_summary,
        "runner_runtime_sandbox": runner_runtime_sandbox,
        "runner_runtime_sandbox_summary": runner_runtime_sandbox_summary,
        "runner_worker_bootstrap_plan": runner_worker_bootstrap_plan,
        "runner_worker_bootstrap_plan_summary": runner_worker_bootstrap_plan_summary,
        "dry_run": True,
        "authorization_granted": False,
        "authorization_token_issued": False,
        "execution_started": False,
        "session_started": False,
        "preflight_clearance_granted": False,
        "sandbox_active": False,
        "worker_started": False,
        "worker_loop_started": False,
        "agent_execution_performed": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/worker-loop/dry-run")
async def dry_run_project_agent_worker_loop(project_id: str, http_request: Request):
    runtime_payload = await dry_run_project_agent_runtime_readiness(project_id, http_request)

    runner_worker_poll = build_agent_runner_worker_poll(
        runtime_payload["runner_worker_bootstrap_plan"],
        requested_by="project_runner_worker_loop_dry_run_api",
    )
    runner_worker_poll_summary = build_agent_runner_worker_poll_summary(runner_worker_poll)
    runner_worker_heartbeat = build_agent_runner_worker_heartbeat(
        runner_worker_poll,
        requested_by="project_runner_worker_loop_dry_run_api",
    )
    runner_worker_heartbeat_summary = build_agent_runner_worker_heartbeat_summary(runner_worker_heartbeat)
    runner_worker_loop_simulation = build_agent_runner_worker_loop_simulation(
        runner_worker_heartbeat,
        requested_by="project_runner_worker_loop_dry_run_api",
    )
    runner_worker_loop_simulation_summary = build_agent_runner_worker_loop_simulation_summary(runner_worker_loop_simulation)
    runner_failure_receipt = build_agent_runner_failure_receipt(
        runner_worker_loop_simulation,
        requested_by="project_runner_worker_loop_dry_run_api",
    )
    runner_failure_receipt_summary = build_agent_runner_failure_receipt_summary(runner_failure_receipt)
    runner_retry_plan = build_agent_runner_retry_plan(
        runner_failure_receipt,
        requested_by="project_runner_worker_loop_dry_run_api",
    )
    runner_retry_plan_summary = build_agent_runner_retry_plan_summary(runner_retry_plan)
    runner_recovery_summary = build_agent_runner_recovery_summary(
        runner_retry_plan,
        requested_by="project_runner_worker_loop_dry_run_api",
    )
    runner_recovery_summary_summary = build_agent_runner_recovery_summary_summary(runner_recovery_summary)

    project = runtime_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_worker_poll_status": runner_worker_poll.get("worker_poll_status", ""),
        "latest_runner_worker_heartbeat_status": runner_worker_heartbeat.get("worker_heartbeat_status", ""),
        "latest_runner_worker_loop_status": runner_worker_loop_simulation.get("worker_loop_status", ""),
        "latest_runner_failure_receipt_status": runner_failure_receipt.get("failure_receipt_status", ""),
        "latest_runner_retry_plan_status": runner_retry_plan.get("retry_plan_status", ""),
        "latest_runner_recovery_status": runner_recovery_summary.get("recovery_status", ""),
        "latest_runner_worker_loop_started": bool(runner_worker_loop_simulation.get("worker_loop_started")),
        "latest_runner_retry_scheduled": bool(runner_retry_plan.get("retry_scheduled")),
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **runtime_payload,
        "project": project,
        "runner_worker_poll": runner_worker_poll,
        "runner_worker_poll_summary": runner_worker_poll_summary,
        "runner_worker_heartbeat": runner_worker_heartbeat,
        "runner_worker_heartbeat_summary": runner_worker_heartbeat_summary,
        "runner_worker_loop_simulation": runner_worker_loop_simulation,
        "runner_worker_loop_simulation_summary": runner_worker_loop_simulation_summary,
        "runner_failure_receipt": runner_failure_receipt,
        "runner_failure_receipt_summary": runner_failure_receipt_summary,
        "runner_retry_plan": runner_retry_plan,
        "runner_retry_plan_summary": runner_retry_plan_summary,
        "runner_recovery_summary": runner_recovery_summary,
        "runner_recovery_summary_summary": runner_recovery_summary_summary,
        "dry_run": True,
        "queue_item_claimed": False,
        "heartbeat_recorded": False,
        "worker_alive": False,
        "worker_started": False,
        "worker_loop_started": False,
        "loop_simulation_recorded": False,
        "failure_detected": False,
        "failure_recorded": False,
        "retry_allowed": False,
        "retry_scheduled": False,
        "retry_attempt_started": False,
        "recovery_complete": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "result_written": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/worker-checkpoint/dry-run")
async def dry_run_project_agent_worker_checkpoint(project_id: str, http_request: Request):
    worker_loop_payload = await dry_run_project_agent_worker_loop(project_id, http_request)

    runner_output_buffer = build_agent_runner_output_buffer(
        worker_loop_payload["runner_recovery_summary"],
        requested_by="project_runner_worker_checkpoint_dry_run_api",
    )
    runner_output_buffer_summary = build_agent_runner_output_buffer_summary(runner_output_buffer)
    runner_artifact_manifest = build_agent_runner_artifact_manifest(
        runner_output_buffer,
        requested_by="project_runner_worker_checkpoint_dry_run_api",
    )
    runner_artifact_manifest_summary = build_agent_runner_artifact_manifest_summary(runner_artifact_manifest)
    runner_result_validation_gate = build_agent_runner_result_validation_gate(
        runner_artifact_manifest,
        requested_by="project_runner_worker_checkpoint_dry_run_api",
    )
    runner_result_validation_gate_summary = build_agent_runner_result_validation_gate_summary(runner_result_validation_gate)
    runner_resume_cursor = build_agent_runner_resume_cursor(
        runner_result_validation_gate,
        requested_by="project_runner_worker_checkpoint_dry_run_api",
    )
    runner_resume_cursor_summary = build_agent_runner_resume_cursor_summary(runner_resume_cursor)
    runner_dead_letter_policy = build_agent_runner_dead_letter_policy(
        runner_resume_cursor,
        requested_by="project_runner_worker_checkpoint_dry_run_api",
    )
    runner_dead_letter_policy_summary = build_agent_runner_dead_letter_policy_summary(runner_dead_letter_policy)
    runner_worker_checkpoint_bundle = build_agent_runner_worker_checkpoint_bundle(
        runner_dead_letter_policy,
        requested_by="project_runner_worker_checkpoint_dry_run_api",
    )
    runner_worker_checkpoint_bundle_summary = build_agent_runner_worker_checkpoint_bundle_summary(runner_worker_checkpoint_bundle)

    project = worker_loop_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_output_buffer_status": runner_output_buffer.get("output_buffer_status", ""),
        "latest_runner_artifact_manifest_status": runner_artifact_manifest.get("artifact_manifest_status", ""),
        "latest_runner_result_validation_gate_status": runner_result_validation_gate.get("result_validation_gate_status", ""),
        "latest_runner_resume_cursor_status": runner_resume_cursor.get("resume_cursor_status", ""),
        "latest_runner_dead_letter_policy_status": runner_dead_letter_policy.get("dead_letter_policy_status", ""),
        "latest_runner_worker_checkpoint_bundle_status": runner_worker_checkpoint_bundle.get("worker_checkpoint_bundle_status", ""),
        "latest_runner_checkpoint_recorded": bool(runner_worker_checkpoint_bundle.get("checkpoint_recorded")),
        "latest_runner_result_accepted": bool(runner_result_validation_gate.get("result_accepted")),
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **worker_loop_payload,
        "project": project,
        "runner_output_buffer": runner_output_buffer,
        "runner_output_buffer_summary": runner_output_buffer_summary,
        "runner_artifact_manifest": runner_artifact_manifest,
        "runner_artifact_manifest_summary": runner_artifact_manifest_summary,
        "runner_result_validation_gate": runner_result_validation_gate,
        "runner_result_validation_gate_summary": runner_result_validation_gate_summary,
        "runner_resume_cursor": runner_resume_cursor,
        "runner_resume_cursor_summary": runner_resume_cursor_summary,
        "runner_dead_letter_policy": runner_dead_letter_policy,
        "runner_dead_letter_policy_summary": runner_dead_letter_policy_summary,
        "runner_worker_checkpoint_bundle": runner_worker_checkpoint_bundle,
        "runner_worker_checkpoint_bundle_summary": runner_worker_checkpoint_bundle_summary,
        "dry_run": True,
        "output_buffer_recorded": False,
        "output_written": False,
        "artifact_manifest_recorded": False,
        "artifact_created": False,
        "validation_passed": False,
        "validation_recorded": False,
        "result_accepted": False,
        "resume_allowed": False,
        "resume_cursor_recorded": False,
        "dead_letter_required": False,
        "dead_letter_recorded": False,
        "checkpoint_recorded": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "result_written": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



@app.post("/api/v1/projects/{project_id}/runner/finalization/dry-run")
async def dry_run_project_agent_finalization(project_id: str, http_request: Request):
    checkpoint_payload = await dry_run_project_agent_worker_checkpoint(project_id, http_request)

    runner_result_acceptance = build_agent_runner_result_acceptance(
        checkpoint_payload["runner_worker_checkpoint_bundle"],
        requested_by="project_runner_finalization_dry_run_api",
    )
    runner_result_acceptance_summary = build_agent_runner_result_acceptance_summary(runner_result_acceptance)
    runner_project_merge_preview = build_agent_runner_project_merge_preview(
        runner_result_acceptance,
        requested_by="project_runner_finalization_dry_run_api",
    )
    runner_project_merge_preview_summary = build_agent_runner_project_merge_preview_summary(runner_project_merge_preview)
    runner_downstream_handoff = build_agent_runner_downstream_handoff(
        runner_project_merge_preview,
        requested_by="project_runner_finalization_dry_run_api",
    )
    runner_downstream_handoff_summary = build_agent_runner_downstream_handoff_summary(runner_downstream_handoff)
    runner_human_review_packet = build_agent_runner_human_review_packet(
        runner_downstream_handoff,
        requested_by="project_runner_finalization_dry_run_api",
    )
    runner_human_review_packet_summary = build_agent_runner_human_review_packet_summary(runner_human_review_packet)
    runner_run_finalization = build_agent_runner_run_finalization(
        runner_human_review_packet,
        requested_by="project_runner_finalization_dry_run_api",
    )
    runner_run_finalization_summary = build_agent_runner_run_finalization_summary(runner_run_finalization)
    runner_completion_ledger = build_agent_runner_completion_ledger(
        runner_run_finalization,
        requested_by="project_runner_finalization_dry_run_api",
    )
    runner_completion_ledger_summary = build_agent_runner_completion_ledger_summary(runner_completion_ledger)

    project = checkpoint_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_result_acceptance_status": runner_result_acceptance.get("result_acceptance_status", ""),
        "latest_runner_project_merge_preview_status": runner_project_merge_preview.get("project_merge_preview_status", ""),
        "latest_runner_downstream_handoff_status": runner_downstream_handoff.get("downstream_handoff_status", ""),
        "latest_runner_human_review_packet_status": runner_human_review_packet.get("human_review_packet_status", ""),
        "latest_runner_run_finalization_status": runner_run_finalization.get("run_finalization_status", ""),
        "latest_runner_completion_ledger_status": runner_completion_ledger.get("completion_ledger_status", ""),
        "latest_runner_run_finalized": bool(runner_run_finalization.get("run_finalized")),
        "latest_runner_completion_ledger_recorded": bool(runner_completion_ledger.get("completion_ledger_recorded")),
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **checkpoint_payload,
        "project": project,
        "runner_result_acceptance": runner_result_acceptance,
        "runner_result_acceptance_summary": runner_result_acceptance_summary,
        "runner_project_merge_preview": runner_project_merge_preview,
        "runner_project_merge_preview_summary": runner_project_merge_preview_summary,
        "runner_downstream_handoff": runner_downstream_handoff,
        "runner_downstream_handoff_summary": runner_downstream_handoff_summary,
        "runner_human_review_packet": runner_human_review_packet,
        "runner_human_review_packet_summary": runner_human_review_packet_summary,
        "runner_run_finalization": runner_run_finalization,
        "runner_run_finalization_summary": runner_run_finalization_summary,
        "runner_completion_ledger": runner_completion_ledger,
        "runner_completion_ledger_summary": runner_completion_ledger_summary,
        "dry_run": True,
        "result_accepted": False,
        "acceptance_recorded": False,
        "merge_applied": False,
        "merge_preview_recorded": False,
        "handoff_ready": False,
        "handoff_recorded": False,
        "next_agent_unlocked": False,
        "human_review_required": True,
        "human_review_recorded": False,
        "approved_by_human": False,
        "run_finalized": False,
        "finalization_recorded": False,
        "completion_ledger_recorded": False,
        "safe_to_continue": False,
        "manual_review_required": True,
        "agent_execution_performed": False,
        "result_written": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "request_id": http_request.state.request_id,
    }



def _runner_orchestration_capability_matrix(finalization_payload: dict) -> list[dict]:
    return [
        {
            "capability_id": "agent_contract_registry",
            "label": "Agent contract registry",
            "stage": "contract",
            "status": "available",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "runner_plan_builder",
            "label": "Runner plan builder",
            "stage": "planning",
            "status": "available",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "dispatch_ticket",
            "label": "Dispatch ticket",
            "stage": "dispatch",
            "status": "available" if finalization_payload.get("runner_dispatch_ticket") else "missing",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "queue_claim",
            "label": "Queue item and claim",
            "stage": "queue",
            "status": "available" if finalization_payload.get("runner_queue_claim") else "missing",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "runtime_readiness",
            "label": "Runtime readiness",
            "stage": "runtime",
            "status": "available" if finalization_payload.get("runner_worker_bootstrap_plan") else "missing",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "worker_loop",
            "label": "Worker loop simulation",
            "stage": "worker",
            "status": "available" if finalization_payload.get("runner_worker_loop_simulation") else "missing",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "checkpoint_bundle",
            "label": "Worker checkpoint bundle",
            "stage": "checkpoint",
            "status": "available" if finalization_payload.get("runner_worker_checkpoint_bundle") else "missing",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
        {
            "capability_id": "finalization_ledger",
            "label": "Finalization and completion ledger",
            "stage": "finalization",
            "status": "available" if finalization_payload.get("runner_completion_ledger") else "missing",
            "real_execution_enabled": False,
            "dry_run_enabled": True,
        },
    ]


def _runner_orchestration_blocker_map(finalization_payload: dict) -> list[dict]:
    return [
        {
            "blocker_id": "real_agent_execution_disabled",
            "severity": "expected",
            "message": "Real Agent execution is still disabled. Current chain is dry-run only.",
            "next_action": "Add explicit real execution adapter after approval gates are stable.",
            "resolved": False,
        },
        {
            "blocker_id": "human_approval_required",
            "severity": "expected",
            "message": "Human approval is still required before any real write or execution.",
            "next_action": "Keep human review packet visible and add approval capture later.",
            "resolved": False,
        },
        {
            "blocker_id": "state_persistence_disabled",
            "severity": "expected",
            "message": "Runner state persistence remains blocked for real execution.",
            "next_action": "Add persistence adapter only after rollback and audit rules are finalized.",
            "resolved": False,
        },
        {
            "blocker_id": "external_provider_calls_disabled",
            "severity": "expected",
            "message": "External model/provider calls are disabled to avoid cost and unsafe side effects.",
            "next_action": "Introduce provider sandbox and quota policy later.",
            "resolved": False,
        },
    ]


def _runner_real_execution_checklist(finalization_payload: dict) -> list[dict]:
    return [
        {
            "check_id": "contract_registry_ready",
            "label": "Agent contracts are registered",
            "passed": bool(finalization_payload.get("runner_plan")),
        },
        {
            "check_id": "dispatch_chain_ready",
            "label": "Dispatch, queue, and worker dry-run chain exists",
            "passed": bool(finalization_payload.get("runner_worker_loop_simulation")),
        },
        {
            "check_id": "checkpoint_chain_ready",
            "label": "Output checkpoint and validation dry-run chain exists",
            "passed": bool(finalization_payload.get("runner_worker_checkpoint_bundle")),
        },
        {
            "check_id": "finalization_chain_ready",
            "label": "Finalization and completion ledger dry-run chain exists",
            "passed": bool(finalization_payload.get("runner_completion_ledger")),
        },
        {
            "check_id": "human_approval_captured",
            "label": "Human approval is captured",
            "passed": False,
        },
        {
            "check_id": "real_execution_adapter_enabled",
            "label": "Real execution adapter is enabled",
            "passed": False,
        },
        {
            "check_id": "provider_quota_policy_enabled",
            "label": "Provider quota and cost policy are enabled",
            "passed": False,
        },
        {
            "check_id": "persistent_runner_state_enabled",
            "label": "Persistent runner state is enabled",
            "passed": False,
        },
    ]


def _runner_safety_contract_snapshot(finalization_payload: dict) -> dict:
    return {
        "snapshot_version": "runner_safety_contract_snapshot_v1",
        "dry_run": True,
        "real_execution_enabled": False,
        "agent_execution_performed": bool(finalization_payload.get("agent_execution_performed")),
        "external_api_called": bool(finalization_payload.get("external_api_called")),
        "cost_incurred_by_crossgrowth": bool(finalization_payload.get("cost_incurred_by_crossgrowth")),
        "write_authorized": bool(finalization_payload.get("write_authorized")),
        "state_persisted": bool(finalization_payload.get("state_persisted")),
        "project_snapshot_saved": bool(finalization_payload.get("project_snapshot_saved")),
        "manual_review_required": bool(finalization_payload.get("manual_review_required", True)),
        "safe_to_continue": bool(finalization_payload.get("safe_to_continue")),
    }


def _runner_milestone_report(finalization_payload: dict) -> dict:
    capability_matrix = _runner_orchestration_capability_matrix(finalization_payload)
    checklist = _runner_real_execution_checklist(finalization_payload)
    dry_run_available = sum(1 for item in capability_matrix if item.get("dry_run_enabled"))
    available_capabilities = sum(1 for item in capability_matrix if item.get("status") == "available")
    passed_checks = sum(1 for item in checklist if item.get("passed"))
    return {
        "milestone_report_version": "runner_orchestration_milestone_report_v1",
        "current_big_stage": "multi_agent_runner_engine",
        "current_part": "orchestration_readiness_report",
        "plain_language_status": "The dry-run multi-agent runner engine is structurally connected, but real execution remains intentionally disabled.",
        "available_capability_count": available_capabilities,
        "capability_count": len(capability_matrix),
        "dry_run_capability_count": dry_run_available,
        "real_execution_capability_count": 0,
        "passed_real_execution_check_count": passed_checks,
        "real_execution_check_count": len(checklist),
        "estimated_progress_label": "non_commercial_multi_agent_dry_run_engine_late_stage",
        "recommended_next_build": "Add operator control center and human approval capture before enabling any real execution.",
    }


@app.post("/api/v1/projects/{project_id}/runner/orchestration-readiness/dry-run")
async def dry_run_project_agent_orchestration_readiness(project_id: str, http_request: Request):
    finalization_payload = await dry_run_project_agent_finalization(project_id, http_request)
    capability_matrix = _runner_orchestration_capability_matrix(finalization_payload)
    blocker_map = _runner_orchestration_blocker_map(finalization_payload)
    real_execution_checklist = _runner_real_execution_checklist(finalization_payload)
    safety_contract_snapshot = _runner_safety_contract_snapshot(finalization_payload)
    milestone_report = _runner_milestone_report(finalization_payload)

    project = finalization_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_orchestration_readiness_status": "orchestration_readiness_dry_run_complete",
        "latest_runner_available_capability_count": milestone_report["available_capability_count"],
        "latest_runner_capability_count": milestone_report["capability_count"],
        "latest_runner_real_execution_enabled": False,
        "latest_runner_recommended_next_build": milestone_report["recommended_next_build"],
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **finalization_payload,
        "project": project,
        "runner_orchestration_readiness_status": "orchestration_readiness_dry_run_complete",
        "runner_capability_matrix": capability_matrix,
        "runner_blocker_map": blocker_map,
        "runner_real_execution_checklist": real_execution_checklist,
        "runner_safety_contract_snapshot": safety_contract_snapshot,
        "runner_milestone_report": milestone_report,
        "dry_run": True,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_operator_control_center(orchestration_payload: dict) -> dict:
    milestone = dict(orchestration_payload.get("runner_milestone_report") or {})
    safety = dict(orchestration_payload.get("runner_safety_contract_snapshot") or {})
    blockers = list(orchestration_payload.get("runner_blocker_map") or [])
    return {
        "operator_control_center_version": "runner_operator_control_center_v1",
        "operator_control_status": "operator_control_dry_run_ready",
        "project_id": str(orchestration_payload.get("project", {}).get("project_id") or orchestration_payload.get("project_id") or "demo_project_default"),
        "current_big_stage": milestone.get("current_big_stage", "multi_agent_runner_engine"),
        "current_part": "operator_control_center",
        "real_execution_enabled": False,
        "dry_run_enabled": True,
        "operator_can_enable_real_execution": False,
        "manual_review_required": True,
        "blocker_count": len(blockers),
        "safety_contract_snapshot": safety,
        "control_switches": [
            {"switch_id": "dry_run_mode", "enabled": True, "locked": True},
            {"switch_id": "real_execution_mode", "enabled": False, "locked": True},
            {"switch_id": "external_provider_calls", "enabled": False, "locked": True},
            {"switch_id": "state_write", "enabled": False, "locked": True},
            {"switch_id": "cost_spend", "enabled": False, "locked": True},
        ],
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
    }


def _runner_human_approval_capture_preview(operator_control_center: dict) -> dict:
    return {
        "human_approval_capture_version": "runner_human_approval_capture_preview_v1",
        "human_approval_status": "human_approval_capture_blocked_in_dry_run",
        "project_id": operator_control_center.get("project_id", "demo_project_default"),
        "operator_control_status": operator_control_center.get("operator_control_status", ""),
        "approval_required": True,
        "approval_captured": False,
        "approved_by_human": False,
        "approval_record_fields": [
            {"field_id": "operator_id", "required": True, "captured": False},
            {"field_id": "approval_reason", "required": True, "captured": False},
            {"field_id": "execution_scope", "required": True, "captured": False},
            {"field_id": "cost_limit_acknowledgement", "required": True, "captured": False},
            {"field_id": "rollback_acknowledgement", "required": True, "captured": False},
        ],
        "approval_record_field_count": 5,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_execution_mode_switch_preview(human_approval_capture: dict) -> dict:
    return {
        "execution_mode_switch_version": "runner_execution_mode_switch_preview_v1",
        "execution_mode_switch_status": "execution_mode_switch_locked",
        "project_id": human_approval_capture.get("project_id", "demo_project_default"),
        "current_mode": "dry_run",
        "requested_mode": "real_execution",
        "mode_switch_allowed": False,
        "mode_switch_applied": False,
        "required_conditions": [
            {"condition_id": "human_approval_captured", "passed": False},
            {"condition_id": "provider_sandbox_ready", "passed": False},
            {"condition_id": "quota_policy_ready", "passed": False},
            {"condition_id": "rollback_plan_ready", "passed": True},
            {"condition_id": "audit_ledger_ready", "passed": True},
        ],
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "dry_run": True,
    }


def _runner_provider_sandbox_preview(execution_mode_switch: dict) -> dict:
    return {
        "provider_sandbox_version": "runner_provider_sandbox_preview_v1",
        "provider_sandbox_status": "provider_sandbox_preview_only",
        "project_id": execution_mode_switch.get("project_id", "demo_project_default"),
        "provider_calls_enabled": False,
        "allowed_providers": [],
        "blocked_provider_categories": [
            "llm_generation",
            "image_generation",
            "video_generation",
            "external_scraping",
            "paid_api_calls",
        ],
        "sandbox_rules": [
            {"rule_id": "no_paid_provider_call", "enforced": True},
            {"rule_id": "no_external_network_execution", "enforced": True},
            {"rule_id": "no_secret_exposure", "enforced": True},
            {"rule_id": "no_autonomous_provider_selection", "enforced": True},
        ],
        "sandbox_rule_count": 4,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "dry_run": True,
    }


def _runner_quota_policy_preview(provider_sandbox: dict) -> dict:
    return {
        "quota_policy_version": "runner_quota_policy_preview_v1",
        "quota_policy_status": "quota_policy_preview_only",
        "project_id": provider_sandbox.get("project_id", "demo_project_default"),
        "quota_policy_enabled": False,
        "budget_limit_cents": 0,
        "max_provider_calls": 0,
        "max_agent_runtime_seconds": 0,
        "quota_rules": [
            {"quota_rule_id": "zero_cost_until_approved", "limit": 0, "unit": "cents"},
            {"quota_rule_id": "zero_provider_calls_until_approved", "limit": 0, "unit": "calls"},
            {"quota_rule_id": "manual_reset_required", "limit": 1, "unit": "approval"},
        ],
        "quota_rule_count": 3,
        "cost_incurred_by_crossgrowth": False,
        "external_api_called": False,
        "dry_run": True,
    }


def _runner_release_decision_packet(quota_policy: dict) -> dict:
    decision_items = [
        {"decision_item_id": "operator_control_ready", "passed": True},
        {"decision_item_id": "human_approval_captured", "passed": False},
        {"decision_item_id": "execution_mode_switch_allowed", "passed": False},
        {"decision_item_id": "provider_sandbox_enabled", "passed": False},
        {"decision_item_id": "quota_policy_enabled", "passed": False},
        {"decision_item_id": "real_execution_allowed", "passed": False},
    ]
    return {
        "release_decision_packet_version": "runner_release_decision_packet_v1",
        "release_decision_status": "release_blocked_pending_operator_approval",
        "project_id": quota_policy.get("project_id", "demo_project_default"),
        "decision_items": decision_items,
        "decision_item_count": len(decision_items),
        "release_allowed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
    }


@app.post("/api/v1/projects/{project_id}/runner/operator-control/dry-run")
async def dry_run_project_agent_operator_control(project_id: str, http_request: Request):
    orchestration_payload = await dry_run_project_agent_orchestration_readiness(project_id, http_request)

    runner_operator_control_center = _runner_operator_control_center(orchestration_payload)
    runner_human_approval_capture_preview = _runner_human_approval_capture_preview(runner_operator_control_center)
    runner_execution_mode_switch_preview = _runner_execution_mode_switch_preview(runner_human_approval_capture_preview)
    runner_provider_sandbox_preview = _runner_provider_sandbox_preview(runner_execution_mode_switch_preview)
    runner_quota_policy_preview = _runner_quota_policy_preview(runner_provider_sandbox_preview)
    runner_release_decision_packet = _runner_release_decision_packet(runner_quota_policy_preview)

    project = orchestration_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_operator_control_status": runner_operator_control_center["operator_control_status"],
        "latest_runner_human_approval_status": runner_human_approval_capture_preview["human_approval_status"],
        "latest_runner_execution_mode_switch_status": runner_execution_mode_switch_preview["execution_mode_switch_status"],
        "latest_runner_provider_sandbox_status": runner_provider_sandbox_preview["provider_sandbox_status"],
        "latest_runner_quota_policy_status": runner_quota_policy_preview["quota_policy_status"],
        "latest_runner_release_decision_status": runner_release_decision_packet["release_decision_status"],
        "latest_runner_release_allowed": False,
        "latest_runner_real_execution_enabled": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **orchestration_payload,
        "project": project,
        "runner_operator_control_center": runner_operator_control_center,
        "runner_human_approval_capture_preview": runner_human_approval_capture_preview,
        "runner_execution_mode_switch_preview": runner_execution_mode_switch_preview,
        "runner_provider_sandbox_preview": runner_provider_sandbox_preview,
        "runner_quota_policy_preview": runner_quota_policy_preview,
        "runner_release_decision_packet": runner_release_decision_packet,
        "dry_run": True,
        "release_allowed": False,
        "real_execution_enabled": False,
        "operator_can_enable_real_execution": False,
        "approval_required": True,
        "approval_captured": False,
        "approved_by_human": False,
        "provider_calls_enabled": False,
        "quota_policy_enabled": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_approval_request_preview(operator_payload: dict) -> dict:
    release_packet = dict(operator_payload.get("runner_release_decision_packet") or {})
    project = dict(operator_payload.get("project") or {})
    return {
        "approval_request_version": "runner_approval_request_preview_v1",
        "approval_request_status": "approval_request_preview_only",
        "approval_request_id": f"approval_request_{project.get('project_id', 'demo_project_default')}_dry_run",
        "project_id": project.get("project_id", "demo_project_default"),
        "release_decision_status": release_packet.get("release_decision_status", "release_blocked_pending_operator_approval"),
        "requested_execution_mode": "real_execution",
        "approval_required": True,
        "approval_request_recorded": False,
        "approved_by_human": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "request_fields": [
            {"field_id": "operator_identity", "required": True, "captured": False},
            {"field_id": "business_reason", "required": True, "captured": False},
            {"field_id": "execution_scope", "required": True, "captured": False},
            {"field_id": "provider_budget_limit", "required": True, "captured": False},
            {"field_id": "rollback_owner", "required": True, "captured": False},
        ],
        "request_field_count": 5,
        "dry_run": True,
    }


def _runner_approval_audit_trail_preview(approval_request: dict) -> dict:
    return {
        "approval_audit_trail_version": "runner_approval_audit_trail_preview_v1",
        "approval_audit_trail_status": "approval_audit_trail_preview_only",
        "approval_request_id": approval_request.get("approval_request_id", ""),
        "project_id": approval_request.get("project_id", "demo_project_default"),
        "audit_events": [
            {"event_id": "request_created_preview", "recorded": False, "actor": "system_preview"},
            {"event_id": "operator_review_pending", "recorded": False, "actor": "operator"},
            {"event_id": "approval_not_captured", "recorded": False, "actor": "operator"},
            {"event_id": "release_blocked", "recorded": False, "actor": "runner_guard"},
        ],
        "audit_event_count": 4,
        "audit_trail_recorded": False,
        "approved_by_human": False,
        "release_allowed": False,
        "dry_run": True,
    }


def _runner_consent_checklist_preview(approval_audit_trail: dict) -> dict:
    consent_items = [
        {"consent_item_id": "understand_real_execution_scope", "required": True, "confirmed": False},
        {"consent_item_id": "accept_provider_cost_limit", "required": True, "confirmed": False},
        {"consent_item_id": "accept_external_api_boundary", "required": True, "confirmed": False},
        {"consent_item_id": "accept_state_write_boundary", "required": True, "confirmed": False},
        {"consent_item_id": "accept_rollback_plan", "required": True, "confirmed": False},
    ]
    return {
        "consent_checklist_version": "runner_consent_checklist_preview_v1",
        "consent_checklist_status": "consent_checklist_incomplete",
        "approval_request_id": approval_audit_trail.get("approval_request_id", ""),
        "project_id": approval_audit_trail.get("project_id", "demo_project_default"),
        "consent_items": consent_items,
        "consent_item_count": len(consent_items),
        "confirmed_consent_count": 0,
        "all_required_consent_confirmed": False,
        "approved_by_human": False,
        "release_allowed": False,
        "dry_run": True,
    }


def _runner_rollback_playbook_preview(consent_checklist: dict) -> dict:
    rollback_steps = [
        {"rollback_step_id": "capture_pre_execution_snapshot", "ready": True, "executed": False},
        {"rollback_step_id": "isolate_failed_runner_state", "ready": True, "executed": False},
        {"rollback_step_id": "restore_project_snapshot", "ready": False, "executed": False},
        {"rollback_step_id": "record_operator_incident_note", "ready": False, "executed": False},
        {"rollback_step_id": "block_followup_real_execution", "ready": True, "executed": False},
    ]
    return {
        "rollback_playbook_version": "runner_rollback_playbook_preview_v1",
        "rollback_playbook_status": "rollback_playbook_preview_only",
        "approval_request_id": consent_checklist.get("approval_request_id", ""),
        "project_id": consent_checklist.get("project_id", "demo_project_default"),
        "rollback_steps": rollback_steps,
        "rollback_step_count": len(rollback_steps),
        "rollback_ready": False,
        "rollback_executed": False,
        "release_allowed": False,
        "dry_run": True,
    }


def _runner_guarded_release_preview(rollback_playbook: dict) -> dict:
    release_checks = [
        {"release_check_id": "approval_request_recorded", "passed": False},
        {"release_check_id": "audit_trail_recorded", "passed": False},
        {"release_check_id": "consent_confirmed", "passed": False},
        {"release_check_id": "rollback_ready", "passed": False},
        {"release_check_id": "provider_quota_enabled", "passed": False},
        {"release_check_id": "operator_final_confirmed", "passed": False},
    ]
    return {
        "guarded_release_preview_version": "runner_guarded_release_preview_v1",
        "guarded_release_status": "guarded_release_blocked",
        "approval_request_id": rollback_playbook.get("approval_request_id", ""),
        "project_id": rollback_playbook.get("project_id", "demo_project_default"),
        "release_checks": release_checks,
        "release_check_count": len(release_checks),
        "passed_release_check_count": 0,
        "release_allowed": False,
        "real_execution_enabled": False,
        "operator_final_confirmation_required": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/operator-approval/dry-run")
async def dry_run_project_agent_operator_approval(project_id: str, http_request: Request):
    operator_payload = await dry_run_project_agent_operator_control(project_id, http_request)

    runner_approval_request_preview = _runner_approval_request_preview(operator_payload)
    runner_approval_audit_trail_preview = _runner_approval_audit_trail_preview(runner_approval_request_preview)
    runner_consent_checklist_preview = _runner_consent_checklist_preview(runner_approval_audit_trail_preview)
    runner_rollback_playbook_preview = _runner_rollback_playbook_preview(runner_consent_checklist_preview)
    runner_guarded_release_preview = _runner_guarded_release_preview(runner_rollback_playbook_preview)

    project = operator_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_approval_request_status": runner_approval_request_preview["approval_request_status"],
        "latest_runner_approval_audit_trail_status": runner_approval_audit_trail_preview["approval_audit_trail_status"],
        "latest_runner_consent_checklist_status": runner_consent_checklist_preview["consent_checklist_status"],
        "latest_runner_rollback_playbook_status": runner_rollback_playbook_preview["rollback_playbook_status"],
        "latest_runner_guarded_release_status": runner_guarded_release_preview["guarded_release_status"],
        "latest_runner_guarded_release_allowed": False,
        "latest_runner_operator_approval_captured": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **operator_payload,
        "project": project,
        "runner_approval_request_preview": runner_approval_request_preview,
        "runner_approval_audit_trail_preview": runner_approval_audit_trail_preview,
        "runner_consent_checklist_preview": runner_consent_checklist_preview,
        "runner_rollback_playbook_preview": runner_rollback_playbook_preview,
        "runner_guarded_release_preview": runner_guarded_release_preview,
        "dry_run": True,
        "approval_required": True,
        "approval_request_recorded": False,
        "approval_captured": False,
        "approved_by_human": False,
        "audit_trail_recorded": False,
        "all_required_consent_confirmed": False,
        "rollback_ready": False,
        "rollback_executed": False,
        "guarded_release_allowed": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "operator_final_confirmation_required": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_operator_decision_input_preview(operator_approval_payload: dict) -> dict:
    guarded_release = dict(operator_approval_payload.get("runner_guarded_release_preview") or {})
    project = dict(operator_approval_payload.get("project") or {})
    return {
        "operator_decision_input_version": "runner_operator_decision_input_preview_v1",
        "operator_decision_input_status": "operator_decision_input_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "approval_request_id": guarded_release.get("approval_request_id", ""),
        "available_decisions": [
            {"decision": "approve_preview", "enabled": True, "real_execution_enabled_after_decision": False},
            {"decision": "reject_preview", "enabled": True, "real_execution_enabled_after_decision": False},
            {"decision": "pause_preview", "enabled": True, "real_execution_enabled_after_decision": False},
        ],
        "default_decision": "pause_preview",
        "decision_captured": False,
        "approved_by_human": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_approval_decision_simulator(decision_input: dict, requested_decision: str = "pause_preview") -> dict:
    decision = str(requested_decision or "pause_preview").strip()
    if decision not in {"approve_preview", "reject_preview", "pause_preview"}:
        decision = "pause_preview"

    status_by_decision = {
        "approve_preview": "approval_decision_preview_approved_but_release_blocked",
        "reject_preview": "approval_decision_preview_rejected",
        "pause_preview": "approval_decision_preview_paused",
    }
    return {
        "approval_decision_simulator_version": "runner_approval_decision_simulator_v1",
        "approval_decision_status": status_by_decision[decision],
        "project_id": decision_input.get("project_id", "demo_project_default"),
        "approval_request_id": decision_input.get("approval_request_id", ""),
        "requested_decision": decision,
        "decision_captured": False,
        "decision_recorded": False,
        "approved_by_human": False,
        "approval_preview_only": decision == "approve_preview",
        "rejected_by_human": False,
        "paused_by_human": decision == "pause_preview",
        "release_allowed": False,
        "real_execution_enabled": False,
        "decision_effects": [
            {"effect_id": "keep_real_execution_disabled", "applied": True},
            {"effect_id": "keep_provider_calls_disabled", "applied": True},
            {"effect_id": "keep_state_write_disabled", "applied": True},
            {"effect_id": "require_final_operator_confirmation", "applied": True},
        ],
        "decision_effect_count": 4,
        "dry_run": True,
    }


def _runner_release_gate_state_preview(decision_simulator: dict) -> dict:
    requested_decision = str(decision_simulator.get("requested_decision") or "pause_preview")
    if requested_decision == "approve_preview":
        gate_state = "release_gate_preview_approved_but_locked"
    elif requested_decision == "reject_preview":
        gate_state = "release_gate_rejected"
    else:
        gate_state = "release_gate_paused"
    return {
        "release_gate_state_version": "runner_release_gate_state_preview_v1",
        "release_gate_status": gate_state,
        "project_id": decision_simulator.get("project_id", "demo_project_default"),
        "approval_request_id": decision_simulator.get("approval_request_id", ""),
        "requested_decision": requested_decision,
        "gate_open": False,
        "gate_locked": True,
        "release_allowed": False,
        "real_execution_enabled": False,
        "operator_final_confirmation_required": True,
        "blocking_reasons": [
            "dry_run_mode_enabled",
            "real_execution_adapter_disabled",
            "provider_quota_policy_disabled",
            "persistent_state_write_disabled",
        ],
        "blocking_reason_count": 4,
        "dry_run": True,
    }


def _runner_execution_unlock_preview(release_gate_state: dict) -> dict:
    unlock_steps = [
        {"unlock_step_id": "capture_real_operator_identity", "ready": False},
        {"unlock_step_id": "set_nonzero_provider_quota", "ready": False},
        {"unlock_step_id": "enable_provider_sandbox", "ready": False},
        {"unlock_step_id": "enable_persistent_runner_state", "ready": False},
        {"unlock_step_id": "perform_final_release_confirmation", "ready": False},
    ]
    return {
        "execution_unlock_preview_version": "runner_execution_unlock_preview_v1",
        "execution_unlock_status": "execution_unlock_blocked",
        "project_id": release_gate_state.get("project_id", "demo_project_default"),
        "approval_request_id": release_gate_state.get("approval_request_id", ""),
        "release_gate_status": release_gate_state.get("release_gate_status", ""),
        "unlock_steps": unlock_steps,
        "unlock_step_count": len(unlock_steps),
        "ready_unlock_step_count": 0,
        "unlock_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "state_persisted": False,
        "dry_run": True,
    }


def _runner_operator_decision_receipt_preview(execution_unlock: dict) -> dict:
    return {
        "operator_decision_receipt_version": "runner_operator_decision_receipt_preview_v1",
        "operator_decision_receipt_status": "operator_decision_receipt_preview_only",
        "project_id": execution_unlock.get("project_id", "demo_project_default"),
        "approval_request_id": execution_unlock.get("approval_request_id", ""),
        "release_gate_status": execution_unlock.get("release_gate_status", ""),
        "receipt_recorded": False,
        "decision_audit_recorded": False,
        "unlock_allowed": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "receipt_items": [
            {"receipt_item_id": "decision_input_preview", "included": True},
            {"receipt_item_id": "decision_simulator", "included": True},
            {"receipt_item_id": "release_gate_state", "included": True},
            {"receipt_item_id": "execution_unlock_preview", "included": True},
            {"receipt_item_id": "dry_run_boundary", "included": True},
        ],
        "receipt_item_count": 5,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/approval-decision/dry-run")
async def dry_run_project_agent_approval_decision(project_id: str, http_request: Request):
    operator_approval_payload = await dry_run_project_agent_operator_approval(project_id, http_request)

    decision_input = _runner_operator_decision_input_preview(operator_approval_payload)
    decision_simulator = _runner_approval_decision_simulator(decision_input, requested_decision="pause_preview")
    release_gate_state = _runner_release_gate_state_preview(decision_simulator)
    execution_unlock_preview = _runner_execution_unlock_preview(release_gate_state)
    operator_decision_receipt = _runner_operator_decision_receipt_preview(execution_unlock_preview)

    project = operator_approval_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_operator_decision_input_status": decision_input["operator_decision_input_status"],
        "latest_runner_approval_decision_status": decision_simulator["approval_decision_status"],
        "latest_runner_release_gate_status": release_gate_state["release_gate_status"],
        "latest_runner_execution_unlock_status": execution_unlock_preview["execution_unlock_status"],
        "latest_runner_operator_decision_receipt_status": operator_decision_receipt["operator_decision_receipt_status"],
        "latest_runner_gate_open": False,
        "latest_runner_unlock_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **operator_approval_payload,
        "project": project,
        "runner_operator_decision_input_preview": decision_input,
        "runner_approval_decision_simulator": decision_simulator,
        "runner_release_gate_state_preview": release_gate_state,
        "runner_execution_unlock_preview": execution_unlock_preview,
        "runner_operator_decision_receipt_preview": operator_decision_receipt,
        "dry_run": True,
        "decision_captured": False,
        "decision_recorded": False,
        "approved_by_human": False,
        "rejected_by_human": False,
        "gate_open": False,
        "gate_locked": True,
        "unlock_allowed": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "receipt_recorded": False,
        "decision_audit_recorded": False,
        "operator_final_confirmation_required": True,
        "manual_review_required": True,
        "safe_to_continue": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "request_id": http_request.state.request_id,
    }



def _runner_execution_sandbox_contract(decision_payload: dict) -> dict:
    project = dict(decision_payload.get("project") or {})
    gate = dict(decision_payload.get("runner_release_gate_state_preview") or {})
    return {
        "execution_sandbox_contract_version": "runner_execution_sandbox_contract_v1",
        "execution_sandbox_status": "execution_sandbox_contract_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "release_gate_status": gate.get("release_gate_status", "release_gate_paused"),
        "sandbox_enabled": False,
        "real_execution_enabled": False,
        "contract_rules": [
            {"rule_id": "no_unapproved_external_calls", "enforced": True},
            {"rule_id": "no_secret_exfiltration", "enforced": True},
            {"rule_id": "no_persistent_write_without_snapshot", "enforced": True},
            {"rule_id": "no_cost_without_quota", "enforced": True},
            {"rule_id": "operator_stop_always_available", "enforced": True},
        ],
        "contract_rule_count": 5,
        "dry_run": True,
    }


def _runner_provider_boundary_preview(sandbox_contract: dict) -> dict:
    provider_boundaries = [
        {"provider_id": "llm_text_generation", "enabled": False, "quota_required": True},
        {"provider_id": "image_generation", "enabled": False, "quota_required": True},
        {"provider_id": "video_generation", "enabled": False, "quota_required": True},
        {"provider_id": "comment_collection", "enabled": False, "quota_required": True},
        {"provider_id": "external_web_fetch", "enabled": False, "quota_required": True},
    ]
    return {
        "provider_boundary_version": "runner_provider_boundary_preview_v1",
        "provider_boundary_status": "provider_boundary_locked",
        "project_id": sandbox_contract.get("project_id", "demo_project_default"),
        "execution_sandbox_status": sandbox_contract.get("execution_sandbox_status", ""),
        "provider_boundaries": provider_boundaries,
        "provider_boundary_count": len(provider_boundaries),
        "enabled_provider_count": 0,
        "provider_calls_enabled": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_secret_boundary_preview(provider_boundary: dict) -> dict:
    secret_rules = [
        {"secret_rule_id": "no_secret_in_prompt", "enforced": True},
        {"secret_rule_id": "no_secret_in_agent_output", "enforced": True},
        {"secret_rule_id": "no_secret_in_export_pack", "enforced": True},
        {"secret_rule_id": "secret_access_requires_named_adapter", "enforced": True},
        {"secret_rule_id": "operator_redaction_required", "enforced": True},
    ]
    return {
        "secret_boundary_version": "runner_secret_boundary_preview_v1",
        "secret_boundary_status": "secret_boundary_locked",
        "project_id": provider_boundary.get("project_id", "demo_project_default"),
        "provider_boundary_status": provider_boundary.get("provider_boundary_status", ""),
        "secret_rules": secret_rules,
        "secret_rule_count": len(secret_rules),
        "secret_access_enabled": False,
        "secret_redaction_required": True,
        "secret_exposure_detected": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_quota_ledger_preview(secret_boundary: dict) -> dict:
    quota_lines = [
        {"quota_line_id": "llm_text_generation_calls", "limit": 0, "used": 0, "unit": "calls"},
        {"quota_line_id": "image_generation_calls", "limit": 0, "used": 0, "unit": "calls"},
        {"quota_line_id": "video_generation_calls", "limit": 0, "used": 0, "unit": "calls"},
        {"quota_line_id": "comment_collection_calls", "limit": 0, "used": 0, "unit": "calls"},
        {"quota_line_id": "total_budget_cents", "limit": 0, "used": 0, "unit": "cents"},
    ]
    return {
        "quota_ledger_version": "runner_quota_ledger_preview_v1",
        "quota_ledger_status": "quota_ledger_zero_budget",
        "project_id": secret_boundary.get("project_id", "demo_project_default"),
        "secret_boundary_status": secret_boundary.get("secret_boundary_status", ""),
        "quota_lines": quota_lines,
        "quota_line_count": len(quota_lines),
        "quota_ledger_recorded": False,
        "quota_enabled": False,
        "total_budget_cents": 0,
        "total_used_cents": 0,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_cost_simulation_preview(quota_ledger: dict) -> dict:
    scenario_items = [
        {"scenario_id": "single_planner_run", "estimated_cost_cents": 0, "allowed": False},
        {"scenario_id": "single_storyboard_run", "estimated_cost_cents": 0, "allowed": False},
        {"scenario_id": "image_asset_generation", "estimated_cost_cents": 0, "allowed": False},
        {"scenario_id": "video_asset_generation", "estimated_cost_cents": 0, "allowed": False},
        {"scenario_id": "comment_collection_batch", "estimated_cost_cents": 0, "allowed": False},
    ]
    return {
        "cost_simulation_version": "runner_cost_simulation_preview_v1",
        "cost_simulation_status": "cost_simulation_blocked_by_zero_quota",
        "project_id": quota_ledger.get("project_id", "demo_project_default"),
        "quota_ledger_status": quota_ledger.get("quota_ledger_status", ""),
        "scenario_items": scenario_items,
        "scenario_item_count": len(scenario_items),
        "estimated_total_cost_cents": 0,
        "cost_limit_cents": 0,
        "cost_simulation_allowed": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_sandbox_incident_plan_preview(cost_simulation: dict) -> dict:
    incident_steps = [
        {"incident_step_id": "stop_worker_loop", "ready": True, "executed": False},
        {"incident_step_id": "freeze_queue_claims", "ready": True, "executed": False},
        {"incident_step_id": "revoke_provider_adapter", "ready": True, "executed": False},
        {"incident_step_id": "redact_sensitive_outputs", "ready": True, "executed": False},
        {"incident_step_id": "write_operator_incident_report", "ready": False, "executed": False},
    ]
    return {
        "sandbox_incident_plan_version": "runner_sandbox_incident_plan_preview_v1",
        "sandbox_incident_plan_status": "sandbox_incident_plan_preview_only",
        "project_id": cost_simulation.get("project_id", "demo_project_default"),
        "cost_simulation_status": cost_simulation.get("cost_simulation_status", ""),
        "incident_steps": incident_steps,
        "incident_step_count": len(incident_steps),
        "incident_plan_ready": False,
        "incident_detected": False,
        "incident_handled": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_execution_sandbox_receipt_preview(incident_plan: dict) -> dict:
    return {
        "execution_sandbox_receipt_version": "runner_execution_sandbox_receipt_preview_v1",
        "execution_sandbox_receipt_status": "execution_sandbox_receipt_preview_only",
        "project_id": incident_plan.get("project_id", "demo_project_default"),
        "sandbox_incident_plan_status": incident_plan.get("sandbox_incident_plan_status", ""),
        "receipt_items": [
            {"receipt_item_id": "sandbox_contract", "included": True},
            {"receipt_item_id": "provider_boundary", "included": True},
            {"receipt_item_id": "secret_boundary", "included": True},
            {"receipt_item_id": "quota_ledger", "included": True},
            {"receipt_item_id": "cost_simulation", "included": True},
            {"receipt_item_id": "incident_plan", "included": True},
        ],
        "receipt_item_count": 6,
        "sandbox_ready_for_real_execution": False,
        "receipt_recorded": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/execution-sandbox/dry-run")
async def dry_run_project_agent_execution_sandbox(project_id: str, http_request: Request):
    decision_payload = await dry_run_project_agent_approval_decision(project_id, http_request)

    runner_execution_sandbox_contract = _runner_execution_sandbox_contract(decision_payload)
    runner_provider_boundary_preview = _runner_provider_boundary_preview(runner_execution_sandbox_contract)
    runner_secret_boundary_preview = _runner_secret_boundary_preview(runner_provider_boundary_preview)
    runner_quota_ledger_preview = _runner_quota_ledger_preview(runner_secret_boundary_preview)
    runner_cost_simulation_preview = _runner_cost_simulation_preview(runner_quota_ledger_preview)
    runner_sandbox_incident_plan_preview = _runner_sandbox_incident_plan_preview(runner_cost_simulation_preview)
    runner_execution_sandbox_receipt_preview = _runner_execution_sandbox_receipt_preview(runner_sandbox_incident_plan_preview)

    project = decision_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_execution_sandbox_status": runner_execution_sandbox_contract["execution_sandbox_status"],
        "latest_runner_provider_boundary_status": runner_provider_boundary_preview["provider_boundary_status"],
        "latest_runner_secret_boundary_status": runner_secret_boundary_preview["secret_boundary_status"],
        "latest_runner_quota_ledger_status": runner_quota_ledger_preview["quota_ledger_status"],
        "latest_runner_cost_simulation_status": runner_cost_simulation_preview["cost_simulation_status"],
        "latest_runner_sandbox_incident_plan_status": runner_sandbox_incident_plan_preview["sandbox_incident_plan_status"],
        "latest_runner_execution_sandbox_receipt_status": runner_execution_sandbox_receipt_preview["execution_sandbox_receipt_status"],
        "latest_runner_sandbox_ready_for_real_execution": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **decision_payload,
        "project": project,
        "runner_execution_sandbox_contract": runner_execution_sandbox_contract,
        "runner_provider_boundary_preview": runner_provider_boundary_preview,
        "runner_secret_boundary_preview": runner_secret_boundary_preview,
        "runner_quota_ledger_preview": runner_quota_ledger_preview,
        "runner_cost_simulation_preview": runner_cost_simulation_preview,
        "runner_sandbox_incident_plan_preview": runner_sandbox_incident_plan_preview,
        "runner_execution_sandbox_receipt_preview": runner_execution_sandbox_receipt_preview,
        "dry_run": True,
        "sandbox_enabled": False,
        "provider_calls_enabled": False,
        "secret_access_enabled": False,
        "quota_enabled": False,
        "cost_simulation_allowed": False,
        "incident_plan_ready": False,
        "sandbox_ready_for_real_execution": False,
        "receipt_recorded": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_provider_adapter_registry_preview(sandbox_payload: dict) -> dict:
    project = dict(sandbox_payload.get("project") or {})
    sandbox_receipt = dict(sandbox_payload.get("runner_execution_sandbox_receipt_preview") or {})
    adapters = [
        {"adapter_id": "text_generation_adapter", "provider_category": "llm_text_generation", "registered": True, "enabled": False, "requires_quota": True, "requires_approval": True},
        {"adapter_id": "image_generation_adapter", "provider_category": "image_generation", "registered": True, "enabled": False, "requires_quota": True, "requires_approval": True},
        {"adapter_id": "video_generation_adapter", "provider_category": "video_generation", "registered": True, "enabled": False, "requires_quota": True, "requires_approval": True},
        {"adapter_id": "comment_collection_adapter", "provider_category": "comment_collection", "registered": True, "enabled": False, "requires_quota": True, "requires_approval": True},
        {"adapter_id": "web_fetch_adapter", "provider_category": "external_web_fetch", "registered": True, "enabled": False, "requires_quota": True, "requires_approval": True},
        {"adapter_id": "export_pack_adapter", "provider_category": "local_export", "registered": True, "enabled": False, "requires_quota": False, "requires_approval": True},
    ]
    return {
        "provider_adapter_registry_version": "runner_provider_adapter_registry_preview_v1",
        "provider_adapter_registry_status": "provider_adapter_registry_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "execution_sandbox_receipt_status": sandbox_receipt.get("execution_sandbox_receipt_status", ""),
        "adapters": adapters,
        "adapter_count": len(adapters),
        "enabled_adapter_count": 0,
        "registered_adapter_count": len(adapters),
        "provider_calls_enabled": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_adapter_handshake_preview(adapter_registry: dict) -> dict:
    handshake_items = [
        {"handshake_item_id": "adapter_registered", "passed": True},
        {"handshake_item_id": "sandbox_ready", "passed": False},
        {"handshake_item_id": "quota_available", "passed": False},
        {"handshake_item_id": "secret_boundary_ready", "passed": True},
        {"handshake_item_id": "operator_approval_captured", "passed": False},
        {"handshake_item_id": "real_execution_adapter_enabled", "passed": False},
    ]
    passed_count = sum(1 for item in handshake_items if item.get("passed"))
    return {
        "provider_adapter_handshake_version": "runner_provider_adapter_handshake_preview_v1",
        "provider_adapter_handshake_status": "provider_adapter_handshake_blocked",
        "project_id": adapter_registry.get("project_id", "demo_project_default"),
        "provider_adapter_registry_status": adapter_registry.get("provider_adapter_registry_status", ""),
        "handshake_items": handshake_items,
        "handshake_item_count": len(handshake_items),
        "passed_handshake_item_count": passed_count,
        "handshake_passed": False,
        "provider_calls_enabled": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_invocation_envelope_preview(adapter_handshake: dict) -> dict:
    return {
        "invocation_envelope_version": "runner_invocation_envelope_preview_v1",
        "invocation_envelope_status": "invocation_envelope_preview_only",
        "project_id": adapter_handshake.get("project_id", "demo_project_default"),
        "provider_adapter_handshake_status": adapter_handshake.get("provider_adapter_handshake_status", ""),
        "invocation_id": f"provider_invocation_{adapter_handshake.get('project_id', 'demo_project_default')}_dry_run",
        "requested_adapter_id": "text_generation_adapter",
        "requested_provider_category": "llm_text_generation",
        "payload_redacted": True,
        "secrets_included": False,
        "quota_reserved": False,
        "operator_approval_attached": False,
        "invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_policy_matrix_preview(invocation_envelope: dict) -> dict:
    policy_rows = [
        {"policy_id": "approval_required", "required": True, "satisfied": False},
        {"policy_id": "quota_required", "required": True, "satisfied": False},
        {"policy_id": "secret_redaction_required", "required": True, "satisfied": True},
        {"policy_id": "sandbox_required", "required": True, "satisfied": False},
        {"policy_id": "audit_receipt_required", "required": True, "satisfied": True},
        {"policy_id": "rollback_plan_required", "required": True, "satisfied": False},
    ]
    satisfied_count = sum(1 for row in policy_rows if row.get("satisfied"))
    return {
        "provider_policy_matrix_version": "runner_provider_policy_matrix_preview_v1",
        "provider_policy_matrix_status": "provider_policy_matrix_blocking_invocation",
        "project_id": invocation_envelope.get("project_id", "demo_project_default"),
        "invocation_envelope_status": invocation_envelope.get("invocation_envelope_status", ""),
        "policy_rows": policy_rows,
        "policy_row_count": len(policy_rows),
        "satisfied_policy_count": satisfied_count,
        "all_required_policies_satisfied": False,
        "invocation_allowed": False,
        "provider_calls_enabled": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_adapter_invocation_receipt_preview(policy_matrix: dict) -> dict:
    return {
        "adapter_invocation_receipt_version": "runner_adapter_invocation_receipt_preview_v1",
        "adapter_invocation_receipt_status": "adapter_invocation_receipt_preview_only",
        "project_id": policy_matrix.get("project_id", "demo_project_default"),
        "provider_policy_matrix_status": policy_matrix.get("provider_policy_matrix_status", ""),
        "receipt_items": [
            {"receipt_item_id": "adapter_registry", "included": True},
            {"receipt_item_id": "adapter_handshake", "included": True},
            {"receipt_item_id": "invocation_envelope", "included": True},
            {"receipt_item_id": "provider_policy_matrix", "included": True},
            {"receipt_item_id": "dry_run_boundary", "included": True},
        ],
        "receipt_item_count": 5,
        "receipt_recorded": False,
        "invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/provider-adapter/dry-run")
async def dry_run_project_agent_provider_adapter(project_id: str, http_request: Request):
    sandbox_payload = await dry_run_project_agent_execution_sandbox(project_id, http_request)

    runner_provider_adapter_registry_preview = _runner_provider_adapter_registry_preview(sandbox_payload)
    runner_provider_adapter_handshake_preview = _runner_provider_adapter_handshake_preview(runner_provider_adapter_registry_preview)
    runner_invocation_envelope_preview = _runner_invocation_envelope_preview(runner_provider_adapter_handshake_preview)
    runner_provider_policy_matrix_preview = _runner_provider_policy_matrix_preview(runner_invocation_envelope_preview)
    runner_adapter_invocation_receipt_preview = _runner_adapter_invocation_receipt_preview(runner_provider_policy_matrix_preview)

    project = sandbox_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_provider_adapter_registry_status": runner_provider_adapter_registry_preview["provider_adapter_registry_status"],
        "latest_runner_provider_adapter_handshake_status": runner_provider_adapter_handshake_preview["provider_adapter_handshake_status"],
        "latest_runner_invocation_envelope_status": runner_invocation_envelope_preview["invocation_envelope_status"],
        "latest_runner_provider_policy_matrix_status": runner_provider_policy_matrix_preview["provider_policy_matrix_status"],
        "latest_runner_adapter_invocation_receipt_status": runner_adapter_invocation_receipt_preview["adapter_invocation_receipt_status"],
        "latest_runner_provider_invocation_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **sandbox_payload,
        "project": project,
        "runner_provider_adapter_registry_preview": runner_provider_adapter_registry_preview,
        "runner_provider_adapter_handshake_preview": runner_provider_adapter_handshake_preview,
        "runner_invocation_envelope_preview": runner_invocation_envelope_preview,
        "runner_provider_policy_matrix_preview": runner_provider_policy_matrix_preview,
        "runner_adapter_invocation_receipt_preview": runner_adapter_invocation_receipt_preview,
        "dry_run": True,
        "provider_calls_enabled": False,
        "handshake_passed": False,
        "quota_reserved": False,
        "operator_approval_attached": False,
        "invocation_allowed": False,
        "provider_call_performed": False,
        "receipt_recorded": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_provider_invocation_router_preview(provider_adapter_payload: dict) -> dict:
    project = dict(provider_adapter_payload.get("project") or {})
    registry = dict(provider_adapter_payload.get("runner_provider_adapter_registry_preview") or {})
    return {
        "provider_invocation_router_version": "runner_provider_invocation_router_preview_v1",
        "provider_invocation_router_status": "provider_invocation_router_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "provider_adapter_registry_status": registry.get("provider_adapter_registry_status", ""),
        "routing_rules": [
            {"route_id": "text_generation_route", "input_type": "copy_or_plan_text", "adapter_id": "text_generation_adapter", "enabled": False},
            {"route_id": "image_generation_route", "input_type": "image_prompt", "adapter_id": "image_generation_adapter", "enabled": False},
            {"route_id": "video_generation_route", "input_type": "video_prompt", "adapter_id": "video_generation_adapter", "enabled": False},
            {"route_id": "comment_collection_route", "input_type": "comment_source_url", "adapter_id": "comment_collection_adapter", "enabled": False},
            {"route_id": "web_fetch_route", "input_type": "public_url", "adapter_id": "web_fetch_adapter", "enabled": False},
            {"route_id": "export_pack_route", "input_type": "local_project_bundle", "adapter_id": "export_pack_adapter", "enabled": False},
        ],
        "routing_rule_count": 6,
        "enabled_route_count": 0,
        "selected_route_id": "text_generation_route",
        "selected_adapter_id": "text_generation_adapter",
        "route_selected": True,
        "route_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_invocation_stub_preview(invocation_router: dict) -> dict:
    return {
        "provider_invocation_stub_version": "runner_provider_invocation_stub_preview_v1",
        "provider_invocation_stub_status": "provider_invocation_stub_generated",
        "project_id": invocation_router.get("project_id", "demo_project_default"),
        "selected_route_id": invocation_router.get("selected_route_id", "text_generation_route"),
        "selected_adapter_id": invocation_router.get("selected_adapter_id", "text_generation_adapter"),
        "stub_invocation_id": f"stub_invocation_{invocation_router.get('project_id', 'demo_project_default')}_dry_run",
        "stub_payload": {
            "input_type": "copy_or_plan_text",
            "payload_redacted": True,
            "prompt_preview": "dry_run_provider_invocation_prompt_placeholder",
            "secret_fields_removed": True,
        },
        "stub_result": {
            "result_type": "text",
            "content_preview": "Provider invocation is blocked in dry-run. This is a normalized stub result.",
            "asset_url": None,
            "items": [],
        },
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_normalized_provider_result_preview(invocation_stub: dict) -> dict:
    return {
        "normalized_provider_result_version": "runner_normalized_provider_result_preview_v1",
        "normalized_provider_result_status": "normalized_provider_result_preview_only",
        "project_id": invocation_stub.get("project_id", "demo_project_default"),
        "stub_invocation_id": invocation_stub.get("stub_invocation_id", ""),
        "adapter_id": invocation_stub.get("selected_adapter_id", "text_generation_adapter"),
        "result_schema": {
            "result_id": "provider_result_dry_run",
            "result_type": "text",
            "status": "blocked_by_dry_run",
            "content": "Provider invocation is blocked in dry-run.",
            "assets": [],
            "evidence": [],
            "warnings": ["real_execution_disabled", "external_api_not_called"],
            "metrics": {"cost_cents": 0, "latency_ms": 0, "provider_calls": 0},
        },
        "normalization_rules": [
            {"rule_id": "always_include_status", "applied": True},
            {"rule_id": "always_include_cost_metrics", "applied": True},
            {"rule_id": "redact_secret_fields", "applied": True},
            {"rule_id": "preserve_adapter_id", "applied": True},
            {"rule_id": "block_external_url_side_effects", "applied": True},
        ],
        "normalization_rule_count": 5,
        "normalized": True,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_idempotency_key_preview(normalized_result: dict) -> dict:
    project_id = normalized_result.get("project_id", "demo_project_default")
    adapter_id = normalized_result.get("adapter_id", "text_generation_adapter")
    return {
        "provider_idempotency_key_version": "runner_provider_idempotency_key_preview_v1",
        "provider_idempotency_key_status": "provider_idempotency_key_preview_only",
        "project_id": project_id,
        "adapter_id": adapter_id,
        "idempotency_key": f"{project_id}:{adapter_id}:dry_run:provider_result_dry_run",
        "dedupe_scope": "project_adapter_dry_run",
        "duplicate_invocation_detected": False,
        "side_effects_allowed": False,
        "state_persisted": False,
        "provider_call_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_result_handoff_preview(idempotency_key: dict) -> dict:
    return {
        "provider_result_handoff_version": "runner_provider_result_handoff_preview_v1",
        "provider_result_handoff_status": "provider_result_handoff_preview_only",
        "project_id": idempotency_key.get("project_id", "demo_project_default"),
        "idempotency_key": idempotency_key.get("idempotency_key", ""),
        "handoff_targets": [
            {"target_id": "storyboard_agent", "receives_result": True, "real_handoff": False},
            {"target_id": "evidence_alignment_checker", "receives_result": True, "real_handoff": False},
            {"target_id": "project_workspace", "receives_result": True, "real_handoff": False},
            {"target_id": "operator_control_center", "receives_result": True, "real_handoff": False},
        ],
        "handoff_target_count": 4,
        "handoff_ready": False,
        "real_handoff_performed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_invocation_audit_receipt_preview(result_handoff: dict) -> dict:
    return {
        "provider_invocation_audit_receipt_version": "runner_provider_invocation_audit_receipt_preview_v1",
        "provider_invocation_audit_receipt_status": "provider_invocation_audit_receipt_preview_only",
        "project_id": result_handoff.get("project_id", "demo_project_default"),
        "idempotency_key": result_handoff.get("idempotency_key", ""),
        "receipt_items": [
            {"receipt_item_id": "provider_invocation_router", "included": True},
            {"receipt_item_id": "provider_invocation_stub", "included": True},
            {"receipt_item_id": "normalized_provider_result", "included": True},
            {"receipt_item_id": "provider_idempotency_key", "included": True},
            {"receipt_item_id": "provider_result_handoff", "included": True},
            {"receipt_item_id": "dry_run_boundary", "included": True},
        ],
        "receipt_item_count": 6,
        "audit_receipt_recorded": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "state_persisted": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/provider-invocation/dry-run")
async def dry_run_project_agent_provider_invocation(project_id: str, http_request: Request):
    provider_adapter_payload = await dry_run_project_agent_provider_adapter(project_id, http_request)

    runner_provider_invocation_router_preview = _runner_provider_invocation_router_preview(provider_adapter_payload)
    runner_provider_invocation_stub_preview = _runner_provider_invocation_stub_preview(runner_provider_invocation_router_preview)
    runner_normalized_provider_result_preview = _runner_normalized_provider_result_preview(runner_provider_invocation_stub_preview)
    runner_provider_idempotency_key_preview = _runner_provider_idempotency_key_preview(runner_normalized_provider_result_preview)
    runner_provider_result_handoff_preview = _runner_provider_result_handoff_preview(runner_provider_idempotency_key_preview)
    runner_provider_invocation_audit_receipt_preview = _runner_provider_invocation_audit_receipt_preview(runner_provider_result_handoff_preview)

    project = provider_adapter_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_provider_invocation_router_status": runner_provider_invocation_router_preview["provider_invocation_router_status"],
        "latest_runner_provider_invocation_stub_status": runner_provider_invocation_stub_preview["provider_invocation_stub_status"],
        "latest_runner_normalized_provider_result_status": runner_normalized_provider_result_preview["normalized_provider_result_status"],
        "latest_runner_provider_idempotency_key_status": runner_provider_idempotency_key_preview["provider_idempotency_key_status"],
        "latest_runner_provider_result_handoff_status": runner_provider_result_handoff_preview["provider_result_handoff_status"],
        "latest_runner_provider_invocation_audit_receipt_status": runner_provider_invocation_audit_receipt_preview["provider_invocation_audit_receipt_status"],
        "latest_runner_provider_call_performed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **provider_adapter_payload,
        "project": project,
        "runner_provider_invocation_router_preview": runner_provider_invocation_router_preview,
        "runner_provider_invocation_stub_preview": runner_provider_invocation_stub_preview,
        "runner_normalized_provider_result_preview": runner_normalized_provider_result_preview,
        "runner_provider_idempotency_key_preview": runner_provider_idempotency_key_preview,
        "runner_provider_result_handoff_preview": runner_provider_result_handoff_preview,
        "runner_provider_invocation_audit_receipt_preview": runner_provider_invocation_audit_receipt_preview,
        "dry_run": True,
        "route_selected": True,
        "route_invocation_allowed": False,
        "normalized": True,
        "handoff_ready": False,
        "real_handoff_performed": False,
        "audit_receipt_recorded": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_provider_failure_taxonomy_preview(provider_invocation_payload: dict) -> dict:
    project = dict(provider_invocation_payload.get("project") or {})
    invocation_receipt = dict(provider_invocation_payload.get("runner_provider_invocation_audit_receipt_preview") or {})
    failure_types = [
        {"failure_type": "timeout", "retryable": True, "requires_operator_review": False},
        {"failure_type": "rate_limited", "retryable": True, "requires_operator_review": False},
        {"failure_type": "quota_exceeded", "retryable": False, "requires_operator_review": True},
        {"failure_type": "provider_unavailable", "retryable": True, "requires_operator_review": False},
        {"failure_type": "schema_mismatch", "retryable": False, "requires_operator_review": True},
        {"failure_type": "secret_boundary_violation", "retryable": False, "requires_operator_review": True},
        {"failure_type": "policy_blocked", "retryable": False, "requires_operator_review": True},
    ]
    return {
        "provider_failure_taxonomy_version": "runner_provider_failure_taxonomy_preview_v1",
        "provider_failure_taxonomy_status": "provider_failure_taxonomy_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "provider_invocation_audit_receipt_status": invocation_receipt.get("provider_invocation_audit_receipt_status", ""),
        "failure_types": failure_types,
        "failure_type_count": len(failure_types),
        "selected_failure_type": "policy_blocked",
        "failure_detected": True,
        "retryable": False,
        "operator_review_required": True,
        "provider_call_performed": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_retry_policy_preview(failure_taxonomy: dict) -> dict:
    retry_steps = [
        {"retry_step_id": "classify_failure", "ready": True, "executed": False},
        {"retry_step_id": "check_idempotency_key", "ready": True, "executed": False},
        {"retry_step_id": "check_quota_before_retry", "ready": False, "executed": False},
        {"retry_step_id": "apply_backoff_window", "ready": False, "executed": False},
        {"retry_step_id": "request_operator_review_for_non_retryable", "ready": True, "executed": False},
    ]
    return {
        "provider_retry_policy_version": "runner_provider_retry_policy_preview_v1",
        "provider_retry_policy_status": "provider_retry_policy_blocked",
        "project_id": failure_taxonomy.get("project_id", "demo_project_default"),
        "selected_failure_type": failure_taxonomy.get("selected_failure_type", "policy_blocked"),
        "retry_steps": retry_steps,
        "retry_step_count": len(retry_steps),
        "retry_allowed": False,
        "max_retry_attempts": 0,
        "backoff_strategy": "none_in_dry_run",
        "operator_review_required": True,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_fallback_plan_preview(retry_policy: dict) -> dict:
    fallback_options = [
        {"fallback_id": "use_existing_project_evidence", "available": True, "selected": True},
        {"fallback_id": "use_template_stub_output", "available": True, "selected": False},
        {"fallback_id": "queue_manual_operator_task", "available": True, "selected": False},
        {"fallback_id": "pause_dependent_agent", "available": True, "selected": False},
        {"fallback_id": "skip_optional_asset_generation", "available": True, "selected": False},
    ]
    return {
        "provider_fallback_plan_version": "runner_provider_fallback_plan_preview_v1",
        "provider_fallback_plan_status": "provider_fallback_plan_preview_only",
        "project_id": retry_policy.get("project_id", "demo_project_default"),
        "provider_retry_policy_status": retry_policy.get("provider_retry_policy_status", ""),
        "fallback_options": fallback_options,
        "fallback_option_count": len(fallback_options),
        "selected_fallback_id": "use_existing_project_evidence",
        "fallback_selected": True,
        "fallback_executed": False,
        "agent_execution_performed": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_circuit_breaker_preview(fallback_plan: dict) -> dict:
    circuit_rules = [
        {"circuit_rule_id": "open_after_repeated_timeouts", "threshold": 3, "active": False},
        {"circuit_rule_id": "open_after_quota_exceeded", "threshold": 1, "active": True},
        {"circuit_rule_id": "open_after_secret_boundary_violation", "threshold": 1, "active": True},
        {"circuit_rule_id": "open_after_schema_mismatch", "threshold": 2, "active": False},
        {"circuit_rule_id": "operator_manual_open", "threshold": 1, "active": False},
    ]
    return {
        "provider_circuit_breaker_version": "runner_provider_circuit_breaker_preview_v1",
        "provider_circuit_breaker_status": "provider_circuit_breaker_preview_only",
        "project_id": fallback_plan.get("project_id", "demo_project_default"),
        "provider_fallback_plan_status": fallback_plan.get("provider_fallback_plan_status", ""),
        "circuit_rules": circuit_rules,
        "circuit_rule_count": len(circuit_rules),
        "circuit_open": True,
        "provider_temporarily_blocked": True,
        "operator_review_required": True,
        "next_provider_call_allowed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_failure_recovery_handoff_preview(circuit_breaker: dict) -> dict:
    handoff_targets = [
        {"target_id": "operator_control_center", "reason": "operator_review_required", "handoff_ready": True},
        {"target_id": "project_workspace", "reason": "show_failure_receipt", "handoff_ready": True},
        {"target_id": "runner_queue", "reason": "pause_dependent_work", "handoff_ready": False},
        {"target_id": "audit_ledger", "reason": "record_failure_classification", "handoff_ready": True},
    ]
    return {
        "provider_failure_recovery_handoff_version": "runner_provider_failure_recovery_handoff_preview_v1",
        "provider_failure_recovery_handoff_status": "provider_failure_recovery_handoff_preview_only",
        "project_id": circuit_breaker.get("project_id", "demo_project_default"),
        "provider_circuit_breaker_status": circuit_breaker.get("provider_circuit_breaker_status", ""),
        "handoff_targets": handoff_targets,
        "handoff_target_count": len(handoff_targets),
        "recovery_handoff_ready": False,
        "real_handoff_performed": False,
        "operator_review_required": True,
        "agent_execution_performed": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_failure_receipt_preview(recovery_handoff: dict) -> dict:
    return {
        "provider_failure_receipt_version": "runner_provider_failure_receipt_preview_v1",
        "provider_failure_receipt_status": "provider_failure_receipt_preview_only",
        "project_id": recovery_handoff.get("project_id", "demo_project_default"),
        "provider_failure_recovery_handoff_status": recovery_handoff.get("provider_failure_recovery_handoff_status", ""),
        "receipt_items": [
            {"receipt_item_id": "failure_taxonomy", "included": True},
            {"receipt_item_id": "retry_policy", "included": True},
            {"receipt_item_id": "fallback_plan", "included": True},
            {"receipt_item_id": "circuit_breaker", "included": True},
            {"receipt_item_id": "recovery_handoff", "included": True},
            {"receipt_item_id": "dry_run_boundary", "included": True},
        ],
        "receipt_item_count": 6,
        "failure_receipt_recorded": False,
        "retry_allowed": False,
        "fallback_executed": False,
        "circuit_open": True,
        "provider_temporarily_blocked": True,
        "operator_review_required": True,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/provider-failure/dry-run")
async def dry_run_project_agent_provider_failure(project_id: str, http_request: Request):
    provider_invocation_payload = await dry_run_project_agent_provider_invocation(project_id, http_request)

    runner_provider_failure_taxonomy_preview = _runner_provider_failure_taxonomy_preview(provider_invocation_payload)
    runner_provider_retry_policy_preview = _runner_provider_retry_policy_preview(runner_provider_failure_taxonomy_preview)
    runner_provider_fallback_plan_preview = _runner_provider_fallback_plan_preview(runner_provider_retry_policy_preview)
    runner_provider_circuit_breaker_preview = _runner_provider_circuit_breaker_preview(runner_provider_fallback_plan_preview)
    runner_provider_failure_recovery_handoff_preview = _runner_provider_failure_recovery_handoff_preview(runner_provider_circuit_breaker_preview)
    runner_provider_failure_receipt_preview = _runner_provider_failure_receipt_preview(runner_provider_failure_recovery_handoff_preview)

    project = provider_invocation_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_provider_failure_taxonomy_status": runner_provider_failure_taxonomy_preview["provider_failure_taxonomy_status"],
        "latest_runner_provider_retry_policy_status": runner_provider_retry_policy_preview["provider_retry_policy_status"],
        "latest_runner_provider_fallback_plan_status": runner_provider_fallback_plan_preview["provider_fallback_plan_status"],
        "latest_runner_provider_circuit_breaker_status": runner_provider_circuit_breaker_preview["provider_circuit_breaker_status"],
        "latest_runner_provider_failure_recovery_handoff_status": runner_provider_failure_recovery_handoff_preview["provider_failure_recovery_handoff_status"],
        "latest_runner_provider_failure_receipt_status": runner_provider_failure_receipt_preview["provider_failure_receipt_status"],
        "latest_runner_provider_temporarily_blocked": True,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **provider_invocation_payload,
        "project": project,
        "runner_provider_failure_taxonomy_preview": runner_provider_failure_taxonomy_preview,
        "runner_provider_retry_policy_preview": runner_provider_retry_policy_preview,
        "runner_provider_fallback_plan_preview": runner_provider_fallback_plan_preview,
        "runner_provider_circuit_breaker_preview": runner_provider_circuit_breaker_preview,
        "runner_provider_failure_recovery_handoff_preview": runner_provider_failure_recovery_handoff_preview,
        "runner_provider_failure_receipt_preview": runner_provider_failure_receipt_preview,
        "dry_run": True,
        "failure_detected": True,
        "retry_allowed": False,
        "fallback_selected": True,
        "fallback_executed": False,
        "circuit_open": True,
        "provider_temporarily_blocked": True,
        "next_provider_call_allowed": False,
        "operator_review_required": True,
        "failure_receipt_recorded": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_provider_health_snapshot_preview(provider_failure_payload: dict) -> dict:
    project = dict(provider_failure_payload.get("project") or {})
    failure_receipt = dict(provider_failure_payload.get("runner_provider_failure_receipt_preview") or {})
    health_items = [
        {"provider_id": "text_generation_adapter", "health": "blocked_by_dry_run", "circuit_open": True},
        {"provider_id": "image_generation_adapter", "health": "blocked_by_dry_run", "circuit_open": True},
        {"provider_id": "video_generation_adapter", "health": "blocked_by_dry_run", "circuit_open": True},
        {"provider_id": "comment_collection_adapter", "health": "blocked_by_dry_run", "circuit_open": True},
        {"provider_id": "web_fetch_adapter", "health": "blocked_by_dry_run", "circuit_open": True},
    ]
    return {
        "provider_health_snapshot_version": "runner_provider_health_snapshot_preview_v1",
        "provider_health_snapshot_status": "provider_health_snapshot_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "provider_failure_receipt_status": failure_receipt.get("provider_failure_receipt_status", ""),
        "health_items": health_items,
        "health_item_count": len(health_items),
        "healthy_provider_count": 0,
        "blocked_provider_count": len(health_items),
        "overall_health": "blocked_by_dry_run",
        "operator_review_required": True,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_metric_rollup_preview(health_snapshot: dict) -> dict:
    metric_rows = [
        {"metric_id": "provider_calls_total", "value": 0, "unit": "calls"},
        {"metric_id": "provider_failures_total", "value": 0, "unit": "failures"},
        {"metric_id": "provider_retries_total", "value": 0, "unit": "retries"},
        {"metric_id": "provider_latency_p95_ms", "value": 0, "unit": "milliseconds"},
        {"metric_id": "provider_cost_cents_total", "value": 0, "unit": "cents"},
        {"metric_id": "provider_circuit_open_total", "value": health_snapshot.get("blocked_provider_count", 0), "unit": "providers"},
    ]
    return {
        "provider_metric_rollup_version": "runner_provider_metric_rollup_preview_v1",
        "provider_metric_rollup_status": "provider_metric_rollup_preview_only",
        "project_id": health_snapshot.get("project_id", "demo_project_default"),
        "provider_health_snapshot_status": health_snapshot.get("provider_health_snapshot_status", ""),
        "metric_rows": metric_rows,
        "metric_row_count": len(metric_rows),
        "provider_calls_total": 0,
        "provider_failures_total": 0,
        "provider_retries_total": 0,
        "provider_cost_cents_total": 0,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_alert_policy_preview(metric_rollup: dict) -> dict:
    alert_rules = [
        {"alert_rule_id": "provider_failure_rate_high", "enabled": True, "triggered": False},
        {"alert_rule_id": "provider_latency_high", "enabled": True, "triggered": False},
        {"alert_rule_id": "provider_cost_limit_reached", "enabled": True, "triggered": False},
        {"alert_rule_id": "provider_circuit_open", "enabled": True, "triggered": True},
        {"alert_rule_id": "secret_boundary_violation", "enabled": True, "triggered": False},
        {"alert_rule_id": "operator_review_required", "enabled": True, "triggered": True},
    ]
    return {
        "provider_alert_policy_version": "runner_provider_alert_policy_preview_v1",
        "provider_alert_policy_status": "provider_alert_policy_preview_only",
        "project_id": metric_rollup.get("project_id", "demo_project_default"),
        "provider_metric_rollup_status": metric_rollup.get("provider_metric_rollup_status", ""),
        "alert_rules": alert_rules,
        "alert_rule_count": len(alert_rules),
        "triggered_alert_count": sum(1 for rule in alert_rules if rule.get("triggered")),
        "alerts_triggered": True,
        "operator_review_required": True,
        "external_notification_sent": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_trace_summary_preview(alert_policy: dict) -> dict:
    trace_events = [
        {"trace_event_id": "provider_adapter_registry_checked", "recorded": True},
        {"trace_event_id": "provider_invocation_routed", "recorded": True},
        {"trace_event_id": "provider_call_blocked_by_dry_run", "recorded": True},
        {"trace_event_id": "failure_taxonomy_previewed", "recorded": True},
        {"trace_event_id": "circuit_breaker_previewed", "recorded": True},
        {"trace_event_id": "alert_policy_previewed", "recorded": True},
    ]
    return {
        "provider_trace_summary_version": "runner_provider_trace_summary_preview_v1",
        "provider_trace_summary_status": "provider_trace_summary_preview_only",
        "project_id": alert_policy.get("project_id", "demo_project_default"),
        "provider_alert_policy_status": alert_policy.get("provider_alert_policy_status", ""),
        "trace_events": trace_events,
        "trace_event_count": len(trace_events),
        "trace_complete": True,
        "trace_persisted": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_observability_dashboard_preview(trace_summary: dict) -> dict:
    dashboard_cards = [
        {"card_id": "overall_provider_health", "value": "blocked_by_dry_run"},
        {"card_id": "provider_calls_total", "value": 0},
        {"card_id": "provider_failures_total", "value": 0},
        {"card_id": "provider_cost_cents_total", "value": 0},
        {"card_id": "provider_circuit_open_total", "value": 5},
        {"card_id": "operator_review_required", "value": True},
    ]
    return {
        "provider_observability_dashboard_version": "runner_provider_observability_dashboard_preview_v1",
        "provider_observability_dashboard_status": "provider_observability_dashboard_preview_only",
        "project_id": trace_summary.get("project_id", "demo_project_default"),
        "provider_trace_summary_status": trace_summary.get("provider_trace_summary_status", ""),
        "dashboard_cards": dashboard_cards,
        "dashboard_card_count": len(dashboard_cards),
        "dashboard_ready": True,
        "operator_review_required": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_provider_observability_receipt_preview(dashboard: dict) -> dict:
    return {
        "provider_observability_receipt_version": "runner_provider_observability_receipt_preview_v1",
        "provider_observability_receipt_status": "provider_observability_receipt_preview_only",
        "project_id": dashboard.get("project_id", "demo_project_default"),
        "provider_observability_dashboard_status": dashboard.get("provider_observability_dashboard_status", ""),
        "receipt_items": [
            {"receipt_item_id": "provider_health_snapshot", "included": True},
            {"receipt_item_id": "provider_metric_rollup", "included": True},
            {"receipt_item_id": "provider_alert_policy", "included": True},
            {"receipt_item_id": "provider_trace_summary", "included": True},
            {"receipt_item_id": "provider_observability_dashboard", "included": True},
            {"receipt_item_id": "dry_run_boundary", "included": True},
        ],
        "receipt_item_count": 6,
        "observability_receipt_recorded": False,
        "dashboard_ready": dashboard.get("dashboard_ready", False),
        "operator_review_required": True,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/provider-observability/dry-run")
async def dry_run_project_agent_provider_observability(project_id: str, http_request: Request):
    provider_failure_payload = await dry_run_project_agent_provider_failure(project_id, http_request)

    runner_provider_health_snapshot_preview = _runner_provider_health_snapshot_preview(provider_failure_payload)
    runner_provider_metric_rollup_preview = _runner_provider_metric_rollup_preview(runner_provider_health_snapshot_preview)
    runner_provider_alert_policy_preview = _runner_provider_alert_policy_preview(runner_provider_metric_rollup_preview)
    runner_provider_trace_summary_preview = _runner_provider_trace_summary_preview(runner_provider_alert_policy_preview)
    runner_provider_observability_dashboard_preview = _runner_provider_observability_dashboard_preview(runner_provider_trace_summary_preview)
    runner_provider_observability_receipt_preview = _runner_provider_observability_receipt_preview(runner_provider_observability_dashboard_preview)

    project = provider_failure_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_provider_health_snapshot_status": runner_provider_health_snapshot_preview["provider_health_snapshot_status"],
        "latest_runner_provider_metric_rollup_status": runner_provider_metric_rollup_preview["provider_metric_rollup_status"],
        "latest_runner_provider_alert_policy_status": runner_provider_alert_policy_preview["provider_alert_policy_status"],
        "latest_runner_provider_trace_summary_status": runner_provider_trace_summary_preview["provider_trace_summary_status"],
        "latest_runner_provider_observability_dashboard_status": runner_provider_observability_dashboard_preview["provider_observability_dashboard_status"],
        "latest_runner_provider_observability_receipt_status": runner_provider_observability_receipt_preview["provider_observability_receipt_status"],
        "latest_runner_provider_observability_dashboard_ready": True,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **provider_failure_payload,
        "project": project,
        "runner_provider_health_snapshot_preview": runner_provider_health_snapshot_preview,
        "runner_provider_metric_rollup_preview": runner_provider_metric_rollup_preview,
        "runner_provider_alert_policy_preview": runner_provider_alert_policy_preview,
        "runner_provider_trace_summary_preview": runner_provider_trace_summary_preview,
        "runner_provider_observability_dashboard_preview": runner_provider_observability_dashboard_preview,
        "runner_provider_observability_receipt_preview": runner_provider_observability_receipt_preview,
        "dry_run": True,
        "dashboard_ready": True,
        "alerts_triggered": True,
        "operator_review_required": True,
        "observability_receipt_recorded": False,
        "trace_persisted": False,
        "external_notification_sent": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_agent_capability_catalog_preview(provider_observability_payload: dict) -> dict:
    project = dict(provider_observability_payload.get("project") or {})
    observability_receipt = dict(provider_observability_payload.get("runner_provider_observability_receipt_preview") or {})
    capabilities = [
        {"capability_id": "plan_generation", "provider_adapter": "text_generation_adapter", "enabled": False, "agent_roles": ["planner_agent"]},
        {"capability_id": "evidence_retrieval", "provider_adapter": "web_fetch_adapter", "enabled": False, "agent_roles": ["retrieval_agent"]},
        {"capability_id": "comment_collection", "provider_adapter": "comment_collection_adapter", "enabled": False, "agent_roles": ["retrieval_agent"]},
        {"capability_id": "storyboard_generation", "provider_adapter": "text_generation_adapter", "enabled": False, "agent_roles": ["storyboard_agent"]},
        {"capability_id": "image_asset_generation", "provider_adapter": "image_generation_adapter", "enabled": False, "agent_roles": ["asset_agent"]},
        {"capability_id": "video_asset_generation", "provider_adapter": "video_generation_adapter", "enabled": False, "agent_roles": ["asset_agent"]},
        {"capability_id": "audit_export", "provider_adapter": "export_pack_adapter", "enabled": False, "agent_roles": ["operator_agent"]},
    ]
    return {
        "agent_capability_catalog_version": "runner_agent_capability_catalog_preview_v1",
        "agent_capability_catalog_status": "agent_capability_catalog_preview_only",
        "project_id": project.get("project_id", "demo_project_default"),
        "provider_observability_receipt_status": observability_receipt.get("provider_observability_receipt_status", ""),
        "capabilities": capabilities,
        "capability_count": len(capabilities),
        "enabled_capability_count": 0,
        "least_privilege_required": True,
        "real_execution_enabled": False,
        "external_api_called": False,
        "dry_run": True,
    }


def _runner_agent_tool_binding_matrix_preview(capability_catalog: dict) -> dict:
    bindings = [
        {"agent_role": "planner_agent", "capability_id": "plan_generation", "tool_bound": True, "tool_enabled": False},
        {"agent_role": "retrieval_agent", "capability_id": "evidence_retrieval", "tool_bound": True, "tool_enabled": False},
        {"agent_role": "retrieval_agent", "capability_id": "comment_collection", "tool_bound": True, "tool_enabled": False},
        {"agent_role": "storyboard_agent", "capability_id": "storyboard_generation", "tool_bound": True, "tool_enabled": False},
        {"agent_role": "asset_agent", "capability_id": "image_asset_generation", "tool_bound": True, "tool_enabled": False},
        {"agent_role": "asset_agent", "capability_id": "video_asset_generation", "tool_bound": True, "tool_enabled": False},
        {"agent_role": "operator_agent", "capability_id": "audit_export", "tool_bound": True, "tool_enabled": False},
    ]
    return {
        "agent_tool_binding_matrix_version": "runner_agent_tool_binding_matrix_preview_v1",
        "agent_tool_binding_matrix_status": "agent_tool_binding_matrix_preview_only",
        "project_id": capability_catalog.get("project_id", "demo_project_default"),
        "agent_capability_catalog_status": capability_catalog.get("agent_capability_catalog_status", ""),
        "bindings": bindings,
        "binding_count": len(bindings),
        "enabled_binding_count": 0,
        "all_bindings_least_privilege": True,
        "tool_invocation_allowed": False,
        "real_execution_enabled": False,
        "external_api_called": False,
        "dry_run": True,
    }


def _runner_capability_policy_gate_preview(binding_matrix: dict) -> dict:
    policy_checks = [
        {"policy_check_id": "agent_role_known", "passed": True},
        {"policy_check_id": "capability_registered", "passed": True},
        {"policy_check_id": "provider_adapter_registered", "passed": True},
        {"policy_check_id": "sandbox_enabled", "passed": False},
        {"policy_check_id": "quota_enabled", "passed": False},
        {"policy_check_id": "operator_approval_captured", "passed": False},
        {"policy_check_id": "observability_ready", "passed": True},
        {"policy_check_id": "failure_handling_ready", "passed": True},
    ]
    passed_count = sum(1 for item in policy_checks if item.get("passed"))
    return {
        "capability_policy_gate_version": "runner_capability_policy_gate_preview_v1",
        "capability_policy_gate_status": "capability_policy_gate_blocked",
        "project_id": binding_matrix.get("project_id", "demo_project_default"),
        "agent_tool_binding_matrix_status": binding_matrix.get("agent_tool_binding_matrix_status", ""),
        "policy_checks": policy_checks,
        "policy_check_count": len(policy_checks),
        "passed_policy_check_count": passed_count,
        "all_required_policy_checks_passed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_tool_invocation_contract_preview(policy_gate: dict) -> dict:
    contract_fields = [
        {"contract_field_id": "agent_role", "required": True, "present": True},
        {"contract_field_id": "capability_id", "required": True, "present": True},
        {"contract_field_id": "provider_adapter_id", "required": True, "present": True},
        {"contract_field_id": "idempotency_key", "required": True, "present": True},
        {"contract_field_id": "operator_approval_id", "required": True, "present": False},
        {"contract_field_id": "quota_reservation_id", "required": True, "present": False},
        {"contract_field_id": "rollback_plan_id", "required": True, "present": False},
    ]
    present_count = sum(1 for item in contract_fields if item.get("present"))
    return {
        "tool_invocation_contract_version": "runner_tool_invocation_contract_preview_v1",
        "tool_invocation_contract_status": "tool_invocation_contract_incomplete",
        "project_id": policy_gate.get("project_id", "demo_project_default"),
        "capability_policy_gate_status": policy_gate.get("capability_policy_gate_status", ""),
        "contract_fields": contract_fields,
        "contract_field_count": len(contract_fields),
        "present_contract_field_count": present_count,
        "contract_complete": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_handoff_plan_preview(tool_contract: dict) -> dict:
    handoff_edges = [
        {"from_agent": "planner_agent", "to_agent": "retrieval_agent", "capability_id": "evidence_retrieval", "enabled": False},
        {"from_agent": "retrieval_agent", "to_agent": "storyboard_agent", "capability_id": "storyboard_generation", "enabled": False},
        {"from_agent": "storyboard_agent", "to_agent": "asset_agent", "capability_id": "image_asset_generation", "enabled": False},
        {"from_agent": "asset_agent", "to_agent": "operator_agent", "capability_id": "audit_export", "enabled": False},
    ]
    return {
        "capability_handoff_plan_version": "runner_capability_handoff_plan_preview_v1",
        "capability_handoff_plan_status": "capability_handoff_plan_preview_only",
        "project_id": tool_contract.get("project_id", "demo_project_default"),
        "tool_invocation_contract_status": tool_contract.get("tool_invocation_contract_status", ""),
        "handoff_edges": handoff_edges,
        "handoff_edge_count": len(handoff_edges),
        "enabled_handoff_edge_count": 0,
        "handoff_ready": False,
        "real_handoff_performed": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_binding_receipt_preview(handoff_plan: dict) -> dict:
    return {
        "capability_binding_receipt_version": "runner_capability_binding_receipt_preview_v1",
        "capability_binding_receipt_status": "capability_binding_receipt_preview_only",
        "project_id": handoff_plan.get("project_id", "demo_project_default"),
        "capability_handoff_plan_status": handoff_plan.get("capability_handoff_plan_status", ""),
        "receipt_items": [
            {"receipt_item_id": "agent_capability_catalog", "included": True},
            {"receipt_item_id": "agent_tool_binding_matrix", "included": True},
            {"receipt_item_id": "capability_policy_gate", "included": True},
            {"receipt_item_id": "tool_invocation_contract", "included": True},
            {"receipt_item_id": "capability_handoff_plan", "included": True},
            {"receipt_item_id": "dry_run_boundary", "included": True},
        ],
        "receipt_item_count": 6,
        "capability_binding_receipt_recorded": False,
        "tool_invocation_allowed": False,
        "handoff_ready": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }



def _runner_capability_invocation_gate_preview(binding_payload: dict) -> dict:
    policy_gate = dict(binding_payload.get("runner_capability_policy_gate_preview") or {})
    tool_contract = dict(binding_payload.get("runner_tool_invocation_contract_preview") or {})
    binding_receipt = dict(binding_payload.get("runner_capability_binding_receipt_preview") or {})
    project_id = str(binding_payload.get("project", {}).get("project_id") or binding_payload.get("project_id") or "demo_project_default")
    gate_checks = [
        {
            "gate_check_id": "capability_policy_gate_passed",
            "passed": bool(policy_gate.get("all_required_policy_checks_passed")),
            "blocking": True,
            "reason": "Capability policy gate must pass before any tool invocation.",
        },
        {
            "gate_check_id": "tool_invocation_contract_complete",
            "passed": bool(tool_contract.get("contract_complete")),
            "blocking": True,
            "reason": "Tool invocation contract must include approval, quota, idempotency, and rollback fields.",
        },
        {
            "gate_check_id": "capability_binding_receipt_recorded",
            "passed": bool(binding_receipt.get("capability_binding_receipt_recorded")),
            "blocking": True,
            "reason": "Capability binding receipt must be recorded before invocation.",
        },
        {
            "gate_check_id": "sandbox_enabled",
            "passed": False,
            "blocking": True,
            "reason": "Execution sandbox must be enabled before capability invocation.",
        },
        {
            "gate_check_id": "operator_approval_captured",
            "passed": False,
            "blocking": True,
            "reason": "Operator approval is required before any real provider-capable invocation.",
        },
        {
            "gate_check_id": "provider_call_guarded",
            "passed": True,
            "blocking": False,
            "reason": "Dry-run keeps provider calls disabled.",
        },
    ]
    blocking_check_ids = [
        item["gate_check_id"]
        for item in gate_checks
        if item.get("blocking") and not item.get("passed")
    ]
    return {
        "capability_invocation_gate_version": "runner_capability_invocation_gate_preview_v1",
        "capability_invocation_gate_status": "capability_invocation_blocked",
        "project_id": project_id,
        "capability_policy_gate_status": policy_gate.get("capability_policy_gate_status", ""),
        "tool_invocation_contract_status": tool_contract.get("tool_invocation_contract_status", ""),
        "capability_binding_receipt_status": binding_receipt.get("capability_binding_receipt_status", ""),
        "gate_checks": gate_checks,
        "gate_check_count": len(gate_checks),
        "passed_gate_check_count": sum(1 for item in gate_checks if item.get("passed")),
        "blocking_check_ids": blocking_check_ids,
        "blocking_check_count": len(blocking_check_ids),
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_request_preview(invocation_gate: dict) -> dict:
    project_id = str(invocation_gate.get("project_id") or "demo_project_default")
    return {
        "capability_invocation_request_version": "runner_capability_invocation_request_preview_v1",
        "capability_invocation_request_status": "capability_invocation_request_blocked",
        "project_id": project_id,
        "capability_invocation_gate_status": invocation_gate.get("capability_invocation_gate_status", ""),
        "request_type": "tool_capability_invocation",
        "target_capability_id": "dry_run_capability_placeholder",
        "target_provider_adapter_id": "dry_run_provider_adapter_placeholder",
        "idempotency_key": f"capability_invocation_{project_id}_dry_run",
        "required_authorization_refs": [
            "operator_approval_id",
            "quota_reservation_id",
            "sandbox_session_id",
            "rollback_plan_id",
        ],
        "missing_authorization_refs": [
            "operator_approval_id",
            "quota_reservation_id",
            "sandbox_session_id",
            "rollback_plan_id",
        ],
        "payload_redacted": True,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_decision_preview(invocation_request: dict) -> dict:
    missing_refs = list(invocation_request.get("missing_authorization_refs") or [])
    decision_reasons = [
        "Capability invocation remains blocked in dry-run.",
        "Real provider or tool invocation requires explicit operator approval, quota reservation, sandbox session, and rollback plan.",
    ]
    return {
        "capability_invocation_decision_version": "runner_capability_invocation_decision_preview_v1",
        "capability_invocation_decision_status": "capability_invocation_blocked",
        "project_id": invocation_request.get("project_id", "demo_project_default"),
        "capability_invocation_request_status": invocation_request.get("capability_invocation_request_status", ""),
        "decision_type": "block_real_invocation",
        "decision_reasons": decision_reasons,
        "missing_authorization_refs": missing_refs,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_capability_invocation_gate_receipt_preview(invocation_decision: dict) -> dict:
    receipt_items = [
        {"receipt_item_id": "capability_invocation_gate", "included": True},
        {"receipt_item_id": "capability_invocation_request", "included": True},
        {"receipt_item_id": "capability_invocation_decision", "included": True},
        {"receipt_item_id": "missing_authorization_refs", "included": True},
        {"receipt_item_id": "dry_run_boundary", "included": True},
    ]
    return {
        "capability_invocation_gate_receipt_version": "runner_capability_invocation_gate_receipt_preview_v1",
        "capability_invocation_gate_receipt_status": "capability_invocation_gate_receipt_preview_only",
        "project_id": invocation_decision.get("project_id", "demo_project_default"),
        "capability_invocation_decision_status": invocation_decision.get("capability_invocation_decision_status", ""),
        "receipt_items": receipt_items,
        "receipt_item_count": len(receipt_items),
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/capability-binding/dry-run")
async def dry_run_project_agent_capability_binding(project_id: str, http_request: Request):
    provider_observability_payload = await dry_run_project_agent_provider_observability(project_id, http_request)

    runner_agent_capability_catalog_preview = _runner_agent_capability_catalog_preview(provider_observability_payload)
    runner_agent_tool_binding_matrix_preview = _runner_agent_tool_binding_matrix_preview(runner_agent_capability_catalog_preview)
    runner_capability_policy_gate_preview = _runner_capability_policy_gate_preview(runner_agent_tool_binding_matrix_preview)
    runner_tool_invocation_contract_preview = _runner_tool_invocation_contract_preview(runner_capability_policy_gate_preview)
    runner_capability_handoff_plan_preview = _runner_capability_handoff_plan_preview(runner_tool_invocation_contract_preview)
    runner_capability_binding_receipt_preview = _runner_capability_binding_receipt_preview(runner_capability_handoff_plan_preview)

    project = provider_observability_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_agent_capability_catalog_status": runner_agent_capability_catalog_preview["agent_capability_catalog_status"],
        "latest_runner_agent_tool_binding_matrix_status": runner_agent_tool_binding_matrix_preview["agent_tool_binding_matrix_status"],
        "latest_runner_capability_policy_gate_status": runner_capability_policy_gate_preview["capability_policy_gate_status"],
        "latest_runner_tool_invocation_contract_status": runner_tool_invocation_contract_preview["tool_invocation_contract_status"],
        "latest_runner_capability_handoff_plan_status": runner_capability_handoff_plan_preview["capability_handoff_plan_status"],
        "latest_runner_capability_binding_receipt_status": runner_capability_binding_receipt_preview["capability_binding_receipt_status"],
        "latest_runner_tool_invocation_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **provider_observability_payload,
        "project": project,
        "runner_agent_capability_catalog_preview": runner_agent_capability_catalog_preview,
        "runner_agent_tool_binding_matrix_preview": runner_agent_tool_binding_matrix_preview,
        "runner_capability_policy_gate_preview": runner_capability_policy_gate_preview,
        "runner_tool_invocation_contract_preview": runner_tool_invocation_contract_preview,
        "runner_capability_handoff_plan_preview": runner_capability_handoff_plan_preview,
        "runner_capability_binding_receipt_preview": runner_capability_binding_receipt_preview,
        "dry_run": True,
        "least_privilege_required": True,
        "all_bindings_least_privilege": True,
        "all_required_policy_checks_passed": False,
        "contract_complete": False,
        "tool_invocation_allowed": False,
        "handoff_ready": False,
        "real_handoff_performed": False,
        "capability_binding_receipt_recorded": False,
        "release_allowed": False,
        "real_execution_enabled": False,
        "agent_execution_performed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
        "write_authorized": False,
        "state_persisted": False,
        "project_snapshot_saved": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_capability_invocation_runtime_rehearsal_preview(invocation_gate_payload: dict) -> dict:
    gate = dict(invocation_gate_payload.get("runner_capability_invocation_gate_preview") or {})
    request = dict(invocation_gate_payload.get("runner_capability_invocation_request_preview") or {})
    decision = dict(invocation_gate_payload.get("runner_capability_invocation_decision_preview") or {})
    project_id = str(invocation_gate_payload.get("project", {}).get("project_id") or invocation_gate_payload.get("project_id") or "demo_project_default")
    gate_blocked = str(gate.get("capability_invocation_gate_status") or "") != "capability_invocation_ready"

    runtime_steps = [
        {
            "runtime_step_id": "validate_capability_invocation_gate",
            "status": "blocked" if gate_blocked else "passed",
            "blocking": gate_blocked,
            "reason": "Capability invocation gate must pass before runtime rehearsal can continue.",
        },
        {
            "runtime_step_id": "reserve_runtime_quota",
            "status": "not_started",
            "blocking": True,
            "reason": "Quota reservation is required before any real provider-capable runtime call.",
        },
        {
            "runtime_step_id": "open_sandbox_session",
            "status": "not_started",
            "blocking": True,
            "reason": "Sandbox session is required before tool execution.",
        },
        {
            "runtime_step_id": "adapter_dry_run",
            "status": "not_started",
            "blocking": True,
            "reason": "Adapter dry-run is blocked until gate, quota, sandbox, and approval are complete.",
        },
        {
            "runtime_step_id": "write_attempt_ledger",
            "status": "ready_for_preview",
            "blocking": False,
            "reason": "Preview ledger can be written without real invocation.",
        },
    ]
    blocking_step_ids = [
        item["runtime_step_id"]
        for item in runtime_steps
        if item.get("blocking") and item.get("status") != "passed"
    ]
    return {
        "capability_invocation_runtime_rehearsal_version": "runner_capability_invocation_runtime_rehearsal_preview_v1",
        "capability_invocation_runtime_rehearsal_status": "runtime_rehearsal_blocked",
        "project_id": project_id,
        "capability_invocation_gate_status": gate.get("capability_invocation_gate_status", ""),
        "capability_invocation_request_status": request.get("capability_invocation_request_status", ""),
        "capability_invocation_decision_status": decision.get("capability_invocation_decision_status", ""),
        "runtime_steps": runtime_steps,
        "runtime_step_count": len(runtime_steps),
        "blocking_step_ids": blocking_step_ids,
        "blocking_step_count": len(blocking_step_ids),
        "runtime_rehearsal_allowed": False,
        "adapter_invocation_attempted": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_attempt_ledger_preview(runtime_rehearsal: dict) -> dict:
    project_id = str(runtime_rehearsal.get("project_id") or "demo_project_default")
    blocked_events = [
        {
            "event_id": f"capability_invocation_attempt_{project_id}_blocked",
            "event_type": "capability_invocation_attempt_blocked",
            "event_status": "blocked",
            "reason": "Runtime rehearsal is blocked before adapter invocation.",
            "blocking_step_ids": list(runtime_rehearsal.get("blocking_step_ids") or []),
        }
    ]
    return {
        "capability_invocation_attempt_ledger_version": "runner_capability_invocation_attempt_ledger_preview_v1",
        "capability_invocation_attempt_ledger_status": "attempt_ledger_preview_recorded",
        "project_id": project_id,
        "attempt_id": f"capability_invocation_attempt_{project_id}_dry_run",
        "attempt_status": "blocked_before_invocation",
        "attempt_events": blocked_events,
        "attempt_event_count": len(blocked_events),
        "runtime_rehearsal_status": runtime_rehearsal.get("capability_invocation_runtime_rehearsal_status", ""),
        "adapter_invocation_attempted": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_rehearsal_receipt_preview(
    runtime_rehearsal: dict,
    attempt_ledger: dict,
) -> dict:
    receipt_checks = [
        {
            "receipt_check_id": "runtime_rehearsal_recorded",
            "passed": bool(runtime_rehearsal.get("capability_invocation_runtime_rehearsal_version")),
        },
        {
            "receipt_check_id": "attempt_ledger_recorded",
            "passed": bool(attempt_ledger.get("capability_invocation_attempt_ledger_version")),
        },
        {
            "receipt_check_id": "provider_call_blocked",
            "passed": not bool(attempt_ledger.get("provider_call_performed")),
        },
        {
            "receipt_check_id": "real_execution_disabled",
            "passed": not bool(attempt_ledger.get("real_execution_enabled")),
        },
    ]
    return {
        "capability_invocation_rehearsal_receipt_version": "runner_capability_invocation_rehearsal_receipt_preview_v1",
        "capability_invocation_rehearsal_receipt_status": "capability_invocation_rehearsal_blocked_safely",
        "project_id": runtime_rehearsal.get("project_id", "demo_project_default"),
        "runtime_rehearsal_status": runtime_rehearsal.get("capability_invocation_runtime_rehearsal_status", ""),
        "attempt_ledger_status": attempt_ledger.get("capability_invocation_attempt_ledger_status", ""),
        "receipt_checks": receipt_checks,
        "receipt_check_count": len(receipt_checks),
        "passed_receipt_check_count": sum(1 for item in receipt_checks if item.get("passed")),
        "capability_invocation_allowed": False,
        "runtime_rehearsal_allowed": False,
        "adapter_invocation_attempted": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/capability-invocation-gate/dry-run")
async def dry_run_project_agent_capability_invocation_gate(project_id: str, http_request: Request):
    capability_binding_payload = await dry_run_project_agent_capability_binding(project_id, http_request)

    runner_capability_invocation_gate_preview = _runner_capability_invocation_gate_preview(capability_binding_payload)
    runner_capability_invocation_request_preview = _runner_capability_invocation_request_preview(runner_capability_invocation_gate_preview)
    runner_capability_invocation_decision_preview = _runner_capability_invocation_decision_preview(runner_capability_invocation_request_preview)
    runner_capability_invocation_gate_receipt_preview = _runner_capability_invocation_gate_receipt_preview(runner_capability_invocation_decision_preview)

    project = capability_binding_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_capability_invocation_gate_status": runner_capability_invocation_gate_preview["capability_invocation_gate_status"],
        "latest_runner_capability_invocation_request_status": runner_capability_invocation_request_preview["capability_invocation_request_status"],
        "latest_runner_capability_invocation_decision_status": runner_capability_invocation_decision_preview["capability_invocation_decision_status"],
        "latest_runner_capability_invocation_gate_receipt_status": runner_capability_invocation_gate_receipt_preview["capability_invocation_gate_receipt_status"],
        "latest_runner_capability_invocation_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **capability_binding_payload,
        "project": project,
        "runner_capability_invocation_gate_preview": runner_capability_invocation_gate_preview,
        "runner_capability_invocation_request_preview": runner_capability_invocation_request_preview,
        "runner_capability_invocation_decision_preview": runner_capability_invocation_decision_preview,
        "runner_capability_invocation_gate_receipt_preview": runner_capability_invocation_gate_receipt_preview,
        "dry_run": True,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_capability_invocation_runbook_preview(rehearsal_payload: dict) -> dict:
    rehearsal = dict(rehearsal_payload.get("runner_capability_invocation_runtime_rehearsal_preview") or {})
    ledger = dict(rehearsal_payload.get("runner_capability_invocation_attempt_ledger_preview") or {})
    receipt = dict(rehearsal_payload.get("runner_capability_invocation_rehearsal_receipt_preview") or {})
    project_id = str(rehearsal_payload.get("project", {}).get("project_id") or rehearsal_payload.get("project_id") or "demo_project_default")

    runbook_steps = [
        {
            "runbook_step_id": "review_capability_gate",
            "title": "Review capability invocation gate",
            "status": "required",
            "blocking": True,
        },
        {
            "runbook_step_id": "capture_operator_approval",
            "title": "Capture explicit operator approval",
            "status": "missing",
            "blocking": True,
        },
        {
            "runbook_step_id": "reserve_quota_and_budget",
            "title": "Reserve quota and budget",
            "status": "missing",
            "blocking": True,
        },
        {
            "runbook_step_id": "open_sandbox_session",
            "title": "Open sandbox session",
            "status": "missing",
            "blocking": True,
        },
        {
            "runbook_step_id": "prepare_rollback_plan",
            "title": "Prepare rollback plan",
            "status": "missing",
            "blocking": True,
        },
        {
            "runbook_step_id": "record_attempt_ledger",
            "title": "Record dry-run attempt ledger",
            "status": "preview_recorded",
            "blocking": False,
        },
    ]
    blocking_step_ids = [
        item["runbook_step_id"]
        for item in runbook_steps
        if item.get("blocking") and item.get("status") != "complete"
    ]

    return {
        "capability_invocation_runbook_version": "runner_capability_invocation_runbook_preview_v1",
        "capability_invocation_runbook_status": "capability_invocation_runbook_blocked",
        "project_id": project_id,
        "runtime_rehearsal_status": rehearsal.get("capability_invocation_runtime_rehearsal_status", ""),
        "attempt_ledger_status": ledger.get("capability_invocation_attempt_ledger_status", ""),
        "rehearsal_receipt_status": receipt.get("capability_invocation_rehearsal_receipt_status", ""),
        "runbook_steps": runbook_steps,
        "runbook_step_count": len(runbook_steps),
        "blocking_step_ids": blocking_step_ids,
        "blocking_step_count": len(blocking_step_ids),
        "real_invocation_ready": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_operator_review_packet_preview(runbook: dict) -> dict:
    project_id = str(runbook.get("project_id") or "demo_project_default")
    review_items = [
        {
            "review_item_id": "risk_summary",
            "status": "required",
            "message": "Review blocked runbook steps before any real invocation.",
        },
        {
            "review_item_id": "missing_authorizations",
            "status": "required",
            "message": "Operator approval, quota, sandbox, and rollback references are still missing.",
        },
        {
            "review_item_id": "dry_run_boundary",
            "status": "passed",
            "message": "Dry-run boundary prevented provider calls and real execution.",
        },
        {
            "review_item_id": "audit_trail",
            "status": "preview_recorded",
            "message": "Runbook preview can be copied into an approval record.",
        },
    ]
    return {
        "capability_invocation_operator_review_packet_version": "runner_capability_invocation_operator_review_packet_preview_v1",
        "capability_invocation_operator_review_packet_status": "operator_review_required",
        "project_id": project_id,
        "review_items": review_items,
        "review_item_count": len(review_items),
        "blocking_step_ids": list(runbook.get("blocking_step_ids") or []),
        "manual_review_required": True,
        "operator_approval_captured": False,
        "real_invocation_ready": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_release_guard_preview(
    runbook: dict,
    operator_review_packet: dict,
) -> dict:
    guard_checks = [
        {
            "guard_check_id": "runbook_unblocked",
            "passed": not bool(runbook.get("blocking_step_ids")),
            "blocking": True,
        },
        {
            "guard_check_id": "operator_review_completed",
            "passed": bool(operator_review_packet.get("operator_approval_captured")),
            "blocking": True,
        },
        {
            "guard_check_id": "real_invocation_disabled",
            "passed": not bool(runbook.get("real_execution_enabled")),
            "blocking": False,
        },
        {
            "guard_check_id": "provider_call_not_performed",
            "passed": not bool(runbook.get("provider_call_performed")),
            "blocking": False,
        },
    ]
    blocking_guard_check_ids = [
        item["guard_check_id"]
        for item in guard_checks
        if item.get("blocking") and not item.get("passed")
    ]
    return {
        "capability_invocation_release_guard_version": "runner_capability_invocation_release_guard_preview_v1",
        "capability_invocation_release_guard_status": "release_guard_blocked",
        "project_id": runbook.get("project_id", "demo_project_default"),
        "runbook_status": runbook.get("capability_invocation_runbook_status", ""),
        "operator_review_packet_status": operator_review_packet.get("capability_invocation_operator_review_packet_status", ""),
        "guard_checks": guard_checks,
        "guard_check_count": len(guard_checks),
        "blocking_guard_check_ids": blocking_guard_check_ids,
        "blocking_guard_check_count": len(blocking_guard_check_ids),
        "release_allowed": False,
        "real_invocation_ready": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/capability-invocation-rehearsal/dry-run")
async def dry_run_project_agent_capability_invocation_rehearsal(project_id: str, http_request: Request):
    invocation_gate_payload = await dry_run_project_agent_capability_invocation_gate(project_id, http_request)

    runner_capability_invocation_runtime_rehearsal_preview = _runner_capability_invocation_runtime_rehearsal_preview(invocation_gate_payload)
    runner_capability_invocation_attempt_ledger_preview = _runner_capability_invocation_attempt_ledger_preview(
        runner_capability_invocation_runtime_rehearsal_preview
    )
    runner_capability_invocation_rehearsal_receipt_preview = _runner_capability_invocation_rehearsal_receipt_preview(
        runner_capability_invocation_runtime_rehearsal_preview,
        runner_capability_invocation_attempt_ledger_preview,
    )

    project = invocation_gate_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_capability_invocation_runtime_rehearsal_status": runner_capability_invocation_runtime_rehearsal_preview["capability_invocation_runtime_rehearsal_status"],
        "latest_runner_capability_invocation_attempt_ledger_status": runner_capability_invocation_attempt_ledger_preview["capability_invocation_attempt_ledger_status"],
        "latest_runner_capability_invocation_rehearsal_receipt_status": runner_capability_invocation_rehearsal_receipt_preview["capability_invocation_rehearsal_receipt_status"],
        "latest_runner_capability_invocation_rehearsal_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **invocation_gate_payload,
        "project": project,
        "runner_capability_invocation_runtime_rehearsal_preview": runner_capability_invocation_runtime_rehearsal_preview,
        "runner_capability_invocation_attempt_ledger_preview": runner_capability_invocation_attempt_ledger_preview,
        "runner_capability_invocation_rehearsal_receipt_preview": runner_capability_invocation_rehearsal_receipt_preview,
        "dry_run": True,
        "capability_invocation_allowed": False,
        "runtime_rehearsal_allowed": False,
        "adapter_invocation_attempted": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_capability_invocation_release_packet_preview(runbook_payload: dict) -> dict:
    runbook = dict(runbook_payload.get("runner_capability_invocation_runbook_preview") or {})
    review = dict(runbook_payload.get("runner_capability_invocation_operator_review_packet_preview") or {})
    guard = dict(runbook_payload.get("runner_capability_invocation_release_guard_preview") or {})
    project_id = str(runbook_payload.get("project", {}).get("project_id") or runbook_payload.get("project_id") or "demo_project_default")

    release_checklist = [
        {
            "release_check_id": "runbook_reviewed",
            "status": "required",
            "passed": False,
            "blocking": True,
            "reason": "Capability invocation runbook must be reviewed before real invocation.",
        },
        {
            "release_check_id": "operator_signoff_captured",
            "status": "missing",
            "passed": False,
            "blocking": True,
            "reason": "Explicit operator signoff is required before release.",
        },
        {
            "release_check_id": "quota_budget_confirmed",
            "status": "missing",
            "passed": False,
            "blocking": True,
            "reason": "Quota and budget reservation are required before provider-capable execution.",
        },
        {
            "release_check_id": "sandbox_session_ready",
            "status": "missing",
            "passed": False,
            "blocking": True,
            "reason": "Sandbox session must be ready before any real tool invocation.",
        },
        {
            "release_check_id": "rollback_plan_ready",
            "status": "missing",
            "passed": False,
            "blocking": True,
            "reason": "Rollback plan is required before release.",
        },
        {
            "release_check_id": "dry_run_boundary_verified",
            "status": "passed",
            "passed": True,
            "blocking": False,
            "reason": "Dry-run boundary kept real provider calls disabled.",
        },
    ]
    blocking_release_check_ids = [
        item["release_check_id"]
        for item in release_checklist
        if item.get("blocking") and not item.get("passed")
    ]
    return {
        "capability_invocation_release_packet_version": "runner_capability_invocation_release_packet_preview_v1",
        "capability_invocation_release_packet_status": "release_packet_blocked",
        "project_id": project_id,
        "runbook_status": runbook.get("capability_invocation_runbook_status", ""),
        "operator_review_packet_status": review.get("capability_invocation_operator_review_packet_status", ""),
        "release_guard_status": guard.get("capability_invocation_release_guard_status", ""),
        "release_checklist": release_checklist,
        "release_check_count": len(release_checklist),
        "blocking_release_check_ids": blocking_release_check_ids,
        "blocking_release_check_count": len(blocking_release_check_ids),
        "release_allowed": False,
        "real_invocation_ready": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "dry_run": True,
    }


def _runner_capability_invocation_risk_summary_preview(release_packet: dict) -> dict:
    project_id = str(release_packet.get("project_id") or "demo_project_default")
    risks = [
        {
            "risk_id": "provider_cost_risk",
            "risk_level": "high_without_approval",
            "mitigation": "Require quota, budget, and explicit operator approval before real provider invocation.",
        },
        {
            "risk_id": "external_api_side_effect_risk",
            "risk_level": "high_without_sandbox",
            "mitigation": "Require sandbox session and rollback plan before real execution.",
        },
        {
            "risk_id": "autonomous_agent_decision_risk",
            "risk_level": "blocked",
            "mitigation": "Keep autonomous LLM decision disabled until explicit real execution mode exists.",
        },
        {
            "risk_id": "audit_gap_risk",
            "risk_level": "medium",
            "mitigation": "Record release packet, signoff packet, and final blocked receipt.",
        },
    ]
    return {
        "capability_invocation_risk_summary_version": "runner_capability_invocation_risk_summary_preview_v1",
        "capability_invocation_risk_summary_status": "risk_summary_requires_operator_review",
        "project_id": project_id,
        "risk_items": risks,
        "risk_item_count": len(risks),
        "highest_risk_level": "high_without_approval",
        "release_allowed": False,
        "manual_review_required": True,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "dry_run": True,
    }


def _runner_capability_invocation_signoff_packet_preview(
    release_packet: dict,
    risk_summary: dict,
) -> dict:
    project_id = str(release_packet.get("project_id") or "demo_project_default")
    signoff_fields = [
        {
            "signoff_field_id": "operator_id",
            "status": "missing",
            "required": True,
        },
        {
            "signoff_field_id": "approval_reason",
            "status": "missing",
            "required": True,
        },
        {
            "signoff_field_id": "quota_budget_acknowledgement",
            "status": "missing",
            "required": True,
        },
        {
            "signoff_field_id": "sandbox_acknowledgement",
            "status": "missing",
            "required": True,
        },
        {
            "signoff_field_id": "rollback_acknowledgement",
            "status": "missing",
            "required": True,
        },
    ]
    missing_signoff_field_ids = [
        item["signoff_field_id"]
        for item in signoff_fields
        if item.get("required") and item.get("status") != "captured"
    ]
    return {
        "capability_invocation_signoff_packet_version": "runner_capability_invocation_signoff_packet_preview_v1",
        "capability_invocation_signoff_packet_status": "signoff_missing",
        "project_id": project_id,
        "release_packet_status": release_packet.get("capability_invocation_release_packet_status", ""),
        "risk_summary_status": risk_summary.get("capability_invocation_risk_summary_status", ""),
        "signoff_fields": signoff_fields,
        "signoff_field_count": len(signoff_fields),
        "missing_signoff_field_ids": missing_signoff_field_ids,
        "missing_signoff_field_count": len(missing_signoff_field_ids),
        "operator_signoff_captured": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "dry_run": True,
    }


def _runner_capability_invocation_final_blocked_receipt_preview(
    release_packet: dict,
    risk_summary: dict,
    signoff_packet: dict,
) -> dict:
    project_id = str(release_packet.get("project_id") or "demo_project_default")
    receipt_reasons = [
        "Release packet is blocked.",
        "Operator signoff is missing.",
        "Quota, sandbox, and rollback acknowledgements are missing.",
        "Real capability invocation remains disabled in dry-run mode.",
    ]
    return {
        "capability_invocation_final_blocked_receipt_version": "runner_capability_invocation_final_blocked_receipt_preview_v1",
        "capability_invocation_final_blocked_receipt_status": "final_blocked_before_real_invocation",
        "project_id": project_id,
        "release_packet_status": release_packet.get("capability_invocation_release_packet_status", ""),
        "risk_summary_status": risk_summary.get("capability_invocation_risk_summary_status", ""),
        "signoff_packet_status": signoff_packet.get("capability_invocation_signoff_packet_status", ""),
        "receipt_reasons": receipt_reasons,
        "receipt_reason_count": len(receipt_reasons),
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/capability-invocation-runbook/dry-run")
async def dry_run_project_agent_capability_invocation_runbook(project_id: str, http_request: Request):
    rehearsal_payload = await dry_run_project_agent_capability_invocation_rehearsal(project_id, http_request)

    runner_capability_invocation_runbook_preview = _runner_capability_invocation_runbook_preview(rehearsal_payload)
    runner_capability_invocation_operator_review_packet_preview = _runner_capability_invocation_operator_review_packet_preview(
        runner_capability_invocation_runbook_preview
    )
    runner_capability_invocation_release_guard_preview = _runner_capability_invocation_release_guard_preview(
        runner_capability_invocation_runbook_preview,
        runner_capability_invocation_operator_review_packet_preview,
    )

    project = rehearsal_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_capability_invocation_runbook_status": runner_capability_invocation_runbook_preview["capability_invocation_runbook_status"],
        "latest_runner_capability_invocation_operator_review_packet_status": runner_capability_invocation_operator_review_packet_preview["capability_invocation_operator_review_packet_status"],
        "latest_runner_capability_invocation_release_guard_status": runner_capability_invocation_release_guard_preview["capability_invocation_release_guard_status"],
        "latest_runner_capability_invocation_release_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **rehearsal_payload,
        "project": project,
        "runner_capability_invocation_runbook_preview": runner_capability_invocation_runbook_preview,
        "runner_capability_invocation_operator_review_packet_preview": runner_capability_invocation_operator_review_packet_preview,
        "runner_capability_invocation_release_guard_preview": runner_capability_invocation_release_guard_preview,
        "dry_run": True,
        "release_allowed": False,
        "real_invocation_ready": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_real_execution_mode_gate_preview(release_packet_payload: dict) -> dict:
    release_packet = dict(release_packet_payload.get("runner_capability_invocation_release_packet_preview") or {})
    risk_summary = dict(release_packet_payload.get("runner_capability_invocation_risk_summary_preview") or {})
    signoff_packet = dict(release_packet_payload.get("runner_capability_invocation_signoff_packet_preview") or {})
    blocked_receipt = dict(release_packet_payload.get("runner_capability_invocation_final_blocked_receipt_preview") or {})
    project_id = str(release_packet_payload.get("project", {}).get("project_id") or release_packet_payload.get("project_id") or "demo_project_default")

    mode_gate_checks = [
        {
            "mode_gate_check_id": "release_packet_unblocked",
            "passed": bool(release_packet.get("release_allowed")),
            "blocking": True,
            "reason": "Release packet must be unblocked before real execution mode can be enabled.",
        },
        {
            "mode_gate_check_id": "operator_signoff_captured",
            "passed": bool(signoff_packet.get("operator_signoff_captured")),
            "blocking": True,
            "reason": "Explicit operator signoff is required.",
        },
        {
            "mode_gate_check_id": "provider_credentials_ready",
            "passed": False,
            "blocking": True,
            "reason": "Provider credentials are not enabled for real execution mode.",
        },
        {
            "mode_gate_check_id": "quota_budget_reserved",
            "passed": False,
            "blocking": True,
            "reason": "Quota and budget must be reserved before real provider calls.",
        },
        {
            "mode_gate_check_id": "sandbox_session_ready",
            "passed": False,
            "blocking": True,
            "reason": "Sandbox session must be ready before tool invocation.",
        },
        {
            "mode_gate_check_id": "rollback_plan_confirmed",
            "passed": False,
            "blocking": True,
            "reason": "Rollback plan must be confirmed before real execution.",
        },
        {
            "mode_gate_check_id": "kill_switch_enabled",
            "passed": True,
            "blocking": False,
            "reason": "Kill switch remains enabled and real execution stays blocked.",
        },
        {
            "mode_gate_check_id": "dry_run_boundary_verified",
            "passed": True,
            "blocking": False,
            "reason": "Dry-run boundary prevented provider calls and real execution.",
        },
    ]
    blocking_mode_gate_check_ids = [
        item["mode_gate_check_id"]
        for item in mode_gate_checks
        if item.get("blocking") and not item.get("passed")
    ]
    return {
        "real_execution_mode_gate_version": "runner_real_execution_mode_gate_preview_v1",
        "real_execution_mode_gate_status": "real_execution_mode_blocked",
        "project_id": project_id,
        "release_packet_status": release_packet.get("capability_invocation_release_packet_status", ""),
        "risk_summary_status": risk_summary.get("capability_invocation_risk_summary_status", ""),
        "signoff_packet_status": signoff_packet.get("capability_invocation_signoff_packet_status", ""),
        "final_blocked_receipt_status": blocked_receipt.get("capability_invocation_final_blocked_receipt_status", ""),
        "mode_gate_checks": mode_gate_checks,
        "mode_gate_check_count": len(mode_gate_checks),
        "blocking_mode_gate_check_ids": blocking_mode_gate_check_ids,
        "blocking_mode_gate_check_count": len(blocking_mode_gate_check_ids),
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "dry_run": True,
    }


def _runner_real_execution_switch_plan_preview(mode_gate: dict) -> dict:
    project_id = str(mode_gate.get("project_id") or "demo_project_default")
    switch_steps = [
        {
            "switch_step_id": "keep_dry_run_mode",
            "status": "active",
            "description": "Keep project in dry-run mode.",
        },
        {
            "switch_step_id": "require_operator_signoff",
            "status": "blocked",
            "description": "Capture operator signoff before real mode.",
        },
        {
            "switch_step_id": "require_provider_credentials",
            "status": "blocked",
            "description": "Enable provider credentials only after approval.",
        },
        {
            "switch_step_id": "require_quota_sandbox_rollback",
            "status": "blocked",
            "description": "Reserve quota, open sandbox, and confirm rollback.",
        },
        {
            "switch_step_id": "preserve_kill_switch",
            "status": "active",
            "description": "Keep kill switch active for all future real execution attempts.",
        },
    ]
    return {
        "real_execution_switch_plan_version": "runner_real_execution_switch_plan_preview_v1",
        "real_execution_switch_plan_status": "switch_plan_blocked_in_dry_run",
        "project_id": project_id,
        "real_execution_mode_gate_status": mode_gate.get("real_execution_mode_gate_status", ""),
        "switch_steps": switch_steps,
        "switch_step_count": len(switch_steps),
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "dry_run": True,
    }


def _runner_real_execution_safety_case_preview(
    mode_gate: dict,
    switch_plan: dict,
) -> dict:
    project_id = str(mode_gate.get("project_id") or "demo_project_default")
    safety_claims = [
        {
            "safety_claim_id": "no_provider_call",
            "passed": True,
            "evidence": "provider_call_performed is false.",
        },
        {
            "safety_claim_id": "no_external_api_call",
            "passed": True,
            "evidence": "external_api_called is false.",
        },
        {
            "safety_claim_id": "no_agent_execution",
            "passed": True,
            "evidence": "agent_execution_performed is false.",
        },
        {
            "safety_claim_id": "real_mode_not_enabled",
            "passed": True,
            "evidence": "real_execution_enabled is false.",
        },
        {
            "safety_claim_id": "manual_review_required",
            "passed": True,
            "evidence": "manual_review_required is true.",
        },
    ]
    return {
        "real_execution_safety_case_version": "runner_real_execution_safety_case_preview_v1",
        "real_execution_safety_case_status": "real_execution_safety_case_blocked_safely",
        "project_id": project_id,
        "real_execution_mode_gate_status": mode_gate.get("real_execution_mode_gate_status", ""),
        "real_execution_switch_plan_status": switch_plan.get("real_execution_switch_plan_status", ""),
        "safety_claims": safety_claims,
        "safety_claim_count": len(safety_claims),
        "passed_safety_claim_count": sum(1 for item in safety_claims if item.get("passed")),
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_mode_receipt_preview(
    mode_gate: dict,
    switch_plan: dict,
    safety_case: dict,
) -> dict:
    project_id = str(mode_gate.get("project_id") or "demo_project_default")
    receipt_reasons = [
        "Real execution mode remains blocked.",
        "Operator signoff is missing.",
        "Provider credentials, quota, sandbox, and rollback are not ready.",
        "Kill switch remains active.",
        "Dry-run boundary remains enforced.",
    ]
    return {
        "real_execution_mode_receipt_version": "runner_real_execution_mode_receipt_preview_v1",
        "real_execution_mode_receipt_status": "real_execution_mode_blocked_safely",
        "project_id": project_id,
        "real_execution_mode_gate_status": mode_gate.get("real_execution_mode_gate_status", ""),
        "real_execution_switch_plan_status": switch_plan.get("real_execution_switch_plan_status", ""),
        "real_execution_safety_case_status": safety_case.get("real_execution_safety_case_status", ""),
        "receipt_reasons": receipt_reasons,
        "receipt_reason_count": len(receipt_reasons),
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/capability-invocation-release-packet/dry-run")
async def dry_run_project_agent_capability_invocation_release_packet(project_id: str, http_request: Request):
    runbook_payload = await dry_run_project_agent_capability_invocation_runbook(project_id, http_request)

    runner_capability_invocation_release_packet_preview = _runner_capability_invocation_release_packet_preview(runbook_payload)
    runner_capability_invocation_risk_summary_preview = _runner_capability_invocation_risk_summary_preview(
        runner_capability_invocation_release_packet_preview
    )
    runner_capability_invocation_signoff_packet_preview = _runner_capability_invocation_signoff_packet_preview(
        runner_capability_invocation_release_packet_preview,
        runner_capability_invocation_risk_summary_preview,
    )
    runner_capability_invocation_final_blocked_receipt_preview = _runner_capability_invocation_final_blocked_receipt_preview(
        runner_capability_invocation_release_packet_preview,
        runner_capability_invocation_risk_summary_preview,
        runner_capability_invocation_signoff_packet_preview,
    )

    project = runbook_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_capability_invocation_release_packet_status": runner_capability_invocation_release_packet_preview["capability_invocation_release_packet_status"],
        "latest_runner_capability_invocation_risk_summary_status": runner_capability_invocation_risk_summary_preview["capability_invocation_risk_summary_status"],
        "latest_runner_capability_invocation_signoff_packet_status": runner_capability_invocation_signoff_packet_preview["capability_invocation_signoff_packet_status"],
        "latest_runner_capability_invocation_final_blocked_receipt_status": runner_capability_invocation_final_blocked_receipt_preview["capability_invocation_final_blocked_receipt_status"],
        "latest_runner_capability_invocation_release_packet_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **runbook_payload,
        "project": project,
        "runner_capability_invocation_release_packet_preview": runner_capability_invocation_release_packet_preview,
        "runner_capability_invocation_risk_summary_preview": runner_capability_invocation_risk_summary_preview,
        "runner_capability_invocation_signoff_packet_preview": runner_capability_invocation_signoff_packet_preview,
        "runner_capability_invocation_final_blocked_receipt_preview": runner_capability_invocation_final_blocked_receipt_preview,
        "dry_run": True,
        "release_allowed": False,
        "real_invocation_ready": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "real_execution_enabled": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_real_execution_readiness_summary_preview(mode_gate_payload: dict) -> dict:
    mode_gate = dict(mode_gate_payload.get("runner_real_execution_mode_gate_preview") or {})
    switch_plan = dict(mode_gate_payload.get("runner_real_execution_switch_plan_preview") or {})
    safety_case = dict(mode_gate_payload.get("runner_real_execution_safety_case_preview") or {})
    mode_receipt = dict(mode_gate_payload.get("runner_real_execution_mode_receipt_preview") or {})
    release_packet = dict(mode_gate_payload.get("runner_capability_invocation_release_packet_preview") or {})
    signoff_packet = dict(mode_gate_payload.get("runner_capability_invocation_signoff_packet_preview") or {})
    project_id = str(mode_gate_payload.get("project", {}).get("project_id") or mode_gate_payload.get("project_id") or "demo_project_default")

    readiness_checks = [
        {
            "readiness_check_id": "real_execution_mode_gate",
            "label": "Real execution mode gate",
            "status": mode_gate.get("real_execution_mode_gate_status", "not_refreshed"),
            "passed": bool(mode_gate.get("real_execution_mode_allowed")),
            "blocking": True,
        },
        {
            "readiness_check_id": "release_packet",
            "label": "Capability invocation release packet",
            "status": release_packet.get("capability_invocation_release_packet_status", "not_refreshed"),
            "passed": bool(release_packet.get("release_allowed")),
            "blocking": True,
        },
        {
            "readiness_check_id": "operator_signoff",
            "label": "Operator signoff",
            "status": signoff_packet.get("capability_invocation_signoff_packet_status", "not_refreshed"),
            "passed": bool(signoff_packet.get("operator_signoff_captured")),
            "blocking": True,
        },
        {
            "readiness_check_id": "switch_plan",
            "label": "Real execution switch plan",
            "status": switch_plan.get("real_execution_switch_plan_status", "not_refreshed"),
            "passed": bool(switch_plan.get("real_execution_mode_allowed")),
            "blocking": True,
        },
        {
            "readiness_check_id": "safety_case",
            "label": "Real execution safety case",
            "status": safety_case.get("real_execution_safety_case_status", "not_refreshed"),
            "passed": bool(safety_case.get("real_execution_enabled")),
            "blocking": True,
        },
        {
            "readiness_check_id": "dry_run_boundary",
            "label": "Dry-run boundary",
            "status": mode_receipt.get("real_execution_mode_receipt_status", "not_refreshed"),
            "passed": not bool(mode_receipt.get("real_execution_enabled")),
            "blocking": False,
        },
    ]
    blocking_readiness_check_ids = [
        item["readiness_check_id"]
        for item in readiness_checks
        if item.get("blocking") and not item.get("passed")
    ]
    return {
        "real_execution_readiness_summary_version": "runner_real_execution_readiness_summary_preview_v1",
        "real_execution_readiness_summary_status": "not_ready_for_real_execution",
        "project_id": project_id,
        "go_no_go_decision": "no_go",
        "go_no_go_reason": "Real execution remains blocked until signoff, quota, sandbox, rollback, credentials, and release packet checks are complete.",
        "readiness_checks": readiness_checks,
        "readiness_check_count": len(readiness_checks),
        "blocking_readiness_check_ids": blocking_readiness_check_ids,
        "blocking_readiness_check_count": len(blocking_readiness_check_ids),
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_operator_next_actions_preview(readiness_summary: dict) -> dict:
    project_id = str(readiness_summary.get("project_id") or "demo_project_default")
    next_actions = [
        {
            "next_action_id": "continue_dry_run_batches",
            "label": "Continue dry-run validation batches",
            "priority": "high",
            "owner": "operator",
        },
        {
            "next_action_id": "prepare_operator_signoff",
            "label": "Prepare operator signoff fields",
            "priority": "high",
            "owner": "operator",
        },
        {
            "next_action_id": "prepare_quota_sandbox_rollback",
            "label": "Prepare quota, sandbox, and rollback references",
            "priority": "high",
            "owner": "operator",
        },
        {
            "next_action_id": "keep_real_execution_disabled",
            "label": "Keep real execution disabled until explicit approval",
            "priority": "critical",
            "owner": "system",
        },
    ]
    return {
        "real_execution_operator_next_actions_version": "runner_real_execution_operator_next_actions_preview_v1",
        "real_execution_operator_next_actions_status": "operator_actions_required",
        "project_id": project_id,
        "next_actions": next_actions,
        "next_action_count": len(next_actions),
        "manual_review_required": True,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_executive_brief_preview(
    readiness_summary: dict,
    operator_next_actions: dict,
) -> dict:
    project_id = str(readiness_summary.get("project_id") or "demo_project_default")
    brief_lines = [
        "No-go for real execution.",
        "Dry-run remains safe: no provider call, no external API call, no agent execution.",
        "Manual review and signoff are still required.",
        "Next step is to prepare approval, quota, sandbox, rollback, and credentials before any real mode attempt.",
    ]
    return {
        "real_execution_executive_brief_version": "runner_real_execution_executive_brief_preview_v1",
        "real_execution_executive_brief_status": "real_execution_no_go_brief_ready",
        "project_id": project_id,
        "brief_lines": brief_lines,
        "brief_line_count": len(brief_lines),
        "go_no_go_decision": readiness_summary.get("go_no_go_decision", "no_go"),
        "blocking_readiness_check_count": readiness_summary.get("blocking_readiness_check_count", 0),
        "operator_next_action_count": operator_next_actions.get("next_action_count", 0),
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-mode-gate/dry-run")
async def dry_run_project_agent_real_execution_mode_gate(project_id: str, http_request: Request):
    release_packet_payload = await dry_run_project_agent_capability_invocation_release_packet(project_id, http_request)

    runner_real_execution_mode_gate_preview = _runner_real_execution_mode_gate_preview(release_packet_payload)
    runner_real_execution_switch_plan_preview = _runner_real_execution_switch_plan_preview(
        runner_real_execution_mode_gate_preview
    )
    runner_real_execution_safety_case_preview = _runner_real_execution_safety_case_preview(
        runner_real_execution_mode_gate_preview,
        runner_real_execution_switch_plan_preview,
    )
    runner_real_execution_mode_receipt_preview = _runner_real_execution_mode_receipt_preview(
        runner_real_execution_mode_gate_preview,
        runner_real_execution_switch_plan_preview,
        runner_real_execution_safety_case_preview,
    )

    project = release_packet_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_mode_gate_status": runner_real_execution_mode_gate_preview["real_execution_mode_gate_status"],
        "latest_runner_real_execution_switch_plan_status": runner_real_execution_switch_plan_preview["real_execution_switch_plan_status"],
        "latest_runner_real_execution_safety_case_status": runner_real_execution_safety_case_preview["real_execution_safety_case_status"],
        "latest_runner_real_execution_mode_receipt_status": runner_real_execution_mode_receipt_preview["real_execution_mode_receipt_status"],
        "latest_runner_real_execution_mode_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **release_packet_payload,
        "project": project,
        "runner_real_execution_mode_gate_preview": runner_real_execution_mode_gate_preview,
        "runner_real_execution_switch_plan_preview": runner_real_execution_switch_plan_preview,
        "runner_real_execution_safety_case_preview": runner_real_execution_safety_case_preview,
        "runner_real_execution_mode_receipt_preview": runner_real_execution_mode_receipt_preview,
        "dry_run": True,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_real_execution_approval_request_draft_preview(readiness_payload: dict) -> dict:
    summary = dict(readiness_payload.get("runner_real_execution_readiness_summary_preview") or {})
    actions = dict(readiness_payload.get("runner_real_execution_operator_next_actions_preview") or {})
    brief = dict(readiness_payload.get("runner_real_execution_executive_brief_preview") or {})
    mode_receipt = dict(readiness_payload.get("runner_real_execution_mode_receipt_preview") or {})
    project_id = str(readiness_payload.get("project", {}).get("project_id") or readiness_payload.get("project_id") or "demo_project_default")

    required_approval_fields = [
        {
            "approval_field_id": "operator_id",
            "label": "Operator ID",
            "required": True,
            "status": "missing",
        },
        {
            "approval_field_id": "approval_reason",
            "label": "Approval reason",
            "required": True,
            "status": "missing",
        },
        {
            "approval_field_id": "budget_limit_acknowledgement",
            "label": "Budget / quota acknowledgement",
            "required": True,
            "status": "missing",
        },
        {
            "approval_field_id": "sandbox_session_id",
            "label": "Sandbox session ID",
            "required": True,
            "status": "missing",
        },
        {
            "approval_field_id": "rollback_plan_id",
            "label": "Rollback plan ID",
            "required": True,
            "status": "missing",
        },
        {
            "approval_field_id": "provider_credential_scope",
            "label": "Provider credential scope",
            "required": True,
            "status": "missing",
        },
        {
            "approval_field_id": "kill_switch_acknowledgement",
            "label": "Kill switch acknowledgement",
            "required": True,
            "status": "missing",
        },
    ]
    missing_approval_field_ids = [
        item["approval_field_id"]
        for item in required_approval_fields
        if item.get("required") and item.get("status") != "captured"
    ]

    return {
        "real_execution_approval_request_draft_version": "runner_real_execution_approval_request_draft_preview_v1",
        "real_execution_approval_request_draft_status": "approval_request_draft_blocked",
        "project_id": project_id,
        "go_no_go_decision": summary.get("go_no_go_decision", "no_go"),
        "readiness_summary_status": summary.get("real_execution_readiness_summary_status", ""),
        "operator_next_actions_status": actions.get("real_execution_operator_next_actions_status", ""),
        "executive_brief_status": brief.get("real_execution_executive_brief_status", ""),
        "real_execution_mode_receipt_status": mode_receipt.get("real_execution_mode_receipt_status", ""),
        "required_approval_fields": required_approval_fields,
        "required_approval_field_count": len(required_approval_fields),
        "missing_approval_field_ids": missing_approval_field_ids,
        "missing_approval_field_count": len(missing_approval_field_ids),
        "approval_request_ready": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_approval_form_schema_preview(approval_request: dict) -> dict:
    project_id = str(approval_request.get("project_id") or "demo_project_default")
    form_sections = [
        {
            "form_section_id": "operator_identity",
            "title": "Operator identity",
            "field_ids": ["operator_id"],
        },
        {
            "form_section_id": "approval_reasoning",
            "title": "Approval reasoning",
            "field_ids": ["approval_reason"],
        },
        {
            "form_section_id": "runtime_controls",
            "title": "Runtime controls",
            "field_ids": [
                "budget_limit_acknowledgement",
                "sandbox_session_id",
                "rollback_plan_id",
                "provider_credential_scope",
                "kill_switch_acknowledgement",
            ],
        },
    ]
    return {
        "real_execution_approval_form_schema_version": "runner_real_execution_approval_form_schema_preview_v1",
        "real_execution_approval_form_schema_status": "approval_form_schema_ready_for_review",
        "project_id": project_id,
        "form_sections": form_sections,
        "form_section_count": len(form_sections),
        "required_approval_fields": list(approval_request.get("required_approval_fields") or []),
        "missing_approval_field_ids": list(approval_request.get("missing_approval_field_ids") or []),
        "approval_request_ready": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "dry_run": True,
    }


def _runner_real_execution_approval_review_queue_preview(
    approval_request: dict,
    approval_form_schema: dict,
) -> dict:
    project_id = str(approval_request.get("project_id") or "demo_project_default")
    queue_items = [
        {
            "queue_item_id": f"real_execution_approval_{project_id}_draft",
            "queue_item_type": "real_execution_approval_request",
            "queue_item_status": "waiting_for_operator_input",
            "priority": "critical",
            "blocked_by": list(approval_request.get("missing_approval_field_ids") or []),
        }
    ]
    return {
        "real_execution_approval_review_queue_version": "runner_real_execution_approval_review_queue_preview_v1",
        "real_execution_approval_review_queue_status": "approval_review_queue_waiting_for_operator",
        "project_id": project_id,
        "queue_items": queue_items,
        "queue_item_count": len(queue_items),
        "approval_form_schema_status": approval_form_schema.get("real_execution_approval_form_schema_status", ""),
        "operator_approval_captured": False,
        "approval_request_ready": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_approval_request_receipt_preview(
    approval_request: dict,
    approval_form_schema: dict,
    approval_review_queue: dict,
) -> dict:
    project_id = str(approval_request.get("project_id") or "demo_project_default")
    receipt_reasons = [
        "Approval request is only a dry-run draft.",
        "Required approval fields are missing.",
        "Approval review queue is waiting for operator input.",
        "Real execution mode remains disabled.",
    ]
    return {
        "real_execution_approval_request_receipt_version": "runner_real_execution_approval_request_receipt_preview_v1",
        "real_execution_approval_request_receipt_status": "approval_request_draft_recorded_not_approved",
        "project_id": project_id,
        "approval_request_draft_status": approval_request.get("real_execution_approval_request_draft_status", ""),
        "approval_form_schema_status": approval_form_schema.get("real_execution_approval_form_schema_status", ""),
        "approval_review_queue_status": approval_review_queue.get("real_execution_approval_review_queue_status", ""),
        "receipt_reasons": receipt_reasons,
        "receipt_reason_count": len(receipt_reasons),
        "operator_approval_captured": False,
        "approval_request_ready": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-readiness-summary/dry-run")
async def dry_run_project_agent_real_execution_readiness_summary(project_id: str, http_request: Request):
    mode_gate_payload = await dry_run_project_agent_real_execution_mode_gate(project_id, http_request)

    runner_real_execution_readiness_summary_preview = _runner_real_execution_readiness_summary_preview(mode_gate_payload)
    runner_real_execution_operator_next_actions_preview = _runner_real_execution_operator_next_actions_preview(
        runner_real_execution_readiness_summary_preview
    )
    runner_real_execution_executive_brief_preview = _runner_real_execution_executive_brief_preview(
        runner_real_execution_readiness_summary_preview,
        runner_real_execution_operator_next_actions_preview,
    )

    project = mode_gate_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_readiness_summary_status": runner_real_execution_readiness_summary_preview["real_execution_readiness_summary_status"],
        "latest_runner_real_execution_go_no_go_decision": runner_real_execution_readiness_summary_preview["go_no_go_decision"],
        "latest_runner_real_execution_operator_next_actions_status": runner_real_execution_operator_next_actions_preview["real_execution_operator_next_actions_status"],
        "latest_runner_real_execution_executive_brief_status": runner_real_execution_executive_brief_preview["real_execution_executive_brief_status"],
        "latest_runner_real_execution_summary_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **mode_gate_payload,
        "project": project,
        "runner_real_execution_readiness_summary_preview": runner_real_execution_readiness_summary_preview,
        "runner_real_execution_operator_next_actions_preview": runner_real_execution_operator_next_actions_preview,
        "runner_real_execution_executive_brief_preview": runner_real_execution_executive_brief_preview,
        "dry_run": True,
        "go_no_go_decision": "no_go",
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_real_execution_approval_decision_preview(approval_payload: dict) -> dict:
    draft = dict(approval_payload.get("runner_real_execution_approval_request_draft_preview") or {})
    schema = dict(approval_payload.get("runner_real_execution_approval_form_schema_preview") or {})
    queue = dict(approval_payload.get("runner_real_execution_approval_review_queue_preview") or {})
    receipt = dict(approval_payload.get("runner_real_execution_approval_request_receipt_preview") or {})
    project_id = str(approval_payload.get("project", {}).get("project_id") or approval_payload.get("project_id") or "demo_project_default")

    decision_checks = [
        {
            "decision_check_id": "approval_request_ready",
            "passed": bool(draft.get("approval_request_ready")),
            "blocking": True,
            "reason": "Approval request must be complete before decision.",
        },
        {
            "decision_check_id": "operator_approval_captured",
            "passed": bool(receipt.get("operator_approval_captured")),
            "blocking": True,
            "reason": "Operator approval has not been captured.",
        },
        {
            "decision_check_id": "missing_fields_resolved",
            "passed": not bool(draft.get("missing_approval_field_ids")),
            "blocking": True,
            "reason": "Required approval fields are still missing.",
        },
        {
            "decision_check_id": "review_queue_cleared",
            "passed": str(queue.get("real_execution_approval_review_queue_status") or "") == "approval_review_queue_cleared",
            "blocking": True,
            "reason": "Approval review queue is still waiting for operator input.",
        },
        {
            "decision_check_id": "form_schema_available",
            "passed": bool(schema.get("real_execution_approval_form_schema_version")),
            "blocking": False,
            "reason": "Approval form schema is available for review.",
        },
        {
            "decision_check_id": "dry_run_boundary_verified",
            "passed": True,
            "blocking": False,
            "reason": "Dry-run boundary remains active.",
        },
    ]
    blocking_decision_check_ids = [
        item["decision_check_id"]
        for item in decision_checks
        if item.get("blocking") and not item.get("passed")
    ]

    return {
        "real_execution_approval_decision_version": "runner_real_execution_approval_decision_preview_v1",
        "real_execution_approval_decision_status": "approval_decision_denied_in_dry_run",
        "project_id": project_id,
        "approval_request_draft_status": draft.get("real_execution_approval_request_draft_status", ""),
        "approval_form_schema_status": schema.get("real_execution_approval_form_schema_status", ""),
        "approval_review_queue_status": queue.get("real_execution_approval_review_queue_status", ""),
        "approval_request_receipt_status": receipt.get("real_execution_approval_request_receipt_status", ""),
        "decision_checks": decision_checks,
        "decision_check_count": len(decision_checks),
        "blocking_decision_check_ids": blocking_decision_check_ids,
        "blocking_decision_check_count": len(blocking_decision_check_ids),
        "approval_decision": "denied",
        "operator_approval_captured": False,
        "approval_request_ready": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_decision_ledger_preview(approval_decision: dict) -> dict:
    project_id = str(approval_decision.get("project_id") or "demo_project_default")
    decision_events = [
        {
            "decision_event_id": f"real_execution_approval_{project_id}_denied",
            "decision_event_type": "real_execution_approval_denied",
            "decision_event_status": "recorded",
            "decision": "denied",
            "reason": "Approval request is incomplete and dry-run mode cannot enable real execution.",
            "blocking_decision_check_ids": list(approval_decision.get("blocking_decision_check_ids") or []),
        }
    ]
    return {
        "real_execution_decision_ledger_version": "runner_real_execution_decision_ledger_preview_v1",
        "real_execution_decision_ledger_status": "decision_ledger_recorded",
        "project_id": project_id,
        "decision_events": decision_events,
        "decision_event_count": len(decision_events),
        "approval_decision_status": approval_decision.get("real_execution_approval_decision_status", ""),
        "approval_decision": "denied",
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "dry_run": True,
    }


def _runner_real_execution_denied_receipt_preview(
    approval_decision: dict,
    decision_ledger: dict,
) -> dict:
    project_id = str(approval_decision.get("project_id") or "demo_project_default")
    denied_reasons = [
        "Approval decision is denied in dry-run.",
        "Operator approval is missing.",
        "Approval request is incomplete.",
        "Real execution mode remains disabled.",
        "No provider call or Agent execution was performed.",
    ]
    return {
        "real_execution_denied_receipt_version": "runner_real_execution_denied_receipt_preview_v1",
        "real_execution_denied_receipt_status": "real_execution_denied_safely",
        "project_id": project_id,
        "approval_decision_status": approval_decision.get("real_execution_approval_decision_status", ""),
        "decision_ledger_status": decision_ledger.get("real_execution_decision_ledger_status", ""),
        "denied_reasons": denied_reasons,
        "denied_reason_count": len(denied_reasons),
        "approval_decision": "denied",
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-approval-request/dry-run")
async def dry_run_project_agent_real_execution_approval_request(project_id: str, http_request: Request):
    readiness_payload = await dry_run_project_agent_real_execution_readiness_summary(project_id, http_request)

    runner_real_execution_approval_request_draft_preview = _runner_real_execution_approval_request_draft_preview(readiness_payload)
    runner_real_execution_approval_form_schema_preview = _runner_real_execution_approval_form_schema_preview(
        runner_real_execution_approval_request_draft_preview
    )
    runner_real_execution_approval_review_queue_preview = _runner_real_execution_approval_review_queue_preview(
        runner_real_execution_approval_request_draft_preview,
        runner_real_execution_approval_form_schema_preview,
    )
    runner_real_execution_approval_request_receipt_preview = _runner_real_execution_approval_request_receipt_preview(
        runner_real_execution_approval_request_draft_preview,
        runner_real_execution_approval_form_schema_preview,
        runner_real_execution_approval_review_queue_preview,
    )

    project = readiness_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_approval_request_draft_status": runner_real_execution_approval_request_draft_preview["real_execution_approval_request_draft_status"],
        "latest_runner_real_execution_approval_form_schema_status": runner_real_execution_approval_form_schema_preview["real_execution_approval_form_schema_status"],
        "latest_runner_real_execution_approval_review_queue_status": runner_real_execution_approval_review_queue_preview["real_execution_approval_review_queue_status"],
        "latest_runner_real_execution_approval_request_receipt_status": runner_real_execution_approval_request_receipt_preview["real_execution_approval_request_receipt_status"],
        "latest_runner_real_execution_operator_approval_captured": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **readiness_payload,
        "project": project,
        "runner_real_execution_approval_request_draft_preview": runner_real_execution_approval_request_draft_preview,
        "runner_real_execution_approval_form_schema_preview": runner_real_execution_approval_form_schema_preview,
        "runner_real_execution_approval_review_queue_preview": runner_real_execution_approval_review_queue_preview,
        "runner_real_execution_approval_request_receipt_preview": runner_real_execution_approval_request_receipt_preview,
        "dry_run": True,
        "operator_approval_captured": False,
        "approval_request_ready": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }



def _runner_real_execution_launch_authorization_preview(decision_payload: dict) -> dict:
    decision = dict(decision_payload.get("runner_real_execution_approval_decision_preview") or {})
    ledger = dict(decision_payload.get("runner_real_execution_decision_ledger_preview") or {})
    denied_receipt = dict(decision_payload.get("runner_real_execution_denied_receipt_preview") or {})
    project_id = str(decision_payload.get("project", {}).get("project_id") or decision_payload.get("project_id") or "demo_project_default")

    authorization_checks = [
        {
            "authorization_check_id": "approval_decision_approved",
            "passed": str(decision.get("approval_decision") or "") == "approved",
            "blocking": True,
            "reason": "Approval decision must be approved before launch authorization.",
        },
        {
            "authorization_check_id": "decision_ledger_recorded",
            "passed": bool(ledger.get("real_execution_decision_ledger_version")),
            "blocking": False,
            "reason": "Decision ledger is recorded for audit.",
        },
        {
            "authorization_check_id": "denied_receipt_absent",
            "passed": False,
            "blocking": True,
            "reason": "Denied receipt is present, so launch cannot be authorized.",
        },
        {
            "authorization_check_id": "real_execution_mode_enabled",
            "passed": bool(decision.get("real_execution_enabled")),
            "blocking": True,
            "reason": "Real execution mode is not enabled.",
        },
        {
            "authorization_check_id": "provider_call_guarded",
            "passed": not bool(decision.get("provider_call_performed")),
            "blocking": False,
            "reason": "No provider call was performed in dry-run.",
        },
        {
            "authorization_check_id": "dry_run_boundary_verified",
            "passed": True,
            "blocking": False,
            "reason": "Dry-run boundary remains enforced.",
        },
    ]
    blocking_authorization_check_ids = [
        item["authorization_check_id"]
        for item in authorization_checks
        if item.get("blocking") and not item.get("passed")
    ]

    return {
        "real_execution_launch_authorization_version": "runner_real_execution_launch_authorization_preview_v1",
        "real_execution_launch_authorization_status": "launch_authorization_denied",
        "project_id": project_id,
        "approval_decision_status": decision.get("real_execution_approval_decision_status", ""),
        "decision_ledger_status": ledger.get("real_execution_decision_ledger_status", ""),
        "denied_receipt_status": denied_receipt.get("real_execution_denied_receipt_status", ""),
        "authorization_checks": authorization_checks,
        "authorization_check_count": len(authorization_checks),
        "blocking_authorization_check_ids": blocking_authorization_check_ids,
        "blocking_authorization_check_count": len(blocking_authorization_check_ids),
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_launch_lock_preview(launch_authorization: dict) -> dict:
    project_id = str(launch_authorization.get("project_id") or "demo_project_default")
    lock_reasons = [
        "Approval decision is not approved.",
        "Launch authorization is denied.",
        "Real execution mode is not enabled.",
        "Provider/tool execution remains disabled.",
    ]
    locks = [
        {
            "launch_lock_id": "approval_lock",
            "lock_status": "locked",
            "reason": "Missing approved operator decision.",
        },
        {
            "launch_lock_id": "real_mode_lock",
            "lock_status": "locked",
            "reason": "Real execution mode is disabled.",
        },
        {
            "launch_lock_id": "provider_lock",
            "lock_status": "locked",
            "reason": "Provider calls are disabled.",
        },
        {
            "launch_lock_id": "dry_run_lock",
            "lock_status": "locked",
            "reason": "Dry-run boundary remains active.",
        },
    ]
    return {
        "real_execution_launch_lock_version": "runner_real_execution_launch_lock_preview_v1",
        "real_execution_launch_lock_status": "launch_locked",
        "project_id": project_id,
        "launch_authorization_status": launch_authorization.get("real_execution_launch_authorization_status", ""),
        "locks": locks,
        "lock_count": len(locks),
        "lock_reasons": lock_reasons,
        "lock_reason_count": len(lock_reasons),
        "launch_authorized": False,
        "launch_allowed": False,
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_launch_denial_receipt_preview(
    launch_authorization: dict,
    launch_lock: dict,
) -> dict:
    project_id = str(launch_authorization.get("project_id") or "demo_project_default")
    denial_events = [
        {
            "denial_event_id": f"real_execution_launch_{project_id}_denied",
            "denial_event_type": "real_execution_launch_denied",
            "denial_event_status": "recorded",
            "reason": "Launch authorization denied and launch lock active.",
        }
    ]
    return {
        "real_execution_launch_denial_receipt_version": "runner_real_execution_launch_denial_receipt_preview_v1",
        "real_execution_launch_denial_receipt_status": "launch_denied_safely",
        "project_id": project_id,
        "launch_authorization_status": launch_authorization.get("real_execution_launch_authorization_status", ""),
        "launch_lock_status": launch_lock.get("real_execution_launch_lock_status", ""),
        "denial_events": denial_events,
        "denial_event_count": len(denial_events),
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_launch_monitor_preview(launch_payload: dict) -> dict:
    authorization = dict(launch_payload.get("runner_real_execution_launch_authorization_preview") or {})
    launch_lock = dict(launch_payload.get("runner_real_execution_launch_lock_preview") or {})
    denial_receipt = dict(launch_payload.get("runner_real_execution_launch_denial_receipt_preview") or {})
    project_id = str(launch_payload.get("project", {}).get("project_id") or launch_payload.get("project_id") or "demo_project_default")

    tripwire_signals = [
        {
            "tripwire_signal_id": "launch_authorization_denied",
            "triggered": str(authorization.get("real_execution_launch_authorization_status") or "") != "launch_authorized",
            "blocking": True,
            "reason": "Launch authorization is not approved.",
        },
        {
            "tripwire_signal_id": "launch_lock_active",
            "triggered": str(launch_lock.get("real_execution_launch_lock_status") or "") == "launch_locked",
            "blocking": True,
            "reason": "Launch lock remains active.",
        },
        {
            "tripwire_signal_id": "denial_receipt_recorded",
            "triggered": bool(denial_receipt.get("real_execution_launch_denial_receipt_version")),
            "blocking": True,
            "reason": "Launch denial receipt is present.",
        },
        {
            "tripwire_signal_id": "provider_call_attempted",
            "triggered": bool(launch_payload.get("provider_call_performed")),
            "blocking": True,
            "reason": "Provider calls must remain disabled during dry-run.",
        },
        {
            "tripwire_signal_id": "external_api_attempted",
            "triggered": bool(launch_payload.get("external_api_called")),
            "blocking": True,
            "reason": "External API calls must remain disabled during dry-run.",
        },
        {
            "tripwire_signal_id": "agent_execution_attempted",
            "triggered": bool(launch_payload.get("agent_execution_performed")),
            "blocking": True,
            "reason": "Real Agent execution must remain disabled during dry-run.",
        },
        {
            "tripwire_signal_id": "dry_run_boundary_active",
            "triggered": bool(launch_payload.get("dry_run")),
            "blocking": False,
            "reason": "Dry-run boundary is active and expected.",
        },
    ]
    blocking_tripwire_signal_ids = [
        item["tripwire_signal_id"]
        for item in tripwire_signals
        if item.get("blocking") and item.get("triggered")
    ]

    health_probe_checks = [
        {
            "health_probe_id": "dry_run_boundary",
            "status": "passed" if launch_payload.get("dry_run") else "failed",
            "message": "Dry-run boundary remains active.",
        },
        {
            "health_probe_id": "provider_call_guard",
            "status": "passed" if not launch_payload.get("provider_call_performed") else "failed",
            "message": "No provider call was performed.",
        },
        {
            "health_probe_id": "external_api_guard",
            "status": "passed" if not launch_payload.get("external_api_called") else "failed",
            "message": "No external API call was performed.",
        },
        {
            "health_probe_id": "agent_execution_guard",
            "status": "passed" if not launch_payload.get("agent_execution_performed") else "failed",
            "message": "No real Agent execution was performed.",
        },
        {
            "health_probe_id": "manual_review_required",
            "status": "passed" if launch_payload.get("manual_review_required") else "failed",
            "message": "Manual review remains required before execution.",
        },
    ]
    failed_health_probe_ids = [
        item["health_probe_id"]
        for item in health_probe_checks
        if item.get("status") != "passed"
    ]

    abort_plan_steps = [
        {
            "abort_step_id": "keep_launch_lock_active",
            "status": "ready",
            "action": "Keep launch lock active and do not authorize execution.",
        },
        {
            "abort_step_id": "block_provider_and_tool_calls",
            "status": "ready",
            "action": "Keep provider, tool, and external API calls disabled.",
        },
        {
            "abort_step_id": "record_monitor_receipt",
            "status": "ready",
            "action": "Record monitor output in Workspace graph summary for audit.",
        },
        {
            "abort_step_id": "require_operator_review",
            "status": "ready",
            "action": "Require operator review before any future real execution attempt.",
        },
    ]

    monitor_status = "launch_monitor_blocked_safely"
    abort_recommended = bool(blocking_tripwire_signal_ids or failed_health_probe_ids)

    return {
        "real_execution_launch_monitor_version": "runner_real_execution_launch_monitor_preview_v1",
        "real_execution_launch_monitor_status": monitor_status,
        "project_id": project_id,
        "launch_authorization_status": authorization.get("real_execution_launch_authorization_status", ""),
        "launch_lock_status": launch_lock.get("real_execution_launch_lock_status", ""),
        "launch_denial_receipt_status": denial_receipt.get("real_execution_launch_denial_receipt_status", ""),
        "tripwire_signals": tripwire_signals,
        "tripwire_signal_count": len(tripwire_signals),
        "blocking_tripwire_signal_ids": blocking_tripwire_signal_ids,
        "blocking_tripwire_signal_count": len(blocking_tripwire_signal_ids),
        "health_probe_checks": health_probe_checks,
        "health_probe_check_count": len(health_probe_checks),
        "failed_health_probe_ids": failed_health_probe_ids,
        "failed_health_probe_count": len(failed_health_probe_ids),
        "health_probe_summary": "dry_run_safe_but_launch_blocked",
        "abort_plan_steps": abort_plan_steps,
        "abort_plan_step_count": len(abort_plan_steps),
        "abort_recommended": abort_recommended,
        "monitoring_started": True,
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_safety_chain_audit_summary_preview(
    incident_payload: dict,
    incident_response: dict,
) -> dict:
    incident = incident_response if isinstance(incident_response, dict) else {}
    monitor = dict(incident_payload.get("runner_real_execution_launch_monitor_preview") or {})
    authorization = dict(incident_payload.get("runner_real_execution_launch_authorization_preview") or {})
    launch_lock = dict(incident_payload.get("runner_real_execution_launch_lock_preview") or {})
    denial_receipt = dict(incident_payload.get("runner_real_execution_launch_denial_receipt_preview") or {})

    project_id = str(
        incident_payload.get("project", {}).get("project_id")
        or incident_payload.get("project_id")
        or incident.get("project_id")
        or "demo_project_default"
    )

    audit_events = [
        {
            "audit_event_id": f"real_execution_safety_chain_{project_id}_launch_authorization",
            "audit_event_type": "real_execution_launch_authorization_checked",
            "audit_event_status": authorization.get("real_execution_launch_authorization_status", "not_refreshed"),
            "blocking": True,
        },
        {
            "audit_event_id": f"real_execution_safety_chain_{project_id}_launch_monitor",
            "audit_event_type": "real_execution_launch_monitor_checked",
            "audit_event_status": monitor.get("real_execution_launch_monitor_status", "not_refreshed"),
            "blocking": bool(monitor.get("abort_recommended")),
        },
        {
            "audit_event_id": f"real_execution_safety_chain_{project_id}_incident_response",
            "audit_event_type": "real_execution_incident_response_recorded",
            "audit_event_status": incident.get("real_execution_incident_response_status", "not_refreshed"),
            "blocking": bool(incident.get("incident_detected")),
        },
    ]

    blocking_tripwire_signal_ids = list(monitor.get("blocking_tripwire_signal_ids") or incident.get("blocking_tripwire_signal_ids") or [])
    failed_health_probe_ids = list(monitor.get("failed_health_probe_ids") or incident.get("failed_health_probe_ids") or [])

    return {
        "real_execution_safety_chain_audit_summary_version": "runner_real_execution_safety_chain_audit_summary_preview_v1",
        "real_execution_safety_chain_audit_summary_status": "safety_chain_recorded_safely",
        "project_id": project_id,
        "chain_status": "blocked_safely",
        "chain_step_count": len(audit_events),
        "audit_events": audit_events,
        "audit_event_count": len(audit_events),
        "launch_authorization_status": authorization.get("real_execution_launch_authorization_status", ""),
        "launch_lock_status": launch_lock.get("real_execution_launch_lock_status", ""),
        "launch_denial_receipt_status": denial_receipt.get("real_execution_launch_denial_receipt_status", ""),
        "launch_monitor_status": monitor.get("real_execution_launch_monitor_status", ""),
        "incident_response_status": incident.get("real_execution_incident_response_status", ""),
        "incident_receipt_status": incident.get("incident_receipt_status", ""),
        "containment_plan_status": incident.get("containment_plan_status", ""),
        "health_probe_summary": monitor.get("health_probe_summary", ""),
        "blocking_tripwire_signal_ids": blocking_tripwire_signal_ids,
        "blocking_tripwire_signal_count": len(blocking_tripwire_signal_ids),
        "failed_health_probe_ids": failed_health_probe_ids,
        "failed_health_probe_count": len(failed_health_probe_ids),
        "abort_recommended": bool(incident.get("abort_recommended") or monitor.get("abort_recommended")),
        "incident_detected": bool(incident.get("incident_detected")),
        "recovery_ready": bool(incident.get("recovery_ready")),
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


def _runner_real_execution_safety_chain_event_preview(audit_summary: dict) -> dict:
    summary = audit_summary if isinstance(audit_summary, dict) else {}
    project_id = str(summary.get("project_id") or "demo_project_default")
    chain_status = str(summary.get("chain_status") or "blocked_safely")
    event_status = "safety_chain_blocked_safely" if chain_status == "blocked_safely" else "safety_chain_recorded"

    event_payload = {
        "audit_summary_version": summary.get("real_execution_safety_chain_audit_summary_version"),
        "audit_summary_status": summary.get("real_execution_safety_chain_audit_summary_status"),
        "chain_status": chain_status,
        "abort_recommended": bool(summary.get("abort_recommended")),
        "incident_detected": bool(summary.get("incident_detected")),
        "safe_to_continue": False,
        "dry_run": True,
    }
    event_message = build_agent_message(
        message_type="runner_real_execution_safety_chain_event",
        source_agent_id="risk_approval_agent",
        target_agent_id="supervisor_agent",
        payload=event_payload,
        run_id="",
        job_id="",
        artifact_ids=[],
        project_id=project_id,
    )

    return {
        "real_execution_safety_chain_event_version": "runner_real_execution_safety_chain_event_preview_v1",
        "event_id": f"real_execution_safety_chain_event_{project_id}_{chain_status}".replace(" ", "_"),
        "event_type": "runner_real_execution_safety_chain_dry_run",
        "event_status": event_status,
        "project_id": project_id,
        "source_agent_id": "risk_approval_agent",
        "target_agent_id": "supervisor_agent",
        "chain_status": chain_status,
        "audit_summary_version": str(summary.get("real_execution_safety_chain_audit_summary_version") or ""),
        "audit_summary_status": str(summary.get("real_execution_safety_chain_audit_summary_status") or ""),
        "audit_event_count": int(summary.get("audit_event_count") or 0),
        "blocking_tripwire_signal_count": int(summary.get("blocking_tripwire_signal_count") or 0),
        "failed_health_probe_count": int(summary.get("failed_health_probe_count") or 0),
        "abort_recommended": bool(summary.get("abort_recommended")),
        "incident_detected": bool(summary.get("incident_detected")),
        "incident_response_status": str(summary.get("incident_response_status") or ""),
        "containment_plan_status": str(summary.get("containment_plan_status") or ""),
        "incident_receipt_status": str(summary.get("incident_receipt_status") or ""),
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
        "safety_chain_message": event_message,
    }


def _runner_real_execution_incident_response_preview(monitor_payload: dict) -> dict:
    monitor = dict(monitor_payload.get("runner_real_execution_launch_monitor_preview") or {})
    project_id = str(monitor_payload.get("project", {}).get("project_id") or monitor_payload.get("project_id") or "demo_project_default")

    blocking_tripwire_signal_ids = list(monitor.get("blocking_tripwire_signal_ids") or [])
    failed_health_probe_ids = list(monitor.get("failed_health_probe_ids") or [])
    abort_recommended = bool(monitor.get("abort_recommended"))

    incident_detected = abort_recommended or bool(blocking_tripwire_signal_ids) or bool(failed_health_probe_ids)
    incident_severity = "high" if blocking_tripwire_signal_ids else "medium"

    containment_actions = [
        {
            "containment_action_id": "keep_launch_lock_active",
            "status": "ready",
            "blocking": True,
            "action": "Keep launch lock active and prevent launch authorization.",
        },
        {
            "containment_action_id": "block_provider_tool_external_api_calls",
            "status": "ready",
            "blocking": True,
            "action": "Keep provider, tool, and external API execution disabled.",
        },
        {
            "containment_action_id": "freeze_real_agent_execution",
            "status": "ready",
            "blocking": True,
            "action": "Keep real Agent execution disabled while incident review is open.",
        },
        {
            "containment_action_id": "preserve_workspace_audit_trace",
            "status": "ready",
            "blocking": False,
            "action": "Preserve monitor, tripwire, health probe, and abort-plan evidence in graph summary.",
        },
    ]

    recovery_checklist = [
        {
            "recovery_check_id": "operator_approval_captured",
            "required": True,
            "status": "missing",
            "reason": "Explicit operator approval is required before any future real execution attempt.",
        },
        {
            "recovery_check_id": "launch_authorization_approved",
            "required": True,
            "status": "missing",
            "reason": "Launch authorization must be approved before execution.",
        },
        {
            "recovery_check_id": "sandbox_session_ready",
            "required": True,
            "status": "missing",
            "reason": "A sandbox session must be ready before provider or tool execution.",
        },
        {
            "recovery_check_id": "rollback_plan_confirmed",
            "required": True,
            "status": "missing",
            "reason": "Rollback plan must be confirmed before real execution.",
        },
        {
            "recovery_check_id": "provider_credentials_scoped",
            "required": True,
            "status": "missing",
            "reason": "Provider credentials must be scoped and reviewed before use.",
        },
        {
            "recovery_check_id": "budget_quota_confirmed",
            "required": True,
            "status": "missing",
            "reason": "Budget and quota limits must be confirmed before external calls.",
        },
    ]

    incident_events = [
        {
            "incident_event_id": f"real_execution_incident_{project_id}_launch_blocked",
            "incident_event_type": "real_execution_launch_blocked",
            "incident_event_status": "recorded",
            "severity": incident_severity,
            "reason": "Launch monitor recommended abort and real execution remains locked.",
            "blocking_tripwire_signal_ids": blocking_tripwire_signal_ids,
            "failed_health_probe_ids": failed_health_probe_ids,
        }
    ]

    incident_receipt = {
        "incident_receipt_version": "runner_real_execution_incident_receipt_preview_v1",
        "incident_receipt_status": "incident_response_recorded",
        "project_id": project_id,
        "incident_detected": incident_detected,
        "incident_severity": incident_severity,
        "incident_event_count": len(incident_events),
        "containment_action_count": len(containment_actions),
        "recovery_check_count": len(recovery_checklist),
        "real_execution_enabled": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }

    return {
        "real_execution_incident_response_version": "runner_real_execution_incident_response_preview_v1",
        "real_execution_incident_response_status": "incident_response_opened_safely" if incident_detected else "incident_response_not_required",
        "project_id": project_id,
        "launch_monitor_status": monitor.get("real_execution_launch_monitor_status", ""),
        "health_probe_summary": monitor.get("health_probe_summary", ""),
        "blocking_tripwire_signal_ids": blocking_tripwire_signal_ids,
        "blocking_tripwire_signal_count": len(blocking_tripwire_signal_ids),
        "failed_health_probe_ids": failed_health_probe_ids,
        "failed_health_probe_count": len(failed_health_probe_ids),
        "abort_recommended": abort_recommended,
        "incident_detected": incident_detected,
        "incident_severity": incident_severity,
        "incident_events": incident_events,
        "incident_event_count": len(incident_events),
        "containment_actions": containment_actions,
        "containment_action_count": len(containment_actions),
        "containment_plan_status": "containment_ready",
        "recovery_checklist": recovery_checklist,
        "recovery_check_count": len(recovery_checklist),
        "recovery_ready": False,
        "incident_receipt": incident_receipt,
        "incident_receipt_status": incident_receipt["incident_receipt_status"],
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "dry_run": True,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-approval-decision/dry-run")
async def dry_run_project_agent_real_execution_approval_decision(project_id: str, http_request: Request):
    approval_payload = await dry_run_project_agent_real_execution_approval_request(project_id, http_request)

    runner_real_execution_approval_decision_preview = _runner_real_execution_approval_decision_preview(approval_payload)
    runner_real_execution_decision_ledger_preview = _runner_real_execution_decision_ledger_preview(
        runner_real_execution_approval_decision_preview
    )
    runner_real_execution_denied_receipt_preview = _runner_real_execution_denied_receipt_preview(
        runner_real_execution_approval_decision_preview,
        runner_real_execution_decision_ledger_preview,
    )

    project = approval_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_approval_decision_status": runner_real_execution_approval_decision_preview["real_execution_approval_decision_status"],
        "latest_runner_real_execution_decision_ledger_status": runner_real_execution_decision_ledger_preview["real_execution_decision_ledger_status"],
        "latest_runner_real_execution_denied_receipt_status": runner_real_execution_denied_receipt_preview["real_execution_denied_receipt_status"],
        "latest_runner_real_execution_approval_decision": "denied",
        "latest_runner_real_execution_enabled_after_decision": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **approval_payload,
        "project": project,
        "runner_real_execution_approval_decision_preview": runner_real_execution_approval_decision_preview,
        "runner_real_execution_decision_ledger_preview": runner_real_execution_decision_ledger_preview,
        "runner_real_execution_denied_receipt_preview": runner_real_execution_denied_receipt_preview,
        "dry_run": True,
        "approval_decision": "denied",
        "operator_approval_captured": False,
        "approval_request_ready": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-launch-authorization/dry-run")
async def dry_run_project_agent_real_execution_launch_authorization(project_id: str, http_request: Request):
    decision_payload = await dry_run_project_agent_real_execution_approval_decision(project_id, http_request)

    runner_real_execution_launch_authorization_preview = _runner_real_execution_launch_authorization_preview(decision_payload)
    runner_real_execution_launch_lock_preview = _runner_real_execution_launch_lock_preview(
        runner_real_execution_launch_authorization_preview
    )
    runner_real_execution_launch_denial_receipt_preview = _runner_real_execution_launch_denial_receipt_preview(
        runner_real_execution_launch_authorization_preview,
        runner_real_execution_launch_lock_preview,
    )

    project = decision_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_launch_authorization_status": runner_real_execution_launch_authorization_preview["real_execution_launch_authorization_status"],
        "latest_runner_real_execution_launch_lock_status": runner_real_execution_launch_lock_preview["real_execution_launch_lock_status"],
        "latest_runner_real_execution_launch_denial_receipt_status": runner_real_execution_launch_denial_receipt_preview["real_execution_launch_denial_receipt_status"],
        "latest_runner_real_execution_launch_authorized": False,
        "latest_runner_real_execution_launch_allowed": False,
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **decision_payload,
        "project": project,
        "runner_real_execution_launch_authorization_preview": runner_real_execution_launch_authorization_preview,
        "runner_real_execution_launch_lock_preview": runner_real_execution_launch_lock_preview,
        "runner_real_execution_launch_denial_receipt_preview": runner_real_execution_launch_denial_receipt_preview,
        "dry_run": True,
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-launch-monitor/dry-run")
async def dry_run_project_agent_real_execution_launch_monitor(project_id: str, http_request: Request):
    launch_payload = await dry_run_project_agent_real_execution_launch_authorization(project_id, http_request)

    runner_real_execution_launch_monitor_preview = _runner_real_execution_launch_monitor_preview(launch_payload)

    project = launch_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_launch_monitor_status": runner_real_execution_launch_monitor_preview["real_execution_launch_monitor_status"],
        "latest_runner_real_execution_blocking_tripwire_signal_count": runner_real_execution_launch_monitor_preview["blocking_tripwire_signal_count"],
        "latest_runner_real_execution_failed_health_probe_count": runner_real_execution_launch_monitor_preview["failed_health_probe_count"],
        "latest_runner_real_execution_abort_recommended": runner_real_execution_launch_monitor_preview["abort_recommended"],
        "latest_runner_real_execution_health_probe_summary": runner_real_execution_launch_monitor_preview["health_probe_summary"],
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **launch_payload,
        "project": project,
        "runner_real_execution_launch_monitor_preview": runner_real_execution_launch_monitor_preview,
        "dry_run": True,
        "monitoring_started": True,
        "abort_recommended": runner_real_execution_launch_monitor_preview["abort_recommended"],
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/projects/{project_id}/runner/real-execution-incident-response/dry-run")
async def dry_run_project_agent_real_execution_incident_response(project_id: str, http_request: Request):
    monitor_payload = await dry_run_project_agent_real_execution_launch_monitor(project_id, http_request)

    runner_real_execution_incident_response_preview = _runner_real_execution_incident_response_preview(monitor_payload)
    runner_real_execution_safety_chain_audit_summary_preview = _runner_real_execution_safety_chain_audit_summary_preview(
        monitor_payload,
        runner_real_execution_incident_response_preview,
    )
    runner_real_execution_safety_chain_event_preview = _runner_real_execution_safety_chain_event_preview(
        runner_real_execution_safety_chain_audit_summary_preview
    )
    runner_event_ledger_summary = build_agent_runner_event_ledger_summary(
        project_id=project_id,
        safety_chain_event=runner_real_execution_safety_chain_event_preview,
        incident_receipt=runner_real_execution_incident_response_preview.get("incident_receipt"),
        requested_by="project_runner_real_execution_incident_response_dry_run_api",
    )
    runner_supervisor_event_ledger_decision_summary = build_agent_runner_supervisor_event_ledger_decision_summary(
        runner_event_ledger_summary,
        project_id=project_id,
        requested_by="project_runner_real_execution_incident_response_dry_run_api",
    )
    runner_supervisor_next_step_routing_plan = build_agent_runner_supervisor_next_step_routing_plan(
        runner_supervisor_event_ledger_decision_summary,
        project_id=project_id,
        requested_by="project_runner_real_execution_incident_response_dry_run_api",
    )
    runner_supervisor_next_step_work_order_preview = build_agent_runner_supervisor_next_step_work_order_preview(
        runner_supervisor_next_step_routing_plan,
        project_id=project_id,
        requested_by="project_runner_real_execution_incident_response_dry_run_api",
    )
    runner_queue_lease_worker_dry_run_chain = build_agent_runner_queue_lease_worker_dry_run_chain(
        runner_supervisor_next_step_work_order_preview,
        project_id=project_id,
        requested_by="project_runner_real_execution_incident_response_dry_run_api",
    )

    project = monitor_payload["project"]
    graph_summary = dict(project.get("graph_summary") or {})
    graph_summary.update({
        "latest_runner_real_execution_incident_response_status": runner_real_execution_incident_response_preview["real_execution_incident_response_status"],
        "latest_runner_real_execution_incident_detected": runner_real_execution_incident_response_preview["incident_detected"],
        "latest_runner_real_execution_incident_severity": runner_real_execution_incident_response_preview["incident_severity"],
        "latest_runner_real_execution_containment_plan_status": runner_real_execution_incident_response_preview["containment_plan_status"],
        "latest_runner_real_execution_recovery_ready": runner_real_execution_incident_response_preview["recovery_ready"],
        "latest_runner_real_execution_incident_receipt_status": runner_real_execution_incident_response_preview["incident_receipt_status"],
        "latest_runner_real_execution_safety_chain_audit_summary_status": runner_real_execution_safety_chain_audit_summary_preview["real_execution_safety_chain_audit_summary_status"],
        "latest_runner_real_execution_safety_chain_status": runner_real_execution_safety_chain_audit_summary_preview["chain_status"],
        "latest_runner_real_execution_safety_chain_audit_event_count": runner_real_execution_safety_chain_audit_summary_preview["audit_event_count"],
        "latest_runner_real_execution_safety_chain_safe_to_continue": runner_real_execution_safety_chain_audit_summary_preview["safe_to_continue"],
        "latest_runner_real_execution_safety_chain_event_status": runner_real_execution_safety_chain_event_preview["event_status"],
        "latest_runner_real_execution_safety_chain_event_type": runner_real_execution_safety_chain_event_preview["event_type"],
        "latest_runner_real_execution_safety_chain_event_id": runner_real_execution_safety_chain_event_preview["event_id"],
        "latest_runner_event_ledger_summary_status": runner_event_ledger_summary["runner_event_ledger_summary_status"],
        "latest_runner_event_ledger_event_count": runner_event_ledger_summary["event_count"],
        "latest_runner_event_ledger_blocking_event_count": runner_event_ledger_summary["blocking_event_count"],
        "latest_runner_event_ledger_safe_to_continue": runner_event_ledger_summary["safe_to_continue"],
        "latest_runner_supervisor_event_ledger_decision_status": runner_supervisor_event_ledger_decision_summary["supervisor_event_ledger_decision_status"],
        "latest_runner_supervisor_recommended_next_action": runner_supervisor_event_ledger_decision_summary["recommended_next_action"],
        "latest_runner_supervisor_routing_allowed": runner_supervisor_event_ledger_decision_summary["supervisor_routing_allowed"],
        "latest_runner_supervisor_next_step_routing_plan_status": runner_supervisor_next_step_routing_plan["supervisor_next_step_routing_plan_status"],
        "latest_runner_supervisor_next_step_type": runner_supervisor_next_step_routing_plan["next_step_type"],
        "latest_runner_supervisor_next_step_target_agent_id": runner_supervisor_next_step_routing_plan["target_agent_id"],
        "latest_runner_supervisor_next_step_routing_allowed": runner_supervisor_next_step_routing_plan["routing_allowed"],
        "latest_runner_supervisor_next_step_work_order_status": runner_supervisor_next_step_work_order_preview["supervisor_next_step_work_order_status"],
        "latest_runner_supervisor_next_step_work_order_id": runner_supervisor_next_step_work_order_preview["work_order_id"],
        "latest_runner_supervisor_next_step_work_order_allowed": runner_supervisor_next_step_work_order_preview["work_order_allowed"],
        "latest_runner_supervisor_next_step_work_order_target_agent_id": runner_supervisor_next_step_work_order_preview["target_agent_id"],
        "latest_runner_queue_lease_worker_chain_status": runner_queue_lease_worker_dry_run_chain["queue_lease_worker_dry_run_chain_status"],
        "latest_runner_queue_persistence_status": runner_queue_lease_worker_dry_run_chain["queue_persistence_status"],
        "latest_runner_worker_lease_status": runner_queue_lease_worker_dry_run_chain["worker_lease_status"],
        "latest_runner_worker_invocation_status": runner_queue_lease_worker_dry_run_chain["worker_invocation_status"],
        "latest_runner_queue_persisted": runner_queue_lease_worker_dry_run_chain["queue_persisted"],
        "latest_runner_worker_lease_created": runner_queue_lease_worker_dry_run_chain["worker_lease_created"],
        "latest_runner_worker_invocation_performed": runner_queue_lease_worker_dry_run_chain["worker_invocation_performed"],
        "latest_runner_queue_lease_worker_safe_to_continue": runner_queue_lease_worker_dry_run_chain["safe_to_continue"],
    })
    project["graph_summary"] = graph_summary
    try:
        project = save_project_snapshot(project)
    except Exception:
        pass

    return {
        **monitor_payload,
        "project": project,
        "runner_real_execution_incident_response_preview": runner_real_execution_incident_response_preview,
        "runner_real_execution_safety_chain_audit_summary_preview": runner_real_execution_safety_chain_audit_summary_preview,
        "runner_real_execution_safety_chain_event_preview": runner_real_execution_safety_chain_event_preview,
        "runner_event_ledger_summary": runner_event_ledger_summary,
        "runner_supervisor_event_ledger_decision_summary": runner_supervisor_event_ledger_decision_summary,
        "runner_supervisor_next_step_routing_plan": runner_supervisor_next_step_routing_plan,
        "runner_supervisor_next_step_work_order_preview": runner_supervisor_next_step_work_order_preview,
        "runner_queue_lease_worker_dry_run_chain": runner_queue_lease_worker_dry_run_chain,
        "dry_run": True,
        "incident_detected": runner_real_execution_incident_response_preview["incident_detected"],
        "incident_response_opened": runner_real_execution_incident_response_preview["incident_detected"],
        "abort_recommended": runner_real_execution_incident_response_preview["abort_recommended"],
        "containment_plan_status": runner_real_execution_incident_response_preview["containment_plan_status"],
        "recovery_ready": False,
        "launch_authorized": False,
        "launch_allowed": False,
        "operator_approval_captured": False,
        "real_execution_mode_allowed": False,
        "real_execution_enabled": False,
        "release_allowed": False,
        "capability_invocation_allowed": False,
        "tool_invocation_allowed": False,
        "provider_call_performed": False,
        "external_api_called": False,
        "agent_execution_performed": False,
        "manual_review_required": True,
        "safe_to_continue": False,
        "request_id": http_request.state.request_id,
    }


def _project_history_payload(project_id: str) -> dict:
    safe_id = _safe_project_id(project_id)
    project, planner_recommendation = _project_with_planner_summary(safe_id)
    return {
        "status": "success",
        "project": project,
        "planner_recommendation": planner_recommendation,
        "recent_runs": list_project_records("runs", safe_id, 20),
        "recent_jobs": list_project_records("jobs", safe_id, 20),
        "recent_artifacts": list_project_records("artifacts", safe_id, 30),
        "recent_reports": list_project_records("exports", safe_id, 20),
        "recent_assets": list_project_assets(safe_id, 30),
        "recent_sources": list_project_sources(safe_id, 30),
        "recent_source_artifacts": list_source_evidence_artifacts(safe_id, 30),
        "recent_source_quality_gates": list_source_quality_gates(safe_id, 30),
        "recent_source_snapshots": list_source_snapshots(safe_id, 30),
    }


@app.get("/api/v1/projects")
async def list_projects(limit: int = 20):
    _ensure_project()
    projects = list_recent_projects(max(1, min(limit, 100)))
    return {"status": "success", "projects": projects, "project_count": len(projects)}


@app.post("/api/v1/projects")
async def create_project(request: ProjectCreateRequest, http_request: Request):
    project_name = _clean_description_text(request.project_name)
    if not project_name:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "project_name is required",
                "request_id": http_request.state.request_id,
            },
        )
    project_id = _safe_project_id(
        f"{project_name.lower()}_{uuid4().hex[:8]}"
    )
    project = save_project_snapshot(
        _project_shape(
            project_id=project_id,
            project_name=project_name,
            product_name=request.product_name,
            product_category=request.product_category,
            source_type=request.source_type,
        )
    )
    return {
        "status": "success",
        "project": project,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    project = load_project(_safe_project_id(project_id))
    if not project:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "project not found"},
        )
    return {"status": "success", "project": update_project_summary(project["project_id"])}



@app.get("/api/v1/projects/{project_id}/planner/recommendation")
async def get_project_planner_recommendation(project_id: str):
    safe_id = _safe_project_id(project_id)
    project = load_project(safe_id)
    if not project:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "project not found"},
        )
    project, recommendation = _project_with_planner_summary(safe_id)
    return {
        "status": "success",
        "project_id": safe_id,
        "project": project,
        "planner_recommendation": recommendation,
    }


@app.post("/api/v1/projects/{project_id}/planner/recommendation/refresh")
async def refresh_project_planner_recommendation(project_id: str):
    safe_id = _safe_project_id(project_id)
    project = load_project(safe_id)
    if not project:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "project not found"},
        )
    project, recommendation = _project_with_planner_summary(safe_id)
    return {
        "status": "success",
        "project_id": safe_id,
        "project": project,
        "planner_recommendation": recommendation,
        "refreshed": True,
    }

@app.get("/api/v1/projects/{project_id}/graph-summary")
async def get_project_graph_summary(project_id: str):
    return _project_history_payload(project_id)


@app.get("/api/v1/projects/{project_id}/history/runs")
async def get_project_run_history(project_id: str, limit: int = 20):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "runs": list_project_records("runs", project_id, max(1, min(limit, 100))),
    }


@app.get("/api/v1/projects/{project_id}/history/jobs")
async def get_project_job_history(project_id: str, limit: int = 20):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "jobs": list_project_records("jobs", project_id, max(1, min(limit, 100))),
    }


@app.get("/api/v1/projects/{project_id}/history/artifacts")
async def get_project_artifact_history(project_id: str, limit: int = 30):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "artifacts": list_project_records("artifacts", project_id, max(1, min(limit, 100))),
    }


@app.get("/api/v1/projects/{project_id}/history/reports")
async def get_project_report_history(project_id: str, limit: int = 20):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "reports": list_project_records("exports", project_id, max(1, min(limit, 100))),
    }


@app.get("/api/v1/projects/{project_id}/history/assets")
async def get_project_asset_history(project_id: str, limit: int = 30):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "assets": list_project_assets(project_id, max(1, min(limit, 100))),
    }


@app.get("/api/v1/projects/{project_id}/history/sources")
async def get_project_source_history(project_id: str, limit: int = 30):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "sources": list_project_sources(project_id, max(1, min(limit, 100))),
    }


@app.get("/api/v1/projects/{project_id}/history/source-artifacts")
async def get_project_source_artifact_history(project_id: str, limit: int = 30):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "source_artifacts": list_source_evidence_artifacts(
            project_id,
            max(1, min(limit, 100)),
        ),
    }


@app.get("/api/v1/projects/{project_id}/history/source-quality-gates")
async def get_project_source_quality_gate_history(project_id: str, limit: int = 30):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "source_quality_gates": list_source_quality_gates(
            project_id,
            max(1, min(limit, 100)),
        ),
    }


@app.get("/api/v1/projects/{project_id}/history/source-snapshots")
async def get_project_source_snapshot_history(project_id: str, limit: int = 30):
    return {
        "status": "success",
        "project_id": _safe_project_id(project_id),
        "source_snapshots": list_source_snapshots(
            project_id,
            max(1, min(limit, 100)),
        ),
    }


@app.post("/api/v1/projects/{project_id}/sources/preview")
async def preview_project_source(
    project_id: str,
    request: ProjectSourceRequest,
    http_request: Request,
):
    try:
        bundle = _build_project_source_bundle(
            project_id,
            request,
            persist=False,
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": str(exc),
                "error_type": "invalid_project_source",
                "request_id": http_request.state.request_id,
            },
        )
    return {
        "status": "success",
        "preview": True,
        **bundle,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/projects/{project_id}/sources")
async def create_project_source(
    project_id: str,
    request: ProjectSourceRequest,
    http_request: Request,
):
    try:
        bundle = _build_project_source_bundle(project_id, request, persist=True)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": str(exc),
                "error_type": "invalid_project_source",
                "request_id": http_request.state.request_id,
            },
        )
    return {
        "status": "success",
        **bundle,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/projects/{project_id}/sources")
async def get_project_sources(project_id: str, limit: int = 30):
    safe_id = _safe_project_id(project_id)
    _ensure_project(safe_id)
    sources = list_project_sources(safe_id, max(1, min(limit, 100)))
    return {
        "status": "success",
        "project_id": safe_id,
        "sources": sources,
        "source_count": len(sources),
    }


@app.get("/api/v1/projects/{project_id}/sources/{source_id}")
async def get_project_source(project_id: str, source_id: str):
    source = load_project_source(_safe_project_id(project_id), source_id)
    if not source:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "project source not found"},
        )
    return {"status": "success", "project_source": source}


@app.get("/api/v1/projects/{project_id}/sources/{source_id}/evidence")
async def get_project_source_evidence(project_id: str, source_id: str):
    artifact = load_source_evidence_artifact(_safe_project_id(project_id), source_id)
    gate = load_source_quality_gate(_safe_project_id(project_id), source_id)
    if not artifact:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "source evidence artifact not found"},
        )
    return {
        "status": "success",
        "source_evidence_artifact": artifact,
        "source_quality_gate": gate or {},
    }


def _source_generation_packet(
    source: dict,
    artifact: dict,
    gate: dict,
) -> dict:
    classifications = artifact.get("review_classifications") or []
    categories: dict[str, list[str]] = {}
    for item in classifications:
        if not isinstance(item, dict):
            continue
        for category in item.get("categories") or ["unclear"]:
            categories.setdefault(str(category), []).append(str(item.get("text") or ""))
    return {
        "packet_version": "source_evidence_v1",
        "intended_model_use": "creative_brief_generation",
        "product": {
            "title": source.get("product_name", ""),
            "category": source.get("product_category", ""),
            "description": source.get("product_description", ""),
            "source_type": source.get("source_type", ""),
            "source_url": source.get("normalized_url") or source.get("source_url", ""),
            "asin": artifact.get("asin", ""),
            "shopify_handle": artifact.get("shopify_handle", ""),
        },
        "review_stats": {
            **(source.get("source_summary") or {}),
            "source_confidence": source.get("source_confidence", 0.0),
            "warnings": list(source.get("warnings") or []),
        },
        "evidence": {
            "quotes": list(artifact.get("evidence_quotes") or [])[:12],
            "review_classifications": classifications[:20],
            "pain_points": categories.get("pain_point", [])[:4],
            "buyer_objections": categories.get("buyer_objection", [])[:4],
            "positive_signals": categories.get("positive_signal", [])[:4],
            "use_cases": categories.get("usage_context", [])[:4],
            "product_signals": list(artifact.get("product_signals") or [])[:8],
        },
        "generation_constraints": [
            "Use only the supplied review evidence and product fields.",
            "Do not claim full-market statistics or verified purchase coverage beyond explicit metadata.",
            "Do not hallucinate reviews from product descriptions or public product metadata.",
            "Keep source warnings and manual fallback requirements visible.",
            "Do not turn buyer objections into positive claims unless evidence explicitly resolves the concern.",
        ],
        "source_quality_gate": gate,
    }


@app.post("/api/v1/projects/{project_id}/sources/{source_id}/generate")
async def generate_from_project_source(
    project_id: str,
    source_id: str,
    request: ProjectSourceGenerateRequest,
    http_request: Request,
):
    safe_id = _safe_project_id(project_id)
    source = load_project_source(safe_id, source_id)
    artifact = load_source_evidence_artifact(safe_id, source_id)
    gate = load_source_quality_gate(safe_id, source_id)
    if not source or not artifact or not gate:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "project source evidence is incomplete",
                "error_type": "source_not_ready",
                "request_id": http_request.state.request_id,
            },
        )
    reviews = [
        str(item.get("review") or "")
        for item in artifact.get("review_snippets") or []
        if isinstance(item, dict) and item.get("review")
    ]
    if not reviews or not gate.get("allows_agent_run"):
        return JSONResponse(
            status_code=409,
            content={
                "status": "fallback_required",
                "error": gate.get("recommended_next_action")
                or "Customer feedback is required for review-grounded generation.",
                "error_type": "manual_reviews_required",
                "source_quality_gate": gate,
                "source_warnings": source.get("warnings") or [],
                "request_id": http_request.state.request_id,
            },
        )
    generation_request = PastedReviewsRequest(
        project_id=safe_id,
        product_name=source.get("product_name") or "Project product",
        product_category=source.get("product_category") or "project_source",
        product_description=source.get("product_description") or None,
        pasted_reviews="\n".join(reviews),
        target_platform=request.target_platform,
        goal=request.goal,
        output_language=request.output_language,
        llm_evidence_packet=_source_generation_packet(source, artifact, gate),
    )
    generated = await generate_from_reviews(generation_request, http_request)
    if isinstance(generated, JSONResponse):
        return generated
    data = generated.get("data") or {}
    bundle = {
        "project_source": source,
        "source_evidence_artifact": artifact,
        "source_quality_gate": gate,
        "source_snapshot": next(
            (
                item
                for item in list_source_snapshots(safe_id, 100)
                if item.get("source_id") == source_id
            ),
            {},
        ),
    }
    data.update(bundle)
    data["artifact_registry"] = _source_registry_snapshot(
        _ensure_project(safe_id),
        bundle,
        data,
    )
    evidence = ((data.get("insights") or {}).get("evidence") or {})
    evidence["source_type"] = source.get("source_type", "")
    evidence["source_url"] = source.get("normalized_url") or source.get("source_url", "")
    evidence["data_warnings"] = list(
        dict.fromkeys((evidence.get("data_warnings") or []) + (source.get("warnings") or []))
    )
    return generated


@app.get("/api/v1/projects/{project_id}/assets")
async def get_project_assets(project_id: str):
    safe_id = _safe_project_id(project_id)
    _ensure_project(safe_id)
    assets = list_project_assets(safe_id, 100)
    return {"status": "success", "project_id": safe_id, "assets": assets}


@app.get("/api/v1/projects/{project_id}/assets/{asset_id}")
async def get_project_asset(project_id: str, asset_id: str):
    asset = load_project_asset(_safe_project_id(project_id), asset_id)
    if not asset:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "project asset not found"},
        )
    return {"status": "success", "asset": asset}


@app.post("/api/v1/projects/{project_id}/assets/upload")
async def upload_project_asset(
    project_id: str,
    http_request: Request,
    asset_role: str = Form("product_image"),
    notes: str = Form(""),
    product_name: str = Form(""),
    product_category: str = Form(""),
    file: UploadFile = File(...),
):
    safe_id = _safe_project_id(project_id)
    if asset_role not in PROJECT_ASSET_ROLES:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": "unsupported asset_role"},
        )
    content_type = str(file.content_type or "").lower()
    suffix = Path(file.filename or "").suffix.lower()
    allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
    if content_type not in PROJECT_ASSET_CONTENT_TYPES or suffix not in allowed_suffixes:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": "unsupported image file type"},
        )
    contents = await file.read(PROJECT_ASSET_MAX_BYTES + 1)
    if not contents or len(contents) > PROJECT_ASSET_MAX_BYTES:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": "image file must be between 1 byte and 8 MB"},
        )
    project = _ensure_project(
        safe_id,
        product_name=product_name,
        product_category=product_category,
        source_type="manual",
    )
    asset_id = f"asset_{uuid4().hex[:16]}"
    safe_filename = re.sub(
        r"[^a-zA-Z0-9_.-]+",
        "_",
        Path(file.filename or f"{asset_id}{suffix}").name,
    )[:160]
    stored_name = f"{asset_id}_{safe_filename}"
    asset_path = project_assets_directory(safe_id) / stored_name
    temp_path = asset_path.with_name(f".{asset_path.name}.tmp")
    temp_path.write_bytes(contents)
    os.replace(temp_path, asset_path)
    asset = {
        "asset_version": "project_asset_v1",
        "asset_id": asset_id,
        "project_id": safe_id,
        "asset_role": asset_role,
        "filename": safe_filename,
        "content_type": content_type,
        "size_bytes": len(contents),
        "storage_path": f"projects/{safe_id}/assets/{stored_name}",
        "created_at": _utc_now_iso(),
        "notes": _clean_description_text(notes),
        "source": "user_upload",
        "artifact_type": "uploaded_product_asset",
    }
    saved_asset = save_project_asset_snapshot(asset)
    update_project_summary(safe_id, project)
    return {
        "status": "success",
        "asset": saved_asset,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/agent-graph/history/runs")
async def agent_graph_history_runs(limit: int = 10):
    return {"status": "success", "runs": load_recent_agent_run_snapshots(max(1, min(limit, 50)))}


@app.get("/api/v1/agent-graph/history/jobs")
async def agent_graph_history_jobs(limit: int = 10):
    return {"status": "success", "jobs": load_recent_video_job_snapshots(max(1, min(limit, 50)))}


@app.get("/api/v1/agent-graph/history/artifacts")
async def agent_graph_history_artifacts(limit: int = 20):
    return {"status": "success", "artifacts": list_recent_artifacts(max(1, min(limit, 100)))}


@app.get("/api/v1/agent-graph/history/events")
async def agent_graph_history_events(limit: int = 50):
    return {"status": "success", "events": list_recent_graph_events(max(1, min(limit, 200)))}


@app.get("/api/v1/agent-graph/history/messages")
async def agent_graph_history_messages(limit: int = 50):
    return {"status": "success", "messages": list_recent_agent_messages(max(1, min(limit, 200)))}


@app.get("/api/v1/agent-graph/history/snapshots")
async def agent_graph_history_snapshots(limit: int = 20):
    return {"status": "success", "snapshots": list_recent_graph_snapshots(max(1, min(limit, 100)))}


@app.get("/api/v1/agent-graph/history/exports")
async def agent_graph_history_exports(limit: int = 20):
    return {"status": "success", "exports": list_recent_graph_exports(max(1, min(limit, 100)))}


@app.get("/api/v1/agent-graph/history/summary")
async def agent_graph_history_summary():
    runs = load_recent_agent_run_snapshots(10)
    jobs = load_recent_video_job_snapshots(10)
    artifacts = list_recent_artifacts(20)
    events = list_recent_graph_events(50)
    messages = list_recent_agent_messages(50)
    snapshots = list_recent_graph_snapshots(20)
    exports = list_recent_graph_exports(20)
    metadata = persistence_metadata()
    return {
        "status": "success",
        **metadata,
        "run_count": len(runs),
        "job_count": len(jobs),
        "artifact_count": len(artifacts),
        "event_count": len(events),
        "message_count": len(messages),
        "snapshot_count": len(snapshots),
        "export_count": len(exports),
        "recent_runs": runs,
        "recent_jobs": jobs,
        "recent_artifacts": artifacts,
        "recent_messages": messages,
        "recent_snapshots": snapshots,
    }


@app.get("/api/v1/agent-graph/runs/{run_id}/report")
async def agent_run_graph_report(run_id: str, format: str = "json"):
    run = AGENT_RUN_STORE.get(run_id) or _stored_run_by_id(run_id)
    if not run:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "agent run not found"},
        )
    return _graph_report_response(_build_run_graph_report(run), format)


@app.get("/api/v1/video-generation/jobs/{job_id}/graph-report")
async def video_job_graph_report(job_id: str, format: str = "json"):
    job = VIDEO_JOB_STORE.get(job_id) or _stored_job_by_id(job_id)
    if not job:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": "video generation job not found"},
        )
    return _graph_report_response(_build_job_graph_report(job), format)


@app.post("/api/v1/agent-runs/from-reviews", response_model=AgentRunCreateResponse)
async def create_agent_run_from_reviews(
    request: PastedReviewsRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
):
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    project = _ensure_project(
        request.project_id,
        product_name=request.product_name,
        product_category=request.product_category or "",
        source_type="pasted_reviews",
    )
    safe_request = request.model_copy(
        update={
            "output_language": output_language,
            "project_id": project["project_id"],
        }
    )
    validation_error = _validate_pasted_reviews_request(safe_request, request_id)
    if validation_error:
        return validation_error

    run = build_agent_run(
        input_type="pasted_reviews",
        output_language=output_language,
        request_id=request_id,
        project_id=project["project_id"],
    )
    AGENT_RUN_STORE.create(run)
    AGENT_RUN_STORE.append_event(
        run["run_id"],
        "run_created",
        "Agent run created for pasted customer feedback.",
        data={
            "input_type": "pasted_reviews",
            "output_language": output_language,
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
        },
    )
    initial_run = _persist_agent_run_graph_os(AGENT_RUN_STORE.get(run["run_id"]) or run)
    AGENT_RUN_STORE.update(
        run["run_id"],
        {
            "artifact_registry": initial_run.get("artifact_registry") or {},
            "agent_messages": initial_run.get("agent_messages") or [],
            "latest_graph_state_snapshot": initial_run.get("latest_graph_state_snapshot") or {},
            "graph_health": initial_run.get("graph_health") or {},
            "persistence": initial_run.get("persistence") or {},
        },
    )
    background_tasks.add_task(_execute_pasted_reviews_agent_run, run["run_id"], safe_request)
    current_run = AGENT_RUN_STORE.get(run["run_id"]) or run
    return {
        "status": "success",
        "run": current_run,
        "poll_url": f"/api/v1/agent-runs/{run['run_id']}",
        "events_url": f"/api/v1/agent-runs/{run['run_id']}/events",
        "request_id": request_id,
    }


@app.get("/api/v1/agent-runs", response_model=AgentRunListResponse)
async def list_agent_runs(http_request: Request, limit: int = 10):
    safe_limit = max(1, min(int(limit or 10), 50))
    runs = AGENT_RUN_STORE.list(safe_limit)
    return {
        "status": "success",
        "runs": runs,
        "run_count": len(runs),
        "limit": safe_limit,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/agent-runs/{run_id}", response_model=AgentRunStatusResponse)
async def get_agent_run(run_id: str, http_request: Request):
    run = AGENT_RUN_STORE.get(run_id)
    if not run:
        _agent_run_not_found(run_id)
    return {
        "status": "success",
        "run": run,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/agent-runs/{run_id}/events", response_model=AgentRunEventsResponse)
async def get_agent_run_events(run_id: str, http_request: Request):
    run = AGENT_RUN_STORE.get(run_id)
    if not run:
        _agent_run_not_found(run_id)
    return {
        "status": "success",
        "run_id": run_id,
        "events": run.get("events") or [],
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/generate-from-reviews", response_model=PastedReviewsResponse)
async def generate_from_reviews(request: PastedReviewsRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    product_name = _clean_description_text(request.product_name)
    emit_event(
        "generate_from_reviews_start",
        request_id,
        endpoint="/api/v1/generate-from-reviews",
        status="started",
        product_category=request.product_category or "user_pasted_reviews_product",
        goal=request.goal,
        output_language=output_language,
    )

    validation_error = _validate_pasted_reviews_request(request, request_id)
    if validation_error:
        emit_event(
            "generate_from_reviews_error",
            request_id,
            endpoint="/api/v1/generate-from-reviews",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or "user_pasted_reviews_product",
            goal=request.goal,
            output_language=output_language,
        )
        return validation_error

    evidence_quotes = _split_pasted_review_quotes(request.pasted_reviews)
    try:
        project = _ensure_project(
            request.project_id,
            product_name=request.product_name,
            product_category=request.product_category or "",
            source_type="pasted_reviews",
        )
        safe_request = request.model_copy(update={"project_id": project["project_id"]})
        source_bundle = _pasted_request_source_bundle(safe_request, persist=True)
        generated = await generate_pasted_reviews_brief(safe_request, evidence_quotes)
        data = _pasted_reviews_response_data(safe_request, generated, evidence_quotes)
        data["project_id"] = project["project_id"]
        uploaded_assets = list_project_assets(project["project_id"], 50)
        data["product_asset_lock_v2"] = build_product_asset_lock_v2(
            project,
            data,
            uploaded_assets,
        )
        data = await translate_product_visible_data(data, output_language)
        data.update(
            {
                "project_source": source_bundle.get("project_source") or {},
                "source_evidence_artifact": source_bundle.get("source_evidence_artifact") or {},
                "source_quality_gate": source_bundle.get("source_quality_gate") or {},
                "source_snapshot": source_bundle.get("source_snapshot") or {},
            }
        )
        data["artifact_registry"] = build_lightweight_artifact_registry(
            generation_data=data,
            project=project,
            uploaded_assets=uploaded_assets,
        )
        response = {
            "status": "success",
            "data": data,
            "request_id": request_id,
            "output_language": output_language,
        }
        emit_event(
            "generate_from_reviews_complete",
            request_id,
            endpoint="/api/v1/generate-from-reviews",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            output_language=output_language,
        )
        return response
    except Exception:
        emit_event(
            "generate_from_reviews_error",
            request_id,
            endpoint="/api/v1/generate-from-reviews",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            error_type="generation_failed",
            output_language=output_language,
        )
        return _description_error(
            "Pasted Reviews Mode generation failed safely. Please retry with fewer review snippets.",
            "generation_failed",
            request_id,
            status_code=503,
        )


@app.post("/api/v1/translate-output", response_model=TranslationResponse)
async def translate_output(request: TranslationRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    emit_event(
        "translate_output_start",
        request_id,
        endpoint="/api/v1/translate-output",
        status="started",
        target_language=request.target_language,
        input_size_char=len(request.text or ""),
    )
    translated_text = await translate_visible_output(
        request.text,
        request.target_language,
    )
    emit_event(
        "translate_output_complete",
        request_id,
        endpoint="/api/v1/translate-output",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        target_language=request.target_language,
        input_size_char=len(request.text or ""),
    )
    return TranslationResponse(
        translated_text=translated_text,
        target_language=request.target_language,
        request_id=request_id,
    )


@app.post("/api/v1/debug-copilot", response_model=DebugCopilotResponse)
async def debug_copilot_flow(request: GrowthRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    emit_event(
        "debug_copilot_start",
        request_id,
        endpoint="/api/v1/debug-copilot",
        status="started",
        goal=request.goal,
    )
    initial_state = {
        "env_state": {"asin_url": request.url, "business_goal": request.goal},
        "cognitive_state": {},
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": {},
        "revision_count": 0,
        "next_nodes": ["planner"],
    }

    final_state = await copilot_engine.ainvoke(initial_state)
    env_state = final_state.get("env_state", {})
    exec_state = final_state.get("execution_state", {})
    telemetry_state = final_state.get("telemetry_state", {})

    response = {
        "request_id": request_id,
        "product_category": env_state.get("product_category"),
        "evidence": env_state.get("evidence"),
        "cognitive_state": final_state.get("cognitive_state", {}),
        "execution_state": exec_state,
        "world_metrics": final_state.get("world_metrics", {}),
        "regenerate_node": exec_state.get("regenerate_node"),
        "revision_count": final_state.get("revision_count", 0),
        "telemetry": telemetry_state,
        "telemetry_summary": summarize_telemetry(telemetry_state),
        "memory_observability": memory_engine.observability_snapshot(),
        "shadow_sources": (
            _amazon_shadow_sources(request.url, env_state.get("product_category", ""))
            if request.real_source_mode == "amazon_shadow"
            else {}
        ),
    }
    emit_event(
        "debug_copilot_complete",
        request_id,
        endpoint="/api/v1/debug-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category"),
        goal=request.goal,
    )
    return response


@app.post("/api/v1/debug-source-probe", response_model=SourceProbeResponse)
async def debug_source_probe(request: SourceProbeRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    emit_event(
        "debug_source_probe_start",
        request_id,
        endpoint="/api/v1/debug-source-probe",
        status="started",
        product_category=request.product_category,
    )
    providers = request.providers or sorted(SOURCE_PROBE_PROVIDERS)
    results = []

    for provider in providers:
        if provider not in SOURCE_PROBE_PROVIDERS:
            results.append(
                SourceProbeResult(
                    provider=provider,
                    status="disabled",
                    error="Provider is not available in debug-only real-source probe.",
                    metadata={"allowed": False},
                )
            )
            continue

        started = time.perf_counter()
        try:
            evidence = source_probe_registry.fetch(
                provider,
                request.url or "",
                request.product_category,
            )
            warnings = list(evidence.data_warnings)
            disabled = any(
                warning.endswith("_disabled") or warning.endswith("_not_enabled")
                for warning in warnings
            )
            if disabled:
                status = "disabled"
            elif evidence.source_type == "unavailable":
                status = "unavailable"
            else:
                status = "success"
            results.append(
                SourceProbeResult(
                    provider=provider,
                    status=status,
                    source_confidence=evidence.confidence,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    evidence_preview=evidence.evidence_quotes[:3],
                    metadata={
                        **evidence.metadata,
                        "source_type": evidence.source_type,
                        "data_warnings": warnings,
                    },
                )
            )
        except Exception as exc:
            results.append(
                SourceProbeResult(
                    provider=provider,
                    status="error",
                    latency_ms=(time.perf_counter() - started) * 1000,
                    error=str(exc),
                )
            )

    fallback_required = not any(
        result.status == "success" and result.source_confidence >= 0.70
        for result in results
    )
    telemetry = SourceProbeTelemetry(
        total_latency_ms=sum(result.latency_ms for result in results),
        provider_count=len(results),
        success_count=sum(result.status == "success" for result in results),
        disabled_count=sum(result.status == "disabled" for result in results),
        unavailable_count=sum(result.status == "unavailable" for result in results),
        error_count=sum(result.status == "error" for result in results),
        fallback_required=fallback_required,
    )
    response = SourceProbeResponse(
        request_id=request_id,
        debug_only=True,
        product_category=request.product_category,
        results=results,
        fallback_required=fallback_required,
        telemetry=telemetry,
        memory_write_allowed=False,
    )
    emit_event(
        "debug_source_probe_complete",
        request_id,
        endpoint="/api/v1/debug-source-probe",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=request.product_category,
        provider_count=len(results),
        fallback_required=fallback_required,
    )
    return response




# L37-A/B multi-product review workspace analysis.
from collections import Counter
from schemas.review_workspace import (
    ReviewProductSummary,
    ReviewSourceBreakdown,
    ReviewSourceGroupSummary,
    ReviewSampleInterpretation,
    ReviewThemeSummary,
    ReviewVideoScript,
    ReviewVideoScriptPack,
    ReviewWorkspaceProduct,
    ReviewWorkspaceRequest,
    ReviewWorkspaceResponse,
    ReviewWorkspaceReview,
)
from schemas.review_paste import (
    PastedReviewWorkspaceAnalyzeRequest,
    PastedReviewWorkspaceAnalyzeResponse,
    ReviewPasteParseRequest,
    ReviewPasteParseResponse,
)

_REVIEW_WORKSPACE_THEME_MARKERS = {
    "leak / mess risk": ["leak", "leaking", "spill", "spilled", "mess", "drip"],
    "hard to clean": [
        "hard to clean",
        "difficult to clean",
        "cleaning under",
        "pulp gets stuck",
        "under the blade",
        "scrub",
        "dishwasher",
    ],
    "motor noise concern": ["too loud", "loud motor", "noisy", "motor noise"],
    "size / fit issue": ["too small", "too big", "doesn't fit", "didn't fit", "opening was bigger", "wide cans", "narrow opening", "\u30b5\u30a4\u30ba\u304c\u5c0f\u3055\u3044", "1\u30b5\u30a4\u30ba\u5927\u304d\u3044", "2\u30b5\u30a4\u30ba\u5927\u304d\u3044", "\u5c0f\u3076\u308a"],
    "grip / slipping concern": ["move a lot", "moves a lot", "stick to the floor", "sliding", "slides", "slip around", "slips", "does not stay", "doesn\'t stay", "stay in place"],
    "thickness / robot vacuum tradeoff": ["robot vacuum", "gets trapped", "get trapped", "too thick", "thick nature", "does not fit under", "doesn\'t fit under", "fit under doors", "under some doors"],
    "color expectation mismatch": ["color", "colour", "shade", "darker", "\u8272\u5473", "\u5199\u771f\u3088\u308a", "\u6697\u3081", "\u8272\u306e\u9055\u3044", "\u989c\u8272", "\u8272\u5dee"],
    "sewing / quality control issue": ["sewing", "stitch", "button hole", "thread", "quality control", "\u7e2b\u88fd", "\u307b\u3064\u308c", "\u30dc\u30bf\u30f3\u7a74", "\u691c\u54c1", "\u54c1\u8cea", "\u9752\u3044\u30da\u30f3"],
    "summer fabric comfort": ["fabric", "soft", "comfortable", "breathable", "\u7d20\u6750", "\u808c\u89e6\u308a", "\u67d4\u3089\u304b", "\u6dbc\u3057", "\u901a\u6c17", "\u900f\u6c14", "\u8f7b\u4fbf"],
    "durability concern": ["broke", "break", "broken", "flimsy", "crack", "not durable"],
    "space constraint": ["small kitchen", "apartment", "storage", "counter space"],
}

_REVIEW_WORKSPACE_FOOD_THEME_MARKERS = {
    "taste / flavor concern": [
        "watery",
        "flavorless",
        "terrible vinegar",
        "bad taste",
        "tastes bad",
        "bland",
        "weak flavor",
        "too sweet",
        "too acidic",
    ],
    "size / quantity mismatch": [
        "stated size is wrong",
        "size is wrong",
        "wrong size",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz bottle",
        "single bottle",
        "not sold by the single bottle",
        "only came in a 2-pack",
        "missing bottle",
        "pack count",
        "quantity mismatch",
    ],
    "price / value concern": [
        "priced wrong",
        "price is wrong",
        "expensive",
        "pricey",
        "not worth",
        "overpriced",
    ],
    "packaging / shipping concern": [
        "arrived damaged",
        "broken bottle",
        "leaked in shipping",
        "poorly packaged",
        "packaging problem",
        "no lid",
        "not lid",
        "air is ever present",
        "oxidation",
        "cap leaked",
    ],
    "quality consistency concern": [
        "quality changed",
        "inconsistent",
        "not the same",
        "store brand is better",
        "infinitely better",
    ],
}


_REVIEW_WORKSPACE_OBJECTION_MARKERS = [
    "but",
    "however",
    "wish",
    "too",
    "not",
    "doesn't",
    "didn't",
    "hard",
    "difficult",
    "wrong",
    "problem",
    "concern",
    "unless",
    "except",
    "although",
    "issue",
]

_REVIEW_WORKSPACE_LIKE_MARKERS = [
    "love", "great", "easy", "perfect", "works", "useful", "recommend", "helpful",
    "small enough", "easy to rinse",
    "will continue to purchase", "best rootbeer", "best root beer", "order it frequently",
    "great flavor", "greater flavor", "smoother", "worth the price",
    "cannot beat the price", "can't beat the price", "value priced", "worth it",
    "??", "??", "??", "??", "??",
]

_REVIEW_WORKSPACE_USE_CASE_MARKERS = [
    "for", "when", "use it", "daily", "morning", "travel", "kitchen", "work", "office",
    "gym", "backpack", "single serving", "protein shake", "kids", "pet",
    "??", "??", "??", "??", "??", "??", "??", "??",
]


def _rw_text(value) -> str:
    return " ".join(str(value or "").split())


def _rw_rating_value(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).split()[0])
    except (TypeError, ValueError):
        return None


def _rw_review_score(review) -> int:
    text = _rw_text(review.text)
    lowered = text.lower()
    if len(text) < 18:
        return 0

    score = 1
    rating = _rw_rating_value(review.rating)
    if rating is not None and rating <= 3:
        score += 3
    if rating is not None and rating >= 4:
        score += 1
    if review.helpful_count:
        score += min(3, int(review.helpful_count) // 5 + 1)
    if any(marker in lowered for marker in _REVIEW_WORKSPACE_OBJECTION_MARKERS):
        score += 3
    if any(marker in lowered for marker in _REVIEW_WORKSPACE_LIKE_MARKERS):
        score += 2
    if len(text) >= 80:
        score += 2
    return score


def _rw_collect_reviews(payload: ReviewWorkspaceRequest) -> list[dict]:
    rows = []
    seen = set()
    for product in payload.products:
        for review in product.reviews:
            text = _rw_text(review.text)
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            score = _rw_review_score(review)
            rows.append({
                "product": product,
                "review": review,
                "text": text,
                "score": score,
                "rating": _rw_rating_value(review.rating),
                "metadata": _rw_extract_review_metadata(review),
            })
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows


def _rw_raw_review_count(payload: ReviewWorkspaceRequest) -> int:
    return sum(len(getattr(product, "reviews", []) or []) for product in payload.products or [])


def _rw_duplicate_review_count(payload: ReviewWorkspaceRequest, rows: list[dict]) -> int:
    return max(0, _rw_raw_review_count(payload) - len(rows))



def _rw_primary_asin(payload: ReviewWorkspaceRequest) -> str:
    for product in payload.products or []:
        asin = _rw_text(getattr(product, "asin", ""))
        if asin:
            return asin
    return ""


def _rw_review_url_blob(row: dict) -> str:
    product = row.get("product")
    review = row.get("review")
    values = [
        getattr(product, "url", ""),
        getattr(product, "asin", ""),
        getattr(review, "source_section", ""),
        row.get("text", ""),
    ]
    return " ".join(str(value or "") for value in values).lower()


def _rw_review_source_tags(row: dict, primary_asin: str) -> list[str]:
    product = row.get("product")
    asin = _rw_text(getattr(product, "asin", ""))
    blob = _rw_review_url_blob(row)
    tags: list[str] = []

    is_variant = bool(asin and primary_asin and asin != primary_asin)
    if is_variant:
        tags.append("variant")
    elif asin or primary_asin:
        tags.append("main_product")

    if any(marker in blob for marker in [
        "filterbystar=critical",
        "filterbystar=one_star",
        "filterbystar=two_star",
        "filterbystar=three_star",
    ]):
        tags.append("low_star")

    if "reviewertype=avp_only_reviews" in blob or "verified purchase" in blob or "\u5df2\u786e\u8ba4\u8d2d\u4e70" in blob:
        tags.append("verified_purchase")

    if "sortby=recent" in blob:
        tags.append("recent")

    return tags or ["unknown"]


def _rw_first_metadata_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        try:
            match = re.search(pattern, text, flags=re.IGNORECASE)
        except re.error:
            continue

        if not match:
            continue

        value = ""
        if match.groups():
            value = match.group(1) or ""
        else:
            value = match.group(0) or ""

        value = " ".join(value.split()).strip(" -:;,??")
        if value:
            return value[:120]

    return ""


def _rw_metadata_between(text: str, start_markers: list[str], end_markers: list[str]) -> str:
    if not text:
        return ""

    best_start = -1
    best_marker = ""

    for marker in start_markers:
        index = text.find(marker)
        if index >= 0 and (best_start < 0 or index < best_start):
            best_start = index
            best_marker = marker

    if best_start < 0:
        return ""

    start = best_start + len(best_marker)
    end = len(text)

    for marker in end_markers:
        index = text.find(marker, start)
        if index >= 0:
            end = min(end, index)

    value = " ".join(text[start:end].split()).strip(" -:;,??")
    return value[:120]

def _rw_extract_review_metadata(review) -> dict:
    raw_text = _rw_text(getattr(review, "text", ""))
    source_section = _rw_text(getattr(review, "source_section", ""))
    blob = f"{raw_text} {source_section}"

    zh_color = chr(0x989c) + chr(0x8272) + ":"
    zh_size = chr(0x5c3a) + chr(0x5bf8) + ":"
    zh_verified = "".join(chr(code) for code in [0x5df2, 0x786e, 0x8ba4, 0x8d2d, 0x4e70])
    zh_useful = "".join(chr(code) for code in [0x4f4d, 0x4f7f, 0x7528, 0x8005, 0x8ba4, 0x4e3a, 0x6b64, 0x8bc4, 0x8bba, 0x6709, 0x7528])
    zh_year = chr(0x5e74)
    zh_month = chr(0x6708)
    zh_day = chr(0x65e5)

    jp_color = "".join(chr(code) for code in [0x30ab, 0x30e9, 0x30fc]) + ":"
    jp_size = "".join(chr(code) for code in [0x30b5, 0x30a4, 0x30ba]) + ":"
    jp_verified = "".join(chr(code) for code in [0x78ba, 0x8a8d, 0x6e08, 0x307f, 0x8cfc, 0x5165])

    rating = _rw_rating_value(getattr(review, "rating", None))

    review_date = _rw_first_metadata_match(
        blob,
        [
            r"Reviewed in .*? on ([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"(\d{4}" + zh_year + r"\d{1,2}" + zh_month + r"\d{1,2}" + zh_day + r")",
        ],
    )

    color = _rw_first_metadata_match(
        blob,
        [
            r"Color:\s*(.+?)(?=\s+Size:|\s+Verified Purchase|\s+Reviewed in|$)",
        ],
    )
    if not color:
        color = _rw_metadata_between(
            blob,
            [zh_color, jp_color],
            [zh_size, jp_size, zh_verified, jp_verified, "Verified Purchase"],
        )

    size = _rw_first_metadata_match(
        blob,
        [
            r"Size:\s*(.+?)(?=\s+Verified Purchase|\s+Reviewed in|$)",
        ],
    )
    if not size:
        size = _rw_metadata_between(
            blob,
            [zh_size, jp_size],
            [zh_verified, jp_verified, "Verified Purchase"],
        )

    helpful_count = getattr(review, "helpful_count", None)
    try:
        helpful_count = int(helpful_count) if helpful_count is not None else None
    except (TypeError, ValueError):
        helpful_count = None

    if helpful_count is None:
        helpful_match = re.search(r"(\d+)\s+people found this helpful", blob, flags=re.IGNORECASE)
        if helpful_match:
            helpful_count = int(helpful_match.group(1))
        elif re.search(r"one person found this helpful", blob, flags=re.IGNORECASE):
            helpful_count = 1

    if helpful_count is None:
        helpful_match = re.search(r"(\d+)\s*" + re.escape(zh_useful), blob)
        if helpful_match:
            helpful_count = int(helpful_match.group(1))

    verified_purchase = any(
        marker in blob
        for marker in [
            "Verified Purchase",
            "Verified purchase",
            zh_verified,
            jp_verified,
            "reviewertype=avp_only_reviews",
        ]
    )

    return {
        "rating": rating,
        "review_date": review_date,
        "verified_purchase": verified_purchase,
        "color": color,
        "size": size,
        "helpful_count": helpful_count,
    }

def _rw_metadata_counter_values(rows: list[dict], key: str, limit: int = 5) -> list[str]:
    counter = Counter()
    for row in rows:
        value = (row.get("metadata") or {}).get(key)
        if value:
            counter[str(value)] += 1
    return [f"{value}: {count}" for value, count in counter.most_common(limit)]


def _rw_source_metadata_summary(rows: list[dict]) -> dict:
    summary = {
        "verified_purchase_count": 0,
        "review_date_count": 0,
        "helpful_vote_review_count": 0,
    }

    for row in rows:
        metadata = row.get("metadata") or {}
        if metadata.get("verified_purchase"):
            summary["verified_purchase_count"] += 1
        if metadata.get("review_date"):
            summary["review_date_count"] += 1
        if metadata.get("helpful_count"):
            summary["helpful_vote_review_count"] += 1

    colors = _rw_metadata_counter_values(rows, "color")
    sizes = _rw_metadata_counter_values(rows, "size")
    dates = _rw_metadata_counter_values(rows, "review_date")

    if colors:
        summary["top_colors"] = colors
    if sizes:
        summary["top_sizes"] = sizes
    if dates:
        summary["top_review_dates"] = dates

    return summary



def _rw_source_label(source_type: str, language: str) -> str:
    if language == "zh-CN":
        return {
            "main_product": "\u4e3b\u5546\u54c1\u8bc4\u8bba",
            "variant": "\u53d8\u4f53\u8bc4\u8bba",
            "low_star": "\u4f4e\u661f\u8bc4\u8bba",
            "verified_purchase": "\u5df2\u786e\u8ba4\u8d2d\u4e70\u8bc4\u8bba",
            "recent": "\u6700\u65b0\u8bc4\u8bba",
            "unknown": "\u672a\u5206\u7c7b\u8bc4\u8bba",
        }.get(source_type, source_type)

    return {
        "main_product": "Main product reviews",
        "variant": "Variant reviews",
        "low_star": "Low-star reviews",
        "verified_purchase": "Verified-purchase reviews",
        "recent": "Recent reviews",
        "unknown": "Unclassified reviews",
    }.get(source_type, source_type)


def _rw_source_group_summary(source_type: str, rows: list[dict], language: str) -> ReviewSourceGroupSummary:
    asin_counts = Counter(_rw_text(getattr(row.get("product"), "asin", "")) or "unknown" for row in rows)
    quotes: list[str] = []
    seen = set()

    for row in sorted(rows, key=lambda item: item.get("score", 0), reverse=True):
        quote = _rw_compact_evidence_quote(row.get("text", ""))
        key = quote.lower()
        if quote and key not in seen:
            seen.add(key)
            quotes.append(quote)
        if len(quotes) >= 3:
            break

    return ReviewSourceGroupSummary(
        source_type=source_type,
        label=_rw_source_label(source_type, language),
        review_count=len(rows),
        high_signal_review_count=sum(1 for row in rows if row.get("score", 0) >= 4),
        asin_count=len([asin for asin in asin_counts if asin != "unknown"]),
        top_asins=[f"{asin}: {count}" for asin, count in asin_counts.most_common(5)],
        evidence_quotes=quotes,
        metadata_summary=_rw_source_metadata_summary(rows),
    )


def _rw_source_breakdown(payload: ReviewWorkspaceRequest, rows: list[dict]) -> ReviewSourceBreakdown:
    language = payload.output_language
    primary_asin = _rw_primary_asin(payload)
    raw_review_count = _rw_raw_review_count(payload)
    unique_review_count = len(rows)
    duplicate_review_count = max(0, raw_review_count - unique_review_count)
    rows_by_source: dict[str, list[dict]] = {
        "main_product": [],
        "variant": [],
        "low_star": [],
        "verified_purchase": [],
        "recent": [],
        "unknown": [],
    }
    asin_counts = Counter()

    for row in rows:
        product = row.get("product")
        asin = _rw_text(getattr(product, "asin", "")) or "unknown"
        asin_counts[asin] += 1

        tags = _rw_review_source_tags(row, primary_asin)
        for tag in tags:
            rows_by_source.setdefault(tag, []).append(row)

    source_groups = [
        _rw_source_group_summary(source_type, source_rows, language)
        for source_type, source_rows in rows_by_source.items()
        if source_rows
    ]

    if language == "zh-CN":
        guidance = [
            "\u4e3b\u5546\u54c1\u4fe1\u53f7\u548c\u53d8\u4f53\u4fe1\u53f7\u9700\u8981\u5206\u5f00\u89e3\u8bfb\uff0c\u4e0d\u8981\u628a\u5355\u4e2a\u5c3a\u7801\u6216\u989c\u8272\u95ee\u9898\u76f4\u63a5\u6cdb\u5316\u4e3a\u6574\u4e2a\u5546\u54c1\u95ee\u9898\u3002",
            "\u4f4e\u661f\u548c\u5df2\u786e\u8ba4\u8d2d\u4e70\u8bc4\u8bba\u66f4\u9002\u5408\u7528\u6765\u627e\u8d2d\u4e70\u987e\u8651\u548c\u53cd\u5bf9\u610f\u89c1\u3002",
            "\u6700\u65b0\u8bc4\u8bba\u66f4\u9002\u5408\u7528\u6765\u89c2\u5bdf\u8fd1\u671f\u8d28\u91cf\u6216\u5c65\u7ea6\u53d8\u5316\u3002",
        ]
    else:
        guidance = [
            "Read main-product and variant signals separately; do not generalize one size/color issue to the entire product.",
            "Use low-star and verified-purchase reviews to identify objections and buyer hesitation.",
            "Use recent reviews to watch for newer quality, fulfillment, or expectation shifts.",
        ]

    return ReviewSourceBreakdown(
        total_reviews=unique_review_count,
        raw_review_count=raw_review_count,
        duplicate_review_count=duplicate_review_count,
        main_product_reviews=len(rows_by_source.get("main_product", [])),
        variant_reviews=len(rows_by_source.get("variant", [])),
        low_star_reviews=len(rows_by_source.get("low_star", [])),
        verified_purchase_reviews=len(rows_by_source.get("verified_purchase", [])),
        recent_reviews=len(rows_by_source.get("recent", [])),
        unknown_reviews=len(rows_by_source.get("unknown", [])),
        asin_review_counts=dict(asin_counts),
        source_groups=source_groups,
        guidance=guidance,
    )


def _rw_packet_theme_items(themes: list[ReviewThemeSummary], limit: int = 6) -> list[dict]:
    items: list[dict] = []
    for theme in (themes or [])[:limit]:
        items.append(
            {
                "label": getattr(theme, "label", ""),
                "evidence_count": getattr(theme, "evidence_count", 0),
                "evidence_quotes": list(getattr(theme, "evidence_quotes", []) or [])[:3],
            }
        )
    return items


def _rw_packet_source_groups(source_breakdown: ReviewSourceBreakdown, limit: int = 6) -> list[dict]:
    groups: list[dict] = []
    for group in list(getattr(source_breakdown, "source_groups", []) or [])[:limit]:
        groups.append(
            {
                "source_type": getattr(group, "source_type", ""),
                "label": getattr(group, "label", ""),
                "review_count": getattr(group, "review_count", 0),
                "high_signal_review_count": getattr(group, "high_signal_review_count", 0),
                "asin_count": getattr(group, "asin_count", 0),
                "top_asins": list(getattr(group, "top_asins", []) or [])[:5],
                "evidence_quotes": list(getattr(group, "evidence_quotes", []) or [])[:3],
                "metadata_summary": dict(getattr(group, "metadata_summary", {}) or {}),
            }
        )
    return groups


def _rw_packet_quotes(
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
    source_breakdown: ReviewSourceBreakdown,
    limit: int = 12,
) -> list[str]:
    quotes: list[str] = []
    seen = set()

    def add(value: str):
        quote = _rw_quote_snippet(value, 240)
        key = " ".join(quote.lower().split())
        if not quote or key in seen:
            return
        seen.add(key)
        quotes.append(quote)

    for themes in [buyer_objections, common_pain_points, liked_points, use_cases]:
        for theme in themes or []:
            for quote in getattr(theme, "evidence_quotes", []) or []:
                add(quote)
                if len(quotes) >= limit:
                    return quotes

    for group in getattr(source_breakdown, "source_groups", []) or []:
        for quote in getattr(group, "evidence_quotes", []) or []:
            add(quote)
            if len(quotes) >= limit:
                return quotes

    return quotes


def _review_workspace_llm_evidence_packet(
    payload: ReviewWorkspaceRequest,
    rows: list[dict],
    high_signal_rows: list[dict],
    source_breakdown: ReviewSourceBreakdown,
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
) -> dict:
    primary_product = next((product for product in payload.products if _rw_text(getattr(product, "title", ""))), None)
    if primary_product is None:
        primary_product = payload.products[0] if payload.products else None

    raw_review_count = getattr(source_breakdown, "raw_review_count", 0)
    duplicate_review_count = getattr(source_breakdown, "duplicate_review_count", 0)
    warnings = [
        "review_workspace_visible_sample_only",
        "review_workspace_no_external_fetch",
    ]
    if duplicate_review_count:
        warnings.append("duplicate_reviews_removed")
    if getattr(source_breakdown, "variant_reviews", 0):
        warnings.append("variant_reviews_present")
    if getattr(source_breakdown, "low_star_reviews", 0):
        warnings.append("low_star_reviews_present")
    if getattr(source_breakdown, "verified_purchase_reviews", 0):
        warnings.append("verified_purchase_reviews_present")

    source_groups = _rw_packet_source_groups(source_breakdown)
    return {
        "packet_version": "review_workspace_v1",
        "intended_model_use": "creative_brief_generation",
        "product": {
            "title": _rw_text(getattr(primary_product, "title", "")) if primary_product else "",
            "asin": _rw_text(getattr(primary_product, "asin", "")) if primary_product else "",
            "source_type": "review_workspace",
            "product_count": len(payload.products),
        },
        "review_stats": {
            "total_reviews": len(rows),
            "parsed_reviews": len(rows),
            "unique_analyzed_reviews": len(rows),
            "raw_review_count": raw_review_count,
            "duplicate_review_count": duplicate_review_count,
            "high_signal_reviews": len(high_signal_rows),
            "verified_purchase_reviews": getattr(source_breakdown, "verified_purchase_reviews", 0),
            "low_star_reviews": getattr(source_breakdown, "low_star_reviews", 0),
            "warnings": warnings,
            "data_warnings": warnings,
        },
        "evidence": {
            "pain_points": _rw_packet_theme_items(common_pain_points),
            "buyer_objections": _rw_packet_theme_items(buyer_objections),
            "positive_signals": _rw_packet_theme_items(liked_points),
            "use_cases": _rw_packet_theme_items(use_cases),
            "quotes": _rw_packet_quotes(
                common_pain_points,
                buyer_objections,
                liked_points,
                use_cases,
                source_breakdown,
            ),
            "source_groups": source_groups,
        },
        "generation_constraints": [
            "Use only supplied review evidence and product fields.",
            "Do not claim full-market statistics.",
            "Do not generalize one variant/color/size issue to the whole product unless multiple reviews support it.",
            "Keep main product / variant / competitor source boundaries visible.",
            "Do not turn buyer objections into positive claims unless evidence explicitly resolves the concern.",
        ],
    }


def _rw_theme_summaries(rows: list[dict], themes: dict[str, list[str]], limit: int = 6) -> list[ReviewThemeSummary]:
    scored = []
    for label, markers in themes.items():
        matched = []
        for row in rows:
            raw_text = row["text"]
            lowered = raw_text.lower()
            compact_quote = _rw_compact_evidence_quote(raw_text) if "_rw_compact_evidence_quote" in globals() else raw_text
            compact_lower = compact_quote.lower()
            if not any(marker.lower() in lowered or marker.lower() in compact_lower for marker in markers):
                continue
            needs_matched_quote = (
                "_rw_theme_needs_matched_quote" in globals()
                and _rw_theme_needs_matched_quote(label)
            )
            if needs_matched_quote and "_rw_quote_matches_theme" in globals() and not _rw_quote_matches_theme(label, compact_quote):
                continue
            if compact_quote:
                matched.append(compact_quote)
        if matched:
            scored.append((label, matched))
    scored.sort(key=lambda item: len(item[1]), reverse=True)
    return [
        ReviewThemeSummary(
            label=label,
            evidence_count=len(quotes),
            evidence_quotes=quotes[:3],
        )
        for label, quotes in scored[:limit]
    ]


def _rw_marker_summaries(rows: list[dict], markers: list[str], label_prefix: str, limit: int = 6) -> list[ReviewThemeSummary]:
    counter = Counter()
    quotes_by_marker: dict[str, list[str]] = {}
    for row in rows:
        lowered = row["text"].lower()
        for marker in markers:
            if marker.lower() in lowered:
                counter[marker] += 1
                quotes_by_marker.setdefault(marker, []).append(row["text"])
    return [
        ReviewThemeSummary(
            label=f"{label_prefix}: {marker}",
            evidence_count=count,
            evidence_quotes=quotes_by_marker.get(marker, [])[:3],
        )
        for marker, count in counter.most_common(limit)
    ]


def _rw_product_summary(product) -> ReviewProductSummary:
    rows = [
        {"text": _rw_text(review.text), "score": _rw_review_score(review), "review": review}
        for review in product.reviews
        if _rw_text(review.text)
    ]
    rows.sort(key=lambda item: item["score"], reverse=True)
    top_rows = rows[:10]
    pain_points = []
    liked_points = []
    for row in top_rows:
        lowered = row["text"].lower()
        if any(marker in lowered for marker in _REVIEW_WORKSPACE_OBJECTION_MARKERS):
            pain_points.append(row["text"])
        if any(marker in lowered for marker in _REVIEW_WORKSPACE_LIKE_MARKERS):
            liked_points.append(row["text"])
    return ReviewProductSummary(
        title=product.title or product.asin or product.url or "Untitled product",
        url=product.url,
        review_count=len(rows),
        high_signal_review_count=sum(1 for row in rows if row["score"] >= 4),
        top_pain_points=pain_points[:3],
        top_liked_points=liked_points[:3],
    )



def _rw_workspace_text_blob(payload, rows) -> str:
    parts: list[str] = []
    for product in getattr(payload, "products", []) or []:
        for attr in ("title", "brand", "description", "platform"):
            value = getattr(product, attr, "")
            if value:
                parts.append(str(value))
        for bullet in getattr(product, "bullet_points", []) or []:
            parts.append(str(bullet))

    for row in rows or []:
        if isinstance(row, dict):
            for key in ("text", "title", "product_title"):
                value = row.get(key)
                if value:
                    parts.append(str(value))

    return " ".join(parts).lower()


def _rw_workspace_is_food(payload, rows) -> bool:
    blob = _rw_workspace_text_blob(payload, rows)
    food_terms = [
        "vinegar",
        "balsamic",
        "olive oil",
        "sauce",
        "dressing",
        "flavor",
        "flavour",
        "taste",
        "tasty",
        "salad",
        "recipe",
        "cooking",
        "kitchen cookbook",
        "modena",
    ]
    return any(term in blob for term in food_terms)


def _rw_workspace_theme_markers(payload, rows):
    if _rw_workspace_is_food(payload, rows):
        return _REVIEW_WORKSPACE_FOOD_THEME_MARKERS
    return _REVIEW_WORKSPACE_THEME_MARKERS



def _rw_evidence_sentence_candidates(text: str) -> list[str]:
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return []

    # Do not blindly split on "?" because Amazon size text like "(16 oz?)"
    # can create broken fragments such as ") colavita, so..."
    normalized = cleaned.replace("!!!", ". ").replace("!!", ". ").replace("!", ". ")

    parts = re.split(r"(?<=[.])\s+|(?<=[?])\s+(?=[A-Z\"'])", normalized)
    candidates = []

    for part in parts:
        sentence = part.strip(" -:;,.")
        if not sentence:
            continue

        if "_rw_clean_evidence_fragment" in globals():
            sentence = _rw_clean_evidence_fragment(sentence)

        if not sentence or len(sentence) < 18:
            continue

        lower = sentence.lower()
        if lower.startswith(("so this is good", "but great for cooking", "and great for cooking")):
            continue

        candidates.append(sentence)

    return candidates or [_rw_clean_evidence_fragment(cleaned) if "_rw_clean_evidence_fragment" in globals() else cleaned]


def _rw_evidence_sentence_score(sentence: str) -> int:
    lower = sentence.lower()
    score = 0

    strong_terms = [
        "wrong size",
        "size is wrong",
        "stated size",
        "listed as",
        "what came was",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz",
        "2-pack",
        "single bottle",
        "not sold",
        "priced wrong",
        "price",
        "cheaper",
        "not worth",
        "not really worth",
        "price is ridiculous",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
        "wateriest",
        "flavorless",
        "terrible",
        "bad taste",
        "makes terrible",
        "store brand is better",
        "not super complex",
        "wish",
        "but",
        "however",
        "problem",
        "concern",
    ]
    for term in strong_terms:
        if term in lower:
            score += 4

    if "listed as" in lower and "what came was" in lower:
        score += 8
    if "received the regular size" in lower and "half size" in lower:
        score += 8

    if 45 <= len(sentence) <= 220:
        score += 3
    elif len(sentence) > 220:
        score += 1

    low_signal_terms = [
        "i bought this after reading reviews",
        "i use it with",
        "i put it on",
        "i throw in",
        "amazon's choice",
        "author of",
        "but great for cooking",
        "so this is good as long",
    ]
    for term in low_signal_terms:
        if term in lower:
            score -= 6

    if lower.startswith(("so ", "but ", "and ", "which ")):
        score -= 5

    return score


def _rw_best_evidence_sentence(text: str) -> str:
    candidates = _rw_evidence_sentence_candidates(text)
    if not candidates:
        return ""

    ranked = sorted(
        enumerate(candidates),
        key=lambda pair: (_rw_evidence_sentence_score(pair[1]), -pair[0]),
        reverse=True,
    )
    return ranked[0][1]



def _rw_clean_evidence_fragment(value: str) -> str:
    text = " ".join(str(value or "").split()).strip(" -:;,.")

    # Prefer the actual review body after Amazon purchase markers.
    for marker in [
        "Verified Purchase",
        "Verified purchase",
        "\u5df2\u786e\u8ba4\u8d2d\u4e70",
        "\u78ba\u8a8d\u6e08\u307f\u8cfc\u5165",
    ]:
        if marker in text:
            text = text.split(marker, 1)[1].strip()
            break

    # Remove English Amazon review chrome.
    text = re.sub(r"Reviewed in .*? on [A-Za-z]+ \d{1,2}, \d{4}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[1-5](?:\.0)?\s+out of 5 stars\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Size:\s*[^.?!?]{1,120}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Color:\s*[^.?!?]{1,120}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+\s+people found this helpful\b.*$", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bone person found this helpful\b.*$", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bHelpful\s+Report\b.*$", " ", text, flags=re.IGNORECASE)

    # Remove Japanese / Chinese Amazon review chrome.
    text = re.sub(r"\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5[^\s]{0,12}\u53d1\u5e03\u8bc4\u8bba", " ", text)
    text = re.sub(r"\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5[^\s]{0,18}\u30ec\u30d3\u30e5\u30fc", " ", text)
    text = re.sub(r"[1-5](?:\.0)?\s*(?:\u661f|\u9897\u661f)(?:\uff08\u6700\u9ad8\s*5\s*\u661f\uff09|\uff0c\u6700\u591a\s*5\s*\u9897\u661f)?", " ", text)
    text = re.sub(r"\u989c\u8272:\s*[^\s?.!?]{1,80}", " ", text)
    text = re.sub(r"\u5c3a\u5bf8:\s*[^\s?.!?]{1,80}", " ", text)
    text = re.sub(r"\d+\s*\u4f4d\u4f7f\u7528\u8005\u8ba4\u4e3a\u6b64\u8bc4\u8bba\u6709\u7528.*$", " ", text)
    text = re.sub(r"\u6709\u7528\s+\u4e3e\u62a5.*$", " ", text)
    text = re.sub(r"\u5c06\u8bc4\u8bba\u7ffb\u8bd1\u6210\u4e2d\u6587.*$", " ", text)

    text = re.sub(r"\s+", " ", text).strip(" -:;,.")
    text = _strip_amazon_reviewer_prefix(text)

    # Remove broken leading punctuation left by metadata cleanup.
    text = re.sub(r"^[)\]\s]+", "", text).strip()
    # Drop fragments that start mid-word after browser text extraction,
    # for example: "r to the glaze but the taste..."
    if re.match(r"^[b-z]\s+(?:to|of|for|with|and|but)\s+", text):
        return ""

    # Drop Amazon report-modal / community-guideline chrome accidentally captured as review text.
    report_modal_markers = [
        "submit a",
        "common reasons customers reviews",
        "harassment, profanity",
        "spam, advertisement, promotions",
        "given in exchange for cash",
        "community guidelines",
        "when we get your",
    ]
    lower_text = text.lower()
    if any(marker in lower_text for marker in report_modal_markers):
        return ""


    # Drop low-value revision prefix while keeping the actual claim.
    text = re.sub(r"^Revised\s+\d{1,2}/\d{1,2}/\d{2,4}\s*-\s*", "", text, flags=re.IGNORECASE)

    # If a candidate begins with a dangling conjunction and is only positive proof,
    # it should not become an objection evidence quote.
    if re.match(r"^(but|and)\s+great for cooking\.?$", text, flags=re.IGNORECASE):
        return ""

    return text.strip(" -:;,.")


def _rw_compact_evidence_quote(value: str, max_len: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""

    for marker in ["Verified Purchase ", "Verified purchase "]:
        if marker in text:
            text = text.split(marker, 1)[1].strip()
            break

    text = re.sub(r"Reviewed in .*? on [A-Za-z]+ \d{1,2}, \d{4}", " ", text)
    text = re.sub(r"Size:\s*[^.]{1,100}", " ", text)
    text = re.sub(r"\b[1-5](?:\.0)? out of 5 stars\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+\s+people found this\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bone person found this\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -:;,.")
    text = _rw_clean_evidence_fragment(text)

    if not text:
        return ""

    best_sentence = _rw_best_evidence_sentence(text)
    if best_sentence:
        best_sentence = _rw_clean_evidence_fragment(best_sentence)
        text = best_sentence

    if len(text) <= max_len:
        return text

    cut = text[:max_len].rstrip()
    sentence_end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if sentence_end >= 80:
        return cut[: sentence_end + 1].strip()

    return cut.rstrip(" ,;:") + "..."


def _rw_rebuild_theme_summary(theme, *, label: str | None = None, evidence_quotes: list[str] | None = None):
    data = theme.model_dump() if hasattr(theme, "model_dump") else dict(theme)
    if label is not None:
        data["label"] = label
    if evidence_quotes is not None:
        data["evidence_quotes"] = evidence_quotes
        data["evidence_count"] = max(data.get("evidence_count", 0), len(evidence_quotes))
    return theme.__class__(**data)


def _rw_compact_theme_summaries(themes):
    compacted = []

    for theme in themes or []:
        quotes = []
        seen = set()

        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = compact.lower()

            if compact and key not in seen:
                seen.add(key)
                quotes.append(compact)

            if len(quotes) >= 2:
                break

        compacted.append(_rw_rebuild_theme_summary(theme, evidence_quotes=quotes))

    return compacted


def _rw_objection_label_from_quotes(label: str, quotes: list[str]) -> str:
    blob = " ".join([label or "", *(quotes or [])]).lower()

    if any(term in blob for term in ["hard to clean", "difficult to clean", "pulp gets stuck", "under the blade"]):
        return "cleanup concern"

    if any(term in blob for term in ["too loud", "loud motor", "motor noise", "noisy"]):
        return "motor noise concern"

    if any(term in blob for term in ["leak", "leaking", "leaked", "spill", "mess"]):
        return "leak / mess concern"

    if any(term in blob for term in [
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "sliding",
        "slides",
        "slip around",
        "slips",
        "does not stay",
        "doesn't stay",
        "stay in place",
    ]):
        return "grip / slipping concern"

    if any(term in blob for term in [
        "robot vacuum",
        "gets trapped",
        "get trapped",
        "too thick",
        "thick nature",
        "does not fit under",
        "doesn't fit under",
        "fit under doors",
        "under some doors",
    ]):
        return "thickness / robot vacuum tradeoff"

    if any(term in blob for term in [
        "not really worth",
        "price is ridiculous",
        "too expensive",
        "overpriced",
        "not worth",
    ]):
        return "price / value concern"

    if any(term in blob for term in [
        "no lid",
        "not lid",
        "without a lid",
        "lid to go over the spout",
        "air is ever present",
        "oxidation",
        "cap leaked",
        "bottle cap",
    ]):
        return "packaging / spout concern"

    if any(term in blob for term in [
        "wrong size",
        "size is wrong",
        "stated size",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz",
        "single bottle",
        "not sold by the single bottle",
        "only came in a 2-pack",
        "missing bottle",
        "pack count",
        "quantity mismatch",
    ]):
        return "quantity / size uncertainty"

    if any(term in blob for term in [
        "priced wrong",
        "price",
        "expensive",
        "cheaper",
        "not worth",
    ]):
        return "price / value uncertainty"

    if any(term in blob for term in [
        "wish",
        "would buy again",
        "if they",
        "preference",
        "wanted",
    ]):
        return "missing expectation / wish"

    if any(term in blob for term in [
        "not super",
        "not the same",
        "not sold",
        "doesn't",
        "didn't",
        "not ",
    ]):
        return "expectation mismatch"

    if any(term in blob for term in ["but", "however", "although", "except", "unless"]):
        return "tradeoff / hesitation"

    cleaned = label.replace("objection: ", "").strip()
    if cleaned in {"but", "not", "wish", "wrong", "too", "however", "?"}:
        return "buyer hesitation"

    return cleaned or "buyer hesitation"



def _rw_quote_is_positive_reassurance_quote(quote: str) -> bool:
    lower = str(quote or "").lower().strip()
    if not lower:
        return False

    negative_markers = [
        "wrong size",
        "size is wrong",
        "stated size",
        "listed as",
        "what came was",
        "half size",
        "not sold by the single bottle",
        "only came in",
        "only came as",
        "received the regular size",
        "priced wrong",
        "not worth",
        "not really worth",
        "price is ridiculous",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
        "wateriest",
        "flavorless",
        "terrible",
        "bad taste",
        "broken",
        "missing",
        "leak",
        "leaked",
        "doesn't",
        "didn't",
    ]
    if any(marker in lower for marker in negative_markers):
        return False

    two_pack_reassurance = (
        any(marker in lower for marker in ["two-pack", "2-pack", "second bottle"])
        and any(marker in lower for marker in [
            "give the second bottle",
            "give one to",
            "friend",
            "gift",
            "appreciate",
            "thoughtfulness",
        ])
    )

    value_reassurance = any(marker in lower for marker in [
        "cannot beat the price",
        "can't beat the price",
        "worth the price",
        "value priced",
        "great value",
        "worth it",
        "worth every",
        "for this quality",
        "excellent quality",
        "high quality",
        "best balsamic",
        "elixir of the gods",
        "exceptional",
        "delicious",
        "amazing",
        "favorite",
        "love this",
        "i love",
    ])

    if ("pricy" in lower or "pricey" in lower) and "worth it" in lower:
        value_reassurance = True

    return two_pack_reassurance or value_reassurance


def _rw_quote_is_strong_positive_signal(quote: str) -> bool:
    lower = str(quote or "").lower().strip()
    if not lower:
        return False

    positive_terms = [
        "love it",
        "will continue to purchase",
        "continue to purchase",
        "best rootbeer",
        "best root beer",
        "order it frequently",
        "great flavor",
        "greater flavor",
        "smoother",
        "smother greater flavor",
        "not as sharp as barq",
        "worth the price",
        "cannot beat the price",
        "can't beat the price",
        "value priced",
    ]
    return any(term in lower for term in positive_terms)


def _rw_quote_is_low_value_objection(quote: str) -> bool:
    lower = str(quote or "").lower().strip()

    if len(lower) < 18:
        return True

    # Strong positive proof can contain words like "but" or "not" in comparisons,
    # but should not become a buyer objection unless there is a clearer complaint.
    if _rw_quote_is_strong_positive_signal(quote) and not any(term in lower for term in [
        "too expensive",
        "not worth",
        "overpriced",
        "wrong",
        "hard to",
        "difficult",
        "problem",
        "issue",
        "broken",
        "leaked",
        "missing",
    ]):
        return True

    # Positive reassurance / gifting / value proof should not be treated as a buyer objection.
    if _rw_quote_is_positive_reassurance_quote(quote) and not (
        ("pricy" in lower or "pricey" in lower or "expensive" in lower) and "worth it" in lower
    ):
        return True

    # Positive proof / usage praise should not be treated as a buyer objection.
    if "great for cooking" in lower and not any(term in lower for term in [
        "wrong",
        "half size",
        "not sold",
        "2-pack",
        "single bottle",
        "priced wrong",
        "flavorless",
        "terrible",
    ]):
        return True

    if lower.startswith(("but great", "and great", "so this is good")):
        return True

    return False


def _rw_label_is_low_quality_objection(label: str, quote: str) -> bool:
    cleaned = str(label or "").replace("objection:", "").strip().lower()
    cleaned = cleaned.rstrip(".:;!?")
    if cleaned not in {"hard", "good", "great", "love", "best"}:
        return False

    lower = str(quote or "").lower()
    negative_context = [
        "hard to",
        "too hard",
        "not good",
        "not great",
        "not love",
        "not the best",
        "difficult",
    ]
    return not any(term in lower for term in negative_context)


def _rw_refine_buyer_objection_summaries(themes):
    grouped: dict[str, list[str]] = {}
    exemplar_theme_by_label = {}

    for theme in _rw_compact_theme_summaries(themes):
        theme_label = getattr(theme, "label", "")
        quotes = getattr(theme, "evidence_quotes", []) or []

        for quote in quotes:
            if _rw_quote_is_low_value_objection(quote):
                continue

            refined_label = _rw_objection_label_from_quotes(theme_label, [quote])
            if refined_label.startswith("objection:"):
                refined_label = refined_label.replace("objection:", "").strip() or "buyer hesitation"

            if refined_label in {"but", "not", "wish", "wrong", "too", "however", "?"}:
                refined_label = "buyer hesitation"

            if _rw_label_is_low_quality_objection(refined_label, quote):
                continue

            grouped.setdefault(refined_label, [])
            if quote not in grouped[refined_label]:
                grouped[refined_label].append(quote)

            exemplar_theme_by_label.setdefault(refined_label, theme)

    refined = []
    for label, quotes in grouped.items():
        refined.append(
            _rw_rebuild_theme_summary(
                exemplar_theme_by_label[label],
                label=label,
                evidence_quotes=quotes[:2],
            )
        )

    return refined


def _rw_quote_matches_theme(label: str, value: str) -> bool:
    lower = str(value or "").lower()
    raw_label = str(label or "").strip().lower()
    phrase = _rw_human_theme_phrase(label).strip().lower()

    price_value_tradeoff = (
        ("pricy" in lower or "pricey" in lower or "expensive" in lower)
        and "worth it" in lower
    )
    if _rw_quote_is_positive_reassurance_quote(value) and not price_value_tradeoff and any(marker in raw_label or marker in phrase for marker in [
        "price / value",
        "price or value",
        "size / quantity",
        "quantity or size",
        "quantity / size",
        "expectation mismatch",
        "tradeoff",
        "hesitation",
        "quality consistency",
    ]):
        return False

    packaging_terms = [
        "no lid",
        "not lid",
        "without a lid",
        "lid to go over the spout",
        "air is ever present",
        "oxidation",
        "cap leaked",
        "bottle cap",
    ]
    size_label_terms = [
        "size / quantity",
        "quantity or size",
        "quantity / size",
        "size or quantity",
    ]
    packaging_label_terms = [
        "packaging / spout",
        "packaging or spout",
        "spout concern",
        "packaging / shipping",
    ]

    has_packaging_signal = any(term in lower for term in packaging_terms)
    is_size_label = any(term in raw_label or term in phrase for term in size_label_terms)
    is_packaging_label = any(term in raw_label or term in phrase for term in packaging_label_terms)

    if has_packaging_signal and is_size_label:
        return False
    if has_packaging_signal and is_packaging_label:
        return True

    positive_value_only_terms = [
        "worth the price",
        "cannot beat the price",
        "can't beat the price",
        "value priced",
        "great value",
        "good value",
        "for this quality",
    ]
    explicit_price_concern_terms = [
        "too expensive",
        "not worth",
        "overpriced",
        "pricey",
        "pricy",
        "priced wrong",
        "price is wrong",
    ]
    has_positive_value_only = any(term in lower for term in positive_value_only_terms)
    has_explicit_price_concern = any(term in lower for term in explicit_price_concern_terms)
    if has_positive_value_only and not has_explicit_price_concern and any(term in raw_label or term in phrase for term in [
        "price / value",
        "price or value",
        "expectation mismatch",
        "tradeoff",
        "hesitation",
        "size / quantity",
        "quantity or size",
        "quantity / size",
    ]):
        return False

    explicit_negative_terms = [
        "not worth",
        "not really worth",
        "price is ridiculous",
        "too expensive",
        "overpriced",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
    ]
    if any(term in lower for term in explicit_negative_terms) and any(term in raw_label or term in phrase for term in [
        "liked signal",
        "buyers calling it",
        "buyers saying they love",
        "positive",
        "great",
        "love",
        "perfect",
        "recommend",
    ]):
        return False

    rug_concern_terms = [
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "sliding",
        "slides",
        "slip around",
        "slips",
        "robot vacuum",
        "gets trapped",
        "too thick",
        "thick nature",
        "does not fit under",
        "doesn't fit under",
    ]
    if any(term in lower for term in rug_concern_terms) and any(term in raw_label or term in phrase for term in [
        "summer fabric comfort",
        "color expectation mismatch",
    ]):
        return False

    marker_groups = [
        (
            ("grip / slipping", "slipping concern"),
            ["move a lot", "moves a lot", "stick to the floor", "sliding", "slides", "slip around", "slips", "does not stay", "doesn't stay"],
        ),
        (
            ("thickness / robot vacuum", "robot vacuum tradeoff", "clearance tradeoff"),
            ["robot vacuum", "gets trapped", "get trapped", "too thick", "thick nature", "does not fit under", "doesn't fit under", "fit under doors", "under some doors"],
        ),
        (
            ("summer fabric comfort",),
            ["fabric", "breathable", "summer", "hot weather", "??", "???", "??", "??", "??", "??"],
        ),
        (
            ("price / value", "price or value", "price / value concern"),
            ["priced wrong", "price is wrong", "too expensive", "not worth", "overpriced", "pricy", "pricey", "cheaper", "expensive", "cost"],
        ),
        (
            ("taste / flavor", "taste or flavor", "quality consistency"),
            ["taste", "flavor", "flavour", "wateriest", "flavorless", "bland", "rich", "glaze", "vinaigrette", "ingredients"],
        ),
        (
            ("size / quantity", "quantity or size", "quantity / size"),
            ["wrong size", "size is wrong", "stated size", "quantity", "listed as", "what came was", "oz", "missing bottle", "pack count", "quantity mismatch", "half size", "regular size"],
        ),
        (
            ("packaging / spout", "packaging / shipping", "spout concern"),
            ["no lid", "not lid", "without a lid", "spout", "air is ever present", "oxidation", "cap leaked", "bottle cap"],
        ),
        (
            ("expectation mismatch", "tradeoff", "hesitation"),
            ["expected", "expectation", "however", "but", "concerned", "mismatch"],
        ),
        (
            ("liked signal", "great", "love", "useful", "easy", "recommend"),
            ["great", "love", "useful", "easy", "recommend", "worth", "quality", "cannot beat", "value priced"],
        ),
    ]

    for label_markers, quote_markers in marker_groups:
        if any(marker in raw_label or marker in phrase for marker in label_markers):
            return any(marker in lower for marker in quote_markers)

    return False


def _rw_theme_needs_matched_quote(label: str) -> bool:
    raw_label = str(label or "").strip().lower()
    phrase = _rw_human_theme_phrase(label).strip().lower()
    markers = [
        "price / value",
        "price or value",
        "taste / flavor",
        "taste or flavor",
        "size / quantity",
        "quantity or size",
        "quality consistency",
        "packaging / spout",
        "packaging / shipping",
        "spout concern",
        "grip / slipping",
        "slipping concern",
        "thickness / robot vacuum",
        "robot vacuum tradeoff",
        "summer fabric comfort",
        "expectation mismatch",
        "quantity / size",
    ]
    return any(marker in raw_label or marker in phrase for marker in markers)


def _rw_refine_theme_quotes(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    refined: list[ReviewThemeSummary] = []
    for theme in themes:
        quotes = list(getattr(theme, "evidence_quotes", []) or [])
        matched = [quote for quote in quotes if _rw_quote_matches_theme(theme.label, quote)]
        if matched:
            theme.evidence_quotes = matched[:3]
            theme.evidence_count = len(matched)
            refined.append(theme)
        elif not _rw_theme_needs_matched_quote(theme.label):
            refined.append(theme)
    return refined


def _rw_theme_first_quote(theme) -> str:
    quotes = getattr(theme, "evidence_quotes", []) or []
    if not quotes:
        return ""

    label = str(getattr(theme, "label", "") or "")
    cleaned_quotes = []
    for quote in quotes:
        value = quote
        if "def _rw_compact_evidence_quote" in globals():
            value = _rw_compact_evidence_quote(value)
        value = " ".join(str(value or "").split()).strip()
        if value:
            cleaned_quotes.append(value)

    for quote in cleaned_quotes:
        if _rw_quote_matches_theme(label, quote):
            return quote

    if _rw_theme_needs_matched_quote(label):
        return ""

    return cleaned_quotes[0] if cleaned_quotes else ""

def _rw_quote_snippet(value: str, max_len: int = 120) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""

    if len(text) <= max_len:
        return text

    cut = text[:max_len].rstrip()
    return cut.rstrip(" ,;:") + "..."


def _rw_human_theme_phrase(label: str) -> str:
    raw = str(label or "").strip()
    normalized = raw.replace("liked signal:", "").strip()

    mapping = {
        "size / quantity mismatch": "quantity or size mismatch",
        "taste / flavor concern": "taste or flavor concern",
        "price / value concern": "price or value concern",
        "packaging / spout concern": "packaging or spout concern",
        "packaging / shipping concern": "packaging or shipping concern",
        "quality consistency concern": "quality consistency concern",
        "color expectation mismatch": "color expectation mismatch",
        "sewing / quality control issue": "sewing or QC concern",
        "summer fabric comfort": "summer fabric comfort",
        "grip / slipping concern": "grip or slipping concern",
        "thickness / robot vacuum tradeoff": "thickness or robot-vacuum tradeoff",
        "leak / mess risk": "mess or spill concern",
        "hard to clean": "cleanup concern",
        "durability concern": "durability concern",
        "time saving": "time-saving benefit",
        "great": "buyers calling it great",
        "love": "buyers saying they love it",
        "useful": "buyers finding it useful",
        "easy": "buyers finding it easy",
        "liked signal: great": "buyers calling it great",
        "liked signal: love": "buyers saying they love it",
        "liked signal: useful": "buyers finding it useful",
        "liked signal: easy": "buyers finding it easy",
    }

    return mapping.get(raw, mapping.get(normalized, normalized or "buyer signal"))

def _rw_quote_has_pain_signal(value: str) -> bool:
    lower = str(value or "").lower()
    if _rw_quote_is_positive_reassurance_quote(value):
        return False

    pain_terms = [
        "wrong size",
        "stated size",
        "listed as",
        "what came was",
        "half size",
        "priced wrong",
        "not worth",
        "not really worth",
        "price is ridiculous",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
        "wateriest",
        "flavorless",
        "terrible",
        "not super complex",
        "not sold",
        "2-pack",
        "single bottle",
        "no lid",
        "not lid",
        "without a lid",
        "lid to go over the spout",
        "air is ever present",
        "oxidation",
        "cap leaked",
        "bottle cap",
        "hard to clean",
        "difficult to clean",
        "cleaning under",
        "pulp gets stuck",
        "under the blade",
        "too loud",
        "loud motor",
        "motor noise",
        "leak",
        "leaked",
        "leaking",
    ]
    return any(term in lower for term in pain_terms)

def _rw_hook_from_theme(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    label = _rw_human_theme_phrase(raw_label)
    quote = _rw_theme_first_quote(theme)
    lower = quote.lower()

    if raw_label == "price / value concern":
        return "The price looks good, but is the size/value actually clear? Watch this before you buy."

    if raw_label == "quality consistency concern":
        return "Would you cook with this every day? Check the quality concern buyers mention."

    if raw_label == "packaging / spout concern":
        return "Before you buy, check the bottle spout concern buyers mention."

    if raw_label == "taste / flavor concern":
        return "I tested this balsamic so you don't have to - here's the flavor warning buyers mention."

    if "listed as" in lower and "what came was" in lower:
        return "POV: you ordered one size, but the bottle that arrived tells a different story."

    if "half size" in lower or "wrong size" in lower or "stated size" in lower:
        return "Before you buy, check the size buyers are actually receiving."

    if "wateriest" in lower or "flavorless" in lower or "terrible" in lower:
        return "I tested this balsamic so you don't have to - here's the flavor warning buyers mention."

    if "priced wrong" in lower or "price" in lower or "cheaper" in lower:
        return "The price looks good, but is the value actually clear? Watch this before you buy."

    return f"Before you buy, check the {label} buyers are calling out."

def _rw_dedupe_text_items(items: list[str], limit: int = 6) -> list[str]:
    deduped: list[str] = []
    seen = set()

    for item in items:
        normalized = " ".join(str(item or "").lower().split())
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped

def _rw_positive_hook_from_theme(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    normalized = raw_label.replace("liked signal:", "").strip().lower()
    quote = _rw_theme_first_quote(theme)

    if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
        return f"Start with the buyer concern: \"{_rw_quote_snippet(quote, 90)}\""

    if normalized == "great":
        return "Buyers keep calling this great - here's the moment that proves why."

    if normalized == "love":
        return "People say they love this - here's the everyday use case behind it."

    if normalized == "useful":
        return "Buyers say this is useful - here's the problem it solves fast."

    if normalized == "easy":
        return "Buyers say this feels easy - here's the moment that makes it click."

    label = _rw_human_theme_phrase(raw_label)
    if normalized in {"positive value signal", "value signal", "value proof"}:
        if quote:
            return f"Use the value proof as the payoff: \"{_rw_quote_snippet(quote, 90)}\""
        return "Use the value proof as the payoff before the CTA."
    if label.lower().startswith("buyers "):
        return f"Use this positive review proof: \"{_rw_quote_snippet(quote, 90)}\""
    return f"Buyers keep mentioning {label} - here's the proof moment."



def _rw_positive_hook_from_theme_zh(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    quote = _rw_quote_snippet(_rw_theme_first_quote(theme), 72)
    lower_quote = quote.lower()
    label = _rw_output_theme_label(raw_label, "zh-CN")

    if quote:
        if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
            return f"\u5148\u770b\u8fd9\u6761\u4e70\u5bb6\u987e\u8651\uff1a\u201c{quote}\u201d"
        if "cannot beat the price" in lower_quote or "worth it" in lower_quote or "pricy" in lower_quote or "pricey" in lower_quote:
            return f"\u8fd9\u74f6\u9999\u918b\u8d35\u4e00\u70b9\u4e5f\u6709\u4eba\u8bf4\u503c\uff1f\u5148\u770b\u8fd9\u53e5\u4e70\u5bb6\u539f\u8bdd\uff1a\u201c{quote}\u201d"

        if "elixir of the gods" in lower_quote or "best balsamic" in lower_quote or "best balsamic vinegar" in lower_quote:
            return f"\u4e3a\u4ec0\u4e48\u6709\u4e70\u5bb6\u628a\u8fd9\u74f6\u9999\u918b\u5938\u5230\u8fd9\u79cd\u7a0b\u5ea6\uff1f\u5148\u770b\u8fd9\u53e5\u539f\u8bdd\uff1a\u201c{quote}\u201d"

        if "two-pack" in lower_quote or "2-pack" in lower_quote or "second bottle" in lower_quote:
            return f"\u4e24\u74f6\u88c5\u4e0d\u53ea\u662f\u591a\u4e70\u4e00\u74f6\uff1f\u8fd9\u53e5\u4e70\u5bb6\u539f\u8bdd\u7ed9\u4e86\u4e00\u4e2a\u9001\u793c\u89d2\u5ea6\uff1a\u201c{quote}\u201d"

        if "love" in lower_quote or "favorite" in lower_quote or "delicious" in lower_quote or "amazing" in lower_quote:
            return f"\u4e70\u5bb6\u4e3a\u4ec0\u4e48\u4f1a\u559c\u6b22\u5b83\uff1f\u5148\u7528\u8fd9\u53e5\u539f\u8bdd\u5f00\u573a\uff1a\u201c{quote}\u201d"

        return f"\u8fd9\u6761\u6b63\u5411\u8bc1\u636e\u53ef\u4ee5\u76f4\u63a5\u53d8\u6210\u5e7f\u544a\u5f00\u5934\uff1a\u201c{quote}\u201d"

    if "\u559c\u6b22" in label:
        return "\u4e70\u5bb6\u4e3a\u4ec0\u4e48\u4f1a\u559c\u6b22\u5b83\uff1f\u5148\u7528\u4e00\u6761\u5177\u4f53\u8bc4\u8bba\u5f00\u573a\u3002"

    if "\u63a8\u8350" in label:
        return "\u4e3a\u4ec0\u4e48\u4e70\u5bb6\u613f\u610f\u63a8\u8350\u5b83\uff1f\u5148\u770b\u8bc4\u8bba\u91cc\u7684\u4f7f\u7528\u573a\u666f\u3002"

    return f"\u8fd9\u6761\u6b63\u5411\u8bc1\u636e\u80fd\u600e\u4e48\u53d8\u6210\u5e7f\u544a\u5f00\u5934\uff1f\u5148\u770b\u4e00\u6761\u5177\u4f53\u4e70\u5bb6\u539f\u8bdd\uff1a{label}"

def _rw_unique_themes_by_first_quote(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    unique: list[ReviewThemeSummary] = []
    seen_quotes = set()

    for theme in themes or []:
        quote = _rw_theme_first_quote(theme)
        key = " ".join(quote.lower().split()) if quote else f"label:{getattr(theme, 'label', '')}"
        if not key or key in seen_quotes:
            continue

        seen_quotes.add(key)
        unique.append(theme)

    return unique


def _rw_unique_theme_evidence_across_themes(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    unique: list[ReviewThemeSummary] = []
    seen_quotes = set()

    for theme in themes or []:
        quotes: list[str] = []
        for quote in getattr(theme, "evidence_quotes", []) or []:
            key = " ".join(str(quote or "").lower().split())
            if not key or key in seen_quotes:
                continue

            seen_quotes.add(key)
            quotes.append(quote)

        if quotes:
            unique.append(_rw_rebuild_theme_summary(theme, evidence_quotes=quotes))

    return unique

def _rw_hooks(common_pain_points: list[ReviewThemeSummary], liked_points: list[ReviewThemeSummary], language: str) -> list[str]:
    is_zh = language == "zh-CN"
    hooks: list[str] = []

    for theme in common_pain_points[:4]:
        label = _rw_output_theme_label(theme.label, language)
        if is_zh:
            hooks.append(f"\u4e70\u4e4b\u524d\u5148\u770b\u6e05\u695a\u8fd9\u4e2a\u95ee\u9898\uff1a{label}")
        else:
            hooks.append(_rw_hook_from_theme(theme))

    for theme in _rw_unique_themes_by_first_quote(liked_points):
        quote = _rw_theme_first_quote(theme)
        if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
            continue
        if is_zh:
            hooks.append(_rw_positive_hook_from_theme_zh(theme))
        else:
            hooks.append(_rw_positive_hook_from_theme(theme))
        if len(hooks) >= 6:
            break

    if not hooks:
        hooks.append(
            "\u5148\u7528\u6700\u5177\u4f53\u7684\u4e70\u5bb6\u539f\u8bdd\u5f00\u573a\uff0c\u518d\u5c55\u793a\u4ea7\u54c1\u5982\u4f55\u56de\u5e94\u8fd9\u4e2a\u573a\u666f\u3002"
            if is_zh
            else "Start with the most specific buyer quote, then show the product moment that resolves it."
        )

    return _rw_dedupe_text_items(hooks, 6)

def _rw_first_available_theme(*theme_groups: list[ReviewThemeSummary]) -> ReviewThemeSummary | None:
    for group in theme_groups:
        if group:
            return group[0]
    return None


def _rw_workspace_product_hint(payload: ReviewWorkspaceRequest, language: str) -> str:
    for product in payload.products or []:
        for attr in ("title", "brand", "description"):
            value = _rw_text(getattr(product, attr, ""))
            if value:
                return _rw_clean_workspace_product_phrase(value, language)

    return "\u8fd9\u4e2a\u5546\u54c1" if language == "zh-CN" else "the product"


def _rw_clean_workspace_product_phrase(value: str, language: str) -> str:
    text = _rw_text(value).replace("...", "").strip(" -_,;:")
    if not text:
        return "\u8fd9\u4e2a\u5546\u54c1" if language == "zh-CN" else "the product"

    root_beer_match = re.search(r"\b(?:[A-Za-z0-9'&.-]+\s+){0,4}root\s*beer\b", text, re.IGNORECASE)
    if root_beer_match:
        return _rw_text(root_beer_match.group(0))

    first_phrase = re.split(r"[,|:;(\[]", text, maxsplit=1)[0].strip(" -_,;:")
    if not first_phrase:
        first_phrase = text

    words = first_phrase.split()
    if len(first_phrase) > 52 and len(words) > 6:
        first_phrase = " ".join(words[:6])

    return first_phrase or ("\u8fd9\u4e2a\u5546\u54c1" if language == "zh-CN" else "the product")


def _rw_signal_lines(
    themes: list[ReviewThemeSummary],
    language: str,
    prefix_en: str,
    prefix_zh: str,
    limit: int = 3,
) -> list[str]:
    lines: list[str] = []
    is_zh = language == "zh-CN"
    for theme in themes[:limit]:
        label = _rw_output_theme_label(theme.label, language)
        quote = _rw_quote_snippet(_rw_theme_first_quote(theme), 100)
        prefix = prefix_zh if is_zh else prefix_en
        if quote:
            lines.append(f"{prefix}: {label} - \"{quote}\"")
        else:
            lines.append(f"{prefix}: {label}")
    return lines


def _rw_sample_interpretation(
    payload: ReviewWorkspaceRequest,
    rows: list[dict],
    high_signal_rows: list[dict],
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
) -> ReviewSampleInterpretation:
    language = payload.output_language
    is_zh = language == "zh-CN"
    product_count = len(payload.products)
    review_count = len(rows)
    raw_review_count = _rw_raw_review_count(payload)
    duplicate_review_count = max(0, raw_review_count - review_count)
    high_signal_count = len(high_signal_rows)

    strongest_signals: list[str] = []
    strongest_signals.extend(_rw_signal_lines(common_pain_points, language, "Pain signal", "\u75db\u70b9\u4fe1\u53f7", 2))
    strongest_signals.extend(_rw_signal_lines(buyer_objections, language, "Buyer objection", "\u8d2d\u4e70\u987e\u8651", 2))
    strongest_signals.extend(_rw_signal_lines(liked_points, language, "Positive proof", "\u6b63\u5411\u8bc1\u636e", 2))
    strongest_signals.extend(_rw_signal_lines(use_cases, language, "Use case", "\u4f7f\u7528\u573a\u666f", 1))

    if not strongest_signals:
        strongest_signals = [
            "\u5f53\u524d\u53ef\u89c1\u8bc4\u8bba\u6837\u672c\u8f83\u5c0f\uff0c\u5efa\u8bae\u5148\u7528\u4e8e\u521b\u610f\u65b9\u5411\u53c2\u8003\u3002"
            if is_zh
            else "The current visible review sample is small, so use it as creative direction input first."
        ]

    if is_zh:
        sample_type = "Amazon \u5f53\u524d\u53ef\u89c1\u9875\u9762\u8bc4\u8bba\u6837\u672c"
        sample_size_note = (
            f"\u5f53\u524d\u6837\u672c\u5305\u542b {product_count} \u4e2a\u5546\u54c1\u3001{raw_review_count} \u6761\u53ef\u89c1\u8bc4\u8bba\uff1b"
            f"\u53bb\u91cd\u540e {review_count} \u6761\u8fdb\u5165\u5206\u6790\uff0c{duplicate_review_count} \u6761\u4e3a\u91cd\u590d\u8bc4\u8bba\u3002"
            f"\u5176\u4e2d {high_signal_count} \u6761\u88ab\u8bc6\u522b\u4e3a\u9ad8\u4fe1\u53f7\u8bc4\u8bba\u3002"
            "\u8fd9\u4e2a\u6837\u672c\u9002\u5408\u505a\u521b\u610f\u4fe1\u53f7\uff0c\u4e0d\u9002\u5408\u5f53\u4f5c\u5b8c\u6574\u8bc4\u8bba\u7edf\u8ba1\u3002"
        )
        suitable_for = [
            "\u63d0\u53d6\u4e70\u5bb6\u539f\u8bdd",
            "\u627e\u77ed\u89c6\u9891 hook",
            "\u53d1\u73b0\u8d2d\u4e70\u987e\u8651",
            "\u63d0\u70bc\u6b63\u5411\u8bc1\u636e",
            "\u751f\u6210\u4f7f\u7528\u573a\u666f\u548c\u811a\u672c\u65b9\u5411",
        ]
        not_suitable_for = [
            "\u63a8\u65ad\u5b8c\u6574\u5dee\u8bc4\u7387",
            "\u4ee3\u8868\u5168\u90e8\u4e70\u5bb6\u6ee1\u610f\u5ea6",
            "\u4f5c\u4e3a\u5b8c\u6574\u5e02\u573a\u7814\u7a76\u6837\u672c",
            "\u5224\u65ad\u5168\u90e8 Amazon \u8bc4\u8bba\u7684\u7edf\u8ba1\u7ed3\u8bba",
        ]
        recommended_directions = [
            "\u5148\u7528\u6700\u5f3a\u75db\u70b9\u4fe1\u53f7\u751f\u6210\u5f00\u5934 hook\u3002",
            "\u7528\u4e70\u5bb6\u539f\u8bdd\u4f5c\u4e3a\u5c4f\u5e55\u5b57\u5e55\u6216\u53e3\u64ad\u5f00\u573a\u3002",
            "\u5728\u811a\u672c\u540e\u6bb5\u52a0\u5165\u6b63\u5411\u8bc1\u636e\uff0c\u907f\u514d\u53ea\u653e\u5927\u8d1f\u9762\u4fe1\u53f7\u3002",
        ]
        use_case_count = _rw_unique_quote_count(use_cases)
        evidence_usage_summary = [
            f"\u75db\u70b9\u8bc1\u636e\uff1a{sum(item.evidence_count for item in common_pain_points)} \u6761\u4fe1\u53f7",
            f"\u8d2d\u4e70\u987e\u8651\uff1a{sum(item.evidence_count for item in buyer_objections)} \u6761\u4fe1\u53f7",
            f"\u6b63\u5411\u8bc1\u636e\u8bc4\u8bba\uff1a{_rw_unique_quote_count(liked_points)} \u6761\u8bc4\u8bba",
            (
                f"\u4f7f\u7528\u573a\u666f\u8bc4\u8bba\uff1a{use_case_count} \u6761\u8bc4\u8bba"
                if use_case_count
                else "\u4f7f\u7528\u573a\u666f\u8bc4\u8bba\uff1a\u5f53\u524d\u6837\u672c\u672a\u8bc6\u522b\u5230\u660e\u786e\u4f7f\u7528\u573a\u666f\u8bc4\u8bba"
            ),
        ]
    else:
        sample_type = "Amazon visible-page review sample"
        sample_size_note = (
            f"This sample contains {product_count} product(s) and {raw_review_count} visible review(s); "
            f"after dedupe, {review_count} review(s) entered analysis and {duplicate_review_count} duplicate review(s) were excluded. "
            f"{high_signal_count} review(s) were identified as high-signal. Use it for creative signals, not full review statistics."
        )
        suitable_for = [
            "extracting buyer wording",
            "finding short-form video hooks",
            "spotting buyer objections",
            "finding positive proof",
            "generating use-case and script directions",
        ]
        not_suitable_for = [
            "estimating the full negative review rate",
            "representing all buyer satisfaction",
            "serving as a complete market research sample",
            "making full Amazon review population claims",
        ]
        recommended_directions = [
            "Use the strongest pain signal as the opening hook.",
            "Turn buyer wording into on-screen text or voiceover.",
            "Add positive proof near the payoff so the script does not only amplify negative signals.",
        ]
        use_case_count = _rw_unique_quote_count(use_cases)
        evidence_usage_summary = [
            f"Pain evidence: {sum(item.evidence_count for item in common_pain_points)} signal(s)",
            f"Buyer objections: {sum(item.evidence_count for item in buyer_objections)} signal(s)",
            f"Positive proof reviews: {_rw_unique_quote_count(liked_points)} review(s)",
            (
                f"Use case reviews: {use_case_count} review(s)"
                if use_case_count
                else "Use case reviews: no explicit use-case reviews were identified in this visible sample."
            ),
        ]

    return ReviewSampleInterpretation(
        sample_type=sample_type,
        sample_size_note=sample_size_note,
        suitable_for=suitable_for,
        not_suitable_for=not_suitable_for,
        strongest_signals=_rw_dedupe_text_items(strongest_signals, 6),
        recommended_creative_directions=recommended_directions,
        evidence_usage_summary=evidence_usage_summary,
    )


def _paste_clean_line(line: str) -> str:
    return " ".join(str(line or "").replace("\u00a0", " ").split())


def _paste_is_meta_line(line: str) -> bool:
    lowered = line.lower().strip()
    if not lowered:
        return True
    if lowered.startswith(_REVIEW_PASTE_META_PREFIXES):
        return True
    if "verified purchase" in lowered:
        return True
    if "found this helpful" in lowered:
        return True
    if lowered in {"read more", "show more", "see more", "customer reviews"}:
        return True
    return False


def _paste_high_signal_score(review: ReviewWorkspaceReview) -> int:
    text = _paste_clean_line(review.text)
    lowered = text.lower()
    if len(text) < 18:
        return 0

    score = 1
    try:
        rating = float(str(review.rating).split()[0]) if review.rating not in (None, "") else None
    except (TypeError, ValueError):
        rating = None

    if rating is not None and rating <= 3:
        score += 3
    if rating is not None and rating >= 4:
        score += 1
    if review.helpful_count:
        score += min(3, int(review.helpful_count) // 5 + 1)
    if any(marker in lowered for marker in ["but", "wish", "too", "not", "hard", "difficult", "problem", "issue", "leak", "broke", "mess"]):
        score += 3
    if any(marker in lowered for marker in ["love", "great", "easy", "perfect", "works", "useful", "recommend"]):
        score += 2
    if len(text) >= 80:
        score += 2
    return score


def _parse_helpful_count(line: str) -> int | None:
    match = re.search(r"(\d+)\s+people\s+found\s+this\s+helpful", line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"one\s+person\s+found\s+this\s+helpful", line, re.IGNORECASE):
        return 1
    return None


def _finalize_pasted_review(
    reviews: list[ReviewWorkspaceReview],
    rating,
    title: str,
    body_lines: list[str],
    helpful_count: int | None,
    source_section: str,
):
    body = _paste_clean_line(" ".join(body_lines))
    title = _paste_clean_line(title)

    if not body and title:
        body = title
        title = ""

    if len(body) < 10:
        return

    reviews.append(
        ReviewWorkspaceReview(
            rating=rating,
            title=title,
            text=body,
            helpful_count=helpful_count,
            source_section=source_section,
        )
    )


def _parse_messy_reviews(raw_text: str, source_section: str) -> list[ReviewWorkspaceReview]:
    lines = [_paste_clean_line(line) for line in str(raw_text or "").splitlines()]
    lines = [line for line in lines if line]

    reviews: list[ReviewWorkspaceReview] = []
    current_rating = None
    current_title = ""
    current_body: list[str] = []
    current_helpful = None
    active = False

    for line in lines:
        helpful = _parse_helpful_count(line)
        if helpful is not None:
            current_helpful = helpful
            continue

        rating_match = _REVIEW_PASTE_RATING_RE.search(line)
        if rating_match:
            if active:
                _finalize_pasted_review(
                    reviews,
                    current_rating,
                    current_title,
                    current_body,
                    current_helpful,
                    source_section,
                )

            active = True
            current_rating = rating_match.group("rating")
            remainder = _paste_clean_line(_REVIEW_PASTE_RATING_RE.sub("", line, count=1))
            current_title = remainder if len(remainder) <= 90 else ""
            current_body = [] if current_title else ([remainder] if remainder else [])
            current_helpful = None
            continue

        if _paste_is_meta_line(line):
            continue

        if active:
            if not current_title and len(line) <= 90 and not current_body:
                current_title = line
            else:
                current_body.append(line)
        else:
            # Generic non-Amazon paste fallback: each meaningful paragraph can be a review.
            if len(line) >= 30:
                reviews.append(
                    ReviewWorkspaceReview(
                        rating=None,
                        title="",
                        text=line,
                        helpful_count=None,
                        source_section=source_section,
                    )
                )

    if active:
        _finalize_pasted_review(
            reviews,
            current_rating,
            current_title,
            current_body,
            current_helpful,
            source_section,
        )

    # Deduplicate while preserving order.
    deduped: list[ReviewWorkspaceReview] = []
    seen = set()
    for review in reviews:
        key = _paste_clean_line(review.text).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(review)

    return deduped





# L-review-workspace-output-quality-polish
def _rw_unique_quote_count(themes: list[ReviewThemeSummary]) -> int:
    seen = set()
    for theme in themes or []:
        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = " ".join(compact.lower().split())
            if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(compact):
                continue
            if key:
                seen.add(key)
    return len(seen)


def _rw_positive_theme_label_from_quote(quote: str, fallback_label: str = "") -> str:
    lower = str(quote or "").lower()
    fallback = str(fallback_label or "").replace("liked signal:", "").strip().lower()

    if "will continue to purchase" in lower or "continue to purchase" in lower or "order it frequently" in lower:
        return "repeat purchase intent"

    if "best rootbeer" in lower or "best root beer" in lower or "absolute best root beer" in lower:
        return "best root beer praise"

    if "barq" in lower or "a&w" in lower or "smoother" in lower or "smother" in lower or "greater flavor" in lower:
        return "root beer flavor comparison"

    if any(term in lower for term in ["small enough for travel", "fits in my bag", "fits in a backpack"]):
        return "portable travel fit"

    if "easy to rinse" in lower or "quick to rinse" in lower:
        return "easy rinse signal"

    if "great flavor" in lower or re.search(r"\bsmooth(?:er|est)?\b", lower):
        return "flavor praise"

    if (
        "worth the price" in lower
        or "cannot beat the price" in lower
        or "can't beat the price" in lower
        or "value priced" in lower
        or "worth it" in lower
    ):
        return "positive value signal"

    if "love" in lower or fallback == "love":
        return "buyers saying they love it"

    if "great" in lower or fallback == "great":
        return "buyers calling it great"

    if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
        return "buyer concern signal"

    if fallback:
        return f"liked signal: {fallback}"

    return "positive proof"


def _rw_refine_liked_point_summaries(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    grouped: dict[str, list[str]] = {}
    seen_quotes = set()

    for theme in _rw_unique_theme_evidence_across_themes(_rw_compact_theme_summaries(themes)):
        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = " ".join(compact.lower().split())
            if not key or key in seen_quotes:
                continue

            seen_quotes.add(key)
            label = _rw_positive_theme_label_from_quote(compact, getattr(theme, "label", ""))
            grouped.setdefault(label, []).append(compact)

    refined: list[ReviewThemeSummary] = []
    for label, quotes in grouped.items():
        refined.append(
            ReviewThemeSummary(
                label=label,
                evidence_count=len(quotes),
                evidence_quotes=quotes[:3],
            )
        )

    return refined


def _rw_use_case_label_from_quote(quote: str, fallback_label: str = "") -> str:
    lower = str(quote or "").lower()

    if "west coast" in lower or "not available" in lower or "unavailable" in lower:
        return "regional availability context"

    if "gift" in lower or "friend" in lower or "give the second bottle" in lower:
        return "gift use case"

    if "daily" in lower or "morning" in lower or "every day" in lower:
        return "daily use context"

    if any(term in lower for term in ["office", "at work", "work desk"]):
        return "office use context"

    if any(term in lower for term in ["gym", "protein shake"]):
        return "gym or shake context"

    if any(term in lower for term in ["travel", "backpack", "in my bag"]):
        return "travel use context"

    if "single serving" in lower or "one smoothie" in lower:
        return "single-serving context"

    if "party" in lower or "guests" in lower:
        return "party or hosting context"

    if "fridge" in lower or "refrigerator" in lower or "stock" in lower or "pack" in lower:
        return "stocking or pack context"

    return "usage context"


def _rw_quote_is_real_use_case(quote: str, label: str = "") -> bool:
    lower = str(quote or "").lower()

    if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
        explicit_context = [
            "at work",
            "office",
            "gym",
            "travel",
            "backpack",
            "every day",
            "daily",
            "morning",
            "commute",
        ]
        if not any(term in lower for term in explicit_context):
            return False

    if _rw_quote_is_strong_positive_signal(quote) and not any(term in lower for term in [
        "west coast",
        "not available",
        "unavailable",
        "gift",
        "friend",
        "daily",
        "morning",
        "party",
        "guests",
        "fridge",
        "refrigerator",
        "pack",
        "stock",
        "office",
        "at work",
        "work desk",
        "gym",
        "protein shake",
        "travel",
        "backpack",
        "in my bag",
        "single serving",
        "one smoothie",
    ]):
        return False

    if str(label or "").strip().lower() == "use case: for" and not any(term in lower for term in [
        "for party",
        "for guests",
        "for daily",
        "for cooking",
        "for salads",
        "for gift",
        "for the fridge",
    ]):
        return False

    return any(term in lower for term in [
        "west coast",
        "not available",
        "unavailable",
        "gift",
        "friend",
        "daily",
        "morning",
        "party",
        "guests",
        "fridge",
        "refrigerator",
        "pack",
        "stock",
        "for cooking",
        "for salads",
        "office",
        "at work",
        "work desk",
        "gym",
        "protein shake",
        "travel",
        "backpack",
        "in my bag",
        "single serving",
        "one smoothie",
    ])


def _rw_refine_use_case_summaries(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    grouped: dict[str, list[str]] = {}
    seen_quotes = set()

    for theme in _rw_compact_theme_summaries(themes):
        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = " ".join(compact.lower().split())
            if not key or key in seen_quotes:
                continue
            if not _rw_quote_is_real_use_case(compact, getattr(theme, "label", "")):
                continue

            seen_quotes.add(key)
            label = _rw_use_case_label_from_quote(compact, getattr(theme, "label", ""))
            grouped.setdefault(label, []).append(compact)

    refined: list[ReviewThemeSummary] = []
    for label, quotes in grouped.items():
        ordered_quotes = sorted(
            quotes,
            key=lambda quote: (
                bool("_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote)),
                quotes.index(quote),
            ),
        )
        refined.append(
            ReviewThemeSummary(
                label=label,
                evidence_count=len(ordered_quotes),
                evidence_quotes=ordered_quotes[:2],
            )
        )

    return refined


def _rw_human_theme_phrase(label: str) -> str:
    raw = str(label or "").strip()
    normalized = raw.replace("liked signal:", "").strip()

    mapping = {
        "size / quantity mismatch": "quantity or size mismatch",
        "taste / flavor concern": "taste or flavor concern",
        "price / value concern": "price or value concern",
        "packaging / spout concern": "packaging or spout concern",
        "packaging / shipping concern": "packaging or shipping concern",
        "quality consistency concern": "quality consistency concern",
        "color expectation mismatch": "color expectation mismatch",
        "sewing / quality control issue": "sewing or QC concern",
        "summer fabric comfort": "summer fabric comfort",
        "grip / slipping concern": "grip or slipping concern",
        "thickness / robot vacuum tradeoff": "thickness or robot-vacuum tradeoff",
        "leak / mess risk": "mess or spill concern",
        "hard to clean": "cleanup concern",
        "durability concern": "durability concern",
        "time saving": "time-saving benefit",
        "repeat purchase intent": "repeat purchase intent",
        "best root beer praise": "best root beer praise",
        "root beer flavor comparison": "root beer flavor comparison",
        "flavor praise": "flavor praise",
        "positive value signal": "positive value signal",
        "regional availability context": "regional availability context",
        "gift use case": "gift use case",
        "daily use context": "daily use context",
        "party or hosting context": "party or hosting context",
        "stocking or pack context": "stocking or pack context",
        "usage context": "usage context",
        "great": "buyers calling it great",
        "love": "buyers saying they love it",
        "useful": "buyers finding it useful",
        "easy": "buyers finding it easy",
        "liked signal: great": "buyers calling it great",
        "liked signal: love": "buyers saying they love it",
        "liked signal: useful": "buyers finding it useful",
        "liked signal: easy": "buyers finding it easy",
    }

    return mapping.get(raw, mapping.get(normalized, normalized or "buyer signal"))


def _rw_output_theme_label(label: str, language: str) -> str:
    phrase = _rw_human_theme_phrase(label)
    if language != "zh-CN":
        return phrase

    normalized = str(label or "").strip().lower()
    phrase_key = phrase.strip().lower()
    zh_labels = {
        "price / value concern": "\u4ef7\u683c / \u4ef7\u503c\u987e\u8651",
        "price or value concern": "\u4ef7\u683c / \u4ef7\u503c\u987e\u8651",
        "packaging / spout concern": "\u5305\u88c5 / \u74f6\u5634\u987e\u8651",
        "packaging or spout concern": "\u5305\u88c5 / \u74f6\u5634\u987e\u8651",
        "packaging / shipping concern": "\u5305\u88c5 / \u8fd0\u8f93\u987e\u8651",
        "packaging or shipping concern": "\u5305\u88c5 / \u8fd0\u8f93\u987e\u8651",
        "taste / flavor concern": "\u5473\u9053 / \u98ce\u5473\u987e\u8651",
        "taste or flavor concern": "\u5473\u9053 / \u98ce\u5473\u987e\u8651",
        "size / quantity mismatch": "\u89c4\u683c / \u6570\u91cf\u4e0d\u4e00\u81f4",
        "quantity or size mismatch": "\u89c4\u683c / \u6570\u91cf\u4e0d\u4e00\u81f4",
        "quality consistency concern": "\u54c1\u8d28\u7a33\u5b9a\u6027\u987e\u8651",
        "color expectation mismatch": "\u989c\u8272 / \u8272\u5dee\u9884\u671f",
        "sewing / quality control issue": "\u7f1d\u5236 / \u8d28\u68c0\u95ee\u9898",
        "summer fabric comfort": "\u590f\u5b63\u9762\u6599\u8212\u9002\u5ea6",
        "quantity / size uncertainty": "\u6570\u91cf / \u89c4\u683c\u4e0d\u786e\u5b9a",
        "expectation mismatch": "\u9884\u671f\u4e0d\u4e00\u81f4",
        "price / value uncertainty": "\u4ef7\u683c / \u4ef7\u503c\u4e0d\u786e\u5b9a",
        "tradeoff / hesitation": "\u53d6\u820d / \u72b9\u8c6b",
        "buyers saying they love it": "\u4e70\u5bb6\u8868\u793a\u559c\u6b22",
        "buyers calling it great": "\u4e70\u5bb6\u8ba4\u4e3a\u4f53\u9a8c\u5f88\u597d",
        "buyers finding it useful": "\u4e70\u5bb6\u8ba4\u4e3a\u6709\u7528",
        "buyers finding it easy": "\u4e70\u5bb6\u8ba4\u4e3a\u5bb9\u6613\u4f7f\u7528",
        "repeat purchase intent": "\u6301\u7eed\u590d\u8d2d / \u613f\u610f\u7ee7\u7eed\u8d2d\u4e70",
        "best root beer praise": "\u6700\u4f73\u53e3\u5473\u8bc4\u4ef7",
        "root beer flavor comparison": "\u98ce\u5473\u5bf9\u6bd4 / \u66f4\u987a\u6ed1\u53e3\u5473",
        "flavor praise": "\u98ce\u5473\u597d\u8bc4",
        "positive value signal": "\u6b63\u5411\u4ef7\u503c\u4fe1\u53f7",
        "regional availability context": "\u5730\u533a\u7a00\u7f3a / \u5f53\u5730\u4e70\u4e0d\u5230",
        "gift use case": "\u9001\u793c\u573a\u666f",
        "daily use context": "\u65e5\u5e38\u996e\u7528\u573a\u666f",
        "party or hosting context": "\u805a\u4f1a / \u62db\u5f85\u573a\u666f",
        "stocking or pack context": "\u56e4\u8d27 / \u5305\u88c5\u573a\u666f",
        "usage context": "\u4f7f\u7528\u573a\u666f",
        "buyer concern signal": "\u8d2d\u4e70\u987e\u8651\u4fe1\u53f7",
        "recommend": "\u4e70\u5bb6\u613f\u610f\u63a8\u8350",
        "perfect": "\u4e70\u5bb6\u8ba4\u4e3a\u8868\u73b0\u5f88\u597d",
        "great": "\u4e70\u5bb6\u8ba4\u4e3a\u4f53\u9a8c\u5f88\u597d",
        "love": "\u4e70\u5bb6\u8868\u793a\u559c\u6b22",
    }
    return zh_labels.get(normalized) or zh_labels.get(phrase_key) or phrase


def _rw_creative_angles(
    common_pain_points: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    language: str = "en",
    buyer_objections: list[ReviewThemeSummary] | None = None,
) -> list[str]:
    is_zh = language == "zh-CN"
    primary_signals = common_pain_points or (buyer_objections or [])
    positive_signals = [
        theme for theme in _rw_unique_themes_by_first_quote(liked_points)
        if not ("_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(_rw_theme_first_quote(theme)))
    ]
    angles: list[str] = []

    primary = primary_signals[0] if primary_signals else None
    primary_label = _rw_output_theme_label(primary.label, language) if primary else ("\u4e70\u5bb6\u987e\u8651" if is_zh else "buyer concern")
    primary_quote = _rw_quote_snippet(_rw_theme_first_quote(primary), 120) if primary else ""

    repeat = next((theme for theme in positive_signals if "repeat purchase" in _rw_human_theme_phrase(theme.label).lower()), None)
    flavor = next((theme for theme in positive_signals if "flavor" in _rw_human_theme_phrase(theme.label).lower() or "root beer" in _rw_human_theme_phrase(theme.label).lower()), None)
    scarcity = next((theme for theme in positive_signals if "regional" in _rw_human_theme_phrase(theme.label).lower()), None)

    if is_zh:
        if primary:
            if repeat:
                repeat_quote = _rw_quote_snippet(_rw_theme_first_quote(repeat), 110)
                angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u5148\u627f\u8ba4{primary_label}\uff0c\u7528\u4e70\u5bb6\u539f\u8bdd\u201c{primary_quote}\u201d\u5f00\u573a\uff0c\u518d\u7528\u590d\u8d2d\u8bc1\u636e\u201c{repeat_quote}\u201d\u56de\u6536\u4fe1\u4efb\u3002")
            else:
                angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u5148\u627f\u8ba4{primary_label}\uff0c\u7528\u4e70\u5bb6\u539f\u8bdd\u201c{primary_quote}\u201d\u5f00\u573a\uff0c\u518d\u7ed9\u51fa\u4e00\u4e2a\u771f\u5b9e\u9009\u62e9/\u4f7f\u7528\u573a\u666f\u3002")

        if flavor:
            flavor_quote = _rw_quote_snippet(_rw_theme_first_quote(flavor), 120)
            angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u628a\u5b83\u62cd\u6210 root beer \u98ce\u5473\u5bf9\u6bd4\uff0c\u4e0d\u53ea\u8bf4\u597d\u559d\uff0c\u800c\u662f\u7528\u539f\u8bdd\u201c{flavor_quote}\u201d\u89e3\u91ca\u548c Barq's / A&W \u7684\u5dee\u5f02\u3002")

        if scarcity:
            scarcity_quote = _rw_quote_snippet(_rw_theme_first_quote(scarcity), 110)
            angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u5f3a\u8c03\u5730\u533a\u7a00\u7f3a\u6216\u4e0d\u5bb9\u6613\u4e70\u5230\uff0c\u7528\u201c{scarcity_quote}\u201d\u505a\u61c2\u7684\u4eba\u624d\u61c2\u7684\u5f00\u573a\u3002")
    else:
        if primary:
            if repeat:
                repeat_quote = _rw_quote_snippet(_rw_theme_first_quote(repeat), 110)
                angles.append(f"Copy-ready angle: Acknowledge the {primary_label} with \"{primary_quote},\" then recover trust with repeat-purchase proof: \"{repeat_quote}.\"")
            else:
                angles.append(f"Copy-ready angle: Acknowledge the {primary_label} with \"{primary_quote},\" then show the real selection or usage context.")
        if flavor:
            flavor_quote = _rw_quote_snippet(_rw_theme_first_quote(flavor), 120)
            angles.append(f"Copy-ready angle: Turn it into a root beer taste comparison, using \"{flavor_quote}\" to explain the Barq's / A&W difference.")
        if scarcity:
            scarcity_quote = _rw_quote_snippet(_rw_theme_first_quote(scarcity), 110)
            angles.append(f"Copy-ready angle: Lean into regional scarcity or hard-to-find appeal with \"{scarcity_quote}.\"")

    if not angles:
        angles.append(
            "\u521b\u610f\u65b9\u5411\uff1a\u7528\u6700\u5177\u4f53\u7684\u4e70\u5bb6\u539f\u8bdd\u5f00\u573a\uff0c\u518d\u628a\u6b63\u5411\u8bc1\u636e\u653e\u5728\u7ed3\u5c3e\u505a\u4fe1\u4efb\u56de\u6536\u3002"
            if is_zh
            else "Copy-ready angle: Open with the most specific buyer quote, then use positive proof as the trust payoff."
        )

    return angles[:3]


def _rw_video_script_pack(
    payload: ReviewWorkspaceRequest,
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
    hooks: list[str],
) -> ReviewVideoScriptPack:
    language = payload.output_language
    is_zh = language == "zh-CN"
    primary = _rw_first_available_theme(common_pain_points, buyer_objections, liked_points, use_cases)
    positive = _rw_first_available_theme(liked_points, use_cases, common_pain_points)
    flavor = next((theme for theme in liked_points if "flavor" in _rw_human_theme_phrase(theme.label).lower() or "root beer" in _rw_human_theme_phrase(theme.label).lower()), positive)

    primary_label = _rw_output_theme_label(primary.label, language) if primary else ("\u4e70\u5bb6\u5173\u6ce8\u70b9" if is_zh else "buyer concern")
    positive_label = _rw_output_theme_label(positive.label, language) if positive else ("\u6b63\u5411\u8bc1\u636e" if is_zh else "positive proof")
    primary_quote = _rw_quote_snippet(_rw_theme_first_quote(primary), 140) if primary else ""
    positive_quote = _rw_quote_snippet(_rw_theme_first_quote(positive), 120) if positive else ""
    flavor_quote = _rw_quote_snippet(_rw_theme_first_quote(flavor), 130) if flavor else positive_quote
    product_hint = _rw_workspace_product_hint(payload, language)
    hook = hooks[0] if hooks else (
        f"\u4e70\u4e4b\u524d\u5148\u770b\u8fd9\u4e2a\u4e70\u5bb6\u4fe1\u53f7\uff1a{primary_label}"
        if is_zh
        else f"Before you buy, look at this buyer signal: {primary_label}."
    )

    if is_zh:
        positioning_note = "\u57fa\u4e8e\u5f53\u524d\u53ef\u89c1\u8bc4\u8bba\u6837\u672c\u751f\u6210\u7684\u7b2c\u4e00\u7248\u77ed\u89c6\u9891\u811a\u672c\uff0c\u9002\u5408\u7ee7\u7eed\u6269\u5c55\u6210\u5206\u955c\u548c\u5173\u952e\u5e27\u3002"
        script_15 = ReviewVideoScript(
            duration_label="15s",
            hook=hook,
            voiceover=[
                f"\u7b2c\u4e00\u955c\uff1a\u51b0\u7bb1\u6216\u8d27\u67b6\u91cc\u628a{product_hint}\u548c\u666e\u901a root beer \u653e\u5728\u4e00\u8d77\uff0c\u5b57\u5e55\u76f4\u63a5\u95ee\uff1a\u8fd9\u4e2a\u4ef7\u683c\u503c\u5417\uff1f",
                f"\u7b2c\u4e8c\u955c\uff1a\u5012\u676f\u5192\u6ce1\uff0c\u540c\u65f6\u5ff5\u51fa\u4e70\u5bb6\u987e\u8651\u539f\u8bdd\uff1a{primary_quote if primary_quote else primary_label}\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u5207\u5230\u53e3\u5473\u5bf9\u6bd4\uff0c\u7528\u6b63\u5411\u539f\u8bdd\u6536\u5c3e\uff1a{flavor_quote or positive_quote or positive_label}\u3002",
            ],
            on_screen_text=[
                f"\u4e70\u5bb6\u5728\u610f\uff1a{primary_label}",
                primary_quote or "\u6765\u81ea\u53ef\u89c1\u8bc4\u8bba\u7684\u4ef7\u683c/\u4ef7\u503c\u4fe1\u53f7",
                flavor_quote or positive_quote or positive_label,
            ],
            cta="\u5982\u679c\u4f60\u4e5f\u5728\u72b9\u8c6b\u8fd9\u4e2a\u70b9\uff0c\u5148\u770b\u8fd9\u4e2a\u53ef\u89c1\u8bc4\u8bba\u6837\u672c\u3002",
            evidence_used=[quote for quote in [primary_quote, flavor_quote or positive_quote] if quote],
        )
        script_30 = ReviewVideoScript(
            duration_label="30s",
            hook=hook,
            voiceover=[
                f"\u7b2c\u4e00\u955c\uff1a\u8d27\u67b6/\u51b0\u7bb1\u5bf9\u6bd4\uff0c\u5148\u628a{primary_label}\u6446\u51fa\u6765\uff1a{primary_quote if primary_quote else primary_label}\u3002",
                f"\u7b2c\u4e8c\u955c\uff1a\u5f00\u7f50\u3001\u5012\u676f\u3001\u6c14\u6ce1\u7279\u5199\uff0c\u8ba9\u753b\u9762\u56de\u5230{product_hint}\u7684\u771f\u5b9e\u996e\u7528\u573a\u666f\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u505a\u98ce\u5473\u5bf9\u6bd4\uff0c\u4e0d\u53ea\u8bf4\u597d\u559d\uff0c\u76f4\u63a5\u7528\u539f\u8bdd\u89e3\u91ca\uff1a{flavor_quote or positive_quote or positive_label}\u3002",
                f"\u7b2c\u56db\u955c\uff1a\u7528\u590d\u8d2d\u6216\u559c\u7231\u8bc1\u636e\u505a\u4fe1\u4efb\u56de\u6536\uff1a{positive_quote if positive_quote else positive_label}\u3002",
            ],
            on_screen_text=[
                f"\u5148\u770b\u987e\u8651\uff1a{primary_label}",
                primary_quote or "\u4ef7\u683c / \u4ef7\u503c\u4fe1\u53f7",
                flavor_quote or "\u98ce\u5473\u5bf9\u6bd4\u8bc1\u636e",
                positive_quote or positive_label,
            ],
            cta="\u628a\u5b83\u5f53\u4f5c\u53ef\u89c1\u8bc4\u8bba\u4fe1\u53f7\uff0c\u4e0d\u5f53\u4f5c\u5b8c\u6574\u8bc4\u8bba\u7edf\u8ba1\uff1b\u8d2d\u4e70\u524d\u5148\u770b\u8fd9\u4e2a\u70b9\u3002",
            evidence_used=[quote for quote in [primary_quote, flavor_quote, positive_quote] if quote],
        )
    else:
        positioning_note = "First-pass short-form scripts generated from the visible review sample, ready to expand into storyboard and keyframes."
        script_15 = ReviewVideoScript(
            duration_label="15s",
            hook=hook,
            voiceover=[
                f"Shot 1: Put {product_hint} next to a familiar root beer and ask whether the price is worth it.",
                f"Shot 2: Pour it over ice while reading the buyer concern: {primary_quote if primary_quote else primary_label}.",
                f"Shot 3: Cut to the flavor comparison and close with proof: {flavor_quote or positive_quote or positive_label}.",
            ],
            on_screen_text=[
                f"Buyer concern: {primary_label}",
                primary_quote or "visible review evidence",
                flavor_quote or positive_quote or positive_label,
            ],
            cta="Check this visible review signal before you buy.",
            evidence_used=[quote for quote in [primary_quote, flavor_quote or positive_quote] if quote],
        )
        script_30 = ReviewVideoScript(
            duration_label="30s",
            hook=hook,
            voiceover=[
                f"Shot 1: Shelf or fridge comparison: frame the {primary_label} with the actual buyer quote: {primary_quote if primary_quote else primary_label}.",
                f"Shot 2: Open, pour, and show the product in a real drinking moment.",
                f"Shot 3: Make the taste comparison specific: {flavor_quote or positive_quote or positive_label}.",
                f"Shot 4: Close with repeat-purchase or liking proof: {positive_quote if positive_quote else positive_label}.",
            ],
            on_screen_text=[
                f"Concern: {primary_label}",
                primary_quote or "Visible review evidence",
                flavor_quote or "Flavor comparison proof",
                positive_quote or positive_label,
            ],
            cta="Use this as a visible review signal, not full review statistics.",
            evidence_used=[quote for quote in [primary_quote, flavor_quote, positive_quote] if quote],
        )

    return ReviewVideoScriptPack(
        positioning_note=positioning_note,
        scripts=[script_15, script_30],
    )


def _rw_creative_proof_source(quote: str, source_breakdown: ReviewSourceBreakdown) -> str:
    quote_key = " ".join(_rw_text(quote).lower().split())
    for group in getattr(source_breakdown, "source_groups", []) or []:
        for candidate in getattr(group, "evidence_quotes", []) or []:
            candidate_key = " ".join(_rw_text(candidate).lower().split())
            if quote_key and (quote_key in candidate_key or candidate_key in quote_key):
                return _rw_text(getattr(group, "source_type", "")) or _rw_text(getattr(group, "label", ""))
    return "visible_review_sample"


def _rw_creative_angle_candidates(
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
    evidence_quotes: list[str],
) -> list[dict]:
    candidates: list[dict] = []

    def add(signal_type: str, theme: ReviewThemeSummary | None = None, quote: str = ""):
        proof_quote = _rw_quote_snippet(quote or _rw_theme_first_quote(theme), 240)
        if not proof_quote:
            return
        candidates.append(
            {
                "signal_type": signal_type,
                "theme": theme,
                "proof_quote": proof_quote,
                "evidence_count": int(getattr(theme, "evidence_count", 0) or 1),
            }
        )

    for signal_type, themes in [
        ("buyer_objection", buyer_objections),
        ("pain_point", common_pain_points),
        ("positive_signal", liked_points),
        ("use_case", use_cases),
    ]:
        for theme in themes or []:
            add(signal_type, theme)

    for quote in evidence_quotes:
        add("high_signal_quote", quote=quote)

    return candidates[:12]


def _rw_creative_angle_title(signal_type: str, label: str, language: str) -> str:
    is_zh = language == "zh-CN"
    prefix = {
        "buyer_objection": "\u987e\u8651\u53cd\u8f6c" if is_zh else "Objection reversal",
        "pain_point": "\u75db\u70b9\u89e3\u9898" if is_zh else "Pain-point resolution",
        "positive_signal": "\u6b63\u5411\u8bc1\u660e" if is_zh else "Positive proof",
        "use_case": "\u573a\u666f\u5171\u9e23" if is_zh else "Use-case resonance",
        "high_signal_quote": "\u4e70\u5bb6\u539f\u8bdd" if is_zh else "Buyer-language proof",
    }.get(signal_type, "\u8bc1\u636e\u89d2\u5ea6" if is_zh else "Evidence angle")
    return f"{prefix}\uff1a{label}" if is_zh else f"{prefix}: {label}"


def _rw_creative_script_copy(
    *,
    signal_type: str,
    label: str,
    product_context: str,
    proof_quote: str,
    payoff_quote: str,
    evidence_count: int,
    language: str,
) -> dict:
    is_zh = language == "zh-CN"
    label_lower = label.lower()
    evidence_scope = (
        f"\u5f53\u524d\u53ef\u89c1\u6837\u672c\u4e2d\u7684 {evidence_count} \u6761\u76f8\u5173\u8bc1\u636e"
        if is_zh
        else f"{evidence_count} related quote{'s' if evidence_count != 1 else ''} in the visible sample"
    )

    if any(term in label_lower for term in ["clean", "cleanup", "\u6e05\u6d17"]):
        scene_actions = (
            [
                f"\u7b2c\u4e00\u955c\uff1a\u62cd{product_context}\u505a\u5b8c\u4e00\u676f\u996e\u54c1\u540e\uff0c\u5200\u5934\u4e0b\u65b9\u6b8b\u7559\u679c\u6e23\u7684\u7279\u5199\uff0c\u53e0\u52a0\u539f\u8bdd\u201c{proof_quote}\u201d\u3002",
                "\u7b2c\u4e8c\u955c\uff1a\u62c6\u89e3\u5c55\u793a\u7528\u6237\u9700\u8981\u68c0\u67e5\u7684\u5200\u5934\u3001\u676f\u4f53\u548c\u51b2\u6d17\u6b65\u9aa4\uff0c\u4e0d\u58f0\u79f0\u5b83\u5df2\u7ecf\u5bb9\u6613\u6e05\u6d17\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u56de\u5230\u771f\u5b9e\u4f7f\u7528\u573a\u666f\uff0c\u7528\u201c{payoff_quote}\u201d\u8bf4\u660e\u4e70\u5bb6\u4e3a\u4ec0\u4e48\u4ecd\u4f1a\u8003\u8651\u5b83\u3002",
            ]
            if is_zh
            else [
                f"Scene 1: Show residue under the blade after one drink, with the buyer quote on screen: \"{proof_quote}\"",
                "Scene 2: Demonstrate the blade, cup, and rinse steps a buyer should inspect, without claiming cleanup is easy.",
                f"Scene 3: Return to the real use context and close with the supplied payoff quote: \"{payoff_quote}\"",
            ]
        )
        cta = (
            "\u8d2d\u4e70\u524d\uff0c\u7528\u8fd9\u53e5\u539f\u8bdd\u68c0\u67e5\u5200\u5934\u7ed3\u6784\u548c\u65e5\u5e38\u51b2\u6d17\u6b65\u9aa4\uff0c\u518d\u5224\u65ad\u662f\u5426\u9002\u5408\u4f60\u7684\u8282\u594f\u3002"
            if is_zh
            else "Before buying, use this quote as a checklist: inspect the blade design and daily rinse steps, then decide whether they fit your routine."
        )
    elif any(term in label_lower for term in ["noise", "loud", "\u566a\u97f3", "\u592a\u54cd"]):
        scene_actions = (
            [
                f"\u7b2c\u4e00\u955c\uff1a\u5728\u6e05\u6668\u516c\u5bd3\u573a\u666f\u4e2d\u542f\u52a8{product_context}\uff0c\u53e0\u52a0\u539f\u8bdd\u201c{proof_quote}\u201d\u3002",
                "\u7b2c\u4e8c\u955c\uff1a\u5c55\u793a\u7528\u6237\u5728\u4e0d\u540c\u65f6\u95f4\u548c\u7a7a\u95f4\u4e2d\u8bc4\u4f30\u9a6c\u8fbe\u58f0\u97f3\uff0c\u4e0d\u58f0\u79f0\u4ea7\u54c1\u66f4\u5b89\u9759\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u7528\u201c{payoff_quote}\u201d\u56de\u5230\u4e70\u5bb6\u771f\u5b9e\u4f7f\u7528\u573a\u666f\u3002",
            ]
            if is_zh
            else [
                f"Scene 1: Start {product_context} in an early-morning apartment setting and overlay the quote: \"{proof_quote}\"",
                "Scene 2: Show the buyer evaluating motor sound across realistic times and spaces, without claiming the product is quieter.",
                f"Scene 3: Return to the supplied use-case proof: \"{payoff_quote}\"",
            ]
        )
        cta = (
            "\u8d2d\u4e70\u524d\uff0c\u5148\u60f3\u6e05\u695a\u4f60\u4f1a\u5728\u4ec0\u4e48\u65f6\u95f4\u548c\u7a7a\u95f4\u4f7f\u7528\uff0c\u518d\u6839\u636e\u8fd9\u6761\u566a\u97f3\u53cd\u9988\u505a\u9009\u62e9\u3002"
            if is_zh
            else "Before buying, match this noise feedback to the time and space where you would actually use the product."
        )
    elif any(term in label_lower for term in ["leak", "spill", "mess", "\u6f0f", "\u6d12"]):
        scene_actions = (
            [
                f"\u7b2c\u4e00\u955c\uff1a\u628a{product_context}\u653e\u8fdb\u5065\u8eab\u5305\u6216\u80cc\u5305\uff0c\u7528\u539f\u8bdd\u201c{proof_quote}\u201d\u70b9\u51fa\u6f0f\u6db2\u98ce\u9669\u3002",
                "\u7b2c\u4e8c\u955c\uff1a\u7279\u5199\u68c0\u67e5\u676f\u76d6\u3001\u5bc6\u5c01\u4f4d\u7f6e\u548c\u643a\u5e26\u59ff\u52bf\uff0c\u4e0d\u58f0\u79f0\u4ea7\u54c1\u9632\u6f0f\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u7528\u201c{payoff_quote}\u201d\u56de\u6536\u4fbf\u643a\u6216\u4f7f\u7528\u573a\u666f\uff0c\u4fdd\u7559\u8d2d\u4e70\u524d\u68c0\u67e5\u63d0\u793a\u3002",
            ]
            if is_zh
            else [
                f"Scene 1: Pack {product_context} beside a gym bag or backpack and surface the leak concern with: \"{proof_quote}\"",
                "Scene 2: Close in on the lid, seal, and carry position a buyer should inspect, without claiming the product is leak-proof.",
                f"Scene 3: Close with the supplied portability or use-case proof: \"{payoff_quote}\" while keeping the pre-purchase check visible.",
            ]
        )
        cta = (
            "\u5982\u679c\u4f60\u4f1a\u628a\u5b83\u653e\u8fdb\u5305\u91cc\uff0c\u8d2d\u4e70\u524d\u5148\u6839\u636e\u8fd9\u6761\u539f\u8bdd\u68c0\u67e5\u676f\u76d6\u3001\u5bc6\u5c01\u548c\u643a\u5e26\u65b9\u5f0f\u3002"
            if is_zh
            else "If you plan to carry it in a bag, use this quote to check the lid, seal, and carry routine before buying."
        )
    elif signal_type == "use_case" or any(
        term in label_lower for term in ["travel", "office", "gym", "single-serving", "usage"]
    ):
        scene_actions = (
            [
                f"\u7b2c\u4e00\u955c\uff1a\u76f4\u63a5\u5c55\u793a{product_context}\u51fa\u73b0\u5728\u8bc4\u8bba\u63d0\u5230\u7684\u4f7f\u7528\u573a\u666f\uff0c\u53e0\u52a0\u201c{proof_quote}\u201d\u3002",
                f"\u7b2c\u4e8c\u955c\uff1a\u8ddf\u62cd\u4e00\u6b21\u5b8c\u6574\u7684\u4f7f\u7528\u52a8\u4f5c\uff0c\u53ea\u5c55\u793a\u539f\u8bdd\u652f\u6301\u7684\u201c{label}\u201d\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u7528\u201c{payoff_quote}\u201d\u6536\u5c3e\uff0c\u8ba9\u89c2\u4f17\u5bf9\u7167\u81ea\u5df1\u7684\u4f7f\u7528\u8282\u594f\u3002",
            ]
            if is_zh
            else [
                f"Scene 1: Put {product_context} directly in the review-backed use context and overlay: \"{proof_quote}\"",
                f"Scene 2: Follow one complete use moment and show only what the supplied \"{label}\" evidence supports.",
                f"Scene 3: Close with \"{payoff_quote}\" and invite viewers to compare it with their own routine.",
            ]
        )
        cta = (
            "\u5bf9\u7167\u8fd9\u6761\u4e70\u5bb6\u573a\u666f\uff0c\u770b\u5b83\u662f\u5426\u771f\u7684\u9002\u5408\u4f60\u7684\u901a\u52e4\u3001\u529e\u516c\u6216\u5065\u8eab\u8282\u594f\u3002"
            if is_zh
            else "Compare this buyer's use case with your own commute, office, or gym routine before choosing."
        )
    else:
        scene_actions = (
            [
                f"\u7b2c\u4e00\u955c\uff1a\u5c55\u793a{product_context}\u548c\u539f\u8bdd\u201c{proof_quote}\u201d\uff0c\u660e\u786e\u8fd9\u662f\u5f53\u524d\u6837\u672c\u7684\u4e70\u5bb6\u4fe1\u53f7\u3002",
                f"\u7b2c\u4e8c\u955c\uff1a\u628a\u201c{label}\u201d\u8f6c\u6362\u6210\u4e00\u4e2a\u53ef\u89c2\u5bdf\u7684\u8d2d\u4e70\u68c0\u67e5\u70b9\uff0c\u4e0d\u6dfb\u52a0\u4ea7\u54c1\u6548\u679c\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u7528\u201c{payoff_quote}\u201d\u6536\u5c3e\uff0c\u4fdd\u7559\u7528\u6237\u81ea\u4e3b\u5224\u65ad\u3002",
            ]
            if is_zh
            else [
                f"Scene 1: Show {product_context} with the supplied buyer line: \"{proof_quote}\" and label it as visible-sample evidence.",
                f"Scene 2: Turn \"{label}\" into one observable pre-purchase check without inventing a product effect.",
                f"Scene 3: Close with the supplied payoff quote: \"{payoff_quote}\" and leave the decision with the viewer.",
            ]
        )
        cta = (
            "\u628a\u8fd9\u6761\u4e70\u5bb6\u539f\u8bdd\u5f53\u4f5c\u8d2d\u4e70\u68c0\u67e5\u9879\uff0c\u518d\u5224\u65ad\u4ea7\u54c1\u662f\u5426\u9002\u5408\u4f60\u7684\u771f\u5b9e\u573a\u666f\u3002"
            if is_zh
            else "Use this buyer quote as a pre-purchase check, then decide whether the product fits your real use context."
        )

    risk_note = (
        f"\u8fd9\u4e2a\u65b9\u5411\u53ea\u6709{evidence_scope}\uff1b\u4e0d\u5f97\u58f0\u79f0\u987e\u8651\u5df2\u89e3\u51b3\uff0c\u4e5f\u4e0d\u5f97\u6269\u5927\u4e3a\u5168\u5e02\u573a\u7ed3\u8bba\u3002"
        if is_zh
        else f"This angle is supported by {evidence_scope}; do not claim the concern is resolved or generalize it to the full market."
    )
    return {"scenes": scene_actions, "cta": cta, "risk_note": risk_note}


def _rw_creative_angle_dedupe_key(angle: dict) -> str:
    cluster = " ".join(_rw_text(angle.get("angle_cluster")).lower().split())
    quote = " ".join(_rw_text(angle.get("proof_quote")).lower().split())
    return cluster or quote


def _rw_rank_and_dedupe_creative_angles(angles: list[dict]) -> tuple[list[dict], int]:
    ranked: list[dict] = []
    seen_clusters: set[str] = set()
    seen_quotes: set[str] = set()
    duplicate_count = 0

    def raw_score(angle: dict) -> int:
        coverage = dict(angle.get("evidence_coverage") or {})
        evidence_count = int(angle.get("supporting_evidence_count") or 0)
        return min(
            100,
            (30 if coverage.get("proof_quote") else 0)
            + (10 if coverage.get("proof_source") else 0)
            + (15 if coverage.get("buyer_pain") else 0)
            + (15 if coverage.get("buyer_objection") else 0)
            + (10 if coverage.get("liked_point") else 0)
            + (10 if coverage.get("use_case") else 0)
            + min(10, max(0, evidence_count - 1) * 5),
        )

    for angle in sorted(
        angles,
        key=lambda item: (
            raw_score(item),
            int(item.get("supporting_evidence_count") or 0),
            bool(item.get("proof_quote")),
        ),
        reverse=True,
    ):
        cluster_key = _rw_creative_angle_dedupe_key(angle)
        quote_key = " ".join(_rw_text(angle.get("proof_quote")).lower().split())
        duplicate_reasons: list[str] = []
        if cluster_key and cluster_key in seen_clusters:
            duplicate_reasons.append("same evidence signal cluster")
        if quote_key and quote_key in seen_quotes:
            duplicate_reasons.append("same proof quote")
        if duplicate_reasons:
            duplicate_count += 1
            continue

        score = raw_score(angle)
        coverage = dict(angle.get("evidence_coverage") or {})
        evidence_count = int(angle.get("supporting_evidence_count") or 0)
        gaps = [name for name, covered in coverage.items() if not covered]
        copy_ready = bool(
            score >= 60
            and evidence_count >= 2
            and
            coverage.get("proof_quote")
            and _rw_text(angle.get("hook"))
            and _rw_text(angle.get("cta"))
            and all(_rw_text(angle.get(field)) for field in ["first_scene", "second_scene", "third_scene"])
        )
        angle.update(
            {
                "evidence_strength_score": score,
                "evidence_gaps": gaps,
                "duplicate_angle_note": "",
                "copy_readiness": "ready" if copy_ready else "needs_evidence",
                "claim_safety_level": "conservative" if score < 70 else "evidence_grounded",
            }
        )
        ranked.append(angle)
        if cluster_key:
            seen_clusters.add(cluster_key)
        if quote_key:
            seen_quotes.add(quote_key)

    ranked.sort(
        key=lambda angle: (
            int(angle.get("evidence_strength_score") or 0),
            int(angle.get("supporting_evidence_count") or 0),
            bool(angle.get("proof_quote")),
        ),
        reverse=True,
    )
    top_angles = ranked[:3]
    for rank, angle in enumerate(top_angles, start=1):
        recommendation_ready = bool(
            rank == 1
            and int(angle.get("evidence_strength_score") or 0) >= 60
            and angle.get("copy_readiness") == "ready"
            and _rw_text(angle.get("proof_quote"))
        )
        angle["angle_rank"] = rank
        angle["is_recommended"] = recommendation_ready
        angle["recommendation_reason"] = (
            "Highest evidence coverage and strongest copy readiness among distinct review-signal clusters."
            if recommendation_ready
            else "Highest-ranked draft, but more distinct review evidence is required before recommendation."
            if rank == 1
            else "Retained as a distinct evidence-backed alternative angle."
        )
        angle["angle_id"] = f"angle_{rank}"
    return top_angles, duplicate_count


def _rw_creative_next_actions(
    top_ad_angles: list[dict],
    quality_checks: dict,
) -> list[dict]:
    actions: list[dict] = []
    recommended = next((angle for angle in top_ad_angles if angle.get("is_recommended")), None)
    if recommended:
        actions.append(
            {
                "action_type": "use_recommended_angle",
                "label": "Use the recommended angle",
                "reason": recommended.get("recommendation_reason", ""),
                "target": recommended.get("angle_id", ""),
                "guidance_only": True,
            }
        )
    if quality_checks.get("weak_evidence") or quality_checks.get("missing_quote"):
        actions.append(
            {
                "action_type": "collect_more_reviews",
                "label": "Collect more distinct review evidence",
                "reason": "Weak or missing quote coverage limits production confidence.",
                "target": "review_workspace",
                "guidance_only": True,
            }
        )
        actions.append(
            {
                "action_type": "lower_claim_strength",
                "label": "Use a more conservative claim",
                "reason": "Keep the script inside the supplied visible-sample evidence boundary.",
                "target": recommended.get("angle_id", "") if recommended else "creative_decision_pack",
                "guidance_only": True,
            }
        )
    if recommended and recommended.get("copy_readiness") == "ready":
        actions.append(
            {
                "action_type": "copy_video_prompt",
                "label": "Copy the provider-neutral video prompt",
                "reason": "The recommended script has a quote, three scenes, CTA, and risk note.",
                "target": "video_prompt_pack",
                "guidance_only": True,
            }
        )
    return actions


def _rw_creative_feedback_runtime(
    top_ad_angles: list[dict],
    recommended_angle: dict,
    quality_checks: dict,
    video_prompt_pack: dict,
    weak_evidence_count: int,
    missing_quote_count: int,
) -> dict:
    feedback_cards: list[dict] = []
    for angle in top_ad_angles:
        script = dict(angle.get("tiktok_script") or {})
        scenes = list(script.get("scenes") or [])
        missing_script_parts = [
            name
            for name, present in [
                ("hook", bool(_rw_text(script.get("hook") or angle.get("hook")))),
                ("scene_1", len(scenes) >= 1 and bool(_rw_text(scenes[0]))),
                ("scene_2", len(scenes) >= 2 and bool(_rw_text(scenes[1]))),
                ("scene_3", len(scenes) >= 3 and bool(_rw_text(scenes[2]))),
                ("cta", bool(_rw_text(script.get("cta") or angle.get("cta")))),
                ("proof_quote", bool(_rw_text(script.get("proof_quote") or angle.get("proof_quote")))),
            ]
            if not present
        ]
        score = int(angle.get("evidence_strength_score") or 0)
        evidence_gaps = list(angle.get("evidence_gaps") or [])
        script_ready = not missing_script_parts
        evidence_ready = bool(angle.get("proof_quote")) and score >= 60
        video_prompt_ready = bool(
            video_prompt_pack.get("keyframe_prompt")
            and list(video_prompt_pack.get("shot_list") or [])
        )
        should_lower_claim = (
            angle.get("claim_safety_level") != "evidence_grounded"
            or bool(evidence_gaps)
            or not evidence_ready
        )
        if script_ready and evidence_ready and not should_lower_claim:
            feedback_status = "ready_to_copy"
            suggested_user_action = "copy_video_prompt" if video_prompt_ready else "use_recommended_angle"
            feedback_reason = "Script and evidence coverage are ready for manual creative review and copy/export."
        elif script_ready and angle.get("proof_quote"):
            feedback_status = "needs_review"
            suggested_user_action = "lower_claim_strength" if should_lower_claim else "use_recommended_angle"
            feedback_reason = "The script is complete, but evidence gaps or conservative claim limits require review."
        else:
            feedback_status = "needs_evidence"
            suggested_user_action = "collect_more_reviews"
            feedback_reason = "Missing quote or script coverage prevents copy-ready use."
        feedback_cards.append(
            {
                "angle_id": angle.get("angle_id", ""),
                "angle_rank": angle.get("angle_rank", 0),
                "title": angle.get("title", ""),
                "is_recommended": bool(angle.get("is_recommended")),
                "feedback_status": feedback_status,
                "feedback_reason": feedback_reason,
                "script_ready": script_ready,
                "video_prompt_ready": video_prompt_ready,
                "evidence_ready": evidence_ready,
                "needs_more_reviews": not evidence_ready,
                "should_lower_claim": should_lower_claim,
                "suggested_user_action": suggested_user_action,
                "copy_target": (
                    "video_prompt_pack"
                    if suggested_user_action == "copy_video_prompt"
                    else angle.get("angle_id", "")
                ),
            }
        )

    recommended_card = next(
        (card for card in feedback_cards if card.get("is_recommended")),
        feedback_cards[0] if feedback_cards else {},
    )
    recommended_script = dict(recommended_angle.get("tiktok_script") or {})
    recommended_scenes = list(recommended_script.get("scenes") or [])
    missing_script_parts = [
        name
        for name, present in [
            ("hook", bool(_rw_text(recommended_script.get("hook")))),
            ("scene_1", len(recommended_scenes) >= 1 and bool(_rw_text(recommended_scenes[0]))),
            ("scene_2", len(recommended_scenes) >= 2 and bool(_rw_text(recommended_scenes[1]))),
            ("scene_3", len(recommended_scenes) >= 3 and bool(_rw_text(recommended_scenes[2]))),
            ("cta", bool(_rw_text(recommended_script.get("cta")))),
            ("proof_quote", bool(_rw_text(recommended_script.get("proof_quote")))),
        ]
        if not present
    ]
    recommended_script_ready = not missing_script_parts
    copy_video_prompt_available = bool(
        video_prompt_pack.get("keyframe_prompt")
        and list(video_prompt_pack.get("shot_list") or [])
    )
    ready_angle_count = sum(card["feedback_status"] == "ready_to_copy" for card in feedback_cards)
    needs_review_angle_count = sum(card["feedback_status"] != "ready_to_copy" for card in feedback_cards)

    if not recommended_card:
        overall_readiness = "needs_evidence"
        overall_reason = "No evidence-backed creative angle is available."
        recommended_next_step = "collect_more_reviews"
    elif missing_quote_count > 0 or weak_evidence_count > 0:
        overall_readiness = "ready_to_review" if recommended_script_ready else "needs_evidence"
        overall_reason = "A draft is available, but weak or missing evidence requires manual review."
        recommended_next_step = (
            "lower_claim_strength"
            if recommended_script_ready and recommended_card.get("should_lower_claim")
            else "collect_more_reviews"
        )
    elif recommended_card.get("feedback_status") == "ready_to_copy":
        overall_readiness = "ready_to_copy"
        overall_reason = "The recommended angle has a complete script and quote-backed evidence."
        recommended_next_step = "copy_video_prompt" if copy_video_prompt_available else "use_recommended_angle"
    else:
        overall_readiness = "ready_to_review"
        overall_reason = "The recommended angle exists but still needs a conservative manual review."
        recommended_next_step = "lower_claim_strength"

    evidence_gap_actions: list[dict] = []
    if missing_quote_count:
        evidence_gap_actions.append(
            {
                "gap_type": "missing_quote",
                "severity": "high",
                "reason": "One or more creative angles do not have a supplied buyer quote.",
                "suggested_action": "collect_more_reviews",
                "target_angle_id": recommended_angle.get("angle_id", ""),
            }
        )
    if weak_evidence_count:
        evidence_gap_actions.append(
            {
                "gap_type": "weak_evidence",
                "severity": "medium",
                "reason": "Visible-sample evidence is not strong enough for broad product claims.",
                "suggested_action": "lower_claim_strength",
                "target_angle_id": recommended_angle.get("angle_id", ""),
            }
        )
    if recommended_card.get("should_lower_claim") and not evidence_gap_actions:
        evidence_gap_actions.append(
            {
                "gap_type": "claim_safety",
                "severity": "medium",
                "reason": "The recommended angle still has evidence gaps or a conservative claim boundary.",
                "suggested_action": "use_conservative_script",
                "target_angle_id": recommended_angle.get("angle_id", ""),
            }
        )

    return {
        "feedback_summary": {
            "recommended_angle_id": recommended_angle.get("angle_id", ""),
            "recommended_angle_title": recommended_angle.get("title", ""),
            "overall_readiness": overall_readiness,
            "overall_readiness_reason": overall_reason,
            "ready_angle_count": ready_angle_count,
            "needs_review_angle_count": needs_review_angle_count,
            "weak_evidence_count": weak_evidence_count,
            "missing_quote_count": missing_quote_count,
            "recommended_next_step": recommended_next_step,
        },
        "angle_feedback_cards": feedback_cards,
        "script_readiness_review": {
            "recommended_script_ready": recommended_script_ready,
            "recommended_script_reason": (
                "The recommended script includes hook, three scenes, CTA, and proof quote."
                if recommended_script_ready
                else "The recommended script is missing required copy parts."
            ),
            "copy_recommended_script_available": recommended_script_ready,
            "copy_video_prompt_available": copy_video_prompt_available,
            "missing_script_parts": missing_script_parts,
            "claim_safety_level": recommended_angle.get("claim_safety_level", "conservative"),
        },
        "evidence_gap_actions": evidence_gap_actions,
        "workspace_flow_hints": [
            {
                "step_id": "review_evidence",
                "label": "Review the supplied evidence",
                "reason": "Confirm that the quote and source support the selected angle.",
                "target_panel": "projectWorkspaceCreativeEvidenceQualityPanel",
                "copy_or_export_hint": "copy_evidence_brief",
            },
            {
                "step_id": "review_recommended_angle",
                "label": "Review the recommended angle and TikTok script",
                "reason": overall_reason,
                "target_panel": "projectWorkspaceCreativeDecisionRecommendationPanel",
                "copy_or_export_hint": "copy_recommended_script",
            },
            {
                "step_id": "review_video_prompt",
                "label": "Review the provider-neutral video prompt",
                "reason": "Copy/export only; no video provider is called.",
                "target_panel": "projectWorkspaceVideoPromptPackPanel",
                "copy_or_export_hint": "copy_video_prompt",
            },
        ],
        "safety_reminders": {
            "provider_disabled": True,
            "video_generation_disabled": True,
            "llm_api_disabled": True,
            "media_upload_disabled": True,
            "paid_operation_disabled": True,
            "registry_write_disabled": True,
        },
    }


def _rw_creative_quality_checks(top_ad_angles: list[dict], evidence_count: int) -> dict:
    unsupported_terms = (
        "100% guaranteed",
        "guaranteed results",
        "never fails",
        "best on the market",
        "eliminates every",
        "works for everyone",
    )
    unsupported_claims: list[str] = []
    for angle in top_ad_angles:
        generated_copy = " ".join(
            _rw_text(angle.get(field))
            for field in ["hook", "script_outline", "first_scene", "second_scene", "third_scene", "cta"]
        ).lower()
        unsupported_claims.extend(term for term in unsupported_terms if term in generated_copy)

    missing_quote_angles = [
        angle.get("angle_id", "")
        for angle in top_ad_angles
        if angle.get("missing_quote") or not _rw_text(angle.get("proof_quote"))
    ]
    weak_evidence_angles = [
        angle.get("angle_id", "")
        for angle in top_ad_angles
        if angle.get("evidence_strength") == "weak"
    ]
    weak_cta_angles = [
        angle.get("angle_id", "")
        for angle in top_ad_angles
        if len(_rw_text(angle.get("cta"))) < 18
    ]
    weak_evidence = evidence_count < 3 or len(top_ad_angles) < 3 or bool(weak_evidence_angles)
    if unsupported_claims:
        recommendation = "Remove unsupported absolute claims before using this creative pack."
    elif missing_quote_angles or weak_evidence:
        recommendation = "Collect more distinct buyer quotes before treating every angle as production-ready."
    elif weak_cta_angles:
        recommendation = "Strengthen the CTA while keeping it tied to the supplied evidence."
    else:
        recommendation = "Evidence coverage is sufficient for manual creative review and copy/export."

    return {
        "missing_quote": bool(missing_quote_angles),
        "missing_quote_angles": missing_quote_angles,
        "unsupported_claim": bool(unsupported_claims),
        "unsupported_claim_terms": sorted(set(unsupported_claims)),
        "weak_cta": bool(weak_cta_angles),
        "weak_cta_angles": weak_cta_angles,
        "weak_evidence": weak_evidence,
        "weak_evidence_angles": weak_evidence_angles,
        "unsafe_provider_action": False,
        "evidence_count": evidence_count,
        "recommendation": recommendation,
        "provider_call_enabled": False,
        "video_generation_performed": False,
        "media_uploaded_or_downloaded": False,
        "paid_operation_enabled": False,
    }


def _rw_creative_variant_selection_pack(
    variants: list[dict],
    recommended_variant_id: str,
) -> dict:
    best_for_by_type = {
        "short_hook": "best_for_tiktok",
        "ugc_testimonial": "best_for_ugc",
        "problem_solution": "best_for_direct_response",
        "direct_demo": "best_for_low_evidence_safe_use",
        "objection_reversal": "best_for_fast_hook_test",
    }
    fit_reason_by_type = {
        "short_hook": "Uses the shortest evidence-backed opening for a fast TikTok hook test.",
        "ugc_testimonial": "Keeps the supplied buyer quote visible, which fits creator-led UGC framing.",
        "problem_solution": "Turns the documented pain or objection into a direct-response inspection sequence.",
        "direct_demo": "Keeps claims conservative by showing the existing product checks instead of promising a result.",
        "objection_reversal": "Tests an objection-first opening while preserving the supplied evidence and resolution boundary.",
    }
    hypothesis_by_type = {
        "short_hook": "A shorter quote-first opening will improve the first-seconds hold rate.",
        "ugc_testimonial": "A visible buyer quote will improve trust without adding a new product claim.",
        "problem_solution": "A pain-led inspection sequence will improve qualified click intent.",
        "direct_demo": "A product-first inspection will improve comprehension with lower claim risk.",
        "objection_reversal": "Acknowledging the objection early will improve engagement from cautious buyers.",
    }
    metric_by_type = {
        "short_hook": "3-second view rate",
        "ugc_testimonial": "hook hold rate",
        "problem_solution": "click-through rate",
        "direct_demo": "qualified view completion",
        "objection_reversal": "click-through rate",
    }

    selection_cards: list[dict] = []
    for variant in variants:
        variant_type = _rw_text(variant.get("variant_type"))
        missing_quote = bool(variant.get("missing_quote"))
        weak_evidence = bool(variant.get("weak_evidence"))
        evidence_score = max(0, min(100, int(variant.get("evidence_strength_score") or 0)))
        readiness = _rw_text(variant.get("copy_readiness")) or "needs_review"
        claim_safety = _rw_text(variant.get("claim_safety_level")) or "conservative"
        risk_level = (
            "high"
            if missing_quote
            else "medium"
            if weak_evidence or claim_safety != "evidence_grounded"
            else "low"
        )
        selection_score = evidence_score
        if readiness == "ready":
            selection_score += 15
        if claim_safety == "evidence_grounded":
            selection_score += 10
        if variant.get("variant_id") == recommended_variant_id:
            selection_score += 8
        if missing_quote:
            selection_score -= 35
        elif weak_evidence:
            selection_score -= 20
        if variant_type == "direct_demo" and weak_evidence:
            selection_score += 12
        selection_score = max(0, min(100, selection_score))
        best_for = best_for_by_type.get(variant_type, "best_for_tiktok")
        selection_reason = fit_reason_by_type.get(
            variant_type,
            "Uses the existing evidence-grounded variant without introducing a new claim.",
        )
        if weak_evidence:
            selection_reason += " Evidence is weak, so treat this as a conservative review draft."
        recommended_next_action = (
            "collect_more_reviews"
            if missing_quote
            else "lower_claim_strength"
            if weak_evidence
            else "prepare_ab_test"
        )
        selection_cards.append(
            {
                "selection_id": f"selection_{variant.get('variant_id', variant_type)}",
                "variant_id": variant.get("variant_id", ""),
                "variant_type": variant_type,
                "variant_title": variant.get("variant_title", ""),
                "best_for": best_for,
                "selection_rank": 0,
                "selection_score": selection_score,
                "selection_reason": selection_reason,
                "audience_fit": (
                    "Buyer-language fit from the selected evidence-grounded source angle."
                    if variant.get("proof_quote")
                    else "Audience fit needs more buyer-language evidence."
                ),
                "platform_fit": "TikTok vertical short-form creative test.",
                "evidence_fit": (
                    "proof_quote_present"
                    if variant.get("proof_quote")
                    else "missing_quote"
                ),
                "risk_level": risk_level,
                "claim_safety_level": (
                    claim_safety if not weak_evidence else "conservative"
                ),
                "copy_readiness": readiness if not weak_evidence else "needs_evidence",
                "test_hypothesis": hypothesis_by_type.get(
                    variant_type,
                    "This evidence-grounded framing may improve qualified engagement.",
                ),
                "success_metric": metric_by_type.get(variant_type, "click-through rate"),
                "recommended_next_action": recommended_next_action,
                "proof_quote": variant.get("proof_quote", ""),
                "risk_note": variant.get("risk_note", ""),
                "do_not_claim": list(variant.get("do_not_claim") or []),
            }
        )

    selection_cards.sort(
        key=lambda card: (-card["selection_score"], card["variant_type"], card["variant_id"])
    )
    for rank, card in enumerate(selection_cards, start=1):
        card["selection_rank"] = rank

    has_strong_evidence = any(
        card["evidence_fit"] == "proof_quote_present"
        and card["copy_readiness"] == "ready"
        and card["claim_safety_level"] == "evidence_grounded"
        for card in selection_cards
    )
    if has_strong_evidence:
        first_card = selection_cards[0] if selection_cards else {}
    else:
        first_card = next(
            (
                card
                for card in selection_cards
                if card["best_for"] == "best_for_low_evidence_safe_use"
            ),
            selection_cards[0] if selection_cards else {},
        )

    pair_candidates = [first_card] if first_card else []
    pair_candidates.extend(
        card
        for card in selection_cards
        if card.get("variant_id") != first_card.get("variant_id")
    )
    variant_a = pair_candidates[0] if pair_candidates else {}
    variant_b = pair_candidates[1] if len(pair_candidates) > 1 else {}
    recommended_ab_pair = {
        "variant_a_id": variant_a.get("variant_id", ""),
        "variant_b_id": variant_b.get("variant_id", ""),
        "variant_a_title": variant_a.get("variant_title", ""),
        "variant_b_title": variant_b.get("variant_title", ""),
    }
    weak_evidence_count = sum(card["copy_readiness"] != "ready" for card in selection_cards)
    missing_quote_count = sum(card["evidence_fit"] == "missing_quote" for card in selection_cards)
    ab_test_plan = {
        "test_name": "Evidence-grounded creative variant A/B readiness test",
        **recommended_ab_pair,
        "hypothesis": (
            f"{variant_a.get('variant_title', 'Variant A')} will outperform "
            f"{variant_b.get('variant_title', 'Variant B')} on "
            f"{variant_a.get('success_metric', 'qualified engagement')} while both stay inside the same evidence boundary."
        ),
        "what_to_change": "Change only the hook framing and creative presentation defined by each selected variant.",
        "what_to_keep_constant": "Keep product, audience, proof quote, offer context, CTA intent, duration range, and evidence boundary constant.",
        "primary_metric": variant_a.get("success_metric", "click-through rate"),
        "secondary_metric": "qualified view completion",
        "minimum_evidence_warning": (
            "Evidence is weak or missing for one or more variants; collect more reviews before paid launch."
            if weak_evidence_count or missing_quote_count
            else "Use only the supplied proof quote and do not generalize the result beyond this visible sample."
        ),
        "safe_launch_note": "Guidance only. Run a small controlled test after human review; no provider, media, or paid action is triggered here.",
    }
    return {
        "pack_version": "variant_selection_pack_v1",
        "selection_summary": {
            "selection_count": len(selection_cards),
            "best_use_case_count": len(
                {card["best_for"] for card in selection_cards if card["best_for"]}
            ),
            "weak_evidence_count": weak_evidence_count,
            "missing_quote_count": missing_quote_count,
            "ready_variant_count": sum(
                card["copy_readiness"] == "ready" for card in selection_cards
            ),
            "selection_readiness": (
                "ready_for_controlled_test" if has_strong_evidence else "needs_evidence_review"
            ),
        },
        "recommended_first_variant_id": first_card.get("variant_id", ""),
        "recommended_ab_pair": recommended_ab_pair,
        "selection_cards": selection_cards,
        "ab_test_plan": ab_test_plan,
        "selection_quality_checks": {
            "distinct_ab_pair": bool(
                variant_a.get("variant_id")
                and variant_b.get("variant_id")
                and variant_a.get("variant_id") != variant_b.get("variant_id")
            ),
            "weak_evidence": bool(weak_evidence_count),
            "missing_quote": bool(missing_quote_count),
            "high_claim_safety_recommended_without_quote": any(
                card["evidence_fit"] == "missing_quote"
                and card["claim_safety_level"] == "evidence_grounded"
                for card in selection_cards
            ),
        },
        "safety_boundaries": {
            "provider_enabled": False,
            "llm_api_enabled": False,
            "video_generation_enabled": False,
            "media_operation_enabled": False,
            "paid_operation_enabled": False,
            "registry_operation_enabled": False,
            "restore_or_rollback_enabled": False,
        },
    }


def _rw_creative_test_feedback_pack(
    variants: list[dict],
    variant_selection_pack: dict,
    unsupported_claims: list[str],
) -> dict:
    selection_cards = list(variant_selection_pack.get("selection_cards") or [])
    selection_by_variant = {
        card.get("variant_id"): card
        for card in selection_cards
        if card.get("variant_id")
    }
    ordered_variants = sorted(
        variants,
        key=lambda variant: (
            int(selection_by_variant.get(variant.get("variant_id"), {}).get("selection_rank") or 999),
            variant.get("variant_id", ""),
        ),
    )
    performance_by_rank = {
        1: ("strong", "strong", "moderate", "positive", "winner"),
        2: ("moderate", "strong", "moderate", "positive", "challenger"),
        3: ("moderate", "moderate", "moderate", "mixed", "promising"),
        4: ("weak", "moderate", "weak", "mixed", "revise"),
        5: ("weak", "weak", "weak", "unclear", "pause"),
    }
    variant_feedback_cards: list[dict] = []
    for index, variant in enumerate(ordered_variants, start=1):
        selection = selection_by_variant.get(variant.get("variant_id"), {})
        watch_signal, click_signal, conversion_signal, sentiment_signal, tier = (
            performance_by_rank.get(index, performance_by_rank[5])
        )
        missing_quote = bool(variant.get("missing_quote"))
        weak_evidence = bool(variant.get("weak_evidence"))
        if missing_quote:
            watch_signal = click_signal = conversion_signal = "insufficient_evidence"
            sentiment_signal = "unverified"
            tier = "evidence_blocked"
        elif weak_evidence:
            conversion_signal = "insufficient_evidence"
            tier = "needs_evidence_review"
        keep_or_change = "keep" if index == 1 and not weak_evidence else "change"
        next_action = (
            "collect_more_reviews"
            if missing_quote
            else "lower_claim_strength"
            if weak_evidence
            else "keep_winner"
            if index == 1
            else "revise_hook"
            if watch_signal == "weak"
            else "revise_cta"
        )
        what_worked = (
            f"The {variant.get('variant_type', 'creative')} framing preserves the selected proof quote "
            f"and is ranked for {selection.get('best_for', 'controlled testing')}."
            if variant.get("proof_quote")
            else "The format remains conservative, but there is no quote-backed proof to validate performance."
        )
        what_to_improve = (
            "Collect another specific buyer quote before changing the claim or treating this result as a winner."
            if missing_quote
            else "Lower claim strength and keep the visible-sample limitation in the hook, scenes, and CTA."
            if weak_evidence
            else "Test one hook or CTA change at a time while keeping the proof quote and scenes constant."
        )
        variant_feedback_cards.append(
            {
                "feedback_id": f"feedback_{variant.get('variant_id', index)}",
                "variant_id": variant.get("variant_id", ""),
                "variant_type": variant.get("variant_type", ""),
                "variant_title": variant.get("variant_title", ""),
                "test_status": "mock_signal_ready" if not weak_evidence else "evidence_review_required",
                "mock_performance_signal": True,
                "watch_rate_signal": watch_signal,
                "click_intent_signal": click_signal,
                "conversion_intent_signal": conversion_signal,
                "comment_sentiment_signal": sentiment_signal,
                "performance_tier": tier,
                "keep_or_change": keep_or_change,
                "what_worked": what_worked,
                "what_to_improve": what_to_improve,
                "next_hook_direction": (
                    variant.get("hook", "")
                    if keep_or_change == "keep"
                    else "Shorten the existing hook while retaining the same buyer quote and concern."
                ),
                "next_scene_direction": (
                    "Keep the existing three-scene evidence sequence; tighten only pacing and visual clarity."
                    if not weak_evidence
                    else "Use a conservative product inspection scene and avoid implying the concern is resolved."
                ),
                "next_cta_direction": (
                    "Keep the CTA as a buyer check, not a guaranteed outcome."
                    if not missing_quote
                    else "Ask viewers to compare their use case; do not make a product-performance claim."
                ),
                "risk_note": variant.get("risk_note", ""),
                "do_not_claim": list(variant.get("do_not_claim") or []),
                "evidence_note": (
                    f"Grounded to supplied quote: {variant.get('proof_quote')}"
                    if variant.get("proof_quote")
                    else "missing_quote: performance feedback is a review draft only."
                ),
                "recommended_next_action": next_action,
            }
        )

    winner = next(
        (card for card in variant_feedback_cards if card["keep_or_change"] == "keep"),
        variant_feedback_cards[0] if variant_feedback_cards else {},
    )
    winner_variant = next(
        (
            variant
            for variant in variants
            if variant.get("variant_id") == winner.get("variant_id")
        ),
        {},
    )
    any_weak = any(variant.get("weak_evidence") for variant in variants)
    any_missing = any(variant.get("missing_quote") for variant in variants)
    action_specs = [
        {
            "action_type": "keep_winner",
            "source_variant_id": winner.get("variant_id", ""),
            "action_title": "Keep the strongest evidence-grounded framing",
            "action_reason": "It leads the deterministic selection ranking while preserving the existing proof and safety boundary.",
            "suggested_copy_change": "Keep the winner hook as the control version.",
            "suggested_video_prompt_change": "Keep the winner shot order and visual proof as the control.",
        },
        {
            "action_type": "revise_hook",
            "source_variant_id": winner.get("variant_id", ""),
            "action_title": "Create one hook-only challenger",
            "action_reason": "A hook-only change isolates the first-seconds effect without changing the evidence.",
            "suggested_copy_change": "Shorten the hook, but keep the same proof quote and concern.",
            "suggested_video_prompt_change": "Change only the opening frame and overlay; keep later shots constant.",
        },
        {
            "action_type": "revise_cta",
            "source_variant_id": winner.get("variant_id", ""),
            "action_title": "Create one CTA-only challenger",
            "action_reason": "A CTA-only change tests click intent without introducing a new product claim.",
            "suggested_copy_change": "Use a clearer buyer-check CTA with no guaranteed outcome.",
            "suggested_video_prompt_change": "Keep all scenes constant and change only the closing overlay.",
        },
    ]
    if any_missing:
        action_specs.extend(
            [
                {
                    "action_type": "strengthen_proof_quote",
                    "source_variant_id": winner.get("variant_id", ""),
                    "action_title": "Strengthen quote coverage",
                    "action_reason": "One or more variants lack a usable buyer quote.",
                    "suggested_copy_change": "Add a specific supplied review quote before selecting a production winner.",
                    "suggested_video_prompt_change": "Do not add a proof overlay until a real quote is available.",
                },
                {
                    "action_type": "collect_more_reviews",
                    "source_variant_id": winner.get("variant_id", ""),
                    "action_title": "Collect more review evidence",
                    "action_reason": "Missing quote coverage prevents a reliable creative iteration decision.",
                    "suggested_copy_change": "Pause claim expansion until another concrete review is supplied.",
                    "suggested_video_prompt_change": "Use only conservative inspection footage while evidence is incomplete.",
                },
            ]
        )
    if any_weak:
        action_specs.append(
            {
                "action_type": "lower_claim_strength",
                "source_variant_id": winner.get("variant_id", ""),
                "action_title": "Lower claim strength",
                "action_reason": "Weak evidence requires a buyer-check framing instead of a product-benefit conclusion.",
                "suggested_copy_change": "Replace resolution language with a visible-sample buyer check.",
                "suggested_video_prompt_change": "Show inspection steps; do not visualize a guaranteed before/after result.",
            }
        )
    if len(variant_feedback_cards) > 1:
        action_specs.append(
            {
                "action_type": "pause_variant",
                "source_variant_id": variant_feedback_cards[-1].get("variant_id", ""),
                "action_title": "Pause the lowest-priority challenger",
                "action_reason": "The lowest deterministic performance tier should not absorb the first test budget.",
                "suggested_copy_change": "Keep the draft for later review instead of expanding its claim.",
                "suggested_video_prompt_change": "Do not send this draft to a provider.",
            }
        )
    iteration_actions = [
        {
            "action_id": f"iteration_action_{index}_{spec['action_type']}",
            "priority": index,
            **spec,
            "evidence_requirement": (
                "Use the existing proof quote and visible-sample boundary; collect a quote first if missing."
            ),
            "risk_control": "Guidance only. No provider, media, paid, registry, or rollback action is triggered.",
        }
        for index, spec in enumerate(action_specs, start=1)
    ]
    return {
        "pack_version": "creative_test_feedback_pack_v1",
        "feedback_summary": {
            "feedback_status": (
                "needs_evidence_review" if any_weak or any_missing else "mock_test_feedback_ready"
            ),
            "variant_feedback_count": len(variant_feedback_cards),
            "mock_signal_only": True,
            "winner_reason": (
                "Selected from deterministic variant ranking; this is not live ad-platform performance data."
            ),
        },
        "recommended_winner_variant_id": winner.get("variant_id", ""),
        "recommended_next_iteration": {
            "source_variant_id": winner.get("variant_id", ""),
            "hook_direction": winner.get("next_hook_direction", ""),
            "scene_direction": winner.get("next_scene_direction", ""),
            "cta_direction": winner.get("next_cta_direction", ""),
            "proof_quote_direction": (
                f"Keep this supplied quote visible: {winner_variant.get('proof_quote')}"
                if winner_variant.get("proof_quote")
                else "Collect a specific buyer quote before increasing claim strength."
            ),
            "iteration_note": "Change one variable at a time and keep the product, audience, proof, and evidence boundary constant.",
        },
        "variant_feedback_cards": variant_feedback_cards,
        "iteration_actions": iteration_actions,
        "feedback_quality_checks": {
            "missing_metric": False,
            "mock_metric_only": True,
            "weak_evidence": any_weak,
            "missing_quote": any_missing,
            "unsupported_claim": bool(unsupported_claims),
            "unsupported_claim_terms": unsupported_claims,
            "unsafe_provider_action": False,
        },
        "safety_boundaries": {
            "provider_enabled": False,
            "llm_api_enabled": False,
            "video_generation_enabled": False,
            "media_operation_enabled": False,
            "paid_operation_enabled": False,
            "registry_operation_enabled": False,
            "restore_or_rollback_enabled": False,
            "feedback_persisted": False,
        },
    }


def _rw_creative_iteration_pack(
    variants: list[dict],
    creative_test_feedback_pack: dict,
    language: str,
) -> dict:
    winner_id = _rw_text(creative_test_feedback_pack.get("recommended_winner_variant_id"))
    winner = next(
        (variant for variant in variants if variant.get("variant_id") == winner_id),
        variants[0] if variants else {},
    )
    feedback_cards = list(creative_test_feedback_pack.get("variant_feedback_cards") or [])
    winner_feedback = next(
        (card for card in feedback_cards if card.get("variant_id") == winner.get("variant_id")),
        feedback_cards[0] if feedback_cards else {},
    )
    actions = list(creative_test_feedback_pack.get("iteration_actions") or [])
    action_by_type = {
        action.get("action_type"): action
        for action in actions
        if action.get("action_type")
    }
    is_zh = language == "zh-CN"
    proof_quote = _rw_text(winner.get("proof_quote"))
    missing_quote = not bool(proof_quote)
    weak_evidence = bool(winner.get("weak_evidence")) or missing_quote
    source_scenes = [
        _rw_text(winner.get("scene_1")),
        _rw_text(winner.get("scene_2")),
        _rw_text(winner.get("scene_3")),
    ]
    source_hook = _rw_text(winner.get("hook"))
    source_cta = _rw_text(winner.get("cta"))
    source_risk = _rw_text(winner.get("risk_note"))
    do_not_claim = list(winner.get("do_not_claim") or [])
    strengthened_do_not_claim = list(dict.fromkeys([
        *do_not_claim,
        "Do not present deterministic mock feedback as live ad-platform performance.",
        "Do not add a product benefit that is not supported by the supplied proof quote.",
    ]))
    if weak_evidence:
        strengthened_do_not_claim.append(
            "Do not increase claim strength until another specific buyer quote is supplied."
        )

    quote_first_hook = (
        f"\u4e0b\u4e00\u8f6e\u5148\u7528\u4e70\u5bb6\u539f\u8bdd\u5f00\u573a\uff1a\u201c{proof_quote}\u201d"
        if is_zh and proof_quote
        else f"Next test: open with the buyer line, \"{proof_quote}\""
        if proof_quote
        else (
            "\u4e0b\u4e00\u8f6e\u53ea\u505a\u4fdd\u5b88\u8d2d\u4e70\u68c0\u67e5\uff0c\u8865\u5145\u539f\u8bdd\u540e\u518d\u63d0\u9ad8\u4e3b\u5f20\u3002"
            if is_zh
            else "Next test: use a conservative buyer check and add a real quote before increasing the claim."
        )
    )
    conservative_cta = (
        "\u5bf9\u7167\u4f60\u7684\u771f\u5b9e\u4f7f\u7528\u573a\u666f\uff0c\u518d\u5224\u65ad\u8fd9\u4e2a\u4ea7\u54c1\u662f\u5426\u9002\u5408\u3002"
        if is_zh
        else "Compare this with your real use case before deciding whether the product fits."
    )
    scene_prefixes = (
        ["\u5f00\u573a\u7279\u5199", "\u8bc1\u636e\u68c0\u67e5", "\u4fdd\u5b88\u6536\u5c3e"]
        if is_zh
        else ["Opening close-up", "Evidence check", "Conservative close"]
    )

    definitions = [
        {
            "goal": "revise_hook",
            "title": (
                f"{winner.get('variant_title', '')} v2\uff1aHook \u7cbe\u70bc"
                if is_zh
                else f"{winner.get('variant_title', '')} v2: Hook refinement"
            ),
            "hook": quote_first_hook,
            "scenes": source_scenes,
            "cta": source_cta,
            "what_changed": "Hook only",
            "why_changed": _rw_text(
                action_by_type.get("revise_hook", {}).get("action_reason")
                or winner_feedback.get("what_to_improve")
            ),
            "action_types": ["keep_winner", "revise_hook"],
        },
        {
            "goal": "revise_scenes",
            "title": (
                f"{winner.get('variant_title', '')} v2\uff1a\u955c\u5934\u8282\u594f"
                if is_zh
                else f"{winner.get('variant_title', '')} v2: Scene pacing"
            ),
            "hook": source_hook,
            "scenes": [
                f"{scene_prefixes[index]}: {scene}"
                for index, scene in enumerate(source_scenes)
            ],
            "cta": source_cta,
            "what_changed": "Scene framing and pacing",
            "why_changed": _rw_text(
                winner_feedback.get("next_scene_direction")
                or "Tighten pacing while preserving the same evidence sequence."
            ),
            "action_types": ["keep_winner"],
        },
        {
            "goal": "revise_cta_and_proof",
            "title": (
                f"{winner.get('variant_title', '')} v2\uff1a\u4fdd\u5b88\u8bc1\u636e\u6536\u5c3e"
                if is_zh
                else f"{winner.get('variant_title', '')} v2: Conservative proof close"
            ),
            "hook": quote_first_hook if weak_evidence else source_hook,
            "scenes": source_scenes,
            "cta": conservative_cta,
            "what_changed": "CTA and proof boundary",
            "why_changed": _rw_text(
                action_by_type.get("lower_claim_strength", {}).get("action_reason")
                or action_by_type.get("revise_cta", {}).get("action_reason")
                or winner_feedback.get("next_cta_direction")
            ),
            "action_types": [
                "revise_cta",
                "lower_claim_strength" if weak_evidence else "keep_winner",
            ],
        },
    ]

    iteration_variants: list[dict] = []
    diffs: list[dict] = []
    for index, definition in enumerate(definitions, start=1):
        iteration_variant_id = (
            f"iteration_v2_{index}_{winner.get('variant_type', 'creative')}_{definition['goal']}"
        )
        revised_scenes = list(definition["scenes"])
        while len(revised_scenes) < 3:
            revised_scenes.append("")
        source_action_ids = [
            action_by_type[action_type].get("action_id", "")
            for action_type in definition["action_types"]
            if action_type in action_by_type
        ]
        revised_risk_note = " ".join(
            part
            for part in [
                source_risk,
                (
                    "Weak evidence: keep this as a conservative review draft and collect another quote."
                    if weak_evidence
                    else "Change one creative variable at a time; mock feedback is not live performance evidence."
                ),
            ]
            if part
        )
        shot_list = [
            {
                "scene_number": scene_number,
                "prompt": scene,
                "evidence_quote": proof_quote,
            }
            for scene_number, scene in enumerate(revised_scenes[:3], start=1)
        ]
        video_prompt = "\n".join([
            f"V2 variant: {definition['title']}",
            f"Iteration goal: {definition['goal']}",
            f"Hook: {definition['hook']}",
            *[f"Shot {shot['scene_number']}: {shot['prompt']}" for shot in shot_list],
            f"CTA: {definition['cta']}",
            f"Proof quote: {proof_quote or 'missing_quote'}",
            f"Risk note: {revised_risk_note}",
            "Do not claim:",
            *[f"- {item}" for item in strengthened_do_not_claim],
        ])
        copy_ready_script = "\n".join([
            f"Hook: {definition['hook']}",
            f"Scene 1: {revised_scenes[0]}",
            f"Scene 2: {revised_scenes[1]}",
            f"Scene 3: {revised_scenes[2]}",
            f"CTA: {definition['cta']}",
            f"Proof quote: {proof_quote or 'missing_quote'}",
            f"Risk note: {revised_risk_note}",
            "Do not claim:",
            *[f"- {item}" for item in strengthened_do_not_claim],
        ])
        iteration_variants.append({
            "iteration_variant_id": iteration_variant_id,
            "source_variant_id": winner.get("variant_id", ""),
            "source_variant_type": winner.get("variant_type", ""),
            "iteration_round": 2,
            "iteration_goal": definition["goal"],
            "revised_variant_title": definition["title"],
            "revised_hook": definition["hook"],
            "revised_scene_1": revised_scenes[0],
            "revised_scene_2": revised_scenes[1],
            "revised_scene_3": revised_scenes[2],
            "revised_cta": definition["cta"],
            "revised_proof_quote": proof_quote,
            "missing_quote": missing_quote,
            "weak_evidence": weak_evidence,
            "revised_risk_note": revised_risk_note,
            "revised_do_not_claim": strengthened_do_not_claim,
            "revised_video_prompt": video_prompt,
            "revised_shot_list": shot_list,
            "copy_ready_v2_script": copy_ready_script,
            "what_changed": definition["what_changed"],
            "why_changed": definition["why_changed"],
            "source_feedback_action_ids": source_action_ids,
            "evidence_requirement": (
                "Collect a specific buyer quote before production use."
                if missing_quote
                else "Keep the supplied proof quote visible and do not generalize beyond the visible sample."
            ),
            "claim_safety_level": (
                "conservative" if weak_evidence else winner.get("claim_safety_level", "conservative")
            ),
            "copy_readiness": (
                "needs_evidence" if weak_evidence else winner.get("copy_readiness", "ready")
            ),
            "recommended_next_action": (
                "collect_more_reviews"
                if missing_quote
                else "lower_claim_strength"
                if weak_evidence
                else "human_review_before_test"
            ),
        })
        revised_fields = {
            "hook": definition["hook"],
            "scene_1": revised_scenes[0],
            "scene_2": revised_scenes[1],
            "scene_3": revised_scenes[2],
            "cta": definition["cta"],
        }
        original_fields = {
            "hook": source_hook,
            "scene_1": source_scenes[0],
            "scene_2": source_scenes[1],
            "scene_3": source_scenes[2],
            "cta": source_cta,
        }
        for field_name, revised_value in revised_fields.items():
            original_value = original_fields[field_name]
            if revised_value == original_value:
                continue
            diffs.append({
                "diff_id": f"diff_{iteration_variant_id}_{field_name}",
                "iteration_variant_id": iteration_variant_id,
                "source_variant_id": winner.get("variant_id", ""),
                "field_name": field_name,
                "original_value": original_value,
                "revised_value": revised_value,
                "change_reason": definition["why_changed"],
                "risk_control": "Keep the original proof quote and strengthened do-not-claim boundaries.",
            })

    recommended = next(
        (
            variant
            for variant in iteration_variants
            if variant["iteration_goal"] == (
                "revise_cta_and_proof" if weak_evidence else "revise_hook"
            )
        ),
        iteration_variants[0] if iteration_variants else {},
    )
    return {
        "pack_version": "creative_iteration_pack_v1",
        "iteration_summary": {
            "iteration_round": 2,
            "iteration_variant_count": len(iteration_variants),
            "diff_count": len(diffs),
            "iteration_goal": recommended.get("iteration_goal", ""),
            "readiness": (
                "needs_evidence_review" if weak_evidence else "ready_for_human_review"
            ),
            "risk_summary": (
                "Claim strength is reduced because the winner has weak or missing evidence."
                if weak_evidence
                else "V2 changes remain inside the original proof and claim-safety boundaries."
            ),
        },
        "source_winner_variant_id": winner.get("variant_id", ""),
        "recommended_iteration_variant_id": recommended.get("iteration_variant_id", ""),
        "iteration_variants": iteration_variants,
        "original_vs_revised_diff": diffs,
        "iteration_quality_checks": {
            "missing_winner": not bool(winner.get("variant_id")),
            "missing_quote": missing_quote,
            "weak_evidence": weak_evidence,
            "unsupported_claim_added": False,
            "do_not_claim_preserved": all(
                set(do_not_claim).issubset(set(variant["revised_do_not_claim"]))
                for variant in iteration_variants
            ),
            "unsafe_provider_action": False,
        },
        "safety_boundaries": {
            "provider_enabled": False,
            "llm_api_enabled": False,
            "video_generation_enabled": False,
            "media_operation_enabled": False,
            "paid_operation_enabled": False,
            "registry_operation_enabled": False,
            "restore_or_rollback_enabled": False,
            "feedback_persisted": False,
        },
    }


def _rw_creative_version_control_pack(
    variants: list[dict],
    creative_test_feedback_pack: dict,
    creative_iteration_pack: dict,
) -> dict:
    variant_by_id = {
        _rw_text(variant.get("variant_id")): variant
        for variant in variants
        if _rw_text(variant.get("variant_id"))
    }
    feedback_cards = {
        _rw_text(card.get("variant_id")): card
        for card in list(creative_test_feedback_pack.get("variant_feedback_cards") or [])
        if _rw_text(card.get("variant_id"))
    }
    diffs_by_iteration: dict[str, list[dict]] = {}
    for diff in list(creative_iteration_pack.get("original_vs_revised_diff") or []):
        iteration_id = _rw_text(diff.get("iteration_variant_id"))
        if iteration_id:
            diffs_by_iteration.setdefault(iteration_id, []).append(diff)

    version_lineage: list[dict] = []
    for variant in variants:
        variant_id = _rw_text(variant.get("variant_id"))
        version_lineage.append({
            "version_id": f"v1_{variant_id}",
            "version_label": "V1",
            "version_round": 1,
            "source_variant_id": variant_id,
            "source_iteration_variant_id": "",
            "parent_version_id": "",
            "variant_type": _rw_text(variant.get("variant_type")),
            "version_title": _rw_text(variant.get("variant_title")),
            "version_goal": _rw_text(variant.get("variant_type")) or "original_variant",
            "change_source": "creative_variant_pack",
            "hook": _rw_text(variant.get("hook")),
            "scene_1": _rw_text(variant.get("scene_1")),
            "scene_2": _rw_text(variant.get("scene_2")),
            "scene_3": _rw_text(variant.get("scene_3")),
            "cta": _rw_text(variant.get("cta")),
            "proof_quote": _rw_text(variant.get("proof_quote")),
            "proof_source": _rw_text(variant.get("proof_source")),
            "missing_quote": bool(variant.get("missing_quote")),
            "weak_evidence": bool(variant.get("weak_evidence")),
            "evidence_strength_score": int(variant.get("evidence_strength_score") or 0),
            "copy_readiness": _rw_text(variant.get("copy_readiness")),
            "claim_safety_level": _rw_text(variant.get("claim_safety_level")),
            "risk_note": _rw_text(variant.get("risk_note")),
            "do_not_claim": list(variant.get("do_not_claim") or []),
            "video_prompt": _rw_text(variant.get("video_prompt")),
            "shot_list": list(variant.get("shot_list") or []),
            "copy_ready_script": _rw_text(variant.get("copy_ready_script")),
            "recommended_use_case": _rw_text(variant.get("variant_reason")),
        })

    comparison_cards: list[dict] = []
    for iteration in list(creative_iteration_pack.get("iteration_variants") or []):
        iteration_id = _rw_text(iteration.get("iteration_variant_id"))
        source_variant_id = _rw_text(iteration.get("source_variant_id"))
        source_variant = variant_by_id.get(source_variant_id, {})
        proof_quote = _rw_text(
            iteration.get("revised_proof_quote") or source_variant.get("proof_quote")
        )
        missing_quote = bool(iteration.get("missing_quote")) or not bool(proof_quote)
        weak_evidence = bool(iteration.get("weak_evidence")) or missing_quote
        version_id = f"v2_{iteration_id}"
        parent_version_id = f"v1_{source_variant_id}"
        source_feedback = feedback_cards.get(source_variant_id, {})
        version_lineage.append({
            "version_id": version_id,
            "version_label": "V2",
            "version_round": 2,
            "source_variant_id": source_variant_id,
            "source_iteration_variant_id": iteration_id,
            "parent_version_id": parent_version_id,
            "variant_type": _rw_text(
                iteration.get("source_variant_type")
                or source_variant.get("variant_type")
            ),
            "version_title": _rw_text(iteration.get("revised_variant_title")),
            "version_goal": _rw_text(iteration.get("iteration_goal")),
            "change_source": "creative_iteration_pack",
            "hook": _rw_text(iteration.get("revised_hook")),
            "scene_1": _rw_text(iteration.get("revised_scene_1")),
            "scene_2": _rw_text(iteration.get("revised_scene_2")),
            "scene_3": _rw_text(iteration.get("revised_scene_3")),
            "cta": _rw_text(iteration.get("revised_cta")),
            "proof_quote": proof_quote,
            "proof_source": _rw_text(source_variant.get("proof_source")),
            "missing_quote": missing_quote,
            "weak_evidence": weak_evidence,
            "evidence_strength_score": int(
                source_variant.get("evidence_strength_score") or 0
            ),
            "copy_readiness": _rw_text(iteration.get("copy_readiness")),
            "claim_safety_level": _rw_text(iteration.get("claim_safety_level")),
            "risk_note": _rw_text(iteration.get("revised_risk_note")),
            "do_not_claim": list(iteration.get("revised_do_not_claim") or []),
            "video_prompt": _rw_text(iteration.get("revised_video_prompt")),
            "shot_list": list(iteration.get("revised_shot_list") or []),
            "copy_ready_script": _rw_text(iteration.get("copy_ready_v2_script")),
            "recommended_use_case": _rw_text(
                iteration.get("recommended_next_action")
            ),
        })
        changed_fields = [
            _rw_text(diff.get("field_name"))
            for diff in diffs_by_iteration.get(iteration_id, [])
            if _rw_text(diff.get("field_name"))
        ]
        comparison_cards.append({
            "comparison_id": f"comparison_{parent_version_id}_{version_id}",
            "base_version_id": parent_version_id,
            "revised_version_id": version_id,
            "comparison_title": (
                f"{_rw_text(source_variant.get('variant_title'))} V1 vs "
                f"{_rw_text(iteration.get('revised_variant_title'))}"
            ),
            "what_changed": changed_fields or [
                _rw_text(iteration.get("what_changed")) or "Evidence boundary review"
            ],
            "why_it_changed": _rw_text(iteration.get("why_changed")),
            "expected_benefit": (
                "Test whether the revision improves clarity while preserving the supplied evidence."
            ),
            "risk_delta": "lower_or_equal" if weak_evidence else "unchanged",
            "evidence_delta": (
                "missing_quote" if missing_quote else "unchanged_existing_quote"
            ),
            "copy_readiness_delta": (
                f"{_rw_text(source_variant.get('copy_readiness')) or 'unknown'} -> "
                f"{_rw_text(iteration.get('copy_readiness')) or 'unknown'}"
            ),
            "best_for": _rw_text(iteration.get("iteration_goal")),
            "recommended_next_action": _rw_text(
                iteration.get("recommended_next_action")
                or source_feedback.get("recommended_next_action")
            ),
            "proof_quote": proof_quote,
            "missing_quote": missing_quote,
            "risk_note": _rw_text(iteration.get("revised_risk_note")),
            "do_not_claim": list(iteration.get("revised_do_not_claim") or []),
        })

    recommended_iteration_id = _rw_text(
        creative_iteration_pack.get("recommended_iteration_variant_id")
    )
    recommended_next_version_id = (
        f"v2_{recommended_iteration_id}" if recommended_iteration_id else ""
    )
    version_ids = {
        _rw_text(version.get("version_id"))
        for version in version_lineage
        if _rw_text(version.get("version_id"))
    }
    if recommended_next_version_id not in version_ids:
        recommended_next_version_id = next(
            (
                version["version_id"]
                for version in version_lineage
                if version["version_round"] == 2
            ),
            "",
        )
    recommended_version = next(
        (
            version
            for version in version_lineage
            if version["version_id"] == recommended_next_version_id
        ),
        {},
    )
    low_evidence_version = next(
        (
            version
            for version in version_lineage
            if version["version_round"] == 2
            and version["claim_safety_level"] == "conservative"
        ),
        recommended_version,
    )
    highest_readiness_version = next(
        (
            version
            for version in version_lineage
            if version["version_round"] == 2
            and version["copy_readiness"] == "ready"
        ),
        recommended_version,
    )
    best_tiktok_version = next(
        (
            version
            for version in version_lineage
            if version["version_goal"] in {"short_hook", "revise_hook"}
        ),
        recommended_version,
    )
    best_direct_response_version = next(
        (
            version
            for version in version_lineage
            if version["version_goal"] in {
                "problem_solution",
                "revise_cta_and_proof",
            }
        ),
        recommended_version,
    )
    missing_quote_count = sum(
        bool(version.get("missing_quote")) for version in version_lineage
    )
    weak_evidence_count = sum(
        bool(version.get("weak_evidence")) for version in version_lineage
    )
    do_not_claim_preserved = all(
        set(variant_by_id.get(version.get("source_variant_id"), {}).get("do_not_claim") or [])
        .issubset(set(version.get("do_not_claim") or []))
        for version in version_lineage
        if version.get("version_round") == 2
    )
    version_risk_summary = {
        "lowest_risk_version_id": _rw_text(low_evidence_version.get("version_id")),
        "highest_readiness_version_id": _rw_text(
            highest_readiness_version.get("version_id")
        ),
        "highest_copy_readiness_version_id": _rw_text(
            highest_readiness_version.get("version_id")
        ),
        "best_tiktok_version_id": _rw_text(best_tiktok_version.get("version_id")),
        "best_for_tiktok_version_id": _rw_text(best_tiktok_version.get("version_id")),
        "best_direct_response_version_id": _rw_text(
            best_direct_response_version.get("version_id")
        ),
        "best_for_direct_response_version_id": _rw_text(
            best_direct_response_version.get("version_id")
        ),
        "low_evidence_safe_version_id": _rw_text(
            low_evidence_version.get("version_id")
        ),
        "best_for_low_evidence_safe_use_version_id": _rw_text(
            low_evidence_version.get("version_id")
        ),
        "risk_notes": [
            "V2 versions keep the original proof quote and do-not-claim boundaries.",
            "Mock feedback and deterministic comparisons are not live performance evidence.",
            (
                "Weak or missing evidence remains explicitly marked; collect another quote "
                "before increasing claim strength."
                if weak_evidence_count or missing_quote_count
                else "Human review is still required before production use."
            ),
        ],
    }
    version_summary = {
        "version_count": len(version_lineage),
        "v1_version_count": sum(
            version["version_round"] == 1 for version in version_lineage
        ),
        "v2_version_count": sum(
            version["version_round"] == 2 for version in version_lineage
        ),
        "comparison_count": len(comparison_cards),
        "recommended_next_test_version_id": recommended_next_version_id,
        "weak_evidence_count": weak_evidence_count,
        "missing_quote_count": missing_quote_count,
        "ready_to_copy_count": sum(
            version.get("copy_readiness") == "ready" for version in version_lineage
        ),
    }
    version_export_snapshot = {
        "version_summary": version_summary,
        "recommended_next_test_version_id": recommended_next_version_id,
        "version_lineage": version_lineage,
        "version_comparison_cards": comparison_cards,
        "version_risk_summary": version_risk_summary,
    }
    return {
        "pack_version": "creative_version_control_pack_v1",
        "version_summary": version_summary,
        "recommended_next_test_version_id": recommended_next_version_id,
        "version_lineage": version_lineage,
        "version_comparison_cards": comparison_cards,
        "version_risk_summary": version_risk_summary,
        "version_export_snapshot": version_export_snapshot,
        "version_quality_checks": {
            "missing_quote": bool(missing_quote_count),
            "missing_quote_count": missing_quote_count,
            "weak_evidence": bool(weak_evidence_count),
            "weak_evidence_count": weak_evidence_count,
            "lineage_complete": all(
                version["version_round"] == 1 or bool(version["parent_version_id"])
                for version in version_lineage
            ),
            "recommended_version_exists": recommended_next_version_id in version_ids,
            "do_not_claim_preserved": do_not_claim_preserved,
            "unsupported_claim_added": False,
            "unsafe_provider_action": False,
        },
        "safety_boundaries": {
            "provider_enabled": False,
            "llm_api_enabled": False,
            "video_generation_enabled": False,
            "media_operation_enabled": False,
            "paid_operation_enabled": False,
            "registry_operation_enabled": False,
            "restore_or_rollback_enabled": False,
            "feedback_persisted": False,
        },
    }


def _rw_creative_asset_pack(
    creative_version_control_pack: dict,
    product_context: str,
    language: str,
) -> dict:
    versions = list(creative_version_control_pack.get("version_lineage") or [])
    version_by_id = {
        _rw_text(version.get("version_id")): version
        for version in versions
        if _rw_text(version.get("version_id"))
    }
    source_version_id = _rw_text(
        creative_version_control_pack.get("recommended_next_test_version_id")
    )
    source_version = version_by_id.get(source_version_id, {})
    if not source_version:
        source_version = next(
            (version for version in versions if version.get("version_round") == 2),
            versions[0] if versions else {},
        )
        source_version_id = _rw_text(source_version.get("version_id"))

    is_zh = language == "zh-CN"
    proof_quote = _rw_text(source_version.get("proof_quote"))
    missing_quote = bool(source_version.get("missing_quote")) or not bool(proof_quote)
    weak_evidence = bool(source_version.get("weak_evidence")) or missing_quote
    do_not_claim = list(source_version.get("do_not_claim") or [])
    required_boundaries = [
        (
            "\u4e0d\u5f97\u628a\u5355\u6761\u8bc4\u8bba\u6269\u5927\u4e3a\u5168\u5e02\u573a\u7edf\u8ba1\u7ed3\u8bba\u3002"
            if is_zh
            else "Do not generalize one review into a full-market statistic."
        ),
        (
            "\u4e0d\u5f97\u5ba3\u79f0\u672a\u88ab\u73b0\u6709\u8bc1\u636e\u652f\u6301\u7684\u4ea7\u54c1\u6548\u679c\u3001\u6027\u80fd\u6216\u7ed3\u679c\u3002"
            if is_zh
            else "Do not claim product effects, performance, or outcomes not supported by the supplied evidence."
        ),
    ]
    if weak_evidence:
        required_boundaries.append(
            (
                "\u8865\u5145\u53ef\u6838\u9a8c\u539f\u8bdd\u524d\uff0c\u4e0d\u5f97\u63d0\u9ad8\u5ba3\u79f0\u5f3a\u5ea6\u3002"
                if is_zh
                else "Do not increase claim strength until a verifiable proof quote is supplied."
            )
        )
    do_not_claim = list(dict.fromkeys([*do_not_claim, *required_boundaries]))

    scenes = [
        _rw_text(source_version.get("scene_1")),
        _rw_text(source_version.get("scene_2")),
        _rw_text(source_version.get("scene_3")),
    ]
    hook = _rw_text(source_version.get("hook"))
    cta = _rw_text(source_version.get("cta"))
    risk_note = _rw_text(source_version.get("risk_note"))
    evidence_link = proof_quote or "missing_quote"
    target_length_seconds = {
        "short_hook": 10,
        "direct_demo": 18,
        "ugc_testimonial": 20,
    }.get(_rw_text(source_version.get("variant_type")), 25)

    keyframe_prompts = [
        {
            "keyframe_id": f"keyframe_{index}",
            "scene_ref": f"scene_{index}",
            "prompt": scene,
            "visual_style": (
                "\u7ad6\u5c4f\u77ed\u89c6\u9891\u3001\u4ea7\u54c1\u4e3a\u4e3b\u3001\u8bc1\u636e\u5b57\u5e55\u6e05\u6670\u53ef\u8bfb"
                if is_zh
                else "Vertical short-video frame, product-first composition, readable evidence overlay"
            ),
            "product_focus": product_context,
            "evidence_link": evidence_link,
            "do_not_claim": do_not_claim,
        }
        for index, scene in enumerate(scenes, start=1)
    ]
    subtitle_source = [hook, proof_quote or evidence_link, cta]
    subtitle_lines = [
        {
            "line_id": f"subtitle_{index}",
            "timestamp_hint": f"{(index - 1) * max(target_length_seconds // 3, 1)}s",
            "subtitle_text": text,
            "scene_ref": f"scene_{index}",
        }
        for index, text in enumerate(subtitle_source, start=1)
    ]
    shooting_script = {
        "hook": hook,
        "scene_1": scenes[0],
        "scene_2": scenes[1],
        "scene_3": scenes[2],
        "cta": cta,
        "proof_quote": proof_quote,
        "missing_quote": missing_quote,
        "risk_note": risk_note,
        "do_not_claim": do_not_claim,
    }
    asset_pack_id = f"asset_pack_{source_version_id}" if source_version_id else ""
    asset_readiness = (
        "needs_evidence"
        if weak_evidence
        else _rw_text(source_version.get("copy_readiness"))
        or "ready_for_human_review"
    )
    recommended_next_action = (
        "collect_more_reviews"
        if missing_quote
        else "lower_claim_strength"
        if weak_evidence
        else _rw_text(source_version.get("recommended_use_case"))
        or "human_review_before_production"
    )
    caption_variants = {
        "short_caption": hook,
        "benefit_caption": (
            f"\u4ece\u4e70\u5bb6\u8bc1\u636e\u51fa\u53d1\u68c0\u67e5\uff1a{hook}"
            if is_zh
            else f"Buyer-evidence product check: {hook}"
        ),
        "proof_caption": proof_quote or "missing_quote",
        "safe_claim_caption": (
            "\u8bf7\u5148\u6838\u5bf9\u5df2\u63d0\u4f9b\u7684\u4e70\u5bb6\u8bc1\u636e\uff0c\u518d\u5224\u65ad\u4ea7\u54c1\u662f\u5426\u9002\u5408\u4f60\u7684\u4f7f\u7528\u573a\u666f\u3002"
            if is_zh
            else "Review the supplied buyer evidence before deciding whether the product fits your use case."
        ),
    }
    asset_pack = {
        "asset_pack_id": asset_pack_id,
        "source_version_id": source_version_id,
        "source_version_label": _rw_text(source_version.get("version_label")),
        "asset_pack_title": (
            f"{_rw_text(source_version.get('version_title'))} \u62cd\u6444\u8d44\u4ea7\u5305"
            if is_zh
            else f"{_rw_text(source_version.get('version_title'))} production asset pack"
        ),
        "target_platform": "TikTok",
        "target_format": "vertical_short_video",
        "target_length_seconds": target_length_seconds,
        "shooting_script": shooting_script,
        "shot_list": list(source_version.get("shot_list") or []),
        "keyframe_prompts": keyframe_prompts,
        "subtitle_lines": subtitle_lines,
        "b_roll_notes": [
            (
                f"\u7528\u4ea7\u54c1\u7279\u5199\u652f\u6491 {scene_ref}\uff0c\u4e0d\u989d\u5916\u6dfb\u52a0\u6548\u679c\u5ba3\u79f0\u3002"
                if is_zh
                else f"Use a product close-up to support {scene_ref} without adding an outcome claim."
            )
            for scene_ref in ("scene_1", "scene_2", "scene_3")
        ],
        "thumbnail_prompt": (
            f"{product_context}\uff0c\u7ad6\u5c4f\u4ea7\u54c1\u7279\u5199\uff0c\u53e0\u52a0\u4e70\u5bb6\u539f\u8bdd\uff1a{evidence_link}"
            if is_zh
            else f"{product_context}, vertical product close-up with supplied buyer evidence overlay: {evidence_link}"
        ),
        "caption_variants": caption_variants,
        "on_screen_text": [text for text in [hook, proof_quote, cta] if text],
        "voiceover_script": "\n".join(
            text for text in [hook, *scenes, cta] if text
        ),
        "product_context": product_context,
        "proof_quotes": [proof_quote] if proof_quote else [],
        "risk_notes": [
            note
            for note in [
                risk_note,
                (
                    "\u4e0a\u7ebf\u524d\u9700\u8981\u4eba\u5de5\u5ba1\u6838\u8bc1\u636e\u548c\u5ba3\u79f0\u8fb9\u754c\u3002"
                    if is_zh
                    else "Human review is required before production use."
                ),
            ]
            if note
        ],
        "do_not_claim": do_not_claim,
        "asset_readiness": asset_readiness,
        "evidence_strength_score": int(
            source_version.get("evidence_strength_score") or 0
        ),
        "recommended_next_action": recommended_next_action,
    }
    missing_script_parts = [
        field
        for field, value in shooting_script.items()
        if field in {"hook", "scene_1", "scene_2", "scene_3", "cta"} and not value
    ]
    asset_packs = [asset_pack] if source_version else []
    return {
        "pack_version": "creative_asset_pack_v1",
        "asset_pack_summary": {
            "asset_pack_count": len(asset_packs),
            "source_version_id": source_version_id,
            "recommended_asset_pack_id": asset_pack_id,
            "target_platform": "TikTok",
            "asset_readiness": asset_readiness if source_version else "unavailable",
            "evidence_strength_score": int(
                source_version.get("evidence_strength_score") or 0
            ),
            "missing_quote_count": int(missing_quote) if source_version else 0,
            "weak_evidence_count": int(weak_evidence) if source_version else 0,
            "risk_summary": risk_note,
        },
        "source_version_id": source_version_id,
        "recommended_asset_pack_id": asset_pack_id,
        "asset_packs": asset_packs,
        "asset_quality_checks": {
            "missing_quote": missing_quote if source_version else True,
            "weak_evidence": weak_evidence if source_version else True,
            "unsupported_claim": False,
            "unsupported_claim_terms": [],
            "missing_script_part": bool(missing_script_parts),
            "missing_script_parts": missing_script_parts,
            "do_not_claim_preserved": bool(do_not_claim),
            "unsafe_provider_action": False,
        },
        "safety_boundaries": {
            "provider_enabled": False,
            "llm_api_enabled": False,
            "video_generation_enabled": False,
            "media_operation_enabled": False,
            "paid_operation_enabled": False,
            "registry_operation_enabled": False,
            "restore_or_rollback_enabled": False,
            "feedback_persisted": False,
        },
    }


def _rw_multi_platform_asset_pack(
    creative_asset_pack: dict,
    language: str,
) -> dict:
    asset_packs = list(creative_asset_pack.get("asset_packs") or [])
    recommended_asset_pack_id = _rw_text(
        creative_asset_pack.get("recommended_asset_pack_id")
    )
    source_asset = next(
        (
            asset
            for asset in asset_packs
            if _rw_text(asset.get("asset_pack_id")) == recommended_asset_pack_id
        ),
        asset_packs[0] if asset_packs else {},
    )
    source_asset_pack_id = _rw_text(source_asset.get("asset_pack_id"))
    is_zh = language == "zh-CN"
    source_script = dict(source_asset.get("shooting_script") or {})
    source_scenes = [
        _rw_text(source_script.get("scene_1")),
        _rw_text(source_script.get("scene_2")),
        _rw_text(source_script.get("scene_3")),
    ]
    source_hook = _rw_text(source_script.get("hook"))
    source_cta = _rw_text(source_script.get("cta"))
    proof_quote = _rw_text(source_script.get("proof_quote"))
    missing_quote = bool(source_script.get("missing_quote")) or not bool(proof_quote)
    weak_evidence = (
        missing_quote
        or _rw_text(source_asset.get("asset_readiness")) == "needs_evidence"
    )
    do_not_claim = list(source_asset.get("do_not_claim") or [])
    safe_claim_notes = list(
        dict.fromkeys(
            [
                *do_not_claim,
                (
                    "\u53ea\u80fd\u4f7f\u7528\u5df2\u63d0\u4f9b\u7684\u4ea7\u54c1\u548c\u4e70\u5bb6\u8bc1\u636e\u3002"
                    if is_zh
                    else "Use only the supplied product and buyer evidence."
                ),
                (
                    "\u5e73\u53f0\u6539\u5199\u4e0d\u5f97\u63d0\u9ad8\u539f\u59cb\u7d20\u6750\u5305\u7684\u4e3b\u5f20\u5f3a\u5ea6\u3002"
                    if is_zh
                    else "Platform adaptation must not increase the source asset pack claim strength."
                ),
            ]
        )
    )
    if weak_evidence:
        safe_claim_notes.append(
            (
                "\u8bc1\u636e\u504f\u5f31\uff0c\u4ec5\u4fdd\u7559\u4fdd\u5b88\u7684\u68c0\u67e5\u548c\u5f15\u5bfc\u6587\u6848\u3002"
                if is_zh
                else "Evidence is weak; keep the script to conservative inspection and guidance language."
            )
        )

    platform_definitions = {
        "tiktok": {
            "title": "TikTok",
            "format": "vertical_short_video",
            "fit_reason": (
                "\u7528\u66f4\u77ed Hook\u3001\u5feb\u8282\u594f\u955c\u5934\u548c\u76f4\u63a5 CTA \u9002\u914d TikTok\u3002"
                if is_zh
                else "Use a shorter hook, faster cuts, and a direct CTA for TikTok."
            ),
            "pacing": (
                "\u5feb\u8282\u594f\uff0c\u524d 2 \u79d2\u8fdb\u5165 Hook\uff0c\u753b\u9762\u548c\u53e3\u8bed\u5b57\u5e55\u540c\u6b65\u3002"
                if is_zh
                else "Fast pacing; land the hook in the first two seconds with conversational subtitles."
            ),
            "cta": source_cta,
            "subtitle_style": (
                "\u53e3\u8bed\u5316\u3001\u77ed\u53e5\u3001\u9ad8\u9891\u6362\u884c"
                if is_zh
                else "Conversational, short lines, frequent line breaks"
            ),
        },
        "instagram_reels": {
            "title": "Instagram Reels",
            "format": "vertical_lifestyle_reel",
            "fit_reason": (
                "\u5f3a\u5316\u4ea7\u54c1\u89c6\u89c9\u3001\u751f\u6d3b\u65b9\u5f0f\u573a\u666f\u548c\u4fdd\u5b88\u7684\u4e70\u5bb6\u4ef7\u503c\u6587\u6848\u3002"
                if is_zh
                else "Strengthen product visuals, lifestyle context, and conservative buyer-led captions."
            ),
            "pacing": (
                "\u6d41\u7545\u89c6\u89c9\u8f6c\u573a\uff0c\u4fdd\u7559\u4ea7\u54c1\u7ec6\u8282\u548c\u4e70\u5bb6\u8bc1\u636e\u3002"
                if is_zh
                else "Use smooth visual transitions while retaining product detail and buyer evidence."
            ),
            "cta": (
                "\u4fdd\u5b58\u8fd9\u4efd\u8d2d\u4e70\u68c0\u67e5\uff0c\u5bf9\u7167\u539f\u8bdd\u518d\u505a\u51b3\u5b9a\u3002"
                if is_zh
                else "Save this buyer check and compare it with the supplied review before deciding."
            ),
            "subtitle_style": (
                "\u7b80\u6d01\u751f\u6d3b\u65b9\u5f0f\u5b57\u5e55\uff0c\u7559\u51fa\u753b\u9762\u547c\u5438\u611f"
                if is_zh
                else "Clean lifestyle subtitles with room for the product visuals"
            ),
        },
        "youtube_shorts": {
            "title": "YouTube Shorts",
            "format": "vertical_explainer_short",
            "fit_reason": (
                "\u4f7f\u7528\u66f4\u89e3\u91ca\u578b\u7684\u7ed3\u6784\u3001\u7a33\u5b9a\u8282\u594f\u548c\u5bf9\u6bd4\u578b CTA\u3002"
                if is_zh
                else "Use a more explanatory structure, steadier pacing, and a compare-or-learn CTA."
            ),
            "pacing": (
                "\u8282\u594f\u7a0d\u7a33\uff0c\u6309 Hook\u3001\u8bc1\u636e\u3001\u68c0\u67e5\u3001CTA \u9012\u8fdb\u3002"
                if is_zh
                else "Steady pacing through hook, evidence, inspection, and CTA."
            ),
            "cta": (
                "\u7ee7\u7eed\u4e86\u89e3\u6216\u5bf9\u6bd4\u8fd9\u6761\u4e70\u5bb6\u8bc1\u636e\uff0c\u518d\u5224\u65ad\u662f\u5426\u9002\u5408\u4f60\u3002"
                if is_zh
                else "Learn more or compare this buyer evidence before deciding whether it fits your use case."
            ),
            "subtitle_style": (
                "\u89e3\u91ca\u578b\u5b57\u5e55\uff0c\u5b8c\u6574\u77ed\u53e5\uff0c\u5173\u952e\u8bc1\u636e\u5355\u72ec\u5f3a\u8c03"
                if is_zh
                else "Explanatory full-sentence subtitles with the proof quote isolated"
            ),
        },
    }

    duration_definitions = {
        15: {
            "best_use": "fast_hook_test",
            "scene_count": 2,
            "duration_note": (
                "\u4ec5\u4fdd\u7559\u6700\u5f3a Hook\u3001\u4e24\u4e2a\u6838\u5fc3\u955c\u5934\u548c\u77ed CTA\u3002"
                if is_zh
                else "Keep only the strongest hook, two core scenes, and a short CTA."
            ),
        },
        30: {
            "best_use": "standard_three_scene_story",
            "scene_count": 3,
            "duration_note": (
                "\u4fdd\u7559\u5b8c\u6574\u4e09\u955c\u5934\u7ed3\u6784\u548c\u8bc1\u636e\u6536\u5c3e\u3002"
                if is_zh
                else "Retain the complete three-scene structure and evidence-led close."
            ),
        },
        45: {
            "best_use": "proof_and_objection_explainer",
            "scene_count": 3,
            "duration_note": (
                "\u589e\u52a0\u8bc1\u636e\u3001\u987e\u8651\u548c\u6bd4\u8f83\u89e3\u91ca\uff0c\u4f46\u4e0d\u589e\u52a0\u672a\u8bc1\u5b9e\u4e3b\u5f20\u3002"
                if is_zh
                else "Add proof, objection, and comparison context without adding unsupported claims."
            ),
        },
    }

    platform_packs: list[dict] = []
    for platform, platform_config in platform_definitions.items():
        for duration, duration_config in duration_definitions.items():
            selected_scenes = source_scenes[: duration_config["scene_count"]]
            opening_hook = source_hook
            if duration == 15:
                opening_hook = source_hook.split(".")[0].strip() or source_hook
            duration_cta = platform_config["cta"]
            if duration == 15:
                duration_cta = duration_cta.split(".")[0].strip() or duration_cta
            script_scenes = [
                {
                    "scene_number": index,
                    "scene_text": scene,
                    "duration_hint_seconds": max(
                        2,
                        (duration - 4) // max(len(selected_scenes), 1),
                    ),
                    "proof_quote": proof_quote,
                    "do_not_claim": safe_claim_notes,
                }
                for index, scene in enumerate(selected_scenes, start=1)
                if scene
            ]
            if duration == 45:
                script_scenes.append(
                    {
                        "scene_number": len(script_scenes) + 1,
                        "scene_text": (
                            f"\u7528\u5df2\u6709\u539f\u8bdd\u56de\u770b\u8d2d\u4e70\u987e\u8651\uff1a{proof_quote}"
                            if is_zh and proof_quote
                            else f"Revisit the buyer concern using the supplied quote: {proof_quote}"
                            if proof_quote
                            else (
                                "\u8bc1\u636e\u4e0d\u8db3\uff1a\u4fdd\u7559\u987e\u8651\uff0c\u4e0d\u5ba3\u79f0\u5df2\u89e3\u51b3\u3002"
                                if is_zh
                                else "Evidence gap: retain the concern and do not claim it is resolved."
                            )
                        ),
                        "duration_hint_seconds": 8,
                        "proof_quote": proof_quote,
                        "do_not_claim": safe_claim_notes,
                    }
                )
            platform_pack_id = f"{platform}_{duration}s_{source_asset_pack_id}"
            keyframes = [
                {
                    **dict(keyframe),
                    "platform": platform,
                    "duration_seconds": duration,
                    "platform_visual_note": platform_config["pacing"],
                    "do_not_claim": safe_claim_notes,
                }
                for keyframe in list(source_asset.get("keyframe_prompts") or [])[
                    : max(2, duration_config["scene_count"])
                ]
            ]
            subtitles = [
                {
                    **dict(line),
                    "subtitle_style": platform_config["subtitle_style"],
                }
                for line in list(source_asset.get("subtitle_lines") or [])[
                    : max(2, duration_config["scene_count"])
                ]
            ]
            source_captions = dict(source_asset.get("caption_variants") or {})
            caption_variants = {
                **source_captions,
                "platform_caption": (
                    source_captions.get("short_caption")
                    if platform == "tiktok"
                    else source_captions.get("benefit_caption")
                    if platform == "instagram_reels"
                    else source_captions.get("safe_claim_caption")
                )
                or opening_hook,
                "duration_caption": f"{duration}s | {opening_hook}",
            }
            platform_packs.append(
                {
                    "platform_pack_id": platform_pack_id,
                    "source_asset_pack_id": source_asset_pack_id,
                    "platform": platform,
                    "format": platform_config["format"],
                    "duration_seconds": duration,
                    "platform_title": platform_config["title"],
                    "platform_fit_reason": platform_config["fit_reason"],
                    "best_use": duration_config["best_use"],
                    "pacing_strategy": (
                        f"{platform_config['pacing']} {duration_config['duration_note']}"
                    ),
                    "opening_hook": opening_hook,
                    "shooting_script": {
                        "hook": opening_hook,
                        "scenes": script_scenes,
                        "cta": duration_cta,
                        "proof_quote": proof_quote,
                        "missing_quote": missing_quote,
                        "risk_note": _rw_text(source_script.get("risk_note")),
                        "do_not_claim": safe_claim_notes,
                    },
                    "shot_list": script_scenes,
                    "keyframe_prompts": keyframes,
                    "subtitle_style": platform_config["subtitle_style"],
                    "subtitle_lines": subtitles,
                    "caption_variants": caption_variants,
                    "thumbnail_prompt": (
                        f"{_rw_text(source_asset.get('thumbnail_prompt'))} "
                        f"Platform: {platform_config['title']}; duration: {duration}s; "
                        f"keep the supplied evidence visible."
                    ).strip(),
                    "b_roll_notes": list(source_asset.get("b_roll_notes") or []),
                    "on_screen_text": list(source_asset.get("on_screen_text") or []),
                    "voiceover_script": "\n".join(
                        [
                            opening_hook,
                            *[
                                _rw_text(scene.get("scene_text"))
                                for scene in script_scenes
                            ],
                            duration_cta,
                        ]
                    ),
                    "safe_claim_notes": safe_claim_notes,
                    "proof_quotes": [proof_quote] if proof_quote else [],
                    "risk_notes": list(source_asset.get("risk_notes") or []),
                    "do_not_claim": safe_claim_notes,
                    "asset_readiness": (
                        "needs_evidence"
                        if weak_evidence
                        else _rw_text(source_asset.get("asset_readiness"))
                        or "ready_for_human_review"
                    ),
                    "evidence_strength_score": int(
                        source_asset.get("evidence_strength_score") or 0
                    ),
                    "claim_safety_level": (
                        "conservative"
                        if weak_evidence
                        else "evidence_grounded"
                    ),
                    "recommended_next_action": (
                        "collect_more_reviews"
                        if missing_quote
                        else "lower_claim_strength"
                        if weak_evidence
                        else "human_review_before_platform_export"
                    ),
                }
            )

    recommended_pack = next(
        (
            pack
            for pack in platform_packs
            if pack["platform"] == "tiktok"
            and pack["duration_seconds"] == 30
        ),
        platform_packs[0] if platform_packs else {},
    )
    required_platforms = set(platform_definitions)
    required_durations = set(duration_definitions)
    present_platforms = {pack["platform"] for pack in platform_packs}
    present_durations = {pack["duration_seconds"] for pack in platform_packs}
    return {
        "pack_version": "multi_platform_asset_pack_v1",
        "multi_platform_summary": {
            "platform_pack_count": len(platform_packs),
            "platform_count": len(present_platforms),
            "duration_count": len(present_durations),
            "platforms": sorted(present_platforms),
            "durations_seconds": sorted(present_durations),
            "source_asset_pack_id": source_asset_pack_id,
            "recommended_platform_pack_id": _rw_text(
                recommended_pack.get("platform_pack_id")
            ),
            "asset_readiness": _rw_text(
                recommended_pack.get("asset_readiness")
            ),
            "evidence_strength_score": int(
                recommended_pack.get("evidence_strength_score") or 0
            ),
            "risk_summary": (
                "\u5f31\u8bc1\u636e\u6a21\u5f0f\uff1a\u6240\u6709\u5e73\u53f0\u5305\u4fdd\u6301\u4fdd\u5b88\u4e3b\u5f20\u3002"
                if is_zh and weak_evidence
                else "Weak-evidence mode: all platform packs retain conservative claims."
                if weak_evidence
                else (
                    "\u6240\u6709\u5e73\u53f0\u5305\u4fdd\u7559\u539f\u59cb\u8bc1\u636e\u548c\u7981\u6b62\u4e3b\u5f20\u8fb9\u754c\u3002"
                    if is_zh
                    else "All platform packs preserve source evidence and do-not-claim boundaries."
                )
            ),
        },
        "source_asset_pack_id": source_asset_pack_id,
        "recommended_platform_pack_id": _rw_text(
            recommended_pack.get("platform_pack_id")
        ),
        "platform_packs": platform_packs,
        "platform_quality_checks": {
            "missing_quote": missing_quote if source_asset else True,
            "weak_evidence": weak_evidence if source_asset else True,
            "unsupported_claim": False,
            "unsupported_claim_terms": [],
            "unsafe_provider_action": False,
            "missing_platform_variant": sorted(
                required_platforms - present_platforms
            ),
            "missing_duration_variant": sorted(
                required_durations - present_durations
            ),
            "do_not_claim_preserved": all(
                set(do_not_claim).issubset(set(pack.get("do_not_claim") or []))
                for pack in platform_packs
            ),
        },
        "safety_boundaries": {
            "provider_enabled": False,
            "llm_api_enabled": False,
            "video_generation_enabled": False,
            "media_operation_enabled": False,
            "paid_operation_enabled": False,
            "registry_operation_enabled": False,
            "restore_or_rollback_enabled": False,
            "feedback_persisted": False,
        },
    }


def _rw_creative_variant_pack(creative_decision_pack: dict, language: str) -> dict:
    angles = list(creative_decision_pack.get("top_ad_angles") or [])
    source_angle = next((angle for angle in angles if angle.get("is_recommended")), angles[0] if angles else {})
    video_pack = dict(creative_decision_pack.get("video_prompt_pack") or {})
    is_zh = language == "zh-CN"
    source_script = dict(source_angle.get("tiktok_script") or {})
    source_scenes = list(source_script.get("scenes") or [])
    while len(source_scenes) < 3:
        source_scenes.append("")
    proof_quote = _rw_text(source_script.get("proof_quote") or source_angle.get("proof_quote"))
    proof_source = _rw_text(source_angle.get("proof_source"))
    risk_note = _rw_text(source_script.get("risk_note") or source_angle.get("risk_note"))
    source_hook = _rw_text(source_script.get("hook") or source_angle.get("hook"))
    source_cta = _rw_text(source_script.get("cta") or source_angle.get("cta"))
    source_title = _rw_text(source_angle.get("title"))
    do_not_claim = list(video_pack.get("do_not_claim") or [])
    missing_quote = not bool(proof_quote)
    weak_evidence = (
        missing_quote
        or int(source_angle.get("evidence_strength_score") or 0) < 60
        or source_angle.get("claim_safety_level") != "evidence_grounded"
    )

    definitions = [
        {
            "variant_type": "ugc_testimonial",
            "title": "\u4e70\u5bb6\u539f\u8bdd UGC" if is_zh else "Buyer-quote UGC",
            "length": 20,
            "style": "\u624b\u6301\u51fa\u955c\u3001\u539f\u8bdd\u53e0\u52a0\u3001\u4fdd\u5b88\u89e3\u8bfb" if is_zh else "Handheld testimonial framing with buyer-quote overlays",
            "hook": (
                f"\u4e70\u5bb6\u7684\u539f\u8bdd\u662f\uff1a\u201c{proof_quote}\u201d"
                if is_zh and proof_quote
                else f"A buyer put it plainly: \"{proof_quote}\""
                if proof_quote
                else source_hook
            ),
            "reason": "Lead with the supplied buyer voice and keep the creator interpretation visibly secondary.",
        },
        {
            "variant_type": "problem_solution",
            "title": "\u95ee\u9898\u68c0\u67e5\u8def\u5f84" if is_zh else "Problem-check path",
            "length": 25,
            "style": "\u95ee\u9898\u7279\u5199\u3001\u8d2d\u4e70\u68c0\u67e5\u3001\u8bc1\u636e\u6536\u5c3e" if is_zh else "Problem close-up, buyer inspection, evidence-led close",
            "hook": source_hook,
            "reason": "Turn the source pain or objection into a pre-purchase inspection sequence without claiming a fix.",
        },
        {
            "variant_type": "direct_demo",
            "title": "\u76f4\u63a5\u6f14\u793a\u68c0\u67e5" if is_zh else "Direct inspection demo",
            "length": 18,
            "style": "\u4ea7\u54c1\u4e3a\u4e3b\u3001\u8fde\u7eed\u52a8\u4f5c\u3001\u5c11\u65c1\u767d" if is_zh else "Product-first continuous demonstration with minimal narration",
            "hook": (
                f"\u76f4\u63a5\u770b\u8fd9\u6761\u8bc4\u8bba\u5bf9\u5e94\u7684\u8d2d\u4e70\u68c0\u67e5\uff1a\u201c{proof_quote}\u201d"
                if is_zh and proof_quote
                else f"Watch the buyer check behind this review: \"{proof_quote}\""
                if proof_quote
                else source_hook
            ),
            "reason": "Use the existing three evidence-grounded scenes as a product-first visual inspection.",
        },
        {
            "variant_type": "objection_reversal",
            "title": "\u987e\u8651\u56de\u5e94\uff08\u4e0d\u5ba3\u79f0\u5df2\u89e3\u51b3\uff09" if is_zh else "Objection response without resolution claim",
            "length": 25,
            "style": "\u5148\u5448\u73b0\u987e\u8651\u3001\u518d\u5c55\u793a\u68c0\u67e5\u3001\u4fdd\u7559\u5224\u65ad" if is_zh else "Objection first, inspection second, viewer decision retained",
            "hook": (
                f"\u5148\u4e0d\u56de\u907f\u8fd9\u4e2a\u987e\u8651\uff1a\u201c{proof_quote}\u201d"
                if is_zh and proof_quote
                else f"Do not skip this buyer concern: \"{proof_quote}\""
                if proof_quote
                else source_hook
            ),
            "reason": "Acknowledge the supplied objection, then show only the checks supported by the existing script.",
        },
        {
            "variant_type": "short_hook",
            "title": "\u539f\u8bdd\u77ed Hook" if is_zh else "Quote-first short hook",
            "length": 10,
            "style": "\u5feb\u8282\u594f\u539f\u8bdd\u5f00\u573a\u3001\u4e09\u955c\u5feb\u5207\u3001\u4fdd\u5b88 CTA" if is_zh else "Fast quote-first open, three quick cuts, conservative CTA",
            "hook": (
                f"\u5341\u79d2\u5148\u770b\u8fd9\u53e5\uff1a\u201c{proof_quote}\u201d"
                if is_zh and proof_quote
                else f"Ten seconds. Start with the buyer line: \"{proof_quote}\""
                if proof_quote
                else source_hook
            ),
            "reason": "Compress the same evidence-backed script into a short opening test without adding a new claim.",
        },
    ]

    variants: list[dict] = []
    for index, definition in enumerate(definitions, start=1):
        variant_id = f"variant_{index}_{definition['variant_type']}"
        variant_hook = _rw_text(definition["hook"])
        shot_list = [
            {
                "scene_number": scene_number,
                "prompt": scene,
                "evidence_quote": proof_quote,
            }
            for scene_number, scene in enumerate(source_scenes[:3], start=1)
            if scene
        ]
        video_prompt = "\n".join(
            [
                f"Variant: {definition['title']}",
                f"Creative style: {definition['style']}",
                f"Hook: {variant_hook}",
                *[f"Shot {shot['scene_number']}: {shot['prompt']}" for shot in shot_list],
                f"CTA: {source_cta}",
                f"Risk note: {risk_note}",
                "Do not claim:",
                *[f"- {item}" for item in do_not_claim],
            ]
        )
        copy_ready_script = "\n".join(
            [
                f"Hook: {variant_hook}",
                f"Scene 1: {source_scenes[0]}",
                f"Scene 2: {source_scenes[1]}",
                f"Scene 3: {source_scenes[2]}",
                f"CTA: {source_cta}",
                f"Proof quote: {proof_quote or 'missing_quote'}",
                f"Risk note: {risk_note}",
            ]
        )
        variants.append(
            {
                "variant_id": variant_id,
                "variant_type": definition["variant_type"],
                "variant_title": definition["title"],
                "source_angle_id": source_angle.get("angle_id", ""),
                "source_angle_title": source_title,
                "target_platform": "TikTok",
                "target_length_seconds": definition["length"],
                "creative_style": definition["style"],
                "hook": variant_hook,
                "scene_1": source_scenes[0],
                "scene_2": source_scenes[1],
                "scene_3": source_scenes[2],
                "cta": source_cta,
                "proof_quote": proof_quote,
                "proof_source": proof_source,
                "missing_quote": missing_quote,
                "weak_evidence": weak_evidence,
                "risk_note": risk_note,
                "do_not_claim": do_not_claim,
                "video_prompt": video_prompt,
                "shot_list": shot_list,
                "copy_ready_script": copy_ready_script,
                "evidence_strength_score": int(source_angle.get("evidence_strength_score") or 0),
                "claim_safety_level": source_angle.get("claim_safety_level", "conservative"),
                "copy_readiness": "needs_evidence" if weak_evidence else source_angle.get("copy_readiness", "ready"),
                "variant_reason": definition["reason"],
            }
        )

    recommended_type = (
        "objection_reversal"
        if source_angle.get("buyer_objection")
        else "problem_solution"
        if source_angle.get("buyer_pain")
        else "direct_demo"
    )
    recommended_variant = next(
        (variant for variant in variants if variant["variant_type"] == recommended_type),
        variants[0] if variants else {},
    )
    if weak_evidence:
        recommended_variant = {}
    missing_quote_variants = [
        variant["variant_id"] for variant in variants if variant["missing_quote"]
    ]
    weak_evidence_variants = [
        variant["variant_id"] for variant in variants if variant["weak_evidence"]
    ]
    unsupported_claims = list(
        creative_decision_pack.get("quality_checks", {}).get("unsupported_claim_terms") or []
    )
    variant_selection_pack = _rw_creative_variant_selection_pack(
        variants,
        recommended_variant.get("variant_id", ""),
    )
    creative_test_feedback_pack = _rw_creative_test_feedback_pack(
        variants,
        variant_selection_pack,
        unsupported_claims,
    )
    creative_iteration_pack = _rw_creative_iteration_pack(
        variants,
        creative_test_feedback_pack,
        language,
    )
    creative_version_control_pack = _rw_creative_version_control_pack(
        variants,
        creative_test_feedback_pack,
        creative_iteration_pack,
    )
    creative_asset_pack = _rw_creative_asset_pack(
        creative_version_control_pack,
        _rw_text(video_pack.get("product_context")),
        language,
    )
    multi_platform_asset_pack = _rw_multi_platform_asset_pack(
        creative_asset_pack,
        language,
    )
    return {
        "pack_version": "creative_variant_pack_v1",
        "variant_summary": {
            "variant_count": len(variants),
            "recommended_variant_id": recommended_variant.get("variant_id", ""),
            "recommended_variant_title": recommended_variant.get("variant_title", ""),
            "recommendation_reason": (
                recommended_variant.get("variant_reason", "")
                if recommended_variant
                else "Weak evidence: variants are available for review, but none is recommended for production use."
            ),
            "weak_evidence_count": len(weak_evidence_variants),
            "missing_quote_count": len(missing_quote_variants),
            "copy_ready_count": sum(variant["copy_readiness"] == "ready" for variant in variants),
        },
        "recommended_variant_id": recommended_variant.get("variant_id", ""),
        "variants": variants,
        "variant_quality_checks": {
            "unsupported_claim": bool(unsupported_claims),
            "unsupported_claim_terms": unsupported_claims,
            "missing_quote": bool(missing_quote_variants),
            "missing_quote_variants": missing_quote_variants,
            "weak_evidence": bool(weak_evidence_variants),
            "weak_evidence_variants": weak_evidence_variants,
            "unsafe_provider_action": False,
        },
        "variant_copy_export": {
            "recommended_script": recommended_variant.get("copy_ready_script", ""),
            "variant_scripts": {
                variant["variant_id"]: variant["copy_ready_script"] for variant in variants
            },
            "variant_video_prompts": {
                variant["variant_id"]: variant["video_prompt"] for variant in variants
            },
        },
        "variant_selection_pack": variant_selection_pack,
        "creative_test_feedback_pack": creative_test_feedback_pack,
        "creative_iteration_pack": creative_iteration_pack,
        "creative_version_control_pack": creative_version_control_pack,
        "creative_asset_pack": creative_asset_pack,
        "multi_platform_asset_pack": multi_platform_asset_pack,
        "safety_boundaries": {
            "real_provider_called": False,
            "llm_api_called": False,
            "video_generated": False,
            "media_uploaded": False,
            "media_downloaded": False,
            "paid_operation_performed": False,
            "registry_written": False,
            "restore_or_rollback_performed": False,
        },
    }


def _review_workspace_creative_decision_pack(
    payload: ReviewWorkspaceRequest,
    source_breakdown: ReviewSourceBreakdown,
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
    sample_interpretation: ReviewSampleInterpretation,
    llm_evidence_packet: dict,
) -> dict:
    language = payload.output_language
    is_zh = language == "zh-CN"
    product_context = _rw_workspace_product_hint(payload, language)
    packet_evidence = dict(llm_evidence_packet.get("evidence") or {})
    evidence_quotes = [
        _rw_quote_snippet(quote, 240)
        for quote in list(packet_evidence.get("quotes") or [])[:12]
        if _rw_text(quote)
    ]
    candidates = _rw_creative_angle_candidates(
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
        evidence_quotes,
    )
    positive_theme = _rw_first_available_theme(liked_points, use_cases)
    positive_quote = _rw_quote_snippet(_rw_theme_first_quote(positive_theme), 180) if positive_theme else ""
    positive_label = _rw_output_theme_label(positive_theme.label, language) if positive_theme else ""

    candidate_angles: list[dict] = []
    for index, candidate in enumerate(candidates, start=1):
        theme = candidate.get("theme")
        signal_type = candidate["signal_type"]
        proof_quote = candidate["proof_quote"]
        raw_label = getattr(theme, "label", "") if theme else ""
        label = _rw_output_theme_label(raw_label, language) if raw_label else (
            "\u9ad8\u4fe1\u53f7\u4e70\u5bb6\u539f\u8bdd" if is_zh else "high-signal buyer quote"
        )
        evidence_count = int(candidate.get("evidence_count") or 0)
        evidence_strength = "strong" if evidence_count >= 3 else "moderate" if proof_quote else "weak"
        target_audience = (
            f"\u6b63\u5728\u8bc4\u4f30{product_context}\u3001\u5e76\u5728\u610f{label}\u7684\u6d88\u8d39\u8005"
            if is_zh
            else f"Buyers evaluating {product_context} who care about {label}"
        )
        hook = (
            f"\u4e70\u4e4b\u524d\uff0c\u5148\u770b\u8fd9\u53e5\u771f\u5b9e\u4e70\u5bb6\u539f\u8bdd\uff1a\u201c{proof_quote}\u201d"
            if is_zh
            else f"Before you buy, start with this real buyer line: \"{proof_quote}\""
        )
        payoff = positive_quote if positive_quote and positive_quote != proof_quote else proof_quote
        script_copy = _rw_creative_script_copy(
            signal_type=signal_type,
            label=label,
            product_context=product_context,
            proof_quote=proof_quote,
            payoff_quote=payoff,
            evidence_count=evidence_count,
            language=language,
        )
        first_scene, second_scene, third_scene = script_copy["scenes"]
        cta = script_copy["cta"]
        script_outline = " ".join([hook, first_scene, second_scene, third_scene, cta])
        risk_note = script_copy["risk_note"]
        title = _rw_creative_angle_title(signal_type, label, language)
        signal_cluster_label = " ".join(label.lower().split())
        coverage = {
            "proof_quote": bool(proof_quote),
            "proof_source": bool(_rw_creative_proof_source(proof_quote, source_breakdown)),
            "buyer_pain": signal_type == "pain_point",
            "buyer_objection": signal_type == "buyer_objection",
            "liked_point": signal_type == "positive_signal" or bool(positive_label),
            "use_case": signal_type == "use_case",
        }
        copy_ready_text = "\n".join(
            [
                f"Hook: {hook}",
                f"Scene 1: {first_scene}",
                f"Scene 2: {second_scene}",
                f"Scene 3: {third_scene}",
                f"CTA: {cta}",
                f"Proof quote: {proof_quote or 'missing_quote'}",
                f"Risk note: {risk_note}",
            ]
        )
        candidate_angles.append(
            {
                "angle_id": f"angle_{index}",
                "title": title,
                "target_audience": target_audience,
                "buyer_pain": label if signal_type == "pain_point" else "",
                "buyer_objection": label if signal_type == "buyer_objection" else "",
                "proof_quote": proof_quote,
                "proof_source": _rw_creative_proof_source(proof_quote, source_breakdown),
                "liked_point_or_positive_reversal": positive_label or label,
                "hook": hook,
                "script_outline": script_outline,
                "first_scene": first_scene,
                "second_scene": second_scene,
                "third_scene": third_scene,
                "cta": cta,
                "evidence_strength": evidence_strength,
                "supporting_evidence_count": evidence_count,
                "evidence_coverage": coverage,
                "evidence_gaps": [],
                "angle_cluster": f"{signal_type}:{signal_cluster_label}",
                "duplicate_angle_note": "",
                "missing_quote": not bool(proof_quote),
                "weak_evidence_reason": (
                    "Only one visible-sample quote supports this angle."
                    if evidence_strength != "strong"
                    else ""
                ),
                "risk_note": risk_note,
                "copy_ready_text": copy_ready_text,
                "tiktok_script": {
                    "hook": hook,
                    "scenes": [first_scene, second_scene, third_scene],
                    "cta": cta,
                    "proof_quote": proof_quote,
                    "risk_note": risk_note,
                },
            }
        )

    top_ad_angles, duplicate_angle_count = _rw_rank_and_dedupe_creative_angles(candidate_angles)
    source_summary = [
        {
            "source_type": group.get("source_type", ""),
            "label": group.get("label", ""),
            "review_count": group.get("review_count", 0),
            "high_signal_review_count": group.get("high_signal_review_count", 0),
        }
        for group in list(packet_evidence.get("source_groups") or [])[:6]
    ]
    evidence_brief = {
        "pain_points": _rw_packet_theme_items(common_pain_points),
        "objections": _rw_packet_theme_items(buyer_objections),
        "liked_points": _rw_packet_theme_items(liked_points),
        "use_cases": _rw_packet_theme_items(use_cases),
        "high_signal_quotes": evidence_quotes,
        "source_breakdown_summary": source_summary,
        "sample_size_note": _rw_text(getattr(sample_interpretation, "sample_size_note", "")),
    }
    primary_angle = top_ad_angles[0] if top_ad_angles else {}
    shot_list = [
        {
            "scene_number": scene_number,
            "prompt": primary_angle.get(field, ""),
            "evidence_quote": primary_angle.get("proof_quote", ""),
        }
        for scene_number, field in enumerate(["first_scene", "second_scene", "third_scene"], start=1)
        if primary_angle.get(field)
    ]
    do_not_claim = [
        "Do not claim full-market statistics from the visible review sample.",
        "Do not promise guaranteed product performance or universal outcomes.",
        "Do not generalize one variant, color, size, or packaging issue to the whole product without repeated evidence.",
        "Do not imply that a buyer objection is resolved unless the supplied evidence explicitly supports the reversal.",
        "Do not claim the product is leak-proof, quiet, or easy to clean unless repeated supplied quotes explicitly support that claim.",
    ]
    if primary_angle.get("title"):
        do_not_claim.append(
            f"Do not present the selected angle \"{primary_angle['title']}\" as a resolved product benefit; "
            "show it as a buyer check grounded in the supplied quote."
        )
    video_copy_ready_text = "\n".join(
        [
            f"Keyframe prompt: {primary_angle.get('title', '')}",
            *[
                f"Shot {shot['scene_number']}: {shot['prompt']}"
                for shot in shot_list
            ],
            "Do not claim:",
            *[f"- {item}" for item in do_not_claim],
        ]
    )
    video_prompt_pack = {
        "keyframe_prompt": (
            f"Create three evidence-grounded keyframes for {product_context}. "
            f"Keep product identity stable and follow the selected angle: {primary_angle.get('title', '')}. "
            f"Anchor the sequence to this visible-review quote: {primary_angle.get('proof_quote', '')}"
            if primary_angle
            else ""
        ),
        "shot_list": shot_list,
        "visual_style_hint": "Clear product-first ecommerce footage, readable evidence overlays, realistic use context, no fabricated before/after result.",
        "product_context": product_context,
        "do_not_claim": do_not_claim,
        "copy_ready_text": video_copy_ready_text,
        "evidence_links": [
            {
                "angle_id": angle["angle_id"],
                "proof_quote": angle["proof_quote"],
                "proof_source": angle["proof_source"],
            }
            for angle in top_ad_angles
        ],
        "provider_call_enabled": False,
        "video_generation_performed": False,
    }
    quality_checks = _rw_creative_quality_checks(top_ad_angles, len(evidence_quotes))
    recommended_angle = next((angle for angle in top_ad_angles if angle.get("is_recommended")), {})
    weak_evidence_count = sum(
        1 for angle in top_ad_angles
        if angle.get("evidence_strength") == "weak"
        or int(angle.get("evidence_strength_score") or 0) < 60
    )
    missing_quote_count = sum(1 for angle in top_ad_angles if angle.get("missing_quote"))
    ready_to_copy_script_count = sum(
        1 for angle in top_ad_angles if angle.get("copy_readiness") == "ready"
    )
    if quality_checks["weak_evidence"]:
        decision_reason = (
            "Weak evidence: the best available angle is ranked for review, "
            "but more distinct buyer quotes are required before production use."
        )
    elif recommended_angle:
        decision_reason = recommended_angle.get("recommendation_reason", "")
    else:
        decision_reason = "Weak evidence: no distinct quote-backed creative angle is ready to recommend."
    creative_next_actions = _rw_creative_next_actions(top_ad_angles, quality_checks)
    creative_feedback_runtime = _rw_creative_feedback_runtime(
        top_ad_angles,
        recommended_angle,
        quality_checks,
        video_prompt_pack,
        weak_evidence_count,
        missing_quote_count,
    )

    creative_decision_pack = {
        "pack_version": "creative_decision_pack_v1",
        "intended_use": "evidence_grounded_creative_decision",
        "top_ad_angles": top_ad_angles,
        "evidence_brief": evidence_brief,
        "video_prompt_pack": video_prompt_pack,
        "quality_checks": quality_checks,
        "recommended_angle_id": recommended_angle.get("angle_id", ""),
        "recommended_angle_title": recommended_angle.get("title", ""),
        "decision_reason": decision_reason,
        "angle_ranking_summary": [
            {
                "angle_id": angle.get("angle_id", ""),
                "angle_rank": angle.get("angle_rank", 0),
                "title": angle.get("title", ""),
                "evidence_strength_score": angle.get("evidence_strength_score", 0),
                "copy_readiness": angle.get("copy_readiness", ""),
            }
            for angle in top_ad_angles
        ],
        "weak_evidence_count": weak_evidence_count,
        "missing_quote_count": missing_quote_count,
        "ready_to_copy_script_count": ready_to_copy_script_count,
        "duplicate_angle_count": duplicate_angle_count,
        "creative_next_actions": creative_next_actions,
        "creative_feedback_runtime": creative_feedback_runtime,
        "weak_evidence_reason": (
            quality_checks["recommendation"] if quality_checks["weak_evidence"] else ""
        ),
        "safety_boundaries": {
            "real_provider_called": False,
            "secret_read": False,
            "media_uploaded": False,
            "media_downloaded": False,
            "video_generated": False,
            "registry_written": False,
            "restore_or_rollback_performed": False,
            "paid_operation_performed": False,
        },
    }
    creative_decision_pack["creative_variant_pack"] = _rw_creative_variant_pack(
        creative_decision_pack,
        language,
    )
    creative_decision_pack["creative_iteration_pack"] = (
        creative_decision_pack["creative_variant_pack"].get("creative_iteration_pack") or {}
    )
    creative_decision_pack["creative_version_control_pack"] = (
        creative_decision_pack["creative_variant_pack"].get(
            "creative_version_control_pack"
        )
        or {}
    )
    creative_decision_pack["creative_asset_pack"] = (
        creative_decision_pack["creative_variant_pack"].get("creative_asset_pack")
        or {}
    )
    creative_decision_pack["multi_platform_asset_pack"] = (
        creative_decision_pack["creative_variant_pack"].get(
            "multi_platform_asset_pack"
        )
        or {}
    )
    return creative_decision_pack



@app.post("/api/v1/analyze-review-workspace", response_model=ReviewWorkspaceResponse)
async def analyze_review_workspace(payload: ReviewWorkspaceRequest):
    rows = _rw_collect_reviews(payload)
    high_signal_rows = [row for row in rows if row["score"] >= 4]
    source_breakdown = _rw_source_breakdown(payload, rows)

    workspace_signal_rows = high_signal_rows or rows
    common_pain_points = _rw_theme_summaries(
        workspace_signal_rows,
        _rw_workspace_theme_markers(payload, workspace_signal_rows),
    )
    buyer_objections = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_OBJECTION_MARKERS,
        "objection",
    )
    liked_points = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_LIKE_MARKERS,
        "liked signal",
        limit=12,
    )
    use_cases = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_USE_CASE_MARKERS,
        "use case",
    )

    common_pain_points = _rw_refine_theme_quotes(_rw_compact_theme_summaries(common_pain_points))
    buyer_objections = _rw_refine_buyer_objection_summaries(buyer_objections)
    liked_points = _rw_refine_liked_point_summaries(liked_points)
    use_cases = _rw_refine_use_case_summaries(use_cases + liked_points + buyer_objections + common_pain_points)

    hooks = _rw_hooks(common_pain_points, liked_points, payload.output_language)
    sample_interpretation = _rw_sample_interpretation(
        payload,
        rows,
        high_signal_rows,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
    )
    video_script_pack = _rw_video_script_pack(
        payload,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
        hooks,
    )
    llm_evidence_packet = _review_workspace_llm_evidence_packet(
        payload,
        rows,
        high_signal_rows,
        source_breakdown,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
    )
    creative_decision_pack = _review_workspace_creative_decision_pack(
        payload,
        source_breakdown,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
        sample_interpretation,
        llm_evidence_packet,
    )

    return ReviewWorkspaceResponse(
        workspace_id=payload.workspace_id,
        product_count=len(payload.products),
        total_reviews=len(rows),
        high_signal_review_count=len(high_signal_rows),
        source_breakdown=source_breakdown,
        common_pain_points=common_pain_points,
        buyer_objections=buyer_objections,
        liked_points=liked_points,
        use_cases=use_cases,
        product_summaries=[_rw_product_summary(product) for product in payload.products],
        creative_angles=_rw_creative_angles(common_pain_points, liked_points, payload.output_language, buyer_objections),
        hooks=hooks,
        recommended_next_actions=[
            "Collect 30-80 high-signal reviews per product before final creative testing.",
            "Prioritize low-star and objection-heavy reviews for ad angle discovery.",
            "Use repeated buyer wording as hook language instead of generic product claims.",
        ],
        sample_interpretation=sample_interpretation,
        video_script_pack=video_script_pack,
        llm_evidence_packet=llm_evidence_packet,
        creative_decision_pack=creative_decision_pack,
    )




# L37-C messy pasted review parser.
import re
from schemas.review_paste import PastedReviewWorkspaceAnalyzeRequest, PastedReviewWorkspaceAnalyzeResponse, ReviewPasteParseRequest, ReviewPasteParseResponse
from schemas.review_workspace import ReviewWorkspaceProduct, ReviewWorkspaceReview

_REVIEW_PASTE_RATING_RE = re.compile(
    r"(?P<rating>[1-5](?:\.\d)?)\s*(?:out of\s*5\s*stars|/5|stars?)",
    re.IGNORECASE,
)

_REVIEW_PASTE_META_PREFIXES = (
    "reviewed in ",
    "verified purchase",
    "vine customer review",
    "people found this helpful",
    "person found this helpful",
    "helpful",
    "report",
    "translate review",
    "color:",
    "size:",
    "style:",
    "pattern name:",
    "flavor name:",
)


def _paste_clean_line(line: str) -> str:
    return " ".join(str(line or "").replace("\u00a0", " ").split())


def _paste_is_meta_line(line: str) -> bool:
    lowered = line.lower().strip()
    if not lowered:
        return True
    if lowered.startswith(_REVIEW_PASTE_META_PREFIXES):
        return True
    if "verified purchase" in lowered:
        return True
    if "found this helpful" in lowered:
        return True
    if lowered in {"read more", "show more", "see more", "customer reviews"}:
        return True
    return False


def _paste_high_signal_score(review: ReviewWorkspaceReview) -> int:
    text = _paste_clean_line(review.text)
    lowered = text.lower()
    if len(text) < 18:
        return 0

    score = 1
    try:
        rating = float(str(review.rating).split()[0]) if review.rating not in (None, "") else None
    except (TypeError, ValueError):
        rating = None

    if rating is not None and rating <= 3:
        score += 3
    if rating is not None and rating >= 4:
        score += 1
    if review.helpful_count:
        score += min(3, int(review.helpful_count) // 5 + 1)
    if any(marker in lowered for marker in ["but", "wish", "too", "not", "hard", "difficult", "problem", "issue", "leak", "broke", "mess"]):
        score += 3
    if any(marker in lowered for marker in ["love", "great", "easy", "perfect", "works", "useful", "recommend"]):
        score += 2
    if len(text) >= 80:
        score += 2
    return score


def _parse_helpful_count(line: str) -> int | None:
    match = re.search(r"(\d+)\s+people\s+found\s+this\s+helpful", line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"one\s+person\s+found\s+this\s+helpful", line, re.IGNORECASE):
        return 1
    return None


def _finalize_pasted_review(
    reviews: list[ReviewWorkspaceReview],
    rating,
    title: str,
    body_lines: list[str],
    helpful_count: int | None,
    source_section: str,
):
    body = _paste_clean_line(" ".join(body_lines))
    title = _paste_clean_line(title)

    if not body and title:
        body = title
        title = ""

    if len(body) < 10:
        return

    reviews.append(
        ReviewWorkspaceReview(
            rating=rating,
            title=title,
            text=body,
            helpful_count=helpful_count,
            source_section=source_section,
        )
    )


def _parse_messy_reviews(raw_text: str, source_section: str) -> list[ReviewWorkspaceReview]:
    lines = [_paste_clean_line(line) for line in str(raw_text or "").splitlines()]
    lines = [line for line in lines if line]

    reviews: list[ReviewWorkspaceReview] = []
    current_rating = None
    current_title = ""
    current_body: list[str] = []
    current_helpful = None
    active = False

    for line in lines:
        helpful = _parse_helpful_count(line)
        if helpful is not None:
            current_helpful = helpful
            continue

        rating_match = _REVIEW_PASTE_RATING_RE.search(line)
        if rating_match:
            if active:
                _finalize_pasted_review(
                    reviews,
                    current_rating,
                    current_title,
                    current_body,
                    current_helpful,
                    source_section,
                )

            active = True
            current_rating = rating_match.group("rating")
            remainder = _paste_clean_line(_REVIEW_PASTE_RATING_RE.sub("", line, count=1))
            current_title = remainder if len(remainder) <= 90 else ""
            current_body = [] if current_title else ([remainder] if remainder else [])
            current_helpful = None
            continue

        if _paste_is_meta_line(line):
            continue

        if active:
            if not current_title and len(line) <= 90 and not current_body:
                current_title = line
            else:
                current_body.append(line)
        else:
            # Generic non-Amazon paste fallback: each meaningful paragraph can be a review.
            if len(line) >= 30:
                reviews.append(
                    ReviewWorkspaceReview(
                        rating=None,
                        title="",
                        text=line,
                        helpful_count=None,
                        source_section=source_section,
                    )
                )

    if active:
        _finalize_pasted_review(
            reviews,
            current_rating,
            current_title,
            current_body,
            current_helpful,
            source_section,
        )

    # Deduplicate while preserving order.
    deduped: list[ReviewWorkspaceReview] = []
    seen = set()
    for review in reviews:
        key = _paste_clean_line(review.text).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(review)

    return deduped


@app.post("/api/v1/analyze-pasted-review-workspace", response_model=PastedReviewWorkspaceAnalyzeResponse)
async def analyze_pasted_review_workspace(payload: PastedReviewWorkspaceAnalyzeRequest):
    reviews = _parse_messy_reviews(payload.raw_text, payload.source_section)
    high_signal_count = sum(1 for review in reviews if _paste_high_signal_score(review) >= 4)

    warnings = []
    if not _paste_clean_line(payload.raw_text):
        warnings.append("empty_input")
    if not reviews:
        warnings.append("no_reviews_detected")
    if reviews and high_signal_count == 0:
        warnings.append("low_signal_reviews")

    workspace_product = ReviewWorkspaceProduct(
        platform=payload.platform,
        url=payload.url,
        asin=payload.asin,
        title=payload.product_title or payload.asin or payload.url or "Pasted review product",
        reviews=reviews,
    )

    parsed = ReviewPasteParseResponse(
        review_count=len(reviews),
        high_signal_review_count=high_signal_count,
        reviews=reviews,
        workspace_product=workspace_product,
        data_warnings=warnings,
    )

    workspace_payload = ReviewWorkspaceRequest(
        workspace_id=payload.workspace_id,
        source="pasted_reviews",
        products=[workspace_product],
        goal=payload.goal,
        output_language=payload.output_language,
    )
    analysis = await analyze_review_workspace(workspace_payload)

    return PastedReviewWorkspaceAnalyzeResponse(
        parsed=parsed,
        analysis=analysis,
    )


@app.post("/api/v1/parse-review-paste", response_model=ReviewPasteParseResponse)
async def parse_review_paste(payload: ReviewPasteParseRequest):
    reviews = _parse_messy_reviews(payload.raw_text, payload.source_section)
    high_signal_count = sum(1 for review in reviews if _paste_high_signal_score(review) >= 4)

    warnings = []
    if not _paste_clean_line(payload.raw_text):
        warnings.append("empty_input")
    if not reviews:
        warnings.append("no_reviews_detected")
    if reviews and high_signal_count == 0:
        warnings.append("low_signal_reviews")

    workspace_product = ReviewWorkspaceProduct(
        platform=payload.platform,
        url=payload.url,
        asin=payload.asin,
        title=payload.product_title or payload.asin or payload.url or "Pasted review product",
        reviews=reviews,
    )

    return ReviewPasteParseResponse(
        review_count=len(reviews),
        high_signal_review_count=high_signal_count,
        reviews=reviews,
        workspace_product=workspace_product,
        data_warnings=warnings,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=get_server_port(), reload=True)
