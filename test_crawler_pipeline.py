"""Verification script for Complete Website Crawler & Test Case Generator pipeline."""

from __future__ import annotations

import logging
import sys

from website_analyzer import WebsiteInspector, validate_url, _normalize_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_url_normalization():
    print("Testing URL normalization...")
    u1 = "https://www.example.com/about/?utm_source=google&ref=123#section"
    norm1 = _normalize_url(u1)
    assert norm1 == "https://www.example.com/about", f"Expected https://www.example.com/about, got {norm1}"
    
    u2 = "HTTPS://WWW.EXAMPLE.COM/contact/"
    norm2 = _normalize_url(u2)
    assert norm2 == "https://www.example.com/contact", f"Expected https://www.example.com/contact, got {norm2}"
    print("[PASS] URL normalization passed!")


def test_url_validation():
    print("Testing URL validation...")
    valid, url = validate_url("saucedemo.com")
    assert valid, "URL validation failed for saucedemo.com"
    assert url == "https://saucedemo.com", f"Unexpected validated URL: {url}"
    print("[PASS] URL validation passed!")


def test_playwright_inspection():
    print("Testing Playwright crawler on https://www.saucedemo.com/...")
    inspector = WebsiteInspector(timeout_ms=20000)
    analysis = inspector.analyze("https://www.saucedemo.com/", max_pages=2)
    print(f"Accessible: {analysis.accessible}")
    print(f"Pages Discovered: {analysis.pages_discovered}")
    print(f"Pages Analyzed: {analysis.pages_analyzed}")
    print(f"Pages Skipped: {analysis.pages_skipped}")
    print(f"Sitemap: {analysis.sitemap}")
    print(f"Interactive Elements Count: {analysis.interactive_elements_count}")
    assert analysis.accessible, "Website should be accessible!"
    assert analysis.pages_analyzed >= 1, "At least 1 page should be analyzed!"
    print("[PASS] Playwright inspection passed!")


if __name__ == "__main__":
    try:
        test_url_normalization()
        test_url_validation()
        test_playwright_inspection()
        print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    except Exception as exc:
        print(f"\nTEST FAILED: {exc}")
        sys.exit(1)
