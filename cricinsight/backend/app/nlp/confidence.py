from typing import Optional, List
from pydantic import BaseModel
from app.nlp.intent_schema import IntentSchema

class ConfidenceBreakdown(BaseModel):
    overall_confidence: float
    model_confidence: float
    schema_valid: bool
    entity_resolution_score: float
    temporal_valid: bool
    confidence_tier: str  # "high", "medium", "low"
    explanation: str

class ConfidenceEvaluator:
    """
    Calibrated query-understanding confidence scoring system.
    Grounds confidence in measurable system checks rather than uncalibrated LLM self-reports.
    """

    @classmethod
    def evaluate(
        cls,
        intent_schema: IntentSchema,
        schema_valid: bool = True,
        resolved_player_count: int = 0,
        unresolved_players: Optional[List[str]] = None,
        is_ambiguous: bool = False,
        temporal_error: bool = False,
    ) -> ConfidenceBreakdown:
        model_conf = max(0.0, min(1.0, intent_schema.confidence))
        unresolved = unresolved_players or []

        # 1. Entity resolution score
        if intent_schema.intent in ["player_summary", "recent_form", "consistency"]:
            if not intent_schema.players:
                entity_score = 0.0
            elif unresolved:
                entity_score = 0.4
            elif is_ambiguous:
                entity_score = 0.5
            else:
                entity_score = 1.0
        elif intent_schema.intent == "comparison":
            if len(intent_schema.players) < 2:
                entity_score = 0.4
            elif unresolved:
                entity_score = 0.5
            elif is_ambiguous:
                entity_score = 0.6
            else:
                entity_score = 1.0
        else:
            entity_score = 0.85

        # 2. Temporal validity
        temporal_valid = not temporal_error
        temp_score = 1.0 if temporal_valid else 0.4

        # 3. Schema validity score
        schema_score = 1.0 if schema_valid else 0.0

        # 4. Calibrated overall score
        # 30% model, 40% entity resolution, 15% temporal, 15% schema
        overall = (
            (model_conf * 0.30) +
            (entity_score * 0.40) +
            (temp_score * 0.15) +
            (schema_score * 0.15)
        )
        overall = round(max(0.0, min(1.0, overall)), 3)

        # Penalize if ambiguous or clarification needed
        if is_ambiguous or intent_schema.needs_clarification:
            overall = min(overall, 0.65)

        # Categorize tier
        if overall >= 0.80 and not is_ambiguous:
            tier = "high"
            explanation = "High confidence: intent and entities verified against Cricsheet database."
        elif overall >= 0.50 or is_ambiguous:
            tier = "medium"
            explanation = "Medium confidence: entity resolution partial or clarification requested."
        else:
            tier = "low"
            explanation = "Low confidence: entities could not be resolved or query format unsupported."

        return ConfidenceBreakdown(
            overall_confidence=overall,
            model_confidence=model_conf,
            schema_valid=schema_valid,
            entity_resolution_score=entity_score,
            temporal_valid=temporal_valid,
            confidence_tier=tier,
            explanation=explanation,
        )
