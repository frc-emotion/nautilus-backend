import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # MongoDB connection URI, defaulting to localhost for development
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    
    # Production, staging, or development environment
    # prod, stage, dev
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev") 

    # Expo push token (LEGACY - not used, frontend doesn't implement push notifications)
    # EXPO_TOKEN: str = os.getenv("EXPO_TOKEN", "")
    
    # Secret key for JWT encoding/decoding
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    
    # Database name, defaulting to a development database
    DB_NAME: str = os.getenv("DB_NAME", "nautilus-dev")
    
    # API versioning
    API_VERSION: str = "1.1"
    
    # JWT expiry duration in days
    JWT_EXPIRY_DAYS: int = int(os.getenv("JWT_EXPIRY_DAYS", "3"))

    SCHOOL_YEAR = {
        "2024-2025": { # Year that school starts
            1: { # Term 1
                "start": 1724223601,
                "end": 1737360001,
            },
            2: { # Term 2
                "start": 1737360001,
                "end": 1749711601,
            },
        },
        "2025-2026":{ # Year that school starts 
            1:{ # Term 1 
                "start" : 1755102300,
                "end" : 1768618800,
            },
            2: { #Term 2 
                "start" : 1768897500,
                "end" : 1780974000,
            },
            
        },
    }

    ROLE_HIERARCHY = ["unverified", "member", "leadership", "executive", "advisor", "admin"]

    MAILGUN_API_KEY: str = os.getenv("MAILGUN_API_KEY", "")

    MAILGUN_ENDPOINT: str = os.getenv("MAILGUN_ENDPOINT", "")

    MAILGUN_FROM_EMAIL: str = os.getenv("MAILGUN_FROM_EMAIL", "")

    # Application port (Railway will proxy external traffic to this internal port)
    PORT: int = int(os.getenv("PORT", "7001"))

    # API URL based on environment
    # Railway handles external routing, these are the public URLs
    API_URL: str = "http://localhost:7001" if ENVIRONMENT == "dev" else ("https://staging.team2658.org" if ENVIRONMENT == "stage" else "https://api.team2658.org")

    DISCORD_WEBHOOK: str = os.getenv("DISCORD_WEBHOOK", "")

    # The Blue Alliance API Key
    TBA_AUTH_KEY: str = os.getenv("TBA_AUTH_KEY", "")
    
    # Cache TTL for TBA API responses in seconds
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "180"))

    # FRC 2025 Reefscape Scoring Configuration
    # TODO: Verify and update with official 2025 Reefscape point values
    SCORING_CONFIG = {
        "auto": {
            # Points per coral level [L1, L2, L3, L4]
            "coral_points_per_level": [3, 4, 6, 7],  # Placeholder values
            "algae_points": {
                "ground": 3,  # Processor (ground) algae points
                "net": 4      # Barge (net) algae points
            }
        },
        "teleop": {
            # Points per coral level [L1, L2, L3, L4]
            "coral_points_per_level": [2, 3, 4, 5],  # Placeholder values
            "algae_points": {
                "ground": 2,  # Processor (ground) algae points
                "net": 3      # Barge (net) algae points
            }
        },
        "climb_points": {
            "PARK": 2,
            "SHALLOW_CAGE": 6,
            "DEEP_CAGE": 12
        }
    }

    # LEGACY: API v1.0 to v1.1 migration variables (migration already completed)
    # APP_MIGRATION_MEETING: str = os.getenv("APP_MIGRATION_MEETING", "")
    # APP_MIGRATION_LEAD: str = os.getenv("APP_MIGRATION_LEAD", "")
    
    
