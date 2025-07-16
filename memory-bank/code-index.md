# Code Index

## Core Libraries

### lib/trading/symbol_translator.py
Translates Actant proprietary format symbols to Bloomberg format. Maps option series codes (VY→VBY Monday, TJ→TJP Tuesday, etc.) and calculates weekday occurrences. Handles both options (e.g., XCMEOCADPS20250714N0VY2/110.75 → VBYN25C2 110.750 Comdty) and futures (e.g., XCMEFFDPSX20250919U0ZN → TYU5 Comdty).

### lib/trading/pnl_calculator/storage.py
Database interface for P&L tracking system. Manages trades, positions, market prices, and snapshots. Key methods: save_processed_trades(), save_market_prices(), get_market_price(), get_positions(), create_eod_snapshot(). Includes _map_to_bloomberg() which uses SymbolTranslator for instrument mapping. Updated get_market_price() to use flexible timestamp lookup instead of exact hour matching.

### lib/trading/pnl_calculator/calculator.py
Core P&L calculation engine implementing FIFO methodology. Handles futures and options with different precision (5 decimal for futures, 4 for options). Methods: calculate_pnl_for_trades(), calculate_position_pnl(), calculate_realized_pnl(), calculate_unrealized_pnl(). Processes exercise assignments and manages rounding for display.

### lib/trading/pnl_calculator/trade_preprocessor.py
Processes raw trade CSV files into standardized format. Monitors data/input/trade_ledger/ directory, tracks processing state, handles duplicates, and manages transaction types (BUY/SELL/EXERCISE). Integrates with PnLCalculator and PositionManager for real-time updates.

### lib/trading/pnl_calculator/service.py
Main service orchestrating P&L tracking components. Manages file watchers, coordinates trade processing, price updates, and position calculations. Methods: start(), stop(), process_pending_files(), get_current_positions(). Implements singleton pattern for global access.

### lib/trading/pnl_calculator/unified_service.py
Higher-level service wrapping PnLService with additional data aggregation. Provides clean API for UI: get_open_positions(), get_trade_history(), get_daily_pnl_history(). Manages component lifecycle and formats data for display.

### lib/trading/pnl_calculator/position_manager.py
Manages real-time position tracking with FIFO methodology. Processes trades, updates positions, calculates P&L, and integrates market prices. Key methods: process_trade(), update_positions(), update_market_prices(). Handles option exercise assignments specially.

### lib/trading/pnl_calculator/price_processor.py
Processes market price CSV files from Bloomberg. Handles futures and options directories separately. Validates and normalizes price data before storage. Integrates with PnLStorage for database operations.

## Dashboard Applications

### apps/dashboards/pnl_v2/
New P&L tracking dashboard with real-time updates. Components:
- app.py: Main layout with 4 tabs (Open Positions, Trade Ledger, Daily P&L, P&L Chart)
- views.py: Individual tab components and data tables
- controller.py: Singleton managing UnifiedPnLService instance
- callbacks.py: Real-time update callbacks on 5-second intervals

### lib/trading/pnl_integration/
New integration package for TYU5 P&L engine (replacing pnl_calculator). Components:
- tyu5_adapter.py: Adapter querying UIKitXv2 data stores and formatting for TYU5 engine
- tyu5_service.py: Service layer managing calculations, monitoring, and output generation
- Direct database to TYU5 path, bypassing old pnl_calculator entirely

## Recent Updates
- Created new pnl_integration package for clean separation from old code
- TYU5 adapter queries cto_trades and price tables directly
- All prices remain decimal throughout (no 32nds conversion)
- Test script at scripts/test_tyu5_integration.py for validation 