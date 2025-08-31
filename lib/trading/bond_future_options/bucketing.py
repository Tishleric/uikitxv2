import pandas as pd
import os
import glob

def strip_small_prices():
    """
    Split CSV files ending with 'outliers.csv' based on adjtheor column values.
    Creates two new files: price_normal (adjtheor > 1e-6) and price_tiny (adjtheor <= 1e-6)
    """
    
    # Get the current script directory
    script_dir = os.path.dirname(__file__)
    yamansmess_dir = os.path.join(script_dir, "data_validation", "yamansmess")
    
    # Create bucket folder
    bucket_dir = os.path.join(yamansmess_dir, "bucket")
    os.makedirs(bucket_dir, exist_ok=True)
    
    # Find all files ending with 'outliers.csv'
    pattern = os.path.join(yamansmess_dir, "*outliers.csv")
    outlier_files = glob.glob(pattern)
    
    if not outlier_files:
        print("No outlier files found!")
        return
    
    print(f"Found {len(outlier_files)} outlier files")
    
    for file_path in outlier_files:
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Get the base filename without extension
            filename = os.path.basename(file_path)
            base_name = filename.replace('_outliers.csv', '')
            
            # Split based on adjtheor values
            normal_df = df[df['adjtheor'] > 1e-6]
            tiny_df = df[df['adjtheor'] <= 1e-6]
            
            # Create output filenames
            normal_filename = f"{base_name}_price_normal.csv"
            tiny_filename = f"{base_name}_price_tiny.csv"
            
            # Save the split files in bucket folder
            normal_path = os.path.join(bucket_dir, normal_filename)
            tiny_path = os.path.join(bucket_dir, tiny_filename)
            
            normal_df.to_csv(normal_path, index=False)
            tiny_df.to_csv(tiny_path, index=False)
            
            print(f"Processed {filename}:")
            print(f"  Normal prices (>{1e-6:.0e}): {len(normal_df)} rows -> {normal_filename}")
            print(f"  Tiny prices (<={1e-6:.0e}): {len(tiny_df)} rows -> {tiny_filename}")
            print()
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# Example usage
if __name__ == "__main__":
    strip_small_prices()  # df parameter not used in this implementation 