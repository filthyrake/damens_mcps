"""Tests for fleet_cli.py security - password handling."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestFleetCLISecurity:
    """Test security aspects of fleet_cli.py."""
    
    def test_add_command_does_not_accept_password_as_argument(self):
        """Verify that the add command does not accept password as a CLI argument."""
        from fleet_cli import cli
        
        runner = CliRunner()
        
        # Try to pass password as argument (old insecure way)
        # This should fail because password is no longer an argument
        result = runner.invoke(cli, [
            '--config', 'test_fleet.json',
            'add', 
            'testserver', 
            '192.168.1.100', 
            'root',
            'insecure_password_in_args'  # This should cause an error
        ])
        
        # Command should fail because password is not an argument anymore
        assert result.exit_code != 0
        assert "Got unexpected extra argument" in result.output or "Error" in result.output
    
    def test_add_command_prompts_for_password(self):
        """Verify that the add command prompts for password securely."""
        from fleet_cli import cli
        
        runner = CliRunner()
        
        # Mock the MultiServerManager to avoid actual file operations
        with patch('fleet_cli.MultiServerManager') as MockManager:
            mock_manager = MagicMock()
            MockManager.return_value = mock_manager
            
            # Simulate password input via stdin
            result = runner.invoke(cli, [
                '--config', 'test_fleet.json',
                'add',
                'testserver',
                '192.168.1.100',
                'root'
            ], input='secure_password\nsecure_password\n')  # Password confirmation
            
            # Command should succeed
            assert result.exit_code == 0
            
            # Verify add_server was called with the password
            mock_manager.add_server.assert_called_once()
            call_args = mock_manager.add_server.call_args
            
            # Check that password was passed to add_server
            assert call_args[0][3] == 'secure_password'  # 4th positional arg is password
            assert "Added server 'testserver'" in result.output
    
    def test_add_command_requires_password_confirmation(self):
        """Verify that password confirmation is required and mismatches are rejected."""
        from fleet_cli import cli
        
        runner = CliRunner()
        
        with patch('fleet_cli.MultiServerManager') as MockManager:
            mock_manager = MagicMock()
            MockManager.return_value = mock_manager
            
            # Provide mismatched passwords
            result = runner.invoke(cli, [
                '--config', 'test_fleet.json',
                'add',
                'testserver',
                '192.168.1.100',
                'root'
            ], input='password1\npassword2\n')  # Mismatched passwords
            
            # Command should fail due to password mismatch
            assert result.exit_code != 0
            assert "Error" in result.output
            
            # add_server should not have been called
            mock_manager.add_server.assert_not_called()
    
    def test_password_not_visible_in_command_help(self):
        """Verify that password is not shown as a required argument in help."""
        from fleet_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['add', '--help'])
        
        # The word "PASSWORD" appears in the description explaining it will be prompted
        # But it should NOT appear as a required argument in the USAGE line
        usage_line = [line for line in result.output.split('\n') if 'USAGE:' in line.upper()][0]
        
        # Help should NOT show PASSWORD as an argument in the usage line
        assert "PASSWORD" not in usage_line.upper()
        
        # Help should show it will be prompted (in the description)
        assert "password will be prompted securely" in result.output.lower()
        
        # Should still show other required arguments
        assert "NAME" in result.output.upper()
        assert "HOST" in result.output.upper()
        assert "USERNAME" in result.output.upper()


class TestSecureFleetCLIComparison:
    """Compare fleet_cli.py with secure_fleet_cli.py for consistency."""
    
    def test_fleet_cli_matches_secure_pattern(self):
        """Verify fleet_cli.py now uses the same secure pattern as secure_fleet_cli.py."""
        # Read the source files directly
        import os
        
        fleet_cli_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fleet_cli.py')
        
        with open(fleet_cli_path, 'r') as f:
            fleet_source = f.read()
        
        # Find the add function definition in fleet_cli
        add_start = fleet_source.find("def add(ctx, name, host, username")
        if add_start == -1:
            pytest.fail("Could not find add function in fleet_cli.py")
        
        # Find the start of the decorators for add function (search backwards)
        decorators_start = fleet_source.rfind("@cli.command()", 0, add_start)
        
        # Find the end of the add function (next function or end of file)
        next_decorator = fleet_source.find("\n@cli.command()", add_start)
        if next_decorator == -1:
            next_decorator = len(fleet_source)
        
        fleet_add_section = fleet_source[decorators_start:next_decorator]
        
        # Both should use click.prompt with hide_input=True
        assert 'click.prompt' in fleet_add_section, "click.prompt not found in add function"
        assert 'hide_input=True' in fleet_add_section, "hide_input=True not found in add function"
        assert 'confirmation_prompt=True' in fleet_add_section, "confirmation_prompt=True not found in add function"
        
        # fleet_cli should NOT have @click.argument('password') in the add function
        assert "@click.argument('password')" not in fleet_add_section, "password is still a CLI argument!"
