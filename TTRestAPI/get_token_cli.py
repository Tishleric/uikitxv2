#!/usr/bin/env python
"""
Command-line tool for getting and refreshing tokens for the Trading Technologies REST API.
"""

import argparse
import json
import sys
import time
from datetime import datetime

from .token_manager import TTTokenManager
from . import tt_config

def main():
    """
    Command-line entry point for getting and refreshing tokens.
    """
    parser = argparse.ArgumentParser(description="Get or refresh tokens for the TT REST API")
    parser.add_argument("--force-refresh", action="store_true", help="Force a token refresh even if current token is valid")
    parser.add_argument("--verify", action="store_true", help="Verify the token validity without refreshing")
    parser.add_argument("--show", action="store_true", help="Show the token value (security risk)")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()
    
    # Check if credentials are set
    if tt_config.TT_API_KEY == "your_api_key_here" or tt_config.TT_API_SECRET == "your_api_secret_here":
        print("ERROR: API credentials are not set in tt_config.py")
        print("Please update the API credentials before running this tool.")
        sys.exit(1)
    
    # Create token manager
    token_manager = TTTokenManager(
        api_key=tt_config.TT_API_KEY,
        api_secret=tt_config.TT_API_SECRET,
        app_name=tt_config.APP_NAME,
        company_name=tt_config.COMPANY_NAME,
        environment=tt_config.ENVIRONMENT,
        token_file=tt_config.TOKEN_FILE,
        auto_refresh=False  # Don't auto-refresh, we'll handle it explicitly
    )
    
    # Perform the requested action
    if args.verify:
        verify_token(token_manager, args.output)
    elif args.force_refresh:
        refresh_token(token_manager, args.output, args.show)
    else:
        get_token(token_manager, args.output, args.show)

def verify_token(token_manager, output_format):
    """
    Verify the validity of the current token.
    
    Args:
        token_manager: The token manager instance
        output_format: The output format (text or json)
    """
    is_valid = token_manager._is_token_valid()
    
    if output_format == "json":
        result = {
            "valid": is_valid,
            "token_exists": token_manager.token is not None,
        }
        
        if is_valid:
            expiry_datetime = datetime.fromtimestamp(token_manager.expiry_time)
            seconds_remaining = int(token_manager.expiry_time - time.time())
            
            result.update({
                "expiry_time": expiry_datetime.isoformat(),
                "seconds_until_expiry": seconds_remaining
            })
            
        print(json.dumps(result, indent=2))
    else:
        if is_valid:
            expiry_datetime = datetime.fromtimestamp(token_manager.expiry_time)
            seconds_remaining = int(token_manager.expiry_time - time.time())
            
            print(f"Token is valid")
            print(f"Expires at: {expiry_datetime}")
            print(f"Time remaining: {seconds_remaining} seconds")
        else:
            if token_manager.token is None:
                print("No token available")
            else:
                print("Token has expired")

def get_token(token_manager, output_format, show_token):
    """
    Get a token, refreshing if necessary.
    
    Args:
        token_manager: The token manager instance
        output_format: The output format (text or json)
        show_token: Whether to show the token value
    """
    try:
        # Try to get a token
        token = token_manager.get_token()
        
        if output_format == "json":
            result = {
                "success": True,
                "expiry_time": datetime.fromtimestamp(token_manager.expiry_time).isoformat(),
                "seconds_until_expiry": int(token_manager.expiry_time - time.time())
            }
            
            if show_token:
                result["token"] = token
                
            print(json.dumps(result, indent=2))
        else:
            print("Token acquired successfully")
            
            if show_token:
                print(f"Token: {token}")
                
            expiry_datetime = datetime.fromtimestamp(token_manager.expiry_time)
            seconds_remaining = int(token_manager.expiry_time - time.time())
            
            print(f"Expires at: {expiry_datetime}")
            print(f"Time remaining: {seconds_remaining} seconds")
            
    except Exception as e:
        if output_format == "json":
            print(json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2))
        else:
            print(f"Error getting token: {str(e)}")
        
        sys.exit(1)

def refresh_token(token_manager, output_format, show_token):
    """
    Force a token refresh.
    
    Args:
        token_manager: The token manager instance
        output_format: The output format (text or json)
        show_token: Whether to show the token value
    """
    try:
        # Force a token refresh
        token_manager._acquire_new_token()
        token = token_manager.token
        
        if output_format == "json":
            result = {
                "success": True,
                "expiry_time": datetime.fromtimestamp(token_manager.expiry_time).isoformat(),
                "seconds_until_expiry": int(token_manager.expiry_time - time.time())
            }
            
            if show_token:
                result["token"] = token
                
            print(json.dumps(result, indent=2))
        else:
            print("Token refreshed successfully")
            
            if show_token:
                print(f"Token: {token}")
                
            expiry_datetime = datetime.fromtimestamp(token_manager.expiry_time)
            seconds_remaining = int(token_manager.expiry_time - time.time())
            
            print(f"Expires at: {expiry_datetime}")
            print(f"Time remaining: {seconds_remaining} seconds")
            
    except Exception as e:
        if output_format == "json":
            print(json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2))
        else:
            print(f"Error refreshing token: {str(e)}")
        
        sys.exit(1)

if __name__ == "__main__":
    main() 