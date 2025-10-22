"""Proxmox MCP Server - Model Context Protocol server for Proxmox VE management."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .proxmox_client import ProxmoxClient
from .auth import AuthManager

__all__ = ["ProxmoxClient", "AuthManager"]
