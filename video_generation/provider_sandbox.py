"""Safe feature-flag contract for future external video providers."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from video_generation.providers import get_video_provider_config, normalize_video_provider


EXTERNAL_CALLS_FEATURE_FLAG = "VIDEO_PROVIDER_EXTERNAL_CALLS_ENABLED"
TRUTHY_VALUES = {"1", "true", "yes", "on"}


def _env_value(env: Mapping[str, str], key: str) -> str:
    return str(env.get(key) or "").strip()


def _flag_enabled(env: Mapping[str, str]) -> bool:
    return _env_value(env, EXTERNAL_CALLS_FEATURE_FLAG).lower() in TRUTHY_VALUES


def provider_external_call_settings(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env_source = env if env is not None else os.environ
    enabled = _flag_enabled(env_source)
    return {
        "feature_flag_name": EXTERNAL_CALLS_FEATURE_FLAG,
        "feature_flag_enabled": enabled,
        "can_call_external_api": False,
        "real_external_api_call_enabled": False,
        "external_api_called": False,
        "integration_mode": "sandbox_flag_enabled" if enabled else "simulated",
    }


def provider_sandbox_readiness(provider: str, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env_source = env if env is not None else os.environ
    config = get_video_provider_config(provider)
    provider_name = normalize_video_provider(provider) or str(provider or "")
    settings = provider_external_call_settings(env_source)
    flag_enabled = bool(settings["feature_flag_enabled"])

    if not config:
        return {
            "provider": provider_name,
            "feature_flag_name": EXTERNAL_CALLS_FEATURE_FLAG,
            "feature_flag_enabled": flag_enabled,
            "api_key_configured": False,
            "can_call_external_api": False,
            "real_external_api_call_enabled": False,
            "external_api_called": False,
            "integration_mode": "unknown_provider",
            "disabled_reason": "Unknown video provider.",
            "sandbox_ready": False,
            "warnings": ["Unknown video provider."],
        }

    requires_api_key = bool(config.get("requires_api_key"))
    env_key_name = str(config.get("env_key_name") or "")
    api_key_configured = bool(env_key_name and _env_value(env_source, env_key_name))

    warnings = [
        "No real external video API request is made in this sandbox scaffold.",
        "Provider-specific HTTP client, request mapping, timeout, retry, polling, and result normalization are future work.",
    ]
    if not requires_api_key:
        integration_mode = "manual_or_prompt_export"
        disabled_reason = "This provider uses manual/prompt export and does not call an external API."
        sandbox_ready = False
        warnings.append("No provider API key is required for this manual/export flow.")
    elif not flag_enabled:
        integration_mode = "simulated"
        disabled_reason = f"{EXTERNAL_CALLS_FEATURE_FLAG} is false; provider flow remains simulated."
        sandbox_ready = False
        warnings.append(f"Set {EXTERNAL_CALLS_FEATURE_FLAG}=true only when intentionally testing provider sandbox behavior.")
    elif not api_key_configured:
        integration_mode = "blocked_missing_api_key"
        disabled_reason = f"{env_key_name} is not configured; external provider call is blocked."
        sandbox_ready = False
        warnings.append(f"{env_key_name} must be configured before any future real provider adapter can run.")
    else:
        integration_mode = "sandbox_ready_no_external_call"
        disabled_reason = "API key presence detected, but no real provider adapter is enabled in this batch."
        sandbox_ready = True
        warnings.append("API key value is intentionally not exposed and no external request is attempted.")

    return {
        "provider": str(config.get("provider") or provider_name),
        "feature_flag_name": EXTERNAL_CALLS_FEATURE_FLAG,
        "feature_flag_enabled": flag_enabled,
        "api_key_configured": api_key_configured,
        "can_call_external_api": False,
        "real_external_api_call_enabled": False,
        "external_api_called": False,
        "integration_mode": integration_mode,
        "disabled_reason": disabled_reason,
        "sandbox_ready": sandbox_ready,
        "warnings": warnings,
    }


def build_provider_sandbox_request_preview(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("provider_payload") if isinstance(job.get("provider_payload"), dict) else {}
    runtime = job.get("provider_runtime") if isinstance(job.get("provider_runtime"), dict) else {}
    return {
        "job_id": str(job.get("job_id") or ""),
        "provider": normalize_video_provider(str(job.get("provider") or "")) or str(job.get("provider") or ""),
        "provider_job_id": str(runtime.get("provider_job_id") or ""),
        "selected_export_key": str(payload.get("selected_export_key") or ""),
        "prompt_present": bool(payload.get("prompt")),
        "scene_count": int(payload.get("scene_count") or 0),
        "recommended_duration_seconds": int(payload.get("recommended_duration_seconds") or 0),
        "aspect_ratio": str(payload.get("aspect_ratio") or ""),
        "secrets_included": False,
    }


def blocked_provider_external_call_result(provider: str, reason: str) -> dict[str, Any]:
    readiness = provider_sandbox_readiness(provider)
    return {
        "provider": readiness.get("provider", normalize_video_provider(provider) or str(provider or "")),
        "status": "blocked",
        "reason": str(reason or readiness.get("disabled_reason") or "external provider call blocked"),
        "integration_mode": readiness.get("integration_mode", "simulated"),
        "feature_flag_enabled": bool(readiness.get("feature_flag_enabled", False)),
        "can_call_external_api": False,
        "real_external_api_call_enabled": False,
        "external_api_called": False,
        "api_key_configured": bool(readiness.get("api_key_configured", False)),
    }
