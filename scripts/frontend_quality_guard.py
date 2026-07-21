from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_INDEX = ROOT / "static" / "index.html"
PUBLIC_SMOKE = ROOT / "scripts" / "smoke_agent_graph_os_public.ps1"


MOJIBAKE_MARKERS = [
    "????",
    "锛",
    "鍦",
    "鐢",
    "鏃",
    "璇",
    "绮",
    "浜",
    "鎻",
    "鍙",
    "鐩",
    "椋",
    "瑙",
    "鏍",
    "绛",
    "€?",
    "鈥",
    "俙",
    "歖",
    "鐢ㄦ埛",
    "鐘硅鲍",
    "璐拱",
    "闈欐",
    "璇佹",
    "鎽樿",
    "鐩爣",
    "鍙椾紬",
    "绛夊緟",
    "鎵ц",
    "杩欐",
    "涓?Hook",
    "椋庨櫓",
    "鐥涚偣",
    "鏍稿績",
    "淇″彿",
]


REQUIRED_HTML_MARKERS = [
    "Workspace refresh shortcut",
    "Workspace last sync timestamp",
    "Workspace sync UX bundle",
    "Visible UI cleanup bundle",
    "Frontend copy guard hardening bundle",
    "Project Workspace history UX bundle",
    "Project Workspace action links bundle",
    "Project Workspace report reader bundle",
    "Project Workspace export pack bundle",
    "Project Workspace export pack safety chain bundle",
    "Project Workspace export pack safety timeline bundle",
    "Project Workspace runner plan panel bundle",
    "Project Workspace dispatch ticket panel bundle",
    "Project Workspace dispatch event panel bundle",
    "Project Workspace dispatch dry-run action bundle",
    "Project Workspace execution receipt panel bundle",
    "Project Workspace work order panel bundle",
    "Project Workspace queue item panel bundle",
    "Project Workspace queue claim panel bundle",
    "Project Workspace worker lease panel bundle",
    "Project Workspace invocation panel bundle",
    "Project Workspace result completion panel bundle",
    "Project Workspace handoff checkpoint panel bundle",
    "Project Workspace transition projection panel bundle",
    "Project Workspace commit plan guard panel bundle",
    "Project Workspace persist request rollback panel bundle",
    "Project Workspace persist gate audit panel bundle",
    "Project Workspace approval policy panel bundle",
    "Project Workspace runtime readiness panel bundle",
    "Project Workspace worker loop panel bundle",
    "Project Workspace worker checkpoint panel bundle",
    "Project Workspace finalization panel bundle",
    "Project Workspace orchestration readiness panel bundle",
    "Project Workspace operator control panel bundle",
    "Project Workspace operator approval panel bundle",
    "Project Workspace approval decision panel bundle",
    "Project Workspace execution sandbox panel bundle",
    "Project Workspace provider adapter panel bundle",
    "Project Workspace provider invocation panel bundle",
    "Project Workspace provider failure panel bundle",
    "Project Workspace provider observability panel bundle",
    "Project Workspace capability binding panel bundle",
    "Project Workspace capability invocation gate panel bundle",
    "Project Workspace capability invocation rehearsal panel bundle",
    "Project Workspace capability invocation runbook panel bundle",
    "Project Workspace capability invocation release packet panel bundle",
    "Project Workspace real execution mode gate panel bundle",
    "Project Workspace real execution readiness summary panel bundle",
    "Project Workspace real execution approval request panel bundle",
    "Project Workspace real execution approval decision panel bundle",
    "Project Workspace real execution launch authorization panel bundle",
    "Project Workspace real execution launch monitor panel bundle",
    "Project Workspace real execution incident response panel bundle",
    "Project Workspace real execution safety chain action",
    "Project Workspace real execution safety chain audit panel bundle",
    "Project Workspace real execution safety timeline bundle",
    "Project Workspace runner event ledger summary bundle",
    "Project Workspace supervisor event ledger decision bundle",
    "Project Workspace supervisor next-step routing plan bundle",
    "Project Workspace supervisor next-step work order preview bundle",
    "Project Workspace queue lease worker dry-run chain bundle",
    "Project Workspace agent contract registry bundle",
    "Project Workspace source adapter contract bundle",
    "Project Workspace multi-agent output chain bundle",
    "Project Workspace keyframe video asset chain bundle",
    "Project Workspace keyframe prompt pack bundle",
    "Project Workspace manual generation result bundle",
    "Project Workspace provider API readiness bundle",
    "Project Workspace provider sandbox runtime bundle",
    "Project Workspace real provider execution gate bundle",
    "Project Workspace provider failure recovery bundle",
    "Project Workspace provider observability report bundle",
    "Project Workspace provider queue lease worker bundle",
    "Project Workspace provider worker checkpoint resume bundle",
    "Project Workspace provider worker finalization bundle",
    "Project Workspace provider artifact lineage bundle",
    "Project Workspace provider artifact registry restore bundle",
    "Project Workspace provider registry operation approval bundle",
    "Project Workspace provider registry transaction rehearsal bundle",
    "Project Workspace provider transaction monitor bundle",
    "Project Workspace provider transaction incident drill bundle",
    "Project Workspace provider execution readiness packet bundle",
    "Project Workspace agent capability runtime bundle",
    "Project Workspace creative decision pack bundle",
    "Project Workspace creative decision usability bundle",
    "Project Workspace creative decision quality polish bundle",
    "Project Workspace creative feedback runtime bundle",
    "Project Workspace real sample export flow bundle",
    "Project Workspace creative variant pack bundle",
    "Project Workspace creative variant selection bundle",
    "Project Workspace creative test feedback bundle",
    "Project Workspace creative iteration bundle",
    "Project Workspace creative version control bundle",
    "Project Workspace creative asset pack bundle",
    "Project Workspace multi platform asset pack bundle",
    "Project Workspace asset quality gate bundle",
    "Project Workspace campaign export pack bundle",
    "Project Workspace review import pack bundle",
    "Project Workspace competitor review comparison bundle",
    "Project Workspace LLM assist dry-run bundle",
    "Project Workspace video provider orchestration dry-run bundle",
    "Project Workspace session snapshot bundle",
    "Project Workspace run snapshot compare bundle",
    "Project Workspace action queue bundle",
    "Project Workspace action ticket bundle",
    "Project Workspace approval decision bundle",
    "Project Workspace execution readiness bundle",
    "Project Workspace execution rehearsal bundle",
    "Project Workspace rehearsal remediation bundle",
    "Project Workspace remediation verification bundle",
    "Project Workspace retry rehearsal plan bundle",
    "Project Workspace retry rehearsal result bundle",
    "Project Workspace retry cycle decision bundle",
    "Project Workspace cycle history timeline bundle",
    "Project Workspace control center bundle",
    "Project Workspace agent run ledger bundle",
    "Project Workspace human review queue bundle",
    "Project Workspace capability permission matrix bundle",
    "Project Workspace system integration health bundle",
    "Project Workspace replay harness bundle",
    "Project Workspace provider adapter contract bundle",
    "Project Workspace provider contract test bundle",
    "Project Workspace provider mock invocation result bundle",
    "Project Workspace provider failure taxonomy bundle",
    "Project Workspace provider asset contract bundle",
    "Project Workspace provider cost quota risk guard bundle",
    "Project Workspace real provider readiness checklist bundle",
    "Project Workspace secret environment gate bundle",
    "Project Workspace network external call block guard bundle",
    "Project Workspace real execution approval token bundle",
    "Project Workspace provider invocation audit packet bundle",
    "Project Workspace review evidence quality bundle",
    "Project Workspace claim risk guard bundle",
    "Project Workspace claim-safe creative brief bundle",
    "Project Workspace claim-safe creative output bundle",
    "Project Workspace claim-safe platform delivery bundle",
    "Project Workspace claim-safe delivery QA bundle",
    "Project Workspace claim-safe delivery remediation bundle",
    "Project Workspace claim-safe remediation verification bundle",
    "Project Workspace final claim-safe export packet bundle",
    "Project Workspace safety chain history summary bundle",
    "Frontend interaction recovery bundle",
    "Frontend interaction binding repair bundle",
    "Project Workspace authorization manifest panel bundle",
    "Critical main zh override marker",
    "Planner clean zh override marker",
    "Agent graph zh override marker",
    "Copy-ready script zh label marker",
]


REQUIRED_SMOKE_MARKERS = [
    "workspace_refresh_shortcut_marker",
    "workspace_last_sync_timestamp_marker",
    "workspace_sync_ux_bundle_marker",
    "visible_ui_cleanup_bundle_marker",
    "frontend_copy_guard_hardening_marker",
    "project_workspace_history_ux_bundle_marker",
    "project_workspace_action_links_bundle_marker",
    "project_workspace_report_reader_bundle_marker",
    "project_workspace_export_pack_bundle_marker",
    "project_workspace_export_pack_safety_chain_marker",
    "project_workspace_export_pack_safety_timeline_marker",
    "project_workspace_runner_plan_panel_marker",
    "project_workspace_dispatch_ticket_panel_marker",
    "project_workspace_dispatch_event_panel_marker",
    "project_workspace_dispatch_dry_run_action_marker",
    "project_workspace_execution_receipt_panel_marker",
    "project_workspace_work_order_panel_marker",
    "project_workspace_queue_item_panel_marker",
    "project_workspace_queue_claim_panel_marker",
    "project_workspace_worker_lease_panel_marker",
    "project_workspace_invocation_panel_marker",
    "project_workspace_result_completion_panel_marker",
    "project_workspace_handoff_checkpoint_panel_marker",
    "project_workspace_transition_projection_panel_marker",
    "project_workspace_commit_plan_guard_panel_marker",
    "project_workspace_persist_request_rollback_panel_marker",
    "project_workspace_persist_gate_audit_panel_marker",
    "project_workspace_approval_policy_panel_marker",
    "project_workspace_runtime_readiness_panel_marker",
    "project_workspace_worker_loop_panel_marker",
    "project_workspace_worker_checkpoint_panel_marker",
    "project_workspace_finalization_panel_marker",
    "project_workspace_orchestration_readiness_panel_marker",
    "project_workspace_operator_control_panel_marker",
    "project_workspace_operator_approval_panel_marker",
    "project_workspace_approval_decision_panel_marker",
    "project_workspace_execution_sandbox_panel_marker",
    "project_workspace_provider_adapter_panel_marker",
    "project_workspace_provider_invocation_panel_marker",
    "project_workspace_provider_failure_panel_marker",
    "project_workspace_provider_observability_panel_marker",
    "project_workspace_capability_binding_panel_marker",
    "project_workspace_capability_invocation_gate_panel_marker",
    "project_workspace_capability_invocation_rehearsal_panel_marker",
    "project_workspace_capability_invocation_runbook_panel_marker",
    "project_workspace_capability_invocation_release_packet_panel_marker",
    "project_workspace_real_execution_mode_gate_panel_marker",
    "project_workspace_real_execution_readiness_summary_panel_marker",
    "project_workspace_real_execution_approval_request_panel_marker",
    "project_workspace_real_execution_approval_decision_panel_marker",
    "project_workspace_real_execution_launch_authorization_panel_marker",
    "project_workspace_real_execution_launch_monitor_panel_marker",
    "project_workspace_real_execution_incident_response_panel_marker",
    "project_workspace_real_execution_safety_chain_action_marker",
    "project_workspace_real_execution_safety_chain_audit_panel_marker",
    "project_workspace_real_execution_safety_timeline_marker",
    "project_workspace_runner_event_ledger_summary_marker",
    "project_workspace_supervisor_event_ledger_decision_marker",
    "project_workspace_supervisor_next_step_routing_plan_marker",
    "project_workspace_supervisor_next_step_work_order_preview_marker",
    "project_workspace_queue_lease_worker_dry_run_chain_marker",
    "project_workspace_agent_contract_registry_marker",
    "project_workspace_source_adapter_contract_marker",
    "project_workspace_multi_agent_output_chain_marker",
    "project_workspace_keyframe_video_asset_chain_marker",
    "project_workspace_keyframe_prompt_pack_marker",
    "project_workspace_manual_generation_result_marker",
    "project_workspace_provider_api_readiness_marker",
    "project_workspace_provider_sandbox_runtime_marker",
    "project_workspace_real_provider_execution_gate_marker",
    "project_workspace_provider_failure_recovery_marker",
    "project_workspace_provider_observability_report_marker",
    "project_workspace_provider_queue_lease_worker_marker",
    "project_workspace_provider_worker_checkpoint_resume_marker",
    "project_workspace_provider_worker_finalization_marker",
    "project_workspace_provider_artifact_lineage_marker",
    "project_workspace_provider_artifact_registry_restore_marker",
    "project_workspace_provider_registry_operation_approval_marker",
    "project_workspace_provider_registry_transaction_rehearsal_marker",
    "project_workspace_provider_transaction_monitor_marker",
    "project_workspace_provider_transaction_incident_drill_marker",
    "project_workspace_provider_execution_readiness_packet_marker",
    "project_workspace_agent_capability_runtime_marker",
    "project_workspace_creative_decision_pack_marker",
    "project_workspace_creative_decision_usability_marker",
    "project_workspace_creative_decision_quality_polish_marker",
    "project_workspace_creative_feedback_runtime_marker",
    "project_workspace_real_sample_export_flow_marker",
    "project_workspace_creative_variant_pack_marker",
    "project_workspace_creative_variant_selection_marker",
    "project_workspace_creative_test_feedback_marker",
    "project_workspace_creative_iteration_marker",
    "project_workspace_creative_version_control_marker",
    "project_workspace_creative_asset_pack_marker",
    "project_workspace_multi_platform_asset_pack_marker",
    "project_workspace_asset_quality_gate_marker",
    "project_workspace_campaign_export_pack_marker",
    "project_workspace_review_import_pack_marker",
    "project_workspace_competitor_review_comparison_marker",
    "project_workspace_llm_assist_dry_run_marker",
    "project_workspace_video_provider_orchestration_dry_run_marker",
    "project_workspace_session_snapshot_marker",
    "project_workspace_run_snapshot_compare_marker",
    "project_workspace_action_queue_marker",
    "project_workspace_action_ticket_marker",
    "project_workspace_approval_decision_marker",
    "project_workspace_execution_readiness_marker",
    "project_workspace_execution_rehearsal_marker",
    "project_workspace_rehearsal_remediation_marker",
    "project_workspace_remediation_verification_marker",
    "project_workspace_retry_rehearsal_plan_marker",
    "project_workspace_retry_rehearsal_result_marker",
    "project_workspace_retry_cycle_decision_marker",
    "project_workspace_cycle_history_timeline_marker",
    "project_workspace_control_center_marker",
    "project_workspace_agent_run_ledger_marker",
    "project_workspace_human_review_queue_marker",
    "project_workspace_capability_permission_matrix_marker",
    "project_workspace_system_integration_health_marker",
    "project_workspace_replay_harness_marker",
    "project_workspace_provider_adapter_contract_marker",
    "project_workspace_provider_contract_test_marker",
    "project_workspace_provider_mock_invocation_result_marker",
    "project_workspace_provider_failure_taxonomy_marker",
    "project_workspace_provider_asset_contract_marker",
    "project_workspace_provider_cost_quota_risk_guard_marker",
    "project_workspace_real_provider_readiness_checklist_marker",
    "project_workspace_secret_environment_gate_marker",
    "project_workspace_network_external_call_block_guard_marker",
    "project_workspace_real_execution_approval_token_marker",
    "project_workspace_provider_invocation_audit_packet_marker",
    "project_workspace_review_evidence_quality_marker",
    "project_workspace_claim_risk_guard_marker",
    "project_workspace_claim_safe_creative_brief_marker",
    "project_workspace_claim_safe_creative_output_marker",
    "project_workspace_claim_safe_platform_delivery_marker",
    "project_workspace_claim_safe_delivery_qa_marker",
    "project_workspace_claim_safe_delivery_remediation_marker",
    "project_workspace_claim_safe_remediation_verification_marker",
    "project_workspace_final_claim_safe_export_packet_marker",
    "project_workspace_safety_chain_history_summary_marker",
    "frontend_interaction_recovery_marker",
    "frontend_interaction_binding_repair_marker",
    "project_workspace_authorization_manifest_panel_marker",
    "critical_main_zh_override_marker",
    "zh_planner_clean_override_marker",
    "agent_graph_zh_override_marker",
    "copy_ready_script_zh_marker",
]


def _line_matches(text: str, marker: str) -> list[int]:
    return [
        index
        for index, line in enumerate(text.splitlines(), start=1)
        if marker in line
    ]


def run_frontend_quality_guard() -> dict:
    issues: list[dict] = []

    if not STATIC_INDEX.exists():
        issues.append({"type": "missing_file", "file": str(STATIC_INDEX)})
        html = ""
    else:
        html = STATIC_INDEX.read_text(encoding="utf-8")

    if not PUBLIC_SMOKE.exists():
        issues.append({"type": "missing_file", "file": str(PUBLIC_SMOKE)})
        smoke = ""
    else:
        smoke = PUBLIC_SMOKE.read_text(encoding="utf-8")

    mojibake_hits = []
    for marker in MOJIBAKE_MARKERS:
        lines = _line_matches(html, marker)
        if lines:
            mojibake_hits.append({"marker": marker, "lines": lines[:10]})

    if mojibake_hits:
        issues.append({"type": "mojibake", "hits": mojibake_hits})

    missing_html_markers = [
        marker for marker in REQUIRED_HTML_MARKERS if marker not in html
    ]
    if missing_html_markers:
        issues.append({
            "type": "missing_html_markers",
            "markers": missing_html_markers,
        })

    missing_smoke_markers = [
        marker for marker in REQUIRED_SMOKE_MARKERS if marker not in smoke
    ]
    if missing_smoke_markers:
        issues.append({
            "type": "missing_smoke_markers",
            "markers": missing_smoke_markers,
        })

    return {
        "ok": not issues,
        "checked_files": [
            STATIC_INDEX.relative_to(ROOT).as_posix(),
            PUBLIC_SMOKE.relative_to(ROOT).as_posix(),
        ],
        "html_marker_count": len(REQUIRED_HTML_MARKERS),
        "smoke_marker_count": len(REQUIRED_SMOKE_MARKERS),
        "mojibake_marker_count": len(MOJIBAKE_MARKERS),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check frontend copy and smoke marker quality.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    result = run_frontend_quality_guard()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("CrossGrowth frontend quality guard")
        print(f"OK: {result['ok']}")
        print(f"Checked files: {', '.join(result['checked_files'])}")
        print(f"HTML markers: {result['html_marker_count']}")
        print(f"Smoke markers: {result['smoke_marker_count']}")
        print(f"Mojibake markers: {result['mojibake_marker_count']}")
        if result["issues"]:
            print("Issues:")
            for issue in result["issues"]:
                print(json.dumps(issue, ensure_ascii=False))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
