"""
Configuration file for Trading Technologies API tokens and settings.
"""

# API credentials
TT_API_KEY = "0549df41-77a8-6799-1a7d-b2f4656a7fd4"  # UAT Key
TT_API_SECRET = "12d0bbbb-9f1b-caff-e9d3-19212d8426c2"  # UAT Secret

# SIM Environment credentials
TT_SIM_API_KEY = "2b429b91-8d96-8aed-4338-3d3d5b73887a"
TT_SIM_API_SECRET = "8d9f572e-292e-c7a0-c39d-383fbfb56b8b"

# Application identifiers
APP_NAME = "UIKitXTT"  # Used in request IDs
COMPANY_NAME = "Fibonacci Research"  # Used in request IDs

# Environment settings
# Use 'UAT' for testing/development, 'LIVE' for production, 'SIM' for simulation
ENVIRONMENT = "SIM"

# Token settings
TOKEN_FILE = "tt_token.json"  # Base filename; path and suffix (_uat, _sim) are resolved in token_manager.py
AUTO_REFRESH = True  # Automatically refresh tokens before expiry
REFRESH_BUFFER_SECONDS = 600  # Refresh token 10 minutes before expiry 