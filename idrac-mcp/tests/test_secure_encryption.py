"""Unit tests for secure password-based encryption in SecureMultiServerManager."""

import pytest
import tempfile
import json
import os
from unittest.mock import patch

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from secure_multi_server_manager import SecureMultiServerManager


class TestPasswordBasedEncryption:
    """Test password-based key derivation for secure fleet management."""
    
    def test_initialization_with_password(self):
        """Test that initialization works with a master password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            # Initialize with a master password
            manager = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="test_password_123"
            )
            
            assert manager.fernet is not None
            assert manager.salt is not None
            assert len(manager.salt) == 16
            # Key file should NOT be created
            assert not os.path.exists(key_file)
    
    def test_password_mismatch_on_init(self):
        """Test that wrong password fails to decrypt existing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            # Create initial config with password
            manager1 = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="correct_password"
            )
            manager1.add_server("server1", "192.168.1.100", "root", "password123")
            
            # Try to load with wrong password - loading should work but decryption will fail
            manager2 = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="wrong_password"
            )
            
            # The manager loads but servers dict should be empty due to decryption failure
            assert len(manager2.servers) == 0
    
    def test_salt_persistence(self):
        """Test that salt is saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            # Create initial config
            manager1 = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="test_password"
            )
            manager1.add_server("server1", "192.168.1.100", "root", "password123")
            salt1 = manager1.salt
            
            # Load config with same password
            manager2 = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="test_password"
            )
            salt2 = manager2.salt
            
            # Salt should be the same
            assert salt1 == salt2
            # Should be able to decrypt
            assert "server1" in manager2.servers
    
    def test_no_key_file_created(self):
        """Test that no encryption key file is created on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            manager = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="test_password"
            )
            manager.add_server("server1", "192.168.1.100", "root", "password123")
            
            # Key file should NOT exist
            assert not os.path.exists(key_file)
    
    def test_backward_compatibility_with_legacy_key(self):
        """Test that existing .fleet_key files are still supported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            # Create a legacy key file
            from cryptography.fernet import Fernet
            legacy_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(legacy_key)
            
            # Initialize should use the legacy key
            with patch('builtins.print'):  # Suppress warning messages
                manager = SecureMultiServerManager(
                    config_file=config_file,
                    key_file=key_file,
                    master_password=None  # Should not be needed with legacy key
                )
            
            assert manager.fernet is not None
            # Verify we can encrypt/decrypt with the loaded key
            test_data = "test_password"
            encrypted = manager._encrypt_password(test_data)
            decrypted = manager._decrypt_password(encrypted)
            assert decrypted == test_data
    
    def test_server_password_encryption_decryption(self):
        """Test that server passwords are encrypted and can be decrypted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            manager = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="test_password"
            )
            
            # Add a server
            test_password = "super_secret_password"
            manager.add_server("server1", "192.168.1.100", "root", test_password)
            
            # Get server config (should decrypt password)
            config = manager.get_server_config("server1")
            
            assert config is not None
            assert config["password"] == test_password
            assert "password_encrypted" not in config  # Should be removed after decryption
    
    def test_config_version_2_format(self):
        """Test that saved config uses version 2.0 format with salt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            manager = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password="test_password"
            )
            manager.add_server("server1", "192.168.1.100", "root", "password123")
            
            # Load and check the config file format
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            assert config_data["version"] == "2.0"
            assert "salt" in config_data
            assert "data" in config_data
            assert config_data["salt"] is not None
    
    def test_empty_password_raises_error(self):
        """Test that empty password raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            # Test with empty string
            with pytest.raises(ValueError, match="Master password cannot be empty"):
                SecureMultiServerManager(
                    config_file=config_file,
                    key_file=key_file,
                    master_password=""
                )
            
            # Test with None will trigger interactive prompt (not tested here)
            # This is covered by integration tests
    
    def test_multiple_sessions_same_password(self):
        """Test that multiple sessions with same password can access data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_fleet.json")
            key_file = os.path.join(tmpdir, ".test_key")
            password = "consistent_password"
            
            # Session 1: Create and add server
            manager1 = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password=password
            )
            manager1.add_server("server1", "192.168.1.100", "root", "password123")
            manager1.add_server("server2", "192.168.1.101", "admin", "password456")
            
            # Session 2: Load and verify
            manager2 = SecureMultiServerManager(
                config_file=config_file,
                key_file=key_file,
                master_password=password
            )
            
            assert len(manager2.servers) == 2
            assert "server1" in manager2.servers
            assert "server2" in manager2.servers
            
            config1 = manager2.get_server_config("server1")
            config2 = manager2.get_server_config("server2")
            
            assert config1["password"] == "password123"
            assert config2["password"] == "password456"


class TestSecurityImprovements:
    """Test security improvements over legacy approach."""
    
    def test_key_derivation_iterations(self):
        """Test that key derivation uses recommended iteration count."""
        # This is more of a documentation test - we verify the code uses 480,000 iterations
        # We can't easily test the actual iteration count without instrumenting the code
        # But we can verify the implementation exists
        from secure_multi_server_manager import SecureMultiServerManager
        import inspect
        
        source = inspect.getsource(SecureMultiServerManager._initialize_encryption)
        
        # Check that the source mentions the OWASP recommended iteration count
        assert "480000" in source or "480,000" in source
        assert "PBKDF2HMAC" in source
    
    def test_salt_uniqueness(self):
        """Test that different configs get different salts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file1 = os.path.join(tmpdir, "fleet1.json")
            config_file2 = os.path.join(tmpdir, "fleet2.json")
            key_file = os.path.join(tmpdir, ".test_key")
            
            manager1 = SecureMultiServerManager(
                config_file=config_file1,
                key_file=key_file,
                master_password="password1"
            )
            manager1.add_server("server1", "192.168.1.100", "root", "pass")
            
            manager2 = SecureMultiServerManager(
                config_file=config_file2,
                key_file=key_file,
                master_password="password2"
            )
            manager2.add_server("server1", "192.168.1.100", "root", "pass")
            
            # Different configs should have different salts
            assert manager1.salt != manager2.salt
