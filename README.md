# SME Interview System

**MARS Digital History Project - Knowledge Capture System**

A web-based voice interview system that captures institutional knowledge from subject matter experts (SMEs) in HF digital communications. The system uses Claude as an AI interviewer, Google Cloud TTS for voice output, and browser-native Web Speech API for voice input.

## Features

- 🎤 **Voice-based interviews** - Natural conversation using browser speech recognition
- 🤖 **AI Interviewer** - Claude-powered intelligent questioning
- 🔊 **Text-to-Speech** - Google Cloud TTS for natural voice responses
- 📝 **Automatic transcription** - All conversations are captured and stored
- 🧠 **Knowledge extraction** - Structured insights extracted automatically
- 💾 **Persistent storage** - SQLite database for all interview data

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask (Python 3.11+) |
| AI/LLM | Claude API (Anthropic) |
| Text-to-Speech | Google Cloud TTS |
| Speech-to-Text | Web Speech API (browser) |
| Database | SQLite |
| Frontend | Vanilla HTML/CSS/JS |
| Containerization | Docker |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key
- Google Cloud API key (for TTS)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sme-interview-system
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   Open http://localhost:5000 in Chrome or Edge (for voice recognition support)

### Local Development (without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python -m flask run --host=0.0.0.0 --port=5000
   ```

## Project Structure

```
sme-interview-system/
├── app/
│   ├── __init__.py
│   ├── main.py               # Flask app entry point
│   ├── config.py             # Configuration management
│   ├── routes/               # API endpoints
│   │   ├── interview.py      # /api/interview endpoints
│   │   ├── sessions.py       # /api/sessions endpoints
│   │   └── static.py         # Static file serving
│   ├── services/             # Business logic
│   │   ├── claude_client.py  # Anthropic API wrapper
│   │   ├── tts_client.py     # Google TTS wrapper
│   │   ├── interview_manager.py
│   │   ├── context_manager.py
│   │   └── knowledge_extractor.py
│   ├── models/               # Database models
│   │   ├── database.py
│   │   ├── session.py
│   │   └── message.py
│   └── prompts/              # AI system prompts
│       ├── interviewer.py
│       └── extractor.py
├── templates/                # HTML templates
├── static/                   # CSS/JS assets
├── data/                     # SQLite DB & audio cache
└── tests/                    # Test files
```

## API Endpoints

### Sessions

- `POST /api/sessions` - Create a new interview session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details
- `POST /api/sessions/{id}/end` - End an interview session
- `DELETE /api/sessions/{id}` - Delete a session

### Interview

- `POST /api/interview` - Process expert input and get response
- `GET /api/transcript/{id}` - Get full transcript
- `GET /api/extraction/{id}` - Get extracted knowledge

### Health

- `GET /health` - Health check endpoint

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `GOOGLE_API_KEY` | Google Cloud TTS key | Required |
| `CLAUDE_MODEL` | Claude model to use | claude-sonnet-4-20250514 |
| `CLAUDE_MAX_TOKENS` | Max response tokens | 300 |
| `TTS_VOICE_NAME` | Google TTS voice | en-US-Neural2-D |
| `MAX_CONTEXT_MESSAGES` | Sliding window size | 30 |
| `EXTRACTION_INTERVAL` | Extract every N exchanges | 10 |

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Security Considerations

- HTTPS is required for voice input in production (browser security requirement)
- API keys should never be committed to version control
- The AI interviewer is configured to redirect away from sensitive topics
   The sensitive topic redirection is implemented entirely through prompt engineering in the AI's system instructions. The interviewer prompt includes a "Security Boundaries" section that tells Claude to immediately redirect the conversation if topics approach current operational frequencies, classified procedures, cryptographic specifics, or active MARS traffic details. It provides a specific redirect phrase to use: "That sounds operationally sensitive—let's stick to the historical and technical aspects." There's no code-level filtering—it relies on Claude following these instructions in its responses.

## Browser Support

Voice recognition requires Chrome or Edge browsers. Text input fallback is available for other browsers.

## License

Copyright © 2025 Phoenix Nest LLC. All rights reserved.

---

*Part of the MARS Digital History Project*
