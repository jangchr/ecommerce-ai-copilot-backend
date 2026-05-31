from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewWorkspaceReview(BaseModel):
    rating: float | int | str | None = None
    title: str = ""
    text: str = ""
    helpful_count: int | None = None
    source_section: str = ""
    captured_at: str = ""


class ReviewWorkspaceProduct(BaseModel):
    platform: str = "unknown"
    url: str = ""
    asin: str = ""
    title: str = ""
    brand: str = ""
    price: str = ""
    rating: float | int | str | None = None
    review_count: int | str | None = None
    bullet_points: list[str] = Field(default_factory=list)
    description: str = ""
    reviews: list[ReviewWorkspaceReview] = Field(default_factory=list)


class ReviewWorkspaceRequest(BaseModel):
    workspace_id: str = "review_workspace"
    source: str = "manual"
    products: list[ReviewWorkspaceProduct] = Field(default_factory=list)
    goal: str = "tiktok_ctr"
    output_language: str = "en"


class ReviewThemeSummary(BaseModel):
    label: str
    evidence_count: int = 0
    evidence_quotes: list[str] = Field(default_factory=list)


class ReviewProductSummary(BaseModel):
    title: str
    url: str = ""
    review_count: int = 0
    high_signal_review_count: int = 0
    top_pain_points: list[str] = Field(default_factory=list)
    top_liked_points: list[str] = Field(default_factory=list)



class ReviewSourceGroupSummary(BaseModel):
    source_type: str = ""
    label: str = ""
    review_count: int = 0
    high_signal_review_count: int = 0
    asin_count: int = 0
    top_asins: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)
    metadata_summary: dict[str, object] = Field(default_factory=dict)


class ReviewSourceBreakdown(BaseModel):
    total_reviews: int = 0
    raw_review_count: int = 0
    duplicate_review_count: int = 0
    main_product_reviews: int = 0
    variant_reviews: int = 0
    low_star_reviews: int = 0
    verified_purchase_reviews: int = 0
    recent_reviews: int = 0
    unknown_reviews: int = 0
    asin_review_counts: dict[str, int] = Field(default_factory=dict)
    source_groups: list[ReviewSourceGroupSummary] = Field(default_factory=list)
    guidance: list[str] = Field(default_factory=list)


class ReviewSampleInterpretation(BaseModel):
    sample_type: str = ""
    sample_size_note: str = ""
    suitable_for: list[str] = Field(default_factory=list)
    not_suitable_for: list[str] = Field(default_factory=list)
    strongest_signals: list[str] = Field(default_factory=list)
    recommended_creative_directions: list[str] = Field(default_factory=list)
    evidence_usage_summary: list[str] = Field(default_factory=list)


class ReviewVideoScript(BaseModel):
    duration_label: str = ""
    hook: str = ""
    voiceover: list[str] = Field(default_factory=list)
    on_screen_text: list[str] = Field(default_factory=list)
    cta: str = ""
    evidence_used: list[str] = Field(default_factory=list)


class ReviewVideoScriptPack(BaseModel):
    positioning_note: str = ""
    scripts: list[ReviewVideoScript] = Field(default_factory=list)


class ReviewWorkspaceResponse(BaseModel):
    workspace_id: str
    product_count: int
    total_reviews: int
    high_signal_review_count: int
    common_pain_points: list[ReviewThemeSummary] = Field(default_factory=list)
    buyer_objections: list[ReviewThemeSummary] = Field(default_factory=list)
    liked_points: list[ReviewThemeSummary] = Field(default_factory=list)
    use_cases: list[ReviewThemeSummary] = Field(default_factory=list)
    product_summaries: list[ReviewProductSummary] = Field(default_factory=list)
    source_breakdown: ReviewSourceBreakdown = Field(default_factory=ReviewSourceBreakdown)
    creative_angles: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)
    sample_interpretation: ReviewSampleInterpretation = Field(default_factory=ReviewSampleInterpretation)
    video_script_pack: ReviewVideoScriptPack = Field(default_factory=ReviewVideoScriptPack)
