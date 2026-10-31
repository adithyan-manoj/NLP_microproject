import pytest
from app.services.tournament_service import TournamentService
from app.database.db import execute_statement

@pytest.fixture(autouse=True)
def clean_tournaments():
    yield
    # Clean up test tournament data
    execute_statement("DELETE FROM tournament_deliveries WHERE match_id LIKE 'tmatch_test%';")
    execute_statement("DELETE FROM tournament_scorecards WHERE tournament_id LIKE 'tour_test%';")
    execute_statement("DELETE FROM tournament_matches WHERE tournament_id LIKE 'tour_test%';")
    execute_statement("DELETE FROM tournament_players WHERE tournament_id LIKE 'tour_test%';")
    execute_statement("DELETE FROM tournament_teams WHERE tournament_id LIKE 'tour_test%';")
    execute_statement("DELETE FROM tournaments WHERE id LIKE 'tour_test%';")

def test_tournament_creation_and_teams():
    # 1. Create Tournament
    tour = TournamentService.create_tournament(
        name="Inter-College Championship 2026",
        season="2026",
        format="T20",
        overs_limit=20
    )
    assert tour["name"] == "Inter-College Championship 2026"
    assert tour["format"] == "T20"
    tour_id = tour["id"]

    # 2. Add Team 1
    t1 = TournamentService.add_team(
        tournament_id=tour_id,
        name="Royal Strikers",
        short_code="RS",
        captain="Rahul Sharma",
        color="#06B6D4",
        players=["Rahul Sharma", "Anil Kumble", "VVS Laxman"]
    )
    assert t1["short_code"] == "RS"
    assert len(t1["players"]) == 3

    # 3. Add Team 2
    t2 = TournamentService.add_team(
        tournament_id=tour_id,
        name="Thunderbolts CC",
        short_code="TCC",
        captain="Vikram Singh",
        color="#F59E0B",
        players=["Vikram Singh", "Suresh Raina", "Harbhajan Singh"]
    )
    assert t2["short_code"] == "TCC"

    # 4. Create Match Fixture
    match = TournamentService.create_match(
        tournament_id=tour_id,
        team1_id=t1["id"],
        team2_id=t2["id"],
        venue="City University Ground",
        match_number=1
    )
    assert match["status"] == "scheduled"
    match_id = match["id"]

    # 5. Record Scorecard (Summary Mode)
    scorecard_payload = {
        "toss_winner_id": t1["id"],
        "toss_decision": "bat",
        "winner_team_id": t1["id"],
        "margin": "25 runs",
        "innings1_runs": 175,
        "innings1_wickets": 4,
        "innings1_overs": 20.0,
        "innings2_runs": 150,
        "innings2_wickets": 8,
        "innings2_overs": 20.0,
        "scorecards": [
            {
                "team_id": t1["id"],
                "player_name": "Rahul Sharma",
                "runs": 85,
                "balls": 52,
                "fours": 8,
                "sixes": 4,
                "overs_bowled": 0.0,
                "maidens": 0,
                "runs_conceded": 0,
                "wickets": 0,
                "is_out": False
            },
            {
                "team_id": t2["id"],
                "player_name": "Harbhajan Singh",
                "runs": 15,
                "balls": 10,
                "fours": 2,
                "sixes": 0,
                "overs_bowled": 4.0,
                "maidens": 0,
                "runs_conceded": 28,
                "wickets": 3,
                "is_out": True
            }
        ]
    }

    res = TournamentService.record_scorecard(match_id, scorecard_payload)
    assert res["status"] == "success"

    # 6. Verify Standings & Net Run Rate (NRR)
    standings = TournamentService.get_standings(tour_id)
    assert len(standings) == 2

    # Winner: Royal Strikers should have 2 points, positive NRR
    winner_row = next(s for s in standings if s["team_id"] == t1["id"])
    assert winner_row["points"] == 2
    assert winner_row["won"] == 1
    assert winner_row["lost"] == 0
    # Royal Strikers: 175/20 - 150/20 = 8.75 - 7.50 = +1.25 NRR
    assert winner_row["nrr"] == 1.25

    # Loser: Thunderbolts CC should have 0 points, negative NRR
    loser_row = next(s for s in standings if s["team_id"] == t2["id"])
    assert loser_row["points"] == 0
    assert loser_row["nrr"] == -1.25

    # 7. Verify Leaderboard (Orange Cap & Purple Cap)
    leaderboard = TournamentService.get_leaderboard(tour_id)
    orange_cap = leaderboard["orange_cap"]
    assert len(orange_cap) >= 1
    assert orange_cap[0]["player_name"] == "Rahul Sharma"
    assert orange_cap[0]["runs"] == 85
    assert orange_cap[0]["strike_rate"] > 160.0

    purple_cap = leaderboard["purple_cap"]
    assert len(purple_cap) >= 1
    assert purple_cap[0]["player_name"] == "Harbhajan Singh"
    assert purple_cap[0]["wickets"] == 3
    assert purple_cap[0]["economy"] == 7.0

def test_live_ball_scoring_and_strike_rotation():
    # Setup tournament & match
    tour = TournamentService.create_tournament(name="Live Scoring Cup")
    t1 = TournamentService.add_team(tour["id"], "Lions", "LIO")
    t2 = TournamentService.add_team(tour["id"], "Tigers", "TIG")
    match = TournamentService.create_match(tour["id"], t1["id"], t2["id"])
    match_id = match["id"]

    # Ball 1: Batter takes a single (1 run) -> Strike rotates
    b1 = TournamentService.record_live_ball(match_id, {
        "innings": 1,
        "over_num": 0,
        "ball_num": 1,
        "batter_name": "A",
        "bowler_name": "Bowler X",
        "non_striker_name": "B",
        "runs_batter": 1,
        "runs_extra": 0,
        "extra_type": "",
        "is_wicket": False
    })
    assert b1["total_runs"] == 1
    assert b1["striker"] == "B"  # Rotated!
    assert b1["non_striker"] == "A"

    # Ball 2: Batter hits a four (4 runs) -> Strike stays
    b2 = TournamentService.record_live_ball(match_id, {
        "innings": 1,
        "over_num": 0,
        "ball_num": 2,
        "batter_name": "B",
        "bowler_name": "Bowler X",
        "non_striker_name": "A",
        "runs_batter": 4,
        "runs_extra": 0,
        "extra_type": "",
        "is_wicket": False
    })
    assert b2["total_runs"] == 5
    assert b2["striker"] == "B"
    assert b2["non_striker"] == "A"
