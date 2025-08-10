"""
Main MCP server for Warewulf management.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp import Server, StdioServerParameters
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from .warewulf_client import WarewulfClient
from .utils.logging import setup_logging
from .utils.validation import (
    validate_node_config, 
    validate_profile_config, 
    validate_image_config
)


class WarewulfMCPServer:
    """
    MCP Server for managing Warewulf cluster provisioning systems.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Warewulf MCP Server.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = setup_logging()
        self.client = None
        
        # Initialize client if config is provided
        if self.config:
            try:
                self.client = WarewulfClient(self.config)
                self.logger.info("Warewulf client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Warewulf client: {e}")
    
    async def initialize_client(self, config: Dict) -> bool:
        """
        Initialize the Warewulf client with configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client = WarewulfClient(config)
            self.config = config
            self.logger.info("Warewulf client initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Warewulf client: {e}")
            return False
    
    def get_tools(self) -> List[Tool]:
        """
        Get list of available tools.
        
        Returns:
            List of Tool objects
        """
        return [
            # Core Management Tools
            Tool(
                name="warewulf_test_connection",
                description="Test connection to Warewulf server",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="warewulf_get_version",
                description="Get Warewulf version information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="warewulf_get_api_docs",
                description="Get API documentation endpoint",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Node Management
            Tool(
                name="warewulf_list_nodes",
                description="List all nodes in the cluster",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="warewulf_get_node",
                description="Get detailed information about a specific node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_create_node",
                description="Create a new node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_name": {
                            "type": "string",
                            "description": "Name of the node"
                        },
                        "profile": {
                            "type": "string",
                            "description": "Profile to assign to the node"
                        },
                        "ipaddr": {
                            "type": "string",
                            "description": "IP address for the node"
                        },
                        "hwaddr": {
                            "type": "string",
                            "description": "MAC address for the node"
                        }
                    },
                    "required": ["node_name"]
                }
            ),
            Tool(
                name="warewulf_update_node",
                description="Update an existing node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        },
                        "node_data": {
                            "type": "object",
                            "description": "Updated node data"
                        }
                    },
                    "required": ["node_id", "node_data"]
                }
            ),
            Tool(
                name="warewulf_delete_node",
                description="Delete a node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_get_node_fields",
                description="Get available node fields",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_get_node_raw",
                description="Get raw node configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_build_node_overlays",
                description="Build overlays for a specific node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_build_all_overlays",
                description="Build all overlays",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Profile Management
            Tool(
                name="warewulf_list_profiles",
                description="List all node profiles",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="warewulf_get_profile",
                description="Get detailed information about a profile",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "Profile identifier"
                        }
                    },
                    "required": ["profile_id"]
                }
            ),
            Tool(
                name="warewulf_create_profile",
                description="Create a new profile",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "profile_name": {
                            "type": "string",
                            "description": "Name of the profile"
                        },
                        "profile_data": {
                            "type": "object",
                            "description": "Profile configuration data"
                        }
                    },
                    "required": ["profile_name", "profile_data"]
                }
            ),
            Tool(
                name="warewulf_update_profile",
                description="Update an existing profile",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "Profile identifier"
                        },
                        "profile_data": {
                            "type": "object",
                            "description": "Updated profile data"
                        }
                    },
                    "required": ["profile_id", "profile_data"]
                }
            ),
            Tool(
                name="warewulf_delete_profile",
                description="Delete a profile",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "Profile identifier"
                        }
                    },
                    "required": ["profile_id"]
                }
            ),
            
            # Image Management
            Tool(
                name="warewulf_list_images",
                description="List all available images",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="warewulf_get_image",
                description="Get detailed information about an image",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Image name"
                        }
                    },
                    "required": ["image_name"]
                }
            ),
            Tool(
                name="warewulf_build_image",
                description="Build an image",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Image name"
                        }
                    },
                    "required": ["image_name"]
                }
            ),
            Tool(
                name="warewulf_import_image",
                description="Import an image",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Image name"
                        },
                        "import_data": {
                            "type": "object",
                            "description": "Import configuration"
                        }
                    },
                    "required": ["image_name", "import_data"]
                }
            ),
            Tool(
                name="warewulf_delete_image",
                description="Delete an image",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Image name"
                        }
                    },
                    "required": ["image_name"]
                }
            ),
            
            # Overlay Management
            Tool(
                name="warewulf_list_overlays",
                description="List all overlays",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="warewulf_get_overlay",
                description="Get detailed information about an overlay",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "overlay_name": {
                            "type": "string",
                            "description": "Overlay name"
                        }
                    },
                    "required": ["overlay_name"]
                }
            ),
            Tool(
                name="warewulf_create_overlay",
                description="Create a new overlay",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "overlay_name": {
                            "type": "string",
                            "description": "Overlay name"
                        },
                        "overlay_data": {
                            "type": "object",
                            "description": "Overlay configuration"
                        }
                    },
                    "required": ["overlay_name", "overlay_data"]
                }
            ),
            Tool(
                name="warewulf_delete_overlay",
                description="Delete an overlay",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "overlay_name": {
                            "type": "string",
                            "description": "Overlay name"
                        }
                    },
                    "required": ["overlay_name"]
                }
            ),
            Tool(
                name="warewulf_get_overlay_file",
                description="Get overlay file contents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "overlay_name": {
                            "type": "string",
                            "description": "Overlay name"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path within overlay"
                        }
                    },
                    "required": ["overlay_name", "file_path"]
                }
            ),
            
            # Power Management
            Tool(
                name="warewulf_power_on",
                description="Power on a node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_power_off",
                description="Power off a node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_power_reset",
                description="Reset a node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_power_cycle",
                description="Power cycle a node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="warewulf_power_status",
                description="Get power status of a node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node identifier"
                        }
                    },
                    "required": ["node_id"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """
        Call a tool by name with arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self.client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="❌ Warewulf client not initialized. Please configure the connection first."
                    )
                ],
                isError=True
            )
        
        try:
            self.logger.info(f"Calling tool: {name} with arguments: {arguments}")
            
            if name == "warewulf_test_connection":
                result = self.client.test_connection()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔌 Connection Test Result:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_version":
                result = self.client.get_version()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📋 Version Information:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_api_docs":
                result = self.client.get_api_docs()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📚 API Documentation:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            # Node Management
            elif name == "warewulf_list_nodes":
                result = self.client.list_nodes()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🖥️ Nodes List:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_node":
                node_id = arguments.get("node_id")
                result = self.client.get_node(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🖥️ Node Information for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_create_node":
                node_data = arguments
                # Validate node configuration
                errors = validate_node_config(node_data)
                if errors:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"❌ Validation errors:\n" + "\n".join(errors)
                            )
                        ],
                        isError=True
                    )
                
                result = self.client.create_node(node_data)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Node Creation Result:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_update_node":
                node_id = arguments.get("node_id")
                node_data = arguments.get("node_data", {})
                result = self.client.update_node(node_id, node_data)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Node Update Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_delete_node":
                node_id = arguments.get("node_id")
                result = self.client.delete_node(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🗑️ Node Deletion Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_node_fields":
                node_id = arguments.get("node_id")
                result = self.client.get_node_fields(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📋 Node Fields for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_node_raw":
                node_id = arguments.get("node_id")
                result = self.client.get_node_raw(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📄 Raw Node Configuration for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_build_node_overlays":
                node_id = arguments.get("node_id")
                result = self.client.build_node_overlays(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔨 Overlay Build Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_build_all_overlays":
                result = self.client.build_all_overlays()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔨 All Overlays Build Result:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            # Profile Management
            elif name == "warewulf_list_profiles":
                result = self.client.list_profiles()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📋 Profiles List:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_profile":
                profile_id = arguments.get("profile_id")
                result = self.client.get_profile(profile_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📋 Profile Information for {profile_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_create_profile":
                profile_name = arguments.get("profile_name")
                profile_data = arguments.get("profile_data", {})
                profile_data["profile_name"] = profile_name
                
                # Validate profile configuration
                errors = validate_profile_config(profile_data)
                if errors:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"❌ Validation errors:\n" + "\n".join(errors)
                            )
                        ],
                        isError=True
                    )
                
                result = self.client.create_profile(profile_data)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Profile Creation Result:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_update_profile":
                profile_id = arguments.get("profile_id")
                profile_data = arguments.get("profile_data", {})
                result = self.client.update_profile(profile_id, profile_data)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Profile Update Result for {profile_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_delete_profile":
                profile_id = arguments.get("profile_id")
                result = self.client.delete_profile(profile_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🗑️ Profile Deletion Result for {profile_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            # Image Management
            elif name == "warewulf_list_images":
                result = self.client.list_images()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🖼️ Images List:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_image":
                image_name = arguments.get("image_name")
                result = self.client.get_image(image_name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🖼️ Image Information for {image_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_build_image":
                image_name = arguments.get("image_name")
                result = self.client.build_image(image_name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔨 Image Build Result for {image_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_import_image":
                image_name = arguments.get("image_name")
                import_data = arguments.get("import_data", {})
                result = self.client.import_image(image_name, import_data)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📥 Image Import Result for {image_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_delete_image":
                image_name = arguments.get("image_name")
                result = self.client.delete_image(image_name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🗑️ Image Deletion Result for {image_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            # Overlay Management
            elif name == "warewulf_list_overlays":
                result = self.client.list_overlays()
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📁 Overlays List:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_overlay":
                overlay_name = arguments.get("overlay_name")
                result = self.client.get_overlay(overlay_name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📁 Overlay Information for {overlay_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_create_overlay":
                overlay_name = arguments.get("overlay_name")
                overlay_data = arguments.get("overlay_data", {})
                result = self.client.create_overlay(overlay_name, overlay_data)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Overlay Creation Result for {overlay_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_delete_overlay":
                overlay_name = arguments.get("overlay_name")
                result = self.client.delete_overlay(overlay_name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🗑️ Overlay Deletion Result for {overlay_name}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_get_overlay_file":
                overlay_name = arguments.get("overlay_name")
                file_path = arguments.get("file_path")
                result = self.client.get_overlay_file(overlay_name, file_path)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"📄 Overlay File Contents for {overlay_name}/{file_path}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            # Power Management
            elif name == "warewulf_power_on":
                node_id = arguments.get("node_id")
                result = self.client.power_on(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔌 Power On Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_power_off":
                node_id = arguments.get("node_id")
                result = self.client.power_off(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔌 Power Off Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_power_reset":
                node_id = arguments.get("node_id")
                result = self.client.power_reset(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔌 Power Reset Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_power_cycle":
                node_id = arguments.get("node_id")
                result = self.client.power_cycle(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔌 Power Cycle Result for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            elif name == "warewulf_power_status":
                node_id = arguments.get("node_id")
                result = self.client.power_status(node_id)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"🔌 Power Status for {node_id}:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"❌ Unknown tool: {name}"
                        )
                    ],
                    isError=True
                )
                
        except Exception as e:
            self.logger.error(f"Error calling tool {name}: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Error executing tool {name}: {str(e)}"
                    )
                ],
                isError=True
            )


async def main():
    """Main entry point for the MCP server."""
    # Create server instance
    server = Server("warewulf-mcp")
    warewulf_server = WarewulfMCPServer()
    
    # Register tools
    @server.list_tools()
    async def handle_list_tools() -> ListToolsResult:
        return ListToolsResult(tools=warewulf_server.get_tools())
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        return await warewulf_server.call_tool(name, arguments)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="warewulf-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
