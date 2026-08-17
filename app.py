"""QA Agent Pro — AI-Powered Website Testing & Test Case Generation Platform."""

from __future__ import annotations

import asyncio
import logging
import sys

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

import streamlit as st

from ui.pages import (
    page_coverage,
    page_dashboard,
    page_reports,
    page_requirement_generator,
    page_risks,
    page_settings,
    page_website_analyzer,
)
from ui.styles import CUSTOM_CSS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

PAGES = {
    "🏠 Dashboard": page_dashboard,
    "🌐 Website Analyzer": page_website_analyzer,
    "🧪 Test Case Generator": page_requirement_generator,
    "📊 Test Coverage": page_coverage,
    "⚠️ Risk Analysis": page_risks,
    "📁 Test Reports": page_reports,
    "⚙️ Settings": page_settings,
}


def init_state() -> None:
    defaults = {
        "page": "🏠 Dashboard",
        "current_report": None,
        "report_history": [],
        "requirement_text": "",
        "website_url": "https://www.saucedemo.com/",
        "demo_mode": False,
        "show_agent_activity": True,
        "default_crawl_depth": 3,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def ensure_playwright_browsers() -> None:
    """Safely check if Playwright Chromium is installed without blocking startup."""
    import shutil
    if shutil.which("chromium") or shutil.which("chromium-browser"):
        return
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False, timeout=30)
    except Exception as exc:
        logging.warning("Playwright browser installation check failed: %s", exc)


def main() -> None:
    st.set_page_config(
        page_title="QA Agent Pro",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<p class="sidebar-brand">🤖 QA Agent Pro</p>', unsafe_allow_html=True)
        st.caption("AI-powered website analysis, test case generation and QA intelligence.")
        st.divider()
        page_keys = list(PAGES.keys())
        current = st.session_state.page if st.session_state.page in PAGES else page_keys[0]
        selection = st.radio("Navigation", page_keys, index=page_keys.index(current))
        st.session_state.page = selection

    if not st.session_state.get("demo_mode"):
        st.markdown('<p class="hero-title">🤖 QA Agent Pro</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hero-subtitle">AI-powered website analysis, test case generation and QA intelligence.</p>',
            unsafe_allow_html=True,
        )

    PAGES[selection]()


if __name__ == "__main__":
    main()
