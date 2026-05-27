import json
import os
from pathlib import Path

from fastapi import FastAPI, Request
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
)
from schemas.source_probe_contract import (
    SourceProbeRequest,
    SourceProbeResponse,
    SourceProbeResult,
    SourceProbeTelemetry,
)
from source_adapters import SourceAdapterRegistry
from source_adapters.amazon_url_utils import normalize_amazon_product_url

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
SUPPORTED_OUTPUT_LANGUAGES = {"en", "zh-CN"}

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


def _split_pasted_review_quotes(text: str, limit: int = 6) -> list[str]:
    cleaned_lines = []
    for raw_line in (text or "").replace("\r", "\n").split("\n"):
        line = raw_line.strip().lstrip("-*•0123456789. )(").strip()
        if line:
            cleaned_lines.append(line)

    if not cleaned_lines:
        normalized = " ".join((text or "").split())
        pieces = [piece.strip() for piece in normalized.replace("!", ".").replace("?", ".").split(".")]
        cleaned_lines = [piece for piece in pieces if piece]

    quotes = []
    for line in cleaned_lines:
        quote = _safe_evidence_quote(line, limit=240)
        if quote and quote not in quotes:
            quotes.append(quote)
        if len(quotes) >= limit:
            break
    return quotes


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
    if len(product_name) + len(_clean_description_text(request.product_description or "")) + len(pasted_reviews) > DESCRIPTION_MAX_CHARS:
        return _description_error(
            "Input is too long for Pasted Reviews Mode. Please shorten the pasted reviews.",
            "input_too_long",
            request_id,
        )
    return None


def _safe_evidence_quote(text: str, limit: int = 220) -> str:
    cleaned = " ".join(_clean_description_text(text).split())
    return cleaned[:limit]


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
    content = (
        "Return JSON with keys: target_audience, core_hook_strategy, emotional_trigger, hook, "
        "cta, storyboard_scenes, evaluation_reasoning, feedback. "
        "storyboard_scenes must be a list of exactly 4 objects with visual_description, narration, evidence_quote_used.\n\n"
        f"Product name: {request.product_name}\n"
        f"Product category: {request.product_category or 'unspecified'}\n"
        f"Product description: {request.product_description or 'unspecified'}\n"
        f"Target platform: {request.target_platform or 'TikTok'}\n"
        f"Goal: {request.goal or 'tiktok_ctr'}\n"
        "Pasted review evidence:\n"
        + "\n".join(f"- {quote}" for quote in evidence_quotes)
    )
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
    return {
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


def _pasted_reviews_response_data(
    request: PastedReviewsRequest,
    generated: dict,
    evidence_quotes: list[str],
) -> dict:
    product_name = _clean_description_text(request.product_name)
    category = _clean_description_text(request.product_category or "user_pasted_reviews_product")
    description_quote = _safe_evidence_quote(request.product_description or "")
    primary_quote = evidence_quotes[0] if evidence_quotes else _safe_evidence_quote(request.pasted_reviews)
    scenes = generated.get("storyboard_scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    normalized_scenes = []
    for index, scene in enumerate(scenes[:4]):
        if not isinstance(scene, dict):
            continue
        fallback_quote = evidence_quotes[index % len(evidence_quotes)] if evidence_quotes else primary_quote
        quote = scene.get("evidence_quote_used") or fallback_quote
        normalized_scenes.append(
            {
                "scene_id": index + 1,
                "scene_goal": scene.get("scene_goal", f"Show {product_name} review pain point"),
                "visual_description": scene.get("visual_description", ""),
                "narration": scene.get("narration", ""),
                "evidence_quote_used": quote,
                "linked_painpoint": quote,
            }
        )

    while len(normalized_scenes) < 4:
        index = len(normalized_scenes) + 1
        quote = evidence_quotes[(index - 1) % len(evidence_quotes)] if evidence_quotes else primary_quote
        normalized_scenes.append(
            {
                "scene_id": index,
                "scene_goal": f"Turn pasted review pain point into a {request.target_platform or 'TikTok'} moment",
                "visual_description": f"Show {product_name} addressing this customer complaint in a simple product scene.",
                "narration": f"This review pain point becomes the creative angle: {quote}",
                "evidence_quote_used": quote,
                "linked_painpoint": quote,
            }
        )

    hook = generated.get("hook") or f"If this review sounds familiar, {product_name} needs a better creative angle."
    cta = generated.get("cta") or f"Use {product_name} to answer the pain point your buyers already mention."
    pain_points = evidence_quotes[:4] or [primary_quote]

    return {
        "insights": {
            "pain_points": pain_points,
            "user_complaint_cluster": pain_points,
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
            "trust_barriers": pain_points,
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
    }


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


def _amazon_intake_fallback_message() -> str:
    return "Paste 3-5 Amazon reviews or product bullets to improve the creative brief."


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
                "data_warnings": list(evidence.data_warnings or []),
                "fallback_required": fallback_required,
                "fallback_message": _amazon_intake_fallback_message() if fallback_required else "",
                "error": metadata.get("error", ""),
                "metadata": {
                    **metadata,
                    "source_type": evidence.source_type,
                    "data_warnings": list(evidence.data_warnings or []),
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=get_server_port(), reload=True)
