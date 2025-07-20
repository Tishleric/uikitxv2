"""
FULLPNL table builder orchestrator.

Manages creation and updates of the master P&L table.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import logging
from datetime import datetime
import pandas as pd

from .data_sources import PnLDatabase, SpotRiskDatabase, MarketPricesDatabase
from .symbol_mapper import SymbolMapper

logger = logging.getLogger(__name__)


class FULLPNLBuilder:
    """Orchestrates building and updating the FULLPNL master table."""
    
    # Greek column definitions (column_name, db_field, description)
    GREEK_COLUMNS = [
        ('delta_f', 'delta_F', 'Delta w.r.t futures'),
        ('delta_y', 'delta_y', 'Delta w.r.t yield'),
        ('gamma_f', 'gamma_F', 'Gamma w.r.t futures'),
        ('gamma_y', 'gamma_y', 'Gamma w.r.t yield'),
        ('speed_f', 'speed_F', 'Speed w.r.t futures'),
        ('theta_f', 'theta_F', 'Theta w.r.t futures'),
        ('vega_f', 'vega_price', 'Vega in price terms'),
        ('vega_y', 'vega_y', 'Vega w.r.t yield'),
    ]
    
    # Fixed DV01 for futures
    FUTURES_DELTA_F = 63.0
    
    def __init__(self, 
                 pnl_db_path: Optional[Path] = None,
                 spot_risk_db_path: Optional[Path] = None,
                 market_prices_db_path: Optional[Path] = None):
        """Initialize builder with database paths.
        
        If paths not provided, uses default locations.
        """
        # Set default paths
        if pnl_db_path is None:
            pnl_db_path = Path("data/output/pnl/pnl_tracker.db")
        if spot_risk_db_path is None:
            spot_risk_db_path = Path("data/output/spot_risk/spot_risk.db")
        if market_prices_db_path is None:
            market_prices_db_path = Path("data/output/market_prices/market_prices.db")
            
        # Initialize data sources
        self.pnl_db = PnLDatabase(pnl_db_path)
        self.spot_risk_db = SpotRiskDatabase(spot_risk_db_path)
        self.market_prices_db = MarketPricesDatabase(market_prices_db_path)
        
        # Initialize symbol mapper
        self.symbol_mapper = SymbolMapper()
        
        logger.info(f"Initialized FULLPNLBuilder with databases:")
        logger.info(f"  P&L: {pnl_db_path}")
        logger.info(f"  Spot Risk: {spot_risk_db_path}")
        logger.info(f"  Market Prices: {market_prices_db_path}")
        
    def create_empty_table_if_missing(self) -> bool:
        """Create FULLPNL table if it doesn't exist.
        
        Returns True if table was created, False if already existed.
        """
        if self.pnl_db.fullpnl_exists():
            logger.info("FULLPNL table already exists")
            return False
            
        logger.info("Creating FULLPNL table...")
        
        # Create table with all expected columns
        create_sql = """
            CREATE TABLE FULLPNL (
                -- Primary identifier
                symbol TEXT PRIMARY KEY,
                
                -- Market data
                bid REAL,
                ask REAL,
                price REAL,
                px_last REAL,
                px_settle REAL,
                
                -- Positions
                open_position REAL,
                closed_position REAL,
                
                -- Greeks (F-space)
                delta_f REAL,
                gamma_f REAL,
                speed_f REAL,
                theta_f REAL,
                vega_f REAL,
                
                -- Greeks (Y-space)
                delta_y REAL,
                gamma_y REAL,
                vega_y REAL,
                
                -- Other fields
                vtexp REAL,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        self.pnl_db.execute(create_sql)
        self.pnl_db.conn.commit()
        
        logger.info("FULLPNL table created successfully")
        return True
        
    def get_missing_columns(self) -> List[str]:
        """Check which expected columns are missing from FULLPNL."""
        expected_columns = {
            'symbol', 'bid', 'ask', 'price', 'px_last', 'px_settle',
            'open_position', 'closed_position',
            'delta_f', 'gamma_f', 'speed_f', 'theta_f', 'vega_f',
            'delta_y', 'gamma_y', 'vega_y', 'vtexp',
            'created_at', 'updated_at'
        }
        
        if not self.pnl_db.fullpnl_exists():
            return list(expected_columns)
            
        existing_columns = set(self.pnl_db.get_fullpnl_columns())
        missing = expected_columns - existing_columns
        
        return sorted(list(missing))
        
    def populate_symbols(self) -> int:
        """Populate FULLPNL with symbols from positions table.
        
        Returns number of symbols added.
        """
        # Get all symbols from positions
        symbols = self.pnl_db.get_all_symbols()
        logger.info(f"Found {len(symbols)} symbols in positions table")
        
        if not symbols:
            logger.warning("No symbols found in positions table")
            return 0
            
        # Insert symbols into FULLPNL
        inserted = 0
        for symbol in symbols:
            try:
                self.pnl_db.execute(
                    "INSERT OR IGNORE INTO FULLPNL (symbol) VALUES (?)",
                    (symbol,)
                )
                if self.pnl_db.conn.total_changes > inserted:
                    inserted += 1
            except Exception as e:
                logger.error(f"Error inserting symbol {symbol}: {e}")
                
        self.pnl_db.conn.commit()
        logger.info(f"Inserted {inserted} new symbols into FULLPNL")
        
        return inserted
        
    def update_positions(self) -> Dict[str, int]:
        """Update open and closed position columns from positions table.
        
        Returns dict with update counts.
        """
        logger.info("Updating position columns...")
        
        # First ensure closed positions are updated
        try:
            from lib.trading.pnl_calculator.controller import PnLController
            controller = PnLController()
            controller.update_closed_positions()
            logger.info("Updated closed positions using ClosedPositionTracker")
        except Exception as e:
            logger.warning(f"Could not update closed positions: {e}")
        
        # Get all positions
        positions = self.pnl_db.get_positions()
        
        open_updated = 0
        closed_updated = 0
        
        for pos in positions:
            symbol = pos['symbol']
            open_pos = pos.get('open_position', 0)
            closed_pos = pos.get('closed_position', 0)
            
            self.pnl_db.execute("""
                UPDATE FULLPNL 
                SET open_position = ?, closed_position = ?, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (open_pos, closed_pos, symbol))
            
            if self.pnl_db.conn.total_changes > open_updated + closed_updated:
                if open_pos is not None:
                    open_updated += 1
                if closed_pos is not None:
                    closed_updated += 1
                    
        self.pnl_db.conn.commit()
        
        logger.info(f"Updated {open_updated} open positions, {closed_updated} closed positions")
        return {'open_position': open_updated, 'closed_position': closed_updated}
        
    def update_spot_risk_data(self) -> Dict[str, int]:
        """Update bid, ask, price, and vtexp from spot risk data.
        
        Returns dict with update counts.
        """
        logger.info("Updating spot risk data (bid/ask/price/vtexp)...")
        
        # Get all symbols from FULLPNL
        cursor = self.pnl_db.execute("SELECT symbol FROM FULLPNL")
        symbols = [row[0] for row in cursor.fetchall()]
        
        # Get spot risk data for all symbols
        spot_risk_data = self.spot_risk_db.get_latest_spot_risk_data(symbols)
        
        bid_updated = 0
        ask_updated = 0
        price_updated = 0
        vtexp_updated = 0
        
        for symbol, data in spot_risk_data.items():
            # Extract values
            bid = data.get('bid')
            ask = data.get('ask')
            adjtheor = data.get('adjtheor')
            midpoint = data.get('midpoint_price')
            vtexp = data.get('vtexp')
            
            # Calculate price using hierarchy: adjtheor -> midpoint -> (bid+ask)/2
            price = None
            if adjtheor is not None and pd.notna(adjtheor):
                price = float(adjtheor)
            elif midpoint is not None and pd.notna(midpoint):
                price = float(midpoint)
            elif bid is not None and ask is not None and pd.notna(bid) and pd.notna(ask):
                price = (float(bid) + float(ask)) / 2
                
            # Convert to float if not None
            if bid is not None and pd.notna(bid):
                bid = float(bid)
            else:
                bid = None
                
            if ask is not None and pd.notna(ask):
                ask = float(ask)
            else:
                ask = None
                
            if vtexp is not None and pd.notna(vtexp):
                vtexp = float(vtexp)
            else:
                vtexp = None
                
            # Update FULLPNL
            self.pnl_db.execute("""
                UPDATE FULLPNL 
                SET bid = ?, ask = ?, price = ?, vtexp = ?, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (bid, ask, price, vtexp, symbol))
            
            if bid is not None:
                bid_updated += 1
            if ask is not None:
                ask_updated += 1
            if price is not None:
                price_updated += 1
            if vtexp is not None:
                vtexp_updated += 1
                
        self.pnl_db.conn.commit()
        
        logger.info(f"Updated: bid={bid_updated}, ask={ask_updated}, price={price_updated}, vtexp={vtexp_updated}")
        return {
            'bid': bid_updated,
            'ask': ask_updated, 
            'price': price_updated,
            'vtexp': vtexp_updated
        }
        
    def update_market_prices(self) -> Dict[str, int]:
        """Update px_last and px_settle from market prices database.
        
        Returns dict with update counts.
        """
        logger.info("Updating market prices (px_last/px_settle)...")
        
        # Get all symbols from FULLPNL
        cursor = self.pnl_db.execute("SELECT symbol FROM FULLPNL")
        symbols = [row[0] for row in cursor.fetchall()]
        
        # Get latest market prices
        market_prices = self.market_prices_db.get_latest_prices(symbols)
        
        # Get T and T+1 dates for px_settle logic
        t_date, t_plus_1_date = self.market_prices_db.get_latest_trade_dates()
        
        px_last_updated = 0
        px_settle_updated = 0
        
        for symbol, prices in market_prices.items():
            px_last = prices.get('current_price')
            px_settle = prices.get('prior_close')
            
            self.pnl_db.execute("""
                UPDATE FULLPNL 
                SET px_last = ?, px_settle = ?, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (px_last, px_settle, symbol))
            
            if px_last is not None:
                px_last_updated += 1
            if px_settle is not None:
                px_settle_updated += 1
                
        self.pnl_db.conn.commit()
        
        logger.info(f"Updated: px_last={px_last_updated}, px_settle={px_settle_updated}")
        return {'px_last': px_last_updated, 'px_settle': px_settle_updated}
        
    def update_greeks(self) -> Dict[str, int]:
        """Update all Greek columns from spot risk calculated data.
        
        Returns dict with update counts.
        """
        logger.info("Updating Greeks...")
        
        # Get all symbols from FULLPNL
        cursor = self.pnl_db.execute("SELECT symbol FROM FULLPNL")
        symbols = [row[0] for row in cursor.fetchall()]
        
        # Get spot risk data (includes Greeks)
        spot_risk_data = self.spot_risk_db.get_latest_spot_risk_data(symbols)
        
        greek_updates = {col[0]: 0 for col in self.GREEK_COLUMNS}
        futures_updated = 0
        
        for symbol in symbols:
            # Check if it's a future
            parsed = self.symbol_mapper.parse_bloomberg_symbol(symbol)
            if parsed and parsed.symbol_type == 'FUT':
                # Set all Greeks for futures (delta_f = 63, others = 0)
                self.pnl_db.execute("""
                    UPDATE FULLPNL 
                    SET delta_f = ?, gamma_f = 0, gamma_y = 0, 
                        speed_f = 0, theta_f = 0, vega_f = 0, vega_y = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = ?
                """, (self.FUTURES_DELTA_F, symbol))
                futures_updated += 1
                greek_updates['delta_f'] += 1
                greek_updates['gamma_f'] += 1
                greek_updates['gamma_y'] += 1
                
            elif symbol in spot_risk_data:
                # Update all Greeks for options
                data = spot_risk_data[symbol]
                
                update_parts = []
                params = []
                
                for col_name, db_field, _ in self.GREEK_COLUMNS:
                    value = data.get(db_field)
                    if value is not None and pd.notna(value):
                        update_parts.append(f"{col_name} = ?")
                        params.append(float(value))
                        greek_updates[col_name] += 1
                        
                if update_parts:
                    params.append(symbol)  # WHERE clause
                    update_sql = f"""
                        UPDATE FULLPNL 
                        SET {', '.join(update_parts)}, updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = ?
                    """
                    self.pnl_db.execute(update_sql, tuple(params))
                    
        self.pnl_db.conn.commit()
        
        logger.info(f"Updated Greeks: {greek_updates}, futures_delta={futures_updated}")
        return greek_updates
        
    def build_or_update(self, full_rebuild: bool = False) -> Dict[str, int]:
        """Build or update the FULLPNL table.
        
        Args:
            full_rebuild: If True, drops and recreates table. If False, updates existing.
            
        Returns dict with counts of updates per column.
        """
        logger.info(f"Starting FULLPNL {'rebuild' if full_rebuild else 'update'} process...")
        
        if full_rebuild:
            # Drop existing table
            self.pnl_db.execute("DROP TABLE IF EXISTS FULLPNL")
            self.pnl_db.conn.commit()
            logger.info("Dropped existing FULLPNL table")
        
        # Create table if needed
        self.create_empty_table_if_missing()
        
        # Populate symbols first
        new_symbols = self.populate_symbols()
        
        # Update all columns
        results = {
            'new_symbols': new_symbols,
        }
        
        # Update positions
        pos_results = self.update_positions()
        results.update(pos_results)
        
        # Update spot risk data (bid/ask/price/vtexp)
        spot_results = self.update_spot_risk_data()
        results.update(spot_results)
        
        # Update market prices
        price_results = self.update_market_prices()
        results.update(price_results)
        
        # Update Greeks
        greek_results = self.update_greeks()
        results.update(greek_results)
        
        # Final update timestamp
        self.pnl_db.execute("UPDATE FULLPNL SET updated_at = CURRENT_TIMESTAMP")
        self.pnl_db.conn.commit()
        
        logger.info(f"FULLPNL update complete: {results}")
        return results
        
    def get_table_summary(self) -> Dict[str, Any]:
        """Get summary statistics of FULLPNL table.
        
        Returns dict with counts and coverage statistics.
        """
        if not self.pnl_db.fullpnl_exists():
            return {'error': 'FULLPNL table does not exist'}
            
        # Get basic counts
        cursor = self.pnl_db.execute("""
            SELECT 
                COUNT(*) as total_symbols,
                COUNT(bid) as with_bid,
                COUNT(ask) as with_ask,
                COUNT(price) as with_price,
                COUNT(px_last) as with_px_last,
                COUNT(px_settle) as with_px_settle,
                COUNT(open_position) as with_open_position,
                COUNT(closed_position) as with_closed_position,
                COUNT(delta_f) as with_delta_f,
                COUNT(vtexp) as with_vtexp
            FROM FULLPNL
        """)
        
        result = cursor.fetchone()
        columns = [col[0] for col in cursor.description]
        
        summary = dict(zip(columns, result))
        
        # Calculate coverage percentages
        total = summary['total_symbols']
        if total > 0:
            # Create a list of keys to avoid modifying dict during iteration
            keys_to_process = [key for key in summary if key != 'total_symbols' and key.startswith('with_')]
            for key in keys_to_process:
                field_name = key[5:]  # Remove 'with_' prefix
                count = summary[key]
                summary[f'{field_name}_coverage'] = round(count / total * 100, 1)
                    
        return summary
        
    def close(self):
        """Close all database connections."""
        self.pnl_db.close()
        self.spot_risk_db.close()
        self.market_prices_db.close() 