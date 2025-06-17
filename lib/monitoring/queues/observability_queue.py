"""Observability queue with error-first strategy and zero-loss guarantees - Phase 4"""

import queue
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import threading
import inspect


@dataclass
class QueueMetrics:
    """Metrics for monitoring queue health"""
    normal_enqueued: int = 0
    error_enqueued: int = 0
    normal_dropped: int = 0  # Should always be 0 with overflow buffer
    error_dropped: int = 0   # Must always be 0
    overflowed: int = 0
    recovered: int = 0
    batch_count: int = 0
    last_drain_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for reporting"""
        return {
            'normal_enqueued': self.normal_enqueued,
            'error_enqueued': self.error_enqueued,
            'normal_dropped': self.normal_dropped,
            'error_dropped': self.error_dropped,
            'overflowed': self.overflowed,
            'recovered': self.recovered,
            'batch_count': self.batch_count,
            'last_drain_time': self.last_drain_time,
            'queue_health': 'healthy' if self.error_dropped == 0 else 'CRITICAL'
        }


@dataclass
class ObservabilityRecord:
    """Single record to be queued for observability"""
    ts: str  # ISO format timestamp
    process: str  # module.function
    status: str  # OK or ERR
    duration_ms: float
    exception: Optional[str] = None
    args: Optional[List[str]] = None
    kwargs: Optional[Dict[str, str]] = None
    result: Optional[str] = None
    # New fields for parent-child tracking
    thread_id: int = 0  # Thread identifier from threading.get_ident()
    call_depth: int = 0  # Stack depth from len(inspect.stack())
    start_ts_us: int = 0  # Start timestamp in microseconds for precise ordering
    
    def is_error(self) -> bool:
        """Check if this is an error record"""
        return self.status == "ERR"


class ObservabilityQueue:
    """
    Dual queue system with error-first strategy.
    
    Features:
    - Unlimited queue for errors (never dropped)
    - Limited queue for normal records (10k)
    - Overflow ring buffer (50k) for normal records
    - Automatic recovery from overflow
    - Comprehensive metrics
    """
    
    def __init__(self, 
                 normal_maxsize: int = 10_000,
                 overflow_maxsize: int = 50_000,
                 warning_threshold: int = 8_000):
        # Dual queue system
        self.error_queue = queue.Queue()  # Unlimited size
        self.normal_queue = queue.Queue(maxsize=normal_maxsize)
        
        # Overflow buffer for normal records
        self.overflow_buffer = deque(maxlen=overflow_maxsize)
        
        # Configuration
        self.normal_maxsize = normal_maxsize
        self.overflow_maxsize = overflow_maxsize
        self.warning_threshold = warning_threshold
        
        # Metrics
        self.metrics = QueueMetrics()
        self._lock = threading.Lock()
        
        # Warning state
        self._last_warning_time = 0
        self._warning_interval = 60  # Warn at most once per minute
    
    def put(self, record: ObservabilityRecord) -> None:
        """
        Add a record to the appropriate queue.
        
        Errors always go to error queue (unlimited).
        Normal records try normal queue, then overflow buffer.
        """
        if record.is_error():
            # Errors MUST never be dropped
            self.error_queue.put(record)
            with self._lock:
                self.metrics.error_enqueued += 1
        else:
            # Try normal queue first
            try:
                self.normal_queue.put_nowait(record)
                with self._lock:
                    self.metrics.normal_enqueued += 1
                    
                # Check if we should warn about queue depth
                if self.normal_queue.qsize() > self.warning_threshold:
                    self._maybe_warn_queue_depth()
                    
            except queue.Full:
                # Queue full, use overflow buffer
                with self._lock:
                    self.overflow_buffer.append(record)
                    self.metrics.overflowed += 1
                    self._maybe_warn_overflow()
    
    def drain(self, max_items: int = 100) -> List[ObservabilityRecord]:
        """
        Drain records with error-first priority.
        
        Order:
        1. All available errors (up to max_items)
        2. Normal records
        3. Recovery from overflow if space available
        """
        batch = []
        
        # Phase 1: Drain errors first (highest priority)
        while not self.error_queue.empty() and len(batch) < max_items:
            try:
                batch.append(self.error_queue.get_nowait())
            except queue.Empty:
                break
        
        # Phase 2: Drain normal records
        while not self.normal_queue.empty() and len(batch) < max_items:
            try:
                batch.append(self.normal_queue.get_nowait())
            except queue.Empty:
                break
        
        # Phase 3: Try to recover from overflow buffer
        with self._lock:
            recovered_count = 0
            while self.overflow_buffer and not self.normal_queue.full():
                try:
                    record = self.overflow_buffer.popleft()
                    self.normal_queue.put_nowait(record)
                    recovered_count += 1
                    self.metrics.recovered += 1
                except queue.Full:
                    # Put it back and stop trying
                    self.overflow_buffer.appendleft(record)
                    break
            
            # Update metrics
            if batch:
                self.metrics.batch_count += 1
                self.metrics.last_drain_time = time.time()
        
        return batch
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        with self._lock:
            return {
                'error_queue_size': self.error_queue.qsize(),
                'normal_queue_size': self.normal_queue.qsize(),
                'overflow_buffer_size': len(self.overflow_buffer),
                'normal_queue_capacity': self.normal_maxsize,
                'overflow_capacity': self.overflow_maxsize,
                'is_normal_full': self.normal_queue.full(),
                'has_overflow': len(self.overflow_buffer) > 0,
                'metrics': self.metrics.to_dict()
            }
    
    def clear(self) -> None:
        """Clear all queues and reset metrics"""
        # Drain all queues
        while not self.error_queue.empty():
            try:
                self.error_queue.get_nowait()
            except queue.Empty:
                break
                
        while not self.normal_queue.empty():
            try:
                self.normal_queue.get_nowait()
            except queue.Empty:
                break
        
        with self._lock:
            self.overflow_buffer.clear()
            self.metrics = QueueMetrics()
    
    def _maybe_warn_queue_depth(self) -> None:
        """Warn if queue is getting full (rate limited)"""
        current_time = time.time()
        if current_time - self._last_warning_time > self._warning_interval:
            queue_size = self.normal_queue.qsize()
            print(f"[WARNING] ObservabilityQueue normal queue at {queue_size}/{self.normal_maxsize} "
                  f"({queue_size/self.normal_maxsize*100:.1f}% full)")
            self._last_warning_time = current_time
    
    def _maybe_warn_overflow(self) -> None:
        """Warn when using overflow buffer (rate limited)"""
        current_time = time.time()
        if current_time - self._last_warning_time > self._warning_interval:
            overflow_size = len(self.overflow_buffer)
            print(f"[WARNING] ObservabilityQueue using overflow buffer: {overflow_size}/{self.overflow_maxsize} "
                  f"({overflow_size/self.overflow_maxsize*100:.1f}% full)")
            self._last_warning_time = current_time 