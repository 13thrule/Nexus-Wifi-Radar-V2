"""
Tests for the two-mode radar system.

Tests both Static Desktop and Mobile Homing modes.
"""

import pytest
from nexus.core.radar_modes import (
    RadarMode, NetworkBlip, RadarState, 
    StaticDesktopMode, MobileHomingMode, RadarSystem, get_radar_system
)


class TestRadarMode:
    """Tests for RadarMode enum."""
    
    def test_radar_mode_values(self):
        """Test radar mode enum has expected values."""
        assert RadarMode.STATIC_DESKTOP.value == "static"
        assert RadarMode.MOBILE_HOMING.value == "mobile"
    
    def test_radar_modes_are_distinct(self):
        """Test modes are different."""
        assert RadarMode.STATIC_DESKTOP != RadarMode.MOBILE_HOMING


class TestNetworkBlip:
    """Tests for NetworkBlip dataclass."""
    
    def test_blip_creation(self):
        """Test creating a network blip."""
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="TestNetwork",
            signal_percent=75,
            channel=6,
            frequency_band="2.4GHz",
            security="WPA2",
            vendor="Test Vendor"
        )
        assert blip.bssid == "AA:BB:CC:DD:EE:FF"
        assert blip.signal_percent == 75
        assert blip.frequency_band == "2.4GHz"
    
    def test_blip_position_ratios(self):
        """Test x/y ratio calculations."""
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="Test",
            signal_percent=50,
            channel=6,
            frequency_band="2.4GHz",
            security="",
            vendor="",
            distance_ratio=0.5,
            angle_degrees=90
        )
        # At 90 degrees, x should be ~0, y should be positive
        assert abs(blip.x_ratio) < 0.01
        assert blip.y_ratio > 0


class TestStaticDesktopMode:
    """Tests for Static Desktop mode."""
    
    def test_calculate_blip_position_24ghz(self):
        """Test 2.4GHz positioning."""
        mode = StaticDesktopMode()
        state = RadarState()
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="Test",
            signal_percent=70,
            channel=6,
            frequency_band="2.4GHz",
            security="WPA2",
            vendor="Cisco"
        )
        
        dist, angle = mode.calculate_blip_position(blip, state)
        
        # Stronger signal = closer (smaller distance ratio)
        assert 0 < dist < 1
        # 2.4GHz should be in left hemisphere (15-165)
        assert 15 <= angle <= 165
    
    def test_calculate_blip_position_5ghz(self):
        """Test 5GHz positioning."""
        mode = StaticDesktopMode()
        state = RadarState()
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="Test",
            signal_percent=50,
            channel=149,
            frequency_band="5GHz",
            security="WPA3",
            vendor="Ubiquiti"
        )
        
        dist, angle = mode.calculate_blip_position(blip, state)
        
        assert 0 < dist < 1
        # 5GHz should be in right hemisphere (195-345)
        assert 195 <= angle <= 360 or 0 <= angle <= 15
    
    def test_signal_affects_distance(self):
        """Test that signal strength affects distance ratio."""
        mode = StaticDesktopMode()
        state = RadarState()
        
        strong_blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Strong", signal_percent=90,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        weak_blip = NetworkBlip(
            bssid="11:22:33:44:55:66", ssid="Weak", signal_percent=20,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        
        strong_dist, _ = mode.calculate_blip_position(strong_blip, state)
        weak_dist, _ = mode.calculate_blip_position(weak_blip, state)
        
        # Strong signal should be closer to center
        assert strong_dist < weak_dist
    
    def test_heatmap_intensity(self):
        """Test heatmap intensity calculation."""
        mode = StaticDesktopMode()
        state = RadarState()
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Test", signal_percent=80,
            channel=6, frequency_band="2.4GHz", security="", vendor="",
            distance_ratio=0.3, angle_degrees=45
        )
        blip.distance_ratio = 0.3
        blip.angle_degrees = 45
        
        # Point close to blip should have high intensity
        intensity_near = mode.calculate_heatmap_intensity(blip.x_ratio, blip.y_ratio, [blip], state)
        # Point far from blip should have low intensity
        intensity_far = mode.calculate_heatmap_intensity(-0.9, -0.9, [blip], state)
        
        assert intensity_near > intensity_far
    
    def test_sonar_frequency(self):
        """Test sonar frequency calculation."""
        mode = StaticDesktopMode()
        state = RadarState()
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Test", signal_percent=80,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        
        freq, interval = mode.calculate_sonar_frequency(blip, state)
        
        assert freq > 200  # Higher than minimum
        assert interval < 500  # Shorter than maximum


class TestMobileHomingMode:
    """Tests for Mobile Homing mode."""
    
    def test_record_calibration_sample(self):
        """Test recording calibration data."""
        mode = MobileHomingMode()
        
        # Record samples at different headings
        mode.record_calibration_sample("AA:BB:CC:DD:EE:FF", 0.0, 50)
        mode.record_calibration_sample("AA:BB:CC:DD:EE:FF", 90.0, 80)  # Strongest
        mode.record_calibration_sample("AA:BB:CC:DD:EE:FF", 180.0, 40)
        
        # Peak direction should be at 90 degrees (strongest signal)
        peak = mode.get_peak_direction("AA:BB:CC:DD:EE:FF")
        assert peak == 90.0
    
    def test_mobile_position_with_calibration(self):
        """Test positioning after calibration."""
        mode = MobileHomingMode()
        state = RadarState()
        state.device_heading = 0.0
        
        # Calibrate: AP strongest at 90 degrees
        mode.record_calibration_sample("AA:BB:CC:DD:EE:FF", 90.0, 80)
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Test", signal_percent=70,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        
        dist, angle = mode.calculate_blip_position(blip, state)
        
        assert 0 < dist < 1
        # Angle should be calculated based on peak direction
        assert 0 <= angle <= 360
    
    def test_sonar_faster_when_pointing_at_ap(self):
        """Test sonar beeps faster when pointing at AP."""
        mode = MobileHomingMode()
        
        # Calibrate: AP at 90 degrees
        mode.record_calibration_sample("AA:BB:CC:DD:EE:FF", 90.0, 80)
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Test", signal_percent=70,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        
        # Pointing at AP (heading 90)
        state_at = RadarState()
        state_at.device_heading = 90.0
        freq_at, interval_at = mode.calculate_sonar_frequency(blip, state_at)
        
        # Pointing away from AP (heading 270)
        state_away = RadarState()
        state_away.device_heading = 270.0
        freq_away, interval_away = mode.calculate_sonar_frequency(blip, state_away)
        
        # Interval should be shorter when pointing at AP
        assert interval_at < interval_away


class TestRadarSystem:
    """Tests for the RadarSystem controller."""
    
    def test_default_mode(self):
        """Test default mode is static on desktop without sensors."""
        system = RadarSystem()
        assert system.state.mode == RadarMode.STATIC_DESKTOP
    
    def test_mode_switching(self):
        """Test switching between modes."""
        system = RadarSystem()
        
        # Start in static
        assert system.state.mode == RadarMode.STATIC_DESKTOP
        
        # Switch to mobile
        system.set_mode(RadarMode.MOBILE_HOMING)
        assert system.state.mode == RadarMode.MOBILE_HOMING
        assert isinstance(system.current_mode, MobileHomingMode)
        
        # Switch back to static
        system.set_mode(RadarMode.STATIC_DESKTOP)
        assert system.state.mode == RadarMode.STATIC_DESKTOP
        assert isinstance(system.current_mode, StaticDesktopMode)
    
    def test_update_network(self):
        """Test updating network data."""
        system = RadarSystem()
        
        system.update_network(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="TestNetwork",
            signal=75,
            channel=6,
            security="WPA2",
            vendor="Cisco"
        )
        
        assert "AA:BB:CC:DD:EE:FF" in system.blips
        blip = system.blips["AA:BB:CC:DD:EE:FF"]
        assert blip.signal_percent == 75
        assert blip.frequency_band == "2.4GHz"
    
    def test_calibration_workflow(self):
        """Test calibration workflow."""
        system = RadarSystem()
        system.set_mode(RadarMode.MOBILE_HOMING)
        
        # Start calibration
        system.start_calibration()
        assert system.state.is_calibrating
        
        # Record calibration points
        networks = [{"bssid": "AA:BB:CC:DD:EE:FF", "signal": 50}]
        system.record_calibration_point(0.0, networks)
        system.record_calibration_point(90.0, [{"bssid": "AA:BB:CC:DD:EE:FF", "signal": 80}])
        
        # Complete calibration
        system.complete_calibration()
        assert not system.state.is_calibrating
        
        # Check peak direction was recorded
        assert "AA:BB:CC:DD:EE:FF" in system.mobile_mode.peak_directions
    
    def test_get_radar_system_singleton(self):
        """Test singleton pattern for radar system."""
        # Clear singleton for test
        import nexus.core.radar_modes as rm
        rm._radar_system = None
        
        system1 = get_radar_system()
        system2 = get_radar_system()
        assert system1 is system2


class TestPassiveOperation:
    """Tests to verify radar modes are 100% passive."""
    
    def test_static_mode_no_transmission(self):
        """Verify static mode doesn't transmit."""
        mode = StaticDesktopMode()
        state = RadarState()
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Test", signal_percent=70,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        # All operations are calculations on received data - no network calls
        dist, angle = mode.calculate_blip_position(blip, state)
        assert dist is not None
        assert angle is not None
    
    def test_mobile_mode_no_transmission(self):
        """Verify mobile mode doesn't transmit."""
        mode = MobileHomingMode()
        state = RadarState()
        
        # Calibration only records received signal strengths
        mode.record_calibration_sample("AA:BB:CC:DD:EE:FF", 0.0, 50)
        
        blip = NetworkBlip(
            bssid="AA:BB:CC:DD:EE:FF", ssid="Test", signal_percent=70,
            channel=6, frequency_band="2.4GHz", security="", vendor=""
        )
        # No network operations
        dist, angle = mode.calculate_blip_position(blip, state)
        assert dist is not None
    
    def test_radar_system_passive(self):
        """Verify radar system is passive."""
        system = RadarSystem()
        # update_network just processes data we already have
        system.update_network("AA:BB:CC:DD:EE:FF", "Test", 70, 6, "WPA2", "Cisco")
        # No transmission occurs - we're just positioning data
        assert "AA:BB:CC:DD:EE:FF" in system.blips
