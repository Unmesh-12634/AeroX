"""
SIH26056 Scraper Package
"""
from .models import ScrapedFlightObservation, normalize_iata, normalize_airline
from .google_flights_scraper import GoogleFlightsScraper
from .makemytrip_scraper import MakeMyTripScraper
from .easemytrip_scraper import EaseMyTripScraper
from .scraper_orchestrator import ScraperOrchestrator
