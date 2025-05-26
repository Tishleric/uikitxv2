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
        self._data_loaded = False
        self._current_file = None
        
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
    
    def get_filtered_data(
        self, 
        scenario_headers: Optional[List[str]] = None,
        shock_types: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get filtered data based on selection criteria.
        
        Args:
            scenario_headers: List of scenario headers to include
            shock_types: List of shock types to include
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
                columns = base_columns + metrics
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
    
    def is_data_loaded(self) -> bool:
        """
        Check if data has been successfully loaded.
        
        Returns:
            True if data is loaded and ready for queries, False otherwise
        """
        return self._data_loaded and Path(self.db_path).exists()


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
            
            metrics = service.get_metric_names()
            print(f"Metrics: {metrics[:5]}...")  # Show first 5
            
            summary = service.get_data_summary()
            print(f"Summary: {summary}")
    else:
        print(f"Test file {json_file} not found") 