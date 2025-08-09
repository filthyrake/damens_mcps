"""Command-line interface for Proxmox MCP Server."""

import asyncio
import json
import os
import secrets
import sys
from typing import Any, Dict, Optional

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        "host": os.getenv("PROXMOX_HOST"),
        "port": int(os.getenv("PROXMOX_PORT", "8006")),
        "protocol": os.getenv("PROXMOX_PROTOCOL", "https"),
        "username": os.getenv("PROXMOX_USERNAME"),
        "password": os.getenv("PROXMOX_PASSWORD"),
        "api_token": os.getenv("PROXMOX_API_TOKEN"),
        "realm": os.getenv("PROXMOX_REALM", "pve"),
        "verify_ssl": os.getenv("PROXMOX_SSL_VERIFY", "true").lower() == "true",
        "secret_key": os.getenv("SECRET_KEY"),
        "server_port": int(os.getenv("SERVER_PORT", "8000")),
        "server_host": os.getenv("SERVER_HOST", "localhost"),
    }
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration."""
    errors = []
    
    if not config["host"]:
        errors.append("PROXMOX_HOST is required")
    
    if not config["api_token"] and (not config["username"] or not config["password"]):
        errors.append("Either PROXMOX_API_TOKEN or PROXMOX_USERNAME/PROXMOX_PASSWORD is required")
    
    if not config["secret_key"]:
        errors.append("SECRET_KEY is required")
    
    if errors:
        console.print(f"[red]Configuration errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        return False
    
    return True


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
def cli(debug: bool):
    """Proxmox MCP Server CLI."""
    if debug:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")


@cli.command()
def init():
    """Initialize configuration."""
    console.print(Panel.fit("Proxmox MCP Server Configuration", style="blue"))
    
    # Check if .env exists
    if os.path.exists(".env"):
        console.print("[yellow]Warning: .env file already exists. This will overwrite it.[/yellow]")
        if not click.confirm("Continue?"):
            return
    
    # Get configuration from user
    config = {}
    
    console.print("\n[bold]Proxmox Connection Settings:[/bold]")
    config["PROXMOX_HOST"] = click.prompt("Proxmox host", default="192.168.1.100")
    config["PROXMOX_PORT"] = click.prompt("Proxmox port", default="8006", type=int)
    config["PROXMOX_PROTOCOL"] = click.prompt("Protocol", default="https", type=click.Choice(["http", "https"]))
    
    auth_method = click.prompt(
        "Authentication method",
        default="password",
        type=click.Choice(["password", "api_token"])
    )
    
    if auth_method == "password":
        config["PROXMOX_USERNAME"] = click.prompt("Username")
        config["PROXMOX_PASSWORD"] = click.prompt("Password", hide_input=True)
        config["PROXMOX_REALM"] = click.prompt("Realm", default="pve")
    else:
        config["PROXMOX_USERNAME"] = click.prompt("Token name (username)")
        config["PROXMOX_API_TOKEN"] = click.prompt("API token", hide_input=True)
    
    config["PROXMOX_SSL_VERIFY"] = click.prompt("Verify SSL", default="true", type=click.Choice(["true", "false"]))
    
    console.print("\n[bold]MCP Server Settings:[/bold]")
    config["SERVER_PORT"] = click.prompt("MCP server port", default="8000", type=int)
    config["SECRET_KEY"] = click.prompt("Secret key", default=secrets.token_urlsafe(32))
    
    # MCP authentication
    config["MCP_USERNAME"] = click.prompt("MCP username", default="admin")
    config["MCP_PASSWORD"] = click.prompt("MCP password", default="admin", hide_input=True)
    config["ADMIN_TOKEN"] = click.prompt("Admin token", default=secrets.token_urlsafe(16))
    
    console.print("\n[bold]Logging Settings:[/bold]")
    config["LOG_LEVEL"] = click.prompt("Log level", default="INFO", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]))
    config["LOG_FORMAT"] = click.prompt("Log format", default="json", type=click.Choice(["json", "console"]))
    
    # Write .env file
    env_content = ""
    for key, value in config.items():
        env_content += f"{key}={value}\n"
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    console.print(f"\n[green]Configuration saved to .env file[/green]")
    console.print(f"[blue]Next steps:[/blue]")
    console.print(f"  1. Review the .env file")
    console.print(f"  2. Run 'proxmox-mcp serve' to start the server")
    console.print(f"  3. Run 'proxmox-mcp health' to test the connection")


@cli.command()
def serve():
    """Start the MCP server."""
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    console.print(Panel.fit("Starting Proxmox MCP Server", style="green"))
    
    try:
        from .http_server import run_server
        run_server()
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to start server: {e}[/red]")
        sys.exit(1)


@cli.command()
def health():
    """Check server health."""
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    console.print(Panel.fit("Proxmox MCP Server Health Check", style="blue"))
    
    # Test HTTP server
    server_url = f"http://{config['server_host']}:{config['server_port']}"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Testing server connection...", total=None)
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{server_url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    progress.update(task, description="Server is healthy")
                    
                    console.print(f"\n[green]✓ Server Status: {data['status']}[/green]")
                    
                    if "proxmox_connection" in data:
                        proxmox_status = data["proxmox_connection"]["status"]
                        if proxmox_status == "success":
                            console.print(f"[green]✓ Proxmox Connection: {proxmox_status}[/green]")
                        else:
                            console.print(f"[red]✗ Proxmox Connection: {proxmox_status}[/red]")
                            console.print(f"  Error: {data['proxmox_connection'].get('error', 'Unknown error')}")
                else:
                    progress.update(task, description="Server is unhealthy")
                    console.print(f"\n[red]✗ Server returned status code: {response.status_code}[/red]")
                    
        except httpx.ConnectError:
            progress.update(task, description="Cannot connect to server")
            console.print(f"\n[red]✗ Cannot connect to server at {server_url}[/red]")
            console.print("Make sure the server is running with 'proxmox-mcp serve'")
        except Exception as e:
            progress.update(task, description="Health check failed")
            console.print(f"\n[red]✗ Health check failed: {e}[/red]")


@cli.command()
@click.option("--username", default="admin", help="MCP username")
@click.option("--password", default="admin", help="MCP password")
def login(username: str, password: str):
    """Login to get JWT token."""
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    console.print(Panel.fit("Proxmox MCP Server Login", style="blue"))
    
    server_url = f"http://{config['server_host']}:{config['server_port']}"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{server_url}/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                
                console.print(f"[green]✓ Login successful[/green]")
                console.print(f"[blue]Token:[/blue] {token}")
                console.print(f"\n[blue]Use this token in your MCP client configuration:[/blue]")
                console.print(f"Authorization: Bearer {token}")
                
            else:
                console.print(f"[red]✗ Login failed: {response.status_code}[/red]")
                if response.text:
                    console.print(f"Error: {response.text}")
                    
    except httpx.ConnectError:
        console.print(f"[red]✗ Cannot connect to server at {server_url}[/red]")
        console.print("Make sure the server is running with 'proxmox-mcp serve'")
    except Exception as e:
        console.print(f"[red]✗ Login failed: {e}[/red]")


@cli.command()
@click.option("--admin-token", help="Admin token")
def create_token(admin_token: str):
    """Create a token using admin token."""
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    if not admin_token:
        admin_token = config.get("ADMIN_TOKEN") or click.prompt("Admin token", hide_input=True)
    
    console.print(Panel.fit("Create JWT Token", style="blue"))
    
    server_url = f"http://{config['server_host']}:{config['server_port']}"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{server_url}/auth/token",
                json={"admin_token": admin_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                
                console.print(f"[green]✓ Token created successfully[/green]")
                console.print(f"[blue]Token:[/blue] {token}")
                console.print(f"\n[blue]Use this token in your MCP client configuration:[/blue]")
                console.print(f"Authorization: Bearer {token}")
                
            else:
                console.print(f"[red]✗ Token creation failed: {response.status_code}[/red]")
                if response.text:
                    console.print(f"Error: {response.text}")
                    
    except httpx.ConnectError:
        console.print(f"[red]✗ Cannot connect to server at {server_url}[/red]")
        console.print("Make sure the server is running with 'proxmox-mcp serve'")
    except Exception as e:
        console.print(f"[red]✗ Token creation failed: {e}[/red]")


@cli.command()
def list_tools():
    """List available tools."""
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    console.print(Panel.fit("Available Proxmox MCP Tools", style="blue"))
    
    server_url = f"http://{config['server_host']}:{config['server_port']}"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{server_url}/tools")
            
            if response.status_code == 200:
                data = response.json()
                tools = data["tools"]
                
                # Create table
                table = Table(title="Available Tools")
                table.add_column("Tool Name", style="cyan", no_wrap=True)
                table.add_column("Description", style="white")
                table.add_column("Parameters", style="yellow")
                
                for tool in tools:
                    name = tool["name"]
                    description = tool["description"]
                    
                    # Format parameters
                    params = []
                    if "inputSchema" in tool and "properties" in tool["inputSchema"]:
                        for param_name, param_info in tool["inputSchema"]["properties"].items():
                            param_type = param_info.get("type", "any")
                            required = param_name in tool["inputSchema"].get("required", [])
                            param_str = f"{param_name}: {param_type}"
                            if required:
                                param_str += " (required)"
                            params.append(param_str)
                    
                    params_str = "\n".join(params) if params else "None"
                    
                    table.add_row(name, description, params_str)
                
                console.print(table)
                
            else:
                console.print(f"[red]✗ Failed to get tools: {response.status_code}[/red]")
                if response.text:
                    console.print(f"Error: {response.text}")
                    
    except httpx.ConnectError:
        console.print(f"[red]✗ Cannot connect to server at {server_url}[/red]")
        console.print("Make sure the server is running with 'proxmox-mcp serve'")
    except Exception as e:
        console.print(f"[red]✗ Failed to list tools: {e}[/red]")


@cli.command()
@click.argument("tool_name")
@click.option("--arguments", "-a", help="Tool arguments as JSON")
def call_tool(tool_name: str, arguments: str):
    """Call a specific tool."""
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    # Parse arguments
    tool_args = {}
    if arguments:
        try:
            tool_args = json.loads(arguments)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON in arguments[/red]")
            sys.exit(1)
    
    console.print(Panel.fit(f"Calling Tool: {tool_name}", style="blue"))
    
    server_url = f"http://{config['server_host']}:{config['server_port']}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{server_url}/tools/{tool_name}",
                json={"arguments": tool_args}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("error"):
                    console.print(f"[red]Tool execution failed: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Tool executed successfully[/green]")
                    console.print(f"[blue]Result:[/blue]")
                    console.print(data["content"])
                    
            else:
                console.print(f"[red]✗ Tool execution failed: {response.status_code}[/red]")
                if response.text:
                    console.print(f"Error: {response.text}")
                    
    except httpx.ConnectError:
        console.print(f"[red]✗ Cannot connect to server at {server_url}[/red]")
        console.print("Make sure the server is running with 'proxmox-mcp serve'")
    except Exception as e:
        console.print(f"[red]✗ Tool execution failed: {e}[/red]")


@cli.command()
def generate_config():
    """Generate configuration examples."""
    console.print(Panel.fit("Configuration Examples", style="blue"))
    
    # Cursor configuration
    cursor_config = {
        "mcpServers": {
            "proxmox": {
                "url": "http://localhost:8000/mcp/",
                "headers": {
                    "Authorization": "Bearer your-jwt-token-here"
                }
            }
        }
    }
    
    console.print("[bold]Cursor Configuration (~/.cursor/mcp.json):[/bold]")
    console.print(json.dumps(cursor_config, indent=2))
    
    # Claude configuration
    claude_config = {
        "mcpServers": {
            "proxmox": {
                "command": "/path/to/proxmox-mcp/.venv/bin/python",
                "args": ["/path/to/proxmox-mcp/src/server.py"],
                "env": {
                    "PROXMOX_HOST": "your-proxmox-host",
                    "PROXMOX_USERNAME": "your-username",
                    "PROXMOX_PASSWORD": "your-password",
                    "SECRET_KEY": "your-secret-key"
                }
            }
        }
    }
    
    console.print("\n[bold]Claude Configuration (~/.config/claude/mcp.json):[/bold]")
    console.print(json.dumps(claude_config, indent=2))


if __name__ == "__main__":
    cli()
