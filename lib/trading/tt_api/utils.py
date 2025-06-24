"""
Utilities for working with the Trading Technologies REST API.
"""

import uuid
import re

from monitoring.decorators import monitor

def generate_guid():
    """
    Generate a new GUID/UUID for use in request IDs.
    
    Returns:
        str: A new UUID string
    """
    return str(uuid.uuid4())

@monitor()
def create_request_id(app_name, company_name):
    """
    Create a request ID in the format required by the TT REST API.
    
    Args:
        app_name (str): The application name
        company_name (str): The company name
    
    Returns:
        str: A properly formatted request ID
    """
    # Sanitize inputs to avoid special characters and spaces
    app_name_clean = sanitize_request_id_part(app_name)
    company_name_clean = sanitize_request_id_part(company_name)
    
    guid = generate_guid()
    return f"{app_name_clean}-{company_name_clean}--{guid}"

def sanitize_request_id_part(text):
    """
    Sanitize a part of the request ID to ensure it meets the requirements:
    - No special characters ($&+,/:;=?@"<>#%{}|\\^~[]`)
    - No spaces
    
    Args:
        text (str): The text to sanitize
    
    Returns:
        str: The sanitized text
    """
    # Replace spaces with underscores
    text = text.replace(" ", "_")
    
    # Remove special characters
    text = re.sub(r'[$&+,/:;=?@"<>#%{}|\^~[\]`]', '', text)
    
    return text

def format_bearer_token(token):
    """
    Format the raw token into the bearer format required for the Authorization header.
    
    Args:
        token (str): The raw token
    
    Returns:
        str: The formatted bearer token
    """
    return f"Bearer {token}"

def is_valid_guid(guid_str):
    """
    Check if a string is a valid GUID/UUID.
    
    Args:
        guid_str (str): The string to check
    
    Returns:
        bool: True if the string is a valid GUID, False otherwise
    """
    try:
        uuid_obj = uuid.UUID(guid_str)
        return str(uuid_obj) == guid_str
    except (ValueError, AttributeError, TypeError):
        return False 