"""
SIH26056: Real-Time Airfare Price Index for India
Main Calculation CLI Entrypoint
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from scripts.index_engine.calculator import AirfareIndexEngine

if __name__ == "__main__":
    engine = AirfareIndexEngine()
    engine.run_full_pipeline()
