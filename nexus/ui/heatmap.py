"""
WiFi signal heatmap visualization.

Provides heatmap rendering for signal strength over a spatial grid.
"""

import tkinter as tk
from typing import List, Tuple, Optional, Dict
import math

from nexus.core.models import Network


class HeatmapRenderer:
    """
    Renders WiFi signal strength as a heatmap.
    
    Creates a color-coded visualization of signal strength
    over a 2D grid representing physical space.
    """
    
    # Color gradient from weak (red) to strong (green)
    GRADIENT = [
        (255, 0, 0),      # -90 dBm (weak)
        (255, 128, 0),    # -80 dBm
        (255, 255, 0),    # -70 dBm
        (128, 255, 0),    # -60 dBm
        (0, 255, 0),      # -50 dBm
        (0, 255, 128),    # -40 dBm
        (0, 255, 255),    # -30 dBm (excellent)
    ]
    
    def __init__(self, parent: tk.Widget, grid_size: int = 20):
        """
        Initialize heatmap renderer.
        
        Args:
            parent: Parent Tkinter widget
            grid_size: Size of each grid cell in pixels
        """
        self.parent = parent
        self.grid_size = grid_size
        
        # Signal data: (x, y) -> rssi_dbm
        self.signal_data: Dict[Tuple[int, int], int] = {}
        
        # Room dimensions (in grid units)
        self.room_width = 20
        self.room_height = 15
        
        # Create canvas
        self.canvas = tk.Canvas(
            parent,
            bg="#1a1a1a",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bind resize
        self.canvas.bind("<Configure>", self._on_resize)
    
    def set_room_size(self, width: int, height: int) -> None:
        """
        Set room dimensions in grid units.
        
        Args:
            width: Room width in grid units
            height: Room height in grid units
        """
        self.room_width = width
        self.room_height = height
        self._draw()
    
    def add_measurement(self, x: int, y: int, rssi_dbm: int) -> None:
        """
        Add a signal strength measurement at a position.
        
        Args:
            x: X coordinate in grid units
            y: Y coordinate in grid units
            rssi_dbm: Signal strength in dBm
        """
        self.signal_data[(x, y)] = rssi_dbm
        self._draw()
    
    def add_network_at_position(self, network: Network, x: int, y: int) -> None:
        """
        Add network measurement at position.
        
        Args:
            network: Network object with signal data
            x: X coordinate
            y: Y coordinate
        """
        self.add_measurement(x, y, network.rssi_dbm)
    
    def clear(self) -> None:
        """Clear all measurements."""
        self.signal_data.clear()
        self._draw()
    
    def _on_resize(self, event) -> None:
        """Handle canvas resize."""
        self._draw()
    
    def _draw(self) -> None:
        """Draw the heatmap."""
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        # Calculate cell size to fit room in canvas
        cell_w = w // self.room_width
        cell_h = h // self.room_height
        cell_size = min(cell_w, cell_h)
        
        # Calculate offset to center the grid
        offset_x = (w - cell_size * self.room_width) // 2
        offset_y = (h - cell_size * self.room_height) // 2
        
        # Draw interpolated heatmap
        if self.signal_data:
            self._draw_heatmap(offset_x, offset_y, cell_size)
        
        # Draw grid
        self._draw_grid(offset_x, offset_y, cell_size)
        
        # Draw measurement points
        self._draw_points(offset_x, offset_y, cell_size)
        
        # Draw legend
        self._draw_legend(w, h)
    
    def _draw_grid(self, offset_x: int, offset_y: int, cell_size: int) -> None:
        """Draw the background grid."""
        for x in range(self.room_width + 1):
            x_pos = offset_x + x * cell_size
            self.canvas.create_line(
                x_pos, offset_y,
                x_pos, offset_y + self.room_height * cell_size,
                fill="#333333", width=1
            )
        
        for y in range(self.room_height + 1):
            y_pos = offset_y + y * cell_size
            self.canvas.create_line(
                offset_x, y_pos,
                offset_x + self.room_width * cell_size, y_pos,
                fill="#333333", width=1
            )
    
    def _draw_heatmap(self, offset_x: int, offset_y: int, cell_size: int) -> None:
        """Draw the interpolated heatmap."""
        if not self.signal_data:
            return
        
        # Simple inverse distance weighting interpolation
        for gx in range(self.room_width):
            for gy in range(self.room_height):
                rssi = self._interpolate(gx, gy)
                if rssi is not None:
                    color = self._rssi_to_color(rssi)
                    
                    x1 = offset_x + gx * cell_size
                    y1 = offset_y + gy * cell_size
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=color, outline=""
                    )
    
    def _interpolate(self, x: int, y: int) -> Optional[int]:
        """
        Interpolate signal strength at a grid position.
        
        Uses inverse distance weighting (IDW).
        """
        if not self.signal_data:
            return None
        
        # Check if we have an exact measurement
        if (x, y) in self.signal_data:
            return self.signal_data[(x, y)]
        
        # IDW interpolation
        weighted_sum = 0.0
        weight_total = 0.0
        
        for (mx, my), rssi in self.signal_data.items():
            distance = math.sqrt((x - mx) ** 2 + (y - my) ** 2)
            if distance < 0.1:
                return rssi
            
            weight = 1.0 / (distance ** 2)
            weighted_sum += rssi * weight
            weight_total += weight
        
        if weight_total > 0:
            return int(weighted_sum / weight_total)
        
        return None
    
    def _draw_points(self, offset_x: int, offset_y: int, cell_size: int) -> None:
        """Draw measurement points."""
        for (x, y), rssi in self.signal_data.items():
            cx = offset_x + x * cell_size + cell_size // 2
            cy = offset_y + y * cell_size + cell_size // 2
            
            # Draw marker
            r = 6
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill="white", outline="black", width=2
            )
            
            # Draw value
            self.canvas.create_text(
                cx, cy + 15,
                text=f"{rssi}",
                fill="white",
                font=("Arial", 8)
            )
    
    def _draw_legend(self, w: int, h: int) -> None:
        """Draw the color legend."""
        legend_x = w - 100
        legend_y = 20
        legend_w = 20
        legend_h = 150
        
        # Draw gradient bar
        steps = len(self.GRADIENT)
        step_h = legend_h // steps
        
        for i, color in enumerate(reversed(self.GRADIENT)):
            y = legend_y + i * step_h
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            self.canvas.create_rectangle(
                legend_x, y, legend_x + legend_w, y + step_h,
                fill=hex_color, outline=""
            )
        
        # Labels
        self.canvas.create_text(
            legend_x + legend_w + 5, legend_y,
            text="-30 dBm", fill="white", font=("Arial", 8), anchor="w"
        )
        self.canvas.create_text(
            legend_x + legend_w + 5, legend_y + legend_h,
            text="-90 dBm", fill="white", font=("Arial", 8), anchor="w"
        )
        self.canvas.create_text(
            legend_x + legend_w // 2, legend_y - 10,
            text="Signal", fill="white", font=("Arial", 9, "bold")
        )
    
    def _rssi_to_color(self, rssi: int) -> str:
        """Convert RSSI to hex color."""
        # Clamp RSSI to -90 to -30 range
        rssi = max(-90, min(-30, rssi))
        
        # Normalize to 0-1
        normalized = (rssi + 90) / 60
        
        # Map to gradient
        idx = normalized * (len(self.GRADIENT) - 1)
        lower = int(idx)
        upper = min(lower + 1, len(self.GRADIENT) - 1)
        frac = idx - lower
        
        # Interpolate colors
        r = int(self.GRADIENT[lower][0] * (1 - frac) + self.GRADIENT[upper][0] * frac)
        g = int(self.GRADIENT[lower][1] * (1 - frac) + self.GRADIENT[upper][1] * frac)
        b = int(self.GRADIENT[lower][2] * (1 - frac) + self.GRADIENT[upper][2] * frac)
        
        return f"#{r:02x}{g:02x}{b:02x}"


class HeatmapWindow:
    """Standalone heatmap window for testing."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WiFi Signal Heatmap")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")
        
        # Header
        header = tk.Frame(self.root, bg="#0066cc", height=50)
        header.pack(fill="x")
        tk.Label(
            header,
            text="📊 WiFi Signal Heatmap",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#0066cc"
        ).pack(pady=10)
        
        # Heatmap
        self.heatmap = HeatmapRenderer(self.root)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # Demo
    window = HeatmapWindow()
    
    # Add sample measurements
    window.heatmap.add_measurement(5, 5, -40)
    window.heatmap.add_measurement(10, 5, -55)
    window.heatmap.add_measurement(15, 5, -70)
    window.heatmap.add_measurement(10, 10, -50)
    window.heatmap.add_measurement(5, 10, -60)
    
    window.run()
