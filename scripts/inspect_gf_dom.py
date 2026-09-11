import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    url = "https://www.google.com/travel/flights?q=Flights%20to%20BOM%20from%20DEL%20on%202026-09-17%20oneway&curr=INR"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("li.pIav2d", timeout=12000)
    items = page.query_selector_all("li.pIav2d")
    print(f"Found {len(items)} items.")
    for i, it in enumerate(items[:5], 1):
        print(f"\n=== ITEM {i} ===")
        print("TEXT:\n", it.inner_text())
        print("ARIA:\n", it.get_attribute("aria-label"))
    browser.close()
