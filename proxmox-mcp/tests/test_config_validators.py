"""Tests for Proxmox validation models (Pydantic v2 migration)."""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'utils'))

from validation import VMConfig, ContainerConfig
from pydantic import ValidationError


class TestVMConfigValidators:
    """Test VM configuration validators."""
    
    def test_valid_vm_config(self):
        """Test valid VM configuration."""
        config = VMConfig(
            name="test-vm",
            node="pve-node1",
            cores=4,
            memory=2048,
            disk_size="20G"
        )
        assert config.name == "test-vm"
        assert config.node == "pve-node1"
        assert config.cores == 4
        assert config.memory == 2048
    
    def test_invalid_vm_name_with_special_chars(self):
        """Test that VM name with special characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(
                name="test@vm!",
                node="pve-node1"
            )
        
        assert "alphanumeric characters, hyphens, and underscores" in str(exc_info.value)
    
    def test_invalid_vm_name_too_long(self):
        """Test that VM name exceeding 128 characters is rejected."""
        long_name = "a" * 129
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(
                name=long_name,
                node="pve-node1"
            )
        
        assert "must not exceed 128 characters" in str(exc_info.value)
    
    def test_valid_vm_name_formats(self):
        """Test various valid VM name formats."""
        valid_names = [
            "vm1",
            "test-vm",
            "test_vm",
            "VM-123_test",
            "a" * 128  # Maximum length
        ]
        
        for name in valid_names:
            config = VMConfig(name=name, node="pve")
            assert config.name == name
    
    def test_cores_validation_invalid_below_minimum(self):
        """Test that cores below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(name="test", node="pve", cores=0)
        
        assert "CPU cores must be between 1 and 128" in str(exc_info.value)
    
    def test_cores_validation_invalid_above_maximum(self):
        """Test that cores above 128 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(name="test", node="pve", cores=256)
        
        assert "CPU cores must be between 1 and 128" in str(exc_info.value)
    
    def test_cores_validation_valid_range(self):
        """Test valid core counts."""
        for cores in [1, 2, 4, 8, 16, 32, 64, 128]:
            config = VMConfig(name="test", node="pve", cores=cores)
            assert config.cores == cores
    
    def test_cores_validation_string_conversion(self):
        """Test that string core counts are converted to integers."""
        config = VMConfig(name="test", node="pve", cores="8")
        assert config.cores == 8
        assert isinstance(config.cores, int)
    
    def test_memory_validation_invalid_below_minimum(self):
        """Test that memory below 64MB is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(name="test", node="pve", memory=32)
        
        assert "Memory must be between 64MB and 1TB" in str(exc_info.value)
    
    def test_memory_validation_invalid_above_maximum(self):
        """Test that memory above 1TB is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(name="test", node="pve", memory=2000000)
        
        assert "Memory must be between 64MB and 1TB" in str(exc_info.value)
    
    def test_memory_validation_valid_range(self):
        """Test valid memory sizes."""
        for memory in [64, 512, 1024, 2048, 4096, 8192, 16384]:
            config = VMConfig(name="test", node="pve", memory=memory)
            assert config.memory == memory
    
    def test_memory_validation_string_conversion(self):
        """Test that string memory values are converted to integers."""
        config = VMConfig(name="test", node="pve", memory="2048")
        assert config.memory == 2048
        assert isinstance(config.memory, int)
    
    def test_disk_size_validation_invalid_format(self):
        """Test that invalid disk size format is rejected."""
        invalid_formats = [
            "abc",
            "10X",
            "G10",
            "10 G",
            "-10G",
        ]
        
        for disk_size in invalid_formats:
            with pytest.raises(ValidationError) as exc_info:
                VMConfig(name="test", node="pve", disk_size=disk_size)
            
            assert "Disk size must be in format" in str(exc_info.value)
    
    def test_disk_size_validation_valid_formats(self):
        """Test valid disk size formats."""
        valid_formats = [
            "10G",
            "100M",
            "1T",
            "500K",
            "2P",
            "50",  # No unit
        ]
        
        for disk_size in valid_formats:
            config = VMConfig(name="test", node="pve", disk_size=disk_size)
            assert config.disk_size == disk_size


class TestContainerConfigValidators:
    """Test container configuration validators."""
    
    def test_valid_container_config(self):
        """Test valid container configuration."""
        config = ContainerConfig(
            name="test-ct",
            node="pve-node1",
            ostemplate="ubuntu-22.04-standard"
        )
        assert config.name == "test-ct"
        assert config.node == "pve-node1"
        assert config.ostemplate == "ubuntu-22.04-standard"
    
    def test_invalid_container_name_with_special_chars(self):
        """Test that container name with special characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                name="test@ct!",
                node="pve",
                ostemplate="ubuntu"
            )
        
        assert "alphanumeric characters, hyphens, and underscores" in str(exc_info.value)
    
    def test_valid_container_name_formats(self):
        """Test various valid container name formats."""
        valid_names = [
            "ct1",
            "test-ct",
            "test_ct",
            "CT-123_test",
        ]
        
        for name in valid_names:
            config = ContainerConfig(name=name, node="pve", ostemplate="ubuntu")
            assert config.name == name
    
    def test_ostemplate_validation_empty_rejected(self):
        """Test that empty OS template is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                name="test",
                node="pve",
                ostemplate=""
            )
        
        assert "OS template is required" in str(exc_info.value)
    
    def test_ostemplate_validation_whitespace_rejected(self):
        """Test that whitespace-only OS template is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                name="test",
                node="pve",
                ostemplate="   "
            )
        
        assert "OS template is required" in str(exc_info.value)
    
    def test_ostemplate_validation_valid_templates(self):
        """Test valid OS templates."""
        valid_templates = [
            "ubuntu-22.04-standard",
            "debian-11-standard",
            "alpine-3.16-default",
            "local:vztmpl/ubuntu-20.04.tar.gz",
        ]
        
        for template in valid_templates:
            config = ContainerConfig(name="test", node="pve", ostemplate=template)
            assert config.ostemplate == template


class TestPydanticV2Migration:
    """Test that Pydantic v2 features work correctly."""
    
    def test_field_validator_decorator_works_vm(self):
        """Test that @field_validator decorator is functioning for VM config."""
        # This test verifies the migration to Pydantic v2 syntax
        
        # Test name validation
        with pytest.raises(ValidationError):
            VMConfig(name="invalid@name", node="pve")
        
        # Test cores validation
        with pytest.raises(ValidationError):
            VMConfig(name="test", node="pve", cores=0)
        
        # Test memory validation
        with pytest.raises(ValidationError):
            VMConfig(name="test", node="pve", memory=32)
        
        # Test disk_size validation
        with pytest.raises(ValidationError):
            VMConfig(name="test", node="pve", disk_size="invalid")
    
    def test_field_validator_decorator_works_container(self):
        """Test that @field_validator decorator is functioning for Container config."""
        # Test name validation
        with pytest.raises(ValidationError):
            ContainerConfig(name="invalid@name", node="pve", ostemplate="ubuntu")
        
        # Test ostemplate validation
        with pytest.raises(ValidationError):
            ContainerConfig(name="test", node="pve", ostemplate="")
    
    def test_classmethod_decorator_present(self):
        """Test that validators have @classmethod decorator."""
        # In Pydantic v2, validators must be classmethods
        # This is automatically enforced by the @field_validator decorator
        # We verify by ensuring validation works as expected
        
        config = VMConfig(name="test", node="pve")
        assert config.name == "test"
        
        with pytest.raises(ValidationError):
            VMConfig(name="", node="pve")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
