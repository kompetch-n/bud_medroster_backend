from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class ReplacementDoctor(BaseModel):
    doctor_id: str
    doctor_name: str
    status: str = "pending"


class LeaveRequest(BaseModel):
    doctor_id: str
    thai_full_name: str
    care_provider_code: str
    ipus: str
    department: str
    sub_department: str

    replacement_doctors: List[ReplacementDoctor]

    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None

    status: Optional[str] = "pending"
    created_at: Optional[datetime] = None