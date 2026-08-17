"""Utility helper for safe structured output from agents."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from models import TestCaseCollection, TestScenarioPlan

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def safe_structured_output(agent: Any, output_model: Type[T], prompt: str, max_retries: int = 3) -> T:
    """Safely get structured output from a Strands agent with exponential backoff retries and fallbacks."""
    for attempt in range(max_retries):
        # Strategy 1: agent(prompt, structured_output_model=output_model)
        try:
            res = agent(prompt, structured_output_model=output_model)
            val = getattr(res, "structured_output", res)
            if isinstance(val, output_model):
                if isinstance(val, TestCaseCollection) and len(val.test_cases) > 0:
                    return val
                elif isinstance(val, TestScenarioPlan) and len(val.scenarios) > 0:
                    return val
                elif not isinstance(val, (TestCaseCollection, TestScenarioPlan)):
                    return val
        except Exception as exc:
            err_str = str(exc)
            if any(term in err_str for term in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded", "Rate limit"]):
                wait_time = 2.0 * (attempt + 1)
                logger.warning("Rate limit hit (429). Retrying in %.1fs (attempt %d/%d)...", wait_time, attempt + 1, max_retries)
                time.sleep(wait_time)
                continue
            logger.warning("structured_output_model call failed: %s", exc)

        # Strategy 2: Agent.structured_output(output_model, prompt)
        try:
            res = agent.structured_output(output_model, prompt)
            if isinstance(res, output_model):
                if isinstance(res, TestCaseCollection) and len(res.test_cases) > 0:
                    return res
                elif isinstance(res, TestScenarioPlan) and len(res.scenarios) > 0:
                    return res
                elif not isinstance(val if 'val' in locals() else res, (TestCaseCollection, TestScenarioPlan)):
                    return res
        except Exception as exc:
            err_str = str(exc)
            if any(term in err_str for term in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded", "Rate limit"]):
                wait_time = 2.0 * (attempt + 1)
                logger.warning("Rate limit hit (429). Retrying in %.1fs (attempt %d/%d)...", wait_time, attempt + 1, max_retries)
                time.sleep(wait_time)
                continue
            logger.warning("legacy structured_output method failed: %s", exc)

        # Strategy 3: Text completion and JSON extraction
        try:
            text_prompt = (
                f"{prompt}\n\n"
                "IMPORTANT: Output ONLY a valid raw JSON object matching the target schema. "
                "Do not include any explanation or markdown formatting outside of the JSON block."
            )
            res = agent(text_prompt)
            text_content = ""
            if hasattr(res, "message") and isinstance(res.message, dict):
                content = res.message.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            text_content += item["text"]
                elif isinstance(content, str):
                    text_content = content
            if not text_content:
                text_content = str(res)

            cleaned = text_content.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            parsed = json.loads(cleaned)
            return output_model.model_validate(parsed)
        except Exception as exc:
            err_str = str(exc)
            if any(term in err_str for term in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded", "Rate limit"]) and attempt < max_retries - 1:
                wait_time = 2.5 * (attempt + 1)
                logger.warning("Rate limit hit on fallback (429). Retrying in %.1fs...", wait_time)
                time.sleep(wait_time)
                continue
            logger.error("Text fallback for structured output failed: %s", exc)

        break

    return output_model.model_validate({})
