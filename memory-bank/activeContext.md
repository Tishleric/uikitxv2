# Active Context & Next Steps

**Current Focus**: Market Prices Enhancement - Current_Price from Spot Risk
**Task**: Add Current_Price column populated from spot risk files
**Status**: ✅ COMPLETE

## Key Achievements (July 18, 2025)
- Added Current_Price column to futures_prices and options_prices tables  
- Created SpotRiskPriceProcessor to extract ADJTHEOR/BID-ASK midpoint
- Integrated with existing SpotRiskFileHandler for automatic updates
- Successfully tested with 57 prices (1 future, 56 options) updated

## Implementation Details
1. **Migration**: Added Current_Price REAL column to both price tables
2. **Price Extraction**: 
   - Primary: ADJTHEOR value from spot risk CSV
   - Fallback: (BID + ASK) / 2 when ADJTHEOR not available
3. **Symbol Translation**: Reused SpotRiskSymbolTranslator for Actant → Bloomberg mapping
4. **Auto-Update**: Hooked into existing file watcher for automatic processing

## Previous Context (M2 Complete)
- ✅ M1 Complete: Symbol mapping and database adapters
- ✅ M2 Complete: Full rebuild working with correct expiry matching
- Created comprehensive verification report
- Documented symbol translation analysis

## Recent Progress
- Automated FULLPNL builder correctly matches options to proper expiries
- Discovered and documented bug in manual scripts (wrong expiry matching)
- Coverage: 100% positions, 75% prices, 62.5% Greeks, 62.5% vtexp
- Missing data explained: strikes 109.5 and 109.75 not in spot risk database

## Key Findings
1. **Automated Builder Correctness**: Our implementation correctly uses contract code mappings:
   - 3MN options → 18JUL25 ✓
   - VBYN options → 21JUL25 ✓
   - TYWN options → 23JUL25 ✓

2. **Manual Script Bug**: Original scripts match all options to 23JUL25 due to:
   - No expiry constraint in query
   - ORDER BY id DESC returns highest ID (which is 23JUL25)
   - This produces incorrect Greeks for 3MN and VBYN options

3. **Symbol Translation**: Identified 5 different symbol translators in codebase
   - Documented in `memory-bank/symbol_translation_analysis.md`
   - Recommend future consolidation into unified service

## Files Created/Updated
- `lib/trading/market_prices/spot_risk_price_processor.py` - New price extraction processor
- `scripts/add_current_price_column.py` - Database migration script
- `scripts/test_spot_risk_price_update.py` - Test and verification script
- `lib/trading/actant/spot_risk/file_watcher.py` - Updated with price processing
- `memory-bank/code-index.md` - Updated documentation 