"""Status helpers for video generation job lifecycle."""

from __future__ import annotations

import time
from typing import Any


VIDEO_JOB_STATUS_CREATED = "created"
VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT = "ready_for_manual_export"
VIDEO_JOB_STATUS_QUEUED = "queued"
VIDEO_JOB_STATUS_PROCESSING = "processing"
VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED = "manual_export_completed"
VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY = "external_result_ready"
VIDEO_JOB_STATUS_FAILED = "failed"
VIDEO_JOB_STATUS_CANCELLED = "cancelled"

VIDEO_JOB_STATUSES = {
    VIDEO_JOB_STATUS_CREATED,
    VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    VIDEO_JOB_STATUS_QUEUED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_CANCELLED,
}

VIDEO_JOB_TERMINAL_STATUSES = {
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_CANCELLED,
}

VIDEO_JOB_ACTIVE_STATUSES = {
    VIDEO_JOB_STATUS_QUEUED,
    VIDEO_JOB_STATUS_PROCESSING,
}

VIDEO_JOB_MANUAL_STATUSES = {
    VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
}

VIDEO_JOB_TRANSITIONS = {
    VIDEO_JOB_STATUS_CREATED: {
        VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
        VIDEO_JOB_STATUS_QUEUED,
        VIDEO_JOB_STATUS_FAILED,
        VIDEO_JOB_STATUS_CANCELLED,
    },
    VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT: {
        VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
        VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
        VIDEO_JOB_STATUS_QUEUED,
        VIDEO_JOB_STATUS_FAILED,
        VIDEO_JOB_STATUS_CANCELLED,
    },
    VIDEO_JOB_STATUS_QUEUED: {
        VIDEO_JOB_STATUS_PROCESSING,
        VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
        VIDEO_JOB_STATUS_FAILED,
        VIDEO_JOB_STATUS_CANCELLED,
    },
    VIDEO_JOB_STATUS_PROCESSING: {
        VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
        VIDEO_JOB_STATUS_FAILED,
        VIDEO_JOB_STATUS_CANCELLED,
    },
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED: {
        VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
        VIDEO_JOB_STATUS_FAILED,
    },
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY: set(),
    VIDEO_JOB_STATUS_FAILED: set(),
    VIDEO_JOB_STATUS_CANCELLED: set(),
}


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_video_job_status(
    status: str,
    fallback: str = VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
) -> str:
    value = str(status or "").strip().lower()
    return value if value in VIDEO_JOB_STATUSES else fallback


def is_valid_video_job_status(status: str) -> bool:
    return str(status or "").strip().lower() in VIDEO_JOB_STATUSES


def can_transition_video_job_status(current: str, next_status: str) -> bool:
    current_status = normalize_video_job_status(current)
    target_status = normalize_video_job_status(next_status)
    if current_status == target_status:
        return True
    return target_status in VIDEO_JOB_TRANSITIONS.get(current_status, set())


def video_job_status_metadata(status: str) -> dict[str, Any]:
    normalized = normalize_video_job_status(status)
    return {
        "status": normalized,
        "is_terminal": normalized in VIDEO_JOB_TERMINAL_STATUSES,
        "is_active": normalized in VIDEO_JOB_ACTIVE_STATUSES,
        "is_manual": normalized in VIDEO_JOB_MANUAL_STATUSES,
        "allowed_next_statuses": sorted(VIDEO_JOB_TRANSITIONS.get(normalized, set())),
    }


def build_video_job_history_event(event: str, status: str, **kwargs: Any) -> dict[str, Any]:
    payload = {
        "event": str(event or "status_changed"),
        "status": normalize_video_job_status(status),
        "updated_at": str(kwargs.pop("updated_at", "") or _utc_now_iso()),
    }
    payload.update({key: value for key, value in kwargs.items() if value is not None})
    return payload
