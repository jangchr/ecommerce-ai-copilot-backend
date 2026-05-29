from __future__ import annotations

from pydantic import BaseModel

from schemas.review_workspace import ReviewWorkspaceProduct, ReviewWorkspaceRequest, ReviewWorkspaceResponse, ReviewWorkspaceReview


class ReviewPasteParseRequest(BaseModel):
    raw_text: str
    platform: str = "unknown"
    product_title: str = ""
    url: str = ""
    asin: str = ""
    source_section: str = "pasted_review"


class ReviewPasteParseResponse(BaseModel):
    review_count: int
    high_signal_review_count: int
    reviews: list[ReviewWorkspaceReview]
    workspace_product: ReviewWorkspaceProduct
    data_warnings: list[str] = []


class PastedReviewWorkspaceAnalyzeRequest(ReviewPasteParseRequest):
    workspace_id: str = "pasted_review_workspace"
    goal: str = "tiktok_ctr"
    output_language: str = "en"


class PastedReviewWorkspaceAnalyzeResponse(BaseModel):
    parsed: ReviewPasteParseResponse
    analysis: ReviewWorkspaceResponse
