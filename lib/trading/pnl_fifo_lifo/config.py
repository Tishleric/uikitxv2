"""
PnL Calculation System Configuration

Purpose: Centralized configuration for the P&L calculation system
"""

# Database configuration
DB_NAME = 'trades.db'  # This will be in the root folder when scripts are run

# Verbose mode for debugging (can be enabled for testing)
VERBOSE = False

# Table names
TRADES_TABLES = ['trades_fifo', 'trades_lifo']
REALIZED_TABLES = ['realized_fifo', 'realized_lifo']
ALL_TABLES = TRADES_TABLES + REALIZED_TABLES + ['pricing', 'daily_positions', 'processed_files']

# Trading methods
METHODS = ['fifo', 'lifo']

# P&L multiplier for proper scaling
PNL_MULTIPLIER = 1000

# Default symbol if none found in trades
DEFAULT_SYMBOL = 'XCMEFFDPSX20250919U0ZN' 

# File watcher directories
SPOT_RISK_INPUT_DIR = 'data/input/actant_spot_risk'
TRADE_LEDGER_INPUT_DIR = 'data/input/trade_ledger' 

# === MASTER WATCHER CONFIGURATION ===

# Close Price Watcher
CLOSE_PRICE_WATCHER = {
    'futures_dir': r'C:\Users\ceterisparibus\Documents\ProductionSpace\Trade_Control\futures',
    'options_dir': r'C:\Users\ceterisparibus\Documents\ProductionSpace\Trade_Control\options',
    'file_patterns': {
        'futures': r'Futures_(\d{8})_(\d{4})\.csv',
        'options': r'Options_(\d{8})_(\d{4})\.csv'
    },
    'expected_times': [14, 15, 16],  # 2pm, 3pm, 4pm CDT
    'roll_4pm_time': 16,  # 4pm CDT - trigger 4pm roll if all files received
    'final_roll_cutoff': 16.5,  # 4:30pm CDT - trigger 4pm roll as fallback
    'process_existing': False  # Don't process historical files
}

# Futures symbol mapping
FUTURES_SYMBOLS = {
    'TU': 'TUU5 Comdty',  # 2-year
    'FV': 'FVU5 Comdty',  # 5-year
    'TY': 'TYU5 Comdty',  # 10-year
    'US': 'USU5 Comdty',  # Ultra Bond
    'RX': 'RXU5 Comdty'   # Euro-Bund
}

# === ALL WATCHERS SUMMARY ===
# 1. ClosePriceWatcher - monitors Z:\Trade_Control for close prices
# 2. SpotRiskPriceWatcher - monitors spot risk CSVs for current prices
# 3. TradeLedgerWatcher - monitors trade ledger for new trades
# 4. PositionsWatcher - monitors database changes and updates positions table 