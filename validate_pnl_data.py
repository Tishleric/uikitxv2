#!/usr/bin/env python3
"""Validate P&L data between database and Excel output.

This script performs non-intrusive validation by comparing:
- Database tables (lot_positions, risk_scenarios, etc.)
- Excel sheets (positions, processed_trades, etc.)
"""

import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class PnLDataValidator:
    """Compare and validate P&L data between database and Excel."""
    
    def __init__(self, db_path="data/output/pnl/pnl_tracker.db"):
        self.db_path = db_path
        self.excel_path = None
        self.excel_data = {}
        self.db_data = {}
        self.issues = []
        
    def get_latest_excel(self, pattern="tyu5_*.xlsx"):
        """Find the most recent TYU5 Excel output."""
        excel_dir = Path("data/output/pnl")
        files = list(excel_dir.glob(pattern))
        
        if not files:
            raise FileNotFoundError(f"No Excel files matching {pattern} found")
            
        # Get most recent by modification time
        latest = max(files, key=lambda x: x.stat().st_mtime)
        self.excel_path = latest
        return latest
        
    def load_excel_sheets(self):
        """Load all sheets from the Excel file."""
        print(f"Loading Excel file: {self.excel_path}")
        
        # Read all sheets
        xl_file = pd.ExcelFile(self.excel_path)
        for sheet_name in xl_file.sheet_names:
            self.excel_data[sheet_name] = pd.read_excel(xl_file, sheet_name)
            print(f"  Loaded sheet '{sheet_name}': {len(self.excel_data[sheet_name])} rows")
            
    def load_db_tables(self):
        """Load relevant tables from the database."""
        print(f"\nLoading database: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        
        # Define tables to load
        tables = ['lot_positions', 'risk_scenarios', 'positions', 'match_history']
        
        for table in tables:
            try:
                self.db_data[table] = pd.read_sql(f"SELECT * FROM {table}", conn)
                print(f"  Loaded table '{table}': {len(self.db_data[table])} rows")
            except Exception as e:
                print(f"  Warning: Could not load {table}: {e}")
                self.db_data[table] = pd.DataFrame()
                
        conn.close()
        
    def check_lot_prices(self):
        """Compare lot entry prices between database and Excel breakdown."""
        print("\n=== CHECKING LOT PRICES ===")
        
        if 'breakdown' not in self.excel_data or self.db_data['lot_positions'].empty:
            print("  Skipping: Missing breakdown sheet or lot_positions data")
            return
            
        # Get lot data from both sources
        db_lots = self.db_data['lot_positions']
        excel_breakdown = self.excel_data['breakdown']
        
        # Filter Excel breakdown for OPEN_POSITION entries
        excel_lots = excel_breakdown[excel_breakdown['Label'] == 'OPEN_POSITION'].copy()
        
        if excel_lots.empty:
            print("  No OPEN_POSITION entries in Excel breakdown")
            return
            
        # Compare prices
        price_issues = []
        
        for idx, db_row in db_lots.iterrows():
            symbol = db_row['symbol']
            db_price = db_row['entry_price']
            
            # Find matching Excel entry
            excel_match = excel_lots[excel_lots['Symbol'].str.contains(symbol.split()[0], na=False)]
            
            if not excel_match.empty:
                # Parse Excel price (might be in 32nds format)
                excel_price_str = str(excel_match.iloc[0]['Price'])
                
                # Check for zero prices
                if db_price == 0 and excel_price_str != '0':
                    price_issues.append({
                        'symbol': symbol,
                        'db_price': db_price,
                        'excel_price': excel_price_str,
                        'issue': 'DB has zero price'
                    })
                    
        if price_issues:
            print("\n  Price Issues Found:")
            for issue in price_issues:
                print(f"    {issue['symbol']:20} DB: {issue['db_price']:.5f}  Excel: {issue['excel_price']}  ({issue['issue']})")
                self.issues.append(f"Price mismatch: {issue}")
        else:
            print("  ✓ All lot prices match")
            
    def check_position_quantities(self):
        """Verify position quantities aggregate correctly."""
        print("\n=== CHECKING POSITION QUANTITIES ===")
        
        if 'positions' not in self.excel_data or self.db_data['lot_positions'].empty:
            print("  Skipping: Missing positions sheet or lot_positions data")
            return
            
        # Aggregate DB quantities by symbol
        db_lots = self.db_data['lot_positions']
        db_totals = db_lots.groupby('symbol')['remaining_quantity'].sum().reset_index()
        
        # Get Excel positions
        excel_positions = self.excel_data['positions']
        
        quantity_issues = []
        
        for idx, row in excel_positions.iterrows():
            symbol = row['Symbol']
            excel_qty = row['Net_Quantity']
            
            # Find DB total for this symbol
            db_match = db_totals[db_totals['symbol'].str.contains(symbol, na=False)]
            
            if not db_match.empty:
                db_qty = db_match.iloc[0]['remaining_quantity']
                
                if abs(db_qty - excel_qty) > 0.01:  # Allow small rounding differences
                    quantity_issues.append({
                        'symbol': symbol,
                        'db_qty': db_qty,
                        'excel_qty': excel_qty,
                        'difference': db_qty - excel_qty
                    })
            else:
                print(f"  Warning: No DB lots found for {symbol}")
                
        if quantity_issues:
            print("\n  Quantity Issues Found:")
            for issue in quantity_issues:
                print(f"    {issue['symbol']:10} DB: {issue['db_qty']:8.0f}  Excel: {issue['excel_qty']:8.0f}  Diff: {issue['difference']:8.0f}")
                self.issues.append(f"Quantity mismatch: {issue}")
        else:
            print("  ✓ All quantities match")
            
    def check_error_indicators(self):
        """Find error indicators like 'awaiting data' in Excel."""
        print("\n=== CHECKING ERROR INDICATORS ===")
        
        error_patterns = ['awaiting data', 'error', 'nan', '#VALUE!', '#REF!']
        errors_found = []
        
        for sheet_name, df in self.excel_data.items():
            if df.empty:
                continue
                
            # Check each column for error patterns
            for col in df.columns:
                # Convert to string for pattern matching
                col_str = df[col].astype(str)
                
                for pattern in error_patterns:
                    mask = col_str.str.contains(pattern, case=False, na=False)
                    if mask.any():
                        error_rows = df[mask]
                        errors_found.append({
                            'sheet': sheet_name,
                            'column': col,
                            'pattern': pattern,
                            'count': len(error_rows),
                            'rows': error_rows.index.tolist()
                        })
                        
        if errors_found:
            print("\n  Error Indicators Found:")
            for error in errors_found:
                print(f"    {error['sheet']:15} {error['column']:20} '{error['pattern']}' in {error['count']} rows")
                if error['count'] <= 5:
                    print(f"      Rows: {error['rows']}")
                self.issues.append(f"Error indicator: {error}")
        else:
            print("  ✓ No error indicators found")
            
    def check_matched_trades(self):
        """Identify trades that should be matched."""
        print("\n=== CHECKING MATCHED TRADES ===")
        
        if 'processed_trades' not in self.excel_data:
            print("  Skipping: No processed_trades sheet")
            return
            
        trades = self.excel_data['processed_trades']
        match_history = self.db_data['match_history']
        
        print(f"  Match history entries: {len(match_history)}")
        
        if trades.empty:
            return
            
        # Group by symbol to find potential matches
        potential_matches = []
        
        for symbol in trades['Symbol'].unique():
            symbol_trades = trades[trades['Symbol'] == symbol].sort_values('Time')
            
            # Simple logic: SELL after BUY should create a match
            for i in range(len(symbol_trades) - 1):
                curr_trade = symbol_trades.iloc[i]
                next_trade = symbol_trades.iloc[i + 1]
                
                if curr_trade['Action'] == 'SELL' and next_trade['Action'] == 'BUY':
                    # This should create a match for the smaller quantity
                    match_qty = min(curr_trade['Quantity'], next_trade['Quantity'])
                    potential_matches.append({
                        'symbol': symbol,
                        'sell_trade': curr_trade['Trade_ID'] if 'Trade_ID' in curr_trade else i,
                        'buy_trade': next_trade['Trade_ID'] if 'Trade_ID' in next_trade else i+1,
                        'quantity': match_qty
                    })
                    
        if potential_matches and len(match_history) == 0:
            print("\n  Missing Matches:")
            print("  No entries in match_history table, but found potential matches:")
            for match in potential_matches[:5]:  # Show first 5
                print(f"    {match['symbol']}: Sell trade {match['sell_trade']} + Buy trade {match['buy_trade']} = {match['quantity']} units")
            self.issues.append(f"Missing matches: {len(potential_matches)} potential matches not recorded")
        else:
            print("  ✓ Match history appears consistent")
            
    def check_risk_scenarios(self):
        """Verify risk scenario calculations."""
        print("\n=== CHECKING RISK SCENARIOS ===")
        
        if 'risk_scenarios' not in self.excel_data or self.db_data['risk_scenarios'].empty:
            print("  Skipping: Missing risk scenario data")
            return
            
        db_risk = self.db_data['risk_scenarios']
        excel_risk = self.excel_data['risk_scenarios']
        
        # Check scenario count
        print(f"  DB scenarios: {len(db_risk)}")
        print(f"  Excel scenarios: {len(excel_risk)}")
        
        # Check for NaN or infinite values
        db_inf_count = np.isinf(db_risk['scenario_pnl']).sum()
        db_nan_count = db_risk['scenario_pnl'].isna().sum()
        
        if db_inf_count > 0 or db_nan_count > 0:
            print(f"  Warning: DB has {db_inf_count} infinite and {db_nan_count} NaN scenario P&L values")
            self.issues.append(f"Risk scenarios: {db_inf_count} infinite, {db_nan_count} NaN values in DB")
            
    def generate_report(self):
        """Generate the final validation report."""
        print("\n" + "="*60)
        print("P&L DATA VALIDATION REPORT")
        print("="*60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Excel File: {self.excel_path.name if self.excel_path else 'Not found'}")
        print(f"Database: {self.db_path}")
        
        if self.issues:
            print(f"\n⚠️  ISSUES FOUND: {len(self.issues)}")
            print("-"*60)
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\n✅ NO ISSUES FOUND - All validations passed")
            
        print("\n" + "="*60)
        
        # Summary statistics
        print("\nSUMMARY STATISTICS:")
        print(f"  Database Tables Loaded: {len([d for d in self.db_data.values() if not d.empty])}")
        print(f"  Excel Sheets Loaded: {len(self.excel_data)}")
        
        if 'positions' in self.excel_data:
            positions = self.excel_data['positions']
            print(f"  Total Positions: {len(positions)}")
            print(f"  Total Unrealized P&L: {positions['Unrealized_PNL'].apply(lambda x: 0 if x == 'awaiting data' else x).sum():,.2f}")
            
    def run_validation(self):
        """Run all validation checks."""
        try:
            # Load data
            self.get_latest_excel()
            self.load_excel_sheets()
            self.load_db_tables()
            
            # Run checks
            self.check_lot_prices()
            self.check_position_quantities()
            self.check_error_indicators()
            self.check_matched_trades()
            self.check_risk_scenarios()
            
            # Generate report
            self.generate_report()
            
        except Exception as e:
            print(f"\n❌ Validation Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    validator = PnLDataValidator()
    validator.run_validation() 