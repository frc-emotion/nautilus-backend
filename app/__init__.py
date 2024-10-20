from quart import Quart
from quart_cors import cors
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import register_routes
from .config import Config

mongo_client = None  # Global MongoDB client

def create_app():
    global mongo_client

    app = Quart(__name__)
    app = cors(app, allow_origin="*")

    # Setup MongoDB client
    mongo_client = AsyncIOMotorClient(Config.MONGO_URI)
    app.db = mongo_client[Config.DB_NAME]

    # Register API routes
    register_routes(app)

    return app