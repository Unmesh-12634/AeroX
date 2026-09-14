"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Unit & Integration Tests: Partitioned Scraping Ledger & Pipeline Architecture
"""

import os
import shutil
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from starlette.testclient import TestClient

from backend.app import app
from backend.db.scraping_ledger import ScrapingLedgerManager, MAX_RECORDS_PER_PARTITION
from backend.db.database import db

client = TestClient(app)

class TestPartitionedPipeline:

    def test_partitioning_and_rollover_logic(self):
        """Test that ScrapingLedgerManager splits and rolls over at threshold."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            mgr = ScrapingLedgerManager(live_dir=tmp_path)

            # Generate 12,000 distinct synthetic test observations
            base_time = datetime(2026, 9, 13, 10, 0, 0)
            sample_records = []
            for i in range(12000):
                sample_records.append({
                    "record_id": f"test_{i}",
                    "source_platform": "google_flights",
                    "travel_date": (base_time + timedelta(days=i % 30)).strftime("%Y-%m-%d"),
                    "route": "DEL-BOM" if i % 2 == 0 else "BOM-BLR",
                    "departure_time": f"{(i % 24):02d}:00",
                    "airline_standardized": "IndiGo" if i % 2 == 0 else "Air India",
                    "total_fare_inr": 3500.0 + i,  # Unique fare ensures no duplicate collision
                    "search_timestamp": (base_time + timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S")
                })

            # Append the 12,000 records
            target_part, total_recs = mgr.append_observations(sample_records)

            # Verification of partition files
            part_files = mgr.get_partition_files()
            assert len(part_files) == 2, f"Expected 2 partitions, found {len(part_files)}"
            assert part_files[0].name == "live_scraped_master_part1.csv"
            assert part_files[1].name == "live_scraped_master_part2.csv"

            # Check counts
            df_part1 = pd.read_csv(part_files[0])
            df_part2 = pd.read_csv(part_files[1])
            assert len(df_part1) == MAX_RECORDS_PER_PARTITION, f"Part 1 should have exactly {MAX_RECORDS_PER_PARTITION}, got {len(df_part1)}"
            assert len(df_part2) == 2000, f"Part 2 should have 2000 records, got {len(df_part2)}"

            # Verification of unified loading
            all_df = mgr.load_all_partitions()
            assert len(all_df) == 12000
            assert mgr.get_total_records() == 12000
            assert mgr.get_latest_timestamp() is not None

    def test_scraper_status_endpoint_returns_partition_metadata(self):
        """Test GET /api/v1/scrape/status returns active partition metrics and recent status."""
        response = client.get("/api/v1/scrape/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "partition_files" in data
        assert len(data["partition_files"]) >= 1
        assert "live_scraped_master_part1.csv" in data["partition_files"]
        assert data["max_records_per_partition"] == 10000
        assert data["total_scraped_records"] >= 8000
        assert "2026" in data["latest_scraped_date"]

    def test_daily_index_coverage_through_september_and_forward(self):
        """Test GET /api/v1/daily-index reflects coverage across simulation and forward booking dates."""
        response = client.get("/api/v1/daily-index")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        points = data["data"]
        assert len(points) > 0
        dates = [p["travel_date"] for p in points]
        # Verify coverage through 2026-09-13 or forward
        assert any(d >= "2026-09-13" for d in dates)
        assert any(d >= "2026-10-01" for d in dates)

    def test_database_repository_reload_and_property(self):
        """Test DataRepository in-memory reload and df property."""
        assert db.df is not None
        assert len(db.df) > 0
        initial_count = len(db.master_df)
        db.reload_data()
        assert len(db.master_df) == initial_count
        assert db.reload() is None

    def test_scrape_trigger_endpoint_availability(self):
        """Test /api/v1/scrape/trigger endpoint response handling with mock."""
        from unittest.mock import patch
        with patch("backend.routers.scraper._run_google_flights_scrape", return_value=[]):
            response = client.get("/api/v1/scrape/trigger?routes=DEL-BOM")
            # May return 200 (queued) or 429 (quota reached if already triggered in testing)
            assert response.status_code in [200, 429]
            data = response.json()
            if response.status_code == 200:
                assert data["status"] in ["queued", "completed"]
            else:
                assert "Scraping quota has been reached" in data.get("detail", {}).get("message", "")

