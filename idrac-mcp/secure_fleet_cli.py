#!/usr/bin/env python3
"""Secure CLI tool for managing iDRAC fleet with encrypted passwords."""

import asyncio
import click
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from secure_multi_server_manager import SecureMultiServerManager

@click.group()
@click.option('--config', '-c', default='fleet_servers.json', help='Fleet configuration file')
@click.option('--key-file', '-k', default='.fleet_key', help='Encryption key file (legacy)')
@click.option('--password', '-p', envvar='IDRAC_FLEET_PASSWORD', help='Master password (or set IDRAC_FLEET_PASSWORD env var)')
@click.pass_context
def cli(ctx, config, key_file, password):
    """Secure iDRAC Fleet Management CLI with encrypted passwords."""
    ctx.ensure_object(dict)
    
    # Prompt for password if not provided and not using legacy key file
    if password is None and not Path(key_file).exists():
        password = click.prompt("Enter fleet master password", hide_input=True)
    
    try:
        ctx.obj['manager'] = SecureMultiServerManager(config, key_file, password)
    except Exception as e:
        click.echo(f"❌ Failed to initialize secure manager: {e}")
        sys.exit(1)

@cli.command()
@click.pass_context
def list(ctx):
    """List all configured servers."""
    manager = ctx.obj['manager']
    servers = manager.list_servers()
    
    if not servers:
        click.echo("No servers configured.")
        return
    
    click.echo(f"Configured servers ({len(servers)}):")
    for server in servers:
        config = manager.servers[server]  # Use raw config to avoid decrypting
        enabled = "✅" if config.get("enabled", True) else "❌"
        click.echo(f"  {enabled} {server}: {config['protocol']}://{config['host']}:{config['port']}")

@cli.command()
@click.argument('name')
@click.argument('host')
@click.argument('username')
@click.option('--port', default=443, help='iDRAC port')
@click.option('--protocol', default='https', help='Protocol (http/https)')
@click.option('--ssl-verify/--no-ssl-verify', default=False, help='Verify SSL certificates')
@click.pass_context
def add(ctx, name, host, username, port, protocol, ssl_verify):
    """Add a server to the fleet (password will be prompted securely)."""
    manager = ctx.obj['manager']
    
    # Securely prompt for password
    password = click.prompt("Enter iDRAC password", hide_input=True, confirmation_prompt=True)
    
    manager.add_server(name, host, username, password, port, protocol, ssl_verify)
    click.echo(f"✅ Added server '{name}' with encrypted password")

@cli.command()
@click.argument('name')
@click.pass_context
def remove(ctx, name):
    """Remove a server from the fleet."""
    manager = ctx.obj['manager']
    manager.remove_server(name)

@cli.command()
@click.argument('name')
@click.pass_context
def enable(ctx, name):
    """Enable a server."""
    manager = ctx.obj['manager']
    manager.enable_server(name)

@cli.command()
@click.argument('name')
@click.pass_context
def disable(ctx, name):
    """Disable a server."""
    manager = ctx.obj['manager']
    manager.disable_server(name)

@cli.command()
@click.pass_context
def test(ctx):
    """Test connection to all enabled servers."""
    manager = ctx.obj['manager']
    
    async def run_test():
        results = await manager.test_all_servers()
        
        for server_name, result in results.items():
            if result["status"] == "success":
                click.echo(f"✅ {server_name}: {result['message']}")
            else:
                click.echo(f"❌ {server_name}: {result['message']}")
    
    asyncio.run(run_test())

@cli.command()
@click.argument('name', required=False)
@click.pass_context
def info(ctx, name):
    """Get system information from servers."""
    manager = ctx.obj['manager']
    
    async def run_info():
        if name:
            # Single server
            config = manager.get_server_config(name)
            if not config:
                click.echo(f"❌ Server '{name}' not found")
                return
            
            try:
                from idrac_client import IDracClient
                async with IDracClient(config) as client:
                    system_info = await client.get_system_info()
                    data = system_info["data"]
                    
                    click.echo(f"📊 {name} System Information:")
                    click.echo(f"  Model: {data.get('model', 'N/A')}")
                    click.echo(f"  Manufacturer: {data.get('manufacturer', 'N/A')}")
                    click.echo(f"  Serial Number: {data.get('serial_number', 'N/A')}")
                    click.echo(f"  Power State: {data.get('power_state', 'N/A')}")
                    click.echo(f"  Health: {data.get('health', 'N/A')}")
                    click.echo(f"  BIOS Version: {data.get('bios_version', 'N/A')}")
            except Exception as e:
                click.echo(f"❌ Failed to get info for {name}: {e}")
        else:
            # All servers
            fleet_info = await manager.get_fleet_system_info()
            
            for server_name, result in fleet_info.items():
                if result["status"] == "success":
                    data = result["data"]
                    click.echo(f"📊 {server_name}:")
                    click.echo(f"  Model: {data.get('model', 'N/A')}")
                    click.echo(f"  Serial: {data.get('serial_number', 'N/A')}")
                    click.echo(f"  Power: {data.get('power_state', 'N/A')}")
                    click.echo(f"  Health: {data.get('health', 'N/A')}")
                else:
                    click.echo(f"❌ {server_name}: {result['message']}")
    
    asyncio.run(run_info())

@cli.command()
@click.pass_context
def health(ctx):
    """Get health status from all enabled servers."""
    manager = ctx.obj['manager']
    
    async def run_health():
        fleet_health = await manager.get_fleet_health()
        
        for server_name, result in fleet_health.items():
            if result["status"] == "success":
                data = result["data"]
                health_status = data.get('overall_health', 'N/A')
                status_icon = "✅" if health_status == "OK" else "⚠️" if health_status == "Warning" else "❌"
                click.echo(f"{status_icon} {server_name}: {health_status}")
            else:
                click.echo(f"❌ {server_name}: {result['message']}")
    
    asyncio.run(run_health())

@cli.command()
@click.pass_context
def power(ctx):
    """Get power status from all enabled servers."""
    manager = ctx.obj['manager']
    
    async def run_power():
        fleet_power = await manager.get_fleet_power_status()
        
        for server_name, result in fleet_power.items():
            if result["status"] == "success":
                data = result["data"]
                power_state = data.get('power_state', 'N/A')
                power_icon = "🟢" if power_state == "On" else "🔴" if power_state == "Off" else "🟡"
                click.echo(f"{power_icon} {server_name}: {power_state}")
            else:
                click.echo(f"❌ {server_name}: {result['message']}")
    
    asyncio.run(run_power())

@cli.command()
@click.argument('name')
@click.pass_context
def thermal(ctx, name):
    """Get thermal status from a specific server."""
    manager = ctx.obj['manager']
    config = manager.get_server_config(name)
    
    if not config:
        click.echo(f"❌ Server '{name}' not found")
        return
    
    async def run_thermal():
        try:
            from idrac_client import IDracClient
            async with IDracClient(config) as client:
                thermal = await client.get_thermal_status()
                data = thermal["data"]
                
                click.echo(f"🌡️ {name} Thermal Status:")
                
                # Temperatures
                temps = data.get('temperatures', {}).get('sensors', [])
                click.echo(f"  Temperature Sensors ({len(temps)}):")
                for temp in temps:
                    temp_icon = "🟢" if temp.get('health') == "OK" else "⚠️" if temp.get('health') == "Warning" else "❌"
                    click.echo(f"    {temp_icon} {temp.get('name', 'Unknown')}: {temp.get('reading_celsius', 'N/A')}°C")
                
                # Fans
                fans = data.get('fans', {}).get('fans', [])
                click.echo(f"  Fans ({len(fans)}):")
                for fan in fans:
                    fan_icon = "🟢" if fan.get('health') == "OK" else "⚠️" if fan.get('health') == "Warning" else "❌"
                    click.echo(f"    {fan_icon} {fan.get('name', 'Unknown')}: {fan.get('reading_rpm', 'N/A')} RPM")
        except Exception as e:
            click.echo(f"❌ Failed to get thermal status for {name}: {e}")
    
    asyncio.run(run_thermal())

@cli.command()
@click.pass_context
def init(ctx):
    """Initialize secure fleet configuration with sample data."""
    manager = ctx.obj['manager']
    manager.create_sample_config()
    click.echo("✅ Secure fleet configuration initialized")

@cli.command()
@click.pass_context
def security_info(ctx):
    """Show security information about the fleet configuration."""
    manager = ctx.obj['manager']
    
    click.echo("🔐 Fleet Security Information:")
    click.echo(f"  Configuration file: {manager.config_file}")
    click.echo(f"  Encryption method: Password-based key derivation (PBKDF2-SHA256)")
    click.echo(f"  Key derivation iterations: 480,000 (OWASP 2023 recommendation)")
    click.echo(f"  Passwords encrypted: ✅")
    click.echo(f"  Servers configured: {len(manager.servers)}")
    
    if manager.key_file.exists():
        click.echo(f"  Legacy key file: ⚠️  Present (.fleet_key)")
        click.echo("  ⚠️  SECURITY WARNING: Legacy key file stores encryption key unencrypted on disk!")
        click.echo("  💡 Consider migrating to password-based encryption by removing .fleet_key")
    else:
        click.echo(f"  Encryption key storage: ✅ No key stored on disk")
        click.echo("  🔒 Master password required for each session")
        click.echo("  💡 Password can be set via --password flag or IDRAC_FLEET_PASSWORD env var")

if __name__ == '__main__':
    cli()
