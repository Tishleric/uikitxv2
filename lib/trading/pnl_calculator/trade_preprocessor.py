"""
Trade Preprocessor for P&L Calculator

Processes raw trade ledger files by:
- Translating Actant symbols to Bloomberg format
- Detecting SOD positions (midnight trades)
- Detecting option expiries (zero price)
- Converting Buy/Sell to signed quantities
- Adding validation status and metadata
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import pytz
import json
import os

from lib.trading.symbol_translator import SymbolTranslator

# Set up module logger
logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    # Fallback if monitoring is not available
    def monitor():
        def decorator(func):
            return func
        return decorator


class TradePreprocessor:
    """Preprocesses trade ledger files for P&L calculation."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the preprocessor.
        
        Args:
            output_dir: Directory for processed files (default: data/output/trade_ledger_processed)
        """
        self.symbol_translator = SymbolTranslator()
        self.chicago_tz = pytz.timezone('America/Chicago')
        
        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("data/output/trade_ledger_processed")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # File to track processing state
        self.state_file = self.output_dir / ".processing_state.json"
        self.processing_state = self._load_processing_state()
        
    def _load_processing_state(self) -> Dict[str, Any]:
        """Load processing state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading processing state: {e}")
        return {}
    
    def _save_processing_state(self):
        """Save processing state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.processing_state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processing state: {e}")
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file needs processing based on size/modification time."""
        stat = file_path.stat()
        file_key = file_path.name
        
        # Get stored state
        stored_state = self.processing_state.get(file_key, {})
        stored_size = stored_state.get('size', -1)
        stored_mtime = stored_state.get('mtime', -1)
        
        # Check if file has changed
        current_size = stat.st_size
        current_mtime = stat.st_mtime
        
        return current_size != stored_size or current_mtime != stored_mtime
    
    def _update_processing_state(self, file_path: Path):
        """Update processing state for a file."""
        stat = file_path.stat()
        file_key = file_path.name
        
        self.processing_state[file_key] = {
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'processed_at': datetime.now().isoformat()
        }
        self._save_processing_state()
    
    @monitor()
    def process_trade_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Process a single trade file.
        
        Args:
            file_path: Path to the trade CSV file
            
        Returns:
            DataFrame of processed trades or None if processing fails
        """
        input_path = Path(file_path)
        
        # Check if file needs processing
        if not self._should_process_file(input_path):
            logger.info(f"File {input_path.name} has not changed, skipping")
            return None
        
        logger.info(f"Processing trade file: {input_path.name}")
        
        try:
            # Read the CSV file
            trades_df = pd.read_csv(input_path)
            
            # Validate required columns
            required_columns = ['tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price']
            missing_columns = set(required_columns) - set(trades_df.columns)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Add processing columns
            trades_df['bloomberg_symbol'] = None
            trades_df['signed_quantity'] = 0.0
            trades_df['validation_status'] = 'OK'
            trades_df['is_sod'] = False
            trades_df['is_expiry'] = False
            trades_df['processing_timestamp'] = datetime.now().isoformat()
            
            # Process each trade
            for idx, row in trades_df.iterrows():
                # 1. Symbol Translation
                actant_symbol = row['instrumentName']
                bloomberg_symbol = self.symbol_translator.translate(actant_symbol)
                
                if bloomberg_symbol:
                    trades_df.at[idx, 'bloomberg_symbol'] = bloomberg_symbol
                else:
                    trades_df.at[idx, 'validation_status'] = 'SYMBOL_ERROR'
                    trades_df.at[idx, 'signed_quantity'] = 0.0
                    continue
                
                # 2. Convert Buy/Sell to signed quantity
                quantity = float(row['quantity'])
                if row['buySell'] == 'S':
                    quantity = -quantity
                elif row['buySell'] != 'B':
                    trades_df.at[idx, 'validation_status'] = 'INVALID_BUYSELL'
                    quantity = 0.0
                trades_df.at[idx, 'signed_quantity'] = quantity
                
                # 3. Parse timestamp (already in Chicago time)
                timestamp_str = str(row['marketTradeTime']).split('.')[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    # Add Chicago timezone info
                    timestamp = self.chicago_tz.localize(timestamp)
                    trades_df.at[idx, 'chicago_time'] = timestamp.isoformat()
                    
                    # 4. SOD detection: trades at midnight Chicago time
                    if timestamp.hour == 0 and timestamp.minute == 0:
                        trades_df.at[idx, 'is_sod'] = True
                        trades_df.at[idx, 'validation_status'] = 'SOD'
                    
                except ValueError as e:
                    logger.error(f"Error parsing timestamp for trade {row['tradeId']}: {e}")
                    trades_df.at[idx, 'validation_status'] = 'TIMESTAMP_ERROR'
                
                # 5. Expiry detection: zero price trades
                if float(row['price']) == 0.0:
                    trades_df.at[idx, 'is_expiry'] = True
                    # Only override status if not already an error
                    if trades_df.at[idx, 'validation_status'] == 'OK':
                        trades_df.at[idx, 'validation_status'] = 'EXPIRY'
            
            # Save processed file
            output_path = self._get_output_path(input_path)
            self._save_processed_file(trades_df, output_path)
            
            # Update processing state
            self._update_processing_state(input_path)
            
            # Log summary
            logger.info(f"Processed {len(trades_df)} trades:")
            logger.info(f"  - Symbol translation success: {(trades_df['bloomberg_symbol'].notna()).sum()}")
            logger.info(f"  - SOD positions: {trades_df['is_sod'].sum()}")
            logger.info(f"  - Expiries: {trades_df['is_expiry'].sum()}")
            logger.info(f"  - Errors: {(trades_df['validation_status'] != 'OK').sum() - trades_df['is_sod'].sum() - trades_df['is_expiry'].sum()}")
            
            return trades_df
            
        except Exception as e:
            logger.error(f"Error processing trade file {input_path}: {e}")
            return None
    
    def _get_output_path(self, input_path: Path) -> Path:
        """Generate output path for processed file.
        
        Preserves the original filename to maintain the trade day.
        """
        # Keep the same filename but add _processed suffix
        base_name = input_path.stem
        output_name = f"{base_name}_processed.csv"
        return self.output_dir / output_name
    
    def _save_processed_file(self, df: pd.DataFrame, output_path: Path):
        """Save processed trades to CSV."""
        try:
            df.to_csv(output_path, index=False)
            logger.info(f"Saved processed trades to {output_path}")
        except Exception as e:
            logger.error(f"Error saving processed file: {e}")
            raise
    
    def process_all_files(self, input_dir: str):
        """Process all trade files in a directory.
        
        Args:
            input_dir: Directory containing trade CSV files
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_dir}")
            return
        
        # Find all CSV files matching trade pattern
        csv_files = list(input_path.glob("trades_*.csv"))
        
        if not csv_files:
            logger.warning(f"No trade files found in {input_dir}")
            return
        
        logger.info(f"Found {len(csv_files)} trade files to process")
        
        for file_path in sorted(csv_files):
            self.process_trade_file(str(file_path)) 