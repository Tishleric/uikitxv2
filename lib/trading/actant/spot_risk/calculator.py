"""
Calculator for Greek calculations on spot risk positions.

This module provides functionality to calculate implied volatility and Greeks
for bond future options using the bond_future_options API.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Import API functions
from lib.trading.bond_future_options.api import calculate_implied_volatility, calculate_greeks

logger = logging.getLogger(__name__)

# Default values for ZN futures (10-year US Treasury Note futures)
DEFAULT_DV01 = 63.0  # Typical value for ZN futures
DEFAULT_CONVEXITY = 0.0042  # Typical convexity for ZN futures


@dataclass
class GreekResult:
    """Container for Greek calculation results"""
    instrument_key: str
    strike: float
    option_type: str
    future_price: float
    market_price: float
    time_to_expiry: float
    
    # Calculated values
    implied_volatility: Optional[float] = None
    calc_vol: Optional[float] = None  # Same as implied_vol for compatibility
    
    # Greeks
    delta_F: Optional[float] = None
    delta_y: Optional[float] = None
    gamma_F: Optional[float] = None
    gamma_y: Optional[float] = None
    vega_price: Optional[float] = None
    vega_y: Optional[float] = None
    theta_F: Optional[float] = None
    volga_price: Optional[float] = None
    vanna_F_price: Optional[float] = None
    charm_F: Optional[float] = None
    speed_F: Optional[float] = None
    color_F: Optional[float] = None
    ultima: Optional[float] = None
    zomma: Optional[float] = None
    
    # Error information
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class SpotRiskGreekCalculator:
    """Calculator for Greeks on spot risk positions using bond_future_options API"""
    
    def __init__(self, dv01: float = DEFAULT_DV01, convexity: float = DEFAULT_CONVEXITY):
        """
        Initialize calculator with future DV01 and convexity.
        
        Args:
            dv01: Dollar Value of 01 basis point for the future (default: 63.0)
            convexity: Convexity of the future (default: 0.0042)
        """
        self.dv01 = dv01
        self.convexity = convexity
        logger.info(f"Initialized SpotRiskGreekCalculator with DV01={dv01}, convexity={convexity}")
    
    def calculate_single_greek(self, 
                               row: pd.Series,
                               future_price: Optional[float] = None) -> GreekResult:
        """
        Calculate Greeks for a single option position.
        
        Args:
            row: Series containing option data with columns:
                - strike: Strike price
                - option_type: 'call' or 'put'
                - midpoint_price: Market price (decimal format)
                - vtexp: Time to expiry in years
                - instrument_key: Instrument identifier
                - future_price: Future price (optional, can override)
            future_price: Optional override for future price
            
        Returns:
            GreekResult object with calculated values or error information
        """
        # Extract required fields
        instrument_key = row.get('instrument_key', 'Unknown')
        strike = row.get('strike')
        option_type = row.get('option_type', '').lower()
        market_price = row.get('midpoint_price')
        time_to_expiry = row.get('vtexp')
        
        # Use provided future price or get from row
        if future_price is None:
            future_price = row.get('future_price')
        
        # Create result object with basic info
        result = GreekResult(
            instrument_key=instrument_key,
            strike=strike,
            option_type=option_type,
            future_price=future_price,
            market_price=market_price,
            time_to_expiry=time_to_expiry
        )
        
        # Validate inputs
        if strike is None or pd.isna(strike):
            result.error = "Missing strike price"
            return result
            
        if option_type not in ['call', 'put']:
            result.error = f"Invalid option type: {option_type}"
            return result
            
        if market_price is None or pd.isna(market_price):
            result.error = "Missing market price"
            return result
            
        if time_to_expiry is None or pd.isna(time_to_expiry):
            result.error = "Missing time to expiry"
            return result
            
        if future_price is None or pd.isna(future_price):
            result.error = "Missing future price"
            return result
        
        # Check for non-positive time to expiry
        if time_to_expiry <= 0:
            result.error = f"Invalid time to expiry: {time_to_expiry} (must be positive)"
            return result
        
        try:
            # Validate inputs before calculation
            if time_to_expiry <= 0:
                logger.warning(f"Zero or negative time to expiry for {instrument_key}, using minimum value")
                time_to_expiry = 1e-6
            
            if market_price <= 0:
                result.error = f"Invalid market price: {market_price}"
                result.success = False
                result.error_message = result.error
                return result
            
            # Check for arbitrage violations
            intrinsic_value = max(0, future_price - strike) if option_type == 'call' else max(0, strike - future_price)
            if market_price < intrinsic_value * 0.95:
                logger.warning(f"Potential arbitrage: {instrument_key} market_price={market_price:.6f} < intrinsic={intrinsic_value:.6f}")
            
            # For deep OTM options with very low prices, use minimum price
            min_price = 1.0 / 64.0  # 1 tick minimum
            if market_price < min_price:
                logger.warning(f"Market price {market_price:.6f} below minimum {min_price:.6f} for {instrument_key}, using minimum")
                market_price = min_price
            
            # Calculate implied volatility with safeguards
            logger.debug(f"Calculating Greeks for {instrument_key}: "
                        f"F={future_price}, K={strike}, T={time_to_expiry}, "
                        f"market_price={market_price}, type={option_type}")
            
            # Use better initial guess based on moneyness
            moneyness = (future_price - strike) / future_price
            initial_guess = 50.0 if abs(moneyness) > 0.1 else 20.0
            
            # Calculate implied volatility using our improved API
            implied_vol = calculate_implied_volatility(
                F=future_price,
                K=strike,
                T=time_to_expiry,
                market_price=market_price,
                option_type=option_type,
                future_dv01=self.dv01 / 1000.0,  # Convert to bond future scale
                future_convexity=self.convexity,
                initial_guess=initial_guess,
                tolerance=1e-6,
                suppress_output=True
            )
            
            # Validate implied vol
            if implied_vol <= 0 or implied_vol > 500:
                logger.warning(f"Unrealistic implied vol {implied_vol:.2f} for {instrument_key}")
                implied_vol = max(1.0, min(500.0, implied_vol))
            
            # Calculate Greeks
            greeks = calculate_greeks(
                F=future_price,
                K=strike,
                T=time_to_expiry,
                volatility=implied_vol,
                option_type=option_type,
                future_dv01=self.dv01 / 1000.0,  # Convert to bond future scale
                future_convexity=self.convexity,
                return_scaled=True
            )
            
            # Update result with calculated values
            result.implied_volatility = implied_vol
            result.calc_vol = implied_vol
            result.delta_F = greeks.get('delta_F', 0.0)
            result.delta_y = greeks.get('delta_y', 0.0)
            result.gamma_F = greeks.get('gamma_F', 0.0)
            result.gamma_y = greeks.get('gamma_y', 0.0)
            result.vega_price = greeks.get('vega_price', 0.0)
            result.vega_y = greeks.get('vega_y', 0.0)
            result.theta_F = greeks.get('theta_F', 0.0)
            result.volga_price = greeks.get('volga_price', 0.0)
            result.vanna_F_price = greeks.get('vanna_F_price', 0.0)
            result.charm_F = greeks.get('charm_F', 0.0)
            result.speed_F = greeks.get('speed_F', 0.0)
            result.color_F = greeks.get('color_F', 0.0)
            result.ultima = greeks.get('ultima', 0.0)
            result.zomma = greeks.get('zomma', 0.0)
            
            logger.debug(f"Successfully calculated Greeks for {instrument_key}: "
                        f"IV={result.implied_volatility:.4f}, delta_y={result.delta_y:.4f}")
            
        except Exception as e:
            result.error = f"Calculation error: {str(e)}"
            result.error_details = {
                'exception_type': type(e).__name__,
                'exception_str': str(e),
                'inputs': {
                    'F': future_price,
                    'K': strike,
                    'T': time_to_expiry,
                    'market_price': market_price,
                    'option_type': option_type,
                    'dv01': self.dv01,
                    'convexity': self.convexity
                }
            }
            logger.error(f"Error calculating Greeks for {instrument_key}: {e}")
        
        return result
    
    def calculate_greeks(self, 
                         df: pd.DataFrame,
                         future_price_col: str = 'future_price',
                         progress_callback: Optional[callable] = None) -> Tuple[pd.DataFrame, List[GreekResult]]:
        """
        Calculate Greeks for all options in DataFrame.
        
        Args:
            df: DataFrame with option data
            future_price_col: Column name for future price
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of:
            - Updated DataFrame with Greek columns added
            - List of GreekResult objects (including errors)
        """
        results = []
        total_rows = len(df)
        
        # Get future price - look for future in the data
        future_price = None
        
        # First try to find a future row
        if 'itype' in df.columns:
            future_rows = df[df['itype'].str.upper() == 'F']
            if len(future_rows) > 0 and 'midpoint_price' in future_rows.columns:
                future_price = future_rows.iloc[0]['midpoint_price']
                logger.info(f"Found future price from future row: {future_price}")
        
        # If not found, try the future_price column
        if future_price is None and future_price_col in df.columns:
            future_prices = df[future_price_col].dropna().unique()
            if len(future_prices) > 0:
                future_price = future_prices[0]
                logger.info(f"Using future price from column: {future_price}")
        
        if future_price is None:
            logger.error("No valid future price found in DataFrame")
        
        # Calculate Greeks for each row
        for idx, row in df.iterrows():
            if progress_callback:
                progress_callback(idx + 1, total_rows)
            
            # Skip futures and non-option rows
            itype = str(row.get('itype', '')).upper()
            if itype in ['F', 'N'] or (itype not in ['C', 'P']):
                continue
            
            # Add option_type based on itype
            row = row.copy()  # Make a copy to avoid modifying original
            row['option_type'] = 'call' if itype == 'C' else 'put'
            row['future_price'] = future_price
            
            result = self.calculate_single_greek(row, future_price)
            results.append(result)
        
        # Add Greek columns to DataFrame
        df_copy = df.copy()
        
        # Initialize Greek columns
        greek_columns = [
            'calc_vol', 'delta_F', 'delta_y', 'gamma_F', 'gamma_y',
            'vega_price', 'vega_y', 'theta_F', 'volga_price', 'vanna_F_price',
            'charm_F', 'speed_F', 'color_F', 'ultima', 'zomma', 'greek_error'
        ]
        
        for col in greek_columns:
            df_copy[col] = np.nan
        
        # Map results back to DataFrame
        result_idx = 0
        for idx, row in df_copy.iterrows():
            # Skip futures and non-option rows (same logic as above)
            itype = str(row.get('itype', '')).upper()
            if itype in ['F', 'N'] or (itype not in ['C', 'P']):
                continue
                
            if result_idx < len(results):
                result = results[result_idx]
                
                # Update row with Greek values
                if result.error is None:
                    df_copy.at[idx, 'calc_vol'] = result.implied_volatility
                    df_copy.at[idx, 'delta_F'] = result.delta_F
                    df_copy.at[idx, 'delta_y'] = result.delta_y
                    df_copy.at[idx, 'gamma_F'] = result.gamma_F
                    df_copy.at[idx, 'gamma_y'] = result.gamma_y
                    df_copy.at[idx, 'vega_price'] = result.vega_price
                    df_copy.at[idx, 'vega_y'] = result.vega_y
                    df_copy.at[idx, 'theta_F'] = result.theta_F
                    df_copy.at[idx, 'volga_price'] = result.volga_price
                    df_copy.at[idx, 'vanna_F_price'] = result.vanna_F_price
                    df_copy.at[idx, 'charm_F'] = result.charm_F
                    df_copy.at[idx, 'speed_F'] = result.speed_F
                    df_copy.at[idx, 'color_F'] = result.color_F
                    df_copy.at[idx, 'ultima'] = result.ultima
                    df_copy.at[idx, 'zomma'] = result.zomma
                else:
                    df_copy.at[idx, 'greek_error'] = result.error
                
                result_idx += 1
        
        # Summary statistics
        successful_calcs = sum(1 for r in results if r.error is None)
        failed_calcs = len(results) - successful_calcs
        
        logger.info(f"Greek calculations complete: {successful_calcs} successful, {failed_calcs} failed")
        
        if failed_calcs > 0:
            # Log summary of errors
            error_types = {}
            for r in results:
                if r.error:
                    error_type = r.error.split(':')[0]
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            logger.warning(f"Error summary: {error_types}")
        
        return df_copy, results 


    
    def _create_error_result(self, instrument_key: str, strike: float, option_type: str,
                           future_price: float, market_price: float, time_to_expiry: float,
                           error_message: str) -> GreekResult:
        """Create a GreekResult with error status and zero Greeks."""
        return GreekResult(
            instrument_key=instrument_key,
            strike=strike,
            option_type=option_type,
            future_price=future_price,
            market_price=market_price,
            time_to_expiry=time_to_expiry,
            implied_volatility=0.0,
            calc_vol=0.0,
            delta_F=0.0,
            delta_y=0.0,
            gamma_F=0.0,
            gamma_y=0.0,
            vega_price=0.0,
            vega_y=0.0,
            theta_F=0.0,
            volga_price=0.0,
            vanna_F_price=0.0,
            charm_F=0.0,
            speed_F=0.0,
            color_F=0.0,
            ultima=0.0,
            zomma=0.0,
            success=False,
            error_message=error_message
        ) 