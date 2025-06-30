"""
Unified API for Bond Future Options calculations.

This module provides simple, consistent interfaces for common calculations
without requiring deep knowledge of the package structure. All functions
handle model instantiation internally and provide sensible defaults.

Example usage:
    >>> from lib.trading.bond_future_options.api import calculate_implied_volatility, calculate_greeks
    >>> vol = calculate_implied_volatility(110.75, 110.5, 0.05, 0.359375)
    >>> greeks = calculate_greeks(110.75, 110.5, 0.05, vol)
"""

import numpy as np
from typing import Dict, Optional, Union, List, Tuple
from .pricing_engine import BondFutureOption
from .analysis import solve_implied_volatility as _solve_implied_volatility
from .analysis import calculate_all_greeks as _calculate_all_greeks
from .greek_validator import GreekPnLValidator
from .bachelier_greek import generate_greek_profiles_data, generate_taylor_error_data


# Default bond future parameters (10-year Treasury note futures typical values)
DEFAULT_FUTURE_DV01 = 0.063
DEFAULT_FUTURE_CONVEXITY = 0.002404
DEFAULT_YIELD_LEVEL = 0.05


def calculate_implied_volatility(
    F: float,
    K: float, 
    T: float,
    market_price: float,
    option_type: str = 'put',
    future_dv01: float = DEFAULT_FUTURE_DV01,
    future_convexity: float = DEFAULT_FUTURE_CONVEXITY,
    yield_level: float = DEFAULT_YIELD_LEVEL,
    initial_guess: float = 100.0,
    tolerance: float = 1e-9,
    suppress_output: bool = True
) -> float:
    """
    Calculate implied volatility from market price using Newton-Raphson method.
    
    Args:
        F: Future price
        K: Strike price
        T: Time to expiry in years
        market_price: Market price of the option (in decimal, not 64ths)
        option_type: 'call' or 'put' (default: 'put')
        future_dv01: DV01 of the bond future (default: 0.063)
        future_convexity: Convexity of the bond future (default: 0.002404)
        yield_level: Current yield level (default: 0.05)
        initial_guess: Initial volatility guess (default: 100.0)
        tolerance: Convergence tolerance (default: 1e-9)
        suppress_output: Whether to suppress iteration output (default: True)
        
    Returns:
        float: Implied price volatility
        
    Example:
        >>> vol = calculate_implied_volatility(110.75, 110.5, 0.05, 0.359375)
        >>> print(f"Implied volatility: {vol:.2f}")
    """
    # Create option model
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Solve for implied volatility
    if suppress_output:
        # Temporarily redirect stdout to suppress iteration output
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            price_volatility, _ = _solve_implied_volatility(
                option_model, F, K, T, market_price, option_type, 
                initial_guess, tolerance
            )
        finally:
            sys.stdout = old_stdout
    else:
        price_volatility, _ = _solve_implied_volatility(
            option_model, F, K, T, market_price, option_type,
            initial_guess, tolerance
        )
    
    return price_volatility


def calculate_greeks(
    F: float,
    K: float,
    T: float,
    volatility: float,
    option_type: str = 'put',
    future_dv01: float = DEFAULT_FUTURE_DV01,
    future_convexity: float = DEFAULT_FUTURE_CONVEXITY,
    yield_level: float = DEFAULT_YIELD_LEVEL,
    return_scaled: bool = True
) -> Dict[str, float]:
    """
    Calculate all Greeks for a bond future option.
    
    Args:
        F: Future price
        K: Strike price
        T: Time to expiry in years
        volatility: Price volatility
        option_type: 'call' or 'put' (default: 'put')
        future_dv01: DV01 of the bond future (default: 0.063)
        future_convexity: Convexity of the bond future (default: 0.002404)
        yield_level: Current yield level (default: 0.05)
        return_scaled: If True, returns Greeks with standard scaling (default: True)
                      - delta_F: not scaled
                      - delta_y, gamma_y, vega_y, theta_F, etc.: scaled by 1000
        
    Returns:
        Dict[str, float]: Dictionary of Greek values
        
    Example:
        >>> greeks = calculate_greeks(110.75, 110.5, 0.05, 75.5)
        >>> print(f"Delta: {greeks['delta_y']:.2f}, Gamma: {greeks['gamma_y']:.2f}")
    """
    # Create option model
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Calculate all Greeks using existing function
    greeks = _calculate_all_greeks(option_model, F, K, T, volatility, option_type)
    
    # If user wants unscaled values, remove the scaling
    if not return_scaled:
        # Create a copy to avoid modifying the original
        unscaled_greeks = {}
        for key, value in greeks.items():
            if key == 'delta_F':
                # delta_F is never scaled
                unscaled_greeks[key] = value
            elif key in ['delta_y', 'gamma_y', 'vega_y', 'theta_F', 'volga_price', 
                        'vanna_F_price', 'charm_F', 'speed_F', 'color_F', 'ultima', 'zomma']:
                # These are scaled by 1000 in the original
                unscaled_greeks[key] = value / 1000.0
            else:
                # Other Greeks (gamma_F, vega_price, vomma_F) are not scaled
                unscaled_greeks[key] = value
        return unscaled_greeks
    
    return greeks


def calculate_taylor_pnl(
    F: float,
    K: float,
    T: float,
    volatility: float,
    dF: Union[float, np.ndarray],
    dSigma: Union[float, np.ndarray],
    dT: Union[float, np.ndarray],
    option_type: str = 'put',
    order: int = 2,
    future_dv01: float = DEFAULT_FUTURE_DV01,
    future_convexity: float = DEFAULT_FUTURE_CONVEXITY,
    yield_level: float = DEFAULT_YIELD_LEVEL
) -> Union[float, np.ndarray]:
    """
    Calculate Taylor series PnL approximation for given market shocks.
    
    Args:
        F: Future price
        K: Strike price
        T: Time to expiry in years
        volatility: Price volatility
        dF: Change in future price (scalar or array)
        dSigma: Change in volatility (scalar or array)
        dT: Change in time (scalar or array, typically negative for time decay)
        option_type: 'call' or 'put' (default: 'put')
        order: Taylor expansion order (0, 1, 2, or 3) (default: 2)
        future_dv01: DV01 of the bond future (default: 0.063)
        future_convexity: Convexity of the bond future (default: 0.002404)
        yield_level: Current yield level (default: 0.05)
        
    Returns:
        Union[float, np.ndarray]: Predicted PnL (scalar or array matching input)
        
    Example:
        >>> pnl = calculate_taylor_pnl(110.75, 110.5, 0.05, 75.5, dF=0.1, dSigma=0.5, dT=-1/252)
        >>> print(f"Predicted PnL: {pnl:.6f}")
    """
    # Create option model
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Calculate Greeks at current point
    greeks = _calculate_all_greeks(option_model, F, K, T, volatility, option_type)
    
    # Create validator instance
    validator = GreekPnLValidator(option_model)
    
    # Convert scalars to arrays if needed
    dF = np.atleast_1d(dF)
    dSigma = np.atleast_1d(dSigma)
    dT = np.atleast_1d(dT)
    
    # Calculate Taylor PnL
    pnl = validator.calculate_taylor_pnl(greeks, dF, dSigma, dT, order=order)
    
    # Return scalar if input was scalar
    if pnl.shape == (1,):
        return float(pnl[0])
    return pnl


def quick_analysis(
    F: float,
    K: float,
    T: float,
    market_price: float,
    option_type: str = 'put',
    future_dv01: float = DEFAULT_FUTURE_DV01,
    future_convexity: float = DEFAULT_FUTURE_CONVEXITY,
    yield_level: float = DEFAULT_YIELD_LEVEL
) -> Dict:
    """
    Perform complete analysis: implied volatility, Greeks, and risk metrics.
    
    Args:
        F: Future price
        K: Strike price
        T: Time to expiry in years
        market_price: Market price of the option (in decimal, not 64ths)
        option_type: 'call' or 'put' (default: 'put')
        future_dv01: DV01 of the bond future (default: 0.063)
        future_convexity: Convexity of the bond future (default: 0.002404)
        yield_level: Current yield level (default: 0.05)
        
    Returns:
        Dict containing:
            - 'implied_volatility': Price volatility
            - 'yield_volatility': Yield volatility
            - 'greeks': Dictionary of all Greeks (scaled)
            - 'risk_metrics': Common risk calculations
            
    Example:
        >>> analysis = quick_analysis(110.75, 110.5, 0.05, 0.359375)
        >>> print(f"Volatility: {analysis['implied_volatility']:.2f}")
        >>> print(f"Delta: {analysis['greeks']['delta_y']:.2f}")
    """
    # Create option model
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Calculate implied volatility
    implied_vol = calculate_implied_volatility(
        F, K, T, market_price, option_type,
        future_dv01, future_convexity, yield_level,
        suppress_output=True
    )
    
    # Calculate yield volatility
    yield_vol = option_model.convert_price_to_yield_volatility(implied_vol)
    
    # Calculate all Greeks
    greeks = calculate_greeks(
        F, K, T, implied_vol, option_type,
        future_dv01, future_convexity, yield_level,
        return_scaled=True
    )
    
    # Calculate some common risk metrics
    risk_metrics = {
        # Dollar risk for 1bp move
        'dollar_delta_1bp': greeks['delta_y'] / 1000.0,  # Remove scaling
        
        # Dollar gamma risk for 1bp move
        'dollar_gamma_1bp': greeks['gamma_y'] / 1000.0,  # Remove scaling
        
        # Daily theta
        'daily_theta': greeks['theta_F'] / 1000.0,  # Already daily, remove scaling
        
        # Vega for 1 vol point
        'vega_1vol': greeks['vega_y'] / 1000.0,  # Remove scaling
        
        # Option moneyness
        'moneyness': (F - K) / F,
        
        # Time value
        'intrinsic_value': max(0, F - K) if option_type == 'call' else max(0, K - F),
        'time_value': market_price - (max(0, F - K) if option_type == 'call' else max(0, K - F))
    }
    
    return {
        'implied_volatility': implied_vol,
        'yield_volatility': yield_vol,
        'greeks': greeks,
        'risk_metrics': risk_metrics,
        'inputs': {
            'F': F,
            'K': K,
            'T': T,
            'market_price': market_price,
            'option_type': option_type
        }
    }


def process_option_batch(
    options_data: List[Dict],
    future_dv01: float = DEFAULT_FUTURE_DV01,
    future_convexity: float = DEFAULT_FUTURE_CONVEXITY,
    yield_level: float = DEFAULT_YIELD_LEVEL,
    suppress_output: bool = True
) -> List[Dict]:
    """
    Process a batch of options, calculating volatility and Greeks for each.
    
    Args:
        options_data: List of dictionaries, each containing:
            - 'F': Future price
            - 'K': Strike price
            - 'T': Time to expiry in years
            - 'market_price': Market price (decimal)
            - 'option_type': 'call' or 'put' (optional, default: 'put')
        future_dv01: DV01 of the bond future (default: 0.063)
        future_convexity: Convexity of the bond future (default: 0.002404)
        yield_level: Current yield level (default: 0.05)
        suppress_output: Whether to suppress iteration output (default: True)
        
    Returns:
        List[Dict]: Original data with added 'volatility' and 'greeks' fields
        
    Example:
        >>> options = [
        ...     {'F': 110.75, 'K': 110.5, 'T': 0.05, 'market_price': 0.359375},
        ...     {'F': 110.75, 'K': 111.0, 'T': 0.05, 'market_price': 0.453125}
        ... ]
        >>> results = process_option_batch(options)
        >>> for opt in results:
        ...     print(f"Strike {opt['K']}: Vol={opt['volatility']:.2f}, Delta={opt['greeks']['delta_y']:.2f}")
    """
    results = []
    
    for option in options_data:
        # Extract required fields
        F = option['F']
        K = option['K']
        T = option['T']
        market_price = option['market_price']
        option_type = option.get('option_type', 'put')
        
        # Calculate implied volatility
        try:
            implied_vol = calculate_implied_volatility(
                F, K, T, market_price, option_type,
                future_dv01, future_convexity, yield_level,
                suppress_output=suppress_output
            )
            
            # Calculate Greeks
            greeks = calculate_greeks(
                F, K, T, implied_vol, option_type,
                future_dv01, future_convexity, yield_level,
                return_scaled=True
            )
            
            # Create result dictionary with original data plus calculations
            result = option.copy()
            result['volatility'] = implied_vol
            result['greeks'] = greeks
            result['success'] = True
            
        except Exception as e:
            # If calculation fails, add error information
            result = option.copy()
            result['volatility'] = None
            result['greeks'] = None
            result['success'] = False
            result['error'] = str(e)
        
        results.append(result)
    
    return results


def convert_price_to_64ths(decimal_price: float) -> float:
    """Convert decimal price to 64ths."""
    return decimal_price * 64.0


def convert_64ths_to_price(price_64ths: float) -> float:
    """Convert price in 64ths to decimal."""
    return price_64ths / 64.0 