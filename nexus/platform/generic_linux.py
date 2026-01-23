"""
Generic Linux WiFi scanner implementation.

Uses nmcli, iwlist, or iw for scanning depending on availability.
"""

import re
import subprocess
import time
from datetime import datetime
from typing import List, Optional

from nexus.core.scan import Scanner
from nexus.core.models import Network, ScanResult, SecurityType
from nexus.core.vendor import lookup_vendor


class LinuxScanner(Scanner):
    """
    Linux WiFi scanner using standard tools.
    
    Supports multiple backends:
    - nmcli: NetworkManager CLI (preferred, no root required)
    - iwlist: Wireless tools (may require root)
    - iw: Modern wireless tools (may require root)
    """
    
    def __init__(self, interface: Optional[str] = None):
        """
        Initialize Linux scanner.
        
        Args:
            interface: WiFi interface name (auto-detected if None)
        """
        self._interface = interface or self._detect_interface()
        self._backend = self._detect_backend()
    
    @property
    def name(self) -> str:
        return f"LinuxScanner ({self._backend})"
    
    @property
    def platform(self) -> str:
        return "linux"
    
    def _detect_interface(self) -> str:
        """Auto-detect the WiFi interface."""
        try:
            # Try using iw
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
        
        try:
            # Try using iwconfig
            result = subprocess.run(
                ["iwconfig"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "IEEE 802.11" in line:
                        return line.split()[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Default fallback
        return "wlan0"
    
    def _detect_backend(self) -> str:
        """Detect available scanning backend."""
        # Prefer nmcli as it doesn't require root
        try:
            result = subprocess.run(
                ["nmcli", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "nmcli"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try iw
        try:
            result = subprocess.run(
                ["iw", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "iw"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fall back to iwlist
        return "iwlist"
    
    def is_available(self) -> bool:
        """Check if this scanner can run."""
        if not self._interface:
            return False
        
        if self._backend == "nmcli":
            try:
                result = subprocess.run(
                    ["nmcli", "device", "wifi", "list"],
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
        
        return True
    
    def scan(self, timeout: float = 10.0) -> ScanResult:
        """
        Perform a WiFi scan.
        
        Args:
            timeout: Maximum time to scan in seconds
            
        Returns:
            ScanResult containing discovered networks
        """
        start_time = time.time()
        
        if self._backend == "nmcli":
            networks = self._scan_nmcli()
        elif self._backend == "iw":
            networks = self._scan_iw()
        else:
            networks = self._scan_iwlist()
        
        duration = time.time() - start_time
        
        return ScanResult(
            networks=networks,
            scan_time=datetime.now(),
            duration_seconds=duration,
            scanner_type=self.name,
            platform=self.platform
        )
    
    def _scan_nmcli(self) -> List[Network]:
        """Scan using nmcli (NetworkManager)."""
        networks = []
        
        try:
            # Rescan first
            subprocess.run(
                ["nmcli", "device", "wifi", "rescan"],
                capture_output=True,
                timeout=10
            )
            
            # Get results
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "device", "wifi", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return networks
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split(":")
                if len(parts) >= 6:
                    ssid = parts[0]
                    bssid = ":".join(parts[1:7])  # Reconstruct BSSID with colons
                    remaining = ":".join(parts[7:])
                    
                    # Parse remaining fields
                    rem_parts = remaining.split(":")
                    if len(rem_parts) >= 4:
                        try:
                            channel = int(rem_parts[0])
                            freq_str = rem_parts[1].replace(" MHz", "")
                            frequency = int(freq_str) if freq_str.isdigit() else self._channel_to_freq(channel)
                            signal_pct = int(rem_parts[2])
                            security_str = rem_parts[3] if len(rem_parts) > 3 else ""
                            
                            networks.append(Network(
                                ssid=ssid,
                                bssid=bssid,
                                channel=channel,
                                frequency_mhz=frequency,
                                rssi_dbm=int(-90 + (signal_pct * 0.6)),
                                security=self._parse_security(security_str),
                                vendor=lookup_vendor(bssid),
                                last_seen=datetime.now()
                            ))
                        except (ValueError, IndexError):
                            continue
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"nmcli scan error: {e}")
        
        return networks
    
    def _scan_iwlist(self) -> List[Network]:
        """Scan using iwlist."""
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
            
            # Parse iwlist output
            current_network = {}
            
            for line in output.split("\n"):
                line = line.strip()
                
                if line.startswith("Cell"):
                    # Save previous network
                    if current_network.get("bssid"):
                        networks.append(self._create_network_from_dict(current_network))
                    
                    current_network = {}
                    match = re.search(r"Address: ([\w:]+)", line)
                    if match:
                        current_network["bssid"] = match.group(1)
                
                elif "ESSID:" in line:
                    match = re.search(r'ESSID:"(.+)"', line)
                    if match:
                        current_network["ssid"] = match.group(1)
                    else:
                        current_network["ssid"] = ""
                
                elif "Channel:" in line:
                    match = re.search(r"Channel:(\d+)", line)
                    if match:
                        current_network["channel"] = int(match.group(1))
                
                elif "Frequency:" in line:
                    match = re.search(r"Frequency:([\d.]+)", line)
                    if match:
                        current_network["frequency"] = int(float(match.group(1)) * 1000)
                
                elif "Signal level=" in line:
                    match = re.search(r"Signal level[=:](-?\d+)", line)
                    if match:
                        current_network["rssi"] = int(match.group(1))
                
                elif "Encryption key:" in line:
                    current_network["encrypted"] = "on" in line.lower()
                
                elif "WPA" in line:
                    current_network["wpa"] = True
                    if "WPA2" in line:
                        current_network["wpa2"] = True
            
            # Don't forget the last network
            if current_network.get("bssid"):
                networks.append(self._create_network_from_dict(current_network))
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"iwlist scan error: {e}")
        
        return networks
    
    def _scan_iw(self) -> List[Network]:
        """Scan using iw command."""
        networks = []
        
        try:
            result = subprocess.run(
                ["sudo", "iw", self._interface, "scan"],
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
                
                if line.startswith("BSS"):
                    # Save previous network
                    if current_network.get("bssid"):
                        networks.append(self._create_network_from_dict(current_network))
                    
                    current_network = {}
                    match = re.search(r"BSS ([\w:]+)", line)
                    if match:
                        current_network["bssid"] = match.group(1)
                
                elif line.startswith("SSID:"):
                    current_network["ssid"] = line.split(":", 1)[1].strip()
                
                elif line.startswith("freq:"):
                    try:
                        current_network["frequency"] = int(line.split(":")[1].strip())
                    except ValueError:
                        pass
                
                elif line.startswith("signal:"):
                    match = re.search(r"(-?\d+)", line)
                    if match:
                        current_network["rssi"] = int(match.group(1))
                
                elif "WPA" in line or "RSN" in line:
                    current_network["wpa"] = True
                    if "RSN" in line:
                        current_network["wpa2"] = True
            
            # Don't forget the last network
            if current_network.get("bssid"):
                networks.append(self._create_network_from_dict(current_network))
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"iw scan error: {e}")
        
        return networks
    
    def _create_network_from_dict(self, data: dict) -> Network:
        """Create Network object from parsed dictionary."""
        channel = data.get("channel", 0)
        frequency = data.get("frequency", self._channel_to_freq(channel))
        
        # Determine security type
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
    
    def _channel_to_freq(self, channel: int) -> int:
        """Convert WiFi channel to frequency in MHz."""
        if channel <= 0:
            return 0
        
        if 1 <= channel <= 14:
            if channel == 14:
                return 2484
            return 2407 + (channel * 5)
        
        if 36 <= channel <= 177:
            return 5000 + (channel * 5)
        
        return 0
    
    def _freq_to_channel(self, freq: int) -> int:
        """Convert frequency to WiFi channel."""
        if freq < 2412:
            return 0
        
        if 2412 <= freq <= 2484:
            if freq == 2484:
                return 14
            return (freq - 2407) // 5
        
        if 5000 <= freq <= 5885:
            return (freq - 5000) // 5
        
        return 0
    
    def _parse_security(self, security_str: str) -> SecurityType:
        """Parse security type from string."""
        security_str = security_str.upper()
        
        if "WPA3" in security_str:
            return SecurityType.WPA3
        elif "WPA2" in security_str:
            return SecurityType.WPA2
        elif "WPA" in security_str:
            return SecurityType.WPA
        elif "WEP" in security_str:
            return SecurityType.WEP
        elif security_str == "" or "OPEN" in security_str:
            return SecurityType.OPEN
        
        return SecurityType.UNKNOWN
