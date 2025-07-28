"""
Positions Aggregator Module

Purpose: Aggregate data from trades.db and spot_risk.db into unified POSITIONS table
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import pandas as pd

from .config import DEFAULT_SYMBOL
from .pnl_engine import calculate_unrealized_pnl
from .data_manager import view_unrealized_positions, load_pricing_dictionaries, get_trading_day

logger = logging.getLogger(__name__)


class PositionsAggregator:
    """Aggregates position, P&L, and Greek data into master positions table."""
    
    def __init__(self, trades_db_path: str, spot_risk_db_path: Optional[str] = None):
        """
        Initialize aggregator with database paths.
        
        Args:
            trades_db_path: Path to trades.db
            spot_risk_db_path: Path to spot_risk.db (optional)
        """
        self.trades_db_path = trades_db_path
        self.spot_risk_db_path = spot_risk_db_path or "data/output/spot_risk/spot_risk.db"
        
    def update_position(self, symbol: str) -> bool:
        """
        Update a single position in the POSITIONS table.
        
        Args:
            symbol: Bloomberg format symbol to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Gather data from both sources
            trade_data = self._get_trade_data(symbol)
            greek_data = self._get_greek_data(symbol) if Path(self.spot_risk_db_path).exists() else {}
            
            # Update positions table
            self._update_positions_table(symbol, trade_data, greek_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating position for {symbol}: {e}")
            return False
    
    def update_all_positions(self) -> Tuple[int, int]:
        """
        Update all positions in the POSITIONS table.
        
        Returns:
            Tuple of (successful_updates, failed_updates)
        """
        success_count = 0
        fail_count = 0
        
        # Get all unique symbols from trades
        symbols = self._get_all_symbols()
        
        for symbol in symbols:
            if self.update_position(symbol):
                success_count += 1
            else:
                fail_count += 1
                
        logger.info(f"Updated {success_count} positions, {fail_count} failures")
        return success_count, fail_count
    
    def _get_trade_data(self, symbol: str) -> Dict:
        """Get position and P&L data from trades.db."""
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        data = {
            'open_position': 0,
            'closed_position': 0,
            'fifo_realized_pnl': 0,
            'fifo_unrealized_pnl': 0,
            'lifo_realized_pnl': 0,
            'lifo_unrealized_pnl': 0
        }
        
        try:
            # Get current trading day
            current_trading_day = get_trading_day(datetime.now()).strftime('%Y-%m-%d')
            
            # Get open positions (net quantity)
            for method in ['fifo', 'lifo']:
                cursor.execute(f"""
                    SELECT SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END)
                    FROM trades_{method}
                    WHERE symbol = ? AND quantity > 0
                """, (symbol,))
                result = cursor.fetchone()
                if method == 'fifo':  # Use FIFO as primary position
                    data['open_position'] = result[0] if result[0] else 0
            
            # Get realized P&L for current trading day only
            for method in ['fifo', 'lifo']:
                cursor.execute("""
                    SELECT realized_pnl
                    FROM daily_positions
                    WHERE symbol = ? AND method = ? AND date = ?
                """, (symbol, method, current_trading_day))
                result = cursor.fetchone()
                data[f'{method}_realized_pnl'] = result[0] if result and result[0] else 0
            
            # Get closed positions from daily_positions for current trading day only
            cursor.execute("""
                SELECT closed_position
                FROM daily_positions
                WHERE symbol = ? AND method = 'fifo' AND date = ?
            """, (symbol, current_trading_day))
            result = cursor.fetchone()
            data['closed_position'] = result[0] if result and result[0] else 0
            
            # Calculate unrealized P&L
            price_dicts = load_pricing_dictionaries(conn)
            
            for method in ['fifo', 'lifo']:
                positions_df = view_unrealized_positions(conn, method)
                positions_df = positions_df[positions_df['symbol'] == symbol]
                
                if not positions_df.empty:
                    unrealized_list = calculate_unrealized_pnl(positions_df, price_dicts, 'live')
                    total_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
                    data[f'{method}_unrealized_pnl'] = total_unrealized
                    
        finally:
            conn.close()
            
        return data
    
    def _get_greek_data(self, symbol: str) -> Dict:
        """Get Greek data from spot_risk.db."""
        data = {
            'delta_y': None,
            'gamma_y': None,
            'speed_y': None,
            'theta': None,
            'vega': None,
            'has_greeks': False,
            'instrument_type': None
        }
        
        try:
            conn = sqlite3.connect(self.spot_risk_db_path)
            cursor = conn.cursor()
            
            # Get latest Greeks for this symbol
            cursor.execute("""
                SELECT 
                    c.delta_y, c.gamma_y, c.speed_F as speed_y, 
                    c.theta_F as theta, c.vega_y as vega,
                    r.instrument_type
                FROM spot_risk_calculated c
                JOIN spot_risk_raw r ON c.raw_id = r.id
                WHERE r.bloomberg_symbol = ?
                    AND c.calculation_status = 'success'
                ORDER BY c.calculation_timestamp DESC
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            if result:
                data['delta_y'] = result[0]
                data['gamma_y'] = result[1]
                data['speed_y'] = result[2]
                data['theta'] = result[3]
                data['vega'] = result[4]
                data['instrument_type'] = result[5]
                data['has_greeks'] = True
                
            conn.close()
            
        except Exception as e:
            logger.debug(f"Could not get Greeks for {symbol}: {e}")
            
        return data
    
    def _update_positions_table(self, symbol: str, trade_data: Dict, greek_data: Dict):
        """Update the positions table with aggregated data."""
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        try:
            # Prepare the update
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT OR REPLACE INTO positions (
                    symbol, open_position, closed_position,
                    delta_y, gamma_y, speed_y, theta, vega,
                    fifo_realized_pnl, fifo_unrealized_pnl,
                    lifo_realized_pnl, lifo_unrealized_pnl,
                    last_updated, last_trade_update, last_greek_update,
                    has_greeks, instrument_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                trade_data['open_position'],
                trade_data['closed_position'],
                greek_data.get('delta_y'),
                greek_data.get('gamma_y'),
                greek_data.get('speed_y'),
                greek_data.get('theta'),
                greek_data.get('vega'),
                trade_data['fifo_realized_pnl'],
                trade_data['fifo_unrealized_pnl'],
                trade_data['lifo_realized_pnl'],
                trade_data['lifo_unrealized_pnl'],
                now,
                now,  # last_trade_update
                now if greek_data.get('has_greeks') else None,  # last_greek_update
                1 if greek_data.get('has_greeks') else 0,
                greek_data.get('instrument_type')
            ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _get_all_symbols(self) -> List[str]:
        """Get all unique symbols from trades database."""
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        symbols = set()
        
        try:
            # Get symbols from trades tables
            for table in ['trades_fifo', 'trades_lifo', 'realized_fifo', 'realized_lifo']:
                cursor.execute(f"SELECT DISTINCT symbol FROM {table}")
                symbols.update(row[0] for row in cursor.fetchall())
                
        finally:
            conn.close()
            
        return list(symbols) 