#!/usr/bin/env python3
"""
Test server for Warewulf MCP Server.

This script provides a mock implementation for testing the MCP server
without requiring a live Warewulf server.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.server import WarewulfMCPServer
from src.utils.logging import setup_logging


class MockWarewulfClient:
    """Mock Warewulf client for testing purposes."""
    
    def __init__(self):
        """Initialize mock client."""
        self.logger = setup_logging()
        self.mock_data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate mock data for testing."""
        return {
            "nodes": [
                {
                    "id": "node001",
                    "name": "compute-01",
                    "ipaddr": "192.168.1.101",
                    "hwaddr": "00:11:22:33:44:55",
                    "profile": "compute",
                    "status": "online"
                },
                {
                    "id": "node002",
                    "name": "compute-02",
                    "ipaddr": "192.168.1.102",
                    "hwaddr": "00:11:22:33:44:66",
                    "profile": "compute",
                    "status": "offline"
                },
                {
                    "id": "node003",
                    "name": "login-01",
                    "ipaddr": "192.168.1.201",
                    "hwaddr": "00:11:22:33:44:77",
                    "profile": "login",
                    "status": "online"
                }
            ],
            "profiles": [
                {
                    "id": "compute",
                    "name": "Compute Node Profile",
                    "description": "Standard compute node configuration",
                    "kernel": "5.15.0",
                    "initrd": "initrd-5.15.0.img"
                },
                {
                    "id": "login",
                    "name": "Login Node Profile",
                    "description": "Login node configuration",
                    "kernel": "5.15.0",
                    "initrd": "initrd-5.15.0.img"
                }
            ],
            "images": [
                {
                    "name": "rocky9-compute",
                    "size": "2.1GB",
                    "status": "ready",
                    "created": "2024-01-15T10:30:00Z"
                },
                {
                    "name": "rocky9-login",
                    "size": "1.8GB",
                    "status": "ready",
                    "created": "2024-01-15T10:30:00Z"
                }
            ],
            "overlays": [
                {
                    "name": "compute-overlay",
                    "description": "Compute node overlay",
                    "files": ["/etc/hosts", "/etc/resolv.conf"]
                },
                {
                    "name": "login-overlay",
                    "description": "Login node overlay",
                    "files": ["/etc/hosts", "/etc/resolv.conf", "/etc/ssh/sshd_config"]
                }
            ]
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Mock connection test."""
        return {
            "success": True,
            "message": "Mock connection successful",
            "data": {
                "status": "connected",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    
    def get_version(self) -> Dict[str, Any]:
        """Mock version info."""
        return {
            "success": True,
            "data": {
                "version": "4.6.0",
                "api_version": "v1",
                "build_date": "2024-01-15"
            }
        }
    
    def list_nodes(self) -> Dict[str, Any]:
        """Mock node listing."""
        return {
            "success": True,
            "data": self.mock_data["nodes"]
        }
    
    def get_node(self, node_id: str) -> Dict[str, Any]:
        """Mock node retrieval."""
        for node in self.mock_data["nodes"]:
            if node["id"] == node_id:
                return {
                    "success": True,
                    "data": node
                }
        return {
            "success": False,
            "error": f"Node {node_id} not found"
        }
    
    def list_profiles(self) -> Dict[str, Any]:
        """Mock profile listing."""
        return {
            "success": True,
            "data": self.mock_data["profiles"]
        }
    
    def list_images(self) -> Dict[str, Any]:
        """Mock image listing."""
        return {
            "success": True,
            "data": self.mock_data["images"]
        }
    
    def list_overlays(self) -> Dict[str, Any]:
        """Mock overlay listing."""
        return {
            "success": True,
            "data": self.mock_data["overlays"]
        }


class TestWarewulfMCPServer(WarewulfMCPServer):
    """Test version of Warewulf MCP Server with mock client."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize test server."""
        super().__init__(config)
        # Replace real client with mock client
        self.client = MockWarewulfClient()
        self.logger.info("Using mock Warewulf client for testing")


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing Warewulf MCP Server...")
    print("=" * 50)
    
    # Create test server
    server = TestWarewulfMCPServer()
    
    # Test tools listing
    print("\n📋 Available Tools:")
    tools = server.get_tools()
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool.name}: {tool.description}")
    
    print(f"\nTotal tools available: {len(tools)}")
    
    # Test basic functionality
    print("\n🔍 Testing Basic Functionality:")
    
    # Test connection
    try:
        result = server.client.test_connection()
        print(f"  ✅ Connection test: {result.get('success', False)}")
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
    
    # Test version
    try:
        result = server.client.get_version()
        print(f"  ✅ Version retrieval: {result.get('success', False)}")
        if result.get('success'):
            version = result.get('data', {}).get('version', 'Unknown')
            print(f"     Version: {version}")
    except Exception as e:
        print(f"  ❌ Version retrieval failed: {e}")
    
    # Test node listing
    try:
        result = server.client.list_nodes()
        print(f"  ✅ Node listing: {result.get('success', False)}")
        if result.get('success'):
            nodes = result.get('data', [])
            print(f"     Found {len(nodes)} nodes")
    except Exception as e:
        print(f"  ❌ Node listing failed: {e}")
    
    # Test profile listing
    try:
        result = server.client.list_profiles()
        print(f"  ✅ Profile listing: {result.get('success', False)}")
        if result.get('success'):
            profiles = result.get('data', [])
            print(f"     Found {len(profiles)} profiles")
    except Exception as e:
        print(f"  ❌ Profile listing failed: {e}")
    
    # Test image listing
    try:
        result = server.client.list_images()
        print(f"  ✅ Image listing: {result.get('success', False)}")
        if result.get('success'):
            images = result.get('data', [])
            print(f"     Found {len(images)} images")
    except Exception as e:
        print(f"  ❌ Image listing failed: {e}")
    
    # Test overlay listing
    try:
        result = server.client.list_overlays()
        print(f"  ✅ Overlay listing: {result.get('success', False)}")
        if result.get('success'):
            overlays = result.get('data', [])
            print(f"     Found {len(overlays)} overlays")
    except Exception as e:
        print(f"  ❌ Overlay listing failed: {e}")
    
    print("\n🎉 Test completed!")
    print("\n⚠️  Note: This is using mock data for testing purposes.")
    print("   To test with a real Warewulf server, update config.json and run the actual server.")


def main():
    """Main entry point."""
    print("🚀 Warewulf MCP Server - Test Mode")
    print("=" * 50)
    
    # Check if config exists
    config_path = Path("config.json")
    if config_path.exists():
        print("📁 Found config.json - will use for server configuration")
    else:
        print("⚠️  No config.json found - using default configuration")
        print("   Copy config.example.json to config.json and edit as needed")
    
    # Run tests
    asyncio.run(test_mcp_server())


if __name__ == "__main__":
    main()
