"""
Database Bottleneck Test
========================
Focused test to identify if database operations are causing the 14-second delay.
"""

import sqlite3
import time
import threading
import os
from datetime import datetime
from pathlib import Path
import sys
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseBottleneckTest:
    """Test various database scenarios to identify bottlenecks"""
    
    def __init__(self, db_path: str = "trades.db"):
        self.db_path = db_path
        
    def test_single_update(self):
        """Test a single price update operation"""
        logger.info("\n=== Testing Single Update ===")
        
        conn = sqlite3.connect(self.db_path)
        
        # Test connection time
        start = time.perf_counter()
        test_conn = sqlite3.connect(self.db_path)
        conn_time = time.perf_counter() - start
        test_conn.close()
        logger.info(f"Connection time: {conn_time*1000:.1f}ms")
        
        # Test single INSERT OR REPLACE
        symbol = "TEST_SYMBOL_1"
        price = 100.5
        timestamp = datetime.now().isoformat()
        
        start = time.perf_counter()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'now', ?, ?)
        """, (symbol, price, timestamp))
        execute_time = time.perf_counter() - start
        
        start = time.perf_counter()
        conn.commit()
        commit_time = time.perf_counter() - start
        
        conn.close()
        
        logger.info(f"Execute time: {execute_time:.3f}s")
        logger.info(f"Commit time: {commit_time:.3f}s")
        logger.info(f"Total: {execute_time + commit_time:.3f}s")
        
    def test_batch_updates(self, num_symbols: int = 10):
        """Test batch update performance"""
        logger.info(f"\n=== Testing Batch Updates ({num_symbols} symbols) ===")
        
        conn = sqlite3.connect(self.db_path)
        
        # Method 1: Individual commits
        logger.info("\nMethod 1: Individual commits")
        total_time = 0
        for i in range(num_symbols):
            symbol = f"TEST_BATCH_1_{i}"
            price = 100.0 + i
            timestamp = datetime.now().isoformat()
            
            start = time.perf_counter()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, 'now', ?, ?)
            """, (symbol, price, timestamp))
            conn.commit()
            duration = time.perf_counter() - start
            total_time += duration
            
        logger.info(f"Total time: {total_time:.3f}s")
        logger.info(f"Avg per update: {total_time/num_symbols:.3f}s")
        
        # Method 2: Single commit
        logger.info("\nMethod 2: Single commit")
        start = time.perf_counter()
        cursor = conn.cursor()
        for i in range(num_symbols):
            symbol = f"TEST_BATCH_2_{i}"
            price = 100.0 + i
            timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, 'now', ?, ?)
            """, (symbol, price, timestamp))
        
        conn.commit()
        batch_time = time.perf_counter() - start
        
        logger.info(f"Total time: {batch_time:.3f}s")
        logger.info(f"Avg per update: {batch_time/num_symbols:.3f}s")
        logger.info(f"Speedup: {total_time/batch_time:.1f}x")
        
        conn.close()
        
    def test_wal_mode(self):
        """Check if WAL mode is enabled and test its impact"""
        logger.info("\n=== Testing WAL Mode ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check current journal mode
        cursor.execute("PRAGMA journal_mode")
        current_mode = cursor.fetchone()[0]
        logger.info(f"Current journal mode: {current_mode}")
        
        if current_mode != 'wal':
            logger.info("WAL mode is NOT enabled. This can cause lock contention!")
            logger.info("To enable: PRAGMA journal_mode=WAL")
        
        # Check other important settings
        cursor.execute("PRAGMA synchronous")
        sync_mode = cursor.fetchone()[0]
        logger.info(f"Synchronous mode: {sync_mode}")
        
        cursor.execute("PRAGMA busy_timeout")
        timeout = cursor.fetchone()[0]
        logger.info(f"Busy timeout: {timeout}ms")
        
        conn.close()
        
    def test_concurrent_writers(self, num_threads: int = 5):
        """Test concurrent write performance"""
        logger.info(f"\n=== Testing Concurrent Writers ({num_threads} threads) ===")
        
        results = {}
        lock_counts = {}
        
        def writer_thread(thread_id: int):
            times = []
            locks = 0
            
            for i in range(10):
                symbol = f"CONCURRENT_{thread_id}_{i}"
                price = 100.0 + i
                timestamp = datetime.now().isoformat()
                
                start = time.perf_counter()
                retry_count = 0
                while retry_count < 10:
                    try:
                        conn = sqlite3.connect(self.db_path, timeout=5.0)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                            VALUES (?, 'now', ?, ?)
                        """, (symbol, price, timestamp))
                        conn.commit()
                        conn.close()
                        break
                    except sqlite3.OperationalError as e:
                        if "database is locked" in str(e):
                            locks += 1
                            retry_count += 1
                            time.sleep(0.1)
                        else:
                            raise
                
                duration = time.perf_counter() - start
                times.append(duration)
            
            results[thread_id] = times
            lock_counts[thread_id] = locks
        
        # Run threads
        threads = []
        start_time = time.perf_counter()
        
        for i in range(num_threads):
            t = threading.Thread(target=writer_thread, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        total_time = time.perf_counter() - start_time
        
        # Analyze results
        all_times = []
        for thread_times in results.values():
            all_times.extend(thread_times)
        
        total_locks = sum(lock_counts.values())
        
        logger.info(f"Total time: {total_time:.3f}s")
        logger.info(f"Total operations: {len(all_times)}")
        logger.info(f"Operations/sec: {len(all_times)/total_time:.1f}")
        logger.info(f"Avg operation time: {sum(all_times)/len(all_times):.3f}s")
        logger.info(f"Max operation time: {max(all_times):.3f}s")
        logger.info(f"Database locks encountered: {total_locks}")
        
    def test_file_system_performance(self):
        """Test if file system is causing delays"""
        logger.info("\n=== Testing File System Performance ===")
        
        # Get database file stats
        db_stat = os.stat(self.db_path)
        logger.info(f"Database size: {db_stat.st_size / (1024*1024):.1f} MB")
        
        # Check if database is on SSD or HDD
        # This is platform-specific, simplified test
        test_file = self.db_path + ".test"
        data = b"x" * 1024 * 1024  # 1MB
        
        # Write test
        start = time.perf_counter()
        with open(test_file, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        write_time = time.perf_counter() - start
        
        # Read test
        start = time.perf_counter()
        with open(test_file, 'rb') as f:
            _ = f.read()
        read_time = time.perf_counter() - start
        
        os.unlink(test_file)
        
        write_speed = 1.0 / write_time  # MB/s
        read_speed = 1.0 / read_time    # MB/s
        
        logger.info(f"Write speed: {write_speed:.1f} MB/s")
        logger.info(f"Read speed: {read_speed:.1f} MB/s")
        
        if write_speed < 50:  # Less than 50 MB/s suggests HDD
            logger.warning("Slow write speed detected! Database may be on HDD.")
        
    def suggest_optimizations(self):
        """Suggest optimizations based on test results"""
        logger.info("\n=== Optimization Suggestions ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check journal mode
        cursor.execute("PRAGMA journal_mode")
        if cursor.fetchone()[0] != 'wal':
            logger.info("1. Enable WAL mode: PRAGMA journal_mode=WAL")
            logger.info("   This allows concurrent readers while writing")
        
        # Check synchronous mode
        cursor.execute("PRAGMA synchronous")
        sync = cursor.fetchone()[0]
        if sync == 2:  # FULL
            logger.info("2. Consider PRAGMA synchronous=NORMAL for better performance")
            logger.info("   (slightly less safe but much faster)")
        
        # Check page size
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        if page_size < 4096:
            logger.info(f"3. Increase page size from {page_size} to 4096 or 8192")
        
        logger.info("\n4. Use batch commits instead of individual commits")
        logger.info("5. Consider using INSERT OR IGNORE + UPDATE instead of INSERT OR REPLACE")
        logger.info("6. Add connection pooling to avoid connection overhead")
        
        conn.close()


def main():
    """Run all database bottleneck tests"""
    tester = DatabaseBottleneckTest()
    
    # Run all tests
    tester.test_single_update()
    tester.test_batch_updates(num_symbols=10)
    tester.test_wal_mode()
    tester.test_concurrent_writers(num_threads=3)
    tester.test_file_system_performance()
    tester.suggest_optimizations()
    
    logger.info("\n=== Database Bottleneck Test Complete ===")


if __name__ == "__main__":
    main()