#!/bin/bash
# NEXUS WiFi Radar - Linux/Mac Uninstallation Script

echo "=========================================="
echo "  NEXUS WiFi Radar - Uninstaller"
echo "=========================================="
echo ""
echo "This will remove:"
echo "  - Virtual environment (venv/)"
echo "  - Python cache files (__pycache__)"
echo "  - Build artifacts (dist/, *.egg-info)"
echo ""
echo "Your source code and configuration will be preserved."
echo ""
read -p "Are you sure you want to uninstall? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "Starting uninstallation..."
echo ""

# Stop any running NEXUS processes
echo "[1/5] Stopping NEXUS processes..."
pkill -f "python.*nexus" 2>/dev/null
sleep 2
echo "      Done."

# Remove virtual environment
echo "[2/5] Removing virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "      Removed venv/"
else
    echo "      Virtual environment not found (already removed)"
fi

# Remove Python cache
echo "[3/5] Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo "      Done."

# Remove build artifacts
echo "[4/5] Removing build artifacts..."
rm -rf dist/ build/ *.egg-info 2>/dev/null
echo "      Done."

# Clean nexus package
echo "[5/5] Cleaning nexus package..."
if [ -d "nexus" ]; then
    find nexus -type f -name "*.pyc" -delete 2>/dev/null
    find nexus -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
fi
echo "      Done."

echo ""
echo "=========================================="
echo "  Uninstallation Complete!"
echo "=========================================="
echo ""
echo "NEXUS has been uninstalled from your system."
echo ""
echo "Preserved files:"
echo "  - Source code (nexus/)"
echo "  - Documentation (docs/, *.md)"
echo "  - Configuration files"
echo "  - Screenshots (assets/)"
echo ""
echo "To reinstall, run: ./install.sh"
echo ""
