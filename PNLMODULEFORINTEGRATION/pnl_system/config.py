"""
PnL Calculation System Configuration

Purpose: Centralized configuration for the P&L calculation system
"""

# Database configuration
DB_NAME = 'trades.db'

# Verbose mode for debugging (can be enabled for testing)
VERBOSE = False

# Table names
TRADES_TABLES = ['trades_fifo', 'trades_lifo']
REALIZED_TABLES = ['realized_fifo', 'realized_lifo']
ALL_TABLES = TRADES_TABLES + REALIZED_TABLES + ['pricing', 'daily_positions']

# Trading methods
METHODS = ['fifo', 'lifo']

# P&L multiplier for proper scaling
PNL_MULTIPLIER = 1000

# Default symbol if none found in trades
DEFAULT_SYMBOL = 'XCMEFFDPSX20250919U0ZN' 