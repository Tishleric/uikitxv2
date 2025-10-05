"""
Calculator for Greek calculations on spot risk positions.

This module provides functionality to calculate implied volatility and Greeks
for bond future options using the bond_future_options API.

TODO: REMOVE HARDCODED ZN FUTURE SELECTION
This module currently has a hardcoded fix to always use ZN futures for all options.
This should be replaced with proper symbol parsing and future matching logic.
See calculate_greeks() method around line 220.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import the new API
from lib.trading.bond_future_options import GreekCalculatorAPI

from .greek_config import GreekConfiguration
from .greek_logger import greek_logger

logger = logging.getLogger(__name__)

# Default values for ZN futures (10-year US Treasury Note futures)
DEFAULT_DV01 = 63.996  # Base DV01 for ZN (update as needed)
DEFAULT_CONVEXITY = 0.0042  # Typical convexity for ZN futures

# Weekly-adjustable hedge ratios (ZN is baseline)
# Note: We derive per-contract DV01 by dividing the base by these ratios.
HEDGE_RATIOS = {
    'ZN': 1.0,
    'US': 0.47,
    'FV': 1.55,
    'TU': 3.61,
}

# DV01 values for different futures contracts (derived, no rounding)
FUTURES_DV01_MAP = {
    'ZN': DEFAULT_DV01 / HEDGE_RATIOS['ZN'],
    'US': DEFAULT_DV01 / HEDGE_RATIOS['US'],
    'FV': DEFAULT_DV01 / HEDGE_RATIOS['FV'],
    'TU': DEFAULT_DV01 / HEDGE_RATIOS['TU'],
}


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
                 model: str = 'bachelier_v1_parity',
                 greek_config: Optional[GreekConfiguration] = None):
        """
        Initialize calculator with future DV01 and convexity.
        
        Args:
            dv01: Dollar Value of 01 basis point for the future (default: 63.0)
            convexity: Convexity of the future (default: 0.0042)
            model: Model version to use (default: 'bachelier_v1_parity')
            greek_config: Optional Greek configuration for selective calculation
        """
        self.dv01 = dv01
        self.convexity = convexity
        self.model = model
        
        # Initialize Greek configuration
        self.greek_config = greek_config or GreekConfiguration()
        
        # Create API instance
        self.api = GreekCalculatorAPI(default_model=model)
        
        # Model parameters for API calls
        self.model_params = {
            'future_dv01': dv01 / 1000.0,  # Convert to bond future scale
            'future_convexity': convexity,
            'yield_level': 0.05  # Default yield level
        }
        
        logger.info(f"Initialized SpotRiskGreekCalculator with DV01={dv01}, convexity={convexity}, model={model}")
    
    def _convert_itype_to_instrument_type(self, itype: str) -> str:
        """
        Convert itype values to standardized instrument_type.
        
        Args:
            itype: Single character type ('F', 'C', 'P') or special values
            
        Returns:
            Standardized instrument type string
        """
        if pd.isna(itype) or not itype:
            return 'UNKNOWN'
        
        itype_upper = str(itype).upper().strip()
        
        mapping = {
            'F': 'FUTURE',
            'C': 'CALL',
            'P': 'PUT',
            'CALL': 'CALL',
            'PUT': 'PUT',
            'FUTURE': 'FUTURE',
            'NET': 'AGGREGATE',
            'NET_FUTURES': 'AGGREGATE',
            'NET_OPTIONS_F': 'AGGREGATE',
            'NET_OPTIONS_Y': 'AGGREGATE'
        }
        
        return mapping.get(itype_upper, 'UNKNOWN')
    
    def _get_futures_dv01(self, instrument_key: str) -> float:
        """
        Get DV01 value for a futures contract based on its type.
        
        This safely handles ActantRisk keys like 'XCME.ZN.SEP25' by extracting
        the series from the second segment and mapping it to our DV01 keys.
        Falls back to the first two characters for other formats and to
        self.dv01 if no mapping is available.
        
        Args:
            instrument_key: The instrument key (e.g., 'XCME.ZN.SEP25', 'ZNH5', 'USU5')
            
        Returns:
            The DV01 value for the futures type, or the calculator default if not found
        """
        futures_type = ''
        try:
            if instrument_key and isinstance(instrument_key, str):
                parts = instrument_key.split('.')
                # ActantRisk futures: 'XCME.<SERIES>.<EXPIRY>'
                if len(parts) >= 2 and parts[0].upper().endswith('CME'):
                    futures_type = parts[1][:2].upper()
                else:
                    futures_type = instrument_key[:2].upper()
        except Exception:
            futures_type = instrument_key[:2].upper() if instrument_key else ''

        # Map Actant series to DV01 map keys
        # ZN -> ZN, ZF -> FV, ZT -> TU, ZB -> US
        alias_map = {
            'ZN': 'ZN',
            'ZF': 'FV',
            'ZT': 'TU',
            'ZB': 'US',
        }
        dv01_key = alias_map.get(futures_type, futures_type)

        # Return mapped value or default
        dv01_value = FUTURES_DV01_MAP.get(dv01_key, self.dv01)
        
        # Log for transparency (only on first encounter)
        if not hasattr(self, '_logged_futures_types'):
            self._logged_futures_types = set()
        
        if dv01_key not in self._logged_futures_types:
            self._logged_futures_types.add(dv01_key)
            if dv01_key in FUTURES_DV01_MAP:
                logger.info(f"Using DV01={dv01_value} for {dv01_key} futures")
            else:
                logger.debug(f"No specific DV01 for {dv01_key}, using default {self.dv01}")
        
        return dv01_value
    
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
            logger.info("Checking 'itype' column for 'F'...")
            # Check raw values first
            logger.info(f"Raw itype unique values: {df['itype'].unique()}")
            # Handle case sensitivity - convert to uppercase for comparison
            future_rows = df[df['itype'].astype(str).str.upper() == 'F']
            logger.info(f"Found {len(future_rows)} rows with itype='F'")
            
            if len(future_rows) > 0:
                # TODO: TEMPORARY HARDCODED FIX - Remove when proper future mapping is implemented
                # Currently hardcoded to use ZN future price for all options
                
                # Try to find ZN future specifically
                zn_future = None
                for idx, row in future_rows.iterrows():
                    key = str(row.get('key', '')).upper()
                    if '.ZN.' in key:
                        zn_future = row
                        logger.info(f"Found ZN future: {key}")
                        break
                
                # Use ZN future if found, otherwise fall back to first future
                if zn_future is not None:
                    if 'midpoint_price' in zn_future.index:
                        future_price = zn_future['midpoint_price']
                        logger.info(f"Using ZN future price: {future_price}")
                    else:
                        logger.warning("midpoint_price not found in ZN future row")
                else:
                    # Fallback to first future if ZN not found
                    logger.info("ZN future not found, using first available future")
                    if 'midpoint_price' in future_rows.columns:
                        future_price = future_rows.iloc[0]['midpoint_price']
                        logger.info(f"Using fallback future price: {future_price}")
        
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
        
        # Log the detected future price
        if greek_logger.isEnabledFor(logging.DEBUG):
            greek_logger.debug(f"FUTURE_PRICE_DETECTED: {future_price}")
        
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
            # Disabled early return to allow futures-only batches to reach
            # the hardcoded futures Greeks section below.
            # return self._add_empty_greek_columns(df), []
        
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
        
        # Call API for batch processing with requested Greeks only
        requested_greeks = self.greek_config.get_api_requested_greeks()
        logger.info(
            f"Calculating Greeks for {len(options_data)} options with "
            f"{len(requested_greeks)} Greeks: {requested_greeks}"
        )
        
        # Debug log API call details
        if greek_logger.isEnabledFor(logging.DEBUG) and len(options_data) > 0:
            sample = options_data[0]
            greek_logger.debug(
                f"API_CALL: model={self.model}, F={sample['F']}, K={sample['K']}, "
                f"T={sample['T']}, mkt_price={sample['market_price']}, type={sample['option_type']}, "
                f"DV01={self.model_params['future_dv01']*1000}"
            )
        
        api_results = self.api.analyze(
            options_data, 
            model=self.model,
            model_params=self.model_params,
            requested_greeks=requested_greeks
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
                
                # Extract Greeks - only set values for enabled Greeks
                greeks = api_result['greeks']
                
                # Process all possible Greeks
                for greek_name in ['delta_F', 'delta_y', 'gamma_F', 'gamma_y', 
                                  'vega_price', 'vega_y', 'theta_F', 'volga_price',
                                  'vanna_F_price', 'charm_F', 'speed_F', 'speed_y', 'color_F',
                                  'ultima', 'zomma']:
                    if self.greek_config.is_enabled(greek_name):
                        # Set the calculated value for enabled Greeks
                        setattr(result, greek_name, greeks.get(greek_name, 0.0))
                    else:
                        # Set None for disabled Greeks (will become NaN in DataFrame)
                        setattr(result, greek_name, None)
                
                # Log success with available values
                log_msg = f"Successfully calculated Greeks for {result.instrument_key}"
                if result.implied_volatility is not None:
                    log_msg += f": IV={result.implied_volatility:.4f}"
                if result.delta_y is not None:
                    log_msg += f", delta_y={result.delta_y:.4f}"
                logger.debug(log_msg)
                
                # Debug log detailed Greek results
                if greek_logger.isEnabledFor(logging.DEBUG):
                    # Build log message with only available Greeks
                    log_parts = [f"RESULT: key={result.instrument_key}"]
                    if result.implied_volatility is not None:
                        log_parts.append(f"IV={result.implied_volatility:.6f}")
                    if result.delta_F is not None:
                        log_parts.append(f"delta_F={result.delta_F:.4f}")
                    if result.gamma_F is not None:
                        log_parts.append(f"gamma_F={result.gamma_F:.6f}")
                    if result.vega_price is not None:
                        log_parts.append(f"vega_price={result.vega_price:.4f}")
                    if result.theta_F is not None:
                        log_parts.append(f"theta_F={result.theta_F:.4f}")
                    greek_logger.debug(", ".join(log_parts))
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
        if 'Instrument Type' in df_copy.columns:
            futures_mask = df_copy['Instrument Type'].str.upper() == 'FUTURE'
        elif 'instrument type' in df_copy.columns:
            futures_mask = df_copy['instrument type'].str.upper() == 'FUTURE'
        elif 'itype' in df_copy.columns:
            futures_mask = df_copy['itype'].str.upper().isin(['F', 'FUTURE'])
        else:
            futures_mask = pd.Series([False] * len(df_copy))
        
        futures_df = df_copy[futures_mask]
        
        if len(futures_df) > 0:
            logger.info(f"Setting hardcoded Greeks for {len(futures_df)} futures rows")
            
            # For each futures row, set hardcoded Greek values
            for idx in futures_df.index:
                # Set hardcoded futures Greeks
                df_copy.at[idx, 'delta_F'] = 1.0
                df_copy.at[idx, 'gamma_F'] = 0.0
                
                # Y-space conversions using DV01 (now contract-specific)
                row = df_copy.loc[idx]
                futures_dv01 = self._get_futures_dv01(row['key'])
                df_copy.at[idx, 'delta_y'] = futures_dv01
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
            all_greek_columns = set(['delta_F', 'delta_y', 'gamma_F', 'gamma_y', 
                                    'vega_price', 'vega_y', 'theta_F', 'volga_price',
                                    'vanna_F_price', 'charm_F', 'speed_F', 'speed_y', 
                                    'color_F', 'ultima', 'zomma'])
            
            for col in df_copy.columns:
                if col not in net_row:
                    # For Greek columns not in the requested list, keep as NaN
                    if col in all_greek_columns and col not in greek_columns:
                        net_row[col] = np.nan
                    # Set appropriate default for other columns
                    elif df_copy[col].dtype in ['float64', 'int64']:
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
        
        # Add instrument_type column based on itype
        if 'itype' in df_copy.columns:
            logger.info("Adding instrument_type column based on itype values")
            df_copy['instrument_type'] = df_copy['itype'].apply(self._convert_itype_to_instrument_type)
            
            # Log the conversion results for debugging
            type_counts = df_copy['instrument_type'].value_counts()
            logger.info(f"Instrument type distribution: {type_counts.to_dict()}")
        else:
            logger.warning("No itype column found, cannot add instrument_type")
        
        return df_copy 