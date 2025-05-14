#!/usr/bin/env python
"""
Token manager for Trading Technologies REST API based on the successful cURL approach.
"""
import requests
import json
import uuid
import os
import time
from datetime import datetime, timedelta

class TTTokenManager:
    """
    Token manager for Trading Technologies REST API.
    Handles token acquisition, storage, and automatic refreshing.
    """
    
    def __init__(self, api_key, api_secret, app_name, company_name, 
                 environment='UAT', token_file='tt_token.json', 
                 auto_refresh=True, refresh_buffer_seconds=600):
        """
        Initialize the token manager with the necessary credentials.
        
        Args:
            api_key (str): The TT REST API application key
            api_secret (str): The TT REST API application secret
            app_name (str): Your application name (used in request IDs)
            company_name (str): Your company name (used in request IDs)
            environment (str): 'UAT' or 'LIVE' environment
            token_file (str): Path to token storage file
            auto_refresh (bool): Whether to auto-refresh tokens before expiry
            refresh_buffer_seconds (int): Seconds before expiry to refresh token
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.app_name = app_name
        self.company_name = company_name
        self.environment = 'ext_uat_cert' if environment == 'UAT' else 'ext_prod_live'
        
        # Always save token file in the TTRestAPI folder
        ttrestapi_dir = os.path.dirname(os.path.abspath(__file__))
        self.token_file = os.path.join(ttrestapi_dir, os.path.basename(token_file))
        
        self.auto_refresh = auto_refresh
        self.refresh_buffer_seconds = refresh_buffer_seconds
        
        self.base_url = f"https://ttrestapi.trade.tt/ttid/{self.environment}"
        self.token_endpoint = f"{self.base_url}/token"
        
        # Token data
        self.token = None
        self.token_type = None
        self.expiry_time = None
        
        # Load token if available
        self._load_token()
    
    def generate_guid(self):
        """Generate a new GUID for the request."""
        return str(uuid.uuid4())
    
    def sanitize_name(self, name):
        """Remove special characters and spaces from name."""
        special_chars = r'$&+,/:;=?@"<>#%{}|\\^~[]` '
        for char in special_chars:
            name = name.replace(char, '')
        return name
    
    def create_request_id(self):
        """Create a properly formatted request ID."""
        app_name_clean = self.sanitize_name(self.app_name)
        company_name_clean = self.sanitize_name(self.company_name)
        guid = self.generate_guid()
        return f"{app_name_clean}-{company_name_clean}--{guid}"
    
    def get_token(self, force_refresh=False):
        """
        Get a valid token, refreshing if necessary.
        
        Args:
            force_refresh (bool): Whether to force a token refresh
            
        Returns:
            str: A valid token, or None if unable to acquire a token
        """
        current_time = datetime.now()
        
        # Check if we need a new token
        if (force_refresh or 
            self.token is None or 
            self.expiry_time is None or 
            (self.auto_refresh and self.expiry_time - timedelta(seconds=self.refresh_buffer_seconds) <= current_time)):
            
            success = self._acquire_token()
            if not success:
                return None
                
        return self.token
    
    def _acquire_token(self):
        """
        Acquire a new token from the TT REST API.
        
        Returns:
            bool: True if token acquisition was successful, False otherwise
        """
        # Generate a request ID
        request_id = self.create_request_id()
        
        # Set up the headers
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Create the data payload for x-www-form-urlencoded
        data = {
            "grant_type": "user_app",
            "app_key": f"{self.api_key}:{self.api_secret}"
        }
        
        # Create the URL with request ID
        url = f"{self.token_endpoint}?requestId={request_id}"
        
        print(f"Attempting to acquire token from: {url}")
        print(f"Token request headers: {headers}")
        print(f"Token request data (for x-www-form-urlencoded): {data}")

        try:
            # Make the request using data parameter for automatic form URL-encoding
            response = requests.post(url, headers=headers, data=data)
            
            # Check if successful
            if response.status_code == 200:
                token_data = response.json()
                
                # Extract the token and expiry information
                self.token = token_data.get('access_token')
                self.token_type = token_data.get('token_type', 'bearer')
                seconds_until_expiry = token_data.get('seconds_until_expiry')
                
                # Calculate the expiry time
                self.expiry_time = datetime.now() + timedelta(seconds=seconds_until_expiry)
                
                # Save the token to file
                self._save_token(token_data)
                
                return True
            else:
                print(f"Failed to acquire token: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error acquiring token: {str(e)}")
            return False
    
    def _load_token(self):
        """
        Load token data from file if available.
        """
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                
                self.token = token_data.get('access_token')
                self.token_type = token_data.get('token_type', 'bearer')
                seconds_until_expiry = token_data.get('seconds_until_expiry')
                acquisition_time_str = token_data.get('acquisition_time')
                
                if self.token and acquisition_time_str and seconds_until_expiry:
                    acquisition_time = datetime.fromisoformat(acquisition_time_str)
                    self.expiry_time = acquisition_time + timedelta(seconds=seconds_until_expiry)
        except Exception as e:
            print(f"Error loading token: {str(e)}")
    
    def _save_token(self, token_data):
        """
        Save token data to file.
        
        Args:
            token_data (dict): Token data to save
        """
        try:
            # Add acquisition time
            token_data['acquisition_time'] = datetime.now().isoformat()
            
            # Ensure directory exists
            token_dir = os.path.dirname(self.token_file)
            if token_dir and not os.path.exists(token_dir):
                os.makedirs(token_dir)
                
            # Save the token data
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
        except Exception as e:
            print(f"Error saving token: {str(e)}")
    
    def get_auth_header(self):
        """
        Get the Authorization header for API requests.
        
        Returns:
            dict: Authorization header, or empty dict if no valid token
        """
        token = self.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def get_request_params(self):
        """
        Get the request ID parameter for API requests.
        
        Returns:
            dict: Request ID parameter as a dict
        """
        return {"requestId": self.create_request_id()}

if __name__ == "__main__":
    # Example usage
    import sys
    
    # Get the absolute path of the parent directory (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)
    
    # Import configuration
    from TTRestAPI import tt_config
    
    token_manager = TTTokenManager(
        api_key=tt_config.TT_API_KEY,
        api_secret=tt_config.TT_API_SECRET,
        app_name=tt_config.APP_NAME,
        company_name=tt_config.COMPANY_NAME,
        environment=tt_config.ENVIRONMENT,
        token_file=tt_config.TOKEN_FILE
    )
    
    token = token_manager.get_token(force_refresh=True)
    if token:
        token_prefix = token[:10]
        token_suffix = token[-10:]
        masked_token = f"{token_prefix}...{token_suffix}"
        print(f"Token acquired successfully: {masked_token}")
        print(f"Token will expire on: {token_manager.expiry_time}")
        sys.exit(0)
    else:
        print("Failed to acquire token")
        sys.exit(1) 