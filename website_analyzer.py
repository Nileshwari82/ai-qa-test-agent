"""Playwright-based website inspection and controlled crawling."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

from models import (
    DiscoveredButton,
    DiscoveredForm,
    DiscoveredInput,
    DiscoveredLink,
    PageAnalysisData,
    PageSummary,
    WebsiteAnalysis,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "outputs" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BLOCKED_LINK_KEYWORDS = {
    "logout",
    "log out",
    "sign out",
    "signout",
    "delete",
    "remove account",
    "purchase",
    "checkout",
    "pay now",
    "submit order",
    "cancel account",
    "unsubscribe",
    "cancel subscription",
    "remove item",
    "clear cart",
}

BLOCKED_PATH_KEYWORDS = {
    "/logout",
    "/signout",
    "/delete",
    "/checkout",
    "/payment",
    "/purchase",
    "/cancel-subscription",
    "/remove-account",
}


def validate_url(url: str) -> tuple[bool, str]:
    """Validate that a URL is suitable for inspection."""
    url = url.strip()
    if not url:
        return False, "URL cannot be empty."
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False, "Only HTTP/HTTPS URLs are supported."
    if not parsed.netloc:
        return False, "Invalid URL format."
    return True, url


def _same_domain(base: str, target: str) -> bool:
    base_netloc = urlparse(base).netloc.lower().replace("www.", "")
    target_netloc = urlparse(target).netloc.lower().replace("www.", "")
    return base_netloc == target_netloc


def _normalize_url(url: str) -> str:
    """Normalize URL by stripping fragment, trailing slashes, and non-functional tracking params."""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/") or "/"
        query_pairs = parse_qsl(parsed.query)
        filtered = [
            (k, v) for k, v in query_pairs
            if not k.lower().startswith(("utm_", "ref", "fbclid", "gclid", "source", "sid"))
        ]
        new_query = urlencode(filtered) if filtered else ""
        netloc = parsed.netloc.lower()
        scheme = parsed.scheme.lower()
        res = f"{scheme}://{netloc}{path}"
        if new_query:
            res += f"?{new_query}"
        return res
    except Exception:
        return url.split("#")[0].rstrip("/") or url


def _is_safe_link(href: str, text: str) -> bool:
    combined = f"{href} {text}".lower()
    if any(keyword in combined for keyword in BLOCKED_LINK_KEYWORDS):
        return False
    if any(keyword in href.lower() for keyword in BLOCKED_PATH_KEYWORDS):
        return False
    return True


def _build_selector(tag: str, element_id: str, name: str, classes: str) -> str:
    if element_id:
        return f"#{element_id}"
    if name:
        return f'{tag}[name="{name}"]'
    if classes:
        first_class = classes.split()[0]
        return f"{tag}.{first_class}"
    return tag


def _snippet(text: str, limit: int = 800) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:limit]


def _scroll_full_page(page, max_scrolls: int = 25, delay_ms: float = 0.15) -> None:
    """Scroll gradually from top to bottom to trigger lazy loading, then scroll back to top."""
    try:
        last_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
        for _ in range(max_scrolls):
            page.evaluate("window.scrollBy(0, 500);")
            time.sleep(delay_ms)
            current_scroll = page.evaluate("window.scrollY + window.innerHeight")
            scroll_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
            if current_scroll >= scroll_height and scroll_height == last_height:
                break
            last_height = scroll_height
        page.evaluate("window.scrollTo(0, 0);")
        time.sleep(0.2)
    except Exception as exc:
        logger.warning("Scrolling page failed: %s", exc)


def _detect_captcha(page, body_text: str) -> bool:
    """Check for CAPTCHA elements on the page."""
    low_text = body_text.lower()
    if "captcha" in low_text or "verify you are human" in low_text or "recaptcha" in low_text:
        return True
    try:
        if page.query_selector("iframe[src*='captcha'], iframe[src*='recaptcha'], .g-recaptcha, .h-captcha, #cf-turnstile"):
            return True
    except Exception:
        pass
    return False


def _detect_auth_required(page, response, body_text: str) -> bool:
    """Check if authentication is required or access is denied."""
    if response and response.status in {401, 403}:
        return True
    low_text = body_text.lower()
    if "access denied" in low_text or "401 unauthorized" in low_text or "403 forbidden" in low_text or "please log in to continue" in low_text:
        return True
    return False


import asyncio
import concurrent.futures
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse


def _launch_browser(playwright):
    """Launch Playwright Chromium with system executable fallback for Linux/Streamlit Cloud."""
    import shutil
    chrome_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ]
    executable = shutil.which("chromium") or shutil.which("chromium-browser")
    if executable:
        try:
            return playwright.chromium.launch(headless=True, executable_path=executable, args=chrome_args)
        except Exception as exc:
            logger.warning("Failed launching system chromium executable at %s: %s", executable, exc)
    try:
        return playwright.chromium.launch(headless=True, args=chrome_args)
    except Exception as exc:
        try:
            from app import ensure_playwright_browsers
            ensure_playwright_browsers()
            return playwright.chromium.launch(headless=True, args=chrome_args)
        except Exception as inner_exc:
            logger.error("Failed launching Playwright Chromium: %s", inner_exc)
            raise exc



class WebsiteInspector:
    """Inspect publicly accessible websites using Playwright."""

    def __init__(self, timeout_ms: int = 30000) -> None:
        self.timeout_ms = timeout_ms

    def analyze(
        self,
        url: str,
        max_pages: int = 3,
        options: dict | None = None,
        on_page_callback: Callable[[str, int, int], None] | None = None,
    ) -> WebsiteAnalysis:
        def _worker():
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                except Exception:
                    pass
            return self._analyze_internal(url, max_pages=max_pages, options=options, on_page_callback=on_page_callback)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(_worker).result()

    def _analyze_internal(
        self,
        url: str,
        max_pages: int = 3,
        options: dict | None = None,
        on_page_callback: Callable[[str, int, int], None] | None = None,
    ) -> WebsiteAnalysis:
        options = options or {}
        valid, result = validate_url(url)
        if not valid:
            return WebsiteAnalysis(
                url=url,
                domain="",
                accessible=False,
                access_message=result,
                crawl_depth=max_pages,
            )
        url = result
        domain = urlparse(url).netloc

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return WebsiteAnalysis(
                url=url,
                domain=domain,
                accessible=False,
                access_message=(
                    "Playwright is not installed. Run: pip install playwright && playwright install chromium"
                ),
                crawl_depth=max_pages,
                analysis_warnings=[str(exc)],
            )

        analysis = WebsiteAnalysis(url=url, domain=domain, accessible=False, crawl_depth=max_pages)
        visited: set[str] = set()
        queue: list[tuple[str, str]] = [(url, "Home")]  # (url, parent_label)
        warnings: list[str] = []
        discovered_sections: set[str] = set()
        sitemap_nodes: list[dict[str, Any]] = []

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QA-Agent-Pro/1.0 "
                    "(Educational QA analysis bot)"
                ),
            )
            page = context.new_page()
            page.set_default_timeout(self.timeout_ms)

            while queue and len(visited) < max_pages:
                current_url, parent_label = queue.pop(0)
                # Normalize URL for deduplication
                normalized_current = _normalize_url(current_url)
                if normalized_current in visited:
                    continue
                visited.add(normalized_current)

                page_index = len(analysis.page_analyses) + 1
                if on_page_callback:
                    on_page_callback(current_url, page_index, max_pages)

                url_path = urlparse(current_url).path or "/"

                page_data = PageAnalysisData(
                    url=current_url,
                    path=url_path,
                    title="Untitled",
                    status="Analyzed",
                )

                try:
                    response = page.goto(current_url, wait_until="domcontentloaded")
                    if response and response.status >= 400:
                        warnings.append(f"HTTP {response.status} for {current_url}")
                        page_data.status = "Failed"
                        page_data.warnings.append(f"HTTP {response.status}")
                        sitemap_nodes.append({
                            "url": current_url,
                            "path": url_path,
                            "title": "Failed to load",
                            "parent": parent_label,
                            "status": "🔴 Failed",
                        })
                        analysis.page_analyses.append(page_data)
                        analysis.pages_skipped += 1
                        continue
                except Exception as exc:
                    warnings.append(f"Failed to load {current_url}: {exc}")
                    page_data.status = "Failed"
                    page_data.warnings.append(str(exc))
                    if len(visited) == 1:
                        analysis.access_message = f"Website unavailable or timed out: {exc}"
                        browser.close()
                        analysis.analysis_warnings = warnings
                        return analysis
                    sitemap_nodes.append({
                        "url": current_url,
                        "path": url_path,
                        "title": "Error",
                        "parent": parent_label,
                        "status": "🔴 Failed",
                    })
                    analysis.page_analyses.append(page_data)
                    analysis.pages_skipped += 1
                    continue

                analysis.accessible = True
                analysis.access_message = "Website loaded successfully."

                # Scroll full page to trigger lazy loading
                _scroll_full_page(page)

                title = page.title() or "Untitled"
                page_data.title = title
                if not analysis.page_title:
                    analysis.page_title = title

                body_text = page.inner_text("body") if page.query_selector("body") else ""

                # Check for CAPTCHA / Auth Required
                if _detect_captcha(page, body_text):
                    page_data.status = "CAPTCHA Detected"
                    page_data.warnings.append("⚠ CAPTCHA Detected. Automated interaction was stopped for this page.")
                    analysis.pages_skipped += 1
                    sitemap_nodes.append({
                        "url": current_url,
                        "path": url_path,
                        "title": title,
                        "parent": parent_label,
                        "status": "⚠️ CAPTCHA Detected",
                    })
                    analysis.page_analyses.append(page_data)
                    continue

                if _detect_auth_required(page, response, body_text):
                    page_data.status = "Auth Required"
                    page_data.warnings.append("🔒 Authentication Required. Page requires credentials for full access.")
                    analysis.pages_skipped += 1
                    sitemap_nodes.append({
                        "url": current_url,
                        "path": url_path,
                        "title": title,
                        "parent": parent_label,
                        "status": "🔒 Auth Required",
                    })
                    analysis.page_analyses.append(page_data)
                    continue

                headings = page.eval_on_selector_all(
                    "h1, h2, h3, h4",
                    "els => els.map(e => e.innerText.trim()).filter(Boolean)",
                )
                page_data.headings = headings[:20]

                page_summary = PageSummary(
                    url=current_url,
                    title=title,
                    headings=headings[:20],
                    visible_text_snippet=_snippet(body_text),
                )
                analysis.pages.append(page_summary)

                # Capture Full-Page Screenshot for this page
                screenshot_filename = f"page_{len(analysis.page_analyses) + 1}_" + re.sub(r"[^\w.-]", "_", url_path.strip("/")) + ".png"
                if screenshot_filename == "page_1_.png":
                    screenshot_filename = "page_1_home.png"
                screenshot_path = OUTPUT_DIR / screenshot_filename
                try:
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    page_data.screenshot_path = str(screenshot_path)
                    if not analysis.screenshot_path:
                        analysis.screenshot_path = str(screenshot_path)
                except Exception as exc:
                    warnings.append(f"Full-page screenshot capture failed for {current_url}: {exc}")

                # Extract Sections
                sections = page.eval_on_selector_all(
                    "header, nav, main, section, article, footer, [role='region'], [role='main'], [role='banner']",
                    "els => els.map(e => (e.getAttribute('aria-label') || e.getAttribute('id') || e.tagName.toLowerCase()).trim()).filter(Boolean)",
                )
                page_data.sections = list(dict.fromkeys(sections + headings[:5]))
                discovered_sections.update(sections)
                discovered_sections.update(headings[:10])

                # Extract Elements per Page
                if options.get("ui_elements", True):
                    self._extract_buttons_for_page(page, current_url, page_data, analysis)
                    self._extract_inputs_for_page(page, current_url, page_data, analysis)
                    self._extract_links_for_page(page, current_url, page_data, analysis, queue, url, title)
                    self._extract_dropdowns_for_page(page, current_url, page_data, analysis)
                    self._extract_checkboxes_for_page(page, current_url, page_data, analysis)
                    self._extract_radios_for_page(page, current_url, page_data, analysis)
                    self._extract_cards_for_page(page, current_url, page_data, analysis)
                    self._extract_tables_for_page(page, current_url, page_data, analysis)

                if options.get("forms", True):
                    self._extract_forms_for_page(page, current_url, page_data, analysis)

                if options.get("navigation", True):
                    nav_items = page.eval_on_selector_all(
                        "nav a, [role='navigation'] a, header a, footer a",
                        "els => els.map(e => e.innerText.trim()).filter(Boolean)",
                    )
                    analysis.navigation.extend(item for item in nav_items if item)

                page_data.interactive_elements_count = (
                    len(page_data.buttons)
                    + len(page_data.inputs)
                    + len(page_data.dropdowns)
                    + len(page_data.checkboxes)
                    + len(page_data.radio_buttons)
                    + len(page_data.links)
                    + len(page_data.forms)
                )

                sitemap_nodes.append({
                    "url": current_url,
                    "path": url_path,
                    "title": title,
                    "parent": parent_label,
                    "status": "🟢 Analyzed",
                    "interactive_count": page_data.interactive_elements_count,
                })
                analysis.page_analyses.append(page_data)

            browser.close()

        analysis.sitemap = sitemap_nodes
        analysis.pages_discovered = len(sitemap_nodes)
        analysis.pages_analyzed = len(analysis.page_analyses)
        analysis.sections = list(dict.fromkeys(discovered_sections))
        analysis.sections_found = len(analysis.sections)
        analysis.interactive_elements_count = (
            len(analysis.buttons)
            + len(analysis.inputs)
            + len(analysis.dropdowns)
            + len(analysis.checkboxes)
            + len(analysis.radio_buttons)
            + len(analysis.links)
            + len(analysis.forms)
        )
        analysis.analysis_warnings = list(dict.fromkeys(warnings))
        if (
            analysis.accessible
            and not analysis.buttons
            and not analysis.inputs
            and not analysis.forms
            and not analysis.links
        ):
            analysis.analysis_warnings.append(
                "No interactive elements detected. The site may be login-protected, CAPTCHA-protected, or heavily JavaScript-dependent."
            )
        return analysis

    @staticmethod
    def _extract_buttons_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        buttons = page.query_selector_all(
            "button, input[type='submit'], input[type='button'], [role='button'], .btn, a.btn, a.button"
        )
        seen: set[str] = set()
        for button in buttons:
            try:
                text = (button.inner_text() or button.get_attribute("value") or button.get_attribute("title") or "").strip()
                if not text or text in seen:
                    continue
                seen.add(text)
                selector = _build_selector(
                    button.evaluate("el => el.tagName.toLowerCase()"),
                    button.get_attribute("id") or "",
                    button.get_attribute("name") or "",
                    button.get_attribute("class") or "",
                )
                btn_obj = DiscoveredButton(text=text[:120], selector=selector, page_url=current_url)
                page_data.buttons.append(btn_obj)
                analysis.buttons.append(btn_obj)
            except Exception:
                continue

    @staticmethod
    def _extract_inputs_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        inputs = page.query_selector_all("input, textarea")
        seen: set[str] = set()
        for field in inputs:
            try:
                input_type = (field.get_attribute("type") or field.evaluate("el => el.tagName.toLowerCase()")).lower()
                if input_type in {"hidden", "submit", "button", "checkbox", "radio"}:
                    continue
                name = field.get_attribute("name") or field.get_attribute("id") or ""
                placeholder = field.get_attribute("placeholder") or ""
                label = field.get_attribute("aria-label") or ""
                key = f"{name}|{input_type}|{placeholder}"
                if key in seen:
                    continue
                seen.add(key)
                selector = _build_selector(
                    field.evaluate("el => el.tagName.toLowerCase()"),
                    field.get_attribute("id") or "",
                    field.get_attribute("name") or "",
                    field.get_attribute("class") or "",
                )
                input_obj = DiscoveredInput(
                    name=name,
                    input_type=input_type,
                    placeholder=placeholder,
                    label=label,
                    selector=selector,
                    page_url=current_url,
                )
                page_data.inputs.append(input_obj)
                analysis.inputs.append(input_obj)
            except Exception:
                continue

    @staticmethod
    def _extract_dropdowns_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        selects = page.query_selector_all("select, [role='combobox'], [role='listbox']")
        seen: set[str] = set()
        for sel in selects:
            try:
                name = sel.get_attribute("name") or sel.get_attribute("id") or sel.get_attribute("aria-label") or "Dropdown"
                if name in seen:
                    continue
                seen.add(name)
                options = sel.eval_on_selector_all(
                    "option, [role='option']",
                    "els => els.map(e => e.innerText.trim()).filter(Boolean)",
                )
                drop_data = {
                    "name": name,
                    "options": options[:10],
                    "page_url": current_url,
                }
                page_data.dropdowns.append(drop_data)
                analysis.dropdowns.append(drop_data)
            except Exception:
                continue

    @staticmethod
    def _extract_checkboxes_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        boxes = page.query_selector_all("input[type='checkbox'], [role='checkbox']")
        seen: set[str] = set()
        for cb in boxes:
            try:
                label = cb.get_attribute("name") or cb.get_attribute("id") or cb.get_attribute("aria-label") or "Checkbox"
                if label in seen:
                    continue
                seen.add(label)
                cb_data = {
                    "label": label,
                    "checked": cb.is_checked() if hasattr(cb, "is_checked") else False,
                    "page_url": current_url,
                }
                page_data.checkboxes.append(cb_data)
                analysis.checkboxes.append(cb_data)
            except Exception:
                continue

    @staticmethod
    def _extract_radios_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        radios = page.query_selector_all("input[type='radio'], [role='radio']")
        seen: set[str] = set()
        for rb in radios:
            try:
                label = rb.get_attribute("name") or rb.get_attribute("id") or rb.get_attribute("value") or "Radio"
                if label in seen:
                    continue
                seen.add(label)
                rb_data = {
                    "label": label,
                    "page_url": current_url,
                }
                page_data.radio_buttons.append(rb_data)
                analysis.radio_buttons.append(rb_data)
            except Exception:
                continue

    @staticmethod
    def _extract_cards_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        cards = page.query_selector_all(".card, [class*='card'], [class*='product'], [class*='item']")
        seen: set[str] = set()
        for card in cards[:15]:
            try:
                title = card.inner_text().split("\n")[0].strip() if card.inner_text() else ""
                if title and title not in seen:
                    seen.add(title)
                    c_data = {"title": title[:80], "page_url": current_url}
                    page_data.cards.append(c_data)
                    analysis.cards.append(c_data)
            except Exception:
                continue

    @staticmethod
    def _extract_tables_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        tables = page.query_selector_all("table, [role='table']")
        for index, tbl in enumerate(tables[:5], start=1):
            try:
                headers = tbl.eval_on_selector_all("th", "els => els.map(e => e.innerText.trim()).filter(Boolean)")
                t_data = {
                    "id": tbl.get_attribute("id") or f"table-{index}",
                    "headers": headers[:10],
                    "page_url": current_url,
                }
                page_data.tables.append(t_data)
                analysis.tables.append(t_data)
            except Exception:
                continue

    @staticmethod
    def _extract_links_for_page(
        page,
        current_url: str,
        page_data: PageAnalysisData,
        analysis: WebsiteAnalysis,
        queue: list[tuple[str, str]],
        base_url: str,
        page_title: str,
    ) -> None:
        anchors = page.query_selector_all("a[href], [data-href], [role='link'][href]")
        seen_hrefs: set[str] = set()
        queue_urls = {_normalize_url(item[0]) for item in queue}

        for anchor in anchors:
            try:
                href = anchor.get_attribute("href") or anchor.get_attribute("data-href") or ""
                text = (anchor.inner_text() or anchor.get_attribute("aria-label") or anchor.get_attribute("title") or "").strip()[:120]
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                    continue
                absolute = urljoin(current_url, href)
                norm_abs = _normalize_url(absolute)
                if norm_abs in seen_hrefs:
                    continue
                seen_hrefs.add(norm_abs)

                link_obj = DiscoveredLink(text=text or norm_abs, href=norm_abs, page_url=current_url)
                page_data.links.append(link_obj)
                analysis.links.append(link_obj)

                if _is_safe_link(norm_abs, text) and _same_domain(base_url, norm_abs):
                    if norm_abs not in queue_urls:
                        queue.append((norm_abs, page_title or current_url))
                        queue_urls.add(norm_abs)
            except Exception:
                continue

    @staticmethod
    def _extract_forms_for_page(page, current_url: str, page_data: PageAnalysisData, analysis: WebsiteAnalysis) -> None:
        forms = page.query_selector_all("form")
        for index, form in enumerate(forms, start=1):
            try:
                action = form.get_attribute("action") or current_url
                method = (form.get_attribute("method") or "get").upper()
                form_id = form.get_attribute("id") or f"form-{index}"
                fields = form.eval_on_selector_all(
                    "input, textarea, select",
                    "els => els.map(e => e.name || e.id || e.placeholder || e.type).filter(Boolean)",
                )
                form_obj = DiscoveredForm(
                    form_id=form_id,
                    action=urljoin(current_url, action),
                    method=method,
                    fields=fields[:20],
                    page_url=current_url,
                )
                page_data.forms.append(form_obj)
                analysis.forms.append(form_obj)
            except Exception:
                continue


def website_analysis_summary(analysis: WebsiteAnalysis) -> dict:
    """Compact summary for LLM prompts representing full-page structure."""
    page_summaries = []
    for p in analysis.page_analyses:
        page_summaries.append({
            "url": p.url,
            "title": p.title,
            "status": p.status,
            "headings": p.headings[:5],
            "functionalities": [f.name for f in p.functionalities],
            "buttons_count": len(p.buttons),
            "inputs_count": len(p.inputs),
            "forms_count": len(p.forms),
        })
    return {
        "url": analysis.url,
        "title": analysis.page_title,
        "pages_analyzed": analysis.pages_analyzed,
        "pages_discovered": analysis.pages_discovered,
        "pages_skipped": analysis.pages_skipped,
        "pages_detail": page_summaries,
        "sections": analysis.sections[:15],
        "all_functionalities": [f.model_dump() for f in analysis.all_functionalities[:30]],
        "warnings": analysis.analysis_warnings,
    }
