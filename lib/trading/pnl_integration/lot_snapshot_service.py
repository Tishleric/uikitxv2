"""
Open Lot Snapshot Service

Captures snapshots of all open positions at 2pm CDT daily for P&L period tracking.
"""

import sqlite3
import logging
from datetime import datetime, time
import pytz
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path

from lib.trading.pnl_integration.settlement_constants import CHICAGO_TZ, SETTLEMENT_TIME

logger = logging.getLogger(__name__)


class LotSnapshotService:
    """Service to capture and store open lot snapshots at settlement time."""
    
    def __init__(self, 
                 pnl_db_path: str = "data/output/pnl/pnl_tracker.db",
                 market_db_path: str = "data/output/market_prices/market_prices.db"):
        """
        Initialize the snapshot service.
        
        Args:
            pnl_db_path: Path to P&L tracker database
            market_db_path: Path to market prices database
        """
        self.pnl_db_path = pnl_db_path
        self.market_db_path = market_db_path
        
    def capture_snapshot(self, snapshot_time: Optional[datetime] = None) -> Dict[str, int]:
        """
        Capture snapshot of all open lots at settlement time.
        
        Args:
            snapshot_time: Time to capture snapshot (default: now)
            
        Returns:
            Dict with counts of lots captured by symbol
        """
        if snapshot_time is None:
            snapshot_time = datetime.now(CHICAGO_TZ)
        
        # Generate settlement key
        settlement_key = self._generate_settlement_key(snapshot_time)
        logger.info(f"Capturing lot snapshot for settlement key: {settlement_key}")
        
        conn = sqlite3.connect(self.pnl_db_path)
        try:
            # Get current open lots from tyu5_position_breakdown
            open_lots_df = self._get_open_lots(conn)
            
            if open_lots_df.empty:
                logger.info("No open lots to snapshot")
                return {}
            
            # Get current market prices
            market_prices = self._get_market_prices(open_lots_df['Symbol'].unique())
            
            # Prepare snapshot records
            snapshot_records = []
            for _, lot in open_lots_df.iterrows():
                symbol = lot['Symbol']
                mark_price = market_prices.get(symbol)
                
                snapshot_records.append((
                    lot['Lot_ID'],
                    settlement_key,
                    symbol,
                    lot['Remaining_Quantity'],
                    lot['Entry_Price'],
                    lot['Entry_DateTime'],
                    mark_price,
                    snapshot_time
                ))
            
            # Write snapshots to database
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO tyu5_open_lot_snapshots
                (lot_id, settlement_key, symbol, quantity_remaining, 
                 entry_price, entry_datetime, mark_price, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, snapshot_records)
            
            conn.commit()
            
            # Count by symbol
            counts = open_lots_df.groupby('Symbol')['Lot_ID'].count().to_dict()
            
            logger.info(f"Captured {len(snapshot_records)} lot snapshots for {len(counts)} symbols")
            return counts
            
        except Exception as e:
            logger.error(f"Error capturing lot snapshot: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _generate_settlement_key(self, dt: datetime) -> str:
        """Generate settlement key in YYYYMMDD_HHMM format."""
        chicago_dt = dt.astimezone(CHICAGO_TZ)
        return chicago_dt.strftime("%Y%m%d_1400")  # Always 2pm for settlements
    
    def _get_open_lots(self, conn: sqlite3.Connection) -> pd.DataFrame:
        """Get current open positions from positions table."""
        # Use tyu5_positions which has the actual position data
        query = """
            SELECT 
                Symbol || '_AGG' as Lot_ID,  -- Aggregate position ID
                Symbol,
                Symbol as Position_ID,
                Avg_Entry_Price as Entry_Price,
                CURRENT_TIMESTAMP as Entry_DateTime,  -- Placeholder
                Net_Quantity as Initial_Quantity,
                Net_Quantity as Remaining_Quantity,
                Type
            FROM tyu5_positions
            WHERE Net_Quantity != 0
            ORDER BY Symbol
        """
        
        return pd.read_sql_query(query, conn)
    
    def _get_market_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current market prices for symbols."""
        prices = {}
        
        try:
            conn = sqlite3.connect(self.market_db_path)
            
            for symbol in symbols:
                # Try futures first
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT current_price 
                    FROM futures_prices 
                    WHERE symbol = ? 
                    ORDER BY last_updated DESC 
                    LIMIT 1
                """, (symbol + " Comdty",))
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    prices[symbol] = float(result[0])
                else:
                    # Try options
                    cursor.execute("""
                        SELECT current_price 
                        FROM options_prices 
                        WHERE symbol = ? 
                        ORDER BY last_updated DESC 
                        LIMIT 1
                    """, (symbol + " Comdty",))
                    
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        prices[symbol] = float(result[0])
                        
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting market prices: {e}")
            
        return prices
    
    def get_snapshots_for_period(self, 
                                start_key: str, 
                                end_key: str) -> pd.DataFrame:
        """
        Get lot snapshots for a specific period.
        
        Args:
            start_key: Start settlement key (e.g., "20240115_1400")
            end_key: End settlement key (e.g., "20240116_1400")
            
        Returns:
            DataFrame with lot snapshots
        """
        conn = sqlite3.connect(self.pnl_db_path)
        
        query = """
            SELECT * FROM tyu5_open_lot_snapshots
            WHERE settlement_key >= ? AND settlement_key <= ?
            ORDER BY symbol, lot_id
        """
        
        df = pd.read_sql_query(query, conn, params=(start_key, end_key))
        conn.close()
        
        return df
    
    def is_2pm_snapshot_needed(self) -> bool:
        """Check if a 2pm snapshot is needed for today."""
        now = datetime.now(CHICAGO_TZ)
        
        # Check if it's 2pm
        if now.hour != 14 or now.minute > 5:  # Allow 5 minute window
            return False
            
        # Check if we already have a snapshot for today
        today_key = self._generate_settlement_key(now)
        
        conn = sqlite3.connect(self.pnl_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tyu5_open_lot_snapshots
            WHERE settlement_key = ?
        """, (today_key,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count == 0 