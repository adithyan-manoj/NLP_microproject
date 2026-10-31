import pytest
from app.nlp.entity_resolution import EntityResolver
from app.nlp.providers.deterministic_provider import DeterministicProvider
from app.nlp.temporal_parser import TemporalParser
from app.nlp.intent_schema import IntentSchema
from app.analytics.engine import analyze_player_batting
from app.insights.insight_generator import InsightGenerator
from app.core.config import settings
from app.ingestion.ingestion_service import ingest_file

@pytest.fixture(autouse=True)
def setup_fixture():
    fixture_path = settings.FIXTURES_DIR / "test_odi_1.json"
    ingest_file(fixture_path, force=True)

def test_resolve_player_identity():
    res_kohli = EntityResolver.resolve_player("kohli")
    assert "Kohli" in res_kohli.canonical_name

    res_rohit = EntityResolver.resolve_player("rohit")
    assert "Sharma" in res_rohit.canonical_name or "Rohit" in res_rohit.canonical_name

def test_nlp_parsing_single_player():
    prompt = "How has Virat Kohli performed against Australia in ODIs?"
    parsed = DeterministicProvider().interpret(prompt)
    assert "Virat Kohli" in parsed.players
    assert parsed.opponent == "Australia"
    assert parsed.format == "ODI"

def test_nlp_parsing_comparison():
    prompt = "Compare Rohit Sharma and Virat Kohli in T20 internationals"
    parsed = DeterministicProvider().interpret(prompt)
    assert "Rohit Sharma" in parsed.players
    assert "Virat Kohli" in parsed.players
    assert parsed.chart_preference in ["bar", "grouped_bar"]

def test_nlp_parsing_recent_n():
    parsed = TemporalParser.parse("Show Kohli's last 10 innings")
    assert parsed.last_n_innings == 10

def test_statistical_engine_calculations():
    res = analyze_player_batting("RG Sharma")
    m = res["metrics"]
    assert m["total_runs"] > 0
    assert m["player_name"] == "RG Sharma"
    assert "batting_average" in m
    assert "strike_rate" in m

@pytest.mark.asyncio
async def test_insight_generation():
    generator = InsightGenerator()
    intent = IntentSchema(
        intent="player_summary",
        players=["Rohit Sharma"],
        format="ODI"
    )
    metrics = [{
        "player_name": "Rohit Sharma",
        "total_runs": 1200,
        "batting_average": 54.5,
        "strike_rate": 92.4,
        "high_score": 117,
        "high_score_not_out": False,
        "innings_count": 25,
        "centuries": 4,
        "fifties": 6,
        "fours": 110,
        "sixes": 35,
        "std_deviation": 28.2,
        "consistency_rating": "Moderate",
        "boundary_runs": 650,
        "sample_size_adequate": True
    }]
    insight = await generator.generate(
        query="Show Rohit Sharma ODI performance",
        intent=intent,
        metrics=metrics,
        evidence=[],
        limitations=[]
    )
    assert "Rohit Sharma" in insight
    assert "1,200" in insight or "1200" in insight
