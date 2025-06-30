"""
Bond Future Option pricing and analysis using Bachelier model.

This module provides tools for:
- Pricing bond future options using the Bachelier (normal distribution) model
- Calculating comprehensive Greeks (delta, gamma, vega, theta, and higher-order)
- Converting between price and yield volatilities using Future DV01
- Generating Greek profiles across market scenarios
"""

from .pricing_engine import BondFutureOption
from .analysis import (
    solve_implied_volatility,
    calculate_all_greeks,
    generate_greek_profiles,
    analyze_bond_future_option_greeks,
    validate_refactoring
)

# Import convenience API functions
from .api import (
    calculate_implied_volatility,
    calculate_greeks,
    calculate_taylor_pnl,
    quick_analysis,
    process_option_batch,
    convert_price_to_64ths,
    convert_64ths_to_price
)

__all__ = [
    # Core classes and functions
    'BondFutureOption',
    'solve_implied_volatility',
    'calculate_all_greeks',
    'generate_greek_profiles',
    'analyze_bond_future_option_greeks',
    'validate_refactoring',
    
    # Convenience API functions
    'calculate_implied_volatility',
    'calculate_greeks',
    'calculate_taylor_pnl',
    'quick_analysis',
    'process_option_batch',
    'convert_price_to_64ths',
    'convert_64ths_to_price'
] 