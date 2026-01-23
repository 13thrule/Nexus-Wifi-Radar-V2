# Enhanced Active Scan Mode (EASM)
## NEXUS WiFi Intelligence Platform

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   ║
║                    ▓  ENHANCED ACTIVE SCAN MODE (EASM)   ▓                   ║
║                    ▓  Legal • Ethical • Standards-Based  ▓                   ║
║                    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Executive Summary

Enhanced Active Scan Mode (EASM) extends NEXUS beyond pure passive beacon reception to include **standards-compliant active scanning techniques**. This mode leverages the WiFi protocol's built-in discovery mechanisms—exactly as every smartphone, laptop, and IoT device does—to gather richer intelligence without any illegal, unethical, or network-affecting operations.

### Design Philosophy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EASM OPERATIONAL ENVELOPE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ✅ ALLOWED                          ❌ PROHIBITED                        │
│   ─────────────                       ─────────────                         │
│   • Probe Requests (broadcast)        • Connecting to networks              │
│   • Probe Requests (directed)         • Authentication attempts             │
│   • Capability queries                • Deauthentication frames             │
│   • Passive channel monitoring        • Association frames                  │
│   • Beacon frame analysis             • Data frame injection                │
│   • Noise floor measurement           • Impersonation of any device         │
│   • Airtime observation               • WPS PIN bruteforcing                │
│   • IE field parsing                  • Handshake capture for cracking      │
│   • OUI fingerprinting                • Any form of denial-of-service       │
│   • Probe response correlation        • Packet replay                       │
│                                       • PMKID harvesting for cracking       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Guarantees

| Guarantee | Description |
|-----------|-------------|
| **100% Legal** | Uses only standard WiFi discovery mechanisms defined in IEEE 802.11 |
| **100% Ethical** | Does not access, disrupt, or interfere with any network or device |
| **100% Standards-Compliant** | All transmitted frames are valid IEEE 802.11 management frames |
| **Zero Network Connection** | Never sends Association or Authentication frames |
| **Zero Security Bypass** | Never attempts to circumvent encryption or access controls |
| **Zero Interference** | Frame transmission rates stay well below disruptive thresholds |
| **Zero Impersonation** | Always uses device's true MAC (or clearly-marked random MACs) |
| **Zero Packet Injection** | Only Probe Requests—no data or control frame injection |

---

## 2. Mode Architecture

### 2.1 System Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEXUS ARCHITECTURE                                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         USER INTERFACES                              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │  │
│  │  │ Radar View │  │  Heatmap   │  │    CLI     │  │ Pip-Boy Skin │   │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘   │  │
│  └────────┼───────────────┼───────────────┼─────────────────┼──────────┘  │
│           │               │               │                 │              │
│           └───────────────┴───────────────┴─────────────────┘              │
│                                   │                                        │
│                                   ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    UNIFIED WORLD MODEL (UWM-X)                       │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────┐ ┌───────────────┐  │  │
│  │  │  Temporal   │ │  Relational  │ │   Spatial  │ │  Environment  │  │  │
│  │  │  Signatures │ │    Graph     │ │   Context  │ │    Context    │  │  │
│  │  └──────┬──────┘ └──────┬───────┘ └─────┬──────┘ └───────┬───────┘  │  │
│  └─────────┼───────────────┼───────────────┼─────────────────┼─────────┘  │
│            │               │               │                 │             │
│            └───────────────┴───────────────┴─────────────────┘             │
│                                   │                                        │
│                                   ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    PASSIVE INTELLIGENCE CORE (PIC)                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │  │
│  │  │ Distance │ │ Fingerprint│ │ Stability │ │ Security │ │ Movement  │  │  │
│  │  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬─────┘  │  │
│  └────────┼────────────┼────────────┼────────────┼────────────┼────────┘  │
│           │            │            │            │            │            │
│           └────────────┴────────────┴────────────┴────────────┘            │
│                                   │                                        │
│                                   ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         SCAN ENGINE                                  │  │
│  │                                                                      │  │
│  │   ┌──────────────────────┐    ┌───────────────────────────────────┐ │  │
│  │   │   PASSIVE SCANNER    │◄───│    ENHANCED ACTIVE SCANNER        │ │  │
│  │   │   (Beacon Listener)  │    │    (EASM - OPTIONAL MODULE)       │ │  │
│  │   │                      │    │                                   │ │  │
│  │   │  • Beacon reception  │    │  • Directed Probe Requests        │ │  │
│  │   │  • Probe response Rx │    │  • Channel Sweeping               │ │  │
│  │   │  • IE parsing        │    │  • IE Requests                    │ │  │
│  │   │  • RSSI measurement  │    │  • Device Fingerprinting          │ │  │
│  │   └──────────────────────┘    │  • Hidden SSID Discovery          │ │  │
│  │                               │  • Passive+ Enhancements          │ │  │
│  │                               └───────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │                     PLATFORM ABSTRACTION LAYER                       │  │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │   │   Windows    │  │    Linux     │  │ Raspberry Pi │              │  │
│  │   │   (Scapy)    │  │ (iwconfig)   │  │  (wpa_cli)   │              │  │
│  │   └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Structure

```
nexus/
├── core/
│   ├── active_scan.py          # NEW: EASM core engine
│   ├── probe_engine.py         # NEW: Probe request management
│   ├── channel_survey.py       # NEW: Channel analysis
│   ├── ie_parser.py            # NEW: Information Element harvesting
│   ├── active_fingerprint.py   # NEW: Active fingerprinting
│   └── hidden_reveal.py        # NEW: Hidden SSID discovery
├── safety/                      # NEW: Safety subsystem
│   ├── __init__.py
│   ├── rate_limiter.py         # Transmission rate limiting
│   ├── legal_guard.py          # Legal compliance checks
│   └── frame_validator.py      # Frame validity checks
```

---

## 3. Feature Specifications

### 3.1 Active Scanning (Directed Probe Requests)

#### Description

Active scanning uses IEEE 802.11 Probe Request frames to solicit Probe Response frames from access points. This is the **standard WiFi discovery mechanism** used by every WiFi device in existence.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      PROBE REQUEST/RESPONSE FLOW                          │
│                                                                           │
│    NEXUS Device                                    Access Point           │
│         │                                              │                  │
│         │  ──────[ Probe Request (SSID: *) ]─────────► │                  │
│         │                (Broadcast)                   │                  │
│         │                                              │                  │
│         │  ◄─────[ Probe Response (SSID: "Home") ]──── │                  │
│         │                (Unicast)                     │                  │
│         │                                              │                  │
│         │  ──────[ Probe Request (SSID: "Work") ]────► │                  │
│         │                (Directed)                    │                  │
│         │                                              │  (if SSID="Work")│
│         │  ◄─────[ Probe Response (SSID: "Work") ]──── │                  │
│         │                                              │                  │
│         │                                              │                  │
│    ┌────┴────┐                                    ┌────┴────┐             │
│    │ NEXUS   │  NO AUTHENTICATION                │   AP    │             │
│    │ Device  │  NO ASSOCIATION                   │         │             │
│    │         │  NO DATA EXCHANGE                 │         │             │
│    └─────────┘                                   └─────────┘             │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Legal Justification

| Aspect | Justification |
|--------|---------------|
| **Standard Protocol** | IEEE 802.11-2020 §11.1.4.3 defines probe requests as the standard active scanning mechanism |
| **Universal Usage** | Every smartphone, laptop, tablet, and IoT device sends probe requests constantly |
| **No Authentication** | Probe requests occur in the unauthenticated, unassociated state |
| **No Network Access** | Zero network resources are consumed beyond the standard discovery process |
| **FCC/ETSI Compliant** | Operating within licensed ISM bands using standard management frames |
| **No CFAA Violation** | No "access" to any computer system occurs—only public beacon solicitation |

#### Technical Behavior

```python
class ProbeEngine:
    """
    Standards-compliant probe request engine.
    
    Modes:
    - BROADCAST: Wildcard SSID probe (discovers all responsive APs)
    - DIRECTED: Specific SSID probe (solicits response from hidden APs)
    - TARGETED: Specific BSSID probe (refreshes specific AP information)
    """
    
    # Safety limits (configurable, defaults are conservative)
    MAX_PROBES_PER_SECOND = 2        # Well below device norm (~10/sec)
    MAX_PROBES_PER_CHANNEL = 3       # Per channel hop
    INTER_PROBE_DELAY_MS = 500       # Minimum delay between probes
    BURST_COOLDOWN_SEC = 5           # Cooldown after probe burst
    
    # Frame configuration
    USE_RANDOMIZED_MAC = False       # Option for privacy (default: real MAC)
    INCLUDE_HT_CAPABILITIES = True   # Include 802.11n capabilities
    INCLUDE_VHT_CAPABILITIES = True  # Include 802.11ac capabilities
    INCLUDE_SUPPORTED_RATES = True   # Include supported rates IE
```

##### Probe Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Broadcast Probe** | SSID field is null (wildcard) | Discover all APs responding to probes |
| **Directed Probe** | SSID field contains specific name | Reveal hidden networks, refresh AP info |
| **Capability Probe** | Includes HT/VHT capability IEs | Query AP for capability details |
| **Targeted Refresh** | Directed at specific BSSID | Force AP to send fresh probe response |

---

### 3.2 Channel Sweeping

#### Description

Channel sweeping systematically samples each WiFi channel to measure occupancy, noise floor, and airtime utilization—purely through passive observation with optional probe stimulation.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         CHANNEL SWEEP PROCESS                             │
│                                                                           │
│   2.4 GHz Band                           5 GHz Band                       │
│   ┌─────────────────────┐                ┌─────────────────────────────┐ │
│   │ Ch 1  ███████░░░ 70%│                │ Ch 36  ██░░░░░░░░░░ 20%     │ │
│   │ Ch 2  ████░░░░░░ 40%│                │ Ch 40  ███░░░░░░░░░ 30%     │ │
│   │ Ch 3  ██████░░░░ 60%│                │ Ch 44  █░░░░░░░░░░░ 10%     │ │
│   │ Ch 4  ███░░░░░░░ 30%│                │ Ch 48  ████░░░░░░░░ 40%     │ │
│   │ Ch 5  █████░░░░░ 50%│                │ Ch 52  DFS ─────────────    │ │
│   │ Ch 6  █████████░ 90%│                │ Ch 56  DFS ─────────────    │ │
│   │ Ch 7  ██████░░░░ 60%│                │ Ch 60  DFS ─────────────    │ │
│   │ Ch 8  ████░░░░░░ 40%│                │ Ch 64  DFS ─────────────    │ │
│   │ Ch 9  ███░░░░░░░ 30%│                │ ...                         │ │
│   │ Ch 10 ████░░░░░░ 40%│                │ Ch 149 █████░░░░░░░ 50%     │ │
│   │ Ch 11 ████████░░ 80%│                │ Ch 153 ██░░░░░░░░░░ 20%     │ │
│   │ Ch 12 █░░░░░░░░░ 10%│                │ Ch 157 ███░░░░░░░░░ 30%     │ │
│   │ Ch 13 █░░░░░░░░░ 10%│                │ Ch 161 ████████░░░░ 80%     │ │
│   │ Ch 14 (JP only)     │                │ Ch 165 ██████░░░░░░ 60%     │ │
│   └─────────────────────┘                └─────────────────────────────┘ │
│                                                                           │
│   Legend: █ = Occupied airtime   ░ = Free airtime   DFS = Radar detect  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Legal Justification

| Aspect | Justification |
|--------|---------------|
| **Passive Observation** | Noise floor and airtime are measured through passive reception only |
| **Standard Capability** | All WiFi chips support channel switching; this is normal operation |
| **No Transmission Required** | Core measurements are purely passive (listen-only) |
| **Probe Stimulation (Optional)** | If probes are sent, they're standard discovery probes |
| **No Interference** | Changing channels is instantaneous and doesn't affect other devices |

#### Technical Behavior

```python
class ChannelSurvey:
    """
    Channel quality measurement through passive observation.
    
    Metrics collected per channel:
    - AP count (from beacons)
    - Noise floor (dBm, from radio)
    - Airtime utilization (% busy)
    - Congestion score (composite)
    - Interference sources (count)
    """
    
    # Survey configuration
    DWELL_TIME_MS = 200              # Time on each channel
    SAMPLES_PER_CHANNEL = 5          # Measurements per dwell
    FULL_SWEEP_CHANNELS_24 = [1, 6, 11]  # 2.4 GHz non-overlapping
    FULL_SWEEP_CHANNELS_5 = [36, 40, 44, 48, 149, 153, 157, 161, 165]
    
    # DFS channel handling
    SKIP_DFS_CHANNELS = True         # Skip 52-144 by default (radar)
    DFS_LISTEN_ONLY = True           # Never transmit on DFS channels
    
    # Metrics
    def measure_channel(self, channel: int) -> ChannelMetrics:
        """
        Measure channel quality.
        
        Returns:
            ChannelMetrics with:
            - noise_floor_dbm: Background noise level
            - beacon_count: APs detected
            - probe_response_count: Probe responses seen
            - airtime_busy_percent: Estimated busy time
            - congestion_score: 0-100 composite score
        """
```

##### Measurements

| Metric | Method | Data Source |
|--------|--------|-------------|
| **Noise Floor** | Radio hardware reading | NIC driver (passive) |
| **AP Count** | Beacon frame counting | Passive reception |
| **Airtime Usage** | Frame duration summation | Passive reception |
| **Congestion Score** | Weighted combination | Calculated |
| **Channel Overlap** | RSSI from adjacent channels | Passive reception |

---

### 3.3 Information Element (IE) Requests

#### Description

Information Elements are tagged data fields in WiFi management frames. EASM harvests IEs from beacons and probe responses to extract detailed AP capabilities.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INFORMATION ELEMENT STRUCTURE                          │
│                                                                           │
│   Beacon Frame                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐│
│   │ Frame │ Timestamp │ Beacon │ Capability │         IEs              ││
│   │ Header│  (8B)     │Interval│   Info     │                          ││
│   └───────┴───────────┴────────┴────────────┴──────────────────────────┘│
│                                                   │                       │
│                                                   ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────┐│
│   │                    INFORMATION ELEMENTS                             ││
│   │                                                                     ││
│   │   ID=0   SSID                    "MyNetwork"                       ││
│   │   ID=1   Supported Rates         1, 2, 5.5, 11, 6, 9, 12, 18 Mbps  ││
│   │   ID=3   DS Parameter Set        Channel 6                          ││
│   │   ID=5   TIM                     Traffic Indication Map             ││
│   │   ID=42  ERP Information         802.11g parameters                 ││
│   │   ID=45  HT Capabilities         802.11n (40MHz, SGI, 2x2 MIMO)    ││
│   │   ID=48  RSN Information         WPA2-PSK, CCMP cipher              ││
│   │   ID=61  HT Operation            802.11n operating params           ││
│   │   ID=127 Extended Capabilities   BSS transition, proxy ARP, etc.   ││
│   │   ID=191 VHT Capabilities        802.11ac (80MHz, 3x3, 256-QAM)    ││
│   │   ID=192 VHT Operation           802.11ac operating params          ││
│   │   ID=221 Vendor Specific         WPS, WMM, Microsoft, Apple, etc.  ││
│   │   ID=255 Extension               HE Capabilities (WiFi 6)           ││
│   │                                                                     ││
│   └─────────────────────────────────────────────────────────────────────┘│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Legal Justification

| Aspect | Justification |
|--------|---------------|
| **Public Broadcast** | IEs are broadcast in every beacon (public information) |
| **No Decryption** | IEs are in unencrypted management frames |
| **Standard Parsing** | Every WiFi client parses IEs to determine compatibility |
| **Probe Response** | Probe responses contain identical IEs to beacons |
| **No Access** | Reading public broadcasts is not "access" under any law |

#### Technical Behavior

```python
class IEParser:
    """
    IEEE 802.11 Information Element parser and harvester.
    
    Extracts and interprets all standard and vendor-specific IEs
    from beacon and probe response frames.
    """
    
    # Standard IEs of interest
    PARSE_IES = {
        0: 'ssid',
        1: 'supported_rates',
        3: 'ds_parameter_set',
        7: 'country',
        32: 'power_constraint',
        42: 'erp_info',
        45: 'ht_capabilities',
        48: 'rsn',              # Security suite
        50: 'extended_rates',
        61: 'ht_operation',
        127: 'extended_capabilities',
        191: 'vht_capabilities',
        192: 'vht_operation',
        221: 'vendor_specific',
        255: 'extension',       # HE (WiFi 6)
    }
    
    # Vendor-specific OUIs
    VENDOR_OUIS = {
        '00:50:f2:01': 'wpa1',           # Microsoft WPA
        '00:50:f2:02': 'wmm',            # WiFi Multimedia
        '00:50:f2:04': 'wps',            # WiFi Protected Setup
        '00:10:18': 'broadcom',
        '00:17:f2': 'apple',
        '00:0c:e7': 'mediatek',
        '00:03:7f': 'atheros',
    }
    
    def parse_frame(self, frame: bytes) -> IECollection:
        """Parse all IEs from a management frame."""
        
    def get_wifi_generation(self, ies: IECollection) -> int:
        """Determine WiFi generation (4/5/6/6E) from capabilities."""
        
    def get_security_suite(self, ies: IECollection) -> SecuritySuite:
        """Extract full security configuration."""
```

##### Extracted Intelligence

| IE Type | Intelligence Extracted |
|---------|----------------------|
| **HT Capabilities** | 802.11n support, channel width, MIMO streams, SGI |
| **VHT Capabilities** | 802.11ac support, 80/160MHz, MU-MIMO, beamforming |
| **HE Capabilities** | 802.11ax (WiFi 6), OFDMA, BSS coloring, TWT |
| **RSN** | Encryption (CCMP/GCMP), auth (PSK/SAE/802.1X), PMF |
| **Vendor Specific** | WPS state, WMM, manufacturer extensions |
| **Extended Caps** | BSS transition, proxy ARP, interworking |

---

### 3.4 Device Fingerprinting (Active)

#### Description

Active fingerprinting enhances passive OUI-based identification by analyzing probe request patterns, timing characteristics, and response behaviors to classify devices with higher confidence.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEVICE FINGERPRINTING PIPELINE                         │
│                                                                           │
│   ┌──────────────────┐                                                    │
│   │  Raw MAC Address │                                                    │
│   │  AA:BB:CC:DD:EE:FF│                                                   │
│   └────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                        OUI LOOKUP                                 │   │
│   │   ┌────────────────┐   ┌────────────────┐   ┌─────────────────┐  │   │
│   │   │ OUI: AA:BB:CC  │──►│ Vendor: TP-Link│──►│ Type: Consumer  │  │   │
│   │   │ (First 3 bytes)│   │ 70% confidence │   │ Router/IoT      │  │   │
│   │   └────────────────┘   └────────────────┘   └─────────────────┘  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│            │                                                              │
│            ▼                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                   PROBE PATTERN ANALYSIS                          │   │
│   │                                                                   │   │
│   │   Probe SSID List         Timing Pattern        Channel Sequence │   │
│   │   ├─ "AndroidAP"          ├─ 100ms burst        ├─ 1, 6, 11      │   │
│   │   ├─ "DIRECT-xx"          ├─ 2s quiet           ├─ then 36-165   │   │
│   │   └─ "MyHomeWiFi"         └─ repeat             └─ systematic    │   │
│   │                                                                   │   │
│   │   Match: Android smartphone pattern                               │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│            │                                                              │
│            ▼                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                   TIMING SIGNATURE ANALYSIS                       │   │
│   │                                                                   │   │
│   │   Inter-probe timing:  87ms ±5ms (very consistent)               │   │
│   │   Burst pattern:       3 probes, 2s gap                           │   │
│   │   Channel dwell:       120ms per channel                          │   │
│   │                                                                   │   │
│   │   Signature match: Samsung Galaxy series (Android 12+)            │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│            │                                                              │
│            ▼                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                    CLASSIFICATION OUTPUT                          │   │
│   │                                                                   │   │
│   │   Device Type:     Smartphone                                     │   │
│   │   OS Family:       Android 12+                                    │   │
│   │   Manufacturer:    Samsung                                        │   │
│   │   Model Estimate:  Galaxy S21/S22 series                          │   │
│   │   Confidence:      85%                                            │   │
│   │                                                                   │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Legal Justification

| Aspect | Justification |
|--------|---------------|
| **MAC Address** | Broadcast in every frame; designed to be public |
| **OUI Lookup** | IEEE publishes OUI registry publicly |
| **Probe Patterns** | Observing broadcast probes from other devices |
| **Timing Analysis** | Passive observation of frame timing |
| **No Tracking** | Device classification, not individual tracking |

#### Technical Behavior

```python
class ActiveFingerprinter:
    """
    Multi-factor device fingerprinting using active observations.
    
    Combines:
    - OUI vendor lookup (100% offline, OUI-IM)
    - Probe SSID patterns (what networks it seeks)
    - Timing signatures (inter-frame timing)
    - Capability IEs (from device's probe requests)
    - Response behavior (how it responds to our probes)
    """
    
    # Known device signatures (offline database)
    DEVICE_SIGNATURES = {
        'iphone': {
            'oui_patterns': ['apple'],
            'probe_ssids': [''],  # iPhones probe with null SSID
            'timing_ms': (50, 150),
            'ie_patterns': ['apple_ie'],
        },
        'android': {
            'oui_patterns': ['samsung', 'huawei', 'xiaomi', 'oppo'],
            'probe_ssids': ['AndroidAP', 'DIRECT-'],
            'timing_ms': (80, 200),
        },
        'windows_laptop': {
            'probe_ssids': ['MSHOME', 'hpsetup'],
            'timing_ms': (100, 300),
        },
        # ... more signatures
    }
    
    def fingerprint(self, device: DeviceObservation) -> DeviceProfile:
        """
        Generate device fingerprint from observations.
        
        Returns:
            DeviceProfile with:
            - device_type (phone/laptop/router/iot/unknown)
            - os_family (ios/android/windows/linux/unknown)
            - manufacturer
            - model_estimate
            - confidence (0-100)
        """
```

##### Fingerprint Factors

| Factor | Weight | Source |
|--------|--------|--------|
| **OUI Vendor** | 30% | MAC address prefix lookup |
| **Probe SSID List** | 25% | SSIDs the device probes for |
| **Timing Signature** | 20% | Inter-frame timing patterns |
| **Capability IEs** | 15% | HT/VHT/HE capabilities in device's probes |
| **Behavioral Patterns** | 10% | Channel hopping, burst patterns |

---

### 3.5 Hidden SSID Discovery

#### Description

Hidden networks broadcast beacons with empty SSID fields but respond to directed probes with their actual SSID. EASM uses correlation techniques to discover hidden SSIDs legally.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HIDDEN SSID DISCOVERY METHODS                          │
│                                                                           │
│  ═══════════════════════════════════════════════════════════════════════ │
│  METHOD 1: CLIENT OBSERVATION (Passive)                                   │
│  ═══════════════════════════════════════════════════════════════════════ │
│                                                                           │
│    Hidden AP                    Client Device                             │
│    BSSID: AA:BB:CC:DD:EE:FF    MAC: 11:22:33:44:55:66                    │
│         │                            │                                    │
│         │  ◄──[ Probe Req: "SecretNet" ]───  │  Client probes for SSID   │
│         │                                    │                            │
│         │  ───[ Probe Resp: "SecretNet" ]──► │  AP reveals SSID          │
│         │                                    │                            │
│    NEXUS observes this exchange passively and learns:                     │
│    BSSID AA:BB:CC:DD:EE:FF = SSID "SecretNet"                            │
│                                                                           │
│  ═══════════════════════════════════════════════════════════════════════ │
│  METHOD 2: DIRECTED PROBE (Active)                                        │
│  ═══════════════════════════════════════════════════════════════════════ │
│                                                                           │
│    Hidden AP                    NEXUS Device                              │
│    BSSID: AA:BB:CC:DD:EE:FF                                              │
│         │                            │                                    │
│         │  (Beacon: SSID="")         │  We see hidden beacon              │
│         │  ───────────────────────►  │                                    │
│         │                            │                                    │
│    For each common/candidate SSID:   │                                    │
│         │                            │                                    │
│         │  ◄──[ Probe Req: "Guest" ]───  │  Try common SSIDs              │
│         │         (No response)          │                                │
│         │                                │                                │
│         │  ◄──[ Probe Req: "Office" ]──  │                                │
│         │                                │                                │
│         │  ───[ Probe Resp: "Office" ]─► │  MATCH! SSID revealed         │
│         │                                │                                │
│                                                                           │
│  ═══════════════════════════════════════════════════════════════════════ │
│  METHOD 3: CORRELATION ANALYSIS (Passive+)                                │
│  ═══════════════════════════════════════════════════════════════════════ │
│                                                                           │
│    Multiple APs same vendor + similar RSSI + same channel                 │
│    → Likely mesh network → Probe with visible network's SSID              │
│                                                                           │
│    Hidden AP temporal pattern matches known visible AP                     │
│    → Likely same organization → Try organization's known SSIDs            │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Legal Justification

| Aspect | Justification |
|--------|---------------|
| **Standard Mechanism** | Hidden SSIDs are explicitly designed to respond to directed probes |
| **Not Security** | Hidden SSIDs are NOT a security feature (IEEE explicitly states this) |
| **Public Response** | AP voluntarily responds with SSID to any probe request |
| **No Bruteforcing** | We use correlation, common lists, and smart guessing—not exhaustive search |
| **Client Observation** | Passively observing other devices' legitimate probe/response exchanges |

#### Technical Behavior

```python
class HiddenSSIDRevealer:
    """
    Standards-compliant hidden SSID discovery.
    
    Methods:
    1. Passive client observation (watch for probe responses)
    2. Directed probing with intelligent SSID candidates
    3. Correlation with visible networks (mesh detection)
    """
    
    # SSID candidate sources
    COMMON_SSIDS = [
        # Enterprise patterns
        "Guest", "Wireless", "WiFi", "Office", "Corporate",
        # Consumer patterns  
        "Home", "MyNetwork", "NETGEAR", "linksys", "xfinitywifi",
        # IoT patterns
        "SmartHome", "Ring", "Nest", "Alexa",
    ]
    
    # Rate limiting for probes
    MAX_SSID_CANDIDATES = 20         # Max SSIDs to try per hidden AP
    INTER_PROBE_DELAY_MS = 1000      # 1 second between probes
    PROBE_TIMEOUT_MS = 500           # Wait time for response
    
    def discover_passive(self, hidden_bssid: str) -> Optional[str]:
        """
        Attempt passive discovery by observing client probes.
        This is the preferred method as it requires zero transmission.
        """
        
    def discover_active(self, hidden_bssid: str, candidates: List[str]) -> Optional[str]:
        """
        Send directed probes with candidate SSIDs.
        Respects rate limits and stops on first match.
        """
        
    def generate_candidates(self, context: NetworkContext) -> List[str]:
        """
        Generate intelligent SSID candidates based on:
        - Nearby visible networks (same vendor → try same SSID)
        - Common SSID patterns
        - Organization name patterns (if enterprise vendor detected)
        """
```

---

### 3.6 Passive+ Enhancements

#### Description

"Passive+" refers to enhancements that are primarily passive but use minimal, targeted active probes to improve intelligence quality.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     PASSIVE+ ENHANCEMENT MODES                            │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  PROBE-ASSISTED DISTANCE ESTIMATION                                  │ │
│  │                                                                      │ │
│  │  Passive only:  RSSI from beacons → distance estimate (±50%)        │ │
│  │  Passive+:      Probe responses provide:                            │ │
│  │                 - Fresh RSSI samples (not cached)                   │ │
│  │                 - Round-trip timing hints                            │ │
│  │                 - Multiple samples for averaging                     │ │
│  │                 → Improved distance estimate (±30%)                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  AP CAPABILITY REFRESH CYCLES                                        │ │
│  │                                                                      │ │
│  │  Passive only:  Must wait for next beacon (100ms-1s interval)       │ │
│  │  Passive+:      Directed probe → immediate probe response            │ │
│  │                 → Fresh capability data on demand                    │ │
│  │                 → Detect configuration changes faster                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  ENHANCED DEVICE CLASSIFICATION                                      │ │
│  │                                                                      │ │
│  │  Passive only:  OUI + beacon IEs only                               │ │
│  │  Passive+:      Probe response IEs may differ from beacon            │ │
│  │                 → Different capabilities exposed                     │ │
│  │                 → Vendor extensions in probe responses               │ │
│  │                 → Higher confidence classification                   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  EXTENDED IE HARVESTING                                              │ │
│  │                                                                      │ │
│  │  Some APs include different/additional IEs in probe responses:      │ │
│  │  - WPS configuration state (often only in probe response)           │ │
│  │  - Interworking (Hotspot 2.0) details                               │ │
│  │  - Vendor diagnostic information                                     │ │
│  │                                                                      │ │
│  │  Passive+ harvests these for complete capability picture            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Integration Specifications

### 4.1 Radar Integration

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        RADAR VIEW INTEGRATION                             │
│                                                                           │
│                    ┌───────────────────────────────┐                      │
│                    │                               │                      │
│                    │      EASM STATUS INDICATOR    │                      │
│                    │     ┌───────────────────┐     │                      │
│                    │     │ ◉ ACTIVE SCAN ON  │     │                      │
│                    │     │   Probes: 12/min  │     │                      │
│                    │     └───────────────────┘     │                      │
│                    │                               │                      │
│        ◎ Hidden    │          RADAR SWEEP         │                      │
│        (revealed)  │              /                │                      │
│                    │             /                 │      ★ Enhanced     │
│     ○ AP          │            ☆                  │      (fresh probe)  │
│                    │           /    ○              │                      │
│                    │          /                    │                      │
│                    │    ○────☆────────○           │                      │
│                    │          \       ◎           │                      │
│                    │           \                   │                      │
│                    │            \                  │                      │
│                    │             ○                 │                      │
│                    │                               │                      │
│                    │     Legend:                   │                      │
│                    │     ○ Passive only           │                      │
│                    │     ☆ Active enhanced        │                      │
│                    │     ◎ Hidden revealed        │                      │
│                    │     ★ Fresh probe response   │                      │
│                    │                               │                      │
│                    └───────────────────────────────┘                      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Radar Data Flow

```python
class EASMRadarIntegration:
    """EASM integration with RadarView."""
    
    def get_enhanced_blips(self, networks: List[Network]) -> List[NetworkBlip]:
        """
        Enhance network blips with EASM data.
        
        Enhancements:
        - Improved distance estimate from probe RSSI averaging
        - Additional capability icons (WiFi 6, WPA3, etc.)
        - Hidden SSID revealed indicator
        - Freshness indicator (time since last probe response)
        """
        
    def get_status_overlay(self) -> EASMStatus:
        """
        Return EASM status for radar overlay display.
        
        Shows:
        - Mode active/inactive
        - Probe rate (probes/minute)
        - Hidden networks revealed count
        - Last active operation
        """
```

### 4.2 Heatmap Integration

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       HEATMAP VIEW INTEGRATION                            │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐│
│   │                    CHANNEL QUALITY HEATMAP                          ││
│   │                                                                     ││
│   │   Channel:  1   2   3   4   5   6   7   8   9  10  11  12  13     ││
│   │            ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐  ││
│   │   APs:     │ 5 │ 2 │ 1 │ 0 │ 2 │ 8 │ 3 │ 1 │ 0 │ 1 │ 6 │ 0 │ 0 │  ││
│   │            ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤  ││
│   │   Quality: │███│██░│█░░│░░░│██░│███│██░│█░░│░░░│█░░│███│░░░│░░░│  ││
│   │            │ D │ C │ B │ A │ C │ F │ C │ B │ A │ B │ D │ A │ A │  ││
│   │            └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘  ││
│   │                                                                     ││
│   │   Legend: ░ = Excellent (A)  █ = Good (B)  ██ = Fair (C)           ││
│   │           ███ = Congested (D)  ████ = Severe (F)                    ││
│   │                                                                     ││
│   │   Recommendation: Use Channel 4, 9, 12, or 13                       ││
│   │                                                                     ││
│   └─────────────────────────────────────────────────────────────────────┘│
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐│
│   │                    EASM METRICS OVERLAY                             ││
│   │                                                                     ││
│   │   Noise Floor:     -95 dBm (excellent)                              ││
│   │   Airtime Usage:   45% (moderate)                                   ││
│   │   Interference:    3 sources detected                               ││
│   │   Hidden Networks: 2 revealed, 1 pending                            ││
│   │                                                                     ││
│   └─────────────────────────────────────────────────────────────────────┘│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Passive Intelligence Core (PIC) Integration

```python
class EASMPICIntegration:
    """
    EASM integration with Passive Intelligence Core.
    
    EASM provides enhanced data to PIC:
    - Fresh RSSI samples for distance estimation
    - IE data for capability profiling
    - Hidden SSID mappings
    - Device fingerprints
    """
    
    def update_pic_intelligence(self, pic: PassiveIntelligenceCore):
        """Push EASM intelligence updates to PIC."""
        
        # Distance estimation enhancement
        pic.update_distance_estimate(
            bssid=self.target_bssid,
            rssi_samples=self.probe_rssi_samples,  # Fresh probed samples
            sample_source='active_probe'
        )
        
        # Capability update
        pic.update_capabilities(
            bssid=self.target_bssid,
            wifi_caps=self.parsed_capabilities,
            source='probe_response_ie'
        )
        
        # Hidden SSID reveal
        if self.revealed_ssid:
            pic.reveal_hidden_ssid(
                bssid=self.target_bssid,
                ssid=self.revealed_ssid,
                method='directed_probe'
            )
        
        # Device fingerprint
        pic.update_device_profile(
            bssid=self.target_bssid,
            profile=self.device_fingerprint,
            confidence=self.fingerprint_confidence
        )
```

### 4.4 Unified World Model (UWM-X) Integration

```python
class EASMWorldModelIntegration:
    """
    EASM integration with Unified World Model.
    
    EASM enhances world model with:
    - Confirmed relationships (mesh discovery via probing)
    - Environment context (channel survey data)
    - Temporal signatures (probe response timing)
    """
    
    def update_world_model(self, uwm: UnifiedWorldModel):
        """Push EASM intelligence to UWM-X."""
        
        # Channel environment context
        uwm.update_environment_context(
            channel=self.surveyed_channel,
            noise_floor_dbm=self.noise_floor,
            airtime_percent=self.airtime_usage,
            ap_count=self.ap_count,
            congestion_score=self.congestion_score
        )
        
        # Relationship confirmation
        # If directed probe to hidden AP with visible AP's SSID succeeds,
        # we've confirmed mesh membership
        if self.mesh_confirmed:
            uwm.add_relationship_edge(
                node_a=self.hidden_bssid,
                node_b=self.visible_bssid,
                edge_type=EdgeType.MESH_PEER,
                confidence=90,
                source='easm_probe_confirm'
            )
        
        # Temporal signature update
        uwm.update_temporal_signature(
            bssid=self.target_bssid,
            probe_response_time_ms=self.response_latency,
            source='active_probe'
        )
```

### 4.5 Threat Detection Integration

```python
class EASMThreatIntegration:
    """
    EASM integration with threat detection.
    
    EASM enhances threat detection with:
    - Probe response anomalies (unexpected responders)
    - Hidden network risk assessment
    - Capability mismatches (beacon vs probe response)
    """
    
    def check_probe_anomalies(self) -> List[Threat]:
        """
        Detect anomalies from probe responses.
        
        Anomalies:
        - Unexpected BSSID responding to probe (possible evil twin)
        - Capability mismatch between beacon and probe response
        - Multiple APs responding with same SSID (rogue detection)
        - Response timing anomalies (replay/injection detection)
        """
        
    def assess_hidden_network_risk(self, hidden: HiddenNetworkProfile) -> RiskAssessment:
        """
        Assess risk of revealed hidden network.
        
        Risk factors:
        - Hidden + WPA2-PSK + default vendor SSID = possible misconfiguration
        - Hidden + enterprise OUI + no enterprise auth = suspicious
        - Hidden + consumer OUI + near enterprise cluster = possible rogue
        """
```

---

## 5. UI Integration (Pip-Boy Skin)

### 5.1 EASM Control Panel

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  ╔══════════════════════════════════════════════════════════════════════╗│
│  ║  ░░▒▒▓▓ VAULT-TEC ACTIVE SCANNING MODULE v1.0 ▓▓▒▒░░                 ║│
│  ║                                                                      ║│
│  ║  ┌────────────────────────────────────────────────────────────────┐ ║│
│  ║  │  STATUS: ■ ACTIVE                    MODE: STANDARD            │ ║│
│  ║  │                                                                │ ║│
│  ║  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │ ║│
│  ║  │  │ PROBES SENT     │  │ RESPONSES RX    │  │ HIDDEN FOUND   │ │ ║│
│  ║  │  │      127        │  │      98         │  │      3         │ │ ║│
│  ║  │  │   2.1/min       │  │   77% rate      │  │   revealed     │ │ ║│
│  ║  │  └─────────────────┘  └─────────────────┘  └────────────────┘ │ ║│
│  ║  │                                                                │ ║│
│  ║  │  LAST OPERATION: Channel 6 sweep complete                      │ ║│
│  ║  │  NEXT SCHEDULED: Hidden SSID probe in 5s                       │ ║│
│  ║  │                                                                │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ║  ┌─ ACTIVE FEATURES ──────────────────────────────────────────────┐ ║│
│  ║  │                                                                │ ║│
│  ║  │  [■] Directed Probes        [■] Channel Sweeping              │ ║│
│  ║  │  [■] IE Harvesting          [■] Device Fingerprinting         │ ║│
│  ║  │  [■] Hidden Discovery       [□] Low-Power Mode                │ ║│
│  ║  │                                                                │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ║  ┌─ SAFETY STATUS ────────────────────────────────────────────────┐ ║│
│  ║  │                                                                │ ║│
│  ║  │  ✓ Rate limiter: 2 probes/sec (within safe limits)           │ ║│
│  ║  │  ✓ No auth frames transmitted                                 │ ║│
│  ║  │  ✓ No association frames transmitted                          │ ║│
│  ║  │  ✓ DFS channels: listen-only mode                             │ ║│
│  ║  │                                                                │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ║        [ TOGGLE EASM ]     [ CONFIGURE ]     [ VIEW LOG ]           ║│
│  ║                                                                      ║│
│  ╚══════════════════════════════════════════════════════════════════════╝│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Hidden Network Panel

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  ╔══════════════════════════════════════════════════════════════════════╗│
│  ║  ░░▒▒▓▓ HIDDEN NETWORK INTELLIGENCE ▓▓▒▒░░                          ║│
│  ║                                                                      ║│
│  ║  ┌─ REVEALED NETWORKS ────────────────────────────────────────────┐ ║│
│  ║  │                                                                │ ║│
│  ║  │  BSSID              REVEALED SSID      METHOD    CONFIDENCE   │ ║│
│  ║  │  ═══════════════════════════════════════════════════════════  │ ║│
│  ║  │  AA:BB:CC:11:22:33  "CorpGuest"       Directed     95%       │ ║│
│  ║  │  AA:BB:CC:11:22:44  "CorpInternal"   Client Obs   100%      │ ║│
│  ║  │  DE:AD:BE:EF:00:01  "BackhaulMesh"   Correlation  85%       │ ║│
│  ║  │                                                                │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ║  ┌─ PENDING DISCOVERY ────────────────────────────────────────────┐ ║│
│  ║  │                                                                │ ║│
│  ║  │  BSSID              VENDOR        CANDIDATES TRIED  STATUS    │ ║│
│  ║  │  ═══════════════════════════════════════════════════════════  │ ║│
│  ║  │  DE:AD:BE:EF:00:02  Ubiquiti         5/20          Probing   │ ║│
│  ║  │  11:22:33:44:55:66  TP-Link          0/20          Queued    │ ║│
│  ║  │                                                                │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ╚══════════════════════════════════════════════════════════════════════╝│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Channel Survey Panel

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  ╔══════════════════════════════════════════════════════════════════════╗│
│  ║  ░░▒▒▓▓ RF SPECTRUM ANALYSIS ▓▓▒▒░░                                 ║│
│  ║                                                                      ║│
│  ║  2.4 GHz BAND                                                        ║│
│  ║  ┌────────────────────────────────────────────────────────────────┐ ║│
│  ║  │ CH  APs  NOISE   AIRTIME  QUALITY  RECOMMENDATION              │ ║│
│  ║  │ ══  ═══  ══════  ═══════  ═══════  ══════════════              │ ║│
│  ║  │  1   5   -92dBm    70%      ██░░    Congested                  │ ║│
│  ║  │  6   8   -90dBm    85%      ███░    Avoid                      │ ║│
│  ║  │ 11   4   -93dBm    55%      █░░░    Acceptable                 │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ║  5 GHz BAND                                                          ║│
│  ║  ┌────────────────────────────────────────────────────────────────┐ ║│
│  ║  │ CH   APs  NOISE   AIRTIME  QUALITY  RECOMMENDATION             │ ║│
│  ║  │ ═══  ═══  ══════  ═══════  ═══════  ══════════════             │ ║│
│  ║  │  36   2   -95dBm    20%      ░░░░    ★ RECOMMENDED             │ ║│
│  ║  │  40   1   -96dBm    15%      ░░░░    ★ RECOMMENDED             │ ║│
│  ║  │  44   3   -94dBm    35%      ░░░░    Good                      │ ║│
│  ║  │ 149   6   -91dBm    60%      ██░░    Moderate                  │ ║│
│  ║  │ 153   4   -93dBm    45%      █░░░    Acceptable                │ ║│
│  ║  └────────────────────────────────────────────────────────────────┘ ║│
│  ║                                                                      ║│
│  ║        [ START SURVEY ]    [ EXPORT DATA ]    [ REFRESH ]           ║│
│  ║                                                                      ║│
│  ╚══════════════════════════════════════════════════════════════════════╝│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Toggle Design

### 6.1 Visibility Levels

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        EASM VISIBILITY LEVELS                             │
│                                                                           │
│  ╔═══════════════════════════════════════════════════════════════════╗   │
│  ║  LEVEL 0: HIDDEN (Default)                                        ║   │
│  ║                                                                   ║   │
│  ║  - EASM module is completely invisible in UI                      ║   │
│  ║  - No menu entries, no settings, no indicators                    ║   │
│  ║  - Module code exists but is never loaded                         ║   │
│  ║  - Zero CPU/memory overhead                                       ║   │
│  ║                                                                   ║   │
│  ║  Enable with: Settings → Developer → Enable Active Scanning       ║   │
│  ║               (requires typing "I UNDERSTAND THE IMPLICATIONS")   ║   │
│  ╚═══════════════════════════════════════════════════════════════════╝   │
│                                                                           │
│  ╔═══════════════════════════════════════════════════════════════════╗   │
│  ║  LEVEL 1: VISIBLE BUT DISABLED                                    ║   │
│  ║                                                                   ║   │
│  ║  - EASM appears in Advanced menu (grayed out toggle)              ║   │
│  ║  - Hovering shows explanation and legal notice                    ║   │
│  ║  - Click to enable shows confirmation dialog                      ║   │
│  ║  - Module is loaded but inactive (minimal overhead)               ║   │
│  ║                                                                   ║   │
│  ╚═══════════════════════════════════════════════════════════════════╝   │
│                                                                           │
│  ╔═══════════════════════════════════════════════════════════════════╗   │
│  ║  LEVEL 2: ENABLED - STANDARD MODE                                 ║   │
│  ║                                                                   ║   │
│  ║  - EASM is active with conservative settings                      ║   │
│  ║  - Low probe rate (1/sec), basic features only                    ║   │
│  ║  - Status indicator in radar view                                 ║   │
│  ║  - All safety limits enforced                                     ║   │
│  ║                                                                   ║   │
│  ╚═══════════════════════════════════════════════════════════════════╝   │
│                                                                           │
│  ╔═══════════════════════════════════════════════════════════════════╗   │
│  ║  LEVEL 3: ENABLED - ADVANCED MODE (Developer)                     ║   │
│  ║                                                                   ║   │
│  ║  - All EASM features available                                    ║   │
│  ║  - Configurable probe rates (still within safe limits)            ║   │
│  ║  - Full channel survey controls                                   ║   │
│  ║  - Hidden SSID dictionary editing                                 ║   │
│  ║  - Detailed logging and statistics                                ║   │
│  ║                                                                   ║   │
│  ╚═══════════════════════════════════════════════════════════════════╝   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Activation Flow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        EASM ACTIVATION FLOW                               │
│                                                                           │
│   USER ACTION                         SYSTEM RESPONSE                     │
│   ═══════════                         ═══════════════                     │
│                                                                           │
│   1. Open Settings                                                        │
│      └──► Settings panel opens                                            │
│                                                                           │
│   2. Click "Developer Options"                                            │
│      └──► Hidden until user has used app for 24+ hours                   │
│          (prevents accidental discovery)                                  │
│                                                                           │
│   3. Toggle "Enable Active Scanning"                                      │
│      └──► Confirmation dialog appears:                                    │
│                                                                           │
│          ┌─────────────────────────────────────────────────────────┐     │
│          │                                                         │     │
│          │   ⚠ ENABLE ENHANCED ACTIVE SCANNING?                    │     │
│          │                                                         │     │
│          │   This mode will send probe request frames to           │     │
│          │   discover WiFi networks. This is a standard            │     │
│          │   WiFi operation performed by all devices.              │     │
│          │                                                         │     │
│          │   ✓ 100% legal (standard IEEE 802.11)                  │     │
│          │   ✓ Does NOT connect to any network                    │     │
│          │   ✓ Does NOT access any data                           │     │
│          │   ✓ Does NOT interfere with other devices              │     │
│          │                                                         │     │
│          │   Type "ENABLE ACTIVE SCAN" to confirm:                 │     │
│          │   ┌───────────────────────────────────────────────┐    │     │
│          │   │                                               │    │     │
│          │   └───────────────────────────────────────────────┘    │     │
│          │                                                         │     │
│          │           [ Cancel ]        [ Enable ]                  │     │
│          │                                                         │     │
│          └─────────────────────────────────────────────────────────┘     │
│                                                                           │
│   4. Type confirmation and click Enable                                   │
│      └──► EASM module loads                                              │
│          └──► EASM tab appears in main UI                                │
│          └──► Radar shows EASM status indicator                          │
│                                                                           │
│   5. Toggle EASM on/off in EASM panel                                     │
│      └──► Instant enable/disable without re-confirmation                 │
│          (confirmation only required once per session)                    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Configuration Interface

```python
@dataclass
class EASMConfig:
    """EASM configuration with safe defaults."""
    
    # Master toggle
    enabled: bool = False
    visibility_level: int = 0  # 0=hidden, 1=visible, 2=standard, 3=advanced
    
    # Feature toggles
    directed_probes_enabled: bool = True
    channel_sweep_enabled: bool = True
    ie_harvesting_enabled: bool = True
    device_fingerprinting_enabled: bool = True
    hidden_discovery_enabled: bool = True
    passive_plus_enabled: bool = True
    
    # Rate limits (cannot exceed hard maximums)
    probe_rate_per_second: float = 1.0   # Max: 5.0
    channel_dwell_time_ms: int = 200     # Min: 100, Max: 1000
    hidden_probe_delay_ms: int = 1000    # Min: 500
    
    # Safety settings (cannot be disabled)
    rate_limiter_enabled: bool = True    # Always True
    legal_guard_enabled: bool = True     # Always True
    frame_validator_enabled: bool = True # Always True
    dfs_listen_only: bool = True         # Always True
    
    # Privacy
    use_randomized_mac: bool = False     # Optional
    
    # Persistence
    remember_enabled_state: bool = False  # Start disabled each session
```

---

## 7. Safety Rules

### 7.1 Safety Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          SAFETY ARCHITECTURE                              │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        EASM ENGINE                                   │ │
│  │                            │                                         │ │
│  │                            ▼                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │                    SAFETY LAYER                              │   │ │
│  │  │                                                              │   │ │
│  │  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │ │
│  │  │   │ Rate Limiter │  │ Legal Guard  │  │ Frame Valid. │     │   │ │
│  │  │   │              │  │              │  │              │     │   │ │
│  │  │   │ • Max 5/sec  │  │ • No auth    │  │ • Valid type │     │   │ │
│  │  │   │ • Burst cool │  │ • No assoc   │  │ • Valid IE   │     │   │ │
│  │  │   │ • Per-AP lim │  │ • No deauth  │  │ • Valid MAC  │     │   │ │
│  │  │   │ • Per-ch lim │  │ • No data    │  │ • No inject  │     │   │ │
│  │  │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │   │ │
│  │  │          │                 │                 │              │   │ │
│  │  │          └─────────────────┼─────────────────┘              │   │ │
│  │  │                            │                                │   │ │
│  │  │                    ALL MUST PASS                            │   │ │
│  │  │                            │                                │   │ │
│  │  └────────────────────────────┼────────────────────────────────┘   │ │
│  │                               │                                     │ │
│  │                               ▼                                     │ │
│  │                      ┌───────────────┐                              │ │
│  │                      │ TX QUEUE      │                              │ │
│  │                      │ (Validated)   │                              │ │
│  │                      └───────┬───────┘                              │ │
│  │                              │                                      │ │
│  │                              ▼                                      │ │
│  │                      ┌───────────────┐                              │ │
│  │                      │ RADIO DRIVER  │                              │ │
│  │                      └───────────────┘                              │ │
│  │                                                                     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Safety Rules Table

| Rule ID | Rule Name | Description | Enforcement |
|---------|-----------|-------------|-------------|
| **S001** | No Authentication | Never send Authentication frames | Frame type whitelist |
| **S002** | No Association | Never send Association frames | Frame type whitelist |
| **S003** | No Deauthentication | Never send Deauth frames | Frame type whitelist |
| **S004** | No Disassociation | Never send Disassoc frames | Frame type whitelist |
| **S005** | No Data Frames | Never send Data frames | Frame type whitelist |
| **S006** | No Action Frames | Never send Action frames | Frame type whitelist |
| **S007** | Probe Only | Only Probe Request frames allowed | Frame type whitelist |
| **S008** | Rate Limit Global | Max 5 probes/second globally | Token bucket |
| **S009** | Rate Limit Per-AP | Max 1 probe/10sec per BSSID | Per-target tracking |
| **S010** | Rate Limit Per-Channel | Max 3 probes per channel visit | Channel state |
| **S011** | Burst Cooldown | 5 second cooldown after 10 probes | Burst detector |
| **S012** | DFS Listen-Only | Never transmit on DFS channels | Channel whitelist |
| **S013** | Valid MAC Source | Source MAC must be real or clearly random | MAC validation |
| **S014** | No MAC Spoofing | Cannot use another device's MAC | MAC validation |
| **S015** | Valid Frame Format | All frames must be valid IEEE 802.11 | Frame parser |
| **S016** | IE Sanity | IEs in probes must be valid | IE validator |
| **S017** | No Injection | Cannot inject into existing conversations | Frame isolation |
| **S018** | No Replay | Cannot replay captured frames | Sequence tracking |

### 7.3 Safety Implementation

```python
class SafetyGuard:
    """
    Safety enforcement layer for EASM.
    
    All frame transmissions MUST pass through SafetyGuard.
    Any safety violation immediately blocks the operation and logs an alert.
    """
    
    # Immutable frame type whitelist (ONLY these are ever sent)
    ALLOWED_FRAME_TYPES = frozenset([
        0x0040,  # Probe Request (subtype 0x04, type 0x00)
    ])
    
    # Immutable channel blacklist (NEVER transmit on these)
    DFS_CHANNELS = frozenset([52, 56, 60, 64, 100, 104, 108, 112, 116, 
                              120, 124, 128, 132, 136, 140, 144])
    
    def validate_frame(self, frame: bytes) -> ValidationResult:
        """
        Validate a frame before transmission.
        
        Returns ValidationResult with:
        - allowed: bool
        - reason: str (if blocked)
        - violations: List[str] (all rule violations)
        """
        violations = []
        
        # S007: Frame type whitelist
        frame_type = self._extract_frame_type(frame)
        if frame_type not in self.ALLOWED_FRAME_TYPES:
            violations.append(f"S007: Frame type {hex(frame_type)} not in whitelist")
        
        # S001-S006: Explicit forbidden frame checks
        if self._is_auth_frame(frame):
            violations.append("S001: Authentication frame forbidden")
        if self._is_assoc_frame(frame):
            violations.append("S002: Association frame forbidden")
        # ... etc
        
        # S008: Global rate limit
        if not self.rate_limiter.acquire():
            violations.append("S008: Global rate limit exceeded")
        
        # S012: DFS channel check
        channel = self._get_target_channel()
        if channel in self.DFS_CHANNELS:
            violations.append(f"S012: DFS channel {channel} is listen-only")
        
        # S013-S014: MAC validation
        src_mac = self._extract_src_mac(frame)
        if not self._is_valid_source_mac(src_mac):
            violations.append("S013/S014: Invalid source MAC")
        
        return ValidationResult(
            allowed=len(violations) == 0,
            reason=violations[0] if violations else None,
            violations=violations
        )
    
    def is_safe_operation(self, operation: EASMOperation) -> bool:
        """High-level operation safety check."""
        # This is called BEFORE building any frames
        
        if operation.type == 'probe_broadcast':
            return self._check_broadcast_limits()
        elif operation.type == 'probe_directed':
            return self._check_directed_limits(operation.target_bssid)
        elif operation.type == 'channel_switch':
            return operation.channel not in self.DFS_CHANNELS
        
        return False  # Unknown operations are forbidden
```

---

## 8. Performance Considerations

### 8.1 Resource Usage

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      EASM RESOURCE FOOTPRINT                              │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  DISABLED (Level 0)                                                  │ │
│  │  • CPU: 0% additional                                                │ │
│  │  • Memory: 0 MB additional (module not loaded)                       │ │
│  │  • Network: 0 bytes/sec                                              │ │
│  │  • Battery: No impact                                                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  ENABLED - IDLE (Module loaded, not actively scanning)               │ │
│  │  • CPU: ~0.1% additional                                             │ │
│  │  • Memory: ~5 MB additional                                          │ │
│  │  • Network: 0 bytes/sec                                              │ │
│  │  • Battery: Minimal impact                                           │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  ENABLED - ACTIVE (Standard mode, 1 probe/sec)                       │ │
│  │  • CPU: ~1-2% additional                                             │ │
│  │  • Memory: ~10-20 MB additional (caches, buffers)                    │ │
│  │  • Network: ~200 bytes/sec TX, ~1 KB/sec RX                         │ │
│  │  • Battery: Low impact (~5% additional drain/hour)                   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  ENABLED - ACTIVE (Advanced mode, 5 probes/sec + channel sweep)      │ │
│  │  • CPU: ~3-5% additional                                             │ │
│  │  • Memory: ~30-50 MB additional                                      │ │
│  │  • Network: ~1 KB/sec TX, ~5 KB/sec RX                              │ │
│  │  • Battery: Moderate impact (~15% additional drain/hour)             │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Optimization Strategies

```python
class EASMPerformanceOptimizer:
    """Performance optimization for EASM operations."""
    
    # Caching
    IE_CACHE_TTL_SEC = 60          # Cache parsed IEs for 60 seconds
    FINGERPRINT_CACHE_TTL_SEC = 300  # Cache fingerprints for 5 minutes
    CHANNEL_SURVEY_CACHE_TTL_SEC = 30  # Cache channel data for 30 seconds
    
    # Batching
    PROBE_BATCH_SIZE = 3           # Send up to 3 probes in one channel dwell
    IE_PARSE_BATCH_SIZE = 10       # Parse up to 10 frames before yield
    
    # Lazy loading
    def load_module_on_demand(self, module_name: str):
        """Load EASM submodules only when needed."""
        if module_name not in self._loaded_modules:
            self._loaded_modules[module_name] = importlib.import_module(
                f'nexus.core.{module_name}'
            )
        return self._loaded_modules[module_name]
    
    # Adaptive rate limiting
    def adjust_rate_for_battery(self, battery_percent: int):
        """Reduce probe rate when battery is low."""
        if battery_percent < 20:
            self.config.probe_rate_per_second = min(
                self.config.probe_rate_per_second, 
                0.5  # Max 1 probe per 2 seconds on low battery
            )
    
    # Background scheduling
    def schedule_low_priority_tasks(self):
        """Run non-urgent tasks during idle periods."""
        # IE parsing, fingerprint calculation, etc.
        # Scheduled when no user interaction for 5+ seconds
```

### 8.3 Platform-Specific Considerations

| Platform | Considerations | Optimizations |
|----------|----------------|---------------|
| **Windows** | Scapy requires Npcap; netsh is fallback | Use native WiFi API when possible |
| **Linux** | Requires monitor mode for some features | Use nl80211 for efficiency |
| **Raspberry Pi** | Limited CPU/memory | Aggressive caching, reduced rates |
| **macOS** | CoreWLAN restrictions | Limited to passive + airport cmd |

---

## 9. Offline & Standards Compliance

### 9.1 Offline Guarantee

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      100% OFFLINE OPERATION                               │
│                                                                           │
│  ╔═══════════════════════════════════════════════════════════════════╗   │
│  ║  EASM REQUIRES NO INTERNET CONNECTION                             ║   │
│  ║                                                                   ║   │
│  ║  All data sources are local:                                      ║   │
│  ║                                                                   ║   │
│  ║  ✓ OUI Database          Bundled offline (IEEE OUI registry)     ║   │
│  ║  ✓ Device Signatures     Bundled offline database                ║   │
│  ║  ✓ Common SSIDs          Bundled offline list                    ║   │
│  ║  ✓ IE Parsing Rules      Hardcoded IEEE 802.11 definitions       ║   │
│  ║  ✓ Fingerprint DB        Bundled offline                         ║   │
│  ║                                                                   ║   │
│  ║  All network activity is LOCAL RF ONLY:                          ║   │
│  ║                                                                   ║   │
│  ║  ✓ Probe Requests        Local RF transmission (WiFi)            ║   │
│  ║  ✓ Probe Responses       Local RF reception (WiFi)               ║   │
│  ║  ✓ Beacon Reception      Local RF reception (WiFi)               ║   │
│  ║                                                                   ║   │
│  ║  ZERO Internet traffic. ZERO cloud dependencies.                  ║   │
│  ║  Works in airplane mode with WiFi enabled.                        ║   │
│  ║  Works in Faraday cages. Works underground.                       ║   │
│  ║                                                                   ║   │
│  ╚═══════════════════════════════════════════════════════════════════╝   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Standards Compliance

| Standard | Compliance | Notes |
|----------|------------|-------|
| **IEEE 802.11-2020** | ✅ Full | Probe requests per §11.1.4.3 |
| **IEEE 802.11ax** | ✅ Full | WiFi 6 IE parsing supported |
| **Wi-Fi Alliance** | ✅ Full | Standard client behavior |
| **FCC Part 15** | ✅ Full | ISM band operation within limits |
| **ETSI EN 300 328** | ✅ Full | EU 2.4 GHz compliance |
| **ETSI EN 301 893** | ✅ Full | EU 5 GHz compliance (with DFS respect) |

### 9.3 Legal Compliance

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      LEGAL COMPLIANCE SUMMARY                             │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  UNITED STATES                                                       │ │
│  │                                                                      │ │
│  │  ✓ Computer Fraud and Abuse Act (CFAA): NO VIOLATION                │ │
│  │    - No "access" to any protected computer                          │ │
│  │    - Probe requests are standard discovery, not "access"            │ │
│  │                                                                      │ │
│  │  ✓ Electronic Communications Privacy Act (ECPA): NO VIOLATION       │ │
│  │    - No interception of communications content                      │ │
│  │    - Management frames are not "communications"                     │ │
│  │                                                                      │ │
│  │  ✓ FCC Regulations: COMPLIANT                                       │ │
│  │    - Operating in ISM bands with standard equipment                 │ │
│  │    - No jamming, no interference                                    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  EUROPEAN UNION                                                      │ │
│  │                                                                      │ │
│  │  ✓ GDPR: COMPLIANT                                                  │ │
│  │    - No personal data collection (MAC addresses are device IDs)     │ │
│  │    - No tracking of individuals                                     │ │
│  │                                                                      │ │
│  │  ✓ Computer Misuse Laws: NO VIOLATION                               │ │
│  │    - No unauthorized access                                         │ │
│  │    - Standard WiFi client behavior                                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  DISCLAIMER                                                          │ │
│  │                                                                      │ │
│  │  This analysis is for educational purposes. Laws vary by            │ │
│  │  jurisdiction. Users are responsible for compliance with local      │ │
│  │  laws. When in doubt, consult a qualified attorney.                 │ │
│  │                                                                      │ │
│  │  NEXUS developers make no warranty regarding legal compliance       │ │
│  │  in any specific jurisdiction.                                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Roadmap

### Phase 1: Core Engine (Week 1-2)
- [ ] `active_scan.py` - Core EASM engine
- [ ] `probe_engine.py` - Probe request transmission
- [ ] `safety/rate_limiter.py` - Rate limiting
- [ ] `safety/legal_guard.py` - Frame type validation
- [ ] `safety/frame_validator.py` - Frame format validation

### Phase 2: Features (Week 3-4)
- [ ] `channel_survey.py` - Channel sweeping and measurement
- [ ] `ie_parser.py` - Information Element parsing
- [ ] `active_fingerprint.py` - Device fingerprinting
- [ ] `hidden_reveal.py` - Hidden SSID discovery

### Phase 3: Integration (Week 5-6)
- [ ] PIC integration
- [ ] UWM-X integration
- [ ] Threat detection integration
- [ ] Radar view integration
- [ ] Heatmap integration

### Phase 4: UI & Polish (Week 7-8)
- [ ] Pip-Boy EASM panel
- [ ] Settings integration
- [ ] Confirmation dialogs
- [ ] Status indicators
- [ ] Documentation

---

## Appendix A: Frame Format Reference

### Probe Request Frame Format

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     PROBE REQUEST FRAME FORMAT                            │
│                     (IEEE 802.11-2020 §9.3.3.9)                          │
│                                                                           │
│  Bytes:  2      2       6         6         6       2      0-N           │
│       ┌─────┬───────┬─────────┬─────────┬─────────┬──────┬─────────────┐ │
│       │Frame│Duration│  DA     │   SA    │  BSSID  │ Seq  │    IEs      │ │
│       │Ctrl │        │(Bcast)  │(Device) │(Bcast)  │ Ctrl │             │ │
│       └─────┴───────┴─────────┴─────────┴─────────┴──────┴─────────────┘ │
│                                                                           │
│  Frame Control: 0x0040 (Probe Request)                                    │
│  DA (Destination): FF:FF:FF:FF:FF:FF (broadcast)                         │
│  SA (Source): Device's real MAC or randomized                            │
│  BSSID: FF:FF:FF:FF:FF:FF (broadcast) or specific AP                     │
│                                                                           │
│  Information Elements (typical):                                          │
│  ┌──────┬────────────────────────────────────────────────────────────┐   │
│  │ ID=0 │ SSID (0-32 bytes, empty for wildcard)                      │   │
│  │ ID=1 │ Supported Rates                                            │   │
│  │ ID=50│ Extended Supported Rates                                   │   │
│  │ ID=45│ HT Capabilities (if 802.11n capable)                       │   │
│  │ ID=191│ VHT Capabilities (if 802.11ac capable)                    │   │
│  │ ID=255│ HE Capabilities (if 802.11ax capable)                     │   │
│  │ ID=221│ Vendor Specific (optional)                                │   │
│  └──────┴────────────────────────────────────────────────────────────┘   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Active Scanning** | WiFi discovery using probe request/response |
| **Beacon** | AP's periodic advertisement frame |
| **BSSID** | AP's MAC address (Basic Service Set ID) |
| **DFS** | Dynamic Frequency Selection (radar avoidance) |
| **EASM** | Enhanced Active Scan Mode (this feature) |
| **HE** | High Efficiency (802.11ax / WiFi 6) |
| **HT** | High Throughput (802.11n / WiFi 4) |
| **IE** | Information Element (tagged data in frames) |
| **OUI** | Organizationally Unique Identifier (MAC prefix) |
| **PIC** | Passive Intelligence Core |
| **Probe Request** | Client's network discovery frame |
| **Probe Response** | AP's reply to probe request |
| **SSID** | Network name (Service Set Identifier) |
| **UWM-X** | Unified World Model Expander |
| **VHT** | Very High Throughput (802.11ac / WiFi 5) |

---

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    END OF ENHANCED ACTIVE SCAN MODE SPECIFICATION             ║
║                                                                               ║
║                         Document Version: 1.0                                 ║
║                         Last Updated: 2026-01-22                              ║
║                         Classification: PUBLIC                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```
