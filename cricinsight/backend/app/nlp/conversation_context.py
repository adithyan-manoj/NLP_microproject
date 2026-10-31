from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from app.nlp.intent_schema import IntentSchema

@dataclass
class ConversationState:
    conversation_id: str
    active_players: List[str] = field(default_factory=list)
    active_opponent: Optional[str] = None
    active_format: Optional[str] = None
    active_competition: Optional[str] = None
    active_venue: Optional[str] = None
    active_start_date: Optional[str] = None
    active_end_date: Optional[str] = None
    active_last_n_innings: Optional[int] = None
    active_last_n_matches: Optional[int] = None
    active_metrics: List[str] = field(default_factory=lambda: ["runs", "batting_average", "strike_rate"])
    last_intent: Optional[str] = None

class ConversationManager:
    """
    Manages multi-turn conversation memory and coreference resolution.
    Retains context across turns (e.g. 'What about his last five innings?')
    without blindly reusing obsolete filters.
    """

    _sessions: Dict[str, ConversationState] = {}

    @classmethod
    def get_or_create(cls, conversation_id: str) -> ConversationState:
        if conversation_id not in cls._sessions:
            cls._sessions[conversation_id] = ConversationState(conversation_id=conversation_id)
        return cls._sessions[conversation_id]

    @classmethod
    def resolve_follow_up(cls, conversation_id: str, current: IntentSchema, raw_query: str) -> IntentSchema:
        """
        Merges existing conversation state with the new query interpretation.
        Resolves pronouns ('his', 'he', 'their') to active entities.
        """
        state = cls.get_or_create(conversation_id)
        q = raw_query.lower()

        # Check for coreference pronouns: "his", "him", "he", "this player"
        has_pronoun = any(p in q.split() for p in ["his", "him", "he", "her", "this", "they"]) or "this player" in q

        # If current has no players but pronoun exists and state has players
        if not current.players and has_pronoun and state.active_players:
            current.players = list(state.active_players)

        # If current has no format, inherit active format if format wasn't explicitly cleared
        if not current.format and state.active_format and not any(w in q for w in ["all formats", "overall"]):
            current.format = state.active_format

        # If user asks "what about his last 5 innings" -> inherit active opponent if not specified
        if not current.opponent and state.active_opponent and not any(w in q for w in ["all opponents", "overall"]):
            current.opponent = state.active_opponent

        # Update state with newly resolved dimensions
        if current.players:
            state.active_players = list(current.players)
        if current.format:
            state.active_format = current.format
        if current.opponent:
            state.active_opponent = current.opponent
        if current.venue:
            state.active_venue = current.venue
        if current.last_n_innings:
            state.active_last_n_innings = current.last_n_innings
        if current.intent:
            state.last_intent = current.intent

        return current

    @classmethod
    def clear(cls, conversation_id: str) -> None:
        if conversation_id in cls._sessions:
            del cls._sessions[conversation_id]
