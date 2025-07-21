import pandas as pd
from .utils import price_to_decimal, decimal_to_32nds
from .bachelier import run_pnl_attribution
import datetime
import os  # Added for path resolution

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

            # P&L logic works for both long (positive qty) and short (negative qty)
            # ACTIVE: Added multiple P&L calculations
            
            # Get all price values (will be None if not available)
            current = self.current_prices.get(symbol, None)
            flash = self.flash_prices.get(symbol, None)
            prior_close = self.prior_close_prices.get(symbol, None)
            
            # Present Values - only calculate if prices available
            prior_present_value = total_qty * avg_price * self.multiplier
            current_present_value = total_qty * current * self.multiplier if current is not None else None
            
            # Multiple P&L calculations - show "awaiting data" if price missing
            unrealized_current = total_qty * (current - avg_price) * self.multiplier if current is not None else "awaiting data"
            unrealized_flash = total_qty * (flash - avg_price) * self.multiplier if flash is not None else "awaiting data"
            unrealized_close = total_qty * (prior_close - avg_price) * self.multiplier if prior_close is not None else "awaiting data"
            
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
                'Realized_PNL': symbol_realized_pnl,  # ACTIVE: Added realized P&L
                'Daily_PNL': daily,
                'Total_PNL': total_pnl  # ACTIVE: Now includes both realized and unrealized
            })

        return pd.DataFrame(result)
    
class PositionCalculator:
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.position_details = {}
        self.current_prices = {}      # Live current price
        self.flash_prices = {}         # Flash close price
        self.prior_close_prices = {}
        self.realized_pnl = {}         # ACTIVE: Store realized P&L by symbol
        self.closed_quantities = {}    # ACTIVE: Store closed quantities by symbol
        self.multiplier = multiplier

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
        today = datetime.date.today().strftime('%Y-%m-%d')
        result = []
        for symbol, pos_list in self.positions.items():
            total_qty = sum(p['remaining'] for p in pos_list)
            type_ = pos_list[0]['Type']
            if total_qty == 0:
                continue
            total_val = sum(p['remaining'] * p['price'] for p in pos_list)
            avg_price = total_val / total_qty if total_qty != 0 else 0
            current = self.current_prices.get(symbol, None)

            today_lots = [p for p in pos_list if p.get('date', '')[:10] == today]
            prev_lots = [p for p in pos_list if p.get('date', '')[:10] != today]

            qty_today = sum(p['remaining'] for p in today_lots)
            qty_prev = sum(p['remaining'] for p in prev_lots)

            close_today = (
                sum(p['remaining'] * p['price'] for p in today_lots) / qty_today
                if qty_today != 0 else 0
            )
            close_prev = self.prior_close_prices.get(symbol, None)

            if qty_today != 0 and qty_prev != 0:
                close = (qty_today * close_today + qty_prev * close_prev) / (qty_today + qty_prev)
            elif qty_today != 0:
                close = close_today
            else:
                close = close_prev

            # ACTIVE: Get all price values
            flash = self.flash_prices.get(symbol, None)
            prior_close = self.prior_close_prices.get(symbol, None)
            
            # ACTIVE: Present Values
            prior_present_value = total_qty * avg_price * self.multiplier
            current_present_value = total_qty * current * self.multiplier if current is not None else None
            
            # ACTIVE: Multiple P&L calculations
            unrealized = total_qty * (current - avg_price) * self.multiplier if current is not None else "awaiting data"
            unrealized_current = unrealized  # Same as unrealized, for clarity
            unrealized_flash = total_qty * (flash - avg_price) * self.multiplier if flash is not None else "awaiting data"
            unrealized_close = total_qty * (prior_close - avg_price) * self.multiplier if prior_close is not None else "awaiting data"
            
            # ACTIVE: Daily P&L uses current vs close
            daily = total_qty * (current - close) * self.multiplier if current is not None and close is not None else "awaiting data"
            
            # Get realized P&L for this symbol
            symbol_realized_pnl = self.realized_pnl.get(symbol, 0.0)
            
            # Get closed quantity for this symbol
            symbol_closed_qty = self.closed_quantities.get(symbol, 0.0)
            
            # Total P&L includes both realized and unrealized
            total_pnl = symbol_realized_pnl + unrealized if unrealized != "awaiting data" else "awaiting data"

            # --- Integrate run_pnl_attribution for options ---
            attribution = {}
            if type_ in ['CALL', 'PUT']:
                option_type = 'call' if type_ == 'CALL' else 'put'
                K = pos_list[0].get('Strike', avg_price)
                prior_price = close_prev
                F = current
                F_prior = close_prev
                dT = 1 / 252.0  # 1 day decay, adjust as needed
                try:
                    today_date = datetime.date.today()
                    if isinstance(today_date, datetime.date) and not isinstance(today_date, datetime.datetime):
                        now_dt = datetime.datetime.combine(today_date, datetime.time(0, 0))
                    else:
                        now_dt = today_date
                    option_str = symbol
                    parts = option_str.split()

                    base_symbol = parts[0]      # 'WY3N5' - use different variable name
                    opt_type = parts[1]         # 'C' (call) or 'P' (put)
                    strike = float(parts[2])    # 110.25
                    
                    # Fix: Use absolute path for ExpirationCalendar.csv
                    calendar_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), 
                        'ExpirationCalendar.csv'
                    )
                    
                    print(dict(
                        now=now_dt-datetime.timedelta(days=0),
                        option_symbol=base_symbol,
                        calendar_csv=calendar_path,  # Use absolute path
                        F=110+11.5/32,
                        K=strike,
                        P=current,
                        Prior=prior_price,
                        F_prior=110+5/32,
                        dT=dT,
                        option_type=opt_type.lower(),
                        r=0.01
                    ))                    
                    attribution_result = run_pnl_attribution(
                        now=now_dt-datetime.timedelta(days=1),
                        option_symbol=base_symbol,
                        calendar_csv=calendar_path,  # Use absolute path
                        F=F,
                        K=strike,
                        P=current,
                        Prior=prior_price,
                        F_prior=F_prior,
                        dT=dT,
                        option_type=opt_type.lower(),
                        r=0.01
                    )

                    attribution = attribution_result.get('attribution', {})
                except Exception as e:
                    attribution = {'attribution_error': str(e)}

            row = {
                'Symbol': symbol,
                'Type': type_,
                'Net_Quantity': total_qty,
                'Closed_Quantity': symbol_closed_qty,  # ACTIVE: Added closed quantity
                'Avg_Entry_Price': avg_price,
                'Avg_Entry_Price_32nds': decimal_to_32nds(avg_price),
                'Prior_Close': close,
                'Current_Price': current,
                'Flash_Close': flash,  # ACTIVE: Added flash close price
                'Prior_Present_Value': prior_present_value,  # ACTIVE: Added
                'Current_Present_Value': current_present_value,  # ACTIVE: Added
                'Unrealized_PNL': unrealized,  # Keep backward compatibility
                'Unrealized_PNL_Current': unrealized_current,  # ACTIVE: Added
                'Unrealized_PNL_Flash': unrealized_flash,  # ACTIVE: Added
                'Unrealized_PNL_Close': unrealized_close,  # ACTIVE: Added
                'Realized_PNL': symbol_realized_pnl,  # ACTIVE: Added realized P&L
                'Daily_PNL': daily,
                'Total_PNL': total_pnl
            }
            if attribution:
                row.update(attribution)

            result.append(row)

        return pd.DataFrame(result)