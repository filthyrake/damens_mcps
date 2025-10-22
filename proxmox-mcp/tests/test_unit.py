"""Unit tests for Proxmox MCP Server components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.proxmox_client import ProxmoxClient
from src.utils.validation import validate_vm_config, validate_container_config


class TestProxmoxClient:
    """Test cases for the ProxmoxClient class."""
    
    def test_client_initialization(self, mock_proxmox_config):
        """Test that the client can be initialized with config."""
        with patch('src.proxmox_client.requests.post') as mock_post:
            # Mock successful authentication
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "ticket": "test-ticket",
                    "CSRFPreventionToken": "test-csrf"
                }
            }
            mock_post.return_value = mock_response
            
            client = ProxmoxClient(mock_proxmox_config)
            assert client.host == mock_proxmox_config["host"]
            assert client.username == mock_proxmox_config["username"]
            assert hasattr(client, 'ticket')
    
    def test_client_authentication_failure(self, mock_proxmox_config):
        """Test client handles authentication failure."""
        with patch('src.proxmox_client.requests.post') as mock_post:
            # Mock authentication failure
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Authentication failed"
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception):
                ProxmoxClient(mock_proxmox_config)
    
    @patch('src.proxmox_client.requests.get')
    def test_test_connection(self, mock_get, mock_proxmox_client):
        """Test the test_connection method."""
        # Use the already-mocked client
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": {"version": "8.0.0"}}
        
        result = mock_proxmox_client.test_connection()
        assert "status" in result
    
    @patch('src.proxmox_client.requests.get')
    def test_get_version(self, mock_get, mock_proxmox_client):
        """Test the get_version method."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": {"version": "8.0.0"}}
        
        result = mock_proxmox_client.get_version()
        assert "data" in result


class TestValidationUtils:
    """Test cases for validation utilities."""
    
    def test_validate_vm_config_valid(self, sample_vm_config):
        """Test VM config validation with valid data."""
        result = validate_vm_config(sample_vm_config)
        assert result is True
    
    def test_validate_vm_config_missing_required(self):
        """Test VM config validation with missing required fields."""
        config = {
            "name": "test-vm",
            "cores": "2"
            # Missing required fields
        }
        result = validate_vm_config(config)
        assert result is False
    
    def test_validate_vm_config_invalid_name(self):
        """Test VM config validation with invalid name."""
        config = {
            "node": "pve",
            "name": "",  # Invalid: empty name
            "cores": "2",
            "memory": "1024"
        }
        result = validate_vm_config(config)
        assert result is False
    
    def test_validate_vm_config_invalid_cores(self):
        """Test VM config validation with invalid cores."""
        config = {
            "node": "pve",
            "name": "test-vm",
            "cores": "invalid",  # Invalid: non-numeric
            "memory": "1024"
        }
        result = validate_vm_config(config)
        assert result is False
    
    def test_validate_container_config_valid(self, sample_container_config):
        """Test container config validation with valid data."""
        result = validate_container_config(sample_container_config)
        assert result is True
    
    def test_validate_container_config_invalid_name(self):
        """Test container config validation with invalid name."""
        config = {
            "node": "pve",
            "name": "",  # Invalid: empty name
            "cores": "1",
            "memory": "512"
        }
        result = validate_container_config(config)
        assert result is False
    
    def test_validate_container_config_invalid_cores(self):
        """Test container config validation with invalid cores."""
        config = {
            "node": "pve",
            "name": "test-container",
            "cores": "-1",  # Invalid: negative cores
            "memory": "512"
        }
        result = validate_container_config(config)
        assert result is False


class TestServerMock:
    """Test cases for WorkingProxmoxMCPServer with mocks."""
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_server_initialization(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test that the server can be initialized with mocked config."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        assert server is not None
        assert hasattr(server, '_list_tools')
        assert hasattr(server, '_call_tool')
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_list_tools(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test that the server can list tools."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        result = server._list_tools()
        
        assert isinstance(result, dict)
        assert 'tools' in result
        tools = result['tools']
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check that all tools have required fields
        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_tool_names_have_prefix(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test that all tool names have the 'proxmox_' prefix."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        result = server._list_tools()
        tools = result['tools']
        
        for tool in tools:
            assert tool['name'].startswith('proxmox_'), \
                f"Tool {tool['name']} doesn't have 'proxmox_' prefix"
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_call_tool_with_invalid_tool(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test calling a non-existent tool."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        result = server._call_tool("invalid_tool", {})
        
        assert 'isError' in result
        assert result['isError'] is True
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_all_tools_have_input_schema(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test that all tools have inputSchema defined."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        result = server._list_tools()
        tools = result['tools']
        
        for tool in tools:
            assert 'inputSchema' in tool, f"Tool {tool['name']} missing inputSchema"
            assert isinstance(tool['inputSchema'], dict)
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_input_schema_structure(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test that inputSchema has required structure."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        result = server._list_tools()
        tools = result['tools']
        
        for tool in tools:
            schema = tool['inputSchema']
            assert 'type' in schema, f"Tool {tool['name']} inputSchema missing 'type'"
            assert schema['type'] == 'object'
            
            if 'properties' in schema:
                assert isinstance(schema['properties'], dict)
            if 'required' in schema:
                assert isinstance(schema['required'], list)
    
    @patch('working_proxmox_server.load_config')
    @patch('working_proxmox_server.ProxmoxClient')
    def test_tool_descriptions_are_meaningful(self, mock_client_class, mock_load_config, mock_proxmox_config):
        """Test that tool descriptions are meaningful."""
        from working_proxmox_server import WorkingProxmoxMCPServer
        
        mock_load_config.return_value = mock_proxmox_config
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        server = WorkingProxmoxMCPServer()
        result = server._list_tools()
        tools = result['tools']
        
        for tool in tools:
            description = tool['description']
            assert isinstance(description, str)
            assert len(description) > 10, f"Tool {tool['name']} has very short description"
            assert 'TODO' not in description, f"Tool {tool['name']} has TODO in description"
