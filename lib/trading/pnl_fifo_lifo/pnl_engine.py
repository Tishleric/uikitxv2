"""
PnL Calculation Engine

Purpose: Core calculation logic for FIFO/LIFO trade processing and P&L calculations
This module preserves the exact calculation logic from the original implementation.
"""

from datetime import datetime, timedelta
import pytz
from .config import VERBOSE, PNL_MULTIPLIER

def process_new_trade(conn, new_trade, method='fifo', trade_timestamp=None):
    """Process a new trade and offset against existing positions"""
    
    cursor = conn.cursor()
    table_suffix = method.lower()
    remaining_qty = new_trade['quantity']
    realized_trades = []
    
    # Get existing positions of opposite side
    opposite_side = 'S' if new_trade['buySell'] == 'B' else 'B'
    positions_query = f"""
        SELECT sequenceId, transactionId, symbol, price, quantity, time 
        FROM trades_{table_suffix} 
        WHERE symbol = ? AND buySell = ? AND quantity > 0
        ORDER BY sequenceId {'ASC' if method == 'fifo' else 'DESC'}
    """
    
    positions = cursor.execute(positions_query, (new_trade['symbol'], opposite_side)).fetchall()
    
    for pos in positions:
        if remaining_qty <= 0:
            break
            
        pos_seq_id, pos_trans_id, pos_symbol, pos_price, pos_qty, pos_time = pos
        offset_qty = min(remaining_qty, pos_qty)
        
        # Calculate realized P&L (multiply by 1000 for proper scaling)
        if opposite_side == 'S':  # We're buying, offsetting a short
            # Short position: entry at higher price (pos_price), exit at lower price (new_trade['price'])
            realized_pnl = (pos_price - new_trade['price']) * offset_qty * PNL_MULTIPLIER
            entry_price = pos_price
            exit_price = new_trade['price']
        else:  # We're selling, offsetting a long
            # Long position: entry at lower price (pos_price), exit at higher price (new_trade['price'])
            realized_pnl = (new_trade['price'] - pos_price) * offset_qty * PNL_MULTIPLIER
            entry_price = pos_price
            exit_price = new_trade['price']
        
        # Record realization
        realized_trades.append({
            'symbol': new_trade['symbol'],
            'sequenceIdBeingOffset': pos_seq_id,
            'sequenceIdDoingOffsetting': new_trade['sequenceId'],
            'partialFull': 'full' if offset_qty == pos_qty else 'partial',
            'quantity': offset_qty,
            'entryPrice': entry_price,
            'exitPrice': exit_price,
            'realizedPnL': realized_pnl,
            'timestamp': trade_timestamp if trade_timestamp else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Update or remove the offset position
        if offset_qty == pos_qty:
            # Full offset - remove from unrealized
            cursor.execute(f"DELETE FROM trades_{table_suffix} WHERE sequenceId = ?", (pos_seq_id,))
        else:
            # Partial offset - update quantity and mark as partial
            cursor.execute(f"""
                UPDATE trades_{table_suffix} 
                SET quantity = ?, fullPartial = 'partial' 
                WHERE sequenceId = ?
            """, (pos_qty - offset_qty, pos_seq_id))
        
        remaining_qty -= offset_qty
    
    # Insert realized trades
    if realized_trades:
        insert_realized = f"""
            INSERT INTO realized_{table_suffix} 
            (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting, partialFull, 
             quantity, entryPrice, exitPrice, realizedPnL, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.executemany(insert_realized, [
            (r['symbol'], r['sequenceIdBeingOffset'], r['sequenceIdDoingOffsetting'], 
             r['partialFull'], r['quantity'], r['entryPrice'], r['exitPrice'], 
             r['realizedPnL'], r['timestamp']) 
            for r in realized_trades
        ])
    
    # Insert remaining quantity as new position if any
    if remaining_qty > 0:
        new_trade_data = dict(new_trade)
        new_trade_data['quantity'] = remaining_qty
        if remaining_qty < new_trade['quantity']:
            new_trade_data['fullPartial'] = 'partial'
        
        insert_new = f"""
            INSERT INTO trades_{table_suffix} 
            (transactionId, symbol, price, original_price, quantity, buySell, sequenceId, time, original_time, fullPartial)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_new, (
            new_trade_data['transactionId'], new_trade_data['symbol'], 
            new_trade_data['price'], new_trade_data['price'],  # original_price = price on insert
            new_trade_data['quantity'], 
            new_trade_data['buySell'], new_trade_data['sequenceId'], 
            new_trade_data['time'], new_trade_data['time'],  # original_time = time on insert
            new_trade_data['fullPartial']
        ))
    # The calling function is now responsible for committing the transaction.
    return realized_trades


def get_effective_entry_price(actual_entry_price, sod_price, trade_time):
    """
    Implements Pmax logic: use whichever happened later (SOD or actual entry)
    If trade happened today, use actual price. If from previous day, use SOD.
    """
    # Parse trade time and get today's 5pm Chicago
    cdt = pytz.timezone('US/Central')
    trade_dt = datetime.strptime(trade_time, '%Y-%m-%d %H:%M:%S.%f')
    trade_dt = cdt.localize(trade_dt.replace(tzinfo=None))
    
    now_cdt = datetime.now(cdt)
    today_5pm = now_cdt.replace(hour=17, minute=0, second=0, microsecond=0)
    yesterday_5pm = today_5pm - timedelta(days=1)
    
    # If trade is from before today's start (5pm yesterday), use SOD price
    if trade_dt < yesterday_5pm:
        return sod_price
    else:
        return actual_entry_price


def get_current_time_period():
    """Determine if we're before 2pm, between 2-4pm, or after 4pm Chicago"""
    cdt = pytz.timezone('US/Central')
    now_cdt = datetime.now(cdt)
    hour = now_cdt.hour
    
    if hour < 14:  # Before 2pm
        return 'pre_2pm'
    elif hour < 16:  # 2pm-4pm
        return '2pm_to_4pm'
    else:  # After 4pm
        return 'post_4pm'


def calculate_unrealized_pnl(positions_df, price_dicts, method='live'):
    """
    Calculate unrealized PnL for positions
    method: 'live', '2pm_close', or '4pm_close'
    """
    if positions_df.empty:
        return []
    
    results = []
    time_period = get_current_time_period() if method == 'live' else None
    
    for _, pos in positions_df.iterrows():
        symbol = pos['symbol']
        qty = pos['quantity']
        actual_price = pos['price']
        trade_time = pos['time']
        
        # Get all relevant prices
        sod_tod = price_dicts['sodTod'].get(symbol, actual_price)
        sod_tom = price_dicts['sodTom'].get(symbol, actual_price)
        close_price = price_dicts['close'].get(symbol, actual_price)
        now_price = price_dicts['now'].get(symbol, actual_price)
        
        # Get effective entry price (Pmax logic)
        entry_price = get_effective_entry_price(actual_price, sod_tod, trade_time)
        
        # Calculate based on method
        if method == 'live':
            if time_period == 'pre_2pm':
                # Before 2pm: use sodTod as intermediate
                pnl = ((sod_tod - entry_price) * qty + (now_price - sod_tod) * qty) * PNL_MULTIPLIER
                intermediate = sod_tod
            else:  # 2pm_to_4pm or post_4pm
                # After 2pm: use sodTom as intermediate
                pnl = ((sod_tom - entry_price) * qty + (now_price - sod_tom) * qty) * PNL_MULTIPLIER
                intermediate = sod_tom
                
        elif method == '2pm_close':
            # 2pm snapshot: use sodTom as intermediate, close as exit
            pnl = ((sod_tom - entry_price) * qty + (close_price - sod_tom) * qty) * PNL_MULTIPLIER
            intermediate = sod_tom
            now_price = close_price
            
        elif method == '4pm_close':
            # 4pm EOD: use sodTod as intermediate, close as exit
            pnl = ((sod_tod - entry_price) * qty + (close_price - sod_tod) * qty) * PNL_MULTIPLIER
            intermediate = sod_tod
            now_price = close_price
        
        # Adjust for position direction
        if pos['buySell'] == 'S':
            pnl = -pnl  # Short positions have inverted P&L
        
        results.append({
            'sequenceId': pos['sequenceId'],
            'symbol': symbol,
            'quantity': qty,
            'buySell': pos['buySell'],
            'entryPrice': entry_price,
            'intermediatePrice': intermediate,
            'exitPrice': now_price,
            'unrealizedPnL': pnl,
            'method': method,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return results


def calculate_daily_simple_unrealized_pnl(positions_df, settle_prices):
    """
    Calculate simplified unrealized P&L for daily positions
    Formula: (Settle Price - Entry Price) × Quantity × 1000
    
    Args:
        positions_df: DataFrame with unrealized positions (from trades_fifo/lifo)
        settle_prices: Dict of symbol -> settle price (from 'close' price type)
    
    Returns:
        List of dicts with P&L details per position
    """
    if positions_df.empty:
        return []
    
    results = []
    for _, pos in positions_df.iterrows():
        symbol = pos['symbol']
        qty = pos['quantity']
        entry_price = pos['price']  # Actual trade price
        
        # Get settle price, default to entry if not available
        settle_price = settle_prices.get(symbol, entry_price)
        
        # Simple calculation: (settle - entry) × qty × 1000
        pnl = (settle_price - entry_price) * qty * PNL_MULTIPLIER
        
        # Invert for short positions
        if pos['buySell'] == 'S':
            pnl = -pnl
        
        results.append({
            'sequenceId': pos['sequenceId'],
            'symbol': symbol,
            'quantity': qty,
            'buySell': pos['buySell'],
            'entryPrice': entry_price,
            'settlePrice': settle_price,
            'unrealizedPnL': pnl,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return results


def calculate_historical_unrealized_pnl(positions_df, price_dicts, valuation_dt):
    """Calculate unrealized P&L with historical valuation date"""
    if positions_df.empty:
        return []
    
    results = []
    for _, pos in positions_df.iterrows():
        symbol = pos['symbol']
        qty = pos['quantity']
        actual_price = pos['price']
        trade_time_str = pos['time']
        
        # Get prices
        sod_tod = price_dicts['sodTod'].get(symbol, actual_price)
        close_price = price_dicts['close'].get(symbol, actual_price)
        
        # Parse trade time
        trade_dt = datetime.strptime(trade_time_str, '%Y-%m-%d %H:%M:%S.%f')
        
        # Determine effective entry price based on valuation date
        val_date = valuation_dt.date()
        trade_date = trade_dt.date()
        
        # If trade is from before valuation date, use SOD price
        if trade_date < val_date:
            entry_price = sod_tod
        else:
            entry_price = actual_price
        
        # 4pm EOD calculation
        pnl = ((sod_tod - entry_price) * qty + (close_price - sod_tod) * qty) * PNL_MULTIPLIER
        
        # Adjust for short positions
        if pos['buySell'] == 'S':
            pnl = -pnl
        
        results.append({
            'sequenceId': pos['sequenceId'],
            'symbol': symbol,
            'quantity': qty,
            'buySell': pos['buySell'],
            'entryPrice': entry_price,
            'unrealizedPnL': pnl
        })
    
    return results 