"""Pytest configuration and fixtures for pfSense MCP tests."""

import os
import sys

# Add the project root directory to the Python path for CI
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_pfsense_config():
    """Mock pfSense configuration."""
    return {
        "host": "192.168.1.1",
        "port": 443,
        "api_key": "test-api-key",
        "api_secret": "test-api-secret",
        "ssl_verify": False
    }


@pytest.fixture
def mock_pfsense_client(mock_pfsense_config):
    """Mock pfSense client."""
    from src.pfsense_client import HTTPPfSenseClient
    
    client = Mock(spec=HTTPPfSenseClient)
    client.config = mock_pfsense_config
    client.host = mock_pfsense_config["host"]
    client.api_key = mock_pfsense_config["api_key"]
    
    # Mock methods
    client.test_connection.return_value = {"status": "success"}
    client.get_system_info.return_value = {"version": "2.7.0"}
    client.get_interfaces.return_value = [{"name": "wan", "status": "up"}]
    client.get_firewall_rules.return_value = [{"id": "1", "description": "Test rule"}]
    
    return client


@pytest.fixture
def sample_firewall_rule():
    """Sample firewall rule for tests."""
    return {
        "interface": "wan",
        "protocol": "tcp",
        "source": "any",
        "destination": "any",
        "port": "80",
        "action": "pass",
        "description": "Test rule"
    }
