"""Authentication manager for iDRAC MCP Server."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .utils.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthManager:
    """Manages authentication and JWT token operations."""
    
    def __init__(self, config: Dict):
        """Initialize the authentication manager.
        
        Args:
            config: Configuration dictionary containing secret key and other auth settings
        """
        self.secret_key = config.get("secret_key")
        if not self.secret_key:
            # Generate a secure secret key if not provided
            self.secret_key = secrets.token_urlsafe(32)
            logger.warning("No secret key provided, generated a new one")
        
        self.access_token_expire_minutes = config.get("access_token_expire_minutes", ACCESS_TOKEN_EXPIRE_MINUTES)
    
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
    
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration delta
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"JWT token verification failed: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str, expected_credentials: Dict) -> bool:
        """Authenticate a user with username and password.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            expected_credentials: Dictionary containing expected username and password hash
            
        Returns:
            True if authentication successful, False otherwise
        """
        expected_username = expected_credentials.get("username")
        expected_password_hash = expected_credentials.get("password_hash")
        
        if not expected_username or not expected_password_hash:
            logger.warning("Missing expected credentials")
            return False
        
        if username != expected_username:
            logger.warning(f"Username mismatch: {username}")
            return False
        
        if not self.verify_password(password, expected_password_hash):
            logger.warning(f"Password verification failed for user: {username}")
            return False
        
        logger.info(f"User authenticated successfully: {username}")
        return True
    
    def create_user_token(self, username: str, admin_token: Optional[str] = None) -> str:
        """Create a token for a user (for admin token authentication).
        
        Args:
            username: Username for the token
            admin_token: Optional admin token for validation
            
        Returns:
            JWT token string
        """
        # In a real implementation, you might validate the admin token here
        if admin_token:
            # Validate admin token logic would go here
            pass
        
        token_data = {
            "sub": username,
            "type": "user",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return self.create_access_token(token_data)
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get the expiration time of a token.
        
        Args:
            token: JWT token string
            
        Returns:
            Expiration datetime or None if invalid
        """
        payload = self.verify_token(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if a token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        expiration = self.get_token_expiration(token)
        if expiration:
            return datetime.utcnow() > expiration
        return True
