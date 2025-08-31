"""Actant Spot Risk Archiver Service

Perpetually mirrors and moves files from the production Spot Risk input path
to a Documents-based archive, preserving exact subfolder structure.

Key behaviors:
- First run: move all day-folders older than today via atomic folder rename.
- Always keep today's folder present at source; move only files inside it
  once they are at least `min_age_minutes` old and stable across scans.
- Hourly thereafter: repeat, and if the date rolled, rename yesterday's folder.
- Maintain a simple append-only CSV ledger per day. Logging is to a rotating
  file under %PROGRAMDATA%\ActantArchive\logs.

This script is designed to be robust with millions of files by preferring
folder-level atomic operations and by rate-limiting per-cycle file moves.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import random
import shutil
import sys
import time
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

PROGRAM_DATA_DIR = Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData")) / "ActantArchive"
LOG_DIR = PROGRAM_DATA_DIR / "logs"
LEDGER_DIR = PROGRAM_DATA_DIR / "ledger"
STATE_DIR = PROGRAM_DATA_DIR / "state"
LOCK_FILE = PROGRAM_DATA_DIR / "archive.lock"


def _setup_dirs() -> None:
	for d in (PROGRAM_DATA_DIR, LOG_DIR, LEDGER_DIR, STATE_DIR):
		d.mkdir(parents=True, exist_ok=True)


def _configure_logging() -> None:
	_setup_dirs()
	log_path = LOG_DIR / "archive.log"
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


def _utc_now_str() -> str:
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _today_folder_name() -> str:
	return date.today().strftime("%Y-%m-%d")


def _is_locked(path: Path) -> bool:
	try:
		with path.open("ab"):
			return False
	except OSError:
		return True


def _free_space_ok(dest_root: Path, min_percent: int) -> bool:
	total, used, free = shutil.disk_usage(dest_root)
	return (free / total) * 100 >= min_percent


def _write_ledger_row(action: str, src: Path, dest: Path, size: int, mtime: float, status: str) -> None:
	_setup_dirs()
	day = datetime.now().strftime("%Y-%m-%d")
	ledger_file = LEDGER_DIR / f"ledger_{day}.csv"
	file_exists = ledger_file.exists()
	with ledger_file.open("a", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		if not file_exists:
			writer.writerow(["utc_ts", "action", "src_path", "dest_path", "bytes", "mtime_epoch", "status"])
		writer.writerow([_utc_now_str(), action, str(src), str(dest), size, int(mtime), status])
		f.flush()
		os.fsync(f.fileno())


def _write_folder_summary(action: str, src: Path, dest: Path, count: int, total_bytes: int, status: str) -> None:
	_setup_dirs()
	day = datetime.now().strftime("%Y-%m-%d")
	ledger_file = LEDGER_DIR / f"ledger_{day}.csv"
	file_exists = ledger_file.exists()
	with ledger_file.open("a", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		if not file_exists:
			writer.writerow(["utc_ts", "action", "src_path", "dest_path", "bytes", "mtime_epoch", "status"])
		writer.writerow([_utc_now_str(), action, str(src), str(dest), total_bytes, count, status])
		f.flush()
		os.fsync(f.fileno())


def _single_instance_guard() -> None:
	_setup_dirs()
	if LOCK_FILE.exists():
		raise SystemExit("Another archiver instance appears to be running (lock file exists).")
	LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _release_instance_guard() -> None:
	try:
		LOCK_FILE.unlink(missing_ok=True)
	except Exception:
		pass


def _enumerate_day_folders(root: Path) -> List[Path]:
	return sorted([p for p in root.iterdir() if p.is_dir()])


def _folder_stats(folder: Path) -> Tuple[int, int]:
	count = 0
	total = 0
	for dirpath, _dirnames, filenames in os.walk(folder):
		for name in filenames:
			fp = Path(dirpath) / name
			try:
				stat = fp.stat()
				total += stat.st_size
				count += 1
			except OSError:
				continue
	return count, total


def _safe_rename_folder(src: Path, dest: Path) -> None:
	dest.parent.mkdir(parents=True, exist_ok=True)
	if dest.exists():
		# Rare; avoid collision by timestamp suffix
		dest = dest.with_name(dest.name + f".{datetime.now().strftime('%H%M%S')}.dupe")
	shutil.move(str(src), str(dest))


def _load_state(state_file: Path) -> Dict[str, Tuple[int, float]]:
	if not state_file.exists():
		return {}
	try:
		return yaml.safe_load(state_file.read_text(encoding="utf-8")) or {}
	except Exception:
		return {}


def _save_state(state_file: Path, state: Dict[str, Tuple[int, float]]) -> None:
	state_file.parent.mkdir(parents=True, exist_ok=True)
	with state_file.open("w", encoding="utf-8") as f:
		yaml.safe_dump(state, f)


def run_once(config: dict) -> None:
	src_root = Path(config["source_root"]).resolve()
	dst_root = Path(config["archive_root"]).resolve()
	min_age = int(config.get("min_age_minutes", 60)) * 60
	max_moves = int(config.get("max_moves_per_cycle", 50000))
	exclude_globs = [g.lower() for g in config.get("exclude_globs", [])]
	free_space_min_percent = int(config.get("free_space_min_percent", 10))

	if not _free_space_ok(dst_root, free_space_min_percent):
		logging.warning("Skipping cycle: free space below threshold on %s", dst_root)
		return

	# 1) Move entire day folders older than today
	today = _today_folder_name()
	for day_folder in _enumerate_day_folders(src_root):
		name = day_folder.name
		if name >= today:
			continue
		dst_folder = dst_root / name
		count, total_bytes = _folder_stats(day_folder)
		try:
			_safe_rename_folder(day_folder, dst_folder)
			_write_folder_summary("folder_move", day_folder, dst_folder, count, total_bytes, "ok")
			logging.info("Moved folder %s → %s (files=%d, bytes=%d)", day_folder, dst_folder, count, total_bytes)
		except Exception as e:
			logging.exception("Failed to move folder %s: %s", day_folder, e)
			_write_folder_summary("folder_move", day_folder, dst_folder, count, total_bytes, f"error:{e}")

	# 2) For today's folder, move only stable, cold files
	today_src = src_root / today
	if not today_src.exists():
		return

	state_file = STATE_DIR / f"today_state_{today}.yaml"
	prev_state = _load_state(state_file)
	new_state: Dict[str, Tuple[int, float]] = {}

	moved = 0
	for dirpath, _dirnames, filenames in os.walk(today_src):
		for name in filenames:
			# exclude patterns
			lower = name.lower()
			if any(Path(lower).match(p) for p in exclude_globs):
				continue

			fp = Path(dirpath) / name
			try:
				stat = fp.stat()
			except OSError:
				continue

			age = time.time() - stat.st_mtime
			key = str(fp)
			prev = prev_state.get(key)
			new_state[key] = (stat.st_size, stat.st_mtime)

			if age < min_age:
				continue
			if prev is not None and (prev[0] != stat.st_size or prev[1] != stat.st_mtime):
				# not stable between scans yet
				continue
			if _is_locked(fp):
				continue

			rel = fp.relative_to(src_root)
			dest_path = dst_root / rel
			dest_path.parent.mkdir(parents=True, exist_ok=True)
			try:
				shutil.move(str(fp), str(dest_path))
				_write_ledger_row("file_move", fp, dest_path, stat.st_size, stat.st_mtime, "ok")
				moved += 1
			except Exception as e:
				logging.exception("Failed to move file %s: %s", fp, e)
				_write_ledger_row("file_move", fp, dest_path, stat.st_size, stat.st_mtime, f"error:{e}")

			if moved >= max_moves:
				break
		if moved >= max_moves:
			break

	_save_state(state_file, new_state)
	logging.info("Today sweep moved %d files (max=%d)", moved, max_moves)


def run_forever(config: dict) -> None:
	interval_min = int(config.get("scan_interval_minutes", 60))
	# Random jitter to avoid top-of-hour collisions
	initial_jitter = random.randint(0, 120)
	logging.info("Initial jitter: %ds", initial_jitter)
	time.sleep(initial_jitter)
	
	try:
		_single_instance_guard()
	except SystemExit as e:
		logging.error(str(e))
		return

	try:
		while True:
			run_once(config)
			time.sleep(interval_min * 60)
	except KeyboardInterrupt:
		logging.info("Received interrupt, shutting down archiver...")
	finally:
		_release_instance_guard()


def main() -> None:
	parser = argparse.ArgumentParser(description="Run the Actant Spot Risk Archiver service")
	parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
	args = parser.parse_args()

	_configure_logging()
	config = _load_yaml_config(Path(args.config))
	run_forever(config)


if __name__ == "__main__":
	main()

