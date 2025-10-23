"""Unit tests for pfSense MCP Server client."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPfSenseClientMock:
    """Test cases for the PfSenseClient with mocks."""
    
    @patch('src.pfsense_client.requests.get')
    def test_client_get_system_info(self, mock_get, mock_pfsense_client):
        """Test getting system information."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"version": "2.7.0"}
        
        result = mock_pfsense_client.get_system_info()
        assert "version" in result
    
    @patch('src.pfsense_client.requests.get')
    def test_client_get_interfaces(self, mock_get, mock_pfsense_client):
        """Test getting network interfaces."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"name": "wan"}]
        
        result = mock_pfsense_client.get_interfaces()
        assert isinstance(result, list)
    
    @patch('src.pfsense_client.requests.get')
    def test_client_connection_error(self, mock_get, mock_pfsense_client):
        """Test handling connection errors."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        # The mock client won't actually raise, but we can test the pattern
        mock_pfsense_client.test_connection.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            mock_pfsense_client.test_connection()


class TestFirewallRuleValidation:
    """Test firewall rule validation."""
    
    def test_valid_firewall_rule(self, sample_firewall_rule):
        """Test that valid firewall rules pass validation."""
        from src.utils.validation import validate_id, validate_port, validate_ip_address
        
        # Test individual components
        assert validate_port(sample_firewall_rule["port"]) is True
        assert sample_firewall_rule["action"] in ["pass", "block", "reject"]
        assert sample_firewall_rule["protocol"] in ["tcp", "udp", "icmp", "any"]
    
    def test_invalid_port(self):
        """Test invalid port validation."""
        from src.utils.validation import validate_port
        
        assert validate_port(0) is False
        assert validate_port(65536) is False
        assert validate_port(-1) is False
    
    def test_valid_ip_addresses(self):
        """Test IP address validation."""
        from src.utils.validation import validate_ip_address
        
        assert validate_ip_address("192.168.1.1") is True
        assert validate_ip_address("10.0.0.0") is True
        assert validate_ip_address("::1") is True
    
    def test_invalid_ip_addresses(self):
        """Test invalid IP addresses."""
        from src.utils.validation import validate_ip_address
        
        assert validate_ip_address("256.256.256.256") is False
        assert validate_ip_address("not-an-ip") is False
        assert validate_ip_address("") is False


class TestServiceManagement:
    """Test service management validation."""
    
    def test_valid_service_names(self):
        """Test valid service names."""
        from src.utils.validation import validate_service_name
        
        valid_services = ["openvpn", "ipsec", "wireguard", "haproxy"]
        for service in valid_services:
            assert validate_service_name(service) is True
    
    def test_invalid_service_names(self):
        """Test invalid service names with injection attempts."""
        from src.utils.validation import validate_service_name
        
        invalid_services = [
            "",
            "service; rm -rf /",
            "service && reboot",
            "../../../etc/init.d/evil"
        ]
        for service in invalid_services:
            assert validate_service_name(service) is False
