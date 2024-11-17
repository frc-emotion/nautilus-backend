from quart import current_app
from typing import Dict, Any, Optional
import datetime
import jwt
from nautilus_api.config import Config
from pymongo.results import UpdateResult, DeleteResult, InsertOneResult

async def generate_jwt_token(user: Dict[str, Any]) -> str:
    """Generate a JWT token for authenticated users."""
    payload = {
        "user_id": str(user["_id"]),
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=Config.JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

async def get_collection(collection_name: str):
    """Helper to retrieve a MongoDB collection from the current app's database."""
    return current_app.db[collection_name]

async def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user by email."""
    account_collection = await get_collection("users")
    return await account_collection.find_one({"email": email})

async def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user by ID."""
    account_collection = await get_collection("users")
    return await account_collection.find_one({"_id": user_id})

async def find_user_by_student_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user by student_id."""
    account_collection = await get_collection("users")
    return await account_collection.find_one({"student_id": user_id})

async def add_new_user(data: Dict[str, Any]) -> InsertOneResult:
    """Add a new user."""
    account_collection = await get_collection("users")

    data["_id"] = await account_collection.count_documents({}) + 1 # since we need user id to be a 16 bit integer

    return await account_collection.insert_one(data)

async def update_user(user_id: int, data: Dict[str, Any]) -> UpdateResult:
    """Update user's data."""
    account_collection = await get_collection("users")
    return await account_collection.update_one({"_id": user_id}, {"$set": data})

async def delete_user(user_id: int) -> DeleteResult:
    """Delete a user by ID."""
    account_collection = await get_collection("users")
    return await account_collection.delete_one({"_id": user_id})

async def update_user_role(user_id: int, role: str) -> UpdateResult:
    """Update user's role."""
    account_collection = await get_collection("users")
    return await account_collection.update_one({"_id": user_id}, {"$set": {"role": role}})

async def update_user_profile(user_id: int, data: Dict[str, Any]) -> UpdateResult:
    """Update user's profile."""
    account_collection = await get_collection("users")
    return await account_collection.update_one({"_id": user_id}, {"$set": data})

async def get_all_users() -> list[Dict[str, Any]]:
    """Retrieve all users."""
    account_collection = await get_collection("users")

    allUsers = await account_collection.find().to_list(None)

    # Remove password field from all users
    for user in allUsers:
        del user["password"]

    return allUsers