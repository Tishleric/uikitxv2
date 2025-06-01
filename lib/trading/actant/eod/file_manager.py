#!/usr/bin/env python3
"""
File Manager for ActantEOD JSON Processing

This module provides utilities for scanning and selecting JSON files from the
ActantEOD shared folder, with automatic selection of the most recent file.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Configuration constants
# Updated to use new data directory structure
# Calculate path relative to this file's location: lib/trading/actant/eod/file_manager.py
# Need to go up 4 levels to reach project root, then down to data/input/eod
_module_path = Path(__file__).resolve()
_project_root = _module_path.parent.parent.parent.parent  # Go up 4 levels
DEFAULT_JSON_FOLDER = str(_project_root / "data" / "input" / "eod")
FALLBACK_JSON_FOLDER = r"Z:\ActantEOD"  # Fallback to shared folder if local not found
JSON_FILE_PATTERN = "*.json"


def get_json_folder_path() -> Path:
    """
    Get the JSON folder path, with fallback to shared folder if local unavailable.
    
    Returns:
        Path: Path to the JSON folder to scan
    """
    # Try local data directory first
    primary_path = Path(DEFAULT_JSON_FOLDER)
    
    # Check if the local data folder is accessible and contains JSON files
    if primary_path.exists() and primary_path.is_dir():
        # Check if it has any JSON files
        if list(primary_path.glob(JSON_FILE_PATTERN)):
            logger.info(f"Using local data folder: {primary_path}")
            return primary_path
    
    # Try fallback shared folder
    fallback_path = Path(FALLBACK_JSON_FOLDER)
    if fallback_path.exists() and fallback_path.is_dir():
        logger.info(f"Using shared folder: {fallback_path}")
        return fallback_path
    
    # If neither exists, return primary path (will create appropriate error later)
    logger.warning(f"Neither local nor shared folder accessible, defaulting to: {primary_path}")
    return primary_path


def scan_json_files(folder_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Scan folder for JSON files and return metadata about each file.
    
    Args:
        folder_path: Optional path to scan. If None, uses default folder.
        
    Returns:
        List of dictionaries containing file metadata:
        - filepath: Path object to the file
        - filename: Just the filename
        - size: File size in bytes
        - modified_time: Last modified timestamp
        - is_valid: Whether the file appears to be valid JSON
    """
    if folder_path is None:
        folder_path = get_json_folder_path()
    
    if not folder_path.exists():
        logger.error(f"Folder does not exist: {folder_path}")
        return []
    
    json_files = []
    
    try:
        # Find all JSON files in the folder
        for json_file in folder_path.glob(JSON_FILE_PATTERN):
            if json_file.is_file():
                try:
                    stat = json_file.stat()
                    file_info = {
                        'filepath': json_file,
                        'filename': json_file.name,
                        'size': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'is_valid': validate_json_file(json_file)
                    }
                    json_files.append(file_info)
                    logger.debug(f"Found JSON file: {json_file.name}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not access file {json_file}: {e}")
                    continue
    
    except (OSError, PermissionError) as e:
        logger.error(f"Could not scan folder {folder_path}: {e}")
        return []
    
    # Sort by modification time (newest first)
    json_files.sort(key=lambda x: x['modified_time'], reverse=True)
    
    logger.info(f"Found {len(json_files)} JSON files in {folder_path}")
    return json_files


def get_most_recent_json_file(folder_path: Optional[Path] = None) -> Optional[Path]:
    """
    Get the path to the most recently modified JSON file.
    
    Args:
        folder_path: Optional path to scan. If None, uses default folder.
        
    Returns:
        Path to the most recent JSON file, or None if no valid files found
    """
    json_files = scan_json_files(folder_path)
    
    # Filter for valid JSON files only
    valid_files = [f for f in json_files if f['is_valid']]
    
    if not valid_files:
        logger.warning("No valid JSON files found")
        return None
    
    most_recent = valid_files[0]  # Already sorted by modification time
    logger.info(f"Most recent JSON file: {most_recent['filename']} "
                f"(modified: {most_recent['modified_time']})")
    
    return most_recent['filepath']


def validate_json_file(file_path: Path) -> bool:
    """
    Validate that a file contains valid JSON and has expected structure.
    
    Args:
        file_path: Path to the JSON file to validate
        
    Returns:
        True if file is valid JSON with expected structure, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic structure validation - check for expected top-level keys
        if not isinstance(data, dict):
            logger.warning(f"JSON file {file_path.name} is not a dictionary")
            return False
        
        # Check for expected Actant structure
        if 'totals' not in data:
            logger.warning(f"JSON file {file_path.name} missing 'totals' key")
            return False
        
        if not isinstance(data['totals'], list):
            logger.warning(f"JSON file {file_path.name} 'totals' is not a list")
            return False
        
        logger.debug(f"JSON file {file_path.name} is valid")
        return True
        
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        logger.warning(f"Invalid JSON file {file_path.name}: {e}")
        return False


def get_json_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a JSON file for display purposes.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing file metadata and basic content info
    """
    metadata = {
        'filename': file_path.name,
        'size_mb': 0.0,
        'modified_time': None,
        'scenario_count': 0,
        'total_points': 0,
        'is_valid': False
    }
    
    try:
        # File system metadata
        stat = file_path.stat()
        metadata['size_mb'] = stat.st_size / (1024 * 1024)
        metadata['modified_time'] = datetime.fromtimestamp(stat.st_mtime)
        
        # Content metadata
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'totals' in data:
            totals = data['totals']
            if isinstance(totals, list):
                metadata['scenario_count'] = len(totals)
                metadata['total_points'] = sum(
                    len(scenario.get('points', [])) 
                    for scenario in totals 
                    if isinstance(scenario, dict)
                )
                metadata['is_valid'] = True
        
    except Exception as e:
        logger.warning(f"Could not extract metadata from {file_path.name}: {e}")
    
    return metadata


if __name__ == "__main__":
    # Test the file manager functionality
    logging.basicConfig(level=logging.INFO)
    
    print("Testing ActantEOD File Manager")
    print("=" * 40)
    
    # Test folder scanning
    files = scan_json_files()
    print(f"Found {len(files)} JSON files")
    
    for file_info in files[:3]:  # Show first 3 files
        print(f"  {file_info['filename']} - {file_info['size']} bytes - "
              f"{file_info['modified_time']} - Valid: {file_info['is_valid']}")
    
    # Test most recent file selection
    most_recent = get_most_recent_json_file()
    if most_recent:
        print(f"\nMost recent file: {most_recent.name}")
        
        # Test metadata extraction
        metadata = get_json_file_metadata(most_recent)
        print(f"Metadata: {metadata}")
    else:
        print("\nNo valid JSON files found") 