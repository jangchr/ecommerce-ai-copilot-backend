"""Lightweight file-backed snapshots for Agent Graph OS demo continuity."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4


PERSISTENCE_MODE = "file_backed_lightweight_v1"
DURABILITY_NOTE = (
    "File-backed demo storage; durability depends on deployment storage configuration."
)
STORAGE_CATEGORIES = (
    "projects",
    "runs",
    "jobs",
    "artifacts",
    "assets",
    "events",
    "approvals",
    "messages",
    "snapshots",
    "exports",
)

DEFAULT_PROJECT_ID = "demo_project_default"
DEFAULT_PROJECT_NAME = "Demo Project"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _storage_root() -> Path:
    return Path(
        os.getenv("AGENT_GRAPH_STORAGE_PATH")
        or Path(__file__).resolve().parent / "storage" / "agent_graph"
    )


def _safe_key(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "")).strip("._")
    return (cleaned or fallback)[:160]


def persistence_metadata() -> dict[str, Any]:
    root = _storage_root()
    return {
        "persistence_mode": PERSISTENCE_MODE,
        "durability_note": DURABILITY_NOTE,
        "storage_configured": bool(os.getenv("AGENT_GRAPH_STORAGE_PATH")),
        "safe_path_hint": f".../{root.parent.name}/{root.name}",
    }


def _record_timestamp(record: dict[str, Any]) -> str:
    return str(
        record.get("updated_at")
        or record.get("created_at")
        or record.get("completed_at")
        or record.get("saved_at")
        or ""
    )


def _write_record(category: str, key: str, record: dict[str, Any]) -> dict[str, Any]:
    if category not in STORAGE_CATEGORIES:
        raise ValueError(f"unsupported agent graph storage category: {category}")
    directory = _storage_root() / category
    directory.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(record)
    payload.setdefault("saved_at", _utc_now_iso())
    payload.setdefault("persistence", persistence_metadata())
    final_path = directory / f"{_safe_key(key)}.json"
    temp_path = directory / f".{final_path.name}.{uuid4().hex}.tmp"
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    os.replace(temp_path, final_path)
    return deepcopy(payload)


def _read_records(category: str, limit: int) -> list[dict[str, Any]]:
    directory = _storage_root() / category
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in directory.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(payload, dict):
            records.append(payload)
    records.sort(key=_record_timestamp, reverse=True)
    return deepcopy(records[: max(1, int(limit or 1))])


def _read_record(category: str, key: str) -> dict[str, Any] | None:
    path = _storage_root() / category / f"{_safe_key(key)}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return deepcopy(payload) if isinstance(payload, dict) else None


def save_agent_run_snapshot(run: dict[str, Any]) -> dict[str, Any]:
    return _write_record("runs", str(run.get("run_id") or uuid4()), run)


def save_project_snapshot(project: dict[str, Any]) -> dict[str, Any]:
    return _write_record(
        "projects",
        str(project.get("project_id") or DEFAULT_PROJECT_ID),
        project,
    )


def save_project_index_entry(project: dict[str, Any]) -> dict[str, Any]:
    return save_project_snapshot(project)


def load_project(project_id: str) -> dict[str, Any] | None:
    return _read_record("projects", project_id or DEFAULT_PROJECT_ID)


def list_recent_projects(limit: int = 20) -> list[dict[str, Any]]:
    return _read_records("projects", limit)


def save_video_job_snapshot(job: dict[str, Any]) -> dict[str, Any]:
    return _write_record("jobs", str(job.get("job_id") or uuid4()), job)


def save_artifact_registry_snapshot(registry: dict[str, Any], key: str) -> dict[str, Any]:
    return _write_record("artifacts", key or str(uuid4()), registry)


def save_graph_event_snapshot(run_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    return _write_record(
        "events",
        run_id or str(uuid4()),
        {
            "run_id": run_id,
            "event_count": len(events or []),
            "events": deepcopy(events or []),
            "updated_at": _utc_now_iso(),
        },
    )


def save_approval_snapshot(approval: dict[str, Any], key: str) -> dict[str, Any]:
    return _write_record("approvals", key or str(uuid4()), approval)


def save_agent_message_snapshot(message: dict[str, Any]) -> dict[str, Any]:
    return _write_record(
        "messages",
        str(message.get("message_id") or uuid4()),
        message,
    )


def save_graph_state_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    key = (
        str(snapshot.get("snapshot_id") or "")
        or f"{snapshot.get('run_id') or snapshot.get('job_id') or 'graph'}_{uuid4().hex[:10]}"
    )
    return _write_record("snapshots", key, snapshot)


def save_graph_report_export(report: dict[str, Any]) -> dict[str, Any]:
    return _write_record(
        "exports",
        str(report.get("export_id") or uuid4()),
        report,
    )


def project_assets_directory(project_id: str) -> Path:
    path = _storage_root() / "projects" / _safe_key(project_id or DEFAULT_PROJECT_ID) / "assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _project_subdirectory(project_id: str, category: str) -> Path:
    allowed = {
        "sources",
        "source_artifacts",
        "source_quality_gates",
        "source_snapshots",
    }
    if category not in allowed:
        raise ValueError(f"unsupported project subdirectory: {category}")
    path = _storage_root() / "projects" / _safe_key(project_id or DEFAULT_PROJECT_ID) / category
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_project_record(
    project_id: str,
    category: str,
    key: str,
    record: dict[str, Any],
) -> dict[str, Any]:
    directory = _project_subdirectory(project_id, category)
    payload = deepcopy(record)
    payload["project_id"] = str(project_id or DEFAULT_PROJECT_ID)
    payload.setdefault("saved_at", _utc_now_iso())
    payload.setdefault("persistence", persistence_metadata())
    final_path = directory / f"{_safe_key(key)}.json"
    temp_path = directory / f".{final_path.name}.{uuid4().hex}.tmp"
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    os.replace(temp_path, final_path)
    return deepcopy(payload)


def _list_project_subrecords(
    project_id: str,
    category: str,
    limit: int,
) -> list[dict[str, Any]]:
    directory = _project_subdirectory(project_id, category)
    records: list[dict[str, Any]] = []
    for path in directory.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(payload, dict):
            records.append(payload)
    records.sort(key=_record_timestamp, reverse=True)
    return deepcopy(records[: max(1, int(limit or 1))])


def _load_project_subrecord(
    project_id: str,
    category: str,
    key: str,
) -> dict[str, Any] | None:
    path = _project_subdirectory(project_id, category) / f"{_safe_key(key)}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return deepcopy(payload) if isinstance(payload, dict) else None


def save_project_source_snapshot(source: dict[str, Any]) -> dict[str, Any]:
    return _write_project_record(
        str(source.get("project_id") or DEFAULT_PROJECT_ID),
        "sources",
        str(source.get("source_id") or uuid4()),
        source,
    )


def load_project_source(project_id: str, source_id: str) -> dict[str, Any] | None:
    return _load_project_subrecord(project_id, "sources", source_id)


def list_project_sources(project_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return _list_project_subrecords(project_id, "sources", limit)


def save_source_evidence_artifact(
    project_id: str,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    return _write_project_record(
        project_id,
        "source_artifacts",
        str(artifact.get("source_id") or artifact.get("artifact_id") or uuid4()),
        artifact,
    )


def load_source_evidence_artifact(
    project_id: str,
    source_id: str,
) -> dict[str, Any] | None:
    return _load_project_subrecord(project_id, "source_artifacts", source_id)


def list_source_evidence_artifacts(
    project_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    return _list_project_subrecords(project_id, "source_artifacts", limit)


def save_source_quality_gate(
    project_id: str,
    source_id: str,
    gate: dict[str, Any],
) -> dict[str, Any]:
    return _write_project_record(project_id, "source_quality_gates", source_id, gate)


def load_source_quality_gate(project_id: str, source_id: str) -> dict[str, Any] | None:
    return _load_project_subrecord(project_id, "source_quality_gates", source_id)


def list_source_quality_gates(project_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return _list_project_subrecords(project_id, "source_quality_gates", limit)


def save_source_snapshot(project_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    return _write_project_record(
        project_id,
        "source_snapshots",
        str(snapshot.get("source_id") or uuid4()),
        snapshot,
    )


def list_source_snapshots(project_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return _list_project_subrecords(project_id, "source_snapshots", limit)


def save_project_asset_snapshot(asset: dict[str, Any]) -> dict[str, Any]:
    project_id = str(asset.get("project_id") or DEFAULT_PROJECT_ID)
    payload = deepcopy(asset)
    payload["project_id"] = project_id
    return _write_record(
        "assets",
        f"{project_id}_{asset.get('asset_id') or uuid4()}",
        payload,
    )


def list_project_assets(project_id: str, limit: int = 50) -> list[dict[str, Any]]:
    safe_project_id = str(project_id or DEFAULT_PROJECT_ID)
    return [
        item
        for item in _read_records("assets", max(limit * 4, 100))
        if str(item.get("project_id") or DEFAULT_PROJECT_ID) == safe_project_id
    ][: max(1, int(limit or 1))]


def load_project_asset(project_id: str, asset_id: str) -> dict[str, Any] | None:
    safe_project_id = str(project_id or DEFAULT_PROJECT_ID)
    for asset in list_project_assets(safe_project_id, 200):
        if str(asset.get("asset_id") or "") == str(asset_id or ""):
            return asset
    return None


def list_project_records(category: str, project_id: str, limit: int = 20) -> list[dict[str, Any]]:
    safe_project_id = str(project_id or DEFAULT_PROJECT_ID)
    records = _read_records(category, max(limit * 5, 100))
    return [
        item
        for item in records
        if str(item.get("project_id") or DEFAULT_PROJECT_ID) == safe_project_id
    ][: max(1, int(limit or 1))]


def update_project_summary(
    project_id: str,
    related_object: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_project_id = str(project_id or DEFAULT_PROJECT_ID)
    project = load_project(safe_project_id) or {
        "project_version": "project_workspace_v1",
        "project_id": safe_project_id,
        "project_name": DEFAULT_PROJECT_NAME if safe_project_id == DEFAULT_PROJECT_ID else safe_project_id,
        "product_name": "",
        "product_category": "",
        "source_type": "demo" if safe_project_id == DEFAULT_PROJECT_ID else "manual",
        "status": "active",
        "created_at": _utc_now_iso(),
        **persistence_metadata(),
    }
    related = related_object if isinstance(related_object, dict) else {}
    object_project_id = str(related.get("project_id") or safe_project_id)
    if object_project_id == safe_project_id:
        if related.get("product_name") and not project.get("product_name"):
            project["product_name"] = str(related.get("product_name"))
        if related.get("product_category") and not project.get("product_category"):
            project["product_category"] = str(related.get("product_category"))
        if related.get("run_id"):
            project["latest_run_id"] = str(related.get("run_id"))
        if related.get("job_id"):
            project["latest_job_id"] = str(related.get("job_id"))
        registry_id = related.get("registry_id") or related.get("latest_artifact_registry_id")
        if registry_id:
            project["latest_artifact_registry_id"] = str(registry_id)

    runs = list_project_records("runs", safe_project_id, 200)
    jobs = list_project_records("jobs", safe_project_id, 200)
    artifacts = list_project_records("artifacts", safe_project_id, 200)
    exports = list_project_records("exports", safe_project_id, 200)
    assets = list_project_assets(safe_project_id, 200)
    sources = list_project_sources(safe_project_id, 200)
    source_artifacts = list_source_evidence_artifacts(safe_project_id, 200)
    source_quality_gates = list_source_quality_gates(safe_project_id, 200)
    source_snapshots = list_source_snapshots(safe_project_id, 200)
    experiments = sum(len(item.get("external_video_experiments") or []) for item in jobs)
    approvals = sum(bool(item.get("latest_human_approval_gate")) for item in jobs)
    project["graph_summary"] = {
        "run_count": len(runs),
        "job_count": len(jobs),
        "artifact_count": sum(
            int((item.get("artifact_counts") or {}).get("total") or 0)
            for item in artifacts
        ),
        "experiment_count": experiments,
        "approval_count": approvals,
        "asset_count": len(assets),
        "report_count": len(exports),
        "source_count": len(sources),
        "source_artifact_count": len(source_artifacts),
        "source_quality_gate_count": len(source_quality_gates),
        "source_snapshot_count": len(source_snapshots),
        "latest_source_id": str((sources[0] if sources else {}).get("source_id") or ""),
        "latest_source_type": str((sources[0] if sources else {}).get("source_type") or ""),
        "latest_source_confidence": float((sources[0] if sources else {}).get("source_confidence") or 0.0),
        "latest_source_gate_status": str((source_quality_gates[0] if source_quality_gates else {}).get("status") or ""),
        "manual_fallback_required_count": sum(
            bool((item.get("source_summary") or {}).get("manual_fallback_needed"))
            for item in sources
        ),
    }
    project["updated_at"] = _utc_now_iso()
    project.setdefault("latest_run_id", None)
    project.setdefault("latest_job_id", None)
    project.setdefault("latest_artifact_registry_id", None)
    return save_project_snapshot(project)


def load_recent_agent_run_snapshots(limit: int = 10) -> list[dict[str, Any]]:
    return _read_records("runs", limit)


def load_recent_video_job_snapshots(limit: int = 10) -> list[dict[str, Any]]:
    return _read_records("jobs", limit)


def load_artifact_registry_snapshot(key: str) -> dict[str, Any] | None:
    return _read_record("artifacts", key)


def list_recent_artifacts(limit: int = 20) -> list[dict[str, Any]]:
    return _read_records("artifacts", limit)


def list_recent_graph_events(limit: int = 50) -> list[dict[str, Any]]:
    records = _read_records("events", limit)
    summaries: list[dict[str, Any]] = []
    for record in records:
        run_id = str(record.get("run_id") or "")
        for event in reversed(record.get("events") or []):
            if not isinstance(event, dict):
                continue
            summaries.append(
                {
                    "run_id": run_id,
                    "event_id": event.get("event_id", ""),
                    "event_type": event.get("event_type", ""),
                    "agent_id": event.get("agent_id", ""),
                    "message": event.get("message", ""),
                    "created_at": event.get("created_at", ""),
                }
            )
            if len(summaries) >= max(1, int(limit or 1)):
                return summaries
    return summaries


def list_recent_agent_messages(limit: int = 50) -> list[dict[str, Any]]:
    return _read_records("messages", limit)


def list_recent_graph_snapshots(limit: int = 20) -> list[dict[str, Any]]:
    return _read_records("snapshots", limit)


def list_recent_graph_exports(limit: int = 20) -> list[dict[str, Any]]:
    return _read_records("exports", limit)
