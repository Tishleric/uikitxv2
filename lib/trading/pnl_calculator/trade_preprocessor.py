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

# Import position manager
from lib.trading.pnl_calculator.position_manager import PositionManager
from lib.trading.pnl_calculator.storage import PnLStorage

# Import TYU5 service for automatic P&L calculation
from lib.trading.pnl_integration.tyu5_service import TYU5Service

# Set up module logger
logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    # Fallback if monitoring is not available
    def monitor(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class TradePreprocessor:
    """Preprocesses trade ledger files for P&L calculation."""
    
    def __init__(self, output_dir: Optional[str] = None, enable_position_tracking: bool = False,
                 storage: Optional[PnLStorage] = None):
        """Initialize the preprocessor.
        
        Args:
            output_dir: Directory for processed files (default: data/output/trade_ledger_processed)
            enable_position_tracking: Whether to update positions as trades are processed
            storage: PnLStorage instance for position tracking (creates default if enabled and not provided)
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
        
        # CTO_INTEGRATION: Always initialize storage for row-level tracking
        if storage is None:
            storage = PnLStorage()
        self.storage = storage
        
        # Position tracking
        self.enable_position_tracking = enable_position_tracking
        self.position_manager = None
        
        if enable_position_tracking:
            self.position_manager = PositionManager(storage)
            logger.info("Position tracking enabled")
    
    def _load_processing_state(self) -> Dict[str, Any]:
        """Load processing state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading processing state: {e}")
        return {}
    
    def _save_processing_state(self) -> None:
        """Save processing state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.processing_state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processing state: {e}")
    
    def _read_trade_csv(self, file_path: str) -> pd.DataFrame:
        """Read and validate trade CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame with trade data
        """
        try:
            trades_df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price']
            missing_columns = set(required_columns) - set(trades_df.columns)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            return trades_df
            
        except Exception as e:
            logger.error(f"Error reading trade CSV {file_path}: {e}")
            raise
    
    def _preprocess_trade(self, row: pd.Series) -> Dict[str, Any]:
        """Preprocess a single trade row.
        
        Args:
            row: Pandas Series with trade data
            
        Returns:
            Dictionary with preprocessed trade data
        """
        # Initialize result
        result = row.to_dict()
        
        # 1. Symbol Translation
        actant_symbol = str(row['instrumentName'])
        bloomberg_symbol = self.symbol_translator.translate(actant_symbol)
        
        result['bloomberg_symbol'] = bloomberg_symbol
        result['validation_status'] = 'OK' if bloomberg_symbol else 'SYMBOL_ERROR'
        
        # 2. Convert Buy/Sell to signed quantity
        quantity = float(row['quantity'])
        if row['buySell'] == 'S':
            quantity = -quantity
        elif row['buySell'] != 'B':
            result['validation_status'] = 'INVALID_BUYSELL'
            quantity = 0.0
        result['signed_quantity'] = quantity
        
        # Convert price to float
        result['price'] = float(row['price'])
        
        # 3. Parse timestamp
        timestamp_str = str(row['marketTradeTime']).split('.')[0]
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            timestamp = self.chicago_tz.localize(timestamp)
            result['chicago_time'] = timestamp.isoformat()
            
            # CTO_INTEGRATION: Enhanced logging for edge case detection
            # Detect start-of-day trades
            if timestamp.hour == 0 and timestamp.minute == 0 and timestamp.second == 0:
                result['is_sod'] = True
                logger.warning(f"SOD TRADE DETECTED: Trade {result['tradeId']} at midnight - WILL BE EXCLUDED FROM P&L")
            else:
                result['is_sod'] = False
            
            # Detect exercises/assignments (price = 0)
            if float(result['price']) == 0.0:
                result['is_expiry'] = True
                logger.warning(f"EXERCISE/ASSIGNMENT DETECTED: Trade {result['tradeId']} with price=0 - WILL BE EXCLUDED FROM P&L")
            else:
                result['is_expiry'] = False
            
            # Log trade summary
            action = 'BUY' if result['buySell'] == 'B' else 'SELL'
            logger.debug(f"Processed trade {result['tradeId']}: {action} {abs(result['signed_quantity'])} "
                        f"{result['instrumentName']} @ {result['price']}")
                
        except ValueError as e:
            logger.error(f"Error parsing timestamp for trade {row['tradeId']}: {e}")
            result['validation_status'] = 'TIMESTAMP_ERROR'
            result['is_sod'] = False
        
        # Add processing metadata
        result['processing_timestamp'] = datetime.now().isoformat()
        
        # CTO_INTEGRATION: Add mock position tracking columns
        result['position_action'] = 'PENDING'
        result['position_after'] = 0
        result['realized_pnl'] = 0.0
        
        return result
    
    def _transform_to_cto_format(self, trade_data: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Transform preprocessed trade data to CTO format.
        
        Args:
            trade_data: Preprocessed trade data from _preprocess_trade
            source_file: Name of the source CSV file
            
        Returns:
            Dictionary with CTO format fields
        """
        # Parse timestamp to extract date and time
        timestamp_str = str(trade_data['marketTradeTime']).split('.')[0]
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            timestamp = self.chicago_tz.localize(timestamp)
            
            # Extract date and time components
            trade_date = timestamp.date()
            trade_time = timestamp.time()
        except ValueError:
            # Fallback to current date/time if parsing fails
            logger.error(f"Failed to parse timestamp for trade {trade_data['tradeId']}")
            trade_date = datetime.now().date()
            trade_time = datetime.now().time()
        
        # Determine instrument type (FUT or OPT)
        instrument_name = str(trade_data.get('instrumentName', ''))
        bloomberg_symbol = trade_data.get('bloomberg_symbol', '')
        
        # Determine instrument type based on symbol pattern
        # Options have 'C' or 'P' in their symbols (e.g., VBYN25C2, TYWN25P3)
        # This can be refined based on actual symbol patterns
        if bloomberg_symbol:
            # Check if symbol contains C or P followed by a number (option pattern)
            if 'C' in bloomberg_symbol or 'P' in bloomberg_symbol:
                # Additional check: ensure it's followed by a number
                for i, char in enumerate(bloomberg_symbol):
                    if char in ['C', 'P'] and i < len(bloomberg_symbol) - 1:
                        if bloomberg_symbol[i+1].isdigit():
                            instrument_type = 'CALL' if char == 'C' else 'PUT'
                            break
                else:
                    instrument_type = 'FUT'
            else:
                instrument_type = 'FUT'
        else:
            instrument_type = 'FUT'
        
        # Transform to CTO format
        cto_trade = {
            'Date': trade_date.isoformat(),
            'Time': trade_time.isoformat(),
            'Symbol': bloomberg_symbol if bloomberg_symbol else instrument_name,
            'Action': 'BUY' if trade_data.get('buySell') == 'B' else 'SELL',
            'Quantity': int(abs(trade_data.get('signed_quantity', 0))),  # Always positive, Action determines direction
            'Price': float(trade_data.get('price', 0.0)),
            'Fees': 0.0,  # No fee data in source
            'Counterparty': 'FRGM',  # Always FRGM as specified
            'tradeID': str(trade_data.get('tradeId', '')),
            'Type': instrument_type,
            'source_file': source_file,
            'is_sod': bool(trade_data.get('is_sod', False)),
            'is_exercise': bool(trade_data.get('is_expiry', False))
        }
        
        # For CTO format, quantity should be negative for sells
        if cto_trade['Action'] == 'SELL':
            cto_trade['Quantity'] = -abs(cto_trade['Quantity'])
        
        return cto_trade
    
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
    
    def _update_processing_state(self, file_path: Path, processed_count: int, mtime: str):
        """Update processing state for a file."""
        stat = file_path.stat()
        file_key = file_path.name
        
        self.processing_state[file_key] = {
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'processed_at': datetime.now().isoformat(),
            'processed_count': processed_count,
            'last_processed_mtime': mtime
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
            # CTO_INTEGRATION: Enhanced logging - file processing start
            logger.info(f"{'='*60}")
            logger.info(f"TRADE FILE PROCESSING: {input_path.name}")
            logger.info(f"{'='*60}")
            logger.info(f"File size: {os.path.getsize(str(input_path)) / 1024:.2f} KB")
            logger.info(f"Processing mode: {'Position tracking ENABLED' if self.enable_position_tracking else 'Position tracking DISABLED'}")
            
            # Check if we've processed this file before
            processed_trades_count = self.storage.get_processed_trades_for_file(input_path.name)
            last_processed_row = self.storage.get_last_processed_row_for_file(input_path.name)
            
            logger.info(f"File {input_path.name}: {processed_trades_count} trades already processed, last processed row: {last_processed_row}")
            
            # CTO_INTEGRATION: Log processing status
            if last_processed_row > 0:
                logger.info(f"Resuming processing from row {last_processed_row + 1}")
            else:
                logger.info("Starting fresh processing (no previous state)")
            
            # Read the CSV file
            df = pd.read_csv(str(input_path), dtype=str)
            total_rows = len(df)
            logger.info(f"Total rows in file: {total_rows}")
            
            # Add row numbers for tracking
            df['_row_number'] = range(1, len(df) + 1)
            
            # Skip already processed rows
            df_to_process = df[df['_row_number'] > last_processed_row]
            new_rows_count = len(df_to_process)
            
            logger.info(f"Processing {new_rows_count} new trades from {input_path.name}")
            
            if new_rows_count == 0:
                logger.info("No new trades to process")
                return None
            
            # Process each new trade
            processed_trades = []
            for idx, row in df_to_process.iterrows():
                try:
                    # Preprocess the trade
                    processed_trade = self._preprocess_trade(row)
                    
                    # Transform to CTO format
                    cto_trade = self._transform_to_cto_format(processed_trade, input_path.name)
                    
                    # Record that we've processed this trade
                    if self.storage.record_processed_trade(
                        input_path.name, 
                        int(row['_row_number']),
                        row.to_dict()  # Use original row data for tracking
                    ):
                        # Insert into CTO trades table
                        if self.storage.insert_cto_trade(cto_trade):
                            logger.debug(f"Inserted trade {cto_trade['tradeID']} into CTO table")
                        processed_trades.append(cto_trade)
                    else:
                        logger.debug(f"Trade {row['tradeId']} already in tracker, skipping")
                        
                except Exception as e:
                    logger.error(f"Error processing trade {row.get('tradeId', 'UNKNOWN')}: {e}")
                    continue
            
            if not processed_trades:
                logger.warning(f"No trades successfully processed from {input_path.name}")
                return None
            
            # Convert to DataFrame
            result_df = pd.DataFrame(processed_trades)
            
            # Update file processing state
            self._update_processing_state(
                input_path, 
                len(processed_trades),
                str(input_path.stat().st_mtime)
            )
            
            logger.info(f"Successfully processed {len(processed_trades)} trades from {input_path.name}")
            
            # Log processing stats
            stats = self.storage.get_processing_stats_for_file(input_path.name)
            logger.info(f"File {input_path.name} total stats: {stats['total_processed']} trades processed")
            
            # CTO_INTEGRATION: Enhanced summary logging
            cto_summary = self.storage.get_cto_trades_summary()
            logger.info(f"{'='*60}")
            logger.info("PROCESSING COMPLETE - CTO TABLE SUMMARY:")
            logger.info(f"  Total trades in database: {cto_summary['total_trades']}")
            logger.info(f"  Trading days covered: {cto_summary['trading_days']}")
            logger.info(f"  Unique symbols: {cto_summary['unique_symbols']}")
            logger.info(f"  SOD trades (excluded): {cto_summary['sod_trades']}")
            logger.info(f"  Exercise trades (excluded): {cto_summary['exercise_trades']}")
            logger.info(f"  Date range: {cto_summary['first_trade_date']} to {cto_summary['last_trade_date']}")
            logger.info(f"{'='*60}")
            
            # Trigger TYU5 P&L calculation after successful trade processing
            try:
                logger.info("Triggering TYU5 P&L calculation...")
                tyu5_service = TYU5Service()
                excel_path = tyu5_service.calculate_pnl()  # Fixed: was run_calculation()
                if excel_path:
                    logger.info(f"TYU5 calculation completed: {excel_path}")
                else:
                    logger.warning("TYU5 calculation returned no output file")
            except Exception as e:
                # Don't fail trade processing if TYU5 fails
                logger.error(f"TYU5 calculation failed (trades still processed): {e}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error processing trade file {input_path.name}: {e}")
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