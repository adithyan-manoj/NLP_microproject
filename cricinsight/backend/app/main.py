import re
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np

from app.core.config import settings
from app.database.db import check_db_exists, get_db, execute_query

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

# Curated player aliases for fast NLP resolution
PLAYER_MAP = {
    "kohli": ("V Kohli", "Virat Kohli"),
    "virat": ("V Kohli", "Virat Kohli"),
    "virat kohli": ("V Kohli", "Virat Kohli"),
    "rohit": ("RG Sharma", "Rohit Sharma"),
    "rohit sharma": ("RG Sharma", "Rohit Sharma"),
    "warner": ("DA Warner", "David Warner"),
    "david warner": ("DA Warner", "David Warner"),
    "smith": ("SPD Smith", "Steve Smith"),
    "steve smith": ("SPD Smith", "Steve Smith"),
    "steven smith": ("SPD Smith", "Steve Smith"),
    "babar": ("Babar Azam", "Babar Azam"),
    "babar azam": ("Babar Azam", "Babar Azam"),
    "bumrah": ("JJ Bumrah", "Jasprit Bumrah"),
    "jasprit bumrah": ("JJ Bumrah", "Jasprit Bumrah"),
    "root": ("JE Root", "Joe Root"),
    "joe root": ("JE Root", "Joe Root"),
    "rahul": ("KL Rahul", "KL Rahul"),
    "kl rahul": ("KL Rahul", "KL Rahul"),
    "gill": ("Shubman Gill", "Shubman Gill"),
    "shubman gill": ("Shubman Gill", "Shubman Gill"),
    "maxwell": ("GJ Maxwell", "Glenn Maxwell"),
    "head": ("TM Head", "Travis Head"),
    "travis head": ("TM Head", "Travis Head"),
    "rizwan": ("Mohammad Rizwan", "Mohammad Rizwan"),
    "williamson": ("KS Williamson", "Kane Williamson"),
    "kane williamson": ("KS Williamson", "Kane Williamson"),
    "starc": ("MA Starc", "Mitchell Starc"),
    "cummins": ("PJ Cummins", "Pat Cummins"),
    "shami": ("Mohammed Shami", "Mohammed Shami"),
}

TEAMS = [
    "Australia", "India", "England", "Pakistan", "South Africa",
    "New Zealand", "West Indies", "Sri Lanka", "Afghanistan", "Bangladesh"
]

def extract_query_parameters(prompt: str, context: Optional[Dict[str, Any]] = None):
    lower = prompt.lower()

    # Identify players
    matched_players = []
    for key in sorted(PLAYER_MAP.keys(), key=len, reverse=True):
        pattern = r"\b" + re.escape(key) + r"\b"
        if re.search(pattern, lower):
            cricsheet_name, canonical_name = PLAYER_MAP[key]
            if (cricsheet_name, canonical_name) not in matched_players:
                matched_players.append((cricsheet_name, canonical_name))

    # Inherit from context if not specified
    if not matched_players and context and "players" in context:
        for p in context["players"]:
            for k, val in PLAYER_MAP.items():
                if val[1].lower() == p.lower():
                    matched_players.append(val)
                    break

    # Format
    detected_format = None
    if re.search(r"\bt20\b|\bit20\b|\bt20i\b|\bt20s\b", lower):
        detected_format = "T20"
    elif re.search(r"\bodi\b|\bodis\b|\bone day\b", lower):
        detected_format = "ODI"
    elif re.search(r"\btest\b|\btests\b", lower):
        detected_format = "Test"
    elif context and context.get("format"):
        detected_format = context["format"]

    # Opponent
    detected_opponent = None
    for team in TEAMS:
        if re.search(r"\b" + re.escape(team.lower()) + r"\b", lower):
            detected_opponent = team
            break
    if not detected_opponent and context and context.get("opponent"):
        detected_opponent = context["opponent"]

    # Recent N
    recent_n = None
    last_n_match = re.search(r"\blast\s+(\d+)\b", lower)
    if last_n_match:
        recent_n = int(last_n_match.group(1))

    return {
        "matched_players": matched_players,
        "format": detected_format,
        "opponent": detected_opponent,
        "recent_n": recent_n,
    }

def get_player_innings_data(cricsheet_name: str, match_type: Optional[str] = None, opponent: Optional[str] = None, recent_n: Optional[int] = None) -> pd.DataFrame:
    sql = """
        SELECT 
            m.match_id, 
            m.date, 
            m.match_type,
            d.batting_team, 
            d.bowling_team,
            SUM(d.batter_runs) as runs,
            COUNT(*) as balls,
            SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
            MAX(CASE WHEN d.is_wicket AND d.player_dismissed = ? THEN 1 ELSE 0 END) as is_out
        FROM deliveries d
        JOIN matches m ON d.match_id = m.match_id
        WHERE d.batter = ?
    """
    params = [cricsheet_name, cricsheet_name]

    if match_type:
        sql += " AND m.match_type = ?"
        params.append(match_type)

    if opponent:
        sql += " AND (m.team_1 = ? OR m.team_2 = ?) AND d.bowling_team = ?"
        params.extend([opponent, opponent, opponent])

    sql += """
        GROUP BY m.match_id, m.date, m.match_type, d.batting_team, d.bowling_team
        ORDER BY m.date ASC
    """

    df = execute_query(sql, params)
    if recent_n and len(df) > recent_n:
        df = df.tail(recent_n).reset_index(drop=True)
    return df

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
    params = extract_query_parameters(req.prompt, req.context)
    matched_players = params["matched_players"]
    match_type = params["format"]
    opponent = params["opponent"]
    recent_n = params["recent_n"]

    if not matched_players:
        matched_players = [("V Kohli", "Virat Kohli")]

    is_comparison = len(matched_players) > 1

    if not is_comparison:
        cricsheet_name, canonical_name = matched_players[0]
        df = get_player_innings_data(cricsheet_name, match_type, opponent, recent_n)

        if df.empty and (match_type or opponent):
            df = get_player_innings_data(cricsheet_name, match_type=None, opponent=None, recent_n=recent_n)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No innings found for {canonical_name} with current filters.")

        total_runs = int(df["runs"].sum())
        total_balls = int(df["balls"].sum())
        innings_count = len(df)
        dismissals = int(df["is_out"].sum())
        batting_avg = round(total_runs / max(1, dismissals), 2)
        strike_rate = round((total_runs / max(1, total_balls)) * 100, 1)
        high_score = int(df["runs"].max())
        high_score_idx = df["runs"].idxmax()
        high_score_not_out = bool(df.loc[high_score_idx, "is_out"] == 0)
        std_dev = round(float(df["runs"].std()), 1) if innings_count > 1 else 0.0
        fours = int(df["fours"].sum())
        sixes = int(df["sixes"].sum())
        centuries = int((df["runs"] >= 100).sum())
        fifties = int(((df["runs"] >= 50) & (df["runs"] < 100)).sum())

        consistency = "High consistency" if std_dev < 25 else "Moderate spread" if std_dev < 40 else "High variance"

        stats = {
            "total_runs": total_runs,
            "batting_average": batting_avg,
            "strike_rate": strike_rate,
            "high_score": high_score,
            "high_score_not_out": high_score_not_out,
            "innings_count": innings_count,
            "dismissals": dismissals,
            "balls_faced": total_balls,
            "std_deviation": std_dev,
            "consistency_rating": consistency,
            "fours": fours,
            "sixes": sixes,
            "boundary_runs": (fours * 4) + (sixes * 6),
            "centuries": centuries,
            "fifties": fifties,
        }

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

        insight = (
            f"Across {innings_count} innings{f' against {opponent}' if opponent else ''}"
            f"{f' in {match_type} cricket' if match_type else ''}, "
            f"{canonical_name} accumulated {total_runs:,} runs with a batting average of {batting_avg} "
            f"and a strike rate of {strike_rate}. His highest score was {high_score}{'*' if high_score_not_out else ''}, "
            f"with {centuries} century and {fifties} half-centuries. "
            f"Standard deviation of {std_dev} indicates {consistency.lower()}."
        )

        observations = [
            f"Scored {total_runs:,} runs off {total_balls:,} balls ({strike_rate} SR).",
            f"Converted {centuries + fifties} innings into 50+ scores ({((centuries + fifties) / innings_count * 100):.0f}% conversion rate).",
            f"Boundary contribution: {fours} fours and {sixes} sixes ({((stats['boundary_runs'] / max(1, total_runs)) * 100):.0f}% of runs).",
            f"Dismissed in {dismissals} of {innings_count} innings ({(innings_count - dismissals)} not outs).",
        ]

        title = f"{canonical_name} Innings Progression"
        if opponent:
            title += f" vs {opponent}"
        if match_type:
            title += f" ({match_type})"

        chart = {
            "chart_type": "line",
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

    else:
        # Comparison between players
        series_data = []
        combined_obs = []
        p_stats = {}

        for c_name, can_name in matched_players:
            df = get_player_innings_data(c_name, match_type, opponent, recent_n)
            t_runs = int(df["runs"].sum()) if not df.empty else 0
            t_balls = int(df["balls"].sum()) if not df.empty else 0
            d_count = int(df["is_out"].sum()) if not df.empty else 0
            b_avg = round(t_runs / max(1, d_count), 2) if not df.empty else 0
            sr = round((t_runs / max(1, t_balls)) * 100, 1) if not df.empty else 0

            p_stats[can_name] = {
                "runs": t_runs,
                "avg": b_avg,
                "sr": sr,
                "innings": len(df),
            }

            combined_obs.append(
                f"{can_name}: {t_runs:,} runs in {len(df)} inns, Avg: {b_avg}, SR: {sr}"
            )

            series_data.append({
                "name": can_name,
                "data": [
                    {"x": "Avg", "y": b_avg},
                    {"x": "Strike Rate / 2", "y": round(sr / 2, 1)},
                    {"x": "Innings", "y": len(df)},
                ]
            })

        p1, p2 = matched_players[0][1], matched_players[1][1]
        insight = (
            f"Comparing {p1} and {p2}{f' in {match_type}' if match_type else ''}: "
            f"{p1} has {p_stats[p1]['runs']:,} runs (avg {p_stats[p1]['avg']}, SR {p_stats[p1]['sr']}) "
            f"across {p_stats[p1]['innings']} innings, while {p2} has {p_stats[p2]['runs']:,} runs "
            f"(avg {p_stats[p2]['avg']}, SR {p_stats[p2]['sr']}) across {p_stats[p2]['innings']} innings."
        )

        stats = {
            "total_runs": p_stats[p1]["runs"],
            "batting_average": p_stats[p1]["avg"],
            "strike_rate": p_stats[p1]["sr"],
            "innings_count": p_stats[p1]["innings"],
            "consistency_rating": f"Vs {p2}",
            "boundary_runs": 0,
        }

        chart = {
            "chart_type": "bar",
            "title": f"Comparison: {p1} vs {p2}",
            "subtitle": f"{match_type or 'All Formats'} metric comparison",
            "x_axis_label": "Metric",
            "y_axis_label": "Value",
            "series": series_data,
        }

        scope = {
            "players": [p[1] for p in matched_players],
            "opponent": opponent,
            "format": match_type or "All formats",
            "date_range": "Available career matches",
            "analysis_type": "Player Head-to-Head Comparison",
        }
        observations = combined_obs

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
