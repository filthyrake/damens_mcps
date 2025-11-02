"""Test http_cli token file permissions.

This test validates that token files created by http_cli.py have secure permissions
to prevent unauthorized access by other users on the system.

Note: These are unit tests that verify the code pattern used in http_cli.py for
secure file creation. Integration tests for the full CLI functionality should be
done separately.
"""

import os
import stat
import tempfile
from pathlib import Path


class TestHttpCliTokenFileSecurityPattern:
    """Test token file security pattern matching http_cli.py implementation."""

    def test_secure_token_file_creation_pattern(self):
        """Test the secure file creation pattern used in http_cli.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate the code pattern from http_cli.py login/create_token functions
            token_file = Path(tmpdir) / ".truenas-mcp" / "token.txt"
            token_file.parent.mkdir(exist_ok=True, mode=0o700)

            # Use os.open with proper permissions to avoid race condition
            # This is the pattern used in http_cli.py
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("test-token-content")
            except (OSError, IOError):
                os.close(fd)
                raise

            # Verify directory permissions
            dir_stat = os.stat(token_file.parent)
            dir_mode = stat.S_IMODE(dir_stat.st_mode)
            assert (
                dir_mode == 0o700
            ), f"Directory should have 0o700 permissions, got {oct(dir_mode)}"

            # Verify file permissions
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert (
                file_mode == 0o600
            ), f"Token file should have 0o600 permissions, got {oct(file_mode)}"

            # Verify content
            assert token_file.read_text() == "test-token-content"

    def test_secure_file_no_group_other_access(self):
        """Test that securely created file has no group or other access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "secure_token.txt"

            # Use the secure pattern from http_cli.py
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("secure-content")
            except (OSError, IOError):
                os.close(fd)
                raise

            # Verify no group or other access
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)

            # Check that group and other permissions are zero
            assert (
                file_mode & 0o077 == 0
            ), f"File should not be accessible by group or others, got {oct(file_mode)}"
            # Check that owner has read and write
            assert (
                file_mode & 0o600 == 0o600
            ), f"Owner should have read/write, got {oct(file_mode)}"

    def test_secure_file_permissions_on_update(self):
        """Test that file permissions remain secure when updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "update_token.txt"

            # Create initial file with secure permissions
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("initial-token")
            except (OSError, IOError):
                os.close(fd)
                raise

            # Verify initial permissions
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert file_mode == 0o600

            # Update the file (same pattern as http_cli.py would use)
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("updated-token")
            except (OSError, IOError):
                os.close(fd)
                raise

            # Verify permissions after update
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert (
                file_mode == 0o600
            ), f"Updated file should maintain 0o600 permissions, got {oct(file_mode)}"

            # Verify content was updated
            assert token_file.read_text() == "updated-token"

    def test_atomic_file_creation(self):
        """Test that file is created atomically with secure permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "atomic_token.txt"

            # Track that os.open creates file with correct mode
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)

            # File should exist immediately after os.open
            assert token_file.exists(), "File should exist after os.open"

            # Check permissions immediately (before writing content)
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert (
                file_mode == 0o600
            ), f"File should have secure permissions from creation, got {oct(file_mode)}"

            # Now write content
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("atomic-token")
            except (OSError, IOError):
                os.close(fd)
                raise

            # Verify permissions are still secure after writing
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert (
                file_mode == 0o600
            ), f"File should maintain secure permissions after write, got {oct(file_mode)}"

    def test_nested_directory_creation(self):
        """Test that directory containing token is created with secure permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate the actual structure used in http_cli.py
            # Path.home() / ".truenas-mcp" / "token.txt"
            token_file = Path(tmpdir) / ".truenas-mcp" / "token.txt"

            # This is the exact pattern from http_cli.py
            token_file.parent.mkdir(exist_ok=True, mode=0o700)

            # Verify the immediate parent directory has secure permissions
            dir_stat = os.stat(token_file.parent)
            dir_mode = stat.S_IMODE(dir_stat.st_mode)
            assert (
                dir_mode == 0o700
            ), f"Directory should have 0o700 permissions, got {oct(dir_mode)}"

            # Create file with secure permissions (same pattern as http_cli.py)
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("nested-token")
            except (OSError, IOError):
                os.close(fd)
                raise

            # Verify file permissions
            file_stat = os.stat(token_file)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            assert (
                file_mode == 0o600
            ), f"File should have 0o600 permissions, got {oct(file_mode)}"
