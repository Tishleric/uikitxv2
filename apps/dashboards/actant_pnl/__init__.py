"""Actant PnL Dashboard Module

This module provides a dashboard for analyzing option P&L using Taylor Series approximations.
"""

from .pnl_dashboard import PnLDashboard, create_dashboard_content, register_callbacks, get_shared_dashboard

__all__ = ['PnLDashboard', 'create_dashboard_content', 'register_callbacks', 'get_shared_dashboard'] 