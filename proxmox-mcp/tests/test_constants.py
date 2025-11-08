"""Tests for validation constants in Proxmox MCP Server."""

from src.utils.validation import (
    MIN_VMID,
    MAX_VMID,
    MIN_CPU_CORES,
    MAX_CPU_CORES,
    MIN_MEMORY_MB,
    MAX_MEMORY_MB,
    MAX_NAME_LENGTH,
    MIN_NAME_LENGTH,
    MAX_SNAPSHOT_NAME_LENGTH,
)


class TestValidationConstants:
    """Test that validation constants have correct values."""
    
    def test_vmid_constants(self):
        """Test VMID range constants."""
        assert MIN_VMID == 100, "MIN_VMID should be 100 (Proxmox reserves 0-99)"
        assert MAX_VMID == 999999, "MAX_VMID should be 999999"
        assert MIN_VMID < MAX_VMID, "MIN_VMID should be less than MAX_VMID"
    
    def test_cpu_core_constants(self):
        """Test CPU core limit constants."""
        assert MIN_CPU_CORES == 1, "MIN_CPU_CORES should be 1"
        assert MAX_CPU_CORES == 128, "MAX_CPU_CORES should be 128"
        assert MIN_CPU_CORES < MAX_CPU_CORES, "MIN_CPU_CORES should be less than MAX_CPU_CORES"
    
    def test_memory_constants(self):
        """Test memory limit constants."""
        assert MIN_MEMORY_MB == 64, "MIN_MEMORY_MB should be 64MB"
        assert MAX_MEMORY_MB == 1048576, "MAX_MEMORY_MB should be 1048576MB (1TB)"
        assert MIN_MEMORY_MB < MAX_MEMORY_MB, "MIN_MEMORY_MB should be less than MAX_MEMORY_MB"
    
    def test_name_length_constants(self):
        """Test name length constants."""
        assert MIN_NAME_LENGTH == 1, "MIN_NAME_LENGTH should be 1"
        assert MAX_NAME_LENGTH == 128, "MAX_NAME_LENGTH should be 128"
        assert MAX_SNAPSHOT_NAME_LENGTH == 128, "MAX_SNAPSHOT_NAME_LENGTH should be 128"
        assert MIN_NAME_LENGTH < MAX_NAME_LENGTH, "MIN_NAME_LENGTH should be less than MAX_NAME_LENGTH"
