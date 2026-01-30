"""
Raspberry Pi WiFi scanner implementation.

Optimized for Raspberry Pi hardware with support for monitor mode
and external WiFi adapters.
"""

import os
import re
import subprocess
import time
from datetime import datetime
from typing import List, Optional

from nexus.core.scan import Scanner
from nexus.core.models import Network, ScanResult, SecurityType
from nexus.core.vendor import lookup_vendor
from nexus.core.logging import get_logger

logger = get_logger(__name__)


class PiScanner(Scanner):
    """
    Raspberry Pi specific WiFi scanner.
    
    Extends LinuxScanner with Pi-specific optimizations:
    - Support for built-in WiFi (brcmfmac)
    - External USB adapter detection
    - Headless operation mode
    """
    
    def __init__(self, interface: Optional[str] = None):
        """
        Initialize Pi scanner.
        
        Args:
            interface: WiFi interface name (auto-detected if None)
        """
        self._interface = interface or self._detect_interface()
    
    @property
    def name(self) -> str:
        return "PiScanner"
    
    @property
    def platform(self) -> str:
        return "raspberry_pi"
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
                return "Raspberry Pi" in cpuinfo or "BCM" in cpuinfo
        except (FileNotFoundError, PermissionError):
            return False
    
    def _detect_interface(self) -> str:
        """Auto-detect the WiFi interface."""
        # First, look for external USB adapters (often wlan1)
        for iface in ["wlan1", "wlan0"]:
            if os.path.exists(f"/sys/class/net/{iface}/wireless"):
                return iface
        
        # Try using iw to find interfaces
        try:
            result = subprocess.run(
                ["iw", "dev"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Interface" in line:
                        return line.split()[-1]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return "wlan0"
    
    def is_available(self) -> bool:
        """Check if this scanner can run."""
        if not self._is_raspberry_pi():
            return False
        
        if not self._interface:
            return False
        
        # Check if interface exists
        return os.path.exists(f"/sys/class/net/{self._interface}")
    
    def scan(self, timeout: float = 10.0) -> ScanResult:
        """
        Perform a WiFi scan.
        
        Args:
            timeout: Maximum time to scan in seconds
            
        Returns:
            ScanResult containing discovered networks
        """
        start_time = time.time()
        
        # Try scanning methods in order of preference
        networks = self._scan_wpa_cli()
        
        if not networks:
            networks = self._scan_iwlist()
        
        duration = time.time() - start_time
        
        return ScanResult(
            networks=networks,
            scan_time=datetime.now(),
            duration_seconds=duration,
            scanner_type=self.name,
            platform=self.platform
        )
    
    def _scan_wpa_cli(self) -> List[Network]:
        """Scan using wpa_cli (wpa_supplicant)."""
        networks = []
        
        try:
            # Trigger scan
            result = subprocess.run(
                ["wpa_cli", "-i", self._interface, "scan"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "OK" not in result.stdout:
                return networks
            
            # Wait for scan to complete
            time.sleep(2)
            
            # Get results
            result = subprocess.run(
                ["wpa_cli", "-i", self._interface, "scan_results"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return networks
            
            # Parse results
            # Format: bssid / frequency / signal level / flags / ssid
            for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                parts = line.split("\t")
                if len(parts) >= 5:
                    try:
                        bssid = parts[0]
                        frequency = int(parts[1])
                        rssi = int(parts[2])
                        flags = parts[3]
                        ssid = parts[4] if len(parts) > 4 else ""
                        
                        networks.append(Network(
                            ssid=ssid,
                            bssid=bssid,
                            channel=self._freq_to_channel(frequency),
                            frequency_mhz=frequency,
                            rssi_dbm=rssi,
                            security=self._parse_flags(flags),
                            vendor=lookup_vendor(bssid),
                            last_seen=datetime.now()
                        ))
                    except (ValueError, IndexError):
                        continue
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"wpa_cli scan error: {e}")

        return networks

    def _scan_iwlist(self) -> List[Network]:
        """Scan using iwlist as fallback."""
        networks = []
        
        try:
            result = subprocess.run(
                ["sudo", "iwlist", self._interface, "scan"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return networks
            
            output = result.stdout
            current_network = {}
            
            for line in output.split("\n"):
                line = line.strip()
                
                if line.startswith("Cell"):
                    if current_network.get("bssid"):
                        networks.append(self._create_network_from_dict(current_network))
                    
                    current_network = {}
                    match = re.search(r"Address: ([\w:]+)", line)
                    if match:
                        current_network["bssid"] = match.group(1)
                
                elif "ESSID:" in line:
                    match = re.search(r'ESSID:"(.*)"', line)
                    current_network["ssid"] = match.group(1) if match else ""
                
                elif "Channel:" in line:
                    match = re.search(r"Channel:(\d+)", line)
                    if match:
                        current_network["channel"] = int(match.group(1))
                
                elif "Frequency:" in line:
                    match = re.search(r"Frequency:([\d.]+)", line)
                    if match:
                        current_network["frequency"] = int(float(match.group(1)) * 1000)
                
                elif "Signal level=" in line or "Signal level:" in line:
                    match = re.search(r"Signal level[=:](-?\d+)", line)
                    if match:
                        current_network["rssi"] = int(match.group(1))
                
                elif "Encryption key:" in line:
                    current_network["encrypted"] = "on" in line.lower()
                
                elif "WPA" in line or "WPA2" in line:
                    current_network["wpa"] = True
                    if "WPA2" in line:
                        current_network["wpa2"] = True
            
            if current_network.get("bssid"):
                networks.append(self._create_network_from_dict(current_network))
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"iwlist scan error: {e}")

        return networks

    def _create_network_from_dict(self, data: dict) -> Network:
        """Create Network from parsed dictionary."""
        channel = data.get("channel", 0)
        frequency = data.get("frequency", self._channel_to_freq(channel))
        
        security = SecurityType.OPEN
        if data.get("wpa2"):
            security = SecurityType.WPA2
        elif data.get("wpa"):
            security = SecurityType.WPA
        elif data.get("encrypted"):
            security = SecurityType.WEP
        
        return Network(
            ssid=data.get("ssid", ""),
            bssid=data.get("bssid", ""),
            channel=channel if channel else self._freq_to_channel(frequency),
            frequency_mhz=frequency,
            rssi_dbm=data.get("rssi", -70),
            security=security,
            vendor=lookup_vendor(data.get("bssid", "")),
            last_seen=datetime.now()
        )
    
    def _freq_to_channel(self, freq: int) -> int:
        """Convert frequency to channel number."""
        if freq < 2412:
            return 0
        
        if 2412 <= freq <= 2484:
            if freq == 2484:
                return 14
            return (freq - 2407) // 5
        
        if 5000 <= freq <= 5885:
            return (freq - 5000) // 5
        
        return 0
    
    def _channel_to_freq(self, channel: int) -> int:
        """Convert channel to frequency."""
        if channel <= 0:
            return 0
        
        if 1 <= channel <= 14:
            if channel == 14:
                return 2484
            return 2407 + (channel * 5)
        
        if 36 <= channel <= 177:
            return 5000 + (channel * 5)
        
        return 0
    
    def _parse_flags(self, flags: str) -> SecurityType:
        """Parse security from wpa_cli flags."""
        flags = flags.upper()
        
        if "WPA3" in flags:
            return SecurityType.WPA3
        elif "WPA2" in flags or "RSN" in flags:
            return SecurityType.WPA2
        elif "WPA" in flags:
            return SecurityType.WPA
        elif "WEP" in flags:
            return SecurityType.WEP
        elif flags == "" or "ESS" in flags:
            return SecurityType.OPEN
        
        return SecurityType.UNKNOWN
