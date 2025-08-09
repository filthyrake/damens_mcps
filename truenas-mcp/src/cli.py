"""Command-line interface for TrueNAS MCP server."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .server import TrueNASMCPServer
from .truenas_client import TrueNASClient
from .auth import AuthManager
from .utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def cli(ctx, config, log_level, log_file):
    """TrueNAS MCP Server - Command Line Interface."""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['log_level'] = log_level
    ctx.obj['log_file'] = log_file
    
    # Set up logging
    setup_logging(level=log_level, log_file=log_file)


@cli.command()
@click.option('--host', required=True, help='TrueNAS host address')
@click.option('--port', default=443, help='TrueNAS port')
@click.option('--api-key', help='API key for authentication')
@click.option('--username', help='Username for authentication')
@click.option('--password', help='Password for authentication')
@click.option('--verify-ssl/--no-verify-ssl', default=True, help='Verify SSL certificates')
@click.option('--output', '-o', type=click.Path(), help='Output file for configuration')
def configure(host, port, api_key, username, password, verify_ssl, output):
    """Configure TrueNAS connection settings."""
    config = {
        'host': host,
        'port': port,
        'verify_ssl': verify_ssl
    }
    
    if api_key:
        config['api_key'] = api_key
    elif username and password:
        config['username'] = username
        config['password'] = password
    else:
        console.print("[red]Error: Either API key or username/password must be provided[/red]")
        sys.exit(1)
    
    # Validate configuration
    try:
        from .utils.validation import validate_config
        validate_config(config)
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)
    
    # Save configuration
    if output:
        config_path = Path(output)
    else:
        config_path = Path.home() / '.truenas-mcp' / 'config.json'
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    console.print(f"[green]Configuration saved to: {config_path}[/green]")


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--host', help='TrueNAS host address')
@click.option('--port', type=int, help='TrueNAS port')
@click.option('--api-key', help='API key for authentication')
@click.option('--username', help='Username for authentication')
@click.option('--password', help='Password for authentication')
def test(config, host, port, api_key, username, password):
    """Test connection to TrueNAS server."""
    # Load configuration
    config_data = _load_config(config, host, port, api_key, username, password)
    
    if not config_data:
        console.print("[red]Error: No configuration provided[/red]")
        sys.exit(1)
    
    console.print("[yellow]Testing connection to TrueNAS server...[/yellow]")
    
    async def test_connection():
        try:
            auth_manager = AuthManager(config_data)
            client = TrueNASClient(config_data, auth_manager)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Connecting to TrueNAS...", total=None)
                
                # Test connection
                success = await client.test_connection()
                
                if success:
                    progress.update(task, description="Connection successful!")
                    console.print("[green]✓ Connection successful![/green]")
                    
                    # Get system info
                    try:
                        system_info = await client.get_system_info()
                        version_info = await client.get_version()
                        
                        # Display system information
                        table = Table(title="TrueNAS System Information")
                        table.add_column("Property", style="cyan")
                        table.add_column("Value", style="white")
                        
                        table.add_row("Hostname", system_info.get('hostname', 'N/A'))
                        table.add_row("Version", version_info.get('version', 'N/A'))
                        table.add_row("Platform", system_info.get('platform', 'N/A'))
                        table.add_row("Uptime", str(system_info.get('uptime', 'N/A')))
                        
                        console.print(table)
                        
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not retrieve system info: {e}[/yellow]")
                else:
                    progress.update(task, description="Connection failed!")
                    console.print("[red]✗ Connection failed![/red]")
                    sys.exit(1)
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(test_connection())


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--host', help='TrueNAS host address')
@click.option('--port', type=int, help='TrueNAS port')
@click.option('--api-key', help='API key for authentication')
@click.option('--username', help='Username for authentication')
@click.option('--password', help='Password for authentication')
def list_tools(config, host, port, api_key, username, password):
    """List available MCP tools."""
    # Load configuration
    config_data = _load_config(config, host, port, api_key, username, password)
    
    if not config_data:
        console.print("[red]Error: No configuration provided[/red]")
        sys.exit(1)
    
    console.print("[yellow]Available MCP Tools:[/yellow]")
    
    # Create MCP server to get tools
    server = TrueNASMCPServer(config_data)
    
    # Get all tools
    all_tools = []
    all_tools.extend(server.system_resource.get_tools())
    all_tools.extend(server.storage_resource.get_tools())
    all_tools.extend(server.network_resource.get_tools())
    all_tools.extend(server.services_resource.get_tools())
    all_tools.extend(server.users_resource.get_tools())
    
    # Group tools by category
    categories = {
        'System': [t for t in all_tools if t.name.startswith('truenas_system_')],
        'Storage': [t for t in all_tools if t.name.startswith('truenas_storage_')],
        'Network': [t for t in all_tools if t.name.startswith('truenas_network_')],
        'Services': [t for t in all_tools if t.name.startswith('truenas_services_')],
        'Users': [t for t in all_tools if t.name.startswith('truenas_users_')],
    }
    
    for category, tools in categories.items():
        if tools:
            console.print(f"\n[bold cyan]{category} Tools:[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Tool Name", style="green")
            table.add_column("Description", style="white")
            
            for tool in tools:
                table.add_row(tool.name, tool.description)
            
            console.print(table)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--host', help='TrueNAS host address')
@click.option('--port', type=int, help='TrueNAS port')
@click.option('--api-key', help='API key for authentication')
@click.option('--username', help='Username for authentication')
@click.option('--password', help='Password for authentication')
def serve(config, host, port, api_key, username, password):
    """Start the MCP server."""
    # Load configuration
    config_data = _load_config(config, host, port, api_key, username, password)
    
    if not config_data:
        console.print("[red]Error: No configuration provided[/red]")
        sys.exit(1)
    
    console.print("[green]Starting TrueNAS MCP Server...[/green]")
    
    async def run_server():
        try:
            server = TrueNASMCPServer(config_data)
            await server.run()
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Server error: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_server())


def _load_config(config_file: str = None, host: str = None, port: int = None, 
                api_key: str = None, username: str = None, password: str = None) -> Dict[str, Any]:
    """Load configuration from file or command line arguments."""
    config = {}
    
    # Load from file if specified
    if config_file:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading config file: {e}[/red]")
            return None
    
    # Override with command line arguments
    if host:
        config['host'] = host
    if port:
        config['port'] = port
    if api_key:
        config['api_key'] = api_key
    if username:
        config['username'] = username
    if password:
        config['password'] = password
    
    # Check for required fields
    if not config.get('host'):
        console.print("[red]Error: Host is required[/red]")
        return None
    
    if not config.get('api_key') and not (config.get('username') and config.get('password')):
        console.print("[red]Error: Either API key or username/password is required[/red]")
        return None
    
    return config


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
