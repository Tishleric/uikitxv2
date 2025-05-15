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
    
    def __init__(self, api_key=None, api_secret=None, app_name=None, company_name=None, 
                 environment='UAT', token_file_base='tt_token.json', 
                 auto_refresh=True, refresh_buffer_seconds=600,
                 config_module=None): # Allow passing config for easier testing/management
        """
        Initialize the token manager with the necessary credentials.
        
        Args:
            api_key (str, optional): The TT REST API application key. If None, loads from config.
            api_secret (str, optional): The TT REST API application secret. If None, loads from config.
            app_name (str, optional): Your application name. If None, loads from config.
            company_name (str, optional): Your company name. If None, loads from config.
            environment (str): 'UAT', 'LIVE', or 'SIM' environment.
            token_file_base (str): Base name for token storage file (e.g., 'tt_token.json').
                                   The actual filename will be like 'tt_token_uat.json'.
            auto_refresh (bool): Whether to auto-refresh tokens before expiry.
            refresh_buffer_seconds (int): Seconds before expiry to refresh token.
            config_module (module, optional): The tt_config module. If None, it's imported.
        """
        if config_module is None:
            from . import tt_config as config_module # Local import
        
        self.app_name = app_name or config_module.APP_NAME
        self.company_name = company_name or config_module.COMPANY_NAME
        self.configured_environment = environment.upper()

        if self.configured_environment == 'UAT':
            self.api_key = api_key or config_module.TT_API_KEY
            self.api_secret = api_secret or config_module.TT_API_SECRET
            self.env_path_segment = 'ext_uat_cert'
        elif self.configured_environment == 'SIM':
            self.api_key = api_key or config_module.TT_SIM_API_KEY
            self.api_secret = api_secret or config_module.TT_SIM_API_SECRET
            self.env_path_segment = 'ext_prod_sim'
        elif self.configured_environment == 'LIVE':
            # Assuming LIVE credentials would be TT_LIVE_API_KEY, TT_LIVE_API_SECRET if added
            # For now, let's make it explicit that they are not yet defined in current tt_config
            if hasattr(config_module, 'TT_LIVE_API_KEY') and hasattr(config_module, 'TT_LIVE_API_SECRET'):
                self.api_key = api_key or config_module.TT_LIVE_API_KEY
                self.api_secret = api_secret or config_module.TT_LIVE_API_SECRET
            else:
                raise ValueError("LIVE environment selected but TT_LIVE_API_KEY/SECRET not found in tt_config.py")
            self.env_path_segment = 'ext_prod_live'
        else:
            raise ValueError(f"Unsupported environment: {self.configured_environment}. Must be 'UAT', 'SIM', or 'LIVE'.")

        ttrestapi_dir = os.path.dirname(os.path.abspath(__file__))
        token_file_name, token_file_ext = os.path.splitext(os.path.basename(token_file_base))
        # Create environment-specific token filename, e.g., tt_token_sim.json
        self.token_file = os.path.join(ttrestapi_dir, f"{token_file_name}_{self.configured_environment.lower()}{token_file_ext}")
        
        self.auto_refresh = auto_refresh
        self.refresh_buffer_seconds = refresh_buffer_seconds
        
        self.base_url = f"https://ttrestapi.trade.tt/ttid/{self.env_path_segment}"
        self.token_endpoint = f"{self.base_url}/token"
        
        # Token data
        self.token = None
        self.token_type = None
        self.expiry_time = None # Stored as datetime object
        
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
        # Ensure api_key and api_secret for app_key are from the correct environment instance variables
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
                
                if seconds_until_expiry is None:
                    print(f"Error: 'seconds_until_expiry' not found in token response: {token_data}")
                    self.token = None # Invalidate token
                    return False

                # Calculate the expiry time
                self.expiry_time = datetime.now() + timedelta(seconds=int(seconds_until_expiry))
                
                # Save the token to file
                self._save_token(token_data, seconds_until_expiry) # Pass seconds_until_expiry
                
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
                # Load seconds_until_expiry and acquisition_time for accurate expiry calculation
                seconds_until_expiry_on_save = token_data.get('seconds_until_expiry_on_save')
                acquisition_time_str = token_data.get('acquisition_time')
                
                if self.token and acquisition_time_str and seconds_until_expiry_on_save is not None:
                    acquisition_time = datetime.fromisoformat(acquisition_time_str)
                    self.expiry_time = acquisition_time + timedelta(seconds=int(seconds_until_expiry_on_save))
                else:
                    self.token = None # Invalidate if essential data is missing
                    self.expiry_time = None
        except Exception as e:
            print(f"Error loading token from {self.token_file}: {str(e)}")
            self.token = None
            self.expiry_time = None
    
    def _save_token(self, token_data, seconds_until_expiry_on_save):
        """
        Save token data to file.
        
        Args:
            token_data (dict): Token data to save (original response from TT)
            seconds_until_expiry_on_save (int): The value of 'seconds_until_expiry' at the time of saving.
        """
        try:
            # Create a dictionary to save, ensuring we don't modify the original token_data if not needed
            data_to_save = token_data.copy() # Start with a copy of the original token response
            data_to_save['acquisition_time'] = datetime.now().isoformat()
            # Store the original 'seconds_until_expiry' value at the time of acquisition
            data_to_save['seconds_until_expiry_on_save'] = seconds_until_expiry_on_save
            
            # Ensure directory exists (though for __file__ dir, it should)
            token_dir = os.path.dirname(self.token_file)
            if token_dir and not os.path.exists(token_dir):
                os.makedirs(token_dir) # Should not be necessary if token_file is in same dir as .py
                
            # Save the token data
            with open(self.token_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            print(f"Token saved to {self.token_file}")
        except Exception as e:
            print(f"Error saving token to {self.token_file}: {str(e)}")
    
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
    from TTRestAPI import tt_config # Now safe due to __main__ guard
    
    print(f"Testing Token Manager with ENVIRONMENT = '{tt_config.ENVIRONMENT}'")
    
    token_manager = TTTokenManager(
        # api_key, api_secret, app_name, company_name are now loaded from tt_config by default
        environment=tt_config.ENVIRONMENT, # Pass the environment from config
        token_file_base=tt_config.TOKEN_FILE, # Pass the base name from config
        config_module=tt_config # Pass the config module itself
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