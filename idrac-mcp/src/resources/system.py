"""System resource handler for iDRAC MCP Server."""

from typing import Dict, Any

from .base import BaseResource

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SystemResource(BaseResource):
    """Handler for system management tools."""
    
    def register_tools(self):
        """Register system management tools."""
        self.tools = [
            self.create_tool(
                name="idrac_system_info",
                description="Get system information from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_system_health",
                description="Get system health status from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_hardware_inventory",
                description="Get hardware inventory from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_power_status",
                description="Get power status from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_thermal_status",
                description="Get thermal status from iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_test_connection",
                description="Test connection to iDRAC",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def handle_system_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system info tool call."""
        try:
            self.log_tool_call("idrac_system_info", arguments)
            result = await self.idrac_client.get_system_info()
            self.log_tool_result("idrac_system_info", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_system_info", None, str(e))
            raise
    
    async def handle_system_health(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system health tool call."""
        try:
            self.log_tool_call("idrac_system_health", arguments)
            result = await self.idrac_client.get_system_health()
            self.log_tool_result("idrac_system_health", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_system_health", None, str(e))
            raise
    
    async def handle_hardware_inventory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hardware inventory tool call."""
        try:
            self.log_tool_call("idrac_hardware_inventory", arguments)
            result = await self.idrac_client.get_hardware_inventory()
            self.log_tool_result("idrac_hardware_inventory", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_hardware_inventory", None, str(e))
            raise
    
    async def handle_power_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle power status tool call."""
        try:
            self.log_tool_call("idrac_power_status", arguments)
            result = await self.idrac_client.get_power_status()
            self.log_tool_result("idrac_power_status", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_power_status", None, str(e))
            raise
    
    async def handle_thermal_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle thermal status tool call."""
        try:
            self.log_tool_call("idrac_thermal_status", arguments)
            result = await self.idrac_client.get_thermal_status()
            self.log_tool_result("idrac_thermal_status", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_thermal_status", None, str(e))
            raise
    
    async def handle_test_connection(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test connection tool call."""
        try:
            self.log_tool_call("idrac_test_connection", arguments)
            result = await self.idrac_client.test_connection()
            self.log_tool_result("idrac_test_connection", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_test_connection", None, str(e))
            raise
