# Active Context

## Current Focus
- Integrating Actant-provided position data into the scenario ladder
- Using Actant fills to establish a baseline position and P&L at spot price
- Projecting realistic P&L scenarios based on actual filled positions rather than assuming flat start
- Converting Actant CSV data to SQLite for more robust data handling

## Next Steps
- Connect to real Actant data feed when available
- Refine P&L calculation logic as needed
- Implement option strategy visualization
- Add error handling and recovery for SQLite database operations

## Recent Decisions
- Using `SampleSOD.csv` for simulating Actant fill data
- P&L projections now start from current net position and P&L derived from Actant fills
- Maintaining separation between TT working orders (future orders) and Actant fills (executed orders)
- Using SQLite as a data store for Actant fill data with CSV as the source
- Implementing graceful fallback to direct CSV reading if SQLite operations fail
