import logging
import multiprocessing
import queue
import re
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import pyarrow as pa
import redis
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lib.monitoring.decorators import monitor
from .publisher import PriceOnlyResultPublisher
from .worker import price_worker


logger = logging.getLogger(__name__)


class PriceOnlyFileHandler(FileSystemEventHandler):
    def __init__(self, task_queue: multiprocessing.Queue, total_files_per_batch: Dict[str, int]):
        self.task_queue = task_queue
        self.total_files_per_batch = total_files_per_batch
        self.processed_files_cache = set()
        self.filename_pattern = re.compile(r"bav_analysis_(\d{8}_\d{6})_chunk_(\d+)_of_(\d+)\.csv")

    @monitor()
    def on_created(self, event):
        if event.is_directory:
            return
        filepath_str = event.src_path
        if filepath_str in self.processed_files_cache:
            return
        path = Path(filepath_str)
        match = self.filename_pattern.match(path.name)
        if not match:
            logger.debug(f"File did not match expected chunk format: {path.name}")
            return
        batch_id, chunk_num_str, total_chunks_str = match.groups()
        total_chunks = int(total_chunks_str)
        if batch_id not in self.total_files_per_batch:
            self.total_files_per_batch[batch_id] = total_chunks
            logger.info(f"Initialized batch {batch_id}. Expecting {total_chunks} chunks.")
        self.task_queue.put((batch_id, str(path)))
        self.processed_files_cache.add(filepath_str)


class PriceOnlyResultAggregator(threading.Thread):
    def __init__(self, result_queue: multiprocessing.Queue, total_files_per_batch: Dict[str, int], publisher: PriceOnlyResultPublisher, batch_timeout_s: int = 3):
        super().__init__(daemon=True)
        self.result_queue = result_queue
        self.total_files_per_batch = total_files_per_batch
        self.publisher = publisher
        self.batch_timeout_s = batch_timeout_s
        self.pending_batches: Dict[str, Dict[str, Any]] = {}

    def _check_for_stale(self):
        now = time.time()
        stale: List[str] = []
        for batch_id, meta in self.pending_batches.items():
            if now - meta.get("start_time", now) > self.batch_timeout_s:
                stale.append(batch_id)
        for batch_id in stale:
            meta = self.pending_batches.pop(batch_id, None)
            expected = self.total_files_per_batch.pop(batch_id, None)
            if meta and meta["results"]:
                full_df = pd.concat(meta["results"], ignore_index=True)
                table = pa.Table.from_pandas(full_df, preserve_index=False)
                self.publisher.publish(batch_id, table)
                logger.warning(f"Flushed partial batch '{batch_id}' after timeout (expected={expected}, got={len(meta['results'])}).")

    def run(self):
        logger.info("PriceOnlyResultAggregator started.")
        while True:
            self._check_for_stale()
            try:
                result = self.result_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if result is None:
                logger.info("Aggregator received sentinel. Exiting.")
                break
            batch_id, filename, df = result
            if batch_id not in self.pending_batches and batch_id in self.total_files_per_batch:
                self.pending_batches[batch_id] = {"results": [], "start_time": time.time()}
            if batch_id not in self.pending_batches:
                logger.warning(f"Received result for unknown batch '{batch_id}'. Discarding.")
                continue
            if df is None:
                logger.error(f"Result for {filename} in batch {batch_id} failed. Discarding entire batch.")
                self.pending_batches.pop(batch_id, None)
                self.total_files_per_batch.pop(batch_id, None)
                continue
            self.pending_batches[batch_id]["results"].append(df)
            expected = self.total_files_per_batch.get(batch_id, None)
            have = len(self.pending_batches[batch_id]["results"])
            logger.info(f"Aggregated chunk {filename} for batch {batch_id} ({have}/{expected}).")
            if expected is not None and have >= expected:
                full_df = pd.concat(self.pending_batches[batch_id]["results"], ignore_index=True)
                table = pa.Table.from_pandas(full_df, preserve_index=False)
                self.publisher.publish(batch_id, table)
                self.pending_batches.pop(batch_id, None)
                self.total_files_per_batch.pop(batch_id, None)


class PriceOnlyWatcher:
    def __init__(self, input_dir: str, num_workers: Optional[int] = None, channel: str = "spot_risk:prices_full"):
        self.input_dir = Path(input_dir)
        self.num_workers = int(num_workers or max(1, (multiprocessing.cpu_count() or 1) - 4))
        self.task_queue: multiprocessing.Queue = multiprocessing.Queue()
        self.result_queue: multiprocessing.Queue = multiprocessing.Queue()
        self.total_files_per_batch = multiprocessing.Manager().dict()  # shared
        self.publisher = PriceOnlyResultPublisher(channel=channel)
        self.observer: Optional[Observer] = None
        self.aggregator: Optional[PriceOnlyResultAggregator] = None
        self.workers: List[multiprocessing.Process] = []

    @monitor()
    def start(self):
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Starting PriceOnlyWatcher on {self.input_dir} with {self.num_workers} workers.")

        handler = PriceOnlyFileHandler(self.task_queue, self.total_files_per_batch)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.input_dir), recursive=True)
        self.observer.start()

        for i in range(self.num_workers):
            p = multiprocessing.Process(target=price_worker, args=(self.task_queue, self.result_queue), name=f"PriceWorker-{i+1}")
            p.daemon = True
            p.start()
            self.workers.append(p)

        self.aggregator = PriceOnlyResultAggregator(self.result_queue, self.total_files_per_batch, self.publisher, batch_timeout_s=3)
        self.aggregator.start()
        logger.info("PriceOnlyWatcher started.")

    def stop(self):
        logger.info("Stopping PriceOnlyWatcher...")
        try:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
        finally:
            for _ in self.workers:
                self.task_queue.put(None)
            for p in self.workers:
                p.join(timeout=2.0)
            if self.aggregator:
                self.result_queue.put(None)
                self.aggregator.join(timeout=2.0)
        logger.info("PriceOnlyWatcher stopped.")

