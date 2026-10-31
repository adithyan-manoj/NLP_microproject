import re
import time
from typing import Tuple, List, Optional
from app.nlp.intent_schema import IntentSchema
from app.nlp.entity_resolution import EntityResolver
from app.nlp.temporal_parser import TemporalParser

class DeterministicProvider:
    """
    Deterministic regex & rule-based parser that executes when both LLMs are unavailable
    or rate-limited, guaranteeing 100% operational resilience for core analytics.
    """

    KNOWN_PLAYERS = [
        "Virat Kohli", "Rohit Sharma", "Sachin Tendulkar", "MS Dhoni",
        "Jasprit Bumrah", "Babar Azam", "Steve Smith", "Joe Root",
        "Kane Williamson", "David Warner", "Pat Cummins", "Mitchell Starc",
        "Ravindra Jadeja", "Hardik Pandya", "KL Rahul", "Shubman Gill"
    ]

    OPPONENTS = [
        "Australia", "India", "Pakistan", "England", "South Africa",
        "New Zealand", "West Indies", "Sri Lanka", "Bangladesh", "Afghanistan"
    ]

    @classmethod
    def interpret_query(cls, query: str) -> Tuple[IntentSchema, float]:
        start = time.perf_counter()
        q = query.lower()

        # 1. Intent identification
        if any(w in q for w in ["highest wicket", "most wicket", "top wicket", "leading wicket"]):
            intent = "bowling_record"
        elif any(w in q for w in ["highest score", "most runs", "most centuries", "world record", "record", "leaderboard", "highest team"]):
            intent = "historical_record"
        elif any(w in q for w in ["compare", "vs", "versus", "better than"]):
            intent = "comparison"
        elif any(w in q for w in ["last", "past", "recent", "form", "streak"]):
            intent = "recent_form"
        elif any(w in q for w in ["consistent", "consistency", "variance", "std dev"]):
            intent = "consistency"
        elif any(w in q for w in ["against", "vs"]):
            intent = "opponent_analysis"
        elif any(w in q for w in ["at venue", "stadium", "ground"]):
            intent = "venue_analysis"
        else:
            intent = "player_summary"

        # 2. Extract players
        found_players = []
        q_tokens = re.findall(r"\b\w+\b", q)
        for p in cls.KNOWN_PLAYERS:
            parts = p.lower().split()
            # Match full name or any distinctive name part (e.g. 'Kohli', 'Rohit', 'Bumrah')
            if p.lower() in q or any(part in q_tokens for part in parts):
                res = EntityResolver.resolve_player(p)
                if res.canonical_name not in found_players:
                    found_players.append(res.canonical_name)

        # 3. Extract opponent
        found_opponent = None
        for opp in cls.OPPONENTS:
            if f"against {opp.lower()}" in q or f"vs {opp.lower()}" in q or (opp.lower() in q and opp not in found_players):
                found_opponent = opp
                break

        # 4. Extract format
        found_format = None
        if "t20i" in q or "t20 international" in q:
            found_format = "IT20"
        elif "t20" in q or "ipl" in q:
            found_format = "T20"
        elif "odi" in q or "one day" in q:
            found_format = "ODI"
        elif "test" in q:
            found_format = "Test"

        # 5. Extract entities and normalized attributes via TextNormalizer
        from app.nlp.preprocessing.text_normalizer import TextNormalizer
        cricket_attrs = TextNormalizer.extract_cricket_entities(query)
        if not found_format and cricket_attrs.get("format"):
            found_format = cricket_attrs.get("format")

        # 6. Temporal
        temporal = TemporalParser.parse(query)
        start_date = temporal.start_date or (f"{cricket_attrs['season']}-01-01" if cricket_attrs.get("season") else None)
        end_date = temporal.end_date or (f"{cricket_attrs['season']}-12-31" if cricket_attrs.get("season") else None)

        # 7. Chart preference
        chart_pref = "line" if intent == "recent_form" else ("grouped_bar" if intent == "comparison" else "bar")

        # 8. Ambiguity check
        needs_clarification = False
        clarification_q = None
        clarification_opts = None

        if "sharma" in q and not any(p in q for p in ["rohit", "ishant", "mohit"]):
            needs_clarification = True
            clarification_q = "Which Sharma did you mean?"
            clarification_opts = ["Rohit Sharma", "Ishant Sharma"]

        schema = IntentSchema(
            intent=intent,
            players=found_players,
            opponent=found_opponent,
            format=found_format,
            competition=cricket_attrs.get("competition"),
            season=cricket_attrs.get("season"),
            statistical_category=cricket_attrs.get("category", "batting"),
            metrics=cricket_attrs.get("metrics") or ["runs", "batting_average", "strike_rate"],
            start_date=start_date,
            end_date=end_date,
            last_n_innings=temporal.last_n_innings,
            last_n_matches=temporal.last_n_matches,
            chart_preference=chart_pref,
            needs_clarification=needs_clarification,
            clarification_question=clarification_q,
            clarification_options=clarification_opts,
            confidence=0.9 if found_players else 0.5,
        )

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return schema, latency_ms

    def interpret(self, query: str) -> IntentSchema:
        schema, _ = self.interpret_query(query)
        return schema

