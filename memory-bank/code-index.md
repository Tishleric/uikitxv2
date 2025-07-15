# Code Index

## Core Libraries

### lib/trading/symbol_translator.py
Core module for translating between Actant and Bloomberg symbol formats. Handles CME options (with day-of-month occurrence calculation for weekly expiries) and futures contracts. Options format includes series-to-weekday mapping (VY=Mon, TJ=Tue, etc.) and formats strikes with 3 decimal places. Futures use product mappings (ZN→TY, TU→TU, etc.).

### lib/trading/pnl_calculator/trade_preprocessor.py
Processes raw trade ledger files: translates Actant symbols to Bloomberg format, detects SOD positions (midnight trades), detects option expiries (zero price), converts Buy/Sell to signed quantities, adds validation status. Tracks file size/modification time to avoid reprocessing unchanged files. Outputs to data/output/trade_ledger_processed/.

### lib/trading/pnl_calculator/trade_file_watcher.py
Monitors trade ledger input directory using watchdog library. Handles file modification events (for growing files) and creation events. Implements 4pm CDT cutover logic for active trade files. Integrates with TradePreprocessor to automatically process files as they change.

### lib/trading/pnl_calculator/price_file_selector.py
Intelligent market price file selection based on timestamp and file type. Implements time windows: 2pm window (1:45-2:30pm CDT) uses PX_LAST, 4pm window (3:45-4:30pm CDT) uses PX_SETTLE. Ignores 3pm files completely. Falls back to most recent valid file if no files match current time window.

### lib/trading/pnl_calculator/calculator.py
Core P&L calculation engine. Calculates unrealized and realized P&L with proper FIFO/average cost tracking. Handles position management, trade processing, and market price updates. Integrates with storage layer for persistence.

### lib/trading/pnl_calculator/service.py
Service layer that coordinates between calculator, storage, and external interfaces. Manages transaction boundaries, handles batch operations, and provides high-level P&L operations.

### lib/trading/pnl_calculator/storage.py
SQLite-based storage for trades, positions, and P&L data. Implements schema with proper indexes and foreign keys. Handles data persistence and retrieval with transaction support.

### lib/trading/pnl_calculator/controller.py
High-level controller that orchestrates the P&L system. Manages file watchers, coordinates updates, and provides interface for UI callbacks. Handles initialization and cleanup of resources.

### lib/trading/pnl_calculator/watcher.py
Base file watcher implementation for monitoring CSV files. Provides debouncing to prevent rapid events and handles both creation and modification events. Used by trade and price file monitoring.

## Dashboard Applications

### apps/dashboards/pnl/app.py
Main P&L dashboard application. Provides real-time P&L tracking with position views, trade history, and performance metrics. Integrates with the P&L calculator system.

### apps/dashboards/pnl/callbacks.py
Callback implementations for P&L dashboard. Handles user interactions, data updates, and real-time refresh logic. Coordinates with PnLController for data operations.

### apps/dashboards/spot_risk/app.py
Spot Risk dashboard for monitoring options risk metrics. Displays position Greeks, model parameters, and risk analytics with real-time updates.

### apps/dashboards/actant_eod/app.py
End-of-day processing dashboard for Actant data. Handles EOD calculations, position reconciliation, and report generation.

### apps/dashboards/actant_preprocessing/app.py
Data preprocessing dashboard for cleaning and validating Actant trade data before analysis.

### apps/dashboards/observatory/app.py
System monitoring dashboard that displays logs, metrics, and system health information from decorated functions.

### apps/dashboards/main/app.py
Main entry point dashboard that provides navigation to all other dashboards and system status overview.

## Scripts

### scripts/run_trade_preprocessor.py
Standalone script to run the trade preprocessor with file watching. Supports both watch mode (continuous monitoring) and process-only mode (one-time processing). Configurable input/output directories.

### scripts/test_trade_preprocessor.py
Test script for trade preprocessor functionality. Verifies symbol translation, SOD detection, expiry detection, and file change tracking. Displays detailed results and examples.

### scripts/test_phase1_integration_fixed.py
Integration test for Phase 1 P&L implementation. Tests symbol translation (100% success), price lookup (86.4% success), and trade preprocessing. Handles both options and futures with proper base symbol mapping for futures prices.

### scripts/test_price_selection_scenarios.py
Tests intelligent price file selection logic across different time windows and scenarios. Verifies correct PX_LAST/PX_SETTLE selection based on timestamps.

## Trading Libraries

### lib/trading/actant/spot_risk/file_watcher.py
Specialized file watcher for Spot Risk CSV processing. Handles daily subfolder structure and maintains processing state. Integrates with Spot Risk parser for automatic processing.

### lib/trading/bond_future_options/factory.py
Factory for creating bond future option calculators with proper configuration for different products.

### lib/trading/bond_future_options/greeks.py
Greek calculation implementations for bond future options including delta, gamma, vega, theta, and rho.

## Data Files

### data/input/trade_ledger/
Input directory for raw trade CSV files. Files grow throughout the day and switch to next day at 4pm CDT.

### data/output/trade_ledger_processed/
Output directory for processed trade files with Bloomberg symbols, validation status, and metadata.

### data/input/market_prices/
Market price CSV files in Options_YYYYMMDD_HHMM.csv format. Contains PX_LAST and PX_SETTLE columns.

### data/output/pnl/
P&L database and related output files including calculation results and audit trails. 