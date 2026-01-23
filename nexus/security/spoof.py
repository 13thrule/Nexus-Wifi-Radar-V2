"""
Spoof Detection for NEXUS WiFi Radar.

100% PASSIVE - Detects potential rogue APs from beacon analysis only.

Detection methods:
- Multiple BSSIDs with same SSID
- Signal anomalies
- Beacon timing inconsistencies
- Security downgrade detection
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict
import time


class ThreatLevel(Enum):
    """Threat level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SpoofType(Enum):
    """Type of potential spoof detected."""
    EVIL_TWIN = "evil_twin"          # Same SSID, different BSSID
    KARMA_ATTACK = "karma_attack"     # Responding to any SSID
    DEAUTH_FLOOD = "deauth_flood"     # Excessive deauth (if detectable)
    SSID_BROADCAST = "ssid_broadcast" # Broadcasting common SSIDs
    SECURITY_DOWNGRADE = "downgrade"  # Weaker security than expected
    SIGNAL_ANOMALY = "signal_anomaly" # Unusual signal behavior


@dataclass
class SpoofAlert:
    """Alert for potential spoofing activity."""
    alert_id: str
    spoof_type: SpoofType
    threat_level: ThreatLevel
    ssid: str
    bssids_involved: List[str]
    description: str
    evidence: List[str] = field(default_factory=list)
    first_detected: float = 0.0
    last_updated: float = 0.0
    is_active: bool = True
    
    @property
    def age_seconds(self) -> float:
        return time.time() - self.first_detected


@dataclass
class NetworkProfile:
    """Profile of expected network characteristics."""
    ssid: str
    expected_bssids: Set[str] = field(default_factory=set)
    expected_security: str = ""
    expected_channel_set: Set[int] = field(default_factory=set)
    min_expected_signal: int = -90
    max_expected_signal: int = -30
    is_trusted: bool = False
    first_seen: float = 0.0
    
    # Tracking
    security_variants: Dict[str, int] = field(default_factory=dict)  # security -> count


class PassiveSpoofDetector:
    """
    Passive spoof detection system.
    
    100% PASSIVE - only analyzes received beacon/probe data.
    No active scanning or packet injection.
    """
    
    # Thresholds
    EVIL_TWIN_BSSID_THRESHOLD = 2  # More than 2 BSSIDs with same SSID = suspicious
    SIGNAL_ANOMALY_THRESHOLD = 30  # dB change considered anomalous
    
    # Common SSIDs that might be targeted
    COMMON_TARGET_SSIDS = {
        "xfinity", "attwifi", "starbucks", "mcdonalds", "hotel", "airport",
        "free wifi", "public wifi", "guest", "open", "hotspot",
        "linksys", "netgear", "dlink", "default", "setup"
    }
    
    def __init__(self):
        # Track all SSIDs and their BSSIDs
        self.ssid_bssid_map: Dict[str, Set[str]] = defaultdict(set)
        
        # Track security per SSID/BSSID combo
        self.security_map: Dict[Tuple[str, str], str] = {}
        
        # Network profiles for trusted networks
        self.profiles: Dict[str, NetworkProfile] = {}
        
        # Active alerts
        self.alerts: Dict[str, SpoofAlert] = {}
        
        # Signal history for anomaly detection
        self.signal_history: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        
        # Track last seen
        self.last_seen: Dict[str, float] = {}
    
    def analyze_network(self, bssid: str, ssid: str, signal: int, 
                        channel: int, security: str) -> List[SpoofAlert]:
        """
        Analyze a network observation for potential spoofing.
        
        Returns list of new or updated alerts.
        """
        now = time.time()
        new_alerts = []
        
        # Update tracking
        self.ssid_bssid_map[ssid].add(bssid)
        self.security_map[(ssid, bssid)] = security
        self.last_seen[bssid] = now
        
        # Record signal history
        self.signal_history[bssid].append((now, signal))
        # Keep only last 60 samples
        if len(self.signal_history[bssid]) > 60:
            self.signal_history[bssid] = self.signal_history[bssid][-60:]
        
        # Check for evil twin (multiple BSSIDs with same SSID)
        evil_twin_alert = self._check_evil_twin(ssid, bssid)
        if evil_twin_alert:
            new_alerts.append(evil_twin_alert)
        
        # Check for security downgrade
        downgrade_alert = self._check_security_downgrade(ssid, bssid, security)
        if downgrade_alert:
            new_alerts.append(downgrade_alert)
        
        # Check for signal anomaly
        anomaly_alert = self._check_signal_anomaly(bssid, ssid, signal)
        if anomaly_alert:
            new_alerts.append(anomaly_alert)
        
        # Check for common target SSID
        target_alert = self._check_common_target(ssid, bssid, security)
        if target_alert:
            new_alerts.append(target_alert)
        
        return new_alerts
    
    def _check_evil_twin(self, ssid: str, bssid: str) -> Optional[SpoofAlert]:
        """Check for evil twin attack (multiple APs with same SSID)."""
        bssids = self.ssid_bssid_map.get(ssid, set())
        
        if len(bssids) <= self.EVIL_TWIN_BSSID_THRESHOLD:
            return None
        
        # Create alert ID
        alert_id = f"evil_twin_{ssid}"
        
        # Check if alert already exists
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.bssids_involved = list(bssids)
            alert.last_updated = time.time()
            return None  # Return None since it's not new
        
        # Determine threat level
        bssid_count = len(bssids)
        if bssid_count > 5:
            threat_level = ThreatLevel.HIGH
        elif bssid_count > 3:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        # Check for security variations (stronger indicator)
        securities = set()
        for b in bssids:
            sec = self.security_map.get((ssid, b), "")
            if sec:
                securities.add(sec)
        
        if len(securities) > 1:
            threat_level = ThreatLevel.HIGH
        
        evidence = [
            f"Found {bssid_count} different BSSIDs broadcasting SSID '{ssid}'",
            f"BSSIDs: {', '.join(list(bssids)[:5])}{'...' if len(bssids) > 5 else ''}",
        ]
        
        if len(securities) > 1:
            evidence.append(f"Different security types detected: {', '.join(securities)}")
        
        alert = SpoofAlert(
            alert_id=alert_id,
            spoof_type=SpoofType.EVIL_TWIN,
            threat_level=threat_level,
            ssid=ssid,
            bssids_involved=list(bssids),
            description=f"Possible Evil Twin: Multiple APs ({bssid_count}) with SSID '{ssid}'",
            evidence=evidence,
            first_detected=time.time(),
            last_updated=time.time()
        )
        
        self.alerts[alert_id] = alert
        return alert
    
    def _check_security_downgrade(self, ssid: str, bssid: str, 
                                   security: str) -> Optional[SpoofAlert]:
        """Check for security downgrade attack."""
        # Get profile if exists
        profile = self.profiles.get(ssid)
        
        if not profile:
            # Create profile from first observation
            profile = NetworkProfile(ssid=ssid, first_seen=time.time())
            self.profiles[ssid] = profile
        
        # Track security variants
        if security not in profile.security_variants:
            profile.security_variants[security] = 0
        profile.security_variants[security] += 1
        
        # Set expected security from most common
        if not profile.expected_security:
            profile.expected_security = max(
                profile.security_variants, 
                key=profile.security_variants.get
            )
        
        # Check for downgrade
        security_strength = self._get_security_strength(security)
        expected_strength = self._get_security_strength(profile.expected_security)
        
        if security_strength < expected_strength and profile.security_variants[security] < 3:
            alert_id = f"downgrade_{ssid}_{bssid}"
            
            if alert_id in self.alerts:
                return None
            
            alert = SpoofAlert(
                alert_id=alert_id,
                spoof_type=SpoofType.SECURITY_DOWNGRADE,
                threat_level=ThreatLevel.MEDIUM,
                ssid=ssid,
                bssids_involved=[bssid],
                description=f"Security downgrade detected for '{ssid}'",
                evidence=[
                    f"Expected security: {profile.expected_security}",
                    f"Observed security: {security}",
                    f"BSSID: {bssid}"
                ],
                first_detected=time.time(),
                last_updated=time.time()
            )
            
            self.alerts[alert_id] = alert
            return alert
        
        return None
    
    def _check_signal_anomaly(self, bssid: str, ssid: str, 
                               signal: int) -> Optional[SpoofAlert]:
        """Check for unusual signal changes."""
        history = self.signal_history.get(bssid, [])
        
        if len(history) < 3:
            return None
        
        # Get recent signals
        recent_signals = [s for _, s in history[-10:]]
        avg_signal = sum(recent_signals) / len(recent_signals)
        
        # Check for sudden large change
        if len(history) >= 2:
            prev_signal = history[-2][1]
            change = abs(signal - prev_signal)
            
            if change > self.SIGNAL_ANOMALY_THRESHOLD:
                alert_id = f"anomaly_{bssid}_{int(time.time())}"
                
                alert = SpoofAlert(
                    alert_id=alert_id,
                    spoof_type=SpoofType.SIGNAL_ANOMALY,
                    threat_level=ThreatLevel.LOW,
                    ssid=ssid,
                    bssids_involved=[bssid],
                    description=f"Signal anomaly detected for '{ssid}'",
                    evidence=[
                        f"Signal changed by {change}dB in one sample",
                        f"Previous: {prev_signal}dBm, Current: {signal}dBm",
                        f"Average signal: {avg_signal:.0f}dBm",
                        "Possible: Mobile AP, interference, or spoof attempt"
                    ],
                    first_detected=time.time(),
                    last_updated=time.time()
                )
                
                self.alerts[alert_id] = alert
                return alert
        
        return None
    
    def _check_common_target(self, ssid: str, bssid: str,
                              security: str) -> Optional[SpoofAlert]:
        """Check if SSID matches common attack targets."""
        ssid_lower = ssid.lower()
        
        # Check against known targets
        is_target = any(target in ssid_lower for target in self.COMMON_TARGET_SSIDS)
        
        if not is_target:
            return None
        
        # Only alert if security is weak
        if security and "WPA2" in security.upper() and "ENTERPRISE" not in security.upper():
            return None
        
        alert_id = f"target_{ssid}_{bssid}"
        
        if alert_id in self.alerts:
            return None
        
        threat_level = ThreatLevel.LOW
        if "OPEN" in (security or "").upper() or not security:
            threat_level = ThreatLevel.MEDIUM
        
        alert = SpoofAlert(
            alert_id=alert_id,
            spoof_type=SpoofType.SSID_BROADCAST,
            threat_level=threat_level,
            ssid=ssid,
            bssids_involved=[bssid],
            description=f"Common target SSID detected: '{ssid}'",
            evidence=[
                f"SSID matches common attack target pattern",
                f"Security: {security or 'OPEN'}",
                "This SSID type is often impersonated by attackers"
            ],
            first_detected=time.time(),
            last_updated=time.time()
        )
        
        self.alerts[alert_id] = alert
        return alert
    
    def _get_security_strength(self, security: str) -> int:
        """Get numeric strength value for security type."""
        if not security:
            return 0
        
        security_upper = security.upper()
        
        if "WPA3" in security_upper:
            return 100
        elif "WPA2" in security_upper and "ENTERPRISE" in security_upper:
            return 90
        elif "WPA2" in security_upper:
            return 70
        elif "WPA" in security_upper:
            return 50
        elif "WEP" in security_upper:
            return 20
        elif "OPEN" in security_upper:
            return 0
        else:
            return 30
    
    def get_active_alerts(self) -> List[SpoofAlert]:
        """Get all active alerts sorted by threat level."""
        threat_order = {
            ThreatLevel.CRITICAL: 0,
            ThreatLevel.HIGH: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.LOW: 3
        }
        
        active = [a for a in self.alerts.values() if a.is_active]
        return sorted(active, key=lambda a: threat_order.get(a.threat_level, 4))
    
    def get_alerts_for_ssid(self, ssid: str) -> List[SpoofAlert]:
        """Get all alerts related to an SSID."""
        return [a for a in self.alerts.values() if a.ssid == ssid]
    
    def get_alerts_for_bssid(self, bssid: str) -> List[SpoofAlert]:
        """Get all alerts involving a BSSID."""
        return [a for a in self.alerts.values() if bssid in a.bssids_involved]
    
    def dismiss_alert(self, alert_id: str):
        """Dismiss an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].is_active = False
    
    def add_trusted_network(self, ssid: str, bssid: str, security: str):
        """Add a network to trusted list (won't generate alerts)."""
        if ssid not in self.profiles:
            self.profiles[ssid] = NetworkProfile(ssid=ssid, first_seen=time.time())
        
        self.profiles[ssid].expected_bssids.add(bssid)
        self.profiles[ssid].expected_security = security
        self.profiles[ssid].is_trusted = True
    
    def get_threat_icon(self, level: ThreatLevel) -> str:
        """Get icon for threat level."""
        icons = {
            ThreatLevel.CRITICAL: "🚨",
            ThreatLevel.HIGH: "⚠️",
            ThreatLevel.MEDIUM: "⚡",
            ThreatLevel.LOW: "ℹ️"
        }
        return icons.get(level, "❓")
    
    def get_spoof_type_icon(self, spoof_type: SpoofType) -> str:
        """Get icon for spoof type."""
        icons = {
            SpoofType.EVIL_TWIN: "👥",
            SpoofType.KARMA_ATTACK: "🎭",
            SpoofType.DEAUTH_FLOOD: "💥",
            SpoofType.SSID_BROADCAST: "📢",
            SpoofType.SECURITY_DOWNGRADE: "🔓",
            SpoofType.SIGNAL_ANOMALY: "📊"
        }
        return icons.get(spoof_type, "❓")


# Global instance
_spoof_detector: Optional[PassiveSpoofDetector] = None


def get_spoof_detector() -> PassiveSpoofDetector:
    """Get the global spoof detector instance."""
    global _spoof_detector
    if _spoof_detector is None:
        _spoof_detector = PassiveSpoofDetector()
    return _spoof_detector
