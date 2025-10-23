"""iDRAC MCP Server - Dell PowerEdge server management via iDRAC."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .idrac_client import IDracClient
from .auth import AuthManager

__all__ = ["IDracClient", "AuthManager"]
