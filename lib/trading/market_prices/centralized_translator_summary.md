# Centralized Symbol Translator

## Overview
A robust, CSV-based symbol translation system that replaces complex regex patterns with simple lookups. Uses `ExpirationCalendar_CLEANED.csv` as the single source of truth for symbol mappings.

## Components

### 1. Strike Converter (`strike_converter.py`)
Handles the unique XCME colon notation for fractional strikes:
- `111` → 111.000
- `111:25` → 111.250  
- `111:5` → 111.500 (special case: :5 means .50)
- `111:75` → 111.750

### 2. Centralized Symbol Translator (`centralized_symbol_translator.py`)
Main translation engine that:
- Parses symbols from any format (XCME, CME, Bloomberg)
- Looks up mappings in the cleaned CSV
- Reconstructs symbols with proper formatting

### 3. Symbol Formats

**XCME Format:**
```
XCME.{BASE}.{EXPIRY}.{STRIKE}.{TYPE}
Example: XCME.VY3.21JUL25.111:75.C
```

**CME Format:**
```
{BASE} {TYPE}{STRIKE_INT}
Example: VY3N5 C11175
```

**Bloomberg Format:**
```
{BASE_WITH_TYPE} {STRIKE} Comdty
Example: VBYN25C3 111.750 Comdty
```

### 4. Symbol Classifications
- **Weekly Mon-Thu**: VY3, GY4, WY4, HY4 (Monday-Thursday)
- **Weekly Friday**: ZN1, ZN2, ZN3, ZN4, ZN5 (1st-5th Friday)
- **Quarterly**: OZN (quarterly expirations)

## Key Features

### 1. Bidirectional Translation
Supports translation between any two formats:
- XCME ↔ Bloomberg
- CME ↔ Bloomberg  
- XCME ↔ CME

### 2. Strike Format Handling
- Automatically converts between XCME colon notation and decimal
- Formats strikes appropriately for each system
- Handles all fractional strike variations

### 3. Option Type Handling
- Bloomberg embeds option type in the base symbol
- Separate Bloomberg_Call and Bloomberg_Put columns in CSV
- Automatic selection based on option type during translation

### 4. Error Handling
- Graceful handling of unknown symbols
- Clear error messages for debugging
- Returns None for unmapped symbols rather than crashing

## Usage Example

```python
from lib.trading.market_prices.centralized_symbol_translator import CentralizedSymbolTranslator

translator = CentralizedSymbolTranslator()

# XCME to Bloomberg
result = translator.translate(
    "XCME.VY3.21JUL25.111:75.C",
    "xcme",
    "bloomberg"
)
# Result: "VBYN25C3 111.750 Comdty"

# Bloomberg to XCME
result = translator.translate(
    "VBYN25C3 111.750 Comdty",
    "bloomberg", 
    "xcme"
)
# Result: "XCME.VY3.21JUL25.111:75.C"
```

## CSV Structure

The cleaned CSV contains base symbols only (strikes and option types removed):
- **Option Symbol**: CME option symbol (e.g., VY3N5)
- **Bloomberg_Call**: Bloomberg call symbol base (e.g., VBYN25C3)
- **Bloomberg_Put**: Bloomberg put symbol base (e.g., VBYN25P3)
- **CME**: CME base symbol (e.g., VY3N5)
- **XCME**: XCME base symbol (e.g., XCME.VY3.21JUL25)

## Testing

Comprehensive test suite covers:
- All strike format variations
- All symbol types (weekly Mon-Thu, Friday, quarterly)
- Round-trip translations
- Edge cases and error handling
- Real database symbols

Run tests with:
```bash
python scripts/test_centralized_translator.py
```

## Benefits

1. **Simplicity**: No complex regex patterns to maintain
2. **Accuracy**: Single source of truth prevents inconsistencies
3. **Maintainability**: Easy to update by modifying CSV
4. **Performance**: Fast dictionary lookups instead of regex matching
5. **Extensibility**: Easy to add new symbols or formats 