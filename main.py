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
    DebugCopilotResponse,
    GenerateCopilotResponse,
    GrowthRequest,
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

DESCRIPTION_MIN_CHARS = 12
DESCRIPTION_MAX_CHARS = 6000

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


@app.post("/api/v1/generate-copilot", response_model=GenerateCopilotResponse)
async def generate_copilot_flow(request: GrowthRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    product_category_hint = _safe_product_category_hint(request.url)
    emit_event(
        "generate_copilot_start",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="started",
        product_category=product_category_hint,
        goal=request.goal,
    )
    emit_event(
        "generate_copilot_after_request_parse",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=product_category_hint,
        goal=request.goal,
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
        )
        return JSONResponse(
            status_code=503,
            content={
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
    }
    emit_event(
        "generate_copilot_complete",
        request_id,
        endpoint="/api/v1/generate-copilot",
        status="success",
        latency_ms=(time.perf_counter() - started) * 1000,
        product_category=env_state.get("product_category"),
        goal=request.goal,
    )
    return response


@app.post("/api/v1/generate-from-description", response_model=ProductDescriptionResponse)
async def generate_from_description(request: ProductDescriptionRequest, http_request: Request):
    started = time.perf_counter()
    request_id = http_request.state.request_id
    product_name = _clean_description_text(request.product_name)
    emit_event(
        "generate_from_description_start",
        request_id,
        endpoint="/api/v1/generate-from-description",
        status="started",
        product_category=request.product_category or "user_provided_product",
        goal=request.goal,
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
        )
        return validation_error

    try:
        generated = await generate_description_brief(request)
        response = {
            "status": "success",
            "data": _description_response_data(request, generated),
            "request_id": request_id,
        }
        emit_event(
            "generate_from_description_complete",
            request_id,
            endpoint="/api/v1/generate-from-description",
            status="success",
            latency_ms=(time.perf_counter() - started) * 1000,
            product_category=request.product_category or product_name,
            goal=request.goal,
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
        )
        return _description_error(
            "Product Description Mode generation failed safely. Please retry with a shorter description.",
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
