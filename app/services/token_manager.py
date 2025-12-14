"""Token management for access control.

Tokens are stored in a JSON file for easy management without server restart.
"""

import json
import os
import secrets
from datetime import datetime
from pathlib import Path


def _get_tokens_file() -> Path:
    """Get the tokens file path, checking config if available."""
    try:
        from app.config import Config
        return Path(Config.TOKENS_FILE)
    except ImportError:
        return Path(os.getenv('TOKENS_FILE', './data/tokens.json'))


def _load_tokens():
    """Load tokens from JSON file."""
    tokens_file = _get_tokens_file()
    if not tokens_file.exists():
        return {"tokens": {}}
    with open(tokens_file, 'r') as f:
        return json.load(f)


def _save_tokens(data):
    """Save tokens to JSON file."""
    tokens_file = _get_tokens_file()
    tokens_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tokens_file, 'w') as f:
        json.dump(data, f, indent=2)


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(16)


def add_token(name: str, callsign: str = None) -> str:
    """Create a new access token for a user."""
    data = _load_tokens()
    token = generate_token()
    
    data["tokens"][token] = {
        "name": name,
        "callsign": callsign,
        "created": datetime.now().isoformat(),
        "active": True,
        "last_used": None,
        "sessions_count": 0
    }
    
    _save_tokens(data)
    return token


def validate_token(token: str) -> dict | None:
    """Check if token is valid and active. Returns user info or None."""
    data = _load_tokens()
    token_data = data["tokens"].get(token)
    
    if token_data and token_data.get("active", False):
        # Update last_used
        token_data["last_used"] = datetime.now().isoformat()
        _save_tokens(data)
        return token_data
    
    return None


def increment_session_count(token: str):
    """Increment the session count for a token."""
    data = _load_tokens()
    if token in data["tokens"]:
        data["tokens"][token]["sessions_count"] = data["tokens"][token].get("sessions_count", 0) + 1
        _save_tokens(data)


def revoke_token(token: str) -> bool:
    """Deactivate a token."""
    data = _load_tokens()
    if token in data["tokens"]:
        data["tokens"][token]["active"] = False
        data["tokens"][token]["revoked"] = datetime.now().isoformat()
        _save_tokens(data)
        return True
    return False


def list_tokens() -> list:
    """List all tokens with their info."""
    data = _load_tokens()
    result = []
    for token, info in data["tokens"].items():
        result.append({
            "token": token,
            "token_short": token[:8] + "...",
            **info
        })
    return sorted(result, key=lambda x: x["created"], reverse=True)


def delete_token(token: str) -> bool:
    """Permanently delete a token."""
    data = _load_tokens()
    if token in data["tokens"]:
        del data["tokens"][token]
        _save_tokens(data)
        return True
    return False
