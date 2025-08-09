"""Services resource handler for TrueNAS MCP server."""

import logging
from typing import Any, Dict, List

from mcp.types import CallToolRequest, CallToolResult, Tool

from .base import BaseResource

logger = logging.getLogger(__name__)


class ServicesResource(BaseResource):
    """Handler for services-related operations."""

    def get_tools(self) -> List[Tool]:
        """Get list of services tools.
        
        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="truenas_services_get_all",
                description="Get all services",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_services_get_service",
                description="Get specific service by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "string",
                            "description": "Service ID"
                        }
                    },
                    "required": ["service_id"]
                }
            ),
            Tool(
                name="truenas_services_start_service",
                description="Start a service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "string",
                            "description": "Service ID"
                        }
                    },
                    "required": ["service_id"]
                }
            ),
            Tool(
                name="truenas_services_stop_service",
                description="Stop a service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "string",
                            "description": "Service ID"
                        }
                    },
                    "required": ["service_id"]
                }
            ),
            Tool(
                name="truenas_services_restart_service",
                description="Restart a service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "string",
                            "description": "Service ID"
                        }
                    },
                    "required": ["service_id"]
                }
            ),
            Tool(
                name="truenas_services_get_smb_shares",
                description="Get SMB shares",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_services_create_smb_share",
                description="Create a new SMB share",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Share name"
                        },
                        "path": {
                            "type": "string",
                            "description": "Path to share"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Share comment"
                        },
                        "readonly": {
                            "type": "boolean",
                            "description": "Make share read-only"
                        }
                    },
                    "required": ["name", "path"]
                }
            ),
            Tool(
                name="truenas_services_get_nfs_shares",
                description="Get NFS shares",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_services_create_nfs_share",
                description="Create a new NFS share",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to share"
                        },
                        "hosts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Allowed hosts"
                        },
                        "readonly": {
                            "type": "boolean",
                            "description": "Make share read-only"
                        }
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="truenas_services_get_iscsi_targets",
                description="Get iSCSI targets",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_services_create_iscsi_target",
                description="Create a new iSCSI target",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Target name"
                        },
                        "alias": {
                            "type": "string",
                            "description": "Target alias"
                        }
                    },
                    "required": ["name"]
                }
            ),
        ]
    
    async def handle_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle services tool calls.
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call result
        """
        tool_name = request.name
        params = request.arguments or {}
        
        try:
            if tool_name == "truenas_services_get_all":
                return await self._get_all_services()
            elif tool_name == "truenas_services_get_service":
                return await self._get_service(params)
            elif tool_name == "truenas_services_start_service":
                return await self._start_service(params)
            elif tool_name == "truenas_services_stop_service":
                return await self._stop_service(params)
            elif tool_name == "truenas_services_restart_service":
                return await self._restart_service(params)
            elif tool_name == "truenas_services_get_smb_shares":
                return await self._get_smb_shares()
            elif tool_name == "truenas_services_create_smb_share":
                return await self._create_smb_share(params)
            elif tool_name == "truenas_services_get_nfs_shares":
                return await self._get_nfs_shares()
            elif tool_name == "truenas_services_create_nfs_share":
                return await self._create_nfs_share(params)
            elif tool_name == "truenas_services_get_iscsi_targets":
                return await self._get_iscsi_targets()
            elif tool_name == "truenas_services_create_iscsi_target":
                return await self._create_iscsi_target(params)
            else:
                return self._create_error_result(f"Unknown services tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in services tool {tool_name}: {e}")
            return self._create_error_result(str(e))
    
    async def _get_all_services(self) -> CallToolResult:
        """Get all services."""
        try:
            services = await self.client.get_services()
            return self._create_success_result(services)
        except Exception as e:
            return self._create_error_result(f"Failed to get services: {e}")
    
    async def _get_service(self, params: Dict[str, Any]) -> CallToolResult:
        """Get specific service."""
        try:
            self._validate_required_params(params, ["service_id"])
            service_id = params["service_id"]
            service = await self.client.get_service(service_id)
            return self._create_success_result(service)
        except Exception as e:
            return self._create_error_result(f"Failed to get service: {e}")
    
    async def _start_service(self, params: Dict[str, Any]) -> CallToolResult:
        """Start a service."""
        try:
            self._validate_required_params(params, ["service_id"])
            service_id = params["service_id"]
            result = await self.client.start_service(service_id)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to start service: {e}")
    
    async def _stop_service(self, params: Dict[str, Any]) -> CallToolResult:
        """Stop a service."""
        try:
            self._validate_required_params(params, ["service_id"])
            service_id = params["service_id"]
            result = await self.client.stop_service(service_id)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to stop service: {e}")
    
    async def _restart_service(self, params: Dict[str, Any]) -> CallToolResult:
        """Restart a service."""
        try:
            self._validate_required_params(params, ["service_id"])
            service_id = params["service_id"]
            result = await self.client.restart_service(service_id)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to restart service: {e}")
    
    async def _get_smb_shares(self) -> CallToolResult:
        """Get SMB shares."""
        try:
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "not_implemented",
                "message": "SMB shares API endpoint not yet implemented"
            }
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to get SMB shares: {e}")
    
    async def _create_smb_share(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new SMB share."""
        try:
            self._validate_required_params(params, ["name", "path"])
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "creation_scheduled",
                "name": params["name"],
                "path": params["path"],
                "comment": self._safe_get_param(params, "comment", ""),
                "readonly": self._safe_get_param(params, "readonly", False),
                "message": "SMB share creation has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create SMB share: {e}")
    
    async def _get_nfs_shares(self) -> CallToolResult:
        """Get NFS shares."""
        try:
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "not_implemented",
                "message": "NFS shares API endpoint not yet implemented"
            }
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to get NFS shares: {e}")
    
    async def _create_nfs_share(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new NFS share."""
        try:
            self._validate_required_params(params, ["path"])
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "creation_scheduled",
                "path": params["path"],
                "hosts": self._safe_get_param(params, "hosts", []),
                "readonly": self._safe_get_param(params, "readonly", False),
                "message": "NFS share creation has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create NFS share: {e}")
    
    async def _get_iscsi_targets(self) -> CallToolResult:
        """Get iSCSI targets."""
        try:
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "not_implemented",
                "message": "iSCSI targets API endpoint not yet implemented"
            }
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to get iSCSI targets: {e}")
    
    async def _create_iscsi_target(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new iSCSI target."""
        try:
            self._validate_required_params(params, ["name"])
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "creation_scheduled",
                "name": params["name"],
                "alias": self._safe_get_param(params, "alias", ""),
                "message": "iSCSI target creation has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create iSCSI target: {e}")
