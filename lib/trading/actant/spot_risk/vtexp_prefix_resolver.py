"""Isolated helper to resolve VTEXP time-format symbols from Actant keys.

This module is intentionally siloed to enable safe testing before integrating
into the shared VTEXP mapper. It focuses on translating only the product/month
prefix (independent of strike and call/put) to the Actant time-format symbol.

Examples:
    XCME.OZN.SEP25.11.C  -> prefix: XCME.OZN.SEP25  -> XCME.ZN.N.G.22AUG25
    XCME.WY3.20AUG25.111.C -> prefix: XCME.WY3.20AUG25 -> XCME.ZN.N.G.20AUG25
"""

from __future__ import annotations

from typing import Optional, Protocol


class RosettaProtocol(Protocol):
    """Minimal protocol for the Rosetta translator used here."""

    def translate(self, symbol: str, src: str, dst: str) -> str:  # pragma: no cover - type signature only
        ...


def extract_spot_prefix(actant_key: str) -> Optional[str]:
    """Extract the Actant product/month prefix from a spot key.

    Returns None for malformed/future-like rows where a 3-part prefix is absent.

    Args:
        actant_key: Full Actant key (e.g., "XCME.OZN.SEP25.11.C")

    Returns:
        Prefix string (e.g., "XCME.OZN.SEP25") or None if not parseable.
    """
    if not actant_key or not isinstance(actant_key, str):
        return None

    parts = actant_key.split('.')
    # Expect at least exchange, product/series, expiry
    if len(parts) < 3:
        return None

    # Futures may have only 3 parts and ITYPE F; caller should guard if needed
    prefix = '.'.join(parts[:3])
    return prefix


def resolve_time_symbol_from_prefix(spot_prefix: str, rosetta: RosettaProtocol) -> Optional[str]:
    """Resolve the Actant time-format symbol from a spot prefix via Rosetta.

    Args:
        spot_prefix: e.g., "XCME.OZN.SEP25"
        rosetta: Translator that understands actantrisk->actantrisk_time

    Returns:
        Time-format symbol (e.g., "XCME.ZN.N.G.22AUG25") or None if unavailable.
    """
    if not spot_prefix:
        return None
    try:
        # Rosetta expects 'actanttime' for the VTEXP (time-format) domain
        return rosetta.translate(spot_prefix, 'actantrisk', 'actanttime')
    except Exception:
        return None


def resolve_time_symbol_from_key(actant_key: str, rosetta: RosettaProtocol) -> Optional[str]:
    """Resolve the Actant time-format symbol from the full spot key.

    This trims strike and C/P, translating only the product/month prefix.

    Args:
        actant_key: Full Actant key (e.g., "XCME.OZN.SEP25.11.C")
        rosetta: Translator implementing RosettaProtocol

    Returns:
        Time-format symbol or None.
    """
    prefix = extract_spot_prefix(actant_key)
    if prefix is None:
        return None
    return resolve_time_symbol_from_prefix(prefix, rosetta)

