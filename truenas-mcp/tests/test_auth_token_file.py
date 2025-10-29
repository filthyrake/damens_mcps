"""Test AuthManager token file operations and security."""

import os
import stat
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from auth import AuthManager


class TestAuthManagerTokenFile:
    """Test AuthManager token file security and permissions."""
    
    def test_token_file_permissions(self):
        """Test that token file is created with secure permissions (0o600)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = os.path.join(tmpdir, "test_token")
            
            config = {
                "api_key": "test-key",
                "token_file": token_file
            }
            
            auth_manager = AuthManager(config)
            
            # Set a token which triggers file save
            test_token = "test-jwt-token-12345"
            auth_manager.set_token(test_token)
            
            # Verify file exists
            assert os.path.exists(token_file), "Token file should exist"
            
            # Verify file permissions are 0o600 (read/write for owner only)
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert file_mode == 0o600, f"Token file should have 0o600 permissions, got {oct(file_mode)}"
            
            # Verify file content
            with open(token_file, 'r') as f:
                content = f.read()
            assert content == test_token, "Token file content should match"
    
    def test_token_file_permissions_on_update(self):
        """Test that token file maintains secure permissions when updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = os.path.join(tmpdir, "test_token")
            
            config = {
                "api_key": "test-key",
                "token_file": token_file
            }
            
            auth_manager = AuthManager(config)
            
            # Set initial token
            auth_manager.set_token("initial-token")
            
            # Verify initial permissions
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert file_mode == 0o600, f"Initial token file should have 0o600 permissions, got {oct(file_mode)}"
            
            # Update token
            auth_manager.set_token("updated-token")
            
            # Verify permissions are still secure after update
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert file_mode == 0o600, f"Updated token file should have 0o600 permissions, got {oct(file_mode)}"
            
            # Verify updated content
            with open(token_file, 'r') as f:
                content = f.read()
            assert content == "updated-token", "Token file content should be updated"
    
    def test_token_file_no_race_condition(self):
        """Test that token file is never created with insecure permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = os.path.join(tmpdir, "test_token")
            
            config = {
                "api_key": "test-key",
                "token_file": token_file
            }
            
            auth_manager = AuthManager(config)
            
            # Set token
            auth_manager.set_token("secure-token")
            
            # File should exist with secure permissions from creation
            assert os.path.exists(token_file), "Token file should exist"
            
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            
            # Permissions should be 0o600 (no group or other access)
            assert file_mode & 0o077 == 0, f"Token file should not be readable by group or others, got {oct(file_mode)}"
            assert file_mode & 0o600 == 0o600, f"Token file should be readable/writable by owner, got {oct(file_mode)}"
    
    def test_token_file_in_subdirectory(self):
        """Test that token file in subdirectory has secure permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory path
            token_file = os.path.join(tmpdir, "subdir", "tokens", "test_token")
            
            config = {
                "api_key": "test-key",
                "token_file": token_file
            }
            
            auth_manager = AuthManager(config)
            
            # Set token - should create subdirectories and file
            auth_manager.set_token("nested-token")
            
            # Verify file exists
            assert os.path.exists(token_file), "Token file should exist in subdirectory"
            
            # Verify file permissions
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert file_mode == 0o600, f"Token file in subdirectory should have 0o600 permissions, got {oct(file_mode)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
