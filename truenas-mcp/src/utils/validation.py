"""Validation utilities for TrueNAS MCP server."""

import logging
import re
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
    
    DEPRECATED: Use specific validation functions instead.
    This function uses a blacklist approach which is not secure.
    
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


def validate_resource_id(resource_id: str) -> bool:
    """Validate resource ID to prevent path traversal attacks.
    
    Resource IDs should only contain alphanumeric characters,
    hyphens, underscores, and dots. No path separators allowed.
    
    Args:
        resource_id: Resource ID to validate (pool_id, dataset_id, etc.)
        
    Returns:
        True if valid, False otherwise
    """
    if not resource_id or not isinstance(resource_id, str):
        logger.error("Resource ID must be a non-empty string")
        return False
    
    # Prevent path traversal - no slashes, no "..", etc.
    if '/' in resource_id or '\\' in resource_id or '..' in resource_id:
        logger.error(f"Resource ID contains path traversal characters: {resource_id}")
        return False
    
    # Whitelist: alphanumeric, hyphen, underscore, dot
    # Allow reasonable length (1-255 characters)
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]{0,254}$'
    if not re.match(pattern, resource_id):
        logger.error(f"Resource ID contains invalid characters: {resource_id}")
        return False
    
    return True


def validate_pool_id(pool_id: str) -> bool:
    """Validate pool ID.
    
    Args:
        pool_id: Pool ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return validate_resource_id(pool_id)


def validate_dataset_id(dataset_id: str) -> bool:
    """Validate dataset ID.
    
    Args:
        dataset_id: Dataset ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return validate_resource_id(dataset_id)


def validate_service_id(service_id: Union[str, int]) -> bool:
    """Validate service ID.
    
    Args:
        service_id: Service ID to validate (can be string or int)
        
    Returns:
        True if valid, False otherwise
    """
    if isinstance(service_id, int):
        return service_id > 0
    elif isinstance(service_id, str):
        return validate_resource_id(service_id)
    else:
        logger.error(f"Service ID must be string or int: {type(service_id)}")
        return False


def validate_user_id(user_id: Union[str, int]) -> bool:
    """Validate user ID.
    
    Args:
        user_id: User ID to validate (can be string or int)
        
    Returns:
        True if valid, False otherwise
    """
    if isinstance(user_id, int):
        return user_id > 0
    elif isinstance(user_id, str):
        return validate_resource_id(user_id)
    else:
        logger.error(f"User ID must be string or int: {type(user_id)}")
        return False


def validate_interface_id(interface_id: str) -> bool:
    """Validate network interface ID.
    
    Args:
        interface_id: Interface ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return validate_resource_id(interface_id)


def validate_snapshot_id(snapshot_id: str) -> bool:
    """Validate snapshot ID.
    
    Args:
        snapshot_id: Snapshot ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return validate_resource_id(snapshot_id)


def validate_app_id(app_id: str) -> bool:
    """Validate application ID.
    
    Args:
        app_id: Application ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return validate_resource_id(app_id)


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
