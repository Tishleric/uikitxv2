import pandas as pd
from .utils import price_to_decimal, decimal_to_32nds
from .bachelier import run_pnl_attribution
from .settlement_pnl import SettlementPnLCalculator, PnLComponent
import datetime
import os  # Added for path resolution
from typing import Dict, List, Optional, Tuple

class PositionCalculator2:
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.position_details = {}
        self.current_prices = {}      # Live current price
        self.flash_prices = {}         # Flash close price
        self.prior_close_prices = {}
        self.realized_pnl = {}         # ACTIVE: Store realized P&L by symbol
        self.closed_quantities = {}    # ACTIVE: Store closed quantities by symbol
        self.multiplier = multiplier
        self.settlement_calculator = SettlementPnLCalculator(multiplier)
        self.settlement_prices = {}    # Store all settlement prices by date
        self.lot_details = {}          # Enhanced lot tracking with timestamps
        self.market_price_timestamps = {}  # Store timestamp of market prices

    def update_prices(self, market_prices_df: pd.DataFrame):
        from .debug_logger import get_debug_logger
        logger = get_debug_logger()
        
        if market_prices_df is None or market_prices_df.empty:
            logger.log("PRICE_UPDATE", "No market prices provided")
            return
            
        logger.log("PRICE_UPDATE", f"Updating prices for {len(market_prices_df)} symbols")
        
        for _, row in market_prices_df.iterrows():
            symbol = row['Symbol']
            # ACTIVE: Handle missing prices without fallbacks
            
            # Store market price timestamp if available
            if 'last_updated' in row and pd.notna(row['last_updated']):
                self.market_price_timestamps[symbol] = pd.to_datetime(row['last_updated'])
            
            # Only set prices if they are actually available
            if pd.notna(row.get('Current_Price')):
                price = price_to_decimal(str(row['Current_Price']))
                self.current_prices[symbol] = price
                logger.log_price_lookup(symbol, 'Current_Price', price, 'market_prices_df')
            else:
                logger.log_price_lookup(symbol, 'Current_Price', None, 'market_prices_df')
                
            if pd.notna(row.get('Flash_Close')):
                price = price_to_decimal(str(row['Flash_Close']))
                self.flash_prices[symbol] = price
                logger.log_price_lookup(symbol, 'Flash_Close', price, 'market_prices_df')
            else:
                logger.log_price_lookup(symbol, 'Flash_Close', None, 'market_prices_df')
                
            if pd.notna(row.get('Prior_Close')):
                price = price_to_decimal(str(row['Prior_Close']))
                self.prior_close_prices[symbol] = price
                logger.log_price_lookup(symbol, 'Prior_Close', price, 'market_prices_df')
            else:
                logger.log_price_lookup(symbol, 'Prior_Close', None, 'market_prices_df')

    def update_settlement_prices(self, settlement_date: datetime.date, prices: Dict[str, float]):
        """
        Update settlement prices for a specific date.
        
        Args:
            settlement_date: The settlement date
            prices: Dict mapping symbol to settlement price
        """
        self.settlement_prices[settlement_date] = prices

    def update_lot_details(self, lot_breakdown_df: pd.DataFrame):
        """
        Update enhanced lot details with timestamps from trade processor.
        
        Args:
            lot_breakdown_df: DataFrame from TradeProcessor.get_position_breakdown_with_timestamps()
        """
        self.lot_details = {}
        
        for _, lot in lot_breakdown_df.iterrows():
            symbol = lot['Symbol']
            if symbol not in self.lot_details:
                self.lot_details[symbol] = []
            
            self.lot_details[symbol].append({
                'lot_id': lot['Lot_ID'],
                'position_id': lot['Position_ID'],
                'entry_datetime': pd.to_datetime(lot['Entry_DateTime']),
                'entry_price': lot['Entry_Price'],
                'initial_quantity': lot['Initial_Quantity'],
                'remaining_quantity': lot['Remaining_Quantity'],
                'exit_datetime': pd.to_datetime(lot['Exit_DateTime']) if pd.notna(lot['Exit_DateTime']) else None,
                'exit_price': lot['Exit_Price'] if pd.notna(lot['Exit_Price']) else None,
                'is_closed': lot['Is_Closed'],
                'type': lot['Type']
            })

    def update_realized_pnl(self, processed_trades_df: pd.DataFrame):
        """Update realized P&L from processed trades.
        
        Args:
            processed_trades_df: DataFrame from TradeProcessor with Realized_PNL column
        """
        # Aggregate realized P&L by symbol
        self.realized_pnl = processed_trades_df.groupby('Symbol')['Realized_PNL'].sum().to_dict()
        
    def update_closed_quantities(self, closed_quantities: dict):
        """Update closed quantities from TradeProcessor.
        
        Args:
            closed_quantities: Dictionary mapping symbol to closed quantity
        """
        self.closed_quantities = closed_quantities.copy()

    def calculate_positions(self) -> pd.DataFrame:
        """Calculate positions with backward compatibility."""
        # Call the new settlement-aware method
        settlement_df = self.calculate_positions_with_settlement()
        
        # If empty, return empty with expected columns
        if settlement_df.empty:
            return pd.DataFrame(columns=[
                'Symbol', 'Type', 'Net_Quantity', 'Closed_Quantity',
                'Avg_Entry_Price', 'Avg_Entry_Price_32nds', 'Prior_Close',
                'Current_Price', 'Flash_Close', 'Prior_Present_Value',
                'Current_Present_Value', 'Unrealized_PNL', 'Unrealized_PNL_Current',
                'Unrealized_PNL_Flash', 'Unrealized_PNL_Close', 'Daily_PNL',
                'Realized_PNL', 'Total_PNL'
            ])
        
        # Return simplified view for backward compatibility
        return settlement_df[[
            'Symbol', 'Type', 'Net_Quantity', 'Closed_Quantity',
            'Avg_Entry_Price', 'Avg_Entry_Price_32nds', 'Prior_Close',
            'Current_Price', 'Flash_Close', 'Prior_Present_Value',
            'Current_Present_Value', 'Unrealized_PNL', 'Unrealized_PNL_Current',
            'Unrealized_PNL_Flash', 'Unrealized_PNL_Close', 'Daily_PNL',
            'Realized_PNL', 'Total_PNL'
        ]]

    def calculate_positions_with_settlement(self) -> pd.DataFrame:
        """Calculate positions with settlement-aware P&L breakdown."""
        today = datetime.date.today().strftime('%Y-%m-%d')
        result = []
        
        for symbol, pos_list in self.positions.items():
            # Support both long (positive) and short (negative) positions
            total_qty = sum(p['remaining'] for p in pos_list)
            type_ = pos_list[0]['Type']
            if total_qty == 0:
                continue
            
            # Weighted average entry price (works for both long and short)
            total_val = sum(p['remaining'] * p['price'] for p in pos_list)
            avg_price = total_val / total_qty if total_qty != 0 else 0
            current = self.current_prices.get(symbol, None)

            # Separate today's and previous days' positions
            today_lots = [p for p in pos_list if p.get('date', '')[:10] == today]
            prev_lots = [p for p in pos_list if p.get('date', '')[:10] != today]

            qty_today = sum(p['remaining'] for p in today_lots)
            qty_prev = sum(p['remaining'] for p in prev_lots)

            # Weighted close: use trade price for today's lots, prior close for previous lots
            close_today = (
                sum(p['remaining'] * p['price'] for p in today_lots) / qty_today
                if qty_today != 0 else 0
            )
            close_prev = self.prior_close_prices.get(symbol, None)

            # Weighted average close for the whole position
            if close_prev is None:
                close = None
            elif qty_today != 0 and qty_prev != 0:
                close = (qty_today * close_today + qty_prev * close_prev) / (qty_today + qty_prev)
            elif qty_today != 0:
                close = close_today
            else:
                close = close_prev
            
            # Get all price values (will be None if not available)
            current = self.current_prices.get(symbol, None)
            flash = self.flash_prices.get(symbol, None)
            prior_close = self.prior_close_prices.get(symbol, None)
            
            # Present Values - only calculate if prices available
            prior_present_value = total_qty * avg_price * self.multiplier
            current_present_value = total_qty * current * self.multiplier if current is not None else None
            
            # Traditional P&L calculations for backward compatibility
            unrealized_current = total_qty * (current - avg_price) * self.multiplier if current is not None else "awaiting data"
            unrealized_flash = total_qty * (flash - avg_price) * self.multiplier if flash is not None else "awaiting data"
            unrealized_close = total_qty * (prior_close - avg_price) * self.multiplier if prior_close is not None else "awaiting data"
            
            # Settlement-aware P&L calculation
            settlement_pnl_data = self._calculate_settlement_aware_pnl(symbol)
            
            # Daily P&L still uses current vs close
            daily = total_qty * (current - close) * self.multiplier if current is not None and close is not None else "awaiting data"
            
            # Get realized P&L for this symbol
            symbol_realized_pnl = self.realized_pnl.get(symbol, 0.0)
            
            # Get closed quantity for this symbol
            symbol_closed_qty = self.closed_quantities.get(symbol, 0.0)
            
            # Total P&L includes both realized and unrealized
            total_pnl = symbol_realized_pnl + unrealized_current if unrealized_current != "awaiting data" else "awaiting data"

            result.append({
                'Symbol': symbol,
                'Type': type_,
                'Net_Quantity': total_qty,
                'Closed_Quantity': symbol_closed_qty,  # ACTIVE: Added closed quantity
                'Avg_Entry_Price': avg_price,
                'Avg_Entry_Price_32nds': decimal_to_32nds(avg_price),
                'Prior_Close': prior_close if prior_close is not None else "awaiting data",
                'Current_Price': current if current is not None else "awaiting data",
                'Flash_Close': flash if flash is not None else "awaiting data",  # ACTIVE: Added flash close price
                'Prior_Present_Value': prior_present_value,
                'Current_Present_Value': current_present_value if current_present_value is not None else "awaiting data",
                'Unrealized_PNL': unrealized_current,  # Keep backward compatibility
                'Unrealized_PNL_Current': unrealized_current,
                'Unrealized_PNL_Flash': unrealized_flash,
                'Unrealized_PNL_Close': unrealized_close,
                'Daily_PNL': daily,
                'Realized_PNL': symbol_realized_pnl,
                'Total_PNL': total_pnl,
                # Settlement-aware fields
                'Settlement_PNL_Total': settlement_pnl_data['total_pnl'],
                'PNL_Components': settlement_pnl_data['components'],
                'Settlements_Crossed': settlement_pnl_data['settlements_crossed'],
                'detailed_components': settlement_pnl_data.get('detailed_components', [])
            })

        return pd.DataFrame(result)
    
    def _calculate_settlement_aware_pnl(self, symbol: str) -> Dict:
        """
        Calculate settlement-aware P&L for a symbol using lot details.
        
        Returns aggregated P&L data with component breakdown.
        """
        if symbol not in self.lot_details:
            return {'total_pnl': 0, 'components': [], 'settlements_crossed': 0}
        
        all_components = []
        total_pnl = 0
        max_settlements = 0
        
        # Get symbol-specific settlement prices
        symbol_settlement_prices = {}
        for date, prices in self.settlement_prices.items():
            if symbol in prices:
                symbol_settlement_prices[date] = prices[symbol]
        
        # Calculate P&L for each lot
        for lot in self.lot_details[symbol]:
            if lot['remaining_quantity'] == 0 and not lot['is_closed']:
                continue  # Skip fully matched but not yet closed lots
            
            current_price = self.current_prices.get(symbol)
            if current_price is None:
                continue
            
            lot_result = self.settlement_calculator.calculate_lot_pnl(
                entry_time=lot['entry_datetime'],
                exit_time=lot['exit_datetime'],
                entry_price=lot['entry_price'],
                exit_price=lot['exit_price'],
                quantity=lot['initial_quantity'],
                current_price=current_price,
                settlement_prices=symbol_settlement_prices,
                current_price_time=self.market_price_timestamps.get(symbol)
            )
            
            total_pnl += lot_result['total_pnl']
            all_components.extend(lot_result['components'])
            
            # Track max settlements crossed
            settlements_in_lot = len([c for c in lot_result['components'] 
                                    if c.period_type in ['entry_to_settle', 'settle_to_settle', 'settle_to_exit']])
            max_settlements = max(max_settlements, settlements_in_lot)
        
        # Aggregate components by type
        aggregated = self.settlement_calculator.aggregate_components_by_type(all_components)
        
        return {
            'total_pnl': total_pnl,
            'components': aggregated,
            'settlements_crossed': max_settlements,
            'detailed_components': all_components  # Keep detailed breakdown
        }

    def get_settlement_pnl_breakdown(self) -> pd.DataFrame:
        """
        Get detailed P&L breakdown by component type for all positions.
        
        Returns DataFrame with P&L split by settlement periods.
        """
        breakdown = []
        
        for symbol in self.positions:
            pnl_data = self._calculate_settlement_aware_pnl(symbol)
            
            if pnl_data['detailed_components']:
                for component in pnl_data['detailed_components']:
                    breakdown.append({
                'Symbol': symbol,
                        'Period_Type': component.period_type,
                        'Start_Time': component.start_time,
                        'End_Time': component.end_time,
                        'Start_Price': component.start_price,
                        'End_Price': component.end_price,
                        'PNL_Amount': component.pnl_amount
                    })

        return pd.DataFrame(breakdown)