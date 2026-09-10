"""
SIH26056: Real-Time Airfare Price Index for India
Real EaseMyTrip Scraper Engine
"""

import time
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from playwright.sync_api import sync_playwright
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

class EaseMyTripScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.platform_name = "easemytrip"

    def search_route(
        self,
        origin_iata: str,
        dest_iata: str,
        travel_date_str: str,  # YYYY-MM-DD
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        """
        Queries EaseMyTrip flight search page.
        URL format: https://flight.easemytrip.com/FlightList/Index?org={origin}&dept={dest}&adt=1&chd=0&inf=0&cls=0&dref={DD/MM/YYYY}
        """
        origin_iata = normalize_iata(origin_iata)
        dest_iata = normalize_iata(dest_iata)
        route_str = f"{origin_iata}-{dest_iata}"
        
        search_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_date = datetime.now().date()
        travel_date_obj = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        lead_time = (travel_date_obj - search_date).days
        
        formatted_date = travel_date_obj.strftime("%d/%m/%Y")
        url = f"https://flight.easemytrip.com/FlightList/Index?org={origin_iata}&dept={dest_iata}&adt=1&chd=0&inf=0&cls=0&dref={formatted_date}"

        observations: List[ScrapedFlightObservation] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                page.set_default_timeout(30000)
                
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(4)
                
                flight_rows = page.query_selector_all("div.flt-row, div[class*='flt-result'], div.row.flt-list")
                if not flight_rows:
                    flight_rows = page.query_selector_all("div[id*='flt_'], div.listingCard")

                for idx, row in enumerate(flight_rows):
                    try:
                        text_content = row.inner_text()
                        if not text_content or ('₹' not in text_content and 'Rs' not in text_content):
                            continue
                            
                        # Price extraction (filter out coupon promo badges like ₹500)
                        all_prices = re.findall(r'(?:₹|Rs\.?)\s*([\d,]+)', text_content)
                        valid_prices = [parse_price(p) for p in all_prices if parse_price(p) and parse_price(p) >= 1500.0]
                        if not valid_prices:
                            continue
                        price_val = valid_prices[0]
                            
                        # Airline name
                        airline_raw = "IndiGo"
                        known_carriers = ["IndiGo", "Air India", "Vistara", "Akasa Air", "SpiceJet", "AirAsia", "AIX Connect"]
                        for kc in known_carriers:
                            if re.search(r'\b' + re.escape(kc) + r'\b', text_content, re.IGNORECASE):
                                airline_raw = kc
                                break
                        airline_std = normalize_airline(airline_raw)
                        
                        # Flight number
                        flight_no = None
                        fn_match = re.search(r'\b(6E|AI|QP|SG|UK|IX|I5)[\s-]*(\d{3,4})\b', text_content)
                        if fn_match:
                            flight_no = f"{fn_match.group(1)} {fn_match.group(2)}"
                            
                        times = re.findall(r'\b([012]?\d:[0-5]\d(?:\s*(?:AM|PM|am|pm))?)\b', text_content)
                        dep_time = times[0].strip() if len(times) >= 1 else "06:15"
                        arr_time = times[1].strip() if len(times) >= 2 else "08:30"
                        
                        dur_match = re.search(r'(\d+\s*(?:h|hr)\s*(?:\d+\s*(?:m|min))?)', text_content, re.IGNORECASE)
                        duration_str = dur_match.group(1).strip() if dur_match else ""
                        duration_mins = parse_duration_to_mins(duration_str)
                        
                        is_nonstop = 'non stop' in text_content.lower() or 'direct' in text_content.lower()
                        
                        raw_hash = hashlib.md5(f"{route_str}_{travel_date_str}_{airline_std}_{dep_time}_{price_val}".encode()).hexdigest()[:12]
                        rec_id = f"SCR_EMT_{int(time.time())}_{idx+1:03d}"
                        
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
                            duration_raw=duration_str,
                            cabin_class=cabin_class,
                            total_fare_inr=price_val,
                            is_nonstop=is_nonstop,
                            raw_hash=raw_hash
                        )
                        observations.append(obs)
                    except Exception as e:
                        continue
                        
                browser.close()
        except Exception as e:
            print(f"[{self.platform_name}] Error querying {route_str} on {travel_date_str}: {e}")

        return observations
