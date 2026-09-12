"""
SIH26056: Real-Time Airfare Price Index for India
Automated Scraping Scheduler CLI Entrypoint
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from scripts.scheduler.cron_daemon import main

if __name__ == "__main__":
    main()
