#!/usr/bin/env python
"""
Script to fetch and display all ADL algorithm IDs and names
accessible via the TT REST API for the configured credentials.
"""

import sys
import os
import json
from pprint import pprint
import requests

# Add the project root to the Python path so we can import from TTRestAPI
# Assuming this script is in TTRestAPI/examples/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Go one level higher
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from TTRestAPI.token_manager import TTTokenManager
    from TTRestAPI import tt_config
except ImportError as e:
    print(f"Error importing TTRestAPI modules: {e}")
    # Provide more context for path issues if they occur
    print(f"Attempted project_root: {project_root}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

# Define the correct base URL
TT_API_BASE_URL = "https://ttrestapi.trade.tt"

def main():
    """Fetch and display ADL algorithms from the TT REST API."""
    print("Initializing TT Token Manager...")
    
    try:
        token_manager = TTTokenManager(
            api_key=tt_config.TT_API_KEY,
            api_secret=tt_config.TT_API_SECRET,
            app_name=getattr(tt_config, 'APP_NAME', "GetAlgosScript"),
            company_name=getattr(tt_config, 'COMPANY_NAME', "MyCompany"),
            environment=tt_config.ENVIRONMENT,
            token_file=getattr(tt_config, 'TOKEN_FILE', os.path.join(project_root, 'tt_token.json'))
        )
    except AttributeError as e:
        print(f"Configuration error in tt_config.py: {e}. Please ensure all required fields are present.")
        return
    except Exception as e:
        print(f"Error initializing TTTokenManager: {e}")
        return
        
    print("\nAttempting to get token...")
    token = token_manager.get_token()

    if not token:
        print("\nFailed to acquire token. Exiting.")
        return
    
    print("Token acquired.")
    
    environment_path = 'ext_uat_cert' if tt_config.ENVIRONMENT == 'UAT' else 'ext_prod_live'
    service = "ttpds"  # As per ttcheatsheet.md, /algos is under ttpds
    endpoint = "/algos"
    url = f"{TT_API_BASE_URL}/{service}/{environment_path}{endpoint}"
    
    # Prepare request ID and headers
    request_id = token_manager.create_request_id()
    params = {"requestId": request_id}
    headers = {
        "x-api-key": tt_config.TT_API_KEY,
        "accept": "application/json",
        "Authorization": f"Bearer {token}" 
    }
    
    print(f"\nMaking API request to: {url}")
    print(f"Request headers: {headers}")
    print(f"Request params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        data = response.json()
        
        # Save the full response for inspection
        output_filename = "my_algos_response.json"
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nFull response saved to '{output_filename}'")

        algos_list = data.get('algos', []) # Assuming the key for the list is 'algos'
                                          # This might also be data directly if it's just a list.
                                          # Or data.get('algorithms') etc. Will confirm from output.

        if not algos_list and isinstance(data, list): # If the root is a list
            algos_list = data

        if algos_list:
            print(f"\nFound {len(algos_list)} algorithms:")
            for algo in algos_list:
                # Attempt to get common fields, will adjust based on actual response
                algo_id = algo.get('id') or algo.get('algoId') or algo.get('algorithmId')
                algo_name = algo.get('name') or algo.get('algoName') or algo.get('algorithmName')
                algo_owner = algo.get('ownerId') or algo.get('userId') # Or similar
                
                print(f"  - Name: {algo_name if algo_name else 'N/A'}, ID: {algo_id if algo_id else 'N/A'}, Owner: {algo_owner if algo_owner else 'N/A'}")
        else:
            print("\nNo algorithms found in the response, or the structure was unexpected.")
            print("Please check 'my_algos_response.json' for the raw data.")

        if 'lastPage' in data and data['lastPage'] == 'false':
            print("\nWARNING: The API response indicates this is not the last page. Pagination handling may be needed.")

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err} - Status: {getattr(http_err.response, 'status_code', 'N/A')}")
        print(f"Response text: {getattr(http_err.response, 'text', 'No response text')}")
    except requests.exceptions.RequestException as req_err:
        print(f"\nRequest error occurred: {req_err}")
    except json.JSONDecodeError:
        print(f"\nFailed to decode JSON from response. Raw response text: {response.text if 'response' in locals() else 'N/A'}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 