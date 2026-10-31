import os
import time
import json
import asyncio
from typing import Optional, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings
from app.nlp.intent_schema import IntentSchema

class GeminiProvider:
    """
    Primary NLP Provider using official Google GenAI Python SDK with structured JSON output.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = settings.GEMINI_MODEL
        DUMMY_KEYS = {"", "YOUR_GEMINI_API_KEY_HERE", "your_gemini_api_key_here"}
        if self.api_key and self.api_key not in DUMMY_KEYS:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    @property
    def is_configured(self) -> bool:
        DUMMY_KEYS = {"", "YOUR_GEMINI_API_KEY_HERE", "your_gemini_api_key_here"}
        return bool(self.api_key and self.api_key not in DUMMY_KEYS and self._client)

    async def interpret_query(self, query: str, context: Optional[str] = None) -> Tuple[IntentSchema, float]:
        """
        Interprets natural language cricket query into canonical IntentSchema.
        Returns: (validated_intent_schema, latency_ms)
        """
        if not self.is_configured:
            raise ValueError("Gemini API key is not configured.")

        start_time = time.perf_counter()

        system_instruction = (
            "You are CricInsight's expert cricket query interpreter. "
            "Analyze user questions and extract structured intent, players, opponents, formats, and time windows. "
            "Follow these rules strictly:\n"
            "1. Cricket formats: 'IT20' is international T20; 'T20' is domestic league T20 (e.g. IPL). Never confuse them.\n"
            "2. 'ODI' is One Day International; 'Test' is Test matches.\n"
            "3. If multiple players are compared, set intent='comparison'.\n"
            "4. If recent form or sequence of innings is requested, set intent='recent_form' and extract last_n_innings.\n"
            "5. If opponent is mentioned (e.g. 'against Australia'), extract opponent.\n"
            "6. Output MUST strictly match the response schema with valid fields."
        )

        prompt = f"User query: {query}"
        if context:
            prompt += f"\nConversation Context: {context}"

        try:
            # Synchronous SDK call wrapped in async thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=IntentSchema,
                    temperature=0.0,
                ),
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raw_text = response.text or "{}"
            parsed = IntentSchema.model_validate_json(raw_text)
            return parsed, latency_ms

        except APIError as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raise e
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raise e
