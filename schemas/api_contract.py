from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class GrowthRequest(BaseModel):
    url: str
    goal: str = "tiktok_ctr"
    real_source_mode: Literal["local", "amazon_shadow"] = "local"
    output_language: str = "en"


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
    output_language: str = "en"


class TranslationRequest(BaseModel):
    text: str
    target_language: str = "zh-CN"


class TranslationResponse(BaseModel):
    translated_text: str
    target_language: str
    request_id: Optional[str] = None


class ProductDescriptionRequest(BaseModel):
    product_name: str
    product_category: Optional[str] = None
    product_description: str
    customer_pain_points: str
    target_platform: str = "TikTok"
    goal: str = "tiktok_ctr"
    output_language: str = "en"


class ProductDescriptionResponse(BaseModel):
    status: str
    data: GenerateCopilotData
    request_id: Optional[str] = None
    output_language: str = "en"


class PastedReviewsRequest(BaseModel):
    product_name: str
    product_category: Optional[str] = None
    product_description: Optional[str] = None
    pasted_reviews: str
    target_platform: str = "TikTok"
    goal: str = "tiktok_ctr"
    output_language: str = "en"


class PastedReviewsResponse(BaseModel):
    status: str
    data: GenerateCopilotData
    request_id: Optional[str] = None
    output_language: str = "en"


class AmazonIntakeRequest(BaseModel):
    url: str
    product_category: str = "amazon_product"


class AmazonReviewItem(BaseModel):
    text: str = ""
    source: str = ""
    rating: int = 0
    date: str = ""
    title: str = ""


class AmazonReviewInsights(BaseModel):
    pain_points: List[str] = Field(default_factory=list)
    buyer_objections: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)
    emotional_triggers: List[str] = Field(default_factory=list)
    evidence_quotes: List[str] = Field(default_factory=list)


class AmazonIntakeData(BaseModel):
    input_url: str = ""
    is_supported: bool = False
    asin: str = ""
    normalized_url: str = ""
    provider_status: str = ""
    source_confidence: float = 0.0
    product_title: str = ""
    rating: str = ""
    review_count: str = ""
    price: str = ""
    category_hint: str = ""
    bullet_points: List[str] = Field(default_factory=list)
    evidence_preview: List[str] = Field(default_factory=list)
    review_items: List[AmazonReviewItem] = Field(default_factory=list)
    review_insights: AmazonReviewInsights = Field(default_factory=AmazonReviewInsights)
    data_warnings: List[str] = Field(default_factory=list)
    fallback_required: bool = True
    fallback_message: str = ""
    error: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AmazonIntakeResponse(BaseModel):
    status: str
    data: AmazonIntakeData
    request_id: Optional[str] = None


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
