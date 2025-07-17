#!/usr/bin/env python3
"""
Rebuild the master P&L table with all available data.

This script:
1. Drops the existing master_pnl table if it exists
2. Creates a new master_pnl table with data from:
   - positions table (P&L database)
   - spot_risk_raw and spot_risk_calculated (Spot Risk database)
   - market_prices tables (Market Prices database)
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

def rebuild_master_pnl_table():
    """Rebuild the master P&L table with current data."""
    print("=== REBUILDING MASTER P&L TABLE ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Connect to databases
    pnl_db = Path("data/output/pnl/pnl_tracker.db")
    spot_risk_db = Path("data/output/spot_risk/spot_risk.db")
    market_prices_db = Path("data/output/market_prices/market_prices.db")
    
    conn_pnl = sqlite3.connect(pnl_db)
    
    # Drop existing master table
    print("\n1. Dropping existing master_pnl table...")
    conn_pnl.execute("DROP TABLE IF EXISTS master_pnl")
    
    # Attach other databases
    print("\n2. Attaching databases...")
    conn_pnl.execute(f"ATTACH DATABASE '{spot_risk_db}' AS spot_risk")
    conn_pnl.execute(f"ATTACH DATABASE '{market_prices_db}' AS market_prices")
    
    # Create the master table
    print("\n3. Creating master_pnl table...")
    create_sql = """
    CREATE TABLE master_pnl AS
    SELECT 
        -- Primary identifier
        p.instrument_name as symbol,
        
        -- Position data
        p.position_quantity as open_position,
        p.avg_cost,
        p.total_realized_pnl,
        p.unrealized_pnl as pnl_live,
        p.last_market_price,
        p.is_option,
        p.option_strike,
        p.option_expiry,
        
        -- Spot risk prices (extracted from JSON)
        json_extract(sr.raw_data, '$.bid') as bid,
        json_extract(sr.raw_data, '$.ask') as ask,
        COALESCE(
            json_extract(sr.raw_data, '$.adjtheor'), 
            sr.midpoint_price
        ) as price,
        
        -- Market prices (these will be NULL for now)
        mp_fut.current_price as px_last_futures,
        mp_fut.prior_close as px_settle_futures,
        mp_opt.current_price as px_last_options,
        mp_opt.prior_close as px_settle_options,
        CASE 
            WHEN p.is_option = 0 THEN mp_fut.current_price
            ELSE mp_opt.current_price
        END as px_last,
        CASE 
            WHEN p.is_option = 0 THEN mp_fut.prior_close
            ELSE mp_opt.prior_close
        END as px_settle,
        
        -- P&L calculations
        CASE 
            WHEN p.is_option = 0 AND mp_fut.current_price IS NOT NULL 
            THEN p.position_quantity * (mp_fut.current_price - p.avg_cost)
            WHEN p.is_option = 1 AND mp_opt.current_price IS NOT NULL
            THEN p.position_quantity * (mp_opt.current_price - p.avg_cost)
            ELSE NULL
        END as pnl_flash,
        
        CASE 
            WHEN p.is_option = 0 AND mp_fut.prior_close IS NOT NULL 
            THEN p.position_quantity * (mp_fut.prior_close - p.avg_cost)
            WHEN p.is_option = 1 AND mp_opt.prior_close IS NOT NULL
            THEN p.position_quantity * (mp_opt.prior_close - p.avg_cost)
            ELSE NULL
        END as pnl_close,
        
        -- Risk metrics
        CASE 
            WHEN p.is_option = 0 THEN 63  -- Futures DV01
            ELSE sc.delta_F                -- Options DV01
        END as dv01,
        
        -- Greeks
        sc.delta_F as delta_f,
        sc.delta_y as delta_y,
        sc.gamma_F as gamma_f,
        sc.gamma_y as gamma_y,
        sc.speed_F as speed_f,
        sc.theta_F as theta_f,
        sc.vega_price as vega_f,
        sc.vega_y as vega_y,
        sc.implied_vol,
        
        -- Additional fields
        sr.vtexp,
        sr.expiry_date,
        
        -- Data freshness
        CURRENT_TIMESTAMP as time_updated,
        CASE 
            WHEN mp_fut.current_price IS NOT NULL OR mp_opt.current_price IS NOT NULL 
            THEN 'px_last available'
            WHEN mp_fut.prior_close IS NOT NULL OR mp_opt.prior_close IS NOT NULL 
            THEN 'px_settle available'
            ELSE 'no market prices'
        END as data_freshness,
        
        -- Debug fields
        sr.bloomberg_symbol as spot_risk_symbol,
        sc.calculation_status as greek_calc_status,
        sc.error_message as greek_error
        
    FROM positions p
    
    -- Join with spot risk data
    LEFT JOIN spot_risk.spot_risk_raw sr 
        ON p.instrument_name = sr.bloomberg_symbol
    LEFT JOIN spot_risk.spot_risk_calculated sc 
        ON sr.id = sc.raw_id
    
    -- Join with market prices
    LEFT JOIN market_prices.futures_prices mp_fut
        ON p.instrument_name = mp_fut.symbol AND p.is_option = 0
    LEFT JOIN market_prices.options_prices mp_opt
        ON p.instrument_name = mp_opt.symbol AND p.is_option = 1
    """
    
    conn_pnl.execute(create_sql)
    conn_pnl.commit()
    
    # Get summary statistics
    print("\n4. Master table created. Getting summary...")
    
    # Total records
    total_records = pd.read_sql("SELECT COUNT(*) as count FROM master_pnl", conn_pnl).iloc[0]['count']
    print(f"\nTotal records: {total_records}")
    
    # Records with spot risk data
    with_spot_risk = pd.read_sql("""
        SELECT COUNT(*) as count 
        FROM master_pnl 
        WHERE spot_risk_symbol IS NOT NULL
    """, conn_pnl).iloc[0]['count']
    print(f"Records with spot risk data: {with_spot_risk}")
    
    # Records with Greeks
    with_greeks = pd.read_sql("""
        SELECT COUNT(*) as count 
        FROM master_pnl 
        WHERE delta_f IS NOT NULL
    """, conn_pnl).iloc[0]['count']
    print(f"Records with calculated Greeks: {with_greeks}")
    
    # Records with market prices
    with_market_prices = pd.read_sql("""
        SELECT COUNT(*) as count 
        FROM master_pnl 
        WHERE px_last IS NOT NULL OR px_settle IS NOT NULL
    """, conn_pnl).iloc[0]['count']
    print(f"Records with market prices: {with_market_prices}")
    
    # Show sample data
    print("\n5. Sample records from master_pnl:")
    sample_df = pd.read_sql("""
        SELECT 
            symbol,
            is_option,
            open_position,
            avg_cost,
            price,
            dv01,
            delta_f,
            spot_risk_symbol,
            greek_calc_status
        FROM master_pnl
        LIMIT 10
    """, conn_pnl)
    print(sample_df.to_string())
    
    # Show data coverage by instrument type
    print("\n6. Data coverage by instrument type:")
    coverage_df = pd.read_sql("""
        SELECT 
            CASE WHEN is_option = 1 THEN 'Options' ELSE 'Futures' END as instrument_type,
            COUNT(*) as total_positions,
            SUM(CASE WHEN spot_risk_symbol IS NOT NULL THEN 1 ELSE 0 END) as with_spot_risk,
            SUM(CASE WHEN delta_f IS NOT NULL THEN 1 ELSE 0 END) as with_greeks,
            SUM(CASE WHEN px_last IS NOT NULL THEN 1 ELSE 0 END) as with_market_prices
        FROM master_pnl
        GROUP BY is_option
    """, conn_pnl)
    print(coverage_df.to_string())
    
    # Show positions without spot risk data
    print("\n7. Positions without spot risk data:")
    missing_df = pd.read_sql("""
        SELECT 
            symbol,
            is_option,
            open_position,
            avg_cost
        FROM master_pnl
        WHERE spot_risk_symbol IS NULL
    """, conn_pnl)
    if len(missing_df) > 0:
        print(missing_df.to_string())
    else:
        print("All positions have spot risk data!")
    
    # Show positions with spot risk but no Greeks
    print("\n8. Positions with spot risk but no Greeks:")
    no_greeks_df = pd.read_sql("""
        SELECT 
            symbol,
            is_option,
            spot_risk_symbol,
            greek_calc_status,
            greek_error
        FROM master_pnl
        WHERE spot_risk_symbol IS NOT NULL AND delta_f IS NULL
    """, conn_pnl)
    if len(no_greeks_df) > 0:
        print(no_greeks_df.to_string(max_colwidth=50))
    else:
        print("All positions with spot risk have Greeks!")
    
    # Show detailed view of all positions with their data coverage
    print("\n9. Detailed position data coverage:")
    detail_df = pd.read_sql("""
        SELECT 
            symbol,
            is_option,
            open_position,
            avg_cost,
            ROUND(price, 4) as price,
            ROUND(bid, 4) as bid,
            ROUND(ask, 4) as ask,
            ROUND(dv01, 2) as dv01,
            ROUND(delta_f, 4) as delta_f,
            CASE 
                WHEN spot_risk_symbol IS NOT NULL THEN 'Yes'
                ELSE 'No'
            END as has_spot_risk,
            CASE 
                WHEN delta_f IS NOT NULL THEN 'Yes'
                ELSE 'No'
            END as has_greeks
        FROM master_pnl
        ORDER BY is_option DESC, symbol
    """, conn_pnl)
    print(detail_df.to_string(index=False))
    
    # Close connections
    conn_pnl.close()
    
    print("\n=== MASTER P&L TABLE REBUILD COMPLETE ===")

if __name__ == "__main__":
    rebuild_master_pnl_table() 