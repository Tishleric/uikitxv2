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
| RadioButton.options | Input | list[str] | Non-empty list of strings | RadioButton(["Yes", "No"]) |
| RadioButton.value | Input | str | One of the provided options | RadioButton(options, value="Yes") |
| Tabs.items | Input | list[tuple[str, UIComponent]] | List of (label, component) tuples | Tabs([("Tab1", button)]) |
| TraceCloser.log_label | Input | str | String to identify the trace | @TraceCloser(log_label="endpoint") |
| TraceTime.include_args | Input | bool | True or False | @TraceTime(include_args=True) |
| TraceTime.include_result | Input | bool | True or False | @TraceTime(include_result=True) |
| TraceCpu.sample_interval | Input | float | Positive float (seconds) | @TraceCpu(sample_interval=0.1) |
| TraceMemory.measure_peak | Input | bool | True or False | @TraceMemory(measure_peak=True) |

## Import Notes (May 5, 2025)
- All components are imported directly: `from components import Button, ComboBox, etc.`
- All decorators are imported directly: `from decorators import TraceTime, TraceCloser, etc.`
