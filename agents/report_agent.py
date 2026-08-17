"""Report Agent (Agent 7) for generating and formatting complete website QA reports."""

from __future__ import annotations

import logging
from typing import Any

from models import QAReport

logger = logging.getLogger(__name__)


class ReportAgent:
    """Agent responsible for assembling, structuring, and formatting final QA reports."""

    def __init__(self, model=None) -> None:
        self._model = model

    def build_report_summary(self, report: QAReport) -> dict[str, Any]:
        """Build executive summary data for report visualization."""
        wa = report.website_analysis
        total_discovered = wa.pages_discovered if wa else 0
        total_analyzed = wa.pages_analyzed if wa else 0
        total_skipped = wa.pages_skipped if wa else 0

        high_priority_tcs = sum(1 for tc in report.test_cases if tc.priority == "High")
        med_priority_tcs = sum(1 for tc in report.test_cases if tc.priority == "Medium")
        low_priority_tcs = sum(1 for tc in report.test_cases if tc.priority == "Low")

        return {
            "title": report.display_title(),
            "mode": report.mode,
            "starting_url": report.source,
            "pages_discovered": total_discovered,
            "pages_analyzed": total_analyzed,
            "pages_skipped": total_skipped,
            "total_functionalities": len(report.functionalities),
            "total_test_cases": len(report.test_cases),
            "priority_counts": {
                "high": high_priority_tcs,
                "medium": med_priority_tcs,
                "low": low_priority_tcs,
            },
            "coverage_score": report.coverage_score,
            "generation_note": report.generation_note,
        }
