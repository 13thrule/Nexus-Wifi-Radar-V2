"""
Data models for Nexus WiFi Radar.

Defines the core dataclasses used throughout the application:
- Network: Represents a discovered WiFi network
- Threat: Represents a security threat
- ScanResult: Container for scan results with metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json


class SecurityType(Enum):
    """WiFi security/encryption types."""
    OPEN = "Open"
    WEP = "WEP"
    WPA = "WPA"
    WPA2 = "WPA2"
    WPA3 = "WPA3"
    WPA2_ENTERPRISE = "WPA2-Enterprise"
    WPA3_ENTERPRISE = "WPA3-Enterprise"
    UNKNOWN = "Unknown"


class ThreatSeverity(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(Enum):
    """Threat category types."""
    WEAK_ENCRYPTION = "weak_encryption"
    SSID_SPOOFING = "ssid_spoofing"
    ROGUE_AP = "rogue_ap"
    CHANNEL_ANOMALY = "channel_anomaly"
    HIDDEN_NETWORK = "hidden_network"
    SIGNAL_ANOMALY = "signal_anomaly"


@dataclass
class Network:
    """
    Represents a discovered WiFi network.
    
    Attributes:
        ssid: Network name (may be empty for hidden networks)
        bssid: MAC address of the access point
        channel: WiFi channel number
        frequency_mhz: Frequency in MHz (e.g., 2437 for channel 6)
        rssi_dbm: Signal strength in dBm (negative value)
        security: Security/encryption type
        vendor: Hardware vendor from OUI lookup
        last_seen: Timestamp of last detection
    """
    ssid: str
    bssid: str
    channel: int
    frequency_mhz: int
    rssi_dbm: int
    security: SecurityType = SecurityType.UNKNOWN
    vendor: str = "Unknown"
    last_seen: datetime = field(default_factory=datetime.now)
    
    @property
    def signal_percent(self) -> int:
        """Convert RSSI dBm to percentage (0-100)."""
        # Typical range: -30 dBm (excellent) to -90 dBm (unusable)
        # Clamp to reasonable range
        rssi = max(-90, min(-30, self.rssi_dbm))
        return int((rssi + 90) * 100 / 60)
    
    @property
    def signal_quality(self) -> str:
        """Get human-readable signal quality."""
        pct = self.signal_percent
        if pct >= 80:
            return "Excellent"
        elif pct >= 60:
            return "Good"
        elif pct >= 40:
            return "Fair"
        else:
            return "Weak"
    
    @property
    def band(self) -> str:
        """Get frequency band (2.4GHz or 5GHz)."""
        if self.frequency_mhz < 3000:
            return "2.4GHz"
        else:
            return "5GHz"
    
    @property
    def is_hidden(self) -> bool:
        """Check if this is a hidden network."""
        return not self.ssid or self.ssid.strip() == ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ssid": self.ssid,
            "bssid": self.bssid,
            "channel": self.channel,
            "frequency_mhz": self.frequency_mhz,
            "rssi_dbm": self.rssi_dbm,
            "signal_percent": self.signal_percent,
            "security": self.security.value,
            "vendor": self.vendor,
            "band": self.band,
            "last_seen": self.last_seen.isoformat(),
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict) -> "Network":
        """Create Network from dictionary."""
        return cls(
            ssid=data["ssid"],
            bssid=data["bssid"],
            channel=data["channel"],
            frequency_mhz=data["frequency_mhz"],
            rssi_dbm=data["rssi_dbm"],
            security=SecurityType(data.get("security", "Unknown")),
            vendor=data.get("vendor", "Unknown"),
            last_seen=datetime.fromisoformat(data["last_seen"]) if "last_seen" in data else datetime.now(),
        )


@dataclass
class Threat:
    """
    Represents a detected security threat.
    
    Attributes:
        id: Unique threat identifier
        severity: Threat severity level
        category: Type of threat
        description: Human-readable description
        networks: List of networks involved in this threat
        detected_at: When the threat was first detected
        resolved: Whether the threat has been resolved
    """
    id: str
    severity: ThreatSeverity
    category: ThreatCategory
    description: str
    networks: List[Network] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "networks": [n.to_dict() for n in self.networks],
            "detected_at": self.detected_at.isoformat(),
            "resolved": self.resolved,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ScanResult:
    """
    Container for scan results with metadata.
    
    Attributes:
        networks: List of discovered networks
        scan_time: When the scan was performed
        duration_seconds: How long the scan took
        scanner_type: Which scanner was used
        platform: Platform the scan ran on
        threats: List of detected threats (if analysis was run)
    """
    networks: List[Network] = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    scanner_type: str = "unknown"
    platform: str = "unknown"
    threats: List[Threat] = field(default_factory=list)
    
    @property
    def network_count(self) -> int:
        """Get number of networks found."""
        return len(self.networks)
    
    @property
    def threat_count(self) -> int:
        """Get number of threats detected."""
        return len(self.threats)
    
    def get_networks_by_signal(self, descending: bool = True) -> List[Network]:
        """Get networks sorted by signal strength."""
        return sorted(self.networks, key=lambda n: n.rssi_dbm, reverse=descending)
    
    def get_networks_by_channel(self) -> dict:
        """Group networks by channel."""
        channels = {}
        for network in self.networks:
            if network.channel not in channels:
                channels[network.channel] = []
            channels[network.channel].append(network)
        return channels
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "networks": [n.to_dict() for n in self.networks],
            "scan_time": self.scan_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "scanner_type": self.scanner_type,
            "platform": self.platform,
            "network_count": self.network_count,
            "threats": [t.to_dict() for t in self.threats],
            "threat_count": self.threat_count,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_csv(self) -> str:
        """Convert to CSV format."""
        lines = ["SSID,BSSID,Channel,Frequency,RSSI,Signal%,Security,Vendor,Band,LastSeen"]
        for n in self.networks:
            lines.append(
                f'"{n.ssid}",{n.bssid},{n.channel},{n.frequency_mhz},'
                f'{n.rssi_dbm},{n.signal_percent},{n.security.value},'
                f'"{n.vendor}",{n.band},{n.last_seen.isoformat()}'
            )
        return "\n".join(lines)
