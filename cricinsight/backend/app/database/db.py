"""
Authoritative Database Access Layer for CricInsight.
Primary: PostgreSQL 16 + pgvector with parameterized SQL.
Fallback: Local columnar mirror (DuckDB) for zero-downtime test and development.
"""

import logging
import threading
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import pandas as pd
import duckdb

from app.core.config import settings
from app.database.connection import get_pool, check_postgres_connection, init_postgres_schema

logger = logging.getLogger("cricinsight.database")

_duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None
_duckdb_lock = threading.Lock()

def get_duckdb_mirror() -> duckdb.DuckDBPyConnection:
    global _duckdb_conn
    if _duckdb_conn is None:
        db_path = str(settings.DUCKDB_PATH)
        try:
            _duckdb_conn = duckdb.connect(database=db_path, read_only=False)
            _init_duckdb_schema(_duckdb_conn)
        except Exception as e:
            logger.warning(f"DuckDB locked for write, falling back to read-only connection: {e}")
            try:
                _duckdb_conn = duckdb.connect(database=db_path, read_only=True)
            except Exception as e2:
                logger.warning(f"DuckDB file locked on Windows, using in-memory instance: {e2}")
                _duckdb_conn = duckdb.connect(database=":memory:")
                _init_duckdb_schema(_duckdb_conn)
    return _duckdb_conn

def _init_duckdb_schema(conn: duckdb.DuckDBPyConnection):
    """Initializes tables and sequences in DuckDB mirror matching PostgreSQL schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id VARCHAR PRIMARY KEY,
            source VARCHAR DEFAULT 'cricsheet',
            source_match_id VARCHAR UNIQUE,
            dates VARCHAR[],
            start_date DATE,
            end_date DATE,
            match_type VARCHAR,
            competition VARCHAR,
            season VARCHAR,
            gender VARCHAR,
            venue VARCHAR,
            city VARCHAR,
            teams VARCHAR[],
            toss_winner VARCHAR,
            toss_decision VARCHAR,
            outcome_winner VARCHAR,
            outcome_by_runs INTEGER,
            outcome_by_wickets INTEGER,
            outcome_result VARCHAR,
            outcome_method VARCHAR,
            player_of_match VARCHAR[],
            balls_per_over INTEGER DEFAULT 6,
            overs_limit INTEGER,
            source_file_hash VARCHAR,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS players (
            id VARCHAR PRIMARY KEY,
            canonical_name VARCHAR,
            cricsheet_id VARCHAR,
            country VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE SEQUENCE IF NOT EXISTS seq_player_aliases START 1;
        CREATE TABLE IF NOT EXISTS player_aliases (
            id INTEGER DEFAULT nextval('seq_player_aliases'),
            player_id VARCHAR,
            alias VARCHAR,
            normalized_alias VARCHAR,
            source VARCHAR DEFAULT 'manual',
            is_primary BOOLEAN DEFAULT FALSE
        );

        CREATE SEQUENCE IF NOT EXISTS seq_innings START 1;
        CREATE TABLE IF NOT EXISTS innings (
            id INTEGER DEFAULT nextval('seq_innings'),
            match_id VARCHAR,
            innings_number INTEGER,
            batting_team VARCHAR,
            bowling_team VARCHAR,
            declared BOOLEAN DEFAULT FALSE,
            overs_limit INTEGER,
            total_runs INTEGER DEFAULT 0,
            total_wickets INTEGER DEFAULT 0,
            total_legal_balls INTEGER DEFAULT 0
        );

        CREATE SEQUENCE IF NOT EXISTS seq_deliveries START 1;
        CREATE TABLE IF NOT EXISTS deliveries (
            id BIGINT DEFAULT nextval('seq_deliveries'),
            innings_id INTEGER,
            match_id VARCHAR,
            over_num INTEGER,
            ball_num INTEGER,
            delivery_index INTEGER,
            batter_id VARCHAR,
            batter_name VARCHAR,
            bowler_id VARCHAR,
            bowler_name VARCHAR,
            non_striker_id VARCHAR,
            non_striker_name VARCHAR,
            batter_runs INTEGER DEFAULT 0,
            extra_runs INTEGER DEFAULT 0,
            total_runs INTEGER DEFAULT 0,
            is_wide BOOLEAN DEFAULT FALSE,
            is_noball BOOLEAN DEFAULT FALSE,
            is_bye BOOLEAN DEFAULT FALSE,
            is_legbye BOOLEAN DEFAULT FALSE,
            is_penalty BOOLEAN DEFAULT FALSE,
            is_legal_ball BOOLEAN DEFAULT TRUE,
            is_ball_faced BOOLEAN DEFAULT TRUE,
            bowler_conceded_runs INTEGER DEFAULT 0,
            is_wicket BOOLEAN DEFAULT FALSE,
            dismissal_kind VARCHAR,
            player_dismissed VARCHAR,
            bowler_credited_wicket BOOLEAN DEFAULT FALSE
        );

        CREATE SEQUENCE IF NOT EXISTS seq_ingestion_runs START 1;
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id INTEGER DEFAULT nextval('seq_ingestion_runs'),
            source VARCHAR DEFAULT 'cricsheet',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            status VARCHAR DEFAULT 'running',
            files_processed INTEGER DEFAULT 0,
            inserted_count INTEGER DEFAULT 0,
            updated_count INTEGER DEFAULT 0,
            skipped_count INTEGER DEFAULT 0,
            rejected_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS match_scorecards (
            id VARCHAR PRIMARY KEY,
            match_id VARCHAR,
            player_name VARCHAR,
            player_id VARCHAR,
            competition VARCHAR,
            season VARCHAR,
            match_type VARCHAR,
            match_date DATE,
            opponent VARCHAR,
            venue VARCHAR,
            innings_number INTEGER DEFAULT 1,
            runs INTEGER DEFAULT 0,
            balls_faced INTEGER DEFAULT 0,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            is_out BOOLEAN DEFAULT TRUE,
            dismissal_kind VARCHAR,
            overs_bowled DOUBLE DEFAULT 0.0,
            wickets INTEGER DEFAULT 0,
            runs_conceded INTEGER DEFAULT 0,
            source VARCHAR DEFAULT 'scorecard_archive',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE SEQUENCE IF NOT EXISTS seq_knowledge_chunks START 1;
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER DEFAULT nextval('seq_knowledge_chunks'),
            source_document VARCHAR,
            section VARCHAR,
            chunk_text TEXT,
            metadata VARCHAR
        );

        CREATE SEQUENCE IF NOT EXISTS seq_query_logs START 1;
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER DEFAULT nextval('seq_query_logs'),
            request_id VARCHAR UNIQUE,
            prompt TEXT,
            session_id VARCHAR,
            provider VARCHAR,
            model_name VARCHAR,
            status VARCHAR,
            latency_ms DOUBLE,
            fallback_used BOOLEAN DEFAULT FALSE,
            fallback_reason VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE SEQUENCE IF NOT EXISTS seq_nlp_predictions START 1;
        CREATE TABLE IF NOT EXISTS nlp_predictions (
            id INTEGER DEFAULT nextval('seq_nlp_predictions'),
            request_id VARCHAR,
            raw_response TEXT,
            validated_schema VARCHAR,
            predicted_intent VARCHAR,
            confidence_score DOUBLE,
            schema_valid BOOLEAN,
            entity_resolution_score DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE SEQUENCE IF NOT EXISTS seq_benchmark_questions START 1;
        CREATE TABLE IF NOT EXISTS benchmark_questions (
            id INTEGER DEFAULT nextval('seq_benchmark_questions'),
            question_id VARCHAR UNIQUE,
            query_text TEXT,
            category VARCHAR,
            expected_intent VARCHAR,
            expected_players VARCHAR[],
            expected_opponent VARCHAR,
            expected_format VARCHAR,
            expected_metrics VARCHAR[],
            expected_start_date DATE,
            expected_recent_n INTEGER,
            expected_chart_preference VARCHAR,
            should_clarify BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE SEQUENCE IF NOT EXISTS seq_evaluation_runs START 1;
        CREATE TABLE IF NOT EXISTS evaluation_runs (
            id INTEGER DEFAULT nextval('seq_evaluation_runs'),
            run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            provider VARCHAR,
            model_name VARCHAR,
            total_questions INTEGER,
            intent_accuracy DOUBLE,
            entity_precision DOUBLE,
            entity_recall DOUBLE,
            entity_f1 DOUBLE,
            exact_match_rate DOUBLE,
            schema_valid_rate DOUBLE,
            avg_latency_ms DOUBLE,
            fallback_rate DOUBLE,
            summary_report VARCHAR
        );

        CREATE TABLE IF NOT EXISTS tournaments (
            id VARCHAR PRIMARY KEY,
            name VARCHAR,
            season VARCHAR DEFAULT '2026',
            format VARCHAR DEFAULT 'T20',
            overs_limit INTEGER DEFAULT 20,
            status VARCHAR DEFAULT 'ongoing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tournament_teams (
            id VARCHAR PRIMARY KEY,
            tournament_id VARCHAR,
            name VARCHAR,
            short_code VARCHAR,
            captain VARCHAR,
            color VARCHAR DEFAULT '#10B981'
        );

        CREATE TABLE IF NOT EXISTS tournament_players (
            id VARCHAR PRIMARY KEY,
            tournament_id VARCHAR,
            team_id VARCHAR,
            name VARCHAR,
            role VARCHAR DEFAULT 'all_rounder'
        );

        CREATE TABLE IF NOT EXISTS tournament_matches (
            id VARCHAR PRIMARY KEY,
            tournament_id VARCHAR,
            team1_id VARCHAR,
            team2_id VARCHAR,
            match_number INTEGER,
            venue VARCHAR,
            match_date DATE,
            status VARCHAR DEFAULT 'completed',
            toss_winner_id VARCHAR,
            toss_decision VARCHAR,
            winner_team_id VARCHAR,
            margin VARCHAR,
            innings1_runs INTEGER DEFAULT 0,
            innings1_wickets INTEGER DEFAULT 0,
            innings1_overs DOUBLE DEFAULT 0.0,
            innings2_runs INTEGER DEFAULT 0,
            innings2_wickets INTEGER DEFAULT 0,
            innings2_overs DOUBLE DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE SEQUENCE IF NOT EXISTS seq_tournament_scorecards START 1;
        CREATE TABLE IF NOT EXISTS tournament_scorecards (
            id INTEGER DEFAULT nextval('seq_tournament_scorecards'),
            match_id VARCHAR,
            tournament_id VARCHAR,
            team_id VARCHAR,
            player_name VARCHAR,
            runs INTEGER DEFAULT 0,
            balls INTEGER DEFAULT 0,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            overs_bowled DOUBLE DEFAULT 0.0,
            maidens INTEGER DEFAULT 0,
            runs_conceded INTEGER DEFAULT 0,
            wickets INTEGER DEFAULT 0,
            is_out BOOLEAN DEFAULT FALSE,
            dismissal_text VARCHAR
        );

        CREATE SEQUENCE IF NOT EXISTS seq_tournament_deliveries START 1;
        CREATE TABLE IF NOT EXISTS tournament_deliveries (
            id INTEGER DEFAULT nextval('seq_tournament_deliveries'),
            match_id VARCHAR,
            innings INTEGER DEFAULT 1,
            over_num INTEGER,
            ball_num INTEGER,
            batter_name VARCHAR,
            bowler_name VARCHAR,
            non_striker_name VARCHAR,
            runs_batter INTEGER DEFAULT 0,
            runs_extra INTEGER DEFAULT 0,
            extra_type VARCHAR,
            is_wicket BOOLEAN DEFAULT FALSE,
            dismissal_kind VARCHAR,
            player_dismissed VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def check_db_exists() -> bool:
    if check_postgres_connection():
        return True
    return settings.DUCKDB_PATH.exists() and settings.DUCKDB_PATH.stat().st_size > 0

def get_db_status() -> Dict[str, Any]:
    pg_ok = check_postgres_connection()
    engine = "PostgreSQL 16 + pgvector" if pg_ok else "DuckDB Analytical Mirror"
    match_count = 0
    delivery_count = 0
    player_count = 0

    try:
        df_m = execute_query("SELECT COUNT(*) as cnt FROM matches;")
        match_count = int(df_m.iloc[0]["cnt"]) if not df_m.empty else 0
        df_d = execute_query("SELECT COUNT(*) as cnt FROM deliveries;")
        delivery_count = int(df_d.iloc[0]["cnt"]) if not df_d.empty else 0
        df_p = execute_query("SELECT COUNT(*) as cnt FROM players;")
        player_count = int(df_p.iloc[0]["cnt"]) if not df_p.empty else 0
    except Exception as e:
        logger.debug(f"Count query failed: {e}")

    return {
        "engine": engine,
        "postgres_connected": pg_ok,
        "matches_count": match_count,
        "deliveries_count": delivery_count,
        "players_count": player_count,
        "ready": match_count > 0 or pg_ok,
    }

def execute_query(sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
    pool = get_pool()
    if pool is not None:
        try:
            pg_sql = sql.replace("?", "%s")
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(pg_sql, params or [])
                    cols = [desc[0] for desc in cur.description] if cur.description else []
                    rows = cur.fetchall() if cur.description else []
                    return pd.DataFrame(rows, columns=cols)
        except Exception as e:
            logger.warning(f"PostgreSQL execute_query error, falling back to DuckDB mirror: {e}")

    duck_sql = sql.replace("%s", "?")
    conn = get_duckdb_mirror()
    with _duckdb_lock:
        cursor = conn.cursor()
        try:
            if params:
                return cursor.execute(duck_sql, params).df()
            else:
                return cursor.execute(duck_sql).df()
        finally:
            cursor.close()

def execute_statement(sql: str, params: Optional[List[Any]] = None) -> int:
    pool = get_pool()
    if pool is not None:
        try:
            pg_sql = sql.replace("?", "%s")
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(pg_sql, params or [])
                    conn.commit()
                    return cur.rowcount
        except Exception as e:
            logger.warning(f"PostgreSQL execute_statement error: {e}")

    duck_sql = sql.replace("%s", "?")
    conn = get_duckdb_mirror()
    with _duckdb_lock:
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(duck_sql, params)
            else:
                cursor.execute(duck_sql)
            return 1
        finally:
            cursor.close()

def init_schema():
    init_postgres_schema()
    get_duckdb_mirror()

class DatabaseClient:
    def query(self, sql: str, params: Optional[Any] = None) -> List[Dict[str, Any]]:
        p_list = list(params) if params else None
        df = execute_query(sql, p_list)
        if df.empty:
            return []
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")

    def execute(self, sql: str, params: Optional[Any] = None) -> int:
        p_list = list(params) if params else None
        return execute_statement(sql, p_list)

_db_client = DatabaseClient()

def get_db() -> DatabaseClient:
    return _db_client

