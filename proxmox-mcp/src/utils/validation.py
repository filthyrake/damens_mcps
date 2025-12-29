"""Input validation utilities for Proxmox MCP Server."""

import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ValidationError, field_validator

# Proxmox VMID limits per documentation
MIN_VMID = 100  # Proxmox reserves 0-99 for system use
MAX_VMID = 999999  # Proxmox VMID upper limit

# CPU and Memory limits for VMs/Containers
MIN_CPU_CORES = 1  # Minimum CPU cores
MAX_CPU_CORES = 128  # Proxmox maximum CPU cores per VM
MIN_MEMORY_MB = 64  # Minimum usable memory for VM
MAX_MEMORY_MB = 1048576  # 1TB - Proxmox maximum memory per VM

# Name length limits
MAX_NAME_LENGTH = 128  # Maximum length for VM/container/node names
MIN_NAME_LENGTH = 1  # Minimum name length
MAX_SNAPSHOT_NAME_LENGTH = 128  # Maximum length for snapshot names


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
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('VM name must contain only alphanumeric characters, hyphens, and underscores')
        if len(v) > MAX_NAME_LENGTH:
            raise ValueError(f'VM name must not exceed {MAX_NAME_LENGTH} characters')
        return v
    
    @field_validator('cores')
    @classmethod
    def validate_cores(cls, v):
        # Use the standalone validation function for consistency
        if not isinstance(v, int):
            try:
                v = int(v)
            except (ValueError, TypeError):
                raise ValueError('CPU cores must be an integer')
        # Reuse validate_cores_range logic
        if not (MIN_CPU_CORES <= v <= MAX_CPU_CORES):
            raise ValueError(f'CPU cores must be between {MIN_CPU_CORES} and {MAX_CPU_CORES}')
        return v
    
    @field_validator('memory')
    @classmethod
    def validate_memory(cls, v):
        # Use the standalone validation function for consistency
        if not isinstance(v, int):
            try:
                v = int(v)
            except (ValueError, TypeError):
                raise ValueError('Memory must be an integer')
        # Reuse validate_memory_range logic
        if not (MIN_MEMORY_MB <= v <= MAX_MEMORY_MB):
            raise ValueError(f'Memory must be between {MIN_MEMORY_MB}MB and {MAX_MEMORY_MB}MB (1TB)')
        return v
    
    @field_validator('disk_size')
    @classmethod
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
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Container name must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @field_validator('ostemplate')
    @classmethod
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
        return MIN_VMID <= vmid_int <= MAX_VMID
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
        raise ValueError(
            f"Invalid VMID '{vmid}': must be a valid integer. "
            f"Valid range: {MIN_VMID}-{MAX_VMID}. "
            f"Example: 100, 101, 200"
        )

    if vmid_int < MIN_VMID:
        raise ValueError(
            f"Invalid VMID '{vmid_int}': too low. "
            f"VMIDs 0-99 are reserved by Proxmox for system use. "
            f"Valid range: {MIN_VMID}-{MAX_VMID}. "
            f"Example: 100, 101, 200"
        )

    if vmid_int > MAX_VMID:
        raise ValueError(
            f"Invalid VMID '{vmid_int}': too high. "
            f"Maximum VMID is {MAX_VMID}. "
            f"Example: 100, 101, 200"
        )

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
    return bool(re.match(r'^[a-zA-Z0-9\-_]+$', node)) and len(node) <= MAX_NAME_LENGTH


def validate_node_name(node: str) -> str:
    """Validate and return node name.

    Args:
        node: Node name

    Returns:
        Validated node name

    Raises:
        ValueError: If node name is invalid
    """
    if not node or not isinstance(node, str):
        raise ValueError(
            "Invalid node name: cannot be empty. "
            "Node names must contain only alphanumeric characters, hyphens, and underscores. "
            "Example: pve, proxmox-node1, node_2"
        )
    if len(node) > MAX_NAME_LENGTH:
        raise ValueError(
            f"Invalid node name '{node}': too long ({len(node)} characters). "
            f"Maximum length is {MAX_NAME_LENGTH} characters."
        )
    if not is_valid_node_name(node):
        raise ValueError(
            f"Invalid node name '{node}': contains invalid characters. "
            "Node names must contain only alphanumeric characters, hyphens, and underscores. "
            "Example: pve, proxmox-node1, node_2"
        )
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
    return bool(re.match(r'^[a-zA-Z0-9\-_]+$', storage)) and len(storage) <= MAX_NAME_LENGTH


def validate_storage_name(storage: str) -> str:
    """Validate and return storage name.

    Args:
        storage: Storage name

    Returns:
        Validated storage name

    Raises:
        ValueError: If storage name is invalid
    """
    if not storage or not isinstance(storage, str):
        raise ValueError(
            "Invalid storage name: cannot be empty. "
            "Storage names must contain only alphanumeric characters, hyphens, and underscores. "
            "Example: local, local-lvm, nfs_storage"
        )
    if len(storage) > MAX_NAME_LENGTH:
        raise ValueError(
            f"Invalid storage name '{storage}': too long ({len(storage)} characters). "
            f"Maximum length is {MAX_NAME_LENGTH} characters."
        )
    if not is_valid_storage_name(storage):
        raise ValueError(
            f"Invalid storage name '{storage}': contains invalid characters. "
            "Storage names must contain only alphanumeric characters, hyphens, and underscores. "
            "Example: local, local-lvm, nfs_storage"
        )
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
    if len(snapshot) < MIN_NAME_LENGTH or len(snapshot) > MAX_SNAPSHOT_NAME_LENGTH:
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
        return MIN_CPU_CORES <= cores_int <= MAX_CPU_CORES
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
        return MIN_MEMORY_MB <= memory_int <= MAX_MEMORY_MB
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
    valid_network_types = ['bridge', 'bond', 'vlan']
    required_fields = ['name', 'type']

    for field in required_fields:
        if field not in config:
            raise ValueError(
                f"Network configuration missing required field: '{field}'. "
                f"Required fields: {', '.join(required_fields)}. "
                "Example: {'name': 'vmbr1', 'type': 'bridge'}"
            )

    network_type = config['type']
    if network_type not in valid_network_types:
        raise ValueError(
            f"Invalid network type '{network_type}'. "
            f"Valid options: {', '.join(valid_network_types)}. "
            "Example: bridge (for VM networking), bond (for link aggregation), vlan (for VLAN tagging)"
        )

    return config
