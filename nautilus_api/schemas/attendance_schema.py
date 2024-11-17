from pydantic import BaseModel, Field

class MeetingSchema(BaseModel):
    title: str = Field(None, description="Title of the meeting")
    created_by: int = Field(None, description="ID of the user creating the meeting")
    time_start: int = Field(None, description="Unix timestamp for the start time")
    time_end: int = Field(None, description="Unix timestamp for the end time")
    location: str = Field(None, description="Location of the meeting")
    description: str = Field(None, description="Detailed description of the meeting")
    hours: int = Field(None, description="Duration of the meeting in hours")

class AttendanceLogSchema(BaseModel):
    meeting_id: int = Field(None, description="ID of the meeting attended")
    lead_id: int = Field(None, description="ID of the user who broadcasted the attendance")
    time_received: int = Field(None, description="Unix timestamp when attendance was received")
    flag: bool = Field(None, description="Flag to indicate if suspicious attendance")

class AttendanceUserSchema(BaseModel):
    user_id: int = Field(None, description="ID of the user")
    logs: list[AttendanceLogSchema] = Field(None, description="List of attendance logs for the user")

class RemoveAttendanceLogSchema(BaseModel):
    meeting_id: int = Field(None, description="ID of the meeting attended")
    user_id: int = Field(None, description="ID of the user whose attendance is updated")
