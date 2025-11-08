"""Tests for constants in iDRAC MCP Server."""

import sys
import os

# Add the parent directory to the path to import from working_mcp_server
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the constants from the working server
import working_mcp_server

# Import from secure manager
from src.secure_multi_server_manager import PBKDF2_ITERATIONS


class TestServerConstants:
    """Test that server constants have correct values."""
    
    def test_request_timeout_constant(self):
        """Test request timeout constant."""
        assert working_mcp_server.DEFAULT_REQUEST_TIMEOUT_SECONDS == 10, \
            "DEFAULT_REQUEST_TIMEOUT_SECONDS should be 10 seconds"
    
    def test_pbkdf2_iterations_constant(self):
        """Test PBKDF2 iterations constant."""
        assert PBKDF2_ITERATIONS == 480000, \
            "PBKDF2_ITERATIONS should be 480000 (OWASP 2023 recommendation)"
