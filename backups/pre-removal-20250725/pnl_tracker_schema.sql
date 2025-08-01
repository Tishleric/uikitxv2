CREATE TABLE tyu5_runs (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                trades_count INTEGER,
                positions_count INTEGER,
                total_pnl REAL,
                excel_file_path TEXT,
                execution_time_seconds REAL
            );
CREATE TABLE FULLPNL_NEW (
        -- Identity columns
        symbol_tyu5 TEXT PRIMARY KEY,
        symbol_bloomberg TEXT,
        type TEXT,
        
        -- Position data from tyu5_positions
        net_quantity REAL,
        closed_quantity REAL,
        avg_entry_price REAL,
        current_price REAL,
        flash_close REAL,
        prior_close REAL,
        current_present_value REAL,
        prior_present_value REAL,
        unrealized_pnl_current REAL,
        unrealized_pnl_flash REAL,
        unrealized_pnl_close REAL,
        realized_pnl REAL,
        daily_pnl REAL,
        total_pnl REAL,
        
        -- Greeks F-space from spot_risk (NO dv01_f)
        vtexp REAL,
        delta_f REAL,
        gamma_f REAL,
        speed_f REAL,
        theta_f REAL,
        vega_f REAL,
        
        -- Greeks Y-space from spot_risk
        dv01_y REAL,
        delta_y REAL,
        gamma_y REAL,
        speed_y REAL,
        theta_y REAL,
        vega_y REAL,
        
        -- Metadata
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        spot_risk_file TEXT,
        tyu5_run_id TEXT
    );
CREATE TABLE market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bloomberg TEXT NOT NULL,                -- Bloomberg asset identifier
            asset_type TEXT NOT NULL,               -- 'FUTURE' or 'OPTION'
            px_settle REAL NOT NULL,                -- Settlement price
            px_last REAL NOT NULL,                  -- Last traded price
            px_bid REAL,                            -- Bid price
            px_ask REAL,                            -- Ask price
            opt_expire_dt TEXT,                     -- Option expiry date (options only)
            moneyness TEXT,                         -- ITM/OTM (options only)
            upload_timestamp DATETIME NOT NULL,      -- When CSV was uploaded
            upload_date DATE NOT NULL,              -- Date of upload (for grouping)
            upload_hour INTEGER NOT NULL,           -- Hour of upload (15 or 17 for 3pm/5pm)
            source_file TEXT NOT NULL,              -- Source CSV filename
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bloomberg, upload_timestamp)
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE processed_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT NOT NULL,
            instrument_name TEXT NOT NULL,
            trade_date DATE NOT NULL,
            trade_timestamp DATETIME NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            side TEXT NOT NULL,                     -- 'B' or 'S'
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_file TEXT NOT NULL
            -- Removed UNIQUE constraint to allow duplicate trade IDs from different days
        );
CREATE TABLE eod_pnl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            instrument_name TEXT NOT NULL,
            opening_position INTEGER NOT NULL,
            closing_position INTEGER NOT NULL,
            trades_count INTEGER NOT NULL,
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            total_pnl REAL NOT NULL,
            avg_buy_price REAL,
            avg_sell_price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(trade_date, instrument_name)
        );
CREATE TABLE trade_processing_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,              -- Original CSV filename
            source_row_number INTEGER NOT NULL,     -- Row number in CSV (1-based)
            trade_id TEXT NOT NULL,                 -- tradeId from CSV
            trade_timestamp DATETIME NOT NULL,      -- marketTradeTime from CSV
            instrument_name TEXT NOT NULL,          -- instrumentName from CSV
            quantity REAL NOT NULL,                 -- quantity from CSV
            price REAL NOT NULL,                    -- price from CSV
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            -- Removed UNIQUE constraint to allow duplicate trade IDs from different days
        );
CREATE TABLE cto_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date DATE NOT NULL,              -- Trade date
            Time TIME NOT NULL,              -- Trade time  
            Symbol TEXT NOT NULL,            -- Bloomberg symbol
            Action TEXT NOT NULL,            -- 'BUY' or 'SELL'
            Quantity INTEGER NOT NULL,       -- Negative for sells
            Price REAL NOT NULL,             -- Decimal price
            Fees REAL DEFAULT 0.0,           -- Trading fees
            Counterparty TEXT NOT NULL,      -- Always 'FRGM' for now
            tradeID TEXT NOT NULL,           -- Original trade ID (removed UNIQUE constraint)
            Type TEXT NOT NULL,              -- 'FUT' or 'OPT'
            
            -- Metadata
            source_file TEXT NOT NULL,       -- Source CSV filename
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Flags for edge cases
            is_sod BOOLEAN DEFAULT 0,        -- Start of day flag (midnight timestamp)
            is_exercise BOOLEAN DEFAULT 0    -- Exercise flag (price = 0)
        );
CREATE TABLE positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_name TEXT NOT NULL UNIQUE,
            position_quantity REAL NOT NULL,        -- Current net position
            avg_cost REAL NOT NULL,                 -- FIFO average cost
            total_realized_pnl REAL NOT NULL DEFAULT 0,  -- Cumulative realized P&L
            unrealized_pnl REAL NOT NULL DEFAULT 0,      -- Current unrealized P&L
            closed_quantity REAL NOT NULL DEFAULT 0,     -- Quantity closed today
            last_market_price REAL,                 -- Last price used for unrealized calc
            last_trade_id TEXT,                     -- For tracking
            last_updated DATETIME NOT NULL,
            is_option BOOLEAN NOT NULL DEFAULT 0,
            option_strike REAL,                     -- For options
            option_expiry DATE,                     -- For options
            has_exercised_trades BOOLEAN DEFAULT 0, -- Flag for exercised options
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        , short_quantity REAL NOT NULL DEFAULT 0, match_history TEXT);
CREATE TABLE position_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_type TEXT NOT NULL,            -- 'SOD' or 'EOD'
            snapshot_timestamp DATETIME NOT NULL,
            instrument_name TEXT NOT NULL,
            position_quantity REAL NOT NULL,
            avg_cost REAL NOT NULL,
            total_realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            market_price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(snapshot_type, snapshot_timestamp, instrument_name)
        );
CREATE TABLE lot_positions (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            trade_id TEXT NOT NULL,
            remaining_quantity REAL NOT NULL,
            entry_price REAL NOT NULL,
            entry_date DATETIME NOT NULL,
            position_id INTEGER REFERENCES positions(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE position_greeks (
            id INTEGER PRIMARY KEY,
            position_id INTEGER REFERENCES positions(id),
            calc_timestamp DATETIME NOT NULL,
            underlying_price REAL NOT NULL,
            implied_vol REAL,
            delta REAL,
            gamma REAL,
            vega REAL,
            theta REAL,
            speed REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE risk_scenarios (
            id INTEGER PRIMARY KEY,
            calc_timestamp DATETIME NOT NULL,
            symbol TEXT NOT NULL,
            scenario_price REAL NOT NULL,
            scenario_pnl REAL NOT NULL,
            scenario_delta REAL,
            scenario_gamma REAL,
            position_quantity REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE match_history (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            match_date DATETIME NOT NULL,
            buy_trade_id TEXT NOT NULL,
            sell_trade_id TEXT NOT NULL,
            matched_quantity REAL NOT NULL,
            buy_price REAL NOT NULL,
            sell_price REAL NOT NULL,
            realized_pnl REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE pnl_attribution (
            id INTEGER PRIMARY KEY,
            position_id INTEGER REFERENCES positions(id),
            calc_timestamp DATETIME NOT NULL,
            total_pnl REAL NOT NULL,
            delta_pnl REAL,
            gamma_pnl REAL,
            vega_pnl REAL,
            theta_pnl REAL,
            speed_pnl REAL,
            residual_pnl REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE tyu5_eod_pnl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL,
                symbol TEXT NOT NULL,
                position_quantity REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                unrealized_pnl_settle REAL NOT NULL,  -- Using px_settle
                unrealized_pnl_current REAL NOT NULL,  -- Using current 4pm price
                total_daily_pnl REAL NOT NULL,
                settlement_price REAL,  -- px_settle used
                current_price REAL,     -- 4pm price used
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, pnl_period_start TIMESTAMP, pnl_period_end TIMESTAMP, trades_in_period INTEGER DEFAULT 0,
                UNIQUE(snapshot_date, symbol)
            );
CREATE TABLE tyu5_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,  -- JSON data
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE tyu5_open_lot_snapshots (
                lot_id TEXT NOT NULL,
                settlement_key TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity_remaining REAL NOT NULL,
                entry_price REAL NOT NULL,
                entry_datetime TIMESTAMP NOT NULL,
                mark_price REAL,  -- Current price at 2pm
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lot_id, settlement_key)
            );
CREATE TABLE IF NOT EXISTS "tyu5_pnl_components" (
"lot_id" TEXT,
  "symbol" TEXT,
  "component_type" TEXT,
  "start_time" TIMESTAMP,
  "end_time" TIMESTAMP,
  "start_price" REAL,
  "end_price" REAL,
  "quantity" INTEGER,
  "pnl_amount" REAL,
  "start_settlement_key" TEXT,
  "end_settlement_key" TEXT
);
CREATE TABLE pnl_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_timestamp DATETIME NOT NULL,
            instrument_name TEXT NOT NULL,
            position INTEGER NOT NULL,
            avg_cost REAL NOT NULL,
            market_price REAL NOT NULL,
            price_source TEXT NOT NULL,             -- 'px_last' or 'px_settle'
            price_upload_time DATETIME NOT NULL,    -- When the price was uploaded
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            total_pnl REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE file_processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,                -- 'trades' or 'market_prices'
            file_size INTEGER NOT NULL,
            file_modified DATETIME NOT NULL,
            processing_status TEXT NOT NULL,        -- 'pending', 'processing', 'completed', 'error'
            error_message TEXT,
            rows_processed INTEGER,
            processing_started DATETIME,
            processing_completed DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE pnl_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calculation_timestamp DATETIME NOT NULL,
            instrument_name TEXT NOT NULL,
            calculation_type TEXT NOT NULL,         -- 'live' or 'eod'
            trades_processed INTEGER NOT NULL,
            market_price_used REAL NOT NULL,
            price_source TEXT NOT NULL,
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_market_prices_lookup 
        ON market_prices(bloomberg, upload_date, upload_hour);
CREATE INDEX idx_trade_tracker_file 
        ON trade_processing_tracker(source_file);
CREATE INDEX idx_trade_tracker_timestamp
        ON trade_processing_tracker(trade_timestamp);
CREATE INDEX idx_cto_trades_date 
        ON cto_trades(Date);
CREATE INDEX idx_cto_trades_symbol
        ON cto_trades(Symbol);
CREATE INDEX idx_position_snapshots 
        ON position_snapshots(snapshot_type, snapshot_timestamp);
CREATE INDEX idx_lot_positions_symbol 
        ON lot_positions(symbol);
CREATE INDEX idx_lot_positions_trade 
        ON lot_positions(trade_id, entry_date);
CREATE INDEX idx_position_greeks_latest 
        ON position_greeks(position_id, calc_timestamp DESC);
CREATE INDEX idx_risk_scenarios_latest 
        ON risk_scenarios(symbol, calc_timestamp DESC)
        WHERE calc_timestamp > datetime('now', '-7 days');
CREATE INDEX idx_match_history_symbol 
        ON match_history(symbol, match_date DESC);
CREATE INDEX idx_pnl_attribution_latest 
        ON pnl_attribution(position_id, calc_timestamp DESC);
CREATE INDEX idx_eod_history_date 
            ON tyu5_eod_pnl_history(snapshot_date)
        ;
CREATE INDEX idx_eod_history_symbol 
            ON tyu5_eod_pnl_history(symbol)
        ;
CREATE INDEX idx_eod_period_start 
            ON tyu5_eod_pnl_history(pnl_period_start)
        ;
CREATE INDEX idx_alerts_type_resolved 
            ON tyu5_alerts(alert_type, resolved)
        ;
CREATE INDEX idx_open_lot_snapshots_settlement_key 
            ON tyu5_open_lot_snapshots(settlement_key)
        ;
CREATE VIEW position_summary AS
        SELECT 
            p.instrument_name,
            p.position_quantity,
            p.avg_cost,
            p.unrealized_pnl,
            p.last_market_price,
            p.is_option,
            p.option_strike,
            p.option_expiry,
            p.closed_quantity,
            COUNT(t.id) as trade_count,
            MIN(t.Date) as first_trade_date,
            MAX(t.Date) as last_trade_date
        FROM positions p
        LEFT JOIN cto_trades t ON p.instrument_name = t.Symbol
        GROUP BY p.instrument_name
/* position_summary(instrument_name,position_quantity,avg_cost,unrealized_pnl,last_market_price,is_option,option_strike,option_expiry,closed_quantity,trade_count,first_trade_date,last_trade_date) */;
CREATE VIEW tyu5_latest_eod_snapshot AS
            SELECT * FROM tyu5_eod_pnl_history
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM tyu5_eod_pnl_history)
/* tyu5_latest_eod_snapshot(id,snapshot_date,symbol,position_quantity,realized_pnl,unrealized_pnl_settle,unrealized_pnl_current,total_daily_pnl,settlement_price,current_price,created_at,pnl_period_start,pnl_period_end,trades_in_period) */;
CREATE VIEW tyu5_daily_pnl_totals AS
            SELECT 
                snapshot_date,
                COUNT(DISTINCT symbol) as symbol_count,
                SUM(CASE WHEN symbol NOT LIKE '%Comdty%' THEN 0 ELSE position_quantity END) as futures_position,
                SUM(CASE WHEN symbol LIKE '%Comdty%' THEN 0 ELSE position_quantity END) as options_position,
                SUM(realized_pnl) as total_realized,
                SUM(unrealized_pnl_settle) as total_unrealized_settle,
                SUM(unrealized_pnl_current) as total_unrealized_current,
                SUM(total_daily_pnl) as total_pnl
            FROM tyu5_eod_pnl_history
            WHERE symbol != 'TOTAL'
            GROUP BY snapshot_date
/* tyu5_daily_pnl_totals(snapshot_date,symbol_count,futures_position,options_position,total_realized,total_unrealized_settle,total_unrealized_current,total_pnl) */;
CREATE VIEW tyu5_pnl_periods AS
            SELECT 
                snapshot_date as pnl_date,
                datetime(snapshot_date, '-1 day', '+14 hours') as period_start_approx,
                datetime(snapshot_date, '+14 hours') as period_end_approx,
                pnl_period_start,
                pnl_period_end,
                COUNT(CASE WHEN symbol != 'TOTAL' THEN 1 END) as position_count,
                MAX(CASE WHEN symbol = 'TOTAL' THEN total_daily_pnl END) as total_period_pnl,
                MAX(CASE WHEN symbol = 'TOTAL' THEN trades_in_period END) as trades_count
            FROM tyu5_eod_pnl_history
            GROUP BY snapshot_date
            ORDER BY snapshot_date DESC
/* tyu5_pnl_periods(pnl_date,period_start_approx,period_end_approx,pnl_period_start,pnl_period_end,position_count,total_period_pnl,trades_count) */;
CREATE VIEW tyu5_pnl_component_summary AS
            SELECT 
                symbol,
                component_type,
                COUNT(*) as component_count,
                SUM(pnl_amount) as total_pnl,
                MIN(start_time) as earliest_start,
                MAX(end_time) as latest_end,
                calculation_run_id
            FROM tyu5_pnl_components
            GROUP BY symbol, component_type, calculation_run_id
            ORDER BY symbol, component_type;
CREATE VIEW tyu5_daily_pnl_components AS
            SELECT 
                DATE(end_time) as pnl_date,
                symbol,
                component_type,
                SUM(pnl_amount) as component_pnl,
                COUNT(*) as lot_count
            FROM tyu5_pnl_components
            GROUP BY DATE(end_time), symbol, component_type
            ORDER BY pnl_date DESC, symbol
/* tyu5_daily_pnl_components(pnl_date,symbol,component_type,component_pnl,lot_count) */;
CREATE VIEW tyu5_eod_pnl_by_period AS
            SELECT 
                start_settlement_key,
                end_settlement_key,
                symbol,
                SUM(pnl_amount) as period_pnl,
                COUNT(*) as component_count,
                GROUP_CONCAT(DISTINCT component_type) as component_types
            FROM tyu5_pnl_components
            WHERE start_settlement_key IS NOT NULL 
              AND end_settlement_key IS NOT NULL
            GROUP BY start_settlement_key, end_settlement_key, symbol
/* tyu5_eod_pnl_by_period(start_settlement_key,end_settlement_key,symbol,period_pnl,component_count,component_types) */;
CREATE TABLE IF NOT EXISTS "tyu5_trades" (
"Date" TEXT,
  "Time" TEXT,
  "Symbol" TEXT,
  "Action" TEXT,
  "Quantity" REAL,
  "Price" TEXT,
  "Type" TEXT,
  "trade_id" TEXT,
  "Bloomberg_Symbol" TEXT,
  "DateTime" TEXT,
  "Realized_PNL" REAL,
  "Matches" TEXT
);
CREATE TABLE IF NOT EXISTS "tyu5_positions" (
"Symbol" TEXT,
  "Type" TEXT,
  "Net_Quantity" REAL,
  "Closed_Quantity" REAL,
  "Avg_Entry_Price" REAL,
  "Avg_Entry_Price_32nds" REAL,
  "Prior_Close" REAL,
  "Current_Price" REAL,
  "Flash_Close" REAL,
  "Prior_Present_Value" REAL,
  "Current_Present_Value" REAL,
  "Unrealized_PNL" REAL,
  "Unrealized_PNL_Current" REAL,
  "Unrealized_PNL_Flash" REAL,
  "Unrealized_PNL_Close" REAL,
  "Daily_PNL" REAL,
  "Realized_PNL" REAL,
  "Total_PNL" REAL
);
CREATE TABLE IF NOT EXISTS "tyu5_summary" (
"Metric" TEXT,
  "Value" REAL,
  "Details" TEXT
);
CREATE TABLE IF NOT EXISTS "tyu5_risk_matrix" (
"Position_ID" TEXT,
  "TYU5_Price" REAL,
  "TYU5_Price_32nds" TEXT,
  "Price_Change" REAL,
  "Scenario_PNL" REAL
);
CREATE TABLE IF NOT EXISTS "tyu5_position_breakdown" (
"Symbol" TEXT,
  "Label" TEXT,
  "Description" TEXT,
  "Quantity" REAL,
  "Price" TEXT,
  "Daily_PNL" TEXT,
  "Type" TEXT,
  "Inception_PNL" REAL,
  "Notes" TEXT
);
CREATE TABLE FULLPNL (
            -- Identity columns
            symbol_tyu5 TEXT PRIMARY KEY,
            symbol_bloomberg TEXT,
            type TEXT,
            
            -- Position data from tyu5_positions
            net_quantity REAL,
            closed_quantity REAL,
            avg_entry_price REAL,
            current_price REAL,
            flash_close REAL,
            prior_close REAL,
            current_present_value REAL,
            prior_present_value REAL,
            unrealized_pnl_current REAL,
            unrealized_pnl_flash REAL,
            unrealized_pnl_close REAL,
            realized_pnl REAL,
            daily_pnl REAL,
            total_pnl REAL,
            
            -- Greeks F-space from spot_risk (no dv01_f - use delta_f for futures DV01)
            vtexp REAL,
            delta_f REAL,
            gamma_f REAL,
            speed_f REAL,
            theta_f REAL,
            vega_f REAL,
            
            -- Greeks Y-space from spot_risk
            dv01_y REAL,
            delta_y REAL,
            gamma_y REAL,
            speed_y REAL,
            theta_y REAL,
            vega_y REAL,
            
            -- Metadata
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            spot_risk_file TEXT,
            tyu5_run_id TEXT
        );
