"""Main MCP server for iDRAC management."""

import asyncio
import os
from typing import Dict, Any, List

from mcp import Server, StdioServerParameters
from mcp.server import Session
from mcp.server.models import InitializationOptions

from .idrac_client import IDracClient
from .auth import AuthManager
from .utils.logging import setup_logging, get_logger
from .resources import (
    SystemResource,
    PowerResource,
    UsersResource,
    NetworkResource,
    StorageResource,
    FirmwareResource,
    VirtualMediaResource
)

logger = get_logger(__name__)


class IDracMCPServer(Server):
    """Main MCP server for iDRAC management."""
    
    def __init__(self):
        """Initialize the iDRAC MCP server."""
        super().__init__(
            StdioServerParameters(
                name="idrac-mcp",
                version="1.0.0"
            )
        )
        
        # Setup logging
        setup_logging(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format_type=os.getenv("LOG_FORMAT", "console")
        )
        
        # Initialize iDRAC client
        self.idrac_config = {
            "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
            "port": int(os.getenv("IDRAC_PORT", "443")),
            "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
            "username": os.getenv("IDRAC_USERNAME", "root"),
            "password": os.getenv("IDRAC_PASSWORD", ""),
            "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
        }
        
        self.idrac_client = IDracClient(self.idrac_config)
        
        # Initialize resource handlers
        self.resources = {
            "system": SystemResource(self.idrac_client),
            "power": PowerResource(self.idrac_client),
            "users": UsersResource(self.idrac_client),
            "network": NetworkResource(self.idrac_client),
            "storage": StorageResource(self.idrac_client),
            "firmware": FirmwareResource(self.idrac_client),
            "virtual_media": VirtualMediaResource(self.idrac_client)
        }
        
        # Register all tools
        self._register_tools()
        
        logger.info("iDRAC MCP Server initialized")
    
    def _register_tools(self):
        """Register all tools from resource handlers."""
        for resource_name, resource in self.resources.items():
            for tool in resource.tools:
                self.register_tool(tool)
                logger.debug(f"Registered tool: {tool.name}")
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to appropriate resource handlers."""
        
        # System tools
        if name == "idrac_system_info":
            return await self.resources["system"].handle_system_info(arguments)
        elif name == "idrac_system_health":
            return await self.resources["system"].handle_system_health(arguments)
        elif name == "idrac_hardware_inventory":
            return await self.resources["system"].handle_hardware_inventory(arguments)
        elif name == "idrac_power_status":
            return await self.resources["system"].handle_power_status(arguments)
        elif name == "idrac_thermal_status":
            return await self.resources["system"].handle_thermal_status(arguments)
        elif name == "idrac_test_connection":
            return await self.resources["system"].handle_test_connection(arguments)
        
        # Power tools
        elif name == "idrac_power_on":
            return await self.resources["power"].handle_power_on(arguments)
        elif name == "idrac_power_off":
            return await self.resources["power"].handle_power_off(arguments)
        elif name == "idrac_power_cycle":
            return await self.resources["power"].handle_power_cycle(arguments)
        elif name == "idrac_graceful_shutdown":
            return await self.resources["power"].handle_graceful_shutdown(arguments)
        
        # User tools
        elif name == "idrac_users_list":
            return await self.resources["users"].handle_users_list(arguments)
        elif name == "idrac_user_create":
            return await self.resources["users"].handle_user_create(arguments)
        
        # Network tools
        elif name == "idrac_network_config":
            return await self.resources["network"].handle_network_config(arguments)
        
        # Storage tools
        elif name == "idrac_storage_controllers":
            return await self.resources["storage"].handle_storage_controllers(arguments)
        
        # Firmware tools
        elif name == "idrac_firmware_versions":
            return await self.resources["firmware"].handle_firmware_versions(arguments)
        
        # Virtual media tools
        elif name == "idrac_virtual_media_list":
            return await self.resources["virtual_media"].handle_virtual_media_list(arguments)
        
        else:
            raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point."""
    server = IDracMCPServer()
    async with server.run_stdio() as stream:
        await stream.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
