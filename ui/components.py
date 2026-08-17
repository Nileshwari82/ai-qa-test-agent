"""Shared UI components for QA Agent Pro."""

from __future__ import annotations

import base64
import os
import pandas as pd
import streamlit as st

from export_utils import export_csv, export_html, export_json, export_markdown, test_cases_dataframe
from models import QAReport, PageAnalysisData


def severity_badge(severity: str) -> str:
    css = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(severity, "badge-medium")
    return f'<span class="status-badge {css}">{severity}</span>'


def metric_card(label: str, value: str, alt: bool = False) -> None:
    css = "metric-card-alt" if alt else "metric-card"
    st.markdown(
        f'<div class="{css}"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def render_agent_activity(steps: dict[str, str], show: bool = True) -> None:
    if not show:
        return
    st.markdown("#### 🤖 AI QA Agent Multi-Step Architecture")
    icons = {
        "website": ("Agent 1 — Website Discovery Agent", "Discovers internal pages, normalizes URLs & creates visual sitemap"),
        "page_analysis": ("Agent 2 — Page Analysis Agent", "Full-page progressive scroll, DOM extraction & screenshot capture"),
        "functionality": ("Agent 3 — Functionality Detection Agent", "Groups page elements into logical user functionalities"),
        "scenario": ("Agent 4 — Test Scenario Agent", "Generates comprehensive test scenarios per functionality"),
        "testcase": ("Agent 5 — Test Case Generator Agent", "Generates detailed test cases with intelligent page allocation"),
        "validator": ("Agent 6 — QA Validator Agent", "Validates test coverage, duplicate IDs, and edge cases"),
        "report": ("Agent 7 — Report Agent", "Formats executive summary and page-by-page QA report"),
    }

    for key, (label, desc) in icons.items():
        status = steps.get(key, "pending")
        if status == "done":
            badge = '<span class="agent-badge badge-done">✓ COMPLETED</span>'
            css = "step-card-done"
        elif status == "running":
            badge = '<span class="agent-badge badge-running">⟳ IN PROGRESS</span>'
            css = "step-card-running"
        else:
            badge = '<span class="agent-badge badge-pending">○ PENDING</span>'
            css = "step-card-pending"

        st.markdown(
            f"""
            <div class="agent-step-card {css}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:15px; letter-spacing:0.3px;">{label}</strong>
                    {badge}
                </div>
                <div style="font-size:12px; opacity:0.85; margin-top:4px;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_export_buttons(report: QAReport) -> None:
    st.markdown("#### 📥 Export Complete QA Report")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button("📥 Export CSV", export_csv(report), "website_qa_test_cases.csv", "text/csv", use_container_width=True)
    with c2:
        st.download_button("📥 Export JSON", export_json(report), "website_qa_report.json", "application/json", use_container_width=True)
    with c3:
        st.download_button("📥 Export Markdown", export_markdown(report), "website_qa_report.md", "text/markdown", use_container_width=True)
    with c4:
        st.download_button("📥 Export HTML", export_html(report), "website_qa_report.html", "text/html", use_container_width=True)


def render_test_cases_table(report: QAReport) -> None:
    df = test_cases_dataframe(report)
    st.dataframe(df, use_container_width=True, hide_index=True)
    for tc in report.test_cases:
        with st.expander(f"{tc.test_case_id}: {tc.title}"):
            st.markdown(f"**Objective:** {tc.test_objective or tc.title}")
            st.markdown(f"**Module:** {tc.module} | **Category:** {tc.category} | **Type:** {tc.test_type}")
            st.markdown(f"**Priority:** {tc.priority} | **Status:** {tc.status} | **Risk:** {tc.risk_level}")
            st.markdown(f"**Automation Potential:** {tc.automation_potential} (Playwright)")
            st.markdown(f"**Preconditions:** {tc.preconditions}")
            st.markdown(f"**Test Data:** {tc.test_data}")
            st.markdown("**Steps:**")
            for i, step in enumerate(tc.steps, 1):
                st.markdown(f"{i}. {step}")
            st.markdown(f"**Expected Result:** {tc.expected_result}")


def render_sitemap_visual(report: QAReport) -> None:
    """Render a visual sitemap tree and crawling statistics."""
    wa = report.website_analysis
    if not wa:
        st.info("No sitemap data available.")
        return

    st.markdown("### 🗺️ Website Visual Sitemap")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Discovered", str(wa.pages_discovered or len(wa.sitemap)), alt=True)
    with c2:
        metric_card("Pages Analyzed", str(wa.pages_analyzed), alt=True)
    with c3:
        metric_card("Pages Skipped", str(wa.pages_skipped), alt=True)
    with c4:
        metric_card("Functionalities", str(len(report.functionalities)), alt=True)

    st.markdown("#### 🌳 Discovered Page Tree")
    if wa.sitemap:
        tree_text = "🌐 " + (wa.url or "Website Root") + "\n"
        for idx, node in enumerate(wa.sitemap):
            prefix = " ├── " if idx < len(wa.sitemap) - 1 else " └── "
            path = node.get("path", "/")
            title = node.get("title", "")
            status = node.get("status", "🟢 Analyzed")
            tree_text += f"{prefix}{status} {path} — \"{title}\"\n"
        st.code(tree_text, language="text")

    if wa.pages_skipped > 0:
        st.warning("⚠️ Some pages were skipped or required authentication/CAPTCHA. See the Pages tab for details.")


def render_pages_table(page_analyses: list[PageAnalysisData]) -> None:
    """Render the page status table and per-page detailed expanders."""
    st.markdown("### 📄 Discovered & Analyzed Pages")
    if not page_analyses:
        st.info("No pages analyzed.")
        return

    # Status summary
    rows = []
    for p in page_analyses:
        status_icon = "🟢" if p.status == "Analyzed" else ("🟡" if p.status == "Partially Analyzed" else ("🔒" if p.status == "Auth Required" else "⚠️"))
        rows.append({
            "Status": f"{status_icon} {p.status}",
            "Page Title": p.title,
            "Path": p.path,
            "Full URL": p.url,
            "Functionalities": len(p.functionalities),
            "Interactive Elements": p.interactive_elements_count,
            "Screenshot": "Captured" if p.screenshot_path else "N/A",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### 🔍 Page-by-Page Deep Dive")
    for idx, page in enumerate(page_analyses, start=1):
        with st.expander(f"Page {idx}: {page.title} ({page.path}) — Status: {page.status}"):
            st.markdown(f"**URL:** [{page.url}]({page.url})")
            st.markdown(f"**Status:** {page.status}")
            if page.warnings:
                for w in page.warnings:
                    st.warning(w)

            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("**Discovered Headings:**")
                if page.headings:
                    for h in page.headings[:8]:
                        st.markdown(f"- {h}")
                else:
                    st.caption("No headings found")

                st.markdown("**Discovered Functionalities:**")
                if page.functionalities:
                    for f in page.functionalities:
                        st.markdown(f"- **{f.name}** ({f.category}): {f.description}")
                else:
                    st.caption("No functionalities identified for this page.")

            with c2:
                if page.screenshot_path and os.path.exists(page.screenshot_path):
                    with open(page.screenshot_path, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode()
                    st.markdown(
                        f'''<div style="max-height:300px; overflow-y:auto; border:1px solid #334155; border-radius:6px; padding:4px;">
                            <img src="data:image/png;base64,{encoded}" style="max-width:100%; height:auto;" />
                        </div>''',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("No screenshot available.")


def render_functionalities_grid(page_analyses: list[PageAnalysisData]) -> None:
    """Render functionalities grouped by page."""
    st.markdown("### ⚙️ Discovered Page Functionalities")
    total_funcs = sum(len(p.functionalities) for p in page_analyses)
    if total_funcs == 0:
        st.info("No page functionalities detected yet.")
        return

    for page in page_analyses:
        if page.functionalities:
            st.markdown(f"#### 📄 Page: {page.title} (`{page.path}`)")
            f_rows = []
            for f in page.functionalities:
                f_rows.append({
                    "Functionality": f.name,
                    "Category": f.category,
                    "Description": f.description,
                    "Associated Elements": ", ".join(f.elements[:5]) if f.elements else "Page Elements",
                })
            st.dataframe(pd.DataFrame(f_rows), use_container_width=True, hide_index=True)


def render_test_cases_by_page_and_functionality(report: QAReport) -> None:
    """Render test cases organized by Page and Functionality."""
    st.markdown("### 🧪 Generated Test Cases by Page & Functionality")
    if not report.test_cases:
        st.info("No test cases generated.")
        return

    # Main table overview
    df = test_cases_dataframe(report)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Grouping by Page & Functionality
    st.markdown("#### 📂 Detailed Test Cases Grouped by Page")
    pages_dict: dict[str, list] = {}
    for tc in report.test_cases:
        page_key = tc.page_title or tc.page_url or "General Page"
        pages_dict.setdefault(page_key, []).append(tc)

    for page_name, cases in pages_dict.items():
        with st.expander(f"📄 {page_name} ({len(cases)} Test Cases)", expanded=False):
            # Sub-group by functionality
            func_dict: dict[str, list] = {}
            for tc in cases:
                func_dict.setdefault(tc.functionality, []).append(tc)

            for func_name, f_cases in func_dict.items():
                st.markdown(f"##### ⚙️ Functionality: {func_name}")
                for tc in f_cases:
                    st.markdown(f"**[{tc.test_case_id}] {tc.title}**")
                    st.markdown(f"- **Type:** `{tc.test_type}` | **Priority:** `{tc.priority}` | **Category:** `{tc.category}`")
                    st.markdown(f"- **Objective:** {tc.test_objective or tc.title}")
                    st.markdown(f"- **Preconditions:** {tc.preconditions or 'None'}")
                    st.markdown(f"- **Test Data:** `{tc.test_data or 'N/A'}`")
                    st.markdown("- **Steps:**")
                    for step_idx, s in enumerate(tc.steps, 1):
                        st.markdown(f"  {step_idx}. {s}")
                    st.markdown(f"- **Expected Result:** {tc.expected_result}")
                    st.divider()


def render_screenshots_gallery(page_analyses: list[PageAnalysisData]) -> None:
    """Render a gallery of all captured full-page screenshots."""
    st.markdown("### 📸 Full-Page Screenshots Gallery")
    has_screenshots = any(p.screenshot_path and os.path.exists(p.screenshot_path) for p in page_analyses)

    if not has_screenshots:
        st.info("No full-page screenshots captured.")
        return

    tabs = st.tabs([f"Page {i+1}: {p.title[:20]}" for i, p in enumerate(page_analyses) if p.screenshot_path])
    idx = 0
    for p in page_analyses:
        if p.screenshot_path and os.path.exists(p.screenshot_path):
            with tabs[idx]:
                st.markdown(f"**URL:** [{p.url}]({p.url})")
                st.caption(f"Full-page screenshot captured for {p.title}")
                with open(p.screenshot_path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode()
                st.markdown(
                    f'''<div style="max-height:650px; overflow-y:auto; border:2px solid #334155; border-radius:8px; padding:8px; background-color:#0f172a; text-align:center;">
                        <img src="data:image/png;base64,{encoded}" style="max-width:100%; height:auto;" />
                    </div>''',
                    unsafe_allow_html=True,
                )
            idx += 1


def render_page_coverage_breakdown(report: QAReport) -> None:
    """Render website & page-by-page coverage dashboard."""
    st.markdown("### 📊 Website & Page Coverage Dashboard")
    st.metric("Overall Test Coverage", f"{report.coverage_score:.0f}%")

    if report.coverage_breakdown:
        cb = report.coverage_breakdown
        st.markdown("#### Test Category Breakdown")
        cols = st.columns(3)
        metrics = [
            ("Functional", cb.functional),
            ("Validation", cb.validation),
            ("UI", cb.ui),
            ("Negative", cb.negative),
            ("Edge Cases", cb.edge_cases),
            ("Security Suggestions", cb.security_suggestions),
        ]
        for col, (label, val) in zip(cols * 2, metrics):
            with col:
                st.progress(min(val / 100, 1.0))
                st.caption(f"{label}: {val:.0f}%")

    st.markdown("#### 📄 Coverage by Page")
    if report.page_analyses:
        for page in report.page_analyses:
            page_tcs = [tc for tc in report.test_cases if tc.page_url == page.url or tc.page_title == page.title]
            ratio = min(100.0, (len(page_tcs) / max(1, len(report.test_cases) / len(report.page_analyses))) * 100)
            st.markdown(f"**{page.title}** (`{page.path}`): {len(page_tcs)} Test Cases")
            st.progress(min(ratio / 100, 1.0))

    st.markdown("#### ⚙️ Functionality Coverage Checklist")
    all_funcs = report.functionalities
    if all_funcs:
        for func in all_funcs:
            covered = any(tc.functionality == func.name or func.name.lower() in tc.title.lower() for tc in report.test_cases)
            icon = "✓ Covered" if covered else "⚠ Needs Attention"
            st.markdown(f"- **{func.name}** ({func.page_title}): {icon}")
    else:
        st.caption("Standard coverage checks applied.")


def render_risk_matrix(report: QAReport) -> None:
    st.markdown("### ⚠️ Risk Analysis & Edge Cases")
    if not report.risk_items:
        for risk in report.risks:
            st.markdown(f"- {risk}")
        return

    df = pd.DataFrame([r.model_dump() for r in report.risk_items])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_full_page_screenshot(screenshot_path: str) -> None:
    if not screenshot_path or not os.path.exists(screenshot_path):
        st.info("No screenshot captured.")
        return

    with open(screenshot_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<div style="max-height:550px; overflow-y:auto; border:1px solid #334155; border-radius:8px; padding:8px; background-color:#0f172a; text-align:center;"><img src="data:image/png;base64,{encoded}" alt="Full Page Screenshot" /></div>',
        unsafe_allow_html=True,
    )


def render_test_case_count_banner(report: QAReport) -> None:
    requested = report.requested_test_cases or 20
    generated = report.generated_test_cases or len(report.test_cases)
    note = report.generation_note or "✓ Requested test cases generated successfully."

    c1, c2 = st.columns([1.2, 2.8])
    with c1:
        st.markdown(
            f"""
            <div style="background:#1e293b; padding:16px; border-radius:8px; border:1px solid #334155;">
                <div style="font-size:12px; color:#94a3b8; text-transform:uppercase; font-weight:bold;">Test Cases Count</div>
                <div style="display:flex; justify-content:space-around; margin-top:8px;">
                    <div><span style="font-size:12px; color:#94a3b8;">Requested</span><br/><strong style="font-size:24px; color:#38bdf8;">{requested}</strong></div>
                    <div><span style="font-size:12px; color:#94a3b8;">Generated</span><br/><strong style="font-size:24px; color:#4ade80;">{generated}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        if generated >= requested:
            st.success(f"**✓ Requested test cases generated successfully.** ({generated}/{requested})")
        else:
            st.warning(f"**Requested:** {requested} | **Generated:** {generated}\n\n_{note}_")
