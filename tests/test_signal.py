"""
Tests for the signal utilities module.
"""

import pytest
from nexus.core.signal import (
    rssi_to_percent,
    percent_to_rssi,
    get_signal_quality,
    get_signal_quality_str,
    get_signal_bars,
    get_signal_icon,
    is_weak_signal,
    is_strong_signal,
    get_signal_color,
    get_signal_hex_color,
    format_signal_strength,
    SignalQuality,
    RSSI_EXCELLENT,
    RSSI_MIN,
)


class TestRSSIToPercent:
    """Tests for RSSI to percentage conversion."""

    def test_excellent_signal(self):
        """Test excellent signal (-30 dBm = 100%)."""
        assert rssi_to_percent(-30) == 100

    def test_minimum_signal(self):
        """Test minimum signal (-90 dBm = 0%)."""
        assert rssi_to_percent(-90) == 0

    def test_mid_range_signal(self):
        """Test mid-range signal (-60 dBm = 50%)."""
        assert rssi_to_percent(-60) == 50

    def test_clamping_high(self):
        """Test clamping above excellent threshold."""
        assert rssi_to_percent(-20) == 100  # Clamped to -30

    def test_clamping_low(self):
        """Test clamping below minimum threshold."""
        assert rssi_to_percent(-100) == 0  # Clamped to -90


class TestPercentToRSSI:
    """Tests for percentage to RSSI conversion."""

    def test_full_percent(self):
        """Test 100% = -30 dBm."""
        assert percent_to_rssi(100) == -30

    def test_zero_percent(self):
        """Test 0% = -90 dBm."""
        assert percent_to_rssi(0) == -90

    def test_mid_percent(self):
        """Test 50% = -60 dBm."""
        assert percent_to_rssi(50) == -60

    def test_clamping(self):
        """Test clamping out-of-range percentages."""
        assert percent_to_rssi(150) == -30  # Clamped to 100%
        assert percent_to_rssi(-10) == -90  # Clamped to 0%


class TestRoundTrip:
    """Test round-trip conversion."""

    def test_rssi_roundtrip(self):
        """Test RSSI -> percent -> RSSI round trip."""
        for rssi in range(-90, -29):
            percent = rssi_to_percent(rssi)
            recovered = percent_to_rssi(percent)
            # Allow 1 dBm tolerance due to integer rounding
            assert abs(rssi - recovered) <= 1


class TestSignalQuality:
    """Tests for signal quality classification."""

    def test_excellent_quality(self):
        """Test excellent quality detection."""
        assert get_signal_quality(-25) == SignalQuality.EXCELLENT
        assert get_signal_quality(-30) == SignalQuality.EXCELLENT

    def test_very_good_quality(self):
        """Test very good quality detection."""
        assert get_signal_quality(-40) == SignalQuality.VERY_GOOD
        assert get_signal_quality(-50) == SignalQuality.VERY_GOOD

    def test_good_quality(self):
        """Test good quality detection."""
        assert get_signal_quality(-55) == SignalQuality.GOOD
        assert get_signal_quality(-60) == SignalQuality.GOOD

    def test_fair_quality(self):
        """Test fair quality detection."""
        assert get_signal_quality(-65) == SignalQuality.FAIR
        assert get_signal_quality(-70) == SignalQuality.FAIR

    def test_weak_quality(self):
        """Test weak quality detection."""
        assert get_signal_quality(-75) == SignalQuality.WEAK
        assert get_signal_quality(-80) == SignalQuality.WEAK

    def test_unusable_quality(self):
        """Test unusable quality detection."""
        assert get_signal_quality(-85) == SignalQuality.UNUSABLE
        assert get_signal_quality(-95) == SignalQuality.UNUSABLE

    def test_quality_string(self):
        """Test quality string output."""
        assert get_signal_quality_str(-30) == "Excellent"
        assert get_signal_quality_str(-60) == "Good"
        assert get_signal_quality_str(-90) == "Unusable"


class TestSignalBars:
    """Tests for signal bars calculation."""

    def test_max_bars(self):
        """Test maximum bars for strong signal."""
        assert get_signal_bars(-30, max_bars=5) == 5

    def test_min_bars(self):
        """Test minimum bars for weak signal."""
        assert get_signal_bars(-90, max_bars=5) == 0

    def test_custom_max_bars(self):
        """Test custom maximum bars."""
        assert get_signal_bars(-30, max_bars=4) == 4
        assert get_signal_bars(-30, max_bars=3) == 3


class TestSignalIcons:
    """Tests for signal icon generation."""

    def test_icon_for_strong_signal(self):
        """Test icon for strong signal."""
        icon = get_signal_icon(-30)
        assert icon in ["█", "▆", "▄", "▂", "░"]

    def test_icon_for_weak_signal(self):
        """Test icon for weak signal."""
        icon = get_signal_icon(-90)
        assert icon == "░"


class TestWeakStrongSignal:
    """Tests for weak/strong signal detection."""

    def test_is_weak_signal(self):
        """Test weak signal detection."""
        assert is_weak_signal(-85) is True
        assert is_weak_signal(-75) is True
        assert is_weak_signal(-60) is False

    def test_is_weak_signal_custom_threshold(self):
        """Test weak signal with custom threshold."""
        assert is_weak_signal(-70, threshold=-65) is True
        assert is_weak_signal(-60, threshold=-65) is False

    def test_is_strong_signal(self):
        """Test strong signal detection."""
        assert is_strong_signal(-50) is True
        assert is_strong_signal(-60) is True
        assert is_strong_signal(-80) is False

    def test_is_strong_signal_custom_threshold(self):
        """Test strong signal with custom threshold."""
        assert is_strong_signal(-55, threshold=-50) is False
        assert is_strong_signal(-45, threshold=-50) is True


class TestSignalColors:
    """Tests for signal color generation."""

    def test_strong_signal_green(self):
        """Test that strong signals are green."""
        r, g, b = get_signal_color(-30)
        assert g > r  # More green than red

    def test_weak_signal_red(self):
        """Test that weak signals are red."""
        r, g, b = get_signal_color(-90)
        assert r > g  # More red than green

    def test_hex_color_format(self):
        """Test hex color string format."""
        color = get_signal_hex_color(-60)
        assert color.startswith("#")
        assert len(color) == 7


class TestFormatSignalStrength:
    """Tests for signal strength formatting."""

    def test_basic_format(self):
        """Test basic signal strength format."""
        result = format_signal_strength(-60, include_percent=False, include_quality=False)
        assert "-60 dBm" in result

    def test_format_with_percent(self):
        """Test format with percentage."""
        result = format_signal_strength(-60, include_percent=True, include_quality=False)
        assert "-60 dBm" in result
        assert "50%" in result

    def test_format_with_quality(self):
        """Test format with quality label."""
        result = format_signal_strength(-60, include_percent=False, include_quality=True)
        assert "-60 dBm" in result
        assert "Good" in result

    def test_format_full(self):
        """Test full format with percent and quality."""
        result = format_signal_strength(-60, include_percent=True, include_quality=True)
        assert "-60 dBm" in result
        assert "50%" in result
        assert "Good" in result
