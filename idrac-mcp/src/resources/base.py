"""Base resource handler for iDRAC MCP Server."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from mcp import Tool

from ..utils.logging import get_logger

logger = get_logger(__name__)


class BaseResource(ABC):
    """Base class for all resource handlers."""
    
    def __init__(self, idrac_client):
        """Initialize the resource handler.
        
        Args:
            idrac_client: iDRAC client instance
        """
        self.idrac_client = idrac_client
        self.tools: List[Tool] = []
        self.register_tools()
    
    @abstractmethod
    def register_tools(self):
        """Register tools for this resource."""
        pass
    
    def create_tool(self, name: str, description: str, input_schema: Dict[str, Any]) -> Tool:
        """Create a tool with the given parameters.
        
        Args:
            name: Tool name
            description: Tool description
            input_schema: Input schema for the tool
            
        Returns:
            Tool instance
        """
        return Tool(
            name=name,
            description=description,
            inputSchema=input_schema
        )
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """Log a tool call.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
        """
        logger.info(f"Tool called: {tool_name}", tool_name=tool_name, arguments=arguments)
    
    def log_tool_result(self, tool_name: str, result: Any, error: str = None):
        """Log a tool result.
        
        Args:
            tool_name: Name of the tool
            result: Tool result
            error: Error message if any
        """
        if error:
            logger.error(f"Tool {tool_name} failed: {error}", tool_name=tool_name, error=error)
        else:
            logger.info(f"Tool {tool_name} completed successfully")
