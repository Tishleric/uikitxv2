"""P&L Calculator implementation using FIFO methodology.

This module implements the main P&L calculation engine that tracks positions,
calculates realized and unrealized profits/losses, and provides daily P&L
breakdowns.
"""

import logging
from collections import defaultdict, deque
from datetime import date, datetime
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd

from .models import Trade, Lot

# Set up module logger
logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    # Fallback if monitoring is not available
    def monitor():
        def decorator(func):
            return func
        return decorator


class PnLCalculator:
    """Calculate daily realized and unrealized P&L using FIFO methodology.
    
    This calculator tracks positions using First-In-First-Out (FIFO) logic,
    supports both long and short positions, and provides comprehensive P&L
    analysis including daily breakdowns.
    
    Attributes:
        trades: List of all trades
        market_closes: Dictionary of market closing prices by (symbol, date)
        positions: Dictionary mapping symbols to deques of Lots
        daily_pnl: Dictionary tracking daily P&L metrics by (symbol, date)
    """
    
    def __init__(self):
        """Initialize a new P&L calculator instance."""
        self.trades: List[Trade] = []
        self.market_closes: Dict[Tuple[str, date], float] = {}
        self.positions: Dict[str, deque] = defaultdict(lambda: deque())
        self.daily_pnl: Dict[Tuple[str, date], Dict[str, float]] = defaultdict(lambda: {
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'position': 0.0,
            'avg_cost': 0.0,
            'market_close': 0.0
        })
        
    @monitor()
    def add_trade(self, timestamp: datetime, symbol: str, quantity: float, 
                  price: float, trade_id: Optional[str] = None) -> None:
        """Add a trade to the calculator.
        
        Args:
            timestamp: When the trade occurred
            symbol: Trading symbol
            quantity: Trade quantity (positive for buy, negative for sell)
            price: Execution price per unit
            trade_id: Optional unique identifier for the trade
            
        Raises:
            ValueError: If trade data is invalid
        """
        try:
            trade = Trade(timestamp, symbol, quantity, price, trade_id)
            self.trades.append(trade)
            logger.info(f"Added trade: {symbol} {quantity} @ {price} on {timestamp}")
        except ValueError as e:
            logger.error(f"Invalid trade data: {e}")
            raise
            
    @monitor()
    def add_market_close(self, symbol: str, close_date: date, close_price: float) -> None:
        """Add market closing price for a symbol on a specific date.
        
        Args:
            symbol: Trading symbol
            close_date: Date of the closing price
            close_price: Market closing price
            
        Raises:
            ValueError: If price is negative
        """
        if close_price < 0:
            raise ValueError(f"Market close price cannot be negative: {close_price}")
            
        self.market_closes[(symbol, close_date)] = close_price
        logger.debug(f"Added market close: {symbol} @ {close_price} on {close_date}")
        
    @monitor()
    def load_trades_from_csv(self, csv_path: str) -> None:
        """Load trades from a CSV file and add them to the calculator.
        
        Expected CSV columns: tradeId, instrumentName, marketTradeTime, buySell, quantity, price
        
        Args:
            csv_path: Path to the CSV file containing trades
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV is missing required columns or has invalid data
        """
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price']
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(f"CSV missing required columns: {missing_columns}")
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Parse timestamp
                    timestamp_str = str(row['marketTradeTime'])
                    timestamp = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    
                    # Convert quantity based on buySell
                    quantity = float(row['quantity'])
                    if row['buySell'] == 'S':
                        quantity = -quantity
                    elif row['buySell'] != 'B':
                        raise ValueError(f"Invalid buySell value: {row['buySell']} (expected 'B' or 'S')")
                    
                    # Add trade
                    self.add_trade(
                        timestamp=timestamp,
                        symbol=str(row['instrumentName']),
                        quantity=quantity,
                        price=float(row['price']),
                        trade_id=str(row['tradeId'])
                    )
                    
                except (ValueError, pd.errors.ParserError) as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    raise ValueError(f"Invalid data in row {idx}: {e}")
                    
            logger.info(f"Loaded {len(df)} trades from {csv_path}")
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.error(f"CSV file is empty: {csv_path}")
            raise ValueError(f"CSV file is empty: {csv_path}")
        
    def _process_buy(self, symbol: str, quantity: float, price: float, 
                     trade_date: date) -> float:
        """Process a buy trade (positive quantity) using FIFO.
        
        First covers any short positions, then adds remaining as long position.
        
        Args:
            symbol: Trading symbol
            quantity: Buy quantity (must be positive)
            price: Execution price
            trade_date: Date of the trade
            
        Returns:
            Realized P&L from covering shorts
        """
        realized_pnl = 0.0
        remaining_to_buy = quantity
        
        # First, cover any short positions (negative lots) using FIFO
        while remaining_to_buy > 0 and self.positions[symbol]:
            # Check if oldest position is short (negative quantity)
            oldest_lot = self.positions[symbol][0]
            
            if oldest_lot.quantity < 0:  # Short position to cover
                short_quantity = abs(oldest_lot.quantity)
                
                if short_quantity <= remaining_to_buy:
                    # Cover entire short position
                    # For shorts: P&L = (Short Price - Cover Price) * Quantity
                    lot_pnl = (oldest_lot.price - price) * short_quantity
                    realized_pnl += lot_pnl
                    remaining_to_buy -= short_quantity
                    self.positions[symbol].popleft()
                    logger.debug(f"Covered short: {short_quantity} @ {price}, P&L: {lot_pnl}")
                else:
                    # Partially cover short position
                    lot_pnl = (oldest_lot.price - price) * remaining_to_buy
                    realized_pnl += lot_pnl
                    oldest_lot.quantity += remaining_to_buy  # Reduce short position
                    remaining_to_buy = 0
                    logger.debug(f"Partially covered short: {remaining_to_buy} @ {price}, P&L: {lot_pnl}")
            else:
                # No more short positions to cover
                break
                
        # If there's remaining quantity after covering shorts, add as new long position
        if remaining_to_buy > 0:
            lot = Lot(remaining_to_buy, price, trade_date)
            self.positions[symbol].append(lot)
            logger.debug(f"Added long position: {remaining_to_buy} @ {price}")
            
        return realized_pnl
        
    def _process_sell(self, symbol: str, quantity: float, price: float, 
                      trade_date: date) -> float:
        """Process a sell trade (negative quantity) using FIFO.
        
        First sells long positions, then creates short positions if needed.
        
        Args:
            symbol: Trading symbol
            quantity: Sell quantity (must be negative)
            price: Execution price
            trade_date: Date of the trade
            
        Returns:
            Realized P&L from selling longs
        """
        realized_pnl = 0.0
        remaining_to_sell = abs(quantity)
        
        while remaining_to_sell > 0 and self.positions[symbol]:
            # Get oldest lot (FIFO)
            oldest_lot = self.positions[symbol][0]
            
            if oldest_lot.quantity > 0:  # Long position
                if oldest_lot.quantity <= remaining_to_sell:
                    # Sell entire lot
                    lot_pnl = (price - oldest_lot.price) * oldest_lot.quantity
                    realized_pnl += lot_pnl
                    remaining_to_sell -= oldest_lot.quantity
                    self.positions[symbol].popleft()
                    logger.debug(f"Sold lot: {oldest_lot.quantity} @ {price}, P&L: {lot_pnl}")
                else:
                    # Partial sell of lot
                    lot_pnl = (price - oldest_lot.price) * remaining_to_sell
                    realized_pnl += lot_pnl
                    oldest_lot.quantity -= remaining_to_sell
                    remaining_to_sell = 0
                    logger.debug(f"Partially sold lot: {remaining_to_sell} @ {price}, P&L: {lot_pnl}")
            else:
                # Hit a short position, stop selling longs
                break
                
        # If remaining quantity after selling all longs, create short position
        if remaining_to_sell > 0:
            short_lot = Lot(-remaining_to_sell, price, trade_date)
            self.positions[symbol].append(short_lot)
            logger.debug(f"Created short position: {remaining_to_sell} @ {price}")
            
        return realized_pnl
        
    def _calculate_position_metrics(self, symbol: str) -> Tuple[float, float]:
        """Calculate current position size and average cost.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (total_position, average_cost)
        """
        total_quantity = 0.0
        total_cost = 0.0
        
        for lot in self.positions[symbol]:
            total_quantity += lot.quantity
            total_cost += lot.quantity * lot.price
            
        avg_cost = total_cost / total_quantity if total_quantity != 0 else 0.0
        return total_quantity, avg_cost
        
    def _calculate_unrealized_pnl(self, symbol: str, market_price: float) -> float:
        """Calculate unrealized P&L for current position.
        
        Args:
            symbol: Trading symbol
            market_price: Current market price
            
        Returns:
            Unrealized P&L amount
        """
        position, avg_cost = self._calculate_position_metrics(symbol)
        if position == 0:
            return 0.0
        return (market_price - avg_cost) * position
        
    @monitor()
    def calculate_daily_pnl(self) -> pd.DataFrame:
        """Calculate daily P&L for all symbols.
        
        Processes all trades and calculates realized P&L from trades,
        unrealized P&L from market movements, and total daily P&L.
        
        Returns:
            DataFrame with daily P&L breakdown by symbol and date
        """
        if not self.trades:
            logger.warning("No trades to process")
            return pd.DataFrame()
            
        # Reset positions for fresh calculation
        self.positions = defaultdict(lambda: deque())
        
        # Sort trades by timestamp
        self.trades.sort(key=lambda x: x.timestamp)
        
        # Get all unique dates and symbols
        dates = sorted(set(trade.timestamp.date() for trade in self.trades))
        symbols = set(trade.symbol for trade in self.trades)
        
        # Add market close dates to ensure we have all trading days
        for (symbol, close_date), _ in self.market_closes.items():
            if close_date not in dates:
                dates.append(close_date)
        dates = sorted(set(dates))
        
        results = []
        
        # Track previous day's unrealized P&L for change calculation
        prev_unrealized: Dict[str, float] = defaultdict(float)
        
        for current_date in dates:
            # Process all trades for current date
            daily_realized: Dict[str, float] = defaultdict(float)
            
            for trade in self.trades:
                if trade.timestamp.date() == current_date:
                    if trade.quantity > 0:  # Buy
                        realized_pnl = self._process_buy(
                            trade.symbol, trade.quantity, trade.price, current_date
                        )
                    else:  # Sell
                        realized_pnl = self._process_sell(
                            trade.symbol, trade.quantity, trade.price, current_date
                        )
                    
                    daily_realized[trade.symbol] += realized_pnl
            
            # Calculate unrealized P&L for each symbol at day end
            for symbol in symbols:
                market_close = self.market_closes.get((symbol, current_date))
                if market_close is None:
                    continue
                    
                position, avg_cost = self._calculate_position_metrics(symbol)
                unrealized_pnl = self._calculate_unrealized_pnl(symbol, market_close)
                
                # Change in unrealized P&L
                unrealized_change = unrealized_pnl - prev_unrealized[symbol]
                
                # Total daily P&L = Realized + Change in Unrealized
                total_daily_pnl = daily_realized[symbol] + unrealized_change
                
                results.append({
                    'date': current_date,
                    'symbol': symbol,
                    'position': position,
                    'avg_cost': avg_cost,
                    'market_close': market_close,
                    'realized_pnl': daily_realized[symbol],
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_change': unrealized_change,
                    'total_daily_pnl': total_daily_pnl
                })
                
                # Update previous unrealized for next day
                prev_unrealized[symbol] = unrealized_pnl
                
        df = pd.DataFrame(results)
        logger.info(f"Calculated daily P&L for {len(df)} symbol-date combinations")
        return df
        
    @monitor()
    def get_position_summary(self, as_of_date: Optional[date] = None) -> pd.DataFrame:
        """Get current position summary as of a specific date.
        
        Args:
            as_of_date: Date to calculate positions for (defaults to latest trade date)
            
        Returns:
            DataFrame with position details for each symbol
        """
        if as_of_date is None:
            as_of_date = max(trade.timestamp.date() for trade in self.trades) if self.trades else date.today()
            
        # Create a temporary calculator to process trades up to as_of_date
        temp_calc = PnLCalculator()
        temp_calc.market_closes = self.market_closes.copy()
        
        # Process trades up to as_of_date
        for trade in self.trades:
            if trade.timestamp.date() <= as_of_date:
                temp_calc.trades.append(trade)
                
        # Calculate positions
        temp_calc.calculate_daily_pnl()  # This populates positions
        
        symbols = set(trade.symbol for trade in temp_calc.trades)
        results = []
        
        for symbol in symbols:
            position, avg_cost = temp_calc._calculate_position_metrics(symbol)
            
            # Skip if no position
            if position == 0:
                continue
                
            market_close = temp_calc.market_closes.get((symbol, as_of_date))
            
            if market_close:
                unrealized_pnl = temp_calc._calculate_unrealized_pnl(symbol, market_close)
                market_value = position * market_close
            else:
                unrealized_pnl = 0
                market_value = 0
                
            results.append({
                'symbol': symbol,
                'position': position,
                'avg_cost': avg_cost,
                'market_price': market_close or 0,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl
            })
            
        df = pd.DataFrame(results)
        logger.info(f"Generated position summary for {len(df)} symbols as of {as_of_date}")
        return df 