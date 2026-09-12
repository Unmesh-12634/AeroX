import sys, os
sys.path.insert(0, os.path.abspath("."))
import time
from playwright.sync_api import sync_playwright
from scripts.scrapers.google_flights_scraper import (
    GoogleFlightsScraper, _stealth_context_args, _apply_stealth,
    GF_FLIGHT_ITEM_SELECTORS, GF_PRICE_SELECTORS, _extract_price_from_text,
    _detect_airline, normalize_airline, parse_duration_to_mins
)
import re

routes = [("DEL", "BOM"), ("DEL", "BLR"), ("BOM", "BLR")]
travel_date = "2026-09-19"

t0 = time.time()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    context = browser.new_context(**_stealth_context_args())
    page = context.new_page()
    _apply_stealth(page)

    scraper = GoogleFlightsScraper(headless=True)
    for orig, dest in routes:
        t_sub = time.time()
        url = scraper._build_url(orig, dest, travel_date)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            # wait briefly for flight items
            for sel in GF_FLIGHT_ITEM_SELECTORS:
                try:
                    page.wait_for_selector(sel, timeout=6000)
                    break
                except Exception:
                    pass
            time.sleep(1.0)
            items = []
            for sel in GF_FLIGHT_ITEM_SELECTORS:
                it = page.query_selector_all(sel)
                if len(it) > len(items):
                    items = it
            print(f"[{orig}-{dest}] Found {len(items)} items in {round(time.time() - t_sub, 2)}s")
            # print first item sample
            if items:
                txt = items[0].inner_text().replace('\n', ' | ')[:120]
                print(f"   Sample: {txt}")
        except Exception as e:
            print(f"[{orig}-{dest}] Error: {e}")
    browser.close()

print(f"Total 3 routes completed in {round(time.time() - t0, 2)}s")
