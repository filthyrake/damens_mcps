"""Proxmox API client for interacting with Proxmox VE.

This is the canonical ProxmoxClient implementation extracted from working_proxmox_server.py.
It uses synchronous HTTP requests with the requests library for maximum compatibility.

This implementation uses individual parameters for initialization. The previous
async/proxmoxer-based implementation that used a config dictionary has been replaced
with this production-tested synchronous implementation.

Example usage:
    client = ProxmoxClient(
        host="proxmox.example.com", port=8006, protocol="https",
        username="root", password="secret", realm="pam", ssl_verify=False
    )
"""

import json
import sys
import threading
import time
import warnings
from typing import Any, Dict, List, Optional

import requests
from urllib3.exceptions import InsecureRequestWarning

from .exceptions import (
    ProxmoxConnectionError,
    ProxmoxAuthenticationError,
    ProxmoxAPIError,
    ProxmoxTimeoutError,
    ProxmoxValidationError,
    ProxmoxResourceNotFoundError,
    ProxmoxConfigurationError
)
from .utils.resilience import create_circuit_breaker, create_retry_decorator


def debug_print(message: str):
    """Print debug messages to stderr to avoid interfering with MCP protocol."""
    print(f"DEBUG: {message}", file=sys.stderr)


def suppress_insecure_request_warning(ssl_verify: bool):
    """
    Context manager to suppress InsecureRequestWarning when SSL verification is disabled.
    
    This is a helper to eliminate code duplication and ensure consistent warning handling.
    """
    class WarningSuppressionContext:
        def __init__(self, should_suppress: bool):
            self.should_suppress = should_suppress
            self.context = None
            
        def __enter__(self):
            self.context = warnings.catch_warnings()
            self.context.__enter__()
            if self.should_suppress:
                warnings.filterwarnings('ignore', category=InsecureRequestWarning)
            return self
            
        def __exit__(self, *args):
            return self.context.__exit__(*args)
    
    return WarningSuppressionContext(not ssl_verify)


class ProxmoxClient:
    """Client for interacting with Proxmox VE API.

    WARNING: This client is NOT thread-safe. The underlying requests.Session
    is not thread-safe, and concurrent use from multiple threads may cause
    connection corruption, authentication issues, or other unexpected behavior.

    For multi-threaded applications, create a separate ProxmoxClient instance
    per thread, or implement external synchronization.

    The client supports context manager protocol for automatic resource cleanup:
        with ProxmoxClient(...) as client:
            client.list_vms()
    """

    # Maximum number of retries for VMID conflicts during VM creation
    VMID_CONFLICT_MAX_RETRIES = 3

    def __init__(self, host: str, port: int, protocol: str, username: str, password: str, realm: str = "pve", ssl_verify: bool = False, ticket_expiry_seconds: int = 7200):
        """
        Initialize Proxmox client.

        Args:
            host: Proxmox hostname or IP address
            port: Proxmox API port (usually 8006)
            protocol: Protocol to use ('https' or 'http')
            username: Proxmox username
            password: Proxmox password
            realm: Authentication realm (default: "pve" for Proxmox VE)
            ssl_verify: Whether to verify SSL certificates (default: False for self-signed)
            ticket_expiry_seconds: Proxmox ticket expiry time in seconds (default: 7200 = 2 hours)

        Raises:
            ProxmoxConfigurationError: If required parameters are empty or invalid
            ProxmoxAuthenticationError: If initial authentication fails
            ProxmoxConnectionError: If connection to Proxmox fails
        """
        # Validate required parameters
        if not host:
            raise ProxmoxConfigurationError("host cannot be empty")
        if not username:
            raise ProxmoxConfigurationError("username cannot be empty")
        if not password:
            raise ProxmoxConfigurationError("password cannot be empty")
        if not protocol:
            raise ProxmoxConfigurationError("protocol cannot be empty")
        if protocol not in ('http', 'https'):
            raise ProxmoxConfigurationError(f"protocol must be 'http' or 'https', got '{protocol}'")
            
        self.host = host
        self.port = port
        self.protocol = protocol
        self.username = username
        self.password = password
        self.realm = realm
        self.ssl_verify = ssl_verify
        self.base_url = f"{protocol}://{host}:{port}/api2/json"
        self.session = requests.Session()

        # Set up authentication
        self.auth_url = f"{self.base_url}/access/ticket"
        self.session.verify = ssl_verify

        # Set headers for Proxmox API (excluding Content-Type to avoid conflicts)
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Proxmox-MCP-Server/1.0'
        })

        # Timeout configuration (seconds)
        self.timeout = 30

        # Authentication ticket tracking
        # Proxmox tickets typically expire after 2 hours (7200 seconds)
        # We refresh proactively at 90% of the expiry time
        self._ticket_expiry_seconds = ticket_expiry_seconds
        self._ticket_refresh_threshold = int(self._ticket_expiry_seconds * 0.9)
        self._ticket_obtained_at: Optional[float] = None
        # Lock to prevent concurrent ticket refresh attempts
        self._auth_lock = threading.Lock()

        # Retry configuration
        self.retry_max_attempts = 3
        self.retry_min_wait = 1.0
        self.retry_max_wait = 10.0
        
        # Circuit breaker configuration
        self.circuit_breaker_enabled = True
        self.circuit_breaker = create_circuit_breaker(
            fail_max=5,
            timeout_duration=60,
            name=f"proxmox_{host}"
        )
        
        # Create retry decorator (for synchronous requests)
        retry_decorator = create_retry_decorator(
            max_attempts=self.retry_max_attempts,
            min_wait=self.retry_min_wait,
            max_wait=self.retry_max_wait,
            retry_exceptions=(
                ProxmoxConnectionError,
                ProxmoxTimeoutError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
            )
        )
        # Apply decorator once during initialization for efficiency
        self._retried_execute_request = retry_decorator(self._execute_request)

        # Get authentication ticket - close session on failure to prevent resource leak
        try:
            self._authenticate()
        except Exception:
            # Clean up session if authentication fails during construction
            if self.session is not None:
                self.session.close()
                self.session = None
            raise

        debug_print("Created Proxmox client (connection details redacted)")
        if not ssl_verify:
            debug_print("WARNING: SSL verification is disabled. This should only be used in development or with trusted self-signed certificates.")
        debug_print(f"SSL Verify: {ssl_verify}")
        debug_print(f"Session headers: {dict(self.session.headers)}")

    def _authenticate(self):
        """Authenticate with Proxmox and get ticket."""
        try:
            # Handle realm properly - use default "pve" if not specified or empty
            if self.realm and self.realm.strip():
                username = f"{self.username}@{self.realm}"
            else:
                username = self.username

            auth_data = {
                'username': username,
                'password': self.password
            }

            # For authentication, we need to send form data, not JSON
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }

            # Context-specific warning suppression - only suppress when SSL verification is disabled
            with suppress_insecure_request_warning(self.ssl_verify):
                response = self.session.post(
                    self.auth_url,
                    data=auth_data,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            auth_result = response.json()
            if auth_result['data']:
                self.session.cookies.set('PVEAuthCookie', auth_result['data']['ticket'])
                self._ticket_obtained_at = time.time()
                debug_print("Authentication successful")
            else:
                raise ProxmoxAuthenticationError("Authentication failed - no ticket received")
        except requests.exceptions.ConnectionError as e:
            debug_print(f"Connection error during authentication: {e}")
            raise ProxmoxConnectionError(f"Failed to connect to Proxmox: {e}") from e
        except requests.exceptions.Timeout as e:
            debug_print(f"Timeout during authentication: {e}")
            raise ProxmoxTimeoutError(f"Authentication request timed out: {e}") from e
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                debug_print(f"Authentication failed - invalid credentials: {e}")
                raise ProxmoxAuthenticationError(f"Invalid credentials: {e}") from e
            else:
                debug_print(f"HTTP error during authentication: {e}")
                raise ProxmoxAPIError(f"HTTP error during authentication: {e}") from e
        except requests.exceptions.RequestException as e:
            debug_print(f"Request error during authentication: {e}")
            raise ProxmoxConnectionError(f"Request error during authentication: {e}") from e
        except (ProxmoxAuthenticationError, ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAPIError):
            raise
        except json.JSONDecodeError as e:
            debug_print(f"Failed to parse authentication response: {e}")
            raise ProxmoxAPIError(f"Invalid JSON in authentication response: {e}") from e
        except KeyError as e:
            debug_print(f"Missing expected field in authentication response: {e}")
            raise ProxmoxAPIError(f"Invalid authentication response format: {e}") from e

    def _is_ticket_expired(self) -> bool:
        """Check if the authentication ticket needs refresh.

        Returns True if the ticket is expired or will expire soon
        (within the refresh threshold).
        """
        if self._ticket_obtained_at is None:
            return True
        elapsed = time.time() - self._ticket_obtained_at
        return elapsed >= self._ticket_refresh_threshold

    def _ensure_valid_ticket(self):
        """Ensure we have a valid authentication ticket, refreshing if needed.

        This method should be called before making API requests to prevent
        authentication failures due to expired tickets. Proxmox tickets
        typically expire after 2 hours.

        Uses a lock to prevent multiple concurrent refresh attempts when
        multiple threads call this method simultaneously near ticket expiry.
        """
        # Fast path: check without lock first
        if not self._is_ticket_expired():
            return

        # Slow path: acquire lock and double-check
        with self._auth_lock:
            # Double-check after acquiring lock (another thread may have refreshed)
            if self._is_ticket_expired():
                debug_print("Authentication ticket expired or expiring soon, refreshing...")
                self._authenticate()

    def close(self):
        """Close the session and release resources.

        Should be called when the client is no longer needed to prevent
        resource leaks (file descriptors, TCP connections).
        """
        if self.session is not None:
            try:
                self.session.close()
                debug_print(f"Closed Proxmox client session for {self.host}")
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

    def __del__(self):
        """Destructor - safety net for resource cleanup.

        This is a last-resort cleanup mechanism for cases where close() was
        not called explicitly and the context manager was not used. Prefer
        using the context manager or calling close() explicitly.
        """
        try:
            self.close()
        except Exception:
            # Suppress exceptions during garbage collection
            pass

    def _execute_request(self, method: str, url: str, _auth_retry: bool = True, **kwargs) -> requests.Response:
        """
        Execute the actual HTTP request (internal method with retry logic).

        This method is decorated with retry logic and should not be called directly.
        Use _make_request instead.

        Args:
            method: HTTP method
            url: Full URL
            _auth_retry: Internal flag - if True, will retry once on 401 after re-auth
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            ProxmoxValidationError: If method is invalid
            ProxmoxConnectionError: If connection fails
            ProxmoxTimeoutError: If request times out
            ProxmoxAuthenticationError: If authentication fails (after retry)
            ProxmoxResourceNotFoundError: If resource not found
            ProxmoxAPIError: If API returns error
        """
        # Method mapping for cleaner code
        method_handlers = {
            'GET': self.session.get,
            'POST': self.session.post,
            'PUT': self.session.put,
            'DELETE': self.session.delete
        }

        try:
            handler = method_handlers.get(method.upper())
            if handler is None:
                raise ProxmoxValidationError(f"Unsupported HTTP method: {method}")

            # Add timeout if not specified
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout

            # Context-specific warning suppression - only suppress when SSL verification is disabled
            with suppress_insecure_request_warning(self.ssl_verify):
                response = handler(url, **kwargs)
                response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            debug_print(f"Connection error for {method} {url}: {e}")
            raise ProxmoxConnectionError(f"Failed to connect to Proxmox: {e}") from e
        except requests.exceptions.Timeout as e:
            debug_print(f"Request timeout for {method} {url}: {e}")
            raise ProxmoxTimeoutError(f"Request timed out: {e}") from e
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # On 401, attempt re-authentication and retry once
                if _auth_retry:
                    debug_print(f"Got 401 for {method} {url}, attempting re-authentication...")
                    try:
                        with self._auth_lock:
                            self._authenticate()
                        # Retry the request with _auth_retry=False to prevent infinite loop
                        return self._execute_request(method, url, _auth_retry=False, **kwargs)
                    except (ProxmoxAuthenticationError, ProxmoxConnectionError) as auth_e:
                        debug_print(f"Re-authentication failed: {auth_e}")
                        raise ProxmoxAuthenticationError(f"Authentication failed after retry: {e}") from e
                else:
                    debug_print(f"Authentication error for {method} {url} (after retry): {e}")
                    raise ProxmoxAuthenticationError(f"Authentication required: {e}") from e
            elif e.response.status_code == 404:
                debug_print(f"Resource not found for {method} {url}: {e}")
                raise ProxmoxResourceNotFoundError(f"Resource not found: {e}") from e
            else:
                debug_print(f"HTTP error for {method} {url}: {e}")
                raise ProxmoxAPIError(f"HTTP error {e.response.status_code}: {e}") from e
        except requests.exceptions.RequestException as e:
            debug_print(f"Request error for {method} {url}: {e}")
            raise ProxmoxConnectionError(f"Request error: {e}") from e
        except (ProxmoxValidationError, ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxResourceNotFoundError, ProxmoxAPIError):
            raise
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request with retry logic and circuit breaker.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object
        """
        # Ensure we have a valid ticket before making the request
        self._ensure_valid_ticket()

        url = f"{self.base_url}{endpoint}"
        debug_print(f"Making {method} request to: {endpoint}")

        # Use pre-decorated request execution (applied once in __init__)
        retried_request = self._retried_execute_request

        # Apply circuit breaker if enabled
        if self.circuit_breaker_enabled and self.circuit_breaker:
            result = self.circuit_breaker.call(
                retried_request, method, url, **kwargs
            )
        else:
            result = retried_request(method, url, **kwargs)

        return result

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Proxmox."""
        try:
            response = self._make_request('GET', '/version')
            try:
                version_data = response.json()
            except json.JSONDecodeError as e:
                debug_print(f"Failed to parse response: {e}")
                return {
                    "status": "error",
                    "error": f"Response parsing failed: {e}",
                    "message": "Connection succeeded but response parsing failed"
                }
            return {
                "status": "success",
                "version": version_data.get('data', {}),
                "message": "Connection successful"
            }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            debug_print(f"Connection test failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Connection failed"
            }

    def list_nodes(self) -> List[Dict[str, Any]]:
        """List all nodes in the cluster."""
        response = self._make_request('GET', '/nodes')
        try:
            nodes_data = response.json()
        except json.JSONDecodeError as e:
            debug_print(f"Failed to parse nodes list response: {e}")
            raise ProxmoxAPIError(f"Invalid JSON response: {e}") from e
        return nodes_data.get('data', [])

    def list_vms(self, node: str = None) -> List[Dict[str, Any]]:
        """List all virtual machines."""
        if node:
            endpoint = f'/nodes/{node}/qemu'
            response = self._make_request('GET', endpoint)
            try:
                vms_data = response.json()
            except json.JSONDecodeError as e:
                debug_print(f"Failed to parse VMs list response: {e}")
                raise ProxmoxAPIError(f"Invalid JSON response: {e}") from e
            return vms_data.get('data', [])
        else:
            # Get VMs from all nodes
            all_vms = []
            nodes = self.list_nodes()
            for node_info in nodes:
                try:
                    response = self._make_request('GET', f'/nodes/{node_info["node"]}/qemu')
                    try:
                        vms_data = response.json()
                    except json.JSONDecodeError as e:
                        debug_print(f"Failed to parse VMs response for node {node_info['node']}: {e}")
                        continue
                    node_vms = vms_data.get('data', [])
                    for vm in node_vms:
                        vm['node'] = node_info['node']
                    all_vms.extend(node_vms)
                except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAPIError) as e:
                    # Log but continue with other nodes
                    debug_print(f"Failed to get VMs from node {node_info['node']}: {e}")
            return all_vms

    def get_vm_info(self, node: str, vmid: int) -> Dict[str, Any]:
        """Get detailed information about a specific VM."""
        response = self._make_request('GET', f'/nodes/{node}/qemu/{vmid}/status/current')
        try:
            vm_data = response.json()
        except json.JSONDecodeError as e:
            debug_print(f"Failed to parse VM info response: {e}")
            raise ProxmoxAPIError(f"Invalid JSON response: {e}") from e
        return vm_data.get('data', {})

    def start_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """Start a virtual machine."""
        try:
            response = self._make_request('POST', f'/nodes/{node}/qemu/{vmid}/status/start')
            result = response.json()
            return {
                "status": "success",
                "message": f"VM {vmid} started successfully",
                "data": result.get('data', {})
            }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to start VM {vmid}"
            }

    def stop_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """Stop a virtual machine."""
        try:
            response = self._make_request('POST', f'/nodes/{node}/qemu/{vmid}/status/stop')
            result = response.json()
            return {
                "status": "success",
                "message": f"VM {vmid} stopped successfully",
                "data": result.get('data', {})
            }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to stop VM {vmid}"
            }

    def list_containers(self, node: str = None) -> List[Dict[str, Any]]:
        """List all containers."""
        if node:
            endpoint = f'/nodes/{node}/lxc'
            response = self._make_request('GET', endpoint)
            try:
                containers_data = response.json()
            except json.JSONDecodeError as e:
                debug_print(f"Failed to parse containers list response: {e}")
                raise ProxmoxAPIError(f"Invalid JSON response: {e}") from e
            return containers_data.get('data', [])
        else:
            # Get containers from all nodes
            all_containers = []
            nodes = self.list_nodes()
            for node_info in nodes:
                try:
                    response = self._make_request('GET', f'/nodes/{node_info["node"]}/lxc')
                    try:
                        containers_data = response.json()
                    except json.JSONDecodeError as e:
                        debug_print(f"Failed to parse containers response for node {node_info['node']}: {e}")
                        continue
                    node_containers = containers_data.get('data', [])
                    for container in node_containers:
                        container['node'] = node_info['node']
                    all_containers.extend(node_containers)
                except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAPIError) as e:
                    debug_print(f"Failed to get containers from node {node_info['node']}: {e}")
            return all_containers

    def list_storage(self, node: str = None) -> List[Dict[str, Any]]:
        """List all storage pools."""
        if node:
            endpoint = f'/nodes/{node}/storage'
            response = self._make_request('GET', endpoint)
            try:
                storage_data = response.json()
            except json.JSONDecodeError as e:
                debug_print(f"Failed to parse storage list response: {e}")
                raise ProxmoxAPIError(f"Invalid JSON response: {e}") from e
            return storage_data.get('data', [])
        else:
            # Get storage from all nodes
            all_storage = []
            nodes = self.list_nodes()
            for node_info in nodes:
                try:
                    response = self._make_request('GET', f'/nodes/{node_info["node"]}/storage')
                    try:
                        storage_data = response.json()
                    except json.JSONDecodeError as e:
                        debug_print(f"Failed to parse storage response for node {node_info['node']}: {e}")
                        continue
                    node_storage = storage_data.get('data', [])
                    for storage in node_storage:
                        storage['node'] = node_info['node']
                    all_storage.extend(node_storage)
                except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAPIError) as e:
                    debug_print(f"Failed to get storage from node {node_info['node']}: {e}")
            return all_storage

    def get_version(self) -> Dict[str, Any]:
        """Get Proxmox version information."""
        try:
            response = self._make_request("GET", "/version")
            if response.status_code == 200:
                version_data = response.json()
                return {
                    "status": "success",
                    "version": version_data.get("data", {}),
                    "message": "Version information retrieved successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get version: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception getting version: {str(e)}"
            }

    def get_node_status(self, node: str) -> Dict[str, Any]:
        """Get detailed status and resource usage for a specific node."""
        try:
            response = self._make_request("GET", f"/nodes/{node}/status")
            if response.status_code == 200:
                status_data = response.json()
                return {
                    "status": "success",
                    "node_status": status_data.get("data", {}),
                    "message": f"Node status retrieved for {node}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get node status: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception getting node status: {str(e)}"
            }

    def get_vm_status(self, node: str, vmid: int) -> Dict[str, Any]:
        """Get current status and resource usage of a VM."""
        try:
            response = self._make_request("GET", f"/nodes/{node}/qemu/{vmid}/status/current")
            if response.status_code == 200:
                status_data = response.json()
                return {
                    "status": "success",
                    "vm_status": status_data.get("data", {}),
                    "message": f"VM status retrieved for {vmid} on {node}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get VM status: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception getting VM status: {str(e)}"
            }

    def create_vm(self, node: str, name: str, vmid: int = None, cores: int = 1, memory: int = 512) -> Dict[str, Any]:
        """Create a new virtual machine.

        If vmid is not specified, automatically allocates the next available VMID.
        Handles VMID conflicts by retrying with a new VMID (up to VMID_CONFLICT_MAX_RETRIES times).

        Args:
            node: Node name where the VM will be created
            name: VM name
            vmid: Optional VM ID. If not specified, auto-allocates next available.
            cores: Number of CPU cores (default: 1)
            memory: Memory in MB (default: 512)

        Returns:
            Dict with status, vmid (on success), and message
        """
        # If user specified a VMID, use it directly without retry logic
        if vmid is not None:
            return self._create_vm_with_vmid(node, name, vmid, cores, memory)

        # Auto-allocate VMID with retry on conflict
        last_error = None
        for attempt in range(self.VMID_CONFLICT_MAX_RETRIES):
            try:
                allocated_vmid = self._get_next_vmid()
                debug_print(f"Attempting VM creation with VMID {allocated_vmid} (attempt {attempt + 1}/{self.VMID_CONFLICT_MAX_RETRIES})")

                result = self._create_vm_with_vmid(node, name, int(allocated_vmid), cores, memory)

                # Check if it was a VMID conflict error
                if result.get("status") == "error":
                    error_msg = result.get("message", "").lower()
                    if "already exists" in error_msg or "vmid" in error_msg and "in use" in error_msg:
                        debug_print(f"VMID {allocated_vmid} conflict detected, retrying...")
                        last_error = result.get("message")
                        continue  # Retry with new VMID

                return result

            except ProxmoxAPIError as e:
                error_str = str(e).lower()
                if "already exists" in error_str or ("vmid" in error_str and "in use" in error_str):
                    debug_print(f"VMID conflict on attempt {attempt + 1}: {e}")
                    last_error = str(e)
                    continue  # Retry with new VMID
                # Other API errors - don't retry
                return {
                    "status": "error",
                    "message": f"Exception creating VM: {str(e)}"
                }
            except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError) as e:
                return {
                    "status": "error",
                    "message": f"Exception creating VM: {str(e)}"
                }

        # Exhausted retries
        return {
            "status": "error",
            "message": f"Failed to create VM after {self.VMID_CONFLICT_MAX_RETRIES} attempts due to VMID conflicts. Last error: {last_error}"
        }

    def _create_vm_with_vmid(self, node: str, name: str, vmid: int, cores: int, memory: int) -> Dict[str, Any]:
        """Internal method to create a VM with a specific VMID.

        Args:
            node: Node name
            name: VM name
            vmid: VM ID to use
            cores: Number of CPU cores
            memory: Memory in MB

        Returns:
            Dict with status and message
        """
        try:
            config = {
                "vmid": str(vmid),
                "name": name,
                "cores": str(cores),
                "memory": str(memory),
                "sockets": "1"
            }

            response = self._make_request("POST", f"/nodes/{node}/qemu", data=config)
            if response.status_code == 200:
                return {
                    "status": "success",
                    "vmid": vmid,
                    "message": f"VM {name} created successfully with ID {vmid}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to create VM: {response.status_code} - {response.text}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception creating VM: {str(e)}"
            }

    def _get_next_vmid(self) -> int:
        """Get the next available VMID using Proxmox cluster API.

        Uses the /cluster/nextid endpoint to get a suggested VMID. Note that
        this does NOT reserve the VMID - concurrent VM creation may still
        cause conflicts. The create_vm method handles this with retry logic.

        Returns:
            Integer of the next available VMID

        Raises:
            ProxmoxAPIError: If unable to determine next VMID
        """
        # Try the cluster-wide nextid endpoint first
        try:
            response = self._make_request("GET", "/cluster/nextid")
            if response.status_code == 200:
                data = response.json()
                next_id = data.get("data")
                if next_id is not None:
                    debug_print(f"Got suggested VMID {next_id} from cluster API")
                    return int(next_id)
        except json.JSONDecodeError as e:
            debug_print(f"Failed to parse nextid response: {e}")
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            debug_print(f"Cluster nextid API failed: {e}")

        # Fallback: calculate from all VMs across all nodes (cluster-wide)
        debug_print("Cluster nextid API failed, falling back to cluster-wide manual calculation")
        try:
            all_vmids = set()

            # Get VMs from all nodes
            nodes = self.list_nodes()
            for node_info in nodes:
                node_name = node_info.get("node")
                if not node_name:
                    continue
                try:
                    # Get VMs
                    response = self._make_request("GET", f"/nodes/{node_name}/qemu")
                    if response.status_code == 200:
                        vms = response.json().get("data", [])
                        for vm in vms:
                            vmid = vm.get("vmid")
                            if vmid is not None:
                                all_vmids.add(int(vmid))

                    # Get containers too - they share the VMID namespace
                    response = self._make_request("GET", f"/nodes/{node_name}/lxc")
                    if response.status_code == 200:
                        containers = response.json().get("data", [])
                        for ct in containers:
                            vmid = ct.get("vmid")
                            if vmid is not None:
                                all_vmids.add(int(vmid))
                except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAPIError, json.JSONDecodeError) as e:
                    debug_print(f"Failed to get VMs/containers from node {node_name}: {e}")
                    continue

            if all_vmids:
                next_id = max(all_vmids) + 1
                debug_print(f"Calculated next VMID {next_id} from cluster scan (found {len(all_vmids)} existing)")
                return next_id

            # No VMs found, start from default
            debug_print("No existing VMs/containers found, starting from VMID 100")
            return 100

        except Exception as e:
            debug_print(f"Failed to calculate next VMID: {e}")
            raise ProxmoxAPIError(f"Unable to determine next available VMID: {e}") from e

    def suspend_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """Suspend a running virtual machine."""
        try:
            response = self._make_request("POST", f"/nodes/{node}/qemu/{vmid}/status/suspend")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"VM {vmid} suspended successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to suspend VM: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception suspending VM: {str(e)}"
            }

    def resume_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """Resume a suspended virtual machine."""
        try:
            response = self._make_request("POST", f"/nodes/{node}/qemu/{vmid}/status/resume")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"VM {vmid} resumed successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to resume VM: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception resuming VM: {str(e)}"
            }

    def delete_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """Delete a virtual machine."""
        try:
            response = self._make_request("DELETE", f"/nodes/{node}/qemu/{vmid}")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"VM {vmid} deleted successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete VM: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception deleting VM: {str(e)}"
            }

    def start_container(self, node: str, vmid: int) -> Dict[str, Any]:
        """Start a container."""
        try:
            response = self._make_request("POST", f"/nodes/{node}/lxc/{vmid}/status/start")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"Container {vmid} started successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to start container: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception starting container: {str(e)}"
            }

    def stop_container(self, node: str, vmid: int) -> Dict[str, Any]:
        """Stop a container."""
        try:
            response = self._make_request("POST", f"/nodes/{node}/lxc/{vmid}/status/stop")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"Container {vmid} stopped successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to stop container: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception stopping container: {str(e)}"
            }

    def get_storage_usage(self, node: str = None) -> Dict[str, Any]:
        """Get storage usage and capacity information."""
        try:
            if node:
                response = self._make_request("GET", f"/nodes/{node}/storage")
            else:
                # Get storage from all nodes
                nodes = self.list_nodes()
                all_storage = []
                for node_info in nodes:
                    node_name = node_info.get("node")
                    if node_name:
                        node_response = self._make_request("GET", f"/nodes/{node_name}/storage")
                        if node_response.status_code == 200:
                            node_storage = node_response.json().get("data", [])
                            for storage in node_storage:
                                storage["node"] = node_name
                            all_storage.extend(node_storage)
                
                return {
                    "status": "success",
                    "storage": all_storage,
                    "count": len(all_storage),
                    "message": "Storage usage retrieved from all nodes"
                }
            
            if response.status_code == 200:
                storage_data = response.json()
                return {
                    "status": "success",
                    "storage": storage_data.get("data", []),
                    "count": len(storage_data.get("data", [])),
                    "message": f"Storage usage retrieved for node {node}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get storage usage: {response.status_code}"
                }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception getting storage usage: {str(e)}"
            }

    def create_snapshot(self, node: str, vmid: int, snapname: str, description: str = "") -> Dict[str, Any]:
        """Create a snapshot of a VM or container."""
        try:
            # Try VM first, then container
            try:
                response = self._make_request("POST", f"/nodes/{node}/qemu/{vmid}/snapshot", 
                                           data={"snapname": snapname, "description": description})
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": f"VM snapshot {snapname} created successfully for VM {vmid}"
                    }
            except (ProxmoxResourceNotFoundError, ProxmoxAPIError) as vm_error:
                debug_print(f"VM snapshot creation failed: {vm_error}")
            
            # Try container if VM failed
            try:
                response = self._make_request("POST", f"/nodes/{node}/lxc/{vmid}/snapshot", 
                                           data={"snapname": snapname, "description": description})
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": f"Container snapshot {snapname} created successfully for container {vmid}"
                    }
            except (ProxmoxResourceNotFoundError, ProxmoxAPIError) as container_error:
                debug_print(f"Container snapshot creation failed: {container_error}")
            
            return {
                "status": "error",
                "message": f"Failed to create snapshot for {vmid} on {node}"
            }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception creating snapshot: {str(e)}"
            }

    def list_snapshots(self, node: str, vmid: int) -> Dict[str, Any]:
        """List snapshots for a VM or container."""
        try:
            # Try VM first, then container
            try:
                response = self._make_request("GET", f"/nodes/{node}/qemu/{vmid}/snapshot")
                if response.status_code == 200:
                    snapshot_data = response.json()
                    return {
                        "status": "success",
                        "snapshots": snapshot_data.get("data", []),
                        "count": len(snapshot_data.get("data", [])),
                        "message": f"VM snapshots retrieved for VM {vmid}"
                    }
            except (ProxmoxResourceNotFoundError, ProxmoxAPIError) as vm_error:
                debug_print(f"VM snapshot listing failed: {vm_error}")
            
            # Try container if VM failed
            try:
                response = self._make_request("GET", f"/nodes/{node}/lxc/{vmid}/snapshot")
                if response.status_code == 200:
                    snapshot_data = response.json()
                    return {
                        "status": "success",
                        "snapshots": snapshot_data.get("data", []),
                        "count": len(snapshot_data.get("data", [])),
                        "message": f"Container snapshots retrieved for container {vmid}"
                    }
            except (ProxmoxResourceNotFoundError, ProxmoxAPIError) as container_error:
                debug_print(f"Container snapshot listing failed: {container_error}")
            
            return {
                "status": "error",
                "message": f"Failed to list snapshots for {vmid} on {node}"
            }
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            return {
                "status": "error",
                "message": f"Exception listing snapshots: {str(e)}"
            }
