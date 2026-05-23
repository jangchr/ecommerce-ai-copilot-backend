from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SourceProbeRequest(BaseModel):
    product_category: str
    url: Optional[str] = None
    providers: List[str] = Field(default_factory=list)
    debug_only: bool = True


class SourceProbeResult(BaseModel):
    provider: str
    status: Literal["disabled", "unavailable", "success", "error"]
    source_confidence: float = 0.0
    latency_ms: float = 0.0
    error: Optional[str] = None
    evidence_preview: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceProbeTelemetry(BaseModel):
    total_latency_ms: float = 0.0
    provider_count: int = 0
    success_count: int = 0
    disabled_count: int = 0
    unavailable_count: int = 0
    error_count: int = 0
    fallback_required: bool


class SourceProbeResponse(BaseModel):
    request_id: Optional[str] = None
    debug_only: bool
    product_category: str
    results: List[SourceProbeResult] = Field(default_factory=list)
    fallback_required: bool
    telemetry: SourceProbeTelemetry
    memory_write_allowed: bool = False
