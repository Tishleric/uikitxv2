#!/usr/bin/env python3
"""Enhanced P&L data validation with detailed analysis."""

import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
import re

class EnhancedPnLValidator:
    """Enhanced validation with better parsing and analysis."""
    
    def __init__(self, db_path="data/output/pnl/pnl_tracker.db"):
        self.db_path = db_path
        self.excel_path = None
        self.excel_data = {}
        self.db_data = {}
        self.issues = []
        
    def parse_32nds_price(self, price_str):
        """Convert 32nds format (e.g., '110-160') to decimal."""
        if pd.isna(price_str) or price_str == 'nan':
            return None
            
        price_str = str(price_str).strip()
        
        # Already decimal
        if '.' in price_str and '-' not in price_str:
            try:
                return float(price_str)
            except:
                return None
                
        # Parse 32nds format
        match = re.match(r'(\d+)-(\d+)/?(\d*)', price_str)
        if match:
            whole = int(match.group(1))
            thirty_seconds = int(match.group(2))
            sub_ticks = int(match.group(3)) if match.group(3) else 0
            
            # Convert to decimal
            decimal = whole + thirty_seconds / 32.0
            if sub_ticks:
                decimal += sub_ticks / 320.0
                
            return decimal
            
        # Try to parse as simple number
        try:
            return float(price_str)
        except:
            return None
            
    def get_latest_excel(self):
        """Find the most recent TYU5 Excel output."""
        excel_dir = Path("data/output/pnl")
        files = list(excel_dir.glob("tyu5_*.xlsx"))
        
        if not files:
            raise FileNotFoundError("No TYU5 Excel files found")
            
        latest = max(files, key=lambda x: x.stat().st_mtime)
        self.excel_path = latest
        print(f"Using Excel file: {latest.name}")
        print(f"  Modified: {datetime.fromtimestamp(latest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        return latest
        
    def load_data(self):
        """Load Excel and database data."""
        # Load Excel
        print("\nLoading Excel sheets...")
        xl_file = pd.ExcelFile(self.excel_path)
        
        # Map sheet names (Excel might have different names)
        sheet_mapping = {
            'Summary': 'summary',
            'Positions': 'positions', 
            'Trades': 'processed_trades',
            'Position_Breakdown': 'breakdown',
            'Risk_Scenarios': 'risk_scenarios'
        }
        
        for excel_name, internal_name in sheet_mapping.items():
            if excel_name in xl_file.sheet_names:
                self.excel_data[internal_name] = pd.read_excel(xl_file, excel_name)
                print(f"  {excel_name}: {len(self.excel_data[internal_name])} rows")
                
        # Load database
        print("\nLoading database tables...")
        conn = sqlite3.connect(self.db_path)
        
        tables = ['lot_positions', 'risk_scenarios', 'positions', 'match_history']
        for table in tables:
            try:
                self.db_data[table] = pd.read_sql(f"SELECT * FROM {table}", conn)
                print(f"  {table}: {len(self.db_data[table])} rows")
            except:
                self.db_data[table] = pd.DataFrame()
                print(f"  {table}: Not found or empty")
                
        conn.close()
        
    def analyze_prices(self):
        """Deep analysis of price discrepancies."""
        print("\n=== PRICE ANALYSIS ===")
        
        if 'breakdown' not in self.excel_data or self.db_data['lot_positions'].empty:
            print("  Skipping: Missing data")
            return
            
        db_lots = self.db_data['lot_positions']
        excel_breakdown = self.excel_data['breakdown']
        
        # Analyze DB prices
        print("\nDatabase Lot Prices:")
        for idx, row in db_lots.iterrows():
            symbol = row['symbol']
            price = row['entry_price']
            qty = row['remaining_quantity']
            
            status = "✓" if price > 0 else "⚠️ ZERO"
            print(f"  {symbol:20} Price: {price:10.5f} Qty: {qty:6.0f} {status}")
            
            if price == 0:
                self.issues.append(f"Zero price in DB for {symbol}")
                
        # Analyze Excel prices
        print("\nExcel Breakdown Prices:")
        open_positions = excel_breakdown[excel_breakdown['Label'] == 'OPEN_POSITION']
        
        for idx, row in open_positions.iterrows():
            symbol = row['Symbol']
            price_str = str(row['Price'])
            qty = row['Quantity']
            
            # Parse price
            decimal_price = self.parse_32nds_price(price_str)
            
            if decimal_price is None:
                status = "⚠️ UNPARSEABLE"
                self.issues.append(f"Cannot parse price '{price_str}' for {symbol}")
            elif decimal_price == 0:
                status = "⚠️ ZERO"
            else:
                status = f"= {decimal_price:.5f}"
                
            print(f"  {symbol:20} Price: {price_str:12} Qty: {qty:6.0f} {status}")
            
    def analyze_quantities(self):
        """Analyze position quantities and aggregation."""
        print("\n=== QUANTITY ANALYSIS ===")
        
        if self.db_data['lot_positions'].empty or 'positions' not in self.excel_data:
            print("  Skipping: Missing data")
            return
            
        # DB aggregation
        db_lots = self.db_data['lot_positions']
        
        # Extract base symbol for grouping
        db_lots['base_symbol'] = db_lots['symbol'].str.extract(r'^([A-Z0-9]+)', expand=False)
        db_summary = db_lots.groupby('base_symbol')['remaining_quantity'].agg(['sum', 'count'])
        
        print("\nDatabase Lot Summary:")
        for symbol, row in db_summary.iterrows():
            print(f"  {symbol:10} Total: {row['sum']:8.0f} from {row['count']} lots")
            
        # Excel positions
        excel_pos = self.excel_data['positions']
        print("\nExcel Position Summary:")
        
        for idx, row in excel_pos.iterrows():
            symbol = row['Symbol']
            net_qty = row['Net_Quantity']
            unrealized = row['Unrealized_PNL']
            
            # Find matching DB total
            db_match = db_summary[db_summary.index == symbol]
            if not db_match.empty:
                db_qty = db_match.iloc[0]['sum']
                diff = net_qty - db_qty
                status = "✓" if abs(diff) < 0.01 else f"⚠️ DIFF: {diff:+.0f}"
            else:
                status = "⚠️ NO DB MATCH"
                
            print(f"  {symbol:10} Net: {net_qty:8.0f} Unrealized: {unrealized} {status}")
            
    def analyze_errors(self):
        """Detailed error analysis."""
        print("\n=== ERROR ANALYSIS ===")
        
        awaiting_data_count = 0
        nan_count = 0
        
        for sheet_name, df in self.excel_data.items():
            sheet_errors = []
            
            for col in df.columns:
                col_str = df[col].astype(str)
                
                # Count specific error types
                awaiting = col_str.str.contains('awaiting data', case=False, na=False).sum()
                nans = col_str.str.contains('nan', case=False, na=False).sum()
                
                if awaiting > 0:
                    sheet_errors.append(f"{col}: {awaiting} 'awaiting data'")
                    awaiting_data_count += awaiting
                    
                if nans > 0 and col != 'attribution_error':  # Skip expected NaN columns
                    sheet_errors.append(f"{col}: {nans} NaN values")
                    nan_count += nans
                    
            if sheet_errors:
                print(f"\n{sheet_name}:")
                for error in sheet_errors:
                    print(f"  {error}")
                    
        print(f"\nTotal 'awaiting data': {awaiting_data_count}")
        print(f"Total NaN values: {nan_count}")
        
        # Check which symbols have missing prices
        if 'positions' in self.excel_data:
            positions = self.excel_data['positions']
            missing_price_symbols = positions[
                positions['Unrealized_PNL'].astype(str).str.contains('awaiting', na=False)
            ]['Symbol'].tolist()
            
            if missing_price_symbols:
                print(f"\nSymbols with missing prices: {', '.join(missing_price_symbols)}")
                self.issues.append(f"Missing prices for: {missing_price_symbols}")
                
    def analyze_matches(self):
        """Analyze trade matching."""
        print("\n=== MATCH ANALYSIS ===")
        
        if 'processed_trades' not in self.excel_data:
            # Try the 'Trades' sheet
            if 'trades' in self.excel_data:
                trades = self.excel_data['trades']
            else:
                print("  No trades sheet found")
                return
        else:
            trades = self.excel_data['processed_trades']
            
        print(f"\nTotal trades: {len(trades)}")
        
        # Analyze by action
        if 'Action' in trades.columns:
            action_counts = trades['Action'].value_counts()
            print("\nTrade actions:")
            for action, count in action_counts.items():
                print(f"  {action}: {count}")
                
        # Check for FIFO matching opportunities
        match_opportunities = 0
        
        for symbol in trades['Symbol'].unique():
            symbol_trades = trades[trades['Symbol'] == symbol]
            
            buys = symbol_trades[symbol_trades['Action'] == 'BUY']['Quantity'].sum()
            sells = symbol_trades[symbol_trades['Action'] == 'SELL']['Quantity'].sum()
            
            matched_qty = min(buys, sells)
            if matched_qty > 0:
                match_opportunities += 1
                print(f"\n  {symbol}: Buy {buys}, Sell {sells} → Could match {matched_qty}")
                
        if match_opportunities > 0 and len(self.db_data['match_history']) == 0:
            print(f"\n⚠️ Found {match_opportunities} symbols with matchable trades but match_history is empty")
            self.issues.append("No match history despite matchable trades")
            
    def generate_summary(self):
        """Generate comprehensive summary."""
        print("\n" + "="*70)
        print("ENHANCED P&L VALIDATION SUMMARY")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Excel: {self.excel_path.name}")
        print(f"Database: {Path(self.db_path).name}")
        
        if self.issues:
            print(f"\n⚠️ ISSUES IDENTIFIED: {len(self.issues)}")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\n✅ All validations passed")
            
        # Key metrics
        print("\nKEY METRICS:")
        
        if 'summary' in self.excel_data:
            summary = self.excel_data['summary']
            for idx, row in summary.iterrows():
                metric = row.get('Metric', '')
                value = row.get('Value', '')
                if metric in ['Total PNL', 'Unrealized PNL', 'Realized PNL']:
                    print(f"  {metric}: {value:,.2f}" if isinstance(value, (int, float)) else f"  {metric}: {value}")
                    
        print("\n" + "="*70)
        
    def run(self):
        """Run all validations."""
        try:
            self.get_latest_excel()
            self.load_data()
            
            self.analyze_prices()
            self.analyze_quantities()
            self.analyze_errors()
            self.analyze_matches()
            
            self.generate_summary()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    validator = EnhancedPnLValidator()
    validator.run() 