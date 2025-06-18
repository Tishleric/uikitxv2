"""Tests for ObservatoryQueue - Phase 4"""

import pytest
import threading
import time
from datetime import datetime
from lib.monitoring.queues import ObservatoryQueue, ObservatoryRecord, QueueMetrics


class TestObservatoryQueue:
    """Test suite for ObservatoryQueue with error-first strategy"""
    
    def create_record(self, status="OK", process="test.function", duration_ms=10.5):
        """Helper to create test records"""
        return ObservatoryRecord(
            ts=datetime.now().isoformat(),
            process=process,
            status=status,
            duration_ms=duration_ms,
            exception="Test error" if status == "ERR" else None
        )
    
    def test_basic_put_and_drain(self):
        """Test basic enqueue and dequeue operations"""
        queue = ObservatoryQueue()
        
        # Add some records
        queue.put(self.create_record("OK"))
        queue.put(self.create_record("ERR"))
        queue.put(self.create_record("OK"))
        
        # Drain and verify
        batch = queue.drain()
        assert len(batch) == 3
        
        # Verify error-first ordering
        assert batch[0].status == "ERR"
        assert batch[1].status == "OK"
        assert batch[2].status == "OK"
    
    def test_errors_never_dropped(self):
        """Test that error records are never dropped even under load"""
        queue = ObservatoryQueue(normal_maxsize=10, overflow_maxsize=5)
        
        # Fill normal queue and overflow
        for i in range(20):
            queue.put(self.create_record("OK", f"test.func{i}"))
        
        # Add many error records
        error_count = 100
        for i in range(error_count):
            queue.put(self.create_record("ERR", f"test.error{i}"))
        
        # Verify metrics
        metrics = queue.metrics
        assert metrics.error_enqueued == error_count
        assert metrics.error_dropped == 0  # Must always be 0
        
        # Drain all and count errors
        all_records = []
        while True:
            batch = queue.drain(max_items=50)
            if not batch:
                break
            all_records.extend(batch)
        
        error_records = [r for r in all_records if r.status == "ERR"]
        assert len(error_records) == error_count
    
    def test_normal_overflow_to_buffer(self):
        """Test normal records overflow to ring buffer when queue is full"""
        queue = ObservatoryQueue(normal_maxsize=5, overflow_maxsize=10)
        
        # Fill normal queue
        for i in range(5):
            queue.put(self.create_record("OK", f"normal{i}"))
        
        assert queue.metrics.normal_enqueued == 5
        assert queue.metrics.overflowed == 0
        
        # Add more - should go to overflow
        for i in range(5, 10):
            queue.put(self.create_record("OK", f"overflow{i}"))
        
        assert queue.metrics.overflowed == 5
        stats = queue.get_queue_stats()
        assert stats['overflow_buffer_size'] == 5
    
    def test_overflow_recovery(self):
        """Test recovery from overflow buffer back to normal queue"""
        queue = ObservatoryQueue(normal_maxsize=3, overflow_maxsize=5)
        
        # Fill normal queue and overflow
        for i in range(7):
            queue.put(self.create_record("OK", f"record{i}"))
        
        assert queue.metrics.overflowed == 4
        
        # Drain some records
        batch1 = queue.drain(max_items=2)
        assert len(batch1) == 2
        
        # Check recovery happened
        assert queue.metrics.recovered > 0
        initial_recovered = queue.metrics.recovered
        
        # Drain more and verify more recovery
        batch2 = queue.drain(max_items=2)
        assert queue.metrics.recovered >= initial_recovered
    
    def test_ring_buffer_overflow(self):
        """Test ring buffer behavior when it reaches capacity"""
        queue = ObservatoryQueue(normal_maxsize=2, overflow_maxsize=3)
        
        # Fill everything
        for i in range(10):
            queue.put(self.create_record("OK", f"record{i}"))
        
        # Ring buffer should only have last 3 items
        stats = queue.get_queue_stats()
        assert stats['overflow_buffer_size'] == 3
        
        # Drain all
        all_records = []
        while True:
            batch = queue.drain()
            if not batch:
                break
            all_records.extend(batch)
        
        # Should get normal queue (2) + overflow buffer (3) = 5 total
        assert len(all_records) == 5
    
    def test_drain_priority_order(self):
        """Test drain respects error-first priority"""
        queue = ObservatoryQueue()
        
        # Add mixed records
        queue.put(self.create_record("OK", "first"))
        queue.put(self.create_record("OK", "second"))
        queue.put(self.create_record("ERR", "error1"))
        queue.put(self.create_record("OK", "third"))
        queue.put(self.create_record("ERR", "error2"))
        
        # Drain with small batch size
        batch = queue.drain(max_items=3)
        
        # Should get both errors first
        assert len(batch) == 3
        assert batch[0].process == "error1"
        assert batch[1].process == "error2"
        assert batch[2].process == "first"
    
    def test_metrics_accuracy(self):
        """Test all metrics are tracked accurately"""
        queue = ObservatoryQueue(normal_maxsize=5, overflow_maxsize=5)
        
        # Initial state
        assert queue.metrics.normal_enqueued == 0
        assert queue.metrics.error_enqueued == 0
        assert queue.metrics.batch_count == 0
        
        # Add records
        for i in range(3):
            queue.put(self.create_record("OK"))
        for i in range(2):
            queue.put(self.create_record("ERR"))
        
        assert queue.metrics.normal_enqueued == 3
        assert queue.metrics.error_enqueued == 2
        
        # Drain
        batch = queue.drain()
        assert queue.metrics.batch_count == 1
        assert queue.metrics.last_drain_time is not None
        
        # Test overflow
        for i in range(10):
            queue.put(self.create_record("OK"))
        
        assert queue.metrics.overflowed > 0
        
        # Clear and verify reset
        queue.clear()
        assert queue.metrics.normal_enqueued == 0
        assert queue.metrics.error_enqueued == 0
    
    def test_thread_safety(self):
        """Test queue operations are thread-safe"""
        queue = ObservatoryQueue(normal_maxsize=100)
        errors = []
        
        def producer(thread_id, count):
            try:
                for i in range(count):
                    status = "ERR" if i % 10 == 0 else "OK"
                    queue.put(self.create_record(status, f"thread{thread_id}.func{i}"))
            except Exception as e:
                errors.append(e)
        
        # Start multiple producer threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=producer, args=(i, 20))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0
        
        # Verify total records
        total_records = queue.metrics.normal_enqueued + queue.metrics.error_enqueued
        assert total_records == 100
    
    def test_queue_stats(self):
        """Test queue statistics reporting"""
        queue = ObservatoryQueue(normal_maxsize=10, overflow_maxsize=20)
        
        # Check initial stats
        stats = queue.get_queue_stats()
        assert stats['error_queue_size'] == 0
        assert stats['normal_queue_size'] == 0
        assert stats['overflow_buffer_size'] == 0
        assert stats['is_normal_full'] is False
        assert stats['has_overflow'] is False
        
        # Fill queues
        for i in range(15):
            queue.put(self.create_record("OK"))
        queue.put(self.create_record("ERR"))
        
        stats = queue.get_queue_stats()
        assert stats['error_queue_size'] == 1
        assert stats['normal_queue_size'] == 10
        assert stats['overflow_buffer_size'] == 5
        assert stats['is_normal_full'] is True
        assert stats['has_overflow'] is True
        
        # Check metrics in stats
        assert 'metrics' in stats
        assert stats['metrics']['queue_health'] == 'healthy'
    
    def test_clear_functionality(self):
        """Test clearing all queues and metrics"""
        queue = ObservatoryQueue()
        
        # Add various records
        for i in range(5):
            queue.put(self.create_record("OK"))
            queue.put(self.create_record("ERR"))
        
        # Verify they're there
        stats = queue.get_queue_stats()
        assert stats['error_queue_size'] > 0
        assert stats['normal_queue_size'] > 0
        
        # Clear
        queue.clear()
        
        # Verify everything is cleared
        stats = queue.get_queue_stats()
        assert stats['error_queue_size'] == 0
        assert stats['normal_queue_size'] == 0
        assert stats['overflow_buffer_size'] == 0
        assert queue.metrics.normal_enqueued == 0
        assert queue.metrics.error_enqueued == 0
    
    def test_warning_thresholds(self):
        """Test warning thresholds are properly tracked"""
        queue = ObservatoryQueue(
            normal_maxsize=10, 
            overflow_maxsize=5,
            warning_threshold=8
        )
        
        # Fill to just before warning threshold
        for i in range(7):
            queue.put(self.create_record("OK"))
        
        # Should not trigger warning yet
        assert queue.normal_queue.qsize() < queue.warning_threshold
        
        # Fill past warning threshold
        for i in range(2):
            queue.put(self.create_record("OK"))
        
        # Should be past warning threshold
        assert queue.normal_queue.qsize() > queue.warning_threshold
        
        # Fill to overflow
        for i in range(5):
            queue.put(self.create_record("OK"))
        
        # Should have overflow
        stats = queue.get_queue_stats()
        assert stats['has_overflow'] is True
        assert stats['overflow_buffer_size'] > 0
        
        # Verify warning interval works (should not warn again within 60s)
        initial_warning_time = queue._last_warning_time
        queue.put(self.create_record("OK"))  # Another overflow
        # Warning time should not change (rate limited)
        assert queue._last_warning_time == initial_warning_time
    
    def test_load_handling(self):
        """Test queue handles high load gracefully"""
        queue = ObservatoryQueue(normal_maxsize=1000, overflow_maxsize=5000)
        
        # Simulate burst load
        start_time = time.time()
        record_count = 10000
        
        for i in range(record_count):
            status = "ERR" if i % 100 == 0 else "OK"
            queue.put(self.create_record(status, f"load.test{i}"))
        
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 1.0  # Less than 1 second for 10k records
        
        # Verify no data loss within capacity limits
        stats = queue.get_queue_stats()
        
        # We have 100 errors (i % 100 == 0) and 9900 normal records
        # Error queue is unlimited, so all 100 errors are stored
        # Normal queue holds 1000, overflow buffer holds 5000
        # So we can store: 100 errors + min(9900, 1000 + 5000) normal = 100 + 6000 = 6100
        total_stored = (stats['error_queue_size'] + 
                       stats['normal_queue_size'] + 
                       stats['overflow_buffer_size'])
        
        expected_errors = 100  # All errors stored (unlimited queue)
        expected_normal = min(9900, 1000 + 5000)  # Limited by queue + buffer capacity
        expected_total = expected_errors + expected_normal
        
        assert total_stored == expected_total
        assert queue.metrics.error_dropped == 0  # Critical: no errors dropped 