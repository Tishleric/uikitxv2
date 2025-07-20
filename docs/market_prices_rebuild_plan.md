# Market Prices System Rebuild Plan

## Overview
Complete rebuild of market prices system with centralized symbol translation, preparing for incoming fresh data streams.

## Timeline
- Phase 1-2: Immediate (before fresh data arrives)
- Phase 3-4: Within 2 hours (ready for fresh data)

## Phase 1: Database Reset & Schema Standardization

### Actions
1. Drop existing futures_prices and options_prices tables
2. Recreate with updated schema including Current_Price column
3. Standardize symbol storage to include "Comdty" suffix

### Schema Updates
```sql
-- Futures table
CREATE TABLE futures_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,
    symbol TEXT NOT NULL,  -- Stored as "TYU5 Comdty"
    Current_Price REAL,    -- NEW: From spot risk
    Flash_Close REAL,      -- From 2pm files
    prior_close REAL,      -- From 4pm files
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, symbol)
);

-- Options table  
CREATE TABLE options_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,
    symbol TEXT NOT NULL,  -- Stored as "VBYN25C3 111.750 Comdty"
    Current_Price REAL,    -- NEW: From spot risk
    Flash_Close REAL,      -- From 2pm files
    prior_close REAL,      -- From 4pm files
    expire_dt DATE,
    moneyness REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, symbol)
);
```

## Phase 2: Update Flash/Prior Processors

### CSV Structure Handling
- Futures files: Use PX_LAST_DEC and PX_SETTLE_DEC columns
- Options files: Continue using PX_LAST and PX_SETTLE
- Implement dynamic column detection for robustness

### Code Changes
1. Update futures_processor.py to handle new columns
2. Ensure all symbols stored with "Comdty" suffix
3. No translation needed (already Bloomberg format)

### Testing
- Process existing files from Z:\Trade_Control\Futures and Options
- Verify Flash_Close and prior_close populate correctly

## Phase 3: Integrate Centralized Translator

### Replace SpotRiskSymbolAdapter
1. Import CentralizedSymbolTranslator in spot_risk_price_processor.py
2. Update translation logic to use new translator
3. Handle XCME colon notation (111:75 → 111.750)

### Translation Strategy
```python
# For symbols within CSV date range
translated = translator.translate(xcme_symbol, 'xcme', 'bloomberg')

# For historical symbols (before CSV coverage)
if not translated:
    log_untranslatable_symbol(xcme_symbol)
    continue  # Skip but don't fail
```

### Remove Hard-coded Logic
- Delete hard-coded expiry date mappings
- Delete series mappings
- Rely entirely on CSV-based translation

## Phase 4: Create Unified File Watcher

### Directory Monitoring
```
Z:\Trade_Control\
├── Futures\     (Flash/Prior files)
├── Options\     (Flash/Prior files)  
└── SpotRisk\    (Current price files)
```

### Processing Flow
1. Flash/Prior files → Direct to database (no translation)
2. Spot risk files → Translate → Database
3. All symbols stored with "Comdty" suffix

### Service Features
- Single process monitoring all directories
- Graceful error handling
- Comprehensive logging
- Translation failure tracking

## Implementation Checklist

### Phase 1
- [ ] Backup existing database (optional)
- [ ] Drop futures_prices and options_prices tables
- [ ] Create tables with new schema
- [ ] Update MarketPriceStorage class for Current_Price

### Phase 2  
- [ ] Update futures_processor for new CSV columns
- [ ] Ensure "Comdty" suffix preserved
- [ ] Test with existing Flash/Prior files
- [ ] Verify database population

### Phase 3
- [ ] Replace SpotRiskSymbolAdapter with CentralizedSymbolTranslator
- [ ] Remove hard-coded mappings
- [ ] Add translation failure logging
- [ ] Test with sample spot risk data

### Phase 4
- [ ] Create unified file watcher service
- [ ] Test all data sources
- [ ] Deploy and monitor
- [ ] Verify fresh data flows correctly

## Success Metrics

1. **Database Health**
   - Tables created with proper schema
   - Historical Flash/Prior data loaded
   - Symbols stored consistently

2. **Translation Accuracy**
   - Fresh symbols translate correctly
   - Historical symbols logged but don't break flow
   - No hard-coded logic remains

3. **System Robustness**
   - Handles CSV structure variations
   - Continues processing despite individual failures
   - Comprehensive error logging

## Risk Management

### Known Risks
1. Historical symbols outside CSV coverage
2. CSV structure variations
3. Translation failures for edge cases

### Mitigation Strategies
1. Log but don't fail on untranslatable symbols
2. Dynamic column detection
3. Comprehensive error tracking for manual review

## Post-Implementation

### Monitoring
- Watch logs for translation failures
- Track Current_Price population rate
- Monitor for any symbol mismatches

### Future Enhancements
- Historical symbol mapping (if needed)
- Translation cache for performance
- Automated error resolution 