"""
Main GUI application for Nexus WiFi Radar - CYBERPUNK EDITION.

Integrates all components into a complete application with:
- Cyberpunk themes (Neon Green, Cyan, Purple, Red, Pink, Sleek Pro)
- Animated radar display with sound waves
- Signal strength heatmap visualization
- Matrix data rain effects
- Audio hydrophone system for network sonar
- Full security audit and threat detection
- Event logging and activity monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import math
from datetime import datetime
from typing import Optional, List, Dict
from collections import defaultdict

try:
    import winsound
except ImportError:
    winsound = None

from nexus.core.scan import get_scanner, Scanner
from nexus.core.models import Network, ScanResult
from nexus.core.config import Config, get_config
from nexus.core.distance import get_estimator, DistanceEstimate
from nexus.core.radar_modes import get_radar_system, RadarMode, RadarSystem
from nexus.core.fingerprint import get_fingerprinter, DeviceType, DEVICE_ICONS
from nexus.core.stability import get_stability_tracker, get_wall_estimator, StabilityRating
from nexus.core.intelligence import get_pic, PassiveIntelligenceCore, NetworkIntelligence
from nexus.core.world_model import get_world_model, UnifiedWorldModel
from nexus.core.hidden_classifier import get_hidden_classifier, HiddenNetworkClassifier, HiddenNetworkType
from nexus.core.oui_vendor import get_oui_intelligence, OUIVendorIntelligence
from nexus.security.detection import ThreatDetector
from nexus.security.spoof import get_spoof_detector, ThreatLevel
from nexus.audio.sonar import SonarAudio, get_sonar
from nexus.ui.skins import get_pipboy_skin, PIPBOY_THEME
from nexus.ui.intel_dashboard import IntelligenceDashboard, IntelEvent, EventType


class NexusApp:
    """
    Main Nexus WiFi Radar application - CYBERPUNK EDITION.
    
    Features:
    - Multiple cyberpunk color themes (F1-F6 to switch, T to cycle)
    - Animated radar with signal waves
    - Heatmap visualization
    - Matrix data rain effect
    - Audio hydrophone for network sonar
    - Full security analysis
    """
    
    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("⚡ NEXUS WiFi Radar v2.0 // INTELLIGENCE EDITION ⚡")
        self.root.geometry("1400x900")
        self.root.configure(bg="#000000")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # State
        self.config = get_config()
        self.scanner: Optional[Scanner] = None
        self.detector = ThreatDetector()
        self.sonar = get_sonar()
        self.distance_estimator = get_estimator()
        self.radar_system = get_radar_system()
        self.fingerprinter = get_fingerprinter()
        self.stability_tracker = get_stability_tracker()
        self.wall_estimator = get_wall_estimator()
        self.spoof_detector = get_spoof_detector()
        self.intelligence_core = get_pic()  # Passive Intelligence Core - the brain of NEXUS
        self.world_model = get_world_model()  # Unified World Model Expander - central intelligence graph
        self.hidden_classifier = get_hidden_classifier()  # Hidden Network Classification Engine
        self.pipboy_skin = None  # Pip-Boy skin instance (lazy-loaded)
        self.is_scanning = False
        self.scan_count = 0
        self.networks: Dict[str, Dict] = {}  # BSSID -> network data
        self.last_result: Optional[ScanResult] = None
        
        # Weak signal detection settings
        self.extended_scan_mode = False  # Extended scan for weak signals
        self.scan_timeout = 10.0  # Normal scan timeout
        self.extended_timeout = 30.0  # Extended scan timeout
        self.weak_signal_threshold = -75  # dBm threshold for weak signal marking
        self.very_weak_threshold = -85  # dBm threshold for very weak signals
        self.min_signal_filter = -95  # Minimum signal to show (default: show all)
        
        # Signal history for charts
        self.signal_history: Dict[str, List[dict]] = defaultdict(list)
        self.max_history = 50
        
        # Animation state
        self.rotation_angle = 0
        self.breathe_phase = 0
        self.glitch_counter = 0
        self.matrix_chars = []
        self.matrix_counter = 0
        self.update_interval = 50  # 20 FPS
        self.wave_intensity = 0.5
        self.effects_enabled = True
        
        # EASM (Enhanced Active Scan Mode) state
        self.easm_enabled = False
        self.easm_cover_open = False  # Safety cover state
        self.easm_armed = False  # Button armed state
        
        # Audio state
        self.selected_network = None
        self.audio_playing = False
        self.audio_thread = None
        self.is_muted = False
        
        # Radar state
        self.radar_zoom = 1.0
        self.radar_pan_x = 0
        self.radar_pan_y = 0
        self.radar_drag_start = None
        self.network_positions = {}
        self.show_heatmap = False
        
        # Event log
        self.event_log = []
        self.max_log_events = 100
        
        # Spectrogram state
        self.spectrogram_history: Dict[str, List[tuple]] = defaultdict(list)  # BSSID -> [(timestamp, signal), ...]
        self.spectrogram_max_seconds = 60  # Time window
        self.spectrogram_selected = "all"  # "all" or specific BSSID
        self.spectrogram_scroll_offset = 0
        
        # Theme system - 6 cyberpunk color profiles
        self.current_profile = "neon_green"
        self.ui_themes = {
            "neon_green": {
                "name": "🟢 NEON GREEN",
                "bg_main": "#000000",
                "bg_panel": "#0a0e27",
                "text_primary": "#00ff00",
                "text_secondary": "#00ffff",
                "text_accent": "#ff00ff",
                "button_primary": "#00ff00",
                "button_secondary": "#00ffff",
                "button_accent": "#ff00ff",
                "border_color": "#00ff00",
                "radar_bg": "#0f1620",
                "grid_color": "#0a2a2a"
            },
            "neon_cyan": {
                "name": "🔵 NEON CYAN",
                "bg_main": "#000000",
                "bg_panel": "#0a1f2a",
                "text_primary": "#00ffff",
                "text_secondary": "#0099ff",
                "text_accent": "#00ff88",
                "button_primary": "#00ffff",
                "button_secondary": "#0099ff",
                "button_accent": "#00ff88",
                "border_color": "#00ffff",
                "radar_bg": "#051a2a",
                "grid_color": "#0a1f2a"
            },
            "neon_purple": {
                "name": "🟣 NEON PURPLE",
                "bg_main": "#000000",
                "bg_panel": "#2a0a2a",
                "text_primary": "#ff00ff",
                "text_secondary": "#ff00aa",
                "text_accent": "#aa00ff",
                "button_primary": "#ff00ff",
                "button_secondary": "#ff00aa",
                "button_accent": "#aa00ff",
                "border_color": "#ff00ff",
                "radar_bg": "#1a052a",
                "grid_color": "#2a0a2a"
            },
            "neon_red": {
                "name": "🔴 NEON RED",
                "bg_main": "#000000",
                "bg_panel": "#2a0a0a",
                "text_primary": "#ff0000",
                "text_secondary": "#ff5500",
                "text_accent": "#ffff00",
                "button_primary": "#ff0000",
                "button_secondary": "#ff5500",
                "button_accent": "#ffff00",
                "border_color": "#ff0000",
                "radar_bg": "#150505",
                "grid_color": "#2a0a0a"
            },
            "neon_pink": {
                "name": "💗 NEON PINK",
                "bg_main": "#000000",
                "bg_panel": "#2a0a20",
                "text_primary": "#ff0088",
                "text_secondary": "#ff3388",
                "text_accent": "#ffaa00",
                "button_primary": "#ff0088",
                "button_secondary": "#ff3388",
                "button_accent": "#ffaa00",
                "border_color": "#ff0088",
                "radar_bg": "#1a050f",
                "grid_color": "#2a0a20"
            },
            "sleek_pro": {
                "name": "⚫ SLEEK PRO",
                "bg_main": "#0a0a0a",
                "bg_panel": "#1a1a1a",
                "text_primary": "#e0e0e0",
                "text_secondary": "#b0b0b0",
                "text_accent": "#00ccff",
                "button_primary": "#333333",
                "button_secondary": "#404040",
                "button_accent": "#00ccff",
                "border_color": "#00ccff",
                "radar_bg": "#111111",
                "grid_color": "#222222"
            },
            "pipboy": PIPBOY_THEME
        }
        
        # Try to get scanner
        try:
            self.scanner = get_scanner(prefer_scapy=self.config.scan.use_scapy)
            self.scanner_status = f"Scanner: {self.scanner.name}"
        except Exception as e:
            self.scanner_status = f"Scanner unavailable: {e}"
            self.scanner = None
        
        # Build UI
        self._build_ui()
        
        # Configure audio
        self.sonar.set_enabled(self.config.audio.enabled)
        self.sonar.set_volume(self.config.audio.volume)
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
        
        # Log startup
        self.log_event("SYSTEM", "Nexus WiFi Radar CYBERPUNK initialized")
        self.log_event("INFO", "Press F1-F6 to change themes, T to cycle")
        self.log_event("INFO", "Press SPACEBAR to start/stop scan")
        self.log_event("READY", "Awaiting scan command...")
        
        # Start update loop
        self._schedule_update()
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind("<F1>", lambda e: self._apply_profile("neon_green"))
        self.root.bind("<F2>", lambda e: self._apply_profile("neon_cyan"))
        self.root.bind("<F3>", lambda e: self._apply_profile("neon_purple"))
        self.root.bind("<F4>", lambda e: self._apply_profile("neon_red"))
        self.root.bind("<F5>", lambda e: self._apply_profile("neon_pink"))
        self.root.bind("<F6>", lambda e: self._apply_profile("sleek_pro"))
        self.root.bind("t", self._cycle_theme)
        self.root.bind("T", self._cycle_theme)
        self.root.bind("<space>", self._toggle_scan)
        self.root.bind("h", lambda e: self._toggle_heatmap())
        self.root.bind("H", lambda e: self._toggle_heatmap())
    
    def _apply_notebook_theme(self, theme):
        """Apply theme colors to notebook tabs."""
        bg_main = theme["bg_main"]
        bg_panel = theme["bg_panel"]
        primary = theme["text_primary"]
        accent = theme["text_accent"]
        
        # Configure notebook background
        self.style.configure('TNotebook', background=bg_main, borderwidth=0, tabmargins=[0, 0, 0, 0])
        self.style.configure('TNotebook.Tab', 
                            background=bg_panel,
                            foreground=primary,
                            padding=[20, 8], 
                            font=("Courier New", 9, "bold"),
                            borderwidth=0)
        self.style.map('TNotebook.Tab', 
                      background=[('selected', primary), ('!selected', bg_panel), ('active', bg_panel)],
                      foreground=[('selected', bg_main), ('!selected', primary), ('active', accent)],
                      expand=[('selected', [0, 0, 0, 0])])
        
        # Also style TFrame to have dark background
        self.style.configure('TFrame', background=bg_main)
        
        # Update treeview with theme colors
        self.style.configure('Treeview', 
                            background=bg_panel,
                            foreground=primary,
                            fieldbackground=bg_panel,
                            font=("Courier New", 9))
        self.style.configure('Treeview.Heading',
                            background=bg_main,
                            foreground=accent,
                            font=("Courier New", 9, "bold"))
        self.style.map('Treeview',
                      background=[('selected', primary)],
                      foreground=[('selected', bg_main)])

    def _cycle_theme(self, event=None):
        """Cycle through themes."""
        profiles = list(self.ui_themes.keys())
        idx = profiles.index(self.current_profile)
        next_idx = (idx + 1) % len(profiles)
        self._apply_profile(profiles[next_idx])
    
    def _apply_profile(self, profile_name):
        """Apply a theme profile."""
        if profile_name not in self.ui_themes:
            return
        
        # Handle Pip-Boy skin toggle
        if profile_name == "pipboy":
            # Lazy-load Pip-Boy skin (pass root to initialize)
            if self.pipboy_skin is None:
                self.pipboy_skin = get_pipboy_skin(self.root)
            self.pipboy_skin.apply()
        else:
            # Revert Pip-Boy skin if switching away from it
            if self.pipboy_skin is not None and self.current_profile == "pipboy":
                self.pipboy_skin.revert()
        
        self.current_profile = profile_name
        theme = self.ui_themes[profile_name]
        
        # Update main window
        self.root.configure(bg=theme["bg_main"])
        
        # Update header
        self.header.configure(bg=theme["bg_main"])
        self.header_title.configure(bg=theme["bg_main"], fg=theme["text_secondary"])
        self.header_subtitle.configure(bg=theme["bg_main"], fg=theme["text_accent"])
        
        # Update radar canvas
        self.radar_canvas.configure(bg=theme["radar_bg"])
        
        # Update matrix canvas
        self.matrix_canvas.configure(bg=theme["bg_main"])
        
        # Update status bar
        self.status_frame.configure(bg=theme["bg_panel"])
        self.status_label.configure(bg=theme["bg_panel"], fg=theme["text_primary"])
        self.stats_label.configure(bg=theme["bg_panel"], fg=theme["text_secondary"])
        
        # Update profile buttons
        for pid, btn in self.profile_buttons.items():
            if pid == profile_name:
                btn.config(relief="sunken", bd=3)
            else:
                btn.config(relief="raised", bd=2)
        
        # Update notebook/tab styling with new theme colors
        if hasattr(self, 'style'):
            self._apply_notebook_theme(theme)
        
        self.log_event("PROFILE", f"Switched to {theme['name']}")
    
    def log_event(self, event_type, message):
        """Log an event."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.event_log.append((timestamp, event_type, message))
        
        if len(self.event_log) > self.max_log_events:
            self.event_log.pop(0)
        
        if hasattr(self, 'event_display'):
            self._update_event_log_display()
    
    def _build_ui(self):
        """Build the user interface."""
        theme = self.ui_themes[self.current_profile]
        
        # Header with cyberpunk styling
        self.header = tk.Frame(self.root, bg=theme["bg_main"], height=100)
        self.header.pack(fill="x", pady=(0, 3))
        self.header.pack_propagate(False)
        
        # Top border with gradient effect
        top_border = tk.Frame(self.header, bg=theme["bg_main"])
        top_border.pack(fill="x")
        tk.Label(top_border, text="═" * 150, font=("Courier New", 3), 
                 fg=theme["text_accent"], bg=theme["bg_main"]).pack()
        
        # Version badge row
        badge_frame = tk.Frame(self.header, bg=theme["bg_main"])
        badge_frame.pack()
        tk.Label(badge_frame, text="╔═══╗", font=("Courier New", 6), 
                 fg="#ff00ff", bg=theme["bg_main"]).pack(side="left")
        tk.Label(badge_frame, text=" v2.0 ", font=("Courier New", 8, "bold"), 
                 fg="#000000", bg="#00ffff").pack(side="left")
        tk.Label(badge_frame, text="╚═══╝", font=("Courier New", 6), 
                 fg="#ff00ff", bg=theme["bg_main"]).pack(side="left")
        tk.Label(badge_frame, text="   ████ PASSIVE INTELLIGENCE PLATFORM ████   ", 
                 font=("Courier New", 7, "bold"), fg="#00ff00", bg=theme["bg_main"]).pack(side="left")
        
        self.header_title = tk.Label(
            self.header,
            text="⚡ NEXUS // WiFi RADAR // INTELLIGENCE EDITION ⚡",
            font=("Courier New", 20, "bold"),
            fg=theme["text_secondary"],
            bg=theme["bg_main"]
        )
        self.header_title.pack(pady=3)
        
        self.header_subtitle = tk.Label(
            self.header,
            text="◈ UWM-X ◈ PIC ◈ HNCE ◈ SONAR ◈ RADAR ◈ HEATMAP ◈ 100% PASSIVE ◈",
            font=("Courier New", 9, "bold"),
            fg=theme["text_accent"],
            bg=theme["bg_main"]
        )
        self.header_subtitle.pack()
        
        # Bottom border
        tk.Label(self.header, text="═" * 150, font=("Courier New", 3), 
                 fg=theme["text_accent"], bg=theme["bg_main"]).pack()
        
        # Matrix canvas (for data rain effect)
        self.matrix_canvas = tk.Canvas(self.root, bg=theme["bg_main"], 
                                        height=50, highlightthickness=0)
        self.matrix_canvas.pack(fill="x", padx=3)
        
        # Main content with notebook - v2.0 improved styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        theme = self.ui_themes[self.current_profile]
        
        # Custom notebook styling with proper dark backgrounds
        # Create custom layout to ensure tab backgrounds work on Windows
        self.style.layout('Dark.TNotebook.Tab', [
            ('Notebook.tab', {'sticky': 'nswe', 'children': [
                ('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [
                    ('Notebook.label', {'side': 'top', 'sticky': ''})
                ]})
            ]})
        ])
        
        self._apply_notebook_theme(theme)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Tab 1: Radar View
        radar_frame = ttk.Frame(self.notebook)
        self.notebook.add(radar_frame, text="🎯 RADAR")
        self._build_radar_view(radar_frame)
        
        # Tab 2: Network List
        list_frame = ttk.Frame(self.notebook)
        self.notebook.add(list_frame, text="📡 NETWORKS")
        self._build_network_list(list_frame)
        
        # Tab 3: Security Audit
        security_frame = ttk.Frame(self.notebook)
        self.notebook.add(security_frame, text="🛡️ SECURITY AUDIT")
        self._build_security_audit(security_frame)
        
        # Tab 4: Intelligence Core (replaces Activity Monitor)
        intel_frame = ttk.Frame(self.notebook)
        self.notebook.add(intel_frame, text="🧠 INTELLIGENCE CORE")
        self._build_intelligence_core(intel_frame)
        
        # Tab 5: Statistics
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 STATISTICS")
        self._build_statistics_view(stats_frame)
        
        # Tab 6: Vulnerabilities
        vuln_frame = ttk.Frame(self.notebook)
        self.notebook.add(vuln_frame, text="⚔️ VULNERABILITIES")
        self._build_vulnerability_view(vuln_frame)
        
        # Tab 7: Event Log
        event_frame = ttk.Frame(self.notebook)
        self.notebook.add(event_frame, text="📝 EVENT LOG")
        self._build_event_log(event_frame)
        
        # Tab 8: Signal Spectrogram (NEW!)
        spectro_frame = ttk.Frame(self.notebook)
        self.notebook.add(spectro_frame, text="🌊 SPECTROGRAM")
        self._build_spectrogram_view(spectro_frame)
        
        # Tab 9: Hidden Network Diagnostics
        hidden_frame = ttk.Frame(self.notebook)
        self.notebook.add(hidden_frame, text="👁️ HIDDEN NETWORKS")
        self._build_hidden_diagnostics(hidden_frame)
        
        # Theme selector row
        self._build_theme_selector()
        
        # Control panel
        self._build_controls()
        
        # Status bar
        self._build_status_bar()
    
    def _build_radar_view(self, parent):
        """Build the radar view with zoom and heatmap controls."""
        theme = self.ui_themes[self.current_profile]
        
        # Zoom controls
        zoom_frame = tk.Frame(parent, bg=theme["radar_bg"])
        zoom_frame.pack(fill="x", padx=3, pady=3)
        
        tk.Label(zoom_frame, text="║ 🔍 ZOOM", font=("Courier New", 9, "bold"),
                 fg=theme["text_secondary"], bg=theme["radar_bg"]).pack(side="left", padx=5)
        
        self.zoom_label = tk.Label(zoom_frame, text="1.0x", font=("Courier New", 9, "bold"),
                                   fg=theme["text_accent"], bg=theme["radar_bg"], width=5)
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_slider = ttk.Scale(zoom_frame, from_=0.5, to=3.0, orient="horizontal",
                                      command=self._on_zoom_change, length=150)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="left", padx=5)
        
        tk.Label(zoom_frame, text="║ CLICK NETWORK FOR DETAILS | DRAG TO PAN ║",
                 font=("Courier New", 8), fg=theme["text_primary"], 
                 bg=theme["radar_bg"]).pack(side="left", padx=10)
        
        # Heatmap toggle
        self.btn_heatmap = tk.Button(zoom_frame, text="🔥 HEATMAP", command=self._toggle_heatmap,
                                     bg="#ff6600", fg="#000000", font=("Courier New", 9, "bold"),
                                     relief="raised", bd=2, padx=8)
        self.btn_heatmap.pack(side="left", padx=5)
        
        # Radar mode toggle
        self.btn_radar_mode = tk.Button(zoom_frame, text="📡 STATIC", command=self._toggle_radar_mode,
                                        bg="#00ff88", fg="#000000", font=("Courier New", 9, "bold"),
                                        relief="raised", bd=2, padx=8)
        self.btn_radar_mode.pack(side="left", padx=5)
        
        # Mode indicator
        self.radar_mode_label = tk.Label(zoom_frame, text="Desktop Mode",
                                         font=("Courier New", 8), fg="#00ff88",
                                         bg=theme["radar_bg"])
        self.radar_mode_label.pack(side="left", padx=5)
        
        # Radar canvas
        self.radar_canvas = tk.Canvas(parent, bg=theme["radar_bg"], highlightthickness=0)
        self.radar_canvas.pack(fill="both", expand=True)
        
        # Bind radar events
        self.radar_canvas.bind("<Button-1>", self._on_radar_click)
        self.radar_canvas.bind("<B1-Motion>", self._on_radar_drag)
        self.radar_canvas.bind("<ButtonRelease-1>", self._on_radar_release)
        self.radar_canvas.bind("<MouseWheel>", self._on_radar_scroll)
    
    def _build_network_list(self, parent):
        """Build the network list view."""
        columns = ("TYPE", "SSID", "SIGNAL", "VENDOR", "LOCATION", "CHANNEL", "SECURITY", "SRC")
        self.network_tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)
        
        widths = [60, 170, 110, 130, 100, 60, 90, 45]
        for col, width in zip(columns, widths):
            self.network_tree.heading(col, text=col)
            self.network_tree.column(col, width=width)
        
        # Style the treeview
        style = ttk.Style()
        style.configure("Treeview", background="#1a1f3a", foreground="#00ffff",
                       fieldbackground="#1a1f3a", borderwidth=1)
        style.map('Treeview', background=[('selected', '#ff00ff')])
        style.configure("Treeview.Heading", background="#0f1620", foreground="#00ff88",
                       borderwidth=2, relief="raised")
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.network_tree.yview)
        self.network_tree.configure(yscrollcommand=scrollbar.set)
        
        self.network_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Tags for color coding
        self.network_tree.tag_configure("excellent", foreground="#00ff00")
        self.network_tree.tag_configure("good", foreground="#00ffff")
        self.network_tree.tag_configure("fair", foreground="#ffff00")
        self.network_tree.tag_configure("weak", foreground="#ff0088")
        self.network_tree.tag_configure("very_weak", foreground="#ff4444", background="#1a0a0a")  # Very weak signals
        self.network_tree.tag_configure("randomized", foreground="#ff8800")  # Orange for randomized MACs
        self.network_tree.tag_configure("easm", foreground="#ff4444", background="#2a1a1a")  # Red highlight for EASM discoveries
        self.network_tree.tag_configure("easm_revealed", foreground="#ff8800", background="#2a2010")  # Orange for revealed hidden SSIDs
    
    def _build_security_audit(self, parent):
        """Build the security audit view."""
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side="right", fill="y")
        
        self.security_text = tk.Text(parent, bg="#0a0e27", fg="#00ff00",
                                     yscrollcommand=scrollbar.set,
                                     font=("Courier New", 9), wrap="word",
                                     state="disabled")
        self.security_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.security_text.yview)
    
    def _build_intelligence_core(self, parent):
        """
        Build the INTELLIGENCE CORE tab - the brain of NEXUS.
        
        Uses the new three-panel IntelligenceDashboard:
        - Left Panel: Intelligence Summary (stats, counts)
        - Center Panel: Intelligence Feed (color-coded scrolling events)
        - Right Panel: Detail Inspector (click to inspect)
        
        100% PASSIVE - Only displays data from beacon analysis.
        """
        theme = self.ui_themes[self.current_profile]
        
        # Use the new three-panel IntelligenceDashboard
        self.intel_dashboard = IntelligenceDashboard(parent, theme, app_ref=self)
        
        # Store reference to container for theme updates
        self.intel_container = self.intel_dashboard.main_frame
    
    def _build_intel_network_overview(self, parent, theme):
        """Section 1: Network Intelligence Overview grid."""
        section = tk.LabelFrame(parent, text="📊 NETWORK INTELLIGENCE OVERVIEW",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Treeview for network grid
        columns = ("icon", "ssid", "signal", "device", "distance", "walls", "stability", "security", "spoof", "movement")
        self.intel_tree = ttk.Treeview(section, columns=columns, show="headings", height=8)
        
        # Configure columns
        self.intel_tree.heading("icon", text="🔧")
        self.intel_tree.heading("ssid", text="SSID")
        self.intel_tree.heading("signal", text="Signal")
        self.intel_tree.heading("device", text="Device")
        self.intel_tree.heading("distance", text="Distance")
        self.intel_tree.heading("walls", text="Walls")
        self.intel_tree.heading("stability", text="Stability")
        self.intel_tree.heading("security", text="Security")
        self.intel_tree.heading("spoof", text="Spoof Risk")
        self.intel_tree.heading("movement", text="Movement")
        
        self.intel_tree.column("icon", width=40, anchor="center")
        self.intel_tree.column("ssid", width=150, anchor="w")
        self.intel_tree.column("signal", width=70, anchor="center")
        self.intel_tree.column("device", width=100, anchor="center")
        self.intel_tree.column("distance", width=80, anchor="center")
        self.intel_tree.column("walls", width=60, anchor="center")
        self.intel_tree.column("stability", width=80, anchor="center")
        self.intel_tree.column("security", width=80, anchor="center")
        self.intel_tree.column("spoof", width=80, anchor="center")
        self.intel_tree.column("movement", width=80, anchor="center")
        
        # Scrollbar
        tree_scroll = ttk.Scrollbar(section, orient="vertical", command=self.intel_tree.yview)
        self.intel_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.intel_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        tree_scroll.pack(side="right", fill="y")
        
        # Bind click for details
        self.intel_tree.bind("<Double-1>", self._on_intel_tree_click)
    
    def _build_intel_fingerprint_section(self, parent, theme):
        """Section 2: Device Fingerprinting Summary."""
        section = tk.LabelFrame(parent, text="🔍 PASSIVE DEVICE FINGERPRINTING",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Device type counts display
        self.intel_fingerprint_text = tk.Text(section, bg=theme["bg_main"], fg=theme["text_primary"],
                                              font=("Courier New", 9), height=6, wrap="word",
                                              state="disabled", bd=0)
        self.intel_fingerprint_text.pack(fill="x", padx=5, pady=5)
        
        # Tags for device types
        self.intel_fingerprint_text.tag_config("header", foreground=theme["text_accent"], font=("Courier New", 9, "bold"))
        self.intel_fingerprint_text.tag_config("icon", foreground="#ffffff")
        self.intel_fingerprint_text.tag_config("count", foreground="#00ff88")
    
    def _build_intel_distance_section(self, parent, theme):
        """Section 3: Distance & Direction Engine."""
        section = tk.LabelFrame(parent, text="📡 DISTANCE & DIRECTION ENGINE",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Distance canvas for mini visualization
        self.intel_distance_canvas = tk.Canvas(section, bg=theme["bg_main"], 
                                               height=150, highlightthickness=0)
        self.intel_distance_canvas.pack(fill="x", padx=5, pady=5)
        
        # Distance legend/stats
        self.intel_distance_text = tk.Text(section, bg=theme["bg_main"], fg=theme["text_primary"],
                                           font=("Courier New", 9), height=4, wrap="word",
                                           state="disabled", bd=0)
        self.intel_distance_text.pack(fill="x", padx=5, pady=5)
    
    def _build_intel_temporal_section(self, parent, theme):
        """Section 4: Temporal Behaviour Engine."""
        section = tk.LabelFrame(parent, text="⏱️ TEMPORAL BEHAVIOUR ENGINE",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Temporal metrics display
        self.intel_temporal_text = tk.Text(section, bg=theme["bg_main"], fg=theme["text_primary"],
                                           font=("Courier New", 9), height=8, wrap="word",
                                           state="disabled", bd=0)
        self.intel_temporal_text.pack(fill="x", padx=5, pady=5)
        
        # Tags
        self.intel_temporal_text.tag_config("header", foreground=theme["text_accent"], font=("Courier New", 9, "bold"))
        self.intel_temporal_text.tag_config("stable", foreground="#00ff00")
        self.intel_temporal_text.tag_config("unstable", foreground="#ffff00")
        self.intel_temporal_text.tag_config("erratic", foreground="#ff0000")
    
    def _build_intel_security_section(self, parent, theme):
        """Section 5: Security Intelligence."""
        section = tk.LabelFrame(parent, text="🛡️ SECURITY INTELLIGENCE",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Security overview - increased height for more content
        self.intel_security_text = tk.Text(section, bg=theme["bg_main"], fg=theme["text_primary"],
                                           font=("Courier New", 9), height=18, wrap="word",
                                           state="disabled", bd=0)
        self.intel_security_text.pack(fill="x", padx=5, pady=5)
        
        # Tags
        self.intel_security_text.tag_config("header", foreground=theme["text_accent"], font=("Courier New", 9, "bold"))
        self.intel_security_text.tag_config("excellent", foreground="#00ff88")
        self.intel_security_text.tag_config("good", foreground="#00ff00")
        self.intel_security_text.tag_config("moderate", foreground="#ffff00")
        self.intel_security_text.tag_config("weak", foreground="#ff8800")
        self.intel_security_text.tag_config("critical", foreground="#ff0000")
        self.intel_security_text.tag_config("spoof_alert", foreground="#ff00ff", font=("Courier New", 9, "bold"))
    
    def _build_intel_relationship_section(self, parent, theme):
        """Section 6: Relationship Mapping."""
        section = tk.LabelFrame(parent, text="🔗 RELATIONSHIP MAPPING",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Relationship canvas for graph visualization
        self.intel_relationship_canvas = tk.Canvas(section, bg=theme["bg_main"], 
                                                   height=180, highlightthickness=0)
        self.intel_relationship_canvas.pack(fill="x", padx=5, pady=5)
        
        # Relationship text summary
        self.intel_relationship_text = tk.Text(section, bg=theme["bg_main"], fg=theme["text_primary"],
                                               font=("Courier New", 9), height=4, wrap="word",
                                               state="disabled", bd=0)
        self.intel_relationship_text.pack(fill="x", padx=5, pady=5)
    
    def _build_intel_mode_manager(self, parent, theme):
        """Section 7: Mode Manager."""
        section = tk.LabelFrame(parent, text="⚙️ MODE MANAGER",
                               font=("Courier New", 10, "bold"),
                               fg=theme["text_accent"], bg=theme["bg_main"],
                               bd=2, relief="ridge")
        section.pack(fill="x", padx=10, pady=5)
        
        # Mode controls row
        controls = tk.Frame(section, bg=theme["bg_main"])
        controls.pack(fill="x", padx=5, pady=5)
        
        # Mode label
        self.intel_mode_label = tk.Label(controls, text="CURRENT MODE: STATIC DESKTOP",
                                         font=("Courier New", 10, "bold"),
                                         fg=theme["text_accent"], bg=theme["bg_main"])
        self.intel_mode_label.pack(side="left", padx=10)
        
        # Mode toggle button
        self.intel_mode_btn = tk.Button(controls, text="🔄 SWITCH MODE",
                                        command=self._toggle_intel_mode,
                                        bg=theme["text_accent"], fg="#000000",
                                        font=("Courier New", 9, "bold"),
                                        relief="raised", bd=2, padx=10)
        self.intel_mode_btn.pack(side="left", padx=10)
        
        # Calibrate button
        self.intel_calibrate_btn = tk.Button(controls, text="🎯 CALIBRATE",
                                             command=self._calibrate_radar,
                                             bg="#ff8800", fg="#000000",
                                             font=("Courier New", 9, "bold"),
                                             relief="raised", bd=2, padx=10)
        self.intel_calibrate_btn.pack(side="left", padx=10)
        
        # Mode status display
        self.intel_mode_status = tk.Text(section, bg=theme["bg_main"], fg=theme["text_primary"],
                                         font=("Courier New", 9), height=4, wrap="word",
                                         state="disabled", bd=0)
        self.intel_mode_status.pack(fill="x", padx=5, pady=5)
    
    def _on_intel_tree_click(self, event):
        """Handle double-click on intelligence tree."""
        selection = self.intel_tree.selection()
        if selection:
            item = selection[0]
            values = self.intel_tree.item(item, "values")
            if values and len(values) >= 2:
                ssid = values[1]
                # Find BSSID for this SSID
                for bssid, net in self.networks.items():
                    if net.get("ssid") == ssid:
                        self._show_network_details(bssid)
                        break
    
    def _toggle_intel_mode(self):
        """Toggle radar mode from intelligence core."""
        self._toggle_radar_mode()
        self._update_intelligence_display()
    
    def _calibrate_radar(self):
        """Start radar calibration."""
        if self.radar_system:
            self.radar_system.start_calibration()
            self.log_event("CALIBRATION", "Radar calibration started")
    
    def _update_intelligence_display(self):
        """Update all intelligence core displays."""
        theme = self.ui_themes[self.current_profile]
        pic = self.intelligence_core
        
        # ═══════════════════════════════════════════════════════════════════
        # UPDATE NEW THREE-PANEL DASHBOARD (PRIMARY)
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'intel_dashboard') and self.intel_dashboard:
            self.intel_dashboard.update_from_pic(pic)
            # Dashboard handles its own display, no need for legacy code
            return
        
        # ═══════════════════════════════════════════════════════════════════
        # LEGACY UPDATES (fallback if dashboard not available)
        # ═══════════════════════════════════════════════════════════════════
        if not hasattr(self, 'intel_tree'):
            return
            
        # Clear and update network overview tree
        for item in self.intel_tree.get_children():
            self.intel_tree.delete(item)
        
        for intel in pic.get_all_networks():
            # Security rating color tag
            sec_rating = intel.security.security_rating.value
            spoof = intel.security.spoof_risk.value
            
            self.intel_tree.insert("", "end", values=(
                intel.device_icon,
                intel.ssid or "[Hidden]",
                f"{intel.signal_percent}%",
                intel.device_category.value.replace("_", " ").title(),
                f"{intel.location.estimated_distance_m:.1f}m",
                f"{intel.location.wall_count}",
                intel.temporal.stability_rating.replace("_", " ").title(),
                sec_rating.title(),
                spoof.title(),
                intel.temporal.movement_state.value.replace("_", " ").title()
            ))
        
        # Update fingerprint section
        self._update_intel_fingerprint_display(pic, theme)
        
        # Update distance section
        self._update_intel_distance_display(pic, theme)
        
        # Update temporal section
        self._update_intel_temporal_display(pic, theme)
        
        # Update security section
        self._update_intel_security_display(pic, theme)
        
        # Update relationship section
        self._update_intel_relationship_display(pic, theme)
        
        # Update mode manager
        self._update_intel_mode_display(pic, theme)
    
    def _update_intel_fingerprint_display(self, pic: PassiveIntelligenceCore, theme):
        """Update device fingerprinting section."""
        if not hasattr(self, 'intel_fingerprint_text'):
            return
        
        self.intel_fingerprint_text.config(state="normal")
        self.intel_fingerprint_text.delete(1.0, "end")
        
        device_summary = pic.get_device_summary()
        
        # Header
        self.intel_fingerprint_text.insert("end", "DEVICE TYPE BREAKDOWN:\n", "header")
        
        # Device icons and counts
        icons = {
            'router': '📡', 'mesh_node': '🔗', 'repeater': '🔁', 'hotspot': '📶',
            'iot': '🧠', 'printer': '🖨️', 'smart_tv': '📺', 'gaming': '🎮',
            'enterprise_ap': '🏢', 'unknown': '❓'
        }
        
        line = ""
        count = 0
        for dev_type, num in device_summary.items():
            if num > 0:
                icon = icons.get(dev_type, '❓')
                line += f"  {icon} {dev_type.replace('_', ' ').title()}: {num}  "
                count += 1
                if count % 3 == 0:
                    self.intel_fingerprint_text.insert("end", line + "\n")
                    line = ""
        if line:
            self.intel_fingerprint_text.insert("end", line + "\n")
        
        total = sum(device_summary.values())
        self.intel_fingerprint_text.insert("end", f"\n  TOTAL DEVICES FINGERPRINTED: {total}\n", "count")
        
        self.intel_fingerprint_text.config(state="disabled")
    
    def _update_intel_distance_display(self, pic: PassiveIntelligenceCore, theme):
        """Update distance & direction section."""
        if not hasattr(self, 'intel_distance_canvas'):
            return
        
        canvas = self.intel_distance_canvas
        canvas.delete("all")
        
        width = canvas.winfo_width() or 400
        height = 150
        cx, cy = width // 2, height - 20
        
        # Draw distance rings
        for dist in [5, 15, 30, 50]:
            r = (dist / 50) * (height - 30)
            canvas.create_arc(cx - r, cy - r, cx + r, cy + r, 
                             start=0, extent=180, outline=theme["text_secondary"], dash=(2, 2))
            canvas.create_text(cx + r + 10, cy, text=f"{dist}m", 
                              font=("Courier New", 7), fill=theme["text_secondary"])
        
        # Plot networks by distance and direction
        networks = pic.get_all_networks()[:20]  # Top 20
        for intel in networks:
            dist = min(intel.location.estimated_distance_m, 50)
            angle = math.radians(180 - intel.location.angle_degrees)
            
            r = (dist / 50) * (height - 30)
            x = cx + r * math.cos(angle)
            y = cy - r * math.sin(angle)
            
            # Color by signal strength
            if intel.signal_percent > 70:
                color = "#00ff00"
            elif intel.signal_percent > 40:
                color = "#ffff00"
            else:
                color = "#ff0000"
            
            canvas.create_oval(x-5, y-5, x+5, y+5, fill=color, outline=theme["text_accent"])
            canvas.create_text(x, y-12, text=intel.device_icon, font=("Segoe UI Emoji", 8))
        
        # Update distance text stats
        if hasattr(self, 'intel_distance_text'):
            self.intel_distance_text.config(state="normal")
            self.intel_distance_text.delete(1.0, "end")
            
            if networks:
                closest = min(networks, key=lambda n: n.location.estimated_distance_m)
                farthest = max(networks, key=lambda n: n.location.estimated_distance_m)
                
                self.intel_distance_text.insert("end", f"  CLOSEST: {closest.ssid or '[Hidden]'} @ {closest.location.estimated_distance_m:.1f}m ({closest.location.wall_description})\n")
                self.intel_distance_text.insert("end", f"  FARTHEST: {farthest.ssid or '[Hidden]'} @ {farthest.location.estimated_distance_m:.1f}m ({farthest.location.wall_description})\n")
                self.intel_distance_text.insert("end", f"  NETWORKS IN RANGE: {len(networks)} | CONFIDENCE: {sum(n.location.distance_confidence for n in networks) // max(len(networks), 1)}%\n")
            
            self.intel_distance_text.config(state="disabled")
    
    def _update_intel_temporal_display(self, pic: PassiveIntelligenceCore, theme):
        """Update temporal behaviour section."""
        if not hasattr(self, 'intel_temporal_text'):
            return
        
        self.intel_temporal_text.config(state="normal")
        self.intel_temporal_text.delete(1.0, "end")
        
        networks = pic.get_all_networks()
        
        # Stability summary
        stability_counts = {'rock_solid': 0, 'stable': 0, 'moderate': 0, 'unstable': 0, 'erratic': 0}
        for net in networks:
            rating = net.temporal.stability_rating
            if rating in stability_counts:
                stability_counts[rating] += 1
        
        self.intel_temporal_text.insert("end", "SIGNAL STABILITY SUMMARY:\n", "header")
        self.intel_temporal_text.insert("end", f"  🟢 Rock Solid: {stability_counts['rock_solid']}  ", "stable")
        self.intel_temporal_text.insert("end", f"🟢 Stable: {stability_counts['stable']}  ", "stable")
        self.intel_temporal_text.insert("end", f"🟡 Moderate: {stability_counts['moderate']}\n", "unstable")
        self.intel_temporal_text.insert("end", f"  🟠 Unstable: {stability_counts['unstable']}  ", "unstable")
        self.intel_temporal_text.insert("end", f"🔴 Erratic: {stability_counts['erratic']}\n\n", "erratic")
        
        # Movement summary
        self.intel_temporal_text.insert("end", "MOVEMENT DETECTION:\n", "header")
        moving = [n for n in networks if n.temporal.movement_state.value in ['moving', 'fast_moving']]
        stationary = [n for n in networks if n.temporal.movement_state.value == 'stationary']
        
        self.intel_temporal_text.insert("end", f"  🚶 Moving: {len(moving)}  📍 Stationary: {len(stationary)}\n")
        
        if moving:
            self.intel_temporal_text.insert("end", f"  ⚡ ACTIVE MOVEMENT: ", "header")
            for m in moving[:3]:
                self.intel_temporal_text.insert("end", f"{m.device_icon} {m.ssid or '[Hidden]'}  ")
            self.intel_temporal_text.insert("end", "\n")
        
        # Trend analysis
        self.intel_temporal_text.insert("end", "\nSIGNAL TRENDS:\n", "header")
        improving = len([n for n in networks if n.temporal.signal_trend == 'improving'])
        declining = len([n for n in networks if n.temporal.signal_trend == 'declining'])
        self.intel_temporal_text.insert("end", f"  📈 Improving: {improving}  📉 Declining: {declining}\n")
        
        self.intel_temporal_text.config(state="disabled")
    
    def _update_intel_security_display(self, pic: PassiveIntelligenceCore, theme):
        """Update security intelligence section."""
        if not hasattr(self, 'intel_security_text'):
            return
        
        self.intel_security_text.config(state="normal")
        self.intel_security_text.delete(1.0, "end")
        
        sec_summary = pic.get_security_summary()
        networks = pic.get_all_networks()
        
        # Security ratings
        self.intel_security_text.insert("end", "SECURITY RATING BREAKDOWN:\n", "header")
        self.intel_security_text.insert("end", f"  🟢 EXCELLENT (WPA3): {sec_summary.get('excellent', 0)}\n", "excellent")
        self.intel_security_text.insert("end", f"  🟢 GOOD (WPA2-Enterprise): {sec_summary.get('good', 0)}\n", "good")
        self.intel_security_text.insert("end", f"  🟡 MODERATE (WPA2-PSK): {sec_summary.get('moderate', 0)}\n", "moderate")
        self.intel_security_text.insert("end", f"  🟠 WEAK (WPA-PSK): {sec_summary.get('weak', 0)}\n", "weak")
        self.intel_security_text.insert("end", f"  🔴 CRITICAL (WEP/Open): {sec_summary.get('critical', 0)}\n", "critical")
        
        # Security Upgrade Advisory
        wpa3_count = sec_summary.get('excellent', 0)
        wpa2_count = sec_summary.get('moderate', 0) + sec_summary.get('good', 0)
        critical_count = sec_summary.get('critical', 0)
        
        self.intel_security_text.insert("end", "\n📋 SECURITY UPGRADE ADVISORY:\n", "header")
        if wpa3_count == 0 and wpa2_count > 0:
            self.intel_security_text.insert("end", "  ⚠️ No WPA3 networks detected.\n", "weak")
            self.intel_security_text.insert("end", "  💡 Consider upgrading routers for stronger encryption.\n", "moderate")
        elif wpa3_count > 0:
            self.intel_security_text.insert("end", f"  ✅ {wpa3_count} network(s) using modern WPA3 encryption.\n", "excellent")
        
        if critical_count > 0:
            self.intel_security_text.insert("end", f"  🚨 {critical_count} network(s) using CRITICAL security!\n", "critical")
            self.intel_security_text.insert("end", "  💡 WEP/Open networks are easily compromised.\n", "critical")
        
        # Spoof alerts with detailed breakdown
        spoof_alerts = pic.get_spoof_alerts()
        if spoof_alerts:
            self.intel_security_text.insert("end", f"\n⚠️ SPOOF/ROGUE DETECTION ({len(spoof_alerts)} ALERTS):\n", "spoof_alert")
            for alert in spoof_alerts[:5]:
                ssid_display = alert.ssid if alert.ssid else "[Hidden SSID]"
                self.intel_security_text.insert("end", f"\n  ⚡ {ssid_display} ({alert.bssid[:8]}...):\n", "spoof_alert")
                
                # Show spoof indicators
                for indicator in alert.security.spoof_indicators[:3]:
                    self.intel_security_text.insert("end", f"     • {indicator}\n", "weak")
                
                # Show spoof risk score breakdown
                risk_score = 0.0
                risk_factors = []
                
                # Vendor analysis
                if alert.vendor == "Unknown":
                    risk_score += 0.2
                    risk_factors.append("Unknown vendor (+0.2)")
                
                # Signal volatility
                if alert.temporal.stability_rating in ['unstable', 'erratic']:
                    risk_score += 0.3
                    risk_factors.append(f"Signal {alert.temporal.stability_rating} (+0.3)")
                
                # Multiple APs with same SSID
                if alert.security.similar_ssid_count > 1:
                    risk_score += 0.2
                    risk_factors.append(f"{alert.security.similar_ssid_count} APs same SSID (+0.2)")
                
                # Hidden SSID with alerts
                if alert.security.is_hidden:
                    risk_score += 0.15
                    risk_factors.append("Hidden SSID (+0.15)")
                
                # Signal anomaly indicators
                if alert.temporal.signal_trend == 'erratic':
                    risk_score += 0.15
                    risk_factors.append("Erratic signal trend (+0.15)")
                
                self.intel_security_text.insert("end", f"     📊 Risk Score: {min(risk_score, 1.0):.2f}\n", 
                                               "critical" if risk_score > 0.5 else "weak")
                
                # Temporal details
                self.intel_security_text.insert("end", f"     📈 Trend: {alert.temporal.signal_trend} | ", "moderate")
                self.intel_security_text.insert("end", f"Volatility: {alert.temporal.long_term_volatility:.1f}% | ", "moderate")
                self.intel_security_text.insert("end", f"Stability: {alert.temporal.stability_score}%\n", "moderate")
                
                # Channel info
                self.intel_security_text.insert("end", f"     📡 Channel: {alert.channel} ({alert.band}) | ", "moderate")
                self.intel_security_text.insert("end", f"Signal: {alert.signal_percent}%\n", "moderate")
        else:
            self.intel_security_text.insert("end", "\n✅ NO SPOOF/ROGUE ALERTS\n", "excellent")
        
        # Vulnerabilities
        vuln_count = sum(len(n.security.vulnerabilities) for n in networks)
        if vuln_count > 0:
            self.intel_security_text.insert("end", f"\n⚠️ VULNERABILITIES DETECTED: {vuln_count}\n", "critical")
            shown = 0
            for net in networks:
                for vuln in net.security.vulnerabilities:
                    if shown < 5:
                        self.intel_security_text.insert("end", f"  • {net.ssid or net.bssid}: {vuln}\n", "weak")
                        shown += 1
        
        self.intel_security_text.config(state="disabled")
    
    def _update_intel_relationship_display(self, pic: PassiveIntelligenceCore, theme):
        """Update relationship mapping section."""
        if not hasattr(self, 'intel_relationship_canvas'):
            return
        
        canvas = self.intel_relationship_canvas
        canvas.delete("all")
        
        width = canvas.winfo_width() or 400
        height = 180
        
        # Get mesh groups and relationships
        mesh_groups = pic.get_mesh_groups()
        networks = pic.get_all_networks()
        
        # Draw relationship graph
        if mesh_groups:
            y_offset = 30
            for mesh_id, members in list(mesh_groups.items())[:3]:
                # Draw mesh group box
                canvas.create_rectangle(20, y_offset, width-20, y_offset+40,
                                       outline=theme["text_accent"], dash=(2, 2))
                canvas.create_text(30, y_offset+5, text=f"🔗 MESH: {mesh_id[:30]}",
                                  font=("Courier New", 8, "bold"), fill=theme["text_accent"], anchor="nw")
                
                # Draw member nodes
                x_pos = 50
                for i, bssid in enumerate(members[:5]):
                    intel = pic.get_network(bssid)
                    if intel:
                        canvas.create_oval(x_pos-8, y_offset+20, x_pos+8, y_offset+36,
                                          fill=theme["text_accent"], outline="#ffffff")
                        canvas.create_text(x_pos, y_offset+28, text=intel.device_icon,
                                          font=("Segoe UI Emoji", 8))
                        
                        if i < len(members) - 1:
                            canvas.create_line(x_pos+8, y_offset+28, x_pos+42, y_offset+28,
                                             fill=theme["text_secondary"], dash=(1, 1))
                        x_pos += 50
                
                y_offset += 50
        else:
            canvas.create_text(width//2, height//2, text="No mesh/cluster relationships detected",
                              font=("Courier New", 9), fill=theme["text_secondary"])
        
        # Update relationship text
        if hasattr(self, 'intel_relationship_text'):
            self.intel_relationship_text.config(state="normal")
            self.intel_relationship_text.delete(1.0, "end")
            
            mesh_count = len(mesh_groups)
            repeaters = len([n for n in networks if n.relationships.is_repeater])
            guests = len([n for n in networks if n.relationships.is_guest_network])
            
            self.intel_relationship_text.insert("end", f"  MESH GROUPS: {mesh_count}  |  REPEATERS: {repeaters}  |  GUEST NETWORKS: {guests}\n")
            self.intel_relationship_text.insert("end", f"  MULTI-BSSID CLUSTERS: {len([n for n in networks if n.relationships.is_multi_bssid])}\n")
            
            self.intel_relationship_text.config(state="disabled")
    
    def _update_intel_mode_display(self, pic: PassiveIntelligenceCore, theme):
        """Update mode manager section."""
        if not hasattr(self, 'intel_mode_label'):
            return
        
        mode_status = pic.get_mode_status()
        mode = mode_status.get('mode', 'static')
        
        if mode == 'mobile':
            self.intel_mode_label.config(text="CURRENT MODE: 📱 MOBILE HOMING",
                                        fg="#ff00ff")
            self.intel_mode_btn.config(text="🔄 SWITCH TO STATIC")
        else:
            self.intel_mode_label.config(text="CURRENT MODE: 🖥️ STATIC DESKTOP",
                                        fg="#00ff88")
            self.intel_mode_btn.config(text="🔄 SWITCH TO MOBILE")
        
        # Update status text
        if hasattr(self, 'intel_mode_status'):
            self.intel_mode_status.config(state="normal")
            self.intel_mode_status.delete(1.0, "end")
            
            self.intel_mode_status.insert("end", f"  MODE: {mode.upper()}\n")
            self.intel_mode_status.insert("end", f"  GYROSCOPE: {'✅ Available' if mode_status.get('has_gyroscope') else '❌ Not Available'}\n")
            self.intel_mode_status.insert("end", f"  MULTI-ANTENNA: {'✅ Available' if mode_status.get('has_multi_antenna') else '❌ Not Available'}\n")
            self.intel_mode_status.insert("end", f"  CALIBRATING: {'⏳ Yes' if mode_status.get('is_calibrating') else '✅ No'}\n")
            
            self.intel_mode_status.config(state="disabled")

    def _build_statistics_view(self, parent):
        """Build the statistics view."""
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side="right", fill="y")
        
        self.stats_text = tk.Text(parent, bg="#0a0e27", fg="#00ff00",
                                  yscrollcommand=scrollbar.set,
                                  font=("Courier New", 9), wrap="word",
                                  state="disabled")
        self.stats_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.stats_text.yview)
        
        # Tags
        self.stats_text.tag_config("header", foreground="#00ffff", font=("Courier New", 10, "bold"))
        self.stats_text.tag_config("subheader", foreground="#ff00ff", font=("Courier New", 9, "bold"))
        self.stats_text.tag_config("secure", foreground="#00ff00")
        self.stats_text.tag_config("warning", foreground="#ffff00")
        self.stats_text.tag_config("critical", foreground="#ff0000")
    
    def _build_vulnerability_view(self, parent):
        """Build the vulnerability analysis view."""
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side="right", fill="y")
        
        self.vuln_text = tk.Text(parent, bg="#0a0e27", fg="#00ff00",
                                 yscrollcommand=scrollbar.set,
                                 font=("Courier New", 8), wrap="word",
                                 state="disabled")
        self.vuln_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.vuln_text.yview)
        
        # Tags
        self.vuln_text.tag_config("header", foreground="#ff0000", font=("Courier New", 10, "bold"))
        self.vuln_text.tag_config("critical", foreground="#ff0000", font=("Courier New", 9, "bold"))
        self.vuln_text.tag_config("warning", foreground="#ffff00")
        self.vuln_text.tag_config("info", foreground="#00ffff")
        self.vuln_text.tag_config("secure", foreground="#00ff00")
    
    def _build_event_log(self, parent):
        """Build the event log view."""
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side="right", fill="y")
        
        self.event_display = tk.Text(parent, bg="#0a0e27", fg="#00ff00",
                                     yscrollcommand=scrollbar.set,
                                     font=("Courier New", 8), wrap="word",
                                     state="disabled")
        self.event_display.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.event_display.yview)
        
        # Tags
        self.event_display.tag_config("header", foreground="#00ffff", font=("Courier New", 9, "bold"))
        self.event_display.tag_config("warning", foreground="#ffff00")
        self.event_display.tag_config("critical", foreground="#ff0000")
        self.event_display.tag_config("info", foreground="#00ff00")
    
    def _build_spectrogram_view(self, parent):
        """Build the signal spectrogram waterfall display."""
        theme = self.ui_themes[self.current_profile]
        
        # Control bar
        ctrl_frame = tk.Frame(parent, bg=theme["bg_panel"])
        ctrl_frame.pack(fill="x", padx=3, pady=3)
        
        tk.Label(ctrl_frame, text="║ 🌊 SIGNAL SPECTROGRAM // TEMPORAL WATERFALL ANALYSIS ║",
                 font=("Courier New", 10, "bold"), fg=theme["text_secondary"],
                 bg=theme["bg_panel"]).pack(side="left", padx=5)
        
        tk.Label(ctrl_frame, text="NETWORK:", font=("Courier New", 9, "bold"),
                 fg=theme["text_accent"], bg=theme["bg_panel"]).pack(side="left", padx=(20, 5))
        
        self.spectro_network_select = ttk.Combobox(ctrl_frame, state="readonly", width=25)
        self.spectro_network_select.pack(side="left", padx=5)
        self.spectro_network_select.set("[ ALL NETWORKS ]")
        self.spectro_network_select.bind("<<ComboboxSelected>>", self._on_spectro_network_change)
        
        tk.Label(ctrl_frame, text="TIME:", font=("Courier New", 9, "bold"),
                 fg=theme["text_accent"], bg=theme["bg_panel"]).pack(side="left", padx=(20, 5))
        
        self.spectro_time_var = tk.StringVar(value="60s")
        for t in ["30s", "60s", "120s"]:
            tk.Radiobutton(ctrl_frame, text=t, variable=self.spectro_time_var, value=t,
                          bg=theme["bg_panel"], fg=theme["text_primary"],
                          selectcolor=theme["bg_main"], activebackground=theme["bg_panel"],
                          command=self._on_spectro_time_change).pack(side="left", padx=3)
        
        # Legend
        legend_frame = tk.Frame(parent, bg=theme["bg_main"])
        legend_frame.pack(fill="x", padx=3)
        
        tk.Label(legend_frame, text="SIGNAL: ", font=("Courier New", 8, "bold"),
                 fg=theme["text_secondary"], bg=theme["bg_main"]).pack(side="left", padx=5)
        
        legend_colors = [("EXCELLENT", "#00ff00"), ("GOOD", "#00ffff"), 
                        ("FAIR", "#ffff00"), ("WEAK", "#ff0088"), ("CRITICAL", "#ff0000")]
        for label, color in legend_colors:
            tk.Label(legend_frame, text=f"■ {label}", font=("Courier New", 8),
                     fg=color, bg=theme["bg_main"]).pack(side="left", padx=8)
        
        # Main spectrogram canvas
        self.spectro_canvas = tk.Canvas(parent, bg="#050510", highlightthickness=0)
        self.spectro_canvas.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Time axis label
        self.spectro_time_label = tk.Label(parent, text="◄ NOW ─────────────────────────────────────────── PAST ►",
                                           font=("Courier New", 9, "bold"),
                                           fg=theme["text_accent"], bg=theme["bg_main"])
        self.spectro_time_label.pack(pady=3)
    
    def _on_spectro_network_change(self, event=None):
        """Handle spectrogram network selection."""
        selected = self.spectro_network_select.get()
        if selected == "[ ALL NETWORKS ]":
            self.spectrogram_selected = "all"
        else:
            # Find BSSID by SSID
            for bssid, data in self.networks.items():
                if data['ssid'] == selected:
                    self.spectrogram_selected = bssid
                    break
    
    def _on_spectro_time_change(self):
        """Handle time window change."""
        time_str = self.spectro_time_var.get()
        self.spectrogram_max_seconds = int(time_str.replace('s', ''))
    
    def _build_hidden_diagnostics(self, parent):
        """Build the Hidden Network Diagnostics panel."""
        theme = self.ui_themes[self.current_profile]
        
        # Header
        header_frame = tk.Frame(parent, bg=theme["bg_panel"])
        header_frame.pack(fill="x", padx=3, pady=3)
        
        tk.Label(header_frame, text="║ 👁️ HIDDEN NETWORK CLASSIFICATION ENGINE (HNCE) // 100% PASSIVE ║",
                 font=("Courier New", 10, "bold"), fg=theme["text_secondary"],
                 bg=theme["bg_panel"]).pack(side="left", padx=5)
        
        # Summary stats bar
        self.hidden_summary_frame = tk.Frame(parent, bg=theme["bg_main"])
        self.hidden_summary_frame.pack(fill="x", padx=3, pady=3)
        
        # Create stat labels
        stats = [
            ("HIDDEN APs:", "hidden_count", "#ff00ff"),
            ("CLUSTERS:", "cluster_count", "#00ffff"),
            ("MESH:", "mesh_count", "#00ff00"),
            ("ENTERPRISE:", "enterprise_count", "#0088ff"),
            ("BACKHAUL:", "backhaul_count", "#ffff00"),
            ("🚨 ROGUE:", "rogue_count", "#ff0000"),
            ("⚠️ SPOOF:", "spoof_count", "#ff6600")
        ]
        
        self.hidden_stat_labels = {}
        for label_text, key, color in stats:
            tk.Label(self.hidden_summary_frame, text=label_text, font=("Courier New", 9, "bold"),
                     fg=theme["text_secondary"], bg=theme["bg_main"]).pack(side="left", padx=5)
            lbl = tk.Label(self.hidden_summary_frame, text="0", font=("Courier New", 10, "bold"),
                          fg=color, bg=theme["bg_main"], width=3)
            lbl.pack(side="left", padx=2)
            self.hidden_stat_labels[key] = lbl
        
        # Main content - split into two panes
        paned = tk.PanedWindow(parent, orient="horizontal", bg=theme["bg_main"], sashwidth=5)
        paned.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Left pane - Hidden network list
        left_frame = tk.Frame(paned, bg=theme["bg_panel"])
        paned.add(left_frame, width=400)
        
        tk.Label(left_frame, text="╔══ HIDDEN NETWORKS ══╗",
                 font=("Courier New", 9, "bold"), fg=theme["text_accent"],
                 bg=theme["bg_panel"]).pack(fill="x", padx=3, pady=3)
        
        # Hidden network treeview
        columns = ("bssid", "vendor", "channel", "rssi", "type", "score", "flags")
        self.hidden_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        
        self.hidden_tree.heading("bssid", text="BSSID")
        self.hidden_tree.heading("vendor", text="VENDOR")
        self.hidden_tree.heading("channel", text="CH")
        self.hidden_tree.heading("rssi", text="RSSI")
        self.hidden_tree.heading("type", text="CLASSIFICATION")
        self.hidden_tree.heading("score", text="ROGUE%")
        self.hidden_tree.heading("flags", text="FLAGS")
        
        self.hidden_tree.column("bssid", width=120)
        self.hidden_tree.column("vendor", width=100)
        self.hidden_tree.column("channel", width=40)
        self.hidden_tree.column("rssi", width=50)
        self.hidden_tree.column("type", width=110)
        self.hidden_tree.column("score", width=55)
        self.hidden_tree.column("flags", width=75)
        
        hidden_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.hidden_tree.yview)
        self.hidden_tree.configure(yscrollcommand=hidden_scroll.set)
        
        self.hidden_tree.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        hidden_scroll.pack(side="right", fill="y")
        
        self.hidden_tree.bind("<<TreeviewSelect>>", self._on_hidden_select)
        
        # Right pane - Details and clusters
        right_frame = tk.Frame(paned, bg=theme["bg_panel"])
        paned.add(right_frame, width=400)
        
        # Details section
        tk.Label(right_frame, text="╔══ PROFILE DETAILS ══╗",
                 font=("Courier New", 9, "bold"), fg=theme["text_accent"],
                 bg=theme["bg_panel"]).pack(fill="x", padx=3, pady=3)
        
        self.hidden_detail_text = tk.Text(right_frame, height=10, bg="#0a0a15", fg=theme["text_primary"],
                                          font=("Courier New", 9), insertbackground=theme["text_accent"],
                                          relief="sunken", bd=2, wrap="word")
        self.hidden_detail_text.pack(fill="x", padx=3, pady=3)
        self.hidden_detail_text.insert("1.0", "[ Select a hidden network to view details ]")
        self.hidden_detail_text.config(state="disabled")
        
        # Clusters section
        tk.Label(right_frame, text="╔══ CLUSTER GROUPS ══╗",
                 font=("Courier New", 9, "bold"), fg=theme["text_accent"],
                 bg=theme["bg_panel"]).pack(fill="x", padx=3, pady=3)
        
        cluster_columns = ("cluster_id", "type", "members", "risk")
        self.cluster_tree = ttk.Treeview(right_frame, columns=cluster_columns, show="headings", height=8)
        
        self.cluster_tree.heading("cluster_id", text="CLUSTER")
        self.cluster_tree.heading("type", text="TYPE")
        self.cluster_tree.heading("members", text="MEMBERS")
        self.cluster_tree.heading("risk", text="RISK")
        
        self.cluster_tree.column("cluster_id", width=100)
        self.cluster_tree.column("type", width=100)
        self.cluster_tree.column("members", width=60)
        self.cluster_tree.column("risk", width=80)
        
        cluster_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.cluster_tree.yview)
        self.cluster_tree.configure(yscrollcommand=cluster_scroll.set)
        
        self.cluster_tree.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        cluster_scroll.pack(side="right", fill="y")
    
    def _on_hidden_select(self, event=None):
        """Handle hidden network selection."""
        selection = self.hidden_tree.selection()
        if not selection:
            return
        
        item = self.hidden_tree.item(selection[0])
        bssid = item['values'][0] if item['values'] else None
        
        if not bssid:
            return
        
        profile = self.hidden_classifier.get_profile(bssid)
        if not profile:
            return
        
        # Update detail text
        theme = self.ui_themes[self.current_profile]
        self.hidden_detail_text.config(state="normal")
        self.hidden_detail_text.delete("1.0", "end")
        
        details = [
            f"╔════════════════════════════════════════╗",
            f"  BSSID: {profile.bssid}",
            f"  OUI: {profile.oui}  |  Vendor: {profile.vendor or 'Unknown'}",
            f"  Channel: {profile.channel} ({profile.band})",
            f"  RSSI: {profile.rssi} dBm",
            f"  Security: {profile.security or 'Unknown'}",
            f"╠════════════════════════════════════════╣",
            f"  CLASSIFICATION: {profile.network_type.value.upper()}",
            f"  Confidence: {profile.classification_confidence}%",
            f"  Reason: {profile.classification_reason}",
            f"╠════════════════════════════════════════╣",
            f"  SCORES:",
            f"    OUI Consistency: {profile.oui_consistency_score:.1f}%",
            f"    Channel Coherence: {profile.channel_coherence_score:.1f}%",
            f"    Signal Grouping: {profile.signal_grouping_score:.1f}%",
            f"    Rogue Likelihood: {profile.rogue_likelihood_score:.1f}%",
            f"╠════════════════════════════════════════╣",
            f"  FLAGS:",
            f"    Rogue Candidate: {'⚠️ YES' if profile.is_rogue_candidate else 'No'}",
            f"    Spoof Candidate: {'🚨 YES' if profile.is_spoof_candidate else 'No'}",
            f"    Outlier: {'⚡ YES' if profile.is_outlier else 'No'}",
            f"╠════════════════════════════════════════╣",
            f"  TEMPORAL:",
            f"    First Seen: {time.strftime('%H:%M:%S', time.localtime(profile.first_seen))}",
            f"    Last Seen: {time.strftime('%H:%M:%S', time.localtime(profile.last_seen))}",
            f"    Observations: {profile.observation_count}",
            f"    Stability: {profile.stability_score:.1f}%",
            f"╚════════════════════════════════════════╝",
        ]
        
        if profile.related_bssids:
            details.append(f"  RELATED: {', '.join(profile.related_bssids[:3])}")
        
        self.hidden_detail_text.insert("1.0", "\n".join(details))
        self.hidden_detail_text.config(state="disabled")
    
    def _update_hidden_diagnostics(self):
        """Update the Hidden Network Diagnostics panel."""
        if not hasattr(self, 'hidden_tree'):
            return
        
        # Get analysis summary
        summary = self.hidden_classifier.get_summary()
        
        # Update summary labels
        if hasattr(self, 'hidden_stat_labels'):
            self.hidden_stat_labels['hidden_count'].config(text=str(summary.get('hidden_count', 0)))
            self.hidden_stat_labels['cluster_count'].config(text=str(summary.get('cluster_count', 0)))
            self.hidden_stat_labels['mesh_count'].config(text=str(summary.get('mesh_count', 0)))
            self.hidden_stat_labels['enterprise_count'].config(text=str(summary.get('enterprise_count', 0)))
            self.hidden_stat_labels['backhaul_count'].config(text=str(summary.get('backhaul_count', 0)))
            self.hidden_stat_labels['rogue_count'].config(text=str(summary.get('rogue_candidates', 0)))
            self.hidden_stat_labels['spoof_count'].config(text=str(summary.get('spoof_candidates', 0)))
        
        # Update hidden network tree
        for item in self.hidden_tree.get_children():
            self.hidden_tree.delete(item)
        
        profiles = self.hidden_classifier.get_all_profiles()
        for profile in sorted(profiles, key=lambda p: -p.rogue_likelihood_score):
            flags = []
            if profile.is_rogue_candidate:
                flags.append("🚨ROGUE")
            if profile.is_spoof_candidate:
                flags.append("⚠️SPOOF")
            if profile.is_outlier:
                flags.append("⚡OUT")
            if profile.is_randomized_mac:
                flags.append("🎲RAND")
            
            # Vendor display with OUI-IM intelligence
            vendor_display = self._get_smart_vendor_display(
                profile.vendor or "Unknown",
                profile.vendor_type,
                profile.is_randomized_mac,
                max_len=12
            )
            
            self.hidden_tree.insert("", "end", values=(
                profile.bssid,
                vendor_display,
                profile.channel,
                f"{profile.rssi}dBm",
                profile.network_type.value[:12],
                f"{profile.rogue_likelihood_score:.0f}%",
                " ".join(flags) if flags else "—"
            ))
        
        # Update cluster tree
        for item in self.cluster_tree.get_children():
            self.cluster_tree.delete(item)
        
        for cluster in self.hidden_classifier.clusters.values():
            risk_str = cluster.rogue_risk.name if hasattr(cluster.rogue_risk, 'name') else "NONE"
            self.cluster_tree.insert("", "end", values=(
                cluster.cluster_id[:15],
                cluster.cluster_type.value[:12],
                len(cluster.members),
                risk_str
            ))
    
    def _build_theme_selector(self):
        """Build theme selector row."""
        theme = self.ui_themes[self.current_profile]
        
        theme_row = tk.Frame(self.root, bg=theme["bg_main"], relief="raised", bd=2)
        theme_row.pack(fill="x", padx=3, pady=2)
        
        tk.Label(theme_row, text="🎨 THEME:", font=("Courier New", 8, "bold"),
                 fg=theme["text_secondary"], bg=theme["bg_main"]).pack(side="left", padx=5)
        
        profiles = [
            ("GREEN", "neon_green", "#00ff00"),
            ("CYAN", "neon_cyan", "#00ffff"),
            ("PURPLE", "neon_purple", "#ff00ff"),
            ("RED", "neon_red", "#ff0000"),
            ("PINK", "neon_pink", "#ff0088"),
            ("PRO", "sleek_pro", "#00ccff"),
            ("PIP-BOY", "pipboy", "#20ff4b")
        ]
        
        self.profile_buttons = {}
        for btn_text, profile_id, color in profiles:
            btn = tk.Button(theme_row, text=btn_text, 
                           command=lambda p=profile_id: self._apply_profile(p),
                           bg=color, fg="#000000", font=("Courier New", 7, "bold"),
                           relief="raised", bd=2, padx=4, pady=1)
            btn.pack(side="left", padx=2, pady=2)
            self.profile_buttons[profile_id] = btn
        
        # Highlight current
        self.profile_buttons["neon_green"].config(relief="sunken", bd=3)
        
        # Audio controls on right
        tk.Label(theme_row, text="║", font=("Courier New", 10),
                 fg=theme["text_accent"], bg=theme["bg_main"]).pack(side="left", padx=10)
        
        tk.Label(theme_row, text="🌊 INTENSITY:", font=("Courier New", 8, "bold"),
                 fg=theme["text_secondary"], bg=theme["bg_main"]).pack(side="left", padx=5)
        
        self.wave_slider = ttk.Scale(theme_row, from_=0, to=100, orient="horizontal",
                                     command=self._set_wave_intensity, length=100)
        self.wave_slider.set(50)
        self.wave_slider.pack(side="left", padx=5)
        
        self.wave_label = tk.Label(theme_row, text="50%", font=("Courier New", 8, "bold"),
                                   fg=theme["text_accent"], bg=theme["bg_main"], width=4)
        self.wave_label.pack(side="left")
        
        # Mute button
        self.btn_mute = tk.Button(theme_row, text="🔊 MUTE", command=self._toggle_mute,
                                  bg="#ff6600", fg="#000000", font=("Courier New", 8, "bold"),
                                  relief="raised", bd=2, padx=5)
        self.btn_mute.pack(side="left", padx=10)
    
    def _build_controls(self):
        """Build control panel."""
        theme = self.ui_themes[self.current_profile]
        
        self.ctrl_frame = tk.Frame(self.root, bg=theme["bg_main"], relief="raised", bd=2)
        self.ctrl_frame.pack(fill="x", padx=3, pady=3)
        
        # Left side - scan controls
        left_frame = tk.Frame(self.ctrl_frame, bg=theme["bg_main"])
        left_frame.pack(side="left", padx=5, pady=5)
        
        self.btn_start = tk.Button(left_frame, text="▶ INITIATE", command=self._start_scan,
                                   bg="#00ff00", fg="#000000", font=("Courier New", 10, "bold"),
                                   relief="raised", bd=2, padx=10, pady=5)
        self.btn_start.pack(side="left", padx=3)
        
        self.btn_stop = tk.Button(left_frame, text="⏹ HALT", command=self._stop_scan,
                                  bg="#ff0088", fg="#000000", font=("Courier New", 10, "bold"),
                                  relief="raised", bd=2, padx=10, pady=5, state="disabled")
        self.btn_stop.pack(side="left", padx=3)
        
        # Extended scan toggle for weak signals
        self.btn_extended = tk.Button(left_frame, text="📡 EXTENDED", command=self._toggle_extended_scan,
                                      bg="#444444", fg="#ffffff", font=("Courier New", 9, "bold"),
                                      relief="raised", bd=2, padx=8, pady=5)
        self.btn_extended.pack(side="left", padx=3)
        
        # Weak signal indicator
        self.weak_signal_label = tk.Label(left_frame, text="", font=("Courier New", 8),
                                          fg="#888888", bg=theme["bg_main"])
        self.weak_signal_label.pack(side="left", padx=5)
        
        # Middle - export and reset
        mid_frame = tk.Frame(self.ctrl_frame, bg=theme["bg_main"])
        mid_frame.pack(side="left", padx=20, pady=5)
        
        tk.Button(mid_frame, text="💾 EXPORT", command=self._export_results,
                  bg="#00ffff", fg="#000000", font=("Courier New", 10, "bold"),
                  relief="raised", bd=2, padx=8).pack(side="left", padx=3)
        
        tk.Button(mid_frame, text="⟲ RESET", command=self._clear_data,
                  bg="#ffff00", fg="#000000", font=("Courier New", 10, "bold"),
                  relief="raised", bd=2, padx=8).pack(side="left", padx=3)
        
        tk.Button(mid_frame, text="🛡️ SECURITY REPORT", command=self._export_security_report,
                  bg="#ff6600", fg="#000000", font=("Courier New", 10, "bold"),
                  relief="raised", bd=2, padx=8).pack(side="left", padx=3)
        
        # EASM Emergency Switch (flip-cover style)
        self._build_easm_switch(mid_frame)
        
        # Right side - hydrophone selector
        right_frame = tk.Frame(self.ctrl_frame, bg=theme["bg_panel"])
        right_frame.pack(side="right", padx=5, pady=5)
        
        tk.Label(right_frame, text="🎧 HYDROPHONE:", font=("Courier New", 9, "bold"),
                 fg="#00ff88", bg=theme["bg_panel"]).pack(side="left", padx=5)
        
        self.network_select = ttk.Combobox(right_frame, state="readonly", width=20)
        self.network_select.pack(side="left", padx=5)
        self.network_select.bind("<<ComboboxSelected>>", self._on_network_selected)
        
        self.audio_status = tk.Label(right_frame, text="[SILENT]", font=("Courier New", 9, "bold"),
                                     fg="#00ff00", bg=theme["bg_panel"], width=12)
        self.audio_status.pack(side="left", padx=5)
    
    def _build_status_bar(self):
        """Build status bar."""
        theme = self.ui_themes[self.current_profile]
        
        self.status_frame = tk.Frame(self.root, bg=theme["bg_panel"], relief="raised", bd=2)
        self.status_frame.pack(fill="x", side="bottom", padx=3, pady=3)
        
        # Top row with version and status
        top_row = tk.Frame(self.status_frame, bg=theme["bg_panel"])
        top_row.pack(fill="x")
        
        tk.Label(top_row, text="║ ⚙ NEXUS v2.0 STATUS TERMINAL ║",
                 font=("Courier New", 9, "bold"), fg=theme["text_accent"],
                 bg=theme["bg_panel"]).pack(side="left", padx=5)
        
        # Engine status indicators
        engines_frame = tk.Frame(top_row, bg=theme["bg_panel"])
        engines_frame.pack(side="right", padx=10)
        
        engines = [("UWM-X", "#00ff00"), ("PIC", "#00ffff"), ("HNCE", "#ff00ff"), ("OUI-IM", "#ff8800"), ("SONAR", "#ffff00")]
        for engine, color in engines:
            tk.Label(engines_frame, text=f"●{engine}", font=("Courier New", 7, "bold"),
                    fg=color, bg=theme["bg_panel"]).pack(side="left", padx=3)
        
        self.status_label = tk.Label(self.status_frame, text="[READY] v2.0 Intelligence Platform Initialized...",
                                     font=("Courier New", 10, "bold"),
                                     fg=theme["text_primary"], bg=theme["bg_panel"])
        self.status_label.pack(anchor="w", padx=10)
        
        self.stats_label = tk.Label(self.status_frame, text="NETWORKS: 0 | SCANS: 0 | MODE: PASSIVE",
                                    font=("Courier New", 9),
                                    fg=theme["text_secondary"], bg=theme["bg_panel"])
        self.stats_label.pack(anchor="w", padx=10, pady=3)
    
    def _build_easm_switch(self, parent):
        """
        Build the EASM (Enhanced Active Scan Mode) emergency switch.
        
        This is a flip-cover style button like a missile launch switch:
        1. First click opens the safety cover (reveals the red button)
        2. Second click arms the system (button glows)
        3. Third click activates EASM
        
        The cover auto-closes after 10 seconds if not activated.
        """
        theme = self.ui_themes[self.current_profile]
        
        # Container frame with industrial styling
        self.easm_container = tk.Frame(parent, bg="#1a1a1a", relief="ridge", bd=3)
        self.easm_container.pack(side="left", padx=15)
        
        # Warning label above
        tk.Label(self.easm_container, text="⚠ ACTIVE SCAN", font=("Courier New", 6, "bold"),
                 fg="#ffcc00", bg="#1a1a1a").pack(pady=(2, 0))
        
        # The switch housing (contains cover and button)
        self.easm_housing = tk.Frame(self.easm_container, bg="#2a2a2a", relief="sunken", bd=2)
        self.easm_housing.pack(padx=5, pady=3)
        
        # Safety cover (yellow/black hazard stripes simulated)
        self.easm_cover = tk.Button(
            self.easm_housing,
            text="╔══════╗\n║COVER ║\n║CLOSED║\n╚══════╝",
            font=("Courier New", 7, "bold"),
            fg="#000000",
            bg="#ffcc00",
            activebackground="#ffdd44",
            relief="raised",
            bd=3,
            command=self._easm_open_cover,
            width=8,
            height=4
        )
        self.easm_cover.pack(padx=3, pady=3)
        
        # The actual red button (hidden behind cover initially)
        self.easm_button = tk.Button(
            self.easm_housing,
            text="EASM\nOFF",
            font=("Courier New", 8, "bold"),
            fg="#ffffff",
            bg="#660000",
            activebackground="#880000",
            relief="raised",
            bd=4,
            command=self._easm_toggle,
            width=8,
            height=3,
            state="disabled"
        )
        # Don't pack yet - it's hidden behind the cover
        
        # Status indicator LED
        self.easm_led = tk.Label(self.easm_container, text="●", font=("Courier New", 10),
                                  fg="#333333", bg="#1a1a1a")
        self.easm_led.pack(pady=(0, 2))
        
        # Auto-close timer ID
        self.easm_cover_timer = None
    
    def _easm_open_cover(self):
        """Open the safety cover to reveal the EASM button."""
        if self.easm_cover_open:
            return
        
        self.easm_cover_open = True
        
        # Animate cover opening
        self.easm_cover.config(
            text="╔══════╗\n║ OPEN ║\n║  ▼▼  ║\n╚══════╝",
            bg="#888800",
            relief="flat"
        )
        
        # Move cover to the side and show the red button
        self.easm_cover.pack_forget()
        self.easm_button.pack(padx=3, pady=3)
        self.easm_button.config(state="normal")
        
        # Show cover as "opened" overlay to the side
        self.easm_cover.config(
            text="◄╗\n ║\n ║\n◄╝",
            width=2
        )
        self.easm_cover.pack(side="left", padx=1)
        
        # LED turns yellow (armed/ready)
        self.easm_led.config(fg="#ffcc00")
        
        # Log the action
        self.log_event("EASM", "⚠ Safety cover OPENED - Active scan available")
        
        # Start auto-close timer (10 seconds)
        if self.easm_cover_timer:
            self.root.after_cancel(self.easm_cover_timer)
        self.easm_cover_timer = self.root.after(10000, self._easm_auto_close)
    
    def _easm_auto_close(self):
        """Auto-close the cover if EASM wasn't activated."""
        if self.easm_cover_open and not self.easm_enabled:
            self._easm_close_cover()
            self.log_event("EASM", "Safety cover auto-closed (timeout)")
    
    def _easm_close_cover(self):
        """Close the safety cover."""
        if not self.easm_cover_open:
            return
        
        self.easm_cover_open = False
        
        # Hide button, show cover
        self.easm_button.pack_forget()
        self.easm_cover.pack_forget()
        
        self.easm_cover.config(
            text="╔══════╗\n║COVER ║\n║CLOSED║\n╚══════╝",
            bg="#ffcc00",
            relief="raised",
            width=8
        )
        self.easm_cover.pack(padx=3, pady=3)
        self.easm_button.config(state="disabled")
        
        # LED turns off
        self.easm_led.config(fg="#333333")
        
        # Cancel timer
        if self.easm_cover_timer:
            self.root.after_cancel(self.easm_cover_timer)
            self.easm_cover_timer = None
    
    def _easm_toggle(self):
        """Toggle Enhanced Active Scan Mode."""
        if not self.easm_cover_open:
            return
        
        self.easm_enabled = not self.easm_enabled
        
        # === WIRE TO SCANNER BACKEND ===
        # Propagate EASM state to the actual scanner
        if self.scanner and hasattr(self.scanner, 'easm_enabled'):
            self.scanner.easm_enabled = self.easm_enabled
        
        if self.easm_enabled:
            # Activate EASM
            self.easm_button.config(
                text="EASM\n▶ ON",
                bg="#ff0000",
                fg="#ffffff",
                relief="sunken"
            )
            self.easm_led.config(fg="#ff0000")  # Red LED = active
            
            # Update status
            self.log_event("EASM", "✓ Enhanced Active Scan Mode ACTIVATED")
            self.log_event("EASM", "  → Probe requests enabled (5/sec rate limit)")
            self.log_event("EASM", "  → Channel sweeping enabled")
            self.log_event("EASM", "  → Hidden SSID discovery enabled")
            self.log_event("EASM", "  → IE harvesting enabled")
            
            # Cancel auto-close timer since it's now active
            if self.easm_cover_timer:
                self.root.after_cancel(self.easm_cover_timer)
                self.easm_cover_timer = None
            
            # Flash the button to confirm
            self._easm_flash_button(3)
            
        else:
            # Deactivate EASM
            self.easm_button.config(
                text="EASM\nOFF",
                bg="#660000",
                fg="#ffffff",
                relief="raised"
            )
            self.easm_led.config(fg="#ffcc00")  # Yellow = cover open but inactive
            
            self.log_event("EASM", "✗ Enhanced Active Scan Mode DEACTIVATED")
            self.log_event("EASM", "  → Returned to passive-only scanning")
            
            # Log EASM stats if available
            if self.scanner and hasattr(self.scanner, 'get_easm_stats'):
                stats = self.scanner.get_easm_stats()
                if stats:
                    self.log_event("EASM", f"  → Session stats: {stats['probes']['sent']} probes, "
                                   f"{stats['probes']['responses']} responses")
            
            # Start auto-close timer again
            self.easm_cover_timer = self.root.after(10000, self._easm_auto_close)
    
    def _easm_flash_button(self, count):
        """Flash the EASM button to confirm activation."""
        if count <= 0:
            return
        
        current_bg = self.easm_button.cget("bg")
        flash_bg = "#ff4444" if current_bg == "#ff0000" else "#ff0000"
        self.easm_button.config(bg=flash_bg)
        
        self.root.after(100, lambda: self._easm_flash_button(count - 1))
    
    def _on_zoom_change(self, value):
        """Handle radar zoom changes."""
        self.radar_zoom = float(value)
        self.zoom_label.config(text=f"{self.radar_zoom:.1f}x")
    
    def _on_radar_click(self, event):
        """Handle radar click."""
        self.radar_drag_start = (event.x, event.y)
        
        # Check if clicked on a network
        for bssid, (net_x, net_y) in self.network_positions.items():
            dist = math.sqrt((event.x - net_x)**2 + (event.y - net_y)**2)
            if dist < 20:
                self.radar_drag_start = None
                self._show_network_details(bssid)
                return
    
    def _on_radar_drag(self, event):
        """Handle radar panning."""
        if self.radar_drag_start is None:
            return
        
        dx = event.x - self.radar_drag_start[0]
        dy = event.y - self.radar_drag_start[1]
        
        self.radar_pan_x += dx
        self.radar_pan_y += dy
        self.radar_drag_start = (event.x, event.y)
    
    def _on_radar_release(self, event):
        """Handle radar mouse release."""
        self.radar_drag_start = None
    
    def _on_radar_scroll(self, event):
        """Handle radar scroll zoom."""
        if event.delta > 0:
            new_zoom = self.radar_zoom * 1.1
        else:
            new_zoom = self.radar_zoom * 0.9
        
        new_zoom = max(0.5, min(3.0, new_zoom))
        self.radar_zoom = new_zoom
        self.zoom_slider.set(new_zoom)
        self.zoom_label.config(text=f"{self.radar_zoom:.1f}x")
    
    def _toggle_heatmap(self):
        """Toggle heatmap display."""
        self.show_heatmap = not self.show_heatmap
        if self.show_heatmap:
            self.btn_heatmap.config(bg="#ff0000", text="🔥 HEATMAP ON")
        else:
            self.btn_heatmap.config(bg="#ff6600", text="🔥 HEATMAP")
    
    def _toggle_extended_scan(self):
        """Toggle extended scan mode for weak signal detection."""
        self.extended_scan_mode = not self.extended_scan_mode
        
        if self.extended_scan_mode:
            self.btn_extended.config(bg="#00ff88", fg="#000000", text="📡 EXTENDED ON")
            self.log_event("SCAN", f"Extended scan mode ENABLED ({self.extended_timeout}s timeout)")
            self._update_status(f"[EXTENDED MODE] Scan timeout: {self.extended_timeout}s - Better weak signal detection")
        else:
            theme = self.ui_themes[self.current_profile]
            self.btn_extended.config(bg="#444444", fg="#ffffff", text="📡 EXTENDED")
            self.log_event("SCAN", f"Extended scan mode disabled ({self.scan_timeout}s timeout)")
            self._update_status(f"[STANDARD MODE] Scan timeout: {self.scan_timeout}s")
    
    def _toggle_radar_mode(self):
        """Toggle between Static Desktop and Mobile Homing radar modes."""
        if self.radar_system.state.mode == RadarMode.STATIC_DESKTOP:
            # Switch to Mobile Homing mode
            self.radar_system.set_mode(RadarMode.MOBILE_HOMING)
            self.btn_radar_mode.config(bg="#ff00ff", text="📡 MOBILE")
            self.radar_mode_label.config(text="Mobile Homing", fg="#ff00ff")
            self.log_event("RADAR", "Switched to MOBILE HOMING mode")
            
            # Start calibration if no sensor data
            if not self.radar_system.state.has_compass:
                self._start_mobile_calibration()
        else:
            # Switch to Static Desktop mode
            self.radar_system.set_mode(RadarMode.STATIC_DESKTOP)
            self.btn_radar_mode.config(bg="#00ff88", text="📡 STATIC")
            self.radar_mode_label.config(text="Desktop Mode", fg="#00ff88")
            self.log_event("RADAR", "Switched to STATIC DESKTOP mode")
    
    def _start_mobile_calibration(self):
        """Start mobile mode calibration."""
        self.radar_system.start_calibration()
        self.log_event("CALIBRATE", "Rotate device 360° to calibrate direction...")
        messagebox.showinfo("Mobile Mode Calibration",
            "MOBILE HOMING MODE\n\n"
            "For best results, slowly rotate your device 360° while scanning.\n\n"
            "The radar will detect which direction each network is strongest.\n\n"
            "Without rotation sensors, this manual calibration helps determine AP directions.")

    def _set_wave_intensity(self, value):
        """Set wave intensity."""
        if not self.is_muted:
            self.wave_intensity = float(value) / 100.0
        if hasattr(self, 'wave_label'):
            self.wave_label.config(text=f"{int(float(value))}%")
    
    def _toggle_mute(self):
        """Toggle audio mute."""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.wave_intensity = 0.0
            self.btn_mute.config(bg="#ffff00", text="🔇 MUTED")
            self.audio_playing = False
        else:
            self.wave_intensity = self.wave_slider.get() / 100.0
            self.btn_mute.config(bg="#ff6600", text="🔊 MUTE")
    
    def _toggle_scan(self, event=None):
        """Toggle scanning."""
        if self.is_scanning:
            self._stop_scan()
        else:
            self._start_scan()
    
    def _start_scan(self):
        """Start WiFi scan."""
        if not self.scanner:
            messagebox.showerror("Error", "No scanner available")
            return
        
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        # Determine scan timeout based on extended mode
        timeout = self.extended_timeout if self.extended_scan_mode else self.scan_timeout
        mode_str = "EXTENDED" if self.extended_scan_mode else "STANDARD"
        self.log_event("SCAN", f"Scan initiated [{mode_str} MODE - {timeout}s timeout]")
        
        def scan_thread():
            while self.is_scanning:
                mode_text = "📡 EXTENDED SCAN" if self.extended_scan_mode else "SCANNING"
                self._update_status(f"[{mode_text}] Acquiring network data...")
                
                try:
                    # Use extended timeout for weak signal detection
                    scan_timeout = self.extended_timeout if self.extended_scan_mode else self.scan_timeout
                    result = self.scanner.scan(timeout=scan_timeout)
                    self.last_result = result
                    self.scan_count += 1
                    
                    # Convert to internal format
                    for network in result.networks:
                        bssid = network.bssid
                        if bssid not in self.networks:
                            ssid_display = (network.ssid or 'Hidden')[:25]
                            self.log_event("SCAN", f"Network found: {ssid_display} ({network.signal_percent}%)")
                        
                        # Calculate distance estimate using passive metrics
                        distance_est = self.distance_estimator.estimate(
                            bssid=bssid,
                            ssid=network.ssid or "",
                            signal_percent=network.signal_percent,
                            channel=network.channel,
                            vendor=network.vendor or "unknown"
                        )
                        
                        # Device fingerprinting (100% passive)
                        fingerprint = self.fingerprinter.fingerprint(
                            bssid=bssid,
                            ssid=network.ssid or "",
                            vendor=network.vendor or "",
                            channel=network.channel,
                            signal=network.signal_percent,
                            security=network.security.value
                        )
                        
                        # Record stability metrics (100% passive)
                        stability_metrics = self.stability_tracker.record_signal(
                            bssid=bssid,
                            ssid=network.ssid or "",
                            signal=network.signal_percent,
                            channel=network.channel
                        )
                        
                        # Wall estimation (100% passive)
                        freq_mhz = 2437 if network.channel <= 14 else 5180 + (network.channel - 36) * 5
                        wall_est = self.wall_estimator.estimate_walls(
                            signal_dbm=network.signal_percent - 100,  # Convert % to approx dBm
                            frequency_mhz=freq_mhz,
                            estimated_distance=distance_est.distance_meters,
                            device_type=fingerprint.device_type.value
                        )
                        
                        # Spoof detection (100% passive)
                        spoof_alerts = self.spoof_detector.analyze_network(
                            bssid=bssid,
                            ssid=network.ssid or "",
                            signal=network.signal_percent,
                            channel=network.channel,
                            security=network.security.value
                        )
                        
                        # Hidden Network Classification (100% passive)
                        is_hidden = not network.ssid or network.ssid.strip() == ""
                        if is_hidden:
                            self.hidden_classifier.record_hidden_network(
                                bssid=bssid,
                                channel=network.channel,
                                rssi=network.signal_percent - 100,
                                security=network.security.value,
                                vendor=network.vendor or "",
                                stability=stability_metrics.stability_score
                            )
                        else:
                            # Record visible network for correlation
                            self.hidden_classifier.record_visible_network(
                                bssid=bssid,
                                ssid=network.ssid,
                                channel=network.channel,
                                rssi=network.signal_percent - 100,
                                security=network.security.value,
                                vendor=network.vendor or ""
                            )
                        
                        self.networks[bssid] = {
                            'ssid': network.ssid or f"Hidden_{bssid}",
                            'signal': network.signal_percent,
                            'channel': network.channel,
                            'security': network.security.value,
                            'bssid': bssid,
                            'vendor': network.vendor,
                            'band': network.band,
                            'type': fingerprint.icon,
                            # Distance estimation data
                            'distance': distance_est.distance_meters,
                            'distance_margin': distance_est.margin_percent,
                            'confidence': distance_est.confidence_percent,
                            'snr': distance_est.snr_db,
                            'noise_level': distance_est.noise_level,
                            'stability': stability_metrics.stability_rating.value,
                            'stability_score': stability_metrics.stability_score,
                            'jitter': stability_metrics.current_jitter,
                            'volatility': stability_metrics.volatility_percent,
                            'trend': stability_metrics.trend,
                            'environment': distance_est.environment_guess,
                            'environment_detail': distance_est.environment_detail,
                            'signal_quality': distance_est.signal_quality,
                            'snr_quality': distance_est.snr_quality,
                            'tooltip': distance_est.to_tooltip(),
                            # Device fingerprint
                            'device_type': fingerprint.device_type.value,
                            'device_icon': fingerprint.icon,
                            'device_desc': fingerprint.description,
                            'device_confidence': fingerprint.confidence,
                            'device_tags': fingerprint.tags,
                            # Wall estimation
                            'wall_estimate': wall_est.estimate.value,
                            'wall_count': wall_est.wall_count,
                            'wall_desc': wall_est.description,
                            # Spoof status
                            'has_alerts': len(spoof_alerts) > 0,
                            'alert_count': len(self.spoof_detector.get_alerts_for_bssid(bssid)),
                            # OUI-IM Vendor Intelligence (populated later from UWM-X)
                            'vendor_confidence': 0.0,
                            'vendor_type': 'unknown',
                            'is_randomized_mac': False,
                            # EASM source tracking
                            'easm_source': False,  # Will be updated below for EASM discoveries
                            'easm_revealed': False  # True if hidden SSID revealed by EASM
                        }
                        
                        # Record spectrogram history (passive data only)
                        now = time.time()
                        self.spectrogram_history[bssid].append((now, network.signal_percent))
                        # Trim old data beyond max window
                        cutoff = now - 120  # Keep 120s max
                        self.spectrogram_history[bssid] = [
                            (t, s) for t, s in self.spectrogram_history[bssid] if t > cutoff
                        ]
                        
                        # Feed Passive Intelligence Core (100% passive)
                        self.intelligence_core.process_network(
                            bssid=bssid,
                            ssid=network.ssid or "",
                            signal_percent=network.signal_percent,
                            channel=network.channel,
                            security=network.security.value,
                            vendor=network.vendor or "",
                            band=network.band or "",
                            noise_db=-95  # Estimated
                        )
                        
                        # Feed Unified World Model Expander (100% passive)
                        uwm_node = self.world_model.update_node(
                            mac=bssid,
                            ssid=network.ssid or "",
                            rssi=network.signal_percent - 100,  # Convert % to approx dBm
                            channel=network.channel,
                            security=network.security.value,
                            vendor=network.vendor or "",
                            distance=distance_est.distance_meters,
                            angle=0.0,  # No angle in static mode
                            stability=stability_metrics.stability_score,
                            spoof_risk=100 if len(spoof_alerts) > 0 else 0
                        )
                        
                        # Update network data with UWM-X OUI-IM intelligence
                        self.networks[bssid]['vendor_confidence'] = uwm_node.vendor_confidence
                        self.networks[bssid]['vendor_type'] = uwm_node.vendor_type
                        self.networks[bssid]['is_randomized_mac'] = uwm_node.is_randomized_mac
                    
                    # === EASM DISCOVERY PROCESSING ===
                    # Mark networks discovered through EASM active probing
                    if self.easm_enabled and self.scanner and hasattr(self.scanner, '_easm_discoveries'):
                        easm_discoveries = getattr(self.scanner, '_easm_discoveries', [])
                        easm_bssids = {d['bssid'].lower() for d in easm_discoveries}
                        
                        for bssid in self.networks:
                            if bssid.lower() in easm_bssids:
                                self.networks[bssid]['easm_source'] = True
                        
                        # Log EASM discoveries
                        if easm_discoveries:
                            for discovery in easm_discoveries:
                                dtype = discovery.get('type', 'probe_response')
                                dssid = discovery.get('ssid', 'Unknown')[:20]
                                if dtype == 'hidden_reveal':
                                    self.networks[discovery['bssid'].lower()]['easm_revealed'] = True
                                    self.root.after(0, lambda s=dssid: self.log_event("EASM", f"⚡ Hidden SSID REVEALED: {s}"))
                                elif dtype == 'probe_response':
                                    self.root.after(0, lambda s=dssid: self.log_event("EASM", f"⚡ Probe response: {s}"))
                        
                        # Log EASM stats periodically
                        if hasattr(self.scanner, 'get_easm_stats'):
                            stats = self.scanner.get_easm_stats()
                            if stats and stats.get('probes', {}).get('sent', 0) > 0:
                                sent = stats['probes']['sent']
                                resp = stats['probes']['responses']
                                revealed = stats['hidden_ssids']['revealed']
                                self.root.after(0, lambda s=sent, r=resp, h=revealed: 
                                    self._update_easm_stats(s, r, h))
                    
                    # Update UWM-X relationships and clusters (100% passive)
                    self.world_model.refresh_environments()
                    self.world_model.compute_relationships()
                    self.world_model.compute_clusters()
                    
                    # Analyze hidden networks (100% passive)
                    self.hidden_classifier.analyze()
                    
                    # Analyze threats
                    threats = self.detector.analyze(result)
                    result.threats = threats
                    
                    # Update UI
                    self.root.after(0, lambda: self._update_display(result))
                    
                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda msg=error_msg: self._update_status(f"[ERROR] {msg}"))
                
                time.sleep(2)
            
            self.root.after(0, self._scan_complete)
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _stop_scan(self):
        """Stop scanning."""
        self.is_scanning = False
        self.audio_playing = False
        self._update_status(f"[HALTED] {len(self.networks)} networks found")
        self.log_event("SCAN", f"Scan stopped - {len(self.networks)} networks")
    
    def _scan_complete(self):
        """Called when scan completes."""
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
    
    def _detect_device_type(self, ssid, bssid):
        """Detect device type from SSID."""
        ssid_lower = ssid.lower()
        
        if any(x in ssid_lower for x in ['iphone', 'ipad']):
            return "🍎 iPhone/iPad"
        elif any(x in ssid_lower for x in ['galaxy', 'samsung', 'android']):
            return "📱 Android"
        elif any(x in ssid_lower for x in ['router', 'netgear', 'tp-link', 'linksys', 'asus']):
            return "🖥️ Router"
        elif any(x in ssid_lower for x in ['alexa', 'echo', 'nest', 'smart']):
            return "🏠 Smart Home"
        elif any(x in ssid_lower for x in ['tv', 'roku', 'firestick', 'chromecast']):
            return "📺 Media"
        elif any(x in ssid_lower for x in ['xbox', 'playstation', 'nintendo']):
            return "🎮 Gaming"
        elif any(x in ssid_lower for x in ['print', 'hp', 'epson']):
            return "🖨️ Printer"
        elif any(x in ssid_lower for x in ['guest', 'public']):
            return "🌐 Guest"
        else:
            return "📶 Private"
    
    def _update_display(self, result: ScanResult):
        """Update all displays."""
        # Update network list
        self._update_network_list()
        
        # Update hydrophone selector
        self._update_network_selector()
        
        # Update spectrogram network selector
        self._update_spectro_selector()
        
        # Update statistics
        self._update_statistics()
        
        # Update security audit
        self._update_security_audit()
        
        # Update vulnerability view
        self._update_vulnerability_view()
        
        # Update Intelligence Core display
        self._update_intelligence_display()
        
        # Update Hidden Network Diagnostics
        self._update_hidden_diagnostics()
        
        # Update stats label with v2.0 format
        hidden_count = len(self.hidden_classifier.profiles)
        world_nodes = len(self.world_model.nodes)
        mode_str = "ACTIVE ⚡" if self.easm_enabled else "PASSIVE"
        mode_color = "#ff0000" if self.easm_enabled else self.ui_themes[self.current_profile]["text_secondary"]
        
        # Count EASM discoveries
        easm_count = sum(1 for d in self.networks.values() if d.get('easm_source', False))
        easm_revealed = sum(1 for d in self.networks.values() if d.get('easm_revealed', False))
        
        # Build stats string
        if self.easm_enabled and easm_count > 0:
            stats_text = f"NETWORKS: {len(self.networks)} ({easm_count}⚡) | HIDDEN: {hidden_count} | REVEALED: {easm_revealed} | NODES: {world_nodes} | SCANS: {self.scan_count} | MODE: {mode_str}"
        else:
            stats_text = f"NETWORKS: {len(self.networks)} | HIDDEN: {hidden_count} | NODES: {world_nodes} | SCANS: {self.scan_count} | MODE: {mode_str}"
        
        self.stats_label.config(text=stats_text, fg=mode_color)
        
        self._update_status(f"[ACTIVE] {len(self.networks)} networks acquired | UWM-X: {world_nodes} nodes")
    
    def _get_smart_vendor_display(self, vendor_name: str, vendor_type: str, is_randomized: bool, max_len: int = 15) -> str:
        """Get vendor display with smart device icons."""
        vendor_name = vendor_name or "Unknown"
        vendor_lower = vendor_name.lower()
        
        # Smart device icon mapping - specific devices first
        device_icons = {
            # Ring devices
            "ring doorbell": "🚪",
            "ring camera": "📹",
            "ring chime": "🔔",
            "ring device": "🔔",
            # Amazon devices
            "amazon echo": "🔊",
            "amazon fire": "📺",
            "amazon sidewalk": "🌐",
            # Blink cameras
            "blink camera": "📹",
            # Smart home
            "nest": "🏠",
            "hue": "💡",
            "philips hue": "💡",
            "sonos": "🔊",
            "tp-link kasa": "💡",
            "wemo": "🔌",
            "smartthings": "🏠",
            "wyze": "📹",
            "arlo": "📹",
            "eufy": "📹",
            # Voice assistants
            "google home": "🔊",
            "homepod": "🔊",
            # Gaming
            "playstation": "🎮",
            "xbox": "🎮",
            "nintendo": "🎮",
            # TV/Streaming
            "roku": "📺",
            "chromecast": "📺",
            "apple tv": "📺",
            "fire tv": "📺",
            "samsung tv": "📺",
            "lg tv": "📺",
            # Printers
            "hp inc": "🖨️",
            "canon": "🖨️",
            "epson": "🖨️",
            "brother": "🖨️",
            # Computers
            "dell": "💻",
            "lenovo": "💻",
            "hp ": "💻",
            "asus": "💻",
            "acer": "💻",
            # Phones
            "apple": "📱",
            "samsung": "📱",
            "google": "📱",
            "oneplus": "📱",
            "xiaomi": "📱",
            "huawei": "📱",
            "oppo": "📱",
            # Routers - UK ISPs
            "bt hub": "📶",
            "bt router": "📶",
            "ee router": "📶",
            "sky router": "📶",
            "virgin media": "📶",
            "talktalk": "📶",
            "plusnet": "📶",
            "vodafone router": "📶",
            # Routers - general
            "netgear": "📶",
            "tp-link": "📶",
            "asus router": "📶",
            "linksys": "📶",
            "d-link": "📶",
            "ubiquiti": "📶",
            "aruba": "📶",
            "cisco": "📶",
            "ruckus": "📶",
            # Mesh systems
            "eero": "🔗",
            "orbi": "🔗",
            "google wifi": "🔗",
            "deco": "🔗",
            "velop": "🔗",
        }
        
        # Check for specific device match
        for device, icon in device_icons.items():
            if device in vendor_lower:
                return f"{icon} {vendor_name[:max_len-2]}"
        
        # Fall back to category-based icons
        if is_randomized:
            return f"🎲 {vendor_name[:max_len-2]}"
        elif vendor_type == "enterprise":
            return f"🏢 {vendor_name[:max_len-2]}"
        elif vendor_type == "mesh":
            return f"🔗 {vendor_name[:max_len-2]}"
        elif vendor_type == "iot":
            return f"📱 {vendor_name[:max_len-2]}"
        else:
            return vendor_name[:max_len]
    
    def _update_network_list(self):
        """Update network tree view."""
        for item in self.network_tree.get_children():
            self.network_tree.delete(item)
        
        # Track weak signal counts
        weak_count = 0
        very_weak_count = 0
        
        for bssid, data in sorted(self.networks.items(), 
                                   key=lambda x: x[1]['signal'], reverse=True):
            sig = data['signal']
            rssi_dbm = sig - 100  # Approximate dBm from percentage
            
            # Skip signals below minimum filter
            if rssi_dbm < self.min_signal_filter:
                continue
            
            bar_len = int(sig / 10)
            signal_bar = "█" * bar_len + "░" * (10 - bar_len)
            
            # Determine signal quality tag
            if sig >= 80:
                tag = "excellent"
            elif sig >= 60:
                tag = "good"
            elif sig >= 40:
                tag = "fair"
            elif rssi_dbm < self.very_weak_threshold:
                tag = "very_weak"
                very_weak_count += 1
            else:
                tag = "weak"
                weak_count += 1
            
            # Signal display with weak indicators
            if rssi_dbm < self.very_weak_threshold:
                signal_display = f"🔻{signal_bar} {sig}%"
            elif rssi_dbm < self.weak_signal_threshold:
                signal_display = f"⚠️{signal_bar} {sig}%"
            else:
                signal_display = f"{signal_bar} {sig}%"
            
            # Check for EASM source - override tag for visual distinction
            is_easm = data.get('easm_source', False)
            is_revealed = data.get('easm_revealed', False)
            if is_revealed:
                tag = "easm_revealed"
            elif is_easm:
                tag = "easm"
            
            # Environment guess (simpler than raw distance)
            env = data.get('environment', 'Unknown')
            
            # Vendor display with OUI-IM intelligence
            vendor_name = data.get('vendor', 'Unknown') or 'Unknown'
            vendor_type = data.get('vendor_type', 'unknown')
            is_randomized = data.get('is_randomized_mac', False)
            
            # Smart device icon mapping
            vendor_display = self._get_smart_vendor_display(vendor_name, vendor_type, is_randomized)
            
            # Source column indicator
            if is_revealed:
                src_display = "⚡👁"  # Revealed hidden
            elif is_easm:
                src_display = "⚡"   # EASM discovery
            else:
                src_display = "📡"   # Passive beacon
            
            self.network_tree.insert("", "end",
                values=(data['type'], data['ssid'][:30], signal_display,
                       vendor_display, env, f"Ch.{data['channel']}", data['security'], src_display),
                tags=(tag,))
        
        # Update weak signal indicator label
        if hasattr(self, 'weak_signal_label'):
            if weak_count > 0 or very_weak_count > 0:
                self.weak_signal_label.config(
                    text=f"⚠️{weak_count} weak | 🔻{very_weak_count} very weak",
                    fg="#ff8800"
                )
            else:
                self.weak_signal_label.config(text="", fg="#888888")
    
    def _update_network_selector(self):
        """Update hydrophone network selector."""
        current = self.network_select.get()
        networks = [data['ssid'] for data in sorted(self.networks.values(),
                                                    key=lambda x: x['signal'], reverse=True)]
        self.network_select['values'] = networks
        if current and current in networks:
            self.network_select.set(current)
    
    def _update_spectro_selector(self):
        """Update spectrogram network selector."""
        if not hasattr(self, 'spectro_network_select'):
            return
        current = self.spectro_network_select.get()
        networks = ["[ ALL NETWORKS ]"] + [data['ssid'] for data in sorted(
            self.networks.values(), key=lambda x: x['signal'], reverse=True)]
        self.spectro_network_select['values'] = networks
        if current and current in networks:
            self.spectro_network_select.set(current)
    
    def _update_easm_stats(self, probes_sent: int, responses: int, revealed: int):
        """Update EASM statistics display."""
        if probes_sent > 0:
            response_rate = (responses / probes_sent) * 100 if probes_sent > 0 else 0
            self.log_event("EASM", f"📊 Stats: {probes_sent} probes → {responses} responses ({response_rate:.0f}%) | {revealed} hidden revealed")
    
    def _draw_spectrogram(self):
        """Draw the signal spectrogram waterfall display."""
        if not hasattr(self, 'spectro_canvas'):
            return
        
        canvas = self.spectro_canvas
        canvas.delete("all")
        
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w < 50 or h < 50:
            return
        
        theme = self.ui_themes[self.current_profile]
        now = time.time()
        max_time = self.spectrogram_max_seconds
        
        # Determine which networks to show
        if self.spectrogram_selected == "all":
            networks_to_show = list(self.spectrogram_history.keys())
        else:
            networks_to_show = [self.spectrogram_selected] if self.spectrogram_selected in self.spectrogram_history else []
        
        if not networks_to_show:
            canvas.create_text(w // 2, h // 2, text="⏳ AWAITING SIGNAL DATA...",
                              font=("Courier New", 14, "bold"), fill=theme["text_secondary"])
            return
        
        # Calculate row height
        row_height = max(20, min(60, (h - 40) // max(len(networks_to_show), 1)))
        
        # Draw waterfall for each network
        y_offset = 20
        bar_width = max(2, (w - 150) // max_time)  # Pixels per second
        
        for bssid in networks_to_show[:15]:  # Limit to 15 networks
            if bssid not in self.networks:
                continue
            
            data = self.networks[bssid]
            history = self.spectrogram_history.get(bssid, [])
            
            # Draw network label
            ssid_display = data['ssid'][:18]
            canvas.create_text(5, y_offset + row_height // 2, text=ssid_display,
                              font=("Courier New", 8), fill=theme["text_primary"], anchor="w")
            
            # Draw waterfall bars (newest on left)
            x_start = 140
            for timestamp, signal in reversed(history):
                age = now - timestamp
                if age > max_time:
                    continue
                
                # X position based on age (0 = now = left side)
                x = x_start + int(age * bar_width)
                if x > w - 10:
                    continue
                
                # Color based on signal strength
                color = self._get_spectro_color(signal)
                
                # Draw bar with glow effect for strong signals
                bar_height = row_height - 4
                canvas.create_rectangle(x, y_offset + 2, x + bar_width - 1, y_offset + bar_height,
                                        fill=color, outline="")
                
                # Add glow for excellent signals
                if signal >= 80:
                    canvas.create_rectangle(x, y_offset, x + bar_width, y_offset + bar_height + 2,
                                            outline=color, width=1)
            
            # Draw current signal value
            if history:
                latest_signal = history[-1][1]
                canvas.create_text(125, y_offset + row_height // 2, 
                                  text=f"{latest_signal}%",
                                  font=("Courier New", 8, "bold"),
                                  fill=self._get_spectro_color(latest_signal), anchor="e")
            
            # Draw separator line
            canvas.create_line(140, y_offset + row_height, w - 10, y_offset + row_height,
                              fill=theme["grid_color"], width=1)
            
            y_offset += row_height
        
        # Draw time scale at bottom
        canvas.create_line(140, h - 25, w - 10, h - 25, fill=theme["text_secondary"], width=1)
        for sec in range(0, max_time + 1, max_time // 4):
            x = 140 + int(sec * bar_width)
            if x < w - 10:
                canvas.create_line(x, h - 28, x, h - 22, fill=theme["text_secondary"], width=1)
                label = "NOW" if sec == 0 else f"-{sec}s"
                canvas.create_text(x, h - 15, text=label, font=("Courier New", 7),
                                  fill=theme["text_accent"])
        
        # Draw animated scan line
        scan_x = 140 + int((now % 2) * bar_width * 2)
        if scan_x < w - 10:
            canvas.create_line(scan_x, 10, scan_x, y_offset,
                              fill=theme["text_primary"], width=2, dash=(4, 2))
    
    def _get_spectro_color(self, signal):
        """Get color for spectrogram based on signal strength."""
        if signal >= 80:
            return "#00ff00"  # Excellent - Green
        elif signal >= 60:
            return "#00ffff"  # Good - Cyan
        elif signal >= 40:
            return "#ffff00"  # Fair - Yellow
        elif signal >= 20:
            return "#ff0088"  # Weak - Pink
        else:
            return "#ff0000"  # Critical - Red

    def _update_statistics(self):
        """Update statistics view."""
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)
        
        if not self.networks:
            self.stats_text.insert("end", "⏳ Waiting for scan data...\n", "info")
            self.stats_text.config(state="disabled")
            return
        
        total = len(self.networks)
        
        # Count by security type
        security_counts = defaultdict(int)
        signal_bands = {"Excellent (80-100%)": 0, "Good (60-79%)": 0, 
                       "Fair (40-59%)": 0, "Weak (<40%)": 0}
        channel_counts = defaultdict(int)
        
        for data in self.networks.values():
            security_counts[data['security']] += 1
            channel_counts[data['channel']] += 1
            
            sig = data['signal']
            if sig >= 80:
                signal_bands["Excellent (80-100%)"] += 1
            elif sig >= 60:
                signal_bands["Good (60-79%)"] += 1
            elif sig >= 40:
                signal_bands["Fair (40-59%)"] += 1
            else:
                signal_bands["Weak (<40%)"] += 1
        
        avg_signal = sum(d['signal'] for d in self.networks.values()) / total
        
        stats = f"""
╔═══════════════════════════════════════════════════════════════╗
║               📊 NETWORK STATISTICS ANALYSIS 📊               ║
║            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
╚═══════════════════════════════════════════════════════════════╝

📡 SCAN SUMMARY
───────────────────────────────────────────────────────────────
  Total Networks: {total}
  Average Signal: {avg_signal:.1f}%
  Scans Complete: {self.scan_count}

🔐 SECURITY BREAKDOWN
───────────────────────────────────────────────────────────────
"""
        for sec_type, count in sorted(security_counts.items()):
            pct = (count / total) * 100
            icon = "🔴" if "Open" in sec_type else "🟢"
            stats += f"  {icon} {sec_type:20} │ {count:3} ({pct:5.1f}%)\n"
        
        stats += "\n📊 SIGNAL DISTRIBUTION\n"
        stats += "───────────────────────────────────────────────────────────────\n"
        for band, count in signal_bands.items():
            pct = (count / total) * 100
            stats += f"  {band:20} │ {count:3} ({pct:5.1f}%)\n"
        
        stats += "\n📶 CHANNEL USAGE\n"
        stats += "───────────────────────────────────────────────────────────────\n"
        for ch in sorted(channel_counts.keys()):
            count = channel_counts[ch]
            pct = (count / total) * 100
            bar = "█" * int(pct / 5)
            stats += f"  Channel {ch:3} │ {bar:20} {count:2} ({pct:.1f}%)\n"
        
        self.stats_text.insert("end", stats)
        self.stats_text.config(state="disabled")
    
    def _update_security_audit(self):
        """Update security audit view."""
        self.security_text.config(state="normal")
        self.security_text.delete("1.0", tk.END)
        
        if not self.networks:
            self.security_text.insert("end", "⏳ Waiting for scan data...\n")
            self.security_text.config(state="disabled")
            return
        
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║            🛡️ WIRELESS SECURITY AUDIT REPORT 🛡️              ║
║            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
╚═══════════════════════════════════════════════════════════════╝

🔴 CRITICAL VULNERABILITIES
───────────────────────────────────────────────────────────────
"""
        
        critical_count = 0
        for bssid, data in self.networks.items():
            if 'Open' in data['security'] or 'WEP' in data['security']:
                critical_count += 1
                report += f"""
  ⚠️  {data['ssid'][:30]}
      Security: {data['security']}
      Signal: {data['signal']}%
      Channel: {data['channel']}
"""
        
        if critical_count == 0:
            report += "  ✓ No critical vulnerabilities found\n"
        
        report += f"""
📈 RISK SUMMARY
───────────────────────────────────────────────────────────────
  🔴 Critical: {critical_count} networks
  Total Networks: {len(self.networks)}
  
💡 RECOMMENDATIONS
───────────────────────────────────────────────────────────────
  • Avoid connecting to Open/WEP networks
  • Use WPA2/WPA3 for home networks
  • Use VPN on public networks
  • Keep router firmware updated
"""
        
        self.security_text.insert("end", report)
        self.security_text.config(state="disabled")
    
    def _update_vulnerability_view(self):
        """Update vulnerability view."""
        self.vuln_text.config(state="normal")
        self.vuln_text.delete("1.0", tk.END)
        
        if not self.networks:
            self.vuln_text.insert("end", "⏳ Awaiting scan data...\n", "info")
            self.vuln_text.config(state="disabled")
            return
        
        self.vuln_text.insert("end", "╔════════════════════════════════════════╗\n", "header")
        self.vuln_text.insert("end", "║     VULNERABILITY ANALYSIS MATRIX      ║\n", "header")
        self.vuln_text.insert("end", "╚════════════════════════════════════════╝\n\n", "header")
        
        critical = 0
        warning = 0
        secure = 0
        
        for bssid, data in sorted(self.networks.items(), 
                                   key=lambda x: x[1]['signal'], reverse=True):
            security = data['security']
            
            if 'Open' in security:
                tag = "critical"
                status = "CRITICAL - NO ENCRYPTION"
                critical += 1
            elif 'WEP' in security:
                tag = "critical"
                status = "CRITICAL - DEPRECATED WEP"
                critical += 1
            elif 'WPA ' in security and 'WPA2' not in security:
                tag = "warning"
                status = "WARNING - WEAK WPA"
                warning += 1
            else:
                tag = "secure"
                status = "SECURE"
                secure += 1
            
            self.vuln_text.insert("end", f"▶ {data['ssid'][:35]}\n", tag)
            self.vuln_text.insert("end", f"  Status: {status}\n", tag)
            self.vuln_text.insert("end", f"  Signal: {data['signal']}% | BSSID: {bssid}\n\n", "info")
        
        self.vuln_text.insert("end", "\n╔════════════════════════════════════════╗\n", "header")
        self.vuln_text.insert("end", f"║  🔴 CRITICAL: {critical}  🟡 WARNING: {warning}  🟢 SECURE: {secure}  ║\n", "header")
        self.vuln_text.insert("end", "╚════════════════════════════════════════╝\n", "header")
        
        self.vuln_text.config(state="disabled")
    
    def _update_event_log_display(self):
        """Update event log display."""
        if not hasattr(self, 'event_display'):
            return
        
        self.event_display.config(state="normal")
        self.event_display.delete("1.0", tk.END)
        
        for timestamp, event_type, message in self.event_log[-50:]:
            if event_type in ("THREAT", "CRITICAL"):
                tag = "critical"
            elif event_type == "WARNING":
                tag = "warning"
            elif event_type in ("SCAN", "PROFILE", "SYSTEM"):
                tag = "header"
            else:
                tag = "info"
            
            line = f"[{timestamp}] {event_type:10} > {message}\n"
            self.event_display.insert(tk.END, line, tag)
        
        self.event_display.see(tk.END)
        self.event_display.config(state="disabled")
    
    def _schedule_update(self):
        """Schedule periodic UI updates."""
        # Update animations
        if self.effects_enabled:
            self.breathe_phase = (self.breathe_phase + 1) % 60
            self.glitch_counter = (self.glitch_counter + 1) % 30
            self.rotation_angle = (self.rotation_angle + 3) % 360
        
        # Update header glitch effect
        glitch_patterns = [
            "⚡ NEXUS // WiFi RADAR // INTELLIGENCE EDITION ⚡",
            "⚡ NEX░S ▓▓ WiFi RADAR ▓▓ v2.0 ⚡",
            "⚡ NEXUS // ▒▒▒▒ RADAR // INTELLIGENCE ⚡",
            "⚡ N̷E̷X̷U̷S̷ // WiFi RADAR // v2.0 ⚡",
        ]
        if self.effects_enabled and self.glitch_counter % 15 < 2:
            self.header_title.config(text=glitch_patterns[self.glitch_counter % len(glitch_patterns)])
        else:
            self.header_title.config(text=glitch_patterns[0])
        
        # Draw radar if scanning or have data
        if self.networks:
            self._draw_radar()
        
        # Draw matrix rain
        self._draw_matrix_rain()
        
        # Draw spectrogram waterfall
        if self.spectrogram_history:
            self._draw_spectrogram()
        
        # Schedule next update
        self.root.after(self.update_interval, self._schedule_update)
    
    def _draw_radar(self):
        """Draw the animated radar display."""
        self.radar_canvas.delete("all")
        self.network_positions = {}
        
        theme = self.ui_themes[self.current_profile]
        
        w = self.radar_canvas.winfo_width()
        h = self.radar_canvas.winfo_height()
        
        if w < 50 or h < 50:
            return
        
        # Center with pan offset
        cx = w // 2 + self.radar_pan_x
        cy = h // 2 + self.radar_pan_y
        r = (min(w, h) // 2 - 50) * self.radar_zoom
        
        # Draw grid
        grid_spacing = 40
        for x in range(0, w, grid_spacing):
            self.radar_canvas.create_line(x, 0, x, h, fill=theme["grid_color"], width=1)
        for y in range(0, h, grid_spacing):
            self.radar_canvas.create_line(0, y, w, y, fill=theme["grid_color"], width=1)
        
        # Draw heatmap if enabled
        if self.show_heatmap and self.networks:
            self._draw_heatmap(cx, cy, r, w, h)
        
        # Draw distance rings - labeled by SIGNAL STRENGTH not distance
        signal_levels = [80, 60, 40, 20]  # Signal % thresholds
        level_labels = ["EXCELLENT", "GOOD", "FAIR", "WEAK"]
        for i, (sig_level, label) in enumerate(zip(signal_levels, level_labels)):
            # Convert signal to radius: 80% signal = closest ring, 20% = furthest
            distance_ratio = 1 - (sig_level / 100.0) * 0.8
            radius = r * distance_ratio
            self.radar_canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=theme["text_secondary"], width=2, dash=(4, 2)
            )
            self.radar_canvas.create_text(
                cx + radius - 30, cy - 10,
                text=f"[{sig_level}%]", fill=theme["text_secondary"],
                font=("Courier New", 8, "bold")
            )
        
        # Draw crosshairs with breathing effect
        pulse = 20 + 5 * math.sin(self.breathe_phase / 10)
        self.radar_canvas.create_line(cx - pulse, cy, cx + pulse, cy,
                                      fill=theme["text_primary"], width=2)
        self.radar_canvas.create_line(cx, cy - pulse, cx, cy + pulse,
                                      fill=theme["text_primary"], width=2)
        
        # Draw center marker
        self.radar_canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10,
                                      fill=theme["text_primary"], outline=theme["text_primary"])
        self.radar_canvas.create_text(cx, cy + 25, text="[YOU]",
                                      fill=theme["text_primary"], font=("Courier New", 9, "bold"))
        
        # Draw rotating scan line
        angle_rad = self.rotation_angle * math.pi / 180
        end_x = cx + r * math.cos(angle_rad)
        end_y = cy + r * math.sin(angle_rad)
        self.radar_canvas.create_line(cx, cy, end_x, end_y,
                                      fill=theme["text_primary"], width=2)
        
        # Draw networks
        current_time = time.time()
        
        # Update radar system with current networks and get positions
        sorted_networks = sorted(self.networks.items(), key=lambda x: x[1]['signal'], reverse=True)
        
        for i, (bssid, data) in enumerate(sorted_networks[:20]):
            sig = data['signal']
            channel = data.get('channel', 1)
            
            # Update radar system
            self.radar_system.update_network(
                bssid=bssid,
                ssid=data['ssid'],
                signal=sig,
                channel=channel,
                security=data.get('security', ''),
                vendor=data.get('vendor', '')
            )
            
            # Get position from radar system
            blip = self.radar_system.blips.get(bssid)
            if blip:
                # Convert ratio to pixel coordinates
                # Note: radar system uses standard math angles, we need to adjust
                x = cx + r * blip.distance_ratio * math.cos(math.radians(blip.angle_degrees - 90))
                y = cy + r * blip.distance_ratio * math.sin(math.radians(blip.angle_degrees - 90))
            else:
                # Fallback positioning
                distance_ratio = 1.0 - (sig / 100.0)
                distance_ratio = max(0.15, distance_ratio)
                if channel <= 14:
                    base_angle = 15 + (channel - 1) * (150 / 13)
                else:
                    base_angle = 195 + ((channel - 36) % 140) * (150 / 140)
                angle_rad = math.radians(base_angle - 90)
                x = cx + r * distance_ratio * math.cos(angle_rad)
                y = cy + r * distance_ratio * math.sin(angle_rad)
            
            self.network_positions[bssid] = (x, y)
            
            # Color based on signal
            if sig >= 80:
                color = "#00ff00"
            elif sig >= 60:
                color = "#00ffff"
            elif sig >= 40:
                color = "#ffff00"
            else:
                color = "#ff0088"
            
            # Draw sound waves
            if self.wave_intensity > 0 and sig >= 60:
                for wave_num in range(2):
                    wave_phase = (current_time * sig / 4 + wave_num * 15) % 40
                    if wave_phase < 30:
                        wave_radius = wave_phase * 1.2
                        self.radar_canvas.create_oval(
                            x - wave_radius, y - wave_radius,
                            x + wave_radius, y + wave_radius,
                            outline=color, width=1
                        )
            
            # Draw network dot with pulse
            pulse = 8 + 4 * math.sin(current_time * 3 + i)
            self.radar_canvas.create_oval(x - pulse, y - pulse, x + pulse, y + pulse,
                                          fill=color, outline=color, width=2)
            
            # Draw device type icon
            self.radar_canvas.create_text(x, y, text=data['type'][:2],
                                          font=("Courier New", 8, "bold"), fill="white")
            
            # Draw label: signal % and SSID (click for distance details)
            label = f"{sig}%\n{data['ssid'][:12]}"
            self.radar_canvas.create_text(x + 30, y, text=label,
                                          font=("Courier New", 7), fill="white", anchor="w")
        
        # Draw mode indicator in corner
        mode_text = "STATIC" if self.radar_system.state.mode == RadarMode.STATIC_DESKTOP else "MOBILE"
        self.radar_canvas.create_text(w - 60, 20, text=f"[{mode_text}]",
                                      font=("Courier New", 9, "bold"),
                                      fill=theme["text_accent"])
    
    def _draw_heatmap(self, cx, cy, r, w, h):
        """Draw signal strength heatmap - uses radar system for position consistency."""
        grid_size = 20
        influence_radius = 120
        
        # Use radar system's network positions for consistency
        net_positions = []
        sorted_networks = sorted(self.networks.items(), key=lambda x: x[1]['signal'], reverse=True)
        
        for i, (bssid, data) in enumerate(sorted_networks[:20]):
            sig = data['signal']
            
            # Get position from radar system if available
            blip = self.radar_system.blips.get(bssid)
            if blip:
                x = cx + r * blip.distance_ratio * math.cos(math.radians(blip.angle_degrees - 90))
                y = cy + r * blip.distance_ratio * math.sin(math.radians(blip.angle_degrees - 90))
            else:
                # Fallback to stored position
                pos = self.network_positions.get(bssid)
                if pos:
                    x, y = pos
                else:
                    # Calculate fallback
                    channel = data.get('channel', 1)
                    distance_ratio = 1.0 - (sig / 100.0)
                    distance_ratio = max(0.15, distance_ratio)
                    if channel <= 14:
                        base_angle = 15 + (channel - 1) * (150 / 13)
                    else:
                        base_angle = 195 + ((channel - 36) % 140) * (150 / 140)
                    angle_rad = math.radians(base_angle - 90)
                    x = cx + r * distance_ratio * math.cos(angle_rad)
                    y = cy + r * distance_ratio * math.sin(angle_rad)
            
            net_positions.append((x, y, sig))
        
        for gx in range(0, w, grid_size):
            for gy in range(0, h, grid_size):
                cell_cx = gx + grid_size // 2
                cell_cy = gy + grid_size // 2
                
                max_signal = 0
                for net_x, net_y, sig in net_positions:
                    dist = math.sqrt((cell_cx - net_x)**2 + (cell_cy - net_y)**2)
                    if dist < influence_radius:
                        influence = sig * (1.0 - dist / influence_radius)
                        max_signal = max(max_signal, influence)
                
                if max_signal > 5:
                    color = self._get_heat_color(max_signal)
                    self.radar_canvas.create_rectangle(
                        gx, gy, gx + grid_size, gy + grid_size,
                        fill=color, outline="", stipple="gray50"
                    )
    
    def _get_heat_color(self, signal):
        """Get heatmap color for signal strength."""
        strength = max(0, min(100, signal))
        
        if strength < 25:
            r, g, b = 0, int(255 * strength / 25), 255
        elif strength < 50:
            ratio = (strength - 25) / 25
            r, g, b = 0, 255, int(255 * (1 - ratio))
        elif strength < 75:
            ratio = (strength - 50) / 25
            r, g, b = int(255 * ratio), 255, 0
        else:
            ratio = (strength - 75) / 25
            r, g, b = 255, int(255 * (1 - ratio)), 0
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _draw_matrix_rain(self):
        """Draw Matrix-style data rain effect."""
        try:
            canvas = self.matrix_canvas
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            
            if w < 50 or h < 10:
                return
            
            canvas.delete("matrix")
            self.matrix_counter += 1
            
            # Update falling characters
            new_chars = []
            for char_data in self.matrix_chars:
                char_data['y'] += char_data['speed']
                if char_data['y'] < h + 20:
                    new_chars.append(char_data)
            self.matrix_chars = new_chars
            
            # Spawn new characters
            if len(self.matrix_chars) < 60 and self.effects_enabled:
                import random
                data_pool = self._generate_matrix_data()
                
                for _ in range(2):
                    self.matrix_chars.append({
                        'x': random.randint(10, max(w - 20, 20)),
                        'y': random.randint(-50, -10),
                        'text': random.choice(data_pool),
                        'speed': random.choice([0.3, 0.5, 0.7, 1.0]),
                        'color': random.choice(['#00ff00'] * 4 + ['#00ff88', '#00aa00'])
                    })
            
            # Draw characters
            for char_data in self.matrix_chars:
                fade = max(0, min(1, 1 - char_data['y'] / (h * 1.5)))
                if fade > 0.1:
                    canvas.create_text(
                        char_data['x'], char_data['y'],
                        text=char_data['text'],
                        fill=char_data['color'],
                        font=("Courier New", 9, "bold"),
                        tag="matrix"
                    )
        except Exception:
            pass
    
    def _generate_matrix_data(self):
        """Generate data for matrix rain."""
        import random
        data = []
        
        # Network data
        for bssid, net_data in list(self.networks.items())[:10]:
            data.extend([
                net_data['ssid'][:10],
                f"{net_data['signal']}%",
                net_data['security'][:5],
                bssid[-8:]
            ])
        
        # Matrix characters
        data.extend(['█', '▓', '░', '║', '═', '0', '1', '●', '◆', '■'])
        
        # Cyberpunk keywords
        data.extend(['NEXUS', 'SCAN', 'DATA', 'SIGNAL', 'NETWORK', 'THREAT', 'ACTIVE'])
        
        return data if data else ['MATRIX', 'DATA', 'FLOW']
    
    def _on_network_selected(self, event=None):
        """Handle network selection for hydrophone."""
        selected = self.network_select.get()
        if selected:
            # Find BSSID
            for bssid, data in self.networks.items():
                if data['ssid'] == selected:
                    self.selected_network = bssid
                    self.audio_playing = True
                    self.audio_status.config(text=f"🎧 {selected[:12]}", fg="#00ff00")
                    
                    # Start audio thread
                    if self.audio_thread is None or not self.audio_thread.is_alive():
                        self.audio_thread = threading.Thread(target=self._play_network_audio, daemon=True)
                        self.audio_thread.start()
                    break
    
    def _play_network_audio(self):
        """
        Play sonar audio for selected network.
        
        In STATIC mode: Simple ping based on signal strength
        In MOBILE mode: Alien motion tracker style - faster beeps when signal improves
        """
        if not winsound:
            return
        
        last_signal = 0
        peak_signal = 0
        
        while self.audio_playing and self.selected_network:
            try:
                if self.selected_network in self.networks:
                    data = self.networks[self.selected_network]
                    signal = data['signal']
                    
                    # Track signal changes for mobile mode
                    signal_delta = signal - last_signal
                    last_signal = signal
                    if signal > peak_signal:
                        peak_signal = signal
                    
                    # Check radar mode
                    is_mobile = self.radar_system.state.mode == RadarMode.MOBILE_HOMING
                    
                    if is_mobile:
                        # MOBILE MODE: Alien motion tracker style
                        # Faster beeps when getting closer (signal improving)
                        # Higher pitch when signal is strong
                        
                        # Base frequency on signal strength
                        base_freq = 300 + int((signal / 100.0) * 1200)
                        
                        # Add urgency if signal is improving
                        if signal_delta > 2:
                            # Signal getting stronger - shorter gaps, higher pitch
                            freq = base_freq + 200
                            duration = int(80 * self.wave_intensity)
                            gap = int(100 * (1 - signal / 100.0) + 50)
                        elif signal_delta < -2:
                            # Signal weakening - longer gaps, lower pitch
                            freq = base_freq - 100
                            duration = int(60 * self.wave_intensity)
                            gap = int(400 * (1 - signal / 100.0) + 200)
                        else:
                            # Stable - normal beep
                            freq = base_freq
                            duration = int(70 * self.wave_intensity)
                            gap = int(250 * (1 - signal / 100.0) + 100)
                        
                        # Extra rapid beeping when very close (high signal)
                        if signal >= 80:
                            # Rapid ping like motion tracker when close
                            for _ in range(3):
                                if duration > 10:
                                    winsound.Beep(freq + 300, 30)
                                    time.sleep(0.05)
                    else:
                        # STATIC MODE: Traditional sonar ping
                        freq = 200 + int((signal / 100.0) * 1800)
                        duration = int(100 * self.wave_intensity)
                        gap = int(300 * (1 - signal / 100.0) + 100)
                    
                    # Play main beep
                    if duration > 10:
                        winsound.Beep(freq, duration)
                    
                    # Wait before next ping
                    time.sleep(gap / 1000.0)
                else:
                    break
            except Exception:
                time.sleep(0.1)
    
    def _show_network_details(self, bssid):
        """Show network details popup with full intelligence dossier."""
        if bssid not in self.networks:
            return
        
        data = self.networks[bssid]
        
        details = tk.Toplevel(self.root)
        details.title(f"📡 {data['ssid'][:40]}")
        details.geometry("520x720")
        details.configure(bg="#0a0e27")
        
        # Create scrollable frame
        canvas = tk.Canvas(details, bg="#0a0e27", highlightthickness=0)
        scrollbar = ttk.Scrollbar(details, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#0a0e27")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header with device icon
        device_icon = data.get('device_icon', '📡')
        tk.Label(scrollable_frame, text=f"{device_icon} {data['ssid']}", 
                 font=("Courier New", 14, "bold"),
                 fg="#00ffff", bg="#0a0e27").pack(pady=10)
        
        tk.Label(scrollable_frame, text="═" * 55, fg="#ff00ff", bg="#0a0e27").pack()
        
        # Check for alerts
        alerts = self.spoof_detector.get_alerts_for_bssid(bssid)
        if alerts:
            alert_color = "#ff0000" if any(a.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] for a in alerts) else "#ffaa00"
            alert_text = f"⚠️ {len(alerts)} SECURITY ALERT(S) DETECTED"
            tk.Label(scrollable_frame, text=alert_text, font=("Courier New", 10, "bold"),
                     fg=alert_color, bg="#0a0e27").pack(pady=5)
            for alert in alerts[:3]:
                tk.Label(scrollable_frame, text=f"   • {alert.description}", 
                         font=("Courier New", 8), fg=alert_color, bg="#0a0e27").pack()
        
        # Device Fingerprint section
        device_type = data.get('device_type', 'unknown')
        device_desc = data.get('device_desc', 'Unknown device')
        device_conf = data.get('device_confidence', 0)
        device_tags = data.get('device_tags', [])
        
        device_info = f"""
🔍 DEVICE FINGERPRINT
───────────────────────────────────────────────
  Type: {device_icon} {device_type.upper()}
  Description: {device_desc}
  Confidence: {device_conf}%
  Tags: {', '.join(device_tags[:5]) if device_tags else 'None'}
"""
        tk.Label(scrollable_frame, text=device_info, font=("Courier New", 9), fg="#ff00ff",
                 bg="#0a0e27", justify="left").pack(padx=15, anchor="w")
        
        # Distance & Wall estimation section
        dist = data.get('distance', 0)
        margin = data.get('distance_margin', 50)
        confidence = data.get('confidence', 0)
        env = data.get('environment', 'Unknown')
        wall_desc = data.get('wall_desc', 'Unknown')
        wall_count = data.get('wall_count', 0)
        
        wall_icons = "🧱" * wall_count if wall_count > 0 else "👁️"
        
        distance_info = f"""
📏 DISTANCE & LOCATION
───────────────────────────────────────────────
  Estimated Distance: ~{dist:.0f} meters (±{margin}%)
  Confidence: {confidence}%
  Environment: {env}
  Obstacle Estimate: {wall_icons} {wall_desc}
"""
        tk.Label(scrollable_frame, text=distance_info, font=("Courier New", 9), fg="#00ff00",
                 bg="#0a0e27", justify="left").pack(padx=15, anchor="w")
        
        # Signal Stability section
        stability = data.get('stability', 'unknown')
        stability_score = data.get('stability_score', 50)
        jitter = data.get('jitter', 0)
        volatility = data.get('volatility', 0)
        trend = data.get('trend', 'stable')
        
        # Stability bar
        stability_bar = self.stability_tracker.get_stability_bar(bssid, 20)
        
        trend_icons = {"improving": "📈", "declining": "📉", "stable": "➡️", "fluctuating": "〰️"}
        trend_icon = trend_icons.get(trend, "➡️")
        
        stability_info = f"""
📊 SIGNAL STABILITY
───────────────────────────────────────────────
  Rating: {stability.upper()} ({stability_score}%)
  Stability: [{stability_bar}]
  Jitter: ±{jitter:.1f} dB
  Volatility: {volatility:.1f}%
  Trend: {trend_icon} {trend.upper()}
"""
        tk.Label(scrollable_frame, text=stability_info, font=("Courier New", 9), fg="#00ffff",
                 bg="#0a0e27", justify="left").pack(padx=15, anchor="w")
        
        # Signal Metrics section
        sig_quality = data.get('signal_quality', 'Unknown')
        snr = data.get('snr', None)
        snr_quality = data.get('snr_quality', 'Unknown')
        noise = data.get('noise_level', 'Unknown')
        
        snr_text = f"{snr} dB ({snr_quality})" if snr else "N/A"
        
        signal_info = f"""
📶 SIGNAL METRICS
───────────────────────────────────────────────
  Signal Strength: {data['signal']}% ({sig_quality})
  SNR: {snr_text}
  Noise Level: {noise}
"""
        tk.Label(scrollable_frame, text=signal_info, font=("Courier New", 9), fg="#ffff00",
                 bg="#0a0e27", justify="left").pack(padx=15, anchor="w")
        
        # Network Info section
        network_info = f"""
📡 NETWORK INFO
───────────────────────────────────────────────
  Channel: {data['channel']} ({data.get('band', '2.4GHz')})
  Security: {data['security']}
  BSSID: {data['bssid']}
  Vendor: {data.get('vendor', 'Unknown')}
"""
        tk.Label(scrollable_frame, text=network_info, font=("Courier New", 9), fg="#aaaaaa",
                 bg="#0a0e27", justify="left").pack(padx=15, anchor="w")
        
        # Disclaimer
        tk.Label(scrollable_frame, text="═" * 55, fg="#ff00ff", bg="#0a0e27").pack(pady=5)
        
        disclaimer = "⚠️ All analysis based on passive RF data only.\n   No active scanning or packet injection used."
        tk.Label(scrollable_frame, text=disclaimer, font=("Courier New", 8), fg="#666666",
                 bg="#0a0e27", justify="center").pack()
        
        tk.Button(scrollable_frame, text="Close", command=details.destroy,
                  bg="#ff00ff", fg="#000000", font=("Courier New", 10, "bold")).pack(pady=15)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _clear_data(self):
        """Clear all data."""
        self.networks.clear()
        self.signal_history.clear()
        self.scan_count = 0
        
        for item in self.network_tree.get_children():
            self.network_tree.delete(item)
        
        self._update_status("[RESET] All data cleared")
        self.log_event("SYSTEM", "Data cleared")
        messagebox.showinfo("Cleared", "All data has been cleared")
    
    def _export_results(self):
        """Export scan results."""
        if not self.networks:
            messagebox.showwarning("No Data", "No networks to export")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")],
            initialfile=f"nexus_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith(".csv"):
                with open(filename, 'w') as f:
                    f.write("SSID,Signal,Channel,Security,BSSID,Type\n")
                    for bssid, data in self.networks.items():
                        f.write(f"{data['ssid']},{data['signal']},{data['channel']},"
                               f"{data['security']},{bssid},{data['type']}\n")
            else:
                import json
                with open(filename, 'w') as f:
                    json.dump(self.networks, f, indent=2)
            
            messagebox.showinfo("Success", f"Exported to:\n{filename}")
            self.log_event("EXPORT", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def _export_security_report(self):
        """Export security report."""
        if not self.networks:
            messagebox.showwarning("No Data", "No networks to report")
            return
        
        # Switch to security tab
        self.notebook.select(2)
        
        self._update_security_audit()
        self.log_event("REPORT", "Security report generated")
        messagebox.showinfo("Report", "Security report displayed in Security Audit tab")
    
    def _update_status(self, message):
        """Update status bar."""
        self.status_label.config(text=message)
    
    def _on_close(self):
        """Handle window close with proper cleanup."""
        # Stop scanning
        self.is_scanning = False
        self.audio_playing = False
        
        # Stop sonar audio
        if self.sonar:
            try:
                self.sonar.stop_all()
            except:
                pass
        
        # Give threads time to stop
        time.sleep(0.3)
        
        # Destroy window
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Entry point for the GUI application."""
    app = NexusApp()
    app.run()


if __name__ == "__main__":
    main()
