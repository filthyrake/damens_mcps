"""Cluster resource handler for Proxmox MCP Server."""

from typing import Any, Dict

from mcp.server import Server

from .base import BaseResource
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ClusterResource(BaseResource):
    """Cluster resource handler."""
    
    def register_tools(self, server: Server) -> None:
        """Register cluster tools with the MCP server."""
        
        # Cluster Status
        server.tool("proxmox_cluster_status")(
            description="Get cluster status information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._get_cluster_status)
        
        # Cluster Nodes
        server.tool("proxmox_cluster_nodes")(
            description="List all nodes in the cluster",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._list_nodes)
        
        # Node Info
        server.tool("proxmox_cluster_get_node_info")(
            description="Get detailed information about a specific node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name"
                    }
                },
                "required": ["node"]
            }
        )(self._get_node_info)
    
    async def _get_cluster_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster status."""
        self.log_tool_call("proxmox_cluster_status", args)
        
        try:
            result = await self.client.get_cluster_status()
            self.log_tool_result("proxmox_cluster_status", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_cluster_status", None, str(e))
            raise
    
    async def _list_nodes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List nodes."""
        self.log_tool_call("proxmox_cluster_nodes", args)
        
        try:
            nodes = await self.client.list_nodes()
            result = {"nodes": nodes, "count": len(nodes)}
            self.log_tool_result("proxmox_cluster_nodes", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_cluster_nodes", None, str(e))
            raise
    
    async def _get_node_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get node information."""
        self.log_tool_call("proxmox_cluster_get_node_info", args)
        
        try:
            node = args["node"]
            result = await self.client.get_node_info(node)
            self.log_tool_result("proxmox_cluster_get_node_info", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_cluster_get_node_info", None, str(e))
            raise
