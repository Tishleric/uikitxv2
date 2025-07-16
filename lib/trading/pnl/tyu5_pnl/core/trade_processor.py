import pandas as pd
from core.utils import price_to_decimal, decimal_to_32nds

import pandas as pd
from core.utils import price_to_decimal, decimal_to_32nds

class TradeProcessor:
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.position_details = {}
        self.current_prices = {}
        self.multiplier = multiplier

    def process_trades(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        processed = []
        trades_df['DateTime'] = trades_df.apply(lambda x: str(x['Date']) + ' ' + str(x['Time']), axis=1)
        trades_df = trades_df.sort_values('DateTime')

        for tid, trade in trades_df.iterrows():
            symbol = trade['Symbol']
            quantity = float(trade['Quantity'])
            price = price_to_decimal(trade['Price'])
            action = trade['Action'].upper()
            trade_id = trade['trade_id'] if 'trade_id' in trade else f"TRADE_{symbol}_{tid}"
            type_ = trade['Type'] if 'Type' in trade else 'FUT'
            if symbol not in self.position_details:
                self.position_details[symbol] = {'trades': [], 'matches': []}
            if symbol not in self.positions:
                self.positions[symbol] = []

            self.position_details[symbol]['trades'].append({
                'trade_id': trade_id,
                'date': trade['DateTime'],
                'action': action,
                'quantity': quantity,
                'price': price,
                'Type': type_,
                'fees': trade.get('Fees', 0)
            })

            realized_pnl = 0
            matches = []
            remaining = abs(quantity)

            # --- SELL/SHORT: match against open longs, open new short if excess ---
            if action in ['SELL', 'SHORT']:
                # Match against open long positions
                for pos in self.positions[symbol]:
                    if remaining <= 0:
                        break
                    if pos['remaining'] > 0 and pos['action'] in ['BUY', 'COVER']:
                        matched = min(remaining, pos['remaining'])
                        pnl = matched * (price - pos['price']) * self.multiplier
                        realized_pnl += pnl
                        match_detail = {
                            'match_date': trade['DateTime'],
                            'opening_trade': pos['trade_id'],
                            'closing_trade': trade_id,
                            'quantity': matched,
                            'entry_price': pos['price'],
                            'exit_price': price,
                            'Type': type_,
                            'realized_pnl': pnl
                        }
                        matches.append(match_detail)
                        self.position_details[symbol]['matches'].append(match_detail)
                        pos['remaining'] -= matched
                        remaining -= matched
                # If there is unmatched quantity, open a new short position
                if remaining > 0:
                    self.positions[symbol].append({
                        'position_id': f"POS_{symbol}_{len(self.positions[symbol])+1:03d}",
                        'quantity': -remaining,
                        'price': price,
                        'date': trade['DateTime'],
                        'remaining': -remaining,
                        'Type': type_,
                        'trade_id': trade_id,
                        'action': action
                    })

            # --- BUY/COVER: match against open shorts, open new long if excess ---
            elif action in ['BUY', 'COVER']:
                # Match against open short positions
                for pos in self.positions[symbol]:
                    if remaining <= 0:
                        break
                    if pos['remaining'] < 0 and pos['action'] in ['SELL', 'SHORT']:
                        matched = min(remaining, -pos['remaining'])
                        pnl = matched * (pos['price'] - price) * self.multiplier
                        realized_pnl += pnl
                        match_detail = {
                            'match_date': trade['DateTime'],
                            'opening_trade': pos['trade_id'],
                            'closing_trade': trade_id,
                            'quantity': matched,
                            'entry_price': pos['price'],
                            'exit_price': price,
                            'Type': type_,
                            'realized_pnl': pnl
                        }
                        matches.append(match_detail)
                        self.position_details[symbol]['matches'].append(match_detail)
                        pos['remaining'] += matched  # less negative (closer to zero)
                        remaining -= matched
                # If there is unmatched quantity, open a new long position
                if remaining > 0:
                    self.positions[symbol].append({
                        'position_id': f"POS_{symbol}_{len(self.positions[symbol])+1:03d}",
                        'quantity': remaining,
                        'price': price,
                        'date': trade['DateTime'],
                        'remaining': remaining,
                        'Type': type_,
                        'trade_id': trade_id,
                        'action': action
                    })

            # --- For other actions, just record as is (rare) ---
            else:
                self.positions[symbol].append({
                    'position_id': f"POS_{symbol}_{len(self.positions[symbol])+1:03d}",
                    'quantity': quantity,
                    'price': price,
                    'date': trade['DateTime'],
                    'remaining': quantity,
                    'Type': type_,
                    'trade_id': trade_id,
                    'action': action
                })

            processed.append({
                'Trade_ID': trade_id,
                'DateTime': trade['DateTime'],
                'Symbol': symbol,
                'Action': action,
                'Quantity': quantity,
                'Price_Decimal': price,
                'Price_32nds': decimal_to_32nds(price),
                'Fees': trade.get('Fees', 0),
                'Type': type_,
                'Realized_PNL': realized_pnl,
                'Counterparty': trade.get('Counterparty', '')
            })

            self.current_prices[symbol] = price

        return pd.DataFrame(processed)