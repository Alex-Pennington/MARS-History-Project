"""
Prompts package for SME Interview System.
Contains system prompts for AI interviewer and knowledge extraction.
"""

from app.prompts.interviewer import INTERVIEWER_SYSTEM_PROMPT
from app.prompts.extractor import EXTRACTOR_SYSTEM_PROMPT

__all__ = ['INTERVIEWER_SYSTEM_PROMPT', 'EXTRACTOR_SYSTEM_PROMPT']
