"""
Default configurations for component factory.

These defaults are applied when creating components via the factory,
but can be overridden by passing explicit arguments.
"""

COMPONENT_DEFAULTS = {
    "datatable": {
        "data": [],
        "columns": [],
        "page_size": 10,
        "style_table": {},
        "style_cell": {},
        "style_header": {},
        "style_data_conditional": []
    },
    "grid": {
        "children": [],
        "style": {},
        "className": ""
    },
    "button": {
        "text": "Button",
        "variant": "primary", 
        "disabled": False,
        "style": {},
        "className": ""
    },
    "graph": {
        "figure": {},
        "style": {},
        "className": "",
        "config": {"displayModeBar": False}
    },
    "container": {
        "children": [],
        "fluid": True,
        "style": {},
        "className": ""
    },
    "text_input": {
        "value": "",
        "placeholder": "Enter text...",
        "disabled": False,
        "style": {},
        "className": ""
    },
    "number_input": {
        "value": 0,
        "disabled": False,
        "style": {},
        "className": ""
    },
    "dropdown": {
        "options": [],
        "value": None,
        "placeholder": "Select...",
        "disabled": False,
        "style": {},
        "className": ""
    },
    "date_picker": {
        "date": None,
        "display_format": "YYYY-MM-DD",
        "disabled": False,
        "style": {},
        "className": ""
    },
    "checkbox": {
        "checked": False,
        "disabled": False,
        "style": {},
        "className": ""
    },
    "radio_button": {
        "options": [],
        "value": None,
        "inline": False,
        "style": {},
        "className": ""
    },
    "slider": {
        "min": 0,
        "max": 100,
        "value": 50,
        "step": 1,
        "disabled": False,
        "marks": None,
        "style": {},
        "className": ""
    }
} 