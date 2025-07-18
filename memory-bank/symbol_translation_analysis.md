# Symbol Translation Analysis

## Overview
Multiple symbol translation systems exist in the codebase, creating potential for inconsistency and maintenance burden.

## Symbol Translators Found

### 1. `lib/trading/symbol_translator.py`
- **Purpose**: General-purpose symbol translation between systems
- **Formats**: Bloomberg ↔ Actant ↔ TT
- **Usage**: Used in various trading modules

### 2. `lib/trading/actant/spot_risk/spot_risk_symbol_translator.py`
- **Purpose**: Specific to Actant spot risk processing
- **Formats**: Actant formats for spot risk calculations
- **Usage**: Spot risk dashboard and calculations

### 3. `lib/trading/treasury_notation_mapper.py`
- **Purpose**: Treasury-specific notation mapping
- **Formats**: Treasury note/bond conventions
- **Usage**: Treasury futures and options

### 4. `lib/trading/fullpnl/symbol_mapper.py`
- **Purpose**: FULLPNL automation specific
- **Formats**: Bloomberg ↔ Actant ↔ vtexp mappings
- **Usage**: FULLPNL table construction

### 5. Hardcoded mappings in `data_sources.py`
- **Location**: `lib/trading/fullpnl/data_sources.py`
- **Purpose**: Contract code to expiry mappings
- **Example**:
  ```python
  CONTRACT_MAPPINGS = {
      '3MN': '18JUL25',    # 3M series
      'VBYN': '21JUL25',   # VBY series  
      'TYWN': '23JUL25',   # TWN series
  }
  ```

## Issues Identified

1. **Duplication**: Similar parsing logic exists in multiple places
2. **Inconsistency**: Different modules may parse the same symbol differently
3. **Maintenance**: Updates need to be made in multiple places
4. **Testing**: Each translator needs separate tests

## Consolidation Strategy

### Short-term (Current)
- Keep existing translators functional
- Document which translator is used where
- Ensure consistency in CONTRACT_MAPPINGS across modules

### Long-term (Recommended)
1. Create a unified `SymbolTranslationService` that:
   - Consolidates all translation logic
   - Provides a single source of truth
   - Supports all required formats
   - Has comprehensive tests

2. Migrate existing modules to use the unified service
3. Deprecate individual translators

## Key Mappings to Preserve

### Bloomberg Contract Codes → Expiries
- 3MN/3M → 18JUL25 (July 18, 2025)
- VBYN/VBY → 21JUL25 (July 21, 2025)
- TYWN/TWN → 23JUL25 (July 23, 2025)

### Strike Notation
- Bloomberg: 110.250 → Actant: 110:25
- Bloomberg: 109.750 → Actant: 109:75

### Instrument Type
- Bloomberg suffix 'P' → PUT
- Bloomberg suffix 'C' → CALL
- No suffix → FUTURE

## Testing Requirements
Any consolidated translator must pass tests for:
- All Bloomberg option formats (3MN5P, VBYN25P3, etc.)
- Fractional strike conversions
- Future symbol parsing
- Round-trip conversions 