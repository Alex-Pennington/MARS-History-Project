"""
Configuration management for SME Interview System.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # ==========================================================================
    # API Keys
    # ==========================================================================
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # ==========================================================================
    # Flask Settings
    # ==========================================================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # ==========================================================================
    # Access Control
    # ==========================================================================
    REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'true').lower() == 'true'
    TOKENS_FILE = os.getenv('TOKENS_FILE', './data/tokens.json')
    
    # ==========================================================================
    # Claude Settings
    # ==========================================================================
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
    CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', 300))
    
    # ==========================================================================
    # Context Management
    # ==========================================================================
    MAX_CONTEXT_MESSAGES = int(os.getenv('MAX_CONTEXT_MESSAGES', 30))
    EXTRACTION_INTERVAL = int(os.getenv('EXTRACTION_INTERVAL', 10))
    
    # ==========================================================================
    # TTS Settings
    # ==========================================================================
    TTS_LANGUAGE_CODE = os.getenv('TTS_LANGUAGE_CODE', 'en-US')
    
    # Voice Presets: 3 tiers × 2 genders
    VOICE_PRESETS = {
        # Budget tier - WaveNet ($4/million chars)
        "budget_female": {
            "name": "en-US-Wavenet-F",
            "display_name": "Budget - Female",
            "tier": "budget",
            "gender": "female",
            "cost_per_char": 0.000004,
            "hourly_estimate": "$0.15/hour",
            "supports_rate": True
        },
        "budget_male": {
            "name": "en-US-Wavenet-D",
            "display_name": "Budget - Male",
            "tier": "budget",
            "gender": "male",
            "cost_per_char": 0.000004,
            "hourly_estimate": "$0.15/hour",
            "supports_rate": True
        },
        
        # Standard tier - Neural2 ($16/million chars)
        "standard_female": {
            "name": "en-US-Neural2-F",
            "display_name": "Standard - Female",
            "tier": "standard",
            "gender": "female",
            "cost_per_char": 0.000016,
            "hourly_estimate": "$0.50/hour",
            "supports_rate": True
        },
        "standard_male": {
            "name": "en-US-Neural2-D",
            "display_name": "Standard - Male",
            "tier": "standard",
            "gender": "male",
            "cost_per_char": 0.000016,
            "hourly_estimate": "$0.50/hour",
            "supports_rate": True
        },
        
        # Premium tier - Chirp 3: HD ($30/million chars)
        "premium_female": {
            "name": "en-US-Chirp3-HD-Kore",
            "display_name": "Premium - Female",
            "tier": "premium",
            "gender": "female",
            "cost_per_char": 0.00003,
            "hourly_estimate": "$1.00/hour",
            "supports_rate": False  # Chirp HD doesn't support rate adjustment
        },
        "premium_male": {
            "name": "en-US-Chirp3-HD-Charon",
            "display_name": "Premium - Male",
            "tier": "premium",
            "gender": "male",
            "cost_per_char": 0.00003,
            "hourly_estimate": "$1.00/hour",
            "supports_rate": False
        }
    }
    
    DEFAULT_VOICE = os.getenv('DEFAULT_VOICE', 'premium_female')
    DEFAULT_SPEECH_RATE = float(os.getenv('DEFAULT_SPEECH_RATE', 0.95))  # Range: 0.5 to 1.5
    
    # ==========================================================================
    # Paths
    # ==========================================================================
    # In Docker, app is at /app, data is at /app/data
    # Locally, we need to go up from app/ to the project root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if we're in Docker (data dir at /app/data) or local
    if os.path.exists('/app/data'):
        DATA_DIR = '/app/data'
    else:
        DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(DATA_DIR, 'interviews.db'))
    AUDIO_CACHE_DIR = os.getenv('AUDIO_CACHE_DIR', os.path.join(DATA_DIR, 'audio_cache'))
    EXPORTS_DIR = os.getenv('EXPORTS_DIR', os.path.join(DATA_DIR, 'exports'))
    
    @classmethod
    def validate(cls) -> list:
        """
        Validate required configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required")
        
        if not cls.GOOGLE_API_KEY and not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            errors.append("GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS is required")
        
        return errors
    
    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.AUDIO_CACHE_DIR, exist_ok=True)
        os.makedirs(cls.EXPORTS_DIR, exist_ok=True)
