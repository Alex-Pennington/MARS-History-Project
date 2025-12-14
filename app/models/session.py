"""
Session model for interview sessions.
"""

import json
from datetime import datetime
from typing import Optional, List


class Session:
    """Model for interview session records."""
    
    @staticmethod
    def create(db, session_id: str, expert_name: str, 
               expert_callsign: Optional[str] = None, topics: Optional[list] = None,
               voice_preset: str = 'premium_female', speech_rate: float = 0.95) -> dict:
        """
        Create a new interview session.
        
        Args:
            db: Database connection
            session_id: UUID for the session
            expert_name: Name of the expert
            expert_callsign: Optional callsign
            topics: Optional list of topics
            voice_preset: Voice preset key (e.g., 'premium_female')
            speech_rate: Speaking rate (0.5 to 1.5)
        
        Returns:
            Created session dict
        """
        cursor = db.cursor()
        
        topics_json = json.dumps(topics) if topics else None
        
        cursor.execute("""
            INSERT INTO sessions (id, expert_name, expert_callsign, topics, voice_preset,
                                  speech_rate, total_chars_synthesized, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0.0)
        """, (session_id, expert_name, expert_callsign, topics_json, voice_preset, speech_rate))
        
        db.commit()
        
        return Session.get_by_id(db, session_id)
    
    @staticmethod
    def get_by_id(db, session_id: str) -> Optional[dict]:
        """
        Get a session by ID.
        
        Args:
            db: Database connection
            session_id: The session ID
        
        Returns:
            Session dict or None
        """
        cursor = db.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        session = dict(row)
        
        # Parse JSON fields
        if session.get("topics"):
            session["topics"] = json.loads(session["topics"])
        if session.get("extracted_knowledge"):
            session["extracted_knowledge"] = json.loads(session["extracted_knowledge"])
        
        return session
    
    @staticmethod
    def get_all(db, status: Optional[str] = None) -> List[dict]:
        """
        Get all sessions, optionally filtered by status.
        
        Args:
            db: Database connection
            status: Optional status filter ('active', 'completed', 'abandoned')
        
        Returns:
            List of session dicts
        """
        cursor = db.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM sessions WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        sessions = []
        
        for row in rows:
            session = dict(row)
            if session.get("topics"):
                session["topics"] = json.loads(session["topics"])
            if session.get("extracted_knowledge"):
                session["extracted_knowledge"] = json.loads(session["extracted_knowledge"])
            sessions.append(session)
        
        return sessions
    
    @staticmethod
    def update(db, session_id: str, **kwargs) -> dict:
        """
        Update a session.
        
        Args:
            db: Database connection
            session_id: The session ID
            **kwargs: Fields to update
        
        Returns:
            Updated session dict
        """
        cursor = db.cursor()
        
        # Handle JSON fields
        if "topics" in kwargs and isinstance(kwargs["topics"], list):
            kwargs["topics"] = json.dumps(kwargs["topics"])
        if "extracted_knowledge" in kwargs and isinstance(kwargs["extracted_knowledge"], dict):
            kwargs["extracted_knowledge"] = json.dumps(kwargs["extracted_knowledge"])
        
        # Add updated_at
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        
        # Build update query
        set_clauses = [f"{key} = ?" for key in kwargs.keys()]
        values = list(kwargs.values()) + [session_id]
        
        cursor.execute(f"""
            UPDATE sessions 
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """, values)
        
        db.commit()
        
        return Session.get_by_id(db, session_id)
    
    @staticmethod
    def delete(db, session_id: str) -> bool:
        """
        Delete a session and its messages.
        
        Args:
            db: Database connection
            session_id: The session ID
        
        Returns:
            True if deleted
        """
        cursor = db.cursor()
        
        # Delete messages first (foreign key)
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM extractions WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        
        db.commit()
        
        return cursor.rowcount > 0
    
    @staticmethod
    def update_cost(db, session_id: str, chars_synthesized: int, cost: float) -> dict:
        """
        Increment the TTS cost tracking for a session.
        
        Args:
            db: Database connection
            session_id: The session ID
            chars_synthesized: Number of characters just synthesized
            cost: Cost for these characters
        
        Returns:
            Updated session dict with new totals
        """
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE sessions 
            SET total_chars_synthesized = total_chars_synthesized + ?,
                estimated_cost = estimated_cost + ?,
                updated_at = ?
            WHERE id = ?
        """, (chars_synthesized, cost, datetime.utcnow().isoformat(), session_id))
        
        db.commit()
        
        return Session.get_by_id(db, session_id)
