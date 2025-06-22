# Dashboard Greek Profile Enhancement Plan

## Executive Summary
This document outlines the plan for enhancing the Bond Future Options dashboard with advanced Greek profile visualizations from `bachelier_greek.py`.

## Current State
- Dashboard displays 11 Greeks in a 4x3 grid (lines 970-1150 in app.py)
- All Greeks now use the new bachelier_greek.py calculations
- Visualization code has been refactored into data generation functions

## Proposed UI Enhancements

### 1. Greek Profile Tab
**Location**: New sub-tab within Greek Analysis section

**Components**:
- **Greek Profiles Chart**: Interactive Plotly line chart showing all Greeks vs Forward Price
  - X-axis: Forward Price range (user adjustable)
  - Y-axis: Greek values
  - Multiple lines for each Greek
  - Toggle switches to show/hide specific Greeks
  - Hover tooltips with exact values

- **Analytical vs Numerical Comparison**:
  - Side-by-side charts comparing analytical and numerical Greeks
  - Error metrics displayed below
  - Color coding: Blue (analytical), Red (numerical)

### 2. Taylor Approximation Analysis
**Location**: Separate collapsible section

**Components**:
- **Summary Table**: DataFrame showing Taylor approximation accuracy
- **Error Chart**: Line chart of Taylor errors across strike range
- **Controls**: Sliders for dF, dSigma, dTau parameters

### 3. Greek Sensitivity Heatmap
**Location**: Below Greek profiles

**Components**:
- **2D Heatmap**: Greek values across strike/volatility grid
- **Greek Selector**: Dropdown to choose which Greek to display
- **Color Scale**: Diverging color scheme (red/blue)
- **Interactive**: Click to see detailed values

## Implementation Details

### Phase 1: Data Integration (30 mins)
```python
# In app.py, add import
from lib.trading.bond_future_options.bachelier_greek import (
    generate_greek_profiles_data,
    generate_taylor_summary_data,
    generate_taylor_error_data
)

# Add callback for Greek profiles
@app.callback(
    Output("greek-profiles-graph", "figure"),
    [Input("strike-slider", "value"),
     Input("volatility-slider", "value"),
     Input("time-slider", "value")]
)
def update_greek_profiles(K, sigma, tau):
    data = generate_greek_profiles_data(K=K, sigma=sigma, tau=tau)
    # Convert to Plotly figure
    return create_greek_profiles_figure(data)
```

### Phase 2: UI Components (45 mins)
```python
# Add to Greek Analysis layout
dbc.Tabs([
    dbc.Tab(label="Current Greeks", tab_id="current-greeks"),
    dbc.Tab(label="Greek Profiles", tab_id="greek-profiles"),
], id="greek-tabs"),

# Greek Profiles tab content
dbc.TabContent([
    dbc.Row([
        dbc.Col([
            html.H5("Greek Profiles vs Forward Price"),
            wcc.Graph(id="greek-profiles-graph"),
        ], width=8),
        dbc.Col([
            html.H5("Controls"),
            html.Label("Strike (K)"),
            dcc.Slider(id="strike-slider", min=108, max=116, value=112),
            html.Label("Volatility (σ)"),
            dcc.Slider(id="volatility-slider", min=0.5, max=1.0, value=0.75),
            html.Label("Time to Maturity (τ)"),
            dcc.Slider(id="time-slider", min=0.01, max=0.5, value=0.25),
        ], width=4),
    ]),
])
```

### Phase 3: Advanced Features (30 mins)
- Add Greek selector checkboxes
- Implement zoom/pan functionality
- Add export to CSV/PNG buttons
- Create comparison mode (overlay multiple parameter sets)

## UI Layout Mockup

```
┌─────────────────────────────────────────────────────┐
│ Greek Analysis                                      │
├─────────────────────────────────────────────────────┤
│ [Current Greeks] [Greek Profiles] [Taylor Analysis] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────┐  ┌──────────────────┐    │
│  │                     │  │ Controls:        │    │
│  │   Greek Profiles    │  │ K: [──●──────]   │    │
│  │     (Chart)         │  │ σ: [────●────]   │    │
│  │                     │  │ τ: [──●──────]   │    │
│  │                     │  │                  │    │
│  └─────────────────────┘  │ □ Delta          │    │
│                           │ □ Gamma          │    │
│  ┌─────────────────────┐  │ □ Vega           │    │
│  │  Analytical vs      │  │ □ Theta          │    │
│  │   Numerical         │  │ ...              │    │
│  └─────────────────────┘  └──────────────────┘    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Benefits
1. **Enhanced Understanding**: Visual representation of how Greeks change across strikes
2. **Model Validation**: Compare analytical vs numerical implementations
3. **Risk Insights**: See sensitivity profiles at a glance
4. **Educational**: Helps traders understand Greek behavior
5. **Interactive**: Real-time parameter adjustments

## Required Components
- Wrapped Graph components (already available)
- Slider inputs for parameters
- Checkbox group for Greek selection
- Tab navigation
- Collapsible panels

## Testing Plan
1. Verify data generation functions return correct format
2. Test UI responsiveness with parameter changes
3. Validate Greek calculations match expectations
4. Performance test with large data ranges
5. Cross-browser compatibility

## Timeline
- Data Integration: 30 minutes
- Basic UI Implementation: 45 minutes  
- Advanced Features: 30 minutes
- Testing & Polish: 30 minutes
- **Total**: ~2.5 hours

## Next Steps
1. Get approval on UI layout
2. Implement data integration layer
3. Build UI components incrementally
4. Test with real market data
5. Deploy to production dashboard 