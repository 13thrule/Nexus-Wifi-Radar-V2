# NEXUS WiFi Radar - Quick Start Guide

Get up and running in 5 minutes! 🚀

## 📦 Installation

### Windows

```powershell
# Clone and install
git clone https://github.com/your-username/nexus-wifi-radar.git
cd nexus-wifi-radar
install.bat
```

**OR** download the ZIP, extract, and double-click `install.bat`

### Linux / Raspberry Pi

```bash
# Clone and install
git clone https://github.com/your-username/nexus-wifi-radar.git
cd nexus-wifi-radar
chmod +x install.sh
./install.sh
```

## 🚀 Launch

### Option 1: Launcher (Recommended)
- **Windows**: Double-click `run_launcher.bat`
- **Linux**: `./venv/bin/python -m nexus launcher`

### Option 2: Direct Radar GUI
- **Windows**: Double-click `run_scanner.bat`
- **Linux**: `./venv/bin/python -m nexus gui`

## 🎯 First Scan

1. Launch NEXUS (see above)
2. Click **"Start Scan"** button
3. Wait 5-10 seconds for networks to appear
4. Networks show up on radar and in table

## 🎨 Customize

### Change Theme
Click theme buttons at top:
- **GREEN** — Neon green (default)
- **CYAN** — Cyan blue
- **PURPLE** — Purple pink
- **RED** — Red alert
- **PINK** — Hot pink
- **PIP-BOY** — Fallout style

### Adjust Filters
- **Minimum Signal**: Slider at top (hides weak networks)
- **Network Type**: Filter by Open/WPA/WPA2/WPA3
- **Vendor**: Search by manufacturer

## 📊 View Intelligence

### Tab Overview
| Tab | What It Shows |
|-----|---------------|
| **Radar** | Circular visualization, networks as blips |
| **Networks** | Sortable table with all details |
| **Security Audit** | Threats and vulnerabilities |
| **Intelligence** | Event feed + detail inspector |
| **Statistics** | Charts, graphs, channel distribution |
| **Event Log** | Timestamped activity |
| **Spectrogram** | Channel utilization heatmap |
| **Hidden Networks** | Analysis of hidden SSIDs |

### Intelligence Dashboard
The **Intelligence Core** tab has 3 panels:

**Left (Summary)**: Quick stats
- 📡 Total networks
- 🚨 Threat count
- ❓ Unknown devices
- 📶 Weak signals

**Center (Feed)**: Event stream
- 🚨 Red = Threat
- ⚠️ Yellow = Anomaly
- 💡 Cyan = Insight
- 📡 Green = Passive

**Right (Inspector)**: Click any event for full details

## 🔍 Identify Devices

NEXUS automatically identifies:
- 🚪 Ring Doorbell
- 📹 Cameras (Ring, Blink, Wyze, Arlo)
- 🔊 Smart Speakers (Echo, Google Home)
- 📶 Routers (BT Hub, EE, Netgear, TP-Link)
- 📱 Phones (Apple, Samsung, Google)
- 💻 Computers (Dell, HP, Lenovo)
- 🎮 Gaming Consoles (PlayStation, Xbox)

Look for icons next to device names!

## ⚡ Active Scanning (Linux Only)

To discover hidden networks:

1. Install Scapy: `pip install scapy`
2. Run with sudo: `sudo ./venv/bin/python -m nexus gui`
3. Enable EASM in settings
4. Hidden networks appear in **Hidden Networks** tab

**Note**: Requires root/sudo permissions

## 🔒 Security Checks

NEXUS automatically detects:
- ❌ Open networks (no password)
- ⚠️ Weak encryption (WEP)
- 🚨 Spoofed SSIDs (same name, different MAC)
- 👻 Hidden networks
- 🔴 Rogue access points

Check the **Security Audit** tab for findings.

## 📈 Monitor Signal Strength

### Radar View
- **Center**: Strongest signals (closest)
- **Edge**: Weakest signals (farthest)
- **Size**: Bigger blips = stronger signal

### Network Table
- Signal bar shows strength
- Click columns to sort
- Filter by minimum signal

### Tips
- Walk around to see signals change
- Strong hidden network nearby? Might be your Ring doorbell!
- Erratic signals indicate moving devices

## 🎯 Common Tasks

### Find Your Ring Doorbell
1. Go to **Hidden Networks** tab
2. Look for strong signal (-50 to -30 dBm)
3. Check vendor: Should show 🚪 Ring or Amazon
4. Distance: Likely 5-15 meters

### Check Router Security
1. Go to **Networks** tab
2. Find your SSID
3. Check Security column
4. Should say WPA2 or WPA3 (not Open or WEP!)

### Identify Unknown Device
1. Note the MAC address (BSSID)
2. Check Vendor column
3. Look at signal strength
4. Go to **Intelligence** tab for AI classification

### Export Scan Results
1. Go to **Event Log** tab
2. Click **"Save Log"** button
3. Choose format: TXT, JSON, or CSV
4. Select save location

## 🛠️ Troubleshooting

### No Networks Found
**Windows**: Check WiFi adapter is on (`netsh wlan show interfaces`)
**Linux**: Run with sudo (`sudo ./venv/bin/python -m nexus gui`)

### App Hangs on Startup (Windows)
Already fixed! Scapy is disabled on Windows to prevent this.

### Blank Radar Display
- Click **"Start Scan"** button
- Wait 10 seconds
- Networks should appear
- If not, check WiFi adapter

### Theme Not Changing
- Click theme button again
- Check if app is scanning (pause first)
- Restart app if needed

### "Permission Denied" Error (Linux)
Run with sudo: `sudo ./venv/bin/python -m nexus gui`

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Architecture Details**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Feature List**: See [docs/FEATURES.md](docs/FEATURES.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md)

## ❓ Get Help

- **Issues**: https://github.com/your-repo/nexus-wifi-radar/issues
- **Discussions**: https://github.com/your-repo/nexus-wifi-radar/discussions
- **Discord**: [Coming soon]

## 🎉 You're Ready!

Start exploring the WiFi spectrum around you. NEXUS reveals the invisible infrastructure that connects our world.

**Pro tip**: Launch the app, start a scan, and just watch for a few minutes. You'll see networks come and go, devices move around, and patterns emerge. It's fascinating! 🌐

---

```
╔═══════════════════════════════════════════════════════════╗
║   NEXUS v2.0 — Your eyes in the invisible spectrum        ║
╚═══════════════════════════════════════════════════════════╝
```
