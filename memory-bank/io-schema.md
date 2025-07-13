# IO Schema - UIKitX v2

## Import Notes (January 31, 2025)
- All components are imported from the package: `from components import Button, ComboBox, etc.`
- All monitoring utilities are imported from the package: `from monitoring.decorators import TraceTime, TraceCloser, etc.`
- All trading utilities are imported from the package: `from trading.common import format_shock_value_for_display, etc.`
- **PricingMonkey is now imported from trading package**: `from trading.pricing_monkey import run_pm_automation, get_market_movement_data_df, SCENARIOS, etc.`
- Package must be installed first: `pip install -e .`

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| Button.className | Input | str | Any string | Button(id="btn", className="my-button") |
| Button.id | Input | str | Unique string | Button(id="submit-button") |
| Button.label | Input | str | Any string | Button(id="btn", label="Submit") |
| Button.n_clicks | Input | int | Non-negative integer | Button(id="btn", n_clicks=0) |
| Button.style | Input | dict &#124; None | CSS style dictionary | Button(id="btn", style={"color": "red"}) |
| Button.theme | Input | Theme &#124; None | Theme object or None | Button(id="btn", theme=my_theme) |
| ComboBox.className | Input | str | Any string | ComboBox(id="cb", className="my-combo") |
| ComboBox.clearable | Input | bool | True or False | ComboBox(id="cb", clearable=False) |
| ComboBox.id | Input | str | Unique string | ComboBox(id="select-product") |
| ComboBox.multi | Input | bool | True or False | ComboBox(id="cb", multi=True) |
| ComboBox.options | Input | list[str] &#124; list[dict] | Non-empty list of strings or dicts with 'label' and 'value' | ComboBox(id="cb", options=["Opt 1", {"label": "Option 2", "value": "opt2"}]) |
| ComboBox.placeholder | Input | str | Any string | ComboBox(id="cb", placeholder="Select an item...") |
| ComboBox.searchable | Input | bool | True or False | ComboBox(id="cb", searchable=False) |
| ComboBox.style | Input | dict &#124; None | CSS style dictionary | ComboBox(id="cb", style={"width": "200px"}) |
| ComboBox.theme | Input | Theme &#124; None | Theme object or None | ComboBox(id="cb", theme=my_theme) |
| ComboBox.value | Input | str &#124; list[str] &#124; None | Selected value or list of values (if multi) | ComboBox(id="cb", value="opt1") |
| Container.children | Input | list &#124; Any &#124; None | Dash components or list of components | Container(id="cont", children=[html.P("Hello")]) |
| Container.className | Input | str | Any string | Container(id="cont", className="my-container") |
| Container.fluid | Input | bool | True or False | Container(id="cont", fluid=True) |
| Container.id | Input | str | Unique string | Container(id="main-container") |
| Container.style | Input | dict &#124; None | CSS style dictionary | Container(id="cont", style={"padding": "10px"}) |
| Container.theme | Input | Theme &#124; None | Theme object or None | Container(id="cont", theme=my_theme) |
| DataTable.className | Input | str | Any string | DataTable(id="table", className="my-table") |
| DataTable.columns | Input | list[dict] | List of column configuration dictionaries | DataTable(id="table", columns=[{"name": "Column 1", "id": "col1"}]) |
| DataTable.data | Input | list[dict] &#124; pd.DataFrame | List of dictionaries or DataFrame | DataTable(id="table", data=[{"col1": "val1"}]) |
| DataTable.id | Input | str | Unique string | DataTable(id="data-display-table") |
| DataTable.page_size | Input | int | Positive integer | DataTable(id="table", page_size=20) |
| DataTable.style_cell | Input | dict &#124; None | CSS style dictionary for cells | DataTable(id="table", style_cell={"textAlign": "left"}) |
| DataTable.style_data_conditional | Input | list &#124; None | List of conditional style dictionaries | DataTable(id="table", style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}]) |
| DataTable.style_header | Input | dict &#124; None | CSS style dictionary for header | DataTable(id="table", style_header={"fontWeight": "bold"}) |
| DataTable.style_table | Input | dict &#124; None | CSS style dictionary for table container | DataTable(id="table", style_table={"width": "100%"}) |
| DataTable.theme | Input | Theme &#124; None | Theme object or None | DataTable(id="table", theme=my_theme) |
| Graph.className | Input | str | Any string | Graph(id="graph", className="my-graph") |
| Graph.config | Input | dict &#124; None | Plotly config dictionary | Graph(id="graph", config={'displayModeBar': False}) |
| Graph.figure | Input | plotly.graph_objects.Figure | Valid Plotly figure | Graph(id="graph", figure=go.Figure()) |
| Graph.id | Input | str | Unique string | Graph(id="main-plot") |
| Graph.style | Input | dict &#124; None | CSS style dictionary | Graph(id="graph", style={"height": "500px"}) |
| Graph.theme | Input | Theme &#124; None | Theme object or None | Graph(id="graph", theme=my_theme) |
| Grid.children | Input | list &#124; Any &#124; None | List of components or (component, width_dict) tuples | Grid(id="grid", children=[(Button(id='b'), {'width': 6})]) |
| Grid.className | Input | str | Any string | Grid(id="grid", className="my-grid-layout") |
| Grid.id | Input | str | Unique string | Grid(id="page-layout-grid") |
| Grid.style | Input | dict &#124; None | CSS style dictionary | Grid(id="grid", style={"backgroundColor": "lightgrey"}) |
| Grid.theme | Input | Theme &#124; None | Theme object or None | Grid(id="grid", theme=my_theme) |
| ListBox.className | Input | str | Any string | ListBox(id="lb", className="my-listbox") |
| ListBox.id | Input | str | Unique string | ListBox(id="item-selector") |
| ListBox.multi | Input | bool | True or False | ListBox(id="lb", multi=False) |
| ListBox.options | Input | list[dict] | List of {"label": str, "value": any} | `[{"label": "PnL", "value": "pnl"}]` |
| ListBox.style | Input | dict &#124; None | CSS style dictionary | ListBox(id="lb", style={"height": "200px"}) |
| ListBox.theme | Input | Theme &#124; None | Theme object or None | ListBox(id="lb", theme=my_theme) |
| ListBox.value | Input | list[any] | Selected values from options | `["pnl", "dv01"]` |
| Mermaid.chart_config | Input (to render) | dict | Mermaid configuration options | Mermaid().render(id="m", graph_definition="graph TD; A-->B", chart_config={"theme": "forest"}) |
| Mermaid.className | Input (to render) | str | Any string | Mermaid().render(id="m", graph_definition="graph TD; A-->B", className="my-diagram") |
| Mermaid.description | Input (to render) | str &#124; None | Description text for the diagram | Mermaid().render(id="m", graph_definition="graph TD; A-->B", description="My process flow.") |
| Mermaid.graph_definition | Input (to render) | str | Valid Mermaid syntax | Mermaid().render(id="m", graph_definition="graph TD; A-->B") |
| Mermaid.id | Input (to render) | str | Unique string for the rendered component | Mermaid().render(id="process-flow", graph_definition="graph TD; A-->B") |
| Mermaid.style | Input (to render) | dict &#124; None | CSS style dictionary for the container | Mermaid().render(id="m", graph_definition="graph TD; A-->B", style={"border": "1px solid"}) |
| Mermaid.theme | Input (to __init__) | Theme &#124; None | Theme object or None | Mermaid(theme=my_theme) |
| Mermaid.title | Input (to render) | str &#124; None | Title for the diagram | Mermaid().render(id="m", graph_definition="graph TD; A-->B", title="Process Diagram") |
| RadioButton.className | Input | str | Any string | RadioButton(id="rb", className="my-radios") |
| RadioButton.id | Input | str | Unique string | RadioButton(id="mode-selector") |
| RadioButton.inline | Input | bool | True or False | RadioButton(id="rb", inline=True) |
| RadioButton.inputStyle | Input | dict &#124; None | CSS style dictionary for input elements | RadioButton(id="rb", inputStyle={"marginRight": "10px"}) |
| RadioButton.labelStyle | Input | dict &#124; None | CSS style dictionary for label elements | RadioButton(id="rb", labelStyle={"fontWeight": "bold"}) |
| RadioButton.options | Input | list[str] &#124; list[dict] | Non-empty list of strings or dicts | RadioButton(id="rb", options=["Yes", "No"]) |
| RadioButton.style | Input | dict &#124; None | CSS style dictionary for the outer container | RadioButton(id="rb", style={"padding": "5px"}) |
| RadioButton.theme | Input | Theme &#124; None | Theme object or None | RadioButton(id="rb", theme=my_theme) |
| RadioButton.value | Input | str &#124; None | One of the provided options | RadioButton(id="rb", value="Yes") |
| RangeSlider.id | Input | str | any valid HTML id | "shock-range-slider" |
| RangeSlider.min | Input | float | any number | -10.0 |
| RangeSlider.max | Input | float | any number > min | 10.0 |
| RangeSlider.value | Input/Output | List[float] | [min_val, max_val] | [-5.0, 5.0] |
| RangeSlider.step | Input | Optional[float] | positive number | 0.1 |
| RangeSlider.marks | Input | Optional[Dict] | {value: label} mapping | {-5: "-5", 0: "0", 5: "5"} |
| Tabs.active_tab | Input | str &#124; None | ID of the initially active tab | Tabs(id="tabs", active_tab="tab-1") |
| Tabs.className | Input | str | Any string | Tabs(id="tabs", className="my-tabs-container") |
| Tabs.id | Input | str | Unique string | Tabs(id="main-app-tabs") |
| Tabs.style | Input | dict &#124; None | CSS style dictionary for the tabs container | Tabs(id="tabs", style={"marginTop": "10px"}) |
| Tabs.tabs | Input | list[tuple[str, Any]] &#124; None | List of (label, component) tuples | Tabs(id="tabs", tabs=[("Tab 1", html.P("Content 1"))]) |
| Tabs.theme | Input | Theme &#124; None | Theme object or None | Tabs(id="tabs", theme=my_theme) |
| Toggle.id | Input | str | any valid HTML id | "view-mode-toggle" |
| Toggle.value | Input/Output | bool | True/False | False |
| Toggle.label | Input | Optional[str] | any string | "Table View" |
| Toggle.labelPosition | Input | str | "left", "right", "top", "bottom" | "left" |
| Tooltip.id | Input | str | Unique string | Tooltip(id="help-tooltip", target="btn-1", children="Click here for help") |
| Tooltip.target | Input | str &#124; dict | Target element ID or pattern dict | Tooltip(target="my-button") or Tooltip(target={"type": "graph", "index": 0}) |
| Tooltip.children | Input | Any | Tooltip content (string or HTML) | Tooltip(children="This is helpful text") |
| Tooltip.placement | Input | str | "auto", "top", "bottom", "left", "right", etc. | Tooltip(placement="top") |
| Tooltip.delay | Input | dict &#124; None | {"show": ms, "hide": ms} | Tooltip(delay={"show": 500, "hide": 100}) |
| Tooltip.style | Input | dict &#124; None | CSS style dictionary | Tooltip(style={"fontSize": "12px"}) |
| Tooltip.className | Input | str | CSS class names | Tooltip(className="custom-tooltip") |
| Tooltip.theme | Input | Theme &#124; None | Theme object or None | Tooltip(theme=my_theme) |
| TraceTime.include_args | Input | bool | True or False | @TraceTime(log_args=True) |
| TraceTime.include_result | Input | bool | True or False | @TraceTime(log_return=True) |
| shock-amount-listbox.options | Input | list[dict] | List of shock amount option dictionaries | [{"label": "+0.025", "value": 0.025}, {"label": "-0.1", "value": -0.1}] |
| shock-amount-listbox.value | Input | list[float] | List of selected shock amounts | [0.025, -0.1, 0.0] |
| format_shock_value_for_display | Function | Returns: str | value: float, shock_type: str | `from trading.common import format_shock_value_for_display; label = format_shock_value_for_display(-0.25, "percentage")` → "-25.0%" |
| create_shock_amount_options | Function | Returns: List[Dict] | shock_values: List[float], shock_type: Optional[str] | `options = create_shock_amount_options(values, "percentage")` |
| PricingMonkey.%Delta | Internal | float | Decimal value (0.0-1.0) | Raw delta values in decimal form (0.125 = 12.5%) |
| MOCK_SPOT_PRICE_STR | Constant | str | TT bond format string | "110'085" for 10-year futures at 110 and 2+5/8 |
| empty_log_tables | Internal | function | N/A | Empties flowTrace and AveragePerformance tables |
| logs-empty-button | Output | int | 0 | Reset n_clicks counter after emptying log tables |
| TT_API_KEY | EnvVar / Config | str | Valid TT API Key | `from trading.tt_api import TT_API_KEY` |
| TT_API_SECRET | EnvVar / Config | str | Valid TT API Secret | `from trading.tt_api import TT_API_SECRET` |
| TT_SIM_API_KEY | EnvVar / Config | str | Valid TT API Key for SIM | `from trading.tt_api import TT_SIM_API_KEY` |
| TT_SIM_API_SECRET | EnvVar / Config | str | Valid TT API Secret for SIM | `from trading.tt_api import TT_SIM_API_SECRET` |
| APP_NAME | EnvVar / Config | str | String, no restricted chars | `from trading.tt_api import APP_NAME` |
| COMPANY_NAME | EnvVar / Config | str | String, no restricted chars | `from trading.tt_api import COMPANY_NAME` |
| ENVIRONMENT | EnvVar / Config | str | "UAT", "SIM", "LIVE" | `from trading.tt_api import ENVIRONMENT` |
| TOKEN_FILE | EnvVar / Config | str | Base filename (e.g., "tt_token.json") | `from trading.tt_api import TOKEN_FILE` |
| AUTO_REFRESH | EnvVar / Config | bool | True or False | `from trading.tt_api import AUTO_REFRESH` |
| REFRESH_BUFFER_SECONDS | EnvVar / Config | int | Positive integer (seconds) | `from trading.tt_api import REFRESH_BUFFER_SECONDS` |
| retention_enabled | Input | bool | True/False | `start_observability_writer(retention_enabled=True)` |
| retention_hours | Input | int | > 0 (default: 6) | `RetentionManager(db_path, retention_hours=6)` |
| cleanup_interval | Input | int | > 0 seconds (default: 60) | `RetentionController(manager, cleanup_interval=60)` |
| max_consecutive_errors | Input | int | > 0 (default: 5) | `RetentionController(manager, max_consecutive_errors=5)` |
| process_deleted | Output | int | >= 0 | `process_deleted, data_deleted = manager.cleanup_old_records()` |
| data_deleted | Output | int | >= 0 | `process_deleted, data_deleted = manager.cleanup_old_records()` |

## Logging Configuration Parameters

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| setup_logging.log_level_main | Input | int | e.g., logging.DEBUG, logging.INFO | from monitoring.logging import setup_logging; setup_logging(log_level_main=logging.DEBUG) |
| setup_logging.log_level_console | Input | int | e.g., logging.DEBUG, logging.INFO | setup_logging(log_level_console=logging.WARNING) |
| setup_logging.log_level_db | Input | int | e.g., logging.INFO, logging.ERROR | setup_logging(log_level_db=logging.INFO) |
| setup_logging.db_path | Input | str | Valid file path string | setup_logging(db_path='logs/my_app_logs.db') |
| setup_logging.console_format | Input | str | Python logging format string | setup_logging(console_format='%(asctime)s - %(name)s - %(message)s') |
| setup_logging.date_format | Input | str | strftime format string | setup_logging(date_format='%H:%M:%S') |
| SQLiteHandler.db_filename | Input | str | Valid file path string | from monitoring.logging import SQLiteHandler; SQLiteHandler(db_filename='logs/specific_handler.db') |

## UI Theme Definition

| Name | Kind | Type | Allowed values / range | Description |
|------|------|------|------------------------|-------------|
| Theme | TypeDef | dataclass | N/A | Defines a color theme for UI components. |
| Theme.base_bg | Field | str | Hex color string | Background color for the main application. |
| Theme.panel_bg | Field | str | Hex color string | Background color for panels and component containers. |
| Theme.primary | Field | str | Hex color string | Primary brand/accent color. |
| Theme.secondary | Field | str | Hex color string | Secondary color for UI elements. |
| Theme.accent | Field | str | Hex color string | Accent color for highlighting. |
| Theme.text_light | Field | str | Hex color string | Light text color. |
| Theme.text_subtle | Field | str | Hex color string | Subtle/muted text color. |
| Theme.danger | Field | str | Hex color string | Color for errors/dangerous actions. |
| Theme.success | Field | str | Hex color string | Color for success/completion. |
| default_theme | Constant | Theme | Instance of Theme | from components.themes import default_theme |

## Logging Database Schema

### `flowTrace` Table

| Column | Type | Description |
|--------|------|-------------|
| id     | INTEGER PRIMARY KEY AUTOINCREMENT | Unique row ID |
| timestamp | TEXT NOT NULL | Timestamp of the log event (display format) |
| machine | TEXT NOT NULL | Machine identifier |
| user    | TEXT NOT NULL | User identifier |
| level   | TEXT NOT NULL | Log level (e.g., INFO, ERROR) |
| function| TEXT NOT NULL | Name of the function traced |
| message | TEXT NOT NULL | Detailed log message from TraceCloser |

### `AveragePerformance` Table

| Column | Type | Description |
|--------|------|-------------|
| function_name     | TEXT PRIMARY KEY | Name of the traced function |
| call_count        | INTEGER NOT NULL DEFAULT 0 | Total number of times the function was called |
| error_count       | INTEGER NOT NULL DEFAULT 0 | Number of times the function raised an error |
| avg_duration_s    | REAL NOT NULL DEFAULT 0.0 | Average execution time in seconds |
| avg_cpu_delta     | REAL NOT NULL DEFAULT 0.0 | Average CPU utilization delta (%) |
| avg_memory_delta_mb | REAL NOT NULL DEFAULT 0.0 | Average RSS memory delta in MB |
| last_updated      | TEXT NOT NULL | ISO 8601 timestamp of the last update to this record |

# Input/Output Schema

## Actant Integration

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| `SampleSOD.csv` | Input | CSV file | See CSV format below | Source of Actant fill data for position and P&L calculation |
| `actant_data.db` | Internal | SQLite DB | Contains `actant_sod_fills` table | Database for storing Actant fill data |
| `actant_fills` | Internal | `list[dict]` | List of dicts with `price: float` and `qty: int` keys | `[{'price': 110.203125, 'qty': 10}, {'price': 110.25, 'qty': -5}]` |
| `baseline_results` | Internal | `dict` | Dict with `base_pos: int` and `base_pnl: float` keys | `{'base_pos': 5, 'base_pnl': 125.0}` |
| `baseline-store` | Output | Dash Store | Contains `baseline_results` | Used to persist baseline data between callbacks |
| `baseline-display` | Output | HTML Div | String representation of position and P&L | "Current Position: Long 5, Realized P&L @ Spot: $125.00" |

### Actant CSV Format

The Actant CSV file (`SampleSOD.csv`) must contain these columns:

- `ACCOUNT`: Account identifier
- `UNDERLYING`: Underlying symbol
- `ASSET`: Asset symbol (e.g., "ZN")
- `RUN_DATE`: Date of the data run
- `PRODUCT_CODE`: Product type (e.g., "FUTURE")
- `LONG_SHORT`: Position direction ("L" for long, "S" for short)
- `QUANTITY`: Position size (positive number)
- `PRICE_TODAY`: Entry price in special format (e.g., "110'065") 

### SQLite Database Schema

The SQLite database table `actant_sod_fills` has the same structure as the CSV file:

| Column | Type | Description |
|--------|------|-------------|
| `ACCOUNT` | TEXT | Account identifier |
| `UNDERLYING` | TEXT | Underlying symbol |
| `ASSET` | TEXT | Asset symbol (e.g., "ZN") |
| `RUN_DATE` | TEXT | Date of the data run |
| `PRODUCT_CODE` | TEXT | Product type (e.g., "FUTURE") |
| `LONG_SHORT` | TEXT | Position direction ("L" for long, "S" for short) |
| `QUANTITY` | REAL | Position size (positive number) |
| `PRICE_TODAY` | TEXT | Entry price in special format (e.g., "110'065") |
| Additional columns as in CSV | Varies | Preserves all columns from source CSV |

## Function Parameters

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| `calculate_baseline_from_actant_fills.actant_fills` | Input | `list[dict]` | List of dicts with `price` and `qty` keys | List of Actant fills |
| `calculate_baseline_from_actant_fills.spot_decimal_price` | Input | `float` | Positive float | Current spot price in decimal format |
| `csv_to_sqlite_table.csv_filepath` | Input | `str` | Valid file path | Path to CSV file to load |
| `csv_to_sqlite_table.db_filepath` | Input | `str` | Valid file path | Path to SQLite DB file to create/update |
| `csv_to_sqlite_table.table_name` | Input | `str` | Valid SQLite table name | Name of table to create from CSV |
| `csv_to_sqlite_table.if_exists` | Input | `str` | 'fail', 'replace', 'append' | How to handle existing table (default: 'replace') |
| `load_actant_zn_fills_from_db.db_filepath` | Input | `str` | Valid file path | Path to SQLite DB file to read |
| `load_actant_zn_fills_from_db.table_name` | Input | `str` | Valid SQLite table name | Name of table containing Actant data |
| `query_sqlite_table.columns` | Input | list[str] &#124; None | List of column names to select | query_sqlite_table(columns=['col_a', 'col_b']) |
| `query_sqlite_table.db_filepath` | Input | str | Valid file path | query_sqlite_table(db_filepath='data.db', ...) |
| `query_sqlite_table.query` | Input | str &#124; None | Full SQL query string | query_sqlite_table(query='SELECT * FROM t') |
| `query_sqlite_table.table_name` | Input | str | Valid SQLite table name | query_sqlite_table(table_name='my_table', ...) |
| `query_sqlite_table.where_clause` | Input | str &#124; None | SQL WHERE clause | query_sqlite_table(where_clause='id > 10') |
| `update_data_with_spot_price.base_pnl` | Input | `float` | Any float | Starting P&L at spot price |
| `update_data_with_spot_price.base_position` | Input | `int` | Any integer | Starting position at spot price |

## TT Special Format Price Parsing

The `convert_tt_special_format_to_decimal` function handles TT's special bond price format:

Format: `XXX'YYZZ` where:
- `XXX`: Whole points (e.g., "110")
- `YY`: 32nds (e.g., "06")
- `ZZ`: Optional fraction of 32nd (e.g., "5" for half of 1/32)

## Data Files & Formats

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| `queries.yaml` | Input File | YAML | Key-value pairs: query_name: SQL_string | Loaded by `demo/query_runner.py` |
| `my_working_orders_response.json` | Input File (Mock) | JSON | TT API-like order list (see file) | Mock data for `ladderTest/scenario_ladder_v1.py` |
| `order_enumerations.json` | Input File / Data | JSON | TT API enum mappings (see file) | Reference for TT order field decoding |

## Ladder Test Application Constants

| Name | Kind | Type | Allowed values / range | Description |
|------|------|------|------------------------|-------------|
| PM_URL | Constant | str | URL string | `https://pricingmonkey.com/b/e9172aaf-2cb4-4f2c-826d-92f57d3aea90` (for `scenario_ladder_v1.py`) |
| BP_DECIMAL_PRICE_CHANGE | Constant | float | 0.0625 | Decimal price change for 1 basis point (e.g., for ZN) |
| DOLLARS_PER_BP | Constant | float | 62.5 | Dollar value per basis point movement per contract (e.g., for ZN) |
| PRICING_MONKEY_URL | Constant | str | URL string | `https://pricingmonkey.com/b/a05cfbe3-30cc-4c08-8bde-601051682959` (for `pMoneySimpleRetrieval.py`) |

## PricingMonkey Functions

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| `get_simple_data` | Function | Returns `pd.DataFrame` | N/A | `from trading.pricing_monkey import get_simple_data; df = get_simple_data()` returns a DataFrame with columns: "Trade Amount", "Trade Description", "Strike", "Expiry Date", "Price" |
| `transform_df_to_sod_format` | Function | Input: `pd.DataFrame`, Returns: `list[list[str]]` | DataFrame from `get_simple_data()` | `from trading.pricing_monkey.retrieval.simple_retrieval import transform_df_to_sod_format; sod_rows = transform_df_to_sod_format(df)` transforms raw data to SOD format |
| `save_sod_to_csv` | Function | Input: `list[list[str]]`, `str`, Returns: `str` | SOD rows from `transform_df_to_sod_format()`, filename | `from trading.pricing_monkey.retrieval.simple_retrieval import save_sod_to_csv; path = save_sod_to_csv(sod_rows, "output.csv")` saves SOD data to CSV file |
| `_get_option_asset_and_expiry_date` | Function | Input: `str`, `datetime.datetime`, Returns: `tuple[str, datetime.date]` | Option trade description, current EST datetime | Asset code and expiry date based on the current date and rolling expiries |
| `get_market_movement_data_df` | Function | Returns nested `dict` of DataFrames | N/A | `from trading.pricing_monkey import get_market_movement_data_df; result = get_market_movement_data_df()` returns market movement data structured by underlying and expiry |
| `run_pm_automation` | Function | Input: `list[dict]`, Returns: `list[pd.DataFrame]` | List of option dicts with 'id', 'desc', 'qty', 'phase' | `from trading.pricing_monkey import run_pm_automation; dfs = run_pm_automation([{'id': 0, 'desc': 'My Option', 'qty': 100, 'phase': 1}])` |
| `SCENARIOS` | Constant | dict | Scenario configuration dictionary | `from trading.pricing_monkey import SCENARIOS; print(SCENARIOS['base']['display_name'])` |
| `get_extended_pm_data` | Function | Returns: pd.DataFrame | N/A | `from trading.pricing_monkey import get_extended_pm_data; df = get_extended_pm_data()` returns 9-column extended dataset |
| `PMRetrievalError` | Exception | Custom exception class | N/A | `from trading.pricing_monkey import PMRetrievalError; raise PMRetrievalError("Failed to retrieve data")` |
| `PMSimpleRetrievalError` | Exception | Custom exception class | N/A | `from trading.pricing_monkey import PMSimpleRetrievalError; raise PMSimpleRetrievalError("Simple retrieval failed")` |

### Option Asset Code Logic

The `_get_option_asset_and_expiry_date` function determines the asset code for option instruments based on:

1. **Option ordinal (1st, 2nd, 3rd, etc.)** extracted from the trade description
2. **Current date and time in US/Eastern timezone**
3. **Rolling expiry determination:**
   - Expiry days are Monday, Wednesday, and Friday
   - If the current day is an expiry day and before 3 PM EST, it counts as a potential expiry
   - If the current day is an expiry day and after 3 PM EST, it is skipped 
4. **Weekday to Asset Code mapping:**
   - Monday: `VY`
   - Wednesday: `WY`
   - Friday: `OZN`

## Actant Data Processing

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| INPUT_JSON_FILENAME | Constant | str | Valid filename string | "GE_XCME.ZN_20250521_102611.json" |
| OUTPUT_CSV_FILENAME_TEMPLATE | Constant | str | String with '{}' placeholder | "{}_processed.csv" |
| OUTPUT_DB_FILENAME | Constant | str | Valid filename string | "actant_eod_data.db" |
| DB_TABLE_NAME | Constant | str | Valid SQLite table name | "scenario_metrics" |
| scenario_header | Output | str | Any string identifier | "XCME.ZN", "21MAY25" |
| uprice | Output | float | > 0 | 109.8671875 |
| point_header_original | Output | str | Original shock value string | "-2.5%", "-2" |
| shock_value | Output | float | Any numeric value | -0.025, -2.0 |
| shock_type | Output | str | "percentage" or "absolute_usd" | "percentage" |
| Notional | Output | float | Any numeric value or NaN | 825530865.01 |
| ab_Epsilon | Output | float | Any numeric value or NaN | -289000.00 |
| ab_Th PnL | Output | float | Any numeric value or NaN | 9640839.84 |
| ab_Theta | Output | float | Any numeric value or NaN | 9.58 |
| ab_Vega | Output | float | Any numeric value or NaN | 2.91 |
| ab_WVega | Output | float | Any numeric value or NaN | 0.70 |
| ab_Zeta | Output | float | Any numeric value or NaN | 13552.20 |
| ab_sDeltaPath | Output | float | Any numeric value or NaN | 3661000.00 |
| ab_sGammaPath | Output | float | Any numeric value or NaN | 41254.40 |
| ab_sOEV | Output | float | Any numeric value or NaN | 274324.66 |

## Pricing Monkey Integration

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| PM_EXTENDED_COLUMNS | Constant | list[str] | 9 specific column names | ["Trade Amount", "Trade Description", "Strike", "Expiry Date", "Price", "DV01 Gamma", "Vega", "%Delta", "Theta"] |
| PM_TO_ACTANT_MAPPING | Constant | dict | PM column → Actant column mapping | {"DV01 Gamma": "ab_sGammaPath", "Vega": "ab_Vega", "%Delta": "ab_sDeltaPath", "Theta": "ab_Theta"} |
| get_extended_pm_data | Function | Returns: pd.DataFrame | N/A | `from trading.pricing_monkey.retrieval import get_extended_pm_data; df = get_extended_pm_data()` |
| process_pm_for_separate_table | Function | Input: pd.DataFrame, Returns: pd.DataFrame | PM DataFrame → Actant schema | `from trading.pricing_monkey.processors import process_pm_for_separate_table; transformed = process_pm_for_separate_table(pm_df)` |
| validate_pm_data | Function | Input: pd.DataFrame, Returns: List[str] | Validation error list | `from trading.pricing_monkey.processors import validate_pm_data; errors = validate_pm_data(pm_df)` |
| data_source | Output | str | "Actant" or "PricingMonkey" | Field added to distinguish data origins in unified view |

## ActantEOD Dashboard

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| DEFAULT_JSON_FOLDER | Constant | str | Windows path string | r"Z:\ActantEOD" |
| FALLBACK_JSON_FOLDER | Constant | str | Local directory name | "ActantEOD" |
| JSON_FILE_PATTERN | Constant | str | Glob pattern | "*.json" |
| get_most_recent_json_file | Function | Returns Path &#124; None | N/A | `from trading.actant.eod import get_most_recent_json_file; path = get_most_recent_json_file()` |
| scan_json_files | Function | Returns List[Dict] | N/A | `files = scan_json_files()` returns list of file metadata |
| validate_json_file | Function | Input: Path, Returns: bool | Valid file path | `is_valid = validate_json_file(path)` |
| ActantDataService.load_data_from_json | Function | Input: Path, Returns: bool | Valid JSON file path | `from trading.actant.eod import ActantDataService; service = ActantDataService(); success = service.load_data_from_json(path)` |
| ActantDataService.get_scenario_headers | Function | Returns: List[str] | N/A | `scenarios = service.get_scenario_headers()` |
| ActantDataService.get_shock_types | Function | Returns: List[str] | N/A | `types = service.get_shock_types()` |
| ActantDataService.get_shock_values | Function | Returns: List[float] | N/A | `values = service.get_shock_values()` |
| ActantDataService.get_shock_values_by_type | Function | Returns: List[float] | shock_type: Optional[str] | `values = service.get_shock_values_by_type("percentage")` |
| ActantDataService.get_metric_names | Function | Returns: List[str] | N/A | `metrics = service.get_metric_names()` |
| ActantDataService.get_filtered_data | Function | Returns: pd.DataFrame | Optional filter parameters | `df = service.get_filtered_data(scenarios=['XCME.ZN'], shock_values=[0.025, -0.1])` |
| ActantDataService.load_pricing_monkey_data | Function | Returns: bool | N/A | `success = service.load_pricing_monkey_data()` |
| ActantDataService.get_data_sources | Function | Returns: List[str] | N/A | `sources = service.get_data_sources()` |
| ActantDataService.is_pm_data_loaded | Function | Returns: bool | N/A | `loaded = service.is_pm_data_loaded()` |

## Bond Future Options

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| BondFutureOption.future_dv01 | Input | float | > 0 | `BondFutureOption(future_dv01=0.063, future_convexity=0.002404)` |
| BondFutureOption.future_convexity | Input | float | Any float | `BondFutureOption(future_dv01=0.063, future_convexity=0.002404)` |
| BondFutureOption.yield_level | Input | float | 0.0 - 1.0 | `BondFutureOption(yield_level=0.05)` |
| bachelier_future_option_price | Function | Returns: float | F, K, T, price_volatility, option_type | `price = model.bachelier_future_option_price(110.789, 110.75, 0.0187, 100.0, 'put')` |
| convert_price_to_yield_volatility | Function | Returns: float | price_volatility | `yield_vol = model.convert_price_to_yield_volatility(100.0)` |
| convert_yield_to_future_price_volatility | Function | Returns: float | yield_volatility | `price_vol = model.convert_yield_to_future_price_volatility(1.58)` |
| delta_F | Function | Returns: float | F, K, T, price_volatility, option_type | `delta = model.delta_F(110.789, 110.75, 0.0187, 100.0, 'put')` |
| gamma_F | Function | Returns: float | F, K, T, price_volatility | `gamma = model.gamma_F(110.789, 110.75, 0.0187, 100.0)` |
| vega_price | Function | Returns: float | F, K, T, price_volatility | `vega = model.vega_price(110.789, 110.75, 0.0187, 100.0)` |
| theta_F | Function | Returns: float | F, K, T, price_volatility | `theta = model.theta_F(110.789, 110.75, 0.0187, 100.0)` |
| solve_implied_volatility | Function | Returns: tuple[float, float] | option_model, F, K, T, market_price, option_type | `price_vol, error = solve_implied_volatility(model, 110.789, 110.75, 0.0187, 0.359375, 'put')` |
| calculate_all_greeks | Function | Returns: dict | option_model, F, K, T, price_volatility, option_type | `greeks = calculate_all_greeks(model, 110.789, 110.75, 0.0187, 100.0, 'put')` |
| generate_greek_profiles | Function | Returns: list[dict] | option_model, base_F, K, T, price_volatility, option_type, range_size, step | `profiles = generate_greek_profiles(model, 110.789, 110.75, 0.0187, 100.0, 'put', 20, 1)` |
| analyze_bond_future_option_greeks | Function | Returns: dict | future_dv01, future_convexity, yield_level, F, K, T, market_price, option_type | `results = analyze_bond_future_option_greeks()` |
| greek_scaling_delta_F | Constant | float | 1.0 | delta_F is not scaled (multiplied by 1) |
| greek_scaling_others | Constant | float | 1000.0 | All other Greeks are multiplied by 1000 for display |
| theta_daily_conversion | Constant | float | 252.0 | Theta is divided by 252 for daily decay |
| model | Input | str | Any registered model name | Model version to use for Greek calculations (default: 'bachelier_v1') |
| model_params | Input | dict | Dict with model-specific params | Additional parameters for the selected model |
| model_version | Output | str | Model name and version | Version of model used for calculation (e.g., 'bachelier_v1.0') |
| GREEK_NAME_MAPPING | Constant | dict | Numerical to analytical Greek mapping | `{'delta': 'delta_F', 'vega': 'vega_price', ...}` |
| GREEK_ORDER | Constant | list[str] | Ordered list of Greek names | `['delta_F', 'gamma_F', 'vega_price', 'theta_F', ...]` |
| GREEK_DESCRIPTIONS | Constant | dict | Greek name to description mapping | `{'delta_F': '∂V/∂F - Price sensitivity', ...}` |
| compute_derivatives | Function | Returns: dict[str, float] | f: Callable, F, sigma, t, h_F, h_sigma, h_t | `greeks = compute_derivatives(price_func, 110.789, 6.948, 0.0187)` |
| compute_derivatives_bond_future | Function | Returns: tuple[dict, float] | option_model, F, K, T, price_vol, option_type | `greeks, time = compute_derivatives_bond_future(model, F, K, T, vol, 'put')` |
| h_F (recommended) | Parameter | float | max(0.0001, F * 1e-5) | Balanced step size for price derivatives |
| h_sigma (recommended) | Parameter | float | max(0.00001, sigma * 1e-4) | Balanced step size for volatility derivatives |
| h_t (recommended) | Parameter | float | max(1e-8, t * 1e-5) | Balanced step size for time derivatives |
| format_greek_comparison | Function | Returns: list[dict] | analytical_greeks, numerical_greeks | `table_data = format_greek_comparison(analytical, numerical)` |
| create_error_table | Function | Returns: list[dict] | N/A | `table_data = create_error_table()` returns error table structure |
| numerical-greeks-table | Output | DataTable data | List of Greek comparison rows | DataTable showing analytical vs numerical Greeks |
| GreekCalculatorAPI.analyze | Function | Returns: dict or list[dict] | options_data, model, model_params | `api.analyze(option_data, model='bachelier_v1')` returns Greek results |
| GreekCalculatorAPI.default_model | Input | str | Any registered model name | `GreekCalculatorAPI(default_model='bachelier_v1')` |
| ModelFactory.register | Function | None | model_name, model_class | `ModelFactory.register('bachelier_v2', BachelierV2)` |
| ModelFactory.create | Function | Returns: OptionModelInterface | model_name | `model = ModelFactory.create('bachelier_v1')` |
| ModelFactory.get_available_models | Function | Returns: list[str] | N/A | `models = ModelFactory.get_available_models()` |
| h_F | Input | float | > 0, adaptive default | Finite difference step size for F (default: max(0.01, F*1e-4)) |

## P&L Calculator

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| Trade.timestamp | Input | datetime | Valid datetime | `Trade(timestamp=datetime(2024, 1, 1, 9, 30), symbol='AAPL', quantity=10, price=100.0)` |
| Trade.symbol | Input | str | Non-empty string | `Trade(symbol='AAPL', ...)` |
| Trade.quantity | Input | float | Non-zero value | `Trade(quantity=10, ...)` for buy, `Trade(quantity=-10, ...)` for sell |
| Trade.price | Input | float | >= 0 | `Trade(price=100.0, ...)` |
| Trade.trade_id | Input | Optional[str] | Any string or None | `Trade(trade_id='12345', ...)` |
| Lot.quantity | Input | float | Non-zero value | `Lot(quantity=10, price=100.0, date=date.today())` |
| Lot.price | Input | float | >= 0 | `Lot(price=100.0, ...)` |
| Lot.date | Input | date | Valid date | `Lot(date=date(2024, 1, 1), ...)` |
| PnLCalculator.add_trade | Function | Returns: None | timestamp, symbol, quantity, price, trade_id | `calc.add_trade(datetime.now(), 'AAPL', 10, 100.0)` |
| PnLCalculator.add_market_close | Function | Returns: None | symbol, close_date, close_price | `calc.add_market_close('AAPL', date.today(), 105.0)` |
| PnLCalculator.load_trades_from_csv | Function | Returns: None | csv_path: str | `calc.load_trades_from_csv('data/input/trade_ledger/trades.csv')` |
| PnLCalculator.calculate_daily_pnl | Function | Returns: pd.DataFrame | N/A | `df = calc.calculate_daily_pnl()` |
| PnLCalculator.get_position_summary | Function | Returns: pd.DataFrame | as_of_date: Optional[date] | `summary = calc.get_position_summary(date(2024, 1, 1))` |
| daily_pnl.date | Output | date | Trading dates | DataFrame column containing trading date |
| daily_pnl.symbol | Output | str | Trading symbols | DataFrame column containing symbol |
| daily_pnl.position | Output | float | Any value | Current position (positive=long, negative=short) |
| daily_pnl.avg_cost | Output | float | >= 0 | Average cost basis of position |
| daily_pnl.market_close | Output | float | >= 0 | Market closing price |
| daily_pnl.realized_pnl | Output | float | Any value | P&L from closed positions |
| daily_pnl.unrealized_pnl | Output | float | Any value | P&L from open positions at market price |
| daily_pnl.unrealized_change | Output | float | Any value | Daily change in unrealized P&L |
| daily_pnl.total_daily_pnl | Output | float | Any value | realized_pnl + unrealized_change |
| position_summary.symbol | Output | str | Trading symbols | DataFrame column containing symbol |
| position_summary.position | Output | float | Non-zero value | Current position size |
| position_summary.avg_cost | Output | float | >= 0 | Average cost basis |
| position_summary.market_price | Output | float | >= 0 | Current market price |
| position_summary.market_value | Output | float | Any value | Position value at market price |
| position_summary.unrealized_pnl | Output | float | Any value | Unrealized P&L |
| _process_buy | Internal | Returns: float | symbol, quantity, price, trade_date | Processes buy trades, returns realized P&L |
| _process_sell | Internal | Returns: float | symbol, quantity, price, trade_date | Processes sell trades, returns realized P&L |
| _calculate_position_metrics | Internal | Returns: Tuple[float, float] | symbol | Returns (position, avg_cost) |
| _calculate_unrealized_pnl | Internal | Returns: float | symbol, market_price | Calculates unrealized P&L |

### P&L Calculator Trade CSV Format

The `load_trades_from_csv` method expects a CSV file with the following columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| tradeId | str/int | Unique trade identifier | 1 |
| instrumentName | str | Full instrument name (used as-is for symbol) | XCMEOCADPS20250714N0VY2/108.75 |
| marketTradeTime | str | Trade timestamp | 2025-07-12 13:03:15.000 |
| buySell | str | Trade direction ('B' or 'S') | B |
| quantity | float | Trade quantity (always positive) | 10.0 |
| price | float | Trade price in decimal format | 1.015625 |

### P&L Calculator Usage Examples

```python
from lib.trading.pnl_calculator import PnLCalculator, Trade, Lot

# Create calculator
calc = PnLCalculator()

# Method 1: Load trades from CSV
calc.load_trades_from_csv("data/input/trade_ledger/trades.csv")

# Method 2: Add trades manually
calc.add_trade(datetime(2024, 1, 1), "AAPL", 10, 100.0)  # Buy 10 @ 100
calc.add_trade(datetime(2024, 1, 2), "AAPL", -5, 110.0)  # Sell 5 @ 110

# Add market closes
calc.add_market_close("AAPL", date(2024, 1, 1), 100.0)
calc.add_market_close("AAPL", date(2024, 1, 2), 110.0)

# Calculate daily P&L
df = calc.calculate_daily_pnl()
# Returns DataFrame with columns: date, symbol, position, avg_cost, market_close, 
# realized_pnl, unrealized_pnl, unrealized_change, total_daily_pnl

# Get position summary
summary = calc.get_position_summary(as_of_date=date(2024, 1, 2))
# Returns DataFrame with columns: symbol, position, avg_cost, market_price, 
# market_value, unrealized_pnl
```

## GreekCalculatorAPI Methods

| Name | Kind | Type | Allowed values / range | Example Usage |
