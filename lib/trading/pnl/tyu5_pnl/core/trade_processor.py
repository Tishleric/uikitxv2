import pandas as pd
from .utils import price_to_decimal, decimal_to_32nds
from .debug_logger import get_debug_logger

class TradeProcessor:
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.position_details = {}
        self.current_prices = {}
        self.closed_quantities = {}  # Track cumulative closed quantities by symbol
        self.multiplier = multiplier

    def process_trades(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        logger = get_debug_logger()
        processed = []
        trades_df['DateTime'] = trades_df.apply(lambda x: str(x['Date']) + ' ' + str(x['Time']), axis=1)
        trades_df = trades_df.sort_values('DateTime')
        
        logger.log("TRADE_PROCESSING", f"Processing {len(trades_df)} trades")

        for tid, trade in trades_df.iterrows():
            symbol = trade['Symbol']
            quantity = float(trade['Quantity'])
            price = price_to_decimal(trade['Price'])
            action = trade['Action'].upper()
            trade_id = trade['trade_id'] if 'trade_id' in trade else f"TRADE_{symbol}_{tid}"
            type_ = trade['Type'] if 'Type' in trade else 'FUT'
            
            logger.log("TRADE_PROCESSING", f"Processing trade {trade_id}", {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'type': type_
            })
            
            if symbol not in self.position_details:
                self.position_details[symbol] = {'trades': [], 'matches': []}
            if symbol not in self.positions:
                self.positions[symbol] = []
            if symbol not in self.closed_quantities:
                self.closed_quantities[symbol] = 0  # Initialize closed quantity tracking

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

            # --- FIFO matching logic for BUY and SELL ---
            if action in ['BUY', 'SELL']:
                target_positions = [p for p in self.positions[symbol] if 
                    ((action == 'BUY' and p['quantity'] < 0) or 
                     (action == 'SELL' and p['quantity'] > 0)) and 
                    p['remaining'] != 0]

                for pos in target_positions:
                    if remaining <= 0:
                        break
                    match_quantity = min(remaining, abs(pos['remaining']))
                    pos_sign = 1 if pos['quantity'] > 0 else -1
                    trade_sign = 1 if action == 'BUY' else -1
                    
                    # Log the match attempt
                    logger.log_trade_matching(
                        symbol, action, quantity,
                        matched_qty=match_quantity,
                        remaining_qty=remaining - match_quantity
                    )

                    if action == 'BUY':
                        pnl = match_quantity * (price - pos['price']) * self.multiplier * pos_sign
                    else:
                        pnl = match_quantity * (pos['price'] - price) * self.multiplier * pos_sign

                    realized_pnl += pnl
                    pos['remaining'] -= match_quantity * pos_sign
                    remaining -= match_quantity
                    
                    # Track the closed quantity (absolute value)
                    self.closed_quantities[symbol] += match_quantity
                    
                    matches.append({
                        'position_id': pos['position_id'],
                        'matched_quantity': match_quantity,
                        'pnl': pnl
                    })

                self.position_details[symbol]['matches'].extend(matches)
                
                # If there is unmatched quantity, open a new position
                if remaining > 0:
                    position_quantity = remaining if action == 'BUY' else -remaining
                    self.positions[symbol].append({
                        'position_id': f"POS_{symbol}_{len(self.positions[symbol])+1:03d}",
                        'quantity': position_quantity,
                        'price': price,
                        'date': trade['DateTime'],
                        'remaining': position_quantity,
                        'Type': type_,
                        'trade_id': trade_id,
                        'action': action
                    })
                    logger.log("POSITION_CREATED", f"New position for {symbol}", {
                        'quantity': position_quantity,
                        'price': price,
                        'trade_id': trade_id
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