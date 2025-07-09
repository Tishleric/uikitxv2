# Component Factory Usage

## Basic Usage

```python
from lib.components.factory import DashComponentFactory

# Create factory
factory = DashComponentFactory()

# Create components with defaults
table = factory.create_datatable("my-table")
button = factory.create_button("my-button")
grid = factory.create_grid("my-grid")
```

## With Theme

```python
factory = DashComponentFactory(theme=my_theme)
# All components get this theme
```

## Override Defaults

```python
table = factory.create_datatable("my-table", page_size=50, data=my_data)
```

## DataTable in Grid (CTO Request)

```python
# Empty table in grid
grid = factory.create_datatable_in_grid(
    grid_id="dashboard-grid",
    table_id="sales-table"
)

# With width
grid = factory.create_datatable_in_grid(
    grid_id="dashboard-grid",
    table_id="sales-table",
    grid_width={"xs": 12, "md": 8}
)

# Dynamic population via callback
@app.callback(
    Output("sales-table", "data"),
    Input("load-btn", "n_clicks")
)
def load_data(n_clicks):
    return [{"x": 1}, {"x": 2}]
```

## All Available Methods

```python
factory.create_datatable(id, **kwargs)
factory.create_grid(id, **kwargs)
factory.create_button(id, **kwargs)
factory.create_graph(id, **kwargs)
factory.create_container(id, **kwargs)
factory.create_datatable_in_grid(grid_id, table_id, grid_width=None)
factory.create_form_grid(grid_id, form_elements, submit_button_text="Submit")
factory.create_dashboard_layout(container_id, title, sections)
``` 