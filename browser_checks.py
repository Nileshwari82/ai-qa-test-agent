"""Safe Playwright checks for generated test cases (non-destructive)."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import sys
from pathlib import Path

from models import BrowserCheckResult, TestCase, WebsiteAnalysis

logger = logging.getLogger(__name__)
CHECK_DIR = Path(__file__).parent / "outputs" / "checks"
CHECK_DIR.mkdir(parents=True, exist_ok=True)


def run_safe_browser_checks(
    analysis: WebsiteAnalysis,
    test_cases: list[TestCase],
    max_checks: int = 8,
) -> list[BrowserCheckResult]:
    """Perform safe visibility/existence checks — no form submissions or destructive actions."""
    def _worker():
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            except Exception:
                pass
        return _run_checks_internal(analysis, test_cases, max_checks)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_worker).result()


def _run_checks_internal(
    analysis: WebsiteAnalysis,
    test_cases: list[TestCase],
    max_checks: int = 8,
) -> list[BrowserCheckResult]:
    if not analysis.accessible or not analysis.url:
        return []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [
            BrowserCheckResult(
                test="Playwright availability",
                result="SKIP",
                evidence="Playwright not installed",
            )
        ]

    results: list[BrowserCheckResult] = []
    selectors_to_check: list[tuple[str, str]] = []

    for button in analysis.buttons[:5]:
        selectors_to_check.append((f"Button visible: {button.text}", button.selector))
    for field in analysis.inputs[:5]:
        label = field.label or field.name or field.placeholder or field.input_type
        selectors_to_check.append((f"Input visible: {label}", field.selector))

    selectors_to_check = selectors_to_check[:max_checks]

    with sync_playwright() as playwright:
        import shutil
        executable = shutil.which("chromium") or shutil.which("chromium-browser")
        if executable:
            try:
                browser = playwright.chromium.launch(headless=True, executable_path=executable)
            except Exception:
                browser = playwright.chromium.launch(headless=True)
        else:
            browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(analysis.url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            browser.close()
            return [
                BrowserCheckResult(
                    test="Page load",
                    result="FAIL",
                    evidence=str(exc),
                )
            ]

        for test_name, selector in selectors_to_check:
            try:
                locator = page.locator(selector).first
                visible = locator.is_visible(timeout=3000)
                screenshot_path = CHECK_DIR / f"check_{len(results)+1}.png"
                if visible:
                    locator.scroll_into_view_if_needed(timeout=2000)
                    page.screenshot(path=str(screenshot_path))
                    results.append(
                        BrowserCheckResult(
                            test=test_name,
                            result="PASS",
                            evidence=str(screenshot_path),
                            selector=selector,
                        )
                    )
                else:
                    results.append(
                        BrowserCheckResult(
                            test=test_name,
                            result="FAIL",
                            evidence="Element not visible",
                            selector=selector,
                        )
                    )
            except Exception as exc:
                results.append(
                    BrowserCheckResult(
                        test=test_name,
                        result="FAIL",
                        evidence=str(exc),
                        selector=selector,
                    )
                )
        browser.close()

    return results
