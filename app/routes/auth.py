"""Authentication routes for token-based access control."""

from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from functools import wraps
from app.services.token_manager import validate_token, increment_session_count
from app.config import Config

bp = Blueprint('auth', __name__)


def require_auth(f):
    """Decorator to require valid session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.REQUIRE_AUTH:
            return f(*args, **kwargs)
        
        if not session.get('authenticated'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('auth.auth_page'))
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
def index():
    """Root route - redirect based on auth status."""
    if not Config.REQUIRE_AUTH or session.get('authenticated'):
        return redirect(url_for('auth.interview_page'))
    return redirect(url_for('auth.auth_page'))


@bp.route('/auth')
def auth_page():
    """Token entry page."""
    if session.get('authenticated'):
        return redirect(url_for('auth.interview_page'))
    return render_template('auth.html')


@bp.route('/interview')
@require_auth
def interview_page():
    """Main interview page - requires auth."""
    return render_template('interview.html')


@bp.route('/api/auth', methods=['POST'])
def authenticate():
    """Validate token and create session."""
    data = request.get_json()
    token = data.get('token', '').strip()
    
    user_info = validate_token(token)
    
    if user_info:
        session['authenticated'] = True
        session['token'] = token
        session['user_name'] = user_info['name']
        session['user_callsign'] = user_info.get('callsign')
        session.permanent = True
        return jsonify({
            'success': True,
            'name': user_info['name'],
            'callsign': user_info.get('callsign')
        })
    
    return jsonify({'error': 'Invalid token'}), 401


@bp.route('/api/logout', methods=['POST'])
def logout():
    """Clear session and logout."""
    session.clear()
    return jsonify({'success': True})


@bp.route('/api/auth/status')
def auth_status():
    """Check current auth status."""
    if session.get('authenticated'):
        return jsonify({
            'authenticated': True,
            'name': session.get('user_name'),
            'callsign': session.get('user_callsign')
        })
    return jsonify({'authenticated': False})
