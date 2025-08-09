#!/bin/bash

# TrueNAS MCP Server Docker Compose Runner
# This script ensures proper environment variable loading

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting TrueNAS MCP Server with Docker Compose"
echo "📁 Project root: $PROJECT_ROOT"

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "❌ Error: .env file not found at $PROJECT_ROOT/.env"
    echo "💡 Please run 'python -m src.http_cli init' to create the .env file"
    exit 1
fi

echo "✅ Found .env file"

# Load environment variables (only valid ones)
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # Only export if key is a valid identifier
    if [[ $key =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
        export "$key=$value"
    fi
done < "$PROJECT_ROOT/.env"

# Check required environment variables
if [ -z "$TRUENAS_HOST" ]; then
    echo "⚠️  Warning: TRUENAS_HOST not set in .env file"
fi

if [ -z "$TRUENAS_API_KEY" ] && [ -z "$TRUENAS_USERNAME" ]; then
    echo "⚠️  Warning: Neither TRUENAS_API_KEY nor TRUENAS_USERNAME/TRUENAS_PASSWORD set"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Warning: SECRET_KEY not set in .env file"
fi

echo "🔧 Starting Docker Compose..."
echo "📊 Environment variables loaded:"
echo "   - TRUENAS_HOST: ${TRUENAS_HOST:-not set}"
echo "   - TRUENAS_PORT: ${TRUENAS_PORT:-443}"
echo "   - DEBUG: ${DEBUG:-false}"
echo "   - LOG_LEVEL: ${LOG_LEVEL:-INFO}"

# Run Docker Compose
cd "$SCRIPT_DIR"
docker-compose up -d

echo "✅ TrueNAS MCP Server started!"
echo "🌐 Server URL: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop server: docker-compose down"
echo "   - Restart server: docker-compose restart"
