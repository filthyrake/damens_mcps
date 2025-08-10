#!/bin/bash
# Setup script for Proxmox MCP Server

echo "🚀 Setting up Proxmox MCP Server..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.simple.txt

# Create config file if it doesn't exist
if [ ! -f config.json ]; then
    echo "⚙️  Creating config.json from example..."
    cp config.example.json config.json
    echo "📝 Please edit config.json with your Proxmox server details"
fi

echo "✅ Setup complete!"
echo ""
echo "To use the server:"
echo "1. Edit config.json with your Proxmox server details"
echo "2. Activate the virtual environment: source .venv/bin/activate"
echo "3. Test the server: python3 test_server.py"
echo "4. Run the server: python3 working_proxmox_server.py"
