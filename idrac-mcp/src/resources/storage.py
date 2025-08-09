"""Storage resource handler for iDRAC MCP Server."""

from typing import Dict, Any

from .base import BaseResource

from ..utils.logging import get_logger

logger = get_logger(__name__)


class StorageResource(BaseResource):
    """Handler for storage management tools."""
    
    def register_tools(self):
        """Register storage management tools."""
        self.tools = [
            self.create_tool(
                name="idrac_storage_controllers",
                description="Get storage controllers information from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def handle_storage_controllers(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle storage controllers tool call."""
        try:
            self.log_tool_call("idrac_storage_controllers", arguments)
            result = await self.idrac_client.get_storage_controllers()
            self.log_tool_result("idrac_storage_controllers", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_storage_controllers", None, str(e))
            raise
