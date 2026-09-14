"""
SIH26056: Real-Time Airfare Price Index for India
Server Launcher Script (FastAPI + Uvicorn)
"""

import os
import sys
import uvicorn

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def run_server(host=None, port=None):
    host = host or os.environ.get("HOST", "0.0.0.0")
    port = port or int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print("SIH26056 AIRFARE PRICE INDEX (APIx) SERVER")
    print(f"Serving Dashboard UI at: http://localhost:{port} (and on LAN at http://0.0.0.0:{port})")
    print(f"API Documentation at:     http://localhost:{port}/docs")
    print("=" * 60)
    uvicorn.run("backend.app:app", host=host, port=port, reload=True, log_level="info")

if __name__ == "__main__":
    run_server()
