"""
NLP Understanding & Intent Router Service.
Parses natural-language queries into structured intents:
- 'player_analysis': single player progression, stats, consistency
- 'player_comparison': multi-player head-to-head comparison
- 'match_analysis': specific match details, scorecards, encounters between teams
"""
import re
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.cricket_data_service import load_alias_lookup

class StructuredQuery(BaseModel):
    intent: str = Field(default="player_analysis", description="'player_analysis', 'player_comparison', or 'match_analysis'")
    players: List[str] = Field(default_factory=list, description="Canonical player names")
    teams: List[str] = Field(default_factory=list, description="Teams mentioned (for match or opponent analysis)")
    opponent: Optional[str] = Field(None, description="Opponent team name if specified")
    format: Optional[str] = Field(None, description="Cricket format: ODI, T20, or Test")
    year: Optional[int] = Field(None, description="Year if specified (e.g. 2023, 2024)")
    start_date: Optional[str] = Field(None, description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="End date YYYY-MM-DD")
    recent_n: Optional[int] = Field(None, description="Filter to last N innings")
    analysis_type: str = Field(default="progression", description="Type: progression, comparison, consistency, match_summary")
    chart_preference: str = Field(default="line", description="Preferred visualization: line or bar")
    needs_clarification: bool = Field(default=False)

TEAMS = [
    "Australia", "India", "England", "Pakistan", "South Africa",
    "New Zealand", "West Indies", "Sri Lanka", "Afghanistan", "Bangladesh",
    "Netherlands", "Ireland", "Zimbabwe", "Scotland", "United States of America", "Nepal", "Namibia", "Oman"
]

MATCH_KEYWORDS = [
    "match", "game", "scorecard", "final", "semi final", "semifinal", "clash", "encounter",
    "who won", "result", "score", "versus", "vs", "head to head"
]

FOLLOW_UP_PRONOUNS = ["he", "his", "him", "her", "their", "they", "this player", "the player", "same player"]

def parse_with_rules(prompt: str, context: Optional[Dict[str, Any]] = None) -> StructuredQuery:
    lower = prompt.lower()
    alias_map = load_alias_lookup()

    # 1. Detect Teams mentioned
    matched_teams: List[str] = []
    for team in TEAMS:
        if re.search(r"\b" + re.escape(team.lower()) + r"\b", lower):
            if team not in matched_teams:
                matched_teams.append(team)

    # 2. Year detection (e.g., 2017 to 2026)
    year_match = re.search(r"\b(20[12]\d)\b", lower)
    detected_year = int(year_match.group(1)) if year_match else None

    # 3. Format detection
    detected_format = None
    if re.search(r"\bt20\b|\bit20\b|\bt20i\b|\bt20s\b|twenty20", lower):
        detected_format = "T20"
    elif re.search(r"\bodi\b|\bodis\b|\bone day\b|\b50 over\b", lower):
        detected_format = "ODI"
    elif re.search(r"\btest\b|\btests\b|\bfirst class\b", lower):
        detected_format = "Test"

    # 4. Player matching
    matched_spans = []
    matched_players: List[str] = []
    sorted_aliases = sorted(alias_map.keys(), key=lambda x: (len(x.split()), len(x)), reverse=True)

    for alias in sorted_aliases:
        if len(alias) <= 2:
            continue
        pattern = r"\b" + re.escape(alias) + r"\b"
        for match in re.finditer(pattern, lower):
            span = match.span()
            overlap = any(s[0] <= span[0] and span[1] <= s[1] for s in matched_spans)
            if not overlap:
                matched_spans.append(span)
                _, canonical_name = alias_map[alias]
                if canonical_name not in matched_players:
                    matched_players.append(canonical_name)

    # Context inheritance
    has_pronoun = any(re.search(r"\b" + re.escape(pronoun) + r"\b", lower) for pronoun in FOLLOW_UP_PRONOUNS)
    is_short_followup = len(lower.split()) <= 6 and ("last" in lower or "what about" in lower or "in t20" in lower or "in odi" in lower)

    if not matched_players and context and context.get("players") and (has_pronoun or is_short_followup):
        matched_players = list(context["players"])

    if not detected_format and context and context.get("format") and context.get("format") != "All formats" and (has_pronoun or is_short_followup):
        detected_format = context["format"]

    opponent = matched_teams[0] if (matched_players and matched_teams) else None
    if not opponent and len(matched_teams) > 1:
        opponent = matched_teams[1]

    # Recent N
    recent_n = None
    last_n_match = re.search(r"\blast\s+(\d+)\b", lower)
    if last_n_match:
        recent_n = int(last_n_match.group(1))

    # 5. Determine Intent
    is_match_query = (
        (len(matched_teams) >= 2 and any(k in lower for k in MATCH_KEYWORDS)) or
        ("match" in lower and (len(matched_teams) >= 1 or detected_year)) or
        ("scorecard" in lower) or
        ("who won" in lower)
    )

    if is_match_query and not matched_players:
        intent = "match_analysis"
        analysis_type = "match_summary"
        chart_pref = "bar"
    elif len(matched_players) >= 2 or ("compare" in lower and len(matched_players) >= 1):
        intent = "player_comparison"
        analysis_type = "comparison"
        chart_pref = "bar"
    else:
        intent = "player_analysis"
        analysis_type = "consistency" if ("consisten" in lower or "variance" in lower) else "progression"
        chart_pref = "line"

    return StructuredQuery(
        intent=intent,
        players=matched_players,
        teams=matched_teams,
        opponent=opponent,
        format=detected_format,
        year=detected_year,
        start_date=None,
        end_date=None,
        recent_n=recent_n,
        analysis_type=analysis_type,
        chart_preference=chart_pref,
        needs_clarification=(not matched_players and not matched_teams),
    )

def extract_query_entities(prompt: str, context: Optional[Dict[str, Any]] = None) -> StructuredQuery:
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            system_instruction = (
                "You are an NLP entity extraction and routing engine for cricket queries. "
                "Classify the question intent as either 'player_analysis', 'player_comparison', or 'match_analysis'. "
                "Extract: players (list of canonical player names), teams (list of countries), "
                "opponent (string or null), format ('ODI', 'T20', 'Test', or null), year (integer or null), "
                "recent_n (integer or null), analysis_type ('progression', 'comparison', 'match_summary'), "
                "and chart_preference ('line' or 'bar'). Never output text outside JSON."
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=f"Prompt: {prompt}\nContext: {json.dumps(context or {})}",
                config={"response_mime_type": "application/json", "system_instruction": system_instruction}
            )
            data = json.loads(response.text)
            parsed = StructuredQuery(**data)
            if parsed.players or parsed.teams:
                return parsed
        except Exception:
            pass

    return parse_with_rules(prompt, context)
