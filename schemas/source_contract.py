from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ReviewRecord(BaseModel):
    rating: int = 0
    text: str = ""
    date: str = ""


class SourceEvidence(BaseModel):
    source_type: str = ""
    source_url: str = ""
    product_category: str = ""
    confidence: float = 0.0
    review_confidence: float = 0.0
    trend_confidence: float = 0.0
    review_count: int = 0
    reviews: List[ReviewRecord] = Field(default_factory=list)
    evidence_quotes: List[str] = Field(default_factory=list)
    trend_signals: List[str] = Field(default_factory=list)
    data_warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
