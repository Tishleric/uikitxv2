#!/usr/bin/env python
"""
Script to fetch and display order-related enumerations from the TT REST API.
This data provides human-readable definitions for various codes used in order objects,
(e.g., orderStatus, orderType, side).
"""

import sys
import os
import json
import requests
from pprint import pprint

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from TTRestAPI.token_manager import TTTokenManager
    from TTRestAPI import tt_config
except ImportError as e:
    print(f"Error importing TTRestAPI modules: {e}")
    print(f"Attempted project_root: {project_root}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

TT_API_BASE_URL = "https://ttrestapi.trade.tt"

def main():
    """Fetch and display order enumeration data from the TT REST API."""
    print(f"Initializing TT Token Manager for environment: {tt_config.ENVIRONMENT}...")
    
    try:
        token_manager = TTTokenManager(
            environment=tt_config.ENVIRONMENT,
            token_file_base=tt_config.TOKEN_FILE,
            config_module=tt_config
        )
    except Exception as e:
        print(f"Error initializing TTTokenManager: {e}")
        return
        
    print("\nAttempting to get token...")
    token = token_manager.get_token()

    if not token:
        print("\nFailed to acquire token. Exiting.")
        return
    
    print("Token acquired.")
    
    service = "ttledger"
    endpoint = "/orderdata" # Endpoint to get enumeration definitions
    url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
    
    request_id = token_manager.create_request_id()
    params = {"requestId": request_id}

    headers = {
        "x-api-key": token_manager.api_key,
        "accept": "application/json",
        "Authorization": f"Bearer {token}" 
    }
    
    print(f"\nMaking API request to: {url}")
    # Avoid printing full token for security, just indicate its presence
    print(f"Request headers: {{key: 'value' for key, value in headers.items() if key != 'Authorization'}} ... Authorization: Bearer <token>")
    print(f"Request params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        data = response.json()
        
        # Save the full response to a file in the ladderTest directory for inspection
        # as the ladder app will use it.
        ladderTest_dir = os.path.join(project_root, "ladderTest")
        if not os.path.exists(ladderTest_dir):
            os.makedirs(ladderTest_dir)
        output_filename = os.path.join(ladderTest_dir, "order_enumerations.json")
        
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nFull response saved to '{output_filename}'")

        print("\n--- Order Enumeration Data Sample ---")
        # Print a sample of the data, e.g., 'side' and 'orderStatus' if they exist
        if 'side' in data:
            print("\nSide Definitions:")
            pprint(data['side'])
        
        if 'orderStatus' in data:
            print("\nOrder Status Definitions:")
            pprint(data['orderStatus'])

        if 'orderType' in data:
            print("\nOrder Type Definitions:")
            pprint(data['orderType'])
            
        print("\nReview the full output in 'ladderTest/order_enumerations.json' for all fields.")

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err} - Status: {getattr(http_err.response, 'status_code', 'N/A')}")
        print(f"Response text: {getattr(http_err.response, 'text', 'No response text')}")
        if hasattr(http_err.response, 'json'):
            try:
                pprint(http_err.response.json())
            except:
                pass # Ignore if response is not json
    except requests.exceptions.RequestException as req_err:
        print(f"\nRequest error occurred: {req_err}")
    except json.JSONDecodeError:
        print(f"\nFailed to decode JSON from response. Raw response text: {response.text if 'response' in locals() else 'N/A'}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 