
from quart import current_app
from pymongo.results import UpdateResult, DeleteResult, InsertOneResult

async def get_collection(collection_name: str):
    """Helper to retrieve a MongoDB collection from the current app's database."""
    return current_app.db[collection_name]

async def update_notification_token(user_id: int, token: str) -> UpdateResult:
    """Update user's notification token."""
    account_collection = await get_collection("users")
    
    # If exists, update the token, else create a new one
    return await account_collection.update_one(
        {"_id": user_id},
        {"$set": {"notification_token": token}},
        upsert=True
    )

async def delete_notification_token(user_id: int) -> UpdateResult:
    """Delete user's notification token."""
    account_collection = await get_collection("users")
    return await account_collection.update_one(
        {"_id": user_id},
        {"$unset": {"notification_token": ""}}
   )

