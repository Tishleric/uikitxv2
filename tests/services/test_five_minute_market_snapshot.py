import os
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
import pytz
import pytest


# Module under test
import scripts.run_five_minute_market_snapshot as snapshot_mod


SAMPLE_BATCH_DIR = Path("sampledata")


def _stage_sample_batch(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("bav_analysis_*_chunk_*_of_16.csv"):
        shutil.copy2(p, dst_dir / p.name)


def _write_vtexp_csv(root: Path, entries: dict[str, float]) -> Path:
    vtexp_dir = root / "data" / "input" / "vtexp"
    vtexp_dir.mkdir(parents=True, exist_ok=True)
    # Name with timestamp to be the latest
    vtexp_path = vtexp_dir / "vtexp_20991231_235959.csv"
    with vtexp_path.open("w", encoding="utf-8") as f:
        f.write("symbol,vtexp\n")
        for symbol, days in entries.items():
            f.write(f"{symbol},{days}\n")
    return vtexp_path


def test_trading_day_folder_roll():
    tz = pytz.timezone("America/Chicago")
    before = tz.localize(datetime(2025, 8, 18, 16, 59, 0))
    after = tz.localize(datetime(2025, 8, 18, 17, 1, 0))

    assert snapshot_mod._trading_day_folder(before) == "2025-08-18"
    assert snapshot_mod._trading_day_folder(after) == "2025-08-19"


def test_find_latest_complete_batch(tmp_path: Path):
    input_dir = tmp_path / "input"
    _stage_sample_batch(SAMPLE_BATCH_DIR, input_dir)

    ts, files = snapshot_mod._find_latest_complete_batch(input_dir)  # type: ignore[attr-defined]
    assert ts is not None
    assert len(files) == 16

    # Remove one file and ensure no complete batch
    files[0].unlink()
    assert snapshot_mod._find_latest_complete_batch(input_dir) is None  # type: ignore[attr-defined]


def test_run_once_happy_path(tmp_path: Path):
    # Arrange: stage input and vtexp under a temp root (as CWD)
    root = tmp_path
    input_dir = root / "in"
    out_root = root / "out"
    _stage_sample_batch(SAMPLE_BATCH_DIR, input_dir)

    # Provide a few expiries present in sample with 10 days each
    vtexp_map = {
        "XCME.ZN.N.G.20AUG25": 10.0,
        "XCME.ZN.N.G.19AUG25": 10.0,
        "XCME.ZN.N.G.18AUG25": 10.0,
        "XCME.ZN.N.G.25AUG25": 10.0,
        "XCME.ZN.N.G.26AUG25": 10.0,
        "XCME.ZN.N.G.27AUG25": 10.0,
        "XCME.ZN.N.G.28AUG25": 10.0,
        "XCME.ZN.N.G.29AUG25": 10.0,
        "XCME.ZN.N.G.SEP25": 10.0,
    }
    # Write vtexp under project root default path so parser's relative reads resolve
    vtexp_file = _write_vtexp_csv(snapshot_mod.PROJECT_ROOT, vtexp_map)

    config = {
        "input_dir": str(input_dir),
        "output_root": str(out_root),
        "interval_minutes": 5,
        "timezone": "America/Chicago",
        "enabled_greeks": [
            "delta_F","delta_y","gamma_F","gamma_y","speed_F","theta_F","vega_price","vega_y"
        ],
        "stale_max_minutes": 10,
        "filename_pattern": "five_min_market_%Y%m%d_%H%M.csv",
    }
    service = snapshot_mod.FiveMinuteMarketSnapshotService(config)

    # Act
    try:
        service.run_once(config)
    finally:
        if vtexp_file.exists():
            vtexp_file.unlink(missing_ok=True)

    # Assert: one output file exists under trading-day folder
    # Determine trading day folder from now
    tz = pytz.timezone("America/Chicago")
    now_ct = datetime.now(tz)
    day = snapshot_mod._trading_day_folder(now_ct)
    day_dir = out_root / day
    assert day_dir.exists()
    out_files = list(day_dir.glob("five_min_market_*.csv"))
    assert len(out_files) == 1

    df = pd.read_csv(out_files[0])
    required_cols = [
        "timestamp","underlying_future_price","expiry","vtexp","strike","itype","bid","ask","adjtheor",
        "implied_vol","delta_F","delta_y","gamma_F","gamma_y","speed_F","speed_y","theta_F","vega_price","vega_y","key","calc_error",
    ]
    for c in required_cols:
        assert c in df.columns

    # Underlying ZN adjtheor from sample: 111.578125
    assert (df["underlying_future_price"].notna()).all()
    assert pytest.approx(float(df["underlying_future_price"].iloc[0]), rel=0, abs=1e-9) == 111.578125

    # vtexp in years ~ 10/252 for some rows
    assert (df["vtexp"].dropna() > 0).any()
    # Check at least one value matches ~0.0397 within tolerance
    assert any(abs(v - (10.0/252.0)) < 1e-3 for v in df["vtexp"].dropna().tolist())

    # No futures/NET rows in output
    assert not df['itype'].astype(str).str.upper().isin(['F','FUTURE','NET','N']).any()

    # Timestamp equals batch token time (format YYYY-MM-DD HH:MM:SS) for all rows
    # From sample filename: bav_analysis_20250818_123309_...
    assert (df['timestamp'].astype(str).str.startswith('2025-08-18 12:33:09')).all()


def test_incomplete_batch_none(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    # Copy only 15 of 16 files
    files = sorted(SAMPLE_BATCH_DIR.glob("bav_analysis_*_chunk_*_of_16.csv"))[:15]
    for p in files:
        shutil.copy2(p, input_dir / p.name)

    assert snapshot_mod._find_latest_complete_batch(input_dir) is None  # type: ignore[attr-defined]


def test_stale_fallback_uses_last_batch(tmp_path: Path):
    root = tmp_path
    input_dir = root / "in"
    out_root = root / "out"
    _stage_sample_batch(SAMPLE_BATCH_DIR, input_dir)
    vtexp_file = _write_vtexp_csv(snapshot_mod.PROJECT_ROOT, {"XCME.ZN.N.G.20AUG25": 10.0, "XCME.ZN.N.G.SEP25": 10.0})

    config = {
        "input_dir": str(input_dir),
        "output_root": str(out_root),
        "interval_minutes": 5,
        "timezone": "America/Chicago",
        "enabled_greeks": ["delta_F","delta_y","gamma_F","gamma_y","speed_F","theta_F","vega_price","vega_y"],
        "stale_max_minutes": 10,
        "filename_pattern": "five_min_market_%Y%m%d_%H%M.csv",
    }
    service = snapshot_mod.FiveMinuteMarketSnapshotService(config)

    # First run populates last-complete state
    try:
        service.run_once(config)

    # Remove input to force stale fallback
    shutil.rmtree(input_dir)

    # Second run should still write a snapshot using last complete batch
        service.run_once(config)
    finally:
        if vtexp_file.exists():
            vtexp_file.unlink(missing_ok=True)

    day_dir = out_root / snapshot_mod._trading_day_folder(pytz.timezone("America/Chicago").localize(datetime.now()))
    out_files = list(day_dir.glob("five_min_market_*.csv"))
    assert len(out_files) >= 2

