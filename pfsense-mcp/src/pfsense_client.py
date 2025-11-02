"""
pfSense API Client for MCP Server.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlencode

import aiohttp
from aiohttp import ClientSession

try:
    from .auth import PfSenseAuth, PfSenseAuthError
    from .utils.logging import get_logger
    from .utils.validation import validate_config, validate_ip_address
    from .utils.resilience import create_circuit_breaker, create_retry_decorator, call_with_circuit_breaker_async
    from .exceptions import (
        PfSenseAPIError,
        PfSenseConnectionError,
        PfSenseTimeoutError,
        PfSenseConfigurationError
    )
except ImportError:
    # Fallback for direct execution
    from auth import PfSenseAuth, PfSenseAuthError
    from utils.logging import get_logger
    from utils.validation import validate_config, validate_ip_address
    from utils.resilience import create_circuit_breaker, create_retry_decorator, call_with_circuit_breaker_async
    from exceptions import (
        PfSenseAPIError,
        PfSenseConnectionError,
        PfSenseTimeoutError,
        PfSenseConfigurationError
    )

logger = get_logger(__name__)

# JWT token configuration constants
DEFAULT_JWT_TOKEN_LIFETIME = 3600  # seconds (1 hour)
DEFAULT_JWT_TOKEN_REFRESH_BUFFER = 300  # seconds (5 minutes)
MAX_JWT_REFRESH_RETRIES = 3


class HTTPPfSenseClient:
    """
    HTTP client for pfSense REST API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the pfSense client.
        
        Args:
            config: Configuration dictionary
        """
        # Validate configuration
        errors = validate_config(config)
        if errors:
            raise PfSenseConfigurationError(f"Configuration errors: {', '.join(errors)}")
        
        self.auth = PfSenseAuth(config)
        self.session: Optional[ClientSession] = None
        self.base_url = self.auth.get_base_url()
        self.jwt_token: Optional[str] = None
        self.jwt_token_expiry: Optional[float] = None
        # JWT token lifetime - configurable, defaults to DEFAULT_JWT_TOKEN_LIFETIME
        # Can be overridden via config if pfSense uses different expiry
        self.jwt_token_lifetime = int(config.get("jwt_token_lifetime", DEFAULT_JWT_TOKEN_LIFETIME))
        self.jwt_token_refresh_buffer = int(config.get("jwt_token_refresh_buffer", DEFAULT_JWT_TOKEN_REFRESH_BUFFER))
        
        # Timeout configuration (seconds, accepts float for sub-second precision)
        self.timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
        
        # Connection pooling configuration
        self.connector_limit = int(config.get("connector_limit", 100))
        self.connector_limit_per_host = int(config.get("connector_limit_per_host", 30))
        
        # Retry configuration
        self.retry_max_attempts = int(config.get("retry_max_attempts", 3))
        self.retry_min_wait = float(config.get("retry_min_wait", 1.0))
        self.retry_max_wait = float(config.get("retry_max_wait", 10.0))
        
        # Circuit breaker configuration
        self.circuit_breaker_enabled = config.get("circuit_breaker_enabled", True)
        self.circuit_breaker = None
        if self.circuit_breaker_enabled:
            self.circuit_breaker = create_circuit_breaker(
                fail_max=int(config.get("circuit_breaker_fail_max", 5)),
                timeout_duration=int(config.get("circuit_breaker_timeout", 60)),
                name="pfsense_api"
            )
        
        # Create retry decorator
        retry_decorator = create_retry_decorator(
            max_attempts=self.retry_max_attempts,
            min_wait=self.retry_min_wait,
            max_wait=self.retry_max_wait,
            retry_exceptions=(
                PfSenseConnectionError,
                PfSenseTimeoutError,
                aiohttp.ClientError,
                aiohttp.ServerTimeoutError,
                aiohttp.ClientConnectorError,
            )
        )
        # Apply decorator once during initialization for efficiency
        self._retried_execute_request = retry_decorator(self._execute_request)
    
    def _token_expired(self) -> bool:
        """
        Check if the JWT token has expired or will expire soon.
        
        Returns:
            True if token is expired or will expire within refresh buffer
        """
        if self.jwt_token_expiry is None:
            return True
        
        current_time = time.time()
        # Refresh if within buffer period of expiration
        return current_time >= (self.jwt_token_expiry - self.jwt_token_refresh_buffer)
    
    async def _ensure_valid_token(self) -> None:
        """
        Ensure we have a valid JWT token, refreshing if necessary.
        
        Implements retry logic with exponential backoff for transient failures.
        Falls back to basic authentication if token acquisition fails after all retries.
        """
        # If we have API key auth, no need for JWT token
        if self.auth.api_key:
            return
        
        # If we don't have username/password, can't get JWT token
        if not (self.auth.username and self.auth.password):
            return
        
        # Check if token is valid and not expired
        if self.jwt_token and not self._token_expired():
            # Token is still valid, no need to refresh
            return
        
        # Token is missing or expired, clear it for refresh
        if self.jwt_token:
            logger.info("JWT token expired, refreshing...")
        self.jwt_token = None
        self.jwt_token_expiry = None
        
        # Retry logic with exponential backoff
        max_retries = MAX_JWT_REFRESH_RETRIES
        for attempt in range(max_retries):
            try:
                self.jwt_token = await self.auth.get_jwt_token()
                self.jwt_token_expiry = time.time() + self.jwt_token_lifetime
                logger.info(f"JWT token acquired successfully (expires in {self.jwt_token_lifetime}s)")
                return
            except (PfSenseAuthError, aiohttp.ClientError) as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, fall back to basic auth
                    logger.warning(f"JWT token acquisition failed after {max_retries} attempts, using fallback auth: {e}")
                    return
                
                # Calculate backoff delay: 2^attempt seconds
                backoff_delay = 2 ** attempt
                logger.warning(f"JWT token acquisition attempt {attempt + 1}/{max_retries} failed: {e}, retrying in {backoff_delay}s...")
                await asyncio.sleep(backoff_delay)
    
    async def _execute_request(
        self, 
        method: str, 
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the actual HTTP request (internal method with retry logic).
        
        This method is decorated with retry logic and should not be called directly.
        Use _make_request instead.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL
            headers: Request headers
            data: Request body data
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            PfSenseAPIError: If the request fails
            PfSenseConnectionError: If connection fails
            PfSenseTimeoutError: If request times out
        """
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                params=params,
                allow_redirects=False,
                timeout=self.timeout
            ) as response:
                response_text = await response.text()
                
                if response.status >= 400:
                    # Check if we got redirected to login page
                    if response.status in [301, 302, 303, 307, 308]:
                        raise PfSenseAPIError(f"Redirected to login page - authentication failed (URL: {url})")
                    elif 'text/html' in response.headers.get('content-type', '') and 'login' in response_text.lower():
                        raise PfSenseAPIError(f"Received login page instead of API response - check authentication (URL: {url})")
                    else:
                        raise PfSenseAPIError(f"API request failed: {response.status} - {response_text} (URL: {url})")
                
                if response_text:
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        return {"raw_response": response_text}
                else:
                    return {}
                    
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error to pfSense: {e}", exc_info=True)
            raise PfSenseConnectionError(f"Failed to connect to pfSense: {str(e)}") from e
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error from pfSense: {e}", exc_info=True)
            raise PfSenseAPIError(f"API HTTP error: {str(e)}") from e
        except aiohttp.ServerTimeoutError as e:
            logger.error(f"Request timeout to pfSense: {e}", exc_info=True)
            raise PfSenseTimeoutError(f"Request timed out: {str(e)}") from e
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with pfSense: {e}", exc_info=True)
            raise PfSenseConnectionError(f"Network error: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}", exc_info=True)
            raise PfSenseAPIError(f"Invalid JSON response: {str(e)}") from e
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the pfSense API with retry logic and circuit breaker.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            PfSenseAPIError: If the request fails
            PfSenseConnectionError: If connection fails
            PfSenseTimeoutError: If request times out
        """
        if not self.session:
            # Create session with connection pooling and proper SSL configuration
            # Use auth manager's SSL context for proper certificate handling
            import ssl
            ssl_context = None
            if self.auth.protocol == "https":
                ssl_context = ssl.create_default_context()
                if not self.auth.ssl_verify:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=self.connector_limit,
                limit_per_host=self.connector_limit_per_host,
                ttl_dns_cache=300
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        
        # Ensure we have a valid JWT token (if applicable)
        await self._ensure_valid_token()
        
        url = urljoin(self.base_url, endpoint)
        
        # Use JWT headers if we have a token, otherwise use original auth
        if self.jwt_token:
            headers = self.auth.get_jwt_headers(self.jwt_token)
        else:
            headers = self.auth.get_auth_headers()
        
        # Use pre-decorated request execution (applied once in __init__)
        retried_request = self._retried_execute_request
        
        # Apply circuit breaker if enabled
        if self.circuit_breaker_enabled and self.circuit_breaker:
            result = await call_with_circuit_breaker_async(
                self.circuit_breaker, retried_request, method, url, headers, data, params
            )
        else:
            result = await retried_request(method, url, headers, data, params)
        
        return result
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        # Use working pfSense 2.8.0 API v2 endpoints
        try:
            # Get system version and status (we know these work)
            version_info = await self._make_request("GET", "/api/v2/system/version")
            status_info = await self._make_request("GET", "/api/v2/status/system")
            
            # Combine the information
            return {
                "version": version_info.get("data", {}).get("version", "Unknown"),
                "status": status_info.get("data", {}),
                "api_status": "Connected"
            }
        except (PfSenseConnectionError, PfSenseTimeoutError) as e:
            logger.error(f"Failed to get system info: {e}", exc_info=True)
            raise
        except PfSenseAPIError as e:
            logger.error(f"API error getting system info: {e}", exc_info=True)
            raise
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        # Use working pfSense 2.8.0 API v2 endpoints
        try:
            # Get system status and service status (we know these work)
            system_status = await self._make_request("GET", "/api/v2/status/system")
            service_status = await self._make_request("GET", "/api/v2/status/services")
            
            return {
                "status": "Online",
                "system": system_status.get("data", {}),
                "services": service_status.get("data", []),
                "note": "System is responding to API calls"
            }
        except (PfSenseConnectionError, PfSenseTimeoutError) as e:
            logger.error(f"Failed to get system health: {e}", exc_info=True)
            raise
        except PfSenseAPIError as e:
            logger.error(f"API error getting system health: {e}", exc_info=True)
            raise
    
    async def get_interfaces(self) -> Dict[str, Any]:
        """Get network interfaces information."""
        try:
            # Get interfaces and interface status (we know these work)
            interfaces = await self._make_request("GET", "/api/v2/interfaces")
            interface_status = await self._make_request("GET", "/api/v2/status/interfaces")
            
            return {
                "interfaces": interfaces.get("data", []),
                "status": interface_status.get("data", []),
                "note": "Combined interface configuration and status"
            }
        except (PfSenseConnectionError, PfSenseTimeoutError) as e:
            logger.error(f"Failed to get interfaces: {e}", exc_info=True)
            raise
        except PfSenseAPIError as e:
            logger.error(f"API error getting interfaces: {e}", exc_info=True)
            raise
    
    async def get_services(self) -> Dict[str, Any]:
        """Get running services information."""
        try:
            # Get service status (we know this works)
            return await self._make_request("GET", "/api/v2/status/services")
        except (PfSenseConnectionError, PfSenseTimeoutError) as e:
            logger.error(f"Failed to get services: {e}", exc_info=True)
            raise
        except PfSenseAPIError as e:
            logger.error(f"API error getting services: {e}", exc_info=True)
            raise
    
    async def get_firewall_rules(self) -> Dict[str, Any]:
        """Get firewall rules and aliases."""
        try:
            # Get firewall aliases (we know this works)
            aliases = await self._make_request("GET", "/api/v2/firewall/aliases")
            
            return {
                "aliases": aliases.get("data", []),
                "note": "Firewall aliases retrieved successfully. Rules may be available via additional endpoints."
            }
        except (PfSenseConnectionError, PfSenseTimeoutError) as e:
            logger.error(f"Failed to get firewall rules: {e}", exc_info=True)
            raise
        except PfSenseAPIError as e:
            logger.error(f"API error getting firewall rules: {e}", exc_info=True)
            raise
    
    async def get_firewall_aliases(self) -> Dict[str, Any]:
        """Get firewall aliases configuration."""
        return await self._make_request("GET", "/api/v2/firewall/aliases")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status information."""
        return await self._make_request("GET", "/api/v2/status/services")
    
    async def get_interface_status(self) -> Dict[str, Any]:
        """Get detailed interface status information."""
        return await self._make_request("GET", "/api/v2/status/interfaces")
    
    async def get_nat_outbound_mappings(self) -> Dict[str, Any]:
        """Get NAT outbound mappings."""
        return await self._make_request("GET", "/api/v2/firewall/nat/outbound/mappings")
    
    async def get_nat_port_forwarding(self) -> Dict[str, Any]:
        """Get NAT port forwarding rules."""
        return await self._make_request("GET", "/api/v2/firewall/nat/port_forward")
    
    async def get_nat_one_to_one_mappings(self) -> Dict[str, Any]:
        """Get NAT one-to-one mappings."""
        return await self._make_request("GET", "/api/v2/firewall/nat/one_to_one/mappings")
    
    async def get_firewall_schedules(self) -> Dict[str, Any]:
        """Get firewall schedules."""
        return await self._make_request("GET", "/api/v2/firewall/schedules")
    
    async def get_firewall_states(self) -> Dict[str, Any]:
        """Get firewall states."""
        return await self._make_request("GET", "/api/v2/firewall/states")
    
    async def get_traffic_shaper(self) -> Dict[str, Any]:
        """Get traffic shaper configuration."""
        return await self._make_request("GET", "/api/v2/firewall/traffic_shaper")
    
    async def get_traffic_shapers(self) -> Dict[str, Any]:
        """Get all traffic shapers."""
        return await self._make_request("GET", "/api/v2/firewall/traffic_shapers")
    
    async def get_traffic_shaper_limiters(self) -> Dict[str, Any]:
        """Get traffic shaper limiters."""
        return await self._make_request("GET", "/api/v2/firewall/traffic_shaper/limiters")
    
    async def get_traffic_shaper_queues(self) -> Dict[str, Any]:
        """Get traffic shaper queues."""
        return await self._make_request("GET", "/api/v2/firewall/traffic_shaper/queue")
    
    async def get_virtual_ips(self) -> Dict[str, Any]:
        """Get virtual IP addresses."""
        return await self._make_request("GET", "/api/v2/firewall/virtual_ips")
    
    async def get_virtual_ip(self, interface: str = None) -> Dict[str, Any]:
        """Get specific virtual IP configuration."""
        if interface:
            return await self._make_request("GET", f"/api/v2/firewall/virtual_ip/{interface}")
        else:
            return await self._make_request("GET", "/api/v2/firewall/virtual_ip")
    
    async def apply_virtual_ip_changes(self) -> Dict[str, Any]:
        """Apply virtual IP configuration changes."""
        return await self._make_request("POST", "/api/v2/firewall/virtual_ip/apply")
    
    async def create_firewall_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new firewall rule."""
        return await self._make_request("POST", "/api/v1/firewall/rule", data=rule_data)
    
    async def delete_firewall_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete a firewall rule."""
        return await self._make_request("DELETE", f"/api/v1/firewall/rule/{rule_id}")
    
    async def update_firewall_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a firewall rule."""
        return await self._make_request("PUT", f"/api/v1/firewall/rule/{rule_id}", data=rule_data)
    
    async def get_firewall_logs(self, limit: int = 100) -> Dict[str, Any]:
        """Get firewall logs."""
        params = {"limit": limit}
        return await self._make_request("GET", "/api/v1/firewall/log", params=params)
    
    async def get_vlans(self) -> Dict[str, Any]:
        """Get VLAN configurations."""
        return await self._make_request("GET", "/api/v1/interface/vlan")
    
    async def create_vlan(self, vlan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new VLAN."""
        return await self._make_request("POST", "/api/v1/interface/vlan", data=vlan_data)
    
    async def delete_vlan(self, vlan_id: str) -> Dict[str, Any]:
        """Delete a VLAN."""
        return await self._make_request("DELETE", f"/api/v1/interface/vlan/{vlan_id}")
    
    async def get_dhcp_leases(self) -> Dict[str, Any]:
        """Get DHCP lease information."""
        try:
            # Try different DHCP endpoints for pfSense 2.8.0
            return await self._make_request("GET", "/api/v2/dhcp/leases")
        except PfSenseAPIError:
            # Fallback to DHCP status
            logger.info("Primary DHCP leases endpoint failed, trying DHCP status endpoint")
            return await self._make_request("GET", "/api/v2/dhcp/status")
    
    async def get_dns_servers(self) -> Dict[str, Any]:
        """Get DNS server configuration."""
        return await self._make_request("GET", "/api/v1/system/dns")
    
    async def get_installed_packages(self) -> Dict[str, Any]:
        """Get installed packages."""
        return await self._make_request("GET", "/api/v1/system/package")
    
    async def install_package(self, package_name: str) -> Dict[str, Any]:
        """Install a package."""
        data = {"package": package_name}
        return await self._make_request("POST", "/api/v1/system/package/install", data=data)
    
    async def remove_package(self, package_name: str) -> Dict[str, Any]:
        """Remove a package."""
        data = {"package": package_name}
        return await self._make_request("POST", "/api/v1/system/package/remove", data=data)
    
    async def get_package_updates(self) -> Dict[str, Any]:
        """Check for package updates."""
        return await self._make_request("GET", "/api/v1/system/package/updates")
    
    async def get_arp_table(self) -> Dict[str, Any]:
        """Get ARP table entries."""
        return await self._make_request("GET", "/api/v2/diagnostics/arp_table")
    
    async def clear_arp_table(self) -> Dict[str, Any]:
        """Clear all ARP table entries."""
        return await self._make_request("DELETE", "/api/v2/diagnostics/arp_table")
    
    async def delete_arp_entry(self, ip_address: str) -> Dict[str, Any]:
        """Delete a specific ARP table entry."""
        if not validate_ip_address(ip_address):
            raise ValueError(f"Invalid IP address: {ip_address}")
        
        params = urlencode({"ip": ip_address})
        return await self._make_request("DELETE", f"/api/v2/diagnostics/arp_table/entry?{params}")
    
    async def get_system_logs(self, limit: int = 100) -> Dict[str, Any]:
        """Get system logs."""
        return await self._make_request("GET", f"/api/v2/system/logs?limit={limit}")
    
    async def get_vpn_status(self) -> Dict[str, Any]:
        """Get VPN connection status."""
        try:
            # Try different VPN endpoints for pfSense 2.8.0
            return await self._make_request("GET", "/api/v2/vpn/status")
        except PfSenseAPIError:
            # Fallback to VPN connections
            logger.info("Primary VPN status endpoint failed, trying connections endpoint")
            return await self._make_request("GET", "/api/v2/vpn/connections")
    
    async def get_openvpn_servers(self) -> Dict[str, Any]:
        """Get OpenVPN server configurations."""
        return await self._make_request("GET", "/api/v1/vpn/openvpn/server")
    
    async def get_openvpn_clients(self) -> Dict[str, Any]:
        """Get OpenVPN client configurations."""
        return await self._make_request("GET", "/api/v1/vpn/openvpn/client")
    
    async def restart_vpn_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a VPN service."""
        data = {"service": service_name}
        return await self._make_request("POST", "/api/v1/service/restart", data=data)
    
    async def create_backup(self, backup_name: str) -> Dict[str, Any]:
        """Create a system backup."""
        data = {"name": backup_name}
        return await self._make_request("POST", "/api/v1/system/backup", data=data)
    
    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore from a backup."""
        data = {"backup_id": backup_id}
        return await self._make_request("POST", "/api/v1/system/backup/restore", data=data)
    
    async def get_backup_list(self) -> Dict[str, Any]:
        """Get list of available backups."""
        return await self._make_request("GET", "/api/v1/system/backup")
    
    async def test_connection(self) -> bool:
        """Test the connection to pfSense."""
        return await self.auth.test_connection()
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
        await self.auth.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
