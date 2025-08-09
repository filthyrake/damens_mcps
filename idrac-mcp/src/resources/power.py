"""Power resource handler for iDRAC MCP Server."""

from typing import Dict, Any

from .base import BaseResource

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PowerResource(BaseResource):
    """Handler for power management tools."""
    
    def register_tools(self):
        """Register power management tools."""
        self.tools = [
            self.create_tool(
                name="idrac_power_on",
                description="Power on the server via iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_power_off",
                description="Power off the server via iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force power off",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_power_cycle",
                description="Power cycle the server via iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force power cycle",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_graceful_shutdown",
                description="Perform graceful shutdown via iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def handle_power_on(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle power on tool call."""
        try:
            self.log_tool_call("idrac_power_on", arguments)
            result = await self.idrac_client.power_on()
            self.log_tool_result("idrac_power_on", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_power_on", None, str(e))
            raise
    
    async def handle_power_off(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle power off tool call."""
        try:
            self.log_tool_call("idrac_power_off", arguments)
            force = arguments.get("force", False)
            result = await self.idrac_client.power_off(force=force)
            self.log_tool_result("idrac_power_off", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_power_off", None, str(e))
            raise
    
    async def handle_power_cycle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle power cycle tool call."""
        try:
            self.log_tool_call("idrac_power_cycle", arguments)
            force = arguments.get("force", False)
            result = await self.idrac_client.power_cycle(force=force)
            self.log_tool_result("idrac_power_cycle", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_power_cycle", None, str(e))
            raise
    
    async def handle_graceful_shutdown(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle graceful shutdown tool call."""
        try:
            self.log_tool_call("idrac_graceful_shutdown", arguments)
            result = await self.idrac_client.power_off(force=False)
            self.log_tool_result("idrac_graceful_shutdown", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_graceful_shutdown", None, str(e))
            raise
