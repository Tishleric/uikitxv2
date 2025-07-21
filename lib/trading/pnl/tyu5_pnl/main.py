import os
import pandas as pd
from .core.trade_processor import TradeProcessor
from .core.position_calculator import PositionCalculator
from .core.pnl_summary import PNLSummary
from .core.risk_matrix import RiskMatrix
from .core.breakdown_generator import BreakdownGenerator
from .pnl_io.excel_writer import ExcelWriterModule   
from .core.debug_logger import get_debug_logger, set_debug_mode
import datetime
global today
today = datetime.date.today()

def run_pnl_analysis(input_file, output_file, base_price, price_range, steps, sample_data=None, debug=False):
    # Enable debug mode if requested
    set_debug_mode(debug)
    logger = get_debug_logger()
    
    if debug:
        logger.log("INITIALIZATION", "Starting TYU5 P&L analysis", {
            'input_file': input_file,
            'output_file': output_file,
            'debug_mode': debug
        })
    
    if sample_data:
        trades_df = sample_data["Trades_Input"]
        market_prices_df = sample_data.get("Market_Prices")
    else:
        trades_df = pd.read_excel(input_file, sheet_name="Trades_Input")
        try:
            market_prices_df = pd.read_excel(input_file, sheet_name="Market_Prices")
        except:
            market_prices_df = None

    tp = TradeProcessor()
    processed_trades_df = tp.process_trades(trades_df)
    
    pc = PositionCalculator()
    pc.positions = tp.positions
    pc.position_details = tp.position_details
    pc.current_prices = tp.current_prices
    pc.update_realized_pnl(processed_trades_df)  # ACTIVE: Pass realized P&L data
    pc.update_closed_quantities(tp.closed_quantities)  # ACTIVE: Pass closed quantities
    
    if market_prices_df is not None:
        pc.update_prices(market_prices_df)
        
    positions_df = pc.calculate_positions()
    summary_df = PNLSummary().generate(positions_df, processed_trades_df)
    breakdown_df = BreakdownGenerator().create(tp.position_details, positions_df, tp.positions)
    
    tyu5_price = tp.current_prices.get("TYU5", base_price)
    risk_df = RiskMatrix().create(positions_df, base_price=tyu5_price, price_range=price_range, steps=steps)
    
    # Include debug logs in Excel if debug mode is enabled
    if debug:
        logger.log("COMPLETION", "Analysis complete, writing output")
        ExcelWriterModule().write(output_file, processed_trades_df, positions_df, summary_df, risk_df, breakdown_df, 
                                  debug_logs_df=logger.get_logs_dataframe())
    else:
        ExcelWriterModule().write(output_file, processed_trades_df, positions_df, summary_df, risk_df, breakdown_df)
    
    # Return DataFrames for database storage
    return {
        'processed_trades_df': processed_trades_df,
        'positions_df': positions_df,
        'summary_df': summary_df,
        'risk_df': risk_df,
        'breakdown_df': breakdown_df
    }
