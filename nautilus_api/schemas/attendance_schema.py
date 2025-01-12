from pydantic import BaseModel, Field, field_validator

from nautilus_api.config import Config

class MeetingSchema(BaseModel):
    title: str = Field(..., description="Title of the meeting")
    created_by: int = Field(..., description="ID of the user creating the meeting")
    time_start: int = Field(..., description="Unix timestamp for the start time")
    time_end: int = Field(..., description="Unix timestamp for the end time")
    location: str = Field(..., description="Location of the meeting")
    description: str = Field(..., description="Detailed description of the meeting")
    hours: float = Field(..., description="Duration of the meeting in hours")
    term: int = Field(..., description="Academic term of the meeting")
    year: str = Field(..., description="Academic year of the meeting")

    @field_validator("term")
    def check_term(cls, value: int) -> int:
        """Ensure term is either 1 or 2."""
        if value not in [1, 2]:
            raise ValueError("Term must be either 1 or 2")
        return value
    
    @field_validator("year")
    def check_year(cls, value: str) -> str:
        """Ensure year is in the correct format."""

        # Check if year is in the format 'YYYY-YYYY'
        if len(value) != 9 or value[4] != "-":
            raise ValueError("Year must be in the format 'YYYY-YYYY'")

        if value not in Config.SCHOOL_YEAR:
            raise ValueError("Year is not in the school year")
        return value

class AttendanceLogSchema(BaseModel):
    meeting_id: int = Field(..., description="ID of the meeting attended")
    lead_id: int = Field(..., description="ID of the user who broadcasted the attendance")
    time_received: int = Field(..., description="Unix timestamp when attendance was received")
    flag: bool = Field(..., description="Flag to indicate if suspicious attendance")

class ManualAttendanceLogSchema(BaseModel):
    meeting_id: int = Field(..., description="ID of the meeting attended")
    lead_id: int = Field(..., description="ID of the user who broadcasted the attendance")
    time_received: int = Field(..., description="Unix timestamp when attendance was received")
    flag: bool = Field(..., description="Flag to indicate if suspicious attendance")
    term: int = Field(..., description="Academic term")
    year: str = Field(..., description="Academic year")
    hours: float = Field(..., description="Duration of the override in hours")


class AttendanceUserSchema(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    logs: list[AttendanceLogSchema] = Field(..., description="List of attendance logs for the user")

class RemoveAttendanceLogSchema(BaseModel):
    meeting_id: int = Field(..., description="ID of the meeting attended")
    user_id: int = Field(..., description="ID of the user whose attendance is updated")


class ManualAttendanceLogSchema(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    attendanceLog: ManualAttendanceLogSchema = Field(..., description="Attendance log data")
    year: str = Field(..., description="Academic year")
    term: int = Field(..., description="Academic term")

    @field_validator('attendanceLog')
    def check_meeting_id(cls, value):
        if value.meeting_id != -1:
            raise ValueError("Manual attendance logs must have meeting_id as -1")
        return value

class RemoveManualAttendanceSchema(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    hours: float = Field(..., description="Total hours to remove")
    term: int = Field(..., description="Academic term")
    year: str = Field(..., description="Academic year")