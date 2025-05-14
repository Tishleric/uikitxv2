#!/usr/bin/env python
"""
Script to fetch and list instruments for a specific product (ZN 10-Year T-Note)
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
ZN_PRODUCT_ID = "16143309052651006928"  # From cme_products_market_7.json

def main():
    """Fetch and list instruments for ZN product."""
    print("Initializing TT Token Manager...")
    token_manager = TTTokenManager(
        api_key=tt_config.TT_API_KEY,
        api_secret=tt_config.TT_API_SECRET,
        app_name=tt_config.APP_NAME,
        company_name=tt_config.COMPANY_NAME,
        environment=tt_config.ENVIRONMENT,
        token_file=tt_config.TOKEN_FILE
    )

    print("\nAttempting to get token...")
    token = token_manager.get_token()
    if not token:
        print("\nFailed to acquire token. Exiting.")
        return
    print("Token acquired.")

    environment_path = 'ext_uat_cert' if tt_config.ENVIRONMENT == 'UAT' else 'ext_prod_live'
    service = "ttpds"
    endpoint = "/instruments"
    url = f"{TT_API_BASE_URL}/{service}/{environment_path}{endpoint}"

    req_id = token_manager.create_request_id() # Get a fresh request ID
    params = {
        "productId": ZN_PRODUCT_ID,
        "requestId": req_id
    }

    headers = {
        "x-api-key": tt_config.TT_API_KEY,
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

        instrument_count = len(data.get('instruments', []))
        print(f"\nSuccess! Found {instrument_count} instruments for ZN (Product ID: {ZN_PRODUCT_ID})")

        output_filename = f"zn_instruments_product_{ZN_PRODUCT_ID}.json"
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Full response saved to '{output_filename}'")

        print("\nListing all instruments (Name - InstrumentID - Contract Month - Maturity Date):")
        if data.get('instruments'):
            for instrument in data['instruments']:
                # Example: Extracting common fields, actual fields might vary
                instr_name = instrument.get('name', 'N/A')
                instr_id = instrument.get('id', 'N/A')
                contract_month = instrument.get('contractMonth', 'N/A') # Assuming this field exists
                maturity_date = instrument.get('maturityDate', 'N/A') # Assuming this field exists
                print(f"  - {instr_name} - ID: {instr_id} - Contract: {contract_month} - Maturity: {maturity_date}")
        else:
            print("  No instruments found in the response.")

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
    except Exception as err:
        print(f"\nAn other error occurred: {err}")

if __name__ == "__main__":
    main() 