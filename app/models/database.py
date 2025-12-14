"""
Database setup and connection management for SQLite.
"""

import sqlite3
import os
from app.config import Config


# Thread-local storage for database connections
_db_connection = None


def get_db() -> sqlite3.Connection:
    """
    Get a database connection.
    
    Returns:
        SQLite database connection
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = sqlite3.connect(
            Config.DATABASE_PATH,
            check_same_thread=False
        )
        _db_connection.row_factory = sqlite3.Row
    
    return _db_connection


def init_db():
    """
    Initialize the database with the required schema.
    Creates tables if they don't exist.
    """
    # Ensure data directory exists
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    db = get_db()
    cursor = db.cursor()
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            expert_name TEXT NOT NULL,
            expert_callsign TEXT,
            topics TEXT,
            status TEXT DEFAULT 'active',
            extracted_knowledge TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            total_duration_seconds INTEGER,
            voice_preset TEXT DEFAULT 'premium_female',
            speech_rate REAL DEFAULT 0.95,
            total_chars_synthesized INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0.0
        )
    """)
    
    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            audio_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Create extractions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            extraction_data TEXT NOT NULL,
            message_range_start INTEGER,
            message_range_end INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_session 
        ON messages(session_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_extractions_session 
        ON extractions(session_id)
    """)
    
    db.commit()
    
    # Run migrations for existing databases
    _run_migrations(db)


def _run_migrations(db):
    """
    Run database migrations to add new columns to existing tables.
    Safe to run multiple times - checks each column individually.
    """
    cursor = db.cursor()
    
    # Get existing column names
    cursor.execute("PRAGMA table_info(sessions)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add voice_preset if missing
    if 'voice_preset' not in existing_columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN voice_preset TEXT DEFAULT 'premium_female'")
    
    # Add speech_rate if missing
    if 'speech_rate' not in existing_columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN speech_rate REAL DEFAULT 0.95")
    
    # Add total_chars_synthesized if missing
    if 'total_chars_synthesized' not in existing_columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN total_chars_synthesized INTEGER DEFAULT 0")
    
    # Add estimated_cost if missing
    if 'estimated_cost' not in existing_columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN estimated_cost REAL DEFAULT 0.0")
    
    db.commit()
    
    # Migrate old voice_quality column to voice_preset if it exists
    if 'voice_quality' in existing_columns:
        cursor.execute("UPDATE sessions SET voice_preset = 'standard_male' WHERE voice_quality = 'standard' AND voice_preset IS NULL")
        cursor.execute("UPDATE sessions SET voice_preset = 'premium_female' WHERE voice_quality = 'natural' AND voice_preset IS NULL")
        db.commit()


def close_db():
    """Close the database connection."""
    global _db_connection
    
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None
