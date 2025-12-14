"""
Tests for ClaudeClient.
"""

import pytest
from unittest.mock import Mock, patch


class TestClaudeClient:
    """Test cases for ClaudeClient."""
    
    @patch('app.services.claude_client.anthropic.Anthropic')
    def test_send_message_basic(self, mock_anthropic):
        """Test basic message sending."""
        from app.services.claude_client import ClaudeClient
        
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        
        # Create client and send message
        client = ClaudeClient(api_key="test-key")
        response = client.send_message([
            {"role": "user", "content": "Hello"}
        ])
        
        assert response == "Test response"
        mock_client.messages.create.assert_called_once()
    
    @patch('app.services.claude_client.anthropic.Anthropic')
    def test_send_with_system_prompt(self, mock_anthropic):
        """Test message sending with system prompt."""
        from app.services.claude_client import ClaudeClient
        
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response
        
        client = ClaudeClient(api_key="test-key")
        client.send_message(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are a helpful assistant."
        )
        
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" in call_kwargs
        assert call_kwargs["system"] == "You are a helpful assistant."
    
    @patch('app.services.claude_client.anthropic.Anthropic')
    def test_format_knowledge_empty(self, mock_anthropic):
        """Test knowledge formatting with empty dict."""
        from app.services.claude_client import ClaudeClient
        
        client = ClaudeClient(api_key="test-key")
        result = client._format_knowledge({})
        
        assert result == "No knowledge extracted yet."
    
    @patch('app.services.claude_client.anthropic.Anthropic')
    def test_format_knowledge_with_topics(self, mock_anthropic):
        """Test knowledge formatting with topics."""
        from app.services.claude_client import ClaudeClient
        
        client = ClaudeClient(api_key="test-key")
        knowledge = {
            "topics_discussed": ["ALE", "MS-DMT"],
            "key_insights": [
                {"topic": "ALE", "insight": "Important detail"}
            ]
        }
        result = client._format_knowledge(knowledge)
        
        assert "Topics: ALE, MS-DMT" in result
        assert "ALE: Important detail" in result
