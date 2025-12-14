"""
Tests for TTSClient.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock


class TestTTSClient:
    """Test cases for TTSClient."""
    
    @patch('app.services.tts_client.texttospeech.TextToSpeechClient')
    def test_synthesize_returns_url(self, mock_tts_class):
        """Test that synthesize returns a URL path."""
        from app.services.tts_client import TTSClient
        
        # Create temp directory for cache
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = Mock()
            mock_tts_class.return_value = mock_client
            mock_response = Mock()
            mock_response.audio_content = b"fake audio content"
            mock_client.synthesize_speech.return_value = mock_response
            
            client = TTSClient(cache_dir=tmpdir)
            url = client.synthesize("Hello world")
            
            assert url.startswith("/audio/")
            assert url.endswith(".mp3")
    
    @patch('app.services.tts_client.texttospeech.TextToSpeechClient')
    def test_synthesize_caches_result(self, mock_tts_class):
        """Test that repeated calls use cache."""
        from app.services.tts_client import TTSClient
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = Mock()
            mock_tts_class.return_value = mock_client
            mock_response = Mock()
            mock_response.audio_content = b"fake audio"
            mock_client.synthesize_speech.return_value = mock_response
            
            client = TTSClient(cache_dir=tmpdir)
            
            # First call should synthesize
            url1 = client.synthesize("Test text")
            assert mock_client.synthesize_speech.call_count == 1
            
            # Second call with same text should use cache
            url2 = client.synthesize("Test text")
            assert mock_client.synthesize_speech.call_count == 1
            assert url1 == url2
    
    @patch('app.services.tts_client.texttospeech.TextToSpeechClient')
    def test_synthesize_different_texts(self, mock_tts_class):
        """Test that different texts get different URLs."""
        from app.services.tts_client import TTSClient
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = Mock()
            mock_tts_class.return_value = mock_client
            mock_response = Mock()
            mock_response.audio_content = b"audio"
            mock_client.synthesize_speech.return_value = mock_response
            
            client = TTSClient(cache_dir=tmpdir)
            
            url1 = client.synthesize("Hello")
            url2 = client.synthesize("World")
            
            assert url1 != url2
            assert mock_client.synthesize_speech.call_count == 2
    
    @patch('app.services.tts_client.texttospeech.TextToSpeechClient')
    def test_clear_cache(self, mock_tts_class):
        """Test cache clearing."""
        from app.services.tts_client import TTSClient
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = Mock()
            mock_tts_class.return_value = mock_client
            mock_response = Mock()
            mock_response.audio_content = b"audio"
            mock_client.synthesize_speech.return_value = mock_response
            
            client = TTSClient(cache_dir=tmpdir)
            
            # Create some cached files
            client.synthesize("Text 1")
            client.synthesize("Text 2")
            
            # Clear cache
            deleted = client.clear_cache()
            
            assert deleted == 2
            assert len(os.listdir(tmpdir)) == 0
