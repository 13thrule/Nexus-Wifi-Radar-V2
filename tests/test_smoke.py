"""
Smoke tests - verify basic imports and module loading.
"""

import pytest


def test_import_nexus():
    """Test that the main nexus package imports."""
    import nexus
    assert hasattr(nexus, "__version__")
    assert nexus.__version__ == "0.2.0"


def test_import_models():
    """Test that core models import correctly."""
    from nexus.core.models import Network, Threat, ScanResult, SecurityType
    
    # Create a basic Network
    network = Network(
        ssid="TestNetwork",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        frequency_mhz=2437,
        rssi_dbm=-50,
    )
    
    assert network.ssid == "TestNetwork"
    assert network.signal_percent > 0
    assert network.band == "2.4GHz"


def test_import_config():
    """Test that config module imports."""
    from nexus.core.config import Config, ScanConfig, UIConfig
    
    config = Config()
    assert config.scan.timeout_seconds == 10
    assert config.ui.theme == "dark"


def test_import_vendor():
    """Test vendor lookup imports and works."""
    from nexus.core.vendor import lookup_vendor, VendorLookup
    
    # Test a known Apple MAC prefix
    vendor = lookup_vendor("00:1C:B3:12:34:56")
    assert vendor == "Apple"
    
    # Test unknown
    vendor = lookup_vendor("00:00:00:00:00:00")
    assert vendor == "Unknown"


def test_import_scanner():
    """Test scanner module imports."""
    from nexus.core.scan import Scanner, get_scanner
    
    # Scanner is abstract, just check it exists
    assert Scanner is not None


def test_import_platform_modules():
    """Test platform modules import."""
    from nexus.platform.windows import WindowsScanner
    from nexus.platform.generic_linux import LinuxScanner
    from nexus.platform.raspberry_pi import PiScanner
    
    assert WindowsScanner is not None
    assert LinuxScanner is not None
    assert PiScanner is not None


def test_import_security():
    """Test security modules import."""
    from nexus.security.detection import ThreatDetector
    from nexus.security.rules import get_default_rules
    from nexus.security.report import ReportGenerator
    
    detector = ThreatDetector()
    rules = get_default_rules()
    
    assert len(rules) >= 4
    assert detector is not None


def test_import_audio():
    """Test audio module imports."""
    from nexus.audio.sonar import SonarAudio, ToneGenerator
    
    # Test tone generation (doesn't play audio)
    tone = ToneGenerator.generate_tone(440, 0.1, 0.5)
    assert len(tone) > 0


def test_import_ui():
    """Test UI modules import (without creating windows)."""
    from nexus.ui.cli import main
    from nexus.ui.radar import RadarView
    from nexus.ui.heatmap import HeatmapRenderer
    
    assert main is not None
    assert RadarView is not None
    assert HeatmapRenderer is not None


def test_network_serialization():
    """Test Network to_dict and to_json."""
    from nexus.core.models import Network, SecurityType
    
    network = Network(
        ssid="TestNet",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=11,
        frequency_mhz=2462,
        rssi_dbm=-65,
        security=SecurityType.WPA2,
        vendor="TestVendor"
    )
    
    d = network.to_dict()
    assert d["ssid"] == "TestNet"
    assert d["security"] == "WPA2"
    assert "signal_percent" in d
    
    json_str = network.to_json()
    assert "TestNet" in json_str


def test_scan_result():
    """Test ScanResult functionality."""
    from nexus.core.models import Network, ScanResult
    
    networks = [
        Network("Net1", "AA:BB:CC:DD:EE:01", 1, 2412, -40),
        Network("Net2", "AA:BB:CC:DD:EE:02", 6, 2437, -60),
        Network("Net3", "AA:BB:CC:DD:EE:03", 11, 2462, -80),
    ]
    
    result = ScanResult(networks=networks)
    
    assert result.network_count == 3
    
    # Test sorting
    sorted_nets = result.get_networks_by_signal()
    assert sorted_nets[0].ssid == "Net1"  # Strongest
    
    # Test channel grouping
    by_channel = result.get_networks_by_channel()
    assert 1 in by_channel
    assert 6 in by_channel


def test_threat_detection():
    """Test basic threat detection."""
    from nexus.core.models import Network, ScanResult, SecurityType
    from nexus.security.detection import ThreatDetector
    
    # Create an open network (should trigger weak encryption rule)
    networks = [
        Network("OpenNet", "AA:BB:CC:DD:EE:01", 6, 2437, -50, SecurityType.OPEN),
        Network("SecureNet", "AA:BB:CC:DD:EE:02", 11, 2462, -60, SecurityType.WPA2),
    ]
    
    result = ScanResult(networks=networks)
    detector = ThreatDetector()
    threats = detector.analyze(result)
    
    # Should detect the open network
    assert len(threats) >= 1
    assert any("OpenNet" in t.description for t in threats)


def test_import_app():
    """Test that the main app module imports."""
    from nexus.app import NexusApp
    
    assert NexusApp is not None
    # Don't instantiate - would create a window


def test_import_server():
    """Test that server module imports."""
    from nexus.server import DashboardServer, FASTAPI_AVAILABLE
    
    assert DashboardServer is not None
    # FASTAPI_AVAILABLE is True or False depending on install


def test_cli_commands():
    """Test CLI command registration."""
    from nexus.ui.cli import (
        cmd_scan, cmd_continuous, cmd_list_scanners,
        cmd_config, cmd_gui, cmd_server
    )
    
    assert cmd_scan is not None
    assert cmd_continuous is not None
    assert cmd_list_scanners is not None
    assert cmd_config is not None
    assert cmd_gui is not None
    assert cmd_server is not None


def test_main_module():
    """Test that nexus can be run as module."""
    import nexus.__main__
    
    assert nexus.__main__ is not None
