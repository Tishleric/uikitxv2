"""
Settlement-Aware P&L Calculator

Implements P&L calculations that properly handle CME settlement boundaries at 2pm CDT.
Splits P&L into components: entry-to-settle, settle-to-settle, settle-to-exit.
"""

from datetime import datetime, date, time, timedelta
from typing import Dict, List, Tuple, Optional
import pytz
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PnLComponent:
    """Represents a single P&L component across a time period."""
    period_type: str  # 'entry_to_settle', 'settle_to_settle', 'settle_to_exit', 'intraday'
    start_time: datetime
    end_time: datetime
    start_price: float
    end_price: float
    pnl_amount: float
    start_settlement_key: Optional[str] = None  # YYYYMMDD_HHMM format
    end_settlement_key: Optional[str] = None    # YYYYMMDD_HHMM format
    
    def __str__(self) -> str:
        return f"{self.period_type}: ${self.pnl_amount:,.2f}"


class SettlementPnLCalculator:
    """
    Calculate P&L with settlement boundary awareness.
    
    Handles positions that span multiple settlement periods,
    breaking them into appropriate components.
    """
    
    SETTLEMENT_HOUR = 14  # 2pm
    CHICAGO_TZ = pytz.timezone('America/Chicago')
    
    def __init__(self, multiplier: float = 1000.0):
        """
        Initialize calculator.
        
        Args:
            multiplier: Contract multiplier (default 1000 for bond futures)
        """
        self.multiplier = multiplier
    
    def _generate_settlement_key(self, dt: datetime) -> str:
        """
        Generate settlement key in YYYYMMDD_HHMM format.
        
        Args:
            dt: Datetime to generate key for (should be settlement time)
            
        Returns:
            Settlement key string
        """
        chicago_dt = self._to_chicago(dt) if dt else None
        if not chicago_dt:
            return ""
        
        # For settlement times, always use 14:00 (2pm)
        if chicago_dt.hour == self.SETTLEMENT_HOUR and chicago_dt.minute == 0:
            return chicago_dt.strftime("%Y%m%d_1400")
        
        # For other times, use actual time (useful for debugging)
        return chicago_dt.strftime("%Y%m%d_%H%M")
    
    def calculate_lot_pnl(self,
                         entry_time: datetime,
                         exit_time: Optional[datetime],
                         entry_price: float,
                         exit_price: Optional[float],
                         quantity: float,
                         current_price: float,
                         settlement_prices: Dict[date, float]) -> Dict:
        """
        Calculate P&L for a single lot with settlement awareness.
        
        Args:
            entry_time: When position was opened
            exit_time: When position was closed (None if still open)
            entry_price: Entry price
            exit_price: Exit price (None if still open)
            quantity: Lot quantity (positive for long, negative for short)
            current_price: Current market price
            settlement_prices: Map of settlement dates to prices
            
        Returns:
            Dict containing:
                - total_pnl: Total P&L amount
                - components: List of PnLComponent objects
                - is_realized: Whether P&L is realized (position closed)
        """
        # Ensure times are in Chicago timezone
        entry_time = self._to_chicago(entry_time)
        exit_time = self._to_chicago(exit_time) if exit_time else None
        
        # For closed positions
        if exit_time and exit_price is not None:
            components = self._calculate_closed_position_components(
                entry_time, exit_time, entry_price, exit_price, 
                quantity, settlement_prices
            )
            total_pnl = sum(c.pnl_amount for c in components)
            return {
                'total_pnl': total_pnl,
                'components': components,
                'is_realized': True
            }
        
        # For open positions - calculate to current time
        current_time = datetime.now(self.CHICAGO_TZ)
        components = self._calculate_closed_position_components(
            entry_time, current_time, entry_price, current_price,
            quantity, settlement_prices
        )
        total_pnl = sum(c.pnl_amount for c in components)
        return {
            'total_pnl': total_pnl,
            'components': components,
            'is_realized': False
        }
    
    def _calculate_closed_position_components(self,
                                            entry_time: datetime,
                                            exit_time: datetime,
                                            entry_price: float,
                                            exit_price: float,
                                            quantity: float,
                                            settlement_prices: Dict[date, float]) -> List[PnLComponent]:
        """
        Break down P&L into components based on settlement boundaries.
        
        Handles three cases:
        1. Intraday: No settlement crossed
        2. Same-day cross: Entry and exit on same day but cross 2pm
        3. Multi-day: Position held across multiple settlements
        """
        components = []
        
        # Get all settlement times between entry and exit
        settlement_times = self._get_settlement_times_between(entry_time, exit_time)
        
        if not settlement_times:
            # Case 1: Intraday position, no settlements crossed
            pnl = quantity * (exit_price - entry_price) * self.multiplier
            components.append(PnLComponent(
                period_type='intraday',
                start_time=entry_time,
                end_time=exit_time,
                start_price=entry_price,
                end_price=exit_price,
                pnl_amount=pnl,
                start_settlement_key=self._generate_settlement_key(entry_time),
                end_settlement_key=self._generate_settlement_key(exit_time)
            ))
            return components
        
        # Cases 2 & 3: Position crosses one or more settlements
        current_time = entry_time
        current_price = entry_price
        
        # Entry to first settlement
        first_settle_time = settlement_times[0]
        first_settle_date = first_settle_time.date()
        first_settle_price = settlement_prices.get(first_settle_date)
        
        if first_settle_price is not None:
            pnl = quantity * (first_settle_price - current_price) * self.multiplier
            components.append(PnLComponent(
                period_type='entry_to_settle',
                start_time=current_time,
                end_time=first_settle_time,
                start_price=current_price,
                end_price=first_settle_price,
                pnl_amount=pnl,
                start_settlement_key=self._generate_settlement_key(current_time),
                end_settlement_key=self._generate_settlement_key(first_settle_time)
            ))
            current_time = first_settle_time
            current_price = first_settle_price
        
        # Settlement to settlement (for multi-day positions)
        for i in range(1, len(settlement_times)):
            prev_settle_time = settlement_times[i-1]
            curr_settle_time = settlement_times[i]
            curr_settle_date = curr_settle_time.date()
            curr_settle_price = settlement_prices.get(curr_settle_date)
            
            if curr_settle_price is not None and current_price is not None:
                pnl = quantity * (curr_settle_price - current_price) * self.multiplier
                components.append(PnLComponent(
                    period_type='settle_to_settle',
                    start_time=prev_settle_time,
                    end_time=curr_settle_time,
                    start_price=current_price,
                    end_price=curr_settle_price,
                    pnl_amount=pnl,
                    start_settlement_key=self._generate_settlement_key(prev_settle_time),
                    end_settlement_key=self._generate_settlement_key(curr_settle_time)
                ))
                current_price = curr_settle_price
            current_time = curr_settle_time
        
        # Last settlement to exit
        if current_price is not None:
            pnl = quantity * (exit_price - current_price) * self.multiplier
            components.append(PnLComponent(
                period_type='settle_to_exit',
                start_time=current_time,
                end_time=exit_time,
                start_price=current_price,
                end_price=exit_price,
                pnl_amount=pnl,
                start_settlement_key=self._generate_settlement_key(current_time),
                end_settlement_key=self._generate_settlement_key(exit_time)
            ))
        
        return components
    
    def _get_settlement_times_between(self, 
                                    start_time: datetime, 
                                    end_time: datetime) -> List[datetime]:
        """
        Get all 2pm settlement times between start and end.
        
        Returns list of settlement datetimes in chronological order.
        """
        settlements = []
        
        # Start from the first potential settlement
        current_date = start_time.date()
        
        # If start is before 2pm on its date, that day's 2pm is a potential settlement
        if start_time.hour < self.SETTLEMENT_HOUR:
            first_potential = self.CHICAGO_TZ.localize(
                datetime.combine(current_date, time(self.SETTLEMENT_HOUR, 0))
            )
            if start_time < first_potential <= end_time:
                settlements.append(first_potential)
        
        # Check subsequent days
        current_date += timedelta(days=1)
        while current_date <= end_time.date():
            settle_time = self.CHICAGO_TZ.localize(
                datetime.combine(current_date, time(self.SETTLEMENT_HOUR, 0))
            )
            if settle_time <= end_time:
                settlements.append(settle_time)
            current_date += timedelta(days=1)
        
        return settlements
    
    def _to_chicago(self, dt: Optional[datetime]) -> Optional[datetime]:
        """Convert datetime to Chicago timezone."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return self.CHICAGO_TZ.localize(dt)
        return dt.astimezone(self.CHICAGO_TZ)
    
    def aggregate_components_by_type(self, 
                                   components: List[PnLComponent]) -> Dict[str, float]:
        """
        Aggregate P&L components by type.
        
        Useful for reporting total P&L by component type across multiple lots.
        """
        aggregated = {}
        for component in components:
            if component.period_type not in aggregated:
                aggregated[component.period_type] = 0
            aggregated[component.period_type] += component.pnl_amount
        return aggregated 