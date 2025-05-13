import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
import inspect # To get source code and docstrings

# Helper function to extract class/function source or docstring
def get_source_or_docstring(filepath, entity_name, get_doc=False):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # This is a simplified way to find entities; for complex cases, AST parsing is better.
        # For now, we'll rely on finding the definition block.
        # For docstrings, we can use eval if the structure is simple, but it's risky.
        # Let's try to find the class/function definition and then its docstring.
        
        lines = source_code.splitlines()
        entity_def_start = -1
        docstring_lines = []
        in_docstring = False
        
        if get_doc:
            # Attempt to find docstring for top-level entities
            # This is a basic parser, might not cover all edge cases
            entity_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"class {entity_name}") or \
                   line.strip().startswith(f"def {entity_name}"):
                    entity_found = True
                    # Look for the start of the docstring on the next lines
                    for j in range(i + 1, len(lines)):
                        stripped_line = lines[j].strip()
                        if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                            in_docstring = True
                            # Handle single-line docstring
                            if (stripped_line.endswith('"""') or stripped_line.endswith("'''")) and len(stripped_line) > 3:
                                docstring_lines.append(stripped_line.strip('"""').strip("'''"))
                                in_docstring = False
                                break
                            docstring_lines.append(stripped_line.strip('"""').strip("'''"))
                        elif in_docstring:
                            if stripped_line.endswith('"""') or stripped_line.endswith("'''"):
                                docstring_lines.append(stripped_line.strip('"""').strip("'''"))
                                in_docstring = False
                                break
                            docstring_lines.append(stripped_line)
                        elif entity_found and not stripped_line.startswith("#") and stripped_line != "": # end of docstring block
                            break
                    break
            return "\n".join(docstring_lines) if docstring_lines else f"Docstring for {entity_name} not found or complex to extract."

        else: # Get source code for the class
            class_source_lines = []
            in_class = False
            indent_level = 0
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith(f"class {entity_name}"):
                    in_class = True
                    class_source_lines.append(line)
                    indent_level = line.find(stripped_line[0]) # Get indent of the class definition
                elif in_class:
                    current_indent = line.find(line.strip()[0]) if line.strip() else indent_level + 1
                    if current_indent <= indent_level and stripped_line != "" and not stripped_line.startswith("#"):
                        # Likely end of class or start of another top-level element
                        break
                    class_source_lines.append(line)
            return "\n".join(class_source_lines) if class_source_lines else f"Source for {entity_name} not found."

    except FileNotFoundError:
        return f"File not found: {filepath}"
    except Exception as e:
        return f"Error extracting from {filepath} for {entity_name}: {e}"

# --- Define file paths (adjust if your script is run from a different location) ---
# Assuming this script is run from the root of the uikitxv2 project,
# or that uikitxv2 is in the PYTHONPATH.
# For notebook usage, we'll add a cell to adjust sys.path.

BASE_PATH = "uikitxv2/" # If running from parent of uikitxv2, adjust to ""
SRC_PATH = BASE_PATH + "src/"
CORE_PATH = SRC_PATH + "core/"
COMPONENTS_PATH = SRC_PATH + "components/"
UTILS_PATH = SRC_PATH + "utils/"

# --- Create Notebook Structure ---
nb = new_notebook()
nb.cells = []

# --- Introductory Cell ---
nb.cells.append(new_markdown_cell("""
# UIKitxv2: Wrapped Components Tutorial

This notebook provides an overview and usage examples for the wrapped UI components available in the `uikitxv2` library. These components are designed to simplify the creation of Dash user interfaces by providing themed wrappers around standard Dash and Dash Bootstrap Components.

**Key Locations:**
- Core components logic: `uikitxv2/src/core/`
- Individual UI components: `uikitxv2/src/components/`
- Theming and utilities: `uikitxv2/src/utils/`
"""))

# --- Setup Python Path ---
nb.cells.append(new_code_cell("""
import sys
import os
import pandas as pd # For DataTable example
import plotly.graph_objects as go # For Graph example

# --- Adjust Python Path ---
# This allows the notebook to find the uikitxv2.src modules.
# Assumes the notebook is in the 'uikitxv2' directory or its parent.
# If uikitxv2 is installed as a package, this might not be necessary.

# Get the absolute path of the current notebook or script
try:
    # This works if running in a Jupyter environment that defines __file__
    current_file_path = os.path.abspath(".") # Or os.path.dirname(__file__) if in a .py script
except NameError:
    # Fallback for environments where __file__ is not defined (e.g., some raw Python interpreters)
    current_file_path = os.getcwd()

# Navigate up to the directory containing 'uikitxv2' if necessary.
# If your 'uikitxv2' folder is directly in 'current_file_path', then project_root is current_file_path
# If 'uikitxv2' is one level up, use os.path.dirname(current_file_path)
# Adjust this logic based on where you save and run this generated notebook.

project_root_candidate1 = current_file_path # If notebook is in uikitxv2/
project_root_candidate2 = os.path.dirname(current_file_path) # If notebook is in uikitxv2/notebooks/

# Check if 'src' directory exists, indicating we are likely in the 'uikitxv2' root
if os.path.isdir(os.path.join(project_root_candidate1, 'src')):
    project_root = project_root_candidate1
elif os.path.isdir(os.path.join(project_root_candidate2, 'src')): # Check if 'uikitxv2/src' exists one level up
     # This means the notebook is likely in a subfolder of uikitxv2, and project_root_candidate2 is the parent of uikitxv2
     # We need to add the parent of uikitxv2 to path, so 'from uikitxv2.src...' works
     # No, if uikitxv2 is the project, and src is inside it, then project_root_candidate1 is correct if notebook is in uikitxv2
     # If notebook is in uikitxv2/notebooks, then project_root_candidate2 is uikitxv2.
     project_root = project_root_candidate2 # This means 'uikitxv2' is the project folder
else:
    project_root = current_file_path # Fallback, might need manual adjustment
    print(f"Warning: Could not reliably determine project root. Assuming: {project_root}")
    print("If imports fail, please adjust 'project_root' or ensure 'uikitxv2' is in your PYTHONPATH.")

# Add the project root to sys.path if it's not already there
# This makes 'from uikitxv2.src...' work
# If your project structure is flat and 'src' is top-level, this might need adjustment.
# The goal is to have the directory *containing* 'uikitxv2' (if 'uikitxv2' is the package name)
# or the 'uikitxv2' directory itself (if 'src' is directly under it and imports are 'from src...')
# in sys.path.

# If 'uikitxv2' is the package name and 'src' is inside it, then the directory *containing* 'uikitxv2'
# should be in sys.path for 'import uikitxv2' to work.
# If imports are 'from src.module', then the directory containing 'src' (i.e., 'uikitxv2') should be in sys.path.

# Let's assume 'uikitxv2' is the main project folder containing 'src'
# and we want to do 'from uikitxv2.src...'
# If the notebook is inside 'uikitxv2', then its parent needs to be on the path.
# If the notebook is outside 'uikitxv2', then the path to 'uikitxv2' itself needs to be on the path.

# Simpler approach for now: add the 'uikitxv2' directory to the path
# This makes 'from src...' work if the notebook is in 'uikitxv2'
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added to sys.path: {project_root}")

# If your top-level package is 'uikitxv2' and you import like 'from uikitxv2.src...',
# then the directory *containing* 'uikitxv2' needs to be on the path.
# Let's assume 'project_root' is the path to 'uikitxv2' folder.
# Then, its parent should be on the path.
uikitxv2_parent_dir = os.path.dirname(project_root)
if uikitxv2_parent_dir not in sys.path and project_root.endswith("uikitxv2"): # Only if project_root is indeed 'uikitxv2'
    sys.path.insert(0, uikitxv2_parent_dir)
    print(f"Added to sys.path for 'uikitxv2' package: {uikitxv2_parent_dir}")


print(f"Python version: {sys.version}")
print(f"Project root considered: {project_root}")
print("Current sys.path (first few entries):")
for i, p in enumerate(sys.path[:5]):
    print(f"  {i}: {p}")

# Attempt to import a core component to verify path setup
try:
    from uikitxv2.src.core.base_component import BaseComponent
    from uikitxv2.src.utils.colour_palette import default_theme, get_button_default_style # and other style getters
    print("\\nSuccessfully imported BaseComponent and default_theme. Path setup likely correct.")
except ImportError as e:
    print(f"\\nImportError: {e}. Please check the Python path setup above.")
    print("Ensure the 'uikitxv2' directory (containing 'src') or its parent is correctly added to sys.path,")
    print("or that the uikitxv2 package is installed.")

"""))


# --- BaseComponent Section ---
nb.cells.append(new_markdown_cell("""
## Core Concept: `BaseComponent`

All wrapped UI components in `uikitxv2` inherit from the `BaseComponent` class.

- **File:** `uikitxv2/src/core/base_component.py`
- **Purpose:** This abstract base class ensures that every UI component:
    - Has a unique `id`. This is crucial for Dash callbacks to identify and interact with components.
    - Is aware of a `theme`. Components can use this theme to style themselves consistently.
- **Key Method:**
    - `render()`: An abstract method that each concrete component must implement. This method is responsible for returning the actual Dash-compatible component (e.g., `dbc.Button`, `dcc.Graph`) that will be displayed in the UI.
"""))

base_component_doc = get_source_or_docstring(CORE_PATH + "base_component.py", "BaseComponent", get_doc=True)
nb.cells.append(new_markdown_cell(f"""
### Docstring for `BaseComponent`
```python
{base_component_doc}
```
"""))

base_component_source = get_source_or_docstring(CORE_PATH + "base_component.py", "BaseComponent", get_doc=False)
nb.cells.append(new_markdown_cell("### Source Code for `BaseComponent`"))
nb.cells.append(new_code_cell(f"{base_component_source}", metadata={"language": "python"}))


# --- Theming System Section ---
nb.cells.append(new_markdown_cell("""
## Theming System

`uikitxv2` components are designed to be themeable, allowing for a consistent look and feel across your application.

- **Theme Object:** Components typically accept a `theme` argument in their constructor. This `theme` is expected to be a Python dictionary containing various style attributes (colors, fonts, etc.). If no theme is provided, a `default_theme` is used.
- **Utility Functions:** The `uikitxv2/src/utils/colour_palette.py` module provides:
    - `default_theme`: A predefined theme dictionary.
    - Style getter functions (e.g., `get_button_default_style(theme)`, `get_container_default_style(theme)`): These functions are used internally by the components to retrieve specific style configurations based on the provided (or default) theme.
"""))

nb.cells.append(new_markdown_cell("### Example: `default_theme` (from `uikitxv2.src.utils.colour_palette`)"
                                  "\n\nThis is a conceptual representation. The actual `default_theme` can be imported and inspected."))
nb.cells.append(new_code_cell("""
# You can import and inspect the actual default_theme
from uikitxv2.src.utils.colour_palette import default_theme

print("Default Theme Keys:", list(default_theme.keys()))
# print("\\nDefault Theme Content (partial):")
# for key, value in list(default_theme.items())[:3]: # Print first 3 items as an example
# print(f"  {key}: {value}")

# Conceptual structure of a theme dictionary:
conceptual_theme_example = {
    'primary_color': '#007bff',
    'secondary_color': '#6c757d',
    'background_color': '#f8f9fa',
    'text_color': '#212529',
    'font_family': 'Arial, sans-serif',
    'button': {
        'background_color': '#007bff',
        'text_color': '#ffffff',
        'border_radius': '5px',
        'padding': '10px 15px'
    },
    # ... other component-specific or general styles
}
print("\\nConceptual Theme Example (structure):")
print(conceptual_theme_example)
""", metadata={"language": "python"}))


# --- Available Components Section ---
nb.cells.append(new_markdown_cell("## Available Components"))

components_info = [
    {"name": "Button", "file": "button.py", "class_name": "Button"},
    {"name": "ComboBox", "file": "combobox.py", "class_name": "ComboBox"},
    {"name": "Container", "file": "container.py", "class_name": "Container"},
    {"name": "DataTable", "file": "datatable.py", "class_name": "DataTable"},
    {"name": "Graph", "file": "graph.py", "class_name": "Graph"},
    {"name": "Grid", "file": "grid.py", "class_name": "Grid"},
    {"name": "ListBox", "file": "listbox.py", "class_name": "ListBox"},
    {"name": "RadioButton", "file": "radiobutton.py", "class_name": "RadioButton"},
    {"name": "Tabs", "file": "tabs.py", "class_name": "Tabs"},
]

for comp_info in components_info:
    class_doc = get_source_or_docstring(COMPONENTS_PATH + comp_info["file"], comp_info["class_name"], get_doc=True)
    
    # Extracting __init__ parameters from docstring (simplified)
    init_doc_lines = []
    in_args_section = False
    if class_doc:
        for line in class_doc.splitlines():
            if line.strip().lower().startswith("args:"):
                in_args_section = True
                continue
            if in_args_section:
                if line.strip() == "" or line.startswith("    ") and not line.startswith("        "): # End of args
                    break
                init_doc_lines.append(line)
    init_params_desc = "\n".join(init_doc_lines) if init_doc_lines else "Refer to source for __init__ parameters."


    nb.cells.append(new_markdown_cell(f"""
### {comp_info['name']}
- **Source File:** `uikitxv2/src/components/{comp_info['file']}`
- **Description:**
  ```
  {class_doc.splitlines()[0] if class_doc else 'N/A'} 
  ``` 
  (Full docstring below)
- **Initialization Parameters:**
  ```
{init_params_desc}
  ```
Full Docstring:
```python
{class_doc}
```
"""))

    # Basic Usage Example
    example_code = f"""
# --- {comp_info['name']} Example ---
from uikitxv2.src.components import {comp_info['class_name']}
from uikitxv2.src.utils.colour_palette import default_theme # Or your custom theme
# For Dash component type checking if needed:
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import pandas as pd # For DataTable
import plotly.graph_objects as go # For Graph

# 1. Initialize the component
# These are example parameters; refer to the docstring for all options.
"""
    if comp_info['name'] == 'Button':
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', label='Click Me!', theme=default_theme)"
    elif comp_info['name'] == 'ComboBox':
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', options=[{{'label': 'Option 1', 'value': 'opt1'}}, {{'label': 'Option 2', 'value': 'opt2'}}], value='opt1', placeholder='Select an option', theme=default_theme)"
    elif comp_info['name'] == 'Container':
        example_code += "from uikitxv2.src.components import Button # For child example\n"
        example_code += f"child_button = Button(id='btn-in-container', label='Child Button')\n"
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', children=[child_button.render(), html.P('Some text in container.')], theme=default_theme, fluid=False)"
    elif comp_info['name'] == 'DataTable':
        example_code += "df = pd.DataFrame({{'col1': [1, 2, 3], 'col2': ['A', 'B', 'C']}})\n"
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', data=df.to_dict('records'), columns=[{{'name': i, 'id': i}} for i in df.columns], page_size=5, theme=default_theme)"
    elif comp_info['name'] == 'Graph':
        example_code += "fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 1, 2])])\n"
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', figure=fig, theme=default_theme)"
    elif comp_info['name'] == 'Grid':
        example_code += "from uikitxv2.src.components import Button # For child example\n"
        example_code += f"btn1 = Button(id='grid-btn1', label='Button 1')\n"
        example_code += f"btn2 = Button(id='grid-btn2', label='Button 2')\n"
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', children=[(btn1, {{'width': 6}}), (btn2, {{'width': 6}})], theme=default_theme)"
    elif comp_info['name'] == 'ListBox':
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', options=['Apple', 'Banana', 'Cherry'], value=['Apple'], multi=True, theme=default_theme)"
    elif comp_info['name'] == 'RadioButton':
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', options=[{{'label': 'Yes', 'value': 'yes'}}, {{'label': 'No', 'value': 'no'}}], value='yes', inline=True, theme=default_theme)"
    elif comp_info['name'] == 'Tabs':
        example_code += "from uikitxv2.src.components import Button # For tab content example\n"
        example_code += f"tab1_content = html.P('This is content for Tab 1')\n"
        example_code += f"tab2_content = Button(id='tab-btn', label='Button in Tab 2')\n"
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', tabs=[('Info', tab1_content), ('Actions', tab2_content)], theme=default_theme)"
    else:
        example_code += f"my_component = {comp_info['class_name']}(id='my-{comp_info['name'].lower()}', theme=default_theme) # Add relevant parameters"

    example_code += """

# 2. Render the component (this is what you'd use in a Dash layout)
rendered_component = my_component.render()

# 3. (For notebook) Print the type and structure of the rendered component
print(f"Rendered component type: {type(rendered_component)}")
if hasattr(rendered_component, 'to_plotly_json'):
    print("Rendered component structure (Plotly JSON):")
    # print(rendered_component.to_plotly_json()) # Can be very verbose, print keys instead
    print({key: type(value).__name__ for key, value in rendered_component.to_plotly_json().get('props', {}).items()})
elif isinstance(rendered_component, go.Figure):
    print("Rendered component is a Plotly Figure. Figure spec (layout):")
    print(rendered_component.layout)
else:
    try:
        # For simple components like html.P or basic Dash components
        print(f"Rendered component: {rendered_component}")
    except Exception:
        print("Could not print component structure directly.")


# In a Dash app, it would typically be used like this:
# app.layout = html.Div([
#     rendered_component
# ])
"""
    nb.cells.append(new_code_cell(example_code, metadata={"language": "python"}))

    # Key Features/Specifics
    key_features = ""
    if comp_info['name'] == 'Container':
        key_features = "- **Children:** Can accept other `BaseComponent` instances (which will be rendered) or standard Dash components/layouts as children.\n- **Fluid:** `fluid=True` makes the container span the full width of its parent."
    elif comp_info['name'] == 'Grid':
        key_features = "- **Children:** Expects a list. Each item can be a `BaseComponent` (or Dash component) for auto-sized columns, or a tuple `(component, width_dict)`. `width_dict` (e.g., `{'xs': 12, 'md': 6}`) controls column spanning at different breakpoints. An integer can also be used for default width (e.g., `(component, 6)`)."
    elif comp_info['name'] == 'DataTable':
        key_features = "- **Data Input:** Accepts data as a list of dictionaries or a Pandas DataFrame (which is converted to `to_dict('records')`).\n- **Columns:** If `columns` are not provided, they are auto-generated from the keys of the first data record.\n- **Styling:** Uses `style_table`, `style_cell`, `style_header`, and `style_data_conditional` for detailed theming, merged with theme defaults."
    elif comp_info['name'] == 'Graph':
        key_features = "- **Figure:** Takes a Plotly `go.Figure` object. Theme defaults are applied to the figure's layout (e.g., background color, font).\n- **Style:** The `style` prop applies to the `dcc.Graph` wrapper div."
    elif comp_info['name'] == 'Tabs':
        key_features = "- **Tabs Data:** The `tabs` prop expects a list of tuples: `[('Tab Label 1', content1), ('Tab Label 2', content2)]`. `content` can be a `BaseComponent` instance (which will be rendered) or any Dash-compatible component/layout."

    if key_features:
        nb.cells.append(new_markdown_cell(f"#### Key Features & Specifics for {comp_info['name']}\n{key_features}"))


# --- Final Cell ---
nb.cells.append(new_markdown_cell("""
## Conclusion

This notebook has introduced the core concepts and usage of the wrapped UI components in `uikitxv2`. By leveraging `BaseComponent` and the theming system, you can build consistent and styled Dash applications more efficiently.

Remember to consult the individual component docstrings and source code for more detailed information on all available parameters and functionalities.
"""))


# --- Write Notebook to File ---
notebook_filename = "components_tutorial.ipynb"
with open(notebook_filename, 'w') as f:
    nbformat.write(nb, f)

print(f"Jupyter notebook '{notebook_filename}' created successfully.")
print(f"Please ensure that the 'uikitxv2' directory is in your Python path or that the package is installed when running the notebook.")
print("You might need to adjust the `sys.path` manipulation cell within the notebook if you encounter import errors, depending on where you run it.")

