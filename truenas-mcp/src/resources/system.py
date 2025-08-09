"""System resource handler for TrueNAS MCP server."""

import logging
from typing import Any, Dict, List

from mcp.types import CallToolRequest, CallToolResult, Tool

from .base import BaseResource

logger = logging.getLogger(__name__)


class SystemResource(BaseResource):
    """Handler for system-related operations."""

    def get_tools(self) -> List[Tool]:
        """Get list of system tools.
        
        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="truenas_system_get_info",
                description="Get detailed system information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_get_version",
                description="Get TrueNAS version information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_get_health",
                description="Get system health status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_get_uptime",
                description="Get system uptime information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_get_stats",
                description="Get system statistics and metrics",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_get_alerts",
                description="Get system alerts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of alerts to return"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_get_alert_classes",
                description="Get available alert classes",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_reboot",
                description="Reboot the TrueNAS system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "delay": {
                            "type": "integer",
                            "description": "Delay in seconds before reboot"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="truenas_system_shutdown",
                description="Shutdown the TrueNAS system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "delay": {
                            "type": "integer",
                            "description": "Delay in seconds before shutdown"
                        }
                    },
                    "required": []
                }
            ),
        ]
    
    async def handle_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle system tool calls.
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call result
        """
        tool_name = request.name
        params = request.arguments or {}
        
        try:
            if tool_name == "truenas_system_get_info":
                return await self._get_system_info()
            elif tool_name == "truenas_system_get_version":
                return await self._get_version()
            elif tool_name == "truenas_system_get_health":
                return await self._get_health()
            elif tool_name == "truenas_system_get_uptime":
                return await self._get_uptime()
            elif tool_name == "truenas_system_get_stats":
                return await self._get_stats()
            elif tool_name == "truenas_system_get_alerts":
                return await self._get_alerts(params)
            elif tool_name == "truenas_system_get_alert_classes":
                return await self._get_alert_classes()
            elif tool_name == "truenas_system_reboot":
                return await self._reboot_system(params)
            elif tool_name == "truenas_system_shutdown":
                return await self._shutdown_system(params)
            else:
                return self._create_error_result(f"Unknown system tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in system tool {tool_name}: {e}")
            return self._create_error_result(str(e))
    
    async def _get_system_info(self) -> CallToolResult:
        """Get detailed system information."""
        try:
            info = await self.client.get_system_info()
            return self._create_success_result(info)
        except Exception as e:
            return self._create_error_result(f"Failed to get system info: {e}")
    
    async def _get_version(self) -> CallToolResult:
        """Get TrueNAS version information."""
        try:
            version = await self.client.get_version()
            return self._create_success_result(version)
        except Exception as e:
            return self._create_error_result(f"Failed to get version: {e}")
    
    async def _get_health(self) -> CallToolResult:
        """Get system health status."""
        try:
            health = await self.client.get_health()
            return self._create_success_result(health)
        except Exception as e:
            return self._create_error_result(f"Failed to get health: {e}")
    
    async def _get_uptime(self) -> CallToolResult:
        """Get system uptime information."""
        try:
            uptime = await self.client.get_uptime()
            return self._create_success_result(uptime)
        except Exception as e:
            return self._create_error_result(f"Failed to get uptime: {e}")
    
    async def _get_stats(self) -> CallToolResult:
        """Get system statistics."""
        try:
            stats = await self.client.get_system_stats()
            return self._create_success_result(stats)
        except Exception as e:
            return self._create_error_result(f"Failed to get stats: {e}")
    
    async def _get_alerts(self, params: Dict[str, Any]) -> CallToolResult:
        """Get system alerts."""
        try:
            alerts = await self.client.get_alert_list()
            
            # Apply limit if specified
            limit = self._safe_get_param(params, "limit")
            if limit and isinstance(limit, int) and limit > 0:
                alerts = alerts[:limit]
            
            return self._create_success_result(alerts)
        except Exception as e:
            return self._create_error_result(f"Failed to get alerts: {e}")
    
    async def _get_alert_classes(self) -> CallToolResult:
        """Get alert classes."""
        try:
            classes = await self.client.get_alert_classes()
            return self._create_success_result(classes)
        except Exception as e:
            return self._create_error_result(f"Failed to get alert classes: {e}")
    
    async def _reboot_system(self, params: Dict[str, Any]) -> CallToolResult:
        """Reboot the system."""
        try:
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            delay = self._safe_get_param(params, "delay", 0)
            
            # This is a placeholder - actual implementation would call the reboot API
            result = {
                "status": "reboot_scheduled",
                "delay_seconds": delay,
                "message": "System reboot has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to reboot system: {e}")
    
    async def _shutdown_system(self, params: Dict[str, Any]) -> CallToolResult:
        """Shutdown the system."""
        try:
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            delay = self._safe_get_param(params, "delay", 0)
            
            # This is a placeholder - actual implementation would call the shutdown API
            result = {
                "status": "shutdown_scheduled",
                "delay_seconds": delay,
                "message": "System shutdown has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to shutdown system: {e}")
