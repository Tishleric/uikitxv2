"""Demo: Process Groups for Organizing Monitored Functions"""

import asyncio
import time
import os

# Suppress monitor output for cleaner demo
os.environ["MONITOR_QUIET"] = "1"

from lib.monitoring.decorators.monitor import (
    monitor, start_observability_writer, stop_observability_writer,
    get_observability_queue
)

# Example 1: Auto-derived process groups (from module name)
@monitor()
def calculate_portfolio_value():
    """Process group auto-derived: tests.monitoring.observability.demo_process_groups"""
    return 1_000_000

@monitor()
def check_risk_limits():
    """Process group auto-derived: tests.monitoring.observability.demo_process_groups"""
    return "PASSED"


# Example 2: Custom business logic grouping
@monitor(process_group="trading.orders")
def submit_order(symbol: str, quantity: int):
    """Grouped under trading.orders"""
    return f"Order submitted: {symbol} x{quantity}"

@monitor(process_group="trading.orders")
def cancel_order(order_id: str):
    """Also grouped under trading.orders"""
    return f"Order {order_id} cancelled"

@monitor(process_group="trading.risk")
def calculate_var():
    """Grouped under trading.risk"""
    return 0.05

@monitor(process_group="trading.risk")
def check_position_limits():
    """Also grouped under trading.risk"""
    return {"futures": "OK", "options": "OK"}


# Example 3: Hierarchical grouping by criticality
@monitor(process_group="critical.realtime")
def process_market_data(symbol: str):
    """Critical real-time processing"""
    time.sleep(0.001)  # Simulate work
    return {"bid": 100.5, "ask": 100.6}

@monitor(process_group="critical.realtime")
async def stream_prices():
    """Critical async price streaming"""
    await asyncio.sleep(0.001)
    return "Streaming..."

@monitor(process_group="batch.reporting")
def generate_eod_report():
    """Non-critical batch job"""
    time.sleep(0.01)  # Simulate work
    return "Report generated"

@monitor(process_group="batch.analytics")
def calculate_daily_pnl():
    """Non-critical analytics"""
    return {"pnl": 25000}


# Example 4: Service-based grouping
@monitor(process_group="api.tt_rest")
def get_working_orders():
    """External TT API call"""
    return [{"id": "123", "status": "working"}]

@monitor(process_group="api.pricing_monkey")
def fetch_option_prices():
    """External Pricing Monkey API"""
    return {"ZN": 110.25}

@monitor(process_group="api.internal.risk")
def query_risk_service():
    """Internal risk service API"""
    return {"exposure": 1_500_000}


def analyze_process_groups():
    """Analyze how functions are grouped in the database"""
    import sqlite3
    
    conn = sqlite3.connect("logs/observability.db")
    cursor = conn.cursor()
    
    # Count records by process group
    cursor.execute("""
        SELECT 
            SUBSTR(process, 1, 
                CASE 
                    WHEN process LIKE 'api.internal.%' THEN LENGTH('api.internal')
                    WHEN process LIKE 'api.%' THEN INSTR(SUBSTR(process || '.', 5), '.') + 3
                    WHEN process LIKE 'trading.%' THEN INSTR(SUBSTR(process || '.', 9), '.') + 7
                    WHEN process LIKE 'critical.%' THEN INSTR(SUBSTR(process || '.', 10), '.') + 8
                    WHEN process LIKE 'batch.%' THEN INSTR(SUBSTR(process || '.', 7), '.') + 5
                    ELSE INSTR(process, '.') - 1
                END
            ) as process_group,
            COUNT(*) as call_count,
            AVG(duration_ms) as avg_duration,
            SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) as error_count
        FROM process_trace
        WHERE process LIKE 'trading.%' 
           OR process LIKE 'critical.%' 
           OR process LIKE 'batch.%'
           OR process LIKE 'api.%'
        GROUP BY process_group
        ORDER BY process_group
    """)
    
    print("\n📊 Process Group Analysis:")
    print("-" * 70)
    print(f"{'Process Group':<30} {'Calls':>10} {'Avg ms':>15} {'Errors':>10}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        group, calls, avg_ms, errors = row
        print(f"{group:<30} {calls:>10} {avg_ms:>15.2f} {errors:>10}")
    
    conn.close()


async def main():
    """Run demo showing process group organization"""
    
    print("🎯 Process Groups Demo")
    print("=" * 70)
    
    # Start monitoring
    writer = start_observability_writer()
    queue = get_observability_queue()
    queue.clear()
    
    try:
        print("\n1️⃣ Auto-derived process groups (using module name):")
        calculate_portfolio_value()
        check_risk_limits()
        
        print("\n2️⃣ Business logic grouping (trading.orders, trading.risk):")
        submit_order("ZN", 100)
        cancel_order("ORD-123")
        calculate_var()
        check_position_limits()
        
        print("\n3️⃣ Criticality-based grouping:")
        process_market_data("ZN")
        await stream_prices()
        generate_eod_report()
        calculate_daily_pnl()
        
        print("\n4️⃣ Service-based grouping:")
        get_working_orders()
        fetch_option_prices()
        query_risk_service()
        
        # Wait for writes
        time.sleep(0.5)
        
        # Analyze the groupings
        analyze_process_groups()
        
        # Show queue stats
        stats = queue.get_queue_stats()
        metrics = stats['metrics']
        print(f"\n📈 Queue Stats: {metrics['normal_enqueued']} normal + {metrics['error_enqueued']} error records processed")
        
    finally:
        stop_observability_writer()


if __name__ == "__main__":
    asyncio.run(main()) 