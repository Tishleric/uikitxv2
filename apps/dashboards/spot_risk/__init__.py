"""Spot Risk Analysis Dashboard Module

This module provides a dashboard for analyzing bond futures option spot risk 
with comprehensive Greek calculations.
"""

from .views import create_spot_risk_content
from .callbacks import register_callbacks

__all__ = ["create_spot_risk_content", "register_callbacks"] 