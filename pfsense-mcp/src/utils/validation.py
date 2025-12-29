"""
Validation utilities for pfSense MCP Server.
"""

import html
import ipaddress
import re
from typing import Any, Dict, List, Union

# Name length limits
MAX_PACKAGE_NAME_LENGTH = 255  # pfSense API limitation
MAX_SERVICE_NAME_LENGTH = 128  # System service name limit
MAX_BACKUP_NAME_LENGTH = 255  # Backup name maximum length
MAX_ID_LENGTH = 128  # Maximum length for generic IDs (rules, VLANs, etc.)

# Network port limits
MIN_PORT = 1  # Minimum valid TCP/UDP port
MAX_PORT = 65535  # Maximum valid TCP/UDP port

# VLAN ID limits
MIN_VLAN_ID = 1  # Minimum valid VLAN ID
MAX_VLAN_ID = 4094  # Maximum valid VLAN ID (802.1Q standard)


def validate_ip_address(ip: str) -> bool:
    """
    Validate if a string is a valid IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_cidr(cidr: str) -> bool:
    """
    Validate if a string is a valid CIDR notation (e.g., 192.168.1.0/24).
    
    Args:
        cidr: CIDR notation string to validate
        
    Returns:
        True if valid CIDR notation, False otherwise
    """
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except (ValueError, TypeError):
        return False


def validate_ip_or_cidr(address: str) -> bool:
    """
    Validate if a string is a valid IP address or CIDR notation.
    
    Args:
        address: IP address or CIDR notation string to validate
        
    Returns:
        True if valid IP or CIDR, False otherwise
    """
    return validate_ip_address(address) or validate_cidr(address)


def validate_port(port: Union[int, str]) -> bool:
    """
    Validate if a port number is valid.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid port (1-65535), False otherwise
    """
    try:
        port_num = int(port)
        return MIN_PORT <= port_num <= MAX_PORT
    except (ValueError, TypeError):
        return False


def validate_port_range(port_range: str) -> bool:
    """
    Validate if a port range is valid (e.g., "8000-9000" or "80").
    
    Args:
        port_range: Port range string to validate
        
    Returns:
        True if valid port or port range, False otherwise
    """
    if not isinstance(port_range, str):
        return False
    
    # Check if it's a single port
    if '-' not in port_range:
        return validate_port(port_range)
    
    # Check if it's a port range
    parts = port_range.split('-')
    if len(parts) != 2:
        return False
    
    try:
        start_port = int(parts[0].strip())
        end_port = int(parts[1].strip())
        
        # Validate both ports are in valid range
        if not (MIN_PORT <= start_port <= MAX_PORT and MIN_PORT <= end_port <= MAX_PORT):
            return False
        
        # Start port should be less than or equal to end port
        return start_port <= end_port
    except (ValueError, TypeError):
        return False


def validate_protocol(protocol: str) -> bool:
    """
    Validate if a protocol string is valid for firewall rules.
    
    Args:
        protocol: Protocol string to validate (e.g., 'tcp', 'udp', 'icmp', 'any')
        
    Returns:
        True if valid protocol, False otherwise
    """
    if not protocol or not isinstance(protocol, str):
        return False
    
    # Common protocols used in pfSense
    valid_protocols = [
        'tcp', 'udp', 'icmp', 'esp', 'ah', 'gre', 'ipv6', 'igmp',
        'pim', 'ospf', 'sctp', 'any', 'icmpv6', 'tcp/udp'
    ]
    
    # Protocol must be alphanumeric or forward slash (for tcp/udp)
    # No special characters that could be used for injection
    if not re.match(r'^[a-zA-Z0-9/]+$', protocol):
        return False
    
    # Check if it's in the list of valid protocols (case-insensitive)
    return protocol.lower() in valid_protocols


def validate_mac_address(mac: str) -> bool:
    """
    Validate if a string is a valid MAC address.
    
    Args:
        mac: MAC address string to validate
        
    Returns:
        True if valid MAC address, False otherwise
    """
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(mac_pattern.match(mac))


def validate_vlan_id(vlan_id: Union[int, str]) -> bool:
    """
    Validate if a VLAN ID is valid.
    
    Args:
        vlan_id: VLAN ID to validate
        
    Returns:
        True if valid VLAN ID (1-4094), False otherwise
    """
    try:
        vlan_num = int(vlan_id)
        return MIN_VLAN_ID <= vlan_num <= MAX_VLAN_ID
    except (ValueError, TypeError):
        return False


def validate_firewall_rule_params(params: Dict[str, Any]) -> List[str]:
    """
    Validate firewall rule parameters.

    Args:
        params: Dictionary of firewall rule parameters

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    valid_actions = ['pass', 'block', 'reject']
    valid_directions = ['in', 'out']
    valid_protocols = [
        'tcp', 'udp', 'icmp', 'esp', 'ah', 'gre', 'ipv6', 'igmp',
        'pim', 'ospf', 'sctp', 'any', 'icmpv6', 'tcp/udp'
    ]

    # Required fields
    required_fields = ['action', 'interface', 'direction']
    for field in required_fields:
        if field not in params or not params[field]:
            errors.append(
                f"Missing required field: '{field}'. "
                f"Required fields for firewall rules: {', '.join(required_fields)}"
            )

    # Validate action
    if 'action' in params and params['action']:
        action = params['action']
        if action not in valid_actions:
            errors.append(
                f"Invalid action '{action}'. "
                f"Valid options: {', '.join(valid_actions)}. "
                "Use 'pass' to allow traffic, 'block' to silently drop, 'reject' to drop with response"
            )

    # Validate direction
    if 'direction' in params and params['direction']:
        direction = params['direction']
        if direction not in valid_directions:
            errors.append(
                f"Invalid direction '{direction}'. "
                f"Valid options: {', '.join(valid_directions)}. "
                "Use 'in' for incoming traffic, 'out' for outgoing traffic"
            )

    # Validate protocol if provided
    if 'protocol' in params and params['protocol']:
        protocol = params['protocol']
        if not validate_protocol(protocol):
            errors.append(
                f"Invalid protocol '{protocol}'. "
                f"Valid options: {', '.join(valid_protocols)}. "
                "Common choices: tcp (web, SSH), udp (DNS, VPN), icmp (ping), any (all protocols)"
            )

    # Validate source/destination if provided (supports both IP and CIDR)
    if 'source' in params and params['source']:
        source = params['source']
        if not validate_ip_or_cidr(source) and source != 'any':
            errors.append(
                f"Invalid source address '{source}'. "
                "Must be a valid IPv4/IPv6 address, CIDR notation, or 'any'. "
                "Examples: 192.168.1.100, 10.0.0.0/8, 2001:db8::1, any"
            )

    if 'destination' in params and params['destination']:
        destination = params['destination']
        if not validate_ip_or_cidr(destination) and destination != 'any':
            errors.append(
                f"Invalid destination address '{destination}'. "
                "Must be a valid IPv4/IPv6 address, CIDR notation, or 'any'. "
                "Examples: 192.168.1.100, 10.0.0.0/8, 2001:db8::1, any"
            )

    # Validate port if provided (supports both single port and ranges)
    if 'port' in params and params['port']:
        port_value = str(params['port'])
        if not validate_port_range(port_value):
            errors.append(
                f"Invalid port '{port_value}'. "
                f"Must be a port number ({MIN_PORT}-{MAX_PORT}) or range. "
                "Examples: 80, 443, 8000-9000, 22"
            )

    return errors


def validate_vlan_params(params: Dict[str, Any]) -> List[str]:
    """
    Validate VLAN parameters.

    Args:
        params: Dictionary of VLAN parameters

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Required fields
    if 'vlan_id' not in params:
        errors.append(
            "Missing required field: 'vlan_id'. "
            f"VLAN ID must be an integer between {MIN_VLAN_ID} and {MAX_VLAN_ID}. "
            "Example: 10, 100, 200"
        )
    else:
        vlan_id = params['vlan_id']
        if not validate_vlan_id(vlan_id):
            errors.append(
                f"Invalid VLAN ID '{vlan_id}'. "
                f"Must be an integer between {MIN_VLAN_ID} and {MAX_VLAN_ID} (IEEE 802.1Q standard). "
                "Common VLANs: 10 (management), 20 (servers), 100 (users), 200 (guests)"
            )

    if 'interface' not in params or not params['interface']:
        errors.append(
            "Missing required field: 'interface'. "
            "Specify the parent interface for this VLAN. "
            "Example: em0, igb0, ix0"
        )

    return errors


def sanitize_string(value: str) -> str:
    """
    Sanitize a string value for safe use in API calls.
    
    DEPRECATED: Use specific validation functions instead (validate_package_name, validate_service_name, etc.)
    This function will be removed in a future version. Please migrate to the appropriate validator.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
        
    Raises:
        DeprecationWarning: This function is deprecated
    """
    import warnings
    warnings.warn(
        "sanitize_string() is deprecated. Use validate_package_name(), validate_service_name(), "
        "validate_backup_name(), or validate_id() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    if not value:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(value))
    return sanitized.strip()


def validate_package_name(name: str) -> bool:
    """
    Validate package name using whitelist approach.
    
    Package names should only contain alphanumeric characters, hyphens, underscores, and dots.
    This prevents command injection attacks.
    
    Args:
        name: Package name to validate
        
    Returns:
        True if valid package name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Only allow alphanumeric, hyphens, underscores, and dots
    # This is safe for pfSense package manager
    pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, name)) and len(name) <= MAX_PACKAGE_NAME_LENGTH


def validate_service_name(name: str) -> bool:
    """
    Validate service name using whitelist approach.
    
    Service names should only contain alphanumeric characters, hyphens, and underscores.
    This prevents command injection attacks.
    
    Args:
        name: Service name to validate
        
    Returns:
        True if valid service name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Only allow alphanumeric, hyphens, and underscores
    # Common service names: openvpn, ipsec, wireguard, etc.
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name)) and len(name) <= MAX_SERVICE_NAME_LENGTH


def validate_backup_name(name: str) -> bool:
    """
    Validate backup name using whitelist approach.
    
    Backup names should only contain alphanumeric characters, hyphens, underscores, and dots.
    
    Args:
        name: Backup name to validate
        
    Returns:
        True if valid backup name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Only allow alphanumeric, hyphens, underscores, and dots
    pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, name)) and len(name) <= MAX_BACKUP_NAME_LENGTH


def validate_id(id_value: str) -> bool:
    """
    Validate generic ID string (for rules, VLANs, backups, etc.).
    
    IDs should only contain alphanumeric characters, hyphens, and underscores.
    
    Args:
        id_value: ID string to validate
        
    Returns:
        True if valid ID, False otherwise
    """
    if not id_value or not isinstance(id_value, str):
        return False
    
    # Only allow alphanumeric, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, id_value)) and len(id_value) <= MAX_ID_LENGTH


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate pfSense configuration parameters.

    Args:
        config: Configuration dictionary

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Required fields
    if 'host' not in config or not config['host']:
        errors.append("Missing required field: host")
    elif not validate_ip_address(config['host']) and not re.match(r'^[a-zA-Z0-9.-]+$', config['host']):
        errors.append("Invalid host format")

    if 'port' in config and not validate_port(config['port']):
        errors.append("Invalid port number")

    # Validate authentication
    has_api_key = 'api_key' in config and config['api_key']
    has_credentials = ('username' in config and config['username'] and
                      'password' in config and config['password'])

    if not has_api_key and not has_credentials:
        errors.append("Either api_key or username/password must be provided")

    return errors


def sanitize_for_api(value: str) -> str:
    """
    Sanitize a string value for safe use in API calls.
    
    Removes dangerous characters and escapes HTML entities to prevent injection attacks.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not value or not isinstance(value, str):
        return ""
    
    # Remove control characters and dangerous patterns
    # Remove null bytes
    cleaned = value.replace('\x00', '')
    
    # Remove other control characters except newlines and tabs
    cleaned = ''.join(char for char in cleaned if char in ('\n', '\t') or ord(char) >= 32)
    
    # Remove dangerous shell characters that could be used for command injection
    dangerous_chars = ['<', '>', '"', "'", ';', '|', '`', '$', '(', ')', '&', '\r']
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    
    # Escape HTML entities
    cleaned = html.escape(cleaned)
    
    return cleaned.strip()