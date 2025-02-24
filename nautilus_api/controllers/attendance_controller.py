# attendance_controller.py

from pydantic import ValidationError
from quart import current_app
from typing import Any, Dict, Union
from nautilus_api.config import Config
from nautilus_api.controllers.account_controller import error_response, success_response
from nautilus_api.controllers.utils import validate_data
import nautilus_api.services.attendance_service as attendance_service
import nautilus_api.services.account_service as account_service
from nautilus_api.schemas.attendance_schema import (
    ManualAttendanceLogSchema,
    MeetingSchema,
    AttendanceLogSchema,
    AttendanceUserSchema,
    RemoveAttendanceLogSchema,
    RemoveManualAttendanceSchema,
    ManualUserMeetingSchema
)
from nautilus_api.schemas.utils import format_validation_error

# Attendance logging function
async def log_attendance(data: Dict[str, Any], user_id: int) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[log_attendance] Start - user_id={user_id}, data={data}")

    validated_data, error = validate_data(AttendanceLogSchema, data, "Log Attendance")
    if error:
        logger.warning(f"[log_attendance] Validation error for user_id={user_id}: {error}")
        return validated_data

    if isinstance(validated_data, dict):  # Return error if validation failed
        logger.warning(f"[log_attendance] Validation returned error dict for user_id={user_id}, data={validated_data}")
        return validated_data

    meeting = await attendance_service.get_meeting_by_id(validated_data.meeting_id)
    if not meeting:
        logger.warning(f"[log_attendance] Meeting not found: {validated_data.meeting_id}")
        return error_response("Meeting not found", 404)

    if not meeting["time_start"] <= validated_data.time_received <= meeting["time_end"]:
        logger.warning(f"[log_attendance] Timestamp out of bounds for user_id={user_id}, meeting_id={meeting['_id']}")
        return error_response("Timestamp out of bounds", 400)

    if await attendance_service.user_already_logged(user_id, validated_data.meeting_id):
        logger.info(f"[log_attendance] Already logged for user_id={user_id}, meeting_id={validated_data.meeting_id}")
        return error_response("Already logged", 409)
    
    # Check if the meeting is a child meeting (has a parent)
    if meeting["parent"]:
        logger.info(f"[log_attendance] Meeting {meeting['_id']} is child of {meeting['parent']}. Checking parent logs.")
        parent_meeting = await attendance_service.get_meeting_by_id(meeting["parent"])
        if not parent_meeting:
            logger.warning(f"[log_attendance] Parent meeting not found for child meeting {meeting['_id']}")
            return error_response("Parent meeting not found", 404)
        
        if await attendance_service.user_already_logged(user_id, parent_meeting["_id"]):
            logger.info(f"[log_attendance] Unlogging parent meeting {parent_meeting['_id']} for user_id={user_id}")
            if not await attendance_service.unlog_attendance(user_id, parent_meeting["_id"]):
                logger.error(f"[log_attendance] Unlog failed for parent meeting {parent_meeting['_id']}, user_id={user_id}")
                return error_response("Unlog failed", 500)

    else:
        # Look for child meetings
        logger.info(f"[log_attendance] Meeting {meeting['_id']} is parent. Checking child logs.")
        child_meetings = await attendance_service.get_child_meetings(validated_data.meeting_id)
        for child_meeting in child_meetings:
            if await attendance_service.user_already_logged(user_id, child_meeting["_id"]):
                logger.info(f"[log_attendance] Unlogging child meeting {child_meeting['_id']} for user_id={user_id}")
                if not await attendance_service.unlog_attendance(user_id, child_meeting["_id"]):
                    logger.error(f"[log_attendance] Unlog failed for child meeting {child_meeting['_id']}, user_id={user_id}")
                    return error_response("Unlog failed", 500)
                break

    if not await attendance_service.log_attendance(validated_data.model_dump(exclude_unset=True), user_id):
        logger.error(f"[log_attendance] Log attendance failed for user_id={user_id}, meeting_id={validated_data.meeting_id}")
        return error_response("Log attendance failed", 500)
    
    if not await attendance_service.update_meeting_attendance(validated_data.meeting_id, user_id):
        logger.error(f"[log_attendance] Meeting update failed for meeting_id={validated_data.meeting_id}, user_id={user_id}")
        return error_response("Meeting update failed", 500)

    logger.info(f"[log_attendance] Success - user_id={user_id}, meeting_id={validated_data.meeting_id}")
    return success_response("Attendance logged", 201)

# Function to get total attendance hours for a user
async def get_attendance_hours(user_id: int) -> Dict[str, Union[int, str]]:
    logger = current_app.logger
    logger.info(f"[get_attendance_hours] Start - user_id={user_id}")
    try:
        total_hours = await attendance_service.get_hours_by_user_id(user_id)
        logger.info(f"[get_attendance_hours] Success - user_id={user_id}, total_hours={total_hours}")
        return success_response("Hours retrieved", 200, {"total_hours": total_hours})
    except Exception as e:
        logger.error(f"[get_attendance_hours] Error retrieving hours for user_id={user_id}: {str(e)}")
        return error_response("Retrieval failed", 500)

# Function to remove an attendance log
async def remove_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[remove_attendance] Start - data={data}")

    validated_data, error = validate_data(AttendanceLogSchema, data, "Remove Attendance")
    if error:
        logger.warning(f"[remove_attendance] Validation error: {error}")
        return validated_data

    if not await attendance_service.remove_attendance(validated_data.model_dump(exclude_unset=True)):
        logger.warning(f"[remove_attendance] Attendance log not found for data={validated_data}")
        return error_response("Attendance log not found", 404)

    logger.info(f"[remove_attendance] Success - log removed for data={validated_data}")
    return success_response("Log removed", 200)

# Function to modify an attendance log
async def modify_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[modify_attendance] Start - data={data}")

    validated_data, error = validate_data(RemoveAttendanceLogSchema, data, "Modify Attendance")
    if error:
        logger.warning(f"[modify_attendance] Validation error: {error}")
        return validated_data

    if not await attendance_service.modify_attendance(validated_data.model_dump(exclude_unset=True)):
        logger.warning(f"[modify_attendance] Attendance log not found or unchanged for data={validated_data}")
        return error_response("Attendance log not found", 404)

    logger.info(f"[modify_attendance] Success - log modified for data={validated_data}")
    return success_response("Log modified", 200)

async def create_meeting(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[create_meeting] Start - data={data}")

    validated_data, error = validate_data(MeetingSchema, data, "Create Meeting")
    if error:
        logger.warning(f"[create_meeting] Validation error: {error}")
        return validated_data

    validated_data = validated_data.model_dump(exclude_unset=True)
    year = validated_data["year"]
    term = validated_data["term"]

    # Check if meeting start/end times are within the term
    if year not in Config.SCHOOL_YEAR:
        logger.warning(f"[create_meeting] Invalid year: {year}")
        return error_response("Invalid year", 400)
    
    if (Config.SCHOOL_YEAR[year][term]["start"] > validated_data["time_start"] or
        Config.SCHOOL_YEAR[year][term]["end"] < validated_data["time_end"]):
        logger.warning("[create_meeting] Meeting out of term bounds")
        return error_response("Meeting out of term", 400)
    
    create_result, idd = await attendance_service.create_meeting(validated_data)
    if not create_result:
        logger.error("[create_meeting] Create meeting (full) failed")
        return error_response("Create meeting failed", 500)

    # Create the half meeting
    validated_data["id"] = idd + 1
    validated_data["hours"] = validated_data["hours"] / 2
    validated_data["title"] = validated_data["title"] + " (1/2)"
    validated_data["parent"] = idd

    create_result2, idd2 = await attendance_service.create_meeting(validated_data)
    if not create_result2:
        logger.error("[create_meeting] Create meeting (half) failed, rolling back full")
        await attendance_service.delete_meeting(idd)
        return error_response("Create meeting failed", 500)
    
    logger.info(f"[create_meeting] Success - created meeting pair (full={idd}, half={idd2})")
    return success_response("Meeting created", 201)

# Function to retrieve a meeting by ID
async def get_meeting_by_id(meeting_id: int) -> Dict[str, Union[Dict[str, Any], str, int]]:
    logger = current_app.logger
    logger.info(f"[get_meeting_by_id] Start - meeting_id={meeting_id}")

    meeting = await attendance_service.get_meeting_by_id(meeting_id)
    if not meeting:
        logger.warning(f"[get_meeting_by_id] Meeting not found: {meeting_id}")
        return error_response("Meeting not found", 404)

    logger.info(f"[get_meeting_by_id] Success - meeting_id={meeting_id}")
    return success_response("Meeting retrieved", 200, {"meeting": meeting})

async def get_clean_meeting_by_id(meeting_id: int) -> Dict[str, Union[Dict[str, Any], str, int]]:
    logger = current_app.logger
    logger.info(f"[get_clean_meeting_by_id] Start - meeting_id={meeting_id}")

    meeting = await attendance_service.get_meeting_by_id(meeting_id)
    if not meeting:
        logger.warning(f"[get_clean_meeting_by_id] Meeting not found: {meeting_id}")
        return error_response("Meeting not found", 404)

    meeting.pop("members_logged", None)
    logger.info(f"[get_clean_meeting_by_id] Success - meeting_id={meeting_id}, cleaned members_logged")
    return success_response("Meeting retrieved", 200, {"meeting": meeting})

async def get_all_clean_meetings() -> Dict[str, Union[list, int]]:
    logger = current_app.logger
    logger.info("[get_all_clean_meetings] Start")

    meetings = await attendance_service.get_all_meetings()
    for m in meetings:
        m.pop("members_logged", None)

    logger.info("[get_all_clean_meetings] Success - returning cleaned meetings")
    return success_response("Meetings retrieved", 200, {"meetings": meetings})

# Function to update a meeting
async def update_meeting(meeting_id: int, data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[update_meeting] Start - meeting_id={meeting_id}, data={data}")

    validated_data, error = validate_data(MeetingSchema, data, "Update Meeting")
    if error:
        logger.warning(f"[update_meeting] Validation error: {error}")
        return validated_data

    result = await attendance_service.update_meeting(meeting_id, validated_data.model_dump(exclude_unset=True))
    if not result.modified_count:
        logger.warning(f"[update_meeting] Not found or unchanged - meeting_id={meeting_id}")
        return error_response("Not found or unchanged", 404)

    logger.info(f"[update_meeting] Success - meeting_id={meeting_id}")
    return success_response("Meeting updated", 200)

# Function to delete a meeting
async def delete_meeting(meeting_id: int) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[delete_meeting] Start - meeting_id={meeting_id}")

    # We cant actually delete a meeting since that would remove all attendance logs and mess up sequential IDs
    deletion = await attendance_service.delete_meeting(meeting_id)
    if not deletion.deleted_count:
        logger.warning(f"[delete_meeting] Meeting not found: {meeting_id}")
        return error_response("Meeting not found", 404)
    
    # Look for any child meetings and delete them
    child_meetings = await attendance_service.get_child_meetings(meeting_id)
    for m in child_meetings:
        logger.info(f"[delete_meeting] Deleting child meeting_id={m['_id']} of parent={meeting_id}")
        delete = await attendance_service.delete_meeting(m["_id"])
        if not delete.deleted_count:
            logger.warning(f"[delete_meeting] Child meeting not found: {m['_id']}")
            return error_response("Meeting not found", 404)

    logger.info(f"[delete_meeting] Success - meeting_id={meeting_id} (and children)")
    return success_response("Meeting deleted", 200)

# Function to retrieve all meetings
async def get_all_meetings() -> Dict[str, Union[list, int]]:
    logger = current_app.logger
    logger.info("[get_all_meetings] Start")

    meetings = await attendance_service.get_all_meetings()
    logger.info("[get_all_meetings] Success")
    return success_response("Meetings retrieved", 200, {"meetings": meetings})

async def get_attendance_by_user_id(user_id: int) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[get_attendance_by_user_id] Start - user_id={user_id}")

    user = await attendance_service.get_attendance_by_user_id(user_id)
    if not user:
        logger.info(f"[get_attendance_by_user_id] No attendance found for user_id={user_id}")
        return success_response("No attendance found", 204, {})

    logger.info(f"[get_attendance_by_user_id] Success - user_id={user_id}")
    return success_response("Attendance retrieved", 200, {"attendance": user})

async def get_all_attendance() -> Dict[str, Union[list, int]]:
    logger = current_app.logger
    logger.info("[get_all_attendance] Start")

    attendance = await attendance_service.get_all_attendance()
    logger.info("[get_all_attendance] Success")
    return success_response("Attendance retrieved", 200, {"attendance": attendance})

async def add_manual_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    logger = current_app.logger
    logger.info(f"[add_manual_attendance] Start - data={data}")

    validated_data, error = validate_data(ManualAttendanceLogSchema, data, "Add Manual Attendance")
    if error:
        logger.warning(f"[add_manual_attendance] Validation error: {error}")
        return validated_data

    user_id = validated_data.user_id
    attendance_log = validated_data.attendanceLog    

    success = await attendance_service.add_manual_attendance_log(user_id, attendance_log.model_dump())
    if not success:
        logger.error(f"[add_manual_attendance] Failed to add manual log for user_id={user_id}")
        return error_response("Failed to add manual attendance log", 500)

    logger.info(f"[add_manual_attendance] Success - user_id={user_id}, log={attendance_log.model_dump()}")
    return success_response("Manual attendance log added", 201)

async def add_user_to_meeting(data):
    logger = current_app.logger
    logger.info(f"[add_user_to_meeting] Start - data={data}")

    validated_data, error = validate_data(ManualUserMeetingSchema, data, "Add Manual Attendance")
    if error:
        logger.warning(f"[add_user_to_meeting] Validation error: {error}")
        return validated_data

    user_id = validated_data.user_id
    attendance_log = validated_data.attendanceLog

    success = await attendance_service.add_user_to_meeting(user_id, attendance_log.model_dump())
    if not success:
        logger.error(f"[add_user_to_meeting] Failed to add user {user_id} to meeting_id={attendance_log.meeting_id}")
        return error_response("Failed to add user to meeting", 500)

    logger.info(f"[add_user_to_meeting] Success - user_id={user_id}, meeting_id={attendance_log.meeting_id}")
    return success_response("User added to meeting", 201)