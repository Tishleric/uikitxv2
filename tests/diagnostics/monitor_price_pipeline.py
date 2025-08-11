"""
Real-time Pipeline Monitor
=========================
Monitors the spot risk -> price updater pipeline in real-time without interference.
"""

import time
import redis
import pickle
import threading
import queue
from datetime import datetime
from collections import deque, defaultdict
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineMonitor:
    """Monitors messages flowing through Redis pub/sub"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)
        self.channel = "spot_risk:results_channel"
        
        # Metrics storage
        self.latencies = deque(maxlen=100)  # Keep last 100 latencies
        self.message_sizes = deque(maxlen=100)
        self.symbols_per_message = deque(maxlen=100)
        self.message_timestamps = defaultdict(float)
        
        # Threading
        self.monitoring = False
        self.stats_queue = queue.Queue()
        
    def monitor_channel(self):
        """Monitor Redis channel for messages"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channel)
        
        logger.info(f"Monitoring {self.channel}...")
        
        message_count = 0
        last_report_time = time.time()
        
        for message in pubsub.listen():
            if not self.monitoring:
                break
                
            if message['type'] != 'message':
                continue
            
            message_count += 1
            receive_time = time.time()
            
            try:
                # Measure deserialization time
                deser_start = time.perf_counter()
                payload = pickle.loads(message['data'])
                deser_time = time.perf_counter() - deser_start
                
                # Calculate latency
                publish_time = payload.get('publish_timestamp', receive_time)
                latency = receive_time - publish_time
                
                # Measure payload size
                payload_size = len(message['data']) / 1024  # KB
                
                # Store metrics
                self.latencies.append(latency)
                self.message_sizes.append(payload_size)
                
                # Log individual message
                batch_id = payload.get('batch_id', 'unknown')
                logger.info(f"Message {message_count} - Batch: {batch_id}, "
                           f"Latency: {latency:.3f}s, Size: {payload_size:.1f}KB, "
                           f"Deser: {deser_time*1000:.1f}ms")
                
                # Store timestamp for rate calculation
                self.message_timestamps[batch_id] = receive_time
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
            
            # Report statistics every 10 messages
            if message_count % 10 == 0:
                self._report_statistics(message_count, receive_time - last_report_time)
                last_report_time = receive_time
    
    def _report_statistics(self, total_messages: int, time_window: float):
        """Report current statistics"""
        if not self.latencies:
            return
        
        avg_latency = statistics.mean(self.latencies)
        max_latency = max(self.latencies)
        min_latency = min(self.latencies)
        
        avg_size = statistics.mean(self.message_sizes) if self.message_sizes else 0
        
        rate = 10 / time_window if time_window > 0 else 0
        
        logger.info(f"""
================== STATISTICS (Last 10 messages) ==================
Total Messages: {total_messages}
Message Rate: {rate:.2f} msg/sec
Latency - Avg: {avg_latency:.3f}s, Max: {max_latency:.3f}s, Min: {min_latency:.3f}s
Payload Size - Avg: {avg_size:.1f}KB
===================================================================
""")
    
    def check_queue_depth(self):
        """Check if messages are queuing up"""
        # Try to get Redis info about pub/sub
        info = self.redis_client.execute_command('PUBSUB', 'NUMSUB', self.channel)
        if info:
            logger.info(f"Channel {self.channel} has {info[1]} subscribers")
    
    def start(self):
        """Start monitoring"""
        self.monitoring = True
        
        # Check initial state
        self.check_queue_depth()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_channel)
        monitor_thread.start()
        
        return monitor_thread
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False


class DatabaseMonitor:
    """Monitor database activity"""
    
    def __init__(self, db_path: str = "trades.db"):
        self.db_path = db_path
        
    def monitor_locks(self, duration: int = 60):
        """Monitor database locks for specified duration"""
        import sqlite3
        import os
        
        logger.info(f"Monitoring database locks for {duration} seconds...")
        
        start_time = time.time()
        lock_events = []
        
        while time.time() - start_time < duration:
            try:
                # Try to get exclusive lock
                conn = sqlite3.connect(self.db_path, timeout=0.1)
                conn.execute("BEGIN EXCLUSIVE")
                conn.rollback()
                conn.close()
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    lock_events.append(time.time())
                    logger.warning(f"Database locked at {datetime.now()}")
            
            time.sleep(0.1)
        
        if lock_events:
            logger.info(f"Database was locked {len(lock_events)} times in {duration} seconds")
        else:
            logger.info(f"No database locks detected in {duration} seconds")


def main():
    """Run the monitoring tool"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor price updater pipeline')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Monitoring duration in seconds (default: 300)')
    parser.add_argument('--db-monitor', action='store_true',
                       help='Also monitor database locks')
    
    args = parser.parse_args()
    
    # Start pipeline monitor
    pipeline_monitor = PipelineMonitor()
    monitor_thread = pipeline_monitor.start()
    
    # Optionally start database monitor
    if args.db_monitor:
        db_monitor = DatabaseMonitor()
        db_thread = threading.Thread(
            target=db_monitor.monitor_locks, 
            args=(args.duration,)
        )
        db_thread.start()
    
    try:
        # Run for specified duration
        logger.info(f"Monitoring for {args.duration} seconds. Press Ctrl+C to stop early.")
        time.sleep(args.duration)
        
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    
    finally:
        # Stop monitoring
        pipeline_monitor.stop()
        monitor_thread.join()
        
        if args.db_monitor and 'db_thread' in locals():
            db_thread.join()
        
        # Final statistics
        if pipeline_monitor.latencies:
            logger.info(f"""
==================== FINAL SUMMARY ====================
Total messages observed: {len(pipeline_monitor.message_timestamps)}
Average latency: {statistics.mean(pipeline_monitor.latencies):.3f}s
Max latency: {max(pipeline_monitor.latencies):.3f}s
Percentiles:
  50th: {statistics.quantiles(pipeline_monitor.latencies, n=4)[1]:.3f}s
  90th: {statistics.quantiles(pipeline_monitor.latencies, n=10)[8]:.3f}s
  99th: {statistics.quantiles(pipeline_monitor.latencies, n=100)[98]:.3f}s
======================================================
""")


if __name__ == "__main__":
    main()