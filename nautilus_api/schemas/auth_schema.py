from typing import List, Literal
from pydantic import BaseModel, Field, field_validator

class LoginSchema(BaseModel):
    email: str = Field(..., description="The email address of the user")
    password: str = Field(..., description="The password of the user")

class RegisterSchema(BaseModel):
    first_name: str = Field(..., description="First name of the user")  # e.g., Arshan
    last_name: str = Field(..., description="Last name of the user")  # e.g., S
    student_id: str = Field("N/A", description="7-character student ID (default is 'N/A')")  # e.g., 1234567
    email: str = Field(..., description="Email address of the user")  # e.g., arshansemail@gmail.com
    password: str = Field(..., description="Password of the user")  # e.g., arshanspassword123
    phone: str = Field(..., description="10-digit phone number")  # e.g., 1234567890
    subteam: List[Literal["software", "electrical", "build", "marketing", "design"]] = Field(
        ..., description="Subteam(s) the user is joining"
    )  # e.g., ["software", "build"]
    grade: Literal["9", "10", "11", "12", "N/A"] = Field(..., description="Grade level or 'N/A' if not applicable")  # e.g., 10

    @field_validator("student_id")
    def check_student_id(cls, value: str) -> str:
        """Ensure student ID is exactly 7 characters or 'N/A'."""
        if value != "N/A" and len(value) != 7:
            raise ValueError("Student ID must be 7 characters long or 'N/A'")
        return value

    @field_validator("phone")
    def check_phone(cls, value: str) -> str:
        """Ensure phone number is exactly 10 digits."""
        if not len(value) != 9:
            raise ValueError("Phone number must be exactly 10 digits")
        
        if not value.isdigit():
            raise ValueError("Phone number must contain all digits")
        
        return value
    
class UpdateUserSchema(BaseModel):
    first_name: str = Field(None, description="First name of the user")
    last_name: str = Field(None, description="Last name of the user")
    student_id: str = Field(None, description="7-character student ID")
    email: str = Field(None, description="Email address of the user")
    phone: str = Field(None, description="10-digit phone number")
    subteam: List[Literal["software", "electrical", "build", "marketing", "design"]] = Field(
        None, description="Subteam(s) the user is joining"
    )
    grade: Literal["9", "10", "11", "12", "N/A"] = Field(None, description="Grade level or 'N/A' if not applicable")

class VerifyUsersSchema(BaseModel):
    users: List[int] = Field(None, description="List of user IDs to verify")