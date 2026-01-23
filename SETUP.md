# NEXUS V2.0 Setup Guide

## Quick Start (2 Minutes)

### Windows
```cmd
# 1. Clone the repository
git clone https://github.com/yourusername/Nexus-Wifi-Radar-V2.git
cd Nexus-Wifi-Radar-V2

# 2. Run installer (creates virtual environment & installs dependencies)
install.bat

# 3. Launch NEXUS
run_scanner.bat
```

### Linux / Mac / Raspberry Pi
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Nexus-Wifi-Radar-V2.git
cd Nexus-Wifi-Radar-V2

# 2. Run installer
chmod +x install.sh
./install.sh

# 3. Launch NEXUS
python3 -m nexus gui

# OR with Enhanced Active Scan Mode (requires sudo & monitor-mode WiFi adapter)
sudo python3 -m nexus gui --easm
```

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, Debian 11+, Raspberry Pi OS
- **Python**: 3.8 or higher
- **RAM**: 512MB minimum
- **Storage**: 100MB

### Recommended
- **RAM**: 2GB+ for smooth operation
- **WiFi Adapter**: Built-in or USB WiFi adapter
- **For EASM** (Linux only): Monitor-mode capable WiFi adapter

---

## Manual Installation (If Installers Don't Work)

### 1. Install Python
**Windows**: Download from [python.org](https://www.python.org/downloads/)  
**Linux**: `sudo apt install python3 python3-pip python3-venv`

### 2. Create Virtual Environment
```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment
**Windows**:
```cmd
venv\Scripts\activate
```

**Linux/Mac**:
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install scapy psutil netifaces matplotlib numpy pillow
```

### 5. Run NEXUS
```bash
python -m nexus gui
```

---

## Platform-Specific Notes

### Windows
- Uses `netsh` for WiFi scanning (no admin rights needed)
- Scapy installed but packet injection disabled on Windows
- EASM mode not available

### Linux
- Uses `nmcli` or `iwlist` for scanning
- EASM mode requires `sudo` and monitor-mode WiFi adapter
- May need to install network-manager: `sudo apt install network-manager`

### Raspberry Pi
- Optimized for RPi 3/4/Zero 2 W
- Works with built-in WiFi or USB adapters
- Can run headless with SSH + X11 forwarding
- EASM mode supported with compatible WiFi adapters

---

## Launch Modes

### GUI Mode (Full Interface)
```bash
python -m nexus gui
```

### CLI Mode (Terminal Only)
```bash
python -m nexus cli --duration 30
```

### Launcher Mode (Choose Interface)
```bash
python -m nexus launcher
```

### EASM Mode (Linux Only - Requires sudo)
```bash
sudo python -m nexus gui --easm
```

---

## Troubleshooting

### "No module named 'nexus'"
Make sure you're in the project directory and virtual environment is activated.

### "Permission denied" on Linux
Use `sudo` for EASM mode: `sudo python3 -m nexus gui --easm`

### WiFi adapter not detected
Check WiFi adapter status:
```bash
# Windows
netsh wlan show interfaces

# Linux
nmcli device status
iwconfig
```

### Scapy import errors on Windows
Scapy may require Npcap. Download from [npcap.com](https://npcap.com/)

### GUI doesn't launch
Check Python/Tkinter installation:
```bash
python -c "import tkinter; print('Tkinter OK')"
```

If fails on Linux: `sudo apt install python3-tk`

---

## Configuration

### Settings File
NEXUS stores settings in:
- **Windows**: `%APPDATA%\nexus\config.json`
- **Linux/Mac**: `~/.config/nexus/config.json`

### OUI Database
The OUI vendor database is embedded in `nexus/core/vendor.py` with 300+ entries.

### Theme Persistence
Your selected theme is saved and restored on next launch.

---

## Testing Installation

Run the test suite to verify everything works:
```bash
# Activate venv first
python -m pytest tests/

# Or run specific tests
python tests/test_smoke.py
python tests/test_features.py
```

---

## Next Steps

1. ✅ Complete installation
2. ✅ Launch GUI
3. ✅ Run first scan
4. ✅ Explore Intelligence Dashboard
5. ✅ Try different themes
6. ✅ Check Hidden Networks tab
7. ✅ Review Security Audit

See [QUICKSTART.md](QUICKSTART.md) for usage guide.
See [docs/FEATURES.md](docs/FEATURES.md) for full feature reference.

---

## Uninstallation

### Simple
Just delete the project folder. NEXUS doesn't install system-wide.

### Complete (with config)
**Windows**:
```cmd
rmdir /s /q "%APPDATA%\nexus"
rmdir /s /q "C:\path\to\Nexus-Wifi-Radar-V2"
```

**Linux/Mac**:
```bash
rm -rf ~/.config/nexus
rm -rf ~/Nexus-Wifi-Radar-V2
```

---

## Getting Help

- **Documentation**: [docs/](docs/) folder
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/Nexus-Wifi-Radar-V2/issues)
- **Features**: [docs/FEATURES.md](docs/FEATURES.md)

---

**Ready to scan! 🚀**
