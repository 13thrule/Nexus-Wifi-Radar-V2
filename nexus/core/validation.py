"""
Input validation utilities for Nexus WiFi Radar.

Provides validation functions for network data to ensure
data integrity and prevent issues with malformed input.
"""

import re
from typing import Optional, Tuple

# Regular expressions for validation
MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
MAC_PATTERN_NO_SEP = re.compile(r"^[0-9A-Fa-f]{12}$")

# Valid WiFi channels
# 2.4 GHz: 1-14 (14 only in Japan)
# 5 GHz: 32-177 (with gaps)
VALID_2GHZ_CHANNELS = set(range(1, 15))
VALID_5GHZ_CHANNELS = {
    32, 36, 40, 44, 48, 52, 56, 60, 64,  # UNII-1 & UNII-2A
    100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144,  # UNII-2C
    149, 153, 157, 161, 165, 169, 173, 177  # UNII-3
}
VALID_CHANNELS = VALID_2GHZ_CHANNELS | VALID_5GHZ_CHANNELS

# RSSI range (in dBm)
MIN_RSSI = -100
MAX_RSSI = 0

# SSID constraints (IEEE 802.11)
MAX_SSID_LENGTH = 32


class ValidationError(ValueError):
    """Raised when validation fails."""
    pass


def validate_mac_address(mac: str, strict: bool = False) -> str:
    """
    Validate and normalize a MAC address.

    Args:
        mac: MAC address string (e.g., "00:11:22:33:44:55" or "00-11-22-33-44-55")
        strict: If True, require separator format

    Returns:
        Normalized MAC address in uppercase with colons

    Raises:
        ValidationError: If MAC address is invalid
    """
    if not mac:
        raise ValidationError("MAC address cannot be empty")

    mac = mac.strip().upper()

    # Try pattern with separators
    if MAC_PATTERN.match(mac):
        # Normalize to colon format
        return mac.replace("-", ":")

    # Try pattern without separators
    if not strict and MAC_PATTERN_NO_SEP.match(mac):
        # Insert colons
        return ":".join(mac[i:i+2] for i in range(0, 12, 2))

    raise ValidationError(
        f"Invalid MAC address format: '{mac}'. "
        "Expected format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"
    )


def validate_bssid(bssid: str) -> str:
    """
    Validate a BSSID (which is a MAC address).

    Args:
        bssid: BSSID string

    Returns:
        Normalized BSSID

    Raises:
        ValidationError: If BSSID is invalid
    """
    try:
        return validate_mac_address(bssid)
    except ValidationError as e:
        raise ValidationError(f"Invalid BSSID: {e}") from e


def validate_ssid(ssid: str, allow_empty: bool = True) -> str:
    """
    Validate an SSID.

    Args:
        ssid: SSID string (network name)
        allow_empty: If True, allow empty SSID (hidden networks)

    Returns:
        Validated SSID string

    Raises:
        ValidationError: If SSID is invalid
    """
    if ssid is None:
        if allow_empty:
            return ""
        raise ValidationError("SSID cannot be None")

    # Convert to string if needed
    ssid = str(ssid)

    if not allow_empty and not ssid.strip():
        raise ValidationError("SSID cannot be empty")

    # Check length (SSID can be 0-32 bytes in UTF-8)
    ssid_bytes = ssid.encode("utf-8")
    if len(ssid_bytes) > MAX_SSID_LENGTH:
        raise ValidationError(
            f"SSID exceeds maximum length of {MAX_SSID_LENGTH} bytes "
            f"(got {len(ssid_bytes)} bytes)"
        )

    return ssid


def validate_channel(channel: int, allow_zero: bool = False) -> int:
    """
    Validate a WiFi channel number.

    Args:
        channel: Channel number
        allow_zero: If True, allow 0 (unknown channel)

    Returns:
        Validated channel number

    Raises:
        ValidationError: If channel is invalid
    """
    if not isinstance(channel, int):
        try:
            channel = int(channel)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Channel must be an integer, got {type(channel).__name__}") from e

    if channel == 0:
        if allow_zero:
            return 0
        raise ValidationError("Channel cannot be 0")

    if channel < 0:
        raise ValidationError(f"Channel cannot be negative: {channel}")

    if channel not in VALID_CHANNELS:
        raise ValidationError(
            f"Invalid WiFi channel: {channel}. "
            f"Valid 2.4GHz channels: 1-14, "
            f"Valid 5GHz channels: 36, 40, 44, ... 165"
        )

    return channel


def validate_frequency(frequency_mhz: int) -> int:
    """
    Validate a frequency in MHz.

    Args:
        frequency_mhz: Frequency in MHz

    Returns:
        Validated frequency

    Raises:
        ValidationError: If frequency is invalid
    """
    if not isinstance(frequency_mhz, int):
        try:
            frequency_mhz = int(frequency_mhz)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Frequency must be an integer, got {type(frequency_mhz).__name__}") from e

    # 2.4 GHz band: 2400-2500 MHz
    # 5 GHz band: 5150-5925 MHz
    if 2400 <= frequency_mhz <= 2500:
        return frequency_mhz
    if 5150 <= frequency_mhz <= 5925:
        return frequency_mhz

    raise ValidationError(
        f"Invalid WiFi frequency: {frequency_mhz} MHz. "
        f"Expected 2400-2500 MHz (2.4GHz) or 5150-5925 MHz (5GHz)"
    )


def validate_rssi(rssi_dbm: int) -> int:
    """
    Validate an RSSI value in dBm.

    Args:
        rssi_dbm: Signal strength in dBm

    Returns:
        Validated RSSI value

    Raises:
        ValidationError: If RSSI is invalid
    """
    if not isinstance(rssi_dbm, (int, float)):
        try:
            rssi_dbm = int(rssi_dbm)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"RSSI must be a number, got {type(rssi_dbm).__name__}") from e

    rssi_dbm = int(rssi_dbm)

    if rssi_dbm > MAX_RSSI:
        raise ValidationError(
            f"RSSI value {rssi_dbm} dBm is invalid (should be negative or zero)"
        )

    if rssi_dbm < MIN_RSSI:
        raise ValidationError(
            f"RSSI value {rssi_dbm} dBm is unrealistically low (minimum: {MIN_RSSI} dBm)"
        )

    return rssi_dbm


def validate_network_data(
    ssid: str,
    bssid: str,
    channel: int,
    frequency_mhz: int,
    rssi_dbm: int
) -> Tuple[str, str, int, int, int]:
    """
    Validate all network data fields at once.

    Args:
        ssid: Network name
        bssid: MAC address of access point
        channel: WiFi channel
        frequency_mhz: Frequency in MHz
        rssi_dbm: Signal strength in dBm

    Returns:
        Tuple of validated (ssid, bssid, channel, frequency_mhz, rssi_dbm)

    Raises:
        ValidationError: If any field is invalid
    """
    validated_ssid = validate_ssid(ssid, allow_empty=True)
    validated_bssid = validate_bssid(bssid)
    validated_channel = validate_channel(channel, allow_zero=True)
    validated_frequency = validate_frequency(frequency_mhz)
    validated_rssi = validate_rssi(rssi_dbm)

    return (validated_ssid, validated_bssid, validated_channel,
            validated_frequency, validated_rssi)


def is_valid_mac(mac: str) -> bool:
    """
    Check if a string is a valid MAC address.

    Args:
        mac: String to check

    Returns:
        True if valid MAC address, False otherwise
    """
    try:
        validate_mac_address(mac)
        return True
    except ValidationError:
        return False


def is_valid_channel(channel: int) -> bool:
    """
    Check if a channel number is valid.

    Args:
        channel: Channel number to check

    Returns:
        True if valid channel, False otherwise
    """
    try:
        validate_channel(channel, allow_zero=False)
        return True
    except ValidationError:
        return False


def normalize_mac(mac: str) -> Optional[str]:
    """
    Normalize a MAC address to uppercase with colons.

    Args:
        mac: MAC address string

    Returns:
        Normalized MAC address or None if invalid
    """
    try:
        return validate_mac_address(mac)
    except ValidationError:
        return None


def channel_to_frequency(channel: int) -> Optional[int]:
    """
    Convert WiFi channel to frequency in MHz.

    Args:
        channel: WiFi channel number

    Returns:
        Frequency in MHz or None if invalid channel
    """
    if channel < 1:
        return None

    # 2.4 GHz channels (1-14)
    if 1 <= channel <= 13:
        return 2407 + (channel * 5)
    if channel == 14:
        return 2484

    # 5 GHz channels
    if channel in VALID_5GHZ_CHANNELS:
        return 5000 + (channel * 5)

    return None


def frequency_to_channel(frequency_mhz: int) -> Optional[int]:
    """
    Convert frequency in MHz to WiFi channel.

    Args:
        frequency_mhz: Frequency in MHz

    Returns:
        Channel number or None if invalid frequency
    """
    # 2.4 GHz band
    if 2412 <= frequency_mhz <= 2472:
        return (frequency_mhz - 2407) // 5
    if frequency_mhz == 2484:
        return 14

    # 5 GHz band
    if 5170 <= frequency_mhz <= 5895:
        return (frequency_mhz - 5000) // 5

    return None
