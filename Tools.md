# SME Interview System - Administrator Tools

This document covers the command-line tools for managing access credentials and working with interview data.

---

## Access Token Management

The system uses token-based authentication. Each interviewer needs a unique token to access the system.

### Token Storage

Tokens are stored in `data/tokens.json`. Each token tracks:
- User name and callsign
- Creation date
- Active/revoked status
- Last used timestamp
- Number of sessions conducted

### Commands

All commands are run from the project root directory.

#### Create a New Token

```bash
python manage_tokens.py add "John Smith" --callsign W1ABC
```

Output:
```
✅ Token created for John Smith
   Callsign: W1ABC

   Token: w-5GsK3dnGRxicp8csqMxA

   Give this token to John - they'll need it to access the system.
```

The callsign is optional:
```bash
python manage_tokens.py add "Jane Doe"
```

#### List All Tokens

```bash
python manage_tokens.py list
```

Shows a table with all tokens including status, session counts, and last used dates.

#### Revoke a Token

Prevents the user from logging in but keeps the record:

```bash
python manage_tokens.py revoke w-5GsK3d
```

You can use a partial token prefix - just enough characters to uniquely identify it.

#### Delete a Token

Permanently removes the token (requires confirmation):

```bash
python manage_tokens.py delete w-5GsK3d
```

---

## Interview Data Export

Export interview transcripts and extracted knowledge for archival or analysis.

### Commands

#### List All Sessions

```bash
python export_interviews.py list
```

Displays a table showing:
- Expert name and callsign
- Interviewer name
- Session status (active/completed)
- Message count
- Estimated API cost
- Date

#### Export a Single Session

```bash
python export_interviews.py one <session_id>
```

Or specify a custom output directory:
```bash
python export_interviews.py one <session_id> --output ./my-exports
```

#### Export All Completed Sessions

```bash
python export_interviews.py all
```

With custom output directory:
```bash
python export_interviews.py all --output ./archives
```

### Export Format

Exports are saved as JSON files in `data/exports/` (default). Each file includes:

```json
{
  "export_date": "2025-12-14T10:30:00Z",
  "session": {
    "id": "uuid-string",
    "expert_name": "Steve Hajducek",
    "expert_callsign": "N2CKH",
    "interviewer_name": "Admin User",
    "voice_preset": "premium_female",
    "status": "completed",
    "created_at": "...",
    "message_count": 45,
    "estimated_cost": 0.25
  },
  "messages": [
    {"role": "assistant", "content": "Hello Steve...", "created_at": "..."},
    {"role": "user", "content": "Thanks, I worked on...", "created_at": "..."}
  ],
  "extractions": [
    {
      "extraction_data": { "topics_discussed": [...], "key_insights": [...] },
      "message_range_start": 1,
      "message_range_end": 10
    }
  ]
}
```

Files are named: `{Expert_Name}_{session_id_prefix}.json`

---

## Quick Reference

| Task | Command |
|------|---------|
| Add token | `python manage_tokens.py add "Name" -c CALLSIGN` |
| List tokens | `python manage_tokens.py list` |
| Revoke token | `python manage_tokens.py revoke <token_prefix>` |
| Delete token | `python manage_tokens.py delete <token_prefix>` |
| List sessions | `python export_interviews.py list` |
| Export one | `python export_interviews.py one <session_id>` |
| Export all | `python export_interviews.py all` |

---

## Database Location

- **SQLite database**: `data/interviews.db`
- **Token file**: `data/tokens.json`
- **Audio cache**: `data/audio_cache/`
- **Exports**: `data/exports/`
