import re
import json
import os
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import uvicorn
from uuid import uuid4

from core.logging_utils import emit_event
from core.telemetry_utils import summarize_telemetry
from core.workflow import copilot_engine, memory_engine
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from schemas.api_contract import (
    AgentRunCreateResponse,
    AgentRunEventsResponse,
    AgentRunListResponse,
    AgentRunStatusResponse,
    AmazonIntakeRequest,
    AmazonIntakeResponse,
    DebugCopilotResponse,
    GenerateCopilotResponse,
    GrowthRequest,
    PastedReviewsRequest,
    PastedReviewsResponse,
    ProductDescriptionRequest,
    ProductDescriptionResponse,
    TranslationRequest,
    TranslationResponse,
    VideoGenerationJobRequest,
    VideoGenerationFromGenerationRequest,
    VideoGenerationJobResponse,
    VideoGenerationJobStatusResponse,
    VideoGenerationJobListResponse,
    VideoGenerationProvidersResponse,
    VideoGenerationProviderPlanResponse,
    VideoGenerationCostCatalogResponse,
    VideoGenerationCostEstimateRequest,
    VideoGenerationCostEstimateResponse,
    VideoGenerationJobResultRequest,
    VideoGenerationExperimentRequest,
    VideoGenerationProviderSubmitRequest,
    VideoGenerationProviderPollRequest,
    VideoGenerationStorageStatusResponse,
)
from agent_runs import (
    InMemoryAgentRunStore,
    apply_evidence_safe_storyboard_rework,
    build_agent_run,
    build_controlled_provider_handoff_checklist,
    build_demo_ready_run_summary,
    build_experiment_comparison_decision_gate,
    build_experiment_feedback_decision,
    build_lightweight_artifact_lineage,
    build_second_experiment_comparison,
    detect_storyboard_rework_need,
    trigger_experiment_rework_run,
)
from schemas.source_probe_contract import (
    SourceProbeRequest,
    SourceProbeResponse,
    SourceProbeResult,
    SourceProbeTelemetry,
)
from source_adapters import SourceAdapterRegistry
from source_adapters.amazon_url_utils import normalize_amazon_product_url
from video_generation.providers import (
    normalize_video_provider,
    supported_video_provider_names,
    video_job_export_formats,
    video_provider_catalog,
    video_provider_payload_metadata,
    video_provider_plan,
)
from video_generation.provider_costs import (
    estimate_cost_from_video_packet,
    estimate_video_generation_cost,
    video_provider_cost_catalog,
)
from video_generation.job_store import get_video_job_store, video_job_storage_diagnostics
from video_generation.job_status import (
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_PROCESSING,
    VIDEO_JOB_STATUS_QUEUED,
    VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    build_video_job_history_event,
    can_transition_video_job_status,
    normalize_video_job_status,
)
from video_generation.provider_runtime import (
    build_provider_poll_runtime,
    build_provider_runtime,
    next_simulated_provider_status,
    provider_poll_history_event,
    provider_submit_history_events,
    supports_provider_polling,
)
from video_generation.provider_integration import provider_plan_integration_metadata

app = FastAPI()
source_probe_registry = SourceAdapterRegistry()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def get_server_port() -> int:
    return int(os.getenv("PORT", "8001"))


def _safe_product_category_hint(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if "://" in value or "/" in value or len(value) > 80:
        return "external_url"
    return value


def _error_type(exc: Exception) -> str:
    name = type(exc).__name__
    text = f"{name}: {exc}".lower()
    if "huggingface" in text or "hf hub" in text or "sentence-transformers" in text:
        return "runtime_model_unavailable"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "memory" in text or "out of memory" in text:
        return "memory_failure"
    return name
INDEX_HTML = STATIC_DIR / "index.html"
SOURCE_PROBE_PROVIDERS = {
    "amazon_review_api",
    "tiktok_trend_api",
    "reddit_review_api",
}

TRANSLATION_SYSTEM_PROMPT = (
    "You translate product creative briefs into natural Chinese. "
    "Preserve Markdown structure. Preserve English product slugs, numbers, percentages, "
    "and necessary technical field names. Do not add facts. Do not change strategy meaning. "
    "Do not translate JSON/code keys inside code blocks unless the value is natural language."
)

DESCRIPTION_SYSTEM_PROMPT = (
    "You create concise ecommerce TikTok creative briefs from user-provided product descriptions. "
    "Use only the supplied product description and customer pain points. Do not invent review evidence, "
    "do not claim Amazon or local dataset sources, and return compact JSON only."
)

PASTED_REVIEWS_SYSTEM_PROMPT = (
    "You create concise ecommerce TikTok creative briefs from user-pasted review snippets. "
    "Use only the supplied product context and pasted reviews. Do not claim Amazon, local dataset, "
    "or external source access. Return compact JSON only."
)

DESCRIPTION_MIN_CHARS = 12
DESCRIPTION_MAX_CHARS = 6000
PASTED_REVIEWS_MIN_CHARS = 24
PASTED_REVIEWS_COMPACT_QUOTE_LIMIT = 12
PASTED_REVIEWS_RAW_MAX_CHARS = 50000
SUPPORTED_OUTPUT_LANGUAGES = {"en", "zh-CN"}
VIDEO_JOB_STORE = get_video_job_store()
AGENT_RUN_STORE = InMemoryAgentRunStore()
VIDEO_GENERATION_RESULT_STATUSES = {
    VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY,
    VIDEO_JOB_STATUS_FAILED,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
async def index():
    return FileResponse(INDEX_HTML)


def _probe_status_from_evidence(evidence) -> str:
    warnings = list(getattr(evidence, "data_warnings", []) or [])
    if any(
        warning.endswith("_disabled") or warning.endswith("_not_enabled")
        for warning in warnings
    ):
        return "disabled"
    if getattr(evidence, "source_type", "") == "unavailable":
        return "unavailable"
    return "success"


def _amazon_shadow_sources(url: str, product_category: str) -> dict:
    started = time.perf_counter()
    try:
        evidence = source_probe_registry.fetch(
            "amazon_review_api",
            url or "",
            product_category or "",
        )
        metadata = dict(evidence.metadata or {})
        return {
            "mode": "amazon_shadow",
            "amazon_review_api": {
                "status": _probe_status_from_evidence(evidence),
                "source_confidence": evidence.confidence,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "evidence_preview": evidence.evidence_quotes[:3],
                "metadata": {
                    **metadata,
                    "source_type": evidence.source_type,
                    "data_warnings": list(evidence.data_warnings),
                },
                "error": metadata.get("error", ""),
            },
            "memory_write_allowed": False,
            "used_for_generation": False,
        }
    except Exception as exc:
        return {
            "mode": "amazon_shadow",
            "amazon_review_api": {
                "status": "error",
                "source_confidence": 0.0,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "evidence_preview": [],
                "metadata": {},
                "error": str(exc),
            },
            "memory_write_allowed": False,
            "used_for_generation": False,
        }


async def translate_visible_output(text: str, target_language: str = "zh-CN") -> str:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0.2,
        max_retries=0,
    )
    message = await llm.ainvoke(
        [
            SystemMessage(content=TRANSLATION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Target language: {target_language}\n\n"
                    "Translate only the visible product output below:\n\n"
                    f"{text}"
                )
            ),
        ]
    )
    return str(message.content or "").strip()


def _normalize_output_language(value: str | None) -> str:
    normalized = (value or "en").strip()
    return normalized or "en"


def _output_language_error(request_id: str):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error": "Unsupported output_language. Use en or zh-CN.",
            "error_type": "unsupported_output_language",
            "request_id": request_id,
        },
    )


def _validate_output_language(value: str | None, request_id: str):
    output_language = _normalize_output_language(value)
    if output_language not in SUPPORTED_OUTPUT_LANGUAGES:
        return None, _output_language_error(request_id)
    return output_language, None


def _json_from_translation(raw: str) -> dict:
    cleaned = (raw or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Translated product payload must be a JSON object.")
    return parsed


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _looks_like_utf8_mojibake(text: str) -> bool:
    markers = ("æ", "ä¸", "å®", "ï¼", "ç")
    return any(marker in text for marker in markers)


def _repair_mojibake_text(text: str) -> str:
    if not text or not _looks_like_utf8_mojibake(text):
        return text
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    if _contains_cjk(repaired):
        return repaired
    return text


def _repair_mojibake_payload(value):
    if isinstance(value, str):
        return _repair_mojibake_text(value)
    if isinstance(value, list):
        return [_repair_mojibake_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _repair_mojibake_payload(item) for key, item in value.items()}
    return value


def _preserve_product_identifiers(translated: dict, original: dict) -> dict:
    if not isinstance(translated, dict) or not isinstance(original, dict):
        return translated

    for key, value in original.items():
        if key in {
            "source",
            "source_type",
            "source_url",
            "data_warnings",
            "product_name",
            "product_category",
            "risk_level",
            "agent_name",
            "packet_version",
            "execution_mode",
            "status",
        }:
            translated[key] = value
        elif isinstance(value, dict) and isinstance(translated.get(key), dict):
            translated[key] = _preserve_product_identifiers(translated[key], value)
        elif isinstance(value, list) and isinstance(translated.get(key), list):
            translated[key] = [
                _preserve_product_identifiers(item, value[index])
                if index < len(value) and isinstance(item, dict) and isinstance(value[index], dict)
                else item
                for index, item in enumerate(translated[key])
            ]
    return translated


async def translate_product_visible_data(data: dict, target_language: str) -> dict:
    if target_language != "zh-CN":
        return data

    raw = await translate_visible_output(
        (
            "Translate only user-visible natural-language string values in this JSON object. "
            "Return valid JSON only. Preserve all object keys exactly. Do not translate source identifiers, "
            "enum-like values, booleans, numbers, request IDs, or URLs.\n\n"
            f"{json.dumps(data, ensure_ascii=False)}"
        ),
        target_language,
    )
    translated = _json_from_translation(raw)
    translated = _repair_mojibake_payload(translated)
    return _preserve_product_identifiers(translated, data)


def _clean_description_text(value: str) -> str:
    return (value or "").strip()


def _strip_amazon_reviewer_prefix(text: str) -> str:
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return ""

    title_starters = (
        "worth", "cannot", "can't", "value", "quality", "great", "good", "love",
        "best", "this", "these", "the", "it", "not", "however", "yes",
        "excellent", "delicious", "tastes", "taste", "no", "price", "flavor",
        "flavour", "bottle", "arrived",
    )
    first_token = re.match(r"^(?:By\s+)?([A-Za-z][A-Za-z0-9_-]{1,24})\b", cleaned, flags=re.IGNORECASE)
    if first_token and first_token.group(1).lower() in title_starters:
        return cleaned

    starter_pattern = "|".join(re.escape(item) for item in title_starters)
    name_pattern = r"(?:Amazon Customer|[A-Za-z][A-Za-z0-9_-]{1,24})"

    cleaned = re.sub(
        rf"^(?:By\s+)?{name_pattern}\s*[:\-]\s+(?=(?:{starter_pattern})\b)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        rf"^(?:By\s+)?{name_pattern}\s+(?=(?:{starter_pattern})\b)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _description_error(error: str, error_type: str, request_id: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error": error,
            "error_type": error_type,
            "request_id": request_id,
        },
    )


def _validate_description_request(request: ProductDescriptionRequest, request_id: str):
    product_name = _clean_description_text(request.product_name)
    product_description = _clean_description_text(request.product_description)
    customer_pain_points = _clean_description_text(request.customer_pain_points)
    combined_size = len(product_name) + len(product_description) + len(customer_pain_points)

    if not product_name:
        return _description_error("product_name is required.", "missing_product_name", request_id)
    if not product_description:
        return _description_error(
            "product_description is required.",
            "missing_product_description",
            request_id,
        )
    if not customer_pain_points:
        return _description_error(
            "customer_pain_points is required.",
            "missing_customer_pain_points",
            request_id,
        )
    if len(product_name) < 2 or len(product_description) < DESCRIPTION_MIN_CHARS or len(customer_pain_points) < DESCRIPTION_MIN_CHARS:
        return _description_error(
            "Product description mode needs a product name plus a short product description and customer pain point summary.",
            "input_too_short",
            request_id,
        )
    if combined_size > DESCRIPTION_MAX_CHARS:
        return _description_error(
            "Input is too long for Product Description Mode. Please shorten the description and pain points.",
            "input_too_long",
            request_id,
        )
    return None


def _is_pasted_review_label_line(line: str) -> bool:
    normalized = " ".join(str(line or "").strip().split()).lower()
    label_prefixes = (
        "\u75db\u70b9:",
        "\u75db\u70b9\uff1a",
        "\u6b63\u5411:",
        "\u6b63\u5411\uff1a",
        "\u4f7f\u7528\u573a\u666f:",
        "\u4f7f\u7528\u573a\u666f\uff1a",
        "pain point:",
        "pain points:",
        "positive:",
        "pros:",
        "use case:",
        "use cases:",
        "usage scenario:",
        "usage scenarios:",
    )
    return normalized.startswith(label_prefixes)


def _clean_pasted_review_quote_text(value: str) -> str:
    text = _clean_description_text(value)
    if not text:
        return ""

    cleaner = globals().get("_rw_clean_evidence_fragment")
    if callable(cleaner):
        text = cleaner(text)

    text = re.sub(r"^(?:Amazon Customer|Kindle Customer)\s*[1-5](?:\.0)?\s+out of\s+5\s+stars\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:Amazon Customer|Kindle Customer)(?=[A-Z])", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^\[?\s*[1-5](?:\.0)?\s+out of\s+5\s+stars\s*\]?\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[1-5](?:\.0)?\s+out of\s+5\s+stars\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:Amazon Customer|Kindle Customer)\s*[1-5](?:\.0)?\s+out of 5 stars\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Reviewed in .*? on [A-Za-z]+ \d{1,2}, \d{4}", " ", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(?:Flavor Name|Size|Color|Style|Pattern Name|Package Quantity)\s*:\s*"
        r".*?(?=\b(?:Flavor Name|Size|Color|Style|Pattern Name|Package Quantity|Verified Purchase|Reviewed in|[1-5](?:\.0)?\s+out of\s+5\s+stars)\b|$)",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5[^\s]{0,18}\u8bc4\u8bba", " ", text)
    text = re.sub(r"\bVerified Purchase\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\u5df2\u9a8c\u8bc1\u8d2d\u4e70|\u5df2\u786e\u8ba4\u8d2d\u4e70", " ", text)
    text = re.sub(r"\b(?:One|Two|\d+)\s+people?\s+found\s+this\s+helpful\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:Helpful|Report|Submit a review|Community guidelines?)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -:;,.[]")
    text = _strip_amazon_reviewer_prefix(text)
    if not re.search(r"[A-Za-z\u4e00-\u9fff]", text):
        return ""
    return text


def _split_pasted_review_quotes(text: str, limit: int = 10) -> list[str]:
    cleaned_lines = []
    for raw_line in (text or "").replace("\r", "\n").split("\n"):
        line = raw_line.strip().lstrip("-*•0123456789. )(").strip()
        line = _clean_pasted_review_quote_text(line)
        if line and not _is_pasted_review_label_line(line):
            cleaned_lines.append(line)

    if not cleaned_lines:
        normalized = " ".join((text or "").split())
        pieces = [piece.strip() for piece in normalized.replace("!", ".").replace("?", ".").split(".")]
        cleaned_lines = [
            cleaned
            for piece in pieces
            for cleaned in [_clean_pasted_review_quote_text(piece)]
            if cleaned and not _is_pasted_review_label_line(cleaned)
        ]

    quotes = []
    for line in cleaned_lines:
        quote = _safe_evidence_quote(line, limit=240)
        if quote and quote not in quotes:
            quotes.append(quote)
        if len(quotes) >= limit:
            break
    return quotes


def _compact_pasted_reviews_for_generation(text: str, limit: int = PASTED_REVIEWS_COMPACT_QUOTE_LIMIT) -> str:
    quotes = _split_pasted_review_quotes(text, limit=limit)
    return "\n".join(quotes)


def _validate_pasted_reviews_request(request: PastedReviewsRequest, request_id: str):
    product_name = _clean_description_text(request.product_name)
    pasted_reviews = _clean_description_text(request.pasted_reviews)

    if not product_name:
        return _description_error("product_name is required.", "missing_product_name", request_id)
    if not pasted_reviews:
        return _description_error("pasted_reviews is required.", "missing_pasted_reviews", request_id)
    if len(pasted_reviews) < PASTED_REVIEWS_MIN_CHARS:
        return _description_error(
            "Pasted Reviews Mode needs a few concrete review snippets or customer complaints.",
            "pasted_reviews_too_short",
            request_id,
        )
    compact_reviews = _compact_pasted_reviews_for_generation(pasted_reviews)
    if not compact_reviews:
        return _description_error(
            "Pasted Reviews Mode needs at least one concrete review line, not only category labels.",
            "pasted_reviews_no_concrete_reviews",
            request_id,
        )
    if len(pasted_reviews) > PASTED_REVIEWS_RAW_MAX_CHARS:
        return _description_error(
            "Input is too long for Pasted Reviews Mode. Please paste a smaller visible review sample.",
            "input_too_long",
            request_id,
        )
    effective_reviews = compact_reviews or pasted_reviews
    if len(product_name) + len(_clean_description_text(request.product_description or "")) + len(effective_reviews) > DESCRIPTION_MAX_CHARS:
        return _description_error(
            "Input is too long for Pasted Reviews Mode. Please shorten the pasted reviews.",
            "input_too_long",
            request_id,
        )
    return None


def _safe_evidence_quote(text: str, limit: int = 220) -> str:
    cleaned = " ".join(_clean_description_text(text).split())
    return cleaned[:limit]


def _video_packet_text(value, limit: int = 260) -> str:
    return _safe_evidence_quote(str(value or ""), limit=limit)


def _video_overlay_text(scene: dict, script: dict) -> str:
    source = (
        scene.get("on_screen_text")
        or scene.get("overlay_text")
        or scene.get("narration")
        or script.get("hook")
        or script.get("cta")
        or ""
    )
    text = _video_packet_text(source, limit=90)
    for separator in [". ", "! ", "? ", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
            break
    return text[:72].strip()


def _build_video_generation_packet(
    product_name: str,
    category: str,
    assets: dict,
    insights: dict,
    evaluation: dict,
    output_language: str = "en",
) -> dict:
    assets = assets if isinstance(assets, dict) else {}
    insights = insights if isinstance(insights, dict) else {}
    evaluation = evaluation if isinstance(evaluation, dict) else {}
    script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
    evidence = insights.get("evidence") if isinstance(insights.get("evidence"), dict) else {}
    source_type = evidence.get("source_type") or storyboard.get("source") or ""
    risk_level = evaluation.get("risk_level") or ""
    raw_scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    normalized_scenes = []

    for index, scene in enumerate(raw_scenes[:4]):
        if not isinstance(scene, dict):
            continue
        visual_prompt = _video_packet_text(
            scene.get("visual_description") or scene.get("visual") or scene.get("scene_goal") or "",
            limit=320,
        )
        narration = _video_packet_text(scene.get("narration") or "", limit=260)
        evidence_quote = _video_packet_text(
            scene.get("evidence_quote_used") or scene.get("evidence_quote") or scene.get("linked_painpoint") or "",
            limit=240,
        )
        risk_notes = []
        if not evidence_quote:
            risk_notes.append("Missing scene-level evidence quote; keep claim conservative.")
        if not visual_prompt or len(visual_prompt) < 24:
            risk_notes.append("Visual prompt is generic; expand with product-specific visible action before video rendering.")
        normalized_scenes.append(
            {
                "scene_id": scene.get("scene_id") or index + 1,
                "duration_seconds": 5,
                "visual_prompt": visual_prompt or f"Show {product_name} in a simple product-use moment.",
                "narration": narration,
                "overlay_text": _video_overlay_text(scene, script),
                "evidence_quote": evidence_quote,
                "risk_notes": risk_notes,
            }
        )

    if not normalized_scenes:
        normalized_scenes.append(
            {
                "scene_id": 1,
                "duration_seconds": 5,
                "visual_prompt": f"Show {product_name} in a vertical product demo.",
                "narration": _video_packet_text(script.get("hook") or script.get("cta") or "", limit=260),
                "overlay_text": _video_packet_text(script.get("hook") or product_name, limit=72),
                "evidence_quote": "",
                "risk_notes": ["No storyboard scenes were available; treat this as a draft placeholder."],
            }
        )

    duration_seconds = 20
    aspect_ratio = "9:16"
    product_descriptor = f"{product_name} ({category or 'product'})"
    cta = _video_packet_text(script.get("cta") or "", limit=180)
    risk_boundary = (
        "Evidence boundary: use only the supplied review/product evidence; avoid unsupported claims, "
        "before/after guarantees, medical claims, or full-market statistics. "
        "If a scene is missing an evidence quote, show product use visually but avoid unsupported factual claims."
    )
    scene_lines = [
        (
            f"Scene {scene['scene_id']} ({scene['duration_seconds']}s) - "
            f"Shot direction: {scene['visual_prompt']} "
            f"Narration: {scene['narration'] or 'No narration supplied.'} "
            f"Overlay text: {scene['overlay_text'] or 'None.'} "
            f"Evidence anchor: {scene['evidence_quote'] or 'Missing; keep claim conservative.'}"
        )
        for scene in normalized_scenes
    ]
    compact_scene_sequence = " | ".join(
        f"Scene {scene['scene_id']}: {scene['visual_prompt']} (overlay: {scene['overlay_text'] or 'none'})"
        for scene in normalized_scenes
    )
    generic_video_prompt = (
        f"Universal video prompt for {product_descriptor}.\n"
        f"Format: {duration_seconds}-second vertical {aspect_ratio} TikTok-style product video.\n"
        f"{risk_boundary}\n"
        "Scene sequence:\n"
        + "\n".join(scene_lines)
        + (f"\nCTA: {cta}" if cta else "\nCTA: Keep the ending grounded and non-exaggerated.")
    )
    capcut_shot_list = "\n".join(
        (
            f"Scene {scene['scene_id']} - {scene['duration_seconds']}s\n"
            f"Shot direction: {scene['visual_prompt']}\n"
            f"Overlay text: {scene['overlay_text'] or 'None'}\n"
            f"Narration: {scene['narration'] or 'No narration supplied'}\n"
            f"Evidence anchor: {scene['evidence_quote'] or 'Missing; keep claim conservative'}\n"
            "Edit notes: use a quick cut, close-up, product handling, and a clean transition to the next scene."
        )
        for scene in normalized_scenes
    )
    runway_style_prompt = (
        f"Cinematic vertical {aspect_ratio} product ad for {product_descriptor}. "
        "Use clean ecommerce lighting, close-up product handling, shallow depth of field, "
        "gentle push-in camera movement, and natural short-form pacing. "
        f"{risk_boundary} "
        f"Visual sequence: {compact_scene_sequence}. "
        "Keep text overlays minimal and preserve the supplied evidence boundary."
    )
    pika_style_prompt = (
        f"Short motion product demo for {product_name}: quick cuts, product-in-use action, "
        "simple overlays, compact narration, and evidence-safe narration. Sequence: "
        + " -> ".join(
            f"{scene['visual_prompt']} [overlay: {scene['overlay_text'] or 'none'}]"
            for scene in normalized_scenes
        )
        + ". Avoid unsupported claims."
    )

    return {
        "packet_version": "video_generation_v1",
        "intended_use": "video_prompt_export",
        "source": {
            "storyboard_source": storyboard.get("source") or source_type,
            "evidence_source_type": source_type,
            "risk_level": risk_level,
            "output_language": output_language,
        },
        "video": {
            "platform": "TikTok",
            "recommended_duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "style_notes": [
                "Vertical short-form product demo.",
                "Keep claims tied to supplied evidence quotes.",
                "Use natural product-use visuals before adding stylized effects.",
            ],
        },
        "scenes": normalized_scenes,
        "evidence_boundary": risk_boundary,
        "full_video_prompt": generic_video_prompt,
        "export_formats": {
            "generic_video_prompt": generic_video_prompt,
            "capcut_shot_list": capcut_shot_list,
            "runway_style_prompt": runway_style_prompt,
            "pika_style_prompt": pika_style_prompt,
        },
    }


def _handoff_text(value, limit: int = 700) -> str:
    return _safe_evidence_quote(str(value or ""), limit=limit)


def _build_product_asset_lock(product_title: str, product_category: str) -> dict:
    product_identity = _handoff_text(product_title or "Product", limit=160)
    category = _handoff_text(product_category or "product", limit=120)
    return {
        "lock_version": "product_asset_lock_v1",
        "product_identity": product_identity,
        "product_category": category,
        "visual_identity_source": "Use the supplied product name/category and a manually uploaded reference product image in external tools.",
        "must_preserve": [
            f"Keep product identity as {product_identity}.",
            f"Keep product category as {category}; do not drift into another category.",
            "Preserve visible color, material, label placement, package shape, and scale from the uploaded/reference product image.",
            "Keep review-backed benefit and concern boundaries tied to supplied evidence.",
        ],
        "must_not_change": [
            "Do not invent fake variants, colors, package sizes, logos, or competitor products.",
            "Do not transform the product into a different category or unrealistic object.",
            "Do not add unsupported medical, safety, before/after, or full-market performance claims.",
            "Do not imply verified certifications, endorsements, or guarantees unless supplied in evidence.",
        ],
        "allowed_contexts": [
            "Clean ecommerce product demo surface.",
            "Simple product-in-use moment relevant to the supplied category.",
            "Close-up handling, setup, or comparison visual that does not invent unsupported claims.",
            "Neutral lifestyle background where the product remains the hero.",
        ],
        "image_reference_rules": [
            "Upload or reference the real product image manually before paid generation.",
            "Use the image as the source of truth for product appearance.",
            "If the generated clip changes product identity, reject it and regenerate from one short clip.",
            "Do not rely on text prompt alone for exact product appearance.",
        ],
        "human_review_required": True,
    }


def _build_keyframe_plan(
    product_title: str,
    product_category: str,
    keyframes: list[dict],
    product_asset_lock: dict,
    aspect_ratio: str,
    quote_preview: list[str],
) -> dict:
    must_preserve = product_asset_lock.get("must_preserve") if isinstance(product_asset_lock.get("must_preserve"), list) else []
    scenes = []
    for index, frame in enumerate((keyframes or [])[:4]):
        if not isinstance(frame, dict):
            continue
        scene_id = frame.get("scene_id") or index + 1
        duration = int(frame.get("duration_seconds") or 5)
        evidence_anchor = _handoff_text(
            frame.get("evidence_anchor") or (quote_preview[index % len(quote_preview)] if quote_preview else ""),
            limit=240,
        )
        scenes.append(
            {
                "scene_id": scene_id,
                "duration_seconds": duration,
                "keyframe_goal": _handoff_text(
                    frame.get("keyframe_goal") or f"Create scene {scene_id} for {product_title}.",
                    limit=260,
                ),
                "product_position": _handoff_text(
                    f"Keep {product_title} clearly visible as the hero product in a vertical {aspect_ratio} frame.",
                    limit=220,
                ),
                "camera_direction": _handoff_text(
                    "Use a stable close-up or gentle push-in; avoid fast camera moves that distort product identity.",
                    limit=220,
                ),
                "motion_control": _handoff_text(
                    frame.get("motion_prompt") or "Use natural product handling and conservative short-form motion.",
                    limit=360,
                ),
                "overlay_text": _handoff_text(frame.get("overlay_text") or "", limit=90),
                "evidence_anchor": evidence_anchor,
                "product_constraints": must_preserve[:4],
                "risk_notes": [
                    "Review this keyframe before paid generation.",
                    "Reject output if product category, shape, color, material, or label identity drifts.",
                    "Do not treat one variant or complaint as a whole-market claim.",
                ],
            }
        )

    if not scenes:
        scenes.append(
            {
                "scene_id": 1,
                "duration_seconds": 5,
                "keyframe_goal": f"Create one conservative product demo opening for {product_title}.",
                "product_position": f"Keep {product_title} centered and clearly visible.",
                "camera_direction": "Static product close-up with clean ecommerce lighting.",
                "motion_control": "Use minimal motion; generate one short clip first.",
                "overlay_text": "",
                "evidence_anchor": quote_preview[0] if quote_preview else "",
                "product_constraints": must_preserve[:4],
                "risk_notes": [
                    "Fallback scene only; review manually before using paid generation.",
                    "Do not invent unsupported claims or product variants.",
                ],
            }
        )

    return {
        "plan_version": "keyframe_plan_v1",
        "recommended_clip_strategy": "Generate one short clip first, review product identity and evidence boundaries, then spend more credits only after approval.",
        "scene_count": len(scenes),
        "scenes": scenes,
        "review_before_paid_generation": True,
        "stability_notes": [
            "Use the product asset lock with every external video prompt.",
            "Keep evidence anchors visible in scene planning; do not invent claims.",
            "Generate one short clip first before spending more credits.",
            f"Preserve {product_category or 'product'} category and product image identity.",
        ],
    }


def _build_external_video_tool_handoff(
    product_name: str,
    category: str,
    data: dict,
) -> dict:
    try:
        data = data if isinstance(data, dict) else {}
        assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
        script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
        storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
        insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
        evidence = insights.get("evidence") if isinstance(insights.get("evidence"), dict) else {}
        llm_packet = data.get("llm_evidence_packet") if isinstance(data.get("llm_evidence_packet"), dict) else {}
        video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else {}
        video = video_packet.get("video") if isinstance(video_packet.get("video"), dict) else {}
        export_formats = video_packet.get("export_formats") if isinstance(video_packet.get("export_formats"), dict) else {}
        scenes = video_packet.get("scenes") if isinstance(video_packet.get("scenes"), list) else []
        storyboard_scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []

        if not scenes and storyboard_scenes:
            for index, scene in enumerate(storyboard_scenes[:4]):
                if not isinstance(scene, dict):
                    continue
                scenes.append(
                    {
                        "scene_id": scene.get("scene_id") or index + 1,
                        "duration_seconds": 5,
                        "visual_prompt": scene.get("visual_description") or scene.get("visual") or scene.get("scene_goal") or "",
                        "narration": scene.get("narration") or "",
                        "overlay_text": scene.get("on_screen_text") or scene.get("overlay_text") or "",
                        "evidence_quote": scene.get("evidence_quote_used") or scene.get("evidence_quote") or scene.get("linked_painpoint") or "",
                    }
                )

        product_title = _handoff_text(product_name or storyboard.get("product_name") or "Product", limit=160)
        product_category = _handoff_text(category or storyboard.get("product_category") or "product", limit=120)
        hook = _handoff_text(script.get("hook") or "", limit=220)
        cta = _handoff_text(script.get("cta") or "", limit=180)
        evidence_quotes = evidence.get("evidence_quotes") if isinstance(evidence.get("evidence_quotes"), list) else []
        packet_evidence = llm_packet.get("evidence") if isinstance(llm_packet.get("evidence"), dict) else {}
        packet_quotes = packet_evidence.get("quotes") if isinstance(packet_evidence.get("quotes"), list) else []
        quote_preview = [_handoff_text(value, limit=220) for value in (evidence_quotes or packet_quotes)[:5] if value]
        duration = int(video.get("recommended_duration_seconds") or 20)
        aspect_ratio = _handoff_text(video.get("aspect_ratio") or "9:16", limit=20)
        source_packet_version = _handoff_text(video_packet.get("packet_version") or "", limit=80)

        keyframes = []
        for index, scene in enumerate(scenes[:4]):
            if not isinstance(scene, dict):
                continue
            visual = _handoff_text(scene.get("visual_prompt") or scene.get("visual_description") or "", limit=360)
            narration = _handoff_text(scene.get("narration") or "", limit=260)
            overlay = _handoff_text(scene.get("overlay_text") or "", limit=90)
            evidence_anchor = _handoff_text(scene.get("evidence_quote") or scene.get("evidence_quote_used") or "", limit=240)
            keyframe_goal = f"Create scene {scene.get('scene_id') or index + 1} for {product_title}: {overlay or narration or visual}"
            keyframes.append(
                {
                    "scene_id": scene.get("scene_id") or index + 1,
                    "duration_seconds": int(scene.get("duration_seconds") or 5),
                    "keyframe_goal": _handoff_text(keyframe_goal, limit=260),
                    "image_prompt": _handoff_text(
                        f"Vertical {aspect_ratio} ecommerce keyframe for {product_title}. {visual} Keep product category as {product_category}.",
                        limit=460,
                    ),
                    "motion_prompt": _handoff_text(
                        f"Animate this keyframe with natural product handling and short-form pacing. Narration: {narration or hook}. Overlay: {overlay or 'minimal text'}.",
                        limit=460,
                    ),
                    "overlay_text": overlay,
                    "evidence_anchor": evidence_anchor,
                }
            )

        if not keyframes:
            keyframes.append(
                {
                    "scene_id": 1,
                    "duration_seconds": 5,
                    "keyframe_goal": f"Create a grounded product demo opening for {product_title}.",
                    "image_prompt": f"Vertical {aspect_ratio} ecommerce keyframe showing {product_title} in a clean product-use moment.",
                    "motion_prompt": f"Animate a short product demo clip for {product_title}; keep claims conservative and evidence-safe.",
                    "overlay_text": hook[:72],
                    "evidence_anchor": quote_preview[0] if quote_preview else "",
                }
            )

        evidence_summary = "; ".join(quote_preview[:3]) or "Use only the supplied review/product evidence."
        general_prompt = _handoff_text(export_formats.get("generic_video_prompt") or video_packet.get("full_video_prompt") or "", limit=1400)
        product_asset_lock = _build_product_asset_lock(product_title, product_category)
        keyframe_plan = _build_keyframe_plan(product_title, product_category, keyframes, product_asset_lock, aspect_ratio, quote_preview)
        lock_summary = (
            f"Product asset lock: preserve {product_asset_lock['product_identity']} as a "
            f"{product_asset_lock['product_category']}; use a manually uploaded/reference product image as identity source."
        )
        keyframe_summary = (
            f"Keyframe plan: {keyframe_plan['scene_count']} scenes. "
            f"{keyframe_plan['recommended_clip_strategy']}"
        )
        gemini_prompt = (
            f"Create a {duration}-second vertical {aspect_ratio} ecommerce video for {product_title} ({product_category}). "
            f"{lock_summary} "
            f"{keyframe_summary} "
            f"Hook: {hook or 'Open with the strongest grounded buyer signal.'} "
            f"CTA: {cta or 'End with a conservative product CTA.'} "
            f"Use these evidence anchors only: {evidence_summary}. "
            "Review before paid generation, keep product appearance consistent, and avoid unsupported claims."
        )
        doubao_prompt = (
            f"Generate a vertical {aspect_ratio} short product video draft for {product_title}. "
            f"{lock_summary} "
            f"{keyframe_summary} "
            f"Scene plan: "
            + " | ".join(
                f"Scene {frame['scene_id']}: {frame['motion_prompt']}"
                for frame in keyframes[:4]
            )
            + f" Evidence boundary: {evidence_summary}. Review one short clip first. No full-market claims."
        )
        image_to_video_prompt = (
            f"Use the uploaded/reference product image as the product identity source. Product: {product_title}. "
            f"Apply the product asset lock and keyframe plan. Animate using the keyframe plan, preserve color/material/shape, "
            "generate one short clip first, and avoid visual changes not supported by the product image, description, or evidence."
        )
        short_motion_prompt = (
            f"{product_title}, vertical {aspect_ratio}, quick ecommerce motion, product-in-use, evidence-safe hook, "
            "clean lighting, short-form pacing, no exaggerated claims."
        )
        negative_prompt = (
            "Do not change the product category, color, material, or package shape. "
            "Do not add competitor logos, medical claims, full-market statistics, fake reviews, unrealistic transformations, or unsupported before/after guarantees."
        )
        copy_ready_generation_brief = "\n".join(
            [
                f"Product: {product_title}",
                f"Category: {product_category}",
                f"Format: {duration}s vertical {aspect_ratio}",
                f"Hook: {hook}",
                f"CTA: {cta}",
                f"Evidence anchors: {evidence_summary}",
                f"Product asset lock: {product_asset_lock['product_identity']} / {product_asset_lock['product_category']}",
                f"Must preserve: {'; '.join(product_asset_lock['must_preserve'][:3])}",
                f"Must not change: {'; '.join(product_asset_lock['must_not_change'][:3])}",
                f"Keyframe plan: {keyframe_plan['scene_count']} scenes; {keyframe_plan['recommended_clip_strategy']}",
                "Workflow: paste a tool prompt into Gemini, Doubao, Runway, Pika, Kling, or a manual video workflow. CrossGrowth does not call external video APIs.",
                "Review the first short clip before paid generation and keep all claims inside the supplied evidence boundary.",
                general_prompt,
            ]
        ).strip()

        return {
            "packet_version": "external_video_tool_handoff_v1",
            "source_packet_version": source_packet_version or "video_generation_v1",
            "recommended_workflow": "Use this package by copying prompts into external video tools. No API call is made by CrossGrowth.",
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
            "requires_user_confirmation_before_paid_generation": True,
            "tool_prompts": {
                "gemini_video_prompt": _handoff_text(gemini_prompt, limit=1600),
                "doubao_video_prompt": _handoff_text(doubao_prompt, limit=1600),
                "general_image_to_video_prompt": _handoff_text(image_to_video_prompt, limit=1200),
                "short_motion_prompt": _handoff_text(short_motion_prompt, limit=700),
            },
            "product_asset_lock": product_asset_lock,
            "keyframe_plan": keyframe_plan,
            "keyframe_prompts": keyframes,
            "product_consistency_rules": [
                "Keep the product category unchanged.",
                "Preserve the visible product color/material/shape from the supplied product image or product description.",
                "Do not introduce unsupported claims.",
                "Keep main product, variant, and competitor boundaries visible when evidence is variant-specific.",
            ],
            "negative_prompt": negative_prompt,
            "copy_ready_generation_brief": _handoff_text(copy_ready_generation_brief, limit=3000),
            "manual_steps": [
                "Upload or reference the product image in the external video tool.",
                "Paste the Gemini/Doubao/general prompt.",
                "Generate one short clip first.",
                "Review product consistency before generating more clips.",
                "Paste the result URL back into the Video Job panel.",
            ],
            "quality_checklist": [
                "Product still matches original product.",
                "Claim is supported by review evidence.",
                "Overlay text matches the scene.",
                "No exaggerated market-wide claims.",
                "Clip is usable before spending more credits.",
            ],
            "warnings": [
                "External tool pricing can vary.",
                "CrossGrowth does not call external video APIs in this flow.",
                "Review costs before using paid generation.",
            ],
        }
    except Exception:
        return {}


def _agent_trace_text(value, limit: int = 220) -> str:
    return _safe_evidence_quote(str(value or ""), limit=limit)


def _agent_trace_items(value, limit: int = 4) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = (
                item.get("label")
                or item.get("theme")
                or item.get("summary")
                or item.get("quote")
                or item.get("text")
                or ""
            )
        else:
            text = item
        cleaned = _agent_trace_text(text)
        if cleaned and cleaned not in items:
            items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def _agent_trace_count(value) -> int:
    return len(value) if isinstance(value, list) else 0


def _build_agent_trace(data: dict, output_language: str = "en") -> dict:
    if not isinstance(data, dict):
        return {}

    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    audience = data.get("audience") if isinstance(data.get("audience"), dict) else {}
    strategy = data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
    evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else {}
    evidence = insights.get("evidence") if isinstance(insights.get("evidence"), dict) else {}
    script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    llm_packet = data.get("llm_evidence_packet") if isinstance(data.get("llm_evidence_packet"), dict) else {}
    video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else {}
    packet_evidence = llm_packet.get("evidence") if isinstance(llm_packet.get("evidence"), dict) else {}
    packet_stats = llm_packet.get("review_stats") if isinstance(llm_packet.get("review_stats"), dict) else {}
    packet_product = llm_packet.get("product") if isinstance(llm_packet.get("product"), dict) else {}
    constraints = llm_packet.get("generation_constraints") if isinstance(llm_packet.get("generation_constraints"), list) else []
    warnings = (
        _agent_trace_items(packet_stats.get("warnings"), limit=4)
        + _agent_trace_items(evidence.get("data_warnings"), limit=4)
        + _agent_trace_items(constraints, limit=3)
    )
    source_type = (
        packet_product.get("source_type")
        or evidence.get("source_type")
        or storyboard.get("source")
        or "unknown"
    )
    review_count = (
        packet_stats.get("total_reviews")
        or packet_stats.get("review_count")
        or evidence.get("review_count")
        or 0
    )
    quote_count = _agent_trace_count(packet_evidence.get("quotes")) or _agent_trace_count(evidence.get("evidence_quotes"))
    video_formats = []
    if isinstance(video_packet.get("export_formats"), dict):
        video_formats = sorted(key for key, value in video_packet["export_formats"].items() if value)

    agents = {
        "evidence_agent": {
            "agent_name": "evidence_agent",
            "role": "Extract buyer evidence and source boundaries",
            "input_summary": f"packet={llm_packet.get('packet_version') or 'none'}; source_type={source_type}; reviews={review_count}",
            "output_summary": f"{quote_count} evidence quotes prepared with source boundary {source_type}.",
            "key_outputs": {
                "packet_version": llm_packet.get("packet_version", ""),
                "source_type": source_type,
                "review_count": review_count,
                "pain_points": _agent_trace_items(insights.get("pain_points") or packet_evidence.get("pain_points"), limit=4),
                "buyer_objections": _agent_trace_items(insights.get("buyer_objections") or packet_evidence.get("buyer_objections"), limit=4),
                "positive_signals": _agent_trace_items(insights.get("positive_signals") or packet_evidence.get("positive_signals"), limit=4),
                "evidence_quote_count": quote_count,
            },
            "warnings": warnings[:8],
            "status": "complete",
        },
        "strategy_agent": {
            "agent_name": "strategy_agent",
            "role": "Choose target audience and creative angle",
            "input_summary": "Uses top evidence signals, buyer objections, and positive proof from the evidence packet.",
            "output_summary": _agent_trace_text(strategy.get("core_hook_strategy") or script.get("hook"), limit=260),
            "key_outputs": {
                "audience_primary": _agent_trace_text(audience.get("primary")),
                "core_hook_strategy": _agent_trace_text(strategy.get("core_hook_strategy"), limit=260),
                "emotional_trigger": _agent_trace_text(strategy.get("emotional_trigger"), limit=260),
            },
            "warnings": [],
            "status": "complete",
        },
        "storyboard_agent": {
            "agent_name": "storyboard_agent",
            "role": "Turn strategy into short-form storyboard",
            "input_summary": _agent_trace_text(strategy.get("core_hook_strategy") or script.get("hook"), limit=220),
            "output_summary": f"{len(scenes)} storyboard scenes with hook and CTA.",
            "key_outputs": {
                "hook": _agent_trace_text(script.get("hook"), limit=260),
                "cta": _agent_trace_text(script.get("cta"), limit=260),
                "scene_count": len(scenes),
            },
            "warnings": [],
            "status": "complete",
        },
        "video_prompt_agent": {
            "agent_name": "video_prompt_agent",
            "role": "Convert storyboard into video prompts and export formats",
            "input_summary": f"storyboard_scene_count={len(scenes)}",
            "output_summary": f"video_packet={video_packet.get('packet_version') or 'none'}; scenes={_agent_trace_count(video_packet.get('scenes'))}",
            "key_outputs": {
                "packet_version": video_packet.get("packet_version", ""),
                "scene_count": _agent_trace_count(video_packet.get("scenes")),
                "export_format_keys": video_formats,
            },
            "warnings": _agent_trace_items(
                [
                    note
                    for scene in (video_packet.get("scenes") if isinstance(video_packet.get("scenes"), list) else [])
                    for note in (scene.get("risk_notes") if isinstance(scene, dict) and isinstance(scene.get("risk_notes"), list) else [])
                ],
                limit=4,
            ),
            "status": "complete",
        },
        "risk_agent": {
            "agent_name": "risk_agent",
            "role": "Check grounding and claim risk",
            "input_summary": _agent_trace_text(evaluation.get("reasoning"), limit=260),
            "output_summary": f"risk_level={evaluation.get('risk_level') or 'unknown'}; grounded={bool(evaluation.get('is_grounded'))}",
            "key_outputs": {
                "risk_level": evaluation.get("risk_level", ""),
                "is_grounded": bool(evaluation.get("is_grounded")),
                "is_approved": bool(evaluation.get("is_approved")),
                "confidence_score": evaluation.get("confidence_score", 0.0),
            },
            "warnings": _agent_trace_items(constraints, limit=4),
            "status": "complete",
        },
    }

    return {
        "trace_version": "agent_trace_v1",
        "execution_mode": "single_workflow_scaffold",
        "is_real_multi_agent_execution": False,
        "output_language": output_language or "en",
        "agents": agents,
        "agent_order": [
            "evidence_agent",
            "strategy_agent",
            "storyboard_agent",
            "video_prompt_agent",
            "risk_agent",
        ],
    }


def _pasted_review_signal_kind(quote: str) -> str:
    lowered = _clean_description_text(quote).lower()
    if not lowered:
        return "neutral"

    positive_value_markers = (
        "worth the price", "worth it", "cannot beat the price", "can't beat the price",
        "value priced", "great value", "good value",
    )
    explicit_price_objection_markers = (
        "too expensive", "high price", "not worth", "overpriced", "pricey", "pricy",
        "cost too much", "priced wrong", "price is wrong",
        "\u4ef7\u683c\u8d35", "\u592a\u8d35", "\u4e0d\u503c",
    )
    packaging_objection_markers = (
        "no lid", "not lid", "without a lid", "lid to go over the spout",
        "air is ever present", "oxidation", "cap leaked", "leaky cap", "bottle cap",
    )
    objection_markers = (
        "too much",
        "\u4ef7\u683c\u8d35", "\u592a\u8d35", "\u4e0d\u503c", "\u6027\u4ef7\u6bd4",
    )
    availability_markers = (
        "not available", "unavailable", "can't find", "cannot find", "hard to find",
        "west coast", "local store", "\u4e70\u4e0d\u5230", "\u4e0d\u597d\u4e70", "\u7f3a\u8d27", "\u897f\u6d77\u5cb8",
    )
    pain_markers = (
        "leak", "broken", "crack", "hard to clean", "too loud", "doesn't work",
        "stopped working", "bad", "terrible", "disappointed", "complain",
        "\u6f0f", "\u7834", "\u88c2", "\u96be\u6e05\u6d17", "\u592a\u5435", "\u5931\u671b", "\u5dee\u8bc4",
    )
    repeat_markers = (
        "continue to purchase", "will continue", "order it frequently", "buy again",
        "repeat purchase", "\u7ee7\u7eed\u8d2d\u4e70", "\u7ecf\u5e38\u8d2d\u4e70", "\u56de\u8d2d", "\u590d\u8d2d",
    )
    positive_markers = (
        "love", "best", "great", "smooth", "smoother", "flavor", "tastes good",
        "delicious", "worth it", "excellent", "favorite", "recommend",
        "\u6700\u597d", "\u559c\u6b22", "\u5f88\u559c\u6b22", "\u8d85\u68d2", "\u53e3\u611f", "\u987a\u6ed1", "\u5473\u9053", "\u597d\u8bc4", "\u63a8\u8350",
    )

    has_positive_value = any(marker in lowered for marker in positive_value_markers)
    has_price_objection = any(marker in lowered for marker in explicit_price_objection_markers)
    has_packaging_objection = any(marker in lowered for marker in packaging_objection_markers)

    if any(marker in lowered for marker in availability_markers):
        return "availability"
    if has_packaging_objection or has_price_objection or any(marker in lowered for marker in objection_markers):
        return "objection"
    if any(marker in lowered for marker in pain_markers):
        return "pain"
    if any(marker in lowered for marker in repeat_markers):
        return "repeat_purchase"
    if has_positive_value:
        return "positive"
    if any(marker in lowered for marker in positive_markers):
        return "positive"
    return "neutral"


def _pasted_review_is_price_value_positive_only(quote: str) -> bool:
    lowered = _clean_description_text(quote).lower()
    positive_value_markers = (
        "worth the price",
        "cannot beat the price",
        "can't beat the price",
        "value priced",
        "great value",
        "good value",
        "worth every",
        "for this quality",
    )
    explicit_price_objection_markers = (
        "too expensive",
        "high price",
        "not worth",
        "overpriced",
        "pricey",
        "pricy",
        "cost too much",
        "priced wrong",
        "price is wrong",
        "\u4ef7\u683c\u8d35",
        "\u592a\u8d35",
        "\u4e0d\u503c",
    )
    has_positive_value = any(marker in lowered for marker in positive_value_markers)
    has_explicit_price_objection = any(marker in lowered for marker in explicit_price_objection_markers)
    return has_positive_value and not has_explicit_price_objection


def _pasted_review_is_real_buyer_objection(quote: str) -> bool:
    kind = _pasted_review_signal_kind(quote)
    if kind not in {"objection", "availability"}:
        return False
    if _pasted_review_is_price_value_positive_only(quote):
        return False
    return True


def _pasted_review_signal_groups(evidence_quotes: list[str]) -> dict[str, list[str]]:
    groups = {
        "pain": [],
        "objection": [],
        "availability": [],
        "repeat_purchase": [],
        "positive": [],
        "neutral": [],
    }
    for quote in evidence_quotes:
        lowered = _clean_description_text(quote).lower()
        kind = _pasted_review_signal_kind(quote)
        target = groups.get(kind, groups["neutral"])
        if quote and quote not in target:
            target.append(quote)
        if quote and any(marker in lowered for marker in [
            "worth the price",
            "worth it",
            "cannot beat the price",
            "can't beat the price",
            "value priced",
            "great value",
            "good value",
        ]) and quote not in groups["positive"]:
            groups["positive"].append(quote)
    return groups


def _pasted_review_scene_goal(quote: str, request: PastedReviewsRequest, product_name: str, provided_goal: str | None = None) -> str:
    goal = _clean_description_text(provided_goal or "")
    kind = _pasted_review_signal_kind(quote)
    if goal and not (kind != "pain" and re.search(r"\bpain point\b|\bcustomer complaint\b", goal, flags=re.IGNORECASE)):
        return goal
    if kind in {"positive", "repeat_purchase"}:
        return "Show the positive review signal"
    if kind == "availability":
        return "Show the availability or scarcity signal"
    if kind == "objection":
        return "Show the buyer objection"
    if kind == "pain":
        return "Show the customer pain point"
    return "Show the core review signal"


async def generate_description_brief(request: ProductDescriptionRequest) -> dict:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0.4,
        max_retries=0,
    )
    content = (
        "Return JSON with keys: target_audience, core_hook_strategy, emotional_trigger, hook, "
        "cta, storyboard_scenes, evaluation_reasoning, feedback. "
        "storyboard_scenes must be a list of exactly 4 objects with visual_description, narration, evidence_quote_used.\n\n"
        f"Product name: {request.product_name}\n"
        f"Product category: {request.product_category or 'unspecified'}\n"
        f"Target platform: {request.target_platform or 'TikTok'}\n"
        f"Goal: {request.goal or 'tiktok_ctr'}\n"
        f"Product description: {request.product_description}\n"
        f"Customer pain points: {request.customer_pain_points}\n"
    )
    message = await llm.ainvoke(
        [
            SystemMessage(content=DESCRIPTION_SYSTEM_PROMPT),
            HumanMessage(content=content),
        ]
    )
    raw = str(message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Description generation returned non-object JSON.")
    return parsed


async def generate_pasted_reviews_brief(request: PastedReviewsRequest, evidence_quotes: list[str]) -> dict:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0.4,
        max_retries=0,
    )
    signal_groups = _pasted_review_signal_groups(evidence_quotes)
    pain_points = signal_groups["pain"][:4]
    buyer_objections = [
        quote
        for quote in (signal_groups["objection"] + signal_groups["availability"])
        if _pasted_review_is_real_buyer_objection(quote)
    ][:4]
    positive_signals = (signal_groups["positive"] + signal_groups["repeat_purchase"])[:4]
    neutral_signals = signal_groups["neutral"][:4]
    llm_evidence_packet = _review_workspace_packet_from_pasted_request(request) or _pasted_reviews_llm_evidence_packet(
        request,
        evidence_quotes,
        signal_groups,
        pain_points,
        buyer_objections,
        positive_signals,
        neutral_signals,
    )
    content = _pasted_reviews_llm_prompt_content(request, llm_evidence_packet)
    message = await llm.ainvoke(
        [
            SystemMessage(content=PASTED_REVIEWS_SYSTEM_PROMPT),
            HumanMessage(content=content),
        ]
    )
    raw = str(message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Pasted reviews generation returned non-object JSON.")
    return parsed


def _description_response_data(request: ProductDescriptionRequest, generated: dict) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_provided_product")
    description_quote = _safe_evidence_quote(request.product_description)
    pain_quote = _safe_evidence_quote(request.customer_pain_points)
    scenes = generated.get("storyboard_scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    normalized_scenes = []
    for index, scene in enumerate(scenes[:4]):
        if not isinstance(scene, dict):
            continue
        quote = scene.get("evidence_quote_used") or pain_quote or description_quote
        normalized_scenes.append(
            {
                "scene_id": index + 1,
                "scene_goal": scene.get("scene_goal", f"Show {product_name} benefit"),
                "visual_description": scene.get("visual_description", ""),
                "narration": scene.get("narration", ""),
                "evidence_quote_used": quote,
                "linked_painpoint": pain_quote,
            }
        )
    while len(normalized_scenes) < 4:
        index = len(normalized_scenes) + 1
        normalized_scenes.append(
            {
                "scene_id": index,
                "scene_goal": f"Make {product_name} feel useful",
                "visual_description": f"Show {product_name} solving the stated customer frustration in a simple {request.target_platform or 'TikTok'} scene.",
                "narration": f"{product_name} is positioned around the pain point: {pain_quote}",
                "evidence_quote_used": pain_quote or description_quote,
                "linked_painpoint": pain_quote,
            }
        )

    hook = generated.get("hook") or f"Stop ignoring this product pain point: {pain_quote}"
    cta = generated.get("cta") or f"Try {product_name} if this pain point sounds familiar."
    data = {
        "insights": {
            "pain_points": [pain_quote],
            "user_complaint_cluster": [pain_quote],
            "evidence": {
                "source_type": "user_provided_description",
                "source_url": "",
                "confidence": 0.55,
                "review_confidence": 0.0,
                "trend_confidence": 0.0,
                "review_count": 0,
                "evidence_quotes": [description_quote, pain_quote],
                "trend_signals": [],
                "data_warnings": ["user_provided_description_no_review_evidence"],
            },
        },
        "audience": {
            "primary": generated.get("target_audience", f"People considering {product_name}"),
            "sensitivity": generated.get("emotional_trigger", ""),
            "trust_barriers": [pain_quote],
        },
        "strategy": {
            "core_hook_strategy": generated.get("core_hook_strategy", ""),
            "emotional_trigger": generated.get("emotional_trigger", ""),
        },
        "assets": {
            "tiktok_script": {
                "hook": hook,
                "cta": cta,
            },
            "storyboard": {
                "product_name": product_name,
                "product_category": category,
                "source": "user_provided_description",
                "scenes": normalized_scenes,
            },
        },
        "evaluation": {
            "confidence_score": 0.62,
            "risk_level": "medium",
            "reasoning": generated.get(
                "evaluation_reasoning",
                "Generated from user-provided description only; no review evidence or source adapter was used.",
            ),
            "is_approved": True,
            "is_grounded": True,
            "creative_approved": True,
            "grounded_approved": True,
        },
        "feedback": generated.get(
            "feedback",
            "Generated from user-provided product description. Validate claims before using in paid creative.",
        ),
    }
    data["video_generation_packet"] = _build_video_generation_packet(
        product_name,
        category,
        data["assets"],
        data["insights"],
        data["evaluation"],
        getattr(request, "output_language", "en"),
    )
    data["external_video_tool_handoff"] = _build_external_video_tool_handoff(product_name, category, data)
    data["agent_trace"] = _build_agent_trace(data, getattr(request, "output_language", "en"))
    data["multi_agent_workflow"] = _build_multi_agent_workflow(data, getattr(request, "output_language", "en"))
    return data


def _multi_agent_workflow_text(value, limit: int = 260) -> str:
    return _agent_trace_text(value, limit=limit)


def _multi_agent_workflow_list(value, limit: int = 5) -> list[str]:
    return _agent_trace_items(value, limit=limit)


def _multi_agent_workflow_score(value, default: float = 0.66) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def _build_multi_agent_workflow(data: dict, output_language: str = "en") -> dict:
    """Build a business-grounded multi-agent workflow view from existing artifacts.

    This is not a separate multi-model execution engine yet. It is a transparent
    agent collaboration layer that maps current business artifacts into agent
    responsibilities, decisions, warnings, and handoffs.
    """
    if not isinstance(data, dict):
        return {}

    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    audience = data.get("audience") if isinstance(data.get("audience"), dict) else {}
    strategy = data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
    evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else {}
    script = assets.get("tiktok_script") if isinstance(assets.get("tiktok_script"), dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets.get("storyboard"), dict) else {}
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []

    llm_packet = data.get("llm_evidence_packet") if isinstance(data.get("llm_evidence_packet"), dict) else {}
    video_packet = data.get("video_generation_packet") if isinstance(data.get("video_generation_packet"), dict) else {}
    handoff = data.get("external_video_tool_handoff") if isinstance(data.get("external_video_tool_handoff"), dict) else {}
    agent_trace = data.get("agent_trace") if isinstance(data.get("agent_trace"), dict) else {}

    packet_evidence = llm_packet.get("evidence") if isinstance(llm_packet.get("evidence"), dict) else {}
    packet_stats = llm_packet.get("review_stats") if isinstance(llm_packet.get("review_stats"), dict) else {}
    packet_product = llm_packet.get("product") if isinstance(llm_packet.get("product"), dict) else {}
    constraints = llm_packet.get("generation_constraints") if isinstance(llm_packet.get("generation_constraints"), list) else []

    handoff_prompts = handoff.get("tool_prompts") if isinstance(handoff.get("tool_prompts"), dict) else {}
    keyframes = handoff.get("keyframe_prompts") if isinstance(handoff.get("keyframe_prompts"), list) else []
    product_rules = handoff.get("product_consistency_rules") if isinstance(handoff.get("product_consistency_rules"), list) else []
    product_asset_lock = handoff.get("product_asset_lock") if isinstance(handoff.get("product_asset_lock"), dict) else {}
    keyframe_plan = handoff.get("keyframe_plan") if isinstance(handoff.get("keyframe_plan"), dict) else {}
    plan_scenes = keyframe_plan.get("scenes") if isinstance(keyframe_plan.get("scenes"), list) else []

    source_type = (
        packet_product.get("source_type")
        or packet_evidence.get("source_type")
        or insights.get("evidence_source")
        or "unknown"
    )
    review_count = (
        packet_stats.get("review_count")
        or packet_evidence.get("review_count")
        or insights.get("review_count")
        or 0
    )
    evidence_quotes = packet_evidence.get("quotes") or packet_evidence.get("evidence_quotes") or insights.get("evidence_quotes") or []
    warning_items = (
        _multi_agent_workflow_list(packet_stats.get("warnings"), limit=4)
        + _multi_agent_workflow_list(insights.get("data_warnings"), limit=4)
        + _multi_agent_workflow_list(constraints, limit=4)
    )

    video_scenes = video_packet.get("scenes") if isinstance(video_packet.get("scenes"), list) else []
    export_formats = video_packet.get("export_formats") if isinstance(video_packet.get("export_formats"), dict) else {}
    export_keys = sorted(key for key, value in export_formats.items() if value)

    estimated_cost_summary = {}
    # A job-level provider_payload.cost_estimate is added later when a Video Job is created.
    # At generation time we expose the estimate agent as ready_for_job_creation.
    if isinstance(video_packet, dict):
        estimated_cost_summary = {
            "packet_version": video_packet.get("packet_version", ""),
            "recommended_duration_seconds": (video_packet.get("video") or {}).get("recommended_duration_seconds", ""),
            "scene_count": len(video_scenes),
            "requires_job_selection": True,
        }

    def agent(
        agent_id: str,
        role: str,
        goal: str,
        input_artifacts: list[str],
        decision_summary: str,
        output_artifacts: list[str],
        handoff_to: list[str],
        status: str = "complete",
        confidence_score: float = 0.66,
        warnings: list[str] | None = None,
        business_impact: str = "",
        requires_human_review: bool = False,
        key_outputs: dict | None = None,
    ) -> dict:
        return {
            "agent_id": agent_id,
            "role": role,
            "goal": goal,
            "status": status,
            "input_artifacts": input_artifacts,
            "decision_summary": _multi_agent_workflow_text(decision_summary, limit=420),
            "output_artifacts": output_artifacts,
            "handoff_to": handoff_to,
            "confidence_score": _multi_agent_workflow_score(confidence_score),
            "warnings": (warnings or [])[:8],
            "requires_human_review": bool(requires_human_review),
            "business_impact": business_impact,
            "key_outputs": key_outputs or {},
        }

    evidence_confidence = _multi_agent_workflow_score(packet_stats.get("source_confidence") or insights.get("source_confidence") or 0.64)
    risk_confidence = _multi_agent_workflow_score(evaluation.get("confidence_score") or 0.66)

    agents = [
        agent(
            "evidence_agent",
            "Evidence Agent",
            "Extract review-backed buyer signals and source boundaries.",
            ["llm_evidence_packet", "insights.evidence"],
            f"Using source_type={source_type}, prepared {len(evidence_quotes) if isinstance(evidence_quotes, list) else 0} evidence quotes from {review_count} review signals.",
            ["pain_points", "buyer_objections", "positive_signals", "evidence_quotes"],
            ["strategy_agent", "risk_agent"],
            confidence_score=evidence_confidence,
            warnings=warning_items,
            business_impact="Keeps creative generation grounded in buyer language instead of generic claims.",
            requires_human_review=bool(warning_items),
            key_outputs={
                "source_type": source_type,
                "review_count": review_count,
                "pain_points": _multi_agent_workflow_list(insights.get("pain_points") or packet_evidence.get("pain_points"), limit=5),
                "evidence_quote_count": len(evidence_quotes) if isinstance(evidence_quotes, list) else 0,
            },
        ),
        agent(
            "strategy_agent",
            "Strategy Agent",
            "Choose the audience, emotional trigger, and creative angle from the evidence.",
            ["llm_evidence_packet", "audience", "strategy"],
            strategy.get("core_hook_strategy") or script.get("hook") or "Use the strongest review-backed pain point as the creative angle.",
            ["target_audience", "core_hook_strategy", "emotional_trigger"],
            ["storyboard_agent", "risk_agent"],
            confidence_score=risk_confidence,
            business_impact="Turns raw buyer evidence into an ad direction that can convert.",
            key_outputs={
                "audience_primary": _multi_agent_workflow_text(audience.get("primary"), limit=320),
                "emotional_trigger": _multi_agent_workflow_text(strategy.get("emotional_trigger"), limit=320),
            },
        ),
        agent(
            "storyboard_agent",
            "Storyboard Agent",
            "Turn strategy into a short-form hook, CTA, and scene plan.",
            ["strategy", "assets.tiktok_script", "assets.storyboard"],
            f"Built a short-form script with hook={bool(script.get('hook'))}, cta={bool(script.get('cta'))}, scenes={len(scenes)}.",
            ["hook", "cta", "storyboard_scenes", "caption_draft"],
            ["asset_lock_agent", "keyframe_agent", "prompt_handoff_agent"],
            confidence_score=risk_confidence,
            business_impact="Converts strategy into a concrete shot list that creators or video tools can follow.",
            key_outputs={
                "hook": _multi_agent_workflow_text(script.get("hook"), limit=320),
                "cta": _multi_agent_workflow_text(script.get("cta"), limit=320),
                "scene_count": len(scenes),
            },
        ),
        agent(
            "asset_lock_agent",
            "Asset Lock Agent",
            "Define product identity and visual consistency constraints before generation.",
            ["product fields", "external_video_tool_handoff.product_asset_lock", "external_video_tool_handoff.product_consistency_rules"],
            "Prepared a product asset lock so external video tools preserve product identity, category, visible material, color, shape, and evidence boundaries.",
            ["product_asset_lock", "product_consistency_rules", "negative_prompt"],
            ["keyframe_agent", "prompt_handoff_agent", "risk_agent"],
            confidence_score=0.76 if product_asset_lock else (0.72 if product_rules else 0.55),
            warnings=[] if product_asset_lock else ["Product asset lock is missing or weak."],
            business_impact="Reduces product drift when using Gemini, Doubao, Runway, Pika, or other external tools.",
            requires_human_review=not bool(product_asset_lock),
            key_outputs={
                "asset_lock_version": product_asset_lock.get("lock_version", ""),
                "product_identity": product_asset_lock.get("product_identity", ""),
                "must_preserve": _multi_agent_workflow_list(product_asset_lock.get("must_preserve"), limit=5),
                "must_not_change": _multi_agent_workflow_list(product_asset_lock.get("must_not_change"), limit=5),
                "rule_count": len(product_rules),
                "rules": product_rules[:5],
            },
        ),
        agent(
            "keyframe_agent",
            "Keyframe Agent",
            "Convert storyboard scenes into controllable keyframes and motion prompts.",
            ["video_generation_packet.scenes", "external_video_tool_handoff.keyframe_prompts", "external_video_tool_handoff.keyframe_plan"],
            f"Prepared {len(plan_scenes) or len(keyframes)} planned keyframes for external video generation tools.",
            ["keyframe_plan", "keyframe_prompts", "motion_prompts", "overlay_text"],
            ["prompt_handoff_agent", "experiment_agent"],
            confidence_score=0.76 if keyframe_plan else (0.72 if keyframes else 0.55),
            warnings=[] if keyframe_plan else ["Keyframe plan is missing; external video tools may improvise too much."],
            business_impact="Improves generation stability by breaking the video into scene-level visual targets.",
            requires_human_review=not bool(keyframe_plan),
            key_outputs={
                "keyframe_plan_version": keyframe_plan.get("plan_version", ""),
                "keyframe_plan_scene_count": keyframe_plan.get("scene_count", 0),
                "recommended_clip_strategy": keyframe_plan.get("recommended_clip_strategy", ""),
                "keyframe_count": len(keyframes),
                "first_keyframe_goal": _multi_agent_workflow_text((keyframes[0] or {}).get("keyframe_goal") if keyframes else "", limit=240),
            },
        ),
        agent(
            "prompt_handoff_agent",
            "Prompt Handoff Agent",
            "Create copy-ready prompts for Gemini, Doubao, image-to-video, and manual workflows.",
            ["video_generation_packet", "external_video_tool_handoff"],
            "Generated external tool prompts without calling external APIs or incurring CrossGrowth cost.",
            ["gemini_video_prompt", "doubao_video_prompt", "general_image_to_video_prompt", "copy_ready_generation_brief"],
            ["cost_agent", "experiment_agent"],
            confidence_score=0.74 if handoff_prompts else 0.55,
            warnings=_multi_agent_workflow_list(handoff.get("warnings"), limit=5),
            business_impact="Lets the user test real external tools manually before committing to paid API integration.",
            key_outputs={
                "packet_version": handoff.get("packet_version", ""),
                "prompt_keys": sorted(key for key, value in handoff_prompts.items() if value),
                "external_api_called": bool(handoff.get("external_api_called", False)),
                "cost_incurred_by_crossgrowth": bool(handoff.get("cost_incurred_by_crossgrowth", False)),
            },
        ),
        agent(
            "cost_agent",
            "Cost Agent",
            "Estimate video generation cost before any real paid provider call.",
            ["video_generation_packet", "provider cost catalog"],
            "Prepared cost-estimate context. Final provider-specific estimate is attached when the user creates a Video Job.",
            ["cost_estimate_context", "requires_user_confirmation"],
            ["provider_job_agent", "risk_agent"],
            status="ready_for_job_creation",
            confidence_score=0.7,
            warnings=["Pricing is estimate-only and must be reviewed before enabling real external API calls."],
            business_impact="Prevents accidental cost surprises before paid video generation.",
            requires_human_review=True,
            key_outputs=estimated_cost_summary,
        ),
        agent(
            "risk_agent",
            "Risk Agent",
            "Check evidence grounding, unsupported claims, and generation risk.",
            ["llm_evidence_packet", "evaluation", "generation_constraints"],
            evaluation.get("reasoning") or "Checked available evidence boundaries and generation constraints.",
            ["risk_level", "is_grounded", "approval_status", "warnings"],
            ["provider_job_agent", "experiment_agent"],
            confidence_score=risk_confidence,
            warnings=_multi_agent_workflow_list(constraints, limit=5),
            business_impact="Protects the output from unsupported market-wide or unverifiable claims.",
            requires_human_review=bool(warning_items) or evaluation.get("risk_level") == "high",
            key_outputs={
                "risk_level": evaluation.get("risk_level", ""),
                "is_grounded": bool(evaluation.get("is_grounded")),
                "is_approved": bool(evaluation.get("is_approved")),
                "confidence_score": evaluation.get("confidence_score", 0.0),
            },
        ),
        agent(
            "provider_job_agent",
            "Provider Job Agent",
            "Track video generation jobs, provider status, result URLs, and manual fallback.",
            ["video_generation_packet", "provider_payload", "cost_estimate"],
            "Ready to create a tracked Video Job. The current generation flow does not call external video APIs.",
            ["video_job", "provider_runtime", "result_url", "history"],
            ["experiment_agent"],
            status="waiting_for_user_action",
            confidence_score=0.66,
            warnings=["Video Job records are memory-backed unless file storage or database persistence is enabled."],
            business_impact="Turns generated prompts into a trackable production task with status and result history.",
            requires_human_review=True,
            key_outputs={
                "supported_providers": ["manual_export", "generic", "capcut", "runway", "pika"],
                "simulated_provider_flow": "ready_for_manual_export -> queued -> processing -> external_result_ready",
            },
        ),
        agent(
            "experiment_agent",
            "Experiment Agent",
            "Record and compare manual Gemini, Doubao, Runway, Pika, or other external video results.",
            ["external_video_tool_handoff", "external_video_experiments"],
            "Waiting for the user to paste external tool results, costs, scores, and notes.",
            ["external_video_experiments", "quality_scores", "tool_comparison"],
            [],
            status="waiting_for_user_experiment",
            confidence_score=0.62,
            warnings=["Manual experiment quality requires user-provided result URLs, screenshots, or notes."],
            business_impact="Collects evidence for deciding whether a real provider API is worth integrating.",
            requires_human_review=True,
            key_outputs={
                "score_dimensions": [
                    "product_consistency",
                    "storyboard_following",
                    "visual_quality",
                    "ad_readiness",
                    "overall",
                ],
            },
        ),
    ]

    agent_order = [item["agent_id"] for item in agents]
    artifact_index = {
        "llm_evidence_packet": bool(llm_packet),
        "video_generation_packet": bool(video_packet),
        "external_video_tool_handoff": bool(handoff),
        "product_asset_lock": bool(product_asset_lock),
        "keyframe_plan": bool(keyframe_plan),
        "agent_trace": bool(agent_trace),
        "cost_estimate_context": bool(estimated_cost_summary),
    }

    return {
        "workflow_version": "multi_agent_workflow_v2",
        "workflow_name": "Business-grounded multi-agent video production workflow",
        "execution_mode": "artifact_orchestrated_agent_workflow",
        "is_real_multi_agent_execution": False,
        "is_plain_automation": False,
        "differentiator": "Each agent is mapped to a business artifact, decision, warning, and handoff instead of a simple linear automation step.",
        "output_language": output_language or "en",
        "agent_order": agent_order,
        "agents": agents,
        "artifact_index": artifact_index,
        "business_goal": "Transform review evidence into a controllable external video generation package and track manual/paid provider experiments.",
        "next_recommended_action": "Review the external video tool handoff, test Gemini or Doubao manually, then record the result in External Video Experiments.",
    }


def _pasted_reviews_llm_evidence_packet(
    request: PastedReviewsRequest,
    evidence_quotes: list[str],
    signal_groups: dict[str, list[str]],
    pain_points: list[str],
    buyer_objections: list[str],
    positive_signals: list[str],
    neutral_signals: list[str],
) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_pasted_reviews_product")
    warnings = [
        "user_pasted_reviews_unverified",
        "user_pasted_reviews_no_external_fetch",
    ]

    return {
        "packet_version": "pasted_reviews_v1",
        "intended_model_use": "creative_brief_generation",
        "product": {
            "title": product_name,
            "category": category,
            "source_type": "user_pasted_reviews",
            "source_url": "",
        },
        "review_stats": {
            "review_count": len(evidence_quotes),
            "source_confidence": 0.64,
            "review_confidence": 0.64,
            "trend_confidence": 0.0,
            "warnings": warnings,
        },
        "evidence": {
            "quotes": evidence_quotes[:12],
            "pain_points": pain_points[:4],
            "buyer_objections": buyer_objections[:4],
            "positive_signals": positive_signals[:4],
            "repeat_purchase_signals": signal_groups.get("repeat_purchase", [])[:3],
            "availability_signals": signal_groups.get("availability", [])[:3],
            "use_cases": neutral_signals[:4],
        },
        "generation_constraints": [
            "Use only the supplied review evidence and product fields.",
            "Do not claim full-market statistics or verified purchase coverage beyond the provided metadata.",
            "Keep uncertainty visible when evidence comes from pasted or extension-collected reviews.",
            "Prefer product-specific review language over generic category claims.",
            "Do not turn buyer objections into positive claims unless the evidence explicitly resolves the concern.",
        ],
    }


def _review_workspace_packet_from_pasted_request(request: PastedReviewsRequest) -> dict | None:
    packet = getattr(request, "llm_evidence_packet", None)
    if isinstance(packet, dict) and packet.get("packet_version") == "review_workspace_v1":
        return packet
    return None


def _pasted_reviews_llm_prompt_content(request: PastedReviewsRequest, llm_evidence_packet: dict) -> str:
    target_platform = getattr(request, "target_platform", None) or "TikTok"
    goal = getattr(request, "goal", None) or "tiktok_ctr"
    return (
        "Return JSON with keys: target_audience, core_hook_strategy, emotional_trigger, hook, "
        "cta, storyboard_scenes, evaluation_reasoning, feedback. "
        "storyboard_scenes must be a list of exactly 4 objects with visual_description, narration, evidence_quote_used.\n\n"
        "Use the following llm_evidence_packet as the only evidence source. "
        "Follow generation_constraints strictly. Do not use raw assumptions outside the packet.\n\n"
        f"Target platform: {target_platform}\n"
        f"Goal: {goal}\n"
        "llm_evidence_packet JSON:\n"
        f"{json.dumps(llm_evidence_packet, ensure_ascii=False, indent=2)}"
    )


def _pasted_reviews_response_data(
    request: PastedReviewsRequest,
    generated: dict,
    evidence_quotes: list[str],
) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_pasted_reviews_product")
    description_quote = _safe_evidence_quote(request.product_description or "")
    primary_quote = evidence_quotes[0] if evidence_quotes else ""
    signal_groups = _pasted_review_signal_groups(evidence_quotes)
    pain_points = signal_groups["pain"][:4]
    buyer_objections = [quote for quote in (signal_groups["objection"] + signal_groups["availability"]) if _pasted_review_is_real_buyer_objection(quote)][:4]
    positive_signals = (signal_groups["positive"] + signal_groups["repeat_purchase"])[:4]
    neutral_signals = signal_groups["neutral"][:4]
    scenes = generated.get("storyboard_scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    normalized_scenes = []
    for index, scene in enumerate(scenes[:4]):
        if not isinstance(scene, dict):
            continue
        fallback_quote = evidence_quotes[index % len(evidence_quotes)] if evidence_quotes else primary_quote
        quote = _safe_evidence_quote(_clean_pasted_review_quote_text(scene.get("evidence_quote_used") or fallback_quote), limit=240)
        normalized_scenes.append(
            {
                "scene_id": index + 1,
                "scene_goal": _pasted_review_scene_goal(quote, request, product_name, scene.get("scene_goal")),
                "visual_description": scene.get("visual_description", ""),
                "narration": scene.get("narration", ""),
                "evidence_quote_used": quote,
                "linked_painpoint": quote,
            }
        )

    while len(normalized_scenes) < 4:
        index = len(normalized_scenes) + 1
        quote = evidence_quotes[(index - 1) % len(evidence_quotes)] if evidence_quotes else primary_quote
        quote = _safe_evidence_quote(_clean_pasted_review_quote_text(quote), limit=240)
        normalized_scenes.append(
            {
                "scene_id": index,
                "scene_goal": _pasted_review_scene_goal(quote, request, product_name),
                "visual_description": f"Show {product_name} turning this customer review signal into a simple product scene.",
                "narration": f"This review signal becomes the creative angle: {quote}",
                "evidence_quote_used": quote,
                "linked_painpoint": quote,
            }
        )

    hook = generated.get("hook") or f"If this review sounds familiar, {product_name} needs a better creative angle."
    cta = generated.get("cta") or f"Use {product_name} to answer the review signal your buyers already mention."
    llm_evidence_packet = _review_workspace_packet_from_pasted_request(request) or _pasted_reviews_llm_evidence_packet(
        request,
        evidence_quotes,
        signal_groups,
        pain_points,
        buyer_objections,
        positive_signals,
        neutral_signals,
    )

    data = {
        "insights": {
            "pain_points": pain_points,
            "buyer_objections": buyer_objections,
            "positive_signals": positive_signals,
            "social_proof": positive_signals,
            "repeat_purchase_signals": signal_groups["repeat_purchase"][:3],
            "availability_signals": signal_groups["availability"][:3],
            "user_complaint_cluster": pain_points + buyer_objections,
            "customer_feedback_signals": (pain_points + buyer_objections + positive_signals + neutral_signals)[:6],
            "evidence": {
                "source_type": "user_pasted_reviews",
                "source_url": "",
                "confidence": 0.64,
                "review_confidence": 0.64,
                "trend_confidence": 0.0,
                "review_count": len(evidence_quotes),
                "evidence_quotes": evidence_quotes,
                "trend_signals": [],
                "data_warnings": [
                    "user_pasted_reviews_unverified",
                    "user_pasted_reviews_no_external_fetch",
                ],
            },
        },
        "audience": {
            "primary": generated.get("target_audience", f"People considering {product_name}"),
            "sensitivity": generated.get("emotional_trigger", ""),
            "trust_barriers": buyer_objections,
        },
        "strategy": {
            "core_hook_strategy": generated.get("core_hook_strategy", ""),
            "emotional_trigger": generated.get("emotional_trigger", ""),
        },
        "assets": {
            "tiktok_script": {
                "hook": hook,
                "cta": cta,
            },
            "storyboard": {
                "product_name": product_name,
                "product_category": category,
                "source": "user_pasted_reviews",
                "scenes": normalized_scenes,
            },
        },
        "evaluation": {
            "confidence_score": 0.66,
            "risk_level": "medium",
            "reasoning": generated.get(
                "evaluation_reasoning",
                "Generated from user-pasted review snippets only; no external fetch or source adapter was used.",
            ),
            "is_approved": True,
            "is_grounded": True,
            "creative_approved": True,
            "grounded_approved": True,
        },
        "feedback": generated.get(
            "feedback",
            "Generated from pasted reviews. Verify claims and review authenticity before using in paid creative.",
        ),
        "llm_evidence_packet": llm_evidence_packet,
    }
    data["video_generation_packet"] = _build_video_generation_packet(
        product_name,
        category,
        data["assets"],
        data["insights"],
        data["evaluation"],
        getattr(request, "output_language", "en"),
    )
    data["external_video_tool_handoff"] = _build_external_video_tool_handoff(product_name, category, data)
    data["agent_trace"] = _build_agent_trace(data, getattr(request, "output_language", "en"))
    data["multi_agent_workflow"] = _build_multi_agent_workflow(data, getattr(request, "output_language", "en"))
    return data


def _agent_run_not_found(run_id: str):
    raise HTTPException(status_code=404, detail=f"Agent run not found: {run_id}")


def _start_agent_run_stage(run_id: str, agent_id: str, message: str, data: dict | None = None) -> None:
    AGENT_RUN_STORE.start_agent(run_id, agent_id)
    AGENT_RUN_STORE.set_graph_node_status(run_id, agent_id, "running")
    AGENT_RUN_STORE.append_event(
        run_id,
        "agent_started",
        message,
        agent_id=agent_id,
        data=data or {},
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "node_started",
        message,
        agent_id=agent_id,
        data={"node_id": agent_id, **(data or {})},
    )


def _complete_agent_run_stage(
    run_id: str,
    agent_id: str,
    message: str,
    decision_summary: str,
    business_impact: str = "",
    output_artifacts: list[str] | None = None,
    warnings: list[str] | None = None,
    data: dict | None = None,
) -> None:
    AGENT_RUN_STORE.complete_agent(
        run_id,
        agent_id,
        decision_summary=decision_summary,
        business_impact=business_impact,
        output_artifacts=output_artifacts,
        warnings=warnings,
    )
    AGENT_RUN_STORE.set_graph_node_status(run_id, agent_id, "complete")
    AGENT_RUN_STORE.append_event(
        run_id,
        "agent_completed",
        message,
        agent_id=agent_id,
        data=data or {},
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "node_completed",
        message,
        agent_id=agent_id,
        data={"node_id": agent_id, **(data or {})},
    )


def _traverse_agent_graph_edge(run_id: str, edge_id: str, reason: str) -> None:
    AGENT_RUN_STORE.traverse_graph_edge(run_id, edge_id, reason)
    AGENT_RUN_STORE.append_event(
        run_id,
        "edge_traversed",
        f"Graph edge traversed: {edge_id}.",
        data={"edge_id": edge_id, "reason": reason},
    )


def _record_graph_transition_decision(
    run_id: str,
    from_node_id: str,
    selected_to_node_id: str,
    agent_id: str,
    decision_type: str,
    reason: str,
    data: dict | None = None,
) -> None:
    decision = AGENT_RUN_STORE.add_transition_decision(
        run_id,
        from_node_id,
        selected_to_node_id,
        agent_id,
        decision_type,
        reason,
        data=data or {},
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "transition_decision",
        reason,
        agent_id=agent_id,
        data=decision,
    )


def _record_graph_validation_result(
    run_id: str,
    validator_agent_id: str,
    target_agent_id: str,
    target_artifact: str,
    status: str,
    reason: str,
    severity: str = "low",
    rework_target: str = "",
) -> None:
    validation = AGENT_RUN_STORE.add_validation_result(
        run_id,
        validator_agent_id,
        target_agent_id,
        target_artifact,
        status,
        reason,
        severity,
        rework_target,
    )
    event_type = "validation_failed" if status == "failed" else "validation_passed"
    AGENT_RUN_STORE.append_event(
        run_id,
        event_type,
        reason,
        agent_id=validator_agent_id,
        data=validation,
    )


def _record_graph_rework_loop(
    run_id: str,
    source_agent_id: str,
    target_agent_id: str,
    reason: str,
    status: str = "requested",
) -> None:
    loop = AGENT_RUN_STORE.add_rework_loop(
        run_id,
        source_agent_id,
        target_agent_id,
        reason,
        status=status,
    )
    AGENT_RUN_STORE.append_event(
        run_id,
        "rework_requested",
        reason,
        agent_id=source_agent_id,
        data=loop,
    )


async def _execute_pasted_reviews_agent_run(run_id: str, request: PastedReviewsRequest) -> None:
    current_agent_id = ""
    try:
        AGENT_RUN_STORE.start_run(run_id)
        AGENT_RUN_STORE.append_event(
            run_id,
            "run_started",
            "Backend-tracked async agent run started.",
            data={"input_type": "pasted_reviews", "output_language": request.output_language or "en"},
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "graph_initialized",
            "Rule-driven agent graph initialized.",
            data={
                "graph_version": "agent_graph_runtime_v1",
                "graph_execution_mode": "rule_driven_agent_graph",
                "autonomy_level": "rule_driven_v1",
                "llm_autonomous_decision_enabled": False,
            },
        )

        current_agent_id = "planner_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Planner Agent validating pasted feedback request.")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Planner Agent completed request validation.",
            "Validated the pasted customer feedback request for artifact-orchestrated async generation.",
            "The run can proceed without changing the existing synchronous endpoint.",
            ["validated_generation_plan"],
        )
        _record_graph_transition_decision(
            run_id,
            "planner_agent",
            "evidence_agent",
            current_agent_id,
            "proceed",
            "Request validation passed; proceed to evidence extraction.",
        )
        _traverse_agent_graph_edge(run_id, "planner_to_evidence", "Request validation passed.")

        current_agent_id = "evidence_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Evidence Agent building review evidence packet.")
        evidence_quotes = _split_pasted_review_quotes(request.pasted_reviews)
        signal_groups = _pasted_review_signal_groups(evidence_quotes)
        pain_points = signal_groups["pain"][:4]
        buyer_objections = [
            quote
            for quote in (signal_groups["objection"] + signal_groups["availability"])
            if _pasted_review_is_real_buyer_objection(quote)
        ][:4]
        positive_signals = (signal_groups["positive"] + signal_groups["repeat_purchase"])[:4]
        neutral_signals = signal_groups["neutral"][:4]
        llm_evidence_packet = _review_workspace_packet_from_pasted_request(request) or _pasted_reviews_llm_evidence_packet(
            request,
            evidence_quotes,
            signal_groups,
            pain_points,
            buyer_objections,
            positive_signals,
            neutral_signals,
        )
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Evidence Agent completed evidence packet.",
            "Built the LLM evidence packet from supplied review snippets and product fields.",
            "Keeps review evidence explicit before any creative claims are made.",
            ["evidence_quotes", "llm_evidence_packet"],
            warnings=(llm_evidence_packet.get("review_stats") or {}).get("warnings") or [],
            data={
                "quote_count": len(evidence_quotes),
                "packet_version": llm_evidence_packet.get("packet_version"),
            },
        )
        _record_graph_transition_decision(
            run_id,
            "evidence_agent",
            "strategy_agent",
            current_agent_id,
            "proceed",
            "Evidence packet exists; proceed to strategy generation.",
            data={"packet_version": llm_evidence_packet.get("packet_version")},
        )
        _traverse_agent_graph_edge(run_id, "evidence_to_strategy", "Evidence packet built.")

        current_agent_id = "strategy_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Strategy Agent calling existing creative generation helper.")
        generated = await generate_pasted_reviews_brief(request, evidence_quotes)
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Strategy Agent completed creative strategy generation.",
            "Generated hook strategy, emotional trigger, hook, CTA, and storyboard draft from the evidence packet.",
            "Turns review evidence into a creative direction while preserving the existing generation behavior.",
            ["creative_strategy", "hook", "cta"],
        )
        _record_graph_transition_decision(
            run_id,
            "strategy_agent",
            "storyboard_agent",
            current_agent_id,
            "proceed",
            "Creative strategy generated; proceed to storyboard normalization.",
        )
        _traverse_agent_graph_edge(run_id, "strategy_to_storyboard", "Creative strategy generated.")

        current_agent_id = "storyboard_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Storyboard Agent building product response artifacts.")
        data = _pasted_reviews_response_data(request, generated, evidence_quotes)
        scenes = ((data.get("assets") or {}).get("storyboard") or {}).get("scenes") or []
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Storyboard Agent completed scenes and script assets.",
            "Normalized generated storyboard scenes into the Product Mode response shape.",
            "Makes the generated result reusable by copy, export, translation, and video job flows.",
            ["storyboard", "tiktok_script"],
            data={"scene_count": len(scenes)},
        )
        _record_graph_transition_decision(
            run_id,
            "storyboard_agent",
            "risk_agent",
            current_agent_id,
            "proceed",
            "Storyboard artifacts exist; run risk validation.",
            data={"scene_count": len(scenes)},
        )
        _traverse_agent_graph_edge(run_id, "storyboard_to_risk", "Storyboard requires risk validation.")

        current_agent_id = "risk_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Risk Agent reviewing warnings and evidence boundaries.")
        evidence = ((data.get("insights") or {}).get("evidence") or {})
        data_warnings = list(evidence.get("data_warnings") or [])
        evaluation = data.get("evaluation") or {}
        risk_level = str(evaluation.get("risk_level") or "").lower()
        warning_text = " ".join(str(item or "") for item in data_warnings).lower()
        unsupported_risk = any(token in warning_text for token in ["unsupported", "medical", "full-market", "full market"])
        risk_check = detect_storyboard_rework_need(data)
        if unsupported_risk and not risk_check.get("needs_rework"):
            risk_check = {
                "needs_rework": True,
                "reason": "Unsupported evidence-boundary warning requires storyboard rework.",
                "matched_terms": ["unsupported_warning"],
                "severity": "high" if "medical" in warning_text else "medium",
            }
        needs_rework = bool(risk_check.get("needs_rework"))
        risk_failed = needs_rework and risk_check.get("severity") == "high"
        risk_validation_status = "failed" if risk_failed else ("warning" if needs_rework or risk_level == "medium" or data_warnings else "passed")
        risk_reason = (
            str(risk_check.get("reason") or "Risk validation requested storyboard rework.")
            if needs_rework
            else "Risk validation passed with warnings." if risk_validation_status == "warning"
            else "Risk validation passed."
        )
        _record_graph_validation_result(
            run_id,
            "risk_agent",
            "storyboard_agent",
            "storyboard",
            risk_validation_status,
            risk_reason,
            severity=str(risk_check.get("severity") or ("medium" if risk_validation_status == "warning" else "low")),
            rework_target="storyboard_agent" if needs_rework else "",
        )
        if needs_rework:
            current_run_state = AGENT_RUN_STORE.get(run_id) or {}
            loop_count = int(current_run_state.get("loop_count") or 0)
            max_loop_count = int(current_run_state.get("max_loop_count") or 1)
            _record_graph_transition_decision(
                run_id,
                "risk_agent",
                "storyboard_agent",
                current_agent_id,
                "rework_requested",
                risk_reason,
                data={
                    "risk_level": risk_level,
                    "loop_count": loop_count,
                    "max_loop_count": max_loop_count,
                    "matched_terms": risk_check.get("matched_terms") or [],
                },
            )
            if loop_count < max_loop_count:
                _record_graph_rework_loop(
                    run_id,
                    "risk_agent",
                    "storyboard_agent",
                    risk_reason,
                    status="applied",
                )
                _traverse_agent_graph_edge(run_id, "risk_to_storyboard_rework", "Risk validation requested evidence-safe storyboard rework.")
                _complete_agent_run_stage(
                    run_id,
                    current_agent_id,
                    "Risk Agent requested evidence-safe storyboard rework.",
                    "Detected risky unsupported storyboard wording and routed the graph back to Storyboard Agent.",
                    "Prevents absolute or unsupported claims from continuing into video handoff.",
                    ["risk_notes", "rework_request"],
                    warnings=data_warnings,
                    data={
                        "matched_terms": risk_check.get("matched_terms") or [],
                        "severity": risk_check.get("severity"),
                    },
                )

                current_agent_id = "storyboard_agent"
                _start_agent_run_stage(run_id, current_agent_id, "Storyboard Agent applying evidence-safe rework.")
                data = apply_evidence_safe_storyboard_rework(
                    data,
                    risk_reason,
                    list(risk_check.get("matched_terms") or []),
                )
                scenes = ((data.get("assets") or {}).get("storyboard") or {}).get("scenes") or []
                _complete_agent_run_stage(
                    run_id,
                    current_agent_id,
                    "Storyboard Agent applied evidence-safe rework.",
                    "Replaced unsupported absolute wording with evidence-bound phrasing.",
                    "Keeps the generated storyboard usable while preserving supplied evidence and product identity.",
                    ["storyboard", "tiktok_script", "agent_graph_rework_summary"],
                    data={"scene_count": len(scenes), "rework_applied": True},
                )
                _record_graph_transition_decision(
                    run_id,
                    "storyboard_agent",
                    "risk_agent",
                    current_agent_id,
                    "validation_requested",
                    "Evidence-safe storyboard rework applied; Risk Agent must validate again.",
                    data={"scene_count": len(scenes), "rework_applied": True},
                )
                _traverse_agent_graph_edge(run_id, "storyboard_to_risk", "Reworked storyboard requires risk validation.")

                current_agent_id = "risk_agent"
                _start_agent_run_stage(run_id, current_agent_id, "Risk Agent re-validating evidence-safe storyboard rework.")
                evidence = ((data.get("insights") or {}).get("evidence") or {})
                data_warnings = list(evidence.get("data_warnings") or [])
                evaluation = data.get("evaluation") or {}
                risk_level = str(evaluation.get("risk_level") or "").lower()
                warning_text = " ".join(str(item or "") for item in data_warnings).lower()
                unsupported_risk = any(token in warning_text for token in ["unsupported", "medical", "full-market", "full market"])
                second_risk_check = detect_storyboard_rework_need(data)
                if unsupported_risk and not second_risk_check.get("needs_rework"):
                    second_risk_check = {
                        "needs_rework": True,
                        "reason": "Unsupported evidence-boundary warning remains after storyboard rework.",
                        "matched_terms": ["unsupported_warning"],
                        "severity": "high" if "medical" in warning_text else "medium",
                    }
                second_needs_rework = bool(second_risk_check.get("needs_rework"))
                if second_needs_rework:
                    second_reason = str(second_risk_check.get("reason") or "Risk remains after evidence-safe rework.")
                    _record_graph_validation_result(
                        run_id,
                        "risk_agent",
                        "storyboard_agent",
                        "storyboard",
                        "failed" if second_risk_check.get("severity") == "high" else "warning",
                        second_reason,
                        severity=str(second_risk_check.get("severity") or "medium"),
                        rework_target="storyboard_agent",
                    )
                    _record_graph_rework_loop(
                        run_id,
                        "risk_agent",
                        "storyboard_agent",
                        "Risk rework limit reached; human review is required before relying on storyboard claims.",
                        status="blocked",
                    )
                    AGENT_RUN_STORE.set_waiting_for_user(
                        run_id,
                        True,
                        "risk rework limit reached; human review is required before relying on storyboard claims.",
                    )
                    AGENT_RUN_STORE.append_event(
                        run_id,
                        "waiting_for_user",
                        "Risk rework limit reached; human review is required before relying on storyboard claims.",
                        agent_id="risk_agent",
                        data={"node_id": "risk_agent", "matched_terms": second_risk_check.get("matched_terms") or []},
                    )
                    _record_graph_transition_decision(
                        run_id,
                        "risk_agent",
                        "asset_lock_agent",
                        "risk_agent",
                        "validation_warning",
                        "Rework limit reached; continue with human review required and no further automatic loop.",
                        data={"loop_count": int((AGENT_RUN_STORE.get(run_id) or {}).get("loop_count") or 0), "max_loop_count": max_loop_count},
                    )
                else:
                    second_status = "warning" if risk_level == "medium" or data_warnings else "passed"
                    second_reason = "Risk validation passed after evidence-safe storyboard rework." if second_status == "passed" else "Risk validation passed after rework with warnings."
                    _record_graph_validation_result(
                        run_id,
                        "risk_agent",
                        "storyboard_agent",
                        "storyboard",
                        second_status,
                        second_reason,
                        severity="medium" if second_status == "warning" else "low",
                    )
                    _record_graph_transition_decision(
                        run_id,
                        "risk_agent",
                        "asset_lock_agent",
                        "risk_agent",
                        "validation_passed",
                        second_reason,
                        data={"risk_level": risk_level, "warning_count": len(data_warnings), "rework_applied": True},
                    )
                _traverse_agent_graph_edge(run_id, "risk_to_asset_lock", "Risk accepted after evidence-safe rework.")
                risk_reason = second_reason
            else:
                _record_graph_rework_loop(
                    run_id,
                    "risk_agent",
                    "storyboard_agent",
                    "Risk rework limit reached; human review is required before relying on storyboard claims.",
                    status="blocked",
                )
                AGENT_RUN_STORE.set_waiting_for_user(
                    run_id,
                    True,
                    "risk rework limit reached; human review is required before relying on storyboard claims.",
                )
                AGENT_RUN_STORE.append_event(
                    run_id,
                    "waiting_for_user",
                    "Risk rework limit reached; human review is required before relying on storyboard claims.",
                    agent_id="risk_agent",
                    data={"node_id": "risk_agent", "matched_terms": risk_check.get("matched_terms") or []},
                )
                _traverse_agent_graph_edge(run_id, "risk_to_asset_lock", "Risk rework limit reached; continue with human review required.")
        else:
            _record_graph_transition_decision(
                run_id,
                "risk_agent",
                "asset_lock_agent",
                current_agent_id,
                "validation_passed",
                risk_reason,
                data={"risk_level": risk_level, "warning_count": len(data_warnings)},
            )
            _traverse_agent_graph_edge(run_id, "risk_to_asset_lock", "Risk accepted or warning-only.")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Risk Agent completed evidence-risk review.",
            "Reviewed warnings and kept user-pasted evidence boundaries visible.",
            "Keeps claims grounded to supplied feedback instead of unsupported market-wide conclusions.",
            ["risk_notes", "data_warnings"],
            warnings=data_warnings,
        )

        current_agent_id = "asset_lock_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Product Asset Lock Agent checking product identity artifacts.")
        video_packet = data.get("video_generation_packet") or {}
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Product Asset Lock Agent completed product identity check.",
            "Checked the video generation packet for product identity and image-reference guidance.",
            "Helps prevent external video drafts from drifting away from the selected product.",
            ["product_asset_lock"],
            warnings=(video_packet.get("risk_notes") or [])[:3] if isinstance(video_packet.get("risk_notes"), list) else [],
        )
        _record_graph_transition_decision(
            run_id,
            "asset_lock_agent",
            "product_identity_validator",
            current_agent_id,
            "proceed",
            "Product asset lock exists; validate product identity.",
        )
        _traverse_agent_graph_edge(run_id, "asset_lock_to_product_identity_validator", "Asset lock ready.")

        product_identity = ((data.get("external_video_tool_handoff") or {}).get("product_asset_lock") or {}).get("product_identity") or ""
        product_category = ((data.get("external_video_tool_handoff") or {}).get("product_asset_lock") or {}).get("product_category") or ""
        AGENT_RUN_STORE.set_graph_node_status(run_id, "product_identity_validator", "running")
        AGENT_RUN_STORE.append_event(
            run_id,
            "node_started",
            "Product Identity Validator started.",
            agent_id="product_identity_validator",
            data={"node_id": "product_identity_validator"},
        )
        if not product_identity or not product_category:
            identity_reason = "Product identity or category is missing; user review is needed before visual prompts."
            _record_graph_validation_result(
                run_id,
                "product_identity_validator",
                "asset_lock_agent",
                "product_asset_lock",
                "failed",
                identity_reason,
                severity="medium",
                rework_target="asset_lock_agent",
            )
            _record_graph_transition_decision(
                run_id,
                "product_identity_validator",
                "asset_lock_agent",
                "product_identity_validator",
                "waiting_for_user",
                identity_reason,
            )
            AGENT_RUN_STORE.set_graph_node_status(run_id, "product_identity_validator", "waiting_for_user")
            AGENT_RUN_STORE.set_waiting_for_user(run_id, True, identity_reason)
            AGENT_RUN_STORE.append_event(
                run_id,
                "waiting_for_user",
                identity_reason,
                agent_id="product_identity_validator",
                data={"node_id": "product_identity_validator"},
            )
            _traverse_agent_graph_edge(run_id, "product_identity_validator_waiting", "Product identity needs user confirmation.")
        else:
            identity_reason = "Product identity validation passed."
            _record_graph_validation_result(
                run_id,
                "product_identity_validator",
                "asset_lock_agent",
                "product_asset_lock",
                "passed",
                identity_reason,
                severity="low",
            )
            _record_graph_transition_decision(
                run_id,
                "product_identity_validator",
                "keyframe_agent",
                "product_identity_validator",
                "validation_passed",
                identity_reason,
                data={"product_identity": product_identity, "product_category": product_category},
            )
            AGENT_RUN_STORE.set_graph_node_status(run_id, "product_identity_validator", "complete")
            AGENT_RUN_STORE.append_event(
                run_id,
                "node_completed",
                "Product Identity Validator completed.",
                agent_id="product_identity_validator",
                data={"node_id": "product_identity_validator"},
            )
            _traverse_agent_graph_edge(run_id, "product_identity_validator_to_keyframe", "Product identity validated.")

        current_agent_id = "keyframe_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Keyframe Agent checking scene/keyframe plan.")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Keyframe Agent completed keyframe planning.",
            "Prepared staged scene guidance for short test clips before longer video export.",
            "Encourages low-risk clip validation before paid or external provider generation.",
            ["keyframe_plan"],
        )
        _record_graph_transition_decision(
            run_id,
            "keyframe_agent",
            "prompt_handoff_agent",
            current_agent_id,
            "proceed",
            "Keyframe plan exists; proceed to prompt handoff.",
        )
        _traverse_agent_graph_edge(run_id, "keyframe_to_prompt_handoff", "Keyframe plan ready.")

        current_agent_id = "prompt_handoff_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Prompt Handoff Agent preparing external tool handoff.")
        handoff = data.get("external_video_tool_handoff") or {}
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Prompt Handoff Agent completed external video prompt handoff.",
            "Prepared manual Gemini/Doubao/export prompts without calling external video APIs.",
            "Keeps external provider work under user control and manual review.",
            ["external_video_tool_handoff"],
            data={"has_handoff": bool(handoff)},
        )
        _record_graph_transition_decision(
            run_id,
            "prompt_handoff_agent",
            "cost_agent",
            current_agent_id,
            "proceed",
            "External video handoff exists; proceed to cost validation.",
        )
        _traverse_agent_graph_edge(run_id, "prompt_handoff_to_cost", "Handoff prompts ready.")

        current_agent_id = "cost_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Cost Agent checking cost boundary.")
        _record_graph_validation_result(
            run_id,
            "cost_agent",
            "route_selector_agent",
            "provider_route",
            "warning",
            "Real external video APIs are disabled; route to manual external tool handoff.",
            severity="medium",
        )
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Cost Agent completed cost boundary check.",
            "Confirmed this async run does not call paid external video APIs.",
            "Cost-incurring provider execution remains gated behind manual/provider job controls.",
            ["cost_boundary"],
            data={"cost_incurred_by_crossgrowth": False},
        )
        _record_graph_transition_decision(
            run_id,
            "cost_agent",
            "route_selector_agent",
            current_agent_id,
            "validation_passed",
            "Cost boundary checked; choose a safe route.",
            data={"external_api_called": False},
        )
        _traverse_agent_graph_edge(run_id, "cost_to_route_selector", "Cost boundary checked.")

        AGENT_RUN_STORE.set_graph_node_status(run_id, "route_selector_agent", "running")
        AGENT_RUN_STORE.append_event(
            run_id,
            "node_started",
            "Route Selector Agent started.",
            agent_id="route_selector_agent",
            data={"node_id": "route_selector_agent"},
        )
        AGENT_RUN_STORE.set_branch_selected(run_id, "manual_external_tool_handoff")
        _record_graph_transition_decision(
            run_id,
            "route_selector_agent",
            "prompt_handoff_agent",
            "route_selector_agent",
            "branch_selected",
            "Real provider APIs are disabled, so the graph selects manual_external_tool_handoff.",
            data={"branch_selected": "manual_external_tool_handoff"},
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "branch_selected",
            "Manual external tool handoff selected because real external API calls are disabled.",
            agent_id="route_selector_agent",
            data={"branch_selected": "manual_external_tool_handoff"},
        )
        AGENT_RUN_STORE.set_graph_node_status(run_id, "route_selector_agent", "complete")
        AGENT_RUN_STORE.append_event(
            run_id,
            "node_completed",
            "Route Selector Agent completed.",
            agent_id="route_selector_agent",
            data={"node_id": "route_selector_agent", "branch_selected": "manual_external_tool_handoff"},
        )
        _traverse_agent_graph_edge(run_id, "route_selector_to_prompt_handoff_fallback", "Manual fallback selected.")
        AGENT_RUN_STORE.set_graph_node_status(run_id, "provider_job_agent", "waiting_for_user")
        AGENT_RUN_STORE.set_graph_node_status(run_id, "experiment_agent", "waiting_for_user")
        AGENT_RUN_STORE.set_waiting_for_user(
            run_id,
            True,
            "Video Job creation and external experiment scoring are waiting for user action after generation.",
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "waiting_for_user",
            "Provider job and experiment nodes are waiting for user action after generation.",
            agent_id="provider_job_agent",
            data={"nodes": ["provider_job_agent", "experiment_agent"]},
        )
        _traverse_agent_graph_edge(run_id, "prompt_handoff_to_finalizer_fallback", "Manual workflow can finalize generated artifacts.")

        current_agent_id = "finalizer_agent"
        _start_agent_run_stage(run_id, current_agent_id, "Finalizer Agent preparing final generated result.")
        final_data = await translate_product_visible_data(data, request.output_language or "en")
        _complete_agent_run_stage(
            run_id,
            current_agent_id,
            "Finalizer Agent completed final result.",
            "Stored the completed Product Mode result on the agent run.",
            "The same dashboard, video job, provider progress, and manual handoff flows can use this result.",
            ["final_product_result", "multi_agent_workflow"],
        )

        AGENT_RUN_STORE.complete_run(run_id, final_data)
        AGENT_RUN_STORE.complete_graph(run_id)
        AGENT_RUN_STORE.append_event(
            run_id,
            "run_completed",
            "Agent run completed.",
            data={
                "has_result": True,
                "external_api_called": False,
                "cost_incurred_by_crossgrowth": False,
            },
        )
        AGENT_RUN_STORE.append_event(
            run_id,
            "graph_completed",
            "Rule-driven agent graph completed.",
            data={"branch_selected": "manual_external_tool_handoff"},
        )
    except Exception as exc:
        error = str(exc or "Agent run failed.")
        if current_agent_id:
            AGENT_RUN_STORE.fail_agent(run_id, current_agent_id, error)
            AGENT_RUN_STORE.append_event(
                run_id,
                "agent_failed",
                "Agent stage failed safely.",
                agent_id=current_agent_id,
                data={"error_type": _error_type(exc)},
            )
        AGENT_RUN_STORE.fail_run(run_id, error)
        AGENT_RUN_STORE.append_event(
            run_id,
            "run_failed",
            "Agent run failed safely.",
            data={"error_type": _error_type(exc), "error": error[:240]},
        )


@app.get("/healthz")
async def healthz(request: Request):
    started = time.perf_counter()
    emit_event(
        "healthz_request",
        request.state.request_id,
        endpoint="/healthz",
        status="ok",
        latency_ms=(time.perf_counter() - started) * 1000,
    )
    return {
        "status": "ok",
        "service": "grounded-ecommerce-creative-agent",
        "stable_baseline": "l9_9_stable",
    }


def _amazon_intake_fallback_message(data_warnings: list[str] | None = None) -> str:
    warnings = set(data_warnings or [])
    if "review_sign_in_required" in warnings:
        return (
            "Product signals were fetched, but Amazon reviews require sign-in. "
            "Paste 3-5 Amazon reviews to improve the creative brief."
        )
    return "Paste 3-5 Amazon reviews or product bullets to improve the creative brief."


def _amazon_empty_review_insights() -> dict:
    return {
        "pain_points": [],
        "buyer_objections": [],
        "use_cases": [],
        "emotional_triggers": [],
        "evidence_quotes": [],
    }


def _amazon_review_insights(review_items: list[dict]) -> dict:
    texts = [
        str(item.get("text") or "").strip()
        for item in review_items
        if str(item.get("text") or "").strip()
    ]
    if not texts:
        return _amazon_empty_review_insights()

    def pick(keywords: tuple[str, ...], fallback: list[str], limit: int = 3) -> list[str]:
        matches = []
        for text in texts:
            lowered = text.lower()
            if any(keyword in lowered for keyword in keywords):
                matches.append(text)
        return _dedupe_amazon_insight_lines(matches or fallback, limit)

    pain_keywords = (
        "leak",
        "crack",
        "broken",
        "watery",
        "thin",
        "flavorless",
        "terrible",
        "problem",
        "issue",
        "hard to",
        "too ",
        "not ",
        "failed",
    )
    objection_keywords = (
        "price",
        "expensive",
        "worth",
        "quality",
        "shipping",
        "delivery",
        "box",
        "bottle",
        "size",
        "received",
        "return",
    )
    use_case_keywords = (
        "salad",
        "vinaigrette",
        "cheese",
        "cooking",
        "use",
        "used",
        "order",
        "favorite",
        "bottle",
    )
    emotion_keywords = (
        "favorite",
        "love",
        "like",
        "good",
        "great",
        "fairly priced",
        "terrible",
        "disappointed",
        "wateriest",
        "flavorless",
    )

    return {
        "pain_points": pick(pain_keywords, texts),
        "buyer_objections": pick(objection_keywords, texts),
        "use_cases": pick(use_case_keywords, texts),
        "emotional_triggers": pick(emotion_keywords, texts),
        "evidence_quotes": _dedupe_amazon_insight_lines(texts, 5),
    }


def _dedupe_amazon_insight_lines(values: list[str], limit: int) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = _clean_description_text(value)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _create_video_generation_job(request: VideoGenerationJobRequest) -> dict:
    packet = dict(request.video_generation_packet or {})
    provider = normalize_video_provider(request.provider or "manual_export") or "manual_export"
    now = _utc_now_iso()
    job_id = f"video_job_{uuid4().hex[:12]}"
    export_formats = video_job_export_formats(packet)
    provider_payload = video_provider_payload_metadata(provider, export_formats, packet)
    provider_payload["cost_estimate"] = estimate_cost_from_video_packet(packet, provider=provider)
    initial_status = normalize_video_job_status(VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT)

    warnings = []
    if not provider_payload["prompt"]:
        warnings.append("missing_generic_video_prompt")
    if not provider_payload["scenes"]:
        warnings.append("missing_video_scenes")

    job = {
        "job_id": job_id,
        "status": initial_status,
        "provider": provider,
        "created_at": now,
        "updated_at": now,
        "output_language": request.output_language,
        "video_generation_packet": packet,
        "provider_payload": provider_payload,
        "result": {
            "result_url": "",
            "preview_url": "",
            "download_url": "",
            "provider_job_id": "",
            "notes": "",
            "message": "Manual export scaffold created. No external video API has been called.",
        },
        "warnings": warnings,
        "history": [
            build_video_job_history_event("created", initial_status, updated_at=now, provider=provider)
        ],
    }
    return VIDEO_JOB_STORE.create(job)


def _update_video_generation_job_result(job: dict, request: VideoGenerationJobResultRequest) -> tuple[dict | None, str]:
    requested_status = _clean_description_text(request.status or "manual_export_completed")
    if requested_status not in VIDEO_GENERATION_RESULT_STATUSES:
        requested_status = VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED
    requested_status = normalize_video_job_status(
        requested_status,
        fallback=VIDEO_JOB_STATUS_MANUAL_EXPORT_COMPLETED,
    )

    current_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    if not can_transition_video_job_status(current_status, requested_status):
        return None, f"invalid video job status transition: {current_status} -> {requested_status}"

    result = dict(job.get("result") or {})
    result.update(
        {
            "result_url": _clean_description_text(request.result_url),
            "preview_url": _clean_description_text(request.preview_url),
            "download_url": _clean_description_text(request.download_url),
            "provider_job_id": _clean_description_text(request.provider_job_id),
            "notes": _clean_description_text(request.notes),
            "message": "External/manual video result recorded." if requested_status != "failed" else "External/manual video generation failed.",
        }
    )

    job["status"] = requested_status
    now = _utc_now_iso()
    job["updated_at"] = now
    job["result"] = result

    history = list(job.get("history") or [])
    if current_status != requested_status:
        history.append(
            build_video_job_history_event(
                "status_changed",
                requested_status,
                updated_at=now,
                from_status=current_status,
                to_status=requested_status,
            )
        )
    history.append(
        build_video_job_history_event(
            "result_update",
            requested_status,
            updated_at=now,
            provider_job_id=result.get("provider_job_id", ""),
            has_result_url=bool(result.get("result_url")),
        )
    )
    job["history"] = history
    return job, ""


def _validate_video_experiment_scores(request: VideoGenerationExperimentRequest) -> str:
    for field_name in [
        "product_consistency_score",
        "storyboard_following_score",
        "visual_quality_score",
        "ad_readiness_score",
        "overall_score",
    ]:
        value = getattr(request, field_name)
        if value is None:
            continue
        if value < 1 or value > 5:
            return f"{field_name} must be between 1 and 5"
    return ""


def _is_second_video_experiment_request(request: VideoGenerationExperimentRequest) -> bool:
    try:
        round_number = int(getattr(request, "experiment_round", 1) or 1)
    except (TypeError, ValueError):
        round_number = 1
    return round_number == 2 or bool(getattr(request, "compare_to_previous", False))


def _experiment_triggered_rework_run_id(experiment: dict) -> str:
    decision = experiment.get("agent_feedback_decision") if isinstance(experiment.get("agent_feedback_decision"), dict) else {}
    return (
        str(experiment.get("triggered_rework_run_id") or "").strip()
        or str(decision.get("triggered_rework_run_id") or "").strip()
    )


def _find_second_experiment_baseline(
    experiments: list[dict],
    request: VideoGenerationExperimentRequest,
) -> dict:
    baseline_id = str(getattr(request, "baseline_experiment_id", "") or "").strip()
    if baseline_id:
        for experiment in experiments:
            if str(experiment.get("experiment_id") or "") == baseline_id:
                return experiment

    linked_rework_run_id = str(getattr(request, "linked_rework_run_id", "") or "").strip()
    if linked_rework_run_id:
        for experiment in reversed(experiments):
            if _experiment_triggered_rework_run_id(experiment) == linked_rework_run_id:
                return experiment

    for experiment in reversed(experiments):
        decision = experiment.get("agent_feedback_decision") if isinstance(experiment.get("agent_feedback_decision"), dict) else {}
        if decision.get("has_feedback") is True:
            return experiment

    return {}


def _rework_run_for_second_experiment(request: VideoGenerationExperimentRequest, baseline: dict) -> dict:
    linked_rework_run_id = (
        str(getattr(request, "linked_rework_run_id", "") or "").strip()
        or _experiment_triggered_rework_run_id(baseline)
    )
    if not linked_rework_run_id:
        return {}
    return AGENT_RUN_STORE.get(linked_rework_run_id) or {}


def _record_external_video_experiment(job: dict, request: VideoGenerationExperimentRequest) -> tuple[dict | None, str]:
    score_error = _validate_video_experiment_scores(request)
    if score_error:
        return None, score_error

    now = _utc_now_iso()
    existing_experiments = list(job.get("external_video_experiments") or job.get("external_experiments") or [])
    is_second_experiment = _is_second_video_experiment_request(request)
    experiment = {
        "experiment_id": f"video_experiment_{uuid4().hex[:12]}",
        "tool_name": _clean_description_text(request.tool_name or "other"),
        "prompt_type": _clean_description_text(request.prompt_type or "custom"),
        "result_url": _clean_description_text(request.result_url),
        "preview_url": _clean_description_text(request.preview_url),
        "prompt_used": _safe_evidence_quote(request.prompt_used, limit=4000),
        "estimated_cost_usd": request.estimated_cost_usd,
        "actual_cost_usd": request.actual_cost_usd,
        "product_consistency_score": request.product_consistency_score,
        "storyboard_following_score": request.storyboard_following_score,
        "visual_quality_score": request.visual_quality_score,
        "ad_readiness_score": request.ad_readiness_score,
        "overall_score": request.overall_score,
        "notes": _clean_description_text(request.notes),
        "failure_reason": _clean_description_text(request.failure_reason),
        "created_at": now,
        "external_api_called": False,
        "cost_incurred_by_crossgrowth": False,
    }
    baseline_experiment_id = _clean_description_text(getattr(request, "baseline_experiment_id", ""))
    linked_rework_run_id = _clean_description_text(getattr(request, "linked_rework_run_id", ""))
    prompt_source = _clean_description_text(getattr(request, "prompt_source", ""))
    if baseline_experiment_id:
        experiment["baseline_experiment_id"] = baseline_experiment_id
    if linked_rework_run_id:
        experiment["linked_rework_run_id"] = linked_rework_run_id
    if prompt_source:
        experiment["prompt_source"] = prompt_source
    if is_second_experiment:
        experiment["experiment_round"] = 2
        experiment["compare_to_previous"] = True
    feedback_decision = build_experiment_feedback_decision(experiment, job)
    original_generation_data = {
        "video_generation_packet": job.get("video_generation_packet") or {},
        "provider_payload": job.get("provider_payload") or {},
        "source_generation": job.get("source_generation") or {},
        "external_video_tool_handoff": job.get("external_video_tool_handoff") or {},
    }
    rework_run = None
    if not is_second_experiment:
        rework_run = trigger_experiment_rework_run(
            str(job.get("job_id") or ""),
            feedback_decision,
            original_generation_data=original_generation_data,
            experiment=experiment,
        )
    if rework_run:
        AGENT_RUN_STORE.create(rework_run)
        feedback_decision = dict(feedback_decision)
        feedback_decision["triggered_rework_run_id"] = rework_run["run_id"]
        feedback_decision["triggered_rework_poll_url"] = f"/api/v1/agent-runs/{rework_run['run_id']}"
        feedback_decision["triggered_rework_events_url"] = f"/api/v1/agent-runs/{rework_run['run_id']}/events"
        if (rework_run.get("result") or {}).get("revised_keyframe_plan"):
            feedback_decision["triggered_rework_result_type"] = "revised_keyframe_plan"
            experiment["triggered_rework_result_type"] = "revised_keyframe_plan"
        if (rework_run.get("result") or {}).get("revised_external_video_handoff"):
            feedback_decision["triggered_rework_next_artifact_type"] = "revised_external_video_handoff"
            experiment["triggered_rework_next_artifact_type"] = "revised_external_video_handoff"
    experiment["agent_feedback_decision"] = feedback_decision

    second_comparison: dict = {}
    comparison_decision_gate: dict = {}
    artifact_lineage_summary: dict = {}
    controlled_provider_handoff_checklist: dict = {}
    demo_ready_run_summary: dict = {}
    if is_second_experiment:
        baseline_experiment = _find_second_experiment_baseline(existing_experiments, request)
        baseline_decision = (
            baseline_experiment.get("agent_feedback_decision")
            if isinstance(baseline_experiment.get("agent_feedback_decision"), dict)
            else {}
        )
        comparison_rework_run = _rework_run_for_second_experiment(request, baseline_experiment)
        if baseline_experiment:
            second_comparison = build_second_experiment_comparison(
                baseline_experiment,
                experiment,
                baseline_decision,
                comparison_rework_run,
            )
            if prompt_source and not second_comparison.get("prompt_source"):
                second_comparison["prompt_source"] = prompt_source
            experiment["second_experiment_comparison"] = second_comparison
            comparison_decision_gate = build_experiment_comparison_decision_gate(
                second_comparison,
                job=job,
                baseline_experiment=baseline_experiment,
                second_experiment=experiment,
            )
            experiment["experiment_comparison_decision_gate"] = comparison_decision_gate
            artifact_lineage_summary = build_lightweight_artifact_lineage(
                job,
                baseline_experiment=baseline_experiment,
                second_experiment=experiment,
                rework_run=comparison_rework_run,
                comparison=second_comparison,
                decision_gate=comparison_decision_gate,
            )
            experiment["artifact_lineage"] = artifact_lineage_summary
            if comparison_decision_gate.get("should_proceed_to_provider_test") is True:
                controlled_provider_handoff_checklist = build_controlled_provider_handoff_checklist(
                    job,
                    comparison_decision_gate,
                    rework_run=comparison_rework_run,
                    comparison=second_comparison,
                )
                demo_ready_run_summary = build_demo_ready_run_summary(
                    job,
                    baseline_experiment,
                    experiment,
                    comparison_rework_run,
                    second_comparison,
                    comparison_decision_gate,
                    artifact_lineage_summary,
                    controlled_provider_handoff_checklist,
                )
                experiment["controlled_provider_handoff_checklist"] = controlled_provider_handoff_checklist
                experiment["demo_ready_run_summary"] = demo_ready_run_summary

    experiments = list(existing_experiments)
    experiments.append(experiment)
    job["external_video_experiments"] = experiments
    job["external_experiments"] = experiments
    job["latest_agent_feedback_decision"] = feedback_decision
    if second_comparison:
        job["latest_second_experiment_comparison"] = second_comparison
    if comparison_decision_gate:
        job["latest_experiment_comparison_decision_gate"] = comparison_decision_gate
    if artifact_lineage_summary:
        job["latest_artifact_lineage"] = artifact_lineage_summary
    if controlled_provider_handoff_checklist:
        job["latest_controlled_provider_handoff_checklist"] = controlled_provider_handoff_checklist
    if demo_ready_run_summary:
        job["latest_demo_ready_run_summary"] = demo_ready_run_summary
    if rework_run:
        job["latest_experiment_rework_run_id"] = rework_run["run_id"]
        rework_run_ids = list(job.get("experiment_rework_run_ids") or [])
        rework_run_ids.append(rework_run["run_id"])
        job["experiment_rework_run_ids"] = rework_run_ids[-10:]
        if (rework_run.get("result") or {}).get("revised_keyframe_plan"):
            job["latest_rework_artifact_type"] = "revised_keyframe_plan"
        if (rework_run.get("result") or {}).get("revised_external_video_handoff"):
            job["latest_rework_next_artifact_type"] = "revised_external_video_handoff"
    existing_feedback = job.get("agent_graph_feedback") if isinstance(job.get("agent_graph_feedback"), dict) else {}
    feedback_decisions = list(existing_feedback.get("decisions") or [])
    feedback_decisions.append(feedback_decision)
    job["agent_graph_feedback"] = {
        "feedback_version": "experiment_feedback_loop_v1",
        "decisions": feedback_decisions[-5:],
    }
    if rework_run:
        job["agent_graph_feedback"]["latest_rework_run_id"] = rework_run["run_id"]
        job["agent_graph_feedback"]["rework_run_ids"] = list(job.get("experiment_rework_run_ids") or [])
        if (rework_run.get("result") or {}).get("revised_keyframe_plan"):
            job["agent_graph_feedback"]["latest_rework_artifact_type"] = "revised_keyframe_plan"
        if (rework_run.get("result") or {}).get("revised_external_video_handoff"):
            job["agent_graph_feedback"]["latest_rework_next_artifact_type"] = "revised_external_video_handoff"
    if second_comparison:
        job["agent_graph_feedback"]["latest_second_experiment_comparison"] = second_comparison
    if comparison_decision_gate:
        job["agent_graph_feedback"]["latest_experiment_comparison_decision_gate"] = comparison_decision_gate
    if artifact_lineage_summary:
        job["agent_graph_feedback"]["latest_artifact_lineage"] = artifact_lineage_summary
    if controlled_provider_handoff_checklist:
        job["agent_graph_feedback"][
            "latest_controlled_provider_handoff_checklist"
        ] = controlled_provider_handoff_checklist
    if demo_ready_run_summary:
        job["agent_graph_feedback"]["latest_demo_ready_run_summary"] = demo_ready_run_summary
    job["updated_at"] = now

    history = list(job.get("history") or [])
    job_status = normalize_video_job_status(job.get("status", ""), fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT)
    history.append(
        build_video_job_history_event(
            "external_video_experiment_recorded",
            job_status,
            updated_at=now,
            experiment_id=experiment["experiment_id"],
            tool_name=experiment["tool_name"],
            prompt_type=experiment["prompt_type"],
            has_result_url=bool(experiment["result_url"]),
            feedback_decision_type=feedback_decision["decision_type"],
            feedback_target_agent_id=feedback_decision.get("target_agent_id", ""),
            feedback_rework_run_id=feedback_decision.get("triggered_rework_run_id", ""),
        )
    )
    history.append(
        build_video_job_history_event(
            "experiment_feedback_recorded",
            job_status,
            updated_at=now,
            experiment_id=experiment["experiment_id"],
            tool_name=experiment["tool_name"],
            prompt_type=experiment["prompt_type"],
            has_result_url=bool(experiment["result_url"]),
            feedback_decision_type=feedback_decision["decision_type"],
            feedback_has_feedback=bool(feedback_decision.get("has_feedback")),
            feedback_target_agent_id=feedback_decision.get("target_agent_id", ""),
            feedback_rework_run_id=feedback_decision.get("triggered_rework_run_id", ""),
        )
    )
    if rework_run and feedback_decision.get("has_feedback"):
        history.append(
            build_video_job_history_event(
                "experiment_feedback_rework_requested",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                source_agent_id=feedback_decision.get("source_agent_id", "experiment_agent"),
                target_agent_id=feedback_decision.get("target_agent_id", ""),
                secondary_target_agent_id=feedback_decision.get("secondary_target_agent_id", ""),
                issue_type=feedback_decision.get("issue_type", ""),
                severity=feedback_decision.get("severity", ""),
                rework_run_id=feedback_decision.get("triggered_rework_run_id", ""),
            )
        )
    if second_comparison:
        history.append(
            build_video_job_history_event(
                "second_external_experiment_recorded",
                job_status,
                updated_at=now,
                baseline_experiment_id=second_comparison.get("baseline_experiment_id", ""),
                second_experiment_id=second_comparison.get("second_experiment_id", ""),
                linked_rework_run_id=second_comparison.get("linked_rework_run_id", ""),
                comparison_status=second_comparison.get("status", ""),
            )
        )
        history.append(
            build_video_job_history_event(
                second_comparison.get("decision_type", "second_experiment_no_change"),
                job_status,
                updated_at=now,
                baseline_experiment_id=second_comparison.get("baseline_experiment_id", ""),
                second_experiment_id=second_comparison.get("second_experiment_id", ""),
                prompt_source=second_comparison.get("prompt_source", ""),
                primary_metric=second_comparison.get("primary_metric", ""),
            )
        )
    if comparison_decision_gate:
        history.append(
            build_video_job_history_event(
                "experiment_comparison_decision_gate_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                gate_version=comparison_decision_gate.get("gate_version", ""),
                comparison_status=comparison_decision_gate.get("comparison_status", ""),
                decision_type=comparison_decision_gate.get("decision_type", ""),
                recommended_route=comparison_decision_gate.get("recommended_route", ""),
            )
        )
        history.append(
            build_video_job_history_event(
                f"experiment_gate_{comparison_decision_gate.get('decision_type', 'manual_review_required')}",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                next_agent_id=comparison_decision_gate.get("next_agent_id", ""),
                secondary_next_agent_id=comparison_decision_gate.get("secondary_next_agent_id", ""),
                requires_human_approval=bool(comparison_decision_gate.get("requires_human_approval")),
                should_trigger_new_rework=bool(comparison_decision_gate.get("should_trigger_new_rework")),
                should_proceed_to_provider_test=bool(
                    comparison_decision_gate.get("should_proceed_to_provider_test")
                ),
            )
        )
    if artifact_lineage_summary:
        history.append(
            build_video_job_history_event(
                "artifact_lineage_summary_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                lineage_version=artifact_lineage_summary.get("lineage_version", ""),
                rework_run_id=artifact_lineage_summary.get("linked_rework_run_id", ""),
                is_linear_workflow=False,
            )
        )
    if controlled_provider_handoff_checklist:
        history.append(
            build_video_job_history_event(
                "controlled_provider_handoff_checklist_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                checklist_version=controlled_provider_handoff_checklist.get("checklist_version", ""),
                provider_mode=controlled_provider_handoff_checklist.get("provider_mode", ""),
                human_approval_required=True,
            )
        )
    if demo_ready_run_summary:
        history.append(
            build_video_job_history_event(
                "demo_ready_run_summary_created",
                job_status,
                updated_at=now,
                experiment_id=experiment["experiment_id"],
                summary_version=demo_ready_run_summary.get("summary_version", ""),
                summary_type=demo_ready_run_summary.get("summary_type", ""),
                is_linear_workflow=False,
            )
        )
    job["history"] = history
    return job, ""


def _summarize_video_generation_job(job: dict) -> dict:
    provider_payload = job.get("provider_payload") or {}
    result = job.get("result") or {}
    source_generation = job.get("source_generation") or {}
    return {
        "job_id": job.get("job_id", ""),
        "status": job.get("status", ""),
        "provider": job.get("provider", ""),
        "provider_label": provider_payload.get("provider_label", ""),
        "selected_export_key": provider_payload.get("selected_export_key", ""),
        "created_at": job.get("created_at", ""),
        "updated_at": job.get("updated_at", ""),
        "output_language": job.get("output_language", ""),
        "has_result_url": bool(result.get("result_url")),
        "result_url": result.get("result_url", ""),
        "preview_url": result.get("preview_url", ""),
        "source_hook": source_generation.get("hook", ""),
        "source_risk_level": source_generation.get("risk_level", ""),
        "warning_count": len(job.get("warnings") or []),
        "experiment_count": len(job.get("external_video_experiments") or []),
    }


def _append_video_job_status_event(
    history: list[dict],
    current_status: str,
    next_status: str,
    now: str,
) -> None:
    if current_status != next_status:
        history.append(
            build_video_job_history_event(
                "status_changed",
                next_status,
                updated_at=now,
                from_status=current_status,
                to_status=next_status,
            )
        )


def _submit_video_generation_provider_job(job: dict, request: VideoGenerationProviderSubmitRequest) -> tuple[dict | None, str]:
    provider = normalize_video_provider(job.get("provider", ""))
    if not supports_provider_polling(provider):
        return None, "provider does not support polling scaffold"

    current_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    next_status = VIDEO_JOB_STATUS_QUEUED
    if not can_transition_video_job_status(current_status, next_status):
        return None, f"invalid video job status transition: {current_status} -> {next_status}"

    now = _utc_now_iso()
    runtime = build_provider_runtime(
        provider,
        provider_job_id=_clean_description_text(request.provider_job_id),
        notes=_clean_description_text(request.notes),
        now=now,
    )
    job["provider_runtime"] = runtime
    job["status"] = next_status
    job["updated_at"] = now

    result = dict(job.get("result") or {})
    result["provider_job_id"] = runtime.get("provider_job_id", "")
    result["message"] = "Provider polling scaffold submitted. No external video API has been called."
    if request.notes:
        result["notes"] = _clean_description_text(request.notes)
    job["result"] = result

    history = list(job.get("history") or [])
    history.extend(provider_submit_history_events(provider, next_status, now=now))
    _append_video_job_status_event(history, current_status, next_status, now)
    job["history"] = history
    return job, ""


def _poll_video_generation_provider_job(job: dict, request: VideoGenerationProviderPollRequest) -> tuple[dict | None, str]:
    provider = normalize_video_provider(job.get("provider", ""))
    runtime = dict(job.get("provider_runtime") or {})
    if not runtime.get("provider_job_id"):
        return None, "provider job has not been submitted"

    current_status = normalize_video_job_status(
        job.get("status", ""),
        fallback=VIDEO_JOB_STATUS_READY_FOR_MANUAL_EXPORT,
    )
    requested_provider_status = _clean_description_text(request.provider_status)
    next_status = next_simulated_provider_status(current_status, requested_provider_status)
    if next_status not in {VIDEO_JOB_STATUS_PROCESSING, VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY, VIDEO_JOB_STATUS_FAILED}:
        next_status = VIDEO_JOB_STATUS_PROCESSING
    if not can_transition_video_job_status(current_status, next_status):
        return None, f"invalid video job status transition: {current_status} -> {next_status}"

    now = _utc_now_iso()
    runtime = build_provider_poll_runtime(
        runtime,
        next_status,
        error_message=_clean_description_text(request.error_message),
        notes=_clean_description_text(request.notes),
        now=now,
    )
    job["provider_runtime"] = runtime
    job["status"] = next_status
    job["updated_at"] = now

    result = dict(job.get("result") or {})
    result["provider_job_id"] = runtime.get("provider_job_id", "")
    result["message"] = "Provider polling scaffold checked. No external video API has been called."
    if next_status == VIDEO_JOB_STATUS_EXTERNAL_RESULT_READY:
        result.update(
            {
                "result_url": _clean_description_text(request.result_url),
                "preview_url": _clean_description_text(request.preview_url),
                "download_url": _clean_description_text(request.download_url),
                "notes": _clean_description_text(request.notes),
                "message": "Simulated provider result recorded.",
            }
        )
    elif next_status == VIDEO_JOB_STATUS_FAILED:
        result["notes"] = _clean_description_text(request.notes)
        result["error_message"] = _clean_description_text(request.error_message)
        result["message"] = "Simulated provider polling marked the job failed."
    job["result"] = result

    history = list(job.get("history") or [])
    _append_video_job_status_event(history, current_status, next_status, now)
    history.append(provider_poll_history_event(provider, next_status, runtime, now=now))
    job["history"] = history
    return job, ""


@app.get("/api/v1/video-generation/providers", response_model=VideoGenerationProvidersResponse)
async def list_video_generation_providers(http_request: Request):
    return {
        "status": "success",
        "providers": video_provider_catalog(),
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/video-generation/providers/{provider}/plan", response_model=VideoGenerationProviderPlanResponse)
async def get_video_generation_provider_plan(provider: str, http_request: Request):
    request_id = http_request.state.request_id
    provider_name = normalize_video_provider(provider)
    plan = video_provider_plan(provider)
    if not provider_name or not plan:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation provider not found",
                "request_id": request_id,
            },
        )
    plan.update(provider_plan_integration_metadata(provider_name))
    return {
        "status": "success",
        "provider": provider_name,
        "plan": plan,
        "request_id": request_id,
    }


@app.get("/api/v1/video-generation/cost/catalog", response_model=VideoGenerationCostCatalogResponse)
async def get_video_generation_cost_catalog(http_request: Request):
    return {
        "status": "success",
        "catalog": video_provider_cost_catalog(),
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/video-generation/cost/estimate", response_model=VideoGenerationCostEstimateResponse)
async def estimate_video_generation_provider_cost(request: VideoGenerationCostEstimateRequest, http_request: Request):
    return {
        "status": "success",
        "estimate": estimate_video_generation_cost(
            provider=request.provider,
            model=request.model,
            duration_seconds=request.duration_seconds,
            clip_count=request.clip_count,
            retry_count=request.retry_count,
            budget_usd=request.budget_usd,
        ),
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/video-generation/storage/status", response_model=VideoGenerationStorageStatusResponse)
async def get_video_generation_storage_status(http_request: Request):
    return {
        "status": "success",
        "storage": video_job_storage_diagnostics(VIDEO_JOB_STORE),
        "request_id": http_request.state.request_id,
    }


def _video_generation_packet_from_generation_data(generation_data: dict) -> dict:
    if not isinstance(generation_data, dict):
        return {}
    packet = generation_data.get("video_generation_packet") or {}
    if not isinstance(packet, dict):
        return {}
    return packet


def _video_generation_source_summary(generation_data: dict) -> dict:
    if not isinstance(generation_data, dict):
        return {}

    assets = generation_data.get("assets") or {}
    script = assets.get("tiktok_script") if isinstance(assets, dict) else {}
    storyboard = assets.get("storyboard") if isinstance(assets, dict) else {}
    evaluation = generation_data.get("evaluation") or {}
    agent_trace = generation_data.get("agent_trace") or {}

    if not isinstance(script, dict):
        script = {}
    if not isinstance(storyboard, dict):
        storyboard = {}
    if not isinstance(evaluation, dict):
        evaluation = {}
    if not isinstance(agent_trace, dict):
        agent_trace = {}

    scenes = storyboard.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    return {
        "hook": script.get("hook", ""),
        "cta": script.get("cta", ""),
        "storyboard_scene_count": len(scenes),
        "risk_level": evaluation.get("risk_level", ""),
        "is_grounded": bool(evaluation.get("is_grounded", False)),
        "agent_trace_version": agent_trace.get("trace_version", ""),
    }


@app.get("/api/v1/video-generation/jobs", response_model=VideoGenerationJobListResponse)
async def list_video_generation_jobs(http_request: Request, limit: int = 20):
    safe_limit = max(1, min(int(limit or 20), 50))
    jobs = VIDEO_JOB_STORE.list(safe_limit)
    summarized = [_summarize_video_generation_job(job) for job in jobs]
    return {
        "status": "success",
        "jobs": summarized,
        "job_count": len(summarized),
        "limit": safe_limit,
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/video-generation/jobs", response_model=VideoGenerationJobResponse)
async def create_video_generation_job(request: VideoGenerationJobRequest, http_request: Request):
    request_id = http_request.state.request_id
    packet = request.video_generation_packet or {}

    if packet.get("packet_version") != "video_generation_v1":
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "video_generation_packet with packet_version=video_generation_v1 is required.",
                "request_id": request_id,
            },
        )

    if not normalize_video_provider(request.provider or "manual_export"):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "unsupported video generation provider",
                "supported_providers": supported_video_provider_names(),
                "request_id": request_id,
            },
        )

    job = _create_video_generation_job(request)
    emit_event(
        "video_generation_job_created",
        request_id,
        endpoint="/api/v1/video-generation/jobs",
        status="success",
        job_id=job["job_id"],
        provider=job["provider"],
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/provider-submit", response_model=VideoGenerationJobStatusResponse)
async def submit_video_generation_provider_job(
    job_id: str,
    request: VideoGenerationProviderSubmitRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, submit_error = _submit_video_generation_provider_job(job, request)
    if submit_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": submit_error,
                "request_id": request_id,
            },
        )

    job = VIDEO_JOB_STORE.update(job_id, job)
    emit_event(
        "video_generation_provider_submitted",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/provider-submit",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/provider-poll", response_model=VideoGenerationJobStatusResponse)
async def poll_video_generation_provider_job(
    job_id: str,
    request: VideoGenerationProviderPollRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, poll_error = _poll_video_generation_provider_job(job, request)
    if poll_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": poll_error,
                "request_id": request_id,
            },
        )

    job = VIDEO_JOB_STORE.update(job_id, job)
    emit_event(
        "video_generation_provider_polled",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/provider-poll",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/result", response_model=VideoGenerationJobStatusResponse)
async def update_video_generation_job_result(
    job_id: str,
    request: VideoGenerationJobResultRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, transition_error = _update_video_generation_job_result(job, request)
    if transition_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": transition_error,
                "request_id": request_id,
            },
        )
    job = VIDEO_JOB_STORE.update(job_id, job)

    emit_event(
        "video_generation_job_result_updated",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/result",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )

    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/{job_id}/experiments", response_model=VideoGenerationJobStatusResponse)
async def record_external_video_experiment(
    job_id: str,
    request: VideoGenerationExperimentRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    job, experiment_error = _record_external_video_experiment(job, request)
    if experiment_error:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": experiment_error,
                "request_id": request_id,
            },
        )

    job = VIDEO_JOB_STORE.update(job_id, job)
    emit_event(
        "external_video_experiment_recorded",
        request_id,
        endpoint="/api/v1/video-generation/jobs/{job_id}/experiments",
        status="success",
        job_id=job_id,
        job_status=job["status"],
        provider=job.get("provider", ""),
    )
    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/video-generation/jobs/from-generation", response_model=VideoGenerationJobResponse)
async def create_video_generation_job_from_generation(
    request: VideoGenerationFromGenerationRequest,
    http_request: Request,
):
    request_id = http_request.state.request_id
    generation_data = request.generation_data or {}
    packet = _video_generation_packet_from_generation_data(generation_data)

    if packet.get("packet_version") != "video_generation_v1":
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "generation_data.video_generation_packet with packet_version=video_generation_v1 is required.",
                "request_id": request_id,
            },
        )

    if not normalize_video_provider(request.provider or "manual_export"):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "unsupported video generation provider",
                "supported_providers": supported_video_provider_names(),
                "request_id": request_id,
            },
        )

    job_request = VideoGenerationJobRequest(
        video_generation_packet=packet,
        provider=request.provider,
        output_language=request.output_language,
    )
    job = _create_video_generation_job(job_request)
    job["source_generation"] = _video_generation_source_summary(generation_data)
    handoff = generation_data.get("external_video_tool_handoff") if isinstance(generation_data.get("external_video_tool_handoff"), dict) else {}
    if handoff:
        job["external_video_tool_handoff"] = handoff
    job["updated_at"] = _utc_now_iso()
    job = VIDEO_JOB_STORE.update(job["job_id"], job)

    emit_event(
        "video_generation_job_created_from_generation",
        request_id,
        endpoint="/api/v1/video-generation/jobs/from-generation",
        status="success",
        job_id=job["job_id"],
        provider=job["provider"],
    )

    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.get("/api/v1/video-generation/jobs/{job_id}", response_model=VideoGenerationJobStatusResponse)
async def get_video_generation_job(job_id: str, http_request: Request):
    request_id = http_request.state.request_id
    job = VIDEO_JOB_STORE.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "video generation job not found",
                "request_id": request_id,
            },
        )

    return {
        "status": "success",
        "job": job,
        "request_id": request_id,
    }


@app.post("/api/v1/amazon-intake", response_model=AmazonIntakeResponse)
async def amazon_intake(request: AmazonIntakeRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    intake = normalize_amazon_product_url(request.url)

    emit_event(
        "amazon_intake_start",
        request_id,
        endpoint="/api/v1/amazon-intake",
        status="started",
        product_category=request.product_category,
    )

    base_data = {
        "input_url": request.url,
        "is_supported": intake.is_supported,
        "asin": intake.asin,
        "normalized_url": intake.normalized_url,
        "provider_status": "unsupported" if not intake.is_supported else "pending",
        "source_confidence": 0.0,
        "product_title": "",
        "rating": "",
        "review_count": "",
        "price": "",
        "category_hint": "",
        "bullet_points": [],
        "evidence_preview": [],
        "review_items": [],
        "review_insights": _amazon_empty_review_insights(),
        "data_warnings": [],
        "fallback_required": True,
        "fallback_message": _amazon_intake_fallback_message(),
        "error": "",
        "metadata": {},
    }

    if not intake.is_supported:
        base_data["data_warnings"] = ["unsupported_amazon_url", intake.reason]
        base_data["metadata"] = {
            "intake_status": "unsupported",
            "intake_reason": intake.reason,
            "intake_source_type": intake.source_type,
        }
        emit_event(
            "amazon_intake_complete",
            request_id,
            endpoint="/api/v1/amazon-intake",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category,
            fallback_required=True,
        )
        return {
            "status": "success",
            "data": base_data,
            "request_id": request_id,
        }

    try:
        evidence = source_probe_registry.fetch(
            "amazon_review_api",
            intake.normalized_url,
            request.product_category,
        )
        metadata = dict(evidence.metadata or {})
        provider_status = _probe_status_from_evidence(evidence)
        fallback_required = not (provider_status == "success" and evidence.confidence >= 0.70)
        data_warnings = list(evidence.data_warnings or [])
        if "review_sign_in_required" in data_warnings:
            fallback_required = True
        review_items = [
            {
                "text": review.text,
                "source": review.source or evidence.source_type,
                "rating": review.rating,
                "date": review.date,
                "title": review.title,
            }
            for review in list(evidence.reviews or [])[:6]
        ]

        base_data.update(
            {
                "provider_status": provider_status,
                "source_confidence": evidence.confidence,
                "product_title": metadata.get("product_title", ""),
                "rating": metadata.get("rating", ""),
                "review_count": metadata.get("review_count", ""),
                "price": metadata.get("price", ""),
                "category_hint": metadata.get("category_hint", ""),
                "bullet_points": list(metadata.get("bullet_points") or []),
                "evidence_preview": list(evidence.evidence_quotes[:3]),
                "review_items": review_items,
                "review_insights": _amazon_review_insights(review_items),
                "data_warnings": data_warnings,
                "fallback_required": fallback_required,
                "fallback_message": _amazon_intake_fallback_message(data_warnings) if fallback_required else "",
                "error": metadata.get("error", ""),
                "metadata": {
                    **metadata,
                    "source_type": evidence.source_type,
                    "data_warnings": data_warnings,
                },
            }
        )

        emit_event(
            "amazon_intake_complete",
            request_id,
            endpoint="/api/v1/amazon-intake",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category,
            fallback_required=fallback_required,
        )
        return {
            "status": "success",
            "data": base_data,
            "request_id": request_id,
        }
    except Exception as exc:
        base_data.update(
            {
                "provider_status": "error",
                "data_warnings": ["amazon_fetch_error"],
                "fallback_required": True,
                "fallback_message": _amazon_intake_fallback_message(),
                "error": str(exc),
                "metadata": {
                    "intake_status": "supported",
                    "asin": intake.asin,
                    "normalized_url": intake.normalized_url,
                    "error_type": "amazon_fetch_error",
                },
            }
        )
        emit_event(
            "amazon_intake_complete",
            request_id,
            endpoint="/api/v1/amazon-intake",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category,
            fallback_required=True,
        )
        return {
            "status": "success",
            "data": base_data,
            "request_id": request_id,
        }


@app.post("/api/v1/generate-copilot", response_model=GenerateCopilotResponse)
async def generate_copilot_flow(request: GrowthRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    product_category_hint = _safe_product_category_hint(request.url)
    emit_event(
        "generate_copilot_start",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="started",
        product_category=product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )
    emit_event(
        "generate_copilot_after_request_parse",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )

    initial_state = {
        "env_state": {"asin_url": request.url, "business_goal": request.goal},
        "cognitive_state": {},
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": {},
        "revision_count": 0,
        "next_nodes": [],
    }

    emit_event(
        "generate_copilot_before_workflow",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="started",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )
    try:
        final_state = await copilot_engine.ainvoke(initial_state)
    except Exception as exc:
        error_type = _error_type(exc)
        emit_event(
            "generate_copilot_error",
            request_id,
            endpoint="/api/v1/generate-copilot",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=product_category_hint,
            goal=request.goal,
            error_type=error_type,
            output_language=output_language,
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": "generate-copilot workflow failed safely. Please retry after the service is warm.",
                "error_type": error_type,
                "request_id": request_id,
            },
        )

    env_state = final_state.get("env_state", {})
    emit_event(
        "generate_copilot_after_workflow",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category") or product_category_hint,
        goal=request.goal,
        output_language=output_language,
    )
    cog_state = final_state.get("cognitive_state", {})
    exec_state = final_state.get("execution_state", {})
    world_metrics = final_state.get("world_metrics", {})
    strategy_data = cog_state.get("strategy", {})
    profile = cog_state.get("profile", {})
    painpoint = profile.get("painpoint", {})
    audience = profile.get("audience", {})
    dopamine = profile.get("dopamine", {})
    storyboard_data = exec_state.get("storyboard", {})
    scenes = storyboard_data.get("scenes", [])

    ui_strategy = {
        "core_hook_strategy": (
            f"Identity attack:\n{strategy_data.get('identity_attack', '')}\n\n"
            f"Status desire:\n{strategy_data.get('status_desire', '')}\n\n"
            f"Evidence:\n" + "\n".join(strategy_data.get("evidence_basis", []))
        ),
        "emotional_trigger": (
            f"Future-self gap:\n{strategy_data.get('future_self_gap', '')}\n\n"
            f"Conversion mechanism:\n{strategy_data.get('conversion_mechanism', '')}\n\n"
            f"CTA logic:\n{strategy_data.get('cta_logic', '')}"
        ),
    }

    hook_text = "Scene graph was not generated."
    cta_text = "Conversion scene was not generated."
    if scenes and isinstance(scenes, list):
        first_scene = scenes[0]
        last_scene = scenes[-1]
        hook_text = (
            f"0-{first_scene.get('duration_sec', 0)}s | {first_scene.get('scene_goal', '')}\n"
            f"Visual: {first_scene.get('visual_description', '')}\n"
            f"Narration: {first_scene.get('narration', '')}\n"
            f"Text: {first_scene.get('on_screen_text', '')}\n"
            f"Retention: {first_scene.get('retention_reason', '')}"
        )
        cta_text = (
            f"Final scene | {last_scene.get('scene_goal', '')}\n"
            f"Visual: {last_scene.get('visual_description', '')}\n"
            f"Narration: {last_scene.get('narration', '')}\n"
            f"Painpoint: {last_scene.get('linked_painpoint', '')}"
        )

    retention_score = world_metrics.get("retention_3s", 0.0)
    if retention_score < 0.50:
        risk_level = "high"
    elif retention_score < 0.70:
        risk_level = "medium"
    else:
        risk_level = "low"

    response = {
        "status": "success",
        "data": {
            "insights": {
                "pain_points": painpoint.get("physical_painpoints", []) + painpoint.get("emotional_painpoints", []),
                "user_complaint_cluster": painpoint.get("use_case_disasters", []),
                "evidence": env_state.get("evidence", {}),
            },
            "audience": {
                "primary": audience.get("primary_user", ""),
                "sensitivity": dopamine.get("viral_emotion", ""),
                "trust_barriers": audience.get("trust_barriers", []),
            },
            "strategy": ui_strategy,
            "assets": {"tiktok_script": {"hook": hook_text, "cta": cta_text}, "storyboard": storyboard_data},
            "evaluation": {
                "confidence_score": retention_score,
                "risk_level": risk_level,
                "reasoning": (
                    f"{world_metrics.get('reason', '')}\n"
                    f"Dopamine score: {world_metrics.get('dopamine_score', 0):.2f}\n"
                    f"Evidence alignment: {world_metrics.get('evidence_alignment', 0):.2f}\n"
                    f"Creative CTR: {world_metrics.get('predicted_ctr', 0) * 100:.1f}%\n"
                    f"Grounded CTR: {world_metrics.get('grounded_ctr', 0) * 100:.1f}%\n"
                    f"Source confidence: {world_metrics.get('source_confidence', 0):.2f}\n"
                    f"Failure type: {world_metrics.get('failure_type', '')}"
                ),
                "is_approved": world_metrics.get("is_approved", False),
                "is_grounded": world_metrics.get("is_grounded", False),
                "creative_approved": world_metrics.get("creative_approved", False),
                "grounded_approved": world_metrics.get("grounded_approved", False),
            },
            "feedback": exec_state.get("reflection", {}).get("root_cause", "Memory writer recorded the final outcome."),
        },
        "output_language": output_language,
    }
    response["data"]["video_generation_packet"] = _build_video_generation_packet(
        storyboard_data.get("product_name") or env_state.get("product_title") or request.url,
        storyboard_data.get("product_category") or env_state.get("product_category") or "",
        response["data"]["assets"],
        response["data"]["insights"],
        response["data"]["evaluation"],
        output_language,
    )
    response["data"]["external_video_tool_handoff"] = _build_external_video_tool_handoff(
        storyboard_data.get("product_name") or env_state.get("product_title") or request.url,
        storyboard_data.get("product_category") or env_state.get("product_category") or "",
        response["data"],
    )
    response["data"]["agent_trace"] = _build_agent_trace(response["data"], output_language)
    response["data"]["multi_agent_workflow"] = _build_multi_agent_workflow(response["data"], output_language)
    try:
        response["data"] = await translate_product_visible_data(
            response["data"],
            output_language,
        )
    except Exception as exc:
        error_type = _error_type(exc)
        emit_event(
            "generate_copilot_error",
            request_id,
            endpoint="/api/v1/generate-copilot",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=env_state.get("product_category"),
            goal=request.goal,
            error_type=error_type,
            output_language=output_language,
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": "generate-copilot language rendering failed safely. Please retry.",
                "error_type": "generation_failed",
                "request_id": request_id,
            },
        )

    emit_event(
        "generate_copilot_complete",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category"),
        goal=request.goal,
        output_language=output_language,
    )
    return response


@app.post("/api/v1/generate-from-description", response_model=ProductDescriptionResponse)
async def generate_from_description(request: ProductDescriptionRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    product_name = _clean_description_text(request.product_name)
    emit_event(
        "generate_from_description_start",
        request_id,
        endpoint="/api/v1/generate-from-description",
        status="started",
        product_category=request.product_category or "user_provided_product",
        goal=request.goal,
        output_language=output_language,
    )

    validation_error = _validate_description_request(request, request_id)
    if validation_error:
        emit_event(
            "generate_from_description_error",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or "user_provided_product",
            goal=request.goal,
            output_language=output_language,
        )
        return validation_error

    try:
        generated = await generate_description_brief(request)
        data = _description_response_data(request, generated)
        data = await translate_product_visible_data(data, output_language)
        response = {
            "status": "success",
            "data": data,
            "request_id": request_id,
            "output_language": output_language,
        }
        emit_event(
            "generate_from_description_complete",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            output_language=output_language,
        )
        return response
    except Exception:
        emit_event(
            "generate_from_description_error",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            error_type="generation_failed",
            output_language=output_language,
        )
        return _description_error(
            "Product Description Mode generation failed safely. Please retry with a shorter description.",
            "generation_failed",
            request_id,
            status_code=503,
        )


@app.post("/api/v1/agent-runs/from-reviews", response_model=AgentRunCreateResponse)
async def create_agent_run_from_reviews(
    request: PastedReviewsRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
):
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    safe_request = request.model_copy(update={"output_language": output_language})
    validation_error = _validate_pasted_reviews_request(safe_request, request_id)
    if validation_error:
        return validation_error

    run = build_agent_run(
        input_type="pasted_reviews",
        output_language=output_language,
        request_id=request_id,
    )
    AGENT_RUN_STORE.create(run)
    AGENT_RUN_STORE.append_event(
        run["run_id"],
        "run_created",
        "Agent run created for pasted customer feedback.",
        data={
            "input_type": "pasted_reviews",
            "output_language": output_language,
            "external_api_called": False,
            "cost_incurred_by_crossgrowth": False,
        },
    )
    background_tasks.add_task(_execute_pasted_reviews_agent_run, run["run_id"], safe_request)
    current_run = AGENT_RUN_STORE.get(run["run_id"]) or run
    return {
        "status": "success",
        "run": current_run,
        "poll_url": f"/api/v1/agent-runs/{run['run_id']}",
        "events_url": f"/api/v1/agent-runs/{run['run_id']}/events",
        "request_id": request_id,
    }


@app.get("/api/v1/agent-runs", response_model=AgentRunListResponse)
async def list_agent_runs(http_request: Request, limit: int = 10):
    safe_limit = max(1, min(int(limit or 10), 50))
    runs = AGENT_RUN_STORE.list(safe_limit)
    return {
        "status": "success",
        "runs": runs,
        "run_count": len(runs),
        "limit": safe_limit,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/agent-runs/{run_id}", response_model=AgentRunStatusResponse)
async def get_agent_run(run_id: str, http_request: Request):
    run = AGENT_RUN_STORE.get(run_id)
    if not run:
        _agent_run_not_found(run_id)
    return {
        "status": "success",
        "run": run,
        "request_id": http_request.state.request_id,
    }


@app.get("/api/v1/agent-runs/{run_id}/events", response_model=AgentRunEventsResponse)
async def get_agent_run_events(run_id: str, http_request: Request):
    run = AGENT_RUN_STORE.get(run_id)
    if not run:
        _agent_run_not_found(run_id)
    return {
        "status": "success",
        "run_id": run_id,
        "events": run.get("events") or [],
        "request_id": http_request.state.request_id,
    }


@app.post("/api/v1/generate-from-reviews", response_model=PastedReviewsResponse)
async def generate_from_reviews(request: PastedReviewsRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    output_language, language_error = _validate_output_language(
        request.output_language,
        request_id,
    )
    if language_error:
        return language_error

    product_name = _clean_description_text(request.product_name)
    emit_event(
        "generate_from_reviews_start",
        request_id,
        endpoint="/api/v1/generate-from-reviews",
        status="started",
        product_category=request.product_category or "user_pasted_reviews_product",
        goal=request.goal,
        output_language=output_language,
    )

    validation_error = _validate_pasted_reviews_request(request, request_id)
    if validation_error:
        emit_event(
            "generate_from_reviews_error",
            request_id,
            endpoint="/api/v1/generate-from-reviews",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or "user_pasted_reviews_product",
            goal=request.goal,
            output_language=output_language,
        )
        return validation_error

    evidence_quotes = _split_pasted_review_quotes(request.pasted_reviews)
    try:
        generated = await generate_pasted_reviews_brief(request, evidence_quotes)
        data = _pasted_reviews_response_data(request, generated, evidence_quotes)
        data = await translate_product_visible_data(data, output_language)
        response = {
            "status": "success",
            "data": data,
            "request_id": request_id,
            "output_language": output_language,
        }
        emit_event(
            "generate_from_reviews_complete",
            request_id,
            endpoint="/api/v1/generate-from-reviews",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            output_language=output_language,
        )
        return response
    except Exception:
        emit_event(
            "generate_from_reviews_error",
            request_id,
            endpoint="/api/v1/generate-from-reviews",
            status="error",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
            error_type="generation_failed",
            output_language=output_language,
        )
        return _description_error(
            "Pasted Reviews Mode generation failed safely. Please retry with fewer review snippets.",
            "generation_failed",
            request_id,
            status_code=503,
        )


@app.post("/api/v1/translate-output", response_model=TranslationResponse)
async def translate_output(request: TranslationRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    emit_event(
        "translate_output_start",
        request_id,
        endpoint="/api/v1/translate-output",
        status="started",
        target_language=request.target_language,
        input_size_char=len(request.text or ""),
    )
    translated_text = await translate_visible_output(
        request.text,
        request.target_language,
    )
    emit_event(
        "translate_output_complete",
        request_id,
        endpoint="/api/v1/translate-output",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        target_language=request.target_language,
        input_size_char=len(request.text or ""),
    )
    return TranslationResponse(
        translated_text=translated_text,
        target_language=request.target_language,
        request_id=request_id,
    )


@app.post("/api/v1/debug-copilot", response_model=DebugCopilotResponse)
async def debug_copilot_flow(request: GrowthRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    emit_event(
        "debug_copilot_start",
        request_id,
        endpoint="/api/v1/debug-copilot",
        status="started",
        goal=request.goal,
    )
    initial_state = {
        "env_state": {"asin_url": request.url, "business_goal": request.goal},
        "cognitive_state": {},
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": {},
        "revision_count": 0,
        "next_nodes": ["planner"],
    }

    final_state = await copilot_engine.ainvoke(initial_state)
    env_state = final_state.get("env_state", {})
    exec_state = final_state.get("execution_state", {})
    telemetry_state = final_state.get("telemetry_state", {})

    response = {
        "request_id": request_id,
        "product_category": env_state.get("product_category"),
        "evidence": env_state.get("evidence"),
        "cognitive_state": final_state.get("cognitive_state", {}),
        "execution_state": exec_state,
        "world_metrics": final_state.get("world_metrics", {}),
        "regenerate_node": exec_state.get("regenerate_node"),
        "revision_count": final_state.get("revision_count", 0),
        "telemetry": telemetry_state,
        "telemetry_summary": summarize_telemetry(telemetry_state),
        "memory_observability": memory_engine.observability_snapshot(),
        "shadow_sources": (
            _amazon_shadow_sources(request.url, env_state.get("product_category", ""))
            if request.real_source_mode == "amazon_shadow"
            else {}
        ),
    }
    emit_event(
        "debug_copilot_complete",
        request_id,
        endpoint="/api/v1/debug-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category"),
        goal=request.goal,
    )
    return response


@app.post("/api/v1/debug-source-probe", response_model=SourceProbeResponse)
async def debug_source_probe(request: SourceProbeRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    emit_event(
        "debug_source_probe_start",
        request_id,
        endpoint="/api/v1/debug-source-probe",
        status="started",
        product_category=request.product_category,
    )
    providers = request.providers or sorted(SOURCE_PROBE_PROVIDERS)
    results = []

    for provider in providers:
        if provider not in SOURCE_PROBE_PROVIDERS:
            results.append(
                SourceProbeResult(
                    provider=provider,
                    status="disabled",
                    error="Provider is not available in debug-only real-source probe.",
                    metadata={"allowed": False},
                )
            )
            continue

        started = time.perf_counter()
        try:
            evidence = source_probe_registry.fetch(
                provider,
                request.url or "",
                request.product_category,
            )
            warnings = list(evidence.data_warnings)
            disabled = any(
                warning.endswith("_disabled") or warning.endswith("_not_enabled")
                for warning in warnings
            )
            if disabled:
                status = "disabled"
            elif evidence.source_type == "unavailable":
                status = "unavailable"
            else:
                status = "success"
            results.append(
                SourceProbeResult(
                    provider=provider,
                    status=status,
                    source_confidence=evidence.confidence,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    evidence_preview=evidence.evidence_quotes[:3],
                    metadata={
                        **evidence.metadata,
                        "source_type": evidence.source_type,
                        "data_warnings": warnings,
                    },
                )
            )
        except Exception as exc:
            results.append(
                SourceProbeResult(
                    provider=provider,
                    status="error",
                    latency_ms=(time.perf_counter() - started) * 1000,
                    error=str(exc),
                )
            )

    fallback_required = not any(
        result.status == "success" and result.source_confidence >= 0.70
        for result in results
    )
    telemetry = SourceProbeTelemetry(
        total_latency_ms=sum(result.latency_ms for result in results),
        provider_count=len(results),
        success_count=sum(result.status == "success" for result in results),
        disabled_count=sum(result.status == "disabled" for result in results),
        unavailable_count=sum(result.status == "unavailable" for result in results),
        error_count=sum(result.status == "error" for result in results),
        fallback_required=fallback_required,
    )
    response = SourceProbeResponse(
        request_id=request_id,
        debug_only=True,
        product_category=request.product_category,
        results=results,
        fallback_required=fallback_required,
        telemetry=telemetry,
        memory_write_allowed=False,
    )
    emit_event(
        "debug_source_probe_complete",
        request_id,
        endpoint="/api/v1/debug-source-probe",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=request.product_category,
        provider_count=len(results),
        fallback_required=fallback_required,
    )
    return response




# L37-A/B multi-product review workspace analysis.
from collections import Counter
from schemas.review_workspace import (
    ReviewProductSummary,
    ReviewSourceBreakdown,
    ReviewSourceGroupSummary,
    ReviewSampleInterpretation,
    ReviewThemeSummary,
    ReviewVideoScript,
    ReviewVideoScriptPack,
    ReviewWorkspaceProduct,
    ReviewWorkspaceRequest,
    ReviewWorkspaceResponse,
    ReviewWorkspaceReview,
)
from schemas.review_paste import (
    PastedReviewWorkspaceAnalyzeRequest,
    PastedReviewWorkspaceAnalyzeResponse,
    ReviewPasteParseRequest,
    ReviewPasteParseResponse,
)

_REVIEW_WORKSPACE_THEME_MARKERS = {
    "leak / mess risk": ["leak", "leaking", "spill", "spilled", "mess", "drip"],
    "hard to clean": ["hard to clean", "difficult to clean", "scrub", "dishwasher"],
    "size / fit issue": ["too small", "too big", "doesn't fit", "didn't fit", "opening was bigger", "wide cans", "narrow opening", "\u30b5\u30a4\u30ba\u304c\u5c0f\u3055\u3044", "1\u30b5\u30a4\u30ba\u5927\u304d\u3044", "2\u30b5\u30a4\u30ba\u5927\u304d\u3044", "\u5c0f\u3076\u308a"],
    "grip / slipping concern": ["move a lot", "moves a lot", "stick to the floor", "sliding", "slides", "slip around", "slips", "does not stay", "doesn\'t stay", "stay in place"],
    "thickness / robot vacuum tradeoff": ["robot vacuum", "gets trapped", "get trapped", "too thick", "thick nature", "does not fit under", "doesn\'t fit under", "fit under doors", "under some doors"],
    "color expectation mismatch": ["color", "colour", "shade", "darker", "\u8272\u5473", "\u5199\u771f\u3088\u308a", "\u6697\u3081", "\u8272\u306e\u9055\u3044", "\u989c\u8272", "\u8272\u5dee"],
    "sewing / quality control issue": ["sewing", "stitch", "button hole", "thread", "quality control", "\u7e2b\u88fd", "\u307b\u3064\u308c", "\u30dc\u30bf\u30f3\u7a74", "\u691c\u54c1", "\u54c1\u8cea", "\u9752\u3044\u30da\u30f3"],
    "summer fabric comfort": ["fabric", "soft", "comfortable", "breathable", "\u7d20\u6750", "\u808c\u89e6\u308a", "\u67d4\u3089\u304b", "\u6dbc\u3057", "\u901a\u6c17", "\u900f\u6c14", "\u8f7b\u4fbf"],
    "durability concern": ["broke", "break", "broken", "flimsy", "crack", "not durable"],
    "space constraint": ["small kitchen", "apartment", "storage", "counter space"],
}

_REVIEW_WORKSPACE_FOOD_THEME_MARKERS = {
    "taste / flavor concern": [
        "watery",
        "flavorless",
        "terrible vinegar",
        "bad taste",
        "tastes bad",
        "bland",
        "weak flavor",
        "too sweet",
        "too acidic",
    ],
    "size / quantity mismatch": [
        "stated size is wrong",
        "size is wrong",
        "wrong size",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz bottle",
        "single bottle",
        "not sold by the single bottle",
        "only came in a 2-pack",
        "missing bottle",
        "pack count",
        "quantity mismatch",
    ],
    "price / value concern": [
        "priced wrong",
        "price is wrong",
        "expensive",
        "pricey",
        "not worth",
        "overpriced",
    ],
    "packaging / shipping concern": [
        "arrived damaged",
        "broken bottle",
        "leaked in shipping",
        "poorly packaged",
        "packaging problem",
        "no lid",
        "not lid",
        "air is ever present",
        "oxidation",
        "cap leaked",
    ],
    "quality consistency concern": [
        "quality changed",
        "inconsistent",
        "not the same",
        "store brand is better",
        "infinitely better",
    ],
}


_REVIEW_WORKSPACE_OBJECTION_MARKERS = [
    "but",
    "however",
    "wish",
    "too",
    "not",
    "doesn't",
    "didn't",
    "hard",
    "difficult",
    "wrong",
    "problem",
    "concern",
    "unless",
    "except",
    "although",
    "issue",
]

_REVIEW_WORKSPACE_LIKE_MARKERS = [
    "love", "great", "easy", "perfect", "works", "useful", "recommend", "helpful",
    "will continue to purchase", "best rootbeer", "best root beer", "order it frequently",
    "great flavor", "greater flavor", "smoother", "worth the price",
    "cannot beat the price", "can't beat the price", "value priced", "worth it",
    "??", "??", "??", "??", "??",
]

_REVIEW_WORKSPACE_USE_CASE_MARKERS = [
    "for", "when", "use it", "daily", "morning", "travel", "kitchen", "work", "kids", "pet",
    "??", "??", "??", "??", "??", "??", "??", "??",
]


def _rw_text(value) -> str:
    return " ".join(str(value or "").split())


def _rw_rating_value(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).split()[0])
    except (TypeError, ValueError):
        return None


def _rw_review_score(review) -> int:
    text = _rw_text(review.text)
    lowered = text.lower()
    if len(text) < 18:
        return 0

    score = 1
    rating = _rw_rating_value(review.rating)
    if rating is not None and rating <= 3:
        score += 3
    if rating is not None and rating >= 4:
        score += 1
    if review.helpful_count:
        score += min(3, int(review.helpful_count) // 5 + 1)
    if any(marker in lowered for marker in _REVIEW_WORKSPACE_OBJECTION_MARKERS):
        score += 3
    if any(marker in lowered for marker in _REVIEW_WORKSPACE_LIKE_MARKERS):
        score += 2
    if len(text) >= 80:
        score += 2
    return score


def _rw_collect_reviews(payload: ReviewWorkspaceRequest) -> list[dict]:
    rows = []
    seen = set()
    for product in payload.products:
        for review in product.reviews:
            text = _rw_text(review.text)
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            score = _rw_review_score(review)
            rows.append({
                "product": product,
                "review": review,
                "text": text,
                "score": score,
                "rating": _rw_rating_value(review.rating),
                "metadata": _rw_extract_review_metadata(review),
            })
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows


def _rw_raw_review_count(payload: ReviewWorkspaceRequest) -> int:
    return sum(len(getattr(product, "reviews", []) or []) for product in payload.products or [])


def _rw_duplicate_review_count(payload: ReviewWorkspaceRequest, rows: list[dict]) -> int:
    return max(0, _rw_raw_review_count(payload) - len(rows))



def _rw_primary_asin(payload: ReviewWorkspaceRequest) -> str:
    for product in payload.products or []:
        asin = _rw_text(getattr(product, "asin", ""))
        if asin:
            return asin
    return ""


def _rw_review_url_blob(row: dict) -> str:
    product = row.get("product")
    review = row.get("review")
    values = [
        getattr(product, "url", ""),
        getattr(product, "asin", ""),
        getattr(review, "source_section", ""),
        row.get("text", ""),
    ]
    return " ".join(str(value or "") for value in values).lower()


def _rw_review_source_tags(row: dict, primary_asin: str) -> list[str]:
    product = row.get("product")
    asin = _rw_text(getattr(product, "asin", ""))
    blob = _rw_review_url_blob(row)
    tags: list[str] = []

    is_variant = bool(asin and primary_asin and asin != primary_asin)
    if is_variant:
        tags.append("variant")
    elif asin or primary_asin:
        tags.append("main_product")

    if any(marker in blob for marker in [
        "filterbystar=critical",
        "filterbystar=one_star",
        "filterbystar=two_star",
        "filterbystar=three_star",
    ]):
        tags.append("low_star")

    if "reviewertype=avp_only_reviews" in blob or "verified purchase" in blob or "\u5df2\u786e\u8ba4\u8d2d\u4e70" in blob:
        tags.append("verified_purchase")

    if "sortby=recent" in blob:
        tags.append("recent")

    return tags or ["unknown"]


def _rw_first_metadata_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        try:
            match = re.search(pattern, text, flags=re.IGNORECASE)
        except re.error:
            continue

        if not match:
            continue

        value = ""
        if match.groups():
            value = match.group(1) or ""
        else:
            value = match.group(0) or ""

        value = " ".join(value.split()).strip(" -:;,??")
        if value:
            return value[:120]

    return ""


def _rw_metadata_between(text: str, start_markers: list[str], end_markers: list[str]) -> str:
    if not text:
        return ""

    best_start = -1
    best_marker = ""

    for marker in start_markers:
        index = text.find(marker)
        if index >= 0 and (best_start < 0 or index < best_start):
            best_start = index
            best_marker = marker

    if best_start < 0:
        return ""

    start = best_start + len(best_marker)
    end = len(text)

    for marker in end_markers:
        index = text.find(marker, start)
        if index >= 0:
            end = min(end, index)

    value = " ".join(text[start:end].split()).strip(" -:;,??")
    return value[:120]

def _rw_extract_review_metadata(review) -> dict:
    raw_text = _rw_text(getattr(review, "text", ""))
    source_section = _rw_text(getattr(review, "source_section", ""))
    blob = f"{raw_text} {source_section}"

    zh_color = chr(0x989c) + chr(0x8272) + ":"
    zh_size = chr(0x5c3a) + chr(0x5bf8) + ":"
    zh_verified = "".join(chr(code) for code in [0x5df2, 0x786e, 0x8ba4, 0x8d2d, 0x4e70])
    zh_useful = "".join(chr(code) for code in [0x4f4d, 0x4f7f, 0x7528, 0x8005, 0x8ba4, 0x4e3a, 0x6b64, 0x8bc4, 0x8bba, 0x6709, 0x7528])
    zh_year = chr(0x5e74)
    zh_month = chr(0x6708)
    zh_day = chr(0x65e5)

    jp_color = "".join(chr(code) for code in [0x30ab, 0x30e9, 0x30fc]) + ":"
    jp_size = "".join(chr(code) for code in [0x30b5, 0x30a4, 0x30ba]) + ":"
    jp_verified = "".join(chr(code) for code in [0x78ba, 0x8a8d, 0x6e08, 0x307f, 0x8cfc, 0x5165])

    rating = _rw_rating_value(getattr(review, "rating", None))

    review_date = _rw_first_metadata_match(
        blob,
        [
            r"Reviewed in .*? on ([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"(\d{4}" + zh_year + r"\d{1,2}" + zh_month + r"\d{1,2}" + zh_day + r")",
        ],
    )

    color = _rw_first_metadata_match(
        blob,
        [
            r"Color:\s*(.+?)(?=\s+Size:|\s+Verified Purchase|\s+Reviewed in|$)",
        ],
    )
    if not color:
        color = _rw_metadata_between(
            blob,
            [zh_color, jp_color],
            [zh_size, jp_size, zh_verified, jp_verified, "Verified Purchase"],
        )

    size = _rw_first_metadata_match(
        blob,
        [
            r"Size:\s*(.+?)(?=\s+Verified Purchase|\s+Reviewed in|$)",
        ],
    )
    if not size:
        size = _rw_metadata_between(
            blob,
            [zh_size, jp_size],
            [zh_verified, jp_verified, "Verified Purchase"],
        )

    helpful_count = getattr(review, "helpful_count", None)
    try:
        helpful_count = int(helpful_count) if helpful_count is not None else None
    except (TypeError, ValueError):
        helpful_count = None

    if helpful_count is None:
        helpful_match = re.search(r"(\d+)\s+people found this helpful", blob, flags=re.IGNORECASE)
        if helpful_match:
            helpful_count = int(helpful_match.group(1))
        elif re.search(r"one person found this helpful", blob, flags=re.IGNORECASE):
            helpful_count = 1

    if helpful_count is None:
        helpful_match = re.search(r"(\d+)\s*" + re.escape(zh_useful), blob)
        if helpful_match:
            helpful_count = int(helpful_match.group(1))

    verified_purchase = any(
        marker in blob
        for marker in [
            "Verified Purchase",
            "Verified purchase",
            zh_verified,
            jp_verified,
            "reviewertype=avp_only_reviews",
        ]
    )

    return {
        "rating": rating,
        "review_date": review_date,
        "verified_purchase": verified_purchase,
        "color": color,
        "size": size,
        "helpful_count": helpful_count,
    }

def _rw_metadata_counter_values(rows: list[dict], key: str, limit: int = 5) -> list[str]:
    counter = Counter()
    for row in rows:
        value = (row.get("metadata") or {}).get(key)
        if value:
            counter[str(value)] += 1
    return [f"{value}: {count}" for value, count in counter.most_common(limit)]


def _rw_source_metadata_summary(rows: list[dict]) -> dict:
    summary = {
        "verified_purchase_count": 0,
        "review_date_count": 0,
        "helpful_vote_review_count": 0,
    }

    for row in rows:
        metadata = row.get("metadata") or {}
        if metadata.get("verified_purchase"):
            summary["verified_purchase_count"] += 1
        if metadata.get("review_date"):
            summary["review_date_count"] += 1
        if metadata.get("helpful_count"):
            summary["helpful_vote_review_count"] += 1

    colors = _rw_metadata_counter_values(rows, "color")
    sizes = _rw_metadata_counter_values(rows, "size")
    dates = _rw_metadata_counter_values(rows, "review_date")

    if colors:
        summary["top_colors"] = colors
    if sizes:
        summary["top_sizes"] = sizes
    if dates:
        summary["top_review_dates"] = dates

    return summary



def _rw_source_label(source_type: str, language: str) -> str:
    if language == "zh-CN":
        return {
            "main_product": "\u4e3b\u5546\u54c1\u8bc4\u8bba",
            "variant": "\u53d8\u4f53\u8bc4\u8bba",
            "low_star": "\u4f4e\u661f\u8bc4\u8bba",
            "verified_purchase": "\u5df2\u786e\u8ba4\u8d2d\u4e70\u8bc4\u8bba",
            "recent": "\u6700\u65b0\u8bc4\u8bba",
            "unknown": "\u672a\u5206\u7c7b\u8bc4\u8bba",
        }.get(source_type, source_type)

    return {
        "main_product": "Main product reviews",
        "variant": "Variant reviews",
        "low_star": "Low-star reviews",
        "verified_purchase": "Verified-purchase reviews",
        "recent": "Recent reviews",
        "unknown": "Unclassified reviews",
    }.get(source_type, source_type)


def _rw_source_group_summary(source_type: str, rows: list[dict], language: str) -> ReviewSourceGroupSummary:
    asin_counts = Counter(_rw_text(getattr(row.get("product"), "asin", "")) or "unknown" for row in rows)
    quotes: list[str] = []
    seen = set()

    for row in sorted(rows, key=lambda item: item.get("score", 0), reverse=True):
        quote = _rw_compact_evidence_quote(row.get("text", ""))
        key = quote.lower()
        if quote and key not in seen:
            seen.add(key)
            quotes.append(quote)
        if len(quotes) >= 3:
            break

    return ReviewSourceGroupSummary(
        source_type=source_type,
        label=_rw_source_label(source_type, language),
        review_count=len(rows),
        high_signal_review_count=sum(1 for row in rows if row.get("score", 0) >= 4),
        asin_count=len([asin for asin in asin_counts if asin != "unknown"]),
        top_asins=[f"{asin}: {count}" for asin, count in asin_counts.most_common(5)],
        evidence_quotes=quotes,
        metadata_summary=_rw_source_metadata_summary(rows),
    )


def _rw_source_breakdown(payload: ReviewWorkspaceRequest, rows: list[dict]) -> ReviewSourceBreakdown:
    language = payload.output_language
    primary_asin = _rw_primary_asin(payload)
    raw_review_count = _rw_raw_review_count(payload)
    unique_review_count = len(rows)
    duplicate_review_count = max(0, raw_review_count - unique_review_count)
    rows_by_source: dict[str, list[dict]] = {
        "main_product": [],
        "variant": [],
        "low_star": [],
        "verified_purchase": [],
        "recent": [],
        "unknown": [],
    }
    asin_counts = Counter()

    for row in rows:
        product = row.get("product")
        asin = _rw_text(getattr(product, "asin", "")) or "unknown"
        asin_counts[asin] += 1

        tags = _rw_review_source_tags(row, primary_asin)
        for tag in tags:
            rows_by_source.setdefault(tag, []).append(row)

    source_groups = [
        _rw_source_group_summary(source_type, source_rows, language)
        for source_type, source_rows in rows_by_source.items()
        if source_rows
    ]

    if language == "zh-CN":
        guidance = [
            "\u4e3b\u5546\u54c1\u4fe1\u53f7\u548c\u53d8\u4f53\u4fe1\u53f7\u9700\u8981\u5206\u5f00\u89e3\u8bfb\uff0c\u4e0d\u8981\u628a\u5355\u4e2a\u5c3a\u7801\u6216\u989c\u8272\u95ee\u9898\u76f4\u63a5\u6cdb\u5316\u4e3a\u6574\u4e2a\u5546\u54c1\u95ee\u9898\u3002",
            "\u4f4e\u661f\u548c\u5df2\u786e\u8ba4\u8d2d\u4e70\u8bc4\u8bba\u66f4\u9002\u5408\u7528\u6765\u627e\u8d2d\u4e70\u987e\u8651\u548c\u53cd\u5bf9\u610f\u89c1\u3002",
            "\u6700\u65b0\u8bc4\u8bba\u66f4\u9002\u5408\u7528\u6765\u89c2\u5bdf\u8fd1\u671f\u8d28\u91cf\u6216\u5c65\u7ea6\u53d8\u5316\u3002",
        ]
    else:
        guidance = [
            "Read main-product and variant signals separately; do not generalize one size/color issue to the entire product.",
            "Use low-star and verified-purchase reviews to identify objections and buyer hesitation.",
            "Use recent reviews to watch for newer quality, fulfillment, or expectation shifts.",
        ]

    return ReviewSourceBreakdown(
        total_reviews=unique_review_count,
        raw_review_count=raw_review_count,
        duplicate_review_count=duplicate_review_count,
        main_product_reviews=len(rows_by_source.get("main_product", [])),
        variant_reviews=len(rows_by_source.get("variant", [])),
        low_star_reviews=len(rows_by_source.get("low_star", [])),
        verified_purchase_reviews=len(rows_by_source.get("verified_purchase", [])),
        recent_reviews=len(rows_by_source.get("recent", [])),
        unknown_reviews=len(rows_by_source.get("unknown", [])),
        asin_review_counts=dict(asin_counts),
        source_groups=source_groups,
        guidance=guidance,
    )


def _rw_packet_theme_items(themes: list[ReviewThemeSummary], limit: int = 6) -> list[dict]:
    items: list[dict] = []
    for theme in (themes or [])[:limit]:
        items.append(
            {
                "label": getattr(theme, "label", ""),
                "evidence_count": getattr(theme, "evidence_count", 0),
                "evidence_quotes": list(getattr(theme, "evidence_quotes", []) or [])[:3],
            }
        )
    return items


def _rw_packet_source_groups(source_breakdown: ReviewSourceBreakdown, limit: int = 6) -> list[dict]:
    groups: list[dict] = []
    for group in list(getattr(source_breakdown, "source_groups", []) or [])[:limit]:
        groups.append(
            {
                "source_type": getattr(group, "source_type", ""),
                "label": getattr(group, "label", ""),
                "review_count": getattr(group, "review_count", 0),
                "high_signal_review_count": getattr(group, "high_signal_review_count", 0),
                "asin_count": getattr(group, "asin_count", 0),
                "top_asins": list(getattr(group, "top_asins", []) or [])[:5],
                "evidence_quotes": list(getattr(group, "evidence_quotes", []) or [])[:3],
                "metadata_summary": dict(getattr(group, "metadata_summary", {}) or {}),
            }
        )
    return groups


def _rw_packet_quotes(
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
    source_breakdown: ReviewSourceBreakdown,
    limit: int = 12,
) -> list[str]:
    quotes: list[str] = []
    seen = set()

    def add(value: str):
        quote = _rw_quote_snippet(value, 240)
        key = " ".join(quote.lower().split())
        if not quote or key in seen:
            return
        seen.add(key)
        quotes.append(quote)

    for themes in [buyer_objections, common_pain_points, liked_points, use_cases]:
        for theme in themes or []:
            for quote in getattr(theme, "evidence_quotes", []) or []:
                add(quote)
                if len(quotes) >= limit:
                    return quotes

    for group in getattr(source_breakdown, "source_groups", []) or []:
        for quote in getattr(group, "evidence_quotes", []) or []:
            add(quote)
            if len(quotes) >= limit:
                return quotes

    return quotes


def _review_workspace_llm_evidence_packet(
    payload: ReviewWorkspaceRequest,
    rows: list[dict],
    high_signal_rows: list[dict],
    source_breakdown: ReviewSourceBreakdown,
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
) -> dict:
    primary_product = next((product for product in payload.products if _rw_text(getattr(product, "title", ""))), None)
    if primary_product is None:
        primary_product = payload.products[0] if payload.products else None

    raw_review_count = getattr(source_breakdown, "raw_review_count", 0)
    duplicate_review_count = getattr(source_breakdown, "duplicate_review_count", 0)
    warnings = [
        "review_workspace_visible_sample_only",
        "review_workspace_no_external_fetch",
    ]
    if duplicate_review_count:
        warnings.append("duplicate_reviews_removed")
    if getattr(source_breakdown, "variant_reviews", 0):
        warnings.append("variant_reviews_present")
    if getattr(source_breakdown, "low_star_reviews", 0):
        warnings.append("low_star_reviews_present")
    if getattr(source_breakdown, "verified_purchase_reviews", 0):
        warnings.append("verified_purchase_reviews_present")

    source_groups = _rw_packet_source_groups(source_breakdown)
    return {
        "packet_version": "review_workspace_v1",
        "intended_model_use": "creative_brief_generation",
        "product": {
            "title": _rw_text(getattr(primary_product, "title", "")) if primary_product else "",
            "asin": _rw_text(getattr(primary_product, "asin", "")) if primary_product else "",
            "source_type": "review_workspace",
            "product_count": len(payload.products),
        },
        "review_stats": {
            "total_reviews": len(rows),
            "parsed_reviews": len(rows),
            "unique_analyzed_reviews": len(rows),
            "raw_review_count": raw_review_count,
            "duplicate_review_count": duplicate_review_count,
            "high_signal_reviews": len(high_signal_rows),
            "verified_purchase_reviews": getattr(source_breakdown, "verified_purchase_reviews", 0),
            "low_star_reviews": getattr(source_breakdown, "low_star_reviews", 0),
            "warnings": warnings,
            "data_warnings": warnings,
        },
        "evidence": {
            "pain_points": _rw_packet_theme_items(common_pain_points),
            "buyer_objections": _rw_packet_theme_items(buyer_objections),
            "positive_signals": _rw_packet_theme_items(liked_points),
            "use_cases": _rw_packet_theme_items(use_cases),
            "quotes": _rw_packet_quotes(
                common_pain_points,
                buyer_objections,
                liked_points,
                use_cases,
                source_breakdown,
            ),
            "source_groups": source_groups,
        },
        "generation_constraints": [
            "Use only supplied review evidence and product fields.",
            "Do not claim full-market statistics.",
            "Do not generalize one variant/color/size issue to the whole product unless multiple reviews support it.",
            "Keep main product / variant / competitor source boundaries visible.",
            "Do not turn buyer objections into positive claims unless evidence explicitly resolves the concern.",
        ],
    }


def _rw_theme_summaries(rows: list[dict], themes: dict[str, list[str]], limit: int = 6) -> list[ReviewThemeSummary]:
    scored = []
    for label, markers in themes.items():
        matched = []
        for row in rows:
            raw_text = row["text"]
            lowered = raw_text.lower()
            compact_quote = _rw_compact_evidence_quote(raw_text) if "_rw_compact_evidence_quote" in globals() else raw_text
            compact_lower = compact_quote.lower()
            if not any(marker.lower() in lowered or marker.lower() in compact_lower for marker in markers):
                continue
            needs_matched_quote = (
                "_rw_theme_needs_matched_quote" in globals()
                and _rw_theme_needs_matched_quote(label)
            )
            if needs_matched_quote and "_rw_quote_matches_theme" in globals() and not _rw_quote_matches_theme(label, compact_quote):
                continue
            if compact_quote:
                matched.append(compact_quote)
        if matched:
            scored.append((label, matched))
    scored.sort(key=lambda item: len(item[1]), reverse=True)
    return [
        ReviewThemeSummary(
            label=label,
            evidence_count=len(quotes),
            evidence_quotes=quotes[:3],
        )
        for label, quotes in scored[:limit]
    ]


def _rw_marker_summaries(rows: list[dict], markers: list[str], label_prefix: str, limit: int = 6) -> list[ReviewThemeSummary]:
    counter = Counter()
    quotes_by_marker: dict[str, list[str]] = {}
    for row in rows:
        lowered = row["text"].lower()
        for marker in markers:
            if marker.lower() in lowered:
                counter[marker] += 1
                quotes_by_marker.setdefault(marker, []).append(row["text"])
    return [
        ReviewThemeSummary(
            label=f"{label_prefix}: {marker}",
            evidence_count=count,
            evidence_quotes=quotes_by_marker.get(marker, [])[:3],
        )
        for marker, count in counter.most_common(limit)
    ]


def _rw_product_summary(product) -> ReviewProductSummary:
    rows = [
        {"text": _rw_text(review.text), "score": _rw_review_score(review), "review": review}
        for review in product.reviews
        if _rw_text(review.text)
    ]
    rows.sort(key=lambda item: item["score"], reverse=True)
    top_rows = rows[:10]
    pain_points = []
    liked_points = []
    for row in top_rows:
        lowered = row["text"].lower()
        if any(marker in lowered for marker in _REVIEW_WORKSPACE_OBJECTION_MARKERS):
            pain_points.append(row["text"])
        if any(marker in lowered for marker in _REVIEW_WORKSPACE_LIKE_MARKERS):
            liked_points.append(row["text"])
    return ReviewProductSummary(
        title=product.title or product.asin or product.url or "Untitled product",
        url=product.url,
        review_count=len(rows),
        high_signal_review_count=sum(1 for row in rows if row["score"] >= 4),
        top_pain_points=pain_points[:3],
        top_liked_points=liked_points[:3],
    )



def _rw_workspace_text_blob(payload, rows) -> str:
    parts: list[str] = []
    for product in getattr(payload, "products", []) or []:
        for attr in ("title", "brand", "description", "platform"):
            value = getattr(product, attr, "")
            if value:
                parts.append(str(value))
        for bullet in getattr(product, "bullet_points", []) or []:
            parts.append(str(bullet))

    for row in rows or []:
        if isinstance(row, dict):
            for key in ("text", "title", "product_title"):
                value = row.get(key)
                if value:
                    parts.append(str(value))

    return " ".join(parts).lower()


def _rw_workspace_is_food(payload, rows) -> bool:
    blob = _rw_workspace_text_blob(payload, rows)
    food_terms = [
        "vinegar",
        "balsamic",
        "olive oil",
        "sauce",
        "dressing",
        "flavor",
        "flavour",
        "taste",
        "tasty",
        "salad",
        "recipe",
        "cooking",
        "kitchen cookbook",
        "modena",
    ]
    return any(term in blob for term in food_terms)


def _rw_workspace_theme_markers(payload, rows):
    if _rw_workspace_is_food(payload, rows):
        return _REVIEW_WORKSPACE_FOOD_THEME_MARKERS
    return _REVIEW_WORKSPACE_THEME_MARKERS



def _rw_evidence_sentence_candidates(text: str) -> list[str]:
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return []

    # Do not blindly split on "?" because Amazon size text like "(16 oz?)"
    # can create broken fragments such as ") colavita, so..."
    normalized = cleaned.replace("!!!", ". ").replace("!!", ". ").replace("!", ". ")

    parts = re.split(r"(?<=[.])\s+|(?<=[?])\s+(?=[A-Z\"'])", normalized)
    candidates = []

    for part in parts:
        sentence = part.strip(" -:;,.")
        if not sentence:
            continue

        if "_rw_clean_evidence_fragment" in globals():
            sentence = _rw_clean_evidence_fragment(sentence)

        if not sentence or len(sentence) < 18:
            continue

        lower = sentence.lower()
        if lower.startswith(("so this is good", "but great for cooking", "and great for cooking")):
            continue

        candidates.append(sentence)

    return candidates or [_rw_clean_evidence_fragment(cleaned) if "_rw_clean_evidence_fragment" in globals() else cleaned]


def _rw_evidence_sentence_score(sentence: str) -> int:
    lower = sentence.lower()
    score = 0

    strong_terms = [
        "wrong size",
        "size is wrong",
        "stated size",
        "listed as",
        "what came was",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz",
        "2-pack",
        "single bottle",
        "not sold",
        "priced wrong",
        "price",
        "cheaper",
        "not worth",
        "not really worth",
        "price is ridiculous",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
        "wateriest",
        "flavorless",
        "terrible",
        "bad taste",
        "makes terrible",
        "store brand is better",
        "not super complex",
        "wish",
        "but",
        "however",
        "problem",
        "concern",
    ]
    for term in strong_terms:
        if term in lower:
            score += 4

    if "listed as" in lower and "what came was" in lower:
        score += 8
    if "received the regular size" in lower and "half size" in lower:
        score += 8

    if 45 <= len(sentence) <= 220:
        score += 3
    elif len(sentence) > 220:
        score += 1

    low_signal_terms = [
        "i bought this after reading reviews",
        "i use it with",
        "i put it on",
        "i throw in",
        "amazon's choice",
        "author of",
        "but great for cooking",
        "so this is good as long",
    ]
    for term in low_signal_terms:
        if term in lower:
            score -= 6

    if lower.startswith(("so ", "but ", "and ", "which ")):
        score -= 5

    return score


def _rw_best_evidence_sentence(text: str) -> str:
    candidates = _rw_evidence_sentence_candidates(text)
    if not candidates:
        return ""

    ranked = sorted(
        enumerate(candidates),
        key=lambda pair: (_rw_evidence_sentence_score(pair[1]), -pair[0]),
        reverse=True,
    )
    return ranked[0][1]



def _rw_clean_evidence_fragment(value: str) -> str:
    text = " ".join(str(value or "").split()).strip(" -:;,.")

    # Prefer the actual review body after Amazon purchase markers.
    for marker in [
        "Verified Purchase",
        "Verified purchase",
        "\u5df2\u786e\u8ba4\u8d2d\u4e70",
        "\u78ba\u8a8d\u6e08\u307f\u8cfc\u5165",
    ]:
        if marker in text:
            text = text.split(marker, 1)[1].strip()
            break

    # Remove English Amazon review chrome.
    text = re.sub(r"Reviewed in .*? on [A-Za-z]+ \d{1,2}, \d{4}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[1-5](?:\.0)?\s+out of 5 stars\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Size:\s*[^.?!?]{1,120}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Color:\s*[^.?!?]{1,120}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+\s+people found this helpful\b.*$", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bone person found this helpful\b.*$", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bHelpful\s+Report\b.*$", " ", text, flags=re.IGNORECASE)

    # Remove Japanese / Chinese Amazon review chrome.
    text = re.sub(r"\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5[^\s]{0,12}\u53d1\u5e03\u8bc4\u8bba", " ", text)
    text = re.sub(r"\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5[^\s]{0,18}\u30ec\u30d3\u30e5\u30fc", " ", text)
    text = re.sub(r"[1-5](?:\.0)?\s*(?:\u661f|\u9897\u661f)(?:\uff08\u6700\u9ad8\s*5\s*\u661f\uff09|\uff0c\u6700\u591a\s*5\s*\u9897\u661f)?", " ", text)
    text = re.sub(r"\u989c\u8272:\s*[^\s?.!?]{1,80}", " ", text)
    text = re.sub(r"\u5c3a\u5bf8:\s*[^\s?.!?]{1,80}", " ", text)
    text = re.sub(r"\d+\s*\u4f4d\u4f7f\u7528\u8005\u8ba4\u4e3a\u6b64\u8bc4\u8bba\u6709\u7528.*$", " ", text)
    text = re.sub(r"\u6709\u7528\s+\u4e3e\u62a5.*$", " ", text)
    text = re.sub(r"\u5c06\u8bc4\u8bba\u7ffb\u8bd1\u6210\u4e2d\u6587.*$", " ", text)

    text = re.sub(r"\s+", " ", text).strip(" -:;,.")
    text = _strip_amazon_reviewer_prefix(text)

    # Remove broken leading punctuation left by metadata cleanup.
    text = re.sub(r"^[)\]\s]+", "", text).strip()
    # Drop fragments that start mid-word after browser text extraction,
    # for example: "r to the glaze but the taste..."
    if re.match(r"^[b-z]\s+(?:to|of|for|with|and|but)\s+", text):
        return ""

    # Drop Amazon report-modal / community-guideline chrome accidentally captured as review text.
    report_modal_markers = [
        "submit a",
        "common reasons customers reviews",
        "harassment, profanity",
        "spam, advertisement, promotions",
        "given in exchange for cash",
        "community guidelines",
        "when we get your",
    ]
    lower_text = text.lower()
    if any(marker in lower_text for marker in report_modal_markers):
        return ""


    # Drop low-value revision prefix while keeping the actual claim.
    text = re.sub(r"^Revised\s+\d{1,2}/\d{1,2}/\d{2,4}\s*-\s*", "", text, flags=re.IGNORECASE)

    # If a candidate begins with a dangling conjunction and is only positive proof,
    # it should not become an objection evidence quote.
    if re.match(r"^(but|and)\s+great for cooking\.?$", text, flags=re.IGNORECASE):
        return ""

    return text.strip(" -:;,.")


def _rw_compact_evidence_quote(value: str, max_len: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""

    for marker in ["Verified Purchase ", "Verified purchase "]:
        if marker in text:
            text = text.split(marker, 1)[1].strip()
            break

    text = re.sub(r"Reviewed in .*? on [A-Za-z]+ \d{1,2}, \d{4}", " ", text)
    text = re.sub(r"Size:\s*[^.]{1,100}", " ", text)
    text = re.sub(r"\b[1-5](?:\.0)? out of 5 stars\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+\s+people found this\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bone person found this\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -:;,.")
    text = _rw_clean_evidence_fragment(text)

    if not text:
        return ""

    best_sentence = _rw_best_evidence_sentence(text)
    if best_sentence:
        best_sentence = _rw_clean_evidence_fragment(best_sentence)
        text = best_sentence

    if len(text) <= max_len:
        return text

    cut = text[:max_len].rstrip()
    sentence_end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if sentence_end >= 80:
        return cut[: sentence_end + 1].strip()

    return cut.rstrip(" ,;:") + "..."


def _rw_rebuild_theme_summary(theme, *, label: str | None = None, evidence_quotes: list[str] | None = None):
    data = theme.model_dump() if hasattr(theme, "model_dump") else dict(theme)
    if label is not None:
        data["label"] = label
    if evidence_quotes is not None:
        data["evidence_quotes"] = evidence_quotes
        data["evidence_count"] = max(data.get("evidence_count", 0), len(evidence_quotes))
    return theme.__class__(**data)


def _rw_compact_theme_summaries(themes):
    compacted = []

    for theme in themes or []:
        quotes = []
        seen = set()

        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = compact.lower()

            if compact and key not in seen:
                seen.add(key)
                quotes.append(compact)

            if len(quotes) >= 2:
                break

        compacted.append(_rw_rebuild_theme_summary(theme, evidence_quotes=quotes))

    return compacted


def _rw_objection_label_from_quotes(label: str, quotes: list[str]) -> str:
    blob = " ".join([label or "", *(quotes or [])]).lower()

    if any(term in blob for term in [
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "sliding",
        "slides",
        "slip around",
        "slips",
        "does not stay",
        "doesn't stay",
        "stay in place",
    ]):
        return "grip / slipping concern"

    if any(term in blob for term in [
        "robot vacuum",
        "gets trapped",
        "get trapped",
        "too thick",
        "thick nature",
        "does not fit under",
        "doesn't fit under",
        "fit under doors",
        "under some doors",
    ]):
        return "thickness / robot vacuum tradeoff"

    if any(term in blob for term in [
        "not really worth",
        "price is ridiculous",
        "too expensive",
        "overpriced",
        "not worth",
    ]):
        return "price / value concern"

    if any(term in blob for term in [
        "no lid",
        "not lid",
        "without a lid",
        "lid to go over the spout",
        "air is ever present",
        "oxidation",
        "cap leaked",
        "bottle cap",
    ]):
        return "packaging / spout concern"

    if any(term in blob for term in [
        "wrong size",
        "size is wrong",
        "stated size",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz",
        "single bottle",
        "not sold by the single bottle",
        "only came in a 2-pack",
        "missing bottle",
        "pack count",
        "quantity mismatch",
    ]):
        return "quantity / size uncertainty"

    if any(term in blob for term in [
        "priced wrong",
        "price",
        "expensive",
        "cheaper",
        "not worth",
    ]):
        return "price / value uncertainty"

    if any(term in blob for term in [
        "wish",
        "would buy again",
        "if they",
        "preference",
        "wanted",
    ]):
        return "missing expectation / wish"

    if any(term in blob for term in [
        "not super",
        "not the same",
        "not sold",
        "doesn't",
        "didn't",
        "not ",
    ]):
        return "expectation mismatch"

    if any(term in blob for term in ["but", "however", "although", "except", "unless"]):
        return "tradeoff / hesitation"

    cleaned = label.replace("objection: ", "").strip()
    if cleaned in {"but", "not", "wish", "wrong", "too", "however", "?"}:
        return "buyer hesitation"

    return cleaned or "buyer hesitation"



def _rw_quote_is_positive_reassurance_quote(quote: str) -> bool:
    lower = str(quote or "").lower().strip()
    if not lower:
        return False

    negative_markers = [
        "wrong size",
        "size is wrong",
        "stated size",
        "listed as",
        "what came was",
        "half size",
        "not sold by the single bottle",
        "only came in",
        "only came as",
        "received the regular size",
        "priced wrong",
        "not worth",
        "not really worth",
        "price is ridiculous",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
        "wateriest",
        "flavorless",
        "terrible",
        "bad taste",
        "broken",
        "missing",
        "leak",
        "leaked",
        "doesn't",
        "didn't",
    ]
    if any(marker in lower for marker in negative_markers):
        return False

    two_pack_reassurance = (
        any(marker in lower for marker in ["two-pack", "2-pack", "second bottle"])
        and any(marker in lower for marker in [
            "give the second bottle",
            "give one to",
            "friend",
            "gift",
            "appreciate",
            "thoughtfulness",
        ])
    )

    value_reassurance = any(marker in lower for marker in [
        "cannot beat the price",
        "can't beat the price",
        "worth the price",
        "value priced",
        "great value",
        "worth it",
        "worth every",
        "for this quality",
        "excellent quality",
        "high quality",
        "best balsamic",
        "elixir of the gods",
        "exceptional",
        "delicious",
        "amazing",
        "favorite",
        "love this",
        "i love",
    ])

    if ("pricy" in lower or "pricey" in lower) and "worth it" in lower:
        value_reassurance = True

    return two_pack_reassurance or value_reassurance


def _rw_quote_is_strong_positive_signal(quote: str) -> bool:
    lower = str(quote or "").lower().strip()
    if not lower:
        return False

    positive_terms = [
        "love it",
        "will continue to purchase",
        "continue to purchase",
        "best rootbeer",
        "best root beer",
        "order it frequently",
        "great flavor",
        "greater flavor",
        "smoother",
        "smother greater flavor",
        "not as sharp as barq",
        "worth the price",
        "cannot beat the price",
        "can't beat the price",
        "value priced",
    ]
    return any(term in lower for term in positive_terms)


def _rw_quote_is_low_value_objection(quote: str) -> bool:
    lower = str(quote or "").lower().strip()

    if len(lower) < 18:
        return True

    # Strong positive proof can contain words like "but" or "not" in comparisons,
    # but should not become a buyer objection unless there is a clearer complaint.
    if _rw_quote_is_strong_positive_signal(quote) and not any(term in lower for term in [
        "too expensive",
        "not worth",
        "overpriced",
        "wrong",
        "hard to",
        "difficult",
        "problem",
        "issue",
        "broken",
        "leaked",
        "missing",
    ]):
        return True

    # Positive reassurance / gifting / value proof should not be treated as a buyer objection.
    if _rw_quote_is_positive_reassurance_quote(quote) and not (
        ("pricy" in lower or "pricey" in lower or "expensive" in lower) and "worth it" in lower
    ):
        return True

    # Positive proof / usage praise should not be treated as a buyer objection.
    if "great for cooking" in lower and not any(term in lower for term in [
        "wrong",
        "half size",
        "not sold",
        "2-pack",
        "single bottle",
        "priced wrong",
        "flavorless",
        "terrible",
    ]):
        return True

    if lower.startswith(("but great", "and great", "so this is good")):
        return True

    return False


def _rw_label_is_low_quality_objection(label: str, quote: str) -> bool:
    cleaned = str(label or "").replace("objection:", "").strip().lower()
    cleaned = cleaned.rstrip(".:;!?")
    if cleaned not in {"hard", "good", "great", "love", "best"}:
        return False

    lower = str(quote or "").lower()
    negative_context = [
        "hard to",
        "too hard",
        "not good",
        "not great",
        "not love",
        "not the best",
        "difficult",
    ]
    return not any(term in lower for term in negative_context)


def _rw_refine_buyer_objection_summaries(themes):
    grouped: dict[str, list[str]] = {}
    exemplar_theme_by_label = {}

    for theme in _rw_compact_theme_summaries(themes):
        theme_label = getattr(theme, "label", "")
        quotes = getattr(theme, "evidence_quotes", []) or []

        for quote in quotes:
            if _rw_quote_is_low_value_objection(quote):
                continue

            refined_label = _rw_objection_label_from_quotes(theme_label, [quote])
            if refined_label.startswith("objection:"):
                refined_label = refined_label.replace("objection:", "").strip() or "buyer hesitation"

            if refined_label in {"but", "not", "wish", "wrong", "too", "however", "?"}:
                refined_label = "buyer hesitation"

            if _rw_label_is_low_quality_objection(refined_label, quote):
                continue

            grouped.setdefault(refined_label, [])
            if quote not in grouped[refined_label]:
                grouped[refined_label].append(quote)

            exemplar_theme_by_label.setdefault(refined_label, theme)

    refined = []
    for label, quotes in grouped.items():
        refined.append(
            _rw_rebuild_theme_summary(
                exemplar_theme_by_label[label],
                label=label,
                evidence_quotes=quotes[:2],
            )
        )

    return refined


def _rw_quote_matches_theme(label: str, value: str) -> bool:
    lower = str(value or "").lower()
    raw_label = str(label or "").strip().lower()
    phrase = _rw_human_theme_phrase(label).strip().lower()

    price_value_tradeoff = (
        ("pricy" in lower or "pricey" in lower or "expensive" in lower)
        and "worth it" in lower
    )
    if _rw_quote_is_positive_reassurance_quote(value) and not price_value_tradeoff and any(marker in raw_label or marker in phrase for marker in [
        "price / value",
        "price or value",
        "size / quantity",
        "quantity or size",
        "quantity / size",
        "expectation mismatch",
        "tradeoff",
        "hesitation",
        "quality consistency",
    ]):
        return False

    packaging_terms = [
        "no lid",
        "not lid",
        "without a lid",
        "lid to go over the spout",
        "air is ever present",
        "oxidation",
        "cap leaked",
        "bottle cap",
    ]
    size_label_terms = [
        "size / quantity",
        "quantity or size",
        "quantity / size",
        "size or quantity",
    ]
    packaging_label_terms = [
        "packaging / spout",
        "packaging or spout",
        "spout concern",
        "packaging / shipping",
    ]

    has_packaging_signal = any(term in lower for term in packaging_terms)
    is_size_label = any(term in raw_label or term in phrase for term in size_label_terms)
    is_packaging_label = any(term in raw_label or term in phrase for term in packaging_label_terms)

    if has_packaging_signal and is_size_label:
        return False
    if has_packaging_signal and is_packaging_label:
        return True

    positive_value_only_terms = [
        "worth the price",
        "cannot beat the price",
        "can't beat the price",
        "value priced",
        "great value",
        "good value",
        "for this quality",
    ]
    explicit_price_concern_terms = [
        "too expensive",
        "not worth",
        "overpriced",
        "pricey",
        "pricy",
        "priced wrong",
        "price is wrong",
    ]
    has_positive_value_only = any(term in lower for term in positive_value_only_terms)
    has_explicit_price_concern = any(term in lower for term in explicit_price_concern_terms)
    if has_positive_value_only and not has_explicit_price_concern and any(term in raw_label or term in phrase for term in [
        "price / value",
        "price or value",
        "expectation mismatch",
        "tradeoff",
        "hesitation",
        "size / quantity",
        "quantity or size",
        "quantity / size",
    ]):
        return False

    explicit_negative_terms = [
        "not worth",
        "not really worth",
        "price is ridiculous",
        "too expensive",
        "overpriced",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
    ]
    if any(term in lower for term in explicit_negative_terms) and any(term in raw_label or term in phrase for term in [
        "liked signal",
        "buyers calling it",
        "buyers saying they love",
        "positive",
        "great",
        "love",
        "perfect",
        "recommend",
    ]):
        return False

    rug_concern_terms = [
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "sliding",
        "slides",
        "slip around",
        "slips",
        "robot vacuum",
        "gets trapped",
        "too thick",
        "thick nature",
        "does not fit under",
        "doesn't fit under",
    ]
    if any(term in lower for term in rug_concern_terms) and any(term in raw_label or term in phrase for term in [
        "summer fabric comfort",
        "color expectation mismatch",
    ]):
        return False

    marker_groups = [
        (
            ("grip / slipping", "slipping concern"),
            ["move a lot", "moves a lot", "stick to the floor", "sliding", "slides", "slip around", "slips", "does not stay", "doesn't stay"],
        ),
        (
            ("thickness / robot vacuum", "robot vacuum tradeoff", "clearance tradeoff"),
            ["robot vacuum", "gets trapped", "get trapped", "too thick", "thick nature", "does not fit under", "doesn't fit under", "fit under doors", "under some doors"],
        ),
        (
            ("summer fabric comfort",),
            ["fabric", "breathable", "summer", "hot weather", "??", "???", "??", "??", "??", "??"],
        ),
        (
            ("price / value", "price or value", "price / value concern"),
            ["priced wrong", "price is wrong", "too expensive", "not worth", "overpriced", "pricy", "pricey", "cheaper", "expensive", "cost"],
        ),
        (
            ("taste / flavor", "taste or flavor", "quality consistency"),
            ["taste", "flavor", "flavour", "wateriest", "flavorless", "bland", "rich", "glaze", "vinaigrette", "ingredients"],
        ),
        (
            ("size / quantity", "quantity or size", "quantity / size"),
            ["wrong size", "size is wrong", "stated size", "quantity", "listed as", "what came was", "oz", "missing bottle", "pack count", "quantity mismatch", "half size", "regular size"],
        ),
        (
            ("packaging / spout", "packaging / shipping", "spout concern"),
            ["no lid", "not lid", "without a lid", "spout", "air is ever present", "oxidation", "cap leaked", "bottle cap"],
        ),
        (
            ("expectation mismatch", "tradeoff", "hesitation"),
            ["expected", "expectation", "however", "but", "concerned", "mismatch"],
        ),
        (
            ("liked signal", "great", "love", "useful", "easy", "recommend"),
            ["great", "love", "useful", "easy", "recommend", "worth", "quality", "cannot beat", "value priced"],
        ),
    ]

    for label_markers, quote_markers in marker_groups:
        if any(marker in raw_label or marker in phrase for marker in label_markers):
            return any(marker in lower for marker in quote_markers)

    return False


def _rw_theme_needs_matched_quote(label: str) -> bool:
    raw_label = str(label or "").strip().lower()
    phrase = _rw_human_theme_phrase(label).strip().lower()
    markers = [
        "price / value",
        "price or value",
        "taste / flavor",
        "taste or flavor",
        "size / quantity",
        "quantity or size",
        "quality consistency",
        "packaging / spout",
        "packaging / shipping",
        "spout concern",
        "grip / slipping",
        "slipping concern",
        "thickness / robot vacuum",
        "robot vacuum tradeoff",
        "summer fabric comfort",
        "expectation mismatch",
        "quantity / size",
    ]
    return any(marker in raw_label or marker in phrase for marker in markers)


def _rw_refine_theme_quotes(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    refined: list[ReviewThemeSummary] = []
    for theme in themes:
        quotes = list(getattr(theme, "evidence_quotes", []) or [])
        matched = [quote for quote in quotes if _rw_quote_matches_theme(theme.label, quote)]
        if matched:
            theme.evidence_quotes = matched[:3]
            theme.evidence_count = len(matched)
            refined.append(theme)
        elif not _rw_theme_needs_matched_quote(theme.label):
            refined.append(theme)
    return refined


def _rw_theme_first_quote(theme) -> str:
    quotes = getattr(theme, "evidence_quotes", []) or []
    if not quotes:
        return ""

    label = str(getattr(theme, "label", "") or "")
    cleaned_quotes = []
    for quote in quotes:
        value = quote
        if "def _rw_compact_evidence_quote" in globals():
            value = _rw_compact_evidence_quote(value)
        value = " ".join(str(value or "").split()).strip()
        if value:
            cleaned_quotes.append(value)

    for quote in cleaned_quotes:
        if _rw_quote_matches_theme(label, quote):
            return quote

    if _rw_theme_needs_matched_quote(label):
        return ""

    return cleaned_quotes[0] if cleaned_quotes else ""

def _rw_quote_snippet(value: str, max_len: int = 120) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""

    if len(text) <= max_len:
        return text

    cut = text[:max_len].rstrip()
    return cut.rstrip(" ,;:") + "..."


def _rw_human_theme_phrase(label: str) -> str:
    raw = str(label or "").strip()
    normalized = raw.replace("liked signal:", "").strip()

    mapping = {
        "size / quantity mismatch": "quantity or size mismatch",
        "taste / flavor concern": "taste or flavor concern",
        "price / value concern": "price or value concern",
        "packaging / spout concern": "packaging or spout concern",
        "packaging / shipping concern": "packaging or shipping concern",
        "quality consistency concern": "quality consistency concern",
        "color expectation mismatch": "color expectation mismatch",
        "sewing / quality control issue": "sewing or QC concern",
        "summer fabric comfort": "summer fabric comfort",
        "grip / slipping concern": "grip or slipping concern",
        "thickness / robot vacuum tradeoff": "thickness or robot-vacuum tradeoff",
        "leak / mess risk": "mess or spill concern",
        "hard to clean": "cleanup concern",
        "durability concern": "durability concern",
        "time saving": "time-saving benefit",
        "great": "buyers calling it great",
        "love": "buyers saying they love it",
        "useful": "buyers finding it useful",
        "easy": "buyers finding it easy",
        "liked signal: great": "buyers calling it great",
        "liked signal: love": "buyers saying they love it",
        "liked signal: useful": "buyers finding it useful",
        "liked signal: easy": "buyers finding it easy",
    }

    return mapping.get(raw, mapping.get(normalized, normalized or "buyer signal"))

def _rw_quote_has_pain_signal(value: str) -> bool:
    lower = str(value or "").lower()
    if _rw_quote_is_positive_reassurance_quote(value):
        return False

    pain_terms = [
        "wrong size",
        "stated size",
        "listed as",
        "what came was",
        "half size",
        "priced wrong",
        "not worth",
        "not really worth",
        "price is ridiculous",
        "move a lot",
        "moves a lot",
        "stick to the floor",
        "robot vacuum",
        "gets trapped",
        "wateriest",
        "flavorless",
        "terrible",
        "not super complex",
        "not sold",
        "2-pack",
        "single bottle",
        "no lid",
        "not lid",
        "without a lid",
        "lid to go over the spout",
        "air is ever present",
        "oxidation",
        "cap leaked",
        "bottle cap",
    ]
    return any(term in lower for term in pain_terms)

def _rw_hook_from_theme(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    label = _rw_human_theme_phrase(raw_label)
    quote = _rw_theme_first_quote(theme)
    lower = quote.lower()

    if raw_label == "price / value concern":
        return "The price looks good, but is the size/value actually clear? Watch this before you buy."

    if raw_label == "quality consistency concern":
        return "Would you cook with this every day? Check the quality concern buyers mention."

    if raw_label == "packaging / spout concern":
        return "Before you buy, check the bottle spout concern buyers mention."

    if raw_label == "taste / flavor concern":
        return "I tested this balsamic so you don't have to - here's the flavor warning buyers mention."

    if "listed as" in lower and "what came was" in lower:
        return "POV: you ordered one size, but the bottle that arrived tells a different story."

    if "half size" in lower or "wrong size" in lower or "stated size" in lower:
        return "Before you buy, check the size buyers are actually receiving."

    if "wateriest" in lower or "flavorless" in lower or "terrible" in lower:
        return "I tested this balsamic so you don't have to - here's the flavor warning buyers mention."

    if "priced wrong" in lower or "price" in lower or "cheaper" in lower:
        return "The price looks good, but is the value actually clear? Watch this before you buy."

    return f"Before you buy, check the {label} buyers are calling out."

def _rw_dedupe_text_items(items: list[str], limit: int = 6) -> list[str]:
    deduped: list[str] = []
    seen = set()

    for item in items:
        normalized = " ".join(str(item or "").lower().split())
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped

def _rw_positive_hook_from_theme(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    normalized = raw_label.replace("liked signal:", "").strip().lower()
    quote = _rw_theme_first_quote(theme)

    if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
        return f"Start with the buyer concern: \"{_rw_quote_snippet(quote, 90)}\""

    if normalized == "great":
        return "Buyers keep calling this great - here's the moment that proves why."

    if normalized == "love":
        return "People say they love this - here's the everyday use case behind it."

    if normalized == "useful":
        return "Buyers say this is useful - here's the problem it solves fast."

    if normalized == "easy":
        return "Buyers say this feels easy - here's the moment that makes it click."

    label = _rw_human_theme_phrase(raw_label)
    if normalized in {"positive value signal", "value signal", "value proof"}:
        if quote:
            return f"Use the value proof as the payoff: \"{_rw_quote_snippet(quote, 90)}\""
        return "Use the value proof as the payoff before the CTA."
    if label.lower().startswith("buyers "):
        return f"Use this positive review proof: \"{_rw_quote_snippet(quote, 90)}\""
    return f"Buyers keep mentioning {label} - here's the proof moment."



def _rw_positive_hook_from_theme_zh(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    quote = _rw_quote_snippet(_rw_theme_first_quote(theme), 72)
    lower_quote = quote.lower()
    label = _rw_output_theme_label(raw_label, "zh-CN")

    if quote:
        if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
            return f"\u5148\u770b\u8fd9\u6761\u4e70\u5bb6\u987e\u8651\uff1a\u201c{quote}\u201d"
        if "cannot beat the price" in lower_quote or "worth it" in lower_quote or "pricy" in lower_quote or "pricey" in lower_quote:
            return f"\u8fd9\u74f6\u9999\u918b\u8d35\u4e00\u70b9\u4e5f\u6709\u4eba\u8bf4\u503c\uff1f\u5148\u770b\u8fd9\u53e5\u4e70\u5bb6\u539f\u8bdd\uff1a\u201c{quote}\u201d"

        if "elixir of the gods" in lower_quote or "best balsamic" in lower_quote or "best balsamic vinegar" in lower_quote:
            return f"\u4e3a\u4ec0\u4e48\u6709\u4e70\u5bb6\u628a\u8fd9\u74f6\u9999\u918b\u5938\u5230\u8fd9\u79cd\u7a0b\u5ea6\uff1f\u5148\u770b\u8fd9\u53e5\u539f\u8bdd\uff1a\u201c{quote}\u201d"

        if "two-pack" in lower_quote or "2-pack" in lower_quote or "second bottle" in lower_quote:
            return f"\u4e24\u74f6\u88c5\u4e0d\u53ea\u662f\u591a\u4e70\u4e00\u74f6\uff1f\u8fd9\u53e5\u4e70\u5bb6\u539f\u8bdd\u7ed9\u4e86\u4e00\u4e2a\u9001\u793c\u89d2\u5ea6\uff1a\u201c{quote}\u201d"

        if "love" in lower_quote or "favorite" in lower_quote or "delicious" in lower_quote or "amazing" in lower_quote:
            return f"\u4e70\u5bb6\u4e3a\u4ec0\u4e48\u4f1a\u559c\u6b22\u5b83\uff1f\u5148\u7528\u8fd9\u53e5\u539f\u8bdd\u5f00\u573a\uff1a\u201c{quote}\u201d"

        return f"\u8fd9\u6761\u6b63\u5411\u8bc1\u636e\u53ef\u4ee5\u76f4\u63a5\u53d8\u6210\u5e7f\u544a\u5f00\u5934\uff1a\u201c{quote}\u201d"

    if "\u559c\u6b22" in label:
        return "\u4e70\u5bb6\u4e3a\u4ec0\u4e48\u4f1a\u559c\u6b22\u5b83\uff1f\u5148\u7528\u4e00\u6761\u5177\u4f53\u8bc4\u8bba\u5f00\u573a\u3002"

    if "\u63a8\u8350" in label:
        return "\u4e3a\u4ec0\u4e48\u4e70\u5bb6\u613f\u610f\u63a8\u8350\u5b83\uff1f\u5148\u770b\u8bc4\u8bba\u91cc\u7684\u4f7f\u7528\u573a\u666f\u3002"

    return f"\u8fd9\u6761\u6b63\u5411\u8bc1\u636e\u80fd\u600e\u4e48\u53d8\u6210\u5e7f\u544a\u5f00\u5934\uff1f\u5148\u770b\u4e00\u6761\u5177\u4f53\u4e70\u5bb6\u539f\u8bdd\uff1a{label}"

def _rw_unique_themes_by_first_quote(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    unique: list[ReviewThemeSummary] = []
    seen_quotes = set()

    for theme in themes or []:
        quote = _rw_theme_first_quote(theme)
        key = " ".join(quote.lower().split()) if quote else f"label:{getattr(theme, 'label', '')}"
        if not key or key in seen_quotes:
            continue

        seen_quotes.add(key)
        unique.append(theme)

    return unique


def _rw_unique_theme_evidence_across_themes(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    unique: list[ReviewThemeSummary] = []
    seen_quotes = set()

    for theme in themes or []:
        quotes: list[str] = []
        for quote in getattr(theme, "evidence_quotes", []) or []:
            key = " ".join(str(quote or "").lower().split())
            if not key or key in seen_quotes:
                continue

            seen_quotes.add(key)
            quotes.append(quote)

        if quotes:
            unique.append(_rw_rebuild_theme_summary(theme, evidence_quotes=quotes))

    return unique

def _rw_hooks(common_pain_points: list[ReviewThemeSummary], liked_points: list[ReviewThemeSummary], language: str) -> list[str]:
    is_zh = language == "zh-CN"
    hooks: list[str] = []

    for theme in common_pain_points[:4]:
        label = _rw_output_theme_label(theme.label, language)
        if is_zh:
            hooks.append(f"\u4e70\u4e4b\u524d\u5148\u770b\u6e05\u695a\u8fd9\u4e2a\u95ee\u9898\uff1a{label}")
        else:
            hooks.append(_rw_hook_from_theme(theme))

    for theme in _rw_unique_themes_by_first_quote(liked_points):
        quote = _rw_theme_first_quote(theme)
        if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
            continue
        if is_zh:
            hooks.append(_rw_positive_hook_from_theme_zh(theme))
        else:
            hooks.append(_rw_positive_hook_from_theme(theme))
        if len(hooks) >= 6:
            break

    if not hooks:
        hooks.append(
            "\u5148\u7528\u6700\u5177\u4f53\u7684\u4e70\u5bb6\u539f\u8bdd\u5f00\u573a\uff0c\u518d\u5c55\u793a\u4ea7\u54c1\u5982\u4f55\u56de\u5e94\u8fd9\u4e2a\u573a\u666f\u3002"
            if is_zh
            else "Start with the most specific buyer quote, then show the product moment that resolves it."
        )

    return _rw_dedupe_text_items(hooks, 6)

def _rw_first_available_theme(*theme_groups: list[ReviewThemeSummary]) -> ReviewThemeSummary | None:
    for group in theme_groups:
        if group:
            return group[0]
    return None


def _rw_workspace_product_hint(payload: ReviewWorkspaceRequest, language: str) -> str:
    for product in payload.products or []:
        for attr in ("title", "brand", "description"):
            value = _rw_text(getattr(product, attr, ""))
            if value:
                return _rw_clean_workspace_product_phrase(value, language)

    return "\u8fd9\u4e2a\u5546\u54c1" if language == "zh-CN" else "the product"


def _rw_clean_workspace_product_phrase(value: str, language: str) -> str:
    text = _rw_text(value).replace("...", "").strip(" -_,;:")
    if not text:
        return "\u8fd9\u4e2a\u5546\u54c1" if language == "zh-CN" else "the product"

    root_beer_match = re.search(r"\b(?:[A-Za-z0-9'&.-]+\s+){0,4}root\s*beer\b", text, re.IGNORECASE)
    if root_beer_match:
        return _rw_text(root_beer_match.group(0))

    first_phrase = re.split(r"[,|:;(\[]", text, maxsplit=1)[0].strip(" -_,;:")
    if not first_phrase:
        first_phrase = text

    words = first_phrase.split()
    if len(first_phrase) > 52 and len(words) > 6:
        first_phrase = " ".join(words[:6])

    return first_phrase or ("\u8fd9\u4e2a\u5546\u54c1" if language == "zh-CN" else "the product")


def _rw_signal_lines(
    themes: list[ReviewThemeSummary],
    language: str,
    prefix_en: str,
    prefix_zh: str,
    limit: int = 3,
) -> list[str]:
    lines: list[str] = []
    is_zh = language == "zh-CN"
    for theme in themes[:limit]:
        label = _rw_output_theme_label(theme.label, language)
        quote = _rw_quote_snippet(_rw_theme_first_quote(theme), 100)
        prefix = prefix_zh if is_zh else prefix_en
        if quote:
            lines.append(f"{prefix}: {label} - \"{quote}\"")
        else:
            lines.append(f"{prefix}: {label}")
    return lines


def _rw_sample_interpretation(
    payload: ReviewWorkspaceRequest,
    rows: list[dict],
    high_signal_rows: list[dict],
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
) -> ReviewSampleInterpretation:
    language = payload.output_language
    is_zh = language == "zh-CN"
    product_count = len(payload.products)
    review_count = len(rows)
    raw_review_count = _rw_raw_review_count(payload)
    duplicate_review_count = max(0, raw_review_count - review_count)
    high_signal_count = len(high_signal_rows)

    strongest_signals: list[str] = []
    strongest_signals.extend(_rw_signal_lines(common_pain_points, language, "Pain signal", "\u75db\u70b9\u4fe1\u53f7", 2))
    strongest_signals.extend(_rw_signal_lines(buyer_objections, language, "Buyer objection", "\u8d2d\u4e70\u987e\u8651", 2))
    strongest_signals.extend(_rw_signal_lines(liked_points, language, "Positive proof", "\u6b63\u5411\u8bc1\u636e", 2))
    strongest_signals.extend(_rw_signal_lines(use_cases, language, "Use case", "\u4f7f\u7528\u573a\u666f", 1))

    if not strongest_signals:
        strongest_signals = [
            "\u5f53\u524d\u53ef\u89c1\u8bc4\u8bba\u6837\u672c\u8f83\u5c0f\uff0c\u5efa\u8bae\u5148\u7528\u4e8e\u521b\u610f\u65b9\u5411\u53c2\u8003\u3002"
            if is_zh
            else "The current visible review sample is small, so use it as creative direction input first."
        ]

    if is_zh:
        sample_type = "Amazon \u5f53\u524d\u53ef\u89c1\u9875\u9762\u8bc4\u8bba\u6837\u672c"
        sample_size_note = (
            f"\u5f53\u524d\u6837\u672c\u5305\u542b {product_count} \u4e2a\u5546\u54c1\u3001{raw_review_count} \u6761\u53ef\u89c1\u8bc4\u8bba\uff1b"
            f"\u53bb\u91cd\u540e {review_count} \u6761\u8fdb\u5165\u5206\u6790\uff0c{duplicate_review_count} \u6761\u4e3a\u91cd\u590d\u8bc4\u8bba\u3002"
            f"\u5176\u4e2d {high_signal_count} \u6761\u88ab\u8bc6\u522b\u4e3a\u9ad8\u4fe1\u53f7\u8bc4\u8bba\u3002"
            "\u8fd9\u4e2a\u6837\u672c\u9002\u5408\u505a\u521b\u610f\u4fe1\u53f7\uff0c\u4e0d\u9002\u5408\u5f53\u4f5c\u5b8c\u6574\u8bc4\u8bba\u7edf\u8ba1\u3002"
        )
        suitable_for = [
            "\u63d0\u53d6\u4e70\u5bb6\u539f\u8bdd",
            "\u627e\u77ed\u89c6\u9891 hook",
            "\u53d1\u73b0\u8d2d\u4e70\u987e\u8651",
            "\u63d0\u70bc\u6b63\u5411\u8bc1\u636e",
            "\u751f\u6210\u4f7f\u7528\u573a\u666f\u548c\u811a\u672c\u65b9\u5411",
        ]
        not_suitable_for = [
            "\u63a8\u65ad\u5b8c\u6574\u5dee\u8bc4\u7387",
            "\u4ee3\u8868\u5168\u90e8\u4e70\u5bb6\u6ee1\u610f\u5ea6",
            "\u4f5c\u4e3a\u5b8c\u6574\u5e02\u573a\u7814\u7a76\u6837\u672c",
            "\u5224\u65ad\u5168\u90e8 Amazon \u8bc4\u8bba\u7684\u7edf\u8ba1\u7ed3\u8bba",
        ]
        recommended_directions = [
            "\u5148\u7528\u6700\u5f3a\u75db\u70b9\u4fe1\u53f7\u751f\u6210\u5f00\u5934 hook\u3002",
            "\u7528\u4e70\u5bb6\u539f\u8bdd\u4f5c\u4e3a\u5c4f\u5e55\u5b57\u5e55\u6216\u53e3\u64ad\u5f00\u573a\u3002",
            "\u5728\u811a\u672c\u540e\u6bb5\u52a0\u5165\u6b63\u5411\u8bc1\u636e\uff0c\u907f\u514d\u53ea\u653e\u5927\u8d1f\u9762\u4fe1\u53f7\u3002",
        ]
        use_case_count = _rw_unique_quote_count(use_cases)
        evidence_usage_summary = [
            f"\u75db\u70b9\u8bc1\u636e\uff1a{sum(item.evidence_count for item in common_pain_points)} \u6761\u4fe1\u53f7",
            f"\u8d2d\u4e70\u987e\u8651\uff1a{sum(item.evidence_count for item in buyer_objections)} \u6761\u4fe1\u53f7",
            f"\u6b63\u5411\u8bc1\u636e\u8bc4\u8bba\uff1a{_rw_unique_quote_count(liked_points)} \u6761\u8bc4\u8bba",
            (
                f"\u4f7f\u7528\u573a\u666f\u8bc4\u8bba\uff1a{use_case_count} \u6761\u8bc4\u8bba"
                if use_case_count
                else "\u4f7f\u7528\u573a\u666f\u8bc4\u8bba\uff1a\u5f53\u524d\u6837\u672c\u672a\u8bc6\u522b\u5230\u660e\u786e\u4f7f\u7528\u573a\u666f\u8bc4\u8bba"
            ),
        ]
    else:
        sample_type = "Amazon visible-page review sample"
        sample_size_note = (
            f"This sample contains {product_count} product(s) and {raw_review_count} visible review(s); "
            f"after dedupe, {review_count} review(s) entered analysis and {duplicate_review_count} duplicate review(s) were excluded. "
            f"{high_signal_count} review(s) were identified as high-signal. Use it for creative signals, not full review statistics."
        )
        suitable_for = [
            "extracting buyer wording",
            "finding short-form video hooks",
            "spotting buyer objections",
            "finding positive proof",
            "generating use-case and script directions",
        ]
        not_suitable_for = [
            "estimating the full negative review rate",
            "representing all buyer satisfaction",
            "serving as a complete market research sample",
            "making full Amazon review population claims",
        ]
        recommended_directions = [
            "Use the strongest pain signal as the opening hook.",
            "Turn buyer wording into on-screen text or voiceover.",
            "Add positive proof near the payoff so the script does not only amplify negative signals.",
        ]
        use_case_count = _rw_unique_quote_count(use_cases)
        evidence_usage_summary = [
            f"Pain evidence: {sum(item.evidence_count for item in common_pain_points)} signal(s)",
            f"Buyer objections: {sum(item.evidence_count for item in buyer_objections)} signal(s)",
            f"Positive proof reviews: {_rw_unique_quote_count(liked_points)} review(s)",
            (
                f"Use case reviews: {use_case_count} review(s)"
                if use_case_count
                else "Use case reviews: no explicit use-case reviews were identified in this visible sample."
            ),
        ]

    return ReviewSampleInterpretation(
        sample_type=sample_type,
        sample_size_note=sample_size_note,
        suitable_for=suitable_for,
        not_suitable_for=not_suitable_for,
        strongest_signals=_rw_dedupe_text_items(strongest_signals, 6),
        recommended_creative_directions=recommended_directions,
        evidence_usage_summary=evidence_usage_summary,
    )


def _paste_clean_line(line: str) -> str:
    return " ".join(str(line or "").replace("\u00a0", " ").split())


def _paste_is_meta_line(line: str) -> bool:
    lowered = line.lower().strip()
    if not lowered:
        return True
    if lowered.startswith(_REVIEW_PASTE_META_PREFIXES):
        return True
    if "verified purchase" in lowered:
        return True
    if "found this helpful" in lowered:
        return True
    if lowered in {"read more", "show more", "see more", "customer reviews"}:
        return True
    return False


def _paste_high_signal_score(review: ReviewWorkspaceReview) -> int:
    text = _paste_clean_line(review.text)
    lowered = text.lower()
    if len(text) < 18:
        return 0

    score = 1
    try:
        rating = float(str(review.rating).split()[0]) if review.rating not in (None, "") else None
    except (TypeError, ValueError):
        rating = None

    if rating is not None and rating <= 3:
        score += 3
    if rating is not None and rating >= 4:
        score += 1
    if review.helpful_count:
        score += min(3, int(review.helpful_count) // 5 + 1)
    if any(marker in lowered for marker in ["but", "wish", "too", "not", "hard", "difficult", "problem", "issue", "leak", "broke", "mess"]):
        score += 3
    if any(marker in lowered for marker in ["love", "great", "easy", "perfect", "works", "useful", "recommend"]):
        score += 2
    if len(text) >= 80:
        score += 2
    return score


def _parse_helpful_count(line: str) -> int | None:
    match = re.search(r"(\d+)\s+people\s+found\s+this\s+helpful", line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"one\s+person\s+found\s+this\s+helpful", line, re.IGNORECASE):
        return 1
    return None


def _finalize_pasted_review(
    reviews: list[ReviewWorkspaceReview],
    rating,
    title: str,
    body_lines: list[str],
    helpful_count: int | None,
    source_section: str,
):
    body = _paste_clean_line(" ".join(body_lines))
    title = _paste_clean_line(title)

    if not body and title:
        body = title
        title = ""

    if len(body) < 10:
        return

    reviews.append(
        ReviewWorkspaceReview(
            rating=rating,
            title=title,
            text=body,
            helpful_count=helpful_count,
            source_section=source_section,
        )
    )


def _parse_messy_reviews(raw_text: str, source_section: str) -> list[ReviewWorkspaceReview]:
    lines = [_paste_clean_line(line) for line in str(raw_text or "").splitlines()]
    lines = [line for line in lines if line]

    reviews: list[ReviewWorkspaceReview] = []
    current_rating = None
    current_title = ""
    current_body: list[str] = []
    current_helpful = None
    active = False

    for line in lines:
        helpful = _parse_helpful_count(line)
        if helpful is not None:
            current_helpful = helpful
            continue

        rating_match = _REVIEW_PASTE_RATING_RE.search(line)
        if rating_match:
            if active:
                _finalize_pasted_review(
                    reviews,
                    current_rating,
                    current_title,
                    current_body,
                    current_helpful,
                    source_section,
                )

            active = True
            current_rating = rating_match.group("rating")
            remainder = _paste_clean_line(_REVIEW_PASTE_RATING_RE.sub("", line, count=1))
            current_title = remainder if len(remainder) <= 90 else ""
            current_body = [] if current_title else ([remainder] if remainder else [])
            current_helpful = None
            continue

        if _paste_is_meta_line(line):
            continue

        if active:
            if not current_title and len(line) <= 90 and not current_body:
                current_title = line
            else:
                current_body.append(line)
        else:
            # Generic non-Amazon paste fallback: each meaningful paragraph can be a review.
            if len(line) >= 30:
                reviews.append(
                    ReviewWorkspaceReview(
                        rating=None,
                        title="",
                        text=line,
                        helpful_count=None,
                        source_section=source_section,
                    )
                )

    if active:
        _finalize_pasted_review(
            reviews,
            current_rating,
            current_title,
            current_body,
            current_helpful,
            source_section,
        )

    # Deduplicate while preserving order.
    deduped: list[ReviewWorkspaceReview] = []
    seen = set()
    for review in reviews:
        key = _paste_clean_line(review.text).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(review)

    return deduped





# L-review-workspace-output-quality-polish
def _rw_unique_quote_count(themes: list[ReviewThemeSummary]) -> int:
    seen = set()
    for theme in themes or []:
        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = " ".join(compact.lower().split())
            if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(compact):
                continue
            if key:
                seen.add(key)
    return len(seen)


def _rw_positive_theme_label_from_quote(quote: str, fallback_label: str = "") -> str:
    lower = str(quote or "").lower()
    fallback = str(fallback_label or "").replace("liked signal:", "").strip().lower()

    if "will continue to purchase" in lower or "continue to purchase" in lower or "order it frequently" in lower:
        return "repeat purchase intent"

    if "best rootbeer" in lower or "best root beer" in lower or "absolute best root beer" in lower:
        return "best root beer praise"

    if "barq" in lower or "a&w" in lower or "smoother" in lower or "smother" in lower or "greater flavor" in lower:
        return "root beer flavor comparison"

    if "great flavor" in lower or "smooth" in lower:
        return "flavor praise"

    if (
        "worth the price" in lower
        or "cannot beat the price" in lower
        or "can't beat the price" in lower
        or "value priced" in lower
        or "worth it" in lower
    ):
        return "positive value signal"

    if "love" in lower or fallback == "love":
        return "buyers saying they love it"

    if "great" in lower or fallback == "great":
        return "buyers calling it great"

    if "_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(quote):
        return "buyer concern signal"

    if fallback:
        return f"liked signal: {fallback}"

    return "positive proof"


def _rw_refine_liked_point_summaries(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    grouped: dict[str, list[str]] = {}
    seen_quotes = set()

    for theme in _rw_unique_theme_evidence_across_themes(_rw_compact_theme_summaries(themes)):
        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = " ".join(compact.lower().split())
            if not key or key in seen_quotes:
                continue

            seen_quotes.add(key)
            label = _rw_positive_theme_label_from_quote(compact, getattr(theme, "label", ""))
            grouped.setdefault(label, []).append(compact)

    refined: list[ReviewThemeSummary] = []
    for label, quotes in grouped.items():
        refined.append(
            ReviewThemeSummary(
                label=label,
                evidence_count=len(quotes),
                evidence_quotes=quotes[:3],
            )
        )

    return refined


def _rw_use_case_label_from_quote(quote: str, fallback_label: str = "") -> str:
    lower = str(quote or "").lower()

    if "west coast" in lower or "not available" in lower or "unavailable" in lower:
        return "regional availability context"

    if "gift" in lower or "friend" in lower or "give the second bottle" in lower:
        return "gift use case"

    if "daily" in lower or "morning" in lower or "every day" in lower:
        return "daily use context"

    if "party" in lower or "guests" in lower:
        return "party or hosting context"

    if "fridge" in lower or "refrigerator" in lower or "stock" in lower or "pack" in lower:
        return "stocking or pack context"

    return "usage context"


def _rw_quote_is_real_use_case(quote: str, label: str = "") -> bool:
    lower = str(quote or "").lower()

    if _rw_quote_is_strong_positive_signal(quote) and not any(term in lower for term in [
        "west coast",
        "not available",
        "unavailable",
        "gift",
        "friend",
        "daily",
        "morning",
        "party",
        "guests",
        "fridge",
        "refrigerator",
        "pack",
        "stock",
    ]):
        return False

    if str(label or "").strip().lower() == "use case: for" and not any(term in lower for term in [
        "for party",
        "for guests",
        "for daily",
        "for cooking",
        "for salads",
        "for gift",
        "for the fridge",
    ]):
        return False

    return any(term in lower for term in [
        "west coast",
        "not available",
        "unavailable",
        "gift",
        "friend",
        "daily",
        "morning",
        "party",
        "guests",
        "fridge",
        "refrigerator",
        "pack",
        "stock",
        "for cooking",
        "for salads",
    ])


def _rw_refine_use_case_summaries(themes: list[ReviewThemeSummary]) -> list[ReviewThemeSummary]:
    grouped: dict[str, list[str]] = {}
    seen_quotes = set()

    for theme in _rw_compact_theme_summaries(themes):
        for quote in getattr(theme, "evidence_quotes", []) or []:
            compact = _rw_compact_evidence_quote(quote)
            key = " ".join(compact.lower().split())
            if not key or key in seen_quotes:
                continue
            if not _rw_quote_is_real_use_case(compact, getattr(theme, "label", "")):
                continue

            seen_quotes.add(key)
            label = _rw_use_case_label_from_quote(compact, getattr(theme, "label", ""))
            grouped.setdefault(label, []).append(compact)

    refined: list[ReviewThemeSummary] = []
    for label, quotes in grouped.items():
        refined.append(
            ReviewThemeSummary(
                label=label,
                evidence_count=len(quotes),
                evidence_quotes=quotes[:2],
            )
        )

    return refined


def _rw_human_theme_phrase(label: str) -> str:
    raw = str(label or "").strip()
    normalized = raw.replace("liked signal:", "").strip()

    mapping = {
        "size / quantity mismatch": "quantity or size mismatch",
        "taste / flavor concern": "taste or flavor concern",
        "price / value concern": "price or value concern",
        "packaging / spout concern": "packaging or spout concern",
        "packaging / shipping concern": "packaging or shipping concern",
        "quality consistency concern": "quality consistency concern",
        "color expectation mismatch": "color expectation mismatch",
        "sewing / quality control issue": "sewing or QC concern",
        "summer fabric comfort": "summer fabric comfort",
        "grip / slipping concern": "grip or slipping concern",
        "thickness / robot vacuum tradeoff": "thickness or robot-vacuum tradeoff",
        "leak / mess risk": "mess or spill concern",
        "hard to clean": "cleanup concern",
        "durability concern": "durability concern",
        "time saving": "time-saving benefit",
        "repeat purchase intent": "repeat purchase intent",
        "best root beer praise": "best root beer praise",
        "root beer flavor comparison": "root beer flavor comparison",
        "flavor praise": "flavor praise",
        "positive value signal": "positive value signal",
        "regional availability context": "regional availability context",
        "gift use case": "gift use case",
        "daily use context": "daily use context",
        "party or hosting context": "party or hosting context",
        "stocking or pack context": "stocking or pack context",
        "usage context": "usage context",
        "great": "buyers calling it great",
        "love": "buyers saying they love it",
        "useful": "buyers finding it useful",
        "easy": "buyers finding it easy",
        "liked signal: great": "buyers calling it great",
        "liked signal: love": "buyers saying they love it",
        "liked signal: useful": "buyers finding it useful",
        "liked signal: easy": "buyers finding it easy",
    }

    return mapping.get(raw, mapping.get(normalized, normalized or "buyer signal"))


def _rw_output_theme_label(label: str, language: str) -> str:
    phrase = _rw_human_theme_phrase(label)
    if language != "zh-CN":
        return phrase

    normalized = str(label or "").strip().lower()
    phrase_key = phrase.strip().lower()
    zh_labels = {
        "price / value concern": "\u4ef7\u683c / \u4ef7\u503c\u987e\u8651",
        "price or value concern": "\u4ef7\u683c / \u4ef7\u503c\u987e\u8651",
        "packaging / spout concern": "\u5305\u88c5 / \u74f6\u5634\u987e\u8651",
        "packaging or spout concern": "\u5305\u88c5 / \u74f6\u5634\u987e\u8651",
        "packaging / shipping concern": "\u5305\u88c5 / \u8fd0\u8f93\u987e\u8651",
        "packaging or shipping concern": "\u5305\u88c5 / \u8fd0\u8f93\u987e\u8651",
        "taste / flavor concern": "\u5473\u9053 / \u98ce\u5473\u987e\u8651",
        "taste or flavor concern": "\u5473\u9053 / \u98ce\u5473\u987e\u8651",
        "size / quantity mismatch": "\u89c4\u683c / \u6570\u91cf\u4e0d\u4e00\u81f4",
        "quantity or size mismatch": "\u89c4\u683c / \u6570\u91cf\u4e0d\u4e00\u81f4",
        "quality consistency concern": "\u54c1\u8d28\u7a33\u5b9a\u6027\u987e\u8651",
        "color expectation mismatch": "\u989c\u8272 / \u8272\u5dee\u9884\u671f",
        "sewing / quality control issue": "\u7f1d\u5236 / \u8d28\u68c0\u95ee\u9898",
        "summer fabric comfort": "\u590f\u5b63\u9762\u6599\u8212\u9002\u5ea6",
        "quantity / size uncertainty": "\u6570\u91cf / \u89c4\u683c\u4e0d\u786e\u5b9a",
        "expectation mismatch": "\u9884\u671f\u4e0d\u4e00\u81f4",
        "price / value uncertainty": "\u4ef7\u683c / \u4ef7\u503c\u4e0d\u786e\u5b9a",
        "tradeoff / hesitation": "\u53d6\u820d / \u72b9\u8c6b",
        "buyers saying they love it": "\u4e70\u5bb6\u8868\u793a\u559c\u6b22",
        "buyers calling it great": "\u4e70\u5bb6\u8ba4\u4e3a\u4f53\u9a8c\u5f88\u597d",
        "buyers finding it useful": "\u4e70\u5bb6\u8ba4\u4e3a\u6709\u7528",
        "buyers finding it easy": "\u4e70\u5bb6\u8ba4\u4e3a\u5bb9\u6613\u4f7f\u7528",
        "repeat purchase intent": "\u6301\u7eed\u590d\u8d2d / \u613f\u610f\u7ee7\u7eed\u8d2d\u4e70",
        "best root beer praise": "\u6700\u4f73\u53e3\u5473\u8bc4\u4ef7",
        "root beer flavor comparison": "\u98ce\u5473\u5bf9\u6bd4 / \u66f4\u987a\u6ed1\u53e3\u5473",
        "flavor praise": "\u98ce\u5473\u597d\u8bc4",
        "positive value signal": "\u6b63\u5411\u4ef7\u503c\u4fe1\u53f7",
        "regional availability context": "\u5730\u533a\u7a00\u7f3a / \u5f53\u5730\u4e70\u4e0d\u5230",
        "gift use case": "\u9001\u793c\u573a\u666f",
        "daily use context": "\u65e5\u5e38\u996e\u7528\u573a\u666f",
        "party or hosting context": "\u805a\u4f1a / \u62db\u5f85\u573a\u666f",
        "stocking or pack context": "\u56e4\u8d27 / \u5305\u88c5\u573a\u666f",
        "usage context": "\u4f7f\u7528\u573a\u666f",
        "buyer concern signal": "\u8d2d\u4e70\u987e\u8651\u4fe1\u53f7",
        "recommend": "\u4e70\u5bb6\u613f\u610f\u63a8\u8350",
        "perfect": "\u4e70\u5bb6\u8ba4\u4e3a\u8868\u73b0\u5f88\u597d",
        "great": "\u4e70\u5bb6\u8ba4\u4e3a\u4f53\u9a8c\u5f88\u597d",
        "love": "\u4e70\u5bb6\u8868\u793a\u559c\u6b22",
    }
    return zh_labels.get(normalized) or zh_labels.get(phrase_key) or phrase


def _rw_creative_angles(
    common_pain_points: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    language: str = "en",
    buyer_objections: list[ReviewThemeSummary] | None = None,
) -> list[str]:
    is_zh = language == "zh-CN"
    primary_signals = common_pain_points or (buyer_objections or [])
    positive_signals = [
        theme for theme in _rw_unique_themes_by_first_quote(liked_points)
        if not ("_rw_quote_has_pain_signal" in globals() and _rw_quote_has_pain_signal(_rw_theme_first_quote(theme)))
    ]
    angles: list[str] = []

    primary = primary_signals[0] if primary_signals else None
    primary_label = _rw_output_theme_label(primary.label, language) if primary else ("\u4e70\u5bb6\u987e\u8651" if is_zh else "buyer concern")
    primary_quote = _rw_quote_snippet(_rw_theme_first_quote(primary), 120) if primary else ""

    repeat = next((theme for theme in positive_signals if "repeat purchase" in _rw_human_theme_phrase(theme.label).lower()), None)
    flavor = next((theme for theme in positive_signals if "flavor" in _rw_human_theme_phrase(theme.label).lower() or "root beer" in _rw_human_theme_phrase(theme.label).lower()), None)
    scarcity = next((theme for theme in positive_signals if "regional" in _rw_human_theme_phrase(theme.label).lower()), None)

    if is_zh:
        if primary:
            if repeat:
                repeat_quote = _rw_quote_snippet(_rw_theme_first_quote(repeat), 110)
                angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u5148\u627f\u8ba4{primary_label}\uff0c\u7528\u4e70\u5bb6\u539f\u8bdd\u201c{primary_quote}\u201d\u5f00\u573a\uff0c\u518d\u7528\u590d\u8d2d\u8bc1\u636e\u201c{repeat_quote}\u201d\u56de\u6536\u4fe1\u4efb\u3002")
            else:
                angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u5148\u627f\u8ba4{primary_label}\uff0c\u7528\u4e70\u5bb6\u539f\u8bdd\u201c{primary_quote}\u201d\u5f00\u573a\uff0c\u518d\u7ed9\u51fa\u4e00\u4e2a\u771f\u5b9e\u9009\u62e9/\u4f7f\u7528\u573a\u666f\u3002")

        if flavor:
            flavor_quote = _rw_quote_snippet(_rw_theme_first_quote(flavor), 120)
            angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u628a\u5b83\u62cd\u6210 root beer \u98ce\u5473\u5bf9\u6bd4\uff0c\u4e0d\u53ea\u8bf4\u597d\u559d\uff0c\u800c\u662f\u7528\u539f\u8bdd\u201c{flavor_quote}\u201d\u89e3\u91ca\u548c Barq's / A&W \u7684\u5dee\u5f02\u3002")

        if scarcity:
            scarcity_quote = _rw_quote_snippet(_rw_theme_first_quote(scarcity), 110)
            angles.append(f"\u521b\u610f\u65b9\u5411\uff1a\u5f3a\u8c03\u5730\u533a\u7a00\u7f3a\u6216\u4e0d\u5bb9\u6613\u4e70\u5230\uff0c\u7528\u201c{scarcity_quote}\u201d\u505a\u61c2\u7684\u4eba\u624d\u61c2\u7684\u5f00\u573a\u3002")
    else:
        if primary:
            if repeat:
                repeat_quote = _rw_quote_snippet(_rw_theme_first_quote(repeat), 110)
                angles.append(f"Copy-ready angle: Acknowledge the {primary_label} with \"{primary_quote},\" then recover trust with repeat-purchase proof: \"{repeat_quote}.\"")
            else:
                angles.append(f"Copy-ready angle: Acknowledge the {primary_label} with \"{primary_quote},\" then show the real selection or usage context.")
        if flavor:
            flavor_quote = _rw_quote_snippet(_rw_theme_first_quote(flavor), 120)
            angles.append(f"Copy-ready angle: Turn it into a root beer taste comparison, using \"{flavor_quote}\" to explain the Barq's / A&W difference.")
        if scarcity:
            scarcity_quote = _rw_quote_snippet(_rw_theme_first_quote(scarcity), 110)
            angles.append(f"Copy-ready angle: Lean into regional scarcity or hard-to-find appeal with \"{scarcity_quote}.\"")

    if not angles:
        angles.append(
            "\u521b\u610f\u65b9\u5411\uff1a\u7528\u6700\u5177\u4f53\u7684\u4e70\u5bb6\u539f\u8bdd\u5f00\u573a\uff0c\u518d\u628a\u6b63\u5411\u8bc1\u636e\u653e\u5728\u7ed3\u5c3e\u505a\u4fe1\u4efb\u56de\u6536\u3002"
            if is_zh
            else "Copy-ready angle: Open with the most specific buyer quote, then use positive proof as the trust payoff."
        )

    return angles[:3]


def _rw_video_script_pack(
    payload: ReviewWorkspaceRequest,
    common_pain_points: list[ReviewThemeSummary],
    buyer_objections: list[ReviewThemeSummary],
    liked_points: list[ReviewThemeSummary],
    use_cases: list[ReviewThemeSummary],
    hooks: list[str],
) -> ReviewVideoScriptPack:
    language = payload.output_language
    is_zh = language == "zh-CN"
    primary = _rw_first_available_theme(common_pain_points, buyer_objections, liked_points, use_cases)
    positive = _rw_first_available_theme(liked_points, use_cases, common_pain_points)
    flavor = next((theme for theme in liked_points if "flavor" in _rw_human_theme_phrase(theme.label).lower() or "root beer" in _rw_human_theme_phrase(theme.label).lower()), positive)

    primary_label = _rw_output_theme_label(primary.label, language) if primary else ("\u4e70\u5bb6\u5173\u6ce8\u70b9" if is_zh else "buyer concern")
    positive_label = _rw_output_theme_label(positive.label, language) if positive else ("\u6b63\u5411\u8bc1\u636e" if is_zh else "positive proof")
    primary_quote = _rw_quote_snippet(_rw_theme_first_quote(primary), 140) if primary else ""
    positive_quote = _rw_quote_snippet(_rw_theme_first_quote(positive), 120) if positive else ""
    flavor_quote = _rw_quote_snippet(_rw_theme_first_quote(flavor), 130) if flavor else positive_quote
    product_hint = _rw_workspace_product_hint(payload, language)
    hook = hooks[0] if hooks else (
        f"\u4e70\u4e4b\u524d\u5148\u770b\u8fd9\u4e2a\u4e70\u5bb6\u4fe1\u53f7\uff1a{primary_label}"
        if is_zh
        else f"Before you buy, look at this buyer signal: {primary_label}."
    )

    if is_zh:
        positioning_note = "\u57fa\u4e8e\u5f53\u524d\u53ef\u89c1\u8bc4\u8bba\u6837\u672c\u751f\u6210\u7684\u7b2c\u4e00\u7248\u77ed\u89c6\u9891\u811a\u672c\uff0c\u9002\u5408\u7ee7\u7eed\u6269\u5c55\u6210\u5206\u955c\u548c\u5173\u952e\u5e27\u3002"
        script_15 = ReviewVideoScript(
            duration_label="15s",
            hook=hook,
            voiceover=[
                f"\u7b2c\u4e00\u955c\uff1a\u51b0\u7bb1\u6216\u8d27\u67b6\u91cc\u628a{product_hint}\u548c\u666e\u901a root beer \u653e\u5728\u4e00\u8d77\uff0c\u5b57\u5e55\u76f4\u63a5\u95ee\uff1a\u8fd9\u4e2a\u4ef7\u683c\u503c\u5417\uff1f",
                f"\u7b2c\u4e8c\u955c\uff1a\u5012\u676f\u5192\u6ce1\uff0c\u540c\u65f6\u5ff5\u51fa\u4e70\u5bb6\u987e\u8651\u539f\u8bdd\uff1a{primary_quote if primary_quote else primary_label}\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u5207\u5230\u53e3\u5473\u5bf9\u6bd4\uff0c\u7528\u6b63\u5411\u539f\u8bdd\u6536\u5c3e\uff1a{flavor_quote or positive_quote or positive_label}\u3002",
            ],
            on_screen_text=[
                f"\u4e70\u5bb6\u5728\u610f\uff1a{primary_label}",
                primary_quote or "\u6765\u81ea\u53ef\u89c1\u8bc4\u8bba\u7684\u4ef7\u683c/\u4ef7\u503c\u4fe1\u53f7",
                flavor_quote or positive_quote or positive_label,
            ],
            cta="\u5982\u679c\u4f60\u4e5f\u5728\u72b9\u8c6b\u8fd9\u4e2a\u70b9\uff0c\u5148\u770b\u8fd9\u4e2a\u53ef\u89c1\u8bc4\u8bba\u6837\u672c\u3002",
            evidence_used=[quote for quote in [primary_quote, flavor_quote or positive_quote] if quote],
        )
        script_30 = ReviewVideoScript(
            duration_label="30s",
            hook=hook,
            voiceover=[
                f"\u7b2c\u4e00\u955c\uff1a\u8d27\u67b6/\u51b0\u7bb1\u5bf9\u6bd4\uff0c\u5148\u628a{primary_label}\u6446\u51fa\u6765\uff1a{primary_quote if primary_quote else primary_label}\u3002",
                f"\u7b2c\u4e8c\u955c\uff1a\u5f00\u7f50\u3001\u5012\u676f\u3001\u6c14\u6ce1\u7279\u5199\uff0c\u8ba9\u753b\u9762\u56de\u5230{product_hint}\u7684\u771f\u5b9e\u996e\u7528\u573a\u666f\u3002",
                f"\u7b2c\u4e09\u955c\uff1a\u505a\u98ce\u5473\u5bf9\u6bd4\uff0c\u4e0d\u53ea\u8bf4\u597d\u559d\uff0c\u76f4\u63a5\u7528\u539f\u8bdd\u89e3\u91ca\uff1a{flavor_quote or positive_quote or positive_label}\u3002",
                f"\u7b2c\u56db\u955c\uff1a\u7528\u590d\u8d2d\u6216\u559c\u7231\u8bc1\u636e\u505a\u4fe1\u4efb\u56de\u6536\uff1a{positive_quote if positive_quote else positive_label}\u3002",
            ],
            on_screen_text=[
                f"\u5148\u770b\u987e\u8651\uff1a{primary_label}",
                primary_quote or "\u4ef7\u683c / \u4ef7\u503c\u4fe1\u53f7",
                flavor_quote or "\u98ce\u5473\u5bf9\u6bd4\u8bc1\u636e",
                positive_quote or positive_label,
            ],
            cta="\u628a\u5b83\u5f53\u4f5c\u53ef\u89c1\u8bc4\u8bba\u4fe1\u53f7\uff0c\u4e0d\u5f53\u4f5c\u5b8c\u6574\u8bc4\u8bba\u7edf\u8ba1\uff1b\u8d2d\u4e70\u524d\u5148\u770b\u8fd9\u4e2a\u70b9\u3002",
            evidence_used=[quote for quote in [primary_quote, flavor_quote, positive_quote] if quote],
        )
    else:
        positioning_note = "First-pass short-form scripts generated from the visible review sample, ready to expand into storyboard and keyframes."
        script_15 = ReviewVideoScript(
            duration_label="15s",
            hook=hook,
            voiceover=[
                f"Shot 1: Put {product_hint} next to a familiar root beer and ask whether the price is worth it.",
                f"Shot 2: Pour it over ice while reading the buyer concern: {primary_quote if primary_quote else primary_label}.",
                f"Shot 3: Cut to the flavor comparison and close with proof: {flavor_quote or positive_quote or positive_label}.",
            ],
            on_screen_text=[
                f"Buyer concern: {primary_label}",
                primary_quote or "visible review evidence",
                flavor_quote or positive_quote or positive_label,
            ],
            cta="Check this visible review signal before you buy.",
            evidence_used=[quote for quote in [primary_quote, flavor_quote or positive_quote] if quote],
        )
        script_30 = ReviewVideoScript(
            duration_label="30s",
            hook=hook,
            voiceover=[
                f"Shot 1: Shelf or fridge comparison: frame the {primary_label} with the actual buyer quote: {primary_quote if primary_quote else primary_label}.",
                f"Shot 2: Open, pour, and show the product in a real drinking moment.",
                f"Shot 3: Make the taste comparison specific: {flavor_quote or positive_quote or positive_label}.",
                f"Shot 4: Close with repeat-purchase or liking proof: {positive_quote if positive_quote else positive_label}.",
            ],
            on_screen_text=[
                f"Concern: {primary_label}",
                primary_quote or "Visible review evidence",
                flavor_quote or "Flavor comparison proof",
                positive_quote or positive_label,
            ],
            cta="Use this as a visible review signal, not full review statistics.",
            evidence_used=[quote for quote in [primary_quote, flavor_quote, positive_quote] if quote],
        )

    return ReviewVideoScriptPack(
        positioning_note=positioning_note,
        scripts=[script_15, script_30],
    )



@app.post("/api/v1/analyze-review-workspace", response_model=ReviewWorkspaceResponse)
async def analyze_review_workspace(payload: ReviewWorkspaceRequest):
    rows = _rw_collect_reviews(payload)
    high_signal_rows = [row for row in rows if row["score"] >= 4]
    source_breakdown = _rw_source_breakdown(payload, rows)

    workspace_signal_rows = high_signal_rows or rows
    common_pain_points = _rw_theme_summaries(
        workspace_signal_rows,
        _rw_workspace_theme_markers(payload, workspace_signal_rows),
    )
    buyer_objections = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_OBJECTION_MARKERS,
        "objection",
    )
    liked_points = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_LIKE_MARKERS,
        "liked signal",
        limit=12,
    )
    use_cases = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_USE_CASE_MARKERS,
        "use case",
    )

    common_pain_points = _rw_refine_theme_quotes(_rw_compact_theme_summaries(common_pain_points))
    buyer_objections = _rw_refine_buyer_objection_summaries(buyer_objections)
    liked_points = _rw_refine_liked_point_summaries(liked_points)
    use_cases = _rw_refine_use_case_summaries(use_cases + liked_points + buyer_objections + common_pain_points)

    hooks = _rw_hooks(common_pain_points, liked_points, payload.output_language)
    sample_interpretation = _rw_sample_interpretation(
        payload,
        rows,
        high_signal_rows,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
    )
    video_script_pack = _rw_video_script_pack(
        payload,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
        hooks,
    )
    llm_evidence_packet = _review_workspace_llm_evidence_packet(
        payload,
        rows,
        high_signal_rows,
        source_breakdown,
        common_pain_points,
        buyer_objections,
        liked_points,
        use_cases,
    )

    return ReviewWorkspaceResponse(
        workspace_id=payload.workspace_id,
        product_count=len(payload.products),
        total_reviews=len(rows),
        high_signal_review_count=len(high_signal_rows),
        source_breakdown=source_breakdown,
        common_pain_points=common_pain_points,
        buyer_objections=buyer_objections,
        liked_points=liked_points,
        use_cases=use_cases,
        product_summaries=[_rw_product_summary(product) for product in payload.products],
        creative_angles=_rw_creative_angles(common_pain_points, liked_points, payload.output_language, buyer_objections),
        hooks=hooks,
        recommended_next_actions=[
            "Collect 30-80 high-signal reviews per product before final creative testing.",
            "Prioritize low-star and objection-heavy reviews for ad angle discovery.",
            "Use repeated buyer wording as hook language instead of generic product claims.",
        ],
        sample_interpretation=sample_interpretation,
        video_script_pack=video_script_pack,
        llm_evidence_packet=llm_evidence_packet,
    )




# L37-C messy pasted review parser.
import re
from schemas.review_paste import PastedReviewWorkspaceAnalyzeRequest, PastedReviewWorkspaceAnalyzeResponse, ReviewPasteParseRequest, ReviewPasteParseResponse
from schemas.review_workspace import ReviewWorkspaceProduct, ReviewWorkspaceReview

_REVIEW_PASTE_RATING_RE = re.compile(
    r"(?P<rating>[1-5](?:\.\d)?)\s*(?:out of\s*5\s*stars|/5|stars?)",
    re.IGNORECASE,
)

_REVIEW_PASTE_META_PREFIXES = (
    "reviewed in ",
    "verified purchase",
    "vine customer review",
    "people found this helpful",
    "person found this helpful",
    "helpful",
    "report",
    "translate review",
    "color:",
    "size:",
    "style:",
    "pattern name:",
    "flavor name:",
)


def _paste_clean_line(line: str) -> str:
    return " ".join(str(line or "").replace("\u00a0", " ").split())


def _paste_is_meta_line(line: str) -> bool:
    lowered = line.lower().strip()
    if not lowered:
        return True
    if lowered.startswith(_REVIEW_PASTE_META_PREFIXES):
        return True
    if "verified purchase" in lowered:
        return True
    if "found this helpful" in lowered:
        return True
    if lowered in {"read more", "show more", "see more", "customer reviews"}:
        return True
    return False


def _paste_high_signal_score(review: ReviewWorkspaceReview) -> int:
    text = _paste_clean_line(review.text)
    lowered = text.lower()
    if len(text) < 18:
        return 0

    score = 1
    try:
        rating = float(str(review.rating).split()[0]) if review.rating not in (None, "") else None
    except (TypeError, ValueError):
        rating = None

    if rating is not None and rating <= 3:
        score += 3
    if rating is not None and rating >= 4:
        score += 1
    if review.helpful_count:
        score += min(3, int(review.helpful_count) // 5 + 1)
    if any(marker in lowered for marker in ["but", "wish", "too", "not", "hard", "difficult", "problem", "issue", "leak", "broke", "mess"]):
        score += 3
    if any(marker in lowered for marker in ["love", "great", "easy", "perfect", "works", "useful", "recommend"]):
        score += 2
    if len(text) >= 80:
        score += 2
    return score


def _parse_helpful_count(line: str) -> int | None:
    match = re.search(r"(\d+)\s+people\s+found\s+this\s+helpful", line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"one\s+person\s+found\s+this\s+helpful", line, re.IGNORECASE):
        return 1
    return None


def _finalize_pasted_review(
    reviews: list[ReviewWorkspaceReview],
    rating,
    title: str,
    body_lines: list[str],
    helpful_count: int | None,
    source_section: str,
):
    body = _paste_clean_line(" ".join(body_lines))
    title = _paste_clean_line(title)

    if not body and title:
        body = title
        title = ""

    if len(body) < 10:
        return

    reviews.append(
        ReviewWorkspaceReview(
            rating=rating,
            title=title,
            text=body,
            helpful_count=helpful_count,
            source_section=source_section,
        )
    )


def _parse_messy_reviews(raw_text: str, source_section: str) -> list[ReviewWorkspaceReview]:
    lines = [_paste_clean_line(line) for line in str(raw_text or "").splitlines()]
    lines = [line for line in lines if line]

    reviews: list[ReviewWorkspaceReview] = []
    current_rating = None
    current_title = ""
    current_body: list[str] = []
    current_helpful = None
    active = False

    for line in lines:
        helpful = _parse_helpful_count(line)
        if helpful is not None:
            current_helpful = helpful
            continue

        rating_match = _REVIEW_PASTE_RATING_RE.search(line)
        if rating_match:
            if active:
                _finalize_pasted_review(
                    reviews,
                    current_rating,
                    current_title,
                    current_body,
                    current_helpful,
                    source_section,
                )

            active = True
            current_rating = rating_match.group("rating")
            remainder = _paste_clean_line(_REVIEW_PASTE_RATING_RE.sub("", line, count=1))
            current_title = remainder if len(remainder) <= 90 else ""
            current_body = [] if current_title else ([remainder] if remainder else [])
            current_helpful = None
            continue

        if _paste_is_meta_line(line):
            continue

        if active:
            if not current_title and len(line) <= 90 and not current_body:
                current_title = line
            else:
                current_body.append(line)
        else:
            # Generic non-Amazon paste fallback: each meaningful paragraph can be a review.
            if len(line) >= 30:
                reviews.append(
                    ReviewWorkspaceReview(
                        rating=None,
                        title="",
                        text=line,
                        helpful_count=None,
                        source_section=source_section,
                    )
                )

    if active:
        _finalize_pasted_review(
            reviews,
            current_rating,
            current_title,
            current_body,
            current_helpful,
            source_section,
        )

    # Deduplicate while preserving order.
    deduped: list[ReviewWorkspaceReview] = []
    seen = set()
    for review in reviews:
        key = _paste_clean_line(review.text).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(review)

    return deduped


@app.post("/api/v1/analyze-pasted-review-workspace", response_model=PastedReviewWorkspaceAnalyzeResponse)
async def analyze_pasted_review_workspace(payload: PastedReviewWorkspaceAnalyzeRequest):
    reviews = _parse_messy_reviews(payload.raw_text, payload.source_section)
    high_signal_count = sum(1 for review in reviews if _paste_high_signal_score(review) >= 4)

    warnings = []
    if not _paste_clean_line(payload.raw_text):
        warnings.append("empty_input")
    if not reviews:
        warnings.append("no_reviews_detected")
    if reviews and high_signal_count == 0:
        warnings.append("low_signal_reviews")

    workspace_product = ReviewWorkspaceProduct(
        platform=payload.platform,
        url=payload.url,
        asin=payload.asin,
        title=payload.product_title or payload.asin or payload.url or "Pasted review product",
        reviews=reviews,
    )

    parsed = ReviewPasteParseResponse(
        review_count=len(reviews),
        high_signal_review_count=high_signal_count,
        reviews=reviews,
        workspace_product=workspace_product,
        data_warnings=warnings,
    )

    workspace_payload = ReviewWorkspaceRequest(
        workspace_id=payload.workspace_id,
        source="pasted_reviews",
        products=[workspace_product],
        goal=payload.goal,
        output_language=payload.output_language,
    )
    analysis = await analyze_review_workspace(workspace_payload)

    return PastedReviewWorkspaceAnalyzeResponse(
        parsed=parsed,
        analysis=analysis,
    )


@app.post("/api/v1/parse-review-paste", response_model=ReviewPasteParseResponse)
async def parse_review_paste(payload: ReviewPasteParseRequest):
    reviews = _parse_messy_reviews(payload.raw_text, payload.source_section)
    high_signal_count = sum(1 for review in reviews if _paste_high_signal_score(review) >= 4)

    warnings = []
    if not _paste_clean_line(payload.raw_text):
        warnings.append("empty_input")
    if not reviews:
        warnings.append("no_reviews_detected")
    if reviews and high_signal_count == 0:
        warnings.append("low_signal_reviews")

    workspace_product = ReviewWorkspaceProduct(
        platform=payload.platform,
        url=payload.url,
        asin=payload.asin,
        title=payload.product_title or payload.asin or payload.url or "Pasted review product",
        reviews=reviews,
    )

    return ReviewPasteParseResponse(
        review_count=len(reviews),
        high_signal_review_count=high_signal_count,
        reviews=reviews,
        workspace_product=workspace_product,
        data_warnings=warnings,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=get_server_port(), reload=True)
