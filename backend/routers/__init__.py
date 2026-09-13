"""
SIH26056 Modular API Routers
"""
from backend.routers.overview import router as overview_router
from backend.routers.daily_index import router as daily_index_router
from backend.routers.routes import router as routes_router
from backend.routers.airlines import router as airlines_router
from backend.routers.observations import router as observations_router
from backend.routers.analytics import router as analytics_router
from backend.routers.scraper import router as scraper_router
from backend.routers.replay import router as replay_router
from backend.routers.backtest import router as backtest_router
from backend.routers.auth import router as auth_router

__all__ = [
    "overview_router",
    "daily_index_router",
    "routes_router",
    "airlines_router",
    "observations_router",
    "analytics_router",
    "scraper_router",
    "replay_router",
    "backtest_router",
    "auth_router"
]
