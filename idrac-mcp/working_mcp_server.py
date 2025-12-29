#!/usr/bin/env python3
"""
Working iDRAC MCP Server - Pure JSON-RPC implementation with real iDRAC functionality

This is the CANONICAL implementation of the iDRAC MCP server.
All other server implementations have been removed to avoid confusion.
Use this file for all iDRAC MCP server operations.
"""

import json
import os
import signal
import sys
from typing import Any, Dict, List, Optional, TypedDict, Literal

# Import the IDracClient from the separate module
from src.idrac_client import (
    IDracClient,
    debug_print,
    redact_sensitive_headers,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
)

# Check for --version flag before any other imports that might fail
if len(sys.argv) > 1 and sys.argv[1] in ('--version', '-v'):
    # Add src directory to path for version import
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    try:
        from version import __version__, __description__
        print(f"iDRAC MCP Server version {__version__}", file=sys.stderr)
        print(__description__, file=sys.stderr)
    except ImportError:
        print("iDRAC MCP Server version 1.0.0", file=sys.stderr)
    sys.exit(0)

# Nested types for create_example_config
class ServerConfig(TypedDict):
    name: str
    host: str
    port: int
    protocol: Literal["https"]
    username: str
    password: str
    ssl_verify: bool

class ServerSettings(TypedDict):
    port: int
    debug: bool

class ExampleConfig(TypedDict):
    _comment: str
    idrac_servers: Dict[str, ServerConfig]
    default_server: str
    server: ServerSettings

# Import validation utilities
_validation_path = os.path.join(os.path.dirname(__file__), 'src', 'utils')
sys.path.insert(0, _validation_path)
try:
    from validation import validate_server_id
except ImportError as e:
    # Fail immediately - this indicates a deployment problem that must be fixed
    print(f"CRITICAL: Failed to import validation module: {e}", file=sys.stderr)
    print("This indicates a deployment or configuration issue.", file=sys.stderr)
    print(f"Expected validation module at: {os.path.join(_validation_path, 'validation.py')}", file=sys.stderr)
    print("Ensure the file exists and all dependencies are installed.", file=sys.stderr)
    sys.exit(1)

def create_example_config(config_path: str = 'config.json') -> None:
    """Create an example configuration file."""
    example_config: ExampleConfig = {
        "_comment": "IMPORTANT: Always use ssl_verify=true in production to prevent MITM attacks! Only set to false for development/testing with self-signed certificates. See SECURITY.md for proper certificate setup.",
        "idrac_servers": {
            "server1": {
                "name": "Production Server 1",
                "host": "192.168.1.100",
                "port": 443,
                "protocol": "https",
                "username": "root",
                "password": "your_password_here",
                "ssl_verify": True
            },
            "server2": {
                "name": "Production Server 2",
                "host": "192.168.1.101",
                "port": 443,
                "protocol": "https",
                "username": "root",
                "password": "your_password_here",
                "ssl_verify": True
            }
        },
        "default_server": "server1",
        "server": {
            "port": 8000,
            "debug": True
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(example_config, f, indent=2)


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file."""
    # Try multiple possible config file locations
    possible_paths: List[str] = [
        'config.json',  # Current directory
        os.path.join(os.path.dirname(__file__), 'config.json'),  # Same directory as script
        os.path.expanduser('~/.idrac-mcp/config.json'),  # User home directory
    ]
    
    config_path: Optional[str] = None
    for path in possible_paths:
        if os.path.exists(path):
            config_path = path
            break
    
    if not config_path:
        raise FileNotFoundError(f"Configuration file not found. Tried: {', '.join(possible_paths)}")
    
    debug_print(f"Using config file: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config: Dict[str, Any] = json.load(f)
        debug_print(f"Configuration loaded successfully from: {config_path}")
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load config file {config_path}: {e}")

# Note: SSL warnings are now suppressed only in the context of specific requests
# where SSL verification is disabled, rather than globally. This allows legitimate
# SSL issues to be visible during development and troubleshooting.

# Completely suppress all output
import logging
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().setLevel(logging.CRITICAL)


# IDracClient is now imported from src.idrac_client


class WorkingIDracMCPServer:
    """Working MCP server for iDRAC integration."""
    
    def __init__(self, config: Dict[str, Any]):
        debug_print("Initializing server...")
        
        # Extract server configuration from provided config dictionary
        config_data = config.get('idrac_servers', {})
        default_server = config.get('default_server')
        
        if not config_data:
            raise ValueError("No iDRAC servers configured in the configuration file")
        
        if default_server and default_server not in config_data:
            raise ValueError(f"Default server '{default_server}' not found in configuration")
        
        # Store server configurations
        self.servers = {}
        for server_id, server_config in config_data.items():
            # Validate required configuration
            required_fields = ['host', 'port', 'username', 'password']
            for field in required_fields:
                if field not in server_config:
                    raise ValueError(f"Missing required configuration field '{field}' for server '{server_id}'")
            
            self.servers[server_id] = {
                "name": server_config.get("name", server_id),
                "host": server_config["host"],
                "port": int(server_config["port"]),
                "protocol": server_config.get("protocol", "https"),
                "username": server_config["username"],
                "password": server_config["password"],
                "ssl_verify": server_config.get("ssl_verify", False)
            }
            
            debug_print(f"Configured server '{server_id}': {self.servers[server_id]['name']} at {self.servers[server_id]['protocol']}://{self.servers[server_id]['host']}:{self.servers[server_id]['port']}")
        
        # Set default server
        self.default_server = default_server or list(self.servers.keys())[0]
        debug_print(f"Default server: {self.default_server}")
        
        # Check for SSL verification issues and emit warning
        ssl_disabled_servers = [
            server_id for server_id, config in self.servers.items()
            if not config.get("ssl_verify", False)
        ]
        if ssl_disabled_servers:
            print("\n" + "="*80, file=sys.stderr)
            print("⚠️  WARNING: SSL VERIFICATION DISABLED ⚠️", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print("\nSSL certificate verification is DISABLED for the following servers:", file=sys.stderr)
            for server_id in ssl_disabled_servers:
                print(f"  - {server_id} ({self.servers[server_id]['name']})", file=sys.stderr)
            print("\nThis makes your connections vulnerable to man-in-the-middle attacks.", file=sys.stderr)
            print("DO NOT use this configuration in production!", file=sys.stderr)
            print("\nTo enable SSL verification, set 'ssl_verify': true in config.json", file=sys.stderr)
            print("or IDRAC_SSL_VERIFY=true in .env file.", file=sys.stderr)
            print("See SECURITY.md for information on proper SSL certificate setup.", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
        
        # Initialize iDRAC clients for all servers
        self.idrac_clients = {}
        for server_id, server_config in self.servers.items():
            self.idrac_clients[server_id] = IDracClient(
                host=server_config["host"],
                port=server_config["port"],
                protocol=server_config["protocol"],
                username=server_config["username"],
                password=server_config["password"],
                ssl_verify=server_config["ssl_verify"]
            )
        
        self.tools = [
            {
                "name": "list_servers",
                "description": (
                    "List all available iDRAC servers configured in this MCP instance.\n\n"
                    "Returns a list of server IDs that can be used with other tools.\n"
                    "The default server is indicated in the configuration."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "test_connection",
                "description": (
                    "Test connection to iDRAC server.\n\n"
                    "Verifies that:\n"
                    "- iDRAC is reachable over the network\n"
                    "- Credentials are valid\n"
                    "- API is responding correctly\n\n"
                    "Example: Test default server connection:\n"
                    '  {}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to test (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "get_system_info",
                "description": (
                    "Get comprehensive iDRAC system information.\n\n"
                    "Returns detailed information including:\n"
                    "- System model and manufacturer\n"
                    "- BIOS version and settings\n"
                    "- Hardware configuration\n"
                    "- Service tag and asset information\n\n"
                    "Example: Get system info for default server:\n"
                    '  {}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to query (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "get_power_status",
                "description": (
                    "Get current server power status.\n\n"
                    "Returns the current power state of the server:\n"
                    "- On: Server is powered on and running\n"
                    "- Off: Server is powered off\n"
                    "- Other states may include standby or transitioning\n\n"
                    "Example: Check power status of default server:\n"
                    '  {}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to query (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "power_on",
                "description": (
                    "Power on the server.\n\n"
                    "This operation will:\n"
                    "- Send a power on command to the server via iDRAC\n"
                    "- Start the boot process if the server is currently off\n"
                    "- Return success if the server is already powered on\n\n"
                    "Example: Power on the default server:\n"
                    '  {}\n'
                    "Example: Power on a specific server:\n"
                    '  {"server_id": "server1"}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to control (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "power_off",
                "description": (
                    "Power off the server gracefully.\n\n"
                    "⚠️ WARNING: This will initiate an orderly shutdown of the server.\n\n"
                    "This operation will:\n"
                    "- Send a graceful shutdown command to the operating system\n"
                    "- Allow services to shut down cleanly\n"
                    "- May take several minutes to complete\n\n"
                    "Use 'force_power_off' only if graceful shutdown fails.\n\n"
                    "Example: Power off the default server:\n"
                    '  {}\n'
                    "Example: Power off a specific server:\n"
                    '  {"server_id": "server1"}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to control (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "force_power_off",
                "description": (
                    "Force power off the server (immediate shutdown).\n\n"
                    "⚠️ DANGER: This performs an immediate hard shutdown, equivalent to pulling the power plug!\n\n"
                    "This operation will:\n"
                    "- Immediately cut power to the server\n"
                    "- Skip all shutdown procedures\n"
                    "- May cause data loss or corruption\n"
                    "- Should only be used when graceful shutdown fails\n\n"
                    "USE WITH EXTREME CAUTION. Try 'power_off' first for graceful shutdown.\n\n"
                    "Example: Force power off the default server:\n"
                    '  {}\n'
                    "Example: Force power off a specific server:\n"
                    '  {"server_id": "server1"}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to control (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "restart",
                "description": (
                    "Restart the server gracefully.\n\n"
                    "⚠️ WARNING: This will initiate a system restart.\n\n"
                    "This operation will:\n"
                    "- Send a graceful restart command to the operating system\n"
                    "- Allow services to shut down cleanly\n"
                    "- Automatically power back on after shutdown\n"
                    "- May take several minutes to complete\n\n"
                    "Example: Restart the default server:\n"
                    '  {}\n'
                    "Example: Restart a specific server:\n"
                    '  {"server_id": "server1"}'
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "ID of the server to control (optional, uses default if not specified)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            }
        ]
        debug_print(f"Created {len(self.tools)} tools")

    def cleanup(self) -> None:
        """Clean up all iDRAC client sessions.

        Should be called during server shutdown to properly release resources
        (file descriptors, TCP connections) for all managed iDRAC clients.
        """
        debug_print("Cleaning up iDRAC client sessions...")
        for server_id, client in self.idrac_clients.items():
            try:
                client.close()
            except Exception as e:
                debug_print(f"Error closing client for {server_id}: {e}")
        self.idrac_clients.clear()
        debug_print("Cleanup complete")

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

    def _validate_and_get_server_id(self, arguments: Dict[str, Any]) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Validate and get server ID from arguments.

        Args:
            arguments: Tool arguments dict that may contain 'server_id'

        Returns:
            Tuple of (server_id, error_response):
            - On success: (server_id, None)
            - On failure: (None, error_response_dict)
            Callers should check: `if error: return error`
        """
        server_id = arguments.get("server_id", self.default_server)

        # Validate server_id format
        if not validate_server_id(server_id):
            return None, self._create_error_response(
                "Error: Invalid server ID format. Server ID must contain only alphanumeric characters, hyphens, and underscores."
            )

        # Check if server exists
        if server_id not in self.idrac_clients:
            return None, self._create_error_response(f"Error: Server with ID '{server_id}' not found.")

        return server_id, None
    
    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        debug_print(f"Calling tool: {name}")
        try:
            if name == "list_servers":
                result = {"servers": list(self.servers.keys())}
            elif name == "test_connection":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].test_connection()
            elif name == "get_system_info":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].get_system_info()
            elif name == "get_power_status":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].get_power_status()
            elif name == "power_on":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].power_on()
            elif name == "power_off":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].power_off()
            elif name == "force_power_off":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].force_power_off()
            elif name == "restart":
                server_id, error = self._validate_and_get_server_id(arguments)
                if error:
                    return error
                result = self.idrac_clients[server_id].restart()
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            result_text = json.dumps(result, indent=2, default=str)
            debug_print(f"Tool result: {result_text}")
            return {
                "content": [{"type": "text", "text": result_text}],
                "isError": False
            }
        except Exception as e:
            debug_print(f"Tool error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    def _send_response(self, request_id: int, result: Dict[str, Any]):
        """Manually send a JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        debug_print(f"Sending response: {json.dumps(response)}")
        print(json.dumps(response), flush=True)
    
    def _send_error(self, request_id: int, error_code: int, error_message: str):
        """Manually send a JSON-RPC error response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
        debug_print(f"Sending error: {json.dumps(response)}")
        print(json.dumps(response), flush=True)
    
    def run(self):
        """Run the server using pure JSON-RPC over stdin/stdout."""
        debug_print("Server run method called - reading from stdin")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                    
                debug_print(f"Received line: {line}")
                
                # Initialize request_id to None at the start of each iteration
                request_id = None
                
                try:
                    request = json.loads(line)
                    debug_print(f"Parsed request: {request}")
                    
                    method = request.get("method")
                    request_id = request.get("id")
                    params = request.get("params", {})
                    
                    if method == "initialize":
                        debug_print("Handling initialize")
                        self._send_response(request_id, {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {
                                "experimental": {},
                                "tools": {
                                    "listChanged": False
                                }
                            },
                            "serverInfo": {
                                "name": "idrac-mcp",
                                "version": "0.1.0"
                            }
                        })
                        
                    elif method == "notifications/initialized":
                        debug_print("Handling notifications/initialized")
                        # This is a notification, no response needed
                        pass
                        
                    elif method == "tools/list":
                        debug_print("Handling tools/list")
                        self._send_response(request_id, {"tools": self.tools})
                        
                    elif method == "tools/call":
                        debug_print(f"Handling tools/call: {params.get('name')}")
                        tool_name = params.get("name")
                        tool_arguments = params.get("arguments", {})
                        result = self._call_tool(tool_name, tool_arguments)
                        self._send_response(request_id, result)
                        
                    elif method == "resources/list":
                        debug_print("Handling resources/list")
                        # Return empty resources list
                        self._send_response(request_id, {"resources": []})
                        
                    elif method == "prompts/list":
                        debug_print("Handling prompts/list")
                        # Return empty prompts list
                        self._send_response(request_id, {"prompts": []})
                        
                    else:
                        debug_print(f"Unknown method: {method}")
                        # For unknown methods, send a proper error response
                        if request_id is not None:
                            self._send_error(request_id, -32601, f"Method not found: {method}")
                        
                except json.JSONDecodeError as e:
                    debug_print(f"JSON decode error: {e}")
                    # Only send error if we have a request ID
                    if request_id is not None:
                        self._send_error(request_id, -32700, "Parse error")
                except Exception as e:
                    debug_print(f"Error handling request: {e}")
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    # Only send error if we have a request ID
                    if request_id is not None:
                        self._send_error(request_id, -32603, "Internal error")
                    
        except KeyboardInterrupt:
            debug_print("Server interrupted")
        except Exception as e:
            debug_print(f"Server error: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
        finally:
            # Always clean up resources on shutdown
            self.cleanup()


def main():
    """Main entry point."""
    debug_print("Starting main...")

    server = None

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        debug_print(f"Received signal {sig_name}, initiating graceful shutdown...")
        if server:
            server.cleanup()
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        config = load_config()
    except FileNotFoundError as e:
        print("Configuration file 'config.json' not found!", file=sys.stderr)
        print(f"   Tried: {e}", file=sys.stderr)
        print("\nCreating example configuration file...", file=sys.stderr)
        try:
            # Try to create in the script directory first
            config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json')
            create_example_config(config_path)
            print(f"Example configuration created at: {config_path}", file=sys.stderr)
            print("\nNext steps:", file=sys.stderr)
            print("   1. Edit 'config.json' with your iDRAC server details", file=sys.stderr)
            print("   2. Update the host, username, and password for each server", file=sys.stderr)
            print("   3. Run the server again", file=sys.stderr)
        except Exception as create_error:
            print(f"Failed to create example config: {create_error}", file=sys.stderr)
            print("\nPlease create a 'config.json' file manually with your iDRAC server details", file=sys.stderr)
            print("   See README.md for configuration instructions", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("\nPlease check your config.json file for valid JSON syntax", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    server = WorkingIDracMCPServer(config)
    server.run()


if __name__ == "__main__":
    main()
