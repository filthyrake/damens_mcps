"""Tests for validation constants in pfSense MCP Server."""

import pytest
from src.utils.validation import (
    MAX_PACKAGE_NAME_LENGTH,
    MAX_SERVICE_NAME_LENGTH,
    MAX_BACKUP_NAME_LENGTH,
    MAX_ID_LENGTH,
    MIN_PORT,
    MAX_PORT,
    MIN_VLAN_ID,
    MAX_VLAN_ID,
)


class TestValidationConstants:
    """Test that validation constants have correct values."""
    
    def test_name_length_constants(self):
        """Test name length limit constants."""
        assert MAX_PACKAGE_NAME_LENGTH == 255, "MAX_PACKAGE_NAME_LENGTH should be 255"
        assert MAX_SERVICE_NAME_LENGTH == 128, "MAX_SERVICE_NAME_LENGTH should be 128"
        assert MAX_BACKUP_NAME_LENGTH == 255, "MAX_BACKUP_NAME_LENGTH should be 255"
        assert MAX_ID_LENGTH == 128, "MAX_ID_LENGTH should be 128"
    
    def test_port_constants(self):
        """Test port range constants."""
        assert MIN_PORT == 1, "MIN_PORT should be 1"
        assert MAX_PORT == 65535, "MAX_PORT should be 65535"
        assert MIN_PORT < MAX_PORT, "MIN_PORT should be less than MAX_PORT"
    
    def test_vlan_constants(self):
        """Test VLAN ID range constants."""
        assert MIN_VLAN_ID == 1, "MIN_VLAN_ID should be 1"
        assert MAX_VLAN_ID == 4094, "MAX_VLAN_ID should be 4094 (802.1Q standard)"
        assert MIN_VLAN_ID < MAX_VLAN_ID, "MIN_VLAN_ID should be less than MAX_VLAN_ID"
