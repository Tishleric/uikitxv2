import os
import pandas as pd
from datetime import datetime, timedelta
from .core.trade_processor import TradeProcessor
from .core.position_calculator import PositionCalculator2 as PositionCalculator
from .core.pnl_summary import PNLSummary
from .core.risk_matrix import RiskMatrix
from .core.breakdown_generator import BreakdownGenerator
from .pnl_io.excel_writer import ExcelWriterModule   
from .core.debug_logger import get_debug_logger, set_debug_mode
import datetime
global today
today = datetime.date.today()

# Import settlement price loader
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from lib.trading.pnl_integration.settlement_price_loader import SettlementPriceLoader

def extract_pnl_components(positions_full_df: pd.DataFrame, breakdown_df: pd.DataFrame) -> pd.DataFrame:
    """Extract P&L components from positions DataFrame into a flat structure.
    
    Args:
        positions_full_df: Full positions DataFrame with detailed_components
        breakdown_df: Breakdown DataFrame for lot mapping (currently unused)
        
    Returns:
        DataFrame with P&L components ready for database storage
    """
    components = []
    
    for idx, position in positions_full_df.iterrows():
        if 'detailed_components' not in position:
            continue
            
        detailed_components = position['detailed_components']
        if not detailed_components:
            continue
            
        symbol = position['Symbol']
        
        for i, comp in enumerate(detailed_components):
            # Generate lot_id from symbol and component index
            lot_id = f"{symbol}_{idx}_{i}"
            
            components.append({
                'lot_id': lot_id,
                'symbol': symbol,
                'component_type': comp.period_type,
                'start_time': comp.start_time,
                'end_time': comp.end_time,
                'start_price': comp.start_price,
                'end_price': comp.end_price,
                'quantity': 0,  # Placeholder - would need lot details
                'pnl_amount': comp.pnl_amount,
                'start_settlement_key': getattr(comp, 'start_settlement_key', None),
                'end_settlement_key': getattr(comp, 'end_settlement_key', None)
            })
    
    return pd.DataFrame(components)

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
    
    # Pass lot breakdown with timestamps for settlement-aware P&L
    lot_breakdown_df = tp.get_position_breakdown_with_timestamps()
    pc.update_lot_details(lot_breakdown_df)
    
    if market_prices_df is not None:
        pc.update_prices(market_prices_df)
    
    # Load settlement prices for P&L calculation
    _load_and_apply_settlement_prices(pc, trades_df)
        
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
    
    # Get full positions DataFrame with settlement components
    positions_full_df = pc.calculate_positions_with_settlement()
    
    # Extract P&L components into separate DataFrame
    pnl_components_df = extract_pnl_components(positions_full_df, breakdown_df)
    
    # Return DataFrames for database storage
    return {
        'processed_trades_df': processed_trades_df,
        'positions_df': positions_df,
        'summary_df': summary_df,
        'risk_df': risk_df,
        'breakdown_df': breakdown_df,
        'pnl_components_df': pnl_components_df
    }


def _load_and_apply_settlement_prices(position_calculator, trades_df):
    """
    Load settlement prices and apply to position calculator.
    
    This is critical for accurate P&L calculation with settlement splits.
    """
    logger = get_debug_logger()
    
    try:
        # Get unique symbols from positions
        symbols = list(position_calculator.positions.keys())
        if not symbols:
            logger.log("SETTLEMENT_PRICES", "No positions to load prices for")
            return
        
        # Determine period bounds from trades
        if not trades_df.empty and 'DateTime' in trades_df.columns:
            trade_times = pd.to_datetime(trades_df['DateTime'])
            earliest_trade = trade_times.min()
            latest_trade = trade_times.max()
            
            # Add buffer for settlements
            period_start = earliest_trade - timedelta(days=1)
            period_end = latest_trade + timedelta(days=1)
        else:
            # Default to last week if no trades
            period_end = datetime.datetime.now()
            period_start = period_end - timedelta(days=7)
        
        # Load settlement prices
        loader = SettlementPriceLoader()
        settlement_prices = loader.load_settlement_prices_for_period(
            period_start, period_end, symbols
        )
        
        # Apply to position calculator
        for settle_date, prices in settlement_prices.items():
            position_calculator.update_settlement_prices(settle_date, prices)
        
        logger.log("SETTLEMENT_PRICES", 
                  f"Loaded settlement prices for {len(settlement_prices)} dates")
        
    except Exception as e:
        logger.log("SETTLEMENT_PRICES", f"Error loading settlement prices: {e}")
        # Don't fail the entire calculation, but the P&L will be incomplete
