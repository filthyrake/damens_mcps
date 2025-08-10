"""
Command-line interface for the Warewulf MCP Server.
"""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from .warewulf_client import WarewulfClient
from .utils.logging import setup_logging
from .utils.validation import sanitize_config


class WarewulfCLI:
    """Command-line interface for Warewulf MCP Server."""
    
    def __init__(self):
        """Initialize CLI."""
        self.logger = setup_logging()
        self.client = None
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.error(f"Configuration file not found: {config_path}")
                sys.exit(1)
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def initialize_client(self, config: Dict[str, Any]) -> None:
        """Initialize Warewulf client."""
        try:
            self.client = WarewulfClient(config)
            self.logger.info("Warewulf client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            sys.exit(1)
    
    def print_json(self, data: Any, pretty: bool = True) -> None:
        """Print data as JSON."""
        if pretty:
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(data))
    
    def print_success(self, message: str, data: Any = None) -> None:
        """Print success message."""
        print(f"✅ {message}")
        if data:
            self.print_json(data)
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        print(f"❌ {message}")
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        print(f"ℹ️  {message}")
    
    async def test_connection(self) -> None:
        """Test connection to Warewulf server."""
        try:
            self.print_info("Testing connection to Warewulf server...")
            result = self.client.test_connection()
            
            if result.get('success'):
                self.print_success("Connection successful", result)
            else:
                self.print_error(f"Connection failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Connection test failed: {e}")
    
    async def get_version(self) -> None:
        """Get Warewulf server version."""
        try:
            self.print_info("Getting Warewulf server version...")
            result = self.client.get_version()
            self.print_success("Version retrieved", result)
            
        except Exception as e:
            self.print_error(f"Failed to get version: {e}")
    
    async def list_nodes(self) -> None:
        """List all nodes."""
        try:
            self.print_info("Listing nodes...")
            result = self.client.list_nodes()
            
            if result.get('success'):
                nodes = result.get('data', [])
                self.print_success(f"Found {len(nodes)} nodes", result)
            else:
                self.print_error(f"Failed to list nodes: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Failed to list nodes: {e}")
    
    async def get_node(self, node_id: str) -> None:
        """Get a specific node."""
        try:
            self.print_info(f"Getting node: {node_id}")
            result = self.client.get_node(node_id)
            
            if result.get('success'):
                self.print_success(f"Node {node_id} retrieved", result)
            else:
                self.print_error(f"Failed to get node: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Failed to get node: {e}")
    
    async def list_profiles(self) -> None:
        """List all profiles."""
        try:
            self.print_info("Listing profiles...")
            result = self.client.list_profiles()
            
            if result.get('success'):
                profiles = result.get('data', [])
                self.print_success(f"Found {len(profiles)} profiles", result)
            else:
                self.print_error(f"Failed to list profiles: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Failed to list profiles: {e}")
    
    async def list_images(self) -> None:
        """List all images."""
        try:
            self.print_info("Listing images...")
            result = self.client.list_images()
            
            if result.get('success'):
                images = result.get('data', [])
                self.print_success(f"Found {len(images)} images", result)
            else:
                self.print_error(f"Failed to list images: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Failed to list images: {e}")
    
    async def list_overlays(self) -> None:
        """List all overlays."""
        try:
            self.print_info("Listing overlays...")
            result = self.client.list_overlays()
            
            if result.get('success'):
                overlays = result.get('data', [])
                self.print_success(f"Found {len(overlays)} overlays", result)
            else:
                self.print_error(f"Failed to list overlays: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Failed to list overlays: {e}")
    
    async def show_status(self) -> None:
        """Show overall status."""
        try:
            self.print_info("Checking overall status...")
            
            # Test connection
            conn_result = self.client.test_connection()
            conn_status = "✅ Connected" if conn_result.get('success') else "❌ Disconnected"
            
            # Get version
            try:
                version_result = self.client.get_version()
                version = version_result.get('data', {}).get('version', 'Unknown')
            except:
                version = "Unknown"
            
            # Get basic counts
            try:
                nodes_result = self.client.list_nodes()
                node_count = len(nodes_result.get('data', [])) if nodes_result.get('success') else 0
            except:
                node_count = 0
            
            try:
                profiles_result = self.client.list_profiles()
                profile_count = len(profiles_result.get('data', [])) if profiles_result.get('success') else 0
            except:
                profile_count = 0
            
            try:
                images_result = self.client.list_images()
                image_count = len(images_result.get('data', [])) if images_result.get('success') else 0
            except:
                image_count = 0
            
            status = {
                "connection": conn_status,
                "version": version,
                "nodes": node_count,
                "profiles": profile_count,
                "images": image_count
            }
            
            self.print_success("Status retrieved", status)
            
        except Exception as e:
            self.print_error(f"Failed to get status: {e}")
    
    def run(self, args: argparse.Namespace) -> None:
        """Run CLI with given arguments."""
        # Load configuration
        config = self.load_config(args.config)
        
        # Initialize client
        self.initialize_client(config)
        
        # Execute command
        if args.command == 'test':
            asyncio.run(self.test_connection())
        elif args.command == 'version':
            asyncio.run(self.get_version())
        elif args.command == 'nodes':
            if args.node_id:
                asyncio.run(self.get_node(args.node_id))
            else:
                asyncio.run(self.list_nodes())
        elif args.command == 'profiles':
            asyncio.run(self.list_profiles())
        elif args.command == 'images':
            asyncio.run(self.list_images())
        elif args.command == 'overlays':
            asyncio.run(self.list_overlays())
        elif args.command == 'status':
            asyncio.run(self.show_status())
        else:
            self.print_error(f"Unknown command: {args.command}")
            sys.exit(1)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Warewulf MCP Server CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c config.json test                    # Test connection
  %(prog)s -c config.json version                 # Get server version
  %(prog)s -c config.json nodes                   # List all nodes
  %(prog)s -c config.json nodes node001          # Get specific node
  %(prog)s -c config.json profiles                # List profiles
  %(prog)s -c config.json images                  # List images
  %(prog)s -c config.json overlays                # List overlays
  %(prog)s -c config.json status                  # Show overall status
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        'command',
        choices=['test', 'version', 'nodes', 'profiles', 'images', 'overlays', 'status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'node_id',
        nargs='?',
        help='Node ID (for nodes command)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.command == 'nodes' and not args.node_id:
        # This is fine - will list all nodes
        pass
    elif args.command == 'nodes' and args.node_id:
        # This is fine - will get specific node
        pass
    elif args.node_id:
        parser.error(f"Unexpected argument: {args.node_id}")
    
    # Run CLI
    cli = WarewulfCLI()
    cli.run(args)


if __name__ == "__main__":
    main()
