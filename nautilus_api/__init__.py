from beartype.claw import beartype_this_package

from nautilus_api.routes import notification_routes
beartype_this_package()
import httpx
from quart import Quart
from quart_cors import cors
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import account_routes, auth_routes, attendance_routes, meeting_routes
from .config import Config
import logging
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
import queue
import os
from exponent_server_sdk_async import (
    AsyncPushClient,
)
from loguru import logger

def flip_name(log_path):
    """flips the file name of a log file to put the date in front"""
    
    log_dir, log_filename = os.path.split(log_path)
    file_name, timestamp = log_filename.rsplit(".", 1)
    return os.path.join(log_dir, f"{timestamp}.{file_name}")

mongo_client = None  # Global MongoDB client

# Configure logger
logger.add(sink="nautilus-backend_{time}.log", rotation="1 day", retention="14 days", level="INFO", enqueue=True)

# Load version info from 'version.json'
def load_version_info():
    try:
        with open("version.json", "r") as f:
            version_info = f.read()
        return version_info
    except Exception as e:
        return {"error": str(e)}
    
def create_app():
    global mongo_client

    app = Quart(__name__)

    # Enable CORS for all routes
    app = cors(app, allow_origin="*")

    # Setup MongoDB client
    mongo_client = AsyncIOMotorClient(Config.MONGO_URI)
    app.db = mongo_client[Config.DB_NAME]

    async_expo_client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {Config.EXPO_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )
    
    app.http_client = httpx.AsyncClient()

    push_client = AsyncPushClient(session=async_expo_client)
    app.push_client = push_client

    # Set the logger for the app
    app.logger = logger

    # Load version info
    app.version_info = load_version_info()

    @app.route("/version")
    async def version():
        return app.version_info
    
    @app.route("/")
    async def home():
        return "greetings curious one"

    # Register API routes
    app.register_blueprint(account_routes.account_api, url_prefix="/api/account")
    app.register_blueprint(auth_routes.auth_api, url_prefix="/api/auth")
    app.register_blueprint(attendance_routes.attendance_api, url_prefix="/api/attendance")
    app.register_blueprint(meeting_routes.meeting_api, url_prefix="/api/meetings")
    app.register_blueprint(notification_routes.notification_api, url_prefix="/api/notifications")

    return app