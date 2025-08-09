"""iDRAC client for interacting with Dell PowerEdge servers."""

import asyncio
import json
import ssl
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import aiohttp
import requests
from requests.auth import HTTPBasicAuth

from .utils.logging import get_logger
from .utils.validation import validate_idrac_config, validate_power_operation, validate_user_config

logger = get_logger(__name__)


class IDracClient:
    """Client for interacting with iDRAC REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the iDRAC client.
        
        Args:
            config: iDRAC configuration dictionary
        """
        self.config = validate_idrac_config(config)
        self.base_url = f"{self.config['protocol']}://{self.config['host']}:{self.config['port']}"
        self.auth = HTTPBasicAuth(self.config['username'], self.config['password'])
        self.session = None
        self._headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Establish connection to iDRAC."""
        try:
            connector = aiohttp.TCPConnector(ssl=self.config['ssl_verify'])
            self.session = aiohttp.ClientSession(
                connector=connector,
                auth=aiohttp.BasicAuth(self.config['username'], self.config['password']),
                headers=self._headers
            )
            logger.info(f"Connected to iDRAC at {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to connect to iDRAC: {e}")
            raise
    
    async def disconnect(self):
        """Close connection to iDRAC."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from iDRAC")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to iDRAC API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data
            
        Raises:
            Exception: If request fails
        """
        if not self.session:
            await self.connect()
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            async with self.session.request(method, url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"iDRAC API request failed: {e}")
            raise Exception(f"API request failed: {e}")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            System information dictionary
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            return {
                "status": "success",
                "data": result,
                "message": "System information retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            raise
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status.
        
        Returns:
            System health information
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            health = result.get('Status', {})
            return {
                "status": "success",
                "data": {
                    "health": health.get('Health'),
                    "state": health.get('State'),
                    "overall_health": "OK" if health.get('Health') == 'OK' else "Warning"
                },
                "message": "System health retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            raise
    
    async def get_hardware_inventory(self) -> Dict[str, Any]:
        """Get hardware inventory.
        
        Returns:
            Hardware inventory information
        """
        try:
            # Get system information
            system_info = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            
            # Get processor information
            processors = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Processors')
            
            # Get memory information
            memory = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Memory')
            
            # Get storage information
            storage = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Storage')
            
            inventory = {
                "system": system_info,
                "processors": processors,
                "memory": memory,
                "storage": storage
            }
            
            return {
                "status": "success",
                "data": inventory,
                "message": "Hardware inventory retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get hardware inventory: {e}")
            raise
    
    async def get_power_status(self) -> Dict[str, Any]:
        """Get power status.
        
        Returns:
            Power status information
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            power_state = result.get('PowerState', 'Unknown')
            
            return {
                "status": "success",
                "data": {
                    "power_state": power_state,
                    "is_on": power_state == 'On',
                    "is_off": power_state == 'Off'
                },
                "message": "Power status retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get power status: {e}")
            raise
    
    async def power_on(self) -> Dict[str, Any]:
        """Power on the server.
        
        Returns:
            Operation result
        """
        try:
            data = {"ResetType": "On"}
            result = await self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', data)
            
            return {
                "status": "success",
                "data": result,
                "message": "Power on command sent successfully"
            }
        except Exception as e:
            logger.error(f"Failed to power on server: {e}")
            raise
    
    async def power_off(self, force: bool = False) -> Dict[str, Any]:
        """Power off the server.
        
        Args:
            force: Force power off
            
        Returns:
            Operation result
        """
        try:
            reset_type = "ForceOff" if force else "GracefulShutdown"
            data = {"ResetType": reset_type}
            result = await self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', data)
            
            return {
                "status": "success",
                "data": result,
                "message": f"Power off command ({reset_type}) sent successfully"
            }
        except Exception as e:
            logger.error(f"Failed to power off server: {e}")
            raise
    
    async def power_cycle(self, force: bool = False) -> Dict[str, Any]:
        """Power cycle the server.
        
        Args:
            force: Force power cycle
            
        Returns:
            Operation result
        """
        try:
            reset_type = "ForceRestart" if force else "GracefulRestart"
            data = {"ResetType": reset_type}
            result = await self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', data)
            
            return {
                "status": "success",
                "data": result,
                "message": f"Power cycle command ({reset_type}) sent successfully"
            }
        except Exception as e:
            logger.error(f"Failed to power cycle server: {e}")
            raise
    
    async def get_thermal_status(self) -> Dict[str, Any]:
        """Get thermal status.
        
        Returns:
            Thermal status information
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1/Thermal')
            
            return {
                "status": "success",
                "data": result,
                "message": "Thermal status retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get thermal status: {e}")
            raise
    
    async def get_users(self) -> Dict[str, Any]:
        """Get iDRAC users.
        
        Returns:
            List of users
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Managers/iDRAC.Embedded.1/Accounts')
            
            return {
                "status": "success",
                "data": result,
                "message": "Users retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise
    
    async def create_user(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new iDRAC user.
        
        Args:
            user_config: User configuration
            
        Returns:
            Operation result
        """
        try:
            validated_config = validate_user_config(user_config)
            result = await self._make_request('POST', '/redfish/v1/Managers/iDRAC.Embedded.1/Accounts', validated_config)
            
            return {
                "status": "success",
                "data": result,
                "message": f"User {validated_config['username']} created successfully"
            }
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration.
        
        Returns:
            Network configuration
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Managers/iDRAC.Embedded.1/EthernetInterfaces')
            
            return {
                "status": "success",
                "data": result,
                "message": "Network configuration retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get network config: {e}")
            raise
    
    async def get_storage_controllers(self) -> Dict[str, Any]:
        """Get storage controllers.
        
        Returns:
            Storage controllers information
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Storage')
            
            return {
                "status": "success",
                "data": result,
                "message": "Storage controllers retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get storage controllers: {e}")
            raise
    
    async def get_firmware_versions(self) -> Dict[str, Any]:
        """Get firmware versions.
        
        Returns:
            Firmware version information
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/UpdateService/FirmwareInventory')
            
            return {
                "status": "success",
                "data": result,
                "message": "Firmware versions retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get firmware versions: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to iDRAC.
        
        Returns:
            Connection test result
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/')
            
            return {
                "status": "success",
                "data": {
                    "connected": True,
                    "version": result.get('RedfishVersion', 'Unknown'),
                    "protocol_version": result.get('ProtocolFeaturesSupported', {})
                },
                "message": "Connection test successful"
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "error",
                "data": {
                    "connected": False,
                    "error": str(e)
                },
                "message": "Connection test failed"
            }
