"""Data Reprocessor for P&L System

Handles dropping and recreating all trading data tables,
then reprocessing from source files.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import time

# Import storage managers
from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.market_prices.storage import MarketPriceStorage

# Import processors
from lib.trading.market_prices.futures_processor import FuturesProcessor
from lib.trading.market_prices.options_processor import OptionsProcessor
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor

logger = logging.getLogger(__name__)


class DataReprocessor:
    """Orchestrates full data reprocessing for P&L system."""
    
    def __init__(self):
        """Initialize reprocessor with storage managers."""
        self.pnl_storage = PnLStorage()
        self.market_storage = MarketPriceStorage()
        
    def drop_all_tables(self) -> Dict[str, Any]:
        """Drop all trading data tables and clear processing state.
        
        Returns:
            Status dictionary with results
        """
        status = {
            'success': True,
            'dropped_tables': [],
            'errors': []
        }
        
        try:
            # Drop P&L tables
            logger.info("Dropping cto_trades table...")
            # Direct SQL since storage class might not have drop method
            with self.pnl_storage._get_connection() as conn:
                conn.execute("DROP TABLE IF EXISTS cto_trades")
                conn.execute("DROP TABLE IF EXISTS processed_trades")
                conn.execute("DROP TABLE IF EXISTS trade_processing_tracker")
                conn.execute("DROP TABLE IF EXISTS file_processing_log")
                conn.commit()
            status['dropped_tables'].extend(['cto_trades', 'processed_trades', 'trade_processing_tracker', 'file_processing_log'])
            
            # Drop market price tables
            logger.info("Dropping market price tables...")
            with self.market_storage._get_connection() as conn:
                conn.execute("DROP TABLE IF EXISTS futures_prices")
                conn.execute("DROP TABLE IF EXISTS options_prices")
                conn.execute("DROP TABLE IF EXISTS market_prices")
                conn.execute("DROP TABLE IF EXISTS price_file_tracker")
                conn.commit()
            status['dropped_tables'].extend(['futures_prices', 'options_prices', 'market_prices', 'price_file_tracker'])
            
            # Clear processing state files
            logger.info("Clearing processing state files...")
            state_file = Path("data/output/trade_ledger_processed/.processing_state.json")
            if state_file.exists():
                state_file.unlink()
                logger.info("Cleared trade processing state")
            
            # Reinitialize to recreate tables
            logger.info("Recreating empty tables...")
            self.pnl_storage._initialize_database()
            self.market_storage._init_database()
            
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            status['success'] = False
            status['errors'].append(str(e))
            
        return status
    
    def reprocess_futures_prices(self) -> Dict[str, Any]:
        """Reprocess all futures price files.
        
        Returns:
            Status dictionary with results
        """
        status = {
            'success': True,
            'files_processed': 0,
            'records_added': 0,
            'errors': []
        }
        
        try:
            processor = FuturesProcessor(self.market_storage)
            futures_dir = Path("data/input/market_prices/futures")
            
            if not futures_dir.exists():
                raise FileNotFoundError(f"Futures directory not found: {futures_dir}")
            
            csv_files = list(futures_dir.glob("*.csv"))
            logger.info(f"Found {len(csv_files)} futures price files")
            
            for csv_file in csv_files:
                try:
                    result = processor.process_file(csv_file)
                    if result:
                        status['files_processed'] += 1
                        # Estimate records from file size or parse result
                except Exception as e:
                    logger.error(f"Error processing {csv_file}: {e}")
                    status['errors'].append(f"{csv_file.name}: {str(e)}")
            
            # Get count of records
            with self.market_storage._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM futures_prices")
                status['records_added'] = cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error reprocessing futures: {e}")
            status['success'] = False
            status['errors'].append(str(e))
            
        return status
    
    def reprocess_options_prices(self) -> Dict[str, Any]:
        """Reprocess all options price files.
        
        Returns:
            Status dictionary with results
        """
        status = {
            'success': True,
            'files_processed': 0,
            'records_added': 0,
            'errors': []
        }
        
        try:
            processor = OptionsProcessor(self.market_storage)
            options_dir = Path("data/input/market_prices/options")
            
            if not options_dir.exists():
                raise FileNotFoundError(f"Options directory not found: {options_dir}")
            
            csv_files = list(options_dir.glob("*.csv"))
            logger.info(f"Found {len(csv_files)} options price files")
            
            for csv_file in csv_files:
                try:
                    result = processor.process_file(csv_file)
                    if result:
                        status['files_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing {csv_file}: {e}")
                    status['errors'].append(f"{csv_file.name}: {str(e)}")
            
            # Get count of records
            with self.market_storage._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM options_prices")
                status['records_added'] = cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error reprocessing options: {e}")
            status['success'] = False
            status['errors'].append(str(e))
            
        return status
    
    def reprocess_trades(self) -> Dict[str, Any]:
        """Reprocess all trade files.
        
        Returns:
            Status dictionary with results
        """
        status = {
            'success': True,
            'files_processed': 0,
            'trades_added': 0,
            'errors': []
        }
        
        try:
            processor = TradePreprocessor()
            processor.process_all_files("data/input/trade_ledger")
            
            # Get counts
            with self.pnl_storage._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cto_trades")
                status['trades_added'] = cursor.fetchone()[0]
                
                # Count files processed (estimate)
                cursor = conn.execute("SELECT COUNT(DISTINCT source_file) FROM cto_trades")
                status['files_processed'] = cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error reprocessing trades: {e}")
            status['success'] = False
            status['errors'].append(str(e))
            
        return status
    
    def orchestrate_full_reprocess(self) -> Dict[str, Any]:
        """Orchestrate the complete reprocessing workflow.
        
        Returns:
            Comprehensive status dictionary
        """
        start_time = time.time()
        
        results = {
            'overall_success': True,
            'start_time': start_time,
            'steps': {},
            'summary': {}
        }
        
        # Step 1: Drop tables
        logger.info("Step 1/4: Dropping all tables...")
        drop_result = self.drop_all_tables()
        results['steps']['drop_tables'] = drop_result
        
        if not drop_result['success']:
            results['overall_success'] = False
            results['summary']['error'] = "Failed to drop tables"
            return results
        
        # Step 2: Process futures prices
        logger.info("Step 2/4: Processing futures prices...")
        futures_result = self.reprocess_futures_prices()
        results['steps']['futures_prices'] = futures_result
        
        # Step 3: Process options prices
        logger.info("Step 3/4: Processing options prices...")
        options_result = self.reprocess_options_prices()
        results['steps']['options_prices'] = options_result
        
        # Step 4: Process trades (triggers TYU5)
        logger.info("Step 4/4: Processing trades...")
        trades_result = self.reprocess_trades()
        results['steps']['trades'] = trades_result
        
        # Summary
        results['elapsed_time'] = time.time() - start_time
        results['summary'] = {
            'futures_records': futures_result.get('records_added', 0),
            'options_records': options_result.get('records_added', 0),
            'trades_processed': trades_result.get('trades_added', 0),
            'total_errors': sum(len(step.get('errors', [])) for step in results['steps'].values())
        }
        
        # Check overall success
        if any(not step.get('success', True) for step in results['steps'].values()):
            results['overall_success'] = False
            
        logger.info(f"Reprocessing complete in {results['elapsed_time']:.2f} seconds")
        return results 