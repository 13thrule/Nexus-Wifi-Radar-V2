"""
Windows WiFi scanner implementation.

Uses netsh for basic scanning and optionally Scapy for packet capture.

EASM Integration (Scapy mode only):
===================================
When EASM is enabled, the Scapy scanner extends passive beacon reception
with legal active scanning:
- Broadcast probe requests (standard WiFi discovery)
- Directed probe requests (hidden SSID reveal)
- IE harvesting from probe responses
- Rate-limited and safety-checked transmissions

EASM does NOT affect netsh mode (passive only, always).
"""

import re
import subprocess
import time
import threading
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from queue import Queue, Empty

from nexus.core.scan import Scanner
from nexus.core.models import Network, ScanResult, SecurityType
from nexus.core.vendor import lookup_vendor
from nexus.core.logging import get_logger

logger = get_logger(__name__)


def _detect_builtin_wifi_adapter() -> Optional[str]:
    """
    Detect built-in WiFi adapter on Windows (prefer over USB).
    
    Returns adapter name if found, else None.
    Built-in adapters are usually more reliable with Scapy than USB dongles.
    """
    try:
        import subprocess
        import json
        
        # Use PowerShell to list WiFi adapters
        ps_cmd = """
$adapters = @();
Get-NetAdapter -Physical | Where-Object {
    ($_.InterfaceDescription -like '*wi-fi*' -or 
     $_.InterfaceDescription -like '*wireless*' -or 
     $_.InterfaceDescription -like '*802.11*') -and
    $_.Status -eq 'Up'
} | ForEach-Object {
    $adapters += @{
        name=$_.Name; 
        description=$_.InterfaceDescription; 
        isUSB=$_.InterfaceDescription -like '*USB*';
        isBuiltIn=$_.InterfaceDescription -notlike '*USB*'
    }
};
$adapters | ConvertTo-Json -Compress
"""
        
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if proc.returncode == 0 and proc.stdout.strip():
            adapters = json.loads(proc.stdout)
            if not isinstance(adapters, list):
                adapters = [adapters]
            
            # Prefer built-in adapters over USB
            builtin = [a for a in adapters if a.get('isBuiltIn')]
            if builtin:
                return builtin[0]['name']
            
            # Fall back to USB if no built-in
            usb = [a for a in adapters if a.get('isUSB')]
            if usb:
                return usb[0]['name']
            
            # Fall back to any WiFi adapter
            if adapters:
                return adapters[0]['name']
    
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        logger.warning(f"WiFi adapter detection failed: {e}")

    return None


# =============================================================================
# SCAPY ADAPTER DIAGNOSTICS
# =============================================================================

class ScapyDiagnostics:
    """
    Diagnose Scapy/Npcap/adapter capabilities on Windows.
    
    This class performs robust checks to determine if Scapy can work
    with the available network adapters without hanging.
    """
    
    def __init__(self):
        self.scapy_available = False
        self.npcap_installed = False
        self.npcap_version = None
        self.adapters: List[Dict] = []
        self.selected_adapter = None
        self.monitor_mode_supported = False
        self.raw_802_11_supported = False
        self.last_error = None
        self._checked = False
    
    def run_diagnostics(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Run full diagnostics with timeout protection.
        
        Returns a dict with diagnostic results.
        On Windows, we skip monitor-mode checks and focus on:
        - Scapy import availability
        - Npcap installation
        - Adapter visibility via netsh
        - Passive beacon capture capability
        """
        result = {
            'scapy_available': False,
            'npcap_installed': False,
            'npcap_version': None,
            'adapters': [],
            'selected_adapter': None,
            'monitor_mode': False,  # Windows rarely supports true monitor mode
            'raw_802_11': False,
            'can_sniff': False,  # Will be True if Npcap + adapter is available
            'errors': []
        }
        
        # Check imports and Npcap quickly (no timeout needed for imports)
        self._check_scapy_import(result)
        if result['scapy_available']:
            self._check_npcap(result)
            # Enumerate adapters with timeout protection
            self._enumerate_adapters(result)
            self._check_adapter_capabilities(result)
        
        return result
    
    def _check_scapy_import(self, result: Dict):
        """Check if Scapy can be imported."""
        try:
            import scapy
            result['scapy_available'] = True
            self.scapy_available = True
        except ImportError as e:
            result['errors'].append(f"Scapy import failed: {e}")
            self.last_error = str(e)
    
    def _check_npcap(self, result: Dict):
        """Check if Npcap is installed and get version."""
        try:
            # Check registry for Npcap
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\Npcap")
                result['npcap_installed'] = True
                self.npcap_installed = True
                winreg.CloseKey(key)
            except WindowsError:
                # Try WOW64 path
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\WOW6432Node\Npcap")
                    result['npcap_installed'] = True
                    self.npcap_installed = True
                    winreg.CloseKey(key)
                except WindowsError:
                    result['errors'].append("Npcap not found in registry")
            
            # Check Npcap DLL exists
            import os
            npcap_paths = [
                r"C:\Windows\System32\Npcap\wpcap.dll",
                r"C:\Windows\SysWOW64\Npcap\wpcap.dll"
            ]
            for path in npcap_paths:
                if os.path.exists(path):
                    result['npcap_installed'] = True
                    self.npcap_installed = True
                    break
                    
        except Exception as e:
            result['errors'].append(f"Npcap check failed: {e}")
    
    def _enumerate_adapters(self, result: Dict):
        """Enumerate network adapters visible to Scapy (with timeout protection)."""
        def _enum_with_timeout():
            try:
                # Use netsh for adapter enumeration instead of Scapy (no hanging)
                import subprocess
                ps_cmd = """
$adapters = @();
Get-NetAdapter -Physical | Where-Object {$_.InterfaceDescription -like '*wi-fi*' -or $_.InterfaceDescription -like '*wireless*' -or $_.InterfaceDescription -like '*802.11*'} | ForEach-Object {
    $adapters += @{name=$_.Name; description=$_.InterfaceDescription; status=$_.Status}
};
$adapters | ConvertTo-Json
"""
                proc = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                if proc.returncode == 0 and proc.stdout.strip():
                    import json
                    try:
                        adapters = json.loads(proc.stdout)
                        if not isinstance(adapters, list):
                            adapters = [adapters]
                        
                        for adapter in adapters:
                            adapter_info = {
                                'name': adapter.get('name', 'Unknown'),
                                'description': adapter.get('description', ''),
                                'guid': '',
                                'mac': '',
                                'ips': [],
                                'is_wifi': True,
                                'is_usb': 'usb' in adapter.get('description', '').lower()
                            }
                            result['adapters'].append(adapter_info)
                            self.adapters.append(adapter_info)
                        return
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: just report Wi-Fi as available
                result['adapters'].append({
                    'name': 'Wi-Fi',
                    'description': 'Windows Wi-Fi Adapter',
                    'guid': '',
                    'mac': '',
                    'ips': [],
                    'is_wifi': True,
                    'is_usb': False
                })
                
            except subprocess.TimeoutExpired:
                result['errors'].append("PowerShell adapter query timed out")
                result['adapters'].append({'name': 'Wi-Fi', 'description': 'Windows Wi-Fi Adapter', 'is_wifi': True, 'is_usb': False})
            except Exception as e:
                result['errors'].append(f"Adapter enumeration failed: {e}")
                result['adapters'].append({'name': 'Wi-Fi', 'description': 'Windows Wi-Fi Adapter', 'is_wifi': True, 'is_usb': False})
        
        # Run in thread to prevent hanging
        import threading
        enum_thread = threading.Thread(target=_enum_with_timeout, daemon=True)
        enum_thread.start()
        enum_thread.join(timeout=4)
        
        if enum_thread.is_alive():
            result['errors'].append("Adapter enumeration timed out")
            result['adapters'].append({'name': 'Wi-Fi', 'description': 'Windows Wi-Fi Adapter', 'is_wifi': True, 'is_usb': False})
    
    def _check_adapter_capabilities(self, result: Dict):
        """Check if any adapter supports monitor mode or raw 802.11."""
        # On Windows, true monitor mode is rare
        # Most adapters only support managed mode with Npcap
        
        wifi_adapters = [a for a in result['adapters'] if a['is_wifi']]
        
        if not wifi_adapters:
            result['errors'].append("No WiFi adapters found")
            return
        
        # Select first WiFi adapter (prefer USB for external)
        usb_wifi = [a for a in wifi_adapters if a['is_usb']]
        result['selected_adapter'] = usb_wifi[0] if usb_wifi else wifi_adapters[0]
        self.selected_adapter = result['selected_adapter']
        
        # On Windows with Npcap, raw 802.11 capture is limited
        # We can't easily detect monitor mode support without trying
        # Mark as potentially available if Npcap is installed
        if result['npcap_installed']:
            result['raw_802_11'] = True
            self.raw_802_11_supported = True
            result['can_sniff'] = True


# =============================================================================
# SAFE SCAPY SNIFFER
# =============================================================================

class SafeScapySniffer:
    """
    Thread-safe Scapy sniffer with timeout and stop conditions.
    
    Prevents UI freezing by running sniff in a separate thread
    with proper timeout handling.
    """
    
    def __init__(self, interface: str = None, logger: Callable = None):
        self._interface = interface
        self._logger = logger or (lambda lvl, msg: print(f"[Scapy {lvl}] {msg}"))
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._packets: List = []
        self._packet_callback: Optional[Callable] = None
        self._stop_event = threading.Event()
        self._error: Optional[str] = None
        self._initialized = False
        self._init_lock = threading.Lock()
    
    def initialize(self, timeout: float = 5.0) -> bool:
        """
        Initialize Scapy sniffer with timeout protection.
        
        Returns True if initialization succeeded.
        """
        with self._init_lock:
            if self._initialized:
                return True
            
            init_queue = Queue()
            
            def _init():
                try:
                    # Import Scapy components
                    from scapy.all import conf, sniff
                    
                    # Configure Scapy for Windows
                    conf.use_pcap = True
                    
                    # If we have an interface, try to validate it
                    if self._interface:
                        from scapy.arch.windows import get_windows_if_list
                        adapters = get_windows_if_list()
                        found = any(
                            self._interface.lower() in str(a.get('name', '')).lower() or
                            self._interface.lower() in str(a.get('description', '')).lower()
                            for a in adapters
                        )
                        if not found:
                            self._logger("WARN", f"Interface '{self._interface}' not found in Scapy adapter list")
                    
                    init_queue.put(('ok', None))
                    
                except Exception as e:
                    init_queue.put(('error', str(e)))
            
            thread = threading.Thread(target=_init, daemon=True)
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                self._error = "Scapy initialization timed out"
                self._logger("ERROR", self._error)
                return False
            
            try:
                status, error = init_queue.get_nowait()
                if status == 'ok':
                    self._initialized = True
                    self._logger("INFO", "Scapy sniffer initialized successfully")
                    return True
                else:
                    self._error = error
                    self._logger("ERROR", f"Scapy init failed: {error}")
                    return False
            except Empty:
                self._error = "No init response"
                return False
    
    def start_sniff(self, packet_callback: Callable, timeout: float = 10.0) -> bool:
        """
        Start sniffing in a background thread.
        
        Args:
            packet_callback: Function to call for each packet
            timeout: Maximum sniff duration in seconds
            
        Returns:
            True if sniffing started successfully
        """
        if self._running:
            return True
        
        if not self._initialized and not self.initialize():
            return False
        
        self._packet_callback = packet_callback
        self._stop_event.clear()
        self._packets.clear()
        self._error = None
        
        def _sniff_thread():
            try:
                from scapy.all import sniff, Dot11
                
                self._running = True
                self._logger("INFO", f"Starting sniff (timeout={timeout}s)")
                
                def stop_filter(pkt):
                    return self._stop_event.is_set()
                
                # Use lfilter to only capture 802.11 frames if possible
                sniff(
                    iface=self._interface,
                    prn=self._handle_packet,
                    timeout=timeout,
                    store=False,
                    stop_filter=stop_filter
                )
                
                self._logger("INFO", f"Sniff completed, captured {len(self._packets)} packets")
                
            except Exception as e:
                self._error = str(e)
                self._logger("ERROR", f"Sniff error: {e}")
            finally:
                self._running = False
        
        self._thread = threading.Thread(target=_sniff_thread, daemon=True)
        self._thread.start()
        return True
    
    def _handle_packet(self, packet):
        """Internal packet handler."""
        self._packets.append(packet)
        if self._packet_callback:
            try:
                self._packet_callback(packet)
            except Exception as e:
                self._logger("ERROR", f"Packet callback error: {e}")
    
    def stop(self):
        """Stop sniffing."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._running = False
    
    def is_running(self) -> bool:
        """Check if sniffer is running."""
        return self._running
    
    def get_error(self) -> Optional[str]:
        """Get last error message."""
        return self._error
    
    def get_packets(self) -> List:
        """Get captured packets."""
        return list(self._packets)


# =============================================================================
# WINDOWS SCANNER
# =============================================================================

class WindowsScanner(Scanner):
    """
    Windows-specific WiFi scanner.
    
    Supports two modes:
    - netsh: Uses 'netsh wlan show networks' command (no admin required)
    - scapy: Uses packet capture for more detailed info (requires Npcap)
    
    EASM (Enhanced Active Scan Mode):
    - Only available in Scapy mode
    - Controlled by easm_enabled property
    - Sends legal IEEE 802.11 probe requests
    - Rate-limited and safety-checked
    """
    
    def __init__(self, use_scapy: bool = True):
        """
        Initialize Windows scanner.
        
        Args:
            use_scapy: If True, prefer Scapy packet capture when available.
                      NOTE: On Windows with USB adapters, Scapy may hang.
                      Set to False to use netsh (always works, passive only).
        """
        self._use_scapy = use_scapy and False  # Disable Scapy by default - it hangs on Windows USB adapters
        self._scapy_available = False  # Don't even check - known to hang
        self._scapy_diagnostics: Optional[Dict] = None
        self._scapy_sniffer: Optional[SafeScapySniffer] = None
        self._scapy_checked = False
        
        # EASM state (only affects Scapy mode)
        self._easm_enabled = False
        self._easm_controller = None
        self._easm_pending = False  # Lazy init flag
        self._easm_discoveries: List[Dict] = []
        
        # Try to detect built-in WiFi adapter (more reliable than USB with Scapy)
        detected_adapter = _detect_builtin_wifi_adapter()
        self._interface_name = detected_adapter or "Wi-Fi"  # Use detected or default
        
        if detected_adapter:
            logger.info(f"Detected WiFi adapter: {detected_adapter}")

        # Log scanner mode
        logger.info("Using netsh mode (reliable, always passive)")
        logger.info("EASM (packet injection) disabled on Windows - use Linux for active scanning")
    
    def _quick_scapy_check(self) -> bool:
        """Quick check if Scapy is importable (no network operations)."""
        try:
            import scapy
            return True
        except ImportError:
            return False
    
    def _run_scapy_diagnostics(self) -> Dict:
        """Run full Scapy diagnostics (with timeout protection)."""
        if self._scapy_diagnostics is not None:
            return self._scapy_diagnostics

        logger.info("Running Scapy diagnostics...")
        diag = ScapyDiagnostics()
        self._scapy_diagnostics = diag.run_diagnostics(timeout=5.0)

        # Log results
        d = self._scapy_diagnostics
        logger.info(f"Scapy available: {d['scapy_available']}")
        logger.info(f"Npcap installed: {d['npcap_installed']}")
        logger.info(f"Adapters found: {len(d['adapters'])}")

        if d['selected_adapter']:
            logger.info(f"Selected adapter: {d['selected_adapter']['description']}")
            self._interface_name = d['selected_adapter'].get('name', 'Wi-Fi')

        if d['errors']:
            for err in d['errors']:
                logger.warning(f"Diagnostic warning: {err}")

        logger.info(f"Can sniff: {d['can_sniff']}")

        return self._scapy_diagnostics
    
    def _init_scapy_sniffer(self) -> bool:
        """Initialize the safe Scapy sniffer."""
        if self._scapy_sniffer is not None:
            return True
        
        # Run diagnostics first
        diag = self._run_scapy_diagnostics()
        
        if not diag['can_sniff']:
            logger.warning("Cannot initialize Scapy sniffer - diagnostics failed")
            return False
        
        # Create sniffer with detected interface
        interface = self._interface_name
        if diag['selected_adapter']:
            interface = diag['selected_adapter'].get('name', interface)
        
        self._scapy_sniffer = SafeScapySniffer(
            interface=interface,
            logger=lambda lvl, msg: print(f"[Scapy {lvl}] {msg}")
        )
        
        # Try to initialize
        if not self._scapy_sniffer.initialize(timeout=5.0):
            logger.error(f"Scapy sniffer init failed: {self._scapy_sniffer.get_error()}")
            self._scapy_sniffer = None
            return False

        logger.info("Scapy sniffer ready")
        return True
    
    @property
    def easm_enabled(self) -> bool:
        """Check if EASM is enabled."""
        return self._easm_enabled
    
    @easm_enabled.setter
    def easm_enabled(self, value: bool):
        """Enable or disable EASM."""
        if value:
            # Scapy packet injection doesn't work reliably on Windows with USB WiFi adapters
            # This is a known Scapy limitation — sniff() and sendp() hang or fail
            logger.info("EASM cannot enable on Windows - Scapy packet injection not supported with USB adapters")
            self._easm_enabled = False
            return

        self._easm_enabled = False
        if self._easm_controller:
            self._stop_easm()
    
    def _init_easm(self):
        """Initialize EASM controller (lazy - actual init happens on first scan)."""
        # Just mark as pending - actual init happens in scan thread
        self._easm_pending = True
        logger.info("EASM Enhanced Active Scan Mode ARMED (will initialize on next scan)")
    
    def _init_easm_real(self):
        """Actually initialize EASM controller (called from scan thread)."""
        if self._easm_controller is not None:
            return True
        
        if not getattr(self, '_easm_pending', False):
            return False
        
        try:
            from nexus.core.easm_manager import EASMController, EASMDiscovery
            
            def easm_callback(discovery: 'EASMDiscovery'):
                """Handle EASM discoveries."""
                self._easm_discoveries.append({
                    'type': discovery.discovery_type,
                    'bssid': discovery.bssid,
                    'ssid': discovery.ssid,
                    'channel': discovery.channel,
                    'rssi_dbm': discovery.rssi_dbm,
                    'capabilities': discovery.capabilities,
                    'source': discovery.source,
                    'timestamp': discovery.timestamp
                })
            
            self._easm_controller = EASMController(
                interface=self._interface_name,
                report_callback=easm_callback,
                logger=self._easm_log
            )
            self._easm_controller.start()
            self._easm_pending = False
            logger.info("EASM Enhanced Active Scan Mode INITIALIZED")
            return True

        except ImportError as e:
            logger.error(f"EASM failed to import EASM module: {e}")
            self._easm_enabled = False
            self._easm_pending = False
            return False
        except Exception as e:
            logger.error(f"EASM failed to initialize: {e}")
            self._easm_enabled = False
            self._easm_pending = False
            return False
    
    def _stop_easm(self):
        """Stop EASM controller."""
        if self._easm_controller:
            self._easm_controller.stop()
            self._easm_controller = None
            logger.info("EASM Enhanced Active Scan Mode STOPPED")
    
    def _easm_log(self, level: str, message: str):
        """EASM logging callback."""
        level_upper = level.upper()
        if level_upper == "ERROR":
            logger.error(f"EASM: {message}")
        elif level_upper in ("WARN", "WARNING"):
            logger.warning(f"EASM: {message}")
        elif level_upper == "DEBUG":
            logger.debug(f"EASM: {message}")
        else:
            logger.info(f"EASM: {message}")
    
    def _run_easm_probes(self, base_networks: List[Network], timeout: float = 2.0) -> List[Dict]:
        """
        Run EASM probe cycle to discover additional network info.
        
        Sends probe requests and collects responses without blocking.
        """
        if not self._easm_controller:
            return []
        
        easm_results = []
        
        try:
            # Clear previous discoveries
            self._easm_discoveries.clear()
            
            # Trigger EASM tick to send probes
            self._easm_controller.tick()
            
            # Also send directed probes for hidden networks we detected
            for network in base_networks:
                if not network.ssid or network.ssid.startswith("Hidden_"):
                    # This is a hidden network - try to reveal it
                    self._easm_controller.request_hidden_reveal(network.bssid, network.channel)
            
            # Wait briefly for responses
            import time
            time.sleep(min(timeout, 1.0))
            
            # Collect discoveries
            easm_results = list(self._easm_discoveries)

            if easm_results:
                logger.info(f"EASM collected {len(easm_results)} discoveries this cycle")

        except Exception as e:
            logger.error(f"EASM probe cycle error: {e}")
        
        return easm_results
    
    def _merge_easm_results(self, networks: List[Network], easm_results: List[Dict]) -> List[Network]:
        """
        Merge EASM discoveries into the network list.
        
        Updates existing networks with EASM data and adds newly discovered ones.
        """
        if not easm_results:
            return networks
        
        # Index existing networks by BSSID
        network_map = {n.bssid.lower(): n for n in networks}
        
        for discovery in easm_results:
            bssid = discovery.get('bssid', '').lower()
            ssid = discovery.get('ssid', '')
            
            if bssid in network_map:
                # Update existing network with EASM data
                existing = network_map[bssid]
                
                # If we revealed a hidden SSID, update it
                if ssid and (not existing.ssid or existing.ssid.startswith("Hidden_")):
                    # Create updated network with revealed SSID
                    network_map[bssid] = Network(
                        ssid=ssid,
                        bssid=existing.bssid,
                        signal_percent=existing.signal_percent,
                        channel=existing.channel,
                        security=existing.security,
                        vendor=existing.vendor,
                        band=existing.band,
                        country=existing.country,
                        supported_rates=existing.supported_rates,
                        beacon_interval=existing.beacon_interval,
                        capabilities=discovery.get('capabilities', existing.capabilities),
                        first_seen=existing.first_seen,
                        last_seen=existing.last_seen
                    )
                    logger.info(f"EASM revealed hidden SSID: {ssid} ({bssid})")
            else:
                # New network discovered via EASM
                if bssid and ssid:
                    new_network = self._create_network(
                        ssid=ssid,
                        bssid=bssid,
                        channel=discovery.get('channel', 0),
                        signal=abs(discovery.get('rssi_dbm', -70)) + 30,  # Convert dBm to approx %
                        security=SecurityType.UNKNOWN
                    )
                    network_map[bssid] = new_network
                    logger.info(f"EASM new network discovered: {ssid} ({bssid})")
        
        return list(network_map.values())

    @property
    def name(self) -> str:
        base_name = "WindowsScanner (netsh)"
        if self._easm_enabled:
            return f"{base_name} + EASM"
        return base_name
    
    @property
    def platform(self) -> str:
        return "windows"
    
    def _check_scapy(self) -> bool:
        """Check if Scapy is available (quick check without slow imports)."""
        try:
            import scapy
            return True
        except ImportError:
            return False
    
    def is_available(self) -> bool:
        """Check if this scanner can run."""
        # netsh is always available on Windows
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def scan(self, timeout: float = 10.0) -> ScanResult:
        """
        Perform a WiFi scan.
        
        Args:
            timeout: Maximum time to scan in seconds
            
        Returns:
            ScanResult containing discovered networks
        """
        start_time = time.time()
        
        # Lazy EASM init (in scan thread, not UI thread)
        if self._easm_enabled and getattr(self, '_easm_pending', False):
            self._init_easm_real()
        
        # Always use netsh for base scanning (reliable, doesn't hang)
        networks = self._scan_netsh()
        
        # If EASM is active, run a quick probe cycle for additional data
        if self._easm_enabled and self._easm_controller:
            easm_networks = self._run_easm_probes(networks, timeout=2.0)
            # Merge EASM discoveries into network list
            networks = self._merge_easm_results(networks, easm_networks)
        
        duration = time.time() - start_time
        
        return ScanResult(
            networks=networks,
            scan_time=datetime.now(),
            duration_seconds=duration,
            scanner_type=self.name,
            platform=self.platform
        )
    
    def _scan_netsh(self) -> List[Network]:
        """
        Scan using netsh command.
        
        NOTE: This mode is ALWAYS passive. EASM does NOT affect it.
        netsh relies on the Windows WLAN service which performs
        its own passive scanning.
        """
        networks = []
        
        try:
            # Get network list
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return networks
            
            output = result.stdout
            
            # Parse output
            # Security is per-SSID, comes BEFORE BSSIDs
            # Multiple BSSIDs can share the same SSID
            current_ssid = ""
            current_bssid = ""
            current_channel = 0
            current_signal = 0
            current_security = SecurityType.UNKNOWN
            ssid_security = SecurityType.UNKNOWN  # Security applies to all BSSIDs under this SSID
            
            for line in output.split("\n"):
                line = line.strip()
                
                if line.startswith("SSID") and ":" in line and "BSSID" not in line:
                    # Save previous network if exists
                    if current_bssid:
                        networks.append(self._create_network(
                            current_ssid, current_bssid, current_channel,
                            current_signal, ssid_security  # Use the SSID's security
                        ))
                    
                    current_ssid = line.split(":", 1)[1].strip()
                    current_bssid = ""
                    current_channel = 0
                    current_signal = 0
                    ssid_security = SecurityType.UNKNOWN  # Reset security for new SSID
                
                elif "Authentication" in line:
                    # Security comes before BSSIDs, applies to all BSSIDs under this SSID
                    ssid_security = self._parse_security(line)
                
                elif line.startswith("BSSID"):
                    # Save previous BSSID if exists (multiple BSSIDs per SSID)
                    if current_bssid:
                        networks.append(self._create_network(
                            current_ssid, current_bssid, current_channel,
                            current_signal, ssid_security
                        ))
                    
                    current_bssid = line.split(":", 1)[1].strip()
                    # Reset per-BSSID values but keep ssid_security
                    current_channel = 0
                    current_signal = 0
                
                elif line.startswith("Signal"):
                    match = re.search(r"(\d+)%", line)
                    if match:
                        current_signal = int(match.group(1))
                
                elif line.startswith("Channel"):
                    match = re.search(r"(\d+)", line)
                    if match:
                        current_channel = int(match.group(1))
            
            # Don't forget the last network
            if current_bssid:
                networks.append(self._create_network(
                    current_ssid, current_bssid, current_channel,
                    current_signal, ssid_security
                ))
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"netsh scan error: {e}")

        return networks
    
    def _scan_scapy(self, timeout: float) -> List[Network]:
        """
        Scan using Scapy packet capture with safe threaded sniffing.
        
        This method uses SafeScapySniffer to prevent UI freezing.
        Falls back to netsh if Scapy sniffing fails.
        
        When EASM is enabled:
        - Sends broadcast probe requests
        - Sends directed probes for hidden SSIDs
        - Processes probe responses for enhanced data
        - All within legal rate limits
        
        When EASM is disabled:
        - Passive beacon reception only
        """
        # Try to initialize sniffer if needed
        if not self._init_scapy_sniffer():
            logger.warning("Scapy sniffer unavailable, falling back to netsh")
            return self._scan_netsh()
        
        networks = []
        seen_bssids = set()
        easm_enhanced_bssids = set()
        
        # Clear EASM discoveries from previous scan
        self._easm_discoveries.clear()
        
        # Track scan timing for EASM tick scheduling
        scan_start = time.time()
        last_easm_tick = scan_start
        easm_tick_interval = 0.5  # EASM tick every 500ms
        
        def packet_handler(packet):
            """Handle captured packets."""
            nonlocal last_easm_tick
            
            try:
                from scapy.all import Dot11Beacon, Dot11ProbeResp, Dot11Elt
                
                # === EASM TICK ===
                if self._easm_enabled and self._easm_controller:
                    now = time.time()
                    if now - last_easm_tick >= easm_tick_interval:
                        self._easm_controller.tick()
                        last_easm_tick = now
                    
                    # Let EASM process this packet
                    self._easm_controller.process_packet(packet)
                
                # === BEACON PROCESSING ===
                if packet.haslayer(Dot11Beacon):
                    bssid = packet.addr2
                    if bssid in seen_bssids:
                        return
                    seen_bssids.add(bssid)
                    
                    # Get SSID
                    ssid = ""
                    if packet.haslayer(Dot11Elt):
                        elt = packet[Dot11Elt]
                        if elt.ID == 0:
                            ssid = elt.info.decode('utf-8', errors='ignore')
                    
                    # Get channel
                    channel = 0
                    try:
                        channel = int(ord(packet[Dot11Beacon].network_stats().get("channel", b"\x00")))
                    except:
                        pass
                    
                    # Get signal strength
                    rssi_dbm = -50
                    if hasattr(packet, 'dBm_AntSignal'):
                        rssi_dbm = packet.dBm_AntSignal
                    
                    # Parse security
                    security = self._parse_beacon_security(packet)
                    
                    networks.append(Network(
                        ssid=ssid,
                        bssid=bssid,
                        channel=channel,
                        frequency_mhz=self._channel_to_freq(channel),
                        rssi_dbm=rssi_dbm,
                        security=security,
                        vendor=lookup_vendor(bssid),
                        last_seen=datetime.now()
                    ))
                
                # === PROBE RESPONSE PROCESSING (EASM Enhanced) ===
                elif packet.haslayer(Dot11ProbeResp) and self._easm_enabled:
                    bssid = packet.addr2
                    
                    ssid = ""
                    if packet.haslayer(Dot11Elt):
                        elt = packet[Dot11Elt]
                        if elt.ID == 0:
                            ssid = elt.info.decode('utf-8', errors='ignore')
                    
                    if bssid not in seen_bssids and ssid:
                        seen_bssids.add(bssid)
                        easm_enhanced_bssids.add(bssid)
                        
                        channel = 0
                        elt = packet.getlayer(Dot11Elt)
                        while elt:
                            if elt.ID == 3 and elt.info:
                                channel = elt.info[0]
                                break
                            elt = elt.payload.getlayer(Dot11Elt) if elt.payload else None
                        
                        rssi_dbm = packet.dBm_AntSignal if hasattr(packet, 'dBm_AntSignal') else -50
                        
                        networks.append(Network(
                            ssid=ssid,
                            bssid=bssid,
                            channel=channel,
                            frequency_mhz=self._channel_to_freq(channel),
                            rssi_dbm=rssi_dbm,
                            security=SecurityType.UNKNOWN,
                            vendor=lookup_vendor(bssid),
                            last_seen=datetime.now()
                        ))
            except Exception as e:
                logger.error(f"Packet handler error: {e}")
        
        try:
            # Start sniffing in background thread
            if not self._scapy_sniffer.start_sniff(packet_handler, timeout=timeout):
                logger.error(f"Sniff failed: {self._scapy_sniffer.get_error()}")
                return self._scan_netsh()

            # Wait for sniff to complete (with timeout protection)
            wait_start = time.time()
            while self._scapy_sniffer.is_running():
                time.sleep(0.1)
                if time.time() - wait_start > timeout + 2.0:
                    logger.warning("Sniff timeout - stopping")
                    self._scapy_sniffer.stop()
                    break

            # Merge any EASM discoveries
            networks = self._merge_easm_discoveries(networks, easm_enhanced_bssids)

            # Log EASM stats
            if self._easm_enabled and self._easm_controller:
                try:
                    stats = self._easm_controller.get_full_stats()
                    logger.info(f"EASM scan complete: {stats['probes']['sent']} probes, "
                          f"{stats['probes']['responses']} responses, "
                          f"{stats['hidden_ssids']['revealed']} hidden revealed")
                except:
                    pass

            logger.info(f"Scapy scan captured {len(networks)} networks")

        except Exception as e:
            logger.error(f"Scapy scan error: {e}")
            return self._scan_netsh()

        # If Scapy found nothing, fall back to netsh
        if not networks:
            logger.info("Scapy found no networks, trying netsh")
            return self._scan_netsh()
        
        return networks
    
    def _parse_beacon_security(self, packet) -> SecurityType:
        """Parse security type from beacon frame."""
        try:
            from scapy.all import Dot11Beacon, Dot11Elt
            
            # Check privacy bit first
            cap = packet[Dot11Beacon].cap
            if not (cap & 0x0010):  # Privacy bit
                return SecurityType.OPEN
            
            # Look for RSN IE (WPA2/WPA3)
            elt = packet.getlayer(Dot11Elt)
            while elt:
                if elt.ID == 48:  # RSN IE
                    # Check for WPA3 (SAE)
                    if elt.info and len(elt.info) > 8:
                        # Look for SAE AKM (00-0F-AC:08)
                        if b'\x00\x0f\xac\x08' in elt.info:
                            return SecurityType.WPA3
                    return SecurityType.WPA2
                elif elt.ID == 221:  # Vendor Specific (WPA1)
                    if elt.info and elt.info.startswith(b'\x00\x50\xf2\x01'):
                        return SecurityType.WPA
                elt = elt.payload.getlayer(Dot11Elt) if elt.payload else None
            
            # Has privacy but no WPA/RSN IE = WEP
            return SecurityType.WEP
            
        except:
            return SecurityType.UNKNOWN
    
    def _merge_easm_discoveries(self, networks: List[Network], 
                                 already_enhanced: set) -> List[Network]:
        """Merge EASM discoveries into network list."""
        if not self._easm_discoveries:
            return networks
        
        # Build BSSID lookup
        bssid_map = {n.bssid.lower(): n for n in networks}
        
        for discovery in self._easm_discoveries:
            bssid = discovery['bssid'].lower()
            
            # Skip if already in networks
            if bssid in bssid_map:
                continue
            
            # Add new network from EASM discovery
            if discovery['ssid']:
                networks.append(Network(
                    ssid=discovery['ssid'],
                    bssid=discovery['bssid'],
                    channel=discovery.get('channel', 0),
                    frequency_mhz=self._channel_to_freq(discovery.get('channel', 0)),
                    rssi_dbm=discovery.get('rssi_dbm', -70),
                    security=SecurityType.UNKNOWN,
                    vendor=lookup_vendor(discovery['bssid']),
                    last_seen=datetime.now()
                ))
        
        return networks
    
    def _create_network(self, ssid: str, bssid: str, channel: int,
                        signal_percent: int, security: SecurityType) -> Network:
        """Create Network object from parsed data."""
        # Convert signal percentage to approximate dBm
        # 100% ≈ -30 dBm, 0% ≈ -90 dBm
        rssi_dbm = int(-90 + (signal_percent * 0.6))
        
        return Network(
            ssid=ssid,
            bssid=bssid,
            channel=channel,
            frequency_mhz=self._channel_to_freq(channel),
            rssi_dbm=rssi_dbm,
            security=security,
            vendor=lookup_vendor(bssid),
            last_seen=datetime.now()
        )
    
    def _channel_to_freq(self, channel: int) -> int:
        """Convert WiFi channel number to frequency in MHz."""
        if channel <= 0:
            return 0
        
        # 2.4 GHz band (channels 1-14)
        if 1 <= channel <= 14:
            if channel == 14:
                return 2484
            return 2407 + (channel * 5)
        
        # 5 GHz band
        if 36 <= channel <= 177:
            return 5000 + (channel * 5)
        
        return 0
    
    def _parse_security(self, line: str) -> SecurityType:
        """Parse security type from netsh output line."""
        line = line.upper()
        
        if "WPA3" in line:
            if "ENTERPRISE" in line:
                return SecurityType.WPA3_ENTERPRISE
            return SecurityType.WPA3
        elif "WPA2" in line:
            if "ENTERPRISE" in line:
                return SecurityType.WPA2_ENTERPRISE
            return SecurityType.WPA2
        elif "WPA" in line:
            return SecurityType.WPA
        elif "WEP" in line:
            return SecurityType.WEP
        elif "OPEN" in line or "NONE" in line:
            return SecurityType.OPEN
        
        return SecurityType.UNKNOWN
    
    def get_easm_stats(self) -> Optional[Dict[str, Any]]:
        """Get EASM statistics (if enabled)."""
        if self._easm_controller:
            return self._easm_controller.get_full_stats()
        return None

