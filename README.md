# Trading Technologies REST API Token Manager

A Python package for managing authentication tokens with the Trading Technologies REST API.

## Overview

This package provides a token management system for the Trading Technologies (TT) REST API, handling:

- Token acquisition
- Automatic token refreshing before expiry
- Token storage for persistence between sessions
- Properly formatted request IDs (GUIDs)

## Installation

### Local Installation

1. Clone or download this repository
2. Install the package:
   ```
   pip install -e .
   ```

### Required Dependencies

- Python 3.6+
- Requests library

## Configuration

Update `TTRestAPI/tt_config.py` with your API credentials:

```python
TT_API_KEY = "your_api_key_here"
TT_API_SECRET = "your_api_secret_here"
APP_NAME = "YourAppName"
COMPANY_NAME = "YourCompanyName"
ENVIRONMENT = "UAT"  # or "LIVE" for production
```

## Usage

### As a Python Package

```python
from TTRestAPI import TTTokenManager
from TTRestAPI.tt_utils import format_bearer_token

# Create token manager instance
token_manager = TTTokenManager(
    api_key="your_api_key",
    api_secret="your_api_secret",
    app_name="YourAppName",
    company_name="YourCompanyName"
)

# Get a valid token (will be refreshed automatically if needed)
token = token_manager.get_token()

# Generate a request ID for API calls
request_id = token_manager.generate_request_id()

# Use in API requests
headers = {
    "x-api-key": "your_api_key",
    "Authorization": format_bearer_token(token),
    "Content-Type": "application/json"
}
```

### Using the Example Script

Run the example script to test your configuration:

```
python example_tt_api.py
```

### Command-Line Token Manager

The package includes a command-line tool for token management:

```
# Get or refresh a token
python tt-token

# Force a token refresh
python tt-token --force-refresh

# Verify token validity
python tt-token --verify

# Show the token value (use with caution)
python tt-token --show

# Output in JSON format
python tt-token --output json
```

## Package Structure

- `TTRestAPI/` - Main package directory
  - `__init__.py` - Package initialization
  - `tt_token_manager.py` - Token management class
  - `tt_config.py` - Configuration settings
  - `tt_utils.py` - Utility functions
  - `tt_example.py` - Package usage example
  - `get_token_cli.py` - Command-line interface
- `example_tt_api.py` - Standalone example script
- `tt-token` - Command-line tool entry point
- `setup.py` - Package installation script

## Token Refresh

Tokens expire after a certain time period. The token manager:

1. Tracks token expiration based on the `seconds_until_expiry` value in the API response
2. Automatically refreshes tokens before they expire when `get_token()` is called
3. Maintains a buffer period (default: 10 minutes) to refresh tokens before actual expiry

## Request IDs

Each TT REST API call requires a unique request ID in the format:
`<app_name>-<company_name>--<guid>`

The token manager handles proper formatting and GUID generation for these request IDs.

## Security Notes

- Store your API credentials securely
- The token file (`tt_token.json`) contains sensitive authentication data and should be protected
- For production use, consider implementing more robust credential storage

## Documentation

For more information about the TT REST API, refer to the official documentation:
[TT REST API Documentation](https://library.tradingtechnologies.com/tt-rest/v2/gs-intro.html)
