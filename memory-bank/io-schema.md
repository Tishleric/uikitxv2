# IO Schema - UIKitX v2

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| Button.label | Input | str | Any string | Button("Submit") |
| ComboBox.options | Input | list[str] | Non-empty list of strings | ComboBox(["Option 1", "Option 2"]) |
| ComboBox.placeholder | Input | str | Any string | ComboBox([], placeholder="Select...") |
| DataTable.data | Input | list[dict] | List of dictionaries with consistent keys | DataTable(data=[{"col1": "val1", "col2": "val2"}]) |
| DataTable.columns | Input | list[dict] | List of column configuration dictionaries | DataTable(columns=[{"name": "Column 1", "id": "col1"}]) |
| DataTable.page_size | Input | int | Positive integer | DataTable(page_size=10) |
| Graph.figure | Input | plotly.graph_objects.Figure | Valid Plotly figure | Graph(go.Figure()) |
| Grid.components | Input | list[UIComponent] | List of wrapped UI components | Grid([button, dropdown]) |
| ListBox.options | Input | list[str] | Non-empty list of strings | ListBox(["Item 1", "Item 2"]) |
| ListBox.values | Input | list[str] | Subset of options | ListBox(options, values=["Item 1"]) |
| Mermaid.graph_definition | Input | str | Valid Mermaid syntax | Mermaid().render("diagram-1", "graph TD; A-->B") |
| Mermaid.chart_config | Input | dict | Mermaid configuration options | Mermaid().render(id, graph, chart_config={"theme": "neutral"}) |
| Mermaid.title | Input | str | Any string | Mermaid().render(id, graph, title="Process Diagram") |
| RadioButton.options | Input | list[str] | Non-empty list of strings | RadioButton(["Yes", "No"]) |
| RadioButton.value | Input | str | One of the provided options | RadioButton(options, value="Yes") |
| Tabs.items | Input | list[tuple[str, UIComponent]] | List of (label, component) tuples | Tabs([("Tab1", button)]) |
| TraceCloser.log_label | Input | str | String to identify the trace | @TraceCloser(log_label="endpoint") |
| TraceTime.include_args | Input | bool | True or False | @TraceTime(include_args=True) |
| TraceTime.include_result | Input | bool | True or False | @TraceTime(include_result=True) |
| TraceCpu.sample_interval | Input | float | Positive float (seconds) | @TraceCpu(sample_interval=0.1) |
| TraceMemory.measure_peak | Input | bool | True or False | @TraceMemory(measure_peak=True) |
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

## Import Notes (May 5, 2025)
- All components are imported directly: `from components import Button, ComboBox, etc.`
- All decorators are imported directly: `from decorators import TraceTime, TraceCloser, etc.`
