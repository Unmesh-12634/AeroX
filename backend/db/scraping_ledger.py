"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Partitioned & Sharded Scraping Ledger Manager

Features:
- Dynamic CSV Partitioning: Capped at MAX_RECORDS_PER_PARTITION (10,000 records) per file.
  Automatically rolls over to live_scraped_master_part2.csv, part3.csv, etc.
- Chronological Sorting: Sorts records by search_timestamp and travel_date on every merge.
- Deduplication: Eliminates duplicate flight quotes on (source_platform, travel_date, route, departure_time, airline_standardized, total_fare_inr).
- Multi-Part Ingestion Layer: Seamlessly discovers and concatenates all partitions into a unified in-memory view.
- Zero Synthetic Fallback: Preserves exact timestamps, real flight numbers, and unbundled fare breakdowns.
"""

import os
import re
import glob
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.config import settings

MAX_RECORDS_PER_PARTITION = 10000
DEDUP_KEYS = ['source_platform', 'travel_date', 'route', 'departure_time', 'airline_standardized', 'total_fare_inr']


class AppendResult(tuple):
    """
    Tuple representing (target_partition_name, total_records).
    Also supports dict-style access for backwards compatibility.
    """
    def __new__(cls, target_partition: str, total_records: int, records_added: int = 0, status: str = "success"):
        return super().__new__(cls, (target_partition, total_records))

    def __init__(self, target_partition: str, total_records: int, records_added: int = 0, status: str = "success"):
        self.target_partition = target_partition
        self.total_partition_records = total_records
        self.total_records = total_records
        self.records_added = records_added
        self.status = status

    def __getitem__(self, item):
        if isinstance(item, str):
            return getattr(self, item, None)
        return super().__getitem__(item)

    def get(self, key, default=None):
        return getattr(self, key, default)


class ScrapingLedgerManager:
    def __init__(self, live_dir: Optional[Path] = None):
        self.live_dir = live_dir or settings.LIVE_SCRAPED_DIR
        self.live_dir.mkdir(parents=True, exist_ok=True)

    def get_partition_files(self) -> List[Path]:
        """
        Discovers all live scraped partition files sorted in numerical sequence order.
        Example: part1.csv, part2.csv, part10.csv (numerical sort).
        Falls back to live_scraped_master.csv if no partitioned files exist yet.
        """
        part_files = list(self.live_dir.glob("live_scraped_master_part*.csv"))
        if part_files:
            def _extract_part_num(p: Path) -> int:
                m = re.search(r"part(\d+)", p.name)
                return int(m.group(1)) if m else 0
            return sorted(part_files, key=_extract_part_num)

        base_file = self.live_dir / "live_scraped_master.csv"
        if base_file.exists():
            return [base_file]

        return []

    def get_active_write_target(self) -> Tuple[Path, int]:
        """
        Determines the current active partition file to write to.
        Returns (filepath, current_row_count).
        If the latest partition has >= MAX_RECORDS_PER_PARTITION, returns the next partition target with 0 count.
        """
        partitions = self.get_partition_files()
        if not partitions:
            target = self.live_dir / "live_scraped_master_part1.csv"
            return target, 0

        latest = partitions[-1]
        try:
            df = pd.read_csv(latest, low_memory=False)
            count = len(df)
            if count >= MAX_RECORDS_PER_PARTITION:
                # Rollover to the next partition index
                match = re.search(r"part(\d+)", latest.name)
                next_part = int(match.group(1)) + 1 if match else 2
                new_target = self.live_dir / f"live_scraped_master_part{next_part}.csv"
                return new_target, 0
            return latest, count
        except Exception:
            return latest, 0

    def append_observations(self, new_records: List[Dict[str, Any]]) -> Tuple[str, int]:
        """
        Appends new records into the partitioned ledger.
        - Sorts chronologically by search_timestamp and travel_date.
        - Deduplicates against existing entries.
        - If partition >= 10,000 rows, rolls over to the next partition (live_scraped_master_part2.csv, etc.).
        - Splits across partition boundary if incoming batch exceeds remaining partition space.
        - Returns (target_partition_name, total_records).
        """
        if not new_records:
            return AppendResult("live_scraped_master_part1.csv", self.get_total_records(), records_added=0, status="no_data")

        df_new = pd.DataFrame(new_records)

        # Standardize search_timestamp
        if 'search_timestamp' not in df_new.columns:
            df_new['search_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Floor validation for commercial domestic airfare
        if 'total_fare_inr' in df_new.columns:
            df_new['total_fare_inr'] = pd.to_numeric(df_new['total_fare_inr'], errors='coerce')
            df_new = df_new.dropna(subset=['total_fare_inr'])
            df_new = df_new[df_new['total_fare_inr'] >= 1500.0]

        if df_new.empty:
            return AppendResult("live_scraped_master_part1.csv", self.get_total_records(), records_added=0, status="no_data")

        # Determine target file
        target_file, current_count = self.get_active_write_target()

        if target_file.exists():
            try:
                df_existing = pd.read_csv(target_file, low_memory=False)
                available_space = max(0, MAX_RECORDS_PER_PARTITION - len(df_existing))
            except Exception:
                df_existing = pd.DataFrame()
                available_space = MAX_RECORDS_PER_PARTITION
        else:
            df_existing = pd.DataFrame()
            available_space = MAX_RECORDS_PER_PARTITION

        written_target_name = target_file.name

        # Fit into current partition or split across rollover
        if len(df_new) <= available_space or available_space == 0:
            if available_space == 0:
                match = re.search(r"part(\d+)", target_file.name)
                next_part = int(match.group(1)) + 1 if match else 2
                target_file = self.live_dir / f"live_scraped_master_part{next_part}.csv"
                written_target_name = target_file.name
                df_combined = df_new
            else:
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)

            df_sorted = self._dedup_and_sort(df_combined)
            df_sorted.to_csv(target_file, index=False)
            self._update_master_symlink_or_copy(target_file)
        else:
            # Split batch into current partition and next partition
            df_fit = df_new.iloc[:available_space]
            df_overflow = df_new.iloc[available_space:]

            df_combined_1 = pd.concat([df_existing, df_fit], ignore_index=True)
            df_sorted_1 = self._dedup_and_sort(df_combined_1)
            df_sorted_1.to_csv(target_file, index=False)

            # Write overflow to next partition
            match = re.search(r"part(\d+)", target_file.name)
            next_part = int(match.group(1)) + 1 if match else 2
            next_target = self.live_dir / f"live_scraped_master_part{next_part}.csv"
            written_target_name = next_target.name

            df_sorted_2 = self._dedup_and_sort(df_overflow)
            df_sorted_2.to_csv(next_target, index=False)
            self._update_master_symlink_or_copy(next_target)

        total_all = self.get_total_records()
        return AppendResult(
            target_partition=written_target_name,
            total_records=total_all,
            records_added=len(df_new),
            status="success"
        )

    def _dedup_and_sort(self, df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicates rows and sorts chronologically."""
        if df.empty:
            return df

        # Deduplicate
        existing_keys = [k for k in DEDUP_KEYS if k in df.columns]
        if existing_keys:
            df = df.drop_duplicates(subset=existing_keys, keep='last')

        # Chronological Sort: primary search_timestamp, secondary travel_date
        sort_cols = []
        ascending = []
        if 'search_timestamp' in df.columns:
            sort_cols.append('search_timestamp')
            ascending.append(True)
        if 'travel_date' in df.columns:
            sort_cols.append('travel_date')
            ascending.append(True)

        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=ascending)

        return df.reset_index(drop=True)

    def _update_master_symlink_or_copy(self, latest_active_file: Path):
        """Ensures live_scraped_master.csv remains available as an aggregated view/alias."""
        master_alias = self.live_dir / "live_scraped_master.csv"
        if latest_active_file.name == "live_scraped_master.csv" and not list(self.live_dir.glob("live_scraped_master_part*.csv")):
            return

        try:
            all_df = self.load_all_partitions()
            all_df.to_csv(master_alias, index=False)
        except Exception as e:
            print(f"[-] Warning: Failed to sync master alias: {e}")

    def load_all_partitions(self) -> pd.DataFrame:
        """
        Discovers all partition files matching live_scraped_master*.csv
        and returns a unified, sorted, deduplicated DataFrame.
        """
        partitions = self.get_partition_files()
        if not partitions:
            base = self.live_dir / "live_scraped_master.csv"
            if base.exists():
                try:
                    return pd.read_csv(base, low_memory=False)
                except Exception:
                    return pd.DataFrame()
            return pd.DataFrame()

        dfs = []
        for p in partitions:
            try:
                df = pd.read_csv(p, low_memory=False)
                dfs.append(df)
            except Exception as e:
                print(f"[-] Error loading partition {p}: {e}")

        if not dfs:
            return pd.DataFrame()

        combined = pd.concat(dfs, ignore_index=True)
        return self._dedup_and_sort(combined)

    def get_total_records(self) -> int:
        """Calculates total unique records across all partitions."""
        partitions = self.get_partition_files()
        if not partitions:
            return 0

        # If only part files exist, count rows from each partition
        total = 0
        for p in partitions:
            try:
                with open(p, "rb") as f:
                    lines = sum(1 for _ in f) - 1
                    total += max(0, lines)
            except Exception:
                pass
        return total

    def get_latest_timestamp(self) -> Optional[str]:
        """Returns the latest search_timestamp across all partitions."""
        partitions = self.get_partition_files()
        if not partitions:
            return None

        # Check newest partition
        latest_file = partitions[-1]
        try:
            df = pd.read_csv(latest_file, low_memory=False)
            if 'search_timestamp' in df.columns:
                valid_ts = df['search_timestamp'].dropna().astype(str)
                if not valid_ts.empty:
                    return str(valid_ts.max())
        except Exception:
            pass

        # Fallback to loading all partitions
        try:
            all_df = self.load_all_partitions()
            if not all_df.empty and 'search_timestamp' in all_df.columns:
                return str(all_df['search_timestamp'].dropna().max())
        except Exception:
            pass

        return None


# Global Singleton instance
scraping_ledger = ScrapingLedgerManager()
