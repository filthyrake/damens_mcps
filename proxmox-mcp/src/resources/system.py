"""System resource handler for Proxmox MCP Server."""

from typing import Any, Dict

from mcp.server import Server

from .base import BaseResource
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SystemResource(BaseResource):
    """System resource handler."""
    
    def register_tools(self, server: Server) -> None:
        """Register system tools with the MCP server."""
        
        # System Version
        server.tool("proxmox_system_version")(
            description="Get Proxmox version information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._get_version)
        
        # Test Connection
        server.tool("proxmox_test_connection")(
            description="Test connection to Proxmox server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._test_connection)
    
    async def _get_version(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get version."""
        self.log_tool_call("proxmox_system_version", args)
        
        try:
            result = await self.client.get_version()
            self.log_tool_result("proxmox_system_version", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_system_version", None, str(e))
            raise
    
    async def _test_connection(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection."""
        self.log_tool_call("proxmox_test_connection", args)
        
        try:
            result = await self.client.test_connection()
            self.log_tool_result("proxmox_test_connection", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_test_connection", None, str(e))
            raise
