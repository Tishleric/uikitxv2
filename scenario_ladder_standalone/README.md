# Scenario Ladder - Standalone Application

A real-time trading ladder visualization tool for TT (Trading Technologies) that displays working orders, projected P&L, and position risk across price levels.

## Overview

The Scenario Ladder application provides:
- Real-time display of working orders from TT REST API
- Position and P&L projections at different price levels
- Integration with Actant SOD (Start of Day) data for baseline positions
- Spot price integration via Pricing Monkey
- Risk and breakeven calculations

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows OS (required for Pricing Monkey integration via pywinauto)
- Trading Technologies account with API access

### Setup Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure TT API credentials:**
   - Edit `lib/trading/tt_api/config.py`
   - Update the following values with your credentials:
     ```python
     TT_API_KEY = "your-api-key"
     TT_API_SECRET = "your-api-secret"
     # Or for SIM environment:
     TT_SIM_API_KEY = "your-sim-api-key"  
     TT_SIM_API_SECRET = "your-sim-api-secret"
     ```
   - Set `ENVIRONMENT = "SIM"` or `"UAT"` or `"LIVE"` as appropriate

3. **Prepare data files (optional):**
   - Place your Actant SOD CSV file in `data/input/sod/`
   - The application will look for `SampleSOD.csv` by default

## Running the Application

```bash
python run_scenario_ladder.py
```

The application will start on `http://127.0.0.1:8053`

## File Structure

### Main Application
- `run_scenario_ladder.py` - Main application entry point with Dash server and callbacks

### Libraries (`lib/`)

#### Components (`lib/components/`)
- **Core Components:**
  - `core/base_component.py` - Base class for all UI components
  - `core/protocols.py` - Protocol definitions for component interfaces
  
- **Basic Components:**
  - `basic/button.py` - Button component wrapper
  
- **Advanced Components:**
  - `advanced/datatable.py` - DataTable component with theming support
  - `advanced/grid.py` - Grid layout component using Bootstrap
  
- **Themes:**
  - `themes/colour_palette.py` - Color definitions and theme configurations

#### Trading Libraries (`lib/trading/`)

- **Ladder Functions:**
  - `ladder/price_formatter.py` - Converts decimal prices to TT bond format (e.g., 110.015625 → "110'005")
  - `ladder/csv_to_sqlite.py` - Utilities for loading CSV data into SQLite databases
  
- **TT API Integration:**
  - `tt_api/config.py` - Configuration file with API credentials and settings
  - `tt_api/token_manager.py` - Handles TT API token acquisition and refresh
  - `tt_api/utils.py` - Helper functions for API requests

### Data Files (`data/`)

- **Input Data:**
  - `input/ladder/my_working_orders_response.json` - Mock data for testing
  - `input/sod/SampleSOD.csv` - Sample Actant SOD data
  
- **Output Data:**
  - `output/ladder/actant_data.db` - SQLite database created from SOD data

## Key Features

### 1. Working Orders Display
- Fetches live working orders from TT API
- Shows buy/sell quantities at each price level
- Color-coded by side (blue for buy, red for sell)

### 2. P&L Projections
- Calculates projected P&L at each price level
- Based on current position and price movements
- Incorporates baseline position from Actant fills

### 3. Position Tracking
- Shows accumulated position at each price level
- Includes both working orders and historical fills

### 4. Risk Calculations
- Displays risk value (position × $15.625)
- Calculates breakeven as P&L / Risk ratio

### 5. Spot Price Integration
- Manual refresh fetches spot price from Pricing Monkey
- Highlights spot price level in the ladder
- All P&L calculations relative to spot

## Configuration Options

### Mock Data Mode
In `run_scenario_ladder.py`, set:
```python
USE_MOCK_DATA = True  # Use mock data instead of live API
```

### Price Constants
Adjust these constants as needed:
```python
BP_DECIMAL_PRICE_CHANGE = 0.0625  # Basis point in decimal
DOLLARS_PER_BP = 62.5  # Dollar value per basis point
```

## Troubleshooting

### Common Issues

1. **Import Errors:**
   - Ensure you're running from the root directory
   - Check that all dependencies are installed

2. **TT API Connection:**
   - Verify API credentials in `config.py`
   - Check that `ENVIRONMENT` matches your credentials
   - Token files are saved as `tt_token_[environment].json`

3. **Pricing Monkey Integration:**
   - Requires Windows OS
   - Browser must be configured to open the PM URL
   - May need to adjust timing constants if UI is slow

4. **No Data Displayed:**
   - Check if you have working orders in TT
   - Verify instrument filters if applicable
   - Check console output for error messages

### Debug Mode
The application prints detailed logs to console including:
- API requests and responses
- Price conversions
- P&L calculations
- Data loading status

## Notes

- The application uses TT's special price format for bonds (e.g., "110'005")
- All prices are converted to decimal for calculations
- P&L is calculated based on basis point movements
- The ladder auto-adjusts range based on working orders and spot price 