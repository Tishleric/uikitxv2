#!/usr/bin/env python3
"""
Remove @monitor decorators from non-callback functions.
Preserves @monitor on functions that also have @app.callback.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple
import shutil


def find_app_callback_above(lines: List[str], monitor_idx: int) -> bool:
    """
    Check if there's an @app.callback decorator above the @monitor line.
    Handles multi-line @app.callback decorators and comments between decorators.
    """
    # Work backwards from monitor position
    idx = monitor_idx - 1
    paren_count = 0
    in_decorator = False
    
    while idx >= 0:
        line = lines[idx].strip()
        
        # Skip empty lines and comments (including between decorators)
        if line == '' or line.startswith('#'):
            idx -= 1
            continue
            
        # If we're tracking a multi-line decorator (looking for its start)
        if in_decorator:
            # Count parentheses backwards
            for char in reversed(line):
                if char == ')':
                    paren_count += 1
                elif char == '(':
                    paren_count -= 1
            
            # Check if this line has the @app.callback start
            if line.startswith('@app.callback'):
                return True
                
            # If parentheses are balanced and we found the decorator start
            if paren_count == 0 and line.startswith('@'):
                in_decorator = False
                # Don't break - continue looking for more decorators
        else:
            # Handle a line that might be a closing parenthesis of a multi-line decorator
            if line == ')':
                # This could be the end of a multi-line decorator
                in_decorator = True
                paren_count = 1
            elif line.startswith('@'):
                # Check if it's @app.callback
                if line.startswith('@app.callback'):
                    return True
                    
                # Check if it's a multi-line decorator
                if line.endswith('(') and not line.endswith('()'):
                    in_decorator = True
                    paren_count = 1
                    
                # Otherwise it's a single-line decorator, continue looking
            else:
                # Not a decorator, comment, or closing paren - stop searching
                break
                
        idx -= 1
    
    return False


def find_function_name(lines: List[str], start_idx: int) -> str:
    """Find the function name after a decorator."""
    idx = start_idx + 1
    while idx < len(lines):
        line = lines[idx].strip()
        # Skip comments and empty lines
        if line == '' or line.startswith('#'):
            idx += 1
            continue
        if line.startswith('def '):
            # Extract function name
            match = re.match(r'def\s+(\w+)\s*\(', line)
            if match:
                return match.group(1)
            break
        idx += 1
    return "unknown"


def remove_monitor_decorator(lines: List[str], monitor_idx: int) -> List[str]:
    """Remove a @monitor decorator line, handling multi-line decorators"""
    new_lines = lines.copy()
    
    # Check if it's a multi-line decorator (ends with '(')
    line = lines[monitor_idx].strip()
    if line.endswith('(') and not line.endswith('()'):
        # Multi-line decorator, need to find closing parenthesis
        idx = monitor_idx + 1
        paren_count = 1
        while idx < len(lines) and paren_count > 0:
            for char in lines[idx]:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        # Found closing paren, remove all lines
                        del new_lines[monitor_idx:idx+1]
                        return new_lines
            idx += 1
    
    # Single line decorator
    del new_lines[monitor_idx]
    return new_lines


def check_monitor_import_needed(lines: List[str]) -> bool:
    """Check if monitor import is still needed after removals"""
    for line in lines:
        if '@monitor' in line and not line.strip().startswith('#'):
            return True
    return False


def process_file(filepath: Path, dry_run: bool = True) -> Tuple[int, int, List[str]]:
    """
    Process a single file to remove @monitor from non-callback functions.
    Returns (monitors_found, monitors_removed, changes_description)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_lines = lines.copy()
    monitors_found = 0
    monitors_removed = 0
    changes = []
    
    # Process from bottom to top to maintain line indices
    i = len(lines) - 1
    while i >= 0:
        line = lines[i].strip()
        if line.startswith('@monitor'):
            monitors_found += 1
            
            # Find function name for reporting
            func_name = find_function_name(lines, i)
            
            # Check if it has @app.callback above it
            if find_app_callback_above(lines, i):
                changes.append(f"  KEEP: @monitor on {func_name} (has @app.callback)")
            else:
                changes.append(f"  REMOVE: @monitor on {func_name}")
                monitors_removed += 1  # Count what would be removed
                if not dry_run:
                    lines = remove_monitor_decorator(lines, i)
        i -= 1
    
    # Check if we need to remove the import
    if not dry_run and monitors_removed > 0:
        if not check_monitor_import_needed(lines):
            # Remove the import line
            for i, line in enumerate(lines):
                if 'from lib.monitoring.decorators import monitor' in line or \
                   'from monitoring.decorators import monitor' in line:
                    changes.append(f"  REMOVE: monitor import (no longer needed)")
                    del lines[i]
                    break
    
    # Write changes if not dry run
    if not dry_run and lines != original_lines:
        # Create backup
        backup_path = filepath.with_suffix(filepath.suffix + '.bak')
        shutil.copy2(filepath, backup_path)
        
        # Write modified content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return monitors_found, monitors_removed, changes


def main():
    parser = argparse.ArgumentParser(description='Remove @monitor from non-callback functions')
    parser.add_argument('files', nargs='*', help='Files to process (if empty, process all)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be done without making changes (default: True)')
    parser.add_argument('--apply', action='store_true',
                        help='Actually make the changes (disables dry-run)')
    parser.add_argument('--single', type=str,
                        help='Process a single file for testing')
    
    args = parser.parse_args()
    
    if args.apply:
        args.dry_run = False
    
    # Get list of files to process
    if args.single:
        files = [Path(args.single)]
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        # Process all Python files with @monitor
        files = []
        for pattern in ['apps/**/*.py', 'lib/**/*.py', 'scripts/**/*.py']:
            files.extend(Path('.').glob(pattern))
        files = [f for f in files if '@monitor' in f.read_text(encoding='utf-8')]
    
    # Process each file
    total_monitors = 0
    total_removed = 0
    
    for filepath in sorted(files):
        print(f"\n{'='*60}")
        print(f"Processing: {filepath}")
        print(f"{'='*60}")
        
        try:
            monitors, removed, changes = process_file(filepath, args.dry_run)
            total_monitors += monitors
            total_removed += removed
            
            if changes:
                print(f"Found {monitors} @monitor decorators")
                for change in changes:
                    print(change)
                
                if args.dry_run:
                    print(f"\nDRY RUN: Would remove {removed} @monitor decorators")
                else:
                    print(f"\nREMOVED: {removed} @monitor decorators")
                    print(f"Backup saved: {filepath}.bak")
        except Exception as e:
            print(f"ERROR processing {filepath}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total @monitor decorators found: {total_monitors}")
    if args.dry_run:
        print(f"  Would remove: {total_removed}")
        print(f"\nTo apply changes, run with --apply flag")
    else:
        print(f"  Removed: {total_removed}")
        print(f"  Backups created for all modified files")


if __name__ == '__main__':
    main() 