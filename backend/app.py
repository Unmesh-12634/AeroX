"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Production FastAPI Server Application
Problem Statement: SIH26056 (Smart Automation - Dr. Aaditya Maheshwari)
"""

import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.routers import (
    overview_router,
    daily_index_router,
    routes_router,
    airlines_router,
    observations_router,
    analytics_router,
    scraper_router,
    replay_router,
    backtest_router,
    auth_router
)
from backend.routers.predictions import router as predictions_router
from backend.routers.training import router as training_router


from fastapi.openapi.utils import get_openapi
from backend.docs_config import OPENAPI_TAGS, API_DESCRIPTION, generate_redoc_page


app = FastAPI(
    title="AEROX — Real-Time Airfare Price Index for India (APIx)",
    description=API_DESCRIPTION,
    version="3.0.0 (SIH 2026 Edition)",
    docs_url="/docs",
    redoc_url=None,  # Custom ReDoc rendered at /redoc
    openapi_tags=OPENAPI_TAGS,
    contact={
        "name": "Team AeroX • Smart India Hackathon 2026 (SIH26056)",
        "url": "http://localhost:8000",
        "email": "team.aerox.sih@gmail.com",
    },
    license_info={
        "name": "Ministry of Civil Aviation (MoCA) & DGCA Domain — SIH26056 Specification",
        "url": "https://www.dgca.gov.in",
    },
    terms_of_service="https://sih.gov.in"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Ms"] = f"{process_time * 1000:.2f}"
    return response

# Register Modular API Routers under /api/v1
app.include_router(overview_router, prefix=settings.API_V1_PREFIX)
app.include_router(daily_index_router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_router, prefix=settings.API_V1_PREFIX)
app.include_router(airlines_router, prefix=settings.API_V1_PREFIX)
app.include_router(observations_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(scraper_router, prefix=settings.API_V1_PREFIX)
app.include_router(replay_router, prefix=settings.API_V1_PREFIX)
app.include_router(backtest_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions_router, prefix=settings.API_V1_PREFIX)
app.include_router(training_router, prefix=settings.API_V1_PREFIX)

# Static Frontend Mounts
if settings.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.FRONTEND_DIR)), name="static")
    logos_dir = settings.FRONTEND_DIR / "logos"
    if logos_dir.exists():
        app.mount("/logos", StaticFiles(directory=str(logos_dir)), name="logos")
    icons_dir = settings.FRONTEND_DIR / "icons"
    if icons_dir.exists():
        app.mount("/icons", StaticFiles(directory=str(icons_dir)), name="icons")

@app.get("/manifest.json")
def serve_manifest():
    manifest_path = settings.FRONTEND_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(
            manifest_path,
            media_type="application/manifest+json",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    return JSONResponse({"error": "manifest not found"}, status_code=404)

@app.get("/sw.js")
def serve_service_worker():
    sw_path = settings.FRONTEND_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(
            sw_path,
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    return JSONResponse({"error": "service worker not found"}, status_code=404)

@app.get("/offline.html")
def serve_offline_html():
    offline_path = settings.FRONTEND_DIR / "offline.html"
    if offline_path.exists():
        return FileResponse(offline_path, media_type="text/html")
    return JSONResponse({"error": "offline page not found"}, status_code=404)

@app.get("/")
def serve_index():
    index_path = settings.FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return JSONResponse({
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "docs": "/docs"
    })

@app.get("/redoc", include_in_schema=False)
def serve_custom_redoc():
    return generate_redoc_page(
        openapi_url="/openapi.json",
        title="AEROX API Documentation | Team AeroX — SIH 2026 (SIH26056)"
    )


from backend.scheduler import scheduler

@app.on_event("startup")
def on_app_startup():
    scheduler.start()

@app.on_event("shutdown")
def on_app_shutdown():
    scheduler.stop()

@app.get("/healthz")
def health_check():
    return {
        "status": "HEALTHY",
        "timestamp": time.time(),
        "version": settings.VERSION
    }
