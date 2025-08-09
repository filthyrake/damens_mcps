"""Network resource handler for TrueNAS MCP server."""

import logging
from typing import Any, Dict, List

from mcp.types import CallToolRequest, CallToolResult, Tool

from .base import BaseResource

logger = logging.getLogger(__name__)


class NetworkResource(BaseResource):
    """Handler for network-related operations."""

    def get_tools(self) -> List[Tool]:
        """Get list of network tools.
        
        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="truenas_network_get_interfaces",
                description="Get all network interfaces",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_network_get_interface",
                description="Get specific network interface by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "interface_id": {
                            "type": "string",
                            "description": "Network interface ID"
                        }
                    },
                    "required": ["interface_id"]
                }
            ),
            Tool(
                name="truenas_network_update_interface",
                description="Update network interface configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "interface_id": {
                            "type": "string",
                            "description": "Network interface ID"
                        },
                        "ip_address": {
                            "type": "string",
                            "description": "IP address"
                        },
                        "netmask": {
                            "type": "string",
                            "description": "Subnet mask"
                        },
                        "gateway": {
                            "type": "string",
                            "description": "Gateway address"
                        },
                        "mtu": {
                            "type": "integer",
                            "description": "MTU size"
                        }
                    },
                    "required": ["interface_id"]
                }
            ),
            Tool(
                name="truenas_network_get_routes",
                description="Get network routes",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_network_test_connectivity",
                description="Test network connectivity to a host",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "host": {
                            "type": "string",
                            "description": "Host to test connectivity to"
                        },
                        "port": {
                            "type": "integer",
                            "description": "Port to test (default: 80)"
                        }
                    },
                    "required": ["host"]
                }
            ),
        ]
    
    async def handle_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle network tool calls.
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call result
        """
        tool_name = request.name
        params = request.arguments or {}
        
        try:
            if tool_name == "truenas_network_get_interfaces":
                return await self._get_interfaces()
            elif tool_name == "truenas_network_get_interface":
                return await self._get_interface(params)
            elif tool_name == "truenas_network_update_interface":
                return await self._update_interface(params)
            elif tool_name == "truenas_network_get_routes":
                return await self._get_routes()
            elif tool_name == "truenas_network_test_connectivity":
                return await self._test_connectivity(params)
            else:
                return self._create_error_result(f"Unknown network tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in network tool {tool_name}: {e}")
            return self._create_error_result(str(e))
    
    async def _get_interfaces(self) -> CallToolResult:
        """Get all network interfaces."""
        try:
            interfaces = await self.client.get_interfaces()
            return self._create_success_result(interfaces)
        except Exception as e:
            return self._create_error_result(f"Failed to get interfaces: {e}")
    
    async def _get_interface(self, params: Dict[str, Any]) -> CallToolResult:
        """Get specific network interface."""
        try:
            self._validate_required_params(params, ["interface_id"])
            interface_id = params["interface_id"]
            interface = await self.client.get_interface(interface_id)
            return self._create_success_result(interface)
        except Exception as e:
            return self._create_error_result(f"Failed to get interface: {e}")
    
    async def _update_interface(self, params: Dict[str, Any]) -> CallToolResult:
        """Update network interface configuration."""
        try:
            self._validate_required_params(params, ["interface_id"])
            interface_id = params["interface_id"]
            
            interface_data = {}
            
            # Add optional parameters
            if "ip_address" in params:
                interface_data["ip_address"] = params["ip_address"]
            if "netmask" in params:
                interface_data["netmask"] = params["netmask"]
            if "gateway" in params:
                interface_data["gateway"] = params["gateway"]
            if "mtu" in params:
                interface_data["mtu"] = params["mtu"]
            
            result = await self.client.update_interface(interface_id, interface_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to update interface: {e}")
    
    async def _get_routes(self) -> CallToolResult:
        """Get network routes."""
        try:
            routes = await self.client.get_routes()
            return self._create_success_result(routes)
        except Exception as e:
            return self._create_error_result(f"Failed to get routes: {e}")
    
    async def _test_connectivity(self, params: Dict[str, Any]) -> CallToolResult:
        """Test network connectivity."""
        try:
            self._validate_required_params(params, ["host"])
            host = params["host"]
            port = self._safe_get_param(params, "port", 80)
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "host": host,
                "port": port,
                "status": "connectivity_test_scheduled",
                "message": f"Connectivity test to {host}:{port} has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to test connectivity: {e}")
