"""Secure configuration management with encrypted password storage for Proxmox MCP."""

import base64
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureConfigManager:
    """Manages Proxmox configuration with encrypted password storage.
    
    Supports both plaintext (legacy, deprecated) and encrypted password formats.
    Uses password-based key derivation (PBKDF2-SHA256) following OWASP 2023 recommendations.
    """
    
    def __init__(self, config_file: str = "config.json", master_password: Optional[str] = None):
        """Initialize the secure configuration manager.
        
        Args:
            config_file: Path to the configuration file
            master_password: Master password for deriving encryption key (required for encrypted configs)
        """
        self.config_file = Path(config_file)
        self.fernet = None
        self.salt = None
        self.config_data = None
        self.master_password = master_password
        
    def _debug_print(self, message: str):
        """Print debug messages to stderr to avoid interfering with MCP protocol."""
        print(f"SecureConfig: {message}", file=sys.stderr)
    
    def _initialize_encryption(self, salt: bytes):
        """Initialize encryption using password-based key derivation.
        
        Args:
            salt: Salt bytes for key derivation
        """
        if not self.master_password:
            raise ValueError("Master password required for encrypted configuration")
        
        self.salt = salt
        
        # Derive key from password using PBKDF2 (OWASP 2023 recommendation: 480,000 iterations)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=480000,  # OWASP 2023 recommendation for PBKDF2-SHA256
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        self.fernet = Fernet(key)
        self._debug_print("Encryption key derived from password")
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt a password.
        
        Args:
            password: Plaintext password
            
        Returns:
            Encrypted password as base64 string
        """
        if not self.fernet:
            raise ValueError("Encryption not initialized")
        return self.fernet.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password.
        
        Args:
            encrypted_password: Encrypted password as base64 string
            
        Returns:
            Decrypted plaintext password
        """
        if not self.fernet:
            raise ValueError("Encryption not initialized")
        return self.fernet.decrypt(encrypted_password.encode()).decode()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, supporting both plaintext and encrypted formats.
        
        Returns:
            Configuration dictionary with decrypted password
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config format is invalid or decryption fails
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        try:
            with open(self.config_file, 'r') as f:
                self.config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        
        # Check if password is encrypted
        if 'password_encrypted' in self.config_data:
            # Encrypted format
            if 'salt' not in self.config_data:
                raise ValueError("Encrypted config missing salt field")
            
            # Initialize encryption with salt from config
            salt = base64.b64decode(self.config_data['salt'])
            self._initialize_encryption(salt)
            
            # Decrypt password
            try:
                decrypted_password = self._decrypt_password(self.config_data['password_encrypted'])
                
                # Return config with decrypted password
                config = self.config_data.copy()
                config['password'] = decrypted_password
                del config['password_encrypted']
                del config['salt']  # Don't include salt in returned config
                
                self._debug_print("✅ Loaded encrypted configuration")
                return config
                
            except Exception as e:
                raise ValueError(f"Failed to decrypt password. Wrong master password? Error: {e}")
        
        elif 'password' in self.config_data:
            # Plaintext format (legacy, deprecated)
            self._debug_print("⚠️  WARNING: Configuration uses PLAINTEXT password storage!")
            self._debug_print("⚠️  This is a SECURITY RISK. Please migrate to encrypted storage.")
            self._debug_print("⚠️  Run: python migrate_config.py")
            self._debug_print("")
            return self.config_data.copy()
        
        else:
            raise ValueError("Configuration missing both 'password' and 'password_encrypted' fields")
    
    def save_encrypted_config(self, config: Dict[str, Any], master_password: str) -> None:
        """Save configuration with encrypted password.
        
        Args:
            config: Configuration dictionary with plaintext password
            master_password: Master password for encryption
            
        Raises:
            ValueError: If config is invalid or encryption fails
        """
        if 'password' not in config:
            raise ValueError("Configuration missing 'password' field")
        
        
        
        # Generate new salt
        self.salt = self.generate_salt()
        self.master_password = master_password
        self._initialize_encryption(self.salt)
        
        # Encrypt password
        encrypted_password = self._encrypt_password(config['password'])
        
        # Create encrypted config
        encrypted_config = config.copy()
        encrypted_config['password_encrypted'] = encrypted_password
        encrypted_config['salt'] = base64.b64encode(self.salt).decode()
        del encrypted_config['password']  # Remove plaintext password
        
        # Save to file
        with open(self.config_file, 'w') as f:
            json.dump(encrypted_config, f, indent=2)
        
        self._debug_print(f"✅ Saved encrypted configuration to {self.config_file}")
        self._debug_print("🔒 Password encrypted with PBKDF2-SHA256 (480,000 iterations)")
    
    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random salt for key derivation.
        
        Returns:
            16 bytes of random data
        """
        return os.urandom(16)
    
    @staticmethod
    def is_encrypted_config(config_file: Path) -> bool:
        """Check if a config file uses encrypted password storage.
        
        Args:
            config_file: Path to config file
            
        Returns:
            True if config uses encrypted storage, False otherwise
        """
        if not config_file.exists():
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return 'password_encrypted' in config and 'salt' in config
        except (json.JSONDecodeError, OSError):
            return False
