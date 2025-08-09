"""Container resource handler for Proxmox MCP Server."""

from typing import Any, Dict

from mcp.server import Server

from .base import BaseResource
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ContainerResource(BaseResource):
    """Container resource handler."""
    
    def register_tools(self, server: Server) -> None:
        """Register container tools with the MCP server."""
        
        # Container List
        server.tool("proxmox_ct_list")(
            description="List all containers across all nodes or a specific node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Optional node name to filter containers"
                    }
                },
                "required": []
            }
        )(self._list_containers)
        
        # Container Get Info
        server.tool("proxmox_ct_get_info")(
            description="Get detailed information about a specific container",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name where the container is located"
                    },
                    "vmid": {
                        "type": "integer",
                        "description": "Container ID"
                    }
                },
                "required": ["node", "vmid"]
            }
        )(self._get_container_info)
        
        # Container Create
        server.tool("proxmox_ct_create")(
            description="Create a new container",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Container name"
                    },
                    "node": {
                        "type": "string",
                        "description": "Node name where to create the container"
                    },
                    "ostemplate": {
                        "type": "string",
                        "description": "OS template (e.g., local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz)"
                    },
                    "cores": {
                        "type": "integer",
                        "description": "Number of CPU cores",
                        "default": 1
                    },
                    "memory": {
                        "type": "integer",
                        "description": "Memory in MB",
                        "default": 512
                    },
                    "storage": {
                        "type": "string",
                        "description": "Storage pool name",
                        "default": "local-lvm"
                    },
                    "disk_size": {
                        "type": "string",
                        "description": "Disk size (e.g., 10G, 100M)",
                        "default": "10G"
                    },
                    "password": {
                        "type": "string",
                        "description": "Root password for the container"
                    },
                    "ssh_keys": {
                        "type": "string",
                        "description": "SSH public keys to install"
                    }
                },
                "required": ["name", "node", "ostemplate"]
            }
        )(self._create_container)
    
    async def _list_containers(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List containers."""
        self.log_tool_call("proxmox_ct_list", args)
        
        try:
            node = args.get("node")
            containers = await self.client.list_containers(node)
            result = {"containers": containers, "count": len(containers)}
            self.log_tool_result("proxmox_ct_list", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_ct_list", None, str(e))
            raise
    
    async def _get_container_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get container information."""
        self.log_tool_call("proxmox_ct_get_info", args)
        
        try:
            node = args["node"]
            vmid = args["vmid"]
            result = await self.client.get_container_info(node, vmid)
            self.log_tool_result("proxmox_ct_get_info", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_ct_get_info", None, str(e))
            raise
    
    async def _create_container(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a container."""
        self.log_tool_call("proxmox_ct_create", args)
        
        try:
            result = await self.client.create_container(args)
            self.log_tool_result("proxmox_ct_create", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_ct_create", None, str(e))
            raise
