"""TYU5 Runner - Primary interface for running TYU5 P&L calculations with CSV data

This is the recommended way to run TYU5 calculations. It accepts pandas DataFrames
directly, making it ideal for:
- Loading trade data from CSV files
- Processing data without database dependencies  
- Direct integration with data pipelines

Example usage:
    # Load CSV data
    trades_df = pd.read_csv('trades.csv')
    prices_df = pd.read_csv('prices.csv')
    
    # Transform to TYU5 format as needed
    trades_input = transform_trades(trades_df)  # Your transformation logic
    
    # Run calculation
    runner = TYU5Runner()
    result = runner.run_with_capture(trades_input, prices_df)
    
    # Access results
    positions = result['positions_df']
    summary = result['summary_df']
"""
import pandas as pd
from pathlib import Path
import logging
from typing import Dict
import lib.trading.pnl.tyu5_pnl.main
from datetime import datetime

logger = logging.getLogger(__name__)


class TYU5Runner:
    """Wrapper to run TYU5 and capture DataFrames directly"""
    
    def __init__(self, tyu5_path: str = None, output_file: str = None):
        if tyu5_path is None:
            # Find TYU5 path relative to current directory
            tyu5_path = Path(__file__).parent.parent / "pnl" / "tyu5_pnl"
        self.tyu5_path = Path(tyu5_path).absolute()
        
        # Set default output file
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/output/pnl/tyu5_debug_{timestamp}.xlsx"
        self.output_file = output_file
        
    def run_with_capture(self, trades_df: pd.DataFrame, market_prices_df: pd.DataFrame = None, 
                        debug: bool = False, base_price: float = 110.78125, 
                        price_range: tuple = (-0.5, 0.5), steps: int = 11) -> Dict[str, pd.DataFrame]:
        """Run TYU5 P&L calculation with DataFrame inputs and capture results.
        
        Args:
            trades_df: DataFrame with columns: Date, Time, Symbol, Action, Quantity, Price, Fees, Type
            market_prices_df: Optional DataFrame with columns: Symbol, Current_Price, Prior_Close, Flash_Close
            debug: Enable debug logging for detailed calculation trace
            base_price: Base price for risk matrix calculations
            price_range: Price range for risk scenarios (min, max)
            steps: Number of steps in risk matrix
            
        Returns:
            Dictionary containing:
            - processed_trades_df: Processed trades with realized P&L
            - positions_df: Current positions with unrealized P&L (shows "awaiting data" for missing prices)
            - summary_df: P&L summary metrics
            - risk_df: Risk scenario matrix
            - breakdown_df: Position breakdown details
        """
        # Prepare sample data format that TYU5 expects
        sample_data = {
            'Trades_Input': trades_df,
            'Market_Prices': market_prices_df
        }
        
        # Call TYU5's main function directly with DataFrame inputs
        return lib.trading.pnl.tyu5_pnl.main.run_pnl_analysis(
            input_file=None,  # Not needed with sample_data
            output_file=self.output_file,
            base_price=base_price,
            price_range=price_range,
            steps=steps,
            sample_data=sample_data,
            debug=debug
        ) 