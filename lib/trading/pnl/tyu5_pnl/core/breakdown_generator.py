import pandas as pd
from .utils import decimal_to_32nds

class BreakdownGenerator:
    def create(self, positions_df: dict, position_details: pd.DataFrame, positions: dict) -> pd.DataFrame:
        breakdown = []
        position_details = pd.DataFrame( position_details )
        for symbol in position_details.Symbol.unique():
            pos_info =  position_details[position_details.Symbol==symbol]
            if  pos_info.empty:
                continue

            current = pos_info.iloc[0]
            breakdown.append({
                'Symbol': symbol,
                'Label': 'SUMMARY',
                'Description': f"{symbol} Summary",
                'Quantity': current['Net_Quantity'],
                'Price': current['Current_Price'],
                'Daily_PNL': current['Daily_PNL'],
                'Type': current['Type'],
                'Inception_PNL': current['Unrealized_PNL'],
                'Notes': ''
            })

            # Fix: Handle symbol format mismatch
            # positions dict may have full symbol format (e.g., "VY3N5 P 109.500")
            # while position_details has base symbol (e.g., "VY3N5")
            
            # First try direct lookup
            symbol_positions = positions.get(symbol, [])
            
            # If not found and symbol looks like an option base (no space), 
            # try to find matching positions by prefix
            if not symbol_positions and ' ' not in symbol:
                # Look for positions that start with this symbol
                for pos_symbol, pos_list in positions.items():
                    if pos_symbol.startswith(symbol + ' '):
                        symbol_positions.extend(pos_list)
            
            for pos in symbol_positions:
                if pos['remaining'] == 0: continue
                entry_price = pos['price']
                current_price = current['Current_Price']
                unreal = (current_price - entry_price) * pos['remaining'] * 1000
                breakdown.append({
                    'Symbol': symbol,
                    'Label': 'OPEN_POSITION',
                    'Description': pos['position_id'],
                    'Quantity': pos['remaining'],
                    'Price': decimal_to_32nds(entry_price),
                    'Daily_PNL': '',
                    'Type': current['Type'],
                    'Inception_PNL': unreal,
            
                })

        return pd.DataFrame(breakdown)
