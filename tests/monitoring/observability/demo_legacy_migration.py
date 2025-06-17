"""Demo: Legacy decorator migration to unified @monitor"""

import time
import os

# Suppress monitor output for cleaner demo
os.environ["MONITOR_QUIET"] = "1"

# Import legacy decorators (for comparison)
from lib.monitoring.decorators.trace_time import TraceTime
from lib.monitoring.decorators.trace_cpu import TraceCpu
from lib.monitoring.decorators.trace_memory import TraceMemory

# Import new unified monitor
from lib.monitoring.decorators.monitor import monitor, start_observability_writer, stop_observability_writer


def demo_legacy_decorators():
    """Show how functions looked with legacy decorators"""
    print("\n=== LEGACY DECORATORS (OLD WAY) ===")
    
    @TraceTime
    @TraceCpu
    @TraceMemory
    def process_trade_data(symbol: str, quantity: int):
        """Process trade with multiple legacy decorators"""
        # Simulate some CPU/memory intensive work
        data = [i**2 for i in range(100000)]
        time.sleep(0.1)
        return {"symbol": symbol, "quantity": quantity, "processed": len(data)}
    
    # Execute function
    result = process_trade_data("AAPL", 100)
    print(f"Legacy result: {result}")


def demo_new_monitor():
    """Show the new unified approach"""
    print("\n=== NEW UNIFIED @monitor (CAPTURES EVERYTHING) ===")
    
    # Start the observability writer
    start_observability_writer(db_path="logs/migration_demo.db")
    
    # Example 1: Simplest migration - just @monitor()
    @monitor()
    def process_trade_data(symbol: str, quantity: int):
        """Process trade with unified monitor - captures EVERYTHING by default"""
        # Simulate some CPU/memory intensive work
        data = [i**2 for i in range(100000)]
        time.sleep(0.1)
        return {"symbol": symbol, "quantity": quantity, "processed": len(data)}
    
    # Example 2: Auto-derived process group
    @monitor()
    def calculate_risk_metrics(portfolio: dict):
        """Monitor automatically uses module name as process group"""
        # Some calculation
        risk_score = sum(portfolio.values()) * 0.05
        return {"risk_score": risk_score, "status": "calculated"}
    
    # Example 3: Explicit process group (optional)
    @monitor(process_group="trading.critical")
    def execute_order(order_id: int, action: str):
        """Only specify process_group when you need custom grouping"""
        time.sleep(0.05)
        return {"order_id": order_id, "action": action, "status": "executed"}
    
    # Example 4: Disable specific captures if needed
    @monitor(capture={"args": True, "result": True, "cpu_usage": False, "memory_usage": False})
    def log_audit_event(event_type: str, user_id: int):
        """Selectively disable CPU/memory tracking if not needed"""
        return {"event": event_type, "user": user_id, "logged": True}
    
    # Execute all functions
    print("\nExecuting monitored functions...")
    
    result1 = process_trade_data("AAPL", 100)
    print(f"Trade processing: {result1}")
    
    result2 = calculate_risk_metrics({"AAPL": 1000, "GOOGL": 2000})
    print(f"Risk metrics: {result2}")
    
    result3 = execute_order(12345, "BUY")
    print(f"Order execution: {result3}")
    
    result4 = log_audit_event("LOGIN", 42)
    print(f"Audit event: {result4}")
    
    # Wait for writes to complete
    time.sleep(0.5)
    
    # Check what was captured
    print("\n=== CAPTURED DATA ===")
    from lib.monitoring.writers import SQLiteWriter
    writer = SQLiteWriter("logs/migration_demo.db")
    stats = writer.get_stats()
    print(f"Process traces captured: {stats['process_trace_count']}")
    print(f"Data traces captured: {stats['data_trace_count']}")
    
    # Query to show captured data
    import sqlite3
    conn = sqlite3.connect("logs/migration_demo.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT process, status, duration_ms, cpu_delta, memory_delta_mb
        FROM process_trace
        ORDER BY ts DESC
        LIMIT 10
    """)
    
    print("\nRecent traces:")
    print(f"{'Process':<50} {'Status':<6} {'Duration(ms)':<12} {'CPU Δ%':<10} {'Memory ΔMB':<12}")
    print("-" * 90)
    
    for row in cursor.fetchall():
        process, status, duration, cpu_delta, mem_delta = row
        cpu_str = f"{cpu_delta:.2f}%" if cpu_delta is not None else "N/A"
        mem_str = f"{mem_delta:.3f} MB" if mem_delta is not None else "N/A"
        print(f"{process:<50} {status:<6} {duration:<12.3f} {cpu_str:<10} {mem_str:<12}")
    
    conn.close()
    stop_observability_writer()


def show_migration_comparison():
    """Show side-by-side comparison of migration approaches"""
    print("\n" + "="*80)
    print("MIGRATION COMPARISON")
    print("="*80)
    
    print("""
OLD WAY (Multiple Decorators):
-----------------------------
@TraceTime
@TraceCpu  
@TraceMemory
def my_function():
    pass

NEW WAY (Single Decorator, Captures Everything):
----------------------------------------------
@monitor()
def my_function():
    pass

Benefits:
- Single decorator instead of multiple
- Captures everything by default (Track Everything philosophy)
- Process group auto-derived from module name
- Zero configuration required
- Cleaner code, same comprehensive monitoring
""")


if __name__ == "__main__":
    # Clean up any existing demo database
    demo_db = "logs/migration_demo.db"
    if os.path.exists(demo_db):
        os.remove(demo_db)
    
    # Run demos
    # demo_legacy_decorators()  # Skip legacy demo to avoid import issues
    demo_new_monitor()
    show_migration_comparison()
    
    print("\n✅ Migration demo complete!") 