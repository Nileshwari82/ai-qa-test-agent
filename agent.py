"""Main orchestrator for QA Agent Pro workflows."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from agents.functionality_agent import FunctionalityDetectorAgent
from agents.report_agent import ReportAgent
from agents.requirement_agent import RequirementAnalyzerAgent
from agents.test_case_agent import ScenarioPlannerAgent, TestCaseGeneratorAgent
from agents.validation_agent import CoverageValidatorAgent, RiskAnalyzerAgent
from agents.website_agent import WebsiteAnalyzerAgent
from browser_checks import run_safe_browser_checks
from config import create_model, validate_configuration
from models import CoverageBreakdown, QAReport, ReportHistoryItem, RiskItem, WebsiteAnalysis
from validators import calculate_category_coverage, calculate_coverage
from website_analyzer import WebsiteInspector

logger = logging.getLogger(__name__)


class WorkflowStep(str, Enum):
    ANALYZING = "Analyzing Requirement..."
    PLANNING = "Planning Test Scenarios..."
    GENERATING = "Generating Test Cases..."
    RISK_ANALYSIS = "Checking Edge Cases & Risks..."
    VALIDATING = "Validating Coverage..."
    REPORT = "Preparing QA Report..."


class WebsiteWorkflowStep(str, Enum):
    URL_VALIDATED = "Starting URL validated"
    WEBSITE_LOADED = "Website accessed"
    CRAWLING_PAGES = "Discovering & crawling internal pages"
    BUILDING_SITEMAP = "Building website sitemap"
    ANALYZING_PAGES = "Analyzing page DOM & full-page screenshots"
    DETECTING_FUNCS = "Grouping elements into page functionalities"
    FEATURE_UNDERSTANDING = "Synthesizing website test requirements"
    SCENARIO_PLANNING = "Generating test scenarios"
    TEST_GENERATION = "Generating page-by-page test cases"
    EXPANDING_CASES = "Validating test case distribution & coverage"
    RISK_ANALYSIS = "Performing risk analysis & edge cases"
    VALIDATING = "Validating test coverage"
    REPORT_READY = "Complete Website QA Report ready"


AGENT_ACTIVITY = [
    ("Website Discovery Agent", "website"),
    ("Page Analysis Agent", "page_analysis"),
    ("Functionality Detector Agent", "functionality"),
    ("Scenario Planner Agent", "scenario"),
    ("Test Case Generator Agent", "testcase"),
    ("QA Validator Agent", "validator"),
    ("Report Agent", "report"),
]


@dataclass
class WorkflowProgress:
    step: str
    message: str = ""


ProgressCallback = Callable[[WorkflowProgress], None]


class QATestCaseOrchestrator:
    def __init__(self) -> None:
        self._model = None
        self._requirement_agent = None
        self._website_agent = None
        self._functionality_agent = None
        self._scenario_agent = None
        self._test_case_agent = None
        self._risk_agent = None
        self._validator_agent = None
        self._report_agent = None
        self._inspector = WebsiteInspector()

    def _ensure_agents(self) -> None:
        if self._model is None:
            self._model = create_model()
            self._requirement_agent = RequirementAnalyzerAgent(self._model)
            self._website_agent = WebsiteAnalyzerAgent(self._model)
            self._functionality_agent = FunctionalityDetectorAgent(self._model)
            self._scenario_agent = ScenarioPlannerAgent(self._model)
            self._test_case_agent = TestCaseGeneratorAgent(self._model)
            self._risk_agent = RiskAnalyzerAgent(self._model)
            self._validator_agent = CoverageValidatorAgent(self._model)
            self._report_agent = ReportAgent(self._model)

    @staticmethod
    def check_configuration() -> tuple[bool, str]:
        return validate_configuration()

    def _build_report(
        self,
        *,
        mode: str,
        source: str,
        requirement: str,
        analysis,
        scenario_plan,
        test_cases,
        risk_analysis,
        validation_result,
        coverage_validation,
        website_analysis=None,
        website_understanding=None,
        browser_checks=None,
        website_element_count=0,
        requested_test_cases=20,
        generated_test_cases=0,
        generation_note="",
    ) -> QAReport:
        categories = calculate_category_coverage(
            test_cases.test_cases, scenario_plan.scenarios, website_element_count
        )
        breakdown = CoverageBreakdown(
            overall=categories["overall"],
            functional=categories["functional"],
            validation=categories["validation"],
            ui=categories["ui"],
            negative=categories["negative"],
            edge_cases=categories["edge_cases"],
            security_suggestions=categories["security_suggestions"],
            is_estimated=False,
            label="Programmatic coverage (category-weighted)",
        )
        risk_items = risk_analysis.risk_items or [
            RiskItem(risk=r, severity="Medium", reason="Identified during analysis", recommendation="Review")
            for r in risk_analysis.risks
        ]
        
        # Gather all functionalities
        all_funcs = []
        if website_analysis:
            all_funcs = website_analysis.all_functionalities

        return QAReport(
            mode=mode,  # type: ignore[arg-type]
            source=source,
            requirement=requirement,
            requirement_analysis=analysis,
            website_analysis=website_analysis,
            website_understanding=website_understanding,
            page_analyses=website_analysis.page_analyses if website_analysis else [],
            functionalities=all_funcs,
            sitemap=website_analysis.sitemap if website_analysis else [],
            test_scenarios=scenario_plan.scenarios,
            test_cases=test_cases.test_cases,
            edge_cases=list(dict.fromkeys(risk_analysis.edge_cases)),
            risks=risk_analysis.risks,
            risk_items=risk_items,
            coverage_score=categories["overall"],
            coverage_breakdown=breakdown,
            coverage_explanation=coverage_validation.coverage_explanation,
            missing_areas=list(dict.fromkeys(coverage_validation.missing_areas + validation_result.issues)),
            recommendations=list(
                dict.fromkeys(
                    risk_analysis.recommendations
                    + coverage_validation.recommendations
                    + risk_analysis.missing_validations
                )
            ),
            validation_details={
                "checks": {
                    "positive_cases_covered": validation_result.positive_cases_covered,
                    "negative_cases_covered": validation_result.negative_cases_covered,
                    "edge_cases_covered": validation_result.edge_cases_covered,
                    "validation_cases_covered": validation_result.validation_cases_covered,
                    "security_cases_relevant": validation_result.security_cases_relevant,
                    "no_duplicate_ids": validation_result.no_duplicate_ids,
                    "expected_results_clear": validation_result.expected_results_clear,
                    "requirement_sufficiently_covered": validation_result.requirement_sufficiently_covered,
                },
                "details": validation_result.details,
            },
            browser_checks=browser_checks or [],
            requested_test_cases=requested_test_cases,
            generated_test_cases=generated_test_cases,
            generation_note=generation_note,
        )

    def run(
        self,
        requirement: str,
        requested_test_cases: int = 20,
        on_progress: ProgressCallback | None = None,
    ) -> QAReport:
        requirement = requirement.strip()
        if not requirement:
            raise ValueError("Requirement cannot be empty.")
        self._ensure_agents()

        def notify(step: WorkflowStep) -> None:
            if on_progress:
                on_progress(WorkflowProgress(step=step.value))

        notify(WorkflowStep.ANALYZING)
        analysis = self._requirement_agent.analyze(requirement)
        notify(WorkflowStep.PLANNING)
        scenario_plan = self._scenario_agent.plan(requirement, analysis)
        notify(WorkflowStep.GENERATING)
        
        target_count = max(1, min(requested_test_cases, 100))
        test_cases = self._test_case_agent.generate(requirement, analysis, scenario_plan, requested_count=target_count)
        
        generated_count = len(test_cases.test_cases)
        note = "✓ Requested test cases generated successfully." if generated_count >= target_count else f"Generated {generated_count}进行中 distinct test cases for the requirement."

        notify(WorkflowStep.RISK_ANALYSIS)
        risk_analysis = self._risk_agent.analyze(requirement, analysis, scenario_plan, test_cases)
        notify(WorkflowStep.VALIDATING)
        validation_result = calculate_coverage(test_cases.test_cases, scenario_plan.scenarios, analysis)
        coverage_validation = self._validator_agent.validate(
            requirement, analysis, scenario_plan, test_cases, risk_analysis,
            validation_result.coverage_score, validation_result.details,
        )
        notify(WorkflowStep.REPORT)
        return self._build_report(
            mode="requirement", source=requirement, requirement=requirement,
            analysis=analysis, scenario_plan=scenario_plan, test_cases=test_cases,
            risk_analysis=risk_analysis, validation_result=validation_result,
            coverage_validation=coverage_validation,
            requested_test_cases=requested_test_cases,
            generated_test_cases=generated_count,
            generation_note=note,
        )

    def run_website(
        self,
        url: str,
        max_pages: int = 5,
        requested_test_cases: int = 20,
        analysis_options: dict | None = None,
        on_progress: ProgressCallback | None = None,
        run_browser_checks: bool = False,
    ) -> QAReport:
        self._ensure_agents()
        analysis_options = analysis_options or {}

        def notify(step: WebsiteWorkflowStep, message: str = "") -> None:
            if on_progress:
                on_progress(WorkflowProgress(step=step.value, message=message))

        notify(WebsiteWorkflowStep.URL_VALIDATED, f"Validating starting URL: {url}")
        
        def page_crawled_callback(page_url: str, current: int, total: int):
            notify(WebsiteWorkflowStep.CRAWLING_PAGES, f"Crawling page {current}/{total}: {page_url}")

        website: WebsiteAnalysis = self._inspector.analyze(
            url,
            max_pages=max_pages,
            options=analysis_options,
            on_page_callback=page_crawled_callback
        )
        if not website.accessible:
            raise ValueError(website.access_message or "Unable to access the website for analysis.")

        notify(WebsiteWorkflowStep.WEBSITE_LOADED, f"Loaded {website.pages_analyzed} pages")
        notify(WebsiteWorkflowStep.BUILDING_SITEMAP, f"Built sitemap with {website.pages_discovered} discovered pages")
        notify(WebsiteWorkflowStep.ANALYZING_PAGES, "Extracted DOM structure and full-page screenshots")

        # Step 3: Run Functionality Detection Agent on each analyzed page
        notify(WebsiteWorkflowStep.DETECTING_FUNCS, "Grouping page elements into functionalities...")
        all_funcs = []
        for page_data in website.page_analyses:
            if page_data.status in {"Analyzed", "Partially Analyzed"}:
                funcs_col = self._functionality_agent.detect(page_data)
                page_data.functionalities = funcs_col.functionalities
                all_funcs.extend(funcs_col.functionalities)

        website.all_functionalities = all_funcs
        website.total_functionalities_count = len(all_funcs)

        notify(WebsiteWorkflowStep.FEATURE_UNDERSTANDING, "Synthesizing website test requirements...")
        understanding = self._website_agent.analyze(website)
        requirement = understanding.synthesized_requirement or (
            f"Test the website at {website.url} across all {website.pages_analyzed} discovered pages and {website.total_functionalities_count} functionalities."
        )

        analysis = self._requirement_agent.analyze(requirement)
        notify(WebsiteWorkflowStep.SCENARIO_PLANNING, "Generating test scenarios across all pages...")
        scenario_plan = self._scenario_agent.plan_for_website(requirement, analysis, website)
        
        target_count = max(1, min(requested_test_cases, 200))
        notify(WebsiteWorkflowStep.TEST_GENERATION, f"Generating {target_count} test cases distributed by page...")
        test_cases = self._test_case_agent.generate_for_website(
            requirement, analysis, scenario_plan, website, requested_count=target_count
        )

        # Ensure every test_case has page_title, page_url, and functionality populated
        if website.page_analyses:
            default_page = website.page_analyses[0]
            default_title = default_page.title
            default_url = default_page.url
            default_func = default_page.functionalities[0].name if default_page.functionalities else "General"

            for i, tc in enumerate(test_cases.test_cases):
                if not tc.page_url:
                    # Assign round-robin to discovered pages
                    assigned_page = website.page_analyses[i % len(website.page_analyses)]
                    tc.page_url = assigned_page.url
                    tc.page_title = assigned_page.title
                    if assigned_page.functionalities:
                        tc.functionality = assigned_page.functionalities[i % len(assigned_page.functionalities)].name
                    else:
                        tc.functionality = "General"
                if not tc.functionality or tc.functionality == "General":
                    # Try to match from title
                    for func in all_funcs:
                        if func.name.lower() in tc.title.lower() or func.name.lower() in tc.test_objective.lower():
                            tc.functionality = func.name
                            break

        # Expansion loop if initial pass falls short of target_count
        current_list = list(test_cases.test_cases)
        max_attempts = 2
        attempt = 0
        while len(current_list) < target_count and attempt < max_attempts:
            attempt += 1
            needed = target_count - len(current_list)
            notify(WebsiteWorkflowStep.EXPANDING_CASES, f"Expanding test cases ({len(current_list)}/{target_count})...")
            extra = self._test_case_agent.expand_for_website(
                requirement, analysis, scenario_plan, website, current_list, needed
            )
            if not extra.test_cases:
                break
            existing_titles = {tc.title.strip().lower() for tc in current_list}
            added = 0
            for new_tc in extra.test_cases:
                if new_tc.title.strip().lower() not in existing_titles:
                    new_tc.test_case_id = f"TC{len(current_list) + 1:02d}"
                    assigned_page = website.page_analyses[len(current_list) % len(website.page_analyses)]
                    if not new_tc.page_url:
                        new_tc.page_url = assigned_page.url
                        new_tc.page_title = assigned_page.title
                        new_tc.functionality = assigned_page.functionalities[0].name if assigned_page.functionalities else "General"
                    current_list.append(new_tc)
                    existing_titles.add(new_tc.title.strip().lower())
                    added += 1
                if len(current_list) >= target_count:
                    break
            if added == 0:
                break

        test_cases.test_cases = current_list
        generated_count = len(current_list)
        website.requested_test_cases = requested_test_cases
        website.generated_test_cases = generated_count

        if generated_count >= requested_test_cases:
            note = f"✓ All {generated_count} requested test cases generated successfully across {website.pages_analyzed} pages."
        else:
            note = f"Generated {generated_count} out of {requested_test_cases} requested. All {website.pages_discovered} pages discovered within the configured crawl limit were analyzed."
        website.generation_note = note

        notify(WebsiteWorkflowStep.RISK_ANALYSIS, "Evaluating risks and edge cases...")
        risk_analysis = self._risk_agent.analyze(
            requirement, analysis, scenario_plan, test_cases, website=website
        )
        notify(WebsiteWorkflowStep.VALIDATING, "Calculating page-by-page test coverage...")
        element_count = website.interactive_elements_count or (len(website.buttons) + len(website.inputs) + len(website.forms))
        validation_result = calculate_coverage(test_cases.test_cases, scenario_plan.scenarios, analysis)
        coverage_validation = self._validator_agent.validate(
            requirement, analysis, scenario_plan, test_cases, risk_analysis,
            validation_result.coverage_score, validation_result.details,
        )
        browser_checks = run_safe_browser_checks(website, test_cases.test_cases) if run_browser_checks else []
        notify(WebsiteWorkflowStep.REPORT_READY, "Complete Website QA Report successfully generated.")
        return self._build_report(
            mode="website", source=website.url, requirement=requirement,
            analysis=analysis, scenario_plan=scenario_plan, test_cases=test_cases,
            risk_analysis=risk_analysis, validation_result=validation_result,
            coverage_validation=coverage_validation, website_analysis=website,
            website_understanding=understanding, browser_checks=browser_checks,
            website_element_count=element_count,
            requested_test_cases=requested_test_cases,
            generated_test_cases=generated_count,
            generation_note=note,
        )


def make_history_item(report: QAReport) -> ReportHistoryItem:
    high_risks = sum(1 for r in report.risk_items if r.severity == "High")
    risk_level = "High" if high_risks >= 2 else ("Medium" if high_risks else "Low")
    return ReportHistoryItem(
        id=str(uuid.uuid4())[:8],
        mode=report.mode,
        title=report.display_title(),
        source=report.source,
        test_case_count=len(report.test_cases),
        coverage_score=report.coverage_score,
        risk_level=risk_level,
        status="Completed",
    )
