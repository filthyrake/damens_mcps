"""Pytest configuration and fixtures for TrueNAS MCP tests - extending existing conftest."""

import pytest
from unittest.mock import AsyncMock, MagicMock


# The existing tests already have some fixtures, adding more comprehensive ones

@pytest.fixture
def mock_truenas_api_responses():
    """Mock API responses for TrueNAS."""
    return {
        "pools": [
            {"name": "tank", "status": "ONLINE", "size": 1000000000000},
            {"name": "backup", "status": "ONLINE", "size": 500000000000}
        ],
        "datasets": [
            {"name": "tank/data", "type": "FILESYSTEM"},
            {"name": "tank/media", "type": "FILESYSTEM"}
        ],
        "interfaces": [
            {"name": "em0", "state": {"link_state": "LINK_STATE_UP"}},
            {"name": "em1", "state": {"link_state": "LINK_STATE_DOWN"}}
        ],
        "services": [
            {"service": "ssh", "state": "RUNNING"},
            {"service": "nfs", "state": "STOPPED"}
        ]
    }


@pytest.fixture
def sample_pool_config():
    """Sample pool configuration for tests."""
    return {
        "name": "test-pool",
        "topology": {
            "data": [
                {"type": "STRIPE", "disks": ["sda", "sdb"]}
            ]
        }
    }


@pytest.fixture
def sample_dataset_config():
    """Sample dataset configuration for tests."""
    return {
        "name": "test-pool/test-dataset",
        "type": "FILESYSTEM",
        "compression": "lz4",
        "atime": "off"
    }
