"""
Device Fingerprinting System for NEXUS WiFi Radar.

100% PASSIVE - Infers device type from beacon data only.

Uses:
- Vendor OUI (MAC address prefix)
- SSID patterns
- Channel usage patterns
- Signal characteristics
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re


class DeviceType(Enum):
    """Device type classification."""
    ROUTER = "router"
    ACCESS_POINT = "access_point"
    MESH_NODE = "mesh_node"
    REPEATER = "repeater"
    MOBILE_HOTSPOT = "mobile_hotspot"
    IOT_DEVICE = "iot"
    PRINTER = "printer"
    SMART_TV = "smart_tv"
    GAMING = "gaming"
    ENTERPRISE = "enterprise"
    UNKNOWN = "unknown"


@dataclass
class DeviceFingerprint:
    """Fingerprint data for a device."""
    device_type: DeviceType
    confidence: int  # 0-100
    icon: str
    description: str
    tags: List[str] = field(default_factory=list)
    inferred_from: List[str] = field(default_factory=list)


# Vendor OUI to device type mapping
# Format: First 6 chars of MAC (AA:BB:CC) -> (DeviceType, confidence, description)
VENDOR_DEVICE_MAP: Dict[str, Tuple[DeviceType, int, str]] = {
    # Mobile/Hotspot vendors
    "Apple": (DeviceType.MOBILE_HOTSPOT, 70, "Apple device - likely iPhone/iPad hotspot"),
    "Samsung": (DeviceType.MOBILE_HOTSPOT, 60, "Samsung device - possibly phone hotspot"),
    "Google": (DeviceType.MOBILE_HOTSPOT, 65, "Google device - Pixel hotspot or Nest"),
    "OnePlus": (DeviceType.MOBILE_HOTSPOT, 75, "OnePlus phone hotspot"),
    "Xiaomi": (DeviceType.MOBILE_HOTSPOT, 70, "Xiaomi phone hotspot"),
    "Huawei": (DeviceType.MOBILE_HOTSPOT, 65, "Huawei device hotspot"),
    
    # Consumer Router vendors
    "TP-Link": (DeviceType.ROUTER, 85, "TP-Link router"),
    "Netgear": (DeviceType.ROUTER, 85, "Netgear router"),
    "Asus": (DeviceType.ROUTER, 85, "ASUS router"),
    "D-Link": (DeviceType.ROUTER, 85, "D-Link router"),
    "Linksys": (DeviceType.ROUTER, 85, "Linksys router"),
    "Belkin": (DeviceType.ROUTER, 80, "Belkin router"),
    "Buffalo": (DeviceType.ROUTER, 80, "Buffalo router"),
    "Tenda": (DeviceType.ROUTER, 80, "Tenda router"),
    
    # ISP Router vendors
    "Arris": (DeviceType.ROUTER, 90, "ISP-provided router (Arris)"),
    "Technicolor": (DeviceType.ROUTER, 90, "ISP-provided router"),
    "Sagemcom": (DeviceType.ROUTER, 90, "ISP-provided router"),
    "Hitron": (DeviceType.ROUTER, 90, "ISP-provided router"),
    "Calix": (DeviceType.ROUTER, 90, "ISP fiber router"),
    "Humax": (DeviceType.ROUTER, 85, "ISP-provided router"),
    "ZTE": (DeviceType.ROUTER, 85, "ZTE router/modem"),
    
    # Enterprise AP vendors
    "Cisco": (DeviceType.ENTERPRISE, 90, "Cisco enterprise AP"),
    "Cisco-Linksys": (DeviceType.ROUTER, 80, "Cisco/Linksys consumer"),
    "Meraki": (DeviceType.ENTERPRISE, 95, "Cisco Meraki enterprise AP"),
    "Ubiquiti": (DeviceType.ENTERPRISE, 90, "Ubiquiti UniFi AP"),
    "Aruba": (DeviceType.ENTERPRISE, 95, "Aruba enterprise AP"),
    "Ruckus": (DeviceType.ENTERPRISE, 95, "Ruckus enterprise AP"),
    "Fortinet": (DeviceType.ENTERPRISE, 90, "Fortinet enterprise AP"),
    "Juniper": (DeviceType.ENTERPRISE, 90, "Juniper/Mist enterprise AP"),
    "Extreme": (DeviceType.ENTERPRISE, 85, "Extreme Networks AP"),
    "Cambium": (DeviceType.ENTERPRISE, 85, "Cambium Networks AP"),
    
    # Mesh system vendors
    "eero": (DeviceType.MESH_NODE, 95, "Amazon eero mesh"),
    "Google Nest": (DeviceType.MESH_NODE, 95, "Google Nest WiFi mesh"),
    "Netgear Orbi": (DeviceType.MESH_NODE, 90, "Netgear Orbi mesh"),
    "Linksys Velop": (DeviceType.MESH_NODE, 90, "Linksys Velop mesh"),
    "TP-Link Deco": (DeviceType.MESH_NODE, 90, "TP-Link Deco mesh"),
    
    # IoT vendors
    "Espressif": (DeviceType.IOT_DEVICE, 90, "ESP8266/ESP32 IoT device"),
    "Tuya": (DeviceType.IOT_DEVICE, 95, "Tuya smart home device"),
    "Shenzhen": (DeviceType.IOT_DEVICE, 70, "Generic Chinese IoT"),
    "Amazon": (DeviceType.IOT_DEVICE, 75, "Amazon Echo/Ring device"),
    "Ring": (DeviceType.IOT_DEVICE, 90, "Ring doorbell/camera"),
    "Wyze": (DeviceType.IOT_DEVICE, 90, "Wyze smart home device"),
    "Philips": (DeviceType.IOT_DEVICE, 80, "Philips Hue bridge"),
    "LIFX": (DeviceType.IOT_DEVICE, 85, "LIFX smart lighting"),
    "Sonos": (DeviceType.IOT_DEVICE, 85, "Sonos speaker"),
    "Ecobee": (DeviceType.IOT_DEVICE, 90, "Ecobee thermostat"),
    "Nest": (DeviceType.IOT_DEVICE, 85, "Nest thermostat/camera"),
    
    # Smart TV vendors
    "LG Electronics": (DeviceType.SMART_TV, 80, "LG Smart TV"),
    "Sony": (DeviceType.SMART_TV, 70, "Sony device (TV/PlayStation)"),
    "Vizio": (DeviceType.SMART_TV, 85, "Vizio Smart TV"),
    "TCL": (DeviceType.SMART_TV, 80, "TCL Roku TV"),
    "Hisense": (DeviceType.SMART_TV, 80, "Hisense Smart TV"),
    "Roku": (DeviceType.SMART_TV, 90, "Roku streaming device"),
    
    # Printer vendors
    "HP Inc": (DeviceType.PRINTER, 90, "HP printer"),
    "Hewlett Packard": (DeviceType.PRINTER, 90, "HP printer"),
    "Canon": (DeviceType.PRINTER, 85, "Canon printer"),
    "Epson": (DeviceType.PRINTER, 85, "Epson printer"),
    "Brother": (DeviceType.PRINTER, 90, "Brother printer"),
    "Xerox": (DeviceType.PRINTER, 90, "Xerox printer"),
    "Lexmark": (DeviceType.PRINTER, 90, "Lexmark printer"),
    
    # Gaming
    "Nintendo": (DeviceType.GAMING, 90, "Nintendo console"),
    "Microsoft": (DeviceType.GAMING, 60, "Microsoft device (Xbox?)"),
    "Valve": (DeviceType.GAMING, 90, "Steam Deck/Link"),
}

# SSID patterns for device type inference
SSID_PATTERNS: List[Tuple[str, DeviceType, int, str]] = [
    # Mobile hotspots
    (r"(?i)^(iphone|ipad|android|pixel|galaxy|oneplus)", DeviceType.MOBILE_HOTSPOT, 90, "Mobile device hotspot"),
    (r"(?i)(hotspot|tether|portable)", DeviceType.MOBILE_HOTSPOT, 85, "Mobile hotspot"),
    (r"(?i)^(my\s*)?phone", DeviceType.MOBILE_HOTSPOT, 80, "Phone hotspot"),
    
    # Mesh networks
    (r"(?i)(eero|orbi|velop|deco|mesh)", DeviceType.MESH_NODE, 85, "Mesh network node"),
    (r"(?i)(google.*wifi|nest.*wifi)", DeviceType.MESH_NODE, 90, "Google mesh"),
    
    # Enterprise patterns
    (r"(?i)(corp|corporate|office|enterprise|business)", DeviceType.ENTERPRISE, 70, "Corporate network"),
    (r"(?i)(staff|employee|internal)", DeviceType.ENTERPRISE, 65, "Enterprise staff network"),
    (r"(?i)(guest|visitor|public)", DeviceType.ACCESS_POINT, 50, "Guest network"),
    (r"(?i)(eduroam)", DeviceType.ENTERPRISE, 95, "Educational enterprise"),
    
    # IoT patterns
    (r"(?i)(ring|nest|echo|alexa|smart|iot)", DeviceType.IOT_DEVICE, 70, "Smart home device"),
    (r"(?i)(camera|doorbell|thermostat|sensor)", DeviceType.IOT_DEVICE, 75, "IoT sensor/camera"),
    (r"(?i)(hue|lifx|wemo|tuya)", DeviceType.IOT_DEVICE, 85, "Smart home device"),
    
    # Printer patterns
    (r"(?i)(print|hp-|canon|epson|brother)", DeviceType.PRINTER, 80, "Wireless printer"),
    (r"(?i)(direct-.*print)", DeviceType.PRINTER, 90, "WiFi Direct printer"),
    
    # Repeater/extender patterns
    (r"(?i)(ext|extender|repeater|boost)", DeviceType.REPEATER, 85, "WiFi repeater/extender"),
    (r"(?i)(_ext$|_rpt$|_2$)", DeviceType.REPEATER, 70, "Likely repeater"),
    
    # Default/generic router patterns
    (r"(?i)^(netgear|linksys|dlink|tplink|asus)", DeviceType.ROUTER, 80, "Consumer router"),
    (r"(?i)^(xfinity|spectrum|att|verizon|comcast)", DeviceType.ROUTER, 85, "ISP router"),
]

# Device type icons for radar display
DEVICE_ICONS: Dict[DeviceType, str] = {
    DeviceType.ROUTER: "📶",
    DeviceType.ACCESS_POINT: "📡",
    DeviceType.MESH_NODE: "🔗",
    DeviceType.REPEATER: "🔄",
    DeviceType.MOBILE_HOTSPOT: "📱",
    DeviceType.IOT_DEVICE: "🧠",
    DeviceType.PRINTER: "🖨️",
    DeviceType.SMART_TV: "📺",
    DeviceType.GAMING: "🎮",
    DeviceType.ENTERPRISE: "🏢",
    DeviceType.UNKNOWN: "❓",
}


class DeviceFingerprinter:
    """
    Passive device fingerprinting system.
    
    Infers device type from:
    - Vendor OUI (MAC prefix)
    - SSID patterns
    - Channel usage
    - Signal characteristics
    """
    
    def __init__(self):
        self.fingerprints: Dict[str, DeviceFingerprint] = {}
        self.signal_history: Dict[str, List[Tuple[float, int]]] = {}  # bssid -> [(timestamp, signal)]
    
    def fingerprint(self, bssid: str, ssid: str, vendor: str, 
                    channel: int, signal: int, security: str) -> DeviceFingerprint:
        """
        Generate device fingerprint from passive beacon data.
        
        100% PASSIVE - only analyzes received beacon information.
        """
        inferred_from = []
        device_type = DeviceType.UNKNOWN
        confidence = 0
        description = "Unknown device"
        tags = []
        
        # 1. Check vendor OUI
        vendor_match = self._match_vendor(vendor)
        if vendor_match:
            device_type, conf, desc = vendor_match
            confidence = conf
            description = desc
            inferred_from.append(f"Vendor: {vendor}")
        
        # 2. Check SSID patterns
        ssid_match = self._match_ssid(ssid)
        if ssid_match:
            ssid_type, ssid_conf, ssid_desc = ssid_match
            # If SSID gives stronger signal, use it
            if ssid_conf > confidence:
                device_type = ssid_type
                confidence = ssid_conf
                description = ssid_desc
            elif ssid_conf > confidence - 20:
                # Corroborating evidence
                confidence = min(99, confidence + 10)
            inferred_from.append(f"SSID pattern: {ssid[:20]}")
        
        # 3. Analyze channel usage
        channel_hints = self._analyze_channel(channel, signal)
        tags.extend(channel_hints)
        
        # 4. Security analysis
        security_hints = self._analyze_security(security, device_type)
        tags.extend(security_hints)
        
        # 5. Check for mobile hotspot indicators
        if self._is_likely_hotspot(ssid, vendor, signal):
            if device_type == DeviceType.UNKNOWN:
                device_type = DeviceType.MOBILE_HOTSPOT
                confidence = 60
                description = "Likely mobile hotspot"
            tags.append("mobile")
            inferred_from.append("Hotspot characteristics")
        
        # 6. Check for enterprise indicators
        if self._is_likely_enterprise(ssid, security, channel):
            if device_type == DeviceType.UNKNOWN:
                device_type = DeviceType.ENTERPRISE
                confidence = 50
                description = "Likely enterprise AP"
            tags.append("enterprise")
        
        # Get icon
        icon = DEVICE_ICONS.get(device_type, "❓")
        
        fingerprint = DeviceFingerprint(
            device_type=device_type,
            confidence=confidence,
            icon=icon,
            description=description,
            tags=tags,
            inferred_from=inferred_from
        )
        
        self.fingerprints[bssid] = fingerprint
        return fingerprint
    
    def _match_vendor(self, vendor: str) -> Optional[Tuple[DeviceType, int, str]]:
        """Match vendor string to device type."""
        if not vendor or vendor == "Unknown":
            return None
        
        vendor_lower = vendor.lower()
        
        for vendor_key, (dev_type, conf, desc) in VENDOR_DEVICE_MAP.items():
            if vendor_key.lower() in vendor_lower:
                return (dev_type, conf, desc)
        
        return None
    
    def _match_ssid(self, ssid: str) -> Optional[Tuple[DeviceType, int, str]]:
        """Match SSID against known patterns."""
        if not ssid:
            return None
        
        for pattern, dev_type, conf, desc in SSID_PATTERNS:
            if re.search(pattern, ssid):
                return (dev_type, conf, desc)
        
        return None
    
    def _analyze_channel(self, channel: int, signal: int) -> List[str]:
        """Analyze channel usage for hints."""
        tags = []
        
        if channel <= 14:
            tags.append("2.4GHz")
            # 2.4GHz DFS channels are rare
            if channel in [1, 6, 11]:
                tags.append("common-channel")
            else:
                tags.append("non-standard-channel")
        elif channel <= 64:
            tags.append("5GHz-low")
        elif channel <= 144:
            tags.append("5GHz-DFS")
            tags.append("likely-enterprise")  # DFS requires proper regulatory compliance
        else:
            tags.append("5GHz-high")
        
        # High signal on 5GHz suggests close proximity (shorter range)
        if channel > 14 and signal > 70:
            tags.append("nearby")
        
        return tags
    
    def _analyze_security(self, security: str, device_type: DeviceType) -> List[str]:
        """Analyze security for device hints."""
        tags = []
        security_upper = security.upper() if security else ""
        
        if "WPA3" in security_upper:
            tags.append("modern-security")
            tags.append("likely-recent-device")
        elif "WPA2" in security_upper and "ENTERPRISE" in security_upper:
            tags.append("enterprise-auth")
        elif "WEP" in security_upper:
            tags.append("legacy-security")
            tags.append("potentially-vulnerable")
        elif "OPEN" in security_upper or not security:
            tags.append("open-network")
            tags.append("no-encryption")
        
        return tags
    
    def _is_likely_hotspot(self, ssid: str, vendor: str, signal: int) -> bool:
        """Check if device is likely a mobile hotspot."""
        hotspot_vendors = ["apple", "samsung", "google", "oneplus", "xiaomi", "huawei", "oppo", "vivo"]
        hotspot_ssids = ["iphone", "android", "pixel", "galaxy", "hotspot", "tether"]
        
        vendor_lower = (vendor or "").lower()
        ssid_lower = (ssid or "").lower()
        
        # Vendor match
        if any(v in vendor_lower for v in hotspot_vendors):
            return True
        
        # SSID match
        if any(h in ssid_lower for h in hotspot_ssids):
            return True
        
        return False
    
    def _is_likely_enterprise(self, ssid: str, security: str, channel: int) -> bool:
        """Check if device is likely enterprise."""
        # Enterprise indicators
        enterprise_ssids = ["corp", "office", "staff", "employee", "eduroam", "802.1x"]
        ssid_lower = (ssid or "").lower()
        security_upper = (security or "").upper()
        
        if any(e in ssid_lower for e in enterprise_ssids):
            return True
        
        if "ENTERPRISE" in security_upper or "802.1X" in security_upper:
            return True
        
        # DFS channels suggest enterprise (require regulatory compliance)
        if 52 <= channel <= 144:
            return True
        
        return False
    
    def get_icon(self, bssid: str) -> str:
        """Get icon for a device."""
        fp = self.fingerprints.get(bssid)
        return fp.icon if fp else "❓"
    
    def get_fingerprint(self, bssid: str) -> Optional[DeviceFingerprint]:
        """Get stored fingerprint for a device."""
        return self.fingerprints.get(bssid)


# Global fingerprinter instance
_fingerprinter: Optional[DeviceFingerprinter] = None


def get_fingerprinter() -> DeviceFingerprinter:
    """Get the global fingerprinter instance."""
    global _fingerprinter
    if _fingerprinter is None:
        _fingerprinter = DeviceFingerprinter()
    return _fingerprinter
