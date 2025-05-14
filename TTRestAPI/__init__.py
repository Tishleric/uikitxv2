"""
Trading Technologies REST API Token Manager package.

This package provides tools for managing authentication tokens for the 
Trading Technologies REST API, including acquisition, refreshing, and storage.
"""

from .token_manager import TTTokenManager
from .tt_utils import (
    generate_guid, 
    create_request_id, 
    sanitize_request_id_part, 
    format_bearer_token, 
    is_valid_guid
)

__version__ = "0.1.0" 