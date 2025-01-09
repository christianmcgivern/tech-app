"""Configuration module for the WebSocket client."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class AudioConfig:
    """Audio configuration settings."""
    input_format: str = "pcm16"
    output_format: str = "pcm16"
    sample_rate: int = 24000
    channels: int = 1
    chunk_size: int = 1024
    max_chunk_size: int = 15 * 1024 * 1024  # 15MB

@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""
    enabled: bool = True
    threshold: float = 0.5
    prefix_padding_ms: int = 300
    silence_duration_ms: int = 200

@dataclass
class Config:
    """Configuration for WebSocket client.
    
    Attributes:
        api_key: OpenAI API key
        model_version: Model version to use (e.g., "gpt-4o-realtime-preview-2024-12-17")
        websocket_url: WebSocket endpoint URL
        voice: Voice to use for audio responses
        modalities: List of enabled modalities (e.g., ["text", "audio"])
        instructions: System instructions for the model
        audio_config: Audio configuration settings
        vad_config: Voice Activity Detection configuration
        max_retries: Maximum number of connection retries
        retry_delay: Initial delay between retries in seconds
    """
    api_key: str
    model_version: str = "gpt-4o-realtime-preview-2024-12-17"
    websocket_url: str = "wss://api.openai.com/v1/audio/speech"
    voice: str = "alloy"
    modalities: List[str] = None
    instructions: str = "You are a helpful assistant."
    audio_config: AudioConfig = None
    vad_config: VADConfig = None
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Initialize default values for nested configurations."""
        if self.modalities is None:
            self.modalities = ["text", "audio"]
        if self.audio_config is None:
            self.audio_config = AudioConfig()
        if self.vad_config is None:
            self.vad_config = VADConfig()
            
    def to_session_config(self) -> Dict[str, Any]:
        """Convert configuration to session update format."""
        return {
            "type": "session.update",
            "session": {
                "modalities": self.modalities,
                "instructions": self.instructions,
                "voice": self.voice,
                "input_audio_format": self.audio_config.input_format,
                "output_audio_format": self.audio_config.output_format,
                "input_audio_transcription": {
                    "enabled": True,
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": self.vad_config.threshold,
                    "prefix_padding_ms": self.vad_config.prefix_padding_ms,
                    "silence_duration_ms": self.vad_config.silence_duration_ms
                }
            }
        } 