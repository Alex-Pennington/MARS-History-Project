"""
KnowledgeExtractor uses Claude to extract structured knowledge from
interview segments. This serves two purposes:
1. Preserves knowledge as context window slides
2. Produces final documentation output
"""

import json
from typing import Optional
from app.prompts.extractor import EXTRACTOR_SYSTEM_PROMPT


class KnowledgeExtractor:
    """Extracts structured knowledge from interview conversations."""
    
    def __init__(self, claude_client):
        """
        Initialize the knowledge extractor.
        
        Args:
            claude_client: ClaudeClient instance for API calls
        """
        self.claude = claude_client
    
    def extract(self, messages: list, existing_knowledge: Optional[dict] = None) -> dict:
        """
        Extract structured knowledge from a conversation segment.
        
        Args:
            messages: List of conversation messages to extract from
            existing_knowledge: Previously extracted knowledge to consider
        
        Returns:
            Extracted knowledge dict with topics, insights, people, etc.
        """
        # Format messages for extraction
        conversation_text = self._format_conversation(messages)
        
        # Build extraction prompt
        prompt = f"""Please extract structured knowledge from this interview segment.

## CONVERSATION SEGMENT
{conversation_text}

## EXISTING KNOWLEDGE (for context, don't repeat)
{json.dumps(existing_knowledge, indent=2) if existing_knowledge else "None yet"}

Please respond with a JSON object containing:
- topics_discussed: array of topic strings
- key_insights: array of {{topic, insight, source_quote, importance}}
- people_mentioned: array of {{name, callsign, context}}
- technical_details: array of {{system, detail, rationale}}
- lessons_learned: array of strings
- open_questions: array of strings
- follow_up_topics: array of strings

Respond ONLY with valid JSON, no other text."""

        # Call Claude for extraction
        response = self.claude.send_message(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            system_prompt=EXTRACTOR_SYSTEM_PROMPT
        )
        
        # Parse response
        try:
            extracted = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            extracted = self._extract_json_from_text(response)
        
        return extracted
    
    def merge_knowledge(self, existing: dict, new: dict) -> dict:
        """
        Merge new extraction with existing knowledge, deduplicating.
        
        Args:
            existing: Existing knowledge dict
            new: Newly extracted knowledge dict
        
        Returns:
            Merged knowledge dict
        """
        if not existing:
            return new
        if not new:
            return existing
        
        merged = {
            "topics_discussed": self._merge_unique(
                existing.get("topics_discussed", []),
                new.get("topics_discussed", [])
            ),
            "key_insights": self._merge_insights(
                existing.get("key_insights", []),
                new.get("key_insights", [])
            ),
            "people_mentioned": self._merge_people(
                existing.get("people_mentioned", []),
                new.get("people_mentioned", [])
            ),
            "technical_details": existing.get("technical_details", []) + 
                                 new.get("technical_details", []),
            "lessons_learned": self._merge_unique(
                existing.get("lessons_learned", []),
                new.get("lessons_learned", [])
            ),
            "open_questions": new.get("open_questions", []),  # Replace with latest
            "follow_up_topics": new.get("follow_up_topics", [])  # Replace with latest
        }
        
        return merged
    
    def _format_conversation(self, messages: list) -> str:
        """Format messages into readable conversation text."""
        lines = []
        for msg in messages:
            role = "Expert" if msg["role"] == "user" else "Interviewer"
            lines.append(f"{role}: {msg['content']}")
        return "\n\n".join(lines)
    
    def _merge_unique(self, list1: list, list2: list) -> list:
        """Merge two lists, removing duplicates while preserving order."""
        seen = set()
        result = []
        for item in list1 + list2:
            item_lower = item.lower() if isinstance(item, str) else str(item)
            if item_lower not in seen:
                seen.add(item_lower)
                result.append(item)
        return result
    
    def _merge_insights(self, existing: list, new: list) -> list:
        """Merge insights, avoiding duplicates by topic."""
        topics_seen = {i.get("topic", "").lower() for i in existing}
        result = list(existing)
        for insight in new:
            if insight.get("topic", "").lower() not in topics_seen:
                result.append(insight)
                topics_seen.add(insight.get("topic", "").lower())
        return result
    
    def _merge_people(self, existing: list, new: list) -> list:
        """Merge people lists, avoiding duplicates by name."""
        names_seen = {p.get("name", "").lower() for p in existing}
        result = list(existing)
        for person in new:
            if person.get("name", "").lower() not in names_seen:
                result.append(person)
                names_seen.add(person.get("name", "").lower())
        return result
    
    def _extract_json_from_text(self, text: str) -> dict:
        """Try to extract JSON from a text response."""
        # Try to find JSON in the response
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(text[start_idx:end_idx])
            except json.JSONDecodeError:
                pass
        
        # Return empty structure if parsing fails
        return {
            "topics_discussed": [],
            "key_insights": [],
            "people_mentioned": [],
            "technical_details": [],
            "lessons_learned": [],
            "open_questions": [],
            "follow_up_topics": []
        }
