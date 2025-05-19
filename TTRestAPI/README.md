# TTRestAPI Package

This package provides integration with the Trading Technologies REST API, focusing on proper authentication and token management.

## Components

### `token_manager.py`

The main token manager class that handles token acquisition, storage, and automatic refreshing.

```python
from TTRestAPI import TTTokenManager

token_manager = TTTokenManager(
    api_key="your_api_key",
    api_secret="your_api_secret",
    app_name="YourAppName",
    company_name="YourCompanyName",
    environment="UAT"  # or "LIVE" for production
)

# Get a valid token (refreshes automatically if needed)
token = token_manager.get_token()

# Get authorization header for API requests
auth_header = token_manager.get_auth_header()

# Get request parameters (including requestId)
params = token_manager.get_request_params()
```

### `tt_config.py`

Configuration settings for the TT REST API. Update this file with your API credentials.

```python
# API credentials
TT_API_KEY = "your_api_key_here"
TT_API_SECRET = "your_api_secret_here"

# Application identifiers
APP_NAME = "YourAppName"  # Used in request IDs
COMPANY_NAME = "YourCompanyName"  # Used in request IDs

# Environment settings
ENVIRONMENT = "UAT"  # or "LIVE" for production
```

### `tt_utils.py`

Utility functions for working with the TT REST API.

```python
from TTRestAPI.tt_utils import (
    generate_guid,
    create_request_id,
    format_bearer_token
)

# Format a token for the Authorization header
auth_header_value = format_bearer_token("my_token")
```

Unit tests in `tests/ttapi/test_tt_utils.py` verify GUID generation, request ID formatting, and sanitize logic.

### `api_example.py`

A comprehensive example of how to use the package to make API requests to different TT REST API services.

### `get_token_cli.py`

Command-line interface for token management, providing tools to get, verify, and refresh tokens.

## API Documentation

For more information about the TT REST API, refer to the official documentation:
[TT REST API Documentation](https://library.tradingtechnologies.com/tt-rest/v2/gs-intro.html)

## Key Authentication Details

- Request IDs must follow the format: `{app_name}-{company_name}--{guid}`
- Token requests use: `grant_type=user_app&app_key={key}:{secret}`
- Service names in URLs must be lowercase
- The Authorization header format is: `Authorization: Bearer {token}` 