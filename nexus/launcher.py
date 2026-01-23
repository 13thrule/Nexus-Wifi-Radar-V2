"""
NEXUS WiFi Radar - Launcher

███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝

A modern launcher for the NEXUS WiFi Intelligence Platform.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Callable


# ASCII Art Logo
NEXUS_LOGO = """
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""

NEXUS_SUBTITLE = "W I F I   R A D A R   v 2 . 0"


class NexusLauncher:
    """
    NEXUS Launcher - Main entry point for the NEXUS platform.
    
    Features:
    - Animated boot sequence
    - Quick-launch buttons for all modules
    - System status display
    - Plugin manager
    - Theme selection
    """
    
    def __init__(self):
        """Initialize the launcher."""
        self.root = tk.Tk()
        self.root.title("NEXUS // LAUNCHER")
        self.root.geometry("900x700")
        self.root.configure(bg="#000000")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 900) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"900x700+{x}+{y}")
        
        # State
        self.boot_complete = False
        self.selected_module = None
        self.animation_running = True
        self.scanline_offset = 0
        
        # Theme
        self.theme = {
            "bg": "#000000",
            "bg_panel": "#0a0e1a",
            "accent": "#00ff88",
            "accent2": "#00ffff",
            "accent3": "#ff00ff",
            "text": "#00ff00",
            "text_dim": "#006600",
            "warning": "#ffff00",
            "error": "#ff0000",
            "border": "#00ff88"
        }
        
        # System info (detected during boot)
        self.system_info = {
            "os": platform.system(),
            "os_version": platform.version()[:30],
            "python": platform.python_version(),
            "scanner": "Detecting...",
            "scapy": "Checking...",
            "easm": "Checking..."
        }
        
        # Build UI
        self._build_ui()
        
        # Start boot sequence
        self.root.after(100, self._run_boot_sequence)
    
    def _build_ui(self):
        """Build the launcher UI."""
        # Main canvas for effects
        self.main_canvas = tk.Canvas(
            self.root, 
            bg=self.theme["bg"], 
            highlightthickness=0,
            width=900, 
            height=700
        )
        self.main_canvas.pack(fill="both", expand=True)
        
        # Logo display (initially hidden, revealed during boot)
        self.logo_frame = tk.Frame(self.main_canvas, bg=self.theme["bg"])
        self.logo_label = tk.Label(
            self.logo_frame,
            text=NEXUS_LOGO,
            font=("Courier New", 10, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg"],
            justify="center"
        )
        self.logo_label.pack()
        
        self.subtitle_label = tk.Label(
            self.logo_frame,
            text=NEXUS_SUBTITLE,
            font=("Courier New", 14, "bold"),
            fg=self.theme["accent2"],
            bg=self.theme["bg"]
        )
        self.subtitle_label.pack(pady=5)
        
        # Boot status label
        self.boot_status = tk.Label(
            self.logo_frame,
            text="INITIALIZING SYSTEMS...",
            font=("Courier New", 10),
            fg=self.theme["text_dim"],
            bg=self.theme["bg"]
        )
        self.boot_status.pack(pady=10)
        
        # Progress bar frame
        self.progress_frame = tk.Frame(self.logo_frame, bg=self.theme["bg"])
        self.progress_frame.pack(pady=5)
        
        self.progress_bar = tk.Canvas(
            self.progress_frame,
            width=400,
            height=20,
            bg=self.theme["bg_panel"],
            highlightthickness=1,
            highlightbackground=self.theme["border"]
        )
        self.progress_bar.pack()
        
        # Place logo frame in center
        self.main_canvas.create_window(450, 250, window=self.logo_frame, anchor="center")
        
        # Main menu frame (hidden until boot complete)
        self.menu_frame = tk.Frame(self.main_canvas, bg=self.theme["bg"])
        
        # Status panel (bottom)
        self.status_frame = tk.Frame(self.main_canvas, bg=self.theme["bg_panel"])
    
    def _run_boot_sequence(self):
        """Run the animated boot sequence."""
        boot_steps = [
            ("Initializing core systems...", 0.1),
            ("Loading configuration...", 0.2),
            ("Detecting platform...", 0.3),
            ("Checking scanner backend...", 0.5),
            ("Initializing intelligence engines...", 0.6),
            ("Loading OUI database...", 0.7),
            ("Checking Scapy availability...", 0.8),
            ("Finalizing boot sequence...", 0.95),
            ("NEXUS READY", 1.0)
        ]
        
        def boot_step(index):
            if index >= len(boot_steps):
                self._boot_complete()
                return
            
            msg, progress = boot_steps[index]
            self.boot_status.config(text=f"[BOOT] {msg}")
            
            # Update progress bar
            self.progress_bar.delete("progress")
            bar_width = int(400 * progress)
            self.progress_bar.create_rectangle(
                0, 0, bar_width, 20,
                fill=self.theme["accent"],
                tags="progress"
            )
            
            # Detect system info during boot
            if index == 2:
                self._detect_platform()
            elif index == 3:
                self._detect_scanner()
            elif index == 6:
                self._detect_scapy()
            
            # Next step
            delay = 200 if index < len(boot_steps) - 1 else 500
            self.root.after(delay, lambda: boot_step(index + 1))
        
        boot_step(0)
    
    def _detect_platform(self):
        """Detect platform info."""
        self.system_info["os"] = platform.system()
        self.system_info["os_version"] = platform.version()[:40]
    
    def _detect_scanner(self):
        """Detect scanner backend."""
        try:
            from nexus.core.scan import get_scanner
            scanner = get_scanner()
            self.system_info["scanner"] = scanner.name
        except Exception as e:
            self.system_info["scanner"] = f"Error: {str(e)[:20]}"
    
    def _detect_scapy(self):
        """Detect Scapy availability."""
        try:
            import scapy
            self.system_info["scapy"] = f"v{scapy.__version__}"
            
            # Check EASM based on platform
            if platform.system() == "Windows":
                self.system_info["easm"] = "Disabled (Windows)"
            else:
                self.system_info["easm"] = "Available"
        except ImportError:
            self.system_info["scapy"] = "Not installed"
            self.system_info["easm"] = "Unavailable"
    
    def _boot_complete(self):
        """Called when boot sequence completes."""
        self.boot_complete = True
        self.boot_status.config(text="[READY] Select a module to launch", fg=self.theme["accent"])
        
        # Hide progress bar
        self.progress_frame.pack_forget()
        
        # Build and show main menu
        self._build_main_menu()
        
        # Start scanline animation
        self._animate_scanlines()
    
    def _build_main_menu(self):
        """Build the main launcher menu."""
        # Clear logo frame and rebuild with menu
        for widget in self.logo_frame.winfo_children():
            if widget not in [self.logo_label, self.subtitle_label, self.boot_status]:
                widget.destroy()
        
        # Module buttons frame
        buttons_frame = tk.Frame(self.logo_frame, bg=self.theme["bg"])
        buttons_frame.pack(pady=20)
        
        # Define modules
        modules = [
            ("🎯 RADAR", "Launch main radar GUI", self._launch_radar, self.theme["accent"]),
            ("🧠 INTELLIGENCE", "Intelligence dashboard", self._launch_intelligence, self.theme["accent2"]),
            ("📡 CLI SCAN", "Command-line scan", self._launch_cli, self.theme["accent3"]),
            ("🌐 DASHBOARD", "Web dashboard server", self._launch_server, "#ff8800"),
            ("⚙️ SETTINGS", "Configuration manager", self._launch_settings, "#ffff00"),
            ("📋 LOGS", "View event logs", self._launch_logs, "#888888"),
        ]
        
        # Create 2x3 grid of buttons
        for i, (text, tooltip, command, color) in enumerate(modules):
            row, col = divmod(i, 3)
            
            btn = tk.Button(
                buttons_frame,
                text=text,
                font=("Courier New", 12, "bold"),
                fg="#000000",
                bg=color,
                activebackground=self._lighten_color(color),
                activeforeground="#000000",
                relief="raised",
                bd=3,
                width=14,
                height=2,
                cursor="hand2",
                command=command
            )
            btn.grid(row=row, column=col, padx=10, pady=10)
            
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=self._lighten_color(c)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
        
        # System status panel
        status_frame = tk.LabelFrame(
            self.logo_frame,
            text="SYSTEM STATUS",
            font=("Courier New", 9, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg_panel"],
            bd=2
        )
        status_frame.pack(pady=15, padx=20, fill="x")
        
        # Status grid
        status_items = [
            ("OS", self.system_info["os"]),
            ("Python", self.system_info["python"]),
            ("Scanner", self.system_info["scanner"]),
            ("Scapy", self.system_info["scapy"]),
            ("EASM", self.system_info["easm"]),
        ]
        
        for i, (label, value) in enumerate(status_items):
            lbl = tk.Label(
                status_frame,
                text=f"{label}:",
                font=("Courier New", 9),
                fg=self.theme["text_dim"],
                bg=self.theme["bg_panel"],
                anchor="e",
                width=10
            )
            lbl.grid(row=i // 3, column=(i % 3) * 2, padx=5, pady=2, sticky="e")
            
            # Color based on value
            if "Error" in value or "Not" in value or "Disabled" in value:
                val_color = self.theme["warning"]
            elif "Available" in value or "v" in value:
                val_color = self.theme["accent"]
            else:
                val_color = self.theme["text"]
            
            val = tk.Label(
                status_frame,
                text=value[:20],
                font=("Courier New", 9, "bold"),
                fg=val_color,
                bg=self.theme["bg_panel"],
                anchor="w",
                width=18
            )
            val.grid(row=i // 3, column=(i % 3) * 2 + 1, padx=5, pady=2, sticky="w")
        
        # Footer
        footer = tk.Label(
            self.logo_frame,
            text="═" * 60 + "\n[ ESC to exit | T to toggle theme | ? for help ]",
            font=("Courier New", 8),
            fg=self.theme["text_dim"],
            bg=self.theme["bg"]
        )
        footer.pack(pady=10)
        
        # Bind keys
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("t", lambda e: self._toggle_theme())
        self.root.bind("T", lambda e: self._toggle_theme())
        self.root.bind("?", lambda e: self._show_help())
        self.root.bind("<F1>", lambda e: self._show_help())
    
    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color."""
        # Simple lighten - add to each channel
        r = min(255, int(hex_color[1:3], 16) + 40)
        g = min(255, int(hex_color[3:5], 16) + 40)
        b = min(255, int(hex_color[5:7], 16) + 40)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _animate_scanlines(self):
        """Animate CRT scanlines effect."""
        if not self.animation_running:
            return
        
        # Draw subtle scanlines
        self.main_canvas.delete("scanline")
        
        for y in range(0, 700, 4):
            adjusted_y = (y + self.scanline_offset) % 700
            alpha = 0.03 if adjusted_y % 8 == 0 else 0.01
            self.main_canvas.create_line(
                0, adjusted_y, 900, adjusted_y,
                fill="#002200",
                tags="scanline"
            )
        
        self.scanline_offset = (self.scanline_offset + 1) % 8
        
        # Continue animation
        self.root.after(100, self._animate_scanlines)
    
    def _launch_radar(self):
        """Launch the main radar GUI."""
        self.boot_status.config(text="[LAUNCHING] Radar GUI...", fg=self.theme["accent2"])
        self.root.update()
        
        # Hide launcher and start radar
        self.root.withdraw()
        
        try:
            from nexus.app import NexusApp
            app = NexusApp()
            
            # When radar closes, show launcher again
            def on_radar_close():
                app.root.destroy()
                self.root.deiconify()
                self.boot_status.config(text="[READY] Select a module to launch", fg=self.theme["accent"])
            
            app.root.protocol("WM_DELETE_WINDOW", on_radar_close)
            app.run()
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Launch Error", f"Failed to launch Radar:\n{e}")
            self.boot_status.config(text="[ERROR] Launch failed", fg=self.theme["error"])
    
    def _launch_intelligence(self):
        """Launch intelligence dashboard directly."""
        self.boot_status.config(text="[LAUNCHING] Intelligence Core...", fg=self.theme["accent2"])
        self._launch_radar()  # For now, launches radar with intel tab focused
    
    def _launch_cli(self):
        """Launch CLI scan in new terminal."""
        self.boot_status.config(text="[LAUNCHING] CLI Scan...", fg=self.theme["accent2"])
        
        try:
            if platform.system() == "Windows":
                # Open new PowerShell window with scan command
                cmd = 'start powershell -NoExit -Command "cd \'{}\'; .\\venv\\Scripts\\python.exe -m nexus scan --weak -v"'.format(
                    Path(__file__).parent.parent
                )
                subprocess.Popen(cmd, shell=True)
            else:
                # Linux/Mac
                subprocess.Popen(["python3", "-m", "nexus", "scan", "--weak", "-v"])
            
            self.boot_status.config(text="[READY] CLI launched in new terminal", fg=self.theme["accent"])
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch CLI:\n{e}")
    
    def _launch_server(self):
        """Launch web dashboard server."""
        self.boot_status.config(text="[LAUNCHING] Web Dashboard...", fg=self.theme["accent2"])
        
        try:
            if platform.system() == "Windows":
                cmd = 'start powershell -NoExit -Command "cd \'{}\'; .\\venv\\Scripts\\python.exe -m nexus server --port 8080"'.format(
                    Path(__file__).parent.parent
                )
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen(["python3", "-m", "nexus", "server", "--port", "8080"])
            
            self.boot_status.config(text="[READY] Dashboard at http://localhost:8080", fg=self.theme["accent"])
            
            # Open browser after short delay
            self.root.after(2000, lambda: self._open_browser("http://localhost:8080"))
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch server:\n{e}")
    
    def _open_browser(self, url: str):
        """Open URL in default browser."""
        import webbrowser
        webbrowser.open(url)
    
    def _launch_settings(self):
        """Launch settings dialog."""
        self.boot_status.config(text="[SETTINGS] Opening configuration...", fg=self.theme["accent2"])
        
        # Create settings window
        settings_win = tk.Toplevel(self.root)
        settings_win.title("NEXUS // SETTINGS")
        settings_win.geometry("500x400")
        settings_win.configure(bg=self.theme["bg"])
        settings_win.transient(self.root)
        
        # Settings content
        tk.Label(
            settings_win,
            text="⚙️ NEXUS CONFIGURATION",
            font=("Courier New", 14, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg"]
        ).pack(pady=20)
        
        # Load current config
        try:
            from nexus.core.config import get_config
            config = get_config()
            
            settings_text = tk.Text(
                settings_win,
                font=("Courier New", 9),
                fg=self.theme["text"],
                bg=self.theme["bg_panel"],
                height=15,
                width=50
            )
            settings_text.pack(padx=20, pady=10, fill="both", expand=True)
            
            # Display config
            settings_text.insert("end", f"Scan Timeout: {config.scan.timeout_seconds}s\n")
            settings_text.insert("end", f"Extended Timeout: {getattr(config.scan, 'extended_timeout_seconds', 30)}s\n")
            settings_text.insert("end", f"Use Scapy: {config.scan.use_scapy}\n")
            settings_text.insert("end", f"Audio Enabled: {config.audio.enabled}\n")
            settings_text.insert("end", f"Theme: {config.ui.theme}\n")
            settings_text.config(state="disabled")
            
        except Exception as e:
            tk.Label(
                settings_win,
                text=f"Error loading config:\n{e}",
                fg=self.theme["error"],
                bg=self.theme["bg"]
            ).pack()
        
        tk.Button(
            settings_win,
            text="Close",
            command=settings_win.destroy,
            bg=self.theme["accent"],
            fg="#000000"
        ).pack(pady=10)
        
        self.boot_status.config(text="[READY] Select a module to launch", fg=self.theme["accent"])
    
    def _launch_logs(self):
        """View event logs."""
        self.boot_status.config(text="[LOGS] Opening log viewer...", fg=self.theme["accent2"])
        
        # Create logs window
        logs_win = tk.Toplevel(self.root)
        logs_win.title("NEXUS // EVENT LOGS")
        logs_win.geometry("700x500")
        logs_win.configure(bg=self.theme["bg"])
        logs_win.transient(self.root)
        
        tk.Label(
            logs_win,
            text="📋 EVENT LOGS",
            font=("Courier New", 14, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg"]
        ).pack(pady=10)
        
        # Log text area
        log_text = tk.Text(
            logs_win,
            font=("Courier New", 9),
            fg=self.theme["text"],
            bg=self.theme["bg_panel"],
            height=20
        )
        log_text.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Try to load recent logs
        log_text.insert("end", "=== NEXUS Event Log ===\n\n")
        log_text.insert("end", f"Session started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_text.insert("end", f"Platform: {self.system_info['os']}\n")
        log_text.insert("end", f"Scanner: {self.system_info['scanner']}\n")
        log_text.insert("end", f"Scapy: {self.system_info['scapy']}\n")
        log_text.insert("end", f"EASM: {self.system_info['easm']}\n")
        log_text.insert("end", "\n[No historical logs available yet]\n")
        log_text.config(state="disabled")
        
        tk.Button(
            logs_win,
            text="Close",
            command=logs_win.destroy,
            bg=self.theme["accent"],
            fg="#000000"
        ).pack(pady=10)
        
        self.boot_status.config(text="[READY] Select a module to launch", fg=self.theme["accent"])
    
    def _toggle_theme(self):
        """Toggle between themes."""
        # Toggle between green and cyan accent
        if self.theme["accent"] == "#00ff88":
            self.theme["accent"] = "#00ffff"
            self.theme["text"] = "#00ffff"
            self.theme["text_dim"] = "#006666"
            self.logo_label.config(fg="#00ffff")
        else:
            self.theme["accent"] = "#00ff88"
            self.theme["text"] = "#00ff00"
            self.theme["text_dim"] = "#006600"
            self.logo_label.config(fg="#00ff88")
        
        self.boot_status.config(text="[THEME] Color scheme updated", fg=self.theme["accent"])
    
    def _show_help(self):
        """Show help dialog."""
        help_text = """
NEXUS WiFi Radar - Launcher Help

MODULES:
  🎯 RADAR       - Main WiFi radar visualization
  🧠 INTELLIGENCE - PIC intelligence dashboard
  📡 CLI SCAN    - Command-line scanning
  🌐 DASHBOARD   - Web-based remote monitoring
  ⚙️ SETTINGS    - Configuration manager
  📋 LOGS        - Event log viewer

KEYBOARD SHORTCUTS:
  ESC  - Exit launcher
  T    - Toggle color theme
  F1/? - Show this help

NOTES:
  - EASM is only available on Linux/Raspberry Pi
  - Extended scan mode improves weak signal detection
  - Web dashboard requires FastAPI (pip install fastapi uvicorn)
"""
        messagebox.showinfo("NEXUS Help", help_text)
    
    def run(self):
        """Run the launcher."""
        self.root.mainloop()
    
    def _on_close(self):
        """Handle window close."""
        self.animation_running = False
        self.root.destroy()


def main():
    """Main entry point for launcher."""
    launcher = NexusLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
