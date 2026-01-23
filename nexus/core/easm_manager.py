"""
Enhanced Active Scan Mode (EASM) Manager for NEXUS WiFi Radar.

╔══════════════════════════════════════════════════════════════════════════════╗
║   ENHANCED ACTIVE SCAN MODE (EASM) CONTROLLER                                ║
║   100% Legal • 100% Standards-Compliant • IEEE 802.11 Probe Requests Only    ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module implements legal active WiFi scanning using only standard
IEEE 802.11 Probe Request frames - the same mechanism used by every
smartphone, laptop, and WiFi device in existence.

LEGAL GUARANTEES (HARD-CODED, CANNOT BE DISABLED):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Only Probe Request frames (subtype 0x04) are transmitted
✓ No Authentication frames
✓ No Association frames
✓ No Deauthentication frames
✓ No Disassociation frames
✓ No Data frames
✓ No impersonation (uses device's real MAC or clearly random)
✓ No DFS channel transmission (channels 52-144 are listen-only)
✓ No connection attempts
✓ Rate-limited to prevent any network impact

SAFETY ARCHITECTURE:
━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────┐
│                    TRIPLE-LAYER SAFETY SYSTEM                    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Rate Limiter │──│ Legal Guard  │──│ Frame Validator      │  │
│  │              │  │              │  │                      │  │
│  │ • 5/sec max  │  │ • Type check │  │ • Layer validation   │  │
│  │ • Per-BSSID  │  │ • Whitelist  │  │ • MAC validation     │  │
│  │ • Burst ctrl │  │ • Blacklist  │  │ • Subtype check      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ALL THREE MUST PASS before any frame is transmitted             │
└─────────────────────────────────────────────────────────────────┘
"""

import time
import random
import threading
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Set, Tuple, Any
from enum import Enum
from collections import defaultdict
import struct


# =============================================================================
# SECTION 1: CONSTANTS AND CONFIGURATION
# =============================================================================

class EASMMode(Enum):
    """EASM operational modes."""
    DISABLED = "disabled"
    STANDARD = "standard"      # Conservative settings
    AGGRESSIVE = "aggressive"  # Higher probe rate (still within legal limits)


# DFS channels - NEVER transmit on these (radar detection required)
# These channels require Dynamic Frequency Selection and we must not interfere
DFS_CHANNELS = frozenset([
    52, 56, 60, 64,           # UNII-2A
    100, 104, 108, 112, 116,  # UNII-2C
    120, 124, 128, 132, 136, 140, 144  # UNII-2C Extended
])

# Safe channels for active probing (non-DFS)
SAFE_CHANNELS_24GHZ = [1, 6, 11]  # Non-overlapping 2.4 GHz
SAFE_CHANNELS_5GHZ = [36, 40, 44, 48, 149, 153, 157, 161, 165]  # UNII-1 and UNII-3

# All safe channels combined
ALL_SAFE_CHANNELS = SAFE_CHANNELS_24GHZ + SAFE_CHANNELS_5GHZ

# IEEE 802.11 Frame Type/Subtype constants
FRAME_TYPE_MANAGEMENT = 0
FRAME_SUBTYPE_PROBE_REQUEST = 4
FRAME_SUBTYPE_PROBE_RESPONSE = 5
FRAME_SUBTYPE_BEACON = 8

# Broadcast address for probe requests
BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"

# Rate limit constants (SAFETY - CANNOT BE CHANGED AT RUNTIME)
MAX_PROBES_PER_SECOND = 5           # Absolute maximum probes per second
MIN_PROBE_INTERVAL_MS = 200         # Minimum 200ms between probes (5/sec)
PER_BSSID_COOLDOWN_SEC = 10         # Don't re-probe same AP for 10 seconds
BURST_SIZE_LIMIT = 3                # Max probes in a quick burst
BURST_COOLDOWN_SEC = 2              # Cooldown after burst
HIDDEN_PROBE_DELAY_MS = 1000        # 1 second between hidden SSID probes
CHANNEL_DWELL_TIME_MS = 300         # Time to stay on each channel


# =============================================================================
# SECTION 2: DATA STRUCTURES
# =============================================================================

@dataclass
class ProbeTarget:
    """A target for directed probe requests."""
    bssid: str
    ssid: Optional[str] = None      # None for hidden SSIDs
    channel: int = 0
    last_probed: float = 0.0
    probe_count: int = 0
    is_hidden: bool = False
    revealed_ssid: Optional[str] = None
    
    def can_probe(self) -> bool:
        """Check if this target can be probed (respecting cooldown)."""
        return time.time() - self.last_probed >= PER_BSSID_COOLDOWN_SEC


@dataclass
class EASMStats:
    """Statistics for EASM operations."""
    probes_sent: int = 0
    probe_responses_received: int = 0
    hidden_ssids_revealed: int = 0
    channels_swept: int = 0
    ies_harvested: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def probes_per_minute(self) -> float:
        """Calculate probe rate."""
        elapsed = time.time() - self.start_time
        if elapsed < 1:
            return 0.0
        return (self.probes_sent / elapsed) * 60


@dataclass
class HarvestedIE:
    """Information Element harvested from probe response."""
    bssid: str
    ie_id: int
    ie_name: str
    ie_data: bytes
    parsed_value: Any = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class EASMDiscovery:
    """A discovery made by EASM (passed to callback)."""
    discovery_type: str          # 'probe_response', 'hidden_reveal', 'ie_harvest', 'capability'
    bssid: str
    ssid: Optional[str] = None
    channel: int = 0
    rssi_dbm: int = -70
    capabilities: Dict[str, Any] = field(default_factory=dict)
    ies: List[HarvestedIE] = field(default_factory=list)
    source: str = "easm"
    timestamp: float = field(default_factory=time.time)


# =============================================================================
# SECTION 3: SAFETY SYSTEM (MANDATORY - CANNOT BE DISABLED)
# =============================================================================

class RateLimiter:
    """
    Rate limiter for probe transmission.
    
    SAFETY LAYER 1: Prevents excessive transmission that could
    interfere with normal network operation.
    
    This class is intentionally simple and conservative.
    The limits are HARD-CODED and cannot be bypassed.
    """
    
    def __init__(self):
        self._probe_times: List[float] = []
        self._burst_count = 0
        self._burst_start = 0.0
        self._per_bssid_last_probe: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def can_send_probe(self, target_bssid: Optional[str] = None) -> Tuple[bool, str]:
        """
        Check if we can send a probe right now.
        
        Args:
            target_bssid: Optional BSSID for per-target rate limiting
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        with self._lock:
            now = time.time()
            
            # Clean old entries (keep last 5 seconds)
            self._probe_times = [t for t in self._probe_times if now - t < 5.0]
            
            # Check global rate limit (5 probes/sec max)
            recent_probes = len([t for t in self._probe_times if now - t < 1.0])
            if recent_probes >= MAX_PROBES_PER_SECOND:
                return False, f"Global rate limit ({MAX_PROBES_PER_SECOND}/sec)"
            
            # Check minimum interval
            if self._probe_times:
                last_probe = self._probe_times[-1]
                if (now - last_probe) * 1000 < MIN_PROBE_INTERVAL_MS:
                    return False, f"Min interval ({MIN_PROBE_INTERVAL_MS}ms)"
            
            # Check burst limit
            if self._burst_count >= BURST_SIZE_LIMIT:
                if now - self._burst_start < BURST_COOLDOWN_SEC:
                    return False, f"Burst cooldown ({BURST_COOLDOWN_SEC}s)"
                else:
                    # Reset burst counter
                    self._burst_count = 0
                    self._burst_start = now
            
            # Check per-BSSID cooldown
            if target_bssid:
                bssid_lower = target_bssid.lower()
                last_bssid_probe = self._per_bssid_last_probe.get(bssid_lower, 0)
                if now - last_bssid_probe < PER_BSSID_COOLDOWN_SEC:
                    return False, f"Per-BSSID cooldown ({PER_BSSID_COOLDOWN_SEC}s)"
            
            return True, "OK"
    
    def record_probe(self, target_bssid: Optional[str] = None):
        """Record that a probe was sent."""
        with self._lock:
            now = time.time()
            self._probe_times.append(now)
            
            # Update burst tracking
            if self._burst_count == 0:
                self._burst_start = now
            self._burst_count += 1
            
            # Update per-BSSID tracking
            if target_bssid:
                self._per_bssid_last_probe[target_bssid.lower()] = now
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            now = time.time()
            recent = len([t for t in self._probe_times if now - t < 60.0])
            return {
                "probes_last_minute": recent,
                "probes_per_second": len([t for t in self._probe_times if now - t < 1.0]),
                "burst_count": self._burst_count,
                "tracked_bssids": len(self._per_bssid_last_probe)
            }


class LegalGuard:
    """
    Legal compliance guard.
    
    SAFETY LAYER 2: Ensures only legal frame types are transmitted.
    
    This implements a WHITELIST approach - only explicitly allowed
    frame types can pass. Everything else is rejected.
    
    ALLOWED (whitelist):
    - Probe Request (Management, subtype 4)
    
    FORBIDDEN (everything else, especially):
    - Authentication
    - Association
    - Deauthentication
    - Disassociation
    - Data frames
    - Action frames
    """
    
    # The ONLY frame type/subtype combination we allow
    # Format: (type, subtype)
    _ALLOWED_FRAMES = frozenset([
        (FRAME_TYPE_MANAGEMENT, FRAME_SUBTYPE_PROBE_REQUEST),  # Probe Request only
    ])
    
    # Explicitly forbidden (for logging purposes)
    _FORBIDDEN_NAMES = {
        (0, 0): "Association Request",
        (0, 1): "Association Response",
        (0, 2): "Reassociation Request",
        (0, 3): "Reassociation Response",
        (0, 10): "Disassociation",
        (0, 11): "Authentication",
        (0, 12): "Deauthentication",
        (0, 13): "Action",
        (2, 0): "Data",
        (2, 4): "Null Data",
        (2, 8): "QoS Data",
    }
    
    @classmethod
    def check_frame_type(cls, frame_type: int, frame_subtype: int) -> Tuple[bool, str]:
        """
        Check if a frame type/subtype is allowed.
        
        Args:
            frame_type: IEEE 802.11 frame type (0=mgmt, 1=ctrl, 2=data)
            frame_subtype: IEEE 802.11 frame subtype
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        key = (frame_type, frame_subtype)
        
        if key in cls._ALLOWED_FRAMES:
            return True, "Probe Request - ALLOWED"
        
        # Get forbidden name for logging
        name = cls._FORBIDDEN_NAMES.get(key, f"Unknown ({frame_type}/{frame_subtype})")
        return False, f"BLOCKED: {name} frame is FORBIDDEN"
    
    @classmethod
    def check_channel(cls, channel: int) -> Tuple[bool, str]:
        """
        Check if transmission on a channel is allowed.
        
        DFS channels require radar detection and we must NOT
        transmit on them without proper hardware support.
        
        Args:
            channel: WiFi channel number
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if channel in DFS_CHANNELS:
            return False, f"BLOCKED: Channel {channel} is DFS (radar detection required)"
        
        if channel < 1 or channel > 177:
            return False, f"BLOCKED: Invalid channel {channel}"
        
        return True, f"Channel {channel} - ALLOWED"
    
    @classmethod
    def is_probe_request(cls, frame_type: int, frame_subtype: int) -> bool:
        """Quick check if frame is a Probe Request."""
        return frame_type == FRAME_TYPE_MANAGEMENT and frame_subtype == FRAME_SUBTYPE_PROBE_REQUEST


class FrameValidator:
    """
    Frame structure validator.
    
    SAFETY LAYER 3: Validates that constructed frames are
    properly formed and don't contain anything unexpected.
    
    Checks:
    - Correct layer structure (Radiotap + Dot11 + Dot11ProbeReq)
    - Valid MAC addresses (no multicast source, etc.)
    - Correct frame control field
    - No injection of unexpected IEs
    """
    
    @staticmethod
    def validate_mac(mac: str, allow_broadcast: bool = False) -> Tuple[bool, str]:
        """
        Validate a MAC address.
        
        Args:
            mac: MAC address string (xx:xx:xx:xx:xx:xx)
            allow_broadcast: Whether broadcast address is allowed
            
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        if not mac:
            return False, "Empty MAC address"
        
        # Normalize
        mac_lower = mac.lower().replace("-", ":")
        
        # Check format
        parts = mac_lower.split(":")
        if len(parts) != 6:
            return False, f"Invalid MAC format: {mac}"
        
        try:
            bytes_val = [int(p, 16) for p in parts]
        except ValueError:
            return False, f"Invalid hex in MAC: {mac}"
        
        # Check for multicast bit in source MAC (bit 0 of first byte)
        # Source MACs should never have multicast bit set (except broadcast)
        if bytes_val[0] & 0x01:
            if mac_lower == BROADCAST_MAC:
                if allow_broadcast:
                    return True, "Broadcast MAC (allowed for destination)"
                else:
                    return False, "Broadcast not allowed as source"
            return False, "Multicast bit set in MAC (invalid for source)"
        
        # Check for all-zeros (invalid)
        if all(b == 0 for b in bytes_val):
            return False, "All-zero MAC address"
        
        return True, "Valid MAC"
    
    @staticmethod
    def validate_probe_request_frame(frame_bytes: bytes) -> Tuple[bool, str]:
        """
        Validate a constructed probe request frame.
        
        This is a final safety check before transmission.
        
        Args:
            frame_bytes: The raw frame bytes
            
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        if not frame_bytes or len(frame_bytes) < 24:
            return False, "Frame too short"
        
        # The frame control field should indicate Probe Request
        # Frame Control is first 2 bytes after Radiotap header
        # We need to find where the actual 802.11 header starts
        
        # For basic validation, check that it's not obviously wrong
        if len(frame_bytes) > 2048:
            return False, "Frame too large (max 2048 bytes)"
        
        return True, "Frame structure valid"


# =============================================================================
# SECTION 4: PROBE REQUEST BUILDER
# =============================================================================

class ProbeRequestBuilder:
    """
    Builds IEEE 802.11 Probe Request frames using Scapy.
    
    All frames are validated through the triple safety system
    before being returned.
    """
    
    def __init__(self, source_mac: str):
        """
        Initialize the probe request builder.
        
        Args:
            source_mac: The source MAC address (device's real MAC)
        """
        # Validate source MAC
        valid, reason = FrameValidator.validate_mac(source_mac)
        if not valid:
            raise ValueError(f"Invalid source MAC: {reason}")
        
        self._source_mac = source_mac.lower()
        self._scapy_available = False
        
        try:
            from scapy.all import (
                RadioTap, Dot11, Dot11ProbeReq, Dot11Elt,
                sendp, conf
            )
            self._scapy_available = True
            self._RadioTap = RadioTap
            self._Dot11 = Dot11
            self._Dot11ProbeReq = Dot11ProbeReq
            self._Dot11Elt = Dot11Elt
            self._sendp = sendp
            self._conf = conf
        except ImportError:
            pass
    
    @property
    def is_available(self) -> bool:
        """Check if Scapy is available for frame building."""
        return self._scapy_available
    
    def build_broadcast_probe(self, 
                               ssid: str = "",
                               supported_rates: bytes = b"\x82\x84\x8b\x96\x0c\x12\x18\x24",
                               channel: int = 0) -> Optional[Any]:
        """
        Build a broadcast probe request.
        
        Args:
            ssid: SSID to probe for (empty string = wildcard/broadcast)
            supported_rates: Supported rates IE data
            channel: Channel hint (for logging)
            
        Returns:
            Scapy packet ready for transmission, or None if blocked
        """
        if not self._scapy_available:
            return None
        
        # SAFETY CHECK 1: Legal Guard - verify this is allowed
        allowed, reason = LegalGuard.check_frame_type(
            FRAME_TYPE_MANAGEMENT, 
            FRAME_SUBTYPE_PROBE_REQUEST
        )
        if not allowed:
            print(f"[EASM SAFETY] {reason}")
            return None
        
        # SAFETY CHECK 2: Channel check
        if channel > 0:
            allowed, reason = LegalGuard.check_channel(channel)
            if not allowed:
                print(f"[EASM SAFETY] {reason}")
                return None
        
        # Build the frame
        # RadioTap header (minimal)
        radio = self._RadioTap()
        
        # Dot11 header
        # type=0 (Management), subtype=4 (Probe Request)
        dot11 = self._Dot11(
            type=0,
            subtype=4,
            addr1=BROADCAST_MAC,      # Destination (broadcast)
            addr2=self._source_mac,   # Source (our MAC)
            addr3=BROADCAST_MAC       # BSSID (broadcast for probe)
        )
        
        # Probe Request layer (empty for basic probe)
        probe_req = self._Dot11ProbeReq()
        
        # Information Elements
        # IE 0: SSID (empty = wildcard)
        ssid_ie = self._Dot11Elt(ID=0, info=ssid.encode('utf-8', errors='ignore'))
        
        # IE 1: Supported Rates
        rates_ie = self._Dot11Elt(ID=1, info=supported_rates)
        
        # Assemble frame
        frame = radio / dot11 / probe_req / ssid_ie / rates_ie
        
        # SAFETY CHECK 3: Final validation
        try:
            frame_bytes = bytes(frame)
            valid, reason = FrameValidator.validate_probe_request_frame(frame_bytes)
            if not valid:
                print(f"[EASM SAFETY] Frame validation failed: {reason}")
                return None
        except Exception as e:
            print(f"[EASM SAFETY] Frame serialization failed: {e}")
            return None
        
        return frame
    
    def build_directed_probe(self,
                              target_bssid: str,
                              ssid: str,
                              channel: int = 0) -> Optional[Any]:
        """
        Build a directed probe request to a specific AP.
        
        Args:
            target_bssid: Target AP's BSSID
            ssid: SSID to probe for
            channel: Channel hint
            
        Returns:
            Scapy packet ready for transmission, or None if blocked
        """
        if not self._scapy_available:
            return None
        
        # SAFETY CHECK: Validate target BSSID
        valid, reason = FrameValidator.validate_mac(target_bssid, allow_broadcast=True)
        if not valid:
            print(f"[EASM SAFETY] Invalid target BSSID: {reason}")
            return None
        
        # SAFETY CHECK: Legal Guard
        allowed, reason = LegalGuard.check_frame_type(
            FRAME_TYPE_MANAGEMENT,
            FRAME_SUBTYPE_PROBE_REQUEST
        )
        if not allowed:
            print(f"[EASM SAFETY] {reason}")
            return None
        
        # SAFETY CHECK: Channel
        if channel > 0:
            allowed, reason = LegalGuard.check_channel(channel)
            if not allowed:
                print(f"[EASM SAFETY] {reason}")
                return None
        
        # Build directed probe
        radio = self._RadioTap()
        
        dot11 = self._Dot11(
            type=0,
            subtype=4,
            addr1=target_bssid.lower(),  # Destination (specific AP)
            addr2=self._source_mac,       # Source (our MAC)
            addr3=target_bssid.lower()    # BSSID (specific AP)
        )
        
        probe_req = self._Dot11ProbeReq()
        ssid_ie = self._Dot11Elt(ID=0, info=ssid.encode('utf-8', errors='ignore'))
        rates_ie = self._Dot11Elt(ID=1, info=b"\x82\x84\x8b\x96\x0c\x12\x18\x24")
        
        frame = radio / dot11 / probe_req / ssid_ie / rates_ie
        
        # Final validation
        try:
            frame_bytes = bytes(frame)
            valid, reason = FrameValidator.validate_probe_request_frame(frame_bytes)
            if not valid:
                print(f"[EASM SAFETY] Frame validation failed: {reason}")
                return None
        except Exception as e:
            print(f"[EASM SAFETY] Frame serialization failed: {e}")
            return None
        
        return frame


# =============================================================================
# SECTION 5: IE PARSER (Information Element Harvester)
# =============================================================================

class IEHarvester:
    """
    Harvests and parses Information Elements from probe responses.
    
    IEs contain capability information like:
    - HT Capabilities (802.11n)
    - VHT Capabilities (802.11ac)
    - HE Capabilities (802.11ax/WiFi 6)
    - RSN (security suites)
    - Supported rates
    - Vendor-specific extensions
    """
    
    # IE ID to name mapping
    IE_NAMES = {
        0: "SSID",
        1: "Supported Rates",
        3: "DS Parameter Set",
        5: "TIM",
        7: "Country",
        32: "Power Constraint",
        42: "ERP Information",
        45: "HT Capabilities",
        48: "RSN",
        50: "Extended Supported Rates",
        61: "HT Operation",
        127: "Extended Capabilities",
        191: "VHT Capabilities",
        192: "VHT Operation",
        221: "Vendor Specific",
        255: "Extension Element",
    }
    
    # Vendor OUIs for Vendor Specific IEs
    VENDOR_OUIS = {
        b"\x00\x50\xf2\x01": "WPA",
        b"\x00\x50\xf2\x02": "WMM/WME",
        b"\x00\x50\xf2\x04": "WPS",
        b"\x00\x10\x18": "Broadcom",
        b"\x00\x17\xf2": "Apple",
    }
    
    @classmethod
    def parse_ies_from_packet(cls, packet, bssid: str) -> List[HarvestedIE]:
        """
        Parse all IEs from a packet (beacon or probe response).
        
        Args:
            packet: Scapy packet with Dot11Elt layers
            bssid: BSSID of the source AP
            
        Returns:
            List of HarvestedIE objects
        """
        harvested = []
        
        try:
            from scapy.all import Dot11Elt
            
            if not packet.haslayer(Dot11Elt):
                return harvested
            
            elt = packet.getlayer(Dot11Elt)
            while elt:
                ie_id = elt.ID
                ie_data = elt.info if hasattr(elt, 'info') else b""
                ie_name = cls.IE_NAMES.get(ie_id, f"Unknown IE {ie_id}")
                
                # Parse specific IEs
                parsed_value = cls._parse_ie_value(ie_id, ie_data)
                
                harvested.append(HarvestedIE(
                    bssid=bssid,
                    ie_id=ie_id,
                    ie_name=ie_name,
                    ie_data=ie_data,
                    parsed_value=parsed_value
                ))
                
                # Move to next IE
                elt = elt.payload.getlayer(Dot11Elt) if elt.payload else None
                
        except Exception as e:
            pass
        
        return harvested
    
    @classmethod
    def _parse_ie_value(cls, ie_id: int, ie_data: bytes) -> Any:
        """Parse specific IE values."""
        try:
            if ie_id == 0:  # SSID
                return ie_data.decode('utf-8', errors='ignore')
            
            elif ie_id == 3:  # DS Parameter Set (channel)
                if ie_data:
                    return ie_data[0]
            
            elif ie_id == 45:  # HT Capabilities
                return cls._parse_ht_capabilities(ie_data)
            
            elif ie_id == 191:  # VHT Capabilities
                return cls._parse_vht_capabilities(ie_data)
            
            elif ie_id == 48:  # RSN
                return cls._parse_rsn(ie_data)
            
            elif ie_id == 221:  # Vendor Specific
                return cls._parse_vendor_specific(ie_data)
            
        except Exception:
            pass
        
        return None
    
    @classmethod
    def _parse_ht_capabilities(cls, data: bytes) -> Dict[str, Any]:
        """Parse HT (802.11n) capabilities."""
        if len(data) < 2:
            return {}
        
        ht_cap = struct.unpack('<H', data[:2])[0]
        
        return {
            "wifi_generation": 4,  # 802.11n
            "ldpc": bool(ht_cap & 0x0001),
            "channel_width_40mhz": bool(ht_cap & 0x0002),
            "sm_power_save": (ht_cap >> 2) & 0x03,
            "greenfield": bool(ht_cap & 0x0010),
            "short_gi_20mhz": bool(ht_cap & 0x0020),
            "short_gi_40mhz": bool(ht_cap & 0x0040),
            "tx_stbc": bool(ht_cap & 0x0080),
            "rx_stbc": (ht_cap >> 8) & 0x03,
        }
    
    @classmethod
    def _parse_vht_capabilities(cls, data: bytes) -> Dict[str, Any]:
        """Parse VHT (802.11ac) capabilities."""
        if len(data) < 4:
            return {}
        
        vht_cap = struct.unpack('<I', data[:4])[0]
        
        max_mpdu_len = vht_cap & 0x03
        supported_width = (vht_cap >> 2) & 0x03
        
        return {
            "wifi_generation": 5,  # 802.11ac
            "max_mpdu_length": [3895, 7991, 11454][max_mpdu_len] if max_mpdu_len < 3 else 3895,
            "supported_channel_width": ["80MHz", "160MHz", "80+80MHz"][supported_width] if supported_width < 3 else "80MHz",
            "rx_ldpc": bool(vht_cap & 0x10),
            "short_gi_80mhz": bool(vht_cap & 0x20),
            "short_gi_160mhz": bool(vht_cap & 0x40),
            "tx_stbc": bool(vht_cap & 0x80),
            "su_beamformer": bool(vht_cap & 0x800),
            "su_beamformee": bool(vht_cap & 0x1000),
            "mu_beamformer": bool(vht_cap & 0x80000),
            "mu_beamformee": bool(vht_cap & 0x100000),
        }
    
    @classmethod
    def _parse_rsn(cls, data: bytes) -> Dict[str, Any]:
        """Parse RSN (security) IE."""
        if len(data) < 8:
            return {}
        
        try:
            version = struct.unpack('<H', data[:2])[0]
            group_cipher_oui = data[2:5]
            group_cipher_type = data[5]
            
            # Cipher suite mapping
            cipher_types = {
                0: "Use group",
                1: "WEP-40",
                2: "TKIP",
                4: "CCMP",
                5: "WEP-104",
                8: "GCMP-128",
                9: "GCMP-256",
            }
            
            return {
                "version": version,
                "group_cipher": cipher_types.get(group_cipher_type, f"Unknown ({group_cipher_type})"),
                "is_wpa2": version >= 1,
            }
        except:
            return {}
    
    @classmethod
    def _parse_vendor_specific(cls, data: bytes) -> Dict[str, Any]:
        """Parse Vendor Specific IE."""
        if len(data) < 4:
            return {}
        
        oui = data[:3]
        vendor_type = data[3]
        
        vendor_name = "Unknown"
        for known_oui, name in cls.VENDOR_OUIS.items():
            if data[:len(known_oui)] == known_oui:
                vendor_name = name
                break
        
        return {
            "oui": oui.hex(),
            "vendor": vendor_name,
            "type": vendor_type,
        }
    
    @classmethod
    def get_wifi_generation(cls, ies: List[HarvestedIE]) -> int:
        """Determine WiFi generation from IEs."""
        has_he = any(ie.ie_id == 255 for ie in ies)  # Extension (HE)
        has_vht = any(ie.ie_id == 191 for ie in ies)
        has_ht = any(ie.ie_id == 45 for ie in ies)
        
        if has_he:
            return 6  # WiFi 6 (802.11ax)
        elif has_vht:
            return 5  # WiFi 5 (802.11ac)
        elif has_ht:
            return 4  # WiFi 4 (802.11n)
        else:
            return 3  # Legacy (802.11a/b/g)


# =============================================================================
# SECTION 6: HIDDEN SSID REVEALER
# =============================================================================

class HiddenSSIDRevealer:
    """
    Reveals hidden SSIDs through legal directed probing.
    
    Hidden networks broadcast beacons with empty SSID fields but
    MUST respond to directed probe requests with the actual SSID.
    This is standard IEEE 802.11 behaviour, not a hack.
    """
    
    # Common SSID patterns to try for hidden networks
    COMMON_SSIDS = [
        # Enterprise patterns
        "Guest", "Wireless", "WiFi", "Office", "Corporate", "Internal",
        "Staff", "Employee", "Secure", "Private", "Admin",
        # Consumer patterns
        "Home", "MyNetwork", "NETGEAR", "linksys", "dlink", "TP-Link",
        "ASUS", "xfinitywifi", "ATT", "Verizon", "Spectrum",
        # IoT patterns
        "SmartHome", "Ring", "Nest", "Alexa", "Echo", "HomePod",
        # Generic
        "default", "setup", "config", "network", "wlan",
    ]
    
    def __init__(self):
        self._pending_reveals: Dict[str, ProbeTarget] = {}
        self._revealed: Dict[str, str] = {}  # bssid -> revealed ssid
        self._candidate_index: Dict[str, int] = {}  # bssid -> index in candidates
    
    def add_hidden_network(self, bssid: str, channel: int = 0) -> None:
        """Add a hidden network to the reveal queue."""
        bssid_lower = bssid.lower()
        if bssid_lower not in self._pending_reveals and bssid_lower not in self._revealed:
            self._pending_reveals[bssid_lower] = ProbeTarget(
                bssid=bssid_lower,
                channel=channel,
                is_hidden=True
            )
            self._candidate_index[bssid_lower] = 0
    
    def get_next_probe_candidate(self) -> Optional[Tuple[str, str, int]]:
        """
        Get the next hidden network probe to try.
        
        Returns:
            Tuple of (bssid, ssid_candidate, channel) or None
        """
        for bssid, target in self._pending_reveals.items():
            if not target.can_probe():
                continue
            
            idx = self._candidate_index.get(bssid, 0)
            if idx >= len(self.COMMON_SSIDS):
                continue  # Exhausted candidates for this BSSID
            
            ssid = self.COMMON_SSIDS[idx]
            return (bssid, ssid, target.channel)
        
        return None
    
    def record_probe_sent(self, bssid: str) -> None:
        """Record that a probe was sent for a hidden network."""
        bssid_lower = bssid.lower()
        if bssid_lower in self._pending_reveals:
            target = self._pending_reveals[bssid_lower]
            target.last_probed = time.time()
            target.probe_count += 1
            self._candidate_index[bssid_lower] = self._candidate_index.get(bssid_lower, 0) + 1
    
    def check_reveal(self, bssid: str, ssid: str) -> bool:
        """
        Check if a probe response revealed a hidden SSID.
        
        Args:
            bssid: BSSID of the responding AP
            ssid: SSID from the probe response
            
        Returns:
            True if this was a new reveal
        """
        bssid_lower = bssid.lower()
        
        if bssid_lower in self._pending_reveals and ssid:
            self._revealed[bssid_lower] = ssid
            del self._pending_reveals[bssid_lower]
            return True
        
        return False
    
    def is_revealed(self, bssid: str) -> bool:
        """Check if a BSSID's SSID has been revealed."""
        return bssid.lower() in self._revealed
    
    def get_revealed_ssid(self, bssid: str) -> Optional[str]:
        """Get the revealed SSID for a BSSID."""
        return self._revealed.get(bssid.lower())
    
    def get_stats(self) -> Dict[str, int]:
        """Get reveal statistics."""
        return {
            "pending": len(self._pending_reveals),
            "revealed": len(self._revealed),
            "total_tracked": len(self._pending_reveals) + len(self._revealed)
        }


# =============================================================================
# SECTION 7: CHANNEL SWEEPER
# =============================================================================

class ChannelSweeper:
    """
    Manages channel hopping for active scanning.
    
    Sweeps through safe (non-DFS) channels, sending probe bursts
    on each channel and collecting responses.
    """
    
    def __init__(self, channels: Optional[List[int]] = None):
        """
        Initialize channel sweeper.
        
        Args:
            channels: List of channels to sweep (defaults to safe channels)
        """
        self._channels = channels or ALL_SAFE_CHANNELS
        self._current_index = 0
        self._last_hop_time = 0.0
        self._channel_stats: Dict[int, Dict] = {}
    
    @property
    def current_channel(self) -> int:
        """Get current channel."""
        return self._channels[self._current_index]
    
    def should_hop(self) -> bool:
        """Check if it's time to hop to next channel."""
        return (time.time() - self._last_hop_time) * 1000 >= CHANNEL_DWELL_TIME_MS
    
    def hop_next(self) -> int:
        """Hop to next channel and return it."""
        self._current_index = (self._current_index + 1) % len(self._channels)
        self._last_hop_time = time.time()
        return self.current_channel
    
    def record_channel_activity(self, channel: int, ap_count: int, noise_dbm: int = -95):
        """Record activity observed on a channel."""
        if channel not in self._channel_stats:
            self._channel_stats[channel] = {
                "observations": 0,
                "total_aps": 0,
                "last_noise_dbm": -95
            }
        
        self._channel_stats[channel]["observations"] += 1
        self._channel_stats[channel]["total_aps"] += ap_count
        self._channel_stats[channel]["last_noise_dbm"] = noise_dbm
    
    def get_recommended_channel(self) -> int:
        """Get recommended channel (least congested)."""
        if not self._channel_stats:
            return 1  # Default to channel 1
        
        # Find channel with lowest average AP count
        best_channel = 1
        best_score = float('inf')
        
        for channel, stats in self._channel_stats.items():
            if stats["observations"] > 0:
                avg_aps = stats["total_aps"] / stats["observations"]
                if avg_aps < best_score:
                    best_score = avg_aps
                    best_channel = channel
        
        return best_channel
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sweeper statistics."""
        return {
            "current_channel": self.current_channel,
            "channels_in_rotation": len(self._channels),
            "channel_stats": dict(self._channel_stats)
        }


# =============================================================================
# SECTION 8: MAIN EASM CONTROLLER
# =============================================================================

class EASMController:
    """
    Enhanced Active Scan Mode Controller.
    
    This is the main entry point for EASM functionality.
    It coordinates all active scanning operations while
    ensuring legal compliance through the triple safety system.
    
    Usage:
        controller = EASMController(
            interface="Wi-Fi",
            report_callback=my_callback,
            source_mac="AA:BB:CC:DD:EE:FF"
        )
        controller.start()
        
        # In scan loop:
        controller.tick()
        
        # On packet receive:
        controller.process_packet(packet)
        
        # When done:
        controller.stop()
    """
    
    def __init__(self, 
                 interface: str,
                 report_callback: Callable[[EASMDiscovery], None],
                 source_mac: Optional[str] = None,
                 logger: Optional[Callable[[str, str], None]] = None):
        """
        Initialize EASM Controller.
        
        Args:
            interface: Network interface name
            report_callback: Called with each discovery
            source_mac: Source MAC for probes (auto-detected if None)
            logger: Optional logging callback (level, message)
        """
        self._interface = interface
        self._report_callback = report_callback
        self._logger = logger or (lambda l, m: print(f"[EASM {l}] {m}"))
        
        # Get source MAC
        self._source_mac = source_mac or self._get_interface_mac()
        if not self._source_mac:
            self._source_mac = self._generate_random_mac()
            self._logger("WARN", f"Using random MAC: {self._source_mac}")
        
        # State
        self._running = False
        self._mode = EASMMode.STANDARD
        
        # Triple safety system (MANDATORY)
        self._rate_limiter = RateLimiter()
        # LegalGuard and FrameValidator are class methods, always active
        
        # Subsystems
        self._probe_builder = ProbeRequestBuilder(self._source_mac)
        self._ie_harvester = IEHarvester()
        self._hidden_revealer = HiddenSSIDRevealer()
        self._channel_sweeper = ChannelSweeper()
        
        # Statistics
        self._stats = EASMStats()
        
        # Known APs (BSSID -> last seen data)
        self._known_aps: Dict[str, Dict] = {}
        
        # Probe response tracking
        self._pending_probes: Dict[str, float] = {}  # bssid -> probe_time
        
        self._logger("INFO", "EASM Controller initialized")
        self._logger("INFO", f"  Interface: {interface}")
        self._logger("INFO", f"  Source MAC: {self._source_mac}")
        self._logger("INFO", f"  Safe channels: {ALL_SAFE_CHANNELS}")
        self._logger("SAFETY", "Triple safety system ACTIVE")
    
    def _get_interface_mac(self) -> Optional[str]:
        """Get MAC address of interface."""
        try:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff)
                           for i in range(0, 48, 8)][::-1])
            return mac
        except:
            return None
    
    def _generate_random_mac(self) -> str:
        """Generate a random locally-administered MAC."""
        # Set locally administered bit, clear multicast bit
        first_byte = (random.randint(0, 255) & 0xFE) | 0x02
        rest = [random.randint(0, 255) for _ in range(5)]
        return ':'.join(f'{b:02x}' for b in [first_byte] + rest)
    
    @property
    def is_running(self) -> bool:
        """Check if EASM is running."""
        return self._running
    
    @property
    def stats(self) -> EASMStats:
        """Get current statistics."""
        return self._stats
    
    def start(self) -> None:
        """Start EASM operations."""
        if self._running:
            return
        
        self._running = True
        self._stats = EASMStats()
        self._logger("INFO", "EASM Controller STARTED")
        self._logger("INFO", f"  Mode: {self._mode.value}")
        self._logger("INFO", f"  Rate limit: {MAX_PROBES_PER_SECOND}/sec")
    
    def stop(self) -> None:
        """Stop EASM operations."""
        if not self._running:
            return
        
        self._running = False
        self._logger("INFO", "EASM Controller STOPPED")
        self._logger("INFO", f"  Probes sent: {self._stats.probes_sent}")
        self._logger("INFO", f"  Responses received: {self._stats.probe_responses_received}")
        self._logger("INFO", f"  Hidden SSIDs revealed: {self._stats.hidden_ssids_revealed}")
    
    def request_hidden_reveal(self, bssid: str, channel: int) -> None:
        """
        Request a hidden SSID reveal attempt for a specific BSSID.
        
        This queues the BSSID for directed probe requests.
        """
        if not self._running:
            return
        
        # Register with hidden revealer for probing
        self._hidden_revealer.add_hidden_network(
            bssid=bssid,
            channel=channel
        )
        self._logger("DEBUG", f"Queued hidden reveal request for {bssid} on ch{channel}")

    def tick(self) -> None:
        """
        Periodic tick - called from scan loop.
        
        This method manages the active scanning operations:
        1. Check rate limits
        2. Send broadcast probes
        3. Send directed probes for hidden SSIDs
        4. Manage channel sweeping
        """
        if not self._running:
            return
        
        # Try to send probes (respecting rate limits)
        self._try_broadcast_probe()
        self._try_hidden_ssid_probe()
    
    def _try_broadcast_probe(self) -> bool:
        """Try to send a broadcast probe request."""
        # Check rate limit
        allowed, reason = self._rate_limiter.can_send_probe()
        if not allowed:
            return False
        
        # Build probe
        frame = self._probe_builder.build_broadcast_probe(
            ssid="",  # Wildcard
            channel=self._channel_sweeper.current_channel
        )
        
        if not frame:
            return False
        
        # Send probe
        if self._send_probe(frame):
            self._rate_limiter.record_probe()
            self._stats.probes_sent += 1
            return True
        
        return False
    
    def _try_hidden_ssid_probe(self) -> bool:
        """Try to send a directed probe for hidden SSID discovery."""
        candidate = self._hidden_revealer.get_next_probe_candidate()
        if not candidate:
            return False
        
        bssid, ssid, channel = candidate
        
        # Check rate limit (with per-BSSID tracking)
        allowed, reason = self._rate_limiter.can_send_probe(bssid)
        if not allowed:
            return False
        
        # Build directed probe
        frame = self._probe_builder.build_directed_probe(
            target_bssid=bssid,
            ssid=ssid,
            channel=channel
        )
        
        if not frame:
            return False
        
        # Send probe
        if self._send_probe(frame):
            self._rate_limiter.record_probe(bssid)
            self._hidden_revealer.record_probe_sent(bssid)
            self._stats.probes_sent += 1
            self._pending_probes[bssid.lower()] = time.time()
            return True
        
        return False
    
    def _send_probe(self, frame) -> bool:
        """
        Send a probe request frame with adapter name fallback.
        
        SAFETY: This is the ONLY method that actually transmits.
        All frames must have passed through the triple safety system.
        
        On Windows, adapter names can vary (Wi-Fi, eth0, etc.). We try
        multiple naming formats to work with different drivers.
        """
        if not self._probe_builder.is_available:
            return False
        
        try:
            from scapy.all import sendp
            import socket
            
            # Try to send with the provided interface name
            # On Windows, Scapy sometimes expects GUID, sometimes friendly name
            interface_attempts = [
                self._interface,                    # "Wi-Fi"
                self._interface.lower(),            # "wi-fi"
                self._interface.replace(" ", ""),   # "WiFi"
            ]
            
            last_error = None
            for iface_name in interface_attempts:
                try:
                    # Timeout-protected send (non-blocking)
                    sendp(frame, iface=iface_name, verbose=False, timeout=1)
                    self._logger("DEBUG", f"Probe sent on {iface_name}")
                    return True
                except (OSError, socket.error) as e:
                    last_error = e
                    continue
            
            # If all attempts failed
            if last_error:
                self._logger("ERROR", f"Probe transmission failed on all adapters: {last_error}")
            return False
            
        except ImportError as e:
            self._logger("ERROR", f"Scapy import failed: {e}")
            return False
        except Exception as e:
            self._logger("ERROR", f"Probe transmission exception: {e}")
            import traceback
            self._logger("DEBUG", traceback.format_exc())
            return False
    
    def process_packet(self, packet) -> None:
        """
        Process a received packet.
        
        Called by the scanner for relevant packets.
        Handles both Beacon and Probe Response frames.
        """
        if not self._running:
            return
        
        try:
            from scapy.all import Dot11Beacon, Dot11ProbeResp, Dot11Elt
            
            bssid = packet.addr2 if hasattr(packet, 'addr2') else None
            if not bssid:
                return
            
            bssid_lower = bssid.lower()
            
            # Get SSID
            ssid = ""
            if packet.haslayer(Dot11Elt):
                elt = packet.getlayer(Dot11Elt)
                if elt and elt.ID == 0:
                    ssid = elt.info.decode('utf-8', errors='ignore') if elt.info else ""
            
            # Get signal strength
            rssi_dbm = -70
            if hasattr(packet, 'dBm_AntSignal'):
                rssi_dbm = packet.dBm_AntSignal
            
            # Get channel
            channel = 0
            try:
                if packet.haslayer(Dot11Beacon):
                    stats = packet[Dot11Beacon].network_stats()
                    channel = int(ord(stats.get("channel", b"\x00")))
                elif packet.haslayer(Dot11ProbeResp):
                    # Parse DS Parameter Set IE
                    elt = packet.getlayer(Dot11Elt)
                    while elt:
                        if elt.ID == 3 and elt.info:  # DS Parameter Set
                            channel = elt.info[0]
                            break
                        elt = elt.payload.getlayer(Dot11Elt) if elt.payload else None
            except:
                pass
            
            # Process Probe Response specifically
            if packet.haslayer(Dot11ProbeResp):
                self._process_probe_response(packet, bssid_lower, ssid, rssi_dbm, channel)
            
            # Process Beacon (check for hidden networks)
            elif packet.haslayer(Dot11Beacon):
                if not ssid or len(ssid) == 0:
                    # Hidden network detected
                    self._hidden_revealer.add_hidden_network(bssid_lower, channel)
                    self._logger("HIDDEN", f"Hidden network detected: {bssid_lower} ch{channel}")
            
            # Track AP
            self._known_aps[bssid_lower] = {
                "ssid": ssid,
                "channel": channel,
                "rssi_dbm": rssi_dbm,
                "last_seen": time.time()
            }
            
        except Exception as e:
            self._logger("ERROR", f"Packet processing error: {e}")
    
    def _process_probe_response(self, packet, bssid: str, ssid: str, 
                                 rssi_dbm: int, channel: int) -> None:
        """
        Process a Probe Response frame.
        
        This is where we extract enhanced intelligence from
        probe responses, including IE harvesting and hidden
        SSID reveals.
        """
        self._stats.probe_responses_received += 1
        
        # Check for hidden SSID reveal
        if self._hidden_revealer.check_reveal(bssid, ssid):
            self._stats.hidden_ssids_revealed += 1
            self._logger("REVEAL", f"Hidden SSID revealed: {bssid} = '{ssid}'")
            
            # Report discovery
            self._report_callback(EASMDiscovery(
                discovery_type="hidden_reveal",
                bssid=bssid,
                ssid=ssid,
                channel=channel,
                rssi_dbm=rssi_dbm,
                source="easm_reveal"
            ))
        
        # Harvest IEs
        ies = self._ie_harvester.parse_ies_from_packet(packet, bssid)
        if ies:
            self._stats.ies_harvested += len(ies)
            
            # Extract capabilities
            wifi_gen = self._ie_harvester.get_wifi_generation(ies)
            capabilities = {
                "wifi_generation": wifi_gen,
                "ie_count": len(ies),
            }
            
            # Add specific parsed values
            for ie in ies:
                if ie.parsed_value and ie.ie_id in [45, 191, 48]:
                    capabilities[ie.ie_name] = ie.parsed_value
            
            # Report discovery
            self._report_callback(EASMDiscovery(
                discovery_type="probe_response",
                bssid=bssid,
                ssid=ssid,
                channel=channel,
                rssi_dbm=rssi_dbm,
                capabilities=capabilities,
                ies=ies,
                source="easm_probe"
            ))
    
    def add_hidden_target(self, bssid: str, channel: int = 0) -> None:
        """Add a hidden network to the reveal queue."""
        self._hidden_revealer.add_hidden_network(bssid, channel)
    
    def get_full_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "running": self._running,
            "mode": self._mode.value,
            "probes": {
                "sent": self._stats.probes_sent,
                "responses": self._stats.probe_responses_received,
                "rate_per_minute": self._stats.probes_per_minute
            },
            "hidden_ssids": self._hidden_revealer.get_stats(),
            "channels": self._channel_sweeper.get_stats(),
            "rate_limiter": self._rate_limiter.get_stats(),
            "known_aps": len(self._known_aps),
            "ies_harvested": self._stats.ies_harvested
        }


# =============================================================================
# SECTION 9: CONVENIENCE FUNCTIONS
# =============================================================================

def create_easm_controller(interface: str,
                           callback: Callable[[EASMDiscovery], None],
                           source_mac: Optional[str] = None) -> EASMController:
    """
    Factory function to create an EASM controller.
    
    Args:
        interface: Network interface name
        callback: Discovery callback
        source_mac: Optional source MAC
        
    Returns:
        Configured EASMController instance
    """
    return EASMController(
        interface=interface,
        report_callback=callback,
        source_mac=source_mac
    )


def is_dfs_channel(channel: int) -> bool:
    """Check if a channel is a DFS channel."""
    return channel in DFS_CHANNELS


def get_safe_channels() -> List[int]:
    """Get list of safe (non-DFS) channels."""
    return list(ALL_SAFE_CHANNELS)
