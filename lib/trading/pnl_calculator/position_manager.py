"""
Position Manager for tracking open positions with P&L

This module manages position state using FIFO calculations from the existing
PnLCalculator. It maintains a lightweight store of non-zero positions and 
handles position updates as trades are processed.
"""

import logging
from datetime import datetime, date, time
from typing import Dict, Any, Optional, List, Tuple
import pytz
from dataclasses import dataclass

from .calculator import PnLCalculator
from .storage import PnLStorage
from .models import Trade

# Set up module logger
logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    # Fallback if monitoring is not available
    def monitor(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@dataclass
class PositionUpdate:
    """Result of processing a trade against a position."""
    instrument_name: str
    previous_quantity: float
    new_quantity: float
    realized_pnl: float
    trade_action: str  # 'OPEN', 'CLOSE', 'AMEND'
    is_exercised: bool = False
    is_sod: bool = False


class PositionManager:
    """Manages position tracking with FIFO P&L calculations."""
    
    def __init__(self, storage: PnLStorage):
        """Initialize the position manager.
        
        Args:
            storage: Storage instance for database operations
        """
        self.storage = storage
        self.chicago_tz = pytz.timezone('America/Chicago')
        
        # FIFO calculators per instrument
        self.calculators: Dict[str, PnLCalculator] = {}
        
        # Track cumulative realized P&L per instrument
        self.realized_pnl_totals: Dict[str, float] = {}
        
        # Load existing positions on startup
        self._load_existing_positions()
    
    def _load_existing_positions(self):
        """Load existing positions from database on startup."""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT instrument_name, position_quantity, avg_cost, total_realized_pnl
        FROM positions
        WHERE position_quantity != 0
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            instrument = row['instrument_name']
            quantity = row['position_quantity']
            avg_cost = row['avg_cost']
            realized_pnl = row['total_realized_pnl']
            
            # Initialize calculator with existing position
            calc = PnLCalculator()
            self.calculators[instrument] = calc
            
            # Add a synthetic trade to establish position
            # Use a past date to ensure it's "first in"
            synthetic_date = datetime(2020, 1, 1, 0, 0, 0)
            calc.add_trade(synthetic_date, instrument, quantity, avg_cost)
            
            # Track realized P&L total
            self.realized_pnl_totals[instrument] = realized_pnl
            
            logger.info(f"Loaded position: {instrument} qty={quantity} avg_cost={avg_cost} realized_pnl={realized_pnl}")
        
        conn.close()
    
    def _get_calculator(self, instrument: str) -> PnLCalculator:
        """Get or create FIFO calculator for an instrument."""
        if instrument not in self.calculators:
            self.calculators[instrument] = PnLCalculator()
            self.realized_pnl_totals[instrument] = 0.0
        return self.calculators[instrument]
    
    def _is_option(self, instrument: str) -> bool:
        """Check if instrument is an option based on naming convention."""
        # Options contain 'OCA' or 'OPA' in the name
        return 'OCA' in instrument or 'OPA' in instrument
    
    def _extract_option_details(self, instrument: str) -> Tuple[Optional[float], Optional[date]]:
        """Extract strike and expiry from option instrument name."""
        if not self._is_option(instrument):
            return None, None
        
        try:
            # Format: XCMEOCADPS20250714N0VY2/108.75
            parts = instrument.split('/')
            if len(parts) == 2:
                strike = float(parts[1])
                
                # Extract date from the instrument code
                date_part = parts[0].split('PS')[1][:8]  # Get YYYYMMDD after PS
                expiry = datetime.strptime(date_part, '%Y%m%d').date()
                
                return strike, expiry
        except (ValueError, IndexError):
            logger.warning(f"Could not parse option details from {instrument}")
            
        return None, None
    
    @monitor()
    def process_trade(self, trade_data: Dict[str, Any]) -> PositionUpdate:
        """Process a trade and update position state.
        
        Args:
            trade_data: Dictionary with trade information including:
                - instrumentName: Instrument identifier
                - marketTradeTime: Trade timestamp
                - quantity: Signed quantity (+ for buy, - for sell)
                - price: Trade price
                - tradeId: Trade identifier
                
        Returns:
            PositionUpdate with details of the position change
        """
        # CTO_INTEGRATION: Original position tracking logic commented out
        # Will be replaced with CTO's calculation engine
        
        instrument = trade_data['instrumentName']
        quantity = float(trade_data['quantity'])
        price = float(trade_data['price'])
        trade_id = trade_data['tradeId']
        timestamp = datetime.strptime(str(trade_data['marketTradeTime']).split('.')[0], '%Y-%m-%d %H:%M:%S')
        
        # Add timezone
        timestamp = self.chicago_tz.localize(timestamp)
        
        # Check for special cases
        is_sod = timestamp.hour == 0 and timestamp.minute == 0
        is_exercised = price == 0.0  # Zero price indicates exercise
        
        if is_exercised:
            logger.warning(f"Exercised option detected: {instrument} trade {trade_id}")
        
        # CTO_INTEGRATION: Return mock position update
        logger.warning(f"Position tracking disabled - returning mock data for {instrument}")
        
        # Return mock PositionUpdate
        return PositionUpdate(
            instrument_name=instrument,
            trade_action='PENDING',
            previous_quantity=0.0,
            new_quantity=0.0,
            realized_pnl=0.0,
            is_exercised=is_exercised,
            is_sod=is_sod
        )
        
        # # Get calculator and current position
        # calc = self._get_calculator(instrument)
        # 
        # # Get position before trade
        # previous_position, _ = calc._calculate_position_metrics(instrument)
        # 
        # # Track realized P&L before adding trade
        # realized_before = self.realized_pnl_totals.get(instrument, 0.0)
        # 
        # # Add trade to calculator
        # calc.add_trade(timestamp, instrument, quantity, price, trade_id)
        # 
        # # Calculate P&L with dummy market close (we'll update with real price later)
        # calc.add_market_close(instrument, timestamp.date(), price)
        # pnl_df = calc.calculate_daily_pnl()
        # 
        # # Get realized P&L from this trade
        # if not pnl_df.empty:
        #     daily_realized = pnl_df[pnl_df['symbol'] == instrument]['realized_pnl'].sum()
        #     self.realized_pnl_totals[instrument] = realized_before + daily_realized
        # else:
        #     daily_realized = 0.0
        # 
        # # Get new position
        # new_position, avg_cost = calc._calculate_position_metrics(instrument)
        # 
        # # Determine trade action
        # if previous_position == 0 and new_position != 0:
        #     trade_action = 'OPEN'
        # elif previous_position != 0 and new_position == 0:
        #     trade_action = 'CLOSE'
        # else:
        #     trade_action = 'AMEND'
        # 
        # # Update position in database
        # self._update_position_record(
        #     instrument=instrument,
        #     position_quantity=new_position,
        #     avg_cost=avg_cost,
        #     realized_pnl=daily_realized,
        #     trade_id=trade_id,
        #     timestamp=timestamp,
        #     is_exercised=is_exercised
        # )
        # 
        # return PositionUpdate(
        #     instrument_name=instrument,
        #     previous_quantity=previous_position,
        #     new_quantity=new_position,
        #     realized_pnl=daily_realized,
        #     trade_action=trade_action,
        #     is_exercised=is_exercised,
        #     is_sod=is_sod
        # )
    
    def _update_position_record(self, instrument: str, position_quantity: float, 
                               avg_cost: float, realized_pnl: float, trade_id: str,
                               timestamp: datetime, is_exercised: bool):
        """Update or delete position record in database."""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        if position_quantity == 0:
            # Delete position record when quantity reaches zero
            cursor.execute("DELETE FROM positions WHERE instrument_name = ?", (instrument,))
            logger.info(f"Closed position for {instrument}")
        else:
            # Extract option details if applicable
            is_option = self._is_option(instrument)
            strike, expiry = self._extract_option_details(instrument)
            
            # Get current total realized P&L
            total_realized = self.realized_pnl_totals.get(instrument, 0.0)
            
            # Update or insert position
            query = """
            INSERT OR REPLACE INTO positions (
                instrument_name, position_quantity, avg_cost, 
                total_realized_pnl, unrealized_pnl, last_trade_id,
                last_updated, is_option, option_strike, option_expiry,
                has_exercised_trades
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                instrument, position_quantity, avg_cost,
                total_realized, 0.0,  # Unrealized will be updated with market prices
                trade_id, timestamp,
                is_option, strike, expiry,
                is_exercised
            ))
            
            logger.info(f"Updated position: {instrument} qty={position_quantity} avg_cost={avg_cost} realized_pnl={total_realized}")
        
        conn.commit()
        conn.close()
    
    @monitor()
    def update_market_prices(self, price_timestamp: Optional[datetime] = None):
        """Update market prices and recalculate unrealized P&L for all positions.
        
        Args:
            price_timestamp: Timestamp for price selection (defaults to now)
        """
        if price_timestamp is None:
            price_timestamp = datetime.now(self.chicago_tz)
        
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        # Get all active positions
        cursor.execute("SELECT instrument_name, position_quantity, avg_cost FROM positions")
        positions = cursor.fetchall()
        
        for pos in positions:
            instrument = pos['instrument_name']
            quantity = pos['position_quantity']
            avg_cost = pos['avg_cost']
            
            # Get market price from storage
            try:
                # Get market price from database
                market_price, price_source = self.storage.get_market_price(
                    instrument, 
                    price_timestamp
                )
                
                if market_price is not None:
                    # Validate that market_price is numeric (not a string like "#N/A")
                    try:
                        market_price_float = float(market_price)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid market price '{market_price}' for {instrument}")
                        continue
                    
                    # Calculate unrealized P&L with proper rounding
                    # Round to 5 decimal places for futures (tick size 1/32 = 0.03125)
                    # Round to 4 decimal places for options (typical precision)
                    unrealized_pnl = (market_price_float - avg_cost) * quantity
                    
                    # Round based on instrument type
                    if instrument.startswith('O'):
                        # Options: 4 decimal places
                        unrealized_pnl = round(unrealized_pnl, 4)
                    else:
                        # Futures: 5 decimal places
                        unrealized_pnl = round(unrealized_pnl, 5)
                    
                    # Update position with new market price
                    update_query = """
                    UPDATE positions 
                    SET unrealized_pnl = ?, last_market_price = ?, last_updated = ?
                    WHERE instrument_name = ?
                    """
                    
                    cursor.execute(update_query, (
                        unrealized_pnl, market_price_float, price_timestamp, instrument
                    ))
                    
                    logger.info(f"Updated {instrument} market price={market_price} unrealized_pnl={unrealized_pnl}")
                else:
                    logger.warning(f"No market price found for {instrument}")
                    
            except Exception as e:
                logger.error(f"Error updating market price for {instrument}: {e}")
        
        conn.commit()
        conn.close()
    
    @monitor()
    def take_snapshot(self, snapshot_type: str, snapshot_timestamp: Optional[datetime] = None):
        """Take a snapshot of all positions.
        
        Args:
            snapshot_type: 'SOD' (5pm CDT) or 'EOD' (4pm CDT)
            snapshot_timestamp: Override timestamp (defaults to appropriate time)
        """
        if snapshot_timestamp is None:
            now = datetime.now(self.chicago_tz)
            
            if snapshot_type == 'SOD':
                # SOD is at 5pm CDT
                snapshot_timestamp = now.replace(hour=17, minute=0, second=0, microsecond=0)
            elif snapshot_type == 'EOD':
                # EOD is at 4pm CDT
                snapshot_timestamp = now.replace(hour=16, minute=0, second=0, microsecond=0)
            else:
                raise ValueError(f"Invalid snapshot type: {snapshot_type}")
        
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        # Get all current positions
        cursor.execute("""
            SELECT instrument_name, position_quantity, avg_cost, 
                   total_realized_pnl, unrealized_pnl, last_market_price
            FROM positions
        """)
        
        positions = cursor.fetchall()
        
        # Insert snapshots
        for pos in positions:
            insert_query = """
            INSERT OR REPLACE INTO position_snapshots (
                snapshot_type, snapshot_timestamp, instrument_name,
                position_quantity, avg_cost, total_realized_pnl,
                unrealized_pnl, market_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, (
                snapshot_type, snapshot_timestamp, pos['instrument_name'],
                pos['position_quantity'], pos['avg_cost'], 
                pos['total_realized_pnl'], pos['unrealized_pnl'],
                pos['last_market_price']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Took {snapshot_type} snapshot at {snapshot_timestamp} for {len(positions)} positions")
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions."""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM positions 
            ORDER BY instrument_name
        """)
        
        positions = []
        for row in cursor.fetchall():
            positions.append(dict(row))
        
        conn.close()
        return positions
    
    def get_position_by_instrument(self, instrument: str) -> Optional[Dict[str, Any]]:
        """Get position for a specific instrument."""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM positions 
            WHERE instrument_name = ?
        """, (instrument,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None 