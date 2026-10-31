import time
import json
from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.nlp.intent_schema import IntentSchema

class QwenProvider:
    """
    Local NLP Fallback Provider using Qwen running on local Ollama instance (RTX 4050 GPU).
    Enforces the identical canonical IntentSchema JSON schema.
    """

    def __init__(self):
        self.base_url = settings.QWEN_BASE_URL.rstrip("/")
        self.model_name = settings.QWEN_MODEL
        self.timeout = float(settings.QWEN_TOTAL_TIMEOUT)

    async def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable and responding."""
        try:
            async with httpx.AsyncClient(timeout=0.3) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def interpret_query(self, query: str, context: Optional[str] = None) -> Tuple[IntentSchema, float]:
        """
        Interprets cricket questions locally via Ollama.
        Returns: (validated_intent_schema, latency_ms)
        """
        start_time = time.perf_counter()

        system_prompt = (
            "You are CricInsight's local cricket query parser. Extract structured intent, players, opponents, "
            "formats, and time windows. Format 'IT20' is international T20; 'T20' is domestic league. "
            "Return valid JSON matching the schema."
        )
        user_prompt = f"Question: {query}"
        if context:
            user_prompt += f"\nContext: {context}"

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": IntentSchema.model_json_schema(),
            "options": {
                "temperature": 0.0,
                "num_ctx": settings.QWEN_CONTEXT_LENGTH,
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            data = resp.json()
            raw_response = data.get("response", "{}")
            parsed = IntentSchema.model_validate_json(raw_response)
            return parsed, latency_ms
