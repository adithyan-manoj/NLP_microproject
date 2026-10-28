"""
Cricket Data Service - DuckDB Analytical and Statistical Engine.
Handles parameterized queries, OLAP aggregations, rolling metrics, and statistical measures.
"""
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from app.database.db import execute_query

def resolve_player_identity(name_query: str) -> Optional[Tuple[str, str]]:
    """
    Resolves a player input (e.g., 'Kohli', 'rohit', 'babar azam') to:
    (cricsheet_name, canonical_name).
    Uses database lookups and built-in canonical aliases.
    """
    clean_q = name_query.strip().lower()

    # Pre-indexed high-frequency mapping
    FAST_MAP = {
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
        "buttler": ("JC Buttler", "Jos Buttler"),
        "jos buttler": ("JC Buttler", "Jos Buttler"),
        "root": ("JE Root", "Joe Root"),
        "joe root": ("JE Root", "Joe Root"),
        "bumrah": ("JJ Bumrah", "Jasprit Bumrah"),
        "jasprit bumrah": ("JJ Bumrah", "Jasprit Bumrah"),
        "williamson": ("KS Williamson", "Kane Williamson"),
        "kane williamson": ("KS Williamson", "Kane Williamson"),
        "dhoni": ("MS Dhoni", "MS Dhoni"),
        "ms dhoni": ("MS Dhoni", "MS Dhoni"),
        "head": ("TM Head", "Travis Head"),
        "travis head": ("TM Head", "Travis Head"),
        "gill": ("Shubman Gill", "Shubman Gill"),
        "shubman gill": ("Shubman Gill", "Shubman Gill"),
        "rahul": ("KL Rahul", "KL Rahul"),
        "kl rahul": ("KL Rahul", "KL Rahul"),
        "rizwan": ("Mohammad Rizwan", "Mohammad Rizwan"),
        "mohammad rizwan": ("Mohammad Rizwan", "Mohammad Rizwan"),
        "starc": ("MA Starc", "Mitchell Starc"),
        "cummins": ("PJ Cummins", "Pat Cummins"),
        "shami": ("Mohammed Shami", "Mohammed Shami"),
        "maxwell": ("GJ Maxwell", "Glenn Maxwell"),
        "de kock": ("Q de Kock", "Quinton de Kock"),
        "quinton de kock": ("Q de Kock", "Quinton de Kock"),
        "mendis": ("BKG Mendis", "Kusal Mendis"),
        "kusal mendis": ("BKG Mendis", "Kusal Mendis"),
        "hope": ("SD Hope", "Shai Hope"),
        "shai hope": ("SD Hope", "Shai Hope"),
        "finch": ("AJ Finch", "Aaron Finch"),
        "aaron finch": ("AJ Finch", "Aaron Finch"),
    }

    if clean_q in FAST_MAP:
        return FAST_MAP[clean_q]

    # Database fallback query
    sql = """
        SELECT canonical_name, aliases 
        FROM players 
        WHERE LOWER(canonical_name) LIKE ? OR LOWER(aliases) LIKE ?
        LIMIT 1
    """
    df = execute_query(sql, [f"%{clean_q}%", f"%{clean_q}%"])
    if not df.empty:
        canon = df.iloc[0]["canonical_name"]
        # Match against deliveries table to get exact batter code
        match_df = execute_query(
            "SELECT batter FROM deliveries WHERE LOWER(batter) = ? OR LOWER(batter) LIKE ? LIMIT 1",
            [clean_q, f"%{clean_q}%"]
        )
        if not match_df.empty:
            return match_df.iloc[0]["batter"], canon
        return canon, canon

    return None

def query_player_innings(
    cricsheet_name: str,
    match_type: Optional[str] = None,
    opponent: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    recent_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Retrieve chronological ball-by-ball aggregated innings records for a batter from DuckDB.
    Guarantees parameterized SQL injection protection.
    """
    sql = """
        SELECT 
            m.match_id, 
            m.date, 
            m.match_type,
            m.venue,
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
    params: List[Any] = [cricsheet_name, cricsheet_name]

    if match_type:
        sql += " AND UPPER(m.match_type) = UPPER(?)"
        params.append(match_type)

    if opponent:
        sql += " AND (UPPER(m.team_1) = UPPER(?) OR UPPER(m.team_2) = UPPER(?)) AND UPPER(d.bowling_team) = UPPER(?)"
        params.extend([opponent, opponent, opponent])

    if start_date:
        sql += " AND m.date >= CAST(? AS DATE)"
        params.append(start_date)

    if end_date:
        sql += " AND m.date <= CAST(? AS DATE)"
        params.append(end_date)

    sql += """
        GROUP BY m.match_id, m.date, m.match_type, m.venue, d.batting_team, d.bowling_team
        ORDER BY m.date ASC
    """

    df = execute_query(sql, params)

    if recent_n and len(df) > recent_n:
        df = df.tail(recent_n).reset_index(drop=True)

    return df

def calculate_statistical_metrics(df: pd.DataFrame, canonical_name: str) -> Dict[str, Any]:
    """
    Computes rigorous cricket statistical metrics directly from the aggregated innings DataFrame.
    """
    if df.empty:
        return {
            "total_runs": 0,
            "batting_average": 0.0,
            "strike_rate": 0.0,
            "high_score": 0,
            "high_score_not_out": False,
            "innings_count": 0,
            "dismissals": 0,
            "balls_faced": 0,
            "std_deviation": 0.0,
            "consistency_rating": "No Data",
            "fours": 0,
            "sixes": 0,
            "boundary_runs": 0,
            "centuries": 0,
            "fifties": 0,
            "rolling_avg_last_5": 0.0,
        }

    total_runs = int(df["runs"].sum())
    total_balls = int(df["balls"].sum())
    innings_count = len(df)
    dismissals = int(df["is_out"].sum())

    # Batting average: runs / outs (if never dismissed, runs / 1)
    batting_avg = round(total_runs / max(1, dismissals), 2)
    strike_rate = round((total_runs / max(1, total_balls)) * 100, 1)

    high_score = int(df["runs"].max())
    high_score_idx = df["runs"].idxmax()
    high_score_not_out = bool(df.loc[high_score_idx, "is_out"] == 0)

    # Standard deviation for scoring dispersion / consistency
    std_dev = round(float(df["runs"].std()), 1) if innings_count > 1 else 0.0
    if std_dev == 0.0:
        consistency = "Single sample"
    elif std_dev < 25:
        consistency = "High consistency"
    elif std_dev < 42:
        consistency = "Moderate spread"
    else:
        consistency = "High variance"

    fours = int(df["fours"].sum())
    sixes = int(df["sixes"].sum())
    boundary_runs = (fours * 4) + (sixes * 6)
    centuries = int((df["runs"] >= 100).sum())
    fifties = int(((df["runs"] >= 50) & (df["runs"] < 100)).sum())

    # Rolling average of last 5 innings
    rolling_last_5 = round(float(df["runs"].tail(5).mean()), 1) if innings_count > 0 else 0.0

    return {
        "player_name": canonical_name,
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
        "boundary_runs": boundary_runs,
        "centuries": centuries,
        "fifties": fifties,
        "rolling_avg_last_5": rolling_last_5,
    }

