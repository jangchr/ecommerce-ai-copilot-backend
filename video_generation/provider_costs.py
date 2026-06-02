"""Configurable cost estimate scaffold for video provider planning."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from video_generation.providers import normalize_video_provider


PRICING_ESTIMATE_WARNING = "Pricing is an internal estimate and can change. Review official pricing before enabling real provider calls."
USER_CONFIRMATION_WARNING = "User confirmation is required before any cost-incurring video generation."
NO_EXTERNAL_API_WARNING = "No external video API cost is incurred in the current manual or simulated flow."

VIDEO_PROVIDER_COST_CATALOG: dict[str, dict[str, Any]] = {
    "manual_export": {
        "provider": "manual_export",
        "model": "manual_export",
        "label": "Manual export",
        "estimated_cost_per_second_usd": 0.0,
        "external_api_call_planned": False,
        "notes": ["Manual export has no provider API cost in this app."],
    },
    "generic": {
        "provider": "generic",
        "model": "generic",
        "label": "Generic video prompt",
        "estimated_cost_per_second_usd": 0.0,
        "external_api_call_planned": False,
        "notes": ["Generic prompt export has no provider API cost in this app."],
    },
    "capcut": {
        "provider": "capcut",
        "model": "capcut",
        "label": "CapCut manual shot list",
        "estimated_cost_per_second_usd": 0.0,
        "external_api_call_planned": False,
        "notes": ["CapCut shot-list export is manual; no external editor API is called."],
    },
    "fal_pika_720p": {
        "provider": "pika",
        "model": "fal_pika_720p",
        "label": "FAL Pika 720p estimate",
        "estimated_cost_per_second_usd": 0.06,
        "external_api_call_planned": False,
        "notes": ["Estimate only; confirm current provider pricing and free-tier terms."],
    },
    "fal_pika_1080p": {
        "provider": "pika",
        "model": "fal_pika_1080p",
        "label": "FAL Pika 1080p estimate",
        "estimated_cost_per_second_usd": 0.10,
        "external_api_call_planned": False,
        "notes": ["Estimate only; higher resolution can cost more."],
    },
    "fal_luma_flash": {
        "provider": "generic",
        "model": "fal_luma_flash",
        "label": "FAL Luma Flash estimate",
        "estimated_cost_per_second_usd": 0.08,
        "external_api_call_planned": False,
        "notes": ["Estimate only; review provider docs before enabling."],
    },
    "fal_kling": {
        "provider": "generic",
        "model": "fal_kling",
        "label": "FAL Kling estimate",
        "estimated_cost_per_second_usd": 0.14,
        "external_api_call_planned": False,
        "notes": ["Estimate only; review provider docs before enabling."],
    },
    "runway_gen4_turbo": {
        "provider": "runway",
        "model": "runway_gen4_turbo",
        "label": "Runway Gen-4 Turbo estimate",
        "estimated_cost_per_second_usd": 0.12,
        "external_api_call_planned": False,
        "notes": ["Estimate only; Runway real API integration remains disabled."],
    },
    "veo_fast": {
        "provider": "generic",
        "model": "veo_fast",
        "label": "Veo fast estimate",
        "estimated_cost_per_second_usd": 0.20,
        "external_api_call_planned": False,
        "notes": ["Estimate only; review official pricing before enabling."],
    },
    "veo_standard": {
        "provider": "generic",
        "model": "veo_standard",
        "label": "Veo standard estimate",
        "estimated_cost_per_second_usd": 0.35,
        "external_api_call_planned": False,
        "notes": ["Estimate only; review official pricing before enabling."],
    },
}

DEFAULT_MODEL_BY_PROVIDER = {
    "manual_export": "manual_export",
    "generic": "generic",
    "capcut": "capcut",
    "runway": "runway_gen4_turbo",
    "pika": "fal_pika_720p",
}


def _positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return fallback
    return max(1, parsed)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def video_provider_cost_catalog() -> list[dict[str, Any]]:
    return [deepcopy(item) for item in VIDEO_PROVIDER_COST_CATALOG.values()]


def video_provider_cost_level(estimated_cost_usd: float | None) -> str:
    if estimated_cost_usd is None:
        return "unknown"
    if estimated_cost_usd <= 0:
        return "free"
    if estimated_cost_usd < 1:
        return "low"
    if estimated_cost_usd < 5:
        return "medium"
    return "high"


def _catalog_entry(provider: str, model: str) -> tuple[str, dict[str, Any] | None]:
    provider_name = normalize_video_provider(provider) or str(provider or "manual_export").strip().lower()
    model_name = str(model or "").strip().lower()
    if not model_name:
        model_name = DEFAULT_MODEL_BY_PROVIDER.get(provider_name, provider_name)
    entry = VIDEO_PROVIDER_COST_CATALOG.get(model_name)
    if not entry:
        entry = VIDEO_PROVIDER_COST_CATALOG.get(provider_name)
    return model_name, deepcopy(entry) if entry else None


def estimate_video_generation_cost(
    provider: str,
    model: str = "",
    duration_seconds: int = 5,
    clip_count: int = 1,
    retry_count: int = 1,
    budget_usd: float | None = None,
) -> dict[str, Any]:
    duration = _positive_int(duration_seconds, 5)
    clips = _positive_int(clip_count, 1)
    retries = _positive_int(retry_count, 1)
    budget = _optional_float(budget_usd)
    provider_name = normalize_video_provider(provider) or str(provider or "manual_export").strip().lower()
    model_name, entry = _catalog_entry(provider_name, model)

    warnings = [PRICING_ESTIMATE_WARNING, "Retries and multiple clips can multiply estimated cost."]
    if not entry:
        warnings.append("Unknown provider/model estimate. Treat as unavailable until pricing is reviewed.")
        return {
            "provider": provider_name,
            "model": model_name,
            "pricing_is_estimate": True,
            "estimated_cost_per_second_usd": None,
            "duration_seconds": duration,
            "clip_count": clips,
            "retry_count": retries,
            "estimated_billable_seconds": duration * clips * retries,
            "estimated_cost_usd": None,
            "cost_level": "unknown",
            "requires_user_confirmation": True,
            "external_api_call_planned": False,
            "budget_usd": budget,
            "within_budget": None,
            "warnings": warnings,
        }

    per_second = float(entry.get("estimated_cost_per_second_usd") or 0.0)
    billable_seconds = duration * clips * retries
    estimated_cost = round(per_second * billable_seconds, 4)
    requires_confirmation = estimated_cost > 0
    if requires_confirmation:
        warnings.append(USER_CONFIRMATION_WARNING)
    else:
        warnings.append(NO_EXTERNAL_API_WARNING)

    within_budget = None
    if budget is not None:
        within_budget = estimated_cost <= budget
        if not within_budget:
            warnings.append("Estimated cost exceeds configured budget.")

    return {
        "provider": provider_name,
        "model": str(entry.get("model") or model_name),
        "label": str(entry.get("label") or ""),
        "pricing_is_estimate": True,
        "estimated_cost_per_second_usd": per_second,
        "duration_seconds": duration,
        "clip_count": clips,
        "retry_count": retries,
        "estimated_billable_seconds": billable_seconds,
        "estimated_cost_usd": estimated_cost,
        "cost_level": video_provider_cost_level(estimated_cost),
        "requires_user_confirmation": requires_confirmation,
        "external_api_call_planned": False,
        "budget_usd": budget,
        "within_budget": within_budget,
        "warnings": warnings + list(entry.get("notes") or []),
    }


def estimate_cost_from_video_packet(
    packet: dict[str, Any],
    provider: str = "manual_export",
    model: str = "",
    retry_count: int = 1,
    budget_usd: float | None = None,
) -> dict[str, Any]:
    video = packet.get("video") if isinstance(packet, dict) and isinstance(packet.get("video"), dict) else {}
    duration = _positive_int(video.get("recommended_duration_seconds"), 20)
    return estimate_video_generation_cost(
        provider=provider,
        model=model,
        duration_seconds=duration,
        clip_count=1,
        retry_count=retry_count,
        budget_usd=budget_usd,
    )
