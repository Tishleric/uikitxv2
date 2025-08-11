# FIFO P&L Calculation Test Suite

## Overview

This test suite validates the correctness of FIFO (First-In-First-Out) realized and unrealized P&L calculations in the trading system.

## Test Structure

### 1. Unit Tests (`test_fifo_pnl_calculations.py`)

Tests core calculation logic in isolation:

#### Realized P&L Tests
- **test_basic_long_realized_pnl**: Buy then Sell scenario
- **test_basic_short_realized_pnl**: Sell then Buy scenario  
- **test_partial_fill_realized_pnl**: Partial position closing
- **test_fifo_ordering**: Validates oldest positions are matched first

#### Unrealized P&L Tests
- **test_pmax_logic_today_trade**: Uses actual price for today's trades
- **test_pmax_logic_yesterday_trade**: Uses SOD price for overnight positions
- **test_unrealized_pnl_before_2pm**: SOD Today as intermediate price
- **test_unrealized_pnl_after_2pm**: SOD Tomorrow as intermediate price
- **test_short_position_unrealized_pnl**: Inverted P&L for shorts
- **test_close_pnl_calculation**: Using close prices vs live prices

#### Complex Scenarios
- **test_mixed_positions_realized_unrealized**: Multiple trades with both P&L types

### 2. Integration Tests (`test_fifo_pnl_integration.py`)

Tests the complete flow with database and positions aggregator:

- **test_full_trade_to_positions_flow**: Trade → Realized P&L → Positions table
- **test_live_vs_close_pnl**: Comparison of live and close P&L values
- **test_price_update_triggers_recalculation**: Price changes update unrealized P&L
- **test_multiple_symbols_isolation**: P&L calculations isolated by symbol

## Running the Tests

### Run All Tests
```bash
python scripts/run_fifo_pnl_tests.py
```

### Run Only Unit Tests
```bash
python scripts/run_fifo_pnl_tests.py unit
```

### Run Only Integration Tests
```bash
python scripts/run_fifo_pnl_tests.py integration
```

### Run Individual Test Files
```bash
# Unit tests
python -m pytest tests/test_fifo_pnl_calculations.py -v

# Integration tests  
python -m pytest tests/integration/test_fifo_pnl_integration.py -v
```

## Test Data Examples

### Realized P&L Calculation
```
Buy 10 @ 112.50
Sell 10 @ 112.75
Realized P&L = (112.75 - 112.50) × 10 × 1000 = $2,500
```

### Unrealized P&L Calculation (Before 2pm)
```
Position: Long 10 @ 112.50
SOD Today: 112.55
Current Price: 112.70

Unrealized P&L = [(112.55 - 112.50) + (112.70 - 112.55)] × 10 × 1000
                = [0.05 + 0.15] × 10 × 1000 = $2,000
```

## Key Concepts Tested

1. **FIFO Matching**: Oldest positions are closed first
2. **Pmax Logic**: Entry price determination for overnight positions
3. **Time-Based Calculations**: Different formulas before/after 2pm Chicago
4. **Short Position Inversion**: P&L is inverted for short positions
5. **Live vs Close P&L**: Real-time vs official close price calculations

## Adding New Tests

When adding new test cases:

1. Follow the existing naming convention: `test_<scenario>_<expected_outcome>`
2. Use helper methods for common operations (creating trades, inserting prices)
3. Include clear comments explaining the calculation logic
4. Test both positive and negative scenarios
5. Verify edge cases (zero quantities, same entry/exit prices, etc.)

## Debugging Failed Tests

If tests fail:

1. Check the assertion messages for expected vs actual values
2. Verify price setup matches the scenario
3. Ensure time mocking is working correctly for time-based tests
4. Check database state using the test's connection object
5. Add print statements to trace calculation steps

## Test Database

Tests use temporary SQLite databases that are:
- Created fresh for each test
- Populated with minimal required data
- Cleaned up automatically after tests complete

This ensures tests are isolated and repeatable.