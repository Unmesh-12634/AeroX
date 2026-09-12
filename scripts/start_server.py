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

def run_server(host="127.0.0.1", port=8000):
    print("=" * 60)
    print("SIH26056 AIRFARE PRICE INDEX (APIx) SERVER")
    print(f"Serving Dashboard UI at: http://{host}:{port}")
    print(f"API Documentation at:     http://{host}:{port}/docs")
    print("=" * 60)
    uvicorn.run("backend.app:app", host=host, port=port, reload=True, log_level="info")

if __name__ == "__main__":
    run_server()
