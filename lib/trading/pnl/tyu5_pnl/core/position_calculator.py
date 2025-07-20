import pandas as pd
from core.utils import price_to_decimal, decimal_to_32nds
from core.bachelier import run_pnl_attribution
import datetime

class PositionCalculator2:
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.position_details = {}
        self.current_prices = {}      # Live current price
        self.flash_prices = {}         # Flash close price
        self.prior_close_prices = {}
        self.realized_pnl = {}         # ACTIVE: Store realized P&L by symbol
        self.multiplier = multiplier

    def update_prices(self, market_prices_df: pd.DataFrame):
        for _, row in market_prices_df.iterrows():
            symbol = row['Symbol']
            # ACTIVE: Updated to use Current_Price and added Flash_Close
            self.current_prices[symbol] = price_to_decimal(str(row['Current_Price']))
            self.flash_prices[symbol] = price_to_decimal(str(row['Flash_Close']))
            self.prior_close_prices[symbol] = price_to_decimal(str(row['Prior_Close'])) if pd.notna(row['Prior_Close']) else self.current_prices[symbol]

    def update_realized_pnl(self, processed_trades_df: pd.DataFrame):
        """Update realized P&L from processed trades.
        
        Args:
            processed_trades_df: DataFrame from TradeProcessor with Realized_PNL column
        """
        # Aggregate realized P&L by symbol
        self.realized_pnl = processed_trades_df.groupby('Symbol')['Realized_PNL'].sum().to_dict()

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
            current = self.current_prices.get(symbol, avg_price)

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
            close_prev = self.prior_close_prices.get(symbol, current)

            # Weighted average close for the whole position
            if qty_today != 0 and qty_prev != 0:
                close = (qty_today * close_today + qty_prev * close_prev) / (qty_today + qty_prev)
            elif qty_today != 0:
                close = close_today
            else:
                close = close_prev

            # P&L logic works for both long (positive qty) and short (negative qty)
            # ACTIVE: Added multiple P&L calculations
            
            # Get all price values
            current = self.current_prices.get(symbol, avg_price)
            flash = self.flash_prices.get(symbol, avg_price)
            prior_close = self.prior_close_prices.get(symbol, avg_price)
            
            # Present Values
            prior_present_value = total_qty * avg_price * self.multiplier
            current_present_value = total_qty * current * self.multiplier
            
            # Multiple P&L calculations
            unrealized_current = total_qty * (current - avg_price) * self.multiplier
            unrealized_flash = total_qty * (flash - avg_price) * self.multiplier
            unrealized_close = total_qty * (prior_close - avg_price) * self.multiplier
            
            # Daily P&L still uses current vs close
            daily = total_qty * (current - close) * self.multiplier
            
            # Get realized P&L for this symbol
            symbol_realized_pnl = self.realized_pnl.get(symbol, 0.0)
            
            # Total P&L includes both realized and unrealized
            total_pnl = symbol_realized_pnl + unrealized_current

            result.append({
                'Symbol': symbol,
                'Type': type_,
                'Net_Quantity': total_qty,
                'Avg_Entry_Price': avg_price,
                'Avg_Entry_Price_32nds': decimal_to_32nds(avg_price),
                'Prior_Close': close,
                'Current_Price': current,
                'Prior_Present_Value': prior_present_value,
                'Current_Present_Value': current_present_value,
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
        self.multiplier = multiplier

    def update_prices(self, market_prices_df: pd.DataFrame):
        for _, row in market_prices_df.iterrows():
            symbol = row['Symbol']
            # ACTIVE: Updated to use Current_Price and added Flash_Close
            self.current_prices[symbol] = price_to_decimal(str(row['Current_Price']))
            self.flash_prices[symbol] = price_to_decimal(str(row['Flash_Close']))
            self.prior_close_prices[symbol] = price_to_decimal(str(row['Prior_Close'])) if pd.notna(row['Prior_Close']) else self.current_prices[symbol]

    def update_realized_pnl(self, processed_trades_df: pd.DataFrame):
        """Update realized P&L from processed trades.
        
        Args:
            processed_trades_df: DataFrame from TradeProcessor with Realized_PNL column
        """
        # Aggregate realized P&L by symbol
        self.realized_pnl = processed_trades_df.groupby('Symbol')['Realized_PNL'].sum().to_dict()

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
            current = self.current_prices.get(symbol, avg_price)

            today_lots = [p for p in pos_list if p.get('date', '')[:10] == today]
            prev_lots = [p for p in pos_list if p.get('date', '')[:10] != today]

            qty_today = sum(p['remaining'] for p in today_lots)
            qty_prev = sum(p['remaining'] for p in prev_lots)

            close_today = (
                sum(p['remaining'] * p['price'] for p in today_lots) / qty_today
                if qty_today != 0 else 0
            )
            close_prev = self.prior_close_prices.get(symbol, current)

            if qty_today != 0 and qty_prev != 0:
                close = (qty_today * close_today + qty_prev * close_prev) / (qty_today + qty_prev)
            elif qty_today != 0:
                close = close_today
            else:
                close = close_prev

            # ACTIVE: Get all price values
            flash = self.flash_prices.get(symbol, avg_price)
            prior_close = self.prior_close_prices.get(symbol, avg_price)
            
            # ACTIVE: Present Values
            prior_present_value = total_qty * avg_price * self.multiplier
            current_present_value = total_qty * current * self.multiplier
            
            # ACTIVE: Multiple P&L calculations
            unrealized = total_qty * (current - avg_price) * self.multiplier
            unrealized_current = unrealized  # Same as unrealized, for clarity
            unrealized_flash = total_qty * (flash - avg_price) * self.multiplier
            unrealized_close = total_qty * (prior_close - avg_price) * self.multiplier
            
            daily = total_qty * (current - close) * self.multiplier
            
            # Get realized P&L for this symbol
            symbol_realized_pnl = self.realized_pnl.get(symbol, 0.0)
            
            # Total P&L includes both realized and unrealized
            total_pnl = symbol_realized_pnl + unrealized

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

                    symbol = parts[0]           # 'WY3N5'
                    type_ = parts[1]            # 'C' (call) or 'P' (put)
                    strike = float(parts[2])    # 110.25
                    print(dict(
                        now=now_dt-datetime.timedelta(days=0),
                        option_symbol=symbol,
                        calendar_csv='core/ExpirationCalendar.csv',
                        F=110+11.5/32,
                        K=strike,
                        P=current,
                        Prior=prior_price,
                        F_prior=110+5/32,
                        dT=dT,
                        option_type=type_.lower(),
                        r=0.01
                    ))                    
                    attribution_result = run_pnl_attribution(
                        now=now_dt-datetime.timedelta(days=1),
                        option_symbol=symbol,
                        calendar_csv='core/ExpirationCalendar.csv',
                        F=F,
                        K=strike,
                        P=current,
                        Prior=prior_price,
                        F_prior=F_prior,
                        dT=dT,
                        option_type=type_.lower(),
                        r=0.01
                    )

                    attribution = attribution_result.get('attribution', {})
                except Exception as e:
                    attribution = {'attribution_error': str(e)}

            row = {
                'Symbol': symbol,
                'Type': type_,
                'Net_Quantity': total_qty,
                'Avg_Entry_Price': avg_price,
                'Avg_Entry_Price_32nds': decimal_to_32nds(avg_price),
                'Prior_Close': close,
                'Current_Price': current,
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