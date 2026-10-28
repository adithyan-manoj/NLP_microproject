"""
NLP Understanding Service.
Extracts entities, intent, formats, opponents, and date boundaries from natural-language queries.
"""
import re
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.cricket_data_service import resolve_player_identity, load_alias_lookup

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

# Words that indicate conversational follow-ups referring to previously discussed player
FOLLOW_UP_PRONOUNS = ["he", "his", "him", "her", "their", "they", "this player", "the player", "same player"]

def parse_with_rules(prompt: str, context: Optional[Dict[str, Any]] = None) -> StructuredQuery:
    """
    Deterministic rule and alias matcher for cricket terminology.
    Matches player aliases, preventing sub-token overlapping collisions.
    """
    lower = prompt.lower()
    alias_map = load_alias_lookup()

    # Track matched character spans in prompt so shorter sub-strings aren't doubly matched
    # E.g. "David Warner" should not match both "David Warner" and "David"
    matched_spans = []
    matched_players: List[str] = []

    # Sort aliases by word count descending, then by length descending
    sorted_aliases = sorted(alias_map.keys(), key=lambda x: (len(x.split()), len(x)), reverse=True)

    for alias in sorted_aliases:
        if len(alias) <= 2:
            continue
        pattern = r"\b" + re.escape(alias) + r"\b"
        for match in re.finditer(pattern, lower):
            span = match.span()
            # Check if this span overlaps with an already matched longer span
            overlap = any(s[0] <= span[0] and span[1] <= s[1] for s in matched_spans)
            if not overlap:
                matched_spans.append(span)
                _, canonical_name = alias_map[alias]
                if canonical_name not in matched_players:
                    matched_players.append(canonical_name)

    # Context inheritance: only inherit player if no new player was mentioned
    # AND the prompt explicitly uses a follow-up pronoun or is a short follow-up
    has_pronoun = any(re.search(r"\b" + re.escape(pronoun) + r"\b", lower) for pronoun in FOLLOW_UP_PRONOUNS)
    is_short_followup = len(lower.split()) <= 6 and ("last" in lower or "what about" in lower or "in t20" in lower or "in odi" in lower)

    if not matched_players and context and context.get("players") and (has_pronoun or is_short_followup):
        matched_players = list(context["players"])

    # Format extraction
    detected_format = None
    if re.search(r"\bt20\b|\bit20\b|\bt20i\b|\bt20s\b|twenty20", lower):
        detected_format = "T20"
    elif re.search(r"\bodi\b|\bodis\b|\bone day\b|\b50 over\b", lower):
        detected_format = "ODI"
    elif re.search(r"\btest\b|\btests\b|\bfirst class\b", lower):
        detected_format = "Test"
    elif context and context.get("format") and context.get("format") != "All formats" and (has_pronoun or is_short_followup):
        detected_format = context["format"]

    # Opponent extraction
    detected_opponent = None
    for team in TEAMS:
        if re.search(r"\b" + re.escape(team.lower()) + r"\b", lower):
            detected_opponent = team
            break
    if not detected_opponent and context and context.get("opponent") and (has_pronoun or is_short_followup):
        detected_opponent = context["opponent"]

    # Recent N innings
    recent_n = None
    last_n_match = re.search(r"\blast\s+(\d+)\b", lower)
    if last_n_match:
        recent_n = int(last_n_match.group(1))

    # Analysis Type & Chart Preference
    if len(matched_players) > 1 or "compare" in lower or (" vs " in lower and len(matched_players) >= 2):
        analysis_type = "comparison"
        chart_pref = "bar"
    elif "consisten" in lower or "spread" in lower or "variance" in lower:
        analysis_type = "consistency"
        chart_pref = "bar"
    else:
        analysis_type = "progression"
        chart_pref = "line"

    return StructuredQuery(
        players=matched_players,
        opponent=detected_opponent,
        format=detected_format,
        start_date=None,
        end_date=None,
        recent_n=recent_n,
        analysis_type=analysis_type,
        chart_preference=chart_pref,
        needs_clarification=len(matched_players) == 0,
    )

def extract_query_entities(prompt: str, context: Optional[Dict[str, Any]] = None) -> StructuredQuery:
    """
    Extracts structured query entities using Gemini if API key is configured;
    falls back seamlessly to deterministic rule parser.
    """
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            system_instruction = (
                "You are an NLP entity extraction engine for cricket statistics. "
                "Analyze the user's question and optional conversational context. "
                "Return a structured JSON object with keys: players (array of canonical player names mentioned in the prompt, or empty list if no player mentioned), "
                "opponent (string or null), format (T20, ODI, Test, or null), recent_n (integer or null), "
                "analysis_type ('progression', 'comparison', 'consistency'), "
                "chart_preference ('line' or 'bar'), and needs_clarification (boolean). "
                "Never default to Virat Kohli unless his name is explicitly in the prompt or context. "
                "Never output text outside the JSON."
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=f"Prompt: {prompt}\nContext: {json.dumps(context or {})}",
                config={"response_mime_type": "application/json", "system_instruction": system_instruction}
            )
            data = json.loads(response.text)
            parsed = StructuredQuery(**data)
            if parsed.players:
                return parsed
        except Exception:
            pass

    return parse_with_rules(prompt, context)
