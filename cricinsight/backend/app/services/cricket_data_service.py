"""
Cricket Data Service - DuckDB Analytical and Statistical Engine.
Handles parameterized queries, OLAP aggregations, rolling metrics, and statistical measures.
"""
from typing import Optional, List, Dict, Any, Tuple
import json
import re
import pandas as pd
import numpy as np
from app.database.db import execute_query

# Cache of dynamically loaded alias map
_ALIAS_LOOKUP_CACHE: Optional[Dict[str, Tuple[str, str]]] = None

# Curated canonical mapping for top international and IPL cricketers
KNOWN_PLAYER_ALIASES: Dict[str, Tuple[str, str]] = {
    # India
    "virat kohli": ("V Kohli", "Virat Kohli"),
    "kohli": ("V Kohli", "Virat Kohli"),
    "virat": ("V Kohli", "Virat Kohli"),
    "king kohli": ("V Kohli", "Virat Kohli"),
    "rohit sharma": ("RG Sharma", "Rohit Sharma"),
    "rohit": ("RG Sharma", "Rohit Sharma"),
    "hitman": ("RG Sharma", "Rohit Sharma"),
    "shubman gill": ("Shubman Gill", "Shubman Gill"),
    "gill": ("Shubman Gill", "Shubman Gill"),
    "shubman": ("Shubman Gill", "Shubman Gill"),
    "kl rahul": ("KL Rahul", "KL Rahul"),
    "rahul": ("KL Rahul", "KL Rahul"),
    "lokesh rahul": ("KL Rahul", "KL Rahul"),
    "hardik pandya": ("HH Pandya", "Hardik Pandya"),
    "hardik": ("HH Pandya", "Hardik Pandya"),
    "pandya": ("HH Pandya", "Hardik Pandya"),
    "suryakumar yadav": ("SA Yadav", "Suryakumar Yadav"),
    "surya kumar yadav": ("SA Yadav", "Suryakumar Yadav"),
    "suryakumar": ("SA Yadav", "Suryakumar Yadav"),
    "surya": ("SA Yadav", "Suryakumar Yadav"),
    "sky": ("SA Yadav", "Suryakumar Yadav"),
    "rishabh pant": ("RR Pant", "Rishabh Pant"),
    "pant": ("RR Pant", "Rishabh Pant"),
    "rishabh": ("RR Pant", "Rishabh Pant"),
    "shreyas iyer": ("SS Iyer", "Shreyas Iyer"),
    "iyer": ("SS Iyer", "Shreyas Iyer"),
    "shikhar dhawan": ("S Dhawan", "Shikhar Dhawan"),
    "dhawan": ("S Dhawan", "Shikhar Dhawan"),
    "gabbar": ("S Dhawan", "Shikhar Dhawan"),
    "ms dhoni": ("MS Dhoni", "MS Dhoni"),
    "dhoni": ("MS Dhoni", "MS Dhoni"),
    "mahi": ("MS Dhoni", "MS Dhoni"),
    "jasprit bumrah": ("JJ Bumrah", "Jasprit Bumrah"),
    "bumrah": ("JJ Bumrah", "Jasprit Bumrah"),
    "mohammed shami": ("Mohammed Shami", "Mohammed Shami"),
    "shami": ("Mohammed Shami", "Mohammed Shami"),
    "ravindra jadeja": ("RA Jadeja", "Ravindra Jadeja"),
    "jadeja": ("RA Jadeja", "Ravindra Jadeja"),
    "sir jadeja": ("RA Jadeja", "Ravindra Jadeja"),
    "kuldeep yadav": ("Kuldeep Yadav", "Kuldeep Yadav"),
    "kuldeep": ("Kuldeep Yadav", "Kuldeep Yadav"),
    "axar patel": ("AR Patel", "Axar Patel"),
    "axar": ("AR Patel", "Axar Patel"),
    "yashasvi jaiswal": ("YBK Jaiswal", "Yashasvi Jaiswal"),
    "jaiswal": ("YBK Jaiswal", "Yashasvi Jaiswal"),
    "sanju samson": ("SV Samson", "Sanju Samson"),
    "samson": ("SV Samson", "Sanju Samson"),
    "ishan kishan": ("Ishan Kishan", "Ishan Kishan"),
    "kishan": ("Ishan Kishan", "Ishan Kishan"),

    # Australia
    "david warner": ("DA Warner", "David Warner"),
    "warner": ("DA Warner", "David Warner"),
    "steve smith": ("SPD Smith", "Steve Smith"),
    "steven smith": ("SPD Smith", "Steve Smith"),
    "smith": ("SPD Smith", "Steve Smith"),
    "smudge": ("SPD Smith", "Steve Smith"),
    "travis head": ("TM Head", "Travis Head"),
    "head": ("TM Head", "Travis Head"),
    "glenn maxwell": ("GJ Maxwell", "Glenn Maxwell"),
    "maxwell": ("GJ Maxwell", "Glenn Maxwell"),
    "maxi": ("GJ Maxwell", "Glenn Maxwell"),
    "mitch marsh": ("MR Marsh", "Mitchell Marsh"),
    "mitchell marsh": ("MR Marsh", "Mitchell Marsh"),
    "aaron finch": ("AJ Finch", "Aaron Finch"),
    "finch": ("AJ Finch", "Aaron Finch"),
    "marnus labuschagne": ("M Labuschagne", "Marnus Labuschagne"),
    "labuschagne": ("M Labuschagne", "Marnus Labuschagne"),
    "pat cummins": ("PJ Cummins", "Pat Cummins"),
    "cummins": ("PJ Cummins", "Pat Cummins"),
    "mitchell starc": ("MA Starc", "Mitchell Starc"),
    "starc": ("MA Starc", "Mitchell Starc"),
    "josh hazlewood": ("JR Hazlewood", "Josh Hazlewood"),
    "hazlewood": ("JR Hazlewood", "Josh Hazlewood"),
    "alex carey": ("AT Carey", "Alex Carey"),
    "marcus stoinis": ("MP Stoinis", "Marcus Stoinis"),
    "stoinis": ("MP Stoinis", "Marcus Stoinis"),
    "tim david": ("TH David", "Tim David"),
    "shane watson": ("SR Watson", "Shane Watson"),
    "watson": ("SR Watson", "Shane Watson"),

    # Pakistan
    "babar azam": ("Babar Azam", "Babar Azam"),
    "babar": ("Babar Azam", "Babar Azam"),
    "mohammad rizwan": ("Mohammad Rizwan", "Mohammad Rizwan"),
    "rizwan": ("Mohammad Rizwan", "Mohammad Rizwan"),
    "fakhar zaman": ("Fakhar Zaman", "Fakhar Zaman"),
    "fakhar": ("Fakhar Zaman", "Fakhar Zaman"),
    "shaheen afridi": ("Shaheen Shah Afridi", "Shaheen Shah Afridi"),
    "shaheen": ("Shaheen Shah Afridi", "Shaheen Shah Afridi"),
    "imam ul haq": ("Imam-ul-Haq", "Imam-ul-Haq"),
    "imam-ul-haq": ("Imam-ul-Haq", "Imam-ul-Haq"),
    "imam": ("Imam-ul-Haq", "Imam-ul-Haq"),
    "shadab khan": ("Shadab Khan", "Shadab Khan"),
    "shadab": ("Shadab Khan", "Shadab Khan"),

    # England
    "jos buttler": ("JC Buttler", "Jos Buttler"),
    "buttler": ("JC Buttler", "Jos Buttler"),
    "joe root": ("JE Root", "Joe Root"),
    "root": ("JE Root", "Joe Root"),
    "ben stokes": ("BA Stokes", "Ben Stokes"),
    "stokes": ("BA Stokes", "Ben Stokes"),
    "jonny bairstow": ("JM Bairstow", "Jonny Bairstow"),
    "bairstow": ("JM Bairstow", "Jonny Bairstow"),
    "harry brook": ("HC Brook", "Harry Brook"),
    "brook": ("HC Brook", "Harry Brook"),
    "jason roy": ("JJ Roy", "Jason Roy"),
    "eoin morgan": ("EJG Morgan", "Eoin Morgan"),
    "morgan": ("EJG Morgan", "Eoin Morgan"),
    "liam livingstone": ("LS Livingstone", "Liam Livingstone"),
    "livingstone": ("LS Livingstone", "Liam Livingstone"),
    "moeen ali": ("MM Ali", "Moeen Ali"),

    # New Zealand
    "kane williamson": ("KS Williamson", "Kane Williamson"),
    "williamson": ("KS Williamson", "Kane Williamson"),
    "daryl mitchell": ("DJ Mitchell", "Daryl Mitchell"),
    "devon conway": ("DP Conway", "Devon Conway"),
    "conway": ("DP Conway", "Devon Conway"),
    "tom latham": ("TWM Latham", "Tom Latham"),
    "latham": ("TWM Latham", "Tom Latham"),
    "martin guptill": ("MJ Guptill", "Martin Guptill"),
    "guptill": ("MJ Guptill", "Martin Guptill"),
    "ross taylor": ("LRPL Taylor", "Ross Taylor"),
    "trent boult": ("TA Boult", "Trent Boult"),
    "boult": ("TA Boult", "Trent Boult"),
    "glenn phillips": ("GD Phillips", "Glenn Phillips"),

    # South Africa
    "quinton de kock": ("Q de Kock", "Quinton de Kock"),
    "de kock": ("Q de Kock", "Quinton de Kock"),
    "heinrich klaasen": ("H Klaasen", "Heinrich Klaasen"),
    "klaasen": ("H Klaasen", "Heinrich Klaasen"),
    "david miller": ("DA Miller", "David Miller"),
    "miller": ("DA Miller", "David Miller"),
    "aiden markram": ("AK Markram", "Aiden Markram"),
    "markram": ("AK Markram", "Aiden Markram"),
    "rassie van der dussen": ("HE van der Dussen", "Rassie van der Dussen"),
    "van der dussen": ("HE van der Dussen", "Rassie van der Dussen"),
    "faf du plessis": ("F du Plessis", "Faf du Plessis"),
    "faf": ("F du Plessis", "Faf du Plessis"),
    "kagiso rabada": ("K Rabada", "Kagiso Rabada"),
    "rabada": ("K Rabada", "Kagiso Rabada"),

    # West Indies
    "shai hope": ("SD Hope", "Shai Hope"),
    "hope": ("SD Hope", "Shai Hope"),
    "nicholas pooran": ("N Pooran", "Nicholas Pooran"),
    "pooran": ("N Pooran", "Nicholas Pooran"),
    "shimron hetmyer": ("SO Hetmyer", "Shimron Hetmyer"),
    "hetmyer": ("SO Hetmyer", "Shimron Hetmyer"),
    "rovman powell": ("R Powell", "Rovman Powell"),
    "jason holder": ("JO Holder", "Jason Holder"),
    "andre russell": ("AD Russell", "Andre Russell"),
    "russell": ("AD Russell", "Andre Russell"),

    # Sri Lanka
    "kusal mendis": ("BKG Mendis", "Kusal Mendis"),
    "mendis": ("BKG Mendis", "Kusal Mendis"),
    "pathum nissanka": ("P Nissanka", "Pathum Nissanka"),
    "nissanka": ("P Nissanka", "Pathum Nissanka"),
    "charith asalanka": ("KIC Asalanka", "Charith Asalanka"),
    "asalanka": ("KIC Asalanka", "Charith Asalanka"),
    "kusal perera": ("MDKJ Perera", "Kusal Perera"),
    "wanindu hasaranga": ("PWH de Silva", "Wanindu Hasaranga"),
    "hasaranga": ("PWH de Silva", "Wanindu Hasaranga"),

    # Afghanistan
    "rashid khan": ("Rashid Khan", "Rashid Khan"),
    "rashid": ("Rashid Khan", "Rashid Khan"),
    "rahmanullah gurbaz": ("Rahmanullah Gurbaz", "Rahmanullah Gurbaz"),
    "gurbaz": ("Rahmanullah Gurbaz", "Rahmanullah Gurbaz"),
    "ibrahim zadran": ("Ibrahim Zadran", "Ibrahim Zadran"),
    "mohammad nabi": ("Mohammad Nabi", "Mohammad Nabi"),
    "nabi": ("Mohammad Nabi", "Mohammad Nabi"),
}

def load_alias_lookup() -> Dict[str, Tuple[str, str]]:
    """
    Builds an in-memory alias dictionary loaded from both curated KNOWN_PLAYER_ALIASES
    and the DuckDB `players` and `deliveries` tables.
    """
    global _ALIAS_LOOKUP_CACHE
    if _ALIAS_LOOKUP_CACHE is not None:
        return _ALIAS_LOOKUP_CACHE

    alias_map: Dict[str, Tuple[str, str]] = dict(KNOWN_PLAYER_ALIASES)

    try:
        # Load all canonical names and aliases stored in players table
        df_players = execute_query("SELECT canonical_name, aliases FROM players")
        df_batters = execute_query("SELECT DISTINCT batter FROM deliveries")
        batter_set = set(df_batters["batter"].dropna().tolist())

        for _, row in df_players.iterrows():
            canon = str(row["canonical_name"])
            aliases_str = str(row["aliases"]) if row["aliases"] else "[]"
            alias_list = []
            try:
                alias_list = json.loads(aliases_str)
            except Exception:
                alias_list = [canon]

            # Find matching batter code in deliveries
            cricsheet_code = canon
            for candidate in alias_list:
                if candidate in batter_set:
                    cricsheet_code = candidate
                    break

            # Map canonical full name
            canon_key = canon.strip().lower()
            if canon_key not in alias_map:
                alias_map[canon_key] = (cricsheet_code, canon)

            # Map multi-token aliases from database
            for a in alias_list:
                a_key = str(a).strip().lower()
                if a_key and a_key not in alias_map and len(a_key) >= 4:
                    alias_map[a_key] = (cricsheet_code, canon)

        # Map distinct deliveries batter names
        for b in batter_set:
            b_key = b.strip().lower()
            if b_key not in alias_map:
                alias_map[b_key] = (b, b)

    except Exception:
        pass

    _ALIAS_LOOKUP_CACHE = alias_map
    return _ALIAS_LOOKUP_CACHE

def resolve_player_identity(name_query: str) -> Optional[Tuple[str, str]]:
    """
    Resolves any player query string (full name, surname, or alias) to:
    (cricsheet_batter_code, canonical_name).
    """
    clean_q = name_query.strip().lower()
    alias_map = load_alias_lookup()

    if clean_q in alias_map:
        return alias_map[clean_q]

    # Dynamic database search fallback
    try:
        sql = """
            SELECT canonical_name, aliases 
            FROM players 
            WHERE LOWER(canonical_name) LIKE ? OR LOWER(aliases) LIKE ?
            LIMIT 1
        """
        df = execute_query(sql, [f"%{clean_q}%", f"%{clean_q}%"])
        if not df.empty:
            canon = df.iloc[0]["canonical_name"]
            # Check deliveries table for batter code
            match_df = execute_query(
                "SELECT batter FROM deliveries WHERE LOWER(batter) = ? OR LOWER(batter) LIKE ? LIMIT 1",
                [clean_q, f"%{clean_q}%"]
            )
            cricsheet_code = match_df.iloc[0]["batter"] if not match_df.empty else canon
            return cricsheet_code, canon
    except Exception:
        pass

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
            "player_name": canonical_name,
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
