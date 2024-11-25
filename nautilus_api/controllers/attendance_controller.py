from pydantic import ValidationError
from quart import current_app
from typing import Any, Dict, Union
import nautilus_api.services.attendance_service as attendance_service
from nautilus_api.schemas.attendance_schema import MeetingSchema, AttendanceLogSchema, AttendanceUserSchema, RemoveAttendanceLogSchema
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
        return {"error": format_validation_error(e), "status": 400}

# Helper function for response formatting
def format_response(message: str, status: int) -> Dict[str, Union[str, int]]:
    """Formats a consistent response dictionary."""
    return {"message": message, "status": status}

# Attendance logging function
async def log_attendance(data: Dict[str, Any], user_id: int) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(AttendanceLogSchema, data, "Log Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    meeting = await attendance_service.get_meeting_by_id(validated_data.meeting_id)
    if not meeting:
        return format_response("Meeting not found", 404)

    if not meeting["time_start"] <= validated_data.time_received <= meeting["time_end"]:
        return format_response("Timestamp out of bounds", 400)

    if await attendance_service.user_already_logged(user_id, validated_data.meeting_id):
        return format_response("Already logged", 409)

    if not await attendance_service.log_attendance(validated_data.model_dump(exclude_unset=True), user_id):
        return format_response("Log attendance failed", 500)
    
    if not await attendance_service.update_meeting_attendance(validated_data.meeting_id, user_id):
        return format_response("Meeting update failed", 500)

    return format_response("Attendance logged", 201)

# Function to get total attendance hours for a user
async def get_attendance_hours(user_id: int) -> Dict[str, Union[int, str]]:
    try:
        total_hours = await attendance_service.get_hours_by_user_id(user_id)
        return {"total_hours": total_hours, "status": 200}
    except Exception as e:
        current_app.logger.error(f"Error retrieving hours for user_id: {user_id} - {str(e)}")
        return {"error": "Retrieval failed", "status": 500}

# Function to remove an attendance log
async def remove_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(AttendanceLogSchema, data, "Remove Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    if not await attendance_service.remove_attendance(validated_data.model_dump(exclude_unset=True)):
        return format_response("Attendance log not found", 404)

    return format_response("Log removed", 200)

# Function to modify an attendance log
async def modify_attendance(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(RemoveAttendanceLogSchema, data, "Modify Attendance")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    if not await attendance_service.modify_attendance(validated_data.model_dump(exclude_unset=True)):
        return format_response("Log not found", 404)

    return format_response("Log modified", 200)

# Function to create a meeting
async def create_meeting(data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(MeetingSchema, data, "Create Meeting")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    if not await attendance_service.create_meeting(validated_data.model_dump(exclude_unset=True)):
        return format_response("Create meeting failed", 500)

    return format_response("Meeting created", 201)

# Function to retrieve a meeting by ID
async def get_meeting_by_id(meeting_id: int) -> Dict[str, Union[Dict[str, Any], str, int]]:
    meeting = await attendance_service.get_meeting_by_id(meeting_id)
    if not meeting:
        return format_response("Meeting not found", 404)

    return {"meeting": meeting, "status": 200}

async def get_clean_meeting_by_id(meeting_id: int) -> Dict[str, Union[Dict[str, Any], str, int]]:
    meeting = await attendance_service.get_meeting_by_id(meeting_id)
    if not meeting:
        return format_response("Meeting not found", 404)

    meeting.pop("members_logged", None)

    return {"meeting": meeting, "status": 200}

async def get_all_clean_meetings() -> Dict[str, Union[list, int]]:
    meetings = await attendance_service.get_all_meetings()
    for meeting in meetings:
        meeting.pop("members_logged", None)

    return {"meetings": meetings, "status": 200}

# Function to update a meeting
async def update_meeting(meeting_id: int, data: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    validated_data = await validate_data(MeetingSchema, data, "Update Meeting")
    if isinstance(validated_data, dict): return validated_data  # Return error if validation failed

    result = await attendance_service.update_meeting(meeting_id, validated_data.model_dump(exclude_unset=True))
    if not result.modified_count:
        return format_response("Not found or unchanged", 404)

    return format_response("Meeting updated", 200)

# Function to delete a meeting
async def delete_meeting(meeting_id: int) -> Dict[str, Union[str, int]]:
    # We cant actually delete a meeting since that would remove all attendance logs and mess up sequential IDs
    if not (await attendance_service.delete_meeting(meeting_id)).deleted_count:
        return format_response("Meeting not found", 404)

    return format_response("Meeting deleted", 200)

# Function to retrieve all meetings
async def get_all_meetings() -> Dict[str, Union[list, int]]:
    meetings = await attendance_service.get_all_meetings()
    return {"meetings": meetings, "status": 200}

async def get_attendance_by_user_id(user_id: int) -> Dict[str, Union[str, int]]:
    user = await attendance_service.get_attendance_by_user_id(user_id)
    
    if not user:
        return format_response("User not found", 404)
    
    return {"attendance": user, "status": 200}