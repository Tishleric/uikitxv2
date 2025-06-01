"""Script to fix test imports after package reorganization."""

import os
import re
from pathlib import Path

# Define import replacements
IMPORT_REPLACEMENTS = {
    # Component imports that are already correct
    r'from components\.(\w+) import': r'from components.\1 import',
    
    # Utils imports need updating
    r'from utils\.colour_palette import': 'from components.themes import',
    
    # Core imports
    r'from core\.base_component import': 'from components.core.base_component import',
    r'from core\.mermaid_protocol import': 'from components.core.protocols import',
    r'from core import': 'from components.core import',
    
    # Decorator imports
    r'from decorators\.(\w+) import': r'from monitoring.decorators.\1 import',
    r'from decorators import': 'from monitoring.decorators import',
    
    # Lumberjack imports
    r'from lumberjack\.(\w+) import': r'from monitoring.logging.\1 import',
    r'from lumberjack import': 'from monitoring.logging import',
    
    # Dashboard imports
    r'from dashboard import dashboard': 'from apps.dashboards.main.app import app as dashboard',
    
    # TTRestAPI imports
    r'from TTRestAPI\.(\w+) import': r'from trading.tt_api.\1 import',
    r'from TTRestAPI import': 'from trading.tt_api import',
    
    # Ladder imports
    r'from ladderTest\.(\w+) import': r'from trading.ladder.\1 import',
    r'from ladderTest import': 'from trading.ladder import',
}

def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file. Returns True if changes were made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for pattern, replacement in IMPORT_REPLACEMENTS.items():
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix imports in all test files."""
    tests_dir = Path("tests")
    
    if not tests_dir.exists():
        print("Tests directory not found!")
        return
    
    total_files = 0
    modified_files = 0
    
    # Process all Python files in tests directory
    for py_file in tests_dir.rglob("*.py"):
        total_files += 1
        if fix_imports_in_file(py_file):
            modified_files += 1
            print(f"Updated: {py_file}")
    
    print(f"\nProcessed {total_files} files, modified {modified_files} files.")

if __name__ == "__main__":
    main() 