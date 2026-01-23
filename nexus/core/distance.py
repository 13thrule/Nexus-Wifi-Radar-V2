"""
Advanced Distance Estimation Module - 100% PASSIVE.

Uses multiple passive RF metrics to estimate distance:
- RSSI (baseline signal strength)
- Noise floor and SNR
- Channel frequency (2.4GHz vs 5GHz vs 6GHz)
- Signal stability over time
- Vendor transmit power estimates
- Multi-scan averaging

All estimates include confidence ranges and environment interpretations.
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta


# Known vendor transmit powers (dBm) - conservative estimates
VENDOR_TX_POWER = {
    # UK ISP routers (typically lower power, ~17-20 dBm)
    "bt": 18,
    "ee": 18,
    "virgin": 19,
    "sky": 18,
    "talktalk": 17,
    "plusnet": 18,
    "vodafone": 18,
    
    # Consumer routers (typically 20-23 dBm)
    "netgear": 20,
    "tp-link": 20,
    "asus": 21,
    "linksys": 20,
    "d-link": 19,
    "belkin": 19,
    "tenda": 19,
    
    # Enterprise/Pro (higher power, 23-27 dBm)
    "cisco": 23,
    "ubiquiti": 24,
    "aruba": 23,
    "ruckus": 24,
    "meraki": 23,
    
    # Mobile hotspots (lower power, ~10-15 dBm)
    "iphone": 12,
    "android": 12,
    "samsung": 13,
    "huawei": 13,
    
    # Default
    "unknown": 20
}

# Path loss exponents by frequency band
PATH_LOSS_EXPONENTS = {
    "2.4ghz": 2.8,   # Travels further, penetrates walls better
    "5ghz": 3.2,     # Shorter range, more attenuation
    "6ghz": 3.5,     # Shortest range, highest attenuation
}

# Reference distance for path loss model (1 meter)
REFERENCE_DISTANCE = 1.0

# Reference RSSI at 1 meter by frequency
REFERENCE_RSSI = {
    "2.4ghz": -30,  # dBm at 1 meter
    "5ghz": -35,
    "6ghz": -38,
}


@dataclass
class SignalSample:
    """Single signal measurement."""
    timestamp: datetime
    rssi_dbm: int
    signal_percent: int
    noise_dbm: Optional[int] = None
    
    @property
    def snr(self) -> Optional[int]:
        """Signal-to-Noise Ratio in dB."""
        if self.noise_dbm is not None:
            return self.rssi_dbm - self.noise_dbm
        return None


@dataclass
class DistanceEstimate:
    """Complete distance estimation with confidence and context."""
    
    # Core estimate
    distance_meters: float
    confidence_percent: int  # 0-100, how confident we are
    margin_percent: int      # ±X% uncertainty
    
    # Signal metrics
    rssi_dbm: int
    signal_percent: int
    snr_db: Optional[int]
    noise_level: str         # "Low", "Medium", "High"
    
    # RF characteristics
    frequency_band: str      # "2.4GHz", "5GHz", "6GHz"
    channel: int
    
    # Stability
    stability: str           # "Very Stable", "Stable", "Fluctuating", "Unstable"
    stability_score: float   # 0-1
    
    # Vendor info
    vendor: str
    estimated_tx_power: int
    
    # Environment interpretation
    environment_guess: str   # "Same room", "One wall away", etc.
    environment_detail: str  # Longer explanation
    
    # Quality indicators
    signal_quality: str      # "Excellent", "Good", "Fair", "Weak", "Critical"
    snr_quality: str         # "Excellent", "Good", "Fair", "Poor"
    
    def to_tooltip(self) -> str:
        """Generate tooltip text for UI display."""
        lines = [
            f"📏 Distance: ~{self.distance_meters:.0f}m (±{self.margin_percent}%)",
            f"📶 Signal: {self.signal_percent}% ({self.signal_quality})",
        ]
        
        if self.snr_db is not None:
            lines.append(f"📊 SNR: {self.snr_db} dB ({self.snr_quality})")
        
        lines.extend([
            f"📻 Noise: {self.noise_level}",
            f"📡 Frequency: {self.frequency_band}",
            f"⚡ Stability: {self.stability}",
            f"🏠 Environment: {self.environment_guess}",
        ])
        
        return "\n".join(lines)
    
    def to_short_label(self) -> str:
        """Short label for radar display."""
        return f"~{self.distance_meters:.0f}m"


class DistanceEstimator:
    """
    Advanced passive distance estimation using multiple RF metrics.
    
    100% PASSIVE - only uses data from received beacon frames.
    """
    
    def __init__(self, history_seconds: int = 60, min_samples: int = 3):
        """
        Initialize estimator.
        
        Args:
            history_seconds: How long to keep signal history
            min_samples: Minimum samples needed for stability calculation
        """
        self.history_seconds = history_seconds
        self.min_samples = min_samples
        
        # Signal history: BSSID -> list of SignalSamples
        self.history: Dict[str, List[SignalSample]] = defaultdict(list)
        
        # Noise floor estimate (updated over time)
        self.noise_floor_estimate = -95  # Default noise floor in dBm
    
    def record_sample(self, bssid: str, rssi_dbm: int, signal_percent: int,
                      noise_dbm: Optional[int] = None):
        """Record a new signal sample."""
        sample = SignalSample(
            timestamp=datetime.now(),
            rssi_dbm=rssi_dbm,
            signal_percent=signal_percent,
            noise_dbm=noise_dbm
        )
        
        self.history[bssid].append(sample)
        self._trim_history(bssid)
        
        # Update noise floor estimate
        if noise_dbm is not None:
            # Exponential moving average
            self.noise_floor_estimate = 0.9 * self.noise_floor_estimate + 0.1 * noise_dbm
    
    def _trim_history(self, bssid: str):
        """Remove old samples beyond history window."""
        cutoff = datetime.now() - timedelta(seconds=self.history_seconds)
        self.history[bssid] = [s for s in self.history[bssid] if s.timestamp > cutoff]
    
    def estimate(self, bssid: str, ssid: str, signal_percent: int, 
                 channel: int, vendor: str = "unknown",
                 rssi_dbm: Optional[int] = None) -> DistanceEstimate:
        """
        Estimate distance using all available passive metrics.
        
        Args:
            bssid: Network BSSID
            ssid: Network SSID
            signal_percent: Current signal strength (0-100)
            channel: WiFi channel number
            vendor: Vendor name (for TX power estimation)
            rssi_dbm: RSSI in dBm (estimated from percent if not provided)
        
        Returns:
            Complete DistanceEstimate with all metrics
        """
        # Convert signal percent to dBm if not provided
        if rssi_dbm is None:
            rssi_dbm = self._percent_to_dbm(signal_percent)
        
        # Record this sample
        self.record_sample(bssid, rssi_dbm, signal_percent)
        
        # Determine frequency band from channel
        freq_band = self._get_frequency_band(channel)
        
        # Get vendor TX power estimate
        tx_power = self._get_tx_power(ssid, vendor)
        
        # Calculate averaged RSSI from history
        avg_rssi = self._get_averaged_rssi(bssid)
        
        # Calculate stability
        stability_score, stability_label = self._calculate_stability(bssid)
        
        # Estimate noise and SNR
        noise_dbm = self._estimate_noise(bssid)
        snr = avg_rssi - noise_dbm if noise_dbm else None
        
        # Calculate base distance using log-distance path loss model
        base_distance = self._calculate_distance(avg_rssi, tx_power, freq_band)
        
        # Adjust distance based on SNR (poor SNR = signal traveling further)
        if snr is not None:
            snr_adjustment = self._snr_distance_adjustment(snr)
            base_distance *= snr_adjustment
        
        # Calculate confidence and margin based on stability
        confidence, margin = self._calculate_confidence(stability_score, snr, freq_band)
        
        # Determine environment guess
        env_guess, env_detail = self._guess_environment(base_distance, snr, stability_score, freq_band)
        
        # Quality labels
        signal_quality = self._signal_quality_label(signal_percent)
        snr_quality = self._snr_quality_label(snr)
        noise_level = self._noise_level_label(noise_dbm)
        
        return DistanceEstimate(
            distance_meters=round(base_distance, 1),
            confidence_percent=confidence,
            margin_percent=margin,
            rssi_dbm=avg_rssi,
            signal_percent=signal_percent,
            snr_db=snr,
            noise_level=noise_level,
            frequency_band=freq_band,
            channel=channel,
            stability=stability_label,
            stability_score=stability_score,
            vendor=vendor,
            estimated_tx_power=tx_power,
            environment_guess=env_guess,
            environment_detail=env_detail,
            signal_quality=signal_quality,
            snr_quality=snr_quality
        )
    
    def _percent_to_dbm(self, percent: int) -> int:
        """Convert signal percentage to approximate dBm."""
        # Common mapping: 100% ≈ -30 dBm, 0% ≈ -100 dBm
        return int(-100 + (percent * 0.7))
    
    def _get_frequency_band(self, channel: int) -> str:
        """Determine frequency band from channel number."""
        if channel <= 14:
            return "2.4GHz"
        elif channel <= 177:
            return "5GHz"
        else:
            return "6GHz"
    
    def _get_tx_power(self, ssid: str, vendor: str) -> int:
        """Estimate transmit power based on SSID and vendor."""
        ssid_lower = ssid.lower() if ssid else ""
        vendor_lower = vendor.lower() if vendor else ""
        
        # Check SSID for ISP indicators
        for isp in ["bt-", "ee ", "virgin", "sky", "talktalk", "plusnet", "vodafone"]:
            if isp in ssid_lower:
                return VENDOR_TX_POWER.get(isp.replace("-", "").replace(" ", "").strip(), 18)
        
        # Check for mobile hotspots
        for mobile in ["iphone", "android", "galaxy", "huawei", "pixel"]:
            if mobile in ssid_lower:
                return VENDOR_TX_POWER.get(mobile.split()[0], 12)
        
        # Check vendor
        for v_key in VENDOR_TX_POWER:
            if v_key in vendor_lower:
                return VENDOR_TX_POWER[v_key]
        
        return VENDOR_TX_POWER["unknown"]
    
    def _get_averaged_rssi(self, bssid: str) -> int:
        """Get averaged RSSI from recent samples."""
        samples = self.history.get(bssid, [])
        if not samples:
            return -70  # Default
        
        # Weight recent samples more heavily
        total_weight = 0
        weighted_sum = 0
        
        for i, sample in enumerate(reversed(samples[-10:])):  # Last 10 samples
            weight = 1.0 + (0.2 * i)  # More recent = higher weight
            weighted_sum += sample.rssi_dbm * weight
            total_weight += weight
        
        return int(weighted_sum / total_weight) if total_weight > 0 else -70
    
    def _calculate_stability(self, bssid: str) -> Tuple[float, str]:
        """
        Calculate signal stability from history.
        
        Returns:
            Tuple of (stability_score 0-1, stability_label)
        """
        samples = self.history.get(bssid, [])
        
        if len(samples) < self.min_samples:
            return 0.5, "Unknown"
        
        # Calculate standard deviation of recent RSSI values
        rssi_values = [s.rssi_dbm for s in samples[-20:]]
        mean_rssi = sum(rssi_values) / len(rssi_values)
        variance = sum((r - mean_rssi) ** 2 for r in rssi_values) / len(rssi_values)
        std_dev = math.sqrt(variance)
        
        # Convert to stability score (lower std dev = higher stability)
        # std_dev < 2 = very stable, > 8 = unstable
        if std_dev < 2:
            return 0.95, "Very Stable"
        elif std_dev < 4:
            return 0.8, "Stable"
        elif std_dev < 6:
            return 0.6, "Fluctuating"
        else:
            return 0.3, "Unstable"
    
    def _estimate_noise(self, bssid: str) -> int:
        """Estimate noise floor from samples or use default."""
        samples = self.history.get(bssid, [])
        
        # Check if any samples have noise readings
        noise_readings = [s.noise_dbm for s in samples if s.noise_dbm is not None]
        
        if noise_readings:
            return int(sum(noise_readings) / len(noise_readings))
        
        return int(self.noise_floor_estimate)
    
    def _calculate_distance(self, rssi: int, tx_power: int, freq_band: str) -> float:
        """
        Calculate distance using log-distance path loss model.
        
        Formula: d = 10 ^ ((TxPower - RSSI) / (10 * n))
        where n is the path loss exponent
        """
        # Get path loss exponent for frequency
        freq_key = freq_band.lower().replace(" ", "")
        n = PATH_LOSS_EXPONENTS.get(freq_key, 3.0)
        
        # Get reference RSSI
        ref_rssi = REFERENCE_RSSI.get(freq_key, -32)
        
        # Adjust for TX power difference from reference (20 dBm assumed)
        tx_adjustment = tx_power - 20
        adjusted_rssi = rssi - tx_adjustment
        
        # Calculate distance
        try:
            exponent = (ref_rssi - adjusted_rssi) / (10 * n)
            distance = REFERENCE_DISTANCE * (10 ** exponent)
            
            # Clamp to reasonable range
            return max(0.5, min(100, distance))
        except (ValueError, OverflowError):
            return 10.0  # Default fallback
    
    def _snr_distance_adjustment(self, snr: int) -> float:
        """
        Adjust distance estimate based on SNR.
        
        Low SNR often means signal is traveling through obstacles,
        which means actual distance might be shorter than RSSI suggests.
        """
        if snr >= 40:
            return 0.9   # Very clear signal, might be closer
        elif snr >= 25:
            return 1.0   # Normal
        elif snr >= 15:
            return 1.1   # Some obstruction
        elif snr >= 10:
            return 1.2   # Significant obstruction
        else:
            return 1.3   # Heavy obstruction, walls etc.
    
    def _calculate_confidence(self, stability: float, snr: Optional[int], 
                             freq_band: str) -> Tuple[int, int]:
        """
        Calculate confidence percentage and margin.
        
        Returns:
            Tuple of (confidence %, margin %)
        """
        # Base confidence from stability
        confidence = int(stability * 60)  # Max 60% from stability
        
        # Add confidence from SNR
        if snr is not None:
            if snr >= 30:
                confidence += 25
            elif snr >= 20:
                confidence += 15
            elif snr >= 10:
                confidence += 5
        
        # Frequency affects confidence (2.4GHz more predictable)
        if "2.4" in freq_band:
            confidence += 10
        elif "5" in freq_band:
            confidence += 5
        
        confidence = min(95, confidence)  # Cap at 95%
        
        # Calculate margin (inverse of confidence)
        if confidence >= 80:
            margin = 25
        elif confidence >= 60:
            margin = 40
        elif confidence >= 40:
            margin = 60
        else:
            margin = 80
        
        return confidence, margin
    
    def _guess_environment(self, distance: float, snr: Optional[int],
                          stability: float, freq_band: str) -> Tuple[str, str]:
        """
        Guess the physical environment based on metrics.
        
        Returns:
            Tuple of (short_guess, detailed_explanation)
        """
        # Determine wall penetration from SNR
        walls_guess = 0
        if snr is not None:
            if snr < 15:
                walls_guess = 2  # Multiple walls
            elif snr < 25:
                walls_guess = 1  # One wall
        
        # Adjust for 5GHz (worse wall penetration)
        if "5" in freq_band and walls_guess > 0:
            walls_guess = max(1, walls_guess - 1)  # 5GHz blocked more by walls
        
        # Generate guess
        if distance < 3 and walls_guess == 0 and stability > 0.7:
            guess = "Same room"
            detail = "Strong, stable signal suggests device is in the same room"
        elif distance < 8 and walls_guess <= 1:
            guess = "One wall away"
            detail = "Signal characteristics suggest one wall or adjacent room"
        elif distance < 15 and walls_guess <= 2:
            guess = "Two rooms away"
            detail = "Moderate signal with some attenuation, likely 1-2 walls"
        elif distance < 25:
            guess = "Different floor/far room"
            detail = "Weaker signal suggests floor change or multiple walls"
        else:
            guess = "Far away"
            detail = "Weak signal indicates significant distance or many obstacles"
        
        # Add stability note
        if stability < 0.5:
            detail += ". Signal unstable - device may be moving."
        
        return guess, detail
    
    def _signal_quality_label(self, percent: int) -> str:
        """Get signal quality label."""
        if percent >= 80:
            return "Excellent"
        elif percent >= 60:
            return "Good"
        elif percent >= 40:
            return "Fair"
        elif percent >= 20:
            return "Weak"
        else:
            return "Critical"
    
    def _snr_quality_label(self, snr: Optional[int]) -> str:
        """Get SNR quality label."""
        if snr is None:
            return "Unknown"
        elif snr >= 40:
            return "Excellent"
        elif snr >= 25:
            return "Good"
        elif snr >= 15:
            return "Fair"
        else:
            return "Poor"
    
    def _noise_level_label(self, noise_dbm: int) -> str:
        """Get noise level label."""
        if noise_dbm >= -85:
            return "High"
        elif noise_dbm >= -92:
            return "Medium"
        else:
            return "Low"


# Global estimator instance
_estimator: Optional[DistanceEstimator] = None


def get_estimator() -> DistanceEstimator:
    """Get the global distance estimator instance."""
    global _estimator
    if _estimator is None:
        _estimator = DistanceEstimator()
    return _estimator
