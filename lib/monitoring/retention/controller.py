"""Controller for orchestrating retention operations.

This module implements the controller layer (MVC pattern) for retention management.
It handles threading, error recovery, and monitoring of the retention process.
"""

import threading
import time
from typing import Optional

from .manager import RetentionManager


class RetentionController:
    """Orchestrates retention operations with error handling and monitoring.
    
    Runs a background thread that periodically calls RetentionManager to
    clean up old records. Handles errors gracefully and provides monitoring.
    
    Attributes:
        manager: RetentionManager instance
        cleanup_interval: Seconds between cleanup runs (default: 60)
        max_consecutive_errors: Max errors before warning (default: 5)
    """
    
    def __init__(
        self,
        manager: RetentionManager,
        cleanup_interval: int = 60,
        max_consecutive_errors: int = 5
    ):
        """Initialize retention controller.
        
        Args:
            manager: RetentionManager instance to use
            cleanup_interval: Seconds between cleanup attempts
            max_consecutive_errors: Max consecutive errors before warning
        """
        self.manager = manager
        self.cleanup_interval = cleanup_interval
        self.max_consecutive_errors = max_consecutive_errors
        
        # Thread management
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self._stop_event = threading.Event()
        
        # Error tracking
        self.consecutive_errors = 0
        self.total_errors = 0
        self.total_cleanups = 0
        
        # Stats tracking
        self.total_process_deleted = 0
        self.total_data_deleted = 0
        self.last_cleanup_time: Optional[float] = None
        self.last_error: Optional[str] = None
    
    def start(self) -> None:
        """Start the retention controller thread.
        
        Starts a background thread that runs cleanup every interval.
        Safe to call multiple times (no-op if already running).
        """
        if self.running:
            print("[RETENTION] Controller already running")
            return
            
        self.running = True
        self._stop_event.clear()
        
        # Start background thread
        self.thread = threading.Thread(
            target=self._run_cleanup_loop,
            name="RetentionController",
            daemon=True
        )
        self.thread.start()
        
        print(f"[RETENTION] Started controller (interval: {self.cleanup_interval}s)")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop the retention controller gracefully.
        
        Args:
            timeout: Max seconds to wait for thread to stop
        """
        if not self.running:
            return
            
        print("[RETENTION] Stopping controller...")
        self.running = False
        self._stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                print("[RETENTION] Warning: Thread did not stop gracefully")
            else:
                print("[RETENTION] Controller stopped")
    
    def _run_cleanup_loop(self) -> None:
        """Main cleanup loop (runs in background thread).
        
        Executes cleanup at regular intervals with error handling.
        """
        print(f"[RETENTION] Cleanup thread started (PID: {threading.get_ident()})")
        
        while self.running:
            try:
                # Perform cleanup
                self._run_single_cleanup()
                
            except Exception as e:
                # Catch-all to prevent thread death
                print(f"[RETENTION] Unexpected error in cleanup loop: {e}")
                self.total_errors += 1
                
            # Wait for next interval (interruptible)
            if self._stop_event.wait(timeout=self.cleanup_interval):
                # Stop event was set
                break
                
        print("[RETENTION] Cleanup thread exiting")
    
    def _run_single_cleanup(self) -> None:
        """Run a single cleanup cycle with error handling."""
        start_time = time.time()
        
        try:
            # Call retention manager
            process_deleted, data_deleted = self.manager.cleanup_old_records()
            
            # Update stats
            self.total_process_deleted += process_deleted
            self.total_data_deleted += data_deleted
            self.total_cleanups += 1
            self.last_cleanup_time = time.time()
            
            # Reset error counter on success
            self.consecutive_errors = 0
            
            # Log if significant deletions
            total = process_deleted + data_deleted
            if total > 0:
                duration_ms = (time.time() - start_time) * 1000
                print(f"[RETENTION] Cleaned {total:,} records "
                      f"({process_deleted:,} process, {data_deleted:,} data) "
                      f"in {duration_ms:.1f}ms")
                      
        except Exception as e:
            # Track errors
            self.consecutive_errors += 1
            self.total_errors += 1
            self.last_error = str(e)
            
            # Log based on error type
            if "database is locked" in str(e):
                # Expected under high load - only warn if persistent
                if self.consecutive_errors > self.max_consecutive_errors:
                    print(f"[RETENTION] WARNING: Database locked for "
                          f"{self.consecutive_errors} consecutive attempts")
            else:
                # Unexpected error - always log
                print(f"[RETENTION] ERROR during cleanup: {e}")
                
            # Don't spam logs for persistent errors
            if self.consecutive_errors == self.max_consecutive_errors:
                print(f"[RETENTION] Suppressing further error logs until success")
    
    def get_controller_stats(self) -> dict:
        """Get statistics about controller operation.
        
        Returns:
            Dict with controller statistics including:
            - running: Whether controller is active
            - total_cleanups: Number of successful cleanup cycles
            - total_errors: Total error count
            - consecutive_errors: Current consecutive error count
            - total_process_deleted: Total process records deleted
            - total_data_deleted: Total data records deleted
            - last_cleanup_time: Timestamp of last successful cleanup
            - last_error: Most recent error message
            - uptime_seconds: Time since controller started
        """
        stats = {
            "running": self.running,
            "total_cleanups": self.total_cleanups,
            "total_errors": self.total_errors,
            "consecutive_errors": self.consecutive_errors,
            "total_process_deleted": self.total_process_deleted,
            "total_data_deleted": self.total_data_deleted,
            "last_cleanup_time": self.last_cleanup_time,
            "last_error": self.last_error,
            "cleanup_interval": self.cleanup_interval,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
        
        # Calculate uptime if running
        if self.thread and self.thread.is_alive():
            # Thread doesn't track start time, so estimate from cleanups
            if self.total_cleanups > 0:
                stats["estimated_uptime_seconds"] = self.total_cleanups * self.cleanup_interval
        
        return stats
    
    def force_cleanup(self) -> tuple[int, int]:
        """Force an immediate cleanup cycle.
        
        Useful for testing or manual intervention.
        Runs in the calling thread (not background thread).
        
        Returns:
            Tuple of (process_deleted, data_deleted)
            
        Raises:
            Any exception from RetentionManager
        """
        print("[RETENTION] Forcing manual cleanup...")
        result = self.manager.cleanup_old_records()
        print(f"[RETENTION] Manual cleanup complete: {sum(result)} records deleted")
        return result 