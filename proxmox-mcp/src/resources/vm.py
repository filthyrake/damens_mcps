"""Virtual Machine resource handler for Proxmox MCP Server."""

from typing import Any, Dict

from mcp.server import Server

from .base import BaseResource
from ..utils.logging import get_logger

logger = get_logger(__name__)


class VMResource(BaseResource):
    """Virtual Machine resource handler."""
    
    def register_tools(self, server: Server) -> None:
        """Register VM tools with the MCP server."""
        
        # VM List
        server.tool("proxmox_vm_list")(
            description="List all virtual machines across all nodes or a specific node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Optional node name to filter VMs"
                    }
                },
                "required": []
            }
        )(self._list_vms)
        
        # VM Get Info
        server.tool("proxmox_vm_get_info")(
            description="Get detailed information about a specific virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name where the VM is located"
                    },
                    "vmid": {
                        "type": "integer",
                        "description": "VM ID"
                    }
                },
                "required": ["node", "vmid"]
            }
        )(self._get_vm_info)
        
        # VM Create
        server.tool("proxmox_vm_create")(
            description="Create a new virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "VM name"
                    },
                    "node": {
                        "type": "string",
                        "description": "Node name where to create the VM"
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
                    "bridge": {
                        "type": "string",
                        "description": "Network bridge",
                        "default": "vmbr0"
                    }
                },
                "required": ["name", "node"]
            }
        )(self._create_vm)
        
        # VM Start
        server.tool("proxmox_vm_start")(
            description="Start a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name where the VM is located"
                    },
                    "vmid": {
                        "type": "integer",
                        "description": "VM ID"
                    }
                },
                "required": ["node", "vmid"]
            }
        )(self._start_vm)
        
        # VM Stop
        server.tool("proxmox_vm_stop")(
            description="Stop a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name where the VM is located"
                    },
                    "vmid": {
                        "type": "integer",
                        "description": "VM ID"
                    }
                },
                "required": ["node", "vmid"]
            }
        )(self._stop_vm)
        
        # VM Shutdown
        server.tool("proxmox_vm_shutdown")(
            description="Shutdown a virtual machine gracefully",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name where the VM is located"
                    },
                    "vmid": {
                        "type": "integer",
                        "description": "VM ID"
                    }
                },
                "required": ["node", "vmid"]
            }
        )(self._shutdown_vm)
        
        # VM Delete
        server.tool("proxmox_vm_delete")(
            description="Delete a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node name where the VM is located"
                    },
                    "vmid": {
                        "type": "integer",
                        "description": "VM ID"
                    }
                },
                "required": ["node", "vmid"]
            }
        )(self._delete_vm)
    
    async def _list_vms(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List virtual machines."""
        self.log_tool_call("proxmox_vm_list", args)
        
        try:
            node = args.get("node")
            vms = await self.client.list_vms(node)
            result = {"vms": vms, "count": len(vms)}
            self.log_tool_result("proxmox_vm_list", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_list", None, str(e))
            raise
    
    async def _get_vm_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get VM information."""
        self.log_tool_call("proxmox_vm_get_info", args)
        
        try:
            node = args["node"]
            vmid = args["vmid"]
            result = await self.client.get_vm_info(node, vmid)
            self.log_tool_result("proxmox_vm_get_info", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_get_info", None, str(e))
            raise
    
    async def _create_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VM."""
        self.log_tool_call("proxmox_vm_create", args)
        
        try:
            result = await self.client.create_vm(args)
            self.log_tool_result("proxmox_vm_create", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_create", None, str(e))
            raise
    
    async def _start_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start a VM."""
        self.log_tool_call("proxmox_vm_start", args)
        
        try:
            node = args["node"]
            vmid = args["vmid"]
            result = await self.client.start_vm(node, vmid)
            self.log_tool_result("proxmox_vm_start", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_start", None, str(e))
            raise
    
    async def _stop_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a VM."""
        self.log_tool_call("proxmox_vm_stop", args)
        
        try:
            node = args["node"]
            vmid = args["vmid"]
            result = await self.client.stop_vm(node, vmid)
            self.log_tool_result("proxmox_vm_stop", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_stop", None, str(e))
            raise
    
    async def _shutdown_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown a VM."""
        self.log_tool_call("proxmox_vm_shutdown", args)
        
        try:
            node = args["node"]
            vmid = args["vmid"]
            result = await self.client.shutdown_vm(node, vmid)
            self.log_tool_result("proxmox_vm_shutdown", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_shutdown", None, str(e))
            raise
    
    async def _delete_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a VM."""
        self.log_tool_call("proxmox_vm_delete", args)
        
        try:
            node = args["node"]
            vmid = args["vmid"]
            result = await self.client.delete_vm(node, vmid)
            self.log_tool_result("proxmox_vm_delete", result)
            return result
        except Exception as e:
            self.log_tool_result("proxmox_vm_delete", None, str(e))
            raise
