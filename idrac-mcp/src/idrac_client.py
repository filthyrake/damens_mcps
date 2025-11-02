"""iDRAC client for interacting with Dell PowerEdge servers."""

import asyncio
import json
import ssl
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import aiohttp
import requests
from requests.auth import HTTPBasicAuth

# Try relative imports first, fall back to absolute
try:
    from .utils.logging import get_logger
    from .utils.validation import validate_idrac_config, validate_power_operation, validate_user_config
    from .utils.resilience import create_circuit_breaker, create_retry_decorator, call_with_circuit_breaker_async
except ImportError:
    # Fallback for direct execution
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        "Resilience utilities not available - retry logic and circuit breaker disabled. "
        "Install dependencies: pip install tenacity pybreaker"
    )
    
    def validate_idrac_config(config):
        """Basic config validation."""
        required_keys = ['host', 'port', 'protocol', 'username', 'password']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
        return config
    
    def validate_power_operation(operation):
        """Basic power operation validation."""
        return operation
    
    def validate_user_config(config):
        """Basic user config validation."""
        return config
    
    def create_circuit_breaker(**kwargs):
        """Stub for circuit breaker - resilience features disabled."""
        logger.warning(
            "create_circuit_breaker called, but resilience features are disabled. "
            "Install tenacity and pybreaker for full functionality."
        )
        return None
    
    def create_retry_decorator(**kwargs):
        """Stub for retry decorator - resilience features disabled."""
        def decorator(func):
            logger.warning(
                "create_retry_decorator called, but resilience features are disabled. "
                "Install tenacity and pybreaker for full functionality."
            )
            return func
        return decorator
    
    async def call_with_circuit_breaker_async(circuit_breaker, func, *args, **kwargs):
        """Stub for async circuit breaker - resilience features disabled."""
        logger.warning(
            "call_with_circuit_breaker_async called, but resilience features are disabled. "
            "Install tenacity and pybreaker for full functionality."
        )
        return await func(*args, **kwargs)

# Initialize logger
try:
    logger = get_logger(__name__)
except NameError:
    logger = logging.getLogger(__name__)


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
        
        # Timeout configuration (seconds)
        self.timeout = aiohttp.ClientTimeout(total=config.get('timeout', 30))
        
        # Connection pooling configuration
        self.connector_limit = config.get('connector_limit', 100)
        self.connector_limit_per_host = config.get('connector_limit_per_host', 30)
        
        # Retry configuration
        self.retry_max_attempts = config.get('retry_max_attempts', 3)
        self.retry_min_wait = config.get('retry_min_wait', 1)
        self.retry_max_wait = config.get('retry_max_wait', 10)
        
        # Circuit breaker configuration
        self.circuit_breaker_enabled = config.get('circuit_breaker_enabled', True)
        self.circuit_breaker = None
        if self.circuit_breaker_enabled:
            self.circuit_breaker = create_circuit_breaker(
                fail_max=config.get('circuit_breaker_fail_max', 5),
                timeout_duration=config.get('circuit_breaker_timeout', 60),
                name=f"idrac_{self.config['host']}"
            )
        
        # Create retry decorator
        retry_decorator = create_retry_decorator(
            max_attempts=self.retry_max_attempts,
            min_wait=self.retry_min_wait,
            max_wait=self.retry_max_wait,
            retry_exceptions=(
                ConnectionError,
                TimeoutError,
                aiohttp.ClientError,
                aiohttp.ServerTimeoutError,
                aiohttp.ClientConnectorError,
            )
        )
        # Apply decorator once during initialization for efficiency
        self._retried_execute_request = retry_decorator(self._execute_request)
    
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
            # Create connector with connection pooling
            connector = aiohttp.TCPConnector(
                ssl=self.config['ssl_verify'],
                limit=self.connector_limit,
                limit_per_host=self.connector_limit_per_host,
                ttl_dns_cache=300
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                auth=aiohttp.BasicAuth(self.config['username'], self.config['password']),
                headers=self._headers,
                timeout=self.timeout
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
    
    async def _execute_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the actual HTTP request (internal method with retry logic).
        
        This method is decorated with retry logic and should not be called directly.
        Use _make_request instead.
        
        Args:
            method: HTTP method
            url: Full URL
            data: Request data
            
        Returns:
            Response data
            
        Raises:
            Exception: If request fails
        """
        try:
            async with self.session.request(method, url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"iDRAC API request failed: {e}")
            raise Exception(f"API request failed: {e}")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to iDRAC API with retry logic and circuit breaker.
        
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
        
        # Use pre-decorated request execution (applied once in __init__)
        retried_request = self._retried_execute_request
        
        # Apply circuit breaker if enabled
        if self.circuit_breaker_enabled and self.circuit_breaker:
            result = await call_with_circuit_breaker_async(
                self.circuit_breaker, retried_request, method, url, data
            )
        else:
            result = await retried_request(method, url, data)
        
        return result
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            System information dictionary
        """
        try:
            result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            
            # Extract actual fields from Redfish response
            system_info = {
                "model": result.get('Model', 'N/A'),
                "manufacturer": result.get('Manufacturer', 'N/A'),
                "serial_number": result.get('SerialNumber', 'N/A'),
                "part_number": result.get('PartNumber', 'N/A'),
                "sku": result.get('SKU', 'N/A'),
                "system_type": result.get('SystemType', 'N/A'),
                "bios_version": result.get('BiosVersion', 'N/A'),
                "power_state": result.get('PowerState', 'N/A'),
                "health": result.get('Status', {}).get('Health', 'N/A'),
                "state": result.get('Status', {}).get('State', 'N/A'),
                "hostname": result.get('HostName', 'N/A'),
                "description": result.get('Description', 'N/A')
            }
            
            return {
                "status": "success",
                "data": system_info,
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
            # Get processor information
            processors_result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Processors')
            processors = processors_result.get('Members', [])
            
            # Get memory information
            memory_result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Memory')
            memory_modules = memory_result.get('Members', [])
            
            # Get storage information
            storage_result = await self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Storage')
            storage_controllers = storage_result.get('Members', [])
            
            # Get detailed processor info
            processor_details = []
            for proc in processors:
                try:
                    proc_id = proc.get('@odata.id', '').split('/')[-1]
                    proc_detail = await self._make_request('GET', f'/redfish/v1/Systems/System.Embedded.1/Processors/{proc_id}')
                    processor_details.append({
                        "id": proc_id,
                        "name": proc_detail.get('Name', 'Unknown'),
                        "model": proc_detail.get('Model', 'N/A'),
                        "manufacturer": proc_detail.get('Manufacturer', 'N/A'),
                        "architecture": proc_detail.get('ProcessorArchitecture', 'N/A'),
                        "cores": proc_detail.get('TotalCores', 'N/A'),
                        "threads": proc_detail.get('TotalThreads', 'N/A'),
                        "health": proc_detail.get('Status', {}).get('Health', 'N/A'),
                        "state": proc_detail.get('Status', {}).get('State', 'N/A')
                    })
                except Exception as e:
                    logger.warning(f"Failed to get processor details for {proc.get('@odata.id', 'unknown')}: {e}")
                    processor_details.append({"id": proc.get('@odata.id', 'unknown'), "error": str(e)})
            
            inventory = {
                "processors": {
                    "count": len(processors),
                    "details": processor_details
                },
                "memory_modules": {
                    "count": len(memory_modules),
                    "modules": memory_modules
                },
                "storage_controllers": {
                    "count": len(storage_controllers),
                    "controllers": storage_controllers
                }
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
            
            temperatures = result.get('Temperatures', [])
            fans = result.get('Fans', [])
            
            # Extract temperature data
            temp_data = []
            for temp in temperatures:
                temp_data.append({
                    "name": temp.get('Name', 'Unknown'),
                    "reading_celsius": temp.get('ReadingCelsius', 'N/A'),
                    "health": temp.get('Status', {}).get('Health', 'N/A'),
                    "state": temp.get('Status', {}).get('State', 'N/A'),
                    "upper_critical": temp.get('UpperThresholdCritical', 'N/A'),
                    "upper_warning": temp.get('UpperThresholdNonCritical', 'N/A')
                })
            
            # Extract fan data
            fan_data = []
            for fan in fans:
                fan_data.append({
                    "name": fan.get('Name', 'Unknown'),
                    "reading_rpm": fan.get('Reading', 'N/A'),
                    "health": fan.get('Status', {}).get('Health', 'N/A'),
                    "state": fan.get('Status', {}).get('State', 'N/A'),
                    "min_rpm": fan.get('MinReadingRange', 'N/A'),
                    "max_rpm": fan.get('MaxReadingRange', 'N/A')
                })
            
            thermal_info = {
                "temperatures": {
                    "count": len(temperatures),
                    "sensors": temp_data
                },
                "fans": {
                    "count": len(fans),
                    "fans": fan_data
                }
            }
            
            return {
                "status": "success",
                "data": thermal_info,
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
