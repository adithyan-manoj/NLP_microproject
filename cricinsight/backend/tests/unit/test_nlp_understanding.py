import pytest
from app.nlp.intent_schema import IntentSchema
from app.nlp.entity_resolution import EntityResolver
from app.nlp.temporal_parser import TemporalParser
from app.nlp.conversation_context import ConversationManager
from app.nlp.confidence import ConfidenceEvaluator
from app.nlp.providers.provider_manager import ProviderManager

def test_intent_schema_validation():
    # Valid schema creation
    schema = IntentSchema(
        intent="comparison",
        players=["Virat Kohli", "Rohit Sharma"],
        format="ODI",
        start_date="2022-01-01",
        metrics=["runs", "batting_average", "strike_rate"]
    )
    assert schema.intent == "comparison"
    assert len(schema.players) == 2
    assert schema.format == "ODI"
    assert schema.start_date == "2022-01-01"

    # Invalid date format should fail validation
    with pytest.raises(ValueError):
        IntentSchema(
            intent="player_summary",
            start_date="01/01/2022"  # not YYYY-MM-DD
        )

def test_format_normalization():
    assert EntityResolver.normalize_format("t20i") == "IT20"
    assert EntityResolver.normalize_format("T20 International") == "IT20"
    assert EntityResolver.normalize_format("t20") == "T20"  # strictly distinct!
    assert EntityResolver.normalize_format("odi") == "ODI"
    assert EntityResolver.normalize_format("test") == "Test"

def test_temporal_parser():
    # Innings window
    t1 = TemporalParser.parse("Show Kohli's last 5 innings as a line chart")
    assert t1.last_n_innings == 5
    assert t1.start_date is None

    # Date range
    t2 = TemporalParser.parse("How has Rohit performed since 2022 in ODIs?")
    assert t2.start_date == "2022-01-01"
    assert t2.last_n_innings is None

    # Matches window
    t3 = TemporalParser.parse("Kohli in his last 10 matches")
    assert t3.last_n_matches == 10

def test_conversation_coreference_resolution():
    conv_id = "test_conv_coref_1"
    ConversationManager.clear(conv_id)

    # Turn 1: User asks about Kohli
    t1_schema = IntentSchema(
        intent="player_summary",
        players=["Virat Kohli"],
        format="ODI"
    )
    t1_resolved = ConversationManager.resolve_follow_up(conv_id, t1_schema, "Show Kohli in ODIs")
    assert t1_resolved.players == ["Virat Kohli"]
    assert t1_resolved.format == "ODI"

    # Turn 2: User asks follow-up with pronoun "his"
    t2_schema = IntentSchema(
        intent="recent_form",
        players=[],  # LLM extracted no player name
        last_n_innings=5
    )
    t2_resolved = ConversationManager.resolve_follow_up(conv_id, t2_schema, "What about his last five innings?")
    assert t2_resolved.players == ["Virat Kohli"]
    assert t2_resolved.format == "ODI"  # inherited format
    assert t2_resolved.last_n_innings == 5

def test_confidence_scoring():
    # High confidence: resolved player, valid schema
    schema = IntentSchema(intent="player_summary", players=["Virat Kohli"], confidence=0.9)
    conf = ConfidenceEvaluator.evaluate(schema, schema_valid=True, resolved_player_count=1)
    assert conf.confidence_tier == "high"
    assert conf.overall_confidence >= 0.80

    # Low confidence: missing player
    schema_empty = IntentSchema(intent="player_summary", players=[], confidence=0.4)
    conf_low = ConfidenceEvaluator.evaluate(schema_empty, schema_valid=True, resolved_player_count=0)
    assert conf_low.confidence_tier == "low"
    assert conf_low.overall_confidence < 0.60

@pytest.mark.asyncio
async def test_provider_manager_fallback():
    manager = ProviderManager()
    # When API keys are not provided, it gracefully falls back to deterministic provider
    result = await manager.interpret("Compare Kohli and Rohit in ODIs since 2022")
    assert result.intent.intent == "comparison"
    assert "Virat Kohli" in result.intent.players
    assert "Rohit Sharma" in result.intent.players
    assert result.intent.format == "ODI"
    assert result.intent.start_date == "2022-01-01"
    assert result.provider_name in ["deterministic", "gemini", "qwen"]
