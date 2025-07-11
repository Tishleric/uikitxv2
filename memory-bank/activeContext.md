# Active Context

## Recent Work
- Implemented NET_OPTIONS aggregation functionality for spot risk dashboard
- Added NET_OPTIONS_F and NET_OPTIONS_Y rows to aggregate options Greeks (simple addition)
- Modified dashboard callbacks to filter NET_OPTIONS rows based on Greek space toggle
- Updated tests to verify correct behavior

## Current State
- Spot risk module now creates three NET rows:
  - NET_FUTURES: Sums all futures with positions (always visible)
  - NET_OPTIONS_F: Sums F-space Greeks for options with positions (visible in F-space mode)
  - NET_OPTIONS_Y: Sums Y-space Greeks for options with positions (visible in Y-space mode)
- All aggregations use simple addition (not position-weighted)
- Greek space toggle correctly filters which NET_OPTIONS row is displayed
- Tests passing for all aggregation functionality

## Next Steps
- Monitor performance with real data files containing many positions
- Consider adding expiry-specific aggregates if requested
- Potential enhancement: Add drill-down from NET rows to see contributing positions