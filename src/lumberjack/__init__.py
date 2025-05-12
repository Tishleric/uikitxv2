"""
Logging framework for UIKitXv2.

This module provides a unified logging system with SQLite storage capabilities,
allowing performance metrics and execution details to be logged and analyzed.
"""

from . import sqlite_handler
from . import logging_config

# Make main components directly importable
from .sqlite_handler import SQLiteHandler
from .logging_config import setup_logging, shutdown_logging 