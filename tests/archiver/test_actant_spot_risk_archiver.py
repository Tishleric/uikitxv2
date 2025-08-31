import os
import sys
import time
import shutil
import importlib
from pathlib import Path

import pytest


def _import_archiver_with_programdata(tmp_path: Path):
    pd = tmp_path / "programdata"
    pd.mkdir(parents=True, exist_ok=True)
    os.environ["PROGRAMDATA"] = str(pd)
    # ensure fresh import
    sys.modules.pop("scripts.run_actant_spot_risk_archiver", None)
    mod = importlib.import_module("scripts.run_actant_spot_risk_archiver")
    importlib.reload(mod)
    return mod


def _config(src: Path, dst: Path, **overrides):
    cfg = {
        "source_root": str(src),
        "archive_root": str(dst),
        "scan_interval_minutes": 60,
        "min_age_minutes": 60,
        "max_moves_per_cycle": 50000,
        "exclude_globs": ["*.tmp", "*.partial", "~$*"],
        "free_space_min_percent": 1,
    }
    cfg.update(overrides)
    return cfg


def _today_name() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def test_today_preserved_and_cold_stable_files_move(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    # one old file (eligible after stability), one fresh file
    old_f = _touch(src / today / "old.csv", age_seconds=7200)
    fresh_f = _touch(src / today / "fresh.csv", age_seconds=10)
    cfg = _config(src, dst, min_age_minutes=60)
    # first run records state
    mod.run_once(cfg)
    # second run should move only the old one
    mod.run_once(cfg)
    assert (src / today).exists()
    assert not (src / today / "old.csv").exists()
    assert (dst / today / "old.csv").exists()
    assert (src / today / "fresh.csv").exists()


def _touch(path: Path, age_seconds: int = 0, content: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    ts = time.time() - age_seconds
    os.utime(path, (ts, ts))
    return path


def test_destination_collision_suffix(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    y2 = time.strftime("%Y-%m-%d", time.localtime(time.time()-2*86400))
    # pre-create conflicting dest folder
    (dst / y2).mkdir(parents=True, exist_ok=True)
    _touch(src / y2 / "a.csv", age_seconds=7200)
    mod.run_once(_config(src, dst))
    # original folder should no longer be at source
    assert not (src / y2).exists()
    # destination has either dupe folder or the direct one (if not exact collision)
    dupe_exists = any(p.name.startswith(y2) for p in dst.iterdir())
    assert dupe_exists


def test_move_past_day_folders(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = time.strftime("%Y-%m-%d")
    # create folders: today-2, today-1, today
    days = [
        (tmp := time.localtime(time.time()-2*86400), time.strftime("%Y-%m-%d", tmp)),
        (tmp := time.localtime(time.time()-1*86400), time.strftime("%Y-%m-%d", tmp)),
        (time.localtime(), today),
    ]
    for _, name in days:
        _touch(src / name / "a.csv", age_seconds=7200)
    mod.run_once(_config(src, dst))
    # older folders moved entirely; today remains
    assert not (src / days[0][1]).exists()
    assert not (src / days[1][1]).exists()
    assert (src / today).exists()
    assert (dst / days[0][1]).exists()
    assert (dst / days[1][1]).exists()


def test_exclude_patterns(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    _touch(src / today / "keep.tmp", age_seconds=7200)
    _touch(src / today / "keep.partial", age_seconds=7200)
    _touch(src / today / "keep.csv", age_seconds=7200)
    cfg = _config(src, dst, min_age_minutes=60)
    mod.run_once(cfg)
    mod.run_once(cfg)
    # tmp and partial remain, csv moved
    assert (src / today / "keep.tmp").exists()
    assert (src / today / "keep.partial").exists()
    assert not (src / today / "keep.csv").exists()
    assert (dst / today / "keep.csv").exists()


def test_rate_limit_respected(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    # create 5 eligible files
    for i in range(5):
        _touch(src / today / f"f{i}.csv", age_seconds=7200)
    cfg = _config(src, dst, min_age_minutes=60, max_moves_per_cycle=2)
    mod.run_once(cfg)
    mod.run_once(cfg)
    # After two cycles with limit=2, 4 moved, 1 remains
    moved = sum(1 for p in (dst / today).glob("*.csv"))
    remaining = sum(1 for p in (src / today).glob("*.csv"))
    assert moved == 4 and remaining == 1


def test_stability_check_across_scans(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    f = _touch(src / today / "unstable.csv", age_seconds=7200, content=b"one")
    cfg = _config(src, dst, min_age_minutes=60)
    # first scan records state
    mod.run_once(cfg)
    # change file -> not stable
    f.write_bytes(b"two")
    os.utime(f, (time.time() - 7200, time.time() - 7200))
    mod.run_once(cfg)
    # third scan (no change) -> move
    mod.run_once(cfg)
    assert not (src / today / "unstable.csv").exists()
    assert (dst / today / "unstable.csv").exists()


def test_free_space_guard(tmp_path: Path, monkeypatch):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    _touch(src / today / "old.csv", age_seconds=7200)
    cfg = _config(src, dst, min_age_minutes=60, free_space_min_percent=101)
    mod.run_once(cfg)
    # nothing moved due to guard
    assert (src / today / "old.csv").exists()
    assert not (dst / today).exists()


def test_idempotent_rerun(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    # yesterday folder
    y = time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))
    _touch(src / y / "a.csv", age_seconds=7200)
    mod.run_once(_config(src, dst))
    # run again -> nothing to move, but no errors
    mod.run_once(_config(src, dst))
    assert not (src / y).exists()
    assert (dst / y / "a.csv").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only locked file behavior")
def test_locked_file_skipped_then_moved(tmp_path: Path):
    mod = _import_archiver_with_programdata(tmp_path)
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    today = _today_name()
    f = _touch(src / today / "locked.csv", age_seconds=7200)
    # hold open handle to simulate lock
    handle = open(f, "rb")
    try:
        mod.run_once(_config(src, dst, min_age_minutes=60))
        # still present in source due to lock
        assert (src / today / "locked.csv").exists()
    finally:
        handle.close()
    # next run should move it
    mod.run_once(_config(src, dst, min_age_minutes=60))
    assert not (src / today / "locked.csv").exists()
    assert (dst / today / "locked.csv").exists()
