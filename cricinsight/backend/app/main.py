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
    find_specific_match,
)
from app.services.nlp_service import extract_query_entities
from app.services.insight_service import synthesize_rag_response

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NLP-Powered Cricket Performance Analysis & RAG System API",
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
        "rag_engine": "DuckDB-OLAP + Gemini RAG",
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

    # --------------------------------------------------------------------------
    # CASE 1: MATCH-LEVEL INQUIRY (Scorecards, Winner, Innings, Top Performers)
    # --------------------------------------------------------------------------
    if structured.intent == "match_analysis" and (len(structured.teams) >= 1 or structured.year):
        team_a = structured.teams[0] if len(structured.teams) >= 1 else None
        team_b = structured.teams[1] if len(structured.teams) >= 2 else None

        match_record = find_specific_match(
            team_a=team_a,
            team_b=team_b,
            match_type=structured.format,
            year=structured.year
        )

        if not match_record:
            teams_str = f"{team_a}" + (f" vs {team_b}" if team_b else "")
            raise HTTPException(
                status_code=404,
                detail=f"No match found for {teams_str} with the specified format/date in DuckDB."
            )

        # Build chart for match innings totals
        chart_series = []
        for inn in match_record["innings"]:
            chart_series.append({
                "name": inn["batting_team"],
                "data": [
                    {"x": "Runs Scored", "y": inn["runs"]},
                    {"x": "Wickets Lost (x10)", "y": inn["wickets"] * 10},
                    {"x": "Overs (x5)", "y": round(inn["overs"] * 5, 1)},
                ]
            })

        scope = {
            "players": [b["batter"] for b in match_record["top_batters"][:3]],
            "teams": match_record["teams"],
            "format": match_record["format"],
            "date_range": match_record["date"],
            "venue": match_record["venue"],
            "competition": match_record["competition"],
            "analysis_type": "Specific Match Scorecard",
        }

        # Observations
        observations = [
            f"Result: {match_record['result']}.",
            f"Top Batter: {match_record['top_batters'][0]['batter']} ({match_record['top_batters'][0]['batting_team']}) scored {match_record['top_batters'][0]['runs']} off {match_record['top_batters'][0]['balls']} balls." if match_record['top_batters'] else "No batting records.",
            f"Top Bowler: {match_record['top_bowlers'][0]['bowler']} took {match_record['top_bowlers'][0]['wickets']} wickets conceding {match_record['top_bowlers'][0]['runs_conceded']} runs." if match_record['top_bowlers'] else "No bowling records.",
            f"Played at {match_record['venue']} ({match_record['competition']}).",
        ]

        # Representative stats for cards
        stats = {
            "player_name": match_record["result"],
            "total_runs": sum(inn["runs"] for inn in match_record["innings"]),
            "batting_average": match_record["top_batters"][0]["runs"] if match_record["top_batters"] else 0,
            "strike_rate": round((match_record["top_batters"][0]["runs"] / max(1, match_record["top_batters"][0]["balls"])) * 100, 1) if match_record["top_batters"] else 0,
            "high_score": match_record["top_batters"][0]["runs"] if match_record["top_batters"] else 0,
            "high_score_not_out": False,
            "innings_count": len(match_record["innings"]),
            "dismissals": sum(inn["wickets"] for inn in match_record["innings"]),
            "balls_faced": sum(inn["overs"] * 6 for inn in match_record["innings"]),
            "std_deviation": 0.0,
            "consistency_rating": match_record["competition"],
            "fours": sum(b["fours"] for b in match_record["top_batters"]),
            "sixes": sum(b["sixes"] for b in match_record["top_batters"]),
            "boundary_runs": sum(b["fours"] * 4 + b["sixes"] * 6 for b in match_record["top_batters"]),
            "centuries": sum(1 for b in match_record["top_batters"] if b["runs"] >= 100),
            "fifties": sum(1 for b in match_record["top_batters"] if 50 <= b["runs"] < 100),
        }

        chart = {
            "chart_type": "bar",
            "title": f"Match Summary: {' vs '.join(match_record['teams'])} ({match_record['format']})",
            "subtitle": f"{match_record['date']} at {match_record['venue']} - {match_record['result']}",
            "x_axis_label": "Metric",
            "y_axis_label": "Value",
            "series": chart_series,
        }

        insight = synthesize_rag_response(
            query_intent="match_analysis",
            scope=scope,
            stats=stats,
            observations=observations,
            match_data=match_record
        )

        return {
            "status": "success",
            "scope": scope,
            "stats": stats,
            "chart": chart,
            "insight": insight,
            "observations": observations,
            "match_details": match_record,
        }

    # --------------------------------------------------------------------------
    # CASE 2: PLAYER ANALYSIS OR COMPARISON
    # --------------------------------------------------------------------------
    player_names = structured.players
    match_type = structured.format
    opponent = structured.opponent
    recent_n = structured.recent_n

    if not player_names:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not identify a player or match from your question. "
                "Please specify a player (e.g. 'Rohit Sharma vs Steve Smith') or a match (e.g. 'India vs Pakistan 2026 T20')."
            )
        )

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

        insight = synthesize_rag_response(
            query_intent="player_analysis",
            scope=scope,
            stats=stats,
            observations=observations
        )

        return {
            "status": "success",
            "scope": scope,
            "stats": stats,
            "chart": chart,
            "insight": insight,
            "observations": observations,
        }

    else:
        # Comparison mode across players
        series_data = []
        combined_obs = []
        comparison_list = []

        for c_name, can_name in resolved_players:
            df = query_player_innings(
                cricsheet_name=c_name,
                match_type=match_type,
                opponent=opponent,
                recent_n=recent_n
            )
            if df.empty and (match_type or opponent):
                df = query_player_innings(c_name, recent_n=recent_n)

            p_metric = calculate_statistical_metrics(df, can_name)
            comparison_list.append(p_metric)

            combined_obs.append(
                f"{can_name}: {p_metric['total_runs']:,} runs, Avg {p_metric['batting_average']}, SR {p_metric['strike_rate']} ({p_metric['centuries']} 100s, {p_metric['fifties']} 50s)."
            )

            # High value multi-metric bar chart for comparison
            series_data.append({
                "name": can_name,
                "data": [
                    {"x": "Batting Avg", "y": p_metric["batting_average"]},
                    {"x": "Strike Rate / 2", "y": round(p_metric["strike_rate"] / 2, 1)},
                    {"x": "Centuries (x10)", "y": p_metric["centuries"] * 10},
                    {"x": "50+ Scores (x5)", "y": (p_metric["centuries"] + p_metric["fifties"]) * 5},
                    {"x": "Innings / 2", "y": round(p_metric["innings_count"] / 2, 1)},
                ]
            })

        p_names_list = [p[1] for p in resolved_players]
        primary_player = comparison_list[0]

        chart = {
            "chart_type": "bar",
            "title": f"Head-to-Head Comparison: {' vs '.join(p_names_list)}",
            "subtitle": f"{match_type or 'All Formats'} career comparative metrics from DuckDB",
            "x_axis_label": "Metric",
            "y_axis_label": "Value",
            "series": series_data,
        }

        scope = {
            "players": p_names_list,
            "opponent": opponent,
            "format": match_type or "All formats",
            "date_range": "Career Records",
            "analysis_type": "Player Head-to-Head Comparison",
        }

        insight = synthesize_rag_response(
            query_intent="player_comparison",
            scope=scope,
            stats=primary_player,
            observations=combined_obs,
            comparison_data=comparison_list
        )

        return {
            "status": "success",
            "scope": scope,
            "stats": primary_player,
            "comparison": comparison_list,
            "chart": chart,
            "insight": insight,
            "observations": combined_obs,
        }

@app.get("/")
def root():
    return {
        "message": "Welcome to CricInsight API",
        "docs": "/docs",
        "health": "/api/health"
    }
