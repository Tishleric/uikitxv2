"""Fix all component imports for the new structure"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace old imports with new ones
    replacements = [
        # Fix core imports
        (r'from \.\.core\.base_component import BaseComponent', 'from ..core import BaseComponent'),
        (r'from \.\.core\.mermaid_protocol import MermaidProtocol', 'from ..core import MermaidProtocol'),
        
        # Fix theme imports
        (r'from \.\.utils\.colour_palette import (.+)', r'from ..themes import \1'),
        
        # Fix any remaining old style imports
        (r'from \.\.\.\.core import', 'from ..core import'),
        (r'from \.\.\.\.themes import', 'from ..themes import'),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in: {file_path}")
        return True
    return False

def main():
    lib_path = Path("lib/components")
    
    # Find all Python files
    py_files = list(lib_path.glob("**/*.py"))
    
    fixed_count = 0
    for file_path in py_files:
        if file_path.name != '__init__.py' and fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main() 