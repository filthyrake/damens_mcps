"""Authentication manager for TrueNAS API access and JWT authentication."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

try:
    from .exceptions import TrueNASError, TrueNASTokenError, TrueNASAuthenticationError
except ImportError:
    from exceptions import TrueNASError, TrueNASTokenError, TrueNASAuthenticationError

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()


class AuthConfig(BaseModel):
    """Authentication configuration."""
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    token_file: Optional[str] = Field(None, description="File to store authentication token")
    token_expiry: int = Field(3600, description="Token expiry time in seconds")


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None


class User(BaseModel):
    """User model for MCP authentication."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class AuthManager:
    """Manages authentication for TrueNAS API access."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the authentication manager.
        
        Args:
            config: Configuration dictionary containing authentication details
        """
        self.config = AuthConfig(**config)
        self._token: Optional[str] = None
        self._token_expiry: Optional[float] = None
        
        # Load token from file if specified
        if self.config.token_file:
            self._load_token_from_file()
    
    def _load_token_from_file(self) -> None:
        """Load authentication token from file."""
        try:
            token_path = Path(self.config.token_file)
            if token_path.exists():
                with open(token_path, 'r') as f:
                    self._token = f.read().strip()
                    logger.info("Loaded authentication token from file")
        except OSError as e:
            logger.warning(f"Failed to load token from file {self.config.token_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error loading token from file {self.config.token_file}: {e}", exc_info=True)
    
    def _save_token_to_file(self, token: str) -> None:
        """Save authentication token to file.
        
        Args:
            token: Authentication token to save
        """
        if not self.config.token_file:
            return
        
        try:
            token_path = Path(self.config.token_file)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(token_path, 'w') as f:
                f.write(token)
            
            # Set appropriate permissions (read/write for owner only)
            token_path.chmod(0o600)
            logger.info("Saved authentication token to file")
        except OSError as e:
            logger.warning(f"Failed to save token to file {self.config.token_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error saving token to file {self.config.token_file}: {e}", exc_info=True)
    
    def _clear_token_file(self) -> None:
        """Clear authentication token from file."""
        if not self.config.token_file:
            return
        
        try:
            token_path = Path(self.config.token_file)
            if token_path.exists():
                token_path.unlink()
                logger.info("Cleared authentication token from file")
        except OSError as e:
            logger.warning(f"Failed to clear token file {self.config.token_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error clearing token file {self.config.token_file}: {e}", exc_info=True)
    
    def get_auth_method(self) -> str:
        """Get the authentication method being used.
        
        Returns:
            Authentication method ('api_key', 'username_password', or 'token')
        """
        if self.config.api_key:
            return "api_key"
        elif self.config.username and self.config.password:
            return "username_password"
        elif self._token:
            return "token"
        else:
            return "none"
    
    def get_api_key(self) -> Optional[str]:
        """Get the API key if available.
        
        Returns:
            API key or None
        """
        return self.config.api_key
    
    def get_credentials(self) -> Optional[Dict[str, str]]:
        """Get username and password credentials if available.
        
        Returns:
            Dictionary with username and password or None
        """
        if self.config.username and self.config.password:
            return {
                "username": self.config.username,
                "password": self.config.password
            }
        return None
    
    def get_token(self) -> Optional[str]:
        """Get the current authentication token if available.
        
        Returns:
            Authentication token or None
        """
        return self._token
    
    def set_token(self, token: str) -> None:
        """Set the authentication token.
        
        Args:
            token: Authentication token to set
        """
        self._token = token
        self._token_expiry = None  # Will be set when token is used
        
        # Save token to file if configured
        self._save_token_to_file(token)
        logger.info("Set authentication token")
    
    def clear_token(self) -> None:
        """Clear the current authentication token."""
        self._token = None
        self._token_expiry = None
        self._clear_token_file()
        logger.info("Cleared authentication token")
    
    def is_authenticated(self) -> bool:
        """Check if authentication is available.
        
        Returns:
            True if authentication is available, False otherwise
        """
        return (
            self.config.api_key is not None or
            (self.config.username is not None and self.config.password is not None) or
            self._token is not None
        )
    
    def validate_config(self) -> bool:
        """Validate the authentication configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check if at least one authentication method is configured
        if not self.is_authenticated():
            logger.error("No authentication method configured")
            return False
        
        # Check for conflicting configurations
        auth_methods = []
        if self.config.api_key:
            auth_methods.append("api_key")
        if self.config.username and self.config.password:
            auth_methods.append("username_password")
        if self._token:
            auth_methods.append("token")
        
        if len(auth_methods) > 1:
            logger.warning(f"Multiple authentication methods configured: {auth_methods}")
        
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests.
        
        Returns:
            Dictionary containing authentication headers
        """
        headers = {}
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        return headers
    
    def rotate_api_key(self, new_api_key: str) -> None:
        """Rotate the API key.
        
        Args:
            new_api_key: New API key to use
        """
        old_api_key = self.config.api_key
        self.config.api_key = new_api_key
        
        # Clear any stored token since we're using API key auth
        self.clear_token()
        
        logger.info("Rotated API key")
        
        # Log the rotation (without exposing the actual keys)
        if old_api_key:
            logger.info("API key rotated (old key was present)")
        else:
            logger.info("API key set (no previous key)")
    
    def update_credentials(self, username: str, password: str) -> None:
        """Update username and password credentials.
        
        Args:
            username: New username
            password: New password
        """
        self.config.username = username
        self.config.password = password
        
        # Clear any stored token since we're using credential auth
        self.clear_token()
        
        logger.info("Updated username and password credentials")
    
    def get_auth_summary(self) -> Dict[str, Any]:
        """Get a summary of the current authentication configuration.
        
        Returns:
            Dictionary containing authentication summary
        """
        return {
            "method": self.get_auth_method(),
            "has_api_key": self.config.api_key is not None,
            "has_credentials": self.config.username is not None and self.config.password is not None,
            "has_token": self._token is not None,
            "token_file": self.config.token_file,
            "is_authenticated": self.is_authenticated(),
        }


class JWTAuthManager:
    """JWT authentication manager for MCP clients."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", access_token_expire_minutes: int = 30):
        """Initialize JWT authentication manager.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm to use
            access_token_expire_minutes: Token expiry time in minutes
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        
        # In-memory user store (in production, use a database)
        self.users_db: Dict[str, UserInDB] = {}
        
        # Create default admin user if admin token is provided
        self._create_default_users()
    
    def _create_default_users(self) -> None:
        """Create default users for development."""
        # Create a default admin user
        admin_user = UserInDB(
            username="admin",
            email="admin@truenas-mcp.local",
            full_name="Administrator",
            disabled=False,
            hashed_password=pwd_context.hash("admin123")  # TODO: Change in production!
        )
        self.users_db[admin_user.username] = admin_user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User object or None if not found
        """
        return self.users_db.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiry time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username)
            return token_data
        except JWTError:
            return None
    
    def get_current_user(self, token: str = Depends(security)) -> User:
        """Get current user from token.
        
        Args:
            token: JWT token from request
            
        Returns:
            Current user
            
        Raises:
            HTTPException: If authentication fails
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token.credentials, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        
        user = self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
    
    def get_current_active_user(self, current_user: User = Depends(get_current_user)) -> User:
        """Get current active user.
        
        Args:
            current_user: Current user from token
            
        Returns:
            Current active user
            
        Raises:
            HTTPException: If user is disabled
        """
        if current_user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    def get_current_user_dependency(self):
        """Get the get_current_user dependency function."""
        return self.get_current_user
    
    def get_current_active_user_dependency(self):
        """Get the get_current_active_user dependency function."""
        return self.get_current_active_user
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, full_name: Optional[str] = None) -> User:
        """Create a new user.
        
        Args:
            username: Username
            password: Password
            email: Email address
            full_name: Full name
            
        Returns:
            Created user
            
        Raises:
            ValueError: If user already exists
        """
        if username in self.users_db:
            raise ValueError("User already exists")
        
        hashed_password = self.get_password_hash(password)
        user = UserInDB(
            username=username,
            email=email,
            full_name=full_name,
            disabled=False,
            hashed_password=hashed_password
        )
        self.users_db[username] = user
        return user
    
    def list_users(self) -> list[User]:
        """List all users.
        
        Returns:
            List of users
        """
        return [User(**user.model_dump(exclude={'hashed_password'})) for user in self.users_db.values()]


# Global JWT auth manager instance for dependency injection
_jwt_auth_manager: Optional[JWTAuthManager] = None


def get_jwt_auth_manager() -> JWTAuthManager:
    """Get the global JWT auth manager instance."""
    global _jwt_auth_manager
    if _jwt_auth_manager is None:
        raise RuntimeError("JWT auth manager not initialized")
    return _jwt_auth_manager


def set_jwt_auth_manager(auth_manager: JWTAuthManager) -> None:
    """Set the global JWT auth manager instance."""
    global _jwt_auth_manager
    _jwt_auth_manager = auth_manager


def get_current_user_dependency(token: str = Depends(security)) -> User:
    """Dependency function to get current user from token."""
    auth_manager = get_jwt_auth_manager()
    return auth_manager.get_current_user(token)


def get_current_active_user_dependency(current_user: User = Depends(get_current_user_dependency)) -> User:
    """Dependency function to get current active user."""
    auth_manager = get_jwt_auth_manager()
    return auth_manager.get_current_active_user(current_user)
