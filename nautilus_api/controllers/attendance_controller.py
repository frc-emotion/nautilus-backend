from pydantic import ValidationError
from quart import current_app
from typing import Any, Dict, Union
from nautilus_api.config import Config
from nautilus_api.controllers.account_controller import error_response, success_response
import nautilus_api.services.attendance_service as attendance_service
from nautilus_api.schemas.attendance_schema import ManualAttendanceLogSchema, MeetingSchema, AttendanceLogSchema, AttendanceUserSchema, RemoveAttendanceLogSchema, RemoveManualAttendanceSchema
from nautilus_api.schemas.utils import format_validation_error

# Helper function for data validation
async def validate_data(schema, data: Dict[str, Any], action: str) -> Union[Any, Dict[str, Union[str, int]]]:
    """Validates data against a schema, logging errors if validation fails."""
    try:
        validated_data = schema(**data)
        current_app.logger.info(f"{action} data validated: {validated_data}")
        return validated_data
    except ValidationError as e:
        current_app.logger.error(f"Validation error in {action}: {e.errors()}")
        return error_response(format_validation_error(e), 400)

# Attendance logging function
async def log_attendance(data: Dict[str, Any], user_id: int) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(AttendanceLogSchema, data, "Log Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    meeting = await attendance_service.get_meeting_by_id(validated_data.meeting_id)
    if not meeting:
        return error_response("Meeting not found", 404)

    if not meeting["time_start"] <= validated_data.time_received <= meeting["time_end"]:
        return error_response("Timestamp out of bounds", 400)

    if await attendance_service.user_already_logged(user_id, validated_data.meeting_id):
        return error_response("Already logged", 409)

    if not await attendance_service.log_attendance(validated_data.model_dump(exclude_unset=True), user_id):
        return error_response("Log attendance failed", 500)
    
    if not await attendance_service.update_meeting_attendance(validated_data.meeting_id, user_id):
        return error_response("Meeting update failed", 500)

    return success_response("Attendance logged", 201)

# Function to get total attendance hours for a user
async def get_attendance_hours(user_id: int) -> Dict[str, Union[int, str]]:
    try:
        total_hours = await attendance_service.get_hours_by_user_id(user_id)
        return success_response("Hours retrieved", 200, {"total_hours": total_hours})
    except Exception as e:
        current_app.logger.error(f"Error retrieving hours for user_id: {user_id} - {str(e)}")
        return error_response("Retrieval failed", 500)

# Function to remove an attendance log
async def remove_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(AttendanceLogSchema, data, "Remove Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    if not await attendance_service.remove_attendance(validated_data.model_dump(exclude_unset=True)):
        return error_response("Attendance log not found", 404)

    return success_response("Log removed", 200)

# Function to modify an attendance log
async def modify_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(RemoveAttendanceLogSchema, data, "Modify Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    if not await attendance_service.modify_attendance(validated_data.model_dump(exclude_unset=True)):
        return error_response("Attendance log not found", 404)

    return success_response("Log modified", 200)

# Function to create a meeting
async def create_meeting(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(MeetingSchema, data, "Create Meeting")
    print(validated_data)
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    validated_data = validated_data.model_dump(exclude_unset=True)

    # Check if meeting start and end times are within the term
    if validated_data["year"] not in Config.SCHOOL_YEAR:
        return error_response("Invalid year", 400)
    
    if Config.SCHOOL_YEAR[validated_data["year"]][validated_data["term"]]["start"] > validated_data["time_start"] or Config.SCHOOL_YEAR[validated_data["year"]][validated_data["term"]]["end"] < validated_data["time_end"]:
        return error_response("Meeting out of term", 400)

    if not await attendance_service.create_meeting(validated_data):
        return error_response("Create meeting failed", 500)

    return success_response("Meeting created", 201)

# Function to retrieve a meeting by ID
async def get_meeting_by_id(meeting_id: int) -> Dict[str, Union[Dict[str, Any], str, int]]:
    meeting = await attendance_service.get_meeting_by_id(meeting_id)
    if not meeting:
        return error_response("Meeting not found", 404)

    return success_response("Meeting retrieved", 200, {"meeting": meeting})

async def get_clean_meeting_by_id(meeting_id: int) -> Dict[str, Union[Dict[str, Any], str, int]]:
    meeting = await attendance_service.get_meeting_by_id(meeting_id)
    if not meeting:
        return error_response("Meeting not found", 404)

    meeting.pop("members_logged", None)

    return success_response("Meeting retrieved", 200, {"meeting": meeting})

async def get_all_clean_meetings() -> Dict[str, Union[list, int]]:
    meetings = await attendance_service.get_all_meetings()
    for meeting in meetings:
        meeting.pop("members_logged", None)

    return success_response("Meetings retrieved", 200, {"meetings": meetings})

# Function to update a meeting
async def update_meeting(meeting_id: int, data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(MeetingSchema, data, "Update Meeting")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    result = await attendance_service.update_meeting(meeting_id, validated_data.model_dump(exclude_unset=True))
    if not result.modified_count:
        return error_response("Not found or unchanged", 404)

    return success_response("Meeting updated", 200)

# Function to delete a meeting
async def delete_meeting(meeting_id: int) -> Dict[str, Union[str, int]]:
    # We cant actually delete a meeting since that would remove all attendance logs and mess up sequential IDs
    if not (await attendance_service.delete_meeting(meeting_id)).deleted_count:
        return error_response("Meeting not found", 404)

    return success_response("Meeting deleted", 200)

# Function to retrieve all meetings
async def get_all_meetings() -> Dict[str, Union[list, int]]:
    meetings = await attendance_service.get_all_meetings()

    return success_response("Meetings retrieved", 200, {"meetings": meetings})

async def get_attendance_by_user_id(user_id: int) -> Dict[str, Union[str, int]]:
    user = await attendance_service.get_attendance_by_user_id(user_id)
    
    if not user:
        return error_response("User not found", 404)
    
    return success_response("Attendance retrieved", 200, {"attendance": user})

async def get_all_attendance() -> Dict[str, Union[list, int]]:
    attendance = await attendance_service.get_all_attendance()
    
    return success_response("Attendance retrieved", 200, {"attendance": attendance})

async def add_manual_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(ManualAttendanceLogSchema, data, "Add Manual Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    user_id = validated_data.user_id
    attendance_log = validated_data.attendanceLog    

    # Add manual attendance log via service
    success = await attendance_service.add_manual_attendance_log(user_id, attendance_log.model_dump())
    if not success:
        return error_response("Failed to add manual attendance log", 500)

    return success_response("Manual attendance log added", 201)
