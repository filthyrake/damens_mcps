#!/usr/bin/env python3
"""
Minimal test server for Proxmox MCP to isolate protocol issues.
"""

import json
import sys

def debug_print(message: str):
    """Print debug message to stderr."""
    print(f"DEBUG: {message}", file=sys.stderr)

def main():
    """Minimal MCP server."""
    debug_print("Minimal test server starting...")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            debug_print(f"Received: {line}")

            try:
                request = json.loads(line)
                method = request.get("method")
                request_id = request.get("id")
                params = request.get("params", {})

                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "serverInfo": {
                                "name": "proxmox-test",
                                "version": "1.0.0"
                            }
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "proxmox_test_connection",
                                    "description": "Test connection to Proxmox server"
                                },
                                {
                                    "name": "proxmox_get_version",
                                    "description": "Get Proxmox version information"
                                }
                            ]
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                elif method == "tools/call":
                    # Handle tool execution
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})

                    if not tool_name:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32602,
                                "message": "Invalid params: tool name is required"
                            }
                        }
                        print(json.dumps(response))
                        sys.stdout.flush()
                        continue

                    # Handle specific tools
                    if tool_name == "proxmox_test_connection":
                        result = {
                            "status": "success",
                            "message": "Connection test successful (minimal server)",
                            "server": "minimal-test-server"
                        }
                    elif tool_name == "proxmox_get_version":
                        result = {
                            "version": "9.0.3",
                            "release": "9.0",
                            "message": "Version info from minimal server"
                        }
                    else:
                        result = {
                            "error": f"Tool {tool_name} not implemented in minimal server"
                        }

                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                elif method == "notifications/initialized":
                    debug_print("Handling notifications/initialized")
                    continue

                elif method == "resources/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": "Method not found: resources/list"
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                elif method == "prompts/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": "Method not found: prompts/list"
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                else:
                    debug_print(f"Unknown method: {method}")
                    if request_id is not None:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                        print(json.dumps(response))
                        sys.stdout.flush()

            except json.JSONDecodeError as e:
                debug_print(f"JSON error: {e}")
                continue
            except Exception as e:
                debug_print(f"Error: {e}")
                continue

    except KeyboardInterrupt:
        debug_print("Server interrupted")
    except Exception as e:
        debug_print(f"Server error: {e}")

if __name__ == "__main__":
    main()
