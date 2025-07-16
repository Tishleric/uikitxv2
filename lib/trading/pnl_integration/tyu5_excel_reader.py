"""TYU5 Excel Reader for P&L Dashboard Integration

This module provides functionality to read and parse TYU5 Excel output files
for display in the P&L tracking dashboard.
"""

import pandas as pd
import os
from glob import glob
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class TYU5ExcelReader:
    """Reader for TYU5 Excel output files."""
    
    def __init__(self, output_dir: str = "data/output/pnl"):
        """Initialize the reader with output directory.
        
        Args:
            output_dir: Directory containing TYU5 Excel files
        """
        self.output_dir = Path(output_dir)
        self.latest_file = None
        self.data = {}
        
    def get_latest_file(self) -> Optional[str]:
        """Find the latest TYU5 Excel file in the output directory.
        
        Returns:
            Path to the latest file or None if no files found
        """
        pattern = str(self.output_dir / "tyu5_pnl_all_*.xlsx")
        files = glob(pattern)
        
        if not files:
            logger.warning(f"No TYU5 files found in {self.output_dir}")
            return None
            
        # Get the most recent file by creation time
        latest = max(files, key=os.path.getctime)
        self.latest_file = latest
        logger.info(f"Found latest TYU5 file: {latest}")
        return latest
        
    def read_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """Read all sheets from the latest TYU5 Excel file.
        
        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        # Always get the latest file to pick up new Excel files
        file_path = self.get_latest_file()
        
        if not file_path:
            logger.error("No TYU5 file available to read")
            return {}
            
        try:
            # Read all sheets
            xl_file = pd.ExcelFile(file_path)
            self.data = {}
            
            for sheet_name in xl_file.sheet_names:
                logger.info(f"Reading sheet: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                self.data[sheet_name] = df
                
            logger.info(f"Successfully read {len(self.data)} sheets from {file_path}")
            return self.data
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return {}
            
    def get_summary_data(self) -> Dict[str, float]:
        """Extract summary statistics from the Summary sheet.
        
        Returns:
            Dictionary of summary metrics
        """
        if 'Summary' not in self.data:
            # Try to read if not already loaded
            self.read_all_sheets()
            
        if 'Summary' not in self.data:
            logger.warning("No Summary sheet available")
            return {
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'realized_pnl': 0.0,
                'unrealized_pnl': 0.0,
                'active_positions': 0,
                'total_trades': 0
            }
            
        summary_df = self.data['Summary']
        summary_dict = {}
        
        # Parse the summary sheet (format: Metric | Value | Details)
        for _, row in summary_df.iterrows():
            metric = row.get('Metric', '').strip().lower().replace(' ', '_')
            value = row.get('Value', 0.0)
            
            if metric:
                summary_dict[metric] = float(value) if pd.notnull(value) else 0.0
                
        return summary_dict
        
    def get_sheet_data(self, sheet_name: str) -> pd.DataFrame:
        """Get data for a specific sheet.
        
        Args:
            sheet_name: Name of the sheet to retrieve
            
        Returns:
            DataFrame for the requested sheet or empty DataFrame
        """
        if sheet_name not in self.data:
            # Try to read if not already loaded
            self.read_all_sheets()
            
        return self.data.get(sheet_name, pd.DataFrame())
        
    def get_file_timestamp(self) -> str:
        """Get the timestamp from the latest file name.
        
        Returns:
            Timestamp string or 'N/A'
        """
        # Ensure we have the latest file
        latest_file = self.get_latest_file()
        if not latest_file:
            return 'N/A'
            
        # Extract timestamp from filename (tyu5_pnl_all_YYYYMMDD_HHMMSS.xlsx)
        filename = os.path.basename(latest_file)
        parts = filename.replace('.xlsx', '').split('_')
        
        if len(parts) >= 5:
            date_str = parts[3]  # YYYYMMDD
            time_str = parts[4]  # HHMMSS
            
            # Format as readable timestamp
            try:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                hour = time_str[:2]
                minute = time_str[2:4]
                second = time_str[4:6]
                
                return f"{year}-{month}-{day} {hour}:{minute}:{second}"
            except:
                return filename
                
        return filename 