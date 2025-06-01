"""Update imports in component files for the new structure"""

import os
import re
from pathlib import Path

# Map old imports to new imports
IMPORT_MAPPINGS = {
    # Component imports
    r'from \.\.core\.base_component import': 'from uikitxv2.components.core import BaseComponent',
    r'from \.\.core\.mermaid_protocol import': 'from uikitxv2.components.core import MermaidProtocol',
    r'from \.\.core\.data_service_protocol import': 'from uikitxv2.components.core import DataServiceProtocol',
    
    # Theme imports
    r'from \.\.utils\.colour_palette import': 'from uikitxv2.components.themes import',
    
    # Update specific function imports
    r'from \.\.core\.base_component import BaseComponent': 'from uikitxv2.components.core import BaseComponent',
    r'from \.\.core\.mermaid_protocol import MermaidProtocol': 'from uikitxv2.components.core import MermaidProtocol',
}

def update_imports_in_file(file_path):
    """Update imports in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Apply import mappings
    for old_pattern, new_import in IMPORT_MAPPINGS.items():
        content = re.sub(old_pattern, new_import, content)
    
    # If content changed, write it back
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated imports in: {file_path}")
        return True
    return False

def main():
    # Process all component files
    lib_path = Path("lib")
    
    # Find all Python files in components
    component_files = list(lib_path.glob("components/**/*.py"))
    
    updated_count = 0
    for file_path in component_files:
        if file_path.name != '__init__.py' and update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main() 