#!/usr/bin/env python3
"""CLI tool for managing access tokens."""

import sys
import os
import json
import secrets
import argparse
from datetime import datetime
from pathlib import Path

# Standalone token functions to avoid importing the full app
TOKENS_FILE = Path(os.getenv('TOKENS_FILE', './data/tokens.json'))


def _load_tokens():
    """Load tokens from JSON file."""
    if not TOKENS_FILE.exists():
        return {"tokens": {}}
    with open(TOKENS_FILE, 'r') as f:
        return json.load(f)


def _save_tokens(data):
    """Save tokens to JSON file."""
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKENS_FILE, 'w') as f:
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


def cmd_add(args):
    """Add a new token."""
    token = add_token(args.name, args.callsign)
    print(f"\n✅ Token created for {args.name}")
    if args.callsign:
        print(f"   Callsign: {args.callsign}")
    print(f"\n   Token: {token}")
    print(f"\n   Give this token to {args.name.split()[0]} - they'll need it to access the system.\n")


def cmd_list(args):
    """List all tokens."""
    tokens = list_tokens()
    
    if not tokens:
        print("\nNo tokens found.\n")
        return
    
    print(f"\n{'Name':<25} {'Callsign':<10} {'Status':<10} {'Sessions':<10} {'Last Used':<20} {'Token':<12}")
    print("-" * 97)
    
    for t in tokens:
        status = "✅ Active" if t["active"] else "❌ Revoked"
        last_used = t.get("last_used") or "Never"
        if last_used != "Never":
            last_used = last_used[:16].replace("T", " ")
        callsign = t.get("callsign") or "-"
        sessions = t.get("sessions_count", 0)
        
        print(f"{t['name']:<25} {callsign:<10} {status:<10} {sessions:<10} {last_used:<20} {t['token_short']:<12}")
    
    print()


def cmd_revoke(args):
    """Revoke a token."""
    # Allow partial token match
    tokens = list_tokens()
    matches = [t for t in tokens if t["token"].startswith(args.token)]
    
    if len(matches) == 0:
        print(f"\n❌ No token found starting with '{args.token}'\n")
        return
    elif len(matches) > 1:
        print(f"\n❌ Multiple tokens match '{args.token}'. Be more specific.\n")
        return
    
    token = matches[0]
    if revoke_token(token["token"]):
        print(f"\n✅ Token revoked for {token['name']}")
        print(f"   They will no longer be able to access the system.\n")
    else:
        print(f"\n❌ Failed to revoke token.\n")


def cmd_delete(args):
    """Permanently delete a token."""
    tokens = list_tokens()
    matches = [t for t in tokens if t["token"].startswith(args.token)]
    
    if len(matches) == 0:
        print(f"\n❌ No token found starting with '{args.token}'\n")
        return
    elif len(matches) > 1:
        print(f"\n❌ Multiple tokens match '{args.token}'. Be more specific.\n")
        return
    
    token = matches[0]
    confirm = input(f"Permanently delete token for {token['name']}? (yes/no): ")
    if confirm.lower() == 'yes':
        if delete_token(token["token"]):
            print(f"\n✅ Token permanently deleted.\n")
        else:
            print(f"\n❌ Failed to delete token.\n")
    else:
        print("\nCancelled.\n")


def main():
    parser = argparse.ArgumentParser(description="Manage interview system access tokens")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Create a new token")
    add_parser.add_argument("name", help="Person's full name")
    add_parser.add_argument("--callsign", "-c", help="Ham radio callsign (optional)")
    add_parser.set_defaults(func=cmd_add)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all tokens")
    list_parser.set_defaults(func=cmd_list)
    
    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke a token (user can't login)")
    revoke_parser.add_argument("token", help="Token or token prefix to revoke")
    revoke_parser.set_defaults(func=cmd_revoke)
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Permanently delete a token")
    delete_parser.add_argument("token", help="Token or token prefix to delete")
    delete_parser.set_defaults(func=cmd_delete)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
