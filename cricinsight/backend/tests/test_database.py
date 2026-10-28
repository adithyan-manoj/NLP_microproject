import pytest
from app.database.db import get_db, execute_query, check_db_exists

def test_db_exists():
    assert check_db_exists() is True

def test_matches_table():
    df = execute_query("SELECT COUNT(*) as cnt FROM matches;")
    assert not df.empty
    assert df["cnt"].iloc[0] > 1000

def test_deliveries_table():
    df = execute_query("SELECT COUNT(*) as cnt FROM deliveries;")
    assert not df.empty
    assert df["cnt"].iloc[0] > 500000

def test_players_table():
    df = execute_query("SELECT canonical_name, aliases FROM players WHERE canonical_name = 'Virat Kohli';")
    assert not df.empty
    assert "Virat Kohli" in df["canonical_name"].iloc[0]

def test_parameterized_query():
    df = execute_query(
        "SELECT batter, SUM(batter_runs) as total_runs FROM deliveries WHERE batter = ? GROUP BY batter;",
        ["V Kohli"]
    )
    assert not df.empty
    assert df["total_runs"].iloc[0] > 1000
