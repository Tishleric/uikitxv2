#!/usr/bin/env python
"""
Simple script to demonstrate a single TT REST API call.

This is the most basic example showing how to:
1. Initialize the token manager
2. Make a simple GET request to fetch exchanges
3. Display the results
"""

import sys
import os
import json
from pprint import pprint

# Add the project root to the Python path so we can import from TTRestAPI
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Import the token manager and config from our package
from TTRestAPI.token_manager import TTTokenManager
from TTRestAPI import tt_config
import requests

# Define the correct base URL as per the updated cheatsheet
TT_API_BASE_URL = "https://ttrestapi.trade.tt" # Changed from apigateway.trade.tt and renamed constant

def main():
    """Make a single API call to fetch exchanges from TT REST API."""
    print("Initializing TT Token Manager...")
    
    # Initialize token manager with credentials from config file
    token_manager = TTTokenManager(
        # api_key, api_secret, app_name, company_name are loaded by TokenManager based on environment
        environment=tt_config.ENVIRONMENT,
        token_file_base=tt_config.TOKEN_FILE, # Pass the base name
        config_module=tt_config # Pass the config module
    )
    
    print("\nAttempting to get token...")
    token = token_manager.get_token() # No force_refresh needed for normal operation

    if not token:
        print("\nFailed to acquire token. Exiting.")
        return
    
    print("Token acquired.")
    
    # Build the URL (ensure lowercase service name as noted in documentation)
    # Use token_manager.env_path_segment for the URL
    service = "ttpds"  # Product Data Service, still ttpds for /markets
    url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}/markets" 
    
    # Get request parameters (includes requestId)
    params = token_manager.get_request_params()
    
    # Prepare headers
    headers = {
        "x-api-key": token_manager.api_key,      # Use API key from token_manager instance
        "accept": "application/json"           
        # No "Content-Type" for GET requests as per successful cURL example
    }
    
    # Add authorization header with the token
    auth_header = token_manager.get_auth_header() # This correctly returns {"Authorization": "Bearer <token>"}
    headers.update(auth_header)
    
    # Make the request
    print(f"\nMaking API request to: {url}")
    print(f"Request headers: {headers}")
    print(f"Request params: {params}")
    response = requests.get(url, headers=headers, params=params)
    
    # Process the response
    if response.status_code == 200:
        data = response.json()
        # Adjust for /markets response structure if needed for printing
        market_count = len(data.get('markets', [])) 
        
        print(f"\nSuccess! Found {market_count} markets")
        print("\nFirst 3 markets:")
        
        # Print the first few markets
        for market in data.get('markets', [])[:3]: # Changed from 'exchanges' to 'markets'
            print(f"  - {market.get('name')} ({market.get('id')})")
            
        # Optionally save the full response to a file for inspection
        with open('markets_response.json', 'w') as f: # Changed filename
            json.dump(data, f, indent=2)
            print("\nFull response saved to 'markets_response.json'") # Changed filename
    else:
        print(f"\nError: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    main() 