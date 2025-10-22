"""Pytest configuration and fixtures for Proxmox MCP tests."""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_proxmox_config():
    """Mock Proxmox configuration."""
    return {
        "host": "192.168.1.100",
        "port": 8006,
        "username": "root@pam",
        "password": "testpassword",
        "node": "pve",
        "ssl_verify": False
    }


@pytest.fixture
def mock_proxmox_client(mock_proxmox_config):
    """Mock Proxmox client."""
    from src.proxmox_client import ProxmoxClient
    
    client = Mock(spec=ProxmoxClient)
    client.config = mock_proxmox_config
    client.host = mock_proxmox_config["host"]
    client.username = mock_proxmox_config["username"]
    client.ticket = "test-ticket"
    client.csrf_token = "test-csrf"
    
    # Mock methods
    client.test_connection.return_value = {"status": "success", "version": "8.0.0"}
    client.get_version.return_value = {"data": {"version": "8.0.0"}}
    client.list_nodes.return_value = [{"node": "pve", "status": "online"}]
    client.list_vms.return_value = [{"vmid": 100, "name": "test-vm", "status": "running"}]
    client.list_containers.return_value = [{"vmid": 101, "name": "test-ct", "status": "running"}]
    
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
