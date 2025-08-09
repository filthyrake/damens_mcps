"""Main MCP server implementation for Proxmox VE integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from .proxmox_client import ProxmoxClient
from .auth import AuthManager
from .utils.logging import get_logger

logger = get_logger(__name__)


class ProxmoxMCPServer:
    """Main MCP server for Proxmox VE integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Proxmox MCP server.
        
        Args:
            config: Configuration dictionary containing Proxmox connection details
        """
        self.config = config
        self.auth_manager = AuthManager(config)
        self.proxmox_client = ProxmoxClient(config)
        
        # Create MCP server
        self.server = Server("proxmox-mcp")
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register all available tools with the MCP server."""
        
        # Core MCP tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
        
        # Register all tool handlers
        self._register_vm_tools()
        self._register_container_tools()
        self._register_storage_tools()
        self._register_network_tools()
        self._register_cluster_tools()
        self._register_system_tools()
    
    def _register_vm_tools(self) -> None:
        """Register virtual machine related tools."""
        
        # VM List
        self.server.tool("proxmox_vm_list")(
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
        self.server.tool("proxmox_vm_get_info")(
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
        self.server.tool("proxmox_vm_create")(
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
        self.server.tool("proxmox_vm_start")(
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
        self.server.tool("proxmox_vm_stop")(
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
        self.server.tool("proxmox_vm_shutdown")(
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
        self.server.tool("proxmox_vm_delete")(
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
    
    def _register_container_tools(self) -> None:
        """Register container related tools."""
        
        # Container List
        self.server.tool("proxmox_ct_list")(
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
        self.server.tool("proxmox_ct_get_info")(
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
        self.server.tool("proxmox_ct_create")(
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
    
    def _register_storage_tools(self) -> None:
        """Register storage related tools."""
        
        # Storage List
        self.server.tool("proxmox_storage_list")(
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
    
    def _register_network_tools(self) -> None:
        """Register network related tools."""
        
        # Network List (placeholder for future implementation)
        self.server.tool("proxmox_network_list")(
            description="List network interfaces (placeholder)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._list_networks)
    
    def _register_cluster_tools(self) -> None:
        """Register cluster related tools."""
        
        # Cluster Status
        self.server.tool("proxmox_cluster_status")(
            description="Get cluster status information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._get_cluster_status)
        
        # Cluster Nodes
        self.server.tool("proxmox_cluster_nodes")(
            description="List all nodes in the cluster",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._list_nodes)
        
        # Node Info
        self.server.tool("proxmox_cluster_get_node_info")(
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
    
    def _register_system_tools(self) -> None:
        """Register system related tools."""
        
        # System Version
        self.server.tool("proxmox_system_version")(
            description="Get Proxmox version information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._get_version)
        
        # Test Connection
        self.server.tool("proxmox_test_connection")(
            description="Test connection to Proxmox server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )(self._test_connection)
    
    async def _list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List all available tools."""
        tools = []
        
        # Add all registered tools
        for tool_name, tool_info in self.server._tools.items():
            tools.append(Tool(
                name=tool_name,
                description=tool_info["description"],
                inputSchema=tool_info["inputSchema"]
            ))
        
        return ListToolsResult(tools=tools)
    
    async def _call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Call a specific tool."""
        tool_name = request.name
        arguments = request.arguments or {}
        
        logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
        
        try:
            # Route to appropriate tool handler
            if tool_name == "proxmox_vm_list":
                result = await self._list_vms(arguments)
            elif tool_name == "proxmox_vm_get_info":
                result = await self._get_vm_info(arguments)
            elif tool_name == "proxmox_vm_create":
                result = await self._create_vm(arguments)
            elif tool_name == "proxmox_vm_start":
                result = await self._start_vm(arguments)
            elif tool_name == "proxmox_vm_stop":
                result = await self._stop_vm(arguments)
            elif tool_name == "proxmox_vm_shutdown":
                result = await self._shutdown_vm(arguments)
            elif tool_name == "proxmox_vm_delete":
                result = await self._delete_vm(arguments)
            elif tool_name == "proxmox_ct_list":
                result = await self._list_containers(arguments)
            elif tool_name == "proxmox_ct_get_info":
                result = await self._get_container_info(arguments)
            elif tool_name == "proxmox_ct_create":
                result = await self._create_container(arguments)
            elif tool_name == "proxmox_storage_list":
                result = await self._list_storage(arguments)
            elif tool_name == "proxmox_network_list":
                result = await self._list_networks(arguments)
            elif tool_name == "proxmox_cluster_status":
                result = await self._get_cluster_status(arguments)
            elif tool_name == "proxmox_cluster_nodes":
                result = await self._list_nodes(arguments)
            elif tool_name == "proxmox_cluster_get_node_info":
                result = await self._get_node_info(arguments)
            elif tool_name == "proxmox_system_version":
                result = await self._get_version(arguments)
            elif tool_name == "proxmox_test_connection":
                result = await self._test_connection(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    # Tool implementations
    
    async def _list_vms(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List virtual machines."""
        node = args.get("node")
        vms = await self.proxmox_client.list_vms(node)
        return {"vms": vms, "count": len(vms)}
    
    async def _get_vm_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get VM information."""
        node = args["node"]
        vmid = args["vmid"]
        return await self.proxmox_client.get_vm_info(node, vmid)
    
    async def _create_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VM."""
        return await self.proxmox_client.create_vm(args)
    
    async def _start_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start a VM."""
        node = args["node"]
        vmid = args["vmid"]
        return await self.proxmox_client.start_vm(node, vmid)
    
    async def _stop_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a VM."""
        node = args["node"]
        vmid = args["vmid"]
        return await self.proxmox_client.stop_vm(node, vmid)
    
    async def _shutdown_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown a VM."""
        node = args["node"]
        vmid = args["vmid"]
        return await self.proxmox_client.shutdown_vm(node, vmid)
    
    async def _delete_vm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a VM."""
        node = args["node"]
        vmid = args["vmid"]
        return await self.proxmox_client.delete_vm(node, vmid)
    
    async def _list_containers(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List containers."""
        node = args.get("node")
        containers = await self.proxmox_client.list_containers(node)
        return {"containers": containers, "count": len(containers)}
    
    async def _get_container_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get container information."""
        node = args["node"]
        vmid = args["vmid"]
        return await self.proxmox_client.get_container_info(node, vmid)
    
    async def _create_container(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a container."""
        return await self.proxmox_client.create_container(args)
    
    async def _list_storage(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List storage."""
        node = args.get("node")
        storage = await self.proxmox_client.list_storage(node)
        return {"storage": storage, "count": len(storage)}
    
    async def _list_networks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List networks (placeholder)."""
        return {"message": "Network listing not yet implemented", "networks": []}
    
    async def _get_cluster_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster status."""
        return await self.proxmox_client.get_cluster_status()
    
    async def _list_nodes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List nodes."""
        nodes = await self.proxmox_client.list_nodes()
        return {"nodes": nodes, "count": len(nodes)}
    
    async def _get_node_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get node information."""
        node = args["node"]
        return await self.proxmox_client.get_node_info(node)
    
    async def _get_version(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get version."""
        return await self.proxmox_client.get_version()
    
    async def _test_connection(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection."""
        return await self.proxmox_client.test_connection()
    
    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Proxmox MCP server")
        
        # Test connection to Proxmox
        try:
            connection_test = await self.proxmox_client.test_connection()
            if connection_test["status"] == "success":
                logger.info("Proxmox connection successful")
            else:
                logger.error(f"Proxmox connection failed: {connection_test['error']}")
        except Exception as e:
            logger.error(f"Failed to test Proxmox connection: {e}")
        
        # Start the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="proxmox-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


async def main() -> None:
    """Main entry point."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    from .utils.logging import setup_logging
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format_type=os.getenv("LOG_FORMAT", "json")
    )
    
    # Configuration
    config = {
        "host": os.getenv("PROXMOX_HOST"),
        "port": int(os.getenv("PROXMOX_PORT", "8006")),
        "protocol": os.getenv("PROXMOX_PROTOCOL", "https"),
        "username": os.getenv("PROXMOX_USERNAME"),
        "password": os.getenv("PROXMOX_PASSWORD"),
        "api_token": os.getenv("PROXMOX_API_TOKEN"),
        "realm": os.getenv("PROXMOX_REALM", "pve"),
        "verify_ssl": os.getenv("PROXMOX_SSL_VERIFY", "true").lower() == "true",
        "secret_key": os.getenv("SECRET_KEY"),
    }
    
    # Validate required configuration
    if not config["host"]:
        raise ValueError("PROXMOX_HOST environment variable is required")
    
    if not config["api_token"] and (not config["username"] or not config["password"]):
        raise ValueError("Either PROXMOX_API_TOKEN or PROXMOX_USERNAME/PROXMOX_PASSWORD is required")
    
    if not config["secret_key"]:
        raise ValueError("SECRET_KEY environment variable is required")
    
    # Create and run server
    server = ProxmoxMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
