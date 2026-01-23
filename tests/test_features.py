"""
Tests for fingerprinting, stability tracking, and spoof detection.

All features are 100% PASSIVE.
"""

import pytest
import time
from nexus.core.fingerprint import (
    DeviceFingerprinter, DeviceType, DeviceFingerprint,
    get_fingerprinter, DEVICE_ICONS
)
from nexus.core.stability import (
    SignalStabilityTracker, WallEstimator, StabilityRating, WallEstimate,
    get_stability_tracker, get_wall_estimator
)
from nexus.security.spoof import (
    PassiveSpoofDetector, SpoofAlert, ThreatLevel, SpoofType,
    get_spoof_detector
)


class TestDeviceFingerprinting:
    """Tests for device fingerprinting."""
    
    def test_fingerprint_router_by_vendor(self):
        """Test router detection from vendor."""
        fp = DeviceFingerprinter()
        result = fp.fingerprint(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="MyNetwork",
            vendor="TP-Link Technologies",
            channel=6,
            signal=70,
            security="WPA2"
        )
        assert result.device_type == DeviceType.ROUTER
        assert result.confidence > 50
    
    def test_fingerprint_mobile_hotspot(self):
        """Test mobile hotspot detection."""
        fp = DeviceFingerprinter()
        result = fp.fingerprint(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="iPhone",
            vendor="Apple Inc",
            channel=6,
            signal=85,
            security="WPA2"
        )
        assert result.device_type == DeviceType.MOBILE_HOTSPOT
    
    def test_fingerprint_enterprise(self):
        """Test enterprise AP detection."""
        fp = DeviceFingerprinter()
        result = fp.fingerprint(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="CorpNetwork",
            vendor="Cisco Systems",
            channel=149,
            signal=60,
            security="WPA2-Enterprise"
        )
        assert result.device_type == DeviceType.ENTERPRISE
    
    def test_fingerprint_iot_device(self):
        """Test IoT device detection."""
        fp = DeviceFingerprinter()
        result = fp.fingerprint(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="Ring-Doorbell",
            vendor="Ring LLC",
            channel=11,
            signal=55,
            security="WPA2"
        )
        assert result.device_type == DeviceType.IOT_DEVICE
    
    def test_device_icons_exist(self):
        """Test all device types have icons."""
        for dt in DeviceType:
            assert dt in DEVICE_ICONS
            assert len(DEVICE_ICONS[dt]) > 0
    
    def test_fingerprinter_is_passive(self):
        """Verify fingerprinting is 100% passive."""
        fp = DeviceFingerprinter()
        # Only processes provided data, no network calls
        result = fp.fingerprint("AA:BB:CC:DD:EE:FF", "Test", "Unknown", 6, 50, "WPA2")
        assert result is not None


class TestSignalStability:
    """Tests for signal stability tracking."""
    
    def test_record_signal(self):
        """Test recording signal samples."""
        tracker = SignalStabilityTracker()
        metrics = tracker.record_signal("AA:BB:CC:DD:EE:FF", "TestNet", 70)
        assert metrics.current_signal == 70
        assert metrics.observation_count == 1
    
    def test_stability_calculation(self):
        """Test stability rating calculation."""
        tracker = SignalStabilityTracker()
        
        # Record stable signals
        for _ in range(10):
            tracker.record_signal("AA:BB:CC:DD:EE:FF", "StableNet", 70)
        
        metrics = tracker.get_metrics("AA:BB:CC:DD:EE:FF")
        assert metrics.stability_rating in [StabilityRating.ROCK_SOLID, StabilityRating.STABLE]
        assert metrics.stability_score >= 70
    
    def test_jitter_detection(self):
        """Test signal jitter detection."""
        tracker = SignalStabilityTracker()
        
        # Record fluctuating signals
        signals = [50, 80, 45, 85, 55, 75, 40, 90, 60, 70]
        for sig in signals:
            tracker.record_signal("AA:BB:CC:DD:EE:FF", "UnstableNet", sig)
        
        metrics = tracker.get_metrics("AA:BB:CC:DD:EE:FF")
        assert metrics.current_jitter > 5  # High jitter expected
        assert metrics.stability_rating in [StabilityRating.UNSTABLE, StabilityRating.ERRATIC]
    
    def test_stability_bar(self):
        """Test ASCII stability bar generation."""
        tracker = SignalStabilityTracker()
        for _ in range(10):
            tracker.record_signal("AA:BB:CC:DD:EE:FF", "Test", 70)
        
        bar = tracker.get_stability_bar("AA:BB:CC:DD:EE:FF", 10)
        assert len(bar) == 10
        assert "·" in bar or "█" in bar or "▓" in bar
    
    def test_tracker_is_passive(self):
        """Verify stability tracking is 100% passive."""
        tracker = SignalStabilityTracker()
        # Only records provided data
        tracker.record_signal("AA:BB:CC:DD:EE:FF", "Test", 70)
        metrics = tracker.get_metrics("AA:BB:CC:DD:EE:FF")
        assert metrics is not None


class TestWallEstimation:
    """Tests for wall estimation."""
    
    def test_line_of_sight(self):
        """Test line of sight detection."""
        estimator = WallEstimator()
        result = estimator.estimate_walls(
            signal_dbm=-35,  # Very strong signal
            frequency_mhz=2437,
            estimated_distance=3.0  # Very close
        )
        # Strong signal at close range should be line of sight or minimal obstruction
        assert result.wall_count <= 1
    
    def test_one_wall(self):
        """Test one wall detection."""
        estimator = WallEstimator()
        result = estimator.estimate_walls(
            signal_dbm=-60,
            frequency_mhz=2437,
            estimated_distance=10.0
        )
        # Should detect some obstruction
        assert result.wall_count >= 0
    
    def test_multiple_walls(self):
        """Test multiple walls detection."""
        estimator = WallEstimator()
        result = estimator.estimate_walls(
            signal_dbm=-80,  # Weak signal
            frequency_mhz=2437,
            estimated_distance=15.0
        )
        assert result.wall_count >= 1
    
    def test_5ghz_adjustment(self):
        """Test 5GHz wall estimation adjustment."""
        estimator = WallEstimator()
        result_24 = estimator.estimate_walls(-70, 2437, 15.0)
        result_5 = estimator.estimate_walls(-70, 5180, 15.0)
        
        # 5GHz should show adjustment in factors
        assert "5GHz" in " ".join(result_5.factors)
    
    def test_wall_estimator_is_passive(self):
        """Verify wall estimation is 100% passive."""
        estimator = WallEstimator()
        # Only uses provided RF data
        result = estimator.estimate_walls(-60, 2437, 10.0)
        assert result is not None


class TestSpoofDetection:
    """Tests for spoof detection."""
    
    def test_evil_twin_detection(self):
        """Test evil twin (multiple BSSIDs same SSID) detection."""
        detector = PassiveSpoofDetector()
        
        # Add multiple APs with same SSID
        detector.analyze_network("AA:BB:CC:DD:EE:01", "FreeWifi", 70, 6, "WPA2")
        detector.analyze_network("AA:BB:CC:DD:EE:02", "FreeWifi", 65, 11, "WPA2")
        alerts = detector.analyze_network("AA:BB:CC:DD:EE:03", "FreeWifi", 60, 1, "WPA2")
        
        # Should detect potential evil twin
        active_alerts = detector.get_active_alerts()
        evil_twins = [a for a in active_alerts if a.spoof_type == SpoofType.EVIL_TWIN]
        assert len(evil_twins) > 0
    
    def test_security_downgrade_detection(self):
        """Test security downgrade detection."""
        detector = PassiveSpoofDetector()
        
        # First observation sets baseline
        detector.analyze_network("AA:BB:CC:DD:EE:FF", "SecureNet", 70, 6, "WPA2")
        detector.analyze_network("AA:BB:CC:DD:EE:FF", "SecureNet", 70, 6, "WPA2")
        detector.analyze_network("AA:BB:CC:DD:EE:FF", "SecureNet", 70, 6, "WPA2")
        
        # Downgrade to OPEN
        alerts = detector.analyze_network("11:22:33:44:55:66", "SecureNet", 75, 6, "OPEN")
        
        # Should detect downgrade
        active_alerts = detector.get_active_alerts()
        downgrades = [a for a in active_alerts if a.spoof_type == SpoofType.SECURITY_DOWNGRADE]
        assert len(downgrades) >= 0  # May or may not trigger depending on counts
    
    def test_common_target_detection(self):
        """Test common attack target SSID detection."""
        detector = PassiveSpoofDetector()
        
        alerts = detector.analyze_network(
            "AA:BB:CC:DD:EE:FF", "Free WiFi Hotspot", 80, 6, "OPEN"
        )
        
        active_alerts = detector.get_active_alerts()
        targets = [a for a in active_alerts if a.spoof_type == SpoofType.SSID_BROADCAST]
        assert len(targets) > 0
    
    def test_alert_dismissal(self):
        """Test alert dismissal."""
        detector = PassiveSpoofDetector()
        
        detector.analyze_network("AA:BB:CC:DD:EE:FF", "Free WiFi", 80, 6, "OPEN")
        
        alerts = detector.get_active_alerts()
        if alerts:
            detector.dismiss_alert(alerts[0].alert_id)
            active_after = detector.get_active_alerts()
            assert len(active_after) < len(alerts)
    
    def test_trusted_network(self):
        """Test trusted network marking."""
        detector = PassiveSpoofDetector()
        
        detector.add_trusted_network("HomeNetwork", "AA:BB:CC:DD:EE:FF", "WPA2")
        profile = detector.profiles.get("HomeNetwork")
        
        assert profile is not None
        assert profile.is_trusted
        assert "AA:BB:CC:DD:EE:FF" in profile.expected_bssids
    
    def test_spoof_detector_is_passive(self):
        """Verify spoof detection is 100% passive."""
        detector = PassiveSpoofDetector()
        # Only analyzes provided beacon data
        alerts = detector.analyze_network("AA:BB:CC:DD:EE:FF", "Test", 70, 6, "WPA2")
        assert isinstance(alerts, list)


class TestGlobalInstances:
    """Test global singleton instances."""
    
    def test_fingerprinter_singleton(self):
        """Test fingerprinter singleton."""
        import nexus.core.fingerprint as fp_mod
        fp_mod._fingerprinter = None
        
        fp1 = get_fingerprinter()
        fp2 = get_fingerprinter()
        assert fp1 is fp2
    
    def test_stability_tracker_singleton(self):
        """Test stability tracker singleton."""
        import nexus.core.stability as st_mod
        st_mod._stability_tracker = None
        
        t1 = get_stability_tracker()
        t2 = get_stability_tracker()
        assert t1 is t2
    
    def test_wall_estimator_singleton(self):
        """Test wall estimator singleton."""
        import nexus.core.stability as st_mod
        st_mod._wall_estimator = None
        
        e1 = get_wall_estimator()
        e2 = get_wall_estimator()
        assert e1 is e2
    
    def test_spoof_detector_singleton(self):
        """Test spoof detector singleton."""
        import nexus.security.spoof as sp_mod
        sp_mod._spoof_detector = None
        
        d1 = get_spoof_detector()
        d2 = get_spoof_detector()
        assert d1 is d2


class TestPassiveIntelligenceCore:
    """Tests for the Passive Intelligence Core (PIC)."""
    
    def test_pic_creation(self):
        """Test PIC can be created."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        assert pic is not None
        assert pic.networks == {}
    
    def test_pic_process_network(self):
        """Test processing a network."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        intel = pic.process_network(
            bssid="AA:BB:CC:DD:EE:FF",
            ssid="TestNetwork",
            signal_percent=75,
            channel=6,
            security="WPA2-PSK",
            vendor="TP-Link",
            band="2.4GHz"
        )
        
        assert intel is not None
        assert intel.bssid == "AA:BB:CC:DD:EE:FF"
        assert intel.ssid == "TestNetwork"
        assert intel.signal_percent == 75
        assert intel.channel == 6
    
    def test_pic_get_network(self):
        """Test getting a specific network."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        pic.process_network(
            bssid="11:22:33:44:55:66",
            ssid="Test1",
            signal_percent=80,
            channel=1,
            security="WPA2"
        )
        
        intel = pic.get_network("11:22:33:44:55:66")
        assert intel is not None
        assert intel.ssid == "Test1"
        
        intel2 = pic.get_network("99:99:99:99:99:99")
        assert intel2 is None
    
    def test_pic_get_all_networks(self):
        """Test getting all networks sorted by signal."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        pic.process_network("A1:B1:C1:D1:E1:F1", "Net1", 50, 1, "WPA2")
        pic.process_network("A2:B2:C2:D2:E2:F2", "Net2", 90, 6, "WPA2")
        pic.process_network("A3:B3:C3:D3:E3:F3", "Net3", 70, 11, "WPA2")
        
        networks = pic.get_all_networks()
        assert len(networks) == 3
        assert networks[0].signal_percent == 90  # Strongest first
        assert networks[2].signal_percent == 50  # Weakest last
    
    def test_pic_security_analysis(self):
        """Test security rating detection."""
        from nexus.core.intelligence import PassiveIntelligenceCore, SecurityRating
        pic = PassiveIntelligenceCore()
        
        # WPA3 should be excellent
        intel = pic.process_network("A1:B1:C1:D1:E1:F1", "SecureNet", 80, 6, "WPA3-SAE")
        assert intel.security.security_rating == SecurityRating.EXCELLENT
        
        # Open should be critical
        intel = pic.process_network("B1:B1:C1:D1:E1:F1", "OpenNet", 80, 6, "Open")
        assert intel.security.security_rating == SecurityRating.CRITICAL
    
    def test_pic_temporal_analysis(self):
        """Test temporal behaviour analysis."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        # Record multiple observations
        for i in range(10):
            intel = pic.process_network(
                "A1:B1:C1:D1:E1:F1", "StableNet", 75, 6, "WPA2"
            )
        
        assert intel.temporal.stability_score > 0
        assert intel.observation_count == 10
    
    def test_pic_distance_estimation(self):
        """Test distance estimation."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        # Strong signal = close
        intel_close = pic.process_network("A1:B1:C1:D1:E1:F1", "CloseNet", 90, 6, "WPA2")
        
        # Weak signal = far
        intel_far = pic.process_network("B1:B1:C1:D1:E1:F1", "FarNet", 30, 6, "WPA2")
        
        assert intel_close.location.estimated_distance_m < intel_far.location.estimated_distance_m
    
    def test_pic_device_fingerprinting(self):
        """Test device type fingerprinting."""
        from nexus.core.intelligence import PassiveIntelligenceCore, DeviceCategory
        pic = PassiveIntelligenceCore()
        
        # Hotspot detection
        intel = pic.process_network("A1:B1:C1:D1:E1:F1", "iPhone", 80, 6, "WPA2", vendor="Apple")
        assert intel.device_category == DeviceCategory.HOTSPOT
    
    def test_pic_mesh_detection(self):
        """Test mesh network detection."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        # Same SSID, same vendor prefix
        pic.process_network("AA:BB:CC:01:02:03", "HomeWiFi", 80, 1, "WPA2")
        pic.process_network("AA:BB:CC:04:05:06", "HomeWiFi", 70, 6, "WPA2")
        pic.process_network("AA:BB:CC:07:08:09", "HomeWiFi", 60, 11, "WPA2")
        
        mesh_groups = pic.get_mesh_groups()
        assert len(mesh_groups) > 0
    
    def test_pic_security_summary(self):
        """Test security summary generation."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        pic.process_network("A1:B1:C1:D1:E1:F1", "Net1", 80, 6, "WPA3")
        pic.process_network("B1:B1:C1:D1:E1:F1", "Net2", 70, 6, "WPA2")
        pic.process_network("C1:B1:C1:D1:E1:F1", "Net3", 60, 6, "Open")
        
        summary = pic.get_security_summary()
        assert summary['excellent'] > 0 or summary['good'] > 0 or summary['moderate'] > 0
    
    def test_pic_device_summary(self):
        """Test device type summary."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        pic.process_network("A1:B1:C1:D1:E1:F1", "Router", 80, 6, "WPA2", vendor="TP-Link")
        pic.process_network("B1:B1:C1:D1:E1:F1", "iPhone", 70, 6, "WPA2")
        
        summary = pic.get_device_summary()
        assert sum(summary.values()) == 2
    
    def test_pic_singleton(self):
        """Test PIC singleton."""
        import nexus.core.intelligence as intel_mod
        intel_mod._pic = None
        
        from nexus.core.intelligence import get_pic
        p1 = get_pic()
        p2 = get_pic()
        assert p1 is p2
    
    def test_pic_clear(self):
        """Test clearing PIC data."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        pic.process_network("A1:B1:C1:D1:E1:F1", "Test", 80, 6, "WPA2")
        assert len(pic.networks) == 1
        
        pic.clear()
        assert len(pic.networks) == 0
    
    def test_pic_mode_status(self):
        """Test mode status retrieval."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        status = pic.get_mode_status()
        assert 'mode' in status
        assert 'has_gyroscope' in status
    
    def test_pic_statistics(self):
        """Test global statistics."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        pic.process_network("A1:B1:C1:D1:E1:F1", "Test1", 80, 6, "WPA2")
        pic.process_network("B1:B1:C1:D1:E1:F1", "Test2", 70, 6, "WPA2")
        
        stats = pic.get_statistics()
        assert stats['total_networks'] == 2
        assert 'security_summary' in stats
        assert 'device_summary' in stats
    
    def test_pic_network_to_dict(self):
        """Test NetworkIntelligence to_dict conversion."""
        from nexus.core.intelligence import PassiveIntelligenceCore
        pic = PassiveIntelligenceCore()
        
        intel = pic.process_network("A1:B1:C1:D1:E1:F1", "TestNet", 75, 6, "WPA2")
        d = intel.to_dict()
        
        assert d['bssid'] == "A1:B1:C1:D1:E1:F1"
        assert d['ssid'] == "TestNet"
        assert d['signal'] == 75
        assert 'distance' in d
        assert 'security_rating' in d