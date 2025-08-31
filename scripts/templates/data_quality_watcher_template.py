#!/usr/bin/env python3
"""
Data Quality Watcher Template
-----------------------------

Purpose:
- Minimal, copyable skeleton that mirrors our existing watcher mechanics
  (watchdog Observer + FileSystemEventHandler, start/stop lifecycle,
  graceful signal handling, Windows-safe keepalive loop).

How to use:
- Copy this file, set DEFAULT_WATCH_DIR and DEFAULT_PATTERN for your dataset
  (e.g., actant_spot_risk, trade_ledger, vtexp).
- Implement the TODOs in the three check stubs (correctness, frequency,
  completeness). Keep them small and focused.

Run:
- python your_new_watcher.py --watch-dir <path> --pattern <glob> --recursive --debug

Notes:
- This template intentionally avoids our monitoring decorator to stay standalone.
- Findings should be logged; integrate with other systems later if needed.
"""

import argparse
import logging
import signal
import sys
import time
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable, Dict, List

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


# --- Defaults (teammate updates per instance) ---
DEFAULT_WATCH_DIR = "data/input/actant_spot_risk"
DEFAULT_PATTERN = "*.csv"
DEFAULT_RECURSIVE = True
TICK_INTERVAL_SEC = 30


# Light aliases so the template reads easily
Finding = Dict[str, str]  # keys: severity, code, message, path, extra_*
DataQualityCheck = Callable[[Path, Dict], List[Finding]]


class DQFileHandler(FileSystemEventHandler):
    """File event handler: reacts to new files, runs your checks, logs findings."""
    def __init__(self, checks: List[DataQualityCheck], state: Dict, pattern: str):
        """Keep the checks and shared state, and remember the filename pattern to match."""
        self.checks = checks
        self.state = state
        self.pattern = pattern

    def on_created(self, event):
        """When a new file shows up: filter by pattern, record the arrival, run checks."""
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not self._matches_pattern(path.name):
            return

        now = time.time()
        # Track arrivals so frequency/completeness checks have something to look at later
        self.state.setdefault("arrivals", []).append(now)

        for check in self.checks:
            findings = check(path, self.state) or []
            for f in findings:
                logging.info(
                    "[DQ] %s %s: %s | path=%s",
                    f.get("severity", "INFO"),
                    f.get("code", "DQ_CODE"),
                    f.get("message", ""),
                    f.get("path", str(path)),
                )

    def _matches_pattern(self, filename: str) -> bool:
        """Simple glob match like 'bav_analysis_*.csv' or 'vtexp_*.csv'."""
        return fnmatch(filename, self.pattern)


class DataQualityWatcher:
    """Small orchestrator: wires the observer, handler, and a periodic "tick" together."""
    def __init__(self, watch_dir: str, pattern: str, recursive: bool, checks: List[DataQualityCheck]):
        """Capture settings, prepare shared state, and set up the observer."""
        self.watch_dir = Path(watch_dir)
        self.pattern = pattern
        self.recursive = recursive
        self.checks = checks
        self.state: Dict = {}
        self.observer = Observer()
        self._running = False

    def start(self):
        """Kick off file watching and start a tiny background heartbeat for cadence checks."""
        handler = DQFileHandler(self.checks, self.state, self.pattern)
        self.observer.schedule(handler, str(self.watch_dir), recursive=self.recursive)
        self.observer.start()
        self._running = True
        self._start_tick_loop()

    def _start_tick_loop(self) -> None:
        """Spawn a daemon thread that calls on_tick() every TICK_INTERVAL_SEC seconds."""
        def loop():
            while self._running:
                try:
                    self.on_tick()
                except Exception:
                    logging.exception("Tick loop error")
                time.sleep(TICK_INTERVAL_SEC)

        import threading

        threading.Thread(target=loop, daemon=True, name="DQTickLoop").start()

    def on_tick(self) -> None:
        """Hook for frequency/completeness: inspect self.state['arrivals'] and decide if we're on track.

        Example ideas:
        - Calculate inter-arrival gaps and flag when they exceed your target interval.
        - Count arrivals since midnight and compare with what you expected by now.
        """
        pass

    def stop(self) -> None:
        """Shut things down cleanly: stop observer and join the thread."""
        self._running = False
        self.observer.stop()
        self.observer.join()


# --- Small check stubs: fill in what you need for your dataset ---
def check_correctness_nonempty(path: Path, state: Dict) -> List[Finding]:
    """Quick sanity checks: file exists, not empty; add CSV header checks if helpful."""
    findings: List[Finding] = []
    try:
        if not path.exists():
            findings.append({
                "severity": "ERROR",
                "code": "DQ_MISSING_FILE",
                "message": "File does not exist",
                "path": str(path),
            })
            return findings

        if path.stat().st_size <= 0:
            findings.append({
                "severity": "ERROR",
                "code": "DQ_EMPTY_FILE",
                "message": "File is empty",
                "path": str(path),
            })
            return findings

        # Add more here if you want: CSV headers, required columns, simple type checks, etc.
    except Exception:
        logging.exception("correctness check failed for %s", path)

    return findings


def check_frequency(path: Path, state: Dict) -> List[Finding]:
    """Look at arrival gaps vs your target interval and flag slowdowns/spikes."""
    findings: List[Finding] = []
    # Compute deltas from state["arrivals"] and compare to your target interval; add findings as needed.
    return findings


def check_completeness(path: Path, state: Dict) -> List[Finding]:
    """Compare what we’ve received so far to what we expected by this time of day."""
    findings: List[Finding] = []
    # For example: expected counts by cutoff or per batch; if we’re short, add a WARN/ERROR finding.
    return findings


def main() -> int:
    """CLI entrypoint: parse flags, print a friendly banner, start the watcher, keep it running."""
    parser = argparse.ArgumentParser(description="Data Quality Watcher (template)")
    parser.add_argument("--watch-dir", default=DEFAULT_WATCH_DIR)
    parser.add_argument("--pattern", default=DEFAULT_PATTERN)
    # Boolean flag pair to allow toggling regardless of default
    parser.add_argument("--recursive", dest="recursive", action="store_true")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false")
    parser.set_defaults(recursive=DEFAULT_RECURSIVE)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("Data Quality Watcher (Template)")
    print("=" * 60)
    print(f"\nMonitoring: {args.watch_dir}")
    print(f"Pattern:    {args.pattern}")
    print("\nPress Ctrl+C to stop\n")

    watcher = DataQualityWatcher(
        watch_dir=args.watch_dir,
        pattern=args.pattern,
        recursive=args.recursive,
        checks=[
            check_correctness_nonempty,
            check_frequency,
            check_completeness,
        ],
    )

    def handle_sigint(signum, frame):
        print("\nShutting down watcher...")
        try:
            watcher.stop()
        finally:
            sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        watcher.start()
        print("Watcher is running...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_sigint(None, None)
    except Exception:
        logging.exception("Watcher crashed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

