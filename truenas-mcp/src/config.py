"""Configuration management for TrueNAS MCP Server."""

import os
import secrets
import string
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


def validate_secret_key_strength(key: str) -> bool:
    """Validate secret key has sufficient entropy.

    Args:
        key: The secret key to validate

    Returns:
        True if the key has sufficient entropy, False otherwise

    Requirements:
        - At least 32 characters long
        - At least 3 of 4 character types (lowercase, uppercase, digits, special)
        - No single character repeated more than half the key length
    """
    if len(key) < 32:
        return False

    # Check for character diversity
    has_lower = any(c in string.ascii_lowercase for c in key)
    has_upper = any(c in string.ascii_uppercase for c in key)
    has_digit = any(c in string.digits for c in key)
    has_special = any(c in string.punctuation for c in key)

    # Require at least 3 of 4 character types
    diversity_count = sum([has_lower, has_upper, has_digit, has_special])
    if diversity_count < 3:
        return False

    # Check for repeating patterns (no character should appear more than half the time)
    if any(key.count(c) > len(key) // 2 for c in set(key)):
        return False

    return True


class TrueNASConfig(BaseModel):
    """TrueNAS server configuration."""

    host: str = Field(..., description="TrueNAS host address")
    port: int = Field(443, description="TrueNAS port")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v):
        if not v:
            raise ValueError("Host cannot be empty")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class ServerConfig(BaseModel):
    """HTTP server configuration."""

    host: str = Field("0.0.0.0", description="Server host to bind to")
    port: int = Field(8000, description="Server port")
    debug: bool = Field(False, description="Enable debug mode")
    reload: bool = Field(False, description="Enable auto-reload")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class AuthConfig(BaseModel):
    """Authentication configuration."""

    secret_key: str = Field(..., description="JWT secret key")
    algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Token expiry in minutes")
    admin_token: Optional[str] = Field(
        None, description="Admin token for initial setup"
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if not validate_secret_key_strength(v):
            raise ValueError(
                "SECRET_KEY must be at least 32 characters with sufficient entropy. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field("INFO", description="Logging level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )
    file: Optional[str] = Field(None, description="Log file path")
    max_size: int = Field(10 * 1024 * 1024, description="Max log file size in bytes")
    backup_count: int = Field(5, description="Number of backup log files")


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # TrueNAS Configuration
    truenas_host: str = Field(..., env="TRUENAS_HOST")
    truenas_port: int = Field(443, env="TRUENAS_PORT")
    truenas_api_key: Optional[str] = Field(None, env="TRUENAS_API_KEY")
    truenas_username: Optional[str] = Field(None, env="TRUENAS_USERNAME")
    truenas_password: Optional[str] = Field(None, env="TRUENAS_PASSWORD")
    truenas_verify_ssl: bool = Field(True, env="TRUENAS_VERIFY_SSL")

    # Server Configuration
    server_host: str = Field("0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(8000, env="SERVER_PORT")
    debug: bool = Field(False, env="DEBUG")
    reload: bool = Field(False, env="RELOAD")

    # Authentication Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    admin_token: Optional[str] = Field(None, env="ADMIN_TOKEN")

    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    log_max_size: int = Field(10 * 1024 * 1024, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(5, env="LOG_BACKUP_COUNT")

    # CORS Configuration
    cors_origins: list[str] = Field(["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list[str] = Field(["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(["*"], env="CORS_ALLOW_HEADERS")

    # Rate Limiting
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("truenas_host")
    @classmethod
    def validate_truenas_host(cls, v):
        if not v:
            raise ValueError("TRUENAS_HOST cannot be empty")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if not validate_secret_key_strength(v):
            raise ValueError(
                "SECRET_KEY must be at least 32 characters with sufficient entropy. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    @field_validator("truenas_port", "server_port")
    @classmethod
    def validate_ports(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


def load_settings() -> Settings:
    """Load application settings from environment variables."""
    try:
        return Settings()
    except Exception as e:
        raise ValueError(f"Failed to load settings: {e}")


def get_truenas_config(settings: Settings) -> TrueNASConfig:
    """Get TrueNAS configuration from settings."""
    return TrueNASConfig(
        host=settings.truenas_host,
        port=settings.truenas_port,
        api_key=settings.truenas_api_key,
        username=settings.truenas_username,
        password=settings.truenas_password,
        verify_ssl=settings.truenas_verify_ssl,
    )


def get_server_config(settings: Settings) -> ServerConfig:
    """Get server configuration from settings."""
    return ServerConfig(
        host=settings.server_host,
        port=settings.server_port,
        debug=settings.debug,
        reload=settings.reload,
    )


def get_auth_config(settings: Settings) -> AuthConfig:
    """Get authentication configuration from settings."""
    return AuthConfig(
        secret_key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        admin_token=settings.admin_token,
    )


def get_logging_config(settings: Settings) -> LoggingConfig:
    """Get logging configuration from settings."""
    return LoggingConfig(
        level=settings.log_level,
        format=settings.log_format,
        file=settings.log_file,
        max_size=settings.log_max_size,
        backup_count=settings.log_backup_count,
    )


def validate_configuration(settings: Settings) -> None:
    """Validate the complete configuration."""
    # Validate TrueNAS configuration
    if not settings.truenas_api_key and not (
        settings.truenas_username and settings.truenas_password
    ):
        raise ValueError(
            "Either TRUENAS_API_KEY or TRUENAS_USERNAME/TRUENAS_PASSWORD must be set"
        )

    # Validate authentication
    if not validate_secret_key_strength(settings.secret_key):
        raise ValueError(
            "SECRET_KEY must be at least 32 characters with sufficient entropy. "
            "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    # Validate ports
    if not 1 <= settings.truenas_port <= 65535:
        raise ValueError("TRUENAS_PORT must be between 1 and 65535")

    if not 1 <= settings.server_port <= 65535:
        raise ValueError("SERVER_PORT must be between 1 and 65535")


def generate_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)


def create_default_env_file() -> None:
    """Create a default .env file with example configuration."""
    env_content = """# TrueNAS MCP Server Configuration
# Copy this file to .env and update with your values

# TrueNAS Configuration
TRUENAS_HOST=your-truenas-host.example.com
TRUENAS_PORT=443
TRUENAS_API_KEY=your-api-key-here
# OR use username/password
# TRUENAS_USERNAME=admin
# TRUENAS_PASSWORD=your-password-here
TRUENAS_VERIFY_SSL=true

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
RELOAD=false

# Authentication Configuration
SECRET_KEY=your-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_TOKEN=your-admin-token-here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/truenas-mcp.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# CORS Configuration
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
"""

    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print(f"Created default .env file: {env_file}")
        print("Please update the configuration with your TrueNAS server details.")
    else:
        print(".env file already exists. Skipping creation.")
