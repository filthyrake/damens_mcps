"""Unit tests for iDRAC MCP Server multi-server scenarios."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestMultiServerManagement:
    """Test multi-server iDRAC management."""
    
    def test_multi_server_config_loading(self, mock_multi_server_config):
        """Test loading multi-server configuration."""
        assert "idrac_servers" in mock_multi_server_config
        assert "server1" in mock_multi_server_config["idrac_servers"]
        assert "server2" in mock_multi_server_config["idrac_servers"]
        assert mock_multi_server_config["default_server"] == "server1"
    
    def test_server_selection(self, mock_multi_server_config):
        """Test server selection from config."""
        servers = mock_multi_server_config["idrac_servers"]
        
        # Test getting specific server config
        server1_config = servers["server1"]
        assert server1_config["host"] == "192.168.1.100"
        
        server2_config = servers["server2"]
        assert server2_config["host"] == "192.168.1.101"
    
    def test_default_server_fallback(self, mock_multi_server_config):
        """Test default server selection."""
        default_server = mock_multi_server_config["default_server"]
        assert default_server in mock_multi_server_config["idrac_servers"]


class TestPowerManagement:
    """Test power management operations."""
    
    def test_valid_power_operations(self, sample_power_operation):
        """Test valid power operations."""
        from src.utils.validation import validate_power_operation
        
        result = validate_power_operation(sample_power_operation)
        assert result["operation"] == "on"
        assert result["force"] is False
        assert result["timeout"] == 60
    
    def test_power_operation_types(self):
        """Test different power operation types."""
        from src.utils.validation import validate_power_operation
        
        valid_operations = ["on", "off", "reset", "graceful_shutdown"]
        
        for op in valid_operations:
            config = {"operation": op, "force": False, "timeout": 60}
            result = validate_power_operation(config)
            assert result["operation"] == op
    
    def test_invalid_power_operation(self):
        """Test invalid power operations."""
        from src.utils.validation import validate_power_operation
        
        invalid_config = {
            "operation": "invalid-operation",
            "timeout": 999
        }
        
        with pytest.raises(ValueError):
            validate_power_operation(invalid_config)


class TestUserManagement:
    """Test user management validation."""
    
    def test_valid_user_config(self, sample_user_config):
        """Test valid user configuration."""
        from src.utils.validation import validate_user_config
        
        result = validate_user_config(sample_user_config)
        assert result["username"] == "testuser"
        assert result["privilege"] == "Administrator"
        assert result["enabled"] is True
    
    def test_user_privilege_levels(self):
        """Test different user privilege levels."""
        from src.utils.validation import validate_user_config
        
        valid_privileges = ["Administrator", "Operator", "ReadOnly"]
        
        for privilege in valid_privileges:
            config = {
                "username": "testuser",
                "password": "securepassword123",
                "privilege": privilege,
                "enabled": True
            }
            result = validate_user_config(config)
            assert result["privilege"] == privilege
    
    def test_invalid_username(self):
        """Test invalid username validation."""
        from src.utils.validation import validate_user_config
        
        invalid_config = {
            "username": "a",  # Too short
            "password": "securepassword123",
            "privilege": "Administrator"
        }
        
        with pytest.raises(ValueError):
            validate_user_config(invalid_config)
    
    def test_invalid_password(self):
        """Test invalid password validation."""
        from src.utils.validation import validate_user_config
        
        invalid_config = {
            "username": "testuser",
            "password": "123",  # Too short
            "privilege": "Administrator"
        }
        
        with pytest.raises(ValueError):
            validate_user_config(invalid_config)


class TestIDracClientMock:
    """Test iDRAC client with mocks."""
    
    @patch('src.idrac_client.requests.get')
    def test_get_system_info(self, mock_get, mock_idrac_client):
        """Test getting system information."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "Model": "PowerEdge R740",
            "ServiceTag": "ABC1234"
        }
        
        result = mock_idrac_client.get_system_info()
        assert "Model" in result
        assert "ServiceTag" in result
    
    @patch('src.idrac_client.requests.get')
    def test_get_power_state(self, mock_get, mock_idrac_client):
        """Test getting power state."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"PowerState": "On"}
        
        result = mock_idrac_client.get_power_state()
        assert result["PowerState"] == "On"
    
    @patch('src.idrac_client.requests.post')
    def test_set_power_state(self, mock_post, mock_idrac_client):
        """Test setting power state."""
        mock_post.return_value.status_code = 204
        
        result = mock_idrac_client.set_power_state()
        assert result["status"] == "success"
