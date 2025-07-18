#!/usr/bin/env python
"""Example: Unified P&L Service with TYU5 Advanced Features

This script demonstrates the enhanced UnifiedPnLService that combines
TradePreprocessor's real-time tracking with TYU5's advanced features.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService
from lib.trading.pnl_integration.unified_pnl_api import UnifiedPnLAPI


def main():
    """Demonstrate unified service capabilities."""
    print("=" * 80)
    print("Unified P&L Service Demo - Phase 3 Integration")
    print("=" * 80)
    
    # Initialize service
    db_path = "data/output/pnl/pnl_tracker.db"
    
    # Create unified service
    service = UnifiedPnLService(
        db_path=db_path,
        trade_ledger_dir="data/input/trade_ledger",
        price_directories=["data/input/market_prices"]
    )
    
    print("\n1. Service Status:")
    print(f"   - TYU5 Features Enabled: {service._tyu5_enabled}")
    
    # Get basic positions
    print("\n2. Basic Positions (TradePreprocessor):")
    positions = service.get_open_positions()
    if positions:
        for pos in positions[:3]:  # Show first 3
            print(f"   - {pos['instrument_name']}: {pos['position_quantity']} @ {pos.get('avg_cost', 0):.4f}")
            print(f"     P&L: ${pos.get('total_realized_pnl', 0) + pos.get('unrealized_pnl', 0):,.2f}")
    else:
        print("   No positions found")
    
    # Get positions with lots (TYU5 feature)
    print("\n3. Positions with Lot Details (TYU5):")
    lot_positions = service.get_positions_with_lots()
    if lot_positions:
        for pos in lot_positions[:2]:  # Show first 2
            print(f"   - {pos['symbol']}: {pos['net_position']} total")
            if 'lots' in pos and pos['lots']:
                print("     Lots:")
                for lot in pos['lots']:
                    print(f"       • {lot['remaining_quantity']} @ {lot['entry_price']:.4f} ({lot['trade_id']})")
    else:
        print("   No lot data available")
    
    # Get portfolio Greeks
    print("\n4. Portfolio Greeks (TYU5):")
    greeks = service.get_portfolio_greeks()
    if greeks['option_count'] > 0:
        print(f"   - Delta: {greeks['total_delta']:.2f}")
        print(f"   - Gamma: {greeks['total_gamma']:.4f}")
        print(f"   - Vega: {greeks['total_vega']:.2f}")
        print(f"   - Theta: {greeks['total_theta']:.2f}")
        print(f"   - Options: {greeks['option_count']}")
    else:
        print("   No options with Greeks")
    
    # Get Greek exposure by position
    print("\n5. Greek Exposure by Position:")
    exposure = service.get_greek_exposure()
    if exposure:
        df = pd.DataFrame(exposure)
        print(df[['symbol', 'position_quantity', 'delta', 'position_delta']].head())
    else:
        print("   No Greek exposure data")
    
    # Get risk scenarios for a specific symbol
    print("\n6. Risk Scenarios:")
    # Find a future symbol
    future_symbols = [p['symbol'] for p in lot_positions if p.get('is_option', 0) == 0]
    if future_symbols:
        symbol = future_symbols[0]
        scenarios = service.get_risk_scenarios(symbol)
        if scenarios:
            print(f"   Scenarios for {symbol}:")
            for s in scenarios[::2]:  # Show every other scenario
                print(f"   - Price: {s['scenario_price']:.2f} => P&L: ${s['scenario_pnl']:,.0f}")
        else:
            print(f"   No scenarios for {symbol}")
    
    # Get comprehensive view for a position
    print("\n7. Comprehensive Position View:")
    if lot_positions:
        symbol = lot_positions[0]['symbol']
        full_view = service.get_comprehensive_position_view(symbol)
        if full_view:
            print(f"   Position: {symbol}")
            print(f"   - Net Quantity: {full_view.get('net_position', 0)}")
            print(f"   - Lots: {full_view.get('lot_count', 0)}")
            if 'greeks' in full_view and full_view['greeks']:
                print(f"   - Delta: {full_view['greeks'].get('delta', 0):.4f}")
            if 'risk_scenarios' in full_view:
                print(f"   - Risk Scenarios: {len(full_view['risk_scenarios'])}")
    
    # Get enhanced portfolio summary
    print("\n8. Enhanced Portfolio Summary:")
    summary = service.get_portfolio_summary_enhanced()
    
    print("   Positions:")
    if 'positions' in summary:
        pos_data = summary['positions']
        print(f"   - Total Positions: {pos_data.get('position_count', 0)}")
        print(f"   - Long: {pos_data.get('long_positions', 0)}")
        print(f"   - Short: {pos_data.get('short_positions', 0)}")
        print(f"   - Total P&L: ${pos_data.get('total_pnl', 0):,.2f}")
    
    print("\n   Advanced Features:")
    if 'lots' in summary:
        print(f"   - Total Lots: {summary['lots'].get('total_lots', 0)}")
    if 'greeks' in summary:
        print(f"   - Options with Greeks: {summary['greeks'].get('option_count', 0)}")
    if 'scenarios' in summary:
        print(f"   - Symbols with Scenarios: {summary['scenarios'].get('symbols_with_scenarios', 0)}")
    
    # Direct API usage example
    print("\n9. Direct API Usage (Advanced Queries):")
    api = UnifiedPnLAPI(db_path)
    
    # Get match history
    matches_df = api.get_match_history()
    if not matches_df.empty:
        print("\n   Recent FIFO Matches:")
        print(matches_df[['symbol', 'matched_quantity', 'realized_pnl']].head(3))
    
    # Get P&L attribution (if available)
    if lot_positions and any(p.get('is_option', 0) == 1 for p in lot_positions):
        option_symbol = next(p['symbol'] for p in lot_positions if p.get('is_option', 0) == 1)
        attribution_df = api.get_position_attribution(option_symbol)
        if not attribution_df.empty:
            print(f"\n   P&L Attribution for {option_symbol}:")
            print(attribution_df[['delta_pnl', 'gamma_pnl', 'vega_pnl', 'theta_pnl']].tail(1))
    
    print("\n" + "=" * 80)
    print("Phase 3 Integration Complete!")
    print("The unified service now provides:")
    print("  ✓ Real-time position tracking (TradePreprocessor)")
    print("  ✓ Lot-level FIFO tracking (TYU5)")
    print("  ✓ Option Greeks calculation (TYU5)")
    print("  ✓ Risk scenario analysis (TYU5)")
    print("  ✓ P&L attribution (TYU5)")
    print("=" * 80)


if __name__ == "__main__":
    main() 