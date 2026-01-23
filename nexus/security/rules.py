"""
Detection rules for WiFi security analysis.

Defines individual detection rules that can be evaluated against networks.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
import uuid

from nexus.core.models import Network, Threat, ThreatSeverity, ThreatCategory, SecurityType


def create_threat(
    severity: ThreatSeverity,
    category: ThreatCategory,
    description: str,
    networks: List[Network]
) -> Threat:
    """
    Helper function to create a Threat object.
    
    Args:
        severity: Threat severity
        category: Threat category
        description: Human-readable description
        networks: Involved networks
        
    Returns:
        New Threat object
    """
    return Threat(
        id=str(uuid.uuid4())[:8],
        severity=severity,
        category=category,
        description=description,
        networks=networks,
        detected_at=datetime.now()
    )


class Rule(ABC):
    """Abstract base class for detection rules."""
    
    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize rule.
        
        Args:
            name: Rule name/identifier
            enabled: Whether the rule is active
        """
        self.name = name
        self.enabled = enabled
    
    @abstractmethod
    def evaluate(
        self,
        networks: List[Network],
        baseline: Dict[str, Network],
        history: Dict[str, List[Network]]
    ) -> List[Threat]:
        """
        Evaluate the rule against networks.
        
        Args:
            networks: Current scan results
            baseline: Known legitimate networks
            history: Historical network data
            
        Returns:
            List of detected threats
        """
        pass


class WeakEncryptionRule(Rule):
    """
    Detects networks with weak or no encryption.
    
    Triggers on: Open networks, WEP, WPA (not WPA2/3)
    """
    
    def __init__(self):
        super().__init__("weak_encryption")
    
    def evaluate(
        self,
        networks: List[Network],
        baseline: Dict[str, Network],
        history: Dict[str, List[Network]]
    ) -> List[Threat]:
        threats = []
        
        weak_types = {SecurityType.OPEN, SecurityType.WEP, SecurityType.WPA}
        
        for network in networks:
            if network.security in weak_types:
                severity = ThreatSeverity.HIGH
                
                if network.security == SecurityType.OPEN:
                    desc = f"Open network '{network.ssid}' has no encryption"
                elif network.security == SecurityType.WEP:
                    desc = f"Network '{network.ssid}' uses deprecated WEP encryption"
                else:
                    desc = f"Network '{network.ssid}' uses outdated WPA (not WPA2/3)"
                
                threats.append(create_threat(
                    severity=severity,
                    category=ThreatCategory.WEAK_ENCRYPTION,
                    description=desc,
                    networks=[network]
                ))
        
        return threats


class SSIDSpoofingRule(Rule):
    """
    Detects potential SSID spoofing (evil twin attacks).
    
    Triggers on: Same SSID with different BSSIDs (excluding mesh networks)
    """
    
    def __init__(self, min_networks: int = 2):
        super().__init__("ssid_spoofing")
        self.min_networks = min_networks
    
    def evaluate(
        self,
        networks: List[Network],
        baseline: Dict[str, Network],
        history: Dict[str, List[Network]]
    ) -> List[Threat]:
        threats = []
        
        # Group networks by SSID
        ssid_groups: Dict[str, List[Network]] = defaultdict(list)
        for network in networks:
            if network.ssid:  # Skip hidden networks
                ssid_groups[network.ssid].append(network)
        
        # Check for multiple BSSIDs per SSID
        for ssid, group in ssid_groups.items():
            if len(group) >= self.min_networks:
                # Check if vendors are different (stronger indicator)
                vendors = set(n.vendor for n in group if n.vendor != "Unknown")
                
                if len(vendors) > 1:
                    # Different vendors - highly suspicious
                    threats.append(create_threat(
                        severity=ThreatSeverity.CRITICAL,
                        category=ThreatCategory.SSID_SPOOFING,
                        description=f"SSID '{ssid}' broadcast by {len(group)} APs with different vendors - possible evil twin",
                        networks=group
                    ))
                else:
                    # Same vendor - could be mesh, but still worth noting
                    if len(group) >= 3:  # Only alert for 3+ APs
                        threats.append(create_threat(
                            severity=ThreatSeverity.LOW,
                            category=ThreatCategory.SSID_SPOOFING,
                            description=f"SSID '{ssid}' broadcast by {len(group)} APs - may be mesh network or spoofing",
                            networks=group
                        ))
        
        return threats


class RogueAPRule(Rule):
    """
    Detects rogue access points.
    
    Triggers on: New APs broadcasting known SSIDs not in baseline
    """
    
    def __init__(self):
        super().__init__("rogue_ap")
    
    def evaluate(
        self,
        networks: List[Network],
        baseline: Dict[str, Network],
        history: Dict[str, List[Network]]
    ) -> List[Threat]:
        threats = []
        
        if not baseline:
            return threats  # No baseline set
        
        # Get known SSIDs from baseline
        baseline_ssids = {n.ssid for n in baseline.values() if n.ssid}
        baseline_bssids = set(baseline.keys())
        
        for network in networks:
            if network.ssid in baseline_ssids and network.bssid not in baseline_bssids:
                # SSID matches but BSSID is unknown - potential rogue
                threats.append(create_threat(
                    severity=ThreatSeverity.CRITICAL,
                    category=ThreatCategory.ROGUE_AP,
                    description=f"Unknown AP '{network.bssid}' broadcasting trusted SSID '{network.ssid}'",
                    networks=[network]
                ))
        
        return threats


class ChannelAnomalyRule(Rule):
    """
    Detects channel-related anomalies.
    
    Triggers on:
    - Networks hopping channels frequently
    - Unusual channel usage
    """
    
    # Standard 2.4 GHz non-overlapping channels
    PREFERRED_24GHZ = {1, 6, 11}
    
    def __init__(self, hop_threshold: int = 3):
        super().__init__("channel_anomaly")
        self.hop_threshold = hop_threshold
    
    def evaluate(
        self,
        networks: List[Network],
        baseline: Dict[str, Network],
        history: Dict[str, List[Network]]
    ) -> List[Threat]:
        threats = []
        
        for network in networks:
            # Check for channel hopping
            if network.bssid in history:
                net_history = history[network.bssid]
                if len(net_history) >= self.hop_threshold:
                    recent = net_history[-self.hop_threshold:]
                    channels = set(n.channel for n in recent)
                    
                    if len(channels) >= self.hop_threshold:
                        threats.append(create_threat(
                            severity=ThreatSeverity.MEDIUM,
                            category=ThreatCategory.CHANNEL_ANOMALY,
                            description=f"Network '{network.ssid}' hopping channels: {sorted(channels)}",
                            networks=[network]
                        ))
            
            # Check for unusual 2.4 GHz channel (not 1, 6, or 11)
            if network.band == "2.4GHz":
                if network.channel not in self.PREFERRED_24GHZ and network.channel > 0:
                    threats.append(create_threat(
                        severity=ThreatSeverity.LOW,
                        category=ThreatCategory.CHANNEL_ANOMALY,
                        description=f"Network '{network.ssid}' on non-standard channel {network.channel}",
                        networks=[network]
                    ))
        
        return threats


class HiddenNetworkRule(Rule):
    """
    Detects hidden (cloaked) networks.
    
    Hidden networks are not inherently malicious but worth noting.
    """
    
    def __init__(self):
        super().__init__("hidden_network")
    
    def evaluate(
        self,
        networks: List[Network],
        baseline: Dict[str, Network],
        history: Dict[str, List[Network]]
    ) -> List[Threat]:
        threats = []
        
        for network in networks:
            if network.is_hidden:
                # Check if this hidden network is in baseline
                if network.bssid in baseline:
                    continue  # Known hidden network
                
                threats.append(create_threat(
                    severity=ThreatSeverity.LOW,
                    category=ThreatCategory.HIDDEN_NETWORK,
                    description=f"Hidden network detected: {network.bssid} ({network.vendor})",
                    networks=[network]
                ))
        
        return threats


def get_default_rules() -> List[Rule]:
    """
    Get the default set of detection rules.
    
    Returns:
        List of enabled Rule instances
    """
    return [
        WeakEncryptionRule(),
        SSIDSpoofingRule(),
        RogueAPRule(),
        ChannelAnomalyRule(),
        HiddenNetworkRule(),
    ]
