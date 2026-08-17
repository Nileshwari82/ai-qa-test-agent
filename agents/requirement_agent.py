"""Requirement Analyzer agent."""

from __future__ import annotations

import logging

from strands import Agent

from agents.utils import safe_structured_output
from models import RequirementAnalysis
from prompts import REQUIREMENT_ANALYZER_PROMPT

logger = logging.getLogger(__name__)


class RequirementAnalyzerAgent:
    """Analyzes software requirements into structured QA metadata."""

    def __init__(self, model) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=REQUIREMENT_ANALYZER_PROMPT,
            name="RequirementAnalyzer",
        )

    def analyze(self, requirement: str) -> RequirementAnalysis:
        logger.info("Requirement analysis started")
        prompt = f"Analyze this software requirement:\n\n{requirement.strip()}"
        result = safe_structured_output(self._agent, RequirementAnalysis, prompt)
        logger.info("Requirement analysis completed: feature=%s", result.feature)
        return result
