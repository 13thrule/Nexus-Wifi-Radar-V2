"""
Command-line interface for Nexus WiFi Radar.

Provides CLI commands for scanning, viewing, and exporting WiFi data.
"""

import argparse
import sys
import json
import time
from datetime import datetime
from typing import Optional

from nexus.core.scan import get_scanner, get_available_scanners
from nexus.core.config import Config, get_config
from nexus.core.models import ScanResult


def cmd_scan(args) -> int:
    """Perform a WiFi scan."""
    try:
        scanner = get_scanner(prefer_scapy=not args.no_scapy)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Extended scan mode for weak signals
    timeout = args.timeout
    if hasattr(args, 'weak') and args.weak:
        timeout = max(timeout, 30.0)  # Minimum 30s for extended scan
        print(f"[EXTENDED SCAN MODE] Scanning for weak signals...")
    
    print(f"Using scanner: {scanner.name}")
    print(f"Scanning for {timeout} seconds...\n")
    
    result = scanner.scan(timeout=timeout)
    
    # Filter by minimum signal strength
    min_signal = getattr(args, 'min_signal', -90)
    if min_signal > -90:
        original_count = len(result.networks)
        result.networks = [n for n in result.networks if n.rssi_dbm >= min_signal]
        if original_count != len(result.networks):
            print(f"Filtered {original_count - len(result.networks)} networks below {min_signal} dBm\n")
    
    if args.json:
        print(result.to_json())
    elif args.csv:
        print(result.to_csv())
    else:
        _print_scan_result(result, verbose=args.verbose, highlight_weak=getattr(args, 'weak', False))
    
    return 0


def cmd_continuous(args) -> int:
    """Perform continuous scanning."""
    try:
        scanner = get_scanner(prefer_scapy=not args.no_scapy)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    print(f"Using scanner: {scanner.name}")
    print(f"Scanning every {args.interval} seconds (Ctrl+C to stop)...\n")
    
    try:
        for result in scanner.scan_continuous(interval=args.interval):
            if args.clear:
                print("\033[2J\033[H", end="")  # Clear screen
            
            _print_scan_result(result, verbose=args.verbose)
            print("-" * 60)
    except KeyboardInterrupt:
        print("\nStopped.")
    
    return 0


def cmd_list_scanners(args) -> int:
    """List available scanners."""
    scanners = get_available_scanners()
    
    if not scanners:
        print("No WiFi scanners available on this system.")
        return 1
    
    print("Available scanners:\n")
    for scanner in scanners:
        status = "✓" if scanner.is_available() else "✗"
        print(f"  {status} {scanner.name}")
        print(f"    Platform: {scanner.platform}")
        print()
    
    return 0


def cmd_config(args) -> int:
    """View or modify configuration."""
    config = get_config()
    
    if args.show:
        print(json.dumps(config.to_dict(), indent=2))
    elif args.reset:
        config.reset()
        config.save()
        print("Configuration reset to defaults.")
    elif args.set:
        # Parse key=value
        try:
            key, value = args.set.split("=", 1)
            parts = key.split(".")
            
            if len(parts) != 2:
                print(f"Error: Invalid key format. Use section.key=value", file=sys.stderr)
                return 1
            
            section, setting = parts
            section_obj = getattr(config, section, None)
            
            if section_obj is None:
                print(f"Error: Unknown section: {section}", file=sys.stderr)
                return 1
            
            if not hasattr(section_obj, setting):
                print(f"Error: Unknown setting: {setting}", file=sys.stderr)
                return 1
            
            # Convert value to appropriate type
            current = getattr(section_obj, setting)
            if isinstance(current, bool):
                value = value.lower() in ("true", "1", "yes")
            elif isinstance(current, int):
                value = int(value)
            elif isinstance(current, float):
                value = float(value)
            
            setattr(section_obj, setting, value)
            config.save()
            print(f"Set {key} = {value}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        print("Use --show to view config, --set key=value to modify, --reset to reset")
    
    return 0


def cmd_gui(args) -> int:
    """Launch the GUI application."""
    try:
        from nexus.app import NexusApp
        
        app = NexusApp()
        app.run()
        return 0
    except ImportError as e:
        print(f"Error: GUI dependencies not available: {e}", file=sys.stderr)
        return 1


def cmd_server(args) -> int:
    """Run the dashboard server."""
    try:
        from nexus.server import DashboardServer, FASTAPI_AVAILABLE
        
        if not FASTAPI_AVAILABLE:
            print("Error: FastAPI not installed. Run: pip install fastapi uvicorn", file=sys.stderr)
            return 1
        
        print(f"Starting Nexus WiFi Radar Dashboard on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop\n")
        
        server = DashboardServer(host=args.host, port=args.port)
        server.run()
        return 0
    except ImportError as e:
        print(f"Error: Server dependencies not available: {e}", file=sys.stderr)
        print("Run: pip install fastapi uvicorn")
        return 1


def _print_scan_result(result: ScanResult, verbose: bool = False, highlight_weak: bool = False) -> None:
    """Print scan result in human-readable format."""
    print(f"Scan completed at {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Networks found: {result.network_count}\n")
    
    if not result.networks:
        print("No networks found.")
        return
    
    # Sort by signal strength
    networks = result.get_networks_by_signal()
    
    # Count weak signals
    weak_count = sum(1 for n in networks if n.rssi_dbm < -75)
    if highlight_weak and weak_count > 0:
        print(f"📡 Weak signals detected: {weak_count} networks below -75 dBm\n")
    
    # Header
    if verbose:
        print(f"{'SSID':<25} {'BSSID':<18} {'CH':<4} {'Signal':<12} {'Security':<12} {'Vendor':<15}")
        print("-" * 95)
    else:
        print(f"{'SSID':<30} {'Signal':<12} {'CH':<4} {'Security':<12}")
        print("-" * 65)
    
    for n in networks:
        ssid = n.ssid[:24] if n.ssid else "<Hidden>"
        
        # Signal display with weak indicator
        signal_str = f"{n.signal_percent}% ({n.rssi_dbm}dBm)"
        if highlight_weak and n.rssi_dbm < -75:
            signal_str = f"⚠️{signal_str}"  # Weak signal marker
        elif highlight_weak and n.rssi_dbm < -85:
            signal_str = f"🔻{signal_str}"  # Very weak signal marker
        
        if verbose:
            print(f"{ssid:<25} {n.bssid:<18} {n.channel:<4} {signal_str:<12} {n.security.value:<12} {n.vendor:<15}")
        else:
            print(f"{ssid:<30} {signal_str:<12} {n.channel:<4} {n.security.value:<12}")
    
    # Signal strength legend when highlighting weak
    if highlight_weak:
        print("\n" + "-" * 65)
        print("Signal Legend: ⚠️ = Weak (<-75dBm)  🔻 = Very Weak (<-85dBm)")


def main(argv: Optional[list] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="nexus",
        description="Nexus WiFi Radar - WiFi scanner and security analyzer"
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.2.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # scan command
    scan_parser = subparsers.add_parser("scan", help="Perform a WiFi scan")
    scan_parser.add_argument(
        "-t", "--timeout", type=float, default=10.0,
        help="Scan timeout in seconds (default: 10)"
    )
    scan_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show detailed output"
    )
    scan_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    scan_parser.add_argument(
        "--csv", action="store_true",
        help="Output as CSV"
    )
    scan_parser.add_argument(
        "--no-scapy", action="store_true",
        help="Disable Scapy packet capture"
    )
    scan_parser.add_argument(
        "--weak", "--show-weak", action="store_true",
        help="Extended scan mode to detect weaker signals (30s timeout)"
    )
    scan_parser.add_argument(
        "--min-signal", type=int, default=-90,
        help="Minimum signal strength in dBm to display (default: -90)"
    )
    scan_parser.set_defaults(func=cmd_scan)
    
    # continuous command
    cont_parser = subparsers.add_parser("continuous", help="Continuous scanning")
    cont_parser.add_argument(
        "-i", "--interval", type=float, default=5.0,
        help="Interval between scans (default: 5s)"
    )
    cont_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show detailed output"
    )
    cont_parser.add_argument(
        "--clear", action="store_true",
        help="Clear screen between scans"
    )
    cont_parser.add_argument(
        "--no-scapy", action="store_true",
        help="Disable Scapy packet capture"
    )
    cont_parser.set_defaults(func=cmd_continuous)
    
    # list-scanners command
    list_parser = subparsers.add_parser("list-scanners", help="List available scanners")
    list_parser.set_defaults(func=cmd_list_scanners)
    
    # config command
    config_parser = subparsers.add_parser("config", help="View or modify configuration")
    config_parser.add_argument(
        "--show", action="store_true",
        help="Show current configuration"
    )
    config_parser.add_argument(
        "--set", metavar="KEY=VALUE",
        help="Set a configuration value (e.g., scan.timeout_seconds=15)"
    )
    config_parser.add_argument(
        "--reset", action="store_true",
        help="Reset configuration to defaults"
    )
    config_parser.set_defaults(func=cmd_config)
    
    # gui command
    gui_parser = subparsers.add_parser("gui", help="Launch GUI application")
    gui_parser.add_argument(
        "--scan", action="store_true",
        help="Perform initial scan on launch"
    )
    gui_parser.set_defaults(func=cmd_gui)
    
    # server command
    server_parser = subparsers.add_parser("server", help="Launch web dashboard server")
    server_parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    server_parser.add_argument(
        "-p", "--port", type=int, default=8080,
        help="Port to listen on (default: 8080)"
    )
    server_parser.set_defaults(func=cmd_server)
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
