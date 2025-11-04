
from typing import Any, Dict, Optional
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

async def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user by ID."""
    account_collection = await get_collection("users")
    return await account_collection.find_one({"_id": user_id})

async def get_all_updates():
    updates_collection = await get_collection("updates")

    # Query for active "1" and project only the "update" field
    result = await updates_collection.find(
        {"active": "1"},  # Filter by active status
        {"_id": 1, "update": 1}  # Only include the "update" field, exclude "_id"
    ).to_list(length=None)  # Convert to a list

    return result

async def update_active_status(update):
    updates_collection = await get_collection("updates")

    result = await updates_collection.update_one(
        {"_id": update["id"]},  # Query to match the "update" field
        {"$set": {"active": "-1"},
         "$push": {"modified_by": update["removed_by"]}
         }  # Set the "active" field to "-1"
    )

    return result

async def add_notification(update):
    updates_collection = await get_collection("updates")

    all_updates = await updates_collection.find().to_list(None)

    if len(all_updates) == 0:
        id= 1
    else:
        id = all_updates[-1]["_id"] + 1

    result = await updates_collection.insert_one({
        "_id": id,
        "update": update["update"],
        "active": "1",
        "created_by": update["created_by"],
        "modified_by":[update["created_by"]],
    })

    return result

async def update_notification(update):
    updates_collection = await get_collection("updates")

    result = await updates_collection.update_one(
        {"_id": update["id"]},  # Query to match the "update" field
                {
                    "$set": {
                        "update": update["update"]
                    },
                    "$push": {
                        "modified_by": update["edited_by"]  # Append to the array
                    }
                }
            )

    return result