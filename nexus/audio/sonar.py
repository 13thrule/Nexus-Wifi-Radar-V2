"""
Sonar-style audio feedback for WiFi scanning.

Provides audio tones based on signal strength and threat detection.
"""

import math
import struct
import wave
import io
from typing import Optional
from threading import Thread
from queue import Queue

from nexus.core.models import Network, Threat, ThreatSeverity


class ToneGenerator:
    """
    Generates audio tones programmatically.
    
    Creates sine wave tones at specified frequencies and durations.
    """
    
    SAMPLE_RATE = 44100
    
    @staticmethod
    def generate_tone(frequency: float, duration: float, volume: float = 0.5) -> bytes:
        """
        Generate a sine wave tone.
        
        Args:
            frequency: Tone frequency in Hz
            duration: Duration in seconds
            volume: Volume level 0.0-1.0
            
        Returns:
            Raw audio data as bytes
        """
        num_samples = int(ToneGenerator.SAMPLE_RATE * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / ToneGenerator.SAMPLE_RATE
            sample = volume * math.sin(2 * math.pi * frequency * t)
            
            # Apply fade in/out to avoid clicks
            if i < 100:
                sample *= i / 100
            elif i > num_samples - 100:
                sample *= (num_samples - i) / 100
            
            # Convert to 16-bit integer
            samples.append(int(sample * 32767))
        
        return struct.pack(f"<{len(samples)}h", *samples)
    
    @staticmethod
    def generate_beep_pattern(frequencies: list, durations: list, volume: float = 0.5) -> bytes:
        """
        Generate a pattern of beeps.
        
        Args:
            frequencies: List of frequencies (0 for silence)
            durations: List of durations for each frequency
            volume: Volume level
            
        Returns:
            Raw audio data
        """
        audio = b""
        for freq, dur in zip(frequencies, durations):
            if freq > 0:
                audio += ToneGenerator.generate_tone(freq, dur, volume)
            else:
                # Silence
                num_samples = int(ToneGenerator.SAMPLE_RATE * dur)
                audio += struct.pack(f"<{num_samples}h", *([0] * num_samples))
        return audio
    
    @staticmethod
    def to_wav(audio_data: bytes) -> bytes:
        """Convert raw audio data to WAV format."""
        buffer = io.BytesIO()
        
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(ToneGenerator.SAMPLE_RATE)
            wav.writeframes(audio_data)
        
        return buffer.getvalue()


class SonarAudio:
    """
    Sonar-style audio feedback for WiFi scanning.
    
    Provides:
    - RSSI-based tone frequency (stronger signal = higher pitch)
    - Threat alert tones (different patterns for severity levels)
    - Network discovery pings
    """
    
    # Frequency ranges for RSSI
    RSSI_FREQ_MIN = 200   # Hz for weak signal (-90 dBm)
    RSSI_FREQ_MAX = 1500  # Hz for strong signal (-30 dBm)
    
    # Threat tone frequencies
    THREAT_FREQ = {
        ThreatSeverity.CRITICAL: 1200,
        ThreatSeverity.HIGH: 900,
        ThreatSeverity.MEDIUM: 600,
        ThreatSeverity.LOW: 400,
    }
    
    def __init__(self, enabled: bool = True, volume: float = 0.7):
        """
        Initialize sonar audio.
        
        Args:
            enabled: Whether audio is enabled
            volume: Volume level 0.0-1.0
        """
        self.enabled = enabled
        self.volume = volume
        self._audio_queue: Queue = Queue()
        self._player_thread: Optional[Thread] = None
        self._running = False
        
        # Check if audio playback is available
        self._audio_available = self._check_audio()
    
    def _check_audio(self) -> bool:
        """Check if audio playback is available."""
        try:
            import winsound
            return True
        except ImportError:
            pass
        
        try:
            import simpleaudio
            return True
        except ImportError:
            pass
        
        return False
    
    def _play_audio(self, audio_data: bytes) -> None:
        """Play audio data."""
        if not self._audio_available or not self.enabled:
            return
        
        wav_data = ToneGenerator.to_wav(audio_data)
        
        try:
            # Try winsound on Windows
            import winsound
            import tempfile
            import os
            
            # Write to temp file and play
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_data)
                temp_path = f.name
            
            winsound.PlaySound(temp_path, winsound.SND_FILENAME)
            os.unlink(temp_path)
            return
        except ImportError:
            pass
        
        try:
            # Try simpleaudio
            import simpleaudio
            play_obj = simpleaudio.play_buffer(
                audio_data, 1, 2, ToneGenerator.SAMPLE_RATE
            )
            play_obj.wait_done()
        except ImportError:
            pass
    
    def rssi_to_frequency(self, rssi_dbm: int) -> float:
        """
        Convert RSSI to tone frequency.
        
        Args:
            rssi_dbm: Signal strength in dBm
            
        Returns:
            Frequency in Hz
        """
        # Clamp RSSI to -90 to -30 range
        rssi = max(-90, min(-30, rssi_dbm))
        
        # Linear mapping: -90 dBm -> MIN, -30 dBm -> MAX
        normalized = (rssi + 90) / 60
        return self.RSSI_FREQ_MIN + normalized * (self.RSSI_FREQ_MAX - self.RSSI_FREQ_MIN)
    
    def play_rssi_tone(self, rssi_dbm: int, duration: float = 0.2) -> None:
        """
        Play a tone based on signal strength.
        
        Args:
            rssi_dbm: Signal strength in dBm
            duration: Tone duration in seconds
        """
        if not self.enabled:
            return
        
        freq = self.rssi_to_frequency(rssi_dbm)
        audio = ToneGenerator.generate_tone(freq, duration, self.volume)
        
        Thread(target=self._play_audio, args=(audio,), daemon=True).start()
    
    def play_network_tone(self, network: Network, duration: float = 0.2) -> None:
        """
        Play a tone for a network.
        
        Args:
            network: Network object
            duration: Tone duration
        """
        self.play_rssi_tone(network.rssi_dbm, duration)
    
    def play_discovery_ping(self) -> None:
        """Play a ping sound for new network discovery."""
        if not self.enabled:
            return
        
        # Ascending two-tone ping
        audio = ToneGenerator.generate_beep_pattern(
            frequencies=[800, 1200],
            durations=[0.05, 0.1],
            volume=self.volume * 0.8
        )
        
        Thread(target=self._play_audio, args=(audio,), daemon=True).start()
    
    def play_lost_ping(self) -> None:
        """Play a ping sound when a network is lost."""
        if not self.enabled:
            return
        
        # Descending two-tone ping
        audio = ToneGenerator.generate_beep_pattern(
            frequencies=[1200, 600],
            durations=[0.05, 0.15],
            volume=self.volume * 0.6
        )
        
        Thread(target=self._play_audio, args=(audio,), daemon=True).start()
    
    def play_threat_alert(self, severity: ThreatSeverity) -> None:
        """
        Play a threat alert tone.
        
        Args:
            severity: Threat severity level
        """
        if not self.enabled:
            return
        
        freq = self.THREAT_FREQ.get(severity, 600)
        
        if severity == ThreatSeverity.CRITICAL:
            # Triple fast beep
            audio = ToneGenerator.generate_beep_pattern(
                frequencies=[freq, 0, freq, 0, freq],
                durations=[0.1, 0.05, 0.1, 0.05, 0.1],
                volume=self.volume
            )
        elif severity == ThreatSeverity.HIGH:
            # Double beep
            audio = ToneGenerator.generate_beep_pattern(
                frequencies=[freq, 0, freq],
                durations=[0.15, 0.1, 0.15],
                volume=self.volume * 0.9
            )
        elif severity == ThreatSeverity.MEDIUM:
            # Single long beep
            audio = ToneGenerator.generate_tone(freq, 0.3, self.volume * 0.8)
        else:
            # Soft click
            audio = ToneGenerator.generate_tone(freq, 0.1, self.volume * 0.5)
        
        Thread(target=self._play_audio, args=(audio,), daemon=True).start()
    
    def play_threat(self, threat: Threat) -> None:
        """
        Play alert for a threat.
        
        Args:
            threat: Threat object
        """
        self.play_threat_alert(threat.severity)
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable audio."""
        self.enabled = enabled
    
    def set_volume(self, volume: float) -> None:
        """Set volume level (0.0-1.0)."""
        self.volume = max(0.0, min(1.0, volume))
    
    def stop_all(self) -> None:
        """Stop all audio playback and cleanup."""
        self.enabled = False
        self._running = False


# Global audio instance
_sonar: Optional[SonarAudio] = None


def get_sonar() -> SonarAudio:
    """Get the global sonar audio instance."""
    global _sonar
    if _sonar is None:
        _sonar = SonarAudio()
    return _sonar
