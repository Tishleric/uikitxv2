#!/usr/bin/env python3
"""
Run the complete TYU5 pipeline using the new direct writer.
This replaces the old TYU5DatabaseWriter approach.
"""

import time
from datetime import datetime
from lib.trading.pnl_integration.tyu5_runner import TYU5Runner
from lib.trading.pnl_integration.trade_ledger_adapter import TradeLedgerAdapter
from lib.trading.pnl_integration.tyu5_direct_writer import TYU5DirectWriter


def run_tyu5_pipeline():
    """Run the complete TYU5 pipeline with direct database writing."""
    print("="*80)
    print("TYU5 Pipeline - Direct Database Writer")
    print("="*80)
    print(f"Start time: {datetime.now().isoformat()}")
    
    # Track execution time
    start_time = time.time()
    
    try:
        # Step 1: Get input data
        print("\n1. Loading trade data from CSV...")
        adapter = TradeLedgerAdapter()
        data_dict = adapter.prepare_tyu5_data()
        trades_df = data_dict['Trades_Input']
        market_prices_df = data_dict.get('Market_Prices')
        
        print(f"   - Loaded {len(trades_df)} trades")
        print(f"   - Loaded {len(market_prices_df) if market_prices_df is not None else 0} market prices")
        
        # Step 2: Run TYU5 calculations
        print("\n2. Running TYU5 P&L calculations...")
        runner = TYU5Runner()
        result = runner.run_with_capture(
            trades_df=trades_df,
            market_prices_df=market_prices_df,
            debug=False  # Set to True for debug logs in Excel
        )
        
        print(f"   - Generated Excel: {runner.output_file}")
        
        # Step 3: Write to database
        print("\n3. Writing results to database...")
        writer = TYU5DirectWriter()
        
        # Calculate execution time
        calc_time = time.time() - start_time
        
        # Prepare metadata
        run_metadata = {
            'excel_file_path': runner.output_file,
            'execution_time_seconds': calc_time
        }
        
        # Write to database
        success, error = writer.write_results(result, run_metadata)
        
        if success:
            print("   ✓ Database write successful")
            
            # Get run info
            latest_run = writer.get_latest_run()
            if latest_run:
                print(f"\n4. Run Summary:")
                print(f"   - Run ID: {latest_run['run_id']}")
                print(f"   - Status: {latest_run['status']}")
                print(f"   - Trades: {latest_run['trades_count']}")
                print(f"   - Positions: {latest_run['positions_count']}")
                if latest_run['total_pnl'] is not None:
                    print(f"   - Total P&L: ${latest_run['total_pnl']:,.2f}")
                print(f"   - Execution time: {latest_run['execution_time_seconds']:.2f} seconds")
        else:
            print(f"   ✗ Database write failed: {error}")
            return False
            
        # Total time
        total_time = time.time() - start_time
        print(f"\nTotal pipeline time: {total_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"\nERROR in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n" + "="*80)
        print(f"End time: {datetime.now().isoformat()}")


if __name__ == "__main__":
    success = run_tyu5_pipeline()
    exit(0 if success else 1) 