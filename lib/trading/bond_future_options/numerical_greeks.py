"""
Numerical Greeks calculation for Bond Future Options using finite differences.

This module provides numerical approximations of option Greeks up to 3rd order
using adaptive finite difference methods. It's designed to work alongside the
analytical Greeks in analysis.py for validation and extended Greek calculation.
"""

import numpy as np
import time
from typing import Dict, Callable, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Greek name mapping from numerical to analytical naming convention
GREEK_NAME_MAPPING = {
    # First order
    'delta': 'delta_F',         # ∂V/∂F
    'vega': 'vega_price',      # ∂V/∂σ (price volatility)
    'theta': 'theta_F',        # ∂V/∂t
    
    # Second order
    'gamma': 'gamma_F',        # ∂²V/∂F²
    'vomma': 'volga_price',    # ∂²V/∂σ² (called volga in bond futures)
    'vanna': 'vanna_F_price',  # ∂²V/∂F∂σ
    'charm': 'charm_F',        # ∂²V/∂F∂t (renamed from original code's conflict)
    
    # Third order (no analytical equivalents)
    'speed': 'speed_F',        # ∂³V/∂F³
    'ultima': 'ultima',        # ∂³V/∂σ³
    'color': 'color_F',        # ∂³V/∂t³ (∂²gamma/∂t)
    'zomma': 'zomma',         # ∂³V/∂F²∂σ
}

# Greek display order
GREEK_ORDER = [
    # 1st order
    'delta_F', 'gamma_F', 'vega_price', 'theta_F',
    # 2nd order  
    'volga_price', 'vanna_F_price', 'charm_F',
    # 3rd order
    'speed_F', 'color_F', 'zomma', 'ultima'
]

# Greek descriptions for UI
GREEK_DESCRIPTIONS = {
    'delta_F': '∂V/∂F - Price sensitivity',
    'gamma_F': '∂²V/∂F² - Delta sensitivity', 
    'vega_price': '∂V/∂σ - Volatility sensitivity',
    'theta_F': '∂V/∂t - Time decay',
    'volga_price': '∂²V/∂σ² - Vega convexity',
    'vanna_F_price': '∂²V/∂F∂σ - Delta/Vega cross',
    'charm_F': '∂²V/∂F∂t - Delta decay',
    'speed_F': '∂³V/∂F³ - Gamma sensitivity',
    'color_F': '∂³V/∂t³ - Gamma decay',
    'zomma': '∂³V/∂F²∂σ - Gamma/Vega cross',
    'ultima': '∂³V/∂σ³ - Vomma sensitivity'
}


def compute_derivatives(f: Callable, F: float, sigma: float, t: float, 
                       h_F: Optional[float] = None, 
                       h_sigma: Optional[float] = None, 
                       h_t: Optional[float] = None,
                       suppress_output: bool = True) -> Dict[str, float]:
    """
    Compute 1st, 2nd, and 3rd derivatives using finite differences with adaptive step sizes.
    
    Parameters:
    -----------
    f : Callable
        Function that takes (F, sigma, t) as arguments and returns option price
    F : float
        Future price at which to evaluate derivatives
    sigma : float
        Price volatility at which to evaluate derivatives
    t : float
        Time to expiration at which to evaluate derivatives
    h_F : Optional[float]
        Step size for F perturbations (default: adaptive based on F)
    h_sigma : Optional[float]
        Step size for sigma perturbations (default: adaptive based on sigma)
    h_t : Optional[float]
        Step size for t perturbations (default: adaptive based on t)
    suppress_output : bool
        Whether to suppress debug output (default: True)
    
    Returns:
    --------
    Dict[str, float]
        Dictionary containing all derivatives with keys matching GREEK_NAME_MAPPING
    """
    
    # Adaptive step sizes - balanced for numerical stability
    if h_F is None:
        h_F = max(0.0001, F * 1e-5)  # Balanced: not too large, not too small
    if h_sigma is None:
        h_sigma = max(0.00001, sigma * 1e-4)  # Appropriate for volatility scale
    if h_t is None:
        h_t = max(1e-8, t * 1e-5)  # Small but stable for time
    
    if not suppress_output:
        logger.info(f"Using step sizes: h_F={h_F:.6f}, h_sigma={h_sigma:.6f}, h_t={h_t:.8f}")
    
    greeks = {}
    
    try:
        # First derivatives (The Greeks) - using parameter-specific step sizes
        greeks['delta'] = (f(F+h_F, sigma, t) - f(F-h_F, sigma, t)) / (2*h_F)
        greeks['vega'] = (f(F, sigma+h_sigma, t) - f(F, sigma-h_sigma, t)) / (2*h_sigma)
        greeks['theta'] = (f(F, sigma, t+h_t) - f(F, sigma, t-h_t)) / (2*h_t)
        
        # Second derivatives
        greeks['gamma'] = (f(F+h_F, sigma, t) - 2*f(F, sigma, t) + f(F-h_F, sigma, t)) / (h_F**2)
        greeks['vomma'] = (f(F, sigma+h_sigma, t) - 2*f(F, sigma, t) + f(F, sigma-h_sigma, t)) / (h_sigma**2)
        
        # Second cross derivatives
        greeks['vanna'] = (f(F+h_F, sigma+h_sigma, t) - f(F+h_F, sigma-h_sigma, t) - 
                          f(F-h_F, sigma+h_sigma, t) + f(F-h_F, sigma-h_sigma, t)) / (4*h_F*h_sigma)
        greeks['charm'] = (f(F+h_F, sigma, t+h_t) - f(F+h_F, sigma, t-h_t) - 
                          f(F-h_F, sigma, t+h_t) + f(F-h_F, sigma, t-h_t)) / (4*h_F*h_t)
        greeks['veta'] = (f(F, sigma+h_sigma, t+h_t) - f(F, sigma+h_sigma, t-h_t) - 
                         f(F, sigma-h_sigma, t+h_t) + f(F, sigma-h_sigma, t-h_t)) / (4*h_sigma*h_t)
        
        # Third derivatives (higher-order Greeks)
        greeks['speed'] = (f(F+2*h_F, sigma, t) - 2*f(F+h_F, sigma, t) + 
                          2*f(F-h_F, sigma, t) - f(F-2*h_F, sigma, t)) / (2*h_F**3)
        greeks['ultima'] = (f(F, sigma+2*h_sigma, t) - 2*f(F, sigma+h_sigma, t) + 
                           2*f(F, sigma-h_sigma, t) - f(F, sigma-2*h_sigma, t)) / (2*h_sigma**3)
        greeks['color'] = (f(F, sigma, t+2*h_t) - 2*f(F, sigma, t+h_t) + 
                          2*f(F, sigma, t-h_t) - f(F, sigma, t-2*h_t)) / (2*h_t**3)
        
        # Third cross derivative - zomma = ∂³V/∂F²∂σ
        vanna_plus = (f(F+h_F, sigma+h_sigma, t) - f(F+h_F, sigma-h_sigma, t) - 
                     f(F-h_F, sigma+h_sigma, t) + f(F-h_F, sigma-h_sigma, t)) / (4*h_F*h_sigma)
        vanna_minus = (f(F, sigma+h_sigma, t) - f(F, sigma-h_sigma, t) - 
                      f(F, sigma+h_sigma, t) + f(F, sigma-h_sigma, t)) / (4*h_F*h_sigma)
        # Corrected calculation for zomma using forward differences on vanna
        h_F2 = h_F  # Use same step size
        vanna_F_plus = (f(F+h_F+h_F2, sigma+h_sigma, t) - f(F+h_F+h_F2, sigma-h_sigma, t) - 
                       f(F+h_F-h_F2, sigma+h_sigma, t) + f(F+h_F-h_F2, sigma-h_sigma, t)) / (4*h_F2*h_sigma)
        vanna_F_minus = (f(F-h_F+h_F2, sigma+h_sigma, t) - f(F-h_F+h_F2, sigma-h_sigma, t) - 
                        f(F-h_F-h_F2, sigma+h_sigma, t) + f(F-h_F-h_F2, sigma-h_sigma, t)) / (4*h_F2*h_sigma)
        greeks['zomma'] = (vanna_F_plus - vanna_F_minus) / (2*h_F)
        
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        logger.warning(f"Error in numerical Greek calculation: {e}")
        # Return NaN for failed calculations
        for key in ['delta', 'vega', 'theta', 'gamma', 'vomma', 'vanna', 
                    'charm', 'veta', 'speed', 'ultima', 'color', 'zomma']:
            if key not in greeks:
                greeks[key] = np.nan
    
    return greeks


def compute_derivatives_bond_future(option_model, F: float, K: float, T: float, 
                                  price_volatility: float, option_type: str = 'put',
                                  suppress_output: bool = True) -> Tuple[Dict[str, float], float]:
    """
    Compute numerical Greeks for bond future options using the Bachelier model.
    
    This is the main interface function that wraps the option pricing model
    and returns Greeks with proper naming conventions for bond futures.
    
    Parameters:
    -----------
    option_model : BondFutureOption
        The bond future option pricing model instance
    F : float
        Current future price
    K : float
        Strike price
    T : float
        Time to expiration (in years)
    price_volatility : float
        Price volatility (not yield volatility)
    option_type : str
        'call' or 'put' (default: 'put')
    suppress_output : bool
        Whether to suppress debug output (default: True)
    
    Returns:
    --------
    Tuple[Dict[str, float], float]
        - Dictionary of Greeks with bond future naming conventions
        - Calculation time in seconds
    """
    
    start_time = time.time()
    
    # Create the pricing function lambda
    # Note: Arguments are (F, sigma, t) to match compute_derivatives signature
    pricing_function = lambda F_val, sigma_val, t_val: option_model.bachelier_future_option_price(
        F_val, K, t_val, sigma_val, option_type
    )
    
    # Compute numerical derivatives
    raw_greeks = compute_derivatives(
        pricing_function, F, price_volatility, T,
        suppress_output=suppress_output
    )
    
    # Map to bond future naming conventions
    mapped_greeks = {}
    for numerical_name, analytical_name in GREEK_NAME_MAPPING.items():
        if numerical_name in raw_greeks:
            value = raw_greeks[numerical_name]
            
            # Apply scaling consistent with analytical Greeks
            if analytical_name == 'delta_F':
                # Delta doesn't need scaling
                mapped_greeks[analytical_name] = value
            elif analytical_name == 'theta_F':
                # Theta is divided by 252 in analytical code for daily theta and scaled by 1000
                # Also, theta sign needs to be negated (∂V/∂t is positive, but theta is -∂V/∂t)
                mapped_greeks[analytical_name] = -value * 1000.0 / 252.0
            elif analytical_name == 'gamma_F':
                # Gamma_F is not scaled in analytical
                mapped_greeks[analytical_name] = value
            elif analytical_name == 'vega_price':
                # Vega_price is NOT scaled in analytical (only vega_y is scaled by 1000)
                mapped_greeks[analytical_name] = value
            elif analytical_name in ['volga_price', 'vanna_F_price', 'charm_F', 'speed_F', 'color_F']:
                # These are scaled by 1000 in the analytical code
                mapped_greeks[analytical_name] = value * 1000.0
            else:
                # Default: no scaling for other Greeks
                mapped_greeks[analytical_name] = value
    
    # Add Y-space Greeks (using DV01 conversions) if needed
    # Note: These would require the option_model.future_dv01 parameter
    
    elapsed_time = time.time() - start_time
    
    return mapped_greeks, elapsed_time


def format_greek_comparison(analytical_greeks: Dict[str, float], 
                          numerical_greeks: Dict[str, float]) -> list:
    """
    Format Greeks for display in a DataTable with comparison metrics.
    
    Parameters:
    -----------
    analytical_greeks : Dict[str, float]
        Greeks calculated analytically
    numerical_greeks : Dict[str, float]
        Greeks calculated numerically
    
    Returns:
    --------
    list
        List of dictionaries formatted for Dash DataTable
    """
    
    table_data = []
    
    for greek_name in GREEK_ORDER:
        # Get values
        analytical_val = analytical_greeks.get(greek_name, None)
        numerical_val = numerical_greeks.get(greek_name, np.nan)
        
        # Format row
        row = {
            'greek': greek_name,
            'description': GREEK_DESCRIPTIONS.get(greek_name, ''),
            'analytical': f"{analytical_val:.6f}" if analytical_val is not None else "N/A",
            'numerical': f"{numerical_val:.6f}" if not np.isnan(numerical_val) else "N/A*"
        }
        
        # Calculate difference and percentage error
        if analytical_val is not None and not np.isnan(numerical_val):
            diff = abs(analytical_val - numerical_val)
            pct_error = (diff / abs(analytical_val) * 100) if analytical_val != 0 else 0
            
            row['difference'] = f"{diff:.6f}"
            row['pct_error'] = f"{pct_error:.2f}%"
            
            # Add color coding info
            if pct_error < 0.01:
                row['_color'] = 'green'
            elif pct_error < 0.1:
                row['_color'] = 'yellow'
            else:
                row['_color'] = 'red'
        else:
            row['difference'] = "N/A"
            row['pct_error'] = "N/A"
            row['_color'] = 'none'
        
        table_data.append(row)
    
    return table_data


def create_error_table() -> list:
    """
    Create an error table when numerical calculation fails.
    
    Returns:
    --------
    list
        List with error message for DataTable
    """
    return [{
        'greek': 'Error',
        'description': 'Numerical calculation failed',
        'analytical': 'N/A',
        'numerical': 'N/A',
        'difference': 'N/A',
        'pct_error': 'N/A',
        '_color': 'none'
    }] 