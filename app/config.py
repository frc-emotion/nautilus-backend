import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    DB_NAME = os.getenv("DB_NAME", "nautilus-dev")
    API_VERSION = "1.0"
    JWT_EXPIRY_DAYS = 3