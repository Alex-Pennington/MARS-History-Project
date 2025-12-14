"""
InterviewManager handles the core interview logic:
- Creating and managing interview sessions
- Processing user input through Claude
- Managing conversation context
- Triggering knowledge extraction
- Generating TTS audio
"""

import uuid
from datetime import datetime
from typing import Optional

from app.services.claude_client import ClaudeClient
from app.services.tts_client import TTSClient
from app.services.context_manager import ContextManager
from app.services.knowledge_extractor import KnowledgeExtractor
from app.models.database import get_db
from app.models.session import Session
from app.models.message import Message
from app.prompts.interviewer import INTERVIEWER_SYSTEM_PROMPT


class InterviewManager:
    """Central orchestrator for interview sessions."""
    
    def __init__(self, claude_client: Optional[ClaudeClient] = None, 
                 tts_client: Optional[TTSClient] = None):
        """
        Initialize the interview manager.
        
        Args:
            claude_client: ClaudeClient instance (creates new if None)
            tts_client: TTSClient instance (creates new if None)
        """
        self.claude = claude_client or ClaudeClient()
        # TTS client will be created per-session with voice quality
        self._tts_client = tts_client
        self.context_manager = ContextManager()
        self.extractor = KnowledgeExtractor(self.claude)
        # Cache of TTS clients per voice preset + speech rate
        self._tts_clients = {}
    
    def _get_tts_client(self, voice_preset: str = 'premium_female', speech_rate: float = 1.0) -> TTSClient:
        """Get or create a TTS client for the given voice preset and speech rate."""
        if self._tts_client:
            return self._tts_client
        cache_key = f"{voice_preset}_{speech_rate}"
        if cache_key not in self._tts_clients:
            self._tts_clients[cache_key] = TTSClient(voice_preset=voice_preset, speech_rate=speech_rate)
        return self._tts_clients[cache_key]
    
    def create_session(self, expert_name: str, expert_callsign: Optional[str] = None,
                       topics: Optional[list] = None, voice_preset: str = 'premium_female',
                       speech_rate: float = 0.95) -> dict:
        """
        Create a new interview session.
        
        Args:
            expert_name: Name of the expert being interviewed
            expert_callsign: Optional callsign of the expert
            topics: Optional list of topics to cover
            voice_preset: Voice preset key (e.g., 'premium_female')
            speech_rate: Speaking rate (0.5 to 1.5)
        
        Returns:
            Dict with session_id, greeting text, audio_url, and cost info
        """
        session_id = str(uuid.uuid4())
        
        # Get the TTS client for this voice preset
        tts = self._get_tts_client(voice_preset, speech_rate)
        
        # Create session in database
        db = get_db()
        Session.create(
            db,
            session_id=session_id,
            expert_name=expert_name,
            expert_callsign=expert_callsign,
            topics=topics,
            voice_preset=voice_preset,
            speech_rate=speech_rate
        )
        
        # Generate personalized greeting
        greeting = self._generate_greeting(expert_name, expert_callsign, topics)
        
        # Save greeting as first assistant message
        Message.create(db, session_id, "assistant", greeting)
        
        # Generate TTS audio for greeting (returns tuple: url, char_count)
        audio_url, char_count = tts.synthesize(greeting)
        
        # Update cost tracking
        cost = tts.calculate_cost(char_count)
        Session.update_cost(db, session_id, char_count, cost)
        
        # Get updated session with cost info
        session = Session.get_by_id(db, session_id)
        
        return {
            "session_id": session_id,
            "greeting": greeting,
            "audio_url": audio_url,
            "voice_preset": voice_preset,
            "speech_rate": speech_rate,
            "session_cost": round(session.get("estimated_cost", 0), 4),
            "chars_synthesized": session.get("total_chars_synthesized", 0)
        }
    
    def process_input(self, session_id: str, user_text: str) -> dict:
        """
        Process expert's spoken input.
        
        Args:
            session_id: The session ID
            user_text: Transcribed text from expert
        
        Returns:
            Dict with response_text, audio_url, message_count, extraction_triggered, cost info
        """
        db = get_db()
        
        # 1. Get session to get voice preset and speech rate
        session = Session.get_by_id(db, session_id)
        voice_preset = session.get("voice_preset", "premium_female")
        speech_rate = session.get("speech_rate", 0.95)
        tts = self._get_tts_client(voice_preset, speech_rate)
        
        # 2. Save user message to DB
        Message.create(db, session_id, "user", user_text)
        
        # 3. Get all messages for this session
        all_messages = Message.get_by_session(db, session_id)
        message_count = len(all_messages)
        
        # 4. Get extracted knowledge for context
        extracted_knowledge = session.get("extracted_knowledge")
        
        # 5. Build context with sliding window
        context_messages = self.context_manager.build_context(
            all_messages, extracted_knowledge
        )
        
        # 6. Call Claude API
        response_text = self.claude.send_with_context(
            messages=context_messages,
            system_prompt=INTERVIEWER_SYSTEM_PROMPT,
            extracted_knowledge=extracted_knowledge
        )
        
        # 7. Save assistant message to DB
        Message.create(db, session_id, "assistant", response_text)
        
        # 8. Generate TTS audio (returns tuple: url, char_count)
        audio_url, char_count = tts.synthesize(response_text)
        
        # 9. Update cost tracking
        cost = tts.calculate_cost(char_count)
        updated_session = Session.update_cost(db, session_id, char_count, cost)
        
        # 10. Check if extraction should run
        extraction_triggered = False
        if self.context_manager.should_extract(message_count + 1):
            self._run_extraction(session_id)
            extraction_triggered = True
        
        return {
            "response_text": response_text,
            "audio_url": audio_url,
            "session_id": session_id,
            "message_count": (message_count + 2) // 2,  # Count exchanges, not messages
            "extraction_triggered": extraction_triggered,
            "chars_this_response": char_count,
            "session_cost": round(updated_session.get("estimated_cost", 0), 4),
            "total_chars": updated_session.get("total_chars_synthesized", 0)
        }
    
    def get_transcript(self, session_id: str) -> dict:
        """
        Get full conversation transcript for a session.
        
        Args:
            session_id: The session ID
        
        Returns:
            Dict with session info and messages
        """
        db = get_db()
        session = Session.get_by_id(db, session_id)
        messages = Message.get_by_session(db, session_id)
        
        return {
            "session_id": session_id,
            "expert_name": session.get("expert_name"),
            "expert_callsign": session.get("expert_callsign"),
            "created_at": session.get("created_at"),
            "status": session.get("status"),
            "messages": [
                {
                    "role": m["role"],
                    "content": m["content"],
                    "timestamp": m["created_at"]
                }
                for m in messages
            ]
        }
    
    def get_extracted_knowledge(self, session_id: str) -> dict:
        """
        Get all extracted knowledge for a session.
        
        Args:
            session_id: The session ID
        
        Returns:
            Extracted knowledge dict
        """
        db = get_db()
        session = Session.get_by_id(db, session_id)
        return session.get("extracted_knowledge") or {
            "topics_discussed": [],
            "key_insights": [],
            "people_mentioned": [],
            "technical_details": [],
            "lessons_learned": [],
            "open_questions": [],
            "follow_up_topics": []
        }
    
    def end_session(self, session_id: str) -> dict:
        """
        End an interview session.
        
        Args:
            session_id: The session ID
        
        Returns:
            Dict with final session stats
        """
        db = get_db()
        
        # Run final extraction
        self._run_extraction(session_id)
        
        # Update session status
        session = Session.get_by_id(db, session_id)
        messages = Message.get_by_session(db, session_id)
        
        # Calculate duration
        if messages:
            start_time = datetime.fromisoformat(messages[0]["created_at"])
            end_time = datetime.fromisoformat(messages[-1]["created_at"])
            duration_seconds = int((end_time - start_time).total_seconds())
        else:
            duration_seconds = 0
        
        Session.update(db, session_id, 
                      status="completed",
                      ended_at=datetime.utcnow().isoformat(),
                      message_count=len(messages),
                      total_duration_seconds=duration_seconds)
        
        # Get updated session for cost info
        final_session = Session.get_by_id(db, session_id)
        
        return {
            "session_id": session_id,
            "status": "completed",
            "message_count": len(messages) // 2,  # Exchanges
            "duration_seconds": duration_seconds,
            "transcript_url": f"/api/transcript/{session_id}",
            "extraction_url": f"/api/extraction/{session_id}",
            "total_chars_synthesized": final_session.get("total_chars_synthesized", 0),
            "total_cost": round(final_session.get("estimated_cost", 0), 4),
            "voice_quality": final_session.get("voice_quality", "natural")
        }
    
    def _generate_greeting(self, expert_name: str, expert_callsign: Optional[str] = None,
                          topics: Optional[list] = None) -> str:
        """Generate a personalized greeting for the interview."""
        name_to_use = expert_callsign or expert_name.split()[0]
        
        greeting = f"Hello {name_to_use}, thank you for joining us today for the MARS Digital History Project. "
        greeting += "I'm looking forward to learning about your experiences and capturing your valuable knowledge. "
        
        if topics:
            topics_str = ", ".join(topics[:2])
            greeting += f"I understand you have expertise in {topics_str}. "
        
        greeting += "Before we begin, could you tell me a bit about how you first got involved in HF digital communications?"
        
        return greeting
    
    def _run_extraction(self, session_id: str) -> None:
        """Run knowledge extraction for a session."""
        db = get_db()
        session = Session.get_by_id(db, session_id)
        messages = Message.get_by_session(db, session_id)
        
        existing_knowledge = session.get("extracted_knowledge")
        
        # Get messages to extract (could be optimized to only extract new ones)
        messages_to_extract = [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-20:]  # Last 20 messages
        ]
        
        # Extract knowledge
        new_knowledge = self.extractor.extract(messages_to_extract, existing_knowledge)
        
        # Merge with existing
        merged_knowledge = self.extractor.merge_knowledge(existing_knowledge, new_knowledge)
        
        # Update session
        Session.update(db, session_id, extracted_knowledge=merged_knowledge)
