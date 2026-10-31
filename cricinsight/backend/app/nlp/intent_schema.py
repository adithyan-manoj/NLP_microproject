from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
import re

MatchFormat = Literal["Test", "ODI", "T20", "IT20", "MDM", "ODM"]
QueryIntent = Literal[
    "player_summary",
    "comparison",
    "recent_form",
    "consistency",
    "opponent_analysis",
    "venue_analysis",
    "score_distribution",
    "unsupported",
    "clarification",
]
ChartType = Literal["line", "bar", "grouped_bar", "histogram", "scatter", "table", "kpi_only"]

class IntentSchema(BaseModel):
    """
    Canonical structured query interpretation schema shared identically
    across Gemini (primary) and Qwen (local fallback).
    """
    intent: QueryIntent = Field(
        default="player_summary",
        description="The primary analytical intent of the user's cricket question."
    )
    players: List[str] = Field(
        default_factory=list,
        description="List of canonical or mentioned player names."
    )
    opponent: Optional[str] = Field(
        default=None,
        description="Opponent team name if filtered (e.g. Australia, Pakistan)."
    )
    team: Optional[str] = Field(
        default=None,
        description="Team the player plays for if specified."
    )
    format: Optional[MatchFormat] = Field(
        default=None,
        description="Match format. Note: T20 (domestic) and IT20 (international) are strictly distinct."
    )
    competition: Optional[str] = Field(
        default=None,
        description="Tournament or league name if specified (e.g. Indian Premier League, IPL, Big Bash League)."
    )
    season: Optional[str] = Field(
        default=None,
        description="Tournament or calendar season if specified (e.g. 2022, 2023, 2024)."
    )
    statistical_category: Optional[Literal["batting", "bowling", "all_round", "fielding"]] = Field(
        default="batting",
        description="Statistical category: batting, bowling, all_round, fielding."
    )
    venue: Optional[str] = Field(
        default=None,
        description="Venue or stadium name if filtered."
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format."
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format."
    )
    last_n_innings: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Number of recent innings to analyze (distinct from calendar date or matches)."
    )
    last_n_matches: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Number of recent matches to analyze."
    )
    metrics: List[str] = Field(
        default_factory=lambda: ["runs", "batting_average", "strike_rate"],
        description="Target metrics requested (e.g. runs, batting_average, strike_rate, economy_rate)."
    )
    chart_preference: Optional[ChartType] = Field(
        default=None,
        description="Visualization format best suited for this query."
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if player, format, or scope is ambiguous and requires user clarification."
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="A concise clarifying question to ask the user."
    )
    clarification_options: Optional[List[str]] = Field(
        default=None,
        description="Possible candidate choices for the user to select from."
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="NLP query understanding confidence score (0.0 to 1.0)."
    )
    schema_version: str = Field(
        default="1.0.0",
        description="Version tag of this canonical schema."
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Strict YYYY-MM-DD format validation
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"Invalid date format '{v}'. Expected YYYY-MM-DD.")
        return v
