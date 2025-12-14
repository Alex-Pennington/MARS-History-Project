"""
ClaudeClient wraps the Anthropic API for interview use.
"""

from typing import Optional
import anthropic
from app.config import Config


class ClaudeClient:
    """Client for interacting with Claude API."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Claude client.
        
        Args:
            api_key: Anthropic API key. Defaults to config value.
            model: Claude model to use. Defaults to config value.
        """
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        self.model = model or Config.CLAUDE_MODEL
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def send_message(self, messages: list, max_tokens: Optional[int] = None, 
                     system_prompt: Optional[str] = None) -> str:
        """
        Send messages to Claude and get response.
        
        Args:
            messages: List of {"role": str, "content": str} dicts
            max_tokens: Max response length (keep short for interviews)
            system_prompt: Optional system prompt to include
        
        Returns:
            Response text string
        """
        max_tokens = max_tokens or Config.CLAUDE_MAX_TOKENS
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text
    
    def send_with_context(self, messages: list, system_prompt: str,
                          extracted_knowledge: Optional[dict] = None,
                          max_tokens: Optional[int] = None) -> str:
        """
        Send messages with context for interview continuation.
        
        Args:
            messages: Recent conversation messages
            system_prompt: The interviewer system prompt
            extracted_knowledge: Previously extracted knowledge to include
            max_tokens: Max response length
        
        Returns:
            Response text string
        """
        # Build full system prompt with knowledge context
        full_system = system_prompt
        
        if extracted_knowledge:
            knowledge_summary = self._format_knowledge(extracted_knowledge)
            full_system = f"{system_prompt}\n\n## KNOWLEDGE CAPTURED SO FAR\n{knowledge_summary}"
        
        return self.send_message(
            messages=messages,
            max_tokens=max_tokens,
            system_prompt=full_system
        )
    
    def _format_knowledge(self, knowledge: dict) -> str:
        """Format extracted knowledge for inclusion in context."""
        sections = []
        
        if knowledge.get("topics_discussed"):
            sections.append(f"Topics: {', '.join(knowledge['topics_discussed'])}")
        
        if knowledge.get("key_insights"):
            insights = [f"- {i['topic']}: {i['insight']}" 
                       for i in knowledge['key_insights'][:5]]
            sections.append(f"Key Insights:\n" + "\n".join(insights))
        
        if knowledge.get("people_mentioned"):
            people = [f"- {p['name']} ({p.get('callsign', 'N/A')})" 
                     for p in knowledge['people_mentioned']]
            sections.append(f"People Mentioned:\n" + "\n".join(people))
        
        if knowledge.get("open_questions"):
            questions = [f"- {q}" for q in knowledge['open_questions'][:3]]
            sections.append(f"Questions to Follow Up:\n" + "\n".join(questions))
        
        return "\n\n".join(sections) if sections else "No knowledge extracted yet."
