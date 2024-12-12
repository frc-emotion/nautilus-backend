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

async def get_all_attendance() -> List[Dict[str, Any]]:
    """Retrieve all attendance documents from the database."""
    attendance_collection = await get_collection("attendance")
    return await attendance_collection.find().to_list(length=None)

async def get_hours_by_user_id(user_id: int) -> int:
    """Calculate total hours of attendance for a specific user by summing log hours."""
    user = await get_attendance_by_user_id(user_id)
    # if not user:
    #     return 0
    # return sum(log["hours"] for log in user.get("logs", []))

    # Need to account for hours based on term and year. Return hours for each year and term

    if not user:
        return {}

    hours = {}
    for log in user.get("logs", []):
        key = f"{log['year']}_{log['term']}"
        hours[key] = hours.get(key, 0) + log["hours"]
    return hours

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
        "term": meeting["term"],
        "year": meeting["year"]
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

    if len(all_meetings) != 0:
        meeting_id = all_meetings[-1]["_id"] + 1
    else:
        meeting_id = 1

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
        "term": data["term"],
        "year": data["year"],
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

async def user_already_logged(user_id: int, meeting_id: str) -> bool:
    """Check if a user has already logged attendance for a given meeting."""
    user = await get_attendance_by_user_id(user_id)
    
    # Check meeting document for user's attendance log
    if user:
        return any(log["meeting_id"] == meeting_id for log in user.get("logs", []))
    
    # Check if user is already logged for the meeting
    meeting = await get_meeting_by_id(meeting_id)
    return user_id in meeting.get("members_logged", []) if meeting else False

async def delete_meeting(meeting_id: int):
    """Delete a meeting by ID"""
    meeting_collection = await get_collection("meetings")

    return await meeting_collection.delete_one({"_id": meeting_id})

async def add_manual_attendance_log(user_id: int, log_data: Dict[str, Any]) -> bool:
    attendance_collection = await get_collection("attendance")
    # Append the new log to the user's logs
    result = await attendance_collection.update_one(
        {"_id": user_id},
        {"$push": {"logs": log_data}},
        upsert=True
    )
    return result.modified_count > 0

async def remove_manual_attendance_logs(user_id: int, hours: float, term: int, year: str) -> bool:
    attendance_collection = await get_collection("attendance")
    user = await get_attendance_by_user_id(user_id)
    if user:
        logs = user.get("logs", [])
        hours_to_remove = hours
        new_logs = []
        for log in logs:
            if log["term"] == term and log["year"] == year and hours_to_remove > 0:
                if log["hours"] <= hours_to_remove:
                    hours_to_remove -= log["hours"]
                    continue  # Skip this log
                else:
                    log["hours"] -= hours_to_remove
                    hours_to_remove = 0
            new_logs.append(log)
        result = await attendance_collection.update_one(
            {"_id": user_id},
            {"$set": {"logs": new_logs}}
        )
        return result.modified_count > 0
    return False
