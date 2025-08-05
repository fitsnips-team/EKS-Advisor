"""
EKS Advisor Views
Presentation layer for the MVC architecture
"""

from .console_view import ConsoleView
from .dashboard_view import DashboardView
from .web_view import WebView

__all__ = [
    'ConsoleView',
    'DashboardView',
    'WebView'
]