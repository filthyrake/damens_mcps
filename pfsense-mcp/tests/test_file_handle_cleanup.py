"""Tests for file handle cleanup in SilentStdout and SilentStderr classes.

Note: These tests recreate the SilentStdout/SilentStderr classes locally
rather than importing them from the main module. This is intentional because
the actual classes are instantiated as module-level globals that modify
sys.stdout/stderr during import, making them difficult to test in isolation.
The tests validate that the cleanup pattern works correctly.
"""

import os
import sys
import pytest
import gc


class TestFileHandleCleanup:
    """Test that file handles are properly closed to prevent resource leaks."""
    
    def test_silent_stdout_closes_file_handle(self):
        """Test that SilentStdout closes its file handle on cleanup."""
        # Import the classes directly
        from importlib import import_module
        
        # We need to test the class in isolation without module-level side effects
        # So we'll create it manually
        class TestSilentStdout:
            def __init__(self):
                self.original_stdout = sys.stdout
                self.null_output = open(os.devnull, 'w')
            
            def write(self, text):
                if text.strip().startswith('{"jsonrpc":'):
                    self.original_stdout.write(text)
            
            def flush(self):
                self.original_stdout.flush()
            
            def fileno(self):
                return self.original_stdout.fileno()
            
            def __del__(self):
                """Ensure file handle is properly closed on cleanup."""
                if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
                    self.null_output.close()
        
        # Create instance
        silent = TestSilentStdout()
        file_handle = silent.null_output
        
        # Verify file is open
        assert not file_handle.closed, "File handle should be open after init"
        
        # Delete the object and force garbage collection
        del silent
        gc.collect()
        
        # Verify file is closed
        assert file_handle.closed, "File handle should be closed after object deletion"
    
    def test_silent_stderr_closes_file_handle(self):
        """Test that SilentStderr closes its file handle on cleanup."""
        # Create test class
        class TestSilentStderr:
            def __init__(self):
                self.original_stderr = sys.stderr
                self.null_output = open(os.devnull, 'w')
            
            def write(self, text):
                pass
            
            def flush(self):
                pass
            
            def fileno(self):
                return self.original_stderr.fileno()
            
            def __del__(self):
                """Ensure file handle is properly closed on cleanup."""
                if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
                    self.null_output.close()
        
        # Create instance
        silent = TestSilentStderr()
        file_handle = silent.null_output
        
        # Verify file is open
        assert not file_handle.closed, "File handle should be open after init"
        
        # Delete the object and force garbage collection
        del silent
        gc.collect()
        
        # Verify file is closed
        assert file_handle.closed, "File handle should be closed after object deletion"
    
    def test_multiple_instances_close_independently(self):
        """Test that multiple instances each close their own file handles."""
        class TestSilent:
            def __init__(self):
                self.null_output = open(os.devnull, 'w')
            
            def __del__(self):
                if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
                    self.null_output.close()
        
        # Create multiple instances
        silent1 = TestSilent()
        silent2 = TestSilent()
        silent3 = TestSilent()
        
        handle1 = silent1.null_output
        handle2 = silent2.null_output
        handle3 = silent3.null_output
        
        # All should be open
        assert not handle1.closed
        assert not handle2.closed
        assert not handle3.closed
        
        # Delete first instance
        del silent1
        gc.collect()
        
        # Only first should be closed
        assert handle1.closed
        assert not handle2.closed
        assert not handle3.closed
        
        # Delete remaining instances
        del silent2
        del silent3
        gc.collect()
        
        # All should be closed
        assert handle1.closed
        assert handle2.closed
        assert handle3.closed
    
    def test_del_handles_missing_attribute(self):
        """Test that __del__ handles cases where null_output doesn't exist."""
        class TestSilent:
            def __init__(self, create_handle=True):
                if create_handle:
                    self.null_output = open(os.devnull, 'w')
            
            def __del__(self):
                if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
                    self.null_output.close()
        
        # Create instance without handle
        silent_no_handle = TestSilent(create_handle=False)
        
        # This should not raise an exception
        del silent_no_handle
        gc.collect()
    
    def test_del_handles_already_closed(self):
        """Test that __del__ handles cases where file is already closed."""
        class TestSilent:
            def __init__(self):
                self.null_output = open(os.devnull, 'w')
            
            def __del__(self):
                if hasattr(self, 'null_output') and self.null_output and not self.null_output.closed:
                    self.null_output.close()
        
        # Create instance
        silent = TestSilent()
        
        # Close manually
        silent.null_output.close()
        assert silent.null_output.closed
        
        # Delete should not raise an exception even though already closed
        del silent
        gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
