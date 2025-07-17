#!/usr/bin/env python
"""
Integrate tyu5_pnl CTO-verified position tracking logic into our SQLite database system.

This script adapts the proven tyu5_pnl logic to work with our database structure,
converting Excel-based workflow to SQLite storage.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import tyu5_pnl modules directly without adding to path to avoid circular import
# We'll import the classes we need directly
import importlib.util

# Load TradeProcessor
trade_processor_spec = importlib.util.spec_from_file_location(
    "trade_processor", 
    Path(__file__).parent.parent / "lib" / "trading" / "pnl" / "tyu5_pnl" / "core" / "trade_processor.py"
)
trade_processor_module = importlib.util.module_from_spec(trade_processor_spec)
trade_processor_spec.loader.exec_module(trade_processor_module)
TradeProcessor = trade_processor_module.TradeProcessor

# For PositionCalculator, we'll create a simplified version to avoid circular import

# Import our database modules
from lib.trading.pnl_calculator.storage import PnLStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_trades_to_tyu5_format(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Convert our trade format to tyu5_pnl expected format."""
    # Create a copy to avoid modifying original
    tyu5_trades = trades_df.copy()
    
    # Rename columns to match tyu5_pnl expectations
    column_mapping = {
        'tradeID': 'trade_id',
        'Date': 'Date',
        'Time': 'Time', 
        'Symbol': 'Symbol',
        'Action': 'Action',
        'Quantity': 'Quantity',
        'Price': 'Price',
        'Fees': 'Fees',
        'Type': 'Type'
    }
    
    # Only rename columns that exist
    rename_dict = {k: v for k, v in column_mapping.items() if k in tyu5_trades.columns}
    tyu5_trades = tyu5_trades.rename(columns=rename_dict)
    
    # Ensure required columns exist with defaults if needed
    if 'Type' not in tyu5_trades.columns:
        # Determine type based on symbol pattern
        tyu5_trades['Type'] = tyu5_trades['Symbol'].apply(
            lambda x: 'OPT' if ('OCA' in x or 'OPA' in x) else 'FUT'
        )
    
    if 'Fees' not in tyu5_trades.columns:
        tyu5_trades['Fees'] = 0.0
        
    return tyu5_trades


def save_positions_to_database(positions_df: pd.DataFrame, storage: PnLStorage):
    """Save positions from tyu5_pnl to our SQLite database."""
    
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    # Clear existing positions
    cursor.execute("DELETE FROM positions")
    logger.info("Cleared existing positions")
    
    # Insert new positions
    for _, pos in positions_df.iterrows():
        # Extract option details if applicable
        symbol = pos['Symbol']
        is_option = pos['Type'] in ['CALL', 'PUT', 'OPT']
        option_strike = None
        option_expiry = None
        
        if is_option and '/' in symbol:
            # Format: XCMEOCADPS20250714N0VY2/108.75
            parts = symbol.split('/')
            if len(parts) == 2:
                try:
                    option_strike = float(parts[1])
                    # Extract date from the instrument code
                    date_part = parts[0].split('PS')[1][:8]  # Get YYYYMMDD after PS
                    option_expiry = datetime.strptime(date_part, '%Y%m%d').date()
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse option details from {symbol}")
        
        # Insert position record
        cursor.execute("""
            INSERT INTO positions (
                instrument_name, position_quantity, avg_cost,
                total_realized_pnl, unrealized_pnl, last_market_price,
                last_trade_id, last_updated, is_option,
                option_strike, option_expiry, closed_quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            pos['Net_Quantity'],
            pos['Avg_Entry_Price'],
            0.0,  # Realized P&L tracked separately
            pos['Unrealized_PNL'],
            pos['Current_Price'],
            'TYU5_IMPORT',
            datetime.now(),
            is_option,
            option_strike,
            option_expiry,
            0.0  # Will be updated by closed position tracker
        ))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Saved {len(positions_df)} positions to database")


def process_trades_with_tyu5_logic():
    """Process all trades using tyu5_pnl logic and save to database."""
    
    # Initialize storage
    storage = PnLStorage("data/output/pnl/pnl_tracker.db")
    
    # Load trades from database
    conn = storage._get_connection()
    trades_df = pd.read_sql_query("""
        SELECT tradeID, Date, Time, Symbol, Action, Quantity, Price, Fees, Type
        FROM cto_trades
        ORDER BY Date, Time
    """, conn)
    conn.close()
    
    if trades_df.empty:
        logger.warning("No trades found in database")
        return
    
    logger.info(f"Processing {len(trades_df)} trades with tyu5_pnl logic")
    
    # Convert to tyu5_pnl format
    tyu5_trades = convert_trades_to_tyu5_format(trades_df)
    
    # Process trades using tyu5_pnl logic
    tp = TradeProcessor()
    processed_trades_df = tp.process_trades(tyu5_trades)
    
    # Calculate positions
    pc = PositionCalculator()
    pc.positions = tp.positions
    pc.position_details = tp.position_details
    pc.current_prices = tp.current_prices
    
    # Get current market prices if available
    conn = storage._get_connection()
    try:
        market_prices_df = pd.read_sql_query("""
            SELECT symbol as Symbol, current_price as Current_Price, prior_close as Prior_Close
            FROM market_prices
            WHERE current_price IS NOT NULL
        """, conn)
        
        if not market_prices_df.empty:
            pc.update_prices(market_prices_df)
            logger.info(f"Updated prices for {len(market_prices_df)} instruments")
    except Exception as e:
        logger.warning(f"Could not load market prices: {e}")
    finally:
        conn.close()
    
    # Calculate final positions
    positions_df = pc.calculate_positions()
    
    if positions_df.empty:
        logger.warning("No positions calculated")
        return
        
    logger.info(f"Calculated {len(positions_df)} positions")
    print("\nPositions Summary:")
    print(positions_df[['Symbol', 'Type', 'Net_Quantity', 'Avg_Entry_Price', 'Unrealized_PNL']])
    
    # Save positions to database
    save_positions_to_database(positions_df, storage)
    
    # Also save as Excel for verification
    output_file = "data/output/pnl/tyu5_positions_verification.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        positions_df.to_excel(writer, sheet_name='Positions', index=False)
        processed_trades_df.to_excel(writer, sheet_name='Processed_Trades', index=False)
    
    logger.info(f"Saved verification Excel to {output_file}")
    
    return positions_df


if __name__ == "__main__":
    positions = process_trades_with_tyu5_logic()
    
    if positions is not None and not positions.empty:
        print("\n✅ Successfully integrated tyu5_pnl position tracking!")
        print(f"Created {len(positions)} positions in the database")
    else:
        print("\n❌ No positions were created - check the logs for issues") 