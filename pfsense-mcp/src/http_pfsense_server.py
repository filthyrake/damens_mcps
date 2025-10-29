#!/usr/bin/env python3
"""
pfSense MCP Server - HTTP-based server for pfSense firewall management.

This is the CANONICAL implementation of the pfSense MCP server.
All other server implementations have been removed to avoid confusion.
Use this file for all pfSense MCP server operations.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import mcp.server.stdio
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    InitializeRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from mcp.shared.message import SessionMessage

try:
    from .pfsense_client import HTTPPfSenseClient, PfSenseAPIError
    from .utils.logging import setup_logging, get_logger
    from .utils.validation import (
        validate_firewall_rule_params,
        validate_vlan_params,
        validate_package_name,
        validate_service_name,
        validate_backup_name,
        validate_id
    )
except ImportError:
    # Fallback for direct execution
    from pfsense_client import HTTPPfSenseClient, PfSenseAPIError
    from utils.logging import setup_logging, get_logger
    from utils.validation import (
        validate_firewall_rule_params,
        validate_vlan_params,
        validate_package_name,
        validate_service_name,
        validate_backup_name,
        validate_id
    )

# Set up logging to stderr only (not stdout to avoid breaking MCP protocol)
import sys
import os

# Completely suppress all output except JSON responses
import sys
import os

# Create a completely silent stdout that only allows JSON
class SilentStdout:
    def __init__(self):
        self.original_stdout = sys.stdout
        self.null_output = open(os.devnull, 'w')
    
    def write(self, text):
        # Only allow JSON responses to go through
        if text.strip().startswith('{"jsonrpc":'):
            self.original_stdout.write(text)
        # Everything else is silently discarded
    
    def flush(self):
        self.original_stdout.flush()
    
    def fileno(self):
        return self.original_stdout.fileno()
    
    def close(self):
        """Explicitly close the null_output file handle."""
        if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
            self.null_output.close()
    
    def __del__(self):
        """Ensure file handle is properly closed on cleanup."""
        self.close()

# Set up the filter
sys.stdout = SilentStdout()

# Completely disable all logging
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().setLevel(logging.CRITICAL)

# Create a completely silent logger
logger = logging.getLogger("pfsense-mcp")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.CRITICAL)

# Also suppress stderr for any remaining output
class SilentStderr:
    def __init__(self):
        self.original_stderr = sys.stderr
        self.null_output = open(os.devnull, 'w')
    
    def write(self, text):
        # Silently discard all stderr output
        pass
    
    def flush(self):
        pass
    
    def fileno(self):
        return self.original_stderr.fileno()
    
    def close(self):
        """Explicitly close the file handle if needed."""
        if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
            self.null_output.close()
    
    def __del__(self):
        """Ensure file handle is properly closed on cleanup."""
        self.close()

sys.stderr = SilentStderr()

# Global client instance
pfsense_client: Optional[HTTPPfSenseClient] = None


class HTTPPfSenseMCPServer:
    """
    MCP Server for pfSense management via HTTP API.
    """
    
    def __init__(self):
        """Initialize the MCP server."""
        self.tools = self._create_tools()
    
    def _create_tools(self) -> List[Tool]:
        """Create the list of available tools."""
        return [
            # System Management Tools
            Tool(
                name="get_system_info",
                description="Get pfSense system information including version and uptime",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_health",
                description="Get pfSense system health information including CPU, memory, and disk usage",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_interfaces",
                description="Get information about all network interfaces and their status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_services",
                description="Get information about running services (DNS, DHCP, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Firewall Management Tools
            Tool(
                name="get_firewall_rules",
                description="Get all firewall rules",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="create_firewall_rule",
                description=(
                    "Create a new firewall rule with validation.\n\n"
                    "This operation will:\n"
                    "- Create a firewall rule with specified action (pass, block, or reject)\n"
                    "- Apply to specified interface and traffic direction\n"
                    "- Optionally filter by source/destination addresses and ports\n\n"
                    "Example: Create a rule to block incoming traffic from 192.168.1.100:\n"
                    '  {"action": "block", "interface": "wan", "direction": "in", "source": "192.168.1.100"}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["pass", "block", "reject"],
                            "description": "Action for the rule"
                        },
                        "interface": {
                            "type": "string",
                            "description": "Interface name"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["in", "out"],
                            "description": "Traffic direction"
                        },
                        "source": {
                            "type": "string",
                            "description": "Source address (IP or 'any')"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination address (IP or 'any')"
                        },
                        "port": {
                            "type": "string",
                            "description": "Port number or service name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Rule description"
                        }
                    },
                    "required": ["action", "interface", "direction"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="delete_firewall_rule",
                description="Delete a firewall rule by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule_id": {
                            "type": "string",
                            "description": "ID of the rule to delete"
                        }
                    },
                    "required": ["rule_id"]
                }
            ),
            Tool(
                name="get_firewall_logs",
                description="Get recent firewall logs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of log entries to retrieve",
                            "default": 100
                        }
                    },
                    "required": []
                }
            ),
            
            # Network Configuration Tools
            Tool(
                name="get_vlans",
                description="Get VLAN configurations",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="create_vlan",
                description="Create a new VLAN",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "vlan_id": {
                            "type": "integer",
                            "description": "VLAN ID (1-4094)"
                        },
                        "interface": {
                            "type": "string",
                            "description": "Parent interface name"
                        },
                        "description": {
                            "type": "string",
                            "description": "VLAN description"
                        }
                    },
                    "required": ["vlan_id", "interface"]
                }
            ),
            Tool(
                name="delete_vlan",
                description="Delete a VLAN by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "vlan_id": {
                            "type": "string",
                            "description": "ID of the VLAN to delete"
                        }
                    },
                    "required": ["vlan_id"]
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
                name="get_dns_servers",
                description="Get DNS server configuration",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Package Management Tools
            Tool(
                name="get_installed_packages",
                description="Get list of installed packages",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="install_package",
                description="Install a new package",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Name of the package to install"
                        }
                    },
                    "required": ["package_name"]
                }
            ),
            Tool(
                name="remove_package",
                description="Remove a package",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Name of the package to remove"
                        }
                    },
                    "required": ["package_name"]
                }
            ),
            Tool(
                name="get_package_updates",
                description="Check for available package updates",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # VPN Management Tools
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
                name="get_openvpn_servers",
                description="Get OpenVPN server configurations",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_openvpn_clients",
                description="Get OpenVPN client configurations",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="restart_vpn_service",
                description="Restart a VPN service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the VPN service to restart"
                        }
                    },
                    "required": ["service_name"]
                }
            ),
            
            # Backup & Restore Tools
            Tool(
                name="create_backup",
                description="Create a system backup",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backup_name": {
                            "type": "string",
                            "description": "Name for the backup"
                        }
                    },
                    "required": ["backup_name"]
                }
            ),
            Tool(
                name="restore_backup",
                description="Restore from a backup",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backup_id": {
                            "type": "string",
                            "description": "ID of the backup to restore from"
                        }
                    },
                    "required": ["backup_id"]
                }
            ),
            Tool(
                name="get_backup_list",
                description="Get list of available backups",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Connection Test Tool
            Tool(
                name="test_connection",
                description="Test connection to pfSense",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """
        Call a tool by name with the given arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result as CallToolResult
        """
        global pfsense_client
        
        if not pfsense_client:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: pfSense client not initialized")],
                isError=True
            )
        
        try:
            
            if name == "get_system_info":
                result = await pfsense_client.get_system_info()
            elif name == "get_system_health":
                result = await pfsense_client.get_system_health()
            elif name == "get_interfaces":
                result = await pfsense_client.get_interfaces()
            elif name == "get_services":
                result = await pfsense_client.get_services()
            elif name == "get_firewall_rules":
                result = await pfsense_client.get_firewall_rules()
            elif name == "create_firewall_rule":
                # Validate parameters
                errors = validate_firewall_rule_params(arguments)
                if errors:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Validation errors: {', '.join(errors)}")],
                        isError=True
                    )
                result = await pfsense_client.create_firewall_rule(arguments)
            elif name == "delete_firewall_rule":
                rule_id = arguments.get("rule_id", "")
                if not rule_id or not validate_id(rule_id):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: rule_id is required and must be alphanumeric with hyphens/underscores")],
                        isError=True
                    )
                result = await pfsense_client.delete_firewall_rule(rule_id)
            elif name == "get_firewall_logs":
                limit = arguments.get("limit", 100)
                result = await pfsense_client.get_firewall_logs(limit)
            elif name == "get_vlans":
                result = await pfsense_client.get_vlans()
            elif name == "create_vlan":
                # Validate parameters
                errors = validate_vlan_params(arguments)
                if errors:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Validation errors: {', '.join(errors)}")],
                        isError=True
                    )
                result = await pfsense_client.create_vlan(arguments)
            elif name == "delete_vlan":
                vlan_id = arguments.get("vlan_id", "")
                if not vlan_id or not validate_id(vlan_id):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: vlan_id is required and must be alphanumeric with hyphens/underscores")],
                        isError=True
                    )
                result = await pfsense_client.delete_vlan(vlan_id)
            elif name == "get_dhcp_leases":
                result = await pfsense_client.get_dhcp_leases()
            elif name == "get_dns_servers":
                result = await pfsense_client.get_dns_servers()
            elif name == "get_installed_packages":
                result = await pfsense_client.get_installed_packages()
            elif name == "install_package":
                package_name = arguments.get("package_name", "")
                if not package_name or not validate_package_name(package_name):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: package_name is required and must be alphanumeric with dots, hyphens, or underscores")],
                        isError=True
                    )
                result = await pfsense_client.install_package(package_name)
            elif name == "remove_package":
                package_name = arguments.get("package_name", "")
                if not package_name or not validate_package_name(package_name):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: package_name is required and must be alphanumeric with dots, hyphens, or underscores")],
                        isError=True
                    )
                result = await pfsense_client.remove_package(package_name)
            elif name == "get_package_updates":
                result = await pfsense_client.get_package_updates()
            elif name == "get_vpn_status":
                result = await pfsense_client.get_vpn_status()
            elif name == "get_openvpn_servers":
                result = await pfsense_client.get_openvpn_servers()
            elif name == "get_openvpn_clients":
                result = await pfsense_client.get_openvpn_clients()
            elif name == "restart_vpn_service":
                service_name = arguments.get("service_name", "")
                if not service_name or not validate_service_name(service_name):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: service_name is required and must be alphanumeric with hyphens or underscores")],
                        isError=True
                    )
                result = await pfsense_client.restart_vpn_service(service_name)
            elif name == "create_backup":
                backup_name = arguments.get("backup_name", "")
                if not backup_name or not validate_backup_name(backup_name):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: backup_name is required and must be alphanumeric with dots, hyphens, or underscores")],
                        isError=True
                    )
                result = await pfsense_client.create_backup(backup_name)
            elif name == "restore_backup":
                backup_id = arguments.get("backup_id", "")
                if not backup_id or not validate_id(backup_id):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Error: backup_id is required and must be alphanumeric with hyphens or underscores")],
                        isError=True
                    )
                result = await pfsense_client.restore_backup(backup_id)
            elif name == "get_backup_list":
                result = await pfsense_client.get_backup_list()
            elif name == "test_connection":
                success = await pfsense_client.test_connection()
                result = {"connected": success}
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True
                )
            
            # Convert result to JSON string for proper serialization
            result_text = json.dumps(result, indent=2, default=str)
            
            # Return proper CallToolResult
            return CallToolResult(
                content=[TextContent(type="text", text=result_text)],
                isError=False
            )
            
        except PfSenseAPIError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"pfSense API error: {str(e)}")],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unexpected error: {str(e)}")],
                isError=True
            )


async def initialize_pfsense_client() -> Optional[HTTPPfSenseClient]:
    """
    Initialize the pfSense client from environment variables.
    
    Returns:
        Initialized HTTPPfSenseClient or None if initialization fails
    """
    config = {
        "host": os.getenv("PFSENSE_HOST", "localhost"),
        "port": os.getenv("PFSENSE_PORT", "443"),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "ssl_verify": os.getenv("PFSENSE_SSL_VERIFY", "true")
    }
    
    try:
        client = HTTPPfSenseClient(config)
        # Test connection
        if await client.test_connection():
            return client
        else:
            return None
    except Exception as e:
        return None


async def main():
    """Main entry point for the MCP server."""
    global pfsense_client
    
    try:
        # Initialize pfSense client (may be None if connection fails)
        pfsense_client = await initialize_pfsense_client()
        
        # Create MCP server
        server = HTTPPfSenseMCPServer()
        
        # Create stdio server
        async with stdio_server() as (read_stream, write_stream):
            # Handle requests
            async for request in read_stream:
                if isinstance(request, ListToolsRequest):
                    await mcp.server.stdio.list_tools(write_stream, request, server.tools)
                elif isinstance(request, CallToolRequest):
                    result = await server._call_tool(request.name, request.arguments)
                    await mcp.server.stdio.call_tool(write_stream, request, result)
                elif isinstance(request, InitializeRequest):
                    # Send initialization response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "serverInfo": {
                                "name": "pfsense-mcp",
                                "version": "1.0.0"
                            }
                        }
                    }
                    # Use original stdout for JSON response
                    original_stdout = sys.stdout.original_stdout
                    sys.stdout = original_stdout
                    print(json.dumps(response))
                    sys.stdout = SilentStdout()
                elif isinstance(request, SessionMessage):
                    # Handle session messages (ignore for now)
                    pass
                else:
                    pass
                    
    except Exception as e:
        sys.exit(1)
    finally:
        if pfsense_client:
            await pfsense_client.close()


if __name__ == "__main__":
    asyncio.run(main())
