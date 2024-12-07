import os

class Config:
    # MongoDB connection URI, defaulting to localhost for development
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    
    # Production flag
    PRODUCTION: bool = os.getenv("PRODUCTION", "False").lower() == "true"

    # Expo push token
    EXPO_TOKEN: str = os.getenv("EXPO_TOKEN", "")
    
    # Secret key for JWT encoding/decoding
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    
    # Database name, defaulting to a development database
    DB_NAME: str = os.getenv("DB_NAME", "nautilus-dev")
    
    # API versioning
    API_VERSION: str = "1.0"
    
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
        }
    }

    ROLE_HIERARCHY = ["unverified", "member", "leadership", "executive", "advisor", "admin"]

    MAILGUN_API_KEY: str = os.getenv("MAILGUN_API_KEY", "")

    MAILGUN_ENDPOINT: str = os.getenv("MAILGUN_ENDPOINT", "")

    MAILGUN_FROM_EMAIL: str = os.getenv("MAILGUN_FROM_EMAIL", "")

    