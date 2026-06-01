"""Dependency-free provider adapter scaffold for video generation handoff."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_VIDEO_PROVIDERS: dict[str, dict[str, Any]] = {
    "manual_export": {
        "label": "Manual export",
        "export_key": "generic_video_prompt",
        "handoff_type": "manual_export",
        "external_api_ready": False,
        "supports_async_polling": False,
        "requires_api_key": False,
        "env_key_name": "",
        "create_mode": "manual_export",
        "status_lifecycle": ["ready_for_manual_export", "manual_export_completed", "external_result_ready", "failed"],
        "polling_strategy": "none",
        "description": "Copy the generic prompt or any export format into your chosen video tool.",
        "prompt_title": "Manual video export prompt",
        "recommended_use": "Copy any export prompt into your preferred video workflow.",
        "copy_instructions": "Use the selected prompt as a manual handoff brief; record the external result URL when ready.",
        "provider_limitations": ["No external video API is called.", "Manual export remains the source of truth."],
        "warnings": ["No external API call is needed for manual export."],
        "next_steps": ["Copy the selected prompt into the user's chosen video tool.", "Record the external result URL when available."],
    },
    "generic": {
        "label": "Generic video prompt",
        "export_key": "generic_video_prompt",
        "handoff_type": "prompt_export",
        "external_api_ready": False,
        "supports_async_polling": False,
        "requires_api_key": False,
        "env_key_name": "",
        "create_mode": "prompt_export",
        "status_lifecycle": ["ready_for_manual_export", "manual_export_completed", "external_result_ready", "failed"],
        "polling_strategy": "none",
        "description": "General-purpose prompt for video generation tools.",
        "prompt_title": "Generic video prompt",
        "recommended_use": "Paste into a general video generation or creative production workflow.",
        "copy_instructions": "Use this universal prompt when no provider-specific format is required.",
        "provider_limitations": ["Generic prompt export is manual; no external video API is called."],
        "warnings": ["Generic prompt export is manual; no external video API is called."],
        "next_steps": ["Use the generic prompt in a compatible external video tool.", "Record result metadata manually."],
    },
    "capcut": {
        "label": "CapCut shot list",
        "export_key": "capcut_shot_list",
        "handoff_type": "shot_list_export",
        "external_api_ready": False,
        "supports_async_polling": False,
        "requires_api_key": False,
        "env_key_name": "",
        "create_mode": "shot_list_export",
        "status_lifecycle": ["ready_for_manual_export", "manual_export_completed", "external_result_ready", "failed"],
        "polling_strategy": "none",
        "description": "Numbered shot list for manual editing in CapCut or similar editors.",
        "prompt_title": "CapCut shot list",
        "recommended_use": "Use as an editing shot list.",
        "copy_instructions": "Paste the numbered scenes into an editor brief and follow the shot directions.",
        "provider_limitations": ["CapCut shot-list export is manual; no external editor API is called."],
        "warnings": ["CapCut shot-list export is manual; no external editor API is called."],
        "next_steps": ["Paste the shot list into an editor or production brief.", "Record final video links manually."],
    },
    "runway": {
        "label": "Runway-style prompt",
        "export_key": "runway_style_prompt",
        "handoff_type": "prompt_export",
        "external_api_ready": False,
        "supports_async_polling": True,
        "requires_api_key": True,
        "env_key_name": "RUNWAY_API_KEY",
        "create_mode": "planned_external_api",
        "status_lifecycle": ["ready_for_manual_export", "queued", "processing", "external_result_ready", "failed"],
        "polling_strategy": "planned async polling by provider_job_id; disabled until provider contract is finalized",
        "description": "Visual prompt shaped for Runway-style video generation.",
        "prompt_title": "Runway-style visual prompt",
        "recommended_use": "Paste into a visual video generation tool as a product-focused prompt.",
        "copy_instructions": "Copy this prompt manually; Runway API calls are not enabled in this scaffold.",
        "provider_limitations": ["Runway API integration is planned but disabled.", "API key/config contract must be finalized before enabling."],
        "warnings": ["Runway API integration is planned but disabled until keys, contracts, timeouts, and provider docs are finalized."],
        "next_steps": ["Define tests-first provider contract.", "Add secret handling for RUNWAY_API_KEY.", "Keep manual export as fallback."],
    },
    "pika": {
        "label": "Pika-style prompt",
        "export_key": "pika_style_prompt",
        "handoff_type": "prompt_export",
        "external_api_ready": False,
        "supports_async_polling": True,
        "requires_api_key": True,
        "env_key_name": "PIKA_API_KEY",
        "create_mode": "planned_external_api",
        "status_lifecycle": ["ready_for_manual_export", "queued", "processing", "external_result_ready", "failed"],
        "polling_strategy": "planned async polling by provider_job_id; disabled until provider contract is finalized",
        "description": "Short motion prompt shaped for Pika-style generation.",
        "prompt_title": "Pika-style motion prompt",
        "recommended_use": "Paste into a short motion video tool as a compact product demo prompt.",
        "copy_instructions": "Copy this prompt manually; Pika API calls are not enabled in this scaffold.",
        "provider_limitations": ["Pika API integration is planned but disabled.", "API key/config contract must be finalized before enabling."],
        "warnings": ["Pika API integration is planned but disabled until keys, contracts, timeouts, and provider docs are finalized."],
        "next_steps": ["Define tests-first provider contract.", "Add secret handling for PIKA_API_KEY.", "Keep manual export as fallback."],
    },
}

VIDEO_PROVIDER_ALIASES = {
    "manual": "manual_export",
    "manual_export": "manual_export",
    "generic": "generic",
    "generic_video_prompt": "generic",
    "capcut": "capcut",
    "capcut_shot_list": "capcut",
    "runway": "runway",
    "runway_style_prompt": "runway",
    "pika": "pika",
    "pika_style_prompt": "pika",
}

EXPORT_FORMAT_KEYS = (
    "generic_video_prompt",
    "capcut_shot_list",
    "runway_style_prompt",
    "pika_style_prompt",
)


def _provider_key(provider: str) -> str:
    return str(provider or "manual_export").strip().lower().replace(" ", "_")


def _compact_text(value: Any, limit: int = 180) -> str:
    return " ".join(str(value or "").split())[:limit]


def normalize_video_provider(provider: str) -> str:
    return VIDEO_PROVIDER_ALIASES.get(_provider_key(provider), "")


def get_video_provider_config(provider: str) -> dict[str, Any]:
    provider_name = normalize_video_provider(provider)
    if not provider_name:
        return {}
    config = deepcopy(SUPPORTED_VIDEO_PROVIDERS[provider_name])
    config["provider"] = provider_name
    return config


def supported_video_provider_names() -> list[str]:
    return list(SUPPORTED_VIDEO_PROVIDERS.keys())


def video_provider_catalog() -> list[dict[str, Any]]:
    return [
        {
            "provider": provider,
            "label": config["label"],
            "export_key": config["export_key"],
            "handoff_type": config["handoff_type"],
            "external_api_ready": config["external_api_ready"],
            "supports_async_polling": config["supports_async_polling"],
            "requires_api_key": config["requires_api_key"],
            "env_key_name": config["env_key_name"],
            "create_mode": config["create_mode"],
            "status_lifecycle": list(config["status_lifecycle"]),
            "description": config["description"],
            "recommended_use": config["recommended_use"],
        }
        for provider, config in SUPPORTED_VIDEO_PROVIDERS.items()
    ]


def video_provider_plan(provider: str) -> dict[str, Any]:
    config = get_video_provider_config(provider)
    if not config:
        return {}
    return {
        "provider": config["provider"],
        "label": config["label"],
        "export_key": config["export_key"],
        "selected_export_key": config["export_key"],
        "external_api_ready": config["external_api_ready"],
        "requires_api_key": config["requires_api_key"],
        "env_key_name": config["env_key_name"],
        "create_mode": config["create_mode"],
        "supported_statuses": list(config["status_lifecycle"]),
        "supports_async_polling": config["supports_async_polling"],
        "polling_strategy": config["polling_strategy"],
        "recommended_use": config["recommended_use"],
        "copy_instructions": config["copy_instructions"],
        "provider_limitations": list(config["provider_limitations"]),
        "next_steps": list(config["next_steps"]),
        "warnings": list(config["warnings"]),
    }


def video_job_export_formats(packet: dict[str, Any]) -> dict[str, str]:
    formats = packet.get("export_formats") if isinstance(packet, dict) else {}
    if not isinstance(formats, dict):
        formats = {}
    return {
        "generic_video_prompt": str(formats.get("generic_video_prompt") or packet.get("full_video_prompt") or ""),
        "capcut_shot_list": str(formats.get("capcut_shot_list") or ""),
        "runway_style_prompt": str(formats.get("runway_style_prompt") or ""),
        "pika_style_prompt": str(formats.get("pika_style_prompt") or ""),
    }


def video_provider_payload_metadata(provider: str, export_formats: dict[str, str], packet: dict[str, Any]) -> dict[str, Any]:
    provider_name = normalize_video_provider(provider) or "manual_export"
    config = get_video_provider_config(provider_name)
    scenes = packet.get("scenes") if isinstance(packet, dict) else []
    if not isinstance(scenes, list):
        scenes = []
    video = packet.get("video") if isinstance(packet.get("video"), dict) else {}
    selected_export_key = config["export_key"]
    selected_prompt = export_formats.get(selected_export_key) or export_formats.get("generic_video_prompt", "")
    evidence_boundary = packet.get("evidence_boundary") or (
        "Use only supplied product and review evidence. Avoid unsupported claims or provider-specific assumptions."
    )
    return {
        "provider": provider_name,
        "provider_label": config["label"],
        "handoff_type": config["handoff_type"],
        "external_api_ready": config["external_api_ready"],
        "supports_async_polling": config["supports_async_polling"],
        "requires_api_key": config["requires_api_key"],
        "env_key_name": config["env_key_name"],
        "create_mode": config["create_mode"],
        "status_lifecycle": list(config["status_lifecycle"]),
        "selected_export_key": selected_export_key,
        "prompt": selected_prompt,
        "prompt_title": config["prompt_title"],
        "prompt_summary": _compact_text(selected_prompt, limit=180),
        "recommended_use": config["recommended_use"],
        "copy_instructions": config["copy_instructions"],
        "provider_limitations": list(config["provider_limitations"]),
        "evidence_boundary": evidence_boundary,
        "scene_count": len(scenes[:4]),
        "recommended_duration_seconds": video.get("recommended_duration_seconds") or 20,
        "aspect_ratio": video.get("aspect_ratio") or "9:16",
        "export_formats": export_formats,
        "scenes": scenes[:4],
        "instructions": [
            "Copy the selected prompt into the chosen video tool.",
            "Use the scene list as a shot-by-shot guide.",
            "This scaffold does not call an external video API yet.",
        ],
        "next_action": "manual_copy_to_video_tool",
    }

