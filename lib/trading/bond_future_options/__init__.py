"""Bond Future Options pricing package using the Bachelier model."""

# Core pricing engine
from .pricing_engine import BondFutureOption

# API functions
from .api import (
    calculate_implied_volatility,
    calculate_greeks,
    calculate_taylor_pnl,
    quick_analysis,
    process_option_batch,
    convert_price_to_64ths,
    convert_64ths_to_price
)

# Analysis functions
from .analysis import (
    analyze_bond_future_option_greeks,
    solve_implied_volatility,
    calculate_all_greeks
)

# Greek profiles
from .bachelier_greek import (
    generate_greek_profiles_data,
    generate_taylor_error_data
)

# Factory/Facade pattern (new)
from .greek_calculator_api import GreekCalculatorAPI
from .model_factory import ModelFactory
from .models import BachelierV1

__all__ = [
    # Core
    'BondFutureOption',
    
    # API
    'calculate_implied_volatility',
    'calculate_greeks',
    'calculate_taylor_pnl',
    'quick_analysis',
    'process_option_batch',
    'convert_price_to_64ths',
    'convert_64ths_to_price',
    
    # Analysis
    'analyze_bond_future_option_greeks',
    'solve_implied_volatility',
    'calculate_all_greeks',
    
    # Greek profiles
    'generate_greek_profiles_data',
    'generate_taylor_error_data',
    
    # Factory/Facade
    'GreekCalculatorAPI',
    'ModelFactory',
    'BachelierV1'
] 