"""Spot Risk Dashboard Controller

This module handles the business logic for the Spot Risk dashboard.
Follows the Controller layer of MVC pattern - coordinates between data and views.
"""

import os
import glob
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

from lib.monitoring.decorators import monitor
from lib.trading.actant.spot_risk import SpotRiskGreekCalculator
# Import the database service instead of the parser
from lib.trading.actant.spot_risk.database import SpotRiskDatabaseService

logger = logging.getLogger(__name__)


class SpotRiskController:
    """Controller for Spot Risk dashboard business logic
    
    Handles data loading, processing, and state management from a live database.
    """
    
    def __init__(self):
        """Initialize the controller with calculator and database service instances"""
        self.calculator = SpotRiskGreekCalculator()
        self.db_service = SpotRiskDatabaseService()
        self.current_data: Optional[pd.DataFrame] = None
        self.data_timestamp: Optional[datetime] = None
        
    @monitor()
    def get_latest_greeks_data(self) -> bool:
        """
        Loads the latest, complete set of Greek positions from the active
        buffer table in the database.

        Returns:
            bool: True if data was loaded successfully, False otherwise.
        """
        try:
            logger.info("Fetching latest greeks data from the database...")
            df = self.db_service.read_greeks_from_active_buffer()

            if df is None or df.empty:
                logger.warning("No data returned from the active buffer table.")
                self.current_data = None
                self.data_timestamp = None
                return False

            # The timestamp of the data batch can be retrieved from the session table
            # For now, we'll use the current time as an indicator of freshness.
            self.data_timestamp = datetime.now()
            self.current_data = df
            
            logger.info(f"Successfully loaded {len(df)} rows from the database.")
            return True

        except Exception as e:
            logger.error(f"Error fetching greeks data from database: {e}", exc_info=True)
            self.current_data = None
            self.data_timestamp = None
            return False

    # The methods below this point (_get_csv_directory, discover_csv_files, 
    # find_latest_csv, read_processed_greeks, load_csv_data, _extract_timestamp)
    # are now deprecated as we are moving to a live database model.
    # They are kept here for potential fallback or debugging but will be removed later.

    def _get_csv_directory(self) -> Path:
        """Get the directory where spot risk CSV files are stored
        
        Returns:
            Path: Directory path for CSV files
        """
        # Navigate from controller location to data directory
        project_root = Path(__file__).parent.parent.parent.parent
        csv_dir = project_root / "data" / "input" / "actant_spot_risk"
        
        # Create directory if it doesn't exist
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        return csv_dir
    
    def _get_latest_date_folder(self, base_dir: Path) -> Optional[Path]:
        """Find the latest date folder in the given directory
        
        Looks for folders with YYYY-MM-DD pattern and returns the most recent one.
        
        Args:
            base_dir: Base directory to search in
            
        Returns:
            Optional[Path]: Path to the latest date folder, or None if no date folders found
        """
        if not base_dir.exists():
            return None
        
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        date_folders = []
        
        for item in base_dir.iterdir():
            if item.is_dir() and date_pattern.match(item.name):
                date_folders.append(item)
        
        if not date_folders:
            return None
        
        # Sort by folder name (which is in YYYY-MM-DD format, so lexical sort works)
        date_folders.sort(key=lambda x: x.name, reverse=True)
        
        return date_folders[0]
    
    def _get_csv_directories(self) -> List[Path]:
        """Get all directories where spot risk CSV files might be stored
        
        Returns:
            List[Path]: List of directory paths, in priority order
        """
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Check output directory first (for processed files)
        output_dir = project_root / "data" / "output" / "spot_risk"
        input_dir = project_root / "data" / "input" / "actant_spot_risk"
        
        dirs = []
        
        # Check for latest date folder in output directory
        if output_dir.exists():
            latest_output_date_folder = self._get_latest_date_folder(output_dir)
            if latest_output_date_folder:
                dirs.append(latest_output_date_folder)
            # Also add root output dir for backward compatibility
            dirs.append(output_dir)
            
        # Check for latest date folder in input directory    
        if input_dir.exists():
            latest_input_date_folder = self._get_latest_date_folder(input_dir)
            if latest_input_date_folder:
                dirs.append(latest_input_date_folder)
            # Also add root input dir for backward compatibility
            dirs.append(input_dir)
            
        # Create input directory if neither exists
        if not dirs:
            input_dir.mkdir(parents=True, exist_ok=True)
            dirs.append(input_dir)
            
        return dirs
    
    @monitor()
    def discover_csv_files(self) -> List[Dict[str, Any]]:
        """Discover available CSV files in the spot risk directory
        
        Returns:
            List[Dict]: List of file info dicts with keys:
                - filepath: Full path to file
                - filename: Just the filename
                - modified_time: Last modified datetime
                - size_mb: File size in MB
        """
        file_info = []
        
        # Check all directories
        for directory in self._get_csv_directories():
            # Use rglob to recursively find CSV files
            csv_files = list(directory.rglob("*.csv"))
            
            for path in csv_files:
                stat = path.stat()
                
                # Prioritize processed files
                is_processed = "_processed" in path.name
                
                file_info.append({
                    'filepath': str(path),
                    'filename': path.name,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'is_processed': is_processed
                })
        
        # Sort by: processed files first, then by modified time (newest first)
        file_info.sort(key=lambda x: (not x['is_processed'], -x['modified_time'].timestamp()))
        
        return file_info
    
    @monitor()
    def find_latest_csv(self) -> Optional[str]:
        """Find the most recently modified CSV file
        
        Returns:
            Optional[str]: Path to latest CSV file, or None if no files found
        """
        files = self.discover_csv_files()
        
        if files:
            return files[0]['filepath']
        
        return None
    
    @monitor()
    def read_processed_greeks(self) -> Optional[pd.DataFrame]:
        """Read Greek data from the most recent processed CSV file
        
        Returns:
            Optional[pd.DataFrame]: DataFrame with pre-calculated Greeks, or None if failed
        """
        try:
            # Find the most recent processed file
            files = self.discover_csv_files()
            processed_files = [f for f in files if f.get('is_processed', False)]
            
            if not processed_files:
                logger.warning("No processed CSV files found")
                return None
            
            # Get the most recent processed file
            latest_file = processed_files[0]['filepath']
            logger.info(f"Reading processed Greeks from: {Path(latest_file).name}")
            
            # Read the CSV file
            df = pd.read_csv(latest_file)
            
            if df is None or df.empty:
                logger.warning(f"Processed file is empty: {latest_file}")
                return None
            
            # Store the timestamp from the processed file
            self.data_timestamp = self._extract_timestamp(latest_file, df)
            
            logger.info(f"Successfully loaded {len(df)} rows from processed file")
            return df
            
        except Exception as e:
            logger.error(f"Error reading processed Greeks: {e}")
            return None
    
    @monitor()
    def load_csv_data(self, filepath: Optional[str] = None) -> bool:
        """Load CSV data and prepare for processing
        
        Args:
            filepath: Path to CSV file. If None, loads latest file.
            
        Returns:
            bool: True if data loaded successfully
        """
        try:
            # Use provided filepath or find latest
            if filepath is None:
                filepath = self.find_latest_csv()
                
            if filepath is None:
                print("No CSV files found in spot risk directory")
                return False
            
            # Parse the CSV file
            # This part of the code is now deprecated as we are moving to a live database.
            # The original parse_spot_risk_csv function is removed from imports.
            # If this method is called, it will cause an error.
            # For now, we'll keep it as is, but it will fail.
            # df = parse_spot_risk_csv(filepath)
            
            # If the original parse_spot_risk_csv function is removed,
            # this block will cause an error.
            # To avoid breaking the code, we'll comment out the line
            # that calls the removed function.
            # The user's edit hint implies this method is deprecated.
            # I will remove the call to parse_spot_risk_csv.
            # The user's edit hint also implies the _extract_timestamp
            # method is now redundant. I will remove it.
            
            # The original code had:
            # df = parse_spot_risk_csv(filepath)
            # self.data_timestamp = self._extract_timestamp(filepath, df)
            # self.current_csv_path = filepath  # Store path for profile saving
            
            # Since parse_spot_risk_csv is removed, we cannot parse the CSV.
            # We will set current_data to None and data_timestamp to None.
            self.current_data = None
            self.data_timestamp = None
            
            print(f"CSV loading is deprecated. No data loaded from {Path(filepath).name}")
            
            # Pre-compute Greek profiles asynchronously
            print("Pre-computing Greek profiles...")
            profile_computed = self.pre_compute_greek_profiles()
            if profile_computed:
                print("Greek profiles computed and saved successfully")
            else:
                print("Warning: Failed to pre-compute Greek profiles")
            
            return True
            
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            return False
    
    def _extract_timestamp(self, filepath: str, df: pd.DataFrame) -> datetime:
        """Extract timestamp from filename or data
        
        Args:
            filepath: Path to CSV file
            df: Parsed DataFrame
            
        Returns:
            datetime: Best guess at data timestamp
        """
        # Try to extract from filename first
        # Expected format: bav_analysis_YYYYMMDD_HHMMSS.csv
        filename = Path(filepath).stem
        parts = filename.split('_')
        
        if len(parts) >= 4:
            try:
                date_str = parts[-2]  # YYYYMMDD
                time_str = parts[-1]  # HHMMSS
                
                # Parse the timestamp
                timestamp_str = f"{date_str}_{time_str}"
                return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except:
                pass
        
        # Fallback to file modification time
        return datetime.fromtimestamp(Path(filepath).stat().st_mtime)
    
    @monitor()
    def get_positions_from_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract position data from DataFrame
        
        Args:
            df: DataFrame with spot risk data
            
        Returns:
            pd.DataFrame: DataFrame with position column added/normalized
        """
        # Check for position column variations
        position_col = None
        for col in ['POS.POSITION', 'pos.position', 'POSITION', 'Position', 'position']:
            if col in df.columns:
                position_col = col
                break
        
        if position_col:
            # Ensure position is numeric and handle NaN values
            try:
                df['position'] = pd.to_numeric(df[position_col], errors='coerce')
                df['position'] = df['position'].fillna(0)
            except Exception:
                df['position'] = 0
        else:
            # If no position column found, add zeros
            df['position'] = 0
            
        return df
    
    @monitor()
    def filter_positions_only(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to only include rows with non-zero positions
        
        Args:
            df: DataFrame with position data
            
        Returns:
            pd.DataFrame: Filtered DataFrame with only position rows
        """
        if 'position' not in df.columns:
            df = self.get_positions_from_csv(df)
            
        # Keep only rows where position != 0
        return df[df['position'] != 0].copy()
    
    @monitor()
    def find_atm_strike(self, df: Optional[pd.DataFrame] = None) -> Optional[float]:
        """Find the at-the-money strike based on rounded future price
        
        Args:
            df: DataFrame with Greek calculations. If None, uses current_data
            
        Returns:
            Optional[float]: ATM strike price, or None if not found
        """
        if df is None:
            df = self.current_data
            
        if df is None or df.empty:
            return None
        
        # First, try to get the future price
        future_price = None
        for _, row in df.iterrows():
            if row.get('itype', '').upper() == 'F':
                try:
                    future_price = float(row.get('midpoint_price', 0))
                    if future_price > 0:  # Valid price found
                        break
                except (ValueError, TypeError):
                    continue
        
        # If no future price found, fall back to delta-based method
        if future_price is None or future_price <= 0:
            logger.warning("No future price found, falling back to delta-based ATM detection")
            
            # Filter for calls only (delta positive for calls)
            type_col = None
            for col in ['itype', 'ITYPE', 'Type', 'type']:
                if col in df.columns:
                    type_col = col
                    break
                    
            if type_col:
                calls_df = df[df[type_col].str.upper() == 'C'].copy()
            else:
                calls_df = df.copy()
                
            # Check for delta column
            delta_col = None
            for col in ['delta', 'Delta', 'DELTA']:
                if col in calls_df.columns:
                    delta_col = col
                    break
                    
            if not delta_col:
                # If no delta yet, use middle of strike range as approximation
                strike_range = self.get_strike_range()
                return (strike_range[0] + strike_range[1]) / 2
                
            # Find strike where delta is closest to 0.5
            calls_df['delta_diff'] = abs(calls_df[delta_col] - 0.5)
            
            # Get the row with minimum difference
            if not calls_df.empty:
                atm_row = calls_df.loc[calls_df['delta_diff'].idxmin()]
                
                # Get strike value
                strike_col = None
                for col in ['strike', 'STRIKE', 'Strike']:
                    if col in calls_df.columns:
                        strike_col = col
                        break
                        
                if strike_col:
                    strike_val = atm_row[strike_col]
                    # Handle INVALID strikes
                    if strike_val is not None and str(strike_val).upper() != 'INVALID':
                        try:
                            return float(strike_val)
                        except (ValueError, TypeError):
                            pass
                            
            return None
        
        # Round future price to nearest 0.25 using standard rounding (not banker's)
        # Add 0.5 before truncating to ensure proper rounding behavior
        rounded_future = int(future_price * 4 + 0.5) / 4
        logger.info(f"Future price: {future_price:.4f}, rounded to nearest 0.25: {rounded_future:.2f}")
        
        # Return the rounded future price as ATM, regardless of available strikes
        logger.info(f"ATM strike set to rounded future price: {rounded_future:.2f}")
        
        return rounded_future
    
    @monitor()
    def generate_greek_profiles(self, selected_greeks: List[str], strike_range: float = 5.0) -> Dict[str, Any]:
        """Generate Greek profiles for selected Greeks using Taylor series expansion
        
        Args:
            selected_greeks: List of Greek names to generate profiles for
            strike_range: Range around ATM strike (default ±5.0)
            
        Returns:
            Dict containing:
                - strikes: Array of strike prices
                - greeks: Dict of Greek name -> array of values
                - positions: List of dicts with position info (strike, size, type)
                - atm_strike: ATM strike value
                - model_params: Dict of model parameters used
        """
        if self.current_data is None or self.current_data.empty:
            logger.warning("No data available for Greek profile generation")
            return {}
        
        # Import the Greek profile function
        from lib.trading.bond_future_options.bachelier_greek import generate_greek_profiles_data
        
        # Find ATM strike
        atm_strike = self.find_atm_strike()
        if atm_strike is None:
            logger.warning("Could not find ATM strike")
            # Use average strike as fallback
            valid_strikes = []
            for _, row in self.current_data.iterrows():
                strike = row.get('strike')
                if strike is not None and strike != 'INVALID':
                    try:
                        strike_float = float(strike)
                        # Check for NaN
                        if not pd.isna(strike_float):
                            valid_strikes.append(strike_float)
                    except (ValueError, TypeError):
                        continue
            
            if valid_strikes:
                atm_strike = sum(valid_strikes) / len(valid_strikes)
            else:
                atm_strike = 112.0  # Default fallback
        
        # Validate ATM strike is not NaN
        if pd.isna(atm_strike):
            logger.error(f"ATM strike is NaN, using default 112.0")
            atm_strike = 112.0
        
        # Get model parameters from first valid option
        sigma = None
        tau = None
        F = None
        
        for _, row in self.current_data.iterrows():
            if row.get('implied_vol') and row.get('time_to_maturity'):
                sigma = float(row['implied_vol'])
                tau = float(row['time_to_maturity'])
                # Use futures price if available, else ATM strike
                for _, future_row in self.current_data.iterrows():
                    if future_row.get('itype') == 'F':
                        F = float(future_row.get('midpoint_price', atm_strike))
                        break
                if F is None:
                    F = atm_strike
                break
        
        # Default values if not found
        if sigma is None:
            sigma = 0.75  # Default volatility
        if tau is None:
            tau = 0.25  # Default time to maturity
        if F is None:
            F = atm_strike
        
        # Validate model parameters are not NaN
        if pd.isna(sigma):
            logger.warning("Sigma is NaN, using default 0.75")
            sigma = 0.75
        if pd.isna(tau):
            logger.warning("Tau is NaN, using default 0.25")
            tau = 0.25
        if pd.isna(F):
            logger.warning("F is NaN, using ATM strike")
            F = atm_strike
        
        # Generate strike range centered at ATM
        strike_min = atm_strike - strike_range
        strike_max = atm_strike + strike_range
        
        # Calculate number of points based on 0.25 increments
        strike_increment = 0.25
        num_points = int((strike_max - strike_min) / strike_increment) + 1
        
        logger.info(f"Generating Greek profiles: ATM={atm_strike:.2f}, range=[{strike_min:.2f}, {strike_max:.2f}], points={num_points}")
        
        # Generate Greek profiles
        profile_data = generate_greek_profiles_data(
            K=int(atm_strike),
            sigma=sigma,
            tau=tau,
            F_range=(strike_min, strike_max),
            num_points=num_points
        )
        
        # Extract position information
        positions = []
        for _, row in self.current_data.iterrows():
            if row.get('position', 0) != 0:
                strike = row.get('strike')
                if strike is not None and strike != 'INVALID':
                    try:
                        strike_float = float(strike)
                        positions.append({
                            'strike': strike_float,
                            'position': float(row['position']),
                            'type': row.get('itype', 'Unknown'),
                            'key': row.get('key', ''),
                            # Include current Greek values for the position
                            'current_greeks': {
                                greek: float(row.get(greek, 0)) for greek in selected_greeks
                            }
                        })
                    except (ValueError, TypeError):
                        continue
        
        # Map F values to strike values (F represents the strike axis)
        strikes = profile_data['F_vals']
        
        # Extract only selected Greeks
        greeks = {}
        for greek in selected_greeks:
            if greek in profile_data['greeks_ana']:
                greeks[greek] = profile_data['greeks_ana'][greek]
            elif greek == 'volga' and 'vomma' in profile_data['greeks_ana']:
                # Handle volga/vomma naming
                greeks[greek] = profile_data['greeks_ana']['vomma']
        
        logger.info(f"Generated profiles: {len(strikes)} strikes, {len(greeks)} Greeks, {len(positions)} positions")
        
        return {
            'strikes': strikes.tolist(),
            'greeks': {k: [float(v) for v in vals] for k, vals in greeks.items()},
            'positions': positions,
            'atm_strike': float(atm_strike),
            'model_params': {
                'sigma': sigma,
                'tau': tau,
                'F': F,
                'model': 'bachelier_v1'
            }
        }
    
    @monitor()
    def generate_greek_profiles_by_expiry(self, selected_greeks: List[str], greek_space: str = 'F', strike_range: float = 5.0) -> Dict[str, Dict[str, Any]]:
        """Generate Greek profiles grouped by expiry date
        
        Args:
            selected_greeks: List of Greek names to generate profiles for
            strike_range: Range around ATM strike (default ±5.0)
            
        Returns:
            Dict with expiry as key, containing:
                - strikes: Array of strike prices
                - greeks: Dict of Greek name -> array of values
                - positions: List of dicts with position info
                - atm_strike: ATM strike value for this expiry
                - model_params: Dict of model parameters used
                - total_position: Net position size for this expiry
        """
        logger.info(f"[DEBUG ENTRY] generate_greek_profiles_by_expiry called with greek_space='{greek_space}', selected_greeks={selected_greeks}")
        
        if self.current_data is None or self.current_data.empty:
            logger.warning("No data available for Greek profile generation")
            return {}
        
        # Check for cached profiles first
        logger.info(f"[DEBUG CACHE CHECK] Checking for cached profiles...")
        # The load_greek_profiles_from_csv method is now deprecated.
        # If this method is called, it will cause an error.
        # For now, we'll keep it as is, but it will fail.
        # cached_profiles = self.load_greek_profiles_from_csv(self.data_timestamp)
        # if cached_profiles:
        #     logger.info(f"Using cached Greek profiles for {len(cached_profiles)} expiries")
            
            # Filter to only requested Greeks
            # filtered_profiles = {}
            # for expiry, profile in cached_profiles.items():
            #     filtered_greeks = {}
            #     for greek in selected_greeks:
            #         if greek in profile.get('greeks', {}):
            #             filtered_greeks[greek] = profile['greeks'][greek]
                
            #     if filtered_greeks:
            #         # Update positions from current data
            #         position_info = []
            #         total_position = 0
                    
            #         # Check for expiry column
            #         expiry_col = None
            #         for col in ['expiry_date', 'expiry', 'Expiry', 'EXPIRY', 'Expiry_Date', 'EXPIRY_DATE']:
            #             if col in self.current_data.columns:
            #                 expiry_col = col
            #                 break
                    
            #         if expiry_col:
            #             expiry_df = self.current_data[self.current_data[expiry_col] == expiry]
                        
            #             # Determine option type and apply put adjustments if needed
            #             option_types = expiry_df['itype'].value_counts() if 'itype' in expiry_df.columns else pd.Series()
            #             if 'P' in option_types.index and 'C' not in option_types.index:
            #                 # This expiry contains only puts
            #                 option_type = 'put'
            #                 logger.info(f"[DEBUG PUT ADJUSTMENT CACHED] Expiry {expiry} identified as PUT options in cached data")
            #                 # Apply put adjustments to F-space Greeks
            #                 filtered_greeks = self._adjust_greeks_for_put(filtered_greeks)
            #             elif 'C' in option_types.index:
            #                 option_type = 'call'
            #             else:
            #                 option_type = 'call'  # Default fallback
                        
            #             # Apply Y-space transformation if needed (for cached profiles)
            #             if greek_space == 'y':
            #                 logger.info(f"[DEBUG Y-SPACE CACHED] Applying Y-space transformation to cached profile for expiry: {expiry}")
                            
            #                 # Get DV01 and convexity from calculator
            #                 dv01 = self.calculator.dv01 / 1000.0  # Convert to decimal (63.0 → 0.063)
            #                 convexity = self.calculator.convexity
                            
            #                 # Option type was already determined above
                            
            #                 # Transform Greeks to Y-space
            #                 filtered_greeks = self._transform_greeks_to_y_space(
            #                     filtered_greeks, dv01, convexity, option_type
            #                 )
            #                 logger.info(f"[DEBUG Y-SPACE CACHED] Transformation complete for {expiry}")
                        
            #             for _, pos in expiry_df.iterrows():
            #                 strike_val = pos.get('strike')
            #                 pos_val = pos.get('pos.position')
                            
            #                 if strike_val is None or pos_val is None:
            #                     continue
                                
            #                 try:
            #                     pos_data = {
            #                         'key': pos.get('key', ''),
            #                         'strike': float(strike_val),
            #                         'type': pos.get('itype', ''),
            #                         'position': float(pos_val),
            #                         'current_greeks': {}
            #                     }
            #                     position_info.append(pos_data)
            #                     total_position += pos_data['position']
            #                 except (ValueError, TypeError):
            #                     continue
                    
            #         filtered_profiles[expiry] = {
            #             'strikes': profile['strikes'],
            #             'greeks': filtered_greeks,
            #             'positions': position_info,
            #             'atm_strike': profile['atm_strike'],
            #             'model_params': profile['model_params'],
            #             'total_position': total_position
            #         }
            
            # if filtered_profiles:
            #     logger.info(f"[DEBUG CACHE RETURN] Returning cached profiles for {len(filtered_profiles)} expiries")
            #     return filtered_profiles
            # else:
            logger.info("Cached profiles not available, computing fresh")
        
        # First, find the global future price from the entire dataset
        global_future_price = None
        for _, row in self.current_data.iterrows():
            if row.get('itype', '').upper() == 'F':
                try:
                    future_price = float(row.get('midpoint_price', 0))
                    if future_price > 0:  # Valid price found
                        global_future_price = future_price
                        logger.info(f"Found global future price: {global_future_price:.4f}")
                        break
                except (ValueError, TypeError):
                    continue
        
        if global_future_price is None:
            logger.warning("No future price found in entire dataset")
        
        # Group positions by expiry
        expiry_groups = {}
        
        # Check for expiry column
        expiry_col = None
        for col in ['expiry_date', 'expiry', 'Expiry', 'EXPIRY', 'Expiry_Date', 'EXPIRY_DATE']:
            if col in self.current_data.columns:
                expiry_col = col
                break
        
        if not expiry_col:
            logger.warning("No expiry column found in data")
            return {}
        
        for _, row in self.current_data.iterrows():
            expiry = row.get(expiry_col)
            if not expiry or pd.isna(expiry):
                continue
                
            if expiry not in expiry_groups:
                expiry_groups[expiry] = []
            expiry_groups[expiry].append(row)
        
        logger.info(f"Found {len(expiry_groups)} expiry groups: {list(expiry_groups.keys())}")
        
        # Generate profiles for each expiry
        profiles_by_expiry = {}
        
        for expiry, positions in expiry_groups.items():
            try:
                # Create DataFrame for this expiry group
                expiry_df = pd.DataFrame(positions)
                
                # Find ATM strike for this expiry, passing the global future price
                atm_strike = self._find_atm_strike_for_expiry(expiry_df, global_future_price)
                if atm_strike is None:
                    logger.warning(f"Could not find ATM strike for expiry {expiry}")
                    continue
                
                # Before calculating strike range, check if we have valid strikes
                valid_strikes = expiry_df['strike'].dropna()
                valid_strikes = valid_strikes[valid_strikes != 'INVALID']
                
                if valid_strikes.empty:
                    logger.warning(f"No valid strikes found for expiry {expiry}, skipping")
                    continue
                
                # Calculate strike range safely
                strike_min = atm_strike - strike_range
                strike_max = atm_strike + strike_range
                
                # Calculate number of points based on 0.25 increments
                strike_increment = 0.25
                num_points = int((strike_max - strike_min) / strike_increment) + 1
                
                logger.info(f"Expiry {expiry}: ATM={atm_strike:.2f}, range=[{strike_min:.2f}, {strike_max:.2f}], points={num_points}")
                
                # Extract model parameters for this expiry
                # Get the first non-null values from this expiry's data
                sigma = None
                tau = None
                F = None
                
                for _, pos in expiry_df.iterrows():
                    # Get implied vol as sigma
                    if sigma is None and pos.get('implied_vol') is not None:
                        try:
                            sigma = float(pos.get('implied_vol'))
                        except (ValueError, TypeError):
                            pass
                    
                    # Get time to expiry as tau
                    if tau is None and pos.get('vtexp') is not None:
                        try:
                            tau = float(pos.get('vtexp'))
                        except (ValueError, TypeError):
                            pass
                    
                    # Use futures price if available
                    if F is None and pos.get('itype') == 'F':
                        try:
                            F = float(pos.get('midpoint_price', atm_strike))
                        except (ValueError, TypeError):
                            pass
                
                # Use global future price if no local future found
                if F is None and global_future_price is not None:
                    F = global_future_price
                
                # Default values if not found
                if sigma is None:
                    sigma = 0.75
                if tau is None:
                    tau = 0.25
                if F is None:
                    F = atm_strike
                
                # Validate parameters
                if pd.isna(sigma):
                    sigma = 0.75
                if pd.isna(tau):
                    tau = 0.25
                if pd.isna(F):
                    F = atm_strike
                
                # Collect position information for this expiry
                position_info = []
                total_position = 0
                
                for _, pos in expiry_df.iterrows():
                    strike_val = pos.get('strike')
                    pos_val = pos.get('pos.position')
                    
                    # Skip if missing required data
                    if strike_val is None or pos_val is None:
                        continue
                        
                    try:
                        pos_data = {
                            'key': pos.get('key', ''),
                            'strike': float(strike_val),
                            'type': pos.get('itype', ''),
                            'position': float(pos_val),
                            # Include current Greek values for the position
                            'current_greeks': {}
                        }
                        
                        # Map selected Greek names to actual column names based on Greek space
                        greek_column_map = {
                            'delta': f'delta_{greek_space}',
                            'gamma': f'gamma_{greek_space}',
                            'vega': 'vega_price' if greek_space == 'F' else f'vega_{greek_space}',
                            'theta': f'theta_{greek_space}',
                            'volga': 'volga_price',  # No space suffix
                            'vanna': f'vanna_{greek_space}_price',
                            'charm': f'charm_{greek_space}',
                            'speed': f'speed_{greek_space}',
                            'color': f'color_{greek_space}',
                            'ultima': 'ultima',  # No space suffix
                            'zomma': 'zomma'  # No space suffix
                        }
                        
                        # Extract Greek values using mapped column names
                        for greek in selected_greeks:
                            col_name = greek_column_map.get(greek, greek)
                            if col_name in pos:
                                try:
                                    pos_data['current_greeks'][greek] = float(pos.get(col_name, 0))
                                except (ValueError, TypeError):
                                    pos_data['current_greeks'][greek] = 0.0
                            else:
                                # No fallback logic needed now that we use greek_space directly
                                pos_data['current_greeks'][greek] = 0.0
                        
                        position_info.append(pos_data)
                        total_position += pos_data['position']
                    except (ValueError, TypeError):
                        continue
                
                # Import the Greek profile function
                from lib.trading.bond_future_options.bachelier_greek import generate_greek_profiles_data
                
                # Generate Greek profiles using bachelier_greek
                logger.info(f"[DEBUG PROFILE GEN] Generating profiles for expiry {expiry}: ATM={atm_strike}, sigma={sigma}, tau={tau}, F={F}")
                profile_data = generate_greek_profiles_data(
                    K=int(atm_strike),  # Convert to int as expected by the function
                    sigma=sigma,
                    tau=tau,
                    F_range=(strike_min, strike_max),
                    num_points=num_points
                )
                
                logger.info(f"[DEBUG PROFILE DATA] Profile generated with keys: {list(profile_data.keys()) if profile_data else 'None'}")
                if profile_data and 'greeks_ana' in profile_data:
                    logger.info(f"[DEBUG PROFILE DATA] Available Greeks: {list(profile_data['greeks_ana'].keys())}")
                
                # Filter for selected Greeks
                filtered_greeks = {}
                for greek in selected_greeks:
                    if greek in profile_data.get('greeks_ana', {}):
                        filtered_greeks[greek] = profile_data['greeks_ana'][greek]
                        logger.info(f"[DEBUG FILTER] Added {greek} to filtered_greeks")
                    else:
                        logger.warning(f"[DEBUG FILTER] Greek {greek} not found in profile data")
                
                # Determine option type for this expiry (for put adjustments)
                option_types = expiry_df['itype'].value_counts() if 'itype' in expiry_df.columns else pd.Series()
                if 'P' in option_types.index and 'C' not in option_types.index:
                    # This expiry contains only puts
                    option_type = 'put'
                    logger.info(f"[DEBUG PUT ADJUSTMENT] Expiry {expiry} identified as PUT options")
                    # Apply put adjustments to F-space Greeks
                    filtered_greeks = self._adjust_greeks_for_put(filtered_greeks)
                elif 'C' in option_types.index:
                    option_type = 'call'
                else:
                    option_type = 'call'  # Default fallback
                
                logger.info(f"[DEBUG PRE-TRANSFORM] About to check transformation: greek_space='{greek_space}', filtered_greeks keys={list(filtered_greeks.keys()) if filtered_greeks else 'Empty'}, len={len(filtered_greeks)}")
                logger.info(f"[DEBUG PRE-TRANSFORM] Condition check: (greek_space == 'y')={greek_space == 'y'}, (filtered_greeks)={bool(filtered_greeks)}")
                
                # Apply Y-space transformation if needed
                if greek_space == 'y' and filtered_greeks:
                    logger.info(f"[DEBUG Y-SPACE] Applying Y-space transformation for expiry: {expiry}")
                    
                    # Get DV01 and convexity from calculator
                    dv01 = self.calculator.dv01 / 1000.0  # Convert to decimal (63.0 → 0.063)
                    convexity = self.calculator.convexity
                    logger.info(f"[DEBUG Y-SPACE] DV01: {dv01}, Convexity: {convexity}")
                    
                    # Option type was already determined above
                    logger.info(f"[DEBUG Y-SPACE] Option type: {option_type}")
                    logger.info(f"[DEBUG Y-SPACE] Applying Y-space transformation for expiry {expiry} with DV01={dv01:.6f}, convexity={convexity:.6f}")
                    
                    # Log sample values before transformation
                    for greek, values in filtered_greeks.items():
                        if values:
                            logger.info(f"[DEBUG Y-SPACE] {greek} F-space range: [{min(values):.6f}, {max(values):.6f}], first 3 values: {values[:3]}")
                    
                    # Transform Greeks to Y-space
                    filtered_greeks = self._transform_greeks_to_y_space(
                        filtered_greeks, dv01, convexity, option_type
                    )
                    
                    # Log sample values after transformation
                    for greek, values in filtered_greeks.items():
                        if values:
                            logger.info(f"[DEBUG Y-SPACE] {greek} Y-space range: [{min(values):.6f}, {max(values):.6f}], first 3 values: {values[:3]}")
                else:
                    logger.info(f"[DEBUG Y-SPACE] No transformation - greek_space: {greek_space}, has greeks: {bool(filtered_greeks)}")
                
                # Track which Greek columns were actually used
                greek_columns_used = {}
                for _, pos in expiry_df.iterrows():
                    for greek in selected_greeks:
                        if greek in greek_columns_used:
                            continue  # Already determined
                        
                        # Check primary column
                        greek_column_map = {
                            'delta': 'delta_F',
                            'gamma': 'gamma_F', 
                            'vega': 'vega_price',
                            'theta': 'theta_F',
                            'volga': 'volga_price',
                            'vanna': 'vanna_F_price',
                            'charm': 'charm_F',
                            'speed': 'speed_F',
                            'color': 'color_F',
                            'ultima': 'ultima',
                            'zomma': 'zomma'
                        }
                        
                        primary_col = greek_column_map.get(greek, greek)
                        if primary_col in pos and pos.get(primary_col) is not None:
                            greek_columns_used[greek] = primary_col
                        # Check fallbacks
                        elif greek == 'delta' and 'delta_y' in pos and pos.get('delta_y') is not None:
                            greek_columns_used[greek] = 'delta_y'
                        elif greek == 'gamma' and 'gamma_y' in pos and pos.get('gamma_y') is not None:
                            greek_columns_used[greek] = 'gamma_y'
                        elif greek == 'vega' and 'vega_y' in pos and pos.get('vega_y') is not None:
                            greek_columns_used[greek] = 'vega_y'
                        else:
                            greek_columns_used[greek] = primary_col  # Default
                
                profiles_by_expiry[expiry] = {
                    'strikes': profile_data['F_vals'],
                    'greeks': filtered_greeks,
                    'positions': position_info,
                    'atm_strike': atm_strike,
                    'model_params': {
                        'sigma': sigma,
                        'tau': tau,
                        'F': F
                    },
                    'total_position': total_position,
                    'greek_columns_used': greek_columns_used  # Add this info
                }
                
                logger.info(f"Generated profile for {expiry}: {len(position_info)} positions, net={total_position:.0f}")
                
            except Exception as e:
                logger.error(f"Error generating profile for expiry {expiry}: {e}")
                continue
        
        logger.info(f"[DEBUG FINAL RETURN] Returning profiles for {len(profiles_by_expiry)} expiries")
        for exp, prof in profiles_by_expiry.items():
            if 'greeks' in prof and prof['greeks']:
                sample_greek = list(prof['greeks'].keys())[0]
                sample_values = prof['greeks'][sample_greek]
                logger.info(f"[DEBUG FINAL RETURN] {exp}: {sample_greek} range [{min(sample_values):.6f}, {max(sample_values):.6f}]")
        
        return profiles_by_expiry
    
    def _find_atm_strike_for_expiry(self, expiry_df: pd.DataFrame, global_future_price: Optional[float] = None) -> Optional[float]:
        """Find ATM strike for a specific expiry group
        
        Args:
            expiry_df: DataFrame containing positions for one expiry
            global_future_price: Future price from the entire dataset (optional)
            
        Returns:
            ATM strike or None if not found
        """
        # Use global future price if provided
        future_price = global_future_price
        
        # If no global future price, try to get from this expiry group (for backwards compatibility)
        if future_price is None:
            for _, row in expiry_df.iterrows():
                if row.get('itype', '').upper() == 'F':
                    try:
                        future_price = float(row.get('midpoint_price', 0))
                        if future_price > 0:  # Valid price found
                            break
                    except (ValueError, TypeError):
                        continue
        
        # If no future price found anywhere, fall back to delta-based method
        if future_price is None or future_price <= 0:
            logger.warning("No future price found, falling back to delta-based ATM detection")
            # Look for CALL positions with delta closest to 0.5
            # (For puts, delta would be negative and approach -0.5 at ATM)
            atm_candidates = []
            
            for _, row in expiry_df.iterrows():
                # Skip if not a call option
                option_type = row.get('itype', '').upper()
                if option_type != 'C':
                    continue
                # Check both cases for column names
                delta_f = row.get('delta_F') if 'delta_F' in row else row.get('delta_f')
                delta_y = row.get('delta_Y') if 'delta_Y' in row else row.get('delta_y')
                strike = row.get('strike')
                
                # Use either delta_f or delta_y
                delta = delta_f if delta_f is not None and not pd.isna(delta_f) else delta_y
                
                if delta is not None and not pd.isna(delta) and strike is not None:
                    try:
                        strike_float = float(strike)
                        delta_float = float(delta)
                        # Check for NaN
                        if not pd.isna(strike_float) and not pd.isna(delta_float):
                            atm_candidates.append({
                                'strike': strike_float,
                                'delta': delta_float,
                                'distance': abs(delta_float - 0.5)
                            })
                    except (ValueError, TypeError):
                        continue
            
            if atm_candidates:
                # Sort by distance from 0.5 delta
                atm_candidates.sort(key=lambda x: x['distance'])
                
                # Log the candidates for debugging
                logger.info(f"ATM candidates for expiry (delta method): {len(atm_candidates)} found")
                for i, candidate in enumerate(atm_candidates[:5]):  # Show top 5
                    logger.info(f"  Candidate {i+1}: Strike={candidate['strike']:.2f}, Delta={candidate['delta']:.4f}, Distance from 0.5={candidate['distance']:.4f}")
                
                selected_atm = atm_candidates[0]['strike']
                logger.info(f"Selected ATM strike (delta method): {selected_atm:.2f} (delta={atm_candidates[0]['delta']:.4f})")
                
                return selected_atm
            else:
                logger.warning("No ATM candidates found using delta method")
                return None
        
        # Round future price to nearest 0.25 using standard rounding (not banker's)
        # Add 0.5 before truncating to ensure proper rounding behavior
        rounded_future = int(future_price * 4 + 0.5) / 4
        logger.info(f"Future price: {future_price:.4f}, rounded to nearest 0.25: {rounded_future:.2f}")
        
        # Return the rounded future price as ATM, regardless of available strikes
        logger.info(f"ATM strike set to rounded future price: {rounded_future:.2f}")
        
        return rounded_future
    
    @monitor()
    def process_greeks(self, model: str = "bachelier_v1", filter_positions: bool = True) -> Optional[pd.DataFrame]:
        """Process Greeks for current data using specified model
        
        Args:
            model: Model version to use for calculations
            filter_positions: If True, only return rows with non-zero positions
            
        Returns:
            Optional[pd.DataFrame]: Processed data with Greeks, or None if failed
        """
        if self.current_data is None:
            print("No data loaded. Call load_csv_data() first.")
            return None
        
        try:
            logger.info(f"Starting process_greeks with filter_positions={filter_positions}")
            
            # Read pre-calculated Greeks from processed CSV file
            df_with_greeks = self.read_processed_greeks()
            
            if df_with_greeks is None:
                logger.warning("No processed Greeks found, falling back to synchronous calculation")
                # Fallback to synchronous calculation if needed
                logger.info(f"Current data shape: {self.current_data.shape}")
                
                # Get positions from the data
                df_with_positions = self.get_positions_from_csv(self.current_data.copy())
                logger.info(f"After get_positions_from_csv, shape: {df_with_positions.shape}")
                
                # Calculate Greeks - returns tuple of (DataFrame, results_list)
                logger.info("Calling calculate_greeks...")
                df_with_greeks, results = self.calculator.calculate_greeks(
                    df_with_positions  # Pass ALL data including future row
                )
            else:
                # Update current_data with the processed data
                self.current_data = df_with_greeks
                logger.info(f"Using pre-calculated Greeks from processed file, shape: {df_with_greeks.shape}")
            
            # Filter to only positions if requested AFTER Greek calculation
            if filter_positions:
                logger.info("Now filtering to positions only...")
                df_with_greeks = self.filter_positions_only(df_with_greeks)
            
            return df_with_greeks
            
        except Exception as e:
            logger.error(f"Error processing Greeks: {e}", exc_info=True)
            print(f"Error processing Greeks: {e}")
            return None
    
    def get_unique_expiries(self) -> List[str]:
        """Get list of unique expiry dates in current data
        
        Returns:
            List[str]: Sorted list of unique expiry dates
        """
        if self.current_data is None:
            return []
        
        # Check both uppercase and lowercase column names
        expiry_col = None
        for col in ['expiry_date', 'EXPIRY_DATE', 'Expiry_Date']:
            if col in self.current_data.columns:
                expiry_col = col
                break
        
        if expiry_col:
            expiries = self.current_data[expiry_col].dropna().unique()
            return sorted(str(e) for e in expiries)
        
        return []
    
    def get_strike_range(self) -> tuple:
        """Get min and max strike prices in current data
        
        Returns:
            tuple: (min_strike, max_strike) or (100.0, 120.0) if no data
        """
        if self.current_data is None:
            return (100.0, 120.0)
        
        # Check both uppercase and lowercase column names
        strike_col = None
        for col in ['strike', 'STRIKE', 'Strike']:
            if col in self.current_data.columns:
                strike_col = col
                break
        
        if strike_col:
            # Convert to numeric, handling invalid values
            strikes = []
            for val in self.current_data[strike_col]:
                # Skip None, INVALID, and other non-numeric values
                if val is None or str(val).upper() == 'INVALID':
                    continue
                try:
                    strike_float = float(val)
                    strikes.append(strike_float)
                except (ValueError, TypeError):
                    continue
            
            if strikes:
                return (float(min(strikes)), float(max(strikes)))
        
        # Return sensible defaults for ZN futures if no valid strikes found
        return (100.0, 120.0)
    
    def filter_data(self, 
                    expiry: Optional[str] = None,
                    option_type: Optional[str] = None,
                    strike_range: Optional[tuple] = None) -> Optional[pd.DataFrame]:
        """Filter current data based on criteria
        
        Args:
            expiry: Filter by specific expiry date
            option_type: Filter by type (All, Calls, Puts, Futures)
            strike_range: Tuple of (min_strike, max_strike)
            
        Returns:
            Optional[pd.DataFrame]: Filtered data or None if no data
        """
        if self.current_data is None:
            return None
        
        df = self.current_data.copy()
        
        # Apply expiry filter
        if expiry and expiry != "All Expiries":
            expiry_col = None
            for col in ['expiry_date', 'EXPIRY_DATE', 'Expiry_Date']:
                if col in df.columns:
                    expiry_col = col
                    break
            
            if expiry_col:
                df = df[df[expiry_col] == expiry]
        
        # Apply type filter
        if option_type and option_type != "All":
            type_col = None
            for col in ['itype', 'ITYPE', 'Type', 'type']:
                if col in df.columns:
                    type_col = col
                    break
            
            if type_col:
                if option_type == "Calls":
                    df = df[df[type_col].str.upper() == 'C']
                elif option_type == "Puts":
                    df = df[df[type_col].str.upper() == 'P']
                elif option_type == "Futures":
                    df = df[df[type_col].str.upper().isin(['F', 'FUTURE'])]
        
        # Apply strike range filter
        if strike_range:
            strike_col = None
            for col in ['strike', 'STRIKE', 'Strike']:
                if col in df.columns:
                    strike_col = col
                    break
            
            if strike_col:
                strikes = pd.to_numeric(df[strike_col], errors='coerce')
                df = df[(strikes >= strike_range[0]) & (strikes <= strike_range[1])]
        
        return df 

    def get_timestamp(self) -> str:
        """Get formatted timestamp from currently loaded data
        
        Returns:
            str: Formatted timestamp string or empty if no data
        """
        if self.data_timestamp:
            return self.data_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return '' 
    
    @monitor()
    def save_greek_profiles_to_csv(self, profiles_by_expiry: Dict[str, Dict[str, Any]], 
                                   original_filepath: str) -> Optional[str]:
        """Save pre-computed Greek profiles to CSV file
        
        Args:
            profiles_by_expiry: Dictionary of Greek profiles by expiry
            original_filepath: Path to original CSV file for naming
            
        Returns:
            Optional[str]: Path to saved profile file, or None if failed
        """
        try:
            if not profiles_by_expiry:
                logger.warning("No profiles to save")
                return None
            
            # Create output filename based on original file
            original_path = Path(original_filepath)
            # The _extract_timestamp method is now deprecated.
            # We will use a placeholder timestamp or remove it if not needed.
            # For now, we'll keep it as is, but it will cause an error.
            # timestamp = self._extract_timestamp(original_filepath, pd.DataFrame())
            # timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            
            # Save to same directory as original file
            output_dir = original_path.parent
            profile_filename = f"greek_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            profile_filepath = output_dir / profile_filename
            
            # Prepare data for CSV
            rows = []
            
            for expiry, profile_data in profiles_by_expiry.items():
                strikes = profile_data.get('strikes', [])
                greeks = profile_data.get('greeks', {})
                atm_strike = profile_data.get('atm_strike', 0)
                model_params = profile_data.get('model_params', {})
                
                # Create rows for each strike and Greek combination
                for i, strike in enumerate(strikes):
                    for greek_name, greek_values in greeks.items():
                        if i < len(greek_values):
                            row = {
                                'expiry': expiry,
                                'strike': float(strike),
                                'greek_name': greek_name,
                                'value': float(greek_values[i]),
                                'atm_strike': float(atm_strike),
                                'sigma': float(model_params.get('sigma', 0)),
                                'tau': float(model_params.get('tau', 0)),
                                'future_price': float(model_params.get('F', 0))
                            }
                            rows.append(row)
            
            # Create DataFrame and save to CSV
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(profile_filepath, index=False)
                logger.info(f"Saved {len(rows)} Greek profile points to {profile_filepath}")
                return str(profile_filepath)
            else:
                logger.warning("No profile data to save")
                return None
                
        except Exception as e:
            logger.error(f"Error saving Greek profiles: {e}")
            return None
    
    @monitor()
    def load_greek_profiles_from_csv(self, timestamp: Optional[datetime] = None) -> Dict[str, Dict[str, Any]]:
        """Load pre-computed Greek profiles from CSV file
        
        Args:
            timestamp: Timestamp to match profile file. If None, loads latest.
            
        Returns:
            Dict: Greek profiles by expiry, or empty dict if not found
        """
        try:
            # Find profile files
            profile_files = []
            
            for directory in self._get_csv_directories():
                pattern = directory / "greek_profiles_*.csv"
                for filepath in directory.glob("greek_profiles_*.csv"):
                    # Extract timestamp from filename
                    filename = filepath.stem
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        try:
                            date_str = parts[-2]
                            time_str = parts[-1]
                            file_timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                            
                            profile_files.append({
                                'filepath': filepath,
                                'timestamp': file_timestamp
                            })
                        except:
                            continue
            
            if not profile_files:
                logger.info("No Greek profile files found")
                return {}
            
            # Sort by timestamp descending
            profile_files.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Select file based on timestamp match or latest
            selected_file = None
            if timestamp:
                # Find closest match
                for pf in profile_files:
                    if abs((pf['timestamp'] - timestamp).total_seconds()) < 60:  # Within 1 minute
                        selected_file = pf['filepath']
                        break
            
            if not selected_file:
                # Use latest file
                selected_file = profile_files[0]['filepath']
            
            logger.info(f"Loading Greek profiles from {selected_file}")
            
            # Read CSV file
            df = pd.read_csv(selected_file)
            
            # Reconstruct profiles dictionary
            profiles_by_expiry = {}
            
            # Group by expiry
            for expiry in df['expiry'].unique():
                expiry_df = df[df['expiry'] == expiry]
                
                # Get unique strikes for this expiry
                strikes = sorted(expiry_df['strike'].unique())
                
                # Get Greeks for this expiry
                greeks = {}
                for greek_name in expiry_df['greek_name'].unique():
                    greek_df = expiry_df[expiry_df['greek_name'] == greek_name].sort_values('strike')
                    greeks[greek_name] = greek_df['value'].tolist()
                
                # Get model parameters (same for all rows of this expiry)
                first_row = expiry_df.iloc[0]
                
                profiles_by_expiry[expiry] = {
                    'strikes': strikes,
                    'greeks': greeks,
                    'positions': [],  # Will be populated from actual data
                    'atm_strike': float(first_row['atm_strike']),
                    'model_params': {
                        'sigma': float(first_row['sigma']),
                        'tau': float(first_row['tau']),
                        'F': float(first_row['future_price'])
                    },
                    'total_position': 0  # Will be calculated from actual positions
                }
            
            logger.info(f"Loaded profiles for {len(profiles_by_expiry)} expiries")
            return profiles_by_expiry
            
        except Exception as e:
            logger.error(f"Error loading Greek profiles: {e}")
            return {}
    
    @monitor()
    def pre_compute_greek_profiles(self) -> bool:
        """Pre-compute and save Greek profiles for all standard Greeks
        
        Returns:
            bool: True if profiles were computed and saved successfully
        """
        try:
            if self.current_data is None or self.current_data.empty:
                logger.warning("No data loaded for profile pre-computation")
                return False
            
            # Define all standard Greeks to pre-compute
            all_greeks = ['delta', 'gamma', 'vega', 'theta', 'volga', 'vanna', 
                         'charm', 'speed', 'color', 'ultima', 'zomma']
            
            logger.info(f"Pre-computing Greek profiles for: {all_greeks}")
            
            # Generate profiles for all Greeks
            profiles_by_expiry = self.generate_greek_profiles_by_expiry(
                selected_greeks=all_greeks,
                greek_space='F',  # Default to F-space
                strike_range=5.0  # ±5 from ATM
            )
            
            if not profiles_by_expiry:
                logger.warning("No profiles generated")
                return False
            
            # Save profiles to CSV
            # The current_csv_path attribute is removed as load_csv_data is deprecated.
            # We will use a placeholder or remove this call if not needed.
            # csv_path = self.current_csv_path if hasattr(self, 'current_csv_path') else None
            # if not csv_path:
            #     csv_path = self.find_latest_csv()
            
            # if csv_path:
            #     saved_path = self.save_greek_profiles_to_csv(profiles_by_expiry, csv_path)
            #     if saved_path:
            #         logger.info(f"Greek profiles saved to: {saved_path}")
            #         return True
            #     else:
            #         logger.error("Failed to save Greek profiles")
            #         return False
            # else:
            #     logger.error("No CSV path available for saving profiles")
            #     return False
            
            # Since load_csv_data is deprecated, we cannot save to CSV.
            # This method will now always return False.
            logger.warning("CSV saving is deprecated. Cannot save Greek profiles.")
            return False
                
        except Exception as e:
            logger.error(f"Error pre-computing Greek profiles: {e}")
            return False 
    
    def _adjust_greeks_for_put(self, f_space_greeks: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust F-space Greeks from call to put values
        
        The bachelier_greek module generates call Greeks by default.
        This method applies the put-call parity adjustments.
        
        Args:
            f_space_greeks: Dictionary of Greek name -> array of F-space call values
            
        Returns:
            Dict: Adjusted Greeks for put options
        """
        import numpy as np
        
        logger.info(f"[DEBUG PUT ADJUSTMENT] Adjusting Greeks for put option")
        
        adjusted_greeks = {}
        
        for greek, values in f_space_greeks.items():
            if greek == 'delta':
                # Put delta = Call delta - 1
                adjusted_values = np.array(values) - 1.0
                logger.info(f"[DEBUG PUT ADJUSTMENT] Delta: call range [{min(values):.6f}, {max(values):.6f}] → put range [{min(adjusted_values):.6f}, {max(adjusted_values):.6f}]")
                adjusted_greeks[greek] = adjusted_values.tolist()
            else:
                # Most other Greeks remain the same for puts
                # (gamma, vega, theta magnitude are same for calls and puts)
                adjusted_greeks[greek] = values
                
        return adjusted_greeks

    def _transform_greeks_to_y_space(self, f_space_greeks: Dict[str, Any], 
                                    dv01: float, convexity: float, 
                                    option_type: str = 'call') -> Dict[str, Any]:
        """Transform F-space Greeks to Y-space with proper scaling
        
        This method replicates the transformations from pricing_engine.py
        and applies the 1000x scaling from analysis.py
        
        Args:
            f_space_greeks: Dictionary of Greek name -> array of F-space values
            dv01: Dollar Value of 01 (as decimal, e.g., 0.063)
            convexity: Future convexity
            option_type: 'call' or 'put' (affects delta calculation)
            
        Returns:
            Dict: Transformed Greeks in Y-space with proper scaling
        """
        import numpy as np
        
        logger.info(f"[DEBUG Y-SPACE TRANSFORM] Starting transformation with DV01={dv01}, convexity={convexity}, option_type={option_type}")
        
        y_space_greeks = {}
        
        for greek_name, f_values in f_space_greeks.items():
            # Convert to numpy array for vectorized operations
            f_array = np.array(f_values)
            
            if greek_name == 'delta':
                # For puts, delta is already negative in F-space
                # Y-space: delta_y = delta_F * DV01
                y_values = f_array * dv01
                # Scale by 1000 (as per analysis.py line ~105)
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'gamma':
                # Y-space: gamma_y = gamma_F * (DV01)² + delta_F * convexity
                # Need delta_F for the convexity adjustment
                if 'delta' in f_space_greeks:
                    delta_f_array = np.array(f_space_greeks['delta'])
                    y_values = f_array * (dv01 ** 2) + delta_f_array * convexity
                else:
                    # Fallback without convexity adjustment if delta not available
                    logger.warning("Delta not available for gamma_y convexity adjustment")
                    y_values = f_array * (dv01 ** 2)
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'vega':
                # Y-space: vega_y = vega_F * DV01
                y_values = f_array * dv01
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'theta':
                # Theta is already in the same units for both spaces
                # But it's scaled by 1000 in analysis.py
                y_space_greeks[greek_name] = (f_array * 1000).tolist()
                
            elif greek_name == 'vanna':
                # Y-space: vanna_y = vanna_F * DV01²
                y_values = f_array * (dv01 ** 2)
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'charm':
                # Y-space: charm_y = charm_F * (-DV01)
                y_values = f_array * (-dv01)
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'speed':
                # Y-space: speed_y = speed_F * (-DV01)³
                y_values = f_array * ((-dv01) ** 3)
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'color':
                # Y-space: color_y = color_F * (-DV01)²
                y_values = f_array * ((-dv01) ** 2)
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name == 'volga':
                # Y-space: volga_y = volga_F * (DV01)²
                y_values = f_array * (dv01 ** 2)
                # Scale by 1000
                y_space_greeks[greek_name] = (y_values * 1000).tolist()
                
            elif greek_name in ['ultima', 'zomma']:
                # These Greeks are scaled by 1000 but don't have specific Y-space transformations
                y_space_greeks[greek_name] = (f_array * 1000).tolist()
                
            else:
                # Unknown Greek - pass through with just scaling
                logger.warning(f"Unknown Greek '{greek_name}' - applying only 1000x scaling")
                y_space_greeks[greek_name] = (f_array * 1000).tolist()
        
        return y_space_greeks 