"""Tests for circuit breaker implementation."""

import pytest
import time
from unittest.mock import Mock

from lib.monitoring.circuit_breaker import CircuitBreaker, CircuitBreakerError


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_init(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(
            failure_threshold=3,
            timeout_seconds=10,
            success_threshold=2
        )
        
        assert cb.failure_threshold == 3
        assert cb.timeout_seconds == 10
        assert cb.success_threshold == 2
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.success_count == 0
    
    def test_successful_calls(self):
        """Test circuit breaker with successful calls."""
        cb = CircuitBreaker()
        
        def success_func(x):
            return x * 2
        
        # Multiple successful calls
        for i in range(10):
            result = cb.call(success_func, i)
            assert result == i * 2
        
        # Circuit should remain closed
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.total_successes == 10
        assert cb.total_failures == 0
    
    def test_circuit_opens_on_failures(self):
        """Test circuit opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise RuntimeError("Test failure")
        
        # First 3 failures should pass through
        for i in range(3):
            with pytest.raises(RuntimeError):
                cb.call(failing_func)
        
        # Circuit should now be open
        assert cb.state == "OPEN"
        assert cb.failure_count == 3
        assert cb.circuit_opened_count == 1
        
        # Next call should fail immediately without calling function
        with pytest.raises(CircuitBreakerError) as exc_info:
            cb.call(failing_func)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
        assert "Next retry in" in str(exc_info.value)
    
    def test_circuit_half_open_transition(self):
        """Test circuit transitions to half-open after timeout."""
        cb = CircuitBreaker(
            failure_threshold=1,
            timeout_seconds=0.1,  # 100ms for fast test
            success_threshold=2
        )
        
        def sometimes_failing(should_fail):
            if should_fail:
                raise RuntimeError("Test failure")
            return "success"
        
        # Open the circuit
        with pytest.raises(RuntimeError):
            cb.call(sometimes_failing, True)
        
        assert cb.state == "OPEN"
        
        # Try immediately - should fail
        with pytest.raises(CircuitBreakerError):
            cb.call(sometimes_failing, False)
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Next call should go through (half-open)
        result = cb.call(sometimes_failing, False)
        assert result == "success"
        assert cb.state == "HALF_OPEN"
        assert cb.success_count == 1
        
        # One more success should close the circuit
        result = cb.call(sometimes_failing, False)
        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_half_open_fails_reopens(self):
        """Test failure in half-open state reopens circuit."""
        cb = CircuitBreaker(
            failure_threshold=1,
            timeout_seconds=0.1
        )
        
        def failing_func():
            raise RuntimeError("Test failure")
        
        # Open the circuit
        with pytest.raises(RuntimeError):
            cb.call(failing_func)
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Try again - should fail and reopen
        with pytest.raises(RuntimeError):
            cb.call(failing_func)
        
        assert cb.state == "OPEN"
        assert cb.failure_count == 1  # Reset to threshold
    
    def test_statistics(self):
        """Test circuit breaker statistics."""
        cb = CircuitBreaker(failure_threshold=2)
        
        def mixed_func(should_fail):
            if should_fail:
                raise RuntimeError("Test failure")
            return "success"
        
        # Some successes
        cb.call(mixed_func, False)
        cb.call(mixed_func, False)
        
        # Some failures
        with pytest.raises(RuntimeError):
            cb.call(mixed_func, True)
        
        stats = cb.get_stats()
        assert stats['state'] == "CLOSED"
        assert stats['total_calls'] == 3
        assert stats['total_successes'] == 2
        assert stats['total_failures'] == 1
        assert stats['failure_count'] == 1
        assert stats['circuit_opened_count'] == 0
    
    def test_manual_reset(self):
        """Test manual circuit reset."""
        cb = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise RuntimeError("Test failure")
        
        # Open the circuit
        with pytest.raises(RuntimeError):
            cb.call(failing_func)
        
        assert cb.state == "OPEN"
        
        # Manual reset
        cb.reset()
        
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None
    
    def test_thread_safety(self):
        """Test circuit breaker is thread-safe."""
        import threading
        
        cb = CircuitBreaker(failure_threshold=10)
        results = []
        errors = []
        
        def worker(thread_id, should_fail):
            try:
                result = cb.call(lambda: 1/0 if should_fail else thread_id)
                results.append(result)
            except Exception as e:
                errors.append(type(e).__name__)
        
        # Launch multiple threads
        threads = []
        for i in range(20):
            t = threading.Thread(target=worker, args=(i, i % 3 == 0))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify thread safety
        assert len(results) + len(errors) == 20
        assert cb.total_calls == 20
    
    def test_with_mock_function(self):
        """Test circuit breaker with mock objects."""
        cb = CircuitBreaker(failure_threshold=2)
        mock_func = Mock()
        
        # Successful calls
        mock_func.return_value = "success"
        result = cb.call(mock_func, "arg1", key="value")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")
        
        # Failing calls
        mock_func.side_effect = Exception("Mock failure")
        
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(mock_func)
        
        # Circuit should be open
        assert cb.state == "OPEN"
        
        # Reset mock call count
        mock_func.reset_mock()
        
        # Next call shouldn't reach the function
        with pytest.raises(CircuitBreakerError):
            cb.call(mock_func)
        
        # Mock should not have been called
        mock_func.assert_not_called()
    
    def test_time_until_retry(self):
        """Test time calculation for retry."""
        cb = CircuitBreaker(
            failure_threshold=1,
            timeout_seconds=5.0
        )
        
        def failing_func():
            raise RuntimeError("Test")
        
        # Open circuit
        with pytest.raises(RuntimeError):
            cb.call(failing_func)
        
        # Check time until retry
        stats = cb.get_stats()
        assert stats['state'] == "OPEN"
        assert 4.0 <= stats['time_until_retry'] <= 5.0
        
        # Wait a bit
        time.sleep(1)
        
        stats = cb.get_stats()
        assert 3.0 <= stats['time_until_retry'] <= 4.0 