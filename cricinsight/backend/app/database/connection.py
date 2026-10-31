"""
Database Connection & Session Management for CricInsight.
Supports PostgreSQL 16 with pgvector via psycopg 3 connection pooling,
with resilient connection checking and zero-latency fallback caching.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import settings

logger = logging.getLogger("cricinsight.database")

_pool: Optional[ConnectionPool] = None
_pg_available: Optional[bool] = None

def check_postgres_connection(force_check: bool = False) -> bool:
    global _pg_available
    if _pg_available is not None and not force_check:
        return _pg_available
    try:
        db_url = settings.get_database_url()
        with psycopg.connect(db_url, connect_timeout=1) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                res = cur.fetchone()
                _pg_available = bool(res is not None and res[0] == 1)
                return _pg_available
    except Exception:
        _pg_available = False
        return False

def get_pool() -> Optional[ConnectionPool]:
    global _pool
    if not check_postgres_connection():
        return None
    if _pool is None:
        try:
            _pool = ConnectionPool(
                conninfo=settings.get_database_url(),
                min_size=1,
                max_size=10,
                timeout=1.0,
                open=True
            )
            logger.info("Initialized PostgreSQL connection pool successfully.")
        except Exception as e:
            logger.warning(f"Failed to open PostgreSQL pool: {e}")
            _pool = None
    return _pool

def init_postgres_schema() -> bool:
    """Executes the initial migration schema in PostgreSQL if reachable."""
    if not check_postgres_connection():
        return False

    migration_path = settings.BACKEND_DIR / "migrations" / "001_initial_schema.sql"
    if not migration_path.exists():
        logger.error(f"Migration file not found at {migration_path}")
        return False

    with open(migration_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    try:
        db_url = settings.get_database_url()
        with psycopg.connect(db_url, autocommit=True, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
        logger.info("Successfully applied PostgreSQL initial schema.")
        return True
    except Exception as e:
        logger.warning(f"Error applying PostgreSQL schema: {e}")
        return False
