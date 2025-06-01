#!/usr/bin/env python3
"""
Pricing Monkey data processor for ActantEOD.

This module processes Pricing Monkey data into a separate table structure
preserving original column names for clear comparison with Actant data.
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# PM column name standardization (spaces to underscores for SQL compatibility)
PM_COLUMN_MAPPING = {
    "Trade Amount": "Trade_Amount",
    "Trade Description": "Trade_Description", 
    "Strike": "Strike",
    "Expiry Date": "Expiry_Date",
    "Price": "Price",
    "DV01 Gamma": "DV01_Gamma",
    "Vega": "Vega",
    "%Delta": "Delta_Percent",
    "Theta": "Theta"
}


def process_pm_for_separate_table(pm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process Pricing Monkey DataFrame for separate PM table with preserved column structure.
    
    Args:
        pm_df (pd.DataFrame): Raw PM data with columns:
                             Trade Amount, Trade Description, Strike, Expiry Date, Price,
                             DV01 Gamma, Vega, %Delta, Theta
    
    Returns:
        pd.DataFrame: Processed PM data with scenario_header and standardized column names:
                     scenario_header, Trade_Amount, Trade_Description, Strike, Expiry_Date, 
                     Price, DV01_Gamma, Vega, Delta_Percent, Theta
    """
    if pm_df.empty:
        logger.warning("Empty PM DataFrame provided for processing")
        return pd.DataFrame()
    
    try:
        logger.info(f"Processing PM data for separate table: {len(pm_df)} rows")
        
        # Create a copy for processing
        processed_df = pm_df.copy()
        
        # Add scenario headers based on Trade Description
        processed_df['scenario_header'] = processed_df['Trade Description'].apply(_parse_scenario_header)
        
        # Rename columns to SQL-friendly names (spaces to underscores)
        processed_df = processed_df.rename(columns=PM_COLUMN_MAPPING)
        
        # Ensure numeric columns are properly typed
        numeric_columns = ['Trade_Amount', 'Strike', 'Price', 'DV01_Gamma', 'Vega', 'Theta']
        for col in numeric_columns:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
        
        # Handle Delta_Percent - convert from percentage string to decimal
        if 'Delta_Percent' in processed_df.columns:
            processed_df['Delta_Percent'] = processed_df['Delta_Percent'].apply(_convert_percentage)
        
        # Reorder columns with scenario_header first
        column_order = ['scenario_header'] + [col for col in processed_df.columns if col != 'scenario_header']
        processed_df = processed_df[column_order]
        
        logger.info(f"PM processing complete: {len(processed_df)} records with {len(processed_df.columns)} columns")
        return processed_df
        
    except Exception as e:
        logger.error(f"Error processing PM data: {e}", exc_info=True)
        return pd.DataFrame()


def _parse_scenario_header(trade_description: str) -> str:
    """
    Parse Trade Description to create scenario header similar to Actant format.
    
    Args:
        trade_description: PM Trade Description string
        
    Returns:
        str: Scenario header (keeping original description for now)
    """
    if pd.isna(trade_description) or not trade_description:
        return "Unknown"
    
    # For now, keep original trade description as requested
    return str(trade_description).strip()


def _convert_percentage(value) -> float:
    """
    Convert percentage value to decimal format.
    
    Args:
        value: Percentage value (string or numeric)
        
    Returns:
        float: Decimal representation or np.nan if conversion fails
    """
    if pd.isna(value):
        return np.nan
    
    try:
        if isinstance(value, str):
            # Remove % symbol and convert
            clean_value = value.replace('%', '').strip()
            if clean_value == '' or clean_value.lower() == 'na':
                return np.nan
            return float(clean_value) / 100.0
        
        # Assume numeric value is already in correct format
        return float(value)
        
    except (ValueError, TypeError):
        logger.debug(f"Could not convert percentage value: {value}")
        return np.nan


def validate_pm_data(pm_df: pd.DataFrame) -> List[str]:
    """
    Validate PM data structure and content.
    
    Args:
        pm_df (pd.DataFrame): PM data to validate
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    
    if pm_df.empty:
        errors.append("PM DataFrame is empty")
        return errors
    
    # Check for required columns
    required_columns = ['Trade Amount', 'Trade Description', 'Strike', 'Price']
    missing_columns = [col for col in required_columns if col not in pm_df.columns]
    if missing_columns:
        errors.append(f"Missing required PM columns: {missing_columns}")
    
    # Check for risk metric columns (original PM column names)
    risk_columns = ["DV01 Gamma", "Vega", "%Delta", "Theta"]
    missing_risk_columns = [col for col in risk_columns if col not in pm_df.columns]
    if missing_risk_columns:
        errors.append(f"Missing risk metric columns: {missing_risk_columns}")
    
    # Check data quality
    if len(pm_df) == 0:
        errors.append("No data rows found")
    
    return errors


if __name__ == "__main__":
    # Test the processor with mock data
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    # Create mock PM data for testing
    mock_pm_data = pd.DataFrame({
        'Trade Amount': [100, -50, 75],
        'Trade Description': ['1st 10y note 25 out put', '1st 10y note 50 out put', '2nd 10y note 25 out put'],
        'Strike': [109.75, 110.0, 109.75],
        'Expiry Date': ['27-May-2025', '27-May-2025', '28-May-2025'],
        'Price': [0.0125, 0.025, 0.0156],
        'DV01 Gamma': [25, 45, 30],
        'Vega': [15, 20, 18],
        '%Delta': [-14.7, -25.3, -16.2],
        'Theta': [2.5, 3.1, 2.8]
    })
    
    logger.info("Testing PM processor with mock data")
    
    # Validate data
    errors = validate_pm_data(mock_pm_data)
    if errors:
        logger.error(f"Validation errors: {errors}")
    else:
        logger.info("Mock data validation passed")
    
    # Transform data
    transformed = process_pm_for_separate_table(mock_pm_data)
    if not transformed.empty:
        logger.info(f"Transformation successful: {len(transformed)} rows")
        logger.info("\nTransformed data preview:")
        print(transformed.head().to_string())
    else:
        logger.error("Transformation failed") 