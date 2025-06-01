"""Script to fix remaining test import issues."""

import os
from pathlib import Path

# Map of files and their specific fixes
FILE_FIXES = {
    # Component tests - imports should be from components, not components.submodule
    "tests/components/test_button_render.py": [
        ("from components.button import Button", "from components import Button")
    ],
    "tests/components/test_combobox_render.py": [
        ("from components.combobox import ComboBox", "from components import ComboBox")
    ],
    "tests/components/test_container_render.py": [
        ("from components.button import Button", "from components import Button"),
        ("from components.container import Container", "from components import Container")
    ],
    "tests/components/test_datatable_render.py": [
        ("from components.datatable import DataTable", "from components import DataTable")
    ],
    "tests/components/test_graph_render.py": [
        ("from components.graph import Graph", "from components import Graph")
    ],
    "tests/components/test_grid_render.py": [
        ("from components.button import Button", "from components import Button"),
        ("from components.grid import Grid", "from components import Grid")
    ],
    "tests/components/test_listbox_render.py": [
        ("from components.listbox import ListBox", "from components import ListBox")
    ],
    "tests/components/test_mermaid_render.py": [
        ("from components.mermaid import Mermaid", "from components import Mermaid")
    ],
    "tests/components/test_radiobutton_render.py": [
        ("from components.radiobutton import RadioButton", "from components import RadioButton")
    ],
    "tests/components/test_tabs_render.py": [
        ("from components.button import Button", "from components import Button"),
        ("from components.tabs import Tabs", "from components import Tabs")
    ],
    
    # Dashboard test - fix syntax error
    "tests/dashboard/test_dashboard_callbacks.py": [
        ("from apps.dashboards.main.app import app as dashboard as dash_module", 
         "from apps.dashboards.main.app import app as dash_module")
    ],
    
    # Ladder tests
    "tests/ladderTest/test_price_formatter.py": [
        ("from trading.ladder.scenario_ladder_v1 import convert_tt_special_format_to_decimal",
         "# The function is defined in the scenario_ladder.py file itself, not as an import")
    ],
    "tests/ladderTest/test_scenario_ladder_v1.py": [
        ("from trading.ladder import scenario_ladder_v1 as slv",
         "# scenario_ladder_v1 is not in the ladder package")
    ],
    
    # Lumberjack tests - fix module names
    "tests/lumberjack/test_logging_config.py": [
        ("from monitoring.logging.logging_config import", "from monitoring.logging.config import")
    ],
    "tests/lumberjack/test_sqlite_handler.py": [
        ("from monitoring.logging.sqlite_handler import", "from monitoring.logging.handlers import")
    ],
    
    # TT API tests
    "tests/ttapi/test_tt_utils.py": [
        ("from trading.tt_api.tt_utils import", "from trading.tt_api.utils import")
    ]
}

def fix_file(file_path: Path, replacements: list[tuple[str, str]]) -> bool:
    """Apply specific replacements to a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Apply targeted fixes to test files."""
    fixed_count = 0
    
    for file_path_str, replacements in FILE_FIXES.items():
        file_path = Path(file_path_str)
        if file_path.exists():
            if fix_file(file_path, replacements):
                print(f"Fixed: {file_path}")
                fixed_count += 1
        else:
            print(f"Warning: {file_path} not found")
    
    print(f"\nFixed {fixed_count} files.")

if __name__ == "__main__":
    main() 