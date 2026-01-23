"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   VAULT-TEC PASSIVE INTELLIGENCE MODULE v3.0                                 ║
║   "A secure vault is a happy vault!"                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

NEXUS WiFi Radar - Pip-Boy 3000 Mk IV Skin
==========================================
A complete retro-futuristic transformation inspired by Fallout's Pip-Boy.

Features:
- CRT curvature and scanline effects
- Phosphor glow animations
- Chunky physical device framing
- Inset beveled panels
- Retro terminal typography
- Vault-Tec flavor text
- 100% tkinter, 100% offline
"""

import tkinter as tk
from tkinter import ttk
import math
import random
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field


# =============================================================================
# SECTION 1: COLOR PALETTE - Vault-Tec Approved Colors
# =============================================================================

class PipBoyPalette:
    """Official Vault-Tec color specifications for Pip-Boy displays."""
    
    # Primary phosphor greens
    GREEN_BRIGHT = "#39FF14"         # Peak phosphor excitation
    GREEN_PRIMARY = "#20C20E"        # Standard text/elements
    GREEN_MEDIUM = "#14991E"         # Medium brightness
    GREEN_DIM = "#0D6B0D"            # Dimmed/inactive elements
    GREEN_DARK = "#0A4A0A"           # Very dim, background accents
    GREEN_DARKER = "#063D12"         # Darkest green
    PHOSPHOR_GLOW = "#14FF00"        # Bloom/glow effect color
    
    # Background layers (simulated CRT depth)
    BG_BLACK = "#0A0A08"             # Deep CRT black
    BG_DARK = "#0D120D"              # Panel backgrounds
    BG_PANEL = "#111611"             # Raised surface
    BG_CARD = "#151915"              # Card background
    BEZEL_DARK = "#1A1A18"           # Device bezel dark
    BEZEL_LIGHT = "#2A2A26"          # Device bezel highlight
    BEZEL_EDGE = "#3A3A34"           # Bezel edge highlight
    
    # Accent colors (status indicators)
    AMBER_BRIGHT = "#FFB000"         # Warning indicators
    AMBER_PRIMARY = "#CC8800"        # Standard amber
    AMBER_DIM = "#996600"            # Dimmed warning
    RED_ALERT = "#FF3333"            # Critical alerts
    RED_DIM = "#991F1F"              # Dimmed alert
    BLUE_INFO = "#33CCFF"            # Information (rare)
    
    # UI element colors
    SCANLINE = "#000000"             # Scanline overlay (with alpha sim)
    INSET_SHADOW = "#050505"         # Panel inset shadow
    INSET_HIGHLIGHT = "#1A2A1A"      # Panel inset highlight


# Alias for internal use
class VaultTecColors:
    """Alias for PipBoyPalette for internal consistency."""
    PHOSPHOR_BRIGHT = PipBoyPalette.GREEN_BRIGHT
    PHOSPHOR_MAIN = PipBoyPalette.GREEN_PRIMARY
    PHOSPHOR_DIM = PipBoyPalette.GREEN_DIM
    PHOSPHOR_DARK = PipBoyPalette.GREEN_DARK
    PHOSPHOR_GLOW = PipBoyPalette.PHOSPHOR_GLOW
    CRT_BLACK = PipBoyPalette.BG_BLACK
    CRT_DARK = PipBoyPalette.BG_DARK
    CRT_SURFACE = PipBoyPalette.BG_PANEL
    BEZEL_DARK = PipBoyPalette.BEZEL_DARK
    BEZEL_LIGHT = PipBoyPalette.BEZEL_LIGHT
    BEZEL_EDGE = PipBoyPalette.BEZEL_EDGE
    AMBER_WARN = PipBoyPalette.AMBER_BRIGHT
    AMBER_DIM = PipBoyPalette.AMBER_DIM
    RED_ALERT = PipBoyPalette.RED_ALERT
    RED_DIM = PipBoyPalette.RED_DIM
    BLUE_INFO = PipBoyPalette.BLUE_INFO
    SCANLINE = PipBoyPalette.SCANLINE
    INSET_SHADOW = PipBoyPalette.INSET_SHADOW
    INSET_HIGHLIGHT = PipBoyPalette.INSET_HIGHLIGHT
    TEXT_TITLE = PipBoyPalette.GREEN_BRIGHT
    TEXT_PRIMARY = PipBoyPalette.GREEN_PRIMARY
    TEXT_SECONDARY = PipBoyPalette.GREEN_MEDIUM
    TEXT_DISABLED = PipBoyPalette.GREEN_DIM
    TEXT_FLAVOR = PipBoyPalette.GREEN_DARK


# Convenience alias - PIPBOY_THEME for app.py compatibility
PIPBOY_THEME = {
    # Required keys for app.py theme system
    "name": "📟 PIP-BOY 3000",
    "bg_main": PipBoyPalette.BG_BLACK,
    "bg_panel": PipBoyPalette.BG_PANEL,
    "text_primary": PipBoyPalette.GREEN_PRIMARY,
    "text_secondary": PipBoyPalette.GREEN_DIM,
    "text_accent": PipBoyPalette.GREEN_BRIGHT,
    "button_primary": PipBoyPalette.GREEN_PRIMARY,
    "button_secondary": PipBoyPalette.GREEN_DIM,
    "button_accent": PipBoyPalette.GREEN_BRIGHT,
    "border_color": PipBoyPalette.GREEN_PRIMARY,
    "radar_bg": PipBoyPalette.BG_BLACK,
    "grid_color": PipBoyPalette.GREEN_DARK,
    # Extended Pip-Boy colors
    "phosphor_bright": PipBoyPalette.GREEN_BRIGHT,
    "phosphor_main": PipBoyPalette.GREEN_PRIMARY,
    "phosphor_dim": PipBoyPalette.GREEN_DIM,
    "phosphor_glow": PipBoyPalette.PHOSPHOR_GLOW,
    "crt_black": PipBoyPalette.BG_BLACK,
    "crt_dark": PipBoyPalette.BG_DARK,
    "bezel_dark": PipBoyPalette.BEZEL_DARK,
    "bezel_light": PipBoyPalette.BEZEL_LIGHT,
    "amber_warn": PipBoyPalette.AMBER_BRIGHT,
    "red_alert": PipBoyPalette.RED_ALERT,
    # CRT effect settings
    "crt_enabled": True,
    "scanlines": True,
    "flicker": True,
    "glow": True,
}


# =============================================================================
# SECTION 2: TYPOGRAPHY - Terminal Fonts
# =============================================================================

class PipBoyFonts:
    """Monospaced terminal font configurations."""
    
    # Font family fallback chains
    TERMINAL_FONTS = [
        "Consolas",
        "Lucida Console", 
        "Courier New",
        "Courier",
        "monospace"
    ]
    
    HEADER_FONTS = [
        "Consolas",
        "Lucida Console",
        "Courier New",
        "Courier",
        "monospace"
    ]
    
    # Alias for backwards compatibility
    MONO_FAMILIES = TERMINAL_FONTS
    
    # Font sizes
    SIZE_TITLE = 16
    SIZE_HEADER = 14
    SIZE_BODY = 11
    SIZE_SMALL = 9
    SIZE_TINY = 8
    
    @classmethod
    def get_family(cls) -> str:
        """Get the first available monospace font."""
        return cls.TERMINAL_FONTS[0]
    
    @classmethod
    def get_terminal_font(cls, size: int = 11) -> tuple:
        """Get terminal font tuple with specified size."""
        return (cls.TERMINAL_FONTS[0], size)
    
    @classmethod
    def get_header_font(cls, size: int = 14) -> tuple:
        """Get header font tuple with specified size."""
        return (cls.HEADER_FONTS[0], size, "bold")
    
    @classmethod
    def title(cls) -> tuple:
        """Title font tuple."""
        return (cls.get_family(), cls.SIZE_TITLE, "bold")
    
    @classmethod
    def header(cls) -> tuple:
        """Header font tuple."""
        return (cls.get_family(), cls.SIZE_HEADER, "bold")
    
    @classmethod
    def body(cls) -> tuple:
        """Body text font tuple."""
        return (cls.get_family(), cls.SIZE_BODY)
    
    @classmethod
    def small(cls) -> tuple:
        """Small text font tuple."""
        return (cls.get_family(), cls.SIZE_SMALL)
    
    @classmethod
    def tiny(cls) -> tuple:
        """Tiny text font tuple."""
        return (cls.get_family(), cls.SIZE_TINY)


# =============================================================================
# SECTION 3: VAULT-TEC FLAVOR TEXT
# =============================================================================

class VaultTecText:
    """Authentic Vault-Tec style flavor text and messages."""
    
    # Boot sequence messages
    BOOT_SEQUENCE = [
        "ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL",
        "NEXUS WIFI RADAR v2.77.14",
        "COPYRIGHT 2077 ROBCO INDUSTRIES",
        "-SERVER 6-",
        "",
        "INITIALIZING PASSIVE INTELLIGENCE CORE...",
        "CALIBRATING RF SENSORS...",
        "LOADING THREAT DETECTION MATRICES...",
        "VAULT-TEC SECURITY PROTOCOLS: ACTIVE",
        "",
        "*** NEXUS RADAR ONLINE ***",
    ]
    
    # Status bar messages (rotating)
    STATUS_MESSAGES = [
        "SCANNING LOCAL AIRSPACE...",
        "VAULT-TEC RECOMMENDS REGULAR SCANS",
        "MONITORING {count} SIGNALS",
        "RF ENVIRONMENT: NOMINAL",
        "PASSIVE SCAN MODE ACTIVE",
        "NO HOSTILE SIGNALS DETECTED",
        "REMEMBER: STAY VIGILANT!",
        "VAULT-TEC: PREPARING FOR THE FUTURE",
        "SIGNAL ANALYSIS IN PROGRESS...",
        "ELECTROMAGNETIC SWEEP ACTIVE",
    ]
    
    # Tab headers with Vault-Tec flair
    TAB_HEADERS = {
        "radar": ">> TACTICAL RADAR DISPLAY <<",
        "networks": ">> DETECTED TRANSMISSIONS <<",
        "heatmap": ">> SIGNAL DENSITY ANALYSIS <<",
        "world": ">> UNIFIED WORLD MODEL <<",
        "threat": ">> THREAT ASSESSMENT <<",
        "hidden": ">> CLASSIFIED SIGNALS <<",
        "security": ">> SECURITY ANALYSIS <<",
        "vendor": ">> DEVICE IDENTIFICATION <<",
        "stability": ">> SIGNAL STABILITY <<",
        "log": ">> SYSTEM TERMINAL <<",
    }
    
    # Panel titles
    PANEL_TITLES = {
        "networks": "[ DETECTED NETWORKS ]",
        "details": "[ SIGNAL DETAILS ]",
        "threats": "[ THREAT MATRIX ]",
        "stats": "[ STATISTICS ]",
        "actions": "[ ACTIONS ]",
    }
    
    # Threat level descriptions
    THREAT_LEVELS = {
        "critical": "!!! CRITICAL THREAT DETECTED !!!",
        "high": "** HIGH RISK SIGNAL **",
        "medium": "* MODERATE CONCERN *",
        "low": "MINIMAL RISK",
        "none": "SIGNAL CLEAR",
    }
    
    # Random flavor for empty states
    EMPTY_STATES = [
        "NO SIGNALS IN RANGE",
        "AIRSPACE CLEAR",
        "AWAITING TRANSMISSION DATA...",
        "SCANNING...",
    ]
    
    @classmethod
    def get_random_status(cls, count: int = 0) -> str:
        """Get a random status message."""
        msg = random.choice(cls.STATUS_MESSAGES)
        return msg.format(count=count)


# =============================================================================
# SECTION 4: ASCII ART DECORATIONS
# =============================================================================

class PipBoyDecorations:
    """ASCII art and decorative elements for Pip-Boy UI."""
    
    # Vault-Tec header
    VAULT_TEC_HEADER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║   VAULT-TEC INDUSTRIES - NEXUS WIFI RADAR                                    ║
║   "Preparing for the future!"                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    # Box drawing characters
    BOX_H = "═"
    BOX_V = "║"
    BOX_TL = "╔"
    BOX_TR = "╗"
    BOX_BL = "╚"
    BOX_BR = "╝"
    BOX_LT = "╠"
    BOX_RT = "╣"
    BOX_TT = "╦"
    BOX_BT = "╩"
    BOX_X = "╬"
    
    # Progress bar characters
    PROG_FULL = "█"
    PROG_EMPTY = "░"
    PROG_HALF = "▓"
    
    # Signal strength bars
    SIGNAL_BARS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    
    # Status indicators
    INDICATOR_ON = "●"
    INDICATOR_OFF = "○"
    INDICATOR_WARN = "◐"
    
    @classmethod
    def make_header(cls, text: str, width: int = 40) -> str:
        """Create a styled header with text."""
        padding = width - len(text) - 4
        left_pad = padding // 2
        right_pad = padding - left_pad
        return f"{cls.BOX_TL}{cls.BOX_H * left_pad} {text} {cls.BOX_H * right_pad}{cls.BOX_TR}"
    
    @classmethod
    def make_progress_bar(cls, progress: float, width: int = 20) -> str:
        """Create a progress bar string (0.0 to 1.0)."""
        progress = max(0.0, min(1.0, progress))
        filled = int(progress * width)
        empty = width - filled
        return f"[{cls.PROG_FULL * filled}{cls.PROG_EMPTY * empty}]"
    
    @classmethod
    def make_status_line(cls, label: str, value: str, status: str = "ok") -> str:
        """Create a status line with indicator."""
        if status == "ok":
            indicator = cls.INDICATOR_ON
        elif status == "warn":
            indicator = cls.INDICATOR_WARN
        else:
            indicator = cls.INDICATOR_OFF
        return f"{indicator} {label}: {value}"
    
    @classmethod
    def signal_bar(cls, strength: int) -> str:
        """Get signal strength bar (0-100)."""
        if strength <= 0:
            return "▁"
        idx = min(int(strength / 100 * len(cls.SIGNAL_BARS)), len(cls.SIGNAL_BARS) - 1)
        return cls.SIGNAL_BARS[idx]
    
    @classmethod
    def make_box(cls, width: int, height: int) -> List[str]:
        """Generate a box frame."""
        lines = []
        lines.append(cls.CORNER_TL + cls.HORIZONTAL * (width - 2) + cls.CORNER_TR)
        for _ in range(height - 2):
            lines.append(cls.VERTICAL + " " * (width - 2) + cls.VERTICAL)
        lines.append(cls.CORNER_BL + cls.HORIZONTAL * (width - 2) + cls.CORNER_BR)
        return lines


# =============================================================================
# SECTION 4B: HEATMAP COLORS
# =============================================================================

class PipBoyHeatmapColors:
    """Pip-Boy styled heatmap color generator."""
    
    # Gradient from dark green to bright green to amber
    GRADIENT = [
        "#0A4A0A",  # 0.0 - very dark
        "#0D6B0D",  # 0.1
        "#109010",  # 0.2
        "#14B514",  # 0.3
        "#18DA18",  # 0.4
        "#20C20E",  # 0.5 - primary green
        "#39FF14",  # 0.6 - bright green
        "#66FF33",  # 0.7
        "#99FF00",  # 0.8
        "#CCCC00",  # 0.9
        "#FFB000",  # 1.0 - amber
    ]
    
    @classmethod
    def get_color_for_intensity(cls, intensity: float) -> str:
        """Get color for intensity value (0.0 to 1.0)."""
        intensity = max(0.0, min(1.0, intensity))
        idx = int(intensity * (len(cls.GRADIENT) - 1))
        return cls.GRADIENT[idx]


# =============================================================================
# SECTION 4C: ANIMATION STATE
# =============================================================================

@dataclass
class AnimationState:
    """State container for CRT animations."""
    scanline_offset: float = 0.0
    glow_phase: float = 0.0
    flicker_phase: float = 0.0
    radar_sweep_angle: float = 0.0
    pulse_phase: float = 0.0
    typing_position: int = 0
    frame_count: int = 0


# =============================================================================
# SECTION 5: CRT EFFECTS SYSTEM
# =============================================================================

class ScanlineOverlay(tk.Canvas):
    """Creates CRT scanline effect overlay as a Canvas widget."""
    
    def __init__(self, parent, spacing: int = 3, opacity: float = 0.15, **kwargs):
        # Set default canvas options
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bg", "")
        
        super().__init__(parent, **kwargs)
        
        self._parent_canvas = parent if isinstance(parent, tk.Canvas) else None
        self.spacing = spacing
        self.opacity = opacity
        self._scanline_ids: List[int] = []
        self._enabled = True
        
        # Bind to configure event for resizing
        self.bind("<Configure>", self._on_configure)
    
    def _on_configure(self, event=None):
        """Redraw on resize."""
        if self._enabled:
            self.draw_scanlines()
        
    def draw_scanlines(self):
        """Draw scanlines across the canvas."""
        if not self._enabled:
            return
            
        self.clear()
        height = self.winfo_height()
        width = self.winfo_width()
        
        if height <= 1 or width <= 1:
            return
        
        # Scanline color (simulated transparency via dark color)
        scanline_color = "#050805"
        
        for y in range(0, height, self.spacing):
            line_id = self.create_line(
                0, y, width, y,
                fill=scanline_color,
                tags="scanline"
            )
            self._scanline_ids.append(line_id)
    
    # Legacy method alias
    def draw(self):
        """Legacy method - calls draw_scanlines."""
        self.draw_scanlines()
    
    def clear(self):
        """Remove all scanlines."""
        self.delete("scanline")
        self._scanline_ids.clear()
    
    def enable(self, enabled: bool = True):
        """Enable or disable scanlines."""
        self._enabled = enabled
        if not enabled:
            self.clear()
        else:
            self.draw_scanlines()


class CRTCurvature:
    """Simulates CRT screen curvature with border vignette effect."""
    
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.vignette_items: List[int] = []
        self._enabled = True
    
    def draw(self):
        """Draw curved edge vignette effect."""
        if not self._enabled:
            return
            
        self.clear()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Create gradient vignette at edges using rectangles
        # This simulates the curved CRT edge darkening
        edge_colors = [
            "#0A0A08", "#0B0B09", "#0C0C0A", "#0D0D0B",
            "#0E0E0C", "#0F0F0D", "#10100E"
        ]
        
        for i, color in enumerate(edge_colors):
            thickness = 8 - i
            # Top edge
            self.vignette_items.append(
                self.canvas.create_rectangle(
                    0, i * 2, width, i * 2 + thickness,
                    fill=color, outline="", tags="vignette"
                )
            )
            # Bottom edge
            self.vignette_items.append(
                self.canvas.create_rectangle(
                    0, height - i * 2 - thickness, width, height - i * 2,
                    fill=color, outline="", tags="vignette"
                )
            )
            # Left edge
            self.vignette_items.append(
                self.canvas.create_rectangle(
                    i * 2, 0, i * 2 + thickness, height,
                    fill=color, outline="", tags="vignette"
                )
            )
            # Right edge
            self.vignette_items.append(
                self.canvas.create_rectangle(
                    width - i * 2 - thickness, 0, width - i * 2, height,
                    fill=color, outline="", tags="vignette"
                )
            )
    
    def clear(self):
        """Remove vignette effect."""
        self.canvas.delete("vignette")
        self.vignette_items.clear()
    
    def enable(self, enabled: bool = True):
        """Enable or disable curvature effect."""
        self._enabled = enabled
        if not enabled:
            self.clear()
        else:
            self.draw()


class PhosphorGlow:
    """Simulates phosphor glow/bloom effect on text and elements."""
    
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.glow_items: List[int] = []
        self._enabled = True
        self._intensity = 1.0
    
    def add_glow(self, x: int, y: int, text: str, 
                 font: tuple = None, layers: int = 3) -> List[int]:
        """Add glowing text at position."""
        if not self._enabled:
            return []
        
        if font is None:
            font = PipBoyFonts.body()
        
        items = []
        glow_colors = [
            VaultTecColors.PHOSPHOR_DARK,
            VaultTecColors.PHOSPHOR_DIM,
            VaultTecColors.PHOSPHOR_MAIN,
        ]
        
        # Draw glow layers (back to front)
        for i, color in enumerate(glow_colors[:layers]):
            offset = (layers - i) * 1
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                item = self.canvas.create_text(
                    x + dx, y + dy,
                    text=text, font=font, fill=color,
                    tags="glow"
                )
                items.append(item)
        
        # Main text on top
        main_item = self.canvas.create_text(
            x, y, text=text, font=font,
            fill=VaultTecColors.PHOSPHOR_BRIGHT,
            tags="glow_main"
        )
        items.append(main_item)
        
        self.glow_items.extend(items)
        return items
    
    def clear(self):
        """Remove all glow effects."""
        self.canvas.delete("glow")
        self.canvas.delete("glow_main")
        self.glow_items.clear()
    
    def set_intensity(self, intensity: float):
        """Set glow intensity (0.0 to 1.0)."""
        self._intensity = max(0.0, min(1.0, intensity))
    
    def enable(self, enabled: bool = True):
        """Enable or disable glow effects."""
        self._enabled = enabled
        if not enabled:
            self.clear()


# =============================================================================
# SECTION 6: CUSTOM WIDGETS
# =============================================================================

class CRTFrame(tk.Frame):
    """
    A frame styled to look like a CRT monitor bezel.
    Features chunky borders with depth simulation.
    """
    
    def __init__(self, parent, title: str = "", **kwargs):
        # Extract custom options
        self.title_text = title
        self.show_screws = kwargs.pop("show_screws", True)
        
        super().__init__(parent, **kwargs)
        
        self.configure(
            bg=VaultTecColors.BEZEL_DARK,
            highlightbackground=VaultTecColors.BEZEL_EDGE,
            highlightthickness=3,
            padx=8,
            pady=8
        )
        
        self._create_bezel()
    
    def _create_bezel(self):
        """Create the bezel decoration."""
        # Title bar if title provided
        if self.title_text:
            title_frame = tk.Frame(self, bg=VaultTecColors.BEZEL_DARK)
            title_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Decorative line before title
            tk.Label(
                title_frame,
                text="══",
                font=PipBoyFonts.small(),
                fg=VaultTecColors.PHOSPHOR_DIM,
                bg=VaultTecColors.BEZEL_DARK
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            # Title
            tk.Label(
                title_frame,
                text=self.title_text,
                font=PipBoyFonts.header(),
                fg=VaultTecColors.PHOSPHOR_BRIGHT,
                bg=VaultTecColors.BEZEL_DARK
            ).pack(side=tk.LEFT)
            
            # Decorative line after title
            tk.Label(
                title_frame,
                text="══" * 20,
                font=PipBoyFonts.small(),
                fg=VaultTecColors.PHOSPHOR_DIM,
                bg=VaultTecColors.BEZEL_DARK
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))


class InsetPanel(tk.Frame):
    """
    A panel with inset/beveled appearance.
    Simulates recessed screen area within the CRT frame.
    """
    
    def __init__(self, parent, title: str = "", depth: int = 2, **kwargs):
        self.title_text = title
        self.depth = depth
        
        super().__init__(parent, **kwargs)
        
        self.configure(
            bg=VaultTecColors.CRT_DARK,
            highlightbackground=VaultTecColors.INSET_SHADOW,
            highlightthickness=depth,
            relief=tk.SUNKEN,
            padx=4,
            pady=4
        )
        
        # Add title if provided
        if self.title_text:
            tk.Label(
                self,
                text=self.title_text,
                font=PipBoyFonts.small(),
                fg=VaultTecColors.TEXT_SECONDARY,
                bg=VaultTecColors.CRT_DARK,
                anchor=tk.W
            ).pack(fill=tk.X, pady=(0, 2))


class ChunkyButton(tk.Button):
    """
    A chunky, retro-styled button like Pip-Boy hardware buttons.
    Features raised appearance with highlight states.
    """
    
    def __init__(self, parent, text: str = "", command: Callable = None, **kwargs):
        # Default styling
        defaults = {
            "font": PipBoyFonts.body(),
            "fg": VaultTecColors.PHOSPHOR_MAIN,
            "bg": VaultTecColors.BEZEL_DARK,
            "activeforeground": VaultTecColors.PHOSPHOR_BRIGHT,
            "activebackground": VaultTecColors.BEZEL_LIGHT,
            "highlightbackground": VaultTecColors.BEZEL_EDGE,
            "highlightthickness": 2,
            "relief": tk.RAISED,
            "borderwidth": 3,
            "padx": 10,
            "pady": 5,
            "cursor": "hand2"
        }
        defaults.update(kwargs)
        
        super().__init__(parent, text=text, command=command, **defaults)
        
        # Bind hover effects
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        
        self._original_fg = self.cget("fg")
        self._original_bg = self.cget("bg")
    
    def _on_hover(self, event=None):
        """Highlight on hover."""
        self.configure(
            fg=VaultTecColors.PHOSPHOR_BRIGHT,
            bg=VaultTecColors.BEZEL_LIGHT
        )
    
    def _on_leave(self, event=None):
        """Restore on leave."""
        self.configure(
            fg=self._original_fg,
            bg=self._original_bg
        )


class TerminalText(tk.Text):
    """
    A text widget styled as a terminal display.
    Features monospace font, green-on-black colors, and optional typing effect.
    """
    
    def __init__(self, parent, **kwargs):
        defaults = {
            "font": PipBoyFonts.body(),
            "fg": VaultTecColors.PHOSPHOR_MAIN,
            "bg": VaultTecColors.CRT_BLACK,
            "insertbackground": VaultTecColors.PHOSPHOR_BRIGHT,
            "selectbackground": VaultTecColors.PHOSPHOR_DIM,
            "selectforeground": VaultTecColors.PHOSPHOR_BRIGHT,
            "highlightbackground": VaultTecColors.INSET_SHADOW,
            "highlightthickness": 1,
            "relief": tk.SUNKEN,
            "borderwidth": 2,
            "padx": 8,
            "pady": 8,
            "wrap": tk.WORD
        }
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)
        
        # Configure text tags for different colors
        self.tag_configure("bright", foreground=VaultTecColors.PHOSPHOR_BRIGHT)
        self.tag_configure("dim", foreground=VaultTecColors.PHOSPHOR_DIM)
        self.tag_configure("warn", foreground=VaultTecColors.AMBER_WARN)
        self.tag_configure("alert", foreground=VaultTecColors.RED_ALERT)
        self.tag_configure("title", foreground=VaultTecColors.TEXT_TITLE, 
                          font=PipBoyFonts.header())
        self.tag_configure("flavor", foreground=VaultTecColors.TEXT_FLAVOR)
    
    def append(self, text: str, tag: str = None):
        """Append text with optional tag."""
        self.configure(state=tk.NORMAL)
        if tag:
            self.insert(tk.END, text, tag)
        else:
            self.insert(tk.END, text)
        self.see(tk.END)
        self.configure(state=tk.DISABLED)
    
    def clear(self):
        """Clear all text."""
        self.configure(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self.configure(state=tk.DISABLED)


class PipBoyListbox(tk.Listbox):
    """A listbox styled for Pip-Boy interface."""
    
    def __init__(self, parent, **kwargs):
        defaults = {
            "font": PipBoyFonts.body(),
            "fg": VaultTecColors.PHOSPHOR_MAIN,
            "bg": VaultTecColors.CRT_BLACK,
            "selectforeground": VaultTecColors.CRT_BLACK,
            "selectbackground": VaultTecColors.PHOSPHOR_MAIN,
            "highlightbackground": VaultTecColors.INSET_SHADOW,
            "highlightthickness": 1,
            "relief": tk.SUNKEN,
            "borderwidth": 2,
            "activestyle": "none"
        }
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)


class PipBoyProgressBar(tk.Canvas):
    """A segmented progress bar in Pip-Boy style."""
    
    def __init__(self, parent, width: int = 200, height: int = 20, 
                 segments: int = 20, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.configure(
            bg=VaultTecColors.CRT_BLACK,
            highlightbackground=VaultTecColors.INSET_SHADOW,
            highlightthickness=1
        )
        
        self.segments = segments
        self.bar_width = width
        self.bar_height = height
        self._value = 0
        self._segment_items = []
        
        self._draw_segments()
    
    def _draw_segments(self):
        """Draw the segment outlines."""
        self.delete("all")
        self._segment_items.clear()
        
        segment_width = (self.bar_width - 4) / self.segments
        padding = 2
        
        for i in range(self.segments):
            x1 = 2 + i * segment_width + padding
            x2 = 2 + (i + 1) * segment_width - padding
            y1 = 4
            y2 = self.bar_height - 4
            
            item = self.create_rectangle(
                x1, y1, x2, y2,
                fill=VaultTecColors.CRT_DARK,
                outline=VaultTecColors.PHOSPHOR_DIM,
                tags=f"segment_{i}"
            )
            self._segment_items.append(item)
        
        self._update_fill()
    
    def _update_fill(self):
        """Update segment fill based on current value."""
        filled_segments = int(self._value / 100 * self.segments)
        
        for i, item in enumerate(self._segment_items):
            if i < filled_segments:
                self.itemconfig(item, fill=VaultTecColors.PHOSPHOR_MAIN)
            else:
                self.itemconfig(item, fill=VaultTecColors.CRT_DARK)
    
    def set_value(self, value: int):
        """Set progress value (0-100)."""
        self._value = max(0, min(100, value))
        self._update_fill()
    
    def get_value(self) -> int:
        """Get current value."""
        return self._value


# =============================================================================
# SECTION 7: ANIMATION SYSTEM
# =============================================================================

class CRTAnimator:
    """
    Manages all Pip-Boy animations:
    - Phosphor flicker
    - Scanline scroll
    - Text typing effect
    - Pulse animations
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._running = False
        self._animations: Dict[str, Dict[str, Any]] = {}
        self._after_ids: List[str] = []
    
    def start(self):
        """Start the animation loop."""
        self._running = True
        self._tick()
    
    def stop(self):
        """Stop all animations."""
        self._running = False
        for after_id in self._after_ids:
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()
    
    def _tick(self):
        """Main animation tick."""
        if not self._running:
            return
        
        for name, anim in list(self._animations.items()):
            if anim.get("enabled", True):
                callback = anim.get("callback")
                if callback:
                    try:
                        callback(anim)
                    except Exception:
                        pass
        
        # Schedule next tick
        after_id = self.root.after(50, self._tick)  # ~20 FPS
        self._after_ids.append(after_id)
    
    def register(self, name: str, callback: Callable, **kwargs):
        """Register an animation."""
        self._animations[name] = {
            "callback": callback,
            "enabled": True,
            "frame": 0,
            **kwargs
        }
    
    def unregister(self, name: str):
        """Unregister an animation."""
        self._animations.pop(name, None)
    
    def enable(self, name: str, enabled: bool = True):
        """Enable or disable a specific animation."""
        if name in self._animations:
            self._animations[name]["enabled"] = enabled


class TextTyper:
    """Simulates typing effect for text widgets."""
    
    def __init__(self, widget: tk.Text, speed_ms: int = 30):
        self.widget = widget
        self.speed_ms = speed_ms
        self._queue: List[str] = []
        self._typing = False
        self._after_id = None
    
    def type_text(self, text: str, callback: Callable = None):
        """Queue text to be typed out."""
        self._queue.append((text, callback))
        if not self._typing:
            self._start_typing()
    
    def _start_typing(self):
        """Begin typing from queue."""
        if not self._queue:
            self._typing = False
            return
        
        self._typing = True
        text, callback = self._queue.pop(0)
        self._type_char(text, 0, callback)
    
    def _type_char(self, text: str, index: int, callback: Callable):
        """Type one character."""
        if index < len(text):
            self.widget.configure(state=tk.NORMAL)
            self.widget.insert(tk.END, text[index])
            self.widget.see(tk.END)
            self.widget.configure(state=tk.DISABLED)
            
            self._after_id = self.widget.after(
                self.speed_ms,
                lambda: self._type_char(text, index + 1, callback)
            )
        else:
            if callback:
                callback()
            self._start_typing()
    
    def stop(self):
        """Stop typing."""
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
        self._queue.clear()
        self._typing = False


# =============================================================================
# SECTION 8: TTK STYLE CONFIGURATION
# =============================================================================

def configure_ttk_styles(style: ttk.Style):
    """Configure all ttk widget styles for Pip-Boy theme."""
    
    # -------------------------------------------------------------------------
    # Notebook (Tabs)
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TNotebook",
        background=VaultTecColors.BEZEL_DARK,
        borderwidth=0,
        tabmargins=[2, 5, 2, 0]
    )
    
    style.configure(
        "PipBoy.TNotebook.Tab",
        background=VaultTecColors.BEZEL_DARK,
        foreground=VaultTecColors.PHOSPHOR_DIM,
        padding=[12, 6],
        font=PipBoyFonts.body(),
        borderwidth=2
    )
    
    style.map(
        "PipBoy.TNotebook.Tab",
        background=[
            ("selected", VaultTecColors.CRT_DARK),
            ("active", VaultTecColors.BEZEL_LIGHT)
        ],
        foreground=[
            ("selected", VaultTecColors.PHOSPHOR_BRIGHT),
            ("active", VaultTecColors.PHOSPHOR_MAIN)
        ],
        expand=[("selected", [1, 1, 1, 0])]
    )
    
    # -------------------------------------------------------------------------
    # Frame
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TFrame",
        background=VaultTecColors.CRT_DARK
    )
    
    style.configure(
        "PipBoy.Bezel.TFrame",
        background=VaultTecColors.BEZEL_DARK
    )
    
    style.configure(
        "PipBoy.Inset.TFrame",
        background=VaultTecColors.CRT_BLACK
    )
    
    # -------------------------------------------------------------------------
    # Label
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        font=PipBoyFonts.body()
    )
    
    style.configure(
        "PipBoy.Title.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_BRIGHT,
        font=PipBoyFonts.title()
    )
    
    style.configure(
        "PipBoy.Header.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_BRIGHT,
        font=PipBoyFonts.header()
    )
    
    style.configure(
        "PipBoy.Dim.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_DIM,
        font=PipBoyFonts.small()
    )
    
    style.configure(
        "PipBoy.Flavor.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.TEXT_FLAVOR,
        font=PipBoyFonts.tiny()
    )
    
    style.configure(
        "PipBoy.Warn.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.AMBER_WARN,
        font=PipBoyFonts.body()
    )
    
    style.configure(
        "PipBoy.Alert.TLabel",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.RED_ALERT,
        font=PipBoyFonts.body()
    )
    
    # -------------------------------------------------------------------------
    # Button
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TButton",
        background=VaultTecColors.BEZEL_DARK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        font=PipBoyFonts.body(),
        borderwidth=3,
        relief=tk.RAISED,
        padding=[10, 5]
    )
    
    style.map(
        "PipBoy.TButton",
        background=[
            ("active", VaultTecColors.BEZEL_LIGHT),
            ("pressed", VaultTecColors.CRT_DARK)
        ],
        foreground=[
            ("active", VaultTecColors.PHOSPHOR_BRIGHT),
            ("pressed", VaultTecColors.PHOSPHOR_BRIGHT)
        ]
    )
    
    # -------------------------------------------------------------------------
    # Entry
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TEntry",
        fieldbackground=VaultTecColors.CRT_BLACK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        insertcolor=VaultTecColors.PHOSPHOR_BRIGHT,
        borderwidth=2,
        relief=tk.SUNKEN,
        font=PipBoyFonts.body()
    )
    
    style.map(
        "PipBoy.TEntry",
        fieldbackground=[("focus", VaultTecColors.CRT_DARK)],
        foreground=[("focus", VaultTecColors.PHOSPHOR_BRIGHT)]
    )
    
    # -------------------------------------------------------------------------
    # Combobox
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TCombobox",
        fieldbackground=VaultTecColors.CRT_BLACK,
        background=VaultTecColors.BEZEL_DARK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        arrowcolor=VaultTecColors.PHOSPHOR_MAIN,
        borderwidth=2,
        relief=tk.SUNKEN,
        font=PipBoyFonts.body()
    )
    
    style.map(
        "PipBoy.TCombobox",
        fieldbackground=[
            ("readonly", VaultTecColors.CRT_BLACK),
            ("focus", VaultTecColors.CRT_DARK)
        ],
        foreground=[
            ("readonly", VaultTecColors.PHOSPHOR_MAIN),
            ("focus", VaultTecColors.PHOSPHOR_BRIGHT)
        ]
    )
    
    # -------------------------------------------------------------------------
    # Treeview
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.Treeview",
        background=VaultTecColors.CRT_BLACK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        fieldbackground=VaultTecColors.CRT_BLACK,
        font=PipBoyFonts.body(),
        rowheight=24,
        borderwidth=2,
        relief=tk.SUNKEN
    )
    
    style.configure(
        "PipBoy.Treeview.Heading",
        background=VaultTecColors.BEZEL_DARK,
        foreground=VaultTecColors.PHOSPHOR_BRIGHT,
        font=PipBoyFonts.header(),
        borderwidth=1,
        relief=tk.RAISED
    )
    
    style.map(
        "PipBoy.Treeview",
        background=[("selected", VaultTecColors.PHOSPHOR_DIM)],
        foreground=[("selected", VaultTecColors.CRT_BLACK)]
    )
    
    style.map(
        "PipBoy.Treeview.Heading",
        background=[("active", VaultTecColors.BEZEL_LIGHT)]
    )
    
    # -------------------------------------------------------------------------
    # Scrollbar
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.Vertical.TScrollbar",
        background=VaultTecColors.BEZEL_DARK,
        troughcolor=VaultTecColors.CRT_BLACK,
        borderwidth=2,
        arrowcolor=VaultTecColors.PHOSPHOR_MAIN,
        relief=tk.RAISED
    )
    
    style.map(
        "PipBoy.Vertical.TScrollbar",
        background=[("active", VaultTecColors.BEZEL_LIGHT)]
    )
    
    style.configure(
        "PipBoy.Horizontal.TScrollbar",
        background=VaultTecColors.BEZEL_DARK,
        troughcolor=VaultTecColors.CRT_BLACK,
        borderwidth=2,
        arrowcolor=VaultTecColors.PHOSPHOR_MAIN,
        relief=tk.RAISED
    )
    
    # -------------------------------------------------------------------------
    # Progressbar
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.Horizontal.TProgressbar",
        background=VaultTecColors.PHOSPHOR_MAIN,
        troughcolor=VaultTecColors.CRT_BLACK,
        borderwidth=2,
        relief=tk.SUNKEN
    )
    
    # -------------------------------------------------------------------------
    # Separator
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TSeparator",
        background=VaultTecColors.PHOSPHOR_DIM
    )
    
    # -------------------------------------------------------------------------
    # Checkbutton
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TCheckbutton",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        font=PipBoyFonts.body(),
        indicatorcolor=VaultTecColors.CRT_BLACK
    )
    
    style.map(
        "PipBoy.TCheckbutton",
        background=[("active", VaultTecColors.CRT_DARK)],
        foreground=[("active", VaultTecColors.PHOSPHOR_BRIGHT)],
        indicatorcolor=[
            ("selected", VaultTecColors.PHOSPHOR_MAIN),
            ("pressed", VaultTecColors.PHOSPHOR_BRIGHT)
        ]
    )
    
    # -------------------------------------------------------------------------
    # Radiobutton
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TRadiobutton",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_MAIN,
        font=PipBoyFonts.body(),
        indicatorcolor=VaultTecColors.CRT_BLACK
    )
    
    style.map(
        "PipBoy.TRadiobutton",
        background=[("active", VaultTecColors.CRT_DARK)],
        foreground=[("active", VaultTecColors.PHOSPHOR_BRIGHT)],
        indicatorcolor=[
            ("selected", VaultTecColors.PHOSPHOR_MAIN),
            ("pressed", VaultTecColors.PHOSPHOR_BRIGHT)
        ]
    )
    
    # -------------------------------------------------------------------------
    # LabelFrame
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TLabelframe",
        background=VaultTecColors.CRT_DARK,
        borderwidth=2,
        relief=tk.GROOVE
    )
    
    style.configure(
        "PipBoy.TLabelframe.Label",
        background=VaultTecColors.CRT_DARK,
        foreground=VaultTecColors.PHOSPHOR_BRIGHT,
        font=PipBoyFonts.header()
    )
    
    # -------------------------------------------------------------------------
    # PanedWindow
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TPanedwindow",
        background=VaultTecColors.BEZEL_DARK
    )
    
    # -------------------------------------------------------------------------
    # Scale
    # -------------------------------------------------------------------------
    style.configure(
        "PipBoy.TScale",
        background=VaultTecColors.BEZEL_DARK,
        troughcolor=VaultTecColors.CRT_BLACK
    )
    
    style.map(
        "PipBoy.TScale",
        background=[("active", VaultTecColors.PHOSPHOR_MAIN)]
    )


# =============================================================================
# SECTION 9: MAIN SKIN CLASS
# =============================================================================

@dataclass
class SkinState:
    """Stores original widget states for reverting."""
    widget: Any
    original_config: Dict[str, Any]
    widget_type: str


class PipBoySkin:
    """
    Complete Pip-Boy 3000 Mk IV skin for NEXUS WiFi Radar.
    
    Transforms the entire interface into a retro-futuristic
    Fallout-style terminal display with CRT effects, phosphor
    glow, and authentic Vault-Tec personality.
    """
    
    def __init__(self, root: tk.Tk = None):
        """
        Initialize the Pip-Boy skin.
        
        Args:
            root: The root Tk window. If None, will try to find it.
        """
        self.root = root
        self._applied = False
        self._original_styles: List[SkinState] = []  # For test compatibility
        self._original_states: List[SkinState] = self._original_styles  # Alias
        self._style: Optional[ttk.Style] = None
        self._animator: Optional[CRTAnimator] = None
        self._scanlines: Dict[int, ScanlineOverlay] = {}
        self._status_message_idx = 0
        self._status_after_id = None
    
    @property
    def is_applied(self) -> bool:
        """Check if skin is currently applied."""
        return self._applied
    
    def apply(self, root: tk.Tk = None) -> bool:
        """
        Apply the Pip-Boy skin to the application.
        
        Args:
            root: The root Tk window (optional if provided in __init__).
            
        Returns:
            True if successfully applied, False otherwise.
        """
        if self._applied:
            return True
        
        if root:
            self.root = root
        
        if not self.root:
            return False
        
        try:
            # Store original window configuration
            self._store_original_state(self.root, "root")
            
            # Configure root window
            self.root.configure(bg=VaultTecColors.BEZEL_DARK)
            
            # Try to set window title with Vault-Tec flair
            try:
                original_title = self.root.title()
                if "NEXUS" in original_title.upper():
                    self.root.title("NEXUS WiFi Radar // VAULT-TEC APPROVED")
            except Exception:
                pass
            
            # Configure ttk styles
            self._style = ttk.Style()
            configure_ttk_styles(self._style)
            
            # Apply theme to all existing widgets
            self._apply_to_widget_tree(self.root)
            
            # Start animator
            self._animator = CRTAnimator(self.root)
            self._animator.start()
            
            # Start status message rotation
            self._start_status_rotation()
            
            self._applied = True
            return True
            
        except Exception as e:
            print(f"Error applying Pip-Boy skin: {e}")
            return False
    
    def revert(self) -> bool:
        """
        Revert to original appearance.
        
        Returns:
            True if successfully reverted, False otherwise.
        """
        if not self._applied:
            return True
        
        try:
            # Stop animations
            if self._animator:
                self._animator.stop()
                self._animator = None
            
            # Stop status rotation
            if self._status_after_id:
                try:
                    self.root.after_cancel(self._status_after_id)
                except Exception:
                    pass
                self._status_after_id = None
            
            # Clear scanlines
            for scanline in self._scanlines.values():
                scanline.clear()
            self._scanlines.clear()
            
            # Restore original widget states
            for state in reversed(self._original_states):
                try:
                    for key, value in state.original_config.items():
                        state.widget.configure(**{key: value})
                except Exception:
                    pass
            
            self._original_states.clear()
            
            # Restore window title
            try:
                title = self.root.title()
                if "VAULT-TEC" in title:
                    self.root.title(title.replace(" // VAULT-TEC APPROVED", ""))
            except Exception:
                pass
            
            self._applied = False
            return True
            
        except Exception as e:
            print(f"Error reverting Pip-Boy skin: {e}")
            return False
    
    def _store_original_state(self, widget: Any, widget_type: str):
        """Store a widget's original configuration."""
        try:
            config = {}
            for key in ["bg", "background", "fg", "foreground", "font"]:
                try:
                    config[key] = widget.cget(key)
                except Exception:
                    pass
            
            self._original_states.append(SkinState(
                widget=widget,
                original_config=config,
                widget_type=widget_type
            ))
        except Exception:
            pass
    
    def _apply_to_widget_tree(self, widget: Any):
        """Recursively apply skin to widget and all children."""
        self._apply_to_widget(widget)
        
        # Process children
        try:
            for child in widget.winfo_children():
                self._apply_to_widget_tree(child)
        except Exception:
            pass
    
    def _apply_to_widget(self, widget: Any):
        """Apply Pip-Boy styling to a single widget."""
        widget_class = widget.winfo_class()
        
        try:
            # Store original state
            self._store_original_state(widget, widget_class)
            
            # Apply based on widget type
            if widget_class == "Frame" or widget_class == "TFrame":
                self._apply_frame_style(widget)
            elif widget_class == "Label" or widget_class == "TLabel":
                self._apply_label_style(widget)
            elif widget_class == "Button" or widget_class == "TButton":
                self._apply_button_style(widget)
            elif widget_class == "Entry" or widget_class == "TEntry":
                self._apply_entry_style(widget)
            elif widget_class == "Text":
                self._apply_text_style(widget)
            elif widget_class == "Listbox":
                self._apply_listbox_style(widget)
            elif widget_class == "Canvas":
                self._apply_canvas_style(widget)
            elif widget_class == "TNotebook":
                self._apply_notebook_style(widget)
            elif widget_class == "Treeview":
                self._apply_treeview_style(widget)
            elif widget_class == "TCombobox":
                self._apply_combobox_style(widget)
            elif widget_class == "TScrollbar":
                self._apply_scrollbar_style(widget)
            elif widget_class == "TCheckbutton":
                self._apply_checkbutton_style(widget)
            elif widget_class == "TRadiobutton":
                self._apply_radiobutton_style(widget)
            elif widget_class == "TLabelframe":
                self._apply_labelframe_style(widget)
            elif widget_class == "TProgressbar":
                self._apply_progressbar_style(widget)
            elif widget_class == "Menu":
                self._apply_menu_style(widget)
                
        except Exception:
            pass
    
    def _apply_frame_style(self, widget):
        """Apply Pip-Boy style to Frame widgets."""
        try:
            if isinstance(widget, ttk.Frame):
                widget.configure(style="PipBoy.TFrame")
            else:
                widget.configure(bg=VaultTecColors.CRT_DARK)
        except Exception:
            pass
    
    def _apply_label_style(self, widget):
        """Apply Pip-Boy style to Label widgets."""
        try:
            if isinstance(widget, ttk.Label):
                widget.configure(style="PipBoy.TLabel")
            else:
                widget.configure(
                    bg=VaultTecColors.CRT_DARK,
                    fg=VaultTecColors.PHOSPHOR_MAIN,
                    font=PipBoyFonts.body()
                )
        except Exception:
            pass
    
    def _apply_button_style(self, widget):
        """Apply Pip-Boy style to Button widgets."""
        try:
            if isinstance(widget, ttk.Button):
                widget.configure(style="PipBoy.TButton")
            else:
                widget.configure(
                    bg=VaultTecColors.BEZEL_DARK,
                    fg=VaultTecColors.PHOSPHOR_MAIN,
                    activebackground=VaultTecColors.BEZEL_LIGHT,
                    activeforeground=VaultTecColors.PHOSPHOR_BRIGHT,
                    font=PipBoyFonts.body(),
                    relief=tk.RAISED,
                    borderwidth=3
                )
        except Exception:
            pass
    
    def _apply_entry_style(self, widget):
        """Apply Pip-Boy style to Entry widgets."""
        try:
            if isinstance(widget, ttk.Entry):
                widget.configure(style="PipBoy.TEntry")
            else:
                widget.configure(
                    bg=VaultTecColors.CRT_BLACK,
                    fg=VaultTecColors.PHOSPHOR_MAIN,
                    insertbackground=VaultTecColors.PHOSPHOR_BRIGHT,
                    font=PipBoyFonts.body(),
                    relief=tk.SUNKEN
                )
        except Exception:
            pass
    
    def _apply_text_style(self, widget):
        """Apply Pip-Boy style to Text widgets."""
        try:
            widget.configure(
                bg=VaultTecColors.CRT_BLACK,
                fg=VaultTecColors.PHOSPHOR_MAIN,
                insertbackground=VaultTecColors.PHOSPHOR_BRIGHT,
                selectbackground=VaultTecColors.PHOSPHOR_DIM,
                selectforeground=VaultTecColors.PHOSPHOR_BRIGHT,
                font=PipBoyFonts.body(),
                relief=tk.SUNKEN,
                borderwidth=2
            )
        except Exception:
            pass
    
    def _apply_listbox_style(self, widget):
        """Apply Pip-Boy style to Listbox widgets."""
        try:
            widget.configure(
                bg=VaultTecColors.CRT_BLACK,
                fg=VaultTecColors.PHOSPHOR_MAIN,
                selectbackground=VaultTecColors.PHOSPHOR_MAIN,
                selectforeground=VaultTecColors.CRT_BLACK,
                font=PipBoyFonts.body(),
                relief=tk.SUNKEN,
                borderwidth=2
            )
        except Exception:
            pass
    
    def _apply_canvas_style(self, widget):
        """Apply Pip-Boy style to Canvas widgets."""
        try:
            widget.configure(
                bg=VaultTecColors.CRT_BLACK,
                highlightbackground=VaultTecColors.PHOSPHOR_DIM,
                highlightthickness=1
            )
            
            # Add scanline overlay
            widget_id = id(widget)
            if widget_id not in self._scanlines:
                scanline = ScanlineOverlay(widget)
                self._scanlines[widget_id] = scanline
                # Defer drawing until widget is mapped
                widget.bind("<Map>", lambda e, s=scanline: s.draw(), add=True)
                widget.bind("<Configure>", lambda e, s=scanline: s.draw(), add=True)
        except Exception:
            pass
    
    def _apply_notebook_style(self, widget):
        """Apply Pip-Boy style to Notebook widgets."""
        try:
            widget.configure(style="PipBoy.TNotebook")
        except Exception:
            pass
    
    def _apply_treeview_style(self, widget):
        """Apply Pip-Boy style to Treeview widgets."""
        try:
            widget.configure(style="PipBoy.Treeview")
            
            # Configure tag colors for different states
            widget.tag_configure("normal", 
                                 background=VaultTecColors.CRT_BLACK,
                                 foreground=VaultTecColors.PHOSPHOR_MAIN)
            widget.tag_configure("threat_high",
                                 background=VaultTecColors.CRT_BLACK,
                                 foreground=VaultTecColors.RED_ALERT)
            widget.tag_configure("threat_medium",
                                 background=VaultTecColors.CRT_BLACK,
                                 foreground=VaultTecColors.AMBER_WARN)
            widget.tag_configure("hidden",
                                 background=VaultTecColors.CRT_BLACK,
                                 foreground=VaultTecColors.PHOSPHOR_DIM)
        except Exception:
            pass
    
    def _apply_combobox_style(self, widget):
        """Apply Pip-Boy style to Combobox widgets."""
        try:
            widget.configure(style="PipBoy.TCombobox")
        except Exception:
            pass
    
    def _apply_scrollbar_style(self, widget):
        """Apply Pip-Boy style to Scrollbar widgets."""
        try:
            # Determine orientation
            orient = str(widget.cget("orient")).lower() if hasattr(widget, "cget") else "vertical"
            if orient == "horizontal":
                widget.configure(style="PipBoy.Horizontal.TScrollbar")
            else:
                widget.configure(style="PipBoy.Vertical.TScrollbar")
        except Exception:
            pass
    
    def _apply_checkbutton_style(self, widget):
        """Apply Pip-Boy style to Checkbutton widgets."""
        try:
            widget.configure(style="PipBoy.TCheckbutton")
        except Exception:
            pass
    
    def _apply_radiobutton_style(self, widget):
        """Apply Pip-Boy style to Radiobutton widgets."""
        try:
            widget.configure(style="PipBoy.TRadiobutton")
        except Exception:
            pass
    
    def _apply_labelframe_style(self, widget):
        """Apply Pip-Boy style to LabelFrame widgets."""
        try:
            widget.configure(style="PipBoy.TLabelframe")
        except Exception:
            pass
    
    def _apply_progressbar_style(self, widget):
        """Apply Pip-Boy style to Progressbar widgets."""
        try:
            widget.configure(style="PipBoy.Horizontal.TProgressbar")
        except Exception:
            pass
    
    def _apply_menu_style(self, widget):
        """Apply Pip-Boy style to Menu widgets."""
        try:
            widget.configure(
                bg=VaultTecColors.BEZEL_DARK,
                fg=VaultTecColors.PHOSPHOR_MAIN,
                activebackground=VaultTecColors.PHOSPHOR_DIM,
                activeforeground=VaultTecColors.PHOSPHOR_BRIGHT,
                font=PipBoyFonts.body()
            )
        except Exception:
            pass
    
    def _start_status_rotation(self):
        """Start rotating status messages (if status bar exists)."""
        # This is a placeholder for status message rotation
        # The actual implementation depends on the app's status bar
        pass
    
    # -------------------------------------------------------------------------
    # Public API for runtime customization
    # -------------------------------------------------------------------------
    
    def get_colors(self) -> type:
        """Get the VaultTecColors class for external use."""
        return VaultTecColors
    
    def get_fonts(self) -> type:
        """Get the PipBoyFonts class for external use."""
        return PipBoyFonts
    
    def get_flavor_text(self) -> type:
        """Get the VaultTecText class for external use."""
        return VaultTecText
    
    def get_decorations(self) -> type:
        """Get the VaultTecDecorations class for external use."""
        return VaultTecDecorations
    
    def create_crt_frame(self, parent, **kwargs) -> CRTFrame:
        """Create a new CRT-styled frame."""
        return CRTFrame(parent, **kwargs)
    
    def create_inset_panel(self, parent, **kwargs) -> InsetPanel:
        """Create a new inset panel."""
        return InsetPanel(parent, **kwargs)
    
    def create_chunky_button(self, parent, **kwargs) -> ChunkyButton:
        """Create a new chunky button."""
        return ChunkyButton(parent, **kwargs)
    
    def create_terminal_text(self, parent, **kwargs) -> TerminalText:
        """Create a new terminal text widget."""
        return TerminalText(parent, **kwargs)
    
    def create_progress_bar(self, parent, **kwargs) -> PipBoyProgressBar:
        """Create a new Pip-Boy style progress bar."""
        return PipBoyProgressBar(parent, **kwargs)
    
    def create_data_card(self, parent, **kwargs) -> InsetPanel:
        """Create a data card widget (alias for inset panel)."""
        return InsetPanel(parent, **kwargs)
    
    def get_theme(self) -> Dict[str, Any]:
        """Get the theme dictionary."""
        return PIPBOY_THEME
    
    def style_radar_canvas(self, canvas: tk.Canvas):
        """Apply Pip-Boy style to a radar canvas."""
        self._apply_canvas_style(canvas)
    
    def draw_radar_grid(self, canvas: tk.Canvas, cx: int, cy: int, radius: int):
        """Draw Pip-Boy styled radar grid."""
        # Draw concentric circles
        for i in range(1, 5):
            r = int(radius * i / 4)
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=VaultTecColors.PHOSPHOR_DIM,
                width=1,
                tags="radar_grid"
            )
        
        # Draw crosshairs
        canvas.create_line(
            cx - radius, cy, cx + radius, cy,
            fill=VaultTecColors.PHOSPHOR_DIM,
            width=1,
            tags="radar_grid"
        )
        canvas.create_line(
            cx, cy - radius, cx, cy + radius,
            fill=VaultTecColors.PHOSPHOR_DIM,
            width=1,
            tags="radar_grid"
        )
    
    def draw_radar_sweep(self, canvas: tk.Canvas, cx: int, cy: int, 
                         radius: int, angle: float):
        """Draw the radar sweep line."""
        canvas.delete("radar_sweep")
        import math
        end_x = cx + int(radius * math.cos(math.radians(angle)))
        end_y = cy - int(radius * math.sin(math.radians(angle)))
        canvas.create_line(
            cx, cy, end_x, end_y,
            fill=VaultTecColors.PHOSPHOR_BRIGHT,
            width=2,
            tags="radar_sweep"
        )


# =============================================================================
# SECTION 10: TAB BAR AND ADDITIONAL CLASSES
# =============================================================================

class PipBoyTabBar:
    """Tab bar styling helper for Pip-Boy theme."""
    
    def __init__(self, notebook: ttk.Notebook):
        """Initialize with a notebook widget."""
        self.notebook = notebook
    
    def restyle_tabs(self):
        """Restyle the tabs with Pip-Boy appearance."""
        if not self.notebook:
            return
        
        try:
            self.notebook.configure(style="PipBoy.TNotebook")
        except Exception:
            pass


# =============================================================================
# SECTION 11: MODULE-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================

# Global skin instance (named for test compatibility)
_pipboy_skin: Optional[PipBoySkin] = None
_skin_instance: Optional[PipBoySkin] = None  # Alias


def get_pipboy_skin(root: tk.Tk = None) -> Optional[PipBoySkin]:
    """
    Get or create the global Pip-Boy skin instance.
    
    Args:
        root: The root Tk window (required on first call).
        
    Returns:
        The PipBoySkin instance, or None if no root provided and not yet created.
    """
    global _pipboy_skin, _skin_instance
    
    if root is None and _pipboy_skin is None:
        return None
    
    if _pipboy_skin is None:
        _pipboy_skin = PipBoySkin(root)
        _skin_instance = _pipboy_skin
    elif root and _pipboy_skin.root is None:
        _pipboy_skin.root = root
    
    return _pipboy_skin


def get_pipboy_theme() -> Dict[str, Any]:
    """Get the Pip-Boy theme dictionary."""
    return PIPBOY_THEME


def apply_pipboy_skin(root: tk.Tk) -> bool:
    """
    Apply Pip-Boy skin to the application.
    
    Args:
        root: The root Tk window.
        
    Returns:
        True if successful, False otherwise.
    """
    skin = get_pipboy_skin(root)
    if skin:
        return skin.apply(root)
    return False


def revert_pipboy_skin() -> bool:
    """
    Revert from Pip-Boy skin to original appearance.
    
    Returns:
        True if successful, False otherwise.
    """
    if _pipboy_skin:
        return _pipboy_skin.revert()
    return True


def is_pipboy_active() -> bool:
    """Check if Pip-Boy skin is currently active."""
    return _pipboy_skin is not None and _pipboy_skin.is_applied


# =============================================================================
# SECTION 12: THEME DICTIONARY FOR COMPATIBILITY
# =============================================================================

# Theme dictionary for app.py compatibility
THEME = PIPBOY_THEME
