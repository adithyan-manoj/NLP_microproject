"""
Dataset Metadata & Coverage Service for CricInsight.
Provides real-time inspection of imported Cricsheet records, formats, teams,
date windows, canonical players, and dataset freshness.
"""

from typing import Dict, Any, List
import pandas as pd
from app.database.db import execute_query, get_db_status

def get_dataset_coverage() -> Dict[str, Any]:
    """Returns detailed statistics and coverage breakdown of the imported dataset."""
    db_status = get_db_status()

    # Formats & match counts
    df_formats = execute_query("""
        SELECT match_type, COUNT(*) as match_count,
               MIN(start_date) as earliest_date,
               MAX(start_date) as latest_date
        FROM matches
        GROUP BY match_type
        ORDER BY match_count DESC;
    """)
    formats_list = df_formats.to_dict(orient="records") if not df_formats.empty else []

    # Competitions
    df_comp = execute_query("""
        SELECT competition, COUNT(*) as count
        FROM matches
        WHERE competition IS NOT NULL AND competition != ''
        GROUP BY competition
        ORDER BY count DESC
        LIMIT 25;
    """)
    competitions = df_comp["competition"].tolist() if not df_comp.empty else []

    # Teams (Dialect-independent extraction from array/list columns)
    df_teams_raw = execute_query("SELECT teams FROM matches WHERE teams IS NOT NULL;")
    teams_set = set()
    if not df_teams_raw.empty:
        for t_list in df_teams_raw["teams"]:
            if hasattr(t_list, "__iter__") and not isinstance(t_list, (str, bytes)):
                for t in t_list:
                    teams_set.add(str(t).strip())
            elif isinstance(t_list, str):
                teams_set.add(t_list.strip("[]'\" "))
    teams_list = sorted(list(teams_set))

    # Venues
    df_venues = execute_query("""
        SELECT venue, COUNT(*) as count
        FROM matches
        WHERE venue IS NOT NULL AND venue != ''
        GROUP BY venue
        ORDER BY count DESC
        LIMIT 25;
    """)
    venues = df_venues["venue"].tolist() if not df_venues.empty else []

    # Date range
    df_dates = execute_query("SELECT MIN(start_date) as min_date, MAX(end_date) as max_date FROM matches;")
    min_date = str(df_dates.iloc[0]["min_date"]) if not df_dates.empty and df_dates.iloc[0]["min_date"] else "N/A"
    max_date = str(df_dates.iloc[0]["max_date"]) if not df_dates.empty and df_dates.iloc[0]["max_date"] else "N/A"

    # Last Ingestion Run
    df_last_run = execute_query("""
        SELECT started_at, finished_at, status, files_processed, inserted_count, updated_count
        FROM ingestion_runs
        ORDER BY id DESC
        LIMIT 1;
    """)
    last_run = df_last_run.to_dict(orient="records")[0] if not df_last_run.empty else None

    return {
        "engine": db_status["engine"],
        "total_matches": db_status["matches_count"],
        "total_deliveries": db_status["deliveries_count"],
        "total_players": db_status["players_count"],
        "formats": formats_list,
        "date_range": {
            "start": min_date,
            "end": max_date,
        },
        "teams_count": len(teams_list),
        "teams": teams_list,
        "top_competitions": competitions,
        "top_venues": venues,
        "last_ingestion": last_run,
        "coverage_limitations": [
            "Dataset coverage is strictly bounded to imported Cricsheet match files.",
            "Historical matches before Cricsheet coverage may not be present.",
            "T20 international records are classified as 'IT20' to distinguish from domestic leagues."
        ]
    }

def get_dataset_status() -> Dict[str, Any]:
    """Returns a lightweight health and freshness status of the dataset."""
    db_status = get_db_status()
    return {
        "status": "ready" if db_status["matches_count"] > 0 else "empty",
        "engine": db_status["engine"],
        "matches": db_status["matches_count"],
        "deliveries": db_status["deliveries_count"],
        "players": db_status["players_count"],
    }
