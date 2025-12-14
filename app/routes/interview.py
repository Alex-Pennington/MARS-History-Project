"""
Interview API routes.
Handles the main interview interaction endpoint.
"""

from flask import Blueprint, request, jsonify
from app.services.interview_manager import InterviewManager
from app.routes.auth import require_auth

interview_bp = Blueprint('interview', __name__)

# Global interview manager instance
_interview_manager = None


def get_interview_manager() -> InterviewManager:
    """Get or create the interview manager singleton."""
    global _interview_manager
    if _interview_manager is None:
        _interview_manager = InterviewManager()
    return _interview_manager


@interview_bp.route('/api/interview', methods=['POST'])
@require_auth
def process_interview_input():
    """
    Process expert's spoken input and get interviewer response.
    
    Request body:
        {
            "session_id": "uuid-string",
            "text": "transcribed speech from expert"
        }
    
    Response:
        {
            "response_text": "interviewer's response",
            "audio_url": "/audio/hash.mp3",
            "session_id": "uuid-string",
            "message_count": 5,
            "extraction_triggered": false
        }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    session_id = data.get("session_id")
    text = data.get("text", "").strip()
    
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    
    if not text:
        return jsonify({"error": "text is required"}), 400
    
    try:
        manager = get_interview_manager()
        result = manager.process_input(session_id, text)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@interview_bp.route('/api/transcript/<session_id>', methods=['GET'])
@require_auth
def get_transcript(session_id: str):
    """
    Get full transcript for a session.
    
    Response:
        {
            "session_id": "uuid-string",
            "expert_name": "Steve Hajducek",
            "expert_callsign": "N2CKH",
            "created_at": "2025-12-14T10:30:00Z",
            "messages": [...]
        }
    """
    try:
        manager = get_interview_manager()
        transcript = manager.get_transcript(session_id)
        
        if not transcript:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(transcript)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@interview_bp.route('/api/extraction/<session_id>', methods=['GET'])
@require_auth
def get_extraction(session_id: str):
    """
    Get extracted knowledge for a session.
    
    Response:
        {
            "session_id": "uuid-string",
            "topics_discussed": [...],
            "key_insights": [...],
            ...
        }
    """
    try:
        manager = get_interview_manager()
        knowledge = manager.get_extracted_knowledge(session_id)
        
        return jsonify({
            "session_id": session_id,
            **knowledge
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
