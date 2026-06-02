"""Disabled-by-default contract helpers for future video provider APIs."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from video_generation.providers import get_video_provider_config, normalize_video_provider


INTEGRATION_DISABLED_REASON = "Real external provider API integration is not enabled yet."
MANUAL_EXPORT_DISABLED_REASON = "This provider is a manual/export flow and does not call an external API."

ERROR_CATEGORIES = (
    "provider_unavailable",
    "provider_timeout",
    "provider_auth_error",
    "provider_rate_limited",
    "provider_payload_error",
    "provider_result_missing",
    "unknown_provider_error",
)


def provider_integration_config(provider: str) -> dict[str, Any]:
    config = get_video_provider_config(provider)
    if not config:
        return {}
    return {
        "provider": config["provider"],
        "external_api_ready": False,
        "integration_enabled": False,
        "requires_api_key": bool(config.get("requires_api_key")),
        "env_key_name": str(config.get("env_key_name") or ""),
        "supports_async_polling": bool(config.get("supports_async_polling")),
        "create_mode": str(config.get("create_mode") or ""),
        "selected_export_key": str(config.get("export_key") or ""),
    }


def provider_integration_readiness(provider: str, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    config = provider_integration_config(provider)
    if not config:
        return {
            "provider": normalize_video_provider(provider) or str(provider or ""),
            "external_api_ready": False,
            "integration_enabled": False,
            "requires_api_key": False,
            "env_key_name": "",
            "api_key_configured": False,
            "can_call_external_api": False,
            "disabled_reason": "Unknown video provider.",
            "warnings": ["Unknown video provider."],
        }

    env_source = env if env is not None else os.environ
    env_key = config["env_key_name"]
    api_key_configured = bool(env_key and str(env_source.get(env_key) or "").strip())
    disabled_reason = INTEGRATION_DISABLED_REASON if config["requires_api_key"] else MANUAL_EXPORT_DISABLED_REASON
    warnings = [
        "Real external video API calls are disabled in this scaffold.",
        "Use manual export/provider polling scaffold until the provider contract is verified.",
    ]
    if config["requires_api_key"]:
        warnings.append(f"{env_key} is required before a real integration can be enabled.")
    return {
        "provider": config["provider"],
        "external_api_ready": False,
        "integration_enabled": False,
        "requires_api_key": config["requires_api_key"],
        "env_key_name": env_key,
        "api_key_configured": api_key_configured,
        "can_call_external_api": False,
        "disabled_reason": disabled_reason,
        "warnings": warnings,
    }


def provider_polling_contract(provider: str) -> dict[str, Any]:
    config = provider_integration_config(provider)
    provider_name = config.get("provider") or normalize_video_provider(provider) or str(provider or "")
    return {
        "provider": provider_name,
        "mode": "simulated_provider_polling",
        "external_api_called": False,
        "default_submit_status": "queued",
        "default_poll_sequence": ["queued", "processing"],
        "completion_statuses": ["external_result_ready", "failed"],
        "timeout_seconds": 30,
        "max_poll_attempts": 20,
        "requires_provider_job_id": True,
        "notes": "No real provider polling is performed until integration_enabled is true in a future contract.",
    }


def build_provider_request_contract(job: dict[str, Any]) -> dict[str, Any]:
    provider = normalize_video_provider(job.get("provider", "")) or str(job.get("provider", "") or "")
    provider_payload = job.get("provider_payload") if isinstance(job.get("provider_payload"), dict) else {}
    runtime = job.get("provider_runtime") if isinstance(job.get("provider_runtime"), dict) else {}
    return {
        "provider": provider,
        "job_id": str(job.get("job_id") or ""),
        "provider_job_id": str(runtime.get("provider_job_id") or job.get("result", {}).get("provider_job_id") or ""),
        "selected_export_key": str(provider_payload.get("selected_export_key") or ""),
        "prompt_present": bool(provider_payload.get("prompt")),
        "scene_count": int(provider_payload.get("scene_count") or 0),
        "recommended_duration_seconds": int(provider_payload.get("recommended_duration_seconds") or 0),
        "aspect_ratio": str(provider_payload.get("aspect_ratio") or ""),
        "request_shape": {
            "prompt": "provider_payload.prompt",
            "scenes": "provider_payload.scenes",
            "aspect_ratio": "provider_payload.aspect_ratio",
            "duration_seconds": "provider_payload.recommended_duration_seconds",
            "metadata": "job_id/provider/selected_export_key",
        },
        "secrets_included": False,
    }


def normalize_provider_response(provider: str, response: dict[str, Any]) -> dict[str, Any]:
    payload = response if isinstance(response, dict) else {}
    provider_name = normalize_video_provider(provider) or str(provider or "")
    status = str(payload.get("status") or payload.get("provider_status") or "processing")
    return {
        "provider": provider_name,
        "provider_status": status,
        "provider_job_id": str(payload.get("provider_job_id") or payload.get("id") or ""),
        "result_url": str(payload.get("result_url") or payload.get("video_url") or ""),
        "preview_url": str(payload.get("preview_url") or payload.get("thumbnail_url") or ""),
        "download_url": str(payload.get("download_url") or ""),
        "error_message": str(payload.get("error_message") or payload.get("error") or ""),
        "raw_response_stored": False,
    }


def provider_error_contract(provider: str, error: dict[str, Any] | str) -> dict[str, Any]:
    provider_name = normalize_video_provider(provider) or str(provider or "")
    if isinstance(error, dict):
        message = str(error.get("message") or error.get("error") or "")
        category = str(error.get("category") or error.get("error_type") or "unknown_provider_error")
    else:
        message = str(error or "")
        category = "unknown_provider_error"
    if category not in ERROR_CATEGORIES:
        category = "unknown_provider_error"
    return {
        "provider": provider_name,
        "error_category": category,
        "message": message[:500],
        "retryable": category in {"provider_unavailable", "provider_timeout", "provider_rate_limited"},
        "safe_for_logs": True,
    }


def provider_plan_integration_metadata(provider: str) -> dict[str, Any]:
    readiness = provider_integration_readiness(provider)
    return {
        "integration_readiness": readiness,
        "polling_contract": provider_polling_contract(provider),
        "request_contract_summary": {
            "secrets_included": False,
            "uses_provider_payload_prompt": True,
            "uses_scene_list": True,
            "requires_provider_job_id_for_polling": True,
        },
        "error_contract_summary": {
            "categories": list(ERROR_CATEGORIES),
            "raw_tracebacks_exposed": False,
            "api_key_values_exposed": False,
        },
    }
