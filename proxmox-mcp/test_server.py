#!/usr/bin/env python3
"""
Test script for the Proxmox MCP Server
"""

import json
import subprocess
import sys
import os

def test_server():
    """Test the Proxmox MCP server with various requests."""
    
    # Start the server
    print("Starting Proxmox MCP server...")
    process = subprocess.Popen(
        [sys.executable, "working_proxmox_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    try:
        # Test initialization
        print("\n1. Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        # Test tools listing
        print("\n2. Testing tools listing...")
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(list_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        # Test connection test
        print("\n3. Testing connection test...")
        test_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "proxmox_test_connection",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(test_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
        print("\n✅ Server test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_server()
