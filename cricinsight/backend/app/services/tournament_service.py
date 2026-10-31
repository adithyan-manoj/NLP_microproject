"""
Tournament Service for CricInsight.
Manages grassroots and local cricket tournaments, team rosters, match scorecards,
live ball-by-ball scoring, dynamic Points Table calculation (with exact NRR),
and Orange/Purple Cap leaderboards.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from app.database.db import execute_query, execute_statement

logger = logging.getLogger("cricinsight.tournaments")

class TournamentService:
    @staticmethod
    def create_tournament(
        name: str,
        season: str = "2026",
        format: str = "T20",
        overs_limit: int = 20,
    ) -> Dict[str, Any]:
        """Creates a new local cricket tournament."""
        tournament_id = f"tour_{uuid.uuid4().hex[:8]}"
        execute_statement("""
            INSERT INTO tournaments (id, name, season, format, overs_limit, status)
            VALUES (?, ?, ?, ?, ?, ?);
        """, [tournament_id, name, season, format, overs_limit, "ongoing"])

        return {
            "id": tournament_id,
            "name": name,
            "season": season,
            "format": format,
            "overs_limit": overs_limit,
            "status": "ongoing",
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def list_tournaments() -> List[Dict[str, Any]]:
        """Lists all local tournaments with team counts and match summaries."""
        df = execute_query("""
            SELECT t.id, t.name, t.season, t.format, t.overs_limit, t.status, t.created_at,
                   COUNT(DISTINCT tm.id) as team_count,
                   COUNT(DISTINCT m.id) as match_count
            FROM tournaments t
            LEFT JOIN tournament_teams tm ON t.id = tm.tournament_id
            LEFT JOIN tournament_matches m ON t.id = m.tournament_id
            GROUP BY t.id, t.name, t.season, t.format, t.overs_limit, t.status, t.created_at
            ORDER BY t.created_at DESC;
        """)
        return df.to_dict(orient="records") if not df.empty else []

    @staticmethod
    def get_tournament(tournament_id: str) -> Optional[Dict[str, Any]]:
        """Gets detailed tournament information including teams and match fixtures."""
        df = execute_query("SELECT * FROM tournaments WHERE id = ?;", [tournament_id])
        if df.empty:
            return None

        tour = df.iloc[0].to_dict()

        # Fetch teams
        df_teams = execute_query("""
            SELECT id, name, short_code, captain, color
            FROM tournament_teams
            WHERE tournament_id = ?
            ORDER BY name;
        """, [tournament_id])
        tour["teams"] = df_teams.to_dict(orient="records") if not df_teams.empty else []

        # Fetch matches
        df_matches = execute_query("""
            SELECT m.*,
                   t1.name as team1_name, t1.short_code as team1_code,
                   t2.name as team2_name, t2.short_code as team2_code,
                   tw.name as winner_name
            FROM tournament_matches m
            LEFT JOIN tournament_teams t1 ON m.team1_id = t1.id
            LEFT JOIN tournament_teams t2 ON m.team2_id = t2.id
            LEFT JOIN tournament_teams tw ON m.winner_team_id = tw.id
            WHERE m.tournament_id = ?
            ORDER BY m.match_date ASC, m.match_number ASC;
        """, [tournament_id])
        tour["matches"] = df_matches.to_dict(orient="records") if not df_matches.empty else []

        # Fetch standings
        tour["standings"] = TournamentService.get_standings(tournament_id)
        tour["leaderboard"] = TournamentService.get_leaderboard(tournament_id)

        return tour

    @staticmethod
    def add_team(
        tournament_id: str,
        name: str,
        short_code: str,
        captain: Optional[str] = None,
        color: str = "#10B981",
        players: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Registers a team and optional squad list into a tournament."""
        team_id = f"team_{uuid.uuid4().hex[:8]}"
        execute_statement("""
            INSERT INTO tournament_teams (id, tournament_id, name, short_code, captain, color)
            VALUES (?, ?, ?, ?, ?, ?);
        """, [team_id, tournament_id, name, short_code.upper(), captain or "", color])

        added_players = []
        if players:
            for p_name in players:
                if p_name.strip():
                    p_id = f"tp_{uuid.uuid4().hex[:8]}"
                    execute_statement("""
                        INSERT INTO tournament_players (id, tournament_id, team_id, name, role)
                        VALUES (?, ?, ?, ?, ?);
                    """, [p_id, tournament_id, team_id, p_name.strip(), "all_rounder"])
                    added_players.append({"id": p_id, "name": p_name.strip()})

        return {
            "id": team_id,
            "tournament_id": tournament_id,
            "name": name,
            "short_code": short_code.upper(),
            "captain": captain,
            "color": color,
            "players": added_players,
        }

    @staticmethod
    def create_match(
        tournament_id: str,
        team1_id: str,
        team2_id: str,
        venue: str = "Local Sports Ground",
        match_date: Optional[str] = None,
        match_number: int = 1,
    ) -> Dict[str, Any]:
        """Creates a scheduled or active match fixture between two teams."""
        match_id = f"tmatch_{uuid.uuid4().hex[:8]}"
        date_val = match_date or datetime.utcnow().strftime("%Y-%m-%d")

        execute_statement("""
            INSERT INTO tournament_matches (
                id, tournament_id, team1_id, team2_id, match_number, venue, match_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, [match_id, tournament_id, team1_id, team2_id, match_number, venue, date_val, "scheduled"])

        return {
            "id": match_id,
            "tournament_id": tournament_id,
            "team1_id": team1_id,
            "team2_id": team2_id,
            "match_number": match_number,
            "venue": venue,
            "match_date": date_val,
            "status": "scheduled",
        }

    @staticmethod
    def record_scorecard(
        match_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Summary Mode: Records post-match totals and individual batting/bowling figures.
        """
        # Fetch match info
        df_m = execute_query("SELECT tournament_id, team1_id, team2_id FROM tournament_matches WHERE id = ?;", [match_id])
        if df_m.empty:
            raise ValueError(f"Match {match_id} not found")

        tour_id = df_m.iloc[0]["tournament_id"]

        # Update Match Summary
        execute_statement("""
            UPDATE tournament_matches
            SET status = 'completed',
                toss_winner_id = ?,
                toss_decision = ?,
                winner_team_id = ?,
                margin = ?,
                innings1_runs = ?,
                innings1_wickets = ?,
                innings1_overs = ?,
                innings2_runs = ?,
                innings2_wickets = ?,
                innings2_overs = ?
            WHERE id = ?;
        """, [
            payload.get("toss_winner_id"),
            payload.get("toss_decision", "bat"),
            payload.get("winner_team_id"),
            payload.get("margin", ""),
            payload.get("innings1_runs", 0),
            payload.get("innings1_wickets", 0),
            payload.get("innings1_overs", 0.0),
            payload.get("innings2_runs", 0),
            payload.get("innings2_wickets", 0),
            payload.get("innings2_overs", 0.0),
            match_id
        ])

        # Delete previous scorecard rows if updating
        execute_statement("DELETE FROM tournament_scorecards WHERE match_id = ?;", [match_id])

        # Insert player scorecards
        scorecards = payload.get("scorecards", [])
        for sc in scorecards:
            execute_statement("""
                INSERT INTO tournament_scorecards (
                    match_id, tournament_id, team_id, player_name,
                    runs, balls, fours, sixes, overs_bowled, maidens, runs_conceded, wickets, is_out, dismissal_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, [
                match_id,
                tour_id,
                sc.get("team_id"),
                sc.get("player_name"),
                sc.get("runs", 0),
                sc.get("balls", 0),
                sc.get("fours", 0),
                sc.get("sixes", 0),
                sc.get("overs_bowled", 0.0),
                sc.get("maidens", 0),
                sc.get("runs_conceded", 0),
                sc.get("wickets", 0),
                sc.get("is_out", False),
                sc.get("dismissal_text", "not out" if not sc.get("is_out") else "out")
            ])

        return {"status": "success", "match_id": match_id, "scorecards_recorded": len(scorecards)}

    @staticmethod
    def record_live_ball(
        match_id: str,
        ball_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Live Ball-by-Ball Mode: Records an individual delivery, updates active striker/bowler,
        rotates strike on odd runs or over end, and updates match totals.
        """
        df_m = execute_query("SELECT tournament_id, innings1_runs, innings1_wickets, innings1_overs, innings2_runs, innings2_wickets, innings2_overs, status FROM tournament_matches WHERE id = ?;", [match_id])
        if df_m.empty:
            raise ValueError(f"Match {match_id} not found")

        tour_id = df_m.iloc[0]["tournament_id"]
        innings = int(ball_data.get("innings", 1))
        over_num = int(ball_data.get("over_num", 0))
        ball_num = int(ball_data.get("ball_num", 1))
        batter = ball_data.get("batter_name", "").strip()
        bowler = ball_data.get("bowler_name", "").strip()
        non_striker = ball_data.get("non_striker_name", "").strip()
        runs_batter = int(ball_data.get("runs_batter", 0))
        runs_extra = int(ball_data.get("runs_extra", 0))
        extra_type = ball_data.get("extra_type", "")
        is_wicket = bool(ball_data.get("is_wicket", False))
        dismissal_kind = ball_data.get("dismissal_kind", "")
        player_dismissed = ball_data.get("player_dismissed", batter if is_wicket else "")

        # Log delivery
        execute_statement("""
            INSERT INTO tournament_deliveries (
                match_id, innings, over_num, ball_num,
                batter_name, bowler_name, non_striker_name,
                runs_batter, runs_extra, extra_type, is_wicket, dismissal_kind, player_dismissed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            match_id, innings, over_num, ball_num,
            batter, bowler, non_striker,
            runs_batter, runs_extra, extra_type, is_wicket, dismissal_kind, player_dismissed
        ])

        # Compute updated innings total
        df_tot = execute_query("""
            SELECT SUM(runs_batter + runs_extra) as total_runs,
                   SUM(CASE WHEN is_wicket = true THEN 1 ELSE 0 END) as total_wickets,
                   COUNT(CASE WHEN extra_type NOT IN ('wide', 'noball') THEN 1 ELSE NULL END) as legal_balls
            FROM tournament_deliveries
            WHERE match_id = ? AND innings = ?;
        """, [match_id, innings])

        total_runs = int(df_tot.iloc[0]["total_runs"] or 0)
        total_wickets = int(df_tot.iloc[0]["total_wickets"] or 0)
        legal_balls = int(df_tot.iloc[0]["legal_balls"] or 0)
        overs = (legal_balls // 6) + (legal_balls % 6) / 10.0

        if innings == 1:
            execute_statement("""
                UPDATE tournament_matches
                SET status = 'live',
                    innings1_runs = ?,
                    innings1_wickets = ?,
                    innings1_overs = ?
                WHERE id = ?;
            """, [total_runs, total_wickets, overs, match_id])
        else:
            execute_statement("""
                UPDATE tournament_matches
                SET status = 'live',
                    innings2_runs = ?,
                    innings2_wickets = ?,
                    innings2_overs = ?
                WHERE id = ?;
            """, [total_runs, total_wickets, overs, match_id])

        # Calculate strike rotation
        # Legal ball count in over
        is_legal = extra_type not in ["wide", "noball"]
        is_over_end = is_legal and (legal_balls % 6 == 0) and legal_balls > 0
        is_odd_run = (runs_batter % 2 == 1)

        new_striker = batter
        new_non_striker = non_striker

        if is_wicket and player_dismissed == batter:
            new_striker = ball_data.get("next_batter", "New Batter")
        elif is_odd_run:
            new_striker, new_non_striker = new_non_striker, new_striker

        if is_over_end:
            # Over end strike change
            new_striker, new_non_striker = new_non_striker, new_striker

        return {
            "status": "recorded",
            "innings": innings,
            "total_runs": total_runs,
            "total_wickets": total_wickets,
            "overs": overs,
            "striker": new_striker,
            "non_striker": new_non_striker,
            "over_completed": is_over_end,
            "legal_balls": legal_balls,
        }

    @staticmethod
    def get_standings(tournament_id: str) -> List[Dict[str, Any]]:
        """
        Calculates the Tournament Points Table with exact Net Run Rate (NRR):
        NRR = (Runs Scored / Overs Faced) - (Runs Conceded / Overs Bowled)
        Points = (Wins * 2) + (Ties/NR * 1)
        """
        df_teams = execute_query("""
            SELECT id, name, short_code, color
            FROM tournament_teams
            WHERE tournament_id = ?;
        """, [tournament_id])

        if df_teams.empty:
            return []

        df_matches = execute_query("""
            SELECT * FROM tournament_matches
            WHERE tournament_id = ? AND status = 'completed';
        """, [tournament_id])

        standings = []
        for _, t in df_teams.iterrows():
            t_id = t["id"]
            p = 0
            w = 0
            l = 0
            tied = 0
            runs_scored = 0
            legal_overs_faced = 0.0
            runs_conceded = 0
            legal_overs_bowled = 0.0

            if not df_matches.empty:
                for _, m in df_matches.iterrows():
                    is_t1 = (m["team1_id"] == t_id)
                    is_t2 = (m["team2_id"] == t_id)

                    if not (is_t1 or is_t2):
                        continue

                    p += 1
                    winner = m["winner_team_id"]
                    if winner == t_id:
                        w += 1
                    elif winner and winner != "tie" and winner != "no_result":
                        l += 1
                    else:
                        tied += 1

                    if is_t1:
                        runs_scored += int(m["innings1_runs"] or 0)
                        legal_overs_faced += float(m["innings1_overs"] or 0.0)
                        runs_conceded += int(m["innings2_runs"] or 0)
                        legal_overs_bowled += float(m["innings2_overs"] or 0.0)
                    else:
                        runs_scored += int(m["innings2_runs"] or 0)
                        legal_overs_faced += float(m["innings2_overs"] or 0.0)
                        runs_conceded += int(m["innings1_runs"] or 0)
                        legal_overs_bowled += float(m["innings1_overs"] or 0.0)

            # Convert overs notation (e.g. 19.3 -> 19.5 real decimal overs)
            def to_true_overs(ov: float) -> float:
                full = int(ov)
                balls = round((ov - full) * 10)
                return full + (balls / 6.0)

            dec_faced = to_true_overs(legal_overs_faced)
            dec_bowled = to_true_overs(legal_overs_bowled)

            for_rate = (runs_scored / dec_faced) if dec_faced > 0 else 0.0
            against_rate = (runs_conceded / dec_bowled) if dec_bowled > 0 else 0.0
            nrr = round(for_rate - against_rate, 3)

            points = (w * 2) + (tied * 1)

            standings.append({
                "team_id": t_id,
                "team_name": t["name"],
                "short_code": t["short_code"],
                "color": t["color"],
                "played": p,
                "won": w,
                "lost": l,
                "tied": tied,
                "points": points,
                "nrr": nrr,
                "runs_for": runs_scored,
                "overs_for": round(legal_overs_faced, 1),
                "runs_against": runs_conceded,
                "overs_against": round(legal_overs_bowled, 1),
            })

        # Rank by: Points DESC, NRR DESC, Won DESC
        standings.sort(key=lambda x: (x["points"], x["nrr"], x["won"]), reverse=True)
        return standings

    @staticmethod
    def get_leaderboard(tournament_id: str) -> Dict[str, Any]:
        """
        Calculates Tournament Leaderboards:
        - Orange Cap: Top Run Scorers (Runs, Inning Count, Average, Strike Rate, 50s, 100s)
        - Purple Cap: Top Wicket Takers (Wickets, Overs, Runs Conceded, Economy Rate, Best Figures)
        """
        # Batting stats
        df_bat = execute_query("""
            SELECT player_name,
                   COUNT(*) as innings,
                   SUM(runs) as total_runs,
                   SUM(balls) as total_balls,
                   SUM(fours) as total_fours,
                   SUM(sixes) as total_sixes,
                   MAX(runs) as high_score,
                   SUM(CASE WHEN is_out = true THEN 1 ELSE 0 END) as dismissals,
                   SUM(CASE WHEN runs >= 50 AND runs < 100 THEN 1 ELSE 0 END) as fifties,
                   SUM(CASE WHEN runs >= 100 THEN 1 ELSE 0 END) as hundreds
            FROM tournament_scorecards
            WHERE tournament_id = ? AND (runs > 0 OR balls > 0)
            GROUP BY player_name
            ORDER BY total_runs DESC, total_balls ASC
            LIMIT 10;
        """, [tournament_id])

        orange_cap = []
        if not df_bat.empty:
            for _, r in df_bat.iterrows():
                d = int(r["dismissals"])
                runs = int(r["total_runs"])
                balls = int(r["total_balls"])
                avg = round(runs / d, 2) if d > 0 else (float(runs) if runs > 0 else 0.0)
                sr = round((runs / balls) * 100.0, 1) if balls > 0 else 0.0

                orange_cap.append({
                    "player_name": r["player_name"],
                    "runs": runs,
                    "balls": balls,
                    "innings": int(r["innings"]),
                    "average": avg,
                    "strike_rate": sr,
                    "high_score": int(r["high_score"]),
                    "fifties": int(r["fifties"]),
                    "hundreds": int(r["hundreds"]),
                    "fours": int(r["total_fours"]),
                    "sixes": int(r["total_sixes"]),
                })

        # Bowling stats
        df_bowl = execute_query("""
            SELECT player_name,
                   SUM(wickets) as total_wickets,
                   SUM(overs_bowled) as total_overs,
                   SUM(runs_conceded) as runs_conceded,
                   SUM(maidens) as maidens
            FROM tournament_scorecards
            WHERE tournament_id = ? AND overs_bowled > 0
            GROUP BY player_name
            ORDER BY total_wickets DESC, runs_conceded ASC
            LIMIT 10;
        """, [tournament_id])

        purple_cap = []
        if not df_bowl.empty:
            for _, r in df_bowl.iterrows():
                w = int(r["total_wickets"])
                rc = int(r["runs_conceded"])
                ov = float(r["total_overs"])

                full = int(ov)
                balls = round((ov - full) * 10)
                dec_ov = full + (balls / 6.0)
                econ = round(rc / dec_ov, 2) if dec_ov > 0 else 0.0

                purple_cap.append({
                    "player_name": r["player_name"],
                    "wickets": w,
                    "overs": ov,
                    "runs_conceded": rc,
                    "economy": econ,
                    "maidens": int(r["maidens"]),
                })

        return {
            "orange_cap": orange_cap,
            "purple_cap": purple_cap
        }
