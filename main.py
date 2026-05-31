import re
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


def _split_pasted_review_quotes(text: str, limit: int = 6) -> list[str]:
    cleaned_lines = []
    for raw_line in (text or "").replace("\r", "\n").split("\n"):
        line = raw_line.strip().lstrip("-*•0123456789. )(").strip()
        if line and not _is_pasted_review_label_line(line):
            cleaned_lines.append(line)

    if not cleaned_lines:
        normalized = " ".join((text or "").split())
        pieces = [piece.strip() for piece in normalized.replace("!", ".").replace("?", ".").split(".")]
        cleaned_lines = [piece for piece in pieces if piece and not _is_pasted_review_label_line(piece)]

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
        "2-pack",
        "two-pack",
        "not sold by the single bottle",
        "only came in a 2-pack",
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
    "great flavor", "greater flavor", "smoother",
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


def _rw_theme_summaries(rows: list[dict], themes: dict[str, list[str]], limit: int = 6) -> list[ReviewThemeSummary]:
    scored = []
    for label, markers in themes.items():
        matched = []
        for row in rows:
            lowered = row["text"].lower()
            if any(marker.lower() in lowered for marker in markers):
                matched.append(row["text"])
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
        "wrong size",
        "size is wrong",
        "stated size",
        "half size",
        "8 1/2 oz",
        "8.5 oz",
        "17 oz",
        "2-pack",
        "single bottle",
        "two-pack",
        "not sold by the single bottle",
        "only came in a 2-pack",
    ]):
        return "quantity / size uncertainty"

    if any(term in blob for term in [
        "priced wrong",
        "price",
        "expensive",
        "cheaper",
        "not worth",
        "worth",
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
    if _rw_quote_is_positive_reassurance_quote(quote):
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

    if _rw_quote_is_positive_reassurance_quote(value) and any(marker in raw_label or marker in phrase for marker in [
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

    marker_groups = [
        (
            ("price / value", "price or value", "price / value concern"),
            ["price", "value", "worth", "pricy", "pricey", "cheaper", "expensive", "quality", "two-pack", "2-pack", "cost"],
        ),
        (
            ("taste / flavor", "taste or flavor", "quality consistency"),
            ["taste", "flavor", "flavour", "wateriest", "flavorless", "bland", "rich", "glaze", "vinaigrette", "ingredients"],
        ),
        (
            ("size / quantity", "quantity or size", "quantity / size"),
            ["size", "quantity", "listed as", "what came was", "oz", "bottle", "two-pack", "2-pack", "half size", "regular size"],
        ),
        (
            ("expectation mismatch", "tradeoff", "hesitation"),
            ["expected", "expectation", "however", "but", "concerned", "not lid", "spout", "air", "mismatch"],
        ),
        (
            ("liked signal", "great", "love", "useful", "easy", "recommend"),
            ["great", "love", "useful", "easy", "recommend", "worth", "quality", "cannot beat"],
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
        "quality consistency concern": "quality consistency concern",
        "color expectation mismatch": "color expectation mismatch",
        "sewing / quality control issue": "sewing or QC concern",
        "summer fabric comfort": "summer fabric comfort",
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
        "wateriest",
        "flavorless",
        "terrible",
        "not super complex",
        "not sold",
        "2-pack",
        "single bottle",
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

    if normalized == "great":
        return "Buyers keep calling this great - here's the moment that proves why."

    if normalized == "love":
        return "People say they love this - here's the everyday use case behind it."

    if normalized == "useful":
        return "Buyers say this is useful - here's the problem it solves fast."

    if normalized == "easy":
        return "Buyers say this feels easy - here's the moment that makes it click."

    label = _rw_human_theme_phrase(raw_label)
    return f"Buyers keep mentioning {label} - here's the proof moment."



def _rw_positive_hook_from_theme_zh(theme) -> str:
    raw_label = str(getattr(theme, "label", "") or "").strip()
    quote = _rw_quote_snippet(_rw_theme_first_quote(theme), 72)
    lower_quote = quote.lower()
    label = _rw_output_theme_label(raw_label, "zh-CN")

    if quote:
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

    for theme in _rw_unique_themes_by_first_quote(liked_points)[:4]:
        if is_zh:
            hooks.append(_rw_positive_hook_from_theme_zh(theme))
        else:
            hooks.append(_rw_positive_hook_from_theme(theme))

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

    if "love" in lower or fallback == "love":
        return "buyers saying they love it"

    if "great" in lower or fallback == "great":
        return "buyers calling it great"

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
                evidence_quotes=quotes[:2],
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
        "quality consistency concern": "quality consistency concern",
        "color expectation mismatch": "color expectation mismatch",
        "sewing / quality control issue": "sewing or QC concern",
        "summer fabric comfort": "summer fabric comfort",
        "leak / mess risk": "mess or spill concern",
        "hard to clean": "cleanup concern",
        "durability concern": "durability concern",
        "time saving": "time-saving benefit",
        "repeat purchase intent": "repeat purchase intent",
        "best root beer praise": "best root beer praise",
        "root beer flavor comparison": "root beer flavor comparison",
        "flavor praise": "flavor praise",
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
        "regional availability context": "\u5730\u533a\u7a00\u7f3a / \u5f53\u5730\u4e70\u4e0d\u5230",
        "gift use case": "\u9001\u793c\u573a\u666f",
        "daily use context": "\u65e5\u5e38\u996e\u7528\u573a\u666f",
        "party or hosting context": "\u805a\u4f1a / \u62db\u5f85\u573a\u666f",
        "stocking or pack context": "\u56e4\u8d27 / \u5305\u88c5\u573a\u666f",
        "usage context": "\u4f7f\u7528\u573a\u666f",
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
    positive_signals = _rw_unique_themes_by_first_quote(liked_points)
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
