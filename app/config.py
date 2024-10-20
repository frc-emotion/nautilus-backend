import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "nautilus")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"