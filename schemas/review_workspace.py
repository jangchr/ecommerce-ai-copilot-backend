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
    creative_angles: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)
