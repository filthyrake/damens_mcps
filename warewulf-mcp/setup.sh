#!/bin/bash

# Warewulf MCP Server Setup Script
# This script sets up the Python virtual environment and installs dependencies

set -e

echo "🚀 Setting up Warewulf MCP Server..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or later is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f "config.json" ]; then
    echo "⚙️ Creating config.json from template..."
    cp config.example.json config.json
    echo "⚠️  Please edit config.json with your Warewulf server details"
else
    echo "✅ config.json already exists"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔐 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env with your credentials"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your Warewulf server details"
echo "2. Edit .env with your credentials"
echo "3. Run: .venv/bin/python working_warewulf_server.py"
echo "4. Test with: .venv/bin/python test_server.py"
echo ""
echo "⚠️  Remember: This MCP server is in testing status!"
echo "   It has NOT been tested against a live Warewulf server."
