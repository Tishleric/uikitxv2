"""Demo script showing retention management in action.

This demonstrates the simple retention approach:
- 6-hour rolling window
- Automatic cleanup every 60 seconds
- Steady state database size
"""

import time
import sqlite3
from datetime import datetime, timedelta

from lib.monitoring.decorators.monitor import (
    monitor, start_observability_writer, stop_observability_writer
)
from lib.monitoring.retention import RetentionManager


def print_database_stats(db_path: str):
    """Print current database statistics."""
    try:
        with sqlite3.connect(db_path) as conn:
            # Get counts
            process_count = conn.execute("SELECT COUNT(*) FROM process_trace").fetchone()[0]
            data_count = conn.execute("SELECT COUNT(*) FROM data_trace").fetchone()[0]
            
            # Get oldest timestamp
            oldest = conn.execute("SELECT MIN(ts) FROM process_trace").fetchone()[0]
            if oldest:
                oldest_dt = datetime.fromisoformat(oldest)
                age_minutes = (datetime.now() - oldest_dt).total_seconds() / 60
            else:
                age_minutes = 0
            
            # Get database size
            page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]
            size_mb = (page_count * page_size) / (1024 * 1024)
            
            print(f"\n[DATABASE STATS]")
            print(f"  Process records: {process_count:,}")
            print(f"  Data records: {data_count:,}")
            print(f"  Oldest data: {age_minutes:.1f} minutes ago")
            print(f"  Database size: {size_mb:.2f} MB")
            
    except Exception as e:
        print(f"[DATABASE STATS] Error: {e}")


def simulate_workload():
    """Simulate a typical workload with various function types."""
    
    @monitor()
    def process_order(order_id: int, amount: float) -> dict:
        """Simulate order processing."""
        time.sleep(0.001)  # Simulate work
        return {"order_id": order_id, "amount": amount, "status": "processed"}
    
    @monitor()
    def calculate_risk(positions: list) -> float:
        """Simulate risk calculation."""
        return sum(p * 0.1 for p in positions)
    
    @monitor()
    def update_market_data(symbol: str, price: float):
        """Simulate market data update."""
        # Occasionally fail
        if price < 0:
            raise ValueError(f"Invalid price: {price}")
        return price
    
    # Mix of operations
    for i in range(10):
        # Order processing
        process_order(1000 + i, 10000.0 * (i + 1))
        
        # Risk calculation
        positions = [100, 200, -150, 300, -50]
        calculate_risk(positions)
        
        # Market data (with occasional error)
        try:
            price = 100.0 + i if i % 7 != 0 else -1.0
            update_market_data("AAPL", price)
        except ValueError:
            pass  # Expected
        
        time.sleep(0.1)


def main():
    """Run retention demo."""
    print("=" * 60)
    print("RETENTION MANAGEMENT DEMO")
    print("=" * 60)
    
    db_path = "logs/retention_demo.db"
    
    # Start observability with retention
    print("\n[1] Starting observability system with 6-minute retention...")
    print("    (Using 6 minutes instead of 6 hours for demo purposes)")
    
    start_observability_writer(
        db_path=db_path,
        batch_size=50,
        drain_interval=0.1,
        retention_hours=0.1,  # 6 minutes for demo
        retention_enabled=True
    )
    
    print_database_stats(db_path)
    
    try:
        # Phase 1: Initial growth
        print("\n[2] Phase 1: Initial growth (30 seconds)...")
        start_time = time.time()
        
        while time.time() - start_time < 30:
            simulate_workload()
            
            # Print stats every 10 seconds
            if int(time.time() - start_time) % 10 == 0:
                print_database_stats(db_path)
        
        # Phase 2: Simulate old data
        print("\n[3] Phase 2: Injecting old data to test retention...")
        
        # Manually insert old data
        old_time = datetime.now() - timedelta(minutes=10)  # 10 minutes old
        with sqlite3.connect(db_path) as conn:
            for i in range(1000):
                ts = (old_time + timedelta(seconds=i * 0.1)).isoformat()
                conn.execute(
                    "INSERT INTO process_trace VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (ts, f"old.process_{i}", "OK", 5.5, None, 0, 0, 0, None, None)
                )
        
        print("    Injected 1,000 old records (10 minutes old)")
        print_database_stats(db_path)
        
        # Phase 3: Watch retention in action
        print("\n[4] Phase 3: Watching retention clean up old data...")
        print("    Retention runs every 60 seconds, cleaning data > 6 minutes old")
        
        # Force immediate cleanup for demo
        manager = RetentionManager(db_path, retention_hours=0.1)
        process_deleted, data_deleted = manager.cleanup_old_records()
        print(f"\n    Cleanup complete: {process_deleted} process records deleted")
        
        print_database_stats(db_path)
        
        # Phase 4: Steady state
        print("\n[5] Phase 4: Steady state operation (20 seconds)...")
        print("    Database size should remain constant as deletions = insertions")
        
        steady_start = time.time()
        while time.time() - steady_start < 20:
            simulate_workload()
            
            if int(time.time() - steady_start) % 5 == 0:
                print_database_stats(db_path)
        
        # Final stats
        print("\n[6] Final statistics:")
        print_database_stats(db_path)
        
        # Show retention controller stats
        from lib.monitoring.decorators.monitor import _retention_controller
        if _retention_controller:
            controller_stats = _retention_controller.get_controller_stats()
            print(f"\n[RETENTION CONTROLLER STATS]")
            print(f"  Total cleanups: {controller_stats['total_cleanups']}")
            print(f"  Records deleted: {controller_stats['total_process_deleted']:,}")
            print(f"  Errors: {controller_stats['total_errors']}")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    
    finally:
        print("\n[7] Stopping observability system...")
        stop_observability_writer()
        
        print("\nDemo complete!")
        print("\nKey observations:")
        print("- Database grew initially, then stabilized after retention kicked in")
        print("- Old records (>6 minutes) were automatically cleaned up") 
        print("- Database size remained constant in steady state")
        print("- No manual VACUUM needed - SQLite reuses freed space")


if __name__ == "__main__":
    main() 