#!/bin/bash
# NEXUS WiFi Radar - Linux/Mac Installation Script

set -e  # Exit on error

echo "=================================="
echo "NEXUS WiFi Radar Installation"
echo "=================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Check if we're on Linux and need system packages
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "Checking system dependencies..."
    
    # Check for Tkinter
    if ! python3 -c "import tkinter" &> /dev/null; then
        echo "❌ Tkinter not found. Installing system packages..."
        sudo apt-get update
        sudo apt-get install -y python3-tk python3-venv python3-pip
    fi
    
    echo "✓ System dependencies OK"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install NEXUS
echo ""
echo "Installing NEXUS WiFi Radar..."
pip install -e .
echo "✓ NEXUS installed"

# Optional: Install Scapy for EASM mode
echo ""
read -p "Install Scapy for active scanning? (requires root, Linux only) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install scapy
    echo "✓ Scapy installed"
    echo "⚠️  Note: You'll need to run NEXUS with sudo for active scanning"
fi

# Run tests
echo ""
read -p "Run test suite? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install pytest
    pytest -v
fi

# Success
echo ""
echo "=================================="
echo "✓ Installation Complete!"
echo "=================================="
echo ""
echo "To launch NEXUS:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Run launcher: python -m nexus launcher"
echo "  3. Or run GUI: python -m nexus gui"
echo ""
echo "For scanning with elevated privileges (Linux):"
echo "  sudo venv/bin/python -m nexus gui"
echo ""
echo "Documentation: README.md"
echo "Issues: https://github.com/your-repo/nexus-wifi-radar/issues"
echo ""
