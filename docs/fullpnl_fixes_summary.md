# FULLPNL Fixes Summary

## Date: 2025-07-23

### Issues Identified

1. **Market Price Join Failure**
   - Symbol mismatch between positions ("TYU5") and market prices ("TYU5 COMDTY", "TYU5 ", etc.)
   - Result: Unrealized P&L = 0 for all open positions

2. **FIFO Realized P&L Sign Error**
   - Used absolute match_quantity with conditional logic
   - Result: Short covering showed as loss instead of gain

3. **Run Tracking Missing**
   - Many scripts didn't pass run_metadata to TYU5DirectWriter
   - Result: FULLPNL couldn't reliably select latest run

4. **Hard-coded Multiplier**
   - Always used 1000 regardless of instrument type
   - Result: Wrong P&L for instruments with different DV01

5. **Symbol Inconsistencies**
   - No canonical symbol handling across modules
   - Result: Duplicate rows, missed joins

### Fixes Implemented

#### 1. Symbol Canonicalization (`lib/trading/common/symbol_utils.py`)
```python
def canonical(symbol: str) -> str:
    # Strip, uppercase, remove " COMDTY", "XCME." prefix
    # Ensures "TYU5" == "TYU5 COMDTY" == " TYU5 "
```

#### 2. FIFO Sign Fix (`lib/trading/pnl/tyu5_pnl/core/trade_processor.py`)
```python
# OLD: Complex conditional logic with abs(match_quantity)
# NEW: signed_match_qty = match_quantity * pos_sign
#      pnl = signed_match_qty * (exit_price - entry_price) * multiplier
```

#### 3. Market Price Join Fix (`lib/trading/pnl/tyu5_pnl/core/position_calculator.py`)
```python
# Build canonical symbol map first
canonical_price_map = {canonical(symbol): row for row in market_prices}
# Then match positions using canonical form
```

#### 4. Instrument Multipliers (`lib/trading/common/instrument_meta.py`)
```python
MULTIPLIERS = {
    'TY': 1000,  # 10-Year Note
    'TU': 2000,  # 2-Year Note
    'FV': 1000,  # 5-Year Note
    # ... etc
}
```

#### 5. Run Tracking (`lib/trading/pnl_integration/tyu5_direct_writer.py`)
```python
# Made run_metadata optional, auto-generates if missing
def write_results(self, dataframes, run_metadata=None):
    if run_metadata is None:
        run_metadata = {}
    run_id = run_metadata.get('run_id', str(uuid.uuid4()))
```

#### 6. FULLPNL Selection (`lib/trading/pnl_integration/fullpnl_builder.py`)
```python
# Use explicit run_id from tyu5_runs table
def _load_tyu5_positions(self, run_id=None):
    if run_id is None:
        # Get latest from tyu5_runs
    # SELECT WHERE run_id = '{run_id}'
```

### Testing

Created `scripts/test_fullpnl_fixes.py` to validate:
- Symbol canonicalization works
- Run tracking is populated
- P&L calculations are correct
- No duplicate symbols in FULLPNL
- Open positions have non-zero unrealized P&L

### Remaining Work

1. **Quantity in P&L Components**
   - Currently hardcoded to 0 in extract_pnl_components()
   - Need to pass actual lot quantities

2. **Database Constraints**
   - Add UNIQUE(symbol, date, run_id) to prevent duplicates

3. **Integration Testing**
   - Run full pipeline with sample data
   - Compare FULLPNL totals to manual calculations

### Usage

After these fixes, run:
```bash
# Clear and reprocess
python scripts/reset_and_trace_pnl.py

# Or run TYU5 directly
python scripts/run_tyu5_analysis.py

# Build FULLPNL
python -c "from lib.trading.pnl_integration.fullpnl_builder import FULLPNLBuilder; FULLPNLBuilder().build_fullpnl()"

# Check results
python scripts/test_pnl_minimal.py
``` 