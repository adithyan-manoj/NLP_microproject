"""
Career Records Service for CricInsight.
Provides deterministic retrieval of all-time international career milestones,
world records, and historical statistics (1877–Present) to support Dual-Lens
answer generation and ground truth context.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.database.db import execute_query, execute_statement, get_duckdb_mirror
from app.database.connection import get_pool
from app.nlp.entity_resolution import EntityResolver

logger = logging.getLogger("cricinsight.career_records")

CORPUS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge" / "player_career_records.json"

class CareerRecordsService:
    """
    Manages deterministic all-time career milestones and world records.
    Bridges the gap between modern ball-by-ball samples and complete cricket history.
    """

    @classmethod
    def init_and_seed(cls) -> int:
        """
        Ensures player_career_records table exists and is populated from the seed JSON.
        """
        if not CORPUS_PATH.exists():
            logger.warning(f"Career records seed file not found: {CORPUS_PATH}")
            return 0

        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)

        # 1. Ensure table in PostgreSQL if available
        pool = get_pool()
        if pool is not None:
            try:
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS player_career_records (
                                canonical_name VARCHAR,
                                player_name VARCHAR,
                                country VARCHAR,
                                format VARCHAR,
                                span VARCHAR,
                                matches INTEGER,
                                innings INTEGER,
                                runs INTEGER,
                                high_score INTEGER,
                                high_score_not_out BOOLEAN DEFAULT FALSE,
                                batting_average DOUBLE PRECISION,
                                strike_rate DOUBLE PRECISION,
                                centuries INTEGER DEFAULT 0,
                                fifties INTEGER DEFAULT 0,
                                wickets INTEGER DEFAULT 0,
                                best_bowling VARCHAR,
                                all_time_milestone TEXT,
                                PRIMARY KEY (canonical_name, format)
                            );
                        """)
                        for r in records:
                            cur.execute("""
                                INSERT INTO player_career_records (
                                    canonical_name, player_name, country, format, span,
                                    matches, innings, runs, high_score, high_score_not_out,
                                    batting_average, strike_rate, centuries, fifties,
                                    wickets, best_bowling, all_time_milestone
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (canonical_name, format) DO UPDATE SET
                                    runs = EXCLUDED.runs,
                                    high_score = EXCLUDED.high_score,
                                    all_time_milestone = EXCLUDED.all_time_milestone;
                            """, (
                                r["canonical_name"], r["player_name"], r.get("country", ""), r["format"], r.get("span", ""),
                                r.get("matches", 0), r.get("innings", 0), r.get("runs", 0), r.get("high_score", 0),
                                r.get("high_score_not_out", False), r.get("batting_average"), r.get("strike_rate"),
                                r.get("centuries", 0), r.get("fifties", 0), r.get("wickets", 0),
                                r.get("best_bowling", ""), r.get("all_time_milestone", "")
                            ))
                        conn.commit()
                        logger.info(f"Seeded {len(records)} career records in PostgreSQL.")
            except Exception as e:
                logger.warning(f"PostgreSQL career records seeding error: {e}")

        # 2. DuckDB analytical mirror
        conn = get_duckdb_mirror()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_career_records (
                canonical_name VARCHAR,
                player_name VARCHAR,
                country VARCHAR,
                format VARCHAR,
                span VARCHAR,
                matches INTEGER,
                innings INTEGER,
                runs INTEGER,
                high_score INTEGER,
                high_score_not_out BOOLEAN DEFAULT FALSE,
                batting_average DOUBLE,
                strike_rate DOUBLE,
                centuries INTEGER DEFAULT 0,
                fifties INTEGER DEFAULT 0,
                wickets INTEGER DEFAULT 0,
                best_bowling VARCHAR,
                all_time_milestone TEXT,
                PRIMARY KEY (canonical_name, format)
            );
        """)

        # Idempotent insert into DuckDB
        for r in records:
            conn.execute("""
                INSERT OR REPLACE INTO player_career_records (
                    canonical_name, player_name, country, format, span,
                    matches, innings, runs, high_score, high_score_not_out,
                    batting_average, strike_rate, centuries, fifties,
                    wickets, best_bowling, all_time_milestone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                r["canonical_name"], r["player_name"], r.get("country", ""), r["format"], r.get("span", ""),
                r.get("matches", 0), r.get("innings", 0), r.get("runs", 0), r.get("high_score", 0),
                r.get("high_score_not_out", False), r.get("batting_average"), r.get("strike_rate"),
                r.get("centuries", 0), r.get("fifties", 0), r.get("wickets", 0),
                r.get("best_bowling", ""), r.get("all_time_milestone", "")
            ])

        logger.info(f"Seeded {len(records)} career records in DuckDB mirror.")
        return len(records)

    @classmethod
    def get_career_milestones_for_player(
        cls,
        player_name: str,
        match_format: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all-time career milestone context for a given player name or canonical ID.
        """
        # Resolve canonical name
        resolved = EntityResolver.resolve_player(player_name)
        canonical_name = resolved.canonical_name or player_name

        # Query career records
        sql = """
            SELECT canonical_name, player_name, country, format, span, matches, runs,
                   high_score, high_score_not_out, batting_average, strike_rate,
                   centuries, fifties, wickets, best_bowling, all_time_milestone
            FROM player_career_records
            WHERE canonical_name = ? OR LOWER(player_name) LIKE LOWER(?)
        """
        params = [canonical_name, f"%{player_name}%"]

        if match_format:
            sql += " AND format = ?"
            params.append(match_format)

        df = execute_query(sql, params)
        if df.empty and (" " in player_name or len(player_name) > 3):
            # Try first or last name match
            parts = player_name.split()
            last_name = parts[-1]
            sql_fallback = """
                SELECT canonical_name, player_name, country, format, span, matches, runs,
                       high_score, high_score_not_out, batting_average, strike_rate,
                       centuries, fifties, wickets, best_bowling, all_time_milestone
                FROM player_career_records
                WHERE LOWER(player_name) LIKE LOWER(?)
            """
            df = execute_query(sql_fallback, [f"%{last_name}%"])

        if df.empty:
            return []

        return df.to_dict(orient="records")

    @classmethod
    def format_milestone_context(cls, milestones: List[Dict[str, Any]]) -> str:
        """Formats milestone records into a clean string for prompt injection."""
        if not milestones:
            return ""

        lines = []
        for m in milestones:
            hs_no = "*" if m.get("high_score_not_out") else ""
            line = (
                f"- {m['player_name']} ({m['format']}, {m['span']}): Career High Score {m['high_score']}{hs_no}, "
                f"Total Runs {m['runs']}, Avg {m['batting_average']}, 100s: {m['centuries']}. "
                f"Milestone: {m['all_time_milestone']}"
            )
            lines.append(line)
        return "\n".join(lines)
