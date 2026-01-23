"""
Configuration management for Nexus WiFi Radar.

Handles loading, saving, and accessing configuration settings.
"""

import json
import os
import platform
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List


def get_config_dir() -> Path:
    """Get the platform-appropriate configuration directory."""
    system = platform.system().lower()
    
    if system == "windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(base) / "nexus"
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(xdg_config) / "nexus"


def get_data_dir() -> Path:
    """Get the platform-appropriate data directory."""
    system = platform.system().lower()
    
    if system == "windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / "nexus"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(xdg_data) / "nexus"


@dataclass
class ScanConfig:
    """Scanning configuration."""
    interval_seconds: int = 30
    timeout_seconds: int = 10
    use_scapy: bool = False  # Set to True to try Scapy mode (requires Npcap + compatible adapter)
    auto_vendor_lookup: bool = True
    
    # Weak signal detection settings
    min_signal_dbm: int = -90          # Minimum signal to display (default: -90 = show all)
    weak_signal_threshold: int = -75   # Signals weaker than this are highlighted as "weak"
    extended_scan: bool = False        # Enable extended scanning mode for weak signals
    extended_timeout_seconds: int = 30 # Timeout when extended_scan is enabled


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "dark"
    radar_max_networks: int = 12
    refresh_rate_ms: int = 1000
    window_width: int = 900
    window_height: int = 600


@dataclass
class AudioConfig:
    """Audio feedback configuration."""
    enabled: bool = True
    volume: float = 0.7
    rssi_tones: bool = True
    threat_alerts: bool = True
    discovery_pings: bool = True


@dataclass
class SecurityConfig:
    """Security/threat detection configuration."""
    baseline_networks: List[str] = field(default_factory=list)
    alert_on_new: bool = True
    rules_enabled: List[str] = field(default_factory=lambda: [
        "weak_encryption",
        "ssid_spoofing",
        "rogue_ap",
        "channel_anomaly"
    ])


@dataclass
class ExportConfig:
    """Export configuration."""
    auto_export: bool = False
    format: str = "csv"
    directory: str = "./exports"


@dataclass
class ServerConfig:
    """Remote server/agent configuration."""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    api_key: str = ""
    agent_mode: bool = False
    server_url: str = ""


@dataclass
class Config:
    """
    Main configuration container.
    
    Manages all application settings with automatic loading/saving.
    """
    scan: ScanConfig = field(default_factory=ScanConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    _config_path: Optional[Path] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Initialize configuration path."""
        if self._config_path is None:
            self._config_path = get_config_dir() / "config.json"
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """
        Load configuration from file.
        
        Args:
            path: Custom config file path (uses default if None)
            
        Returns:
            Config instance with loaded settings
        """
        config = cls()
        config._config_path = path or get_config_dir() / "config.json"
        
        if config._config_path.exists():
            try:
                with open(config._config_path, "r") as f:
                    data = json.load(f)
                
                if "scan" in data:
                    config.scan = ScanConfig(**data["scan"])
                if "ui" in data:
                    config.ui = UIConfig(**data["ui"])
                if "audio" in data:
                    config.audio = AudioConfig(**data["audio"])
                if "security" in data:
                    config.security = SecurityConfig(**data["security"])
                if "export" in data:
                    config.export = ExportConfig(**data["export"])
                if "server" in data:
                    config.server = ServerConfig(**data["server"])
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                # Return default config on error
                print(f"Warning: Could not load config: {e}")
        
        return config
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            path: Custom config file path (uses default if None)
        """
        save_path = path or self._config_path
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "scan": asdict(self.scan),
            "ui": asdict(self.ui),
            "audio": asdict(self.audio),
            "security": asdict(self.security),
            "export": asdict(self.export),
            "server": asdict(self.server),
        }
        
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "scan": asdict(self.scan),
            "ui": asdict(self.ui),
            "audio": asdict(self.audio),
            "security": asdict(self.security),
            "export": asdict(self.export),
            "server": asdict(self.server),
        }
    
    def reset(self) -> None:
        """Reset all settings to defaults."""
        self.scan = ScanConfig()
        self.ui = UIConfig()
        self.audio = AudioConfig()
        self.security = SecurityConfig()
        self.export = ExportConfig()
        self.server = ServerConfig()


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config() -> Config:
    """Reload configuration from disk."""
    global _config
    _config = Config.load()
    return _config
