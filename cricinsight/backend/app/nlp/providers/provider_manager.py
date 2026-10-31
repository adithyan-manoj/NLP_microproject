import time
import asyncio
import uuid
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from app.core.config import settings
from app.nlp.intent_schema import IntentSchema
from app.nlp.providers.gemini_provider import GeminiProvider
from app.nlp.providers.qwen_provider import QwenProvider
from app.nlp.providers.deterministic_provider import DeterministicProvider

@dataclass
class ProviderExecutionResult:
    intent: IntentSchema
    provider_name: str
    model_name: str
    latency_ms: float
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    error_category: Optional[str] = None

class CircuitBreaker:
    """Tracks consecutive failures to avoid repeated slow timeouts on down providers."""
    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False

    def record_success(self):
        self.failure_count = 0
        self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True

    def can_attempt(self) -> bool:
        if not self.is_open:
            return True
        # Check if reset timeout elapsed
        if time.time() - self.last_failure_time > self.reset_timeout_sec:
            self.is_open = False
            self.failure_count = 0
            return True
        return False

class ProviderManager:
    """
    Centralized NLP Provider Orchestrator managing:
    Gemini (Primary) -> Qwen Ollama (Local Fallback) -> Deterministic (Resilience).
    Enforces overall deadline <= 32s and records observability telemetry.
    """

    def __init__(self):
        self.gemini = GeminiProvider()
        self.qwen = QwenProvider()
        self.gemini_circuit = CircuitBreaker()
        self.qwen_circuit = CircuitBreaker()
        self.max_deadline = float(settings.LLM_MAX_TOTAL_DEADLINE)

    async def interpret(
        self,
        query: str,
        context: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ProviderExecutionResult:
        req_id = request_id or str(uuid.uuid4())
        start_overall = time.perf_counter()

        fallback_used = False
        fallback_reason = None

        # Determine order of LLMs based on settings
        primary = settings.LLM_PRIMARY_PROVIDER.lower()

        async def _try_qwen(reason_prefix: str = "") -> Optional[ProviderExecutionResult]:
            if not self.qwen_circuit.can_attempt():
                return None
            remaining_time = max(1.0, self.max_deadline - (time.perf_counter() - start_overall))
            qwen_timeout = min(float(settings.QWEN_TOTAL_TIMEOUT), remaining_time)
            if await self.qwen.is_available():
                try:
                    intent, latency = await asyncio.wait_for(
                        self.qwen.interpret_query(query, context),
                        timeout=qwen_timeout
                    )
                    self.qwen_circuit.record_success()
                    return ProviderExecutionResult(
                        intent=intent,
                        provider_name="qwen",
                        model_name=self.qwen.model_name,
                        latency_ms=latency,
                        fallback_used=bool(reason_prefix),
                        fallback_reason=reason_prefix if reason_prefix else None,
                    )
                except asyncio.TimeoutError:
                    self.qwen_circuit.record_failure()
                except Exception as e:
                    self.qwen_circuit.record_failure()
            return None

        async def _try_gemini(reason_prefix: str = "") -> Optional[ProviderExecutionResult]:
            if not self.gemini.is_configured or not self.gemini_circuit.can_attempt():
                return None
            remaining_time = max(1.0, self.max_deadline - (time.perf_counter() - start_overall))
            gemini_timeout = min(float(settings.GEMINI_TOTAL_TIMEOUT), remaining_time)
            try:
                intent, latency = await asyncio.wait_for(
                    self.gemini.interpret_query(query, context),
                    timeout=gemini_timeout
                )
                self.gemini_circuit.record_success()
                return ProviderExecutionResult(
                    intent=intent,
                    provider_name="gemini",
                    model_name=self.gemini.model_name,
                    latency_ms=latency,
                    fallback_used=bool(reason_prefix),
                    fallback_reason=reason_prefix if reason_prefix else None,
                )
            except asyncio.TimeoutError:
                self.gemini_circuit.record_failure()
            except Exception as e:
                self.gemini_circuit.record_failure()
            return None

        # 1. Primary Attempt
        if primary == "qwen":
            res = await _try_qwen()
            if res:
                return res
            fallback_used = True
            fallback_reason = "Qwen local daemon offline or timed out; failover to Gemini"
            if settings.LLM_FALLBACK_ENABLED:
                res = await _try_gemini(reason_prefix=fallback_reason)
                if res:
                    return res
                fallback_reason += "; Gemini fallback unavailable"
        else:
            res = await _try_gemini()
            if res:
                return res
            fallback_used = True
            fallback_reason = "Gemini unavailable; failover to Qwen"
            if settings.LLM_FALLBACK_ENABLED:
                res = await _try_qwen(reason_prefix=fallback_reason)
                if res:
                    return res
                fallback_reason += "; Qwen fallback unavailable"

        # 3. Deterministic Fallback: Guarantees reliable operation without LLMs
        intent, latency = DeterministicProvider.interpret_query(query)
        return ProviderExecutionResult(
            intent=intent,
            provider_name="deterministic",
            model_name="rule_based",
            latency_ms=latency,
            fallback_used=True,
            fallback_reason=fallback_reason or "Offline resilience mode",
        )
