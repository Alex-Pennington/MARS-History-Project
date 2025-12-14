"""
Message model for interview conversation messages.
"""

from typing import List, Optional


class Message:
    """Model for conversation message records."""
    
    @staticmethod
    def create(db, session_id: str, role: str, content: str, 
               audio_path: Optional[str] = None) -> dict:
        """
        Create a new message.
        
        Args:
            db: Database connection
            session_id: The session this message belongs to
            role: 'user' or 'assistant'
            content: Message text content
            audio_path: Optional path to TTS audio file
        
        Returns:
            Created message dict
        """
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, audio_path)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, audio_path))
        
        db.commit()
        
        return Message.get_by_id(db, cursor.lastrowid)
    
    @staticmethod
    def get_by_id(db, message_id: int) -> Optional[dict]:
        """
        Get a message by ID.
        
        Args:
            db: Database connection
            message_id: The message ID
        
        Returns:
            Message dict or None
        """
        cursor = db.cursor()
        cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    @staticmethod
    def get_by_session(db, session_id: str) -> List[dict]:
        """
        Get all messages for a session.
        
        Args:
            db: Database connection
            session_id: The session ID
        
        Returns:
            List of message dicts, ordered by creation time
        """
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC
        """, (session_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_recent(db, session_id: str, limit: int = 30) -> List[dict]:
        """
        Get recent messages for a session.
        
        Args:
            db: Database connection
            session_id: The session ID
            limit: Maximum number of messages to return
        
        Returns:
            List of recent message dicts
        """
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM messages 
            WHERE session_id = ? 
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit))
        
        # Reverse to get chronological order
        return [dict(row) for row in reversed(cursor.fetchall())]
    
    @staticmethod
    def count_by_session(db, session_id: str) -> int:
        """
        Count messages in a session.
        
        Args:
            db: Database connection
            session_id: The session ID
        
        Returns:
            Number of messages
        """
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
            (session_id,)
        )
        return cursor.fetchone()[0]
    
    @staticmethod
    def delete_by_session(db, session_id: str) -> int:
        """
        Delete all messages for a session.
        
        Args:
            db: Database connection
            session_id: The session ID
        
        Returns:
            Number of messages deleted
        """
        cursor = db.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        db.commit()
        return cursor.rowcount
    
    @staticmethod
    def to_claude_format(messages: List[dict]) -> List[dict]:
        """
        Convert message dicts to Claude API format.
        
        Args:
            messages: List of message dicts from database
        
        Returns:
            List of dicts with 'role' and 'content' keys only
        """
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]
