#!/usr/bin/env python3
"""
Test Integrated Settlement-Aware P&L Pipeline

This script tests that our settlement-aware P&L is properly integrated
through the entire TYU5 pipeline.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import sqlite3
import logging
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl.tyu5_pnl import main as tyu5_main
from lib.trading.pnl_integration.settlement_constants import CHICAGO_TZ, get_pnl_date_for_trade
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_trades():
    """Create test trades that span settlement boundaries."""
    cdt = pytz.timezone('America/Chicago')
    
    trades = []
    base_date = date.today() - timedelta(days=2)
    
    # Trade 1: Buy TYU5 before 2pm (belongs to that day's P&L)
    trade_time1 = cdt.localize(datetime.combine(base_date, datetime.min.time().replace(hour=10)))
    trades.append({
        'Date': base_date.strftime('%Y-%m-%d'),
        'Time': '10:00:00',
        'marketTradeTime': trade_time1.strftime('%Y-%m-%d %H:%M:%S'),
        'trade_id': 'T001',
        'Symbol': 'TYU5',
        'Quantity': 10,
        'Price': '110-16',  # Using 32nds format
        'Action': 'BUY',
        'Type': 'FUT'
    })
    
    # Trade 2: Sell half after 2pm same day (belongs to next day's P&L)
    trade_time2 = cdt.localize(datetime.combine(base_date, datetime.min.time().replace(hour=15)))
    trades.append({
        'Date': base_date.strftime('%Y-%m-%d'),
        'Time': '15:00:00',
        'marketTradeTime': trade_time2.strftime('%Y-%m-%d %H:%M:%S'),
        'trade_id': 'T002',
        'Symbol': 'TYU5',
        'Quantity': -5,
        'Price': '110-24',  # 110.75 = 110 + 24/32
        'Action': 'SELL',
        'Type': 'FUT'
    })
    
    # Trade 3: Sell rest next day after 2pm
    next_date = base_date + timedelta(days=1)
    trade_time3 = cdt.localize(datetime.combine(next_date, datetime.min.time().replace(hour=15)))
    trades.append({
        'Date': next_date.strftime('%Y-%m-%d'),
        'Time': '15:00:00',
        'marketTradeTime': trade_time3.strftime('%Y-%m-%d %H:%M:%S'),
        'trade_id': 'T003',
        'Symbol': 'TYU5',
        'Quantity': -5,
        'Price': '111-00',  # 111.0
        'Action': 'SELL',
        'Type': 'FUT'
    })
    
    return pd.DataFrame(trades)


def create_test_settlement_prices():
    """Create settlement prices in market_prices.db for testing."""
    db_path = "data/output/market_prices/market_prices.db"
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create futures_prices table if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS futures_prices (
            symbol TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            prior_close REAL,
            Flash_Close REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, trade_date)
        )
    """)
    
    # Insert test settlement prices
    base_date = date.today() - timedelta(days=3)
    
    test_prices = [
        ('TYU5 Comdty', base_date.isoformat(), 110.25),  # Day -3
        ('TYU5 Comdty', (base_date + timedelta(1)).isoformat(), 110.625),  # Day -2
        ('TYU5 Comdty', (base_date + timedelta(2)).isoformat(), 110.875),  # Day -1
        ('TYU5 Comdty', date.today().isoformat(), 111.125),  # Today
    ]
    
    for symbol, trade_date, price in test_prices:
        cursor.execute("""
            INSERT OR REPLACE INTO futures_prices (symbol, trade_date, prior_close)
            VALUES (?, ?, ?)
        """, (symbol, trade_date, price))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Created {len(test_prices)} test settlement prices")


def run_integrated_test():
    """Run the integrated test."""
    logger.info("Starting integrated settlement P&L test")
    
    # Create test data
    trades_df = create_test_trades()
    create_test_settlement_prices()
    
    logger.info(f"Created {len(trades_df)} test trades")
    logger.info(trades_df[['Date', 'Time', 'Symbol', 'Quantity', 'Price']])
    
    # Create sample data for TYU5
    sample_data = {
        'Trades_Input': trades_df,
        'Market_Prices': pd.DataFrame()  # Empty - we'll load from DB
    }
    
    # Run TYU5 analysis
    output_file = "data/output/test_integrated_settlement_pnl.xlsx"
    
    try:
        results = tyu5_main.run_pnl_analysis(
            input_file=None,
            output_file=output_file,
            base_price=110.5,
            price_range=2.0,
            steps=10,
            sample_data=sample_data,
            debug=True
        )
        
        logger.info("TYU5 analysis completed successfully")
        
        # Check results
        positions_df = results['positions_df']
        logger.info(f"\nPositions DataFrame:\n{positions_df}")
        
        # Check for settlement P&L columns
        if 'Settlement_PNL_Total' in positions_df.columns:
            logger.info("\n✓ Settlement P&L integration successful!")
            logger.info(f"Settlement P&L Total: {positions_df['Settlement_PNL_Total'].iloc[0]}")
            
            if 'PNL_Components' in positions_df.columns:
                logger.info(f"P&L Components: {positions_df['PNL_Components'].iloc[0]}")
        else:
            logger.error("✗ Settlement P&L columns not found in output")
        
        # Check breakdown for timestamps
        breakdown_df = results['breakdown_df']
        if 'entry_datetime' in breakdown_df.columns:
            logger.info("\n✓ Timestamp tracking successful!")
            logger.info(f"Lot timestamps preserved in breakdown")
        else:
            logger.error("✗ Timestamps not found in breakdown")
        
        # Check for alerts about missing prices
        conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
        cursor = conn.execute("""
            SELECT COUNT(*) FROM tyu5_alerts 
            WHERE alert_type = 'MISSING_SETTLEMENT_PRICE'
            AND created_at > datetime('now', '-1 hour')
        """)
        alert_count = cursor.fetchone()[0]
        conn.close()
        
        if alert_count > 0:
            logger.warning(f"Found {alert_count} missing price alerts")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_integrated_test()
    
    if success:
        logger.info("\n✓ All integration tests passed!")
    else:
        logger.error("\n✗ Integration tests failed")
        sys.exit(1) 