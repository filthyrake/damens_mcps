"""TrueNAS MCP Server - Model Context Protocol server for TrueNAS Scale integration."""

__version__ = "0.1.0"
__author__ = "TrueNAS MCP Team"
__email__ = "truenas-mcp@example.com"

from .server import TrueNASMCPServer
from .http_server import create_app, run_server

__all__ = ["TrueNASMCPServer", "create_app", "run_server"]
