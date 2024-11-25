from quart import Quart
from quart_cors import cors
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import account_routes, auth_routes, attendance_routes, meeting_routes
from .config import Config
import logging
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
import queue
import os
from beartype.claw import beartype_this_package
beartype_this_package()

def flip_name(log_path):
    """flips the file name of a log file to put the date in front"""
    
    log_dir, log_filename = os.path.split(log_path)
    file_name, timestamp = log_filename.rsplit(".", 1)
    return os.path.join(log_dir, f"{timestamp}.{file_name}")

mongo_client = None  # Global MongoDB client

# Create a logging queue
log_queue = queue.Queue()

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create log handlers
console_handler = logging.StreamHandler()
file_handler = TimedRotatingFileHandler("nautilus-backend.log", when="midnight", interval=1)
file_handler.suffix = "%Y-%m-%d"
file_handler.namer = flip_name

# Set log formatting
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# You want it looking ugly or what?
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Use QueueHandler to handle logging asynchronously
queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)

# Set up the listener with console and file handlers
listener = QueueListener(log_queue, console_handler, file_handler)
listener.start()

def create_app():
    global mongo_client

    app = Quart(__name__)

    # Enable CORS for all routes
    app = cors(app, allow_origin="*")

    # Setup MongoDB client
    mongo_client = AsyncIOMotorClient(Config.MONGO_URI)
    app.db = mongo_client[Config.DB_NAME]

    # Set the logger for the app
    app.logger = logger
    app.logger_listener = listener

    # Register API routes
    app.register_blueprint(account_routes.account_api, url_prefix="/api/account")
    app.register_blueprint(auth_routes.auth_api, url_prefix="/api/auth")
    app.register_blueprint(attendance_routes.attendance_api, url_prefix="/api/attendance")
    app.register_blueprint(meeting_routes.meeting_api, url_prefix="/api/meetings")

    return app