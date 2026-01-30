"""
Signal strength utilities for Nexus WiFi Radar.

Provides centralized signal calculation functions to ensure
consistency across all modules.

Signal Strength Reference:
- -30 dBm: Excellent (max practical strength)
- -50 dBm: Very good
- -60 dBm: Good
- -70 dBm: Fair
- -80 dBm: Weak
- -90 dBm: Unusable (practical minimum)
"""

from enum import Enum
from typing import Tuple

# Signal strength boundaries (in dBm)
RSSI_EXCELLENT = -30
RSSI_VERY_GOOD = -50
RSSI_GOOD = -60
RSSI_FAIR = -70
RSSI_WEAK = -80
RSSI_MIN = -90


class SignalQuality(Enum):
    """Signal quality levels."""
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very Good"
    GOOD = "Good"
    FAIR = "Fair"
    WEAK = "Weak"
    UNUSABLE = "Unusable"


def rssi_to_percent(rssi_dbm: int) -> int:
    """
    Convert RSSI dBm to percentage (0-100).

    Uses a linear mapping between -90 dBm (0%) and -30 dBm (100%).
    Values outside this range are clamped.

    Args:
        rssi_dbm: Signal strength in dBm (negative value)

    Returns:
        Signal strength as percentage (0-100)

    Example:
        >>> rssi_to_percent(-30)
        100
        >>> rssi_to_percent(-60)
        50
        >>> rssi_to_percent(-90)
        0
    """
    # Clamp to reasonable range
    rssi = max(RSSI_MIN, min(RSSI_EXCELLENT, rssi_dbm))

    # Linear mapping: -90 dBm = 0%, -30 dBm = 100%
    # Formula: percent = (rssi - RSSI_MIN) / (RSSI_EXCELLENT - RSSI_MIN) * 100
    return int((rssi - RSSI_MIN) * 100 / (RSSI_EXCELLENT - RSSI_MIN))


def percent_to_rssi(percent: int) -> int:
    """
    Convert percentage to RSSI dBm.

    Args:
        percent: Signal strength percentage (0-100)

    Returns:
        Signal strength in dBm

    Example:
        >>> percent_to_rssi(100)
        -30
        >>> percent_to_rssi(50)
        -60
        >>> percent_to_rssi(0)
        -90
    """
    # Clamp to valid range
    percent = max(0, min(100, percent))

    # Inverse of rssi_to_percent
    return int(RSSI_MIN + (percent * (RSSI_EXCELLENT - RSSI_MIN) / 100))


def get_signal_quality(rssi_dbm: int) -> SignalQuality:
    """
    Get human-readable signal quality from RSSI.

    Args:
        rssi_dbm: Signal strength in dBm

    Returns:
        SignalQuality enum value
    """
    if rssi_dbm >= RSSI_EXCELLENT:
        return SignalQuality.EXCELLENT
    elif rssi_dbm >= RSSI_VERY_GOOD:
        return SignalQuality.VERY_GOOD
    elif rssi_dbm >= RSSI_GOOD:
        return SignalQuality.GOOD
    elif rssi_dbm >= RSSI_FAIR:
        return SignalQuality.FAIR
    elif rssi_dbm >= RSSI_WEAK:
        return SignalQuality.WEAK
    else:
        return SignalQuality.UNUSABLE


def get_signal_quality_str(rssi_dbm: int) -> str:
    """
    Get human-readable signal quality string from RSSI.

    Args:
        rssi_dbm: Signal strength in dBm

    Returns:
        Quality string (e.g., "Excellent", "Good", "Weak")
    """
    return get_signal_quality(rssi_dbm).value


def get_signal_bars(rssi_dbm: int, max_bars: int = 5) -> int:
    """
    Convert RSSI to number of signal bars.

    Args:
        rssi_dbm: Signal strength in dBm
        max_bars: Maximum number of bars (default 5)

    Returns:
        Number of signal bars (0 to max_bars)
    """
    percent = rssi_to_percent(rssi_dbm)
    return int(percent * max_bars / 100)


def get_signal_icon(rssi_dbm: int) -> str:
    """
    Get a Unicode signal strength icon.

    Args:
        rssi_dbm: Signal strength in dBm

    Returns:
        Unicode icon representing signal strength
    """
    bars = get_signal_bars(rssi_dbm, max_bars=4)
    icons = ["░", "▂", "▄", "▆", "█"]
    return icons[bars]


def is_weak_signal(rssi_dbm: int, threshold: int = RSSI_WEAK) -> bool:
    """
    Check if signal is considered weak.

    Args:
        rssi_dbm: Signal strength in dBm
        threshold: Threshold for weak signal (default -80 dBm)

    Returns:
        True if signal is weak
    """
    return rssi_dbm < threshold


def is_strong_signal(rssi_dbm: int, threshold: int = RSSI_GOOD) -> bool:
    """
    Check if signal is considered strong.

    Args:
        rssi_dbm: Signal strength in dBm
        threshold: Threshold for strong signal (default -60 dBm)

    Returns:
        True if signal is strong
    """
    return rssi_dbm >= threshold


def get_signal_color(rssi_dbm: int) -> Tuple[int, int, int]:
    """
    Get RGB color for signal strength visualization.

    Returns green for strong signals, yellow for fair, red for weak.

    Args:
        rssi_dbm: Signal strength in dBm

    Returns:
        RGB tuple (0-255 for each channel)
    """
    percent = rssi_to_percent(rssi_dbm)

    if percent >= 60:
        # Green for strong signals
        return (0, 255, 0)
    elif percent >= 40:
        # Yellow/Orange for fair signals
        # Interpolate from green to yellow
        ratio = (percent - 40) / 20
        return (int(255 * (1 - ratio)), 255, 0)
    elif percent >= 20:
        # Orange for weak signals
        ratio = (percent - 20) / 20
        return (255, int(255 * ratio), 0)
    else:
        # Red for very weak signals
        return (255, 0, 0)


def get_signal_hex_color(rssi_dbm: int) -> str:
    """
    Get hex color string for signal strength visualization.

    Args:
        rssi_dbm: Signal strength in dBm

    Returns:
        Hex color string (e.g., "#00ff00" for green)
    """
    r, g, b = get_signal_color(rssi_dbm)
    return f"#{r:02x}{g:02x}{b:02x}"


def format_signal_strength(rssi_dbm: int, include_percent: bool = True,
                          include_quality: bool = False) -> str:
    """
    Format signal strength for display.

    Args:
        rssi_dbm: Signal strength in dBm
        include_percent: Include percentage
        include_quality: Include quality label

    Returns:
        Formatted string (e.g., "-65 dBm (58%)" or "-65 dBm (58%, Good)")
    """
    parts = [f"{rssi_dbm} dBm"]

    if include_percent or include_quality:
        extra = []
        if include_percent:
            extra.append(f"{rssi_to_percent(rssi_dbm)}%")
        if include_quality:
            extra.append(get_signal_quality_str(rssi_dbm))
        parts.append(f"({', '.join(extra)})")

    return " ".join(parts)
