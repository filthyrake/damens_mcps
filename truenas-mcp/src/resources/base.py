"""Base resource class for TrueNAS MCP server."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import CallToolRequest, CallToolResult, TextContent, Tool

from ..truenas_client import TrueNASClient

logger = logging.getLogger(__name__)


class BaseResource(ABC):
    """Base class for all resource handlers."""

    def __init__(self, client: TrueNASClient):
        """Initialize the base resource.
        
        Args:
            client: TrueNAS API client instance
        """
        self.client = client
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Get list of tools provided by this resource.
        
        Returns:
            List of Tool objects
        """
        pass
    
    @abstractmethod
    async def handle_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle a tool call for this resource.
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call result
        """
        pass
    
    def register_tools(self, server: Server) -> None:
        """Register tools with the MCP server.
        
        Args:
            server: MCP server instance
        """
        # This is a default implementation that can be overridden
        # by subclasses if they need custom registration logic
        pass
    
    def _format_response(self, data: Any) -> str:
        """Format response data for MCP output.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted string representation
        """
        if isinstance(data, dict):
            return self._format_dict(data)
        elif isinstance(data, list):
            return self._format_list(data)
        else:
            return str(data)
    
    def _format_dict(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Format dictionary data.
        
        Args:
            data: Dictionary to format
            indent: Indentation level
            
        Returns:
            Formatted string
        """
        if not data:
            return "{}"
        
        lines = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                formatted_value = self._format_dict(value, indent + 1)
                lines.append(f"{indent_str}{key}:")
                lines.append(formatted_value)
            elif isinstance(value, list):
                formatted_value = self._format_list(value, indent + 1)
                lines.append(f"{indent_str}{key}:")
                lines.append(formatted_value)
            else:
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _format_list(self, data: List[Any], indent: int = 0) -> str:
        """Format list data.
        
        Args:
            data: List to format
            indent: Indentation level
            
        Returns:
            Formatted string
        """
        if not data:
            return "[]"
        
        lines = []
        indent_str = "  " * indent
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                formatted_item = self._format_dict(item, indent + 1)
                lines.append(f"{indent_str}[{i}]:")
                lines.append(formatted_item)
            elif isinstance(item, list):
                formatted_item = self._format_list(item, indent + 1)
                lines.append(f"{indent_str}[{i}]:")
                lines.append(formatted_item)
            else:
                lines.append(f"{indent_str}[{i}]: {item}")
        
        return "\n".join(lines)
    
    def _validate_required_params(self, params: Dict[str, Any], required: List[str]) -> None:
        """Validate that required parameters are present.
        
        Args:
            params: Parameters to validate
            required: List of required parameter names
            
        Raises:
            ValueError: If required parameters are missing
        """
        missing = [param for param in required if param not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
    
    def _safe_get_param(self, params: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get a parameter value.
        
        Args:
            params: Parameters dictionary
            key: Parameter key
            default: Default value if key not found
            
        Returns:
            Parameter value or default
        """
        return params.get(key, default)
    
    def _create_error_result(self, error: str) -> CallToolResult:
        """Create an error result.
        
        Args:
            error: Error message
            
        Returns:
            Error result
        """
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {error}")],
            isError=True
        )
    
    def _create_success_result(self, data: Any) -> CallToolResult:
        """Create a success result.
        
        Args:
            data: Data to include in result
            
        Returns:
            Success result
        """
        formatted_data = self._format_response(data)
        return CallToolResult(
            content=[TextContent(type="text", text=formatted_data)]
        )
