"""
Run the Trade Preprocessor with File Watching

This script monitors the trade ledger input directory and automatically
processes files as they are created or modified.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import argparse
import time
from pathlib import Path

from lib.trading.pnl_calculator.trade_file_watcher import TradeFileWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Trade Preprocessor with File Watching')
    parser.add_argument(
        '--input-dir',
        default='data/input/trade_ledger',
        help='Directory to watch for trade files (default: data/input/trade_ledger)'
    )
    parser.add_argument(
        '--output-dir',
        default='data/output/trade_ledger_processed',
        help='Directory for processed files (default: data/output/trade_ledger_processed)'
    )
    parser.add_argument(
        '--process-only',
        action='store_true',
        help='Process existing files and exit (no watching)'
    )
    
    args = parser.parse_args()
    
    # Validate directories
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    
    print(f"\nTrade Preprocessor")
    print("=" * 60)
    print(f"Input directory:  {input_path.absolute()}")
    print(f"Output directory: {output_path.absolute()}")
    print(f"Mode: {'Process only' if args.process_only else 'Watch mode'}")
    print("=" * 60)
    
    # Create watcher
    watcher = TradeFileWatcher(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    if args.process_only:
        # Just process existing files
        print("\nProcessing existing files...")
        watcher.preprocessor.process_all_files(args.input_dir)
        print("\nProcessing complete.")
    else:
        # Start watching
        try:
            watcher.start()
            print("\nWatching for file changes... (Press Ctrl+C to stop)")
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            watcher.stop()
            print("Stopped.")


if __name__ == "__main__":
    main() 