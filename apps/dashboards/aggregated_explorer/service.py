from __future__ import annotations

import os
import sys
from typing import List

import pandas as pd

# Ensure project root on sys.path for 'core' import when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.aggregated_data_protocol import AggregatedDataService


AGGREGATED_CSV_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    'lib', 'trading', 'bond_future_options', 'generatedcsvs', 'aggregated'
)


class AggregatedCSVService(AggregatedDataService):
    """Filesystem-backed service for aggregated CSV browsing.

    Args:
        base_dir: Optional override directory containing aggregated CSV files.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = base_dir or AGGREGATED_CSV_DIR

    def _list_csv_files(self) -> List[str]:
        """List CSV filenames in the base directory, sorted lexicographically."""
        if not os.path.isdir(self.base_dir):
            return []
        return sorted([f for f in os.listdir(self.base_dir) if f.lower().endswith('.csv')])

    def list_available_days(self) -> List[str]:
        """Return ordered day codes present on disk, including OZN_SEP25 for Friday.

        The preferred order is Monday–Thursday codes followed by the Friday exception.
        """
        files = self._list_csv_files()
        days: set[str] = set()
        for fname in files:
            # Expect forms: aggregated_18AUG25_C.csv, aggregated_19AUG25_P.csv, aggregated_OZN_SEP25_C.csv
            parts = fname.replace('.csv', '').split('_')
            if len(parts) < 3:
                continue
            # parts[1] could be 18AUG25 or OZN, handle OZN_SEP25
            if parts[1] == 'OZN' and len(parts) >= 4 and parts[2] == 'SEP25':
                day_code = 'OZN_SEP25'
            else:
                day_code = parts[1]
            days.add(day_code)
        # Prefer Mon-Thu first then Friday special if present
        ordering = ['18AUG25', '19AUG25', '20AUG25', '21AUG25', 'OZN_SEP25']
        return [d for d in ordering if d in days] or sorted(days)

    def list_available_sides(self, day_code: str) -> List[str]:
        """Return available option sides for a given day code, subset of ["C", "P"]."""
        sides: set[str] = set()
        for s in ('C', 'P'):
            try:
                _ = self.get_csv_path(day_code, s)
                sides.add(s)
            except FileNotFoundError:
                pass
        return sorted(sides)

    def get_csv_path(self, day_code: str, side: str) -> str:
        """Resolve the absolute CSV path for a given day code and side.

        Raises:
            FileNotFoundError: If the expected CSV file is not found.
        """
        if day_code == 'OZN_SEP25':
            fname = f'aggregated_OZN_SEP25_{side}.csv'
        else:
            fname = f'aggregated_{day_code}_{side}.csv'
        path = os.path.join(self.base_dir, fname)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        return path

    def list_unique_timestamps(self, csv_path: str) -> List[str]:
        """Return sorted, deduplicated timestamps formatted as '%Y-%m-%d %H:%M:%S'."""
        df = pd.read_csv(csv_path)
        if 'timestamp' not in df.columns:
            return []
        # Parse to datetime to ensure proper ordering
        ts = pd.to_datetime(df['timestamp'], errors='coerce')
        ts = ts.dropna().drop_duplicates().sort_values()
        return [t.strftime('%Y-%m-%d %H:%M:%S') for t in ts]

    def get_rows_for_timestamp(self, csv_path: str, timestamp: str) -> pd.DataFrame:
        """Return a DataFrame of rows matching an exact timestamp string."""
        df = pd.read_csv(csv_path)
        if 'timestamp' not in df.columns:
            return pd.DataFrame()
        return df[df['timestamp'] == timestamp]


