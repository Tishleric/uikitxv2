"""Tests for RetentionController - orchestration and threading."""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from lib.monitoring.retention.controller import RetentionController


@pytest.fixture
def mock_manager():
    """Create a mock RetentionManager."""
    manager = Mock()
    manager.cleanup_old_records.return_value = (10, 20)  # Default success
    return manager


def test_controller_init(mock_manager):
    """Test RetentionController initialization."""
    controller = RetentionController(
        mock_manager, 
        cleanup_interval=30,
        max_consecutive_errors=3
    )
    
    assert controller.manager == mock_manager
    assert controller.cleanup_interval == 30
    assert controller.max_consecutive_errors == 3
    assert controller.running is False
    assert controller.thread is None
    assert controller.consecutive_errors == 0
    assert controller.total_errors == 0


def test_controller_start_stop(mock_manager):
    """Test starting and stopping controller."""
    controller = RetentionController(mock_manager, cleanup_interval=0.1)
    
    # Start controller
    controller.start()
    assert controller.running is True
    assert controller.thread is not None
    assert controller.thread.is_alive()
    
    # Give it time to run at least once
    time.sleep(0.2)
    
    # Stop controller
    controller.stop(timeout=1.0)
    assert controller.running is False
    assert not controller.thread.is_alive()
    
    # Verify cleanup was called
    assert mock_manager.cleanup_old_records.called


def test_controller_multiple_start(mock_manager):
    """Test calling start multiple times is safe."""
    controller = RetentionController(mock_manager, cleanup_interval=0.1)
    
    controller.start()
    thread1 = controller.thread
    
    # Second start should be no-op
    controller.start()
    thread2 = controller.thread
    
    assert thread1 == thread2  # Same thread
    assert controller.running is True
    
    controller.stop()


def test_controller_cleanup_success(mock_manager):
    """Test successful cleanup cycles."""
    controller = RetentionController(mock_manager, cleanup_interval=0.05)
    
    # Mock returns (process_deleted, data_deleted)
    mock_manager.cleanup_old_records.return_value = (100, 200)
    
    controller.start()
    time.sleep(0.15)  # Allow ~3 cycles
    controller.stop()
    
    # Verify stats
    assert controller.total_cleanups >= 2
    assert controller.total_process_deleted >= 200
    assert controller.total_data_deleted >= 400
    assert controller.consecutive_errors == 0
    assert controller.total_errors == 0
    assert controller.last_cleanup_time is not None


def test_controller_cleanup_errors(mock_manager):
    """Test error handling during cleanup."""
    controller = RetentionController(mock_manager, cleanup_interval=0.05)
    
    # Make cleanup fail
    mock_manager.cleanup_old_records.side_effect = Exception("Test error")
    
    controller.start()
    time.sleep(0.15)  # Allow ~3 cycles
    controller.stop()
    
    # Verify error tracking
    assert controller.total_cleanups == 0
    assert controller.total_errors >= 2
    assert controller.consecutive_errors >= 2
    assert controller.last_error == "Test error"


def test_controller_database_locked_handling(mock_manager):
    """Test handling of database locked errors."""
    import sqlite3
    
    controller = RetentionController(
        mock_manager, 
        cleanup_interval=0.05,
        max_consecutive_errors=2
    )
    
    # Simulate database locked error
    mock_manager.cleanup_old_records.side_effect = sqlite3.OperationalError("database is locked")
    
    with patch('builtins.print') as mock_print:
        controller.start()
        time.sleep(0.2)  # Allow multiple cycles
        controller.stop()
    
    # Should warn after max consecutive errors
    warning_calls = [call for call in mock_print.call_args_list 
                    if "WARNING: Database locked" in str(call)]
    assert len(warning_calls) >= 1


def test_controller_error_recovery(mock_manager):
    """Test recovery after errors."""
    controller = RetentionController(mock_manager, cleanup_interval=0.05)
    
    # Fail first, then succeed
    call_count = 0
    def cleanup_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Temporary error")
        return (50, 100)  # Success
    
    mock_manager.cleanup_old_records.side_effect = cleanup_side_effect
    
    controller.start()
    time.sleep(0.2)  # Allow multiple cycles
    controller.stop()
    
    # Should have some errors then success
    assert controller.total_errors == 2
    assert controller.total_cleanups >= 1
    assert controller.consecutive_errors == 0  # Reset after success


def test_controller_stats(mock_manager):
    """Test controller statistics."""
    controller = RetentionController(mock_manager, cleanup_interval=0.05)
    
    mock_manager.cleanup_old_records.return_value = (25, 50)
    
    controller.start()
    time.sleep(0.15)
    
    stats = controller.get_controller_stats()
    
    assert stats['running'] is True
    assert stats['total_cleanups'] >= 2
    assert stats['total_errors'] == 0
    assert stats['consecutive_errors'] == 0
    assert stats['total_process_deleted'] >= 50
    assert stats['total_data_deleted'] >= 100
    assert stats['cleanup_interval'] == 0.05
    assert stats['thread_alive'] is True
    assert 'estimated_uptime_seconds' in stats
    
    controller.stop()


def test_controller_force_cleanup(mock_manager):
    """Test manual cleanup trigger."""
    controller = RetentionController(mock_manager)
    
    mock_manager.cleanup_old_records.return_value = (75, 150)
    
    # Force cleanup without starting thread
    process_deleted, data_deleted = controller.force_cleanup()
    
    assert process_deleted == 75
    assert data_deleted == 150
    assert mock_manager.cleanup_old_records.called


def test_controller_thread_safety(mock_manager):
    """Test thread safety of controller operations."""
    controller = RetentionController(mock_manager, cleanup_interval=0.01)
    
    # Start controller
    controller.start()
    
    # Concurrent operations
    results = []
    
    def get_stats():
        for _ in range(10):
            stats = controller.get_controller_stats()
            results.append(stats)
            time.sleep(0.01)
    
    # Run stats collection in parallel with cleanup
    stats_thread = threading.Thread(target=get_stats)
    stats_thread.start()
    
    time.sleep(0.15)  # Let cleanup run
    
    controller.stop()
    stats_thread.join()
    
    # All stats calls should succeed
    assert len(results) == 10
    assert all('running' in r for r in results)


def test_controller_graceful_shutdown_timeout(mock_manager):
    """Test graceful shutdown with timeout."""
    controller = RetentionController(mock_manager, cleanup_interval=0.1)
    
    # Make cleanup slow
    def slow_cleanup():
        time.sleep(1.0)  # Longer than stop timeout
        return (0, 0)
    
    mock_manager.cleanup_old_records.side_effect = slow_cleanup
    
    controller.start()
    time.sleep(0.05)  # Let thread start cleanup
    
    # Stop with short timeout
    start_stop = time.time()
    controller.stop(timeout=0.2)
    stop_duration = time.time() - start_stop
    
    # Should timeout, not wait full second
    assert stop_duration < 0.5


def test_controller_exception_resilience(mock_manager):
    """Test controller continues after unexpected exceptions."""
    controller = RetentionController(mock_manager, cleanup_interval=0.05)
    
    # Various error types
    errors = [
        Exception("General error"),
        ValueError("Value error"),
        RuntimeError("Runtime error"),
        (10, 20),  # Success
        Exception("Another error"),
        (5, 10),   # Success
    ]
    
    mock_manager.cleanup_old_records.side_effect = errors
    
    controller.start()
    time.sleep(0.35)  # Allow all cycles
    controller.stop()
    
    # Should handle all errors and continue
    assert controller.total_errors == 4
    assert controller.total_cleanups == 2  # Two successful runs
    assert controller.thread is not None  # Thread didn't die 