from pydantic import BaseModel

class AttendanceSchema(BaseModel):
    student_name: str