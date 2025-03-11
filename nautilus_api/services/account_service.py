from quart import current_app
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone, timedelta
import jwt, time
from nautilus_api.config import Config
from pymongo.results import UpdateResult, DeleteResult, InsertOneResult

async def generate_jwt_token(user: Dict[str, Any]) -> str:
    """Generate a JWT token for authenticated users."""
    payload = {
        "user_id": int(user["_id"]),
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(days=Config.JWT_EXPIRY_DAYS),
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

    all_users = await account_collection.find().to_list(None)
    
    if len(all_users) == 0:
        data["_id"] = 1
    else:
        data["_id"] = all_users[-1]["_id"] + 1 # since we need user id to be a 16 bit integer

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

async def get_user_directory() -> list[Dict[str, Any]]:
    """Retrieve all users."""
    account_collection = await get_collection("users")

    allUsers = await account_collection.find().to_list(None)

    # Remove password field from all users
    for user in allUsers:
        del user["password"]
        del user["email"]
        del user["api_version"]
        del user["phone"]
        del user["created_at"]
        del user["student_id"]
        del user["notification_token"]

    return allUsers

async def mass_verify_users(user_ids: list[int]) -> UpdateResult:
    """Verify multiple users by setting their role to 'member'."""
    account_collection = await get_collection("users")
    return await account_collection.update_many(
        {"_id": {"$in": user_ids}},
        {"$set": {"role": "member"}}
    )

def verify_jwt_token(token: str) -> Union[Dict[str, Any], None]:
    try:
        # Decode the token with the secret and algorithm used for encoding
        decoded_payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])

        # Optionally, check expiration manually (since decode() doesn't automatically raise an exception on expiry)
        exp_timestamp = decoded_payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                return None

        return decoded_payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
async def find_student_id_directory(student_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user by student_id."""
    account_collection = await get_collection("directory")
    return await account_collection.find_one({"student_id": student_id})

async def mass_delete_users(user_ids: list[int]) -> DeleteResult:
    """Delete multiple users by ID."""
    account_collection = await get_collection("users")
    return await account_collection.delete_many({"_id": {"$in": user_ids}})

async def delete_user_meetings(user_id:int)->UpdateResult:
    print(user_id)
    """Delete a user's id in meeting attendance by id."""
    student=await find_user_by_id(user_id)
    student_id=student.get("student_id")
    meetings_collection=await get_collection("meetings")
    for document in await meetings_collection.find({}).to_list(length=None):
            print(f"Document: {document}")

    
    result= await meetings_collection.update_many(
        {"members_logged": student_id},
        {"$pull": {"members_logged": student_id}}
    )
    print(result)
    return(result)

async def delete_user_attendance(user_id:int)->DeleteResult:
    attendance_collection=await get_collection("attendance")
    return await attendance_collection.delete_one({"_id":user_id})

async def migrate_1_0_to_1_1(users_collection, hours_collection, collection_4_5, attendance_collection, user) -> None:
    current_app.logger.info(f"Migrating user {user['student_id']} from API version 1.0 to 1.1")

    # Add 4.5 field to user
    user["api_version"] = "1.1"

    # Check 4_5 collection

    if await collection_4_5.find_one({"student_id": user["student_id"]}):
        user["4.5"] = True
        current_app.logger.info(f"User {user['student_id']} has 4.5")
    else:
        user["4.5"] = False
        current_app.logger.info(f"User {user['student_id']} does not have 4.5")

    # Go through hours collection and update user's hours via attendance collection
    if await hours_collection.find_one({"student_id": user["student_id"]}):
        current_app.logger.info(f"User {user['student_id']} has hours")

        hours = await hours_collection.find_one({"student_id": user["student_id"]})

        current_app.logger.info(f"User {user['student_id']} has {hours['hours']} hours")

        user_id = users_collection.find_one({"student_id": user["student_id"]})["_id"]

        # Calculate current term based on current date and given constants
    #     SCHOOL_YEAR = {
    #     "2024-2025": { # Year that school starts
    #         1: { # Term 1
    #             "start": 1724223601,
    #             "end": 1737360001,
    #         },
    #         2: { # Term 2
    #             "start": 1737360001,
    #             "end": 1749711601,
    #         },
    #     }
    # }

        current_time = int(time.time())

        year = datetime.now().year

        current_year = Config.SCHOOL_YEAR[f"{year}-{year+1}"]

        current_term = 69

        if current_time >= current_year[1]["start"] and current_time <= current_year[1]["end"]:
            current_term = 1
        elif current_time >= current_year[2]["start"] and current_time <= current_year[2]["end"]:
            current_term = 2
            

        # Add hours to user
        toInsert = {
            "meeting_id": Config.APP_MIGRATION_MEETING,
            "lead_id": Config.APP_MIGRATION_LEAD,
            "time_received": current_time,
            "flag": False,
            "hours": hours["hours"],
            "term": current_term,
            "year": f"{year}-{year+1}"
        }

        # Check if user already has hours in attendance collection
        if await attendance_collection.find_one({"_id": user_id}):
            current_app.logger.info(f"User {user['student_id']} already has hours in attendance collection")
            # Insert in logs array
            await attendance_collection.update_one({"_id": user_id}, {"$push": {"logs": toInsert}})
        else:
            current_app.logger.info(f"User {user['student_id']} does not have hours in attendance collection")
            # Create new document
            await attendance_collection.insert_one({"_id": user_id, "logs": [toInsert]})


        # Update user's hours in attendance collection
        # {
        # "_id": 25,
        # "logs": [
        #     {
        #     "meeting_id": 9,
        #     "lead_id": 37,
        #     "time_received": 1741224021,
        #     "flag": false,
        #     "hours": 2,
        #     "term": 2,
        #     "year": "2024-2025"
        #     }
        # ]
        # }

async def migrate_user_api_version() -> UpdateResult:
    # Find all users and if their api version is behind then execute the update
    account_collection = await get_collection("users")
    
    current_api_version = Config.API_VERSION

    # Switch case control structure for versions based on each user who is behind the current API version
    outdated_users = await account_collection.find({"api_version": {"$ne": current_api_version}}).to_list(None)

    current_app.logger.info(f"Found {len(outdated_users)} outdated users")

    for user in outdated_users:
        if user["api_version"] == "1.0":
            await migrate_1_0_to_1_1(account_collection, await get_collection("hours"), await get_collection("4_5"), await get_collection("attendance"), user)
