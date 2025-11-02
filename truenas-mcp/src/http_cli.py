"""CLI for HTTP-based TrueNAS MCP Server."""

import asyncio
import json
import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Optional

import click
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import (
    Settings,
    create_default_env_file,
    generate_secret_key,
    load_settings,
    validate_configuration,
)
from .http_server import create_app
from .utils.logging import setup_logging

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
def cli(debug: bool, config: Optional[str]):
    """TrueNAS MCP HTTP Server CLI."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if config:
        # Load from specific config file
        pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the HTTP MCP server."""
    try:
        # Load settings
        settings = load_settings()

        # Override with CLI options
        settings.server_host = host
        settings.server_port = port
        settings.reload = reload

        # Validate configuration
        validate_configuration(settings)

        # Setup logging
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file=settings.log_file,
        )

        console.print(
            Panel.fit(
                f"[bold green]TrueNAS MCP HTTP Server[/bold green]\n"
                f"Host: {host}\n"
                f"Port: {port}\n"
                f"TrueNAS: {settings.truenas_host}:{settings.truenas_port}\n"
                f"Debug: {settings.debug}\n"
                f"Auto-reload: {reload}",
                title="Server Configuration",
            )
        )

        # Create and run app
        app = create_app()

        import uvicorn

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level=settings.log_level.lower(),
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
def init():
    """Initialize the server configuration."""
    try:
        # Create default .env file
        create_default_env_file()

        # Generate secret key
        secret_key = generate_secret_key()

        console.print(
            Panel.fit(
                f"[bold green]Configuration Initialized[/bold green]\n\n"
                f"[bold]Secret Key:[/bold] {secret_key}\n\n"
                f"Please update the .env file with your TrueNAS server details:\n"
                f"1. Set TRUENAS_HOST to your TrueNAS server address\n"
                f"2. Set TRUENAS_API_KEY to your API key\n"
                f"3. Update SECRET_KEY with the generated key above\n"
                f"4. Optionally set ADMIN_TOKEN for admin access",
                title="Next Steps",
            )
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--url", default="http://localhost:8000", help="Server URL")
def health(url: str):
    """Check server health."""
    try:
        response = requests.get(f"{url}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            console.print(
                Panel.fit(
                    f"[bold green]Server Healthy[/bold green]\n"
                    f"Status: {data.get('status')}\n"
                    f"TrueNAS Connection: {data.get('truenas_connection')}\n"
                    f"Timestamp: {data.get('timestamp')}",
                    title="Health Check",
                )
            )
        else:
            console.print(
                f"[bold red]Server Unhealthy[/bold red] - Status: {response.status_code}"
            )
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Connection Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--url", default="http://localhost:8000", help="Server URL")
@click.option("--username", prompt=True, help="Username")
@click.option("--password", prompt=True, hide_input=True, help="Password")
def login(url: str, username: str, password: str):
    """Login to get an access token."""
    try:
        response = requests.post(
            f"{url}/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            console.print(
                Panel.fit(
                    f"[bold green]Login Successful[/bold green]\n"
                    f"Username: {data.get('user', {}).get('username')}\n"
                    f"Token Type: {data.get('token_type')}\n"
                    f"Access Token: {data.get('access_token')[:50]}...",
                    title="Authentication",
                )
            )

            # Save token to file with secure permissions
            token_file = Path.home() / ".truenas-mcp" / "token.txt"
            token_file.parent.mkdir(exist_ok=True, mode=0o700)

            # Use os.open with proper permissions to avoid race condition
            # File is created with 0o600 permissions atomically
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write(data.get("access_token"))
            except (OSError, IOError):
                os.close(fd)
                raise

            console.print(f"[green]Token saved to: {token_file}[/green]")

        else:
            console.print(
                f"[bold red]Login Failed[/bold red] - Status: {response.status_code}"
            )
            if response.text:
                console.print(f"Error: {response.text}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Connection Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--url", default="http://localhost:8000", help="Server URL")
@click.option("--admin-token", required=True, help="Admin token")
@click.option("--username", default="admin", help="Username for token")
def create_token(url: str, admin_token: str, username: str):
    """Create an access token using admin token."""
    try:
        response = requests.post(
            f"{url}/auth/token",
            json={"admin_token": admin_token, "username": username},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            console.print(
                Panel.fit(
                    f"[bold green]Token Created[/bold green]\n"
                    f"Username: {username}\n"
                    f"Token Type: {data.get('token_type')}\n"
                    f"Access Token: {data.get('access_token')[:50]}...",
                    title="Token Creation",
                )
            )

            # Save token to file with secure permissions
            token_file = Path.home() / ".truenas-mcp" / "token.txt"
            token_file.parent.mkdir(exist_ok=True, mode=0o700)

            # Use os.open with proper permissions to avoid race condition
            # File is created with 0o600 permissions atomically
            fd = os.open(str(token_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    f.write(data.get("access_token"))
            except (OSError, IOError):
                os.close(fd)
                raise

            console.print(f"[green]Token saved to: {token_file}[/green]")

        else:
            console.print(
                f"[bold red]Token Creation Failed[/bold red] - Status: {response.status_code}"
            )
            if response.text:
                console.print(f"Error: {response.text}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Connection Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--url", default="http://localhost:8000", help="Server URL")
@click.option(
    "--token-file", default="~/.truenas-mcp/token.txt", help="Token file path"
)
def list_tools(url: str, token_file: str):
    """List available MCP tools."""
    try:
        # Load token
        token_path = Path(token_file).expanduser()
        if not token_path.exists():
            console.print(f"[bold red]Token file not found: {token_path}[/bold red]")
            console.print("Please login first using: truenas-mcp login")
            sys.exit(1)

        token = token_path.read_text().strip()

        # Make request
        response = requests.post(
            f"{url}/mcp/tools/list",
            headers={"Authorization": f"Bearer {token}"},
            json={},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", [])

            # Create table
            table = Table(title="Available MCP Tools")
            table.add_column("Tool Name", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Category", style="yellow")

            for tool in tools:
                name = tool.get("name", "")
                description = tool.get("description", "")
                category = name.split("_")[1] if "_" in name else "unknown"

                table.add_row(name, description, category)

            console.print(table)

        else:
            console.print(
                f"[bold red]Failed to list tools[/bold red] - Status: {response.status_code}"
            )
            if response.text:
                console.print(f"Error: {response.text}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Connection Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--url", default="http://localhost:8000", help="Server URL")
@click.option(
    "--token-file", default="~/.truenas-mcp/token.txt", help="Token file path"
)
@click.argument("tool_name")
@click.argument("arguments", nargs=-1)
def call_tool(url: str, token_file: str, tool_name: str, arguments: tuple):
    """Call an MCP tool."""
    try:
        # Load token
        token_path = Path(token_file).expanduser()
        if not token_path.exists():
            console.print(f"[bold red]Token file not found: {token_path}[/bold red]")
            console.print("Please login first using: truenas-mcp login")
            sys.exit(1)

        token = token_path.read_text().strip()

        # Parse arguments
        args = {}
        for arg in arguments:
            if "=" in arg:
                key, value = arg.split("=", 1)
                args[key] = value
            else:
                args[arg] = True

        # Make request
        response = requests.post(
            f"{url}/mcp/tools/call",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": tool_name, "arguments": args},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            console.print(
                Panel.fit(
                    f"[bold green]Tool Call Successful[/bold green]\n"
                    f"Tool: {tool_name}\n"
                    f"Result: {json.dumps(data, indent=2)}",
                    title="Tool Result",
                )
            )

        else:
            console.print(
                f"[bold red]Tool call failed[/bold red] - Status: {response.status_code}"
            )
            if response.text:
                console.print(f"Error: {response.text}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Connection Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
def generate_config():
    """Generate configuration examples."""
    try:
        # Generate secret key
        secret_key = generate_secret_key()

        # Create examples
        examples = {
            "docker_compose": {
                "description": "Docker Compose environment variables",
                "content": f"""# Docker Compose .env file
TRUENAS_HOST=your-truenas-host.example.com
TRUENAS_PORT=443
TRUENAS_API_KEY=your-api-key-here
TRUENAS_VERIFY_SSL=true
SECRET_KEY={secret_key}
ADMIN_TOKEN=your-admin-token-here
DEBUG=false
LOG_LEVEL=INFO""",
            },
            "kubernetes_secret": {
                "description": "Kubernetes Secret (base64 encoded)",
                "content": f"""# Create Kubernetes secret
kubectl create secret generic truenas-mcp-secrets \\
  --from-literal=truenas_api_key=your-api-key-here \\
  --from-literal=secret_key={secret_key} \\
  --from-literal=admin_token=your-admin-token-here""",
            },
            "cursor_config": {
                "description": "Cursor MCP configuration",
                "content": """{
  "mcpServers": {
    "truenas": {
      "url": "http://your-mcp-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer your-jwt-token"
      }
    }
  }
}""",
            },
        }

        for name, example in examples.items():
            console.print(
                Panel.fit(
                    f"[bold]{example['description']}[/bold]\n\n"
                    f"[code]{example['content']}[/code]",
                    title=name.replace("_", " ").title(),
                )
            )
            console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
