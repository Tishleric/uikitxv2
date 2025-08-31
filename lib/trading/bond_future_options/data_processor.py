#!/usr/bin/env python3
"""
Extract rows by ActantRisk key from CSV files in data_validation folders and
combine them into a single CSV with source attribution.
"""

import csv
import argparse
import glob
import os


 

def extract_rows_by_key(key_value, output_filename=None):
    """
    Extract rows where 'key' column matches the specified value from each CSV file.
    
    Parameters:
    -----------
    key_value : str
        Value to search for in the 'key' column (e.g., "XCME.WY3.20AUG25.110.C")
    output_filename : str, optional
        Output filename. If None, auto-generates based on key_value and timestamp.
    """
    
    # Get the current script directory
    script_dir = os.path.dirname(__file__)
    data_validation_dir = os.path.join(script_dir, 'data_validation')
    
    # Find all CSV files in both date folders
    csv_files = []
    for date_folder in [
        '2025-08-18', '2025-08-19', '2025-08-20',
        '2025-08-21', '2025-08-22', '2025-08-25', '2025-08-26'
    ]:
        folder_path = os.path.join(data_validation_dir, date_folder)
        if os.path.exists(folder_path):
            pattern = os.path.join(folder_path, '*.csv')
            csv_files.extend(glob.glob(pattern))
    
    # Sort files by filename for consistent ordering
    csv_files.sort()
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Generate output filename if not provided
    if output_filename is None:
        safe_key = key_value.replace('.', '_').replace(':', '_')
        output_filename = f"extracted_key_{safe_key}.csv"
    
    output_path = os.path.join(data_validation_dir, output_filename)
    
    # Extract rows
    extracted_rows = []
    header = None
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Get header from first file
                if header is None and len(rows) > 0:
                    header = rows[0]
                
                # Find key column index
                key_col_index = None
                if header and 'key' in header:
                    key_col_index = header.index('key')
                
                # Search for matching key value
                if key_col_index is not None:
                    for row_data in rows[1:]:  # Skip header
                        if len(row_data) > key_col_index and row_data[key_col_index] == key_value:
                            # Check if adjtheor column has valid data
                            adjtheor_col_index = header.index('adjtheor') if 'adjtheor' in header else None
                            if adjtheor_col_index is not None and len(row_data) > adjtheor_col_index:
                                adjtheor_value = row_data[adjtheor_col_index]
                                # Check if adjtheor is non-empty and non-zero
                                adjtheor_str = str(adjtheor_value).strip()
                                if adjtheor_value and adjtheor_str and adjtheor_str not in ('0', '0.0'):
                                    # Add source filename as additional column
                                    filename = os.path.basename(csv_file)
                                    row_with_source = row_data + [filename]
                                    extracted_rows.append(row_with_source)
                                    break  # Only take first match per file
                else:
                    print(f"Warning: No 'key' column found in {csv_file}")
                    
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    # Write combined results
    if extracted_rows:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header with added source column
            if header:
                header_with_source = header + ['source_file']
                writer.writerow(header_with_source)
            
            # Write extracted rows
            writer.writerows(extracted_rows)
        
        print(f"Extracted key '{key_value}' from {len(extracted_rows)} files")
        print(f"Output saved to: {output_path}")
    else:
        print(f"No rows found with key '{key_value}'!")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract per-key time series from data_validation CSVs and write one output CSV per key "
            "into generatedcsvs/."
        )
    )
    parser.add_argument(
        "--key",
        dest="keys",
        action="append",
        help="ActantRisk key to extract (repeatable)",
    )
    parser.add_argument(
        "--keys-csv",
        dest="keys_csv",
        help="CSV file containing a 'key' column or one key per line",
    )
    args = parser.parse_args()

    def _load_keys_from_csv(path):
        keys = []
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return keys
                header = rows[0]
                idx = 0
                if header and "key" in header:
                    idx = header.index("key")
                    data_rows = rows[1:]
                else:
                    # No explicit header; treat all rows as single-value keys
                    data_rows = rows
                for r in data_rows:
                    if not r:
                        continue
                    val = r[idx].strip()
                    if val:
                        keys.append(val)
        except Exception as e:
            print(f"Failed to read keys from {path}: {e}")
        return keys

    keys_to_process = []
    if args.keys:
        keys_to_process.extend([k for k in args.keys if k])
    if args.keys_csv:
        keys_to_process.extend(_load_keys_from_csv(args.keys_csv))

    if not keys_to_process:
        parser.print_usage()
        print("No keys provided. Use --key and/or --keys-csv.")
        return

    # Output directory: lib/trading/bond_future_options/generatedcsvs/
    script_dir = os.path.dirname(__file__)
    out_dir = os.path.join(script_dir, 'generatedcsvs')
    os.makedirs(out_dir, exist_ok=True)

    for key in keys_to_process:
        safe_key = key.replace('.', '_').replace(':', '_').replace('/', '_')
        output_filename = os.path.join(out_dir, f"extracted_key_{safe_key}.csv")
        extract_rows_by_key(key, output_filename)


if __name__ == "__main__":
    main()