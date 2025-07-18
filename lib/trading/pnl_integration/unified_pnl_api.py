"""Unified P&L API - Merges TradePreprocessor and TYU5 advanced features

This API provides a comprehensive view of positions with lot tracking,
Greeks, risk scenarios, and P&L attribution.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import sqlite3
import json

from lib.trading.pnl_calculator.storage import PnLStorage

logger = logging.getLogger(__name__)


class UnifiedPnLAPI:
    """API for accessing unified P&L data with advanced TYU5 features."""
    
    def __init__(self, db_path: str = "data/output/pnl/pnl_tracker.db"):
        """Initialize the unified API.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.storage = PnLStorage(db_path)
        
    def get_positions_with_lots(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get positions with lot-level detail from TYU5 data.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of position dictionaries with lot details
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Query positions with lot details
            query = """
                SELECT 
                    p.instrument_name as symbol,
                    p.position_quantity as net_position,
                    p.avg_cost,
                    p.last_market_price,
                    p.total_realized_pnl,
                    p.unrealized_pnl,
                    p.short_quantity,
                    p.is_option,
                    p.option_strike,
                    p.option_expiry,
                    p.last_updated,
                    -- Aggregate lot data
                    COUNT(l.id) as lot_count,
                    SUM(l.remaining_quantity) as total_lot_quantity,
                    -- Latest Greek data
                    g.delta,
                    g.gamma,
                    g.vega,
                    g.theta,
                    g.speed,
                    g.implied_vol,
                    g.calc_timestamp as greek_timestamp
                FROM positions p
                LEFT JOIN lot_positions l ON p.instrument_name = l.symbol
                LEFT JOIN (
                    SELECT 
                        pg.*, 
                        p2.instrument_name,
                        ROW_NUMBER() OVER (PARTITION BY pg.position_id ORDER BY pg.calc_timestamp DESC) as rn
                    FROM position_greeks pg
                    JOIN positions p2 ON pg.position_id = p2.id
                ) g ON p.instrument_name = g.instrument_name AND g.rn = 1
                WHERE p.position_quantity != 0
            """
            
            params = []
            if symbol:
                query += " AND p.instrument_name = ?"
                params.append(symbol)
                
            query += " GROUP BY p.instrument_name"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            # Get individual lots for each position
            positions = []
            for _, pos in df.iterrows():
                position_dict = pos.to_dict()
                
                # Get detailed lots
                lot_query = """
                    SELECT 
                        trade_id,
                        remaining_quantity,
                        entry_price,
                        entry_date
                    FROM lot_positions
                    WHERE symbol = ?
                    ORDER BY entry_date
                """
                lots_df = pd.read_sql_query(lot_query, conn, params=[pos['symbol']])
                position_dict['lots'] = lots_df.to_dict('records')
                
                positions.append(position_dict)
                
            return positions
            
        finally:
            conn.close()
            
    def get_greek_exposure(self, as_of: Optional[datetime] = None) -> pd.DataFrame:
        """Get current Greek exposure across all positions.
        
        Args:
            as_of: Optional timestamp (defaults to latest)
            
        Returns:
            DataFrame with Greek values by position
        """
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
                SELECT 
                    p.instrument_name as symbol,
                    p.position_quantity,
                    p.is_option,
                    pg.underlying_price,
                    pg.implied_vol,
                    pg.delta,
                    pg.gamma,
                    pg.vega,
                    pg.theta,
                    pg.speed,
                    pg.calc_timestamp,
                    -- Position-weighted Greeks
                    pg.delta * p.position_quantity as position_delta,
                    pg.gamma * p.position_quantity as position_gamma,
                    pg.vega * p.position_quantity as position_vega,
                    pg.theta * p.position_quantity as position_theta,
                    pg.speed * p.position_quantity as position_speed
                FROM positions p
                JOIN position_greeks pg ON p.id = pg.position_id
                WHERE p.is_option = 1 AND p.position_quantity != 0
            """
            
            if as_of:
                query += " AND pg.calc_timestamp <= ?"
                params = [as_of]
            else:
                params = []
                
            # Get latest for each position
            query = f"""
                WITH ranked_greeks AS ({query})
                SELECT * FROM (
                    SELECT *, 
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY calc_timestamp DESC) as rn
                    FROM ranked_greeks
                ) WHERE rn = 1
            """
            
            return pd.read_sql_query(query, conn, params=params)
            
        finally:
            conn.close()
            
    def get_portfolio_greeks(self) -> Dict[str, float]:
        """Get aggregated portfolio-level Greeks.
        
        Returns:
            Dictionary with total portfolio Greeks
        """
        greeks_df = self.get_greek_exposure()
        
        if greeks_df.empty:
            return {
                'total_delta': 0.0,
                'total_gamma': 0.0,
                'total_vega': 0.0,
                'total_theta': 0.0,
                'total_speed': 0.0,
                'option_count': 0,
                'last_update': None
            }
            
        return {
            'total_delta': float(greeks_df['position_delta'].sum()),
            'total_gamma': float(greeks_df['position_gamma'].sum()),
            'total_vega': float(greeks_df['position_vega'].sum()),
            'total_theta': float(greeks_df['position_theta'].sum()),
            'total_speed': float(greeks_df['position_speed'].sum()),
            'option_count': len(greeks_df),
            'last_update': greeks_df['calc_timestamp'].max()
        }
        
    def get_risk_scenarios(self, symbol: Optional[str] = None, 
                          scenario_date: Optional[date] = None) -> pd.DataFrame:
        """Get risk scenario analysis.
        
        Args:
            symbol: Optional symbol to filter by
            scenario_date: Optional date (defaults to latest)
            
        Returns:
            DataFrame with scenario analysis
        """
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
                SELECT 
                    symbol,
                    scenario_price,
                    scenario_pnl,
                    scenario_delta,
                    scenario_gamma,
                    position_quantity,
                    calc_timestamp
                FROM risk_scenarios
                WHERE 1=1
            """
            
            params = []
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
                
            if scenario_date:
                query += " AND DATE(calc_timestamp) = ?"
                params.append(scenario_date)
            else:
                # Get latest scenarios
                query = f"""
                    WITH latest_calc AS (
                        SELECT MAX(calc_timestamp) as max_ts
                        FROM risk_scenarios
                    )
                    {query} AND calc_timestamp = (SELECT max_ts FROM latest_calc)
                """
                
            query += " ORDER BY symbol, scenario_price"
            
            return pd.read_sql_query(query, conn, params=params)
            
        finally:
            conn.close()
            
    def get_position_attribution(self, symbol: str, 
                               start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> pd.DataFrame:
        """Get P&L attribution by Greeks for a position.
        
        Args:
            symbol: Position symbol
            start_date: Start date for attribution
            end_date: End date for attribution
            
        Returns:
            DataFrame with P&L attribution
        """
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
                SELECT 
                    pa.calc_timestamp,
                    pa.total_pnl,
                    pa.delta_pnl,
                    pa.gamma_pnl,
                    pa.vega_pnl,
                    pa.theta_pnl,
                    pa.speed_pnl,
                    pa.residual_pnl,
                    p.instrument_name as symbol
                FROM pnl_attribution pa
                JOIN positions p ON pa.position_id = p.id
                WHERE p.instrument_name = ?
            """
            
            params = [symbol]
            
            if start_date:
                query += " AND DATE(pa.calc_timestamp) >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND DATE(pa.calc_timestamp) <= ?"
                params.append(end_date)
                
            query += " ORDER BY pa.calc_timestamp"
            
            return pd.read_sql_query(query, conn, params=params)
            
        finally:
            conn.close()
            
    def get_match_history(self, symbol: Optional[str] = None,
                         trade_date: Optional[date] = None) -> pd.DataFrame:
        """Get FIFO match history showing how positions were closed.
        
        Args:
            symbol: Optional symbol to filter by
            trade_date: Optional date to filter by
            
        Returns:
            DataFrame with match history
        """
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
                SELECT 
                    symbol,
                    match_date,
                    buy_trade_id,
                    sell_trade_id,
                    matched_quantity,
                    buy_price,
                    sell_price,
                    realized_pnl,
                    created_at
                FROM match_history
                WHERE 1=1
            """
            
            params = []
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
                
            if trade_date:
                query += " AND DATE(match_date) = ?"
                params.append(trade_date)
                
            query += " ORDER BY match_date DESC"
            
            return pd.read_sql_query(query, conn, params=params)
            
        finally:
            conn.close()
            
    def get_comprehensive_position_view(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive view of a position including all advanced features.
        
        Args:
            symbol: Position symbol
            
        Returns:
            Dictionary with complete position information
        """
        # Get position with lots
        positions = self.get_positions_with_lots(symbol)
        if not positions:
            return None
            
        position = positions[0]
        
        # Add Greeks if available
        greeks_df = self.get_greek_exposure()
        if not greeks_df.empty:
            greek_row = greeks_df[greeks_df['symbol'] == symbol]
            if not greek_row.empty:
                position['greeks'] = greek_row.iloc[0].to_dict()
                
        # Add risk scenarios
        scenarios_df = self.get_risk_scenarios(symbol)
        if not scenarios_df.empty:
            position['risk_scenarios'] = scenarios_df.to_dict('records')
            
        # Add P&L attribution if available
        attribution_df = self.get_position_attribution(symbol)
        if not attribution_df.empty:
            position['attribution_history'] = attribution_df.to_dict('records')
            
        # Add match history
        matches_df = self.get_match_history(symbol)
        if not matches_df.empty:
            position['match_history'] = matches_df.to_dict('records')
            
        return position
        
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary.
        
        Returns:
            Dictionary with portfolio-level metrics
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Get position summary
            position_summary = pd.read_sql_query("""
                SELECT 
                    COUNT(DISTINCT instrument_name) as position_count,
                    SUM(CASE WHEN position_quantity > 0 THEN 1 ELSE 0 END) as long_positions,
                    SUM(CASE WHEN position_quantity < 0 THEN 1 ELSE 0 END) as short_positions,
                    SUM(total_realized_pnl) as total_realized_pnl,
                    SUM(unrealized_pnl) as total_unrealized_pnl,
                    SUM(total_realized_pnl + unrealized_pnl) as total_pnl,
                    MAX(last_updated) as last_update
                FROM positions
                WHERE position_quantity != 0
            """, conn).iloc[0].to_dict()
            
            # Get lot summary
            lot_summary = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_lots,
                    COUNT(DISTINCT symbol) as symbols_with_lots
                FROM lot_positions
            """, conn).iloc[0].to_dict()
            
            # Get Greeks
            portfolio_greeks = self.get_portfolio_greeks()
            
            # Get scenario summary
            scenario_summary = pd.read_sql_query("""
                SELECT 
                    COUNT(DISTINCT symbol) as symbols_with_scenarios,
                    COUNT(DISTINCT calc_timestamp) as scenario_runs,
                    MAX(calc_timestamp) as latest_scenario_run
                FROM risk_scenarios
            """, conn).iloc[0].to_dict()
            
            return {
                'positions': position_summary,
                'lots': lot_summary,
                'greeks': portfolio_greeks,
                'scenarios': scenario_summary
            }
            
        finally:
            conn.close() 