# TT REST API Examples

This directory contains example scripts for using the TT REST API.

## Getting Started

### Prerequisites

- Python 3.6+
- Access to TT REST API (API Key and Secret)
- The following Python packages:
  - requests

### Running the Simple Example

The `simple_api_call.py` script demonstrates a single API call to get exchanges from the TT REST API:

1. Ensure your API credentials are properly set in `TTRestAPI/tt_config.py`
2. Run the script:

```bash
python simple_api_call.py
```

This will:
- Initialize the token manager
- Make a GET request to fetch exchanges
- Display the first 3 exchanges
- Save the complete response as `exchanges_response.json`

## Understanding the Code

The simple example demonstrates:

1. **Authentication**: Using the TTTokenManager to handle tokens
2. **Request Formation**: Building URLs, headers, and query parameters correctly
3. **Response Handling**: Processing the JSON response

## Notes

- The URLs are case-sensitive (service names must be lowercase)
- All requests require:
  - API Key in the header (`x-api-key`)
  - Authorization token in the header
  - Request ID as a query parameter

For more detailed examples, see `api_example.py` in the parent directory. 