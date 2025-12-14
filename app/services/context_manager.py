"""
ContextManager maintains interview quality over extended conversations by:
- Keeping a sliding window of recent messages
- Periodically extracting and summarizing knowledge
- Injecting extracted knowledge back into context
"""

from typing import Optional
from app.config import Config


class ContextManager:
    """Manages conversation context for long interviews."""
    
    def __init__(self, max_messages: Optional[int] = None, extraction_interval: Optional[int] = None):
        """
        Initialize the context manager.
        
        Args:
            max_messages: Maximum message pairs to keep in sliding window.
            extraction_interval: Extract knowledge every N exchanges.
        """
        self.max_messages = max_messages or Config.MAX_CONTEXT_MESSAGES
        self.extraction_interval = extraction_interval or Config.EXTRACTION_INTERVAL
    
    def build_context(self, all_messages: list, extracted_knowledge: Optional[dict] = None) -> list:
        """
        Build the messages array for Claude API call.
        Uses a sliding window approach to keep context manageable.
        
        Args:
            all_messages: All messages from the session
            extracted_knowledge: Previously extracted knowledge
        
        Returns:
            List of message dicts for Claude API (only 'role' and 'content')
        """
        # Apply sliding window - keep last N messages
        if len(all_messages) > self.max_messages:
            # Keep the most recent messages
            windowed_messages = all_messages[-self.max_messages:]
        else:
            windowed_messages = all_messages
        
        # Strip to only role and content for Claude API
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in windowed_messages
        ]
    
    def should_extract(self, message_count: int) -> bool:
        """
        Check if we should run knowledge extraction.
        
        Args:
            message_count: Total number of messages in session
        
        Returns:
            True if extraction should run
        """
        # Extract every N exchanges (user + assistant = 2 messages per exchange)
        exchanges = message_count // 2
        return exchanges > 0 and exchanges % self.extraction_interval == 0
    
    def get_messages_for_extraction(self, all_messages: list, 
                                     last_extraction_index: int = 0) -> list:
        """
        Get messages that need to be extracted.
        
        Args:
            all_messages: All messages from the session
            last_extraction_index: Index of last extracted message
        
        Returns:
            List of messages to extract knowledge from
        """
        return all_messages[last_extraction_index:]
    
    def estimate_tokens(self, messages: list) -> int:
        """
        Estimate token count for a list of messages.
        Rough estimate: ~4 characters per token.
        
        Args:
            messages: List of message dicts
        
        Returns:
            Estimated token count
        """
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4
