"""
Scanner interface and factory for Nexus WiFi Radar.

Provides an abstract Scanner base class and a factory function
to get the appropriate scanner for the current platform.
"""

import platform
import sys
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
import time

from nexus.core.models import Network, ScanResult


class Scanner(ABC):
    """
    Abstract base class for WiFi scanners.
    
    Implement this interface for platform-specific scanning.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the scanner name/type."""
        pass
    
    @property
    @abstractmethod
    def platform(self) -> str:
        """Return the platform this scanner is for."""
        pass
    
    @abstractmethod
    def scan(self, timeout: float = 10.0) -> ScanResult:
        """
        Perform a WiFi scan.
        
        Args:
            timeout: Maximum time to scan in seconds
            
        Returns:
            ScanResult containing discovered networks
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this scanner can run on the current system.
        
        Returns:
            True if the scanner is available and functional
        """
        pass
    
    def scan_continuous(self, interval: float = 5.0, callback=None):
        """
        Perform continuous scanning with callbacks.
        
        Args:
            interval: Time between scans in seconds
            callback: Function to call with each ScanResult
            
        Yields:
            ScanResult for each scan iteration
        """
        while True:
            result = self.scan()
            if callback:
                callback(result)
            yield result
            time.sleep(interval)


def get_scanner(prefer_scapy: bool = True) -> Scanner:
    """
    Factory function to get the appropriate scanner for the current platform.
    
    Args:
        prefer_scapy: If True, prefer Scapy-based scanning when available
        
    Returns:
        Scanner instance appropriate for the current platform
        
    Raises:
        RuntimeError: If no suitable scanner is available
    """
    system = platform.system().lower()
    
    if system == "windows":
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=prefer_scapy)
        if scanner.is_available():
            return scanner
    
    elif system == "linux":
        # Check if running on Raspberry Pi
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
                if "Raspberry Pi" in cpuinfo or "BCM" in cpuinfo:
                    from nexus.platform.raspberry_pi import PiScanner
                    scanner = PiScanner()
                    if scanner.is_available():
                        return scanner
        except (FileNotFoundError, PermissionError):
            pass
        
        # Generic Linux
        from nexus.platform.generic_linux import LinuxScanner
        scanner = LinuxScanner()
        if scanner.is_available():
            return scanner
    
    elif system == "darwin":
        # macOS - use generic Linux scanner with airport
        from nexus.platform.generic_linux import LinuxScanner
        scanner = LinuxScanner()
        if scanner.is_available():
            return scanner
    
    raise RuntimeError(
        f"No suitable WiFi scanner available for platform: {system}. "
        "Please ensure you have the required dependencies installed."
    )


def get_available_scanners() -> List[Scanner]:
    """
    Get a list of all available scanners on the current system.
    
    Returns:
        List of Scanner instances that are available
    """
    available = []
    system = platform.system().lower()
    
    if system == "windows":
        from nexus.platform.windows import WindowsScanner
        for use_scapy in [True, False]:
            scanner = WindowsScanner(use_scapy=use_scapy)
            if scanner.is_available():
                available.append(scanner)
    
    if system == "linux":
        from nexus.platform.generic_linux import LinuxScanner
        from nexus.platform.raspberry_pi import PiScanner
        
        for scanner_cls in [LinuxScanner, PiScanner]:
            scanner = scanner_cls()
            if scanner.is_available():
                available.append(scanner)
    
    return available
