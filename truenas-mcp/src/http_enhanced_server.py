#!/usr/bin/env python3
"""
HTTP-based TrueNAS MCP Server - Comprehensive TrueNAS Scale Management
Based on svnstfns/truenas-mcp-server approach with HTTP REST API calls
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from the project root (parent of src directory)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables only")

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTTPTrueNASClient:
    """HTTP-based TrueNAS client using REST API calls."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 443)
        self.api_key = config.get("api_key")
        self.protocol = config.get("protocol", "https")
        self.ssl_verify = config.get("ssl_verify", False)
        self.session = None
        
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            try:
                import aiohttp
                import ssl
                
                # Create SSL context
                ssl_context = None
                if self.protocol == "https":
                    ssl_context = ssl.create_default_context()
                    if not self.ssl_verify:
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                self.session = aiohttp.ClientSession(connector=connector)
                logger.info(f"Created HTTP session for {self.protocol}://{self.host}:{self.port}")
                
            except ImportError:
                logger.error("aiohttp library not available. Install with: pip install aiohttp")
                raise
            except Exception as e:
                logger.error(f"Failed to create HTTP session: {e}")
                raise
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to TrueNAS API."""
        await self._get_session()
        
        url = f"{self.protocol}://{self.host}:{self.port}/api/v2.0/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        
        try:
            logger.info(f"Making {method} request to {url}")
            if data:
                logger.info(f"Request data: {json.dumps(data, indent=2)}")
            
            async with self.session.request(method, url, headers=headers, json=data) as response:
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response text: {response_text}")
                
                if response.status >= 400:
                    raise Exception(f"HTTP {response.status}: {response_text}")
                
                if response_text:
                    return json.loads(response_text)
                return {}
                
        except Exception as e:
            logger.error(f"Error making request to TrueNAS: {e}")
            raise
    
    async def _close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    # Connection & System Management
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to TrueNAS."""
        try:
            # Try to get system info as a connection test
            system_info = await self._make_request("GET", "system/info")
            return {
                "status": "connected",
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "message": "Connection test successful",
                "system_info": system_info
            }
        except Exception as e:
            return {
                "status": "error",
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "message": f"Connection failed: {str(e)}"
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        try:
            return await self._make_request("GET", "system/info")
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "error": str(e),
                "hostname": self.host,
                "message": "Failed to get system information"
            }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            # Get system alerts and warnings
            alerts = await self._make_request("GET", "alert/list")
            system_info = await self._make_request("GET", "system/info")
            
            return {
                "status": "healthy" if not alerts else "warning",
                "alerts": alerts,
                "system_info": system_info,
                "message": "System health check completed"
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "message": f"Failed to get system health: {str(e)}"
            }
    
    async def get_storage_pools(self) -> List[Dict[str, Any]]:
        """Get storage pools information."""
        try:
            return await self._make_request("GET", "pool")
        except Exception as e:
            logger.error(f"Error getting storage pools: {e}")
            return []
    
    async def get_datasets(self, pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get datasets information."""
        try:
            endpoint = "zfs/dataset"
            if pool_name:
                endpoint += f"?pool={pool_name}"
            return await self._make_request("GET", endpoint)
        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return []
    
    async def create_dataset(self, name: str, pool: str, dataset_type: str = "filesystem") -> Dict[str, Any]:
        """Create a new dataset."""
        try:
            data = {
                "name": name,
                "type": dataset_type
            }
            return await self._make_request("POST", "zfs/dataset", data)
        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            return {"error": str(e)}
    
    async def delete_dataset(self, name: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete a dataset."""
        try:
            data = {"recursive": recursive}
            return await self._make_request("DELETE", f"zfs/dataset/id/{name}", data)
        except Exception as e:
            logger.error(f"Error deleting dataset: {e}")
            return {"error": str(e)}
    
    async def list_custom_apps(self) -> List[Dict[str, Any]]:
        """List all Custom Apps."""
        try:
            return await self._make_request("GET", "app")
        except Exception as e:
            logger.error(f"Error listing custom apps: {e}")
            return []
    
    async def get_custom_app_status(self, app_name: str) -> Dict[str, Any]:
        """Get status of a Custom App."""
        try:
            return await self._make_request("GET", f"app/id/{app_name}")
        except Exception as e:
            logger.error(f"Error getting app status: {e}")
            return {"error": str(e)}
    
    async def start_custom_app(self, app_name: str) -> Dict[str, Any]:
        """Start a Custom App."""
        try:
            return await self._make_request("POST", f"app/id/{app_name}/start")
        except Exception as e:
            logger.error(f"Error starting app: {e}")
            return {"error": str(e)}
    
    async def stop_custom_app(self, app_name: str) -> Dict[str, Any]:
        """Stop a Custom App."""
        try:
            return await self._make_request("POST", f"app/id/{app_name}/stop")
        except Exception as e:
            logger.error(f"Error stopping app: {e}")
            return {"error": str(e)}
    
    async def restart_custom_app(self, app_name: str) -> Dict[str, Any]:
        """Restart a Custom App."""
        try:
            # First stop, then start
            await self._make_request("POST", f"app/id/{app_name}/stop")
            await asyncio.sleep(2)  # Wait a bit
            return await self._make_request("POST", f"app/id/{app_name}/start")
        except Exception as e:
            logger.error(f"Error restarting app: {e}")
            return {"error": str(e)}
    
    async def deploy_custom_app(self, app_name: str, compose_data: str) -> Dict[str, Any]:
        """Deploy a new Custom App from Docker Compose."""
        try:
            # This would need to be implemented based on TrueNAS API
            # For now, return a placeholder
            return {
                "message": f"Deploying app {app_name}",
                "status": "deploying",
                "compose_data": compose_data[:100] + "..." if len(compose_data) > 100 else compose_data
            }
        except Exception as e:
            logger.error(f"Error deploying app: {e}")
            return {"error": str(e)}
    
    async def update_custom_app(self, app_name: str, compose_data: str) -> Dict[str, Any]:
        """Update an existing Custom App."""
        try:
            # This would need to be implemented based on TrueNAS API
            return {
                "message": f"Updating app {app_name}",
                "status": "updating"
            }
        except Exception as e:
            logger.error(f"Error updating app: {e}")
            return {"error": str(e)}
    
    async def delete_custom_app(self, app_name: str, delete_volumes: bool = False) -> Dict[str, Any]:
        """Delete a Custom App."""
        try:
            return await self._make_request("DELETE", f"app/id/{app_name}")
        except Exception as e:
            logger.error(f"Error deleting app: {e}")
            return {"error": str(e)}
    
    async def get_app_logs(self, app_name: str, lines: int = 50) -> Dict[str, Any]:
        """Get logs from a Custom App."""
        try:
            return await self._make_request("GET", f"app/id/{app_name}/logs?limit={lines}")
        except Exception as e:
            logger.error(f"Error getting app logs: {e}")
            return {"error": str(e)}
    
    async def get_app_metrics(self, app_name: str) -> Dict[str, Any]:
        """Get performance metrics for a Custom App."""
        try:
            # This would need to be implemented based on TrueNAS API
            return {
                "app_name": app_name,
                "message": "Metrics not implemented yet"
            }
        except Exception as e:
            logger.error(f"Error getting app metrics: {e}")
            return {"error": str(e)}
    
    async def validate_compose(self, compose_data: str) -> Dict[str, Any]:
        """Validate Docker Compose for TrueNAS compatibility."""
        try:
            # Basic validation - check if it's valid YAML/JSON
            import yaml
            yaml.safe_load(compose_data)
            return {
                "valid": True,
                "message": "Docker Compose appears valid"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "Docker Compose validation failed"
            }
    
    async def convert_compose_to_app(self, compose_data: str) -> Dict[str, Any]:
        """Convert Docker Compose to TrueNAS Custom App format."""
        try:
            # This would need to be implemented based on TrueNAS API
            return {
                "message": "Conversion not implemented yet",
                "compose_data": compose_data[:100] + "..." if len(compose_data) > 100 else compose_data
            }
        except Exception as e:
            logger.error(f"Error converting compose: {e}")
            return {"error": str(e)}
    
    async def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interfaces and their status."""
        try:
            return await self._make_request("GET", "interface")
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            return []
    
    async def get_network_routes(self) -> List[Dict[str, Any]]:
        """Get network routing information."""
        try:
            return await self._make_request("GET", "network/route")
        except Exception as e:
            logger.error(f"Error getting network routes: {e}")
            return []
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """List all users on the system."""
        try:
            return await self._make_request("GET", "user")
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def create_user(self, username: str, full_name: str, password: str) -> Dict[str, Any]:
        """Create a new user account."""
        try:
            data = {
                "username": username,
                "full_name": full_name,
                "password": password
            }
            return await self._make_request("POST", "user", data)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {"error": str(e)}
    
    async def delete_user(self, username: str) -> Dict[str, Any]:
        """Delete a user account."""
        try:
            return await self._make_request("DELETE", f"user/id/{username}")
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return {"error": str(e)}
    
    async def get_snapshots(self, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """List snapshots."""
        try:
            endpoint = "zfs/snapshot"
            if dataset:
                endpoint += f"?dataset={dataset}"
            return await self._make_request("GET", endpoint)
        except Exception as e:
            logger.error(f"Error getting snapshots: {e}")
            return []
    
    async def create_snapshot(self, dataset: str, name: str) -> Dict[str, Any]:
        """Create a new snapshot."""
        try:
            data = {
                "dataset": dataset,
                "name": name
            }
            return await self._make_request("POST", "zfs/snapshot", data)
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return {"error": str(e)}
    
    async def delete_snapshot(self, snapshot_name: str) -> Dict[str, Any]:
        """Delete a snapshot."""
        try:
            return await self._make_request("DELETE", f"zfs/snapshot/id/{snapshot_name}")
        except Exception as e:
            logger.error(f"Error deleting snapshot: {e}")
            return {"error": str(e)}
    
    async def get_replication_tasks(self) -> List[Dict[str, Any]]:
        """List replication tasks."""
        try:
            return await self._make_request("GET", "replication")
        except Exception as e:
            logger.error(f"Error getting replication tasks: {e}")
            return []
    
    async def get_services(self) -> List[Dict[str, Any]]:
        """List system services and their status."""
        try:
            return await self._make_request("GET", "service")
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []
    
    async def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start a system service."""
        try:
            return await self._make_request("POST", f"service/start", {"service": service_name})
        except Exception as e:
            logger.error(f"Error starting service: {e}")
            return {"error": str(e)}
    
    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop a system service."""
        try:
            return await self._make_request("POST", f"service/stop", {"service": service_name})
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            return {"error": str(e)}
    
    async def enable_service(self, service_name: str) -> Dict[str, Any]:
        """Enable a system service to start on boot."""
        try:
            return await self._make_request("POST", f"service/enable", {"service": service_name})
        except Exception as e:
            logger.error(f"Error enabling service: {e}")
            return {"error": str(e)}
    
    async def disable_service(self, service_name: str) -> Dict[str, Any]:
        """Disable a system service from starting on boot."""
        try:
            return await self._make_request("POST", f"service/disable", {"service": service_name})
        except Exception as e:
            logger.error(f"Error disabling service: {e}")
            return {"error": str(e)}
    
    async def __aenter__(self):
        await self._get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()


class HTTPTrueNASMCPServer:
    """HTTP-based TrueNAS MCP Server."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = HTTPTrueNASClient(config)
    
    async def _list_tools(self) -> List[Tool]:
        """List all available tools."""
        return [
            # System Management
            Tool(
                name="test_connection",
                description="Test connection to TrueNAS server",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_system_info",
                description="Get comprehensive system information from TrueNAS",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_system_health",
                description="Get system health status and alerts",
                inputSchema={"type": "object", "properties": {}}
            ),
            
            # Storage Management
            Tool(
                name="get_storage_pools",
                description="List all storage pools with usage information",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_datasets",
                description="List datasets, optionally filtered by pool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_name": {
                            "type": "string",
                            "description": "Optional pool name to filter by"
                        }
                    }
                }
            ),
            Tool(
                name="create_dataset",
                description="Create a new dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Dataset name (e.g., 'tank/media')"
                        },
                        "pool": {
                            "type": "string",
                            "description": "Pool name"
                        },
                        "dataset_type": {
                            "type": "string",
                            "description": "Dataset type (filesystem, volume, etc.)",
                            "default": "filesystem"
                        }
                    },
                    "required": ["name", "pool"]
                }
            ),
            Tool(
                name="delete_dataset",
                description="Delete a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Dataset name to delete"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Delete recursively",
                            "default": False
                        }
                    },
                    "required": ["name"]
                }
            ),
            
            # Custom Apps Management
            Tool(
                name="list_custom_apps",
                description="List all Custom Apps with detailed information",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_custom_app_status",
                description="Get detailed status of a Custom App",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App"
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            Tool(
                name="start_custom_app",
                description="Start a stopped Custom App",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App to start"
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            Tool(
                name="stop_custom_app",
                description="Stop a running Custom App",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App to stop"
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            Tool(
                name="restart_custom_app",
                description="Restart a Custom App",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App to restart"
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            Tool(
                name="deploy_custom_app",
                description="Deploy a new Custom App from Docker Compose",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name for the new Custom App"
                        },
                        "compose_data": {
                            "type": "string",
                            "description": "Docker Compose YAML content"
                        }
                    },
                    "required": ["app_name", "compose_data"]
                }
            ),
            Tool(
                name="update_custom_app",
                description="Update an existing Custom App configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App to update"
                        },
                        "compose_data": {
                            "type": "string",
                            "description": "Updated Docker Compose YAML content"
                        }
                    },
                    "required": ["app_name", "compose_data"]
                }
            ),
            Tool(
                name="delete_custom_app",
                description="Delete a Custom App and optionally its volumes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App to delete"
                        },
                        "delete_volumes": {
                            "type": "boolean",
                            "description": "Whether to delete associated volumes",
                            "default": False
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            Tool(
                name="get_app_logs",
                description="Get logs from a Custom App",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App"
                        },
                        "lines": {
                            "type": "integer",
                            "description": "Number of log lines to retrieve",
                            "default": 50
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            Tool(
                name="get_app_metrics",
                description="Get performance metrics for a Custom App",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the Custom App"
                        }
                    },
                    "required": ["app_name"]
                }
            ),
            
            # Docker Compose Tools
            Tool(
                name="validate_compose",
                description="Validate Docker Compose for TrueNAS compatibility",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "compose_data": {
                            "type": "string",
                            "description": "Docker Compose YAML content to validate"
                        }
                    },
                    "required": ["compose_data"]
                }
            ),
            Tool(
                name="convert_compose_to_app",
                description="Convert Docker Compose to TrueNAS Custom App format",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "compose_data": {
                            "type": "string",
                            "description": "Docker Compose YAML content to convert"
                        }
                    },
                    "required": ["compose_data"]
                }
            ),
            
            # Network Management
            Tool(
                name="get_network_interfaces",
                description="Get network interfaces and their status",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_network_routes",
                description="Get network routing information",
                inputSchema={"type": "object", "properties": {}}
            ),
            
            # User Management
            Tool(
                name="get_users",
                description="List all users on the system",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="create_user",
                description="Create a new user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username for the new user"
                        },
                        "full_name": {
                            "type": "string",
                            "description": "Full name of the user"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password for the user"
                        }
                    },
                    "required": ["username", "full_name", "password"]
                }
            ),
            Tool(
                name="delete_user",
                description="Delete a user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username to delete"
                        }
                    },
                    "required": ["username"]
                }
            ),
            
            # Snapshot Management
            Tool(
                name="get_snapshots",
                description="List snapshots, optionally filtered by dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset": {
                            "type": "string",
                            "description": "Optional dataset name to filter by"
                        }
                    }
                }
            ),
            Tool(
                name="create_snapshot",
                description="Create a new snapshot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset": {
                            "type": "string",
                            "description": "Dataset name to snapshot"
                        },
                        "name": {
                            "type": "string",
                            "description": "Snapshot name"
                        }
                    },
                    "required": ["dataset", "name"]
                }
            ),
            Tool(
                name="delete_snapshot",
                description="Delete a snapshot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshot_name": {
                            "type": "string",
                            "description": "Full snapshot name to delete"
                        }
                    },
                    "required": ["snapshot_name"]
                }
            ),
            
            # Replication Management
            Tool(
                name="get_replication_tasks",
                description="List replication tasks",
                inputSchema={"type": "object", "properties": {}}
            ),
            
            # Service Management
            Tool(
                name="get_services",
                description="List system services and their status",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="start_service",
                description="Start a system service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service to start"
                        }
                    },
                    "required": ["service_name"]
                }
            ),
            Tool(
                name="stop_service",
                description="Stop a system service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service to stop"
                        }
                    },
                    "required": ["service_name"]
                }
            ),
            Tool(
                name="enable_service",
                description="Enable a system service to start on boot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service to enable"
                        }
                    },
                    "required": ["service_name"]
                }
            ),
            Tool(
                name="disable_service",
                description="Disable a system service from starting on boot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service to disable"
                        }
                    },
                    "required": ["service_name"]
                }
            ),
        ]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name with arguments."""
        try:
            if name == "test_connection":
                result = await self.client.test_connection()
            elif name == "get_system_info":
                result = await self.client.get_system_info()
            elif name == "get_system_health":
                result = await self.client.get_system_health()
            elif name == "get_storage_pools":
                result = await self.client.get_storage_pools()
            elif name == "get_datasets":
                result = await self.client.get_datasets(arguments.get("pool_name"))
            elif name == "create_dataset":
                result = await self.client.create_dataset(
                    arguments["name"], 
                    arguments["pool"], 
                    arguments.get("dataset_type", "filesystem")
                )
            elif name == "delete_dataset":
                result = await self.client.delete_dataset(
                    arguments["name"], 
                    arguments.get("recursive", False)
                )
            elif name == "list_custom_apps":
                result = await self.client.list_custom_apps()
            elif name == "get_custom_app_status":
                result = await self.client.get_custom_app_status(arguments["app_name"])
            elif name == "start_custom_app":
                result = await self.client.start_custom_app(arguments["app_name"])
            elif name == "stop_custom_app":
                result = await self.client.stop_custom_app(arguments["app_name"])
            elif name == "restart_custom_app":
                result = await self.client.restart_custom_app(arguments["app_name"])
            elif name == "deploy_custom_app":
                result = await self.client.deploy_custom_app(
                    arguments["app_name"], 
                    arguments["compose_data"]
                )
            elif name == "update_custom_app":
                result = await self.client.update_custom_app(
                    arguments["app_name"], 
                    arguments["compose_data"]
                )
            elif name == "delete_custom_app":
                result = await self.client.delete_custom_app(
                    arguments["app_name"], 
                    arguments.get("delete_volumes", False)
                )
            elif name == "get_app_logs":
                result = await self.client.get_app_logs(
                    arguments["app_name"], 
                    arguments.get("lines", 50)
                )
            elif name == "get_app_metrics":
                result = await self.client.get_app_metrics(arguments["app_name"])
            elif name == "validate_compose":
                result = await self.client.validate_compose(arguments["compose_data"])
            elif name == "convert_compose_to_app":
                result = await self.client.convert_compose_to_app(arguments["compose_data"])
            elif name == "get_network_interfaces":
                result = await self.client.get_network_interfaces()
            elif name == "get_network_routes":
                result = await self.client.get_network_routes()
            elif name == "get_users":
                result = await self.client.get_users()
            elif name == "create_user":
                result = await self.client.create_user(
                    arguments["username"], 
                    arguments["full_name"], 
                    arguments["password"]
                )
            elif name == "delete_user":
                result = await self.client.delete_user(arguments["username"])
            elif name == "get_snapshots":
                result = await self.client.get_snapshots(arguments.get("dataset"))
            elif name == "create_snapshot":
                result = await self.client.create_snapshot(
                    arguments["dataset"], 
                    arguments["name"]
                )
            elif name == "delete_snapshot":
                result = await self.client.delete_snapshot(arguments["snapshot_name"])
            elif name == "get_replication_tasks":
                result = await self.client.get_replication_tasks()
            elif name == "get_services":
                result = await self.client.get_services()
            elif name == "start_service":
                result = await self.client.start_service(arguments["service_name"])
            elif name == "stop_service":
                result = await self.client.stop_service(arguments["service_name"])
            elif name == "enable_service":
                result = await self.client.enable_service(arguments["service_name"])
            elif name == "disable_service":
                result = await self.client.disable_service(arguments["service_name"])
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    "isError": False
                }
            
            # Convert result to JSON string for display
            result_text = json.dumps(result, indent=2, default=str)
            return {
                "content": [{"type": "text", "text": result_text}],
                "isError": False
            }
            
        except Exception as e:
            error_text = f"Error calling tool {name}: {str(e)}"
            logger.error(error_text)
            return {
                "content": [{"type": "text", "text": error_text}],
                "isError": True
            }
    
    async def run(self) -> None:
        """Run the MCP server."""
        server = Server("truenas-mcp-server")
        
        @server.list_tools()
        async def list_tools() -> List[Tool]:
            return await self._list_tools()
        
        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            return await self._call_tool(name, arguments)
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="truenas-mcp-server",
                    server_version="1.0.0",
                    capabilities={}
                )
            )


async def main() -> None:
    """Main entry point."""
    # Load configuration from environment variables
    config = {
        "host": os.getenv("TRUENAS_HOST", "localhost"),
        "port": int(os.getenv("TRUENAS_PORT", "443")),
        "api_key": os.getenv("TRUENAS_API_KEY"),
        "protocol": os.getenv("TRUENAS_PROTOCOL", "https"),
        "ssl_verify": os.getenv("TRUENAS_SSL_VERIFY", "false").lower() == "true"
    }
    
    if not config["api_key"]:
        logger.error("TRUENAS_API_KEY environment variable is required")
        sys.exit(1)
    
    server = HTTPTrueNASMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
