"""Validation utilities for TrueNAS MCP server."""

import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class TrueNASConfigValidator(BaseModel):
    """Validator for TrueNAS configuration."""
    host: str = Field(..., description="TrueNAS host address")
    port: int = Field(443, ge=1, le=65535, description="TrueNAS port")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    
    class Config:
        extra = "forbid"


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate TrueNAS configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        validator = TrueNASConfigValidator(**config)
        return validator.dict()
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ValueError(f"Invalid configuration: {e}")


def validate_api_response(response: Any, expected_type: Optional[type] = None) -> bool:
    """Validate API response.
    
    Args:
        response: API response to validate
        expected_type: Expected type of response
        
    Returns:
        True if response is valid, False otherwise
    """
    if response is None:
        logger.warning("API response is None")
        return False
    
    if expected_type and not isinstance(response, expected_type):
        logger.warning(f"API response type mismatch: expected {expected_type}, got {type(response)}")
        return False
    
    return True


def validate_pool_config(pool_data: Dict[str, Any]) -> bool:
    """Validate storage pool configuration.
    
    Args:
        pool_data: Pool configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ["name", "disks", "raid_type"]
    
    for field in required_fields:
        if field not in pool_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate RAID type
    valid_raid_types = ["mirror", "stripe", "raidz1", "raidz2", "raidz3"]
    if pool_data["raid_type"] not in valid_raid_types:
        logger.error(f"Invalid RAID type: {pool_data['raid_type']}")
        return False
    
    # Validate disks
    if not isinstance(pool_data["disks"], list) or len(pool_data["disks"]) == 0:
        logger.error("Disks must be a non-empty list")
        return False
    
    return True


def validate_dataset_config(dataset_data: Dict[str, Any]) -> bool:
    """Validate dataset configuration.
    
    Args:
        dataset_data: Dataset configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ["name", "pool", "type"]
    
    for field in required_fields:
        if field not in dataset_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate dataset type
    valid_types = ["FILESYSTEM", "VOLUME"]
    if dataset_data["type"] not in valid_types:
        logger.error(f"Invalid dataset type: {dataset_data['type']}")
        return False
    
    return True


def validate_user_config(user_data: Dict[str, Any]) -> bool:
    """Validate user configuration.
    
    Args:
        user_data: User configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ["username", "full_name", "password"]
    
    for field in required_fields:
        if field not in user_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate username format
    username = user_data["username"]
    if not username or len(username) < 1:
        logger.error("Username cannot be empty")
        return False
    
    # Validate password strength (basic)
    password = user_data["password"]
    if not password or len(password) < 8:
        logger.error("Password must be at least 8 characters long")
        return False
    
    return True


def validate_network_config(network_data: Dict[str, Any]) -> bool:
    """Validate network configuration.
    
    Args:
        network_data: Network configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    # Validate IP address format (basic)
    if "ip_address" in network_data:
        ip = network_data["ip_address"]
        if not _is_valid_ip_address(ip):
            logger.error(f"Invalid IP address: {ip}")
            return False
    
    # Validate netmask format (basic)
    if "netmask" in network_data:
        netmask = network_data["netmask"]
        if not _is_valid_ip_address(netmask):
            logger.error(f"Invalid netmask: {netmask}")
            return False
    
    # Validate MTU
    if "mtu" in network_data:
        mtu = network_data["mtu"]
        if not isinstance(mtu, int) or mtu < 68 or mtu > 9000:
            logger.error(f"Invalid MTU: {mtu}")
            return False
    
    return True


def _is_valid_ip_address(ip: str) -> bool:
    """Check if string is a valid IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    except Exception:
        return False


def sanitize_input(input_data: Any) -> Any:
    """Sanitize input data to prevent injection attacks.
    
    Args:
        input_data: Input data to sanitize
        
    Returns:
        Sanitized input data
    """
    if isinstance(input_data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')']
        for char in dangerous_chars:
            input_data = input_data.replace(char, '')
        return input_data.strip()
    
    elif isinstance(input_data, dict):
        return {key: sanitize_input(value) for key, value in input_data.items()}
    
    elif isinstance(input_data, list):
        return [sanitize_input(item) for item in input_data]
    
    else:
        return input_data


def validate_permissions(permissions: Dict[str, Any]) -> bool:
    """Validate permissions object.
    
    Args:
        permissions: Permissions object to validate
        
    Returns:
        True if permissions are valid, False otherwise
    """
    if not isinstance(permissions, dict):
        logger.error("Permissions must be a dictionary")
        return False
    
    # Add specific permission validation logic here
    # This is a placeholder for future implementation
    
    return True
