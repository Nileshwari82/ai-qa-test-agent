import asyncio
import concurrent.futures
import sys
from playwright.sync_api import sync_playwright

def run_playwright():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com")
        title = page.title()
        browser.close()
        return title

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_playwright)
        result = future.result()
        print("Playwright launched successfully in thread pool! Page title:", result)
