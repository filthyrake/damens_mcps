"""Tests for secure configuration management with encrypted password storage."""

import json
import os
import pytest
import sys
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from secure_config import SecureConfigManager


class TestSecureConfigManager:
    """Test secure configuration manager."""
    
    def test_save_and_load_encrypted_config(self, tmp_path):
        """Test saving and loading encrypted configuration."""
        config_file = tmp_path / "config.json"
        master_password = "test-master-password"
        
        # Create test config
        config = {
            "host": "proxmox.example.com",
            "port": 8006,
            "protocol": "https",
            "username": "root@pam",
            "password": "my-secret-password",
            "realm": "pve",
            "ssl_verify": False
        }
        
        # Save encrypted config
        manager = SecureConfigManager(config_file=str(config_file))
        manager.save_encrypted_config(config, master_password)
        
        # Verify file was created
        assert config_file.exists()
        
        # Load and verify encryption
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        # Should have encrypted password and salt, not plaintext password
        assert 'password_encrypted' in saved_data
        assert 'salt' in saved_data
        assert 'password' not in saved_data
        
        # Load encrypted config
        manager2 = SecureConfigManager(config_file=str(config_file), master_password=master_password)
        loaded_config = manager2.load_config()
        
        # Verify decrypted config matches original
        assert loaded_config['host'] == config['host']
        assert loaded_config['username'] == config['username']
        assert loaded_config['password'] == config['password']
        assert 'password_encrypted' not in loaded_config
        assert 'salt' not in loaded_config
    
    def test_load_encrypted_config_wrong_password(self, tmp_path):
        """Test that loading with wrong password fails."""
        config_file = tmp_path / "config.json"
        master_password = "correct-password"
        
        config = {
            "host": "proxmox.example.com",
            "username": "root@pam",
            "password": "secret"
        }
        
        # Save with correct password
        manager = SecureConfigManager(config_file=str(config_file))
        manager.save_encrypted_config(config, master_password)
        
        # Try to load with wrong password
        manager2 = SecureConfigManager(config_file=str(config_file), master_password="wrong-password")
        with pytest.raises(ValueError, match="Failed to decrypt password"):
            manager2.load_config()
    
    def test_load_plaintext_config(self, tmp_path):
        """Test loading plaintext (legacy) configuration."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "proxmox.example.com",
            "username": "root@pam",
            "password": "plaintext-password"
        }
        
        # Save plaintext config
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Load plaintext config (no master password needed)
        manager = SecureConfigManager(config_file=str(config_file))
        loaded_config = manager.load_config()
        
        assert loaded_config['password'] == "plaintext-password"
    
    def test_is_encrypted_config_detection(self, tmp_path):
        """Test detection of encrypted vs plaintext configs."""
        encrypted_file = tmp_path / "encrypted.json"
        plaintext_file = tmp_path / "plaintext.json"
        
        # Create encrypted config
        config = {
            "host": "test.com",
            "username": "user",
            "password": "pass"
        }
        manager = SecureConfigManager(config_file=str(encrypted_file))
        manager.save_encrypted_config(config, "master-password")
        
        # Create plaintext config
        with open(plaintext_file, 'w') as f:
            json.dump(config, f)
        
        # Test detection
        assert SecureConfigManager.is_encrypted_config(encrypted_file) is True
        assert SecureConfigManager.is_encrypted_config(plaintext_file) is False
        assert SecureConfigManager.is_encrypted_config(tmp_path / "nonexistent.json") is False
    
    def test_save_without_password_field(self, tmp_path):
        """Test that saving config without password field fails."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "test.com",
            "username": "user"
            # Missing password field
        }
        
        manager = SecureConfigManager(config_file=str(config_file))
        with pytest.raises(ValueError, match="missing 'password' field"):
            manager.save_encrypted_config(config, "master-password")
    
    def test_save_with_empty_master_password(self, tmp_path):
        """Test that empty master password is rejected."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "test.com",
            "username": "user",
            "password": "pass"
        }
        
        manager = SecureConfigManager(config_file=str(config_file))
        with pytest.raises(ValueError, match="Master password required"):
            manager.save_encrypted_config(config, "")
    
    def test_load_encrypted_without_master_password(self, tmp_path):
        """Test that loading encrypted config without password fails."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "test.com",
            "username": "user",
            "password": "pass"
        }
        
        # Save encrypted config
        manager = SecureConfigManager(config_file=str(config_file))
        manager.save_encrypted_config(config, "master-password")
        
        # Try to load without master password
        manager2 = SecureConfigManager(config_file=str(config_file))
        with pytest.raises(ValueError, match="Master password required"):
            manager2.load_config()
    
    def test_load_missing_config_file(self, tmp_path):
        """Test that loading non-existent config fails gracefully."""
        config_file = tmp_path / "nonexistent.json"
        
        manager = SecureConfigManager(config_file=str(config_file))
        with pytest.raises(FileNotFoundError):
            manager.load_config()
    
    def test_load_invalid_json(self, tmp_path):
        """Test that loading invalid JSON fails gracefully."""
        config_file = tmp_path / "invalid.json"
        
        # Write invalid JSON
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        manager = SecureConfigManager(config_file=str(config_file))
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.load_config()
    
    def test_encrypted_password_not_readable(self, tmp_path):
        """Test that encrypted password is not human-readable."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "test.com",
            "username": "user",
            "password": "my-secret-password-123"
        }
        
        manager = SecureConfigManager(config_file=str(config_file))
        manager.save_encrypted_config(config, "master-password")
        
        # Read the saved file
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        # Verify plaintext password is not in the file
        encrypted = saved_data['password_encrypted']
        assert "my-secret-password-123" not in encrypted
        assert len(encrypted) > 20  # Encrypted data should be longer
    
    def test_config_missing_password_fields(self, tmp_path):
        """Test loading config that has neither password nor password_encrypted."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "test.com",
            "username": "user"
            # Missing both password and password_encrypted
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        manager = SecureConfigManager(config_file=str(config_file))
        with pytest.raises(ValueError, match="missing both 'password' and 'password_encrypted'"):
            manager.load_config()
    
    def test_encrypted_config_missing_salt(self, tmp_path):
        """Test loading encrypted config without salt fails."""
        config_file = tmp_path / "config.json"
        
        config = {
            "host": "test.com",
            "username": "user",
            "password_encrypted": "some-encrypted-data"
            # Missing salt field
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        manager = SecureConfigManager(config_file=str(config_file), master_password="test")
        with pytest.raises(ValueError, match="missing salt field"):
            manager.load_config()
    
    def test_salt_generation(self):
        """Test that salt generation produces random bytes."""
        salt1 = SecureConfigManager.generate_salt()
        salt2 = SecureConfigManager.generate_salt()
        
        assert len(salt1) == 16
        assert len(salt2) == 16
        assert salt1 != salt2  # Should be random


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
