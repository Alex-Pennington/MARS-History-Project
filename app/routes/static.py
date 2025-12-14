"""
Static file serving routes.
Serves the frontend interview page and audio files.
"""

import os
from flask import Blueprint, send_from_directory, send_file, render_template
from app.config import Config

static_bp = Blueprint('static_routes', __name__)

# Get the base directory for templates and static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Audio cache directory - use absolute path for Docker compatibility
AUDIO_DIR = '/app/data/audio_cache' if os.path.exists('/app/data') else os.path.join(BASE_DIR, 'data', 'audio_cache')


@static_bp.route('/')
def index():
    """Serve the main interview page."""
    return send_from_directory(TEMPLATES_DIR, 'interview.html')


@static_bp.route('/static/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(os.path.join(STATIC_DIR, 'css'), filename)


@static_bp.route('/static/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory(os.path.join(STATIC_DIR, 'js'), filename)


@static_bp.route('/audio/<filename>')
def serve_audio(filename):
    """
    Serve cached TTS audio files.
    
    Args:
        filename: The audio file name (e.g., 'abc123.mp3')
    """
    audio_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(audio_path):
        return {"error": "Audio file not found", "path": audio_path}, 404
    
    return send_file(
        audio_path,
        mimetype='audio/mpeg',
        as_attachment=False
    )


@static_bp.route('/health')
def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "sme-interview-system"}
