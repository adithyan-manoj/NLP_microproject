"""
Idempotent Ingestion Service for CricInsight.
Parses, hashes, validates, and stores Cricsheet match files into PostgreSQL / DuckDB mirror.
Tracks ingestion runs, skip counts, updates, and rejections.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.database.db import execute_query, execute_statement, get_duckdb_mirror
from app.database.connection import get_pool
from app.ingestion.cricsheet_parser import parse_cricsheet_match, CricsheetParseError

logger = logging.getLogger("cricinsight.ingestion")

def ingest_file(file_path: Path, force: bool = False) -> str:
    """
    Ingests a single Cricsheet match JSON file idempotently.
    Returns: 'inserted', 'updated', 'skipped', or raises CricsheetParseError.
    """
    parsed = parse_cricsheet_match(file_path)
    match = parsed["match"]
    match_id = match["id"]
    file_hash = parsed["file_hash"]

    # Check existing record
    existing = execute_query(
        "SELECT id, source_file_hash FROM matches WHERE id = ?;",
        [match_id]
    )

    if not existing.empty:
        existing_hash = existing.iloc[0]["source_file_hash"]
        if existing_hash == file_hash and not force:
            return "skipped"
        else:
            execute_statement("DELETE FROM deliveries WHERE match_id = ?;", [match_id])
            execute_statement("DELETE FROM innings WHERE match_id = ?;", [match_id])
            execute_statement("DELETE FROM matches WHERE id = ?;", [match_id])
            status = "updated"
    else:
        status = "inserted"

    pool = get_pool()
    if pool is not None:
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO matches (
                            id, source, source_match_id, dates, start_date, end_date,
                            match_type, match_type_number, competition, season, gender,
                            venue, city, teams, toss_winner, toss_decision,
                            outcome_winner, outcome_by_runs, outcome_by_wickets,
                            outcome_result, outcome_method, player_of_match,
                            balls_per_over, overs_limit, source_file_hash
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s
                        ) ON CONFLICT (source, source_match_id) DO UPDATE SET
                            source_file_hash = EXCLUDED.source_file_hash,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (
                        match["id"], match["source"], match["source_match_id"],
                        match["dates"], match["start_date"], match["end_date"],
                        match["match_type"], match["match_type_number"],
                        match["competition"], match["season"], match["gender"],
                        match["venue"], match["city"], match["teams"],
                        match["toss_winner"], match["toss_decision"],
                        match["outcome_winner"], match["outcome_by_runs"], match["outcome_by_wickets"],
                        match["outcome_result"], match["outcome_method"], match["player_of_match"],
                        match["balls_per_over"], match["overs_limit"], match["source_file_hash"]
                    ))

                    for p in parsed["players"]:
                        cur.execute("""
                            INSERT INTO players (id, canonical_name, cricsheet_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id) DO NOTHING;
                        """, (p["id"], p["canonical_name"], p.get("cricsheet_id")))

                    for a in parsed["player_aliases"]:
                        cur.execute("""
                            INSERT INTO player_aliases (player_id, alias, normalized_alias, source, is_primary)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (player_id, normalized_alias) DO NOTHING;
                        """, (a["player_id"], a["alias"], a["normalized_alias"], a["source"], a["is_primary"]))

                    inn_id_map = {}
                    for inn in parsed["innings"]:
                        cur.execute("""
                            INSERT INTO innings (
                                match_id, innings_number, batting_team, bowling_team,
                                declared, overs_limit, total_runs, total_wickets, total_legal_balls
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id, innings_number;
                        """, (
                            inn["match_id"], inn["innings_number"], inn["batting_team"],
                            inn["bowling_team"], inn["declared"], inn["overs_limit"],
                            inn["total_runs"], inn["total_wickets"], inn["total_legal_balls"]
                        ))
                        row = cur.fetchone()
                        if row:
                            inn_id_map[row[1]] = row[0]

                    for d in parsed["deliveries"]:
                        inn_pk = inn_id_map.get(d["innings_number"], d["innings_number"])
                        cur.execute("""
                            INSERT INTO deliveries (
                                innings_id, match_id, over_num, ball_num, delivery_index,
                                batter_id, batter_name, bowler_id, bowler_name,
                                non_striker_id, non_striker_name, batter_runs, extra_runs, total_runs,
                                is_wide, is_noball, is_bye, is_legbye, is_penalty,
                                is_legal_ball, is_ball_faced, bowler_conceded_runs,
                                is_wicket, dismissal_kind, player_dismissed, bowler_credited_wicket
                            ) VALUES (
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s, %s
                            );
                        """, (
                            inn_pk, d["match_id"], d["over_num"], d["ball_num"], d["delivery_index"],
                            d["batter_id"], d["batter_name"], d["bowler_id"], d["bowler_name"],
                            d["non_striker_id"], d["non_striker_name"], d["batter_runs"], d["extra_runs"], d["total_runs"],
                            d["is_wide"], d["is_noball"], d["is_bye"], d["is_legbye"], d["is_penalty"],
                            d["is_legal_ball"], d["is_ball_faced"], d["bowler_conceded_runs"],
                            d["is_wicket"], d["dismissal_kind"], d["player_dismissed"], d["bowler_credited_wicket"]
                        ))
                    conn.commit()
            _ingest_into_duckdb(parsed)
            return status
        except Exception as e:
            logger.warning(f"PostgreSQL insertion error, writing to DuckDB mirror: {e}")

    _ingest_into_duckdb(parsed)
    return status

def _ingest_into_duckdb(parsed: Dict[str, Any]):
    """Stores parsed match in DuckDB mirror using sequences."""
    conn = get_duckdb_mirror()
    m = parsed["match"]
    match_id = m["id"]

    conn.execute("DELETE FROM deliveries WHERE match_id = ?;", [match_id])
    conn.execute("DELETE FROM innings WHERE match_id = ?;", [match_id])
    conn.execute("DELETE FROM matches WHERE id = ?;", [match_id])

    conn.execute("""
        INSERT INTO matches (
            id, source, source_match_id, dates, start_date, end_date,
            match_type, competition, season, gender, venue, city, teams,
            toss_winner, toss_decision, outcome_winner, outcome_by_runs, outcome_by_wickets,
            outcome_result, outcome_method, player_of_match, balls_per_over, overs_limit, source_file_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, [
        m["id"], m["source"], m["source_match_id"], m["dates"], m["start_date"], m["end_date"],
        m["match_type"], m["competition"], m["season"], m["gender"], m["venue"], m["city"], m["teams"],
        m["toss_winner"], m["toss_decision"], m["outcome_winner"], m["outcome_by_runs"], m["outcome_by_wickets"],
        m["outcome_result"], m["outcome_method"], m["player_of_match"], m["balls_per_over"], m["overs_limit"], m["source_file_hash"]
    ])

    for p in parsed["players"]:
        conn.execute("DELETE FROM player_aliases WHERE player_id = ?;", [p["id"]])
        conn.execute("""
            INSERT OR REPLACE INTO players (id, canonical_name, cricsheet_id)
            VALUES (?, ?, ?);
        """, [p["id"], p["canonical_name"], p.get("cricsheet_id")])

    for a in parsed["player_aliases"]:
        conn.execute("""
            INSERT INTO player_aliases (player_id, alias, normalized_alias, source, is_primary)
            VALUES (?, ?, ?, ?, ?);
        """, [a["player_id"], a["alias"], a["normalized_alias"], a["source"], a["is_primary"]])

    for inn in parsed["innings"]:
        conn.execute("""
            INSERT INTO innings (
                match_id, innings_number, batting_team, bowling_team,
                declared, overs_limit, total_runs, total_wickets, total_legal_balls
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            inn["match_id"], inn["innings_number"], inn["batting_team"],
            inn["bowling_team"], inn["declared"], inn["overs_limit"],
            inn["total_runs"], inn["total_wickets"], inn["total_legal_balls"]
        ])

    for d in parsed["deliveries"]:
        conn.execute("""
            INSERT INTO deliveries (
                innings_id, match_id, over_num, ball_num, delivery_index,
                batter_id, batter_name, bowler_id, bowler_name,
                non_striker_id, non_striker_name, batter_runs, extra_runs, total_runs,
                is_wide, is_noball, is_bye, is_legbye, is_penalty,
                is_legal_ball, is_ball_faced, bowler_conceded_runs,
                is_wicket, dismissal_kind, player_dismissed, bowler_credited_wicket
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            d["innings_number"], d["match_id"], d["over_num"], d["ball_num"], d["delivery_index"],
            d["batter_id"], d["batter_name"], d["bowler_id"], d["bowler_name"],
            d["non_striker_id"], d["non_striker_name"], d["batter_runs"], d["extra_runs"], d["total_runs"],
            d["is_wide"], d["is_noball"], d["is_bye"], d["is_legbye"], d["is_penalty"],
            d["is_legal_ball"], d["is_ball_faced"], d["bowler_conceded_runs"],
            d["is_wicket"], d["dismissal_kind"], d["player_dismissed"], d["bowler_credited_wicket"]
        ])

def ingest_directory(directory_path: Path, force: bool = False) -> Dict[str, Any]:
    """Ingests all Cricsheet JSON files from a target directory."""
    files = list(directory_path.glob("*.json"))
    started_at = datetime.utcnow()
    inserted = 0
    updated = 0
    skipped = 0
    rejected = 0
    errors = []

    for f in files:
        try:
            status = ingest_file(f, force=force)
            if status == "inserted":
                inserted += 1
            elif status == "updated":
                updated += 1
            elif status == "skipped":
                skipped += 1
        except Exception as e:
            rejected += 1
            errors.append({"file": f.name, "error": str(e)})

    finished_at = datetime.utcnow()
    summary = {
        "source": "cricsheet",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "files_processed": len(files),
        "inserted_count": inserted,
        "updated_count": updated,
        "skipped_count": skipped,
        "rejected_count": rejected,
        "error_details": errors[:20]
    }

    try:
        execute_statement("""
            INSERT INTO ingestion_runs (
                source, started_at, finished_at, status, files_processed,
                inserted_count, updated_count, skipped_count, rejected_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            summary["source"], started_at, finished_at,
            "completed" if rejected == 0 else "partial_errors",
            summary["files_processed"], summary["inserted_count"],
            summary["updated_count"], summary["skipped_count"], summary["rejected_count"]
        ])
    except Exception as e:
        logger.debug(f"Could not record ingestion run: {e}")

    return summary

class IngestionService:
    @staticmethod
    def import_directory(directory_path: Path, force: bool = False) -> Dict[str, Any]:
        return ingest_directory(directory_path, force=force)

    @staticmethod
    def import_file(file_path: Path, force: bool = False) -> str:
        return ingest_file(file_path, force=force)

