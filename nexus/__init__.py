"""
Nexus WiFi Radar - Cross-platform WiFi scanner and security analyzer.

A modular WiFi network scanner with radar visualization, threat detection,
and audio feedback capabilities.
"""

__version__ = "0.2.0"
__author__ = "Nexus WiFi Radar Contributors"

from nexus.core.models import Network, ScanResult
from nexus.core.scan import get_scanner

__all__ = ["Network", "ScanResult", "get_scanner", "__version__"]
