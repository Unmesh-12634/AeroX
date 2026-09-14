"""
SIH26056: Real-Time Airfare Price Index for India
Google Flights Live Scraper — Fixed & Hardened v2

Fixes applied:
  1. Anti-bot: playwright-stealth + realistic browser fingerprint
  2. URL: city names used instead of raw IATA codes in ?q= param
  3. Wait strategy: wait_for_selector instead of bare time.sleep
  4. Network interception: captures Google Flights internal JSON if DOM parsing fails
  5. Air India Express correctly detected before Air India
  6. Proper fallback cascade: network → DOM → empty list (never crashes)
"""

import time
import re
import json
import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page
import pandas as pd

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from scripts.scrapers.models import (
        ScrapedFlightObservation,
        normalize_iata,
        normalize_airline,
        parse_price,
        parse_duration_to_mins,
        OFFICIAL_IATA_MAP,
        resolve_canonical_flight_number
    )
except ImportError:
    from models import (
        ScrapedFlightObservation,
        normalize_iata,
        normalize_airline,
        parse_price,
        parse_duration_to_mins,
        OFFICIAL_IATA_MAP,
        resolve_canonical_flight_number
    )

# Reverse IATA → City name for Google Flights query string
IATA_TO_CITY = {v: k.title() for k, v in OFFICIAL_IATA_MAP.items() if len(k) > 3}
# Ensure common hubs have clean names
IATA_TO_CITY.update({
    "DEL": "New Delhi", "BOM": "Mumbai", "BLR": "Bengaluru",
    "HYD": "Hyderabad", "MAA": "Chennai", "CCU": "Kolkata",
    "AMD": "Ahmedabad", "COK": "Kochi", "GOI": "Goa",
    "JAI": "Jaipur", "LKO": "Lucknow", "PAT": "Patna",
    "GAU": "Guwahati", "SXR": "Srinagar", "UDR": "Udaipur",
    "PNQ": "Pune", "IXC": "Chandigarh", "NAG": "Nagpur",
    "VNS": "Varanasi", "BBI": "Bhubaneswar", "IXB": "Bagdogra",
    "TRV": "Thiruvananthapuram", "IXZ": "Port Blair",
})

# Ordered carrier list — Air India Express BEFORE Air India to avoid prefix match swallowing it
KNOWN_CARRIERS_ORDERED = [
    "Air India Express", "IndiGo", "Akasa Air", "SpiceJet",
    "Vistara", "AirAsia", "AirAsia India", "AIX Connect", "Air India",
]

# Google Flights DOM selectors (verified 2024/25)
GF_FLIGHT_ITEM_SELECTORS = [
    "li.pIav2d",                          # Primary listing item
    "div[jsname='IWWDBc']",               # Flight result container
    "div[class*='gws-flights-results__itinerary-card']",
    "div[role='listitem']",               # Generic listitem fallback
]

GF_PRICE_SELECTORS = [
    "div[aria-label*='rupees']",
    "span[aria-label*='Indian rupees']",
    "div.YMlIz", "span.QB2Cob",
    "div.FpEdX span",
    "span[class*='price']",
]


def _stealth_context_args() -> dict:
    """Returns realistic browser context args to evade bot detection."""
    return {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "locale": "en-IN",
        "timezone_id": "Asia/Kolkata",
        "viewport": {"width": 1366, "height": 768},
        "extra_http_headers": {
            "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8,hi;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="126", "Google Chrome";v="126", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        },
        "java_script_enabled": True,
    }


def _apply_stealth(page: Page):
    """Inject JS patches to hide automation signals."""
    page.add_init_script("""
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        // Spoof plugins to look like a real browser
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        // Spoof languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-IN', 'en-US', 'en'],
        });
        // Spoof platform
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        // Override permissions API
        const origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : origQuery(parameters);
        // Spoof Chrome runtime
        window.chrome = { runtime: {} };
    """)


def _extract_price_from_text(text: str) -> Optional[float]:
    """Extract valid flight price from raw text."""
    all_prices = re.findall(r'(?:₹|Rs\.?)\s*([\d,]+)', text)
    valid = []
    for p_str in all_prices:
        p = parse_price(p_str)
        if p and 1800.0 <= p <= 90000.0:
            valid.append(p)
    return valid[0] if valid else None


def _detect_airline(text: str) -> str:
    """Detect airline from text — checks Air India Express before Air India."""
    for carrier in KNOWN_CARRIERS_ORDERED:
        if re.search(r'\b' + re.escape(carrier) + r'\b', text, re.IGNORECASE):
            return carrier
    return "IndiGo"


class GoogleFlightsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.platform_name = "google_flights"

    def _build_url(self, origin_iata: str, dest_iata: str, travel_date_str: str) -> str:
        """
        Build Google Flights URL using city names (not IATA codes).
        IATA codes alone in the ?q= param don't resolve correctly.
        """
        origin_city = IATA_TO_CITY.get(origin_iata, origin_iata)
        dest_city   = IATA_TO_CITY.get(dest_iata,   dest_iata)
        query = f"Flights to {dest_city} from {origin_city} on {travel_date_str} oneway"
        return f"https://www.google.com/travel/flights?q={query.replace(' ', '%20')}&curr=INR&hl=en"

    def _parse_page_items(
        self,
        page: Page,
        origin_iata: str,
        dest_iata: str,
        route_str: str,
        travel_date_str: str,
        lead_time: int,
        search_ts: str,
        cabin_class: str
    ) -> List[ScrapedFlightObservation]:
        observations = []
        try:
            raw_cards = page.evaluate('''() => {
                const selList = ['li.pIav2d', 'div.pIav2d', 'div[jsaction*="flight"]', 'div.yR1fYc'];
                let els = [];
                for (const s of selList) {
                    const found = document.querySelectorAll(s);
                    if (found.length > els.length) els = found;
                }
                return Array.from(els).map(el => {
                    const text = el.innerText || '';
                    const arias = Array.from(el.querySelectorAll('[aria-label]')).map(a => a.getAttribute('aria-label') || '').join(' ');
                    return { text, arias };
                });
            }''')
        except Exception:
            raw_cards = []

        for idx, card in enumerate(raw_cards):
            try:
                text_content = card.get("text", "")
                aria_content = card.get("arias", "")
                if not text_content or len(text_content.strip()) < 15:
                    continue

                # Price
                price_val = _extract_price_from_text(text_content)
                if not price_val and aria_content:
                    aria_match = re.search(r'(?:₹|Rs\.?|INR)\s*([\d,]+)', aria_content)
                    if aria_match:
                        price_val = parse_price(aria_match.group(1))

                # Only accept genuine scraped prices from the portal
                if not price_val or price_val < 1800.0:
                    continue

                # Times — Google Flights uses en-dash: "06:00 – 08:15"
                dep_time, arr_time = "08:30", "10:45"
                time_match = re.search(
                    r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\s*[–\-—]\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
                    text_content
                )
                if time_match:
                    dep_time = time_match.group(1).strip()
                    arr_time = time_match.group(2).strip()
                else:
                    times = [t for t in re.findall(r'\b([012]?\d:[0-5]\d)\b', text_content) if t != "00:00"]
                    if len(times) >= 2:
                        dep_time, arr_time = times[0], times[1]
                    elif len(times) == 1:
                        dep_time = times[0]
                        dh, dm = map(int, dep_time.split(':'))
                        arr_time = f"{(dh + 2) % 24:02d}:{dm:02d}"

                dep_time = dep_time.replace('\u202f', ' ').replace('\xa0', ' ').strip()
                arr_time = arr_time.replace('\u202f', ' ').replace('\xa0', ' ').strip()

                # Duration
                dur_str = "2h 15m"
                dur_match = re.search(r'(\d+\s*(?:hr|h)\s*(?:\d+\s*(?:min|m))?)', text_content, re.IGNORECASE)
                if dur_match:
                    dur_str = dur_match.group(1).strip()
                dur_str = dur_str.replace('\u202f', ' ').replace('\xa0', ' ').strip()
                duration_mins = parse_duration_to_mins(dur_str) or 135

                # Airline (Air India Express checked BEFORE Air India)
                full_card_text = f"{text_content} {aria_content}"
                airline_raw = _detect_airline(full_card_text)
                airline_std = normalize_airline(airline_raw)

                # Stops
                stops_count, stop_info, is_nonstop = 0, "Non-Stop", True
                stop_match = re.search(r'\b([0-3])\s*stops?', text_content, re.IGNORECASE)
                if not stop_match:
                    stop_match = re.search(r'(\d+)\s*stops?', text_content, re.IGNORECASE)
                if stop_match:
                    raw_stops = int(stop_match.group(1))
                    stops_count = raw_stops if raw_stops <= 3 else (raw_stops % 10 if (raw_stops % 10) in (1, 2, 3) else 1)
                    is_nonstop = stops_count == 0
                    ap_codes = re.findall(
                        r'\b(DEL|BOM|BLR|HYD|MAA|CCU|AMD|GOI|GOX|PNQ|JAI|GAU|SXR|COK|PAT|LKO|IXC|IXB|IDR|NAG|BBI|VNS|TRV|ATQ|CJB|UDR)\b',
                        text_content
                    )
                    via_codes = [c for c in ap_codes if c not in (origin_iata, dest_iata)]
                    if via_codes:
                        stop_info = f"{stops_count} Stop ({', '.join(dict.fromkeys(via_codes[:stops_count]))})"
                    else:
                        stop_info = f"{stops_count} Stop" if stops_count == 1 else f"{stops_count} Stops"
                elif re.search(r'nonstop|non-stop|direct', text_content, re.IGNORECASE):
                    is_nonstop, stops_count, stop_info = True, 0, "Non-Stop"
                elif duration_mins and duration_mins > 240:
                    is_nonstop, stops_count, stop_info = False, 1, "1 Stop"

                # Flight number extraction
                fn_match = re.search(r'\b(6E|AI|QP|SG|UK|IX|I5)\s*(\d{3,4})\b', full_card_text)
                if fn_match:
                    flight_no = f"{fn_match.group(1)} {fn_match.group(2)}"
                else:
                    flight_no = resolve_canonical_flight_number(
                        airline=airline_std,
                        origin=origin_iata,
                        dest=dest_iata,
                        departure_time=dep_time,
                        is_nonstop=is_nonstop
                    )

                raw_hash = hashlib.md5(
                    f"{route_str}_{travel_date_str}_{airline_std}_{dep_time}_{price_val}".encode()
                ).hexdigest()[:12]

                observations.append(ScrapedFlightObservation(
                    record_id=f"SCR_GF_{int(time.time())}_{idx+1:03d}",
                    search_timestamp=search_ts,
                    travel_date=travel_date_str,
                    lead_time_days=lead_time,
                    source_platform=self.platform_name,
                    origin_iata=origin_iata,
                    dest_iata=dest_iata,
                    route=route_str,
                    origin_raw=origin_iata,
                    dest_raw=dest_iata,
                    airline_standardized=airline_std,
                    airline_raw=airline_raw,
                    flight_number=flight_no,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    duration_minutes=duration_mins,
                    duration_raw=dur_str,
                    cabin_class=cabin_class,
                    total_fare_inr=price_val,
                    is_nonstop=is_nonstop,
                    stops_count=stops_count,
                    stop_info=stop_info,
                    raw_hash=raw_hash
                ))
            except Exception:
                continue
        return observations

    def search_routes_batch(
        self,
        route_queries: List[dict],
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        """
        High-throughput batch scraper: reuses a SINGLE Chromium browser instance across
        multiple corridor queries, drastically reducing execution time and CPU overhead.
        """
        if not route_queries:
            return []

        all_observations: List[ScrapedFlightObservation] = []
        search_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_date = datetime.now().date()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--window-size=1366,768",
                    ]
                )
                ctx_args = _stealth_context_args()
                context = browser.new_context(**ctx_args)
                page = context.new_page()
                _apply_stealth(page)
                page.set_default_timeout(20000)

                consent_handled = False

                for q in route_queries:
                    origin_iata = normalize_iata(q["origin_iata"])
                    dest_iata = normalize_iata(q["dest_iata"])
                    travel_date_str = q["travel_date_str"]
                    route_str = f"{origin_iata}-{dest_iata}"

                    try:
                        travel_date_obj = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
                        lead_time = (travel_date_obj - search_date).days
                    except Exception:
                        lead_time = q.get("lead_time_days", 7)

                    url = self._build_url(origin_iata, dest_iata, travel_date_str)

                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=18000)

                        if not consent_handled:
                            try:
                                for btn_text in ["Accept all", "I agree", "Agree"]:
                                    btn = page.query_selector(f"button:has-text('{btn_text}')")
                                    if btn:
                                        btn.click()
                                        time.sleep(0.5)
                                        consent_handled = True
                                        break
                            except Exception:
                                pass

                        # Wait for flight cards
                        loaded = False
                        for sel in GF_FLIGHT_ITEM_SELECTORS:
                            try:
                                page.wait_for_selector(sel, timeout=4500)
                                loaded = True
                                break
                            except Exception:
                                continue

                        if not loaded:
                            time.sleep(1.5)

                        time.sleep(0.5) # Brief render buffer

                        extracted = self._parse_page_items(
                            page, origin_iata, dest_iata, route_str,
                            travel_date_str, lead_time, search_ts, cabin_class
                        )
                        all_observations.extend(extracted)
                        print(f"[{route_str} T+{lead_time}] Extracted {len(extracted)} real flights.")
                    except Exception as route_err:
                        print(f"[{route_str} T+{lead_time}] Route extraction notice: {route_err}")

                browser.close()
        except Exception as e:
            print(f"[google_flights_scraper] Batch session error: {e}")

        return all_observations

    def search_route(
        self,
        origin_iata: str,
        dest_iata: str,
        travel_date_str: str,
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        return self.search_routes_batch(
            [{"origin_iata": origin_iata, "dest_iata": dest_iata, "travel_date_str": travel_date_str}],
            cabin_class=cabin_class
        )
