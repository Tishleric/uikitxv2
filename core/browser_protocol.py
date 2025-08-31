"""Browser automation protocol.

Defines a minimal interface for one-shot browser-driven collectors. New
automations (e.g., Pricing Monkey runners) should implement this Protocol to
ensure consistent invocation and testing.
"""

from __future__ import annotations

from typing import Protocol
import pandas as pd


class BrowserCollector(Protocol):

	def collect_once(self) -> pd.DataFrame:
		"""Run a single collection cycle and return a DataFrame."""
		...


