"""
Hidden Network Classification Engine (HNCE)

100% PASSIVE - Analyzes hidden SSIDs to classify their purpose:
- Mesh nodes
- Backhaul links
- Enterprise APs
- Extenders/Repeaters
- Rogue AP candidates
- Spoof candidates
- Misconfigured devices

All analysis is performed on passively received beacon data only.
OUI-IM integration provides enhanced vendor intelligence for classification.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import time
import math
from collections import defaultdict

# OUI-IM Integration (100% offline vendor intelligence)
from nexus.core.oui_vendor import get_oui_intelligence, VendorInfo


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class HiddenNetworkType(Enum):
    """Classification of hidden network purpose."""
    UNKNOWN = "unknown"
    MESH_NODE = "mesh_node"
    BACKHAUL_LINK = "backhaul_link"
    ENTERPRISE_AP = "enterprise_ap"
    EXTENDER_REPEATER = "extender_repeater"
    ROGUE_CANDIDATE = "rogue_candidate"
    SPOOF_CANDIDATE = "spoof_candidate"
    MISCONFIGURED = "misconfigured"
    IOT_DEVICE = "iot_device"
    GUEST_ISOLATED = "guest_isolated"


class RogueRisk(Enum):
    """Rogue/spoof risk level."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ClusterType(Enum):
    """Hidden network cluster classification."""
    UNKNOWN = "unknown"
    MESH_CLUSTER = "mesh_cluster"
    ENTERPRISE_CLUSTER = "enterprise_cluster"
    MIXED_VENDOR = "mixed_vendor"
    SINGLE_DEVICE = "single_device"
    BACKHAUL_GROUP = "backhaul_group"
    SUSPICIOUS_GROUP = "suspicious_group"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HiddenNetworkProfile:
    """Full classification profile for a hidden network."""
    bssid: str
    oui: str = ""
    vendor: str = ""
    channel: int = 0
    band: str = "2.4GHz"
    rssi: int = -70
    security: str = ""
    
    # OUI-IM Vendor Intelligence
    vendor_confidence: float = 0.0
    vendor_type: str = "unknown"       # consumer, enterprise, iot, mesh, mobile, isp
    is_randomized_mac: bool = False
    vendor_mismatch: bool = False
    
    # Classification
    network_type: HiddenNetworkType = HiddenNetworkType.UNKNOWN
    cluster_id: Optional[str] = None
    
    # Scores (0-100)
    oui_consistency_score: float = 0.0
    channel_coherence_score: float = 0.0
    signal_grouping_score: float = 0.0
    rogue_likelihood_score: float = 0.0
    
    # Flags
    is_rogue_candidate: bool = False
    is_spoof_candidate: bool = False
    is_outlier: bool = False
    
    # Temporal (if available)
    first_seen: float = 0.0
    last_seen: float = 0.0
    observation_count: int = 0
    stability_score: float = 50.0
    
    # Classification confidence
    classification_confidence: int = 0
    classification_reason: str = ""
    
    # Related networks
    related_bssids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'bssid': self.bssid,
            'oui': self.oui,
            'vendor': self.vendor,
            'channel': self.channel,
            'band': self.band,
            'rssi': self.rssi,
            'security': self.security,
            'vendor_confidence': self.vendor_confidence,
            'vendor_type': self.vendor_type,
            'is_randomized_mac': self.is_randomized_mac,
            'vendor_mismatch': self.vendor_mismatch,
            'network_type': self.network_type.value,
            'cluster_id': self.cluster_id,
            'oui_consistency_score': self.oui_consistency_score,
            'channel_coherence_score': self.channel_coherence_score,
            'signal_grouping_score': self.signal_grouping_score,
            'rogue_likelihood_score': self.rogue_likelihood_score,
            'is_rogue_candidate': self.is_rogue_candidate,
            'is_spoof_candidate': self.is_spoof_candidate,
            'is_outlier': self.is_outlier,
            'stability_score': self.stability_score,
            'classification_confidence': self.classification_confidence,
            'classification_reason': self.classification_reason,
            'related_bssids': self.related_bssids
        }


@dataclass
class HiddenCluster:
    """A cluster of related hidden networks."""
    cluster_id: str
    cluster_type: ClusterType = ClusterType.UNKNOWN
    members: List[str] = field(default_factory=list)  # BSSIDs
    
    # Cluster metrics
    oui_consistency: float = 0.0
    channel_coherence: float = 0.0
    signal_similarity: float = 0.0
    
    # Aggregate scores
    avg_rssi: float = -70.0
    channel_spread: int = 0
    vendor_count: int = 0
    
    # Risk assessment
    rogue_risk: RogueRisk = RogueRisk.NONE
    suspicion_flags: List[str] = field(default_factory=list)
    
    # Classification
    classification_label: str = ""
    confidence: int = 0


@dataclass 
class HNCEAnalysisResult:
    """Complete HNCE analysis result."""
    timestamp: float = 0.0
    hidden_count: int = 0
    cluster_count: int = 0
    
    # Profiles indexed by BSSID
    profiles: Dict[str, HiddenNetworkProfile] = field(default_factory=dict)
    
    # Clusters indexed by cluster_id
    clusters: Dict[str, HiddenCluster] = field(default_factory=dict)
    
    # Rogue candidates
    rogue_candidates: List[str] = field(default_factory=list)
    spoof_candidates: List[str] = field(default_factory=list)
    
    # Summary
    mesh_count: int = 0
    enterprise_count: int = 0
    backhaul_count: int = 0
    suspicious_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

# OUIs commonly used for mesh/enterprise systems
MESH_VENDOR_OUIS = {
    'E4:F0:42', 'F0:99:BF',  # eero
    '18:E8:29', '70:3A:CB',  # Netgear Orbi
    'B4:FB:E4', 'AC:84:C6',  # TP-Link Deco
    '78:8A:20', 'A4:77:33',  # Ubiquiti
    '00:18:0A',              # Aruba
    '00:0B:86',              # Aruba
    '64:D1:54',              # Aruba
    '00:24:6C',              # Ruckus
    'EC:58:EA',              # Ruckus
    '00:1A:1E',              # Cisco/Meraki
    '00:18:74',              # Cisco
    '88:15:44',              # Cisco Meraki
    '0C:8D:DB',              # Cisco Meraki
    'AC:17:C8',              # Cisco Meraki
}

ENTERPRISE_VENDOR_OUIS = {
    '00:18:0A', '00:0B:86', '64:D1:54',  # Aruba
    '00:24:6C', 'EC:58:EA',              # Ruckus
    '00:1A:1E', '00:18:74',              # Cisco
    '88:15:44', '0C:8D:DB', 'AC:17:C8',  # Cisco Meraki
    '00:26:86', '00:23:69',              # Extreme Networks
    '00:04:96',                          # HPE/Aruba
    '00:1B:2F', '00:21:55',              # Meru/Fortinet
}

IOT_VENDOR_OUIS = {
    'B4:E6:2D', '68:C6:3A',  # Ring
    '18:B4:30', '50:14:79',  # Nest
    'F0:D2:F1', '44:65:0D',  # Amazon Echo
    '70:EE:50', '38:F7:3D',  # Smart TVs
    '00:17:88',              # Philips Hue
    'D0:73:D5',              # Wyze
    'AC:CF:23',              # Shelly
}

# Channels commonly used for backhaul
BACKHAUL_CHANNELS = {36, 40, 44, 48, 149, 153, 157, 161, 165}

# DFS channels
DFS_CHANNELS = {52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144}


# ═══════════════════════════════════════════════════════════════════════════════
# HIDDEN NETWORK CLASSIFICATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class HiddenNetworkClassifier:
    """
    Hidden Network Classification Engine (HNCE)
    
    100% PASSIVE - All analysis from received beacon/probe data only.
    """
    
    def __init__(self):
        # Hidden network profiles
        self.profiles: Dict[str, HiddenNetworkProfile] = {}
        
        # Clusters
        self.clusters: Dict[str, HiddenCluster] = {}
        
        # Indexes
        self.oui_index: Dict[str, Set[str]] = defaultdict(set)  # OUI -> BSSIDs
        self.channel_index: Dict[int, Set[str]] = defaultdict(set)  # Channel -> BSSIDs
        self.vendor_index: Dict[str, Set[str]] = defaultdict(set)  # Vendor -> BSSIDs
        
        # Known visible networks (for correlation)
        self.visible_networks: Dict[str, dict] = {}
        
        # Analysis state
        self.last_analysis: Optional[HNCEAnalysisResult] = None
        
    def record_hidden_network(
        self,
        bssid: str,
        channel: int,
        rssi: int,
        security: str = "",
        vendor: str = "",
        stability: float = 50.0
    ) -> HiddenNetworkProfile:
        """
        Record a hidden network observation.
        
        100% PASSIVE - Only processes received beacon data.
        OUI-IM provides vendor intelligence for classification.
        """
        now = time.time()
        oui = bssid[:8].upper() if len(bssid) >= 8 else ""
        band = "5GHz" if channel > 14 else "2.4GHz"
        
        # OUI-IM Vendor Intelligence (100% offline)
        oui_im = get_oui_intelligence()
        vendor_info = oui_im.lookup(bssid)
        
        if bssid in self.profiles:
            profile = self.profiles[bssid]
            profile.last_seen = now
            profile.observation_count += 1
            profile.rssi = rssi
            profile.stability_score = stability
            if channel != profile.channel:
                # Channel changed - could indicate DFS hopping
                profile.channel = channel
        else:
            # Use OUI-IM vendor name if not provided
            resolved_vendor = vendor if vendor else (vendor_info.name if vendor_info.is_known else "")
            
            profile = HiddenNetworkProfile(
                bssid=bssid,
                oui=oui,
                vendor=resolved_vendor,
                channel=channel,
                band=band,
                rssi=rssi,
                security=security,
                first_seen=now,
                last_seen=now,
                observation_count=1,
                stability_score=stability
            )
            self.profiles[bssid] = profile
        
        # Apply OUI-IM intelligence
        profile.vendor_confidence = vendor_info.confidence
        profile.vendor_type = vendor_info.vendor_type
        profile.is_randomized_mac = vendor_info.is_randomized
        
        # Detect vendor mismatch
        if profile.vendor and vendor_info.is_known:
            profile.vendor_mismatch = profile.vendor.lower() not in vendor_info.name.lower()
        
        # Update indexes
        self.oui_index[oui].add(bssid)
        self.channel_index[channel].add(bssid)
        if profile.vendor:
            self.vendor_index[profile.vendor].add(bssid)
        
        return profile
    
    def record_visible_network(
        self,
        bssid: str,
        ssid: str,
        channel: int,
        rssi: int,
        security: str = "",
        vendor: str = ""
    ):
        """
        Record a visible network for correlation with hidden networks.
        
        100% PASSIVE.
        """
        self.visible_networks[bssid] = {
            'bssid': bssid,
            'ssid': ssid,
            'channel': channel,
            'rssi': rssi,
            'security': security,
            'vendor': vendor,
            'oui': bssid[:8].upper() if len(bssid) >= 8 else ""
        }
    
    def analyze(self) -> HNCEAnalysisResult:
        """
        Perform full HNCE analysis on all recorded hidden networks.
        
        100% PASSIVE - All analysis from cached beacon data.
        """
        result = HNCEAnalysisResult(
            timestamp=time.time(),
            hidden_count=len(self.profiles)
        )
        
        if not self.profiles:
            self.last_analysis = result
            return result
        
        # Step 1: Group by OUI prefix
        self._group_by_oui()
        
        # Step 2: Cluster by channel proximity
        self._cluster_by_channel()
        
        # Step 3: Score each profile
        for bssid, profile in self.profiles.items():
            self._compute_oui_consistency(profile)
            self._compute_channel_coherence(profile)
            self._compute_signal_grouping(profile)
            self._compute_rogue_likelihood(profile)
            self._classify_network(profile)
        
        # Step 4: Build clusters
        self._build_clusters()
        
        # Step 5: Classify clusters
        for cluster in self.clusters.values():
            self._classify_cluster(cluster)
        
        # Step 6: Detect outliers and rogues
        self._detect_outliers()
        self._flag_rogue_candidates()
        
        # Compile results
        result.profiles = {k: v for k, v in self.profiles.items()}
        result.clusters = {k: v for k, v in self.clusters.items()}
        result.cluster_count = len(self.clusters)
        
        # Counts by type
        for profile in self.profiles.values():
            if profile.network_type == HiddenNetworkType.MESH_NODE:
                result.mesh_count += 1
            elif profile.network_type == HiddenNetworkType.ENTERPRISE_AP:
                result.enterprise_count += 1
            elif profile.network_type == HiddenNetworkType.BACKHAUL_LINK:
                result.backhaul_count += 1
            
            if profile.is_rogue_candidate:
                result.rogue_candidates.append(profile.bssid)
                result.suspicious_count += 1
            if profile.is_spoof_candidate:
                result.spoof_candidates.append(profile.bssid)
        
        self.last_analysis = result
        return result
    
    def _group_by_oui(self):
        """Group hidden networks by OUI prefix."""
        # Already done via oui_index during recording
        pass
    
    def _cluster_by_channel(self):
        """Cluster hidden networks by channel proximity."""
        # Group 2.4GHz channels (overlapping: 1-5, 6-10, 11-14)
        # Group 5GHz channels by proximity
        pass
    
    def _compute_oui_consistency(self, profile: HiddenNetworkProfile):
        """
        Compute OUI consistency score.
        
        Formula: vendor_match_ratio = matching_oui_count / total_in_group
        """
        oui = profile.oui
        if not oui:
            profile.oui_consistency_score = 0.0
            return
        
        same_oui_count = len(self.oui_index.get(oui, set()))
        
        if same_oui_count <= 1:
            # Single device with this OUI
            profile.oui_consistency_score = 50.0
        else:
            # Multiple devices share OUI - likely same deployment
            profile.oui_consistency_score = min(100.0, 50.0 + same_oui_count * 10)
        
        # Check if OUI matches known patterns
        if oui in MESH_VENDOR_OUIS:
            profile.oui_consistency_score = min(100.0, profile.oui_consistency_score + 20)
        elif oui in ENTERPRISE_VENDOR_OUIS:
            profile.oui_consistency_score = min(100.0, profile.oui_consistency_score + 15)
    
    def _compute_channel_coherence(self, profile: HiddenNetworkProfile):
        """
        Compute channel coherence score.
        
        Formula: coherence = 1 / (1 + channel_variance)
        """
        channel = profile.channel
        same_channel_count = len(self.channel_index.get(channel, set()))
        
        # Get channels used by same OUI
        same_oui_bssids = self.oui_index.get(profile.oui, set())
        if len(same_oui_bssids) > 1:
            channels = [self.profiles[b].channel for b in same_oui_bssids if b in self.profiles]
            if channels:
                channel_variance = self._variance(channels)
                coherence = 1 / (1 + channel_variance)
                profile.channel_coherence_score = coherence * 100
            else:
                profile.channel_coherence_score = 50.0
        else:
            profile.channel_coherence_score = 50.0
        
        # Bonus for expected backhaul channels
        if channel in BACKHAUL_CHANNELS:
            profile.channel_coherence_score = min(100.0, profile.channel_coherence_score + 10)
    
    def _compute_signal_grouping(self, profile: HiddenNetworkProfile):
        """
        Compute signal grouping score.
        
        Formula: grouping = 1 / (1 + RSSI_variance)
        """
        same_oui_bssids = self.oui_index.get(profile.oui, set())
        
        if len(same_oui_bssids) > 1:
            rssi_values = [self.profiles[b].rssi for b in same_oui_bssids if b in self.profiles]
            if rssi_values:
                rssi_variance = self._variance(rssi_values)
                grouping = 1 / (1 + rssi_variance / 100)  # Normalize
                profile.signal_grouping_score = grouping * 100
            else:
                profile.signal_grouping_score = 50.0
        else:
            profile.signal_grouping_score = 50.0
    
    def _compute_rogue_likelihood(self, profile: HiddenNetworkProfile):
        """
        Compute rogue likelihood score.
        
        Formula: rogue_likelihood = weighted_sum(OUI_mismatch, channel_outlier, RSSI_outlier, BSSID_anomaly, OUI-IM_adjustment)
        
        OUI-IM Integration enhances detection with:
        - Randomized MAC detection
        - Vendor confidence scoring
        - Vendor type awareness
        """
        score = 0.0
        weights = {
            'oui_mismatch': 0.25,
            'channel_outlier': 0.20,
            'rssi_outlier': 0.15,
            'bssid_anomaly': 0.15,
            'security_weak': 0.10,
            'oui_im_risk': 0.15  # New OUI-IM weight
        }
        
        # Get OUI-IM intelligence
        oui_im = get_oui_intelligence()
        
        # OUI mismatch - unknown or suspicious OUI (base score)
        oui = profile.oui
        if not oui:
            score += weights['oui_mismatch'] * 80
        elif oui not in MESH_VENDOR_OUIS and oui not in ENTERPRISE_VENDOR_OUIS and oui not in IOT_VENDOR_OUIS:
            # Check if it matches visible networks
            visible_ouis = {v.get('oui', '') for v in self.visible_networks.values()}
            if oui not in visible_ouis:
                score += weights['oui_mismatch'] * 50
        
        # OUI-IM Enhanced Risk Assessment
        oui_im_adjustment = oui_im.calculate_rogue_risk_adjustment(
            mac=profile.bssid,
            is_hidden=True,  # Always hidden in HNCE
            rssi=profile.rssi,
            channel=profile.channel
        )
        score += weights['oui_im_risk'] * oui_im_adjustment
        
        # Bonus risk for randomized MAC on hidden network
        if profile.is_randomized_mac:
            score += weights['oui_im_risk'] * 25
        
        # Vendor mismatch detected by OUI-IM
        if profile.vendor_mismatch:
            score += weights['oui_mismatch'] * 30
        
        # Channel outlier
        if profile.channel in DFS_CHANNELS:
            # DFS is legitimate but unusual for hidden
            score += weights['channel_outlier'] * 20
        
        same_oui_bssids = self.oui_index.get(oui, set())
        if len(same_oui_bssids) > 1:
            channels = [self.profiles[b].channel for b in same_oui_bssids if b in self.profiles]
            if channels and profile.channel not in channels[:-1]:  # Exclude self
                # Channel doesn't match others in group
                score += weights['channel_outlier'] * 40
        
        # RSSI outlier - very strong hidden network is suspicious
        if profile.rssi > -40:
            score += weights['rssi_outlier'] * 60
        elif profile.rssi > -50:
            score += weights['rssi_outlier'] * 30
        
        # BSSID anomaly - check for sequential BSSIDs
        if self._check_bssid_anomaly(profile.bssid):
            score += weights['bssid_anomaly'] * 50
        
        # Security - open or WEP is suspicious
        sec_lower = profile.security.lower()
        if 'open' in sec_lower or sec_lower == '':
            score += weights['security_weak'] * 70
        elif 'wep' in sec_lower:
            score += weights['security_weak'] * 50
        
        profile.rogue_likelihood_score = min(100.0, score)
    
    def _check_bssid_anomaly(self, bssid: str) -> bool:
        """Check for BSSID anomalies (like spoofed patterns)."""
        parts = bssid.upper().split(':')
        if len(parts) != 6:
            return True
        
        # Check for all same bytes (obvious fake)
        if len(set(parts)) == 1:
            return True
        
        # Check for sequential pattern
        try:
            last_bytes = [int(p, 16) for p in parts[-3:]]
            if last_bytes[0] == last_bytes[1] == last_bytes[2]:
                return True
        except ValueError:
            return True
        
        return False
    
    def _classify_network(self, profile: HiddenNetworkProfile):
        """Classify a hidden network based on computed scores."""
        oui = profile.oui
        reasons = []
        confidence = 50
        
        # Check for enterprise patterns FIRST (more specific)
        # Only classify as enterprise if NOT also in mesh list
        if oui in ENTERPRISE_VENDOR_OUIS and oui not in MESH_VENDOR_OUIS:
            profile.network_type = HiddenNetworkType.ENTERPRISE_AP
            reasons.append("Enterprise vendor OUI")
            confidence = 75
        
        # Check for mesh patterns (some overlap with enterprise)
        elif oui in MESH_VENDOR_OUIS:
            same_oui_count = len(self.oui_index.get(oui, set()))
            if same_oui_count >= 2:
                profile.network_type = HiddenNetworkType.MESH_NODE
                reasons.append(f"Mesh vendor OUI ({same_oui_count} nodes)")
                confidence = 80
            else:
                profile.network_type = HiddenNetworkType.EXTENDER_REPEATER
                reasons.append("Mesh vendor OUI (single node)")
                confidence = 60
        
        # Check for backhaul
        elif profile.channel in BACKHAUL_CHANNELS and profile.band == "5GHz":
            same_channel = len(self.channel_index.get(profile.channel, set()))
            if same_channel >= 2:
                profile.network_type = HiddenNetworkType.BACKHAUL_LINK
                reasons.append(f"5GHz backhaul channel ({same_channel} on ch{profile.channel})")
                confidence = 70
        
        # Check for IoT
        elif oui in IOT_VENDOR_OUIS:
            profile.network_type = HiddenNetworkType.IOT_DEVICE
            reasons.append("IoT vendor OUI")
            confidence = 70
        
        # Check rogue likelihood
        if profile.rogue_likelihood_score > 60:
            profile.network_type = HiddenNetworkType.ROGUE_CANDIDATE
            reasons.append(f"High rogue score ({profile.rogue_likelihood_score:.0f}%)")
            confidence = int(profile.rogue_likelihood_score)
            profile.is_rogue_candidate = True
        
        # Default
        if profile.network_type == HiddenNetworkType.UNKNOWN:
            # Try to infer from visible networks
            if self._correlate_with_visible(profile):
                reasons.append("Correlated with visible network")
                confidence = 60
            else:
                reasons.append("No matching patterns")
                confidence = 30
        
        profile.classification_confidence = confidence
        profile.classification_reason = "; ".join(reasons)
    
    def _correlate_with_visible(self, profile: HiddenNetworkProfile) -> bool:
        """Try to correlate hidden network with visible networks."""
        oui = profile.oui
        channel = profile.channel
        
        for visible in self.visible_networks.values():
            # Same OUI and same/adjacent channel = likely same deployment
            if visible.get('oui') == oui:
                v_channel = visible.get('channel', 0)
                if v_channel == channel or abs(v_channel - channel) <= 4:
                    profile.related_bssids.append(visible['bssid'])
                    profile.network_type = HiddenNetworkType.GUEST_ISOLATED
                    return True
        
        return False
    
    def _build_clusters(self):
        """Build clusters of related hidden networks."""
        self.clusters.clear()
        
        # Cluster by OUI
        cluster_id = 0
        assigned = set()
        
        for oui, bssids in self.oui_index.items():
            if len(bssids) >= 2:
                cluster_id += 1
                cid = f"hnce_cluster_{cluster_id}"
                
                cluster = HiddenCluster(
                    cluster_id=cid,
                    members=list(bssids)
                )
                
                # Compute cluster metrics
                rssi_values = []
                channels = set()
                vendors = set()
                
                for bssid in bssids:
                    if bssid in self.profiles:
                        profile = self.profiles[bssid]
                        profile.cluster_id = cid
                        rssi_values.append(profile.rssi)
                        channels.add(profile.channel)
                        if profile.vendor:
                            vendors.add(profile.vendor)
                        assigned.add(bssid)
                
                if rssi_values:
                    cluster.avg_rssi = sum(rssi_values) / len(rssi_values)
                    cluster.signal_similarity = 100 / (1 + self._variance(rssi_values) / 50)
                
                cluster.channel_spread = len(channels)
                cluster.vendor_count = len(vendors) if vendors else 1
                cluster.oui_consistency = 100.0  # All same OUI
                
                if cluster.channel_spread > 0:
                    cluster.channel_coherence = 100 / cluster.channel_spread
                
                self.clusters[cid] = cluster
        
        # Create single-device "clusters" for unclustered
        for bssid, profile in self.profiles.items():
            if bssid not in assigned:
                cluster_id += 1
                cid = f"hnce_single_{cluster_id}"
                
                cluster = HiddenCluster(
                    cluster_id=cid,
                    cluster_type=ClusterType.SINGLE_DEVICE,
                    members=[bssid],
                    avg_rssi=profile.rssi,
                    channel_spread=1,
                    vendor_count=1,
                    oui_consistency=50.0,
                    channel_coherence=50.0,
                    signal_similarity=50.0
                )
                
                profile.cluster_id = cid
                self.clusters[cid] = cluster
    
    def _classify_cluster(self, cluster: HiddenCluster):
        """Classify a cluster based on member profiles."""
        if len(cluster.members) < 2:
            cluster.cluster_type = ClusterType.SINGLE_DEVICE
            cluster.classification_label = "Single Hidden AP"
            cluster.confidence = 50
            return
        
        # Check member types
        member_types = []
        for bssid in cluster.members:
            if bssid in self.profiles:
                member_types.append(self.profiles[bssid].network_type)
        
        # Determine cluster type
        if all(t == HiddenNetworkType.MESH_NODE for t in member_types):
            cluster.cluster_type = ClusterType.MESH_CLUSTER
            cluster.classification_label = f"Mesh Network ({len(cluster.members)} nodes)"
            cluster.confidence = 85
        
        elif all(t == HiddenNetworkType.ENTERPRISE_AP for t in member_types):
            cluster.cluster_type = ClusterType.ENTERPRISE_CLUSTER
            cluster.classification_label = f"Enterprise Deployment ({len(cluster.members)} APs)"
            cluster.confidence = 80
        
        elif any(t == HiddenNetworkType.ROGUE_CANDIDATE for t in member_types):
            cluster.cluster_type = ClusterType.SUSPICIOUS_GROUP
            cluster.classification_label = f"Suspicious Group ({len(cluster.members)} devices)"
            cluster.rogue_risk = RogueRisk.HIGH
            cluster.confidence = 70
        
        elif cluster.vendor_count > 1:
            cluster.cluster_type = ClusterType.MIXED_VENDOR
            cluster.classification_label = f"Mixed Vendor ({cluster.vendor_count} vendors)"
            cluster.confidence = 50
        
        else:
            cluster.cluster_type = ClusterType.UNKNOWN
            cluster.classification_label = f"Unknown Cluster ({len(cluster.members)} devices)"
            cluster.confidence = 40
    
    def _detect_outliers(self):
        """Detect outlier hidden networks."""
        if len(self.profiles) < 3:
            return
        
        # Compute global stats
        all_rssi = [p.rssi for p in self.profiles.values()]
        rssi_mean = sum(all_rssi) / len(all_rssi)
        rssi_std = math.sqrt(self._variance(all_rssi))
        
        for profile in self.profiles.values():
            # RSSI outlier (more than 2 std from mean)
            if rssi_std > 0 and abs(profile.rssi - rssi_mean) > 2 * rssi_std:
                profile.is_outlier = True
            
            # Channel outlier (only one on its channel)
            if len(self.channel_index.get(profile.channel, set())) == 1:
                # Only outlier if there are many on other channels
                if sum(len(s) for s in self.channel_index.values()) > 5:
                    profile.is_outlier = True
    
    def _flag_rogue_candidates(self):
        """Flag potential rogue/spoof candidates."""
        for profile in self.profiles.values():
            # High rogue score
            if profile.rogue_likelihood_score > 60:
                profile.is_rogue_candidate = True
            
            # Very strong signal + unknown vendor
            if profile.rssi > -45 and profile.oui not in MESH_VENDOR_OUIS and profile.oui not in ENTERPRISE_VENDOR_OUIS:
                profile.is_rogue_candidate = True
            
            # Check for spoof patterns
            if self._check_spoof_pattern(profile):
                profile.is_spoof_candidate = True
    
    def _check_spoof_pattern(self, profile: HiddenNetworkProfile) -> bool:
        """Check if profile matches known spoof patterns."""
        # Hidden network mimicking visible network's characteristics
        for visible in self.visible_networks.values():
            # Same channel, similar RSSI, different OUI = potential evil twin
            if (visible.get('channel') == profile.channel and 
                abs(visible.get('rssi', -100) - profile.rssi) < 10 and
                visible.get('oui') != profile.oui):
                return True
        
        return False
    
    def _variance(self, values: List[float]) -> float:
        """Compute variance of values."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def get_profile(self, bssid: str) -> Optional[HiddenNetworkProfile]:
        """Get profile for a BSSID."""
        return self.profiles.get(bssid)
    
    def get_cluster(self, cluster_id: str) -> Optional[HiddenCluster]:
        """Get cluster by ID."""
        return self.clusters.get(cluster_id)
    
    def get_all_profiles(self) -> List[HiddenNetworkProfile]:
        """Get all hidden network profiles."""
        return list(self.profiles.values())
    
    def get_rogue_candidates(self) -> List[HiddenNetworkProfile]:
        """Get all rogue candidate profiles."""
        return [p for p in self.profiles.values() if p.is_rogue_candidate]
    
    def get_spoof_candidates(self) -> List[HiddenNetworkProfile]:
        """Get all spoof candidate profiles."""
        return [p for p in self.profiles.values() if p.is_spoof_candidate]
    
    def get_clusters_by_type(self, cluster_type: ClusterType) -> List[HiddenCluster]:
        """Get clusters of a specific type."""
        return [c for c in self.clusters.values() if c.cluster_type == cluster_type]
    
    def get_summary(self) -> dict:
        """Get analysis summary."""
        if not self.last_analysis:
            self.analyze()
        
        result = self.last_analysis
        return {
            'hidden_count': result.hidden_count,
            'cluster_count': result.cluster_count,
            'mesh_count': result.mesh_count,
            'enterprise_count': result.enterprise_count,
            'backhaul_count': result.backhaul_count,
            'rogue_candidates': len(result.rogue_candidates),
            'spoof_candidates': len(result.spoof_candidates),
            'suspicious_count': result.suspicious_count
        }
    
    def clear(self):
        """Clear all data."""
        self.profiles.clear()
        self.clusters.clear()
        self.oui_index.clear()
        self.channel_index.clear()
        self.vendor_index.clear()
        self.visible_networks.clear()
        self.last_analysis = None


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_hnce: Optional[HiddenNetworkClassifier] = None

def get_hidden_classifier() -> HiddenNetworkClassifier:
    """Get global HNCE instance."""
    global _hnce
    if _hnce is None:
        _hnce = HiddenNetworkClassifier()
    return _hnce
