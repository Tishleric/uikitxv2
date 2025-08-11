"""
Mock Greek Calculator for Testing Configuration
Simulates the actual calculator behavior with configurable Greeks.
"""

import pandas as pd
import numpy as np
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from greek_config import GreekConfiguration


@dataclass
class MockGreekResult:
    """Mock result object similar to GreekResult in production."""
    instrument_key: str
    strike: float
    option_type: str
    success: bool = True
    
    # Greeks (all optional)
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
    speed_y: Optional[float] = None
    color_F: Optional[float] = None
    ultima: Optional[float] = None
    zomma: Optional[float] = None


class MockGreekCalculator:
    """Mock calculator that respects Greek configuration."""
    
    def __init__(self, greek_config: Optional[GreekConfiguration] = None):
        """Initialize with Greek configuration."""
        self.greek_config = greek_config or GreekConfiguration()
        self.calculation_times = {}
        
    def calculate_greeks(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[MockGreekResult]]:
        """
        Calculate Greeks for options in DataFrame, respecting configuration.
        
        Returns:
            Tuple of (DataFrame with Greek columns, List of results)
        """
        print(f"\nCalculating Greeks with configuration:")
        print(self.greek_config.summary())
        
        # Start timing
        start_time = time.time()
        
        # Get enabled Greeks
        enabled_greeks = self.greek_config.get_enabled_greeks()
        api_requested = self.greek_config.get_api_requested_greeks()
        
        print(f"\nRequesting from API: {api_requested}")
        
        # Filter for options only
        options_df = df[df['instrument_type'].isin(['CALL', 'PUT'])].copy()
        results = []
        
        # Add all Greek columns (enabled ones get values, disabled get NaN)
        all_greek_columns = [
            'delta_F', 'delta_y', 'gamma_F', 'gamma_y', 'vega_price', 'vega_y',
            'theta_F', 'volga_price', 'vanna_F_price', 'charm_F', 'speed_F',
            'speed_y', 'color_F', 'ultima', 'zomma'
        ]
        
        for col in all_greek_columns:
            df[col] = np.nan
        
        # Simulate Greek calculations for each option
        for idx, row in options_df.iterrows():
            result = MockGreekResult(
                instrument_key=row['instrument_key'],
                strike=row['strike'],
                option_type=row['instrument_type']
            )
            
            # Simulate calculation time per Greek (in milliseconds)
            greek_calc_times = {
                'delta_F': 0.5, 'delta_y': 0.5,
                'gamma_F': 0.8, 'gamma_y': 0.8,
                'vega_price': 1.0, 'vega_y': 1.0,
                'theta_F': 0.6,
                'volga_price': 1.5, 'vanna_F_price': 1.2,
                'charm_F': 1.0, 'speed_F': 1.2,
                'color_F': 1.5, 'ultima': 2.0, 'zomma': 1.8
            }
            
            # Calculate only enabled Greeks
            row_calc_time = 0
            for greek in api_requested:
                if greek in greek_calc_times:
                    # Simulate calculation delay
                    time.sleep(greek_calc_times[greek] / 1000)
                    row_calc_time += greek_calc_times[greek]
                    
                    # Generate mock value
                    if greek == 'delta_F':
                        value = np.random.normal(0.5, 0.2)
                    elif greek == 'gamma_F':
                        value = np.random.normal(0.02, 0.005)
                    else:
                        value = np.random.normal(0, 0.1)
                    
                    setattr(result, greek, value)
                    df.at[idx, greek] = value
                    
                    # Handle derived Greeks
                    if greek == 'speed_F' and 'speed_y' in enabled_greeks:
                        speed_y_value = value * 63.0**3  # Mock DV01 conversion
                        result.speed_y = speed_y_value
                        df.at[idx, 'speed_y'] = speed_y_value
            
            results.append(result)
            self.calculation_times[row['instrument_key']] = row_calc_time
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Print summary
        avg_time_per_option = (sum(self.calculation_times.values()) / len(self.calculation_times)) if self.calculation_times else 0
        print(f"\nCalculation Summary:")
        print(f"- Total options processed: {len(options_df)}")
        print(f"- Greeks calculated per option: {len(api_requested)}")
        print(f"- Average time per option: {avg_time_per_option:.1f}ms")
        print(f"- Total calculation time: {total_time:.3f}s")
        
        # Mark calculation status
        df['greek_calc_success'] = True
        df.loc[options_df.index, 'greek_calc_error'] = ''
        
        return df, results
    
    def calculate_aggregates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate aggregate rows, handling missing Greeks gracefully."""
        print("\nCalculating aggregates...")
        
        # Only aggregate enabled Greeks
        enabled_greeks = self.greek_config.get_enabled_greeks()
        
        # Define which Greeks to aggregate for each type
        f_space_greeks = [g for g in ['delta_F', 'gamma_F', 'theta_F', 'speed_F', 'color_F'] 
                         if g in enabled_greeks]
        y_space_greeks = [g for g in ['delta_y', 'gamma_y', 'speed_y', 'vega_y'] 
                         if g in enabled_greeks]
        
        # Create NET_OPTIONS_F aggregate
        options_mask = df['instrument_type'].isin(['CALL', 'PUT'])
        if options_mask.any() and f_space_greeks:
            net_f_row = {
                'instrument_key': 'NET_OPTIONS_F',
                'instrument_type': 'AGGREGATE',
                'position': df.loc[options_mask, 'position'].sum()
            }
            
            for greek in f_space_greeks:
                if greek in df.columns:
                    net_f_row[greek] = df.loc[options_mask, greek].sum(skipna=True)
            
            # Set disabled Greeks to NaN
            for col in df.columns:
                if col not in net_f_row:
                    net_f_row[col] = np.nan
            
            df = pd.concat([df, pd.DataFrame([net_f_row])], ignore_index=True)
        
        print(f"- Aggregated {len(f_space_greeks)} F-space Greeks")
        print(f"- Aggregated {len(y_space_greeks)} Y-space Greeks")
        
        return df