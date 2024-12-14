from datetime import timedelta
from typing import Any, Dict, Optional
from beartype.claw import beartype_this_package
import jwt
from quart_cors import cors
from quart_rate_limiter import RateLimit, RateLimiter, remote_addr_key
beartype_this_package()

from nautilus_api.routes import notification_routes
import httpx
from quart import Quart, current_app, g, request
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import account_routes, auth_routes, attendance_routes, meeting_routes
from .config import Config
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
logger.add(sink="logs/nautilus-backend_{time}.log", rotation="1 day", retention="14 days", level="INFO", enqueue=True)

# Load version info from 'version.json'
def load_version_info():
    try:
        with open("version.json", "r") as f:
            version_info = f.read()
        return version_info
    except Exception as e:
        return {"error": str(e)}
    
async def get_id():
    auth_header: Optional[str] = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token: str = auth_header.split(" ")[1]
        try:
            decoded_token: Dict[str, Any] = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            g.user = decoded_token
            current_app.logger.info(f"User {g.user.get('user_id')} authenticated successfully")
            return g.user.get("user_id")
        except jwt.ExpiredSignatureError:
            g.user = None
            current_app.logger.warning("Expired token provided for authentication")
            return request.access_route[0]
        except jwt.InvalidTokenError:
            g.user = None
            current_app.logger.warning("Invalid token provided for authentication")
            return request.access_route[0]
    else:
        g.user = None
        current_app.logger.warning("No token provided for authentication")
        return request.access_route[0]      
    
    
def create_app():
    global mongo_client

    app = Quart(__name__)

    # Enable CORS for all routes
    app = cors(app, allow_origin="*") # TODO: SHOULD BE CHANGED TO THE FRONTEND URL

    rate_limiter = RateLimiter(app, key_function=get_id, default_limits=[
        RateLimit(3, timedelta(seconds=1)),
        RateLimit(60, timedelta(minutes=1)),
    ],)

    logger.info("Starting Nautilus API")
    
    # Config
    
    #if not Config.ENVIRONMENT != "prod":
    logger.info("Running in development mode")
    logger.info("Config for API: ")
    logger.info(Config.__dict__)


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

    app.rate_limiter = rate_limiter

    @app.route("/version")
    async def version():
        return app.version_info
    
    @app.route("/")
    async def home():
        if Config.ENVIRONMENT == "prod":
            return ":)"
        
        return "greetings curious one"

    # Register API routes
    app.register_blueprint(account_routes.account_api, url_prefix="/api/account")
    app.register_blueprint(auth_routes.auth_api, url_prefix="/api/auth")
    app.register_blueprint(attendance_routes.attendance_api, url_prefix="/api/attendance")
    app.register_blueprint(meeting_routes.meeting_api, url_prefix="/api/meetings")
    app.register_blueprint(notification_routes.notification_api, url_prefix="/api/notifications")

    return app