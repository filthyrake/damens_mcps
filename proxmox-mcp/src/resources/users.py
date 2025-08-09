"""Users resource handler for Proxmox MCP Server."""

from typing import Any, Dict

from mcp.server import Server

from .base import BaseResource
from ..utils.logging import get_logger

logger = get_logger(__name__)


class UsersResource(BaseResource):
    """Users resource handler."""
    
    def register_tools(self, server: Server) -> None:
        """Register user tools with the MCP server."""
        
        # Placeholder for future user management tools
        server.tool("proxmox_users_list")(
            description="List all users (placeholder)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._list_users)
    
    async def _list_users(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List users (placeholder)."""
        self.log_tool_call("proxmox_users_list", args)
        
        try:
            result = {"message": "User management not yet implemented", "users": []}
            self.log_tool_result("proxmox_users_list", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_users_list", None, str(e))
            raise
