"""Fake provider client contracts for future video API integration tests."""

from __future__ import annotations

from uuid import uuid4
from typing import Any

from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
    normalize_video_job_status,
)
from video_generation.providers import normalize_video_provider


FAKE_CLIENT_MODE = "fake_no_network"
FAKE_PROVIDER_STATUSES = {
    VIDEO_JOB_STATUS_QUEUED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
}


def _compact_text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _fake_provider_job_id(provider: str) -> str:
    return f"{provider}_fake_{uuid4().hex[:12]}"


def build_provider_create_request(job: dict[str, Any]) -> dict[str, Any]:
    provider = normalize_video_provider(str(job.get("provider") or "")) or str(job.get("provider") or "")
    provider_payload = job.get("provider_payload") if isinstance(job.get("provider_payload"), dict) else {}
    scenes = provider_payload.get("scenes") if isinstance(provider_payload.get("scenes"), list) else []
    scene_count = len(scenes) if scenes else int(provider_payload.get("scene_count") or 0)
    return {
        "provider": provider,
        "job_id": str(job.get("job_id") or ""),
        "selected_export_key": str(provider_payload.get("selected_export_key") or ""),
        "prompt": _compact_text(provider_payload.get("prompt"), limit=4000),
        "prompt_present": bool(provider_payload.get("prompt")),
        "scene_count": scene_count,
        "scenes": scenes[:4],
        "aspect_ratio": str(provider_payload.get("aspect_ratio") or ""),
        "duration_seconds": int(provider_payload.get("recommended_duration_seconds") or 0),
        "metadata": {
            "provider": provider,
            "job_id": str(job.get("job_id") or ""),
            "selected_export_key": str(provider_payload.get("selected_export_key") or ""),
        },
        "secrets_included": False,
        "external_api_called": False,
    }


def normalize_provider_create_response(provider: str, response: dict[str, Any]) -> dict[str, Any]:
    return normalize_provider_status_response(provider, response)


def normalize_provider_status_response(provider: str, response: dict[str, Any]) -> dict[str, Any]:
    payload = response if isinstance(response, dict) else {}
    provider_name = normalize_video_provider(provider) or str(provider or "")
    provider_status = normalize_video_job_status(
        str(payload.get("provider_status") or payload.get("status") or VIDEO_JOB_STATUS_PROCESSING),
        fallback=VIDEO_JOB_STATUS_PROCESSING,
    )
    if provider_status not in FAKE_PROVIDER_STATUSES:
        provider_status = VIDEO_JOB_STATUS_PROCESSING
    raw_response_safe = {
        "provider_status": provider_status,
        "has_result_url": bool(payload.get("result_url") or payload.get("video_url")),
        "has_preview_url": bool(payload.get("preview_url") or payload.get("thumbnail_url")),
        "has_download_url": bool(payload.get("download_url")),
        "external_api_called": False,
    }
    return {
        "provider": provider_name,
        "provider_job_id": str(payload.get("provider_job_id") or payload.get("id") or ""),
        "provider_status": provider_status,
        "result_url": str(payload.get("result_url") or payload.get("video_url") or ""),
        "preview_url": str(payload.get("preview_url") or payload.get("thumbnail_url") or ""),
        "download_url": str(payload.get("download_url") or ""),
        "error_message": str(payload.get("error_message") or payload.get("error") or ""),
        "raw_response_safe": raw_response_safe,
        "external_api_called": False,
    }


class ProviderClient:
    provider = ""
    supports_real_network = False

    def create_video_job(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def get_video_job(self, provider_job_id: str, state: str = "") -> dict[str, Any]:
        raise NotImplementedError

    def normalize_response(self, response: dict[str, Any]) -> dict[str, Any]:
        return normalize_provider_status_response(self.provider, response)


class FakeProviderClient(ProviderClient):
    provider = "provider"
    supports_real_network = False

    def create_video_job(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_job_id": _fake_provider_job_id(self.provider),
            "provider_status": VIDEO_JOB_STATUS_QUEUED,
            "result_url": "",
            "preview_url": "",
            "download_url": "",
            "error_message": "",
            "request_preview": {
                "job_id": str(request.get("job_id") or ""),
                "selected_export_key": str(request.get("selected_export_key") or ""),
                "prompt_present": bool(request.get("prompt")),
                "scene_count": int(request.get("scene_count") or 0),
                "secrets_included": False,
            },
            "external_api_called": False,
            "client_mode": FAKE_CLIENT_MODE,
        }

    def get_video_job(self, provider_job_id: str, state: str = "") -> dict[str, Any]:
        status = normalize_video_job_status(state, fallback=VIDEO_JOB_STATUS_PROCESSING)
        if status not in FAKE_PROVIDER_STATUSES:
            status = VIDEO_JOB_STATUS_PROCESSING
        result_url = ""
        preview_url = ""
        download_url = ""
        if status == VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY:
            result_url = f"https://example.com/{self.provider}/{provider_job_id}.mp4"
            preview_url = f"https://example.com/{self.provider}/{provider_job_id}.jpg"
            download_url = result_url
        return {
            "provider": self.provider,
            "provider_job_id": str(provider_job_id or _fake_provider_job_id(self.provider)),
            "provider_status": status,
            "result_url": result_url,
            "preview_url": preview_url,
            "download_url": download_url,
            "error_message": "fake provider failure" if status == VIDEO_JOB_STATUS_FAILED else "",
            "external_api_called": False,
            "client_mode": FAKE_CLIENT_MODE,
        }


class FakeRunwayClient(FakeProviderClient):
    provider = "runway"


class FakePikaClient(FakeProviderClient):
    provider = "pika"


def build_provider_client(provider: str, mode: str = "fake") -> ProviderClient:
    provider_name = normalize_video_provider(provider)
    if mode != "fake":
        raise ValueError("Only fake provider clients are available; real provider clients are not implemented.")
    if provider_name == "runway":
        return FakeRunwayClient()
    if provider_name == "pika":
        return FakePikaClient()
    raise ValueError(f"Unsupported fake provider client: {provider}")
