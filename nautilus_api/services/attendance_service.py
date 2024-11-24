from quart import current_app
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from pymongo.results import UpdateResult, DeleteResult, InsertOneResult

async def get_collection(collection_name: str):
    """Helper to retrieve a MongoDB collection from the current app's database."""
    return current_app.db[collection_name]

async def get_attendance_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch attendance data for a specific user by user_id."""
    attendance_collection = await get_collection("attendance")
    return await attendance_collection.find_one({"_id": user_id})

async def get_hours_by_user_id(user_id: int) -> int:
    """Calculate total hours of attendance for a specific user by summing log hours."""
    user = await get_attendance_by_user_id(user_id)
    if not user:
        return 0
    return sum(log["hours"] for log in user.get("logs", []))

async def log_attendance(data: Dict[str, Any], user_id: int) -> Union[UpdateResult, InsertOneResult]:
    """
    Log attendance for a user. If user already has attendance logs, append the new log.
    If not, create a new attendance document for the user.
    """
    attendance_collection = await get_collection("attendance")
    user = await get_attendance_by_user_id(user_id)

    # Fetch amt of hours for the meeting
    meeting = await get_meeting_by_id(data["meeting_id"])

    # Structure for a new attendance log entry
    new_log = {
        "meeting_id": data["meeting_id"],
        "lead_id": data["lead_id"],
        "time_received": data["time_received"],
        "flag": data["flag"],
        "hours": meeting["hours"],
    }

    if user:
        # Append the new log to the user's existing attendance logs
        user["logs"].append(new_log)
        result = await attendance_collection.update_one(
            {"_id": int(user_id)},
            {"$set": {"logs": user["logs"]}}
        )
    else:
        # Create a new attendance document with the log for the user
        result = await attendance_collection.insert_one({
            "_id": int(user_id),
            "logs": [new_log],
        })
    return result

async def remove_attendance(data: Dict[str, Any]) -> Optional[UpdateResult]:
    """
    Remove a specific attendance log from a user's attendance records.
    """
    attendance_collection = await get_collection("attendance")
    user = await get_attendance_by_user_id(data["user_id"])

    if user:
        # Filter out the log with the specified meeting_id
        user["logs"] = [log for log in user["logs"] if log["meeting_id"] != data["meeting_id"]]
        return await attendance_collection.update_one(
            {"_id": data["user_id"]},
            {"$set": {"logs": user["logs"]}}
        )
    return None

async def modify_attendance(data: Dict[str, Any]) -> Optional[UpdateResult]:
    """
    Modify an existing attendance log for a user. Update `time_received` and `hours`.
    """
    attendance_collection = await get_collection("attendance")
    user = await get_attendance_by_user_id(data["user_id"])

    if user:
        # Find and update the log with the matching meeting_id
        for log in user["logs"]:
            if log["meeting_id"] == data["meeting_id"]:
                log.update({
                    "time_received": data["time_received"],
                    "hours": data["hours"]
                })
                return await attendance_collection.update_one(
                    {"_id": data["user_id"]},
                    {"$set": {"logs": user["logs"]}}
                )
    return None

async def update_meeting_attendance(meeting_id: str, user_id: str) -> Optional[UpdateResult]:
    """
    Append a user to the `members_logged` list for a specific meeting.
    """
    meetings_collection = await get_collection("meetings")
    meeting = await meetings_collection.find_one({"_id": meeting_id})

    # Ensure the user is added only if they are not already in the list
    if meeting and user_id not in meeting.get("members_logged", []):
        meeting["members_logged"].append(user_id)
        return await meetings_collection.update_one(
            {"_id": meeting_id},
            {"$set": {"members_logged": meeting["members_logged"]}}
        )
    return None

async def create_meeting(data: Dict[str, Any]) -> InsertOneResult:
    """
    Create a new meeting document in the `meetings` collection.
    """
    meeting_collection = await get_collection("meetings")

    # Meeting id must be a 16 bit number so we cant use the default ObjectId. Start at 0 and increment by 1 (essentially a counter)
    all_meetings = await meeting_collection.find().to_list(None)

    meeting_id = all_meetings[-1]["_id"] + 1

    new_meeting = {
        "title": data["title"],
        "created_by": data["created_by"],
        "time_start": data["time_start"],
        "time_end": data["time_end"],
        "location": data["location"],
        "description": data["description"],
        "hours": data["hours"],
        "created_at": datetime.now(timezone.utc),
        "members_logged": [],
        "_id": meeting_id
    }
    return await meeting_collection.insert_one(new_meeting)

async def get_meeting_by_id(meeting_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a meeting document by its unique ID."""
    meeting_collection = await get_collection("meetings")
    return await meeting_collection.find_one({"_id": meeting_id})

async def update_meeting(meeting_id: int, data: Dict[str, Any]) -> UpdateResult:
    """Update fields in an existing meeting document by meeting ID."""
    meeting_collection = await get_collection("meetings")
    return await meeting_collection.update_one({"_id": meeting_id}, {"$set": data})

async def get_all_meetings() -> List[Dict[str, Any]]:
    """Retrieve all meeting documents from the database."""
    meeting_collection = await get_collection("meetings")
    return await meeting_collection.find().to_list(length=None)

# async def user_already_logged_meeting(meeting_id: str, user_id: str) -> bool:
#     """Check if a user is already logged for a specific meeting."""
#     meeting = await get_meeting_by_id(meeting_id)
#     return user_id in meeting.get("members_logged", []) if meeting else False

# async def user_already_logged_attendance(meeting_id: str, user_id: str) -> bool:
#     """Check if a user has already logged attendance for a specific meeting."""
#     user = await get_attendance_by_user_id(user_id)
#     return any(log["meeting_id"] == meeting_id for log in user.get("logs", [])) if user else False

async def user_already_logged(user_id: str, meeting_id: str) -> bool:
    """Check if a user has already logged attendance for a given meeting."""
    user = await get_attendance_by_user_id(user_id)
    
    # Check meeting document for user's attendance log
    if user:
        return any(log["meeting_id"] == meeting_id for log in user.get("logs", []))
    
    # Check if user is already logged for the meeting
    meeting = await get_meeting_by_id(meeting_id)
    return user_id in meeting.get("members_logged", []) if meeting else False

    