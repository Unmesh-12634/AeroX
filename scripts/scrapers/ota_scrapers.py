"""
SIH26056: Real-Time Airfare Price Index for India
Real OTA Scrapers: MakeMyTrip, Yatra, EaseMyTrip, Cleartrip, Ixigo, Goibibo
"""

import time
import re
import hashlib
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional
from playwright.sync_api import sync_playwright
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from scripts.scrapers.models import (
        ScrapedFlightObservation,
        normalize_iata,
        normalize_airline,
        parse_price,
        parse_duration_to_mins
    )
except ImportError:
    from models import (
        ScrapedFlightObservation,
        normalize_iata,
        normalize_airline,
        parse_price,
        parse_duration_to_mins
    )

KNOWN_CARRIERS = ["IndiGo", "Air India", "Vistara", "Akasa Air", "SpiceJet", "AirAsia", "AIX Connect", "Air India Express"]

class BaseOTAPlaywrightScraper:
    def __init__(self, platform_name: str, headless: bool = True):
        self.platform_name = platform_name
        self.headless = headless

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        raise NotImplementedError

    def search_route(
        self,
        origin_iata: str,
        dest_iata: str,
        travel_date_str: str,  # YYYY-MM-DD
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        origin_iata = normalize_iata(origin_iata)
        dest_iata = normalize_iata(dest_iata)
        route_str = f"{origin_iata}-{dest_iata}"
        
        search_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_date = datetime.now().date()
        travel_date_obj = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        lead_time = (travel_date_obj - search_date).days

        url = self.get_search_url(origin_iata, dest_iata, travel_date_obj)
        observations: List[ScrapedFlightObservation] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-http2",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security"
                    ]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-IN",
                    viewport={"width": 1366, "height": 768},
                    extra_http_headers={
                        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
                        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                        "Sec-Ch-Ua-Mobile": "?0",
                        "Sec-Ch-Ua-Platform": '"Windows"',
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1"
                    }
                )
                page = context.new_page()
                page.set_default_timeout(25000)
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                except Exception as goto_e:
                    print(f" (Nav: {goto_e}) ", end="")
                time.sleep(3) # Allow dynamic XHR/DOM to render flight cards
                
                # Dismiss modal if present
                try:
                    close_btn = page.query_selector("span.commonModal__close, button.buttonClose, span.close, button[aria-label='Close']")
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
                except:
                    pass

                # Generic DOM extraction for flight result cards
                card_selectors = [
                    ".listingCard", ".listingCardWrap", "div[id*='flight_list_item']",
                    "div.flt-row", "div[class*='flt-result']", "div.row.flt-list",
                    "div[data-test-id*='flight']", ".flight-item", ".flightCard",
                    "div[class*='flightItem']", "div[class*='FlightCard']", "div[class*='listing-card']"
                ]
                
                flight_cards = []
                for sel in card_selectors:
                    found = page.query_selector_all(sel)
                    if found and len(found) > len(flight_cards):
                        flight_cards = found

                # Fallback: find all container divs containing prices
                if not flight_cards:
                    flight_cards = page.query_selector_all("div:has-text('₹'):not(:has(div:has-text('₹')))")

                for idx, card in enumerate(flight_cards):
                    try:
                        text = card.inner_text()
                        if not text or ('₹' not in text and 'Rs' not in text):
                            continue
                        
                        # Price regex
                        price_match = re.search(r'₹\s*([\d,]+)', text)
                        if not price_match:
                            price_match = re.search(r'Rs\.?\s*([\d,]+)', text)
                        if not price_match:
                            continue
                            
                        price_val = parse_price(price_match.group(1))
                        if not price_val or pd.isna(price_val) or price_val < 500:
                            continue
                            
                        # Airline
                        airline_raw = "IndiGo"
                        for kc in KNOWN_CARRIERS:
                            if re.search(r'\b' + re.escape(kc) + r'\b', text, re.IGNORECASE):
                                airline_raw = kc
                                break
                        airline_std = normalize_airline(airline_raw)
                        
                        # Flight Number
                        flight_no = None
                        fn_match = re.search(r'\b(6E|AI|QP|SG|UK|IX|I5)[\s-]*(\d{3,4})\b', text)
                        if fn_match:
                            flight_no = f"{fn_match.group(1)} {fn_match.group(2)}"
                            
                        # Departure & Arrival Times
                        times = re.findall(r'\b([012]?\d:[0-5]\d)\b', text)
                        dep_time = times[0] if len(times) >= 1 else "00:00"
                        arr_time = times[1] if len(times) >= 2 else "00:00"
                        
                        # Duration
                        dur_match = re.search(r'(\d+\s*(?:h|hr|hrs)\s*(?:\d+\s*(?:m|min|mins))?)', text, re.IGNORECASE)
                        dur_str = dur_match.group(1).strip() if dur_match else ""
                        duration_mins = parse_duration_to_mins(dur_str)
                        
                        is_nonstop = 'non stop' in text.lower() or 'non-stop' in text.lower() or 'direct' in text.lower()
                        
                        raw_hash = hashlib.md5(f"{route_str}_{travel_date_str}_{self.platform_name}_{airline_std}_{dep_time}_{price_val}".encode()).hexdigest()[:12]
                        rec_id = f"SCR_{self.platform_name[:3].upper()}_{int(time.time())}_{idx+1:03d}"
                        
                        obs = ScrapedFlightObservation(
                            record_id=rec_id,
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
                            raw_hash=raw_hash
                        )
                        observations.append(obs)
                    except Exception:
                        continue
                        
                browser.close()
        except Exception as e:
            print(f"[{self.platform_name}] Query error on {route_str} ({travel_date_str}): {e}")

        return observations

# 1. MakeMyTrip Scraper
class MakeMyTripScraper(BaseOTAPlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(platform_name="makemytrip", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%d/%m/%Y")
        return f"https://www.makemytrip.com/flight/search?itinerary={origin}-{dest}-{d_str}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"

# 2. Yatra Scraper
class YatraScraper(BaseOTAPlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(platform_name="yatra", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%d/%m/%Y")
        return f"https://flight.yatra.com/air-search/dom2/trigger?type=O&viewName=normal&flexi=0&noOfSegments=1&origin={origin}&originCode={origin}&destination={dest}&destinationCode={dest}&flight_depart_date={d_str}&ADT=1&CHD=0&INF=0&class=Economy"

# 3. EaseMyTrip Scraper
class EaseMyTripScraper(BaseOTAPlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(platform_name="easemytrip", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%d/%m/%Y")
        return f"https://flight.easemytrip.com/FlightList/Index?org={origin}&dept={dest}&adt=1&chd=0&inf=0&cls=0&dref={d_str}"

# 4. Cleartrip Scraper
class CleartripScraper(BaseOTAPlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(platform_name="cleartrip", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%d/%m/%Y")
        return f"https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date={d_str}&from={origin}&to={dest}&intl=n"

# 5. Ixigo Scraper
class IxigoScraper(BaseOTAPlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(platform_name="ixigo", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%d%m%Y")
        return f"https://www.ixigo.com/search/result/flight/{origin}/{dest}/{d_str}//1/0/0/e/0"

# 6. Goibibo Scraper
class GoibiboScraper(BaseOTAPlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(platform_name="goibibo", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%Y%m%d")
        return f"https://www.goibibo.com/flights/air-{origin}-{dest}-{d_str}--1-0-0-E-D/"
