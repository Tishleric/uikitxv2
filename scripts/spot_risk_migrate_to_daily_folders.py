"""Migration script to reorganize existing Spot Risk files into daily folders.

This script:
1. Scans existing files in flat structure
2. Determines appropriate date folder based on filename timestamp
3. Moves files into date subfolders
4. Handles both input and output directories
"""

import os
import shutil
import re
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_timestamp_from_filename(filename: str) -> datetime:
    """Extract timestamp from BAV analysis filename.
    
    Args:
        filename: Filename like bav_analysis_20240115_120000.csv
        
    Returns:
        datetime: Parsed timestamp
    """
    # Pattern: bav_analysis_YYYYMMDD_HHMMSS.csv or bav_analysis_processed_YYYYMMDD_HHMMSS.csv
    pattern = r'bav_analysis(?:_processed)?_(\d{8})_(\d{6})\.csv'
    match = re.match(pattern, filename)
    
    if not match:
        raise ValueError(f"Cannot extract timestamp from filename: {filename}")
    
    date_str = match.group(1)
    time_str = match.group(2)
    
    # Parse datetime
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M%S")
    
    # Assume the timestamp in filename is in EST
    est = pytz.timezone('US/Eastern')
    return est.localize(dt)


def get_date_folder_for_timestamp(timestamp: datetime) -> str:
    """Determine the date folder for a given timestamp using 3pm EST boundaries.
    
    Args:
        timestamp: The file timestamp
        
    Returns:
        str: Date folder name in YYYY-MM-DD format
    """
    # If before 3pm EST, belongs to previous day's folder
    if timestamp.hour < 15:
        folder_date = timestamp.date() - timedelta(days=1)
    else:
        folder_date = timestamp.date()
    
    return folder_date.strftime('%Y-%m-%d')


def migrate_directory(directory: Path, dry_run: bool = False) -> int:
    """Migrate files in a directory to daily folder structure.
    
    Args:
        directory: Directory to migrate
        dry_run: If True, only show what would be done
        
    Returns:
        int: Number of files migrated
    """
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return 0
    
    migrated_count = 0
    
    # Find all BAV analysis CSV files in root directory
    for csv_file in directory.glob("bav_analysis*.csv"):
        # Skip if already in a subfolder
        if len(csv_file.relative_to(directory).parts) > 1:
            continue
        
        try:
            # Extract timestamp and determine date folder
            timestamp = extract_timestamp_from_filename(csv_file.name)
            date_folder = get_date_folder_for_timestamp(timestamp)
            
            # Create target path
            target_dir = directory / date_folder
            target_path = target_dir / csv_file.name
            
            if dry_run:
                logger.info(f"Would move: {csv_file.name} → {date_folder}/{csv_file.name}")
            else:
                # Create date folder if needed
                target_dir.mkdir(exist_ok=True)
                
                # Move file
                shutil.move(str(csv_file), str(target_path))
                logger.info(f"Moved: {csv_file.name} → {date_folder}/{csv_file.name}")
            
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {csv_file.name}: {e}")
    
    return migrated_count


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate Spot Risk files to daily folder structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Input directory path (default: data/input/actant_spot_risk)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory path (default: data/output/spot_risk)"
    )
    
    args = parser.parse_args()
    
    # Determine directories
    project_root = Path(__file__).parent.parent
    
    if args.input_dir:
        input_dir = Path(args.input_dir)
    else:
        input_dir = project_root / "data" / "input" / "actant_spot_risk"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / "data" / "output" / "spot_risk"
    
    logger.info("Spot Risk File Migration")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'ACTUAL MIGRATION'}")
    logger.info("-" * 50)
    
    # Migrate input directory
    logger.info(f"\nMigrating input directory: {input_dir}")
    input_count = migrate_directory(input_dir, dry_run=args.dry_run)
    
    # Migrate output directory
    logger.info(f"\nMigrating output directory: {output_dir}")
    output_count = migrate_directory(output_dir, dry_run=args.dry_run)
    
    # Summary
    logger.info("\n" + "-" * 50)
    logger.info(f"Migration {'simulation' if args.dry_run else 'complete'}:")
    logger.info(f"- Input files: {input_count}")
    logger.info(f"- Output files: {output_count}")
    logger.info(f"- Total: {input_count + output_count}")
    
    if args.dry_run:
        logger.info("\nThis was a dry run. Use without --dry-run to actually move files.")


if __name__ == "__main__":
    main() 