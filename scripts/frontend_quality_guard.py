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
