#!/usr/bin/env python3
"""
Count @app.callback decorators in Python files.
This is a validation tool for the monitor removal script.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


def count_callbacks_in_file(filepath: Path) -> Tuple[int, List[str]]:
    """
    Count @app.callback decorators in a file and return function names.
    
    Returns:
        (count, list_of_function_names)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    callback_count = 0
    callback_functions = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line starts an @app.callback
        if line.startswith('@app.callback'):
            callback_count += 1
            
            # Skip to the end of the decorator (handling multi-line)
            paren_count = line.count('(') - line.count(')')
            i += 1
            
            while i < len(lines) and paren_count > 0:
                line = lines[i].strip()
                paren_count += line.count('(') - line.count(')')
                i += 1
            
            # Now look for the function definition
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('def '):
                    # Extract function name
                    match = re.match(r'def\s+(\w+)\s*\(', line)
                    if match:
                        func_name = match.group(1)
                        callback_functions.append(func_name)
                    break
                elif line and not line.startswith('@'):
                    # Hit non-decorator, non-empty line before def
                    break
                i += 1
        else:
            i += 1
    
    return callback_count, callback_functions


def count_monitors_on_callbacks(filepath: Path) -> Tuple[int, List[str]]:
    """
    Count how many callback functions also have @monitor decorators.
    
    Returns:
        (count, list_of_monitored_callback_names)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    monitored_callbacks = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line starts an @app.callback
        if line.startswith('@app.callback'):
            # Found a callback, now check if it has @monitor
            has_monitor = False
            callback_func_name = None
            
            # Skip the @app.callback decorator
            paren_count = line.count('(') - line.count(')')
            i += 1
            
            while i < len(lines) and paren_count > 0:
                line = lines[i].strip()
                paren_count += line.count('(') - line.count(')')
                i += 1
            
            # Now look for @monitor and the function definition
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('@monitor'):
                    has_monitor = True
                elif line.startswith('def '):
                    # Extract function name
                    match = re.match(r'def\s+(\w+)\s*\(', line)
                    if match:
                        callback_func_name = match.group(1)
                    break
                elif line and not line.startswith('@'):
                    # Hit non-decorator line before def
                    break
                i += 1
            
            if has_monitor and callback_func_name:
                monitored_callbacks.append(callback_func_name)
        else:
            i += 1
    
    return len(monitored_callbacks), monitored_callbacks


def main():
    parser = argparse.ArgumentParser(description='Count callbacks and monitors in Python files')
    parser.add_argument('files', nargs='*', help='Files to analyze (default: all .py files)')
    parser.add_argument('--single', help='Analyze a single file')
    parser.add_argument('--details', action='store_true', help='Show function names')
    
    args = parser.parse_args()
    
    # Get files to process
    if args.single:
        files = [Path(args.single)]
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        # Find all Python files
        files = list(Path('.').rglob('*.py'))
        # Exclude backups and virtual environments
        files = [f for f in files if not any(p in str(f) for p in ['_backup', 'venv', '.git', '__pycache__'])]
    
    total_callbacks = 0
    total_monitored_callbacks = 0
    results = {}
    
    for filepath in sorted(files):
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue
            
        callback_count, callback_names = count_callbacks_in_file(filepath)
        monitor_count, monitored_names = count_monitors_on_callbacks(filepath)
        
        if callback_count > 0:
            results[str(filepath)] = {
                'callbacks': callback_count,
                'callback_names': callback_names,
                'monitored': monitor_count,
                'monitored_names': monitored_names
            }
            total_callbacks += callback_count
            total_monitored_callbacks += monitor_count
    
    # Display results
    print("\n" + "="*80)
    print("CALLBACK ANALYSIS REPORT")
    print("="*80)
    
    for filepath, data in results.items():
        print(f"\n{filepath}:")
        print(f"  Total @app.callback decorators: {data['callbacks']}")
        print(f"  Callbacks with @monitor: {data['monitored']}")
        
        if args.details:
            print(f"  Callback functions:")
            for name in data['callback_names']:
                monitored = " [MONITORED]" if name in data['monitored_names'] else ""
                print(f"    - {name}{monitored}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total files with callbacks: {len(results)}")
    print(f"Total @app.callback decorators: {total_callbacks}")
    print(f"Total callbacks with @monitor: {total_monitored_callbacks}")
    print(f"Callbacks WITHOUT @monitor: {total_callbacks - total_monitored_callbacks}")
    
    # Special check for main app.py
    main_app = Path('apps/dashboards/main/app.py')
    if str(main_app) in results:
        print(f"\nMain Dashboard (app.py):")
        print(f"  Callbacks: {results[str(main_app)]['callbacks']}")
        print(f"  Monitored: {results[str(main_app)]['monitored']}")


if __name__ == '__main__':
    main() 