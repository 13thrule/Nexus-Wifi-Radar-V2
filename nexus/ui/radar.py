"""
Radar-style WiFi network visualization.

Provides a RadarView class for displaying networks in a radar-style canvas.
"""

import math
import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable
from datetime import datetime

from nexus.core.models import Network, ScanResult


class RadarView:
    """
    Radar-style visualization of WiFi networks.
    
    Displays networks as blips on a radar screen with:
    - Distance from center based on signal strength
    - Color coding by signal quality
    - Labels showing SSID and signal percentage
    """
    
    # Color scheme
    COLORS = {
        "background": "#1a1a1a",
        "grid": "#333333",
        "sweep": "#00ff00",
        "excellent": "#00ff00",
        "good": "#ffff00",
        "fair": "#ff9900",
        "weak": "#ff6b6b",
        "text": "#ffffff",
        "label_bg": "#000000",
    }
    
    def __init__(self, parent: tk.Widget, max_networks: int = 12):
        """
        Initialize RadarView.
        
        Args:
            parent: Parent Tkinter widget
            max_networks: Maximum number of networks to display
        """
        self.parent = parent
        self.max_networks = max_networks
        self.networks: List[Network] = []
        self.sweep_angle = 0
        self.animate_sweep = True
        
        # Create canvas
        self.canvas = tk.Canvas(
            parent,
            bg=self.COLORS["background"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bind resize event
        self.canvas.bind("<Configure>", self._on_resize)
        
        # Start sweep animation
        self._animate()
    
    def update_networks(self, networks: List[Network]) -> None:
        """
        Update the displayed networks.
        
        Args:
            networks: List of Network objects to display
        """
        # Sort by signal strength and take top N
        self.networks = sorted(
            networks,
            key=lambda n: n.rssi_dbm,
            reverse=True
        )[:self.max_networks]
        
        self._draw()
    
    def update_from_scan(self, result: ScanResult) -> None:
        """
        Update from a ScanResult.
        
        Args:
            result: ScanResult containing networks
        """
        self.update_networks(result.networks)
    
    def set_animate(self, enabled: bool) -> None:
        """Enable or disable sweep animation."""
        self.animate_sweep = enabled
    
    def _on_resize(self, event) -> None:
        """Handle canvas resize."""
        self._draw()
    
    def _animate(self) -> None:
        """Animate the radar sweep."""
        if self.animate_sweep:
            self.sweep_angle = (self.sweep_angle + 3) % 360
            self._draw()
        
        self.canvas.after(50, self._animate)
    
    def _draw(self) -> None:
        """Draw the radar display."""
        self.canvas.delete("all")
        
        # Get canvas dimensions
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        # Calculate center and radius
        cx = w // 2
        cy = h // 2
        radius = min(w, h) // 2 - 50
        
        if radius < 20:
            return
        
        # Draw grid circles
        self._draw_grid(cx, cy, radius)
        
        # Draw sweep line
        if self.animate_sweep:
            self._draw_sweep(cx, cy, radius)
        
        # Draw networks
        self._draw_networks(cx, cy, radius)
        
        # Draw legend
        self._draw_legend(w, h)
    
    def _draw_grid(self, cx: int, cy: int, radius: int) -> None:
        """Draw the radar grid circles."""
        # Concentric circles at 25%, 50%, 75%, 100%
        for pct in [25, 50, 75, 100]:
            r = int(radius * pct / 100)
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=self.COLORS["grid"],
                width=1
            )
            
            # Label the ring
            if pct < 100:
                label = f"{100 - pct}%"
                self.canvas.create_text(
                    cx + r + 5, cy,
                    text=label,
                    fill=self.COLORS["grid"],
                    font=("Arial", 8),
                    anchor="w"
                )
        
        # Cross hairs
        self.canvas.create_line(
            cx - radius, cy, cx + radius, cy,
            fill=self.COLORS["grid"], width=1
        )
        self.canvas.create_line(
            cx, cy - radius, cx, cy + radius,
            fill=self.COLORS["grid"], width=1
        )
    
    def _draw_sweep(self, cx: int, cy: int, radius: int) -> None:
        """Draw the animated sweep line."""
        angle_rad = math.radians(self.sweep_angle - 90)
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)
        
        self.canvas.create_line(
            cx, cy, x, y,
            fill=self.COLORS["sweep"],
            width=2
        )
        
        # Fade trail
        for i in range(1, 4):
            trail_angle = math.radians(self.sweep_angle - 90 - i * 5)
            tx = cx + radius * math.cos(trail_angle)
            ty = cy + radius * math.sin(trail_angle)
            
            # Calculate faded color
            intensity = int(255 * (1 - i * 0.25))
            color = f"#{intensity:02x}ff{intensity:02x}"
            
            self.canvas.create_line(
                cx, cy, tx, ty,
                fill=color,
                width=1
            )
    
    def _draw_networks(self, cx: int, cy: int, radius: int) -> None:
        """Draw network blips on the radar."""
        if not self.networks:
            return
        
        # Distribute networks evenly around the radar
        angle_step = 360 / max(len(self.networks), 1)
        
        for i, network in enumerate(self.networks):
            # Calculate position
            # Signal strength determines distance from center
            # 100% signal = center, 0% signal = edge
            signal_pct = network.signal_percent
            distance = radius * (1 - signal_pct / 100)
            
            # Angle based on index
            angle_deg = i * angle_step - 90  # Start from top
            angle_rad = math.radians(angle_deg)
            
            x = cx + distance * math.cos(angle_rad)
            y = cy + distance * math.sin(angle_rad)
            
            # Determine color based on signal strength
            color = self._get_signal_color(signal_pct)
            
            # Draw blip
            blip_size = 8
            self.canvas.create_oval(
                x - blip_size, y - blip_size,
                x + blip_size, y + blip_size,
                fill=color,
                outline="white",
                width=2
            )
            
            # Draw label
            label_text = f"{network.ssid[:15] if network.ssid else '<Hidden>'}\n{signal_pct}%"
            
            # Offset label based on position
            label_x = x + 15 if x >= cx else x - 15
            anchor = "w" if x >= cx else "e"
            
            self.canvas.create_text(
                label_x, y,
                text=label_text,
                fill=color,
                font=("Arial", 8),
                anchor=anchor
            )
    
    def _draw_legend(self, w: int, h: int) -> None:
        """Draw the signal strength legend."""
        legend_x = 10
        legend_y = h - 80
        
        items = [
            ("Excellent", self.COLORS["excellent"], "80-100%"),
            ("Good", self.COLORS["good"], "60-79%"),
            ("Fair", self.COLORS["fair"], "40-59%"),
            ("Weak", self.COLORS["weak"], "0-39%"),
        ]
        
        for i, (label, color, range_text) in enumerate(items):
            y = legend_y + i * 18
            
            # Color box
            self.canvas.create_rectangle(
                legend_x, y, legend_x + 12, y + 12,
                fill=color, outline="white"
            )
            
            # Label
            self.canvas.create_text(
                legend_x + 18, y + 6,
                text=f"{label} ({range_text})",
                fill=self.COLORS["text"],
                font=("Arial", 8),
                anchor="w"
            )
    
    def _get_signal_color(self, signal_pct: int) -> str:
        """Get color based on signal percentage."""
        if signal_pct >= 80:
            return self.COLORS["excellent"]
        elif signal_pct >= 60:
            return self.COLORS["good"]
        elif signal_pct >= 40:
            return self.COLORS["fair"]
        else:
            return self.COLORS["weak"]


class RadarWindow:
    """
    Standalone radar window for testing.
    
    Creates a complete Tkinter window with RadarView.
    """
    
    def __init__(self):
        """Initialize radar window."""
        self.root = tk.Tk()
        self.root.title("Nexus WiFi Radar")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")
        
        # Header
        header = tk.Frame(self.root, bg="#0066cc", height=50)
        header.pack(fill="x")
        tk.Label(
            header,
            text="📡 Nexus WiFi Radar",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#0066cc"
        ).pack(pady=10)
        
        # Radar view
        self.radar = RadarView(self.root)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Arial", 10)
        )
        status.pack(side="bottom", fill="x", padx=10, pady=5)
    
    def update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_var.set(message)
    
    def run(self) -> None:
        """Run the main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    # Demo with sample data
    window = RadarWindow()
    
    # Create sample networks for testing
    sample_networks = [
        Network("HomeNetwork", "AA:BB:CC:DD:EE:01", 6, 2437, -45, vendor="Netgear"),
        Network("Office_5G", "AA:BB:CC:DD:EE:02", 36, 5180, -55, vendor="Cisco"),
        Network("Guest", "AA:BB:CC:DD:EE:03", 11, 2462, -65, vendor="TP-Link"),
        Network("Neighbor_2G", "AA:BB:CC:DD:EE:04", 1, 2412, -75, vendor="Asus"),
        Network("IoT_Network", "AA:BB:CC:DD:EE:05", 6, 2437, -80, vendor="Amazon"),
    ]
    
    window.radar.update_networks(sample_networks)
    window.update_status(f"Displaying {len(sample_networks)} networks")
    window.run()
