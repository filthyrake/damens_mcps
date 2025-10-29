"""Proxmox API client for interacting with Proxmox VE.

This is the canonical ProxmoxClient implementation extracted from working_proxmox_server.py.
It uses synchronous HTTP requests with the requests library for maximum compatibility.

IMPORTANT: This implementation uses individual parameters for initialization instead of 
a config dictionary. This change was made to consolidate the working implementation 
from working_proxmox_server.py which has been proven in production.

Old API (deprecated):
    client = ProxmoxClient(config={"host": "...", "port": 8006, ...})

New API:
    client = ProxmoxClient(
        host="...", port=8006, protocol="https",
        username="...", password="...", realm="pve", ssl_verify=False
    )
"""

import json
import sys
from typing import Any, Dict, List

import requests

from .exceptions import (
    ProxmoxError,
    ProxmoxConnectionError,
    ProxmoxAuthenticationError,
    ProxmoxAPIError,
    ProxmoxTimeoutError,
    ProxmoxValidationError,
    ProxmoxResourceNotFoundError
)


def debug_print(message: str):
    """Print debug messages to stderr to avoid interfering with MCP protocol."""
    print(f"DEBUG: {message}", file=sys.stderr)


class ProxmoxClient:
    """Client for interacting with Proxmox VE API."""

    def __init__(self, host: str, port: int, protocol: str, username: str, password: str, realm: str = "pve", ssl_verify: bool = False):
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
        """
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

        # Get authentication ticket
        self._authenticate()

        debug_print("Created Proxmox client (connection details redacted)")
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
            
            response = self.session.post(self.auth_url, data=auth_data, headers=headers)
            response.raise_for_status()
            auth_result = response.json()
            if auth_result['data']:
                self.session.cookies.set('PVEAuthCookie', auth_result['data']['ticket'])
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

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request with proper error handling and debugging."""
        url = f"{self.base_url}{endpoint}"
        debug_print(f"Making {method} request to: {endpoint}")
        
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
            
            response = handler(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            debug_print(f"Connection error for {method} {endpoint}: {e}")
            raise ProxmoxConnectionError(f"Failed to connect to Proxmox: {e}") from e
        except requests.exceptions.Timeout as e:
            debug_print(f"Request timeout for {method} {endpoint}: {e}")
            raise ProxmoxTimeoutError(f"Request timed out: {e}") from e
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                debug_print(f"Authentication error for {method} {endpoint}: {e}")
                raise ProxmoxAuthenticationError(f"Authentication required: {e}") from e
            elif e.response.status_code == 404:
                debug_print(f"Resource not found for {method} {endpoint}: {e}")
                raise ProxmoxResourceNotFoundError(f"Resource not found: {e}") from e
            else:
                debug_print(f"HTTP error for {method} {endpoint}: {e}")
                raise ProxmoxAPIError(f"HTTP error {e.response.status_code}: {e}") from e
        except requests.exceptions.RequestException as e:
            debug_print(f"Request error for {method} {endpoint}: {e}")
            raise ProxmoxConnectionError(f"Request error: {e}") from e
        except (ProxmoxValidationError, ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxResourceNotFoundError, ProxmoxAPIError):
            raise

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
        """Create a new virtual machine."""
        try:
            # Get next available VMID if not specified
            if vmid is None:
                vmid = self._get_next_vmid(node)
            
            # Basic VM configuration
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

    def _get_next_vmid(self, node: str) -> str:
        """Get the next available VMID."""
        try:
            response = self._make_request("GET", f"/nodes/{node}/qemu")
            if response.status_code == 200:
                vms = response.json().get("data", [])
                if vms:
                    # Find the highest VMID and add 1
                    max_vmid = max(int(vm.get("vmid", 0)) for vm in vms)
                    return str(max_vmid + 1)
                else:
                    return "100"  # Default starting VMID
            else:
                return "100"  # Fallback
        except (ProxmoxConnectionError, ProxmoxTimeoutError, ProxmoxAuthenticationError, ProxmoxAPIError) as e:
            debug_print(f"Failed to get next VMID: {e}")
            return "100"  # Fallback

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
