"""Resource handlers for Proxmox MCP Server."""

from .base import BaseResource
from .vm import VMResource
from .container import ContainerResource
from .storage import StorageResource
from .network import NetworkResource
from .cluster import ClusterResource
from .system import SystemResource
from .users import UsersResource

__all__ = [
    "BaseResource",
    "VMResource", 
    "ContainerResource",
    "StorageResource",
    "NetworkResource",
    "ClusterResource",
    "SystemResource",
    "UsersResource"
]
