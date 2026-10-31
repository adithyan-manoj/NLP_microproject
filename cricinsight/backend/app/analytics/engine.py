"""
Cricket Analytics Engine.
Queries structured Cricsheet records with parameterized filters,
aggregates ball-by-ball deliveries into chronological innings & spells,
and calculates deterministic batting, bowling, opponent, and venue performance.
"""

from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
from app.database.db import execute_query
from app.analytics.cricket_metrics import calculate_batting_metrics, calculate_bowling_metrics

def get_candidate_player_names(player_name: str) -> List[str]:
    """Retrieves all aliases for a player name or initials to guarantee delivery matching."""
    names = set([player_name])
    try:
        alias_df = execute_query("""
            SELECT a.alias, p.canonical_name 
            FROM player_aliases a
            JOIN players p ON a.player_id = p.id
            WHERE p.canonical_name = ? 
               OR a.normalized_alias = LOWER(?)
               OR a.player_id = (SELECT player_id FROM player_aliases WHERE normalized_alias = LOWER(?) LIMIT 1);
        """, [player_name, player_name, player_name])
        if not alias_df.empty:
            names.update(alias_df["alias"].dropna().tolist())
            names.update(alias_df["canonical_name"].dropna().tolist())
    except Exception:
        pass
    return list(names)

def get_player_match_count(
    player_name: str,
    match_type: Optional[str] = None,
    competition: Optional[str] = None,
    season: Optional[str] = None,
    opponent: Optional[str] = None,
    venue: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> int:
    """Calculates distinct matches played across deliveries and scorecards."""
    names = get_candidate_player_names(player_name)
    placeholders = ", ".join(["?"] * len(names))
    sql = f"""
        SELECT COUNT(DISTINCT d.match_id) as cnt
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        WHERE (d.batter_name IN ({placeholders}) OR d.bowler_name IN ({placeholders}) OR d.non_striker_name IN ({placeholders}))
    """
    params: List[Any] = names + names + names
    if match_type:
        sql += " AND m.match_type = ?"
        params.append(match_type)
    if competition:
        if competition.upper() == "IPL":
            sql += " AND (m.competition = 'IPL' OR LOWER(m.competition) LIKE '%indian premier league%' OR m.match_type = 'T20')"
        else:
            sql += " AND (m.competition = ? OR LOWER(m.competition) LIKE ?)"
            params.extend([competition, f"%{competition.lower()}%"])
    if season:
        sql += " AND (m.season = ? OR m.season LIKE ? OR strftime(m.start_date, '%Y') = ?)"
        params.extend([str(season), f"%{season}%", str(season)])
    if opponent:
        sql += " AND (d.match_id IN (SELECT match_id FROM innings WHERE bowling_team = ? OR batting_team = ?))"
        params.extend([opponent, opponent])
    if venue:
        sql += " AND m.venue = ?"
        params.append(venue)
    if start_date:
        sql += " AND m.start_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND m.start_date <= ?"
        params.append(end_date)

    match_count = 0
    try:
        res = execute_query(sql, params)
        if not res.empty:
            match_count = int(res.iloc[0]["cnt"])
    except Exception:
        pass

    # Also count matches in match_scorecards not already counted
    try:
        sc_sql = f"""
            SELECT COUNT(DISTINCT match_id) as cnt
            FROM match_scorecards
            WHERE (player_name IN ({placeholders}) OR player_id IN ({placeholders}))
        """
        sc_params: List[Any] = names + names
        if match_type:
            sc_sql += " AND match_type = ?"
            sc_params.append(match_type)
        if competition:
            if competition.upper() == "IPL":
                sc_sql += " AND (competition = 'IPL' OR LOWER(competition) LIKE '%indian premier league%' OR match_type = 'T20')"
            else:
                sc_sql += " AND (competition = ? OR LOWER(competition) LIKE ?)"
                sc_params.extend([competition, f"%{competition.lower()}%"])
        if season:
            sc_sql += " AND (season = ? OR season LIKE ? OR strftime(match_date, '%Y') = ?)"
            sc_params.extend([str(season), f"%{season}%", str(season)])
        if opponent:
            sc_sql += " AND opponent = ?"
            sc_params.append(opponent)
        if venue:
            sc_sql += " AND venue = ?"
            sc_params.append(venue)
        if start_date:
            sc_sql += " AND match_date >= ?"
            sc_params.append(start_date)
        if end_date:
            sc_sql += " AND match_date <= ?"
            sc_params.append(end_date)
        sc_res = execute_query(sc_sql, sc_params)
        if not sc_res.empty:
            match_count += int(sc_res.iloc[0]["cnt"])
    except Exception:
        pass

    return match_count

def get_player_innings_history(
    player_name: str,
    match_type: Optional[str] = None,
    competition: Optional[str] = None,
    season: Optional[str] = None,
    opponent: Optional[str] = None,
    venue: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    last_n_innings: Optional[int] = None,
    last_n_matches: Optional[int] = None,
) -> pd.DataFrame:
    """
    Retrieves chronological batting innings for a player with allowlisted filters.
    Groups ball-by-ball deliveries by (match_id, innings_number) and unifies with match_scorecards.
    """
    names = get_candidate_player_names(player_name)
    placeholders = ", ".join(["?"] * len(names))

    sql = f"""
        SELECT
            d.match_id,
            d.innings_id,
            m.start_date,
            m.match_type,
            m.venue,
            inn.bowling_team as opponent,
            SUM(d.batter_runs) as runs,
            SUM(CASE WHEN d.is_ball_faced THEN 1 ELSE 0 END) as balls_faced,
            SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
            MAX(CASE WHEN d.is_wicket AND d.player_dismissed IN ({placeholders}) THEN 1 ELSE 0 END) as is_out
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        JOIN innings inn ON d.match_id = inn.match_id AND d.innings_id = inn.innings_number
        WHERE d.batter_name IN ({placeholders})
    """
    params: List[Any] = names + names

    if match_type:
        sql += " AND m.match_type = ?"
        params.append(match_type)
    if competition:
        if competition.upper() == "IPL":
            sql += " AND (m.competition = 'IPL' OR LOWER(m.competition) LIKE '%indian premier league%' OR m.match_type = 'T20')"
        else:
            sql += " AND (m.competition = ? OR LOWER(m.competition) LIKE ?)"
            params.extend([competition, f"%{competition.lower()}%"])
    if season:
        sql += " AND (m.season = ? OR m.season LIKE ? OR strftime(m.start_date, '%Y') = ?)"
        params.extend([str(season), f"%{season}%", str(season)])
    if opponent:
        sql += " AND inn.bowling_team = ?"
        params.append(opponent)
    if venue:
        sql += " AND m.venue = ?"
        params.append(venue)
    if start_date:
        sql += " AND m.start_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND m.start_date <= ?"
        params.append(end_date)

    sql += " GROUP BY d.match_id, d.innings_id, m.start_date, m.match_type, m.venue, inn.bowling_team"
    sql += " ORDER BY m.start_date ASC, d.innings_id ASC"

    if last_n_matches:
        subquery = f"""
            SELECT DISTINCT id FROM matches m
            JOIN deliveries d ON m.id = d.match_id
            WHERE d.batter_name IN ({placeholders})
            ORDER BY m.start_date DESC
            LIMIT ?
        """
        match_ids_df = execute_query(subquery, names + [last_n_matches])
        if not match_ids_df.empty:
            match_ids = match_ids_df["id"].tolist()
            m_placeholders = ", ".join(["?"] * len(match_ids))
            sql += f" HAVING d.match_id IN ({m_placeholders})"
            params.extend(match_ids)

    df = execute_query(sql, params)

    # Union with Tier 2 match_scorecards if available
    try:
        existing_matches = set(df["match_id"].dropna().tolist()) if not df.empty else set()
        sc_sql = f"""
            SELECT
                match_id,
                innings_number as innings_id,
                match_date as start_date,
                match_type,
                venue,
                opponent,
                runs,
                balls_faced,
                fours,
                sixes,
                CASE WHEN is_out THEN 1 ELSE 0 END as is_out
            FROM match_scorecards
            WHERE (player_name IN ({placeholders}) OR player_id IN ({placeholders}))
        """
        sc_params: List[Any] = names + names
        if match_type:
            sc_sql += " AND match_type = ?"
            sc_params.append(match_type)
        if competition:
            if competition.upper() == "IPL":
                sc_sql += " AND (competition = 'IPL' OR LOWER(competition) LIKE '%indian premier league%' OR match_type = 'T20')"
            else:
                sc_sql += " AND (competition = ? OR LOWER(competition) LIKE ?)"
                sc_params.extend([competition, f"%{competition.lower()}%"])
        if season:
            sc_sql += " AND (season = ? OR season LIKE ? OR strftime(match_date, '%Y') = ?)"
            sc_params.extend([str(season), f"%{season}%", str(season)])
        if opponent:
            sc_sql += " AND opponent = ?"
            sc_params.append(opponent)
        if venue:
            sc_sql += " AND venue = ?"
            sc_params.append(venue)
        if start_date:
            sc_sql += " AND match_date >= ?"
            sc_params.append(start_date)
        if end_date:
            sc_sql += " AND match_date <= ?"
            sc_params.append(end_date)

        sc_df = execute_query(sc_sql, sc_params)
        if not sc_df.empty:
            sc_df = sc_df[~sc_df["match_id"].isin(existing_matches)]
            if not sc_df.empty:
                df = pd.concat([df, sc_df], ignore_index=True) if not df.empty else sc_df
    except Exception:
        pass

    if last_n_innings and not df.empty and len(df) > last_n_innings:
        df = df.tail(last_n_innings).reset_index(drop=True)

    return df

def get_player_bowling_history(
    player_name: str,
    match_type: Optional[str] = None,
    opponent: Optional[str] = None,
    venue: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    last_n_spells: Optional[int] = None,
) -> pd.DataFrame:
    """
    Retrieves chronological bowling spells for a player with allowlisted filters.
    """
    names = get_candidate_player_names(player_name)
    placeholders = ", ".join(["?"] * len(names))

    sql = f"""
        SELECT
            d.match_id,
            d.innings_id,
            m.start_date,
            m.match_type,
            m.venue,
            inn.batting_team as opponent,
            SUM(CASE WHEN d.is_legal_ball THEN 1 ELSE 0 END) as legal_balls,
            SUM(d.bowler_conceded_runs) as runs_conceded,
            SUM(CASE WHEN d.bowler_credited_wicket THEN 1 ELSE 0 END) as wickets,
            SUM(CASE WHEN d.total_runs = 0 AND d.is_legal_ball THEN 1 ELSE 0 END) as dots,
            SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        JOIN innings inn ON d.match_id = inn.match_id AND d.innings_id = inn.innings_number
        WHERE d.bowler_name IN ({placeholders})
    """
    params: List[Any] = names

    if match_type:
        sql += " AND m.match_type = ?"
        params.append(match_type)
    if opponent:
        sql += " AND inn.batting_team = ?"
        params.append(opponent)
    if venue:
        sql += " AND m.venue = ?"
        params.append(venue)
    if start_date:
        sql += " AND m.start_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND m.start_date <= ?"
        params.append(end_date)

    sql += " GROUP BY d.match_id, d.innings_id, m.start_date, m.match_type, m.venue, inn.batting_team"
    sql += " ORDER BY m.start_date ASC, d.innings_id ASC"

    df = execute_query(sql, params)

    if last_n_spells and not df.empty and len(df) > last_n_spells:
        df = df.tail(last_n_spells).reset_index(drop=True)

    return df

def analyze_player_batting(
    player_name: str,
    match_type: Optional[str] = None,
    competition: Optional[str] = None,
    season: Optional[str] = None,
    opponent: Optional[str] = None,
    venue: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    last_n_innings: Optional[int] = None,
    last_n_matches: Optional[int] = None,
) -> Dict[str, Any]:
    """Generates complete batting performance analysis for a player."""
    df_innings = get_player_innings_history(
        player_name=player_name,
        match_type=match_type,
        competition=competition,
        season=season,
        opponent=opponent,
        venue=venue,
        start_date=start_date,
        end_date=end_date,
        last_n_innings=last_n_innings,
        last_n_matches=last_n_matches,
    )

    matches_count = get_player_match_count(
        player_name=player_name,
        match_type=match_type,
        competition=competition,
        season=season,
        opponent=opponent,
        venue=venue,
        start_date=start_date,
        end_date=end_date,
    )

    metrics = calculate_batting_metrics(df_innings, player_name, matches_count=matches_count)

    # Chronological progression for chart series
    progression = []
    if not df_innings.empty:
        for i, row in df_innings.iterrows():
            progression.append({
                "innings_number": i + 1,
                "runs": int(row["runs"]),
                "balls": int(row["balls_faced"]),
                "date": str(row["start_date"]),
                "opponent": str(row["opponent"]),
                "venue": str(row["venue"]),
                "is_out": bool(row["is_out"]),
            })

    match_ids = df_innings["match_id"].dropna().unique().tolist() if ("match_id" in df_innings.columns and not df_innings.empty) else []

    return {
        "metrics": metrics,
        "progression": progression,
        "raw_innings_count": len(df_innings),
        "matches_count": metrics.get("matches", matches_count),
        "match_ids": match_ids,
        "granularity": "ball_by_ball" if not df_innings.empty else "match_scorecard",
    }

def compare_players(
    players: List[str],
    match_type: Optional[str] = None,
    opponent: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    last_n_innings: Optional[int] = None,
) -> Dict[str, Any]:
    """Computes head-to-head comparison metrics across multiple players."""
    comparison_table = []
    for p in players:
        analysis = analyze_player_batting(
            player_name=p,
            match_type=match_type,
            opponent=opponent,
            start_date=start_date,
            end_date=end_date,
            last_n_innings=last_n_innings,
        )
        m = analysis["metrics"]
        comparison_table.append({
            "player": p,
            "innings": m["innings_count"],
            "runs": m["total_runs"],
            "average": m["batting_average"],
            "strike_rate": m["strike_rate"],
            "centuries": m["centuries"],
            "fifties": m["fifties"],
            "consistency_std_dev": m["std_deviation"],
            "boundary_pct": m["boundary_percentage"],
            "high_score": m["high_score"],
        })

    return {
        "players": players,
        "comparison": comparison_table,
        "scope": {
            "format": match_type or "All formats",
            "opponent": opponent or "All opponents",
            "start_date": start_date,
            "end_date": end_date,
            "last_n_innings": last_n_innings,
        }
    }
