"""
Tests for the validation module.
"""

import pytest
from nexus.core.validation import (
    validate_mac_address,
    validate_bssid,
    validate_ssid,
    validate_channel,
    validate_frequency,
    validate_rssi,
    validate_network_data,
    is_valid_mac,
    is_valid_channel,
    normalize_mac,
    channel_to_frequency,
    frequency_to_channel,
    ValidationError,
)


class TestMACValidation:
    """Tests for MAC address validation."""

    def test_valid_mac_with_colons(self):
        """Test valid MAC address with colons."""
        assert validate_mac_address("00:11:22:33:44:55") == "00:11:22:33:44:55"
        assert validate_mac_address("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"

    def test_valid_mac_with_dashes(self):
        """Test valid MAC address with dashes."""
        assert validate_mac_address("00-11-22-33-44-55") == "00:11:22:33:44:55"

    def test_valid_mac_without_separators(self):
        """Test valid MAC address without separators."""
        assert validate_mac_address("001122334455") == "00:11:22:33:44:55"

    def test_invalid_mac_empty(self):
        """Test empty MAC address."""
        with pytest.raises(ValidationError):
            validate_mac_address("")

    def test_invalid_mac_wrong_format(self):
        """Test invalid MAC address format."""
        with pytest.raises(ValidationError):
            validate_mac_address("not-a-mac")

    def test_invalid_mac_too_short(self):
        """Test MAC address that's too short."""
        with pytest.raises(ValidationError):
            validate_mac_address("00:11:22:33:44")

    def test_invalid_mac_invalid_hex(self):
        """Test MAC address with invalid hex characters."""
        with pytest.raises(ValidationError):
            validate_mac_address("GG:HH:II:JJ:KK:LL")

    def test_is_valid_mac(self):
        """Test is_valid_mac helper function."""
        assert is_valid_mac("00:11:22:33:44:55") is True
        assert is_valid_mac("invalid") is False

    def test_normalize_mac(self):
        """Test MAC normalization."""
        assert normalize_mac("00-11-22-33-44-55") == "00:11:22:33:44:55"
        assert normalize_mac("invalid") is None


class TestSSIDValidation:
    """Tests for SSID validation."""

    def test_valid_ssid(self):
        """Test valid SSID."""
        assert validate_ssid("MyNetwork") == "MyNetwork"
        assert validate_ssid("Network with spaces") == "Network with spaces"

    def test_empty_ssid_allowed(self):
        """Test empty SSID when allowed."""
        assert validate_ssid("", allow_empty=True) == ""
        assert validate_ssid(None, allow_empty=True) == ""

    def test_empty_ssid_not_allowed(self):
        """Test empty SSID when not allowed."""
        with pytest.raises(ValidationError):
            validate_ssid("", allow_empty=False)

    def test_ssid_too_long(self):
        """Test SSID exceeding max length."""
        long_ssid = "a" * 33  # 33 bytes, exceeds 32 byte limit
        with pytest.raises(ValidationError):
            validate_ssid(long_ssid)


class TestChannelValidation:
    """Tests for channel validation."""

    def test_valid_2ghz_channels(self):
        """Test valid 2.4GHz channels."""
        for ch in range(1, 15):
            assert validate_channel(ch) == ch

    def test_valid_5ghz_channels(self):
        """Test valid 5GHz channels."""
        valid_5ghz = [36, 40, 44, 48, 149, 153, 157, 161, 165]
        for ch in valid_5ghz:
            assert validate_channel(ch) == ch

    def test_invalid_channel_zero(self):
        """Test channel 0 when not allowed."""
        with pytest.raises(ValidationError):
            validate_channel(0, allow_zero=False)

    def test_channel_zero_allowed(self):
        """Test channel 0 when allowed."""
        assert validate_channel(0, allow_zero=True) == 0

    def test_invalid_channel_negative(self):
        """Test negative channel."""
        with pytest.raises(ValidationError):
            validate_channel(-1)

    def test_invalid_channel_not_wifi(self):
        """Test non-WiFi channel."""
        with pytest.raises(ValidationError):
            validate_channel(50)  # Not a valid WiFi channel

    def test_is_valid_channel(self):
        """Test is_valid_channel helper."""
        assert is_valid_channel(6) is True
        assert is_valid_channel(50) is False


class TestFrequencyValidation:
    """Tests for frequency validation."""

    def test_valid_2ghz_frequency(self):
        """Test valid 2.4GHz frequency."""
        assert validate_frequency(2437) == 2437

    def test_valid_5ghz_frequency(self):
        """Test valid 5GHz frequency."""
        assert validate_frequency(5180) == 5180

    def test_invalid_frequency_too_low(self):
        """Test frequency below valid range."""
        with pytest.raises(ValidationError):
            validate_frequency(1000)

    def test_invalid_frequency_middle(self):
        """Test frequency in gap between bands."""
        with pytest.raises(ValidationError):
            validate_frequency(3500)


class TestRSSIValidation:
    """Tests for RSSI validation."""

    def test_valid_rssi(self):
        """Test valid RSSI values."""
        assert validate_rssi(-30) == -30
        assert validate_rssi(-60) == -60
        assert validate_rssi(-90) == -90

    def test_invalid_rssi_positive(self):
        """Test positive RSSI (invalid)."""
        with pytest.raises(ValidationError):
            validate_rssi(10)

    def test_invalid_rssi_too_low(self):
        """Test unrealistically low RSSI."""
        with pytest.raises(ValidationError):
            validate_rssi(-150)


class TestChannelFrequencyConversion:
    """Tests for channel/frequency conversion."""

    def test_channel_to_frequency_2ghz(self):
        """Test 2.4GHz channel to frequency conversion."""
        assert channel_to_frequency(1) == 2412
        assert channel_to_frequency(6) == 2437
        assert channel_to_frequency(11) == 2462
        assert channel_to_frequency(14) == 2484

    def test_channel_to_frequency_5ghz(self):
        """Test 5GHz channel to frequency conversion."""
        assert channel_to_frequency(36) == 5180
        assert channel_to_frequency(149) == 5745

    def test_frequency_to_channel_2ghz(self):
        """Test 2.4GHz frequency to channel conversion."""
        assert frequency_to_channel(2412) == 1
        assert frequency_to_channel(2437) == 6
        assert frequency_to_channel(2484) == 14

    def test_frequency_to_channel_5ghz(self):
        """Test 5GHz frequency to channel conversion."""
        assert frequency_to_channel(5180) == 36
        assert frequency_to_channel(5745) == 149


class TestNetworkDataValidation:
    """Tests for complete network data validation."""

    def test_valid_network_data(self):
        """Test valid network data."""
        result = validate_network_data(
            ssid="TestNetwork",
            bssid="00:11:22:33:44:55",
            channel=6,
            frequency_mhz=2437,
            rssi_dbm=-60
        )
        assert result == ("TestNetwork", "00:11:22:33:44:55", 6, 2437, -60)

    def test_network_data_normalizes_bssid(self):
        """Test that BSSID is normalized."""
        result = validate_network_data(
            ssid="Test",
            bssid="00-11-22-33-44-55",
            channel=6,
            frequency_mhz=2437,
            rssi_dbm=-60
        )
        assert result[1] == "00:11:22:33:44:55"
