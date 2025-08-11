#!/usr/bin/env python3
"""
Extract unique descriptions from BrokerTrades CSV files.

This script reads all DASONLY.*.csv files in data/reference/BrokerTrades/
and extracts unique values from the DESCRIPTION column.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Set, List
import argparse


def extract_unique_descriptions(directory_path: str) -> Set[str]:
    """
    Extract unique descriptions from all CSV files in the specified directory.
    
    Args:
        directory_path: Path to the BrokerTrades directory
        
    Returns:
        Set of unique description strings
    """
    unique_descriptions = set()
    csv_files = list(Path(directory_path).glob("DASONLY.*.csv"))
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    for csv_file in csv_files:
        print(f"Processing: {csv_file.name}")
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Check if DESCRIPTION column exists
            if 'DESCRIPTION' in df.columns:
                # Extract non-null descriptions
                descriptions = df['DESCRIPTION'].dropna()
                # Add to unique set
                unique_descriptions.update(descriptions)
                print(f"  -> Found {len(descriptions)} descriptions ({len(descriptions.unique())} unique)")
            else:
                print(f"  -> WARNING: No DESCRIPTION column found")
                
        except Exception as e:
            print(f"  -> ERROR reading file: {e}")
    
    return unique_descriptions


def save_results(descriptions: Set[str], output_file: str):
    """
    Save unique descriptions to a text file.
    
    Args:
        descriptions: Set of unique descriptions
        output_file: Path to output file
    """
    # Sort descriptions alphabetically
    sorted_descriptions = sorted(descriptions)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Unique Broker Trade Descriptions\n")
        f.write(f"# Total: {len(sorted_descriptions)} unique descriptions\n")
        f.write("#" + "="*60 + "\n\n")
        
        for desc in sorted_descriptions:
            f.write(f"{desc}\n")
    
    print(f"\nResults saved to: {output_file}")


def main():
    """Main function to run the extraction."""
    parser = argparse.ArgumentParser(description="Extract unique descriptions from BrokerTrades CSV files")
    parser.add_argument(
        "--input-dir",
        default="data/reference/BrokerTrades",
        help="Input directory containing CSV files (default: data/reference/BrokerTrades)"
    )
    parser.add_argument(
        "--output",
        default="data/output/unique_broker_descriptions.txt",
        help="Output file path (default: data/output/unique_broker_descriptions.txt)"
    )
    parser.add_argument(
        "--csv-output",
        action="store_true",
        help="Also save results as CSV with occurrence counts"
    )
    
    args = parser.parse_args()
    
    # Check if input directory exists
    if not os.path.exists(args.input_dir):
        print(f"ERROR: Input directory '{args.input_dir}' does not exist")
        return 1
    
    print(f"Extracting unique descriptions from: {args.input_dir}")
    
    # Extract unique descriptions
    unique_descriptions = extract_unique_descriptions(args.input_dir)
    
    print(f"\nTotal unique descriptions found: {len(unique_descriptions)}")
    
    # Save results
    save_results(unique_descriptions, args.output)
    
    # Optionally save as CSV with counts
    if args.csv_output:
        csv_output = args.output.replace('.txt', '_with_counts.csv')
        print(f"\nCalculating occurrence counts for CSV output...")
        
        # Re-read files to count occurrences
        description_counts = {}
        csv_files = list(Path(args.input_dir).glob("DASONLY.*.csv"))
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                if 'DESCRIPTION' in df.columns:
                    value_counts = df['DESCRIPTION'].value_counts()
                    for desc, count in value_counts.items():
                        description_counts[desc] = description_counts.get(desc, 0) + count
            except:
                pass
        
        # Save as CSV
        count_df = pd.DataFrame(
            list(description_counts.items()),
            columns=['Description', 'Count']
        ).sort_values('Description')
        
        count_df.to_csv(csv_output, index=False)
        print(f"CSV with counts saved to: {csv_output}")
    
    # Print sample of descriptions
    print("\nSample of unique descriptions:")
    print("-" * 60)
    sorted_descs = sorted(unique_descriptions)
    for desc in sorted_descs[:10]:
        print(f"  {desc}")
    if len(sorted_descs) > 10:
        print(f"  ... and {len(sorted_descs) - 10} more")
    
    return 0


if __name__ == "__main__":
    exit(main())