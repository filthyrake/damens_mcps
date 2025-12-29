"""Pytest configuration and fixtures for TrueNAS MCP tests."""

import os
import sys

# Add the project root directory to the Python path for CI
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_truenas_config():
    """Mock TrueNAS configuration."""
    return {
        "host": "192.168.1.100",
        "port": 443,
        "api_key": "test-api-key",
        "ssl_verify": False
    }


@pytest.fixture
def mock_truenas_client(mock_truenas_config):
    """Mock TrueNAS client."""
    client = MagicMock()
    client.config = mock_truenas_config
    client.host = mock_truenas_config["host"]
    client.api_key = mock_truenas_config["api_key"]

    # Mock common methods
    client.test_connection.return_value = {"status": "success"}
    client.get_system_info.return_value = {"hostname": "truenas", "version": "13.0"}

    return client
