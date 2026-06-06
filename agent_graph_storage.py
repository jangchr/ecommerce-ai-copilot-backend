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
    "runs",
    "jobs",
    "artifacts",
    "events",
    "approvals",
    "messages",
    "snapshots",
    "exports",
)


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

