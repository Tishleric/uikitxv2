# Future Enhancements

## Spot Risk Database Service Layer

### Overview
Comprehensive database service design for future implementation when CSV backend needs upgrading.

### Architecture
```
SpotRiskDatabaseService
├── Connection Management
│   ├── Context manager for connections
│   ├── Automatic retry on lock errors
│   └── Proper transaction handling
│
├── Session Management
│   ├── create_session() → session_id
│   ├── update_session_status()
│   └── get_active_session()
│
├── Raw Data Operations
│   ├── insert_raw_data(df, session_id)
│   ├── get_raw_data(session_id)
│   └── delete_old_raw_data(days_to_keep)
│
├── Calculated Data Operations  
│   ├── insert_calculated_greeks(results, session_id)
│   ├── get_latest_calculations()
│   └── get_calculation_history(instrument_key)
│
└── Query Operations (for UI)
    ├── get_filtered_data(filters)
    ├── get_unique_expiries()
    ├── get_strike_range()
    └── export_to_dataframe(session_id)
```

### Key Features
- SQLite with WAL mode for concurrent access
- Batch operations for performance
- JSON serialization for raw data
- Comprehensive error handling
- Transaction safety
- Query optimization with indexes

### Integration Points
1. Pipeline: Optional storage after Greek calculation
2. UI: Replace CSV loading with database queries
3. Auto-refresh: Use sessions for incremental updates

### Benefits
- Historical data retention
- Multi-session support
- Crash recovery
- Performance with large datasets
- Concurrent user access

*Note: Database schema already created in schema.sql and spot_risk.db exists.* 