# TTRestAPI/examples/get_current_position.py
import os
import sys
import uuid
import json
import requests

# --- Add project root to sys.path ---
# Assuming this script is in TTRestAPI/examples, the project root is two levels up.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TTRestAPI_path = os.path.join(project_root, 'TTRestAPI')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if TTRestAPI_path not in sys.path:
    sys.path.insert(0, TTRestAPI_path)
# --- End sys.path modification ---

try:
    from token_manager import TTTokenManager
    import tt_config # Default tt_config.py from TTRestAPI directory
    print("Successfully imported TTTokenManager and tt_config.")
except ImportError as e:
    print(f"Error importing TTTokenManager or tt_config: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

def fetch_current_positions(token_manager_instance):
    """
    Fetches current positions from the TT REST API (ttmonitor service).

    Args:
        token_manager_instance (TTTokenManager): An initialized instance of TTTokenManager.

    Returns:
        dict: The JSON response from the API, or None if an error occurs.
    """
    token = token_manager_instance.get_token()
    if not token:
        print("Failed to acquire token.")
        return None

    service = "ttmonitor"
    endpoint = "position" # Endpoint for getting positions
    # Construct the full URL: https://ttrestapi.trade.tt/ttmonitor/<env>/position
    base_url = tt_config.TT_API_BASE_URL 
    url = f"{base_url}/{service}/{token_manager_instance.env_path_segment}/{endpoint}"
    
    request_id = token_manager_instance.create_request_id()
    
    headers = {
        "x-api-key": token_manager_instance.api_key,
        "accept": "application/json", # Important for GET requests
        "Authorization": f"Bearer {token}"
    }
    
    # Optional: Filter by accountId(s)
    # params = {"requestId": request_id, "accountIds": "YOUR_ACCOUNT_ID_1,YOUR_ACCOUNT_ID_2"}
    params = {"requestId": request_id} 

    print(f"Making API request to: {url}")
    print(f"Request headers: {{key: 'value' for key, value in headers.items() if key != 'Authorization'}} ... Authorization: Bearer <token>")
    print(f"Request params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        response_json = response.json()
        print("API request successful.")
        return response_json

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - {http_err.response.text if http_err.response else 'No response text'}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response. Raw response: {response.text[:500]}...") # Print first 500 chars
    return None

if __name__ == "__main__":
    print(f"Initializing TT Token Manager for environment: {tt_config.ENVIRONMENT}...")
    
    # Determine which keys to check based on the environment
    required_keys = []
    if tt_config.ENVIRONMENT == "SIM":
        required_keys = ['TT_SIM_API_KEY', 'TT_SIM_API_SECRET', 'TT_API_KEY'] # TT_API_KEY is used by token manager regardless
        if not all([hasattr(tt_config, key) for key in required_keys]):
            print(f"Error: For SIM environment, one or more of {required_keys} not found in tt_config.py.")
            print("Please ensure these are configured in TTRestAPI/tt_config.py.")
            sys.exit(1)
    elif tt_config.ENVIRONMENT == "UAT": # Or any other env that uses the primary keys
        required_keys = ['TT_API_KEY', 'TT_APP_SECRET'] # Assuming TT_APP_SECRET is what was intended for UAT secret
        if not all([hasattr(tt_config, key) for key in required_keys]):
            # Adjusted error message to reflect TT_APP_SECRET might be the one for UAT.
            print(f"Error: For {tt_config.ENVIRONMENT} environment, TT_API_KEY or TT_APP_SECRET (or intended UAT secret) not found in tt_config.py.")
            print("Please ensure these are configured in TTRestAPI/tt_config.py.")
            sys.exit(1)
    else: # Default to checking standard keys for other environments like LIVE
        required_keys = ['TT_API_KEY', 'TT_APP_SECRET'] 
        if not all([hasattr(tt_config, key) for key in required_keys]):
            print(f"Error: TT_API_KEY or TT_APP_SECRET not found in tt_config.py for environment {tt_config.ENVIRONMENT}.")
            print("Please ensure these are configured in TTRestAPI/tt_config.py.")
            sys.exit(1)

    # Instantiate the token manager
    token_manager = TTTokenManager(
        environment=tt_config.ENVIRONMENT,
        token_file_base=tt_config.TOKEN_FILE, 
        config_module=tt_config 
    )

    position_data = fetch_current_positions(token_manager)

    if position_data:
        output_filename = "my_current_position_response.json"
        output_path = os.path.join(os.path.dirname(__file__), output_filename) # Save in the same directory as the script
        
        try:
            with open(output_path, 'w') as f:
                json.dump(position_data, f, indent=2)
            print(f"Full position response saved to '{output_path}'")
        except IOError as e:
            print(f"Error saving position data to file: {e}")

        print("\n--- Current Position Data Sample ---")
        if isinstance(position_data, dict) and 'fills' in position_data: # Assuming 'fills' is the key for position items, adjust if different
            # Print a few sample position items if available, or the whole thing if small
            sample_positions = position_data['fills'][:3] if len(position_data['fills']) > 3 else position_data['fills']
            for i, pos in enumerate(sample_positions):
                print(f"Position Item {i+1}: {pos}")
        elif isinstance(position_data, list) and position_data: # If the response is a list of positions
             sample_positions = position_data[:3] if len(position_data) > 3 else position_data
             for i, pos in enumerate(sample_positions):
                print(f"Position Item {i+1}: {pos}")
        else:
            print(json.dumps(position_data, indent=2)) # Print the whole response if structure is unknown or small
    else:
        print("Failed to fetch or process position data.") 