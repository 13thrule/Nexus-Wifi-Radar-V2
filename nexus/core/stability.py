"""
Signal Stability and Wall Estimation for NEXUS WiFi Radar.

100% PASSIVE - All calculations based on received beacon data only.

Features:
- Signal jitter/volatility tracking
- Stability scoring
- Wall estimation based on signal characteristics
- Spoof detection via signal anomalies
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque
from enum import Enum


class StabilityRating(Enum):
    """Signal stability classification."""
    ROCK_SOLID = "rock_solid"
    STABLE = "stable"
    MODERATE = "moderate"
    UNSTABLE = "unstable"
    ERRATIC = "erratic"


class WallEstimate(Enum):
    """Wall/obstacle estimation."""
    LINE_OF_SIGHT = "line_of_sight"
    ONE_WALL = "one_wall"
    TWO_WALLS = "two_walls"
    MULTIPLE_WALLS = "multiple_walls"
    FAR_SIDE = "far_side"
    OUTDOOR = "outdoor"


@dataclass
class StabilityMetrics:
    """Signal stability metrics for a network."""
    bssid: str
    
    # Current values
    current_signal: int = 0
    current_jitter: float = 0.0  # Standard deviation of recent signals
    
    # Statistics
    avg_signal: float = 0.0
    min_signal: int = 100
    max_signal: int = 0
    signal_range: int = 0
    
    # Stability rating
    stability_rating: StabilityRating = StabilityRating.MODERATE
    stability_score: int = 50  # 0-100
    
    # Volatility
    volatility_percent: float = 0.0
    trend: str = "stable"  # "improving", "declining", "stable", "fluctuating"
    
    # Time tracking
    first_seen: float = 0.0
    last_seen: float = 0.0
    observation_count: int = 0
    
    # Anomaly detection
    is_anomalous: bool = False
    anomaly_reason: str = ""


@dataclass  
class WallEstimateResult:
    """Wall estimation result."""
    estimate: WallEstimate
    wall_count: int
    description: str
    confidence: int  # 0-100
    factors: List[str] = field(default_factory=list)


# Signal characteristics for wall estimation
# Based on typical signal loss per obstacle
WALL_LOSS_DB = {
    "drywall": 3,      # Interior wall
    "wood": 4,         # Wood door/wall
    "glass": 2,        # Window
    "concrete": 12,    # Concrete wall
    "brick": 8,        # Brick wall
    "metal": 15,       # Metal obstruction
    "floor": 10,       # Floor/ceiling
}

# Expected free-space signal at various distances (rough estimates)
# Based on typical router TX power of 20dBm and antenna gain
EXPECTED_SIGNAL_BY_DISTANCE = {
    5: -35,    # 5m, line of sight
    10: -45,   # 10m
    15: -52,   # 15m
    20: -58,   # 20m
    30: -65,   # 30m
    50: -72,   # 50m
}


class SignalStabilityTracker:
    """
    Tracks signal stability over time for all networks.
    
    100% PASSIVE - only analyzes received signal data.
    """
    
    # Configuration
    HISTORY_SIZE = 60  # Keep last 60 samples per network
    MIN_SAMPLES_FOR_RATING = 5
    
    # Jitter thresholds (standard deviation of signal)
    JITTER_ROCK_SOLID = 1.0
    JITTER_STABLE = 3.0
    JITTER_MODERATE = 6.0
    JITTER_UNSTABLE = 10.0
    # Above UNSTABLE = ERRATIC
    
    def __init__(self):
        # Signal history: bssid -> deque of (timestamp, signal)
        self.signal_history: Dict[str, deque] = {}
        
        # Stability metrics per network
        self.metrics: Dict[str, StabilityMetrics] = {}
        
        # SSID tracking for spoof detection
        self.ssid_to_bssids: Dict[str, set] = {}
    
    def record_signal(self, bssid: str, ssid: str, signal: int, 
                      channel: int = 0, noise: int = -95) -> StabilityMetrics:
        """
        Record a signal observation.
        
        Returns updated stability metrics.
        """
        now = time.time()
        
        # Initialize history if needed
        if bssid not in self.signal_history:
            self.signal_history[bssid] = deque(maxlen=self.HISTORY_SIZE)
            self.metrics[bssid] = StabilityMetrics(bssid=bssid, first_seen=now)
        
        # Track SSID -> BSSID mapping for spoof detection
        if ssid:
            if ssid not in self.ssid_to_bssids:
                self.ssid_to_bssids[ssid] = set()
            self.ssid_to_bssids[ssid].add(bssid)
        
        # Add to history
        self.signal_history[bssid].append((now, signal))
        
        # Update metrics
        metrics = self.metrics[bssid]
        metrics.current_signal = signal
        metrics.last_seen = now
        metrics.observation_count += 1
        
        # Calculate statistics
        self._update_statistics(bssid)
        
        # Calculate stability rating
        self._calculate_stability(bssid)
        
        # Check for anomalies
        self._check_anomalies(bssid, ssid)
        
        return metrics
    
    def _update_statistics(self, bssid: str):
        """Update signal statistics."""
        history = self.signal_history[bssid]
        metrics = self.metrics[bssid]
        
        if len(history) < 2:
            return
        
        signals = [s for _, s in history]
        
        # Basic stats
        metrics.avg_signal = sum(signals) / len(signals)
        metrics.min_signal = min(signals)
        metrics.max_signal = max(signals)
        metrics.signal_range = metrics.max_signal - metrics.min_signal
        
        # Calculate jitter (standard deviation)
        variance = sum((s - metrics.avg_signal) ** 2 for s in signals) / len(signals)
        metrics.current_jitter = math.sqrt(variance)
        
        # Volatility as percentage of average
        if metrics.avg_signal > 0:
            metrics.volatility_percent = (metrics.current_jitter / metrics.avg_signal) * 100
        
        # Trend analysis (last 10 samples)
        recent = signals[-10:] if len(signals) >= 10 else signals
        if len(recent) >= 3:
            first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
            second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
            
            diff = second_half - first_half
            if diff > 3:
                metrics.trend = "improving"
            elif diff < -3:
                metrics.trend = "declining"
            elif metrics.current_jitter > self.JITTER_UNSTABLE:
                metrics.trend = "fluctuating"
            else:
                metrics.trend = "stable"
    
    def _calculate_stability(self, bssid: str):
        """Calculate stability rating and score."""
        metrics = self.metrics[bssid]
        
        if metrics.observation_count < self.MIN_SAMPLES_FOR_RATING:
            metrics.stability_rating = StabilityRating.MODERATE
            metrics.stability_score = 50
            return
        
        jitter = metrics.current_jitter
        
        # Determine rating based on jitter
        if jitter <= self.JITTER_ROCK_SOLID:
            metrics.stability_rating = StabilityRating.ROCK_SOLID
            metrics.stability_score = 95
        elif jitter <= self.JITTER_STABLE:
            metrics.stability_rating = StabilityRating.STABLE
            metrics.stability_score = 80
        elif jitter <= self.JITTER_MODERATE:
            metrics.stability_rating = StabilityRating.MODERATE
            metrics.stability_score = 60
        elif jitter <= self.JITTER_UNSTABLE:
            metrics.stability_rating = StabilityRating.UNSTABLE
            metrics.stability_score = 35
        else:
            metrics.stability_rating = StabilityRating.ERRATIC
            metrics.stability_score = 15
        
        # Adjust score based on signal range
        if metrics.signal_range > 20:
            metrics.stability_score = max(10, metrics.stability_score - 15)
        elif metrics.signal_range > 10:
            metrics.stability_score = max(10, metrics.stability_score - 5)
    
    def _check_anomalies(self, bssid: str, ssid: str):
        """Check for signal anomalies that might indicate spoofing."""
        metrics = self.metrics[bssid]
        metrics.is_anomalous = False
        metrics.anomaly_reason = ""
        
        # Check for sudden large signal changes
        history = self.signal_history[bssid]
        if len(history) >= 2:
            recent_signals = [s for _, s in list(history)[-5:]]
            if len(recent_signals) >= 2:
                last_diff = abs(recent_signals[-1] - recent_signals[-2])
                if last_diff > 25:
                    metrics.is_anomalous = True
                    metrics.anomaly_reason = f"Sudden signal jump: {last_diff}dB"
        
        # Check for multiple BSSIDs with same SSID (potential rogue AP)
        if ssid and ssid in self.ssid_to_bssids:
            bssid_count = len(self.ssid_to_bssids[ssid])
            if bssid_count > 3:  # More than 3 APs with same SSID is suspicious
                metrics.is_anomalous = True
                metrics.anomaly_reason = f"Multiple APs ({bssid_count}) with same SSID"
    
    def get_metrics(self, bssid: str) -> Optional[StabilityMetrics]:
        """Get stability metrics for a network."""
        return self.metrics.get(bssid)
    
    def get_stability_bar(self, bssid: str, width: int = 10) -> str:
        """Get ASCII stability bar for display."""
        metrics = self.metrics.get(bssid)
        if not metrics:
            return "?" * width
        
        score = metrics.stability_score
        filled = int((score / 100) * width)
        
        # Color coding via characters
        if score >= 80:
            char = "█"
        elif score >= 60:
            char = "▓"
        elif score >= 40:
            char = "▒"
        else:
            char = "░"
        
        return char * filled + "·" * (width - filled)
    
    def get_potential_rogues(self) -> Dict[str, List[str]]:
        """
        Get SSIDs that might have rogue APs.
        
        Returns dict of SSID -> list of BSSIDs
        """
        rogues = {}
        for ssid, bssids in self.ssid_to_bssids.items():
            if len(bssids) > 2:  # Multiple APs with same SSID
                rogues[ssid] = list(bssids)
        return rogues


class WallEstimator:
    """
    Estimates walls/obstacles between user and AP.
    
    100% PASSIVE - uses signal characteristics only.
    """
    
    # Typical TX power for different device types (dBm)
    TX_POWER_ESTIMATES = {
        "router": 20,
        "enterprise": 23,
        "mobile_hotspot": 15,
        "iot": 12,
        "default": 18,
    }
    
    # Path loss exponents
    PATH_LOSS = {
        "free_space": 2.0,
        "indoor_los": 2.2,
        "indoor_obstructed": 3.5,
        "indoor_heavy": 4.5,
    }
    
    def estimate_walls(self, signal_dbm: int, frequency_mhz: int = 2437,
                       estimated_distance: float = None,
                       device_type: str = "default") -> WallEstimateResult:
        """
        Estimate number of walls between user and AP.
        
        Args:
            signal_dbm: Signal strength in dBm (negative number)
            frequency_mhz: Channel frequency
            estimated_distance: Optional distance estimate in meters
            device_type: Type of device for TX power estimation
            
        Returns:
            WallEstimateResult with estimation details
        """
        factors = []
        
        # Get estimated TX power
        tx_power = self.TX_POWER_ESTIMATES.get(device_type, 18)
        factors.append(f"Assumed TX power: {tx_power}dBm")
        
        # Calculate free-space path loss
        # FSPL = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
        # Simplified: FSPL ≈ 20*log10(d) + 20*log10(f) - 27.55 (d in m, f in MHz)
        
        if estimated_distance and estimated_distance > 0:
            # Calculate expected free-space signal
            fspl = 20 * math.log10(estimated_distance) + 20 * math.log10(frequency_mhz) - 27.55
            expected_signal = tx_power - fspl
            factors.append(f"Expected free-space signal at {estimated_distance:.0f}m: {expected_signal:.0f}dBm")
            
            # Signal deficit = expected - actual (positive means walls)
            signal_deficit = expected_signal - signal_dbm
            factors.append(f"Signal deficit: {signal_deficit:.0f}dB")
        else:
            # Estimate based on signal strength alone
            # Assume typical indoor environment
            signal_deficit = self._estimate_deficit_from_signal(signal_dbm, tx_power)
            factors.append(f"Estimated signal deficit: {signal_deficit:.0f}dB")
        
        # Estimate walls based on deficit
        # Typical drywall: 3-5dB per wall
        # Typical concrete: 10-15dB per wall
        # Use average of 5dB per wall for estimation
        
        if signal_deficit < 3:
            estimate = WallEstimate.LINE_OF_SIGHT
            wall_count = 0
            description = "Clear line of sight"
            confidence = 70
        elif signal_deficit < 8:
            estimate = WallEstimate.ONE_WALL
            wall_count = 1
            description = "One wall or light obstruction"
            confidence = 60
        elif signal_deficit < 15:
            estimate = WallEstimate.TWO_WALLS
            wall_count = 2
            description = "One to two rooms away"
            confidence = 55
        elif signal_deficit < 25:
            estimate = WallEstimate.MULTIPLE_WALLS
            wall_count = 3
            description = "Several walls or one floor"
            confidence = 50
        else:
            estimate = WallEstimate.FAR_SIDE
            wall_count = 4
            description = "Far side of building or multiple floors"
            confidence = 40
        
        # Adjust for 5GHz (more attenuation through walls)
        if frequency_mhz > 5000:
            factors.append("5GHz: Higher wall attenuation")
            if wall_count > 0:
                wall_count = max(1, wall_count - 1)
                description += " (5GHz adjusted)"
        
        return WallEstimateResult(
            estimate=estimate,
            wall_count=wall_count,
            description=description,
            confidence=confidence,
            factors=factors
        )
    
    def _estimate_deficit_from_signal(self, signal_dbm: int, tx_power: int) -> float:
        """Estimate signal deficit when distance is unknown."""
        # Assume signal of -40dBm is line of sight at close range
        # This is a rough heuristic
        
        if signal_dbm >= -40:
            return 0
        elif signal_dbm >= -50:
            return 5
        elif signal_dbm >= -60:
            return 10
        elif signal_dbm >= -70:
            return 18
        elif signal_dbm >= -80:
            return 28
        else:
            return 40
    
    def get_wall_icon(self, estimate: WallEstimate) -> str:
        """Get icon for wall estimate."""
        icons = {
            WallEstimate.LINE_OF_SIGHT: "👁️",
            WallEstimate.ONE_WALL: "🧱",
            WallEstimate.TWO_WALLS: "🧱🧱",
            WallEstimate.MULTIPLE_WALLS: "🏠",
            WallEstimate.FAR_SIDE: "🏢",
            WallEstimate.OUTDOOR: "🌳",
        }
        return icons.get(estimate, "❓")


# Global instances
_stability_tracker: Optional[SignalStabilityTracker] = None
_wall_estimator: Optional[WallEstimator] = None


def get_stability_tracker() -> SignalStabilityTracker:
    """Get the global stability tracker instance."""
    global _stability_tracker
    if _stability_tracker is None:
        _stability_tracker = SignalStabilityTracker()
    return _stability_tracker


def get_wall_estimator() -> WallEstimator:
    """Get the global wall estimator instance."""
    global _wall_estimator
    if _wall_estimator is None:
        _wall_estimator = WallEstimator()
    return _wall_estimator
