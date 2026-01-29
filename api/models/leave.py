from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LeaveRequest(BaseModel):
    doctor_id: str
    thai_full_name: str
    care_provider_code: str
    ipus: str
    department: str
    sub_department: str

    replacement_doctor_id: Optional[str] = None
    replacement_doctor_name: Optional[str] = None

    leave_type: str
    start_date: str
    end_date: str
    reason: Optional[str] = None

    status: Optional[str] = "pending"
    created_at: Optional[datetime] = datetime.utcnow()
