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
    ReviewThemeSummary,
    ReviewWorkspaceRequest,
    ReviewWorkspaceResponse,
)

_REVIEW_WORKSPACE_THEME_MARKERS = {
    "leak / mess risk": ["leak", "leaking", "spill", "spilled", "mess", "drip"],
    "hard to clean": ["hard to clean", "difficult to clean", "scrub", "dishwasher"],
    "size / fit issue": ["too small", "too big", "doesn't fit", "didn't fit", "opening was bigger", "wide cans", "narrow opening"],
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
            })
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows


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



def _rw_compact_evidence_quote(value: str, max_len: int = 260) -> str:
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
    text = re.sub(r"\s+", " ", text).strip(" -:;,.")

    if not text:
        return ""

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


def _rw_refine_buyer_objection_summaries(themes):
    refined = []
    seen_labels = set()

    for theme in _rw_compact_theme_summaries(themes):
        quotes = getattr(theme, "evidence_quotes", []) or []
        label = _rw_objection_label_from_quotes(getattr(theme, "label", ""), quotes)

        if label.startswith("objection:"):
            label = label.replace("objection:", "").strip() or "buyer hesitation"

        if label in seen_labels:
            continue

        seen_labels.add(label)
        refined.append(_rw_rebuild_theme_summary(theme, label=label, evidence_quotes=quotes))

    return refined


def _rw_creative_angles(common_pain_points: list[ReviewThemeSummary], liked_points: list[ReviewThemeSummary]) -> list[str]:
    angles = []
    for theme in common_pain_points[:4]:
        angles.append(f"Turn the repeated complaint around: show how the product avoids {theme.label}.")
    for theme in liked_points[:2]:
        angles.append(f"Use positive proof as the hook: buyers repeatedly mention {theme.label}.")
    if not angles:
        angles.append("Use the most specific review quote as the opening hook, then show the product solving it.")
    return angles[:6]


def _rw_hooks(common_pain_points: list[ReviewThemeSummary], liked_points: list[ReviewThemeSummary], language: str) -> list[str]:
    is_zh = language == "zh-CN"
    hooks = []
    for theme in common_pain_points[:4]:
        if is_zh:
            hooks.append(f"???????????{theme.label}?")
        else:
            hooks.append(f"Still dealing with {theme.label}? Watch this before you buy.")
    for theme in liked_points[:2]:
        if is_zh:
            hooks.append(f"??????????{theme.label}?")
        else:
            hooks.append(f"Why are buyers calling out {theme.label}?")
    return hooks[:6] or (["??????????????????"] if is_zh else ["Before you buy, look at what real buyers complain about most."])


@app.post("/api/v1/analyze-review-workspace", response_model=ReviewWorkspaceResponse)
async def analyze_review_workspace(payload: ReviewWorkspaceRequest):
    rows = _rw_collect_reviews(payload)
    high_signal_rows = [row for row in rows if row["score"] >= 4]

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
    )
    use_cases = _rw_marker_summaries(
        high_signal_rows or rows,
        _REVIEW_WORKSPACE_USE_CASE_MARKERS,
        "use case",
    )

    common_pain_points = _rw_compact_theme_summaries(common_pain_points)
    buyer_objections = _rw_refine_buyer_objection_summaries(buyer_objections)
    liked_points = _rw_compact_theme_summaries(liked_points)
    use_cases = _rw_compact_theme_summaries(use_cases)

    return ReviewWorkspaceResponse(
        workspace_id=payload.workspace_id,
        product_count=len(payload.products),
        total_reviews=len(rows),
        high_signal_review_count=len(high_signal_rows),
        common_pain_points=common_pain_points,
        buyer_objections=buyer_objections,
        liked_points=liked_points,
        use_cases=use_cases,
        product_summaries=[_rw_product_summary(product) for product in payload.products],
        creative_angles=_rw_creative_angles(common_pain_points, liked_points),
        hooks=_rw_hooks(common_pain_points, liked_points, payload.output_language),
        recommended_next_actions=[
            "Collect 30-80 high-signal reviews per product before final creative testing.",
            "Prioritize low-star and objection-heavy reviews for ad angle discovery.",
            "Use repeated buyer wording as hook language instead of generic product claims.",
        ],
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
