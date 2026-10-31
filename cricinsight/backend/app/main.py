"""
CricInsight — NLP-Powered Cricket Performance Analysis & RAG System API.
FastAPI modular application orchestrating:
1. NLP query interpretation (Gemini primary, Qwen local fallback, deterministic resilience)
2. Conversational context & coreference resolution
3. Database-grounded entity & format resolution
4. Calibrated query confidence evaluation
5. Deterministic cricket analytics calculation (Python + Pandas)
6. Hybrid RAG retrieval (pgvector + PostgreSQL FTS + RRF)
7. Adaptive fl_chart specification generation
8. Evidence-grounded insight generation
"""

import uuid
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.db import get_db_status, execute_query, execute_statement
from app.ingestion.ingestion_service import IngestionService
from app.schemas.api_contracts import (
    ChatQueryRequest,
    ChatQueryResponse,
    ProviderInfo,
    ConfidenceBreakdown,
)
from app.schemas.verification_contracts import (
    CricketMetricSet,
    LocalComputationEvidence,
    ExternalVerificationEvidence,
    FieldComparisonItem,
    DiscrepancyReport,
    VerifiedResult,
    DualPipelineAudit,
)
from app.services.gemini_verification_service import GeminiVerificationService
from app.services.metric_comparator import MetricComparator
from app.services.enrichment_recalculation_service import EnrichmentRecalculationService
from app.services.dataset_service import get_dataset_coverage, get_dataset_status
from app.analytics.engine import analyze_player_batting, compare_players
from app.visualization.chart_selector import select_chart_specification

from app.nlp.providers.provider_manager import ProviderManager
from app.nlp.conversation_context import ConversationManager
from app.nlp.entity_resolution import EntityResolver
from app.nlp.confidence import ConfidenceEvaluator
from app.retrieval.hybrid_search import HybridKnowledgeRetriever
from app.insights.insight_generator import InsightGenerator
from app.evaluation.benchmark_runner import BenchmarkRunner
from app.services.tournament_service import TournamentService
from app.services.career_records_service import CareerRecordsService

logger = logging.getLogger("cricinsight.api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NLP-Powered Cricket Performance Analysis & RAG System API",
)

@app.on_event("startup")
def on_startup():
    try:
        CareerRecordsService.init_and_seed()
    except Exception as e:
        logger.warning(f"Could not seed career records on startup: {e}")


# CORS configuration for Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
provider_manager = ProviderManager()
insight_generator = InsightGenerator()

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "message": "CricInsight NLP-Powered Cricket Performance Analysis API is active.",
        "status": "online"
    }

@app.get("/api/health")
def health_check():
    db_status = get_db_status()
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_engine": db_status["engine"],
        "database_ready": db_status["ready"],
        "counts": {
            "matches": db_status["matches_count"],
            "deliveries": db_status["deliveries_count"],
            "players": db_status["players_count"],
        }
    }

@app.get("/api/dataset/coverage")
def dataset_coverage():
    return get_dataset_coverage()

@app.get("/api/dataset/status")
def dataset_status():
    return get_dataset_status()

@app.get("/api/players/search")
def search_players(q: str = Query(..., min_length=1, description="Player search query")):
    """Fuzzy and alias search for players from the authoritative database."""
    sql = """
        SELECT DISTINCT p.id, p.canonical_name, a.alias
        FROM players p
        LEFT JOIN player_aliases a ON p.id = a.player_id
        WHERE LOWER(p.canonical_name) LIKE ? OR LOWER(a.alias) LIKE ?
        LIMIT 20;
    """
    term = f"%{q.lower().strip()}%"
    df = execute_query(sql, [term, term])
    if df.empty:
        return []
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")

@app.post("/api/chat/query", response_model=ChatQueryResponse)
async def chat_query(req: ChatQueryRequest):
    """
    Main conversational query orchestration endpoint.
    Guarantees deterministic analytics, grounded explanations, and multi-tier confidence.
    """
    t_start = time.perf_counter()
    request_id = str(uuid.uuid4())
    conv_id = req.context.get("conversation_id", f"conv_{request_id[:8]}") if req.context else f"conv_{request_id[:8]}"

    # Step 1: Centralized NLP Interpretation (Gemini -> Qwen -> Deterministic fallback)
    nlp_exec = await provider_manager.interpret(req.prompt, request_id=request_id)
    intent = nlp_exec.intent

    # Step 2: Multi-turn Conversation & Coreference Resolution
    intent = ConversationManager.resolve_follow_up(conv_id, intent, req.prompt)

    # Step 3: Entity Resolution & Format Normalization against database
    resolved_players = []
    unresolved_players = []
    is_ambiguous = False
    clarification_options = []

    for p_name in intent.players:
        res = EntityResolver.resolve_player(p_name)
        if res.is_ambiguous:
            is_ambiguous = True
            clarification_options.extend(res.candidates or [])
        if res.canonical_name:
            resolved_players.append(res.canonical_name)
        else:
            unresolved_players.append(p_name)

    # Format normalization
    if intent.format:
        intent.format = EntityResolver.normalize_format(intent.format)

    # Step 4: Calibrated Multi-tier Confidence Evaluation
    confidence = ConfidenceEvaluator.evaluate(
        intent_schema=intent,
        schema_valid=True,
        resolved_player_count=len(resolved_players),
        unresolved_players=unresolved_players,
        is_ambiguous=is_ambiguous,
    )

    # Step 4: Calibrated Multi-tier Confidence Evaluation & Knowledge Query Check
    prompt_lower = req.prompt.lower()
    is_knowledge_or_milestone = (
        intent.intent in ["bowling_record", "historical_record", "record_lookup"]
        or any(w in prompt_lower for w in [
            "dls", "duckworth", "rule", "rules", "lbw", "wides", "super over", "world record",
            "264", "400", "highest score", "175", "183", "average", "highest wicket", "most wicket",
            "leading wicket", "most centuries", "highest team total", "highest total", "record"
        ])
        or any(name in prompt_lower for name in ["bradman", "tendulkar", "lara", "gayle", "kapil dev", "dhoni", "bumrah", "rohit", "kohli", "smith"])
    )

    # Ambiguity / Clarification check (bypassed if knowledge or career record is query target)
    if not is_knowledge_or_milestone and (intent.needs_clarification or is_ambiguous or (not resolved_players and intent.intent in ["player_summary", "comparison", "recent_form"])):
        clarif_q = intent.clarification_question or (
            f"Could you clarify which player you are referring to? Multiple matches found: {', '.join(clarification_options)}"
            if is_ambiguous
            else "Which player's records would you like to inspect?"
        )
        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        try:
            execute_statement("""
                INSERT INTO query_logs (
                    request_id, prompt, session_id, provider, model_name, status, latency_ms, fallback_used, fallback_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, [
                request_id, req.prompt, conv_id, nlp_exec.provider_name, nlp_exec.model_name,
                "clarification_required", latency_ms, nlp_exec.fallback_used, nlp_exec.fallback_reason
            ])
        except Exception as e:
            logger.debug(f"Could not persist query log: {e}")

        return ChatQueryResponse(
            request_id=request_id,
            status="clarification_required",
            answer=clarif_q,
            interpretation=intent.model_dump(),
            confidence=confidence,
            provider=ProviderInfo(
                name=nlp_exec.provider_name,
                model=nlp_exec.model_name,
                latency_ms=latency_ms,
                fallback_used=nlp_exec.fallback_used,
                fallback_reason=nlp_exec.fallback_reason,
            ),
            clarification_required=True,
            clarification_options=clarification_options or ["Virat Kohli", "Rohit Sharma", "David Warner"]
        )


    # Step 5: Dual Independent Pipelines Execution
    is_comparison = len(resolved_players) > 1 or intent.intent == "comparison"
    match_type = intent.format
    opponent = intent.opponent
    recent_n = intent.last_n_innings

    coverage_info = get_dataset_coverage()
    metrics_list = []
    chart_spec = {}
    pipeline_audit: Optional[DualPipelineAudit] = None
    verified_result: Optional[VerifiedResult] = None
    discrepancy_report: Optional[DiscrepancyReport] = None

    if is_comparison:
        comp_res = compare_players(
            players=resolved_players,
            match_type=match_type,
            opponent=opponent,
            start_date=intent.start_date,
            end_date=intent.end_date,
            last_n_innings=recent_n
        )
        metrics_list = comp_res.get("comparison", [])
        chart_spec = select_chart_specification("player_comparison", comp_res)
    elif resolved_players:
        player_name = resolved_players[0]

        # Branch 1: Independent Local Deterministic Analytics Engine
        async def compute_local():
            return analyze_player_batting(
                player_name=player_name,
                match_type=match_type,
                competition=intent.competition,
                season=intent.season,
                opponent=opponent,
                venue=intent.venue,
                start_date=intent.start_date,
                end_date=intent.end_date,
                last_n_innings=recent_n,
            )

        # Branch 2: Parallel External Verification (Independent Grounding)
        async def verify_external():
            return await GeminiVerificationService.verify_statistics(
                player=player_name,
                competition=intent.competition,
                season=intent.season,
                category=intent.statistical_category or "batting"
            )

        # Execute Branch 1 & Branch 2 strictly in parallel
        analysis_data, external_verif = await asyncio.gather(
            compute_local(),
            verify_external()
        )

        local_m = analysis_data.get("metrics", {})
        local_metric_set = CricketMetricSet(
            matches=local_m.get("matches"),
            innings=local_m.get("innings"),
            runs=local_m.get("runs"),
            balls_faced=local_m.get("balls_faced"),
            not_outs=local_m.get("not_outs"),
            batting_average=local_m.get("batting_average"),
            strike_rate=local_m.get("strike_rate"),
            high_score=local_m.get("high_score"),
            high_score_not_out=local_m.get("high_score_not_out", False),
            fifties=local_m.get("fifties"),
            hundreds=local_m.get("hundreds"),
            fours=local_m.get("fours"),
            sixes=local_m.get("sixes"),
        )

        local_comp = LocalComputationEvidence(
            player=player_name,
            competition=intent.competition,
            season=intent.season,
            category=intent.statistical_category or "batting",
            metrics=local_metric_set,
            granularity=analysis_data.get("granularity", "ball_by_ball"),
            matches_count=analysis_data.get("matches_count", 0),
            innings_count=local_m.get("innings_count", 0),
            match_ids=analysis_data.get("match_ids", []),
            calculated_at=datetime.utcnow().isoformat(),
            provenance="Local Deterministic Analytics Engine (DuckDB/PostgreSQL)",
        )

        # Step 6: Dedicated Field-Level Comparison
        discrepancy_report = MetricComparator.compare(local_comp, external_verif)

        # Step 7: Discrepancy Resolution & Local Enrichment
        verified_result, final_discrepancy, final_local = EnrichmentRecalculationService.reconcile_and_enrich(
            local_comp=local_comp,
            external_verif=external_verif,
            discrepancy_report=discrepancy_report,
            format_type=match_type or "T20"
        )

        # Complete Dual-Pipeline Audit preservation
        pipeline_audit = DualPipelineAudit(
            local_computation=local_comp,
            external_verification=external_verif,
            discrepancy_report=final_discrepancy,
            verified_result=verified_result,
            pipeline_latency_ms=round((time.perf_counter() - t_start) * 1000, 2)
        )

        # Use verified result metrics
        vm = verified_result.metrics
        metrics_list = [{
            "player_name": player_name,
            "matches": vm.matches,
            "innings": vm.innings,
            "innings_count": vm.innings or 0,
            "total_runs": vm.runs or 0,
            "runs": vm.runs or 0,
            "balls_faced": vm.balls_faced or 0,
            "not_outs": vm.not_outs or 0,
            "batting_average": vm.batting_average,
            "strike_rate": vm.strike_rate or 0.0,
            "high_score": vm.high_score or 0,
            "high_score_not_out": vm.high_score_not_out or False,
            "fifties": vm.fifties or 0,
            "centuries": vm.hundreds or 0,
            "hundreds": vm.hundreds or 0,
            "fours": vm.fours or 0,
            "sixes": vm.sixes or 0,
            "boundary_runs": ((vm.fours or 0) * 4) + ((vm.sixes or 0) * 6),
            "boundary_percentage": round(((((vm.fours or 0) * 4) + ((vm.sixes or 0) * 6)) / max(1, vm.runs or 1)) * 100, 1),
            "std_deviation": local_m.get("std_deviation", 0.0),
            "median_score": local_m.get("median_score", 0.0),
            "sample_size_adequate": (vm.innings or 0) >= 5,
        }]

        analysis_type = "recent_performance" if (recent_n or intent.intent == "recent_form") else "single_player_summary"
        chart_spec = select_chart_specification(analysis_type, analysis_data)

    # Step 8: Career Milestones & Hybrid RAG Retrieval
    career_milestones = []
    lookup_targets = resolved_players if resolved_players else intent.players
    if not lookup_targets:
        for legend in ["Rohit Sharma", "Virat Kohli", "Sachin Tendulkar", "Brian Lara", "Donald Bradman", "Chris Gayle", "MS Dhoni", "Kapil Dev"]:
            if legend.lower() in prompt_lower:
                lookup_targets = [legend]
                break

    for p in lookup_targets:
        career_milestones.extend(CareerRecordsService.get_career_milestones_for_player(p, match_format=intent.format))

    domain_evidence = HybridKnowledgeRetriever.search(req.prompt, top_k=2)

    # Step 9: Grounded Insight Synthesis (Qwen Primary -> Gemini -> Deterministic)
    answer_text = await insight_generator.generate(
        query=req.prompt,
        intent=intent,
        metrics=metrics_list,
        evidence=domain_evidence,
        limitations=coverage_info.get("coverage_limitations", []),
        career_milestones=career_milestones,
        verified_result=verified_result,
        discrepancy_report=discrepancy_report,
    )

    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
    try:
        execute_statement("""
            INSERT INTO query_logs (
                request_id, prompt, session_id, provider, model_name, status, latency_ms, fallback_used, fallback_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            request_id, req.prompt, conv_id, nlp_exec.provider_name, nlp_exec.model_name,
            "success", latency_ms, nlp_exec.fallback_used, nlp_exec.fallback_reason
        ])
    except Exception as e:
        logger.debug(f"Could not persist query log: {e}")

    return ChatQueryResponse(
        request_id=request_id,
        status="success",
        answer=answer_text,
        interpretation=intent.model_dump(),
        confidence=confidence,
        provider=ProviderInfo(
            name=nlp_exec.provider_name,
            model=nlp_exec.model_name,
            latency_ms=latency_ms,
            fallback_used=nlp_exec.fallback_used,
            fallback_reason=nlp_exec.fallback_reason,
        ),
        metrics=metrics_list,
        chart=chart_spec,
        evidence=domain_evidence,
        dataset_coverage={
            "matches": coverage_info.get("total_matches", 0),
            "formats": [f["match_type"] for f in coverage_info.get("formats", [])]
        },
        limitations=coverage_info.get("coverage_limitations", []),
        verification_pipeline=pipeline_audit,
    )

@app.get("/api/evaluation/summary")
def get_evaluation_summary():
    """Returns NLP & retrieval evaluation metrics and benchmark accuracy."""
    return BenchmarkRunner.get_latest_summary()

@app.post("/api/evaluation/run")
async def run_evaluation_benchmark():
    """Triggers an on-demand evaluation suite execution."""
    return await BenchmarkRunner.run_evaluation()

@app.get("/api/evaluation/providers")
def get_provider_status():
    """Returns status and configuration of Gemini, Qwen, and Deterministic engines."""
    return {
        "primary_provider": {
            "name": "gemini",
            "model": settings.GEMINI_MODEL,
            "configured": provider_manager.gemini.is_configured,
            "timeout_seconds": settings.GEMINI_TOTAL_TIMEOUT,
        },
        "fallback_provider": {
            "name": "qwen",
            "model": settings.QWEN_MODEL,
            "base_url": settings.QWEN_BASE_URL,
            "enabled": settings.LLM_FALLBACK_ENABLED,
            "timeout_seconds": settings.QWEN_TOTAL_TIMEOUT,
        },
        "resilience_engine": {
            "name": "deterministic",
            "model": "rule_based_python",
            "status": "active",
        },
        "max_overall_deadline_seconds": settings.LLM_MAX_TOTAL_DEADLINE,
    }

@app.post("/api/analyze")
async def analyze_legacy(payload: Dict[str, Any]):
    """Backwards-compatible legacy endpoint wrapping /api/chat/query."""
    prompt = payload.get("prompt") or payload.get("query") or ""
    req = ChatQueryRequest(prompt=prompt, context=payload.get("context"))
    res = await chat_query(req)
    first_metric = res.metrics[0] if res.metrics else {}
    return {
        "status": res.status,
        "scope": res.interpretation,
        "stats": first_metric,
        "metrics": res.metrics,
        "chart": res.chart,
        "insight": res.answer,
        "answer": res.answer,
        "confidence": res.confidence,
        "provider": res.provider,
        "evidence": res.evidence,
        "dataset_coverage": res.dataset_coverage,
        "limitations": res.limitations,
        "clarification_required": res.clarification_required,
    }

@app.post("/api/ingestion/import")
def run_import(path: Optional[str] = None):
    """Trigger ingestion of Cricsheet match records from directory."""
    dir_to_import = Path(path) if path else settings.FIXTURES_DIR
    if not dir_to_import.exists():
        raise HTTPException(status_code=400, detail=f"Directory {dir_to_import} not found")
    return IngestionService.import_directory(dir_to_import)

@app.post("/api/ingestion/update")
def run_update(path: Optional[str] = None):
    """Re-scan and idempotently update Cricsheet dataset."""
    dir_to_import = Path(path) if path else settings.FIXTURES_DIR
    if not dir_to_import.exists():
        raise HTTPException(status_code=400, detail=f"Directory {dir_to_import} not found")
    return IngestionService.import_directory(dir_to_import)

@app.get("/api/ingestion/history")
def get_ingestion_history():
    """Retrieve historical ingestion runs."""
    df = execute_query("""
        SELECT id, source, started_at, finished_at, status,
               files_processed, inserted_count, updated_count, skipped_count, rejected_count
        FROM ingestion_runs
        ORDER BY started_at DESC
        LIMIT 20;
    """)
    if df.empty:
        return []
    records = [{k: (None if pd.isna(v) else v) for k, v in row.items()} for row in df.to_dict(orient="records")]
    return jsonable_encoder(records)

@app.get("/api/teams")
def get_teams():
    """Retrieve unique teams present in the imported dataset."""
    teams_set = set()
    df_inn = execute_query("SELECT DISTINCT batting_team FROM innings WHERE batting_team IS NOT NULL AND batting_team != '';")
    if not df_inn.empty:
        teams_set.update(df_inn["batting_team"].tolist())
    df_bowl = execute_query("SELECT DISTINCT bowling_team FROM innings WHERE bowling_team IS NOT NULL AND bowling_team != '';")
    if not df_bowl.empty:
        teams_set.update(df_bowl["bowling_team"].tolist())

    df_all = execute_query("SELECT teams FROM matches;")
    if not df_all.empty:
        for _, row in df_all.iterrows():
            t_data = row["teams"]
            if hasattr(t_data, "__iter__") and not isinstance(t_data, (str, bytes)):
                teams_set.update([str(x) for x in t_data if str(x)])
            elif isinstance(t_data, str):
                teams_set.add(t_data)
    return sorted(list(teams_set))

@app.get("/api/competitions")
def get_competitions():
    """Retrieve unique competitions in the dataset."""
    df = execute_query("SELECT DISTINCT competition FROM matches WHERE competition IS NOT NULL AND competition != '' ORDER BY competition;")
    return df["competition"].tolist() if not df.empty else []

@app.get("/api/venues")
def get_venues():
    """Retrieve unique cricket venues in the dataset."""
    df = execute_query("SELECT DISTINCT venue FROM matches WHERE venue IS NOT NULL AND venue != '' ORDER BY venue;")
    return df["venue"].tolist() if not df.empty else []

@app.get("/api/evaluation/queries")
def get_evaluation_queries(limit: int = 50):
    """Retrieve recent query evaluation logs."""
    df = execute_query("""
        SELECT request_id, prompt, session_id, provider, model_name, status, latency_ms, fallback_used, fallback_reason, created_at
        FROM query_logs
        ORDER BY created_at DESC
        LIMIT ?;
    """, [limit])
    if df.empty:
        return []
    records = [{k: (None if pd.isna(v) else v) for k, v in row.items()} for row in df.to_dict(orient="records")]
    return jsonable_encoder(records)


# ==============================================================================
# Local Tournament & Grassroots Match Scoring Endpoints
# ==============================================================================

@app.get("/api/tournaments")
def get_tournaments():
    """List all registered local cricket tournaments."""
    return TournamentService.list_tournaments()

@app.post("/api/tournaments")
def create_tournament(payload: Dict[str, Any]):
    """Create a new local tournament."""
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Tournament name is required")
    season = payload.get("season", "2026")
    fmt = payload.get("format", "T20")
    overs = int(payload.get("overs_limit", 20))
    return TournamentService.create_tournament(name=name, season=season, format=fmt, overs_limit=overs)

@app.get("/api/tournaments/{tournament_id}")
def get_tournament_details(tournament_id: str):
    """Retrieve full details of a tournament including fixtures and standings."""
    tour = TournamentService.get_tournament(tournament_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tour

@app.post("/api/tournaments/{tournament_id}/teams")
def add_tournament_team(tournament_id: str, payload: Dict[str, Any]):
    """Add a team and optional squad list to a tournament."""
    name = payload.get("name")
    short_code = payload.get("short_code")
    if not name or not short_code:
        raise HTTPException(status_code=400, detail="Team name and short_code are required")
    return TournamentService.add_team(
        tournament_id=tournament_id,
        name=name,
        short_code=short_code,
        captain=payload.get("captain"),
        color=payload.get("color", "#10B981"),
        players=payload.get("players", [])
    )

@app.post("/api/tournaments/{tournament_id}/matches")
def create_tournament_match(tournament_id: str, payload: Dict[str, Any]):
    """Schedule or create a match fixture between two registered teams."""
    team1_id = payload.get("team1_id")
    team2_id = payload.get("team2_id")
    if not team1_id or not team2_id:
        raise HTTPException(status_code=400, detail="team1_id and team2_id are required")
    return TournamentService.create_match(
        tournament_id=tournament_id,
        team1_id=team1_id,
        team2_id=team2_id,
        venue=payload.get("venue", "Local Sports Ground"),
        match_date=payload.get("match_date"),
        match_number=int(payload.get("match_number", 1))
    )

@app.post("/api/tournaments/matches/{match_id}/scorecard")
def record_match_scorecard(match_id: str, payload: Dict[str, Any]):
    """Summary Mode: Record post-match scorecard totals and individual player figures."""
    try:
        return TournamentService.record_scorecard(match_id, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tournaments/matches/{match_id}/ball")
def record_live_ball(match_id: str, payload: Dict[str, Any]):
    """Live Mode: Record ball-by-ball delivery, auto-rotate strike, and update score."""
    try:
        return TournamentService.record_live_ball(match_id, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tournaments/{tournament_id}/standings")
def get_tournament_standings(tournament_id: str):
    """Retrieve the real-time Points Table with exact Net Run Rate (NRR)."""
    return TournamentService.get_standings(tournament_id)

@app.get("/api/tournaments/{tournament_id}/leaderboard")
def get_tournament_leaderboard(tournament_id: str):
    """Retrieve the Orange Cap (Runs) and Purple Cap (Wickets) leaderboards."""
    return TournamentService.get_leaderboard(tournament_id)


