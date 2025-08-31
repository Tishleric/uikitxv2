"""
Key generation protocol for producing ActantRisk option keys.

Contracts:
- Implementations must be pure (no global side effects) and return deterministic sets.
- Implementations should validate inputs and fail fast on invalid ranges.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol, Set


@dataclass(frozen=True)
class KeyGenerationSpec:
    """Specification for ActantRisk key generation.

    Attributes:
        start_date: Inclusive start date (calendar date in CT).
        end_date: Inclusive end date (calendar date in CT).
        min_strike: Minimum strike (e.g., 110.0).
        max_strike: Maximum strike (e.g., 114.75).
        step: Strike step size in points (e.g., 0.25 for quarter steps).
        include_puts: Whether to include put keys.
        include_calls: Whether to include call keys.
    """

    start_date: date
    end_date: date
    min_strike: float
    max_strike: float
    step: float
    include_puts: bool = True
    include_calls: bool = True


class KeyGenerationProtocol(Protocol):
    """Abstract contract for key generation implementations."""

    def generate_keys(self, spec: KeyGenerationSpec) -> Set[str]:
        """Generate a set of ActantRisk keys according to spec.

        Returns:
            A deduplicated set of full ActantRisk keys (e.g.,
            "XCME.WY3.20AUG25.112:25.C").
        """
        ...




