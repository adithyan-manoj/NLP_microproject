"""
NLP Understanding Service.
Extracts entities, intent, formats, opponents, and date boundaries from natural-language queries.
Employs Google GenAI SDK with structured response if configured, paired with a reliable
deterministic regex and rule-based parser fallback.
"""
import re
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.cricket_data_service import resolve_player_identity

class StructuredQuery(BaseModel):
    players: List[str] = Field(default_factory=list, description="Canonical names or identifiers of players mentioned")
    opponent: Optional[str] = Field(None, description="Opponent team name if specified")
    format: Optional[str] = Field(None, description="Cricket format: ODI, T20, or Test")
    start_date: Optional[str] = Field(None, description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="End date YYYY-MM-DD")
    recent_n: Optional[int] = Field(None, description="Filter to last N innings if requested")
    analysis_type: str = Field(default="progression", description="Type: progression, comparison, consistency, milestone")
    chart_preference: str = Field(default="line", description="Preferred visualization: line or bar")
    needs_clarification: bool = Field(default=False)

TEAMS = [
    "Australia", "India", "England", "Pakistan", "South Africa",
    "New Zealand", "West Indies", "Sri Lanka", "Afghanistan", "Bangladesh",
    "Netherlands", "Ireland", "Zimbabwe", "Scotland"
]

def parse_with_rules(prompt: str, context: Optional[Dict[str, Any]] = None) -> StructuredQuery:
    """
    Deterministic rule and regex extractor for cricket terminology.
    """
    lower = prompt.lower()

    # 1. Player matching
    players = []
    # Test common player names
    candidate_tokens = [
        "virat kohli", "kohli", "rohit sharma", "rohit", "david warner", "warner",
        "steve smith", "smith", "babar azam", "babar", "jos buttler", "buttler",
        "joe root", "root", "jasprit bumrah", "bumrah", "kane williamson", "williamson",
        "ms dhoni", "dhoni", "travis head", "head", "shubman gill", "gill",
        "kl rahul", "rahul", "mohammad rizwan", "rizwan", "mitchell starc", "starc",
        "pat cummins", "cummins", "mohammed shami", "shami", "glenn maxwell", "maxwell",
        "quinton de kock", "de kock", "kusal mendis", "mendis", "shai hope", "hope"
    ]

    for token in candidate_tokens:
        if re.search(r"\b" + re.escape(token) + r"\b", lower):
            resolved = resolve_player_identity(token)
            if resolved and resolved[1] not in players:
                players.append(resolved[1])

    # Context inheritance for conversational follow-ups
    if not players and context and context.get("players"):
        players = list(context["players"])

    # Default player if none mentioned
    if not players:
        players = ["Virat Kohli"]

    # 2. Format extraction
    detected_format = None
    if re.search(r"\bt20\b|\bit20\b|\bt20i\b|\bt20s\b|twenty20", lower):
        detected_format = "T20"
    elif re.search(r"\bodi\b|\bodis\b|\bone day\b|\b50 over\b", lower):
        detected_format = "ODI"
    elif re.search(r"\btest\b|\btests\b|\bfirst class\b", lower):
        detected_format = "Test"
    elif context and context.get("format") and context.get("format") != "All formats":
        detected_format = context["format"]

    # 3. Opponent extraction
    detected_opponent = None
    for team in TEAMS:
        if re.search(r"\b" + re.escape(team.lower()) + r"\b", lower):
            detected_opponent = team
            break
    if not detected_opponent and context and context.get("opponent"):
        detected_opponent = context["opponent"]

    # 4. Recent N innings
    recent_n = None
    last_n_match = re.search(r"\blast\s+(\d+)\b", lower)
    if last_n_match:
        recent_n = int(last_n_match.group(1))

    # 5. Analysis Type & Chart Preference
    if len(players) > 1 or "compare" in lower or "vs" in lower and len(players) >= 2:
        analysis_type = "comparison"
        chart_pref = "bar"
    elif "consisten" in lower or "spread" in lower or "variance" in lower:
        analysis_type = "consistency"
        chart_pref = "bar"
    else:
        analysis_type = "progression"
        chart_pref = "line"

    return StructuredQuery(
        players=players,
        opponent=detected_opponent,
        format=detected_format,
        start_date=None,
        end_date=None,
        recent_n=recent_n,
        analysis_type=analysis_type,
        chart_preference=chart_pref,
        needs_clarification=False,
    )

def extract_query_entities(prompt: str, context: Optional[Dict[str, Any]] = None) -> StructuredQuery:
    """
    Extracts structured query entities using Gemini if API key is configured;
    falls back seamlessly to deterministic rules.
    """
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            system_instruction = (
                "You are an NLP entity extraction engine for cricket statistics. "
                "Analyze the user's question and optional conversational context. "
                "Return a structured JSON object with keys: players (array of canonical strings), "
                "opponent (string or null), format (T20, ODI, Test, or null), recent_n (integer or null), "
                "analysis_type ('progression', 'comparison', 'consistency'), "
                "chart_preference ('line' or 'bar'), and needs_clarification (boolean). "
                "Never output text outside the JSON."
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=f"Prompt: {prompt}\nContext: {json.dumps(context or {})}",
                config={"response_mime_type": "application/json", "system_instruction": system_instruction}
            )
            data = json.loads(response.text)
            return StructuredQuery(**data)
        except Exception:
            # Graceful fallback on API timeout or error
            pass

    return parse_with_rules(prompt, context)

