#!/bin/bash

# Test script to verify environment variable loading in Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Testing Docker Compose Environment Variable Loading"
echo "📁 Project root: $PROJECT_ROOT"

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "❌ Error: .env file not found at $PROJECT_ROOT/.env"
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

echo "📊 Environment variables from .env file:"
echo "   - TRUENAS_HOST: ${TRUENAS_HOST:-not set}"
echo "   - TRUENAS_PORT: ${TRUENAS_PORT:-not set}"
echo "   - TRUENAS_API_KEY: ${TRUENAS_API_KEY:-not set}"
echo "   - SECRET_KEY: ${SECRET_KEY:-not set}"
echo "   - DEBUG: ${DEBUG:-not set}"
echo "   - LOG_LEVEL: ${LOG_LEVEL:-not set}"

# Test Docker Compose config
echo ""
echo "🔧 Testing Docker Compose configuration..."
cd "$SCRIPT_DIR"

# Show the resolved environment variables that Docker Compose would use
echo "📋 Docker Compose resolved environment variables:"
docker-compose config | grep -A 20 "environment:" || echo "No environment section found"

echo ""
echo "✅ Environment variable test complete!"
