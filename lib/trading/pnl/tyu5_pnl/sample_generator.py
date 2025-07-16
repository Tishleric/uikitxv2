
import pandas as pd
import datetime
from typing import Dict
from main import run_pnl_analysis
global today
def create_sample_input_data() -> Dict[str, pd.DataFrame]:
    trades = [
        {'Date': '2024-01-15', 'Time': '09:30:00', 'Symbol': 'TYU5', 'Action': 'BUY',
         'Quantity': 10, 'Price': '119-16', 'Fees': 22.50, 'Counterparty': 'GS'},
        {'Date': '2024-01-17', 'Time': '09:45:00', 'Symbol': 'TYU5', 'Action': 'SELL',
         'Quantity': 3, 'Price': '119-28', 'Fees': 6.75, 'Counterparty': 'C'}
    ]
    trades_df = pd.DataFrame(trades)
    market = [{'Symbol': 'TYU5', 'Current_Price': '119-24', 'Prior_Close': '119-20'}]
    market_df = pd.DataFrame(market)
    return {'Trades_Input': trades_df, 'Market_Prices': market_df}

def read_sample_input(file_path="sample_input.xlsx"):
    # List all sheet names
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names  # e.g., ['Trades_Input', 'Market_Prices', ...]
    
    # Read each sheet into a DataFrame and store in a dict
    sample_data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in sheet_names}
    return sample_data

def main():
    #sample_data = create_sample_input_data()

    input_file = "sample_input.xlsx"
    output_file = "sample_output.xlsx"
    base_price = 119.25
    price_range = (-3,3)
    steps = 10

    # Save sample data to an Excel file for testing
    # with pd.ExcelWriter(input_file) as writer:
    #     sample_data['Trades_Input'].to_excel(writer, sheet_name='Trades_Input', index=False)
    #     sample_data['Market_Prices'].to_excel(writer, sheet_name='Market_Prices', index=False)

    # Run the PnL analysis with the sample data


# Usage
    sample_data = read_sample_input("sample_input.xlsx")
    print(sample_data.keys())  # dict_keys(['Trades_Input', 'Market_Prices', ...])
    print(sample_data['Trades_Input'].head())
    run_pnl_analysis(input_file, output_file, base_price, price_range, steps, sample_data)
    print(f"PnL analysis completed. Output saved to {output_file}")
    print(f"Sample data used for testing: {sample_data}")
    print(f"Base price: {base_price}, Price range: {price_range}, Steps: {steps}")

if __name__ == "__main__":
    main()
