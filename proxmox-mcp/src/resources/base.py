"""Base resource class for Proxmox MCP Server."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool

from ..proxmox_client import ProxmoxClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BaseResource(ABC):
    """Base class for all resource handlers."""
    
    def __init__(self, client: ProxmoxClient):
        """Initialize the resource handler.
        
        Args:
            client: Proxmox client instance
        """
        self.client = client
    
    @abstractmethod
    def register_tools(self, server: Server) -> None:
        """Register tools for this resource with the MCP server.
        
        Args:
            server: MCP server instance
        """
        pass
    
    def create_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler) -> Tool:
        """Create a tool definition.
        
        Args:
            name: Tool name
            description: Tool description
            input_schema: Input schema for the tool
            handler: Tool handler function
            
        Returns:
            Tool definition
        """
        return Tool(
            name=name,
            description=description,
            inputSchema=input_schema
        )
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Log a tool call.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
        """
        logger.info(f"Calling tool: {tool_name}", extra={
            "tool_name": tool_name,
            "arguments": arguments
        })
    
    def log_tool_result(self, tool_name: str, result: Any, error: str = None) -> None:
        """Log a tool result.
        
        Args:
            tool_name: Name of the tool that was called
            result: Tool result
            error: Error message if any
        """
        if error:
            logger.error(f"Tool {tool_name} failed: {error}")
        else:
            logger.info(f"Tool {tool_name} completed successfully")
