"""Local tests for configuration, validators, and optional live agent runs."""

from __future__ import annotations

import sys

from agent import QATestCaseOrchestrator
from config import validate_configuration
from demo_data import DEMO_REQUIREMENTS
from models import TestCase, TestScenario
from validators import calculate_coverage, validate_test_case_structure


def test_validators() -> None:
    cases = [
        TestCase(
            test_case_id="TC01",
            test_scenario_id="TS01",
            title="Login with valid credentials",
            preconditions="User exists",
            test_data="email/password",
            steps=["Open login", "Enter credentials", "Submit"],
            expected_result="User is logged in successfully",
            priority="High",
            test_type="Positive",
            category="Functional",
        ),
        TestCase(
            test_case_id="TC02",
            test_scenario_id="TS02",
            title="Login with invalid password",
            preconditions="User exists",
            test_data="bad password",
            steps=["Open login", "Enter wrong password", "Submit"],
            expected_result="Error message displayed",
            priority="High",
            test_type="Negative",
        ),
    ]
    scenarios = [
        TestScenario(scenario_id="TS01", title="Valid login", category="positive", description="Happy path"),
        TestScenario(scenario_id="TS02", title="Invalid login", category="negative", description="Error path"),
        TestScenario(scenario_id="TS03", title="Empty fields", category="validation", description="Required fields"),
        TestScenario(scenario_id="TS04", title="SQL injection", category="security", description="Security test"),
    ]
    issues, details = validate_test_case_structure(cases)
    coverage = calculate_coverage(cases, scenarios)
    assert details["total_test_cases"] == 2
    assert coverage.coverage_score > 0
    print(f"[PASS] Validators (coverage={coverage.coverage_score:.0f}%)")


def test_configuration() -> None:
    valid, message = validate_configuration()
    print(f"[INFO] Configuration: valid={valid}, message={message}")


def test_empty_requirement() -> None:
    orchestrator = QATestCaseOrchestrator()
    try:
        orchestrator.run("")
        raise AssertionError("Expected ValueError for empty requirement")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
        print("[PASS] Empty requirement rejected")


def run_live_tests() -> None:
    valid, message = validate_configuration()
    if not valid:
        print(f"[SKIP] Live agent tests — {message}")
        return

    orchestrator = QATestCaseOrchestrator()
    test_names = ["Login", "Password Reset", "User Registration"]

    for name in test_names:
        requirement = DEMO_REQUIREMENTS[name]
        print(f"\n[RUN] Live test: {name}")
        report = orchestrator.run(requirement)
        assert report.requirement_analysis.feature
        assert len(report.test_scenarios) >= 3
        assert len(report.test_cases) >= 3
        print(
            f"[PASS] {name}: scenarios={len(report.test_scenarios)}, "
            f"cases={len(report.test_cases)}, coverage={report.coverage_score:.0f}%"
        )


def main() -> int:
    print("=== AI QA Test Case Agent — Local Tests ===\n")
    test_validators()
    test_configuration()
    test_empty_requirement()

    if "--live" in sys.argv:
        run_live_tests()
    else:
        print("\n[INFO] Skipping live LLM tests. Run with --live after setting GEMINI_API_KEY in .env")

    print("\nAll local tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
