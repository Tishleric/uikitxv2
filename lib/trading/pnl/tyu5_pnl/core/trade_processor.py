import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from .utils import price_to_decimal, decimal_to_32nds
from .debug_logger import get_debug_logger
import json

class TradeProcessor:
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.position_details = {}
        self.current_prices = {}
        self.closed_quantities = {}  # Track cumulative closed quantities by symbol
        self.multiplier = multiplier
        self.lot_counter = 0  # For generating unique lot IDs

    def _generate_lot_id(self, symbol: str) -> str:
        """Generate unique lot ID."""
        self.lot_counter += 1
        return f"LOT_{symbol}_{self.lot_counter:06d}"

    def _serialize_matches(self, matches: List[Dict]) -> str:
        """Serialize matches list to JSON, handling datetime objects."""
        if not matches:
            return ''
        
        # Convert datetime objects to strings
        serializable_matches = []
        for match in matches:
            serializable_match = {}
            for key, value in match.items():
                if isinstance(value, (datetime, pd.Timestamp)):
                    serializable_match[key] = str(value)
                else:
                    serializable_match[key] = value
            serializable_matches.append(serializable_match)
        
        return json.dumps(serializable_matches)

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
            trade_datetime = pd.to_datetime(trade['DateTime'])  # Parse as datetime
            
            logger.log("TRADE_PROCESSING", f"Processing trade {trade_id}", {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'type': type_,
                'datetime': str(trade_datetime)
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
                'datetime': trade_datetime,  # Store as datetime object
                'action': action,
                'quantity': quantity,
                'price': price,
                'Type': type_,
                'fees': trade.get('Fees', 0)
            })

            realized_pnl = 0
            matches = []
            remaining = abs(quantity)
            trade_sign = 1 if action == 'BUY' else -1

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
                    
                    # Mark lot as fully closed if remaining is 0
                    if pos['remaining'] == 0:
                        pos['exit_datetime'] = trade_datetime
                        pos['exit_price'] = price
                        pos['exit_trade_id'] = trade_id
                    
                    matches.append({
                        'position_id': pos['position_id'],
                        'lot_id': pos.get('lot_id'),
                        'matched_quantity': match_quantity,
                        'pnl': pnl,
                        'entry_datetime': pos['entry_datetime'],
                        'exit_datetime': trade_datetime,
                        'entry_price': pos['price'],
                        'exit_price': price
                    })

                self.position_details[symbol]['matches'].extend(matches)
                
                # If there is unmatched quantity, open a new position
                if remaining > 0:
                    net_quantity = remaining * trade_sign
                    lot_id = self._generate_lot_id(symbol)
                    new_position = {
                        'position_id': trade_id,
                        'lot_id': lot_id,
                        'quantity': net_quantity,
                        'price': price,
                        'remaining': abs(net_quantity),
                        'Type': type_,
                        'date': trade['DateTime'],
                        'entry_datetime': trade_datetime,  # Track entry time
                        'entry_trade_id': trade_id,
                        'exit_datetime': None,  # Not yet closed
                        'exit_price': None,
                        'exit_trade_id': None
                    }
                    self.positions[symbol].append(new_position)
                    
                    logger.log("POSITION", f"Opened new position {lot_id}", {
                        'symbol': symbol,
                        'quantity': net_quantity,
                        'price': price,
                        'entry_time': str(trade_datetime)
                    })

            # Process the trade
            processed_trade = trade.to_dict()
            processed_trade['Realized_PNL'] = realized_pnl
            processed_trade['Matches'] = self._serialize_matches(matches)
            processed_trade['Symbol'] = symbol
            processed_trade['Price'] = decimal_to_32nds(price)
            processed.append(processed_trade)

        return pd.DataFrame(processed)

    def get_position_breakdown_with_timestamps(self) -> pd.DataFrame:
        """
        Get detailed position breakdown with entry/exit timestamps.
        
        Returns DataFrame with all lots and their lifecycle information.
        """
        breakdown = []
        
        for symbol, positions in self.positions.items():
            for pos in positions:
                breakdown.append({
                    'Symbol': symbol,
                    'Lot_ID': pos.get('lot_id', pos['position_id']),
                    'Position_ID': pos['position_id'],
                    'Entry_Trade_ID': pos.get('entry_trade_id'),
                    'Entry_DateTime': pos.get('entry_datetime'),
                    'Entry_Price': pos['price'],
                    'Initial_Quantity': pos['quantity'],
                    'Remaining_Quantity': pos['remaining'],
                    'Exit_Trade_ID': pos.get('exit_trade_id'),
                    'Exit_DateTime': pos.get('exit_datetime'),
                    'Exit_Price': pos.get('exit_price'),
                    'Is_Closed': pos['remaining'] == 0,
                    'Type': pos['Type']
                })
        
        return pd.DataFrame(breakdown)