"""
Greek Value Trace Logger Configuration
"""
import logging
import os
from datetime import datetime

# Create formatters and handlers
def setup_greek_logger():
    logger = logging.getLogger('greek_trace')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - GREEK_TRACE - %(message)s')
    console_handler.setFormatter(console_format)
    
    # File handler
    log_dir = os.path.join("logs", "greek_trace")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"greek_values_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Global greek trace logger
greek_logger = setup_greek_logger()
