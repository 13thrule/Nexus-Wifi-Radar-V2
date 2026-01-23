# Changelog

All notable changes to NEXUS WiFi Radar will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-23

### 🎉 Major Release - Complete Rewrite

#### Added
- **Intelligence Dashboard** — Three-panel design (Summary, Feed, Detail Inspector)
- **Smart Device Detection** — 300+ OUI entries with device-specific icons (🚪 Ring, 📹 Camera, 🔊 Echo, etc.)
- **Six Cyberpunk Themes** — Neon Green, Cyan, Purple, Red, Pink, Pip-Boy
- **Dynamic Theme System** — Real-time tab color updates, no restart needed
- **Enhanced Vendor Lookup** — Smart locally-administered MAC handling (e.g., 72:d4:2e → cc:d4:2e)
- **UK ISP Router Support** — BT Hub, EE Router, Sky, Virgin Media, TalkTalk, Plusnet, Vodafone
- **IoT Device Icons** — Visual indicators for Ring doorbells, cameras, smart home devices
- **Detailed Event Inspector** — Full network intelligence on threat/anomaly clicks
- **NEXUS Launcher** — Central hub with animated boot sequence
- **Hidden Network Classification** — HNCE engine identifies device types
- **Signal Stability Tracking** — Erratic signal detection
- **Movement Detection** — Fast-moving device alerts
- **Security Parsing Fix** — Correct WPA2/WPA3 detection from netsh output
- **Event Feed System** — Color-coded intelligence stream (Threat, Anomaly, Insight, Passive)
- **Periodic Summaries** — Every 10 scans, generate environment overview
- **Multiple Network Views** — Radar, Table, Heatmap, Spectrogram, Event Log
- **Distance Estimation** — RSSI to meters with environment awareness
- **Vulnerability Scanning** — Open networks, weak encryption, rogue APs
- **EASM Mode** — Active scanning for hidden network discovery (Linux only)

#### Enhanced
- **Vendor Database** — Expanded from ~50 to 300+ OUI entries
- **Security Detection** — Multi-indicator spoof detection
- **World Model (UWM-X)** — Network relationship tracking
- **Passive Intelligence Core (PIC)** — Unified analysis coordinator
- **OUI-IM Engine** — Full vendor intelligence with risk scoring
- **Performance** — Optimized scan processing and UI updates

#### Fixed
- **Windows Security Parsing** — Authentication now correctly parsed before BSSIDs
- **Notebook Tab Colors** — Dynamic theme application to all tabs
- **Event System Crash** — Fixed pack ordering in Intelligence Feed
- **MAC Randomization** — Better detection of locally-administered addresses
- **Channel Display** — Correct 2.4GHz/5GHz band identification

#### Technical
- **Architecture** — Modular core, reusable components
- **Type Hints** — Full type annotations for all public APIs
- **Testing** — Comprehensive test suite with pytest
- **Documentation** — Complete README with examples
- **License** — MIT License
- **Platform Support** — Windows (netsh), Linux (nmcli/iwlist), Raspberry Pi

### 🔒 Security Notes
- Scapy disabled on Windows due to Npcap USB adapter incompatibility
- All vendor lookups performed offline (no network calls)
- No telemetry or data collection

---

## [1.0.0] - 2025-XX-XX

### Initial Release
- Basic WiFi scanning
- Radar visualization
- Security threat detection
- Cross-platform support (Windows, Linux)
- OUI vendor lookup (~50 entries)

---

## Upgrade Guide

### From 1.x to 2.0

**Breaking Changes:**
- Configuration file format changed — backup your `config.json` before upgrading
- Some API signatures in `nexus.core` have changed (see MIGRATION.md)

**New Dependencies:**
- None! NEXUS 2.0 remains zero-dependency for core functionality

**Steps:**
1. Backup configuration: `cp config.json config.json.bak`
2. Pull latest code: `git pull origin main`
3. Reinstall: `pip install -e .`
4. Launch: `python -m nexus gui`
5. Reconfigure settings if needed

---

## Future Roadmap

### v2.1 (Q1 2026)
- [ ] Web dashboard with REST API
- [ ] Export to JSON/CSV/HTML
- [ ] Custom detection rule builder (GUI)
- [ ] Signal strength graphs
- [ ] Multi-language support

### v2.2 (Q2 2026)
- [ ] Machine learning device classification
- [ ] Bluetooth LE scanning
- [ ] GPS integration for wardriving
- [ ] Database storage (SQLite)

### v3.0 (Future)
- [ ] Distributed scanning (multiple sensors)
- [ ] Cloud intelligence sharing (opt-in)
- [ ] Mobile app (Android/iOS)
- [ ] Professional security audit mode

---

**Note**: Dates are approximate. Features may be added, removed, or rescheduled based on community feedback and development priorities.
