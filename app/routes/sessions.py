"""
Sessions API routes.
Handles session creation, listing, and management.
"""

from flask import Blueprint, request, jsonify
from app.services.interview_manager import InterviewManager
from app.models.database import get_db
from app.models.session import Session

sessions_bp = Blueprint('sessions', __name__)

# Global interview manager instance
_interview_manager = None


def get_interview_manager() -> InterviewManager:
    """Get or create the interview manager singleton."""
    global _interview_manager
    if _interview_manager is None:
        _interview_manager = InterviewManager()
    return _interview_manager


@sessions_bp.route('/api/sessions', methods=['POST'])
def create_session():
    """
    Create a new interview session.
    
    Request body:
        {
            "expert_name": "Steve Hajducek",
            "expert_callsign": "N2CKH",  // optional
            "topics": ["ALE", "MS-DMT"],  // optional
            "voice_preset": "premium_female",  // optional: tier_gender format
            "speech_rate": 0.95  // optional: 0.5 to 1.5
        }
    
    Response:
        {
            "session_id": "uuid-string",
            "greeting": "Hello Steve...",
            "audio_url": "/audio/hash.mp3",
            "voice_preset": "premium_female",
            "speech_rate": 0.95,
            "session_cost": 0.0012,
            "chars_synthesized": 150
        }
    """
    from app.config import Config
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    expert_name = data.get("expert_name", "").strip()
    
    if not expert_name:
        return jsonify({"error": "expert_name is required"}), 400
    
    expert_callsign = data.get("expert_callsign")
    topics = data.get("topics")
    voice_preset = data.get("voice_preset", "premium_female")
    speech_rate = data.get("speech_rate", 0.95)
    
    # Validate voice_preset
    if voice_preset not in Config.VOICE_PRESETS:
        voice_preset = "premium_female"
    
    # Validate speech_rate (0.5 to 1.5)
    try:
        speech_rate = float(speech_rate)
        speech_rate = max(0.5, min(1.5, speech_rate))
    except (TypeError, ValueError):
        speech_rate = 0.95
    
    try:
        manager = get_interview_manager()
        result = manager.create_session(
            expert_name=expert_name,
            expert_callsign=expert_callsign,
            topics=topics,
            voice_preset=voice_preset,
            speech_rate=speech_rate
        )
        return jsonify(result), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route('/api/sessions', methods=['GET'])
def list_sessions():
    """
    List all interview sessions.
    
    Query params:
        status: Filter by status (active, completed, abandoned)
    
    Response:
        {
            "sessions": [
                {
                    "id": "uuid-string",
                    "expert_name": "Steve Hajducek",
                    "expert_callsign": "N2CKH",
                    "status": "completed",
                    "message_count": 47,
                    "created_at": "2025-12-14T10:30:00Z"
                }
            ]
        }
    """
    status = request.args.get("status")
    
    try:
        db = get_db()
        sessions = Session.get_all(db, status=status)
        
        # Return simplified list
        session_list = [
            {
                "id": s["id"],
                "expert_name": s["expert_name"],
                "expert_callsign": s.get("expert_callsign"),
                "status": s["status"],
                "message_count": s.get("message_count", 0),
                "created_at": s["created_at"]
            }
            for s in sessions
        ]
        
        return jsonify({"sessions": session_list})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """
    Get details of a specific session.
    
    Response:
        {
            "id": "uuid-string",
            "expert_name": "Steve Hajducek",
            "expert_callsign": "N2CKH",
            "status": "active",
            "topics": ["ALE", "MS-DMT"],
            "message_count": 10,
            "created_at": "2025-12-14T10:30:00Z"
        }
    """
    try:
        db = get_db()
        session = Session.get_by_id(db, session_id)
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(session)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route('/api/sessions/<session_id>/end', methods=['POST'])
def end_session(session_id: str):
    """
    End an interview session.
    
    Response:
        {
            "session_id": "uuid-string",
            "status": "completed",
            "message_count": 47,
            "duration_seconds": 1823,
            "transcript_url": "/api/transcript/uuid",
            "extraction_url": "/api/extraction/uuid"
        }
    """
    try:
        manager = get_interview_manager()
        result = manager.end_session(session_id)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """
    Delete a session and all its data.
    
    Response:
        {
            "deleted": true,
            "session_id": "uuid-string"
        }
    """
    try:
        db = get_db()
        deleted = Session.delete(db, session_id)
        
        if not deleted:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({"deleted": True, "session_id": session_id})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
