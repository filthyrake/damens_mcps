#!/usr/bin/env python3
"""Migration script to convert plaintext config.json to encrypted format.

This script helps users migrate from plaintext password storage to encrypted storage.
It reads the existing config.json, encrypts the password, and saves it back.

Usage:
    python migrate_config.py [--config config.json] [--backup]
"""

import argparse
import getpass
import json
import shutil
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from secure_config import SecureConfigManager
except ImportError as e:
    print(f"❌ Failed to import secure_config module: {e}", file=sys.stderr)
    print("Make sure you're running this from the proxmox-mcp directory", file=sys.stderr)
    sys.exit(1)


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate Proxmox MCP config from plaintext to encrypted password storage"
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to config file (default: config.json)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup of original config file'
    )
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Non-interactive mode (fails if master password not provided via env)'
    )
    
    args = parser.parse_args()
    config_path = Path(args.config)
    
    # Check if config file exists
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}", file=sys.stderr)
        print("\nExpected to find a config.json file.", file=sys.stderr)
        print("If you haven't created one yet, copy config.example.json to config.json first.", file=sys.stderr)
        sys.exit(1)
    
    # Check if already encrypted
    if SecureConfigManager.is_encrypted_config(config_path):
        print(f"✅ Configuration file is already encrypted: {config_path}")
        print("No migration needed.")
        sys.exit(0)
    
    print("🔐 Proxmox MCP Configuration Migration Tool")
    print("=" * 50)
    print(f"Config file: {config_path}")
    print()
    
    # Load existing plaintext config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"❌ Failed to read config file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Verify it has a password field
    if 'password' not in config:
        print("❌ Config file doesn't contain a 'password' field", file=sys.stderr)
        print("Cannot migrate without a password.", file=sys.stderr)
        sys.exit(1)
    
    print("Current configuration:")
    print(f"  Host: {config.get('host', 'N/A')}")
    print(f"  Username: {config.get('username', 'N/A')}")
    print(f"  Password: {'*' * len(config.get('password', ''))}")
    print()
    
    # Create backup if requested
    if args.backup:
        backup_path = config_path.with_suffix('.json.backup')
        try:
            shutil.copy2(config_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
        except OSError as e:
            print(f"❌ Failed to create backup: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Get master password
    if args.no_interactive:
        # Try to get from environment
        master_password = os.environ.get('PROXMOX_MASTER_PASSWORD')
        if not master_password:
            print("❌ No master password provided in PROXMOX_MASTER_PASSWORD env var", file=sys.stderr)
            sys.exit(1)
    else:
        print("Enter a master password to encrypt your configuration.")
        print("You will need this password every time you start the MCP server.")
        print()
        master_password = getpass.getpass("Master password: ")
        confirm_password = getpass.getpass("Confirm master password: ")
        
        if master_password != confirm_password:
            print("❌ Passwords do not match", file=sys.stderr)
            sys.exit(1)
        
        if not master_password:
            print("❌ Master password cannot be empty", file=sys.stderr)
            sys.exit(1)
    
    # Encrypt and save
    print()
    print("🔒 Encrypting password...")
    
    try:
        manager = SecureConfigManager(config_file=str(config_path))
        manager.save_encrypted_config(config, master_password)
        
        print()
        print("✅ Migration complete!")
        print()
        print("Your password is now encrypted using PBKDF2-SHA256 with 480,000 iterations.")
        print("The encryption key is NOT stored on disk - you'll need to provide the")
        print("master password each time you start the server.")
        print()
        print("Next steps:")
        print("  1. Test the encrypted config:")
        print(f"     PROXMOX_MASTER_PASSWORD='{master_password}' python working_proxmox_server.py")
        print()
        print("  2. For production use, set the master password via environment variable:")
        print("     export PROXMOX_MASTER_PASSWORD='your-master-password'")
        print()
        
        if args.backup:
            print(f"  3. After confirming it works, you can delete the backup: {backup_path}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    import os  # Import here for --no-interactive mode
    main()
