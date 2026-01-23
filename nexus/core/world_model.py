"""
Unified World Model Expander (UWM-X) for NEXUS WiFi Radar.

100% PASSIVE - No transmissions, only analysis of received data.

The UWM-X is the central intelligence graph that unifies all PIC data:
- Relationship inference (AP↔client, mesh, repeater, cluster)
- Temporal behavior modeling (signatures, patterns, anomalies)
- Environmental context fusion (interference, congestion, wall density)
- Movement vector prediction
- Cross-module scoring
- OUI Vendor Intelligence (via OUI-IM integration)

All subsystems read from UWM-X for unified intelligence.
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum, auto
from collections import defaultdict, deque
import statistics

# OUI-IM Integration (100% offline vendor intelligence)
from nexus.core.oui_vendor import get_oui_intelligence, VendorInfo


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class NodeType(Enum):
    """Node classification in world graph."""
    ACCESS_POINT = "access_point"
    CLIENT = "client"
    MESH_NODE = "mesh_node"
    REPEATER = "repeater"
    HOTSPOT = "hotspot"
    IOT_DEVICE = "iot_device"
    ROGUE_AP = "rogue_ap"
    UNKNOWN = "unknown"


class EdgeType(Enum):
    """Relationship types between nodes."""
    AP_CLIENT = "ap_client"           # AP serves client
    MESH_PEER = "mesh_peer"           # Mesh network peers
    REPEATER_PARENT = "repeater_parent"  # Repeater to parent AP
    SAME_SSID = "same_ssid"           # Share SSID
    SAME_VENDOR = "same_vendor"       # Share vendor OUI
    CO_PRESENCE = "co_presence"       # Appear/disappear together
    INTERFERENCE = "interference"     # Same channel interference
    CLUSTER = "cluster"               # Same cluster grouping


class TemporalPattern(Enum):
    """Temporal behavior patterns."""
    UNKNOWN = "unknown"               # Not yet classified
    ALWAYS_ON = "always_on"           # Constant presence
    PERIODIC = "periodic"             # Regular intervals
    TRANSIENT = "transient"           # Brief appearances
    SPORADIC = "sporadic"             # Random presence
    MOBILE = "mobile"                 # Moving device
    STATIONARY = "stationary"         # Fixed position


class AnomalyType(Enum):
    """Anomaly classifications."""
    NONE = "none"
    SIGNAL_SPIKE = "signal_spike"
    SIGNAL_DROP = "signal_drop"
    CHANNEL_HOP = "channel_hop"
    BSSID_CHANGE = "bssid_change"
    SECURITY_DOWNGRADE = "security_downgrade"
    VENDOR_MISMATCH = "vendor_mismatch"
    PRESENCE_GAP = "presence_gap"
    RAPID_MOVEMENT = "rapid_movement"


class EnvironmentType(Enum):
    """Environmental context classification."""
    QUIET = "quiet"                   # Low interference
    NORMAL = "normal"                 # Typical environment
    CONGESTED = "congested"           # Many APs, high interference
    STORMY = "stormy"                 # Severe interference
    SHIELDED = "shielded"             # High wall density


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TemporalSignature:
    """Temporal behavior signature for a node."""
    pattern: TemporalPattern = TemporalPattern.UNKNOWN
    confidence: int = 0
    
    # Presence metrics
    presence_ratio: float = 0.0       # Time visible / total time
    avg_session_duration: float = 0.0  # Average continuous presence (seconds)
    session_count: int = 0
    
    # Signal metrics over time
    rssi_mean: float = -70.0
    rssi_variance: float = 0.0
    rssi_trend: float = 0.0           # Positive = improving, negative = declining
    rssi_derivative: float = 0.0      # Rate of change
    
    # Periodicity
    is_periodic: bool = False
    period_seconds: float = 0.0
    
    # Anomalies
    anomaly_count: int = 0
    last_anomaly: Optional[AnomalyType] = None
    anomaly_history: List[Tuple[float, AnomalyType]] = field(default_factory=list)


@dataclass
class MovementVector:
    """Movement prediction vector."""
    # Current state
    speed: float = 0.0                # Relative units (RSSI change rate)
    direction: float = 0.0            # Degrees (0-360)
    
    # Derivatives
    velocity_x: float = 0.0           # X component
    velocity_y: float = 0.0           # Y component
    acceleration: float = 0.0         # Rate of velocity change
    
    # Prediction
    predicted_distance: float = 0.0   # Predicted distance in T+1
    predicted_angle: float = 0.0      # Predicted angle in T+1
    prediction_confidence: int = 0
    
    # Classification
    is_moving: bool = False
    is_approaching: bool = False
    is_receding: bool = False


@dataclass
class EnvironmentContext:
    """Environmental context scores."""
    # Interference
    interference_score: float = 0.0   # 0-100, higher = more interference
    interference_sources: int = 0     # Count of interfering APs
    
    # Congestion
    congestion_score: float = 0.0     # 0-100, higher = more congested
    aps_on_channel: int = 0
    
    # Wall density (attenuation)
    wall_density_score: float = 0.0   # 0-100, higher = more walls
    estimated_walls: int = 0
    attenuation_db: float = 0.0
    
    # Classification
    environment_type: EnvironmentType = EnvironmentType.NORMAL
    
    # Channel health
    channel_quality: float = 50.0     # 0-100


@dataclass
class GraphEdge:
    """Edge in the world graph."""
    source_mac: str
    target_mac: str
    edge_type: EdgeType
    weight: float = 1.0               # Relationship strength (0-1)
    confidence: int = 50
    
    # Temporal
    first_seen: float = 0.0
    last_seen: float = 0.0
    observation_count: int = 0
    
    # Co-presence
    co_presence_ratio: float = 0.0    # How often seen together


@dataclass
class GraphCluster:
    """Cluster of related nodes."""
    cluster_id: str
    cluster_type: str                 # "mesh", "repeater_chain", "vendor_group", "ssid_group"
    members: Set[str] = field(default_factory=set)
    primary_node: Optional[str] = None
    
    # Metrics
    cohesion_score: float = 0.0       # Internal similarity
    avg_signal: float = -70.0
    channel_spread: int = 0           # Number of distinct channels


@dataclass
class WorldNode:
    """
    Unified node in the world graph.
    Aggregates all intelligence for a single device/AP.
    """
    # Identity
    mac: str                          # BSSID or client MAC
    node_type: NodeType = NodeType.UNKNOWN
    
    # Basic info (from PIC)
    ssid: str = ""
    vendor: str = ""
    oui: str = ""
    channel: int = 0
    band: str = "2.4GHz"
    security: str = ""
    
    # OUI-IM Vendor Intelligence (from OUI-IM module)
    vendor_confidence: float = 0.0     # 0-100, vendor lookup confidence
    vendor_type: str = "unknown"       # consumer, enterprise, iot, mesh, mobile, isp
    is_randomized_mac: bool = False    # Locally administered / randomized MAC
    
    # Current state
    rssi: int = -100
    is_visible: bool = False
    last_seen: float = 0.0
    first_seen: float = 0.0
    
    # History (rolling windows)
    rssi_history: List[Tuple[float, int]] = field(default_factory=list)
    channel_history: List[Tuple[float, int]] = field(default_factory=list)
    presence_intervals: List[Tuple[float, float]] = field(default_factory=list)
    
    # Computed vectors
    distance_estimate: float = 0.0
    angle_estimate: float = 0.0
    movement: MovementVector = field(default_factory=MovementVector)
    
    # Temporal signature
    temporal: TemporalSignature = field(default_factory=TemporalSignature)
    
    # Environmental context
    environment: EnvironmentContext = field(default_factory=EnvironmentContext)
    
    # Scores (0-100)
    stability_score: float = 50.0
    spoof_risk_score: float = 0.0
    confidence_score: float = 50.0
    fingerprint_confidence: float = 50.0
    
    # Relationships
    edges: List[str] = field(default_factory=list)  # Edge IDs
    cluster_id: Optional[str] = None
    
    # Anomalies
    anomaly_flags: List[AnomalyType] = field(default_factory=list)
    
    # Home Point relative (only valid if Home Point set)
    home_relative_distance: float = 0.0
    home_relative_angle: float = 0.0
    home_relative_vector: Tuple[float, float] = (0.0, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED WORLD MODEL EXPANDER (UWM-X)
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedWorldModel:
    """
    The Unified World Model Expander (UWM-X).
    
    100% PASSIVE - Only processes received beacon/probe data.
    
    Central intelligence graph that unifies all PIC data:
    - Nodes: Devices and APs with full intelligence profile
    - Edges: Relationships between nodes
    - Clusters: Grouped nodes (mesh, repeater chains, etc.)
    - Temporal signatures: Behavior patterns over time
    - Environmental context: Interference, congestion, wall density
    - Movement vectors: Prediction and tracking
    
    All subsystems read from UWM-X for unified intelligence.
    """
    
    # Configuration
    MAX_RSSI_HISTORY = 100
    MAX_CHANNEL_HISTORY = 50
    MAX_PRESENCE_INTERVALS = 20
    MAX_ANOMALY_HISTORY = 50
    
    # Temporal smoothing (EMA alpha)
    EMA_ALPHA = 0.3
    
    # Thresholds
    VISIBILITY_TIMEOUT = 30.0         # Seconds before marked invisible
    CO_PRESENCE_THRESHOLD = 0.7       # Min overlap for co-presence edge
    MOVEMENT_THRESHOLD = 3.0          # RSSI change for movement detection
    ANOMALY_THRESHOLD = 2.0           # Std devs for anomaly detection
    
    # Path loss model
    TX_POWER_DBM = 20                  # Assumed transmit power
    PATH_LOSS_EXPONENT = 3.0          # Indoor path loss exponent
    WALL_ATTENUATION_DB = 3.0         # dB per wall
    
    def __init__(self):
        # Graph storage
        self.nodes: Dict[str, WorldNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.clusters: Dict[str, GraphCluster] = {}
        
        # SSID to MACs mapping
        self.ssid_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Channel to MACs mapping
        self.channel_index: Dict[int, Set[str]] = defaultdict(set)
        
        # Vendor to MACs mapping
        self.vendor_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Home Point (user-selected only, never inferred)
        self.home_point: Optional[str] = None  # MAC of home point AP
        self.home_point_vector: Tuple[float, float] = (0.0, 0.0)
        
        # Global environment
        self.global_environment: EnvironmentContext = EnvironmentContext()
        
        # Statistics
        self.total_nodes_seen: int = 0
        self.active_nodes: int = 0
        self.total_edges: int = 0
        self.total_clusters: int = 0
        
        # Timestamps
        self.last_update: float = 0.0
        self.model_age: float = 0.0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CORE UPDATE METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_node(self, mac: str, ssid: str = "", rssi: int = -100,
                    channel: int = 0, security: str = "", vendor: str = "",
                    band: str = "", node_type: Optional[NodeType] = None,
                    distance: float = 0.0, angle: float = 0.0,
                    stability: float = 50.0, spoof_risk: float = 0.0,
                    fingerprint_conf: float = 50.0) -> WorldNode:
        """
        Update or create a node in the world graph.
        
        100% PASSIVE - Only processes received data.
        """
        now = time.time()
        
        # Get or create node
        if mac not in self.nodes:
            self.nodes[mac] = WorldNode(mac=mac, first_seen=now)
            self.total_nodes_seen += 1
        
        node = self.nodes[mac]
        
        # Track previous state for derivative calculation
        prev_rssi = node.rssi
        prev_channel = node.channel
        
        # Update basic fields
        if ssid:
            node.ssid = ssid
        node.rssi = rssi
        node.channel = channel
        node.security = security
        if vendor:
            node.vendor = vendor
            node.oui = mac[:8].upper()
        node.band = band or self._get_band(channel)
        node.is_visible = True
        node.last_seen = now
        
        # OUI-IM Vendor Intelligence Integration (100% offline)
        self._apply_oui_intelligence(node, rssi)
        
        # Update type if provided
        if node_type:
            node.node_type = node_type
        
        # Update scores
        node.stability_score = stability
        node.spoof_risk_score = spoof_risk
        node.fingerprint_confidence = fingerprint_conf
        node.distance_estimate = distance
        node.angle_estimate = angle
        
        # Record history
        self._record_rssi_history(node, now, rssi)
        self._record_channel_history(node, now, channel, prev_channel)
        self._update_presence(node, now)
        
        # Update indices
        if ssid:
            self.ssid_index[ssid].add(mac)
        self.channel_index[channel].add(mac)
        if vendor:
            self.vendor_index[vendor].add(mac)
        
        # Compute derivatives and movement
        self._compute_movement_vector(node, prev_rssi, rssi, now)
        
        # Compute temporal signature
        self._compute_temporal_signature(node)
        
        # Detect anomalies
        self._detect_anomalies(node, prev_rssi, prev_channel)
        
        # Update environmental context
        self._compute_environment_context(node)
        
        # Update home-relative position
        if self.home_point:
            self._compute_home_relative(node)
        
        # Compute confidence
        self._compute_confidence(node)
        
        self.last_update = now
        return node
    
    def _get_band(self, channel: int) -> str:
        """Determine band from channel."""
        if channel <= 14:
            return "2.4GHz"
        elif channel <= 177:
            return "5GHz"
        else:
            return "6GHz"
    
    def _apply_oui_intelligence(self, node: WorldNode, rssi: int):
        """
        Apply OUI Vendor Intelligence to a node.
        
        100% OFFLINE - Uses static OUI table via OUI-IM.
        
        Updates:
        - vendor (if not already set)
        - vendor_confidence
        - vendor_type
        - is_randomized_mac
        - spoof_risk_score adjustments
        """
        oui_im = get_oui_intelligence()
        vendor_info = oui_im.lookup(node.mac)
        
        # Update vendor info from OUI-IM
        node.vendor_confidence = vendor_info.confidence
        node.vendor_type = vendor_info.vendor_type
        node.is_randomized_mac = vendor_info.is_randomized
        
        # Set vendor name if not already set
        if not node.vendor and vendor_info.is_known:
            node.vendor = vendor_info.name
            node.oui = vendor_info.prefix
        
        # Apply spoof risk adjustment from OUI-IM
        is_hidden = not node.ssid or node.ssid == ""
        spoof_adjustment = oui_im.calculate_spoof_risk_adjustment(
            mac=node.mac,
            claimed_vendor=node.vendor if node.vendor != vendor_info.name else "",
            is_hidden=is_hidden,
            rssi=rssi
        )
        
        if spoof_adjustment > 0:
            node.spoof_risk_score = min(100.0, node.spoof_risk_score + spoof_adjustment)
            
            # Add vendor mismatch anomaly if detected
            if node.vendor and vendor_info.is_known and node.vendor != vendor_info.name:
                if AnomalyType.VENDOR_MISMATCH not in node.anomaly_flags:
                    node.anomaly_flags.append(AnomalyType.VENDOR_MISMATCH)

    def _record_rssi_history(self, node: WorldNode, timestamp: float, rssi: int):
        """Record RSSI in rolling history."""
        node.rssi_history.append((timestamp, rssi))
        if len(node.rssi_history) > self.MAX_RSSI_HISTORY:
            node.rssi_history = node.rssi_history[-self.MAX_RSSI_HISTORY:]
    
    def _record_channel_history(self, node: WorldNode, timestamp: float, 
                                 channel: int, prev_channel: int):
        """Record channel changes."""
        if prev_channel != channel and prev_channel != 0:
            node.channel_history.append((timestamp, channel))
            if len(node.channel_history) > self.MAX_CHANNEL_HISTORY:
                node.channel_history = node.channel_history[-self.MAX_CHANNEL_HISTORY:]
    
    def _update_presence(self, node: WorldNode, timestamp: float):
        """Update presence intervals."""
        if not node.presence_intervals:
            node.presence_intervals.append((timestamp, timestamp))
        else:
            last_start, last_end = node.presence_intervals[-1]
            # If within timeout, extend interval
            if timestamp - last_end < self.VISIBILITY_TIMEOUT:
                node.presence_intervals[-1] = (last_start, timestamp)
            else:
                # New interval
                node.presence_intervals.append((timestamp, timestamp))
        
        # Trim old intervals
        if len(node.presence_intervals) > self.MAX_PRESENCE_INTERVALS:
            node.presence_intervals = node.presence_intervals[-self.MAX_PRESENCE_INTERVALS:]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MOVEMENT VECTOR COMPUTATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _compute_movement_vector(self, node: WorldNode, prev_rssi: int, 
                                  curr_rssi: int, timestamp: float):
        """
        Compute movement vector from RSSI derivatives.
        
        Formula:
        - motion_score = |dRSSI/dt| normalized
        - velocity = EMA(current_velocity, new_velocity, α)
        - approaching if dRSSI > 0, receding if dRSSI < 0
        """
        mv = node.movement
        
        if len(node.rssi_history) < 2:
            return
        
        # Get time delta
        t1, r1 = node.rssi_history[-2]
        t2, r2 = node.rssi_history[-1]
        dt = max(t2 - t1, 0.1)  # Prevent division by zero
        
        # Compute derivative (dRSSI/dt)
        drssi_dt = (r2 - r1) / dt
        
        # Normalize to speed (arbitrary units)
        new_speed = abs(drssi_dt) * 2.0
        
        # EMA smoothing
        mv.speed = self.EMA_ALPHA * new_speed + (1 - self.EMA_ALPHA) * mv.speed
        
        # Direction estimation using angle and RSSI gradient
        # If signal improving, moving towards; if declining, moving away
        if drssi_dt > self.MOVEMENT_THRESHOLD:
            mv.is_approaching = True
            mv.is_receding = False
        elif drssi_dt < -self.MOVEMENT_THRESHOLD:
            mv.is_approaching = False
            mv.is_receding = True
        else:
            mv.is_approaching = False
            mv.is_receding = False
        
        # Movement detection
        mv.is_moving = mv.speed > self.MOVEMENT_THRESHOLD
        
        # Compute velocity components (using current angle estimate)
        angle_rad = math.radians(node.angle_estimate)
        direction_sign = 1 if mv.is_approaching else -1
        mv.velocity_x = mv.speed * math.cos(angle_rad) * direction_sign
        mv.velocity_y = mv.speed * math.sin(angle_rad) * direction_sign
        
        # Predict next position
        if mv.is_moving:
            # Simple linear prediction
            mv.predicted_distance = node.distance_estimate - (mv.speed * direction_sign * 0.5)
            mv.predicted_angle = node.angle_estimate  # Assume same direction
            mv.prediction_confidence = min(70, int(50 + 20 * (1 - node.temporal.rssi_variance / 100)))
        else:
            mv.predicted_distance = node.distance_estimate
            mv.predicted_angle = node.angle_estimate
            mv.prediction_confidence = 80
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TEMPORAL SIGNATURE COMPUTATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _compute_temporal_signature(self, node: WorldNode):
        """
        Compute temporal behavior signature.
        
        Formulas:
        - presence_ratio = Σ(interval_durations) / total_time
        - rssi_variance = var(rssi_history)
        - rssi_trend = linear_regression_slope(rssi_history)
        """
        ts = node.temporal
        
        if len(node.rssi_history) < 3:
            return
        
        # Extract RSSI values
        rssi_values = [r for _, r in node.rssi_history]
        timestamps = [t for t, _ in node.rssi_history]
        
        # Basic stats
        ts.rssi_mean = statistics.mean(rssi_values)
        ts.rssi_variance = statistics.variance(rssi_values) if len(rssi_values) > 1 else 0.0
        
        # Compute trend (simple linear regression slope)
        if len(timestamps) >= 5:
            n = len(timestamps)
            t_mean = sum(timestamps) / n
            r_mean = ts.rssi_mean
            
            numerator = sum((t - t_mean) * (r - r_mean) for t, r in zip(timestamps, rssi_values))
            denominator = sum((t - t_mean) ** 2 for t in timestamps)
            
            if denominator > 0:
                ts.rssi_trend = numerator / denominator
        
        # Compute derivative (recent rate of change)
        if len(rssi_values) >= 2:
            recent = rssi_values[-5:]
            ts.rssi_derivative = (recent[-1] - recent[0]) / max(len(recent), 1)
        
        # Presence ratio
        total_time = timestamps[-1] - node.first_seen if timestamps else 1
        presence_time = sum(end - start for start, end in node.presence_intervals)
        ts.presence_ratio = min(1.0, presence_time / max(total_time, 1))
        
        # Session metrics
        ts.session_count = len(node.presence_intervals)
        if ts.session_count > 0:
            durations = [end - start for start, end in node.presence_intervals]
            ts.avg_session_duration = sum(durations) / ts.session_count
        
        # Pattern classification
        ts.pattern = self._classify_temporal_pattern(ts)
        ts.confidence = self._compute_pattern_confidence(ts, len(rssi_values))
    
    def _classify_temporal_pattern(self, ts: TemporalSignature) -> TemporalPattern:
        """Classify temporal behavior pattern."""
        # Always on: high presence ratio, low variance
        if ts.presence_ratio > 0.9 and ts.rssi_variance < 20:
            return TemporalPattern.ALWAYS_ON
        
        # Stationary: low movement, stable signal
        if ts.rssi_variance < 10 and abs(ts.rssi_derivative) < 1:
            return TemporalPattern.STATIONARY
        
        # Mobile: high variance, significant derivative
        if ts.rssi_variance > 50 or abs(ts.rssi_derivative) > 3:
            return TemporalPattern.MOBILE
        
        # Transient: low presence ratio, few sessions
        if ts.presence_ratio < 0.3 and ts.session_count <= 2:
            return TemporalPattern.TRANSIENT
        
        # Sporadic: moderate presence, multiple sessions
        if ts.presence_ratio < 0.6 and ts.session_count > 3:
            return TemporalPattern.SPORADIC
        
        # Periodic: check for regularity (simplified)
        if ts.session_count >= 3 and ts.presence_ratio > 0.4:
            return TemporalPattern.PERIODIC
        
        return TemporalPattern.UNKNOWN
    
    def _compute_pattern_confidence(self, ts: TemporalSignature, sample_count: int) -> int:
        """Compute confidence in pattern classification."""
        base_confidence = min(80, sample_count * 2)
        
        # Boost for clear patterns
        if ts.pattern == TemporalPattern.ALWAYS_ON and ts.presence_ratio > 0.95:
            base_confidence += 15
        elif ts.pattern == TemporalPattern.STATIONARY and ts.rssi_variance < 5:
            base_confidence += 10
        
        return min(95, base_confidence)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANOMALY DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _detect_anomalies(self, node: WorldNode, prev_rssi: int, prev_channel: int):
        """
        Detect anomalies using multi-factor analysis.
        
        Formula: anomaly if |value - mean| > threshold * std_dev
        """
        now = time.time()
        new_anomalies = []
        
        # Signal spike/drop detection
        if len(node.rssi_history) >= 5:
            rssi_values = [r for _, r in node.rssi_history[-20:]]
            mean_rssi = statistics.mean(rssi_values)
            std_rssi = statistics.stdev(rssi_values) if len(rssi_values) > 1 else 5.0
            
            current_rssi = node.rssi
            deviation = abs(current_rssi - mean_rssi)
            
            if deviation > self.ANOMALY_THRESHOLD * std_rssi:
                if current_rssi > mean_rssi:
                    new_anomalies.append(AnomalyType.SIGNAL_SPIKE)
                else:
                    new_anomalies.append(AnomalyType.SIGNAL_DROP)
        
        # Channel hop detection
        if prev_channel != 0 and prev_channel != node.channel:
            # Check if frequent
            if len(node.channel_history) >= 3:
                recent_hops = len([1 for t, _ in node.channel_history if now - t < 60])
                if recent_hops >= 2:
                    new_anomalies.append(AnomalyType.CHANNEL_HOP)
        
        # Rapid movement detection
        if node.movement.is_moving and node.movement.speed > 10:
            new_anomalies.append(AnomalyType.RAPID_MOVEMENT)
        
        # Record anomalies
        for anomaly in new_anomalies:
            if anomaly not in node.anomaly_flags:
                node.anomaly_flags.append(anomaly)
            node.temporal.anomaly_history.append((now, anomaly))
            node.temporal.last_anomaly = anomaly
            node.temporal.anomaly_count += 1
        
        # Trim history
        if len(node.temporal.anomaly_history) > self.MAX_ANOMALY_HISTORY:
            node.temporal.anomaly_history = node.temporal.anomaly_history[-self.MAX_ANOMALY_HISTORY:]
        
        # Clear old anomaly flags
        node.anomaly_flags = node.anomaly_flags[-5:]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ENVIRONMENTAL CONTEXT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _compute_environment_context(self, node: WorldNode):
        """
        Compute environmental context scores.
        
        Formulas:
        - interference_score = Σ overlapping_channels * power_density
        - congestion_score = Σ APs_on_same_channel weighted by RSSI
        - wall_density = (expected_RSSI - observed_RSSI) / attenuation_constant
        """
        env = node.environment
        
        # Count APs on same channel
        same_channel_macs = self.channel_index.get(node.channel, set())
        env.aps_on_channel = len(same_channel_macs)
        
        # Congestion score (0-100)
        if env.aps_on_channel <= 2:
            env.congestion_score = 0
        elif env.aps_on_channel <= 5:
            env.congestion_score = 25 + (env.aps_on_channel - 2) * 10
        elif env.aps_on_channel <= 10:
            env.congestion_score = 55 + (env.aps_on_channel - 5) * 5
        else:
            env.congestion_score = min(100, 80 + (env.aps_on_channel - 10) * 2)
        
        # Interference score (sum of overlapping channel powers)
        interference_sum = 0
        for ch in range(max(1, node.channel - 2), min(14, node.channel + 3)):
            if ch != node.channel:
                for other_mac in self.channel_index.get(ch, set()):
                    if other_mac in self.nodes:
                        other_rssi = self.nodes[other_mac].rssi
                        # Weight by proximity (higher RSSI = more interference)
                        interference_sum += max(0, (other_rssi + 100) / 50)
        
        env.interference_score = min(100, interference_sum * 10)
        env.interference_sources = len([m for ch in range(max(1, node.channel - 2), 
                                                           min(14, node.channel + 3))
                                         if ch != node.channel
                                         for m in self.channel_index.get(ch, set())])
        
        # Wall density estimation
        # expected_RSSI at distance d with no walls
        expected_rssi = self.TX_POWER_DBM - 40 - 10 * self.PATH_LOSS_EXPONENT * math.log10(max(1, node.distance_estimate))
        actual_rssi = node.rssi
        attenuation = expected_rssi - actual_rssi
        
        env.attenuation_db = max(0, attenuation)
        env.estimated_walls = int(attenuation / self.WALL_ATTENUATION_DB)
        env.wall_density_score = min(100, env.estimated_walls * 20)
        
        # Channel quality (inverse of congestion + interference)
        env.channel_quality = max(0, 100 - (env.congestion_score * 0.5 + env.interference_score * 0.5))
        
        # Environment classification
        if env.interference_score > 70 and env.congestion_score > 70:
            env.environment_type = EnvironmentType.STORMY
        elif env.congestion_score > 50:
            env.environment_type = EnvironmentType.CONGESTED
        elif env.wall_density_score > 60:
            env.environment_type = EnvironmentType.SHIELDED
        elif env.congestion_score < 20 and env.interference_score < 20:
            env.environment_type = EnvironmentType.QUIET
        else:
            env.environment_type = EnvironmentType.NORMAL
    
    def refresh_environments(self):
        """
        Recompute environment context for all nodes.
        
        Call this after batch updates to refresh congestion/interference scores.
        """
        for node in self.nodes.values():
            self._compute_environment_context(node)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HOME POINT SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_home_point(self, mac: str) -> bool:
        """
        Set the Home Point (user-selected only, NEVER inferred).
        
        Home Point anchors the radar and all relative positions.
        """
        if mac not in self.nodes:
            return False
        
        self.home_point = mac
        home_node = self.nodes[mac]
        self.home_point_vector = (0.0, 0.0)  # Home is always origin
        
        # Recompute all relative positions
        for node in self.nodes.values():
            self._compute_home_relative(node)
        
        return True
    
    def clear_home_point(self):
        """Clear the Home Point."""
        self.home_point = None
        self.home_point_vector = (0.0, 0.0)
        
        for node in self.nodes.values():
            node.home_relative_distance = 0.0
            node.home_relative_angle = 0.0
            node.home_relative_vector = (0.0, 0.0)
    
    def _compute_home_relative(self, node: WorldNode):
        """
        Compute position relative to Home Point.
        
        Formula: relative_vector = device_vector - home_point_vector
        """
        if not self.home_point or self.home_point not in self.nodes:
            return
        
        home_node = self.nodes[self.home_point]
        
        # Home is at origin, so relative = absolute for home
        if node.mac == self.home_point:
            node.home_relative_distance = 0.0
            node.home_relative_angle = 0.0
            node.home_relative_vector = (0.0, 0.0)
            return
        
        # Compute vector from home to node
        # Using distance and angle estimates
        home_x = 0.0
        home_y = 0.0
        
        node_angle_rad = math.radians(node.angle_estimate)
        node_x = node.distance_estimate * math.cos(node_angle_rad)
        node_y = node.distance_estimate * math.sin(node_angle_rad)
        
        rel_x = node_x - home_x
        rel_y = node_y - home_y
        
        node.home_relative_vector = (rel_x, rel_y)
        node.home_relative_distance = math.sqrt(rel_x**2 + rel_y**2)
        node.home_relative_angle = math.degrees(math.atan2(rel_y, rel_x)) % 360
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIDENCE SCORING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _compute_confidence(self, node: WorldNode):
        """
        Compute overall confidence score.
        
        Multi-factor: sample count, variance, recency, fingerprint confidence
        """
        factors = []
        
        # Sample count factor
        sample_conf = min(100, len(node.rssi_history) * 2)
        factors.append(sample_conf)
        
        # Variance factor (lower variance = higher confidence)
        if node.temporal.rssi_variance > 0:
            var_conf = max(0, 100 - node.temporal.rssi_variance * 2)
        else:
            var_conf = 80
        factors.append(var_conf)
        
        # Recency factor
        age = time.time() - node.last_seen
        if age < 5:
            recency_conf = 100
        elif age < 30:
            recency_conf = 80
        elif age < 60:
            recency_conf = 50
        else:
            recency_conf = 20
        factors.append(recency_conf)
        
        # Fingerprint confidence
        factors.append(node.fingerprint_confidence)
        
        # Average
        node.confidence_score = sum(factors) / len(factors)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIP INFERENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def compute_relationships(self):
        """
        Compute all relationship edges between nodes.
        
        Types:
        - Same SSID
        - Same vendor
        - Co-presence
        - Same channel (interference)
        
        100% PASSIVE - Only analyzes existing data.
        """
        now = time.time()
        new_edges = []
        
        # Same SSID relationships
        for ssid, macs in self.ssid_index.items():
            if len(macs) > 1 and ssid:
                mac_list = list(macs)
                for i, mac1 in enumerate(mac_list):
                    for mac2 in mac_list[i+1:]:
                        edge_id = f"{mac1}_{mac2}_same_ssid"
                        if edge_id not in self.edges:
                            self.edges[edge_id] = GraphEdge(
                                source_mac=mac1,
                                target_mac=mac2,
                                edge_type=EdgeType.SAME_SSID,
                                first_seen=now
                            )
                        edge = self.edges[edge_id]
                        edge.last_seen = now
                        edge.observation_count += 1
                        edge.weight = min(1.0, edge.observation_count / 10)
                        new_edges.append(edge_id)
        
        # Same vendor relationships
        for vendor, macs in self.vendor_index.items():
            if len(macs) > 1 and vendor and vendor != "Unknown":
                mac_list = list(macs)
                for i, mac1 in enumerate(mac_list):
                    for mac2 in mac_list[i+1:]:
                        edge_id = f"{mac1}_{mac2}_same_vendor"
                        if edge_id not in self.edges:
                            self.edges[edge_id] = GraphEdge(
                                source_mac=mac1,
                                target_mac=mac2,
                                edge_type=EdgeType.SAME_VENDOR,
                                first_seen=now
                            )
                        edge = self.edges[edge_id]
                        edge.last_seen = now
                        edge.observation_count += 1
                        edge.weight = 0.5  # Weaker relationship
                        new_edges.append(edge_id)
        
        # Interference relationships (same channel)
        for channel, macs in self.channel_index.items():
            if len(macs) > 1:
                mac_list = list(macs)
                for i, mac1 in enumerate(mac_list):
                    for mac2 in mac_list[i+1:]:
                        edge_id = f"{mac1}_{mac2}_interference"
                        if edge_id not in self.edges:
                            self.edges[edge_id] = GraphEdge(
                                source_mac=mac1,
                                target_mac=mac2,
                                edge_type=EdgeType.INTERFERENCE,
                                first_seen=now
                            )
                        edge = self.edges[edge_id]
                        edge.last_seen = now
                        edge.observation_count += 1
                        new_edges.append(edge_id)
        
        # Co-presence relationships
        self._compute_co_presence_edges()
        
        # Update node edge references
        for edge_id in new_edges:
            edge = self.edges[edge_id]
            if edge_id not in self.nodes.get(edge.source_mac, WorldNode(mac="")).edges:
                self.nodes[edge.source_mac].edges.append(edge_id)
            if edge_id not in self.nodes.get(edge.target_mac, WorldNode(mac="")).edges:
                self.nodes[edge.target_mac].edges.append(edge_id)
        
        self.total_edges = len(self.edges)
    
    def _compute_co_presence_edges(self):
        """
        Compute co-presence correlation edges.
        
        Formula: corr = overlap(presence_intervals) / total_time
        """
        now = time.time()
        macs = list(self.nodes.keys())
        
        for i, mac1 in enumerate(macs):
            node1 = self.nodes[mac1]
            if len(node1.presence_intervals) < 2:
                continue
            
            for mac2 in macs[i+1:]:
                node2 = self.nodes[mac2]
                if len(node2.presence_intervals) < 2:
                    continue
                
                # Compute overlap
                overlap = self._compute_interval_overlap(
                    node1.presence_intervals, 
                    node2.presence_intervals
                )
                
                total_time = now - min(node1.first_seen, node2.first_seen)
                if total_time <= 0:
                    continue
                
                co_presence_ratio = overlap / total_time
                
                if co_presence_ratio >= self.CO_PRESENCE_THRESHOLD:
                    edge_id = f"{mac1}_{mac2}_co_presence"
                    if edge_id not in self.edges:
                        self.edges[edge_id] = GraphEdge(
                            source_mac=mac1,
                            target_mac=mac2,
                            edge_type=EdgeType.CO_PRESENCE,
                            first_seen=now
                        )
                    edge = self.edges[edge_id]
                    edge.last_seen = now
                    edge.co_presence_ratio = co_presence_ratio
                    edge.weight = co_presence_ratio
                    edge.confidence = int(co_presence_ratio * 100)
    
    def _compute_interval_overlap(self, intervals1: List[Tuple[float, float]], 
                                   intervals2: List[Tuple[float, float]]) -> float:
        """Compute total overlap between two sets of intervals."""
        total_overlap = 0.0
        
        for start1, end1 in intervals1:
            for start2, end2 in intervals2:
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                if overlap_end > overlap_start:
                    total_overlap += overlap_end - overlap_start
        
        return total_overlap
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLUSTERING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def compute_clusters(self):
        """
        Compute clusters of related nodes.
        
        Cluster types:
        - Mesh: Same SSID, same vendor, different channels
        - SSID group: Same SSID
        - Vendor group: Same vendor
        
        100% PASSIVE - Only analyzes existing data.
        """
        self.clusters.clear()
        
        # Mesh cluster detection
        for ssid, macs in self.ssid_index.items():
            if len(macs) >= 2 and ssid:
                # Check if same vendor
                vendors = set()
                channels = set()
                for mac in macs:
                    node = self.nodes.get(mac)
                    if node:
                        vendors.add(node.vendor)
                        channels.add(node.channel)
                
                # Mesh: same vendor, multiple channels
                if len(vendors) == 1 and len(channels) > 1 and list(vendors)[0] != "Unknown":
                    cluster_id = f"mesh_{ssid}_{list(vendors)[0][:10]}"
                    self.clusters[cluster_id] = GraphCluster(
                        cluster_id=cluster_id,
                        cluster_type="mesh",
                        members=macs.copy(),
                        channel_spread=len(channels)
                    )
                    
                    # Mark nodes
                    for mac in macs:
                        if mac in self.nodes:
                            self.nodes[mac].cluster_id = cluster_id
                            self.nodes[mac].node_type = NodeType.MESH_NODE
                
                # SSID group (not mesh)
                elif len(macs) >= 2:
                    cluster_id = f"ssid_{ssid}"
                    self.clusters[cluster_id] = GraphCluster(
                        cluster_id=cluster_id,
                        cluster_type="ssid_group",
                        members=macs.copy()
                    )
        
        # Compute cluster metrics
        for cluster in self.clusters.values():
            signals = []
            for mac in cluster.members:
                node = self.nodes.get(mac)
                if node:
                    signals.append(node.rssi)
            
            if signals:
                cluster.avg_signal = statistics.mean(signals)
            
            # Cohesion: how similar are the members
            if len(signals) > 1:
                variance = statistics.variance(signals)
                cluster.cohesion_score = max(0, 100 - variance)
        
        self.total_clusters = len(self.clusters)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GLOBAL ENVIRONMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def compute_global_environment(self):
        """Compute global environmental context."""
        env = self.global_environment
        
        # Aggregate across all visible nodes
        interference_scores = []
        congestion_scores = []
        wall_scores = []
        
        for node in self.nodes.values():
            if node.is_visible:
                interference_scores.append(node.environment.interference_score)
                congestion_scores.append(node.environment.congestion_score)
                wall_scores.append(node.environment.wall_density_score)
        
        if interference_scores:
            env.interference_score = statistics.mean(interference_scores)
            env.congestion_score = statistics.mean(congestion_scores)
            env.wall_density_score = statistics.mean(wall_scores)
        
        # Classify global environment
        if env.interference_score > 70 and env.congestion_score > 70:
            env.environment_type = EnvironmentType.STORMY
        elif env.congestion_score > 50:
            env.environment_type = EnvironmentType.CONGESTED
        elif env.wall_density_score > 60:
            env.environment_type = EnvironmentType.SHIELDED
        elif env.congestion_score < 20 and env.interference_score < 20:
            env.environment_type = EnvironmentType.QUIET
        else:
            env.environment_type = EnvironmentType.NORMAL
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAINTENANCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_visibility(self):
        """Update visibility status for all nodes."""
        now = time.time()
        self.active_nodes = 0
        
        for node in self.nodes.values():
            if now - node.last_seen > self.VISIBILITY_TIMEOUT:
                node.is_visible = False
            else:
                node.is_visible = True
                self.active_nodes += 1
    
    def prune_old_data(self, max_age_seconds: float = 3600):
        """Remove nodes not seen for a long time."""
        now = time.time()
        to_remove = [mac for mac, node in self.nodes.items() 
                     if now - node.last_seen > max_age_seconds]
        
        for mac in to_remove:
            del self.nodes[mac]
            
            # Clean indices
            for ssid_macs in self.ssid_index.values():
                ssid_macs.discard(mac)
            for ch_macs in self.channel_index.values():
                ch_macs.discard(mac)
            for v_macs in self.vendor_index.values():
                v_macs.discard(mac)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_node(self, mac: str) -> Optional[WorldNode]:
        """Get a node by MAC."""
        return self.nodes.get(mac)
    
    def get_all_nodes(self) -> List[WorldNode]:
        """Get all nodes sorted by signal strength."""
        return sorted(self.nodes.values(), key=lambda n: n.rssi, reverse=True)
    
    def get_visible_nodes(self) -> List[WorldNode]:
        """Get currently visible nodes."""
        return [n for n in self.nodes.values() if n.is_visible]
    
    def get_edges_for_node(self, mac: str) -> List[GraphEdge]:
        """Get all edges connected to a node."""
        node = self.nodes.get(mac)
        if not node:
            return []
        return [self.edges[eid] for eid in node.edges if eid in self.edges]
    
    def get_cluster_members(self, cluster_id: str) -> List[WorldNode]:
        """Get all nodes in a cluster."""
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return []
        return [self.nodes[mac] for mac in cluster.members if mac in self.nodes]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get model statistics."""
        return {
            'total_nodes': self.total_nodes_seen,
            'active_nodes': self.active_nodes,
            'total_edges': self.total_edges,
            'total_clusters': self.total_clusters,
            'home_point': self.home_point,
            'environment': self.global_environment.environment_type.value,
            'last_update': self.last_update,
        }
    
    def to_radar_vectors(self) -> List[Dict[str, Any]]:
        """
        Export nodes as radar-compatible vectors.
        
        Returns unified vectors for radar rendering.
        """
        vectors = []
        for node in self.get_visible_nodes():
            vectors.append({
                'mac': node.mac,
                'ssid': node.ssid,
                'distance': node.distance_estimate,
                'angle': node.angle_estimate,
                'signal': node.rssi,
                'stability': node.stability_score,
                'spoof_risk': node.spoof_risk_score,
                'is_moving': node.movement.is_moving,
                'movement_speed': node.movement.speed,
                'movement_direction': 'approaching' if node.movement.is_approaching else 'receding' if node.movement.is_receding else 'stable',
                'node_type': node.node_type.value,
                'cluster_id': node.cluster_id,
                'environment': node.environment.environment_type.value,
                'confidence': node.confidence_score,
                'home_relative_distance': node.home_relative_distance,
                'home_relative_angle': node.home_relative_angle,
            })
        return vectors


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_uwm: Optional[UnifiedWorldModel] = None


def get_world_model() -> UnifiedWorldModel:
    """Get the global UWM-X instance."""
    global _uwm
    if _uwm is None:
        _uwm = UnifiedWorldModel()
    return _uwm
