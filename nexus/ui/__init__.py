"""User interface components.

Note: GUI components (RadarView, IntelligenceDashboard) are lazily imported
to allow CLI usage without tkinter installed.
"""

# CLI is always available
from nexus.ui.cli import main as cli_main

__all__ = ["cli_main"]


def get_radar_view():
    """Lazily import RadarView to avoid tkinter dependency for CLI users."""
    from nexus.ui.radar import RadarView
    return RadarView


def get_intel_dashboard():
    """Lazily import IntelligenceDashboard to avoid tkinter dependency."""
    from nexus.ui.intel_dashboard import IntelligenceDashboard, IntelEvent, EventType
    return IntelligenceDashboard, IntelEvent, EventType
