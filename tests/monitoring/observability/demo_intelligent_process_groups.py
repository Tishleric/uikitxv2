"""Demo: Intelligent Process Group Assignment Strategies"""

import os
os.environ["MONITOR_QUIET"] = "1"  # Suppress output for cleaner demo

from lib.monitoring.decorators.monitor import monitor, get_observability_queue
from lib.monitoring.process_groups import (
    ProcessGroupStrategies, 
    set_global_strategy,
    auto_monitor,
    ModuleBasedStrategy,
    PatternBasedStrategy,
    SemanticStrategy,
    LayeredStrategy
)


def demo_manual_assignment():
    """Traditional manual process group assignment"""
    print("\n=== MANUAL PROCESS GROUP ASSIGNMENT ===")
    
    @monitor(process_group="trading.orders")
    def submit_order(symbol: str, qty: int):
        return f"Order submitted: {symbol} x{qty}"
    
    @monitor(process_group="trading.risk")
    def check_risk_limits(position: int):
        return position < 1000
    
    @monitor(process_group="external.pricing_monkey")
    def fetch_pm_data():
        return {"price": 110.25}
    
    # Execute functions
    queue = get_observability_queue()
    queue.clear()
    
    submit_order("ZN", 10)
    check_risk_limits(500)
    fetch_pm_data()
    
    # Show assigned groups
    records = queue.drain(10)
    for r in records:
        print(f"Function: {r.process.split('.')[-1]:<20} Group: {r.process}")


def demo_pattern_based_assignment():
    """Automatic assignment based on function name patterns"""
    print("\n\n=== PATTERN-BASED AUTOMATIC ASSIGNMENT ===")
    
    # Set up pattern-based strategy
    strategy = PatternBasedStrategy({
        r'^get_.*': 'data.read',
        r'^save_.*': 'data.write',
        r'^calculate_.*': 'compute',
        r'^submit_.*': 'trading.orders',
        r'^check_.*': 'validation',
        r'^fetch_.*_price.*': 'market_data'
    })
    set_global_strategy(strategy)
    
    # Functions will be auto-assigned to groups
    @auto_monitor()
    def get_user_data(user_id: int):
        return {"id": user_id, "name": "Trader"}
    
    @auto_monitor()
    def save_trade_record(trade: dict):
        return "Saved"
    
    @auto_monitor()
    def calculate_portfolio_var():
        return 0.05
    
    @auto_monitor()
    def submit_market_order(symbol: str):
        return "Submitted"
    
    @auto_monitor()
    def check_compliance_rules():
        return True
    
    @auto_monitor()
    def fetch_bond_prices():
        return [110.25, 110.50]
    
    # Execute
    queue = get_observability_queue()
    queue.clear()
    
    get_user_data(123)
    save_trade_record({"id": 1})
    calculate_portfolio_var()
    submit_market_order("ZN")
    check_compliance_rules()
    fetch_bond_prices()
    
    # Show auto-assigned groups
    records = queue.drain(10)
    print("\nPattern-based assignments:")
    for r in records:
        func_name = r.process.split('.')[-1]
        group = '.'.join(r.process.split('.')[:-1])
        print(f"Function: {func_name:<25} → Group: {group}")


def demo_semantic_assignment():
    """Assignment based on semantic analysis"""
    print("\n\n=== SEMANTIC-BASED ASSIGNMENT ===")
    
    set_global_strategy(SemanticStrategy())
    
    @auto_monitor()
    def load_historical_data():
        """Load historical market data from database"""
        return []
    
    @auto_monitor()
    def update_position_tracker(position: int):
        """Update position in database"""
        return position
    
    @auto_monitor()
    def process_trade_confirmation(trade: dict):
        """Process and transform trade confirmation"""
        return trade
    
    @auto_monitor()
    def handle_order_request(request: dict):
        """REST API endpoint for order submission"""
        return {"status": "accepted"}
    
    # Execute
    queue = get_observability_queue()
    queue.clear()
    
    load_historical_data()
    update_position_tracker(100)
    process_trade_confirmation({"id": 1})
    handle_order_request({"symbol": "ZN"})
    
    records = queue.drain(10)
    print("\nSemantic assignments (based on function names/docs):")
    for r in records:
        func_name = r.process.split('.')[-1]
        group = '.'.join(r.process.split('.')[:-1])
        print(f"Function: {func_name:<25} → Group: {group}")


def demo_trading_system_strategy():
    """Pre-configured strategy for trading systems"""
    print("\n\n=== TRADING SYSTEM STRATEGY ===")
    
    # Use pre-configured trading system strategy
    set_global_strategy(ProcessGroupStrategies.for_trading_system())
    
    # Order management functions
    @auto_monitor()
    def submit_order_to_exchange(order: dict):
        return {"order_id": "12345"}
    
    @auto_monitor()
    def cancel_order_request(order_id: str):
        return {"status": "cancelled"}
    
    @auto_monitor()
    def get_working_order_status(order_id: str):
        return {"status": "working"}
    
    # Market data functions
    @auto_monitor()
    def get_bond_price(symbol: str):
        return 110.25
    
    @auto_monitor()
    def fetch_market_data_snapshot():
        return {"ZN": 110.25, "ZF": 109.50}
    
    # Risk functions
    @auto_monitor()
    def calculate_portfolio_risk():
        return {"var": 0.05, "cvar": 0.08}
    
    @auto_monitor()
    def check_position_limits(symbol: str, qty: int):
        return qty < 1000
    
    # P&L functions
    @auto_monitor()
    def calculate_daily_pnl():
        return 25000.0
    
    @auto_monitor()
    def update_position_tracker(symbol: str, qty: int):
        return {"symbol": symbol, "position": qty}
    
    # External API functions
    @auto_monitor()
    def tt_submit_order(order: dict):
        return {"tt_order_id": "TT123"}
    
    @auto_monitor()
    def pm_get_option_prices():
        return {"calls": [], "puts": []}
    
    # Execute all functions
    queue = get_observability_queue()
    queue.clear()
    
    # Order management
    submit_order_to_exchange({"symbol": "ZN", "qty": 10})
    cancel_order_request("12345")
    get_working_order_status("12345")
    
    # Market data
    get_bond_price("ZN")
    fetch_market_data_snapshot()
    
    # Risk
    calculate_portfolio_risk()
    check_position_limits("ZN", 500)
    
    # P&L
    calculate_daily_pnl()
    update_position_tracker("ZN", 100)
    
    # External APIs
    tt_submit_order({"symbol": "ZN"})
    pm_get_option_prices()
    
    # Show intelligently assigned groups
    records = queue.drain(20)
    print("\nTrading system assignments:")
    print("-" * 60)
    
    # Group by process group
    groups = {}
    for r in records:
        func_name = r.process.split('.')[-1]
        group = '.'.join(r.process.split('.')[:-1])
        if group not in groups:
            groups[group] = []
        groups[group].append(func_name)
    
    # Display organized by group
    for group in sorted(groups.keys()):
        print(f"\n{group}:")
        for func in groups[group]:
            print(f"  - {func}")


def demo_future_multi_group():
    """Demo of future multi-group support (not yet implemented)"""
    print("\n\n=== FUTURE: MULTI-GROUP SUPPORT ===")
    print("Concept: Functions could belong to multiple groups")
    print("\nExample (not yet implemented):")
    print("@multi_monitor(groups=['trading.orders', 'critical.realtime', 'audit.all'])")
    print("def submit_order():")
    print("    pass")
    print("\nThis would allow:")
    print("- Filtering by any group in dashboards")
    print("- Different retention policies per group")
    print("- Role-based access control per group")
    print("- Aggregation across multiple dimensions")


def main():
    """Run all demos"""
    print("🎯 Intelligent Process Group Assignment Demo")
    print("=" * 60)
    
    demo_manual_assignment()
    demo_pattern_based_assignment()
    demo_semantic_assignment()
    demo_trading_system_strategy()
    demo_future_multi_group()
    
    print("\n\n📊 Key Benefits of Intelligent Assignment:")
    print("1. Consistency - Similar functions automatically grouped together")
    print("2. Evolution - New functions auto-assigned without manual updates")
    print("3. Refactoring - Move functions between modules without losing grouping")
    print("4. Discovery - Semantic analysis finds natural groupings")
    print("5. Flexibility - Multiple strategies can be combined")


if __name__ == "__main__":
    main() 