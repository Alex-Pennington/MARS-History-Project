"""
Routes package for SME Interview System.
Contains API endpoints for interviews, sessions, and static file serving.
"""

from flask import Blueprint

# Create blueprints
interview_bp = Blueprint('interview', __name__)
sessions_bp = Blueprint('sessions', __name__)
static_bp = Blueprint('static_routes', __name__)

# Import route handlers to register them
from app.routes import interview, sessions, static
