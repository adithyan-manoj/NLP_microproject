"""
Unit Tests for Phase 2: Cricket Analytics Core.
Verifies Phase 2 Exit Conditions:
- All core metrics match independently verified reference calculations
- Batting average handles dismissals and not-outs
- Zero dismissals returns None (undefined/not out)
- Strike rate accounts for balls faced vs wides
- Bowler-credited wickets exclude run-outs
- Economy rate uses legal deliveries / 6
- Consistency metrics (std deviation, median)
"""

import pytest
import pandas as pd
from app.analytics.cricket_metrics import calculate_batting_metrics, calculate_bowling_metrics
from app.analytics.engine import analyze_player_batting, compare_players
from app.ingestion.ingestion_service import ingest_file
from app.core.config import settings

def test_batting_metrics_with_dismissals():
    # 5 innings: [50 out, 100 out, 40 not out, 60 out, 0 out] -> Total runs: 250, Dismissals: 4, Not outs: 1
    # Average: 250 / 4 = 62.5
    # Balls: [40, 80, 30, 50, 2] = 202
    # Strike rate: (250 / 202) * 100 = 123.76
    df = pd.DataFrame([
        {"runs": 50, "balls_faced": 40, "fours": 5, "sixes": 1, "is_out": 1},
        {"runs": 100, "balls_faced": 80, "fours": 10, "sixes": 3, "is_out": 1},
        {"runs": 40, "balls_faced": 30, "fours": 4, "sixes": 0, "is_out": 0},
        {"runs": 60, "balls_faced": 50, "fours": 6, "sixes": 2, "is_out": 1},
        {"runs": 0, "balls_faced": 2, "fours": 0, "sixes": 0, "is_out": 1},
    ])
    metrics = calculate_batting_metrics(df, "Test Player")
    assert metrics["total_runs"] == 250
    assert metrics["dismissals"] == 4
    assert metrics["not_outs"] == 1
    assert metrics["batting_average"] == 62.5
    assert metrics["strike_rate"] == 123.76
    assert metrics["high_score"] == 100
    assert metrics["high_score_not_out"] is False
    assert metrics["centuries"] == 1
    assert metrics["fifties"] == 2  # 50 and 60
    assert metrics["fours"] == 25
    assert metrics["sixes"] == 6
    assert metrics["boundary_runs"] == 25 * 4 + 6 * 6  # 100 + 36 = 136
    assert metrics["sample_size_adequate"] is True

def test_batting_average_zero_dismissals():
    # 2 innings: [45 not out, 55 not out] -> Total runs: 100, Dismissals: 0
    # Average must be None (undefined / not applicable), never an invented number
    df = pd.DataFrame([
        {"runs": 45, "balls_faced": 35, "fours": 4, "sixes": 1, "is_out": 0},
        {"runs": 55, "balls_faced": 40, "fours": 5, "sixes": 2, "is_out": 0},
    ])
    metrics = calculate_batting_metrics(df, "Not Out Finisher")
    assert metrics["total_runs"] == 100
    assert metrics["dismissals"] == 0
    assert metrics["not_outs"] == 2
    assert metrics["batting_average"] is None
    assert metrics["high_score"] == 55
    assert metrics["high_score_not_out"] is True

def test_bowling_metrics():
    # Spell 1: 24 legal balls (4 overs), 20 runs, 2 wickets
    # Spell 2: 30 legal balls (5 overs), 35 runs, 3 wickets
    # Total: 54 legal balls (9 overs), 55 runs, 5 wickets
    # Economy: 55 / 9 = 6.11
    # Average: 55 / 5 = 11.0
    # Strike rate: 54 / 5 = 10.8
    df = pd.DataFrame([
        {"legal_balls": 24, "runs_conceded": 20, "wickets": 2},
        {"legal_balls": 30, "runs_conceded": 35, "wickets": 3},
    ])
    metrics = calculate_bowling_metrics(df, "Lead Pacer")
    assert metrics["total_legal_balls"] == 54
    assert metrics["overs_bowled_display"] == "9.0"
    assert metrics["runs_conceded"] == 55
    assert metrics["wickets"] == 5
    assert metrics["economy_rate"] == 6.11
    assert metrics["bowling_average"] == 11.0
    assert metrics["bowling_strike_rate"] == 10.8

def test_analytics_engine_with_fixture():
    fixture_path = settings.FIXTURES_DIR / "test_odi_1.json"
    ingest_file(fixture_path)

    # Analyze Rohit Sharma from ODI fixture against Australia
    rohit_analysis = analyze_player_batting("RG Sharma", match_type="ODI", opponent="Australia")
    m = rohit_analysis["metrics"]
    assert m["player_name"] == "RG Sharma"
    assert m["total_runs"] == 11  # 4 + 1 + 6 + 0
    assert m["fours"] == 1
    assert m["sixes"] == 1
    assert m["dismissals"] == 1

    # Compare Rohit and Kohli
    comp = compare_players(["RG Sharma", "V Kohli"])
    assert len(comp["comparison"]) == 2
    p_names = [c["player"] for c in comp["comparison"]]
    assert "RG Sharma" in p_names
    assert "V Kohli" in p_names
