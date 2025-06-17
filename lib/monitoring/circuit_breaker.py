"""Simple circuit breaker for preventing cascading failures.

A circuit breaker prevents cascading failures by failing fast when a 
component is unhealthy, allowing it time to recover.
"""

import time
import threading
from typing import Callable, Any, Optional
from datetime import datetime


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Simple circuit breaker implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures exceeded threshold, requests fail immediately  
    - HALF_OPEN: Testing if service recovered
    
    Attributes:
        failure_threshold: Number of failures before opening circuit
        timeout_seconds: How long to wait before trying again
        success_threshold: Successes needed in HALF_OPEN to close circuit
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        success_threshold: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        # State tracking
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_attempt_time: Optional[float] = None
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.circuit_opened_count = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            self.total_calls += 1
            
            # Check if we should transition from OPEN to HALF_OPEN
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. Next retry in "
                        f"{self._time_until_retry():.1f} seconds"
                    )
        
        # Try to execute the function
        try:
            result = func(*args, **kwargs)
            
            # Record success
            with self._lock:
                self._on_success()
            
            return result
            
        except Exception as e:
            # Record failure
            with self._lock:
                self._on_failure()
            
            # Re-raise the original exception
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try resetting."""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.timeout_seconds
    
    def _time_until_retry(self) -> float:
        """Calculate seconds until next retry attempt."""
        if self.last_failure_time is None:
            return 0.0
        
        elapsed = time.time() - self.last_failure_time
        return max(0.0, self.timeout_seconds - elapsed)
    
    def _on_success(self):
        """Handle successful execution."""
        self.total_successes += 1
        self.last_attempt_time = time.time()
        
        if self.state == "CLOSED":
            # Reset failure count on success
            self.failure_count = 0
            
        elif self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # Enough successes, close the circuit
                self.state = "CLOSED"
                self.failure_count = 0
                self.success_count = 0
    
    def _on_failure(self):
        """Handle failed execution."""
        self.total_failures += 1
        self.last_failure_time = time.time()
        self.last_attempt_time = time.time()
        
        if self.state == "CLOSED":
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                # Too many failures, open the circuit
                self.state = "OPEN"
                self.circuit_opened_count += 1
                
        elif self.state == "HALF_OPEN":
            # Failure in half-open state, reopen immediately
            self.state = "OPEN"
            self.failure_count = self.failure_threshold
    
    def get_state(self) -> str:
        """Get current circuit breaker state."""
        with self._lock:
            return self.state
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "state": self.state,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "total_calls": self.total_calls,
                "total_failures": self.total_failures,
                "total_successes": self.total_successes,
                "circuit_opened_count": self.circuit_opened_count,
                "last_failure_time": datetime.fromtimestamp(self.last_failure_time).isoformat() 
                    if self.last_failure_time else None,
                "time_until_retry": self._time_until_retry() if self.state == "OPEN" else None
            }
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self.state = "CLOSED"
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None 