#!/usr/bin/env python3
"""
Example script demonstrating how to process option data from CSV using the simplified API.

This script shows how to:
1. Read option data from CSV (price, strike, time to expiry, market price)
2. Calculate implied volatility for each option
3. Calculate all Greeks
4. Write the enhanced data back to CSV
"""

import pandas as pd
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from lib.trading.bond_future_options.api import (
    calculate_implied_volatility,
    calculate_greeks,
    quick_analysis,
    process_option_batch
)


def process_csv_with_api(input_file: str, output_file: str):
    """
    Process option data from CSV and add volatility and Greeks.
    
    Expected CSV columns:
    - F: Future price
    - K: Strike price  
    - T: Time to expiry (in years)
    - market_price: Option market price (decimal format)
    - option_type: 'call' or 'put' (optional, defaults to 'put')
    """
    
    # Read CSV data
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    # Validate required columns
    required_cols = ['F', 'K', 'T', 'market_price']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Add option_type if missing
    if 'option_type' not in df.columns:
        df['option_type'] = 'put'
    
    # Convert DataFrame to list of dictionaries for batch processing
    options_data = df.to_dict('records')
    
    # Process all options
    print(f"Processing {len(options_data)} options...")
    results = process_option_batch(options_data)
    
    # Extract results back to DataFrame
    processed_data = []
    for result in results:
        if result['success']:
            # Flatten the result for CSV output
            flat_result = {
                'F': result['F'],
                'K': result['K'],
                'T': result['T'],
                'market_price': result['market_price'],
                'option_type': result['option_type'],
                'implied_volatility': result['volatility'],
                # Main Greeks
                'delta_F': result['greeks']['delta_F'],
                'delta_y': result['greeks']['delta_y'],
                'gamma_y': result['greeks']['gamma_y'],
                'vega_y': result['greeks']['vega_y'],
                'theta_F': result['greeks']['theta_F'],
                # Higher-order Greeks
                'volga_price': result['greeks']['volga_price'],
                'vanna_F_price': result['greeks']['vanna_F_price'],
                'charm_F': result['greeks']['charm_F'],
                'speed_F': result['greeks']['speed_F'],
                'color_F': result['greeks']['color_F']
            }
        else:
            # If calculation failed, include error info
            flat_result = {
                'F': result['F'],
                'K': result['K'],
                'T': result['T'],
                'market_price': result['market_price'],
                'option_type': result['option_type'],
                'error': result['error']
            }
        
        processed_data.append(flat_result)
    
    # Create output DataFrame
    output_df = pd.DataFrame(processed_data)
    
    # Write to CSV
    print(f"Writing results to {output_file}...")
    output_df.to_csv(output_file, index=False)
    
    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    print(f"\nProcessing complete:")
    print(f"  - Successful: {successful}")
    print(f"  - Failed: {failed}")
    
    return output_df


def create_sample_csv(filename: str):
    """Create a sample CSV file with option data."""
    
    sample_data = pd.DataFrame({
        'F': [110.75, 110.75, 110.75, 110.75, 110.75],
        'K': [110.00, 110.25, 110.50, 110.75, 111.00],
        'T': [0.05, 0.05, 0.05, 0.05, 0.05],  # ~18 days to expiry
        'market_price': [0.890625, 0.640625, 0.359375, 0.203125, 0.109375],
        'option_type': ['put', 'put', 'put', 'put', 'put']
    })
    
    sample_data.to_csv(filename, index=False)
    print(f"Created sample CSV: {filename}")
    

def demonstrate_single_option():
    """Demonstrate API usage for a single option."""
    
    print("\n" + "="*60)
    print("Single Option Analysis Example")
    print("="*60)
    
    # Option parameters
    F = 110.75  # Future price
    K = 110.50  # Strike price
    T = 0.05    # Time to expiry (years)
    market_price = 0.359375  # Market price (decimal)
    
    # Method 1: Calculate implied volatility only
    print("\n1. Calculating implied volatility...")
    vol = calculate_implied_volatility(F, K, T, market_price)
    print(f"   Implied volatility: {vol:.2f}")
    
    # Method 2: Calculate Greeks using the implied volatility
    print("\n2. Calculating Greeks...")
    greeks = calculate_greeks(F, K, T, vol)
    print(f"   Delta (Y-space): {greeks['delta_y']:.2f}")
    print(f"   Gamma (Y-space): {greeks['gamma_y']:.2f}")
    print(f"   Vega (Y-space): {greeks['vega_y']:.2f}")
    print(f"   Theta (F-space): {greeks['theta_F']:.2f}")
    
    # Method 3: Complete analysis in one call
    print("\n3. Quick analysis (all-in-one)...")
    analysis = quick_analysis(F, K, T, market_price)
    print(f"   Implied vol: {analysis['implied_volatility']:.2f}")
    print(f"   Yield vol: {analysis['yield_volatility']:.2f}")
    print(f"   Daily theta: ${analysis['risk_metrics']['daily_theta']:.2f}")
    print(f"   Dollar delta (1bp): ${analysis['risk_metrics']['dollar_delta_1bp']:.2f}")
    print(f"   Time value: ${analysis['risk_metrics']['time_value']:.6f}")


if __name__ == "__main__":
    # Set up file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_input = os.path.join(script_dir, "sample_options.csv")
    sample_output = os.path.join(script_dir, "options_with_greeks.csv")
    
    # Demonstrate single option analysis
    demonstrate_single_option()
    
    # Create and process sample CSV
    print("\n" + "="*60)
    print("CSV Processing Example")
    print("="*60)
    
    # Create sample data
    create_sample_csv(sample_input)
    
    # Process the CSV
    result_df = process_csv_with_api(sample_input, sample_output)
    
    # Display first few rows
    print("\nFirst few rows of output:")
    print(result_df.head())
    
    print(f"\nFull results saved to: {sample_output}") 