"""
Insight Generation Service.
Produces concise, evidence-based commentary and analytical observations strictly
grounded in already computed statistics, without hallucinations or invented facts.
"""
from typing import Dict, Any, List, Optional
from app.core.config import settings

def generate_analytical_insight(
    query_scope: Dict[str, Any],
    stats: Dict[str, Any],
    observations: List[str]
) -> str:
    """
    Generates a natural-language analytical explanation.
    Uses Gemini API if key is present, otherwise produces a mathematically grounded template summary.
    """
    # Fallback / deterministic grounded insight
    player = ", ".join(query_scope.get("players", ["Player"]))
    opponent = query_scope.get("opponent")
    fmt = query_scope.get("format")
    analysis_type = query_scope.get("analysis_type", "progression")

    if "Comparison" in analysis_type or len(query_scope.get("players", [])) > 1:
        fallback = (
            f"Head-to-head comparison between {player}{f' in {fmt}' if fmt else ''}: "
            f"metrics reflect aggregate performance and efficiency across filtered matches. "
            f"{' '.join(observations[:2])}"
        )
    else:
        runs = stats.get("total_runs", 0)
        avg = stats.get("batting_average", 0)
        sr = stats.get("strike_rate", 0)
        high = stats.get("high_score", 0)
        not_out = "*" if stats.get("high_score_not_out") else ""
        innings = stats.get("innings_count", 0)
        centuries = stats.get("centuries", 0)
        fifties = stats.get("fifties", 0)
        std_dev = stats.get("std_deviation", 0)
        rating = stats.get("consistency_rating", "Moderate")

        fallback = (
            f"Across {innings} innings{f' against {opponent}' if opponent else ''}"
            f"{f' in {fmt}' if fmt else ''}, {player} compiled {runs:,} runs "
            f"at a batting average of {avg} and a strike rate of {sr}. His top score was {high}{not_out}, "
            f"registering {centuries} centuries and {fifties} half-centuries. "
            f"With a standard deviation of \u00b1{std_dev}, the scoring profile reflects {rating.lower()}."
        )

    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                "You are an expert sports data analyst. Write a concise, 2-to-3 sentence analytical summary "
                "explaining the following cricket performance numbers. Strictly follow these constraints:\n"
                "1. Base your statements ONLY on the provided calculated stats and observations.\n"
                "2. DO NOT invent match dates, tournament stories, or commentary not present in the data.\n"
                "3. Include metrics such as average, strike rate, and consistency.\n\n"
                f"Scope: {query_scope}\n"
                f"Stats: {stats}\n"
                f"Observations: {observations}"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            if response.text and len(response.text.strip()) > 10:
                return response.text.strip()
        except Exception:
            pass

    return fallback

