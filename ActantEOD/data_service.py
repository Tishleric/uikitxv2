#!/usr/bin/env python3
"""
Data Service Implementation for ActantEOD

This module provides the concrete implementation of data operations for ActantEOD,
including SQLite database interaction and data filtering capabilities.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import the protocol from the core module
import sys
import os

# Add project root to path and create module alias
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Create module alias for imports
import src
sys.modules['uikitxv2'] = src

from uikitxv2.core.data_service_protocol import DataServiceProtocol

# Import new PM modules
from pricing_monkey_retrieval import get_extended_pm_data, PMRetrievalError
from pricing_monkey_processor import process_pm_for_separate_table, validate_pm_data

logger = logging.getLogger(__name__)


class ActantDataService(DataServiceProtocol):
    """
    Concrete implementation of data service for ActantEOD scenario metrics.
    
    This service handles loading data from JSON files, storing in SQLite,
    and providing filtered access to the data for dashboard components.
    """
    
    def __init__(self, db_path: str = "actant_eod_data.db"):
        """
        Initialize the data service.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.table_name = "scenario_metrics"
        self.pm_table_name = "pm_data"  # Separate table for PM data
        self._data_loaded = False
        self._current_file = None
        self._pm_data_loaded = False
        
    def load_data_from_json(self, json_file_path: Path) -> bool:
        """
        Load and process data from a JSON file into SQLite database.
        
        Args:
            json_file_path: Path to the Actant JSON file to load
            
        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading data from {json_file_path}")
            
            # Load and parse JSON
            with open(json_file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Process data using existing logic from process_actant_json.py
            flattened_records = self._flatten_data(raw_data)
            
            if not flattened_records:
                logger.warning("No data records extracted from JSON")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(flattened_records)
            logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
            
            # Save to SQLite
            self._save_to_database(df)
            
            self._data_loaded = True
            self._current_file = json_file_path
            logger.info(f"Successfully loaded data from {json_file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data from {json_file_path}: {e}")
            self._data_loaded = False
            return False
    
    def _flatten_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten the nested JSON structure into a list of records.
        
        Args:
            raw_data: The parsed JSON data from the file
            
        Returns:
            List of flat dictionaries for DataFrame conversion
        """
        flattened_records = []
        totals_list = raw_data.get("totals", [])
        
        for scenario in totals_list:
            scenario_header = scenario.get("header")
            scenario_uprice = self._try_convert_to_float(str(scenario.get("uprice", 0)))
            
            for point in scenario.get("points", []):
                original_point_header = point.get("header")
                shock_value, shock_type, _ = self._parse_point_header(original_point_header)
                
                # Create base record with scenario and point info
                record = {
                    "scenario_header": scenario_header,
                    "uprice": scenario_uprice,
                    "point_header_original": original_point_header,
                    "shock_value": shock_value,
                    "shock_type": shock_type,
                }
                
                # Add all metrics from the values dict
                for metric_name, metric_value_str in point.get("values", {}).items():
                    record[metric_name] = self._try_convert_to_float(metric_value_str)
                
                flattened_records.append(record)
        
        return flattened_records
    
    def _try_convert_to_float(self, value_str: str) -> float:
        """
        Attempt to convert a string value to float, handling "na" values.
        
        Args:
            value_str: String representation of a number or "na"
            
        Returns:
            Converted float value or np.nan for "na" or conversion errors
        """
        if isinstance(value_str, (int, float)):
            return float(value_str)
        
        if str(value_str).lower() == "na":
            return np.nan
        
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return np.nan
    
    def _parse_point_header(self, header_str: str) -> tuple:
        """
        Parse a point header string into a numeric value and type.
        
        Args:
            header_str: The header string (e.g., "-30%", "-2", "0.25")
            
        Returns:
            Tuple of (shock_value, shock_type, original_header_str)
        """
        if not header_str:
            return None, None, header_str
        
        try:
            if header_str.endswith('%'):
                # Handle percentage values
                value = float(header_str.rstrip('%')) / 100
                return value, "percentage", header_str
            else:
                # Handle absolute USD values
                value = float(header_str)
                return value, "absolute_usd", header_str
        except (ValueError, TypeError):
            return None, None, header_str
    
    def _save_to_database(self, df: pd.DataFrame) -> None:
        """
        Save DataFrame to SQLite database.
        
        Args:
            df: DataFrame to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df.to_sql(self.table_name, conn, if_exists="replace", index=False)
            conn.close()
            logger.info(f"Successfully saved data to SQLite: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error saving to SQLite: {e}")
            raise
    
    def get_scenario_headers(self) -> List[str]:
        """
        Get list of unique scenario headers from the loaded data.
        
        Returns:
            List of scenario header strings
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"SELECT DISTINCT scenario_header FROM {self.table_name} ORDER BY scenario_header"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df['scenario_header'].dropna().tolist()
        except Exception as e:
            logger.error(f"Error getting scenario headers: {e}")
            return []
    
    def get_shock_types(self) -> List[str]:
        """
        Get list of unique shock types from the loaded data.
        
        Returns:
            List of shock type strings
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"SELECT DISTINCT shock_type FROM {self.table_name} ORDER BY shock_type"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df['shock_type'].dropna().tolist()
        except Exception as e:
            logger.error(f"Error getting shock types: {e}")
            return []
    
    def get_shock_values(self) -> List[float]:
        """
        Get list of unique shock values from the loaded data.
        
        Returns:
            List of shock values as floats, sorted numerically
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"SELECT DISTINCT shock_value FROM {self.table_name} ORDER BY shock_value"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df['shock_value'].dropna().tolist()
        except Exception as e:
            logger.error(f"Error getting shock values: {e}")
            return []
    
    def get_shock_values_by_type(self, shock_type: Optional[str] = None) -> List[float]:
        """
        Get list of unique shock values filtered by shock type.
        
        Args:
            shock_type: Shock type to filter by ('percentage' or 'absolute_usd'). 
                       If None, returns all shock values.
        
        Returns:
            List of shock values as floats, sorted numerically
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            if shock_type:
                query = f"SELECT DISTINCT shock_value FROM {self.table_name} WHERE shock_type = ? ORDER BY shock_value"
                df = pd.read_sql_query(query, conn, params=[shock_type])
            else:
                query = f"SELECT DISTINCT shock_value FROM {self.table_name} ORDER BY shock_value"
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            
            return df['shock_value'].dropna().tolist()
        except Exception as e:
            logger.error(f"Error getting shock values by type: {e}")
            return []
    
    def get_metric_names(self) -> List[str]:
        """
        Get list of available metric names from the loaded data.
        
        Returns:
            List of metric name strings
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            conn.close()
            
            # Filter out non-metric columns
            excluded_columns = {
                'scenario_header', 'uprice', 'point_header_original', 
                'shock_value', 'shock_type'
            }
            
            metric_columns = [
                col[1] for col in columns 
                if col[1] not in excluded_columns
            ]
            
            return sorted(metric_columns)
        except Exception as e:
            logger.error(f"Error getting metric names: {e}")
            return []
    
    def _quote_column_name(self, column_name: str) -> str:
        """
        Quote column names that contain spaces or special characters for SQL.
        
        Args:
            column_name: The column name to quote
            
        Returns:
            Quoted column name safe for SQL
        """
        # If column name contains spaces or special chars, quote it
        if ' ' in column_name or any(char in column_name for char in ['-', '+', '*', '/', '(', ')']):
            return f'"{column_name}"'
        return column_name

    def get_filtered_data(
        self, 
        scenario_headers: Optional[List[str]] = None,
        shock_types: Optional[List[str]] = None,
        shock_values: Optional[List[float]] = None,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get filtered data based on selection criteria.
        
        Args:
            scenario_headers: List of scenario headers to include
            shock_types: List of shock types to include
            shock_values: List of shock values to include
            metrics: List of metrics to include
            
        Returns:
            Filtered pandas DataFrame
        """
        if not self.is_data_loaded():
            return pd.DataFrame()
        
        try:
            # Build base query
            base_columns = ['scenario_header', 'uprice', 'point_header_original', 'shock_value', 'shock_type']
            
            if metrics:
                # Quote metric column names that may have spaces
                quoted_metrics = [self._quote_column_name(metric) for metric in metrics]
                columns = base_columns + quoted_metrics
            else:
                columns = ['*']
            
            columns_str = ', '.join(columns) if columns != ['*'] else '*'
            query = f"SELECT {columns_str} FROM {self.table_name}"
            
            # Build WHERE conditions
            conditions = []
            params = []
            
            if scenario_headers:
                placeholders = ','.join(['?' for _ in scenario_headers])
                conditions.append(f"scenario_header IN ({placeholders})")
                params.extend(scenario_headers)
            
            if shock_types:
                placeholders = ','.join(['?' for _ in shock_types])
                conditions.append(f"shock_type IN ({placeholders})")
                params.extend(shock_types)
            
            if shock_values:
                placeholders = ','.join(['?' for _ in shock_values])
                conditions.append(f"shock_value IN ({placeholders})")
                params.extend(shock_values)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY scenario_header, shock_value"
            
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting filtered data: {e}")
            return pd.DataFrame()
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the loaded data.
        
        Returns:
            Dictionary containing data summary information
        """
        if not self.is_data_loaded():
            return {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get basic counts
            count_query = f"SELECT COUNT(*) as total_rows FROM {self.table_name}"
            total_rows = pd.read_sql_query(count_query, conn).iloc[0]['total_rows']
            
            # Get unique counts
            scenario_count_query = f"SELECT COUNT(DISTINCT scenario_header) as count FROM {self.table_name}"
            scenario_count = pd.read_sql_query(scenario_count_query, conn).iloc[0]['count']
            
            shock_type_count_query = f"SELECT COUNT(DISTINCT shock_type) as count FROM {self.table_name}"
            shock_type_count = pd.read_sql_query(shock_type_count_query, conn).iloc[0]['count']
            
            conn.close()
            
            return {
                'total_rows': total_rows,
                'scenario_count': scenario_count,
                'shock_type_count': shock_type_count,
                'current_file': self._current_file.name if self._current_file else None,
                'metric_count': len(self.get_metric_names())
            }
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
    
    def load_pricing_monkey_data(self) -> bool:
        """
        Load Pricing Monkey data via browser automation and integrate with existing data.
        
        Returns:
            True if PM data was loaded successfully, False otherwise
        """
        try:
            logger.info("Starting Pricing Monkey data retrieval and processing")
            
            # Step 1: Retrieve PM data via browser automation
            pm_df = get_extended_pm_data()
            
            # Step 2: Validate retrieved data
            validation_errors = validate_pm_data(pm_df)
            if validation_errors:
                logger.error(f"PM data validation failed: {validation_errors}")
                return False
            
            # Step 3: Process PM data for separate table
            processed_pm_df = process_pm_for_separate_table(pm_df)
            if processed_pm_df.empty:
                logger.error("PM data processing resulted in empty DataFrame")
                return False
            
            # Debug logging: show first 5 rows of processed data
            logger.info(f"PM Data Processing Summary: {len(processed_pm_df)} rows, {len(processed_pm_df.columns)} columns")
            logger.info("First 5 rows of processed PM data:")
            print("\n" + "="*80)
            print("PROCESSED PM DATA (First 5 rows):")
            print("="*80)
            print(processed_pm_df.head().to_string())
            print("="*80 + "\n")
            
            # Step 4: Save to separate PM table
            self._save_pm_to_database(processed_pm_df)
            
            self._pm_data_loaded = True
            logger.info(f"Successfully loaded PM data: {len(processed_pm_df)} records")
            return True
            
        except PMRetrievalError as e:
            logger.error(f"PM data retrieval failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading PM data: {e}", exc_info=True)
            return False
    
    def _ensure_schema_compatibility(self) -> None:
        """
        Ensure database schema includes data_source column for dual-source support.
        
        Adds data_source column if missing and backfills existing Actant data.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if data_source column exists
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'data_source' not in columns:
                logger.info("Adding data_source column to support dual-source architecture")
                
                # Add the column
                cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN data_source TEXT")
                
                # Backfill existing data as Actant source
                cursor.execute(f"UPDATE {self.table_name} SET data_source = 'Actant' WHERE data_source IS NULL")
                
                conn.commit()
                logger.info("Schema migration completed successfully")
            
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Error during schema migration: {e}")
            raise

    def _save_pm_to_database(self, df: pd.DataFrame) -> None:
        """
        Save PM DataFrame to separate PM table in SQLite database.
        
        Args:
            df: PM DataFrame to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df.to_sql(self.pm_table_name, conn, if_exists="replace", index=False)
            conn.close()
            logger.info(f"Successfully saved PM data to SQLite table '{self.pm_table_name}': {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error saving PM data to SQLite: {e}")
            raise

    def _append_to_database(self, df: pd.DataFrame) -> None:
        """
        Append DataFrame to existing SQLite database.
        
        Args:
            df: DataFrame to append
        """
        try:
            # Ensure schema compatibility before appending
            self._ensure_schema_compatibility()
            
            conn = sqlite3.connect(self.db_path)
            df.to_sql(self.table_name, conn, if_exists="append", index=False)
            conn.close()
            logger.info(f"Successfully appended data to SQLite: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error appending to SQLite: {e}")
            raise
    
    def get_data_sources(self) -> List[str]:
        """
        Get list of available data sources in the loaded data.
        
        Returns:
            List of data source names
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            # Check if data_source column exists
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'data_source' in columns:
                query = f"SELECT DISTINCT data_source FROM {self.table_name} ORDER BY data_source"
                df = pd.read_sql_query(query, conn)
                conn.close()
                return df['data_source'].dropna().tolist()
            else:
                conn.close()
                # If no data_source column, assume all data is from Actant
                return ['Actant'] if self._data_loaded else []
                
        except Exception as e:
            logger.error(f"Error getting data sources: {e}")
            return []
    
    def is_data_loaded(self) -> bool:
        """
        Check if data has been successfully loaded.
        
        Returns:
            True if data is loaded and ready for queries, False otherwise
        """
        return self._data_loaded and Path(self.db_path).exists()
    
    def is_pm_data_loaded(self) -> bool:
        """
        Check if Pricing Monkey data has been loaded.
        
        Returns:
            True if PM data is loaded, False otherwise
        """
        return self._pm_data_loaded

    def categorize_metrics(self) -> Dict[str, List[str]]:
        """
        Categorize all available metrics into predefined categories.
        
        Returns:
            Dictionary mapping category names to lists of metric names
        """
        if not self.is_data_loaded():
            return {}
        
        all_metrics = self.get_metric_names()
        
        # Define metric categories with their patterns
        metric_categories = {
            "Delta": ["Delta", "ab_Delta", "bs_Delta", "pa_Delta", "sDelta", "sDeltaCorr", "sDeltaPath", "ab_sDeltaPath", "bs_sDeltaPath", "pa_sDeltaPath"],
            "Epsilon": ["Epsilon", "ab_Epsilon", "bs_Epsilon", "pa_Epsilon"],
            "Gamma": ["Gamma", "ab_Gamma", "bs_Gamma", "pa_Gamma", "sGamma", "sGammaCorr", "sGammaPath", "ab_sGammaPath", "bs_sGammaPath", "pa_sGammaPath"],
            "Theta": ["Theta", "ab_Theta", "bs_Theta", "pa_Theta"],
            "Vega": ["Vega", "ab_Vega", "bs_Vega", "pa_Vega", "WVega", "ab_WVega", "bs_WVega", "pa_WVega"],
            "Zeta": ["Zeta", "ab_Zeta", "bs_Zeta", "pa_Zeta"],
            "Vol": ["ATMVol", "Down1SDVol", "Down2SDVol", "DownHalfSDVol", "Up1SDVol", "Up2SDVol", "UpHalfSDVol"],
            "OEV": ["OEV", "ab_sOEV", "bs_sOEV", "pa_sOEV", "sOEV"],
            "Th PnL": ["Th PnL", "ab_Th PnL", "bs_Th PnL", "pa_Th PnL"],
            "Misc": []  # Will be populated with remaining metrics
        }
        
        # Create the categorized result
        categorized = {}
        used_metrics = set()
        
        # First pass: assign metrics to predefined categories
        for category, metric_patterns in metric_categories.items():
            if category == "Misc":
                continue
            
            category_metrics = []
            for metric in all_metrics:
                if metric in metric_patterns:
                    category_metrics.append(metric)
                    used_metrics.add(metric)
            
            if category_metrics:  # Only include categories with metrics
                categorized[category] = sorted(category_metrics)
        
        # Second pass: add remaining metrics to Misc
        misc_metrics = [m for m in all_metrics if m not in used_metrics]
        if misc_metrics:
            categorized["Misc"] = sorted(misc_metrics)
        
        return categorized

    def filter_metrics_by_prefix(self, metrics: List[str], prefix_filter: Optional[str] = None) -> List[str]:
        """
        Filter metrics by prefix pattern.
        
        Args:
            metrics: List of metric names to filter
            prefix_filter: Filter type ("ab", "bs", "pa", "base", or None for all)
            
        Returns:
            Filtered list of metric names
        """
        if not prefix_filter or prefix_filter == "all":
            return metrics
        
        if prefix_filter == "base":
            # Base metrics have no prefix (don't start with ab_, bs_, pa_, or s)
            return [m for m in metrics if not any(m.startswith(p) for p in ["ab_", "bs_", "pa_", "s"])]
        elif prefix_filter == "ab":
            return [m for m in metrics if m.startswith("ab_")]
        elif prefix_filter == "bs":
            return [m for m in metrics if m.startswith("bs_")]
        elif prefix_filter == "pa":
            return [m for m in metrics if m.startswith("pa_")]
        else:
            return metrics

    def get_shock_range_by_scenario(self, scenario_header: str, shock_type: Optional[str] = None) -> tuple[float, float]:
        """
        Get the min and max shock values for a specific scenario.
        
        Args:
            scenario_header: The scenario to get range for
            shock_type: Optional shock type filter
            
        Returns:
            Tuple of (min_shock, max_shock)
        """
        if not self.is_data_loaded():
            return (0.0, 0.0)
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            if shock_type:
                query = f"""
                    SELECT MIN(shock_value) as min_val, MAX(shock_value) as max_val 
                    FROM {self.table_name} 
                    WHERE scenario_header = ? AND shock_type = ?
                """
                df = pd.read_sql_query(query, conn, params=[scenario_header, shock_type])
            else:
                query = f"""
                    SELECT MIN(shock_value) as min_val, MAX(shock_value) as max_val 
                    FROM {self.table_name} 
                    WHERE scenario_header = ?
                """
                df = pd.read_sql_query(query, conn, params=[scenario_header])
            
            conn.close()
            
            if df.empty or df.iloc[0]['min_val'] is None:
                return (0.0, 0.0)
            
            return (float(df.iloc[0]['min_val']), float(df.iloc[0]['max_val']))
            
        except Exception as e:
            logger.error(f"Error getting shock range for scenario {scenario_header}: {e}")
            return (0.0, 0.0)

    def get_distinct_shock_values_by_scenario_and_type(self, scenario_header: str, shock_type: str) -> List[float]:
        """
        Get distinct shock values for a specific scenario and shock type.
        
        Args:
            scenario_header: The scenario to get shock values for
            shock_type: The shock type ('percentage' or 'absolute_usd')
            
        Returns:
            Sorted list of distinct shock values
        """
        if not self.is_data_loaded():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f"""
                SELECT DISTINCT shock_value 
                FROM {self.table_name} 
                WHERE scenario_header = ? AND shock_type = ?
                ORDER BY shock_value
            """
            df = pd.read_sql_query(query, conn, params=[scenario_header, shock_type])
            conn.close()
            
            if df.empty:
                return []
            
            return df['shock_value'].tolist()
            
        except Exception as e:
            logger.error(f"Error getting distinct shock values for scenario {scenario_header}, type {shock_type}: {e}")
            return []

    def get_filtered_data_with_range(
        self,
        scenario_headers: Optional[List[str]] = None,
        shock_types: Optional[List[str]] = None,
        shock_ranges: Optional[Dict[str, List[float]]] = None,  # scenario -> [min, max]
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get filtered data with shock range filtering per scenario.
        
        Args:
            scenario_headers: List of scenario headers to include
            shock_types: List of shock types to include
            shock_ranges: Dict mapping scenario names to [min, max] shock ranges
            metrics: List of metrics to include
            
        Returns:
            Filtered pandas DataFrame
        """
        if not self.is_data_loaded():
            return pd.DataFrame()
        
        try:
            # Build base query
            base_columns = ['scenario_header', 'uprice', 'point_header_original', 'shock_value', 'shock_type']
            
            if metrics:
                # Quote metric column names that may have spaces
                quoted_metrics = [self._quote_column_name(metric) for metric in metrics]
                columns = base_columns + quoted_metrics
            else:
                columns = ['*']
            
            columns_str = ', '.join(columns) if columns != ['*'] else '*'
            query = f"SELECT {columns_str} FROM {self.table_name}"
            
            # Build WHERE conditions
            conditions = []
            params = []
            
            if scenario_headers:
                placeholders = ','.join(['?' for _ in scenario_headers])
                conditions.append(f"scenario_header IN ({placeholders})")
                params.extend(scenario_headers)
            
            if shock_types:
                placeholders = ','.join(['?' for _ in shock_types])
                conditions.append(f"shock_type IN ({placeholders})")
                params.extend(shock_types)
            
            # Add shock range conditions per scenario
            if shock_ranges:
                range_conditions = []
                for scenario, shock_range in shock_ranges.items():
                    if len(shock_range) == 2:
                        range_conditions.append(
                            f"(scenario_header = ? AND shock_value BETWEEN ? AND ?)"
                        )
                        params.extend([scenario, shock_range[0], shock_range[1]])
                
                if range_conditions:
                    conditions.append(f"({' OR '.join(range_conditions)})")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY scenario_header, shock_value"
            
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting filtered data with range: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Test the data service
    logging.basicConfig(level=logging.INFO)
    
    service = ActantDataService()
    
    # Test with existing JSON file
    json_file = Path("GE_XCME.ZN_20250521_102611.json")
    if json_file.exists():
        print("Testing ActantDataService")
        print("=" * 30)
        
        # Load data
        success = service.load_data_from_json(json_file)
        print(f"Data loaded: {success}")
        
        if success:
            # Test queries
            scenarios = service.get_scenario_headers()
            print(f"Scenarios: {scenarios[:3]}...")  # Show first 3
            
            shock_types = service.get_shock_types()
            print(f"Shock types: {shock_types}")
            
            shock_values = service.get_shock_values()
            print(f"Shock values: {shock_values}")
            
            metrics = service.get_metric_names()
            print(f"Metrics: {metrics[:5]}...")  # Show first 5
            
            summary = service.get_data_summary()
            print(f"Summary: {summary}")
    else:
        print(f"Test file {json_file} not found") 