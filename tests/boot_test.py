"""
Quick boot test - run this to verify basic functionality.
"""

def main():
    print("=" * 60)
    print("Nexus WiFi Radar - Boot Test")
    print("=" * 60)
    
    errors = []
    
    # Test 1: Import main package
    print("\n[1/8] Importing nexus package...", end=" ")
    try:
        import nexus
        print(f"OK (v{nexus.__version__})")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("nexus import", e))
    
    # Test 2: Import models
    print("[2/8] Importing core models...", end=" ")
    try:
        from nexus.core.models import Network, Threat, ScanResult, SecurityType
        print("OK")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("models import", e))
    
    # Test 3: Import config
    print("[3/8] Importing config...", end=" ")
    try:
        from nexus.core.config import Config, get_config
        config = Config()
        print("OK")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("config import", e))
    
    # Test 4: Import vendor lookup
    print("[4/8] Importing vendor lookup...", end=" ")
    try:
        from nexus.core.vendor import lookup_vendor
        result = lookup_vendor("00:1C:B3:00:00:00")
        print(f"OK (test lookup: {result})")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("vendor import", e))
    
    # Test 5: Import platform scanners
    print("[5/8] Importing platform scanners...", end=" ")
    try:
        from nexus.platform.windows import WindowsScanner
        from nexus.platform.generic_linux import LinuxScanner
        from nexus.platform.raspberry_pi import PiScanner
        print("OK")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("platform import", e))
    
    # Test 6: Import security
    print("[6/8] Importing security modules...", end=" ")
    try:
        from nexus.security.detection import ThreatDetector
        from nexus.security.rules import get_default_rules
        rules = get_default_rules()
        print(f"OK ({len(rules)} rules loaded)")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("security import", e))
    
    # Test 7: Import audio
    print("[7/8] Importing audio module...", end=" ")
    try:
        from nexus.audio.sonar import SonarAudio, ToneGenerator
        # Generate a test tone (no playback)
        tone = ToneGenerator.generate_tone(440, 0.01, 0.1)
        print(f"OK ({len(tone)} bytes test tone)")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("audio import", e))
    
    # Test 8: Import UI (no window creation)
    print("[8/8] Importing UI modules...", end=" ")
    try:
        from nexus.ui.cli import main as cli_main
        from nexus.ui.radar import RadarView
        from nexus.ui.heatmap import HeatmapRenderer
        print("OK")
    except Exception as e:
        print(f"FAIL: {e}")
        errors.append(("ui import", e))
    
    # Test creating objects
    print("\n" + "-" * 60)
    print("Creating test objects...")
    
    try:
        from nexus.core.models import Network, ScanResult, SecurityType
        
        net = Network(
            ssid="TestNetwork",
            bssid="AA:BB:CC:DD:EE:FF",
            channel=6,
            frequency_mhz=2437,
            rssi_dbm=-55,
            security=SecurityType.WPA2,
        )
        print(f"  Network: {net.ssid} @ {net.signal_percent}% ({net.band})")
        
        result = ScanResult(networks=[net])
        print(f"  ScanResult: {result.network_count} networks")
        
        from nexus.security.detection import ThreatDetector
        detector = ThreatDetector()
        threats = detector.analyze(result)
        print(f"  ThreatDetector: {len(threats)} threats found")
        
    except Exception as e:
        print(f"  Object creation FAILED: {e}")
        errors.append(("object creation", e))
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"BOOT TEST FAILED - {len(errors)} error(s):")
        for name, err in errors:
            print(f"  - {name}: {err}")
        return 1
    else:
        print("BOOT TEST PASSED - All modules loaded successfully!")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
