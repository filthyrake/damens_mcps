"""Resource handlers for iDRAC MCP Server."""

from .base import BaseResource
from .system import SystemResource
from .power import PowerResource
from .users import UsersResource
from .network import NetworkResource
from .storage import StorageResource
from .firmware import FirmwareResource
from .virtual_media import VirtualMediaResource

__all__ = [
    "BaseResource",
    "SystemResource", 
    "PowerResource",
    "UsersResource",
    "NetworkResource",
    "StorageResource",
    "FirmwareResource",
    "VirtualMediaResource"
]
