# TYU5 P&L Integration

This module provides integration between UIKitXv2 and the TYU5 P&L calculation engine.

## Recommended Data Flow: CSV → DataFrame → TYU5

The primary and recommended method for running TYU5 calculations is through the **TYU5Runner** class, which accepts pandas DataFrames directly:

```python
from lib.trading.pnl_integration.tyu5_runner import TYU5Runner
import pandas as pd

# 1. Load your trade data from CSV
trades_df = pd.read_csv('path/to/trades.csv')

# 2. Transform to TYU5 format (example)
trades_input = pd.DataFrame({
    'Date': trades_df['trade_date'],
    'Time': trades_df['trade_time'],
    'Symbol': trades_df['symbol'],
    'Action': trades_df['side'].map({'B': 'BUY', 'S': 'SELL'}),
    'Quantity': trades_df['quantity'].abs(),
    'Price': trades_df['price'],
    'Fees': trades_df['fees'],
    'Counterparty': trades_df['counterparty'],
    'Type': trades_df['instrument_type']  # 'FUT', 'CALL', or 'PUT'
})

# 3. Load market prices (optional)
market_prices = pd.DataFrame({
    'Symbol': ['TYH5'],
    'Current_Price': ['119-240'],
    'Prior_Close': ['119-220'],
    'Flash_Close': ['119-230']
})

# 4. Run TYU5
runner = TYU5Runner()
result = runner.run_with_capture(
    trades_input=trades_input,
    market_prices=market_prices,
    output_file='output/tyu5_results.xlsx'
)

# 5. Access results
if result['status'] == 'SUCCESS':
    positions_df = result['positions_df']
    summary_df = result['summary_df']
    print(f"Total P&L: {summary_df['Value'].iloc[0]}")
```

## Key Components

### TYU5Runner (Recommended)
- **Purpose**: Primary interface for running TYU5 calculations
- **Input**: Pandas DataFrames
- **Output**: Dictionary of result DataFrames + Excel file
- **Benefits**: No database dependencies, direct CSV support

### TradeLedgerAdapter
- **Purpose**: Helper for reading and transforming trade ledger CSV files
- **Use Case**: When you need help transforming legacy CSV formats

### TYU5Adapter (Deprecated)
- **Purpose**: Reads from cto_trades database table
- **Status**: Being phased out in favor of direct DataFrame input
- **Note**: Still functional but not recommended for new implementations

## Missing Price Data Handling

When market prices are not available, TYU5 will display "awaiting data" instead of calculated P&L values. This prevents misleading calculations based on stale or incorrect price data.

## Database Writing (Optional)

Results can optionally be persisted to database using TYU5DatabaseWriter:

```python
from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter

db_writer = TYU5DatabaseWriter()
db_writer.write_results(
    trades_df=result['trades_df'],
    positions_df=result['positions_df'],
    summary_df=result['summary_df'],
    risk_df=result['risk_df'],
    breakdown_df=result['breakdown_df']
)
```

## Migration from cto_trades

If you're currently using the cto_trades table:

1. Export your data to CSV or load directly from source CSV files
2. Transform to TYU5 format as shown above
3. Use TYU5Runner instead of TYU5Adapter
4. Remove dependencies on TradePreprocessor for TYU5 calculations 