#!/usr/bin/env python3
"""
Minimal test server to isolate MCP communication issues.
"""

import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp.server import Server, InitializationOptions, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    TextContent,
    ListToolsRequest,
    ListToolsResult,
    Tool
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalTestServer:
    """Minimal test server to isolate MCP issues."""
    
    def __init__(self):
        self.server = Server("minimal-test-server")
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="test_simple",
                    description="A simple test tool that returns a string",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "A message to echo back"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                    name="test_json",
                    description="A test tool that returns JSON data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "JSON data to process"
                            }
                        },
                        "required": ["data"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            logger.info(f"Calling tool: {name} with arguments: {arguments}")
            
            try:
                if name == "test_simple":
                    message = arguments.get("message", "No message provided")
                    result_text = f"Echo: {message}"
                    logger.info(f"Returning simple result: {result_text}")
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=result_text)]
                    )
                    
                elif name == "test_json":
                    data = arguments.get("data", "{}")
                    try:
                        parsed_data = json.loads(data)
                        result_text = json.dumps(parsed_data, indent=2)
                    except json.JSONDecodeError:
                        result_text = f"Invalid JSON: {data}"
                    
                    logger.info(f"Returning JSON result: {result_text}")
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=result_text)]
                    )
                    
                else:
                    error_text = f"Unknown tool: {name}"
                    logger.error(error_text)
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=error_text)]
                    )
                    
            except Exception as e:
                error_text = f"Error calling tool {name}: {str(e)}"
                logger.error(error_text)
                
                return CallToolResult(
                    content=[TextContent(type="text", text=error_text)]
                )
    
    async def run(self) -> None:
        """Run the minimal test server."""
        logger.info("Starting minimal test server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="minimal-test-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(), 
                        experimental_capabilities={}
                    )
                )
            )

async def main() -> None:
    """Main entry point."""
    logger.info("Initializing minimal test server...")
    server = MinimalTestServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
