from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

import pandas as pd


logger = logging.getLogger(__name__)


def _midpoint(bid, ask):
    try:
        if bid is None or ask is None:
            return None
        return (float(bid) + float(ask)) / 2.0
    except Exception:
        return None


def _best_price(row: pd.Series) -> float | None:
    adj = row.get("adjtheor")
    if pd.notna(adj):
        try:
            return float(adj)
        except Exception:
            pass
    bid, ask = row.get("bid"), row.get("ask")
    return _midpoint(bid, ask)


def compute_underlying_price(df: pd.DataFrame, underlying_base: str = "ZN") -> float | None:
    """Derive underlying futures price for the batch.

    Strategy: pick futures rows (itype == 'F'), then select the first row whose
    key contains the underlying base (e.g., 'ZN'). Prefer adjtheor; fallback to midpoint.
    """
    if df is None or df.empty:
        return None
    cols = {c.lower() for c in df.columns}
    if "itype" not in cols or "key" not in cols:
        return None
    futures = df[df["itype"].astype(str).str.upper() == "F"]
    if futures.empty:
        return None
    # filter by underlying base substring in key, else take first
    if underlying_base:
        mask = futures["key"].astype(str).str.contains(underlying_base, case=False, na=False)
        candidates = futures[mask]
        if candidates.empty:
            candidates = futures
    else:
        candidates = futures
    row = candidates.iloc[0]
    price = _best_price(row)
    if price is None:
        logger.warning("Underlying price not found (no adjtheor/bid-ask) in futures row.")
    return price


def transform_batch(
    df: pd.DataFrame,
    underlying_price: float | None,
    allowed_expiry_tokens: Iterable[str] | None = None,
) -> Tuple[List[str], List[str], List[str], List[List[float]]]:
    """Build arrays for multi-row PI updates.

    Returns:
        scope_keys, field_names (PI), value_types, values (list of [PI5, PI6])
    """
    cols = [c.lower() for c in df.columns]
    missing = [c for c in ("key", "adjtheor", "bid", "ask", "itype") if c not in cols]
    if missing:
        logger.info(f"Input DF missing columns (ok if not all needed): {missing}")

    # Only options rows produce output; futures are used to compute underlying only
    is_future = df.get("itype").astype(str).str.upper().eq("F") if "itype" in cols else pd.Series(False, index=df.index)
    options = df[~is_future].copy()

    # Filter by allowed expiry tokens in key, if provided
    if allowed_expiry_tokens:
        mask_any = False
        combined_mask = pd.Series(False, index=options.index)
        for tok in allowed_expiry_tokens:
            m = options["key"].astype(str).str.contains(tok, case=False, na=False)
            combined_mask = combined_mask | m
            mask_any = True
        if mask_any:
            before = len(options)
            options = options[combined_mask]
            after = len(options)
            if before != after:
                logger.info(f"Expiry allowlist filtered {before - after} option rows; kept {after}.")

    scope_keys: List[str] = []
    values: List[List[float]] = []
    field_names = ["PI5", "PI6"]
    value_types = ["DOUBLE", "DOUBLE"]

    skipped = 0
    for _, row in options.iterrows():
        key = row.get("key")
        if not key or pd.isna(key):
            skipped += 1
            continue
        theo = _best_price(row)
        if theo is None:
            skipped += 1
            continue
        pi6 = underlying_price
        if pi6 is None:
            # If underlying not found this batch, still push PI5; set PI6 to 0.0 (or skip row if required)
            pi6 = 0.0
        scope_keys.append(str(key))
        values.append([float(theo), float(pi6)])

    if skipped:
        logger.info(f"Skipped {skipped} option rows without price or key.")

    return scope_keys, field_names, value_types, values

