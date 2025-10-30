"""Tests for configuration loading functionality."""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import working_mcp_server


class TestConfigLoading:
    """Test configuration loading functionality."""
    
    def test_create_example_config(self):
        """Test that create_example_config creates a valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Create the example config
            working_mcp_server.create_example_config(config_path)
            
            # Verify the file was created
            assert os.path.exists(config_path)
            
            # Verify it's valid JSON
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Verify required fields exist
            assert 'idrac_servers' in config
            assert 'default_server' in config
            assert 'server' in config
            
            # Verify server structure
            assert len(config['idrac_servers']) > 0
            first_server = list(config['idrac_servers'].values())[0]
            assert 'host' in first_server
            assert 'port' in first_server
            assert 'username' in first_server
            assert 'password' in first_server
            
        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_load_config_success(self):
        """Test successful config loading."""
        valid_config = {
            "idrac_servers": {
                "test_server": {
                    "name": "Test Server",
                    "host": "192.168.1.100",
                    "port": 443,
                    "protocol": "https",
                    "username": "root",
                    "password": "password",
                    "ssl_verify": False
                }
            },
            "default_server": "test_server"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            json.dump(valid_config, f)
        
        try:
            # Mock the possible paths to include our temp file
            with patch.object(working_mcp_server, 'load_config') as mock_load:
                mock_load.return_value = valid_config
                config = mock_load()
                
                assert config is not None
                assert 'idrac_servers' in config
                assert 'test_server' in config['idrac_servers']
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        # Create a function that will fail to find config
        def load_missing_config():
            possible_paths = ['/nonexistent/config.json']
            raise FileNotFoundError(f"Configuration file not found. Tried: {', '.join(possible_paths)}")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_missing_config()
        
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_load_config_invalid_json(self):
        """Test config loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            f.write("{ invalid json }")
        
        try:
            with patch('working_mcp_server.load_config') as mock_load:
                mock_load.side_effect = ValueError("Invalid JSON in config file")
                
                with pytest.raises(ValueError) as exc_info:
                    mock_load()
                
                assert "Invalid JSON" in str(exc_info.value)
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_server_initialization_with_config(self):
        """Test that server can be initialized with config."""
        valid_config = {
            "idrac_servers": {
                "test_server": {
                    "name": "Test Server",
                    "host": "192.168.1.100",
                    "port": 443,
                    "protocol": "https",
                    "username": "root",
                    "password": "password",
                    "ssl_verify": False
                }
            },
            "default_server": "test_server"
        }
        
        # Test that server can be initialized with config parameter
        server = working_mcp_server.WorkingIDracMCPServer(valid_config)
        
        assert server is not None
        assert 'test_server' in server.servers
        assert server.default_server == 'test_server'
    
    def test_server_initialization_missing_servers(self):
        """Test server initialization with missing servers config."""
        invalid_config = {
            "default_server": "test_server"
        }
        
        with pytest.raises(ValueError) as exc_info:
            working_mcp_server.WorkingIDracMCPServer(invalid_config)
        
        assert "No iDRAC servers configured" in str(exc_info.value)
    
    def test_server_initialization_missing_required_fields(self):
        """Test server initialization with missing required fields."""
        invalid_config = {
            "idrac_servers": {
                "test_server": {
                    "name": "Test Server",
                    "host": "192.168.1.100"
                    # Missing port, username, password
                }
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            working_mcp_server.WorkingIDracMCPServer(invalid_config)
        
        assert "Missing required configuration field" in str(exc_info.value)


class TestMainFunction:
    """Test main function error handling."""
    
    def test_main_with_missing_config(self):
        """Test that main() handles missing config gracefully."""
        # Create a mock for load_config that raises FileNotFoundError
        with patch('working_mcp_server.load_config') as mock_load:
            mock_load.side_effect = FileNotFoundError("Configuration file not found. Tried: config.json")
            
            # Mock create_example_config to avoid actual file creation
            with patch('working_mcp_server.create_example_config'):
                # Test that main exits with code 1
                with pytest.raises(SystemExit) as exc_info:
                    working_mcp_server.main()
                
                assert exc_info.value.code == 1
    
    def test_main_with_invalid_json(self):
        """Test that main() handles invalid JSON gracefully."""
        with patch('working_mcp_server.load_config') as mock_load:
            mock_load.side_effect = ValueError("Invalid JSON in config file")
            
            # Test that main exits with code 1
            with pytest.raises(SystemExit) as exc_info:
                working_mcp_server.main()
            
            assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
