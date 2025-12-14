"""
TTSClient wraps Google Cloud Text-to-Speech API.
Supports voice quality presets with cost tracking.
"""

import hashlib
import os
from typing import Optional, Tuple
from google.cloud import texttospeech
from app.config import Config


class TTSClient:
    """Client for Google Cloud Text-to-Speech API with voice quality selection."""
    
    def __init__(self, voice_preset: str = "premium_female", speech_rate: float = 1.0,
                 language_code: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the TTS client.
        
        Args:
            voice_preset: Voice preset key from Config.VOICE_PRESETS. Defaults to 'premium_female'.
            speech_rate: Speaking rate multiplier. Defaults to 1.0.
            language_code: Language code. Defaults to config value.
            cache_dir: Directory for caching audio files.
        """
        from app.config import Config
        
        preset = Config.VOICE_PRESETS.get(voice_preset, Config.VOICE_PRESETS["premium_female"])
        self.voice_name = preset["name"]
        self.supports_rate = preset["supports_rate"]
        self.cost_per_char = preset["cost_per_char"]
        self.speech_rate = speech_rate if self.supports_rate else None
        
        self.language_code = language_code or Config.TTS_LANGUAGE_CODE
        self.cache_dir = cache_dir or Config.AUDIO_CACHE_DIR
        
        # Initialize client
        self.client = texttospeech.TextToSpeechClient()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def synthesize(self, text: str) -> Tuple[str, int]:
        """
        Convert text to speech and save as MP3.
        Uses content-hash caching to avoid re-synthesizing identical text.
        
        Args:
            text: Text to convert to speech
        
        Returns:
            Tuple of (URL path to audio file, character count)
        """
        char_count = len(text)
        
        # Generate cache key from text content AND voice name
        cache_key = hashlib.md5(f"{text}:{self.voice_name}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        # Return cached if exists
        if os.path.exists(cache_path):
            return f"/audio/{cache_key}.mp3", char_count
        
        # Synthesize
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name
        )
        
        # Build audio config - only include speaking_rate if supported
        if self.speech_rate is not None:
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.speech_rate
            )
        else:
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
        
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to cache
        with open(cache_path, "wb") as f:
            f.write(response.audio_content)
        
        return f"/audio/{cache_key}.mp3", char_count
    
    def calculate_cost(self, char_count: int) -> float:
        """
        Calculate cost for synthesizing text.
        
        Args:
            char_count: Number of characters synthesized
        
        Returns:
            Estimated cost in USD
        """
        return char_count * self.cost_per_char
    
    def get_audio_path(self, url: str) -> str:
        """
        Get the full filesystem path for an audio URL.
        
        Args:
            url: Audio URL path (e.g., /audio/abc123.mp3)
        
        Returns:
            Full filesystem path to the audio file
        """
        filename = url.split("/")[-1]
        return os.path.join(self.cache_dir, filename)
    
    def clear_cache(self) -> int:
        """
        Clear all cached audio files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".mp3"):
                os.remove(os.path.join(self.cache_dir, filename))
                count += 1
        return count
