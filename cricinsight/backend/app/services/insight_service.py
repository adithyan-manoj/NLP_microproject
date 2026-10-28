"""
RAG (Retrieval-Augmented Generation) & Insight Synthesizer.
Retrieves precise OLAP facts, statistical metrics, match scorecards, and historical records
from DuckDB, constructs structured context, and synthesizes accurate, evidence-grounded insights.
"""
from typing import Dict, Any, List, Optional
from app.core.config import settings

def generate_analytical_insight(
    query_scope: Dict[str, Any],
    stats: Dict[str, Any],
    observations: List[str]
) -> str:
    """Backward-compatible wrapper for synthesize_rag_response."""
    return synthesize_rag_response(
        query_intent="player_analysis",
        scope=query_scope,
        stats=stats,
        observations=observations
    )
def synthesize_rag_response(
    query_intent: str,
    scope: Dict[str, Any],
    stats: Dict[str, Any],
    observations: List[str],
    match_data: Optional[Dict[str, Any]] = None,
    comparison_data: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    RAG synthesis:
    1. Retrieval: Exact statistical and scorecard facts retrieved from DuckDB.
    2. Augmentation: Grounded context formulated with boundaries and strict anti-hallucination prompts.
    3. Generation: Gemini LLM synthesis if API key is present; deterministic template synthesis as reliable fallback.
    """

    # Deterministic fallback synthesis
    if query_intent == "match_analysis" and match_data:
        m_teams = " vs ".join(match_data.get("teams", []))
        m_venue = match_data.get("venue", "International Venue")
        m_date = match_data.get("date", "")
        m_res = match_data.get("result", "")
        m_comp = match_data.get("competition", "")
        inn_summaries = []
        for inn in match_data.get("innings", []):
            inn_summaries.append(f"{inn['batting_team']} {inn['runs']}/{inn['wickets']} in {inn['overs']} ov")

        fallback = (
            f"In the {m_comp} match played at {m_venue} on {m_date}, {m_teams} clashed. "
            f"Scores: {', '.join(inn_summaries)}. {m_res}. "
            f"Key individual highlights: {', '.join(observations[:2])}."
        )

    elif query_intent == "player_comparison" and comparison_data:
        p_summaries = []
        for p in comparison_data:
            p_summaries.append(
                f"{p['player_name']}: {p['total_runs']:,} runs, avg {p['batting_average']}, SR {p['strike_rate']} across {p['innings_count']} innings"
            )
        fmt = scope.get("format", "international")
        fallback = (
            f"Head-to-head {fmt} comparison: {'; '.join(p_summaries)}. "
            f"{' '.join(observations[:2])}"
        )

    else:
        # Single player progression
        player = ", ".join(scope.get("players", ["Player"]))
        opponent = scope.get("opponent")
        fmt = scope.get("format")
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

    # Augmented Generation with Gemini
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            rag_prompt = (
                "You are an expert cricket performance analyst answering an analytical query using RAG. "
                "Synthesize a concise, 2-to-3 sentence analytical summary strictly based on the following retrieved facts:\n"
                "- Query Intent: {intent}\n"
                "- Scope: {scope}\n"
                "- Retrieved Stats: {stats}\n"
                "- Observations: {observations}\n"
                "- Match Record: {match_record}\n\n"
                "Constraints:\n"
                "1. Cite ONLY retrieved numbers, players, and teams above. Zero hallucinations.\n"
                "2. Highlight key performance takeaways or turning points."
            ).format(
                intent=query_intent,
                scope=scope,
                stats=stats,
                observations=observations,
                match_record=match_data or comparison_data or "N/A"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=rag_prompt,
            )
            if response.text and len(response.text.strip()) > 15:
                return response.text.strip()
        except Exception:
            pass

    return fallback
