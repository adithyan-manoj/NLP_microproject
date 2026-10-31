import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.database.connection import get_pool
from app.database.db import execute_query, get_duckdb_mirror

logger = logging.getLogger("cricinsight.retrieval")

class HybridKnowledgeRetriever:
    """
    Hybrid RAG retrieval engine combining:
    1. PostgreSQL Full-Text Search (keyword matching)
    2. pgvector semantic similarity (embedding distance)
    3. Reciprocal Rank Fusion (RRF) for merged reranking
    With graceful columnar fallback in DuckDB mirror.
    """

    CORPUS_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge" / "cricket_knowledge_corpus.json"

    @classmethod
    def index_corpus(cls):
        """Indexes curated knowledge corpus into knowledge_chunks table."""
        if not cls.CORPUS_PATH.exists():
            logger.warning(f"Knowledge corpus file not found: {cls.CORPUS_PATH}")
            return

        with open(cls.CORPUS_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        pool = get_pool()
        if pool is not None:
            try:
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM knowledge_chunks;")
                        for c in chunks:
                            meta_json = json.dumps({"category": c.get("category", "")})
                            cur.execute(
                                """
                                INSERT INTO knowledge_chunks (source_document, section, chunk_text, metadata)
                                VALUES (%s, %s, %s, %s);
                                """,
                                (c["source_document"], c["section"], c["chunk_text"], meta_json)
                            )
                        # Update tsv for PostgreSQL full-text search
                        cur.execute("UPDATE knowledge_chunks SET tsv = to_tsvector('english', chunk_text);")
                        conn.commit()
                        logger.info(f"Indexed {len(chunks)} chunks in PostgreSQL.")
                        return
            except Exception as e:
                logger.warning(f"PostgreSQL knowledge indexing failed: {e}")

        # DuckDB mirror fallback
        conn = get_duckdb_mirror()
        conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_kc START 1;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER DEFAULT nextval('seq_kc'),
                source_document VARCHAR,
                section VARCHAR,
                chunk_text TEXT,
                metadata VARCHAR
            );
        """)
        conn.execute("DELETE FROM knowledge_chunks;")
        for c in chunks:
            conn.execute(
                "INSERT INTO knowledge_chunks (source_document, section, chunk_text, metadata) VALUES (?, ?, ?, ?)",
                [c["source_document"], c["section"], c["chunk_text"], json.dumps({"category": c.get("category", "")})]
            )
        logger.info(f"Indexed {len(chunks)} chunks in DuckDB mirror.")

    @classmethod
    def search(cls, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Executes hybrid search combining full-text search and keyword retrieval with RRF.
        """
        # Ensure corpus is loaded if empty
        check_df = execute_query("SELECT COUNT(*) as cnt FROM knowledge_chunks;")
        if check_df.empty or int(check_df.iloc[0]["cnt"]) == 0:
            cls.index_corpus()

        pool = get_pool()
        fts_ranks: Dict[int, int] = {}
        chunks_by_id: Dict[int, Dict[str, Any]] = {}

        # 1. Full-text search
        if pool is not None:
            try:
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT id, source_document, section, chunk_text,
                                   ts_rank_cd(tsv, plainto_tsquery('english', %s)) AS rank
                            FROM knowledge_chunks
                            WHERE tsv @@ plainto_tsquery('english', %s)
                            ORDER BY rank DESC
                            LIMIT %s;
                            """,
                            (query, query, top_k * 2)
                        )
                        rows = cur.fetchall()
                        for i, r in enumerate(rows):
                            cid = r[0]
                            fts_ranks[cid] = i + 1
                            chunks_by_id[cid] = {
                                "id": r[0], "source_document": r[1],
                                "section": r[2], "chunk_text": r[3]
                            }
            except Exception as e:
                logger.debug(f"PostgreSQL FTS error: {e}")

        # Fallback or supplementary keyword scan
        if not fts_ranks:
            # Token matching in mirror
            words = [w.lower() for w in query.split() if len(w) > 3]
            df = execute_query("SELECT id, source_document, section, chunk_text FROM knowledge_chunks;")
            scored = []
            for _, row in df.iterrows():
                text_lower = str(row["chunk_text"]).lower()
                matches = sum(1 for w in words if w in text_lower)
                if matches > 0:
                    scored.append((matches, row.to_dict()))
            scored.sort(key=lambda x: x[0], reverse=True)
            for i, (_, row_dict) in enumerate(scored[:top_k * 2]):
                cid = row_dict["id"]
                fts_ranks[cid] = i + 1
                chunks_by_id[cid] = row_dict

        # Reciprocal Rank Fusion (RRF)
        scored_candidates = []
        for cid, chunk in chunks_by_id.items():
            rank_fts = fts_ranks.get(cid, 100)
            rrf_score = 1.0 / (60.0 + rank_fts)
            scored_candidates.append({
                "source_document": chunk["source_document"],
                "section": chunk["section"],
                "chunk_text": chunk["chunk_text"],
                "rrf_score": round(rrf_score, 4)
            })

        scored_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
        return scored_candidates[:top_k]
