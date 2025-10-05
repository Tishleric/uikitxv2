import pandas as pd
import warnings
import os

# Suppress all pandas warnings
warnings.filterwarnings('ignore', category=pd.errors.ChainedAssignmentError)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)  # Use built-in FutureWarning

from bachelier_greek import analytical_greeks, analytical_greeks_put
from Brent_Bisection import *
import matplotlib.pyplot as plt

def filter_mispriced_options(df, option_type):

    if option_type == 'C':
        df['moneyness'] = (-df['strike'] + df['underlying_future_price'])
    elif option_type == 'P':
        df['moneyness'] = (df['strike'] - df['underlying_future_price'])

    df = df[df['adjtheor'] >= df['moneyness']]

    return df

def plot_pnl_diff(df2):

    """
    # Extract date and base name from filename
    base_name = file_name.replace('extracted_key_', '')
    parts = base_name.split('_')
    
    # Extract date from parts (e.g., "27AUG25" from "XCME_WY4_27AUG25_113_C")
    # Date is typically the 3rd part (index 2) after splitting by '_'
    if len(parts) > 2:
        date_part = parts[2]
    else:
        raise ValueError("Date not found in filename")
    """
    #df2["IV_binary_search"] = df2['implied_vol']
    df2 = df2[['timestamp', 'underlying_future_price', 'expiry', 'vtexp', 'strike', 'adjtheor', 'itype']]
    df2 = df2[df2['adjtheor'] >= 0]
    df2['recalculated_price_binary_search'] = df2['adjtheor']
    if df2['itype'].iloc[0] == 'C':
        df2['moneyness'] = (-df2['strike'] + df2['underlying_future_price'])
    elif df2['itype'].iloc[0] == 'P':
        df2['moneyness'] = (df2['strike'] - df2['underlying_future_price'])
    df2['adjtheor'] = df2['adjtheor'].astype(float)

    df2['IV_binary_search'] = df2.apply(lambda row: implied_vol(row['underlying_future_price'], row['strike'], row['vtexp'], row['adjtheor'], row['itype']), axis=1)
    if df2['itype'].iloc[0] == 'C':
        df2['recalculated_price_binary_search'] = df2.apply(lambda row: bachelier_call(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp']), axis=1)
    elif df2['itype'].iloc[0] == 'P':
        df2['recalculated_price_binary_search'] = df2.apply(lambda row: bachelier_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp']), axis=1)
    
    if df2['itype'].iloc[0] == 'C':
        df2['delta_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['delta'], axis=1)
        df2['theta_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['theta'], axis=1)
        df2['vega_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['vega'], axis=1)
        df2['gamma_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['gamma'], axis=1)
        df2['speed_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['speed'], axis=1)
        df2['volga_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['volga'], axis=1)
        df2['vanna_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['vanna'], axis=1)
        df2['veta_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['veta'], axis=1)
        df2['charm_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['charm'], axis=1)
        df2['theta_dot_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp']).get('theta_dot', 0), axis=1)
    elif df2['itype'].iloc[0] == 'P':
        df2['delta_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['delta'], axis=1)
        df2['theta_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['theta'], axis=1)
        df2['vega_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['vega'], axis=1)
        df2['gamma_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['gamma'], axis=1)
        df2['speed_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['speed'], axis=1)
        df2['volga_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['volga'], axis=1)
        df2['vanna_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['vanna'], axis=1)
        df2['veta_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['veta'], axis=1)
        df2['charm_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['charm'], axis=1)
        df2['theta_dot_binary_search'] = df2.apply(lambda row: analytical_greeks_put(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp']).get('theta_dot', 0), axis=1)

    df2['del_F'] = df2['underlying_future_price'].shift(-1) - df2['underlying_future_price']
    df2['del_T'] = df2['vtexp'].shift(-1) - df2['vtexp']
    df2['del_C'] = df2['adjtheor'].shift(-1) - df2['adjtheor']
    df2['del_IV'] = df2['IV_binary_search'].shift(-1) - df2['IV_binary_search']
    df2['pnl_explained'] = df2['delta_binary_search']*df2['del_F'] + df2['theta_binary_search']*df2['del_T'] + df2['vega_binary_search']*df2['del_IV'] + (df2['gamma_binary_search']*(df2['del_F']**2))/2
    df2['pnl_explained'] = df2['pnl_explained'] + (df2['speed_binary_search']*(df2['del_F']**3)/6)
    #df2['pnl_explained_without_vega'] = df2['pnl_explained'] - (df2['vega_binary_search']*df2['del_IV'])
    df2['delta_pnl'] = df2['delta_binary_search']*df2['del_F']
    df2['theta_pnl'] = df2['theta_binary_search']*df2['del_T']
    df2['vega_pnl'] = df2['vega_binary_search']*df2['del_IV']
    df2['gamma_pnl'] = 0.5*df2['gamma_binary_search']*df2['del_F']**2
    df2['speed_pnl'] = (df2['speed_binary_search']*(df2['del_F']**3)/6)
    df2['volga_pnl'] = 0.5*df2['volga_binary_search']*df2['del_IV']**2
    df2['vanna_pnl'] = df2['vanna_binary_search']*df2['del_F']*df2['del_IV']
    df2['veta_pnl'] = df2['veta_binary_search']*df2['del_IV']*df2['del_T']
    df2['charm_pnl'] = df2['charm_binary_search']*df2['del_F']*df2['del_T']
    df2['theta_dot_pnl'] = 0.5*df2['theta_dot_binary_search']*(df2['del_T']**2)
    df2['error'] = (df2['pnl_explained']/df2['del_C'] - 1)*100
    #df2['error_without_vega'] = (df2['pnl_explained_without_vega']/df2['del_C'] - 1)*100
    df2['pnl_explained_2nd_order'] = df2['pnl_explained'] + df2['vanna_pnl'] + df2['veta_pnl'] + df2['charm_pnl'] + df2['volga_pnl'] 
    df2['error_2nd_order'] = (df2['pnl_explained_2nd_order']/df2['del_C'] - 1)*100
    df2 = df2[['timestamp','underlying_future_price', 'expiry', 'vtexp','strike','adjtheor','itype','IV_binary_search','recalculated_price_binary_search','moneyness','delta_binary_search','theta_binary_search','vega_binary_search','gamma_binary_search','speed_binary_search', 'volga_binary_search', 'vanna_binary_search', 'veta_binary_search', 'charm_binary_search', 'theta_dot_binary_search', 'del_F','del_T','del_C','del_IV','pnl_explained','delta_pnl','theta_pnl','vega_pnl', 'gamma_pnl', 'speed_pnl','volga_pnl', 'vanna_pnl', 'veta_pnl', 'charm_pnl', 'theta_dot_pnl', 'pnl_explained', 'pnl_explained_2nd_order', 'error', 'error_2nd_order']]
    df2 = df2.drop_duplicates()
    #df2.plot(x='moneyness', y='error', kind='scatter')
    #df2.plot(x='moneyness', y='error_without_vega', kind='scatter')

    #df2.plot(x='moneyness', y='error_with_volga', kind='scatter')

    """
    df = pd.read_csv(f'lib/trading/bond_future_options/data_validation/yamansmess/ATM_C_{date_part}_vols.csv')
    df = df.drop_duplicates(subset=['timestamp'])  # Remove duplicate timestamps
    df = df.set_index("timestamp")
    
    df2 = df2.drop_duplicates(subset=['timestamp'])  # Remove duplicate timestamps  
    df2 = df2.set_index("timestamp")

    df2['ATM_Strike'] = df['strike']
    df2['ATM_IV'] = df['IV_binary_search']
    df2['Skew_IV'] = df2['IV_binary_search'] - df2['ATM_IV']

    df2['del_ATM_IV'] = df2['ATM_IV'].shift(-1) - df2['ATM_IV']
    df2['del_Skew_IV'] = df2['Skew_IV'].shift(-1) - df2['Skew_IV']
    df2['ATM_IV_vega_pnl'] = df2['vega_binary_search']*df2['del_ATM_IV']
    df2['Skew_IV_vega_pnl'] = df2['vega_binary_search']*df2['del_Skew_IV']
    df2['combined_vega_pnl'] = df2['ATM_IV_vega_pnl'] + df2['Skew_IV_vega_pnl']
    """

    #df2.to_csv(f'lib/trading/bond_future_options/data_validation/accuracy_validation/{base_name}_Plex.csv')

    df3 = df2[abs(df2['error_2nd_order']) > 5.0]
    #df3.to_csv(f'lib/trading/bond_future_options/data_validation/accuracy_validation/{base_name}_Plex_outliers_2nd_order.csv')

    df4 = df2[abs(df2['error']) > 5.0]
    #df4.to_csv(f'lib/trading/bond_future_options/data_validation/accuracy_validation/{base_name}_Plex_outliers_error.csv')
    #plt.show()

    return df2, df3, df4

def process_five_minute_data():
    """
    Process CSV files from FiveMinuteMarketSelected_by_instrument folders,
    apply filter_mispriced_options, and save to accuracy_validation folders.
    """
    import glob
    
    # Source and destination base paths
    source_base = "Y:/uikitxv2/data/FiveMinuteMarketSelected_by_instrument"
    dest_base = "Y:/uikitxv2/lib/trading/bond_future_options/data_validation/accuracy_validation"
    
    # Date folders to process
    date_folders = ["19AUG25", "20AUG25", "21AUG25"]
    
    for date_folder in date_folders:
        print(f"Processing {date_folder}...")
        
        # Source and destination paths for this date
        source_path = f"{source_base}/{date_folder}"
        dest_path = f"{dest_base}/{date_folder}"
        
        # Create destination folder if it doesn't exist
        os.makedirs(dest_path, exist_ok=True)
        
        # Get all CSV files in this date folder
        csv_files = glob.glob(f"{source_path}/*.csv")
        
        print(f"Found {len(csv_files)} CSV files in {date_folder}")
        
        for csv_file in csv_files:
            try:
                # Read CSV file
                df = pd.read_csv(csv_file)
                option_type = df['itype'].iloc[0]

                # Apply filter_mispriced_options
                df_filtered = filter_mispriced_options(df, option_type)
                
                # Get filename without path
                filename = os.path.basename(csv_file)
                
                # Save filtered data to destination
                output_path = os.path.join(dest_path, filename)
                df_filtered.to_csv(output_path, index=False)
                
                print(f"Processed: {filename} -> {len(df_filtered)} rows after filtering")
                
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
        
        print(f"Completed {date_folder}\n")

if __name__ == "__main__":
    # Process five minute data
    #process_five_minute_data()
    
    # Process accuracy validation data to create Plex files
    
    # Original code (commented out)
    """
    set_of_file_names = {'extracted_key_XCME_GY4_26AUG25_111_75_C.csv', 'extracted_key_XCME_GY4_26AUG25_112_5_C.csv', 
    'extracted_key_XCME_GY4_26AUG25_112_25_C.csv', 'extracted_key_XCME_GY4_26AUG25_112_75_C.csv', 
    'extracted_key_XCME_GY4_26AUG25_112_C.csv', 'extracted_key_XCME_GY4_26AUG25_113_C.csv', 
    'extracted_key_XCME_HY3_21AUG25_111_75_C.csv', 'extracted_key_XCME_HY3_21AUG25_112_5_C.csv', 
    'extracted_key_XCME_HY3_21AUG25_112_25_C.csv', 'extracted_key_XCME_HY3_21AUG25_112_75_C.csv', 
    'extracted_key_XCME_HY3_21AUG25_112_C.csv', 'extracted_key_XCME_HY3_21AUG25_113_C.csv', 
    'extracted_key_XCME_VY4_25AUG25_111_75_C.csv', 'extracted_key_XCME_VY4_25AUG25_112_5_C.csv', 
    'extracted_key_XCME_VY4_25AUG25_112_25_C.csv', 'extracted_key_XCME_VY4_25AUG25_112_75_C.csv', 
    'extracted_key_XCME_VY4_25AUG25_112_C.csv', 'extracted_key_XCME_VY4_25AUG25_113_C.csv', 
    'extracted_key_XCME_WY4_27AUG25_111_75_C.csv', 'extracted_key_XCME_WY4_27AUG25_112_5_C.csv', 
    'extracted_key_XCME_WY4_27AUG25_112_25_C.csv', 'extracted_key_XCME_WY4_27AUG25_112_75_C.csv', 
    'extracted_key_XCME_WY4_27AUG25_112_C.csv', 'extracted_key_XCME_WY4_27AUG25_113_C.csv'}

    for file_name in set_of_file_names:
        print("="*100)
        print(file_name)
        print("="*100)
        df2 = pd.read_csv(f'lib/trading/bond_future_options/data_validation/yamansmess/{file_name}')
        df2 = df2.drop_duplicates(subset=['vtexp'])
        plot_pnl_diff(df2, file_name)
    """

    import glob
    folder_names = ["19AUG25", "20AUG25", "21AUG25"]
    folder_path = r"Y:/uikitxv2/lib/trading/bond_future_options/data_validation/accuracy_validation"  # change this to your folder path
    for folder_name in folder_names:
        folder = folder_path + f"/{folder_name}"
        files = [os.path.basename(p) for p in glob.glob(os.path.join(folder, "*unique_hourly.csv"))]

        for file in files:
            df = pd.read_csv(folder + f"/{file}")
            if df['itype'].iloc[0] == 'P':
                df['adjtheor'] = df['adjtheor'].apply(lambda x: x if x > 0 else 0)

            df2, df3, df4 = plot_pnl_diff(df)
            df2.to_csv(folder_path + f"/{folder_name}_Plex/{file.replace('.csv', '_hourly_Plex.csv')}")
            df3.to_csv(folder_path + f"/{folder_name}_Plex/{file.replace('.csv', '_hourly_Plex_outliers_2nd_order.csv')}")
            df4.to_csv(folder_path + f"/{folder_name}_Plex/{file.replace('.csv', '_hourly_Plex_outliers_error.csv')}")
            print(f"Processed {file}")

