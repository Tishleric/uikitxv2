# IO Schema - UIKitX v2

| Name | Kind | Type | Allowed values / range | Example Usage |
|------|------|------|------------------------|---------------|
| Button.label | Input | str | Any string | Button("Submit") |
| ComboBox.options | Input | list[str] | Non-empty list of strings | ComboBox(["Option 1", "Option 2"]) |
| ComboBox.placeholder | Input | str | Any string | ComboBox([], placeholder="Select...") |
| Graph.figure | Input | plotly.graph_objects.Figure | Valid Plotly figure | Graph(go.Figure()) |
| Grid.components | Input | list[UIComponent] | List of wrapped UI components | Grid([button, dropdown]) |
| ListBox.options | Input | list[str] | Non-empty list of strings | ListBox(["Item 1", "Item 2"]) |
| ListBox.values | Input | list[str] | Subset of options | ListBox(options, values=["Item 1"]) |
| RadioButton.options | Input | list[str] | Non-empty list of strings | RadioButton(["Yes", "No"]) |
| RadioButton.value | Input | str | One of the provided options | RadioButton(options, value="Yes") |
| Tabs.items | Input | list[tuple[str, UIComponent]] | List of (label, component) tuples | Tabs([("Tab1", button)]) |
