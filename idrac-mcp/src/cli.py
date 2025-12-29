"""Command-line interface for iDRAC MCP Server."""

import os
import sys
import asyncio
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .utils.mcp_logging import setup_logging, get_logger

logger = get_logger(__name__)
console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
def cli(debug):
    """iDRAC MCP Server CLI."""
    if debug:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")


@cli.command()
def init():
    """Initialize configuration interactively."""
    console.print(Panel.fit("iDRAC MCP Server Configuration", style="bold blue"))
    
    config = {}
    
    # iDRAC settings
    config["IDRAC_HOST"] = Prompt.ask("iDRAC Host", default="192.168.1.100")  # Change this to your iDRAC IP
    config["IDRAC_PORT"] = Prompt.ask("iDRAC Port", default="443")
    config["IDRAC_PROTOCOL"] = Prompt.ask("iDRAC Protocol", choices=["http", "https"], default="https")
    config["IDRAC_USERNAME"] = Prompt.ask("iDRAC Username", default="root")
    config["IDRAC_PASSWORD"] = Prompt.ask("iDRAC Password", password=True)
    
    # SSL settings
    ssl_verify = Confirm.ask("Verify SSL certificates?", default=False)
    config["IDRAC_SSL_VERIFY"] = str(ssl_verify).lower()
    
    # Server settings
    config["SERVER_PORT"] = Prompt.ask("Server Port", default="8000")
    config["SECRET_KEY"] = Prompt.ask("Secret Key", default="your-secret-key-here-change-this")
    
    # Authentication
    config["MCP_USERNAME"] = Prompt.ask("MCP Username", default="admin")
    config["MCP_PASSWORD"] = Prompt.ask("MCP Password", default="admin-change-this")
    config["ADMIN_TOKEN"] = Prompt.ask("Admin Token", default="admin-token-change-this")
    
    # Logging
    config["LOG_LEVEL"] = Prompt.ask("Log Level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    config["LOG_FORMAT"] = Prompt.ask("Log Format", choices=["console", "json"], default="console")
    
    # Write to .env file
    env_content = "\n".join([f"{k}={v}" for k, v in config.items()])
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    console.print(f"[green]Configuration saved to .env file[/green]")


@cli.command()
def serve():
    """Start the HTTP server."""
    console.print(Panel.fit("Starting iDRAC MCP HTTP Server", style="bold green"))
    
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
    console.print(Panel.fit("iDRAC MCP Server Health Check", style="bold blue"))
    
    try:
        import httpx
        with httpx.Client() as client:
            response = client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Server is healthy[/green]")
                console.print(f"Status: {data.get('status')}")
                console.print(f"iDRAC Connection: {data.get('idrac_connection')}")
            else:
                console.print(f"[red]✗ Server health check failed[/red]")
                console.print(f"Status code: {response.status_code}")
    except Exception as e:
        console.print(f"[red]✗ Health check failed: {e}[/red]")


@cli.command()
def login():
    """Login to get JWT token."""
    console.print(Panel.fit("iDRAC MCP Server Login", style="bold blue"))
    
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    
    try:
        import httpx
        with httpx.Client() as client:
            response = client.post(
                "http://localhost:8000/auth/login",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Login successful[/green]")
                console.print(f"Token: {data.get('access_token')}")
            else:
                console.print(f"[red]✗ Login failed[/red]")
                console.print(f"Error: {response.text}")
    except Exception as e:
        console.print(f"[red]✗ Login failed: {e}[/red]")


@cli.command()
@click.option("--admin-token", required=True, help="Admin token for authentication")
def create_token(admin_token):
    """Create JWT token using admin token."""
    console.print(Panel.fit("Create JWT Token", style="bold blue"))
    
    try:
        import httpx
        with httpx.Client() as client:
            response = client.post(
                "http://localhost:8000/auth/token",
                json={"admin_token": admin_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Token created successfully[/green]")
                console.print(f"Token: {data.get('access_token')}")
            else:
                console.print(f"[red]✗ Token creation failed[/red]")
                console.print(f"Error: {response.text}")
    except Exception as e:
        console.print(f"[red]✗ Token creation failed: {e}[/red]")


@cli.command()
def list_tools():
    """List available tools."""
    console.print(Panel.fit("Available iDRAC MCP Tools", style="bold blue"))
    
    try:
        import httpx
        with httpx.Client() as client:
            response = client.get("http://localhost:8000/mcp/list_tools")
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                
                table = Table(title="Available Tools")
                table.add_column("Tool Name", style="cyan")
                table.add_column("Description", style="white")
                
                for tool in tools:
                    table.add_row(tool["name"], tool["description"])
                
                console.print(table)
            else:
                console.print(f"[red]✗ Failed to list tools[/red]")
                console.print(f"Error: {response.text}")
    except Exception as e:
        console.print(f"[red]✗ Failed to list tools: {e}[/red]")


@cli.command()
@click.option("--tool", required=True, help="Tool name to call")
@click.option("--arguments", help="Tool arguments (JSON format)")
def call_tool(tool, arguments):
    """Call a specific tool."""
    console.print(Panel.fit(f"Call Tool: {tool}", style="bold blue"))
    
    try:
        import json
        import httpx
        
        # Parse arguments
        tool_args = {}
        if arguments:
            tool_args = json.loads(arguments)
        
        # Get token first
        admin_token = os.getenv("ADMIN_TOKEN", "admin-token-change-this")
        
        with httpx.Client() as client:
            # Get token
            token_response = client.post(
                "http://localhost:8000/auth/token",
                json={"admin_token": admin_token}
            )
            
            if token_response.status_code != 200:
                console.print(f"[red]✗ Failed to get token[/red]")
                return
            
            token = token_response.json()["access_token"]
            
            # Call tool
            response = client.post(
                "http://localhost:8000/mcp/call_tool",
                json={"name": tool, "arguments": tool_args},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Tool call successful[/green]")
                console.print(f"Result: {data}")
            else:
                console.print(f"[red]✗ Tool call failed[/red]")
                console.print(f"Error: {response.text}")
    except Exception as e:
        console.print(f"[red]✗ Tool call failed: {e}[/red]")


@cli.command()
def generate_config():
    """Generate configuration examples."""
    console.print(Panel.fit("Configuration Examples", style="bold blue"))
    
    cursor_config = {
        "mcpServers": {
            "idrac": {
                "url": "http://localhost:8000/mcp/",
                "headers": {
                    "Authorization": "Bearer your-jwt-token-here"
                }
            }
        }
    }
    
    claude_config = {
        "mcpServers": {
            "idrac": {
                "command": "/path/to/idrac-mcp/.venv/bin/python",
                "args": [
                    "/path/to/idrac-mcp/src/server.py"
                ],
                "env": {
                    "IDRAC_HOST": "your-idrac-host",
                    "IDRAC_USERNAME": "your-username",
                    "IDRAC_PASSWORD": "your-password",
                    "SECRET_KEY": "your-secret-key"
                }
            }
        }
    }
    
    console.print("\n[bold]Cursor Configuration (~/.cursor/mcp.json):[/bold]")
    console.print_json(data=cursor_config)
    
    console.print("\n[bold]Claude Configuration (~/.config/claude/mcp.json):[/bold]")
    console.print_json(data=claude_config)


if __name__ == "__main__":
    cli()
