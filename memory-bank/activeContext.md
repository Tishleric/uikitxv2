# Active Context

## Current State (January 21, 2025)
Working on Spot Risk dashboard Greek profile functionality. Successfully implemented position filtering, basic Greek profiles, and now Greek profiles by expiry are fully functional.

### Completed Today
1. ✅ Fixed position filtering bug (column name was 'pos.position' not 'POS.POSITION')
2. ✅ Fixed graph display structural issue (graph container was nested inside table container)
3. ✅ Fixed Greek profiles by expiry - COMPLETE multi-step fix:
   - Fixed column detection ('expiry_date' not 'expiry')
   - Added missing 'current_greeks' field to position data
   - Created mapping from Greek names to actual CSV column names
   - Added fallback logic for alternative column names

### Greek Profiles by Expiry - FULLY FIXED
The method now correctly:
- Detects 'expiry_date' column in the CSV data
- Groups positions by expiry date
- Calculates ATM strike for each expiry
- Extracts model parameters using correct columns
- Maps Greek names to actual column names:
  - 'delta' → 'delta_F' (or 'delta_y' as fallback)
  - 'gamma' → 'gamma_F' (or 'gamma_y' as fallback)
  - 'vega' → 'vega_price' (or 'vega_y' as fallback)
  - 'theta' → 'theta_F'
  - Plus mappings for all higher-order Greeks
- Includes current Greek values in position hover text
- Generates separate Greek profiles for each expiry with proper headers

### Technical Achievement
Successfully resolved a complex multi-layer issue involving:
1. Column name mismatches between expected and actual CSV columns
2. Data structure inconsistencies between single and by-expiry methods
3. Greek naming convention differences between UI selections and data columns

The dashboard now displays Greek profiles organized by expiry date with full functionality including position markers with Greek value tooltips.

### CSV Parser Bug Fix (January 21, 2025)
**Issue**: Greek calculations were failing with "No valid future price found" error when processing new spot risk CSV files.

**Root Cause**: The parser in `lib/trading/actant/spot_risk/parser.py` was using `skiprows=[1]` for all CSV files, which was designed to skip a type row in the original format. However, processed CSV files don't have this type row, so it was accidentally skipping the future row (which was on line 2).

**Fix**: Modified parser to conditionally skip rows based on filename:
- If filename contains 'processed', don't skip any rows
- Otherwise, skip row 1 (for original format with type row)

**Result**: Future row with `itype='F'` is now correctly parsed, allowing Greek calculations to find the future price.