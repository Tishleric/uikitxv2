#!/usr/bin/env python3
"""
Process Actant JSON output into a flattened DataFrame, CSV, and SQLite database.

This script reads an Actant JSON file (typically named like 'GE_XCME.ZN_20250521_102611.json'),
parses the data, converts it to a pandas DataFrame, and saves it as both:
- A CSV file with the same base name plus "_processed.csv"
- A table in an SQLite database file named "actant_eod_data.db"

The script handles both percentage shocks (e.g., "-30%") and absolute price shocks (e.g., "-2"),
and converts string values to appropriate numeric types when possible.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd

# Configuration constants
OUTPUT_CSV_FILENAME_TEMPLATE = "{}_processed.csv"
OUTPUT_DB_FILENAME = "actant_eod_data.db"
DB_TABLE_NAME = "scenario_metrics"


def try_convert_to_float(value_str: str) -> float:
    """
    Attempt to convert a string value to float, handling "na" values.
    
    Args:
        value_str: String representation of a number or "na" from JSON
        
    Returns:
        Converted float value or np.nan for "na" or conversion errors
    """
    if isinstance(value_str, (int, float)):
        return float(value_str)
    
    if value_str.lower() == "na":
        return np.nan
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{value_str}' to float, using NaN.")
        return np.nan


def parse_point_header(header_str: str) -> Tuple[Optional[float], Optional[str], str]:
    """
    Parse a point header string into a numeric value and type.
    
    Args:
        header_str: The header string (e.g., "-30%", "-2", "0.25")
        
    Returns:
        Tuple of (shock_value, shock_type, original_header_str)
        - shock_value: Parsed numeric value (e.g., -0.30, -2.0)
        - shock_type: "percentage" or "absolute_usd"
        - original_header_str: The original input string
    """
    if not header_str:
        return None, None, header_str
    
    try:
        if header_str.endswith('%'):
            # Handle percentage values (e.g., "-30%")
            value = float(header_str.rstrip('%')) / 100
            return value, "percentage", header_str
        else:
            # Handle absolute USD values (e.g., "-2")
            value = float(header_str)
            return value, "absolute_usd", header_str
    except (ValueError, TypeError):
        print(f"Warning: Could not parse header '{header_str}', returning None.")
        return None, None, header_str


def flatten_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten the nested JSON structure into a list of records for DataFrame conversion.
    
    Args:
        raw_data: The parsed JSON data from the file
        
    Returns:
        List of flat dictionaries, each representing a row in the resulting DataFrame
    """
    flattened_records = []
    totals_list = raw_data.get("totals", [])
    
    for scenario in totals_list:
        scenario_header = scenario.get("header")
        scenario_uprice = try_convert_to_float(str(scenario.get("uprice", 0)))
        
        for point in scenario.get("points", []):
            original_point_header = point.get("header")
            shock_value, shock_type, _ = parse_point_header(original_point_header)
            
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
                record[metric_name] = try_convert_to_float(metric_value_str)
            
            flattened_records.append(record)
    
    return flattened_records


def main():
    """Main function to execute the script's workflow."""
    # Import file manager for dynamic JSON selection
    from file_manager import get_most_recent_json_file
    
    # Ensure paths are absolute and reliable
    script_dir = Path(__file__).resolve().parent
    
    # Get the most recent JSON file dynamically
    input_json_path = get_most_recent_json_file()
    if input_json_path is None:
        print("Error: No valid JSON files found.")
        return
    
    output_csv_path = script_dir / OUTPUT_CSV_FILENAME_TEMPLATE.format(input_json_path.stem)
    output_db_path = script_dir / OUTPUT_DB_FILENAME
    
    # Load and parse JSON
    try:
        with open(input_json_path, 'r') as f:
            raw_data = json.load(f)
        print(f"Successfully loaded {input_json_path}")
    except FileNotFoundError:
        print(f"Error: File {input_json_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: File {input_json_path} contains invalid JSON.")
        return
    
    # Process data
    flattened_records = flatten_data(raw_data)
    if not flattened_records:
        print("Warning: No data records extracted from the JSON.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(flattened_records)
    print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns.")
    
    # Save to CSV
    try:
        df.to_csv(output_csv_path, index=False)
        print(f"Successfully saved data to CSV: {output_csv_path}")
    except IOError as e:
        print(f"Error saving CSV: {e}")
    
    # Save to SQLite
    try:
        conn = sqlite3.connect(output_db_path)
        df.to_sql(DB_TABLE_NAME, conn, if_exists="replace", index=False)
        conn.close()
        print(f"Successfully saved data to SQLite database: {output_db_path}, table: {DB_TABLE_NAME}")
    except sqlite3.Error as e:
        print(f"Error saving to SQLite: {e}")
    
    # Summary
    print("\nProcessing complete!")
    print(f"Output files created:")
    print(f"1. CSV:    {output_csv_path}")
    print(f"2. SQLite: {output_db_path} (table: {DB_TABLE_NAME})")
    
    # Display dataframe shape and sample
    print(f"\nDataFrame shape: {df.shape}")
    print("\nSample of processed data (first 3 rows):")
    print(df.head(3))


if __name__ == "__main__":
    main() 