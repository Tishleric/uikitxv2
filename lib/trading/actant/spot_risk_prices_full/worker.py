import logging
import multiprocessing
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import pyarrow as pa

from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv


logger = logging.getLogger(__name__)


def wait_for_file_stable(filepath: Path, timeout: int = 10) -> bool:
    last_size = -1
    stable_for = 0
    start = time.time()
    while time.time() - start < timeout:
        try:
            size = filepath.stat().st_size
            if size > 0 and size == last_size:
                stable_for += 1
                if stable_for >= 2:
                    return True
            else:
                stable_for = 0
                last_size = size
        except FileNotFoundError:
            return False
        except PermissionError:
            stable_for = 0
            last_size = -1
        time.sleep(0.2)
    return False


def price_worker(task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue) -> None:
    """Worker: stabilize → parse → select columns; emit DataFrame."""
    pid = multiprocessing.current_process().pid
    logger.info(f"Price-only worker started (PID {pid}).")
    while True:
        task = task_queue.get()
        if task is None:
            logger.info(f"Worker PID {pid} received sentinel. Exiting.")
            break
        batch_id, filepath_str = task
        path = Path(filepath_str)
        if not wait_for_file_stable(path):
            logger.warning(f"Worker PID {pid}: file did not stabilize: {path.name}")
            result_queue.put((batch_id, path.name, None))
            continue
        try:
            df = parse_spot_risk_csv(path, calculate_time_to_expiry=False)
            if df is None or df.empty:
                result_queue.put((batch_id, path.name, pd.DataFrame()))
                continue
            # Normalize and select only the requested columns
            df.columns = [c.lower() for c in df.columns]
            cols = [c for c in ("key", "itype", "bid", "ask", "adjtheor") if c in df.columns]
            df = df[cols].copy()
            result_queue.put((batch_id, path.name, df))
        except Exception as e:
            logger.error(f"Worker PID {pid} failed on {path.name}: {e}", exc_info=True)
            result_queue.put((batch_id, path.name, None))

