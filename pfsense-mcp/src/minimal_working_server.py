#!/usr/bin/env python3
"""
Minimal Working pfSense MCP Server - Exact TrueNAS pattern.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import the real pfSense client
try:
    from .pfsense_client import HTTPPfSenseClient
    from .auth import PfSenseAuth
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from pfsense_client import HTTPPfSenseClient
    from auth import PfSenseAuth

class RealPfSenseClient:
    """Real pfSense client using the REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 443)
        self.protocol = config.get("protocol", "https")
        self.api_key = config.get("api_key")
        self.username = config.get("username")
        self.password = config.get("password")
        self.verify_ssl = config.get("verify_ssl", True)
        
        # Initialize the real pfSense client
        self.client = HTTPPfSenseClient(config)
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to pfSense."""
        try:
            # First test basic connectivity
            import aiohttp
            import ssl
            
            # Create SSL context that ignores certificate verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                # Test basic connectivity first
                base_url = f"{self.protocol}://{self.host}:{self.port}"
                try:
                    async with session.get(f"{base_url}/", allow_redirects=False) as response:
                        basic_connectivity = {
                            "status": response.status,
                            "content_type": response.headers.get('content-type', 'unknown'),
                            "location": response.headers.get('location', 'none')
                        }
                except Exception as e:
                    basic_connectivity = {"error": str(e)}
            
            # Now test API connection
            result = await self.client.test_connection()
            
            return {
                "status": "connected",
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "message": "pfSense MCP server is working",
                "basic_connectivity": basic_connectivity,
                "api_connection": result
            }
        except Exception as e:
            return {
                "status": "error",
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "message": f"Connection failed: {str(e)}",
                "error_details": str(e)
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            result = await self.client.get_system_info()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get system info: {str(e)}"
            }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        try:
            result = await self.client.get_system_health()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get system health: {str(e)}"
            }
    
    async def get_interfaces(self) -> Dict[str, Any]:
        """Get network interfaces information."""
        try:
            result = await self.client.get_interfaces()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get interfaces: {str(e)}"
            }
    
    async def get_services(self) -> Dict[str, Any]:
        """Get running services information."""
        try:
            result = await self.client.get_services()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get services: {str(e)}"
            }
    
    async def get_firewall_rules(self) -> Dict[str, Any]:
        """Get firewall rules."""
        try:
            result = await self.client.get_firewall_rules()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get firewall rules: {str(e)}"
            }
    
    async def get_firewall_aliases(self) -> Dict[str, Any]:
        """Get firewall aliases."""
        try:
            result = await self.client.get_firewall_aliases()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get firewall aliases: {str(e)}"
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status."""
        try:
            result = await self.client.get_service_status()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get service status: {str(e)}"
            }
    
    async def get_interface_status(self) -> Dict[str, Any]:
        """Get interface status."""
        try:
            result = await self.client.get_interface_status()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get interface status: {str(e)}"
            }
    
    async def get_nat_outbound_mappings(self) -> Dict[str, Any]:
        """Get NAT outbound mappings."""
        try:
            result = await self.client.get_nat_outbound_mappings()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get NAT outbound mappings: {str(e)}"
            }
    
    async def get_nat_port_forwarding(self) -> Dict[str, Any]:
        """Get NAT port forwarding rules."""
        try:
            result = await self.client.get_nat_port_forwarding()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get NAT port forwarding: {str(e)}"
            }
    
    async def get_nat_one_to_one_mappings(self) -> Dict[str, Any]:
        """Get NAT one-to-one mappings."""
        try:
            result = await self.client.get_nat_one_to_one_mappings()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get NAT one-to-one mappings: {str(e)}"
            }
    
    async def get_firewall_schedules(self) -> Dict[str, Any]:
        """Get firewall schedules."""
        try:
            result = await self.client.get_firewall_schedules()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get firewall schedules: {str(e)}"
            }
    
    async def get_firewall_states(self) -> Dict[str, Any]:
        """Get firewall states."""
        try:
            result = await self.client.get_firewall_states()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get firewall states: {str(e)}"
            }
    
    async def get_traffic_shaper(self) -> Dict[str, Any]:
        """Get traffic shaper configuration."""
        try:
            result = await self.client.get_traffic_shaper()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get traffic shaper: {str(e)}"
            }
    
    async def get_traffic_shapers(self) -> Dict[str, Any]:
        """Get all traffic shapers."""
        try:
            result = await self.client.get_traffic_shapers()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get traffic shapers: {str(e)}"
            }
    
    async def get_traffic_shaper_limiters(self) -> Dict[str, Any]:
        """Get traffic shaper limiters."""
        try:
            result = await self.client.get_traffic_shaper_limiters()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get traffic shaper limiters: {str(e)}"
            }
    
    async def get_traffic_shaper_queues(self) -> Dict[str, Any]:
        """Get traffic shaper queues."""
        try:
            result = await self.client.get_traffic_shaper_queues()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get traffic shaper queues: {str(e)}"
            }
    
    async def get_virtual_ips(self) -> Dict[str, Any]:
        """Get virtual IP addresses."""
        try:
            result = await self.client.get_virtual_ips()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get virtual IPs: {str(e)}"
            }
    
    async def get_virtual_ip(self, interface: str = None) -> Dict[str, Any]:
        """Get specific virtual IP configuration."""
        try:
            result = await self.client.get_virtual_ip(interface)
            return result
        except Exception as e:
            return {
                "error": f"Failed to get virtual IP: {str(e)}"
            }
    
    async def apply_virtual_ip_changes(self) -> Dict[str, Any]:
        """Apply virtual IP configuration changes."""
        try:
            result = await self.client.apply_virtual_ip_changes()
            return result
        except Exception as e:
            return {
                "error": f"Failed to apply virtual IP changes: {str(e)}"
            }
    
    async def get_arp_table(self) -> Dict[str, Any]:
        """Get ARP table entries."""
        try:
            result = await self.client.get_arp_table()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get ARP table: {str(e)}"
            }
    
    async def clear_arp_table(self) -> Dict[str, Any]:
        """Clear all ARP table entries."""
        try:
            result = await self.client.clear_arp_table()
            return result
        except Exception as e:
            return {
                "error": f"Failed to clear ARP table: {str(e)}"
            }
    
    async def delete_arp_entry(self, ip_address: str) -> Dict[str, Any]:
        """Delete a specific ARP table entry."""
        try:
            result = await self.client.delete_arp_entry(ip_address)
            return result
        except Exception as e:
            return {
                "error": f"Failed to delete ARP entry: {str(e)}"
            }
    
    async def get_system_logs(self, limit: int = 100) -> Dict[str, Any]:
        """Get system logs."""
        try:
            result = await self.client.get_system_logs(limit)
            return result
        except Exception as e:
            return {
                "error": f"Failed to get system logs: {str(e)}"
            }
    
    async def get_dhcp_leases(self) -> Dict[str, Any]:
        """Get DHCP lease information."""
        try:
            result = await self.client.get_dhcp_leases()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get DHCP leases: {str(e)}"
            }
    
    async def get_vpn_status(self) -> Dict[str, Any]:
        """Get VPN connection status."""
        try:
            result = await self.client.get_vpn_status()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get VPN status: {str(e)}"
            }
    
    async def get_firewall_logs(self, limit: int = 100) -> Dict[str, Any]:
        """Get firewall logs."""
        try:
            result = await self.client.get_firewall_logs(limit)
            return result
        except Exception as e:
            return {
                "error": f"Failed to get firewall logs: {str(e)}"
            }


class MinimalPfSenseMCPServer:
    """Minimal MCP server for pfSense integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the server."""
        self.config = config
        self.client = RealPfSenseClient(config)
        self.server = Server("pfsense-mcp")
        
        # Register tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
    
    async def _list_tools(self) -> List[Tool]:
        """List all available tools."""
        tools = [
            Tool(
                name="test_connection",
                description="Test connection to pfSense server",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_info",
                description="Get basic system information from pfSense",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_version",
                description="Get pfSense version information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_health",
                description="Get system health and performance information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_interfaces",
                description="Get network interface status and configuration",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_arp_table",
                description="Get ARP table entries",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_firewall_rules",
                description="Get firewall rules configuration",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_services",
                description="Get running services status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_dhcp_leases",
                description="Get DHCP lease information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_vpn_status",
                description="Get VPN connection status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="clear_arp_table",
                description="Clear all ARP table entries",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="delete_arp_entry",
                description="Delete a specific ARP table entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ip_address": {
                            "type": "string",
                            "description": "IP address of the ARP entry to delete"
                        }
                    },
                    "required": ["ip_address"]
                }
            ),
            Tool(
                name="get_system_logs",
                description="Get system logs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of log entries to retrieve (default: 100)",
                            "default": 100
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_firewall_aliases",
                description="Get firewall aliases configuration",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_service_status",
                description="Get detailed service status information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_interface_status",
                description="Get detailed interface status information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_nat_outbound_mappings",
                description="Get NAT outbound mappings",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_nat_port_forwarding",
                description="Get NAT port forwarding rules",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_nat_one_to_one_mappings",
                description="Get NAT one-to-one mappings",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_firewall_schedules",
                description="Get firewall schedules",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_firewall_states",
                description="Get firewall states",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_traffic_shaper",
                description="Get traffic shaper configuration",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_traffic_shapers",
                description="Get all traffic shapers",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_traffic_shaper_limiters",
                description="Get traffic shaper limiters",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_traffic_shaper_queues",
                description="Get traffic shaper queues",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_virtual_ips",
                description="Get virtual IP addresses",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_virtual_ip",
                description="Get specific virtual IP configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "interface": {
                            "type": "string",
                            "description": "Interface name (e.g., wan, lan, opt1)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="apply_virtual_ip_changes",
                description="Apply virtual IP configuration changes",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_firewall_logs",
                description="Get firewall logs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of log entries to retrieve (default: 100)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_firewall_aliases",
                description="Get firewall aliases configuration",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_service_status",
                description="Get detailed service status information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_interface_status",
                description="Get detailed interface status information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]
        
        return tools
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle tool calls."""
        tool_name = name
        
        try:
            if tool_name == "test_connection":
                result = await self.client.test_connection()
                return {
                    "content": [{"type": "text", "text": f"Connection test: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_system_info":
                result = await self.client.get_system_info()
                return {
                    "content": [{"type": "text", "text": f"System Info: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_version":
                result = await self.client.get_system_info()
                return {
                    "content": [{"type": "text", "text": f"pfSense Version: {result.get('version', 'Unknown')}"}],
                    "isError": False
                }
            elif tool_name == "get_system_health":
                result = await self.client.get_system_health()
                return {
                    "content": [{"type": "text", "text": f"System Health: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_interfaces":
                result = await self.client.get_interfaces()
                return {
                    "content": [{"type": "text", "text": f"Interfaces: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_arp_table":
                result = await self.client.get_arp_table()
                return {
                    "content": [{"type": "text", "text": f"ARP Table: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_firewall_rules":
                result = await self.client.get_firewall_rules()
                return {
                    "content": [{"type": "text", "text": f"Firewall Rules: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_services":
                result = await self.client.get_services()
                return {
                    "content": [{"type": "text", "text": f"Services: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_dhcp_leases":
                result = await self.client.get_dhcp_leases()
                return {
                    "content": [{"type": "text", "text": f"DHCP Leases: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_vpn_status":
                result = await self.client.get_vpn_status()
                return {
                    "content": [{"type": "text", "text": f"VPN Status: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "clear_arp_table":
                result = await self.client.clear_arp_table()
                return {
                    "content": [{"type": "text", "text": f"ARP Table Cleared: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "delete_arp_entry":
                ip_address = arguments.get("ip_address")
                if not ip_address:
                    return {
                        "content": [{"type": "text", "text": "Error: ip_address parameter is required"}],
                        "isError": True
                    }
                result = await self.client.delete_arp_entry(ip_address)
                return {
                    "content": [{"type": "text", "text": f"ARP Entry Deleted: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_system_logs":
                limit = arguments.get("limit", 100)
                result = await self.client.get_system_logs(limit)
                return {
                    "content": [{"type": "text", "text": f"System Logs: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_firewall_aliases":
                result = await self.client.get_firewall_aliases()
                return {
                    "content": [{"type": "text", "text": f"Firewall Aliases: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_service_status":
                result = await self.client.get_service_status()
                return {
                    "content": [{"type": "text", "text": f"Service Status: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_interface_status":
                result = await self.client.get_interface_status()
                return {
                    "content": [{"type": "text", "text": f"Interface Status: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_nat_outbound_mappings":
                result = await self.client.get_nat_outbound_mappings()
                return {
                    "content": [{"type": "text", "text": f"NAT Outbound Mappings: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_nat_port_forwarding":
                result = await self.client.get_nat_port_forwarding()
                return {
                    "content": [{"type": "text", "text": f"NAT Port Forwarding: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_nat_one_to_one_mappings":
                result = await self.client.get_nat_one_to_one_mappings()
                return {
                    "content": [{"type": "text", "text": f"NAT One-to-One Mappings: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_firewall_schedules":
                result = await self.client.get_firewall_schedules()
                return {
                    "content": [{"type": "text", "text": f"Firewall Schedules: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_firewall_states":
                result = await self.client.get_firewall_states()
                return {
                    "content": [{"type": "text", "text": f"Firewall States: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_traffic_shaper":
                result = await self.client.get_traffic_shaper()
                return {
                    "content": [{"type": "text", "text": f"Traffic Shaper: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_traffic_shapers":
                result = await self.client.get_traffic_shapers()
                return {
                    "content": [{"type": "text", "text": f"Traffic Shapers: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_traffic_shaper_limiters":
                result = await self.client.get_traffic_shaper_limiters()
                return {
                    "content": [{"type": "text", "text": f"Traffic Shaper Limiters: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_traffic_shaper_queues":
                result = await self.client.get_traffic_shaper_queues()
                return {
                    "content": [{"type": "text", "text": f"Traffic Shaper Queues: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_virtual_ips":
                result = await self.client.get_virtual_ips()
                return {
                    "content": [{"type": "text", "text": f"Virtual IPs: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_virtual_ip":
                interface = arguments.get("interface")
                result = await self.client.get_virtual_ip(interface)
                return {
                    "content": [{"type": "text", "text": f"Virtual IP: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "apply_virtual_ip_changes":
                result = await self.client.apply_virtual_ip_changes()
                return {
                    "content": [{"type": "text", "text": f"Virtual IP Changes Applied: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            elif tool_name == "get_firewall_logs":
                limit = arguments.get("limit", 100)
                result = await self.client.get_firewall_logs(limit)
                return {
                    "content": [{"type": "text", "text": f"Firewall Logs: {json.dumps(result, indent=2)}"}],
                    "isError": False
                }
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pfsense-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Load configuration from environment
    config = {
        "host": os.getenv("PFSENSE_HOST", "localhost"),
        "port": int(os.getenv("PFSENSE_PORT", "443")),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME", "admin"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "ssl_verify": os.getenv("PFSENSE_SSL_VERIFY", "true"),
    }
    
    # Create and run server
    server = MinimalPfSenseMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
