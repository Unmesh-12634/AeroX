import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import json
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", locale="en-IN")
        page = context.new_page()
        page.set_default_timeout(25000)
        
        url = "https://www.google.com/travel/flights?q=Flights%20to%20BOM%20from%20DEL%20on%202026-09-17%20oneway&curr=INR"
        print("Navigating to URL...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector("li.pIav2d", timeout=12000)
            
        items = page.query_selector_all("li.pIav2d")
        print(f"Found {len(items)} flights.")
        if not items:
            browser.close()
            return
            
        first_flight = items[0]
        print("Clicking flight 1:", first_flight.inner_text().replace('\n', ' | ')[:100])
        first_flight.click()
        page.wait_for_timeout(3000)
        
        print("Current page URL:", page.url)
        # Wait for booking options section to load
        try:
            page.wait_for_selector("div[role='region'], div.X39p6b, a[href*='google.com/travel/clk'], div.X8sX5c", timeout=10000)
        except Exception as e:
            print("Notice waiting on booking selector:", e)
            
        # Get all text from booking page
        body_text = page.inner_text("body")
        print("\n--- ALL TEXT ON BOOKING PAGE (First 3000 chars) ---")
        print(body_text[:3000])
        print("\n--- END TEXT ---")
        
        # Look for buttons or partner links
        links = page.query_selector_all("a, button, div[role='button']")
        print(f"\nTotal interactive elements: {len(links)}")
        for el in links:
            t = el.inner_text().strip()
            if '₹' in t or any(v in t.lower() for v in ['book with', 'makemytrip', 'easemytrip', 'cleartrip', 'yatra', 'air india', 'indigo', 'akasa', 'spicejet', 'trip.com', 'agoda', 'booking.com']):
                print("  INTERACTIVE OPTION:", t.replace('\n', ' || '))
                
        browser.close()

if __name__ == "__main__":
    inspect()
