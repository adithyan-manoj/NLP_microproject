import pytest
from app.database.db import get_db, execute_query, check_db_exists
from app.core.config import settings
from app.ingestion.ingestion_service import ingest_file

@pytest.fixture(autouse=True)
def setup_fixture():
    fixture_path = settings.FIXTURES_DIR / "test_odi_1.json"
    ingest_file(fixture_path)

def test_db_exists():
    assert check_db_exists() is True

def test_matches_table():
    df = execute_query("SELECT COUNT(*) as cnt FROM matches;")
    assert not df.empty
    assert df["cnt"].iloc[0] >= 1

def test_deliveries_table():
    df = execute_query("SELECT COUNT(*) as cnt FROM deliveries;")
    assert not df.empty
    assert df["cnt"].iloc[0] >= 14

def test_players_table():
    df = execute_query("SELECT canonical_name FROM players WHERE canonical_name = 'V Kohli' OR canonical_name = 'Virat Kohli';")
    assert not df.empty
    assert "Kohli" in df["canonical_name"].iloc[0]

def test_parameterized_query():
    df = execute_query(
        "SELECT batter_name, SUM(batter_runs) as total_runs FROM deliveries WHERE batter_name = ? GROUP BY batter_name;",
        ["V Kohli"]
    )
    assert not df.empty
    assert df["total_runs"].iloc[0] >= 0
