"""Manually process trades"""
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.storage import PnLStorage

# Initialize
storage = PnLStorage()
preprocessor = TradePreprocessor(storage)

# Drop and recreate tables
print("Dropping tables...")
with storage._get_connection() as conn:
    conn.execute("DROP TABLE IF EXISTS cto_trades")
    conn.execute("DROP TABLE IF EXISTS processed_trades")
    conn.execute("DROP TABLE IF EXISTS trade_processing_tracker")
    conn.execute("DROP TABLE IF EXISTS file_processing_log")
    conn.commit()
    
# Reinitialize
print("Recreating tables...")
storage._initialize_database()

# Process trades
print("Processing trades...")
result = preprocessor.process_trades()
print(f"Processed: {result}") 