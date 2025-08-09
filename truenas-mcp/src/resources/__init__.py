"""Resource handlers for TrueNAS MCP server."""

from .base import BaseResource
from .system import SystemResource
from .storage import StorageResource
from .network import NetworkResource
from .services import ServicesResource
from .users import UsersResource

__all__ = [
    "BaseResource",
    "SystemResource", 
    "StorageResource",
    "NetworkResource",
    "ServicesResource",
    "UsersResource",
]
