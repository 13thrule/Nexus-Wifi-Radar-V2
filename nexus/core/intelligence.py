"""
Passive Intelligence Core (PIC) for NEXUS WiFi Radar.

100% PASSIVE - No transmissions, only analysis of received data.

The PIC is the central brain that aggregates all passive intelligence:
- Device fingerprinting
- Distance/direction estimation
- Wall estimation
- Stability analysis
- Temporal behaviour
- Security context
- Relationship mapping
- Spoof detection
- Movement detection

All other modules can query the PIC for unified intelligence.
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime


class DeviceCategory(Enum):
    """Device type classification."""
    PHONE = "phone"
    LAPTOP = "laptop"
    ROUTER = "router"
    REPEATER = "repeater"
    MESH_NODE = "mesh_node"
    HOTSPOT = "hotspot"
    IOT = "iot"
    PRINTER = "printer"
    SMART_TV = "smart_tv"
    GAMING = "gaming"
    ENTERPRISE_AP = "enterprise_ap"
    UNKNOWN = "unknown"


class SecurityRating(Enum):
    """Security rating levels."""
    EXCELLENT = "excellent"  # WPA3
    GOOD = "good"           # WPA2-Enterprise
    MODERATE = "moderate"   # WPA2-PSK
    WEAK = "weak"           # WPA-PSK
    CRITICAL = "critical"   # WEP or Open


class MovementState(Enum):
    """Movement detection states."""
    STATIONARY = "stationary"
    SLOW_DRIFT = "slow_drift"
    MOVING = "moving"
    FAST_MOVING = "fast_moving"
    APPEARED = "appeared"
    DISAPPEARED = "disappeared"


class SpoofRisk(Enum):
    """Spoofing risk levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WiFiCapabilities:
    """WiFi capabilities extracted from beacons."""
    wifi_generation: int = 4  # 4, 5, 6, 6E
    supports_ht: bool = False   # 802.11n
    supports_vht: bool = False  # 802.11ac
    supports_he: bool = False   # 802.11ax
    supports_wpa3: bool = False
    supports_pmf: bool = False  # Protected Management Frames
    is_mesh: bool = False
    is_multi_bssid: bool = False
    max_streams: int = 1
    channel_width: int = 20  # MHz


@dataclass
class TemporalMetrics:
    """Temporal behaviour analysis."""
    # Signal trends
    signal_trend: str = "stable"  # improving, declining, stable, erratic
    trend_strength: float = 0.0   # How strong the trend is
    
    # Volatility
    short_term_volatility: float = 0.0  # Last 10 samples
    long_term_volatility: float = 0.0   # All samples
    
    # Stability
    stability_score: int = 50  # 0-100
    stability_rating: str = "moderate"
    
    # Patterns
    uptime_estimate: float = 0.0  # Hours since first seen
    activity_level: str = "normal"  # quiet, normal, busy, bursty
    burst_count: int = 0
    
    # Anomalies
    anomaly_count: int = 0
    last_anomaly: Optional[str] = None
    
    # Movement
    movement_state: MovementState = MovementState.STATIONARY
    movement_confidence: int = 0
    estimated_speed: float = 0.0  # Relative units


@dataclass
class LocationMetrics:
    """Distance and direction estimation."""
    # Distance
    estimated_distance_m: float = 0.0
    distance_confidence: int = 0
    distance_margin_percent: float = 50.0
    
    # Direction (for radar)
    angle_degrees: float = 0.0
    direction_confidence: int = 0
    
    # Obstacles
    wall_count: int = 0
    wall_description: str = "Unknown"
    environment_type: str = "indoor"  # indoor, outdoor, mixed
    
    # Position on radar
    radar_distance_ratio: float = 0.5  # 0=center, 1=edge
    radar_x: float = 0.0
    radar_y: float = 0.0


@dataclass
class SecurityMetrics:
    """Security analysis results."""
    # Basic
    encryption: str = "Unknown"
    security_rating: SecurityRating = SecurityRating.MODERATE
    
    # Details
    cipher_suite: str = "Unknown"
    auth_type: str = "Unknown"
    
    # Risks
    is_default_ssid: bool = False
    is_hidden: bool = False
    has_weak_config: bool = False
    channel_overlap_risk: bool = False
    
    # Spoofing
    spoof_risk: SpoofRisk = SpoofRisk.NONE
    spoof_indicators: List[str] = field(default_factory=list)
    similar_ssid_count: int = 0
    
    # Vulnerabilities
    vulnerabilities: List[str] = field(default_factory=list)


@dataclass 
class RelationshipData:
    """Network relationship information."""
    # Multi-AP detection
    is_part_of_mesh: bool = False
    mesh_group_id: Optional[str] = None
    mesh_members: List[str] = field(default_factory=list)
    
    # Repeater detection
    is_repeater: bool = False
    parent_ap_bssid: Optional[str] = None
    
    # Guest network
    is_guest_network: bool = False
    primary_network_ssid: Optional[str] = None
    
    # Multi-BSSID
    is_multi_bssid: bool = False
    bssid_cluster: List[str] = field(default_factory=list)
    
    # Client tracking (monitor mode only)
    connected_clients: List[str] = field(default_factory=list)
    client_count: int = 0


@dataclass
class NetworkIntelligence:
    """
    Complete intelligence profile for a single network.
    This is the unified data structure that PIC provides.
    """
    # Identity
    bssid: str
    ssid: str
    vendor: str = "Unknown"
    
    # Classification
    device_category: DeviceCategory = DeviceCategory.UNKNOWN
    device_icon: str = "❓"
    device_description: str = "Unknown device"
    classification_confidence: int = 0
    
    # Current state
    signal_percent: int = 0
    signal_dbm: int = -100
    channel: int = 0
    band: str = "2.4GHz"
    frequency_mhz: int = 2437
    
    # Capabilities
    capabilities: WiFiCapabilities = field(default_factory=WiFiCapabilities)
    
    # Location
    location: LocationMetrics = field(default_factory=LocationMetrics)
    
    # Temporal
    temporal: TemporalMetrics = field(default_factory=TemporalMetrics)
    
    # Security
    security: SecurityMetrics = field(default_factory=SecurityMetrics)
    
    # Relationships
    relationships: RelationshipData = field(default_factory=RelationshipData)
    
    # Timestamps
    first_seen: float = 0.0
    last_seen: float = 0.0
    observation_count: int = 0
    
    # Raw history (last 100 samples)
    signal_history: List[Tuple[float, int]] = field(default_factory=list)
    
    # Tags for quick filtering
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI display."""
        return {
            'bssid': self.bssid,
            'ssid': self.ssid,
            'vendor': self.vendor,
            'device_type': self.device_category.value,
            'device_icon': self.device_icon,
            'signal': self.signal_percent,
            'channel': self.channel,
            'band': self.band,
            'distance': self.location.estimated_distance_m,
            'direction': self.location.angle_degrees,
            'walls': self.location.wall_count,
            'wall_desc': self.location.wall_description,
            'stability': self.temporal.stability_score,
            'stability_rating': self.temporal.stability_rating,
            'security_rating': self.security.security_rating.value,
            'encryption': self.security.encryption,
            'spoof_risk': self.security.spoof_risk.value,
            'movement': self.temporal.movement_state.value,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'tags': list(self.tags),
        }


class PassiveIntelligenceCore:
    """
    The central intelligence aggregation system.
    
    100% PASSIVE - Only processes received beacon/probe data.
    
    This is the brain of NEXUS that unifies:
    - Device fingerprinting
    - Distance estimation
    - Direction estimation
    - Wall estimation
    - Stability analysis
    - Temporal behaviour
    - Security context
    - Relationship mapping
    - Spoof detection
    - Movement detection
    """
    
    # Configuration
    MAX_HISTORY_SIZE = 100
    MOVEMENT_THRESHOLD_DB = 5  # Signal change to detect movement
    VOLATILITY_WINDOW = 10
    
    # Device icons
    DEVICE_ICONS = {
        DeviceCategory.PHONE: "📱",
        DeviceCategory.LAPTOP: "💻",
        DeviceCategory.ROUTER: "📡",
        DeviceCategory.REPEATER: "🔁",
        DeviceCategory.MESH_NODE: "🔗",
        DeviceCategory.HOTSPOT: "📶",
        DeviceCategory.IOT: "🧠",
        DeviceCategory.PRINTER: "🖨️",
        DeviceCategory.SMART_TV: "📺",
        DeviceCategory.GAMING: "🎮",
        DeviceCategory.ENTERPRISE_AP: "🏢",
        DeviceCategory.UNKNOWN: "❓",
    }
    
    def __init__(self):
        # Main intelligence store
        self.networks: Dict[str, NetworkIntelligence] = {}
        
        # SSID to BSSID mapping for relationship detection
        self.ssid_map: Dict[str, Set[str]] = defaultdict(set)
        
        # Vendor prefix cache
        self.vendor_cache: Dict[str, str] = {}
        
        # Mesh/cluster detection
        self.potential_mesh_groups: Dict[str, Set[str]] = {}
        
        # Mode state
        self.radar_mode: str = "static"  # static, mobile
        self.has_gyroscope: bool = False
        self.has_multi_antenna: bool = False
        self.manual_mode_override: Optional[str] = None
        
        # Global statistics
        self.total_networks_seen: int = 0
        self.active_networks: int = 0
        self.spoof_alerts: int = 0
        
        # Import other modules for integration
        self._init_integrations()
    
    def _init_integrations(self):
        """Initialize connections to other NEXUS modules."""
        try:
            from nexus.core.fingerprint import get_fingerprinter
            self.fingerprinter = get_fingerprinter()
        except ImportError:
            self.fingerprinter = None
        
        try:
            from nexus.core.stability import get_stability_tracker, get_wall_estimator
            self.stability_tracker = get_stability_tracker()
            self.wall_estimator = get_wall_estimator()
        except ImportError:
            self.stability_tracker = None
            self.wall_estimator = None
        
        try:
            from nexus.core.distance import get_estimator
            self.distance_estimator = get_estimator()
        except ImportError:
            self.distance_estimator = None
        
        try:
            from nexus.core.radar_modes import get_radar_system
            self.radar_system = get_radar_system()
        except ImportError:
            self.radar_system = None
        
        try:
            from nexus.security.spoof import get_spoof_detector
            self.spoof_detector = get_spoof_detector()
        except ImportError:
            self.spoof_detector = None
    
    def process_network(self, bssid: str, ssid: str, signal_percent: int,
                        channel: int, security: str, vendor: str = "",
                        band: str = "", noise_db: int = -95) -> NetworkIntelligence:
        """
        Process a network observation and update intelligence.
        
        This is the main entry point called during scanning.
        100% PASSIVE - only processes received beacon data.
        """
        now = time.time()
        
        # Get or create network intelligence
        if bssid not in self.networks:
            self.networks[bssid] = NetworkIntelligence(
                bssid=bssid,
                ssid=ssid,
                first_seen=now
            )
            self.total_networks_seen += 1
        
        intel = self.networks[bssid]
        
        # Update basic info
        intel.ssid = ssid or intel.ssid
        intel.signal_percent = signal_percent
        intel.signal_dbm = signal_percent - 100  # Approximate conversion
        intel.channel = channel
        intel.band = band or self._get_band(channel)
        intel.frequency_mhz = self._channel_to_freq(channel)
        intel.vendor = vendor or intel.vendor
        intel.last_seen = now
        intel.observation_count += 1
        
        # Update SSID map
        if ssid:
            self.ssid_map[ssid].add(bssid)
        
        # Record signal history
        intel.signal_history.append((now, signal_percent))
        if len(intel.signal_history) > self.MAX_HISTORY_SIZE:
            intel.signal_history = intel.signal_history[-self.MAX_HISTORY_SIZE:]
        
        # Run all analysis engines
        self._analyze_device_fingerprint(intel, security)
        self._analyze_location(intel, noise_db)
        self._analyze_temporal(intel)
        self._analyze_security(intel, security)
        self._analyze_relationships(intel)
        self._analyze_movement(intel)
        
        # Update tags
        self._update_tags(intel)
        
        # Update global stats
        self._update_global_stats()
        
        return intel
    
    def _get_band(self, channel: int) -> str:
        """Determine band from channel."""
        if channel <= 14:
            return "2.4GHz"
        elif channel <= 177:
            return "5GHz"
        else:
            return "6GHz"
    
    def _channel_to_freq(self, channel: int) -> int:
        """Convert channel to frequency in MHz."""
        if channel <= 14:
            return 2407 + channel * 5
        elif channel <= 64:
            return 5000 + channel * 5
        elif channel <= 144:
            return 5000 + channel * 5
        else:
            return 5000 + channel * 5
    
    def _analyze_device_fingerprint(self, intel: NetworkIntelligence, security: str):
        """Analyze device type and capabilities."""
        
        # Use existing fingerprinter if available
        if self.fingerprinter:
            fp = self.fingerprinter.fingerprint(
                bssid=intel.bssid,
                ssid=intel.ssid,
                vendor=intel.vendor,
                channel=intel.channel,
                signal=intel.signal_percent,
                security=security
            )
            
            # Map fingerprint to our categories
            type_map = {
                'router': DeviceCategory.ROUTER,
                'access_point': DeviceCategory.ROUTER,
                'mesh_node': DeviceCategory.MESH_NODE,
                'repeater': DeviceCategory.REPEATER,
                'mobile_hotspot': DeviceCategory.HOTSPOT,
                'iot': DeviceCategory.IOT,
                'printer': DeviceCategory.PRINTER,
                'smart_tv': DeviceCategory.SMART_TV,
                'gaming': DeviceCategory.GAMING,
                'enterprise': DeviceCategory.ENTERPRISE_AP,
            }
            
            intel.device_category = type_map.get(fp.device_type.value, DeviceCategory.UNKNOWN)
            intel.device_icon = self.DEVICE_ICONS.get(intel.device_category, "❓")
            intel.device_description = fp.description
            intel.classification_confidence = fp.confidence
        else:
            # Fallback fingerprinting
            intel.device_category = self._fallback_fingerprint(intel.ssid, intel.vendor, security)
            intel.device_icon = self.DEVICE_ICONS.get(intel.device_category, "❓")
        
        # Analyze WiFi capabilities from security string
        intel.capabilities = self._analyze_capabilities(security, intel.band)
    
    def _fallback_fingerprint(self, ssid: str, vendor: str, security: str) -> DeviceCategory:
        """Simple fingerprinting when full module unavailable."""
        ssid_lower = (ssid or "").lower()
        vendor_lower = (vendor or "").lower()
        
        # Hotspot patterns
        if any(h in ssid_lower for h in ["iphone", "android", "pixel", "galaxy", "hotspot"]):
            return DeviceCategory.HOTSPOT
        
        # Enterprise patterns
        if "enterprise" in security.lower() or any(e in ssid_lower for e in ["corp", "office", "eduroam"]):
            return DeviceCategory.ENTERPRISE_AP
        
        # IoT patterns
        if any(i in ssid_lower for i in ["ring", "nest", "echo", "smart", "iot", "camera"]):
            return DeviceCategory.IOT
        
        # Mesh patterns
        if any(m in ssid_lower for m in ["eero", "orbi", "velop", "deco", "mesh"]):
            return DeviceCategory.MESH_NODE
        
        # Router vendors
        if any(r in vendor_lower for r in ["tp-link", "netgear", "asus", "linksys", "d-link"]):
            return DeviceCategory.ROUTER
        
        return DeviceCategory.UNKNOWN
    
    def _analyze_capabilities(self, security: str, band: str) -> WiFiCapabilities:
        """Analyze WiFi capabilities."""
        caps = WiFiCapabilities()
        security_upper = security.upper() if security else ""
        
        # WiFi generation inference
        if "WPA3" in security_upper:
            caps.wifi_generation = 6
            caps.supports_he = True
            caps.supports_wpa3 = True
        elif "5GHz" in band or "6GHz" in band:
            caps.wifi_generation = 5
            caps.supports_vht = True
        else:
            caps.wifi_generation = 4
            caps.supports_ht = True
        
        # PMF detection
        if "PMF" in security_upper or "WPA3" in security_upper:
            caps.supports_pmf = True
        
        return caps
    
    def _analyze_location(self, intel: NetworkIntelligence, noise_db: int):
        """Analyze distance, direction, and obstacles."""
        
        # Use existing distance estimator if available
        if self.distance_estimator:
            est = self.distance_estimator.estimate(
                bssid=intel.bssid,
                ssid=intel.ssid,
                signal_percent=intel.signal_percent,
                channel=intel.channel,
                vendor=intel.vendor
            )
            intel.location.estimated_distance_m = est.distance_meters
            intel.location.distance_confidence = est.confidence_percent
            intel.location.distance_margin_percent = est.margin_percent
            intel.location.environment_type = est.environment_guess
        else:
            # Fallback distance calculation
            intel.location.estimated_distance_m = self._estimate_distance_fallback(
                intel.signal_percent, intel.channel
            )
            intel.location.distance_confidence = 40
        
        # Use radar system for direction
        if self.radar_system:
            self.radar_system.update_network(
                bssid=intel.bssid,
                ssid=intel.ssid,
                signal=intel.signal_percent,
                channel=intel.channel,
                security=intel.security.encryption,
                vendor=intel.vendor
            )
            
            blip = self.radar_system.blips.get(intel.bssid)
            if blip:
                intel.location.angle_degrees = blip.angle_degrees
                intel.location.radar_distance_ratio = blip.distance_ratio
                intel.location.radar_x = blip.x_ratio
                intel.location.radar_y = blip.y_ratio
        else:
            # Fallback direction based on channel
            intel.location.angle_degrees = self._channel_to_angle(intel.channel)
            intel.location.radar_distance_ratio = 1.0 - (intel.signal_percent / 100.0) * 0.85
        
        # Wall estimation
        if self.wall_estimator:
            wall_est = self.wall_estimator.estimate_walls(
                signal_dbm=intel.signal_dbm,
                frequency_mhz=intel.frequency_mhz,
                estimated_distance=intel.location.estimated_distance_m,
                device_type=intel.device_category.value
            )
            intel.location.wall_count = wall_est.wall_count
            intel.location.wall_description = wall_est.description
        else:
            # Fallback wall estimation
            intel.location.wall_count = self._estimate_walls_fallback(intel.signal_dbm)
            intel.location.wall_description = f"{intel.location.wall_count} wall(s) estimated"
    
    def _estimate_distance_fallback(self, signal_percent: int, channel: int) -> float:
        """Fallback distance estimation."""
        # Simple path loss model
        # Assume TX power 20dBm, path loss exponent 3
        signal_dbm = signal_percent - 100
        tx_power = 20
        
        path_loss = tx_power - signal_dbm
        
        # Adjust for frequency
        if channel > 14:
            path_loss -= 6  # 5GHz has more loss
        
        # Distance = 10^((path_loss - 40) / (10 * n))
        # With n=3 for indoor
        distance = 10 ** ((path_loss - 40) / 30)
        
        return max(1.0, min(100.0, distance))
    
    def _channel_to_angle(self, channel: int) -> float:
        """Convert channel to radar angle."""
        if channel <= 14:
            return 15 + (channel - 1) * (150 / 13)
        else:
            return 195 + ((channel - 36) % 140) * (150 / 140)
    
    def _estimate_walls_fallback(self, signal_dbm: int) -> int:
        """Fallback wall count estimation."""
        if signal_dbm >= -50:
            return 0
        elif signal_dbm >= -60:
            return 1
        elif signal_dbm >= -70:
            return 2
        elif signal_dbm >= -80:
            return 3
        else:
            return 4
    
    def _analyze_temporal(self, intel: NetworkIntelligence):
        """Analyze temporal behaviour patterns."""
        history = intel.signal_history
        
        if len(history) < 3:
            return
        
        signals = [s for _, s in history]
        times = [t for t, _ in history]
        
        # Calculate volatility
        if len(signals) >= self.VOLATILITY_WINDOW:
            recent = signals[-self.VOLATILITY_WINDOW:]
            avg = sum(recent) / len(recent)
            variance = sum((s - avg) ** 2 for s in recent) / len(recent)
            intel.temporal.short_term_volatility = math.sqrt(variance)
        
        all_avg = sum(signals) / len(signals)
        all_variance = sum((s - all_avg) ** 2 for s in signals) / len(signals)
        intel.temporal.long_term_volatility = math.sqrt(all_variance)
        
        # Calculate trend
        if len(signals) >= 5:
            first_half = sum(signals[:len(signals)//2]) / (len(signals)//2)
            second_half = sum(signals[len(signals)//2:]) / (len(signals) - len(signals)//2)
            
            diff = second_half - first_half
            intel.temporal.trend_strength = abs(diff)
            
            if diff > 3:
                intel.temporal.signal_trend = "improving"
            elif diff < -3:
                intel.temporal.signal_trend = "declining"
            elif intel.temporal.short_term_volatility > 10:
                intel.temporal.signal_trend = "erratic"
            else:
                intel.temporal.signal_trend = "stable"
        
        # Calculate stability score
        if intel.temporal.long_term_volatility <= 2:
            intel.temporal.stability_score = 95
            intel.temporal.stability_rating = "rock_solid"
        elif intel.temporal.long_term_volatility <= 5:
            intel.temporal.stability_score = 80
            intel.temporal.stability_rating = "stable"
        elif intel.temporal.long_term_volatility <= 10:
            intel.temporal.stability_score = 60
            intel.temporal.stability_rating = "moderate"
        elif intel.temporal.long_term_volatility <= 15:
            intel.temporal.stability_score = 35
            intel.temporal.stability_rating = "unstable"
        else:
            intel.temporal.stability_score = 15
            intel.temporal.stability_rating = "erratic"
        
        # Uptime estimate
        if len(times) >= 2:
            intel.temporal.uptime_estimate = (times[-1] - times[0]) / 3600  # Hours
        
        # Activity level
        recent_observations = len([t for t, _ in history if t > time.time() - 60])
        if recent_observations > 20:
            intel.temporal.activity_level = "bursty"
        elif recent_observations > 10:
            intel.temporal.activity_level = "busy"
        elif recent_observations > 2:
            intel.temporal.activity_level = "normal"
        else:
            intel.temporal.activity_level = "quiet"
    
    def _analyze_security(self, intel: NetworkIntelligence, security: str):
        """Analyze security posture."""
        security_upper = (security or "").upper()
        
        # Encryption type
        intel.security.encryption = security or "Unknown"
        
        # Security rating
        if "WPA3" in security_upper:
            intel.security.security_rating = SecurityRating.EXCELLENT
            intel.security.cipher_suite = "CCMP-256/GCMP-256"
            intel.security.auth_type = "SAE"
        elif "WPA2" in security_upper and "ENTERPRISE" in security_upper:
            intel.security.security_rating = SecurityRating.GOOD
            intel.security.cipher_suite = "CCMP"
            intel.security.auth_type = "802.1X"
        elif "WPA2" in security_upper:
            intel.security.security_rating = SecurityRating.MODERATE
            intel.security.cipher_suite = "CCMP"
            intel.security.auth_type = "PSK"
        elif "WPA" in security_upper:
            intel.security.security_rating = SecurityRating.WEAK
            intel.security.cipher_suite = "TKIP"
            intel.security.auth_type = "PSK"
        elif "WEP" in security_upper:
            intel.security.security_rating = SecurityRating.CRITICAL
            intel.security.cipher_suite = "WEP"
            intel.security.auth_type = "Shared Key"
            intel.security.vulnerabilities.append("WEP encryption is broken")
        elif "OPEN" in security_upper or not security:
            intel.security.security_rating = SecurityRating.CRITICAL
            intel.security.cipher_suite = "None"
            intel.security.auth_type = "Open"
            intel.security.vulnerabilities.append("No encryption")
        
        # Default SSID detection
        default_patterns = [
            "linksys", "netgear", "dlink", "tp-link", "asus", "default",
            "setup", "configure", "router", "wireless", "wifi"
        ]
        ssid_lower = (intel.ssid or "").lower()
        intel.security.is_default_ssid = any(p in ssid_lower for p in default_patterns)
        if intel.security.is_default_ssid:
            intel.security.vulnerabilities.append("Default SSID detected")
        
        # Hidden SSID
        intel.security.is_hidden = not intel.ssid or intel.ssid.startswith("Hidden_")
        
        # Spoof detection via spoof detector
        if self.spoof_detector:
            alerts = self.spoof_detector.get_alerts_for_bssid(intel.bssid)
            if alerts:
                intel.security.spoof_risk = SpoofRisk.HIGH if len(alerts) > 1 else SpoofRisk.MEDIUM
                intel.security.spoof_indicators = [a.description for a in alerts[:3]]
        
        # Check for multiple BSSIDs with same SSID
        if intel.ssid in self.ssid_map:
            count = len(self.ssid_map[intel.ssid])
            intel.security.similar_ssid_count = count
            if count > 3:
                # Compare enum by their order in definition (NONE=0, LOW=1, MEDIUM=2, etc.)
                spoof_levels = list(SpoofRisk)
                current_idx = spoof_levels.index(intel.security.spoof_risk)
                medium_idx = spoof_levels.index(SpoofRisk.MEDIUM)
                if medium_idx > current_idx:
                    intel.security.spoof_risk = SpoofRisk.MEDIUM
                intel.security.spoof_indicators.append(f"Multiple APs ({count}) with same SSID")
        
        # Channel overlap risk
        same_channel = [n for n in self.networks.values() 
                        if n.channel == intel.channel and n.bssid != intel.bssid]
        if len(same_channel) > 2:
            intel.security.channel_overlap_risk = True
            intel.security.vulnerabilities.append(f"Channel {intel.channel} crowded ({len(same_channel)+1} networks)")
    
    def _analyze_relationships(self, intel: NetworkIntelligence):
        """Analyze network relationships."""
        
        # Multi-BSSID detection (same vendor prefix, similar SSID)
        vendor_prefix = intel.bssid[:8].upper()
        similar = []
        for other_bssid, other_intel in self.networks.items():
            if other_bssid == intel.bssid:
                continue
            if other_bssid[:8].upper() == vendor_prefix:
                similar.append(other_bssid)
        
        if similar:
            intel.relationships.is_multi_bssid = True
            intel.relationships.bssid_cluster = similar
        
        # Mesh detection (same SSID, different BSSIDs, similar vendor)
        if intel.ssid in self.ssid_map:
            ssid_bssids = self.ssid_map[intel.ssid]
            if len(ssid_bssids) > 1:
                # Check if they share vendor prefix
                prefixes = set(b[:8].upper() for b in ssid_bssids)
                if len(prefixes) == 1:
                    intel.relationships.is_part_of_mesh = True
                    intel.relationships.mesh_members = list(ssid_bssids)
                    
                    # Create mesh group ID
                    mesh_id = f"mesh_{intel.ssid}_{list(prefixes)[0]}"
                    intel.relationships.mesh_group_id = mesh_id
        
        # Guest network detection (SSID contains "guest", "_guest", "-guest")
        ssid_lower = (intel.ssid or "").lower()
        if "guest" in ssid_lower:
            intel.relationships.is_guest_network = True
            # Try to find primary network
            for other_ssid in self.ssid_map.keys():
                if other_ssid.lower() in ssid_lower.replace("guest", "").replace("_", "").replace("-", ""):
                    intel.relationships.primary_network_ssid = other_ssid
                    break
        
        # Repeater detection (same SSID, signal stability worse than others)
        if intel.ssid in self.ssid_map and len(self.ssid_map[intel.ssid]) > 1:
            for other_bssid in self.ssid_map[intel.ssid]:
                if other_bssid == intel.bssid:
                    continue
                other = self.networks.get(other_bssid)
                if other and other.temporal.stability_score > intel.temporal.stability_score + 20:
                    intel.relationships.is_repeater = True
                    intel.relationships.parent_ap_bssid = other_bssid
                    break
    
    def _analyze_movement(self, intel: NetworkIntelligence):
        """Analyze movement patterns."""
        history = intel.signal_history
        
        if len(history) < 5:
            intel.temporal.movement_state = MovementState.APPEARED
            return
        
        # Check recent signal changes
        recent = [s for _, s in history[-10:]]
        
        if len(recent) < 3:
            return
        
        # Calculate signal change rate
        changes = [abs(recent[i] - recent[i-1]) for i in range(1, len(recent))]
        avg_change = sum(changes) / len(changes)
        max_change = max(changes)
        
        # Classify movement
        if avg_change < 2 and max_change < 5:
            intel.temporal.movement_state = MovementState.STATIONARY
            intel.temporal.movement_confidence = 90
        elif avg_change < 5 and max_change < 10:
            intel.temporal.movement_state = MovementState.SLOW_DRIFT
            intel.temporal.movement_confidence = 70
        elif avg_change < 10:
            intel.temporal.movement_state = MovementState.MOVING
            intel.temporal.movement_confidence = 60
        else:
            intel.temporal.movement_state = MovementState.FAST_MOVING
            intel.temporal.movement_confidence = 50
        
        # Estimate relative speed (arbitrary units)
        intel.temporal.estimated_speed = avg_change * 2
    
    def _update_tags(self, intel: NetworkIntelligence):
        """Update quick-filter tags."""
        intel.tags.clear()
        
        # Device type tag
        intel.tags.add(intel.device_category.value)
        
        # Band tag
        intel.tags.add(intel.band.replace("GHz", "ghz").replace(".", "_"))
        
        # Security tags
        if intel.security.security_rating == SecurityRating.CRITICAL:
            intel.tags.add("insecure")
        if intel.security.security_rating == SecurityRating.EXCELLENT:
            intel.tags.add("secure")
        if intel.security.spoof_risk != SpoofRisk.NONE:
            intel.tags.add("spoof_risk")
        if intel.security.is_hidden:
            intel.tags.add("hidden")
        
        # Relationship tags
        if intel.relationships.is_part_of_mesh:
            intel.tags.add("mesh")
        if intel.relationships.is_repeater:
            intel.tags.add("repeater")
        if intel.relationships.is_guest_network:
            intel.tags.add("guest")
        
        # Movement tags
        if intel.temporal.movement_state in [MovementState.MOVING, MovementState.FAST_MOVING]:
            intel.tags.add("moving")
        
        # Stability tags
        if intel.temporal.stability_rating in ["unstable", "erratic"]:
            intel.tags.add("unstable")
    
    def _update_global_stats(self):
        """Update global statistics."""
        now = time.time()
        
        # Count active networks (seen in last 30 seconds)
        self.active_networks = sum(
            1 for n in self.networks.values()
            if now - n.last_seen < 30
        )
        
        # Count spoof alerts
        self.spoof_alerts = sum(
            1 for n in self.networks.values()
            if n.security.spoof_risk != SpoofRisk.NONE
        )
    
    # === PUBLIC API ===
    
    def get_network(self, bssid: str) -> Optional[NetworkIntelligence]:
        """Get intelligence for a specific network."""
        return self.networks.get(bssid)
    
    def get_all_networks(self) -> List[NetworkIntelligence]:
        """Get all network intelligence sorted by signal strength."""
        return sorted(
            self.networks.values(),
            key=lambda n: n.signal_percent,
            reverse=True
        )
    
    def get_networks_by_tag(self, tag: str) -> List[NetworkIntelligence]:
        """Get networks matching a tag."""
        return [n for n in self.networks.values() if tag in n.tags]
    
    def get_spoof_alerts(self) -> List[NetworkIntelligence]:
        """Get networks with spoof risk."""
        return [n for n in self.networks.values() if n.security.spoof_risk != SpoofRisk.NONE]
    
    def get_mesh_groups(self) -> Dict[str, List[str]]:
        """Get detected mesh network groups."""
        groups = {}
        for net in self.networks.values():
            if net.relationships.is_part_of_mesh and net.relationships.mesh_group_id:
                if net.relationships.mesh_group_id not in groups:
                    groups[net.relationships.mesh_group_id] = []
                groups[net.relationships.mesh_group_id].append(net.bssid)
        return groups
    
    def get_security_summary(self) -> Dict[str, int]:
        """Get security rating summary."""
        summary = {r.value: 0 for r in SecurityRating}
        for net in self.networks.values():
            summary[net.security.security_rating.value] += 1
        return summary
    
    def get_device_summary(self) -> Dict[str, int]:
        """Get device type summary."""
        summary = {d.value: 0 for d in DeviceCategory}
        for net in self.networks.values():
            summary[net.device_category.value] += 1
        return summary
    
    def get_mode_status(self) -> Dict[str, Any]:
        """Get current radar mode status."""
        if self.radar_system:
            mode = self.radar_system.state.mode.value
            is_calibrating = self.radar_system.state.is_calibrating
        else:
            mode = "static"
            is_calibrating = False
        
        return {
            'mode': mode,
            'has_gyroscope': self.has_gyroscope,
            'has_multi_antenna': self.has_multi_antenna,
            'manual_override': self.manual_mode_override,
            'is_calibrating': is_calibrating,
        }
    
    def set_mode(self, mode: str, manual: bool = False):
        """Set radar mode."""
        if manual:
            self.manual_mode_override = mode
        
        if self.radar_system:
            from nexus.core.radar_modes import RadarMode
            if mode == "mobile":
                self.radar_system.set_mode(RadarMode.MOBILE_HOMING)
            else:
                self.radar_system.set_mode(RadarMode.STATIC_DESKTOP)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get global statistics."""
        return {
            'total_networks': self.total_networks_seen,
            'active_networks': self.active_networks,
            'spoof_alerts': self.spoof_alerts,
            'security_summary': self.get_security_summary(),
            'device_summary': self.get_device_summary(),
            'mesh_groups': len(self.get_mesh_groups()),
        }
    
    def clear(self):
        """Clear all intelligence data."""
        self.networks.clear()
        self.ssid_map.clear()
        self.total_networks_seen = 0
        self.active_networks = 0
        self.spoof_alerts = 0


# Global PIC instance
_pic: Optional[PassiveIntelligenceCore] = None


def get_pic() -> PassiveIntelligenceCore:
    """Get the global Passive Intelligence Core instance."""
    global _pic
    if _pic is None:
        _pic = PassiveIntelligenceCore()
    return _pic
