import duckdb
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from contextlib import contextmanager
from app.core.config import settings

def get_db_path() -> str:
    return str(settings.DUCKDB_PATH)

def check_db_exists() -> bool:
    return settings.DUCKDB_PATH.exists() and settings.DUCKDB_PATH.stat().st_size > 0

@contextmanager
def get_db(read_only: bool = True):
    """
    Context manager for DuckDB connection.
    Defaults to read_only=True for safe concurrent analytical queries.
    """
    db_path = get_db_path()
    conn = duckdb.connect(database=db_path, read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()

def execute_query(sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
    """
    Execute a parameterized SQL query safely against DuckDB and return a Pandas DataFrame.
    Always uses parameterized queries to prevent SQL injection.
    """
    with get_db(read_only=True) as conn:
        if params:
            return conn.execute(sql, params).df()
        else:
            return conn.execute(sql).df()

def init_schema():
    """
    Initialize DuckDB tables if they do not exist.
    Tables: matches, deliveries, players
    """
    settings.DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db(read_only=False) as conn:
        # Table: matches
        conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id VARCHAR PRIMARY KEY,
                date DATE,
                match_type VARCHAR,
                competition VARCHAR,
                venue VARCHAR,
                team_1 VARCHAR,
                team_2 VARCHAR
            );
        """)

        # Table: deliveries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
                match_id VARCHAR,
                innings_number INTEGER,
                batting_team VARCHAR,
                bowling_team VARCHAR,
                over_num INTEGER,
                ball_num INTEGER,
                batter VARCHAR,
                bowler VARCHAR,
                non_striker VARCHAR,
                batter_runs INTEGER,
                extra_runs INTEGER,
                is_wicket BOOLEAN,
                dismissal_kind VARCHAR,
                player_dismissed VARCHAR,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            );
        """)

        # Table: players
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id VARCHAR PRIMARY KEY,
                canonical_name VARCHAR,
                aliases VARCHAR
            );
        """)

        # Create indexes for fast analytical slicing
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_type ON matches(match_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_match ON deliveries(match_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_players_canonical ON players(canonical_name);")
