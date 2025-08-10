#!/usr/bin/env python3
"""
Working Proxmox MCP Server - Pure JSON-RPC implementation with real Proxmox functionality
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List

import requests
import urllib3


def debug_print(message: str):
    """Print debug messages to stderr to avoid interfering with MCP protocol."""
    print(f"DEBUG: {message}", file=sys.stderr)


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file."""
    # Try multiple possible config file locations
    possible_paths = [
        'config.json',  # Current directory
        os.path.join(os.path.dirname(__file__), 'config.json'),  # Same directory as script
        os.path.expanduser('~/.proxmox-mcp/config.json'),  # User home directory
    ]

    config_path = None
    for path in possible_paths:
        if os.path.exists(path):
            config_path = path
            break

    if not config_path:
        raise FileNotFoundError(f"Configuration file not found. Tried: {', '.join(possible_paths)}")

    debug_print(f"Using config file: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        debug_print(f"Configuration loaded successfully from: {config_path}")
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load config file {config_path}: {e}")


def main():
    """Main entry point for the server."""
    # Load configuration
    config = load_config()

    # Only suppress SSL warnings when explicitly configured to not verify SSL
    # This is safer than globally disabling all warnings
    if not config.get('ssl_verify', True):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        debug_print("SSL warnings disabled due to ssl_verify=False configuration")

    debug_print("Server starting...")

    # Completely suppress all output
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(logging.NullHandler())
    logging.getLogger().setLevel(logging.CRITICAL)

    # Create and run the server
    server = WorkingProxmoxMCPServer()
    server.run()


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
                raise Exception("Authentication failed - no ticket received")
        except Exception as e:
            debug_print(f"Authentication failed: {e}")
            raise

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
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response = handler(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            debug_print(f"Request failed: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Proxmox."""
        try:
            response = self._make_request('GET', '/version')
            try:
                version_data = response.json()
                return {
                    "status": "success",
                    "version": version_data.get('data', {}),
                    "message": "Connection successful"
                }
            except (ValueError, KeyError) as parse_error:
                debug_print(f"Failed to parse response: {parse_error}")
                return {
                    "status": "error",
                    "error": f"Response parsing failed: {parse_error}",
                    "message": "Connection succeeded but response parsing failed"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Connection failed"
            }

    def list_nodes(self) -> List[Dict[str, Any]]:
        """List all nodes in the cluster."""
        try:
            response = self._make_request('GET', '/nodes')
            nodes_data = response.json()
            return nodes_data.get('data', [])
        except Exception as e:
            debug_print(f"Failed to list nodes: {e}")
            return []

    def list_vms(self, node: str = None) -> List[Dict[str, Any]]:
        """List all virtual machines."""
        try:
            if node:
                endpoint = f'/nodes/{node}/qemu'
            else:
                # Get VMs from all nodes
                all_vms = []
                nodes = self.list_nodes()
                for node_info in nodes:
                    try:
                        response = self._make_request('GET', f'/nodes/{node_info["node"]}/qemu')
                        vms_data = response.json()
                        node_vms = vms_data.get('data', [])
                        for vm in node_vms:
                            vm['node'] = node_info['node']
                        all_vms.extend(node_vms)
                    except Exception as e:
                        debug_print(f"Failed to get VMs from node {node_info['node']}: {e}")
                return all_vms

            response = self._make_request('GET', endpoint)
            vms_data = response.json()
            return vms_data.get('data', [])
        except Exception as e:
            debug_print(f"Failed to list VMs: {e}")
            return []

    def get_vm_info(self, node: str, vmid: int) -> Dict[str, Any]:
        """Get detailed information about a specific VM."""
        try:
            response = self._make_request('GET', f'/nodes/{node}/qemu/{vmid}/status/current')
            vm_data = response.json()
            return vm_data.get('data', {})
        except Exception as e:
            debug_print(f"Failed to get VM info: {e}")
            return {}

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
        except Exception as e:
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
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to stop VM {vmid}"
            }

    def list_containers(self, node: str = None) -> List[Dict[str, Any]]:
        """List all containers."""
        try:
            if node:
                endpoint = f'/nodes/{node}/lxc'
            else:
                # Get containers from all nodes
                all_containers = []
                nodes = self.list_nodes()
                for node_info in nodes:
                    try:
                        response = self._make_request('GET', f'/nodes/{node_info["node"]}/lxc')
                        containers_data = response.json()
                        node_containers = containers_data.get('data', [])
                        for container in node_containers:
                            container['node'] = node_info['node']
                        all_containers.extend(node_containers)
                    except Exception as e:
                        debug_print(f"Failed to get containers from node {node_info['node']}: {e}")
                return all_containers

            response = self._make_request('GET', endpoint)
            containers_data = response.json()
            return containers_data.get('data', [])
        except Exception as e:
            debug_print(f"Failed to list containers: {e}")
            return []

    def list_storage(self, node: str = None) -> List[Dict[str, Any]]:
        """List all storage pools."""
        try:
            if node:
                endpoint = f'/nodes/{node}/storage'
            else:
                # Get storage from all nodes
                all_storage = []
                nodes = self.list_nodes()
                for node_info in nodes:
                    try:
                        response = self._make_request('GET', f'/nodes/{node_info["node"]}/storage')
                        storage_data = response.json()
                        node_storage = storage_data.get('data', [])
                        for storage in node_storage:
                            storage['node'] = node_info['node']
                        all_storage.extend(node_storage)
                    except Exception as e:
                        debug_print(f"Failed to get storage from node {node_info['node']}: {e}")
                return all_storage

            response = self._make_request('GET', endpoint)
            storage_data = response.json()
            return storage_data.get('data', [])
        except Exception as e:
            debug_print(f"Failed to list storage: {e}")
            return []

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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
            except Exception as vm_error:
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
            except Exception as container_error:
                debug_print(f"Container snapshot creation failed: {container_error}")
            
            return {
                "status": "error",
                "message": f"Failed to create snapshot for {vmid} on {node}"
            }
        except Exception as e:
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
            except Exception as vm_error:
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
            except Exception as container_error:
                debug_print(f"Container snapshot listing failed: {container_error}")
            
            return {
                "status": "error",
                "message": f"Failed to list snapshots for {vmid} on {node}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Exception listing snapshots: {str(e)}"
            }


class WorkingProxmoxMCPServer:
    """Working Proxmox MCP server using pure JSON-RPC."""

    def __init__(self):
        """Initialize the server."""
        debug_print("Server starting...")
        self.proxmox_client = None
        
        # Load configuration
        self.config = load_config()
        
        try:
            debug_print("Initializing Proxmox client...")
            self.proxmox_client = ProxmoxClient(
                host=self.config['host'],
                port=self.config['port'],
                protocol=self.config['protocol'],
                username=self.config['username'],
                password=self.config['password'],
                realm=self.config.get('realm', 'pve'),
                ssl_verify=self.config.get('ssl_verify', False)
            )
            
            # Test connection in a non-blocking way
            try:
                connection_result = self.proxmox_client.test_connection()
                if connection_result.get('status') == 'success':
                    debug_print("Proxmox connection successful")
                else:
                    debug_print(f"Proxmox connection failed: {connection_result.get('error', 'Unknown error')}")
                    debug_print("Server will continue but Proxmox operations may fail")
            except Exception as conn_e:
                debug_print(f"Connection test failed: {conn_e}")
                debug_print("Server will continue but Proxmox operations will fail")
                
        except Exception as e:
            debug_print(f"Failed to initialize Proxmox client: {e}")
            debug_print("Server will continue but Proxmox operations will fail")
            self.proxmox_client = None
        
        debug_print("Server initialization complete")

    def _list_tools(self) -> Dict[str, Any]:
        """List all available tools."""
        return {
            "tools": [
                {
                    "name": "proxmox_test_connection", 
                    "description": "Test connection to Proxmox server",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "proxmox_list_nodes", 
                    "description": "List all nodes in the cluster",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "proxmox_get_node_status", 
                    "description": "Get detailed status and resource usage for a specific node",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            }
                        },
                        "required": ["node"]
                    }
                },
                {
                    "name": "proxmox_list_vms", 
                    "description": "List all virtual machines",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name (optional)"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "proxmox_get_vm_info", 
                    "description": "Get detailed information about a specific VM",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_get_vm_status", 
                    "description": "Get current status and resource usage of a VM",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_create_vm", 
                    "description": "Create a new virtual machine",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID (optional, auto-assigned if not specified)"
                            },
                            "name": {
                                "type": "string",
                                "description": "VM name"
                            },
                            "cores": {
                                "type": "string",
                                "description": "Number of CPU cores (default: 1)"
                            },
                            "memory": {
                                "type": "string",
                                "description": "Memory in MB (default: 512)"
                            }
                        },
                        "required": ["node", "name"]
                    }
                },
                {
                    "name": "proxmox_start_vm", 
                    "description": "Start a virtual machine",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_stop_vm", 
                    "description": "Stop a virtual machine",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_suspend_vm", 
                    "description": "Suspend a running virtual machine",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_resume_vm", 
                    "description": "Resume a suspended virtual machine",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_delete_vm", 
                    "description": "Delete a virtual machine",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_list_containers", 
                    "description": "List all containers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name (optional)"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "proxmox_start_container", 
                    "description": "Start a container",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "Container ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_stop_container", 
                    "description": "Stop a container",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "Container ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_list_storage", 
                    "description": "List all storage pools",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name (optional)"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "proxmox_get_storage_usage", 
                    "description": "Get storage usage and capacity information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name (optional)"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "proxmox_create_snapshot", 
                    "description": "Create a snapshot of a VM or container",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM/Container ID"
                            },
                            "snapname": {
                                "type": "string",
                                "description": "Snapshot name"
                            },
                            "description": {
                                "type": "string",
                                "description": "Snapshot description (optional)"
                            }
                        },
                        "required": ["node", "vmid", "snapname"]
                    }
                },
                {
                    "name": "proxmox_list_snapshots", 
                    "description": "List snapshots for a VM or container",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM/Container ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_get_version", 
                    "description": "Get Proxmox version information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
        }

    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        debug_print(f"Calling tool: {name} with arguments: {arguments}")
        
        # Check if Proxmox client is available
        if self.proxmox_client is None:
            return {
                "content": [{"type": "text", "text": "Proxmox client not available. Please check your configuration and ensure the Proxmox server is reachable."}],
                "isError": True
            }

        try:
            if name == "proxmox_test_connection":
                result = self.proxmox_client.test_connection()
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_nodes":
                nodes = self.proxmox_client.list_nodes()
                result = {"nodes": nodes, "count": len(nodes)}
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_get_node_status":
                node = arguments.get('node')
                if not node:
                    return {
                        "content": [{"type": "text", "text": "Error: 'node' parameter is required"}],
                        "isError": True
                    }
                result = self.proxmox_client.get_node_status(node)
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_vms":
                node = arguments.get('node')
                vms = self.proxmox_client.list_vms(node)
                result = {"vms": vms, "count": len(vms)}
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_get_vm_info":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                vm_info = self.proxmox_client.get_vm_info(node, int(vmid))
                result_text = json.dumps(vm_info, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_get_vm_status":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.get_vm_status(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_create_vm":
                node = arguments.get('node')
                name = arguments.get('name')
                if not node or not name:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'name' are required"}],
                        "isError": True
                    }
                vmid = arguments.get('vmid')
                cores = arguments.get('cores', '1')
                memory = arguments.get('memory', '512')
                result = self.proxmox_client.create_vm(node, name, vmid, cores, memory)
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_start_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.start_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_stop_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.stop_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_suspend_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.suspend_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_resume_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.resume_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_delete_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.delete_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_containers":
                node = arguments.get('node')
                containers = self.proxmox_client.list_containers(node)
                result = {"containers": containers, "count": len(containers)}
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_start_container":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.start_container(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_stop_container":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.stop_container(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_storage":
                node = arguments.get('node')
                storage = self.proxmox_client.list_storage(node)
                result = {"storage": storage, "count": len(storage)}
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_get_storage_usage":
                node = arguments.get('node')
                result = self.proxmox_client.get_storage_usage(node)
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_create_snapshot":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                snapname = arguments.get('snapname')
                if not node or not vmid or not snapname:
                    return {
                        "content": [{"type": "text", "text": "Error: 'node', 'vmid', and 'snapname' are required"}],
                        "isError": True
                    }
                description = arguments.get('description', '')
                result = self.proxmox_client.create_snapshot(node, int(vmid), snapname, description)
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_snapshots":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                if not node or not vmid:
                    return {
                        "content": [{"type": "text", "text": "Error: Both 'node' and 'vmid' are required"}],
                        "isError": True
                    }
                result = self.proxmox_client.list_snapshots(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_get_version":
                version = self.proxmox_client.get_version()
                result_text = json.dumps(version, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    "isError": True
                }
        except Exception as e:
            debug_print(f"Tool execution failed: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }

    def _send_response(self, request_id: int, result: Dict[str, Any]):
        """Send a response to the client."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response))
        sys.stdout.flush()

    def _send_error(self, request_id: int, error_code: int, error_message: str):
        """Send an error response to the client."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
        print(json.dumps(response))
        sys.stdout.flush()

    def run(self):
        """Run the server using pure JSON-RPC over stdin/stdout."""
        debug_print("Server run method called - reading from stdin")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                debug_print(f"Received line: {line}")

                try:
                    request = json.loads(line)
                    debug_print(f"Parsed request: {request}")

                    method = request.get("method")
                    request_id = request.get("id")
                    params = request.get("params", {})

                    if method == "initialize":
                        # Handle MCP initialization
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "protocolVersion": "2025-06-18",
                                "capabilities": {},
                                "serverInfo": {
                                    "name": "proxmox-mcp",
                                    "version": "1.0.0"
                                }
                            }
                        }
                        print(json.dumps(response))
                        sys.stdout.flush()

                    elif method == "tools/list":
                        # Handle tools listing
                        debug_print("Handling tools/list request")
                        tools_result = self._list_tools()
                        self._send_response(request_id, tools_result)

                    elif method == "tools/call":
                        # Handle tool execution
                        debug_print(f"Handling tools/call request: {params}")
                        tool_name = params.get("name")
                        tool_args = params.get("arguments", {})

                        if not tool_name:
                            self._send_error(request_id, -32602, "Invalid params: tool name is required")
                            continue

                        result = self._call_tool(tool_name, tool_args)
                        self._send_response(request_id, result)

                    elif method == "notifications/initialized":
                        # Handle initialization notification (no response needed)
                        debug_print("Handling notifications/initialized")
                        continue

                    elif method == "notifications/cancel":
                        # Handle notification cancellation (no-op for now)
                        debug_print("Handling notifications/cancel")
                        continue

                    elif method == "resources/list":
                        # Handle resources listing (not supported, return error)
                        debug_print("Handling resources/list request (not supported)")
                        self._send_error(request_id, -32601, "Method not found: resources/list")
                        continue

                    elif method == "prompts/list":
                        # Handle prompts listing (not supported, return error)
                        debug_print("Handling prompts/list request (not supported)")
                        self._send_error(request_id, -32601, "Method not found: prompts/list")
                        continue

                    else:
                        # Unknown method
                        debug_print(f"Unknown method requested: {method}")
                        self._send_error(request_id, -32601, f"Method not found: {method}")

                except json.JSONDecodeError as e:
                    debug_print(f"JSON decode error: {e}")
                    if request_id is not None:
                        self._send_error(request_id, -32700, "Parse error")
                    continue

                except Exception as e:
                    debug_print(f"Request processing error: {e}")
                    debug_print(f"Error type: {type(e).__name__}")
                    import traceback
                    debug_print(f"Traceback: {traceback.format_exc()}")
                    if request_id is not None:
                        self._send_error(request_id, -32603, f"Internal error: {str(e)}")
                    continue

        except KeyboardInterrupt:
            debug_print("Server interrupted by user")
        except Exception as e:
            debug_print(f"Server error: {e}")
            import traceback
            debug_print(f"Server traceback: {traceback.format_exc()}")
            # Don't exit, just log the error and continue
            debug_print("Server continuing despite error...")


def main():
    """Main entry point."""
    try:
        server = WorkingProxmoxMCPServer()
        server.run()
    except Exception as e:
        debug_print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
