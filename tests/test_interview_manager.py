"""
Tests for InterviewManager.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock


class TestInterviewManager:
    """Test cases for InterviewManager."""
    
    @pytest.fixture
    def mock_clients(self):
        """Create mock Claude and TTS clients."""
        claude_client = Mock()
        claude_client.send_with_context.return_value = "Interview question response"
        
        tts_client = Mock()
        tts_client.synthesize.return_value = "/audio/test123.mp3"
        
        return claude_client, tts_client
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            with patch('app.config.Config.DATABASE_PATH', db_path):
                from app.models.database import init_db, get_db
                init_db()
                yield get_db()
    
    @patch('app.services.interview_manager.get_db')
    def test_create_session(self, mock_get_db, mock_clients, temp_db):
        """Test session creation."""
        from app.services.interview_manager import InterviewManager
        
        mock_get_db.return_value = temp_db
        claude_client, tts_client = mock_clients
        
        manager = InterviewManager(claude_client, tts_client)
        result = manager.create_session(
            expert_name="Test Expert",
            expert_callsign="W1TEST"
        )
        
        assert "session_id" in result
        assert "greeting" in result
        assert "audio_url" in result
        assert "Test" in result["greeting"] or "W1TEST" in result["greeting"]
        tts_client.synthesize.assert_called_once()
    
    @patch('app.services.interview_manager.get_db')  
    def test_generate_greeting_with_callsign(self, mock_get_db, mock_clients):
        """Test greeting generation uses callsign when available."""
        from app.services.interview_manager import InterviewManager
        
        claude_client, tts_client = mock_clients
        manager = InterviewManager(claude_client, tts_client)
        
        greeting = manager._generate_greeting(
            expert_name="John Smith",
            expert_callsign="K1ABC"
        )
        
        assert "K1ABC" in greeting
    
    @patch('app.services.interview_manager.get_db')
    def test_generate_greeting_with_topics(self, mock_get_db, mock_clients):
        """Test greeting includes topics when provided."""
        from app.services.interview_manager import InterviewManager
        
        claude_client, tts_client = mock_clients
        manager = InterviewManager(claude_client, tts_client)
        
        greeting = manager._generate_greeting(
            expert_name="John",
            topics=["ALE", "MS-DMT"]
        )
        
        assert "ALE" in greeting or "expertise" in greeting


class TestContextManager:
    """Test cases for ContextManager."""
    
    def test_should_extract_at_interval(self):
        """Test extraction triggers at correct intervals."""
        from app.services.context_manager import ContextManager
        
        manager = ContextManager(extraction_interval=5)
        
        # Should not extract before interval
        assert not manager.should_extract(4)
        assert not manager.should_extract(8)
        
        # Should extract at interval (every 5 exchanges = 10 messages)
        assert manager.should_extract(10)
        assert manager.should_extract(20)
    
    def test_build_context_sliding_window(self):
        """Test sliding window limits context size."""
        from app.services.context_manager import ContextManager
        
        manager = ContextManager(max_messages=5)
        
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        context = manager.build_context(messages)
        
        assert len(context) == 5
        assert context[0]["content"] == "Message 5"  # Should have last 5
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        from app.services.context_manager import ContextManager
        
        manager = ContextManager()
        
        messages = [
            {"role": "user", "content": "Hello world"},  # ~11 chars
            {"role": "assistant", "content": "Hi there"}  # ~8 chars
        ]
        
        tokens = manager.estimate_tokens(messages)
        
        # ~19 chars / 4 = ~4 tokens
        assert 3 <= tokens <= 6


class TestKnowledgeExtractor:
    """Test cases for KnowledgeExtractor."""
    
    def test_merge_unique_deduplicates(self):
        """Test that merge_unique removes duplicates."""
        from app.services.knowledge_extractor import KnowledgeExtractor
        
        extractor = KnowledgeExtractor(Mock())
        
        list1 = ["ALE", "MS-DMT"]
        list2 = ["ale", "MARS-ALE"]  # 'ale' should be deduped
        
        result = extractor._merge_unique(list1, list2)
        
        assert len(result) == 3
        assert "ALE" in result
        assert "MS-DMT" in result
        assert "MARS-ALE" in result
    
    def test_merge_knowledge_combines_topics(self):
        """Test merging knowledge combines topics."""
        from app.services.knowledge_extractor import KnowledgeExtractor
        
        extractor = KnowledgeExtractor(Mock())
        
        existing = {"topics_discussed": ["ALE"]}
        new = {"topics_discussed": ["MS-DMT"]}
        
        result = extractor.merge_knowledge(existing, new)
        
        assert "ALE" in result["topics_discussed"]
        assert "MS-DMT" in result["topics_discussed"]
    
    def test_extract_json_from_text_handles_prefix(self):
        """Test JSON extraction handles text before JSON."""
        from app.services.knowledge_extractor import KnowledgeExtractor
        
        extractor = KnowledgeExtractor(Mock())
        
        text = 'Here is the JSON:\n{"topics_discussed": ["test"]}'
        result = extractor._extract_json_from_text(text)
        
        assert result["topics_discussed"] == ["test"]
