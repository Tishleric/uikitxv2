"""
Configuration file for Trading Technologies API tokens and settings.
"""

# API credentials
TT_API_KEY = "0549df41-77a8-6799-1a7d-b2f4656a7fd4"
TT_API_SECRET = "12d0bbbb-9f1b-caff-e9d3-19212d8426c2"

# Application identifiers
APP_NAME = "UIKitXTT"  # Used in request IDs
COMPANY_NAME = "Fibonacci Research"  # Used in request IDs

# Environment settings
# Use 'UAT' for testing/development, 'LIVE' for production
ENVIRONMENT = "UAT"

# Token settings
TOKEN_FILE = "tt_token.json"  # Just the filename; path is resolved in token_manager.py
AUTO_REFRESH = True  # Automatically refresh tokens before expiry
REFRESH_BUFFER_SECONDS = 600  # Refresh token 10 minutes before expiry 