-- Master Positions Table Schema
-- Purpose: Aggregate positions, P&L, and Greeks from multiple sources
-- Version: 1.0

-- Table: positions
-- Consolidates data from trades.db and spot_risk.db
CREATE TABLE IF NOT EXISTS positions (
    symbol TEXT PRIMARY KEY,
    
    -- Position data from trades.db
    open_position REAL DEFAULT 0,      -- Net position quantity (unrealized)
    closed_position REAL DEFAULT 0,    -- Cumulative closed quantity
    
    -- Greeks from spot_risk.db (spot_risk_calculated table)
    delta_y REAL,                      -- Delta in Y-space
    gamma_y REAL,                      -- Gamma in Y-space  
    speed_y REAL,                      -- Speed in Y-space (3rd order)
    theta REAL,                        -- Theta (from theta_F)
    vega REAL,                         -- Vega (from vega_y)
    
    -- P&L from trades.db (realized and calculated unrealized)
    fifo_realized_pnl REAL DEFAULT 0,
    fifo_unrealized_pnl REAL DEFAULT 0,
    lifo_realized_pnl REAL DEFAULT 0,
    lifo_unrealized_pnl REAL DEFAULT 0,
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_trade_update TIMESTAMP,       -- When trade data last changed
    last_greek_update TIMESTAMP,       -- When Greek data last changed
    
    -- Data source tracking
    has_greeks BOOLEAN DEFAULT 0,      -- Whether Greeks are available
    instrument_type TEXT,              -- 'FUTURE', 'CALL', 'PUT' from spot_risk
    
    CHECK (open_position IS NOT NULL),
    CHECK (closed_position IS NOT NULL)
);

-- Index for fast lookups and updates
CREATE INDEX IF NOT EXISTS idx_positions_updated ON positions(last_updated);
CREATE INDEX IF NOT EXISTS idx_positions_type ON positions(instrument_type);

-- Trigger to update timestamp on any change
CREATE TRIGGER IF NOT EXISTS positions_update_timestamp 
AFTER UPDATE ON positions
BEGIN
    UPDATE positions SET last_updated = CURRENT_TIMESTAMP 
    WHERE symbol = NEW.symbol;
END; 