"""Extended Pydantic models for QA Agent Pro."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class RequirementAnalysis(BaseModel):
    feature: str = Field(default="General Feature", description="Primary feature being tested")
    actors: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    expected_behavior: str = Field(default="Expected behavior", description="Expected system behavior")
    preconditions: list[str] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                return json.loads(cleaned)
            except Exception:
                return {}
        return v


class TestScenario(BaseModel):
    scenario_id: str = "TS01"
    title: str = "Test Scenario"
    category: str = "Functional"
    description: str = ""
    module: str = "General"


class TestScenarioPlan(BaseModel):
    scenarios: list[TestScenario] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {"scenarios": []}
        if isinstance(v, list):
            return {"scenarios": v}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                if isinstance(data, list):
                    return {"scenarios": data}
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
            return {"scenarios": []}
        return v


class TestCase(BaseModel):
    test_case_id: str = "TC01"
    test_scenario_id: str = "TS01"
    title: str = "Test Case"
    page_title: str = ""
    page_url: str = ""
    functionality: str = "General"
    preconditions: str = ""
    test_data: str = ""
    steps: list[str] = Field(default_factory=list)
    expected_result: str = ""
    priority: str = "Medium"
    test_type: str = "Functional"
    module: str = "General"
    category: str = "Functional"
    status: str = "Not Executed"
    automation_potential: str = "Medium"
    risk_level: str = "Low"
    test_objective: str = ""


class TestCaseCollection(BaseModel):
    test_cases: list[TestCase] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {"test_cases": []}
        if isinstance(v, list):
            return {"test_cases": v}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                if isinstance(data, list):
                    return {"test_cases": data}
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
            return {"test_cases": []}
        return v


class RiskItem(BaseModel):
    risk: str = ""
    severity: Literal["High", "Medium", "Low"] = "Medium"
    reason: str = ""
    recommendation: str = ""


class RiskAnalysis(BaseModel):
    edge_cases: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    risk_items: list[RiskItem] = Field(default_factory=list)
    missing_validations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                return json.loads(cleaned)
            except Exception:
                return {}
        return v


class CoverageValidation(BaseModel):
    coverage_explanation: str = ""
    missing_areas: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                return json.loads(cleaned)
            except Exception:
                return {}
        return v


class CoverageBreakdown(BaseModel):
    overall: float = 0.0
    functional: float = 0.0
    validation: float = 0.0
    ui: float = 0.0
    negative: float = 0.0
    edge_cases: float = 0.0
    security_suggestions: float = 0.0
    is_estimated: bool = False
    label: str = "Programmatic coverage"


class ValidationCheckResult(BaseModel):
    positive_cases_covered: bool = False
    negative_cases_covered: bool = False
    edge_cases_covered: bool = False
    validation_cases_covered: bool = False
    security_cases_relevant: bool = False
    no_duplicate_ids: bool = False
    expected_results_clear: bool = False
    requirement_sufficiently_covered: bool = False
    coverage_score: float = 0.0
    issues: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
# --- Website analysis models ---


class DiscoveredFunctionality(BaseModel):
    name: str = ""
    description: str = ""
    page_url: str = ""
    page_title: str = ""
    elements: list[str] = Field(default_factory=list)
    category: str = "Functional"


class DiscoveredFunctionalityCollection(BaseModel):
    functionalities: list[DiscoveredFunctionality] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {"functionalities": []}
        if isinstance(v, list):
            return {"functionalities": v}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                if isinstance(data, list):
                    return {"functionalities": data}
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
            return {"functionalities": []}
        return v


class PageSummary(BaseModel):
    url: str
    title: str
    headings: list[str] = Field(default_factory=list)
    visible_text_snippet: str = ""


class DiscoveredButton(BaseModel):
    text: str
    selector: str
    page_url: str


class DiscoveredInput(BaseModel):
    name: str = ""
    input_type: str = "text"
    placeholder: str = ""
    label: str = ""
    selector: str = ""
    page_url: str = ""


class DiscoveredLink(BaseModel):
    text: str
    href: str
    page_url: str


class DiscoveredForm(BaseModel):
    form_id: str = ""
    action: str = ""
    method: str = "GET"
    fields: list[str] = Field(default_factory=list)
    page_url: str = ""


class PageAnalysisData(BaseModel):
    url: str
    path: str = "/"
    title: str = ""
    status: Literal["Analyzed", "Partially Analyzed", "Failed", "Auth Required", "CAPTCHA Detected"] = "Analyzed"
    screenshot_path: str = ""
    headings: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    buttons: list[DiscoveredButton] = Field(default_factory=list)
    inputs: list[DiscoveredInput] = Field(default_factory=list)
    links: list[DiscoveredLink] = Field(default_factory=list)
    forms: list[DiscoveredForm] = Field(default_factory=list)
    dropdowns: list[dict[str, Any]] = Field(default_factory=list)
    checkboxes: list[dict[str, Any]] = Field(default_factory=list)
    radio_buttons: list[dict[str, Any]] = Field(default_factory=list)
    cards: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    interactive_elements_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    functionalities: list[DiscoveredFunctionality] = Field(default_factory=list)


class WebsiteAnalysis(BaseModel):
    url: str
    domain: str = ""
    accessible: bool = False
    access_message: str = ""
    page_title: str = ""
    crawl_mode: str = "Website Pages"
    pages_discovered: int = 0
    pages_analyzed: int = 0
    pages_skipped: int = 0
    total_functionalities_count: int = 0
    pages: list[PageSummary] = Field(default_factory=list)
    page_analyses: list[PageAnalysisData] = Field(default_factory=list)
    all_functionalities: list[DiscoveredFunctionality] = Field(default_factory=list)
    sitemap: list[dict[str, Any]] = Field(default_factory=list)
    buttons: list[DiscoveredButton] = Field(default_factory=list)
    inputs: list[DiscoveredInput] = Field(default_factory=list)
    links: list[DiscoveredLink] = Field(default_factory=list)
    forms: list[DiscoveredForm] = Field(default_factory=list)
    navigation: list[str] = Field(default_factory=list)
    sections_found: int = 0
    interactive_elements_count: int = 0
    dropdowns: list[dict[str, Any]] = Field(default_factory=list)
    checkboxes: list[dict[str, Any]] = Field(default_factory=list)
    radio_buttons: list[dict[str, Any]] = Field(default_factory=list)
    cards: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    screenshot_path: str = ""
    analysis_warnings: list[str] = Field(default_factory=list)
    crawl_depth: int = 3
    requested_test_cases: int = 20
    generated_test_cases: int = 0
    generation_note: str = ""


class WebsiteFeatureUnderstanding(BaseModel):
    inferred_features: list[str] = Field(default_factory=list)
    primary_flows: list[str] = Field(default_factory=list)
    test_focus_areas: list[str] = Field(default_factory=list)
    synthesized_requirement: str = ""
    summary: str = ""

    @model_validator(mode="before")
    @classmethod
    def _validate_input(cls, v: Any) -> Any:
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                cleaned = v.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                return json.loads(cleaned)
            except Exception:
                return {}
        return v


class BrowserCheckResult(BaseModel):
    test: str
    result: Literal["PASS", "FAIL", "SKIP"] = "SKIP"
    evidence: str = ""
    selector: str = ""


class ReportHistoryItem(BaseModel):
    id: str
    mode: Literal["requirement", "website"] = "requirement"
    title: str
    source: str
    test_case_count: int = 0
    coverage_score: float = 0.0
    risk_level: str = "Medium"
    status: str = "Completed"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="minutes"))


class QAReport(BaseModel):
    mode: Literal["requirement", "website"] = "requirement"
    source: str = ""
    requirement: str = ""
    requirement_analysis: RequirementAnalysis | None = None
    website_analysis: WebsiteAnalysis | None = None
    website_understanding: WebsiteFeatureUnderstanding | None = None
    page_analyses: list[PageAnalysisData] = Field(default_factory=list)
    functionalities: list[DiscoveredFunctionality] = Field(default_factory=list)
    sitemap: list[dict[str, Any]] = Field(default_factory=list)
    test_scenarios: list[TestScenario] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    risk_items: list[RiskItem] = Field(default_factory=list)
    coverage_score: float = 0.0
    coverage_breakdown: CoverageBreakdown | None = None
    coverage_explanation: str = ""
    missing_areas: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    validation_details: dict[str, Any] = Field(default_factory=dict)
    browser_checks: list[BrowserCheckResult] = Field(default_factory=list)
    requested_test_cases: int = 20
    generated_test_cases: int = 0
    generation_note: str = ""

    def display_title(self) -> str:
        if self.mode == "website" and self.website_analysis:
            return self.website_analysis.domain or self.source
        return self.requirement_analysis.feature if self.requirement_analysis else self.source[:60]

    def to_markdown(self) -> str:
        title = "# Complete Website QA Report" if self.mode == "website" else "# QA Agent Pro — Requirement QA Report"
        lines = [
            title,
            "",
            f"**Mode:** {self.mode.title()}",
            f"**Starting URL / Source:** {self.source}",
            f"**Overall Coverage Score:** {self.coverage_score:.0f}%",
            "",
        ]
        if self.website_analysis:
            wa = self.website_analysis
            lines.extend(
                [
                    "## Website Summary",
                    f"- **Starting URL:** {wa.url}",
                    f"- **Pages Discovered:** {wa.pages_discovered or len(wa.sitemap)}",
                    f"- **Pages Analyzed:** {wa.pages_analyzed}",
                    f"- **Pages Skipped:** {wa.pages_skipped}",
                    f"- **Total Functionalities:** {len(self.functionalities)}",
                    f"- **Total Test Cases:** {len(self.test_cases)}",
                    "",
                    "## Website Sitemap",
                ]
            )
            for node in wa.sitemap:
                lines.append(f"- [{node.get('status', '🟢')}] **{node.get('title', 'Page')}** ({node.get('path', '/')}) - {node.get('url')}")
            lines.append("")

            lines.append("## Page-by-Page Analysis & Test Cases")
            for idx, p in enumerate(self.page_analyses, 1):
                lines.extend([
                    f"### PAGE {idx} — {p.title.upper()}",
                    f"**URL:** {p.url}",
                    f"**Status:** {p.status}",
                ])
                if p.screenshot_path:
                    lines.append(f"**Full Page Screenshot:** `{p.screenshot_path}`")

                lines.append("**Discovered Functionalities:**")
                if p.functionalities:
                    for f in p.functionalities:
                        lines.append(f"- **{f.name}** ({f.category}): {f.description}")
                else:
                    lines.append("- General Page Functionality")

                lines.append("**Test Cases:**")
                page_tcs = [tc for tc in self.test_cases if tc.page_url == p.url or tc.page_title == p.title]
                if page_tcs:
                    for tc in page_tcs:
                        lines.extend([
                            f"#### [{tc.test_case_id}] {tc.title}",
                            f"- **Functionality:** {tc.functionality} | **Type:** {tc.test_type} | **Priority:** {tc.priority}",
                            f"- **Preconditions:** {tc.preconditions or 'None'}",
                            f"- **Test Data:** {tc.test_data or 'N/A'}",
                            "- **Steps:**",
                        ])
                        lines.extend(f"  {s_idx}. {s}" for s_idx, s in enumerate(tc.steps, 1))
                        lines.append(f"- **Expected Result:** {tc.expected_result}")
                        lines.append("")
                else:
                    lines.append("_No specific test cases allocated to this page._\n")

        elif self.requirement_analysis:
            ra = self.requirement_analysis
            lines.extend(
                [
                    "## Requirement Analysis",
                    f"**Feature:** {ra.feature}",
                    f"**Expected Behavior:** {ra.expected_behavior}",
                    "",
                    "## Test Scenarios",
                ]
            )
            for scenario in self.test_scenarios:
                lines.append(f"- **{scenario.scenario_id}** [{scenario.category}] {scenario.title}")
            lines.extend(["", "## Test Cases"])
            for tc in self.test_cases:
                lines.extend(
                    [
                        f"### {tc.test_case_id}: {tc.title}",
                        f"- Module: {tc.module} | Type: {tc.test_type} | Priority: {tc.priority} | Status: {tc.status}",
                        f"- Objective: {tc.test_objective or tc.title}",
                        "- Steps:",
                    ]
                )
                lines.extend(f"  {i}. {step}" for i, step in enumerate(tc.steps, 1))
                lines.append(f"- Expected: {tc.expected_result}")
                lines.append("")

        if self.risk_items:
            lines.extend(["", "## Risk Matrix"])
            for item in self.risk_items:
                lines.append(
                    f"- **{item.risk}** ({item.severity}): {item.reason} → {item.recommendation}"
                )
        lines.extend(
            [
                "",
                "## Coverage Overview",
                f"**Overall Score:** {self.coverage_score:.0f}%",
                self.coverage_explanation,
            ]
        )
        if self.coverage_breakdown:
            cb = self.coverage_breakdown
            lines.extend(
                [
                    f"- Functional: {cb.functional:.0f}%",
                    f"- Validation: {cb.validation:.0f}%",
                    f"- UI: {cb.ui:.0f}%",
                    f"- Negative: {cb.negative:.0f}%",
                    f"- Edge Cases: {cb.edge_cases:.0f}%",
                    f"- Security Suggestions: {cb.security_suggestions:.0f}%",
                    f"- *{cb.label}*",
                ]
            )
        lines.extend(["", "## Recommendations"])
        lines.extend(f"- {item}" for item in self.recommendations)
        return "\n".join(lines)
