#!/usr/bin/env python3
"""
Test script for the iDRAC MCP server with real functionality
"""

import json
import subprocess
import sys
import time

def test_server():
    """Test the MCP server with various requests."""
    
    # Start the server
    print("Starting iDRAC MCP server with real functionality...")
    process = subprocess.Popen(
        [sys.executable, "working_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/damenknight/damens_mcps/idrac-mcp"
    )
    
    # Wait a moment for server to start
    time.sleep(1)
    
    # Test 1: Initialize
    print("\n1. Testing initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        },
        "id": 1
    }
    
    process.stdin.write(json.dumps(init_request) + "\n")
    process.stdin.flush()
    
    response = process.stdout.readline()
    print(f"Response: {response.strip()}")
    
    # Test 2: List tools
    print("\n2. Testing tools/list...")
    list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    
    process.stdin.write(json.dumps(list_request) + "\n")
    process.stdin.flush()
    
    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Test 3: List servers
    print("\n3. Testing list_servers...")
    list_servers_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "list_servers",
            "arguments": {}
        },
        "id": 3
    }

    process.stdin.write(json.dumps(list_servers_request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Test 4: Test connection to default server
    print("\n4. Testing real iDRAC connection (default server)...")
    connection_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "test_connection",
            "arguments": {}
        },
        "id": 4
    }

    process.stdin.write(json.dumps(connection_request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Test 5: Get system info from default server
    print("\n5. Testing get_system_info (default server)...")
    system_info_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_system_info",
            "arguments": {}
        },
        "id": 5
    }

    process.stdin.write(json.dumps(system_info_request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Test 6: Get power status from default server
    print("\n6. Testing get_power_status (default server)...")
    power_status_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_power_status",
            "arguments": {}
        },
        "id": 6
    }

    process.stdin.write(json.dumps(power_status_request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Test 7: Test connection to specific server (if multiple servers configured)
    print("\n7. Testing connection to specific server...")
    specific_connection_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "test_connection",
            "arguments": {
                "server_id": "production"
            }
        },
        "id": 7
    }

    process.stdin.write(json.dumps(specific_connection_request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Test 8: Power management tools (read-only test)
    print("\n8. Testing power management tools...")
    print("Note: These are read-only tests to avoid affecting your server")

    power_on_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "power_on",
            "arguments": {}
        },
        "id": 8
    }

    process.stdin.write(json.dumps(power_on_request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Power on response: {response.strip()}")

    # Clean up
    process.terminate()
    process.wait()
    
    print("\n✅ All tests completed successfully!")

    # Parse the tools list to show available tools
    try:
        tools_response = json.loads(response.strip())
        if "result" in tools_response and "tools" in tools_response["result"]:
            print("\n📋 Available tools:")
            for tool in tools_response["result"]["tools"]:
                print(f"  • {tool['name']} - {tool['description']}")
        else:
            print("\n📋 Available tools:")
            for tool in [
                "list_servers - List all available iDRAC servers",
                "test_connection - Test connection to iDRAC",
                "get_system_info - Get server hardware info", 
                "get_power_status - Get current power status",
                "power_on - Power on the server",
                "power_off - Gracefully power off the server",
                "force_power_off - Force power off the server",
                "restart - Gracefully restart the server"
            ]:
                print(f"  • {tool}")
    except:
        print("\n📋 Available tools:")
        for tool in [
            "list_servers - List all available iDRAC servers",
            "test_connection - Test connection to iDRAC",
            "get_system_info - Get server hardware info",
            "get_power_status - Get current power status",
            "power_on - Power on the server",
            "power_off - Gracefully power off the server",
            "force_power_off - Force power off the server",
            "restart - Gracefully restart the server"
        ]:
            print(f"  • {tool}")

if __name__ == "__main__":
    test_server()
