"""Input validation utilities for Proxmox MCP Server."""

import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ValidationError, validator


class VMConfig(BaseModel):
    """Validation model for VM configuration."""
    
    name: str
    node: str
    cores: int = 1
    memory: int = 512
    storage: str = "local-lvm"
    disk_size: str = "10G"
    network_model: str = "virtio"
    bridge: str = "vmbr0"
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('VM name must contain only alphanumeric characters, hyphens, and underscores')
        if len(v) > 128:
            raise ValueError('VM name must not exceed 128 characters')
        return v
    
    @validator('cores')
    def validate_cores(cls, v):
        if not isinstance(v, int):
            try:
                v = int(v)
            except (ValueError, TypeError):
                raise ValueError('CPU cores must be an integer')
        if v < 1 or v > 128:
            raise ValueError('CPU cores must be between 1 and 128')
        return v
    
    @validator('memory')
    def validate_memory(cls, v):
        if not isinstance(v, int):
            try:
                v = int(v)
            except (ValueError, TypeError):
                raise ValueError('Memory must be an integer')
        if v < 64 or v > 1048576:  # 64MB to 1TB
            raise ValueError('Memory must be between 64MB and 1TB (1048576MB)')
        return v
    
    @validator('disk_size')
    def validate_disk_size(cls, v):
        if not re.match(r'^\d+[KMGTP]?$', v):
            raise ValueError('Disk size must be in format: number[KMGTP] (e.g., 10G, 100M)')
        return v


class ContainerConfig(BaseModel):
    """Validation model for container configuration."""
    
    name: str
    node: str
    ostemplate: str
    cores: int = 1
    memory: int = 512
    storage: str = "local-lvm"
    disk_size: str = "10G"
    password: Optional[str] = None
    ssh_keys: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Container name must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @validator('ostemplate')
    def validate_ostemplate(cls, v):
        if not v or not v.strip():
            raise ValueError('OS template is required')
        return v


def validate_vm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate VM configuration parameters.
    
    Args:
        config: VM configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValidationError: If configuration is invalid
    """
    try:
        vm_config = VMConfig(**config)
        return vm_config.dict()
    except ValidationError as e:
        raise ValueError(f"Invalid VM configuration: {e}")


def validate_container_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate container configuration parameters.
    
    Args:
        config: Container configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValidationError: If configuration is invalid
    """
    try:
        container_config = ContainerConfig(**config)
        return container_config.dict()
    except ValidationError as e:
        raise ValueError(f"Invalid container configuration: {e}")


def is_valid_vmid(vmid: Union[int, str]) -> bool:
    """Check if VM/Container ID is valid (boolean check).
    
    Args:
        vmid: VM/Container ID
        
    Returns:
        True if valid, False otherwise
    """
    try:
        vmid_int = int(vmid)
        return 100 <= vmid_int <= 999999
    except (ValueError, TypeError):
        return False


def validate_vmid(vmid: Union[int, str]) -> int:
    """Validate and convert VM/Container ID to integer.
    
    Args:
        vmid: VM/Container ID
        
    Returns:
        Validated VM/Container ID as integer
        
    Raises:
        ValueError: If VMID is invalid
    """
    try:
        vmid_int = int(vmid)
    except (ValueError, TypeError):
        raise ValueError("VMID must be a valid integer between 100 and 999999")
    
    if vmid_int < 100 or vmid_int > 999999:
        raise ValueError("VMID must be between 100 and 999999")
    
    return vmid_int


def is_valid_node_name(node: str) -> bool:
    """Check if node name is valid (boolean check).
    
    Args:
        node: Node name
        
    Returns:
        True if valid, False otherwise
    """
    if not node or not isinstance(node, str):
        return False
    return bool(re.match(r'^[a-zA-Z0-9\-_]+$', node)) and len(node) <= 128


def validate_node_name(node: str) -> str:
    """Validate and return node name.
    
    Args:
        node: Node name
        
    Returns:
        Validated node name
        
    Raises:
        ValueError: If node name is invalid
    """
    if not is_valid_node_name(node):
        raise ValueError("Node name must contain only alphanumeric characters, hyphens, and underscores")
    return node


def is_valid_storage_name(storage: str) -> bool:
    """Check if storage name is valid (boolean check).
    
    Args:
        storage: Storage name
        
    Returns:
        True if valid, False otherwise
    """
    if not storage or not isinstance(storage, str):
        return False
    return bool(re.match(r'^[a-zA-Z0-9\-_]+$', storage)) and len(storage) <= 128


def validate_storage_name(storage: str) -> str:
    """Validate and return storage name.
    
    Args:
        storage: Storage name
        
    Returns:
        Validated storage name
        
    Raises:
        ValueError: If storage name is invalid
    """
    if not is_valid_storage_name(storage):
        raise ValueError("Storage name must contain only alphanumeric characters, hyphens, and underscores")
    return storage


def validate_snapshot_name(snapshot: str) -> bool:
    """Validate snapshot name.
    
    Snapshot names should only contain alphanumeric characters, hyphens, and underscores.
    This prevents injection attacks and ensures compatibility.
    
    Args:
        snapshot: Snapshot name
        
    Returns:
        True if valid, False otherwise
    """
    if not snapshot or not isinstance(snapshot, str):
        return False
    
    # Only allow alphanumeric, hyphens, and underscores
    # No special characters that could be used for injection
    if not re.match(r'^[a-zA-Z0-9\-_]+$', snapshot):
        return False
    
    # Reasonable length limit
    if len(snapshot) < 1 or len(snapshot) > 128:
        return False
    
    return True


def validate_cores_range(cores: Union[int, str]) -> bool:
    """Validate CPU cores range.
    
    Args:
        cores: Number of CPU cores
        
    Returns:
        True if valid, False otherwise
    """
    try:
        cores_int = int(cores)
        return 1 <= cores_int <= 128
    except (ValueError, TypeError):
        return False


def validate_memory_range(memory: Union[int, str]) -> bool:
    """Validate memory range.
    
    Args:
        memory: Memory in MB
        
    Returns:
        True if valid, False otherwise
    """
    try:
        memory_int = int(memory)
        return 64 <= memory_int <= 1048576  # 64MB to 1TB
    except (ValueError, TypeError):
        return False


def validate_network_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate network configuration.
    
    Args:
        config: Network configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_fields = ['name', 'type']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Network configuration missing required field: {field}")
    
    if config['type'] not in ['bridge', 'bond', 'vlan']:
        raise ValueError("Network type must be one of: bridge, bond, vlan")
    
    return config
