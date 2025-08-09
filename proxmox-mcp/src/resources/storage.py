"""Storage resource handler for Proxmox MCP Server."""

from typing import Any, Dict

from mcp.server import Server

from .base import BaseResource
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StorageResource(BaseResource):
    """Storage resource handler."""
    
    def register_tools(self, server: Server) -> None:
        """Register storage tools with the MCP server."""
        
        # Storage List
        server.tool("proxmox_storage_list")(
            description="List all storage pools across all nodes or a specific node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Optional node name to filter storage"
                    }
                },
                "required": []
            }
        )(self._list_storage)
    
    async def _list_storage(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List storage."""
        self.log_tool_call("proxmox_storage_list", args)
        
        try:
            node = args.get("node")
            storage = await self.client.list_storage(node)
            result = {"storage": storage, "count": len(storage)}
            self.log_tool_result("proxmox_storage_list", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_storage_list", None, str(e))
            raise
