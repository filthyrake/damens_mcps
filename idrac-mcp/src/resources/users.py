"""Users resource handler for iDRAC MCP Server."""

from typing import Dict, Any

from .base import BaseResource

from ..utils.logging import get_logger

logger = get_logger(__name__)


class UsersResource(BaseResource):
    """Handler for user management tools."""
    
    def register_tools(self):
        """Register user management tools."""
        self.tools = [
            self.create_tool(
                name="idrac_users_list",
                description="List iDRAC users",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            self.create_tool(
                name="idrac_user_create",
                description="Create a new iDRAC user",
                input_schema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username for the new user"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password for the new user"
                        },
                        "privilege": {
                            "type": "string",
                            "description": "User privilege level",
                            "enum": ["Administrator", "Operator", "ReadOnly"],
                            "default": "Administrator"
                        },
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether the user is enabled",
                            "default": True
                        }
                    },
                    "required": ["username", "password"]
                }
            )
        ]
    
    async def handle_users_list(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle users list tool call."""
        try:
            self.log_tool_call("idrac_users_list", arguments)
            result = await self.idrac_client.get_users()
            self.log_tool_result("idrac_users_list", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_users_list", None, str(e))
            raise
    
    async def handle_user_create(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user create tool call."""
        try:
            self.log_tool_call("idrac_user_create", arguments)
            result = await self.idrac_client.create_user(arguments)
            self.log_tool_result("idrac_user_create", result)
            return result
        except Exception as e:
            self.log_tool_result("idrac_user_create", None, str(e))
            raise
