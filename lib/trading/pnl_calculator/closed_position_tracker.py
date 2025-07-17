"""
Closed Position Tracker

This module tracks closed positions by analyzing trade history from the cto_trades table.
It calculates cumulative positions and identifies when positions go to zero.
"""

import logging
from datetime import datetime, date
from typing import Dict, Optional, Tuple
import sqlite3
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    def monitor(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class ClosedPositionTracker:
    """Tracks closed positions based on trade history."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @monitor()
    def calculate_closed_positions_for_date(self, trade_date: date) -> Dict[str, float]:
        """
        Calculate closed positions for a specific date.
        
        Returns:
            Dict mapping symbol to closed quantity for that date
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all trades up to and including the specified date
        query = """
        SELECT Symbol, Date, Time, Quantity
        FROM cto_trades
        WHERE Date <= ?
          AND is_sod = 0
          AND is_exercise = 0
        ORDER BY Date, Time
        """
        
        cursor.execute(query, (trade_date.isoformat(),))
        trades = cursor.fetchall()
        
        # Calculate cumulative positions day by day
        daily_positions = defaultdict(lambda: defaultdict(float))  # date -> symbol -> position
        closed_today = defaultdict(float)  # symbol -> closed quantity today
        
        for trade in trades:
            symbol = trade['Symbol']
            quantity = float(trade['Quantity'])
            t_date = datetime.strptime(trade['Date'], '%Y-%m-%d').date()
            
            # Get previous position
            if t_date == date.min:  # First date
                prev_position = 0
            else:
                # Find the most recent date before this one
                prev_dates = [d for d in daily_positions.keys() if d < t_date]
                if prev_dates:
                    prev_date = max(prev_dates)
                    prev_position = daily_positions[prev_date].get(symbol, 0)
                else:
                    prev_position = 0
            
            # Calculate new position
            new_position = prev_position + quantity
            daily_positions[t_date][symbol] = new_position
            
            # Check if this is the target date and position went through zero
            if t_date == trade_date:
                # Position closed today if:
                # 1. Previous position was non-zero and new position is zero
                # 2. OR position went through zero (sign changed)
                if prev_position != 0 and new_position == 0:
                    # Full close
                    closed_today[symbol] += abs(prev_position)
                elif prev_position != 0 and new_position != 0 and (prev_position * new_position < 0):
                    # Position flipped sign (went through zero)
                    closed_today[symbol] += abs(prev_position)
        
        conn.close()
        return dict(closed_today)
    
    @monitor()
    def update_positions_table_with_closed_quantities(self, trade_date: Optional[date] = None):
        """
        Update the positions table with closed quantities.
        
        Args:
            trade_date: Date to calculate closed positions for (default: today)
        """
        if trade_date is None:
            trade_date = date.today()
            
        # Calculate closed positions
        closed_positions = self.calculate_closed_positions_for_date(trade_date)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # First, reset all closed_quantity to 0
        cursor.execute("UPDATE positions SET closed_quantity = 0")
        
        # Update closed quantities for symbols that had closures
        for symbol, closed_qty in closed_positions.items():
            cursor.execute("""
                UPDATE positions 
                SET closed_quantity = ?
                WHERE instrument_name = ?
            """, (closed_qty, symbol))
            
            # If position doesn't exist in positions table (fully closed), insert it
            cursor.execute("""
                INSERT OR IGNORE INTO positions (
                    instrument_name, position_quantity, avg_cost, 
                    total_realized_pnl, unrealized_pnl, closed_quantity,
                    last_updated
                ) VALUES (?, 0, 0, 0, 0, ?, CURRENT_TIMESTAMP)
            """, (symbol, closed_qty))
            
            logger.info(f"Updated closed quantity for {symbol}: {closed_qty}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated closed quantities for {len(closed_positions)} symbols on {trade_date}")
    
    @monitor()
    def get_position_history(self, symbol: str) -> list:
        """
        Get full position history for a symbol.
        
        Returns:
            List of (date, position, trades) tuples
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT Date, Time, Quantity, Price, Action
        FROM cto_trades
        WHERE Symbol = ?
          AND is_sod = 0
          AND is_exercise = 0
        ORDER BY Date, Time
        """
        
        cursor.execute(query, (symbol,))
        trades = cursor.fetchall()
        
        history = []
        cumulative_position = 0
        
        for trade in trades:
            quantity = float(trade['Quantity'])
            cumulative_position += quantity
            
            history.append({
                'date': trade['Date'],
                'time': trade['Time'],
                'action': trade['Action'],
                'quantity': quantity,
                'price': float(trade['Price']),
                'position_after': cumulative_position
            })
        
        conn.close()
        return history 