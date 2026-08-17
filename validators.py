"""Programmatic validation logic for test cases and coverage scoring."""

from __future__ import annotations

from collections import Counter

from models import (
    RequirementAnalysis,
    TestCase,
    TestScenario,
    ValidationCheckResult,
)

POSITIVE_TYPES = {"positive", "happy path", "happy_path"}
NEGATIVE_TYPES = {"negative", "error", "error_handling"}
BOUNDARY_TYPES = {"boundary", "edge", "edge case", "edge_case"}
VALIDATION_TYPES = {"validation", "validate"}
SECURITY_TYPES = {"security", "injection", "auth", "authentication", "authorization"}


def _normalize(value: str) -> str:
    return value.strip().lower()


def _matches_any(value: str, keywords: set[str]) -> bool:
    normalized = _normalize(value)
    return any(keyword in normalized for keyword in keywords)


def validate_test_case_structure(test_cases: list[TestCase]) -> tuple[list[str], dict]:
    """Check duplicates, missing fields, and empty expected results."""
    issues: list[str] = []
    ids = [tc.test_case_id for tc in test_cases]
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        issues.append(f"Duplicate test case IDs: {', '.join(duplicate_ids)}")

    missing_fields = 0
    empty_results = 0
    unclear_results = 0

    for tc in test_cases:
        if not tc.title.strip():
            missing_fields += 1
            issues.append(f"{tc.test_case_id}: missing title")
        if not tc.steps:
            missing_fields += 1
            issues.append(f"{tc.test_case_id}: missing steps")
        if not tc.expected_result.strip():
            empty_results += 1
            issues.append(f"{tc.test_case_id}: empty expected result")
        elif len(tc.expected_result.strip()) < 8:
            unclear_results += 1
            issues.append(f"{tc.test_case_id}: expected result may be too vague")

    details = {
        "total_test_cases": len(test_cases),
        "duplicate_id_count": len(duplicate_ids),
        "missing_field_count": missing_fields,
        "empty_expected_result_count": empty_results,
        "unclear_expected_result_count": unclear_results,
        "priority_breakdown": dict(Counter(tc.priority for tc in test_cases)),
        "type_breakdown": dict(Counter(tc.test_type for tc in test_cases)),
    }
    return issues, details


def calculate_coverage(
    test_cases: list[TestCase],
    scenarios: list[TestScenario],
    requirement_analysis: RequirementAnalysis | None = None,
) -> ValidationCheckResult:
    """Calculate coverage score based on actual category checks."""
    issues: list[str] = []

    scenario_categories = {_normalize(s.category) for s in scenarios}
    test_types = {_normalize(tc.test_type) for tc in test_cases}
    scenario_titles = " ".join(_normalize(s.title) + " " + _normalize(s.description) for s in scenarios)
    combined_types = test_types | scenario_categories | {_normalize(t) for t in scenario_titles.split()}

    positive_cases_covered = any(_matches_any(t, POSITIVE_TYPES) for t in combined_types) or any(
        "valid" in _normalize(tc.title) for tc in test_cases
    )
    negative_cases_covered = any(_matches_any(t, NEGATIVE_TYPES) for t in combined_types) or any(
        "invalid" in _normalize(tc.title) or "empty" in _normalize(tc.title) for tc in test_cases
    )
    edge_cases_covered = any(_matches_any(t, BOUNDARY_TYPES) for t in combined_types)
    validation_cases_covered = any(_matches_any(t, VALIDATION_TYPES) for t in combined_types) or any(
        "format" in _normalize(tc.title) or "validation" in _normalize(tc.title) for tc in test_cases
    )
    security_cases_relevant = any(_matches_any(t, SECURITY_TYPES) for t in combined_types) or any(
        "sql" in _normalize(tc.title)
        or "xss" in _normalize(tc.title)
        or "injection" in _normalize(tc.title)
        for tc in test_cases
    )

    structure_issues, structure_details = validate_test_case_structure(test_cases)
    issues.extend(structure_issues)

    no_duplicate_ids = structure_details["duplicate_id_count"] == 0
    expected_results_clear = structure_details["empty_expected_result_count"] == 0 and (
        structure_details["unclear_expected_result_count"] <= max(1, len(test_cases) // 5)
    )

    scenario_ids = {s.scenario_id for s in scenarios}
    linked_scenario_ids = {tc.test_scenario_id for tc in test_cases}
    scenario_link_ratio = len(linked_scenario_ids & scenario_ids) / max(len(scenario_ids), 1)
    requirement_sufficiently_covered = len(test_cases) >= max(3, len(scenarios) // 2) and scenario_link_ratio >= 0.5

    if not positive_cases_covered:
        issues.append("No positive/happy-path test cases detected")
    if not negative_cases_covered:
        issues.append("No negative/error test cases detected")
    if not edge_cases_covered:
        issues.append("No boundary/edge test cases detected")
    if not validation_cases_covered:
        issues.append("No validation test cases detected")
    if len(test_cases) < 3:
        issues.append("Very few test cases generated (< 3)")

    checks = {
        "positive_cases_covered": positive_cases_covered,
        "negative_cases_covered": negative_cases_covered,
        "edge_cases_covered": edge_cases_covered,
        "validation_cases_covered": validation_cases_covered,
        "security_cases_relevant": security_cases_relevant,
        "no_duplicate_ids": no_duplicate_ids,
        "expected_results_clear": expected_results_clear,
        "requirement_sufficiently_covered": requirement_sufficiently_covered,
    }

    # Weighted score: 8 core checks + scenario linkage bonus
    weights = {
        "positive_cases_covered": 15,
        "negative_cases_covered": 15,
        "edge_cases_covered": 12,
        "validation_cases_covered": 12,
        "security_cases_relevant": 8,
        "no_duplicate_ids": 10,
        "expected_results_clear": 13,
        "requirement_sufficiently_covered": 15,
    }
    score = sum(weights[key] for key, passed in checks.items() if passed)
    score = min(100.0, score)

    if requirement_analysis and requirement_analysis.missing_information:
        penalty = min(10, len(requirement_analysis.missing_information) * 2)
        score = max(0.0, score - penalty)
        issues.append(
            f"Requirement has {len(requirement_analysis.missing_information)} missing information gap(s)"
        )

    details = {
        **structure_details,
        "scenario_link_ratio": round(scenario_link_ratio, 2),
        "checks_passed": sum(1 for passed in checks.values() if passed),
        "checks_total": len(checks),
    }

    return ValidationCheckResult(
        positive_cases_covered=positive_cases_covered,
        negative_cases_covered=negative_cases_covered,
        edge_cases_covered=edge_cases_covered,
        validation_cases_covered=validation_cases_covered,
        security_cases_relevant=security_cases_relevant,
        no_duplicate_ids=no_duplicate_ids,
        expected_results_clear=expected_results_clear,
        requirement_sufficiently_covered=requirement_sufficiently_covered,
        coverage_score=score,
        issues=issues,
        details=details,
    )


def calculate_category_coverage(
    test_cases: list[TestCase],
    scenarios: list[TestScenario],
    website_element_count: int = 0,
) -> dict[str, float]:
    """Calculate per-category coverage from generated tests and discovered elements."""
    if not test_cases:
        return {
            "overall": 0.0,
            "functional": 0.0,
            "validation": 0.0,
            "ui": 0.0,
            "negative": 0.0,
            "edge_cases": 0.0,
            "security_suggestions": 0.0,
        }

    def count_matching(keywords: set[str]) -> int:
        return sum(
            1
            for tc in test_cases
            if _matches_any(tc.test_type, keywords)
            or _matches_any(tc.category, keywords)
            or any(_matches_any(k, keywords) for k in [tc.title, tc.test_objective])
        )

    total = len(test_cases)
    functional = count_matching(POSITIVE_TYPES | {"functional", "positive"}) / total * 100
    validation = count_matching(VALIDATION_TYPES | {"validation", "format", "required"}) / total * 100
    ui = sum(
        1 for tc in test_cases if "ui" in _normalize(tc.category) or "visibility" in _normalize(tc.title)
    ) / total * 100
    negative = count_matching(NEGATIVE_TYPES | {"negative"}) / total * 100
    edge = count_matching(BOUNDARY_TYPES | {"edge", "boundary"}) / total * 100
    security = count_matching(SECURITY_TYPES | {"security"}) / total * 100

    base = calculate_coverage(test_cases, scenarios)
    overall = base.coverage_score

    if website_element_count > 0:
        grounded = sum(
            1
            for tc in test_cases
            if any(
                token in _normalize(tc.title) + _normalize(" ".join(tc.steps))
                for token in ("button", "input", "form", "link", "field", "login", "email", "password")
            )
        )
        grounding_ratio = min(1.0, grounded / max(total * 0.5, 1))
        overall = min(100.0, overall * 0.7 + grounding_ratio * 30)

    return {
        "overall": round(overall, 1),
        "functional": round(min(100.0, functional * 1.2), 1),
        "validation": round(min(100.0, validation * 1.3), 1),
        "ui": round(min(100.0, ui * 2.5 + (10 if ui else 0)), 1),
        "negative": round(min(100.0, negative * 1.4), 1),
        "edge_cases": round(min(100.0, edge * 1.5), 1),
        "security_suggestions": round(min(100.0, security * 2.0 + (5 if security else 0)), 1),
    }
