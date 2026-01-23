"""
OUI Vendor Intelligence Module (OUI-IM)

100% OFFLINE - All vendor lookups from local static data.
100% PASSIVE - No network calls, no transmissions.

Provides:
- Vendor name lookup from BSSID/MAC
- Randomized MAC detection
- Vendor confidence scoring
- Spoof/rogue risk adjustments based on vendor
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Set
import re


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VendorInfo:
    """Vendor lookup result."""
    name: str
    prefix: str
    confidence: float  # 0-100
    is_known: bool
    is_randomized: bool
    vendor_type: str  # "consumer", "enterprise", "iot", "mesh", "unknown"
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'prefix': self.prefix,
            'confidence': self.confidence,
            'is_known': self.is_known,
            'is_randomized': self.is_randomized,
            'vendor_type': self.vendor_type
        }


# ═══════════════════════════════════════════════════════════════════════════════
# OUI DATABASE - OFFLINE STATIC DATA
# Common WiFi vendors organized by category
# ═══════════════════════════════════════════════════════════════════════════════

# Consumer Router Vendors
CONSUMER_VENDORS = {
    # TP-Link
    '50:C7:BF': 'TP-Link', '98:DA:C4': 'TP-Link', 'B4:FB:E4': 'TP-Link',
    'AC:84:C6': 'TP-Link', '60:E3:27': 'TP-Link', '14:EB:B6': 'TP-Link',
    '30:B5:C2': 'TP-Link', '1C:3B:F3': 'TP-Link', 'C0:E4:2D': 'TP-Link',
    '54:C8:0F': 'TP-Link', 'F4:EC:38': 'TP-Link', 'D8:07:B6': 'TP-Link',
    
    # Netgear
    '00:14:6C': 'Netgear', '20:4E:7F': 'Netgear', '9C:3D:CF': 'Netgear',
    'C4:04:15': 'Netgear', 'E4:F4:C6': 'Netgear', '84:1B:5E': 'Netgear',
    '10:0D:7F': 'Netgear', 'A0:63:91': 'Netgear', '6C:B0:CE': 'Netgear',
    '18:E8:29': 'Netgear', '70:3A:CB': 'Netgear', 'B0:B9:8A': 'Netgear',
    
    # Linksys
    '00:06:25': 'Linksys', '00:0C:41': 'Linksys', '00:12:17': 'Linksys',
    '00:14:BF': 'Linksys', '00:16:B6': 'Linksys', '00:18:39': 'Linksys',
    '00:1A:70': 'Linksys', '00:1C:10': 'Linksys', '00:1E:E5': 'Linksys',
    '00:21:29': 'Linksys', '00:22:6B': 'Linksys', '00:23:69': 'Linksys',
    'C8:D7:19': 'Linksys', 'E8:9F:80': 'Linksys',
    
    # ASUS
    '00:1E:8C': 'ASUS', '00:22:15': 'ASUS', '00:23:54': 'ASUS',
    '00:24:8C': 'ASUS', '08:60:6E': 'ASUS', '10:7B:44': 'ASUS',
    '14:DD:A9': 'ASUS', '1C:87:2C': 'ASUS', '2C:4D:54': 'ASUS',
    '30:85:A9': 'ASUS', '38:2C:4A': 'ASUS', '3C:97:0E': 'ASUS',
    '40:16:7E': 'ASUS', '4C:ED:FB': 'ASUS', '50:46:5D': 'ASUS',
    '54:04:A6': 'ASUS', '60:45:CB': 'ASUS', 'AC:22:0B': 'ASUS',
    
    # D-Link
    '00:05:5D': 'D-Link', '00:0D:88': 'D-Link', '00:11:95': 'D-Link',
    '00:13:46': 'D-Link', '00:15:E9': 'D-Link', '00:17:9A': 'D-Link',
    '00:19:5B': 'D-Link', '00:1B:11': 'D-Link', '00:1C:F0': 'D-Link',
    '00:1E:58': 'D-Link', '00:21:91': 'D-Link', '00:22:B0': 'D-Link',
    '00:24:01': 'D-Link', '00:26:5A': 'D-Link', '14:D6:4D': 'D-Link',
    '1C:7E:E5': 'D-Link', '28:10:7B': 'D-Link', '34:08:04': 'D-Link',
    
    # Belkin
    '00:11:50': 'Belkin', '00:17:3F': 'Belkin', '00:1C:DF': 'Belkin',
    '00:22:75': 'Belkin', '08:86:3B': 'Belkin', '94:10:3E': 'Belkin',
    'B4:75:0E': 'Belkin', 'C0:56:27': 'Belkin', 'EC:1A:59': 'Belkin',
}

# Mesh/Extender Systems
MESH_VENDORS = {
    # eero
    'E4:F0:42': 'eero', 'F0:99:BF': 'eero', '50:DC:E7': 'eero',
    
    # Google Nest/WiFi
    'F4:F5:E8': 'Google Nest', '18:D6:C7': 'Google Nest', '54:60:09': 'Google Nest',
    
    # Netgear Orbi
    '9C:3D:CF': 'Netgear Orbi', '18:E8:29': 'Netgear Orbi', '70:3A:CB': 'Netgear Orbi',
    
    # TP-Link Deco
    'B4:FB:E4': 'TP-Link Deco', 'AC:84:C6': 'TP-Link Deco', '98:DA:C4': 'TP-Link Deco',
    
    # Ubiquiti AmpliFi
    '78:8A:20': 'Ubiquiti AmpliFi', 'E4:38:83': 'Ubiquiti AmpliFi',
    
    # Plume
    '58:D5:6E': 'Plume',
    
    # Velop (Linksys)
    'C8:D7:19': 'Linksys Velop',
}

# Enterprise/Professional
ENTERPRISE_VENDORS = {
    # Cisco
    '00:00:0C': 'Cisco', '00:01:42': 'Cisco', '00:01:43': 'Cisco',
    '00:01:63': 'Cisco', '00:01:64': 'Cisco', '00:01:96': 'Cisco',
    '00:01:97': 'Cisco', '00:01:C7': 'Cisco', '00:01:C9': 'Cisco',
    '00:02:16': 'Cisco', '00:02:17': 'Cisco', '00:02:3D': 'Cisco',
    '00:02:4A': 'Cisco', '00:02:4B': 'Cisco', '00:02:7D': 'Cisco',
    '00:02:7E': 'Cisco', '00:02:B9': 'Cisco', '00:02:BA': 'Cisco',
    '00:03:31': 'Cisco', '00:03:32': 'Cisco', '00:03:6B': 'Cisco',
    '00:03:6C': 'Cisco', '00:03:9F': 'Cisco', '00:03:A0': 'Cisco',
    '00:03:E3': 'Cisco', '00:03:E4': 'Cisco', '00:03:FD': 'Cisco',
    '00:03:FE': 'Cisco', '00:04:27': 'Cisco', '00:04:28': 'Cisco',
    '00:18:74': 'Cisco', '00:1A:1E': 'Cisco', '00:1A:2F': 'Cisco',
    
    # Cisco Meraki
    '88:15:44': 'Cisco Meraki', '0C:8D:DB': 'Cisco Meraki', 'AC:17:C8': 'Cisco Meraki',
    'E0:55:3D': 'Cisco Meraki', '34:56:FE': 'Cisco Meraki', '00:18:0A': 'Cisco Meraki',
    
    # Aruba/HPE
    '00:0B:86': 'Aruba', '00:1A:1E': 'Aruba', '64:D1:54': 'Aruba',
    '6C:F3:7F': 'Aruba', '94:B4:0F': 'Aruba', 'D8:C7:C8': 'Aruba',
    '00:04:96': 'Aruba', '24:DE:C6': 'Aruba', 'F0:61:C0': 'Aruba',
    
    # Ruckus
    '00:24:6C': 'Ruckus', 'EC:58:EA': 'Ruckus', '74:91:1A': 'Ruckus',
    'C4:10:8A': 'Ruckus', '58:B6:33': 'Ruckus', '70:DF:2F': 'Ruckus',
    
    # Ubiquiti
    '78:8A:20': 'Ubiquiti', 'A4:77:33': 'Ubiquiti', '00:15:6D': 'Ubiquiti',
    '00:27:22': 'Ubiquiti', '04:18:D6': 'Ubiquiti', '24:A4:3C': 'Ubiquiti',
    '44:D9:E7': 'Ubiquiti', '60:22:32': 'Ubiquiti', '68:72:51': 'Ubiquiti',
    '74:83:C2': 'Ubiquiti', '74:AC:B9': 'Ubiquiti', '80:2A:A8': 'Ubiquiti',
    'B4:FB:E4': 'Ubiquiti', 'DC:9F:DB': 'Ubiquiti', 'F0:9F:C2': 'Ubiquiti',
    'FC:EC:DA': 'Ubiquiti',
    
    # Extreme Networks
    '00:26:86': 'Extreme Networks', '00:23:69': 'Extreme Networks',
    
    # Juniper/Mist
    '5C:5B:35': 'Juniper Mist', '00:12:1E': 'Juniper', 'F0:1C:2D': 'Juniper',
    
    # Fortinet
    '00:1B:2F': 'Fortinet', '00:21:55': 'Fortinet', '00:09:0F': 'Fortinet',
}

# IoT/Smart Home
IOT_VENDORS = {
    # Amazon/Ring
    '68:54:FD': 'Amazon', '74:C2:46': 'Amazon', 'A0:02:DC': 'Amazon',
    'B4:7C:9C': 'Amazon', 'F0:D2:F1': 'Amazon Echo', '44:65:0D': 'Amazon Echo',
    'FC:65:DE': 'Amazon Echo', '40:B4:CD': 'Amazon Echo', 'B4:E6:2D': 'Ring',
    '68:C6:3A': 'Ring',
    
    # Google/Nest
    '18:B4:30': 'Nest', '50:14:79': 'Nest', '64:16:66': 'Nest',
    'F4:F5:E8': 'Google Home', '54:60:09': 'Google Home',
    
    # Apple HomeKit devices
    '00:03:93': 'Apple', '00:05:02': 'Apple', '00:0A:27': 'Apple',
    '00:0A:95': 'Apple', '00:0D:93': 'Apple', '00:10:FA': 'Apple',
    '00:11:24': 'Apple', '00:14:51': 'Apple', '00:16:CB': 'Apple',
    '00:17:F2': 'Apple', '00:19:E3': 'Apple', '00:1B:63': 'Apple',
    '00:1C:B3': 'Apple', '00:1D:4F': 'Apple', '00:1E:52': 'Apple',
    '00:1F:5B': 'Apple', '00:1F:F3': 'Apple', '00:21:E9': 'Apple',
    '00:22:41': 'Apple', '00:23:12': 'Apple', '00:23:32': 'Apple',
    '00:23:6C': 'Apple', '00:23:DF': 'Apple', '00:24:36': 'Apple',
    '00:25:00': 'Apple', '00:25:4B': 'Apple', '00:25:BC': 'Apple',
    '00:26:08': 'Apple', '00:26:4A': 'Apple', '00:26:B0': 'Apple',
    '00:26:BB': 'Apple', '04:0C:CE': 'Apple', '10:93:E9': 'Apple',
    '14:99:E2': 'Apple', '20:78:F0': 'Apple', '24:A2:E1': 'Apple',
    '28:CF:DA': 'Apple', '34:C0:59': 'Apple', '38:C9:86': 'Apple',
    '3C:15:C2': 'Apple', '44:4C:0C': 'Apple', '48:60:BC': 'Apple',
    '54:26:96': 'Apple', '58:B0:35': 'Apple', '60:03:08': 'Apple',
    '68:A8:6D': 'Apple', '7C:6D:62': 'Apple', '84:78:8B': 'Apple',
    '8C:29:37': 'Apple', '90:27:E4': 'Apple', '98:03:D8': 'Apple',
    'A4:B1:97': 'Apple', 'B8:17:C2': 'Apple', 'C8:2A:14': 'Apple',
    'D4:9D:C0': 'Apple', 'E4:C6:3D': 'Apple', 'F4:F1:5A': 'Apple',
    
    # Philips Hue
    '00:17:88': 'Philips Hue',
    
    # Samsung SmartThings
    '7C:64:56': 'Samsung SmartThings', '00:07:AB': 'Samsung',
    '00:09:18': 'Samsung', '00:12:47': 'Samsung', '00:13:77': 'Samsung',
    '00:15:B9': 'Samsung', '00:17:C9': 'Samsung', '00:18:AF': 'Samsung',
    '00:1A:8A': 'Samsung', '00:1B:98': 'Samsung', '00:1C:43': 'Samsung',
    '00:1D:25': 'Samsung', '00:1D:F6': 'Samsung', '00:1E:7D': 'Samsung',
    '00:1F:CD': 'Samsung', '00:21:19': 'Samsung', '00:21:4C': 'Samsung',
    '00:21:D1': 'Samsung', '00:21:D2': 'Samsung', '00:24:54': 'Samsung',
    '00:24:90': 'Samsung', '00:24:91': 'Samsung', '00:26:37': 'Samsung',
    
    # Sonos
    '00:0E:58': 'Sonos', '5C:AA:FD': 'Sonos', '94:9F:3E': 'Sonos',
    '78:28:CA': 'Sonos', 'B8:E9:37': 'Sonos',
    
    # Wyze
    'D0:73:D5': 'Wyze', '2C:AA:8E': 'Wyze',
    
    # Shelly
    'AC:CF:23': 'Shelly', 'E8:DB:84': 'Shelly',
    
    # TP-Link/Kasa Smart
    '1C:3B:F3': 'TP-Link Kasa', '50:C7:BF': 'TP-Link Kasa',
    
    # Smart TVs
    '70:EE:50': 'LG Electronics', '38:F7:3D': 'LG Electronics',
    '00:E0:91': 'LG Electronics', '10:68:3F': 'LG Electronics',
    '40:B8:9A': 'LG Electronics', '58:A2:B5': 'LG Electronics',
    '64:99:5D': 'LG Electronics', '74:40:BE': 'LG Electronics',
    'AC:0D:1B': 'LG Electronics', 'B4:E6:2A': 'LG Electronics',
    'C4:36:6C': 'LG Electronics', 'CC:2D:8C': 'LG Electronics',
    '08:D4:6A': 'Samsung TV', '10:1D:C0': 'Samsung TV',
    '14:49:E0': 'Samsung TV', '24:C4:4A': 'Samsung TV',
    '30:CD:A7': 'Samsung TV', '40:16:3B': 'Samsung TV',
    '54:88:0E': 'Samsung TV', '5C:49:7D': 'Samsung TV',
    '78:BD:BC': 'Samsung TV', '8C:71:F8': 'Samsung TV',
    'A8:23:FE': 'Samsung TV', 'BC:72:B1': 'Samsung TV',
    'C8:AB:B0': 'Samsung TV', 'E4:7C:F9': 'Samsung TV',
    'F8:04:2E': 'Samsung TV', 'FC:03:9F': 'Samsung TV',
    'EC:FA:5C': 'Sony TV', '78:84:3C': 'Sony TV',
    '30:52:CB': 'Sony TV', '04:5D:4B': 'Sony TV',
    'A4:93:4C': 'Sony TV',
}

# Mobile Device Vendors (for hotspot detection)
MOBILE_VENDORS = {
    # Apple (iPhone/iPad hotspots)
    # (Apple entries also in IOT_VENDORS, these are duplicates for categorization)
    
    # Samsung Mobile
    '00:07:AB': 'Samsung Mobile', '00:09:18': 'Samsung Mobile',
    '00:12:47': 'Samsung Mobile', '00:13:77': 'Samsung Mobile',
    '78:52:1A': 'Samsung Mobile', 'AC:5F:3E': 'Samsung Mobile',
    '14:F4:2A': 'Samsung Mobile', '28:27:BF': 'Samsung Mobile',
    '30:07:4D': 'Samsung Mobile', '40:0E:85': 'Samsung Mobile',
    '50:A4:C8': 'Samsung Mobile', '58:C3:8B': 'Samsung Mobile',
    '64:B3:10': 'Samsung Mobile', '78:25:AD': 'Samsung Mobile',
    '94:63:D1': 'Samsung Mobile', 'A0:39:EE': 'Samsung Mobile',
    'B4:3A:28': 'Samsung Mobile', 'BC:44:86': 'Samsung Mobile',
    'C4:73:1E': 'Samsung Mobile', 'D0:FC:CC': 'Samsung Mobile',
    'E4:58:B8': 'Samsung Mobile', 'FC:A1:83': 'Samsung Mobile',
    
    # OnePlus
    'C0:EE:FB': 'OnePlus', '94:65:2D': 'OnePlus',
    
    # Xiaomi
    '00:9E:C8': 'Xiaomi', '0C:1D:AF': 'Xiaomi', '14:F6:5A': 'Xiaomi',
    '18:59:36': 'Xiaomi', '20:34:FB': 'Xiaomi', '28:6C:07': 'Xiaomi',
    '34:80:B3': 'Xiaomi', '38:A4:ED': 'Xiaomi', '50:8F:4C': 'Xiaomi',
    '58:44:98': 'Xiaomi', '64:09:80': 'Xiaomi', '7C:1D:D9': 'Xiaomi',
    '8C:5A:C1': 'Xiaomi', '98:FA:E3': 'Xiaomi', 'A4:77:33': 'Xiaomi',
    'AC:C1:EE': 'Xiaomi', 'B0:E2:35': 'Xiaomi', 'C4:0B:CB': 'Xiaomi',
    'D4:97:0B': 'Xiaomi', 'E8:AB:FA': 'Xiaomi', 'F0:B4:29': 'Xiaomi',
    'F8:A4:5F': 'Xiaomi',
    
    # Huawei
    '00:18:82': 'Huawei', '00:1E:10': 'Huawei', '00:25:68': 'Huawei',
    '00:25:9E': 'Huawei', '00:34:FE': 'Huawei', '00:46:4B': 'Huawei',
    '00:66:4B': 'Huawei', '04:02:1F': 'Huawei', '04:C0:6F': 'Huawei',
    '04:F9:38': 'Huawei', '08:19:A6': 'Huawei', '08:63:61': 'Huawei',
    '0C:37:DC': 'Huawei', '10:1B:54': 'Huawei', '10:44:00': 'Huawei',
    '10:47:80': 'Huawei', '14:30:04': 'Huawei', '14:A5:1A': 'Huawei',
    '20:08:ED': 'Huawei', '20:0B:C7': 'Huawei', '20:2B:C1': 'Huawei',
    '24:09:95': 'Huawei', '24:1F:A0': 'Huawei', '24:69:A5': 'Huawei',
    '28:31:52': 'Huawei', '28:3C:E4': 'Huawei', '2C:55:D3': 'Huawei',
}

# ISP/Telecom Router Vendors
ISP_VENDORS = {
    # Arris/Motorola (Cable modems)
    '00:00:CA': 'Arris', '00:0C:E5': 'Arris', '00:1A:77': 'Arris',
    '00:1C:C1': 'Arris', '00:1D:CE': 'Arris', '00:1E:5A': 'Arris',
    '00:1F:7E': 'Arris', '00:20:40': 'Arris', '00:23:AF': 'Arris',
    '00:24:A1': 'Arris', '14:AB:F0': 'Arris', '20:3D:66': 'Arris',
    '2C:9E:5F': 'Arris', '30:60:23': 'Arris', '40:B7:F3': 'Arris',
    '54:E2:E0': 'Arris', '5C:57:1A': 'Arris', '64:0F:28': 'Arris',
    '70:03:7E': 'Arris', '84:BB:69': 'Arris', '84:E0:58': 'Arris',
    '90:B1:34': 'Arris', '94:CC:B9': 'Arris', '94:E8:C5': 'Arris',
    'A0:C5:62': 'Arris', 'B4:EE:B4': 'Arris', 'BC:64:4B': 'Arris',
    'C0:05:C2': 'Arris', 'CC:B5:5A': 'Arris', 'E8:65:D4': 'Arris',
    'F8:8B:37': 'Arris',
    
    # Technicolor
    '28:C6:8E': 'Technicolor', '50:39:55': 'Technicolor', '70:F8:E7': 'Technicolor',
    '84:3A:4B': 'Technicolor', '90:01:3B': 'Technicolor', '90:55:DE': 'Technicolor',
    '94:3D:C9': 'Technicolor', 'A0:1B:29': 'Technicolor', 'B0:C7:45': 'Technicolor',
    'FC:94:E3': 'Technicolor',
    
    # Sagemcom
    '18:A6:F7': 'Sagemcom', '30:D3:2D': 'Sagemcom', '34:B1:F7': 'Sagemcom',
    '5C:33:8E': 'Sagemcom', '64:7C:34': 'Sagemcom', '68:A3:78': 'Sagemcom',
    '7C:03:4C': 'Sagemcom', '80:F5:03': 'Sagemcom', '84:26:15': 'Sagemcom',
    '88:03:55': 'Sagemcom', '90:8D:78': 'Sagemcom', 'A8:4E:3F': 'Sagemcom',
    'B0:4E:26': 'Sagemcom', 'C8:91:F9': 'Sagemcom', 'D0:84:B0': 'Sagemcom',
    'E8:F1:B0': 'Sagemcom',
    
    # ZTE
    '00:15:EB': 'ZTE', '00:19:C6': 'ZTE', '00:1E:73': 'ZTE',
    '00:22:93': 'ZTE', '00:25:12': 'ZTE', '00:26:ED': 'ZTE',
    '34:4B:50': 'ZTE', '54:22:F8': 'ZTE', '58:2A:F7': 'ZTE',
    '68:E1:DC': 'ZTE', '78:31:C1': 'ZTE', '84:74:2A': 'ZTE',
    '90:D8:F3': 'ZTE', 'A0:EC:F9': 'ZTE', 'AC:64:17': 'ZTE',
    'B0:75:D5': 'ZTE', 'C8:64:C7': 'ZTE', 'D0:15:4A': 'ZTE',
    'DC:02:8E': 'ZTE', 'E0:19:54': 'ZTE', 'E8:C7:CF': 'ZTE',
    'F4:B8:A7': 'ZTE', 'F8:4A:BF': 'ZTE',
}


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED OUI TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def _build_oui_table() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Build combined OUI lookup table and type table."""
    oui_table = {}
    type_table = {}
    
    # Add all vendors with their types
    for prefix, name in CONSUMER_VENDORS.items():
        oui_table[prefix.upper()] = name
        type_table[prefix.upper()] = "consumer"
    
    for prefix, name in MESH_VENDORS.items():
        oui_table[prefix.upper()] = name
        type_table[prefix.upper()] = "mesh"
    
    for prefix, name in ENTERPRISE_VENDORS.items():
        oui_table[prefix.upper()] = name
        type_table[prefix.upper()] = "enterprise"
    
    for prefix, name in IOT_VENDORS.items():
        oui_table[prefix.upper()] = name
        type_table[prefix.upper()] = "iot"
    
    for prefix, name in MOBILE_VENDORS.items():
        oui_table[prefix.upper()] = name
        type_table[prefix.upper()] = "mobile"
    
    for prefix, name in ISP_VENDORS.items():
        oui_table[prefix.upper()] = name
        type_table[prefix.upper()] = "isp"
    
    return oui_table, type_table


# Build tables at module load (100% offline)
OUI_TABLE, TYPE_TABLE = _build_oui_table()


# ═══════════════════════════════════════════════════════════════════════════════
# OUI VENDOR INTELLIGENCE MODULE
# ═══════════════════════════════════════════════════════════════════════════════

class OUIVendorIntelligence:
    """
    OUI Vendor Intelligence Module (OUI-IM).
    
    100% OFFLINE - All lookups from static data.
    100% PASSIVE - No network calls.
    """
    
    # Locally administered bit position in first byte
    LOCALLY_ADMINISTERED_BIT = 0x02
    
    # Patterns that suggest randomized MACs
    RANDOMIZED_PATTERNS = {
        # Common randomization prefixes
        '02:', '06:', '0A:', '0E:',
        '12:', '16:', '1A:', '1E:',
        '22:', '26:', '2A:', '2E:',
        '32:', '36:', '3A:', '3E:',
        '42:', '46:', '4A:', '4E:',
        '52:', '56:', '5A:', '5E:',
        '62:', '66:', '6A:', '6E:',
        '72:', '76:', '7A:', '7E:',
        '82:', '86:', '8A:', '8E:',
        '92:', '96:', '9A:', '9E:',
        'A2:', 'A6:', 'AA:', 'AE:',
        'B2:', 'B6:', 'BA:', 'BE:',
        'C2:', 'C6:', 'CA:', 'CE:',
        'D2:', 'D6:', 'DA:', 'DE:',
        'E2:', 'E6:', 'EA:', 'EE:',
        'F2:', 'F6:', 'FA:', 'FE:',
    }
    
    def __init__(self):
        self.oui_table = OUI_TABLE
        self.type_table = TYPE_TABLE
        self.cache: Dict[str, VendorInfo] = {}
    
    def lookup(self, mac_or_bssid: str) -> VendorInfo:
        """
        Look up vendor information for a MAC/BSSID.
        
        100% OFFLINE - Uses static OUI table.
        
        Args:
            mac_or_bssid: MAC address or BSSID (e.g., "AA:BB:CC:DD:EE:FF")
            
        Returns:
            VendorInfo with vendor details
        """
        # Handle None or empty input
        if not mac_or_bssid:
            return VendorInfo(
                name="Unknown",
                prefix="",
                confidence=0.0,
                is_known=False,
                is_randomized=False,
                vendor_type="unknown"
            )
        
        # Normalize MAC
        mac = mac_or_bssid.upper().replace('-', ':')
        
        # Check cache
        if mac in self.cache:
            return self.cache[mac]
        
        # Extract OUI prefix (first 3 bytes)
        prefix = self._extract_prefix(mac)
        
        # Check for randomized MAC
        is_randomized = self._is_randomized_mac(mac)
        
        # Lookup in OUI table
        if prefix in self.oui_table:
            vendor_name = self.oui_table[prefix]
            vendor_type = self.type_table.get(prefix, "consumer")
            confidence = 100.0 if not is_randomized else 30.0
            
            info = VendorInfo(
                name=vendor_name,
                prefix=prefix,
                confidence=confidence,
                is_known=True,
                is_randomized=is_randomized,
                vendor_type=vendor_type
            )
        else:
            # Unknown vendor
            info = VendorInfo(
                name="Unknown",
                prefix=prefix,
                confidence=0.0,
                is_known=False,
                is_randomized=is_randomized,
                vendor_type="unknown"
            )
        
        # Cache result
        self.cache[mac] = info
        return info
    
    def _extract_prefix(self, mac: str) -> str:
        """Extract OUI prefix from MAC address."""
        parts = mac.split(':')
        if len(parts) >= 3:
            return ':'.join(parts[:3]).upper()
        return mac[:8].upper()
    
    def _is_randomized_mac(self, mac: str) -> bool:
        """
        Detect if MAC address is randomized.
        
        Randomized MACs have the locally administered bit set (bit 1 of first byte).
        """
        # Check locally administered bit
        try:
            first_byte = int(mac.split(':')[0], 16)
            if first_byte & self.LOCALLY_ADMINISTERED_BIT:
                return True
        except (ValueError, IndexError):
            pass
        
        # Check common randomization patterns
        mac_upper = mac.upper()
        for pattern in self.RANDOMIZED_PATTERNS:
            if mac_upper.startswith(pattern):
                return True
        
        # Also check if prefix not in OUI table (often indicates randomized)
        prefix = self._extract_prefix(mac)
        if prefix not in self.oui_table:
            # Additional heuristics for randomization
            try:
                first_byte = int(mac.split(':')[0], 16)
                # Odd first nibble with unknown OUI is suspicious
                if first_byte % 2 == 0 and first_byte & self.LOCALLY_ADMINISTERED_BIT:
                    return True
            except (ValueError, IndexError):
                pass
        
        return False
    
    def get_vendor_name(self, mac_or_bssid: str) -> str:
        """Get vendor name for a MAC/BSSID."""
        return self.lookup(mac_or_bssid).name
    
    def get_vendor_type(self, mac_or_bssid: str) -> str:
        """Get vendor type for a MAC/BSSID."""
        return self.lookup(mac_or_bssid).vendor_type
    
    def is_known_vendor(self, mac_or_bssid: str) -> bool:
        """Check if vendor is in OUI table."""
        return self.lookup(mac_or_bssid).is_known
    
    def is_randomized(self, mac_or_bssid: str) -> bool:
        """Check if MAC appears to be randomized."""
        return self.lookup(mac_or_bssid).is_randomized
    
    def calculate_spoof_risk_adjustment(
        self,
        mac: str,
        claimed_vendor: str = "",
        is_hidden: bool = False,
        rssi: int = -70
    ) -> float:
        """
        Calculate spoof risk adjustment based on vendor analysis.
        
        Returns a value to ADD to existing spoof risk score.
        """
        info = self.lookup(mac)
        adjustment = 0.0
        
        # Unknown vendor with hidden SSID and strong signal = suspicious
        if not info.is_known and is_hidden and rssi > -50:
            adjustment += 25.0
        
        # Vendor mismatch (claimed vs OUI)
        if claimed_vendor and info.is_known:
            if claimed_vendor.lower() not in info.name.lower():
                adjustment += 15.0
        
        # Randomized MAC with hidden SSID = suspicious
        if info.is_randomized and is_hidden:
            adjustment += 20.0
        
        # Unknown vendor with very strong signal
        if not info.is_known and rssi > -40:
            adjustment += 10.0
        
        return min(adjustment, 50.0)  # Cap at 50
    
    def calculate_rogue_risk_adjustment(
        self,
        mac: str,
        is_hidden: bool = False,
        rssi: int = -70,
        channel: int = 6
    ) -> float:
        """
        Calculate rogue risk adjustment based on vendor analysis.
        
        Returns a value to ADD to existing rogue risk score.
        """
        info = self.lookup(mac)
        adjustment = 0.0
        
        # Unknown vendor + hidden + strong signal = rogue candidate
        if not info.is_known and is_hidden and rssi > -50:
            adjustment += 30.0
        
        # Randomized MAC on infrastructure (not client)
        if info.is_randomized:
            adjustment += 15.0
        
        # Unknown enterprise-like behavior
        if not info.is_known and channel in {36, 40, 44, 48, 149, 153, 157, 161}:
            # 5GHz backhaul channel without known vendor
            adjustment += 10.0
        
        return min(adjustment, 50.0)
    
    def calculate_cluster_score_adjustment(
        self,
        mac: str,
        cluster_vendor: str
    ) -> float:
        """
        Calculate cluster score adjustment based on vendor matching.
        
        Returns a bonus if vendor matches cluster's predominant vendor.
        """
        info = self.lookup(mac)
        
        if not info.is_known:
            return -10.0  # Unknown vendor reduces cluster confidence
        
        if info.name.lower() == cluster_vendor.lower():
            return 20.0  # Same vendor boosts cluster confidence
        
        if info.vendor_type == "mesh" and cluster_vendor:
            # Different mesh vendors in same cluster is suspicious
            return -5.0
        
        return 0.0
    
    def get_statistics(self) -> dict:
        """Get OUI database statistics."""
        return {
            'total_ouis': len(self.oui_table),
            'consumer_count': len(CONSUMER_VENDORS),
            'mesh_count': len(MESH_VENDORS),
            'enterprise_count': len(ENTERPRISE_VENDORS),
            'iot_count': len(IOT_VENDORS),
            'mobile_count': len(MOBILE_VENDORS),
            'isp_count': len(ISP_VENDORS),
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """Clear the lookup cache."""
        self.cache.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_oui_im: Optional[OUIVendorIntelligence] = None


def get_oui_intelligence() -> OUIVendorIntelligence:
    """Get global OUI-IM instance."""
    global _oui_im
    if _oui_im is None:
        _oui_im = OUIVendorIntelligence()
    return _oui_im


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def lookup_vendor(mac_or_bssid: str) -> VendorInfo:
    """Quick vendor lookup using global instance."""
    return get_oui_intelligence().lookup(mac_or_bssid)


def get_vendor_name(mac_or_bssid: str) -> str:
    """Quick vendor name lookup."""
    return get_oui_intelligence().get_vendor_name(mac_or_bssid)


def is_randomized_mac(mac_or_bssid: str) -> bool:
    """Quick randomized MAC check."""
    return get_oui_intelligence().is_randomized(mac_or_bssid)
