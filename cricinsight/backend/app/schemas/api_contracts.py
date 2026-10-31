"""
Pydantic API Request and Response Contracts for CricInsight.
Defines strict schemas for the chat query endpoint, dataset coverage,
and evaluation endpoints consumed by the Flutter frontend.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.nlp.confidence import ConfidenceBreakdown
from app.schemas.verification_contracts import DualPipelineAudit

class ChatQueryRequest(BaseModel):
    prompt: str = Field(..., description="Natural language cricket query")
    session_id: Optional[str] = Field(None, description="Optional conversational session ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Active conversational context")

class ProviderInfo(BaseModel):
    name: str = Field(..., description="gemini | qwen | deterministic_rule")
    model: str = Field(..., description="Model identifier used for generation")
    latency_ms: float = Field(default=0.0)
    fallback_used: bool = Field(default=False)
    fallback_reason: Optional[str] = None

class ChatQueryResponse(BaseModel):
    request_id: str
    status: str = Field(..., description="success | clarification_required | no_data | unsupported_query | error")
    answer: str
    interpretation: Dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceBreakdown
    provider: ProviderInfo
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    chart: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_coverage: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    clarification_required: bool = False
    clarification_options: Optional[List[str]] = None
    verification_pipeline: Optional[DualPipelineAudit] = Field(
        default=None,
        description="Independent local computation and parallel external verification audit payload"
    )
