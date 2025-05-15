#!/usr/bin/env python
"""
Script to fetch detailed information for a specific instrument (ZN Jun25)
from the TT REST API.
"""

import sys
import os
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from TTRestAPI.token_manager import TTTokenManager
from TTRestAPI import tt_config
import requests

TT_API_BASE_URL = "https://ttrestapi.trade.tt"
# ZN Jun25 Instrument ID from zn_instruments_product_*.json
ZN_JUN25_INSTRUMENT_ID = "4877721789746411490" 

def main():
    """Fetch and display details for the ZN Jun25 instrument."""
    print("Initializing TT Token Manager...")
    token_manager = TTTokenManager(
        # api_key and api_secret are now loaded by TokenManager based on environment
        app_name=tt_config.APP_NAME, # Can be omitted if default from config is desired
        company_name=tt_config.COMPANY_NAME, # Can be omitted if default from config is desired
        environment=tt_config.ENVIRONMENT, 
        token_file_base=tt_config.TOKEN_FILE, # Pass the base name
        config_module=tt_config # Pass the config module for robust credential loading
    )

    print("\nAttempting to get token...")
    token = token_manager.get_token()
    if not token:
        print("\nFailed to acquire token. Exiting.")
        return
    print("Token acquired.")

    environment_path = 'ext_uat_cert' # This needs to be dynamic based on token_manager
    if tt_config.ENVIRONMENT.upper() == 'UAT':
        environment_path = 'ext_uat_cert'
    elif tt_config.ENVIRONMENT.upper() == 'SIM':
        environment_path = 'ext_prod_sim'
    elif tt_config.ENVIRONMENT.upper() == 'LIVE':
        environment_path = 'ext_prod_live'
    # Or, more robustly, use the one from token_manager instance:
    # environment_path = token_manager.env_path_segment

    service = "ttpds"
    # Endpoint uses a path parameter for instrumentId
    endpoint = f"/instrument/{ZN_JUN25_INSTRUMENT_ID}"
    # Use token_manager.env_path_segment for the URL
    url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"

    req_id = token_manager.create_request_id() # Get a fresh request ID
    params = {
        "requestId": req_id
        # No other params like productId needed here, instrumentId is in the path
    }

    headers = {
        "x-api-key": token_manager.api_key,  # Use the API key from the token_manager instance
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print(f"\nMaking API request to: {url}")
    print(f"Request headers: {headers}")
    print(f"Request params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        print(f"\nSuccess! Fetched details for ZN Jun25 (Instrument ID: {ZN_JUN25_INSTRUMENT_ID})")

        output_filename = f"zn_jun25_instr_details_{ZN_JUN25_INSTRUMENT_ID}.json"
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Full response saved to '{output_filename}'")

        print("\nInstrument Details:")
        # Print the whole JSON structure prettily for inspection
        print(json.dumps(data, indent=2))
        
        # Specifically look for and print common price-related fields if they exist
        print("\nPotential Price Information:")
        price_fields = ['lastPx', 'bidPx', 'askPx', 'settlementPx', 'highPx', 'lowPx', 'openPx', 'closePx', 'volume']
        found_price_info = False
        for field in price_fields:
            if field in data:
                print(f"  {field}: {data[field]}")
                found_price_info = True
        if not found_price_info:
            print("  No common direct price fields (lastPx, bidPx, etc.) found in the root of the response.")
            print("  Price data might be nested, part of a different structure, or not available via this endpoint.")

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
    except Exception as err:
        print(f"\nAn other error occurred: {err}")

if __name__ == "__main__":
    main() 