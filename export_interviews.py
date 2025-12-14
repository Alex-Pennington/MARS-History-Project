#!/usr/bin/env python3
"""Export interview data for archival."""

import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DATABASE = Path('./data/interviews.db')
EXPORT_DIR = Path('./data/exports')


def export_session(session_id: str, output_dir: Path):
    """Export a single session with all messages and extractions."""
    if not DATABASE.exists():
        print(f"Database not found at {DATABASE}")
        return None
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get session info
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    
    if not session:
        print(f"Session {session_id} not found")
        conn.close()
        return None
    
    session = dict(session)
    
    # Get messages
    cursor.execute(
        "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    )
    messages = [dict(row) for row in cursor.fetchall()]
    
    # Get extractions
    cursor.execute(
        "SELECT extraction_data, message_range_start, message_range_end, created_at FROM extractions WHERE session_id = ?",
        (session_id,)
    )
    extractions = []
    for row in cursor.fetchall():
        ext = dict(row)
        ext['extraction_data'] = json.loads(ext['extraction_data']) if ext['extraction_data'] else None
        extractions.append(ext)
    
    conn.close()
    
    # Build export object
    export = {
        "export_date": datetime.now().isoformat(),
        "session": {
            "id": session["id"],
            "expert_name": session["expert_name"],
            "expert_callsign": session.get("expert_callsign"),
            "interviewer_name": session.get("token_user_name"),
            "interviewer_callsign": session.get("token_user_callsign"),
            "voice_preset": session.get("voice_preset"),
            "speech_rate": session.get("speech_rate"),
            "status": session["status"],
            "created_at": session["created_at"],
            "ended_at": session.get("ended_at"),
            "message_count": session.get("message_count", 0),
            "total_chars_synthesized": session.get("total_chars_synthesized"),
            "estimated_cost": session.get("estimated_cost")
        },
        "messages": messages,
        "extractions": extractions
    }
    
    # Write to file
    output_dir.mkdir(parents=True, exist_ok=True)
    expert_name = (session['expert_name'] or 'Unknown').replace(' ', '_')
    filename = f"{expert_name}_{session['id'][:8]}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(export, f, indent=2)
    
    print(f"✅ Exported: {filepath}")
    return filepath


def export_all(output_dir: Path):
    """Export all completed sessions."""
    if not DATABASE.exists():
        print(f"Database not found at {DATABASE}")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, expert_name FROM sessions WHERE status = 'completed'")
    sessions = cursor.fetchall()
    conn.close()
    
    if not sessions:
        print("No completed sessions to export.")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for session in sessions:
        export_session(session["id"], output_dir)


def list_sessions():
    """List all sessions."""
    if not DATABASE.exists():
        print(f"\nDatabase not found at {DATABASE}\n")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, expert_name, expert_callsign, token_user_name, 
               status, created_at, message_count, estimated_cost
        FROM sessions 
        ORDER BY created_at DESC
    """)
    sessions = cursor.fetchall()
    conn.close()
    
    if not sessions:
        print("\nNo sessions found.\n")
        return
    
    print(f"\n{'Expert':<20} {'Callsign':<10} {'Interviewer':<15} {'Status':<12} {'Messages':<10} {'Cost':<8} {'Date':<12}")
    print("-" * 97)
    
    for s in sessions:
        expert = (s["expert_name"] or "Unknown")[:20]
        callsign = (s["expert_callsign"] or "-")[:10]
        interviewer = (s["token_user_name"] or "-")[:15]
        status = (s["status"] or "unknown")[:12]
        messages = s["message_count"] or 0
        cost = f"${s['estimated_cost'] or 0:.2f}"
        date = (s["created_at"] or "")[:10]
        
        print(f"{expert:<20} {callsign:<10} {interviewer:<15} {status:<12} {messages:<10} {cost:<8} {date:<12}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Export interview data")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all sessions")
    list_parser.set_defaults(func=lambda args: list_sessions())
    
    # Export one command
    one_parser = subparsers.add_parser("one", help="Export single session")
    one_parser.add_argument("session_id", help="Session ID to export")
    one_parser.add_argument("--output", "-o", default="./data/exports", help="Output directory")
    one_parser.set_defaults(func=lambda args: export_session(args.session_id, Path(args.output)))
    
    # Export all command
    all_parser = subparsers.add_parser("all", help="Export all completed sessions")
    all_parser.add_argument("--output", "-o", default="./data/exports", help="Output directory")
    all_parser.set_defaults(func=lambda args: export_all(Path(args.output)))
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
