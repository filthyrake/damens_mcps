"""TrueNAS API client for communicating with TrueNAS Scale server."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel, Field

from .auth import AuthManager
from .utils.validation import validate_id, validate_dataset_name

logger = logging.getLogger(__name__)


class TrueNASConfig(BaseModel):
    """Configuration for TrueNAS connection."""
    host: str = Field(..., description="TrueNAS host address")
    port: int = Field(443, description="TrueNAS port")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the TrueNAS API."""
        protocol = "https" if self.port == 443 else "http"
        return f"{protocol}://{self.host}:{self.port}/api/v2.0"


class TrueNASClient:
    """Client for interacting with TrueNAS Scale API."""

    def __init__(self, config: Dict[str, Any], auth_manager: AuthManager):
        """Initialize the TrueNAS client.
        
        Args:
            config: Configuration dictionary
            auth_manager: Authentication manager instance
        """
        self.config = TrueNASConfig(**config)
        self.auth_manager = auth_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Establish connection to TrueNAS."""
        if self.session is None:
            connector = aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)
            
            # Authenticate if needed
            if not self.config.api_key:
                await self._authenticate()
    
    async def disconnect(self) -> None:
        """Close connection to TrueNAS."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _authenticate(self) -> None:
        """Authenticate with TrueNAS using username/password."""
        if not self.config.username or not self.config.password:
            raise ValueError("Username and password required for authentication")
        
        auth_url = urljoin(self.config.base_url, "auth/generate_token")
        auth_data = {
            "username": self.config.username,
            "password": self.config.password
        }
        
        try:
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self._auth_token = result.get("token")
                    if not self._auth_token:
                        raise ValueError("No token received from authentication")
                else:
                    raise ValueError(f"Authentication failed: {response.status}")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the TrueNAS API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request data for POST/PUT requests
            params: Query parameters
            
        Returns:
            API response data
        """
        if self.session is None:
            await self.connect()
        
        url = urljoin(self.config.base_url, endpoint)
        headers = self._get_headers()
        
        try:
            async with self.session.request(
                method, url, json=data, params=params, headers=headers
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise ValueError(f"API request failed: {response.status} - {error_text}")
                
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    # System Information Methods
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        return await self._make_request("GET", "system/info")
    
    async def get_version(self) -> Dict[str, Any]:
        """Get TrueNAS version information."""
        return await self._make_request("GET", "system/version")
    
    async def get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        return await self._make_request("GET", "system/health")
    
    async def get_uptime(self) -> Dict[str, Any]:
        """Get system uptime information."""
        return await self._make_request("GET", "system/uptime")
    
    # Storage Methods
    
    async def get_pools(self) -> List[Dict[str, Any]]:
        """Get all storage pools."""
        return await self._make_request("GET", "pool")
    
    async def get_pool(self, pool_id: str) -> Dict[str, Any]:
        """Get specific storage pool by ID.
        
        Args:
            pool_id: Pool identifier
            
        Raises:
            ValueError: If pool_id is invalid or contains path traversal characters
        """
        if not validate_id(pool_id):
            raise ValueError(f"Invalid pool_id: {pool_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("GET", f"pool/id/{pool_id}")
    
    async def create_pool(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new storage pool."""
        return await self._make_request("POST", "pool", data=pool_data)
    
    async def delete_pool(self, pool_id: str) -> Dict[str, Any]:
        """Delete a storage pool.
        
        Args:
            pool_id: Pool identifier
            
        Raises:
            ValueError: If pool_id is invalid or contains path traversal characters
        """
        if not validate_id(pool_id):
            raise ValueError(f"Invalid pool_id: {pool_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("DELETE", f"pool/id/{pool_id}")
    
    async def get_datasets(self, pool_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get datasets, optionally filtered by pool.
        
        Args:
            pool_id: Optional pool identifier to filter datasets
            
        Raises:
            ValueError: If pool_id is provided but invalid
        """
        endpoint = "pool/dataset"
        params = None
        if pool_id:
            if not validate_id(pool_id):
                raise ValueError(f"Invalid pool_id: {pool_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
            params = {"pool": pool_id}
        return await self._make_request("GET", endpoint, params=params)
    
    async def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dataset."""
        return await self._make_request("POST", "pool/dataset", data=dataset_data)
    
    async def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Delete a dataset.
        
        Args:
            dataset_id: Dataset identifier (can include hierarchy like pool/dataset)
            
        Raises:
            ValueError: If dataset_id is invalid or contains path traversal sequences
        """
        if not validate_dataset_name(dataset_id):
            raise ValueError(f"Invalid dataset_id: {dataset_id}. Must not contain path traversal sequences.")
        return await self._make_request("DELETE", f"pool/dataset/id/{dataset_id}")
    
    # Network Methods
    
    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interfaces."""
        return await self._make_request("GET", "network/interface")
    
    async def get_interface(self, interface_id: str) -> Dict[str, Any]:
        """Get specific network interface.
        
        Args:
            interface_id: Interface identifier
            
        Raises:
            ValueError: If interface_id is invalid
        """
        if not validate_id(interface_id):
            raise ValueError(f"Invalid interface_id: {interface_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("GET", f"network/interface/id/{interface_id}")
    
    async def update_interface(self, interface_id: str, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update network interface configuration.
        
        Args:
            interface_id: Interface identifier
            interface_data: Interface configuration data
            
        Raises:
            ValueError: If interface_id is invalid
        """
        if not validate_id(interface_id):
            raise ValueError(f"Invalid interface_id: {interface_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("PUT", f"network/interface/id/{interface_id}", data=interface_data)
    
    async def get_routes(self) -> List[Dict[str, Any]]:
        """Get network routes."""
        return await self._make_request("GET", "network/route")
    
    # Services Methods
    
    async def get_services(self) -> List[Dict[str, Any]]:
        """Get all services."""
        return await self._make_request("GET", "service")
    
    async def get_service(self, service_id: str) -> Dict[str, Any]:
        """Get specific service.
        
        Args:
            service_id: Service identifier
            
        Raises:
            ValueError: If service_id is invalid
        """
        if not validate_id(service_id):
            raise ValueError(f"Invalid service_id: {service_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("GET", f"service/id/{service_id}")
    
    async def start_service(self, service_id: str) -> Dict[str, Any]:
        """Start a service.
        
        Args:
            service_id: Service identifier
            
        Raises:
            ValueError: If service_id is invalid
        """
        if not validate_id(service_id):
            raise ValueError(f"Invalid service_id: {service_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("POST", f"service/id/{service_id}/start")
    
    async def stop_service(self, service_id: str) -> Dict[str, Any]:
        """Stop a service.
        
        Args:
            service_id: Service identifier
            
        Raises:
            ValueError: If service_id is invalid
        """
        if not validate_id(service_id):
            raise ValueError(f"Invalid service_id: {service_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("POST", f"service/id/{service_id}/stop")
    
    async def restart_service(self, service_id: str) -> Dict[str, Any]:
        """Restart a service.
        
        Args:
            service_id: Service identifier
            
        Raises:
            ValueError: If service_id is invalid
        """
        if not validate_id(service_id):
            raise ValueError(f"Invalid service_id: {service_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("POST", f"service/id/{service_id}/restart")
    
    # User Management Methods
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        return await self._make_request("GET", "user")
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get specific user.
        
        Args:
            user_id: User identifier
            
        Raises:
            ValueError: If user_id is invalid
        """
        if not validate_id(user_id):
            raise ValueError(f"Invalid user_id: {user_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("GET", f"user/id/{user_id}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        return await self._make_request("POST", "user", data=user_data)
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information.
        
        Args:
            user_id: User identifier
            user_data: User configuration data
            
        Raises:
            ValueError: If user_id is invalid
        """
        if not validate_id(user_id):
            raise ValueError(f"Invalid user_id: {user_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("PUT", f"user/id/{user_id}", data=user_data)
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user.
        
        Args:
            user_id: User identifier
            
        Raises:
            ValueError: If user_id is invalid
        """
        if not validate_id(user_id):
            raise ValueError(f"Invalid user_id: {user_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("DELETE", f"user/id/{user_id}")
    
    async def get_groups(self) -> List[Dict[str, Any]]:
        """Get all groups."""
        return await self._make_request("GET", "group")
    
    # Monitoring Methods
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return await self._make_request("GET", "system/stats")
    
    async def get_alert_list(self) -> List[Dict[str, Any]]:
        """Get system alerts."""
        return await self._make_request("GET", "alert/list")
    
    async def get_alert_classes(self) -> List[Dict[str, Any]]:
        """Get alert classes."""
        return await self._make_request("GET", "alert/list/classes")
    
    # Backup and Replication Methods
    
    async def get_replication_tasks(self) -> List[Dict[str, Any]]:
        """Get replication tasks."""
        return await self._make_request("GET", "replication")
    
    async def create_replication_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new replication task."""
        return await self._make_request("POST", "replication", data=task_data)
    
    async def get_snapshots(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get snapshots, optionally filtered by dataset.
        
        Args:
            dataset_id: Optional dataset identifier to filter snapshots
            
        Raises:
            ValueError: If dataset_id is provided but invalid
        """
        endpoint = "zfs/snapshot"
        params = None
        if dataset_id:
            if not validate_dataset_name(dataset_id):
                raise ValueError(f"Invalid dataset_id: {dataset_id}. Must not contain path traversal sequences.")
            params = {"dataset": dataset_id}
        return await self._make_request("GET", endpoint, params=params)
    
    async def create_snapshot(self, snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new snapshot."""
        return await self._make_request("POST", "zfs/snapshot", data=snapshot_data)
    
    async def delete_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Delete a snapshot.
        
        Args:
            snapshot_id: Snapshot identifier (can include hierarchy)
            
        Raises:
            ValueError: If snapshot_id is invalid
        """
        if not validate_dataset_name(snapshot_id):
            raise ValueError(f"Invalid snapshot_id: {snapshot_id}. Must not contain path traversal sequences.")
        return await self._make_request("DELETE", f"zfs/snapshot/id/{snapshot_id}")
    
    # Docker/Kubernetes Methods (for TrueNAS Scale)
    
    async def get_applications(self) -> List[Dict[str, Any]]:
        """Get installed applications (Docker/Kubernetes)."""
        return await self._make_request("GET", "app")
    
    async def get_application(self, app_id: str) -> Dict[str, Any]:
        """Get specific application.
        
        Args:
            app_id: Application identifier
            
        Raises:
            ValueError: If app_id is invalid
        """
        if not validate_id(app_id):
            raise ValueError(f"Invalid app_id: {app_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("GET", f"app/id/{app_id}")
    
    async def install_application(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Install a new application."""
        return await self._make_request("POST", "app", data=app_data)
    
    async def uninstall_application(self, app_id: str) -> Dict[str, Any]:
        """Uninstall an application.
        
        Args:
            app_id: Application identifier
            
        Raises:
            ValueError: If app_id is invalid
        """
        if not validate_id(app_id):
            raise ValueError(f"Invalid app_id: {app_id}. Must be alphanumeric with dots, hyphens, or underscores only.")
        return await self._make_request("DELETE", f"app/id/{app_id}")
    
    # Utility Methods
    
    async def test_connection(self) -> bool:
        """Test connection to TrueNAS."""
        try:
            await self.get_system_info()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_api_docs(self) -> Dict[str, Any]:
        """Get API documentation."""
        return await self._make_request("GET", "docs")
