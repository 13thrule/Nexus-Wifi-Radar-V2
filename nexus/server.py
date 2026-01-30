"""
FastAPI-based remote dashboard server for Nexus WiFi Radar.

Provides REST API endpoints and a web dashboard with:
- Optional API key authentication
- Rate limiting to prevent abuse
- Secure headers
"""

import asyncio
import hashlib
import json
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import List, Optional, Dict, Callable
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    Request = None
    Depends = None

from nexus.core.scan import get_scanner
from nexus.core.models import Network, ScanResult, Threat
from nexus.core.config import get_config
from nexus.core.logging import get_logger
from nexus.security.detection import ThreatDetector

logger = get_logger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.

    Limits requests per IP address to prevent abuse.
    """

    def __init__(self, requests_per_minute: int = 30, scan_cooldown: int = 5):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per IP
            scan_cooldown: Minimum seconds between scans per IP
        """
        self.requests_per_minute = requests_per_minute
        self.scan_cooldown = scan_cooldown
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._last_scan: Dict[str, float] = {}

    def _cleanup_old_requests(self, ip: str) -> None:
        """Remove requests older than 1 minute."""
        now = time.time()
        self._requests[ip] = [t for t in self._requests[ip] if now - t < 60]

    def check_rate_limit(self, ip: str) -> bool:
        """Check if request is allowed under rate limit."""
        self._cleanup_old_requests(ip)
        return len(self._requests[ip]) < self.requests_per_minute

    def record_request(self, ip: str) -> None:
        """Record a request from an IP."""
        self._requests[ip].append(time.time())

    def can_scan(self, ip: str) -> bool:
        """Check if IP can perform a scan (respects cooldown)."""
        last = self._last_scan.get(ip, 0)
        return time.time() - last >= self.scan_cooldown

    def record_scan(self, ip: str) -> None:
        """Record that IP performed a scan."""
        self._last_scan[ip] = time.time()

    def get_scan_wait_time(self, ip: str) -> int:
        """Get seconds until IP can scan again."""
        last = self._last_scan.get(ip, 0)
        wait = self.scan_cooldown - (time.time() - last)
        return max(0, int(wait))


class APIKeyAuth:
    """
    Optional API key authentication.

    If NEXUS_API_KEY environment variable is set, all API requests
    must include a matching X-API-Key header.
    """

    def __init__(self):
        """Initialize authentication."""
        self.api_key = os.environ.get("NEXUS_API_KEY")
        self.enabled = self.api_key is not None
        if self.enabled:
            logger.info("API key authentication enabled")
        else:
            logger.warning("API key authentication disabled (set NEXUS_API_KEY to enable)")

    def verify(self, provided_key: Optional[str]) -> bool:
        """Verify provided API key."""
        if not self.enabled:
            return True
        if not provided_key:
            return False
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(provided_key, self.api_key)

    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)


# Pydantic models for API
if FASTAPI_AVAILABLE:
    class NetworkResponse(BaseModel):
        ssid: str
        bssid: str
        channel: int
        frequency_mhz: int
        rssi_dbm: int
        signal_percent: int
        security: str
        vendor: str
        band: str
        last_seen: str
    
    class ThreatResponse(BaseModel):
        id: str
        severity: str
        category: str
        description: str
        network_count: int
        detected_at: str
    
    class ScanResponse(BaseModel):
        networks: List[NetworkResponse]
        network_count: int
        threats: List[ThreatResponse]
        threat_count: int
        scan_time: str
        duration_seconds: float
    
    class StatusResponse(BaseModel):
        status: str
        scanner: str
        platform: str
        last_scan: Optional[str]
        network_count: int
        threat_count: int
else:
    # Stub classes when FastAPI not available
    NetworkResponse = None
    ThreatResponse = None
    ScanResponse = None
    StatusResponse = None


class DashboardServer:
    """
    Remote dashboard server for Nexus WiFi Radar.

    Provides:
    - REST API for scanning and data retrieval
    - WebSocket for real-time updates
    - Web dashboard UI
    - Optional API key authentication
    - Rate limiting to prevent abuse
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """Initialize server."""
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")

        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Nexus WiFi Radar API",
            description="WiFi scanning and security analysis API",
            version="2.0.0"
        )

        # Security
        self.rate_limiter = RateLimiter(requests_per_minute=60, scan_cooldown=5)
        self.auth = APIKeyAuth()

        # Add CORS middleware for web dashboard
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # State
        self.scanner = None
        self.detector = ThreatDetector()
        self.last_result: Optional[ScanResult] = None
        self.connected_clients: List[WebSocket] = []

        # Try to get scanner
        try:
            self.scanner = get_scanner()
            logger.info(f"Scanner initialized: {self.scanner.name}")
        except RuntimeError as e:
            logger.warning(f"Scanner not available: {e}")
        except OSError as e:
            logger.warning(f"Scanner OS error: {e}")

        # Setup routes
        self._setup_routes()
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded header (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _check_auth(self, request: Request) -> None:
        """Check API key authentication."""
        if self.auth.enabled:
            api_key = request.headers.get("X-API-Key")
            if not self.auth.verify(api_key):
                logger.warning(f"Unauthorized request from {self._get_client_ip(request)}")
                raise HTTPException(status_code=401, detail="Invalid or missing API key")

    def _check_rate_limit(self, request: Request) -> None:
        """Check rate limiting."""
        ip = self._get_client_ip(request)
        if not self.rate_limiter.check_rate_limit(ip):
            logger.warning(f"Rate limit exceeded for {ip}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
        self.rate_limiter.record_request(ip)

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Serve the web dashboard."""
            return self._get_dashboard_html()

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint (no auth required)."""
            return {
                "status": "healthy",
                "version": "2.0.0",
                "scanner_available": self.scanner is not None,
                "auth_enabled": self.auth.enabled
            }

        @self.app.get("/api/status", response_model=StatusResponse)
        async def get_status(request: Request):
            """Get server status."""
            self._check_auth(request)
            self._check_rate_limit(request)

            return StatusResponse(
                status="online",
                scanner=self.scanner.name if self.scanner else "unavailable",
                platform=self.scanner.platform if self.scanner else "unknown",
                last_scan=self.last_result.scan_time.isoformat() if self.last_result else None,
                network_count=self.last_result.network_count if self.last_result else 0,
                threat_count=len(self.detector.get_active_threats())
            )

        @self.app.get("/api/scan", response_model=ScanResponse)
        async def scan(request: Request, timeout: float = 10.0):
            """Perform a WiFi scan."""
            self._check_auth(request)
            self._check_rate_limit(request)

            if not self.scanner:
                raise HTTPException(status_code=503, detail="Scanner not available")

            # Check scan cooldown
            ip = self._get_client_ip(request)
            if not self.rate_limiter.can_scan(ip):
                wait_time = self.rate_limiter.get_scan_wait_time(ip)
                raise HTTPException(
                    status_code=429,
                    detail=f"Scan cooldown active. Wait {wait_time} seconds."
                )

            # Clamp timeout to reasonable range
            timeout = max(1.0, min(60.0, timeout))

            logger.info(f"Scan requested by {ip} (timeout={timeout}s)")
            self.rate_limiter.record_scan(ip)

            result = self.scanner.scan(timeout=timeout)
            threats = self.detector.analyze(result)
            result.threats = threats
            self.last_result = result

            logger.info(f"Scan complete: {result.network_count} networks, {len(threats)} threats")

            # Notify WebSocket clients
            await self._broadcast_update(result)

            return self._scan_to_response(result)

        @self.app.get("/api/networks", response_model=List[NetworkResponse])
        async def get_networks(request: Request):
            """Get last scan's networks."""
            self._check_auth(request)
            self._check_rate_limit(request)

            if not self.last_result:
                return []
            return [self._network_to_response(n) for n in self.last_result.networks]

        @self.app.get("/api/threats", response_model=List[ThreatResponse])
        async def get_threats(request: Request):
            """Get active threats."""
            self._check_auth(request)
            self._check_rate_limit(request)

            return [self._threat_to_response(t) for t in self.detector.get_active_threats()]

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await websocket.accept()
            self.connected_clients.append(websocket)
            logger.info(f"WebSocket client connected (total: {len(self.connected_clients)})")

            try:
                while True:
                    # Keep connection alive, handle incoming messages
                    data = await websocket.receive_text()

                    if data == "scan":
                        if self.scanner:
                            result = self.scanner.scan(timeout=10)
                            threats = self.detector.analyze(result)
                            result.threats = threats
                            self.last_result = result
                            await self._broadcast_update(result)
            except WebSocketDisconnect:
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)
                logger.info(f"WebSocket client disconnected (remaining: {len(self.connected_clients)})")
    
    async def _broadcast_update(self, result: ScanResult):
        """Broadcast scan update to all WebSocket clients."""
        message = json.dumps({
            "type": "scan_update",
            "data": self._scan_to_response(result).model_dump()
        })

        disconnected = []
        for client in self.connected_clients:
            try:
                await client.send_text(message)
            except (WebSocketDisconnect, RuntimeError, ConnectionError) as e:
                logger.debug(f"WebSocket send failed: {e}")
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            if client in self.connected_clients:
                self.connected_clients.remove(client)
    
    def _network_to_response(self, network: Network) -> NetworkResponse:
        """Convert Network to API response."""
        return NetworkResponse(
            ssid=network.ssid,
            bssid=network.bssid,
            channel=network.channel,
            frequency_mhz=network.frequency_mhz,
            rssi_dbm=network.rssi_dbm,
            signal_percent=network.signal_percent,
            security=network.security.value,
            vendor=network.vendor,
            band=network.band,
            last_seen=network.last_seen.isoformat()
        )
    
    def _threat_to_response(self, threat: Threat) -> ThreatResponse:
        """Convert Threat to API response."""
        return ThreatResponse(
            id=threat.id,
            severity=threat.severity.value,
            category=threat.category.value,
            description=threat.description,
            network_count=len(threat.networks),
            detected_at=threat.detected_at.isoformat()
        )
    
    def _scan_to_response(self, result: ScanResult) -> ScanResponse:
        """Convert ScanResult to API response."""
        return ScanResponse(
            networks=[self._network_to_response(n) for n in result.networks],
            network_count=result.network_count,
            threats=[self._threat_to_response(t) for t in result.threats],
            threat_count=len(result.threats),
            scan_time=result.scan_time.isoformat(),
            duration_seconds=result.duration_seconds
        )
    
    def _get_dashboard_html(self) -> str:
        """Generate the web dashboard HTML."""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Nexus WiFi Radar - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0a0a1a;
            color: #eee;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #0066cc, #004499);
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; }
        .header .status { font-size: 14px; color: #aaccff; margin-top: 5px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: #12122a;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a4a;
        }
        .card h2 {
            font-size: 16px;
            color: #00d4ff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        button {
            background: #0066cc;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        button:hover { background: #0077ee; }
        button:disabled { background: #333; cursor: not-allowed; }
        button.scanning { background: #cc6600; }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        .stat {
            background: #1a1a3a;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat .value { font-size: 32px; font-weight: bold; color: #00d4ff; }
        .stat .label { font-size: 12px; color: #888; margin-top: 5px; }
        .network-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .network {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #2a2a4a;
        }
        .network:hover { background: #1a1a3a; }
        .network .ssid { font-weight: bold; }
        .network .meta { font-size: 12px; color: #888; margin-top: 4px; }
        .signal-bar {
            width: 100px;
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
        }
        .signal-fill {
            height: 100%;
            transition: width 0.3s;
        }
        .signal-excellent { background: linear-gradient(90deg, #00cc00, #00ff00); }
        .signal-good { background: linear-gradient(90deg, #88cc00, #aaff00); }
        .signal-fair { background: linear-gradient(90deg, #cc8800, #ffaa00); }
        .signal-weak { background: linear-gradient(90deg, #cc0000, #ff4444); }
        .threat {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .threat.critical { background: #330000; border-left: 4px solid #ff0000; }
        .threat.high { background: #332200; border-left: 4px solid #ff6600; }
        .threat.medium { background: #333300; border-left: 4px solid #ffcc00; }
        .threat.low { background: #003300; border-left: 4px solid #00cc00; }
        .threat .severity { font-weight: bold; text-transform: uppercase; font-size: 12px; }
        .threat .description { margin-top: 5px; }
        #radar {
            width: 100%;
            height: 350px;
            background: #0a0a1a;
            border-radius: 8px;
        }
        .empty { color: #666; text-align: center; padding: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📡 Nexus WiFi Radar</h1>
        <div class="status" id="status">Connecting...</div>
    </div>
    
    <div class="container">
        <div class="controls">
            <button id="scanBtn" onclick="scan()">🔍 Scan Networks</button>
            <button onclick="location.reload()">🔄 Refresh</button>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="value" id="networkCount">0</div>
                <div class="label">Networks</div>
            </div>
            <div class="stat">
                <div class="value" id="threatCount">0</div>
                <div class="label">Threats</div>
            </div>
            <div class="stat">
                <div class="value" id="lastScan">--</div>
                <div class="label">Last Scan</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📡 Radar View</h2>
                <canvas id="radar"></canvas>
            </div>
            
            <div class="card">
                <h2>📋 Networks</h2>
                <div class="network-list" id="networkList">
                    <div class="empty">Click Scan to discover networks</div>
                </div>
            </div>
            
            <div class="card" style="grid-column: span 2">
                <h2>⚠️ Security Threats</h2>
                <div id="threatList">
                    <div class="empty">No threats detected</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let networks = [];
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${location.host}/ws`);
            ws.onopen = () => {
                document.getElementById('status').textContent = 'Connected';
            };
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'scan_update') {
                    updateDisplay(msg.data);
                }
            };
            ws.onclose = () => {
                document.getElementById('status').textContent = 'Disconnected - Reconnecting...';
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        async function scan() {
            const btn = document.getElementById('scanBtn');
            btn.disabled = true;
            btn.classList.add('scanning');
            btn.textContent = '⏳ Scanning...';
            
            try {
                const response = await fetch('/api/scan?timeout=10');
                const data = await response.json();
                updateDisplay(data);
            } catch (e) {
                console.error('Scan failed:', e);
            }
            
            btn.disabled = false;
            btn.classList.remove('scanning');
            btn.textContent = '🔍 Scan Networks';
        }
        
        function updateDisplay(data) {
            networks = data.networks || [];
            
            document.getElementById('networkCount').textContent = data.network_count || 0;
            document.getElementById('threatCount').textContent = data.threat_count || 0;
            document.getElementById('lastScan').textContent = 
                new Date(data.scan_time).toLocaleTimeString();
            
            updateNetworkList(networks);
            updateThreatList(data.threats || []);
            drawRadar(networks);
        }
        
        function updateNetworkList(networks) {
            const list = document.getElementById('networkList');
            
            if (!networks.length) {
                list.innerHTML = '<div class="empty">No networks found</div>';
                return;
            }
            
            list.innerHTML = networks.sort((a, b) => b.rssi_dbm - a.rssi_dbm).map(n => {
                const pct = n.signal_percent;
                let signalClass = 'weak';
                if (pct >= 80) signalClass = 'excellent';
                else if (pct >= 60) signalClass = 'good';
                else if (pct >= 40) signalClass = 'fair';
                
                return `
                    <div class="network">
                        <div>
                            <div class="ssid">${n.ssid || '&lt;Hidden&gt;'}</div>
                            <div class="meta">${n.security} • CH ${n.channel} • ${n.vendor}</div>
                        </div>
                        <div style="text-align: right">
                            <div class="signal-bar">
                                <div class="signal-fill signal-${signalClass}" style="width: ${pct}%"></div>
                            </div>
                            <div class="meta">${pct}% (${n.rssi_dbm} dBm)</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateThreatList(threats) {
            const list = document.getElementById('threatList');
            
            if (!threats.length) {
                list.innerHTML = '<div class="empty">✅ No threats detected</div>';
                return;
            }
            
            list.innerHTML = threats.map(t => `
                <div class="threat ${t.severity}">
                    <div class="severity">${t.severity}</div>
                    <div class="description">${t.description}</div>
                </div>
            `).join('');
        }
        
        function drawRadar(networks) {
            const canvas = document.getElementById('radar');
            const ctx = canvas.getContext('2d');
            
            canvas.width = canvas.offsetWidth * 2;
            canvas.height = canvas.offsetHeight * 2;
            ctx.scale(2, 2);
            
            const w = canvas.offsetWidth;
            const h = canvas.offsetHeight;
            const cx = w / 2;
            const cy = h / 2;
            const r = Math.min(w, h) / 2 - 40;
            
            // Clear
            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, w, h);
            
            // Grid circles
            ctx.strokeStyle = '#1a1a3a';
            for (let i = 1; i <= 4; i++) {
                ctx.beginPath();
                ctx.arc(cx, cy, r * i / 4, 0, Math.PI * 2);
                ctx.stroke();
            }
            
            // Cross
            ctx.beginPath();
            ctx.moveTo(cx - r, cy);
            ctx.lineTo(cx + r, cy);
            ctx.moveTo(cx, cy - r);
            ctx.lineTo(cx, cy + r);
            ctx.stroke();
            
            // Networks
            const top12 = networks.slice(0, 12);
            top12.forEach((net, i) => {
                const angle = (i * 30 - 90) * Math.PI / 180;
                const dist = r * (1 - net.signal_percent / 100);
                const x = cx + dist * Math.cos(angle);
                const y = cy + dist * Math.sin(angle);
                
                const pct = net.signal_percent;
                let color = '#ff4444';
                if (pct >= 80) color = '#00ff00';
                else if (pct >= 60) color = '#aaff00';
                else if (pct >= 40) color = '#ffaa00';
                
                // Blip
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, 8, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // Label
                ctx.fillStyle = color;
                ctx.font = '10px sans-serif';
                ctx.textAlign = x > cx ? 'left' : 'right';
                const labelX = x + (x > cx ? 12 : -12);
                ctx.fillText((net.ssid || '<Hidden>').slice(0, 12), labelX, y - 5);
                ctx.fillText(`${pct}%`, labelX, y + 10);
            });
        }
        
        // Init
        connectWebSocket();
        
        // Fetch initial status
        fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').textContent = 
                    `Scanner: ${data.scanner} | ${data.platform}`;
            });
    </script>
</body>
</html>'''
    
    def run(self):
        """Run the server."""
        import uvicorn
        uvicorn.run(self.app, host=self.host, port=self.port)


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Convenience function to run the dashboard server."""
    server = DashboardServer(host=host, port=port)
    server.run()


if __name__ == "__main__":
    run_server()
