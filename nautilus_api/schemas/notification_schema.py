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

class InitialNotificationSchema(BaseModel):
    update: str = Field(..., description="Update message")
    active: str = Field(..., description="Is the update active? 1 for active, -1 for inactive")
    created_by: int = Field(..., description="ID of the user who created the update")

class UpdateNotificationSchema(BaseModel):
    id: int = Field(..., description="ID of the update")
    update: str = Field(..., description="Update message")
    edited_by: int = Field(..., description="ID of the user who edited the update")

class RemoveNotificationSchema(BaseModel):
    id: int = Field(..., description="ID of the update")
    removed_by: int = Field(..., description="ID of the user who removed the update")