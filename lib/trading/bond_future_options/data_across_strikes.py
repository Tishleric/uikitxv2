import pandas as pd
import glob
import os
from bachelier_greek import analytical_greeks
from Brent_Bisection import *
import matplotlib.pyplot as plt


def greeks_calculator(df2):
    """
    Extract data from a single CSV file for given option type and expiry at specific timestamps.
    
    Parameters:
    -----------
    option_type : str
        "call" or "put" (will be converted to "C" or "P")
    expiry_date : str
        Date in format like "21AUG25"
    t1 : str
        First timestamp (e.g., "2025-08-18 14:34:26")
    t2 : str
        Second timestamp (e.g., "2025-08-18 14:39:27")
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with rows matching the timestamps, filtered by strike column
    """
    # Avoid pandas chained-assignment warnings by working on a copy with a clean index
    df2 = df2.copy().reset_index(drop=True)

    df2["IV_binary_search"] = df2['underlying_future_price']
    df2['recalculated_price_binary_search'] = df2['adjtheor']
    df2['moneyness'] = (-df2['strike'] + df2['underlying_future_price'])
    df2['adjtheor'] = df2['adjtheor'].astype(float)

    # Quiet debug printing by default to avoid console spam in UI flows
    verbose = False

    for i in range(len(df2)):
        #print(i, "of", len(df2)-1)
        S, K, T = df2['underlying_future_price'].iloc[i], df2['strike'].iloc[i], df2['vtexp'].iloc[i]
        C_mkt = df2['adjtheor'].iloc[i]
        if C_mkt < 0:
            continue
        if S < 0:
            continue
        #print(S, K, T, C_mkt)
        # Root function in sigma: f(sig) = model - market
        if verbose:
            print("C_mkt", C_mkt, type(C_mkt))
        def f_sigma(sig): return bachelier_call(S, K, sig, T) - C_mkt

        if abs(df2['moneyness'].iloc[i]) > df2['adjtheor'].iloc[i]:
            print(i, "of", len(df2)-1)
            print("timestamp", df2['timestamp'].iloc[i])
            print("Instrinsic value is greater than option price")

        if df2['adjtheor'].iloc[i] < 0:
            print("Option price is negative")

        # Bracket [0, hi] by geometric expansion
        lo, hi = 0.0, 1e-4
        while f_sigma(hi) < 0: hi *= 2.0
        if verbose:
            print("timestamp", df2['timestamp'].iloc[i])
        # Scalar-safe assignments to avoid chained assignment
        iv_value = bisection(f_sigma, lo, hi, xtol=1e-16, ftol=1e-16)[0]
        df2.at[i, 'IV_binary_search'] = iv_value
        if verbose:
            print("IV_binary_search", df2.at[i, 'IV_binary_search'])
        df2.at[i, 'recalculated_price_binary_search'] = bachelier_call(S, K, df2.at[i, 'IV_binary_search'], T)

    df2['delta_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['delta'], axis=1)
    df2['theta_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['theta'], axis=1)
    df2['vega_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['vega'], axis=1)
    df2['gamma_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['gamma'], axis=1)
    df2['speed_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['speed'], axis=1)
    df2['volga_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['volga'], axis=1)
    df2['vanna_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['vanna'], axis=1)
    df2['veta_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['veta'], axis=1)
    df2['charm_binary_search'] = df2.apply(lambda row: analytical_greeks(row['underlying_future_price'], row['strike'], row['IV_binary_search'], row['vtexp'])['charm'], axis=1)

    df2 = df2[['timestamp','underlying_future_price','vtexp','strike','adjtheor','IV_binary_search','recalculated_price_binary_search','moneyness','delta_binary_search','theta_binary_search','vega_binary_search','gamma_binary_search','speed_binary_search','volga_binary_search','vanna_binary_search','veta_binary_search','charm_binary_search']]
    df2 = df2.drop_duplicates()
    return df2

def data_across_strikes(df1,df2):
    df1 = greeks_calculator(df1)
    df2 = greeks_calculator(df2)
    print(df1)
    print(df2)
    df1.reset_index(drop=True, inplace=True)
    df2.reset_index(drop=True, inplace=True)

    if len(df1) != len(df2):
        print("Error: df1 and df2 have different lengths")
        return None

    df1['IV1'] = df1['IV_binary_search']
    df1['IV2'] = df2['IV_binary_search']

    df2['IV_binary_search'] = df2['IV_binary_search']
    df1['del_F'] = df2['underlying_future_price'] - df1['underlying_future_price']
    df1['del_T'] = df2['vtexp'] - df1['vtexp']
    df1['pnl_actual'] = df2['adjtheor'] - df1['adjtheor']
    df1['del_IV'] = df2['IV_binary_search'] - df1['IV_binary_search']

    df1['delta_pnl'] = df1['delta_binary_search']*df1['del_F']
    df1['theta_pnl'] = df1['theta_binary_search']*df1['del_T']
    df1['vega_pnl'] = df1['vega_binary_search']*df1['del_IV']
    df1['gamma_pnl'] = 0.5*df1['gamma_binary_search']*(df1['del_F']**2)
    df1['speed_pnl'] = (df1['speed_binary_search']*(df1['del_F']**3)/6)
    df1['volga_pnl'] = df1['volga_binary_search']*(df1['del_IV']**2)
    df1['vanna_pnl'] = df1['vanna_binary_search']*df1['del_F']*df1['del_IV']
    df1['veta_pnl'] = df1['veta_binary_search']*df1['del_IV']*df1['del_T']
    df1['charm_pnl'] = df1['charm_binary_search']*df1['del_F']*df1['del_T']

    #df1['theta_dot_pnl'] = 0.5*df1['theta_dot_binary_search']*(df1['del_T']**2)

    df1['pnl_explained'] = df1['delta_pnl'] + df1['theta_pnl'] + df1['vega_pnl'] + df1['gamma_pnl'] + df1['speed_pnl']

    df1['percentage_error'] = abs((df1['pnl_explained']/df1['pnl_actual'] - 1)*100)

    df1['pnl_explained_2nd_order_cross_effects'] = df1['delta_pnl'] + df1['theta_pnl'] + df1['vega_pnl'] + df1['gamma_pnl'] + df1['speed_pnl'] + df1['volga_pnl'] + df1['vanna_pnl'] + df1['veta_pnl'] + df1['charm_pnl']

    df1['percentage_error_2nd_order_cross_effects'] = abs((df1['pnl_explained_2nd_order_cross_effects']/df1['pnl_actual'] - 1)*100)
    df1 = df1[df1['adjtheor'] > 0.0001]

    return df1

# Example usage for testing
if __name__ == "__main__":
    # Test the function using relative paths
    script_dir = os.path.dirname(__file__)
    csv_path = os.path.join(script_dir, "generatedcsvs", "aggregated", "aggregated_18AUG25_C.csv")
    
    df1 = pd.read_csv(csv_path)
    df2 = pd.read_csv(csv_path)
    df1 = df1.iloc[0:11]
    df2 = df2.iloc[11:22]

    print(df1)
    print(df2)
    df = data_across_strikes(df1, df2)
    


    