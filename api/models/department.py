from pydantic import BaseModel, Field
from typing import Optional, List

class Shift(BaseModel):
    name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class SubDepartment(BaseModel):
    name: str
    shifts: List[Shift] = []

class Department(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    department: str
    sub_departments: List[SubDepartment] = []
