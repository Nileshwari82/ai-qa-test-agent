"""End-to-end integration test for full QA Agent Pro website analysis workflow."""

from __future__ import annotations

import logging
import sys

from agent import QATestCaseOrchestrator, WebsiteWorkflowStep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_full_website_qa_workflow():
    print("Testing full website QA analysis workflow...")
    orchestrator = QATestCaseOrchestrator()
    
    # Run website analysis with max_pages=2 and requested_test_cases=10
    report = orchestrator.run_website(
        url="https://www.saucedemo.com/",
        max_pages=2,
        requested_test_cases=10,
        analysis_options={
            "ui_elements": True,
            "forms": True,
            "navigation": True,
        },
    )
    
    print("\n--- REPORT SUMMARY ---")
    print(f"Mode: {report.mode}")
    print(f"Source: {report.source}")
    print(f"Coverage Score: {report.coverage_score:.0f}%")
    print(f"Pages Discovered: {report.website_analysis.pages_discovered if report.website_analysis else 0}")
    print(f"Pages Analyzed: {len(report.page_analyses)}")
    print(f"Total Functionalities: {len(report.functionalities)}")
    print(f"Total Test Cases: {len(report.test_cases)}")
    print(f"Generation Note: {report.generation_note.encode('ascii', 'ignore').decode()}")
    
    assert report.mode == "website"
    assert len(report.page_analyses) >= 1
    assert len(report.test_cases) > 0
    print("[PASS] Full website QA analysis workflow passed!")


if __name__ == "__main__":
    try:
        test_full_website_qa_workflow()
        print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    except Exception as exc:
        print(f"\nTEST FAILED: {exc}")
        sys.exit(1)
