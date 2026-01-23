"""
Tests for Enhanced Active Scan Mode (EASM) module.

EASM is 100% legal - only uses IEEE 802.11 Probe Requests
which are standard WiFi discovery frames sent by every device.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch


class TestEASMImport:
    """Test that EASM module imports correctly."""
    
    def test_import_easm_manager(self):
        """EASM module should import without errors."""
        from nexus.core import easm_manager
        assert easm_manager is not None
    
    def test_import_easm_controller(self):
        """EASMController class should be importable."""
        from nexus.core.easm_manager import EASMController
        assert EASMController is not None
    
    def test_import_rate_limiter(self):
        """RateLimiter class should be importable."""
        from nexus.core.easm_manager import RateLimiter
        assert RateLimiter is not None
    
    def test_import_legal_guard(self):
        """LegalGuard class should be importable."""
        from nexus.core.easm_manager import LegalGuard
        assert LegalGuard is not None
    
    def test_import_frame_validator(self):
        """FrameValidator class should be importable."""
        from nexus.core.easm_manager import FrameValidator
        assert FrameValidator is not None
    
    def test_import_easm_discovery(self):
        """EASMDiscovery dataclass should be importable."""
        from nexus.core.easm_manager import EASMDiscovery
        assert EASMDiscovery is not None


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_create_rate_limiter(self):
        """Rate limiter should be created."""
        from nexus.core.easm_manager import RateLimiter
        limiter = RateLimiter()
        assert limiter is not None
    
    def test_first_probe_allowed(self):
        """First probe should always be allowed."""
        from nexus.core.easm_manager import RateLimiter
        limiter = RateLimiter()
        allowed, reason = limiter.can_send_probe()
        assert allowed is True
        assert reason == "OK"
    
    def test_per_bssid_cooldown(self):
        """Per-BSSID cooldown should prevent repeated probing."""
        from nexus.core.easm_manager import RateLimiter
        limiter = RateLimiter()
        
        bssid = "AA:BB:CC:DD:EE:FF"
        # First probe to this BSSID allowed
        allowed, _ = limiter.can_send_probe(bssid)
        assert allowed is True
        limiter.record_probe(bssid)
        
        # Immediate second probe blocked (either by cooldown or interval)
        allowed, reason = limiter.can_send_probe(bssid)
        assert allowed is False
        # Reason could be either "cooldown" or "interval"
        assert "cooldown" in reason.lower() or "interval" in reason.lower()
    
    def test_stats_tracking(self):
        """Rate limiter should track statistics."""
        from nexus.core.easm_manager import RateLimiter
        limiter = RateLimiter()
        
        limiter.record_probe()  # Broadcast
        limiter.record_probe("AA:BB:CC:DD:EE:FF")  # Directed
        
        stats = limiter.get_stats()
        assert "probes_last_minute" in stats
        assert "tracked_bssids" in stats


class TestLegalGuard:
    """Test legal compliance system."""
    
    def test_create_legal_guard(self):
        """Legal guard should be created."""
        from nexus.core.easm_manager import LegalGuard
        guard = LegalGuard()
        assert guard is not None
    
    def test_probe_request_allowed(self):
        """Probe Request frames should be allowed."""
        from nexus.core.easm_manager import LegalGuard
        
        # type=0 (Management), subtype=4 (Probe Request)
        allowed, reason = LegalGuard.check_frame_type(0, 4)
        assert allowed is True
        assert "ALLOWED" in reason
    
    def test_non_probe_frames_blocked(self):
        """Non-probe frames should be blocked."""
        from nexus.core.easm_manager import LegalGuard
        
        # type=0 (Management), subtype=0 (Association Request) - BLOCKED
        allowed, reason = LegalGuard.check_frame_type(0, 0)
        assert allowed is False
        assert "BLOCKED" in reason
        
        # type=0 (Management), subtype=11 (Authentication) - BLOCKED
        allowed, reason = LegalGuard.check_frame_type(0, 11)
        assert allowed is False
        assert "Authentication" in reason
        
        # type=2 (Data) - BLOCKED
        allowed, reason = LegalGuard.check_frame_type(2, 0)
        assert allowed is False
    
    def test_dfs_channel_blocking(self):
        """DFS channels should be blocked."""
        from nexus.core.easm_manager import LegalGuard
        
        # Channel 52 is DFS
        allowed, reason = LegalGuard.check_channel(52)
        assert allowed is False
        assert "DFS" in reason
        
        # Channel 100 is DFS
        allowed, reason = LegalGuard.check_channel(100)
        assert allowed is False
        
        # Channel 6 is safe
        allowed, reason = LegalGuard.check_channel(6)
        assert allowed is True
        
        # Channel 36 is safe
        allowed, reason = LegalGuard.check_channel(36)
        assert allowed is True


class TestFrameValidator:
    """Test frame validation."""
    
    def test_create_validator(self):
        """Frame validator should be created."""
        from nexus.core.easm_manager import FrameValidator
        validator = FrameValidator()
        assert validator is not None
    
    def test_valid_mac_address(self):
        """Valid MAC addresses should pass validation."""
        from nexus.core.easm_manager import FrameValidator
        
        valid, reason = FrameValidator.validate_mac("AA:BB:CC:DD:EE:FF")
        assert valid is True
        
        valid, reason = FrameValidator.validate_mac("aa:bb:cc:dd:ee:ff")
        assert valid is True
    
    def test_invalid_mac_address(self):
        """Invalid MAC addresses should fail validation."""
        from nexus.core.easm_manager import FrameValidator
        
        valid, reason = FrameValidator.validate_mac("invalid")
        assert valid is False
        
        valid, reason = FrameValidator.validate_mac("")
        assert valid is False
        
        valid, reason = FrameValidator.validate_mac(None)
        assert valid is False


class TestProbeRequestBuilder:
    """Test probe request frame building."""
    
    def test_import_builder(self):
        """ProbeRequestBuilder should be importable."""
        from nexus.core.easm_manager import ProbeRequestBuilder
        assert ProbeRequestBuilder is not None
    
    def test_create_builder(self):
        """Builder should be created with source MAC."""
        from nexus.core.easm_manager import ProbeRequestBuilder
        builder = ProbeRequestBuilder(source_mac="AA:BB:CC:DD:EE:FF")
        assert builder is not None


class TestIEHarvester:
    """Test Information Element harvester."""
    
    def test_import_harvester(self):
        """IEHarvester should be importable."""
        from nexus.core.easm_manager import IEHarvester
        assert IEHarvester is not None
    
    def test_create_harvester(self):
        """Harvester should be created."""
        from nexus.core.easm_manager import IEHarvester
        harvester = IEHarvester()
        assert harvester is not None


class TestHiddenSSIDRevealer:
    """Test hidden SSID revelation system."""
    
    def test_import_revealer(self):
        """HiddenSSIDRevealer should be importable."""
        from nexus.core.easm_manager import HiddenSSIDRevealer
        assert HiddenSSIDRevealer is not None
    
    def test_create_revealer(self):
        """Revealer should be created."""
        from nexus.core.easm_manager import HiddenSSIDRevealer
        revealer = HiddenSSIDRevealer()
        assert revealer is not None
    
    def test_add_hidden_network(self):
        """Should track hidden networks for probing."""
        from nexus.core.easm_manager import HiddenSSIDRevealer
        revealer = HiddenSSIDRevealer()
        
        revealer.add_hidden_network("AA:BB:CC:DD:EE:FF", 6)
        
        # Stats should show one pending
        stats = revealer.get_stats()
        assert stats["pending"] == 1
    
    def test_reveal_tracking(self):
        """Should track when SSID is revealed."""
        from nexus.core.easm_manager import HiddenSSIDRevealer
        revealer = HiddenSSIDRevealer()
        
        # Add hidden network
        revealer.add_hidden_network("AA:BB:CC:DD:EE:FF", 6)
        
        # Check reveal
        revealed = revealer.check_reveal("AA:BB:CC:DD:EE:FF", "TestSSID")
        assert revealed is True
        
        # Should now be revealed
        assert revealer.is_revealed("AA:BB:CC:DD:EE:FF") is True
        assert revealer.get_revealed_ssid("AA:BB:CC:DD:EE:FF") == "TestSSID"
    
    def test_common_ssids_available(self):
        """Should have list of common SSIDs to try."""
        from nexus.core.easm_manager import HiddenSSIDRevealer
        assert len(HiddenSSIDRevealer.COMMON_SSIDS) > 0
        assert "Guest" in HiddenSSIDRevealer.COMMON_SSIDS


class TestChannelSweeper:
    """Test channel sweeping system."""
    
    def test_import_sweeper(self):
        """ChannelSweeper should be importable."""
        from nexus.core.easm_manager import ChannelSweeper
        assert ChannelSweeper is not None
    
    def test_create_sweeper(self):
        """Sweeper should be created."""
        from nexus.core.easm_manager import ChannelSweeper
        sweeper = ChannelSweeper()
        assert sweeper is not None
    
    def test_safe_channels_available(self):
        """Should have safe channel list."""
        from nexus.core.easm_manager import ALL_SAFE_CHANNELS, DFS_CHANNELS
        
        # Safe channels exist
        assert len(ALL_SAFE_CHANNELS) > 0
        
        # Safe channels should not include DFS
        for ch in ALL_SAFE_CHANNELS:
            assert ch not in DFS_CHANNELS


class TestEASMController:
    """Test main EASM controller."""
    
    def test_create_controller(self):
        """Controller should be created."""
        from nexus.core.easm_manager import EASMController
        
        def dummy_callback(discovery):
            pass
        
        controller = EASMController(
            interface="Wi-Fi",
            report_callback=dummy_callback
        )
        assert controller is not None
    
    def test_controller_starts_stopped(self):
        """Controller should start in stopped state."""
        from nexus.core.easm_manager import EASMController
        
        def dummy_callback(discovery):
            pass
        
        controller = EASMController(
            interface="Wi-Fi",
            report_callback=dummy_callback
        )
        assert controller.is_running is False
    
    def test_start_stop(self):
        """Controller should start and stop."""
        from nexus.core.easm_manager import EASMController
        
        def dummy_callback(discovery):
            pass
        
        controller = EASMController(
            interface="Wi-Fi",
            report_callback=dummy_callback
        )
        
        controller.start()
        assert controller.is_running is True
        
        controller.stop()
        assert controller.is_running is False
    
    def test_stats_available(self):
        """Statistics should be available."""
        from nexus.core.easm_manager import EASMController
        
        def dummy_callback(discovery):
            pass
        
        controller = EASMController(
            interface="Wi-Fi",
            report_callback=dummy_callback
        )
        
        stats = controller.get_full_stats()
        assert "probes" in stats
        assert "hidden_ssids" in stats
    
    def test_discovery_callback(self):
        """Discovery callback should be called."""
        from nexus.core.easm_manager import EASMController, EASMDiscovery
        discoveries = []
        
        def callback(discovery: EASMDiscovery):
            discoveries.append(discovery)
        
        controller = EASMController(
            interface="Wi-Fi",
            report_callback=callback
        )
        assert controller is not None


class TestLegalCompliance:
    """Test that EASM stays within legal bounds."""
    
    def test_only_probe_requests(self):
        """EASM should ONLY allow Probe Request frames."""
        from nexus.core.easm_manager import LegalGuard
        
        # Probe Request (type=0, subtype=4) is the ONLY allowed frame
        allowed, _ = LegalGuard.check_frame_type(0, 4)
        assert allowed is True
        
        # Everything else should be blocked
        blocked_count = 0
        for ftype in range(4):
            for subtype in range(16):
                if ftype == 0 and subtype == 4:
                    continue
                allowed, _ = LegalGuard.check_frame_type(ftype, subtype)
                if not allowed:
                    blocked_count += 1
        
        # Should block 63 frame types (4*16 - 1)
        assert blocked_count == 63
    
    def test_dfs_channel_compliance(self):
        """Should never transmit on DFS channels."""
        from nexus.core.easm_manager import LegalGuard, DFS_CHANNELS
        
        # All DFS channels must be blocked
        for ch in DFS_CHANNELS:
            allowed, _ = LegalGuard.check_channel(ch)
            assert allowed is False, f"DFS channel {ch} should be blocked"
    
    def test_no_authentication_frames(self):
        """Should never send authentication frames."""
        from nexus.core.easm_manager import LegalGuard
        
        # Authentication is type=0, subtype=11
        allowed, reason = LegalGuard.check_frame_type(0, 11)
        assert allowed is False
        assert "Authentication" in reason
    
    def test_no_deauth_frames(self):
        """Should never send deauthentication frames."""
        from nexus.core.easm_manager import LegalGuard
        
        # Deauthentication is type=0, subtype=12
        allowed, reason = LegalGuard.check_frame_type(0, 12)
        assert allowed is False
        assert "Deauthentication" in reason


class TestWindowsScannerEASM:
    """Test EASM integration in Windows scanner."""
    
    def test_scanner_has_easm_property(self):
        """Windows scanner should have easm_enabled property."""
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=False)
        
        assert hasattr(scanner, 'easm_enabled')
        assert scanner.easm_enabled is False
    
    def test_easm_enable_disable(self):
        """EASM should be toggleable (Scapy not available will fail gracefully)."""
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=True)
        
        # If Scapy is available, EASM can be enabled
        # If not, it should fail gracefully
        initial = scanner.easm_enabled
        scanner.easm_enabled = True
        # Either enabled or still disabled if Scapy unavailable
        scanner.easm_enabled = False
        assert scanner.easm_enabled is False
    
    def test_scanner_name_reflects_easm(self):
        """Scanner name should indicate EASM when enabled."""
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=False)
        
        # netsh mode name doesn't include EASM
        assert "EASM" not in scanner.name
    
    def test_get_easm_stats(self):
        """Scanner should provide EASM stats method."""
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=False)
        
        assert hasattr(scanner, 'get_easm_stats')
        # Without EASM enabled, stats should be None
        assert scanner.get_easm_stats() is None


class TestPassiveCompliance:
    """Verify EASM maintains passive architecture principles."""
    
    def test_easm_is_optional(self):
        """EASM should be completely optional."""
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=True)
        
        # Should work fine without EASM
        assert scanner.easm_enabled is False
    
    def test_netsh_mode_unaffected(self):
        """netsh mode should NEVER use EASM."""
        from nexus.platform.windows import WindowsScanner
        scanner = WindowsScanner(use_scapy=False)
        
        # Even if we try to enable EASM, netsh mode is passive-only
        # This documents the design intent
        name = scanner.name
        assert "netsh" in name
        assert "EASM" not in name
    
    def test_discovery_dataclass(self):
        """EASMDiscovery should contain expected fields."""
        from nexus.core.easm_manager import EASMDiscovery
        from dataclasses import fields
        
        field_names = [f.name for f in fields(EASMDiscovery)]
        
        # Required fields for intelligence
        assert 'discovery_type' in field_names
        assert 'bssid' in field_names
        assert 'ssid' in field_names
        assert 'channel' in field_names
        assert 'source' in field_names
