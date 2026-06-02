"""Simulated provider runtime helpers for video generation jobs."""

from __future__ import annotations

import time
from uuid import uuid4
from typing import Any

from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
    build_video_job_history_event,
    normalize_video_job_status,
)
from video_generation.providers import get_video_provider_config
from video_generation.provider_integration import provider_integration_readiness


PROVIDER_RUNTIME_MODE = "simulated_provider_polling"


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def supports_provider_polling(provider: str) -> bool:
    config = get_video_provider_config(provider)
    return bool(config.get("supports_async_polling") or config.get("create_mode") == "planned_external_api")


def simulated_provider_job_id(provider: str) -> str:
    provider_key = str(provider or "provider").strip().lower().replace(" ", "_") or "provider"
    return f"{provider_key}_sim_{uuid4().hex[:12]}"


def build_provider_runtime(
    provider: str,
    provider_job_id: str = "",
    notes: str = "",
    now: str | None = None,
) -> dict[str, Any]:
    timestamp = now or _utc_now_iso()
    return {
        "provider_job_id": str(provider_job_id or simulated_provider_job_id(provider)),
        "provider_status": VIDEO_JOB_STATUS_QUEUED,
        "submitted_at": timestamp,
        "last_polled_at": "",
        "poll_count": 0,
        "mode": PROVIDER_RUNTIME_MODE,
        "integration_mode": "simulated",
        "real_external_api_call_enabled": False,
        "external_api_called": False,
        "integration_readiness": provider_integration_readiness(provider),
        "notes": str(notes or ""),
    }


def provider_submit_history_events(provider: str, status: str, now: str | None = None) -> list[dict[str, Any]]:
    timestamp = now or _utc_now_iso()
    return [
        build_video_job_history_event(
            "provider_submitted",
            status,
            updated_at=timestamp,
            provider=provider,
            external_api_called=False,
        )
    ]


def next_simulated_provider_status(current_status: str, requested_status: str = "") -> str:
    requested = normalize_video_job_status(requested_status, fallback="")
    if requested in {VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY, VIDEO_JOB_STATUS_FAILED, VIDEO_JOB_STATUS_PROCESSING}:
        return requested
    current = normalize_video_job_status(current_status, fallback=VIDEO_JOB_STATUS_QUEUED)
    if current == VIDEO_JOB_STATUS_QUEUED:
        return VIDEO_JOB_STATUS_PROCESSING
    if current == VIDEO_JOB_STATUS_PROCESSING:
        return VIDEO_JOB_STATUS_PROCESSING
    return current


def build_provider_poll_runtime(
    runtime: dict[str, Any],
    next_status: str,
    error_message: str = "",
    notes: str = "",
    now: str | None = None,
) -> dict[str, Any]:
    timestamp = now or _utc_now_iso()
    updated = dict(runtime or {})
    updated["provider_status"] = next_status
    updated["last_polled_at"] = timestamp
    updated["poll_count"] = int(updated.get("poll_count") or 0) + 1
    updated["mode"] = updated.get("mode") or PROVIDER_RUNTIME_MODE
    updated["integration_mode"] = "simulated"
    updated["real_external_api_call_enabled"] = False
    updated["external_api_called"] = False
    if error_message:
        updated["error_message"] = str(error_message)
    if notes:
        updated["notes"] = str(notes)
    return updated


def provider_poll_history_event(provider: str, status: str, runtime: dict[str, Any], now: str | None = None) -> dict[str, Any]:
    return build_video_job_history_event(
        "provider_polled",
        status,
        updated_at=now or _utc_now_iso(),
        provider=provider,
        provider_job_id=runtime.get("provider_job_id", ""),
        provider_status=runtime.get("provider_status", ""),
        poll_count=runtime.get("poll_count", 0),
        external_api_called=False,
    )
