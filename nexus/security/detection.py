"""
Threat detection engine for WiFi security analysis.

Analyzes networks against security rules and generates threats.
"""

from typing import List, Dict, Optional, Set, TYPE_CHECKING
from datetime import datetime
import uuid

from nexus.core.models import Network, Threat, ScanResult, ThreatSeverity, ThreatCategory

# Lazy import to avoid circular dependency
_rules_module = None

def _get_default_rules():
    """Lazy import of rules to avoid circular dependency."""
    global _rules_module
    if _rules_module is None:
        from nexus.security import rules as _rules_module
    return _rules_module.get_default_rules()


class ThreatDetector:
    """
    WiFi threat detection engine.
    
    Analyzes scan results against security rules to detect:
    - Weak encryption
    - SSID spoofing (evil twin)
    - Rogue access points
    - Channel anomalies
    """
    
    def __init__(self, rules: Optional[List] = None):
        """
        Initialize threat detector.
        
        Args:
            rules: List of detection rules (uses defaults if None)
        """
        self.rules = rules if rules is not None else _get_default_rules()
        self.baseline_networks: Dict[str, Network] = {}
        self._known_threats: Dict[str, Threat] = {}
        self._network_history: Dict[str, List[Network]] = {}
    
    def set_baseline(self, networks: List[Network]) -> None:
        """
        Set baseline networks (known good networks).
        
        Args:
            networks: List of known legitimate networks
        """
        self.baseline_networks = {n.bssid: n for n in networks}
    
    def add_baseline_network(self, network: Network) -> None:
        """Add a network to the baseline."""
        self.baseline_networks[network.bssid] = network
    
    def analyze(self, scan_result: ScanResult) -> List[Threat]:
        """
        Analyze scan result for threats.
        
        Args:
            scan_result: ScanResult to analyze
            
        Returns:
            List of detected threats
        """
        threats = []
        
        # Update network history
        for network in scan_result.networks:
            if network.bssid not in self._network_history:
                self._network_history[network.bssid] = []
            self._network_history[network.bssid].append(network)
        
        # Run each rule
        for rule in self.rules:
            if rule.enabled:
                rule_threats = rule.evaluate(
                    scan_result.networks,
                    self.baseline_networks,
                    self._network_history
                )
                threats.extend(rule_threats)
        
        # Update known threats
        for threat in threats:
            self._known_threats[threat.id] = threat
        
        return threats
    
    def get_threat_summary(self) -> Dict[str, int]:
        """
        Get summary of threats by severity.
        
        Returns:
            Dictionary mapping severity to count
        """
        summary = {s.value: 0 for s in ThreatSeverity}
        
        for threat in self._known_threats.values():
            if not threat.resolved:
                summary[threat.severity.value] += 1
        
        return summary
    
    def get_active_threats(self) -> List[Threat]:
        """Get list of unresolved threats."""
        return [t for t in self._known_threats.values() if not t.resolved]
    
    def resolve_threat(self, threat_id: str) -> bool:
        """
        Mark a threat as resolved.
        
        Args:
            threat_id: ID of the threat to resolve
            
        Returns:
            True if threat was found and resolved
        """
        if threat_id in self._known_threats:
            self._known_threats[threat_id].resolved = True
            return True
        return False
    
    def clear_history(self) -> None:
        """Clear network history and known threats."""
        self._network_history.clear()
        self._known_threats.clear()
