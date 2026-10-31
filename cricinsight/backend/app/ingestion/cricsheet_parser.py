"""
Cricsheet JSON Parser.
Parses official hierarchical Cricsheet JSON match files with:
- Exact metadata extraction (meta, info, innings)
- MD5 file hashing for idempotency
- Full extras breakdown (wides, noballs, byes, legbyes, penalties)
- Official cricket ball-counting conventions:
  * legal_ball: neither wide nor no-ball
  * ball_faced: batter faced ball (excludes wides, includes no-balls)
  * bowler_conceded_runs: batter runs + wides + noballs (excludes byes, leg-byes, penalties)
  * bowler_credited_wicket: caught, bowled, lbw, stumped, hit wicket, caught and bowled
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Dismissal kinds credited to the bowler in official cricket scoring
BOWLER_CREDITED_DISMISSALS = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
}

# Dismissals NOT credited to the bowler
NON_BOWLER_DISMISSALS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
    "handled the ball",
    "hit the ball twice",
}

class CricsheetParseError(Exception):
    """Raised when a Cricsheet JSON file is malformed or invalid."""
    pass

def compute_file_hash(content_bytes: bytes) -> str:
    """Computes a deterministic MD5 hex digest for file change detection."""
    return hashlib.md5(content_bytes).hexdigest()

def normalize_format(raw_type: str) -> str:
    """Preserves official Cricsheet match format designations."""
    fmt = raw_type.strip()
    # Normalize case while preserving international vs domestic distinction
    if fmt.upper() in {"IT20", "T20I"}:
        return "IT20"
    if fmt.upper() in {"T20", "TWENTY20"}:
        return "T20"
    if fmt.upper() in {"ODI"}:
        return "ODI"
    if fmt.upper() in {"TEST"}:
        return "Test"
    if fmt.upper() in {"MDM"}:
        return "MDM"
    if fmt.upper() in {"ODM"}:
        return "ODM"
    return fmt

# Pre-defined canonical name and alias map for prominent international players
KNOWN_PLAYER_ALIASES: Dict[str, Tuple[str, List[str]]] = {
    "V Kohli": ("Virat Kohli", ["Virat Kohli", "Kohli", "V Kohli", "King Kohli"]),
    "RG Sharma": ("Rohit Sharma", ["Rohit Sharma", "Rohit", "RG Sharma", "Hitman"]),
    "JJ Bumrah": ("Jasprit Bumrah", ["Jasprit Bumrah", "Bumrah", "JJ Bumrah"]),
    "RA Jadeja": ("Ravindra Jadeja", ["Ravindra Jadeja", "Jadeja", "RA Jadeja", "Sir Jadeja"]),
    "HH Pandya": ("Hardik Pandya", ["Hardik Pandya", "Pandya", "HH Pandya"]),
    "KL Rahul": ("KL Rahul", ["KL Rahul", "Lokesh Rahul", "Rahul"]),
    "S Gill": ("Shubman Gill", ["Shubman Gill", "Gill", "S Gill"]),
    "Shubman Gill": ("Shubman Gill", ["Shubman Gill", "Gill"]),
    "SS Iyer": ("Shreyas Iyer", ["Shreyas Iyer", "Iyer", "SS Iyer"]),
    "SA Yadav": ("Suryakumar Yadav", ["Suryakumar Yadav", "SKY", "Surya", "SA Yadav"]),
    "Mohammed Shami": ("Mohammed Shami", ["Mohammed Shami", "Shami", "M Shami"]),
    "Mohammed Siraj": ("Mohammed Siraj", ["Mohammed Siraj", "Siraj", "M Siraj"]),
    "Kuldeep Yadav": ("Kuldeep Yadav", ["Kuldeep Yadav", "K Yadav"]),
    "MS Dhoni": ("MS Dhoni", ["MS Dhoni", "Mahendra Singh Dhoni", "Dhoni", "Mahi"]),
    "SR Tendulkar": ("Sachin Tendulkar", ["Sachin Tendulkar", "Tendulkar", "SR Tendulkar", "Sachin"]),
    "SPD Smith": ("Steve Smith", ["Steve Smith", "Steven Smith", "Smith", "SPD Smith"]),
    "DA Warner": ("David Warner", ["David Warner", "Warner", "DA Warner"]),
    "TM Head": ("Travis Head", ["Travis Head", "Head", "TM Head"]),
    "GJ Maxwell": ("Glenn Maxwell", ["Glenn Maxwell", "Maxwell", "GJ Maxwell"]),
    "MA Starc": ("Mitchell Starc", ["Mitchell Starc", "Starc", "MA Starc"]),
    "PJ Cummins": ("Pat Cummins", ["Pat Cummins", "Cummins", "PJ Cummins"]),
    "JR Hazlewood": ("Josh Hazlewood", ["Josh Hazlewood", "Hazlewood", "JR Hazlewood"]),
    "A Zampa": ("Adam Zampa", ["Adam Zampa", "Zampa", "A Zampa"]),
    "M Labuschagne": ("Marnus Labuschagne", ["Marnus Labuschagne", "Labuschagne", "M Labuschagne"]),
    "MP Stoinis": ("Marcus Stoinis", ["Marcus Stoinis", "Stoinis", "MP Stoinis"]),
    "MR Marsh": ("Mitchell Marsh", ["Mitchell Marsh", "Marsh", "MR Marsh"]),
    "Babar Azam": ("Babar Azam", ["Babar Azam", "Babar"]),
    "Mohammad Rizwan": ("Mohammad Rizwan", ["Mohammad Rizwan", "Rizwan"]),
    "Shaheen Shah Afridi": ("Shaheen Afridi", ["Shaheen Shah Afridi", "Shaheen"]),
    "JE Root": ("Joe Root", ["Joe Root", "Root", "JE Root"]),
    "BA Stokes": ("Ben Stokes", ["Ben Stokes", "Stokes", "BA Stokes"]),
}

def parse_cricsheet_match(file_path: Path) -> Dict[str, Any]:
    """
    Parses a single Cricsheet match JSON file into structured relational dicts.
    Returns:
    {
        "match": Dict,
        "players": List[Dict],
        "player_aliases": List[Dict],
        "innings": List[Dict],
        "deliveries": List[Dict],
        "file_hash": str,
        "source_match_id": str
    }
    """
    try:
        content_bytes = file_path.read_bytes()
        file_hash = compute_file_hash(content_bytes)
        data = json.loads(content_bytes.decode("utf-8"))
    except Exception as e:
        raise CricsheetParseError(f"Failed to read/decode JSON from {file_path.name}: {e}")

    # Top-level validation
    if not isinstance(data, dict):
        raise CricsheetParseError(f"Root object in {file_path.name} is not a dictionary.")
    
    meta = data.get("meta", {})
    info = data.get("info", {})
    raw_innings = data.get("innings", [])

    if not info:
        raise CricsheetParseError(f"Missing 'info' section in {file_path.name}.")

    source_match_id = file_path.stem

    # Match Dates handling (array of strings, e.g. ["2023-10-15"] or multi-day tests)
    dates_raw = info.get("dates", [])
    if isinstance(dates_raw, str):
        dates_list = [dates_raw]
    elif isinstance(dates_raw, list) and dates_raw:
        dates_list = [str(d) for d in dates_raw]
    else:
        dates_list = ["1970-01-01"]

    start_date = dates_list[0]
    end_date = dates_list[-1]

    # Format & Competition
    raw_match_type = str(info.get("match_type", "Unknown"))
    match_type = normalize_format(raw_match_type)
    match_type_num = info.get("match_type_number")
    
    event = info.get("event", {})
    competition = event.get("name") if isinstance(event, dict) else str(event) if event else None
    season = str(info.get("season", ""))
    gender = str(info.get("gender", "male"))
    venue = info.get("venue")
    city = info.get("city")
    teams = [str(t) for t in info.get("teams", [])]

    # Toss & Outcome
    toss = info.get("toss", {})
    toss_winner = toss.get("winner")
    toss_decision = toss.get("decision")

    outcome = info.get("outcome", {})
    outcome_winner = outcome.get("winner")
    by_data = outcome.get("by", {})
    outcome_by_runs = by_data.get("runs") if isinstance(by_data, dict) else None
    outcome_by_wickets = by_data.get("wickets") if isinstance(by_data, dict) else None
    outcome_result = outcome.get("result")
    outcome_method = outcome.get("method")

    player_of_match = [str(p) for p in info.get("player_of_match", [])]
    balls_per_over = int(info.get("balls_per_over", 6))
    overs_limit = int(info.get("overs", 0)) if info.get("overs") else None

    match_record = {
        "id": f"cricsheet_{source_match_id}",
        "source": "cricsheet",
        "source_match_id": source_match_id,
        "dates": dates_list,
        "start_date": start_date,
        "end_date": end_date,
        "match_type": match_type,
        "match_type_number": match_type_num,
        "competition": competition,
        "season": season,
        "gender": gender,
        "venue": venue,
        "city": city,
        "teams": teams,
        "toss_winner": toss_winner,
        "toss_decision": toss_decision,
        "outcome_winner": outcome_winner,
        "outcome_by_runs": outcome_by_runs,
        "outcome_by_wickets": outcome_by_wickets,
        "outcome_result": outcome_result,
        "outcome_method": outcome_method,
        "player_of_match": player_of_match,
        "balls_per_over": balls_per_over,
        "overs_limit": overs_limit,
        "source_file_hash": file_hash,
    }

    # Player Registry Extraction
    # info.registry.people maps player name -> unique Cricsheet ID
    registry_people = info.get("registry", {}).get("people", {})
    parsed_players = {}
    parsed_aliases = []

    # Also inspect info.players which maps team -> list of players
    team_players = info.get("players", {})
    all_player_names = set()
    if isinstance(team_players, dict):
        for t_name, p_list in team_players.items():
            for p in p_list:
                all_player_names.add(str(p))

    for p_name in all_player_names:
        c_id = registry_people.get(p_name)
        player_pk = f"p_{c_id}" if c_id else f"p_name_{p_name.lower().replace(' ', '_')}"

        if p_name in KNOWN_PLAYER_ALIASES:
            canon_name, aliases_list = KNOWN_PLAYER_ALIASES[p_name]
        else:
            canon_name = p_name
            aliases_list = [p_name]

        parsed_players[p_name] = {
            "id": player_pk,
            "canonical_name": canon_name,
            "cricsheet_id": c_id,
            "metadata": {"source": "match_info", "cricsheet_name": p_name}
        }

        seen_aliases = set()
        for idx, al in enumerate(aliases_list):
            al_norm = al.lower().strip()
            if al_norm not in seen_aliases:
                seen_aliases.add(al_norm)
                parsed_aliases.append({
                    "player_id": player_pk,
                    "alias": al,
                    "normalized_alias": al_norm,
                    "source": "canonical" if idx == 0 else "alias",
                    "is_primary": (al == canon_name)
                })

    # Innings and Deliveries parsing
    parsed_innings = []
    parsed_deliveries = []
    delivery_index = 0

    for inn_idx, inn_data in enumerate(raw_innings):
        batting_team = inn_data.get("team", "")
        # Find bowling team
        bowling_team = next((t for t in teams if t != batting_team), "Unknown")
        declared = inn_data.get("declared", False)
        inn_overs_limit = inn_data.get("target", {}).get("overs")

        inn_total_runs = 0
        inn_total_wickets = 0
        inn_total_legal_balls = 0

        # Cricsheet JSON representation can have 'overs' list
        overs_list = inn_data.get("overs", [])
        for over_data in overs_list:
            over_num = int(over_data.get("over", 0))
            raw_deliveries = over_data.get("deliveries", [])

            for b_idx, deliv in enumerate(raw_deliveries):
                delivery_index += 1
                ball_num = b_idx + 1

                batter_name = deliv.get("batter", "")
                bowler_name = deliv.get("bowler", "")
                non_striker_name = deliv.get("non_striker", "")

                runs_info = deliv.get("runs", {})
                b_runs = int(runs_info.get("batter", 0))
                e_runs = int(runs_info.get("extras", 0))
                tot_runs = int(runs_info.get("total", b_runs + e_runs))

                extras_info = deliv.get("extras", {})
                wides = int(extras_info.get("wides", 0))
                noballs = int(extras_info.get("noballs", 0))
                byes = int(extras_info.get("byes", 0))
                legbyes = int(extras_info.get("legbyes", 0))
                penalty = int(extras_info.get("penalty", 0))

                is_wide = wides > 0
                is_noball = noballs > 0
                is_bye = byes > 0
                is_legbye = legbyes > 0
                is_penalty = penalty > 0

                # Official Cricket Rule:
                # - Legal ball: not a wide and not a no-ball
                # - Ball faced: faced by batter (legal ball + noballs, but NOT wides)
                is_legal_ball = (not is_wide) and (not is_noball)
                is_ball_faced = not is_wide

                # Bowler conceded runs:
                # Bowler is charged for batter runs + wides + noballs.
                # Bowler is NOT charged for byes, leg-byes, or penalty runs.
                bowler_conceded_runs = b_runs + wides + noballs

                # Wickets analysis
                wickets_list = deliv.get("wickets", [])
                is_wicket = len(wickets_list) > 0
                dismissal_kind = None
                player_dismissed = None
                bowler_credited_wicket = False

                if is_wicket:
                    w_first = wickets_list[0]
                    dismissal_kind = w_first.get("kind", "")
                    player_dismissed = w_first.get("player_out", "")
                    if dismissal_kind in BOWLER_CREDITED_DISMISSALS:
                        bowler_credited_wicket = True

                # Aggregates
                inn_total_runs += tot_runs
                if is_wicket and dismissal_kind != "retired hurt":
                    inn_total_wickets += 1
                if is_legal_ball:
                    inn_total_legal_balls += 1

                # Player IDs
                batter_pk = parsed_players.get(batter_name, {}).get("id")
                bowler_pk = parsed_players.get(bowler_name, {}).get("id")
                non_striker_pk = parsed_players.get(non_striker_name, {}).get("id")

                parsed_deliveries.append({
                    "delivery_index": delivery_index,
                    "innings_number": inn_idx + 1,
                    "match_id": match_record["id"],
                    "over_num": over_num,
                    "ball_num": ball_num,
                    "batter_id": batter_pk,
                    "batter_name": batter_name,
                    "bowler_id": bowler_pk,
                    "bowler_name": bowler_name,
                    "non_striker_id": non_striker_pk,
                    "non_striker_name": non_striker_name,
                    "batter_runs": b_runs,
                    "extra_runs": e_runs,
                    "total_runs": tot_runs,
                    "is_wide": is_wide,
                    "is_noball": is_noball,
                    "is_bye": is_bye,
                    "is_legbye": is_legbye,
                    "is_penalty": is_penalty,
                    "is_legal_ball": is_legal_ball,
                    "is_ball_faced": is_ball_faced,
                    "bowler_conceded_runs": bowler_conceded_runs,
                    "is_wicket": is_wicket,
                    "dismissal_kind": dismissal_kind,
                    "player_dismissed": player_dismissed,
                    "bowler_credited_wicket": bowler_credited_wicket,
                    "extras_detail": extras_info,
                    "wicket_detail": wickets_list if is_wicket else None,
                })

        parsed_innings.append({
            "match_id": match_record["id"],
            "innings_number": inn_idx + 1,
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "declared": declared,
            "overs_limit": inn_overs_limit,
            "total_runs": inn_total_runs,
            "total_wickets": inn_total_wickets,
            "total_legal_balls": inn_total_legal_balls,
        })

    return {
        "match": match_record,
        "players": list(parsed_players.values()),
        "player_aliases": parsed_aliases,
        "innings": parsed_innings,
        "deliveries": parsed_deliveries,
        "file_hash": file_hash,
        "source_match_id": source_match_id,
    }
