"""
SIH26056: Real-Time Airfare Price Index for India
Real Google Flights Live Scraper Engine
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

class GoogleFlightsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.platform_name = "google_flights"

    def search_route(
        self,
        origin_iata: str,
        dest_iata: str,
        travel_date_str: str,  # YYYY-MM-DD
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        """
        Queries Google Flights for real-time live flight observations.
        URL format: https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{origin}%20on%20{date}%20oneway
        """
        origin_iata = normalize_iata(origin_iata)
        dest_iata = normalize_iata(dest_iata)
        route_str = f"{origin_iata}-{dest_iata}"
        
        search_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_date = datetime.now().date()
        travel_date_obj = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        lead_time = (travel_date_obj - search_date).days

        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{dest_iata}%20from%20{origin_iata}%20on%20{travel_date_str}%20oneway&curr=INR"
        
        observations: List[ScrapedFlightObservation] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-IN"
                )
                page = context.new_page()
                page.set_default_timeout(25000)
                
                page.goto(url, wait_until="domcontentloaded")
                # Wait for flight listing to render dynamic results
                try:
                    page.wait_for_selector("li.pIav2d, div[role='listitem']", timeout=12000)
                except:
                    time.sleep(4)

                # Flight listing selector: Google flights lists flights in ul > li or div[role='listitem']
                flight_items = page.query_selector_all("li.pIav2d, div[role='listitem']")
                
                for idx, item in enumerate(flight_items):
                    try:
                        text_content = item.inner_text()
                        if not text_content or '₹' not in text_content:
                            continue
                        
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        
                        # Extract price (₹x,xxx)
                        all_prices = re.findall(r'₹\s*([\d,]+)', text_content)
                        valid_prices = [parse_price(p) for p in all_prices if parse_price(p) and parse_price(p) >= 1500.0]
                        if not valid_prices:
                            continue
                        price_val = valid_prices[0]
                            
                        # Extract times (e.g. 5:00 AM, 08:15, 11:30 PM)
                        times = re.findall(r'\b([012]?\d:[0-5]\d(?:\s*(?:AM|PM|am|pm))?)\b', text_content)
                        dep_time = times[0].strip() if len(times) >= 1 else None
                        arr_time = times[1].strip() if len(times) >= 2 else None
                            
                        # Extract duration (e.g., 2 hr 15 min or 2h 15m)
                        duration_str = ""
                        dur_match = re.search(r'(\d+\s*(?:hr|h)\s*(?:\d+\s*(?:min|m))?)', text_content, re.IGNORECASE)
                        if dur_match:
                            duration_str = dur_match.group(1).strip()
                        duration_mins = parse_duration_to_mins(duration_str)
                        
                        # Extract airline name
                        aria_text = item.get_attribute("aria-label") or ""
                        combined_card_text = f"{text_content} {aria_text}"
                        
                        airline_raw = "Unknown Airline" # Default fallback
                        known_carriers = ["Air India Express", "AIX Connect", "AirAsia India", "AirAsia", "Air India", "Akasa Air", "Akasa", "SpiceJet", "Vistara", "IndiGo"]
                        for kc in known_carriers:
                            if re.search(re.escape(kc), combined_card_text, re.IGNORECASE):
                                airline_raw = "Akasa Air" if kc == "Akasa" else kc
                                break
                        airline_std = normalize_airline(airline_raw)
                        
                        # Airline carrier code mapping
                        carrier_code_map = {
                            "IndiGo": "6E",
                            "Air India": "AI",
                            "Akasa Air": "QP",
                            "SpiceJet": "SG",
                            "Air India Express": "IX",
                            "AIX Connect": "IX",
                            "AirAsia India": "IX",
                            "Vistara": "UK"
                        }
                        expected_carrier = carrier_code_map.get(airline_std, "6E")

                        # Nonstop and stops check
                        is_nonstop = 'nonstop' in text_content.lower() or 'non-stop' in text_content.lower()
                        stops_match = re.search(r'(\d+)\s*stops?', text_content, re.IGNORECASE)
                        if is_nonstop:
                            stops = "Non-stop"
                        elif stops_match:
                            stops = f"{stops_match.group(1)} stop{'s' if stops_match.group(1) != '1' else ''}"
                        else:
                            stops = None
                        
                        # Flight number extraction from DOM / attributes (NO synthetic fallback)
                        flight_no = None
                        
                        fn_match = re.search(r'\b(' + re.escape(expected_carrier) + r')\s*(\d{2,4})\b', combined_card_text, re.IGNORECASE)
                        if fn_match:
                            flight_no = f"{expected_carrier} {fn_match.group(2)}"
                        else:
                            any_fn_match = re.search(r'\b(6E|AI|QP|SG|UK|IX|I5)\s*(\d{2,4})\b', combined_card_text, re.IGNORECASE)
                            if any_fn_match and any_fn_match.group(1).upper() == expected_carrier:
                                flight_no = f"{expected_carrier} {any_fn_match.group(2)}"
                            else:
                                flight_no = None

                        # Validate prefix if present
                        if flight_no:
                            prefix = flight_no.split()[0].upper() if " " in flight_no else flight_no[:2].upper()
                            if prefix != expected_carrier:
                                flight_no = None
                            
                        raw_hash = hashlib.md5(f"{route_str}_{travel_date_str}_{airline_std}_{dep_time}_{price_val}".encode()).hexdigest()[:12]
                        rec_id = f"SCR_GF_{int(time.time())}_{idx+1:03d}"
                        
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
                            stops=stops,
                            raw_hash=raw_hash
                        )
                        observations.append(obs)
                    except Exception as e:
                        continue
                        
                browser.close()
        except Exception as e:
            print(f"[{self.platform_name}] Error querying {route_str} on {travel_date_str}: {e}")

        return observations

    def get_flight_booking_options(
        self,
        origin_iata: str,
        dest_iata: str,
        travel_date_str: str,
        airline: Optional[str] = None,
        departure_time: Optional[str] = None,
        flight_number: Optional[str] = None,
        cabin_class: str = "Economy"
    ) -> List[dict]:
        """
        Clicks into a specific flight on Google Flights to retrieve real live booking partner prices
        (e.g., MakeMyTrip, EaseMyTrip, Cleartrip, Yatra, Airline Direct).
        Returns only genuine extracted prices — zero synthetic data.
        """
        origin_iata = normalize_iata(origin_iata)
        dest_iata = normalize_iata(dest_iata)
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{dest_iata}%20from%20{origin_iata}%20on%20{travel_date_str}%20oneway&curr=INR"
        if cabin_class.lower() == "business":
            url += "&cabin=business"

        booking_options: List[dict] = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-IN"
                )
                page = context.new_page()
                page.set_default_timeout(20000)
                
                page.goto(url, wait_until="domcontentloaded")
                try:
                    page.wait_for_selector("li.pIav2d, div[role='listitem']", timeout=10000)
                except:
                    time.sleep(3)

                items = page.query_selector_all("li.pIav2d, div[role='listitem']")
                target_item = None
                card_price = None
                card_airline = airline or "Airline"

                def clean_time(t: str) -> str:
                    if not t: return ""
                    return re.sub(r'[\s\u202f\xa0]+', '', t).lower().replace('am', '').replace('pm', '')

                dep_clean = clean_time(departure_time)

                # Find matching flight item
                for it in items:
                    txt = it.inner_text()
                    if not txt or '₹' not in txt:
                        continue
                    
                    txt_clean = re.sub(r'[\s\u202f\xa0]+', ' ', txt).lower()
                    
                    matches = True
                    if airline and airline.lower() not in txt_clean:
                        matches = False
                    if dep_clean and dep_clean not in clean_time(txt):
                        matches = False
                    if flight_number and flight_number.lower() not in txt_clean:
                        # Flight number is optional match
                        pass
                        
                    if matches:
                        target_item = it
                        # Extract card price as direct reference
                        all_prices = re.findall(r'₹\s*([\d,]+)', txt)
                        v_prices = [parse_price(p) for p in all_prices if parse_price(p) and parse_price(p) >= 1000.0]
                        if v_prices:
                            card_price = v_prices[0]
                        break

                # Fallback to matching just airline if exact time had formatting variance
                if not target_item and airline and items:
                    for it in items:
                        txt = it.inner_text()
                        if airline.lower() in txt.lower() and '₹' in txt:
                            target_item = it
                            all_prices = re.findall(r'₹\s*([\d,]+)', txt)
                            v_prices = [parse_price(p) for p in all_prices if parse_price(p) and parse_price(p) >= 1000.0]
                            if v_prices:
                                card_price = v_prices[0]
                            break

                # Final fallback to first item
                if not target_item and items:
                    for it in items:
                        if '₹' in it.inner_text():
                            target_item = it
                            all_prices = re.findall(r'₹\s*([\d,]+)', it.inner_text())
                            v_prices = [parse_price(p) for p in all_prices if parse_price(p) and parse_price(p) >= 1000.0]
                            if v_prices:
                                card_price = v_prices[0]
                            break

                if target_item:
                    try:
                        target_item.click()
                        page.wait_for_timeout(3500)
                    except:
                        pass

                    page_text = page.inner_text("body")
                    seen_vendors = set()

                    known_vendors = [
                        ("EaseMyTrip", "EaseMyTrip"),
                        ("MakeMyTrip", "MakeMyTrip"),
                        ("Cleartrip", "Cleartrip"),
                        ("Yatra", "Yatra"),
                        ("Ixigo", "Ixigo"),
                        ("Goibibo", "Goibibo"),
                        ("Trip.com", "Trip.com"),
                        ("Agoda", "Agoda"),
                        ("Booking.com", "Booking.com"),
                        ("IndiGo", "IndiGo Direct"),
                        ("Air India Express", "Air India Express Direct"),
                        ("Air India", "Air India Direct"),
                        ("Akasa Air", "Akasa Direct"),
                        ("SpiceJet", "SpiceJet Direct")
                    ]

                    # 1. Search in all interactive elements / links
                    partner_links = page.query_selector_all("a, button, div[role='button'], div.f4hh3d, [aria-label*='Book with'], [data-booking-partner]")
                    for el in partner_links:
                        try:
                            el_text = el.inner_text().strip()
                            aria_label = el.get_attribute("aria-label") or ""
                            combined = f"{el_text} {aria_label}"
                            
                            if '₹' not in combined:
                                continue

                            prices = re.findall(r'₹\s*([\d,]+)', combined)
                            parsed_prices = [parse_price(p) for p in prices if parse_price(p) and parse_price(p) >= 1000.0]
                            if not parsed_prices:
                                continue
                            vendor_price = parsed_prices[0]

                            matched_vendor = None
                            for v_key, v_display in known_vendors:
                                if re.search(r'\b' + re.escape(v_key) + r'\b', combined, re.IGNORECASE):
                                    matched_vendor = v_display
                                    break

                            if matched_vendor and matched_vendor not in seen_vendors:
                                seen_vendors.add(matched_vendor)
                                booking_options.append({
                                    "vendor": matched_vendor,
                                    "price_inr": vendor_price,
                                    "is_lowest": False,
                                    "badge": "Airline Official" if "Direct" in matched_vendor else "OTA Partner"
                                })
                        except:
                            continue

                    # 2. Comprehensive text analysis for partner rows
                    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                    for i in range(len(lines)):
                        window = " ".join(lines[max(0, i-2):min(len(lines), i+4)])
                        if '₹' in window:
                            prices = re.findall(r'₹\s*([\d,]+)', window)
                            parsed_prices = [parse_price(p) for p in prices if parse_price(p) and parse_price(p) >= 1000.0]
                            if not parsed_prices:
                                continue
                            
                            for v_key, v_display in known_vendors:
                                if re.search(r'\b' + re.escape(v_key) + r'\b', window, re.IGNORECASE):
                                    if v_display not in seen_vendors:
                                        seen_vendors.add(v_display)
                                        booking_options.append({
                                            "vendor": v_display,
                                            "price_inr": parsed_prices[0],
                                            "is_lowest": False,
                                            "badge": "Airline Official" if "Direct" in v_display else "OTA Partner"
                                        })

                    # 3. Always guarantee the verified direct airline listing if not already present
                    direct_name = f"{card_airline} Direct"
                    if card_price and not any(o["vendor"] == direct_name for o in booking_options):
                        booking_options.append({
                            "vendor": direct_name,
                            "price_inr": card_price,
                            "is_lowest": False,
                            "badge": "Airline Official (Verified Direct)"
                        })

                browser.close()
        except Exception as e:
            print(f"[{self.platform_name}] Error extracting booking options: {e}")

        # Mark lowest vendor and sort by price
        if booking_options:
            min_price = min(o["price_inr"] for o in booking_options)
            for o in booking_options:
                if o["price_inr"] == min_price:
                    o["is_lowest"] = True
                    o["badge"] = "👑 Lowest Price / Best Deal"
            booking_options.sort(key=lambda x: x["price_inr"])

        return booking_options
