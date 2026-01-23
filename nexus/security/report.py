"""
Report generation for security analysis.

Generates reports in various formats (JSON, HTML, CSV).
"""

import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from nexus.core.models import ScanResult, Threat, ThreatSeverity


class ReportGenerator:
    """
    Generates security reports from scan results and threats.
    
    Supports multiple output formats:
    - JSON: Machine-readable, for automation
    - HTML: Human-readable, for viewing in browser
    - CSV: Spreadsheet-compatible
    """
    
    def __init__(self):
        """Initialize report generator."""
        pass
    
    def generate_json(
        self,
        scan_result: ScanResult,
        threats: List[Threat],
        include_networks: bool = True
    ) -> str:
        """
        Generate JSON report.
        
        Args:
            scan_result: Scan result data
            threats: List of detected threats
            include_networks: Whether to include full network list
            
        Returns:
            JSON string
        """
        report = {
            "report_time": datetime.now().isoformat(),
            "scan_time": scan_result.scan_time.isoformat(),
            "scan_duration_seconds": scan_result.duration_seconds,
            "scanner": scan_result.scanner_type,
            "platform": scan_result.platform,
            "summary": {
                "total_networks": scan_result.network_count,
                "total_threats": len(threats),
                "threats_by_severity": self._count_by_severity(threats),
            },
            "threats": [t.to_dict() for t in threats],
        }
        
        if include_networks:
            report["networks"] = [n.to_dict() for n in scan_result.networks]
        
        return json.dumps(report, indent=2)
    
    def generate_html(
        self,
        scan_result: ScanResult,
        threats: List[Threat],
        title: str = "WiFi Security Report"
    ) -> str:
        """
        Generate HTML report.
        
        Args:
            scan_result: Scan result data
            threats: List of detected threats
            title: Report title
            
        Returns:
            HTML string
        """
        severity_colors = {
            ThreatSeverity.CRITICAL: "#ff0000",
            ThreatSeverity.HIGH: "#ff6600",
            ThreatSeverity.MEDIUM: "#ffcc00",
            ThreatSeverity.LOW: "#00cc00",
        }
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            margin: 0;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #00d4ff; }}
        h2 {{ color: #00a8cc; border-bottom: 1px solid #333; padding-bottom: 10px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .card {{
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .card .number {{ font-size: 48px; font-weight: bold; }}
        .card .label {{ color: #888; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{ background: #16213e; color: #00d4ff; }}
        tr:hover {{ background: #16213e; }}
        .severity {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        .critical {{ background: #ff0000; }}
        .high {{ background: #ff6600; }}
        .medium {{ background: #ffcc00; color: #000; }}
        .low {{ background: #00cc00; color: #000; }}
        .signal-bar {{
            width: 100px;
            height: 10px;
            background: #333;
            border-radius: 5px;
            overflow: hidden;
        }}
        .signal-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ff0000, #ffff00, #00ff00);
        }}
        .meta {{ color: #666; font-size: 14px; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 {title}</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <div class="card">
                <div class="number">{scan_result.network_count}</div>
                <div class="label">Networks Found</div>
            </div>
            <div class="card">
                <div class="number" style="color: #ff6600">{len(threats)}</div>
                <div class="label">Threats Detected</div>
            </div>
            <div class="card">
                <div class="number">{scan_result.duration_seconds:.1f}s</div>
                <div class="label">Scan Duration</div>
            </div>
        </div>
"""
        
        # Threats section
        if threats:
            html += """
        <h2>⚠️ Security Threats</h2>
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Networks</th>
                </tr>
            </thead>
            <tbody>
"""
            for threat in sorted(threats, key=lambda t: list(ThreatSeverity).index(t.severity)):
                severity_class = threat.severity.value
                network_count = len(threat.networks)
                html += f"""
                <tr>
                    <td><span class="severity {severity_class}">{threat.severity.value.upper()}</span></td>
                    <td>{threat.category.value.replace('_', ' ').title()}</td>
                    <td>{threat.description}</td>
                    <td>{network_count}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""
        else:
            html += """
        <h2>✅ No Threats Detected</h2>
        <p>No security issues were found in this scan.</p>
"""
        
        # Networks section
        html += """
        <h2>📶 Discovered Networks</h2>
        <table>
            <thead>
                <tr>
                    <th>SSID</th>
                    <th>BSSID</th>
                    <th>Signal</th>
                    <th>Channel</th>
                    <th>Security</th>
                    <th>Vendor</th>
                </tr>
            </thead>
            <tbody>
"""
        for network in sorted(scan_result.networks, key=lambda n: n.rssi_dbm, reverse=True):
            ssid = network.ssid if network.ssid else "&lt;Hidden&gt;"
            signal_pct = network.signal_percent
            html += f"""
                <tr>
                    <td>{ssid}</td>
                    <td><code>{network.bssid}</code></td>
                    <td>
                        <div class="signal-bar">
                            <div class="signal-fill" style="width: {signal_pct}%"></div>
                        </div>
                        {signal_pct}% ({network.rssi_dbm} dBm)
                    </td>
                    <td>{network.channel} ({network.band})</td>
                    <td>{network.security.value}</td>
                    <td>{network.vendor}</td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
        
        <div class="meta">
            <p>Scanner: {scan_result.scanner_type} | Platform: {scan_result.platform}</p>
            <p>Scan time: {scan_result.scan_time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def generate_csv(self, scan_result: ScanResult) -> str:
        """
        Generate CSV report of networks.
        
        Args:
            scan_result: Scan result data
            
        Returns:
            CSV string
        """
        return scan_result.to_csv()
    
    def generate_threat_csv(self, threats: List[Threat]) -> str:
        """
        Generate CSV report of threats.
        
        Args:
            threats: List of threats
            
        Returns:
            CSV string
        """
        lines = ["ID,Severity,Category,Description,NetworkCount,DetectedAt"]
        
        for t in threats:
            desc = t.description.replace('"', '""')  # Escape quotes
            lines.append(
                f'{t.id},{t.severity.value},{t.category.value},"{desc}",'
                f'{len(t.networks)},{t.detected_at.isoformat()}'
            )
        
        return "\n".join(lines)
    
    def save_report(
        self,
        content: str,
        path: Path,
        create_dirs: bool = True
    ) -> None:
        """
        Save report to file.
        
        Args:
            content: Report content
            path: Output file path
            create_dirs: Create parent directories if needed
        """
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _count_by_severity(self, threats: List[Threat]) -> dict:
        """Count threats by severity level."""
        counts = {s.value: 0 for s in ThreatSeverity}
        for threat in threats:
            counts[threat.severity.value] += 1
        return counts
