# P&L Table Data Structure Mapping

> **Implementation Note**: For a complete guide on building the master P&L table with all quirks and gotchas, see [master_pnl_table_implementation_guide.md](master_pnl_table_implementation_guide.md)

## Overview
This document provides a comprehensive mapping of data structures, processing pipelines, and storage locations for the P&L table integration project. The goal is to combine data from multiple sources (SQLite databases and CSV files) to create a unified P&L view.

## Data Sources

### 1. Trade Ledger (SQLite)
- **Database**: `data/output/pnl/pnl_tracker.db`
- **Processing**: Trade CSV files → TradePreprocessor → SQLite storage
- **Key Tables**: `cto_trades`, `positions`, `processed_trades`

### 2. Actant Spot Risk (CSV + SQLite)
- **Input Location**: `data/input/actant_spot_risk/`
- **Processing**: CSV files → SpotRiskGreekCalculator → Processed CSV files + SQLite
- **Output CSV Location**: `data/output/spot_risk/processed/`
- **Output Database**: `data/output/spot_risk/spot_risk.db`
- **Key Tables**: `spot_risk_sessions`, `spot_risk_raw`, `spot_risk_calculated`

### 3. Market Prices (SQLite)
- **Database**: `data/output/market_prices/market_prices.db`
- **Processing**: Price CSV files → PriceProcessor → SQLite storage
- **Key Tables**: `futures_prices`, `options_prices`

### 4. Time to Expiry (vtexp) Data
- **Input Location**: `data/input/vtexp/`
- **File Format**: `vtexp_YYYYMMDD_HHMMSS.csv`
- **Processing**: Most recent CSV file is read for vtexp mappings
- **Usage**: Maps to options in spot risk processing instead of calculating

## Database Schemas

### positions Table (pnl_tracker.db)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| instrument_name | TEXT UNIQUE | Trading instrument identifier |
| position_quantity | REAL | Current net position |
| avg_cost | REAL | FIFO average cost basis |
| total_realized_pnl | REAL | Cumulative realized P&L |
| unrealized_pnl | REAL | Current unrealized P&L |
| last_market_price | REAL | Last price used for unrealized calc |
| last_trade_id | TEXT | For tracking purposes |
| last_updated | DATETIME | Last update timestamp |
| is_option | BOOLEAN | True if option, False if future |
| option_strike | REAL | Strike price (options only) |
| option_expiry | DATE | Expiration date (options only) |
| has_exercised_trades | BOOLEAN | Flag for exercised options |
| created_at | DATETIME | Record creation timestamp |

### cto_trades Table (pnl_tracker.db)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| Date | DATE | Trade date |
| Time | TIME | Trade time |
| Symbol | TEXT | Bloomberg symbol (translated) |
| Action | TEXT | 'BUY' or 'SELL' |
| Quantity | INTEGER | Negative for sells |
| Price | REAL | Decimal price |
| Fees | REAL | Trading fees (default 0.0) |
| Counterparty | TEXT | Always 'FRGM' |
| tradeID | TEXT | Original trade ID from CSV (NOT UNIQUE - resets daily) |
| Type | TEXT | 'FUT' or 'OPT' |
| source_file | TEXT | Source CSV filename |
| processed_at | DATETIME | Processing timestamp |
| is_sod | BOOLEAN | Start of day flag (midnight) |
| is_exercise | BOOLEAN | Exercise flag (price = 0) |

### Actant Spot Risk CSV Format
| Column | Type | Description |
|--------|------|-------------|
| key | TEXT | Instrument identifier (e.g., XCMEOCADPS20250714N0VY2/108.75) |
| itype | TEXT | Instrument type: 'F' (future), 'C' (call), 'P' (put) |
| strike | REAL | Option strike price |
| bid | REAL | Bid price |
| ask | REAL | Ask price |
| adjtheor | REAL | Adjusted theoretical price (preferred) |
| expire_dt | TEXT | Expiration date |
| moneyness | REAL | Option moneyness |
| volume | INTEGER | Trading volume |
| open_interest | INTEGER | Open interest |
| last | REAL | Last traded price |

### vtexp CSV Format  
| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Option symbol (e.g., XCME.ZN.N.G.17JUL25) |
| vtexp | REAL | Time to expiry in years (e.g., 0.166667) |

### Processed Spot Risk CSV (with Greeks)
All columns from raw CSV plus:

| Column | Type | Description |
|--------|------|-------------|
| midpoint_price | REAL | Calculated from bid/ask or adjtheor |
| price_source | TEXT | Source of price: 'adjtheor', 'calculated', 'bid_only', etc. |
| expiry_date | DATE | Parsed from instrument key |
| vtexp | REAL | Time to expiry in years |
| implied_vol | REAL | Implied volatility |
| delta_F | REAL | Delta with respect to futures price |
| delta_y | REAL | Delta with respect to yield |
| gamma_F | REAL | Gamma with respect to futures price |
| gamma_y | REAL | Gamma with respect to yield |
| vega_price | REAL | Vega in price terms |
| vega_y | REAL | Vega in yield terms |
| theta_F | REAL | Theta with respect to futures price |
| charm_F | REAL | Charm (delta decay) |
| volga_price | REAL | Volga (vega convexity) |
| vanna_F_price | REAL | Vanna (cross-derivative) |
| speed_F | REAL | Speed (3rd order) |
| color_F | REAL | Color (3rd order) |
| ultima | REAL | Ultima (3rd order) |
| zomma | REAL | Zomma (3rd order) |

### spot_risk_sessions Table (spot_risk.db)
| Column | Type | Description |
|--------|------|-------------|
| session_id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| start_time | TIMESTAMP | Session start time |
| last_refresh | TIMESTAMP | Last refresh time |
| source_file | TEXT | Source CSV filename |
| data_timestamp | TEXT | Timestamp from the data |
| status | TEXT | 'active', 'completed', 'failed' |
| row_count | INTEGER | Number of rows processed |
| error_count | INTEGER | Number of errors |
| notes | TEXT | Additional notes |

### spot_risk_raw Table (spot_risk.db)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| session_id | INTEGER | Foreign key to sessions |
| load_timestamp | TIMESTAMP | When data was loaded |
| instrument_key | TEXT | Instrument identifier |
| instrument_type | TEXT | 'CALL', 'PUT', 'FUTURE' |
| expiry_date | TEXT | Option expiration date |
| strike | REAL | Option strike price |
| midpoint_price | REAL | Calculated price |
| raw_data | TEXT | Full row as JSON |

### spot_risk_calculated Table (spot_risk.db)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| raw_id | INTEGER | Foreign key to raw data |
| session_id | INTEGER | Foreign key to sessions |
| calculation_timestamp | TIMESTAMP | When calculated |
| model_version | TEXT | Model used |
| implied_vol | REAL | Implied volatility |
| delta_F, gamma_F, etc. | REAL | All Greek values |
| calculation_status | TEXT | 'success' or 'failed' |
| error_message | TEXT | Error details if failed |
| calculation_time_ms | REAL | Calculation duration |

## Processing Pipelines

### 1. Trade Processing Pipeline

```
Input: data/input/trade_ledger/*.csv
       ↓
1. TradeFileWatcher monitors directory
       ↓
2. TradePreprocessor.process_trade_file()
   - Symbol translation (Actant → Bloomberg)
   - SOD detection (00:00:00.000 timestamp)
   - Exercise detection (price = 0)
   - Quantity adjustment (negative for sells)
       ↓
3. PnLStorage.save_processed_trades()
   - No deduplication (trade IDs reset daily)
   - Storage in cto_trades table
       ↓
4. PositionManager.process_trade()
   - FIFO position tracking
   - Realized P&L calculation
   - Position updates
```

**Key Files**:
- Watcher: `lib/trading/pnl_calculator/file_watcher.py`
- Preprocessor: `lib/trading/pnl_calculator/trade_preprocessor.py`
- Storage: `lib/trading/pnl_calculator/storage.py`
- Position Manager: `lib/trading/pnl_calculator/position_manager.py`

### 2. Spot Risk Processing Pipeline

```
Input: data/input/actant_spot_risk/bav_analysis_YYYYMMDD_HHMMSS.csv
       ↓
1. SpotRiskWatcher monitors directory
       ↓
2. parse_spot_risk_csv()
   - Column normalization
   - Price calculation (adjtheor preferred)
   - Expiry date extraction
   - vtexp mapping from data/input/vtexp/ CSV files
       ↓
3. SpotRiskGreekCalculator.calculate_greeks()
   - Implied volatility calculation
   - Full Greeks suite computation
   - Model: Bachelier for bond futures
       ↓
4. Save processed data
   - CSV file with original data + calculated Greeks
   - SQLite storage in spot_risk.db
   - Aggregate rows for totals
```

**Key Files**:
- Watcher: `lib/trading/actant/spot_risk/file_watcher.py`
- Parser: `lib/trading/actant/spot_risk/parser.py`
- Calculator: `lib/trading/actant/spot_risk/calculator.py`
- Time Calculator: `lib/trading/actant/spot_risk/time_calculator.py`

### 3. Market Price Processing Pipeline

```
Input: data/input/market_prices/*.csv (2pm, 3pm, 4pm files)
       ↓
1. PriceFileWatcher monitors directory
       ↓
2. PriceProcessor filters by time
   - 2pm files → current_price (PX_LAST)
   - 3pm files → ignored
   - 4pm files → prior_close (PX_SETTLE)
       ↓
3. Symbol mapping and validation
       ↓
4. Storage in market_prices tables
```

**Key Files**:
- Storage: `lib/trading/market_prices/storage.py`
- Processor: Integrated with trade processing

## Symbol Translation

The `SymbolTranslator` class handles mapping between formats:

### Actant → Bloomberg Examples

**Options**:
- `XCMEOCADPS20250714N0VY2/108.75` → `VBYN25C2 108.750 Comdty`
- `XCMEOPADPS20250714N0VY2/110.75` → `VBYN25P2 110.750 Comdty`

**Futures**:
- `XCMEFFDPSX20250919U0ZN` → `TYU5 Comdty`

### Translation Logic

1. **Options**: Extract date, series code, strike from Actant format
   - Map series to Bloomberg contract (e.g., VY → VBY)
   - Calculate weekday occurrence in month
   - Format: `{Contract}{Month}{Year}{Type}{Occurrence} {Strike} Comdty`

2. **Futures**: Extract month/year codes and product
   - Map product codes (e.g., ZN → TY)
   - Format: `{Product}{Month}{YearDigit} Comdty`

**Key File**: `lib/trading/symbol_translator.py`

## P&L Calculation Components

### Required Data Points

| Field | Source | Notes |
|-------|--------|-------|
| Symbol | positions.instrument_name | Bloomberg format |
| Open Position | positions.position_quantity | Current net position |
| Closed Position | Derived from trade history | Sum of trades to zero position |
| Avg Cost | positions.avg_cost | FIFO average |
| Last Price | positions.last_market_price | From market prices |
| Bid | Spot Risk CSV | From processed files |
| Ask | Spot Risk CSV | From processed files |
| Implied Vol | Spot Risk CSV | Calculated field |
| Greeks | Spot Risk CSV | All Greek fields |
| Non Gamma LIFO PnL | To be implemented | Futures P&L |
| Gamma LIFO PnL | To be implemented | Options P&L |

### Join Strategy

**Primary Join**: `instrument_name` (positions) ↔ `key` (spot risk)
- Requires symbol translation for consistent format
- Time alignment consideration for market data freshness

## Master P&L Table Schema

### Table Definition: `master_pnl_view`

| Column | Type | Source | Logic/Notes | Phase |
|--------|------|--------|-------------|-------|
| **symbol** | TEXT | positions.instrument_name | Bloomberg format | 1 |
| **bid** | REAL | spot_risk_raw.bid | Via bloomberg_symbol join | 1 |
| **ask** | REAL | spot_risk_raw.ask | Via bloomberg_symbol join | 1 |
| **price** | REAL | spot_risk_raw.adjtheor → midpoint_price | COALESCE(adjtheor, midpoint_price) | 1 |
| **px_last** | REAL | market_prices.current_price | Available after 2pm CDT | 1 |
| **px_settle** | REAL | market_prices.prior_close | From previous day 4pm | 1 |
| **open_position** | REAL | positions.position_quantity | Current net position | 1 |
| **closed_position** | REAL | Calculated from cto_trades | When cumulative position = 0 | 2 |
| **pnl_live** | REAL | Calculated | position × (last_market_price - avg_cost) | 1 |
| **pnl_flash** | REAL | Calculated | position × (px_last - avg_cost) when available | 1 |
| **pnl_close** | REAL | Calculated | position × (px_settle - avg_cost) when available | 1 |
| **dv01** | REAL | Calculated | Options: delta_F, Futures: 63 | 1 |
| **delta_f** | REAL | spot_risk_calculated.delta_F | Delta w.r.t futures | 1 |
| **delta_y** | REAL | spot_risk_calculated.delta_y | Delta w.r.t yield | 1 |
| **gamma_f** | REAL | spot_risk_calculated.gamma_F | Gamma w.r.t futures | 1 |
| **gamma_y** | REAL | spot_risk_calculated.gamma_y | Gamma w.r.t yield | 1 |
| **speed_f** | REAL | spot_risk_calculated.speed_F | Speed w.r.t futures | 1 |
| **speed_y** | REAL | spot_risk_calculated.speed_y | Speed w.r.t yield | 1 |
| **theta_f** | REAL | spot_risk_calculated.theta_F | Theta w.r.t futures | 1 |
| **theta_y** | REAL | spot_risk_calculated.theta_y | Theta w.r.t yield | 1 |
| **vega_f** | REAL | spot_risk_calculated.vega_price | Vega in price terms | 1 |
| **vega_y** | REAL | spot_risk_calculated.vega_y | Vega w.r.t yield | 1 |
| **pnl_explained** | TEXT | To be implemented | Breakdown of P&L drivers | 4 |
| **lifo_futures** | REAL | To be implemented | LIFO P&L for futures | 3 |
| **lifo_complement_futures** | REAL | To be implemented | Remaining futures P&L | 3 |
| **lifo_gamma** | REAL | To be implemented | LIFO P&L for options | 3 |
| **lifo_complement_gamma** | REAL | To be implemented | Remaining options P&L | 3 |
| **vtexp** | REAL | spot_risk_raw.vtexp | From external mapping | 1 |
| **expiry_date** | TEXT | spot_risk_raw.expiry_date | Option expiration | 1 |
| **underlying_future** | TEXT | Derived | Extract from option symbol | 2 |
| **time_updated** | TIMESTAMP | System | CURRENT_TIMESTAMP | 1 |
| **data_freshness** | TEXT | Calculated | Status of px_last/px_settle | 1 |

### Data Source Joins

```sql
FROM positions p
LEFT JOIN spot_risk_raw sr ON p.instrument_name = sr.bloomberg_symbol
LEFT JOIN spot_risk_calculated sc ON sr.id = sc.raw_id
LEFT JOIN market_prices mp ON p.instrument_name = mp.symbol
LEFT JOIN closed_positions cp ON p.instrument_name = cp.symbol
```

### Implementation Phases

#### Phase 1: Basic Table with Available Data (Immediate)
- Implement bloomberg_symbol in spot_risk tables
- Create view with all directly available columns
- Include basic P&L calculations (live, flash, close)
- Add all Greeks in both spaces
- Include data freshness indicators

**Prerequisites**: 
- Bloomberg symbol translation in spot_risk (Chat 1)
- Understanding of existing P&L logic (Chat 2)

#### Phase 2: Closed Positions & Underlying Mapping (Week 1)
- Implement closed position calculation logic
- Add underlying future extraction for options
- Create position history tracking if needed

**Prerequisites**:
- Investigation results from Chat 2
- Clear logic for position closure detection

#### Phase 3: LIFO Implementation (Week 2)
- Design LIFO tracking tables
- Implement LIFO calculation for futures
- Implement LIFO calculation for options (gamma)
- Add complement calculations

**Prerequisites**:
- LIFO calculation methodology
- Historical trade data structure

#### Phase 4: P&L Explained (Week 3)
- Implement P&L attribution logic
- Break down P&L by market moves vs trades
- Add detailed explanatory text

**Prerequisites**:
- All other calculations complete
- Clear attribution methodology

### Technical Considerations

1. **Performance**: 
   - Create materialized view for faster queries
   - Add appropriate indexes on join columns
   - Consider partitioning by date for historical data

2. **Data Freshness**:
   - px_last updates at 2pm CDT
   - px_settle updates at 4pm CDT (for next day)
   - Spot risk updates periodically
   - Position data is real-time

3. **Symbol Mapping Requirements**:
   - bloomberg_symbol must be added to spot_risk_raw
   - Translation happens during spot risk processing
   - Failed translations should be handled gracefully

4. **View vs Table**:
   - Start with a VIEW for flexibility
   - Move to materialized view or table for performance
   - Consider real-time vs batch updates

## File Locations Summary

### Input Files
- Trade Ledger: `data/input/trade_ledger/*.csv`
- Spot Risk: `data/input/actant_spot_risk/bav_analysis_*.csv`
- Market Prices: `data/input/market_prices/*.csv`
- Time to Expiry: `data/input/vtexp/vtexp_*.csv`

### Processing Code
- Trade Processing: `lib/trading/pnl_calculator/`
- Spot Risk Processing: `lib/trading/actant/spot_risk/`
- Symbol Translation: `lib/trading/symbol_translator.py`
- Market Prices: `lib/trading/market_prices/`

### Output/Storage
- P&L Database: `data/output/pnl/pnl_tracker.db`
- Processed Spot Risk CSV: `data/output/spot_risk/processed/`
- Spot Risk Database: `data/output/spot_risk/spot_risk.db`
- Market Prices DB: `data/output/market_prices/market_prices.db`
- Monitoring DB: `data/output/monitoring/process_monitor.db`

## Notes and Considerations

1. **Time Zones**: 
   - Trade timestamps are in market time
   - Spot risk files use EST/EDT boundaries (3pm cutoff)
   - Proper timezone handling required for joins

2. **Data Freshness**:
   - Positions update real-time with trades
   - Market prices update 2-3 times daily
   - Spot risk updates periodically
   - Consider staleness when joining

3. **Symbol Mapping**:
   - Critical for joining positions with spot risk
   - Bloomberg format is the standard
   - Translation happens during trade processing

4. **P&L Calculation**:
   - FIFO method for position tracking
   - Realized P&L stored cumulatively
   - Unrealized P&L requires current market prices
   - Greeks provide risk metrics for options

5. **Edge Cases**:
   - SOD trades (midnight timestamp)
   - Exercised options (price = 0)
   - Missing market data
   - Symbol translation failures

6. **Recent Changes**:
   - **Trade Deduplication Removed**: Trade IDs are no longer unique as they reset daily. The system now accepts all trades.
   - **vtexp External Mapping**: Time to expiry values now come from external CSV files rather than being calculated.
   - **Spot Risk SQLite Storage**: Spot risk data is now stored in both CSV and SQLite formats for better querying capabilities.

## Known Issues & Required Fixes

### 1. Symbol Format Mismatch for vtexp Mapping
- **Issue**: vtexp CSV uses different symbol format than spot risk data
  - vtexp: `XCME.ZN.N.G.17JUL25`
  - spot risk: `XCME.ZN2.11JUL25.110.C`
- **Impact**: Greek calculations fail with "NoneType" errors due to missing vtexp
- **Solution**: Create mapping logic to convert between formats

### 2. Incomplete Data Population
- **Positions Table**: Currently empty (0 records)
- **Market Prices**: Not populated during repopulation script
- **Impact**: Cannot create comprehensive P&L view without position data

### 3. Symbol Translation Success
- **Fixed**: SpotRiskSymbolTranslator now handles 98.5% of symbols (6001/6092)
- **Remaining**: Only aggregate rows ("XCME.ZN") fail translation 