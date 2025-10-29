"""Test JWTAuthManager methods and user management functionality."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from auth import JWTAuthManager, User, UserInDB


class TestJWTAuthManagerMethods:
    """Test JWTAuthManager methods are properly accessible."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create a JWTAuthManager instance for testing."""
        return JWTAuthManager(secret_key="test-secret-key-12345")
    
    def test_create_user_method_exists(self, auth_manager):
        """Test that create_user method exists on JWTAuthManager."""
        assert hasattr(auth_manager, 'create_user')
        assert callable(auth_manager.create_user)
    
    def test_list_users_method_exists(self, auth_manager):
        """Test that list_users method exists on JWTAuthManager."""
        assert hasattr(auth_manager, 'list_users')
        assert callable(auth_manager.list_users)
    
    def test_create_user_functionality(self, auth_manager):
        """Test that create_user method works correctly."""
        # Create a new user
        user = auth_manager.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            full_name="Test User"
        )
        
        # Verify user was created
        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.disabled is False
        
        # Verify user is in the database
        stored_user = auth_manager.get_user("testuser")
        assert stored_user is not None
        assert isinstance(stored_user, UserInDB)
        assert stored_user.username == "testuser"
    
    def test_create_user_duplicate_raises_error(self, auth_manager):
        """Test that creating a duplicate user raises ValueError."""
        # Create first user
        auth_manager.create_user("testuser", "testpass123")
        
        # Attempt to create duplicate should raise ValueError
        with pytest.raises(ValueError, match="User already exists"):
            auth_manager.create_user("testuser", "anotherpass")
    
    def test_list_users_functionality(self, auth_manager):
        """Test that list_users method works correctly."""
        # Should have default admin user
        users = auth_manager.list_users()
        assert len(users) >= 1
        assert isinstance(users, list)
        assert all(isinstance(u, User) for u in users)
        
        # Find admin user
        admin_user = next((u for u in users if u.username == "admin"), None)
        assert admin_user is not None
        
        # Create additional users
        auth_manager.create_user("user1", "pass1", email="user1@example.com")
        auth_manager.create_user("user2", "pass2", email="user2@example.com")
        
        # List should now have more users
        users = auth_manager.list_users()
        assert len(users) >= 3
        
        # Verify new users are in the list
        usernames = [u.username for u in users]
        assert "user1" in usernames
        assert "user2" in usernames
    
    def test_list_users_excludes_password(self, auth_manager):
        """Test that list_users doesn't expose hashed passwords."""
        # Create a user
        auth_manager.create_user("testuser", "testpass123")
        
        # Get users list
        users = auth_manager.list_users()
        
        # Verify User objects don't have hashed_password attribute
        for user in users:
            assert isinstance(user, User)
            assert not hasattr(user, 'hashed_password')
    
    def test_methods_are_instance_methods(self, auth_manager):
        """Test that create_user and list_users are bound instance methods."""
        # These should be bound methods, not functions
        assert hasattr(auth_manager.create_user, '__self__')
        assert hasattr(auth_manager.list_users, '__self__')
        assert auth_manager.create_user.__self__ is auth_manager
        assert auth_manager.list_users.__self__ is auth_manager


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
