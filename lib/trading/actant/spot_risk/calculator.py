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

# Import the new API
from lib.trading.bond_future_options import GreekCalculatorAPI
from lib.monitoring.decorators import monitor

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
    model_version: Optional[str] = None


class SpotRiskGreekCalculator:
    """Calculator for Greeks on spot risk positions using bond_future_options API"""
    
    def __init__(self, 
                 dv01: float = DEFAULT_DV01, 
                 convexity: float = DEFAULT_CONVEXITY,
                 model: str = 'bachelier_v1'):
        """
        Initialize calculator with future DV01 and convexity.
        
        Args:
            dv01: Dollar Value of 01 basis point for the future (default: 63.0)
            convexity: Convexity of the future (default: 0.0042)
            model: Model version to use (default: 'bachelier_v1')
        """
        self.dv01 = dv01
        self.convexity = convexity
        self.model = model
        
        # Create API instance
        self.api = GreekCalculatorAPI(default_model=model)
        
        # Model parameters for API calls
        self.model_params = {
            'future_dv01': dv01 / 1000.0,  # Convert to bond future scale
            'future_convexity': convexity,
            'yield_level': 0.05  # Default yield level
        }
        
        logger.info(f"Initialized SpotRiskGreekCalculator with DV01={dv01}, convexity={convexity}, model={model}")
    
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
        
        # Log DataFrame info for debugging
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {list(df.columns)}")
        if 'itype' in df.columns:
            logger.info(f"itype values: {df['itype'].value_counts().to_dict()}")
        
        # Get future price - look for future in the data
        future_price = None
        
        # First try to find a future row - check both uppercase and lowercase column names
        if 'Instrument Type' in df.columns:
            future_rows = df[df['Instrument Type'].str.upper() == 'FUTURE']
            logger.info(f"Checking 'Instrument Type' column: found {len(future_rows)} future rows")
            if len(future_rows) > 0 and 'Price' in future_rows.columns:
                future_price = future_rows.iloc[0]['Price']
                logger.info(f"Found future price from future row: {future_price}")
        elif 'instrument type' in df.columns:
            future_rows = df[df['instrument type'].str.upper() == 'FUTURE']
            logger.info(f"Checking 'instrument type' column: found {len(future_rows)} future rows")
            if len(future_rows) > 0 and 'price' in future_rows.columns:
                future_price = future_rows.iloc[0]['price']
                logger.info(f"Found future price from future row (lowercase): {future_price}")
        
        # Fallback to itype column if Instrument Type not found
        if future_price is None and 'itype' in df.columns:
            logger.info(f"Checking 'itype' column for 'F'...")
            # Check raw values first
            logger.info(f"Raw itype unique values: {df['itype'].unique()}")
            # Handle case sensitivity - convert to uppercase for comparison
            future_rows = df[df['itype'].astype(str).str.upper() == 'F']
            logger.info(f"Found {len(future_rows)} rows with itype='F'")
            if len(future_rows) > 0:
                logger.info(f"Future row data: {future_rows.iloc[0].to_dict()}")
                if 'midpoint_price' in future_rows.columns:
                    future_price = future_rows.iloc[0]['midpoint_price']
                    logger.info(f"Found future price from future row (itype): {future_price}")
                else:
                    logger.warning(f"midpoint_price column not found in future rows. Available columns: {list(future_rows.columns)}")
        
        # If not found, try the future_price column
        if future_price is None and future_price_col in df.columns:
            future_prices = df[future_price_col].dropna().unique()
            if len(future_prices) > 0:
                future_price = future_prices[0]
                logger.info(f"Using future price from column: {future_price}")
        
        if future_price is None:
            # List what we searched for better debugging
            searched_locations = []
            if 'Instrument Type' in df.columns or 'instrument type' in df.columns:
                searched_locations.append("'Instrument Type'/'instrument type' == 'FUTURE'")
            if 'itype' in df.columns:
                searched_locations.append("'itype' == 'F'")
            if future_price_col in df.columns:
                searched_locations.append(f"'{future_price_col}' column")
            
            error_msg = (
                f"No valid future price found in DataFrame. "
                f"Searched: {', '.join(searched_locations)}. "
                f"DataFrame must contain a future row with price data."
            )
            raise ValueError(error_msg)
        
        # Filter options only - check both cases
        if 'Instrument Type' in df.columns:
            option_mask = df['Instrument Type'].isin(['CALL', 'PUT'])
        elif 'instrument type' in df.columns:
            option_mask = df['instrument type'].str.upper().isin(['CALL', 'PUT'])
        elif 'itype' in df.columns:
            option_mask = df['itype'].str.upper().isin(['C', 'P'])
        else:
            logger.error("No instrument type column found")
            return self._add_empty_greek_columns(df), []
        
        options_df = df[option_mask].copy()
        
        if len(options_df) == 0:
            logger.info("No options found in DataFrame")
            return self._add_empty_greek_columns(df), []
        
        # Prepare options data for API
        options_data = []
        for idx, row in options_df.iterrows():
            # Determine column names based on what's available - check both cases
            if 'Instrument Type' in row:
                option_type = str(row['Instrument Type']).lower()
            elif 'instrument type' in row:
                option_type = str(row['instrument type']).lower()
            else:
                itype_val = row.get('itype', '')
                option_type = 'call' if str(itype_val).upper() == 'C' else 'put'
            
            strike = row.get('Strike', row.get('strike'))
            market_price = row.get('Price', row.get('price', row.get('midpoint_price')))
            time_to_expiry = row.get('vtexp')
            
            options_data.append({
                'F': future_price,
                'K': strike,
                'T': time_to_expiry,
                'market_price': market_price,
                'option_type': option_type,
                '_index': idx,  # Keep track of original index
                '_instrument_key': row.get('instrument_key', row.get('key', row.get('Product', 'Unknown')))
            })
        
        # Call API for batch processing
        logger.info(f"Calculating Greeks for {len(options_data)} options")
        api_results = self.api.analyze(
            options_data, 
            model=self.model,
            model_params=self.model_params
        )
        
        # Process results and create GreekResult objects
        for option_data, api_result in zip(options_data, api_results):
            idx = option_data['_index']
            
            # Create GreekResult object
            result = GreekResult(
                instrument_key=option_data['_instrument_key'],
                strike=option_data['K'],
                option_type=option_data['option_type'],
                future_price=option_data['F'],
                market_price=option_data['market_price'],
                time_to_expiry=option_data['T'],
                model_version=api_result.get('model_version')
            )
            
            if api_result['success']:
                # Update with calculated values
                result.implied_volatility = api_result['volatility']
                result.calc_vol = api_result['volatility']
                result.success = True
                
                # Extract all Greeks
                greeks = api_result['greeks']
                for greek_name in ['delta_F', 'delta_y', 'gamma_F', 'gamma_y', 
                                  'vega_price', 'vega_y', 'theta_F', 'volga_price',
                                  'vanna_F_price', 'charm_F', 'speed_F', 'speed_y', 'color_F',
                                  'ultima', 'zomma']:
                    setattr(result, greek_name, greeks.get(greek_name, 0.0))
                
                logger.debug(f"Successfully calculated Greeks for {result.instrument_key}: "
                           f"IV={result.implied_volatility:.4f}, delta_y={result.delta_y:.4f}")
            else:
                # Handle error
                result.success = False
                result.error = api_result['error_message']
                result.error_message = api_result['error_message']
                logger.warning(f"Failed to calculate Greeks for {result.instrument_key}: {result.error}")
            
            results.append(result)
            
            if progress_callback:
                progress_callback(len(results), len(options_data))
        
        # Add Greek columns to DataFrame
        df_copy = self._add_empty_greek_columns(df)
        
        # Map results back to DataFrame
        for option_data, result in zip(options_data, results):
            idx = option_data['_index']
            
            # Update row with Greek values
            if result.success:
                df_copy.at[idx, 'calc_vol'] = result.implied_volatility
                df_copy.at[idx, 'implied_vol'] = result.implied_volatility
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
                df_copy.at[idx, 'speed_y'] = result.speed_y
                df_copy.at[idx, 'color_F'] = result.color_F
                df_copy.at[idx, 'ultima'] = result.ultima
                df_copy.at[idx, 'zomma'] = result.zomma
                df_copy.at[idx, 'greek_calc_success'] = True
                df_copy.at[idx, 'model_version'] = result.model_version
            else:
                df_copy.at[idx, 'greek_calc_error'] = result.error
                df_copy.at[idx, 'greek_calc_success'] = False
        
        # Add price source warnings if available
        if 'price_source' in df_copy.columns:
            # Add warning for rows not using adjtheor
            for idx in df_copy.index:
                price_source = df_copy.at[idx, 'price_source']
                if price_source and price_source != 'adjtheor' and price_source != 'unknown':
                    current_error = df_copy.at[idx, 'greek_calc_error']
                    if pd.isna(current_error) or current_error == '':
                        # No existing error, just add price source warning
                        if price_source == 'calculated':
                            df_copy.at[idx, 'greek_calc_error'] = 'Using calculated midpoint (adjtheor not available)'
                        elif price_source == 'bid_only':
                            df_copy.at[idx, 'greek_calc_error'] = 'Using bid price only (adjtheor not available)'
                        elif price_source == 'ask_only':
                            df_copy.at[idx, 'greek_calc_error'] = 'Using ask price only (adjtheor not available)'
                        elif price_source.startswith('fallback_'):
                            col_name = price_source.replace('fallback_', '')
                            df_copy.at[idx, 'greek_calc_error'] = f'Using {col_name} price (adjtheor not available)'
                        elif price_source == 'missing':
                            df_copy.at[idx, 'greek_calc_error'] = 'No valid price available'
                    else:
                        # Append to existing error
                        if price_source != 'missing':  # Don't double report missing prices
                            df_copy.at[idx, 'greek_calc_error'] = f"{current_error}; Price: {price_source}"
        
        # Summary statistics
        successful_calcs = sum(1 for r in results if r.success)
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
        
        # Process futures rows with hardcoded Greeks
        logger.info("Processing futures rows with hardcoded Greeks")
        
        # Filter futures - check both cases
        if 'Instrument Type' in df.columns:
            futures_mask = df['Instrument Type'].str.upper() == 'FUTURE'
        elif 'instrument type' in df.columns:
            futures_mask = df['instrument type'].str.upper() == 'FUTURE'
        elif 'itype' in df.columns:
            futures_mask = df['itype'].str.upper().isin(['F', 'FUTURE'])
        else:
            futures_mask = pd.Series([False] * len(df))
        
        futures_df = df[futures_mask]
        
        if len(futures_df) > 0:
            logger.info(f"Setting hardcoded Greeks for {len(futures_df)} futures rows")
            
            # For each futures row, set hardcoded Greek values
            for idx in futures_df.index:
                # Set hardcoded futures Greeks
                df_copy.at[idx, 'delta_F'] = 1.0
                df_copy.at[idx, 'gamma_F'] = 0.0
                
                # Y-space conversions using DV01
                df_copy.at[idx, 'delta_y'] = 63.0
                df_copy.at[idx, 'gamma_y'] = 0.0042 # This is convexity, not gamma
                
                # All other Greeks are 0 for futures
                df_copy.at[idx, 'vega_price'] = 0.0
                df_copy.at[idx, 'vega_y'] = 0.0
                df_copy.at[idx, 'theta_F'] = 0.0
                df_copy.at[idx, 'volga_price'] = 0.0
                df_copy.at[idx, 'vanna_F_price'] = 0.0
                df_copy.at[idx, 'charm_F'] = 0.0
                df_copy.at[idx, 'speed_F'] = 0.0
                df_copy.at[idx, 'color_F'] = 0.0
                df_copy.at[idx, 'ultima'] = 0.0
                df_copy.at[idx, 'zomma'] = 0.0
                
                # Futures don't have implied volatility
                df_copy.at[idx, 'calc_vol'] = 0.0
                df_copy.at[idx, 'implied_vol'] = 0.0
                
                # Mark as successfully calculated
                df_copy.at[idx, 'greek_calc_success'] = True
                df_copy.at[idx, 'greek_calc_error'] = ''
                df_copy.at[idx, 'model_version'] = 'futures_hardcoded'
            
            logger.info(f"Set hardcoded Greeks for {len(futures_df)} futures")
        
        return df_copy, results
    
    def _add_empty_greek_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add empty Greek columns to DataFrame."""
        df_copy = df.copy()
        
        # Greek columns
        greek_columns = [
            'calc_vol', 'implied_vol', 'delta_F', 'delta_y', 'gamma_F', 'gamma_y',
            'vega_price', 'vega_y', 'theta_F', 'volga_price', 'vanna_F_price',
            'charm_F', 'speed_F', 'color_F', 'ultima', 'zomma'
        ]
        
        # Status columns
        status_columns = [
            'greek_calc_success', 'greek_calc_error', 'model_version'
        ]
        
        # Initialize all columns with NaN or appropriate defaults
        for col in greek_columns:
            df_copy[col] = np.nan
            
        for col in status_columns:
            if col == 'greek_calc_success':
                df_copy[col] = False
            else:
                df_copy[col] = ''
        
        return df_copy
    
    def calculate_single_greek(self, 
                               row: pd.Series,
                               future_price: Optional[float] = None) -> GreekResult:
        """
        Calculate Greeks for a single option position.
        
        This method is kept for backwards compatibility but now uses the API internally.
        
        Args:
            row: Series containing option data
            future_price: Optional override for future price
            
        Returns:
            GreekResult object with calculated values or error information
        """
        # Extract required fields
        instrument_key = row.get('instrument_key', 'Unknown')
        strike = row.get('strike', row.get('Strike'))
        
        # Determine option type
        if 'option_type' in row:
            option_type = str(row['option_type']).lower()
        elif 'Instrument Type' in row:
            option_type = str(row['Instrument Type']).lower()
        elif 'itype' in row:
            option_type = 'call' if str(row['itype']).upper() == 'C' else 'put'
        else:
            option_type = 'unknown'
        
        market_price = row.get('midpoint_price', row.get('Price'))
        time_to_expiry = row.get('vtexp')
        
        # Use provided future price or get from row
        if future_price is None:
            future_price = row.get('future_price')
        
        # Create option data for API
        option_data = {
            'F': future_price,
            'K': strike,
            'T': time_to_expiry,
            'market_price': market_price,
            'option_type': option_type
        }
        
        # Call API
        api_result = self.api.analyze(option_data, model=self.model, model_params=self.model_params)
        
        # Convert to GreekResult
        result = GreekResult(
            instrument_key=instrument_key,
            strike=strike,
            option_type=option_type,
            future_price=future_price,
            market_price=market_price,
            time_to_expiry=time_to_expiry,
            model_version=api_result.get('model_version')
        )
        
        if api_result['success']:
            result.implied_volatility = api_result['volatility']
            result.calc_vol = api_result['volatility']
            result.success = True
            
            # Extract all Greeks
            greeks = api_result['greeks']
            for greek_name in ['delta_F', 'delta_y', 'gamma_F', 'gamma_y', 
                              'vega_price', 'vega_y', 'theta_F', 'volga_price',
                              'vanna_F_price', 'charm_F', 'speed_F', 'color_F',
                              'ultima', 'zomma']:
                setattr(result, greek_name, greeks.get(greek_name, 0.0))
        else:
            result.success = False
            result.error = api_result['error_message']
            result.error_message = api_result['error_message']
        
        return result
    
    def calculate_aggregates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate aggregate rows for futures and options positions.
        
        Creates:
        - NET_FUTURES row that sums all futures with non-zero positions
        - NET_OPTIONS_F row that sums all options with non-zero positions (F-space Greeks)
        - NET_OPTIONS_Y row that sums all options with non-zero positions (Y-space Greeks)
        
        Args:
            df: DataFrame with Greek calculations
            
        Returns:
            DataFrame with aggregate rows appended
        """
        logger.info("Calculating aggregate rows")
        
        # Make a copy to avoid modifying original
        df_copy = df.copy()
        
        # Define Greek columns to aggregate
        f_space_greeks = [
            'delta_F', 'gamma_F', 'theta_F', 'vega_price', 'volga_price',
            'vanna_F_price', 'charm_F', 'speed_F', 'color_F', 'ultima', 'zomma'
        ]
        
        y_space_greeks = [
            'delta_y', 'gamma_y', 'vega_y'  # Y-space has fewer Greeks available
        ]
        
        # Get position column name
        position_col = None
        for col in ['position', 'po', 'pos.position', 'Position', 'POS.POSITION']:
            if col in df_copy.columns:
                position_col = col
                break
        
        if position_col is None:
            # Try to find any column with 'position' in the name
            for col in df_copy.columns:
                if 'position' in col.lower():
                    position_col = col
                    logger.info(f"Found position column: {col}")
                    break
        
        if position_col is None:
            logger.warning("No position column found for aggregation")
            return df_copy
        
        # Helper function to create aggregate row
        def create_aggregate_row(filtered_df, row_key, greek_columns):
            """Create an aggregate row for given filtered data and Greek columns"""
            if len(filtered_df) == 0:
                return None
                
            net_row = {}
            
            # Set identifier columns
            if 'key' in df_copy.columns:
                net_row['key'] = row_key
            if 'product' in df_copy.columns:
                net_row['product'] = row_key
            if 'instrument_key' in df_copy.columns:
                net_row['instrument_key'] = row_key
            if 'Product' in df_copy.columns:
                net_row['Product'] = row_key
            
            # Set instrument type to NET
            if 'itype' in df_copy.columns:
                net_row['itype'] = 'NET'
            if 'Instrument Type' in df_copy.columns:
                net_row['Instrument Type'] = 'NET'
            if 'instrument type' in df_copy.columns:
                net_row['instrument type'] = 'NET'
            
            # Sum positions
            total_position = filtered_df[position_col].sum()
            net_row[position_col] = total_position
            
            # Clear fields that don't make sense for aggregates
            for col in ['strike', 'Strike', 'bid', 'ask', 'adjtheor', 'midpoint_price', 
                       'vtexp', 'expiry_date', 'calc_vol', 'implied_vol']:
                if col in df_copy.columns:
                    net_row[col] = None
            
            # Sum Greeks (simple addition)
            for greek_col in greek_columns:
                if greek_col in filtered_df.columns:
                    net_row[greek_col] = filtered_df[greek_col].sum(skipna=True)
            
            # Set status columns
            if 'greek_calc_success' in df_copy.columns:
                net_row['greek_calc_success'] = True
            if 'greek_calc_error' in df_copy.columns:
                net_row['greek_calc_error'] = ''
            if 'model_version' in df_copy.columns:
                net_row['model_version'] = 'net_aggregate'
            
            # Set price source if exists
            if 'price_source' in df_copy.columns:
                net_row['price_source'] = 'aggregate'
            
            # Copy other columns with appropriate defaults
            for col in df_copy.columns:
                if col not in net_row:
                    # Set appropriate default based on column type
                    if df_copy[col].dtype in ['float64', 'int64']:
                        net_row[col] = 0
                    else:
                        net_row[col] = ''
            
            return net_row
        
        # Filter for instrument types
        futures_mask = pd.Series([False] * len(df_copy))
        options_mask = pd.Series([False] * len(df_copy))
        
        if 'Instrument Type' in df_copy.columns:
            futures_mask = df_copy['Instrument Type'].str.upper() == 'FUTURE'
            options_mask = df_copy['Instrument Type'].str.upper().isin(['CALL', 'PUT'])
        elif 'instrument type' in df_copy.columns:
            futures_mask = df_copy['instrument type'].str.upper() == 'FUTURE'
            options_mask = df_copy['instrument type'].str.upper().isin(['CALL', 'PUT'])
        elif 'itype' in df_copy.columns:
            futures_mask = df_copy['itype'].str.upper().isin(['F', 'FUTURE'])
            options_mask = df_copy['itype'].str.upper().isin(['C', 'P', 'CALL', 'PUT'])
        
        # Filter for non-zero positions
        position_mask = pd.notna(df_copy[position_col]) & (df_copy[position_col] != 0)
        
        # Collect all aggregate rows before appending
        aggregate_rows = []
        
        # Process futures
        futures_with_positions = df_copy[futures_mask & position_mask].copy()
        if len(futures_with_positions) > 0:
            logger.info(f"Found {len(futures_with_positions)} futures with non-zero positions")
            # For futures, we aggregate all Greek columns (F and Y space)
            all_greeks = list(set(f_space_greeks + y_space_greeks))
            net_futures_row = create_aggregate_row(futures_with_positions, 'NET_FUTURES', all_greeks)
            if net_futures_row:
                aggregate_rows.append(net_futures_row)
                logger.info("Prepared NET_FUTURES aggregate row")
        
        # Process options
        options_with_positions = df_copy[options_mask & position_mask].copy()
        if len(options_with_positions) > 0:
            logger.info(f"Found {len(options_with_positions)} options with non-zero positions")
            
            # Create NET_OPTIONS_F row
            net_options_f_row = create_aggregate_row(options_with_positions, 'NET_OPTIONS_F', f_space_greeks)
            if net_options_f_row:
                aggregate_rows.append(net_options_f_row)
                logger.info("Prepared NET_OPTIONS_F aggregate row")
            
            # Create NET_OPTIONS_Y row
            net_options_y_row = create_aggregate_row(options_with_positions, 'NET_OPTIONS_Y', y_space_greeks)
            if net_options_y_row:
                # Also populate F-space Greeks with zeros for consistency
                for greek in f_space_greeks:
                    if greek not in y_space_greeks and greek in df_copy.columns:
                        net_options_y_row[greek] = 0.0
                aggregate_rows.append(net_options_y_row)
                logger.info("Prepared NET_OPTIONS_Y aggregate row")
        
        # Append all aggregate rows at once
        if aggregate_rows:
            aggregate_df = pd.DataFrame(aggregate_rows)
            df_copy = pd.concat([df_copy, aggregate_df], ignore_index=True)
            logger.info(f"Added {len(aggregate_rows)} aggregate rows")
        
        return df_copy 