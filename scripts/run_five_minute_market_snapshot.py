#!/usr/bin/env python3
"""
Five-Minute Market Snapshot Service

Reads the latest complete 16-chunk Actant Spot Risk batch from the input tree,
parses and computes Greeks for all rows (futures and options), and writes a
timestamped CSV snapshot every 5 minutes into a trading-day subfolder under the
configured output root. Trading day rolls at 5:00 PM America/Chicago.

No modifications to existing watcher pipelines. Runs independently.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytz
import yaml
import pandas as pd

# Project path setup
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.snapshot_protocol import SnapshotServiceProtocol
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.actant.spot_risk.greek_config import GreekConfiguration


PROGRAM_DATA_DIR = Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData")) / "FiveMinuteMarket"
LOG_DIR = PROGRAM_DATA_DIR / "logs"
LOCK_FILE = PROGRAM_DATA_DIR / "snapshot.lock"


def _setup_dirs() -> None:
    for d in (PROGRAM_DATA_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _configure_logging() -> None:
    _setup_dirs()
    log_path = LOG_DIR / "snapshot.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _load_yaml_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ct_now(timezone_name: str) -> datetime:
    tz = pytz.timezone(timezone_name)
    return datetime.now(tz)


def _trading_day_folder(now_ct: datetime) -> str:
    """
    Determine trading day folder name that rolls at 5:00 PM CT.
    If now >= 17:00 local, use next calendar day as trading date.
    """
    five_pm = now_ct.replace(hour=17, minute=0, second=0, microsecond=0)
    trading_date = now_ct.date() if now_ct < five_pm else (now_ct + timedelta(days=1)).date()
    return trading_date.strftime("%Y-%m-%d")


def _find_latest_complete_batch(input_dir: Path) -> Optional[Tuple[str, List[Path]]]:
    """Locate the latest timestamp with exactly 16 chunk files that are present."""
    # Expect pattern bav_analysis_YYYYMMDD_HHMMSS_chunk_N_of_16.csv
    candidates: Dict[str, List[Path]] = {}
    for path in input_dir.rglob("bav_analysis_*_chunk_*_of_16.csv"):
        name = path.name
        # Extract timestamp token 'YYYYMMDD_HHMMSS'
        try:
            ts_token = name.split("bav_analysis_")[1].split("_chunk_")[0]
        except Exception:
            continue
        candidates.setdefault(ts_token, []).append(path)

    if not candidates:
        return None

    # Sort by timestamp token descending
    latest_ts = sorted(candidates.keys(), reverse=True)[0]
    files = candidates[latest_ts]
    if len(files) != 16:
        logging.warning("Latest batch %s has %d files (expected 16)", latest_ts, len(files))
        return None

    # Sort files by chunk index for deterministic processing
    files_sorted = sorted(
        files,
        key=lambda p: int(p.stem.split("_chunk_")[1].split("_of_")[0])
    )
    return latest_ts, files_sorted


def _wait_file_stable(path: Path, checks: int = 3, sleep_s: float = 0.2) -> bool:
    last = -1
    stable = 0
    for _ in range(200):  # ~40s worst-case
        try:
            size = path.stat().st_size
        except OSError:
            time.sleep(sleep_s)
            continue
        if size > 0 and size == last:
            stable += 1
            if stable >= checks:
                return True
        else:
            stable = 0
        last = size
        time.sleep(sleep_s)
    return False


def _ensure_batch_stable(paths: List[Path]) -> bool:
    for p in paths:
        if not _wait_file_stable(p):
            logging.warning("File not stable: %s", p.name)
            return False
    return True


def _build_greek_config(enabled_list: List[str]) -> GreekConfiguration:
    # Build from provided list; fall back to defaults then toggle
    cfg = GreekConfiguration()
    # Disable all first
    for k in list(cfg.enabled_greeks.keys()):
        cfg.enabled_greeks[k] = False
    for name in enabled_list:
        if name in cfg.enabled_greeks:
            cfg.enabled_greeks[name] = True
    # Validate derived/supported
    cfg._validate_configuration()
    return cfg


def _compute_zn_underlying_price(df: pd.DataFrame) -> Optional[float]:
    """Compute the ZN underlying future price from futures rows in the parsed DF."""
    if 'itype' not in df.columns or 'key' not in df.columns:
        return None

    futures = df[df['itype'].astype(str).str.upper().isin(['F', 'FUTURE'])]
    if futures.empty:
        return None

    # Match literal '.ZN.' in key
    zn_mask = futures['key'].astype(str).str.upper().str.contains(r"\.ZN\.", regex=True, na=False)
    target = futures[zn_mask]
    row = target.iloc[0] if not target.empty else futures.iloc[0]

    # Price priority: adjtheor -> midpoint_price -> (bid+ask)/2
    val = None
    if 'adjtheor' in row.index and pd.notna(row['adjtheor']):
        val = row['adjtheor']
    elif 'midpoint_price' in row.index and pd.notna(row['midpoint_price']):
        val = row['midpoint_price']
    else:
        bid = row['bid'] if 'bid' in row.index else None
        ask = row['ask'] if 'ask' in row.index else None
        if pd.notna(bid) and pd.notna(ask):
            try:
                val = (float(bid) + float(ask)) / 2.0
            except Exception:
                val = None

    try:
        return float(val) if val is not None else None
    except Exception:
        return None


class FiveMinuteMarketSnapshotService(SnapshotServiceProtocol):
    def __init__(self, config: Dict[str, object]):
        self.config = config
        tz_name = str(config.get('timezone', 'America/Chicago'))
        self.ct_tz = pytz.timezone(tz_name)
        self.input_dir = Path(str(config['input_dir'])).resolve()
        self.output_root = Path(str(config['output_root'])).resolve()
        self.interval_min = int(config.get('interval_minutes', 5))
        self.stale_max_minutes = int(config.get('stale_max_minutes', 10))

        # Greeks config
        enabled_greeks = list(config.get('enabled_greeks', []))
        self.greek_config = _build_greek_config(enabled_greeks)
        self.calculator = SpotRiskGreekCalculator(greek_config=self.greek_config)

        # Filename pattern
        self.filename_pattern = str(config.get('filename_pattern', 'five_min_market_%Y%m%d_%H%M.csv'))

        # State
        self.last_complete_batch_ts: Optional[str] = None
        self.last_complete_batch_paths: List[Path] = []

    def _select_latest_batch(self) -> Optional[Tuple[str, List[Path]]]:
        latest = _find_latest_complete_batch(self.input_dir)
        if latest is None:
            return None
        ts, paths = latest
        if not _ensure_batch_stable(paths):
            return None
        return ts, paths

    def _load_batch_dataframe(self, paths: List[Path]) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        for p in paths:
            df = parse_spot_risk_csv(p, calculate_time_to_expiry=True, vtexp_data=None)
            frames.append(df)
        full = pd.concat(frames, ignore_index=True)
        # Deduplicate conservatively on full key
        if 'key' in full.columns:
            full = full.drop_duplicates(subset=['key'], keep='first')
        return full

    def _prepare_output_dataframe(self, df_with_greeks: pd.DataFrame, batch_ts_token: str, underlying_price: Optional[float]) -> pd.DataFrame:
        # Keep only options rows in output (strip futures/aggregates)
        df_out = df_with_greeks.copy()
        if 'itype' in df_out.columns:
            itype_u = df_out['itype'].astype(str).str.upper()
            df_out = df_out[itype_u.isin(['C', 'P'])].copy()
        elif 'instrument_type' in df_out.columns:
            inst_u = df_out['instrument_type'].astype(str).str.upper()
            df_out = df_out[inst_u.isin(['CALL', 'PUT'])].copy()
        elif 'Instrument Type' in df_out.columns:
            inst_u2 = df_out['Instrument Type'].astype(str).str.upper()
            df_out = df_out[inst_u2.isin(['CALL', 'PUT'])].copy()

        # Deduplicate by full key again post-filter (safety)
        if 'key' in df_out.columns:
            df_out = df_out.drop_duplicates(subset=['key'], keep='first')

        # Timestamp from batch filename token (already Chicago time)
        try:
            dt = datetime.strptime(batch_ts_token, "%Y%m%d_%H%M%S")
            ts_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_str = ''

        # Build output aligned to the row index so scalar values broadcast to every row
        out = pd.DataFrame(index=df_out.index)
        out['timestamp'] = ts_str
        out['underlying_future_price'] = underlying_price
        out['expiry'] = df_out.get('expiry_date')
        out['vtexp'] = df_out.get('vtexp')  # years as used in calc
        out['strike'] = df_out.get('strike')
        out['itype'] = df_out.get('itype')
        out['bid'] = df_out.get('bid')
        out['ask'] = df_out.get('ask')
        out['adjtheor'] = df_out.get('adjtheor') if 'adjtheor' in df_out.columns else None
        out['implied_vol'] = df_out.get('implied_vol')
        for col in ['delta_F','delta_y','gamma_F','gamma_y','speed_F','speed_y','theta_F','vega_price','vega_y']:
            out[col] = df_out.get(col)
        out['key'] = df_out.get('key')
        # Row-level calc error at end
        # Compose calc_error: prefer greeks error; else mark missing VTEXP; else empty
        base_err = df_out['greek_calc_error'].fillna('') if 'greek_calc_error' in df_out.columns else ''
        if isinstance(base_err, str):
            # Rare path: if base_err isn't a series (shouldn't happen), broadcast
            base_err = pd.Series([''] * len(df_out), index=df_out.index)
        vtexp_series = df_out.get('vtexp')
        no_vtexp_mask = vtexp_series.isna() if vtexp_series is not None else pd.Series([False] * len(df_out), index=df_out.index)
        composed = base_err.copy()
        composed[(base_err.astype(str).str.len() == 0) & no_vtexp_mask] = 'No vtexp mapping'
        out['calc_error'] = composed

        return out

    def _write_snapshot(self, df_out: pd.DataFrame, run_ct: datetime) -> Path:
        trading_day = _trading_day_folder(run_ct)
        day_dir = self.output_root / trading_day
        day_dir.mkdir(parents=True, exist_ok=True)
        filename = run_ct.strftime(self.filename_pattern)
        target = day_dir / filename
        tmp = target.with_suffix('.tmp')

        # Atomic write using pandas to_csv
        # Ensure consistent column order
        columns = [
            'timestamp','underlying_future_price','expiry','vtexp','strike','itype','bid','ask','adjtheor','implied_vol',
            'delta_F','delta_y','gamma_F','gamma_y','speed_F','speed_y','theta_F','vega_price','vega_y','key','calc_error'
        ]
        # Keep only existing columns
        cols_present = [c for c in columns if c in df_out.columns]
        df_out.to_csv(tmp, index=False, columns=cols_present)
        os.replace(tmp, target)
        logging.info("Wrote snapshot: %s (rows=%d)", target, len(df_out))
        return target

    def run_once(self, config: Dict[str, object]) -> None:
        run_ct = _ct_now(str(self.config.get('timezone', 'America/Chicago')))

        selected = self._select_latest_batch()
        if selected is None:
            # Try stale fallback if we have one
            if self.last_complete_batch_paths:
                age_min = self.interval_min
                logging.warning("No complete batch; using last complete (age<=%d min)", self.stale_max_minutes)
                selected = (self.last_complete_batch_ts, self.last_complete_batch_paths)
            else:
                logging.warning("No batch available; skipping this tick")
                return

        ts_token, paths = selected
        df_full = self._load_batch_dataframe(paths)

        # Compute ZN underlying price once, inject into DF as future_price and drop futures
        zn_price = _compute_zn_underlying_price(df_full)
        if zn_price is None:
            logging.warning("ZN future price not found; underlying_future_price will be empty")

        # Set column used by calculator as an override
        df_full['future_price'] = zn_price
        # Remove futures rows so calculator uses provided future_price column
        df_for_calc = df_full[~df_full['itype'].astype(str).str.upper().isin(['F', 'FUTURE'])].copy() if 'itype' in df_full.columns else df_full.copy()

        df_with_greeks, _ = self.calculator.calculate_greeks(df_for_calc, future_price_col='future_price')

        # Console summary for rows with errors
        if 'greek_calc_error' in df_with_greeks.columns:
            err = df_with_greeks['greek_calc_error'].fillna('')
            mask = err.astype(str).str.len() > 0
            cnt = int(mask.sum())
            if cnt > 0:
                logging.warning("Greek calc errors in batch %s: %d rows", ts_token, cnt)
                # Top 3 unique messages
                top = (
                    err[mask]
                    .value_counts()
                    .head(3)
                )
                for msg, c in top.items():
                    logging.warning("  [%dx] %s", c, msg)

        df_out = self._prepare_output_dataframe(df_with_greeks, ts_token, zn_price)
        self._write_snapshot(df_out, run_ct)

        # Update last-complete state
        self.last_complete_batch_ts = ts_token
        self.last_complete_batch_paths = paths

    def run_forever(self, config: Dict[str, object]) -> None:
        # Jitter a bit to avoid exact alignment
        time.sleep(1.0)
        try:
            while True:
                start = time.time()
                try:
                    self.run_once(self.config)
                except Exception as e:
                    logging.exception("Snapshot cycle failed: %s", e)
                elapsed = time.time() - start
                sleep_s = max(0.0, self.interval_min * 60 - elapsed)
                time.sleep(sleep_s)
        except KeyboardInterrupt:
            logging.info("Received interrupt; exiting")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Five-Minute Market Snapshot service")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "five_minute_market.yaml"), help="Path to YAML config file")
    args = parser.parse_args()

    _configure_logging()
    config = _load_yaml_config(Path(args.config))

    # Single instance guard
    _setup_dirs()
    if LOCK_FILE.exists():
        logging.error("Another snapshot instance appears to be running (lock file exists)")
        return
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")

    try:
        service = FiveMinuteMarketSnapshotService(config)
        service.run_forever(config)
    finally:
        try:
            LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()

