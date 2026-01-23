"""
Two-Mode Radar System for NEXUS WiFi Radar.

100% PASSIVE - No transmissions, only passive beacon reception.

MODE 1: STATIC DESKTOP MODE
- Device is stationary
- Distance from center = signal strength (stronger = closer)
- Angle = channel-based grouping (2.4GHz left, 5GHz right)
- Stable blip positions
- Circular heatmap

MODE 2: MOBILE HOMING MODE  
- Device can be rotated by user
- Distance from center = signal strength
- Angle = direction of strongest signal (via sensors or manual rotation)
- Blips rotate with device orientation
- Directional wedge heatmap
- Sonar beeps faster when pointed at AP
"""

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict


class RadarMode(Enum):
    """Radar operating modes."""
    STATIC_DESKTOP = "static"
    MOBILE_HOMING = "mobile"


@dataclass
class NetworkBlip:
    """Represents a network on the radar."""
    bssid: str
    ssid: str
    signal_percent: int
    channel: int
    frequency_band: str  # "2.4GHz", "5GHz", "6GHz"
    security: str
    vendor: str
    
    # Calculated position
    distance_ratio: float = 0.0  # 0 = center, 1 = edge
    angle_degrees: float = 0.0   # 0-360
    
    # For mobile mode - direction tracking
    peak_signal: int = 0
    peak_angle: float = 0.0
    signal_history: List[Tuple[float, int]] = field(default_factory=list)  # (angle, signal)
    
    @property
    def x_ratio(self) -> float:
        """X position as ratio (-1 to 1)."""
        return self.distance_ratio * math.cos(math.radians(self.angle_degrees))
    
    @property
    def y_ratio(self) -> float:
        """Y position as ratio (-1 to 1)."""
        return self.distance_ratio * math.sin(math.radians(self.angle_degrees))


@dataclass
class RadarState:
    """Current state of the radar system."""
    mode: RadarMode = RadarMode.STATIC_DESKTOP
    device_heading: float = 0.0      # Current device orientation (0-360)
    scan_angle: float = 0.0          # Rotating scan line angle
    is_calibrating: bool = False     # Mobile mode calibration in progress
    calibration_progress: float = 0.0
    
    # Sensor availability
    has_gyroscope: bool = False
    has_compass: bool = False
    has_multi_antenna: bool = False
    
    # Heatmap
    heatmap_mode: str = "circular"   # "circular" or "directional"
    directional_wedge_angle: float = 60.0  # Degrees width of directional wedge


class RadarModeBase(ABC):
    """Base class for radar modes."""
    
    @abstractmethod
    def calculate_blip_position(self, blip: NetworkBlip, state: RadarState) -> Tuple[float, float]:
        """
        Calculate blip position on radar.
        
        Returns:
            Tuple of (distance_ratio, angle_degrees)
        """
        pass
    
    @abstractmethod
    def calculate_heatmap_intensity(self, x: float, y: float, blips: List[NetworkBlip], 
                                     state: RadarState) -> float:
        """
        Calculate heatmap intensity at a point.
        
        Returns:
            Intensity value 0-100
        """
        pass
    
    @abstractmethod
    def calculate_sonar_frequency(self, blip: NetworkBlip, state: RadarState) -> Tuple[int, int]:
        """
        Calculate sonar beep parameters.
        
        Returns:
            Tuple of (frequency_hz, interval_ms)
        """
        pass


class StaticDesktopMode(RadarModeBase):
    """
    MODE 1: STATIC DESKTOP MODE
    
    - Device is stationary (no rotation tracking)
    - Distance from center = signal strength
    - Angle determined by WiFi channel:
        * 2.4GHz (Ch 1-14) → Left hemisphere (0-180°)
        * 5GHz (Ch 36-177) → Right hemisphere (180-360°)
        * 6GHz → Far right (330-360°)
    - Channels sorted within hemisphere
    - Circular heatmap
    """
    
    def calculate_blip_position(self, blip: NetworkBlip, state: RadarState) -> Tuple[float, float]:
        """Calculate position based on signal strength and channel."""
        
        # Distance: stronger signal = closer to center
        # 100% signal = 0.1 from center, 0% = 1.0 at edge
        distance_ratio = 1.0 - (blip.signal_percent / 100.0) * 0.85
        distance_ratio = max(0.1, min(1.0, distance_ratio))
        
        # Angle: based on channel and frequency band
        angle = self._channel_to_angle(blip.channel, blip.frequency_band)
        
        return distance_ratio, angle
    
    def _channel_to_angle(self, channel: int, band: str) -> float:
        """
        Map WiFi channel to radar angle.
        
        2.4GHz (Ch 1-14):  Left hemisphere, 15° to 165°
        5GHz (Ch 36-177):  Right hemisphere, 195° to 345°
        6GHz:              Far right, 350° to 360°
        """
        if "2.4" in band or channel <= 14:
            # 2.4GHz: Channels 1-14 map to 15°-165° (left side)
            # Channel 1 at top-left (15°), Channel 14 at bottom-left (165°)
            angle = 15 + (channel - 1) * (150 / 13)
            
        elif "5" in band or (36 <= channel <= 177):
            # 5GHz: Map channels to right hemisphere (195°-345°)
            # Common 5GHz channels: 36,40,44,48,52,56,60,64,100,104,108,112,116,120,124,128,132,136,140,144,149,153,157,161,165
            if channel <= 64:
                # Lower 5GHz (36-64) → 195° to 255°
                ch_offset = (channel - 36) / 28
                angle = 195 + ch_offset * 60
            elif channel <= 144:
                # Middle 5GHz (100-144) → 255° to 300°
                ch_offset = (channel - 100) / 44
                angle = 255 + ch_offset * 45
            else:
                # Upper 5GHz (149-177) → 300° to 345°
                ch_offset = (channel - 149) / 28
                angle = 300 + ch_offset * 45
                
        else:
            # 6GHz or unknown: far right
            angle = 350 + (channel % 10) * 1
        
        return angle % 360
    
    def calculate_heatmap_intensity(self, x: float, y: float, blips: List[NetworkBlip],
                                     state: RadarState) -> float:
        """Circular heatmap - intensity based on distance to all blips."""
        if not blips:
            return 0
        
        max_intensity = 0
        influence_radius = 0.3  # How far each blip's influence extends
        
        for blip in blips:
            # Calculate distance from point to blip
            dx = x - blip.x_ratio
            dy = y - blip.y_ratio
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < influence_radius:
                # Intensity falls off with distance, weighted by signal strength
                falloff = 1.0 - (dist / influence_radius)
                intensity = blip.signal_percent * falloff
                max_intensity = max(max_intensity, intensity)
        
        return max_intensity
    
    def calculate_sonar_frequency(self, blip: NetworkBlip, state: RadarState) -> Tuple[int, int]:
        """Sonar based on signal strength only (no direction in static mode)."""
        # Frequency: 200Hz (weak) to 2000Hz (strong)
        freq = 200 + int((blip.signal_percent / 100.0) * 1800)
        
        # Interval: 500ms (weak) to 100ms (strong) 
        interval = 500 - int((blip.signal_percent / 100.0) * 400)
        
        return freq, interval


class MobileHomingMode(RadarModeBase):
    """
    MODE 2: MOBILE HOMING MODE
    
    - Device can be rotated by user
    - Distance from center = signal strength
    - Angle = direction of strongest signal:
        * Uses device orientation sensors if available
        * Or manual "rotate to scan" calibration
        * Or multi-antenna RSSI differences
    - Blips rotate as device rotates
    - Directional wedge heatmap
    - Sonar beeps faster when pointed at AP
    
    Like the motion tracker from ALIENS.
    """
    
    def __init__(self):
        # Track signal strength at different device orientations
        self.calibration_data: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self.peak_directions: Dict[str, float] = {}  # BSSID -> peak direction
    
    def record_calibration_sample(self, bssid: str, device_heading: float, signal: int):
        """Record a signal sample during calibration rotation."""
        self.calibration_data[bssid].append((device_heading, signal))
        
        # Update peak direction
        samples = self.calibration_data[bssid]
        if samples:
            peak_sample = max(samples, key=lambda x: x[1])
            self.peak_directions[bssid] = peak_sample[0]
    
    def get_peak_direction(self, bssid: str) -> Optional[float]:
        """Get the direction where this AP's signal was strongest."""
        return self.peak_directions.get(bssid)
    
    def calculate_blip_position(self, blip: NetworkBlip, state: RadarState) -> Tuple[float, float]:
        """Calculate position based on signal strength and detected direction."""
        
        # Distance: same as static mode
        distance_ratio = 1.0 - (blip.signal_percent / 100.0) * 0.85
        distance_ratio = max(0.1, min(1.0, distance_ratio))
        
        # Angle: based on peak signal direction, adjusted for current heading
        peak_dir = self.get_peak_direction(blip.bssid)
        
        if peak_dir is not None:
            # AP direction relative to current device heading
            # If device is pointing at AP, AP appears at top (90°)
            relative_angle = (peak_dir - state.device_heading + 90) % 360
            angle = relative_angle
        else:
            # No calibration data - fall back to channel-based
            angle = self._fallback_channel_angle(blip.channel, blip.frequency_band)
        
        return distance_ratio, angle
    
    def _fallback_channel_angle(self, channel: int, band: str) -> float:
        """Fallback to channel-based positioning when no direction data."""
        if "2.4" in band or channel <= 14:
            return 15 + (channel - 1) * (150 / 13)
        else:
            return 195 + ((channel - 36) % 140) * (150 / 140)
    
    def calculate_heatmap_intensity(self, x: float, y: float, blips: List[NetworkBlip],
                                     state: RadarState) -> float:
        """
        Directional wedge heatmap.
        
        Intensity is higher in the direction we're pointing (top of radar).
        """
        if not blips:
            return 0
        
        # Convert point to angle from center
        point_angle = math.degrees(math.atan2(y, x)) % 360
        
        # Check if point is within the directional wedge (centered at 90° = top)
        wedge_center = 90  # Top of radar
        wedge_half = state.directional_wedge_angle / 2
        
        angle_diff = abs((point_angle - wedge_center + 180) % 360 - 180)
        wedge_factor = max(0, 1.0 - (angle_diff / wedge_half)) if angle_diff < wedge_half else 0.3
        
        # Calculate base intensity from blips
        max_intensity = 0
        influence_radius = 0.4
        
        for blip in blips:
            dx = x - blip.x_ratio
            dy = y - blip.y_ratio
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < influence_radius:
                falloff = 1.0 - (dist / influence_radius)
                intensity = blip.signal_percent * falloff * wedge_factor
                max_intensity = max(max_intensity, intensity)
        
        return max_intensity
    
    def calculate_sonar_frequency(self, blip: NetworkBlip, state: RadarState) -> Tuple[int, int]:
        """
        Sonar that beeps faster when pointed at the AP.
        
        Like the Alien motion tracker - faster clicks = closer to target direction.
        """
        # Base frequency from signal strength
        base_freq = 200 + int((blip.signal_percent / 100.0) * 1800)
        
        # Calculate how close we're pointing to this AP
        peak_dir = self.get_peak_direction(blip.bssid)
        
        if peak_dir is not None:
            # Angular difference between where we're pointing and where AP is
            angle_diff = abs((state.device_heading - peak_dir + 180) % 360 - 180)
            
            # Pointing accuracy: 1.0 = directly at AP, 0.0 = opposite direction
            pointing_accuracy = 1.0 - (angle_diff / 180.0)
            
            # Interval: gets faster when pointing at AP
            # 600ms when pointing away, 50ms when pointing directly at AP
            base_interval = 600 - int((blip.signal_percent / 100.0) * 200)
            interval = int(base_interval * (1.0 - pointing_accuracy * 0.9))
            interval = max(50, interval)
            
            # Frequency boost when pointing at AP
            freq = base_freq + int(pointing_accuracy * 500)
        else:
            # No direction data - use signal-only calculation
            interval = 500 - int((blip.signal_percent / 100.0) * 400)
            freq = base_freq
        
        return freq, interval


class RadarSystem:
    """
    Main radar system managing both modes.
    
    100% PASSIVE - All calculations use only received beacon data.
    """
    
    def __init__(self):
        self.state = RadarState()
        self.static_mode = StaticDesktopMode()
        self.mobile_mode = MobileHomingMode()
        self.blips: Dict[str, NetworkBlip] = {}
        
        # Callbacks
        self.on_mode_change: Optional[Callable[[RadarMode], None]] = None
        self.on_calibration_complete: Optional[Callable[[], None]] = None
        
        # Detect available sensors
        self._detect_sensors()
    
    def _detect_sensors(self):
        """Detect available orientation sensors (platform-specific)."""
        import platform
        
        self.state.has_gyroscope = False
        self.state.has_compass = False
        self.state.has_multi_antenna = False
        
        # On Windows, check for sensor API
        if platform.system() == "Windows":
            try:
                # Windows Sensor API would be checked here
                # For now, assume no sensors on desktop Windows
                pass
            except Exception:
                pass
        
        # On mobile/embedded, would check for:
        # - Android: SensorManager.getDefaultSensor(TYPE_ORIENTATION)
        # - iOS: CLLocationManager heading
        # - Raspberry Pi: I2C compass modules
        
        # Auto-select mode based on sensors
        if self.state.has_gyroscope or self.state.has_compass:
            self.state.mode = RadarMode.MOBILE_HOMING
        else:
            self.state.mode = RadarMode.STATIC_DESKTOP
    
    @property
    def current_mode(self) -> RadarModeBase:
        """Get the currently active mode handler."""
        if self.state.mode == RadarMode.MOBILE_HOMING:
            return self.mobile_mode
        return self.static_mode
    
    def set_mode(self, mode: RadarMode):
        """Switch radar mode."""
        if mode != self.state.mode:
            self.state.mode = mode
            
            # Update heatmap style
            if mode == RadarMode.STATIC_DESKTOP:
                self.state.heatmap_mode = "circular"
            else:
                self.state.heatmap_mode = "directional"
            
            if self.on_mode_change:
                self.on_mode_change(mode)
    
    def update_device_heading(self, heading: float):
        """Update device orientation (0-360 degrees, 0 = North)."""
        self.state.device_heading = heading % 360
    
    def start_calibration(self):
        """Start mobile mode calibration (user rotates device 360°)."""
        self.state.is_calibrating = True
        self.state.calibration_progress = 0.0
        self.mobile_mode.calibration_data.clear()
        self.mobile_mode.peak_directions.clear()
    
    def record_calibration_point(self, heading: float, networks: List[dict]):
        """Record calibration data at current heading."""
        if not self.state.is_calibrating:
            return
        
        for net in networks:
            self.mobile_mode.record_calibration_sample(
                net['bssid'], heading, net['signal']
            )
        
        # Update progress (assume 360° rotation needed)
        self.state.calibration_progress = min(1.0, self.state.calibration_progress + (1.0 / 36))
    
    def complete_calibration(self):
        """Complete calibration and switch to mobile homing mode."""
        self.state.is_calibrating = False
        self.state.calibration_progress = 1.0
        
        if self.on_calibration_complete:
            self.on_calibration_complete()
    
    def update_network(self, bssid: str, ssid: str, signal: int, channel: int,
                       security: str = "", vendor: str = ""):
        """Update or add a network to the radar."""
        band = "2.4GHz" if channel <= 14 else "5GHz" if channel <= 177 else "6GHz"
        
        if bssid in self.blips:
            blip = self.blips[bssid]
            blip.signal_percent = signal
            blip.channel = channel
        else:
            blip = NetworkBlip(
                bssid=bssid,
                ssid=ssid,
                signal_percent=signal,
                channel=channel,
                frequency_band=band,
                security=security,
                vendor=vendor
            )
            self.blips[bssid] = blip
        
        # Calculate position
        blip.distance_ratio, blip.angle_degrees = self.current_mode.calculate_blip_position(
            blip, self.state
        )
        
        # If calibrating, record sample
        if self.state.is_calibrating:
            self.mobile_mode.record_calibration_sample(bssid, self.state.device_heading, signal)
    
    def get_blip_positions(self) -> List[Tuple[str, float, float, float, int]]:
        """
        Get all blip positions for rendering.
        
        Returns:
            List of (bssid, x_ratio, y_ratio, distance_ratio, signal_percent)
        """
        positions = []
        for bssid, blip in self.blips.items():
            positions.append((
                bssid,
                blip.x_ratio,
                blip.y_ratio,
                blip.distance_ratio,
                blip.signal_percent
            ))
        return positions
    
    def get_heatmap_intensity(self, x: float, y: float) -> float:
        """Get heatmap intensity at a point (-1 to 1 coordinates)."""
        return self.current_mode.calculate_heatmap_intensity(
            x, y, list(self.blips.values()), self.state
        )
    
    def get_sonar_params(self, bssid: str) -> Optional[Tuple[int, int]]:
        """Get sonar parameters for a network."""
        blip = self.blips.get(bssid)
        if blip:
            return self.current_mode.calculate_sonar_frequency(blip, self.state)
        return None
    
    def clear(self):
        """Clear all blips."""
        self.blips.clear()


# Global radar system instance
_radar_system: Optional[RadarSystem] = None


def get_radar_system() -> RadarSystem:
    """Get the global radar system instance."""
    global _radar_system
    if _radar_system is None:
        _radar_system = RadarSystem()
    return _radar_system
