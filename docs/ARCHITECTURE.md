# Nexus WiFi Radar - Architecture

## Overview

Nexus WiFi Radar is a cross-platform WiFi network scanner and security analysis tool with radar-style visualization, threat detection, and audio feedback capabilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Radar UI   │  │  Heatmap    │  │  CLI / Remote Dashboard │ │
│  │  (Tkinter)  │  │  (Canvas)   │  │  (FastAPI + HTML/JS)    │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          └────────────────┼─────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Core Engine                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Scanner   │  │   Models    │  │   Config Manager        │ │
│  │  Interface  │  │  (Network,  │  │   (Settings, Paths)     │ │
│  └──────┬──────┘  │   Threat)   │  └─────────────────────────┘ │
│         │         └─────────────┘                               │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Platform Abstraction Layer                     ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐││
│  │  │   Windows    │ │ Generic      │ │  Raspberry Pi        │││
│  │  │   Scanner    │ │ Linux        │ │  Scanner             │││
│  │  │   (netsh/    │ │ Scanner      │ │  (iwlist/wpa)        │││
│  │  │    scapy)    │ │ (iwlist/nmcli│ │                      │││
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Security Engine                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Detection  │  │   Rules     │  │   Report Generator      │ │
│  │   Engine    │  │  (Weak enc, │  │   (JSON, HTML, CSV)     │ │
│  │             │  │   Rogue AP) │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Audio Feedback                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Sonar Module - RSSI-based tones, threat alerts             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
nexus/
├── __init__.py           # Package initialization, version
├── app.py                # Main GUI application
├── server.py             # FastAPI web dashboard
├── core/
│   ├── __init__.py
│   ├── scan.py           # Scanner interface and factory
│   ├── models.py         # Network, Threat, ScanResult dataclasses
│   ├── config.py         # Configuration management
│   ├── vendor.py         # OUI/MAC vendor lookup
│   ├── oui_vendor.py     # OUI Vendor Intelligence Module (OUI-IM)
│   ├── distance.py       # Signal-to-distance estimation
│   ├── fingerprint.py    # Device type fingerprinting
│   ├── stability.py      # Signal stability tracking
│   ├── radar_modes.py    # Radar visualization modes
│   ├── intelligence.py   # Passive Intelligence Core (PIC)
│   ├── world_model.py    # Unified World Model Expander (UWM-X)
│   └── hidden_classifier.py  # Hidden Network Classification Engine (HNCE)
├── ui/
│   ├── __init__.py
│   ├── radar.py          # RadarView class (Tkinter canvas)
│   ├── heatmap.py        # HeatmapRenderer class
│   ├── cli.py            # Command-line interface
│   └── skins/            # UI Skin Plugin System
│       ├── __init__.py   # Skin loader/exports
│       └── pipboy.py     # Pip-Boy skin (Fallout aesthetic)
├── audio/
│   ├── __init__.py
│   └── sonar.py          # Audio feedback (RSSI tones, alerts)
├── platform/
│   ├── __init__.py
│   ├── windows.py        # WindowsScanner (netsh, scapy)
│   ├── raspberry_pi.py   # PiScanner (iwlist, wpa_supplicant)
│   └── generic_linux.py  # LinuxScanner (nmcli, iwlist)
└── security/
    ├── __init__.py
    ├── detection.py      # ThreatDetector class
    ├── rules.py          # Detection rules (weak enc, rogue AP)
    ├── spoof.py          # Spoof detection
    └── report.py         # Report generation
```

## UI Skin System

The skin system (`nexus/ui/skins/`) provides:

- **Modular Themes**: Drop-in visual skin plugins
- **Non-Destructive**: Original styling preserved, revertible
- **100% Offline**: No external assets or network calls
- **Animated Effects**: CRT scanlines, flicker, glow

### Pip-Boy Skin

The Pip-Boy skin transforms NEXUS into a Fallout-style terminal:

```python
# Key components:
- PipBoyPalette: Green phosphor color palette
- PipBoyFonts: Terminal font configuration
- CRTAnimator: Animated CRT effects (~30 FPS)
- PipBoySkin: Main skin class (apply/revert)
- PipBoyHeatmapColors: Green monochrome gradient
- PipBoyDecorations: ASCII art elements
```

## Data Flow

1. **Scan Request** → Platform-specific scanner collects raw network data
2. **Network Objects** → Parsed into `Network` dataclass with vendor lookup
3. **Threat Analysis** → Security engine evaluates networks against rules
4. **UI Update** → Radar/Heatmap/CLI displays results
5. **Audio Feedback** → Sonar module generates tones based on RSSI/threats
6. **Export/Report** → Data saved to CSV/JSON/HTML

## Key Design Decisions

### 1. Platform Abstraction
- Abstract `Scanner` interface allows seamless platform switching
- Factory pattern (`get_scanner()`) auto-detects platform at runtime
- Each platform module encapsulates OS-specific commands

### 2. Dataclass Models
- Immutable `Network` and `Threat` dataclasses ensure data integrity
- Type hints throughout for IDE support and validation
- JSON serialization built-in for API/export

### 3. Plugin Architecture (Future)
- Detection rules are modular and can be added without core changes
- UI components are independent and swappable

### 4. Thread Safety
- Scanning runs in background threads
- UI updates via thread-safe queues
- Locks protect shared network state

## Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| tkinter | GUI framework | Yes (stdlib) |
| scapy | Packet capture | Optional (enhanced scanning) |
| matplotlib | Heatmap visualization | Optional |
| fastapi | Remote dashboard | Optional |
| uvicorn | ASGI server | Optional |

## Configuration

Configuration is managed via `nexus/core/config.py`:

```python
# Default config locations:
# Windows: %APPDATA%/nexus/config.json
# Linux:   ~/.config/nexus/config.json
```

## Security Considerations

- No credentials stored
- Scan results can contain sensitive network names
- Export files should be protected
- Remote dashboard requires authentication (Phase 4)
