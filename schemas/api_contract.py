from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class GrowthRequest(BaseModel):
    url: str
    goal: str = "tiktok_ctr"
    real_source_mode: Literal["local", "amazon_shadow"] = "local"


class EvidencePayload(BaseModel):
    source_type: str = ""
    source_url: str = ""
    confidence: float = 0.0
    review_confidence: float = 0.0
    trend_confidence: float = 0.0
    review_count: int = 0
    evidence_quotes: List[str] = Field(default_factory=list)
    trend_signals: List[str] = Field(default_factory=list)
    data_warnings: List[str] = Field(default_factory=list)


class ProductInsights(BaseModel):
    pain_points: List[str] = Field(default_factory=list)
    user_complaint_cluster: List[str] = Field(default_factory=list)
    evidence: EvidencePayload = Field(default_factory=EvidencePayload)


class ProductAudience(BaseModel):
    primary: str = ""
    sensitivity: str = ""
    trust_barriers: List[str] = Field(default_factory=list)


class ProductStrategy(BaseModel):
    core_hook_strategy: str = ""
    emotional_trigger: str = ""


class TikTokScript(BaseModel):
    hook: str = ""
    cta: str = ""


class ProductAssets(BaseModel):
    tiktok_script: TikTokScript = Field(default_factory=TikTokScript)
    storyboard: Dict[str, Any] = Field(default_factory=dict)


class ProductEvaluation(BaseModel):
    confidence_score: float = 0.0
    risk_level: str = ""
    reasoning: str = ""
    is_approved: bool = False
    is_grounded: bool = False
    creative_approved: bool = False
    grounded_approved: bool = False


class GenerateCopilotData(BaseModel):
    insights: ProductInsights
    audience: ProductAudience
    strategy: ProductStrategy
    assets: ProductAssets
    evaluation: ProductEvaluation
    feedback: str = ""


class GenerateCopilotResponse(BaseModel):
    status: str
    data: GenerateCopilotData


class DebugCopilotResponse(BaseModel):
    request_id: Optional[str] = None
    product_category: Optional[str] = None
    evidence: Optional[EvidencePayload] = None
    cognitive_state: Dict[str, Any] = Field(default_factory=dict)
    execution_state: Dict[str, Any] = Field(default_factory=dict)
    world_metrics: Dict[str, Any] = Field(default_factory=dict)
    telemetry: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    telemetry_summary: Dict[str, Any] = Field(default_factory=dict)
    memory_observability: Dict[str, Any] = Field(default_factory=dict)
    shadow_sources: Dict[str, Any] = Field(default_factory=dict)
    regenerate_node: Optional[str] = None
    revision_count: int = 0
