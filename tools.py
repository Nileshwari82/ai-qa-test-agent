"""Strands tools for test case validation and coverage calculation."""

from __future__ import annotations

import json

from strands import tool

from models import TestCase, TestScenario
from validators import calculate_coverage, validate_test_case_structure


@tool
def validate_test_cases(test_cases_json: str) -> str:
    """Validate test cases for duplicate IDs, missing fields, and empty expected results.

    Args:
        test_cases_json: JSON string with a list of test case objects or {"test_cases": [...]}.

    Returns:
        JSON string with validation issues and summary statistics.
    """
    try:
        payload = json.loads(test_cases_json)
        if isinstance(payload, dict) and "test_cases" in payload:
            raw_cases = payload["test_cases"]
        elif isinstance(payload, list):
            raw_cases = payload
        else:
            return json.dumps({"error": "Invalid format. Expected list or {'test_cases': [...]}."})

        test_cases = [TestCase.model_validate(item) for item in raw_cases]
        issues, details = validate_test_case_structure(test_cases)
        return json.dumps(
            {
                "valid": len(issues) == 0,
                "issue_count": len(issues),
                "issues": issues,
                "details": details,
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"error": f"Validation failed: {exc}"})


@tool
def calculate_coverage_score(test_cases_json: str, scenarios_json: str) -> str:
    """Calculate test coverage indicators based on scenario categories and test case types.

    Args:
        test_cases_json: JSON string of test cases (list or {"test_cases": [...]}).
        scenarios_json: JSON string of scenarios (list or {"scenarios": [...]}).

    Returns:
        JSON string with coverage score, checks, and issues.
    """
    try:
        cases_payload = json.loads(test_cases_json)
        scenarios_payload = json.loads(scenarios_json)

        raw_cases = cases_payload["test_cases"] if isinstance(cases_payload, dict) else cases_payload
        raw_scenarios = (
            scenarios_payload["scenarios"] if isinstance(scenarios_payload, dict) else scenarios_payload
        )

        test_cases = [TestCase.model_validate(item) for item in raw_cases]
        scenarios = [TestScenario.model_validate(item) for item in raw_scenarios]
        result = calculate_coverage(test_cases, scenarios)

        return json.dumps(
            {
                "coverage_score": result.coverage_score,
                "checks": {
                    "positive_cases_covered": result.positive_cases_covered,
                    "negative_cases_covered": result.negative_cases_covered,
                    "edge_cases_covered": result.edge_cases_covered,
                    "validation_cases_covered": result.validation_cases_covered,
                    "security_cases_relevant": result.security_cases_relevant,
                    "no_duplicate_ids": result.no_duplicate_ids,
                    "expected_results_clear": result.expected_results_clear,
                    "requirement_sufficiently_covered": result.requirement_sufficiently_covered,
                },
                "issues": result.issues,
                "details": result.details,
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"error": f"Coverage calculation failed: {exc}"})
