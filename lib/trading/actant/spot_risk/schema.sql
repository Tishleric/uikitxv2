-- Spot Risk Database Schema
-- Version: 1.0
-- Purpose: Store raw and calculated spot risk data with session management

-- Table: spot_risk_sessions
-- Tracks data loading sessions for audit and refresh management
CREATE TABLE IF NOT EXISTS spot_risk_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_refresh TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file TEXT,
    data_timestamp TEXT,  -- Timestamp from the data itself
    status TEXT DEFAULT 'active',  -- active, completed, failed
    row_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    notes TEXT
);

-- Table: spot_risk_raw
-- Stores raw data from CSV files for audit trail and reprocessing
CREATE TABLE IF NOT EXISTS spot_risk_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    instrument_key TEXT NOT NULL,
    bloomberg_symbol TEXT,  -- Translated Bloomberg symbol (nullable)
    instrument_type TEXT,  -- 'CALL', 'PUT', 'FUTURE', etc.
    expiry_date TEXT,
    strike REAL,
    midpoint_price REAL,
    vtexp REAL,  -- Time to expiry in years from vtexp CSV mapping
    raw_data TEXT NOT NULL,  -- Full row as JSON
    FOREIGN KEY (session_id) REFERENCES spot_risk_sessions(session_id)
);

-- Table: spot_risk_calculated  
-- Stores calculated Greeks and model outputs
CREATE TABLE IF NOT EXISTS spot_risk_calculated (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT NOT NULL,
    
    -- Calculated values
    implied_vol REAL,
    
    -- 1st Order Greeks
    delta_F REAL,
    delta_y REAL,
    vega_y REAL,
    vega_price REAL,
    theta_F REAL,
    rho_y REAL,
    
    -- 2nd Order Greeks  
    gamma_F REAL,
    gamma_y REAL,
    vanna_F_y REAL,
    vanna_F_price REAL,
    charm_F REAL,
    volga_y REAL,
    volga_price REAL,
    veta_y REAL,
    
    -- 3rd Order Greeks
    speed_F REAL,
    color_F REAL,
    ultima REAL,
    zomma REAL,
    
    -- Status tracking
    calculation_status TEXT NOT NULL,  -- 'success', 'failed'
    error_message TEXT,
    calculation_time_ms REAL,  -- Performance tracking
    
    FOREIGN KEY (raw_id) REFERENCES spot_risk_raw(id),
    FOREIGN KEY (session_id) REFERENCES spot_risk_sessions(session_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_raw_session ON spot_risk_raw(session_id);
CREATE INDEX IF NOT EXISTS idx_raw_instrument ON spot_risk_raw(instrument_key);
CREATE INDEX IF NOT EXISTS idx_raw_bloomberg ON spot_risk_raw(bloomberg_symbol);
CREATE INDEX IF NOT EXISTS idx_raw_type ON spot_risk_raw(instrument_type);
CREATE INDEX IF NOT EXISTS idx_raw_expiry ON spot_risk_raw(expiry_date);

CREATE INDEX IF NOT EXISTS idx_calc_session ON spot_risk_calculated(session_id);
CREATE INDEX IF NOT EXISTS idx_calc_raw ON spot_risk_calculated(raw_id);
CREATE INDEX IF NOT EXISTS idx_calc_status ON spot_risk_calculated(calculation_status);
CREATE INDEX IF NOT EXISTS idx_calc_timestamp ON spot_risk_calculated(calculation_timestamp);

-- View: latest_calculations
-- Convenience view for most recent calculations per instrument
CREATE VIEW IF NOT EXISTS latest_calculations AS
SELECT 
    r.instrument_key,
    r.bloomberg_symbol,
    r.instrument_type,
    r.expiry_date,
    r.strike,
    r.midpoint_price,
    c.*
FROM spot_risk_raw r
INNER JOIN spot_risk_calculated c ON r.id = c.raw_id
WHERE c.id IN (
    SELECT MAX(c2.id)
    FROM spot_risk_calculated c2
    GROUP BY c2.raw_id
); 