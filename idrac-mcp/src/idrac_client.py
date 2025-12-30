"""Synchronous iDRAC client for interacting with Dell PowerEdge servers via Redfish API.

This is the canonical iDRAC client implementation, extracted from working_mcp_server.py.
It uses the requests library for synchronous HTTP calls and is designed for use in
the JSON-RPC MCP server implementation.

Example usage:
    # Using config dictionary (recommended):
    config = {
        "host": "idrac.example.com",
        "port": 443,
        "protocol": "https",
        "username": "admin",
        "password": "<your-password>",  # Set via environment variable
        "ssl_verify": False
    }
    client = IDracClient(config)

    # Or use as context manager:
    with IDracClient(config) as client:
        info = client.get_system_info()
"""

import sys
import time
import warnings
from typing import Any, Dict, Optional, Union

import requests
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning

from src.utils.validation import validate_idrac_config
from src.utils.resilience import CachedResponse, DEFAULT_CACHE_TTL_SECONDS

# Request timeout configuration
# Balance between responsiveness and reliability for iDRAC API calls
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10


def debug_print(message: str) -> None:
    """Print debug messages to stderr to avoid interfering with MCP protocol."""
    print(f"DEBUG: {message}", file=sys.stderr)


def redact_sensitive_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive header values for safe logging."""
    if not isinstance(headers, dict):
        return headers

    sensitive_keys = ['authorization', 'cookie', 'x-auth-token', 'set-cookie']
    redacted = {}

    for key, value in headers.items():
        if key.lower() in sensitive_keys:
            redacted[key] = "REDACTED"
        else:
            redacted[key] = value

    return redacted


class IDracClient:
    """Synchronous client for interacting with iDRAC server via Redfish API.

    This client is designed for use with synchronous MCP server implementations.
    It uses the requests library for HTTP calls.

    Supports two initialization patterns for backwards compatibility:
    1. Config dictionary: IDracClient({"host": ..., "port": ..., ...})
    2. Keyword args: IDracClient(host="...", port=..., protocol="...", username="...", password="...", ssl_verify=...)

    Attributes:
        host: iDRAC hostname or IP address
        port: iDRAC port (usually 443)
        protocol: Protocol to use ('https' recommended)
        ssl_verify: Whether to verify SSL certificates
        base_url: Full base URL for API calls
        session: Requests session with auth and headers configured
    """

    def __init__(
        self,
        host: Union[str, Dict[str, Any]],
        port: Optional[int] = None,
        protocol: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssl_verify: bool = False
    ):
        """Initialize the iDRAC client.

        Args:
            host: Either a config dict with keys (host, port, protocol,
                username, password, ssl_verify) OR the hostname/IP string.
            port: iDRAC port (usually 443) - required if host is a string
            protocol: Protocol to use ('https' recommended) - required if host is a string
            username: iDRAC username - required if host is a string
            password: iDRAC password - required if host is a string
            ssl_verify: Whether to verify SSL certificates (default: False for self-signed)
        """
        # Support both config dict and keyword args for backwards compatibility
        if isinstance(host, dict):
            # Validate config - raises ValueError on invalid config
            validated = validate_idrac_config(host)
            self.config = validated
            self.host = validated['host']
            self.port = validated['port']
            self.protocol = validated['protocol']
            self.username = validated['username']
            self.password = validated['password']
            self.ssl_verify = validated.get('ssl_verify', False)
        else:
            # Keyword/positional arguments
            if port is None or protocol is None or username is None or password is None:
                raise ValueError(
                    "When using keyword arguments, host, port, protocol, username, "
                    "and password are all required"
                )
            self.host = host
            self.port = port
            self.protocol = protocol
            self.username = username
            self.password = password
            self.ssl_verify = ssl_verify
            # Store config dict for backwards compatibility
            self.config = {
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "username": self.username,
                "password": self.password,
                "ssl_verify": self.ssl_verify
            }

        self.base_url = f"{self.protocol}://{self.host}:{self.port}"
        self.session = requests.Session()
        
        # Response caching for static data (Issue #173)
        # System info rarely changes, cache for 5 minutes by default
        self._system_info_cache: Optional[CachedResponse[Dict[str, Any]]] = None
        self._cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS

        # Use explicit HTTPBasicAuth for better compatibility
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.session.auth = self.auth
        self.session.verify = self.ssl_verify

        # Set headers for iDRAC API
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'iDRAC-MCP-Server/1.0'
        })

        # Debug: Print session info (redacted to avoid sensitive details)
        debug_print("Created iDRAC client (connection details redacted)")
        if not self.ssl_verify:
            debug_print("WARNING: SSL verification is disabled. This should only be used in development or with trusted self-signed certificates.")
        debug_print(f"SSL Verify: {self.ssl_verify}")
        safe_headers = redact_sensitive_headers(dict(self.session.headers))
        debug_print(f"Session headers: {safe_headers}")
        debug_print(f"Auth type: {type(self.auth).__name__}")

    def close(self) -> None:
        """Close the session and release resources.

        Should be called when the client is no longer needed to prevent
        resource leaks (file descriptors, TCP connections).
        """
        if self.session is not None:
            try:
                self.session.close()
                debug_print(f"Closed iDRAC client session for {self.host}")
            except Exception as e:
                debug_print(f"Error closing session for {self.host}: {e}")
            finally:
                self.session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures session is closed."""
        self.close()
        return False

    def _execute_http_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute HTTP request with context-specific warning suppression.

        Helper method to eliminate duplication in _make_request.
        Supports GET, POST, PUT, DELETE, and PATCH methods for Redfish API compatibility.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            url: Full URL to request
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object from requests

        Raises:
            ValueError: If unsupported HTTP method is provided
        """
        method_map = {
            'GET': self.session.get,
            'POST': self.session.post,
            'PUT': self.session.put,
            'DELETE': self.session.delete,
            'PATCH': self.session.patch,
        }

        handler = method_map.get(method.upper())
        if not handler:
            raise ValueError(f"Unsupported HTTP method: {method}")

        with warnings.catch_warnings():
            if not self.ssl_verify:
                warnings.filterwarnings('ignore', category=InsecureRequestWarning)
            return handler(url, timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS, **kwargs)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request with proper error handling and debugging.

        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., '/redfish/v1/')
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object from requests

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        debug_print(f"Making {method} request to: {url}")
        debug_print(f"Session auth configured: {self.session.auth is not None}")
        debug_print(f"Session has cookies: {len(self.session.cookies)} cookies")
        safe_headers = redact_sensitive_headers(dict(self.session.headers))
        debug_print(f"Session headers: {safe_headers}")

        try:
            response = self._execute_http_request(method, url, **kwargs)

            debug_print(f"Response status: {response.status_code}")
            safe_response_headers = redact_sensitive_headers(dict(response.headers))
            debug_print(f"Response headers: {safe_response_headers}")
            debug_print(f"Response has cookies: {len(response.cookies)} cookies")

            if response.status_code == 401:
                debug_print("401 Unauthorized - attempting to re-authenticate")
                # Clear any existing cookies and re-authenticate
                self.session.cookies.clear()
                self.session.auth = self.auth
                debug_print(f"Re-authenticated with auth type: {type(self.auth).__name__}")
                debug_print(f"Cleared cookies, session now has: {len(self.session.cookies)} cookies")

                # Only retry idempotent methods to avoid double-applying side effects
                idempotent_methods = {'GET', 'PUT', 'HEAD'}
                if method.upper() in idempotent_methods:
                    response = self._execute_http_request(method, url, **kwargs)
                    debug_print(f"Retry response status: {response.status_code}")
                    debug_print(f"Retry response has cookies: {len(response.cookies)} cookies")
                else:
                    debug_print(f"Not retrying {method} request - non-idempotent method may have side effects")

            return response

        except Exception as e:
            debug_print(f"Request error: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to iDRAC server.

        Returns:
            Dict with connection status and details
        """
        try:
            response = self._make_request('GET', '/redfish/v1/')
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "host": self.host,
                    "port": self.port,
                    "message": f"Successfully connected to iDRAC at {self.host}:{self.port}",
                    "response_code": response.status_code
                }
            else:
                return {
                    "status": "error",
                    "host": self.host,
                    "port": self.port,
                    "message": f"Connection failed with status code: {response.status_code}",
                    "response_code": response.status_code
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "host": self.host,
                "port": self.port,
                "message": "Connection refused - server may be unreachable or port blocked",
                "response_code": None
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "host": self.host,
                "port": self.port,
                "message": "Connection timeout - server took too long to respond",
                "response_code": None
            }
        except Exception as e:
            return {
                "status": "error",
                "host": self.host,
                "port": self.port,
                "message": f"Connection error: {str(e)}",
                "response_code": None
            }

    def get_system_info(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get system information from iDRAC.

        Args:
            use_cache: If True, return cached data if available and valid.
                      Set to False to force a fresh API call.

        Returns:
            Dict with system information or error details
        """
        # Check cache first if enabled
        if use_cache and self._system_info_cache and self._system_info_cache.is_valid():
            debug_print("Returning cached system info")
            return self._system_info_cache.data
        
        try:
            response = self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            if response.status_code == 200:
                data = response.json()
                result = {
                    "host": self.host,
                    "protocol": self.protocol,
                    "ssl_verify": self.ssl_verify,
                    "system_info": {
                        "manufacturer": data.get('Manufacturer', 'Unknown'),
                        "model": data.get('Model', 'Unknown'),
                        "serial_number": data.get('SerialNumber', 'Unknown'),
                        "power_state": data.get('PowerState', 'Unknown'),
                        "health": data.get('Status', {}).get('Health', 'Unknown')
                    },
                    "message": "System information retrieved successfully"
                }
                # Cache the successful response
                self._system_info_cache = CachedResponse(result, self._cache_ttl_seconds)
                return result
            else:
                return {
                    "host": self.host,
                    "protocol": self.protocol,
                    "ssl_verify": self.ssl_verify,
                    "error": f"Failed to get system info: HTTP {response.status_code}",
                    "message": "Failed to retrieve system information"
                }
        except Exception as e:
            return {
                "host": self.host,
                "protocol": self.protocol,
                "ssl_verify": self.ssl_verify,
                "error": str(e),
                "message": f"Error retrieving system information: {str(e)}"
            }
    
    def invalidate_cache(self) -> None:
        """Invalidate all cached responses.
        
        Call this after operations that might change system info
        (e.g., power operations, reboots).
        """
        if self._system_info_cache:
            self._system_info_cache.invalidate()
        debug_print("All caches invalidated")

    def get_power_status(self) -> Dict[str, Any]:
        """Get current power status of the server.

        Returns:
            Dict with power status information
        """
        try:
            response = self._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
            if response.status_code == 200:
                data = response.json()
                power_state = data.get('PowerState', 'Unknown')

                # Get additional power information if available
                power_response = self._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1/Power')
                power_info = {}
                if power_response.status_code == 200:
                    power_data = power_response.json()
                    power_info = {
                        "total_consumption": power_data.get('PowerControl', [{}])[0].get('PowerConsumedWatts', 'Unknown'),
                        "power_supplies": len(power_data.get('PowerSupplies', []))
                    }

                return {
                    "host": self.host,
                    "power_status": power_state,
                    "power_info": power_info,
                    "message": f"Power status: {power_state}"
                }
            else:
                return {
                    "host": self.host,
                    "power_status": "unknown",
                    "error": f"Failed to get power status: HTTP {response.status_code}",
                    "message": "Failed to retrieve power status"
                }
        except Exception as e:
            return {
                "host": self.host,
                "power_status": "unknown",
                "error": str(e),
                "message": f"Error retrieving power status: {str(e)}"
            }

    def power_on(self) -> Dict[str, Any]:
        """Power on the server.

        Returns:
            Dict with operation result
        """
        # Invalidate cache since power state will change
        self.invalidate_cache()
        try:
            payload = {"ResetType": "On"}
            response = self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', json=payload)
            if response.status_code in [200, 202, 204]:
                return {
                    "host": self.host,
                    "action": "power_on",
                    "status": "success",
                    "message": "Power on command sent successfully"
                }
            else:
                return {
                    "host": self.host,
                    "action": "power_on",
                    "status": "error",
                    "error": f"Failed to power on: HTTP {response.status_code}",
                    "message": "Failed to send power on command"
                }
        except Exception as e:
            return {
                "host": self.host,
                "action": "power_on",
                "status": "error",
                "error": str(e),
                "message": f"Error sending power on command: {str(e)}"
            }

    def power_off(self) -> Dict[str, Any]:
        """Power off the server gracefully.

        Returns:
            Dict with operation result
        """
        # Invalidate cache since power state will change
        self.invalidate_cache()
        try:
            payload = {"ResetType": "GracefulShutdown"}
            response = self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', json=payload)
            if response.status_code in [200, 202, 204]:
                return {
                    "host": self.host,
                    "action": "power_off",
                    "status": "success",
                    "message": "Power off command sent successfully"
                }
            else:
                return {
                    "host": self.host,
                    "action": "power_off",
                    "status": "error",
                    "error": f"Failed to power off: HTTP {response.status_code}",
                    "message": "Failed to send power off command"
                }
        except Exception as e:
            return {
                "host": self.host,
                "action": "power_off",
                "status": "error",
                "error": str(e),
                "message": f"Error sending power off command: {str(e)}"
            }

    def force_power_off(self) -> Dict[str, Any]:
        """Force power off the server (immediate shutdown).

        WARNING: This performs an immediate hard shutdown. May cause data loss.

        Returns:
            Dict with operation result
        """
        # Invalidate cache since power state will change
        self.invalidate_cache()
        try:
            payload = {"ResetType": "ForceOff"}
            response = self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', json=payload)
            if response.status_code in [200, 202, 204]:
                return {
                    "host": self.host,
                    "action": "force_power_off",
                    "status": "success",
                    "message": "Force power off command sent successfully"
                }
            else:
                return {
                    "host": self.host,
                    "action": "force_power_off",
                    "status": "error",
                    "error": f"Failed to force power off: HTTP {response.status_code}",
                    "message": "Failed to send force power off command"
                }
        except Exception as e:
            return {
                "host": self.host,
                "action": "force_power_off",
                "status": "error",
                "error": str(e),
                "message": f"Error sending force power off command: {str(e)}"
            }

    def restart(self) -> Dict[str, Any]:
        """Restart the server gracefully.

        Returns:
            Dict with operation result
        """
        # Invalidate cache since system state will change after restart
        self.invalidate_cache()
        try:
            payload = {"ResetType": "GracefulRestart"}
            response = self._make_request('POST', '/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', json=payload)
            if response.status_code in [200, 202, 204]:
                return {
                    "host": self.host,
                    "action": "restart",
                    "status": "success",
                    "message": "Restart command sent successfully"
                }
            else:
                return {
                    "host": self.host,
                    "action": "restart",
                    "status": "error",
                    "error": f"Failed to restart: HTTP {response.status_code}",
                    "message": "Failed to send restart command"
                }
        except Exception as e:
            return {
                "host": self.host,
                "action": "restart",
                "status": "error",
                "error": str(e),
                "message": f"Error sending restart command: {str(e)}"
            }
