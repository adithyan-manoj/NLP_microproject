"""
CricInsight - Cricsheet Data Ingestion Pipeline
Parses hierarchical Cricsheet JSON files into normalized DuckDB tables:
- matches
- deliveries
- players
"""

import os
import sys
import json
import zipfile
import argparse
import urllib.request
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
import pandas as pd
import duckdb

# Determine backend directory and project root
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DATA_DIR = BACKEND_DIR / "data" / "cricsheet"
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "cricinsight.duckdb"
PEOPLE_CSV_PATH = BACKEND_DIR / "data" / "people.csv"

# Pre-defined canonical name and alias map for prominent international players
KNOWN_PLAYER_ALIASES: Dict[str, Tuple[str, List[str]]] = {
    # Unique name (in Cricsheet): (Canonical display name, list of aliases)
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
    "Shaheen Shah Afridi": ("Shaheen Afridi", ["Shaheen Afridi", "Shaheen Shah Afridi", "Shaheen"]),
    "JE Root": ("Joe Root", ["Joe Root", "Root", "JE Root"]),
    "BA Stokes": ("Ben Stokes", ["Ben Stokes", "Stokes", "BA Stokes"]),
    "JC Buttler": ("Jos Buttler", ["Jos Buttler", "Buttler", "JC Buttler"]),
    "KS Williamson": ("Kane Williamson", ["Kane Williamson", "Williamson", "KS Williamson"]),
    "TA Boult": ("Trent Boult", ["Trent Boult", "Boult", "TA Boult"]),
    "Q de Kock": ("Quinton de Kock", ["Quinton de Kock", "de Kock", "Q de Kock"]),
    "H Klaasen": ("Heinrich Klaasen", ["Heinrich Klaasen", "Klaasen", "H Klaasen"]),
    "K Rabada": ("Kagiso Rabada", ["Kagiso Rabada", "Rabada", "K Rabada"]),
    "Rashid Khan": ("Rashid Khan", ["Rashid Khan", "Rashid"]),
    "Shakib Al Hasan": ("Shakib Al Hasan", ["Shakib Al Hasan", "Shakib"]),
}


def download_dataset_if_needed(target_dir: Path):
    """
    Downloads and extracts a curated sample of modern Cricsheet matches
    if target_dir contains no json files.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    existing_files = list(target_dir.glob("*.json"))
    if existing_files:
        print(f"Found {len(existing_files)} existing JSON files in {target_dir}.")
        return

    print("No JSON files found in data directory. Downloading Cricsheet dataset...")
    temp_zip_odi = Path("/tmp/odis_test.zip")
    temp_zip_t20 = Path("/tmp/t20s_test.zip")

    if not temp_zip_odi.exists():
        print("Downloading ODIs zip from Cricsheet...")
        urllib.request.urlretrieve("https://cricsheet.org/downloads/odis_male_json.zip", temp_zip_odi)

    if not temp_zip_t20.exists():
        print("Downloading T20s zip from Cricsheet...")
        urllib.request.urlretrieve("https://cricsheet.org/downloads/t20s_male_json.zip", temp_zip_t20)

    # Curate high-value matches (e.g., matches since 2018 or major teams)
    top_teams = {'India', 'Australia', 'England', 'Pakistan', 'South Africa',
                 'New Zealand', 'West Indies', 'Sri Lanka', 'Afghanistan', 'Bangladesh'}

    print("Extracting curated international matches (ODIs and T20Is)...")
    extracted_count = 0

    # Extract ODIs
    with zipfile.ZipFile(temp_zip_odi) as z:
        for name in z.namelist():
            if not name.endswith('.json'):
                continue
            try:
                data = json.loads(z.read(name))
                info = data.get('info', {})
                dates = info.get('dates', [])
                teams = set(info.get('teams', []))
                if not dates:
                    continue
                date_str = dates[0]
                # Include matches from 2018+ or top team encounters from 2015+
                if date_str >= '2019-01-01' or (date_str >= '2015-01-01' and len(teams & top_teams) >= 2):
                    target_file = target_dir / name
                    target_file.write_bytes(z.read(name))
                    extracted_count += 1
            except Exception:
                continue

    # Extract T20s
    with zipfile.ZipFile(temp_zip_t20) as z:
        for name in z.namelist():
            if not name.endswith('.json'):
                continue
            try:
                data = json.loads(z.read(name))
                info = data.get('info', {})
                dates = info.get('dates', [])
                teams = set(info.get('teams', []))
                if not dates:
                    continue
                date_str = dates[0]
                # Include top team T20 internationals from 2020+
                if date_str >= '2020-01-01' and len(teams & top_teams) >= 2:
                    target_file = target_dir / name
                    target_file.write_bytes(z.read(name))
                    extracted_count += 1
            except Exception:
                continue

    print(f"Extracted {extracted_count} curated Cricsheet JSON matches into {target_dir}")


def parse_match_file(file_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, str]]:
    """
    Parses a single Cricsheet JSON file into:
    - match metadata dict
    - deliveries list of dicts
    - registry player_id -> unique_name map
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    match_id = file_path.stem
    info = data.get("info", {})

    # Dates
    dates = info.get("dates", [])
    match_date = dates[0] if dates else None

    # Match Type normalization (ODI, T20, Test)
    raw_type = info.get("match_type", "Unknown")
    if raw_type in ("IT20", "T20"):
        match_type = "T20"
    elif raw_type in ("ODI", "ODM"):
        match_type = "ODI"
    elif raw_type in ("Test", "MDM"):
        match_type = "Test"
    else:
        match_type = raw_type

    # Event / Competition
    event = info.get("event", {})
    competition = event.get("name") if isinstance(event, dict) else str(event)

    venue = info.get("venue", "Unknown")
    teams = info.get("teams", [])
    team_1 = teams[0] if len(teams) > 0 else "Unknown"
    team_2 = teams[1] if len(teams) > 1 else "Unknown"

    match_row = {
        "match_id": match_id,
        "date": match_date,
        "match_type": match_type,
        "competition": competition,
        "venue": venue,
        "team_1": team_1,
        "team_2": team_2,
    }

    # Player registry
    people_registry = info.get("registry", {}).get("people", {})

    deliveries = []
    innings_list = data.get("innings", [])

    for inn_idx, inn in enumerate(innings_list, start=1):
        batting_team = inn.get("team", "Unknown")
        # Bowling team is the opposing team
        bowling_team = team_2 if batting_team == team_1 else team_1

        for over_data in inn.get("overs", []):
            over_num = over_data.get("over", 0)
            for ball_idx, deliv in enumerate(over_data.get("deliveries", []), start=1):
                batter = deliv.get("batter", "Unknown")
                bowler = deliv.get("bowler", "Unknown")
                non_striker = deliv.get("non_striker")

                runs_dict = deliv.get("runs", {})
                batter_runs = runs_dict.get("batter", 0)
                extra_runs = runs_dict.get("extras", 0)

                wickets = deliv.get("wickets", [])
                if wickets:
                    is_wicket = True
                    dismissal_kind = wickets[0].get("kind")
                    player_dismissed = wickets[0].get("player_out")
                else:
                    is_wicket = False
                    dismissal_kind = None
                    player_dismissed = None

                deliveries.append({
                    "match_id": match_id,
                    "innings_number": inn_idx,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "over_num": over_num,
                    "ball_num": ball_idx,
                    "batter": batter,
                    "bowler": bowler,
                    "non_striker": non_striker,
                    "batter_runs": batter_runs,
                    "extra_runs": extra_runs,
                    "is_wicket": is_wicket,
                    "dismissal_kind": dismissal_kind,
                    "player_dismissed": player_dismissed,
                })

    return match_row, deliveries, people_registry


def build_players_table(conn: duckdb.DuckDBPyConnection, collected_players: Dict[str, str], seen_names: Set[str]):
    """
    Populates the 'players' table with canonical names and alias lists.
    """
    player_rows = []

    # 1. Process known international stars
    for unique_name, (canonical_name, aliases) in KNOWN_PLAYER_ALIASES.items():
        # Find player_id if collected, else use generated id
        pid = collected_players.get(unique_name, f"p_{abs(hash(unique_name)) % 10000000:07d}")
        # Ensure unique_name is in aliases
        if unique_name not in aliases:
            aliases.append(unique_name)
        player_rows.append({
            "player_id": pid,
            "canonical_name": canonical_name,
            "aliases": json.dumps(aliases),
        })
        seen_names.add(unique_name)
        seen_names.add(canonical_name)

    # 2. Add all other seen players from deliveries / registry
    for name, pid in collected_players.items():
        if name in seen_names:
            continue
        # Default alias list is [name]
        aliases = [name]
        player_rows.append({
            "player_id": pid,
            "canonical_name": name,
            "aliases": json.dumps(aliases),
        })
        seen_names.add(name)

    # 3. Add any batters/bowlers who weren't in registry
    for name in seen_names:
        if any(r["canonical_name"] == name for r in player_rows):
            continue
        pid = f"p_{abs(hash(name)) % 10000000:07d}"
        player_rows.append({
            "player_id": pid,
            "canonical_name": name,
            "aliases": json.dumps([name]),
        })

    df_players = pd.DataFrame(player_rows).drop_duplicates(subset=["player_id"])
    conn.register("temp_players", df_players)
    conn.execute("INSERT OR REPLACE INTO players SELECT * FROM temp_players;")
    conn.unregister("temp_players")
    print(f"Inserted {len(df_players)} players into players table.")


def ingest_data(data_dir: Path, db_path: Path, limit: int = 0, reset: bool = False):
    """
    Main ingestion orchestrator:
    Reads JSON files from data_dir, normalizes them, and loads into DuckDB.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    json_files = sorted(list(data_dir.glob("*.json")))
    if not json_files:
        print(f"No JSON files found in {data_dir}. Checking downloads...")
        download_dataset_if_needed(data_dir)
        json_files = sorted(list(data_dir.glob("*.json")))

    if not json_files:
        print("Error: No match files available for ingestion.")
        return

    if limit > 0:
        json_files = json_files[:limit]

    print(f"Preparing to ingest {len(json_files)} matches into {db_path}...")

    # Connect to DuckDB
    conn = duckdb.connect(str(db_path))

    if reset:
        print("Resetting existing tables...")
        conn.execute("DROP TABLE IF EXISTS deliveries;")
        conn.execute("DROP TABLE IF EXISTS matches;")
        conn.execute("DROP TABLE IF EXISTS players;")

    # Initialize Schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id VARCHAR PRIMARY KEY,
            date DATE,
            match_type VARCHAR,
            competition VARCHAR,
            venue VARCHAR,
            team_1 VARCHAR,
            team_2 VARCHAR
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            match_id VARCHAR,
            innings_number INTEGER,
            batting_team VARCHAR,
            bowling_team VARCHAR,
            over_num INTEGER,
            ball_num INTEGER,
            batter VARCHAR,
            bowler VARCHAR,
            non_striker VARCHAR,
            batter_runs INTEGER,
            extra_runs INTEGER,
            is_wicket BOOLEAN,
            dismissal_kind VARCHAR,
            player_dismissed VARCHAR
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id VARCHAR PRIMARY KEY,
            canonical_name VARCHAR,
            aliases VARCHAR
        );
    """)

    matches_list = []
    deliveries_list = []
    collected_registry: Dict[str, str] = {}
    seen_player_names: Set[str] = set()

    for idx, fpath in enumerate(json_files, start=1):
        try:
            match_row, deliveries, registry = parse_match_file(fpath)
            matches_list.append(match_row)
            deliveries_list.extend(deliveries)

            for pname, pid in registry.items():
                collected_registry[pname] = pid

            for d in deliveries:
                seen_player_names.add(d["batter"])
                seen_player_names.add(d["bowler"])

            if idx % 200 == 0 or idx == len(json_files):
                print(f"Processed {idx}/{len(json_files)} matches ({len(deliveries_list):,} deliveries)...")
        except Exception as e:
            print(f"Warning: Failed parsing {fpath.name}: {e}")

    # Load matches into DuckDB
    print("Loading matches into DuckDB...")
    df_matches = pd.DataFrame(matches_list).drop_duplicates(subset=["match_id"])
    conn.register("temp_matches", df_matches)
    conn.execute("INSERT OR REPLACE INTO matches SELECT * FROM temp_matches;")
    conn.unregister("temp_matches")

    # Load deliveries into DuckDB
    print(f"Loading {len(deliveries_list):,} deliveries into DuckDB...")
    df_deliveries = pd.DataFrame(deliveries_list)
    conn.register("temp_deliveries", df_deliveries)
    # Replace deliveries for these matches to maintain idempotency
    match_ids_tuple = tuple(df_matches["match_id"].tolist())
    if len(match_ids_tuple) == 1:
        conn.execute(f"DELETE FROM deliveries WHERE match_id = '{match_ids_tuple[0]}';")
    elif len(match_ids_tuple) > 1:
        conn.execute(f"DELETE FROM deliveries WHERE match_id IN {match_ids_tuple};")
    conn.execute("INSERT INTO deliveries SELECT * FROM temp_deliveries;")
    conn.unregister("temp_deliveries")

    # Load players
    print("Building players registry...")
    build_players_table(conn, collected_registry, seen_player_names)

    # Indexes
    print("Creating performance indexes...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_type ON matches(match_type);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_match ON deliveries(match_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_players_canonical ON players(canonical_name);")

    # Verification counts
    m_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    d_count = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    p_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    print("\n--- INGESTION SUMMARY ---")
    print(f"Total Matches:    {m_count:,}")
    print(f"Total Deliveries: {d_count:,}")
    print(f"Total Players:    {p_count:,}")
    print(f"DuckDB database ready at: {db_path}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest Cricsheet JSON data into DuckDB")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Path to Cricsheet JSON files")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to target DuckDB file")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of match files to ingest (0 for all)")
    parser.add_argument("--reset", action="store_true", help="Drop and rebuild tables")
    parser.add_argument("--download", action="store_true", help="Force download curated dataset")

    args = parser.parse_args()

    if args.download:
        download_dataset_if_needed(args.data_dir)

    ingest_data(
        data_dir=args.data_dir,
        db_path=args.db_path,
        limit=args.limit,
        reset=args.reset,
    )


if __name__ == "__main__":
    main()
