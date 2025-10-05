"""
Configuration file for Trading Technologies API tokens and settings.
"""

# API credentials
TT_LIVE_API_KEY = "c57b0353-72de-95c4-feba-743ede8c6750"  # UAT Key
TT_LIVE_API_SECRET = "cdd2d2f0-997e-67cc-654d-689b933fa439"  # UAT Secret

TT_API_KEY = "c57b0353-72de-95c4-feba-743ede8c6750"  # UAT Key
TT_API_SECRET = "cdd2d2f0-997e-67cc-654d-689b933fa439"  # UAT Secret

# SIM Environment credentials
TT_SIM_API_KEY = ""
TT_SIM_API_SECRET = ""

# Application identifiers
APP_NAME = "DAS"  # Used in request IDs
COMPANY_NAME = "Sumo Capital LLC"  # Used in request IDs

# Environment settings
# Use 'UAT' for testing/development, 'LIVE' for production, 'SIM' for simulation
ENVIRONMENT = "LIVE"

# Token settings
TOKEN_FILE = "tt_token.json"  # Base filename; path and suffix (_uat, _sim) are resolved in token_manager.py
AUTO_REFRESH = True  # Automatically refresh tokens before expiry
REFRESH_BUFFER_SECONDS = 600  # Refresh token 10 minutes before expiry 