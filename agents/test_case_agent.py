"""Test Scenario Planner and Test Case Generator agents."""

from __future__ import annotations

import json
import logging

from strands import Agent

from agents.utils import safe_structured_output
from models import RequirementAnalysis, TestCase, TestCaseCollection, TestScenarioPlan, WebsiteAnalysis
from prompts import (
    SCENARIO_PLANNER_PROMPT,
    TEST_CASE_GENERATOR_PROMPT,
    WEBSITE_SCENARIO_PLANNER_PROMPT,
    WEBSITE_TEST_CASE_GENERATOR_PROMPT,
)
from website_analyzer import website_analysis_summary

logger = logging.getLogger(__name__)


class ScenarioPlannerAgent:
    def __init__(self, model) -> None:
        self._agent = Agent(model=model, system_prompt=SCENARIO_PLANNER_PROMPT, name="ScenarioPlanner")
        self._website_agent = Agent(
            model=model, system_prompt=WEBSITE_SCENARIO_PLANNER_PROMPT, name="WebsiteScenarioPlanner"
        )

    def plan(self, requirement: str, analysis: RequirementAnalysis) -> TestScenarioPlan:
        logger.info("Scenario planning started")
        prompt = (
            f"Original requirement:\n{requirement.strip()}\n\n"
            f"Requirement analysis:\n{analysis.model_dump_json(indent=2)}\n\n"
            "Create comprehensive test scenarios."
        )
        result = safe_structured_output(self._agent, TestScenarioPlan, prompt)
        logger.info("Scenario planning completed: %d scenarios", len(result.scenarios))
        return result

    def plan_for_website(
        self,
        requirement: str,
        analysis: RequirementAnalysis,
        website: WebsiteAnalysis,
    ) -> TestScenarioPlan:
        logger.info("Website scenario planning started")
        summary = website_analysis_summary(website)
        prompt = (
            f"Synthesized requirement:\n{requirement.strip()}\n\n"
            f"Requirement analysis:\n{analysis.model_dump_json(indent=2)}\n\n"
            f"Discovered website elements:\n{json.dumps(summary, indent=2)}\n\n"
            "Create website-grounded test scenarios across all page sections."
        )
        result = safe_structured_output(self._website_agent, TestScenarioPlan, prompt)
        logger.info("Website scenario planning completed: %d scenarios", len(result.scenarios))
        return result


class TestCaseGeneratorAgent:
    def __init__(self, model) -> None:
        self._agent = Agent(model=model, system_prompt=TEST_CASE_GENERATOR_PROMPT, name="TestCaseGenerator")
        self._website_agent = Agent(
            model=model, system_prompt=WEBSITE_TEST_CASE_GENERATOR_PROMPT, name="WebsiteTestCaseGenerator"
        )

    def generate(
        self,
        requirement: str,
        analysis: RequirementAnalysis,
        scenario_plan: TestScenarioPlan,
        requested_count: int = 20,
    ) -> TestCaseCollection:
        logger.info("Test case generation started (requested=%d)", requested_count)
        prompt = (
            f"Original requirement:\n{requirement.strip()}\n\n"
            f"Requirement analysis:\n{analysis.model_dump_json(indent=2)}\n\n"
            f"Test scenarios:\n{json.dumps([s.model_dump() for s in scenario_plan.scenarios], indent=2)}\n\n"
            f"TARGET TEST CASE COUNT: Generate EXACTLY {requested_count} distinct test cases.\n"
            "Distribute test cases across Functional, Negative, Validation, UI, Edge Cases, Accessibility, and Security."
        )
        result = safe_structured_output(self._agent, TestCaseCollection, prompt)
        logger.info("Test case generation completed: %d test cases", len(result.test_cases))
        return result

    def generate_for_website(
        self,
        requirement: str,
        analysis: RequirementAnalysis,
        scenario_plan: TestScenarioPlan,
        website: WebsiteAnalysis,
        requested_count: int = 20,
    ) -> TestCaseCollection:
        logger.info("Website test case generation started (requested=%d)", requested_count)
        summary = website_analysis_summary(website)
        prompt = (
            f"Synthesized requirement:\n{requirement.strip()}\n\n"
            f"Requirement analysis:\n{analysis.model_dump_json(indent=2)}\n\n"
            f"Scenarios:\n{json.dumps([s.model_dump() for s in scenario_plan.scenarios], indent=2)}\n\n"
            f"Discovered full-page elements:\n{json.dumps(summary, indent=2)}\n\n"
            f"TARGET TEST CASE COUNT: Generate EXACTLY {requested_count} detailed, element-grounded test cases.\n"
            "Cover Navigation, Search, Forms, Buttons, Dropdowns, Cards, Tables, and Footers."
        )
        result = safe_structured_output(self._website_agent, TestCaseCollection, prompt)
        logger.info("Website test case generation completed: %d test cases", len(result.test_cases))
        return result

    def expand_for_website(
        self,
        requirement: str,
        analysis: RequirementAnalysis,
        scenario_plan: TestScenarioPlan,
        website: WebsiteAnalysis,
        existing_cases: list[TestCase],
        additional_needed: int,
    ) -> TestCaseCollection:
        logger.info("Expanding test cases for website (additional_needed=%d)", additional_needed)
        summary = website_analysis_summary(website)
        existing_titles = [tc.title for tc in existing_cases]
        prompt = (
            f"Context: We need {additional_needed} MORE unique test cases to reach the requested target count.\n\n"
            f"Existing Test Case Titles ({len(existing_titles)}):\n{json.dumps(existing_titles, indent=2)}\n\n"
            f"Discovered full-page elements:\n{json.dumps(summary, indent=2)}\n\n"
            f"Generate EXACTLY {additional_needed} NEW, unique, distinct test cases covering extra edge cases, "
            "accessibility, UI alignment, negative flows, boundary values, and footer/nav checks not already covered. "
            "Do NOT duplicate any existing titles."
        )
        result = safe_structured_output(self._website_agent, TestCaseCollection, prompt)
        return result
