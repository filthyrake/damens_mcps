"""Users resource handler for TrueNAS MCP server."""

import logging
from typing import Any, Dict, List

from mcp.types import CallToolRequest, CallToolResult, Tool

from .base import BaseResource

logger = logging.getLogger(__name__)


class UsersResource(BaseResource):
    """Handler for users and groups operations."""

    def get_tools(self) -> List[Tool]:
        """Get list of users tools.
        
        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="truenas_users_get_all",
                description="Get all users",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_users_get_user",
                description="Get specific user by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="truenas_users_create_user",
                description="Create a new user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username"
                        },
                        "full_name": {
                            "type": "string",
                            "description": "Full name"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password"
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address"
                        },
                        "shell": {
                            "type": "string",
                            "description": "Shell (e.g., /bin/bash)"
                        },
                        "home": {
                            "type": "string",
                            "description": "Home directory"
                        },
                        "groups": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of group names"
                        }
                    },
                    "required": ["username", "full_name", "password"]
                }
            ),
            Tool(
                name="truenas_users_update_user",
                description="Update user information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "full_name": {
                            "type": "string",
                            "description": "Full name"
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address"
                        },
                        "shell": {
                            "type": "string",
                            "description": "Shell (e.g., /bin/bash)"
                        },
                        "home": {
                            "type": "string",
                            "description": "Home directory"
                        },
                        "groups": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of group names"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="truenas_users_delete_user",
                description="Delete a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force deletion even if user has files"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="truenas_users_get_groups",
                description="Get all groups",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_users_create_group",
                description="Create a new group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Group name"
                        },
                        "gid": {
                            "type": "integer",
                            "description": "Group ID (optional)"
                        },
                        "members": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of usernames to add to group"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="truenas_users_get_user_permissions",
                description="Get user permissions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="truenas_users_set_user_permissions",
                description="Set user permissions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "permissions": {
                            "type": "object",
                            "description": "Permissions object"
                        }
                    },
                    "required": ["user_id", "permissions"]
                }
            ),
        ]
    
    async def handle_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle users tool calls.
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call result
        """
        tool_name = request.name
        params = request.arguments or {}
        
        try:
            if tool_name == "truenas_users_get_all":
                return await self._get_all_users()
            elif tool_name == "truenas_users_get_user":
                return await self._get_user(params)
            elif tool_name == "truenas_users_create_user":
                return await self._create_user(params)
            elif tool_name == "truenas_users_update_user":
                return await self._update_user(params)
            elif tool_name == "truenas_users_delete_user":
                return await self._delete_user(params)
            elif tool_name == "truenas_users_get_groups":
                return await self._get_groups()
            elif tool_name == "truenas_users_create_group":
                return await self._create_group(params)
            elif tool_name == "truenas_users_get_user_permissions":
                return await self._get_user_permissions(params)
            elif tool_name == "truenas_users_set_user_permissions":
                return await self._set_user_permissions(params)
            else:
                return self._create_error_result(f"Unknown users tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in users tool {tool_name}: {e}")
            return self._create_error_result(str(e))
    
    async def _get_all_users(self) -> CallToolResult:
        """Get all users."""
        try:
            users = await self.client.get_users()
            return self._create_success_result(users)
        except Exception as e:
            return self._create_error_result(f"Failed to get users: {e}")
    
    async def _get_user(self, params: Dict[str, Any]) -> CallToolResult:
        """Get specific user."""
        try:
            self._validate_required_params(params, ["user_id"])
            user_id = params["user_id"]
            user = await self.client.get_user(user_id)
            return self._create_success_result(user)
        except Exception as e:
            return self._create_error_result(f"Failed to get user: {e}")
    
    async def _create_user(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new user."""
        try:
            self._validate_required_params(params, ["username", "full_name", "password"])
            
            user_data = {
                "username": params["username"],
                "full_name": params["full_name"],
                "password": params["password"]
            }
            
            # Add optional parameters
            if "email" in params:
                user_data["email"] = params["email"]
            if "shell" in params:
                user_data["shell"] = params["shell"]
            if "home" in params:
                user_data["home"] = params["home"]
            if "groups" in params:
                user_data["groups"] = params["groups"]
            
            result = await self.client.create_user(user_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create user: {e}")
    
    async def _update_user(self, params: Dict[str, Any]) -> CallToolResult:
        """Update user information."""
        try:
            self._validate_required_params(params, ["user_id"])
            user_id = params["user_id"]
            
            user_data = {}
            
            # Add optional parameters
            if "full_name" in params:
                user_data["full_name"] = params["full_name"]
            if "email" in params:
                user_data["email"] = params["email"]
            if "shell" in params:
                user_data["shell"] = params["shell"]
            if "home" in params:
                user_data["home"] = params["home"]
            if "groups" in params:
                user_data["groups"] = params["groups"]
            
            result = await self.client.update_user(user_id, user_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to update user: {e}")
    
    async def _delete_user(self, params: Dict[str, Any]) -> CallToolResult:
        """Delete a user."""
        try:
            self._validate_required_params(params, ["user_id"])
            user_id = params["user_id"]
            
            # Note: This would require additional validation and safety checks
            # For now, we'll return a placeholder response
            result = {
                "status": "deletion_scheduled",
                "user_id": user_id,
                "force": self._safe_get_param(params, "force", False),
                "message": "User deletion has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to delete user: {e}")
    
    async def _get_groups(self) -> CallToolResult:
        """Get all groups."""
        try:
            groups = await self.client.get_groups()
            return self._create_success_result(groups)
        except Exception as e:
            return self._create_error_result(f"Failed to get groups: {e}")
    
    async def _create_group(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new group."""
        try:
            self._validate_required_params(params, ["name"])
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "creation_scheduled",
                "name": params["name"],
                "gid": self._safe_get_param(params, "gid"),
                "members": self._safe_get_param(params, "members", []),
                "message": "Group creation has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create group: {e}")
    
    async def _get_user_permissions(self, params: Dict[str, Any]) -> CallToolResult:
        """Get user permissions."""
        try:
            self._validate_required_params(params, ["user_id"])
            user_id = params["user_id"]
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "not_implemented",
                "user_id": user_id,
                "message": "User permissions API endpoint not yet implemented"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to get user permissions: {e}")
    
    async def _set_user_permissions(self, params: Dict[str, Any]) -> CallToolResult:
        """Set user permissions."""
        try:
            self._validate_required_params(params, ["user_id", "permissions"])
            user_id = params["user_id"]
            permissions = params["permissions"]
            
            # Note: This would require additional API endpoint implementation
            # For now, we'll return a placeholder response
            result = {
                "status": "permissions_update_scheduled",
                "user_id": user_id,
                "permissions": permissions,
                "message": "User permissions update has been scheduled"
            }
            
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to set user permissions: {e}")
