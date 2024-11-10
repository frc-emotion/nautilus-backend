from typing import List, Literal
from pydantic import BaseModel, field_validator


class RegisterSchema(BaseModel):
    first_name: str # Arshan
    last_name: str # Shokoohi
    student_id: str = "N/A" # 1234567
    email: str # arshansemail@gmail.com
    password: str # arshanspassword123
    phone: str # 1234567890
    subteam: List[Literal["software", "electrical", "build", "marketing", "design"]] # Software, Electrical, Build, Marketing, Design
    grade: Literal["9", "10", "11", "12", "N/A"] # 9, 10, 11, 12, N/A

    @field_validator("student_id")
    def check_student_id(cls, value):
        if len(value) != 7:
            raise ValueError("Student ID must be 7 characters long")
        return value
    
    @field_validator("phone")
    def check_phone(cls, value):
        if len(value) != 10:
            raise ValueError("Phone number must be 10 digits long")
        return value
    