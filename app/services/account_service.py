from quart import current_app
import datetime
from app.config import Config
import jwt 

# Roles: "admin", "executive", "advisor", "mentor", "leadership", "member"

async def generate_jwt_token(user_data):
    # Generate a new JWT token
    token = jwt.encode(
        {
            "user_id": str(user_data["_id"]),
            "role": str(user_data["role"]),
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=Config.JWT_EXPIRY_DAYS),
            "iat": datetime.datetime.now(datetime.timezone.utc),
        },
        Config.JWT_SECRET,
        algorithm="HS256"
        )
    return token

async def find_user_by_email(email):
    users_collection = current_app.db["users"]

    user = await users_collection.find_one({"email": email})
    return user

async def find_user_by_id(user_id):
    users_collection = current_app.db["users"]

    user = await users_collection.find_one({"_id": user_id})
    return user

async def update_user(user_id, data):
    users_collection = current_app.db["users"]

    result = await users_collection.update_one({"_id": user_id}, {"$set": data})
    return result

async def delete_user(user_id):
    users_collection = current_app.db["users"]

    result = await users_collection.delete_one({"_id": user_id})
    return result

async def add_new_user(data):
    users_collection = current_app.db["users"]

    result = await users_collection.insert_one(data)
    return result

async def modify_user(user_id, key, value):
    users_collection = current_app.db["users"]
    
    result = await users_collection.update_one({"_id": user_id}, {"$set": {key: value}})
    return result
    