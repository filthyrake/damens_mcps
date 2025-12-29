#!/usr/bin/env python3
"""
Working Proxmox MCP Server - Pure JSON-RPC implementation with real Proxmox functionality

This is the CANONICAL implementation of the Proxmox MCP server.
All other server implementations have been removed to avoid confusion.
Use this file for all Proxmox MCP server operations.
"""

import json
import logging
import os
import signal
import sys
import threading
from typing import Any, Dict, List, Optional

import urllib3

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import validation functions, logging, and client
from src.utils.validation import (
    is_valid_vmid,
    is_valid_node_name,
    is_valid_storage_name,
    validate_snapshot_name,
    validate_cores_range,
    validate_memory_range
)
from src.utils.mcp_logging import setup_mcp_logging, suppress_noisy_loggers
from src.exceptions import (
    ProxmoxError,
    ProxmoxConnectionError,
    ProxmoxAuthenticationError,
    ProxmoxAPIError,
    ProxmoxTimeoutError,
    ProxmoxConfigurationError,
    ProxmoxValidationError,
    ProxmoxResourceNotFoundError
)
from src.proxmox_client import ProxmoxClient
from src.secure_config import SecureConfigManager


# Initialize logger at module load time to avoid race conditions
# This ensures logging is available even if WorkingProxmoxMCPServer is instantiated before main()
logger = setup_mcp_logging("proxmox-mcp")
suppress_noisy_loggers()


def debug_print(message: str) -> None:
    """Print debug messages to stderr to avoid interfering with MCP protocol."""
    print(f"DEBUG: {message}", file=sys.stderr)


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file, supporting both plaintext and encrypted passwords."""
    # Try multiple possible config file locations
    possible_paths: List[str] = [
        'config.json',  # Current directory
        os.path.join(os.path.dirname(__file__), 'config.json'),  # Same directory as script
        os.path.expanduser('~/.proxmox-mcp/config.json'),  # User home directory
    ]

    config_path: Optional[str] = None
    for path in possible_paths:
        if os.path.exists(path):
            config_path = path
            break

    if not config_path:
        raise ProxmoxConfigurationError(f"Configuration file not found. Tried: {', '.join(possible_paths)}")

    debug_print(f"Using config file: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config: Dict[str, Any] = json.load(f)
        debug_print(f"Configuration loaded successfully from: {config_path}")
        return config
    except json.JSONDecodeError as e:
        raise ProxmoxConfigurationError(f"Invalid JSON in config file {config_path}: {e}")
    except OSError as e:
        raise ProxmoxConfigurationError(f"Failed to read config file {config_path}: {e}")


class WorkingProxmoxMCPServer:
    """Working Proxmox MCP server using pure JSON-RPC."""

    def __init__(self):
        """Initialize the server."""
        debug_print("Server starting...")
        self.proxmox_client = None
        # Lock for thread-safe cleanup (guards against concurrent cleanup calls)
        self._cleanup_lock = threading.Lock()

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
            except ProxmoxError as conn_e:
                debug_print(f"Connection test failed: {conn_e}")
                debug_print("Server will continue but Proxmox operations will fail")
                
        except ProxmoxError as e:
            debug_print(f"Failed to initialize Proxmox client: {e}")
            debug_print("Server will continue but Proxmox operations will fail")
            self.proxmox_client = None
        
        debug_print("Server initialization complete")

    def cleanup(self) -> None:
        """Clean up the Proxmox client session.

        Should be called during server shutdown to properly release resources
        (file descriptors, TCP connections).

        Thread-safe: uses a lock to prevent concurrent cleanup attempts
        (e.g., from signal handlers or multiple shutdown paths).
        """
        with self._cleanup_lock:
            if self.proxmox_client is None:
                debug_print("Cleanup called but client already None")
                return

            debug_print("Cleaning up Proxmox client session...")
            try:
                self.proxmox_client.close()
            except Exception as e:
                if logger:
                    logger.warning(f"Error closing Proxmox client: {e}")
            finally:
                self.proxmox_client = None
            if logger:
                logger.debug("Cleanup complete")

    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Create a standardized MCP error response.

        Args:
            message: The error message to include in the response

        Returns:
            Dict with MCP-formatted error response containing content and isError flag
        """
        return {
            "content": [{"type": "text", "text": message}],
            "isError": True
        }

    def _validate_node_and_vmid(self, node: str, vmid: str) -> Optional[Dict[str, Any]]:
        """Validate node and vmid parameters for VM/container operations.

        This method validates that both parameters are present and conform to
        Proxmox naming requirements.

        Args:
            node: Node name to validate (alphanumeric with hyphens/underscores)
            vmid: VM/Container ID to validate (integer 100-999999)

        Returns:
            None if validation passes, or an MCP error response dict if validation
            fails. Callers should check: `if error := self._validate_node_and_vmid(...): return error`
        """
        if not node or not vmid:
            return self._create_error_response("Error: Both 'node' and 'vmid' are required")
        if not is_valid_node_name(node):
            return self._create_error_response(f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores")
        if not is_valid_vmid(vmid):
            return self._create_error_response(f"Error: Invalid VMID '{vmid}'. Must be between 100 and 999999")
        return None

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
                        "required": [],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "proxmox_list_nodes", 
                    "description": "List all nodes in the cluster",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
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
                                "type": "integer",
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
                                "type": "integer",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_create_vm", 
                    "description": (
                        "Create a new virtual machine in Proxmox.\n\n"
                        "This operation will:\n"
                        "- Create a VM with specified configuration\n"
                        "- Auto-assign VMID if not provided (next available ID)\n"
                        "- Allocate storage from specified pool\n\n"
                        "Example: Create a VM with 2 cores and 4GB RAM:\n"
                        '  {"node": "pve", "name": "test-vm", "cores": "2", "memory": "4096"}'
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "integer",
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
                        "required": ["node", "name"],
                        "additionalProperties": False
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
                                "type": "integer",
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
                                "type": "integer",
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
                                "type": "integer",
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
                                "type": "integer",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                },
                {
                    "name": "proxmox_delete_vm", 
                    "description": (
                        "Delete a virtual machine permanently.\n\n"
                        "⚠️ WARNING: This operation is destructive and cannot be undone!\n\n"
                        "This will:\n"
                        "- Permanently delete the VM and its configuration\n"
                        "- Remove all associated storage (if configured)\n"
                        "- Cannot be reversed once completed\n\n"
                        "Ensure you have backups before proceeding."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            },
                            "vmid": {
                                "type": "integer",
                                "description": "VM ID"
                            }
                        },
                        "required": ["node", "vmid"],
                        "additionalProperties": False
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
                                "type": "integer",
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
                                "type": "integer",
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
                                "type": "integer",
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
                                "type": "integer",
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
                # Validate node name
                if not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
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
                # Validate node name if provided
                if node and not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                # Use include_metadata=True when querying all nodes to expose partial failures
                if node:
                    vms = self.proxmox_client.list_vms(node)
                    result = {"vms": vms, "count": len(vms)}
                else:
                    vms_result = self.proxmox_client.list_vms(node, include_metadata=True)
                    result = {
                        "vms": vms_result["data"],
                        "count": len(vms_result["data"]),
                        "successful_nodes": vms_result["successful_nodes"],
                        "failed_nodes": vms_result["failed_nodes"],
                        "partial_failure": vms_result["partial_failure"]
                    }
                    if vms_result["partial_failure"]:
                        result["warning"] = f"Data incomplete: failed to query nodes {[n['node'] for n in vms_result['failed_nodes']]}"
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
                # Validate inputs to prevent injection attacks
                if not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                if not is_valid_vmid(vmid):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid VMID '{vmid}'. Must be between 100 and 999999"}],
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
                # Validate inputs to prevent injection attacks
                if not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                if not is_valid_vmid(vmid):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid VMID '{vmid}'. Must be between 100 and 999999"}],
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
                # Validate node name
                if not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                vmid = arguments.get('vmid')
                if vmid and not is_valid_vmid(vmid):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid VMID '{vmid}'. Must be between 100 and 999999"}],
                        "isError": True
                    }
                # Validate cores
                cores = arguments.get('cores', 1)
                if not validate_cores_range(cores):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid cores '{cores}'. Must be between 1 and 128"}],
                        "isError": True
                    }
                # Validate memory
                memory = arguments.get('memory', 512)
                if not validate_memory_range(memory):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid memory '{memory}'. Must be between 64 and 1048576 MB"}],
                        "isError": True
                    }
                # Validate storage name if provided
                storage = arguments.get('storage')
                if storage and not is_valid_storage_name(storage):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid storage name '{storage}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                result = self.proxmox_client.create_vm(node, name, vmid, cores, memory)
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_start_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.start_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_stop_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.stop_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_suspend_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.suspend_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_resume_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.resume_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_delete_vm":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.delete_vm(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_containers":
                node = arguments.get('node')
                # Validate node name if provided
                if node and not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                # Use include_metadata=True when querying all nodes to expose partial failures
                if node:
                    containers = self.proxmox_client.list_containers(node)
                    result = {"containers": containers, "count": len(containers)}
                else:
                    containers_result = self.proxmox_client.list_containers(node, include_metadata=True)
                    result = {
                        "containers": containers_result["data"],
                        "count": len(containers_result["data"]),
                        "successful_nodes": containers_result["successful_nodes"],
                        "failed_nodes": containers_result["failed_nodes"],
                        "partial_failure": containers_result["partial_failure"]
                    }
                    if containers_result["partial_failure"]:
                        result["warning"] = f"Data incomplete: failed to query nodes {[n['node'] for n in containers_result['failed_nodes']]}"
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_start_container":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.start_container(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_stop_container":
                node = arguments.get('node')
                vmid = arguments.get('vmid')
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                result = self.proxmox_client.stop_container(node, int(vmid))
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_list_storage":
                node = arguments.get('node')
                # Validate node name if provided
                if node and not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
                # Use include_metadata=True when querying all nodes to expose partial failures
                if node:
                    storage = self.proxmox_client.list_storage(node)
                    result = {"storage": storage, "count": len(storage)}
                else:
                    storage_result = self.proxmox_client.list_storage(node, include_metadata=True)
                    result = {
                        "storage": storage_result["data"],
                        "count": len(storage_result["data"]),
                        "successful_nodes": storage_result["successful_nodes"],
                        "failed_nodes": storage_result["failed_nodes"],
                        "partial_failure": storage_result["partial_failure"]
                    }
                    if storage_result["partial_failure"]:
                        result["warning"] = f"Data incomplete: failed to query nodes {[n['node'] for n in storage_result['failed_nodes']]}"
                result_text = json.dumps(result, indent=2, default=str)
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False
                }
            elif name == "proxmox_get_storage_usage":
                node = arguments.get('node')
                # Validate node name if provided
                if node and not is_valid_node_name(node):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid node name '{node}'. Must be alphanumeric with hyphens/underscores"}],
                        "isError": True
                    }
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
                # Validate node and vmid
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
                # Validate snapshot name
                if not validate_snapshot_name(snapname):
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid snapshot name '{snapname}'. Must be alphanumeric with hyphens/underscores, max 128 characters"}],
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
                error = self._validate_node_and_vmid(node, vmid)
                if error:
                    return error
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
        except ProxmoxConnectionError as e:
            if logger:
                logger.error(f"Proxmox connection error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Connection error: {str(e)}"}],
                "isError": True
            }
        except ProxmoxAuthenticationError as e:
            if logger:
                logger.error(f"Proxmox authentication error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Authentication error: {str(e)}"}],
                "isError": True
            }
        except ProxmoxTimeoutError as e:
            if logger:
                logger.error(f"Proxmox timeout in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Timeout error: {str(e)}"}],
                "isError": True
            }
        except ProxmoxValidationError as e:
            if logger:
                logger.error(f"Validation error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Validation error: {str(e)}"}],
                "isError": True
            }
        except ProxmoxResourceNotFoundError as e:
            if logger:
                logger.error(f"Resource not found in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Resource not found: {str(e)}"}],
                "isError": True
            }
        except ProxmoxError as e:
            if logger:
                logger.error(f"Proxmox API error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Proxmox error: {str(e)}"}],
                "isError": True
            }
        except (ConnectionError, TimeoutError) as e:
            if logger:
                logger.error(f"Network error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Network error: {str(e)}"}],
                "isError": True
            }
        except json.JSONDecodeError as e:
            if logger:
                logger.error(f"JSON decode error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": "Error: Invalid JSON response from Proxmox"}],
                "isError": True
            }
        except Exception as e:
            if logger:
                logger.exception(f"Unexpected error in tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Unexpected error: {type(e).__name__}"}],
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

                request_id = None  # Initialize before try block to handle JSON parse errors
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
                    if logger:
                        logger.error(f"JSON decode error: {e}")
                    if request_id is not None:
                        self._send_error(request_id, -32700, "Parse error")
                    continue

                except ProxmoxError as e:
                    if logger:
                        logger.error(f"Request processing error: {e}")
                    if request_id is not None:
                        self._send_error(request_id, -32603, f"Internal error: {str(e)}")
                    continue

                except Exception as e:
                    if logger:
                        logger.exception(f"Unexpected error handling request: {e}")
                    if request_id is not None:
                        self._send_error(request_id, -32603, "Internal error")
                    continue

        except KeyboardInterrupt:
            if logger:
                logger.info("Server interrupted by user")
        except Exception as e:
            # Catch-all for unexpected fatal errors outside of request processing
            if logger:
                logger.exception(f"Fatal server error: {e}")
        finally:
            # Always clean up resources on shutdown
            self.cleanup()


def main():
    """Main entry point."""
    # Check for --version flag
    if len(sys.argv) > 1 and sys.argv[1] in ('--version', '-v'):
        # Import version info
        try:
            from src.version import __version__, __description__
            print(f"Proxmox MCP Server version {__version__}")
            print(__description__)
        except ImportError:
            print("Proxmox MCP Server version 1.0.0")
        sys.exit(0)

    # Logger is already initialized at module load time
    server = None

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name}, initiating graceful shutdown...")
        if server:
            server.cleanup()
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        logger.debug("Server starting...")
        server = WorkingProxmoxMCPServer()
        server.run()
    except ProxmoxConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ProxmoxConnectionError as e:
        logger.error(f"Connection error: {e}")
        sys.exit(1)
    except ProxmoxAuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        sys.exit(1)
    except ProxmoxError as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
