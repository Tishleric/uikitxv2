"""
Standalone bond option pricing module for volatility comparison.
Extracted from the main project's bond future options pricing engine.
"""

import numpy as np
import re
from typing import Optional
from scipy.stats import norm


def parse_treasury_price(price_str: str) -> Optional[float]:
    """
    Parse treasury price from various formats.
    
    Handles formats like:
    - "110-08.5" (110 and 8.5/32)
    - "110-08.75" (110 and 8.75/32)
    - "110-08" (110 and 8/32)
    
    Args:
        price_str: Price string to parse
        
    Returns:
        Decimal price value, or None if parsing fails
    """
    if not price_str:
        return None
        
    # Remove any whitespace
    price_str = price_str.strip()
    
    # Try to match the treasury format (e.g., "110-08.5")
    match = re.match(r'^(\d+)-(\d+)(?:\.(\d+))?$', price_str)
    if not match:
        return None
        
    try:
        whole_points = int(match.group(1))
        thirty_seconds_part = int(match.group(2))
        fraction_str = match.group(3) or "0"
        
        # Convert fractional part to its decimal value
        if len(fraction_str) == 1:
            fraction_as_decimal = int(fraction_str) / 10.0
        elif len(fraction_str) == 2:
            fraction_as_decimal = int(fraction_str) / 100.0
        else:
            fraction_as_decimal = int(fraction_str) / (10 ** len(fraction_str))
            
        # Convert to decimal price
        decimal_price = whole_points + (thirty_seconds_part + fraction_as_decimal) / 32.0
        return decimal_price
        
    except (ValueError, AttributeError):
        return None


class BondFutureOption:
    """Bond future option pricing model using Bachelier (normal) distribution."""
    
    def __init__(self, future_dv01, future_convexity, yield_level):
        """
        Initialize bond future option pricing model.
        
        Args:
            future_dv01: DV01 of the underlying bond future
            future_convexity: Convexity of the underlying bond future
            yield_level: Current yield level (for conversion calculations)
        """
        self.future_dv01 = future_dv01
        self.future_convexity = future_convexity
        self.yield_level = yield_level

    def bachelier_future_option_price(self, F, K, T, vol, option_type='call'):
        """Calculate option price using Bachelier (normal) model for futures."""
        sqrt_T = np.sqrt(T)
        
        # Standard normal CDF
        def N(x):
            return norm.cdf(x)
        
        # Standard normal PDF
        def n(x):
            return norm.pdf(x)
        
        d = (F - K) / (vol * sqrt_T)
        
        if option_type.lower() == 'call':
            price = (F - K) * N(d) + vol * sqrt_T * n(d)
        elif option_type.lower() == 'put':
            price = (K - F) * N(-d) + vol * sqrt_T * n(d)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
            
        return price

    def delta_F(self, F, K, T, vol, option_type='call'):
        """Calculate delta with respect to future price."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        
        if option_type.lower() == 'call':
            return norm.cdf(d)
        elif option_type.lower() == 'put':
            return norm.cdf(d) - 1
        else:
            raise ValueError("option_type must be 'call' or 'put'")

    def delta_y(self, F, K, T, vol, option_type='call'):
        """Calculate delta with respect to yield."""
        delta_F_val = self.delta_F(F, K, T, vol, option_type)
        return -delta_F_val * self.future_dv01

    def gamma_y(self, F, K, T, vol):
        """Calculate gamma with respect to yield."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        gamma_F = norm.pdf(d) / (vol * sqrt_T)
        return gamma_F * (self.future_dv01 ** 2)

    def vega_y(self, F, K, T, vol):
        """Calculate vega with respect to yield volatility."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return sqrt_T * norm.pdf(d) * self.future_dv01

    def theta_F(self, F, K, T, vol):
        """Calculate theta with respect to time."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return -vol * norm.pdf(d) / (2 * sqrt_T)

    def volga_price(self, F, K, T, vol):
        """Calculate volga (vega of vega) with respect to price volatility."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return sqrt_T * norm.pdf(d) * d / vol

    def vanna_F_price(self, F, K, T, vol):
        """Calculate vanna (delta of vega) with respect to future price and price volatility."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return -norm.pdf(d) / (vol * sqrt_T)

    def charm_F(self, F, K, T, vol):
        """Calculate charm (theta of delta) with respect to future price."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return norm.pdf(d) * d / (2 * T * vol)

    def speed_F(self, F, K, T, vol):
        """Calculate speed (gamma of gamma) with respect to future price."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return -norm.pdf(d) * d / ((vol * sqrt_T) ** 2)

    def color_F(self, F, K, T, vol):
        """Calculate color (gamma of theta) with respect to future price."""
        sqrt_T = np.sqrt(T)
        d = (F - K) / (vol * sqrt_T)
        return norm.pdf(d) * (1 + d**2) / (4 * T * vol * sqrt_T)

    def convert_price_to_yield_volatility(self, price_vol):
        """Convert price volatility to yield volatility."""
        return price_vol / self.future_dv01


def calculate_bond_option_volatility(F, K, T, market_price, option_type='call'):
    """
    Calculate implied volatility for a bond future option using hardcoded parameters.
    
    Args:
        F: Future price (will be parsed from pricing monkey format)
        K: Strike price (will be parsed from pricing monkey format)
        T: Time to expiration in years
        market_price: Market option price in 64ths
        option_type: 'call' or 'put' (hardcoded to 'call')
        
    Returns:
        Implied volatility (price volatility)
    """
    # Hardcoded values as requested
    future_dv01 = 0.063
    future_convexity = 0.002404
    yield_level = 0.05
    option_type = 'call'  # Always call as requested
    
    # Convert market price from 64ths to decimal
    market_price_decimal = market_price / 64.0
    
    # Basic sanity checks
    if T <= 0:
        raise ValueError(f"Time to expiry must be positive, got {T}")
    
    if market_price_decimal <= 0:
        raise ValueError(f"Market price must be positive, got {market_price_decimal}")
    
    # Check if market price is reasonable vs intrinsic value
    if option_type.lower() == 'call':
        intrinsic = max(0, F - K)
    else:
        intrinsic = max(0, K - F)
    
    if market_price_decimal < intrinsic * 0.95:  # Allow some tolerance
        print(f"  WARNING: Market price {market_price_decimal:.6f} is less than intrinsic value {intrinsic:.6f}")
        print(f"           This may indicate stale/bad data or arbitrage opportunity")
    
    # Initialize model
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Solve for implied volatility using Newton-Raphson with safeguards
    price_volatility = 20.0  # Better initial guess
    tolerance = 1e-6  # Looser tolerance to avoid infinite loops
    dx = 0.1  # Smaller step size
    max_iterations = 100  # Maximum iterations to prevent hanging
    
    iteration = 0
    option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type) - market_price_decimal
    
    while abs(option_price) > tolerance and iteration < max_iterations:
        iteration += 1
        
        # Calculate derivative numerically
        option_implied_2 = option_model.bachelier_future_option_price(F, K, T, price_volatility + dx, option_type) - market_price_decimal
        derivative = (option_implied_2 - option_price) / dx
        
        # Check for zero derivative (would cause division by zero)
        if abs(derivative) < 1e-10:
            print(f"  WARNING: Derivative too small at iteration {iteration}, breaking")
            break
        
        # Newton-Raphson update
        new_volatility = price_volatility - option_price / derivative
        
        # Bound the volatility to reasonable values
        new_volatility = max(0.1, min(1000.0, new_volatility))
        
        price_volatility = new_volatility
        option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type) - market_price_decimal
    
    if iteration >= max_iterations:
        print(f"  WARNING: Newton-Raphson failed to converge after {max_iterations} iterations")
        print(f"           Final error: {abs(option_price):.6f}, Final vol: {price_volatility:.6f}")
    
    return price_volatility


def analyze_bond_future_option_greeks(F, K, T, market_price, option_type='call'):
    """
    Full Greek analysis with hardcoded parameters matching the main dashboard.
    
    Args:
        F: Future price 
        K: Strike price
        T: Time to expiration in years
        market_price: Market option price in 64ths
        option_type: Option type (hardcoded to 'call')
        
    Returns:
        Dictionary with analysis results
    """
    # Hardcoded values as requested
    future_dv01 = 0.063
    future_convexity = 0.002404
    yield_level = 0.05
    option_type = 'call'  # Always call as requested
    
    # Convert market price from 64ths to decimal
    market_price_decimal = market_price / 64.0
    
    # Initialize model
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Solve for implied volatility
    price_volatility = calculate_bond_option_volatility(F, K, T, market_price, option_type)
    
    # Calculate Greeks at current F
    greeks = {}
    
    # Delta calculations (delta_F not scaled, delta_y scaled by 1000)
    for greek in ['delta_F', 'delta_y']:
        greek_value = getattr(option_model, greek)(F, K, T, price_volatility, option_type)
        if greek != 'delta_F':
            greek_value *= 1000
        greeks[greek] = greek_value
    
    # Other Greeks (all scaled by 1000)
    for greek in ['gamma_y','vega_y', 'theta_F', 'volga_price', 'vanna_F_price', 'charm_F', 'speed_F', 'color_F']:  
        greek_value = getattr(option_model, greek)(F, K, T, price_volatility) * 1000.
        greeks[greek] = greek_value
    
    return {
        'implied_volatility': price_volatility,
        'yield_volatility': option_model.convert_price_to_yield_volatility(price_volatility),
        'greeks': greeks
    } 