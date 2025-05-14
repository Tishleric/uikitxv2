#!/usr/bin/env python
"""
Example script to demonstrate using TTTokenManager with the TT REST API.
This shows how to make any TT REST API request with proper authentication.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import the token manager and config
from TTRestAPI.token_manager import TTTokenManager
from TTRestAPI import tt_config

def make_api_request(token_manager, service, endpoint, method="GET", data=None):
    """
    Make an authenticated request to the TT REST API.
    
    Args:
        token_manager: Instance of TTTokenManager
        service: Service name (e.g., 'ttpds', 'ttuser')
        endpoint: API endpoint
        method: HTTP method (GET, POST, etc.)
        data: Data to send for POST/PUT requests
        
    Returns:
        Response object
    """
    # Build the URL
    environment = 'ext_uat_cert' if tt_config.ENVIRONMENT == 'UAT' else 'ext_prod_live'
    base_url = f"https://ttrestapi.trade.tt/{service}/{environment}"
    
    # Ensure endpoint starts with a slash
    if not endpoint.startswith('/'):
        endpoint = f"/{endpoint}"
    
    # Build the full URL with request ID
    url = f"{base_url}{endpoint}"
    
    # Get request ID parameter and authentication header
    params = token_manager.get_request_params()
    headers = {
        "x-api-key": tt_config.TT_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Add authorization header
    auth_header = token_manager.get_auth_header()
    headers.update(auth_header)
    
    # Make the request based on the method
    print(f"Making {method} request to {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, params=params, json=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, params=params, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers, params=params)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    return response

def main():
    """
    Example of using the TTTokenManager to make an API request.
    """
    # Initialize the token manager
    token_manager = TTTokenManager(
        api_key=tt_config.TT_API_KEY,
        api_secret=tt_config.TT_API_SECRET,
        app_name=tt_config.APP_NAME,
        company_name=tt_config.COMPANY_NAME,
        environment=tt_config.ENVIRONMENT,
        token_file=tt_config.TOKEN_FILE
    )
    
    # Example 1: Get exchanges (ttpds service)
    print("\n=== Example 1: Get exchanges ===")
    response = make_api_request(token_manager, "ttpds", "/exchanges")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Found {len(data.get('exchanges', []))} exchanges")
        # Print the first few exchanges as an example
        for exchange in data.get('exchanges', [])[:3]:
            print(f"  - {exchange.get('name')} ({exchange.get('id')})")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Example 2: Get user information (ttuser service)
    print("\n=== Example 2: Get user information ===")
    response = make_api_request(token_manager, "ttuser", "/users/self")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success! User info retrieved")
        print(f"  Username: {data.get('username')}")
        print(f"  Email: {data.get('email')}")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    main() 