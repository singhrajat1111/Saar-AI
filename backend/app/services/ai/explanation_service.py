import os
import hashlib
import json
import structlog
from typing import Dict, Any

from app.services.ai.cache import ai_cache
from app.services.ai.gemini import GeminiProvider
from app.services.ai.openai import OpenAIProvider
from app.services.ai.prompt_builder import (
    build_recommendation_prompt,
    build_chart_prompt,
    build_test_prompt,
    build_summary_prompt,
    build_quality_prompt,
    build_insight_prompt,
    build_report_prompt,
    build_presentation_prompt,
)
from app.services.ai.response_parser import AIResponseParser
from app.services.ai.rule_engine import RuleBasedExplainer

logger = structlog.get_logger()

# Maps explanation type strings to prompt builder functions
PROMPT_DISPATCH = {
    "recommendation": build_recommendation_prompt,
    "chart": build_chart_prompt,
    "statistical_test": build_test_prompt,
    "test": build_test_prompt,
    "executive_summary": build_summary_prompt,
    "quality_score": build_quality_prompt,
    "insight": build_insight_prompt,
    "report": build_report_prompt,
    "presentation": build_presentation_prompt,
}


class ExplanationService:
    """
    Unified orchestrator for AI explanations.

    Provider selection order (cascading fallback):
      1. Gemini (if GEMINI_API_KEY is set)
      2. OpenAI (if OPENAI_API_KEY is set and Gemini fails)
      3. Rule-Based Engine (deterministic, always available)

    All responses are structured dicts — never plain strings.
    Responses are cached by SHA-256 hash of (type, level, payload).
    """

    @staticmethod
    def get_cache_key(explanation_type: str, level: str, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True)
        raw = f"{explanation_type.lower().strip()}:{level.lower().strip()}:{serialized}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def explain(explanation_type: str, level: str, payload: Dict[str, Any], dataset_id: str | None = None) -> Dict[str, Any]:
        explanation_type = explanation_type.lower().strip()
        level = level.lower().strip()

        # ── 1. Cache check ────────────────────────────────────────────────────
        # Include dataset_id in cache key if provided
        serialized = json.dumps(payload, sort_keys=True)
        raw = f"{explanation_type.lower().strip()}:{level.lower().strip()}:{serialized}:{dataset_id or ''}"
        cache_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        cached = ai_cache.get(cache_key)
        if cached:
            logger.info("ai_explanation_cache_hit", type=explanation_type, level=level)
            result = cached if isinstance(cached, dict) else {"summary": cached}
            result["cached"] = True
            return result

        # Fetch rows count for reliability check
        rows_count = 0
        if dataset_id:
            try:
                from app.core.dataset_store import DatasetStore
                dataset = DatasetStore.get_dataset(dataset_id)
                if dataset:
                    rows_count = dataset.get("rows_count", 0)
            except Exception as e:
                logger.warn("failed_to_fetch_dataset_for_reliability_check", dataset_id=dataset_id, error=str(e))

        from app.core.reliability_helper import ReliabilityHelper
        assessment = ReliabilityHelper.assess(rows_count)

        # ── 2. Build prompt ───────────────────────────────────────────────────
        prompt_fn = PROMPT_DISPATCH.get(explanation_type, build_insight_prompt)
        prompt = prompt_fn(payload, level)

        if assessment.requires_caution():
            action_str = ", ".join(assessment.recommended_actions)
            warning_prompt = (
                f"\n\n[CRITICAL WARNING FOR AI]: This dataset has limited statistical reliability. "
                f"Reliability level: {assessment.level}. Explanation: {assessment.explanation} "
                f"You MUST explicitly explain these limitations in the 'summary' and 'limitations' fields, "
                f"emphasize that recommendations are based only on observable values, "
                f"avoid implying any confidence in statistical inferences, and recommend these actions: {action_str}"
            )
            prompt += warning_prompt

        # ── 3. Cascading provider execution ───────────────────────────────────
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        result: Dict[str, Any] | None = None

        # Try Gemini
        if gemini_key and result is None:
            result = ExplanationService._try_provider(
                GeminiProvider(gemini_key), prompt, "gemini"
            )

        # Try OpenAI if Gemini failed or unavailable
        if openai_key and result is None:
            result = ExplanationService._try_provider(
                OpenAIProvider(openai_key), prompt, "openai"
            )

        # Rule Engine as final fallback
        if result is None:
            logger.info("ai_explanation_using_rule_engine", type=explanation_type, level=level)
            result = RuleBasedExplainer.explain(explanation_type, level, payload)

        # Inject limitations into the response dict if dataset is not standard
        if assessment.requires_caution():
            orig_limitations = result.get("limitations", "")
            result["limitations"] = f"{assessment.explanation} {orig_limitations}".strip()
            
            summary_lower = result.get("summary", "").lower()
            if "limited sample size" not in summary_lower and "reliability" not in summary_lower:
                result["summary"] = (
                    f"{result.get('summary', '')} "
                    f"Please note: {assessment.explanation} Conclusions are strictly limited, and no reliable statistical inference should be made."
                ).strip()

        # ── 4. Cache and return ───────────────────────────────────────────────
        ai_cache.set(cache_key, result)
        result["cached"] = False
        return result

    @staticmethod
    def _try_provider(provider, prompt: str, provider_name: str) -> Dict[str, Any] | None:
        """
        Attempt to call a provider and parse the response.
        Returns a validated dict on success, None on any failure.
        Failure is logged but not re-raised (caller handles fallback).
        """
        try:
            raw_response = provider.generate_explanation(prompt)
            parsed = AIResponseParser.parse(raw_response, provider_name)
            logger.info("ai_provider_success", provider=provider_name)
            return parsed
        except ValueError as ve:
            # Structured validation failure (malformed JSON / missing fields)
            logger.warn(
                "ai_provider_structured_validation_failed",
                provider=provider_name,
                reason=str(ve),
            )
            return None
        except Exception as e:
            # Network error, quota, timeout, etc.
            logger.warn(
                "ai_provider_call_failed",
                provider=provider_name,
                error=str(e),
            )
            return None
