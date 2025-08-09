"""Secure multi-server manager for iDRAC fleet management with encrypted passwords."""

import asyncio
import json
import os
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

# Try relative import first, fall back to absolute
try:
    from .idrac_client import IDracClient
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from idrac_client import IDracClient

class SecureMultiServerManager:
    """Manages multiple iDRAC servers with encrypted password storage."""
    
    def __init__(self, config_file: str = "fleet_servers.json", key_file: str = ".fleet_key"):
        """Initialize the secure multi-server manager.
        
        Args:
            config_file: Path to the encrypted servers configuration file
            key_file: Path to the encryption key file
        """
        self.config_file = Path(config_file)
        self.key_file = Path(key_file)
        self.fernet = None
        self.servers = {}
        self._initialize_encryption()
        self.load_config()
    
    def _initialize_encryption(self):
        """Initialize encryption key."""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
            self.fernet = Fernet(key)
        else:
            # Generate new key
            print("🔐 Setting up encryption for fleet management...")
            password = getpass.getpass("Enter a master password for fleet encryption: ")
            if not password:
                raise ValueError("Master password cannot be empty")
            
            # Generate key from password
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.fernet = Fernet(key)
            
            # Save key (in production, you might want to store this more securely)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            print(f"✅ Encryption key saved to {self.key_file}")
            print("⚠️  Keep this key file secure! If lost, you'll need to reconfigure all servers.")
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt a password."""
        return self.fernet.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password."""
        return self.fernet.decrypt(encrypted_password.encode()).decode()
    
    def load_config(self):
        """Load server configurations from encrypted file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    encrypted_data = json.load(f)
                
                # Decrypt the data
                decrypted_data = self.fernet.decrypt(encrypted_data['data'].encode())
                config = json.loads(decrypted_data.decode())
                self.servers = config.get('servers', {})
                
                print(f"✅ Loaded {len(self.servers)} servers from {self.config_file}")
            except Exception as e:
                print(f"❌ Failed to load server config: {e}")
                self.servers = {}
        else:
            print(f"⚠️ No server config file found at {self.config_file}")
            self.servers = {}
    
    def save_config(self):
        """Save server configurations to encrypted file."""
        try:
            config = {"servers": self.servers}
            config_json = json.dumps(config)
            
            # Encrypt the data
            encrypted_data = self.fernet.encrypt(config_json.encode())
            
            # Save encrypted data
            with open(self.config_file, 'w') as f:
                json.dump({
                    'version': '1.0',
                    'data': encrypted_data.decode()
                }, f, indent=2)
            
            print(f"✅ Saved {len(self.servers)} servers to {self.config_file}")
        except Exception as e:
            print(f"❌ Failed to save server config: {e}")
    
    def add_server(self, name: str, host: str, username: str, password: str, 
                   port: int = 443, protocol: str = "https", ssl_verify: bool = False):
        """Add a server to the configuration with encrypted password.
        
        Args:
            name: Server name/identifier
            host: iDRAC host address
            username: iDRAC username
            password: iDRAC password (will be encrypted)
            port: iDRAC port
            protocol: Protocol (http/https)
            ssl_verify: Whether to verify SSL certificates
        """
        self.servers[name] = {
            "host": host,
            "port": port,
            "protocol": protocol,
            "username": username,
            "password_encrypted": self._encrypt_password(password),
            "ssl_verify": ssl_verify,
            "enabled": True
        }
        self.save_config()
        print(f"✅ Added server '{name}' ({host}) with encrypted password")
    
    def get_server_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server with decrypted password.
        
        Args:
            name: Server name
            
        Returns:
            Server configuration with decrypted password or None if not found
        """
        if name not in self.servers:
            return None
        
        config = self.servers[name].copy()
        
        # Decrypt password
        if 'password_encrypted' in config:
            config['password'] = self._decrypt_password(config['password_encrypted'])
            del config['password_encrypted']
        
        return config
    
    def remove_server(self, name: str):
        """Remove a server from the configuration.
        
        Args:
            name: Server name to remove
        """
        if name in self.servers:
            del self.servers[name]
            self.save_config()
            print(f"✅ Removed server '{name}'")
        else:
            print(f"❌ Server '{name}' not found")
    
    def list_servers(self) -> List[str]:
        """List all configured servers.
        
        Returns:
            List of server names
        """
        return list(self.servers.keys())
    
    def enable_server(self, name: str):
        """Enable a server.
        
        Args:
            name: Server name to enable
        """
        if name in self.servers:
            self.servers[name]["enabled"] = True
            self.save_config()
            print(f"✅ Enabled server '{name}'")
        else:
            print(f"❌ Server '{name}' not found")
    
    def disable_server(self, name: str):
        """Disable a server.
        
        Args:
            name: Server name to disable
        """
        if name in self.servers:
            self.servers[name]["enabled"] = False
            self.save_config()
            print(f"✅ Disabled server '{name}'")
        else:
            print(f"❌ Server '{name}' not found")
    
    async def test_server(self, name: str) -> Dict[str, Any]:
        """Test connection to a specific server.
        
        Args:
            name: Server name to test
            
        Returns:
            Test result
        """
        config = self.get_server_config(name)
        if not config:
            return {
                "status": "error",
                "message": f"Server '{name}' not found"
            }
        
        if not config.get("enabled", True):
            return {
                "status": "error",
                "message": f"Server '{name}' is disabled"
            }
        
        try:
            async with IDracClient(config) as client:
                result = await client.test_connection()
                return {
                    "status": "success",
                    "server": name,
                    "data": result,
                    "message": f"Server '{name}' connection successful"
                }
        except Exception as e:
            return {
                "status": "error",
                "server": name,
                "message": f"Server '{name}' connection failed: {e}"
            }
    
    async def test_all_servers(self) -> Dict[str, Any]:
        """Test connection to all enabled servers.
        
        Returns:
            Results for all servers
        """
        results = {}
        enabled_servers = [name for name, config in self.servers.items() 
                          if config.get("enabled", True)]
        
        print(f"🔍 Testing {len(enabled_servers)} enabled servers...")
        
        for name in enabled_servers:
            print(f"  Testing {name}...")
            result = await self.test_server(name)
            results[name] = result
        
        return results
    
    async def get_fleet_system_info(self) -> Dict[str, Any]:
        """Get system information from all enabled servers.
        
        Returns:
            System information for all servers
        """
        results = {}
        enabled_servers = [name for name, config in self.servers.items() 
                          if config.get("enabled", True)]
        
        print(f"📊 Getting system info from {len(enabled_servers)} servers...")
        
        for name in enabled_servers:
            try:
                config = self.get_server_config(name)
                async with IDracClient(config) as client:
                    system_info = await client.get_system_info()
                    results[name] = {
                        "status": "success",
                        "data": system_info["data"]
                    }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    async def get_fleet_health(self) -> Dict[str, Any]:
        """Get health status from all enabled servers.
        
        Returns:
            Health information for all servers
        """
        results = {}
        enabled_servers = [name for name, config in self.servers.items() 
                          if config.get("enabled", True)]
        
        print(f"🏥 Getting health status from {len(enabled_servers)} servers...")
        
        for name in enabled_servers:
            try:
                config = self.get_server_config(name)
                async with IDracClient(config) as client:
                    health = await client.get_system_health()
                    results[name] = {
                        "status": "success",
                        "data": health["data"]
                    }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    async def get_fleet_power_status(self) -> Dict[str, Any]:
        """Get power status from all enabled servers.
        
        Returns:
            Power status for all servers
        """
        results = {}
        enabled_servers = [name for name, config in self.servers.items() 
                          if config.get("enabled", True)]
        
        print(f"⚡ Getting power status from {len(enabled_servers)} servers...")
        
        for name in enabled_servers:
            try:
                config = self.get_server_config(name)
                async with IDracClient(config) as client:
                    power = await client.get_power_status()
                    results[name] = {
                        "status": "success",
                        "data": power["data"]
                    }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    def create_sample_config(self):
        """Create a sample server configuration file."""
        print("🔐 Creating sample encrypted configuration...")
        print("⚠️  You'll need to set a master password for encryption")
        
        # This will trigger the encryption setup
        self._initialize_encryption()
        
        sample_config = {
            "servers": {
                "server1": {
                    "host": "192.168.1.100",
                    "port": 443,
                    "protocol": "https",
                    "username": "root",
                    "password_encrypted": self._encrypt_password("your-password"),
                    "ssl_verify": False,
                    "enabled": True
                },
                "server2": {
                    "host": "192.168.1.101",
                    "port": 443,
                    "protocol": "https",
                    "username": "root",
                    "password_encrypted": self._encrypt_password("your-password"),
                    "ssl_verify": False,
                    "enabled": True
                }
            }
        }
        
        self.servers = sample_config["servers"]
        self.save_config()
        
        print(f"✅ Created sample encrypted configuration at {self.config_file}")
        print("💡 Edit the file to add your actual server details")
        print("🔐 Passwords are now encrypted and secure")
