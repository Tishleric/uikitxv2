#!/usr/bin/env python3
"""
Mock test environment for FRG Monitor position display issue.
Tests why closed positions disappear from the dashboard.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockTradesDB:
    """In-memory SQLite database with production schema"""
    
    def __init__(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._create_schema()
        logger.info("Created in-memory database with production schema")
        
    def _create_schema(self):
        """Create all required tables matching production"""
        cursor = self.conn.cursor()
        
        # trades_fifo table
        cursor.execute("""
        CREATE TABLE trades_fifo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            quantity REAL,
            price REAL,
            buySell TEXT,
            realizedPnL REAL DEFAULT 0,
            account TEXT DEFAULT 'TEST'
        )
        """)
        
        # trades_lifo table (same structure)
        cursor.execute("""
        CREATE TABLE trades_lifo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            quantity REAL,
            price REAL,
            buySell TEXT,
            realizedPnL REAL DEFAULT 0,
            account TEXT DEFAULT 'TEST'
        )
        """)
        
        # realized_fifo table
        cursor.execute("""
        CREATE TABLE realized_fifo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            quantity REAL,
            realizedPnL REAL,
            buy_id INTEGER,
            sell_id INTEGER
        )
        """)
        
        # realized_lifo table
        cursor.execute("""
        CREATE TABLE realized_lifo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            quantity REAL,
            realizedPnL REAL,
            buy_id INTEGER,
            sell_id INTEGER
        )
        """)
        
        # positions table
        cursor.execute("""
        CREATE TABLE positions (
            symbol TEXT PRIMARY KEY,
            open_position REAL DEFAULT 0,
            closed_position REAL DEFAULT 0,
            delta_y REAL,
            gamma_y REAL,
            speed_y REAL,
            theta REAL,
            vega REAL,
            fifo_realized_pnl REAL DEFAULT 0,
            fifo_unrealized_pnl REAL DEFAULT 0,
            lifo_realized_pnl REAL DEFAULT 0,
            lifo_unrealized_pnl REAL DEFAULT 0,
            fifo_unrealized_pnl_close REAL DEFAULT 0,
            lifo_unrealized_pnl_close REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_trade_update TIMESTAMP,
            last_greek_update TIMESTAMP,
            has_greeks BOOLEAN DEFAULT 0,
            instrument_type TEXT
        )
        """)
        
        # pricing table
        cursor.execute("""
        CREATE TABLE pricing (
            symbol TEXT,
            price_type TEXT,
            price REAL,
            timestamp TEXT,
            PRIMARY KEY (symbol, price_type)
        )
        """)
        
        self.conn.commit()
        logger.info("Schema created successfully")
        
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and return results"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
        
    def print_table(self, table_name: str, where_clause: str = ""):
        """Print contents of a table for debugging"""
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        rows = self.execute_query(query)
        if not rows:
            print(f"\n{table_name}: (empty)")
            return
            
        print(f"\n{table_name}:")
        if rows:
            # Print column headers
            columns = rows[0].keys()
            print(" | ".join(columns))
            print("-" * (len(" | ".join(columns))))
            
            # Print rows
            for row in rows:
                values = [str(row[col]) for col in columns]
                print(" | ".join(values))


class TimeController:
    """Control system time for testing date boundaries"""
    
    def __init__(self, start_time: str = "2025-01-29 09:00:00"):
        self.current_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        self.chicago_tz = pytz.timezone('America/Chicago')
        logger.info(f"Time controller initialized at {self.current_time}")
        
    def set_time(self, new_time_str: str):
        """Jump to specific time"""
        self.current_time = datetime.strptime(new_time_str, "%Y-%m-%d %H:%M:%S")
        logger.info(f"Time set to {self.current_time}")
        
    def advance_hours(self, hours: float):
        """Move time forward by hours"""
        self.current_time += timedelta(hours=hours)
        logger.info(f"Time advanced to {self.current_time}")
        
    def get_now_sql(self) -> str:
        """Return SQL that mocks 'now' for queries"""
        return f"'{self.current_time.strftime('%Y-%m-%d %H:%M:%S')}'"
        
    def get_timestamp(self) -> str:
        """Get current timestamp in millisecond format"""
        return self.current_time.strftime('%Y-%m-%d %H:%M:%S.000')


class MockTradeProcessor:
    """Simulate FIFO/LIFO matching logic"""
    
    def __init__(self, db: MockTradesDB, time_controller: TimeController):
        self.db = db
        self.time = time_controller
        self.next_trade_id = 1
        
    def insert_trade(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """Process a trade through FIFO matching"""
        timestamp = self.time.get_timestamp()
        buy_sell = 'B' if side == 'BUY' else 'S'
        
        logger.info(f"Processing trade: {side} {quantity} {symbol} @ {price} at {timestamp}")
        
        cursor = self.db.conn.cursor()
        
        # Insert into both FIFO and LIFO tables
        for table in ['trades_fifo', 'trades_lifo']:
            cursor.execute(f"""
            INSERT INTO {table} (timestamp, symbol, quantity, price, buySell)
            VALUES (?, ?, ?, ?, ?)
            """, (timestamp, symbol, quantity, price, buy_sell))
        
        self.db.conn.commit()
        
        # Run FIFO matching if this is a closing trade
        self._run_fifo_matching(symbol)
        
        # Update pricing
        cursor.execute("""
        INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
        VALUES (?, 'now', ?, ?)
        """, (symbol, price, timestamp))
        
        self.db.conn.commit()
        
        return {
            'symbol': symbol,
            'action': 'trade_processed',
            'timestamp': timestamp
        }
        
    def _run_fifo_matching(self, symbol: str):
        """Simple FIFO matching logic"""
        cursor = self.db.conn.cursor()
        
        # Get all trades for symbol in FIFO order
        trades = cursor.execute("""
        SELECT id, timestamp, quantity, price, buySell, realizedPnL
        FROM trades_fifo
        WHERE symbol = ? AND quantity > 0
        ORDER BY timestamp, id
        """, (symbol,)).fetchall()
        
        buys = [t for t in trades if t['buySell'] == 'B']
        sells = [t for t in trades if t['buySell'] == 'S']
        
        # Match buys and sells
        for sell in sells:
            sell_qty_remaining = sell['quantity']
            sell_price = sell['price']
            
            for buy in buys:
                if sell_qty_remaining <= 0:
                    break
                    
                if buy['quantity'] <= 0:
                    continue
                    
                # Calculate match quantity
                match_qty = min(buy['quantity'], sell_qty_remaining)
                
                if match_qty > 0:
                    # Calculate P&L
                    pnl = (sell_price - buy['price']) * match_qty * 1000  # Assuming multiplier of 1000
                    
                    # Update quantities
                    new_buy_qty = buy['quantity'] - match_qty
                    new_sell_qty = sell['quantity'] - match_qty
                    
                    # Update trades_fifo
                    cursor.execute("""
                    UPDATE trades_fifo SET quantity = ? WHERE id = ?
                    """, (new_buy_qty, buy['id']))
                    
                    cursor.execute("""
                    UPDATE trades_fifo SET quantity = ? WHERE id = ?
                    """, (new_sell_qty, sell['id']))
                    
                    # Insert into realized_fifo
                    cursor.execute("""
                    INSERT INTO realized_fifo (timestamp, symbol, quantity, realizedPnL, buy_id, sell_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (sell['timestamp'], symbol, match_qty, pnl, buy['id'], sell['id']))
                    
                    sell_qty_remaining -= match_qty
                    
                    logger.info(f"Matched {match_qty} @ P&L: ${pnl:.2f}")
        
        self.db.conn.commit()


class MockPositionsAggregator:
    """Simulate PositionsAggregator behavior with exact production SQL"""
    
    def __init__(self, db: MockTradesDB, time_controller: TimeController):
        self.db = db
        self.time = time_controller
        
    def run_aggregation(self):
        """Execute the exact SQL from positions_aggregator.py"""
        logger.info(f"Running aggregator at {self.time.current_time}")
        
        # Build the query with mocked time
        query = f"""
        WITH all_symbols AS (
            SELECT DISTINCT symbol FROM trades_fifo
            UNION
            SELECT DISTINCT symbol FROM trades_lifo
        ),
        open_positions AS (
            SELECT 
                symbol,
                SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as open_position
            FROM trades_fifo
            WHERE quantity > 0
            GROUP BY symbol
        ),
        closed_positions_fifo AS (
            SELECT 
                symbol,
                SUM(ABS(quantity)) as closed_position,
                SUM(realizedPnL) as fifo_realized_pnl
            FROM realized_fifo
            WHERE 
                DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE({self.time.get_now_sql()}, 'localtime')
            GROUP BY symbol
        ),
        closed_positions_lifo AS (
            SELECT 
                symbol,
                SUM(realizedPnL) as lifo_realized_pnl
            FROM realized_lifo
            WHERE 
                DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE({self.time.get_now_sql()}, 'localtime')
            GROUP BY symbol
        )
        SELECT 
            s.symbol,
            COALESCE(o.open_position, 0) as open_position,
            COALESCE(cf.closed_position, 0) as closed_position,
            COALESCE(cf.fifo_realized_pnl, 0) as fifo_realized_pnl,
            COALESCE(cl.lifo_realized_pnl, 0) as lifo_realized_pnl
        FROM all_symbols s
        LEFT JOIN open_positions o ON s.symbol = o.symbol
        LEFT JOIN closed_positions_fifo cf ON s.symbol = cf.symbol
        LEFT JOIN closed_positions_lifo cl ON s.symbol = cl.symbol
        """
        
        results = self.db.execute_query(query)
        
        # Update positions table
        cursor = self.db.conn.cursor()
        
        for row in results:
            cursor.execute("""
            INSERT OR REPLACE INTO positions (
                symbol, open_position, closed_position,
                fifo_realized_pnl, lifo_realized_pnl,
                last_updated, instrument_type
            ) VALUES (?, ?, ?, ?, ?, ?, 'FUTURE')
            """, (
                row['symbol'], 
                row['open_position'], 
                row['closed_position'],
                row['fifo_realized_pnl'], 
                row['lifo_realized_pnl'],
                self.time.get_timestamp()
            ))
            
        self.db.conn.commit()
        
        logger.info(f"Aggregator processed {len(results)} symbols")
        return results


class MockFRGMonitor:
    """Simulate dashboard query logic"""
    
    def __init__(self, db: MockTradesDB, time_controller: TimeController):
        self.db = db
        self.time = time_controller
        
    def get_display_rows(self) -> List[Dict]:
        """Run exact query from app.py"""
        query = """
        SELECT 
            p.symbol,
            p.instrument_type,
            p.open_position,
            p.closed_position,
            p.fifo_realized_pnl,
            p.fifo_unrealized_pnl,
            (p.fifo_realized_pnl + p.fifo_unrealized_pnl) as pnl_live
        FROM positions p
        WHERE p.open_position != 0 OR p.closed_position != 0
        ORDER BY p.symbol
        """
        
        rows = self.db.execute_query(query)
        return [dict(row) for row in rows]


class PositionDisplayTest:
    """Main test runner"""
    
    def __init__(self):
        self.time = TimeController("2025-01-29 09:00:00")
        self.db = MockTradesDB()
        self.processor = MockTradeProcessor(self.db, self.time)
        self.aggregator = MockPositionsAggregator(self.db, self.time)
        self.dashboard = MockFRGMonitor(self.db, self.time)
        
    def run_test_case_1_same_day(self):
        """Test Case 1: Same-day open/close"""
        print("\n" + "="*60)
        print("TEST CASE 1: Same Day Open/Close")
        print("="*60)
        
        # 10am: Open position
        self.time.set_time("2025-01-30 10:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "BUY", 5, 109.50)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After BUY at {self.time.current_time} ---")
        self._print_state()
        
        # 2pm: Close position  
        self.time.set_time("2025-01-30 14:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "SELL", 5, 109.75)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After SELL at {self.time.current_time} ---")
        self._print_state()
        
        # Test at 5:01pm (next trading day)
        self.time.set_time("2025-01-30 17:01:00")
        self.aggregator.run_aggregation()
        
        print(f"\n--- After 5pm at {self.time.current_time} ---")
        self._print_state()
        
    def run_test_case_2_cross_day(self):
        """Test Case 2: Cross-day close"""
        print("\n" + "="*60)
        print("TEST CASE 2: Cross Day Close")
        print("="*60)
        
        # Reset database for clean test
        self.db = MockTradesDB()
        self.processor = MockTradeProcessor(self.db, self.time)
        self.aggregator = MockPositionsAggregator(self.db, self.time)
        self.dashboard = MockFRGMonitor(self.db, self.time)
        
        # Yesterday 2pm: Open position
        self.time.set_time("2025-01-29 14:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "BUY", 5, 109.50)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After BUY at {self.time.current_time} (yesterday) ---")
        self._print_state()
        
        # Simulate moving to next day - run aggregator at 9am today
        self.time.set_time("2025-01-30 09:00:00")
        self.aggregator.run_aggregation()
        
        print(f"\n--- Next morning at {self.time.current_time} (before close) ---")
        self._print_state()
        
        # Today 10am: Close position
        self.time.set_time("2025-01-30 10:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "SELL", 5, 109.75)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After SELL at {self.time.current_time} (today) ---")
        self._print_state()
        
    def run_test_case_3_next_day_view(self):
        """Test Case 3: View position the next day after closing"""
        print("\n" + "="*60)
        print("TEST CASE 3: Next Day View After Close")
        print("="*60)
        
        # Reset database
        self.db = MockTradesDB()
        self.processor = MockTradeProcessor(self.db, self.time)
        self.aggregator = MockPositionsAggregator(self.db, self.time)
        self.dashboard = MockFRGMonitor(self.db, self.time)
        
        # Day 1 at 10am: Open position
        self.time.set_time("2025-01-30 10:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "BUY", 5, 109.50)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After BUY at {self.time.current_time} ---")
        self._print_state()
        
        # Day 1 at 2pm: Close position
        self.time.set_time("2025-01-30 14:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "SELL", 5, 109.75)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After SELL at {self.time.current_time} ---")
        self._print_state()
        
        # Day 2 at 9am: Check if position still shows
        self.time.set_time("2025-01-31 09:00:00")
        self.aggregator.run_aggregation()
        
        print(f"\n--- Next day at {self.time.current_time} ---")
        self._print_state()
        
        print("\nDEBUG: Checking what aggregator sees for closed positions:")
        # Run the closed positions query manually to debug
        query = f"""
        SELECT 
            symbol,
            SUM(ABS(quantity)) as closed_position,
            SUM(realizedPnL) as fifo_realized_pnl,
            DATE(timestamp, 
                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                      THEN '+1 day' 
                      ELSE '+0 day' 
                 END) as trading_day,
            DATE({self.time.get_now_sql()}, 'localtime') as current_trading_day
        FROM realized_fifo
        WHERE symbol = 'ZNH5 Comdty'
        GROUP BY symbol
        """
        debug_rows = self.db.execute_query(query)
        for row in debug_rows:
            print(f"  Symbol: {row['symbol']}, closed: {row['closed_position']}, "
                  f"trading_day: {row['trading_day']}, current: {row['current_trading_day']}")
                  
    def run_test_case_4_5pm_cutoff(self):
        """Test Case 4: Test 5pm cutoff behavior"""
        print("\n" + "="*60)
        print("TEST CASE 4: 5pm Cutoff Edge Case")
        print("="*60)
        
        # Reset database
        self.db = MockTradesDB()
        self.processor = MockTradeProcessor(self.db, self.time)
        self.aggregator = MockPositionsAggregator(self.db, self.time)
        self.dashboard = MockFRGMonitor(self.db, self.time)
        
        # Open at 10am
        self.time.set_time("2025-01-30 10:00:00")
        self.processor.insert_trade("ZNH5 Comdty", "BUY", 5, 109.50)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After BUY at {self.time.current_time} ---")
        positions = self.db.execute_query("SELECT * FROM positions WHERE symbol = 'ZNH5 Comdty'")
        print(f"Position exists: {len(positions) > 0}")
        
        # Close at 4:59pm (before cutoff)
        self.time.set_time("2025-01-30 16:59:00")
        self.processor.insert_trade("ZNH5 Comdty", "SELL", 5, 109.75)
        self.aggregator.run_aggregation()
        
        print(f"\n--- After SELL at 4:59pm ---")
        dashboard_rows = self.dashboard.get_display_rows()
        print(f"Dashboard shows {len(dashboard_rows)} rows")
        if dashboard_rows:
            row = dashboard_rows[0]
            print(f"  {row['symbol']}: open={row['open_position']}, closed={row['closed_position']}")
        
        # Check at 4:59pm (same moment)
        print(f"\nTime check at 4:59pm:")
        self._debug_aggregator_view()
        
        # Move to 5:01pm (after cutoff)
        self.time.set_time("2025-01-30 17:01:00")
        self.aggregator.run_aggregation()
        
        print(f"\n--- After moving to 5:01pm (after cutoff) ---")
        dashboard_rows = self.dashboard.get_display_rows()
        print(f"Dashboard shows {len(dashboard_rows)} rows")
        if dashboard_rows:
            row = dashboard_rows[0]
            print(f"  {row['symbol']}: open={row['open_position']}, closed={row['closed_position']}")
        
        print(f"\nTime check at 5:01pm:")
        self._debug_aggregator_view()
        
        # Show what happened to the closed position data
        print(f"\nDEBUG: Realized entry status:")
        query = f"""
        SELECT 
            DATE(timestamp, 
                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                      THEN '+1 day' 
                      ELSE '+0 day' 
                 END) as trading_day,
            DATE({self.time.get_now_sql()}, 'localtime') as current_trading_day,
            CASE 
                WHEN DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE({self.time.get_now_sql()}, 'localtime')
                THEN 'INCLUDED in aggregator'
                ELSE 'EXCLUDED from aggregator'
            END as status
        FROM realized_fifo
        WHERE symbol = 'ZNH5 Comdty'
        """
        result = self.db.execute_query(query)[0]
        print(f"  Realized entry: trading_day={result['trading_day']}, current={result['current_trading_day']}")
        print(f"  Status: {result['status']}")
        
        # Show the actual date calculation for "now"
        print(f"\nDEBUG: How 'now' translates to trading day at 5:01pm:")
        now_query = f"""
        SELECT 
            {self.time.get_now_sql()} as now_timestamp,
            strftime('%H', {self.time.get_now_sql()}) as hour,
            DATE({self.time.get_now_sql()}, 'localtime') as base_date,
            DATE({self.time.get_now_sql()}, 'localtime',
                 CASE WHEN CAST(strftime('%H', {self.time.get_now_sql()}) AS INTEGER) >= 17 
                      THEN '+1 day' 
                      ELSE '+0 day' 
                 END) as calculated_trading_day
        """
        now_result = self.db.execute_query(now_query)[0]
        print(f"  Now: {now_result['now_timestamp']} (hour {now_result['hour']})")
        print(f"  Base date: {now_result['base_date']}")
        print(f"  Calculated trading day: {now_result['calculated_trading_day']}")
        
    def _debug_aggregator_view(self):
        """Show what the aggregator's date logic sees"""
        query = f"""
        SELECT 
            DATE({self.time.get_now_sql()}, 'localtime') as current_date,
            CAST(strftime('%H', {self.time.get_now_sql()}) AS INTEGER) as current_hour,
            CASE WHEN CAST(strftime('%H', {self.time.get_now_sql()}) AS INTEGER) >= 17 
                 THEN 'Next trading day' 
                 ELSE 'Same trading day' 
            END as trading_day_status
        """
        result = self.db.execute_query(query)[0]
        print(f"  Current: {result['current_date']} {result['current_hour']}:00 -> {result['trading_day_status']}")
        
    def _print_state(self):
        """Print current state of all relevant tables"""
        # Show positions table
        self.db.print_table("positions", "symbol = 'ZNH5 Comdty'")
        
        # Show what dashboard would display
        dashboard_rows = self.dashboard.get_display_rows()
        print("\nDashboard would show:")
        if dashboard_rows:
            for row in dashboard_rows:
                print(f"  {row['symbol']}: open={row['open_position']}, closed={row['closed_position']}, pnl=${row['fifo_realized_pnl']:.2f}")
        else:
            print("  (No rows)")
            
        # Show realized entries with trading day calculation
        print("\nRealized entries with trading day:")
        realized_query = f"""
        SELECT 
            timestamp,
            strftime('%H', timestamp) as hour,
            quantity,
            realizedPnL,
            DATE(timestamp, 
                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                      THEN '+1 day' 
                      ELSE '+0 day' 
                 END) as trading_day,
            DATE({self.time.get_now_sql()}, 'localtime') as current_trading_day
        FROM realized_fifo 
        WHERE symbol = 'ZNH5 Comdty'
        """
        
        realized_rows = self.db.execute_query(realized_query)
        for row in realized_rows:
            print(f"  {row['timestamp']} (hour={row['hour']}) -> trading_day={row['trading_day']}, current={row['current_trading_day']}")


if __name__ == "__main__":
    test = PositionDisplayTest()
    
    # Run specific test case based on command line argument
    import sys
    if len(sys.argv) > 1:
        test_num = sys.argv[1]
        if test_num == "1":
            test.run_test_case_1_same_day()
        elif test_num == "2":
            test.run_test_case_2_cross_day()
        elif test_num == "3":
            test.run_test_case_3_next_day_view()
        elif test_num == "4":
            test.run_test_case_4_5pm_cutoff()
    else:
        # Run just Test Case 4 for now
        test.run_test_case_4_5pm_cutoff()