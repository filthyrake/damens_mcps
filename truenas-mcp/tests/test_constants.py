"""Tests for configuration constants in TrueNAS MCP Server."""

from src.config import (
    MIN_SECRET_KEY_LENGTH,
    MIN_PORT,
    MAX_PORT,
)


class TestConfigConstants:
    """Test that configuration constants have correct values."""
    
    def test_secret_key_length_constant(self):
        """Test secret key length constant."""
        assert MIN_SECRET_KEY_LENGTH == 32, "MIN_SECRET_KEY_LENGTH should be 32 (256 bits)"
    
    def test_port_constants(self):
        """Test port range constants."""
        assert MIN_PORT == 1, "MIN_PORT should be 1"
        assert MAX_PORT == 65535, "MAX_PORT should be 65535"
        assert MIN_PORT < MAX_PORT, "MIN_PORT should be less than MAX_PORT"
