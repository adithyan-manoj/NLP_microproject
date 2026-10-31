import pytest
from app.services.career_records_service import CareerRecordsService
from app.insights.insight_generator import InsightGenerator
from app.nlp.intent_schema import IntentSchema
from app.retrieval.hybrid_search import HybridKnowledgeRetriever
from app.database.db import execute_query

def test_career_records_seeding_and_retrieval():
    """Verifies that player career records seed properly and retrieve all-time milestones."""
    count = CareerRecordsService.init_and_seed()
    assert count >= 15, "Expected at least 15 career milestone records to be seeded"

    # Test Rohit Sharma retrieval
    rohit_records = CareerRecordsService.get_career_milestones_for_player("Rohit Sharma")
    assert len(rohit_records) > 0
    odi_rec = next((r for r in rohit_records if r["format"] == "ODI"), None)
    assert odi_rec is not None
    assert odi_rec["high_score"] == 264
    assert "264 off 173 balls" in odi_rec["all_time_milestone"]

    # Test Don Bradman retrieval
    bradman_records = CareerRecordsService.get_career_milestones_for_player("Donald Bradman")
    assert len(bradman_records) > 0
    assert bradman_records[0]["batting_average"] == 99.94
    assert bradman_records[0]["high_score"] == 334

    # Test Virat Kohli retrieval
    kohli_records = CareerRecordsService.get_career_milestones_for_player("Virat Kohli", match_format="ODI")
    assert len(kohli_records) == 1
    assert kohli_records[0]["centuries"] == 50
    assert "50 centuries" in kohli_records[0]["all_time_milestone"]

def test_dual_lens_deterministic_explanation():
    """Verifies that deterministic explanation incorporates the all-time milestone note."""
    generator = InsightGenerator()
    intent = IntentSchema(
        intent="player_summary",
        players=["Rohit Sharma"],
        format="T20"
    )
    metrics = [{
        "player_name": "Rohit Sharma",
        "total_runs": 176,
        "batting_average": 44.0,
        "strike_rate": 128.5,
        "innings_count": 5,
        "centuries": 0,
        "fifties": 1,
        "high_score": 80,
        "high_score_not_out": True,
        "std_deviation": 31.8
    }]
    milestones = CareerRecordsService.get_career_milestones_for_player("Rohit Sharma", match_format="ODI")

    explanation = generator._generate_deterministic_explanation(intent, metrics, career_milestones=milestones)

    # Must contain both in-dataset numbers AND all-time world record note
    assert "Rohit Sharma has scored 176 runs" in explanation
    assert "highest score of 80*" in explanation
    assert "Note: In all-time international cricket, Rohit Sharma has a career high score of 264 in ODIs" in explanation
    assert "world record" in explanation

def test_dynamic_knowledge_caching_and_local_retrieval():
    """Verifies that verified insight facts are cached and retrieved locally via HybridKnowledgeRetriever."""
    generator = InsightGenerator()
    test_query = "What was the world record score of Rohit Sharma?"
    test_explanation = (
        "In the current dataset sample his high score is 80*. "
        "Note: In all-time international cricket, Rohit Sharma holds the world record score of 264 vs Sri Lanka in 2014."
    )

    generator._cache_verified_chunk(test_query, test_explanation, player_name="Rohit Sharma")

    # Verify DuckDB/PostgreSQL has the cached chunk
    df = execute_query("SELECT * FROM knowledge_chunks WHERE source_document = 'gemini_verified_cache';")
    assert not df.empty, "Expected cached chunk in knowledge_chunks"

    # Verify HybridKnowledgeRetriever finds it locally
    results = HybridKnowledgeRetriever.search("Rohit Sharma world record 264", top_k=5)
    assert len(results) > 0
    matched = any("264" in r.get("chunk_text", "") for r in results)
    assert matched, "Expected local RAG search to retrieve cached 264 milestone"
