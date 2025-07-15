"""
Phase 1 Integration Test with Fixed Symbol Translator

Tests the complete Phase 1 data pipeline:
1. Symbol Translation (Actant -> Bloomberg)
2. Trade Preprocessing (validation, SOD detection)
3. Market Price Lookup
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
import pytz
from pathlib import Path
import json
from typing import Optional

from lib.trading.symbol_translator import SymbolTranslator
from lib.trading.pnl_calculator.price_file_selector import PriceFileSelector

def process_trades_with_translation(trade_file: str):
    """Process trades with symbol translation and validation."""
    
    # Initialize translator
    translator = SymbolTranslator()
    
    # Read trades
    trades_df = pd.read_csv(trade_file)
    print(f"\nLoaded {len(trades_df)} trades from {trade_file}")
    
    # Add processing columns
    trades_df['bloomberg_symbol'] = None
    trades_df['validation_status'] = 'OK'
    trades_df['is_sod'] = False
    trades_df['is_expiry'] = False
    trades_df['signed_quantity'] = 0.0
    
    # Chicago timezone for SOD detection
    chicago_tz = pytz.timezone('America/Chicago')
    
    # Process each trade
    for idx, row in trades_df.iterrows():
        # 1. Symbol Translation
        actant_symbol = row['instrumentName']
        bloomberg_symbol = translator.translate(actant_symbol)
        
        if bloomberg_symbol:
            trades_df.at[idx, 'bloomberg_symbol'] = bloomberg_symbol
        else:
            trades_df.at[idx, 'validation_status'] = 'SYMBOL_ERROR'
            continue
            
        # 2. Trade Preprocessing
        # Convert Buy/Sell to signed quantity
        quantity = float(row['quantity'])
        if row['buySell'] == 'S':
            quantity = -quantity
        trades_df.at[idx, 'signed_quantity'] = quantity
        
        # Parse timestamp and check for SOD/Expiry
        timestamp_str = str(row['marketTradeTime']).split('.')[0]
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        # Convert to Chicago time for SOD check
        if timestamp.tzinfo is None:
            timestamp = chicago_tz.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(chicago_tz)
            
        # SOD detection: trades at midnight Chicago time
        if timestamp.hour == 0 and timestamp.minute == 0:
            trades_df.at[idx, 'is_sod'] = True
            trades_df.at[idx, 'validation_status'] = 'SOD'
            
        # Expiry detection: zero price trades
        if float(row['price']) == 0.0:
            trades_df.at[idx, 'is_expiry'] = True
            trades_df.at[idx, 'validation_status'] = 'EXPIRY'
    
    return trades_df

def is_futures_symbol(bloomberg_symbol: str) -> bool:
    """Check if a Bloomberg symbol is a futures contract."""
    if not bloomberg_symbol:
        return False
    # Futures format: {Product}{Month}{Year} Comdty (e.g., TYU5 Comdty)
    # Options format: {Contract}{Month}{Year}{Type}{Occurrence} {Strike} Comdty
    parts = bloomberg_symbol.split()
    if len(parts) == 2 and parts[1] == 'Comdty':
        # Check if first part matches futures pattern (2-3 letters + letter + digit)
        symbol_part = parts[0]
        if len(symbol_part) >= 3 and symbol_part[:-2].isalpha() and symbol_part[-2].isalpha() and symbol_part[-1].isdigit():
            return True
    return False

def extract_futures_base_symbol(futures_symbol: str) -> str:
    """Extract base symbol from futures contract (e.g., TYU5 -> TY)."""
    # Remove ' Comdty' and extract base
    symbol_part = futures_symbol.split()[0]
    # Remove month and year (last 2 chars)
    return symbol_part[:-2]

def lookup_market_prices(processed_trades: pd.DataFrame, price_directory: str, current_time: Optional[datetime] = None):
    """Look up market prices for Bloomberg symbols using intelligent file selection."""
    
    # Get unique Bloomberg symbols (excluding errors)
    valid_trades = processed_trades[processed_trades['bloomberg_symbol'].notna()]
    unique_symbols = valid_trades['bloomberg_symbol'].unique()
    
    print(f"\nLooking up prices for {len(unique_symbols)} unique symbols")
    
    # Separate futures and options symbols
    futures_symbols = [s for s in unique_symbols if is_futures_symbol(s)]
    options_symbols = [s for s in unique_symbols if not is_futures_symbol(s)]
    
    print(f"  Futures: {len(futures_symbols)}, Options: {len(options_symbols)}")
    
    # Use price file selector
    selector = PriceFileSelector()
    base_dir = Path(price_directory).parent
    
    # Select appropriate price files
    file_selection = selector.select_price_files(base_dir, current_time)
    
    # Load futures prices
    futures_price_lookup = {}
    futures_price_col = 'PX_LAST'  # default
    
    if futures_symbols and 'futures' in file_selection and 'file' in file_selection['futures']:
        futures_info = file_selection['futures']
        futures_file = futures_info['file']
        futures_price_col = futures_info['price_column']
        
        print(f"Using futures price file: {futures_file.name} (column: {futures_price_col})")
        futures_df = pd.read_csv(futures_file)
        
        # Create base symbol lookup
        for _, row in futures_df.iterrows():
            base_symbol = row['SYMBOL']
            futures_price_lookup[base_symbol] = row[futures_price_col]
    
    # Load options prices
    options_price_lookup = {}
    options_price_col = 'PX_LAST'  # default
    
    if options_symbols and 'options' in file_selection and 'file' in file_selection['options']:
        options_info = file_selection['options']
        options_file = options_info['file']
        options_price_col = options_info['price_column']
        
        print(f"Using options price file: {options_file.name} (column: {options_price_col})")
        options_df = pd.read_csv(options_file)
        
        # Create price lookup dictionary
        for _, row in options_df.iterrows():
            symbol = row['SYMBOL']
            options_price_lookup[symbol] = row[options_price_col]
    
    # Add price columns
    processed_trades['market_price'] = None
    processed_trades['price_source'] = None
    
    # Look up prices
    found_count = 0
    for idx, row in processed_trades.iterrows():
        bloomberg_symbol = row['bloomberg_symbol']
        if not bloomberg_symbol:
            continue
            
        if is_futures_symbol(bloomberg_symbol):
            # Look up futures price using base symbol
            base_symbol = extract_futures_base_symbol(bloomberg_symbol)
            if base_symbol in futures_price_lookup:
                processed_trades.at[idx, 'market_price'] = futures_price_lookup[base_symbol]
                processed_trades.at[idx, 'price_source'] = futures_price_col
                found_count += 1
            else:
                processed_trades.at[idx, 'price_source'] = 'MISSING'
        else:
            # Look up options price
            if bloomberg_symbol in options_price_lookup:
                processed_trades.at[idx, 'market_price'] = options_price_lookup[bloomberg_symbol]
                processed_trades.at[idx, 'price_source'] = options_price_col
                found_count += 1
            else:
                processed_trades.at[idx, 'price_source'] = 'MISSING'
    
    print(f"Found prices for {found_count}/{len(unique_symbols)} symbols")
    
    return processed_trades

def generate_integration_report(processed_trades: pd.DataFrame, output_dir: str):
    """Generate integration test report."""
    
    # Summary statistics
    summary = {
        'test_timestamp': datetime.now().isoformat(),
        'total_trades': len(processed_trades),
        'symbol_translation': {
            'success': len(processed_trades[processed_trades['bloomberg_symbol'].notna()]),
            'failed': len(processed_trades[processed_trades['bloomberg_symbol'].isna()])
        },
        'validation_summary': dict(processed_trades['validation_status'].value_counts()),
        'price_lookup': {
            'found': len(processed_trades[processed_trades['market_price'].notna()]),
            'missing': len(processed_trades[(processed_trades['bloomberg_symbol'].notna()) & 
                                          (processed_trades['market_price'].isna())])
        },
        'sod_positions': len(processed_trades[processed_trades['is_sod'] == True]),
        'expiry_trades': len(processed_trades[processed_trades['is_expiry'] == True])
    }
    
    # Save outputs
    os.makedirs(output_dir, exist_ok=True)
    
    # Save processed trades
    output_csv = os.path.join(output_dir, f"phase1_integration_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    processed_trades.to_csv(output_csv, index=False)
    
    # Save summary (convert numpy int64 to int for JSON serialization)
    summary_json = os.path.join(output_dir, f"phase1_summary_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    summary_serializable = json.loads(json.dumps(summary, default=int))
    with open(summary_json, 'w') as f:
        json.dump(summary_serializable, f, indent=2)
    
    return summary

def main():
    """Run Phase 1 integration test."""
    
    print("=" * 80)
    print("Phase 1 Integration Test - With Fixed Symbol Translator")
    print("=" * 80)
    
    # File paths
    trade_file = "data/input/trade_ledger/trades_20250714.csv"
    price_directory = "data/input/market_prices/options"
    output_dir = "data/output/integration_test"
    
    # Step 1: Process trades with symbol translation
    processed_trades = process_trades_with_translation(trade_file)
    
    # Show sample translations
    print("\nSample Symbol Translations:")
    sample = processed_trades[['instrumentName', 'bloomberg_symbol', 'validation_status']].head(5)
    print(sample.to_string())
    
    # Step 2: Look up market prices
    processed_trades = lookup_market_prices(processed_trades, price_directory)
    
    # Show price lookup results
    print("\nPrice Lookup Results:")
    price_summary = processed_trades.groupby('price_source').size()
    print(price_summary)
    
    # Step 3: Generate report
    summary = generate_integration_report(processed_trades, output_dir)
    
    # Print summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Symbol Translation Success: {summary['symbol_translation']['success']}/{summary['total_trades']}")
    print(f"Prices Found: {summary['price_lookup']['found']}/{summary['symbol_translation']['success']}")
    print(f"SOD Positions: {summary['sod_positions']}")
    print(f"Expiry Trades: {summary['expiry_trades']}")
    
    # Success criteria
    translation_rate = summary['symbol_translation']['success'] / summary['total_trades']
    price_rate = summary['price_lookup']['found'] / summary['symbol_translation']['success'] if summary['symbol_translation']['success'] > 0 else 0
    
    print(f"\nTranslation Success Rate: {translation_rate:.1%}")
    print(f"Price Lookup Success Rate: {price_rate:.1%}")
    
    if translation_rate > 0.9 and price_rate > 0.8:
        print("\n✅ Phase 1 Integration Test PASSED!")
    else:
        print("\n❌ Phase 1 Integration Test FAILED - Symbol format alignment needed")
        
        # Show examples of missing prices
        if price_rate < 0.8:
            print("\nExamples of symbols without prices:")
            missing = processed_trades[(processed_trades['bloomberg_symbol'].notna()) & 
                                      (processed_trades['market_price'].isna())]
            if len(missing) > 0:
                print(missing[['bloomberg_symbol', 'price_source']].head(10).to_string())

if __name__ == "__main__":
    main() 