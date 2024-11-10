from quart import Quart
from quart_cors import cors
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import register_routes
from .config import Config
import logging
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
import queue

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
    register_routes(app)

    return app