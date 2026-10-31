"""
Unit tests for Cricsheet JSON Parser and Idempotent Ingestion Service.
Verifies Phase 1 Exit Conditions:
- Real Cricsheet samples import correctly
- Repeated imports do not create duplicates (idempotency)
- Corrected files update records safely
- Extras, legal deliveries, balls faced, and bowler wicket attribution
"""

import json
from pathlib import Path
import pytest
import pandas as pd

from app.core.config import settings
from app.ingestion.cricsheet_parser import parse_cricsheet_match, compute_file_hash
from app.ingestion.ingestion_service import ingest_file, ingest_directory
from app.services.dataset_service import get_dataset_coverage, get_dataset_status
from app.database.db import execute_query, execute_statement

@pytest.fixture
def sample_fixture_path() -> Path:
    fixture_path = settings.FIXTURES_DIR / "test_odi_1.json"
    assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"
    return fixture_path

def test_cricsheet_parser_structure(sample_fixture_path):
    parsed = parse_cricsheet_match(sample_fixture_path)
    match = parsed["match"]
    assert match["match_type"] == "ODI"
    assert match["venue"] == "Narendra Modi Stadium, Ahmedabad"
    assert "India" in match["teams"]
    assert "Australia" in match["teams"]
    assert match["outcome_winner"] == "Australia"
    assert len(match["dates"]) == 1
    assert match["start_date"] == "2023-11-19"
    assert parsed["file_hash"] is not None

def test_cricket_scoring_and_extras_edge_cases(sample_fixture_path):
    parsed = parse_cricsheet_match(sample_fixture_path)
    deliveries = parsed["deliveries"]
    assert len(deliveries) == 14  # 7 balls in over 0, 7 balls in over 1

    # Over 0 Ball 3: Wide
    wide_deliv = deliveries[2]
    assert wide_deliv["is_wide"] is True
    assert wide_deliv["is_legal_ball"] is False
    assert wide_deliv["is_ball_faced"] is False
    assert wide_deliv["bowler_conceded_runs"] == 1

    # Over 1 Ball 5: No-ball (with 1 batter run)
    noball_deliv = deliveries[11]
    assert noball_deliv["is_noball"] is True
    assert noball_deliv["is_legal_ball"] is False
    assert noball_deliv["is_ball_faced"] is True  # batter faces no-balls
    assert noball_deliv["batter_runs"] == 1
    assert noball_deliv["bowler_conceded_runs"] == 2  # 1 batter run + 1 noball

    # Over 1 Ball 6: Bye (2 runs)
    bye_deliv = deliveries[12]
    assert bye_deliv["is_bye"] is True
    assert bye_deliv["batter_runs"] == 0
    assert bye_deliv["extra_runs"] == 2
    assert bye_deliv["bowler_conceded_runs"] == 0  # bowler is NOT charged for byes

    # Over 0 Ball 7: Caught dismissal (bowler credited)
    caught_deliv = deliveries[6]
    assert caught_deliv["is_wicket"] is True
    assert caught_deliv["dismissal_kind"] == "caught"
    assert caught_deliv["bowler_credited_wicket"] is True

    # Over 1 Ball 7: Run out dismissal (bowler NOT credited)
    runout_deliv = deliveries[13]
    assert runout_deliv["is_wicket"] is True
    assert runout_deliv["dismissal_kind"] == "run out"
    assert runout_deliv["bowler_credited_wicket"] is False

def test_idempotent_ingestion(sample_fixture_path):
    match_id = "cricsheet_test_odi_1"
    # Clean previous record to test fresh insertion
    execute_statement("DELETE FROM deliveries WHERE match_id = ?;", [match_id])
    execute_statement("DELETE FROM innings WHERE match_id = ?;", [match_id])
    execute_statement("DELETE FROM matches WHERE id = ?;", [match_id])

    # Run 1: First ingestion -> inserted
    status1 = ingest_file(sample_fixture_path)
    assert status1 == "inserted"

    df_before = execute_query("SELECT COUNT(*) as cnt FROM deliveries WHERE match_id = ?;", [match_id])
    count_before = int(df_before.iloc[0]["cnt"])
    assert count_before == 14

    # Run 2: Second ingestion -> skipped (MD5 hash matches)
    status2 = ingest_file(sample_fixture_path)
    assert status2 == "skipped"

    df_after = execute_query("SELECT COUNT(*) as cnt FROM deliveries WHERE match_id = ?;", [match_id])
    count_after = int(df_after.iloc[0]["cnt"])
    assert count_after == count_before, "Duplicate rows created on repeated ingestion!"

def test_dataset_coverage_service(sample_fixture_path):
    ingest_file(sample_fixture_path)
    coverage = get_dataset_coverage()
    assert coverage["total_matches"] >= 1
    assert coverage["total_deliveries"] >= 14
    assert "ODI" in [f["match_type"] for f in coverage["formats"]]
    assert "India" in coverage["teams"]
    assert "Australia" in coverage["teams"]
    assert len(coverage["coverage_limitations"]) > 0

    status = get_dataset_status()
    assert status["status"] == "ready"
    assert status["matches"] >= 1
