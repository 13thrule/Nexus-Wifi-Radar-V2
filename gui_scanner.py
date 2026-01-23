#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, math, subprocess, re
from datetime import datetime
from collections import defaultdict

from scapy.all import sniff, Dot11Beacon, Dot11ProbeResp

class WiFiScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("WiFi Signal Scanner - Scapy")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e1e")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.networks = {}
        self.signal_data = defaultdict(list)
        self.is_scanning = False
        self.scan_count = 0
        
        header = tk.Frame(self.root, bg="#0066cc", height=50)
        header.pack(fill="x")
        tk.Label(header, text="📡 WiFi Signal Scanner - All Networks", font=("Arial", 16, "bold"), 
                fg="white", bg="#0066cc").pack(pady=10)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Radar tab
        radar_frame = ttk.Frame(self.notebook)
        self.notebook.add(radar_frame, text="Radar")
        self.radar_canvas = tk.Canvas(radar_frame, bg="#1a1a1a", highlightthickness=0)
        self.radar_canvas.pack(fill="both", expand=True)
        
        # List tab
        list_frame = ttk.Frame(self.notebook)
        self.notebook.add(list_frame, text="Networks")
        cols = ("Network", "Signal", "Channel")
        self.tree = ttk.Treeview(list_frame, columns=cols, height=20, show="headings")
        for col, w in zip(cols, [400, 80, 80]):
            self.tree.column(col, width=w)
            self.tree.heading(col, text=col)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        # Controls
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill="x", padx=10, pady=5)
        ttk.Button(ctrl, text="🚀 Scan (30s)", command=self.start_scan).pack(side="left", padx=5)
        self.btn_stop = ttk.Button(ctrl, text="⏹️ Stop", command=self.stop_scan, state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        ttk.Button(ctrl, text="💾 Export CSV", command=self.export_csv).pack(side="left", padx=5)
        
        # Status
        status = ttk.LabelFrame(self.root, text="Status", padding=10)
        status.pack(fill="x", padx=10, pady=5)
        self.status_label = tk.Label(status, text="Ready. Click Scan to find all WiFi networks.", font=("Arial", 10), fg="#00ff00")
        self.status_label.pack(anchor="w")
        self.stats_label = tk.Label(status, text="Networks: 0 | Scans: 0", font=("Arial", 9), fg="#aaa")
        self.stats_label.pack(anchor="w", pady=5)
    
    def packet_handler(self, packet):
        if not self.is_scanning:
            return
        
        if packet.haslayer(Dot11Beacon):
            bssid = packet[Dot11Beacon].bssid
            ssid = packet[Dot11Beacon].info.decode('utf-8', errors='ignore')
            channel = int(packet[Dot11Beacon].ch) if hasattr(packet[Dot11Beacon], 'ch') else 0
            
            if ssid:
                signal = -(256 - packet.dBm_AntSignal) if hasattr(packet, 'dBm_AntSignal') else 50
                signal = max(0, min(100, int((signal + 100) * 1.25)))
                
                if ssid not in self.networks:
                    self.networks[ssid] = {'signal': signal, 'channel': channel, 'bssid': bssid}
                else:
                    self.networks[ssid]['signal'] = max(self.networks[ssid]['signal'], signal)
                    self.networks[ssid]['channel'] = channel
    
    def start_scan(self):
        def scan():
            self.is_scanning = True
            self.btn_stop.config(state="normal")
            self.networks.clear()
            
            self.status_label.config(text="🔍 Scanning for all WiFi networks... (30 seconds)", fg="#00ccff")
            self.root.update()
            
            try:
                sniff(prn=self.packet_handler, timeout=30, store=False)
            except Exception as e:
                self.status_label.config(text=f"Error: Install Npcap from npcap.com first!", fg="#ff6b6b")
            
            if self.networks:
                self.update_display()
                self.scan_count += 1
                self.status_label.config(text=f"✅ Found {len(self.networks)} networks!", fg="#00ff00")
            else:
                self.status_label.config(text="⚠️ No networks. Need Npcap: npcap.com/download", fg="#ffff00")
            
            self.btn_stop.config(state="disabled")
            self.is_scanning = False
        
        threading.Thread(target=scan, daemon=True).start()
    
    def stop_scan(self):
        self.is_scanning = False
        self.status_label.config(text="Scan stopped", fg="#ffff00")
        self.btn_stop.config(state="disabled")
    
    def update_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for ssid, data in sorted(self.networks.items(), key=lambda x: x[1]['signal'], reverse=True):
            self.signal_data[ssid].append({'signal': data['signal'], 'channel': data['channel'], 'time': datetime.now()})
            
            if data['signal'] >= 80:
                tags = ("excellent",)
            elif data['signal'] >= 60:
                tags = ("good",)
            elif data['signal'] >= 40:
                tags = ("fair",)
            else:
                tags = ("weak",)
            
            self.tree.insert("", "end", values=(ssid[:50], f"{data['signal']}%", f"CH {data['channel']}"), tags=tags)
        
        self.tree.tag_configure("excellent", foreground="#00ff00")
        self.tree.tag_configure("good", foreground="#ffff00")
        self.tree.tag_configure("fair", foreground="#ff9900")
        self.tree.tag_configure("weak", foreground="#ff6b6b")
        
        self.draw_radar()
        self.stats_label.config(text=f"Networks: {len(self.networks)} | Scans: {self.scan_count}")
    
    def draw_radar(self):
        self.radar_canvas.delete("all")
        w = self.radar_canvas.winfo_width()
        h = self.radar_canvas.winfo_height()
        
        if w < 2: w = 400
        if h < 2: h = 300
        
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 40
        
        for dist in [100, 75, 50, 25]:
            self.radar_canvas.create_oval(cx - r*dist/100, cy - r*dist/100,
                                         cx + r*dist/100, cy + r*dist/100,
                                         outline="#333", width=1)
        
        for i, (ssid, data) in enumerate(list(self.networks.items())[:12]):
            sig = data['signal']
            angle = (i * 30 - 90) * 3.14159 / 180
            dist = r * (sig / 100)
            x = cx + dist * math.cos(angle)
            y = cy + dist * math.sin(angle)
            
            color = "#00ff00" if sig >= 80 else "#ffff00" if sig >= 60 else "#ff9900" if sig >= 40 else "#ff6b6b"
            self.radar_canvas.create_oval(x-8, y-8, x+8, y+8, fill=color, outline="white", width=2)
            self.radar_canvas.create_text(x+20, y, text=f"{ssid[:15]}\n{sig}%", fill=color, font=("Arial", 7))
    
    def export_csv(self):
        if not self.signal_data:
            messagebox.showwarning("No Data", "No scan data to export")
            return
        
        filename = f"wifi_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, 'w') as f:
                f.write("SSID,Signal(%),Channel,Time\n")
                for ssid, readings in self.signal_data.items():
                    for r in readings:
                        f.write(f"{ssid},{r['signal']},{r['channel']},{r['time']}\n")
            messagebox.showinfo("Success", f"Exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def on_close(self):
        self.is_scanning = False
        time.sleep(0.2)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WiFiScanner(root)
    root.mainloop()
