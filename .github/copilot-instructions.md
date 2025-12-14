# SME Interview System - Copilot Instructions

## Project Overview
This is a Flask-based web application for conducting voice interviews with Subject Matter Experts (SMEs) for the MARS Digital History Project.

## Technology Stack
- **Backend**: Flask (Python 3.11+)
- **AI/LLM**: Claude API (Anthropic)
- **Text-to-Speech**: Google Cloud TTS
- **Speech-to-Text**: Web Speech API (browser)
- **Database**: SQLite
- **Frontend**: Vanilla HTML/CSS/JS
- **Containerization**: Docker

## Project Structure
```
sme-interview-system/
├── app/
│   ├── __init__.py
│   ├── main.py               # Flask app entry point
│   ├── config.py             # Configuration management
│   ├── routes/               # API endpoints
│   ├── services/             # Business logic
│   ├── models/               # Database models
│   └── prompts/              # AI system prompts
├── templates/                # HTML templates
├── static/                   # CSS/JS assets
├── data/                     # SQLite DB & audio cache
└── tests/                    # Test files
```

## Development Guidelines
- Use environment variables for all API keys
- Keep Claude responses short (max 300 tokens) for interview flow
- Implement sliding window context management
- Cache TTS audio using content hashes
- All API endpoints return JSON

## Key Environment Variables
- `ANTHROPIC_API_KEY`: Claude API key
- `GOOGLE_API_KEY`: Google Cloud TTS key
- `FLASK_ENV`: development/production
- `DATABASE_PATH`: SQLite database path

## Running the Project
```bash
docker-compose up --build
# Access at http://localhost:5000
```
