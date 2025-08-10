#!/usr/bin/env python3
"""
Basic tests for the Proxmox MCP Server.

This module contains basic tests to verify the functionality
of the Proxmox MCP server and its components.
"""

import unittest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from working_proxmox_server import ProxmoxMCPServer
from src.proxmox_client import ProxmoxClient
from src.utils.validation import validate_vm_config, validate_container_config

class TestProxmoxClient(unittest.TestCase):
    """Test cases for the ProxmoxClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ProxmoxClient()
    
    def test_client_initialization(self):
        """Test that the client can be initialized."""
        self.assertIsNotNone(self.client)
        self.assertTrue(hasattr(self.client, 'host'))
        self.assertTrue(hasattr(self.client, 'username'))
    
    @patch('src.proxmox_client.requests.get')
    def test_test_connection(self, mock_get):
        """Test the test_connection method."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"version": "8.0.0"}}
        mock_get.return_value = mock_response
        
        result = self.client.test_connection()
        self.assertIn('status', result)
    
    @patch('src.proxmox_client.requests.get')
    def test_get_version(self, mock_get):
        """Test the get_version method."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"version": "8.0.0"}}
        mock_get.return_value = mock_response
        
        result = self.client.get_version()
        self.assertIn('data', result)

class TestProxmoxMCPServer(unittest.TestCase):
    """Test cases for the ProxmoxMCPServer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.server = ProxmoxMCPServer()
    
    def test_server_initialization(self):
        """Test that the server can be initialized."""
        self.assertIsNotNone(self.server)
        self.assertTrue(hasattr(self.server, '_list_tools'))
        self.assertTrue(hasattr(self.server, '_call_tool'))
    
    def test_list_tools(self):
        """Test that the server can list tools."""
        tools = self.server._list_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        # Check that all tools have required fields
        for tool in tools:
            self.assertIn('name', tool)
            self.assertIn('description', tool)
            self.assertIn('inputSchema', tool)
    
    def test_tool_names_have_prefix(self):
        """Test that all tool names have the 'proxmox_' prefix."""
        tools = self.server._list_tools()
        for tool in tools:
            self.assertTrue(tool['name'].startswith('proxmox_'), 
                          f"Tool {tool['name']} doesn't have 'proxmox_' prefix")
    
    def test_call_tool_with_invalid_tool(self):
        """Test calling a non-existent tool."""
        result = self.server._call_tool("invalid_tool", {})
        self.assertIn('isError', result)
        self.assertTrue(result['isError'])

class TestValidationUtils(unittest.TestCase):
    """Test cases for validation utilities."""
    
    def test_validate_vm_config_valid(self):
        """Test VM config validation with valid data."""
        config = {
            "name": "test-vm",
            "cores": "2",
            "memory": "1024"
        }
        result = validate_vm_config(config)
        self.assertTrue(result)
    
    def test_validate_vm_config_invalid(self):
        """Test VM config validation with invalid data."""
        config = {
            "name": "",  # Invalid: empty name
            "cores": "invalid",  # Invalid: non-numeric cores
            "memory": "0"  # Invalid: zero memory
        }
        result = validate_vm_config(config)
        self.assertFalse(result)
    
    def test_validate_container_config_valid(self):
        """Test container config validation with valid data."""
        config = {
            "name": "test-container",
            "cores": "1",
            "memory": "512"
        }
        result = validate_container_config(config)
        self.assertTrue(result)
    
    def test_validate_container_config_invalid(self):
        """Test container config validation with invalid data."""
        config = {
            "name": "",  # Invalid: empty name
            "cores": "-1",  # Invalid: negative cores
            "memory": "abc"  # Invalid: non-numeric memory
        }
        result = validate_container_config(config)
        self.assertFalse(result)

class TestToolDefinitions(unittest.TestCase):
    """Test cases for tool definitions and schemas."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.server = ProxmoxMCPServer()
        self.tools = self.server._list_tools()
    
    def test_all_tools_have_input_schema(self):
        """Test that all tools have inputSchema defined."""
        for tool in self.tools:
            self.assertIn('inputSchema', tool, 
                         f"Tool {tool['name']} missing inputSchema")
            self.assertIsInstance(tool['inputSchema'], dict)
    
    def test_input_schema_structure(self):
        """Test that inputSchema has required structure."""
        for tool in self.tools:
            schema = tool['inputSchema']
            self.assertIn('type', schema, 
                         f"Tool {tool['name']} inputSchema missing 'type'")
            self.assertEqual(schema['type'], 'object')
            
            if 'properties' in schema:
                self.assertIsInstance(schema['properties'], dict)
            if 'required' in schema:
                self.assertIsInstance(schema['required'], list)
    
    def test_tool_descriptions_are_meaningful(self):
        """Test that tool descriptions are meaningful."""
        for tool in self.tools:
            description = tool['description']
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 10, 
                             f"Tool {tool['name']} has very short description")
            self.assertNotIn('TODO', description, 
                           f"Tool {tool['name']} has TODO in description")

def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestProxmoxClient,
        TestProxmoxMCPServer,
        TestValidationUtils,
        TestToolDefinitions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success/failure
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🧪 Running Proxmox MCP Server Tests...")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
