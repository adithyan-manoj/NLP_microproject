import re
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from app.database.db import get_db

@dataclass
class PlayerResolution:
    canonical_name: str
    player_id: str
    is_ambiguous: bool = False
    candidates: List[str] = None

class EntityResolver:
    """
    Database-backed entity resolution service for cricket players, teams, venues, and formats.
    Ensures player names are grounded in actual database records, not LLM hallucinations.
    """

    FORMAT_MAPPINGS: Dict[str, str] = {
        # International formats
        "t20i": "IT20",
        "t20 international": "IT20",
        "it20": "IT20",
        "odi": "ODI",
        "one day international": "ODI",
        "one-day": "ODI",
        "test": "Test",
        "test match": "Test",
        # Domestic formats (strictly distinct)
        "t20": "T20",
        "twenty20": "T20",
        "odm": "ODM",
        "one day match": "ODM",
        "mdm": "MDM",
    }

    @staticmethod
    def normalize_name(name: str) -> str:
        """Strip punctuation, excessive whitespace, and lower-case for alias matching."""
        name = re.sub(r"[^\w\s]", "", name)
        return " ".join(name.strip().lower().split())

    @classmethod
    def normalize_format(cls, raw_format: Optional[str]) -> Optional[str]:
        if not raw_format:
            return None
        cleaned = raw_format.strip().lower()
        return cls.FORMAT_MAPPINGS.get(cleaned, raw_format.upper())

    @classmethod
    def resolve_player(cls, name_query: str) -> PlayerResolution:
        """
        Resolves a player name or alias against the database.
        Detects ambiguities (e.g. 'Sharma' matching both 'Rohit Sharma' and 'Ishant Sharma').
        """
        db = get_db()
        norm = cls.normalize_name(name_query)
        if not norm:
            return PlayerResolution(canonical_name=name_query, player_id="", is_ambiguous=False)

        # 1. Exact canonical name match
        rows = db.query(
            "SELECT id, canonical_name FROM players WHERE LOWER(canonical_name) = %s",
            (norm,)
        )
        if rows:
            return PlayerResolution(
                canonical_name=rows[0]["canonical_name"],
                player_id=rows[0]["id"]
            )

        # 2. Exact alias match
        rows = db.query(
            """
            SELECT p.id, p.canonical_name 
            FROM player_aliases a
            JOIN players p ON a.player_id = p.id
            WHERE a.normalized_alias = %s
            GROUP BY p.id, p.canonical_name
            """,
            (norm,)
        )
        if len(rows) == 1:
            return PlayerResolution(
                canonical_name=rows[0]["canonical_name"],
                player_id=rows[0]["id"]
            )
        elif len(rows) > 1:
            candidate_names = [r["canonical_name"] for r in rows]
            return PlayerResolution(
                canonical_name=candidate_names[0],
                player_id=rows[0]["id"],
                is_ambiguous=True,
                candidates=candidate_names
            )

        # 3. Substring / ILIKE matching
        pattern = f"%{norm}%"
        rows = db.query(
            """
            SELECT DISTINCT p.id, p.canonical_name 
            FROM players p
            LEFT JOIN player_aliases a ON a.player_id = p.id
            WHERE LOWER(p.canonical_name) LIKE %s OR LOWER(a.alias) LIKE %s
            LIMIT 5
            """,
            (pattern, pattern)
        )
        if len(rows) == 1:
            return PlayerResolution(
                canonical_name=rows[0]["canonical_name"],
                player_id=rows[0]["id"]
            )
        elif len(rows) > 1:
            candidate_names = [r["canonical_name"] for r in rows]
            return PlayerResolution(
                canonical_name=candidate_names[0],
                player_id=rows[0]["id"],
                is_ambiguous=True,
                candidates=candidate_names
            )

        # 4. Fallback if not yet in database
        return PlayerResolution(
            canonical_name=name_query.strip(),
            player_id="",
            is_ambiguous=False
        )
