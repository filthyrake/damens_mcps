"""Pytest configuration and fixtures for iDRAC MCP tests."""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_idrac_config():
    """Mock iDRAC configuration."""
    return {
        "host": "192.168.1.100",
        "port": 443,
        "protocol": "https",
        "username": "root",
        "password": "testpassword",
        "ssl_verify": False
    }


@pytest.fixture
def mock_multi_server_config():
    """Mock configuration for multiple iDRAC servers."""
    return {
        "idrac_servers": {
            "server1": {
                "host": "192.168.1.100",
                "port": 443,
                "protocol": "https",
                "username": "root",
                "password": "password1",
                "ssl_verify": False
            },
            "server2": {
                "host": "192.168.1.101",
                "port": 443,
                "protocol": "https",
                "username": "root",
                "password": "password2",
                "ssl_verify": False
            }
        },
        "default_server": "server1"
    }


@pytest.fixture
def mock_idrac_client(mock_idrac_config):
    """Mock iDRAC client."""
    from src.idrac_client import IDracClient
    
    client = Mock(spec=IDracClient)
    client.config = mock_idrac_config
    client.host = mock_idrac_config["host"]
    client.username = mock_idrac_config["username"]
    
    # Mock methods
    client.get_system_info.return_value = {"Model": "PowerEdge R740", "ServiceTag": "ABC1234"}
    client.get_power_state.return_value = {"PowerState": "On"}
    client.set_power_state.return_value = {"status": "success"}
    client.get_storage_info.return_value = {"Controllers": [{"Id": "RAID.Integrated.1"}]}
    
    return client


@pytest.fixture
def sample_power_operation():
    """Sample power operation for tests."""
    return {
        "operation": "on",
        "force": False,
        "timeout": 60
    }


@pytest.fixture
def sample_user_config():
    """Sample user configuration for tests."""
    return {
        "username": "testuser",
        "password": "securepassword123",
        "privilege": "Administrator",
        "enabled": True
    }
