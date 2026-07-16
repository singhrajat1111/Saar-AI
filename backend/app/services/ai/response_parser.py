import re
import json
import structlog
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = structlog.get_logger()

# Required top-level keys every AI response must contain
REQUIRED_FIELDS = {"title", "summary", "key_takeaway", "evidence", "limitations"}


class AIResponseParser:
    """
    Parses and validates LLM output before it is returned to the API layer.

    Responsibilities:
      1. Strip any wrapping markdown/code-block wrappers the LLM may add.
      2. Parse the result as structured JSON.
      3. Validate all required fields are present.
      4. Attempt a single repair pass if JSON is malformed.
      5. Raise ValueError if repair fails so the caller can fall back.

    All paths return a validated dict — never a plain string.
    """

    FALLBACK_STRUCT: Dict[str, Any] = {
        "title": "Analysis Explanation",
        "summary": (
            "An explanation could not be generated for this item. "
            "Please review the supporting evidence below."
        ),
        "key_takeaway": (
            "Unable to generate a key takeaway. Please review the dataset manually."
        ),
        "evidence": [],
        "limitations": (
            "No AI provider was available. This is a system-generated placeholder."
        ),
        "provider": "system",
        "generated_at": "",
    }

    @staticmethod
    def parse(raw_output: Optional[str], provider_name: str = "") -> Dict[str, Any]:
        """
        Parse and validate raw LLM output into a structured dict.

        Raises:
            ValueError: If the output cannot be parsed or repaired, so the caller
                        can retry or fall back to the Rule Engine.
        """
        if not raw_output or not raw_output.strip():
            logger.warn("response_parser_empty_output", provider=provider_name)
            raise ValueError("Provider returned an empty response.")

        text = raw_output.strip()

        # Strip wrapping code fences (```json ... ```, ```markdown ... ```, etc.)
        text = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
        text = text.strip()

        # Attempt direct JSON parse
        parsed = AIResponseParser._try_parse_json(text)

        # Attempt extraction/repair if direct parse failed
        if parsed is None:
            logger.warn(
                "response_parser_json_parse_failed_attempting_repair",
                provider=provider_name,
            )
            extracted = AIResponseParser._extract_json_object(text)
            if extracted:
                parsed = AIResponseParser._try_parse_json(extracted)

        if parsed is None:
            logger.error(
                "response_parser_repair_failed",
                provider=provider_name,
                raw_length=len(text),
            )
            raise ValueError(
                "Could not parse LLM response as JSON even after repair attempt."
            )

        if not isinstance(parsed, dict):
            raise ValueError(f"Parsed JSON is not a dict, got: {type(parsed)}")

        # Validate required fields
        missing = REQUIRED_FIELDS - set(parsed.keys())
        if missing:
            logger.warn(
                "response_parser_missing_fields",
                missing=list(missing),
                provider=provider_name,
            )
            raise ValueError(
                f"Structured response is missing required fields: {missing}"
            )

        # Normalise evidence array
        evidence = parsed.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        normalised_evidence = []
        for item in evidence:
            if isinstance(item, dict):
                normalised_evidence.append(
                    {
                        "label": str(item.get("label", "")),
                        "value": str(item.get("value", "")),
                        "source": item.get("source", "Python Statistical Engine"),
                    }
                )
        parsed["evidence"] = normalised_evidence

        # Inject metadata
        parsed["provider"] = provider_name or parsed.get("provider", "unknown")
        parsed["generated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(
            "response_parser_success",
            provider=provider_name,
            has_takeaway=bool(parsed.get("key_takeaway")),
        )
        return parsed

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Dict]:
        try:
            result = json.loads(text)
            return result if isinstance(result, dict) else None
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def _extract_json_object(text: str) -> Optional[str]:
        """Extract the first valid JSON object from surrounding prose."""
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None

    @staticmethod
    def build_fallback(provider_name: str = "rule_based_fallback") -> Dict[str, Any]:
        """Return a safe minimal fallback struct when all else fails."""
        fb = dict(AIResponseParser.FALLBACK_STRUCT)
        fb["provider"] = provider_name
        fb["generated_at"] = datetime.now(timezone.utc).isoformat()
        return fb
