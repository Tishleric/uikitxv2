import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def plot_error_vs_moneyness_by_strike(date, t1, t2):
    """
    Plot error vs moneyness for each strike at specific timestamps.
    
    Parameters:
    -----------
    date : str
        Date in format like "21AUG25"
    t1 : str
        First timestamp (e.g., "2025-08-21 11:34:25")
    t2 : str
        Second timestamp (e.g., "2025-08-21 11:44:25")
    """
    
    # Get the current script directory
    script_dir = os.path.dirname(__file__)
    data_dir = script_dir  # Files are in the same directory as the script
    
    # Pattern to match files for the specific date
    pattern = f"XCME_HY3_{date}_*_C.csv_Plex.csv"
    files = glob.glob(os.path.join(data_dir, pattern))
    
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    # Create figure for plotting
    plt.figure(figsize=(12, 8))
    
    for file_path in files:
        try:
            # Extract strike from filename
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            strike = parts[3] if len(parts) > 3 else "unknown"
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Filter by timestamps
            mask = (df['timestamp'] == t1) | (df['timestamp'] == t2)
            filtered_df = df[mask]
            
            if len(filtered_df) > 0:
                # Plot error vs moneyness for this strike
                plt.scatter(filtered_df['moneyness'], filtered_df['error'], 
                           label=f'Strike {strike}', alpha=0.7, s=50)
                
                print(f"Strike {strike}: {len(filtered_df)} data points")
            else:
                print(f"Strike {strike}: No data found for timestamps {t1} and {t2}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    plt.xlabel('Moneyness')
    plt.ylabel('Error (%)')
    plt.title(f'Error vs Moneyness for {date} at timestamps {t1} and {t2}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def main():
    """Example usage"""
    
    # Example parameters - modify these as needed
    date = "21AUG25"
    t1 = "2025-08-18 14:34:26"
    t2 = "2025-08-18 14:39:27"
    
    print(f"Plotting error vs moneyness for date: {date}")
    print(f"Timestamps: {t1} and {t2}")
    print("=" * 60)
    
    plot_error_vs_moneyness_by_strike(date, t1, t2)

if __name__ == "__main__":
    main()
