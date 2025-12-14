"""
Models package for SME Interview System.
Contains database setup and data models.
"""

from app.models.database import init_db, get_db
from app.models.session import Session
from app.models.message import Message

__all__ = ['init_db', 'get_db', 'Session', 'Message']
