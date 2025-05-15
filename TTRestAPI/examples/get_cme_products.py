#!/usr/bin/env python
"""
Script to fetch and list products for a specific market (CME) from the TT REST API.
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
CME_MARKET_ID = "7"

def main():
    """Fetch and list products for CME market."""
    print("Initializing TT Token Manager...")
    token_manager = TTTokenManager(
        environment=tt_config.ENVIRONMENT,
        token_file_base=tt_config.TOKEN_FILE,
        config_module=tt_config
    )

    print("\nAttempting to get token...")
    token = token_manager.get_token()
    if not token:
        print("\nFailed to acquire token. Exiting.")
        return
    print("Token acquired.")

    service = "ttpds"
    endpoint = "/products"
    url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"

    req_id = token_manager.create_request_id() # Get a fresh request ID
    params = {
        "marketId": CME_MARKET_ID,
        "requestId": req_id
    }

    headers = {
        "x-api-key": token_manager.api_key,
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

        product_count = len(data.get('products', []))
        print(f"\nSuccess! Found {product_count} products for CME (Market ID: {CME_MARKET_ID})")

        output_filename = f"cme_products_market_{CME_MARKET_ID}.json"
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Full response saved to '{output_filename}'")

        print("\nListing all products (Name - Symbol - ProductID):")
        if data.get('products'):
            for product in data['products']:
                print(f"  - {product.get('name')} - {product.get('productSymbol')} - {product.get('id')}")
        else:
            print("  No products found in the response.")

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
    except Exception as err:
        print(f"\nAn other error occurred: {err}")

if __name__ == "__main__":
    main() 