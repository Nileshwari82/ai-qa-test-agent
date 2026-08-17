"""Edge Case / Risk Analyzer and Coverage Validator agents."""

from __future__ import annotations

import json
import logging

from strands import Agent

from agents.utils import safe_structured_output
from models import (
    CoverageValidation,
    RequirementAnalysis,
    RiskAnalysis,
    RiskItem,
    TestCaseCollection,
    TestScenarioPlan,
    WebsiteAnalysis,
)
from prompts import COVERAGE_VALIDATOR_PROMPT, RISK_ANALYZER_PROMPT, WEBSITE_RISK_ANALYZER_PROMPT
from tools import calculate_coverage_score, validate_test_cases
from website_analyzer import website_analysis_summary

logger = logging.getLogger(__name__)


class RiskAnalyzerAgent:
    def __init__(self, model) -> None:
        self._agent = Agent(model=model, system_prompt=RISK_ANALYZER_PROMPT, name="RiskAnalyzer")
        self._website_agent = Agent(
            model=model, system_prompt=WEBSITE_RISK_ANALYZER_PROMPT, name="WebsiteRiskAnalyzer"
        )

    def analyze(
        self,
        requirement: str,
        analysis: RequirementAnalysis,
        scenario_plan: TestScenarioPlan,
        test_cases: TestCaseCollection,
        website: WebsiteAnalysis | None = None,
    ) -> RiskAnalysis:
        logger.info("Risk analysis started")
        website_block = ""
        if website:
            website_block = (
                f"\nDiscovered website data:\n{json.dumps(website_analysis_summary(website), indent=2)}\n"
            )
        prompt = (
            f"Context:\n{requirement.strip()}\n\n"
            f"Requirement analysis:\n{analysis.model_dump_json(indent=2)}\n\n"
            f"Scenarios:\n{json.dumps([s.model_dump() for s in scenario_plan.scenarios], indent=2)}\n\n"
            f"Test cases:\n{json.dumps([tc.model_dump() for tc in test_cases.test_cases], indent=2)}"
            f"{website_block}\n\nIdentify edge cases, risks, and recommendations."
        )
        agent = self._website_agent if website else self._agent
        result = safe_structured_output(agent, RiskAnalysis, prompt)
        if not result.risk_items and result.risks:
            result.risk_items = [
                RiskItem(
                    risk=risk,
                    severity="Medium",
                    reason="Identified during analysis",
                    recommendation="Review and add targeted test cases",
                )
                for risk in result.risks
            ]
        logger.info("Risk analysis completed")
        return result


class CoverageValidatorAgent:
    def __init__(self, model) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=COVERAGE_VALIDATOR_PROMPT,
            tools=[validate_test_cases, calculate_coverage_score],
            name="CoverageValidator",
        )

    def validate(
        self,
        requirement: str,
        analysis: RequirementAnalysis,
        scenario_plan: TestScenarioPlan,
        test_cases: TestCaseCollection,
        risk_analysis: RiskAnalysis,
        programmatic_score: float,
        programmatic_details: dict,
    ) -> CoverageValidation:
        logger.info("Coverage validation started (score=%.1f)", programmatic_score)
        prompt = (
            f"Context:\n{requirement.strip()}\n\n"
            f"Scenarios: {len(scenario_plan.scenarios)} | Test cases: {len(test_cases.test_cases)}\n\n"
            f"Risk analysis:\n{risk_analysis.model_dump_json(indent=2)}\n\n"
            f"Programmatic score: {programmatic_score:.1f}%\n"
            f"Details:\n{json.dumps(programmatic_details, indent=2)}\n\n"
            "Use tools to verify, then provide missing areas and recommendations."
        )
        return safe_structured_output(self._agent, CoverageValidation, prompt)
