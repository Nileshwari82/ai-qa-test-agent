"""Page renderers for QA Agent Pro."""

from __future__ import annotations

import traceback
import pandas as pd
import streamlit as st

from agent import QATestCaseOrchestrator, WebsiteWorkflowStep, make_history_item
from config import get_model_id, validate_configuration
from demo_data import DEMO_REQUIREMENTS
from ui.components import (
    metric_card,
    render_agent_activity,
    render_export_buttons,
    render_full_page_screenshot,
    render_functionalities_grid,
    render_page_coverage_breakdown,
    render_pages_table,
    render_risk_matrix,
    render_screenshots_gallery,
    render_sitemap_visual,
    render_test_case_count_banner,
    render_test_cases_by_page_and_functionality,
    render_test_cases_table,
)


def page_dashboard() -> None:
    st.markdown('<p class="hero-title">Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Overview of your QA analysis runs</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    history = st.session_state.get("report_history", [])
    report = st.session_state.get("current_report")
    with c1:
        metric_card("Total Runs", str(len(history)), alt=True)
    with c2:
        metric_card("Latest Cases", str(len(report.test_cases)) if report else "—", alt=True)
    with c3:
        metric_card("Coverage", f"{report.coverage_score:.0f}%" if report else "—", alt=True)
    with c4:
        metric_card("Mode", report.mode.title() if report else "—", alt=True)

    st.markdown("### Quick Actions")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("🌐 Analyze Website", use_container_width=True):
            st.session_state.page = "Website Analyzer"
            st.rerun()
    with qa2:
        if st.button("📝 Generate From Requirement", use_container_width=True):
            st.session_state.page = "Test Case Generator"
            st.rerun()
    with qa3:
        if st.button("📁 View Reports", use_container_width=True):
            st.session_state.page = "Test Reports"
            st.rerun()

    st.markdown("### Recent Analysis")
    if history:
        df = pd.DataFrame([h.model_dump() for h in history[:10]])
        st.dataframe(
            df[["title", "test_case_count", "coverage_score", "risk_level", "status", "created_at"]].rename(
                columns={
                    "title": "Website/Feature",
                    "test_case_count": "Test Cases",
                    "coverage_score": "Coverage",
                    "risk_level": "Risk",
                    "created_at": "Date",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No analysis runs yet. Start with Website Analyzer or Test Case Generator.")


def page_website_analyzer() -> None:
    st.markdown('<p class="hero-title">🤖 AI Website QA Agent</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Provide a starting URL to automatically crawl internal pages, build a sitemap, discover functionalities, and generate page-by-page test cases.</p>', unsafe_allow_html=True)

    url = st.text_input(
        "Enter Starting URL",
        value=st.session_state.get("website_url", "https://www.saucedemo.com/"),
        placeholder="https://www.example.com/",
    )
    st.session_state.website_url = url

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        crawl_mode = st.selectbox("Crawl Mode", ["Website Pages", "Current Page Only", "Custom"], index=0)
    with c2:
        if crawl_mode == "Current Page Only":
            max_pages = 1
            st.info("Max Pages set to 1 for Current Page Only.")
        else:
            max_pages = st.number_input("Maximum Pages", min_value=1, max_value=50, value=5, help="Up to 50 pages can be discovered and analyzed.")
    with c3:
        preset_count = st.selectbox("Target Test Cases", [10, 20, 50, 100, "Custom"], index=1)
    with c4:
        if preset_count == "Custom":
            requested_test_cases = st.number_input("Custom Test Case Count", min_value=1, max_value=200, value=25)
        else:
            requested_test_cases = int(preset_count)

    st.markdown("**Agent Options**")
    o1, o2, o3, o4, o5 = st.columns(5)
    with o1:
        opt_screenshots = st.checkbox("Full Page Screenshots", True)
    with o2:
        opt_funcs = st.checkbox("Discover Functionalities", True)
    with o3:
        opt_testcases = st.checkbox("Generate Test Cases", True)
    with o4:
        opt_risks = st.checkbox("Risk Analysis", True)
    with o5:
        opt_coverage = st.checkbox("Coverage Analysis", True)

    run_checks = st.checkbox("▶ Run Safe Browser Check (visibility & link verification)", value=False)

    analyze = st.button("🚀 Start Complete Website Analysis", type="primary", use_container_width=True)

    if analyze:
        valid, msg = validate_configuration()
        if not valid:
            st.error(msg)
            return
        if not url.strip():
            st.error("Please enter a valid starting URL.")
            return

        steps = {k: "pending" for k in ["website", "page_analysis", "functionality", "scenario", "testcase", "validator", "report"]}
        status_lines: list[str] = []
        progress = st.progress(0)
        status_box = st.empty()
        agent_box = st.empty()

        import concurrent.futures
        import queue
        import time
        from agent import WorkflowProgress

        progress_queue: queue.Queue[WorkflowProgress] = queue.Queue()

        def thread_safe_on_progress(p: WorkflowProgress) -> None:
            # ONLY push to thread-safe queue from background thread. DO NOT touch Streamlit UI here.
            progress_queue.put(p)

        def update_ui_from_progress(p: WorkflowProgress) -> None:
            try:
                step_name = p.step
                step_msg = p.message
                status_lines.append(f"{step_name}: {step_msg}" if step_msg else step_name)
                mapping = {
                    WebsiteWorkflowStep.URL_VALIDATED.value: ("website",),
                    WebsiteWorkflowStep.CRAWLING_PAGES.value: ("website",),
                    WebsiteWorkflowStep.WEBSITE_LOADED.value: ("website",),
                    WebsiteWorkflowStep.BUILDING_SITEMAP.value: ("website",),
                    WebsiteWorkflowStep.ANALYZING_PAGES.value: ("page_analysis",),
                    WebsiteWorkflowStep.DETECTING_FUNCS.value: ("functionality",),
                    WebsiteWorkflowStep.FEATURE_UNDERSTANDING.value: ("scenario",),
                    WebsiteWorkflowStep.SCENARIO_PLANNING.value: ("scenario",),
                    WebsiteWorkflowStep.TEST_GENERATION.value: ("testcase",),
                    WebsiteWorkflowStep.EXPANDING_CASES.value: ("testcase",),
                    WebsiteWorkflowStep.RISK_ANALYSIS.value: ("validator",),
                    WebsiteWorkflowStep.VALIDATING.value: ("validator",),
                    WebsiteWorkflowStep.REPORT_READY.value: ("report",),
                }
                for step_val, keys in mapping.items():
                    if step_name == step_val:
                        for k in keys:
                            steps[k] = "done" if step_name == WebsiteWorkflowStep.REPORT_READY.value else "running"

                if step_name == WebsiteWorkflowStep.REPORT_READY.value:
                    for k in steps:
                        steps[k] = "done"

                progress.progress(min(len(status_lines) / 14, 1.0))
                with status_box.container():
                    st.info(f"🤖 **AI Agent Progress:** {step_name} — {step_msg}")
                with agent_box.container():
                    render_agent_activity(steps, st.session_state.get("show_agent_activity", True))
            except Exception:
                pass

        def run_website_task():
            orchestrator = QATestCaseOrchestrator()
            return orchestrator.run_website(
                url,
                max_pages=max_pages,
                requested_test_cases=requested_test_cases,
                analysis_options={
                    "ui_elements": True,
                    "forms": True,
                    "navigation": True,
                    "opt_screenshots": opt_screenshots,
                    "opt_funcs": opt_funcs,
                    "opt_testcases": opt_testcases,
                    "opt_risks": opt_risks,
                    "opt_coverage": opt_coverage,
                },
                on_progress=thread_safe_on_progress,
                run_browser_checks=run_checks,
            )

        try:
            with st.spinner("Running AI Website QA Agent pipeline..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_website_task)
                    # Poll queue on the MAIN Streamlit thread while task executes
                    while not future.done():
                        time.sleep(0.05)
                        while not progress_queue.empty():
                            try:
                                item = progress_queue.get_nowait()
                                update_ui_from_progress(item)
                            except queue.Empty:
                                break
                    # Drain remaining queued progress items after task completes
                    while not progress_queue.empty():
                        try:
                            item = progress_queue.get_nowait()
                            update_ui_from_progress(item)
                        except queue.Empty:
                            break
                    report = future.result()

            st.session_state.current_report = report
            history_item = make_history_item(report)
            st.session_state.report_history = [history_item] + st.session_state.get("report_history", [])
            st.session_state.selected_report_id = history_item.id
            st.success("Complete Website QA Analysis finished!")
        except Exception as exc:
            st.error(f"Analysis error: {exc}")
            if not st.session_state.get("demo_mode"):
                with st.expander("Technical Error Log"):
                    st.code(traceback.format_exc())

    report = st.session_state.get("current_report")
    if report and report.mode == "website" and report.website_analysis:
        _render_website_results(report)


def _render_website_results(report) -> None:
    wa = report.website_analysis
    st.divider()
    st.markdown("### 📊 Complete Website QA Analysis Dashboard")
    
    # 1. Test Case Count Banner
    render_test_case_count_banner(report)

    # 2. Executive Summary Metrics
    cols = st.columns(6)
    stats = [
        ("Pages Discovered", wa.pages_discovered or len(wa.sitemap)),
        ("Pages Analyzed", wa.pages_analyzed),
        ("Pages Skipped", wa.pages_skipped),
        ("Functionalities", len(report.functionalities)),
        ("Total Test Cases", len(report.test_cases)),
        ("Coverage", f"{report.coverage_score:.0f}%"),
    ]
    for col, (label, val) in zip(cols, stats):
        with col:
            metric_card(label, str(val), alt=True)

    # 3. Eight Primary QA Tabs
    tabs = st.tabs([
        "🗺️ Website Map",
        "📄 Pages",
        "⚙️ Functionalities",
        "🧪 Test Cases",
        "📊 Coverage",
        "⚠️ Risks",
        "📸 Screenshots",
        "📑 Final Report"
    ])

    with tabs[0]:
        render_sitemap_visual(report)

    with tabs[1]:
        render_pages_table(report.page_analyses)

    with tabs[2]:
        render_functionalities_grid(report.page_analyses)

    with tabs[3]:
        render_test_cases_by_page_and_functionality(report)

    with tabs[4]:
        render_page_coverage_breakdown(report)

    with tabs[5]:
        render_risk_matrix(report)
        st.markdown("#### 💡 Recommendations")
        for rec in report.recommendations:
            st.markdown(f"- {rec}")

    with tabs[6]:
        render_screenshots_gallery(report.page_analyses)

    with tabs[7]:
        st.markdown("### 📑 Final Website QA Report")
        st.markdown(report.to_markdown())
        st.divider()
        render_export_buttons(report)


def page_requirement_generator() -> None:
    st.markdown('<p class="hero-title">🧪 Test Case Generator</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Generate detailed test cases from software requirements</p>', unsafe_allow_html=True)

    example = st.selectbox("Example requirement", ["Custom"] + list(DEMO_REQUIREMENTS.keys()))
    if example != "Custom":
        st.session_state.requirement_text = DEMO_REQUIREMENTS[example]
    requirement = st.text_area("Requirement", value=st.session_state.get("requirement_text", ""), height=140)
    st.session_state.requirement_text = requirement

    c1, c2 = st.columns(2)
    with c1:
        requested_count = st.number_input("Target Number of Test Cases", min_value=1, max_value=200, value=20)
    with c2:
        st.caption("The AI agent will generate structured test cases covering positive, negative, boundary, UI, and edge cases.")

    if st.button("🚀 Generate Test Cases", type="primary", use_container_width=True):
        valid, msg = validate_configuration()
        if not valid:
            st.error(msg)
            return
        if not requirement.strip():
            st.error("Please enter a requirement.")
            return
        steps = {k: "pending" for k in ["requirement", "scenario", "testcase", "risk", "validator"]}
        prog = st.progress(0)
        act = st.empty()

        def on_progress(p):
            order = ["requirement", "scenario", "testcase", "risk", "validator"]
            for i, key in enumerate(order):
                steps[key] = "done" if i < len(order) - 1 else "running"
            prog.progress(0.2 * (order.index("requirement") + 1))
            with act.container():
                render_agent_activity(steps, st.session_state.get("show_agent_activity", True))

        try:
            with st.spinner("Running agent pipeline..."):
                report = QATestCaseOrchestrator().run(requirement, requested_test_cases=requested_count, on_progress=on_progress)
            st.session_state.current_report = report
            item = make_history_item(report)
            st.session_state.report_history = [item] + st.session_state.get("report_history", [])
            st.session_state.selected_report_id = item.id
            st.success("Test cases generated!")
        except Exception as exc:
            st.error(f"Agent workflow failed: {exc}")

    report = st.session_state.get("current_report")
    if report and report.mode == "requirement":
        st.divider()
        render_test_case_count_banner(report)
        if report.requirement_analysis:
            ra = report.requirement_analysis
            st.markdown(f"**Feature:** {ra.feature} | **Behavior:** {ra.expected_behavior}")
        render_test_cases_table(report)
        render_page_coverage_breakdown(report)
        render_export_buttons(report)


def page_coverage() -> None:
    st.markdown('<p class="hero-title">📊 Test Coverage</p>', unsafe_allow_html=True)
    report = st.session_state.get("current_report")
    if not report:
        st.info("Run an analysis first to view coverage.")
        return
    render_page_coverage_breakdown(report)
    st.markdown("#### Validation Checks")
    for name, passed in report.validation_details.get("checks", {}).items():
        st.markdown(f"{'✅' if passed else '❌'} {name.replace('_', ' ').title()}")
    st.markdown("#### Missing Areas")
    for item in report.missing_areas:
        st.markdown(f"- {item}")


def page_risks() -> None:
    st.markdown('<p class="hero-title">⚠️ Risk Analysis</p>', unsafe_allow_html=True)
    report = st.session_state.get("current_report")
    if not report:
        st.info("Run an analysis first.")
        return
    render_risk_matrix(report)
    st.markdown("#### Recommendations")
    for rec in report.recommendations:
        st.markdown(f"- {rec}")


def page_reports() -> None:
    st.markdown('<p class="hero-title">📁 Test Reports</p>', unsafe_allow_html=True)
    history = st.session_state.get("report_history", [])
    if not history:
        st.info("No reports yet.")
        return
    for item in history:
        with st.expander(f"{item.title} — {item.created_at} ({item.test_case_count} cases, {item.coverage_score:.0f}%)"):
            st.markdown(f"**Source:** {item.source}")
            st.markdown(f"**Mode:** {item.mode} | **Risk:** {item.risk_level} | **Status:** {item.status}")
            if st.button(f"Load report", key=f"load_{item.id}"):
                st.session_state.selected_report_id = item.id
    report = st.session_state.get("current_report")
    if report:
        st.divider()
        render_export_buttons(report)


def page_settings() -> None:
    st.markdown('<p class="hero-title">⚙️ Settings</p>', unsafe_allow_html=True)
    valid, msg = validate_configuration()
    st.markdown(f"**Model:** {get_model_id()}")
    st.markdown(f"**Status:** {'Configured' if valid else 'Configuration issue'}")
    if not valid:
        st.error(msg)
