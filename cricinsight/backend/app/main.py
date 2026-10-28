import re
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from app.core.config import settings
from app.database.db import check_db_exists, get_db, execute_query
from app.services.cricket_data_service import (
    resolve_player_identity,
    query_player_innings,
    calculate_statistical_metrics,
)
from app.services.nlp_service import extract_query_entities
from app.services.insight_service import generate_analytical_insight

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NLP-Powered Cricket Performance Analysis System API",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None

@app.get("/api/health")
def health_check():
    db_ok = check_db_exists()
    match_count = 0
    delivery_count = 0
    player_count = 0

    if db_ok:
        try:
            with get_db(read_only=True) as conn:
                match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
                delivery_count = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
                player_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        except Exception:
            db_ok = False

    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "Ready" if db_ok else "No data",
        "counts": {
            "matches": match_count,
            "deliveries": delivery_count,
            "players": player_count,
        }
    }

@app.get("/api/players")
def list_players(q: Optional[str] = None):
    sql = "SELECT canonical_name, aliases FROM players"
    params = []
    if q:
        sql += " WHERE LOWER(canonical_name) LIKE ? OR LOWER(aliases) LIKE ?"
        params = [f"%{q.lower()}%", f"%{q.lower()}%"]
    sql += " LIMIT 50"
    df = execute_query(sql, params)
    return df.to_dict(orient="records")

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    structured = extract_query_entities(req.prompt, req.context)
    player_names = structured.players
    match_type = structured.format
    opponent = structured.opponent
    recent_n = structured.recent_n

    if not player_names:
        player_names = ["Virat Kohli"]

    # Resolve player codes
    resolved_players = []
    for p_name in player_names:
        res = resolve_player_identity(p_name)
        if res:
            resolved_players.append(res)
        else:
            resolved_players.append((p_name, p_name))

    is_comparison = len(resolved_players) > 1

    if not is_comparison:
        cricsheet_name, canonical_name = resolved_players[0]
        df = query_player_innings(
            cricsheet_name=cricsheet_name,
            match_type=match_type,
            opponent=opponent,
            start_date=structured.start_date,
            end_date=structured.end_date,
            recent_n=recent_n
        )

        # Fallback to unrestricted player innings if strict filter yields no matches
        if df.empty and (match_type or opponent):
            df = query_player_innings(
                cricsheet_name=cricsheet_name,
                match_type=None,
                opponent=None,
                recent_n=recent_n
            )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No innings found for {canonical_name} in the database."
            )

        stats = calculate_statistical_metrics(df, canonical_name)
        innings_count = stats["innings_count"]

        # Build chart series
        chart_series = [{
            "name": canonical_name,
            "data": [
                {
                    "x": f"Inn {i+1}",
                    "y": int(row.runs),
                    "date": str(row.date),
                    "opponent": row.bowling_team,
                    "balls": int(row.balls),
                }
                for i, row in df.iterrows()
            ]
        }]

        observations = [
            f"Accumulated {stats['total_runs']:,} runs across {innings_count} innings at {stats['strike_rate']} SR.",
            f"Achieved {stats['centuries']} centuries and {stats['fifties']} half-centuries ({((stats['centuries'] + stats['fifties']) / max(1, innings_count) * 100):.0f}% milestone rate).",
            f"Boundary contribution: {stats['fours']} fours & {stats['sixes']} sixes ({((stats['boundary_runs'] / max(1, stats['total_runs'])) * 100):.0f}% of total runs).",
            f"Recent form (last 5 innings average): {stats['rolling_avg_last_5']} runs per innings.",
        ]

        title = f"{canonical_name} Innings Progression"
        if opponent:
            title += f" vs {opponent}"
        if match_type:
            title += f" ({match_type})"

        chart = {
            "chart_type": structured.chart_preference or "line",
            "title": title,
            "subtitle": f"Last {innings_count} innings from DuckDB ball-by-ball records",
            "x_axis_label": "Innings",
            "y_axis_label": "Runs",
            "series": chart_series,
        }

        scope = {
            "players": [canonical_name],
            "opponent": opponent,
            "format": match_type or "All formats",
            "date_range": f"{df['date'].min()} to {df['date'].max()}",
            "analysis_type": "Innings Form Progression",
        }

        insight = generate_analytical_insight(scope, stats, observations)

    else:
        # Comparison mode across players
        series_data = []
        combined_obs = []
        p_stats_map = {}

        for c_name, can_name in resolved_players:
            df = query_player_innings(
                cricsheet_name=c_name,
                match_type=match_type,
                opponent=opponent,
                recent_n=recent_n
            )
            # If no innings under filter, get overall
            if df.empty and (match_type or opponent):
                df = query_player_innings(c_name, recent_n=recent_n)

            p_metric = calculate_statistical_metrics(df, can_name)
            p_stats_map[can_name] = p_metric

            combined_obs.append(
                f"{can_name}: {p_metric['total_runs']:,} runs in {p_metric['innings_count']} inns, "
                f"Avg: {p_metric['batting_average']}, SR: {p_metric['strike_rate']}"
            )

            series_data.append({
                "name": can_name,
                "data": [
                    {"x": "Avg", "y": p_metric["batting_average"]},
                    {"x": "Strike Rate / 2", "y": round(p_metric["strike_rate"] / 2, 1)},
                    {"x": "Innings", "y": p_metric["innings_count"]},
                ]
            })

        p1_name = resolved_players[0][1]
        stats = p_stats_map[p1_name]

        p_names_list = [p[1] for p in resolved_players]
        chart = {
            "chart_type": "bar",
            "title": f"Comparison: {' vs '.join(p_names_list)}",
            "subtitle": f"{match_type or 'All Formats'} metric comparison",
            "x_axis_label": "Metric",
            "y_axis_label": "Value",
            "series": series_data,
        }

        scope = {
            "players": p_names_list,
            "opponent": opponent,
            "format": match_type or "All formats",
            "date_range": "Available career matches",
            "analysis_type": "Player Head-to-Head Comparison",
        }

        observations = combined_obs
        insight = generate_analytical_insight(scope, stats, observations)

    return {
        "status": "success",
        "scope": scope,
        "stats": stats,
        "chart": chart,
        "insight": insight,
        "observations": observations,
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to CricInsight API",
        "docs": "/docs",
        "health": "/api/health"
    }
