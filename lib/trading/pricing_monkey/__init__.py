"""
Pricing Monkey integration for automated trading data collection.

This package provides browser automation tools for retrieving and processing
trading data from the Pricing Monkey web interface.
"""

# Automation exports
from .automation import run_pm_automation

# Retrieval exports
from .retrieval import (
    get_extended_pm_data,
    PMRetrievalError,
    get_simple_data,
    PMSimpleRetrievalError
)

# Processing exports
from .processors import (
    process_pm_for_separate_table,
    validate_pm_data,
    get_market_movement_data_df,
    SCENARIOS
)

__all__ = [
    # Automation
    'run_pm_automation',
    # Retrieval
    'get_extended_pm_data',
    'PMRetrievalError', 
    'get_simple_data',
    'PMSimpleRetrievalError',
    # Processing
    'process_pm_for_separate_table',
    'validate_pm_data',
    'get_market_movement_data_df',
    'SCENARIOS'
] 