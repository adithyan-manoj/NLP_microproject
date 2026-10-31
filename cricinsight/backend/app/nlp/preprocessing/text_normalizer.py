"""
NLP Preprocessing Pipeline for CricInsight.
Handles:
1. Text Normalization & Whitespace Sanitation
2. Cricket Domain Lexicon & Abbreviation Expansion
3. Season, Competition, and Format Extraction
4. Statistical Category & Metric Target Extraction
"""

import re
from typing import Dict, Any, List, Optional, Tuple

CRICKET_LEXICON = {
    r"\bipl\b": "Indian Premier League",
    r"\bbbl\b": "Big Bash League",
    r"\bcpl\b": "Caribbean Premier League",
    r"\bpsl\b": "Pakistan Super League",
    r"\bwpl\b": "Women's Premier League",
    r"\bt20i\b": "international t20",
    r"\bt20\b": "twenty20",
    r"\bodi\b": "one day international",
    r"\bsr\b": "strike rate",
    r"\bavg\b": "batting average",
    r"\becon\b": "economy rate",
    r"\bdls\b": "Duckworth-Lewis-Stern",
    r"\bnrr\b": "net run rate",
    r"\bc&b\b": "caught and bowled",
    r"\blbw\b": "leg before wicket",
}

COMPETITION_MAPPINGS = {
    "ipl": "IPL",
    "indian premier league": "IPL",
    "bbl": "BBL",
    "big bash league": "BBL",
    "cpl": "CPL",
    "caribbean premier league": "CPL",
    "psl": "PSL",
    "pakistan super league": "PSL",
    "wpl": "WPL",
    "womens premier league": "WPL",
    "world cup": "World Cup",
    "icc cricket world cup": "ODI World Cup",
    "t20 world cup": "T20 World Cup",
}

FORMAT_MAPPINGS = {
    "ipl": "T20",
    "bbl": "T20",
    "cpl": "T20",
    "psl": "T20",
    "wpl": "T20",
    "t20": "T20",
    "twenty20": "T20",
    "it20": "IT20",
    "t20i": "IT20",
    "odi": "ODI",
    "one day": "ODI",
    "test": "Test",
}

ALL_BATTING_METRICS = [
    "matches",
    "innings",
    "runs",
    "balls_faced",
    "not_outs",
    "batting_average",
    "strike_rate",
    "high_score",
    "fifties",
    "hundreds",
    "fours",
    "sixes",
]


class TextNormalizer:
    """Preprocesses natural language queries before provider interpretation."""

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Cleans whitespace, lowercase-normalizes, and expands key abbreviations."""
        normalized = text.strip()
        # Collapse multiple whitespace
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @classmethod
    def extract_cricket_entities(cls, query: str) -> Dict[str, Any]:
        """
        Extracts deterministic cricket parameters:
        - competition (IPL, BBL, etc.)
        - season (e.g. 2022, 2023)
        - format (T20, ODI, Test, IT20)
        - category (batting / bowling)
        - requested metrics
        """
        query_lower = query.lower()

        # 1. Season extraction (4-digit year between 1877 and 2030)
        season = None
        season_match = re.search(r"\b(18[7-9]\d|19\d{2}|20[0-2]\d|2030)\b", query_lower)
        if season_match:
            season = season_match.group(1)

        # 2. Competition extraction
        competition = None
        for key, comp_val in COMPETITION_MAPPINGS.items():
            if re.search(rf"\b{re.escape(key)}\b", query_lower):
                competition = comp_val
                break

        # 3. Format extraction
        detected_format = None
        for key, fmt_val in FORMAT_MAPPINGS.items():
            if re.search(rf"\b{re.escape(key)}\b", query_lower):
                detected_format = fmt_val
                break

        # 4. Statistical category
        category = "batting"
        if any(w in query_lower for w in ["bowling", "wickets", "overs", "economy", "maidens", "best bowling", "spell"]):
            category = "bowling"

        # 5. Required metrics
        # If user asks for general statistics (e.g. "show me statistics", "stats in 2022"),
        # provide the comprehensive official cricket card.
        metrics = list(ALL_BATTING_METRICS)
        specific_metrics_found = []
        if "strike rate" in query_lower or "sr" in query_lower:
            specific_metrics_found.append("strike_rate")
        if "average" in query_lower or "avg" in query_lower:
            specific_metrics_found.append("batting_average")
        if "highest score" in query_lower or "high score" in query_lower or "top score" in query_lower:
            specific_metrics_found.append("high_score")
        if "fifty" in query_lower or "fifties" in query_lower or "50s" in query_lower:
            specific_metrics_found.append("fifties")
        if "century" in query_lower or "centuries" in query_lower or "hundreds" in query_lower or "100s" in query_lower:
            specific_metrics_found.append("hundreds")
        if "four" in query_lower or "fours" in query_lower or "4s" in query_lower:
            specific_metrics_found.append("fours")
        if "six" in query_lower or "sixes" in query_lower or "6s" in query_lower:
            specific_metrics_found.append("sixes")
        if "runs" in query_lower:
            specific_metrics_found.append("runs")

        # If user asked specifically for only one or two metrics (e.g. "what was his strike rate"),
        # keep specific metrics; if general "stats" or "statistics", include full set.
        if specific_metrics_found and not any(w in query_lower for w in ["stats", "statistics", "all", "summary", "record", "performance"]):
            metrics = specific_metrics_found

        return {
            "competition": competition,
            "season": season,
            "format": detected_format,
            "category": category,
            "metrics": metrics,
        }
