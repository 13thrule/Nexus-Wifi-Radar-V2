# Nexus WiFi Radar - Features

## Implemented Features (v2.0)

### 📡 WiFi Scanning
- [x] Real-time WiFi network discovery
- [x] Signal strength measurement (RSSI → percentage)
- [x] Channel and frequency detection
- [x] BSSID (MAC address) capture
- [x] Band detection (2.4GHz vs 5GHz)
- [x] Security type parsing (Open, WEP, WPA, WPA2, WPA3)
- [x] OUI vendor lookup (MAC → manufacturer)
- [x] Multi-platform scanner interface

### 🔒 Threat Detection
- [x] `Threat` dataclass with severity levels
- [x] Weak encryption detection (WEP, Open)
- [x] Evil twin / SSID spoofing detection
- [x] Rogue AP heuristics
- [x] Channel anomaly detection
- [x] Hidden network detection
- [x] Threat summary with severity levels

### 📊 Visualization
- [x] Full tabbed GUI application
- [x] Radar-style network display
- [x] Color-coded signal strength
- [x] Network table with details
- [x] Threat panel with alerts
- [x] Settings/configuration panel
- [x] Signal strength heatmap

### 🎨 Theming & Skins
- [x] 7 cyberpunk color themes (F1-F7 to switch)
- [x] Neon Green, Cyan, Purple, Red, Pink, Sleek Pro
- [x] **Pip-Boy Skin Plugin** - Fallout-style terminal aesthetic
  - [x] Green phosphor monochrome palette
  - [x] CRT scanline animation effects
  - [x] Retro terminal fonts (Fixedsys, Terminal)
  - [x] Amber warning highlights
  - [x] Animated radar sweep
  - [x] ASCII art decorations (Vault-Tec style)
  - [x] Chunky button styling
  - [x] 100% offline, non-destructive, toggleable

### 🔊 Audio Feedback
- [x] Sonar-style signal tones
- [x] RSSI-based pitch/volume
- [x] Threat alert sounds
- [x] Configurable audio settings

### 🌐 Web Dashboard
- [x] FastAPI REST API server
- [x] Real-time WebSocket updates
- [x] HTML/JS web dashboard
- [x] Remote scan triggering
- [x] Network/threat API endpoints

### 💾 Data Export
- [x] JSON export (full data)
- [x] CSV export with timestamp
- [x] HTML report generation

### 🖥️ Platform Support
- [x] Windows (netsh + optional Scapy)
- [x] Linux (nmcli / iwlist / iw)
- [x] Raspberry Pi (wpa_cli / iwlist)

### ⌨️ Command Line Interface
- [x] `nexus scan` - Single scan
- [x] `nexus continuous` - Continuous scanning
- [x] `nexus config` - View/modify config
- [x] `nexus gui` - Launch GUI
- [x] `nexus server` - Launch web dashboard
- [x] `nexus list-scanners` - Show available scanners

---

## Feature Details

### Scanning Engine

The scanning engine uses platform-specific backends:

| Platform | Primary | Fallback | Optional |
|----------|---------|----------|----------|
| Windows | netsh | - | Scapy |
| Linux | nmcli | iwlist, iw | Scapy |
| Raspberry Pi | wpa_cli | iwlist | - |

**Network Data Model:**
```python
@dataclass
class Network:
    ssid: str           # Network name
    bssid: str          # MAC address
    channel: int        # WiFi channel (1-165)
    frequency_mhz: int  # Frequency in MHz
    rssi_dbm: int       # Signal strength in dBm
    security: SecurityType = UNKNOWN
    vendor: str = "Unknown"
    last_seen: datetime = field(default_factory=datetime.now)
    
    @property
    def signal_percent(self) -> int:
        # Convert dBm to 0-100%
    
    @property
    def band(self) -> str:
        # "2.4GHz" or "5GHz"
```

### Threat Detection

Five built-in detection rules:

1. **WeakEncryptionRule** - Flags OPEN and WEP networks
2. **SSIDSpoofingRule** - Detects duplicate SSIDs from different BSSIDs
3. **RogueAPRule** - Identifies unauthorized access points
4. **ChannelAnomalyRule** - Flags unusual channel usage patterns
5. **HiddenNetworkRule** - Reports networks without SSIDs

**Threat Severity Levels:**
- `CRITICAL` - Immediate security risk
- `HIGH` - Significant security concern
- `MEDIUM` - Potential issue
- `LOW` - Informational
- `INFO` - For awareness only

### GUI Application

The main GUI (`nexus gui`) provides:

- **Radar Tab**: Visual radar with networks positioned by signal strength
- **Networks Tab**: Sortable table with all network details
- **Threats Tab**: Security alerts with severity indicators
- **Settings Tab**: Configuration options

Controls:
- Scan button for manual scans
- Continuous mode toggle
- Export to JSON/CSV/HTML
- Audio toggle

### Web Dashboard

The FastAPI server (`nexus server`) provides:

**REST API:**
- `GET /api/status` - Server status and stats
- `GET /api/scan?timeout=10` - Trigger scan
- `GET /api/networks` - Last scan's networks
- `GET /api/threats` - Active threats

**WebSocket:**
- `WS /ws` - Real-time scan updates

**Dashboard:**
- Modern web UI at server root
- Auto-refreshing data
- Responsive design

### Audio Sonar

The audio module generates:
- **Signal Tones**: Pitch based on RSSI (-30dBm = high, -90dBm = low)
- **Threat Alerts**: Distinct sounds for each severity level
- **Sweep Mode**: Cycles through detected networks

---

## Configuration

Configuration is stored in JSON and can be modified via CLI:

```bash
# View all settings
nexus config --show

# Modify a setting
nexus config --set scan.timeout_seconds=15
nexus config --set audio.enabled=true

# Reset to defaults
nexus config --reset
```

**Config Structure:**
```python
@dataclass
class Config:
    scan: ScanConfig      # timeout, use_scapy, interfaces
    ui: UIConfig          # theme, window size, update interval
    audio: AudioConfig    # enabled, volume, sweep
    security: SecurityConfig  # enabled rules, whitelist
```

---

## Roadmap (Future)

### Phase 5 - Advanced Features (Optional)
- [ ] GPS integration for geolocation
- [ ] Signal strength heatmap overlay
- [ ] Network history/trends
- [ ] Custom rule definitions
- [ ] PCAP file analysis
- [ ] Machine learning anomaly detection

### Phase 6 - Deployment
- [ ] GitHub Actions CI/CD
- [ ] PyPI package publishing
- [ ] Docker container
- [ ] Standalone executables (PyInstaller)
