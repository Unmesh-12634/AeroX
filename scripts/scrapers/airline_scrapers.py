"""
SIH26056: Real-Time Airfare Price Index for India
Direct Airline Portal Scrapers: IndiGo, Air India, Akasa Air, SpiceJet
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

class BaseAirlinePortalScraper:
    def __init__(self, airline_name: str, headless: bool = True):
        self.airline_name = airline_name
        self.platform_name = f"{airline_name.lower().replace(' ', '')}_direct"
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
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-IN",
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()
                page.set_default_timeout(30000)
                
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(4)
                
                # Extract cards / rows
                cards = page.query_selector_all("div[class*='flight'], div[class*='fare'], tr[class*='flight'], div[class*='trip-row'], div[class*='flight-row']")
                if not cards:
                    cards = page.query_selector_all("div:has-text('₹'):not(:has(div:has-text('₹')))")

                for idx, card in enumerate(cards):
                    try:
                        text = card.inner_text()
                        if not text or ('₹' not in text and 'Rs' not in text):
                            continue
                            
                        price_match = re.search(r'₹\s*([\d,]+)', text)
                        if not price_match:
                            price_match = re.search(r'Rs\.?\s*([\d,]+)', text)
                        if not price_match:
                            continue
                            
                        price_val = parse_price(price_match.group(1))
                        if not price_val or pd.isna(price_val) or price_val < 500:
                            continue
                            
                        airline_std = normalize_airline(self.airline_name)
                        
                        flight_no = None
                        fn_match = re.search(r'\b(6E|AI|QP|SG|UK|IX|I5)[\s-]*(\d{3,4})\b', text)
                        if fn_match:
                            flight_no = f"{fn_match.group(1)} {fn_match.group(2)}"
                            
                        times = re.findall(r'\b([012]?\d:[0-5]\d)\b', text)
                        dep_time = times[0] if len(times) >= 1 else "00:00"
                        arr_time = times[1] if len(times) >= 2 else "00:00"
                        
                        dur_match = re.search(r'(\d+\s*(?:h|hr)\s*(?:\d+\s*(?:m|min))?)', text, re.IGNORECASE)
                        dur_str = dur_match.group(1).strip() if dur_match else ""
                        duration_mins = parse_duration_to_mins(dur_str)
                        
                        raw_hash = hashlib.md5(f"{route_str}_{travel_date_str}_{self.platform_name}_{dep_time}_{price_val}".encode()).hexdigest()[:12]
                        rec_id = f"SCR_{self.airline_name[:3].upper()}_{int(time.time())}_{idx+1:03d}"
                        
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
                            airline_raw=self.airline_name,
                            flight_number=flight_no,
                            departure_time=dep_time,
                            arrival_time=arr_time,
                            duration_minutes=duration_mins,
                            duration_raw=dur_str,
                            cabin_class=cabin_class,
                            total_fare_inr=price_val,
                            is_nonstop=True,
                            raw_hash=raw_hash
                        )
                        observations.append(obs)
                    except Exception:
                        continue
                        
                browser.close()
        except Exception as e:
            print(f"[{self.platform_name}] Error on {route_str} ({travel_date_str}): {e}")

        return observations

# 1. IndiGo Direct Scraper
class IndiGoDirectScraper(BaseAirlinePortalScraper):
    def __init__(self, headless: bool = True):
        super().__init__(airline_name="IndiGo", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%Y-%m-%d")
        return f"https://www.goindigo.in/flight-booking.html?origin={origin}&destination={dest}&travelDate={d_str}&isOneWay=true"

# 2. Air India Direct Scraper
class AirIndiaDirectScraper(BaseAirlinePortalScraper):
    def __init__(self, headless: bool = True):
        super().__init__(airline_name="Air India", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%Y-%m-%d")
        return f"https://www.airindia.com/in/en/book/flight-search.html?from={origin}&to={dest}&date={d_str}&adults=1"

# 3. Akasa Air Direct Scraper
class AkasaDirectScraper(BaseAirlinePortalScraper):
    def __init__(self, headless: bool = True):
        super().__init__(airline_name="Akasa Air", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%Y-%m-%d")
        return f"https://www.akasaair.com/flight-search?origin={origin}&destination={dest}&date={d_str}"

# 4. SpiceJet Direct Scraper
class SpiceJetDirectScraper(BaseAirlinePortalScraper):
    def __init__(self, headless: bool = True):
        super().__init__(airline_name="SpiceJet", headless=headless)

    def get_search_url(self, origin: str, dest: str, travel_date: datetime.date) -> str:
        d_str = travel_date.strftime("%Y-%m-%d")
        return f"https://www.spicejet.com/flights?origin={origin}&destination={dest}&date={d_str}"
