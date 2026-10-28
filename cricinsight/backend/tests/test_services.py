import pytest
from app.services.cricket_data_service import (
    resolve_player_identity,
    query_player_innings,
    calculate_statistical_metrics,
)
from app.services.nlp_service import parse_with_rules, extract_query_entities
from app.services.insight_service import generate_analytical_insight

def test_resolve_player_identity():
    # Canonical mapping checks
    c_name, canon = resolve_player_identity("kohli")
    assert c_name == "V Kohli"
    assert canon == "Virat Kohli"

    c_name, canon = resolve_player_identity("rohit")
    assert c_name == "RG Sharma"
    assert canon == "Rohit Sharma"

def test_nlp_parsing_single_player():
    prompt = "How has Virat Kohli performed against Australia in ODIs?"
    parsed = parse_with_rules(prompt)
    assert "Virat Kohli" in parsed.players
    assert parsed.opponent == "Australia"
    assert parsed.format == "ODI"
    assert parsed.analysis_type == "progression"
    assert parsed.chart_preference == "line"

def test_nlp_parsing_comparison():
    prompt = "Compare Rohit Sharma and Virat Kohli in T20 internationals"
    parsed = parse_with_rules(prompt)
    assert "Rohit Sharma" in parsed.players
    assert "Virat Kohli" in parsed.players
    assert parsed.format == "T20"
    assert parsed.analysis_type == "comparison"
    assert parsed.chart_preference == "bar"

def test_nlp_parsing_recent_n():
    prompt = "Show Kohli's last 10 innings"
    parsed = parse_with_rules(prompt)
    assert "Virat Kohli" in parsed.players
    assert parsed.recent_n == 10

def test_statistical_engine_calculations():
    df = query_player_innings("V Kohli", recent_n=5)
    assert not df.empty
    stats = calculate_statistical_metrics(df, "Virat Kohli")
    assert stats["innings_count"] == 5
    assert stats["total_runs"] > 0
    assert stats["batting_average"] > 0
    assert stats["strike_rate"] > 0
    assert "rolling_avg_last_5" in stats

def test_insight_generation():
    scope = {"players": ["Virat Kohli"], "format": "ODI", "opponent": "Australia"}
    stats = {
        "total_runs": 1200,
        "batting_average": 54.5,
        "strike_rate": 92.4,
        "high_score": 117,
        "high_score_not_out": False,
        "innings_count": 25,
        "centuries": 4,
        "fifties": 6,
        "std_deviation": 28.2,
        "consistency_rating": "Moderate spread",
    }
    obs = ["Scored 1200 runs", "4 centuries"]
    insight = generate_analytical_insight(scope, stats, obs)
    assert "Virat Kohli" in insight
    assert "1,200" in insight or "1200" in insight

