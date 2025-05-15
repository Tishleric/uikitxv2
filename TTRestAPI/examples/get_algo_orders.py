#!/usr/bin/env python
"""
Script to fetch and display working orders, attempting to identify those
related to a specific algorithm from the TT REST API.
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
TARGET_ALGO_NAME = "5MartingaleAPITEST" # As identified from previous script
TARGET_ALGO_ID = "10628608476345732679" # As identified from previous script
TARGET_ALGO_OWNER_ID = 1168910 # As identified from previous script (ownerId of the algo definition)

def main():
    """Fetch and display working orders from the TT REST API."""
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
    
    # Using ttledger service for orders
    service = "ttledger" 
    endpoint = "/orders"
    url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
    
    request_id = token_manager.create_request_id()
    params = {"requestId": request_id}
    # Potentially add other filters like accountId, instrumentId if your algo trades on a specific one
    # params["includeOrdersWithNoFills"] = "true" # Example, check API docs for available params

    headers = {
        "x-api-key": token_manager.api_key,
        "accept": "application/json",
        "Authorization": f"Bearer {token}" 
    }
    
    print(f"\nMaking API request to: {url}")
    print(f"Request headers: {{key: 'value' for key, value in headers.items() if key != 'Authorization'}} ... Authorization: Bearer <token>") # Avoid printing full token
    print(f"Request params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        data = response.json()
        
        output_filename = "my_working_orders_response.json"
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nFull response saved to '{output_filename}'")

        orders = data.get('orders', [])

        if not orders and isinstance(data, list): # If the root is a list
            orders = data
            
        if orders:
            print(f"\nFound {len(orders)} working orders:")
            matched_orders = 0
            for i, order in enumerate(orders):
                # --- Attempt to identify orders from the target algorithm ---
                # Check common fields. The exact fields depend on TT REST API's response structure for orders.
                # We're looking for algoId, specific text tags, or if the order's user matches the algo owner.
                
                is_target_algo_order = False
                reason = []

                # Check 1: Direct Algo ID match (if field exists)
                if str(order.get('algoId')) == TARGET_ALGO_ID:
                    is_target_algo_order = True
                    reason.append(f"algoId match ({TARGET_ALGO_ID})")
                
                # Check 2: User ID match (if order has a userId field and it matches algo owner)
                # Note: The API might show orders for the user whose API key is used, not necessarily the algo owner directly on each order.
                # This check might be more relevant if orders are filtered by a specific user who owns the algo.
                if str(order.get('userId')) == str(TARGET_ALGO_OWNER_ID): # Compare as strings
                    # This might be too broad if the API key user is the algo owner and has manual orders
                    # is_target_algo_order = True # Commenting out to avoid over-matching initially
                    reason.append(f"userId match ({TARGET_ALGO_OWNER_ID}) - (potential broad match)")


                # Check 3: Text fields (common for custom algo tags)
                # Common fields are 'textA', 'textB', 'textC', 'miscText', 'orderTag'
                custom_tags_to_check = ['textA', 'textB', 'textC', 'miscText', 'orderTag']
                for tag_field in custom_tags_to_check:
                    if order.get(tag_field) and TARGET_ALGO_NAME in str(order.get(tag_field)):
                        is_target_algo_order = True
                        reason.append(f"{tag_field} contains '{TARGET_ALGO_NAME}'")
                    elif order.get(tag_field) and TARGET_ALGO_ID in str(order.get(tag_field)):
                         is_target_algo_order = True
                         reason.append(f"{tag_field} contains '{TARGET_ALGO_ID}'")


                if is_target_algo_order:
                    print(f"\n--- MATCHED ALGO ORDER (Reason: {', '.join(reason)}) ---")
                    matched_orders += 1
                elif i < 5 : # Print first few non-matching orders for schema inspection
                     print(f"\n--- Sample Order {i+1} (Not Matched to Target Algo) ---")
                
                if is_target_algo_order or i < 5: # Print details for matched or first few samples
                    pprint(order)
                    # Essential fields to display for any order:
                    # print(f"  ID: {order.get('orderId', 'N/A')}, Instr: {order.get('instrumentId', 'N/A')}, Side: {order.get('side')}")
                    # print(f"  Qty: {order.get('orderQty', 'N/A')}, Price: {order.get('price', 'N/A')}, Status: {order.get('ordStatus')}")
                    # print(f"  AlgoID: {order.get('algoId', 'N/A')}, TextA: {order.get('textA', 'N/A')}, OrderTag: {order.get('orderTag', 'N/A')}")

            if matched_orders == 0:
                print(f"\nNo orders explicitly matched to algorithm '{TARGET_ALGO_NAME}' (ID: {TARGET_ALGO_ID}).")
                print("Inspect 'my_working_orders_response.json' and the sample orders above to identify relevant fields for filtering.")
            else:
                print(f"\nFound {matched_orders} orders potentially related to '{TARGET_ALGO_NAME}'.")

        else:
            print("\nNo working orders found or the response structure was unexpected.")
            print("Please check 'my_working_orders_response.json' for the raw data.")

        if 'lastPage' in data and data.get('lastPage') == 'false':
            print("\nWARNING: The API response indicates this is not the last page. Pagination handling may be needed for a complete list.")

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