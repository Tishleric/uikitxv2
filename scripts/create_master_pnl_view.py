#!/usr/bin/env python
"""
Create the master P&L view combining data from all sources.

This script creates a comprehensive P&L view with:
- Position data from pnl_tracker.db
- Market data from spot_risk.db (via Bloomberg symbol join)
- Greeks from spot_risk_calculated table
- Basic P&L calculations

Phase 1 implementation - using only data we currently have.
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def attach_databases(conn):
    """Attach all required databases to the main connection."""
    cursor = conn.cursor()
    
    # Attach spot risk database
    cursor.execute("ATTACH DATABASE 'data/output/spot_risk/spot_risk.db' AS spot_risk")
    
    # Try to attach market prices if it exists
    market_db = Path("data/output/market_prices/market_prices.db")
    if market_db.exists():
        cursor.execute("ATTACH DATABASE 'data/output/market_prices/market_prices.db' AS market_prices")
        logger.info("Attached market prices database")
    else:
        logger.warning("Market prices database not found - px_last and px_settle will be NULL")
    
    return conn


def create_master_pnl_view(conn):
    """Create the master P&L view with all available data."""
    
    cursor = conn.cursor()
    
    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS master_pnl_view")
    
    # Create a table by selecting and joining all data
    view_sql = """
    CREATE TABLE master_pnl_view AS
    WITH 
    -- Extract raw spot risk data from JSON
    spot_risk_data AS (
        SELECT 
            sr.id,
            sr.bloomberg_symbol,
            sr.instrument_key,
            sr.instrument_type,
            sr.midpoint_price,
            sr.expiry_date,
            sr.strike,
            -- Extract from JSON raw_data
            json_extract(sr.raw_data, '$.bid') as bid,
            json_extract(sr.raw_data, '$.ask') as ask,
            json_extract(sr.raw_data, '$.adjtheor') as adjtheor,
            json_extract(sr.raw_data, '$.vtexp') as vtexp,
            json_extract(sr.raw_data, '$.last') as last_price
        FROM spot_risk.spot_risk_raw sr
        WHERE sr.bloomberg_symbol IS NOT NULL
    ),
    -- Get latest spot risk record per symbol
    latest_spot_risk AS (
        SELECT 
            sr.*,
            ROW_NUMBER() OVER (PARTITION BY sr.bloomberg_symbol ORDER BY sr.id DESC) as rn
        FROM spot_risk_data sr
    )
    SELECT 
        -- Identifiers
        p.instrument_name as symbol,
        
        -- Market Data from Spot Risk
        CAST(lsr.bid AS REAL) as bid,
        CAST(lsr.ask AS REAL) as ask,
        COALESCE(CAST(lsr.adjtheor AS REAL), lsr.midpoint_price) as price,
        
        -- Market Prices (if available)
        NULL as px_last,  -- Will be populated when market prices available
        NULL as px_settle, -- Will be populated when market prices available
        
        -- Position Data
        p.position_quantity as open_position,
        NULL as closed_position, -- Phase 2
        
        -- Basic P&L Calculations
        p.position_quantity * (p.last_market_price - p.avg_cost) * 1000 as pnl_live,
        NULL as pnl_flash,  -- Requires px_last
        NULL as pnl_close,  -- Requires px_settle
        
        -- DV01
        CASE 
            WHEN p.is_option = 1 THEN sc.delta_F
            ELSE 63.0  -- Hardcoded for futures
        END as dv01,
        
        -- Greeks (F-space)
        sc.delta_F as delta_f,
        sc.gamma_F as gamma_f,
        sc.speed_F as speed_f,
        sc.theta_F as theta_f,
        sc.vega_price as vega_f,
        
        -- Greeks (Y-space) 
        sc.delta_y as delta_y,
        sc.gamma_y as gamma_y,
        NULL as speed_y,  -- Not calculated yet
        NULL as theta_y,  -- Not calculated yet  
        sc.vega_y as vega_y,
        
        -- Option Details
        CAST(lsr.vtexp AS REAL) as vtexp,
        lsr.expiry_date as expiry_date,
        NULL as underlying_future, -- Phase 2
        
        -- Metadata
        CURRENT_TIMESTAMP as time_updated,
        CASE 
            WHEN sc.calculation_status = 'success' THEN 'Complete'
            WHEN sc.calculation_status = 'failed' THEN 'Greeks Failed'
            WHEN lsr.bloomberg_symbol IS NOT NULL THEN 'No Greeks'
            ELSE 'No Spot Risk Data'
        END as data_freshness,
        
        -- Additional useful fields
        p.avg_cost,
        p.unrealized_pnl,
        p.is_option,
        lsr.instrument_type,
        sc.implied_vol,
        sc.calculation_status,
        sc.error_message
        
    FROM 
        positions p
        
    -- Join with latest spot risk data
    LEFT JOIN latest_spot_risk lsr 
        ON p.instrument_name = lsr.bloomberg_symbol 
        AND lsr.rn = 1
        
    -- Join with calculated Greeks
    LEFT JOIN spot_risk.spot_risk_calculated sc 
        ON lsr.id = sc.raw_id
        
    WHERE 
        p.position_quantity != 0  -- Only show active positions
    
    ORDER BY 
        p.is_option,
        p.instrument_name
    """
    
    cursor.execute(view_sql)
    conn.commit()
    
    logger.info("Created master_pnl_view table successfully")
    
    # Create indexes on the master table for better performance
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_master_pnl_symbol ON master_pnl_view(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_master_pnl_is_option ON master_pnl_view(is_option)")
        conn.commit()
        logger.info("Created performance indexes")
    except Exception as e:
        logger.warning(f"Could not create indexes: {e}")
    
    # Also create index on spot risk if not exists
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_spot_risk_bloomberg 
            ON spot_risk.spot_risk_raw(bloomberg_symbol)
        """)
        conn.commit()
    except:
        pass  # Index might already exist


def display_view_summary(conn):
    """Display a summary of the created view."""
    
    # Query the view
    df = pd.read_sql_query("SELECT * FROM master_pnl_view", conn)
    
    print("\n" + "=" * 80)
    print("MASTER P&L VIEW SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal Positions: {len(df)}")
    print(f"Futures: {len(df[df['is_option'] == 0])}")
    print(f"Options: {len(df[df['is_option'] == 1])}")
    
    # Show sample data
    print("\n📊 Sample Data (First 5 positions):")
    display_cols = [
        'symbol', 'open_position', 'avg_cost', 'price', 
        'pnl_live', 'dv01', 'delta_f', 'gamma_f', 'data_freshness'
    ]
    
    # Only show columns that exist
    available_cols = [col for col in display_cols if col in df.columns]
    print(df[available_cols].head().to_string(index=False))
    
    # Data quality summary
    print("\n📊 Data Quality:")
    print(f"  Positions with spot risk data: {df['bid'].notna().sum()}/{len(df)}")
    print(f"  Positions with Greeks calculated: {df['delta_f'].notna().sum()}/{len(df)}")
    print(f"  Positions with vtexp: {df['vtexp'].notna().sum()}/{len(df)}")
    
    # P&L Summary
    print(f"\n💰 P&L Summary:")
    total_pnl = df['pnl_live'].sum()
    print(f"  Total Live P&L: ${total_pnl:,.2f}")
    print(f"  Futures P&L: ${df[df['is_option'] == 0]['pnl_live'].sum():,.2f}")
    print(f"  Options P&L: ${df[df['is_option'] == 1]['pnl_live'].sum():,.2f}")
    
    # Save to Excel for verification
    output_file = "data/output/pnl/master_pnl_view.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        df.to_excel(writer, sheet_name='Master_PnL', index=False)
        
        # Add a summary sheet
        summary_data = {
            'Metric': ['Total Positions', 'Futures', 'Options', 'Total P&L', 
                      'With Spot Risk', 'With Greeks', 'With vtexp'],
            'Value': [len(df), 
                     len(df[df['is_option'] == 0]),
                     len(df[df['is_option'] == 1]),
                     f"${total_pnl:,.2f}",
                     df['bid'].notna().sum(),
                     df['delta_f'].notna().sum(),
                     df['vtexp'].notna().sum()]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\n📄 Saved detailed view to: {output_file}")


def main():
    """Main function to create the master P&L view."""
    
    print("\n🚀 CREATING MASTER P&L VIEW")
    print("=" * 80)
    
    # Connect to main database
    pnl_db = "data/output/pnl/pnl_tracker.db"
    if not Path(pnl_db).exists():
        logger.error("P&L database not found!")
        return False
        
    conn = sqlite3.connect(pnl_db)
    
    try:
        # Attach other databases
        attach_databases(conn)
        
        # Create the view
        create_master_pnl_view(conn)
        
        # Display summary
        display_view_summary(conn)
        
        print("\n✅ Master P&L table created successfully!")
        print("\n⚠️  Note: This is a table, not a view. Run this script again to refresh data.")
        print("\nNext steps for Phase 2:")
        print("  - Implement closed position calculation")
        print("  - Add market price integration (px_last, px_settle)")
        print("  - Extract underlying future from option symbols")
        print("  - Implement LIFO calculations")
        print("  - Convert to a proper view or materialized view")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating view: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 