"""
SIH26056: Real-Time Airfare Price Index for India
Real MakeMyTrip / Indian OTA Scraper Engine
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

class MakeMyTripScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.platform_name = "makemytrip"

    def search_route(
        self,
        origin_iata: str,
        dest_iata: str,
        travel_date_str: str,  # YYYY-MM-DD
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        """
        Queries MakeMyTrip flight search interface.
        URL format: https://www.makemytrip.com/flight/search?itinerary={origin}-{dest}-{DD/MM/YYYY}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E
        """
        origin_iata = normalize_iata(origin_iata)
        dest_iata = normalize_iata(dest_iata)
        route_str = f"{origin_iata}-{dest_iata}"
        
        search_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_date = datetime.now().date()
        travel_date_obj = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        lead_time = (travel_date_obj - search_date).days
        
        formatted_date = travel_date_obj.strftime("%d/%m/%Y")
        url = f"https://www.makemytrip.com/flight/search?itinerary={origin_iata}-{dest_iata}-{formatted_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"

        observations: List[ScrapedFlightObservation] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
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
                except Exception as goto_err:
                    print(f" (Navigation notice: {goto_err}) ", end="")
                time.sleep(3) # Wait for flight listing cards to populate
                
                # Check for overlay dismiss / modal
                try:
                    close_btn = page.query_selector("span.commonModal__close, button.buttonClose")
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
                except:
                    pass

                # MMT flight cards typically reside in .listingCard or div[id^='listing-card']
                flight_cards = page.query_selector_all(".listingCard, .listingCardWrap, div[id*='flight_list_item']")
                
                if not flight_cards:
                    # Fallback to general listing container
                    flight_cards = page.query_selector_all("div[class*='listingCard']")

                for idx, card in enumerate(flight_cards):
                    try:
                        text_content = card.inner_text()
                        if not text_content or ('₹' not in text_content and 'Rs' not in text_content):
                            continue
                        
                        # Price extraction
                        price_match = re.search(r'₹\s*([\d,]+)', text_content)
                        if not price_match:
                            price_match = re.search(r'Rs\.?\s*([\d,]+)', text_content)
                        if not price_match:
                            continue
                            
                        price_val = parse_price(price_match.group(1))
                        if not price_val or pd.isna(price_val):
                            continue
                            
                        # Airline extraction
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
                            
                        # Departure & Arrival times (e.g. 06:15 ... 08:30)
                        times = re.findall(r'\b([012]?\d:[0-5]\d)\b', text_content)
                        dep_time = times[0] if len(times) >= 1 else "00:00"
                        arr_time = times[1] if len(times) >= 2 else "00:00"
                        
                        # Duration
                        dur_match = re.search(r'(\d+\s*(?:h|hr)\s*(?:\d+\s*(?:m|min))?)', text_content, re.IGNORECASE)
                        duration_str = dur_match.group(1).strip() if dur_match else ""
                        duration_mins = parse_duration_to_mins(duration_str)
                        
                        is_nonstop = 'non stop' in text_content.lower() or 'non-stop' in text_content.lower() or 'direct' in text_content.lower()
                        
                        raw_hash = hashlib.md5(f"{route_str}_{travel_date_str}_{airline_std}_{dep_time}_{price_val}".encode()).hexdigest()[:12]
                        rec_id = f"SCR_MMT_{int(time.time())}_{idx+1:03d}"
                        
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
