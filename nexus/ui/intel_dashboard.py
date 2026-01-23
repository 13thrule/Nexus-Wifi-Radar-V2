"""
NEXUS Intelligence Dashboard - Three-Panel Design

A redesigned intelligence UI with:
- Left Panel: Intelligence Summary (stats, counts)
- Center Panel: Intelligence Feed (color-coded scrolling events)
- Right Panel: Detail Inspector (click to inspect)
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Dict, List, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
import time
import math


class EventType(Enum):
    """Intelligence event types with color coding."""
    THREAT = "threat"        # Red - security threats
    ANOMALY = "anomaly"      # Yellow - behavioral anomalies
    INSIGHT = "insight"      # Cyan - new intelligence insights
    PASSIVE = "passive"      # Green - normal passive observations
    SYSTEM = "system"        # Gray - system messages
    ALERT = "alert"          # Magenta - high priority alerts


@dataclass
class IntelEvent:
    """An intelligence event for the feed."""
    event_type: EventType
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    network_bssid: Optional[str] = None
    network_ssid: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: int = 1  # 1-5 scale
    
    @property
    def time_str(self) -> str:
        return self.timestamp.strftime("%H:%M:%S")
    
    @property
    def type_icon(self) -> str:
        icons = {
            EventType.THREAT: "🚨",
            EventType.ANOMALY: "⚠️",
            EventType.INSIGHT: "💡",
            EventType.PASSIVE: "📡",
            EventType.SYSTEM: "⚙️",
            EventType.ALERT: "🔴",
        }
        return icons.get(self.event_type, "•")


class IntelligenceDashboard:
    """
    Three-panel intelligence dashboard for NEXUS.
    
    Layout:
    ┌────────────┬─────────────────────────┬────────────────┐
    │  SUMMARY   │     INTELLIGENCE        │    DETAIL      │
    │  PANEL     │     FEED                │    INSPECTOR   │
    │            │     (scrolling)         │                │
    │  Stats     │     Color-coded         │    Selected    │
    │  Counters  │     events              │    item info   │
    │            │                         │                │
    └────────────┴─────────────────────────┴────────────────┘
    """
    
    def __init__(self, parent: tk.Frame, theme: Dict, app_ref=None):
        """
        Initialize the dashboard.
        
        Args:
            parent: Parent frame to build dashboard in
            theme: UI theme dictionary
            app_ref: Reference to main NexusApp for callbacks
        """
        self.parent = parent
        self.theme = theme
        self.app = app_ref
        
        # Event storage
        self.events: List[IntelEvent] = []
        self.max_events = 500
        self.selected_event: Optional[IntelEvent] = None
        
        # Stats counters
        self.stats = {
            "total_networks": 0,
            "threats": 0,
            "unknown_devices": 0,
            "stability_anomalies": 0,
            "vendor_anomalies": 0,
            "weak_signals": 0,
            "hidden_networks": 0,
            "open_networks": 0,
            "mesh_groups": 0,
            "moving_devices": 0,
        }
        
        # Animation state
        self.glow_phase = 0
        self.animation_id = None
        
        # Network tracking for discovery detection
        self._known_networks: set = set()
        self._scan_count = 0
        self._last_summary_scan = 0
        
        # Build the dashboard
        self._build_dashboard()
    
    def _build_dashboard(self):
        """Build the three-panel dashboard layout."""
        # Main container with header
        self.main_frame = tk.Frame(self.parent, bg=self.theme["bg_main"])
        self.main_frame.pack(fill="both", expand=True)
        
        # ═══════════════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════════════
        self._build_header()
        
        # ═══════════════════════════════════════════════════════════════════
        # THREE-PANEL LAYOUT
        # ═══════════════════════════════════════════════════════════════════
        self.panels_frame = tk.Frame(self.main_frame, bg=self.theme["bg_main"])
        self.panels_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure grid weights for responsive layout
        self.panels_frame.columnconfigure(0, weight=1, minsize=250)  # Left panel
        self.panels_frame.columnconfigure(1, weight=3, minsize=400)  # Center panel
        self.panels_frame.columnconfigure(2, weight=2, minsize=300)  # Right panel
        self.panels_frame.rowconfigure(0, weight=1)
        
        # Build panels
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        
        # Start glow animation
        self._animate_glow()
    
    def _build_header(self):
        """Build the dashboard header."""
        header_frame = tk.Frame(self.main_frame, bg=self.theme["bg_panel"], height=60)
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        header_frame.pack_propagate(False)
        
        # ASCII art header
        header_text = "╔═══════════════════════════════════════════════════════════════════════════════════════════════════╗\n"
        header_text += "║  🧠 NEXUS INTELLIGENCE DASHBOARD // PASSIVE ANALYSIS CORE                                          ║\n"
        header_text += "╚═══════════════════════════════════════════════════════════════════════════════════════════════════╝"
        
        self.header_label = tk.Label(
            header_frame,
            text=header_text,
            font=("Courier New", 9, "bold"),
            fg=self.theme["text_accent"],
            bg=self.theme["bg_panel"],
            justify="left"
        )
        self.header_label.pack(fill="x", padx=5, pady=5)
        
        # Status indicator
        self.status_label = tk.Label(
            header_frame,
            text="● MONITORING",
            font=("Courier New", 8),
            fg="#00ff00",
            bg=self.theme["bg_panel"]
        )
        self.status_label.place(relx=0.95, rely=0.5, anchor="e")
    
    def _build_left_panel(self):
        """Build the left summary panel with stats."""
        left_frame = tk.LabelFrame(
            self.panels_frame,
            text="📊 INTELLIGENCE SUMMARY",
            font=("Courier New", 9, "bold"),
            fg=self.theme["text_accent"],
            bg=self.theme["bg_panel"],
            bd=2,
            relief="ridge"
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3), pady=0)
        
        # Stat cards container
        stats_container = tk.Frame(left_frame, bg=self.theme["bg_panel"])
        stats_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Build stat cards
        self.stat_widgets = {}
        stat_defs = [
            ("total_networks", "📡 NETWORKS", "#00ff88"),
            ("threats", "🚨 THREATS", "#ff0000"),
            ("unknown_devices", "❓ UNKNOWN", "#ff8800"),
            ("stability_anomalies", "📉 UNSTABLE", "#ffff00"),
            ("vendor_anomalies", "🏭 VENDOR ⚠️", "#ff00ff"),
            ("weak_signals", "📶 WEAK SIG", "#888888"),
            ("hidden_networks", "👻 HIDDEN", "#00ffff"),
            ("open_networks", "🔓 OPEN", "#ff4444"),
            ("mesh_groups", "🔗 MESH", "#00ff00"),
            ("moving_devices", "🚶 MOVING", "#00ffff"),
        ]
        
        for i, (key, label, color) in enumerate(stat_defs):
            card = self._create_stat_card(stats_container, key, label, color)
            card.pack(fill="x", pady=2)
    
    def _create_stat_card(self, parent: tk.Frame, key: str, label: str, color: str) -> tk.Frame:
        """Create a single stat card widget."""
        card = tk.Frame(parent, bg=self.theme["bg_main"], bd=1, relief="solid")
        
        # Label
        lbl = tk.Label(
            card,
            text=label,
            font=("Courier New", 8),
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_main"],
            anchor="w"
        )
        lbl.pack(side="left", padx=5, pady=3)
        
        # Value
        val = tk.Label(
            card,
            text="0",
            font=("Courier New", 12, "bold"),
            fg=color,
            bg=self.theme["bg_main"],
            anchor="e"
        )
        val.pack(side="right", padx=5, pady=3)
        
        # Severity bar canvas
        bar = tk.Canvas(
            card,
            width=50,
            height=8,
            bg=self.theme["bg_main"],
            highlightthickness=0
        )
        bar.pack(side="right", padx=5)
        
        self.stat_widgets[key] = {
            "card": card,
            "label": lbl,
            "value": val,
            "bar": bar,
            "color": color
        }
        
        return card
    
    def _build_center_panel(self):
        """Build the center intelligence feed panel."""
        center_frame = tk.LabelFrame(
            self.panels_frame,
            text="📜 INTELLIGENCE FEED",
            font=("Courier New", 9, "bold"),
            fg=self.theme["text_accent"],
            bg=self.theme["bg_panel"],
            bd=2,
            relief="ridge"
        )
        center_frame.grid(row=0, column=1, sticky="nsew", padx=3, pady=0)
        
        # Filter bar
        filter_frame = tk.Frame(center_frame, bg=self.theme["bg_panel"])
        filter_frame.pack(fill="x", padx=5, pady=3)
        
        tk.Label(
            filter_frame,
            text="FILTER:",
            font=("Courier New", 8),
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_panel"]
        ).pack(side="left", padx=2)
        
        # Filter buttons
        self.filter_buttons = {}
        filters = [
            ("all", "ALL", self.theme["text_primary"]),
            ("threat", "🚨 THREAT", "#ff0000"),
            ("anomaly", "⚠️ ANOMALY", "#ffff00"),
            ("insight", "💡 INSIGHT", "#00ffff"),
        ]
        
        for key, text, color in filters:
            btn = tk.Button(
                filter_frame,
                text=text,
                font=("Courier New", 7),
                fg=color,
                bg=self.theme["bg_main"],
                activebackground=color,
                activeforeground="#000000",
                relief="flat",
                bd=1,
                padx=5,
                cursor="hand2",
                command=lambda k=key: self._filter_feed(k)
            )
            btn.pack(side="left", padx=2)
            self.filter_buttons[key] = btn
        
        # Clear button
        tk.Button(
            filter_frame,
            text="🗑️ CLEAR",
            font=("Courier New", 7),
            fg="#888888",
            bg=self.theme["bg_main"],
            relief="flat",
            bd=1,
            cursor="hand2",
            command=self._clear_feed
        ).pack(side="right", padx=2)
        
        # Feed scrollable area
        feed_container = tk.Frame(center_frame, bg=self.theme["bg_main"])
        feed_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbar for feed
        self.feed_canvas = tk.Canvas(
            feed_container,
            bg=self.theme["bg_main"],
            highlightthickness=0
        )
        
        scrollbar = ttk.Scrollbar(
            feed_container,
            orient="vertical",
            command=self.feed_canvas.yview
        )
        
        self.feed_frame = tk.Frame(self.feed_canvas, bg=self.theme["bg_main"])
        
        self.feed_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.feed_canvas.pack(side="left", fill="both", expand=True)
        
        self.feed_window = self.feed_canvas.create_window(
            (0, 0),
            window=self.feed_frame,
            anchor="nw"
        )
        
        # Configure scroll region
        def configure_scroll(event):
            self.feed_canvas.configure(scrollregion=self.feed_canvas.bbox("all"))
        self.feed_frame.bind("<Configure>", configure_scroll)
        
        def configure_width(event):
            self.feed_canvas.itemconfig(self.feed_window, width=event.width)
        self.feed_canvas.bind("<Configure>", configure_width)
        
        # Mousewheel binding - only for this canvas, not bind_all
        def on_mousewheel(event):
            self.feed_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.feed_canvas.bind("<MouseWheel>", on_mousewheel)
        self.feed_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Store feed item widgets
        self.feed_items: List[tk.Frame] = []
        self.current_filter = "all"
    
    def _build_right_panel(self):
        """Build the right detail inspector panel."""
        right_frame = tk.LabelFrame(
            self.panels_frame,
            text="🔍 DETAIL INSPECTOR",
            font=("Courier New", 9, "bold"),
            fg=self.theme["text_accent"],
            bg=self.theme["bg_panel"],
            bd=2,
            relief="ridge"
        )
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(3, 0), pady=0)
        
        # Detail content
        self.detail_frame = tk.Frame(right_frame, bg=self.theme["bg_panel"])
        self.detail_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initial placeholder
        self._show_placeholder_detail()
    
    def _show_placeholder_detail(self):
        """Show placeholder when no item is selected."""
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        placeholder = tk.Label(
            self.detail_frame,
            text="╔════════════════════════════╗\n"
                 "║                            ║\n"
                 "║   SELECT AN EVENT FROM     ║\n"
                 "║   THE FEED TO INSPECT      ║\n"
                 "║                            ║\n"
                 "║   💡 Double-click events   ║\n"
                 "║      for full details      ║\n"
                 "║                            ║\n"
                 "╚════════════════════════════╝",
            font=("Courier New", 9),
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_panel"],
            justify="center"
        )
        placeholder.pack(expand=True)
    
    def _show_event_detail(self, event: IntelEvent):
        """Show details for a selected event."""
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        self.selected_event = event
        
        # Type/Time header
        colors = {
            EventType.THREAT: "#ff0000",
            EventType.ANOMALY: "#ffff00",
            EventType.INSIGHT: "#00ffff",
            EventType.PASSIVE: "#00ff00",
            EventType.SYSTEM: "#888888",
            EventType.ALERT: "#ff00ff",
        }
        color = colors.get(event.event_type, self.theme["text_primary"]) or self.theme["text_primary"]
        
        header = tk.Label(
            self.detail_frame,
            text=f"{event.type_icon} {event.event_type.value.upper()}",
            font=("Courier New", 12, "bold"),
            fg=color,
            bg=self.theme["bg_panel"]
        )
        header.pack(fill="x", pady=(0, 5))
        
        # Timestamp
        time_lbl = tk.Label(
            self.detail_frame,
            text=f"🕐 {event.time_str}",
            font=("Courier New", 9),
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_panel"]
        )
        time_lbl.pack(fill="x")
        
        # Severity bar
        severity_frame = tk.Frame(self.detail_frame, bg=self.theme["bg_panel"])
        severity_frame.pack(fill="x", pady=5)
        
        tk.Label(
            severity_frame,
            text="SEVERITY:",
            font=("Courier New", 8),
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_panel"]
        ).pack(side="left")
        
        for i in range(5):
            c = color if i < event.severity else self.theme["bg_main"]
            bar = tk.Canvas(severity_frame, width=20, height=10, bg=str(c), highlightthickness=1,
                           highlightbackground=str(color))
            bar.pack(side="left", padx=1)
        
        # Divider
        tk.Label(
            self.detail_frame,
            text="─" * 35,
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_panel"]
        ).pack(fill="x", pady=5)
        
        # Title
        title_lbl = tk.Label(
            self.detail_frame,
            text=event.title,
            font=("Courier New", 10, "bold"),
            fg=self.theme["text_primary"],
            bg=self.theme["bg_panel"],
            wraplength=280,
            justify="left"
        )
        title_lbl.pack(fill="x", anchor="w")
        
        # Message
        msg_text = tk.Text(
            self.detail_frame,
            font=("Courier New", 9),
            fg=self.theme["text_secondary"],
            bg=self.theme["bg_main"],
            height=4,
            wrap="word",
            bd=1,
            relief="solid"
        )
        msg_text.pack(fill="x", pady=5)
        msg_text.insert("1.0", event.message)
        msg_text.config(state="disabled")
        
        # Network info (if applicable)
        if event.network_ssid or event.network_bssid:
            tk.Label(
                self.detail_frame,
                text="─" * 35,
                fg=self.theme["text_secondary"],
                bg=self.theme["bg_panel"]
            ).pack(fill="x", pady=5)
            
            tk.Label(
                self.detail_frame,
                text="📡 ASSOCIATED NETWORK",
                font=("Courier New", 9, "bold"),
                fg=self.theme["text_accent"],
                bg=self.theme["bg_panel"]
            ).pack(fill="x", anchor="w")
            
            if event.network_ssid:
                tk.Label(
                    self.detail_frame,
                    text=f"SSID: {event.network_ssid}",
                    font=("Courier New", 9),
                    fg=self.theme["text_primary"],
                    bg=self.theme["bg_panel"]
                ).pack(fill="x", anchor="w")
            
            if event.network_bssid:
                tk.Label(
                    self.detail_frame,
                    text=f"BSSID: {event.network_bssid}",
                    font=("Courier New", 8),
                    fg=self.theme["text_secondary"],
                    bg=self.theme["bg_panel"]
                ).pack(fill="x", anchor="w")
        
        # Additional details
        if event.details:
            tk.Label(
                self.detail_frame,
                text="─" * 35,
                fg=self.theme["text_secondary"],
                bg=self.theme["bg_panel"]
            ).pack(fill="x", pady=5)
            
            tk.Label(
                self.detail_frame,
                text="📋 DETAILS",
                font=("Courier New", 9, "bold"),
                fg=self.theme["text_accent"],
                bg=self.theme["bg_panel"]
            ).pack(fill="x", anchor="w")
            
            for key, value in event.details.items():
                tk.Label(
                    self.detail_frame,
                    text=f"{key}: {value}",
                    font=("Courier New", 8),
                    fg=self.theme["text_secondary"],
                    bg=self.theme["bg_panel"],
                    anchor="w"
                ).pack(fill="x")
        
        # Action buttons
        btn_frame = tk.Frame(self.detail_frame, bg=self.theme["bg_panel"])
        btn_frame.pack(fill="x", pady=10, side="bottom")
        
        if event.network_bssid and self.app:
            tk.Button(
                btn_frame,
                text="🔍 INSPECT",
                font=("Courier New", 8),
                fg="#000000",
                bg=self.theme["text_accent"],
                command=lambda b=event.network_bssid: self._inspect_network(str(b)) if b else None
            ).pack(side="left", padx=2)
        
        tk.Button(
            btn_frame,
            text="📋 COPY",
            font=("Courier New", 8),
            fg="#000000",
            bg="#888888",
            command=lambda: self._copy_event_to_clipboard(event)
        ).pack(side="left", padx=2)
    
    def _create_feed_item(self, event: IntelEvent) -> tk.Frame:
        """Create a feed item widget for an event."""
        colors = {
            EventType.THREAT: ("#ff0000", "#330000"),
            EventType.ANOMALY: ("#ffff00", "#333300"),
            EventType.INSIGHT: ("#00ffff", "#003333"),
            EventType.PASSIVE: ("#00ff00", "#003300"),
            EventType.SYSTEM: ("#888888", "#222222"),
            EventType.ALERT: ("#ff00ff", "#330033"),
        }
        fg_color, bg_color = colors.get(event.event_type, (self.theme["text_primary"], self.theme["bg_main"]))
        
        # Item frame
        item = tk.Frame(
            self.feed_frame,
            bg=bg_color,
            bd=1,
            relief="solid",
            cursor="hand2"
        )
        
        # Left border indicator
        indicator = tk.Frame(item, bg=fg_color, width=4)
        indicator.pack(side="left", fill="y")
        
        # Content area
        content = tk.Frame(item, bg=bg_color)
        content.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        
        # Top row: time + type
        top_row = tk.Frame(content, bg=bg_color)
        top_row.pack(fill="x")
        
        time_lbl = tk.Label(
            top_row,
            text=event.time_str,
            font=("Courier New", 7),
            fg="#888888",
            bg=bg_color
        )
        time_lbl.pack(side="left")
        
        type_lbl = tk.Label(
            top_row,
            text=f" {event.type_icon} {event.event_type.value.upper()}",
            font=("Courier New", 7, "bold"),
            fg=fg_color,
            bg=bg_color
        )
        type_lbl.pack(side="left")
        
        # Severity dots
        for i in range(event.severity):
            dot = tk.Canvas(top_row, width=6, height=6, bg=bg_color, highlightthickness=0)
            dot.create_oval(1, 1, 5, 5, fill=fg_color)
            dot.pack(side="right", padx=1)
        
        # Title
        title_lbl = tk.Label(
            content,
            text=event.title[:50] + ("..." if len(event.title) > 50 else ""),
            font=("Courier New", 8, "bold"),
            fg=self.theme["text_primary"],
            bg=bg_color,
            anchor="w"
        )
        title_lbl.pack(fill="x")
        
        # Message preview
        msg_preview = event.message[:60] + ("..." if len(event.message) > 60 else "")
        msg_lbl = tk.Label(
            content,
            text=msg_preview,
            font=("Courier New", 7),
            fg=self.theme["text_secondary"],
            bg=bg_color,
            anchor="w"
        )
        msg_lbl.pack(fill="x")
        
        # Click binding
        def on_click(e, ev=event):
            self._show_event_detail(ev)
            # Highlight selected
            for fi in self.feed_items:
                fi.config(relief="solid")
            item.config(relief="raised")
        
        for widget in [item, indicator, content, top_row, time_lbl, type_lbl, title_lbl, msg_lbl]:
            widget.bind("<Button-1>", on_click)
        
        # Hover effect
        def on_enter(e):
            item.config(bd=2)
        def on_leave(e):
            item.config(bd=1)
        item.bind("<Enter>", on_enter)
        item.bind("<Leave>", on_leave)
        
        return item
    
    def add_event(self, event: IntelEvent):
        """Add a new event to the feed."""
        self.events.insert(0, event)
        
        # Trim old events
        if len(self.events) > self.max_events:
            self.events = self.events[:self.max_events]
        
        # Create and display feed item
        item = self._create_feed_item(event)
        
        # Pack new item at the top of the feed
        # We need to repack all items to maintain correct order
        # First, unpack all existing items
        for existing in self.feed_items:
            try:
                existing.pack_forget()
            except:
                pass
        
        # Insert new item at beginning of list
        self.feed_items.insert(0, item)
        
        # Repack all items in order (applying current filter)
        for i, feed_item in enumerate(self.feed_items):
            if i < len(self.events):
                evt = self.events[i]
                if self.current_filter == "all" or evt.event_type.value == self.current_filter:
                    try:
                        feed_item.pack(fill="x", pady=1)
                    except:
                        pass
        
        # Trim old feed items
        while len(self.feed_items) > 100:
            old_item = self.feed_items.pop()
            try:
                old_item.destroy()
            except:
                pass
        
        # Scroll to top
        try:
            self.feed_canvas.yview_moveto(0)
        except:
            pass
        
        # Update stats based on event type
        if event.event_type == EventType.THREAT:
            self.stats["threats"] += 1
        
        self._update_stats_display()
    
    def _filter_feed(self, filter_type: str):
        """Filter the feed by event type."""
        self.current_filter = filter_type
        
        # Update button states
        for key, btn in self.filter_buttons.items():
            if key == filter_type:
                btn.config(relief="sunken")
            else:
                btn.config(relief="flat")
        
        # Show/hide items
        for i, item in enumerate(self.feed_items):
            if i < len(self.events):
                event = self.events[i]
                if filter_type == "all" or event.event_type.value == filter_type:
                    item.pack(fill="x", pady=1)
                else:
                    item.pack_forget()
    
    def _clear_feed(self):
        """Clear all events from feed."""
        for item in self.feed_items:
            item.destroy()
        self.feed_items.clear()
        self.events.clear()
        self._show_placeholder_detail()
    
    def _inspect_network(self, bssid: str):
        """Open network details in main app."""
        if self.app and hasattr(self.app, '_show_network_details'):
            self.app._show_network_details(bssid)
    
    def _copy_event_to_clipboard(self, event: IntelEvent):
        """Copy event details to clipboard."""
        text = f"[{event.time_str}] {event.event_type.value.upper()}\n"
        text += f"Title: {event.title}\n"
        text += f"Message: {event.message}\n"
        if event.network_ssid:
            text += f"Network: {event.network_ssid} ({event.network_bssid})\n"
        if event.details:
            text += "Details:\n"
            for k, v in event.details.items():
                text += f"  {k}: {v}\n"
        
        self.parent.clipboard_clear()
        self.parent.clipboard_append(text)
    
    def update_stats(self, new_stats: Dict[str, int]):
        """Update the stats display."""
        self.stats.update(new_stats)
        self._update_stats_display()
    
    def _update_stats_display(self):
        """Refresh the stats widgets."""
        for key, value in self.stats.items():
            if key in self.stat_widgets:
                widget = self.stat_widgets[key]
                widget["value"].config(text=str(value))
                
                # Update severity bar
                bar = widget["bar"]
                bar.delete("all")
                
                # Calculate fill percentage (based on some max)
                max_vals = {
                    "total_networks": 50,
                    "threats": 10,
                    "unknown_devices": 20,
                    "stability_anomalies": 15,
                    "vendor_anomalies": 10,
                    "weak_signals": 30,
                    "hidden_networks": 10,
                    "open_networks": 5,
                    "mesh_groups": 10,
                    "moving_devices": 10,
                }
                max_val = max_vals.get(key, 10)
                fill_pct = min(1.0, value / max_val)
                
                bar.create_rectangle(
                    0, 0, int(50 * fill_pct), 8,
                    fill=widget["color"],
                    outline=""
                )
    
    def _animate_glow(self):
        """Animate glow effects on stat cards."""
        if not hasattr(self, 'main_frame') or not self.main_frame.winfo_exists():
            return
        
        self.glow_phase = (self.glow_phase + 0.1) % (2 * math.pi)
        
        # Pulse the header color
        intensity = int(128 + 40 * math.sin(self.glow_phase))
        
        # Pulse threat counter if > 0
        if self.stats.get("threats", 0) > 0 and "threats" in self.stat_widgets:
            pulse = int(200 + 55 * math.sin(self.glow_phase * 2))
            self.stat_widgets["threats"]["value"].config(fg=f"#{pulse:02x}0000")
        
        # Pulse hidden networks counter in cyan
        if self.stats.get("hidden_networks", 0) > 0 and "hidden_networks" in self.stat_widgets:
            pulse = int(200 + 55 * math.sin(self.glow_phase * 1.5))
            self.stat_widgets["hidden_networks"]["value"].config(fg=f"#00{pulse:02x}{pulse:02x}")
        
        # Continue animation
        self.animation_id = self.parent.after(100, self._animate_glow)
    
    def update_from_pic(self, pic):
        """
        Update dashboard from PassiveIntelligenceCore.
        
        This is called after each scan to refresh stats and generate events.
        """
        networks = pic.get_all_networks()
        self._scan_count += 1
        
        # Track previous network count for new network detection
        prev_count = self.stats.get("total_networks", 0)
        prev_networks = getattr(self, '_known_networks', set())
        current_networks = {n.bssid for n in networks}
        
        # Update stats
        self.stats["total_networks"] = len(networks)
        self.stats["threats"] = len(pic.get_spoof_alerts())
        self.stats["unknown_devices"] = len([n for n in networks if n.vendor == "Unknown"])
        self.stats["stability_anomalies"] = len([n for n in networks if n.temporal.stability_rating in ['unstable', 'erratic']])
        self.stats["weak_signals"] = len([n for n in networks if n.signal_percent < 30])
        self.stats["hidden_networks"] = len([n for n in networks if n.security.is_hidden])
        self.stats["open_networks"] = len([n for n in networks if "Open" in n.security.security_rating.value])
        self.stats["mesh_groups"] = len(pic.get_mesh_groups())
        self.stats["moving_devices"] = len([n for n in networks if n.temporal.movement_state.value in ['moving', 'fast_moving']])
        
        # Vendor anomalies
        self.stats["vendor_anomalies"] = len([n for n in networks 
            if n.vendor == "Unknown" or "Generic" in (n.vendor or "")])
        
        self._update_stats_display()
        
        # Generate events for notable findings
        self._generate_events_from_scan(networks, pic, prev_networks, current_networks)
        
        # Generate periodic summary (every 10 scans)
        if self._scan_count - self._last_summary_scan >= 10:
            self._generate_summary_event(networks, pic)
            self._last_summary_scan = self._scan_count
        
        # Store current networks for next comparison
        self._known_networks = current_networks
    
    def _generate_summary_event(self, networks, pic):
        """Generate a periodic summary event."""
        threats = self.stats["threats"]
        hidden = self.stats["hidden_networks"]
        total = self.stats["total_networks"]
        
        # Calculate average signal
        if networks:
            avg_signal = sum(n.signal_percent for n in networks) / len(networks)
        else:
            avg_signal = 0
        
        # Determine overall status
        if threats > 0:
            status = "⚠️ THREATS DETECTED"
            severity = 3
            event_type = EventType.ALERT
        elif hidden > 3:
            status = "👁️ MULTIPLE HIDDEN NETWORKS"
            severity = 2
            event_type = EventType.SYSTEM
        else:
            status = "✅ ENVIRONMENT STABLE"
            severity = 1
            event_type = EventType.SYSTEM
        
        event = IntelEvent(
            event_type=event_type,
            title=f"Scan Summary: {status}",
            message=f"Monitoring {total} networks | Avg signal: {avg_signal:.0f}%",
            severity=severity,
            details={
                "Networks": total,
                "Threats": threats,
                "Hidden": hidden,
                "Weak Signals": self.stats["weak_signals"],
                "Scans": self._scan_count
            }
        )
        self.add_event(event)
    
    def _generate_events_from_scan(self, networks, pic, prev_networks, current_networks):
        """Generate intelligence events from scan results."""
        # Track what we've already reported to avoid duplicates within same scan
        reported_bssids = set()
        
        # ═══════════════════════════════════════════════════════════════════
        # NEW NETWORK DETECTION
        # ═══════════════════════════════════════════════════════════════════
        new_networks = current_networks - prev_networks
        for net in networks:
            if net.bssid in new_networks and net.bssid not in reported_bssids:
                # Check if we recently reported this network (within last 50 events)
                recent_reports = [e for e in self.events[:50] 
                                 if e.network_bssid == net.bssid and e.event_type == EventType.INSIGHT]
                if not recent_reports:
                    event = IntelEvent(
                        event_type=EventType.INSIGHT,
                        title=f"New Network: {net.ssid or '[Hidden]'}",
                        message=f"Discovered {net.device_category.value.replace('_', ' ').title()} at {net.location.estimated_distance_m:.0f}m",
                        network_bssid=net.bssid,
                        network_ssid=net.ssid,
                        severity=1,
                        details={
                            "Vendor": net.vendor or "Unknown",
                            "Channel": net.channel,
                            "Signal": f"{net.signal_percent}%",
                            "Distance": f"{net.location.wall_description}"
                        }
                    )
                    self.add_event(event)
                    reported_bssids.add(net.bssid)
        
        # ═══════════════════════════════════════════════════════════════════
        # NETWORK DISAPPEARED DETECTION  
        # ═══════════════════════════════════════════════════════════════════
        disappeared = prev_networks - current_networks
        if prev_networks and len(disappeared) > 0 and len(disappeared) < 5:  # Avoid spam if many disappear
            for bssid in disappeared:
                recent_reports = [e for e in self.events[:30] 
                                 if e.network_bssid == bssid and "Disappeared" in e.title]
                if not recent_reports:
                    event = IntelEvent(
                        event_type=EventType.PASSIVE,
                        title=f"Network Disappeared",
                        message=f"Network {bssid[:8]}... no longer detected",
                        network_bssid=bssid,
                        severity=1,
                        details={"Status": "Out of range or powered off"}
                    )
                    self.add_event(event)
        
        # ═══════════════════════════════════════════════════════════════════
        # THREAT DETECTION (Spoof Alerts)
        # ═══════════════════════════════════════════════════════════════════
        for alert in pic.get_spoof_alerts():
            if alert.bssid in reported_bssids:
                continue
            # Check for recent duplicate reports
            existing = [e for e in self.events[:30] 
                       if e.network_bssid == alert.bssid and e.event_type == EventType.THREAT]
            if not existing:
                # Build detailed information
                details = {
                    "Risk Level": alert.security.spoof_risk.value,
                    "Indicators": ", ".join(alert.security.spoof_indicators[:3])
                }
                
                # Add vendor info with smart icons
                if alert.vendor and alert.vendor != "Unknown":
                    vendor_display = alert.vendor
                    if "ring" in alert.vendor.lower():
                        vendor_display = f"🚪 {alert.vendor}"
                    elif "amazon" in alert.vendor.lower():
                        vendor_display = f"🔊 {alert.vendor}"
                    elif "camera" in alert.vendor.lower():
                        vendor_display = f"📹 {alert.vendor}"
                    details["Vendor"] = vendor_display
                else:
                    details["Vendor"] = "Unknown / Randomized"
                
                # Add signal and distance
                details["Signal"] = f"{alert.signal_percent}% ({alert.signal_percent - 100}dBm)"
                details["Distance"] = f"~{alert.location.estimated_distance_m:.1f}m ({alert.location.wall_description})"
                
                # Add channel and security
                details["Channel"] = f"Ch.{alert.channel} ({alert.band})"
                if not alert.security.is_hidden:
                    details["Security"] = alert.security.security_rating.value
                else:
                    details["Type"] = "Hidden Network"
                
                # Add device classification
                device_type = alert.device_category.value.replace('_', ' ').title()
                details["Device Class"] = device_type
                
                # Add stability if available
                if hasattr(alert.temporal, 'stability_rating'):
                    details["Stability"] = f"{alert.temporal.stability_rating} ({alert.temporal.stability_score:.0f}%)"
                
                # Add first/last seen if available
                if hasattr(alert.temporal, 'first_seen'):
                    from datetime import datetime
                    first_seen = datetime.fromtimestamp(alert.temporal.first_seen).strftime("%H:%M:%S")
                    details["First Seen"] = first_seen
                
                event = IntelEvent(
                    event_type=EventType.THREAT,
                    title=f"Potential Spoof Detected: {alert.ssid or '[Hidden]'}",
                    message=f"Network shows {len(alert.security.spoof_indicators)} spoof indicators",
                    network_bssid=alert.bssid,
                    network_ssid=alert.ssid,
                    severity=4,
                    details=details
                )
                self.add_event(event)
                reported_bssids.add(alert.bssid)
        
        # ═══════════════════════════════════════════════════════════════════
        # STABILITY ANOMALIES
        # ═══════════════════════════════════════════════════════════════════
        for net in networks:
            if net.bssid in reported_bssids:
                continue
            if net.temporal.stability_rating == 'erratic':
                existing = [e for e in self.events[:30]
                           if e.network_bssid == net.bssid and "Erratic" in e.title]
                if not existing:
                    event = IntelEvent(
                        event_type=EventType.ANOMALY,
                        title=f"Erratic Signal: {net.ssid or '[Hidden]'}",
                        message=f"Signal stability is erratic ({net.temporal.stability_score:.0f}%)",
                        network_bssid=net.bssid,
                        network_ssid=net.ssid,
                        severity=2,
                        details={
                            "Signal": f"{net.signal_percent}%",
                            "Trend": net.temporal.signal_trend
                        }
                    )
                    self.add_event(event)
                    reported_bssids.add(net.bssid)
        
        # ═══════════════════════════════════════════════════════════════════
        # STRONG SIGNAL DETECTION (Close Proximity)
        # ═══════════════════════════════════════════════════════════════════
        for net in networks:
            if net.bssid in reported_bssids:
                continue
            if net.signal_percent >= 85 and net.location.estimated_distance_m < 5:
                existing = [e for e in self.events[:50]
                           if e.network_bssid == net.bssid and "Close" in e.title]
                if not existing:
                    event = IntelEvent(
                        event_type=EventType.INSIGHT,
                        title=f"Close Proximity: {net.ssid or '[Hidden]'}",
                        message=f"Very strong signal ({net.signal_percent}%) - likely same room",
                        network_bssid=net.bssid,
                        network_ssid=net.ssid,
                        severity=1,
                        details={
                            "Distance": f"~{net.location.estimated_distance_m:.1f}m",
                            "Device": net.device_category.value.replace('_', ' ').title()
                        }
                    )
                    self.add_event(event)
                    reported_bssids.add(net.bssid)
        
        # ═══════════════════════════════════════════════════════════════════
        # MOVING DEVICE DETECTION
        # ═══════════════════════════════════════════════════════════════════
        for net in networks:
            if net.bssid in reported_bssids:
                continue
            if net.temporal.movement_state.value == 'fast_moving':
                existing = [e for e in self.events[:30]
                           if e.network_bssid == net.bssid and "Moving" in e.title]
                if not existing:
                    event = IntelEvent(
                        event_type=EventType.ANOMALY,
                        title=f"Fast Moving: {net.ssid or '[Hidden]'}",
                        message=f"Device appears to be moving rapidly",
                        network_bssid=net.bssid,
                        network_ssid=net.ssid,
                        severity=2,
                        details={
                            "Movement": net.temporal.movement_state.value,
                            "Device": net.device_category.value.replace('_', ' ').title()
                        }
                    )
                    self.add_event(event)
                    reported_bssids.add(net.bssid)
        
        # ═══════════════════════════════════════════════════════════════════
        # HIDDEN NETWORK WITH HIGH SIGNAL
        # ═══════════════════════════════════════════════════════════════════
        for net in networks:
            if net.bssid in reported_bssids:
                continue
            if net.security.is_hidden and net.signal_percent >= 60:
                existing = [e for e in self.events[:50]
                           if e.network_bssid == net.bssid and "Hidden" in e.title and "Strong" in e.title]
                if not existing:
                    # Build detailed info
                    details = {
                        "Channel": f"Ch.{net.channel} ({net.band})",
                        "Distance": f"~{net.location.estimated_distance_m:.1f}m ({net.location.wall_description})",
                        "Signal": f"{net.signal_percent}% ({net.signal_percent - 100}dBm)"
                    }
                    
                    # Add vendor with smart icons
                    if net.vendor and net.vendor != "Unknown":
                        vendor_display = net.vendor
                        if "ring" in net.vendor.lower():
                            vendor_display = f"🚪 {net.vendor}"
                        elif "amazon" in net.vendor.lower() or "sidewalk" in net.vendor.lower():
                            vendor_display = f"🌐 {net.vendor}"
                        elif "camera" in net.vendor.lower() or "blink" in net.vendor.lower():
                            vendor_display = f"📹 {net.vendor}"
                        details["Vendor"] = vendor_display
                    
                    # Add device classification
                    device_type = net.device_category.value.replace('_', ' ').title()
                    details["Device Class"] = device_type
                    
                    # Add security if available
                    if hasattr(net.security, 'security_rating'):
                        details["Security"] = net.security.security_rating.value
                    
                    # Add stability
                    if hasattr(net.temporal, 'stability_rating'):
                        details["Stability"] = f"{net.temporal.stability_rating} ({net.temporal.stability_score:.0f}%)"
                    
                    event = IntelEvent(
                        event_type=EventType.INSIGHT,
                        title=f"Strong Hidden Network",
                        message=f"Hidden network at {net.signal_percent}% signal - investigate",
                        network_bssid=net.bssid,
                        severity=2,
                        details=details
                    )
                    self.add_event(event)
                    reported_bssids.add(net.bssid)
    
    def destroy(self):
        """Clean up dashboard resources."""
        if self.animation_id:
            self.parent.after_cancel(self.animation_id)
