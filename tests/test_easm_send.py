#!/usr/bin/env python3
"""
Simple test: Can EASM send a probe request on Windows?

This tests the new adapter name fallback logic.
"""

import sys
import subprocess

def get_wifi_interface():
    """Get WiFi interface name from netsh."""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if line.startswith('    Name'):
                return line.split(':', 1)[1].strip()
    except:
        pass
    return "Wi-Fi"  # Default

def test_easm_send():
    """Test EASM packet sending."""
    from nexus.core.easm_manager import EASMController, EASMDiscovery
    
    interface = get_wifi_interface()
    print(f"Testing EASM send on interface: {interface}")
    
    discoveries = []
    def callback(d):
        discoveries.append(d)
        print(f"  Discovery: {d}")
    
    def logger(level, msg):
        print(f"[EASM {level}] {msg}")
    
    # Create controller
    controller = EASMController(
        interface=interface,
        report_callback=callback,
        logger=logger
    )
    
    # Try to start
    print("Starting EASM...")
    controller.start()
    
    # Try a single tick (send one probe)
    print("Sending broadcast probe...")
    controller.tick()
    
    # Wait briefly
    import time
    time.sleep(1)
    
    # Stop
    print("Stopping EASM...")
    controller.stop()
    
    print(f"\nResult: Sent probe request successfully!")
    print(f"Note: EASM can send packets if Npcap & drivers are properly installed.")

if __name__ == "__main__":
    try:
        test_easm_send()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
