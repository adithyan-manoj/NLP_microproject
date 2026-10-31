"""
Deterministic Cricket Statistical Formulas.
Implements official ICC scoring conventions:
- Batting Average (with not-out handling)
- Batting Strike Rate (balls faced excludes wides, includes no-balls)
- Bowling Wickets (bowler-credited only, excludes run-outs)
- Bowling Economy Rate (runs conceded per legal 6-ball over)
- Consistency (Standard Deviation, Median, IQR)
- Rolling Averages & Form Progression
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

def calculate_batting_metrics(
    df_innings: pd.DataFrame,
    player_name: str,
    matches_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Computes deterministic batting metrics from an innings-aggregated DataFrame.
    Expected columns: ['match_id', 'date', 'runs', 'balls_faced', 'fours', 'sixes', 'is_out', 'opponent', 'venue', 'format']
    """
    if df_innings.empty:
        return {
            "player_name": player_name,
            "matches": matches_count or 0,
            "innings": 0,
            "innings_count": 0,
            "total_runs": 0,
            "runs": 0,
            "balls_faced": 0,
            "dismissals": 0,
            "not_outs": 0,
            "batting_average": None,
            "strike_rate": 0.0,
            "high_score": 0,
            "high_score_not_out": False,
            "fours": 0,
            "sixes": 0,
            "boundary_runs": 0,
            "boundary_percentage": 0.0,
            "centuries": 0,
            "hundreds": 0,
            "fifties": 0,
            "std_deviation": 0.0,
            "median_score": 0.0,
            "sample_size_adequate": False,
        }

    total_runs = int(df_innings["runs"].sum())
    total_balls = int(df_innings["balls_faced"].sum())
    innings_count = len(df_innings)
    
    # Dismissal counting (not-out handling)
    dismissals = int(df_innings["is_out"].sum()) if "is_out" in df_innings.columns else innings_count
    not_outs = innings_count - dismissals

    # Batting Average: runs / dismissals. If 0 dismissals, average is undefined (return None)
    if dismissals > 0:
        batting_average = round(float(total_runs / dismissals), 2)
    else:
        batting_average = None  # Undefined (infinite/not dismissed)

    # Batting Strike Rate: (runs / balls_faced) * 100
    if total_balls > 0:
        strike_rate = round(float((total_runs / total_balls) * 100), 2)
    else:
        strike_rate = 0.0

    # High score
    max_idx = df_innings["runs"].idxmax()
    high_score = int(df_innings.loc[max_idx, "runs"])
    high_score_not_out = not bool(df_innings.loc[max_idx, "is_out"]) if "is_out" in df_innings.columns else False

    # Boundaries
    fours = int(df_innings["fours"].sum()) if "fours" in df_innings.columns else 0
    sixes = int(df_innings["sixes"].sum()) if "sixes" in df_innings.columns else 0
    boundary_runs = (fours * 4) + (sixes * 6)
    boundary_pct = round(float((boundary_runs / max(1, total_runs)) * 100), 1) if total_runs > 0 else 0.0

    # Milestones
    centuries = int((df_innings["runs"] >= 100).sum())
    fifties = int(((df_innings["runs"] >= 50) & (df_innings["runs"] < 100)).sum())

    # Consistency metrics
    scores = df_innings["runs"].tolist()
    std_dev = round(float(np.std(scores, ddof=1)), 2) if len(scores) > 1 else 0.0
    median_score = round(float(np.median(scores)), 1)
    
    # Rolling averages
    rolling_last_3 = round(float(np.mean(scores[-3:])), 2) if len(scores) >= 3 else round(float(np.mean(scores)), 2)
    rolling_last_5 = round(float(np.mean(scores[-5:])), 2) if len(scores) >= 5 else round(float(np.mean(scores)), 2)

    unique_matches = len(df_innings["match_id"].unique()) if "match_id" in df_innings.columns else innings_count
    final_matches = matches_count if (matches_count is not None and matches_count > 0) else unique_matches

    return {
        "player_name": player_name,
        "matches": final_matches,
        "innings": innings_count,
        "innings_count": innings_count,
        "total_runs": total_runs,
        "runs": total_runs,
        "balls_faced": total_balls,
        "dismissals": dismissals,
        "not_outs": not_outs,
        "batting_average": batting_average,
        "strike_rate": strike_rate,
        "high_score": high_score,
        "high_score_not_out": high_score_not_out,
        "fours": fours,
        "sixes": sixes,
        "boundary_runs": boundary_runs,
        "boundary_percentage": boundary_pct,
        "centuries": centuries,
        "hundreds": centuries,
        "fifties": fifties,
        "std_deviation": std_dev,
        "median_score": median_score,
        "rolling_avg_last_3": rolling_last_3,
        "rolling_avg_last_5": rolling_last_5,
        "sample_size_adequate": innings_count >= 5,
    }

def calculate_bowling_metrics(df_spells: pd.DataFrame, player_name: str) -> Dict[str, Any]:
    """
    Computes deterministic bowling metrics from match bowling spell records.
    Expected columns: ['legal_balls', 'runs_conceded', 'wickets', 'dots', 'fours', 'sixes']
    """
    if df_spells.empty:
        return {
            "player_name": player_name,
            "spells_count": 0,
            "total_legal_balls": 0,
            "overs_bowled_display": "0.0",
            "overs_bowled_exact": 0.0,
            "runs_conceded": 0,
            "wickets": 0,
            "economy_rate": 0.0,
            "bowling_average": None,
            "bowling_strike_rate": None,
        }

    total_legal_balls = int(df_spells["legal_balls"].sum())
    runs_conceded = int(df_spells["runs_conceded"].sum())
    wickets = int(df_spells["wickets"].sum())
    spells_count = len(df_spells)

    # Overs calculation
    completed_overs = total_legal_balls // 6
    remaining_balls = total_legal_balls % 6
    overs_display = f"{completed_overs}.{remaining_balls}"
    overs_exact = round(total_legal_balls / 6.0, 4)

    # Economy rate: runs / (legal_balls / 6)
    if total_legal_balls > 0:
        economy_rate = round(float(runs_conceded / (total_legal_balls / 6.0)), 2)
    else:
        economy_rate = 0.0

    # Bowling Average: runs / wickets
    bowling_average = round(float(runs_conceded / wickets), 2) if wickets > 0 else None

    # Bowling Strike Rate: legal_balls / wickets
    bowling_sr = round(float(total_legal_balls / wickets), 2) if wickets > 0 else None

    return {
        "player_name": player_name,
        "spells_count": spells_count,
        "total_legal_balls": total_legal_balls,
        "overs_bowled_display": overs_display,
        "overs_bowled_exact": overs_exact,
        "runs_conceded": runs_conceded,
        "wickets": wickets,
        "economy_rate": economy_rate,
        "bowling_average": bowling_average,
        "bowling_strike_rate": bowling_sr,
        "sample_size_adequate": spells_count >= 5,
    }
