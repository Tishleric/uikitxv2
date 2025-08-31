"""Aggregated data service protocol for dashboards.

Defines the interface required to browse day/side CSVs, list unique timestamps,
and fetch row subsets by exact timestamp. Concrete implementations must adhere
to this contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class AggregatedDataService(ABC):
    """Abstract base class for aggregated CSV data access.

    Preconditions:
        - Implementations must ensure paths provided exist when returned.
        - Timestamps returned by list_unique_timestamps are ISO-like strings.

    Postconditions:
        - Methods never return None; empty lists/dataframes are acceptable.
    """

    @abstractmethod
    def list_available_days(self) -> List[str]:
        """Return available day codes (e.g., "18AUG25", "19AUG25", "20AUG25", "21AUG25", "OZN_SEP25")."""

    @abstractmethod
    def list_available_sides(self, day_code: str) -> List[str]:
        """Return sides available for a given day code, subset of ["C", "P"]."""

    @abstractmethod
    def get_csv_path(self, day_code: str, side: str) -> str:
        """Return absolute path to the target CSV for day_code and side ("C"/"P")."""

    @abstractmethod
    def list_unique_timestamps(self, csv_path: str) -> List[str]:
        """Return sorted, de-duplicated timestamp strings from the target CSV."""

    @abstractmethod
    def get_rows_for_timestamp(self, csv_path: str, timestamp: str) -> pd.DataFrame:
        """Return rows from the CSV where column "timestamp" matches the provided value exactly."""


