"""
PnL Calculation Module for Actant Option Analysis

This module implements the Taylor Series expansion formulas extracted from
the Excel workbook for comparing option pricing methods.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple, Dict

from monitoring.decorators import monitor


@dataclass
class OptionGreeks:
    """Container for option Greeks and market data."""
    shocks: np.ndarray  # Strike offsets in basis points
    call_prices: np.ndarray  # Actant call prices
    put_prices: np.ndarray  # Actant put prices
    call_delta_dv01: np.ndarray  # Call delta DV01
    put_delta_dv01: np.ndarray  # Put delta DV01
    gamma_dv01: np.ndarray  # Gamma DV01 (same for calls and puts)
    vega_dv01: np.ndarray  # Vega DV01
    theta: np.ndarray  # Theta
    forward: float  # Forward price
    strike: float  # Strike price
    time_to_expiry: float  # Time to expiry in years
    underlying_price: float  # Current underlying price
    
    @property
    def atm_index(self) -> int:
        """Find index of ATM position (shock = 0)."""
        zero_indices = np.where(np.abs(self.shocks) < 0.001)[0]
        if len(zero_indices) == 0:
            raise ValueError("No ATM position found (shock = 0)")
        return zero_indices[0]
    
    @property
    def num_strikes(self) -> int:
        """Number of strike points."""
        return len(self.shocks)


class TaylorSeriesPricer:
    """Calculate option prices using Taylor Series expansion."""
    
    @staticmethod
    def from_atm(greeks: OptionGreeks, option_type: str = 'call') -> np.ndarray:
        """
        Calculate option prices using 2nd order Taylor series from ATM.
        
        Args:
            greeks: OptionGreeks object containing market data
            option_type: 'call' or 'put'
            
        Returns:
            Array of estimated option prices
        """
        atm_idx = greeks.atm_index
        
        if option_type.lower() == 'call':
            atm_price = greeks.call_prices[atm_idx]
            atm_delta = greeks.call_delta_dv01[atm_idx]
        else:
            atm_price = greeks.put_prices[atm_idx]
            atm_delta = greeks.put_delta_dv01[atm_idx]
            
        atm_gamma = greeks.gamma_dv01[atm_idx]
        atm_shock = greeks.shocks[atm_idx]
        
        # Calculate prices for all shocks
        shock_diff = greeks.shocks - atm_shock
        prices = atm_price + atm_delta * shock_diff + 0.5 * atm_gamma * shock_diff**2
        
        return prices
    
    @staticmethod
    def from_neighbor(greeks: OptionGreeks, option_type: str = 'call', 
                      offset: float = -0.25) -> np.ndarray:
        """
        Calculate option prices using 2nd order Taylor series from neighboring points.
        
        This matches the Excel implementation where each position uses its own greeks
        to predict the next position's price.
        
        Args:
            greeks: OptionGreeks object containing market data
            option_type: 'call' or 'put'
            offset: Not used (kept for compatibility)
            
        Returns:
            Array of estimated option prices
        """
        prices = np.zeros(greeks.num_strikes)
        
        # Special handling for boundary cases
        atm_idx = greeks.atm_index
        
        # For each position, use its greeks to predict from a neighbor
        for i in range(greeks.num_strikes):
            # Determine which position's greeks to use for prediction
            if i == 0:
                # First position: use next position's greeks to predict backward
                source_idx = 1
                target_idx = 0
            else:
                # All other positions: use previous position's greeks to predict forward
                source_idx = i - 1
                target_idx = i
            
            # Get source position's values (the position whose greeks we use)
            if option_type.lower() == 'call':
                source_price = greeks.call_prices[source_idx]
                source_delta = greeks.call_delta_dv01[source_idx]
            else:
                source_price = greeks.put_prices[source_idx]
                source_delta = greeks.put_delta_dv01[source_idx]
                
            source_gamma = greeks.gamma_dv01[source_idx]
            
            # Calculate shock difference (target - source)
            shock_diff = greeks.shocks[target_idx] - greeks.shocks[source_idx]
            
            # Apply Taylor expansion
            prices[i] = (source_price + 
                        source_delta * shock_diff + 
                        0.5 * source_gamma * shock_diff**2)
        
        return prices


class PnLCalculator:
    """Calculate P&L for different pricing methods."""
    
    @staticmethod
    def calculate_pnl(prices: np.ndarray, reference_idx: Optional[int] = None) -> np.ndarray:
        """
        Calculate P&L relative to a reference position.
        
        Args:
            prices: Array of option prices
            reference_idx: Index of reference position (default: ATM)
            
        Returns:
            Array of P&L values
        """
        if reference_idx is None:
            # Find ATM position (middle of array)
            reference_idx = len(prices) // 2
            
        reference_price = prices[reference_idx]
        return prices - reference_price
    
    @staticmethod
    def calculate_all_pnls(greeks: OptionGreeks, option_type: str = 'call') -> pd.DataFrame:
        """
        Calculate P&L for all methods: Actant, TS0, and TS-0.25.
        
        Args:
            greeks: OptionGreeks object containing market data
            option_type: 'call' or 'put'
            
        Returns:
            DataFrame with P&L results for all methods
        """
        # Get actual prices
        if option_type.lower() == 'call':
            actant_prices = greeks.call_prices
        else:
            actant_prices = greeks.put_prices
            
        # Calculate Taylor Series prices
        ts0_prices = TaylorSeriesPricer.from_atm(greeks, option_type)
        ts_neighbor_prices = TaylorSeriesPricer.from_neighbor(greeks, option_type)
        
        # Calculate P&Ls
        atm_idx = greeks.atm_index
        actant_pnl = PnLCalculator.calculate_pnl(actant_prices, atm_idx)
        ts0_pnl = PnLCalculator.calculate_pnl(ts0_prices, atm_idx)
        ts_neighbor_pnl = PnLCalculator.calculate_pnl(ts_neighbor_prices, atm_idx)
        
        # Calculate differences
        ts0_diff = ts0_pnl - actant_pnl
        ts_neighbor_diff = ts_neighbor_pnl - actant_pnl
        
        # Create DataFrame
        results_df = pd.DataFrame({
            'shock_bp': greeks.shocks,
            'actant_price': actant_prices,
            'ts0_price': ts0_prices,
            'ts_neighbor_price': ts_neighbor_prices,
            'actant_pnl': actant_pnl,
            'ts0_pnl': ts0_pnl,
            'ts_neighbor_pnl': ts_neighbor_pnl,
            'ts0_diff': ts0_diff,
            'ts_neighbor_diff': ts_neighbor_diff
        })
        
        return results_df


@monitor()
def parse_actant_csv_to_greeks(df: pd.DataFrame, expiration: str = 'XCME.ZN') -> OptionGreeks:
    """
    Parse Actant CSV data into OptionGreeks object.
    
    Args:
        df: DataFrame from Actant CSV file
        expiration: Expiration identifier to filter
        
    Returns:
        OptionGreeks object with parsed data
    """
    # Filter for specific expiration
    exp_data = df[df['Expiration'] == expiration].copy()
    
    # Extract shock values from column headers (skip first 4 columns)
    shock_columns = df.columns[4:]  # Skip Expiration, Value, UPrice, and first shock
    shocks = np.array([float(col) for col in shock_columns])
    
    # Helper function to extract row data
    def get_row_values(value_name: str) -> np.ndarray:
        row = exp_data[exp_data['Value'] == value_name]
        if row.empty:
            raise ValueError(f"Value '{value_name}' not found for expiration '{expiration}'")
        return row.iloc[0, 4:].values.astype(float)
    
    # Extract all required data
    underlying_price = float(exp_data.iloc[0]['UPrice'])
    
    greeks = OptionGreeks(
        shocks=shocks * 16,  # Convert to basis points (1 shock = 16 bp)
        call_prices=get_row_values('ab_sCall'),
        put_prices=get_row_values('ab_sPut'),
        call_delta_dv01=get_row_values('ab_sDeltaPathDV01Call'),
        put_delta_dv01=get_row_values('ab_sDeltaPathDV01Put'),
        gamma_dv01=get_row_values('ab_sGammaPathDV01'),
        vega_dv01=get_row_values('ab_VegaDV01'),
        theta=get_row_values('ab_Theta'),
        forward=get_row_values('ab_F')[0],  # Same for all strikes
        strike=get_row_values('ab_K')[0],  # Same for all strikes
        time_to_expiry=get_row_values('ab_T')[0],  # Same for all strikes
        underlying_price=underlying_price
    )
    
    return greeks 