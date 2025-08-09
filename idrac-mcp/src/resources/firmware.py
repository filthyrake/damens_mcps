"""Firmware resource handler for iDRAC MCP Server."""

from typing import Dict, Any

from .base import BaseResource

from ..utils.logging import get_logger

logger = get_logger(__name__)


class FirmwareResource(BaseResource):
    """Handler for firmware management tools."""
    
    def register_tools(self):
        """Register firmware management tools."""
        self.tools = [
            self.create_tool(
                name="idrac_firmware_versions",
                description="Get firmware versions from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def handle_firmware_versions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle firmware versions tool call."""
        try:
            self.log_tool_call("idrac_firmware_versions", arguments)
            result = await self.idrac_client.get_firmware_versions()
            self.log_tool_result("idrac_firmware_versions", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_firmware_versions", None, str(e))
            raise
