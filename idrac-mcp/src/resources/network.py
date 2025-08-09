"""Network resource handler for iDRAC MCP Server."""

from typing import Dict, Any

from .base import BaseResource

from ..utils.logging import get_logger

logger = get_logger(__name__)


class NetworkResource(BaseResource):
    """Handler for network management tools."""
    
    def register_tools(self):
        """Register network management tools."""
        self.tools = [
            self.create_tool(
                name="idrac_network_config",
                description="Get iDRAC network configuration",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def handle_network_config(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network config tool call."""
        try:
            self.log_tool_call("idrac_network_config", arguments)
            result = await self.idrac_client.get_network_config()
            self.log_tool_result("idrac_network_config", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_network_config", None, str(e))
            raise
