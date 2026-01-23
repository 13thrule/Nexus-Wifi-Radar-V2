"""
Vendor lookup from OUI (MAC address prefix) database.

Provides functionality to look up hardware vendor from MAC address.
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict

from nexus.core.config import get_data_dir


# Built-in common OUI prefixes (subset for quick lookups without external file)
# Format: First 3 bytes of MAC (uppercase, no colons) -> Vendor name
COMMON_OUI: Dict[str, str] = {
    # Apple
    "00A040": "Apple",
    "001CB3": "Apple",
    "0023DF": "Apple",
    "002332": "Apple",
    "002436": "Apple",
    "002500": "Apple",
    "0026BB": "Apple",
    "003065": "Apple",
    "003EE1": "Apple",
    "00F76F": "Apple",
    "04E536": "Apple",
    "086698": "Apple",
    "0C74C2": "Apple",
    "109ADD": "Apple",
    "14109F": "Apple",
    "20C9D0": "Apple",
    "24AB81": "Apple",
    "28E02C": "Apple",
    "2CB43A": "Apple",
    "34C059": "Apple",
    "3C0754": "Apple",
    "40A6D9": "Apple",
    "44D884": "Apple",
    "4C57CA": "Apple",
    "502EA6": "Apple",
    "5855CA": "Apple",
    "5C8D4E": "Apple",
    "60C547": "Apple",
    "64B9E8": "Apple",
    "6C94F8": "Apple",
    "70ECE4": "Apple",
    "7831C1": "Apple",
    "78CA39": "Apple",
    "7C6DF8": "Apple",
    "8C7C92": "Apple",
    "9027E4": "Apple",
    "9801A7": "Apple",
    "A85C2C": "Apple",
    "AC87A3": "Apple",
    "B065BD": "Apple",
    "B8E856": "Apple",
    "BC5436": "Apple",
    "C82A14": "Apple",
    "CCD281": "Apple",
    "D02B20": "Apple",
    "D89695": "Apple",
    "DC2B2A": "Apple",
    "E0F5C6": "Apple",
    "E4CE8F": "Apple",
    "F0B479": "Apple",
    "F81EDF": "Apple",
    "FCFC48": "Apple",
    
    # Cisco / Linksys
    "000142": "Cisco",
    "000164": "Cisco",
    "0001C7": "Cisco",
    "000C30": "Cisco",
    "001BD4": "Linksys",
    "002129": "Cisco Linksys",
    "0024B2": "Netgear",
    
    # Intel
    "001E64": "Intel",
    "001F3B": "Intel",
    "0021B7": "Lexmark",
    "002219": "Samsung",
    "002314": "Intel",
    "00248C": "Intel",
    "3C970E": "Intel",
    "4CEB42": "Intel",
    "5C514F": "Intel",
    "606C66": "Intel",
    "6C8814": "Intel",
    "8086F2": "Intel",
    "94659C": "Intel",
    "9C2A83": "Intel",
    "A4C494": "Intel",
    "B4969B": "Intel",
    "DC536C": "Intel",
    "F81654": "Intel",
    
    # TP-Link
    "14CC20": "TP-Link",
    "1C3BF3": "TP-Link",
    "300D43": "TP-Link",
    "50C7BF": "TP-Link",  # Common TP-Link
    "5C899A": "TP-Link",
    "6466B3": "TP-Link",
    "743170": "TP-Link",
    "A842A1": "TP-Link",
    "B09575": "TP-Link",
    "C025E9": "TP-Link",
    "D46E0E": "TP-Link",
    "EC086B": "TP-Link",
    "F4F26D": "TP-Link",
    "60A4B7": "TP-Link",
    "787D0E": "TP-Link",
    "7C8BCA": "TP-Link",
    "8C210A": "TP-Link",
    "B4B024": "TP-Link",
    "C006C3": "TP-Link",
    "DCFE18": "TP-Link",
    
    # Netgear
    "001E2A": "Netgear",
    "00223F": "Netgear",
    "002438": "Netgear",
    "008EF2": "Netgear",
    "204E7F": "Netgear",
    "28C68E": "Netgear",
    "4494FC": "Netgear",
    "6038E0": "Netgear",
    "6CB0CE": "Netgear",
    "9CC9EB": "Netgear",
    "A00460": "Netgear",
    "C03F0E": "Netgear",
    "E4F4C6": "Netgear",
    
    # Asus
    "000C6E": "Asus",
    "000E5E": "Asus",
    "0011D8": "Asus",
    "00152F": "Asus",
    "001731": "Asus",
    "001A92": "Asus",
    "001E8C": "Asus",
    "002354": "Asus",
    "1C872C": "Asus",
    "2C56DC": "Asus",
    "3085A9": "Asus",
    "485B39": "Asus",
    "54040E": "Asus",
    "AC9E17": "Asus",
    "BCEE7B": "Asus",
    "E03F49": "Asus",
    
    # D-Link
    "0015E9": "D-Link",
    "00179A": "D-Link",
    "001CF0": "D-Link",
    "001E58": "D-Link",
    "002401": "D-Link",
    "00265A": "D-Link",
    "1CAFF7": "D-Link",
    "28107B": "D-Link",
    "340804": "D-Link",
    "5CD998": "D-Link",
    "78542E": "D-Link",
    "9094E4": "D-Link",
    "C8BE19": "D-Link",
    
    # Samsung
    "0007AB": "Samsung",
    "000D6F": "Samsung",
    "000E6D": "Samsung",
    "001247": "Samsung",
    "001632": "Samsung",
    "0017D5": "Samsung",
    "001A8A": "Samsung",
    "001E7D": "Samsung",
    "002339": "Samsung",
    "002566": "Samsung",
    "5C0A5B": "Samsung",
    "6C2F2C": "Samsung",
    "78D6F0": "Samsung",
    "84119E": "Samsung",
    "94350A": "Samsung",
    "A8F274": "Samsung",
    "C44619": "Samsung",
    "D0176A": "Samsung",
    "F02A61": "Samsung",
    
    # Huawei
    "001E10": "Huawei",
    "002568": "Huawei",
    "04C06F": "Huawei",
    "0C37DC": "Huawei",
    "10C61F": "Huawei",
    "20F17C": "Huawei",
    "24DB96": "Huawei",
    "34CDBE": "Huawei",
    "4C5499": "Huawei",
    "582AF7": "Huawei",
    "706A0A": "Huawei",
    "80B686": "Huawei",
    "88CEFA": "Huawei",
    "AC853D": "Huawei",
    "C8D15E": "Huawei",
    "E0247F": "Huawei",
    "F4C714": "Huawei",
    
    # Microsoft
    "0050F2": "Microsoft",
    "001DD8": "Microsoft",
    "002635": "Microsoft",
    "28188D": "Microsoft",
    "3CDA2A": "Microsoft",
    "50D94F": "Microsoft",
    "6045BD": "Microsoft",
    "7CED8D": "Microsoft",
    "98E743": "Microsoft",
    "B4AE2B": "Microsoft",
    "C8D9D2": "Microsoft",
    
    # Google
    "001A11": "Google",
    "3C5AB4": "Google",
    "54609A": "Google",
    "A47733": "Google",
    "F4F5E8": "Google",
    
    # Amazon / Ring
    "0050F5": "Amazon Echo",
    "38F73D": "Amazon Echo",
    "407D0F": "Amazon Fire",
    "6854FD": "Amazon Echo",
    "747548": "Amazon Fire",
    "84D6D0": "Amazon Echo",
    "B47C9C": "Amazon Echo",
    "F0272D": "Amazon Fire",
    "FC65DE": "Amazon Fire",
    # Ring (Amazon subsidiary)
    "3C6A2C": "Ring Doorbell",
    "444E6D": "Ring Camera",
    "A0D0DC": "Ring Chime",
    "1CAE3E": "Ring Device",
    "B86D83": "Ring Device",
    "94F39E": "Ring Doorbell",
    "F44F77": "Ring Device",
    "E8C8CD": "Ring Camera",
    "98F4AB": "Ring Doorbell",
    # Amazon Sidewalk (IoT mesh)
    "34D270": "Amazon Sidewalk",
    "44CB8B": "Amazon Sidewalk",
    "7CD566": "Amazon Sidewalk",
    # Blink (Amazon)
    "58B1F4": "Blink Camera",
    "0C75BD": "Blink Camera",
    "D43639": "Blink Camera",
    
    # Xiaomi
    "0C1DAF": "Xiaomi",
    "14F65A": "Xiaomi",
    "286C07": "Xiaomi",
    "34CE00": "Xiaomi",
    "640980": "Xiaomi",
    "7C1DD9": "Xiaomi",
    "8CBEBE": "Xiaomi",
    "AC64DD": "Xiaomi",
    "F48B32": "Xiaomi",
    
    # Ubiquiti
    "00156D": "Ubiquiti",
    "002722": "Ubiquiti",
    "04180F": "Ubiquiti",
    "24A43C": "Ubiquiti",
    "44D9E7": "Ubiquiti",
    "687251": "Ubiquiti",
    "802AA8": "Ubiquiti",
    "B4FBE4": "Ubiquiti",
    "DC9FDB": "Ubiquiti",
    "F4E2C6": "Ubiquiti",
    "FCECDA": "Ubiquiti",
    
    # BT (British Telecom) / EE / Plusnet - UK ISP routers
    "CCD42E": "BT Hub",
    "72D42E": "BT Hub",  # BT Smart Hub variant
    "30D3F7": "BT Hub",
    "AC5A14": "BT Hub",
    "C0F188": "BT Hub",
    "00BF61": "BT Hub",
    "087190": "BT Hub",
    "C4415A": "EE Router",
    "F8DFA8": "EE Router",
    "80FB06": "EE Router",
    "48F8E1": "EE Router",
    "BC9680": "Plusnet Router",
    "E091F5": "Plusnet Router",
    
    # Virgin Media / Sky UK
    "C0053A": "Virgin Media",
    "CC2D21": "Virgin Media",
    "E0B9BA": "Virgin Media",
    "60B4F7": "Virgin Media",
    "B4EAC1": "Virgin Media",
    "0018E7": "Sky Router",
    "D0A0D6": "Sky Router",
    "D437D7": "Sky Router",
    "F4968D": "Sky Router",
    "C4B8B4": "Sky Router",
    
    # TalkTalk / Vodafone UK
    "80CC9C": "TalkTalk Router",
    "BCF2AF": "TalkTalk Router",
    "3C6200": "TalkTalk Router",
    "A4934C": "Vodafone Router",
    "B0EEB5": "Vodafone Router",
    "00241E": "Vodafone Router",
    
    # Arris / Motorola / Technicolor (common cable modems)
    "00E09C": "Arris",
    "0050E3": "Arris",
    "20E571": "Arris",
    "3C36E4": "Arris",
    "6CCB46": "Arris",
    "E8B2AC": "Arris",
    "001E46": "Motorola",
    "CC61E5": "Motorola",
    "1C1B0D": "Technicolor",
    "78D3D3": "Technicolor",
    
    # D-Link
    "00055D": "D-Link",
    "001B11": "D-Link",
    "001CF0": "D-Link",
    "00265A": "D-Link",
    "00AD24": "D-Link",
    "1C5F2B": "D-Link",
    "28107B": "D-Link",
    "340804": "D-Link",
    "5CD998": "D-Link",
    "78542E": "D-Link",
    "B8A386": "D-Link",
    "C0A0BB": "D-Link",
    "C4E903": "D-Link",
    
    # Belkin / Linksys (Foxconn)
    "001150": "Belkin",
    "001CDF": "Belkin",
    "08863B": "Belkin",
    "94103E": "Belkin",
    "B4750E": "Belkin",
    "002275": "Linksys",
    "00121C": "Linksys",
    "001839": "Linksys",
    "0024E2": "Linksys",
    "48F17F": "Linksys",
    "6C7220": "Linksys",
    "C0C1C0": "Linksys",
    
    # ZTE
    "000C43": "ZTE",
    "0015EB": "ZTE",
    "001E73": "ZTE",
    "002293": "ZTE",
    "00265E": "ZTE",
    "006057": "ZTE",
    "24C44A": "ZTE",
    "482C10": "ZTE",
    "744AA4": "ZTE",
    "9CC9EB": "ZTE",
    
    # HP / Hewlett-Packard
    "000102": "HP",
    "001083": "HP",
    "0014C2": "HP",
    "001635": "HP",
    "001A4B": "HP",
    "001B78": "HP",
    "0030C1": "HP",
    "1CC1DE": "HP",
    "3464A9": "HP",
    "8C8590": "HP",
    "B499BA": "HP",
    "D8D385": "HP",
    
    # Intel
    "001F3B": "Intel",
    "002553": "Intel",
    "5CA6E6": "Intel",
    "00155D": "Intel",
    "001111": "Intel",
    "00088B": "Intel",
    "001517": "Intel",
    "001700": "Intel",
    "00180F": "Intel",
    "002314": "Intel",
    "3C6278": "Intel",
    "606720": "Intel",
    "80C5F2": "Intel",
    "94E6F7": "Intel",
    "A4C494": "Intel",
    "B44BD2": "Intel",
    "F8633F": "Intel",
    
    # Realtek
    "00E04C": "Realtek",
    "00E074": "Realtek",
    "001E8C": "Realtek",
    "002618": "Realtek",
    "52540F": "Realtek",
    "7CC2C6": "Realtek",
    "900325": "Realtek",
    
    # Qualcomm / Atheros
    "001371": "Qualcomm",
    "003C9D": "Qualcomm",
    "4C0BBE": "Qualcomm",
    "000B86": "Atheros",
    "001A6C": "Atheros",
    "00248C": "Atheros",
    "7843EF": "Atheros",
    
    # MediaTek / Ralink
    "000CFC": "MediaTek",
    "00E087": "MediaTek",
    "2C56DC": "MediaTek",
    "000E8E": "Ralink",
    "001C10": "Ralink",
    
    # Aruba / Ruckus / Cambium (Enterprise WiFi)
    "000B86": "Aruba",
    "002128": "Aruba",
    "00246C": "Aruba",
    "002432": "Aruba",
    "6CB7F4": "Aruba",
    "9C1C12": "Aruba",
    "D8C7C8": "Aruba",
    "00254C": "Ruckus",
    "5C5B35": "Ruckus",
    "C4108F": "Ruckus",
    "EC8EAE": "Ruckus",
    "0004F2": "Cambium",
    "58C175": "Cambium",
    "DC4436": "Cambium",
    "000496": "Cambium",
    "00A0F8": "Cambium",
    "8C7F3B": "Cambium",
    "0019D2": "Cambium",
    
    # AVM FRITZ!Box (German routers)
    "2424FF": "AVM FRITZ!Box",
    "3C3786": "AVM FRITZ!Box",
    "442C05": "AVM FRITZ!Box",
    "54040E": "AVM FRITZ!Box",
    "B0487A": "AVM FRITZ!Box",
    "C80E14": "AVM FRITZ!Box",
    "CCC50A": "AVM FRITZ!Box",
    
    # Synology / QNAP (NAS with WiFi)
    "001132": "Synology",
    "0011B7": "Synology",
    "001D09": "QNAP",
    "24528A": "QNAP",
    
    # Additional common routers/APs found in UK/EU
    "80EA0B": "Shenzhen RF-Link",  # Various consumer routers
    "F0090D": "Zhongshan Linkpro",  # Consumer routers  
    "0C8E29": "Shenzhen Gongjin",   # Common OEM router manufacturer (BT, etc)
    "1C872C": "ASUSTek",
    "2CFDA1": "ASUSTek",
    "7824AF": "ASUSTek",
    "AC9E17": "ASUSTek",
    "E03F49": "ASUSTek",
    "04D9F5": "ASUSTek",
    "049226": "ASUSTek",
    "083E5D": "ASUSTek",
    "1C3BF3": "ASUSTek",
    
    # Sagemcom (ISP routers)
    "001E80": "Sagemcom",
    "3C814F": "Sagemcom",
    "68A378": "Sagemcom",
    "8424B2": "Sagemcom",
    "A84E3F": "Sagemcom",
    "B0E739": "Sagemcom",
    "F8B568": "Sagemcom",
    
    # Arcadyan (ISP router ODM)
    "001A2A": "Arcadyan",
    "14CC20": "Arcadyan",
    "74317F": "Arcadyan",
    "88719C": "Arcadyan",
    "D03745": "Arcadyan",
    
    # Sercomm (ISP router ODM)  
    "0024D1": "Sercomm",
    "0025D3": "Sercomm",
    "C80E77": "Sercomm",
    "E091F5": "Sercomm",
    
    # Humax (Set-top boxes/routers)
    "00095B": "Humax",
    "001B9E": "Humax",
    "002255": "Humax",
    "98D6BB": "Humax",
    
    # Private/Randomized MAC detection
    "02": "Randomized",  # Local bit set
    "06": "Randomized",
    "0A": "Randomized",
    "0E": "Randomized",
    "12": "Randomized",
    "16": "Randomized",
    "1A": "Randomized",
    "1E": "Randomized",
    "22": "Randomized",
    "26": "Randomized",
    "2A": "Randomized",
    "2E": "Randomized",
    "32": "Randomized",
    "36": "Randomized",
    "3A": "Randomized",
    "3E": "Randomized",
}


class VendorLookup:
    """
    MAC address vendor lookup using OUI database.
    
    Supports both built-in common vendors and external OUI file.
    """
    
    def __init__(self, oui_file: Optional[Path] = None):
        """
        Initialize vendor lookup.
        
        Args:
            oui_file: Path to OUI database file (optional)
        """
        self._extended_oui: Dict[str, str] = {}
        self._oui_file = oui_file
        
        if oui_file and oui_file.exists():
            self._load_oui_file(oui_file)
    
    def _load_oui_file(self, path: Path) -> None:
        """Load extended OUI database from file."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # Standard OUI format: XX-XX-XX (hex) <vendor>
                    match = re.match(r"([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})\s+\(hex\)\s+(.+)", line)
                    if match:
                        oui = (match.group(1) + match.group(2) + match.group(3)).upper()
                        vendor = match.group(4).strip()
                        self._extended_oui[oui] = vendor
        except Exception as e:
            print(f"Warning: Could not load OUI file: {e}")
    
    @staticmethod
    def normalize_mac(mac: str) -> str:
        """
        Normalize MAC address to uppercase, no separators.
        
        Args:
            mac: MAC address in any format (e.g., "00:11:22:33:44:55")
            
        Returns:
            Normalized MAC (e.g., "001122334455")
        """
        return re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    
    @staticmethod
    def get_oui(mac: str) -> str:
        """
        Extract OUI (first 3 bytes) from MAC address.
        
        Args:
            mac: MAC address in any format
            
        Returns:
            6-character OUI string
        """
        normalized = VendorLookup.normalize_mac(mac)
        return normalized[:6] if len(normalized) >= 6 else ""
    
    def lookup(self, mac: str) -> str:
        """
        Look up vendor from MAC address.
        
        Args:
            mac: MAC address in any format
            
        Returns:
            Vendor name or "Unknown"
        """
        oui = self.get_oui(mac)
        
        if not oui:
            return "Unknown"
        
        # Check built-in database first (exact match)
        if oui in COMMON_OUI:
            return COMMON_OUI[oui]
        
        # Check extended database (exact match)
        if oui in self._extended_oui:
            return self._extended_oui[oui]
        
        # Check if this is a locally administered MAC (local bit set)
        # Second character being 2, 6, A, or E indicates locally administered
        # This often happens with router guest networks / additional BSSIDs
        if len(oui) >= 2:
            second_char = oui[1].upper()
            if second_char in ['2', '6', 'A', 'E']:
                # Try to find the base OUI by clearing the local bit
                # 2->0, 6->4, A->8, E->C
                base_char_map = {'2': '0', '6': '4', 'A': '8', 'E': 'C'}
                base_oui = oui[0] + base_char_map[second_char] + oui[2:]
                
                # Check if base OUI matches a known vendor
                if base_oui in COMMON_OUI:
                    return COMMON_OUI[base_oui]
                if base_oui in self._extended_oui:
                    return self._extended_oui[base_oui]
                
                # No base match found - likely a randomized mobile MAC
                return "Private/Random"
        
        return "Unknown"
    
    def lookup_batch(self, macs: list) -> Dict[str, str]:
        """
        Look up vendors for multiple MAC addresses.
        
        Args:
            macs: List of MAC addresses
            
        Returns:
            Dictionary mapping MAC -> vendor
        """
        return {mac: self.lookup(mac) for mac in macs}


# Global vendor lookup instance (lazy loaded)
_vendor_lookup: Optional[VendorLookup] = None


def get_vendor_lookup() -> VendorLookup:
    """Get the global vendor lookup instance."""
    global _vendor_lookup
    if _vendor_lookup is None:
        oui_path = get_data_dir() / "oui.txt"
        _vendor_lookup = VendorLookup(oui_path if oui_path.exists() else None)
    return _vendor_lookup


def lookup_vendor(mac: str) -> str:
    """
    Convenience function to look up vendor from MAC address.
    
    Args:
        mac: MAC address in any format
        
    Returns:
        Vendor name or "Unknown"
    """
    return get_vendor_lookup().lookup(mac)
