"""Integration tests for circuit breaker with observability system."""

import pytest
import tempfile
import sqlite3
import os
import time
from unittest.mock import patch

from lib.monitoring.decorators.monitor import (
    monitor, start_observability_writer, stop_observability_writer
)
from lib.monitoring.circuit_breaker import CircuitBreakerError


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with observability."""
    
    def setup_method(self):
        """Clean up before each test."""
        stop_observability_writer()
    
    def teardown_method(self):
        """Clean up after each test."""
        stop_observability_writer()
    
    def test_circuit_breaker_protects_sqlite_writer(self):
        """Test that circuit breaker protects against database failures."""
        # Create a read-only database to simulate write failures
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Start observability
            start_observability_writer(
                db_path=db_path,
                batch_size=5,
                drain_interval=0.05
            )
            
            # Make database read-only to simulate failures
            os.chmod(db_path, 0o444)
            
            @monitor()
            def test_function(x):
                return x * 2
            
            # Generate some records - these should fail to write
            for i in range(20):
                test_function(i)
            
            # Give writer time to process
            time.sleep(0.5)
            
            # Get writer stats
            from lib.monitoring.decorators.monitor import _batch_writer
            if _batch_writer:
                stats = _batch_writer.get_stats()
                
                # Circuit breaker should have opened
                cb_stats = stats.get('circuit_breaker', {})
                assert cb_stats.get('state') in ['OPEN', 'HALF_OPEN']
                assert cb_stats.get('total_failures') >= 3
                assert cb_stats.get('circuit_opened_count') >= 1
                
                # But the system should still be running
                assert _batch_writer.is_alive()
            
        finally:
            # Clean up
            stop_observability_writer()
            try:
                os.chmod(db_path, 0o666)  # Make writable again
                os.unlink(db_path)
            except:
                pass
    
    def test_circuit_breaker_recovery(self):
        """Test that circuit breaker recovers when database becomes available."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Start observability with short timeout for faster test
            from lib.monitoring.writers.sqlite_writer import BatchWriter
            from lib.monitoring.decorators.monitor import get_observability_queue
            
            queue = get_observability_queue()
            writer = BatchWriter(
                db_path=db_path,
                queue=queue,
                batch_size=5,
                drain_interval=0.05
            )
            
            # Configure circuit breaker for faster recovery
            writer.circuit_breaker.timeout_seconds = 0.5
            writer.start()
            
            @monitor()
            def test_function(x):
                return x * 2
            
            # Phase 1: Generate successful writes
            for i in range(5):
                test_function(i)
            time.sleep(0.2)
            
            initial_written = writer.total_written
            assert initial_written > 0
            
            # Phase 2: Make database read-only to trigger failures
            os.chmod(db_path, 0o444)
            
            for i in range(10):
                test_function(i + 100)
            time.sleep(0.2)
            
            # Check circuit opened
            assert writer.circuit_breaker.get_state() == "OPEN"
            
            # Phase 3: Fix database and wait for recovery
            os.chmod(db_path, 0o666)
            time.sleep(0.6)  # Wait for timeout
            
            # Generate more records
            for i in range(5):
                test_function(i + 200)
            time.sleep(0.3)
            
            # Circuit should have recovered
            final_stats = writer.circuit_breaker.get_stats()
            assert final_stats['state'] in ['CLOSED', 'HALF_OPEN']
            assert writer.total_written > initial_written
            
            # Stop writer
            writer.stop()
            
        finally:
            # Clean up
            try:
                os.chmod(db_path, 0o666)
                os.unlink(db_path)
            except:
                pass
    
    def test_circuit_breaker_statistics_in_dashboard(self):
        """Test that circuit breaker stats are available for monitoring."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            start_observability_writer(db_path=db_path)
            
            @monitor()
            def test_function():
                return "test"
            
            # Generate some activity
            for _ in range(5):
                test_function()
            
            time.sleep(0.2)
            
            # Get stats through public API
            from lib.monitoring.decorators.monitor import _batch_writer
            if _batch_writer:
                stats = _batch_writer.get_stats()
                
                # Verify circuit breaker stats are included
                assert 'circuit_breaker' in stats
                cb_stats = stats['circuit_breaker']
                
                assert 'state' in cb_stats
                assert 'total_calls' in cb_stats
                assert 'total_successes' in cb_stats
                assert 'total_failures' in cb_stats
                assert 'circuit_opened_count' in cb_stats
                
                # Should be healthy
                assert cb_stats['state'] == 'CLOSED'
                assert cb_stats['total_calls'] > 0
                
        finally:
            stop_observability_writer()
            try:
                os.unlink(db_path)
            except:
                pass
    
    def test_no_data_loss_with_circuit_breaker(self):
        """Verify that circuit breaker doesn't cause data loss when queue is used."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Start with small queue to test overflow handling
            start_observability_writer(
                db_path=db_path,
                batch_size=5,
                drain_interval=0.05
            )
            
            @monitor()
            def tracked_function(n):
                return n ** 2
            
            # Generate records
            expected_results = []
            for i in range(10):
                result = tracked_function(i)
                expected_results.append(result)
            
            # Wait for writes
            time.sleep(0.5)
            
            # Verify all records were written
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM process_trace WHERE process LIKE '%tracked_function%'")
            count = cursor.fetchone()[0]
            assert count == 10
            
            # Verify results were captured
            cursor.execute("""
                SELECT data_value FROM data_trace 
                WHERE process LIKE '%tracked_function%' 
                AND data = 'result'
                ORDER BY ts
            """)
            
            results = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Should have all results
            assert len(results) == 10
            
        finally:
            stop_observability_writer()
            try:
                os.unlink(db_path)
            except:
                pass 