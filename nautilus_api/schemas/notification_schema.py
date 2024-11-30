from typing import List, Literal
from pydantic import BaseModel, Field, field_validator

class TriggerNotificationSchema(BaseModel):
    title: str = Field(..., description="Title of the notification")
    message: str = Field(..., description="Message of the notification")
    user_id: int = Field(..., description="ID of the user receiving the notification")

class MassNotificationSchema(BaseModel):
    title: str = Field(..., description="Title of the notification")
    message: str = Field(..., description="Message of the notification")
    users: List[int] = Field(..., description="List of user IDs to receive the notification")
