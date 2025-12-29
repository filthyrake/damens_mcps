"""Pytest configuration and fixtures for Proxmox MCP tests."""

import os
import sys

# Add the project root directory to the Python path for CI
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_proxmox_config():
    """Mock Proxmox configuration."""
    return {
        "host": "192.168.1.100",
        "port": 8006,
        "protocol": "https",
        "username": "root@pam",
        "password": "testpassword",
        "realm": "pam",
        "node": "pve",
        "ssl_verify": False
    }


@pytest.fixture
def mock_proxmox_client(mock_proxmox_config, monkeypatch):
    """Mock Proxmox client."""
    from src.proxmox_client import ProxmoxClient
    
    # Mock the _authenticate method to avoid actual API calls
    def mock_authenticate(self):
        """Mock authentication to prevent actual API calls during testing."""
        pass
    
    monkeypatch.setattr(ProxmoxClient, '_authenticate', mock_authenticate)
    
    # Create a real client instance but with mocked authentication
    client = ProxmoxClient(
        host=mock_proxmox_config["host"],
        port=mock_proxmox_config["port"],
        protocol=mock_proxmox_config["protocol"],
        username=mock_proxmox_config["username"],
        password=mock_proxmox_config["password"],
        realm=mock_proxmox_config["realm"],
        ssl_verify=mock_proxmox_config["ssl_verify"]
    )
    
    return client


@pytest.fixture
def sample_vm_config():
    """Sample VM configuration for tests."""
    return {
        "node": "pve",
        "vmid": 100,
        "name": "test-vm",
        "cores": 2,
        "memory": 2048,
        "disk": "32G",
        "network": "virtio,bridge=vmbr0"
    }


@pytest.fixture
def sample_container_config():
    """Sample container configuration for tests."""
    return {
        "node": "pve",
        "vmid": 101,
        "name": "test-container",
        "ostemplate": "local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz",
        "cores": 1,
        "memory": 512,
        "rootfs": "local-lvm:8",
        "network": "name=eth0,bridge=vmbr0"
    }


@pytest.fixture
def mock_server_config(tmp_path):
    """Create a temporary config file for testing."""
    import json
    
    config = {
        "host": "192.168.1.100",
        "port": 8006,
        "username": "root@pam",
        "password": "testpassword",
        "node": "pve",
        "ssl_verify": False
    }
    
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    
    return str(config_file)
