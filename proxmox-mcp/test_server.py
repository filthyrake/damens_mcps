#!/usr/bin/env python3
"""
Test script for the Proxmox MCP Server
"""

import json
import subprocess
import sys
import os
import time

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
    
    # Give the server a moment to start up
    time.sleep(1)
    
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
        if response:
            print(f"✅ Response: {response.strip()}")
        else:
            print("❌ No response received")
            return
        
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
        if response:
            print(f"✅ Response: {response.strip()}")
        else:
            print("❌ No response received")
            return
        
        # Test connection test (this will fail with placeholder config, but that's expected)
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
        if response:
            print(f"✅ Response: {response.strip()}")
            # Parse the response to see if it's an error (expected with placeholder config)
            try:
                parsed = json.loads(response)
                if "error" in parsed:
                    print("ℹ️  Connection test failed as expected (placeholder config)")
                else:
                    print("✅ Connection test successful")
            except json.JSONDecodeError:
                print("⚠️  Response received but couldn't parse JSON")
        else:
            print("❌ No response received")
            return
        
        print("\n✅ Server test completed successfully!")
        print("ℹ️  Note: Connection test failed because config.json contains placeholder values.")
        print("   This is expected behavior. Update config.json with real Proxmox details to test full functionality.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

if __name__ == "__main__":
    test_server()
