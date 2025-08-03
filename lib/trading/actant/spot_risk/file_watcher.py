"""File watcher for automatic Spot Risk CSV processing.

This module monitors the input directory for new CSV files and automatically
processes them through the Greek calculation pipeline using a parallel worker pool.
"""

import os
import time
import logging
import json
import uuid
import threading
import multiprocessing
from pathlib import Path
from typing import Set, Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
import re
import time # Add time for watchdog sleep
import glob # Add glob for vtexp file searching
import queue # Add queue for DatabaseWriter timeout
import redis # Import redis
import pyarrow as pa  # Import pyarrow for Arrow serialization
import pickle  # Import pickle for envelope serialization
import sqlite3  # Import sqlite3 for position loading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from lib.monitoring.decorators import monitor
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.actant.spot_risk.database import SpotRiskDatabaseService
from lib.trading.market_prices.rosetta_stone import RosettaStone

logger = logging.getLogger(__name__)


def _wait_for_file_stabilization(filepath: Path, timeout: int = 10) -> bool:
    """
    Waits for a file to be fully written by checking for a non-zero, stable size.
    This function is intended to be called from a worker process.
        
    Returns:
        True if the file is ready, False if it times out or remains empty.
    """
    last_size = -1
    stable_for = 0
    start_time = time.time()
    logger.debug(f"Waiting for file to stabilize: {filepath.name}")

    while time.time() - start_time < timeout:
        try:
            current_size = filepath.stat().st_size
            if current_size > 0 and current_size == last_size:
                stable_for += 1
                if stable_for >= 2:  # Stable for 2 checks (approx 0.4 seconds)
                    logger.info(f"File is stable and ready: {filepath.name} (size: {current_size} bytes)")
                    return True
            else:
                stable_for = 0
            last_size = current_size
        except FileNotFoundError:
            logger.warning(f"File not found while waiting for stabilization: {filepath.name}")
            return False
        except PermissionError:
            # On Windows, a file might be temporarily locked while being written.
            # We reset the stability check and continue trying.
            stable_for = 0
            last_size = -1
        except Exception as e:
            logger.warning(f"Unexpected error checking file {filepath.name}: {e}")
            return False
        time.sleep(0.2)
    
    logger.warning(f"File did not stabilize after {timeout} seconds: {filepath.name}")
    return False


def calculation_worker(task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
    """
    Worker process for calculating Greeks. Pulls file paths from a queue,
    waits for them to be stable, processes them, and puts the resulting
    DataFrame in the result queue.
    """
    pid = os.getpid()
    logger.info(f"Calculation worker started with PID: {pid}")
    calculator = SpotRiskGreekCalculator()
    symbol_translator = RosettaStone()

    while True:
        task = task_queue.get()
        if task is None:
            logger.info(f"Worker {pid} received sentinel. Exiting.")
            break

        batch_id, filepath_str, vtexp_data, positions_snapshot = task
        filepath = Path(filepath_str)

        # --- NEW: Wait for file stabilization within the worker ---
        if not _wait_for_file_stabilization(filepath):
            logger.error(f"Worker {pid} failed to process {filepath.name} because it did not stabilize. Invalidating.")
            result_queue.put((batch_id, filepath.name, None)) # Signal failure for this file
            continue
        # --- END NEW ---

        logger.info(f"[PARALLEL] Worker PID={pid} started processing {filepath.name} for batch {batch_id}")

        try:
            start_time = time.time()
            df = parse_spot_risk_csv(filepath, calculate_time_to_expiry=True, vtexp_data=vtexp_data)
            if df is None or df.empty:
                raise ValueError("Failed to parse CSV or CSV is empty.")
            
            # Filter by positions if we have any active positions
            if positions_snapshot:
                original_count = len(df)
                
                # Translate symbols to Bloomberg format for comparison
                df['bloomberg_symbol'] = df['key'].apply(
                    lambda x: symbol_translator.translate(x, 'actantrisk', 'bloomberg') if x else None
                )
                
                # Keep rows where we have positions OR future rows (needed for Greek calculations)
                # Future rows identified by itype='F' - handle case sensitivity
                is_future = df['itype'].astype(str).str.upper() == 'F' if 'itype' in df.columns else pd.Series(False, index=df.index)
                has_position = df['bloomberg_symbol'].isin(positions_snapshot)
                df_filtered = df[is_future | has_position]
                
                rows_dropped = original_count - len(df_filtered)
                futures_kept = is_future.sum()
                logger.info(f"Worker {pid}: Filtered {filepath.name} - kept {len(df_filtered)}/{original_count} rows (dropped {rows_dropped} non-position rows, preserved {futures_kept} future rows)")
                
                df = df_filtered
                
            # Skip processing if no rows remain after filtering
            if df.empty:
                logger.info(f"Worker {pid}: No positions to process in {filepath.name}, skipping calculations")
                result_queue.put((batch_id, filepath.name, pd.DataFrame()))
                continue

            df_with_greeks, _ = calculator.calculate_greeks(df)
            df_with_aggregates = calculator.calculate_aggregates(df_with_greeks)
            
            processing_time = time.time() - start_time
            logger.info(f"[PARALLEL] Worker PID={pid} finished {filepath.name} in {processing_time:.2f}s")
            
            result_queue.put((batch_id, filepath.name, df_with_aggregates))
            
        except Exception as e:
            logger.error(f"Worker {pid} failed to process {filepath.name}: {e}", exc_info=True)
            result_queue.put((batch_id, filepath.name, None)) # Signal failure for this file

class ResultPublisher(threading.Thread):
    """
    A dedicated thread to take completed batches, serialize them, and publish
    them to a Redis channel for downstream consumption.
    """
    def __init__(self, result_queue: multiprocessing.Queue, total_files_per_batch: Dict[str, int]):
        super().__init__()
        self.result_queue = result_queue
        self.total_files_per_batch = total_files_per_batch
        self.pending_batches: Dict[str, Dict[str, Any]] = {}
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)  # Changed to handle raw bytes for Arrow
        self.redis_channel = "spot_risk:results_channel"
        self.daemon = True
        logger.info("ResultPublisher thread initialized.")

    def run(self):
        logger.info("ResultPublisher thread started, connected to Redis.")
        while True:
            self._check_for_stale_batches()
            try:
                result = self.result_queue.get(timeout=20.0)
            except queue.Empty:
                continue

            if result is None:
                logger.info("ResultPublisher received sentinel. Exiting.")
                break

            batch_id, filename, df = result
            
            if batch_id not in self.pending_batches and batch_id in self.total_files_per_batch:
                logger.info(f"Initializing tracking for new batch '{batch_id}'.")
                self.pending_batches[batch_id] = {
                    'results': [],
                    'start_time': time.time()
                }

            if batch_id not in self.pending_batches:
                logger.warning(f"Received result for an unknown or stale batch '{batch_id}'. Discarding.")
                continue

            if df is None:
                logger.error(f"Received failed result for {filename} in batch {batch_id}. Batch will be invalidated.")
                self.pending_batches.pop(batch_id, None)
                self.total_files_per_batch.pop(batch_id, None)
                continue

            self.pending_batches[batch_id]['results'].append(df)
            logger.info(f"Aggregated chunk {filename} for batch {batch_id}. "
                        f"({len(self.pending_batches[batch_id]['results'])}/{self.total_files_per_batch.get(batch_id, '?')})")

            if batch_id in self.total_files_per_batch and \
               len(self.pending_batches[batch_id]['results']) == self.total_files_per_batch[batch_id]:
                
                # --- Start Instrumentation ---
                batch_start_time = self.pending_batches[batch_id]['start_time']
                processing_duration = time.time() - batch_start_time
                logger.info(f"Batch {batch_id} is complete. Publishing to Redis... (Processing Duration: {processing_duration:.3f}s)")
                # --- End Instrumentation ---
                
                # Add detailed timing for the publishing process
                t0 = time.time()
                
                full_df = pd.concat(self.pending_batches[batch_id]['results'], ignore_index=True)
                t1 = time.time()
                
                try:
                    # Convert DataFrame to Apache Arrow format for high-speed serialization
                    arrow_table = pa.Table.from_pandas(full_df)
                    t2 = time.time()
                    
                    sink = pa.BufferOutputStream()
                    with pa.ipc.new_stream(sink, arrow_table.schema) as writer:
                        writer.write_table(arrow_table)
                    buffer = sink.getvalue()
                    t3 = time.time()
                    
                    # Create metadata envelope with Arrow data
                    payload = {
                        'batch_id': batch_id,
                        'publish_timestamp': time.time(),
                        'format': 'arrow',
                        'data': buffer  # The raw Arrow bytes
                    }
                    
                    # Use pickle for the envelope to handle binary data
                    pickled_payload = pickle.dumps(payload)
                    payload_size_mb = len(pickled_payload) / (1024 * 1024)
                    
                    # Add detailed logging to diagnose the delay
                    logger.info(f"About to publish {payload_size_mb:.2f} MB to Redis...")
                    t_pre_publish = time.time()
                    
                    result = self.redis_client.publish(self.redis_channel, pickled_payload)
                    
                    t4 = time.time()
                    logger.info(f"Redis publish returned: {result} subscribers received the message")

                    logger.info(
                        f"Successfully published batch {batch_id} to Redis channel '{self.redis_channel}' using Arrow format.\n"
                        f"    - pd.concat:      {(t1 - t0) * 1000:.2f} ms\n"
                        f"    - pa.Table.from_pandas: {(t2 - t1) * 1000:.2f} ms\n"
                        f"    - pa.write_table: {(t3 - t2) * 1000:.2f} ms\n"
                        f"    - redis.publish:  {(t4 - t3) * 1000:.2f} ms\n"
                        f"    -------------------------------------\n"
                        f"    - Total Publish Time: {(t4 - t0) * 1000:.2f} ms"
                    )
                except Exception as e:
                    logger.error(f"Failed to publish batch {batch_id} to Redis: {e}", exc_info=True)

                self.pending_batches.pop(batch_id, None)
                self.total_files_per_batch.pop(batch_id, None)

    def _check_for_stale_batches(self, timeout_seconds: int = 120):
        """Checks for batches that have not completed within the timeout and removes them."""
        now = time.time()
        stale_batches = []
        for batch_id, data in self.pending_batches.items():
            if now - data['start_time'] > timeout_seconds:
                stale_batches.append(batch_id)
        
        for batch_id in stale_batches:
            logger.error(f"Batch '{batch_id}' is stale (older than {timeout_seconds}s). Discarding {len(self.pending_batches[batch_id]['results'])} received chunks.")
            self.pending_batches.pop(batch_id, None)
            self.total_files_per_batch.pop(batch_id, None)


class SpotRiskFileHandler(FileSystemEventHandler):
    """A lightweight file event handler that puts file paths onto a task queue."""
    
    def __init__(self, task_queue: multiprocessing.Queue, total_files_per_batch: Dict[str, int], 
                 vtexp_cache: Dict[str, Any], watcher_ref):
        self.task_queue = task_queue
        self.total_files_per_batch = total_files_per_batch
        self.vtexp_cache = vtexp_cache
        self.watcher_ref = watcher_ref  # Reference to SpotRiskWatcher for position access
        self.processed_files_cache = set()
        self.last_processed_batch_id = None
        self.batch_position_snapshots = {}  # Store position snapshot per batch
        self.filename_pattern = re.compile(
            r"bav_analysis_(\d{8}_\d{6})_chunk_(\d+)_of_(\d+)\.csv"
        )
        logger.info("SpotRiskFileHandler initialized with position awareness.")
    
    @monitor()
    def on_created(self, event):
        if event.is_directory:
            return

        filepath_str = event.src_path
        if filepath_str in self.processed_files_cache:
            return
        
        filepath = Path(filepath_str)
            
        # --- REMOVED: No longer waiting here. The worker will wait. ---
        
        match = self.filename_pattern.match(filepath.name)

        if not match:
            logger.debug(f"File did not match expected chunk format: {filepath.name}")
            return
            
        batch_id, chunk_num_str, total_chunks_str = match.groups()
        total_chunks = int(total_chunks_str)
        
        # --- Efficient vtexp Cache Refresh ---
        # Only check for a new vtexp file if this is the first chunk of a new batch
        if batch_id != self.last_processed_batch_id:
            logger.info(f"New batch '{batch_id}' detected. Checking for vtexp file updates.")
            self._refresh_vtexp_cache()
            self.last_processed_batch_id = batch_id
            
            # Take a snapshot of positions for this batch
            with self.watcher_ref.positions_lock:
                self.batch_position_snapshots[batch_id] = self.watcher_ref.positions_cache.copy()
                logger.info(f"Captured position snapshot for batch {batch_id}: {len(self.batch_position_snapshots[batch_id])} active positions")
        # --- End Efficient Refresh ---

        # Take a snapshot of the current vtexp data to ensure consistency for this entire batch
        vtexp_data_for_batch = self.vtexp_cache.get('data')
        
        # Get the position snapshot for this batch
        positions_snapshot = self.batch_position_snapshots.get(batch_id, set())

        if batch_id not in self.total_files_per_batch:
            self.total_files_per_batch[batch_id] = total_chunks
            logger.info(f"Initialized batch {batch_id}. Expecting {total_chunks} total chunks.")

        logger.info(f"Immediately queueing task for chunk {chunk_num_str}/{total_chunks} of batch {batch_id}")
        self.task_queue.put((batch_id, filepath_str, vtexp_data_for_batch, positions_snapshot))
        
        self.processed_files_cache.add(filepath_str)
        threading.Timer(10.0, self.processed_files_cache.discard, [filepath_str]).start()

    def _refresh_vtexp_cache(self):
        """Checks for a new vtexp file and updates the shared cache if found."""
        try:
            vtexp_dir = Path('data/input/vtexp')
            latest_vtexp_file = max(glob.glob(str(vtexp_dir / 'vtexp_*.csv')), key=os.path.getctime, default=None)

            if latest_vtexp_file and latest_vtexp_file != self.vtexp_cache.get('filepath'):
                logger.info(f"New vtexp file found: {latest_vtexp_file}. Reloading cache.")
                df = pd.read_csv(latest_vtexp_file)
                # Corrected from 'expiry_code' to 'symbol' to match the actual CSV header.
                self.vtexp_cache['data'] = df.set_index('symbol')['vtexp'].to_dict()
                self.vtexp_cache['filepath'] = latest_vtexp_file
                logger.info(f"vtexp cache updated with {len(df)} entries.")
        except Exception as e:
            logger.error(f"Failed to refresh vtexp cache: {e}", exc_info=True)


class SpotRiskWatcher:
    """Main watcher service that orchestrates the parallel processing pipeline."""
    
    def __init__(self, input_dir: str, num_workers: Optional[int] = None):
        self.input_dir = Path(input_dir)
        self.num_workers = int(num_workers or os.cpu_count())
        self.observer = Observer()
        
        # Using a Manager for the shared dictionary across processes
        self.manager = multiprocessing.Manager()
        self.total_files_per_batch = self.manager.dict()
        self.vtexp_cache = self.manager.dict({
            'filepath': None,
            'data': None
        })
        
        # Position-aware cache
        self.positions_cache = set()  # Bloomberg symbols we have positions for
        self.positions_lock = threading.Lock()
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)
        
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        
        self.workers: List[multiprocessing.Process] = []
        self.result_publisher_thread: Optional[ResultPublisher] = None
        self.watchdog_thread: Optional[threading.Thread] = None
        self.position_listener_thread: Optional[threading.Thread] = None
        
        logger.info(f"SpotRiskWatcher initialized for {input_dir} with {self.num_workers} workers (CPU count: {os.cpu_count()}).")
        
    def _load_positions_from_db(self):
        """Load symbols with open positions from trades.db."""
        try:
            with self.positions_lock:
                conn = sqlite3.connect("trades.db")
                cursor = conn.cursor()
                
                # Query for all symbols with non-zero open positions
                cursor.execute("""
                    SELECT DISTINCT symbol 
                    FROM positions 
                    WHERE open_position != 0
                """)
                
                symbols = {row[0] for row in cursor.fetchall()}
                self.positions_cache = symbols
                conn.close()
                
                logger.info(f"Loaded {len(self.positions_cache)} active position symbols from database")
        except Exception as e:
            logger.error(f"Failed to load positions from database: {e}", exc_info=True)
    
    def _listen_for_position_updates(self):
        """Listen for position update notifications via Redis."""
        logger.info("Starting position update listener thread...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe("positions:changed")
        
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            
            logger.info("Received positions:changed signal. Refreshing position cache...")
            self._load_positions_from_db()
        
    @monitor()
    def start(self):
        """Start the file watcher and the processing pool."""
        logger.info("Starting SpotRiskWatcher pipeline...")
        
        # Load initial positions
        self._load_positions_from_db()
        
        # Start position listener thread
        self.position_listener_thread = threading.Thread(
            target=self._listen_for_position_updates, 
            daemon=True,
            name="PositionListener"
        )
        self.position_listener_thread.start()

        # 1. Start Result Publisher Thread
        self.result_publisher_thread = ResultPublisher(self.result_queue, self.total_files_per_batch)
        self.result_publisher_thread.start()

        # 2. Start Worker Processes
        for i in range(self.num_workers):
            process = multiprocessing.Process(
                target=calculation_worker,
                args=(self.task_queue, self.result_queue),
                name=f"Worker-{i+1}"
            )
            process.daemon = True
            process.start()
            self.workers.append(process)

        # 3. Start the Worker Watchdog Thread
        self.watchdog_thread = threading.Thread(target=self._worker_watchdog, daemon=True)
        self.watchdog_thread.start()
        logger.info("Worker watchdog thread started.")

        # 4. Start File System Observer
        event_handler = SpotRiskFileHandler(self.task_queue, self.total_files_per_batch, self.vtexp_cache, self)
        self.observer.schedule(event_handler, str(self.input_dir), recursive=True)
        self.observer.start()
        
        logger.info("SpotRiskWatcher pipeline started successfully.")

    def _worker_watchdog(self):
        """Monitors worker processes and restarts any that have died."""
        while True:
            for i, worker in enumerate(self.workers):
                if not worker.is_alive():
                    logger.error(f"Worker process {worker.name} (PID: {worker.pid}) has died unexpectedly. Restarting.")
                    
                    # Create and start a new worker to replace the dead one
                    new_worker = multiprocessing.Process(
                        target=calculation_worker,
                        args=(self.task_queue, self.result_queue),
                        name=f"Worker-{i+1}"
                    )
                    new_worker.daemon = True
                    new_worker.start()
                    self.workers[i] = new_worker
                    logger.info(f"Restarted worker {new_worker.name} (PID: {new_worker.pid}).")
            
            time.sleep(15) # Check every 15 seconds
    
    def stop(self):
        """Gracefully stop the watcher and all child processes/threads."""
        logger.info("Stopping SpotRiskWatcher pipeline...")

        # 1. Stop watching for new files
        self.observer.stop()
        self.observer.join()
        logger.info("File observer stopped.")

        # 2. Signal workers to terminate
        for _ in self.workers:
            self.task_queue.put(None)
        
        # 3. Wait for workers to finish
        for worker in self.workers:
            worker.join()
        logger.info("Calculation workers stopped.")

        # 4. Signal Result Publisher to terminate
        self.result_queue.put(None)
        if self.result_publisher_thread:
            self.result_publisher_thread.join()
        logger.info("Result publisher thread stopped.")

        # Watchdog is a daemon thread, so it will exit automatically.
        
        # 5. Stop the manager
        self.manager.shutdown()
        logger.info("Multiprocessing manager stopped.")
        
        logger.info("SpotRiskWatcher pipeline stopped successfully.") 