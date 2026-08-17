"""Export utilities for QA reports."""

from __future__ import annotations

import json
from io import BytesIO

import pandas as pd

from models import QAReport


def test_cases_dataframe(report: QAReport) -> pd.DataFrame:
    rows = []
    for tc in report.test_cases:
        rows.append(
            {
                "ID": tc.test_case_id,
                "Page": tc.page_title or "Page",
                "URL": tc.page_url or report.source,
                "Functionality": tc.functionality,
                "Test Case": tc.title,
                "Type": tc.test_type,
                "Priority": tc.priority,
                "Preconditions": tc.preconditions,
                "Steps": "\n".join(f"{i}. {s}" for i, s in enumerate(tc.steps, 1)),
                "Expected Result": tc.expected_result,
                "Status": tc.status,
                "Category": tc.category,
                "Automation Potential": tc.automation_potential,
            }
        )
    return pd.DataFrame(rows)


def export_json(report: QAReport) -> bytes:
    return report.model_dump_json(indent=2).encode("utf-8")


def export_markdown(report: QAReport) -> bytes:
    return report.to_markdown().encode("utf-8")


def export_csv(report: QAReport) -> bytes:
    buffer = BytesIO()
    test_cases_dataframe(report).to_csv(buffer, index=False)
    return buffer.getvalue()


def export_html(report: QAReport) -> bytes:
    df = test_cases_dataframe(report)
    html_parts = [
        "<html><head><meta charset='utf-8'><title>QA Agent Pro - Website QA Report</title>",
        "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:2rem;}table{border-collapse:collapse;width:100%;}",
        "th,td{border:1px solid #ddd;padding:8px;}th{background:#2563eb;color:white;}</style></head><body>",
        "<h1>QA Agent Pro - Complete Website QA Report</h1>",
        f"<p><strong>Mode:</strong> {report.mode.title()} | <strong>Starting URL:</strong> {report.source}</p>",
        f"<p><strong>Overall Coverage:</strong> {report.coverage_score:.0f}%</p>",
    ]
    if report.website_analysis:
        wa = report.website_analysis
        html_parts.append(
            f"<h2>Website Overview</h2><ul>"
            f"<li>URL: {wa.url}</li>"
            f"<li>Pages Discovered: {wa.pages_discovered}</li>"
            f"<li>Pages Analyzed: {wa.pages_analyzed}</li>"
            f"<li>Pages Skipped: {wa.pages_skipped}</li>"
            f"<li>Discovered Functionalities: {len(report.functionalities)}</li>"
            f"<li>Total Test Cases: {len(report.test_cases)}</li></ul>"
        )
    html_parts.append("<h2>Test Cases by Page & Functionality</h2>")
    html_parts.append(df.to_html(index=False, escape=True))
    if report.risk_items:
        html_parts.append("<h2>Risk Analysis Matrix</h2><table><tr><th>Risk</th><th>Severity</th><th>Reason</th><th>Recommendation</th></tr>")
        for item in report.risk_items:
            html_parts.append(
                f"<tr><td>{item.risk}</td><td>{item.severity}</td>"
                f"<td>{item.reason}</td><td>{item.recommendation}</td></tr>"
            )
        html_parts.append("</table>")
    html_parts.append("</body></html>")
    return "".join(html_parts).encode("utf-8")
