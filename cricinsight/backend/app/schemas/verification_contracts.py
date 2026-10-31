"""
Verification and Dual Pipeline Contracts for CricInsight.
Defines schemas for:
- CricketMetricSet (standardized batting/bowling metrics)
- LocalComputationEvidence (independent deterministic calculation)
- ExternalVerificationEvidence (independent Gemini/external research)
- FieldComparisonItem & DiscrepancyReport (field-by-field audit)
- VerifiedResult & DualPipelineAudit (provenance-tracked verified payload)
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class CricketMetricSet(BaseModel):
    """Standardized cricket statistical metrics across local and external pipelines."""
    matches: Optional[int] = Field(None, description="Number of matches played")
    innings: Optional[int] = Field(None, description="Number of innings batted")
    runs: Optional[int] = Field(None, description="Total runs scored")
    balls_faced: Optional[int] = Field(None, description="Total balls faced (excluding wides)")
    not_outs: Optional[int] = Field(None, description="Number of not-out innings")
    batting_average: Optional[float] = Field(None, description="Batting average: runs / dismissals")
    strike_rate: Optional[float] = Field(None, description="Batting strike rate: (runs / balls) * 100")
    high_score: Optional[int] = Field(None, description="Highest individual score")
    high_score_not_out: Optional[bool] = Field(False, description="Whether highest score was not out")
    fifties: Optional[int] = Field(None, description="Number of scores between 50 and 99")
    hundreds: Optional[int] = Field(None, description="Number of scores 100 or above")
    fours: Optional[int] = Field(None, description="Number of boundaries (4s)")
    sixes: Optional[int] = Field(None, description="Number of sixes (6s)")

    @field_validator("high_score", mode="before")
    @classmethod
    def parse_high_score(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            clean = v.replace("*", "").replace(",", "").strip()
            try:
                return int(float(clean))
            except (ValueError, TypeError):
                return None
        return v

    @field_validator("runs", "balls_faced", "not_outs", "fifties", "hundreds", "fours", "sixes", "matches", "innings", mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            clean = v.replace(",", "").strip()
            try:
                return int(float(clean))
            except (ValueError, TypeError):
                return None
        return v

    @field_validator("batting_average", "strike_rate", mode="before")
    @classmethod
    def parse_float_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            clean = v.replace(",", "").strip()
            try:
                return float(clean)
            except (ValueError, TypeError):
                return None
        return v


class LocalComputationEvidence(BaseModel):
    """
    Independent local deterministic calculation result.
    Produced strictly by Python + DuckDB/PostgreSQL analytics engine without LLM influence.
    """
    player: str
    competition: Optional[str] = None
    season: Optional[str] = None
    category: str = "batting"
    metrics: CricketMetricSet
    granularity: Literal["ball_by_ball", "match_scorecard", "scorecard", "career_record"] = "ball_by_ball"
    matches_count: int = 0
    innings_count: int = 0
    match_ids: List[str] = Field(default_factory=list)
    calculated_at: str = ""
    provenance: str = "Local Deterministic Analytics Engine (Cricsheet/DuckDB)"


class ExternalVerificationEvidence(BaseModel):
    """
    Independent external verification evidence.
    Retrieved independently by Gemini with Google Search Grounding from official cricket sources.
    Must NOT receive Qwen's numbers or local calculation before retrieval.
    """
    player: str
    competition: Optional[str] = None
    season: Optional[str] = None
    category: str = "batting"
    metrics: CricketMetricSet
    source_name: str = "Official Cricket Archives (ESPNcricinfo / IPL / ICC)"
    source_urls: List[str] = Field(default_factory=list)
    retrieval_status: Literal["success", "partial", "failed", "disabled"] = "success"
    retrieval_timestamp: str = ""
    error_message: Optional[str] = None


class FieldComparisonItem(BaseModel):
    """Comparison of a single metric field between local and external pipelines."""
    metric: str
    local_value: Any
    external_value: Any
    status: Literal["MATCH", "DISCREPANCY", "LOCAL_MISSING", "EXTERNAL_MISSING", "DEFINITION_DIFFERENCE"]
    difference_explanation: Optional[str] = None


class DiscrepancyReport(BaseModel):
    """
    Comprehensive field-level discrepancy analysis report.
    Itemizes differences and categorizes the underlying root causes.
    """
    has_discrepancy: bool = False
    total_fields_compared: int = 0
    matching_fields: int = 0
    discrepant_fields: int = 0
    comparisons: List[FieldComparisonItem] = Field(default_factory=list)
    detected_issues: List[str] = Field(
        default_factory=list,
        description="e.g. MISSING_LOCAL_MATCHES, DUPLICATE_RECORDS, INCORRECT_LOCAL_CALCULATION, STATISTICAL_DEFINITION_DIFFERENCE, EXTERNAL_SOURCE_ERROR"
    )
    resolution_strategy: str = "PRESERVE_LOCAL"
    audit_trail: List[str] = Field(default_factory=list)


class VerifiedResult(BaseModel):
    """
    The final verified cricket statistical result.
    Grounded in audited evidence with provenance tracking.
    """
    metrics: CricketMetricSet
    verification_status: Literal[
        "VERIFIED_CONSISTENT",
        "ENRICHED_AND_RECALCULATED",
        "LOCAL_PRESERVED_EXTERNAL_REJECTED",
        "CORRECTED_LOCAL",
        "PARTIAL_UNVERIFIED",
        "EXTERNAL_FAILED"
    ]
    confidence_score: float = 1.0
    provenance_summary: str = ""
    discrepancy_resolved: bool = True
    notes: List[str] = Field(default_factory=list)


class DualPipelineAudit(BaseModel):
    """
    Complete dual-pipeline audit object.
    Preserves original local computation alongside external verification for complete auditability.
    """
    local_computation: LocalComputationEvidence
    external_verification: Optional[ExternalVerificationEvidence] = None
    discrepancy_report: Optional[DiscrepancyReport] = None
    verified_result: VerifiedResult
    pipeline_latency_ms: float = 0.0
