# IO Schema - UIKitX v2

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
| Grid.children | Input | list &#124; Any &#124; None | List of components or (component, width_dict) tuples | Grid(id="grid", children=[(Button(id=\'b\'), {'width': 6})]) |
| Grid.className | Input | str | Any string | Grid(id="grid", className="my-grid-layout") |
| Grid.id | Input | str | Unique string | Grid(id="page-layout-grid") |
| Grid.style | Input | dict &#124; None | CSS style dictionary | Grid(id="grid", style={"backgroundColor": "lightgrey"}) |
| Grid.theme | Input | Theme &#124; None | Theme object or None | Grid(id="grid", theme=my_theme) |
| ListBox.className | Input | str | Any string | ListBox(id="lb", className="my-listbox") |
| ListBox.id | Input | str | Unique string | ListBox(id="item-selector") |
| ListBox.multi | Input | bool | True or False | ListBox(id="lb", multi=False) |
| ListBox.options | Input | list[str] &#124; list[dict] | Non-empty list of strings or dicts | ListBox(id="lb", options=["Item A"]) |
| ListBox.style | Input | dict &#124; None | CSS style dictionary | ListBox(id="lb", style={"height": "200px"}) |
| ListBox.theme | Input | Theme &#124; None | Theme object or None | ListBox(id="lb", theme=my_theme) |
| ListBox.value | Input | list[str] &#124; str | Subset of options (list if multi, else str) | ListBox(id="lb", value=["Item A"]) |
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
| Tabs.active_tab | Input | str &#124; None | ID of the initially active tab | Tabs(id="tabs", active_tab="tab-1") |
| Tabs.className | Input | str | Any string | Tabs(id="tabs", className="my-tabs-container") |
| Tabs.id | Input | str | Unique string | Tabs(id="main-app-tabs") |
| Tabs.style | Input | dict &#124; None | CSS style dictionary for the tabs container | Tabs(id="tabs", style={"marginTop": "10px"}) |
| Tabs.tabs | Input | list[tuple[str, Any]] &#124; None | List of (label, component) tuples | Tabs(id="tabs", tabs=[("Tab 1", html.P("Content 1"))]) |
| Tabs.theme | Input | Theme &#124; None | Theme object or None | Tabs(id="tabs", theme=my_theme) |
| TraceTime.include_args | Input | bool | True or False | @TraceTime(log_args=True) |
| TraceTime.include_result | Input | bool | True or False | @TraceTime(log_return=True) |
| PricingMonkey.%Delta | Internal | float | Decimal value (0.0-1.0) | Raw delta values in decimal form (0.125 = 12.5%) |
| MOCK_SPOT_PRICE_STR | Constant | str | TT bond format string | "110'085" for 10-year futures at 110 and 2+5/8 |
| empty_log_tables | Internal | function | N/A | Empties flowTrace and AveragePerformance tables |
| logs-empty-button | Output | int | 0 | Reset n_clicks counter after emptying log tables |
| TT_API_KEY | EnvVar / Config | str | Valid TT API Key | `TT_API_KEY = "your_api_key_here"` (in `TTRestAPI/tt_config.py`) |
| TT_API_SECRET | EnvVar / Config | str | Valid TT API Secret | `TT_API_SECRET = "your_api_secret_here"` (in `TTRestAPI/tt_config.py`) |
| TT_SIM_API_KEY | EnvVar / Config | str | Valid TT API Key for SIM | `TT_SIM_API_KEY = "your_sim_api_key"` (in `TTRestAPI/tt_config.py`) |
| TT_SIM_API_SECRET | EnvVar / Config | str | Valid TT API Secret for SIM | `TT_SIM_API_SECRET = "your_sim_api_secret"` (in `TTRestAPI/tt_config.py`) |
| APP_NAME | EnvVar / Config | str | String, no restricted chars | `APP_NAME = "YourAppName"` (in `TTRestAPI/tt_config.py`) |
| COMPANY_NAME | EnvVar / Config | str | String, no restricted chars | `COMPANY_NAME = "YourCompanyName"` (in `TTRestAPI/tt_config.py`) |
| ENVIRONMENT | EnvVar / Config | str | "UAT", "SIM", "LIVE" | `ENVIRONMENT = "SIM"` (in `TTRestAPI/tt_config.py`) |
| TOKEN_FILE | EnvVar / Config | str | Base filename (e.g., "tt_token.json") | `TOKEN_FILE = "tt_token.json"` (in `TTRestAPI/tt_config.py`). Actual file will be e.g. `tt_token_sim.json`. |
| AUTO_REFRESH | EnvVar / Config | bool | True or False | `AUTO_REFRESH = True` (in `TTRestAPI/tt_config.py`) |
| REFRESH_BUFFER_SECONDS | EnvVar / Config | int | Positive integer (seconds) | `REFRESH_BUFFER_SECONDS = 600` (in `TTRestAPI/tt_config.py`) |

## Logging Configuration Parameters

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| setup_logging.log_level_main | Input | int | e.g., logging.DEBUG, logging.INFO | setup_logging(log_level_main=logging.DEBUG) |
| setup_logging.log_level_console | Input | int | e.g., logging.DEBUG, logging.INFO | setup_logging(log_level_console=logging.WARNING) |
| setup_logging.log_level_db | Input | int | e.g., logging.INFO, logging.ERROR | setup_logging(log_level_db=logging.INFO) |
| setup_logging.db_path | Input | str | Valid file path string | setup_logging(db_path='logs/my_app_logs.db') |
| setup_logging.console_format | Input | str | Python logging format string | setup_logging(console_format='%(asctime)s - %(name)s - %(message)s') |
| setup_logging.date_format | Input | str | strftime format string | setup_logging(date_format='%H:%M:%S') |
| SQLiteHandler.db_filename | Input | str | Valid file path string | SQLiteHandler(db_filename='logs/specific_handler.db') |

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
| default_theme | Constant | Theme | Instance of Theme | The default theme instance (`#000000` based). |

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

## Import Notes (May 5, 2025)
- All components are imported directly: `from components import Button, ComboBox, etc.`
- All decorators are imported directly: `from decorators import TraceTime, TraceCloser, etc.`

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
