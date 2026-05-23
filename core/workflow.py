import asyncio
import hashlib
import json
import os
import re
import shutil
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import jsonpatch
import json_repair
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from core.agent_state import GraphState
from core.runtime_config import enabled_source_tools
from source_adapters import SourceAdapterRegistry

load_dotenv()


api_rate_limiter = AsyncLimiter(max_rate=2, time_period=1)


class PromptRegistry:
    _templates = {
        "planner": (
            "You are the workflow planner. Classify the product, decide task complexity from real inputs only, "
            "and select tools only from the provided available_tools list. Do not select unavailable real APIs."
        ),
        "audience": "You are an audience analyst. Use only the provided evidence and mark uncertainty clearly.",
        "painpoint": "You are a painpoint analyst. Extract physical and emotional pains grounded in review evidence.",
        "dopamine": (
            "You are a viral emotion extractor. Use only review evidence. "
            "Return exactly 4 short bullets: relief_moment, contrast_mechanism, satisfaction_trigger, viral_emotion. "
            "Each bullet must be under 18 words. No long explanation."
        ),
        "synthesis": (
            "You are a cognitive synthesizer. Convert compact analysis extracts and evidence into one structured "
            "buyer profile. Keep only decisions required by downstream strategy and storyboard generation."
        ),
        "strategy": (
            "You are a growth strategy engine. Use compact inputs only. "
            "Every decision must cite evidence_basis and flag weak evidence. "
            "Avoid long market analysis; keep only judgments that affect the output schema."
        ),
        "storyboard": (
            "You are a scene graph generator. Produce exactly 4 executable short-video scenes. "
            "Each scene MUST copy one exact evidence quote from evidence.evidence_quotes into evidence_quote_used; "
            "do not paraphrase evidence_quote_used. Each scene must connect linked_painpoint to that quote. "
            "Each visual_description must be concrete and evidence-linked, 120-180 characters. "
            "Each narration must be 80-130 characters and directly tied to the evidence quote. "
            "Do not over-explain or write cinematic essays. "
            "Use at least 4 distinct quotes when available. "
            "Use at most 3 dopamine_trigger=true scenes to avoid reward hacking."
        ),
        "reflection": "You are a self-repair controller. Diagnose the failed layer before proposing JSONPatch operations.",
    }

    @classmethod
    def get(cls, role_key: str) -> str:
        return cls._templates.get(role_key, "You are a precise AI assistant.")


class StateCompressor:
    MAX_CHARS = 24_000

    @classmethod
    def check_and_compress(cls, value: str) -> str:
        return value[: cls.MAX_CHARS] if len(value) > cls.MAX_CHARS else value


class ToolSource(BaseModel):
    source_type: str = Field(description="real_api | local_dataset | mock | unavailable | tool_error | llm_inferred")
    source_role: str = Field(description="review | trend | product_meta | ad_metric")
    source_url: str
    confidence: float = Field(ge=0.0, le=1.0)
    items: List[dict]


class EvidenceBundle(BaseModel):
    source_type: str
    source_url: str
    confidence: float
    review_confidence: float
    trend_confidence: float
    review_count: int
    evidence_quotes: List[str]
    trend_signals: List[str]
    data_warnings: List[str]


class AudienceProfile(BaseModel):
    primary_user: str
    anxiety_points: List[str]
    trust_barriers: List[str]
    buying_motivation: str


class PainpointProfile(BaseModel):
    physical_painpoints: List[str]
    emotional_painpoints: List[str]
    use_case_disasters: List[str]
    evidence_quotes: List[str]


class DopamineProfile(BaseModel):
    relief_moment: str
    contrast_mechanism: str
    satisfaction_trigger: str
    viral_emotion: str


class CognitiveProfile(BaseModel):
    audience: AudienceProfile
    painpoint: PainpointProfile
    dopamine: DopamineProfile
    confidence: float = Field(ge=0.0, le=1.0)
    grounding_notes: List[str]


class ExecutionPlan(BaseModel):
    product_category: str
    cognitive_complexity: str = Field(description="high | low")
    selected_tools: List[str] = Field(default_factory=lambda: ["amazon_review_mock"])


class StrategicNarrative(BaseModel):
    target_user: str
    core_pain: str
    evidence_basis: List[str]
    identity_attack: str
    status_desire: str
    future_self_gap: str
    broken_expectation: str
    visual_hook: str
    emotional_arc: List[str]
    trust_barrier: str
    objection_handling: str
    conversion_mechanism: str
    cta_logic: str
    risk_notes: List[str]


class ComputableScene(BaseModel):
    scene_id: int
    duration_sec: float
    scene_goal: str
    visual_description: str
    narration: str
    on_screen_text: str
    camera_motion: str
    camera_speed: float
    transition_style: str
    emotional_intensity: float = Field(ge=0.0, le=1.0)
    audio_emotion: str
    dopamine_trigger: bool
    dopamine_type: str
    retention_reason: str
    linked_painpoint: str
    evidence_quote_used: str


class Storyboard(BaseModel):
    scenes: List[ComputableScene]


class DiffPatch(BaseModel):
    op: str
    path: str
    value: Optional[Any] = None


class ReflectionResult(BaseModel):
    root_cause: str
    failed_layer: str = Field(description="retrieval | analysis | strategy | storyboard | reward")
    patches: List[DiffPatch] = Field(default_factory=list)
    regenerate_node: Optional[str] = None


class NodeMetrics(BaseModel):
    total_tokens: int = 0
    latency_ms: float = 0.0
    reasoning_latency_ms: float = 0.0
    retries: int = 0
    status: str = "success"
    error: Optional[str] = None
    model: str = ""
    role_key: str = ""
    node_name: str = ""
    input_size_char: int = 0
    memory_context_used: bool = False
    evidence_count: int = 0
    trend_signal_count: int = 0
    fallback: bool = False
    fallback_indicators: List[str] = Field(default_factory=list)
    reasoning_preview: str = ""


class ToolRuntime:
    def __init__(self):
        self.adapter_registry = SourceAdapterRegistry()

    async def run(self, tool_name: str, payload: dict) -> ToolSource:
        if tool_name == "amazon_review_mock":
            return await self._mock_amazon_reviews(payload)
        if tool_name == "amazon_review_api":
            return await self._real_amazon_reviews(payload)
        if tool_name == "tiktok_trend_mock":
            return await self._mock_tiktok_trends(payload)
        if tool_name == "tiktok_trend_api":
            return await self._real_tiktok_trends(payload)
        if tool_name == "reddit_review_api":
            return await self._real_reddit_reviews(payload)
        if tool_name == "local_review_dataset":
            return await self._local_review_dataset(payload)
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _mock_amazon_reviews(self, payload: dict) -> ToolSource:
        url = payload.get("url", "")
        product_hint = "product"
        if "mug" in url.lower() or "cup" in url.lower():
            product_hint = "cup"
        reviews = [
            {
                "rating": 2,
                "text": f"The {product_hint} looked good online, but it felt flimsy after a week.",
                "date": "mock",
            },
            {
                "rating": 1,
                "text": "I bought it for daily use and the main feature failed when I needed it most.",
                "date": "mock",
            },
            {
                "rating": 3,
                "text": "The idea is useful, but I do not fully trust the quality for the price.",
                "date": "mock",
            },
        ]
        return ToolSource(source_type="mock", source_role="review", source_url=url, confidence=0.45, items=reviews)

    async def _real_amazon_reviews(self, payload: dict) -> ToolSource:
        url = payload.get("url", "")
        product_category = payload.get("env_state", {}).get("product_category", "")
        evidence = self.adapter_registry.fetch("amazon_review_api", url, product_category)
        return ToolSource(
            source_type=evidence.source_type,
            source_role="review",
            source_url=evidence.source_url,
            confidence=evidence.confidence,
            items=[_model_dump(review) for review in evidence.reviews],
        )

    async def _mock_tiktok_trends(self, payload: dict) -> ToolSource:
        url = payload.get("url", "")
        product_category = payload.get("env_state", {}).get("product_category", "")
        evidence = self.adapter_registry.fetch("tiktok_trend_mock", url, canonical_category(product_category))
        items = [
            {"trend": signal, "text": signal, "date": "mock"}
            for signal in evidence.trend_signals
        ]
        return ToolSource(source_type="mock", source_role="trend", source_url=url, confidence=0.35, items=items)

    async def _real_tiktok_trends(self, payload: dict) -> ToolSource:
        url = payload.get("url", "")
        product_category = payload.get("env_state", {}).get("product_category", "")
        evidence = self.adapter_registry.fetch("tiktok_trend_api", url, product_category)
        return ToolSource(
            source_type=evidence.source_type,
            source_role="trend",
            source_url=evidence.source_url,
            confidence=evidence.confidence,
            items=[
                {"trend": signal, "text": signal, "date": "api"}
                for signal in evidence.trend_signals
            ],
        )

    async def _real_reddit_reviews(self, payload: dict) -> ToolSource:
        url = payload.get("url", "")
        product_category = payload.get("env_state", {}).get("product_category", "")
        evidence = self.adapter_registry.fetch("reddit_review_api", url, product_category)
        return ToolSource(
            source_type=evidence.source_type,
            source_role="review",
            source_url=evidence.source_url,
            confidence=evidence.confidence,
            items=[_model_dump(review) for review in evidence.reviews],
        )

    async def _local_review_dataset(self, payload: dict) -> ToolSource:
        url = payload.get("url", "")
        candidates = category_candidates(payload.get("env_state", {}).get("product_category", ""), url)
        evidence = None
        for candidate in candidates:
            candidate_evidence = self.adapter_registry.fetch("local_review_dataset", url, candidate)
            if candidate_evidence.reviews:
                evidence = candidate_evidence
                break
        if evidence is None:
            fallback_category = candidates[0] if candidates else canonical_category(
                payload.get("env_state", {}).get("product_category", "")
            )
            evidence = self.adapter_registry.fetch("local_review_dataset", url, fallback_category)
        items = [_model_dump(review) for review in evidence.reviews]
        return ToolSource(
            # Keep the workflow evidence/reward contract stable while the adapter boundary changes.
            source_type="local_dataset" if items else "unavailable",
            source_role="review",
            source_url=evidence.source_url if items else url,
            confidence=0.75 if items else 0.0,
            items=items,
        )


tool_runtime = ToolRuntime()


def normalize_category(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"['’]s\b", "", value)
    value = re.sub(r"([a-z])['’]\b", r"\1", value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


CATEGORY_ALIASES = {
    "women_clothing": "women_bras",
    "women_underwear": "women_bras",
    "bra": "women_bras",
    "bras": "women_bras",
    "girls_clothing": "girls_overalls",
    "children_clothing": "girls_overalls",
    "kids_clothing": "girls_overalls",
    "vinegar": "balsamic_vinegar",
    "balsamic": "balsamic_vinegar",
    "balsamic_vinegar_glaze": "balsamic_vinegar",
}


def canonical_category(value: str) -> str:
    normalized = normalize_category(value)
    return CATEGORY_ALIASES.get(normalized, normalized)


def category_candidates(product_category: str, url: str) -> List[str]:
    candidates = []
    for value in [product_category, url.rstrip("/").split("/")[-1]]:
        normalized = canonical_category(value)
        if normalized and normalized not in {"general", "food", "product", "products"}:
            candidates.append(normalized)
    return list(dict.fromkeys(candidates))


def memory_fingerprint(record: dict) -> str:
    metrics = record.get("reward_metrics", {})
    raw = json.dumps(
        {
            "product_type": record.get("product_type"),
            "core_pain": record.get("strategy", {}).get("core_pain"),
            "predicted_ctr": round(metrics.get("predicted_ctr", record.get("predicted_ctr", 0)), 3),
            "grounded_ctr": round(metrics.get("grounded_ctr", record.get("grounded_ctr", 0)), 3),
            "is_grounded": metrics.get("is_grounded", False),
            "failure_type": metrics.get("failure_type", ""),
            "source_confidence": round(metrics.get("source_confidence", 0), 2),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def memory_max_record_count() -> int:
    try:
        return max(1, int(os.getenv("MEMORY_MAX_RECORD_COUNT", "500")))
    except ValueError:
        return 500


class FaissMemoryEngine:
    def __init__(self, max_record_count: Optional[int] = None, load_records: bool = True):
        self.index_path = Path("storage/faiss_memory")
        self.fallback_path = Path("storage/memory_records.json")
        self.max_record_count = max_record_count or memory_max_record_count()
        self.embeddings = None
        self.success_store = None
        self.failure_store = None
        self.records = {"success": [], "failure": []}
        self.stats = {
            "write_count": 0,
            "skipped_count": 0,
            "retrieval_count": 0,
            "retrieval_hits": {"success": 0, "failure": 0},
            "backend": "json_fallback",
            "faiss_error": "",
            "faiss_fallback_count": 0,
            "faiss_recovery_count": 0,
            "faiss_fallback_trace": [],
            "max_record_count": self.max_record_count,
            "peak_record_count": 0,
            "limit_reached_count": 0,
            "pruned_count": 0,
        }
        if load_records:
            self._load_records()

    def _total_record_count(self) -> int:
        return len(self.records.get("success", [])) + len(self.records.get("failure", []))

    def _update_peak_record_count(self) -> None:
        self.stats["peak_record_count"] = max(
            int(self.stats.get("peak_record_count", 0)),
            self._total_record_count(),
        )

    def _enforce_record_limit(self, preferred_bucket: Optional[str] = None) -> bool:
        self._update_peak_record_count()
        excess = self._total_record_count() - self.max_record_count
        if excess <= 0:
            return False
        self.stats["limit_reached_count"] += 1
        bucket_order = [preferred_bucket] if preferred_bucket in {"success", "failure"} else []
        bucket_order.extend(bucket for bucket in ["failure", "success"] if bucket not in bucket_order)
        removed = 0
        for bucket in bucket_order:
            while excess > 0 and self.records.get(bucket):
                self.records[bucket].pop(0)
                removed += 1
                excess -= 1
        self.stats["pruned_count"] += removed
        return removed > 0

    def _load_records(self):
        legacy_path = Path("memory_records.json")
        load_path = self.fallback_path if self.fallback_path.exists() else legacy_path
        if load_path.exists():
            try:
                self.records = json.loads(load_path.read_text(encoding="utf-8"))
                self.records = self._migrate_records(self.records)
                self._enforce_record_limit()
                self._persist_records()
            except Exception:
                self.records = {"success": [], "failure": []}

    def _memory_bucket_for_record(self, record: dict) -> str:
        metrics = record.get("reward_metrics", {})
        grounded_ctr = metrics.get("grounded_ctr", record.get("grounded_ctr", 0))
        is_grounded = metrics.get("is_grounded", False)
        is_approved = metrics.get("is_approved", False)
        return "success" if is_approved and is_grounded and grounded_ctr >= 0.04 else "failure"

    def _migrate_records(self, records: dict) -> dict:
        migrated = {"success": [], "failure": []}
        seen = {"success": set(), "failure": set()}
        for item in records.get("success", []) + records.get("failure", []):
            bucket = self._memory_bucket_for_record(item)
            fingerprint = item.get("fingerprint") or memory_fingerprint(item)
            item["fingerprint"] = fingerprint
            if fingerprint in seen[bucket]:
                continue
            migrated[bucket].append(item)
            seen[bucket].add(fingerprint)
        return migrated

    def _persist_records(self):
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        self.fallback_path.write_text(json.dumps(self.records, ensure_ascii=False, indent=2), encoding="utf-8")

    def _set_faiss_fallback(self, operation: str, exc: Exception) -> None:
        error = str(exc)
        self.stats["backend"] = "json_fallback"
        self.stats["faiss_error"] = error
        self.stats["faiss_fallback_count"] += 1
        trace = self.stats["faiss_fallback_trace"]
        matching = next(
            (
                item
                for item in trace
                if item.get("operation") == operation and item.get("error") == error
            ),
            None,
        )
        if matching:
            matching["count"] = int(matching.get("count", 1)) + 1
        else:
            trace.append({"operation": operation, "error": error, "count": 1})
        del trace[:-20]

    def _ensure_faiss(self, operation: str = "load"):
        if self.embeddings is not None:
            self.stats["backend"] = "faiss"
            return True
        previous_backend = self.stats.get("backend")
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_huggingface import HuggingFaceEmbeddings

            self.FAISS = FAISS
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            success_path = self.index_path / "success"
            failure_path = self.index_path / "failure"
            if success_path.exists():
                self.success_store = FAISS.load_local(
                    str(success_path), self.embeddings, allow_dangerous_deserialization=True
                )
            if failure_path.exists():
                self.failure_store = FAISS.load_local(
                    str(failure_path), self.embeddings, allow_dangerous_deserialization=True
                )
            self.stats["backend"] = "faiss"
            self.stats["faiss_error"] = ""
            if previous_backend == "json_fallback" and self.stats["faiss_fallback_count"]:
                self.stats["faiss_recovery_count"] += 1
            return True
        except Exception as exc:
            self._set_faiss_fallback(operation, exc)
            print(f"[Semantic Memory] FAISS unavailable, using JSON fallback: {exc}")
            return False

    def _rebuild_faiss_indexes(self) -> None:
        for bucket in ["success", "failure"]:
            save_path = self.index_path / bucket
            records = self.records.get(bucket, [])
            attr = "success_store" if bucket == "success" else "failure_store"
            if not records:
                setattr(self, attr, None)
                if save_path.exists():
                    shutil.rmtree(save_path)
                continue
            docs = [
                Document(
                    page_content=json.dumps(record, ensure_ascii=False),
                    metadata={"bucket": bucket, "ctr": record.get("predicted_ctr", 0)},
                )
                for record in records
            ]
            store = self.FAISS.from_documents(docs, self.embeddings)
            setattr(self, attr, store)
            store.save_local(str(save_path))

    def save_memory(self, record: dict):
        metrics = record.get("reward_metrics", {})
        predicted_ctr = metrics.get("predicted_ctr", record.get("predicted_ctr", 0))
        grounded_ctr = metrics.get("grounded_ctr", 0)
        is_grounded = metrics.get("is_grounded", False)
        is_approved = metrics.get("is_approved", False)
        bucket = self._memory_bucket_for_record(record)
        record["predicted_ctr"] = predicted_ctr
        record["grounded_ctr"] = grounded_ctr
        record["fingerprint"] = memory_fingerprint(record)
        if any(item.get("fingerprint") == record["fingerprint"] for item in self.records.get(bucket, [])):
            self.stats["skipped_count"] += 1
            return
        self.records.setdefault(bucket, []).append(record)
        self.stats["write_count"] += 1
        was_pruned = self._enforce_record_limit(preferred_bucket=bucket)
        self._persist_records()

        if not self._ensure_faiss(operation="write"):
            return
        if was_pruned:
            self._rebuild_faiss_indexes()
            return

        text_content = json.dumps(record, ensure_ascii=False)
        doc = Document(page_content=text_content, metadata={"bucket": bucket, "ctr": predicted_ctr})
        attr = "success_store" if bucket == "success" else "failure_store"
        store = getattr(self, attr)
        if store is None:
            setattr(self, attr, self.FAISS.from_documents([doc], self.embeddings))
        else:
            store.add_documents([doc])
        save_path = self.index_path / bucket
        getattr(self, attr).save_local(str(save_path))

    def retrieve(self, query: str, k: int = 2) -> dict:
        self.stats["retrieval_count"] += 1
        result = {"success": [], "failure": []}
        if self._ensure_faiss(operation="retrieval"):
            for bucket, store in [("success", self.success_store), ("failure", self.failure_store)]:
                if store is not None:
                    result[bucket] = [d.page_content for d in store.similarity_search(query, k=k)]
                else:
                    result[bucket] = [
                        json.dumps(item, ensure_ascii=False) for item in self.records.get(bucket, [])[-k:]
                    ]
            self._record_retrieval_hits(result)
            return result

        for bucket in ["success", "failure"]:
            result[bucket] = [
                json.dumps(item, ensure_ascii=False) for item in self.records.get(bucket, [])[-k:]
            ]
        self._record_retrieval_hits(result)
        return result

    def _record_retrieval_hits(self, result: dict) -> None:
        for bucket in ["success", "failure"]:
            self.stats["retrieval_hits"][bucket] += len(result.get(bucket, []))

    def observability_snapshot(self) -> dict:
        total_count = self._total_record_count()
        self._update_peak_record_count()
        return {
            **self.stats,
            "memory_record_count": {
                "success": len(self.records.get("success", [])),
                "failure": len(self.records.get("failure", [])),
                "total": total_count,
            },
            "memory_growth": {
                "total_records": total_count,
                "max_record_count": self.max_record_count,
                "peak_record_count": self.stats["peak_record_count"],
                "remaining_capacity": max(0, self.max_record_count - total_count),
                "limit_reached": total_count >= self.max_record_count,
                "limit_reached_count": self.stats["limit_reached_count"],
                "pruned_count": self.stats["pruned_count"],
            },
            "faiss_observability": {
                "backend": self.stats["backend"],
                "fallback_count": self.stats["faiss_fallback_count"],
                "recovery_count": self.stats["faiss_recovery_count"],
                "fallback_trace": list(self.stats["faiss_fallback_trace"]),
            },
        }


memory_engine = FaissMemoryEngine()


class CognitiveAgent:
    def __init__(
        self,
        name: str,
        role_key: str,
        schema_class: Optional[Type[BaseModel]] = None,
        temp: float = 0.7,
        reasoning_temp: Optional[float] = None,
        compile_temp: float = 0.1,
        reasoning_budget: str = "",
    ):
        self.name = name
        self.role_key = role_key
        self.schema_class = schema_class
        self.reasoning_budget = reasoning_budget
        self.model = os.getenv("MODEL_NAME", "deepseek-chat")
        self.reasoning_llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
            model=self.model,
            temperature=temp if reasoning_temp is None else reasoning_temp,
            max_retries=0,
        )
        self.compile_llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
            model=self.model,
            temperature=compile_temp,
            max_retries=0,
        )

    async def _invoke(self, messages, llm=None):
        async with api_rate_limiter:
            return await asyncio.wait_for((llm or self.reasoning_llm).ainvoke(messages), timeout=45)

    async def _reasoning_pass(self, system_prompt: str, payload: dict) -> tuple[str, int]:
        budget = f"\nReasoning budget: {self.reasoning_budget}" if self.reasoning_budget else ""
        messages = [
            SystemMessage(content=f"{system_prompt}{budget}\n\nTHINKING MODE: reason from evidence. Do not output JSON."),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2)),
        ]
        msg = await self._invoke(messages, self.reasoning_llm)
        tokens = msg.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        return msg.content, tokens

    async def _compile_pass(self, reasoning: str) -> tuple[str, int]:
        schema = json.dumps(self.schema_class.model_json_schema(), ensure_ascii=False, indent=2)
        messages = [
            SystemMessage(
                content=(
                    "COMPILER MODE: return strict JSON only. No markdown, no prose.\n\n"
                    f"JSON Schema:\n{schema}"
                )
            ),
            HumanMessage(content=reasoning),
        ]
        msg = await self._invoke(messages, self.compile_llm)
        tokens = msg.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        return msg.content, tokens

    async def _self_heal_json(self, broken_json: str, error: str) -> tuple[str, int]:
        messages = [
            SystemMessage(content="You repair JSON syntax and schema compatibility only."),
            HumanMessage(content=f"Error:\n{error}\n\nBroken JSON:\n{broken_json}"),
        ]
        msg = await self._invoke(messages, self.compile_llm)
        tokens = msg.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        return msg.content, tokens

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def run(self, inputs: dict) -> tuple[Any, NodeMetrics]:
        start_time = time.time()
        system_prompt = PromptRegistry.get(self.role_key)
        clean_inputs = {
            key: StateCompressor.check_and_compress(value) if isinstance(value, str) else value
            for key, value in inputs.items()
        }

        try:
            if not self.schema_class:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=json.dumps(clean_inputs, ensure_ascii=False, indent=2)),
                ]
                ai_msg = await self._invoke(messages, self.reasoning_llm)
                token_usage = ai_msg.response_metadata.get("token_usage", {})
                return ai_msg.content, NodeMetrics(
                    total_tokens=token_usage.get("total_tokens", 0),
                    latency_ms=(time.time() - start_time) * 1000,
                    model=self.model,
                    role_key=self.role_key,
                )

            reasoning_start = time.perf_counter()
            reasoning, reasoning_tokens = await self._reasoning_pass(system_prompt, clean_inputs)
            reasoning_latency_ms = (time.perf_counter() - reasoning_start) * 1000
            raw, compile_tokens = await self._compile_pass(reasoning)
            total_tokens = reasoning_tokens + compile_tokens
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = None
            last_error = ""
            for _ in range(2):
                try:
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = json_repair.loads(raw)
                    result = self.schema_class.model_validate(parsed)
                    break
                except Exception as exc:
                    last_error = str(exc)
                    raw, heal_tokens = await self._self_heal_json(raw, last_error)
                    total_tokens += heal_tokens
                    raw = raw.replace("```json", "").replace("```", "").strip()
            if result is None:
                raise ValueError(f"JSON self-healing failed: {last_error}")
            return result, NodeMetrics(
                total_tokens=total_tokens,
                latency_ms=(time.time() - start_time) * 1000,
                reasoning_latency_ms=reasoning_latency_ms,
                model=self.model,
                role_key=self.role_key,
                reasoning_preview=reasoning[:500],
            )
        except Exception as exc:
            traceback.print_exc()
            raise exc


class RewardEngine:
    @staticmethod
    def calculate_reward(scene_graph: dict, evidence: Optional[dict] = None) -> dict:
        evidence = evidence or {}
        raw_confidence = evidence.get("confidence", 0.5)
        source_confidence = 0.5 if raw_confidence is None else float(raw_confidence)
        review_confidence = float(evidence.get("review_confidence", source_confidence) or 0.0)
        source_types = str(evidence.get("source_type", "unknown")).split("+")
        trusted_sources = {"real_api", "local_dataset"}
        confidence_penalty = 0.0 if any(source_type in trusted_sources for source_type in source_types) else 0.15
        scenes = scene_graph.get("scenes", [])
        if not scenes:
            return {
                "retention_3s": 0,
                "dopamine_score": 0,
                "creative_score": 0,
                "grounded_score": 0,
                "predicted_ctr": 0,
                "grounded_ctr": 0,
                "creative_approved": False,
                "grounded_approved": False,
                "is_approved": False,
                "is_grounded": False,
                "failure_type": "weak_visual",
                "reason": "No scenes were generated.",
                "reward_hacking_penalty": 0.0,
                "source_confidence": source_confidence,
                "confidence_penalty": confidence_penalty,
            }

        scene_count = len(scenes)
        safe_speeds = [min(float(s.get("camera_speed", 1.0) or 1.0), 3.0) for s in scenes]
        motion_intensity = sum(safe_speeds) / scene_count
        dopamine_count = sum(1 for s in scenes if s.get("dopamine_trigger"))
        visual_quality = sum(min(len(s.get("visual_description", "")) / 120, 1.0) for s in scenes) / scene_count
        narration_quality = sum(min(len(s.get("narration", "")) / 80, 1.0) for s in scenes) / scene_count
        evidence_quotes = evidence.get("evidence_quotes", [])

        def has_real_alignment(scene: dict) -> bool:
            quote = scene.get("evidence_quote_used", "")
            pain = scene.get("linked_painpoint", "")
            if not quote or not pain or not evidence_quotes:
                return False
            return max(token_overlap(quote, evidence_quote) for evidence_quote in evidence_quotes) >= 0.25

        evidence_alignment = sum(1 for s in scenes if has_real_alignment(s)) / scene_count
        emotion_score = sum(float(s.get("emotional_intensity", 0) or 0) for s in scenes) / scene_count

        retention_3s = min(0.92, 0.25 + (motion_intensity * 0.1) + min(dopamine_count, 3) * 0.12)
        dopamine_score = min(1.0, dopamine_count / 3.0)
        fatigue_penalty = 0.2 if scene_count > 6 else 0.0
        if motion_intensity > 2.5:
            fatigue_penalty += 0.2
        reward_hacking_penalty = 0.2 if dopamine_count == scene_count and scene_count > 1 else 0.0

        creative_score = (
            0.20 * retention_3s
            + 0.20 * dopamine_score
            + 0.20 * visual_quality
            + 0.15 * narration_quality
            + 0.15 * evidence_alignment
            + 0.10 * emotion_score
            - fatigue_penalty
            - reward_hacking_penalty
        )
        grounded_score = max(0.0, creative_score - confidence_penalty) * source_confidence
        predicted_ctr = max(0.01, min(0.12, creative_score * 0.12))
        grounded_ctr = max(0.01, min(0.12, grounded_score * 0.12))

        hard_failures = []
        failure_type = ""
        if any(len(s.get("visual_description", "")) < 60 for s in scenes):
            hard_failures.append("One or more scenes have weak visual_description.")
            failure_type = failure_type or "weak_visual"
        if any(not s.get("linked_painpoint") for s in scenes):
            hard_failures.append("One or more scenes are not linked to a painpoint.")
            failure_type = failure_type or "no_evidence_alignment"
        if evidence_alignment < 0.5:
            hard_failures.append("Scenes do not cite enough real evidence quotes.")
            failure_type = failure_type or "no_evidence_alignment"
        if reward_hacking_penalty:
            hard_failures.append("All scenes set dopamine_trigger=true, possible reward hacking.")
            failure_type = failure_type or "reward_hacking"
        if not failure_type and review_confidence < 0.60:
            failure_type = "low_source_confidence"

        creative_approved = creative_score >= 0.40 and not hard_failures
        grounded_approved = grounded_score >= 0.30 and review_confidence >= 0.60 and not hard_failures

        return {
            "retention_3s": retention_3s,
            "dopamine_score": dopamine_score,
            "visual_quality": visual_quality,
            "narration_quality": narration_quality,
            "evidence_alignment": evidence_alignment,
            "emotion_score": emotion_score,
            "creative_score": creative_score,
            "grounded_score": grounded_score,
            "predicted_ctr": predicted_ctr,
            "grounded_ctr": grounded_ctr,
            "creative_approved": creative_approved,
            "grounded_approved": grounded_approved,
            "is_approved": creative_approved,
            "is_grounded": grounded_approved,
            "failure_type": failure_type,
            "reason": "; ".join(hard_failures)
            or f"motion={motion_intensity:.2f}, dopamine={dopamine_count}, fatigue_penalty={fatigue_penalty:.2f}",
            "reward_hacking_penalty": reward_hacking_penalty,
            "source_confidence": source_confidence,
            "confidence_penalty": confidence_penalty,
        }


def _model_dump(model: Any) -> dict:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _error_metrics(role_key: str, exc: Exception) -> dict:
    return NodeMetrics(status="error", error=str(exc), role_key=role_key).model_dump()


def token_overlap(a: str, b: str) -> float:
    left = {token.strip(".,!?;:\"'()[]{}").lower() for token in a.split()}
    right = {token.strip(".,!?;:\"'()[]{}").lower() for token in b.split()}
    left.discard("")
    right.discard("")
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _clear_regenerate_node_if_current(state: GraphState, current_node: str) -> dict:
    new_exec = state.get("execution_state", {}).copy()
    if new_exec.get("regenerate_node") == current_node:
        new_exec.pop("regenerate_node", None)
    return new_exec


def sanitize_patches(patches: List[dict]) -> List[dict]:
    allowed_ops = {"replace", "add", "remove"}
    safe = []
    for patch in patches:
        if patch.get("op") not in allowed_ops:
            continue
        path = patch.get("path", "")
        if not path.startswith("/scenes"):
            continue
        if patch.get("op") in {"replace", "add"} and "value" not in patch:
            continue
        if patch.get("op") == "remove":
            patch = {key: value for key, value in patch.items() if key in {"op", "path"}}
        safe.append(patch)
    return safe


def failure_to_regenerate_node(metrics: dict) -> str:
    failure_type = metrics.get("failure_type", "")
    if failure_type in {"weak_visual", "no_evidence_alignment", "reward_hacking"}:
        return "storyboard"
    if failure_type == "low_source_confidence":
        return "retrieval"
    return "governance"


def _truncate_jsonable(value: Any, max_chars: int) -> Any:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    return text[:max_chars]


def _memory_context_has_records(value: Any) -> bool:
    if not value:
        return False
    try:
        decoded = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return True
    if isinstance(decoded, dict):
        return any(bool(records) for records in decoded.values())
    return bool(decoded)


def _enrich_cognitive_telemetry(metrics: dict, node_name: str, payload: dict) -> dict:
    evidence_quotes = payload.get("evidence_quotes", []) or []
    trend_signals = payload.get("trend_signals", []) or []
    memory_context_used = _memory_context_has_records(payload.get("memory_context"))
    indicators = []
    if not evidence_quotes:
        indicators.append("no_evidence_quotes")
    if not trend_signals:
        indicators.append("no_trend_signals")
    if node_name == "strategy" and not memory_context_used:
        indicators.append("no_memory_context")
    if node_name == "cognitive_synthesis":
        for field_name in ("audience_text", "painpoint_text", "dopamine_text"):
            if not payload.get(field_name):
                indicators.append(f"missing_{field_name}")

    enriched = metrics.copy()
    enriched.update(
        {
            "node_name": node_name,
            "input_size_char": len(json.dumps(payload, ensure_ascii=False)),
            "memory_context_used": memory_context_used,
            "evidence_count": len(evidence_quotes),
            "trend_signal_count": len(trend_signals),
            "fallback": bool(indicators),
            "fallback_indicators": indicators,
        }
    )
    return enriched


def _with_memory_observability(metrics: dict) -> dict:
    snapshot = memory_engine.observability_snapshot()
    retrieval_hits = snapshot.get("retrieval_hits", {}) or {}
    record_count = snapshot.get("memory_record_count", {}) or {}
    growth = snapshot.get("memory_growth", {}) or {}
    faiss = snapshot.get("faiss_observability", {}) or {}
    enriched = metrics.copy()
    enriched.update(
        {
            "memory_observability": snapshot,
            "memory_write_count": int(snapshot.get("write_count", 0) or 0),
            "memory_skipped_count": int(snapshot.get("skipped_count", 0) or 0),
            "memory_retrieval_count": int(snapshot.get("retrieval_count", 0) or 0),
            "memory_retrieval_hits_success": int(retrieval_hits.get("success", 0) or 0),
            "memory_retrieval_hits_failure": int(retrieval_hits.get("failure", 0) or 0),
            "memory_record_count_success": int(record_count.get("success", 0) or 0),
            "memory_record_count_failure": int(record_count.get("failure", 0) or 0),
            "memory_record_count_total": int(record_count.get("total", 0) or 0),
            "memory_backend": str(snapshot.get("backend", "")),
            "memory_faiss_error": str(snapshot.get("faiss_error", "")),
            "memory_max_record_count": int(growth.get("max_record_count", 0) or 0),
            "memory_peak_record_count": int(growth.get("peak_record_count", 0) or 0),
            "memory_remaining_capacity": int(growth.get("remaining_capacity", 0) or 0),
            "memory_limit_reached": bool(growth.get("limit_reached", False)),
            "memory_limit_reached_count": int(growth.get("limit_reached_count", 0) or 0),
            "memory_pruned_count": int(growth.get("pruned_count", 0) or 0),
            "faiss_fallback_count": int(faiss.get("fallback_count", 0) or 0),
            "faiss_recovery_count": int(faiss.get("recovery_count", 0) or 0),
            "faiss_fallback_trace": faiss.get("fallback_trace", []) or [],
        }
    )
    return enriched


def compact_strategy_input(state: GraphState) -> dict:
    env = state.get("env_state", {})
    cog = state.get("cognitive_state", {})
    evidence = env.get("evidence", {}) or {}
    profile = cog.get("profile", {}) or {}
    painpoint = profile.get("painpoint", {}) if isinstance(profile, dict) else {}
    audience = profile.get("audience", {}) if isinstance(profile, dict) else {}
    dopamine = profile.get("dopamine", {}) if isinstance(profile, dict) else {}
    memory_context = memory_engine.retrieve(env.get("product_category", "general"))

    core_painpoints = []
    if isinstance(painpoint, dict):
        core_painpoints.extend(painpoint.get("physical_painpoints", [])[:3])
        core_painpoints.extend(painpoint.get("emotional_painpoints", [])[:2])

    return {
        "product_category": env.get("product_category", ""),
        "audience_summary": _truncate_jsonable(
            {
                "primary_user": audience.get("primary_user", "") if isinstance(audience, dict) else "",
                "buying_motivation": audience.get("buying_motivation", "") if isinstance(audience, dict) else "",
                "trust_barriers": audience.get("trust_barriers", [])[:3] if isinstance(audience, dict) else [],
            },
            600,
        ),
        "core_painpoints": core_painpoints[:4],
        "dopamine_summary": _truncate_jsonable(dopamine, 500),
        "evidence_quotes": evidence.get("evidence_quotes", [])[:4],
        "trend_signals": evidence.get("trend_signals", [])[:2],
        "source_confidence": {
            "source_type": evidence.get("source_type", ""),
            "confidence": evidence.get("confidence", 0),
            "review_confidence": evidence.get("review_confidence", 0),
            "trend_confidence": evidence.get("trend_confidence", 0),
            "data_warnings": evidence.get("data_warnings", [])[:3],
        },
        "memory_context": _truncate_jsonable(memory_context, 800),
    }


def compact_storyboard_input(state: GraphState) -> dict:
    env = state.get("env_state", {})
    cog = state.get("cognitive_state", {})
    evidence = env.get("evidence", {}) or {}
    strategy = cog.get("strategy", {}) or {}
    profile = cog.get("profile", {}) or {}
    painpoint = profile.get("painpoint", {}) if isinstance(profile, dict) else {}

    return {
        "product_category": env.get("product_category", ""),
        "strategy": {
            "target_user": strategy.get("target_user", ""),
            "core_pain": strategy.get("core_pain", ""),
            "visual_hook": strategy.get("visual_hook", ""),
            "broken_expectation": strategy.get("broken_expectation", ""),
            "emotional_arc": strategy.get("emotional_arc", [])[:4],
            "conversion_mechanism": strategy.get("conversion_mechanism", ""),
            "cta_logic": strategy.get("cta_logic", ""),
            "risk_notes": strategy.get("risk_notes", [])[:2],
        },
        "painpoints": {
            "physical": painpoint.get("physical_painpoints", [])[:3] if isinstance(painpoint, dict) else [],
            "emotional": painpoint.get("emotional_painpoints", [])[:2] if isinstance(painpoint, dict) else [],
        },
        "evidence_quotes": evidence.get("evidence_quotes", [])[:5],
        "trend_signals": evidence.get("trend_signals", [])[:2],
    }


def compact_synthesis_input(state: GraphState) -> dict:
    env = state.get("env_state", {})
    cog = state.get("cognitive_state", {})
    evidence = env.get("evidence", {}) or {}

    return {
        "product_category": env.get("product_category", ""),
        "evidence_quotes": evidence.get("evidence_quotes", [])[:5],
        "trend_signals": evidence.get("trend_signals", [])[:2],
        "audience_text": str(cog.get("audience_text", ""))[:900],
        "painpoint_text": str(cog.get("painpoint_text", ""))[:900],
        "dopamine_text": str(cog.get("dopamine_text", ""))[:600],
        "source_confidence": {
            "source_type": evidence.get("source_type", ""),
            "confidence": evidence.get("confidence", 0),
            "review_confidence": evidence.get("review_confidence", 0),
            "trend_confidence": evidence.get("trend_confidence", 0),
            "data_warnings": evidence.get("data_warnings", [])[:3],
        },
    }


async def planner_node(state: GraphState) -> dict:
    agent = CognitiveAgent("Planner", "planner", ExecutionPlan, reasoning_temp=0.2)
    available_tools = enabled_source_tools()
    try:
        res, metrics = await agent.run(
            {
                "url": state.get("env_state", {}).get("asin_url", ""),
                "available_tools": available_tools,
            }
        )
        metrics_data = _model_dump(metrics)
    except Exception as exc:
        res = None
        metrics_data = _error_metrics("planner", exc)
    category = res.product_category if res else "general"
    complexity = res.cognitive_complexity if res else "high"
    selected_tools = [tool for tool in (res.selected_tools if res and res.selected_tools else []) if tool in available_tools]
    if "local_review_dataset" not in selected_tools:
        selected_tools.insert(0, "local_review_dataset")
    if "tiktok_trend_mock" not in selected_tools:
        selected_tools.append("tiktok_trend_mock")
    preferred_order = [
        "amazon_review_api",
        "reddit_review_api",
        "local_review_dataset",
        "amazon_review_mock",
        "tiktok_trend_api",
        "tiktok_trend_mock",
    ]
    selected_tools = [tool for tool in preferred_order if tool in selected_tools]
    new_env = state.get("env_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    new_env.update(
        {
            "product_category": category,
            "complexity": complexity,
            "available_tools": available_tools,
            "selected_tools": selected_tools,
        }
    )
    new_tele["planner"] = metrics_data
    return {"env_state": new_env, "telemetry_state": new_tele}


async def retrieval_node(state: GraphState) -> dict:
    env = state.get("env_state", {})
    is_regeneration = state.get("execution_state", {}).get("regenerate_node") == "retrieval"
    selected_tools = env.get("selected_tools") or ["amazon_review_mock"]
    url = env.get("asin_url", "")
    retrieval_start = time.perf_counter()
    sources = []
    source_traces = []
    review_items = []
    trend_items = []
    failed_real_roles = set()

    def adapter_info(tool_name: str) -> tuple[str, bool]:
        if tool_name == "amazon_review_mock":
            return "InlineAmazonReviewMock", True
        try:
            return (
                tool_runtime.adapter_registry.adapter_name(tool_name),
                tool_runtime.adapter_registry.is_enabled(tool_name),
            )
        except ValueError:
            return tool_name, False

    def append_trace(tool_name: str, source: ToolSource, elapsed_ms: float, fallback_reason: str = "") -> None:
        adapter_name, enabled = adapter_info(tool_name)
        fallback = bool(fallback_reason)
        source_traces.append(
            {
                "source_name": tool_name,
                "adapter_name": adapter_name,
                "enabled": enabled,
                "fallback": fallback,
                "fallback_reason": fallback_reason,
                "fetch_latency_ms": elapsed_ms,
                "source_type": source.source_type,
                "confidence": source.confidence,
                "source_role": source.source_role,
            }
        )

    for tool_name in selected_tools:
        if tool_name == "amazon_review_mock" and review_items:
            continue
        fetch_start = time.perf_counter()
        try:
            source = await tool_runtime.run(tool_name, {"url": url, "env_state": env})
            source_data = _model_dump(source)
            sources.append(source_data)
            reason = ""
            if source.items and source.source_role in failed_real_roles:
                reason = f"{source.source_role}_real_source_unavailable"
            append_trace(tool_name, source, (time.perf_counter() - fetch_start) * 1000, reason)
            if source.source_type in {"unavailable", "tool_error"} and tool_name.endswith("_api"):
                failed_real_roles.add(source.source_role)
            if source.source_role == "review":
                review_items.extend(source.items)
            elif source.source_role == "trend":
                trend_items.extend(source.items)
        except Exception as exc:
            adapter_name, enabled = adapter_info(tool_name)
            sources.append(
                {
                    "source_type": "tool_error",
                    "source_role": "review" if "review" in tool_name or "amazon" in tool_name else "trend",
                    "source_url": url,
                    "confidence": 0.0,
                    "items": [],
                    "tool_name": tool_name,
                    "error": str(exc),
                }
            )
            source_traces.append(
                {
                    "source_name": tool_name,
                    "adapter_name": adapter_name,
                    "enabled": enabled,
                    "fallback": False,
                    "fallback_reason": f"tool_error: {exc}",
                    "fetch_latency_ms": (time.perf_counter() - fetch_start) * 1000,
                    "source_type": "tool_error",
                    "confidence": 0.0,
                    "source_role": "review" if "review" in tool_name or "amazon" in tool_name else "trend",
                }
            )
    if not review_items and "amazon_review_mock" not in selected_tools:
        fetch_start = time.perf_counter()
        source = await tool_runtime.run("amazon_review_mock", {"url": url, "env_state": env})
        source_data = _model_dump(source)
        sources.append(source_data)
        review_items.extend(source.items)
        append_trace(
            "amazon_review_mock",
            source,
            (time.perf_counter() - fetch_start) * 1000,
            "no_review_source_returned_items",
        )
    source = next((item for item in sources if item.get("source_role") == "review" and item.get("items")), sources[0] if sources else {})
    new_env = state.get("env_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    new_env["tool_sources"] = sources
    new_env["review_source"] = source
    new_env["raw_reviews"] = review_items
    new_env["trend_signals"] = trend_items
    new_tele["retrieval_sources"] = {
        "total_tokens": 0,
        "latency_ms": (time.perf_counter() - retrieval_start) * 1000,
        "retries": 0,
        "status": "success",
        "error": None,
        "model": "tool_runtime",
        "role_key": "retrieval_sources",
        "source_traces": source_traces,
    }
    new_tele["retrieval_sources"] = _with_memory_observability(new_tele["retrieval_sources"])
    if is_regeneration:
        new_exec = state.get("execution_state", {}).copy()
        new_exec.pop("storyboard", None)
        new_exec.pop("reflection", None)
        new_exec.pop("sanitized_patches", None)
        new_exec.pop("reflection_patch_error", None)
        new_exec.pop("regenerate_node", None)
        new_exec["analysis_attempts"] = 0
        return {
            "env_state": new_env,
            "cognitive_state": {},
            "execution_state": new_exec,
            "telemetry_state": new_tele,
        }
    return {
        "env_state": new_env,
        "execution_state": _clear_regenerate_node_if_current(state, "retrieval"),
        "telemetry_state": new_tele,
    }


async def evidence_builder_node(state: GraphState) -> dict:
    env = state.get("env_state", {})
    tool_sources = env.get("tool_sources", [])
    raw_reviews = env.get("raw_reviews", [])
    trend_signals = env.get("trend_signals", [])
    quotes = [r.get("text", "") for r in raw_reviews if r.get("text")][:8]
    trend_quotes = [item.get("text") or item.get("trend", "") for item in trend_signals if item.get("text") or item.get("trend")][:8]
    review_sources = [
        src for src in tool_sources if src.get("source_role") == "review" and src.get("items")
    ]
    trend_sources = [
        src for src in tool_sources if src.get("source_role") == "trend" and src.get("items")
    ]
    review_confidences = [float(src.get("confidence", 0.0) or 0.0) for src in review_sources]
    trend_confidences = [float(src.get("confidence", 0.0) or 0.0) for src in trend_sources]
    review_confidence = sum(review_confidences) / len(review_confidences) if review_confidences else 0.0
    trend_confidence = sum(trend_confidences) / len(trend_confidences) if trend_confidences else 0.0
    avg_confidence = (0.8 * review_confidence) + (0.2 * trend_confidence)
    source_types = sorted({src.get("source_type", "unknown") for src in tool_sources}) or ["unknown"]
    warnings = []
    for src in tool_sources:
        source_type = src.get("source_type", "unknown")
        if source_type in {"mock", "llm_inferred"}:
            warnings.append(f"{source_type} source used; confidence reduced.")
        elif source_type == "unavailable":
            warnings.append("Requested tool unavailable; fallback may be used.")
        elif source_type == "tool_error":
            warnings.append(f"Tool error: {src.get('error', '')}")
        elif source_type == "local_dataset":
            warnings.append("Local curated review dataset used.")
    evidence = EvidenceBundle(
        source_type="+".join(source_types),
        source_url=env.get("asin_url", ""),
        confidence=avg_confidence,
        review_confidence=review_confidence,
        trend_confidence=trend_confidence,
        review_count=len(raw_reviews),
        evidence_quotes=quotes,
        trend_signals=trend_quotes,
        data_warnings=warnings,
    )
    new_env = env.copy()
    new_env["evidence"] = _model_dump(evidence)
    return {"env_state": new_env, "execution_state": _clear_regenerate_node_if_current(state, "evidence_builder")}


async def parallel_analysis_node(state: GraphState) -> dict:
    evidence = state.get("env_state", {}).get("evidence", {})
    raw_data = json.dumps(
        {
            "review_evidence": state.get("env_state", {}).get("raw_reviews", []),
            "trend_signals": state.get("env_state", {}).get("trend_signals", []),
            "evidence": evidence,
        },
        ensure_ascii=False,
    )
    dopamine_data = json.dumps(
        {
            "evidence_quotes": evidence.get("evidence_quotes", [])[:5],
            "trend_signals": evidence.get("trend_signals", [])[:2],
        },
        ensure_ascii=False,
    )
    agents = {
        "audience": CognitiveAgent("Audience", "audience"),
        "painpoint": CognitiveAgent("Painpoint", "painpoint"),
        "dopamine": CognitiveAgent("Dopamine", "dopamine", temp=0.3),
    }

    async def run_agent(key: str, agent: CognitiveAgent):
        try:
            input_data = dopamine_data if key == "dopamine" else raw_data
            res, metrics = await agent.run({"data": input_data})
            return key, res or "", _model_dump(metrics)
        except Exception as exc:
            return key, "", _error_metrics(key, exc)

    results = await asyncio.gather(*(run_agent(k, v) for k, v in agents.items()))
    new_cog = state.get("cognitive_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    new_exec = state.get("execution_state", {}).copy()
    new_exec["analysis_attempts"] = new_exec.get("analysis_attempts", 0) + 1
    for key, content, metrics in results:
        new_cog[f"{key}_text"] = content
        if key == "dopamine":
            metrics = _with_memory_observability(metrics)
        new_tele[f"analysis_{key}"] = metrics
    if new_exec.get("regenerate_node") == "parallel_analysis":
        new_exec.pop("regenerate_node", None)
    return {
        "cognitive_state": new_cog,
        "telemetry_state": new_tele,
        "execution_state": new_exec,
    }


async def cognitive_synthesis_node(state: GraphState) -> dict:
    agent = CognitiveAgent(
        "Cognitive Synthesis",
        "synthesis",
        CognitiveProfile,
        reasoning_temp=0.3,
        reasoning_budget="Max 220 words. Extract only profile fields needed by strategy and storyboard.",
    )
    payload = {}
    try:
        payload = compact_synthesis_input(state)
        res, metrics = await agent.run(payload)
        metrics_data = _model_dump(metrics)
    except Exception as exc:
        res = None
        metrics_data = _error_metrics("synthesis", exc)
    metrics_data = _with_memory_observability(
        _enrich_cognitive_telemetry(metrics_data, "cognitive_synthesis", payload)
    )
    new_cog = state.get("cognitive_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    if res:
        new_cog["profile"] = _model_dump(res)
    new_tele["cognitive_synthesis"] = metrics_data
    return {
        "cognitive_state": new_cog,
        "telemetry_state": new_tele,
        "execution_state": _clear_regenerate_node_if_current(state, "cognitive_synthesis"),
    }


async def strategy_node(state: GraphState) -> dict:
    agent = CognitiveAgent(
        "Strategy",
        "strategy",
        StrategicNarrative,
        reasoning_temp=0.9,
        compile_temp=0.1,
        reasoning_budget="Max 180 words. Use bullets. No rhetorical expansion.",
    )
    payload = {}
    try:
        payload = compact_strategy_input(state)
        res, metrics = await agent.run(payload)
        metrics_data = _model_dump(metrics)
    except Exception as exc:
        res = None
        metrics_data = _error_metrics("strategy", exc)
    metrics_data = _with_memory_observability(
        _enrich_cognitive_telemetry(metrics_data, "strategy", payload)
    )
    new_cog = state.get("cognitive_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    if res:
        new_cog["strategy"] = _model_dump(res)
    new_tele["strategy"] = metrics_data
    return {
        "cognitive_state": new_cog,
        "telemetry_state": new_tele,
        "execution_state": _clear_regenerate_node_if_current(state, "strategy"),
    }


async def storyboard_node(state: GraphState) -> dict:
    agent = CognitiveAgent(
        "Storyboard",
        "storyboard",
        Storyboard,
        reasoning_temp=0.7,
        compile_temp=0.1,
        reasoning_budget="Max 220 words. Produce compact scene logic only. No cinematic essay.",
    )
    try:
        res, metrics = await agent.run(compact_storyboard_input(state))
        metrics_data = _model_dump(metrics)
    except Exception as exc:
        res = None
        metrics_data = _error_metrics("storyboard", exc)
    new_exec = state.get("execution_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    if res:
        new_exec["storyboard"] = _model_dump(res)
        new_exec.pop("regenerate_node", None)
    new_tele["storyboard"] = metrics_data
    return {"execution_state": new_exec, "telemetry_state": new_tele}


async def governance_node(state: GraphState) -> dict:
    world_metrics = RewardEngine.calculate_reward(
        state.get("execution_state", {}).get("storyboard", {}),
        state.get("env_state", {}).get("evidence", {}),
    )
    return {"world_metrics": world_metrics, "execution_state": _clear_regenerate_node_if_current(state, "governance")}


async def reflection_patch_node(state: GraphState) -> dict:
    count = state.get("revision_count", 0)
    agent = CognitiveAgent("Reflection", "reflection", ReflectionResult, reasoning_temp=0.5, compile_temp=0.1)
    try:
        res, metrics = await agent.run(
            {
                "metrics": state.get("world_metrics", {}),
                "evidence": state.get("env_state", {}).get("evidence", {}),
                "profile": state.get("cognitive_state", {}).get("profile", {}),
                "strategy": state.get("cognitive_state", {}).get("strategy", {}),
                "storyboard": state.get("execution_state", {}).get("storyboard", {}),
            }
        )
        metrics_data = _model_dump(metrics)
    except Exception as exc:
        res = None
        metrics_data = _error_metrics("reflection", exc)
    new_exec = state.get("execution_state", {}).copy()
    new_tele = state.get("telemetry_state", {}).copy()
    new_tele["reflection"] = metrics_data
    if res:
        patch_applied = False
        reflection = _model_dump(res)
        new_exec["reflection"] = reflection
        if res.failed_layer == "storyboard" and res.patches:
            try:
                patch_list = sanitize_patches([_model_dump(p) for p in res.patches])
                if patch_list:
                    new_exec["storyboard"] = jsonpatch.JsonPatch(patch_list).apply(
                        state.get("execution_state", {}).get("storyboard", {}), in_place=False
                    )
                    new_exec["sanitized_patches"] = patch_list
                    patch_applied = True
                else:
                    new_exec["reflection_patch_error"] = "No valid patches after sanitization."
            except Exception as exc:
                new_exec["reflection_patch_error"] = str(exc)
        if patch_applied:
            new_exec["regenerate_node"] = "governance"
        elif res.regenerate_node:
            new_exec["regenerate_node"] = res.regenerate_node
        else:
            new_exec["regenerate_node"] = failure_to_regenerate_node(state.get("world_metrics", {}))
    elif state.get("world_metrics", {}).get("failure_type"):
        new_exec["regenerate_node"] = failure_to_regenerate_node(state.get("world_metrics", {}))
    return {"execution_state": new_exec, "telemetry_state": new_tele, "revision_count": count + 1}


async def analytics_node(state: GraphState) -> dict:
    metrics = state.get("world_metrics", {})
    reflection = state.get("execution_state", {}).get("reflection", {})
    record = {
        "product_type": state.get("env_state", {}).get("product_category", "general"),
        "pain_signature": state.get("cognitive_state", {}).get("profile", {}).get("painpoint", {}),
        "strategy": state.get("cognitive_state", {}).get("strategy", {}),
        "storyboard_pattern": state.get("execution_state", {}).get("storyboard", {}),
        "predicted_ctr": metrics.get("predicted_ctr", 0),
        "retention_3s": metrics.get("retention_3s", 0),
        "failure_reason": metrics.get("reason", ""),
        "failed_layer": reflection.get("failed_layer", ""),
        "reward_metrics": metrics,
    }
    memory_engine.save_memory(record)
    new_tele = state.get("telemetry_state", {}).copy()
    new_tele["analytics_memory"] = _with_memory_observability(
        {
            "total_tokens": 0,
            "latency_ms": 0.0,
            "retries": 0,
            "status": "success",
            "error": None,
            "model": "memory_engine",
            "role_key": "analytics_memory",
            "node_name": "analytics_memory",
        }
    )
    return {"telemetry_state": new_tele}


def planner_router(state: GraphState) -> str:
    env = state.get("env_state", {})
    cog = state.get("cognitive_state", {})
    exec_state = state.get("execution_state", {})
    if not env.get("raw_reviews"):
        return "retrieval"
    if not env.get("evidence"):
        return "evidence_builder"
    missing_analysis = not cog.get("audience_text") or not cog.get("painpoint_text") or not cog.get("dopamine_text")
    if missing_analysis and exec_state.get("analysis_attempts", 0) < 2:
        return "parallel_analysis"
    if missing_analysis:
        return "cognitive_synthesis"
    if not cog.get("profile"):
        return "cognitive_synthesis"
    if not cog.get("strategy"):
        return "strategy"
    return "storyboard"


def governance_router(state: GraphState) -> str:
    metrics = state.get("world_metrics", {})
    if state.get("revision_count", 0) >= 3:
        return "analytics"
    if metrics.get("is_approved") and metrics.get("is_grounded"):
        return "analytics"
    return "reflection"


def reflection_router(state: GraphState) -> str:
    target = state.get("execution_state", {}).get("regenerate_node")
    allowed = {"retrieval", "parallel_analysis", "cognitive_synthesis", "strategy", "storyboard", "governance"}
    return target if target in allowed else "governance"


def build_async_system():
    workflow = StateGraph(GraphState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("evidence_builder", evidence_builder_node)
    workflow.add_node("parallel_analysis", parallel_analysis_node)
    workflow.add_node("cognitive_synthesis", cognitive_synthesis_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("storyboard", storyboard_node)
    workflow.add_node("governance", governance_node)
    workflow.add_node("reflection", reflection_patch_node)
    workflow.add_node("analytics", analytics_node)

    workflow.set_entry_point("planner")
    workflow.add_conditional_edges("planner", planner_router)
    workflow.add_edge("retrieval", "evidence_builder")
    workflow.add_edge("evidence_builder", "parallel_analysis")
    workflow.add_edge("parallel_analysis", "cognitive_synthesis")
    workflow.add_edge("cognitive_synthesis", "strategy")
    workflow.add_edge("strategy", "storyboard")
    workflow.add_edge("storyboard", "governance")
    workflow.add_conditional_edges("governance", governance_router)
    workflow.add_conditional_edges("reflection", reflection_router)
    workflow.add_edge("analytics", END)
    return workflow.compile()


copilot_engine = build_async_system()
